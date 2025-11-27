"""
Liturgical Librarian - Phase 4 (Phrase-Level Index)

Queries the comprehensive phrase-level index (psalms_liturgy_index table)
with intelligent aggregation to prevent duplicate prayer contexts.

Features:
- Aggregates matches by prayer name (handles "Amidah" appearing 79x)
- Uses Google Gemini 2.5 Pro with extended thinking for intelligent context summarization
- Automatic fallback to Claude Sonnet 4.5 with extended thinking if Gemini quota exhausted
- Handles inconsistent metadata (e.g., "Avot" vs "Patriarchs")
- Provides both aggregated and detailed views

Usage:
    from src.agents.liturgical_librarian import LiturgicalLibrarian

    # With LLM summarization (default)
    librarian = LiturgicalLibrarian()
    results = librarian.find_liturgical_usage_by_phrase(psalm_chapter=23, psalm_verses=[3])

    # Without LLM (code-only summaries)
    librarian = LiturgicalLibrarian(use_llm_summaries=False)
    results = librarian.find_liturgical_usage_by_phrase(psalm_chapter=23)
"""

import sqlite3
import os
import json
import time
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass
from collections import defaultdict
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

if TYPE_CHECKING:
    from src.utils.cost_tracker import CostTracker


def _is_retryable_gemini_error(exception, verbose=False):
    """
    Determine if a Gemini API exception is retryable (temporary rate limit) vs permanent (quota exhausted).

    Returns True for temporary errors that should be retried with backoff.
    Returns False for quota exhaustion errors that should trigger Claude fallback.

    Args:
        exception: The exception to classify
        verbose: Whether to print classification info

    Returns:
        bool: True if retryable, False otherwise
    """
    error_msg = str(exception).lower()

    # Check for daily quota exhaustion indicators
    # These should NOT be retried - switch to Claude immediately
    quota_indicators = [
        'quota exceeded',
        'resource exhausted',
        'daily limit',
        '10,000 rpd',
        'quota has been exceeded'
    ]

    if any(indicator in error_msg for indicator in quota_indicators):
        if verbose:
            print(f"[INFO] Detected quota exhaustion (not retrying, will switch to Claude)")
        return False

    # Temporary rate limit errors - safe to retry with backoff
    rate_limit_indicators = [
        '429',
        'too many requests',
        'rate limit',
        'try again'
    ]

    if any(indicator in error_msg for indicator in rate_limit_indicators):
        if verbose:
            print(f"[INFO] Detected temporary rate limit (will retry with backoff)")
        return True

    # Network/transient errors - safe to retry
    transient_indicators = [
        'timeout',
        'connection',
        'network',
        'unavailable',
        'internal error'
    ]

    if any(indicator in error_msg for indicator in transient_indicators):
        return True

    # Default: don't retry unknown errors
    return False


@dataclass
class LiturgicalMatch:
    """A single match from psalms_liturgy_index with full prayer metadata."""

    # Index data
    index_id: int
    psalm_chapter: int
    psalm_verse_start: Optional[int]
    psalm_verse_end: Optional[int]
    psalm_phrase_hebrew: str
    phrase_length: int
    liturgy_phrase_hebrew: str
    liturgy_context: str
    match_type: str
    confidence: float
    is_unique: int  # 0 or 1 - whether phrase is unique to this psalm chapter
    locations: Optional[str]

    # Prayer metadata
    prayer_id: int
    prayer_name: Optional[str]
    source_text: str
    sefaria_ref: str
    nusach: str
    prayer_type: str
    occasion: Optional[str]
    service: Optional[str]
    section: Optional[str]

    # Canonical classification fields (our own, better than Sefaria)
    canonical_prayer_name: Optional[str]
    canonical_L1_Occasion: Optional[str]
    canonical_L2_Service: Optional[str]
    canonical_L3_Signpost: Optional[str]
    canonical_L4_SubSection: Optional[str]
    canonical_location_description: Optional[str]


@dataclass
class ValidationResult:
    """Result of LLM validation for a phrase match."""

    is_valid: bool  # True if this is really from the target psalm
    confidence: float  # 0.0-1.0 confidence in the validation
    reason: str  # Explanation (e.g., "Different psalm", "Context mismatch")
    liturgy_quote: Optional[str] = None  # Actual quote from liturgy
    translation: Optional[str] = None  # Translation of the quote
    notes: Optional[str] = None  # Additional context/warnings


@dataclass
class PhraseUsageMatch:
    """Represents where a specific phrase from a psalm appears in liturgy.

    Groups by PHRASE first, then shows all prayers/contexts where that phrase appears.
    """

    # Psalm phrase info
    psalm_phrase_hebrew: str  # The phrase from the psalm (e.g., "למען שמו")
    psalm_verse_range: str  # Which verse(s), e.g., "23:3" or "23:1-2"
    content_used_description: str  # Human-readable description of what content is used
    phrase_length: int  # Number of words in phrase

    # Usage statistics
    occurrence_count: int  # Total times this phrase appears in liturgy
    unique_prayer_contexts: int  # Number of distinct prayer contexts

    # Prayer contexts where this phrase appears
    prayer_contexts: List[str]  # List of prayer names/sections

    # Aggregated metadata
    occasions: List[str]
    services: List[str]
    nusachs: List[str]
    sections: List[str]

    # Summary (LLM-generated or code-generated)
    liturgical_summary: str

    # Match quality
    confidence_avg: float
    match_types: List[str]  # e.g., ["exact_verse", "phrase_match"]

    # Example context
    representative_liturgy_context: str  # Short excerpt showing phrase in use

    # Validation info (for filtered/flagged matches)
    validation_notes: Optional[str] = None  # Warnings about potential false positives

    # Raw data (optional)
    raw_matches: Optional[List[LiturgicalMatch]] = None


class LiturgicalLibrarian:
    """
    Main interface for querying liturgical usage from phrase-level index.

    Handles Phase 4 data with intelligent aggregation and optional LLM summarization.
    """

    def __init__(
        self,
        db_path: str = "data/liturgy.db",
        tanakh_db_path: str = "database/tanakh.db",
        use_llm_summaries: bool = True,
        google_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        thinking_budget: int = 4096,
        request_delay: float = 0.5,
        verbose: bool = False,
        cost_tracker: Optional['CostTracker'] = None
    ):
        """
        Initialize Liturgical Librarian.

        Args:
            db_path: Path to liturgy database
            tanakh_db_path: Path to tanakh database (for psalm verse text)
            use_llm_summaries: Whether to use LLM for intelligent summaries (Gemini 2.5 Pro primary, Claude Sonnet 4.5 fallback)
            google_api_key: Google API key (defaults to GOOGLE_API_KEY env var)
            anthropic_api_key: Anthropic API key for fallback (defaults to ANTHROPIC_API_KEY env var)
            thinking_budget: Token budget for Gemini's reasoning phase (default 4096)
                           - Higher values (up to 24576) for more complex reasoning
                           - Set to -1 for dynamic thinking (model decides)
                           - Set to 0 to disable thinking (not recommended)
            request_delay: Delay in seconds between API calls to avoid rate limits (default 0.5)
                         - Gemini Tier 1: 150 RPM = 2.5 req/sec max
                         - 0.5s delay = 2 req/sec (safely under limit)
                         - Set to 0 to disable (not recommended)
            verbose: Whether to print LLM prompts and responses
            cost_tracker: CostTracker instance for tracking API costs
        """
        self.db_path = db_path
        self.tanakh_db_path = tanakh_db_path
        self.use_llm_summaries = use_llm_summaries
        self.thinking_budget = thinking_budget
        self.request_delay = request_delay
        self.verbose = verbose
        self.gemini_client = None
        self.anthropic_client = None
        self.llm_provider = None  # Track which provider is active: 'gemini', 'anthropic', or None
        self._last_request_time = 0  # Track last API call time for rate limiting

        # Initialize cost tracker (import here to avoid circular dependency)
        if cost_tracker is None:
            from src.utils.cost_tracker import CostTracker
            self.cost_tracker = CostTracker()
        else:
            self.cost_tracker = cost_tracker

        # Load environment variables from .env file
        load_dotenv()

        # Initialize LLM clients if needed
        if use_llm_summaries:
            # Try Gemini 2.5 Pro first (primary)
            try:
                from google import genai
                api_key = google_api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
                if api_key:
                    # Initialize Gemini client
                    # Note: SDK retry config (RetryConfig) not available in this SDK version
                    # Using tenacity-based retry decorator instead (see _call_gemini_with_retry)
                    self.gemini_client = genai.Client(api_key=api_key)
                    self.llm_provider = 'gemini'
                    print("[INFO] Liturgical Librarian: Using Gemini 2.5 Pro with tenacity-based retry logic")
            except ImportError:
                if self.verbose:
                    print("[INFO] google-genai package not installed. Will try Claude Sonnet fallback.")

            # ALWAYS try to initialize Claude Sonnet 4.5 as fallback (even if Gemini available)
            # This ensures Claude is available if Gemini quota is exhausted at runtime
            try:
                import anthropic
                api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
                if api_key:
                    self.anthropic_client = anthropic.Anthropic(api_key=api_key)
                    # Only set as primary provider if Gemini not available
                    if not self.llm_provider:
                        self.llm_provider = 'anthropic'
                        print("[INFO] Liturgical Librarian: Using Claude Sonnet 4.5 for summaries (Gemini unavailable)")
                    else:
                        print("[INFO] Liturgical Librarian: Claude Sonnet 4.5 initialized as fallback")
            except ImportError:
                if self.verbose:
                    print("[INFO] anthropic package not installed.")

            # If neither provider available, fall back to code-only
            if not self.llm_provider:
                print("[WARNING] No LLM provider available (tried Gemini and Claude). Using code-only summaries.")
                self.use_llm_summaries = False

    def _enforce_rate_limit(self):
        """
        Enforce rate limiting between API calls to avoid burst requests.

        Gemini Tier 1 has 150 RPM limit = 2.5 req/sec burst rate.
        This method ensures we don't exceed the configured request_delay.
        """
        if self.request_delay > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.request_delay:
                sleep_time = self.request_delay - elapsed
                if self.verbose:
                    print(f"[RATE LIMIT] Sleeping {sleep_time:.2f}s to avoid burst requests...")
                time.sleep(sleep_time)
            self._last_request_time = time.time()

    @retry(
        retry=lambda retry_state: (
            retry_state.outcome.failed and
            retry_state.outcome.exception() is not None and
            _is_retryable_gemini_error(retry_state.outcome.exception())
        ),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _call_gemini_with_retry(self, prompt: str, temperature: float, thinking_budget: int):
        """
        Call Gemini API with exponential backoff retry for transient errors only.

        Retries up to 5 times with exponential backoff (2s, 4s, 8s, 10s, 10s) for:
        - Temporary rate limit errors (429 burst limit)
        - Network errors (timeouts, connection issues)

        Does NOT retry for:
        - Quota exhaustion (daily limit) - switches to Claude immediately
        - Other permanent errors

        Args:
            prompt: The prompt to send to Gemini
            temperature: Temperature setting for generation
            thinking_budget: Token budget for thinking phase

        Returns:
            Response object from Gemini API

        Raises:
            Exception: Re-raises exception for non-retryable errors or after all retries exhausted
        """
        from google.genai import types

        if self.verbose:
            print(f"[API] Calling Gemini 2.5 Pro...")

        response = self.gemini_client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config=types.GenerateContentConfig(
                # NOTE: max_output_tokens conflicts with thinking_config, causing response.text to be None
                # Gemini will automatically allocate tokens between thinking and output
                temperature=temperature,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=thinking_budget
                ),
                # Explicitly disable Automatic Function Calling to prevent internal burst requests
                # AFC can make up to 10 internal API calls which triggers 429 errors
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                )
            )
        )

        return response

    def generate_research_bundle(self, psalm_chapter: int) -> Dict[str, Any]:
        """
        Generate a research bundle for a given psalm chapter.

        This method orchestrates the process of finding liturgical usage,
        generating summaries, and structuring the data into a research bundle.

        Args:
            psalm_chapter: The psalm chapter number.

        Returns:
            A dictionary representing the research bundle.
        """
        # Use find_liturgical_usage_by_phrase to get the data
        phrase_usage_matches = self.find_liturgical_usage_by_phrase(
            psalm_chapter=psalm_chapter,
            separate_full_psalm=True,
            include_raw_matches=True
        )

        full_psalm_summary = ""
        phrase_groups = []

        # Separate full psalm recitations from phrase groups
        for match in phrase_usage_matches:
            if match.psalm_phrase_hebrew == f"[Full Psalm {psalm_chapter}]":
                # For full psalm recitations, we only need the summary
                full_psalm_summary = match.liturgical_summary
            else:
                # Simplified phrase groups: only phrase/verse + summary
                phrase_groups.append({
                    'phrase': match.psalm_phrase_hebrew,
                    'verses': match.psalm_verse_range,
                    'summary': match.liturgical_summary
                })

        return {
            'psalm_chapter': psalm_chapter,
            'full_psalm_summary': full_psalm_summary,
            'phrase_groups': phrase_groups
        }

    def format_for_research_bundle(
        self,
        phrase_usage_matches: List['PhraseUsageMatch'],
        psalm_chapter: int
    ) -> str:
        """
        Formats the aggregated liturgical usage data into a markdown string
        suitable for inclusion in the research bundle.
        """
        md = f"## Modern Jewish Liturgical Use (Psalm {psalm_chapter})\n\n"
        md += f"This section summarizes how Psalm {psalm_chapter} and its phrases are used in contemporary Jewish liturgy.\n\n"

        full_psalm_summary_text = ""
        phrase_summaries = []

        for match in phrase_usage_matches:
            if match.psalm_phrase_hebrew == f"[Full Psalm {psalm_chapter}]":
                full_psalm_summary_text = match.liturgical_summary
            else:
                phrase_summaries.append(match)

        if full_psalm_summary_text:
            md += f"### Full Psalm {psalm_chapter} Recitation\n\n"
            md += f"{full_psalm_summary_text}\n\n"

        if phrase_summaries:
            md += "### Phrase-Level Liturgical Usage\n\n"
            md += f"The following phrases from Psalm {psalm_chapter} appear in various liturgical contexts:\n\n"
            for match in phrase_summaries:
                md += f"#### Phrase: {match.psalm_phrase_hebrew} (from {match.psalm_verse_range})\n\n"
                md += f"{match.liturgical_summary}\n\n"
                if match.validation_notes:
                    md += f"**Note**: {match.validation_notes}\n\n"
                md += "---\n\n" # Separator for phrases

        if not full_psalm_summary_text and not phrase_summaries:
            md += f"No significant liturgical usage found for Psalm {psalm_chapter} or its phrases.\n\n"

        return md

    def find_liturgical_usage_aggregated(
        self,
        psalm_chapter: int,
        min_confidence: float = 0.75
    ) -> List[PhraseUsageMatch]:
        """
        Finds aggregated liturgical usage for a given psalm chapter.
        This method is called by ResearchAssembler.
        """
        return self.find_liturgical_usage_by_phrase(
            psalm_chapter=psalm_chapter,
            min_confidence=min_confidence,
            separate_full_psalm=True,
            include_raw_matches=False # No need for raw matches in aggregated view
        )

    def _get_db_connection(self):
        """Establish a connection to the SQLite database."""
        return sqlite3.connect(self.db_path)

    def find_liturgical_usage_by_phrase(
        self,
        psalm_chapter: int,
        psalm_verses: Optional[List[int]] = None,
        min_confidence: float = 0.75,
        include_raw_matches: bool = False,
        separate_full_psalm: bool = True
    ) -> List[PhraseUsageMatch]:
        """
        Find liturgical usage grouped by PHRASE (not by prayer).

        This is the preferred method that answers: "Where does THIS SPECIFIC PHRASE
        from the psalm appear in liturgy?"

        Args:
            psalm_chapter: Psalm chapter number
            psalm_verses: Specific verses (None = entire chapter)
            min_confidence: Minimum confidence threshold
            include_raw_matches: Include full list of raw matches
            separate_full_psalm: If True, separate full psalm recitations from phrase quotes

        Returns:
            List of phrase usage matches (one per unique psalm phrase)
        """
        # 1. Get all raw matches
        raw_matches = self._get_raw_matches(
            psalm_chapter=psalm_chapter,
            psalm_verses=psalm_verses,
            min_confidence=min_confidence
        )

        if not raw_matches:
            return []

        # 2. Separate full psalm recitations and phrase matches
        if separate_full_psalm:
            # Per user feedback, only 'entire_chapter' is a "full psalm recitation"
            full_psalm_matches = [m for m in raw_matches if m.match_type == 'entire_chapter']
            phrase_matches = [m for m in raw_matches if m.match_type != 'entire_chapter']

            # Get prayer_ids where full/substantial content is present (to deduplicate phrases)
            full_psalm_prayer_ids = set(m.prayer_id for m in full_psalm_matches)

            # Filter out phrase matches from same contexts where full/substantial content exists
            phrase_matches = [m for m in phrase_matches if m.prayer_id not in full_psalm_prayer_ids]
        else:
            phrase_matches = raw_matches
            full_psalm_matches = []

        # 3. Group by psalm phrase
        grouped = self._group_by_psalm_phrase(phrase_matches)

        # 4. Merge overlapping phrases (same prayer contexts)
        # This is now disabled as per user feedback to have separate summaries.
        # grouped = self._merge_overlapping_phrase_groups(grouped)

        # 4.5. LLM Validation Pass for phrase matches
        # DISABLED per user feedback - validation should be implicit in summary generation
        # The LLM will naturally handle false positives as part of its analysis
        validation_notes = {}
        # if self.use_llm_summaries and self.anthropic_client:
        #     grouped, validation_notes = self._validate_phrase_groups_with_llm(grouped, psalm_chapter)
        #     if self.verbose:
        #         print(f"DEBUG: number of groups to be processed: {len(grouped)}")

        # 5. Create aggregated results for each phrase
        phrase_results = []

        for phrase_key_tuple, matches in grouped.items():
            phrase_key = phrase_key_tuple[0]
            # Extract metadata
            contexts_data = self._extract_contexts_metadata(matches)

            # Get unique prayer contexts
            prayer_contexts = self._extract_prayer_contexts(matches)

            # Generate verse range
            verse_range = self._format_verse_range(psalm_chapter, matches)

            # Generate summary (LLM or code)
            if self.use_llm_summaries and len(matches) >= 1:
                # Enforce rate limiting before API call
                self._enforce_rate_limit()

                summary = self._generate_phrase_llm_summary(
                    psalm_phrase=phrase_key,
                    psalm_verse_range=verse_range,
                    prayer_contexts=prayer_contexts,
                    contexts=contexts_data,
                    total_count=len(matches),
                    matches=matches
                )
            else:
                summary = self._generate_phrase_code_summary(
                    phrase_key, prayer_contexts, contexts_data
                )

            # Build result
            phrase_results.append(PhraseUsageMatch(
                psalm_phrase_hebrew=phrase_key,
                psalm_verse_range=verse_range,
                content_used_description=self._format_content_used(matches[0]),
                phrase_length=matches[0].phrase_length,
                occurrence_count=len(matches),
                unique_prayer_contexts=len(prayer_contexts),
                prayer_contexts=prayer_contexts,
                occasions=contexts_data['occasions'],
                services=contexts_data['services'],
                nusachs=contexts_data['nusachs'],
                sections=contexts_data['sections'],
                liturgical_summary=summary,
                confidence_avg=sum(m.confidence for m in matches) / len(matches),
                match_types=list(set(m.match_type for m in matches)),
                # Increased from 200 to 400 chars for better context (Session 131)
                representative_liturgy_context=matches[0].liturgy_context[:400] + "...",
                validation_notes=validation_notes.get(phrase_key_tuple),
                raw_matches=matches if include_raw_matches else None
            ))

        # 6. Handle full psalm recitations separately if requested
        if separate_full_psalm and full_psalm_matches:
            # Consolidate all full psalm matches into ONE entry
            # (Don't group by phrase since they're all "full psalm" regardless of trigger phrase)
            contexts_data = self._extract_contexts_metadata(full_psalm_matches)
            prayer_contexts = self._extract_prayer_contexts(full_psalm_matches)

            # Generate summary with verse coverage information
            summary = self._generate_full_psalm_summary(
                psalm_chapter=psalm_chapter,
                matches=full_psalm_matches,
                prayer_contexts=prayer_contexts,
                contexts_data=contexts_data
            )

            # Determine actual verse range from matches
            all_verses = []
            for m in full_psalm_matches:
                if m.match_type == 'exact_verse':
                    all_verses.append(m.psalm_verse_start)
                elif m.match_type == 'verse_range':
                    all_verses.extend(range(m.psalm_verse_start, m.psalm_verse_end + 1))
                elif m.match_type == 'verse_set' and m.locations:
                    try:
                        all_verses.extend(json.loads(m.locations))
                    except (json.JSONDecodeError, TypeError):
                        pass
                elif m.match_type == 'entire_chapter':
                    psalm_verses = self._get_psalm_verses(psalm_chapter)
                    if psalm_verses:
                        all_verses.extend(psalm_verses.keys())

            if all_verses:
                unique_verses = sorted(set(all_verses))
                verse_range_str = self._format_verse_list(unique_verses)
                psalm_verse_range = f"{psalm_chapter}:{verse_range_str}"
            else:
                psalm_verse_range = f"{psalm_chapter}:1-end"

            # Collect all unique match types from the full psalm matches
            full_psalm_match_types = list(set(m.match_type for m in full_psalm_matches))

            phrase_results.append(PhraseUsageMatch(
                psalm_phrase_hebrew=f"[Full Psalm {psalm_chapter}]",
                psalm_verse_range=psalm_verse_range,
                content_used_description=f"Entire Psalm {psalm_chapter}",
                phrase_length=0,  # Full psalm
                occurrence_count=len(full_psalm_matches),
                unique_prayer_contexts=len(prayer_contexts),
                prayer_contexts=prayer_contexts,
                occasions=contexts_data['occasions'],
                services=contexts_data['services'],
                nusachs=contexts_data['nusachs'],
                sections=contexts_data['sections'],
                liturgical_summary=summary,
                confidence_avg=sum(m.confidence for m in full_psalm_matches) / len(full_psalm_matches) if full_psalm_matches else 0,
                match_types=full_psalm_match_types,  # Use actual match types from the matches
                representative_liturgy_context="[Full psalm recitation]",
                raw_matches=full_psalm_matches if include_raw_matches else None
            ))

        # Sort by occurrence count (most common first)
        phrase_results.sort(key=lambda x: x.occurrence_count, reverse=True)

        return phrase_results

    def _get_raw_matches(
        self,
        psalm_chapter: int,
        psalm_verses: Optional[List[int]],
        min_confidence: float
    ) -> List[LiturgicalMatch]:
        """Query database for all raw matches with full metadata."""

        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Build query
        if psalm_verses is None:
            # Entire chapter
            query = """
                SELECT
                    i.index_id,
                    i.psalm_chapter,
                    i.psalm_verse_start,
                    i.psalm_verse_end,
                    i.psalm_phrase_hebrew,
                    i.phrase_length,
                    i.liturgy_phrase_hebrew,
                    i.liturgy_context,
                    i.match_type,
                    i.confidence,
                    i.is_unique,
                    i.locations,
                    p.prayer_id,
                    p.prayer_name,
                    p.source_text,
                    p.sefaria_ref,
                    p.nusach,
                    p.prayer_type,
                    p.occasion,
                    p.service,
                    p.section,
                    p.canonical_prayer_name,
                    p.canonical_L1_Occasion,
                    p.canonical_L2_Service,
                    p.canonical_L3_Signpost,
                    p.canonical_L4_SubSection,
                    p.canonical_location_description
                FROM psalms_liturgy_index i
                JOIN prayers p ON i.prayer_id = p.prayer_id
                WHERE i.psalm_chapter = ?
                  AND i.confidence >= ?
                  AND (i.match_type != 'phrase_match' OR i.is_unique = 1)
                ORDER BY i.confidence DESC, p.prayer_name
            """
            params = (psalm_chapter, min_confidence)
        else:
            # Specific verses
            verse_conditions = " OR ".join([
                "(i.psalm_verse_start <= ? AND (i.psalm_verse_end >= ? OR i.psalm_verse_end IS NULL))"
                for _ in psalm_verses
            ])

            query = f"""
                SELECT
                    i.index_id,
                    i.psalm_chapter,
                    i.psalm_verse_start,
                    i.psalm_verse_end,
                    i.psalm_phrase_hebrew,
                    i.phrase_length,
                    i.liturgy_phrase_hebrew,
                    i.liturgy_context,
                    i.match_type,
                    i.confidence,
                    i.is_unique,
                    i.locations,
                    p.prayer_id,
                    p.prayer_name,
                    p.source_text,
                    p.sefaria_ref,
                    p.nusach,
                    p.prayer_type,
                    p.occasion,
                    p.service,
                    p.section,
                    p.canonical_prayer_name,
                    p.canonical_L1_Occasion,
                    p.canonical_L2_Service,
                    p.canonical_L3_Signpost,
                    p.canonical_L4_SubSection,
                    p.canonical_location_description
                FROM psalms_liturgy_index i
                JOIN prayers p ON i.prayer_id = p.prayer_id
                WHERE i.psalm_chapter = ?
                  AND ({verse_conditions})
                  AND i.confidence >= ?
                  AND (i.match_type != 'phrase_match' OR i.is_unique = 1)
                ORDER BY i.confidence DESC, p.prayer_name
            """

            params = [psalm_chapter]
            for v in psalm_verses:
                params.extend([v, v])
            params.append(min_confidence)

        cursor.execute(query, params)

        matches = []
        for row in cursor.fetchall():
            matches.append(LiturgicalMatch(
                index_id=row[0],
                psalm_chapter=row[1],
                psalm_verse_start=row[2],
                psalm_verse_end=row[3],
                psalm_phrase_hebrew=row[4],
                phrase_length=row[5],
                liturgy_phrase_hebrew=row[6],
                liturgy_context=row[7],
                match_type=row[8],
                confidence=row[9],
                is_unique=row[10],
                locations=row[11],
                prayer_id=row[12],
                prayer_name=row[13],
                source_text=row[14],
                sefaria_ref=row[15],
                nusach=row[16],
                prayer_type=row[17],
                occasion=row[18],
                service=row[19],
                section=row[20],
                canonical_prayer_name=row[21],
                canonical_L1_Occasion=row[22],
                canonical_L2_Service=row[23],
                canonical_L3_Signpost=row[24],
                canonical_L4_SubSection=row[25],
                canonical_location_description=row[26]
            ))

        conn.close()
        return matches

    def _group_by_psalm_phrase(self, matches: List[LiturgicalMatch]) -> Dict[tuple, List[LiturgicalMatch]]:
        """
        Group matches by a composite key to ensure distinct summaries for distinct items.
        """
        grouped = defaultdict(list)

        for match in matches:
            # Filter out phrases with <2 meaningful words (like "פ" or single letters)
            if match.match_type == 'phrase_match':
                word_count = self._count_meaningful_hebrew_words(match.psalm_phrase_hebrew)
                if word_count < 2:
                    if self.verbose:
                        print(f"[FILTER] Phrase with <2 words (length: {len(match.psalm_phrase_hebrew)} chars, {word_count} words)")
                    continue

                # Filter out phrases that are not unique to this psalm chapter
                # (is_unique=0 means the phrase appears in other psalm chapters)
                if match.is_unique == 0:
                    if self.verbose:
                        try:
                            phrase_preview = match.psalm_phrase_hebrew[:50] + '...' if len(match.psalm_phrase_hebrew) > 50 else match.psalm_phrase_hebrew
                            print(f"[FILTER] Non-unique phrase (appears in other psalms): {phrase_preview}")
                        except UnicodeEncodeError:
                            print(f"[FILTER] Non-unique phrase (appears in other psalms) - length {len(match.psalm_phrase_hebrew)} chars")
                    continue

            # Use a composite key to group matches
            key = (
                match.psalm_phrase_hebrew.strip(),
                match.match_type,
                match.psalm_verse_start,
                match.psalm_verse_end
            )
            grouped[key].append(match)

        return dict(grouped)

    def _extract_contexts_metadata(self, matches: List[LiturgicalMatch]) -> Dict[str, Any]:
        """Extract structured metadata from a list of matches."""

        occasions = sorted(set(m.occasion for m in matches if m.occasion))
        services = sorted(set(m.service for m in matches if m.service))
        nusachs = sorted(set(m.nusach for m in matches if m.nusach))
        sections = sorted(set(m.section for m in matches if m.section))
        prayer_types = sorted(set(m.prayer_type for m in matches if m.prayer_type))

        return {
            'occasions': occasions,
            'services': services,
            'nusachs': nusachs,
            'sections': sections,
            'prayer_types': prayer_types,
            'total_count': len(matches)
        }

    def _extract_prayer_contexts(self, matches: List[LiturgicalMatch]) -> List[str]:
        """
        Extract unique prayer context descriptions from matches.

        Returns a list like: ["Amidah - Patriarchs (Ashkenaz)", "Shabbat Kiddush (Sefard)", ...]"""
        contexts = set()

        for match in matches:
            # Build a descriptive context string
            parts = []

            # Add prayer name or section
            if match.prayer_name and match.prayer_name.strip():
                parts.append(match.prayer_name.strip())
            elif match.section and match.section.strip():
                parts.append(match.section.strip())

            # Add nusach if available
            if match.nusach:
                parts.append(f"({match.nusach})")

            if parts:
                contexts.add(" ".join(parts))
            else:
                contexts.add("Unknown context")

        return sorted(list(contexts))

    def _format_verse_range(self, psalm_chapter: int, matches: List[LiturgicalMatch]) -> str:
        """
        Format a verse range string like "23:3" or "23:1-2".
        """
        verses = set()
        for match in matches:
            if match.psalm_verse_start:
                verses.add(match.psalm_verse_start)
            if match.psalm_verse_end and match.psalm_verse_end != match.psalm_verse_start:
                verses.add(match.psalm_verse_end)

        if not verses:
            return f"{psalm_chapter}:?"

        verses_sorted = sorted(list(verses))
        if len(verses_sorted) == 1:
            return f"{psalm_chapter}:{verses_sorted[0]}"
        else:
            return f"{psalm_chapter}:{verses_sorted[0]}-{verses_sorted[-1]}"

    def _format_content_used(self, match) -> str:
        """
        Format a description of what content from the psalm is used.

        Returns a string like:
        - "Entire Psalm 145"
        - "Psalm 23:3 (complete verse)"
        - "Phrase from Psalm 145:1-2"
        - "Verses 27:1-14"
        """
        if hasattr(match, 'psalm_phrase_hebrew') and match.psalm_phrase_hebrew == f"[Full Psalm {match.psalm_chapter}]":
            return f"Entire Psalm {match.psalm_chapter}"

        # Determine match type description
        if match.match_type == 'entire_chapter':
            return f"Entire Psalm {match.psalm_chapter}"
        elif match.match_type == 'exact_verse':
            if match.psalm_verse_start == match.psalm_verse_end or match.psalm_verse_end is None:
                return f"Psalm {match.psalm_chapter}:{match.psalm_verse_start} (complete verse)"
            else:
                return f"Verses {match.psalm_chapter}:{match.psalm_verse_start}-{match.psalm_verse_end} (complete)"
        elif match.match_type == 'verse_range':
            return f"Verses {match.psalm_chapter}:{match.psalm_verse_start}-{match.psalm_verse_end}"
        elif match.match_type == 'verse_set':
            # Get actual verse numbers from the phrase if available
            return f"Selected verses from Psalm {match.psalm_chapter}"
        elif match.match_type == 'phrase_match':
            # Show the actual Hebrew phrase
            phrase_excerpt = match.psalm_phrase_hebrew[:50] + '...' if len(match.psalm_phrase_hebrew) > 50 else match.psalm_phrase_hebrew
            if match.psalm_verse_start == match.psalm_verse_end or match.psalm_verse_end is None:
                return f"Phrase \"{phrase_excerpt}\" from Psalm {match.psalm_chapter}:{match.psalm_verse_start}"
            else:
                return f"Phrase \"{phrase_excerpt}\" from Psalm {match.psalm_chapter}:{match.psalm_verse_start}-{match.psalm_verse_end}"
        else:
            return f"Psalm {match.psalm_chapter}:{match.psalm_verse_start}"

    def _generate_phrase_llm_summary(
        self,
        psalm_phrase: str,
        psalm_verse_range: str,
        prayer_contexts: List[str],
        contexts: Dict[str, Any],
        total_count: int,
        matches: List[LiturgicalMatch]
    ) -> str:
        """
        Use LLM (Gemini 2.5 Pro or Claude Sonnet 4.5) to generate intelligent summary for a specific psalm phrase.

        This prompt is designed for PHRASE-level descriptions, not prayer-level.
        Uses canonical classification fields and location_description to understand context.
        """
        if not self.llm_provider:
            return self._generate_phrase_code_summary(psalm_phrase, prayer_contexts, contexts)

        # Build context description with match details
        context_lines = []
        context_lines.append(f"Psalm phrase: {psalm_phrase} (from verse {psalm_verse_range})")
        context_lines.append(f"Total occurrences: {total_count}")
        context_lines.append(f"Appears in {len(prayer_contexts)} distinct prayer contexts:")
        context_lines.append("")

        # Prioritize matches by type (full psalms first, then phrases)
        prioritized_matches = self._prioritize_matches_by_type(matches)

        # Provide detailed match information for LLM to analyze
        context_lines.append("Detailed matches (ordered by significance - full recitations first, phrases last):")
        for i, match in enumerate(prioritized_matches[:5], 1):  # Show up to 5 detailed matches
            context_lines.append(f"\nMatch {i}:")
            context_lines.append(f"  Source Text: {match.source_text}")
            context_lines.append(f"  Main prayer in this liturgical block: {match.canonical_prayer_name or 'N/A'}")
            context_lines.append(f"  Location Description: {match.canonical_location_description or 'N/A'}")
            context_lines.append(f"  L1 Occasion: {match.canonical_L1_Occasion or 'N/A'}")
            context_lines.append(f"  L2 Service: {match.canonical_L2_Service or 'N/A'}")
            context_lines.append(f"  L3 Signpost: {match.canonical_L3_Signpost or 'N/A'}")
            context_lines.append(f"  L4 SubSection: {match.canonical_L4_SubSection or 'N/A'}")
            context_lines.append(f"  Match Type: {match.match_type}")

            # Add match type context to help LLM understand significance
            if match.match_type == 'phrase_match':
                context_lines.append(f"  NOTE: This is a PHRASE excerpt, not full verse/psalm")
            elif match.match_type in ['entire_chapter', 'verse_range', 'verse_set']:
                context_lines.append(f"  NOTE: This is a FULL/SUBSTANTIAL recitation")

            # Increased from 500 to 1000 chars to provide more context for quotations (Session 131)
            context_lines.append(f"  Liturgy Context: {match.liturgy_context[:1000]}..." if len(match.liturgy_context) > 1000 else f"  Liturgy Context: {match.liturgy_context}")

        if len(prioritized_matches) > 15:
            remaining = len(prioritized_matches) - 15
            # Count remaining matches by type
            remaining_types = {}
            for m in prioritized_matches[15:]:
                remaining_types[m.match_type] = remaining_types.get(m.match_type, 0) + 1
            type_summary = ", ".join(f"{count} {mtype}" for mtype, count in remaining_types.items())
            context_lines.append(f"\n... and {remaining} more matches ({type_summary})")

        context_description = "\n".join(context_lines)

        prompt = f'''You are a scholarly liturgist writing for a Biblical commentary. Your task is to describe how a specific phrase from Psalms is used in Jewish liturgy.

PHRASE BEING ANALYZED:
{context_description}

YOUR TASK:
Write a 4-6 sentence scholarly narrative describing WHERE, WHEN, and HOW this phrase appears in Jewish liturgy. This should read like a paragraph from an academic commentary, NOT a list or data compilation.

CRITICAL REQUIREMENTS:

1. **NARRATIVE STYLE - NOT LISTS**
   - Write in flowing, scholarly prose
   - NO bullet points, NO "appears in X contexts:" format
   - Synthesize information into coherent paragraphs
   - Example: "The phrase appears throughout the Amidah in all traditions..." (GOOD)
   - NOT: "Appears in: Amidah (Ashkenaz), Amidah (Sefard)..." (BAD)

2. **DEDUPLICATE AND CONSOLIDATE**
   - "Amidah (Ashkenaz)" + "Amidah (Sefard)" + "Amidah (Edot_HaMizrach)"
     → "Amidah across all Jewish traditions"
   - "Menorah Lighting (Sefard) on Chanukah"
     → "Menorah Lighting ceremony in the Sefard rite during Chanukah"
   - Look for patterns and group intelligently

3. **PRIORITIZE BY MATCH TYPE**
   - The matches are ordered by significance: full psalm recitations first, then verse ranges, then phrases
   - If you see entire_chapter or verse_range matches, prioritize discussing those
   - Phrase matches are less significant - don't let them dominate the summary

4. **INCLUDE EXTENDED HEBREW QUOTATIONS (REQUIRED AND CRITICAL)**
   - **MANDATORY**: For phrase excerpts, you MUST include at least ONE extended Hebrew quotation
   - The quotation must show CONTEXT: include words BEFORE and AFTER the phrase itself
   - **Minimum**: At least 10-15 Hebrew words (not just repeating the 2-3 word phrase)
   - Extract from the "Liturgy Context" field provided for each match
   - **Example of GOOD quotation** (shows context around "הֲדַר כְּבוֹד הוֹדֶךָ"):
     "The liturgy states: 'בְּיַד נְבִיאֶיךָ בְּסוֹד עֲבָדֶיךָ. דִּמִּיתָ הֲדַר כְּבוֹד הוֹדֶךָ גְּדֻלָּתְךָ וּגְבוּרָתֶךָ'"
   - **Example of BAD quotation** (just the phrase): "The phrase 'הֲדַר כְּבוֹד הוֹדֶךָ' appears"
   - If multiple distinct usages exist, include AT LEAST one quotation, more if contexts are interesting/different
   - For full psalm recitations (entire_chapter): Mention the recitation without quoting the entire text
   - **Your summary will be REJECTED if it lacks proper extended quotations**

5. **USE CANONICAL CLASSIFICATION DATA**
   - L1 Occasion (Weekday/Shabbat/High Holidays/etc.)
   - L2 Service (Shacharit/Mincha/Maariv/Musaf/etc.)
   - L3 Signpost (Pesukei Dezimra/Amidah/Tachanun/etc.)
   - Location Description provides crucial context about composite blocks

6. **SYNTHESIS AND THINKING**
   - Identify liturgical patterns and their significance
   - Mention if usage varies by tradition (Ashkenaz vs. Sefard vs. Edot HaMizrach)
   - Note when phrase appears in special occasions vs. daily liturgy
   - Explain liturgical context where helpful

7. **READ LITURGY CONTEXT CAREFULLY**
   - The "Liturgy Context" field shows surrounding text
   - Use it to understand HOW the phrase is integrated
   - Extract representative quotes from there

8. **DISTINGUISH MAIN PRAYER VS. SUPPLEMENT** (CRITICAL):
   - The 'Main prayer in this liturgical block' field shows the primary prayer
   - The 'Location Description' explains the FULL structure of the block
   - A phrase/verse may be: (a) IN the main prayer itself, (b) in supplementary material BEFORE the main prayer, or (c) in supplementary material AFTER the main prayer

   **KEY PHRASES TO WATCH FOR**:
   - "This block begins with [Psalm X]... It is followed by [Main Prayer]"
     → The phrase is in a PRELUDE/INTRODUCTION, NOT in the main prayer
     → Say: "The phrase appears in Psalm X, which is recited as an introductory supplement before [Main Prayer]"
     → NOT: "The phrase appears in [Main Prayer]"

   - "After [Main Prayer], it includes [Psalm X]"
     → The phrase is in a CONCLUSION/SUPPLEMENT, NOT in the main prayer
     → Say: "The phrase appears in Psalm X, recited as a concluding supplement after [Main Prayer]"

   - "The phrase is found within [Prayer Name]" OR matches Main Prayer field
     → The phrase IS in the main prayer
     → Say: "The phrase appears within [Main Prayer]"

   **EXAMPLE (CORRECT)**:
   - Location: "This block begins with Psalms 1, 2, 3, and 4. It is followed by the complete Shir HaYichud..."
   - Main Prayer: "Shir HaYichud and Anim Zemirot"
   - Phrase from Psalm 1
   - CORRECT: "The phrase appears in Psalm 1, recited as an introductory supplement before Shir HaYichud on Yom Kippur night"
   - WRONG: "The phrase appears in Shir HaYichud"

GOOD EXAMPLE (4-6 sentences, narrative, with Hebrew quote):

The phrase 'כְּב֣וֹד מַלְכוּתְךָ֣' (the glory of Your kingdom) is prominently featured in the Kedushah section of the Amidah across all Jewish traditions during the Musaf service on Rosh Hashanah and Yom Kippur. In this context, the liturgy proclaims: 'אָבִֽינוּ מַלְכֵּֽנוּ גַּלֵּה כְּבוֹד מַלְכוּתְךָ עָלֵֽינוּ מְהֵרָה' ('Our Father, our King, reveal the glory of Your kingdom upon us swiftly'). The phrase also appears in the Sefard tradition's Menorah Lighting ceremony during Chanukah, where it emphasizes themes of divine sovereignty and revelation. Additionally, it features in various piyyutim (liturgical poems) during the High Holidays, reinforcing the petition for God's kingship to be manifest to all humanity.

BAD EXAMPLE (list-like, no quotes, too short):

The phrase 'כְּב֣וֹד מַלְכוּתְךָ֣' appears in 15 prayer contexts: Amidah (Ashkenaz), Amidah (Edot_HaMizrach), Kedushah (Ashkenaz), Menorah Lighting (Sefard), and 11 more. Occasions: Chanukah, Festivals, Yom Kippur. Services: Maariv, Mincha, Musaf, Neilah, Shacharit.

OUTPUT FORMAT:
Write ONLY the narrative paragraph (4-6 sentences). No preamble, no "Summary:" label, just the scholarly prose.'''

        if self.verbose:
            try:
                print(f"\n{'='*70}")
                print(f"LLM PROMPT FOR PHRASE: {psalm_phrase}")
                print(f"{'='*70}")
                print(prompt)
                print(f"{'='*70}\n")
            except UnicodeEncodeError:
                print(f"\n{'='*70}")
                print(f"LLM PROMPT FOR PHRASE: [Hebrew text - encoding error]")
                print(f"{'='*70}\n")

        # Get psalm chapter from matches for validation
        psalm_chapter = matches[0].psalm_chapter if matches else 0

        # Retry logic: Try up to 2 times if quality is poor or misattribution detected
        max_attempts = 2
        attempt = 0
        best_summary = None
        best_score = 0.0

        try:
            while attempt < max_attempts:
                attempt += 1

                # Call Gemini API with automatic retry for transient errors (429, network issues, etc.)
                response = self._call_gemini_with_retry(
                    prompt=prompt,
                    temperature=0.6,  # Increased from 0.3 for more synthesis/narrative flow
                    thinking_budget=self.thinking_budget
                )

                # Extract text from response - handle different response structures
                summary = None

                # Try method 1: response.text (simple access)
                if hasattr(response, 'text') and response.text:
                    summary = response.text.strip()

                # Try method 2: candidates structure
                if not summary and hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            # Extract from parts list
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    summary = part.text.strip()
                                    break

                if not summary:
                    raise ValueError(f"Could not extract text from response. Response type: {type(response)}, has text: {hasattr(response, 'text')}, has candidates: {hasattr(response, 'candidates')}")

                if self.verbose:
                    try:
                        print(f"\n{'='*70}")
                        print(f"LLM RESPONSE FOR PHRASE (Attempt {attempt}/{max_attempts}): {psalm_phrase}")
                        print(f"{'='*70}")
                        print(summary)
                        # Gemini token usage
                        if hasattr(response, 'usage_metadata'):
                            input_tokens = response.usage_metadata.prompt_token_count
                            output_tokens = response.usage_metadata.candidates_token_count
                            thinking_tokens = getattr(response.usage_metadata, 'thoughts_token_count', 0)
                            print(f"\nToken usage: {input_tokens} input, {output_tokens} output, {thinking_tokens} thinking")
                        print(f"{'='*70}\n")
                    except UnicodeEncodeError:
                        print(f"\n{'='*70}")
                        print(f"LLM RESPONSE FOR PHRASE (Attempt {attempt}/{max_attempts}): [Hebrew text - encoding error]")
                        if hasattr(response, 'usage_metadata'):
                            input_tokens = response.usage_metadata.prompt_token_count
                            output_tokens = response.usage_metadata.candidates_token_count
                            thinking_tokens = getattr(response.usage_metadata, 'thoughts_token_count', 0)
                            print(f"Token usage: {input_tokens} input, {output_tokens} output, {thinking_tokens} thinking")
                        print(f"{'='*70}\n")

                # Track usage and costs (Gemini)
                if hasattr(response, 'usage_metadata'):
                    input_tokens = response.usage_metadata.prompt_token_count
                    output_tokens = response.usage_metadata.candidates_token_count
                    thinking_tokens = getattr(response.usage_metadata, 'thoughts_token_count', 0)
                    self.cost_tracker.add_usage(
                        model="gemini-2.5-pro",
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        thinking_tokens=thinking_tokens
                    )

                # Validate summary quality
                quality_result = self._validate_summary_quality(summary, 'phrase', psalm_chapter)

                if self.verbose:
                    print(f"Quality validation: score={quality_result['score']:.2f}, valid={quality_result['is_valid']}")
                    if quality_result['issues']:
                        print(f"  Issues: {', '.join(quality_result['issues'])}")

                # Check for misattribution
                misattribution_result = self._check_for_misattribution(summary, psalm_chapter)

                if self.verbose and misattribution_result['is_misattributed']:
                    print(f"[WARNING] Possible misattribution detected!")
                    print(f"  Detected psalm: {misattribution_result['detected_psalm']}")
                    print(f"  Confidence: {misattribution_result['confidence']:.2f}")
                    print(f"  Reason: {misattribution_result['reason']}")

                # Track best summary (highest quality score)
                if quality_result['score'] > best_score:
                    best_score = quality_result['score']
                    best_summary = summary

                # If quality is good AND no misattribution, accept immediately
                if quality_result['is_valid'] and not misattribution_result['is_misattributed']:
                    if self.verbose:
                        print(f"[OK] Summary accepted (score={quality_result['score']:.2f})")
                    return summary

                # If misattribution detected with high confidence, reject and retry
                if misattribution_result['is_misattributed'] and misattribution_result['confidence'] >= 0.7:
                    if attempt < max_attempts:
                        if self.verbose:
                            print(f"[RETRY] Misattribution detected, retrying...")
                        continue
                    else:
                        if self.verbose:
                            print(f"[WARNING] Misattribution detected but max attempts reached, using best summary")
                        break

                # If quality is poor, retry once
                if not quality_result['is_valid'] and attempt < max_attempts:
                    if self.verbose:
                        print(f"[RETRY] Poor quality (score={quality_result['score']:.2f}), retrying...")
                    continue
                else:
                    # Either quality is acceptable or we've exhausted retries
                    break

            # Return best summary after all attempts
            if self.verbose and best_summary != summary:
                print(f"[OK] Using best summary from {attempt} attempts (score={best_score:.2f})")

            return best_summary if best_summary else summary

        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__

            if self.verbose:
                print(f"[DEBUG] Exception in phrase summary: {error_type}: {error_msg[:200]}")
                print(f"[DEBUG] Provider: {self.llm_provider}, Has Claude: {self.anthropic_client is not None}")

            # If Gemini failed and Claude available, switch to Claude
            if self.llm_provider == 'gemini' and self.anthropic_client:
                print(f"[WARNING] Gemini API error. Switching to Claude Sonnet 4.5 fallback.")
                print(f"[INFO] Error: {error_type}: {error_msg[:150]}")
                self.llm_provider = 'anthropic'
                # Retry with Claude
                try:
                    return self._generate_phrase_llm_summary_claude(psalm_phrase, psalm_verse_range, prayer_contexts, contexts, total_count, matches)
                except Exception as claude_error:
                    print(f"[WARNING] Claude also failed: {type(claude_error).__name__}: {str(claude_error)[:100]}")
                    # Fall through to code-only summary
            elif self.llm_provider == 'gemini':
                print(f"[WARNING] Gemini API error and no Claude fallback available. Using code-only summaries.")
                print(f"[INFO] Error: {error_type}: {error_msg[:150]}")
            else:
                print(f"[WARNING] LLM summarization failed ({error_type}: {error_msg[:100]}). Using code-only fallback.")

            # Fallback to code-only summary
            return self._generate_phrase_code_summary(psalm_phrase, prayer_contexts, contexts)

    def _generate_phrase_llm_summary_claude(
        self,
        psalm_phrase: str,
        psalm_verse_range: str,
        prayer_contexts: List[str],
        contexts: Dict[str, Any],
        total_count: int,
        matches: List[LiturgicalMatch]
    ) -> str:
        """
        Use Claude Sonnet 4.5 with extended thinking to generate intelligent summary (fallback when Gemini quota exhausted).
        """
        if not self.anthropic_client:
            return self._generate_phrase_code_summary(psalm_phrase, prayer_contexts, contexts)

        # Build same context as Gemini version
        context_lines = []
        context_lines.append(f"Psalm phrase: {psalm_phrase} (from verse {psalm_verse_range})")
        context_lines.append(f"Total occurrences: {total_count}")
        context_lines.append(f"Appears in {len(prayer_contexts)} distinct prayer contexts:")
        context_lines.append("")

        prioritized_matches = self._prioritize_matches_by_type(matches)

        context_lines.append("Detailed matches (ordered by significance - full recitations first, phrases last):")
        for i, match in enumerate(prioritized_matches[:15], 1):
            context_lines.append(f"\nMatch {i}:")
            context_lines.append(f"  Source Text: {match.source_text}")
            context_lines.append(f"  Main prayer in this liturgical block: {match.canonical_prayer_name or 'N/A'}")
            context_lines.append(f"  Location Description: {match.canonical_location_description or 'N/A'}")
            context_lines.append(f"  L1 Occasion: {match.canonical_L1_Occasion or 'N/A'}")
            context_lines.append(f"  L2 Service: {match.canonical_L2_Service or 'N/A'}")
            context_lines.append(f"  L3 Signpost: {match.canonical_L3_Signpost or 'N/A'}")
            context_lines.append(f"  L4 SubSection: {match.canonical_L4_SubSection or 'N/A'}")
            context_lines.append(f"  Match Type: {match.match_type}")
            if match.match_type == 'phrase_match':
                context_lines.append(f"  NOTE: This is a PHRASE excerpt, not full verse/psalm")
            elif match.match_type in ['entire_chapter', 'verse_range', 'verse_set']:
                context_lines.append(f"  NOTE: This is a FULL/SUBSTANTIAL recitation")
            context_lines.append(f"  Liturgy Context: {match.liturgy_context[:1000]}..." if len(match.liturgy_context) > 1000 else f"  Liturgy Context: {match.liturgy_context}")

        if len(prioritized_matches) > 15:
            remaining = len(prioritized_matches) - 15
            remaining_types = {}
            for m in prioritized_matches[15:]:
                remaining_types[m.match_type] = remaining_types.get(m.match_type, 0) + 1
            type_summary = ", ".join(f"{count} {mtype}" for mtype, count in remaining_types.items())
            context_lines.append(f"\n... and {remaining} more matches ({type_summary})")

        context_description = "\n".join(context_lines)

        # Use same prompt structure as Gemini (without extended thinking references)
        prompt = f'''You are a scholarly liturgist writing for a Biblical commentary. Your task is to describe how a specific phrase from Psalms is used in Jewish liturgy.

PHRASE BEING ANALYZED:
{context_description}

YOUR TASK:
Write a 4-6 sentence scholarly narrative describing WHERE, WHEN, and HOW this phrase appears in Jewish liturgy. This should read like a paragraph from an academic commentary, NOT a list or data compilation.

CRITICAL REQUIREMENTS:
1. NARRATIVE STYLE - Write in flowing scholarly prose, NO bullet points
2. DEDUPLICATE AND CONSOLIDATE - Group by tradition intelligently
3. PRIORITIZE BY MATCH TYPE - Full recitations first, phrases last
4. INCLUDE EXTENDED HEBREW QUOTATIONS - At least ONE 10-15 word quotation with context
5. USE CANONICAL CLASSIFICATION - L1 Occasion, L2 Service data
6. DISTINGUISH MAIN PRAYER VS. SUPPLEMENT - Note if phrase is in prelude/conclusion vs. main prayer

OUTPUT FORMAT:
Write ONLY the narrative paragraph (4-6 sentences). No preamble, no "Summary:" label.'''

        try:
            import anthropic
            # Use streaming with extended thinking (matches macro/micro analyst pattern)
            stream = self.anthropic_client.messages.stream(
                model="claude-sonnet-4-5",
                max_tokens=2000,  # Increased for Sonnet's more detailed output
                thinking={
                    "type": "enabled",
                    "budget_tokens": 5000  # Extended thinking for liturgical analysis
                },
                messages=[{"role": "user", "content": prompt}]
            )

            # Collect thinking and response from stream
            thinking_text = ""
            response_text = ""

            with stream as response_stream:
                for chunk in response_stream:
                    if hasattr(chunk, 'type'):
                        if chunk.type == 'content_block_delta':
                            if hasattr(chunk, 'delta'):
                                if hasattr(chunk.delta, 'type'):
                                    if chunk.delta.type == 'thinking_delta':
                                        thinking_text += chunk.delta.thinking
                                    elif chunk.delta.type == 'text_delta':
                                        response_text += chunk.delta.text

            summary = response_text.strip()

            # Track usage and costs (Claude)
            final_message = response_stream.get_final_message()
            if hasattr(final_message, 'usage'):
                usage = final_message.usage
                thinking_tokens = getattr(usage, 'thinking_tokens', 0) if hasattr(usage, 'thinking_tokens') else 0
                self.cost_tracker.add_usage(
                    model="claude-sonnet-4-5",
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                    thinking_tokens=thinking_tokens
                )

            if self.verbose:
                print(f"[INFO] Claude Sonnet 4.5 generated summary for phrase: {psalm_phrase[:50]}...")
                print(f"[INFO] Thinking tokens used: ~{len(thinking_text.split()) if thinking_text else 0}")

            return summary

        except Exception as e:
            print(f"[WARNING] Claude Sonnet summarization failed ({type(e).__name__}: {e}). Using code-only fallback.")
            return self._generate_phrase_code_summary(psalm_phrase, prayer_contexts, contexts)

    def _generate_phrase_code_summary(
        self,
        psalm_phrase: str,
        prayer_contexts: List[str],
        contexts: Dict[str, Any]
    ) -> str:
        """Generate code-based summary for a phrase (fallback or no-LLM mode)."""

        parts = [f"The phrase '{psalm_phrase}' appears in {len(prayer_contexts)} prayer context(s):"]
        parts.append(", ".join(prayer_contexts[:5]))
        if len(prayer_contexts) > 5:
            parts[-1] += f" (and {len(prayer_contexts) - 5} more)"

        if contexts['occasions']:
            parts.append(f"Occasions: {', '.join(contexts['occasions'])}")
        if contexts['services']:
            parts.append(f"Services: {', '.join(contexts['services'])}")

        return ". ".join(parts) + "."

    def _generate_full_psalm_summary(
        self,
        psalm_chapter: int,
        matches: List[LiturgicalMatch],
        prayer_contexts: List[str],
        contexts_data: Dict[str, Any]
    ) -> str:
        """
        Generate a summary for full/partial psalm recitations with verse coverage information.
        """
        # Collect verse coverage data AND location descriptions
        verse_coverage = {}
        location_descriptions = {}  # NEW: Track location descriptions
        psalm_verses = self._get_psalm_verses(psalm_chapter)
        total_verses = len(psalm_verses) if psalm_verses else 1 # Avoid division by zero

        for match in matches:
            prayer_name = match.canonical_prayer_name or "Unknown Prayer"

            percentage = 0
            verse_range = ""
            is_full = False

            if match.match_type == 'entire_chapter':
                percentage = 100
                verse_range = f"1-{total_verses}" if total_verses > 1 else "1"
                is_full = True
            elif match.match_type == 'verse_range':
                if match.psalm_verse_start and match.psalm_verse_end and total_verses > 0:
                    num_verses = match.psalm_verse_end - match.psalm_verse_start + 1
                    percentage = (num_verses / total_verses) * 100
                    verse_range = f"{match.psalm_verse_start}-{match.psalm_verse_end}"
                    is_full = percentage >= 80
            elif match.match_type == 'verse_set':
                if hasattr(match, 'locations') and match.locations:
                    try:
                        verses = json.loads(match.locations)
                        num_verses = len(verses)
                        if total_verses > 0:
                            percentage = (num_verses / total_verses) * 100
                        verse_range = self._format_verse_list(verses)
                        is_full = percentage >= 80
                    except (json.JSONDecodeError, TypeError):
                        pass # Keep default values
            elif match.match_type == 'exact_verse':
                if total_verses > 0:
                    percentage = (1 / total_verses) * 100
                verse_range = str(match.psalm_verse_start)
                is_full = False

            # To avoid duplicate prayer names in verse_coverage
            if prayer_name not in verse_coverage:
                verse_coverage[prayer_name] = {
                    'verses': verse_range,
                    'percentage': percentage,
                    'is_full': is_full
                }
                # NEW: Store location description
                location_descriptions[prayer_name] = match.canonical_location_description or ""

        # Use LLM for intelligent summary if available
        if self.gemini_client and len(matches) >= 1:
            # Enforce rate limiting before API call
            self._enforce_rate_limit()

            return self._generate_full_psalm_llm_summary(
                psalm_chapter, verse_coverage, prayer_contexts, contexts_data, location_descriptions
            )

        # Fallback code-only summary
        full_recitations = [p for p, data in verse_coverage.items() if data['is_full']]
        partial_recitations = [p for p, data in verse_coverage.items() if not data['is_full']]

        parts = []
        if full_recitations:
            parts.append(f"Full Psalm {psalm_chapter} recited in: {', '.join(full_recitations[:3])}")
            if len(full_recitations) > 3:
                parts.append(f"(and {len(full_recitations) - 3} more)")

        if partial_recitations:
            examples = []
            for prayer in partial_recitations[:2]:
                data = verse_coverage[prayer]
                examples.append(f"{prayer} (verses {data['verses']})")
            parts.append(f"Partial recitation in: {', '.join(examples)}")

        return ". ".join(parts) + "." if parts else f"Psalm {psalm_chapter} appears in {len(prayer_contexts)} prayer contexts."

    def _generate_full_psalm_llm_summary(
        self,
        psalm_chapter: int,
        verse_coverage: Dict[str, Dict],
        prayer_contexts: List[str],
        contexts_data: Dict[str, Any],
        location_descriptions: Dict[str, str] = None
    ) -> str:
        """
        Use LLM to generate an intelligent summary of full/partial psalm recitations.
        Uses canonical classification fields AND location descriptions for accurate liturgical placement.
        """
        location_descriptions = location_descriptions or {}

        # Build context description
        context_lines = []
        context_lines.append(f"Psalm {psalm_chapter} usage in Jewish liturgy:")
        context_lines.append(f"Total prayer contexts: {len(prayer_contexts)}")
        context_lines.append("")

        # Group by full vs. partial
        full_recitations = {p: d for p, d in verse_coverage.items() if d['is_full']}
        partial_recitations = {p: d for p, d in verse_coverage.items() if not d['is_full']}

        if full_recitations:
            context_lines.append(f"Full recitations ({len(full_recitations)}):")
            for prayer, data in list(full_recitations.items())[:5]:
                context_lines.append(f"  - Main Prayer: {prayer} (verses {data['verses']}, {data['percentage']:.0f}%)")
                # NEW: Include location description
                if prayer in location_descriptions and location_descriptions[prayer]:
                    context_lines.append(f"    Location Description: {location_descriptions[prayer][:300]}...")
            if len(full_recitations) > 5:
                context_lines.append(f"  ... and {len(full_recitations) - 5} more")

        if partial_recitations:
            context_lines.append(f"\nPartial recitations ({len(partial_recitations)}):")
            for prayer, data in list(partial_recitations.items())[:5]:
                context_lines.append(f"  - Main Prayer: {prayer} (verses {data['verses']}, {data['percentage']:.0f}%)")
                # NEW: Include location description
                if prayer in location_descriptions and location_descriptions[prayer]:
                    context_lines.append(f"    Location Description: {location_descriptions[prayer][:300]}...")
            if len(partial_recitations) > 5:
                context_lines.append(f"  ... and {len(partial_recitations) - 5} more")

        context_lines.append("")
        if contexts_data['occasions']:
            context_lines.append(f"L1 Occasions: {', '.join(contexts_data['occasions'])}")
        if contexts_data['services']:
            context_lines.append(f"L2 Services: {', '.join(contexts_data['services'])}")
        if contexts_data['nusachs']:
            context_lines.append(f"Traditions: {', '.join(contexts_data['nusachs'])}")

        context_description = "\n".join(context_lines)

        prompt = f'''You are a scholarly liturgist writing for a Biblical commentary. Your task is to describe where and how an entire Psalm is recited in Jewish liturgy.

PSALM BEING ANALYZED:
{context_description}

YOUR TASK:
Write a 4-6 sentence scholarly narrative describing WHERE, WHEN, and HOW this psalm is recited in Jewish liturgy. This should read like a paragraph from an academic commentary, NOT a list or data compilation.

CRITICAL REQUIREMENTS:

1. **NARRATIVE STYLE - NOT LISTS**
   - Write in flowing, scholarly prose
   - Synthesize information into coherent paragraphs
   - NO bullet points or "appears in:" format

2. **DISTINGUISH FULL VS. PARTIAL RECITATIONS**
   - Note if entire psalm is recited or just portions
   - Mention which verses if partial (use the verse coverage data)
   - Note: The indexer sometimes misses verses, so 80%+ coverage likely means full psalm

3. **DEDUPLICATE AND CONSOLIDATE**
   - Group by tradition and occasion intelligently
   - "Tachanun across all traditions" not "Tachanun (Ashkenaz), Tachanun (Sefard)..."

4. **USE CANONICAL CLASSIFICATION**
   - L1 Occasions and L2 Services are highly accurate
   - Provide specific liturgical placement
   - Mention when psalm appears (daily/weekly/seasonal)

5. **SYNTHESIS AND SIGNIFICANCE**
   - Explain liturgical context and meaning
   - Note variations by tradition if significant
   - Mention both regular and special occasion usage

6. **DISTINGUISH MAIN PRAYER VS. SUPPLEMENT** (CRITICAL):
   - The 'Main prayer in this liturgical block' field shows the primary prayer
   - The 'Location Description' explains the FULL structure of the block
   - A psalm may be: (a) THE main prayer itself, (b) supplementary material BEFORE the main prayer, or (c) supplementary material AFTER the main prayer

   **KEY PHRASES TO WATCH FOR**:
   - "This block begins with [Psalm X]... It is followed by [Main Prayer]"
     → Psalm X is a PRELUDE/INTRODUCTION, NOT part of the main prayer
     → Say: "Psalm X is recited as an introductory supplement before [Main Prayer]"
     → NOT: "Psalm X is incorporated into [Main Prayer]"

   - "After [Main Prayer], it includes [Psalm X]"
     → Psalm X is a CONCLUSION/SUPPLEMENT, NOT part of the main prayer
     → Say: "Psalm X is recited as a concluding supplement after [Main Prayer]"

   - "The psalm constitutes the core of [Prayer Name]" OR "Main prayer: [Psalm X]"
     → The psalm IS the main prayer
     → Say: "Psalm X forms the core of [Prayer Name]"

   **EXAMPLE (CORRECT)**:
   - Location: "This block begins with Psalms 1, 2, 3, and 4. It is followed by the complete Shir HaYichud..."
   - Main Prayer: "Shir HaYichud and Anim Zemirot"
   - CORRECT: "Psalm 1 is recited as an introductory supplement before Shir HaYichud on Yom Kippur night"
   - WRONG: "Psalm 1 is incorporated into Shir HaYichud"

GOOD EXAMPLE (narrative, informative):

"Psalm 27 is recited in its entirety during the penitential period from Rosh Chodesh Elul through Shemini Atzeret, appearing in both the morning (Shacharit) and evening (Maariv) services across all traditions. The psalm's themes of seeking God's presence ('One thing I ask of the Lord') make it particularly appropriate for this season of introspection and repentance. Edot HaMizrach communities also incorporate it into an extended Pesukei Dezimra on Shabbat and festivals. Individual verses, particularly verse 14 ('Hope in the Lord'), appear in composite prayer blocks after Aleinu and in High Holiday piyyutim within the Ashkenazic tradition."

OUTPUT FORMAT:
Write ONLY the narrative paragraph (4-6 sentences). No preamble, no "Summary:" label.'''

        if self.verbose:
            try:
                print(f"\n{'='*70}")
                print(f"LLM PROMPT FOR FULL PSALM {psalm_chapter}")
                print(f"{'='*70}")
                print(prompt)
                print(f"{'='*70}\n")
            except UnicodeEncodeError:
                print(f"\n{'='*70}")
                print(f"LLM PROMPT FOR FULL PSALM {psalm_chapter} [encoding error in prompt display]")
                print(f"{'='*70}\n")

        # Retry logic: Try up to 2 times if quality is poor or misattribution detected
        max_attempts = 2
        attempt = 0
        best_summary = None
        best_score = 0.0

        try:
            while attempt < max_attempts:
                attempt += 1

                # Call Gemini API with automatic retry for transient errors (429, network issues, etc.)
                response = self._call_gemini_with_retry(
                    prompt=prompt,
                    temperature=0.6,
                    thinking_budget=self.thinking_budget
                )

                # Extract text from response - handle different response structures
                summary = None

                # Try method 1: response.text (simple access)
                if hasattr(response, 'text') and response.text:
                    summary = response.text.strip()

                # Try method 2: candidates structure
                if not summary and hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            # Extract from parts list
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    summary = part.text.strip()
                                    break

                if not summary:
                    raise ValueError(f"Could not extract text from response. Response type: {type(response)}, has text: {hasattr(response, 'text')}, has candidates: {hasattr(response, 'candidates')}")

                if self.verbose:
                    try:
                        print(f"\n{'='*70}")
                        print(f"LLM RESPONSE FOR FULL PSALM {psalm_chapter} (Attempt {attempt}/{max_attempts})")
                        print(f"{'='*70}")
                        print(summary)
                        # Gemini token usage
                        if hasattr(response, 'usage_metadata'):
                            input_tokens = response.usage_metadata.prompt_token_count
                            output_tokens = response.usage_metadata.candidates_token_count
                            thinking_tokens = getattr(response.usage_metadata, 'thoughts_token_count', 0)
                            print(f"\nToken usage: {input_tokens} input, {output_tokens} output, {thinking_tokens} thinking")
                        print(f"{'='*70}\n")
                    except UnicodeEncodeError:
                        print(f"\n{'='*70}")
                        print(f"LLM RESPONSE FOR FULL PSALM {psalm_chapter} (Attempt {attempt}/{max_attempts}) [encoding error]")
                        if hasattr(response, 'usage_metadata'):
                            input_tokens = response.usage_metadata.prompt_token_count
                            output_tokens = response.usage_metadata.candidates_token_count
                            thinking_tokens = getattr(response.usage_metadata, 'thoughts_token_count', 0)
                            print(f"Token usage: {input_tokens} input, {output_tokens} output, {thinking_tokens} thinking")
                        print(f"{'='*70}\n")

                # Track usage and costs (Gemini)
                if hasattr(response, 'usage_metadata'):
                    input_tokens = response.usage_metadata.prompt_token_count
                    output_tokens = response.usage_metadata.candidates_token_count
                    thinking_tokens = getattr(response.usage_metadata, 'thoughts_token_count', 0)
                    self.cost_tracker.add_usage(
                        model="gemini-2.5-pro",
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        thinking_tokens=thinking_tokens
                    )

                # Validate summary quality
                quality_result = self._validate_summary_quality(summary, 'full_psalm', psalm_chapter)

                if self.verbose:
                    print(f"Quality validation: score={quality_result['score']:.2f}, valid={quality_result['is_valid']}")
                    if quality_result['issues']:
                        print(f"  Issues: {', '.join(quality_result['issues'])}")

                # Check for misattribution
                misattribution_result = self._check_for_misattribution(summary, psalm_chapter)

                if self.verbose and misattribution_result['is_misattributed']:
                    print(f"[WARNING] Possible misattribution detected!")
                    print(f"  Detected psalm: {misattribution_result['detected_psalm']}")
                    print(f"  Confidence: {misattribution_result['confidence']:.2f}")
                    print(f"  Reason: {misattribution_result['reason']}")

                # Track best summary (highest quality score)
                if quality_result['score'] > best_score:
                    best_score = quality_result['score']
                    best_summary = summary

                # If quality is good AND no misattribution, accept immediately
                if quality_result['is_valid'] and not misattribution_result['is_misattributed']:
                    if self.verbose:
                        print(f"[OK] Summary accepted (score={quality_result['score']:.2f})")
                    return summary

                # If misattribution detected with high confidence, reject and retry
                if misattribution_result['is_misattributed'] and misattribution_result['confidence'] >= 0.7:
                    if attempt < max_attempts:
                        if self.verbose:
                            print(f"[RETRY] Misattribution detected, retrying...")
                        continue
                    else:
                        if self.verbose:
                            print(f"[WARNING] Misattribution detected but max attempts reached, using best summary")
                        break

                # If quality is poor, retry once
                if not quality_result['is_valid'] and attempt < max_attempts:
                    if self.verbose:
                        print(f"[RETRY] Poor quality (score={quality_result['score']:.2f}), retrying...")
                    continue
                else:
                    # Either quality is acceptable or we've exhausted retries
                    break

            # Return best summary after all attempts
            if self.verbose and best_summary != summary:
                print(f"[OK] Using best summary from {attempt} attempts (score={best_score:.2f})")

            return best_summary if best_summary else summary

        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__

            if self.verbose:
                print(f"[DEBUG] Exception in full psalm summary: {error_type}: {error_msg[:200]}")
                print(f"[DEBUG] Provider: {self.llm_provider}, Has Claude: {self.anthropic_client is not None}")

            # If Gemini failed and Claude available, switch to Claude
            if self.llm_provider == 'gemini' and self.anthropic_client:
                print(f"[WARNING] Gemini API error. Switching to Claude Sonnet 4.5 fallback.")
                print(f"[INFO] Error: {error_type}: {error_msg[:150]}")
                self.llm_provider = 'anthropic'
                # Retry with Claude
                try:
                    return self._generate_full_psalm_llm_summary_claude(psalm_chapter, verse_coverage, prayer_contexts, contexts_data, location_descriptions)
                except Exception as claude_error:
                    print(f"[WARNING] Claude also failed: {type(claude_error).__name__}: {str(claude_error)[:100]}")
                    # Fall through to code-only summary
            elif self.llm_provider == 'gemini':
                print(f"[WARNING] Gemini API error and no Claude fallback available. Using code-only summaries.")
                print(f"[INFO] Error: {error_type}: {error_msg[:150]}")
            else:
                print(f"[WARNING] LLM summarization failed ({error_type}: {error_msg[:100]}). Using code-only fallback.")

            # Return code-only summary
            full_list = ', '.join(list(full_recitations.keys())[:3])
            partial_list = ', '.join([f"{p} (v. {d['verses']})" for p, d in list(partial_recitations.items())[:2]])
            parts = []
            if full_recitations:
                parts.append(f"Full Psalm {psalm_chapter}: {full_list}")
            if partial_recitations:
                parts.append(f"Partial: {partial_list}")
            return ". ".join(parts) + "." if parts else f"Psalm {psalm_chapter} in {len(prayer_contexts)} contexts"

    def _generate_full_psalm_llm_summary_claude(
        self,
        psalm_chapter: int,
        verse_coverage: Dict[str, Dict],
        prayer_contexts: List[str],
        contexts_data: Dict[str, Any],
        location_descriptions: Dict[str, str] = None
    ) -> str:
        """
        Use Claude Sonnet 4.5 with extended thinking to generate summary for full psalm (fallback when Gemini quota exhausted).
        """
        if not self.anthropic_client:
            # Fallback to code-only
            full_recitations = {p: d for p, d in verse_coverage.items() if d['is_full']}
            partial_recitations = {p: d for p, d in verse_coverage.items() if not d['is_full']}
            full_list = ', '.join(list(full_recitations.keys())[:3])
            partial_list = ', '.join([f"{p} (v. {d['verses']})" for p, d in list(partial_recitations.items())[:2]])
            parts = []
            if full_recitations:
                parts.append(f"Full Psalm {psalm_chapter}: {full_list}")
            if partial_recitations:
                parts.append(f"Partial: {partial_list}")
            return ". ".join(parts) + "." if parts else f"Psalm {psalm_chapter} in {len(prayer_contexts)} contexts"

        location_descriptions = location_descriptions or {}

        # Build same context as Gemini version
        context_lines = []
        context_lines.append(f"Psalm {psalm_chapter} usage in Jewish liturgy:")
        context_lines.append(f"Total prayer contexts: {len(prayer_contexts)}")
        context_lines.append("")

        full_recitations = {p: d for p, d in verse_coverage.items() if d['is_full']}
        partial_recitations = {p: d for p, d in verse_coverage.items() if not d['is_full']}

        if full_recitations:
            context_lines.append(f"Full recitations ({len(full_recitations)}):")
            for prayer, data in list(full_recitations.items())[:5]:
                context_lines.append(f"  - Main Prayer: {prayer} (verses {data['verses']}, {data['percentage']:.0f}%)")
                if prayer in location_descriptions and location_descriptions[prayer]:
                    context_lines.append(f"    Location Description: {location_descriptions[prayer][:300]}...")
            if len(full_recitations) > 5:
                context_lines.append(f"  ... and {len(full_recitations) - 5} more")

        if partial_recitations:
            context_lines.append(f"\nPartial recitations ({len(partial_recitations)}):")
            for prayer, data in list(partial_recitations.items())[:5]:
                context_lines.append(f"  - Main Prayer: {prayer} (verses {data['verses']}, {data['percentage']:.0f}%)")
                if prayer in location_descriptions and location_descriptions[prayer]:
                    context_lines.append(f"    Location Description: {location_descriptions[prayer][:300]}...")
            if len(partial_recitations) > 5:
                context_lines.append(f"  ... and {len(partial_recitations) - 5} more")

        context_lines.append("")
        if contexts_data['occasions']:
            context_lines.append(f"L1 Occasions: {', '.join(contexts_data['occasions'])}")
        if contexts_data['services']:
            context_lines.append(f"L2 Services: {', '.join(contexts_data['services'])}")
        if contexts_data['nusachs']:
            context_lines.append(f"Traditions: {', '.join(contexts_data['nusachs'])}")

        context_description = "\n".join(context_lines)

        # Use same prompt structure as Gemini
        prompt = f'''You are a scholarly liturgist writing for a Biblical commentary. Your task is to describe where and how an entire Psalm is recited in Jewish liturgy.

PSALM BEING ANALYZED:
{context_description}

YOUR TASK:
Write a 4-6 sentence scholarly narrative describing WHERE, WHEN, and HOW this psalm is recited in Jewish liturgy.

CRITICAL REQUIREMENTS:
1. NARRATIVE STYLE - Flowing scholarly prose, NO bullet points
2. DISTINGUISH FULL VS. PARTIAL RECITATIONS
3. DEDUPLICATE AND CONSOLIDATE - Group by tradition
4. USE CANONICAL CLASSIFICATION - L1 Occasions and L2 Services
5. SYNTHESIS AND SIGNIFICANCE - Explain liturgical context
6. DISTINGUISH MAIN PRAYER VS. SUPPLEMENT

OUTPUT FORMAT:
Write ONLY the narrative paragraph (4-6 sentences). No preamble, no "Summary:" label.'''

        try:
            import anthropic
            # Use streaming with extended thinking (matches macro/micro analyst pattern)
            stream = self.anthropic_client.messages.stream(
                model="claude-sonnet-4-5",
                max_tokens=2000,  # Increased for Sonnet's more detailed output
                thinking={
                    "type": "enabled",
                    "budget_tokens": 5000  # Extended thinking for liturgical analysis
                },
                messages=[{"role": "user", "content": prompt}]
            )

            # Collect thinking and response from stream
            thinking_text = ""
            response_text = ""

            with stream as response_stream:
                for chunk in response_stream:
                    if hasattr(chunk, 'type'):
                        if chunk.type == 'content_block_delta':
                            if hasattr(chunk, 'delta'):
                                if hasattr(chunk.delta, 'type'):
                                    if chunk.delta.type == 'thinking_delta':
                                        thinking_text += chunk.delta.thinking
                                    elif chunk.delta.type == 'text_delta':
                                        response_text += chunk.delta.text

            summary = response_text.strip()

            # Track usage and costs (Claude)
            final_message = response_stream.get_final_message()
            if hasattr(final_message, 'usage'):
                usage = final_message.usage
                thinking_tokens = getattr(usage, 'thinking_tokens', 0) if hasattr(usage, 'thinking_tokens') else 0
                self.cost_tracker.add_usage(
                    model="claude-sonnet-4-5",
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                    thinking_tokens=thinking_tokens
                )

            if self.verbose:
                print(f"[INFO] Claude Sonnet 4.5 generated summary for full Psalm {psalm_chapter}")
                print(f"[INFO] Thinking tokens used: ~{len(thinking_text.split()) if thinking_text else 0}")

            return summary

        except Exception as e:
            print(f"[WARNING] Claude Sonnet summarization failed ({type(e).__name__}: {e}). Using code-only fallback.")
            # Code-only fallback
            full_list = ', '.join(list(full_recitations.keys())[:3])
            partial_list = ', '.join([f"{p} (v. {d['verses']})" for p, d in list(partial_recitations.items())[:2]])
            parts = []
            if full_recitations:
                parts.append(f"Full Psalm {psalm_chapter}: {full_list}")
            if partial_recitations:
                parts.append(f"Partial: {partial_list}")
            return ". ".join(parts) + "." if parts else f"Psalm {psalm_chapter} in {len(prayer_contexts)} contexts"

    def _validate_summary_quality(self, summary: str, summary_type: str, psalm_chapter: int) -> Dict[str, Any]:
        """
        Validate the quality of an LLM-generated summary.

        Checks for common failure modes:
        - Too short / too long
        - List-like format instead of narrative
        - Missing Hebrew quotations (for phrase summaries)
        - Use of forbidden phrases ("appears in:", "Summary:")

        Returns:
            Dict with 'is_valid' (bool), 'score' (float), and 'issues' (list of strings)
        """
        issues = []
        score = 1.0

        # 1. Length check (approximate sentence count by splitting on '.')
        sentences = summary.split('.')
        num_sentences = len([s for s in sentences if len(s.strip()) > 5])
        if not (3 <= num_sentences <= 7):
            issues.append(f"Incorrect sentence count ({num_sentences})")
            score -= 0.2

        # 2. Check for list-like formats
        if any(line.strip().startswith('* ') or line.strip().startswith('- ') for line in summary.split('\n')):
            issues.append("Uses list format (bullet points)")
            score -= 0.5

        if "appears in:" in summary.lower() or "prayer contexts:" in summary.lower():
            issues.append("Uses list-like 'appears in:' format")
            score -= 0.4

        # 3. Check for forbidden preamble
        if summary.lower().strip().startswith("summary:"):
            issues.append("Contains 'Summary:' preamble")
            score -= 0.5

        # 4. Hebrew quotation check (critical for phrase summaries)
        if summary_type == 'phrase':
            import re
            hebrew_chars = re.findall(r'[\u0590-\u05FF]+', summary)
            if not hebrew_chars:
                issues.append("Missing required Hebrew quotation")
                score -= 0.7
            else:
                # Check if there is at least one long enough quotation
                longest_quote = max(hebrew_chars, key=len)
                # A word is roughly 5-6 chars, so 7 words is ~35-42 chars.
                # Let's check word count in the quote.
                quote_words = longest_quote.split()
                if len(quote_words) < 5:
                    issues.append(f"Hebrew quote is too short ({len(quote_words)} words)")
                    score -= 0.3

        # Final decision
        is_valid = score >= 0.5 and not any(crit in str(issues) for crit in ["Missing required Hebrew", "Uses list format"])

        return {
            'is_valid': is_valid,
            'score': max(0.0, score),
            'issues': issues
        }

    def _check_for_misattribution(self, summary: str, expected_psalm: int) -> Dict[str, Any]:
        """
        Placeholder for checking if the summary incorrectly attributes content
        to a different psalm.
        """
        return {
            'is_misattributed': False,
            'detected_psalm': None,
            'confidence': 0.0,
            'reason': ''
        }

    def _validate_phrase_groups_with_llm(
        self,
        grouped: Dict[str, List[LiturgicalMatch]],
        psalm_chapter: int
    ) -> tuple[Dict[str, List[LiturgicalMatch]], Dict[str, str]]:
        """
        Validate all phrase groups with LLM to filter false positives.

        Samples representative matches from each group and validates them.
        Filters out groups that fail validation.
        """
        validated_groups = {}
        validation_notes = {}
        filtered_count = 0

        for phrase_key, matches in grouped.items():
            # HEURISTIC PRE-FILTER: Check if Location Description explicitly mentions other psalms
            import re
            should_keep = True
            heuristic_reason = None

            for match in matches[:2]:  # Check first 2 matches
                loc_desc = match.canonical_location_description or ""
                # Look for "Psalm(s) X, Y, Z" or "Psalms X-Y" patterns where X != psalm_chapter
                psalm_mentions = re.findall(r'Psalms?\s+(\d+)(?:\s*[,\-]\s*(\d+))*', loc_desc)
                if psalm_mentions:
                    # Extract all mentioned psalm numbers
                    mentioned_psalms = set()
                    for match_tuple in psalm_mentions:
                        for num_str in match_tuple:
                            if num_str:
                                mentioned_psalms.add(int(num_str))

                    # If other psalms are mentioned but NOT our target psalm, likely a false positive
                    if mentioned_psalms and psalm_chapter not in mentioned_psalms:
                        other_psalms = sorted(mentioned_psalms)
                        heuristic_reason = f"Location Description mentions Psalms {other_psalms} but not Psalm {psalm_chapter}"
                        should_keep = False
                        if self.verbose:
                            print(f"[HEURISTIC FILTER] Phrase - {heuristic_reason}")
                        break

            if not should_keep:
                filtered_count += 1
                validation_notes[phrase_key] = f"FILTERED: {heuristic_reason}"
                continue  # Skip LLM validation for this group

            # Sample 1-2 representative matches for LLM validation
            sample_matches = matches[:min(2, len(matches))]

            # Generate verse range for context
            verse_range = self._format_verse_range(psalm_chapter, matches)

            # Validate each sample
            validations = []
            for match in sample_matches:
                validation = self._validate_phrase_match_with_llm(
                    psalm_phrase=phrase_key,
                    psalm_chapter=psalm_chapter,
                    psalm_verse_range=verse_range,
                    match=match
                )
                validations.append(validation)

            # Decision logic: Filter if ANY validation fails with moderate confidence
            should_keep = True
            for val in validations:
                # LOWERED THRESHOLD: Filter at 0.5 instead of 0.7 to catch more false positives
                if not val.is_valid and val.confidence >= 0.5:
                    if self.verbose:
                        try:
                            # phrase_key is a tuple, get the Hebrew text from first element
                            phrase_text = phrase_key[0] if isinstance(phrase_key, tuple) else phrase_key
                            print(f"[FILTERED] Phrase (len:{len(phrase_text)}) - {val.reason}")
                        except (UnicodeEncodeError, AttributeError):
                            print(f"[FILTERED] Phrase - {val.reason}")
                    should_keep = False
                    filtered_count += 1
                    validation_notes[phrase_key] = f"FILTERED: {val.reason}"
                    break
                elif not val.is_valid and val.confidence >= 0.3:
                    # Low confidence rejection - add warning but keep
                    if self.verbose:
                        try:
                            phrase_text = phrase_key[0] if isinstance(phrase_key, tuple) else phrase_key
                            print(f"[WARNING] Phrase (len:{len(phrase_text)}) - {val.reason}")
                        except (UnicodeEncodeError, AttributeError):
                            print(f"[WARNING] Phrase - {val.reason}")
                    validation_notes[phrase_key] = f"WARNING: {val.reason}"


            if should_keep:
                validated_groups[phrase_key] = matches

        if self.verbose:
            print(f"\n[OK] LLM Validation complete: {len(validated_groups)}/{len(grouped)} phrase groups kept ({filtered_count} filtered)")

        return validated_groups, validation_notes

    def _validate_phrase_match_with_llm(
        self,
        psalm_phrase: str,
        psalm_chapter: int,
        psalm_verse_range: str,
        match: LiturgicalMatch
    ) -> ValidationResult:
        """
        Use LLM to validate if a phrase match is really from **the target psalm**.

        Checks for:
        - Different psalm with same words
        - Context mismatch (unrelated text that happens to share words)
        - Provides liturgical context quote for valid matches

        Returns:
            ValidationResult with is_valid, confidence, reason, and optional quote/translation
        """
        if not self.gemini_client:
            # Without LLM, accept all matches
            return ValidationResult(
                is_valid=True,
                confidence=0.5,
                reason="No LLM available for validation"
            )

        # Get fuller context from database if needed
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT hebrew_text, canonical_prayer_name, canonical_location_description FROM prayers WHERE prayer_id = ?",
                (match.prayer_id,)
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                hebrew_text, prayer_name, location_desc = result
                # Use first 30000 chars of hebrew_text for context
                fuller_context = hebrew_text[:30000] if hebrew_text else match.liturgy_context
            else:
                fuller_context = match.liturgy_context
                prayer_name = "Unknown"
                location_desc = ""

        except Exception as e:
            if self.verbose:
                print(f"[WARNING] Could not fetch fuller context: {e}")
            fuller_context = match.liturgy_context
            prayer_name = "Unknown"
            location_desc = ""

        prompt = f'''You are a meticulous biblical scholar analyzing whether a liturgical text quotes from **Psalm {psalm_chapter}** or from a DIFFERENT biblical source.

**CRITICAL**: Many Hebrew phrases appear in MULTIPLE psalms. Your job is to determine which psalm the liturgy is ACTUALLY quoting.

**TARGET PSALM**: {psalm_chapter}
**SEARCHED PHRASE**: "{psalm_phrase}" (exists in Psalm {psalm_chapter}:{psalm_verse_range})

**EVIDENCE**:
- **Prayer Name**: {prayer_name or "Unknown"} ({match.nusach})
- **Main Prayer in this Liturgical Block**: {match.canonical_prayer_name or "N/A"}
- **Location Description**: {location_desc or 'N/A'}
- **Full Liturgy Text**:
```
{fuller_context[:20000]}
```

**ANALYSIS PROCEDURE** (follow these steps):

1. **CHECK FOR EXPLICIT PSALM MARKERS**:
   - Look for explicit psalm numbers in Hebrew (e.g., "מזמור קמה", "מזמור קמו", "תהלים קמה")
   - Look for psalm attribution phrases (e.g., "לדוד מזמור", "מזמור שיר")

2. **EXAMINE SURROUNDING VERSES**:
   - Read the verses BEFORE and AFTER the phrase in the liturgy
   - Compare them to Psalm {psalm_chapter} and other psalms
   - The phrase "ודרך רשעים" appears in BOTH Psalm 1:6 AND Psalm 146:9 - check which one matches the context
   - The phrase "הללי נפשי את ה'" is from Psalm 146:1, NOT Psalm 1

3. **USE THE LOCATION DESCRIPTION**:
   - The Location Description often explicitly states which psalms are in this block
   - Example: "begins with Psalms 1, 2, 3, and 4" means Psalm 1 IS present
   - Example: "followed by Psalms 146, 147, 148" means these psalms ARE present
   - Example: "includes Ashrei (Psalm 145)" means Psalm 145 IS present

4. **MAKE YOUR DETERMINATION**:
   - If the surrounding verses match Psalm {psalm_chapter}: `is_valid: true`, HIGH confidence (0.8-1.0)
   - If the surrounding verses match a DIFFERENT psalm: `is_valid: false`, HIGH confidence (0.8-1.0)
   - If you see explicit mention of a different psalm number: `is_valid: false`, MAXIMUM confidence (1.0)
   - If uncertain: LOW confidence (0.3-0.5)

**Respond in JSON format ONLY**:
```json
{{
  "is_valid": true/false,
  "confidence": 0.0-1.0,
  "reason": "Brief explanation with specific evidence (e.g., 'Surrounding verses are from Psalm 146:8-9, not Psalm 1')",
  "liturgy_quote": "Relevant Hebrew quote showing context",
  "translation": "English translation if helpful",
  "notes": "Additional context"
}}
```

**CRITICAL EXAMPLES**:
1. If searching for Psalm 1 and you see "ודרך רשעים יעות" with surrounding text "הללי נפשי את ה׳... יהוה שמר את גרים":
   → `is_valid: false`, `confidence: 0.95`, `reason: "This is Psalm 146:9 (context: verses 8-9), not Psalm 1:6"`

2. If searching for Psalm 145 and you see "הדר כבוד הודך" with Location Description saying "includes Ashrei (Psalm 145)":
   → `is_valid: true`, `confidence: 0.9`, `reason: "Location Description confirms Psalm 145 (Ashrei) is in this block"`

Output ONLY the JSON.'''

        if self.verbose:
            try:
                print(f"\n{'='*70}")
                print(f"LLM VALIDATION: Psalm {psalm_chapter}:{psalm_verse_range}")
                print(f"{'='*70}\n")
            except UnicodeEncodeError:
                pass  # Skip printing on Windows console with encoding issues

        try:
            # Import types for config
            from google.genai import types

            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=types.GenerateContentConfig(
                    # NOTE: max_output_tokens conflicts with thinking_config
                    temperature=0.1,  # Low temperature for factual validation
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=1024  # Lower budget for simple validation task
                    )
                )
            )

            # Extract text from response - handle different response structures
            result_text = None

            # Try method 1: response.text (simple access)
            if hasattr(response, 'text') and response.text:
                result_text = response.text.strip()

            # Try method 2: candidates structure
            if not result_text and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        # Extract from parts list
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                result_text = part.text.strip()
                                break

            if not result_text:
                raise ValueError(f"Could not extract text from validation response. Response type: {type(response)}")

            if self.verbose:
                try:
                    print(f"LLM Validation Result: {result_text[:200]}...")
                except UnicodeEncodeError:
                    pass  # Skip printing on Windows with encoding issues

            # Parse JSON response
            import json
            import re

            # Extract JSON from response (in case LLM adds extra text)
            json_match = re.search(r'{{.*}}', result_text, re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group(0))

                return ValidationResult(
                    is_valid=result_json.get("is_valid", True),
                    confidence=result_json.get("confidence", 0.7),
                    reason=result_json.get("reason", "LLM validation"),
                    liturgy_quote=result_json.get("liturgy_quote"),
                    translation=result_json.get("translation"),
                    notes=result_json.get("notes")
                )
            else:
                # Failed to parse JSON, assume valid
                return ValidationResult(
                    is_valid=True,
                    confidence=0.5,
                    reason="Could not parse LLM response"
                )

        except Exception as e:
            if self.verbose:
                print(f"[WARNING] LLM validation error: {e}")
            # On error, assume valid (conservative approach)
            return ValidationResult(
                is_valid=True,
                confidence=0.5,
                reason=f"Validation error: {str(e)}"
            )

    def _get_psalm_verses(self, psalm_chapter: int) -> Dict[int, str]:
        """
        Get all verses from a psalm chapter from the tanakh database.

        Returns:
            Dict mapping verse number to Hebrew text
        """
        try:
            conn = sqlite3.connect(self.tanakh_db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT verse, hebrew FROM verses WHERE book_name = ? AND chapter = ? ORDER BY verse",
                ('Psalms', psalm_chapter)
            )

            verses = {row[0]: row[1] for row in cursor.fetchall()}
            conn.close()
            return verses
        except Exception as e:
            if self.verbose:
                print(f"[WARNING] Error loading psalm verses: {e}")
            return {}

    def _normalize_hebrew_for_comparison(self, text: str) -> str:
        """
        Normalize Hebrew text for comparison by removing punctuation and standardizing whitespace.
        Preserves letters only.
        """
        import re
        # Remove cantillation marks (U+0591 to U+05AF)
        text = re.sub(r'[\u0591-\u05AF]', '', text)
        # Remove vowel points (U+05B0 to U+05BD, U+05BF to U+05C7)
        text = re.sub(r'[\u05B0-\u05BD\u05BF-\u05C7]', '', text)
        # Remove other marks like sof pasuq, geresh, gershayim
        text = re.sub(r'[\u05BE\u05C0\u05C3\u05F3\u05F4]', '', text)
        # Remove punctuation
        text = re.sub(r'[^\u05D0-\u05EA\s]', '', text)
        # Normalize whitespace
        text = ' '.join(text.split())
        return text.strip()

    def _count_meaningful_hebrew_words(self, text: str) -> int:
        """
        Count meaningful Hebrew words (excluding punctuation, markers, etc.).

        Filters out:
        - Single letters (like paragraph marker פ)
        - Punctuation marks
        - Cantillation and vowel points
        """
        import re

        # Remove cantillation marks, vowel points, and punctuation
        normalized = self._normalize_hebrew_for_comparison(text)

        # Split into words
        words = normalized.split()

        # Count words that are at least 2 Hebrew letters
        meaningful_words = [w for w in words if len(w) >= 2]

        return len(meaningful_words)

    def _format_verse_list(self, verses: List[int]) -> str:
        """
        Format a list of verse numbers as ranges (e.g., [1,2,3,5,6,7] -> "1-3, 5-7").
        """
        if not verses:
            return ""

        verses = sorted(verses)
        ranges = []
        start = verses[0]
        end = verses[0]

        for v in verses[1:]:
            if v == end + 1:
                end = v
            else:
                ranges.append(f"{start}-{end}" if start != end else str(start))
                start = v
                end = v

        ranges.append(f"{start}-{end}" if start != end else str(start))
        return ", ".join(ranges)

    def _merge_overlapping_phrase_groups(
        self,
        grouped: Dict[str, List[LiturgicalMatch]]
    ) -> Dict[str, List[LiturgicalMatch]]:
        """
        Merge phrase groups that appear in identical prayer contexts.

        If two phrases always appear together in the same contexts, they're likely
        part of the same continuous recitation and should be merged.
        """
        if not grouped:
            return grouped

        # Build context signatures for each phrase group
        phrase_contexts = {}
        for phrase, matches in grouped.items():
            # Create a signature based on prayer_ids
            prayer_ids = tuple(sorted(set(m.prayer_id for m in matches)))
            phrase_contexts[phrase] = prayer_ids

        # Find groups with identical contexts
        context_to_phrases = defaultdict(list)
        for phrase, context_sig in phrase_contexts.items():
            context_to_phrases[context_sig].append(phrase)

        # Merge groups with identical contexts
        merged = {}
        for context_sig, phrases in context_to_phrases.items():
            if len(phrases) == 1:
                # No merging needed
                phrase = phrases[0]
                merged[phrase] = grouped[phrase]
            else:
                # Merge multiple phrases that appear in same contexts
                # Create a merged key showing the verse range
                all_matches = []
                for phrase in phrases:
                    all_matches.extend(grouped[phrase])

                # Use the longest phrase as the representative
                longest_phrase = max(phrases, key=len)
                merged_key = f"{longest_phrase} [+ {len(phrases)-1} overlapping phrase(s)]"

                merged[merged_key] = all_matches

                if self.verbose:
                    print(f"[OK] Merged {len(phrases)} overlapping phrases into one entry")

        return merged

    def _prioritize_matches_by_type(self, matches: List[LiturgicalMatch]) -> List[LiturgicalMatch]:
        """
        Sort matches by match_type priority for LLM presentation.

        Priority order (highest to lowest):
        1. entire_chapter - full psalm recitations
        2. verse_range - multiple consecutive verses
        3. verse_set - multiple non-consecutive verses
        4. exact_verse - single complete verse
        5. phrase_match - partial verse excerpts

        This ensures LLM sees most significant usages first.

        Args:
            matches: List of liturgical matches to prioritize

        Returns:
            Sorted list with highest priority matches first
        """
        # Define priority scores (lower = higher priority)
        type_priority = {
            'entire_chapter': 1,
            'verse_range': 2,
            'verse_set': 3,
            'exact_verse': 4,
            'phrase_match': 5
        }

        # Sort by priority, then by confidence (higher confidence first)
        return sorted(
            matches,
            key=lambda m: (
                type_priority.get(m.match_type, 999),  # Unknown types go last
                -m.confidence  # Higher confidence first within same type
            )
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the liturgical index."""

        conn = self._get_db_connection()
        cursor = conn.cursor()

        stats = {}

        # Total matches
        cursor.execute("SELECT COUNT(*) FROM psalms_liturgy_index")
        stats['total_matches'] = cursor.fetchone()[0]

        # Unique Psalms indexed
        cursor.execute("SELECT COUNT(DISTINCT psalm_chapter) FROM psalms_liturgy_index")
        stats['psalms_indexed'] = cursor.fetchone()[0]

        # Matches by type
        cursor.execute('''
            SELECT match_type, COUNT(*)
            FROM psalms_liturgy_index
            GROUP BY match_type
        ''')
        stats['by_match_type'] = dict(cursor.fetchall())

        # Average confidence
        cursor.execute("SELECT AVG(confidence) FROM psalms_liturgy_index")
        stats['avg_confidence'] = round(cursor.fetchone()[0] or 0, 3)

        # Top Psalms by matches
        cursor.execute('''
            SELECT psalm_chapter, COUNT(*) as count
            FROM psalms_liturgy_index
            GROUP BY psalm_chapter
            ORDER BY count DESC
            LIMIT 10
        ''')
        stats['top_psalms'] = cursor.fetchall()

        # Unique prayers referenced
        cursor.execute('''
            SELECT COUNT(DISTINCT prayer_id)
            FROM psalms_liturgy_index
        ''')
        stats['unique_prayers'] = cursor.fetchone()[0]

        conn.close()
        return stats


# CLI for testing
def main():
    """Command-line interface for testing."""
    import sys
    import argparse

    # Configure UTF-8 output for Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Liturgical Librarian - Query phrase-level liturgical index',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Query Psalm 23 with LLM summaries (default)
  python src/agents/liturgical_librarian.py 23

  # Query specific verses
  python src/agents/liturgical_librarian.py 23 --verses 1 2 3

  # Disable LLM summaries
  python src/agents/liturgical_librarian.py 23 --skip-liturgy-llm

  # Show statistics
  python src/agents/liturgical_librarian.py --stats
        '''
    )

    parser.add_argument(
        'psalm',
        type=int,
        nargs='?',
        help='Psalm number (1-150)'
    )
    parser.add_argument(
        '--verses',
        type=int,
        nargs='+',
        help='Specific verses to query'
    )
    parser.add_argument(
        '--skip-liturgy-llm',
        action='store_true',
        help='Skip LLM summaries, use code-only aggregation'
    )
    parser.add_argument(
        '--min-confidence',
        type=float,
        default=0.75,
        help='Minimum confidence threshold (0.0-1.0)'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show database statistics'
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Include detailed raw matches in output'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show LLM prompts and responses (for debugging)'
    )

    args = parser.parse_args()

    # Initialize librarian
    use_llm = not args.skip_liturgy_llm
    librarian = LiturgicalLibrarian(use_llm_summaries=use_llm, verbose=args.verbose)

    if args.stats:
        print("\n" + "=" * 70)
        print("LITURGICAL INDEX STATISTICS")
        print("=" * 70 + "\n")

        stats = librarian.get_statistics()

        print(f"Total matches: {stats['total_matches']:,}")
        print(f"Psalms indexed: {stats['psalms_indexed']}/150")
        print(f"Unique prayers: {stats['unique_prayers']:,}")
        print(f"Average confidence: {stats['avg_confidence']:.3f}")

        print(f"\nBy match type:")
        for match_type, count in sorted(stats['by_match_type'].items()):
            pct = count / stats['total_matches'] * 100
            print(f"  {match_type.replace('_', ' ').title()}: {count:,} ({pct:.1f}%)")

        print(f"\nTop 10 Psalms by matches:")
        for psalm, count in stats['top_psalms']:
            print(f"  Psalm {psalm}: {count:,} matches")

        print()
        return

    if not args.psalm:
        parser.print_help()
        return

    # Query liturgical usage
    print("\n" + "=" * 70)
    verse_text = f" (verses {', '.join(map(str, args.verses))})" if args.verses else ""
    print(f"LITURGICAL USAGE: PSALM {args.psalm}{verse_text}")
    print("=" * 70)

    if use_llm:
        print("Using Claude Sonnet 4.5 for intelligent context summaries")
    else:
        print("Using code-only summaries (--skip-liturgy-llm)")

    print()

    # Get phrase-based results (NEW METHOD)
    results = librarian.find_liturgical_usage_by_phrase(
        psalm_chapter=args.psalm,
        psalm_verses=args.verses,
        min_confidence=args.min_confidence,
        include_raw_matches=args.detailed,
        separate_full_psalm=True
    )

    if not results:
        print("No liturgical usage found for this query.\n")
        return

    # Display results
    total_occurrences = sum(r.occurrence_count for r in results)
    print(f"Found {len(results)} distinct phrase(s) with {total_occurrences} total occurrence(s):\n")

    for i, match in enumerate(results, 1):
        # Header
        print(f"{i}. Phrase: {match.psalm_phrase_hebrew}")
        print(f"   Verse: {match.psalm_verse_range}")
        print(f"   Occurrences: {match.occurrence_count} across {match.unique_prayer_contexts} prayer context(s)")
        print(f"   Confidence: {int(match.confidence_avg * 100)}%")
        print()

        # LLM summary
        print(f"   {match.liturgical_summary}")
        print()

        # Prayer contexts (show first 10)
        print(f"   Prayer contexts:")
        for ctx in match.prayer_contexts[:10]:
            print(f"     - {ctx}")
        if len(match.prayer_contexts) > 10:
            print(f"     ... and {len(match.prayer_contexts) - 10} more")
        print()

        if args.detailed and match.raw_matches:
            print(f"   Raw matches ({len(match.raw_matches)}):")
            for j, raw in enumerate(match.raw_matches[:5], 1):  # Show first 5
                liturgy_excerpt = raw.liturgy_context[:60] + "..." if len(raw.liturgy_context) > 60 else raw.liturgy_context
                print(f"     {j}. {raw.canonical_prayer_name or raw.canonical_L3_signpost} ({raw.nusach})")
                print(f"        Context: {liturgy_excerpt}")
            if len(match.raw_matches) > 5:
                print(f"     ... and {len(match.raw_matches) - 5} more")
            print()

        print("-" * 70)
        print()

    # TODO: Update format_for_research_bundle for phrase-based results
    # print("=" * 70)
    # print("RESEARCH BUNDLE FORMAT:")
    # print("=" * 70)
    # print()
    # print(librarian.format_for_research_bundle(results, args.psalm, args.verses))
    # print()


if __name__ == "__main__":
    main()
