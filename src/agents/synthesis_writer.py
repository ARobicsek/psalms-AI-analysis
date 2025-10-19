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
1. **IntroductionEssay** - The introductory essay already written for this psalm
2. **MacroAnalysis** - Overall thesis and structure
3. **MicroAnalysis** - Verse-by-verse discoveries
4. **ResearchBundle** - Lexical, concordance, and research materials

## YOUR INPUTS

### INTRODUCTION ESSAY (already written for this psalm)
{introduction_essay}

### MACRO THESIS
{macro_analysis}

### MICRO DISCOVERIES
{micro_analysis}

### RESEARCH MATERIALS
{research_bundle}

---

## YOUR TASK: WRITE VERSE-BY-VERSE COMMENTARY

For EACH verse in the psalm, write a commentary annotation that draws on diverse scholarly angles:

**LENGTH GUIDELINES:**
- **Target length**: 150-400 words per verse
- **Can be longer** (400+ words) if there's a genuinely interesting finding or insight that merits extended illumination
- Let the content determine the length - don't pad or artificially constrain

### ITEMS OF INTEREST TO ILLUMINATE (when relevant to the verse):

The following areas are of particular interest to intelligent, well-read lay readers who desire poetic, literary, linguistic, and historical insights:

1. **Poetics**
   - Parallelism types (synonymous, antithetical, synthetic, climactic)
   - Wordplay (paronomasia, alliteration, assonance)
   - Sound patterns and phonetic effects
   - Meter and rhythm
   - Structural devices (chiasm, inclusio, envelope structure)

2. **Literary Insights**
   - Narrative techniques and rhetorical strategies
   - Genre conventions and innovations
   - Dramatic progression and turning points
   - Imagery and its function
   - Irony, hyperbole, understatement

3. **Historical and Cultic Insights**
   - Liturgical setting and worship context
   - Historical period indicators (vocabulary, theology, cultural references)
   - Temple/sanctuary practices
   - Royal psalms and kingship theology
   - Festival associations (Sukkot, Passover, New Year, etc.)

4. **Comparative Religion**
   - Ancient Near Eastern parallels (Ugaritic, Akkadian, Egyptian)
   - Polemic against Canaanite/Mesopotamian religion
   - Appropriation and transformation of ANE motifs
   - Cite specific texts (KTU numbers, Enuma Elish, etc.)

5. **Grammar and Syntax** (when illuminating)
   - Rare or ambiguous grammatical forms
   - Verb tenses and aspect (especially jussive, cohortative, imperative)
   - Word order significance
   - Difficult constructions that affect meaning

6. **Textual Criticism**
   - Comparison of Masoretic Text (MT) vs Septuagint (LXX)
   - What LXX choices reveal about the Vorlage (Hebrew base text)
   - Textual variants and their implications
   - Translation challenges and scholarly debates

7. **Lexical Analysis**
   - Etymology when theologically illuminating
   - Semantic range of key terms (use BDB data)
   - Rare vocabulary and hapax legomena
   - Technical terminology (legal, cultic, military, agricultural)

8. **Comparative Biblical Usage**
   - Concordance insights: how this word/phrase appears elsewhere
   - Development of theological concepts across Scripture
   - Formulaic language and its variations
   - Quotation and allusion to other biblical texts

9. **Figurative Language**
   - How vehicles (metaphors, similes) function in this verse
   - How the same figurative vehicles are used across Scripture
   - Target-vehicle-ground-posture analysis
   - Evolution of metaphorical meaning

10. **Timing/Composition Clues**
    - Vocabulary that suggests dating (Persian loanwords, Aramaisms, etc.)
    - Theological development indicators
    - Historical allusions (Babylonian exile, monarchy, etc.)
    - Liturgical evolution markers

11. **Traditional Interpretation**
    - Classical Jewish commentary (Rashi, Ibn Ezra, Radak, Kimchi)
    - Targum renderings
    - Church fathers (Augustine, Jerome, etc.)
    - Medieval Christian interpretation
    - Modern critical scholarship debates

### IMPORTANT NOTES:

- **Relationship to Introduction Essay**: You have the complete introduction essay. Your verse commentary should COMPLEMENT (not repeat) the introduction. If the introduction discussed a theme at length, you can allude to it briefly but focus on verse-specific details not covered in the introduction.
- **Independence from macro thesis**: The verse commentary need NOT always relate to the macro thesis - follow what's interesting in each verse
- **Reader interest**: Focus on what would genuinely interest and inform an intelligent, well-read lay reader who desires poetic, literary, linguistic, and historical insights
- **Flexibility**: Some verses may focus on poetics, others on Vorlage, others on Ugaritic parallels, others on figurative language patterns - let the verse and research materials guide you
- **Depth over breadth**: Better to explore 2-3 angles deeply than mention everything superficially
- **Evidence-based**: Ground all observations in the research materials provided (BDB, concordances, figurative language database, traditional commentaries)
- **Use research bundle effectively**: The research bundle contains:
  * BDB lexicon entries with semantic ranges, etymologies, and usage patterns
  * Concordance data showing where Hebrew terms appear elsewhere in Scripture - cite these parallels!
  * Figurative language instances showing how vehicles/metaphors are used across the Bible
  * Traditional commentary excerpts from Rashi, Ibn Ezra, Radak - engage with these interpretive traditions!
  * LXX text showing ancient Greek interpretation
- **Define technical terms**: When using jargon (jussive, anaphora, chiasm, inclusio, polemic, theophany, etc.), provide brief, accessible definitions for lay readers
- **Vary your approach**: Don't use the same scholarly angles for every verse - alternate between poetics, historical context, textual criticism, figurative analysis, etc.

### FORMAT FOR EACH VERSE:

**Verse [N]**
[150-300 words of commentary drawing on relevant scholarly angles]

---

## CRITICAL REQUIREMENTS

- **Cover ALL verses** in the psalm
- **Length**: 150-400 words per verse (can be longer if there's genuinely interesting material to illuminate)
- **Variety**: Don't use the same angles for every verse - vary your approach across poetics, textual criticism, figurative language, historical context, etc.
- **Evidence**: Cite Hebrew terms, concordance patterns, research findings, traditional commentators
- **Readability**: Scholarly but accessible for intelligent lay readers (New Yorker/Atlantic level)
- **Define terms**: Explain technical terminology when used
- **Independence**: Don't force connections to the macro thesis if they're not natural - follow what's interesting in each verse

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

        # Step 3: Generate verse commentary (now with access to introduction)
        verse_commentary = self._generate_verse_commentary(
            psalm_number=psalm_number,
            macro_analysis=macro_analysis,
            micro_analysis=micro_analysis,
            research_bundle=research_bundle,
            max_tokens=max_tokens_verse,
            introduction_essay=introduction  # Pass the introduction to verse commentary
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

    def _trim_figurative_proportionally(self, figurative_section: str, keep_ratio: float) -> str:
        """
        Trim figurative language section proportionally across all queries.

        Instead of cutting off entire queries, this keeps a percentage of results
        from each query, ensuring all search terms are represented.

        Args:
            figurative_section: The full figurative language section
            keep_ratio: Proportion to keep (0.0 to 1.0)

        Returns:
            Trimmed figurative section with proportional representation
        """
        import re

        # Split into individual query blocks (### Query N)
        query_pattern = r'(### Query \d+.*?)(?=### Query \d+|$)'
        queries = re.findall(query_pattern, figurative_section, re.DOTALL)

        if not queries:
            # Fallback: simple truncation
            target_size = int(len(figurative_section) * keep_ratio)
            return figurative_section[:target_size] + f"\n\n[Trimmed {len(figurative_section) - target_size} chars]"

        trimmed_queries = []
        total_trimmed = 0
        total_original = 0

        for query_block in queries:
            total_original += len(query_block)

            # Extract query header (first few lines before #### Instances:)
            match = re.match(r'(.*?#### Instances:)(.*)', query_block, re.DOTALL)
            if not match:
                # No instances found, keep header only
                trimmed_queries.append(query_block)
                continue

            header = match.group(1)
            instances_text = match.group(2)

            # Split instances by verse markers (**Verse** or similar)
            instance_pattern = r'(\*\*[^*]+\*\*.*?)(?=\*\*[^*]+\*\*|$)'
            instances = re.findall(instance_pattern, instances_text, re.DOTALL)

            if not instances:
                # No clear instances, keep as-is
                trimmed_queries.append(query_block)
                continue

            # Keep proportional number of instances
            keep_count = max(1, int(len(instances) * keep_ratio))  # Keep at least 1
            kept_instances = instances[:keep_count]
            omitted_count = len(instances) - keep_count

            # Reassemble
            trimmed_block = header + '\n' + ''.join(kept_instances)
            if omitted_count > 0:
                trimmed_block += f"\n\n[{omitted_count} more instances omitted for space]\n"

            trimmed_queries.append(trimmed_block)
            total_trimmed += len(trimmed_block)

        result = '## Figurative Language Instances\n\n' + '\n'.join(trimmed_queries)

        self.logger.info(f"Proportional trim: {total_original:,} → {total_trimmed:,} chars ({keep_ratio:.1%} kept)")
        return result

    def _trim_research_bundle(self, research_bundle: str, max_chars: int = 250000) -> str:
        """
        Intelligently trim research bundle to fit within token limits.

        Priority order:
        1. Keep all lexicon entries (most important for word analysis)
        2. Keep all figurative language examples (critical for literary analysis)
        3. Keep all commentary entries (provides interpretive context)
        4. Trim concordance results (least critical - shows usage patterns)

        Args:
            research_bundle: Full research bundle markdown
            max_chars: Maximum characters (~125k tokens with 2 chars/token ratio)

        Returns:
            Trimmed research bundle
        """
        if len(research_bundle) <= max_chars:
            return research_bundle

        self.logger.warning(f"Research bundle too large ({len(research_bundle)} chars). Trimming to {max_chars} chars...")

        # Split into sections
        sections = research_bundle.split('\n## ')
        header = sections[0] if sections else ""

        # Find and separate sections
        lexicon_section = ""
        figurative_section = ""
        commentary_section = ""
        concordance_section = ""

        for section in sections[1:]:
            section_name = section.split('\n')[0] if section else ''
            if 'Lexicon Entries' in section_name:  # Match "Hebrew Lexicon Entries" or "BDB Lexicon Entries"
                lexicon_section = '## ' + section
            elif section_name.startswith('Figurative Language Instances'):
                figurative_section = '## ' + section
            elif 'Commentaries' in section_name or 'Commentary' in section_name:  # Match "Traditional Commentaries" or "Sefaria Commentary"
                commentary_section = '## ' + section
            elif 'Concordance' in section_name:  # Match "Concordance Searches" or "Concordance Results"
                concordance_section = '## ' + section

        # Calculate sizes
        header_size = len(header)
        lexicon_size = len(lexicon_section)
        figurative_size = len(figurative_section)
        commentary_size = len(commentary_section)
        concordance_size = len(concordance_section)

        # Try to keep everything, trim concordance first, then figurative if needed
        available_for_concordance = max_chars - (header_size + lexicon_size + figurative_size + commentary_size)

        if available_for_concordance < 0:
            # Even without concordance we're over limit - need to trim figurative too
            self.logger.warning(f"Research bundle exceeds limit even without concordance. Trimming figurative language proportionally.")
            # Calculate how much figurative we can keep
            available_for_figurative = max_chars - (header_size + lexicon_size + commentary_size + 1000)  # Leave 1k for concordance header
            if available_for_figurative > 0 and figurative_size > 0:
                trim_ratio = available_for_figurative / figurative_size
                self.logger.info(f"Trimming figurative proportionally: keeping {trim_ratio:.1%} of each query's results")
                figurative_section = self._trim_figurative_proportionally(figurative_section, trim_ratio)
            else:
                figurative_section = ""
            # Drop concordance entirely
            concordance_section = ""
        elif available_for_concordance < concordance_size:
            # Trim concordance section
            self.logger.info(f"Trimming concordance from {concordance_size} to {available_for_concordance} chars")
            concordance_lines = concordance_section.split('\n')
            trimmed_concordance = []
            current_size = 0
            for line in concordance_lines:
                if current_size + len(line) + 1 <= available_for_concordance:
                    trimmed_concordance.append(line)
                    current_size += len(line) + 1
                else:
                    trimmed_concordance.append(f"\n[Concordance results trimmed for context length. {concordance_size - current_size} chars omitted.]")
                    break
            concordance_section = '\n'.join(trimmed_concordance)

        # Reassemble
        result = '\n\n'.join(filter(None, [
            header,
            lexicon_section,
            concordance_section,
            figurative_section,
            commentary_section
        ]))

        self.logger.info(f"Research bundle trimmed: {len(research_bundle)} → {len(result)} chars")
        return result

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

        # Trim research bundle if needed to fit within 200K token limit
        # Target: ~330K chars max (~165K tokens with 2:1 ratio)
        # Conservative: 90% of theoretical max (340k) to leave safety margin
        research_text = self._trim_research_bundle(research_bundle, max_chars=330000)

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
            # Save full prompt to file for inspection
            prompt_file = Path(f"output/debug/intro_prompt_psalm_{psalm_number}.txt")
            prompt_file.parent.mkdir(parents=True, exist_ok=True)
            prompt_file.write_text(prompt, encoding='utf-8')
            self.logger.info(f"Saved introduction prompt to {prompt_file}")

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
        max_tokens: int,
        introduction_essay: str = ""
    ) -> str:
        """Generate verse-by-verse commentary."""
        self.logger.info(f"Generating verse commentary for Psalm {psalm_number}")

        # Format inputs
        macro_text = self._format_macro_for_prompt(macro_analysis)
        micro_text = self._format_micro_for_prompt(micro_analysis)

        # Trim research bundle if needed - verse commentary includes introduction essay
        # so needs more aggressive trimming than intro generation
        # Target: ~320K chars max (~160K tokens)
        # Conservative: 90% of theoretical max (334k) to leave safety margin for intro essay
        research_text = self._trim_research_bundle(research_bundle, max_chars=320000)

        # Build prompt
        prompt = VERSE_COMMENTARY_PROMPT.format(
            psalm_number=psalm_number,
            introduction_essay=introduction_essay,
            macro_analysis=macro_text,
            micro_analysis=micro_text,
            research_bundle=research_text
        )

        # Log prompt for debugging
        if self.logger:
            self.logger.debug(f"Verse commentary prompt length: {len(prompt)} chars")
            # Save full prompt to file for inspection
            prompt_file = Path(f"output/debug/verse_prompt_psalm_{psalm_number}.txt")
            prompt_file.parent.mkdir(parents=True, exist_ok=True)
            prompt_file.write_text(prompt, encoding='utf-8')
            self.logger.info(f"Saved verse commentary prompt to {prompt_file}")

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

        # Add research questions
        questions = macro.get('research_questions', [])
        if questions:
            lines.append("")
            lines.append("**Research Questions** (from Macro Analyst):")
            for i, q in enumerate(questions, 1):
                lines.append(f"  {i}. {q}")

        return "\n".join(lines)

    def _format_micro_for_prompt(self, micro: Dict) -> str:
        """Format MicroAnalysis for prompt."""
        lines = []

        # Handle both old format ('verses') and new format ('verse_commentaries')
        verses = micro.get('verse_commentaries', micro.get('verses', []))

        for verse_data in verses:
            verse_num = verse_data.get('verse_number', verse_data.get('verse', 0))
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

        # Add thematic threads if present
        threads = micro.get('thematic_threads', [])
        if threads:
            lines.append("**Thematic Threads Across Verses:**")
            for thread in threads:
                lines.append(f"  - {thread}")
            lines.append("")

        # Add synthesis notes if present
        synth_notes = micro.get('synthesis_notes', '')
        if synth_notes:
            lines.append("**Synthesis Notes for Research:**")
            lines.append(synth_notes)

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
