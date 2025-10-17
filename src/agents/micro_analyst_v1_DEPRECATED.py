"""
MicroAnalyst Agent - Pass 2 of Five-Pass Scholar-Writer Architecture

Performs detailed verse-by-verse analysis with full research integration.
This is the most complex agent in the pipeline, performing TWO stages:

Stage 1: Research Request Generation
    - Receives MacroAnalysis (thesis, structure, research questions)
    - Generates comprehensive research requests (25-50 BDB entries, concordances, figurative, commentary)
    - Uses extended thinking for strategic research planning

Stage 2: Verse-by-Verse Analysis
    - Receives MacroAnalysis + Research Bundle
    - Produces detailed commentary for every verse
    - Shows how each verse supports macro thesis
    - Integrates lexical, figurative, concordance, and commentary data

Model: Claude Sonnet 4.5 with extended thinking
Input: MacroAnalysis + Psalm text + RAG context
Output: MicroAnalysis object + ResearchBundle

Author: Claude (Anthropic)
Date: 2025 (Phase 3b)
"""

import sys
import os
import json
from pathlib import Path
from typing import Tuple, Dict, List, Optional, Any
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


# Stage 1: Research Request Generation Prompt
RESEARCH_REQUEST_PROMPT = """You are generating research requests for detailed verse-by-verse analysis of Psalm {psalm_number}.

You have completed the MACRO ANALYSIS (Pass 1):

{macro_analysis}

---

PSALM TEXT:

{psalm_text}

---

RAG CONTEXT (Scholarly Resources):

{rag_context}

---

Now you must identify what research data is needed for thorough verse-by-verse commentary in Pass 2.

Generate specific research requests in four categories:

1. **BDB LEXICON REQUESTS**
   - Identify ALL significant Hebrew words that deserve lexical investigation across the entire psalm
   - BE COMPREHENSIVE. Request lexicon entries for EVERY theologically, poetically, or semantically significant word
   - For each word, explain WHY it's significant (aligned with macro thesis)
   - Expected volume: 2-4 words per verse (so {verse_count}-verse psalm = {min_bdb}-{max_bdb} requests)
   - Include:
     * Theological terms relevant to thesis
     * Action verbs with theological implications
     * Metaphorical language (especially relevant to poetic devices identified)
     * Rare or unusual vocabulary
     * Terms with rich semantic ranges
     * Words where etymology illuminates meaning
   - ALIGN WITH MACRO THESIS: Prioritize words that support your thesis and research questions

2. **CONCORDANCE SEARCHES**
   - Identify Hebrew roots or phrases to trace across biblical corpus
   - Focus on thematic patterns relevant to macro thesis
   - Specify for each:
     * "consonantal": All forms of root
     * "voweled": Distinguish homographs
     * "exact": Specific vocalized form
   - Specify scope:
     * "auto": Smart frequency detection (RECOMMENDED)
     * "Psalms" / "Torah" / "Prophets" / "Writings" / "Tanakh"
   - Be strategic: 5-10 searches focused on thesis-relevant themes

3. **FIGURATIVE LANGUAGE CHECKS**
   - Identify verses with metaphor, simile, personification, metonymy
   - For each verse specify:
     * Verse number
     * Likely figurative type
     * Reason (how it relates to thesis/poetic devices)
     * VEHICLE: What comparison/image is used
     * VEHICLE_SYNONYMS: 2-4 related terms for searching

4. **COMMENTARY REQUESTS (OPTIONAL)**
   - Identify 2-5 key verses for traditional commentary
   - Select verses that are:
     * Theologically complex
     * Central to thesis
     * Using rare vocabulary
     * Interpretively challenging

CRITICAL REQUIREMENTS:
- ALIGN WITH MACRO THESIS: All requests should support analysis of thesis/research questions
- BE COMPREHENSIVE: Request lexicon entries for ALL significant words
- BE SPECIFIC: Justify every request with reference to macro analysis
- THINK STRATEGICALLY: Use your research questions from Pass 1 to guide requests

OUTPUT FORMAT: Return ONLY valid JSON with this structure:

{{
  "bdb_requests": [
    {{"word": "קוֹל", "reason": "Voice of LORD - central to sevenfold anaphora and thesis about divine speech"}},
    {{"word": "מַבּוּל", "reason": "Flood term in v.10 - connects to primordial sovereignty (Research Q3)"}},
    ... (Continue for ALL significant words in psalm)
  ],
  "concordance_searches": [
    {{"query": "קוֹל יְהוָה", "level": "exact", "scope": "Psalms", "purpose": "Track 'voice of LORD' formula across Psalms"}},
    {{"query": "בְּנֵי אֵלִים", "level": "exact", "scope": "Tanakh", "purpose": "Divine council imagery (Research Q4)"}},
    ... (5-10 strategic searches)
  ],
  "figurative_checks": [
    {{"verse": 3, "likely_type": "metaphor", "reason": "Waters as chaos/power - supports storm theology thesis", "vehicle": "waters", "vehicle_synonyms": ["sea", "deep", "flood", "ocean"]}},
    ... (Check ALL verses with figurative language)
  ],
  "commentary_requests": [
    {{"verse": 10, "reason": "Rare mabbul term - need classical interpretation for primordial theology"}},
    ... (2-5 key verses)
  ]
}}

IMPORTANT: Your requests will directly support the Scholar-Writer's verse-by-verse analysis. Request comprehensive lexical data for ALL significant words.

Return ONLY the JSON object, no additional text.
"""


# Stage 2: Verse-by-Verse Analysis Prompt
VERSE_ANALYSIS_PROMPT = """You are performing detailed verse-by-verse analysis of Psalm {psalm_number}.

MACRO ANALYSIS (Pass 1):

{macro_analysis}

---

PSALM TEXT WITH LXX:

{psalm_text_with_lxx}

---

RESEARCH BUNDLE:

{research_bundle}

---

TASK:
Analyze each verse of Psalm {psalm_number} with comprehensive commentary that:

1. **Integrates Research Data**:
   - Lexical insights from BDB entries
   - Figurative analysis from database
   - Traditional commentary excerpts
   - Concordance patterns (thematic connections)

2. **Connects to Macro Thesis**:
   - Show how each verse supports overall thesis
   - Reference structural outline and poetic devices
   - Answer research questions from Pass 1

3. **Provides Scholarly Depth**:
   - Hebrew word analysis (etymology, semantics, usage)
   - LXX Greek translation insights (early interpretation)
   - Literary analysis (parallelism, word choice, structure)
   - Theological implications

4. **Maintains Verse-Level Focus**:
   - Each verse gets thorough treatment
   - Don't skip verses or group too much
   - Balance depth with conciseness

OUTPUT FORMAT: Return ONLY valid JSON with this structure:

{{
  "verse_commentaries": [
    {{
      "verse_number": 1,
      "commentary": "Full verse commentary integrating all research (2-4 paragraphs). Discuss Hebrew terms, LXX insights, figurative language, structural role, theological meaning. Be specific and cite evidence.",
      "lexical_insights": [
        "קוֹל (qol) - 'voice/sound': BDB shows range from natural sounds to divine speech. Sevenfold repetition (vv.3-9) creates liturgical rhythm.",
        "יְהוָה - Divine name: Repeated 18x, emphasizing personal covenant God vs. generic divine force."
      ],
      "figurative_analysis": [
        "Waters metaphor (v.3): Chaos imagery from ANE creation myths, here subordinated to YHWH's voice.",
        "Anaphora device: Sevenfold 'voice of LORD' - completeness symbolism (Research Q1)."
      ],
      "thesis_connection": "Opening summons to divine beings establishes hierarchical framework central to thesis: YHWH's supremacy over divine realm precedes demonstration of natural sovereignty in vv.3-9."
    }},
    {{
      "verse_number": 2,
      "commentary": "...",
      "lexical_insights": [...],
      "figurative_analysis": [...],
      "thesis_connection": "..."
    }},
    ... (Continue for EVERY verse in psalm)
  ],
  "thematic_threads": [
    "Divine sovereignty: Progresses from divine council (vv.1-2) → natural realm (vv.3-9) → human blessing (vv.10-11)",
    "Storm-god polemic: Systematic transfer of Baal attributes to YHWH throughout psalm",
    "Sevenfold structure: Completeness theme in anaphora, supporting absolute sovereignty claim"
  ],
  "synthesis_notes": "Pass 3 should emphasize liturgical performance context - psalm likely performed antiphonally with sevenfold 'voice' as crescendo. Introduction should establish Ugaritic background before detailed analysis. Conclusion should highlight unique movement from cosmic power to covenantal intimacy (vv.10-11 shift)."
}}

CRITICAL REQUIREMENTS:
- Analyze EVERY verse (no skipping)
- Integrate research data (cite BDB entries, figurative instances, commentaries)
- Connect each verse to macro thesis explicitly
- Use extended thinking for deep analysis
- Be specific and evidence-based
- Balance scholarly depth with readability

Return ONLY the JSON object, no additional text.
"""


class MicroAnalyst:
    """
    MicroAnalyst Agent - Pass 2 of Five-Pass Architecture.

    Performs two-stage verse-by-verse analysis:
    1. Generate comprehensive research requests
    2. Analyze each verse with research integrated

    Uses Claude Sonnet 4.5 with extended thinking for deep analysis.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        db_path: str = "data/tanakh.db",
        docs_dir: str = "docs",
        logger=None
    ):
        """
        Initialize MicroAnalyst agent.

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            db_path: Path to Tanakh SQLite database
            docs_dir: Path to docs directory for RAG documents
            logger: Logger instance (or will create default)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"  # Sonnet 4.5
        self.rag_manager = RAGManager(docs_dir)
        self.db = TanakhDatabase(Path(db_path))
        self.research_assembler = ResearchAssembler()
        self.logger = logger or get_logger("micro_analyst")

    def analyze_psalm(
        self,
        psalm_number: int,
        macro_analysis: MacroAnalysis
    ) -> Tuple[MicroAnalysis, ResearchBundle]:
        """
        Perform complete two-stage micro analysis.

        Args:
            psalm_number: Psalm number (1-150)
            macro_analysis: MacroAnalysis object from Pass 1

        Returns:
            Tuple of (MicroAnalysis, ResearchBundle)

        Raises:
            ValueError: If analysis fails or response invalid
        """
        self.logger.info(f"Starting micro analysis for Psalm {psalm_number}")

        # Stage 1: Generate research requests
        self.logger.info("Stage 1: Generating research requests...")
        research_request = self._generate_research_requests(psalm_number, macro_analysis)

        # Stage 2: Assemble research bundle
        self.logger.info("Stage 2: Assembling research bundle...")
        research_bundle = self.research_assembler.assemble(research_request)

        summary = research_bundle.to_dict()['summary']
        self.logger.info(f"  Lexicon entries: {summary['lexicon_entries']}")
        self.logger.info(f"  Concordance results: {summary['concordance_results']}")
        self.logger.info(f"  Figurative instances: {summary['figurative_instances']}")
        self.logger.info(f"  Commentary entries: {summary['commentary_entries']}")

        # Stage 3: Verse-by-verse analysis
        self.logger.info("Stage 3: Performing verse-by-verse analysis...")
        micro_analysis = self._analyze_verses(psalm_number, macro_analysis, research_bundle)

        self.logger.info(f"Micro analysis complete: {len(micro_analysis.verse_commentaries)} verses analyzed")

        return micro_analysis, research_bundle

    def _generate_research_requests(
        self,
        psalm_number: int,
        macro_analysis: MacroAnalysis
    ) -> ResearchRequest:
        """
        Stage 1: Generate comprehensive research requests.

        Args:
            psalm_number: Psalm number
            macro_analysis: MacroAnalysis from Pass 1

        Returns:
            ResearchRequest object for Research Assembler
        """
        # Fetch psalm text
        psalm = self.db.get_psalm(psalm_number)
        if not psalm:
            raise ValueError(f"Psalm {psalm_number} not found in database")

        # Format psalm text
        psalm_text = self._format_psalm_text(psalm)

        # Get RAG context
        rag_context = self.rag_manager.get_rag_context(psalm_number)
        rag_formatted = self.rag_manager.format_for_prompt(rag_context, include_framework=False)

        # Calculate expected research volume
        verse_count = len(psalm.verses)
        min_bdb = verse_count * 2
        max_bdb = verse_count * 4

        # Format prompt
        prompt = RESEARCH_REQUEST_PROMPT.format(
            psalm_number=psalm_number,
            macro_analysis=macro_analysis.to_markdown(),
            psalm_text=psalm_text,
            rag_context=rag_formatted,
            verse_count=verse_count,
            min_bdb=min_bdb,
            max_bdb=max_bdb
        )

        # Call Sonnet 4.5 with extended thinking
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                thinking={
                    "type": "enabled",
                    "budget_tokens": 5000
                },
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract JSON from response
            response_text = self._extract_json_from_response(response)

            # Parse and validate
            data = json.loads(response_text)
            scholar_request = ScholarResearchRequest.from_dict(data)

            # Convert to ResearchRequest format
            request_dict = scholar_request.to_research_request(psalm_number)
            research_request = ResearchRequest.from_dict(request_dict)

            self.logger.info(f"Research requests generated:")
            self.logger.info(f"  BDB: {len(scholar_request.bdb_requests)}")
            self.logger.info(f"  Concordance: {len(scholar_request.concordance_searches)}")
            self.logger.info(f"  Figurative: {len(scholar_request.figurative_checks)}")
            self.logger.info(f"  Commentary: {len(scholar_request.commentary_requests or [])}")

            return research_request

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse research request JSON: {e}")
            raise ValueError(f"Invalid JSON from MicroAnalyst Stage 1: {e}")
        except Exception as e:
            self.logger.error(f"Error generating research requests: {e}")
            raise

    def _analyze_verses(
        self,
        psalm_number: int,
        macro_analysis: MacroAnalysis,
        research_bundle: ResearchBundle
    ) -> MicroAnalysis:
        """
        Stage 2: Perform verse-by-verse analysis with research.

        Args:
            psalm_number: Psalm number
            macro_analysis: MacroAnalysis from Pass 1
            research_bundle: ResearchBundle from Stage 1

        Returns:
            MicroAnalysis object
        """
        # Fetch psalm text with LXX
        psalm = self.db.get_psalm(psalm_number)
        if not psalm:
            raise ValueError(f"Psalm {psalm_number} not found in database")

        # Format psalm text with LXX from RAG context
        psalm_text_with_lxx = self._format_psalm_with_lxx(psalm, research_bundle.rag_context)

        # Format research bundle as markdown
        research_md = research_bundle.to_markdown()

        # Format prompt
        prompt = VERSE_ANALYSIS_PROMPT.format(
            psalm_number=psalm_number,
            macro_analysis=macro_analysis.to_markdown(),
            psalm_text_with_lxx=psalm_text_with_lxx,
            research_bundle=research_md
        )

        # Call Sonnet 4.5 with extended thinking
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=16384,  # Longer for verse-by-verse analysis
                thinking={
                    "type": "enabled",
                    "budget_tokens": 10000
                },
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract JSON from response
            response_text = self._extract_json_from_response(response)

            # Parse and validate
            data = json.loads(response_text)

            # Create MicroAnalysis object
            verse_commentaries = [
                VerseCommentary(**vc) if isinstance(vc, dict) else vc
                for vc in data.get('verse_commentaries', [])
            ]

            micro_analysis = MicroAnalysis(
                psalm_number=psalm_number,
                verse_commentaries=verse_commentaries,
                thematic_threads=data.get('thematic_threads', []),
                synthesis_notes=data.get('synthesis_notes', '')
            )

            self.logger.info(f"Verse analysis complete: {len(verse_commentaries)} verses")
            self.logger.info(f"Thematic threads identified: {len(micro_analysis.thematic_threads)}")

            return micro_analysis

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse verse analysis JSON: {e}")
            raise ValueError(f"Invalid JSON from MicroAnalyst Stage 2: {e}")
        except Exception as e:
            self.logger.error(f"Error analyzing verses: {e}")
            raise

    def _extract_json_from_response(self, response: Any) -> str:
        """
        Extract JSON from Anthropic API response.

        Handles both text and thinking blocks.

        Args:
            response: Anthropic API response

        Returns:
            JSON string
        """
        # Find text content (skip thinking blocks)
        for block in response.content:
            if block.type == "text":
                return block.text.strip()

        raise ValueError("No text content found in response")

    def _format_psalm_text(self, psalm) -> str:
        """Format psalm text for prompt."""
        lines = [f"Psalm {psalm.chapter}"]
        lines.append("")

        for verse in psalm.verses:
            lines.append(f"v{verse.verse}: {verse.hebrew}")
            lines.append(f"    {verse.english}")
            lines.append("")

        return "\n".join(lines)

    def _format_psalm_with_lxx(self, psalm, rag_context) -> str:
        """Format psalm text with LXX translation."""
        lines = [f"Psalm {psalm.chapter}"]
        lines.append("")

        # Parse LXX verses from rag_context
        lxx_verses = {}
        if rag_context and rag_context.lxx_text:
            for line in rag_context.lxx_text.split('\n'):
                if line.startswith('v'):
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        verse_num = int(parts[0][1:])
                        lxx_verses[verse_num] = parts[1].strip()

        for verse in psalm.verses:
            verse_num = verse.verse
            lines.append(f"v{verse_num} (Hebrew): {verse.hebrew}")
            lines.append(f"v{verse_num} (English): {verse.english}")

            # Add LXX if available
            if verse_num in lxx_verses:
                lines.append(f"v{verse_num} (LXX): {lxx_verses[verse_num]}")

            lines.append("")

        return "\n".join(lines)


def main():
    """Command-line interface for MicroAnalyst agent."""
    import argparse

    # Ensure UTF-8 for Hebrew/Greek output on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Perform verse-by-verse micro analysis (Pass 2)'
    )
    parser.add_argument('psalm_number', type=int,
                       help='Psalm number (1-150)')
    parser.add_argument('macro_analysis_file', type=str,
                       help='Path to MacroAnalysis JSON file from Pass 1')
    parser.add_argument('--output-dir', type=str, default='output/phase3_test',
                       help='Output directory for results')
    parser.add_argument('--db-path', type=str, default='data/tanakh.db',
                       help='Path to Tanakh database')

    args = parser.parse_args()

    try:
        # Load macro analysis
        from src.schemas.analysis_schemas import load_macro_analysis
        macro_analysis = load_macro_analysis(args.macro_analysis_file)

        print(f"Loaded MacroAnalysis for Psalm {macro_analysis.psalm_number}")
        print(f"Thesis: {macro_analysis.thesis_statement[:100]}...")
        print()

        # Initialize agent
        analyst = MicroAnalyst(db_path=args.db_path)

        # Perform analysis
        print(f"Analyzing Psalm {args.psalm_number}...")
        micro_analysis, research_bundle = analyst.analyze_psalm(args.psalm_number, macro_analysis)

        # Save results
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save MicroAnalysis (JSON + Markdown)
        micro_json_path = output_dir / f"psalm_{args.psalm_number:03d}_micro.json"
        micro_md_path = output_dir / f"psalm_{args.psalm_number:03d}_micro.md"

        with open(micro_json_path, 'w', encoding='utf-8') as f:
            f.write(micro_analysis.to_json())

        with open(micro_md_path, 'w', encoding='utf-8') as f:
            f.write(micro_analysis.to_markdown())

        # Save Research Bundle (Markdown)
        bundle_md_path = output_dir / f"psalm_{args.psalm_number:03d}_research.md"
        with open(bundle_md_path, 'w', encoding='utf-8') as f:
            f.write(research_bundle.to_markdown())

        print(f"\n=== ANALYSIS COMPLETE ===")
        print(f"Verses analyzed: {len(micro_analysis.verse_commentaries)}")
        print(f"Thematic threads: {len(micro_analysis.thematic_threads)}")
        print(f"\nOutput files:")
        print(f"  {micro_json_path}")
        print(f"  {micro_md_path}")
        print(f"  {bundle_md_path}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
