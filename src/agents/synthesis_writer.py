"""
Synthesis Writer Agent (Pass 3)
Phase 3c: Final commentary synthesis

This agent produces the final Psalm commentary by synthesizing:
- MacroAnalysis (thesis, structure, poetic devices)
- MicroAnalysis (verse-by-verse discoveries)
- ResearchBundle (lexicon, concordances, figurative analysis, commentary)

It produces:
1. Introduction Essay (800-1200 words) - Engages macro thesis critically
2. Verse-by-Verse Commentary - Independent scholarly angles (poetics, polemics, LXX/MT, Ugaritic, etc.)

Model: Claude Sonnet 4.5
Input: MacroAnalysis + MicroAnalysis + ResearchBundle
Output: Complete commentary with introduction and verse annotations

Author: Claude (Anthropic)
Date: 2025-10-17 (Phase 3c)
"""

import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, List, Any
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Handle imports for both module and script usage
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.schemas.analysis_schemas import MacroAnalysis, MicroAnalysis
    from src.utils.logger import get_logger
else:
    from ..schemas.analysis_schemas import MacroAnalysis, MicroAnalysis
    from ..utils.logger import get_logger


# System prompt for Introduction Essay
INTRODUCTION_ESSAY_PROMPT = """You are a biblical scholar writing an **introduction essay** for Psalm {psalm_number}.

You have been provided with:
1. **MacroAnalysis** - A macro thesis about the psalm's structure, genre, and poetic devices
2. **MicroAnalysis** - Detailed verse-by-verse discoveries
3. **ResearchBundle** - Deep lexical, concordance, and figurative language research

## YOUR INPUTS

### MACRO THESIS
{macro_analysis}

### MICRO DISCOVERIES
{micro_analysis}

### RESEARCH MATERIALS
{research_bundle}

---

## YOUR TASK: WRITE INTRODUCTION ESSAY (800-1200 words)

Write a scholarly introduction essay that:

1. **Engages the macro thesis critically**
   - You have FULL AUTHORITY to revise, refine, or reject the macro thesis if evidence warrants
   - If the thesis holds up, defend it with evidence from micro analysis and research
   - If the thesis needs refinement, change it based on your synthesis
   - If the thesis is fundamentally flawed, offer an alternative

2. **Synthesizes all three sources smoothly**
   - Integrate insights from macro structure, micro discoveries, and research materials
   - Show how lexical evidence, concordances, and figurative analysis support (or challenge) the thesis
   - Cite specific examples from the research bundle when relevant
   - Make connections between poetic devices and theological meaning
   - Novel insights are strongly encouraged. You are in conversation with the sources, not just summarizing them.

3. **Addresses major interpretive questions**
   - What is the psalm's central message and how does it function?
   - What are the key poetic/rhetorical strategies and why do they matter?
   - How does this psalm relate to its Ancient Near Eastern context?
   - What are the most significant interpretive debates or challenges?
   - What earned this psalm its place in the biblical canon?
   - What is fascinating or unique about this psalm from a literary perspective? From a theological perspective? From a historical perspective?

4. **Engages prior scholarship and classical interpretations**
   - Note relevant traditional rabbinic or patristic readings when available
   - Reference how scholars have historically interpreted key passages
   - Acknowledge interpretive debates and schools of thought
   - Example: "Traditional interpretation sees X, but recent scholarship suggests Y..."

5. **Makes intertextual connections**
   - Cite parallel biblical texts where similar language/imagery appears
   - Reference ANE parallels (Ugaritic, Akkadian, Egyptian texts) when relevant
   - Show how this psalm's language echoes or innovates or is in conversation with other texts
   - Example: "The 'voice of YHWH' formula also appears in Psalm 18..."

6. **Writes for an educated general reader**
   - Scholarly rigor but accessible prose
   - Technical terms explained when necessary
   - Balance depth with readability
   - Novel insights are strongly encouraged

7. **Uses proper citations**
   - When referring to specific Hebrew verse, phrases and terms, cite in Hebrew and English
   - in Hebrew, replace the tegragrammaton with 'ה
   - When citing research, note the source (e.g., "BDB lexicon notes...", "Concordance shows...")
   - When referencing other texts, cite book/chapter/verse (e.g., "Gen 1:2", "KTU 1.4")

8. **Stylistic guidelines**
You are a distinguished professor of biblical literature, akin to a figure like Robert Alter, Ellen F. Davis or James Kugel. Your task is to write an essay on a specific psalm for a sophisticated lay audience, such as the readers of The New Yorker or The Atlantic.

Your writing style should be scholarly, lucid, and engaging. Your tone is one of measured confidence, not breathless praise. You illuminate the text's brilliance through insightful analysis rather than by simply labeling it as "brilliant" or a "masterpiece."

Key Stylistic Directives:
Tone & Persona: Adopt a voice that is authoritative yet accessible. You are a trusted guide leading the reader through the literary and theological landscape of the psalm. Your prose should be elegant and uncluttered.

From Praise to Analysis: Do not use effusive or sycophantic language. Avoid words like "masterpiece," "tour de force," "breathtaking," "audacious," or "remarkable." Instead of telling the reader the psalm is sophisticated, show them through your analysis.

Instead of: "The psalm's central innovation lies in its theological revolution..."

Try: "The psalm's engine is the sevenfold repetition of qôl YHWH. By taking the familiar sound of the storm and attributing it solely to Israel's God, the poet re-maps the cosmos."

Use Jargon Sparingly: Academic terms like "polemic," "theophany," or "cosmology" are acceptable, but they should be used to bring clarity, not to signal academic status. When used, they should feel integrated into the prose, not dropped in like keywords. Explain the concept if necessary.

Instead of: "The psalm's opening summons to the bĕnê 'ēlîm immediately signals its polemical intent."

Try: "The psalm opens in an unexpected place: the divine throne room, where the poet calls upon the bĕnê 'ēlîm (בני אלים), the 'sons of the gods,' to pay homage. This is a direct challenge to the surrounding polytheistic world—an act of theological appropriation from the very first line."

Emphasize Action and Imagery: Use strong verbs and concrete imagery. Describe what the poet does. How do they construct the poem? What world do they build?

Instead of: "The image of Lebanon's cedars being 'broken' by YHWH's voice would have been particularly striking."

Try: "The poet makes the LORD's voice a physical force, a divine percussion that splinters the legendary cedars of Lebanon, trees that were ancient symbols of permanence and strength."

Vary Sentence Structure: Employ a mix of shorter, punchier sentences and longer, more complex ones to create a readable and engaging rhythm. Use rhetorical questions to draw the reader into the interpretive process.

Example of Stylistic Transformation:
Here are two versions of a snippet from an essay to illustrate the point:

Excessively "LLM-ish" version:

"While the macro thesis correctly identifies this psalm as a 'liturgical polemic' that appropriates Baal theology, the evidence suggests an even more sophisticated literary achievement: Psalm 29 functions as a theological tour de force that systematically dismantles polytheistic cosmology by concentrating all divine power into the sevenfold qôl-YHWH (קול־ה׳, 'voice of the LORD'), culminating not in chaotic divine display but in covenantal blessing for God's people."

Revised Version in the Target Style:

"Scholars often describe Psalm 29 as a 'liturgical polemic,' a poem that co-opts the language of Canaanite storm-god worship to declare the supremacy of Israel's God. This is true, but it doesn't capture the poem's full artistry. The poet does more than just borrow; they dismantle and rebuild. The psalm methodically gathers the scattered powers of the Canaanite pantheon—the thunder, the flood, the quaking wilderness—and concentrates them into a single, seven-fold utterance: the qôl YHWH (קול־ה׳), the 'voice of the LORD.' The result is a startling redirection of cosmic power, moving it away from raw, chaotic display and toward a final, focused act of blessing for God's people."

## CRITICAL REQUIREMENTS

- **Length**: 800-1200 words (aim for the middle of this range)
- **Tone**: Scholarly but engaging, confident but nuanced
- **Structure**: Clear paragraphs with logical flow
- **Authority**: You are the final voice - revise the thesis if needed
- **Integration**: Smoothly weave together all three input sources

---

Write the introduction essay below in plain text (NOT JSON). Use markdown formatting for emphasis (*italics*) and Hebrew transliterations.
"""


# System prompt for Verse Commentary
VERSE_COMMENTARY_PROMPT = """You are a biblical scholar writing **verse-by-verse commentary** for Psalm {psalm_number}.

You have been provided with:
1. **MacroAnalysis** - Overall thesis and structure
2. **MicroAnalysis** - Verse-by-verse discoveries
3. **ResearchBundle** - Lexical, concordance, and research materials

## YOUR INPUTS

### MACRO THESIS
{macro_analysis}

### MICRO DISCOVERIES
{micro_analysis}

### RESEARCH MATERIALS
{research_bundle}

---

## YOUR TASK: WRITE VERSE-BY-VERSE COMMENTARY

For EACH verse in the psalm, write a commentary annotation of **150-300 words** that draws on diverse scholarly angles:

### SCHOLARLY ANGLES TO CONSIDER (choose what's relevant per verse):

1. **Poetics** - Parallelism, wordplay, sound patterns, meter
2. **Polemics** - Theological debates, Canaanite appropriation, monotheistic claims
3. **Interpretive Debates** - How have scholars interpreted this verse? What are the controversies? What do classical commentators (rabbinic, patristic, medieval) say?
4. **Vorlage Insights** - LXX vs MT differences, textual variants, translation challenges
5. **Ugaritic/ANE Context** - Parallels, loan words, cultural background (cite specific texts like KTU, Enuma Elish, etc.)
6. **Lexical Depth** - Rare words, semantic ranges, etymologies (draw from BDB, concordances)
7. **Intertextuality** - Connections to other biblical texts (cite specific verses where similar language appears)
8. **Theological Significance** - What does this verse reveal about God, humanity, worship?

### IMPORTANT NOTES:

- **Independence from macro thesis**: The verse commentary need NOT always relate to the macro thesis
- **Reader interest**: Focus on what would genuinely interest and inform a reader
- **Flexibility**: Some verses may focus on poetics, others on vorlage, others on Ugaritic parallels
- **Depth over breadth**: Better to explore 2-3 angles well than mention everything superficially
- **Evidence-based**: Ground observations in the research materials provided
- **Use research bundle effectively**: The research bundle contains concordance data showing where Hebrew terms appear elsewhere in Scripture - cite these parallels! It also contains commentary excerpts - engage with these interpretive traditions!

### FORMAT FOR EACH VERSE:

**Verse [N]**
[150-300 words of commentary drawing on relevant scholarly angles]

---

## CRITICAL REQUIREMENTS

- **Cover ALL verses** in the psalm
- **Length**: 100-300 words per verse (some complex verses may go longer)
- **Variety**: Don't use the same angles for every verse - vary your approach
- **Evidence**: Cite Hebrew terms, concordance patterns, research findings
- **Readability**: Scholarly but not pedantic
- **Independence**: Don't force connections to the macro thesis if they're not natural

---

Write the verse-by-verse commentary below in plain text (NOT JSON). Use markdown formatting.
"""


class SynthesisWriter:
    """
    Pass 3: Synthesis Writer Agent using Claude Sonnet 4.5.

    Takes MacroAnalysis + MicroAnalysis + ResearchBundle and produces:
    1. Introduction essay (800-1200 words)
    2. Verse-by-verse commentary (150-300 words per verse)

    Example:
        >>> writer = SynthesisWriter(api_key="your-key")
        >>> commentary = writer.write_commentary(
        ...     macro_file="psalm_029_macro.json",
        ...     micro_file="psalm_029_micro_v2.json",
        ...     research_file="psalm_029_research_v2.md"
        ... )
        >>> print(commentary['introduction'])
        >>> print(commentary['verse_commentary'])
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        logger=None
    ):
        """
        Initialize SynthesisWriter agent.

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            logger: Logger instance (or will create default)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required (pass api_key or set ANTHROPIC_API_KEY)")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"  # Sonnet 4.5
        self.logger = logger or get_logger("synthesis_writer")

        self.logger.info(f"SynthesisWriter initialized with model {self.model}")

    def write_commentary(
        self,
        macro_file: Path,
        micro_file: Path,
        research_file: Path,
        psalm_number: Optional[int] = None,
        max_tokens_intro: int = 4000,
        max_tokens_verse: int = 16000
    ) -> Dict[str, str]:
        """
        Generate complete commentary from analysis files.

        Args:
            macro_file: Path to MacroAnalysis JSON file
            micro_file: Path to MicroAnalysis JSON file
            research_file: Path to Research Bundle markdown file
            psalm_number: Psalm number (extracted from files if not provided)
            max_tokens_intro: Max tokens for introduction essay
            max_tokens_verse: Max tokens for verse commentary

        Returns:
            Dictionary with 'introduction' and 'verse_commentary' keys

        Raises:
            ValueError: If files not found or parsing fails
        """
        self.logger.info("Starting commentary synthesis")

        # Step 1: Load input files
        macro_analysis = self._load_macro_analysis(macro_file)
        micro_analysis = self._load_micro_analysis(micro_file)
        research_bundle = self._load_research_bundle(research_file)

        # Extract psalm number
        if not psalm_number:
            psalm_number = macro_analysis.get('psalm_number', 0)

        self.logger.info(f"Synthesizing commentary for Psalm {psalm_number}")
        self.logger.info(f"  Macro thesis: {len(str(macro_analysis))} chars")
        self.logger.info(f"  Micro analysis: {len(str(micro_analysis))} chars")
        self.logger.info(f"  Research bundle: {len(research_bundle)} chars")

        # Step 2: Generate introduction essay
        introduction = self._generate_introduction(
            psalm_number=psalm_number,
            macro_analysis=macro_analysis,
            micro_analysis=micro_analysis,
            research_bundle=research_bundle,
            max_tokens=max_tokens_intro
        )

        # Step 3: Generate verse commentary
        verse_commentary = self._generate_verse_commentary(
            psalm_number=psalm_number,
            macro_analysis=macro_analysis,
            micro_analysis=micro_analysis,
            research_bundle=research_bundle,
            max_tokens=max_tokens_verse
        )

        self.logger.info("Commentary synthesis complete")
        self.logger.info(f"  Introduction: {len(introduction)} chars")
        self.logger.info(f"  Verse commentary: {len(verse_commentary)} chars")

        return {
            'introduction': introduction,
            'verse_commentary': verse_commentary,
            'psalm_number': psalm_number
        }

    def _load_macro_analysis(self, file_path: Path) -> Dict[str, Any]:
        """Load MacroAnalysis from JSON file."""
        self.logger.info(f"Loading macro analysis from {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_micro_analysis(self, file_path: Path) -> Dict[str, Any]:
        """Load MicroAnalysis from JSON file."""
        self.logger.info(f"Loading micro analysis from {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_research_bundle(self, file_path: Path) -> str:
        """Load Research Bundle from markdown file."""
        self.logger.info(f"Loading research bundle from {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _generate_introduction(
        self,
        psalm_number: int,
        macro_analysis: Dict,
        micro_analysis: Dict,
        research_bundle: str,
        max_tokens: int
    ) -> str:
        """Generate introduction essay."""
        self.logger.info(f"Generating introduction essay for Psalm {psalm_number}")

        # Format inputs
        macro_text = self._format_macro_for_prompt(macro_analysis)
        micro_text = self._format_micro_for_prompt(micro_analysis)

        # Truncate research bundle if too long (keep first 50k chars)
        research_text = research_bundle[:50000]
        if len(research_bundle) > 50000:
            research_text += "\n\n[Research bundle truncated for token limits...]"

        # Build prompt
        prompt = INTRODUCTION_ESSAY_PROMPT.format(
            psalm_number=psalm_number,
            macro_analysis=macro_text,
            micro_analysis=micro_text,
            research_bundle=research_text
        )

        # Log prompt for debugging (optional)
        if self.logger:
            self.logger.debug(f"Introduction prompt length: {len(prompt)} chars")
            # Optionally save full prompt to file for inspection
            # prompt_file = Path(f"output/debug/intro_prompt_psalm_{psalm_number}.txt")
            # prompt_file.parent.mkdir(parents=True, exist_ok=True)
            # prompt_file.write_text(prompt, encoding='utf-8')

        # Call Claude
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract text
            introduction = ""
            for block in response.content:
                if block.type == "text":
                    introduction += block.text

            self.logger.info(f"Introduction generated: {len(introduction)} chars")

            # Log API call
            self.logger.log_api_call(
                api_name="Anthropic Claude",
                endpoint=self.model,
                status_code=200,
                response_time_ms=0
            )

            return introduction.strip()

        except Exception as e:
            self.logger.error(f"Error generating introduction: {e}")
            raise

    def _generate_verse_commentary(
        self,
        psalm_number: int,
        macro_analysis: Dict,
        micro_analysis: Dict,
        research_bundle: str,
        max_tokens: int
    ) -> str:
        """Generate verse-by-verse commentary."""
        self.logger.info(f"Generating verse commentary for Psalm {psalm_number}")

        # Format inputs
        macro_text = self._format_macro_for_prompt(macro_analysis)
        micro_text = self._format_micro_for_prompt(micro_analysis)

        # Truncate research bundle if needed
        research_text = research_bundle[:100000]
        if len(research_bundle) > 100000:
            research_text += "\n\n[Research bundle truncated for token limits...]"

        # Build prompt
        prompt = VERSE_COMMENTARY_PROMPT.format(
            psalm_number=psalm_number,
            macro_analysis=macro_text,
            micro_analysis=micro_text,
            research_bundle=research_text
        )

        # Call Claude
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract text
            commentary = ""
            for block in response.content:
                if block.type == "text":
                    commentary += block.text

            self.logger.info(f"Verse commentary generated: {len(commentary)} chars")

            # Log API call
            self.logger.log_api_call(
                api_name="Anthropic Claude",
                endpoint=self.model,
                status_code=200,
                response_time_ms=0
            )

            return commentary.strip()

        except Exception as e:
            self.logger.error(f"Error generating verse commentary: {e}")
            raise

    def _format_macro_for_prompt(self, macro: Dict) -> str:
        """Format MacroAnalysis for prompt."""
        lines = []
        lines.append(f"**Thesis**: {macro.get('thesis_statement', 'N/A')}")
        lines.append(f"**Genre**: {macro.get('genre', 'N/A')}")
        lines.append(f"**Context**: {macro.get('historical_context', 'N/A')}")
        lines.append("")
        lines.append("**Structure**:")
        for div in macro.get('structural_outline', []):
            lines.append(f"  - {div.get('section', '')}: {div.get('theme', '')}")
        lines.append("")
        lines.append("**Poetic Devices**:")
        for device in macro.get('poetic_devices', []):
            lines.append(f"  - {device.get('device', '')}: {device.get('description', '')}")
        return "\n".join(lines)

    def _format_micro_for_prompt(self, micro: Dict) -> str:
        """Format MicroAnalysis for prompt."""
        lines = []
        for verse_data in micro.get('verses', []):
            verse_num = verse_data.get('verse', 0)
            commentary = verse_data.get('commentary', '')
            lines.append(f"**Verse {verse_num}**: {commentary}")

            # Add discoveries if present
            lexical = verse_data.get('lexical_insights', [])
            if lexical:
                lines.append(f"  Lexical: {', '.join(lexical)}")

            figurative = verse_data.get('figurative_analysis', [])
            if figurative:
                lines.append(f"  Figurative: {', '.join(figurative)}")

            lines.append("")

        return "\n".join(lines)

    def write_and_save(
        self,
        macro_file: str,
        micro_file: str,
        research_file: str,
        output_dir: str = "output",
        output_name: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate commentary and save to files.

        Args:
            macro_file: Path to MacroAnalysis JSON
            micro_file: Path to MicroAnalysis JSON
            research_file: Path to Research Bundle markdown
            output_dir: Directory to save output
            output_name: Base name for output files (default: psalm_NNN_commentary)

        Returns:
            Commentary dictionary with 'introduction' and 'verse_commentary'
        """
        # Generate commentary
        commentary = self.write_commentary(
            macro_file=Path(macro_file),
            micro_file=Path(micro_file),
            research_file=Path(research_file)
        )

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Determine output name
        psalm_number = commentary['psalm_number']
        if not output_name:
            output_name = f"psalm_{psalm_number:03d}_commentary"

        # Save complete commentary
        full_path = output_path / f"{output_name}.md"
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(f"# Commentary on Psalm {psalm_number}\n\n")
            f.write("## Introduction\n\n")
            f.write(commentary['introduction'])
            f.write("\n\n---\n\n")
            f.write("## Verse-by-Verse Commentary\n\n")
            f.write(commentary['verse_commentary'])

        self.logger.info(f"Saved complete commentary to {full_path}")

        # Save separate files
        intro_path = output_path / f"{output_name}_intro.md"
        with open(intro_path, 'w', encoding='utf-8') as f:
            f.write(commentary['introduction'])
        self.logger.info(f"Saved introduction to {intro_path}")

        verse_path = output_path / f"{output_name}_verses.md"
        with open(verse_path, 'w', encoding='utf-8') as f:
            f.write(commentary['verse_commentary'])
        self.logger.info(f"Saved verse commentary to {verse_path}")

        return commentary


def main():
    """Command-line interface for SynthesisWriter agent."""
    import argparse

    # Ensure UTF-8 for Hebrew output on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Generate final commentary synthesis (Pass 3: SynthesisWriter)'
    )
    parser.add_argument('--macro', type=str, required=True,
                       help='Path to MacroAnalysis JSON file')
    parser.add_argument('--micro', type=str, required=True,
                       help='Path to MicroAnalysis JSON file')
    parser.add_argument('--research', type=str, required=True,
                       help='Path to Research Bundle markdown file')
    parser.add_argument('--output-dir', type=str, default='output',
                       help='Output directory (default: output)')
    parser.add_argument('--output-name', type=str, default=None,
                       help='Base name for output files (default: psalm_NNN_commentary)')

    args = parser.parse_args()

    try:
        # Initialize writer
        writer = SynthesisWriter()

        print("=" * 80)
        print("SYNTHESIS WRITER (Pass 3)")
        print("=" * 80)
        print()
        print(f"Macro Analysis:  {args.macro}")
        print(f"Micro Analysis:  {args.micro}")
        print(f"Research Bundle: {args.research}")
        print()
        print("Generating commentary...")
        print("This may take 60-120 seconds for both introduction and verse commentary.")
        print()

        # Generate and save
        commentary = writer.write_and_save(
            macro_file=args.macro,
            micro_file=args.micro,
            research_file=args.research,
            output_dir=args.output_dir,
            output_name=args.output_name
        )

        # Display preview
        print("=" * 80)
        print(f"COMMENTARY SYNTHESIS COMPLETE: PSALM {commentary['psalm_number']}")
        print("=" * 80)
        print()
        print("INTRODUCTION ESSAY (preview):")
        print(commentary['introduction'][:500] + "...")
        print()
        print("VERSE COMMENTARY (preview):")
        print(commentary['verse_commentary'][:500] + "...")
        print()
        print("=" * 80)
        print(f"Complete commentary saved to {args.output_dir}/")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
