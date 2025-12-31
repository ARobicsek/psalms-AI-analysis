"""
Tribal Curator - LLM-enhanced agent for analyzing figurative language in
structured biblical passages like Genesis 49's tribal blessings.

This agent adapts the FigurativeCurator pattern to analyze passages organized
by named segments (tribes, nations, etc.) rather than verse-by-verse.

Key Features:
- Extracts figurative language per segment from source passage
- Searches for same vehicles AND segment names as targets throughout concordance
- Uses 3-iteration refinement approach
- Generates ~500-word scholarly insights per segment with Hebrew quotations
- Emphasizes genuine insights and 'aha' moments over trite observations

Author: Claude Code
Date: 2025-12-30
"""

import json
import os
import re
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from src.agents.figurative_librarian import FigurativeLibrarian, FigurativeRequest, FigurativeBundle


# ============================================================================
# Configuration Classes
# ============================================================================

@dataclass
class SegmentConfig:
    """Configuration for a single segment (e.g., one tribe's blessing)."""
    verses: List[int]
    blessing_type: str = "blessing"
    paired_with: Optional[str] = None  # For combined segments like Simeon & Levi
    notes: Optional[str] = None


@dataclass
class PassageAnalysisConfig:
    """Configuration for analyzing any biblical passage's figurative language."""
    book: str                           # e.g., "Genesis"
    chapter: int                        # e.g., 49
    name: str                           # e.g., "Jacob's Tribal Blessings"
    segments: Dict[str, SegmentConfig]  # Named segments with verse ranges
    output_dir: str                     # Where to save results
    words_per_segment: int = 500        # Target insight length


# Pre-configured for Genesis 49
GENESIS_49_CONFIG = PassageAnalysisConfig(
    book="Genesis",
    chapter=49,
    name="Jacob's Tribal Blessings",
    output_dir="output/genesis_49",
    words_per_segment=1000,  # Target 1000 words, up to 2000 if rich material
    segments={
        "Reuben": SegmentConfig(
            verses=[3, 4],
            blessing_type="rebuke",
            notes="Firstborn who lost preeminence due to transgression"
        ),
        "Simeon and Levi": SegmentConfig(
            verses=[5, 6, 7],
            blessing_type="rebuke",
            notes="Brothers united in violence, cursed for their anger"
        ),
        "Judah": SegmentConfig(
            verses=[8, 9, 10, 11, 12],
            blessing_type="royal_blessing",
            notes="Lion imagery, scepter, royal destiny"
        ),
        "Zebulun": SegmentConfig(
            verses=[13],
            blessing_type="territorial",
            notes="Maritime/coastal blessing"
        ),
        "Issachar": SegmentConfig(
            verses=[14, 15],
            blessing_type="agricultural",
            notes="Strong donkey, willing labor"
        ),
        "Dan": SegmentConfig(
            verses=[16, 17],
            blessing_type="military",
            notes="Serpent/viper imagery, judge of his people"
        ),
        "Gad": SegmentConfig(
            verses=[19],
            blessing_type="military",
            notes="Raider imagery with wordplay"
        ),
        "Asher": SegmentConfig(
            verses=[20],
            blessing_type="prosperity",
            notes="Rich food, royal delicacies"
        ),
        "Naphtali": SegmentConfig(
            verses=[21],
            blessing_type="poetic",
            notes="Hind/doe imagery, beautiful fawns"
        ),
        "Joseph": SegmentConfig(
            verses=[22, 23, 24, 25, 26],
            blessing_type="extended_blessing",
            notes="Longest blessing - fruitful bough, archers, blessings"
        ),
        "Benjamin": SegmentConfig(
            verses=[27],
            blessing_type="military",
            notes="Wolf imagery - ravenous predator"
        ),
    }
)


# ============================================================================
# Output Dataclasses
# ============================================================================

@dataclass
class SegmentAnalysisOutput:
    """Output for a single segment (e.g., one tribe)."""
    segment_name: str
    verses: List[int]
    source_text_hebrew: str
    source_text_english: str

    # Figurative elements found in source
    vehicles_identified: List[str]
    targets_identified: List[str]

    # Search results
    vehicle_search_results: Dict[str, int]  # vehicle -> count
    target_search_results: int              # segment name as target elsewhere

    # Curated examples
    curated_examples: List[Dict[str, Any]]

    # Tribe as target examples (how this tribe is described figuratively elsewhere)
    tribe_as_target_examples: List[Dict[str, Any]]

    # Final insight
    insight_text: str                       # 1000-2000 words

    # Metadata
    token_usage: Dict[str, int]
    iteration_count: int


@dataclass
class FullAnalysisOutput:
    """Complete analysis of all segments."""
    passage_name: str
    book: str
    chapter: int
    segments: Dict[str, SegmentAnalysisOutput]
    total_token_usage: Dict[str, int]
    total_cost: float


# ============================================================================
# Main Curator Class
# ============================================================================

class TribalCurator:
    """
    LLM-enhanced curator for analyzing figurative language in structured
    biblical passages (tribal blessings, oracles, etc.).

    This agent:
    1. Loads passage text and identifies figurative elements per segment
    2. Searches figurative concordance for vehicles AND segment-as-target
    3. Uses iterative refinement (up to 3 iterations)
    4. Synthesizes ~500-word scholarly insights with genuine 'aha' moments
    """

    MAX_ITERATIONS = 3
    MIN_RESULTS_FOR_USEFUL = 1

    # Search result caps
    INITIAL_SEARCH_CAP = 50
    FOLLOWUP_SEARCH_CAP = 30

    # Gemini pricing
    GEMINI_INPUT_COST_PER_M = 2.00
    GEMINI_OUTPUT_COST_PER_M = 12.00
    GEMINI_THINKING_COST_PER_M = 12.00

    def __init__(
        self,
        config: PassageAnalysisConfig,
        google_api_key: Optional[str] = None,
        verbose: bool = False,
        dry_run: bool = False,
        tanakh_db_path: Optional[Path] = None,
        figurative_db_path: Optional[Path] = None,
        deep_research_path: Optional[Path] = None
    ):
        """
        Initialize the Tribal Curator.

        Args:
            config: Passage analysis configuration
            google_api_key: Google API key (defaults to GEMINI_API_KEY env var)
            verbose: Print detailed progress
            dry_run: Don't call LLM, just show prompts
            tanakh_db_path: Path to tanakh.db for verse text
            figurative_db_path: Path to figurative language database
            deep_research_path: Optional path to deep research file for additional context
        """
        self.config = config
        self.verbose = verbose
        self.dry_run = dry_run
        self.gemini_client = None

        # Set database paths
        project_root = Path(__file__).parent.parent.parent
        self.tanakh_db_path = tanakh_db_path or (project_root / "database" / "tanakh.db")
        self.figurative_db_path = figurative_db_path or Path(
            "C:/Users/ariro/OneDrive/Documents/Bible/database/Biblical_fig_language.db"
        )

        # Deep research file path
        self.deep_research_path = deep_research_path
        self.deep_research_content = None
        if deep_research_path and deep_research_path.exists():
            try:
                self.deep_research_content = deep_research_path.read_text(encoding='utf-8')
                if verbose:
                    print(f"[INFO] Loaded deep research from {deep_research_path} ({len(self.deep_research_content):,} chars)")
            except Exception as e:
                if verbose:
                    print(f"[WARNING] Could not load deep research: {e}")

        # Initialize figurative librarian
        self.figurative_librarian = FigurativeLibrarian(db_path=self.figurative_db_path)

        # Initialize Gemini client
        if not dry_run:
            try:
                from google import genai
                api_key = google_api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
                if api_key:
                    self.gemini_client = genai.Client(api_key=api_key)
                    if verbose:
                        print("[INFO] Initialized Gemini client")
                else:
                    raise ValueError("No Google API key found. Set GEMINI_API_KEY in .env")
            except ImportError:
                raise ImportError("google-genai package not installed. Run: pip install google-genai")

    @property
    def active_model(self) -> str:
        """Return the name of the active LLM model."""
        if self.dry_run:
            return "None (Dry Run)"
        return "gemini-3-pro-preview"

    def _get_passage_text(
        self,
        book: str,
        chapter: int,
        verses: Optional[List[int]] = None
    ) -> List[Tuple[int, str, str]]:
        """
        Get passage text from tanakh database.

        Args:
            book: Book name (e.g., "Genesis")
            chapter: Chapter number
            verses: Optional list of specific verses (None = all verses)

        Returns:
            List of (verse_number, hebrew_text, english_text) tuples
        """
        conn = sqlite3.connect(str(self.tanakh_db_path))
        cursor = conn.cursor()

        if verses:
            placeholders = ",".join("?" * len(verses))
            cursor.execute(f"""
                SELECT verse, hebrew, english
                FROM verses
                WHERE book_name = ? AND chapter = ? AND verse IN ({placeholders})
                ORDER BY verse
            """, [book, chapter] + verses)
        else:
            cursor.execute("""
                SELECT verse, hebrew, english
                FROM verses
                WHERE book_name = ? AND chapter = ?
                ORDER BY verse
            """, (book, chapter))

        results = cursor.fetchall()
        conn.close()
        return results

    def _get_figurative_instances_for_verses(
        self,
        book: str,
        chapter: int,
        verses: List[int]
    ) -> List[Any]:
        """
        Get all figurative instances from the source passage verses.

        Returns:
            List of FigurativeInstance objects from those verses
        """
        request = FigurativeRequest(
            book=book,
            chapter=chapter,
            verse_start=min(verses),
            verse_end=max(verses),
            max_results=100
        )
        bundle = self.figurative_librarian.search(request)

        # Filter to exact verses (in case verse_start/end includes extras)
        return [inst for inst in bundle.instances if inst.verse in verses]

    def _call_gemini(
        self,
        prompt: str,
        temperature: float = 0.4,
        thinking_budget: int = 10000
    ) -> Tuple[str, Dict[str, int]]:
        """
        Call Gemini with extended thinking.

        Returns:
            Tuple of (response_text, token_usage_dict)
        """
        if self.dry_run:
            print("\n" + "=" * 80)
            print("DRY RUN - Would send this prompt to Gemini:")
            print("=" * 80)
            print(prompt[:3000] + "..." if len(prompt) > 3000 else prompt)
            print("=" * 80 + "\n")
            return "[DRY RUN - No LLM response]", {"input": 0, "output": 0, "thinking": 0, "cost": 0.0}

        from google.genai import types

        if self.verbose:
            print(f"[API] Calling Gemini 3 Pro (thinking_level=high)...")

        start_time = time.time()

        # Try Gemini 3 Pro first, fall back to 2.5 Pro if not available
        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-3-pro-preview",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    thinking_config=types.ThinkingConfig(
                        thinking_level="high"  # Maximum reasoning depth
                    ),
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    )
                )
            )
        except Exception as e:
            # Fallback to Gemini 2.5 Pro if 3.0 not available
            if self.verbose:
                print(f"[WARNING] Gemini 3 Pro failed ({e}), falling back to 2.5 Pro...")
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=thinking_budget
                    ),
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    )
                )
            )

        elapsed = time.time() - start_time
        if self.verbose:
            print(f"[API] Response received in {elapsed:.1f}s")

        # Extract text from response
        response_text = ""
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text

        # Get token usage
        token_usage = {"input": 0, "output": 0, "thinking": 0, "cost": 0.0}
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            token_usage["input"] = getattr(usage, 'prompt_token_count', 0) or 0
            token_usage["output"] = getattr(usage, 'candidates_token_count', 0) or 0
            token_usage["thinking"] = getattr(usage, 'thoughts_token_count', 0) or 0

            # Calculate cost
            input_cost = (token_usage["input"] / 1_000_000) * self.GEMINI_INPUT_COST_PER_M
            output_cost = (token_usage["output"] / 1_000_000) * self.GEMINI_OUTPUT_COST_PER_M
            thinking_cost = (token_usage["thinking"] / 1_000_000) * self.GEMINI_THINKING_COST_PER_M
            token_usage["cost"] = input_cost + output_cost + thinking_cost

        return response_text, token_usage

    def _get_verse_hebrew(self, reference: str) -> Optional[str]:
        """Get full Hebrew text for a verse reference."""
        match = re.match(r'(\d?\s*\w+)\s+(\d+):(\d+)', reference)
        if not match:
            return None

        book_name = match.group(1).strip()
        chapter = int(match.group(2))
        verse = int(match.group(3))

        # Book name normalization
        book_name_map = {
            'Genesis': 'Genesis', 'Gen': 'Genesis',
            'Exodus': 'Exodus', 'Ex': 'Exodus',
            'Leviticus': 'Leviticus', 'Lev': 'Leviticus',
            'Numbers': 'Numbers', 'Num': 'Numbers',
            'Deuteronomy': 'Deuteronomy', 'Deut': 'Deuteronomy',
            'Psalms': 'Psalms', 'Psalm': 'Psalms', 'Ps': 'Psalms',
            'Proverbs': 'Proverbs', 'Prov': 'Proverbs',
            'Isaiah': 'Isaiah', 'Isa': 'Isaiah',
            'Jeremiah': 'Jeremiah', 'Jer': 'Jeremiah',
            'Ezekiel': 'Ezekiel', 'Ezek': 'Ezekiel',
            'Hosea': 'Hosea', 'Joel': 'Joel', 'Amos': 'Amos',
        }
        normalized_book = book_name_map.get(book_name, book_name)

        try:
            conn = sqlite3.connect(str(self.tanakh_db_path))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT hebrew FROM verses
                WHERE book_name = ? AND chapter = ? AND verse = ?
            """, (normalized_book, chapter, verse))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception:
            return None

    def _format_instances_for_prompt(
        self,
        instances: List[Any],
        max_per_query: int = 12
    ) -> str:
        """Format figurative instances for inclusion in prompt."""
        lines = []
        for inst in instances[:max_per_query]:
            types_list = []
            if inst.is_metaphor: types_list.append("metaphor")
            if inst.is_simile: types_list.append("simile")
            if inst.is_personification: types_list.append("personification")
            if inst.is_metonymy: types_list.append("metonymy")
            if inst.is_hyperbole: types_list.append("hyperbole")
            if inst.is_idiom: types_list.append("idiom")
            types_str = ", ".join(types_list) if types_list else "figurative"

            target_str = " > ".join(inst.target[:3]) if inst.target else "N/A"
            vehicle_str = " > ".join(inst.vehicle[:3]) if inst.vehicle else "N/A"

            # Get full Hebrew verse
            full_hebrew = self._get_verse_hebrew(inst.reference) or ""
            hebrew_display = f"\n  Full Hebrew: {full_hebrew}" if full_hebrew else ""

            lines.append(f"""
**{inst.reference}** ({types_str})
  English: {inst.figurative_text}
  Hebrew phrase: {inst.figurative_text_hebrew or 'N/A'}{hebrew_display}
  Target: {target_str}
  Vehicle: {vehicle_str}
  Explanation: {inst.explanation[:250]}{'...' if len(inst.explanation) > 250 else ''}
""")
        return "\n".join(lines)

    def _build_phase1_prompt(
        self,
        segment_name: str,
        segment_config: SegmentConfig,
        passage_text: List[Tuple[int, str, str]],
        source_figurative: List[Any]
    ) -> str:
        """
        Build Phase 1 prompt: Identify vehicles and plan searches.
        """
        # Format passage text
        text_lines = []
        for verse_num, hebrew, english in passage_text:
            text_lines.append(f"**Verse {verse_num}**")
            text_lines.append(f"Hebrew: {hebrew}")
            text_lines.append(f"English: {english}")
            text_lines.append("")
        text_formatted = "\n".join(text_lines)

        # Format existing figurative instances
        if source_figurative:
            fig_formatted = self._format_instances_for_prompt(source_figurative, max_per_query=15)
        else:
            fig_formatted = "(No pre-tagged figurative instances found in database for these verses)"

        prompt = f"""You are analyzing the figurative language in Jacob's blessing of {segment_name} (Genesis 49:{min(segment_config.verses)}-{max(segment_config.verses)}).

## THE BLESSING TEXT

{text_formatted}

## PRE-TAGGED FIGURATIVE INSTANCES FROM THIS PASSAGE

{fig_formatted}

## YOUR TASK: IDENTIFY VEHICLES AND PLAN SEARCHES

Analyze the figurative language in this blessing and identify:

1. **ALL VEHICLES used** - The concrete images/concepts that carry meaning
   - Examples: lion, serpent, water, scepter, vine, wolf, donkey, etc.
   - Be thorough - even minor figurative elements matter

2. **THE TARGETS** - What these vehicles represent
   - The tribe itself ({segment_name})
   - Characteristics being attributed (power, treachery, abundance, etc.)

3. **SEARCH STRATEGY** - What to search in the figurative concordance:
   - Each vehicle term (to find similar imagery elsewhere)
   - The tribe name "{segment_name}" as a TARGET (to find other figurative descriptions of this tribe)

**IMPORTANT SEARCH RULES:**
- Each search term must be a SINGLE WORD
- No phrases, no boolean operators
- Suggest the most productive single-word terms

Return as JSON:

```json
{{
  "vehicles_identified": [
    {{
      "vehicle": "lion",
      "hebrew_term": "אריה / גור",
      "verse": 9,
      "figurative_function": "Represents Judah's royal power and predatory dominance"
    }}
  ],
  "targets_identified": [
    {{
      "target": "{segment_name}",
      "what_is_being_said": "Summary of what the blessing says about this tribe"
    }}
  ],
  "vehicle_searches": [
    {{
      "term": "lion",
      "expected_insight": "How lion imagery is used for leaders/tribes elsewhere"
    }}
  ],
  "target_search": {{
    "term": "{segment_name}",
    "expected_insight": "How {segment_name} is described figuratively elsewhere in Scripture"
  }},
  "key_interpretive_questions": [
    "Why was THIS vehicle chosen rather than alternatives?",
    "What specific aspect of the vehicle is being activated?"
  ]
}}
```
"""
        return prompt

    def _build_phase2_prompt(
        self,
        segment_name: str,
        segment_config: SegmentConfig,
        passage_text: List[Tuple[int, str, str]],
        source_figurative: List[Any],
        all_search_results: Dict[str, FigurativeBundle],
        phase1_analysis: Dict[str, Any]
    ) -> str:
        """
        Build Phase 2 prompt: Synthesize insights from search results.
        """
        # Format passage text (abbreviated)
        text_lines = []
        for verse_num, hebrew, english in passage_text:
            text_lines.append(f"v{verse_num}: {hebrew}")
            text_lines.append(f"    {english}")
        text_formatted = "\n".join(text_lines)

        # Format all search results
        results_formatted = []
        for search_term, bundle in all_search_results.items():
            if bundle.instances:
                results_formatted.append(f"\n### Search: '{search_term}' ({len(bundle.instances)} results)\n")
                results_formatted.append(self._format_instances_for_prompt(bundle.instances, max_per_query=10))

        # Get vehicles from phase 1
        vehicles = phase1_analysis.get("vehicles_identified", [])
        vehicles_summary = ", ".join(v.get("vehicle", "?") for v in vehicles)

        # Include deep research if available
        deep_research_section = ""
        if self.deep_research_content:
            # Trim to reasonable size and add section
            deep_content = self.deep_research_content[:30000]  # Cap at 30K chars
            if len(self.deep_research_content) > 30000:
                deep_content += "\n\n[... deep research truncated for length ...]"
            deep_research_section = f"""

## DEEP WEB RESEARCH (Additional Scholarly Context)

The following is scholarly research gathered from web sources about Genesis 49 and the tribal blessings. Use relevant insights to enrich your analysis:

{deep_content}

"""

        prompt = f"""You are synthesizing a scholarly insight about the figurative language in Jacob's blessing of {segment_name} (Genesis 49).

## THE BLESSING TEXT

{text_formatted}

## VEHICLES IDENTIFIED IN THIS BLESSING

{vehicles_summary}

## SEARCH RESULTS FROM FIGURATIVE CONCORDANCE

The following are figurative instances from throughout Scripture (Pentateuch, Psalms, Proverbs, Major Prophets) that use similar vehicles or describe {segment_name}:

{''.join(results_formatted)}
{deep_research_section}

## YOUR TASK: WRITE A SCHOLARLY INSIGHT ({self.config.words_per_segment}-2000 WORDS)

Write a substantive scholarly essay about the figurative language in {segment_name}'s blessing.
**Target {self.config.words_per_segment} words minimum, but expand to 1500-2000 words if there is rich material that will create genuine 'aha' moments for readers hungry to learn.**

**CRITICAL REQUIREMENTS - READ CAREFULLY:**

1. **SEEK GENUINE INSIGHTS, NOT TRITE OBSERVATIONS**
   - Do NOT state the obvious (e.g., "lions are powerful")
   - Do NOT make generic statements about metaphors
   - FIND something surprising, illuminating, or counterintuitive
   - Ask: "What would a careful reader NOT notice without this concordance data?"

2. **ANSWER THESE QUESTIONS:**
   - Why THIS specific vehicle and not alternatives? (What would be lost if Jacob said "Judah is a bear" instead of "lion"?)
   - What specific ASPECT of the vehicle is being activated? (Not all qualities - which ones?)
   - How does this vehicle's usage ELSEWHERE illuminate its meaning HERE?
   - Are there SURPRISING patterns or INVERSIONS of typical usage?

3. **RECEPTION HISTORY & CULTURAL IMPACT**
   - How has this imagery influenced art, literature, or iconography? (e.g., Lion of Judah in heraldry, flags, Rastafarianism)
   - Has this imagery shaped political or national identity? (e.g., tribal symbols, state emblems)
   - Are there notable interpretive traditions (Rabbinic, Christian, academic) that offer insight?
   - Include this section where relevant - some tribes have rich reception history, others less so

4. **USE QUOTATIONS GENEROUSLY**
   - Quote the Hebrew with English translation
   - Quote parallel passages from the search results
   - Show, don't just tell

5. **STRUCTURE:**
   - Open with a specific, provocative observation (not a generic introduction)
   - Develop the insight with evidence from the concordance
   - Include reception history and cultural influence where relevant
   - Connect to the broader meaning of this tribe's destiny
   - Close with the "so what" - why does this figurative choice matter?

**WHAT MAKES A GOOD INSIGHT:**
- "The concordance reveals that lion imagery for Judah INVERTS the typical pattern where..."
- "Strikingly, when serpent imagery appears for Dan, it's the ONLY positive use of..."
- "The choice of 'hind' (אַיָּלָה) rather than 'gazelle' (צְבִי) is significant because..."

**WHAT TO AVOID:**
- "Jacob uses powerful imagery to describe..."
- "This metaphor emphasizes the tribe's strength..."
- "The figurative language highlights..."
- Generic statements that could apply to any metaphor

Return as JSON:

```json
{{
  "insight_title": "A specific, intriguing title (not generic)",
  "insight_text": "Your {self.config.words_per_segment}-2000 word scholarly essay with Hebrew quotations, reception history, and cultural impact...",
  "key_discovery": "The single most surprising/illuminating finding",
  "curated_examples": [
    {{
      "reference": "Isaiah 31:4",
      "hebrew": "כַּאֲרִי וְכַכְּפִיר עַל־טַרְפּוֹ",
      "english": "Like a lion, like a young lion over its prey",
      "why_relevant": "Shows how lion imagery for YHWH echoes the Judah blessing"
    }},
    {{
      "reference": "Ezekiel 19:2-3",
      "hebrew": "...",
      "english": "...",
      "why_relevant": "..."
    }},
    {{
      "reference": "...",
      "hebrew": "...",
      "english": "...",
      "why_relevant": "..."
    }},
    {{
      "reference": "...",
      "hebrew": "...",
      "english": "...",
      "why_relevant": "..."
    }},
    {{
      "reference": "...",
      "hebrew": "...",
      "english": "...",
      "why_relevant": "..."
    }}
  ],
  "tribe_as_target_examples": [
    {{
      "reference": "Hosea 5:14",
      "context": "How {segment_name} is described figuratively elsewhere in Scripture",
      "hebrew": "...",
      "english": "...",
      "significance": "What this tells us about how the prophets/poets viewed this tribe"
    }}
  ]
}}
```

**IMPORTANT:**
- Provide AT LEAST 5 curated biblical parallel examples (more if available and illuminating)
- Include examples of {segment_name} being used as a figurative TARGET elsewhere in Scripture (from the TARGET search results)
- The goal is an insight that would make a scholar say "I never noticed that before!" - not a summary of what the blessing says.
"""
        return prompt

    def _build_iterative_review_prompt(
        self,
        segment_name: str,
        iteration: int,
        previous_searches: Dict[str, int],
        failed_searches: List[str]
    ) -> str:
        """Build prompt for iterative review of search results."""
        results_summary = []
        for term, count in previous_searches.items():
            status = "+" if count >= self.MIN_RESULTS_FOR_USEFUL else "-"
            results_summary.append(f"  {status} '{term}': {count} results")

        failed_list = ", ".join(failed_searches) if failed_searches else "None"

        prompt = f"""You are reviewing search results for figurative analysis of {segment_name}'s blessing.

## ITERATION {iteration} of {self.MAX_ITERATIONS}

## SEARCH RESULTS SO FAR
{chr(10).join(results_summary)}

## FAILED SEARCHES (0 results)
{failed_list}

## YOUR TASK: DECIDE ON ADDITIONAL SEARCHES

For failed searches, suggest alternative terms:
- "serpent" failed? Try: "snake", "viper", "adder"
- "staff" failed? Try: "rod", "scepter"

For thin results, suggest related concepts:
- "lion" has results but want more? Try: "prey", "roar", "crouch"

**SINGLE WORDS ONLY** - no phrases or operators.

Return JSON:

```json
{{
  "additional_searches": [
    {{"term": "viper", "reason": "Alternative for serpent"}}
  ],
  "stop_searching": false,
  "stop_reason": null
}}
```

Set "stop_searching": true if results are sufficient.
"""
        return prompt

    def _parse_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract and parse JSON from LLM response."""
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group(0)
            else:
                return {}

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            if self.verbose:
                print(f"[WARNING] JSON parse error: {e}")
            return {}

    def analyze_segment(self, segment_name: str) -> SegmentAnalysisOutput:
        """
        Analyze a single segment (e.g., one tribe's blessing).

        Args:
            segment_name: Name of the segment to analyze

        Returns:
            SegmentAnalysisOutput with insight and curated examples
        """
        if segment_name not in self.config.segments:
            raise ValueError(f"Unknown segment: {segment_name}")

        segment_config = self.config.segments[segment_name]
        total_tokens = {"input": 0, "output": 0, "thinking": 0, "cost": 0.0}

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"ANALYZING: {segment_name}")
            print(f"Verses: {self.config.book} {self.config.chapter}:{min(segment_config.verses)}-{max(segment_config.verses)}")
            print(f"{'='*60}")

        # Step 1: Load passage text
        if self.verbose:
            print(f"\n[STEP 1] Loading passage text...")
        passage_text = self._get_passage_text(
            self.config.book,
            self.config.chapter,
            segment_config.verses
        )
        if not passage_text:
            raise ValueError(f"Could not load text for {segment_name}")

        source_hebrew = "\n".join(row[1] for row in passage_text)
        source_english = "\n".join(row[2] for row in passage_text)

        if self.verbose:
            print(f"         Loaded {len(passage_text)} verses")

        # Step 2: Get existing figurative instances from these verses
        if self.verbose:
            print(f"\n[STEP 2] Getting figurative instances from source passage...")
        source_figurative = self._get_figurative_instances_for_verses(
            self.config.book,
            self.config.chapter,
            segment_config.verses
        )
        if self.verbose:
            print(f"         Found {len(source_figurative)} pre-tagged instances")

        # Step 3: Phase 1 - Identify vehicles and plan searches
        if self.verbose:
            print(f"\n[STEP 3] Phase 1: Identifying vehicles and planning searches...")

        phase1_prompt = self._build_phase1_prompt(
            segment_name, segment_config, passage_text, source_figurative
        )
        phase1_response, phase1_tokens = self._call_gemini(phase1_prompt)
        self._add_tokens(total_tokens, phase1_tokens)

        phase1_analysis = self._parse_json_from_response(phase1_response)

        vehicles_identified = [v.get("vehicle", "") for v in phase1_analysis.get("vehicles_identified", [])]
        if self.verbose:
            print(f"         Vehicles identified: {', '.join(vehicles_identified)}")

        # Step 4: Execute searches
        if self.verbose:
            print(f"\n[STEP 4] Executing figurative concordance searches...")

        all_search_results: Dict[str, FigurativeBundle] = {}

        # Search for each vehicle
        vehicle_searches = phase1_analysis.get("vehicle_searches", [])
        for vs in vehicle_searches:
            term = vs.get("term", "")
            if term:
                request = FigurativeRequest(
                    vehicle_contains=term,
                    max_results=self.INITIAL_SEARCH_CAP
                )
                bundle = self.figurative_librarian.search(request)
                all_search_results[term] = bundle
                if self.verbose:
                    print(f"         Vehicle '{term}': {len(bundle.instances)} results")

        # Search for segment name as target
        target_search = phase1_analysis.get("target_search", {})
        target_term = target_search.get("term", segment_name)
        # For combined names like "Simeon and Levi", search each separately
        target_names = [n.strip() for n in segment_name.replace(" and ", ",").split(",")]
        target_results_count = 0
        for tname in target_names:
            request = FigurativeRequest(
                target_contains=tname,
                max_results=self.INITIAL_SEARCH_CAP
            )
            bundle = self.figurative_librarian.search(request)
            all_search_results[f"TARGET:{tname}"] = bundle
            target_results_count += len(bundle.instances)
            if self.verbose:
                print(f"         Target '{tname}': {len(bundle.instances)} results")

        # Step 5: Iterative refinement
        iteration = 1
        while iteration <= self.MAX_ITERATIONS and not self.dry_run:
            failed = [t for t, b in all_search_results.items() if len(b.instances) == 0]
            if not failed:
                if self.verbose:
                    print(f"         All searches successful")
                break

            if self.verbose:
                print(f"\n[STEP 5.{iteration}] Iteration {iteration}: Reviewing failed searches...")

            counts = {t: len(b.instances) for t, b in all_search_results.items()}
            review_prompt = self._build_iterative_review_prompt(
                segment_name, iteration, counts, failed
            )
            review_response, review_tokens = self._call_gemini(review_prompt, thinking_budget=4000)
            self._add_tokens(total_tokens, review_tokens)

            review = self._parse_json_from_response(review_response)

            if review.get("stop_searching", False):
                if self.verbose:
                    print(f"         Stopping: {review.get('stop_reason', 'sufficient results')}")
                break

            additional = review.get("additional_searches", [])
            if not additional:
                break

            for search in additional[:5]:
                term = search.get("term", "")
                if term and term not in all_search_results:
                    request = FigurativeRequest(
                        vehicle_contains=term,
                        max_results=self.FOLLOWUP_SEARCH_CAP
                    )
                    bundle = self.figurative_librarian.search(request)
                    all_search_results[term] = bundle
                    if self.verbose:
                        status = "+" if len(bundle.instances) > 0 else "-"
                        print(f"         {status} '{term}': {len(bundle.instances)} results")

            iteration += 1

        # Step 6: Phase 2 - Synthesize insight
        if self.verbose:
            total_results = sum(len(b.instances) for b in all_search_results.values())
            print(f"\n[STEP 6] Phase 2: Synthesizing insight from {total_results} total results...")

        phase2_prompt = self._build_phase2_prompt(
            segment_name, segment_config, passage_text, source_figurative,
            all_search_results, phase1_analysis
        )
        phase2_response, phase2_tokens = self._call_gemini(phase2_prompt, thinking_budget=15000)
        self._add_tokens(total_tokens, phase2_tokens)

        phase2_analysis = self._parse_json_from_response(phase2_response)

        # Build output
        vehicle_search_results = {
            t: len(b.instances) for t, b in all_search_results.items()
            if not t.startswith("TARGET:")
        }

        return SegmentAnalysisOutput(
            segment_name=segment_name,
            verses=segment_config.verses,
            source_text_hebrew=source_hebrew,
            source_text_english=source_english,
            vehicles_identified=vehicles_identified,
            targets_identified=[segment_name],
            vehicle_search_results=vehicle_search_results,
            target_search_results=target_results_count,
            curated_examples=phase2_analysis.get("curated_examples", []),
            tribe_as_target_examples=phase2_analysis.get("tribe_as_target_examples", []),
            insight_text=phase2_analysis.get("insight_text", ""),
            token_usage=total_tokens,
            iteration_count=iteration
        )

    def _add_tokens(self, total: Dict[str, Any], new: Dict[str, Any]):
        """Add token counts to running total."""
        total["input"] += new.get("input", 0)
        total["output"] += new.get("output", 0)
        total["thinking"] += new.get("thinking", 0)
        total["cost"] += new.get("cost", 0.0)

    def analyze_all(self) -> FullAnalysisOutput:
        """
        Analyze all segments and produce combined output.

        Returns:
            FullAnalysisOutput with all segment analyses
        """
        results = {}
        total_tokens = {"input": 0, "output": 0, "thinking": 0, "cost": 0.0}

        for segment_name in self.config.segments:
            output = self.analyze_segment(segment_name)
            results[segment_name] = output
            self._add_tokens(total_tokens, output.token_usage)

        return FullAnalysisOutput(
            passage_name=self.config.name,
            book=self.config.book,
            chapter=self.config.chapter,
            segments=results,
            total_token_usage=total_tokens,
            total_cost=total_tokens["cost"]
        )
