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
from pathlib import Path
from typing import Optional, Dict
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
   - **IMPORTANT**: The Macro and Micro analysts have identified interesting research questions (see their inputs above). You should attempt to answer any of these questions that can be meaningfully addressed with the available research materials. If a question is answerable, weave the answer into your essay where appropriate.

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

6. **Reflects on liturgical context and reception**
   - The research bundle includes detailed information about where and how this psalm (or specific phrases from it) appears in Jewish liturgy
   - Pay attention to liturgical usage patterns - they reveal how the psalm has been interpreted and valued in Jewish tradition
   - Consider what the liturgical placement tells us about the psalm's meaning and reception
   - Integrate liturgical insights naturally into your discussion - don't treat them as a separate topic
   - Example: "The daily recitation of this verse in the Amidah suggests that Jewish liturgy understood it as..."

7. **Writes for an educated general reader**
   - Scholarly rigor but accessible prose
   - Technical terms explained when necessary
   - Balance depth with readability
   - Novel insights are strongly encouraged

8. **Uses proper citations**
   - When referring to specific Hebrew verse, phrases and terms, cite in Hebrew and English
   - in Hebrew, replace the tegragrammaton with 'ה
   - When citing research, note the source (e.g., "BDB lexicon notes...", "Concordance shows...")
   - When referencing other texts, cite book/chapter/verse (e.g., "Gen 1:2", "KTU 1.4")

9. **Stylistic guidelines**
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

## OUTPUT FORMAT

Write TWO sections:

### 1. Introduction Essay (800-1200 words)
[Write the main introduction essay as described above]

### 2. Modern Jewish Liturgical Use (150-300 words)
After the introduction essay, write a separate section titled "## Modern Jewish Liturgical Use" that summarizes where and how elements of this psalm appear in Jewish liturgy.

This section should:
- Summarize the liturgical usage information provided in the research bundle
- Distinguish between full recitations of the psalm vs. individual verses or phrases quoted in prayers
- Be specific about occasions (Weekday/Shabbat/Festivals), services (Shacharit/Mincha/Maariv), and traditions (Ashkenaz/Sefard/Edot HaMizrach)
- Explain what the liturgical placement reveals about how Jewish tradition has understood and valued this psalm
- Be scholarly but concise - aim for 150-300 words

Example structure:
"Psalm [X] is recited in its entirety during [occasion/service/tradition]. Verse [Y] from this psalm appears in [specific prayer], recited during [service] on [occasions]. The phrase '[Hebrew phrase]' from verse [Z] is incorporated into [prayer/piyyut] in the [tradition] nusach. This liturgical usage reflects the tradition's understanding of this psalm as..."

---

Write both sections below in plain text (NOT JSON). Use markdown formatting for emphasis (*italics*) and Hebrew transliterations.
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

### PHONETIC TRANSCRIPTIONS
{phonetic_section}


---

## YOUR TASK: WRITE VERSE-BY-VERSE COMMENTARY

For EACH verse in the psalm, write a commentary annotation that draws on diverse scholarly angles:

**AUDIENCE HEBREW PROFICIENCY:**
- Your readers are familiar with biblical and rabbinic Hebrew
- When you quote sources (biblical texts, rabbinic sources, liturgical texts), provide the Hebrew original AS WELL AS the English translation
- Include enough Hebrew to support your point and/or demonstrate things of interest (unusual constructions, wordplay, idioms, etc.)
- Don't rely solely on translation—let readers see the Hebrew evidence for themselves
- NOTE: The verse text in Hebrew will be programmatically inserted before your commentary, so you do NOT need to include it yourself

**LENGTH GUIDELINES:**
- **Target length**: 150-400 words per verse
- **Can be longer** (400+ words) if there's a genuinely interesting finding or insight that merits extended illumination
- Let the content determine the length - don't pad or artificially constrain

### ITEMS OF INTEREST TO ILLUMINATE (when relevant to the verse):

The following areas are of particular interest to intelligent, well-read lay readers who desire poetic, literary, linguistic, and historical insights:

1. **Phonetics & Sound Patterns (CRITICAL)**
   - You are provided with an authoritative phonetic transcription for each verse with STRESS MARKING (e.g., `**Phonetic**: pō-**TĒ**-akh et-yā-**DHE**-khā`).
   - **STRESS NOTATION**: Syllables in **BOLD CAPS** indicate stressed syllables based on Hebrew cantillation marks (te'amim). Example: `mal-**KHŪTH**-khā` means the middle syllable KHŪTH receives the primary stress.
   - **USE THIS DATA**: When discussing alliteration, assonance, rhythm, meter, or other sound-based poetic devices, you MUST base your claims on this transcription, not on modern pronunciation.
   - **STRESS ANALYSIS**: You can now analyze prosodic patterns by counting stressed syllables (marked in **BOLD CAPS**). For example, "This verse has a 3+2 stress pattern with stresses on VŌDH, KHĀ, MĒ in the first colon and KHĀ, BĒ in the second."
   - **VERIFY CLAIMS**: For example, before claiming a "soft 'f' sound," check the transcription. If it says `p` (e.g., in `pō-te-akh`), your claim is incorrect. The transcription is your ground truth for all phonetic analysis. Distinguish `p` vs `f`, `b` vs `v`, `k` vs `kh`.
   - If you are ever providing a transcription for ANY reason, you must use the authoritative phonetic transcription provided to you; **do not make it up on your own.**
   
2. **Poetics**
   - Parallelism types (synonymous, antithetical, synthetic, climactic)
   - Wordplay (paronomasia, alliteration, assonance) - *Must be verified with phonetic transcription*
   - Meter and rhythm
   - Structural devices (chiasm, inclusio, envelope structure)
   - **Unusual turns of phrase**: When a verse contains an interesting or unusual Hebrew phrase, idiom, or construction (like הֲ֭דַר כְּב֣וֹד הוֹדֶ֑ךָ or עֱז֣וּז נֽוֹרְאֹתֶ֣יךָ), comment on it - explain what makes it distinctive, how it functions poetically, and what it contributes to the verse's meaning

   **Figurative Language Integration (CRITICAL):**
   For each verse containing figurative language where the research provided relevant biblical parallels:
   1. **Identify the image** and explain its meaning in this specific context
   2. **Cite compelling parallel uses** from the figurative language database (at least 1-2 specific references with book/chapter/verse)
   3. **Analyze the pattern**: How common is this image? How is it typically used across Scripture?
   4. **Note distinctive features**: How does this psalm's use differ from or extend typical usage?

   Example: "The 'opened hand' imagery (v. 16) appears 23 times in Scripture as an idiom for generosity (Deut 15:8, 11). Psalm 145 distinctively applies this human obligation metaphor to divine providence, transforming covenant ethics into cosmic theology."

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

3a. **Modern Liturgical Context** (IMPORTANT)
   - The research bundle includes detailed information about where and how this verse (or phrases from it) appears in Jewish liturgy
   - When a verse appears in liturgy, comment on this usage and what it reveals about reception and interpretation
   - Be specific: mention the prayer name, service (Shacharit/Mincha/Maariv), occasion (Weekday/Shabbat/Festivals), and tradition (Ashkenaz/Sefard/Edot HaMizrach)
   - Consider what the liturgical placement tells us about how Jewish tradition understood this verse
   - Integrate liturgical insights naturally - don't treat them as a separate "trivia" item
   - Example: "The placement of this verse in the daily Amidah suggests the tradition understood it as expressing fundamental covenantal theology..."

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
   - Target (what the figuration is ABOUT)-vehicle (what the target is likened to)-ground (what characteristics of the target are illuminated by this choice of vehicle)
   -posture analysis
   - Evolution of metaphorical meaning

10. **Timing/Composition Clues**
    - Vocabulary that suggests dating (Persian loanwords, Aramaisms, etc.)
    - Theological development indicators
    - Historical allusions (Babylonian exile, monarchy, etc.)
    - Liturgical evolution markers

11. **Interpretation and Reception**
    - *Influence of verse and their use in aggada and halacha by the Mishna, Talum, Midrashim, etc as provided in the Torah Temimah* - MAKE SURE to carefully review the Torah Temimah material in the research bundle
    - *Medieval Jewish commentary (Rashi, Ibn Ezra, Radak)* - see research bundle
    - *Jewish commentaries of the modern era (Metzudat David, Malbim, Meiri)* - see research bundle
    - Targum renderings
    - Church fathers (Augustine, Jerome, etc.)
    - Medieval Christian interpretation
    - Modern critical scholarship debates

### VALIDATION CHECK - Figurative Language:

Before finalizing, review each verse with figurative language identified in the research:
- ✓ Does the commentary cite at least ONE specific biblical parallel from the database?
- ✓ Does it use the comparison to generate an insight about THIS verse?
- ✓ Does it provide pattern analysis (e.g., "This imagery appears 11x in Psalms, predominantly in contexts of...")?

If any check fails, REVISE to incorporate comparative analysis using the database.

### IMPORTANT NOTES:

- **Relationship to Introduction Essay**: You have the complete introduction essay. Your verse commentary should COMPLEMENT (not repeat) the introduction. If the introduction discussed a theme at length, you can allude to it briefly but focus on verse-specific details not covered in the introduction.
- **Address interesting questions**: The Macro and Micro analysts have identified interesting research questions (see their inputs above). When commenting on specific verses, if any of these questions are relevant to that verse and can be meaningfully answered with the available research materials, address them in your commentary.
- **Independence from macro thesis**: The verse commentary need NOT always relate to the macro thesis - follow what's interesting in each verse
- **Reader interest**: Focus on what would genuinely interest and inform an intelligent, well-read lay reader who desires poetic, literary, linguistic, and historical insights
- **Flexibility**: Some verses may focus on poetics, others on Vorlage, others on Ugaritic parallels, others on figurative language patterns - let the verse and research materials guide you
- **Depth over breadth**: Better to explore 2-3 angles deeply than mention everything superficially
- **Evidence-based**: Ground all observations in the research materials provided (BDB, concordances, figurative language database, traditional commentaries)
- **Use research bundle effectively**: The research bundle contains:
  * BDB lexicon entries with semantic ranges, etymologies, and usage patterns
  * Concordance data showing where Hebrew terms appear elsewhere in Scripture - cite these parallels!
  * Figurative language instances showing how vehicles/metaphors are used across the Bible - use them produce insights about the intent of the poet and their selection of this figuration here
  * Traditional commentary excerpts from Rashi, Ibn Ezra, Radak, Meiri, Metzudat David and Malbim - engage with these interpretive traditions!
  * The Torah Temimah identifies instances where a given text was mined for aggadic and halachic purposes - make sure to carefully review and incorporate these materials where relevant
  * LXX text showing ancient Greek interpretation
- **Define technical terms**: When using jargon (jussive, anaphora, chiasm, inclusio, polemic, theophany, hendiadys, etc.), provide brief, accessible definitions for lay readers
- **Vary your approach**: Don't use the same scholarly angles for every verse - alternate between poetics, historical context, textual criticism, figurative analysis, etc.
- **Comment on unusual phrases and poetic devices**: When a verse contains interesting or unusual Hebrew phrases, idioms, wordplay, or poetic devices, make sure to comment on them. These linguistic and literary features are precisely what intelligent lay readers find fascinating.

### FORMAT FOR EACH VERSE:

**Verse [N]**

[150-400 words of commentary drawing on relevant scholarly angles. Include Hebrew text when quoting sources—readers are familiar with biblical and rabbinic Hebrew. NOTE: The verse text in Hebrew will be programmatically inserted before your commentary.]

---

## CRITICAL REQUIREMENTS

- **Cover ALL verses** in the psalm
- **Length**: 150-400 words per verse (can and should be longer—400+ words—if there's genuinely interesting material to illuminate, such as unusual Hebrew phrases, complex poetic devices, significant textual variants, or important interpretive questions to address)
- **Variety**: Don't use the same angles for every verse - vary your approach across poetics, textual criticism, figurative language, historical context, etc.
- **Evidence**: Cite Hebrew terms, concordance patterns, research findings, traditional commentators
- **Readability**: Scholarly but accessible for intelligent lay readers (New Yorker/Atlantic level)
- **Define terms**: Explain technical terminology when used
- **Independence**: Don't force connections to the macro thesis if they're not natural - follow what's interesting in each verse
- **Emphasize the interesting**: Make sure to comment on unusual turns of phrase, distinctive Hebrew idioms, and poetic devices. These are what make the commentary valuable and engaging.

---

Write the verse-by-verse commentary below in plain text (NOT JSON). Use markdown formatting.
"""


def format_phonetic_section(micro_analysis: 'MicroAnalysis') -> str:
    """Format phonetic transcriptions for inclusion in prompts."""
    lines = ["## PHONETIC TRANSCRIPTIONS\n"]
    lines.append("*Reference these for accurate phonetic commentary. DO NOT make phonetic claims without consulting these transcriptions.*\n")

    # Helper to get attribute/key value with fallback
    def get_value(obj, key, default=''):
        if hasattr(obj, key):
            return getattr(obj, key, default)
        elif isinstance(obj, dict):
            return obj.get(key, default)
        return default

    verses = []
    if hasattr(micro_analysis, 'verse_commentaries'): # Pydantic
        verses = micro_analysis.verse_commentaries
    elif isinstance(micro_analysis, dict): # Dict
        verses = micro_analysis.get('verse_commentaries', [])

    for vc in verses:
        phonetic_transcription = get_value(vc, 'phonetic_transcription')
        if phonetic_transcription:
            lines.append(f"**Verse {get_value(vc, 'verse_number')}**: `{phonetic_transcription}`\n")

    return "\n".join(lines)


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
        macro_analysis: 'MacroAnalysis',
        micro_analysis: 'MicroAnalysis',
        research_bundle_content: str,
        psalm_number: int,
        max_tokens_intro: int = 4000,
        max_tokens_verse: int = 16000
    ) -> Dict[str, str]:
        """
        Generate complete commentary from analysis objects.

        Args:
            macro_analysis: MacroAnalysis object
            micro_analysis: MicroAnalysis object
            research_bundle_content: Research Bundle markdown content
            psalm_number: Psalm number
            max_tokens_intro: Max tokens for introduction essay
            max_tokens_verse: Max tokens for verse commentary

        Returns:
            Dictionary with 'introduction' and 'verse_commentary' keys
        """
        self.logger.info("Starting commentary synthesis")

        self.logger.info(f"Synthesizing commentary for Psalm {psalm_number}")
        self.logger.info(f"  Macro thesis: {len(macro_analysis.to_markdown())} chars")
        self.logger.info(f"  Micro analysis: {len(micro_analysis.to_markdown())} chars")
        self.logger.info(f"  Research bundle: {len(research_bundle_content)} chars")

        # Check for phonetic data and log it
        try:
            verses = []
            if hasattr(micro_analysis, 'verse_commentaries'): # Pydantic
                verses = micro_analysis.verse_commentaries
            elif isinstance(micro_analysis, dict): # Dict
                verses = micro_analysis.get('verse_commentaries', [])

            if verses:
                phonetic_found = False
                # Check the first verse for phonetic data to confirm it's present
                first_verse = verses[0]
                if (hasattr(first_verse, 'phonetic_transcription') and first_verse.phonetic_transcription) or \
                   (isinstance(first_verse, dict) and first_verse.get('phonetic_transcription')):
                   phonetic_found = True

                if phonetic_found:
                    self.logger.info("✓ Phonetic transcription data FOUND and passed to synthesis writer.")
                else:
                    self.logger.warning("⚠ Phonetic transcription data NOT FOUND in the provided micro_analysis.")
            else:
                self.logger.warning("⚠ No verse commentaries found in micro_analysis to check for phonetic data.")
        except (AttributeError, TypeError, StopIteration) as e:
            self.logger.warning(f"⚠ Could not verify phonetic data presence: {e}")

        # Step 2: Generate introduction essay
        introduction = self._generate_introduction(
            psalm_number=psalm_number,
            macro_analysis=macro_analysis,
            micro_analysis=micro_analysis,
            research_bundle=research_bundle_content,
            max_tokens=max_tokens_intro
        )

        # Step 3: Generate verse commentary (now with access to introduction)
        verse_commentary = self._generate_verse_commentary(
            psalm_number=psalm_number,
            macro_analysis=macro_analysis,
            micro_analysis=micro_analysis,
            research_bundle=research_bundle_content,
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

    
# This section is removed as file loading is now handled in the pipeline script
#
#    def _load_macro_analysis(self, file_path: Path) -> Dict[str, Any]:
#        """Load MacroAnalysis from JSON file."""
#        self.logger.info(f"Loading macro analysis from {file_path}")
#        with open(file_path, 'r', encoding='utf-8') as f:
#            return json.load(f)
#
#    def _load_micro_analysis(self, file_path: Path) -> Dict[str, Any]:
#        """Load MicroAnalysis from JSON file."""
#        self.logger.info(f"Loading micro analysis from {file_path}")
#        with open(file_path, 'r', encoding='utf-8') as f:
#            return json.load(f)
#
#    def _load_research_bundle(self, file_path: Path) -> str:
#        """Load Research Bundle from markdown file."""
#        self.logger.info(f"Loading research bundle from {file_path}")
#        with open(file_path, 'r', encoding='utf-8') as f:
#            return f.read()

    def _trim_figurative_with_priority(self, figurative_section: str, keep_ratio: float) -> str:
        """
        Intelligently trim figurative language section, prioritizing instances from Psalms.

        Instead of simple proportional trimming, this function categorizes instances
        by source (Psalms vs. other books) and discards non-Psalms instances first.

        Args:
            figurative_section: The full figurative language section markdown.
            keep_ratio: The proportion of original instances to keep (0.0 to 1.0).

        Returns:
            Trimmed figurative language section with Psalms instances prioritized.
        """
        import re

        # Split into individual query blocks (### Query N)
        query_pattern = r'(### Query \d+.*?)(?=### Query \d+|$)'
        queries = re.findall(query_pattern, figurative_section, re.DOTALL)

        if not queries:
            # Fallback: simple truncation if no queries are found
            target_size = int(len(figurative_section) * keep_ratio)
            return figurative_section[:target_size] + f"\n\n[Trimmed {len(figurative_section) - target_size} chars]"

        trimmed_queries = []
        total_original_instances = 0
        total_kept_instances = 0

        for query_block in queries:
            # Extract query header and instances text
            match = re.match(r'(.*?#### Instances:)(.*)', query_block, re.DOTALL)
            if not match:
                trimmed_queries.append(query_block)
                continue

            header = match.group(1)
            instances_text = match.group(2)

            # Find all individual instances
            instance_pattern = r'(\*\*[^*]+\*\*.*?)(?=\*\*[^*]+\*\*|$)'
            instances = re.findall(instance_pattern, instances_text, re.DOTALL)

            if not instances:
                trimmed_queries.append(query_block)
                continue

            total_original_instances += len(instances)

            # --- New Prioritization Logic ---
            psalms_instances = [inst for inst in instances if "Psalms" in inst]
            other_instances = [inst for inst in instances if "Psalms" not in inst]

            target_keep_count = max(1, int(len(instances) * keep_ratio))

            kept_instances = []
            # Prioritize keeping instances from Psalms
            if len(psalms_instances) >= target_keep_count:
                # If we have enough Psalms instances, take from them
                kept_instances = psalms_instances[:target_keep_count]
            else:
                # If not, take all Psalms instances and fill the rest from other books
                kept_instances.extend(psalms_instances)
                remaining_needed = target_keep_count - len(psalms_instances)
                if remaining_needed > 0:
                    kept_instances.extend(other_instances[:remaining_needed])
            
            total_kept_instances += len(kept_instances)
            omitted_count = len(instances) - len(kept_instances)

            # Reassemble the query block
            trimmed_block = header + '\n' + ''.join(kept_instances)
            if omitted_count > 0:
                trimmed_block += f"\n\n[{omitted_count} more instances omitted for space]\n"

            trimmed_queries.append(trimmed_block)

        result = '## Figurative Language Instances\n\n' + '\n'.join(trimmed_queries)
        
        original_char_len = len(figurative_section)
        final_char_len = len(result)
        
        self.logger.info(f"Figurative trim (prioritizing Psalms): "
                        f"{original_char_len:,} → {final_char_len:,} chars. "
                        f"Instances: {total_original_instances} → {total_kept_instances}.")
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
                self.logger.info(f"Trimming figurative with priority for Psalms: keeping {trim_ratio:.1%} of each query's results")
                figurative_section = self._trim_figurative_with_priority(figurative_section, trim_ratio)
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
        macro_analysis,  # MacroAnalysis object or Dict
        micro_analysis,  # MicroAnalysis object or Dict
        research_bundle: str,
        max_tokens: int
    ) -> str:
        """
        Generate introduction essay.

        Args:
            psalm_number: Psalm number
            macro_analysis: MacroAnalysis object or dict
            micro_analysis: MicroAnalysis object or dict
            research_bundle: Research bundle markdown content
            max_tokens: Maximum tokens for generation

        Returns:
            Generated introduction text
        """
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

            # Track model usage
            if hasattr(self, 'tracker') and self.tracker:
                self.tracker.track_model_usage(
                    agent_name='synthesis_writer',
                    model=self.model,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens)

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
        macro_analysis,  # MacroAnalysis object or Dict
        micro_analysis,  # MicroAnalysis object or Dict
        research_bundle: str,
        max_tokens: int,
        introduction_essay: str = ""
    ) -> str:
        """
        Generate verse-by-verse commentary.

        Args:
            psalm_number: Psalm number
            macro_analysis: MacroAnalysis object or dict
            micro_analysis: MicroAnalysis object or dict
            research_bundle: Research bundle markdown content
            max_tokens: Maximum tokens for generation
            introduction_essay: Previously generated introduction text

        Returns:
            Generated verse commentary text
        """
        self.logger.info(f"Generating verse commentary for Psalm {psalm_number}")

        # Format inputs
        macro_text = self._format_macro_for_prompt(macro_analysis)
        micro_text = self._format_micro_for_prompt(micro_analysis)
        phonetic_section = format_phonetic_section(micro_analysis)

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
            research_bundle=research_text,
            phonetic_section=phonetic_section
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

            # Track model usage
            if hasattr(self, 'tracker') and self.tracker:
                self.tracker.track_model_usage(
                    agent_name='synthesis_writer',
                    model=self.model,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens)

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

    def _format_macro_for_prompt(self, macro) -> str:
        """
        Format MacroAnalysis for prompt.

        Handles both Pydantic MacroAnalysis objects and dict format.

        Args:
            macro: MacroAnalysis object or dict

        Returns:
            Formatted string for prompt
        """
        lines = []

        # Helper to get attribute/key value with fallback
        def get_value(obj, key, default='N/A'):
            if hasattr(obj, key):
                return getattr(obj, key, default)
            elif isinstance(obj, dict):
                return obj.get(key, default)
            return default

        lines.append(f"**Thesis**: {get_value(macro, 'thesis_statement')}")
        lines.append(f"**Genre**: {get_value(macro, 'genre')}")
        lines.append(f"**Context**: {get_value(macro, 'historical_context')}")
        lines.append("")
        lines.append("**Structure**:")

        structural_outline = get_value(macro, 'structural_outline', [])
        for div in structural_outline:
            section = get_value(div, 'section', '')
            theme = get_value(div, 'theme', '')
            lines.append(f"  - {section}: {theme}")

        lines.append("")
        lines.append("**Poetic Devices**:")

        poetic_devices = get_value(macro, 'poetic_devices', [])
        for device in poetic_devices:
            device_name = get_value(device, 'device', '')
            description = get_value(device, 'description', '')
            lines.append(f"  - {device_name}: {description}")

        # Add research questions
        questions = get_value(macro, 'research_questions', [])
        if questions:
            lines.append("")
            lines.append("**Research Questions** (from Macro Analyst):")
            for i, q in enumerate(questions, 1):
                lines.append(f"  {i}. {q}")

        return "\n".join(lines)

    def _format_micro_for_prompt(self, micro) -> str:
        """
        Format MicroAnalysis for prompt.

        Handles both Pydantic MicroAnalysis objects and dict format.
        Properly extracts phonetic transcription data from VerseCommentary objects.

        Args:
            micro: MicroAnalysis object or dict

        Returns:
            Formatted string for prompt including phonetic data
        """
        lines = []

        # Helper to get attribute/key value with fallback
        def get_value(obj, key, default=''):
            if hasattr(obj, key):
                return getattr(obj, key, default)
            elif isinstance(obj, dict):
                return obj.get(key, default)
            return default

        # Handle both Pydantic object and dict formats
        # Support both new format ('verse_commentaries') and old format ('verses')
        if hasattr(micro, 'verse_commentaries'):
            # Pydantic MicroAnalysis object
            verses = micro.verse_commentaries
        elif isinstance(micro, dict):
            # Dictionary format
            verses = micro.get('verse_commentaries', micro.get('verses', []))
        else:
            verses = []

        for verse_data in verses: # Iterate through all verses
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

            # Add discoveries if present
            lexical = get_value(verse_data, 'lexical_insights', [])
            if lexical:
                lines.append(f"  Lexical: {', '.join(lexical)}")

            figurative = get_value(verse_data, 'figurative_analysis', [])
            if figurative:
                lines.append(f"  Figurative: {', '.join(figurative)}")

            lines.append("")

        # Add thematic threads if present
        threads = get_value(micro, 'thematic_threads', [])
        if threads:
            lines.append("**Thematic Threads Across Verses:**")
            for thread in threads:
                lines.append(f"  - {thread}")
            lines.append("")

        # Add interesting questions if present
        interesting_questions = get_value(micro, 'interesting_questions', [])
        if interesting_questions:
            lines.append("")
            lines.append("**Interesting Questions** (from Micro Analyst):")
            for i, q in enumerate(interesting_questions, 1):
                lines.append(f"  {i}. {q}")
            lines.append("")

        # Add synthesis notes if present
        synth_notes = get_value(micro, 'synthesis_notes', '')
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
