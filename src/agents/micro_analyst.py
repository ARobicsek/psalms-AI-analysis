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
from typing import Tuple, Optional, Dict
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
else:
    from ..schemas.analysis_schemas import MacroAnalysis, MicroAnalysis, VerseCommentary
    from .rag_manager import RAGManager
    from .research_assembler import ResearchAssembler, ResearchRequest, ResearchBundle
    from .scholar_researcher import ScholarResearchRequest
    from ..data_sources.tanakh_database import TanakhDatabase
    from ..utils.logger import get_logger
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

1. **Curious Word Choices**: Rare words? Unexpected vocabulary? Interesting verbs/nouns?
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

{{
  "verse_discoveries": [
    {{
      "verse_number": 1,
      "observations": "Quick summary of what's interesting/curious in this verse (2-4 sentences). Focus on discoveries, not analysis.",
      "curious_words": ["קוֹל", "בְּנֵי אֵלִים"],  // Hebrew words worth investigating
      "poetic_features": ["anaphora setup", "divine council imagery"],
      "figurative_elements": ["sons of gods - metaphor or literal?"],
      "puzzles": ["Why 'sons of gods' (plural) in monotheistic psalm?"],
      "lxx_insights": "LXX uses 'υἱοὶ θεοῦ' - shows early plural divine beings interpretation",
      "macro_relation": "Supports divine council framework from thesis" // OR "Interesting independent of thesis: ..."
    }},
    {{
      "verse_number": 2,
      "observations": "...",
      ...
    }},
    ... (all {verse_count} verses)
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
}}

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
   - Repeated phrases from discoveries
   - Thematic roots identified
   - VALID LEVELS: "consonantal" (all root forms), "voweled" (distinguish homographs), "exact" (specific vocalization)
   - **DEFAULT TO "consonantal"** - Only use "exact" if specifically concerned about homographs (same consonants, different vocalizations)
   - "consonantal" finds all forms of a root pattern regardless of vocalization
   - 5-10 strategic searches

3. **FIGURATIVE LANGUAGE** - Verses with notable and interesting figurative speech
   - **BE SELECTIVE**: Only request searches for VIVID, UNUSUAL, or THEOLOGICALLY RICH figurative language, or language CENTRAL to the psalm
   - **AVOID very common body part imagery** unless used in surprising ways: hand, eye/gaze, mouth, heart, face, ear
   - **AVOID very common theological terms** unless central to the psalm: mercy, fear, bless, praise
   - **FOCUS ON**: Unusual metaphors, nature imagery, architectural imagery, rare verbs of action, surprising personification
   - **For psalms >15 verses**: Limit to 8-12 figurative searches (most striking imagery only)
   - **For psalms 10-15 verses**: Limit to 10-15 figurative searches
   - **For psalms <10 verses**: Up to 12-18 figurative searches acceptable
   - **SEARCH SCOPE**: Default to searching both Psalms AND Pentateuch (not just Psalms)
   - **HIERARCHICAL SEARCH STRATEGY**: For each figurative element:
     * Specify the specific vehicle (main image, e.g., "stronghold", "shepherd", "storm")
     * Include direct synonyms (e.g., for "stronghold": "fortress", "citadel", "refuge")
     * Include broader category terms (e.g., for "stronghold": "military", "protection", "defense")
     * **INCLUDE MORPHOLOGICAL VARIATIONS** where relevant:
       - Singular AND plural forms (e.g., "banner" AND "banners", "wall" AND "walls")
       - Base verbs AND gerunds (e.g., "stand" AND "standing", "rise" AND "rising")
       - Apply this to synonyms too (e.g., if searching "arise", include "arises", "arising")
     * The synthesis and master editor agents will determine which results are most relevant
   - Examples of GOOD figurative requests: "pour forth" (vivid action), "fathom" (rare concept), "nostril" (specific idiom)
   - Examples of BAD figurative requests: "hand", "gaze", "mouth", "way", "mercy", "bless" (too common, will return 100s of results)

4. **COMMENTARY** - Traditional Jewish commentary for verses
   {commentary_instructions}

OUTPUT FORMAT: Return ONLY valid JSON:

{{
  "bdb_requests": [
    {{"word": "קוֹל", "reason": "Central to sevenfold anaphora - need semantic range and theological uses"}},
    {{"word": "בְּנֵי אֵלִים", "reason": "Divine council puzzle - etymology and comparative ANE usage"}}
  ],
  "concordance_searches": [
    {{"query": "קול יהוה", "level": "consonantal", "scope": "Psalms", "purpose": "Track 'voice of LORD' formula usage patterns"}},
    {{"query": "בני אלים", "level": "consonantal", "scope": "Tanakh", "purpose": "Divine council references across Hebrew Bible"}}
  ],
  "figurative_checks": [
    {{"verse": 3, "reason": "Waters as primordial chaos imagery - vivid and theologically rich", "vehicle": "waters", "vehicle_synonyms": ["water", "sea", "seas", "deep", "depths", "flood", "floods", "ocean", "oceans"], "broader_terms": ["chaos", "creation", "cosmology", "primordial"], "scope": "Psalms+Pentateuch"}},
    {{"verse": 5, "reason": "Voice 'breaking' cedars - unusual storm personification", "vehicle": "breaking", "vehicle_synonyms": ["break", "breaks", "shatter", "shatters", "shattering", "split", "splits", "fracture", "fractures"], "broader_terms": ["power", "force", "destruction"], "scope": "Psalms+Pentateuch"}},
    {{"verse": 7, "reason": "Stronghold imagery - architectural metaphor for divine protection", "vehicle": "stronghold", "vehicle_synonyms": ["strongholds", "fortress", "fortresses", "citadel", "citadels", "refuge", "refuges"], "broader_terms": ["military", "protection", "defense"], "scope": "Psalms+Pentateuch"}}
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
        commentary_mode: str = "all"
    ):
        """Initialize MicroAnalyst v2 agent.

        Args:
            api_key: Anthropic API key
            db_path: Path to tanakh database
            docs_dir: Directory for RAG documents
            logger: Optional logger instance
            commentary_mode: "all" (request all 7 commentaries for all verses) or
                           "selective" (only request commentaries for specific verses)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required")

        if commentary_mode not in ["all", "selective"]:
            raise ValueError(f"Invalid commentary_mode: {commentary_mode}. Must be 'all' or 'selective'")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"  # Sonnet 4.5
        self.rag_manager = RAGManager(docs_dir)
        self.db = TanakhDatabase(Path(db_path))
        self.research_assembler = ResearchAssembler()
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

        # Build prompt
        prompt = DISCOVERY_PASS_PROMPT.format(
            psalm_number=psalm_number,
            macro_analysis=macro_analysis.to_markdown(),
            psalm_text_with_phonetics=psalm_text_with_lxx,
            rag_context=rag_formatted,
            verse_count=verse_count
        )

        # Call Sonnet 4.5
        self.logger.info("  Calling Sonnet 4.5...")
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract and parse JSON
            response_text = self._extract_json_from_response(response)
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
            self.logger.error(f"Failed to parse discovery JSON: {e}")
            raise ValueError(f"Invalid JSON from discovery pass: {e}")
        except Exception as e:
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

        # Build prompt
        prompt = RESEARCH_REQUEST_PROMPT.format(
            discoveries=json.dumps(discoveries, ensure_ascii=False, indent=2),
            commentary_instructions=commentary_instructions
        )

        # Call Sonnet 4.5
        self.logger.info("  Calling Sonnet 4.5 for research request generation...")
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract and parse JSON
            response_text = self._extract_json_from_response(response)
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
            request_dict = scholar_request.to_research_request(psalm_number)
            research_request = ResearchRequest.from_dict(request_dict)

            self.logger.info(f"  ✓ Research requests generated")
            return research_request

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse research request JSON: {e}")
            raise ValueError(f"Invalid JSON from research generation: {e}")
        except Exception as e:
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
            vc = VerseCommentary(
                verse_number=disc['verse_number'],
                commentary=disc.get('observations', ''),
                lexical_insights=disc.get('curious_words', []),
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
        """Get phonetic transcription for each verse of the psalm."""
        self.logger.info("  Generating phonetic transcriptions...")
        psalm = self.db.get_psalm(psalm_number)
        if not psalm:
            self.logger.error(f"Could not retrieve psalm {psalm_number} for phonetic transcription.")
            return {}

        phonetic_data = {}
        for verse in psalm.verses:
            try:
                # Call the phonetic analyst to get the detailed transcription
                analysis = self.phonetic_analyst.transcribe_verse(verse.hebrew)

                # Join the syllabified transcriptions into a single string for the prompt
                # Use 'syllable_transcription' which includes syllable boundaries (e.g., "tə-hil-lāh")
                transcribed_words = [word['syllable_transcription'] for word in analysis['words']]
                verse_transcription = " ".join(transcribed_words)
                
                phonetic_data[verse.verse] = verse_transcription
            except Exception as e:
                self.logger.error(f"Error transcribing verse {verse.verse}: {e}")
                phonetic_data[verse.verse] = "[Transcription Error]"

        self.logger.info("  ✓ Phonetic transcriptions generated.")
        return phonetic_data


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
