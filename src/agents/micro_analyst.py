"""
MicroAnalyst Agent v2 - Pass 2 of Five-Pass Scholar-Writer Architecture

REDESIGNED PHILOSOPHY (2025-10-17):
- CURIOSITY-DRIVEN rather than thesis-driven
- DISCOVERY MODE: Find what's interesting, puzzling, surprising
- Quick verse-by-verse FIRST PASS to identify research opportunities
- Smart research requests based on actual discoveries
- MINIMAL ANALYSIS: Pass comprehensive research forward to SynthesisWriter

THREE-STAGE PROCESS:
Stage 1: Quick Verse-by-Verse Discovery Pass
    - Read each verse with fresh eyes
    - Notice patterns, surprises, puzzles, curious word choices
    - Identify verses with figurative language
    - Note interesting poetic devices
    - Keep macro thesis in peripheral vision (not central focus)
    - Log observations for each verse

Stage 2: Generate Research Requests
    - Based on discoveries from Stage 1
    - Request lexicon entries for curious/important words
    - Request concordances for interesting patterns
    - Request figurative analysis for metaphorical verses
    - Request commentary for puzzling/complex verses

Stage 3: Assemble Research Bundle
    - Call Research Assembler with requests
    - Return MicroAnalysis (discovery notes) + ResearchBundle

Model: Claude Sonnet 4.5 with extended thinking
Input: MacroAnalysis + Psalm text (Hebrew/English/LXX) + RAG context
Output: MicroAnalysis (discovery notes) + ResearchBundle

Author: Claude (Anthropic)
Date: 2025-10-17 (Phase 3b redesign)
"""

import sys
import os
import json
from pathlib import Path
from typing import Tuple, Optional, Dict, List
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Handle imports for both module and script usage
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.schemas.analysis_schemas import MacroAnalysis, MicroAnalysis, VerseCommentary
    from src.agents.rag_manager import RAGManager
    from src.agents.research_assembler import ResearchAssembler, ResearchRequest, ResearchBundle
    from src.agents.scholar_researcher import ScholarResearchRequest
    from src.data_sources.tanakh_database import TanakhDatabase
    from src.utils.logger import get_logger
    from src.utils.cost_tracker import CostTracker
else:
    from ..schemas.analysis_schemas import MacroAnalysis, MicroAnalysis, VerseCommentary
    from .rag_manager import RAGManager
    from .research_assembler import ResearchAssembler, ResearchRequest, ResearchBundle
    from .scholar_researcher import ScholarResearchRequest
    from ..data_sources.tanakh_database import TanakhDatabase
    from ..utils.logger import get_logger
    from ..utils.cost_tracker import CostTracker
from .phonetic_analyst import PhoneticAnalyst


# Stage 1: Quick Discovery Pass Prompt
DISCOVERY_PASS_PROMPT = """You are conducting a QUICK DISCOVERY PASS of Psalm {psalm_number}.

Your goal: Find what's INTERESTING, CURIOUS, PUZZLING, or SURPRISING in each verse. You have been provided with authoritative phonetic transcriptions to aid in analyzing sound patterns.

MACRO CONTEXT (for peripheral awareness - NOT your primary focus):

{macro_analysis}

---

PSALM TEXT & PHONETIC DATA:

{psalm_text_with_phonetics}

---

RAG SCHOLARLY CONTEXT:

{rag_context}

---

DISCOVERY TASK:

Read through each verse ATOMICALLY, with FRESH EYES. For each verse, note:

1. **Lexical Insights**: Key words/phrases worth investigating?
   - **EXACT FORM**: Copy the phrase letter-for-letter from the verse, including all prefixes and suffixes
     ✗ WRONG: "צל כנפים" when verse has "בְּצֵל כְּנָפֶיךָ"
     ✓ RIGHT: "בצל כנפיך" (exact form with ב prefix and יך suffix)
   - **VARIANTS**: Generate phrase variations across morphological categories:
     - Person: "בצל כנפי" (my), "בצל כנפיך" (your), "בצל כנפיו" (his)
     - Number: "בצל כנף" (singular wing), "בצל כנפים" (wings)
     - With/without prefix: "צל כנפיך" (without ב)
     - Verb phrases by tense: "פקדת לילה" (perfect), "תפקד לילה" (imperfect), "פקד לילה" (infinitive)
   - DO NOT include synonyms - only morphological forms of the exact phrase
2. **Poetic Patterns**: Parallelism? Wordplay? Sound patterns? Repetition?
   - **IMPORTANT**: When analyzing sound patterns (alliteration, assonance), you MUST use the provided phonetic transcription as your ground truth. Do not guess at pronunciation.
3. **Figurative Language**: Metaphors? Similes? Personification? What images are used?
4. **Puzzles/Conundrums**: Ambiguous phrasing? Interpretive challenges? Strange syntax?
5. **Surprises**: Anything unexpected given the genre/context?
6. **LXX Insights**: How did ancient Greek translators interpret the Hebrew? Any revealing choices?
7. **Connections**: Does this verse relate to macro thesis? If so, how? If NOT, what else is interesting?

IMPORTANT PRINCIPLES:
- Be CURIOUS, not confirmatory
- Notice what's ACTUALLY in the text, not what you expect
- The macro thesis may be WRONG or incomplete - find what's genuinely interesting
- Look for LINGUISTIC puzzles, poetic cleverness, theological depth
- Don't force everything to "support the thesis" - find intrinsic interest

After noting discoveries for each verse, formulate 5 or more **INTERESTING QUESTIONS** about:
- Unusual word choices and phrases (e.g., why THIS word/phrase and not another?)
- Striking poetic devices and their function
- Surprising grammatical or syntactic patterns
- Puzzling theological or rhetorical moves
- Interpretive conundrums that merit exploration

Examples of good questions:
- "Why did the poet choose 'בְּנֵי אֵלִים' (sons of gods) rather than a more monotheistic formulation?"
- "What is the function of the unusual phrase 'הֲדַר כְּבוֹד הוֹדֶךָ' - is this poetic accumulation or does each word contribute distinct meaning?"
- "Why does the psalmist shift from perfect tense to imperfect at verse 7?"

These questions should guide the Synthesizer and Editor to address genuinely interesting aspects of the psalm.

OUTPUT FORMAT: Return ONLY valid JSON. Do NOT include the phonetic transcription in your output.

{
  "verse_discoveries": [
    {
      "verse_number": 1,
      "observations": "Quick summary of what's interesting/curious in this verse (2-4 sentences). Focus on discoveries, not analysis.",
      "lexical_insights": [  // Hebrew words/phrases worth investigating
        {
          "phrase": "בְּנֵי אֵלִים",  // Exact form from verse
          "variants": [],  // Morphological variants of word or phrase that should be looked for
          "notes": "Divine council beings - key theological term"  // Why worth investigating
        },
        {
          "phrase": "קוֹל",
          "variants": ["קולו", "קולך", "קולי"],  // With possessive suffixes if context suggests
          "notes": "Voice of divine speech - repeated formula"
        }
      ],
      "poetic_features": ["anaphora setup", "divine council imagery"],
      "figurative_elements": ["sons of gods - metaphor or literal?"],
      "puzzles": ["Why 'sons of gods' (plural) in monotheistic psalm?"],
      "lxx_insights": "LXX uses 'υἱοὶ θεοῦ' - shows early plural divine beings interpretation",
      "macro_relation": "Supports divine council framework from thesis" // OR "Interesting independent of thesis: ..."
    },
    {
      "verse_number": 2,
      "observations": "...",
      ...
    },
    ... (all Psalm {psalm_number} verses)
  ],
  "overall_patterns": [
    "Sevenfold 'voice of LORD' anaphora - completeness symbolism worth exploring",
    "Geographic progression (waters → Lebanon → wilderness → temple) - cosmological journey?",
    "Shift from imperative (vv.1-2) to descriptive (vv.3-9) to blessing (vv.10-11) - rhetorical strategy"
  ],
  "interesting_questions": [
    "Why did the poet choose the phrase 'בְּנֵי אֵלִים' (sons of gods) rather than a more monotheistic formulation?",
    "What is the significance of the sevenfold repetition of 'קוֹל יְהוָה' (voice of the LORD)?",
    "How do the unusual word combinations like 'הֲדַר כְּבוֹד הוֹדֶךָ' function poetically?",
    "Why does the psalm shift from imperative to descriptive mood at verse 3?",
    "What does the rare word 'מַבּוּל' (flood) contribute to the cosmological imagery?"
  ],
  "research_priorities": [
    "LEXICON: Focus on storm vocabulary, divine epithets, rare geographical terms",
    "CONCORDANCE: Track 'voice of LORD' formula, divine council language, geographic patterns",
    "FIGURATIVE: All verses with water/storm/nature imagery",
    "COMMENTARY: Verses with interpretive puzzles (e.g., mabbul, divine council)"
  ]
}

Return ONLY the JSON object, no additional text.
"""


# Commentary instruction templates
COMMENTARY_ALL_VERSES = """**REQUEST COMMENTARY FOR EVERY VERSE** in the psalm
   - All 7 available commentators will be consulted: Rashi, Ibn Ezra, Radak, Metzudat David, Malbim, Meiri, Torah Temimah
   - Provide a brief reason explaining what aspect of each verse merits traditional commentary perspective
   - This comprehensive approach ensures the Synthesis Writer has classical grounding for every verse
   - Examples of good reasons:
     * "Opening invocation - how do commentators frame the psalm's purpose?"
     * "Key theological claim - traditional interpretation of divine attribute"
     * "Poetic parallelism - how do commentators explain the relationship between cola?"
     * "Rare vocabulary - classical exegesis illuminates unusual term"
     * "Figurative language - traditional understanding of metaphor"
"""

COMMENTARY_SELECTIVE = """**REQUEST COMMENTARY ONLY FOR VERSES** that are genuinely puzzling, interesting, complex, or merit traditional interpretation
   - All 7 available commentators will be consulted: Rashi, Ibn Ezra, Radak, Metzudat David, Malbim, Meiri, Torah Temimah
   - Be selective and judicious: only request for SOME verses that would most benefit from classical commentary
   - Focus on: interpretive puzzles, rare vocabulary, complex syntax, theologically loaded passages, unusual imagery
   - Provide a brief reason explaining what specific aspect merits traditional commentary
   - Examples of good reasons:
     * "Divine council language - how do traditional commentators handle 'sons of gods'?"
     * "Rare term 'mabbul' - classical exegesis illuminates unusual vocabulary"
     * "Ambiguous syntax - commentators resolve interpretive challenge"
     * "Theological claim - traditional understanding of divine attribute"
"""

# Stage 2: Research Request Generation Prompt
RESEARCH_REQUEST_PROMPT = """Based on your verse-by-verse discoveries, generate targeted research requests.

DISCOVERIES FROM STAGE 1:

{discoveries}

---

GENERATE RESEARCH REQUESTS:

1. **BDB LEXICON** - Hebrew words worth deep investigation
   - **BE HIGHLY JUDICIOUS**: Only request words that are genuinely puzzling, rare, or theologically significant
   - **AVOID common words** like יוֹם (day), אִישׁ (man), אֶרֶץ (earth), שָׁמַיִם (heavens), לֵב (heart), יָד (hand), עַיִן (eye), פֶּה (mouth), דֶּרֶךְ (way)
   - **Focus on**: Rare vocabulary, technical cultic terms, words with ambiguous meanings, theologically loaded terms, hapax legomena
   - **For psalms >15 verses**: Limit to 12-18 requests (ONLY the most essential words)
   - **For psalms 10-15 verses**: Limit to 15-22 requests
   - **For psalms <10 verses**: Up to 25-30 requests acceptable
   - Examples of GOOD requests: rare verbs, divine epithets, unusual compounds, technical cultic terms, words used in surprising ways
   - Examples of BAD requests: יוֹם, לֵב, יָד, עַיִן, פֶּה, דֶּרֶךְ, בָּשָׂר (unless used in truly puzzling context)

2. **CONCORDANCE SEARCHES** - Patterns to trace across Scripture
   - **For each lexical insight**: Copy the **EXACT PHRASE** from the micro analyst's discovery
     - Use the **exact phrase** as the primary query (without niqqudot/vowels) but otherwise the same,letter-for-letter
     - **Limit to phrase length: 3 words or fewer**
     - Add any **variants** as alternate queries (these are morphological forms only)
   - **SEARCH LEVEL**: "consonantal" (finds all forms of a root pattern)
     - Only use "exact" for homographs (same consonants, different vocalization)
     - Only use "voweled" when vocalization is critical
   - **IMPORTANT RESTRICTIONS**:
     - NEVER search single-word variants of multi-word phrases (e.g., if phrase is "דבר בלב", don't search just "דבר")
     - Variants are ONLY morphological forms (suffixes, plurals), NOT synonyms
     - **Limit to phrase length: 3 words or fewer**
   - **LIMIT**: 5-15 strategic searches total

3. **FIGURATIVE LANGUAGE** - Search the figurative language database for relevant metaphors

   **!!! CRITICAL - READ THIS FIRST !!!**

   The database vehicle field contains JSON arrays like:
   - ["chaff blown by wind", "agricultural byproduct", "natural element"]
   - ["A tree planted by streams", "Plant", "Natural element"]
   - ["dust and ashes", "inert matter", "earthly substances"]

   Your search terms match via SUBSTRING within these arrays. Therefore:
   - "tree" matches ["A tree planted by streams", ...]
   - "chaff" matches ["chaff blown by wind", ...]
   - "dust" matches ["dust and ashes", ...]

   **YOU MUST include SIMPLE SINGLE-WORD TERMS for every concept!**

   **IMPORTANT: TERM ORDER = PRIORITY**
   The order of terms in vehicle_synonyms determines search priority:
   - First terms are searched first and fill the results quota
   - Later terms may be TRUNCATED if space is limited (only top 20 results kept per query)

   **Order your terms from MOST IMPORTANT to LEAST IMPORTANT for your analysis.**
   Consider: Which terms best support your thesis? Which matches would be most
   valuable for the synthesis writer to see? Put those first.

   **CORRECT EXAMPLE - Tree/Plant Metaphor (Psalm 1:3)**:
   ```json
   {{
     "verse": 3,
     "reason": "Tree metaphor for righteous person planted by water",
     "vehicle": "tree",
     "vehicle_synonyms": ["tree", "plant", "planted", "leaf", "fruit", "root", "stream", "water", "flourish", "grow", "wither", "tree planted", "bears fruit", "by streams"],
     "broader_terms": ["vegetation", "agriculture", "growth", "nature"],
     "priority_ranking": {{
       "tree planted by streams": 1,
       "tree planted": 1,
       "planted": 2,
       "tree": 2,
       "plant": 3,
       "leaf": 3,
       "fruit": 3
     }},
        }}
   ```

   **CORRECT EXAMPLE - Chaff/Wind Metaphor (Psalm 1:4)**:
   ```json
   {{
     "verse": 4,
     "reason": "Chaff imagery for worthless wicked driven by wind",
     "vehicle": "chaff",
     "vehicle_synonyms": ["chaff", "dust", "straw", "wind", "scatter", "blow", "driven", "chaff blown", "dust in wind", "driven by wind", "blown away"],
     "broader_terms": ["agricultural waste", "worthlessness", "impermanence"],
     "priority_ranking": {{
       "chaff blown by wind": 1,
       "chaff blown": 1,
       "chaff": 2,
       "dust": 2,
       "wind": 3,
       "scatter": 3
     }},
        }}
   ```

   **WRONG EXAMPLE - DO NOT DO THIS**:
   ```json
   {{
     "vehicle": "righteous person as a thriving tree",
     "vehicle_synonyms": ["progressive moral flourishing", "stability through Torah devotion"]
   }}
   ```
   This will match NOTHING. The database has "tree", not "righteous person as a thriving tree".

   **CHECKLIST - Every figurative_checks entry MUST have:**
   [ ] vehicle: A simple 1-2 word term (e.g., "tree", "chaff", "dust", "face")
   [ ] vehicle_synonyms: 10-15+ terms ORDERED BY YOUR PRIORITY:
       - Put the most important terms for your analysis FIRST
       - Later terms may be truncated when results are filtered
       - Include both phrases and single words as appropriate for matching
   [ ] broader_terms: 3-5 category words (vegetation, agriculture, nature)

   **COMMON PSALM METAPHOR SEARCH TERMS**:
   - Tree/vegetation: tree, plant, planted, leaf, fruit, root, branch, vine, grass, wither, flourish, grow
   - Water: water, stream, river, fountain, rain, dew, sea, flood, deep, drink, thirst
   - Chaff/dust: chaff, dust, straw, ash, scatter, blow, wind, driven, tossed
   - Light/darkness: light, lamp, shine, bright, darkness, shadow, night, dawn, sun, moon
   - Path/way: path, way, road, walk, stand, sit, step, foot, stumble, fall
   - Refuge/protection: refuge, shelter, rock, fortress, stronghold, tower, shield, hide, cover
   - Body parts: face, hand, eye, mouth, heart, ear, arm, foot (use with action verbs)

   **QUANTITY GUIDELINES**:
   - Wisdom psalms: 4-6 figurative searches
   - Lament psalms: 6-10 figurative searches (more emotional metaphors)
   - ALL psalms: Minimum 3 figurative searches required

4. **COMMENTARY** - Traditional Jewish commentary for verses
   {commentary_instructions}

OUTPUT FORMAT: Return ONLY valid JSON:

**CRITICAL**: Every concordance_searches entry MUST include an "alternates" field (array of strings). Even if you can't think of good morphological/grammatical alternates for a particular query, include an empty array []. Do NOT omit this field.

{{
  "bdb_requests": [
    {{"word": "קוֹל", "reason": "Central to sevenfold anaphora - need semantic range and theological uses"}},
    {{"word": "בְּנֵי אֵלִים", "reason": "Divine council puzzle - etymology and comparative ANE usage"}}
  ],
  "concordance_searches": [
    {{"query": "ליהוה הישועה", "level": "consonantal", "purpose": "Track 'voice of LORD' formula usage patterns", "alternates": ["תשועה ליהוה", "ישועה מיהוה", "ישועת יהוה"]}},
    {{"query": "מרים ראש", "level": "consonantal", "purpose": "Divine council references across Hebrew Bible", "alternates": ["רום ראש", "ירים ראשי"]}},
    {{"query": "unique phrase", "level": "consonantal", "purpose": "Example with no obvious alternates", "alternates": []}}
  ],
  "figurative_checks": [
    {{"verse": 3, "reason": "Tree metaphor for righteous person planted by water", "vehicle": "tree", "vehicle_synonyms": ["tree", "plant", "planted", "leaf", "fruit", "root", "stream", "water", "flourish", "grow", "wither", "tree planted", "bears fruit", "by streams"], "broader_terms": ["vegetation", "agriculture", "growth", "nature"], "priority_ranking": {{"tree planted by streams": 1, "tree planted": 1, "planted": 2, "tree": 2, "plant": 3, "leaf": 3, "fruit": 3}}},
    {{"verse": 4, "reason": "Chaff imagery for worthless wicked driven by wind", "vehicle": "chaff", "vehicle_synonyms": ["chaff", "dust", "straw", "wind", "scatter", "blow", "driven", "chaff blown", "dust in wind", "driven by wind", "blown away"], "broader_terms": ["agricultural waste", "worthlessness", "impermanence"], "priority_ranking": {{"chaff blown by wind": 1, "chaff blown": 1, "chaff": 2, "dust": 2, "wind": 3, "scatter": 3}}},
    {{"verse": 6, "reason": "Path/way metaphor for life choices and destiny", "vehicle": "way", "vehicle_synonyms": ["way", "path", "road", "walk", "stand", "sit", "step", "foot", "perish", "know", "righteous way", "wicked way"], "broader_terms": ["journey", "direction", "choice", "destiny"], "priority_ranking": {{"righteous way": 1, "wicked way": 1, "way": 2, "path": 2, "road": 3, "walk": 3}}}
  ],
  "commentary_requests": [
    {{"verse": 1, "reason": "Opening beatitude - how do commentators interpret 'ashrei' and the threefold structure?"}},
    {{"verse": 2, "reason": "Torah meditation - traditional understanding of 'delight' and day/night study"}},
    {{"verse": 3, "reason": "Tree metaphor - classical interpretation of 'transplanted' vs. natural growth"}},
    {{"verse": 4, "reason": "Chaff imagery - how commentators contrast with tree metaphor"}},
    {{"verse": 5, "reason": "Judgment language - traditional eschatology and assembly of righteous"}},
    {{"verse": 6, "reason": "Two ways theology - how commentators frame knowing vs. perishing"}}
  ]
}}

Return ONLY the JSON object, no additional text.
"""


class MicroAnalystV2:
    """
    MicroAnalyst Agent v2 - Curiosity-driven discovery and research.

    Three stages:
    1. Quick verse-by-verse discovery pass
    2. Generate research requests based on discoveries
    3. Assemble research bundle
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        db_path: str = "data/tanakh.db",
        docs_dir: str = "docs",
        logger=None,
        commentary_mode: str = "all",
        cost_tracker: Optional[CostTracker] = None
    ):
        """Initialize MicroAnalyst v2 agent.

        Args:
            api_key: Anthropic API key
            db_path: Path to tanakh database
            docs_dir: Directory for RAG documents
            logger: Optional logger instance
            commentary_mode: "all" (request all 7 commentaries for all verses) or
                           "selective" (only request commentaries for specific verses)
            cost_tracker: CostTracker instance for tracking API costs
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required")

        if commentary_mode not in ["all", "selective"]:
            raise ValueError(f"Invalid commentary_mode: {commentary_mode}. Must be 'all' or 'selective'")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-5"  # Sonnet 4.5
        self.rag_manager = RAGManager(docs_dir)
        self.db = TanakhDatabase(Path(db_path))
        self.cost_tracker = cost_tracker or CostTracker()
        self.research_assembler = ResearchAssembler(cost_tracker=self.cost_tracker)
        self.logger = logger or get_logger("micro_analyst_v2")
        self.phonetic_analyst = PhoneticAnalyst()
        self.commentary_mode = commentary_mode

    def analyze_psalm(
        self,
        psalm_number: int,
        macro_analysis: MacroAnalysis
    ) -> Tuple[MicroAnalysis, ResearchBundle]:
        """
        Perform three-stage micro analysis.

        Args:
            psalm_number: Psalm number (1-150)
            macro_analysis: MacroAnalysis object from Pass 1

        Returns:
            Tuple of (MicroAnalysis with discoveries, ResearchBundle)
        """
        self.logger.info(f"=" * 80)
        self.logger.info(f"MICROANALYST V2: Psalm {psalm_number}")
        self.logger.info(f"=" * 80)

        # Log what we're receiving
        self._log_inputs(psalm_number, macro_analysis)

        # Stage 1: Quick discovery pass
        self.logger.info("\n[STAGE 1] Quick Verse-by-Verse Discovery Pass")
        
        # First, get phonetic transcriptions for the whole psalm
        phonetic_data = self._get_phonetic_transcriptions(psalm_number)
        
        discoveries = self._discovery_pass(psalm_number, macro_analysis, phonetic_data)
        self._log_discoveries(discoveries)

        # Stage 2: Generate research requests
        self.logger.info("\n[STAGE 2] Generating Research Requests from Discoveries")
        research_request = self._generate_research_requests(discoveries, psalm_number)
        self._log_research_requests(research_request)

        # Stage 3: Assemble research bundle
        self.logger.info("\n[STAGE 3] Assembling Research Bundle")
        research_bundle = self.research_assembler.assemble(research_request)
        self._log_research_bundle(research_bundle)

        # Create MicroAnalysis from discoveries, now including phonetic data
        micro_analysis = self._create_micro_analysis(psalm_number, discoveries, phonetic_data)

        self.logger.info(f"\n{'=' * 80}")
        self.logger.info(f"MICROANALYST V2 COMPLETE")
        self.logger.info(f"{'=' * 80}\n")

        return micro_analysis, research_bundle

    def _log_inputs(self, psalm_number: int, macro_analysis: MacroAnalysis):
        """Log comprehensive input information."""
        self.logger.info("\nINPUTS RECEIVED:")
        self.logger.info(f"  Psalm Number: {psalm_number}")
        self.logger.info(f"  Macro Thesis: {macro_analysis.thesis_statement[:100]}...")
        self.logger.info(f"  Structural Divisions: {len(macro_analysis.structural_outline)}")
        self.logger.info(f"  Poetic Devices: {len(macro_analysis.poetic_devices)}")
        self.logger.info(f"  Research Questions: {len(macro_analysis.research_questions)}")

        # Check psalm text availability
        psalm = self.db.get_psalm(psalm_number)
        if psalm:
            self.logger.info(f"  Psalm Verses: {len(psalm.verses)}")
        else:
            self.logger.warning(f"  Psalm text not available in database")

        # Check RAG/LXX availability
        rag_context = self.rag_manager.get_rag_context(psalm_number)
        self.logger.info(f"  RAG Genre: {rag_context.psalm_function['genre'] if rag_context.psalm_function else 'N/A'}")
        self.logger.info(f"  Ugaritic Parallels: {len(rag_context.ugaritic_parallels)}")
        self.logger.info(f"  LXX Available: {'Yes' if rag_context.lxx_text else 'No'}")
        if rag_context.lxx_text:
            lxx_verses = rag_context.lxx_text.count('\n') + 1
            self.logger.info(f"  LXX Verses: {lxx_verses}")

    def _discovery_pass(
        self,
        psalm_number: int,
        macro_analysis: MacroAnalysis,
        phonetic_data: dict
    ) -> dict:
        """Stage 1: Quick discovery pass through all verses."""
        # Fetch psalm with LXX
        psalm = self.db.get_psalm(psalm_number)
        if not psalm:
            raise ValueError(f"Psalm {psalm_number} not found in database")

        # Get RAG context
        rag_context = self.rag_manager.get_rag_context(psalm_number)

        # Format inputs
        psalm_text_with_lxx = self._format_psalm_with_lxx(psalm, rag_context)
        rag_formatted = self.rag_manager.format_for_prompt(rag_context, include_framework=False)
        verse_count = len(psalm.verses)

        # Build prompt - use replace to avoid brace conflicts
        prompt = DISCOVERY_PASS_PROMPT
        prompt = prompt.replace('{psalm_number}', str(psalm_number))
        prompt = prompt.replace('{macro_analysis}', macro_analysis.to_markdown())
        prompt = prompt.replace('{psalm_text_with_phonetics}', psalm_text_with_lxx)
        prompt = prompt.replace('{rag_context}', rag_formatted)
        prompt = prompt.replace('{verse_count}', str(verse_count))

        # Call Sonnet 4.5 with retry logic
        self.logger.info("  Calling Sonnet 4.5...")

        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    import time
                    wait_time = retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    self.logger.info(f"  Retry attempt {attempt + 1}/{max_retries} after {wait_time}s delay...")
                    time.sleep(wait_time)

                # Use streaming to avoid 10-minute timeout for large token requests
                stream = self.client.messages.stream(
                    model=self.model,
                    max_tokens=32768,  # Doubled to 32K to ensure no output constraint (was 16K, originally 8K)
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

                # Collect response chunks
                response_text = ""
                with stream as response_stream:
                    for chunk in response_stream:
                        if hasattr(chunk, 'type') and chunk.type == 'content_block_delta':
                            if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'type'):
                                if chunk.delta.type == 'text_delta':
                                    response_text += chunk.delta.text

                # Track usage and costs (discovery pass)
                final_message = response_stream.get_final_message()
                if hasattr(final_message, 'usage'):
                    usage = final_message.usage
                    thinking_tokens = getattr(usage, 'thinking_tokens', 0) if hasattr(usage, 'thinking_tokens') else 0
                    self.cost_tracker.add_usage(
                        model=self.model,
                        input_tokens=usage.input_tokens,
                        output_tokens=usage.output_tokens,
                        thinking_tokens=thinking_tokens
                    )

                self.logger.debug(f"Response text preview: {response_text[:500]}")

                # Try to extract JSON from markdown code blocks if present
                if response_text.startswith("```"):
                    # Extract from code block
                    lines = response_text.split('\n')
                    json_lines = []
                    in_json = False
                    for line in lines:
                        if line.startswith("```"):
                            if in_json:
                                break
                            in_json = True
                            continue
                        if in_json:
                            json_lines.append(line)
                    response_text = '\n'.join(json_lines)
                    self.logger.debug(f"Extracted from code block, length: {len(response_text)}")

                discoveries = json.loads(response_text)

                self.logger.info(f"  ✓ Discovery pass complete")
                return discoveries

            except json.JSONDecodeError as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"JSON parsing error (attempt {attempt + 1}/{max_retries}): {e}")
                    self.logger.warning("  Retrying with fresh request...")
                    continue  # Retry
                else:
                    # Out of retries
                    self.logger.error(f"Failed to parse discovery JSON after {max_retries} attempts: {e}")
                    raise ValueError(f"Invalid JSON from discovery pass: {e}")

            except Exception as e:
                # Check if it's a retryable error (API or network/streaming issues)
                import anthropic
                import httpx
                import httpcore
                is_retryable = isinstance(e, (
                    anthropic.InternalServerError,
                    anthropic.RateLimitError,
                    anthropic.APIConnectionError,
                    httpx.RemoteProtocolError,
                    httpcore.RemoteProtocolError
                ))

                if is_retryable and attempt < max_retries - 1:
                    self.logger.warning(f"Retryable error (attempt {attempt + 1}/{max_retries}): {type(e).__name__}: {e}")
                    self.logger.warning("  Retrying with fresh request...")
                    continue  # Retry
                else:
                    # Not retryable or out of retries
                    self.logger.error(f"Error in discovery pass: {e}")
                    raise

    def _generate_research_requests(
        self,
        discoveries: dict,
        psalm_number: int
    ) -> ResearchRequest:
        """Stage 2: Generate research requests from discoveries."""
        # Select commentary instructions based on mode
        commentary_instructions = (
            COMMENTARY_ALL_VERSES if self.commentary_mode == "all"
            else COMMENTARY_SELECTIVE
        )

        # Log the commentary mode being used
        self.logger.info(f"  Commentary mode: {self.commentary_mode}")

        # Build prompt - use string replacement instead of format to avoid conflicts with JSON braces
        prompt = RESEARCH_REQUEST_PROMPT.replace('{discoveries}', json.dumps(discoveries, ensure_ascii=False, indent=2))
        prompt = prompt.replace('{commentary_instructions}', commentary_instructions)

        # Call Sonnet 4.5 with retry logic
        self.logger.info("  Calling Sonnet 4.5 for research request generation...")

        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    import time
                    wait_time = retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    self.logger.info(f"  Retry attempt {attempt + 1}/{max_retries} after {wait_time}s delay...")
                    time.sleep(wait_time)

                # Use streaming to avoid potential timeout
                # Psalm 18 (51 verses) requires ~26K chars of JSON output, so we need high max_tokens
                stream = self.client.messages.stream(
                    model=self.model,
                    max_tokens=16384,  # Increased from 8K to handle long psalms like Psalm 18 (51 verses)
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

                # Collect response chunks
                response_text = ""
                with stream as response_stream:
                    for chunk in response_stream:
                        if hasattr(chunk, 'type') and chunk.type == 'content_block_delta':
                            if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'type'):
                                if chunk.delta.type == 'text_delta':
                                    response_text += chunk.delta.text

                # Track usage and costs (research generation pass)
                final_message = response_stream.get_final_message()
                if hasattr(final_message, 'usage'):
                    usage = final_message.usage
                    thinking_tokens = getattr(usage, 'thinking_tokens', 0) if hasattr(usage, 'thinking_tokens') else 0
                    self.cost_tracker.add_usage(
                        model=self.model,
                        input_tokens=usage.input_tokens,
                        output_tokens=usage.output_tokens,
                        thinking_tokens=thinking_tokens
                    )

                # Check for truncation (stop_reason == 'max_tokens' means output was cut off)
                stop_reason = getattr(final_message, 'stop_reason', None)
                if stop_reason == 'max_tokens':
                    self.logger.warning(f"  ⚠ Response was truncated at max_tokens limit ({len(response_text)} chars)")
                    self.logger.warning(f"  This may cause JSON parsing errors for long psalms")

                self.logger.debug(f"Response text preview: {response_text[:500]}")

                # Try to extract JSON from markdown code blocks if present
                if response_text.startswith("```"):
                    # Extract from code block
                    lines = response_text.split('\n')
                    json_lines = []
                    in_json = False
                    for line in lines:
                        if line.startswith("```"):
                            if in_json:
                                break
                            in_json = True
                            continue
                        if in_json:
                            json_lines.append(line)
                    response_text = '\n'.join(json_lines)
                    self.logger.debug(f"Extracted from code block, length: {len(response_text)}")

                data = json.loads(response_text)

                # Convert to ResearchRequest via ScholarResearchRequest
                scholar_request = ScholarResearchRequest.from_dict(data)
                request_dict = scholar_request.to_research_request(psalm_number, logger=self.logger)

                # Add verse count for figurative search result filtering
                psalm = self.db.get_psalm(psalm_number)
                if psalm:
                    request_dict['verse_count'] = len(psalm.verses)
                    self.logger.info(f"  Psalm {psalm_number} has {len(psalm.verses)} verses (figurative limit: {'20' if len(psalm.verses) < 20 else '10'} per query)")

                research_request = ResearchRequest.from_dict(request_dict)

                # DEBUG: Log what LLM generated before fixing
                if self.logger:
                    self.logger.info("=== Phrase Extraction Debug (LLM Output) ===")
                    for i, req in enumerate(research_request.concordance_requests):
                        self.logger.info(f"  Request {i+1}: query='{req.query}' level='{req.level}'")
                        if hasattr(req, 'alternates') and req.alternates:
                            self.logger.info(f"    Alternates: {req.alternates}")

                # Extract exact phrases and variants from discoveries and override LLM base forms
                exact_phrases, variants_mapping = self._extract_exact_phrases_from_discoveries(discoveries)

                if exact_phrases:
                    self.logger.info(f"  Extracted {len(exact_phrases)} exact phrases from discoveries")
                    # Override LLM base forms with exact phrases
                    research_request = self._override_llm_base_forms(research_request, exact_phrases, variants_mapping, psalm_number)
                else:
                    self.logger.warning("  No exact phrases extracted from discoveries, attempting verse text extraction")
                    # Try to extract directly from verse text
                    research_request = self._override_llm_base_forms(research_request, {}, {}, psalm_number)

                self.logger.info(f"  ✓ Research requests generated")
                return research_request

            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse research request JSON: {e}")
                raise ValueError(f"Invalid JSON from research generation: {e}")

            except Exception as e:
                # Check if it's a retryable error (API or network/streaming issues)
                import anthropic
                import httpx
                import httpcore
                is_retryable = isinstance(e, (
                    anthropic.InternalServerError,
                    anthropic.RateLimitError,
                    anthropic.APIConnectionError,
                    httpx.RemoteProtocolError,
                    httpcore.RemoteProtocolError
                ))

                if is_retryable and attempt < max_retries - 1:
                    self.logger.warning(f"Retryable error (attempt {attempt + 1}/{max_retries}): {type(e).__name__}: {e}")
                    self.logger.warning("  Retrying with fresh request...")
                    continue  # Retry
                else:
                    # Not retryable or out of retries
                    self.logger.error(f"Error generating research requests: {e}")
                    raise

    def _create_micro_analysis(
        self,
        psalm_number: int,
        discoveries: dict,
        phonetic_data: dict
    ) -> MicroAnalysis:
        """Create MicroAnalysis object from discoveries."""
        # Convert discoveries to VerseCommentary objects
        verse_commentaries = []
        for disc in discoveries.get('verse_discoveries', []):
            # Handle both legacy curious_words and new lexical_insights formats
            lexical_insights = disc.get('lexical_insights', [])

            # If legacy format with curious_words, convert to new structured format
            if not lexical_insights and 'curious_words' in disc:
                # Convert each curious word to the new structured format
                lexical_insights = [
                    {
                        "phrase": word,
                        "variants": [],  # No variants in legacy format
                        "notes": f"Word identified for investigation (legacy format)"
                    }
                    for word in disc.get('curious_words', [])
                ]

            vc = VerseCommentary(
                verse_number=disc['verse_number'],
                commentary=disc.get('observations', ''),
                lexical_insights=lexical_insights,
                figurative_analysis=disc.get('figurative_elements', []),
                thesis_connection=disc.get('macro_relation', ''),
                phonetic_transcription=phonetic_data.get(disc['verse_number'], '[Transcription not found]')
            )
            verse_commentaries.append(vc)

        # Create MicroAnalysis
        micro = MicroAnalysis(
            psalm_number=psalm_number,
            verse_commentaries=verse_commentaries,
            thematic_threads=discoveries.get('overall_patterns', []),
            interesting_questions=discoveries.get('interesting_questions', []),
            synthesis_notes="\n".join(discoveries.get('research_priorities', []))
        )

        return micro

    def _log_discoveries(self, discoveries: dict):
        """Log discovery pass results."""
        self.logger.info(f"\n  DISCOVERIES:")
        verse_discoveries = discoveries.get('verse_discoveries', [])
        self.logger.info(f"    Verses analyzed: {len(verse_discoveries)}")

        # Sample first verse
        if verse_discoveries:
            v1 = verse_discoveries[0]
            self.logger.info(f"\n    Sample (v{v1['verse_number']}):")
            self.logger.info(f"      Observations: {v1.get('observations', '')[:80]}...")
            self.logger.info(f"      Curious words: {len(v1.get('curious_words', []))}")
            self.logger.info(f"      Poetic features: {len(v1.get('poetic_features', []))}")

        overall_patterns = discoveries.get('overall_patterns', [])
        self.logger.info(f"\n    Overall patterns identified: {len(overall_patterns)}")
        for pattern in overall_patterns[:2]:
            self.logger.info(f"      - {pattern[:80]}...")

    def _log_research_requests(self, request: ResearchRequest):
        """Log research request summary."""
        self.logger.info(f"\n  RESEARCH REQUESTS:")
        self.logger.info(f"    BDB lexicon: {len(request.lexicon_requests)}")
        self.logger.info(f"    Concordance: {len(request.concordance_requests)}")
        self.logger.info(f"    Figurative: {len(request.figurative_requests)}")
        self.logger.info(f"    Commentary: {len(request.commentary_requests or [])}")

        # Log detailed figurative requests
        if request.figurative_requests:
            self.logger.info(f"\n  FIGURATIVE LANGUAGE REQUESTS (detailed):")
            for i, fig_req in enumerate(request.figurative_requests, 1):
                self.logger.info(f"    [{i}] Verse: {fig_req.chapter}:{fig_req.verse_start if hasattr(fig_req, 'verse_start') else 'N/A'}")
                if hasattr(fig_req, 'vehicle_contains') and fig_req.vehicle_contains:
                    self.logger.info(f"        vehicle_contains: {fig_req.vehicle_contains}")
                if hasattr(fig_req, 'vehicle_search_terms') and fig_req.vehicle_search_terms:
                    self.logger.info(f"        vehicle_search_terms: {fig_req.vehicle_search_terms}")
                if hasattr(fig_req, 'notes') and fig_req.notes:
                    self.logger.info(f"        notes: {fig_req.notes[:100]}...")

    def _log_research_bundle(self, bundle: ResearchBundle):
        """Log research bundle assembly results."""
        summary = bundle.to_dict()['summary']
        self.logger.info(f"\n  RESEARCH BUNDLE ASSEMBLED:")
        self.logger.info(f"    Lexicon entries: {summary['lexicon_entries']}")
        self.logger.info(f"    Concordance results: {summary['concordance_results']}")
        self.logger.info(f"    Figurative instances: {summary['figurative_instances']}")
        self.logger.info(f"    Commentary entries: {summary['commentary_entries']}")

    def _extract_json_from_response(self, response) -> str:
        """Extract JSON from Anthropic API response."""
        # Log all blocks for debugging
        self.logger.debug(f"Response has {len(response.content)} blocks")
        for i, block in enumerate(response.content):
            self.logger.debug(f"Block {i}: type={block.type}")
            if block.type == "text":
                text = block.text.strip()
                self.logger.debug(f"Block {i} text length: {len(text)}")
                if text:  # Only return non-empty text
                    return text
        raise ValueError("No text content found in response")

    def _format_psalm_with_lxx(self, psalm, rag_context) -> str:
        """Format psalm text with LXX translation."""
        lines = [f"Psalm {psalm.chapter}\n"]

        # Parse LXX verses
        lxx_verses = {}
        if rag_context and rag_context.lxx_text:
            for line in rag_context.lxx_text.split('\n'):
                if line.startswith('v'):
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        verse_num = int(parts[0][1:])
                        lxx_verses[verse_num] = parts[1].strip()

        for verse in psalm.verses:
            v_num = verse.verse
            lines.append(f"v{v_num}")
            lines.append(f"  Hebrew: {verse.hebrew}")
            lines.append(f"  English: {verse.english}")
            if v_num in lxx_verses:
                lines.append(f"  LXX (Greek): {lxx_verses[v_num]}")
            lines.append("")

        return "\n".join(lines)

    def _get_phonetic_transcriptions(self, psalm_number: int) -> Dict[int, str]:
        """Get phonetic transcription for each verse of the psalm with stress marking."""
        self.logger.info("  Generating phonetic transcriptions with stress marking...")
        psalm = self.db.get_psalm(psalm_number)
        if not psalm:
            self.logger.error(f"Could not retrieve psalm {psalm_number} for phonetic transcription.")
            return {}

        phonetic_data = {}
        for verse in psalm.verses:
            try:
                # Call the phonetic analyst to get the detailed transcription
                analysis = self.phonetic_analyst.transcribe_verse(verse.hebrew)

                # Join the syllabified transcriptions WITH STRESS MARKING into a single string
                # Use 'syllable_transcription_stressed' which shows stressed syllables in **BOLD CAPS**
                # Example: "tə-**HIL**-lāh lə-dhā-**WIDH**"
                transcribed_words = [word['syllable_transcription_stressed'] for word in analysis['words']]
                verse_transcription = " ".join(transcribed_words)

                phonetic_data[verse.verse] = verse_transcription
            except Exception as e:
                self.logger.error(f"Error transcribing verse {verse.verse}: {e}")
                phonetic_data[verse.verse] = "[Transcription Error]"

        self.logger.info("  ✓ Phonetic transcriptions with stress marking generated.")
        return phonetic_data

    def _extract_exact_phrases_from_discoveries(self, discoveries: dict) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
        """
        Extract exact phrases and variants from discoveries to override LLM base forms.

        Preserves morphological prefixes/suffixes while removing vowel points for searching.

        Args:
            discoveries: Dictionary containing verse_discoveries with lexical_insights

        Returns:
            Tuple of:
            - Dictionary mapping normalized keys to exact phrases without vowel points
            - Dictionary mapping normalized keys to lists of variant phrases
        """
        import re
        phrase_mapping = {}
        variants_mapping = {}

        for verse_disc in discoveries.get('verse_discoveries', []):
            # Handle Phase 2 format with phrase/variants structure
            for insight in verse_disc.get('lexical_insights', []):
                # Handle both string format (legacy) and dict format (Phase 2)
                if isinstance(insight, str):
                    phrase = insight
                    variants = []
                else:
                    phrase = insight.get('phrase', '')
                    variants = insight.get('variants', [])

                if not phrase:
                    continue

                # Replace maqqef (־) with space before removing vowel points
                # Maqqef (U+05BE) is in vowel point range and would be removed, concatenating words
                phrase_with_spaces = phrase.replace('\u05BE', ' ')

                # Remove vowel points but keep consonants
                clean_phrase = re.sub(r'[\u0591-\u05C7]', '', phrase_with_spaces)

                # Create normalized key for matching
                key = re.sub(r'[^\u05D0-\u05EA]', '', clean_phrase)

                if key and clean_phrase:
                    phrase_mapping[key] = clean_phrase

                    # Clean variants (remove vowel points)
                    if variants:
                        clean_variants = []
                        for variant in variants:
                            # Replace maqqef with space first
                            variant_with_spaces = variant.replace('\u05BE', ' ')
                            clean_variant = re.sub(r'[\u0591-\u05C7]', '', variant_with_spaces)
                            if clean_variant and clean_variant != clean_phrase:
                                clean_variants.append(clean_variant)
                        if clean_variants:
                            variants_mapping[key] = clean_variants

            # Handle legacy curious_words format
            if 'curious_words' in verse_disc and not verse_disc.get('lexical_insights'):
                for word in verse_disc.get('curious_words', []):
                    if word:
                        clean_word = re.sub(r'[\u0591-\u05C7]', '', word)
                        key = re.sub(r'[^\u05D0-\u05EA]', '', clean_word)
                        if key and clean_word:
                            phrase_mapping[key] = clean_word

        return phrase_mapping, variants_mapping

    def _query_in_verse(self, query: str, verse_hebrew: str) -> bool:
        """
        Check if a query phrase appears in a verse (allowing for some flexibility).

        Args:
            query: The search query (consonantal form)
            verse_hebrew: The full Hebrew verse text

        Returns:
            True if the query appears to be in the verse
        """
        import re
        from ..concordance.hebrew_text_processor import split_words

        # Replace maqqef with space before removing vowel points
        query_with_spaces = query.replace('\u05BE', ' ')
        verse_with_spaces = verse_hebrew.replace('\u05BE', ' ')

        # Remove vowel points for comparison
        query_clean = re.sub(r'[\u0591-\u05C7]', '', query_with_spaces)
        verse_clean = re.sub(r'[\u0591-\u05C7]', '', verse_with_spaces)

        # Split into words
        query_words = split_words(query_clean)
        verse_words = split_words(verse_clean)

        # If query has fewer words, check if it's a subsequence
        if len(query_words) <= len(verse_words):
            for i in range(len(verse_words) - len(query_words) + 1):
                # Check if query words match verse words starting at position i
                match = True
                for j, qword in enumerate(query_words):
                    if qword not in verse_words[i + j]:
                        # Check for substring match (allows for prefixes/suffixes)
                        if qword not in verse_words[i + j] and verse_words[i + j] not in qword:
                            match = False
                            break
                if match:
                    return True

        return False

    def _extract_exact_form_from_verse(self, query: str, verse_hebrew: str) -> str:
        """
        Extract the exact form of a phrase from a verse.

        Args:
            query: The search query (consonantal form)
            verse_hebrew: The full Hebrew verse text

        Returns:
            The exact Hebrew phrase from the verse
        """
        import re
        from ..concordance.hebrew_text_processor import split_words

        # Replace maqqef with space before removing vowel points
        query_with_spaces = query.replace('\u05BE', ' ')
        verse_with_spaces = verse_hebrew.replace('\u05BE', ' ')

        # Remove vowel points for matching
        query_clean = re.sub(r'[\u0591-\u05C7]', '', query_with_spaces)
        verse_clean = re.sub(r'[\u0591-\u05C7]', '', verse_with_spaces)

        # Split into words
        query_words = split_words(query_clean)
        verse_words = split_words(verse_with_spaces)  # With maqqefs replaced
        verse_words_clean = split_words(verse_clean)

        # Find the best matching sequence
        best_match = None
        best_score = 0

        for i in range(len(verse_words_clean) - len(query_words) + 1):
            score = 0
            for j, qword in enumerate(query_words):
                vword = verse_words_clean[i + j]
                if qword == vword:
                    score += 3
                elif qword in vword:
                    score += 2
                elif vword in qword:
                    score += 1

            if score > best_score:
                best_score = score
                # Extract the original Hebrew (with pointing)
                best_match = ' '.join(verse_words[i:i+len(query_words)])

        # Require at least 2 points per word to consider it a match
        if best_score >= len(query_words) * 2:
            return best_match

        return None

    def _extract_all_phrase_forms_from_verse(self, query: str, verse_hebrew: str) -> List[str]:
        """
        Extract ALL possible forms of a phrase from verse, including:
        - Words in different order than query
        - Words with intervening text
        - Words without intervening text (collapsed form)

        This ensures we always find the source verse even if LLM created
        a conceptual phrase that doesn't match actual word order.

        Example:
            Query: "נשא חרפה" (bear reproach)
            Verse: "וְחֶרְפָּה לֹא־נָשָׂא" (and reproach NOT bear)
            Returns: ["חרפה לא נשא", "חרפה נשא"]

        Args:
            query: The search query (consonantal form)
            verse_hebrew: The full Hebrew verse text

        Returns:
            List of all possible phrase forms found in the verse
        """
        import re
        from itertools import product
        from ..concordance.hebrew_text_processor import split_words

        # Replace maqqef with space before removing vowel points
        query_with_spaces = query.replace('\u05BE', ' ')
        verse_with_spaces = verse_hebrew.replace('\u05BE', ' ')

        # Remove vowel points for matching
        query_clean = re.sub(r'[\u0591-\u05C7]', '', query_with_spaces)

        query_words = split_words(query_clean)
        verse_words = split_words(verse_with_spaces)  # With maqqefs replaced by spaces

        # Clean each word individually to maintain array alignment
        verse_words_clean = [re.sub(r'[\u0591-\u05C7]', '', word) for word in verse_words]

        results = []

        # Find all positions where each query word appears
        word_positions = {}
        for qword in query_words:
            word_positions[qword] = []
            for i, vword in enumerate(verse_words_clean):
                # Skip empty words (like paseq marks)
                if not vword or not qword:
                    continue
                # Substring match (allows prefixes/suffixes)
                if qword in vword or vword in qword:
                    word_positions[qword].append(i)

        # Check if all query words are present
        if not all(positions for positions in word_positions.values()):
            return []  # Some words not found

        # Generate all valid combinations
        for combination in product(*word_positions.values()):
            # Sort positions to get actual verse order
            sorted_positions = sorted(combination)

            # Skip if positions are duplicates (same word position for multiple query words)
            if len(set(sorted_positions)) != len(sorted_positions):
                continue

            # Extract the span from first to last position
            start = sorted_positions[0]
            end = sorted_positions[-1]

            # Form 1: With intervening words (actual verse order)
            full_span = ' '.join(verse_words[start:end+1])
            # Remove vowel points for searching
            full_span_clean = re.sub(r'[\u0591-\u05C7]', '', full_span)
            if full_span_clean not in results:
                results.append(full_span_clean)

            # Form 2: Without intervening words (collapsed)
            collapsed = ' '.join(verse_words[i] for i in sorted_positions)
            collapsed_clean = re.sub(r'[\u0591-\u05C7]', '', collapsed)
            if collapsed_clean not in results and collapsed_clean != full_span_clean:
                results.append(collapsed_clean)

        return results

    def _override_llm_base_forms(self, research_request: ResearchRequest, exact_phrases: Dict[str, str], variants_mapping: Dict[str, List[str]], psalm_number: int):
        """
        Override LLM base forms with exact phrases from discoveries.

        Args:
            research_request: The ResearchRequest object generated by LLM
            exact_phrases: Dictionary of exact phrases to use
            variants_mapping: Dictionary mapping normalized keys to variant phrases
            psalm_number: Psalm number for fallback verse text extraction

        Returns:
            Modified ResearchRequest with exact phrases preserved
        """
        import re
        fixed_count = 0
        variants_added = 0

        # Fix concordance requests
        for req in research_request.concordance_requests:
            original_query = req.query
            # Normalize for matching
            normalized = re.sub(r'[^\u05D0-\u05EA]', '', original_query)
            normalized = re.sub(r'[\u0591-\u05C7]', '', normalized)

            # Check if normalized query is contained in any stored phrase
            matched_phrase = None
            matched_key = None
            for stored_key, stored_phrase in exact_phrases.items():
                # Check if query is substring of stored phrase (allowing suffixes/prefixes)
                if normalized in stored_key:
                    matched_phrase = stored_phrase
                    matched_key = stored_key
                    break

            if matched_phrase:
                # Store the original LLM query as an alternate if it's different
                original_as_alternate = False

                # Set the exact phrase as the primary query
                if matched_phrase != original_query:
                    # Create alternates list if it doesn't exist
                    if not hasattr(req, 'alternates') or not req.alternates:
                        req.alternates = []
                    # Add the original query as an alternate if it's different
                    if original_query not in req.alternates:
                        req.alternates.append(original_query)
                        original_as_alternate = True

                req.query = matched_phrase
                req.notes += f" [FIXED: Using exact phrase from verse]"
                fixed_count += 1
                self.logger.info(f"    ✓ Fixed '{original_query}' → '{req.query}' (matched substring)")
                if original_as_alternate:
                    self.logger.info(f"    ✓ Added original query as alternate: '{original_query}'")

                # Add variants from lexical insights if available
                if matched_key in variants_mapping:
                    variants = variants_mapping[matched_key]
                    # Create alternates list if it doesn't exist
                    if not hasattr(req, 'alternates') or not req.alternates:
                        req.alternates = []
                    # Add new variants (avoid duplicates)
                    for variant in variants:
                        if variant not in req.alternates and variant != req.query:
                            req.alternates.append(variant)
                            variants_added += 1
                    self.logger.info(f"    ✓ Added {len(variants)} variants from lexical insights")

        # NEW: Fallback extraction from verse text if no matches found
        if fixed_count == 0:
            self.logger.warning("  No exact phrase matches found in discoveries, attempting verse text extraction")
            verse_fixed_count = 0

            # Get the psalm text from database for fallback
            psalm = self.db.get_psalm(psalm_number)
            if psalm:
                for req in research_request.concordance_requests:
                    original_query = req.query
                    if "[FIXED: Using exact phrase]" in req.notes:
                        continue  # Skip if already fixed

                    # Try to find phrase in psalm verses
                    for verse in psalm.verses:
                        hebrew_text = verse.hebrew
                        if self._query_in_verse(original_query, hebrew_text):
                            # Extract exact form from verse
                            exact_form = self._extract_exact_form_from_verse(original_query, hebrew_text)
                            if exact_form and exact_form != req.query:
                                req.query = exact_form
                                req.notes += f" [FIXED: Extracted from verse {verse.verse}]"
                                verse_fixed_count += 1
                                self.logger.info(f"    ✓ Fixed '{original_query}' → '{req.query}' (from verse {verse.verse})")
                                break

                if verse_fixed_count > 0:
                    self.logger.info(f"  Fixed {verse_fixed_count} additional queries using verse text extraction")

        # CRITICAL FIX: Always extract all phrase forms from verse to guarantee source verse is found
        # This handles cases where LLM created conceptual phrases with different word order
        self.logger.info("  Extracting all phrase forms from source verses to guarantee matches...")
        from ..concordance.hebrew_text_processor import split_words

        psalm = self.db.get_psalm(psalm_number)
        if psalm:
            phrase_forms_added = 0
            for req in research_request.concordance_requests:
                # Only process phrases (2+ words)
                query_words = split_words(req.query)
                if len(query_words) < 2:
                    continue

                # Find the verse this phrase came from
                source_verse = None
                for verse in psalm.verses:
                    if self._query_in_verse(req.query, verse.hebrew):
                        source_verse = verse
                        break

                # If not found with same order, try finding verse with all words in any order
                if not source_verse:
                    for verse in psalm.verses:
                        all_forms = self._extract_all_phrase_forms_from_verse(
                            req.query, verse.hebrew
                        )
                        if all_forms:
                            source_verse = verse
                            break

                # Extract all possible forms from the source verse
                if source_verse:
                    all_forms = self._extract_all_phrase_forms_from_verse(
                        req.query, source_verse.hebrew
                    )

                    if all_forms:
                        # Create alternate_queries list if needed
                        if not hasattr(req, 'alternate_queries') or req.alternate_queries is None:
                            req.alternate_queries = []

                        # Add all forms as alternates (avoid duplicates)
                        added_count = 0
                        for form in all_forms:
                            if form not in req.alternate_queries and form != req.query:
                                req.alternate_queries.append(form)
                                added_count += 1
                                self.logger.info(f"    ✓ Added verse form as alternate: '{form}'")

                        if added_count > 0:
                            req.notes += f" [GUARANTEED: Added {added_count} forms from verse {source_verse.verse}]"
                            phrase_forms_added += added_count

            if phrase_forms_added > 0:
                self.logger.info(f"  Added {phrase_forms_added} verse forms to guarantee source verse matches")

        self.logger.info(f"  Fixed {fixed_count} queries to preserve exact morphology")
        if variants_added > 0:
            self.logger.info(f"  Added {variants_added} variants from lexical insights")
        return research_request


def main():
    """CLI for MicroAnalyst v2."""
    import argparse

    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description='MicroAnalyst v2: Discovery-driven analysis')
    parser.add_argument('psalm_number', type=int, help='Psalm number (1-150)')
    parser.add_argument('macro_analysis_file', type=str, help='Path to MacroAnalysis JSON')
    parser.add_argument('--output-dir', type=str, default='output/phase3_test',
                       help='Output directory')
    parser.add_argument('--db-path', type=str, default='data/tanakh.db',
                       help='Database path')

    args = parser.parse_args()

    try:
        # Load macro analysis
        from src.schemas.analysis_schemas import load_macro_analysis, save_analysis
        macro_analysis = load_macro_analysis(args.macro_analysis_file)

        print(f"\nMICROANALYST V2 - Psalm {args.psalm_number}")
        print("=" * 80)

        # Initialize
        analyst = MicroAnalystV2(db_path=args.db_path)

        # Analyze
        micro_analysis, research_bundle = analyst.analyze_psalm(
            args.psalm_number,
            macro_analysis
        )

        # Save outputs
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        micro_json = output_dir / f"psalm_{args.psalm_number:03d}_micro_v2.json"
        micro_md = output_dir / f"psalm_{args.psalm_number:03d}_micro_v2.md"
        bundle_md = output_dir / f"psalm_{args.psalm_number:03d}_research_v2.md"

        save_analysis(micro_analysis, str(micro_json), format="json")
        save_analysis(micro_analysis, str(micro_md), format="markdown")

        with open(bundle_md, 'w', encoding='utf-8') as f:
            f.write(research_bundle.to_markdown())

        print(f"\n{'=' * 80}")
        print("OUTPUT FILES:")
        print(f"  {micro_json}")
        print(f"  {micro_md}")
        print(f"  {bundle_md}")
        print(f"{'=' * 80}\n")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
