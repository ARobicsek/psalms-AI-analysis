"""
Master Editor Agent (Pass 4 - Final Review & Enhancement)

This agent uses GPT-5 to provide final editorial review and enhancement of the
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

Model: GPT-5
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
from datetime import datetime
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
You are writing for a sophisticated lay audience, such as the readers of *The New Yorker* or *The Atlantic*. **Imagine your reader is a highly intelligent, curious person who is not a biblical scholar, a linguist, or an academic.** Your primary goal is to make complex ideas clear and fascinating. Your prose must be scholarly, lucid, and engaging. Your tone is one of measured confidence, not breathless praise. 
**Your erudition should be demonstrated by your original ideas and your ability to make difficult concepts accessible, not by using jargon.**

## YOUR INPUTS

### PSALM TEXT (Hebrew, English, LXX, and Phonetic)
{psalm_text}

### INTRODUCTION ESSAY (for review)
{introduction_essay}

### VERSE-BY-VERSE COMMENTARY (for review)
{verse_commentary}

### FULL RESEARCH BUNDLE
{research_bundle}

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
- Interesting insights from the Torah Temimah (re rabbinic use/interpretation) not included
- Illuminating traditional commentary (Rashi, Ibn Ezra, Radak, Meiri, Metzudat David, Malbim) not integrated
- Research questions identified by Macro and Micro analysts not answered (even when answerable with available materials)
- **Liturgical context not addressed**: The research bundle includes detailed information about where and how this psalm (or specific verses/phrases from it) appears in Jewish liturgy. This liturgical usage reveals how Jewish tradition has interpreted and valued the psalm and should be integrated naturally into the commentary
- Weak, forced, unclear or incorrect phonetic analysis. ONLY NOTEWORTHY, STRONG and ILLUMINATING phonetic poetic devices should be pointed out (e.g. alliteration, assonance, onomatopoeia, rhyme, rhythm, meter).
- Authorotative Phonetic transcription provided above in ### PSALM TEXT MUST BE USED to analyze sound patterns.
- Stress analysis ignored: The phonetic transcriptions include stress marking where syllables in **BOLD CAPS** indicate stressed syllables based on Hebrew cantillation marks. For example, `mal-**KHŪTH**-khā` means the middle syllable KHŪTH receives primary stress. If you wish to analyze prosodic patterns, meter, or stress counts, you should add this analysis by counting the **BOLD CAPS** syllables.
- IRRELEVANT phonetic transcriptions. ONLY provide phonetic transcriptions where the pronunciation specifically illustrates the point you are making. Otherwise, just proivide the relevant Hebrew with English translation (not transcriptions). Example of RELEVANT transcription:"The triple anaphora לֹא (LŌ’) … לֹא … לֹא gives the line its pulse; read aloud, the negatives strike like posts in a fence...". Example of IRRELEVANT transcription: "The wicked “will not stand” (לֹא־יָקֻמוּ, lō’-yā-QU-mū) in the judgment..."
- Comparative textual insights (e.g. MT vs LXX) not addressed
- NOTEWORTHY poetic devices (e.g. assonance, chiasm, inclusio, parallelism) not described
- Unusual or interesting Hebrew phrases not commented on (e.g., distinctive idioms, unusual word pairings like הֲ֭דַר כְּב֣וֹד הוֹדֶ֑ךָ or עֱז֣וּז נֽוֹרְאֹתֶ֣יךָ)
- Interesting lexical insights in BDB not surfaced
- Concordance patterns not explored
- Figurative language not analyzed
- Figurative language parallels from database not cited or analyzed
- ANE parallels available but not discussed

### 3. STYLISTIC PROBLEMS
**Too "LLM-ish" or breathless:**
- Overuse of words like: "masterpiece," "tour de force," "breathtaking," "audacious," "remarkable," "stunning"
- Telling instead of showing (saying "brilliant" instead of demonstrating brilliance through analysis)
**Too academic or "insider" in tone:**
- **Avoid overly technical grammatical phrasing.** Instead of "the perfects are used," prefer "the poet uses the perfect verb tense to convey..." This helps the reader understand you're talking about a verb form without needing prior grammatical knowledge.
- **Translate academic jargon into plain English.** 
- AVOID opaque or overly academic terms where there are other terms that would work just as well (e.g. avoid phrases LIKE "biblical topos," "programmatic exemplar").
- **Clarity is paramount.** If a sentence feels like it was written for a dissertation defense, rewrite it for a coffee shop conversation with a clever friend.
- AVOID Unnecessarily complex sentence structures that obscure rather than illuminate

**Markup for Phonetic transcription (i.e. transliteration)**:
- **too many phonetic transcriptions clutter the prose. ONLY use transcriptions when the reader NEEDS to know how something was pronounced in order to understand your point about a poetic device. Do NOT transliterate words where the pronunciation does not pertain to the point you are making.** On the other hand, DO always provide the relevant text/words in Hebrew with English TRANSLATION.
- When you use a phonetically transcribed Hebrew word or phrase in your prose, **you MUST include the Hebrew text alongside the phonetic transcription** in the format: Hebrew (phonetic transcription). For example: "The opening line, אַשְׁרֵי־הָאִישׁ (`'ash-rēy-hā-'IY-sh`).
- **You MUST enclose the phonetic transcription in backticks**. This is how the document generator will identify it for italicization.
- When you use a phonetically transcribed Hebrew word or phrase in your prose, **you MUST use the phonetic transcription from the PSALM TEXT section above EXCEPT for the tetragrammaton, which you should render as YHWH**. This ensures consistency and accuracy in pronunciation guidance for readers.
- ALWAYS provide the Hebrew text before the transcription. Do NOT use standalone transcriptions without Hebrew.
  * CORRECT: "The verb יֶהְגֶּה (`yeh-GEH`) is onomotopoeic, evoking a murmuring sound..."
  * INCORRECT: "The verb `yeh-GEH` is onomotopoeic..."

**Should conform to this style:**
- Measured, confident tone (like a distinguished professor)
- Show brilliance through analysis, don't label it
- Use strong verbs and concrete imagery
- Vary sentence structure for readability
- Explain technical terms when needed (e.g., "jussive," "anaphora," "chiasm," "inclusio")
- Elegant, uncluttered prose for sophisticated lay readers (New Yorker/Atlantic level)
- AVOID pompous tone and fancy terms that signal you're a professor; prove your erudition through the incisive and original quality of your insights and your lapidary prose.

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
**This is a critical failure. Every technical term MUST be defined.** The definition can be 
- a brief parenthetical note,
- woven directly into the sentence,
- or included as a short explanation at the end of the introductory essay or verse commentary.
EXAMPLES OF TERMS THAT MUST BE DEFINED:
- **Literary & Rhetorical Terms:** "jussive", "anaphora", "chiasm", "inclusio", **"colon"** (a single line of poetry in a parallel pair), "Vorlage", hendiadys, doxology,etc.
- **Hebrew Grammatical Terms:** **"intensive stem (Pi'el)"** (a verb form often indicating intensified action), **"Hithpolel"** (a reflexive verb form), etc. Explain what the form *does* functionally.
- **Scholarly Shorthand:** **"BDB"** (the Brown-Driver-Briggs Hebrew and English Lexicon, a standard scholarly dictionary that includes...), "LXX" (the Septuagint, an ancient Greek translation of the Hebrew Bible that sometimes differs from the Masoretic Texts in ways that can reveal...), "MT" (the Masoretic Text, the standard Hebrew version known through...), "11QPsa" (the Psalm scroll from Qumran Cave 11, which contains variant readings that shed light on...)
- **General Academic Terms or terms related to the Ancient Near East:** Any word not in common general lay usage must be clarified (including "ANE").

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

**Stage 2: Revised Introduction (TWO SECTIONS REQUIRED)**
Rewrite the introduction to address identified weaknesses. The revised introduction must include TWO sections:

**Section 1: Introduction Essay**
- Maintain 800-1600 words (can be longer if genuinely warranted by interesting findings and/or length of the psalm)
- Correct any factual errors
- Surface missed insights from research materials, especially the Torah Temimah and traditional commentaries
- Address answerable questions raised by the Macro and Micro analysts (weave answers into the essay where appropriate)
- Integrate liturgical insights naturally where relevant (don't treat liturgy as separate topic)
- Achieve the target style (Alter/Kugel/Bloom level)
- Define technical terms for lay readers
- Engage specific texts (Hebrew, LXX) with analysis

**Section 2: Modern Jewish Liturgical Use (REQUIRED)**
The draft you're reviewing ALREADY contains a "## Modern Jewish Liturgical Use" section. Your job is to REVISE and IMPROVE it, NOT to skip it or output just a header.

**MANDATORY ACTIONS:**
1. **Review the existing liturgical section** in the draft introduction
2. **Cross-reference with research bundle** to verify accuracy and add missing details
3. **Restructure into clear subsections** (use #### for Heading 4):
   * #### Full psalm - Where/when the complete psalm is recited (if applicable)
   * #### Key verses - Each verse used in liturgy, starting with Hebrew + English, then explaining context with Hebrew from the prayers
   * #### Phrases - Each phrase used in liturgy, starting with Hebrew + English, then explaining context with Hebrew from the prayers
4. **OMIT subsections that don't apply** to this psalm
5. **Add Hebrew quotations** - for EVERY verse/phrase, include Hebrew from both the psalm AND the prayer
6. **Be specific** - name the service, occasion, tradition
7. **Explain significance** - why this usage matters theologically, or is relevant to our understanding of the psalm, or reflects something interesting about how the psalm was received, understood, appropriated or reinterpreted by the tradition.

**Target: 200-500 words** (longer if extensive usage)

**⚠️ CRITICAL: Output the COMPLETE revised section with REAL CONTENT. Writing just "## Modern Jewish Liturgical Use" with nothing after it is UNACCEPTABLE and will fail validation.**

**Stage 3: Revised Verse Commentary**
Rewrite the verse-by-verse commentary to address identified weaknesses. For each verse:

- **Audience Hebrew Proficiency**: Your readers are familiar with biblical and rabbinic Hebrew. When you quote sources (biblical texts, rabbinic sources, liturgical texts), provide the Hebrew original AS WELL AS the English translation. Include enough Hebrew to support your point and/or demonstrate things of interest (unusual constructions, wordplay, idioms, etc.). Don't rely solely on translation—let readers see the Hebrew evidence for themselves. NOTE: The verse text in Hebrew will be programmatically inserted before your commentary, so you do NOT need to include it yourself.

- **Length**: Target 300-500 words per verse. Shorter (200-250 words) is acceptable for simple verses with minimal interesting features. Longer (500-800 words) is ENCOURAGED and often NECESSARY for verses with:
  * Unusual Hebrew phrases or idioms (like הֲ֭דַר כְּב֣וֹד הוֹדֶ֑ךָ or עֱז֣וּז נֽוֹרְאֹתֶ֣יךָ)
  * Complex poetic devices (chiasm, inclusio, intricate parallelism)
  * Significant textual variants (MT vs LXX differences)
  * Important interpretive questions that can be answered with research materials
  * Examples of use of the text by aggadic or halachic traditions (see the Torah Temimah); powerful insights into early rabbinic reception and interpretation
  * Rich figurative language requiring comparative analysis

  Remember: intelligent lay readers are HUNGRY for substantive analysis of linguistic and literary features. Don't shortchange them!

- **Scholarly Grounding**: Your analysis must be grounded in the provided research bundle and demonstrate awareness of the principles in the **ANALYTICAL FRAMEWORK** document. Use its terminology (e.g., "telescopic analysis," "A is so, and what's more, B") where appropriate to frame your insights.

- **Discretion**: You have full editorial discretion. You are not required to include every detail from the synthesizer's commentary. Your role is to *evaluate* the synthesizer's choices regarding phonetic and figurative language, and then decide whether to retain, enhance, rewrite, or replace them to achieve the highest level of scholarly excellence.

- **Items of interest to include** (when relevant):
  **Interpretation and Reception**, including
    - *Influence of verses and their use in aggada and halacha by the Mishna, Talmud, Midrashim, etc as provided in the Torah Temimah* - make sure to carefully review the Torah Temimah material in the research bundle
    - *Medieval Jewish commentary (Rashi, Ibn Ezra, Radak)*
    - *Jewish commentaries of the modern era (Metzudat David, Malbim, Meiri)*
    - **Modern liturgical context (IMPORTANT)**: When a verse (or phrase from it) appears in Jewish liturgy, comment on this usage and what it reveals about reception and interpretation/re-interpretation. Be specific about the prayer name, service, occasion, and tradition. Integrate liturgical insights naturally.
    - Church fathers and medieval Christian interpretation if very illuminating
    - Modern critical scholarship debates
  * Figurative language analysis (how does the usage of similar figuration elsewhere shed light on how it's functioning here?)
  * Poetics (parallelism, wordplay, structure, clever devices, sound patterns (USE the authoritative phonetic information you are provided above to conduct this analysis))
  * **Unusual turns of phrase**: When a verse contains an interesting or unusual Hebrew phrase, idiom, or construction (like הֲ֭דַר כְּב֣וֹד הוֹדֶ֑ךָ or עֱז֣וּז נֽוֹרְאֹתֶ֣יךָ), comment on it—explain what makes it distinctive, how it functions poetically, and what it contributes to the verse's meaning
  * Literary insights (narrative techniques, rhetorical strategies)
  * Historical and cultic insights (worship setting, historical context)
  * Comparative religion (ANE parallels, theological contrasts)
  * Grammar and syntax (especially when illuminating)
  * Textual criticism (MT vs LXX, hints about Vorlage)
  * Comparative biblical usage (concordance insights showing how terms/phrases appear elsewhere)
  * Timing/composition clues (vocabulary, theology, historical references)

**Figurative Language Integration:**
For verses with figurative language where research provided biblical parallels:
- MUST cite at least one specific biblical parallel from the database (book:chapter:verse)
- MUST analyze the usage pattern (frequency, typical contexts)
- MUST note how this psalm's use compares to typical usage
- SHOULD provide insight beyond generic observation. Why was THIS figuration chosen by the poet? What can we learn about its senses from how it's used elsewhere? Think deeply and carefully about this!

Example of GOOD: "“He shall be like a tree transplanted by channels of water” (v. 3). The participle shathul is precise; BDB glosses it “transplanted,” a term elsewhere used of vines or trees set in a chosen place (Jeremiah 17:8; Ezekiel 17:22–23; 19:10). The site is not random: palgei mayim are divided channels, irrigation runnels, rather than a single stream. This is cultivation as much as nature."

Example of BAD: "Verse 16 speaks of God opening his hand. This imagery appears elsewhere in Scripture." (too vague, no specific citations, no pattern analysis, no INSIGHT)

- **Address interesting questions**: When relevant to specific verses, address answerable questions raised by the Macro and Micro analysts
- **Complement the introduction**: Don't repeat what the introduction covered in depth; add verse-specific detail
- **Correct style**: Avoid breathless LLM language; show rather than tell
- **Define terms and ensure accesibility**: Scrupulously apply the rules from criteria #4 (Stypistic Problems) and #6 (Undefined Technical Terms). Rewrite any sentence that sounds like it belongs in an academic journal. And ensure all technical terms have a definition in-line or after the commentary.
- **Emphasize the interesting**: Make sure to comment on unusual turns of phrase, distinctive Hebrew idioms, and poetic devices. These linguistic and literary features are precisely what intelligent lay readers find fascinating.
- **REMEMBER**: Very curious intelligent readers are depending on you to be their guide through this compelling, mysterious and enduring text that has been studied and recited with fervor for millenia. Give them new insights and deeply enhance their encounter with this work.
- **REMEMBER**: You have deep access to resources that NO scholar has had complete access to before. Use this to your advantage to produce truly outstanding commentary.

---

## CRITICAL REQUIREMENT: LITURGICAL SUMMARY

**⚠️ MANDATORY: You MUST write a complete `## Modern Jewish Liturgical Use` section with actual content.**

This is NOT optional. This is NOT a placeholder. You MUST:
1. **Find the liturgical data** in the research bundle (look for sections titled "Modern Jewish Liturgical Use (Psalm N)" or "Phrase-Level Liturgical Usage")
2. **Write actual content** - the section cannot be empty or contain only the header
3. **Use the proper structure**:
   - Include subsections (#### Full psalm, #### Key verses, #### Phrases) as appropriate for THIS psalm
   - OMIT subsections that don't apply to this specific psalm
   - For verses and phrases, ALWAYS start with Hebrew text + English translation
   - Include Hebrew quotations from the prayers themselves to illustrate usage
   - for individual verses and phrases that appear in the liturgy, reflect on whether their liturgical use goes with the grain of its natural ("pshat") reading or whether the compilers of the liturgy have put this verse or phrase to use in a novel way.
   - Be specific about occasions, services, and traditions
4. **Target 150-400 words** (can be longer if the psalm has extensive liturgical use)

**Your output will fail validation if this section is empty or missing.**
---

## OUTPUT FORMAT

Return your response with these THREE sections in order:

### EDITORIAL ASSESSMENT

Write your 200-400 word critical analysis of the current draft.

### REVISED INTRODUCTION

Your revised introduction must have TWO parts (do NOT label them with "PART 1" or "PART 2" - just write the content):

First, write the revised introduction essay (600-1200 words) incorporating improvements from your assessment. Begin directly with the essay content.

Second, IMMEDIATELY after finishing the essay, add a blank line and write this EXACT TEXT as a marker:

---LITURGICAL-SECTION-START---

Then continue with 2-4 substantial paragraphs (200-500 words) about liturgical usage:
- Full psalm recitation (if applicable) - where, when, which traditions
- Key verses in prayers (if applicable) - for EACH: Hebrew text, English, prayer name, service, occasion, Hebrew quote from the prayer
- Phrases in prayers (if applicable) - same format as verses

Use BOTH the existing liturgical content in the draft introduction AND the detailed liturgical data in the research bundle.

Write actual content with specific prayer names, services, and Hebrew quotations.

### REVISED VERSE COMMENTARY

**Verse 1**

[Your revised commentary for verse 1. NOTE: The Hebrew verse text will be programmatically inserted before your commentary. TARGET: 300-500 words. Do NOT shortchange the reader—intelligent lay readers want substantive analysis of linguistic and literary features. Aim for 400-500 words when the verse has interesting Hebrew phrases, poetic devices, figurative language, or interpretive questions. Only use 200-300 words for genuinely simple verses.]

**Verse 2**

[Your revised commentary for verse 2. TARGET: 300-500 words as above.]

[Continue for all verses...]

---

## CRITICAL REQUIREMENTS

- **Authority**: You are the final editorial voice - make bold revisions where needed
- **Scholarship**: Ground all claims in the research materials provided
- **Accessibility**: Write for intelligent lay readers (New Yorker/Atlantic audience)
- **Style**: Measured confidence, not breathless praise; show, don't tell
- **Completeness**: Cover all verses, define technical terms, engage specific texts
- **Excellence**: Elevate from "good" to "National Book Award" level
- **Length**: Aim for 400-500 words per verse when there are interesting features to analyze. Do not be terse when the verse warrants substantive treatment.

Begin your editorial review and revision below.
"""


class MasterEditor:
    """
    Pass 4: Master Editor Agent using GPT-5.

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
            psalm_text = self._get_psalm_text(psalm_number, micro_analysis)

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
        self.logger.info(f"Calling GPT-5 for editorial review of Psalm {psalm_number}")

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

        # Call GPT-5
        # Note: GPT-5 uses different API parameters - no system messages, only user messages
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

            # Save response for debugging
            if self.logger:
                response_file = Path(f"output/debug/master_editor_response_psalm_{psalm_number}.txt")
                response_file.parent.mkdir(parents=True, exist_ok=True)
                response_file.write_text(response_text, encoding='utf-8')
                self.logger.info(f"Saved editorial response to {response_file}")

            # Parse response into sections
            result = self._parse_editorial_response(response_text, psalm_number)

            return result
        
        except openai.RateLimitError as e:
            self.logger.error(f"OpenAI API quota exceeded: {e}. Please check your plan and billing details.")
            raise  # Re-raise the exception to be handled by the pipeline
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during editorial review: {e}")
            raise

    def _parse_editorial_response(self, response_text: str, psalm_number: int) -> Dict[str, str]:
        """Parse the GPT-5 response into structured sections."""
        import re

        # Find section markers using regex to match only at line start with exact pattern
        assessment_marker = "### EDITORIAL ASSESSMENT"
        intro_marker = "### REVISED INTRODUCTION"
        verses_marker = "### REVISED VERSE COMMENTARY"

        # Default values
        assessment = ""
        revised_introduction = ""
        revised_verses = ""

        # Find section positions
        assessment_match = re.search(r'^### EDITORIAL ASSESSMENT\s*$', response_text, re.MULTILINE)
        intro_match = re.search(r'^### REVISED INTRODUCTION\s*$', response_text, re.MULTILINE)
        verses_match = re.search(r'^### REVISED VERSE COMMENTARY\s*$', response_text, re.MULTILINE)

        # Extract assessment (from EDITORIAL ASSESSMENT to REVISED INTRODUCTION)
        if assessment_match and intro_match:
            assessment = response_text[assessment_match.end():intro_match.start()].strip()
        elif assessment_match:
            assessment = response_text[assessment_match.end():].strip()

        # Extract introduction (from REVISED INTRODUCTION to REVISED VERSE COMMENTARY)
        if intro_match and verses_match:
            revised_introduction = response_text[intro_match.end():verses_match.start()].strip()
        elif intro_match:
            revised_introduction = response_text[intro_match.end():].strip()

        # Extract verse commentary (from REVISED VERSE COMMENTARY to end)
        if verses_match:
            revised_verses = response_text[verses_match.end():].strip()

        # Replace the liturgical marker with proper markdown header
        if "---LITURGICAL-SECTION-START---" in revised_introduction:
            revised_introduction = revised_introduction.replace(
                "---LITURGICAL-SECTION-START---",
                "## Modern Jewish Liturgical Use"
            )
            self.logger.info("✓ Liturgical section marker found and replaced with header")

            # Validate that there's content after the header
            liturgical_idx = revised_introduction.find("## Modern Jewish Liturgical Use")
            content_after_header = revised_introduction[liturgical_idx + len("## Modern Jewish Liturgical Use"):].strip()

            if len(content_after_header) < 100:
                self.logger.warning(
                    f"⚠️  WARNING: Liturgical section appears very short ({len(content_after_header)} chars)"
                )
            else:
                self.logger.info(f"✓ Liturgical section has {len(content_after_header)} chars of content")
        else:
            self.logger.warning("⚠️  WARNING: Liturgical section marker not found in revised introduction!")

        return {
            'assessment': assessment,
            'revised_introduction': revised_introduction,
            'revised_verses': revised_verses,
            'psalm_number': psalm_number
        }

    def _get_psalm_text(self, psalm_number: int, micro_analysis: Optional[Dict] = None) -> str:
        """Retrieve psalm text from database and include phonetics."""
        try:
            from src.data_sources.tanakh_database import TanakhDatabase
            from src.agents.rag_manager import RAGManager

            db = TanakhDatabase(Path("database/tanakh.db"))
            rag = RAGManager("docs")

            psalm = db.get_psalm(psalm_number)
            rag_context = rag.get_rag_context(psalm_number)

            if not psalm:
                return "[Psalm text not available]"

            # Extract phonetic data from micro_analysis
            phonetic_data = {}
            if micro_analysis:
                verses_data = micro_analysis.get('verse_commentaries', micro_analysis.get('verses', []))
                for verse_data in verses_data:
                    verse_num = verse_data.get('verse_number', verse_data.get('verse', 0))
                    phonetic = verse_data.get('phonetic_transcription', '')
                    if verse_num and phonetic:
                        phonetic_data[verse_num] = phonetic

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
                if v_num in phonetic_data:
                    lines.append(f"**Phonetic**: `{phonetic_data[v_num]}`")
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

                # Get commentary (phonetics are now in PSALM TEXT section, not here)
                commentary = get_value(verse_data, 'commentary', '')

                # Format verse (no longer including phonetics here)
                lines.append(f"**Verse {verse_num}**")
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
