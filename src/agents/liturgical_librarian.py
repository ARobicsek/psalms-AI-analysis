"""
Liturgical Librarian - Phase 4 (Phrase-Level Index)

Queries the comprehensive phrase-level index (psalms_liturgy_index table)
with intelligent aggregation to prevent duplicate prayer contexts.

Features:
- Aggregates matches by prayer name (handles "Amidah" appearing 79x)
- Uses Claude Haiku 4.5 for intelligent context summarization
- Handles inconsistent metadata (e.g., "Avot" vs "Patriarchs")
- Provides both aggregated and detailed views

Usage:
    from src.agents.liturgical_librarian import LiturgicalLibrarian

    # With LLM summarization (default)
    librarian = LiturgicalLibrarian()
    results = librarian.find_liturgical_usage_aggregated(psalm_chapter=23, psalm_verses=[3])

    # Without LLM (code-only summaries)
    librarian = LiturgicalLibrarian(use_llm_summaries=False)
    results = librarian.find_liturgical_usage_aggregated(psalm_chapter=23)
"""

import sqlite3
import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from collections import defaultdict


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


@dataclass
class AggregatedPrayerMatch:
    """Aggregated match representing one prayer with multiple occurrences."""

    prayer_name: str
    occurrence_count: int
    representative_phrase: str
    representative_context: str
    contexts_summary: str
    confidence_avg: float
    match_types: List[str]

    # Metadata
    occasions: List[str]
    services: List[str]
    nusachs: List[str]
    sections: List[str]

    # Raw matches (for detailed view)
    raw_matches: Optional[List[LiturgicalMatch]] = None


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
        anthropic_api_key: Optional[str] = None,
        verbose: bool = False
    ):
        """
        Initialize Liturgical Librarian.

        Args:
            db_path: Path to liturgy database
            tanakh_db_path: Path to tanakh database (for psalm verse text)
            use_llm_summaries: Whether to use Claude Haiku for intelligent summaries
            verbose: Whether to print LLM prompts and responses
            anthropic_api_key: API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.db_path = db_path
        self.tanakh_db_path = tanakh_db_path
        self.use_llm_summaries = use_llm_summaries
        self.verbose = verbose
        self.anthropic_client = None

        # Initialize LLM client if needed
        if use_llm_summaries:
            try:
                from anthropic import Anthropic
                api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
                if not api_key:
                    print("[WARNING] ANTHROPIC_API_KEY not found. Falling back to code-only summaries.")
                    self.use_llm_summaries = False
                else:
                    self.anthropic_client = Anthropic(api_key=api_key)
            except ImportError:
                print("[WARNING] anthropic package not installed. Falling back to code-only summaries.")
                self.use_llm_summaries = False

    def find_liturgical_usage_aggregated(
        self,
        psalm_chapter: int,
        psalm_verses: Optional[List[int]] = None,
        min_confidence: float = 0.75,
        include_raw_matches: bool = False
    ) -> List[AggregatedPrayerMatch]:
        """
        Find liturgical usage with intelligent aggregation by prayer.

        This is the main method that solves the duplication problem.
        Instead of returning 79 separate Amidah entries, it returns ONE
        Amidah entry with a summary of all 79 contexts.

        Args:
            psalm_chapter: Psalm number (1-150)
            psalm_verses: Specific verses (None = entire chapter)
            min_confidence: Minimum confidence threshold (0.0-1.0)
            include_raw_matches: Include full list of raw matches in results

        Returns:
            List of aggregated prayer matches (one per unique prayer)
        """
        # 1. Get all raw matches from index
        raw_matches = self._get_raw_matches(
            psalm_chapter=psalm_chapter,
            psalm_verses=psalm_verses,
            min_confidence=min_confidence
        )

        if not raw_matches:
            return []

        # 2. Group by prayer (smart grouping handles variants)
        grouped = self._group_by_prayer(raw_matches)

        # 3. Create aggregated results
        aggregated_results = []

        for prayer_key, matches in grouped.items():
            # Extract metadata
            contexts_data = self._extract_contexts_metadata(matches)

            # Generate summary (LLM or code)
            if self.use_llm_summaries and len(matches) >= 3:
                summary = self._generate_llm_summary(
                    prayer_name=prayer_key,
                    contexts=contexts_data,
                    total_count=len(matches)
                )
            else:
                summary = self._generate_code_summary(contexts_data)

            # Build aggregated result
            aggregated_results.append(AggregatedPrayerMatch(
                prayer_name=prayer_key,
                occurrence_count=len(matches),
                representative_phrase=matches[0].liturgy_phrase_hebrew,
                representative_context=matches[0].liturgy_context,
                contexts_summary=summary,
                confidence_avg=sum(m.confidence for m in matches) / len(matches),
                match_types=list(set(m.match_type for m in matches)),
                occasions=sorted(set(m.occasion for m in matches if m.occasion)),
                services=sorted(set(m.service for m in matches if m.service)),
                nusachs=sorted(set(m.nusach for m in matches if m.nusach)),
                sections=sorted(set(m.section for m in matches if m.section)),
                raw_matches=matches if include_raw_matches else None
            ))

        # Sort by occurrence count (most common first)
        aggregated_results.sort(key=lambda x: x.occurrence_count, reverse=True)

        return aggregated_results

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

        # 2. Separate and verify full psalm recitations
        if separate_full_psalm:
            # Separate exact_verse matches (potential full psalm) from phrase_match (excerpts)
            potential_full = [m for m in raw_matches if m.match_type == 'exact_verse']
            phrase_matches = [m for m in raw_matches if m.match_type != 'exact_verse']

            # Verify full psalm matches (filter out false positives)
            full_psalm_matches = self._verify_full_psalm_matches(potential_full, psalm_chapter)

            # Get prayer_ids where full psalm is recited (to deduplicate phrases)
            full_psalm_prayer_ids = set(m.prayer_id for m in full_psalm_matches)

            # Filter out phrase matches from same contexts where full psalm is recited
            phrase_matches = [m for m in phrase_matches if m.prayer_id not in full_psalm_prayer_ids]
        else:
            phrase_matches = raw_matches
            full_psalm_matches = []

        # 3. Group by psalm phrase
        grouped = self._group_by_psalm_phrase(phrase_matches)

        # 4. Merge overlapping phrases (same prayer contexts)
        grouped = self._merge_overlapping_phrase_groups(grouped)

        # 4.5. LLM Validation Pass (if enabled)
        if self.use_llm_summaries and self.anthropic_client:
            grouped = self._validate_phrase_groups_with_llm(grouped, psalm_chapter)

        # 5. Create aggregated results for each phrase
        phrase_results = []

        for phrase_key, matches in grouped.items():
            # Extract metadata
            contexts_data = self._extract_contexts_metadata(matches)

            # Get unique prayer contexts
            prayer_contexts = self._extract_prayer_contexts(matches)

            # Generate verse range
            verse_range = self._format_verse_range(psalm_chapter, matches)

            # Generate summary (LLM or code)
            if self.use_llm_summaries and len(matches) >= 3:
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
                representative_liturgy_context=matches[0].liturgy_context[:200] + "...",
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

            # Determine actual verse range from found_verses (show range of all verses found)
            all_found_verses = []
            for m in full_psalm_matches:
                if hasattr(m, 'found_verses') and m.found_verses:
                    all_found_verses.extend(m.found_verses)

            if all_found_verses:
                unique_verses = sorted(set(all_found_verses))
                verse_range_str = self._format_verse_list(unique_verses)
                psalm_verse_range = f"{psalm_chapter}:{verse_range_str}"
            else:
                psalm_verse_range = f"{psalm_chapter}:1-end"

            phrase_results.append(PhraseUsageMatch(
                psalm_phrase_hebrew=f"[Full Psalm {psalm_chapter}]",
                psalm_verse_range=psalm_verse_range,
                phrase_length=0,  # Full psalm
                occurrence_count=len(full_psalm_matches),
                unique_prayer_contexts=len(prayer_contexts),
                prayer_contexts=prayer_contexts,
                occasions=contexts_data['occasions'],
                services=contexts_data['services'],
                nusachs=contexts_data['nusachs'],
                sections=contexts_data['sections'],
                liturgical_summary=summary,
                confidence_avg=sum(m.confidence for m in full_psalm_matches) / len(full_psalm_matches),
                match_types=['exact_verse'],
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

        conn = sqlite3.connect(self.db_path)
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
                    p.prayer_id,
                    p.prayer_name,
                    p.source_text,
                    p.sefaria_ref,
                    p.nusach,
                    p.prayer_type,
                    p.occasion,
                    p.service,
                    p.section
                FROM psalms_liturgy_index i
                JOIN prayers p ON i.prayer_id = p.prayer_id
                WHERE i.psalm_chapter = ?
                  AND i.confidence >= ?
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
                    p.prayer_id,
                    p.prayer_name,
                    p.source_text,
                    p.sefaria_ref,
                    p.nusach,
                    p.prayer_type,
                    p.occasion,
                    p.service,
                    p.section
                FROM psalms_liturgy_index i
                JOIN prayers p ON i.prayer_id = p.prayer_id
                WHERE i.psalm_chapter = ?
                  AND ({verse_conditions})
                  AND i.confidence >= ?
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
                prayer_id=row[10],
                prayer_name=row[11],
                source_text=row[12],
                sefaria_ref=row[13],
                nusach=row[14],
                prayer_type=row[15],
                occasion=row[16],
                service=row[17],
                section=row[18]
            ))

        conn.close()
        return matches

    def _group_by_prayer(self, matches: List[LiturgicalMatch]) -> Dict[str, List[LiturgicalMatch]]:
        """
        Group matches by prayer name with smart normalization.

        Handles variants like:
        - "Patriarchs" vs "Avot" -> same prayer
        - "Amidah" vs "Amida" -> same prayer
        - None/empty -> use section or "Unknown"
        """
        grouped = defaultdict(list)

        for match in matches:
            # Determine grouping key
            key = self._get_prayer_grouping_key(match)
            grouped[key].append(match)

        return dict(grouped)

    def _get_prayer_grouping_key(self, match: LiturgicalMatch) -> str:
        """
        Generate a normalized grouping key for a prayer match.

        This handles naming inconsistencies:
        - Uses prayer_name if available
        - Falls back to section if prayer_name is None/empty
        - Normalizes common variants
        """
        # Start with prayer_name
        if match.prayer_name and match.prayer_name.strip():
            key = match.prayer_name.strip()
        elif match.section and match.section.strip():
            key = match.section.strip()
        else:
            key = "Unknown Prayer"

        # Normalize common variants (case-insensitive)
        key_lower = key.lower()

        # Amidah variants
        if 'amida' in key_lower or 'amidah' in key_lower:
            key = "Amidah"

        # Patriarchs/Avot variants
        if 'patriarch' in key_lower or 'avot' in key_lower or 'avos' in key_lower:
            # Check if it's part of Amidah
            if match.section and 'amida' in match.section.lower():
                key = "Amidah - Patriarchs"
            else:
                key = "Patriarchs"

        # Magen Avot
        if 'magen avot' in key_lower:
            key = "Magen Avot"

        return key

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

    def _generate_llm_summary(
        self,
        prayer_name: str,
        contexts: Dict[str, Any],
        total_count: int
    ) -> str:
        """
        Use Claude Haiku 4.5 to generate intelligent context summary.

        Handles inconsistent metadata and generates natural language descriptions.
        """

        if not self.anthropic_client:
            return self._generate_code_summary(contexts)

        # Build context description
        context_lines = []
        if contexts['occasions']:
            context_lines.append(f"Occasions: {', '.join(contexts['occasions'])}")
        if contexts['services']:
            context_lines.append(f"Services: {', '.join(contexts['services'])}")
        if contexts['nusachs']:
            context_lines.append(f"Traditions (nusach): {', '.join(contexts['nusachs'])}")
        if contexts['sections']:
            context_lines.append(f"Sections: {', '.join(contexts['sections'])}")
        if contexts['prayer_types']:
            context_lines.append(f"Types: {', '.join(contexts['prayer_types'])}")

        context_description = "\n".join(context_lines) if context_lines else "Limited metadata available"

        prompt = f"""You are summarizing liturgical contexts for a scholarly Biblical commentary tool.

Prayer/Section: {prayer_name}
Number of occurrences: {total_count}

Liturgical contexts:
{context_description}

Generate a concise 1-2 sentence summary describing WHERE and WHEN this text appears in Jewish liturgy.

Guidelines:
- Identify patterns (e.g., "all daily services" instead of listing each)
- Be specific about occasions (Weekday, Shabbat, High Holidays, etc.)
- Mention traditions (Ashkenaz, Sefard, Edot HaMizrach) if relevant
- Handle inconsistent naming (e.g., "Amida" = "Amidah", "Avot" = "Patriarchs")
- Focus on liturgical significance, not just data listing
- Keep it concise and scholarly

Example output: "Appears in the Patriarchs blessing of the Amidah across all daily services (Shacharit, Mincha, Maariv), Shabbat, and High Holidays (Rosh Hashanah and Yom Kippur), in Ashkenaz, Sefard, and Edot HaMizrach traditions."

Output only the summary, no preamble or explanation."""

        if self.verbose:
            print(f"\n{'='*70}")
            print(f"LLM PROMPT FOR: {prayer_name}")
            print(f"{'='*70}")
            print(prompt)
            print(f"{'='*70}\n")

        try:
            response = self.anthropic_client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=300,
                temperature=0.3,  # Fairly deterministic
                messages=[{"role": "user", "content": prompt}]
            )

            summary = response.content[0].text.strip()

            if self.verbose:
                print(f"\n{'='*70}")
                print(f"LLM RESPONSE FOR: {prayer_name}")
                print(f"{'='*70}")
                print(summary)
                print(f"\nToken usage: {response.usage.input_tokens} input, {response.usage.output_tokens} output")
                print(f"{'='*70}\n")

            # Track usage for cost monitoring (optional)
            # Could log: response.usage.input_tokens, response.usage.output_tokens

            return summary

        except Exception as e:
            print(f"[WARNING] LLM summarization failed ({e}). Using code-only fallback.")
            return self._generate_code_summary(contexts)

    def _generate_code_summary(self, contexts: Dict[str, Any]) -> str:
        """Generate summary using pure code (fallback or no-LLM mode)."""

        parts = []

        if contexts['occasions']:
            parts.append(f"Occasions: {', '.join(contexts['occasions'])}")
        if contexts['services']:
            parts.append(f"Services: {', '.join(contexts['services'])}")
        if contexts['nusachs']:
            parts.append(f"Traditions: {', '.join(contexts['nusachs'])}")
        if contexts['sections']:
            parts.append(f"Sections: {', '.join(contexts['sections'])}")

        if parts:
            return f"Appears in {contexts['total_count']} contexts. " + "; ".join(parts) + "."
        else:
            return f"Appears in {contexts['total_count']} liturgical contexts (limited metadata)."

    def format_for_research_bundle(
        self,
        aggregated_matches: List[AggregatedPrayerMatch],
        psalm_chapter: int,
        psalm_verses: Optional[List[int]] = None
    ) -> str:
        """
        Format aggregated matches for research bundle (optimized for AI agents).

        Returns:
            Markdown-formatted section for research bundle
        """

        if not aggregated_matches:
            verse_text = f" (verse{'s' if psalm_verses and len(psalm_verses) > 1 else ''} {', '.join(map(str, psalm_verses))})" if psalm_verses else ""
            return f"## Liturgical Usage\n\nNo liturgical usage found for Psalm {psalm_chapter}{verse_text}.\n"

        # Build header
        verse_text = f" - Verse{'s' if psalm_verses and len(psalm_verses) > 1 else ''} {', '.join(map(str, psalm_verses))}" if psalm_verses else ""
        total_occurrences = sum(m.occurrence_count for m in aggregated_matches)

        output = [f"## Liturgical Usage: Psalm {psalm_chapter}{verse_text}\n"]
        output.append(f"This passage appears in **{len(aggregated_matches)} distinct prayer(s)** "
                     f"with **{total_occurrences} total occurrence(s)** in the liturgy:\n")

        # Format each prayer
        for i, match in enumerate(aggregated_matches, 1):
            output.append(f"### {i}. {match.prayer_name}")

            if match.occurrence_count > 1:
                output.append(f"**Occurrences**: {match.occurrence_count} contexts")

            output.append(f"**Phrase in liturgy**: {match.representative_phrase}")

            if match.representative_context:
                # Truncate very long contexts
                context = match.representative_context
                if len(context) > 200:
                    context = context[:197] + "..."
                output.append(f"**Context**: {context}")

            # LLM-generated summary
            output.append(f"**Where it appears**: {match.contexts_summary}")

            # Confidence and match quality
            confidence_pct = int(match.confidence_avg * 100)
            output.append(f"**Confidence**: {confidence_pct}% (Match type: {', '.join(match.match_types)})")

            output.append("")  # Blank line between prayers

        return "\n".join(output)

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

    def _group_by_psalm_phrase(self, matches: List[LiturgicalMatch]) -> Dict[str, List[LiturgicalMatch]]:
        """
        Group matches by psalm phrase (the phrase from the psalm).

        This creates one group per unique phrase from the psalm that appears in liturgy.
        Filters out phrases with <2 meaningful words.
        """
        grouped = defaultdict(list)

        for match in matches:
            # Filter out phrases with <2 meaningful words (like "פ" or single letters)
            word_count = self._count_meaningful_hebrew_words(match.psalm_phrase_hebrew)
            if word_count < 2:
                if self.verbose:
                    print(f"[FILTER] Phrase with <2 words (length: {len(match.psalm_phrase_hebrew)} chars, {word_count} words)")
                continue

            # Use the psalm phrase as the key
            key = match.psalm_phrase_hebrew.strip()
            grouped[key].append(match)

        return dict(grouped)

    def _extract_prayer_contexts(self, matches: List[LiturgicalMatch]) -> List[str]:
        """
        Extract unique prayer context descriptions from matches.

        Returns a list like: ["Amidah - Patriarchs (Ashkenaz)", "Shabbat Kiddush (Sefard)", ...]
        """
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
        Use Claude Haiku to generate intelligent summary for a specific psalm phrase.

        This prompt is designed for PHRASE-level descriptions, not prayer-level.
        Includes hebrew_text context and requests quotes/translations for phrase excerpts.
        """
        if not self.anthropic_client:
            return self._generate_phrase_code_summary(psalm_phrase, prayer_contexts, contexts)

        # Get hebrew_text from a representative match (first one)
        representative_hebrew_text = ""
        if matches:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT hebrew_text FROM prayers WHERE prayer_id = ?",
                    (matches[0].prayer_id,)
                )
                result = cursor.fetchone()
                conn.close()

                if result and result[0]:
                    representative_hebrew_text = result[0][:30000]  # Use first 30000 chars
            except Exception as e:
                if self.verbose:
                    print(f"[WARNING] Could not fetch hebrew_text for summary: {e}")

        # Build context description
        context_lines = []
        context_lines.append(f"Psalm phrase: {psalm_phrase} (from verse {psalm_verse_range})")
        context_lines.append(f"Total occurrences: {total_count}")
        context_lines.append(f"Appears in {len(prayer_contexts)} distinct prayer contexts:")

        # Show up to 10 prayer contexts
        for ctx in prayer_contexts[:10]:
            context_lines.append(f"  - {ctx}")
        if len(prayer_contexts) > 10:
            context_lines.append(f"  ... and {len(prayer_contexts) - 10} more")

        context_lines.append("")
        if contexts['occasions']:
            context_lines.append(f"Occasions: {', '.join(contexts['occasions'])}")
        if contexts['services']:
            context_lines.append(f"Services: {', '.join(contexts['services'])}")
        if contexts['nusachs']:
            context_lines.append(f"Traditions: {', '.join(contexts['nusachs'])}")
        if contexts['sections']:
            context_lines.append(f"Sections: {', '.join(contexts['sections'])}")

        # Add hebrew text context if available
        if representative_hebrew_text:
            context_lines.append("")
            context_lines.append("Representative Hebrew text from prayer:")
            context_lines.append("```")
            context_lines.append(representative_hebrew_text[:10000])  # Show 10000 chars in prompt
            if len(representative_hebrew_text) > 10000:
                context_lines.append("... [text continues]")
            context_lines.append("```")

        context_description = "\n".join(context_lines)

        prompt = f"""You are summarizing liturgical usage for a scholarly Biblical commentary tool.

You are analyzing where a SPECIFIC PHRASE from a psalm appears in Jewish liturgy.

{context_description}

Generate a concise 2-3 sentence summary describing WHERE and WHEN this specific phrase appears in Jewish liturgy.

IMPORTANT: For phrase excerpts (not full verses), please provide:
1. **A brief quote from the liturgy showing how the phrase is used (2-3 sentences in Hebrew) for EACH context where it appears.**
2. An English translation of that quote
3. Explanation of the context in whichit appears liturgically

Guidelines:
- Start by mentioning the phrase itself (in transliteration if possible)
- Identify patterns in where it appears (e.g., "appears in the Patriarchs blessing across all services")
- Be specific about occasions (Weekday, Shabbat, High Holidays, etc.)
- Mention traditions (Ashkenaz, Sefard, Edot HaMizrach) if relevant
- Group related contexts (e.g., "appears in the Amidah for daily services" not "Amidah Shacharit, Amidah Mincha, Amidah Maariv")
- For phrase excerpts: **Include a representative quote and translation showing liturgical context**
- Focus on liturgical significance
- Keep it concise and scholarly

Example output: "The phrase 'למען שמו' (l'ma'an shemo, 'for His name's sake') appears in the Patriarchs (Avot) blessing of the Amidah, recited in all daily services (Shacharit, Mincha, and Maariv) as well as Musaf and Neilah. The Amidah blessing reads: 'ברוך אתה ה׳ אלוהי אברהם אלוהי יצחק ואלוהי יעקב... ומביא גואל לבני בניהם למען שמו באהבה' ('Blessed are You, Lord our God of Abraham, God of Isaac, and God of Jacob... who brings a redeemer to their children's children for His name's sake with love'). It also appears in various Selichot and in the Edot HaMizrach liturgy for the Sounding of the Shofar."

Output only the summary, no preamble."""

        if self.verbose:
            print(f"\n{'='*70}")
            print(f"LLM PROMPT FOR PHRASE: {psalm_phrase}")
            print(f"{'='*70}")
            print(prompt)
            print(f"{'='*70}\n")

        try:
            response = self.anthropic_client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=400,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            summary = response.content[0].text.strip()

            if self.verbose:
                print(f"\n{'='*70}")
                print(f"LLM RESPONSE FOR PHRASE: {psalm_phrase}")
                print(f"{'='*70}")
                print(summary)
                print(f"\nToken usage: {response.usage.input_tokens} input, {response.usage.output_tokens} output")
                print(f"{'='*70}\n")

            return summary

        except Exception as e:
            print(f"[WARNING] LLM summarization failed ({e}). Using code-only fallback.")
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
        # Collect verse coverage data
        verse_coverage = {}
        for match in matches:
            prayer_name = match.prayer_name or "Unknown Prayer"
            if hasattr(match, 'found_verses') and match.found_verses:
                verse_range = self._format_verse_list(match.found_verses)
                percentage = getattr(match, 'found_percentage', 0)
                verse_coverage[prayer_name] = {
                    'verses': verse_range,
                    'percentage': percentage,
                    'is_full': percentage >= 80
                }

        # Use LLM for intelligent summary if available
        if self.anthropic_client and len(matches) >= 2:
            return self._generate_full_psalm_llm_summary(
                psalm_chapter, verse_coverage, prayer_contexts, contexts_data
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
        contexts_data: Dict[str, Any]
    ) -> str:
        """
        Use LLM to generate an intelligent summary of full/partial psalm recitations.
        """
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
                context_lines.append(f"  - {prayer} (verses {data['verses']}, {data['percentage']:.0f}%)")
            if len(full_recitations) > 5:
                context_lines.append(f"  ... and {len(full_recitations) - 5} more")

        if partial_recitations:
            context_lines.append(f"\nPartial recitations ({len(partial_recitations)}):")
            for prayer, data in list(partial_recitations.items())[:5]:
                context_lines.append(f"  - {prayer} (verses {data['verses']}, {data['percentage']:.0f}%)")
            if len(partial_recitations) > 5:
                context_lines.append(f"  ... and {len(partial_recitations) - 5} more")

        context_lines.append("")
        if contexts_data['occasions']:
            context_lines.append(f"Occasions: {', '.join(contexts_data['occasions'])}")
        if contexts_data['services']:
            context_lines.append(f"Services: {', '.join(contexts_data['services'])}")
        if contexts_data['nusachs']:
            context_lines.append(f"Traditions: {', '.join(contexts_data['nusachs'])}")

        context_description = "\n".join(context_lines)

        prompt = f"""You are summarizing liturgical usage for a scholarly Biblical commentary tool.

You are analyzing where Psalm {psalm_chapter} is recited (fully or partially) in Jewish liturgy.

{context_description}

Generate a concise 2-3 sentence summary describing WHERE and WHEN this psalm is recited in Jewish liturgy.

Guidelines:
- Distinguish between full recitations and partial verses used
- Mention which verses are used if partial
- Identify patterns in occasions (Weekday, Shabbat, Festivals, etc.)
- Mention traditions (Ashkenaz, Sefard, Edot HaMizrach) if relevant
- Focus on liturgical significance
- Keep it concise and scholarly

Example output: "Psalm 23 is recited in its entirety in the Shabbat afternoon Shalosh Seudos (Third Meal) across all traditions. Verse 3 ('for His name's sake') is incorporated into the Amidah's Patriarchs blessing for all daily services. Additionally, verses 2-4 appear in Sefardic Shabbat Zemirot and Kiddush."

Output only the summary, no preamble."""

        if self.verbose:
            print(f"\n{'='*70}")
            print(f"LLM PROMPT FOR FULL PSALM {psalm_chapter}")
            print(f"{'='*70}")
            print(prompt)
            print(f"{'='*70}\n")

        try:
            response = self.anthropic_client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            summary = response.content[0].text.strip()

            if self.verbose:
                print(f"\n{'='*70}")
                print(f"LLM RESPONSE FOR FULL PSALM {psalm_chapter}")
                print(f"{'='*70}")
                print(summary)
                print(f"\nToken usage: {response.usage.input_tokens} input, {response.usage.output_tokens} output")
                print(f"{'='*70}\n")

            return summary

        except Exception as e:
            if self.verbose:
                print(f"[WARNING] LLM summarization failed ({e}). Using code-only fallback.")
            # Return code-only summary
            full_list = ', '.join(list(full_recitations.keys())[:3])
            partial_list = ', '.join([f"{p} (v. {d['verses']})" for p, d in list(partial_recitations.items())[:2]])
            parts = []
            if full_recitations:
                parts.append(f"Full Psalm {psalm_chapter}: {full_list}")
            if partial_recitations:
                parts.append(f"Partial: {partial_list}")
            return ". ".join(parts) + "." if parts else f"Psalm {psalm_chapter} in {len(prayer_contexts)} contexts"

    def _validate_phrase_groups_with_llm(
        self,
        grouped: Dict[str, List[LiturgicalMatch]],
        psalm_chapter: int
    ) -> Dict[str, List[LiturgicalMatch]]:
        """
        Validate all phrase groups with LLM to filter false positives.

        Samples representative matches from each group and validates them.
        Filters out groups that fail validation.
        """
        validated_groups = {}
        filtered_count = 0

        for phrase_key, matches in grouped.items():
            # Sample 1-2 representative matches for validation
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

            # Decision logic: Filter if ANY validation fails with high confidence
            should_keep = True
            for val in validations:
                if not val.is_valid and val.confidence >= 0.7:
                    if self.verbose:
                        print(f"[FILTERED] Phrase (len:{len(phrase_key)}) - {val.reason}")
                    should_keep = False
                    filtered_count += 1
                    break
                elif not val.is_valid and val.confidence >= 0.5:
                    # Low confidence rejection - add warning but keep
                    if self.verbose:
                        print(f"[WARNING] Phrase (len:{len(phrase_key)}) - {val.reason}")
                    # Add validation note to first match for reporting
                    if hasattr(matches[0], 'validation_warning'):
                        matches[0].validation_warning = val.reason

            if should_keep:
                validated_groups[phrase_key] = matches

        if self.verbose:
            print(f"\n[OK] LLM Validation complete: {len(validated_groups)}/{len(grouped)} phrase groups kept ({filtered_count} filtered)")

        return validated_groups

    def _validate_phrase_match_with_llm(
        self,
        psalm_phrase: str,
        psalm_chapter: int,
        psalm_verse_range: str,
        match: LiturgicalMatch
    ) -> ValidationResult:
        """
        Use LLM to validate if a phrase match is really from the target psalm.

        Checks for:
        - Different psalm with same words
        - Context mismatch (unrelated text that happens to share words)
        - Provides liturgical context quote for valid matches

        Returns:
            ValidationResult with is_valid, confidence, reason, and optional quote/translation
        """
        if not self.anthropic_client:
            # Without LLM, accept all matches
            return ValidationResult(
                is_valid=True,
                confidence=0.5,
                reason="No LLM available for validation"
            )

        # Get fuller context from database if needed
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT hebrew_text, prayer_name, section FROM prayers WHERE prayer_id = ?",
                (match.prayer_id,)
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                hebrew_text, prayer_name, section = result
                # Use first 30000 chars of hebrew_text for context
                fuller_context = hebrew_text[:30000] if hebrew_text else match.liturgy_context
            else:
                fuller_context = match.liturgy_context

        except Exception as e:
            if self.verbose:
                print(f"[WARNING] Could not fetch fuller context: {e}")
            fuller_context = match.liturgy_context

        prompt = f"""You are validating liturgical usage for a scholarly Biblical commentary tool.

**Task**: Determine if this phrase match is genuinely from Psalm {psalm_chapter} or a false positive.

**Psalm phrase being searched**: {psalm_phrase} (from Psalm {psalm_chapter}:{psalm_verse_range})

**Prayer context**: {match.prayer_name or match.section or "Unknown"}
**Nusach/Tradition**: {match.nusach}

**Liturgy context** (Hebrew text from prayer):
```
{fuller_context[:20000]}
```

**Analyze and determine**:

1. **Is this phrase really from Psalm {psalm_chapter}?**
   - Check if the surrounding context indicates this is Psalm {psalm_chapter}
   - Watch for: Different psalms that share words (e.g., many psalms start with "לדוד ה'")
   - Watch for: Common Hebrew phrases that appear in multiple contexts

2. **If it's a phrase excerpt** (not full verse):
   - Extract the relevant quote from the liturgy showing how it's used
   - Provide a brief translation/explanation

**Respond in JSON format**:
```json
{{
  "is_valid": true/false,
  "confidence": 0.0-1.0,
  "reason": "Brief explanation (e.g., 'This is Psalm 20, not Psalm 23', 'Valid quote from Psalm 23:3')",
  "liturgy_quote": "Relevant Hebrew quote from liturgy (if valid and a phrase excerpt)",
  "translation": "English translation of the quote (if provided)",
  "notes": "Any additional context or warnings (optional)"
}}
```

**Examples**:
- If you see "מזמור לדוד לַיהוָה הָאָרֶץ" → This is Psalm 24, NOT Psalm 23
- If you see "למען שמו" in the Amidah Avot blessing → Valid from Psalm 23:3
- If common words like "טוב" appear in unrelated context → Likely false positive

Output ONLY the JSON, no additional text."""

        if self.verbose:
            print(f"\n{'='*70}")
            print(f"LLM VALIDATION: Psalm {psalm_chapter}:{psalm_verse_range}")
            print(f"{'='*70}")
            # Skip printing prompt due to Hebrew encoding issues in Windows console
            # print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
            print(f"{'='*70}\n")

        try:
            response = self.anthropic_client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=400,
                temperature=0.1,  # Low temperature for factual validation
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text.strip()

            if self.verbose:
                print(f"LLM Validation Result: {result_text[:200]}...")

            # Parse JSON response
            import json
            import re

            # Extract JSON from response (in case LLM adds extra text)
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
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

    def _check_verses_in_prayer(self, hebrew_text: str, psalm_verses: Dict[int, str]) -> List[int]:
        """
        Check which verses from a psalm appear in the prayer's hebrew_text.

        Args:
            hebrew_text: The full Hebrew text of the prayer
            psalm_verses: Dict mapping verse number to Hebrew text

        Returns:
            List of verse numbers found in the prayer text
        """
        normalized_prayer = self._normalize_hebrew_for_comparison(hebrew_text)
        found_verses = []

        for verse_num, verse_text in psalm_verses.items():
            normalized_verse = self._normalize_hebrew_for_comparison(verse_text)
            # Check if at least 70% of the verse words appear in sequence
            verse_words = normalized_verse.split()

            # For short verses (1-3 words), require exact match
            if len(verse_words) <= 3:
                if normalized_verse in normalized_prayer:
                    found_verses.append(verse_num)
            else:
                # For longer verses, check if most words appear in order
                # This handles minor variations in text
                words_found = 0
                prayer_words = normalized_prayer.split()
                verse_idx = 0

                for prayer_word in prayer_words:
                    if verse_idx < len(verse_words) and prayer_word == verse_words[verse_idx]:
                        words_found += 1
                        verse_idx += 1

                        # If we've found 70%+ of verse words in order, count it
                        if words_found / len(verse_words) >= 0.7:
                            found_verses.append(verse_num)
                            break

        return found_verses

    def _verify_full_psalm_matches(self, matches: List[LiturgicalMatch], psalm_chapter: int) -> List[LiturgicalMatch]:
        """
        Verify that "full psalm" matches actually contain substantial portions of the psalm.

        New implementation: Checks actual verse content in hebrew_text field.
        Reports which verses are present and filters false positives.
        """
        if not matches:
            return []

        # Get all verses of the psalm
        psalm_verses = self._get_psalm_verses(psalm_chapter)
        if not psalm_verses:
            if self.verbose:
                print(f"[WARNING] Could not load psalm {psalm_chapter} verses, using old heuristic")
            return matches  # Fall back to accepting all matches if we can't verify

        total_verses = len(psalm_verses)
        verified = []

        # Get hebrew_text for each prayer_id
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for match in matches:
            try:
                # Get the full hebrew_text from prayers table
                cursor.execute(
                    "SELECT hebrew_text FROM prayers WHERE prayer_id = ?",
                    (match.prayer_id,)
                )
                result = cursor.fetchone()

                if not result or not result[0]:
                    if self.verbose:
                        print(f"[WARNING] No hebrew_text for prayer_id {match.prayer_id} ({match.prayer_name})")
                    continue

                hebrew_text = result[0]

                # Check which verses are present
                found_verses = self._check_verses_in_prayer(hebrew_text, psalm_verses)
                found_count = len(found_verses)

                # Determine if this is a true full psalm or partial
                percentage = (found_count / total_verses) * 100 if total_verses > 0 else 0

                # Full psalm: At least 80% of verses present
                # Partial: 30-79% of verses
                # False positive: < 30%

                if percentage >= 30:  # Keep if at least 30% of verses present
                    # Annotate the match with verse information
                    match.found_verses = found_verses
                    match.found_percentage = percentage

                    if self.verbose:
                        verse_range = self._format_verse_list(found_verses)
                        status = "FULL" if percentage >= 80 else "PARTIAL"
                        print(f"[{status}] Psalm match in {match.prayer_name}: verses {verse_range} ({percentage:.0f}%)")

                    verified.append(match)
                else:
                    if self.verbose:
                        print(f"[FILTER] False 'full psalm' match in {match.prayer_name} - only {found_count}/{total_verses} verses ({percentage:.0f}%)")

            except Exception as e:
                if self.verbose:
                    print(f"[WARNING] Error verifying match for prayer_id {match.prayer_id}: {e}")
                continue

        conn.close()

        if self.verbose:
            print(f"\nFull psalm verification: {len(verified)}/{len(matches)} matches kept")

        return verified

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

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the liturgical index."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Total matches
        cursor.execute("SELECT COUNT(*) FROM psalms_liturgy_index")
        stats['total_matches'] = cursor.fetchone()[0]

        # Unique Psalms indexed
        cursor.execute("SELECT COUNT(DISTINCT psalm_chapter) FROM psalms_liturgy_index")
        stats['psalms_indexed'] = cursor.fetchone()[0]

        # Matches by type
        cursor.execute("""
            SELECT match_type, COUNT(*)
            FROM psalms_liturgy_index
            GROUP BY match_type
        """)
        stats['by_match_type'] = dict(cursor.fetchall())

        # Average confidence
        cursor.execute("SELECT AVG(confidence) FROM psalms_liturgy_index")
        stats['avg_confidence'] = round(cursor.fetchone()[0] or 0, 3)

        # Top Psalms by matches
        cursor.execute("""
            SELECT psalm_chapter, COUNT(*) as count
            FROM psalms_liturgy_index
            GROUP BY psalm_chapter
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['top_psalms'] = cursor.fetchall()

        # Unique prayers referenced
        cursor.execute("""
            SELECT COUNT(DISTINCT prayer_id)
            FROM psalms_liturgy_index
        """)
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
        epilog="""
Examples:
  # Query Psalm 23 with LLM summaries (default)
  python src/agents/liturgical_librarian.py 23

  # Query specific verses
  python src/agents/liturgical_librarian.py 23 --verses 1 2 3

  # Disable LLM summaries
  python src/agents/liturgical_librarian.py 23 --skip-liturgy-llm

  # Show statistics
  python src/agents/liturgical_librarian.py --stats
        """
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
        print("Using Claude Haiku 4.5 for intelligent context summaries")
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
                print(f"     {j}. {raw.prayer_name or raw.section} ({raw.nusach})")
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
