"""
Master Editor Agent (Pass 4 - Final Review & Enhancement)

This agent uses GPT-5 (o1) to provide final editorial review and enhancement of the
generated commentary, elevating it from "good" to "National Book Award" level.

The Master Editor has access to ALL research materials and performs:
1. Critical review of introduction essay and verse commentary
2. Identification of weaknesses (factual errors, missed insights, style issues)
3. Revision and rewriting to achieve excellence

Editorial Focus Areas:
- Factual accuracy (e.g., no biblical errors)
- Completeness (all interesting elements brought to light)
- Poetic and literary analysis depth
- Style quality (avoiding LLM-ish breathlessness, maintaining scholarly tone)
- Coherence and argumentation strength
- Appropriate technical terminology usage
- Balance between introduction and verse commentary (complementary, not repetitive)

Model: GPT-5 (o1)
Input: Introduction + Verse Commentary + Full Research Bundle
Output: Revised Introduction + Revised Verse Commentary with editorial notes

Expertise Level: Robert Alter, James Kugel, Harold Bloom
Target Audience: Intelligent, well-read lay readers

Author: Claude (Anthropic)
Date: 2025-10-18
"""

import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Handle imports for both module and script usage
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.utils.logger import get_logger
else:
    from ..utils.logger import get_logger


# Master Editor System Prompt
MASTER_EDITOR_PROMPT = """You are a MASTER EDITOR and biblical scholar of the highest caliber, comparable to Robert Alter, James Kugel, Harold Bloom, or Ellen F. Davis.

You have been provided with:
1. **Introduction Essay** - A scholarly introduction to Psalm {psalm_number}
2. **Verse-by-Verse Commentary** - Detailed verse annotations
3. **Full Research Bundle** - Complete lexicon entries (BDB), concordance data, figurative language analysis, traditional commentary, Hebrew/English/LXX texts

Your task: Review the introduction and verse commentary critically, identify weaknesses, and revise/rewrite to achieve EXCELLENCE.

## YOUR INPUTS

### INTRODUCTION ESSAY (for review)
{introduction_essay}

### VERSE-BY-VERSE COMMENTARY (for review)
{verse_commentary}

### FULL RESEARCH BUNDLE
{research_bundle}

### PSALM TEXT (Hebrew, English, LXX)
{psalm_text}

### MACRO THESIS (original structural analysis)
{macro_analysis}

### MICRO DISCOVERIES (verse-level observations)
{micro_analysis}

### ANALYTICAL FRAMEWORK (for reference on poetic conventions)
{analytical_framework}

---

## YOUR EDITORIAL REVIEW CRITERIA

Review the introduction and verse commentary for these issues:

### 1. FACTUAL ERRORS
- Biblical errors (e.g., "Jacob had brothers" when he had only one - Esau)
- Misattributions of texts or quotations
- Incorrect historical or cultural claims
- Mistaken grammatical analysis
- Wrong verse references

### 2. MISSED OPPORTUNITIES
- Phonetic transcription data available but not used to analyze sound patterns (alliteration, assonance)
- Phonetic claims made that CONTRADICT the provided transcription (e.g., claiming "soft f" when transcription shows "p")
- LXX suggests alternative Vorlage not mentioned
- Poetic devices (e.g. assonance, chiasm, inclusio, parallelism) not described
- Unusual or interesting Hebrew phrases not commented on (e.g., distinctive idioms, unusual word pairings like הֲ֭דַר כְּב֣וֹד הוֹדֶ֑ךָ or עֱז֣וּז נֽוֹרְאֹתֶ֣יךָ)
- Interesting lexical insights in BDB not surfaced
- Concordance patterns not explored
- Figurative language not analyzed
- Figurative language parallels from database not cited or analyzed
- ANE parallels available but not discussed
- Comparative textual insights (e.g. MT vs LXX) not addressed
- Research questions identified by Macro and Micro analysts not answered (even when answerable with available materials)

### 3. STYLISTIC PROBLEMS
**Too "LLM-ish" or breathless:**
- Overuse of words like: "masterpiece," "tour de force," "breathtaking," "audacious," "remarkable," "stunning"
- Telling instead of showing (saying "brilliant" instead of demonstrating brilliance through analysis)
- Academic jargon dropped in without integration or explanation
- Unnecessarily complex sentence structures that obscure rather than illuminate

**Should conform to this style:**
- Measured, confident tone (like a distinguished professor)
- Show brilliance through analysis, don't label it
- Use strong verbs and concrete imagery
- Vary sentence structure for readability
- Explain technical terms when needed (e.g., "jussive," "anaphora," "chiasm," "inclusio")
- Elegant, uncluttered prose for sophisticated lay readers (New Yorker/Atlantic level)

### 4. ARGUMENT COHERENCE
- Introduction thesis unclear or unsupported
- Verse commentary disconnected from overall argument
- Logical gaps or contradictions
- Claims without evidence from research materials

### 5. BALANCE ISSUES
- Introduction and verse commentary repeat each other excessively
- Items of interest belong in both: introduction should mention briefly, verse commentary should explore in depth
- Introduction too general, missing specific textual engagement
- Verse commentary too superficial, missing scholarly depth

### 6. UNDEFINED TECHNICAL TERMS
- Terms like "jussive," "anaphora," "chiasm," "inclusio" used without explanation
- Hebrew grammatical terms not clarified for lay readers
- Assumed knowledge of ANE context without providing background

### 7. AUDIENCE APPROPRIATENESS
- Too academic and inaccessible for intelligent lay readers
- Too simplistic and lacking scholarly rigor
- Missing the balance of being "accessible but not popularizing"
- Missing the spark that makes things interesting for a curious intelligent reader

---

## YOUR TASK: EDITORIAL REVISION

**Stage 1: Critical Analysis**
First, provide a brief editorial assessment (200-400 words):
- What works well in the current draft?
- What are the main weaknesses?
- What specific revisions are needed?
- What insights from the research bundle were missed?
- What interesting questions were asked by the Macro and Micro analysts but not answered, which CAN be answered with the available research materials?
- Were unusual or interesting Hebrew phrases and poetic devices adequately commented on in the verse-by-verse commentary?

**Figurative Language Assessment:**
- Are interesting biblical parallels from the figurative language database specifically cited (book:chapter:verse)?
- Does the commentary analyze usage patterns (frequency, typical contexts)?
- Does it provide insights beyond generic observations?
- Are comparisons used to illuminate THIS psalm's distinctive usage?

**Stage 2: Revised Introduction**
Rewrite the introduction essay to address identified weaknesses. The revised introduction should:
- Maintain 800-1400 words (can be longer if genuinely warranted by interesting findings and/or length of the psalm)
- Correct any factual errors
- Surface missed insights from research materials
- Address answerable questions raised by the Macro and Micro analysts (weave answers into the essay where appropriate)
- Achieve the target style (Alter/Kugel/Bloom level)
- Define technical terms for lay readers
- Engage specific texts (Hebrew, LXX) with analysis

**Stage 3: Revised Verse Commentary**
Rewrite the verse-by-verse commentary to address identified weaknesses. For each verse:
- **Length**: Target 300-500 words per verse. Shorter (200-250 words) is acceptable for simple verses with minimal interesting features. Longer (500-800 words) is ENCOURAGED and often NECESSARY for verses with:
  * Unusual Hebrew phrases or idioms (like הֲ֭דַר כְּב֣וֹד הוֹדֶ֑ךָ or עֱז֣וּז נֽוֹרְאֹתֶ֣יךָ)
  * Complex poetic devices (chiasm, inclusio, intricate parallelism)
  * Significant textual variants (MT vs LXX differences)
  * Important interpretive questions that can be answered with research materials
  * Rich figurative language requiring comparative analysis

  Remember: intelligent lay readers are HUNGRY for substantive analysis of linguistic and literary features. Don't shortchange them!

- **Scholarly Grounding**: Your analysis must be grounded in the provided research bundle and demonstrate awareness of the principles in the **ANALYTICAL FRAMEWORK** document. Use its terminology (e.g., "telescopic analysis," "A is so, and what's more, B") where appropriate to frame your insights.

- **Discretion**: You have full editorial discretion. You are not required to include every detail from the synthesizer's commentary. Your role is to *evaluate* the synthesizer's choices regarding phonetic and figurative language, and then decide whether to retain, enhance, rewrite, or replace them to achieve the highest level of scholarly excellence.

- **Items of interest to include** (when relevant):
  * Poetics (parallelism, wordplay, structure, clever devices, sound patterns (USE the authoritative phonetic information you are provided))
  * **Unusual turns of phrase**: When a verse contains an interesting or unusual Hebrew phrase, idiom, or construction (like הֲ֭דַר כְּב֣וֹד הוֹדֶ֑ךָ or עֱז֣וּז נֽוֹרְאֹתֶ֣יךָ), comment on it—explain what makes it distinctive, how it functions poetically, and what it contributes to the verse's meaning
  * Literary insights (narrative techniques, rhetorical strategies)
  * Historical and cultic insights (worship setting, historical context)
  * Comparative religion (ANE parallels, theological contrasts)
  * Grammar and syntax (especially when illuminating)
  * Textual criticism (MT vs LXX, hints about Vorlage)
  * Comparative biblical usage (concordance insights showing how terms/phrases appear elsewhere)
  * Figurative language analysis (how vehicles/metaphors work across Scripture)
  * Timing/composition clues (vocabulary, theology, historical references)
  * Traditional interpretation (Rashi, Ibn Ezra, Radak, church fathers)

**Figurative Language Integration:**
For verses with figurative language where research provided biblical parallels:
- MUST cite at least one specific biblical parallel from the database (book:chapter:verse)
- MUST analyze the usage pattern (frequency, typical contexts)
- MUST note how this psalm's use compares to typical usage
- SHOULD provide insight beyond generic observation

Example of GOOD: "The 'opened hand' (v. 16) echoes Deut 15:8's generosity idiom but uniquely applies human covenant obligation to divine providence—appearing 23x in Scripture primarily in ethics contexts."

Example of BAD: "Verse 16 speaks of God opening his hand. This imagery appears elsewhere in Scripture." (too vague, no specific citations, no pattern analysis)

- **Address interesting questions**: When relevant to specific verses, address answerable questions raised by the Macro and Micro analysts
- **Complement the introduction**: Don't repeat what the introduction covered in depth; add verse-specific detail
- **Correct style**: Avoid breathless LLM language; show rather than tell
- **Define terms**: Explain technical terminology for lay readers
- **Emphasize the interesting**: Make sure to comment on unusual turns of phrase, distinctive Hebrew idioms, and poetic devices. These linguistic and literary features are precisely what intelligent lay readers find fascinating.

---

## OUTPUT FORMAT

Return your response in this exact structure:

### EDITORIAL ASSESSMENT

[Your 200-400 word critical analysis of the current draft]

### REVISED INTRODUCTION

[The complete revised introduction essay, 800-1400 words]

### REVISED VERSE COMMENTARY

**Verse 1**
[Revised commentary for verse 1]

**Verse 2**
[Revised commentary for verse 2]

[Continue for all verses...]

---

## CRITICAL REQUIREMENTS

- **Authority**: You are the final editorial voice - make bold revisions where needed
- **Scholarship**: Ground all claims in the research materials provided
- **Accessibility**: Write for intelligent lay readers (New Yorker/Atlantic audience)
- **Style**: Measured confidence, not breathless praise; show, don't tell
- **Completeness**: Cover all verses, define technical terms, engage specific texts
- **Excellence**: Elevate from "good" to "National Book Award" level

Begin your editorial review and revision below.
"""


class MasterEditor:
    """
    Pass 4: Master Editor Agent using GPT-5 (o1).

    Takes completed commentary (introduction + verse) plus full research bundle
    and provides expert editorial review and revision.

    This agent has the highest editorial authority and aims to elevate commentary
    from "good" to "excellent" - National Book Award level scholarly writing.

    Example:
        >>> editor = MasterEditor(api_key="your-openai-key")
        >>> result = editor.edit_commentary(
        ...     introduction_file="psalm_023_synthesis_intro.md",
        ...     verse_file="psalm_023_synthesis_verses.md",
        ...     research_file="psalm_023_research_v2.md",
        ...     macro_file="psalm_023_macro.json",
        ...     micro_file="psalm_023_micro_v2.json"
        ... )
        >>> print(result['assessment'])
        >>> print(result['revised_introduction'])
        >>> print(result['revised_verses'])
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        logger=None
    ):
        """
        Initialize Master Editor agent.

        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            logger: Logger instance (or will create default)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required (pass api_key or set OPENAI_API_KEY)")

        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-5"
        self.logger = logger or get_logger("master_editor")

        self.logger.info(f"MasterEditor initialized with model {self.model}")

    def edit_commentary(
        self,
        introduction_file: Path,
        verse_file: Path,
        research_file: Path,
        macro_file: Path,
        micro_file: Path,
        psalm_text_file: Optional[Path] = None,
        psalm_number: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Perform master editorial review and revision.

        Args:
            introduction_file: Path to introduction essay markdown
            verse_file: Path to verse commentary markdown
            research_file: Path to research bundle markdown
            macro_file: Path to macro analysis JSON
            micro_file: Path to micro analysis JSON
            psalm_text_file: Path to psalm text (Hebrew/English/LXX) - optional
            psalm_number: Psalm number (extracted from files if not provided)

        Returns:
            Dictionary with:
                - 'assessment': Editorial analysis
                - 'revised_introduction': Revised introduction essay
                - 'revised_verses': Revised verse commentary
                - 'psalm_number': Psalm number

        Raises:
            ValueError: If files not found or parsing fails
        """
        self.logger.info("Starting master editorial review")

        # Load all inputs
        introduction = self._load_text_file(introduction_file)
        verse_commentary = self._load_text_file(verse_file)
        research_bundle = self._load_text_file(research_file)
        macro_analysis = self._load_json_file(macro_file)
        micro_analysis = self._load_json_file(micro_file)

        # Extract psalm number
        if not psalm_number:
            psalm_number = macro_analysis.get('psalm_number', 0)

        # Load or retrieve psalm text
        psalm_text = ""
        if psalm_text_file and psalm_text_file.exists():
            psalm_text = self._load_text_file(psalm_text_file)
        else:
            # Try to extract from database
            psalm_text = self._get_psalm_text(psalm_number)

        # Load analytical framework from RAG
        try:
            from src.agents.rag_manager import RAGManager
            rag_manager = RAGManager("docs")
            analytical_framework = rag_manager.load_analytical_framework()
            self.logger.info("✓ Analytical framework loaded successfully for Master Editor.")
        except Exception as e:
            self.logger.warning(f"Could not load analytical framework: {e}")
            analytical_framework = "[Analytical framework not available]"

        self.logger.info(f"Editing commentary for Psalm {psalm_number}")
        self.logger.info(f"  Introduction: {len(introduction)} chars")
        self.logger.info(f"  Verse commentary: {len(verse_commentary)} chars")
        self.logger.info(f"  Research bundle: {len(research_bundle)} chars")

        # Generate editorial revision
        result = self._perform_editorial_review(
            psalm_number=psalm_number,
            introduction=introduction,
            verse_commentary=verse_commentary,
            research_bundle=research_bundle,
            macro_analysis=macro_analysis,
            micro_analysis=micro_analysis,
            psalm_text=psalm_text,
            analytical_framework=analytical_framework
        )

        self.logger.info("Master editorial review complete")
        self.logger.info(f"  Assessment: {len(result['assessment'])} chars")
        self.logger.info(f"  Revised introduction: {len(result['revised_introduction'])} chars")
        self.logger.info(f"  Revised verses: {len(result['revised_verses'])} chars")

        return result

    def _perform_editorial_review(
        self,
        psalm_number: int,
        introduction: str,
        verse_commentary: str,
        research_bundle: str,
        macro_analysis: Dict,
        micro_analysis: Dict,
        psalm_text: str,
        analytical_framework: str
    ) -> Dict[str, str]:
        """Call GPT-5 for editorial review."""
        self.logger.info(f"Calling GPT-5 (o1) for editorial review of Psalm {psalm_number}")

        # Format macro and micro for prompt
        macro_text = self._format_analysis_for_prompt(macro_analysis, "macro")
        micro_text = self._format_analysis_for_prompt(micro_analysis, "micro")

        # Build prompt
        prompt = MASTER_EDITOR_PROMPT.format(
            psalm_number=psalm_number,
            introduction_essay=introduction,
            verse_commentary=verse_commentary,
            research_bundle=research_bundle,
            psalm_text=psalm_text or "[Psalm text not available]",
            macro_analysis=macro_text,
            micro_analysis=micro_text,
            analytical_framework=analytical_framework
        )

        # Save prompt for debugging
        if self.logger:
            prompt_file = Path(f"output/debug/master_editor_prompt_psalm_{psalm_number}.txt")
            prompt_file.parent.mkdir(parents=True, exist_ok=True)
            prompt_file.write_text(prompt, encoding='utf-8')
            self.logger.info(f"Saved editorial prompt to {prompt_file}")

        # Call GPT-5 (o1)
        # Note: o1 uses different API parameters - no system messages, only user messages
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract response text
            response_text = response.choices[0].message.content

            self.logger.info(f"Editorial review generated: {len(response_text)} chars")

            # Parse response into sections
            result = self._parse_editorial_response(response_text, psalm_number)

            return result

        except Exception as e:
            self.logger.error(f"Error in editorial review: {e}")
            raise

    def _parse_editorial_response(self, response_text: str, psalm_number: int) -> Dict[str, str]:
        """Parse the GPT-5 response into structured sections."""
        # Find section markers
        assessment_marker = "### EDITORIAL ASSESSMENT"
        intro_marker = "### REVISED INTRODUCTION"
        verses_marker = "### REVISED VERSE COMMENTARY"

        # Default values
        assessment = ""
        revised_introduction = ""
        revised_verses = ""

        # Split by markers
        parts = response_text.split("###")

        for i, part in enumerate(parts):
            part = part.strip()

            if part.startswith("EDITORIAL ASSESSMENT"):
                # Extract assessment text (everything until next ### marker)
                assessment_text = part.replace("EDITORIAL ASSESSMENT", "", 1).strip()
                # Find where next section starts
                next_section_idx = assessment_text.find("REVISED INTRODUCTION")
                if next_section_idx > 0:
                    assessment = assessment_text[:next_section_idx].strip()
                else:
                    assessment = assessment_text.strip()

            elif part.startswith("REVISED INTRODUCTION"):
                intro_text = part.replace("REVISED INTRODUCTION", "", 1).strip()
                # Find where next section starts
                next_section_idx = intro_text.find("REVISED VERSE COMMENTARY")
                if next_section_idx > 0:
                    revised_introduction = intro_text[:next_section_idx].strip()
                else:
                    revised_introduction = intro_text.strip()

            elif part.startswith("REVISED VERSE COMMENTARY"):
                revised_verses = part.replace("REVISED VERSE COMMENTARY", "", 1).strip()

        return {
            'assessment': assessment,
            'revised_introduction': revised_introduction,
            'revised_verses': revised_verses,
            'psalm_number': psalm_number
        }

    def _get_psalm_text(self, psalm_number: int) -> str:
        """Retrieve psalm text from database."""
        try:
            from src.data_sources.tanakh_database import TanakhDatabase
            from src.agents.rag_manager import RAGManager

            db = TanakhDatabase(Path("database/tanakh.db"))
            rag = RAGManager("docs")

            psalm = db.get_psalm(psalm_number)
            rag_context = rag.get_rag_context(psalm_number)

            if not psalm:
                return "[Psalm text not available]"

            # Format with LXX
            lines = [f"# Psalm {psalm_number}\n"]

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
                lines.append(f"\n## Verse {v_num}")
                lines.append(f"**Hebrew:** {verse.hebrew}")
                lines.append(f"**English:** {verse.english}")
                if v_num in lxx_verses:
                    lines.append(f"**LXX (Greek):** {lxx_verses[v_num]}")

            return "\n".join(lines)

        except Exception as e:
            self.logger.warning(f"Could not retrieve psalm text: {e}")
            return "[Psalm text not available]"

    def _load_text_file(self, file_path: Path) -> str:
        """Load text file."""
        self.logger.info(f"Loading text file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _load_json_file(self, file_path: Path) -> Dict:
        """Load JSON file."""
        self.logger.info(f"Loading JSON file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _format_analysis_for_prompt(self, analysis: Dict, type: str) -> str:
        """
        Format analysis JSON for inclusion in prompt.

        Handles both Pydantic objects and dictionary formats.
        Extracts phonetic transcription data for micro analysis.
        """
        # Helper to get attribute/key value with fallback
        def get_value(obj, key, default=''):
            if hasattr(obj, key):
                return getattr(obj, key, default)
            elif isinstance(obj, dict):
                return obj.get(key, default)
            return default

        if type == "macro":
            lines = []
            lines.append(f"**Thesis**: {get_value(analysis, 'thesis_statement', 'N/A')}")
            lines.append(f"**Genre**: {get_value(analysis, 'genre', 'N/A')}")

            structure = get_value(analysis, 'structural_outline', [])
            if structure:
                lines.append("\n**Structure**:")
                for div in structure:
                    section = get_value(div, 'section', '')
                    theme = get_value(div, 'theme', '')
                    lines.append(f"  - {section}: {theme}")

            devices = get_value(analysis, 'poetic_devices', [])
            if devices:
                lines.append("\n**Poetic Devices**:")
                for device in devices:
                    device_name = get_value(device, 'device', '')
                    description = get_value(device, 'description', '')
                    lines.append(f"  - {device_name}: {description}")

            # Add research questions
            questions = get_value(analysis, 'research_questions', [])
            if questions:
                lines.append("\n**Research Questions** (from Macro Analyst):")
                for i, q in enumerate(questions, 1):
                    lines.append(f"  {i}. {q}")

            return "\n".join(lines)

        elif type == "micro":
            lines = []

            # Handle both Pydantic object and dict formats
            # Support both new format ('verse_commentaries') and old format ('verses')
            if hasattr(analysis, 'verse_commentaries'):
                # Pydantic MicroAnalysis object
                verses = analysis.verse_commentaries
            elif isinstance(analysis, dict):
                # Dictionary format
                verses = analysis.get('verse_commentaries', analysis.get('verses', []))
            else:
                verses = []

            for verse_data in verses[:5]:  # Sample first 5 verses for brevity
                # Get verse number (handle both field names)
                verse_num = get_value(verse_data, 'verse_number', get_value(verse_data, 'verse', 0))

                # Get commentary
                commentary = get_value(verse_data, 'commentary', '')

                # CRITICAL: Extract phonetic transcription data
                phonetic = get_value(verse_data, 'phonetic_transcription', '')

                # Format verse with phonetic data if available
                lines.append(f"**Verse {verse_num}**")
                if phonetic:
                    lines.append(f"**Phonetic**: `{phonetic}`")
                lines.append(commentary)
                lines.append("")

            if len(verses) > 5:
                lines.append(f"[... and {len(verses) - 5} more verses]")

            # Add interesting questions if present
            interesting_questions = get_value(analysis, 'interesting_questions', [])
            if interesting_questions:
                lines.append("")
                lines.append("**Interesting Questions** (from Micro Analyst):")
                for i, q in enumerate(interesting_questions, 1):
                    lines.append(f"  {i}. {q}")

            return "\n".join(lines)

        return json.dumps(analysis, ensure_ascii=False, indent=2)

    def edit_and_save(
        self,
        introduction_file: str,
        verse_file: str,
        research_file: str,
        macro_file: str,
        micro_file: str,
        output_dir: str = "output",
        output_name: Optional[str] = None,
        psalm_text_file: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Perform editorial review and save results.

        Args:
            introduction_file: Path to introduction essay
            verse_file: Path to verse commentary
            research_file: Path to research bundle
            macro_file: Path to macro analysis
            micro_file: Path to micro analysis
            output_dir: Directory to save output
            output_name: Base name for output files
            psalm_text_file: Optional path to psalm text

        Returns:
            Editorial result dictionary
        """
        # Perform editorial review
        result = self.edit_commentary(
            introduction_file=Path(introduction_file),
            verse_file=Path(verse_file),
            research_file=Path(research_file),
            macro_file=Path(macro_file),
            micro_file=Path(micro_file),
            psalm_text_file=Path(psalm_text_file) if psalm_text_file else None
        )

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Determine output name
        psalm_number = result['psalm_number']
        if not output_name:
            output_name = f"psalm_{psalm_number:03d}_edited"

        # Save assessment
        assessment_path = output_path / f"{output_name}_assessment.md"
        with open(assessment_path, 'w', encoding='utf-8') as f:
            f.write(f"# Editorial Assessment - Psalm {psalm_number}\n\n")
            f.write(result['assessment'])
        self.logger.info(f"Saved editorial assessment to {assessment_path}")

        # Save revised introduction
        intro_path = output_path / f"{output_name}_intro.md"
        with open(intro_path, 'w', encoding='utf-8') as f:
            f.write(result['revised_introduction'])
        self.logger.info(f"Saved revised introduction to {intro_path}")

        # Save revised verse commentary
        verses_path = output_path / f"{output_name}_verses.md"
        with open(verses_path, 'w', encoding='utf-8') as f:
            f.write(result['revised_verses'])
        self.logger.info(f"Saved revised verses to {verses_path}")

        # Save complete revised commentary
        complete_path = output_path / f"{output_name}.md"
        with open(complete_path, 'w', encoding='utf-8') as f:
            f.write(f"# Commentary on Psalm {psalm_number} (Master Edited)\n\n")
            f.write("## Introduction\n\n")
            f.write(result['revised_introduction'])
            f.write("\n\n---\n\n")
            f.write("## Verse-by-Verse Commentary\n\n")
            f.write(result['revised_verses'])
        self.logger.info(f"Saved complete revised commentary to {complete_path}")

        return result


def main():
    """Command-line interface for Master Editor."""
    import argparse

    # Ensure UTF-8 for Hebrew output on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Master Editor: Final editorial review with GPT-5 (Pass 4)'
    )
    parser.add_argument('--introduction', type=str, required=True,
                       help='Path to introduction essay file')
    parser.add_argument('--verses', type=str, required=True,
                       help='Path to verse commentary file')
    parser.add_argument('--research', type=str, required=True,
                       help='Path to research bundle file')
    parser.add_argument('--macro', type=str, required=True,
                       help='Path to macro analysis JSON')
    parser.add_argument('--micro', type=str, required=True,
                       help='Path to micro analysis JSON')
    parser.add_argument('--psalm-text', type=str, default=None,
                       help='Path to psalm text file (optional)')
    parser.add_argument('--output-dir', type=str, default='output',
                       help='Output directory (default: output)')
    parser.add_argument('--output-name', type=str, default=None,
                       help='Base name for output files')

    args = parser.parse_args()

    try:
        # Initialize editor
        editor = MasterEditor()

        print("=" * 80)
        print("MASTER EDITOR (Pass 4 - GPT-5)")
        print("=" * 80)
        print()
        print(f"Introduction:  {args.introduction}")
        print(f"Verses:        {args.verses}")
        print(f"Research:      {args.research}")
        print(f"Macro:         {args.macro}")
        print(f"Micro:         {args.micro}")
        print()
        print("Performing master editorial review...")
        print("This may take 2-5 minutes for GPT-5 to analyze and revise.")
        print()

        # Edit and save
        result = editor.edit_and_save(
            introduction_file=args.introduction,
            verse_file=args.verses,
            research_file=args.research,
            macro_file=args.macro,
            micro_file=args.micro,
            psalm_text_file=args.psalm_text,
            output_dir=args.output_dir,
            output_name=args.output_name
        )

        # Display preview
        print("=" * 80)
        print(f"MASTER EDITORIAL REVIEW COMPLETE: PSALM {result['psalm_number']}")
        print("=" * 80)
        print()
        print("EDITORIAL ASSESSMENT (preview):")
        print(result['assessment'][:400] + "...")
        print()
        print("=" * 80)
        print(f"Complete revised commentary saved to {args.output_dir}/")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
