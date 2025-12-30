"""
Figurative Curator - LLM-enhanced agent for curating figurative language insights.

This agent transforms raw figurative concordance results into interpretive insights
using Gemini 3 Pro with high reasoning capabilities.

Author: Claude Code
Date: 2025-12-29
Session: 226
"""

import json
import os
import re
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from src.agents.figurative_librarian import FigurativeLibrarian, FigurativeRequest, FigurativeBundle


@dataclass
class FigurativeSearchRequest:
    """A parsed figurative search request from the micro analyst."""
    vehicle_contains: str
    vehicle_search_terms: List[str]
    notes: str
    verse_ref: Optional[str] = None


@dataclass
class CuratorSearchResult:
    """Results from a single search performed by the curator."""
    query_type: str  # 'initial', 'follow_up_same_target', 'follow_up_alternative_vehicle', etc.
    vehicle_term: str
    num_results: int
    instances: List[Dict[str, Any]]


@dataclass
class FigurativeCuratorOutput:
    """Output from the figurative curator."""
    psalm_number: int
    curated_examples_by_vehicle: Dict[str, List[Dict[str, Any]]]  # 5-15 examples per vehicle
    figurative_insights: List[Dict[str, str]]  # 4-5 prose insights
    search_summary: Dict[str, Any]  # What searches were performed
    iteration_log: List[Dict[str, Any]]  # Log of each iteration for debugging
    token_usage: Dict[str, int]  # Token counts for cost tracking
    raw_llm_response: str  # For debugging


class FigurativeCurator:
    """
    LLM-enhanced figurative language curator.

    This agent:
    1. Reviews micro analyst's figurative requests and improves them
    2. Executes searches against the figurative concordance
    3. Performs ITERATIVE follow-up searches (review → search → review again)
    4. Curates 5-15 examples per vehicle with Hebrew text
    5. Synthesizes results into interpretive insights
    """

    MAX_ITERATIONS = 3  # Maximum review → search → review cycles
    MIN_RESULTS_FOR_USEFUL = 1  # Even 1 result can provide useful insight

    # Search result caps - results are already randomized across books in the DB
    INITIAL_SEARCH_CAP = 50  # Cap for initial micro analyst searches
    FOLLOWUP_SEARCH_CAP = 30  # Cap for follow-up searches

    # Gemini 3 Pro pricing (as of Nov 2025)
    # https://ai.google.dev/gemini-api/docs/pricing
    GEMINI_3_PRO_INPUT_COST_PER_M = 2.00   # $2.00 per million input tokens (≤200K context)
    GEMINI_3_PRO_OUTPUT_COST_PER_M = 12.00  # $12.00 per million output tokens
    GEMINI_3_PRO_THINKING_COST_PER_M = 12.00  # Thinking tokens billed as output

    def __init__(
        self,
        google_api_key: Optional[str] = None,
        verbose: bool = False,
        dry_run: bool = False,
        max_iterations: int = 3,
        tanakh_db_path: Optional[Path] = None
    ):
        """
        Initialize the Figurative Curator.

        Args:
            google_api_key: Google API key (defaults to GEMINI_API_KEY env var)
            verbose: Print detailed progress
            dry_run: Don't call LLM, just show prompts
            max_iterations: Maximum review → search → review cycles (default 3)
            tanakh_db_path: Path to tanakh.db (defaults to database/tanakh.db)
        """
        self.verbose = verbose
        self.dry_run = dry_run
        self.max_iterations = max_iterations
        self.gemini_client = None

        # Set database path
        if tanakh_db_path:
            self.tanakh_db_path = tanakh_db_path
        else:
            # Default to project root / database / tanakh.db
            project_root = Path(__file__).parent.parent.parent
            self.tanakh_db_path = project_root / "database" / "tanakh.db"

        # Initialize figurative librarian
        self.figurative_librarian = FigurativeLibrarian()

        # Initialize Gemini client
        if not dry_run:
            try:
                from google import genai
                api_key = google_api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
                if api_key:
                    self.gemini_client = genai.Client(api_key=api_key)
                    if verbose:
                        print("[INFO] Initialized Gemini 3.0 Pro client")
                else:
                    raise ValueError("No Google API key found. Set GEMINI_API_KEY in .env")
            except ImportError:
                raise ImportError("google-genai package not installed. Run: pip install google-genai")

    @property
    def active_model(self) -> str:
        """Return the name of the active LLM model."""
        if self.dry_run:
            return "None (Dry Run)"
        # Default to Gemini 3 Pro Preview as configured in _call_gemini
        return "gemini-3-pro-preview"

    def _get_psalm_text(self, psalm_number: int) -> List[Tuple[int, str, str]]:
        """
        Get psalm text from tanakh database.

        Returns:
            List of (verse_number, hebrew_text, english_text) tuples
        """
        conn = sqlite3.connect(str(self.tanakh_db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT verse, hebrew, english
            FROM verses
            WHERE book_name = 'Psalms' AND chapter = ?
            ORDER BY verse
        """, (psalm_number,))

        verses = cursor.fetchall()
        conn.close()
        return verses

    def _call_gemini(
        self,
        prompt: str,
        temperature: float = 0.3,
        thinking_budget: int = 8192
    ) -> Tuple[str, Dict[str, int]]:
        """
        Call Gemini 3.0 Pro with high reasoning.

        Args:
            prompt: The prompt to send
            temperature: Generation temperature
            thinking_budget: Token budget for reasoning phase

        Returns:
            Tuple of (response_text, token_usage_dict)
        """
        if self.dry_run:
            print("\n" + "="*80)
            print("DRY RUN - Would send this prompt to Gemini 3.0 Pro:")
            print("="*80)
            print(prompt[:3000] + "..." if len(prompt) > 3000 else prompt)
            print("="*80 + "\n")
            return "[DRY RUN - No LLM response]", {"input": 0, "output": 0}

        from google.genai import types

        if self.verbose:
            print(f"[API] Calling Gemini 3 Pro (thinking_level=high)...")

        start_time = time.time()

        # Use Gemini 3 Pro with high reasoning level
        # Gemini 3 uses thinking_level instead of thinking_budget
        # Options: "none", "low", "medium", "high"
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

            # Calculate precise cost
            input_cost = (token_usage["input"] / 1_000_000) * self.GEMINI_3_PRO_INPUT_COST_PER_M
            output_cost = (token_usage["output"] / 1_000_000) * self.GEMINI_3_PRO_OUTPUT_COST_PER_M
            thinking_cost = (token_usage["thinking"] / 1_000_000) * self.GEMINI_3_PRO_THINKING_COST_PER_M
            token_usage["cost"] = input_cost + output_cost + thinking_cost

        return response_text, token_usage

    def _get_verse_hebrew(self, reference: str) -> Optional[str]:
        """
        Get full Hebrew text for a verse reference like 'Jeremiah 25:15'.

        Returns:
            The full Hebrew verse text, or None if not found.
        """
        # Parse the reference
        match = re.match(r'(\d?\s*\w+)\s+(\d+):(\d+)', reference)
        if not match:
            return None

        book_name = match.group(1).strip()
        chapter = int(match.group(2))
        verse = int(match.group(3))

        # Normalize book name for tanakh.db lookup
        # tanakh.db uses: "I Samuel", "II Kings", etc. (Roman numerals with space)
        # Figurative DB may use: "1 Samuel", "2 Kings", etc. (Arabic numerals)
        book_name_map = {
            # Direct matches (already in tanakh.db format)
            'Psalms': 'Psalms', 'Psalm': 'Psalms', 'Ps': 'Psalms',
            'Isaiah': 'Isaiah', 'Isa': 'Isaiah', 'Is': 'Isaiah',
            'Jeremiah': 'Jeremiah', 'Jer': 'Jeremiah',
            'Ezekiel': 'Ezekiel', 'Ezek': 'Ezekiel', 'Ez': 'Ezekiel',
            'Proverbs': 'Proverbs', 'Prov': 'Proverbs', 'Pr': 'Proverbs',
            'Job': 'Job',
            'Genesis': 'Genesis', 'Gen': 'Genesis',
            'Exodus': 'Exodus', 'Ex': 'Exodus', 'Exod': 'Exodus',
            'Leviticus': 'Leviticus', 'Lev': 'Leviticus',
            'Numbers': 'Numbers', 'Num': 'Numbers',
            'Deuteronomy': 'Deuteronomy', 'Deut': 'Deuteronomy', 'Dt': 'Deuteronomy',
            'Joshua': 'Joshua', 'Josh': 'Joshua',
            'Judges': 'Judges', 'Judg': 'Judges',
            'Ruth': 'Ruth',
            'Lamentations': 'Lamentations', 'Lam': 'Lamentations',
            'Esther': 'Esther', 'Est': 'Esther',
            'Daniel': 'Daniel', 'Dan': 'Daniel',
            'Ezra': 'Ezra',
            'Nehemiah': 'Nehemiah', 'Neh': 'Nehemiah',
            # Minor prophets
            'Hosea': 'Hosea', 'Hos': 'Hosea',
            'Joel': 'Joel',
            'Amos': 'Amos', 'Am': 'Amos',
            'Obadiah': 'Obadiah', 'Obad': 'Obadiah',
            'Jonah': 'Jonah', 'Jon': 'Jonah',
            'Micah': 'Micah', 'Mic': 'Micah',
            'Nahum': 'Nahum', 'Nah': 'Nahum',
            'Habakkuk': 'Habakkuk', 'Hab': 'Habakkuk',
            'Zephaniah': 'Zephaniah', 'Zeph': 'Zephaniah',
            'Haggai': 'Haggai', 'Hag': 'Haggai',
            'Zechariah': 'Zechariah', 'Zech': 'Zechariah',
            'Malachi': 'Malachi', 'Mal': 'Malachi',
            # Books with numbers - convert Arabic to Roman numerals for tanakh.db
            '1 Samuel': 'I Samuel', '1 Sam': 'I Samuel', '1Samuel': 'I Samuel', 'I Samuel': 'I Samuel',
            '2 Samuel': 'II Samuel', '2 Sam': 'II Samuel', '2Samuel': 'II Samuel', 'II Samuel': 'II Samuel',
            '1 Kings': 'I Kings', '1 Kgs': 'I Kings', '1Kings': 'I Kings', 'I Kings': 'I Kings',
            '2 Kings': 'II Kings', '2 Kgs': 'II Kings', '2Kings': 'II Kings', 'II Kings': 'II Kings',
            '1 Chronicles': 'I Chronicles', '1 Chr': 'I Chronicles', '1Chronicles': 'I Chronicles', 'I Chronicles': 'I Chronicles',
            '2 Chronicles': 'II Chronicles', '2 Chr': 'II Chronicles', '2Chronicles': 'II Chronicles', 'II Chronicles': 'II Chronicles',
            # Song of Songs
            'Song of Songs': 'Song of Songs', 'Song': 'Song of Songs', 'Songs': 'Song of Songs',
            'Canticles': 'Song of Songs', 'Song of Solomon': 'Song of Songs',
            # Ecclesiastes
            'Ecclesiastes': 'Ecclesiastes', 'Eccl': 'Ecclesiastes', 'Ecc': 'Ecclesiastes', 'Qohelet': 'Ecclesiastes',
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
        max_per_query: int = 15,
        include_full_hebrew: bool = True
    ) -> str:
        """Format figurative instances for inclusion in prompt, with full Hebrew text."""
        lines = []
        for i, inst in enumerate(instances[:max_per_query]):
            types_list = []
            if inst.is_metaphor: types_list.append("metaphor")
            if inst.is_simile: types_list.append("simile")
            if inst.is_personification: types_list.append("personification")
            if inst.is_metonymy: types_list.append("metonymy")
            if inst.is_hyperbole: types_list.append("hyperbole")
            if inst.is_idiom: types_list.append("idiom")
            types_str = ", ".join(types_list) if types_list else "other"

            target_str = " → ".join(inst.target[:3]) if inst.target else "N/A"
            vehicle_str = " → ".join(inst.vehicle[:3]) if inst.vehicle else "N/A"
            ground_str = " → ".join(inst.ground[:3]) if inst.ground else "N/A"

            # Get full Hebrew verse text if requested
            hebrew_phrase = inst.figurative_text_hebrew or 'N/A'
            full_hebrew_verse = ""
            if include_full_hebrew:
                full_verse = self._get_verse_hebrew(inst.reference)
                if full_verse and full_verse != hebrew_phrase:
                    full_hebrew_verse = f"\n*Full Hebrew verse*: {full_verse}"

            lines.append(f"""
**{inst.reference}** ({types_str}) - confidence: {inst.confidence:.2f}
*Figurative phrase (English)*: {inst.figurative_text}
*Figurative phrase (Hebrew)*: {hebrew_phrase}{full_hebrew_verse}
*Target*: {target_str}
*Vehicle*: {vehicle_str}
*Ground*: {ground_str}
*Explanation*: {inst.explanation[:300]}{'...' if len(inst.explanation) > 300 else ''}
""")
        return "\n".join(lines)

    def _build_phase1_prompt(
        self,
        psalm_number: int,
        psalm_text: List[Tuple[int, str, str]],
        micro_analyst_requests: List[FigurativeSearchRequest],
        initial_results: Dict[str, FigurativeBundle]
    ) -> str:
        """
        Build the Phase 1 prompt: Review requests, suggest improvements and follow-ups.
        """
        # Format psalm text
        psalm_lines = []
        for verse_num, hebrew, english in psalm_text:
            psalm_lines.append(f"**Verse {verse_num}**")
            psalm_lines.append(f"Hebrew: {hebrew}")
            psalm_lines.append(f"English: {english}")
            psalm_lines.append("")
        psalm_formatted = "\n".join(psalm_lines)

        # Format micro analyst requests
        requests_formatted = []
        for i, req in enumerate(micro_analyst_requests, 1):
            requests_formatted.append(f"""
**Request {i}: {req.vehicle_contains}**
- Search terms: {', '.join(req.vehicle_search_terms[:8])}...
- Notes: {req.notes}
""")

        # Format initial results summary
        results_summary = []
        for vehicle, bundle in initial_results.items():
            results_summary.append(f"- **{vehicle}**: {len(bundle.instances)} results")

        # Format sample results for each vehicle
        sample_results = []
        for vehicle, bundle in initial_results.items():
            if bundle.instances:
                sample_results.append(f"\n### Results for '{vehicle}' ({len(bundle.instances)} total)\n")
                sample_results.append(self._format_instances_for_prompt(bundle.instances, max_per_query=10))

        prompt = f"""You are analyzing the figurative language of Psalm {psalm_number} using a comprehensive biblical figurative concordance.

## THE PSALM

{psalm_formatted}

## MICRO ANALYST'S FIGURATIVE SEARCH REQUESTS

The micro analyst identified these figurative elements and requested searches:

{''.join(requests_formatted)}

## INITIAL SEARCH RESULTS SUMMARY

{chr(10).join(results_summary)}

## SAMPLE RESULTS BY VEHICLE

{''.join(sample_results)}

## YOUR TASK: PHASE 1 - ANALYZE AND RECOMMEND FOLLOW-UP SEARCHES

Based on the psalm's figurative language and these initial results, identify:

1. **GAPS IN THE MICRO ANALYST'S REQUESTS**
   - What figurative elements in the psalm were NOT requested but should be?
   - What alternative vehicles for the SAME TARGETS should we search?
     (e.g., if "shepherd" describes God's care, what OTHER vehicles describe God's care?)

2. **PROMISING FOLLOW-UP SEARCHES**
   For each major vehicle in the psalm, suggest follow-up searches that would help answer:
   - "Why THIS vehicle and not alternatives?" (search: same target, different vehicles)
   - "What ground does this specific vehicle activate?" (search: similar vehicles, compare grounds)
   - "How is this vehicle used elsewhere for similar targets?" (search: same vehicle, see target patterns)

3. **CROSS-PSALM PATTERNS**
   - Are there other psalms that use similar vehicle clusters? (worth searching)
   - Does this psalm's vehicle progression (e.g., shepherd→host) appear elsewhere?

**IMPORTANT SEARCH SYNTAX RULES:**
- Each search term must be a SINGLE WORD (e.g., "fortress", "rock", "refuge")
- Do NOT use boolean operators (OR, AND, NOT) - they will fail
- Do NOT use phrases or multiple words (e.g., "shadow of death" will fail)
- If you want to search for related concepts, create SEPARATE search entries for each word

Return your analysis as JSON:

```json
{{
  "analysis": {{
    "key_figurative_elements": [
      {{
        "verse": "23:1",
        "vehicle": "shepherd",
        "target": "YHWH/divine care",
        "why_significant": "Controls entire psalm imagery"
      }}
    ],
    "gaps_identified": [
      {{
        "missing_element": "description of what was missed",
        "suggested_search": {{"vehicle_contains": "term", "notes": "why"}}
      }}
    ]
  }},
  "follow_up_searches": [
    {{
      "purpose": "Find alternative vehicles for divine care/provision",
      "search": {{"vehicle_contains": "king", "notes": "Alternative to shepherd for divine relationship"}},
      "expected_insight": "What king imagery offers vs shepherd imagery"
    }},
    {{
      "purpose": "Find alternative vehicles for divine protection",
      "search": {{"vehicle_contains": "fortress", "notes": "Static protection vs mobile care"}},
      "expected_insight": "Contrast static vs dynamic protection metaphors"
    }},
    {{
      "purpose": "Another alternative for divine protection",
      "search": {{"vehicle_contains": "rock", "notes": "Stability/permanence imagery"}},
      "expected_insight": "What rock imagery offers that shepherd doesn't"
    }}
  ],
  "cross_psalm_patterns": [
    {{
      "pattern": "shepherd-to-host transition",
      "search_suggestion": "Look for other psalms with provision imagery shift"
    }}
  ]
}}
```

Focus on searches that will help answer: WHY did the poet choose THIS specific vehicle? What would be LOST if a different vehicle were used?
"""
        return prompt

    def _build_phase2_prompt(
        self,
        psalm_number: int,
        psalm_text: List[Tuple[int, str, str]],
        all_results: Dict[str, FigurativeBundle],
        phase1_analysis: Dict[str, Any]
    ) -> str:
        """
        Build the Phase 2 prompt: Synthesize insights from all search results.
        """
        # Format psalm text (abbreviated)
        psalm_lines = []
        for verse_num, hebrew, english in psalm_text:
            psalm_lines.append(f"v{verse_num}: {hebrew[:60]}... | {english[:80]}...")
        psalm_formatted = "\n".join(psalm_lines)

        # Format all results and track which vehicles have results
        all_results_formatted = []
        vehicles_with_results = []
        for vehicle, bundle in all_results.items():
            if bundle.instances:
                vehicles_with_results.append(f"{vehicle} ({len(bundle.instances)})")
                all_results_formatted.append(f"\n### '{vehicle}' ({len(bundle.instances)} results)\n")
                all_results_formatted.append(self._format_instances_for_prompt(bundle.instances, max_per_query=12))

        vehicles_summary = ", ".join(vehicles_with_results)
        num_vehicles_with_results = len(vehicles_with_results)

        prompt = f"""You are synthesizing insights about the figurative language of Psalm {psalm_number}.

## THE PSALM (abbreviated)
{psalm_formatted}

## ALL SEARCH RESULTS FROM FIGURATIVE CONCORDANCE
{''.join(all_results_formatted)}

## VEHICLES WITH RESULTS: {num_vehicles_with_results}
{vehicles_summary}

## PHASE 1 ANALYSIS (for context)
Key elements: {json.dumps(phase1_analysis.get('analysis', {}).get('key_figurative_elements', []), indent=2)}

## YOUR TASK: SYNTHESIZE FIGURATIVE INSIGHTS

Based on ALL the concordance data, generate comprehensive output. You MUST be thorough.

### 1. CURATED EXAMPLES BY VEHICLE

**CRITICAL REQUIREMENTS:**
- Provide curated examples for **ALL vehicles that returned results** (you have {num_vehicles_with_results} vehicles with results - provide examples for ALL of them, not just 5)
- Each vehicle should have **5-15 examples** - this is PER VEHICLE, not total
- If you searched for it and got results, you MUST include curated examples for it
- Do NOT skip vehicles just because they seem minor - even 3-5 examples from minor vehicles help

**ESPECIALLY IMPORTANT:**
- If the psalm has a TITLE with figurative language (e.g., "hind of the dawn" in Ps 22), you MUST analyze that vehicle thoroughly
- Title imagery often sets the interpretive key for the entire psalm

For each example, ALWAYS include:
- The Hebrew text (both the figurative phrase AND the full verse if available)
- Why this example illuminates the psalm's use of this vehicle

The number of examples per vehicle should reflect usefulness:
- 5-7 examples: For vehicles with fewer results or more repetitive patterns
- 8-12 examples: For vehicles with diverse, illuminating parallels
- 12-15 examples: For central/controlling vehicles where the range of usage is critical

### 2. FIGURATIVE INSIGHTS

**CRITICAL REQUIREMENTS:**
- Provide **4-5 insights** (aim for 5) - three is NOT enough for thorough analysis
- Each insight should be **100-150 words** (substantial paragraphs, not brief notes)
- Cover different aspects of the psalm's figurative language - don't cluster all insights around one verse

Each insight should:
- Identify a specific figurative element in Psalm {psalm_number}
- Show what the concordance reveals about this vehicle's usage elsewhere in Scripture
- Explain what the poet's CHOICE of this vehicle tells us
- Answer: "Why this vehicle and not alternatives?"

**Topics to consider for insights:**
- Why this specific vehicle rather than alternatives used for similar targets?
- What ground is being activated that other vehicles would not provide?
- How does this vehicle's usage elsewhere illuminate its meaning here?
- Are there surprising patterns, absences, or INVERSIONS of typical usage?
- How do vehicle transitions within the psalm create meaning?
- Does the title imagery connect to the body of the psalm?

### 3. FIGURATIVE STRUCTURE SUMMARY

**CRITICAL: Choose the structure_type that ACTUALLY fits this psalm:**

- **"descent"** or **"descent_ascent"**: For psalms that move from despair to hope, or from danger to deliverance (e.g., Ps 22 moves from abandonment → dissolution → predators → eventual rescue)
- **"contrast"**: For psalms with binary opposition (wicked vs. righteous, death vs. life, enemies vs. God)
- **"journey"**: For psalms with clear spatial/temporal progression (e.g., Ps 23: pasture → valley → table → house)
- **"dominant_metaphor"**: When one vehicle controls the entire psalm
- **"chiastic"**: When vehicles mirror around a center point
- **"thematic_clusters"**: When vehicles group by domain rather than sequence
- **"lament_structure"**: Complaint → petition → confidence → praise
- **"other"**: With explanation

Do NOT default to "journey" just because it's the example. Analyze what THIS psalm actually does with its figurative language.

Return as JSON:

```json
{{
  "curated_examples_by_vehicle": {{
    "shepherd": [
      {{
        "reference": "Isaiah 40:11",
        "type": "metaphor",
        "figurative_text_english": "Like a shepherd he tends his flock...",
        "figurative_text_hebrew": "כְּרֹעֶה עֶדְרוֹ יִרְעֶה",
        "full_verse_hebrew": "כְּרֹעֶה עֶדְרוֹ יִרְעֶה בִּזְרֹעוֹ יְקַבֵּץ טְלָאִים וּבְחֵיקוֹ יִשָּׂא עָלוֹת יְנַהֵל",
        "reason_selected": "Shows shepherd imagery applied to God at national scale vs Ps 23's individual 'my shepherd'"
      }},
      {{
        "reference": "Ezekiel 34:12",
        "type": "metaphor",
        "figurative_text_english": "As a shepherd seeks out his flock...",
        "figurative_text_hebrew": "כְּבַקָּרַת רֹעֶה עֶדְרוֹ",
        "full_verse_hebrew": "...",
        "reason_selected": "Shepherd actively seeking lost sheep - illuminates 'he leads me' in Ps 23:2-3"
      }}
    ],
    "hind": [
      {{
        "reference": "...",
        "type": "...",
        "figurative_text_english": "...",
        "figurative_text_hebrew": "...",
        "full_verse_hebrew": "...",
        "reason_selected": "..."
      }}
    ]
  }},
  "figurative_insights": [
    {{
      "title": "Why Shepherd Over King?",
      "insight": "The concordance reveals... [100-150 words of substantive analysis]",
      "verses_addressed": ["23:1"]
    }},
    {{
      "title": "Second Insight Title",
      "insight": "[100-150 words]...",
      "verses_addressed": ["..."]
    }},
    {{
      "title": "Third Insight Title",
      "insight": "[100-150 words]...",
      "verses_addressed": ["..."]
    }},
    {{
      "title": "Fourth Insight Title",
      "insight": "[100-150 words]...",
      "verses_addressed": ["..."]
    }},
    {{
      "title": "Fifth Insight Title",
      "insight": "[100-150 words]...",
      "verses_addressed": ["..."]
    }}
  ],
  "vehicle_map": {{
    "structure_type": "descent|descent_ascent|contrast|journey|dominant_metaphor|chiastic|thematic_clusters|lament_structure|other",
    "structure": "[describe the actual structure, e.g., 'abandonment (vv1-2) → bodily dissolution (vv14-15) → predator attack (vv12-13, 16-18) → deliverance hope (vv19-31)']",
    "structure_meaning": "[what this structure communicates about the psalm's theology/message]",
    "key_elements": [
      {{
        "element": "[specific vehicle transition or cluster]",
        "location": "[verse(s)]",
        "significance": "[why this matters]"
      }}
    ]
  }}
}}
```

**FINAL CHECKLIST before responding:**
- [ ] Did I include curated examples for ALL {num_vehicles_with_results} vehicles that had results?
- [ ] Does each vehicle have 5-15 examples (not 15 total)?
- [ ] Did I provide 4-5 insights (preferably 5)?
- [ ] Is each insight 100-150 words?
- [ ] Did I analyze title imagery if present?
- [ ] Does my structure_type actually match THIS psalm's pattern?

IMPORTANT: For EVERY curated example, include BOTH the Hebrew figurative phrase AND the full Hebrew verse. The Hebrew text is essential for scholarly commentary.

Remember: The goal is insights that would make a commentary SMARTER and more INTERESTING. Show how the concordance data illuminates the poet's choices in ways that weren't obvious before.
"""
        return prompt

    def _build_iterative_review_prompt(
        self,
        psalm_number: int,
        iteration: int,
        previous_searches: Dict[str, int],  # vehicle -> result count
        failed_searches: List[str],  # searches that returned 0 results
        psalm_text: List[Tuple[int, str, str]]
    ) -> str:
        """
        Build a prompt for iterative review of search results.
        Called after follow-up searches to decide if more searches are needed.
        """
        # Format psalm text briefly
        psalm_lines = [f"v{v}: {e[:60]}..." for v, h, e in psalm_text]
        psalm_formatted = "\n".join(psalm_lines)

        # Format search results summary
        results_summary = []
        for vehicle, count in previous_searches.items():
            status = "✓" if count >= self.MIN_RESULTS_FOR_USEFUL else "✗"
            results_summary.append(f"  {status} '{vehicle}': {count} results")

        failed_list = ", ".join(failed_searches) if failed_searches else "None"

        prompt = f"""You are reviewing search results for figurative analysis of Psalm {psalm_number}.

## ITERATION {iteration} of {self.max_iterations}

## THE PSALM
{psalm_formatted}

## SEARCH RESULTS SO FAR
{chr(10).join(results_summary)}

## FAILED SEARCHES (0 results)
{failed_list}

## YOUR TASK: DECIDE ON ADDITIONAL SEARCHES

Review the searches that returned 0 or few results. Consider:
1. Are there ALTERNATIVE TERMS that might find the same concept?
   - Example: "fortress" returned 0 → try "stronghold", "refuge", "rock"
   - Example: "chase" returned 0 → try "hunt", "seek", "follow"
2. Are there RELATED CONCEPTS worth exploring?
   - Example: "shepherd" is well-covered → also search "pasture", "flock", "grazing"
3. Are there GAPS in coverage for this psalm's figurative language?

**IMPORTANT SEARCH SYNTAX RULES:**
- Each search term must be a SINGLE WORD (e.g., "fortress", "rock", "refuge")
- Do NOT use boolean operators (OR, AND, NOT) - they will return 0 results
- Do NOT use phrases or multiple words - they will fail
- Create SEPARATE search entries for each alternative term

Return JSON with ONLY new searches to perform (don't repeat previous searches):

```json
{{
  "assessment": {{
    "well_covered_vehicles": ["list of vehicles with good results"],
    "needs_alternative_terms": ["list of concepts that failed but should retry with different terms"],
    "gaps_to_fill": ["figurative elements not yet searched"]
  }},
  "additional_searches": [
    {{
      "vehicle_contains": "refuge",
      "notes": "Alternative term for 'fortress' which returned 0",
      "expected_insight": "What refuge imagery offers that shepherd doesn't"
    }}
  ],
  "stop_searching": false,
  "stop_reason": null
}}
```

Set "stop_searching": true if:
- All major vehicles are well-covered (5+ results each)
- Additional searches are unlikely to yield new insights
- We've exhausted reasonable alternative terms for failed searches

Be strategic: Don't suggest searches just to search. Each additional search costs tokens.
"""
        return prompt

    def _parse_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract and parse JSON from LLM response."""
        # Try to find JSON block
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON
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

    def curate(
        self,
        psalm_number: int,
        micro_analyst_requests: List[FigurativeSearchRequest]
    ) -> FigurativeCuratorOutput:
        """
        Main entry point: curate figurative insights for a psalm.

        Uses an iterative loop:
        1. Execute initial searches from micro analyst
        2. Phase 1: LLM analyzes and recommends follow-ups
        3. Execute follow-ups, then review results
        4. If searches failed or gaps remain, iterate (up to max_iterations)
        5. Phase 2: Synthesize all results into curated examples and insights

        Args:
            psalm_number: The psalm to analyze
            micro_analyst_requests: Parsed figurative requests from micro analyst

        Returns:
            FigurativeCuratorOutput with curated examples and insights
        """
        total_tokens = {"input": 0, "output": 0, "thinking": 0, "cost": 0.0}
        all_search_results: Dict[str, FigurativeBundle] = {}
        iteration_log: List[Dict[str, Any]] = []

        # Get psalm text
        if self.verbose:
            print(f"\n[STEP 1] Loading Psalm {psalm_number} text...")
        psalm_text = self._get_psalm_text(psalm_number)
        if not psalm_text:
            raise ValueError(f"Could not load Psalm {psalm_number} from database")
        if self.verbose:
            print(f"         Loaded {len(psalm_text)} verses")

        # Execute initial searches from micro analyst requests
        if self.verbose:
            print(f"\n[STEP 2] Executing {len(micro_analyst_requests)} initial searches...")

        for req in micro_analyst_requests:
            search_request = FigurativeRequest(
                vehicle_contains=req.vehicle_contains,
                vehicle_search_terms=req.vehicle_search_terms,
                max_results=self.INITIAL_SEARCH_CAP,
                notes=req.notes
            )
            bundle = self.figurative_librarian.search(search_request)
            all_search_results[req.vehicle_contains] = bundle
            if self.verbose:
                count = len(bundle.instances)
                cap_note = f" (capped at {self.INITIAL_SEARCH_CAP})" if count >= self.INITIAL_SEARCH_CAP else ""
                print(f"         '{req.vehicle_contains}': {count} results{cap_note}")

        iteration_log.append({
            "phase": "initial",
            "searches": {v: len(b.instances) for v, b in all_search_results.items()}
        })

        # Phase 1: Analyze and recommend follow-up searches
        if self.verbose:
            print(f"\n[STEP 3] Phase 1: Analyzing results and recommending follow-ups...")

        phase1_prompt = self._build_phase1_prompt(
            psalm_number, psalm_text, micro_analyst_requests, all_search_results
        )

        phase1_response, phase1_tokens = self._call_gemini(phase1_prompt, thinking_budget=8192)
        total_tokens["input"] += phase1_tokens["input"]
        total_tokens["output"] += phase1_tokens["output"]
        total_tokens["thinking"] += phase1_tokens.get("thinking", 0)
        total_tokens["cost"] += phase1_tokens.get("cost", 0.0)

        phase1_analysis = self._parse_json_from_response(phase1_response)

        if self.verbose and phase1_analysis:
            follow_ups = phase1_analysis.get("follow_up_searches", [])
            print(f"         Recommended {len(follow_ups)} follow-up searches")

        # ITERATIVE SEARCH LOOP
        iteration = 1
        current_review = None
        while iteration <= self.max_iterations and not self.dry_run:
            # Get follow-up searches for this iteration
            if iteration == 1:
                follow_ups = phase1_analysis.get("follow_up_searches", []) if phase1_analysis else []
            else:
                # Use searches from iterative review
                follow_ups = current_review.get("additional_searches", []) if current_review else []

            if not follow_ups:
                if self.verbose:
                    print(f"         No follow-up searches for iteration {iteration}")
                break

            if self.verbose:
                print(f"\n[STEP 4.{iteration}] Iteration {iteration}: Executing {len(follow_ups)} follow-up searches...")

            # Execute follow-up searches
            iteration_results = {}
            for follow_up in follow_ups[:8]:  # Limit to 8 per iteration
                search_spec = follow_up.get("search", follow_up)  # Handle both formats
                vehicle = search_spec.get("vehicle_contains", "")
                if vehicle and vehicle not in all_search_results:
                    search_request = FigurativeRequest(
                        vehicle_contains=vehicle,
                        max_results=self.FOLLOWUP_SEARCH_CAP,
                        notes=search_spec.get("notes", "")
                    )
                    bundle = self.figurative_librarian.search(search_request)
                    all_search_results[vehicle] = bundle
                    count = len(bundle.instances)
                    iteration_results[vehicle] = count
                    if self.verbose:
                        status = "✓" if count >= self.MIN_RESULTS_FOR_USEFUL else "✗"
                        cap_note = f" (capped at {self.FOLLOWUP_SEARCH_CAP})" if count >= self.FOLLOWUP_SEARCH_CAP else ""
                        print(f"         {status} '{vehicle}': {count} results{cap_note}")

            iteration_log.append({
                "phase": f"iteration_{iteration}",
                "searches": iteration_results
            })

            # Check if we should continue iterating
            failed_searches = [v for v, count in iteration_results.items() if count == 0]
            all_counts = {v: len(b.instances) for v, b in all_search_results.items()}

            # If no failures and we have enough results, stop
            if not failed_searches and all(c >= self.MIN_RESULTS_FOR_USEFUL for c in all_counts.values()):
                if self.verbose:
                    print(f"         All searches successful, stopping iteration")
                break

            # Ask LLM if we should continue
            if iteration < self.max_iterations:
                if self.verbose:
                    print(f"\n[STEP 4.{iteration}b] Reviewing iteration {iteration} results...")

                review_prompt = self._build_iterative_review_prompt(
                    psalm_number, iteration, all_counts, failed_searches, psalm_text
                )
                review_response, review_tokens = self._call_gemini(review_prompt, thinking_budget=4096)
                total_tokens["input"] += review_tokens["input"]
                total_tokens["output"] += review_tokens["output"]
                total_tokens["thinking"] += review_tokens.get("thinking", 0)
                total_tokens["cost"] += review_tokens.get("cost", 0.0)

                current_review = self._parse_json_from_response(review_response)

                if current_review.get("stop_searching", False):
                    if self.verbose:
                        reason = current_review.get("stop_reason", "LLM decided to stop")
                        print(f"         Stopping: {reason}")
                    break

                additional = current_review.get("additional_searches", [])
                if self.verbose:
                    print(f"         LLM recommended {len(additional)} more searches")

                if not additional:
                    break

            iteration += 1

        # Phase 2: Synthesize insights with all collected results
        if self.verbose:
            total_results = sum(len(b.instances) for b in all_search_results.values())
            print(f"\n[STEP 5] Phase 2: Synthesizing insights from {len(all_search_results)} vehicles ({total_results} total results)...")

        phase2_prompt = self._build_phase2_prompt(
            psalm_number, psalm_text, all_search_results, phase1_analysis
        )

        phase2_response, phase2_tokens = self._call_gemini(phase2_prompt, thinking_budget=12288)
        total_tokens["input"] += phase2_tokens["input"]
        total_tokens["output"] += phase2_tokens["output"]
        total_tokens["thinking"] += phase2_tokens.get("thinking", 0)
        total_tokens["cost"] += phase2_tokens.get("cost", 0.0)

        phase2_analysis = self._parse_json_from_response(phase2_response)

        # Build output
        return FigurativeCuratorOutput(
            psalm_number=psalm_number,
            curated_examples_by_vehicle=phase2_analysis.get("curated_examples_by_vehicle", {}),
            figurative_insights=phase2_analysis.get("figurative_insights", []),
            search_summary={
                "initial_searches": len(micro_analyst_requests),
                "total_iterations": iteration,
                "total_results": sum(len(b.instances) for b in all_search_results.values()),
                "vehicles_searched": list(all_search_results.keys()),
                "results_by_vehicle": {v: len(b.instances) for v, b in all_search_results.items()},
                "vehicle_map": phase2_analysis.get("vehicle_map", {})
            },
            iteration_log=iteration_log,
            token_usage=total_tokens,
            raw_llm_response=phase2_response
        )
