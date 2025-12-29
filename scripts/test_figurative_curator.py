"""
Test script for the Figurative Curator - an LLM-enhanced agent that transforms
raw figurative concordance results into interpretive insights.

This script allows testing the curator independently of the full pipeline.

Usage:
    python scripts/test_figurative_curator.py --psalm 23
    python scripts/test_figurative_curator.py --psalm 23 --log logs/micro_analyst_v2_20251226_091518.log
    python scripts/test_figurative_curator.py --psalm 22 --verbose
    python scripts/test_figurative_curator.py --psalm 23 --dry-run  # Just show what would be sent to LLM

Author: Claude Code
Date: 2025-12-29
"""

import argparse
import io
import json
import os
import re
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

# Fix Windows console encoding for Hebrew output
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.figurative_librarian import FigurativeLibrarian, FigurativeRequest, FigurativeBundle

# Load environment variables
load_dotenv()


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
    figurative_insights: List[Dict[str, str]]  # 3-5 prose insights
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
        max_iterations: int = 3
    ):
        """
        Initialize the Figurative Curator.

        Args:
            google_api_key: Google API key (defaults to GEMINI_API_KEY env var)
            verbose: Print detailed progress
            dry_run: Don't call LLM, just show prompts
            max_iterations: Maximum review → search → review cycles (default 3)
        """
        self.verbose = verbose
        self.dry_run = dry_run
        self.max_iterations = max_iterations
        self.gemini_client = None

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
                    print("[ERROR] No Google API key found. Set GEMINI_API_KEY in .env")
                    sys.exit(1)
            except ImportError:
                print("[ERROR] google-genai package not installed. Run: pip install google-genai")
                sys.exit(1)

    def _get_psalm_text(self, psalm_number: int) -> List[Tuple[int, str, str]]:
        """
        Get psalm text from tanakh database.

        Returns:
            List of (verse_number, hebrew_text, english_text) tuples
        """
        db_path = PROJECT_ROOT / "database" / "tanakh.db"
        conn = sqlite3.connect(str(db_path))
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

        db_path = PROJECT_ROOT / "database" / "tanakh.db"
        try:
            conn = sqlite3.connect(str(db_path))
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

        # Format all results
        all_results_formatted = []
        for vehicle, bundle in all_results.items():
            if bundle.instances:
                all_results_formatted.append(f"\n### '{vehicle}' ({len(bundle.instances)} results)\n")
                all_results_formatted.append(self._format_instances_for_prompt(bundle.instances, max_per_query=12))

        prompt = f"""You are synthesizing insights about the figurative language of Psalm {psalm_number}.

## THE PSALM (abbreviated)
{psalm_formatted}

## ALL SEARCH RESULTS FROM FIGURATIVE CONCORDANCE
{''.join(all_results_formatted)}

## PHASE 1 ANALYSIS (for context)
Key elements: {json.dumps(phase1_analysis.get('analysis', {}).get('key_figurative_elements', []), indent=2)}

## YOUR TASK: SYNTHESIZE FIGURATIVE INSIGHTS

Based on ALL the concordance data, generate:

### 1. CURATED EXAMPLES BY VEHICLE (5-15 examples per major vehicle)
For EACH major vehicle in Psalm {psalm_number}, select the 5-15 most illuminating examples from the concordance results.
Group examples by vehicle. For each example, ALWAYS include:
- The Hebrew text (both the figurative phrase AND the full verse if available)
- Why this example illuminates the psalm's use of this vehicle

The number of examples per vehicle should reflect usefulness:
- 5-7 examples: If the vehicle is minor or examples are repetitive
- 8-12 examples: For major vehicles with diverse, illuminating parallels
- 12-15 examples: For central vehicles (like "shepherd" in Ps 23) where the range of usage is critical

### 2. FIGURATIVE INSIGHTS (3-5 prose paragraphs)
Write 3-5 substantial insights (100-150 words each) that a commentary writer could directly incorporate. Each insight should:
- Identify a specific figurative element in Psalm {psalm_number}
- Show what the concordance reveals about this vehicle's usage elsewhere
- Explain what the poet's CHOICE of this vehicle tells us
- Answer: "Why this and not alternatives?"

Focus on questions like:
- Why this specific vehicle rather than alternatives used for similar targets?
- What ground is being activated that other vehicles would not provide?
- How does this vehicle's usage elsewhere illuminate its meaning here?
- Are there surprising patterns, absences, or transformations?

### 3. FIGURATIVE STRUCTURE SUMMARY
Create a summary of the psalm's figurative architecture. This should show how vehicles relate to each other and to the psalm's movement.

**Be creative and adapt the format to the psalm's actual structure:**
- For psalms with a clear journey/progression (like Ps 23): Show the movement from one vehicle domain to another
- For psalms with contrasting pairs (e.g., wicked vs. righteous): Show the binary opposition of vehicle clusters
- For psalms with a single dominant metaphor: Show how the metaphor is developed and varied
- For psalms with chiastic structure: Show how vehicles mirror each other around a center
- For psalms with thematic clustering: Group vehicles by the domain they illuminate

The key is to reveal the psalm's figurative LOGIC - how do the metaphors work together?

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
    "table": [
      {{
        "reference": "Ezekiel 39:20",
        "type": "metaphor",
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
      "insight": "The concordance reveals...",
      "verses_addressed": ["23:1"]
    }}
  ],
  "vehicle_map": {{
    "structure_type": "journey|contrast|dominant_metaphor|chiastic|thematic_clusters|other",
    "structure": "shepherd (vv1-4) → host (v5) → permanent dweller (v6)",
    "structure_meaning": "Movement from pastoral dependence through royal banquet to temple presence",
    "key_elements": [
      {{
        "element": "shepherd/sheep → host/guest transition",
        "location": "v5",
        "significance": "Shift from animal to human status; from wilderness to civilization"
      }}
    ]
  }}
}}
```

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


def parse_micro_analyst_log(log_path: Path) -> Tuple[int, List[FigurativeSearchRequest]]:
    """
    Parse a micro analyst log file to extract psalm number and figurative requests.

    Args:
        log_path: Path to the log file

    Returns:
        Tuple of (psalm_number, list of FigurativeSearchRequest)
    """
    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract psalm number
    psalm_match = re.search(r'MICROANALYST V2: Psalm (\d+)', content)
    if not psalm_match:
        raise ValueError("Could not find psalm number in log")
    psalm_number = int(psalm_match.group(1))

    # Extract figurative requests section
    requests = []

    # Find the FIGURATIVE LANGUAGE REQUESTS section
    fig_section = re.search(
        r'FIGURATIVE LANGUAGE REQUESTS \(detailed\):(.+?)(?=\n\[STAGE|\nRESEARCH BUNDLE|$)',
        content,
        re.DOTALL
    )

    if fig_section:
        section_text = fig_section.group(1)

        # Parse each request block
        request_blocks = re.split(r'\[\d+\] Verse:', section_text)
        for block in request_blocks[1:]:  # Skip first empty split
            vehicle_match = re.search(r'vehicle_contains: (\w+)', block)
            terms_match = re.search(r"vehicle_search_terms: \[([^\]]+)\]", block)
            notes_match = re.search(r'notes: (.+?)(?=\n|$)', block)

            if vehicle_match:
                vehicle = vehicle_match.group(1)
                terms = []
                if terms_match:
                    terms_str = terms_match.group(1)
                    terms = [t.strip().strip("'\"") for t in terms_str.split(',')]
                notes = notes_match.group(1) if notes_match else ""

                requests.append(FigurativeSearchRequest(
                    vehicle_contains=vehicle,
                    vehicle_search_terms=terms,
                    notes=notes
                ))

    return psalm_number, requests


def create_sample_requests(psalm_number: int) -> List[FigurativeSearchRequest]:
    """
    Create sample figurative requests for a psalm (for testing without a log file).
    These are based on typical requests for well-known psalms.
    """
    samples = {
        23: [
            FigurativeSearchRequest("shepherd", ["shepherd", "sheep", "flock", "pasture", "graze"], "Controlling metaphor for divine care"),
            FigurativeSearchRequest("pasture", ["pasture", "grass", "green", "water", "still"], "Provision and rest imagery"),
            FigurativeSearchRequest("path", ["path", "way", "road", "walk", "lead"], "Guidance metaphor"),
            FigurativeSearchRequest("valley", ["valley", "shadow", "darkness", "death", "deep"], "Threat imagery"),
            FigurativeSearchRequest("rod", ["rod", "staff", "stick", "shepherd staff"], "Shepherd implements"),
            FigurativeSearchRequest("table", ["table", "feast", "banquet", "meal", "host"], "Hospitality imagery"),
            FigurativeSearchRequest("oil", ["oil", "anoint", "pour", "head"], "Anointing imagery"),
            FigurativeSearchRequest("cup", ["cup", "overflow", "full", "abundance"], "Blessing overflow"),
            FigurativeSearchRequest("pursue", ["pursue", "follow", "chase", "hunt"], "Reversed pursuit metaphor"),
            FigurativeSearchRequest("house", ["house", "dwell", "temple", "dwelling"], "Temple/dwelling imagery"),
        ],
        22: [
            FigurativeSearchRequest("hind", ["hind", "doe", "deer", "gazelle", "dawn"], "Title imagery"),
            FigurativeSearchRequest("roaring", ["roar", "roaring", "cry", "lion roar"], "Prayer as animal cry"),
            FigurativeSearchRequest("worm", ["worm", "maggot", "insect", "lowly"], "Extreme degradation"),
            FigurativeSearchRequest("bulls", ["bull", "bulls", "ox", "Bashan"], "Enemy as cattle"),
            FigurativeSearchRequest("lion", ["lion", "lions", "mouth", "tear"], "Predator imagery"),
            FigurativeSearchRequest("water", ["water", "pour", "poured", "liquid"], "Bodily dissolution"),
            FigurativeSearchRequest("wax", ["wax", "melt", "melting", "heart"], "Heart liquefaction"),
            FigurativeSearchRequest("potsherd", ["potsherd", "pottery", "clay", "dry"], "Desiccation metaphor"),
            FigurativeSearchRequest("dust", ["dust", "earth", "death", "grave"], "Mortality imagery"),
            FigurativeSearchRequest("dogs", ["dog", "dogs", "pack", "scavenger"], "Unclean scavengers"),
        ]
    }

    return samples.get(psalm_number, samples[23])  # Default to Psalm 23


def format_output(output: FigurativeCuratorOutput) -> str:
    """Format curator output as readable markdown."""
    lines = []
    lines.append(f"# Figurative Curator Output: Psalm {output.psalm_number}")
    lines.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

    # Token usage and cost
    lines.append("## Token Usage & Cost")
    lines.append(f"- Input: {output.token_usage.get('input', 0):,}")
    lines.append(f"- Output: {output.token_usage.get('output', 0):,}")
    lines.append(f"- Thinking: {output.token_usage.get('thinking', 0):,}")
    total_tokens = output.token_usage.get('input', 0) + output.token_usage.get('output', 0) + output.token_usage.get('thinking', 0)
    lines.append(f"- **Total tokens: {total_tokens:,}**")
    cost = output.token_usage.get('cost', 0.0)
    lines.append(f"- **Cost: ${cost:.4f}** (Gemini 3 Pro @ $2/M input, $12/M output)\n")

    # Search summary
    lines.append("## Search Summary")
    summary = output.search_summary
    lines.append(f"- Initial searches: {summary.get('initial_searches', 0)}")
    lines.append(f"- Total iterations: {summary.get('total_iterations', 1)}")
    lines.append(f"- Total results found: {summary.get('total_results', 0)}")
    lines.append(f"- Vehicles searched: {', '.join(summary.get('vehicles_searched', []))}")

    # Results by vehicle
    if summary.get("results_by_vehicle"):
        lines.append("\n### Results by Vehicle")
        for vehicle, count in summary["results_by_vehicle"].items():
            status = "✓" if count >= 3 else "✗"
            lines.append(f"- {status} **{vehicle}**: {count} results")
    lines.append("")

    # Iteration log
    if output.iteration_log:
        lines.append("### Iteration Log")
        for entry in output.iteration_log:
            phase = entry.get("phase", "?")
            searches = entry.get("searches", {})
            if searches:
                search_summary = ", ".join(f"{v}:{c}" for v, c in searches.items())
                lines.append(f"- **{phase}**: {search_summary}")
        lines.append("")

    # Figurative Structure Summary (was Vehicle Map)
    if summary.get("vehicle_map"):
        vm = summary["vehicle_map"]
        lines.append("### Figurative Structure")
        # Show structure type if present (new flexible format)
        if vm.get("structure_type"):
            lines.append(f"**Type**: {vm.get('structure_type', 'N/A')}")
        lines.append(f"**Structure**: {vm.get('structure', 'N/A')}")
        # Support both old format (progression_meaning) and new format (structure_meaning)
        meaning = vm.get('structure_meaning') or vm.get('progression_meaning', 'N/A')
        lines.append(f"**Meaning**: {meaning}")
        # Support both old format (key_transitions) and new format (key_elements)
        elements = vm.get("key_elements") or vm.get("key_transitions")
        if elements:
            lines.append("\n**Key elements**:")
            for el in elements:
                # New format uses 'element' and 'location'
                if 'element' in el:
                    lines.append(f"- {el.get('element', '?')} (v{el.get('location', '?')}): {el.get('significance', '')}")
                # Old format uses 'from', 'to', 'at_verse'
                elif 'from' in el:
                    lines.append(f"- {el.get('from', '?')} → {el.get('to', '?')} (v{el.get('at_verse', '?')}): {el.get('significance', '')}")
        lines.append("")

    # Figurative Insights
    lines.append("## Figurative Insights\n")
    for i, insight in enumerate(output.figurative_insights, 1):
        title = insight.get("title", f"Insight {i}")
        text = insight.get("insight", "")
        verses = insight.get("verses_addressed", [])

        lines.append(f"### {i}. {title}")
        if verses:
            lines.append(f"*Verses: {', '.join(verses)}*\n")
        lines.append(text)
        lines.append("")

    # Curated Examples by Vehicle
    lines.append("## Curated Examples by Vehicle\n")

    if isinstance(output.curated_examples_by_vehicle, dict):
        # New format: grouped by vehicle
        for vehicle, examples in output.curated_examples_by_vehicle.items():
            lines.append(f"### Vehicle: {vehicle.upper()} ({len(examples)} examples)\n")

            for i, ex in enumerate(examples, 1):
                ref = ex.get("reference", "Unknown")
                fig_type = ex.get("type", "?")
                text_en = ex.get("figurative_text_english", ex.get("figurative_text", ""))
                text_he = ex.get("figurative_text_hebrew", "")
                full_verse_he = ex.get("full_verse_hebrew", "")
                reason = ex.get("reason_selected", "")

                lines.append(f"#### {i}. {ref} ({fig_type})")
                if text_en:
                    lines.append(f"> {text_en}")
                if text_he:
                    lines.append(f">\n> **Hebrew**: {text_he}")
                if full_verse_he and full_verse_he != text_he:
                    lines.append(f">\n> **Full verse**: {full_verse_he}")
                if reason:
                    lines.append(f"\n**Why selected**: {reason}")
                lines.append("")
    else:
        # Fallback: old flat list format
        for i, ex in enumerate(output.curated_examples_by_vehicle, 1):
            ref = ex.get("reference", "Unknown")
            vehicle = ex.get("vehicle", "?")
            fig_type = ex.get("type", "?")
            text = ex.get("figurative_text", "")
            reason = ex.get("reason_selected", "")

            lines.append(f"### {i}. {ref} — {vehicle} ({fig_type})")
            lines.append(f"> {text}")
            lines.append(f"\n**Why selected**: {reason}\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Test the Figurative Curator on a psalm",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/test_figurative_curator.py --psalm 23
    python scripts/test_figurative_curator.py --psalm 23 --log logs/micro_analyst_v2_20251226_091518.log
    python scripts/test_figurative_curator.py --psalm 22 --verbose --dry-run
        """
    )
    parser.add_argument("--psalm", type=int, required=True, help="Psalm number to analyze")
    parser.add_argument("--log", type=str, help="Path to micro analyst log file (optional)")
    parser.add_argument("--output", type=str, help="Output file path (default: stdout)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed progress")
    parser.add_argument("--dry-run", action="store_true", help="Don't call LLM, just show prompts")

    args = parser.parse_args()

    # Get figurative requests
    if args.log:
        log_path = Path(args.log)
        if not log_path.exists():
            print(f"Error: Log file not found: {log_path}")
            sys.exit(1)
        psalm_number, requests = parse_micro_analyst_log(log_path)
        if psalm_number != args.psalm:
            print(f"Warning: Log is for Psalm {psalm_number}, but --psalm {args.psalm} specified. Using log's psalm.")
            args.psalm = psalm_number
        print(f"Parsed {len(requests)} figurative requests from log file")
    else:
        requests = create_sample_requests(args.psalm)
        print(f"Using {len(requests)} sample requests for Psalm {args.psalm}")

    # Initialize curator
    curator = FigurativeCurator(
        verbose=args.verbose,
        dry_run=args.dry_run
    )

    # Run curation
    print(f"\nCurating figurative insights for Psalm {args.psalm}...")
    print("=" * 60)

    try:
        output = curator.curate(args.psalm, requests)
    except Exception as e:
        print(f"\nError during curation: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    # Format and output results
    formatted = format_output(output)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(formatted, encoding='utf-8')
        print(f"\nOutput written to: {output_path}")
    else:
        print("\n" + "=" * 60)
        print(formatted)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Psalm: {output.psalm_number}")
    # Count curated examples across all vehicles
    total_examples = sum(len(exs) for exs in output.curated_examples_by_vehicle.values()) if isinstance(output.curated_examples_by_vehicle, dict) else len(output.curated_examples_by_vehicle)
    print(f"Vehicles with curated examples: {len(output.curated_examples_by_vehicle)}")
    print(f"Total curated examples: {total_examples}")
    print(f"Figurative insights: {len(output.figurative_insights)}")
    print(f"Total iterations: {output.search_summary.get('total_iterations', 1)}")
    total_tokens = output.token_usage.get('input', 0) + output.token_usage.get('output', 0) + output.token_usage.get('thinking', 0)
    print(f"Total tokens: {total_tokens:,}")

    if not args.dry_run:
        # Use precise cost from tracker
        cost = output.token_usage.get("cost", 0.0)
        print(f"Cost: ${cost:.4f} (Gemini 3 Pro)")


if __name__ == "__main__":
    main()
