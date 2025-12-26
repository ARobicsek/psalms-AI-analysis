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
    from src.utils.cost_tracker import CostTracker
else:
    from ..schemas.analysis_schemas import MacroAnalysis, MicroAnalysis
    from ..utils.logger import get_logger
    from ..utils.cost_tracker import CostTracker


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
   - Interesting historical anecdotes and literary and scholarly insights are welcome to enliven and enrich the essay

3. **Addresses major interpretive questions**
   - What is this psalm about? If there are sections that seem quite different, what theme, context or idea holds them together?
   - What is the psalm's central message and how does it function?
   - What are the key poetic/rhetorical strategies and why do they matter?
   - How does this psalm relate to its Ancient Near Eastern context?
   - What are the most significant interpretive debates or challenges?
   - What earned this psalm its place in the biblical canon?
   - **IMPORTANT**: The Macro and Micro analysts have identified interesting research questions (see their inputs above). You should attempt to answer any of these questions that can be meaningfully addressed with the available research materials. If a question is answerable, weave the answer into your essay where appropriate.

4. **Engages prior scholarship and classical interpretations**
   - Note relevant traditional rabbinic or patristic readings when available
   - Reference how scholars have historically interpreted key passages
   - Acknowledge interpretive debates and schools of thought
   - Example: "Traditional interpretation sees X, but recent scholarship suggests Y..."
   - Discuss scholarly debates when they are engaging for a smart, curious lay audience

5. **Makes intertextual connections**
   - Cite parallel biblical texts where similar language/imagery appears
   - Reference ANE parallels (Ugaritic, Akkadian, Egyptian texts) when relevant. The Deep Web Research section may contain useful information here.
   - Show how this psalm's language echoes or innovates or is in conversation with other texts
   - Example: "The term 'לְבָדָד' carries echoes of Deuteronomy 33:28 "וַיִּשְׁכֹּן֩ יִשְׂרָאֵ֨ל בֶּ֤טַח בָּדָד֙...אֶ֖רֶץ דָּגָ֣ן וְתִיר֑וֹשׁ" - ("Israel dwells secure, alone… in a land of grain and wine") "
   - Carefully review the 'Related Psalms Analysis' section of the research bundle for interesting/informative parallels with other psalms, and incorporate these insights when relevant.

6. **Reflects on liturgical context and reception**
   - The research bundle includes detailed information about where and how this psalm (or specific phrases from it) appears in Jewish liturgy
   - Pay attention to liturgical usage patterns - they reveal how the psalm has been interpreted and valued in Jewish tradition
   - Consider what the liturgical placement tells us about the psalm's meaning and reception
   - Integrate liturgical insights naturally into your discussion - don't treat them as a separate topic
   - **CRITICAL: When mentioning liturgical usage, QUOTE the relevant liturgical texts in Hebrew with English translation**
   - Example: "The daily recitation of this verse in the Amidah suggests that Jewish liturgy understood it as..."
   - The Deep Web Research section may contain interesting information about the cultural afterlife of this psalm. Use it to enliven the essay.

7. **SHOWS evidence through generous quotation** (CRITICAL)
   - **Quote liberally from all sources - biblical parallels, liturgical texts, traditional commentaries**
   - When you mention a biblical parallel (e.g., "this echoes Psalm 44:4"), QUOTE it in Hebrew with English translation
   - When you reference liturgical usage (e.g., "appears in Shabbat Musaf"), QUOTE the relevant liturgical text in Hebrew with English
   - When you cite multiple parallels for a pattern (e.g., "light of your face" in Ps 4:7, 44:4, 89:16, Prov 16:15), quote at least 1-2 of the most illustrative examples in Hebrew with English
   - When you mention a linguistic pattern across psalms (e.g., בְּנֵי אִישׁ in Ps 49:3, 62:10), quote the best example(s) to show the pattern
   - Don't just cite - SHOW the reader the actual text. Your readers are hungry to see the Hebrew evidence
   - Think of quotations as your proof - they transform vague claims into vivid demonstrations

8. **Writes for an educated general reader**
   - Scholarly rigor but accessible prose
   - Technical terms explained when necessary
   - Balance depth with readability
   - Novel insights are strongly encouraged

9. **Uses proper citations with quotations**
   - When referring to specific Hebrew verse, phrases and terms, cite in Hebrew and English
   - In Hebrew, replace the tetragrammaton with 'ה
   - **IMPORTANT: Most citations should be accompanied by actual quotations (Hebrew + English)**
   - When citing research, note the source (e.g., "BDB lexicon notes...", "Concordance shows...")
   - When referencing other texts, cite book/chapter/verse AND quote the relevant portion when illustrative (e.g., "Gen 1:2", "KTU 1.4")

10. **Stylistic guidelines**
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
- do NOT try to comment on liturgical use of this psalm WITHOUT carefully consulting the research bundle's liturgical information
- for PHRASES that appear in liturgy, make sure to quote the phrases in full in Hebrew, and make sure to include enough of a quotation from the relevant prayer(s) to properly illustrate their use.
- for individual verses and phrases that appear in the liturgy, reflect on whether their liturgical use goes with the grain of its natural ("pshat") reading or whether the compilers of the liturgy have put this verse or phrase to use in a novel way.


This section should:
- Summarize the liturgical usage information provided in the research bundle
- Distinguish between full recitations of the psalm vs. individual verses or phrases quoted in prayers
- Be specific about occasions (Weekday/Shabbat/Festivals), services (Shacharit/Mincha/Maariv), and traditions (Ashkenaz/Sefard/Edot HaMizrach)
- Explain what the liturgical placement reveals about how Jewish tradition has understood and valued this psalm
- Be scholarly but concise - aim for 150-300 words

Example structure:
"Psalm [X] is recited in its entirety during [occasion/service/tradition]. Verse [Y] from this psalm appears in [specific prayer], recited during [service] on [occasions]. The phrase '[Hebrew phrase]' from verse [Z] is incorporated into [prayer/piyyut] in the [tradition] nusach. This liturgical usage reflects the tradition's understanding of this psalm as..."

---

Write both sections below in plain text (NOT JSON). Use markdown formatting for emphasis (*italics*) and phonetic transcriptions.
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

**CRITICAL: START each verse's commentary with the Hebrew text of that verse, punctuated to show poetic structure:**
- Present the verse using punctuation (semicolons, periods, commas) to illustrate how the verse is poetically divided
- This punctuated presentation helps readers see the verse's structure at a glance
- Example: Original verse "בְּקׇרְאִי עֲנֵנִי ׀ אֱלֹקֵי צִדְקִי בַּצָּר הִרְחַבְתָּ לִּי חׇנֵּנִי וּשְׁמַע תְּפִלָּתִֽי׃" becomes "בְּקׇרְאִי עֲנֵנִי אֱלֹקֵי צִדְקִי; בַּצָּר הִרְחַבְתָּ לִּי; חׇנֵּנִי וּשְׁמַע תְּפִלָּתִי."
- After presenting the punctuated verse, proceed immediately with your commentary

**LENGTH GUIDELINES:**
- **Target length**: 150-400 words per verse
- **Can be longer** (400+ words) if there's a genuinely interesting finding or insight that merits extended illumination
- Let the content determine the length - don't pad or artificially constrain

**PACING FOR LONG PSALMS (35+ verses):**
For longer psalms, you have limited output space. Plan ahead and pace yourself:
- **Strategic grouping allowed**: You MAY group 2-4 thematically related verses together (e.g., "Verses 21-24") when they form a natural unit. Use heading format: `**Verses N-M**`
- **Plan from the start**: If grouping is necessary, do it THROUGHOUT the psalm—not just at the end. Decide your grouping strategy before you begin writing.
- **Equal treatment**: Later verses deserve the same quality of analysis as early verses. Do NOT rush or provide minimal content for late verses.
- **Avoid truncation notes**: NEVER write things like "Due to length constraints, remaining verses are not included." Instead, adjust your pacing from the beginning.
- **Quality over quantity**: A thoughtful 200-word treatment of grouped verses is better than 50 rushed words per verse at the end.

### ITEMS OF INTEREST TO ILLUMINATE (when relevant to the verse):

The following areas are of particular interest to intelligent, well-read lay readers who desire poetic, literary, linguistic, and historical insights:

1. **Phonetics & Sound Patterns (CRITICAL)**
   - You are provided with an authoritative phonetic transcription for each verse with STRESS MARKING (e.g., `**Phonetic**: pō-**TĒ**-akh et-yā-**DHE**-khā`).
   - **STRESS NOTATION**: Syllables in **BOLD CAPS** indicate stressed syllables based on Hebrew cantillation marks (te'amim). Example: `mal-**KHŪTH**-khā` means the middle syllable KHŪTH receives the primary stress.
   - **USE THIS DATA**: When discussing alliteration, assonance, rhythm, meter, or other sound-based poetic devices, you MUST base your claims on this transcription, not on modern pronunciation.
   - **STRESS ANALYSIS**: You can now analyze prosodic patterns by counting stressed syllables (marked in **BOLD CAPS**). For example, "This verse has a 3+2 stress pattern with stresses on VŌDH, KHĀ, MĒ in the first colon and KHĀ, BĒ in the second."
   - **VERIFY CLAIMS**: For example, before claiming a "soft 'f' sound," check the transcription. If it says `p` (e.g., in `pō-te-akh`), your claim is incorrect. The transcription is your ground truth for all phonetic analysis. Distinguish `p` vs `f`, `b` vs `v`, `k` vs `kh`.
   - If you are ever providing a transcription for ANY reason, you must use the authoritative phonetic transcription provided to you; **do not make it up on your own.**
   - **too many transcriptions clutter the prose. ONLY use transcriptions when the reader NEEDS to know how something was pronounced in order to understand your point about a poetic device. Do NOT transliterate words where the pronunciation does not pertain to the point you are making.** On the other hand, DO always provide the relevant text/words in Hebrew with English TRANSLATION.
-
   
2. **Poetics**
   - Parallelism types (synonymous, antithetical, synthetic, climactic)
   - Wordplay (e.g. paronomasia, alliteration, assonance) - *Must be verified with phonetic transcription*
   - Meter and rhythm
   - Structural devices (chiasm, inclusio, envelope structure)
   - **Unusual turns of phrase**: When a verse contains an interesting or unusual Hebrew phrase, idiom, or construction (like הֲ֭דַר כְּב֣וֹד הוֹדֶ֑ךָ or עֱז֣וּז נֽוֹרְאֹתֶ֣יךָ), comment on it - explain what makes it distinctive, how it functions poetically, and what it contributes to the verse's meaning

   **Figurative Language Integration (CRITICAL):**
   For each verse containing figurative language where the research provided relevant biblical parallels:
   1. **Identify the image** and explain its meaning in this specific context
   2. **QUOTE compelling parallel uses** from the figurative language database (at least 1-2 specific passages in Hebrew + English)
   3. **Analyze the pattern**: How common is this image? How is it typically used across Scripture?
   4. **Note distinctive features**: How does this psalm's use differ from or extend typical usage?
   5. **Quote liberally** - don't just cite references. Show readers the actual Hebrew text with English translation from at least 1-2 of the best parallels. You have a unique resource for this - USE IT by showing the texts!

   WEAK example: "The 'opened hand' imagery (v. 16) appears 23 times in Scripture as an idiom for generosity (Deut 15:8, 11). Psalm 145 distinctively applies this human obligation metaphor to divine providence." [This just cites - it doesn't quote]

   STRONG example: "The 'opened hand' imagery (v. 16) appears 23 times in Scripture. In Deuteronomy, it's a covenantal command: כִּֽי־פָתֹ֧חַ תִּפְתַּ֛ח אֶת־יָדְךָ֖ ל֑וֹ ('you shall surely open your hand to him,' Deut 15:8). Psalm 145 transforms this obligation into cosmic theology—the opened hand becomes God's."

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
   - Later cultural, political, religious influence and afterlife

3a. **Modern Liturgical Context** (IMPORTANT)
   - The research bundle includes detailed information about where and how this verse (or phrases from it) appears in Jewish liturgy
   - When a verse appears in liturgy, comment on this usage and what it reveals about reception and interpretation
   - **CRITICAL: QUOTE the liturgical texts in Hebrew with English translation to show HOW the verse is used**
   - Be specific: mention the prayer name, service (Shacharit/Mincha/Maariv), occasion (Weekday/Shabbat/Festivals), and tradition (Ashkenaz/Sefard/Edot HaMizrach)
   - Consider what the liturgical placement tells us about how Jewish tradition understood this verse
   - Integrate liturgical insights naturally - don't treat them as a separate "trivia" item
   - WEAK example: "The placement of this verse in the daily Amidah suggests the tradition understood it as expressing fundamental covenantal theology..." [too vague, no quotation]
   - STRONG example: "This verse appears in the Shabbat Musaf Amidah in the context of the sacrificial offerings: 'וְהִקְרִיבוּ לְךָ עוֹלוֹת תְּמִימִים זִבְחֵי צֶדֶק' ('and they shall offer You whole burnt-offerings, righteous sacrifices'), suggesting the tradition read this psalm's call for righteous sacrifices as..."

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
   - **CRITICAL: When mentioning parallel uses, QUOTE at least one illustrative example (Hebrew + English)**
   - Development of theological concepts across Scripture - show this through quoted examples
   - Formulaic language and its variations - demonstrate with quotations
   - Quotation and allusion to other biblical texts - show the actual texts
   - Insights from the 'Related Psalms Analysis' section - when there are convincing parallels, QUOTE the relevant Hebrew from the other psalm(s) with English translation
   - Don't just say "this appears in Psalm X" - show readers what Psalm X actually says

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
    - Make sure to read the "### About the Commentators" section in the research bundle for context on these commentators
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

[START with the Hebrew text of the verse, punctuated to show poetic structure. Then provide 150-400 words of commentary drawing on relevant scholarly angles. Include Hebrew text when quoting sources—readers are familiar with biblical and rabbinic Hebrew.]

---

## CRITICAL REQUIREMENTS

- **Cover ALL verses** in the psalm — NEVER truncate or skip verses
- **Length**: 150-400 words per verse (can and should be longer—400+ words—if there's genuinely interesting material to illuminate, such as unusual Hebrew phrases, complex poetic devices, significant textual variants, or important interpretive questions to address)
- **Pacing**: For long psalms (35+ verses), plan your pacing from the START. You may group thematically related verses, but do so consistently throughout—not just to rush through the end. NEVER write "remaining verses not included" or similar truncation notes.
- **Variety**: Don't use the same angles for every verse - vary your approach across poetics, textual criticism, figurative language, historical context, etc.
- **Evidence**: Cite Hebrew terms, concordance patterns, research findings, traditional commentators
- **Readability**: Scholarly but accessible for intelligent lay readers (New Yorker/Atlantic level)
- **Define terms**: Explain technical terminology when used
- **Independence**: Don't force connections to the macro thesis if they're not natural - follow what's interesting in each verse
- **Emphasize the interesting**: Make sure to comment on unusual turns of phrase, distinctive Hebrew idioms, and poetic devices. These are what make the commentary valuable and engaging.
- **Equal treatment for all verses**: The final verses of the psalm deserve the same thoughtful analysis as the opening verses. Plan accordingly.

---

Write the verse-by-verse commentary below in plain text (NOT JSON). Use markdown formatting.
"""


def format_phonetic_section(micro_analysis: 'MicroAnalysis') -> str:
    """Format phonetic transcription for inclusion in prompts."""
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
        logger=None,
        cost_tracker: Optional[CostTracker] = None
    ):
        """
        Initialize SynthesisWriter agent.

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            logger: Logger instance (or will create default)
            cost_tracker: CostTracker instance for tracking API costs
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required (pass api_key or set ANTHROPIC_API_KEY)")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-5"  # Sonnet 4.5
        self.logger = logger or get_logger("synthesis_writer")
        self.cost_tracker = cost_tracker or CostTracker()

        # Track whether deep research was removed due to size constraints
        self._deep_research_removed_for_space = False

        # Track which model was actually used for synthesis (may switch to Gemini for large bundles)
        self._synthesis_model_used = self.model

        # Track sections removed during trimming
        self._sections_removed = []

        # Store the trimmed research bundle for external access (debugging/logging)
        self._trimmed_research_bundle = None

        # Initialize Gemini client for fallback (lazy initialization)
        self._gemini_client = None

        self.logger.info(f"SynthesisWriter initialized with model {self.model}")

    @property
    def deep_research_removed_for_space(self) -> bool:
        """Return whether deep research was removed due to character limits."""
        return self._deep_research_removed_for_space

    @property
    def synthesis_model_used(self) -> str:
        """Return the model actually used for synthesis (may differ from default if Gemini fallback used)."""
        return self._synthesis_model_used

    @property
    def sections_removed(self) -> list:
        """Return list of sections removed during trimming."""
        return self._sections_removed

    @property
    def trimmed_research_bundle(self) -> str:
        """Return the trimmed research bundle text (after size reduction)."""
        return self._trimmed_research_bundle

    def _get_gemini_client(self):
        """Lazy initialization of Gemini client."""
        if self._gemini_client is None:
            try:
                from google import genai
                gemini_api_key = os.environ.get("GEMINI_API_KEY")
                if not gemini_api_key:
                    raise ValueError("GEMINI_API_KEY not found in environment")
                self._gemini_client = genai.Client(api_key=gemini_api_key)
                self.logger.info("Gemini client initialized for fallback")
            except ImportError:
                raise ImportError("google-genai package required for Gemini fallback. Install with: pip install google-genai")
        return self._gemini_client

    def _calculate_verse_token_limit(self, num_verses: int) -> int:
        """
        Calculate appropriate token limit for verse commentary based on psalm length.

        Target: ~1800 tokens per verse to maintain consistent depth across all psalms.
        Minimum: 16000 tokens (for psalms with fewer than 9 verses).
        Maximum: 64000 tokens (Claude Sonnet 4.5 API limit).

        Args:
            num_verses: Number of verses in the psalm

        Returns:
            Token limit for verse commentary generation
        """
        BASE_TOKENS_PER_VERSE = 1800
        MAX_TOKENS_LIMIT = 64000  # Claude Sonnet 4.5 max output tokens
        calculated = BASE_TOKENS_PER_VERSE * num_verses
        # Cap at API limit, minimum 16K
        return min(MAX_TOKENS_LIMIT, max(16000, calculated))

    def write_commentary(
        self,
        macro_analysis: 'MacroAnalysis',
        micro_analysis: 'MicroAnalysis',
        research_bundle_content: str,
        psalm_number: int,
        max_tokens_intro: int = 4000,
        max_tokens_verse: int = None  # Now optional, will be calculated if not provided
    ) -> Dict[str, str]:
        """
        Generate complete commentary from analysis objects.

        Args:
            macro_analysis: MacroAnalysis object
            micro_analysis: MicroAnalysis object
            research_bundle_content: Research Bundle markdown content
            psalm_number: Psalm number
            max_tokens_intro: Max tokens for introduction essay
            max_tokens_verse: Max tokens for verse commentary (if None, calculated based on psalm length)

        Returns:
            Dictionary with 'introduction' and 'verse_commentary' keys
        """
        self.logger.info("Starting commentary synthesis")

        # Calculate verse count for dynamic token scaling
        num_verses = 0
        if hasattr(micro_analysis, 'verse_commentaries'):
            num_verses = len(micro_analysis.verse_commentaries)
        elif isinstance(micro_analysis, dict):
            num_verses = len(micro_analysis.get('verse_commentaries', []))

        # Calculate verse token limit if not provided
        if max_tokens_verse is None:
            max_tokens_verse = self._calculate_verse_token_limit(num_verses)
            ideal_tokens = 1800 * num_verses
            if ideal_tokens > 64000:
                self.logger.warning(f"Long psalm ({num_verses} verses): capped at 64K tokens (ideal: {ideal_tokens})")
                self.logger.warning(f"  Effective tokens per verse: {max_tokens_verse // num_verses} (target: 1800)")
            self.logger.info(f"Calculated verse token limit for {num_verses} verses: {max_tokens_verse} tokens")

        self.logger.info(f"Synthesizing commentary for Psalm {psalm_number}")
        self.logger.info(f"  Macro thesis: {len(macro_analysis.to_markdown())} chars")
        self.logger.info(f"  Micro analysis: {len(micro_analysis.to_markdown())} chars")
        self.logger.info(f"  Research bundle: {len(research_bundle_content)} chars")
        self.logger.info(f"  Verse commentary token limit: {max_tokens_verse} tokens ({num_verses} verses)")

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
                        f"{original_char_len:,} -> {final_char_len:,} chars. "
                        f"Instances: {total_original_instances} -> {total_kept_instances}.")
        return result

    def _trim_research_bundle(self, research_bundle: str, max_chars: int = 600000) -> tuple:
        """
        Intelligently trim research bundle to fit within token limits.

        Priority order for trimming (first to last - least to most important):
        1. Related Psalms section - progressive trim (remove full psalm texts first)
        2. Related Psalms section - full removal
        3. Figurative Language - trim to 75%
        4. Figurative Language - trim to 50%

        If still over limit after step 4, return a flag indicating Gemini fallback needed.
        The Gemini 2.5 Pro model has 1M token context and can handle larger bundles.

        Preserved (never trimmed unless Gemini also fails):
        - Lexicon entries (most important for word analysis)
        - Traditional Commentaries (core interpretive context)
        - Liturgical Usage (essential for liturgical essays)
        - RAG/Scholarly Context (foundational framework)
        - Rabbi Sacks references (modern insights)
        - Concordance results
        - Deep Web Research

        Args:
            research_bundle: Full research bundle markdown
            max_chars: Maximum characters for Claude (~200K tokens)

        Returns:
            Tuple of (trimmed_bundle, deep_research_was_removed, needs_gemini_fallback)
        """
        import re

        deep_research_removed = False
        needs_gemini_fallback = False
        original_size = len(research_bundle)
        sections_removed = []

        if original_size <= max_chars:
            return research_bundle, deep_research_removed, needs_gemini_fallback

        self.logger.warning(f"Research bundle too large ({original_size:,} chars). Max: {max_chars:,}. Starting progressive trimming...")

        # Helper function to extract and remove a section
        def extract_section(bundle: str, section_pattern: str) -> tuple:
            """Extract a section from the bundle, return (section_content, bundle_without_section)."""
            pattern = rf'(## {section_pattern}.*?)(?=\n## [A-Z]|\n---\n\n## |\Z)'
            match = re.search(pattern, bundle, flags=re.DOTALL)
            if match:
                section = match.group(1)
                bundle_without = bundle[:match.start()] + bundle[match.end():]
                return section.strip(), bundle_without
            return "", bundle

        # Helper function to trim Related Psalms by removing full psalm texts
        def trim_related_psalms_progressively(section: str) -> str:
            """
            Trim Related Psalms section by removing full psalm text blocks.
            Keeps the preamble and word/phrase relationship data.
            """
            if not section:
                return section

            # Pattern to match "### Full Text of Psalm N" blocks and their content
            # These blocks contain the entire psalm text which is the bulk of the section
            full_text_pattern = r'### Full Text of Psalm \d+.*?(?=### (?:Full Text|Shared|Related)|## |$)'
            trimmed = re.sub(full_text_pattern, '', section, flags=re.DOTALL)

            # Add note about trimming
            if len(trimmed) < len(section):
                trimmed += "\n\n*[Full psalm texts removed for context length - word/phrase relationships preserved]*\n"

            return trimmed

        # Helper function to trim Figurative Language section
        def trim_figurative_by_ratio(section: str, keep_ratio: float) -> str:
            """Trim figurative language section, prioritizing instances from Psalms."""
            if not section or keep_ratio >= 1.0:
                return section

            # Split into query blocks
            query_pattern = r'(### Query \d+.*?)(?=### Query \d+|$)'
            queries = re.findall(query_pattern, section, re.DOTALL)

            if not queries:
                # Fallback: simple line-based trimming
                lines = section.split('\n')
                header_lines = []
                content_lines = []
                in_header = True
                for line in lines:
                    if in_header and (line.startswith('##') or line.startswith('*') or line.strip() == ''):
                        header_lines.append(line)
                    else:
                        in_header = False
                        content_lines.append(line)
                keep_count = max(1, int(len(content_lines) * keep_ratio))
                trimmed_content = content_lines[:keep_count]
                trimmed_content.append(f"\n[Section trimmed to {keep_ratio:.0%} for context length]")
                return '\n'.join(header_lines + trimmed_content)

            trimmed_queries = []
            for query_block in queries:
                # Find instances section
                match = re.match(r'(.*?#### (?:Instances|All Instances).*?:)(.*)', query_block, re.DOTALL)
                if not match:
                    trimmed_queries.append(query_block)
                    continue

                header = match.group(1)
                instances_text = match.group(2)

                # Find individual instances (marked by **Reference**)
                instance_pattern = r'(\*\*[^*]+\*\*.*?)(?=\*\*[^*]+\*\*|$)'
                instances = re.findall(instance_pattern, instances_text, re.DOTALL)

                if not instances:
                    trimmed_queries.append(query_block)
                    continue

                # Instances are already sorted by priority from assembly
                # Simply take the first target_count (highest priority first)
                target_count = max(1, int(len(instances) * keep_ratio))
                kept = instances[:target_count]

                omitted = len(instances) - len(kept)
                trimmed_block = header + '\n' + ''.join(kept)
                if omitted > 0:
                    trimmed_block += f"\n\n[{omitted} more instances omitted for space]\n"

                trimmed_queries.append(trimmed_block)

            result = '## Figurative Language Instances\n\n' + '\n'.join(trimmed_queries)
            return result

        # ========================================
        # STEP 1: Trim Related Psalms (remove full texts, keep relationships)
        # ========================================
        related_section, temp_bundle = extract_section(research_bundle, 'Related Psalms')

        if related_section:
            trimmed_related = trim_related_psalms_progressively(related_section)
            test_bundle = temp_bundle + '\n\n' + trimmed_related

            if len(test_bundle) <= max_chars:
                self.logger.info(f"Trimmed Related Psalms (removed full texts). "
                               f"Size: {original_size:,} -> {len(test_bundle):,} chars")
                research_bundle = test_bundle
                sections_removed.append("Related Psalms (full texts removed)")
            else:
                # Still over - continue to step 2
                research_bundle = test_bundle
                sections_removed.append("Related Psalms (full texts removed)")
                self.logger.info(f"Trimmed Related Psalms but still over limit...")

        # ========================================
        # STEP 2: Remove Related Psalms entirely
        # ========================================
        if len(research_bundle) > max_chars:
            related_section, temp_bundle = extract_section(research_bundle, 'Related Psalms')

            if related_section or "Related Psalms (full texts removed)" in sections_removed:
                research_bundle = temp_bundle
                # Update sections_removed - replace trimmed with removed
                if "Related Psalms (full texts removed)" in sections_removed:
                    sections_removed.remove("Related Psalms (full texts removed)")
                sections_removed.append("Related Psalms")

                if len(research_bundle) <= max_chars:
                    self.logger.info(f"Removed Related Psalms entirely. "
                                   f"Size: {original_size:,} -> {len(research_bundle):,} chars")
                else:
                    self.logger.info(f"Removed Related Psalms but still over limit...")

        # ========================================
        # STEP 3: Trim Figurative Language to 75%
        # ========================================
        if len(research_bundle) > max_chars:
            figurative_section, temp_bundle = extract_section(research_bundle, 'Figurative Language')

            if figurative_section:
                trimmed_fig = trim_figurative_by_ratio(figurative_section, 0.75)
                test_bundle = temp_bundle + '\n\n' + trimmed_fig
                research_bundle = test_bundle
                sections_removed.append("Figurative Language (trimmed to 75%)")

                if len(research_bundle) <= max_chars:
                    self.logger.info(f"Trimmed Figurative Language to 75%. "
                                   f"Size: {original_size:,} -> {len(research_bundle):,} chars")
                else:
                    self.logger.info(f"Trimmed Figurative Language to 75% but still over limit...")

        # ========================================
        # STEP 4: Trim Figurative Language to 50%
        # ========================================
        if len(research_bundle) > max_chars:
            figurative_section, temp_bundle = extract_section(research_bundle, 'Figurative Language')

            if figurative_section:
                trimmed_fig = trim_figurative_by_ratio(figurative_section, 0.50)
                test_bundle = temp_bundle + '\n\n' + trimmed_fig
                research_bundle = test_bundle
                # Update sections_removed
                if "Figurative Language (trimmed to 75%)" in sections_removed:
                    sections_removed.remove("Figurative Language (trimmed to 75%)")
                sections_removed.append("Figurative Language (trimmed to 50%)")

                if len(research_bundle) <= max_chars:
                    self.logger.info(f"Trimmed Figurative Language to 50%. "
                                   f"Size: {original_size:,} -> {len(research_bundle):,} chars")
                else:
                    self.logger.info(f"Trimmed Figurative Language to 50% but still over limit...")

        # ========================================
        # STEP 5: If still over limit, flag for Gemini fallback
        # ========================================
        if len(research_bundle) > max_chars:
            needs_gemini_fallback = True
            self.logger.warning(f"Bundle still {len(research_bundle):,} chars (limit: {max_chars:,}). "
                              f"Flagging for Gemini 2.5 Pro fallback (1M token context).")

        self.logger.info(f"Research bundle processing: {original_size:,} -> {len(research_bundle):,} chars")

        # Store sections removed for stats tracking (accumulate, don't overwrite)
        # This ensures we capture trimming from both intro and verse commentary calls
        if sections_removed:
            for section in sections_removed:
                # Check if this is a replacement for an existing entry
                if "Figurative Language (trimmed to 75%)" in section and "Figurative Language (trimmed to 50%)" in self._sections_removed:
                    # Don't add the 75% entry if 50% is already there
                    continue
                elif "Figurative Language (trimmed to 50%)" in section:
                    # Replace any existing 75% entry with 50%
                    if "Figurative Language (trimmed to 75%)" in self._sections_removed:
                        self._sections_removed.remove("Figurative Language (trimmed to 75%)")
                    if section not in self._sections_removed:
                        self._sections_removed.append(section)
                elif "Related Psalms (full texts removed)" in section and "Related Psalms" in self._sections_removed:
                    # Don't add the partial entry if full removal is already there
                    continue
                elif "Related Psalms" in section:
                    # Replace any existing partial entry with full removal
                    if "Related Psalms (full texts removed)" in self._sections_removed:
                        self._sections_removed.remove("Related Psalms (full texts removed)")
                    if section not in self._sections_removed:
                        self._sections_removed.append(section)
                else:
                    # Add other sections normally
                    if section not in self._sections_removed:
                        self._sections_removed.append(section)

        # Add trimming summary at the bottom of the research bundle
        trimming_summary = f"\n\n---\n## Research Bundle Processing Summary\n"
        trimming_summary += f"- Original size: {original_size:,} characters\n"
        trimming_summary += f"- Final size: {len(research_bundle):,} characters\n"
        trimming_summary += f"- Removed: {original_size - len(research_bundle):,} characters ({((original_size - len(research_bundle)) / original_size * 100):.1f}%)\n"

        if sections_removed:
            trimming_summary += f"- Sections removed/trimmed: {', '.join(sections_removed)}\n"
        else:
            trimming_summary += "- No sections removed (within size limit)\n"

        if needs_gemini_fallback:
            trimming_summary += "- Note: Using Gemini 2.5 Pro for synthesis (larger context window)\n"

        research_bundle += trimming_summary

        return research_bundle, deep_research_removed, needs_gemini_fallback

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

        # Trim research bundle if needed to fit within token limits
        # Target: ~350K chars max (~200K tokens at 1.75:1 ratio)
        # This leaves room for prompt template + macro/micro analysis
        research_text, deep_research_removed, needs_gemini = self._trim_research_bundle(research_bundle, max_chars=350000)

        # Store trimmed bundle for external access (debugging/logging)
        # Only set on first call (intro) - this captures the most aggressive trimming
        if self._trimmed_research_bundle is None:
            self._trimmed_research_bundle = research_text

        # Track if deep research was removed for space (will be reported in stats)
        self._deep_research_removed_for_space = deep_research_removed

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

        # Choose model based on bundle size
        if needs_gemini:
            return self._generate_introduction_with_gemini(prompt, psalm_number, max_tokens)
        else:
            return self._generate_introduction_with_claude(prompt, psalm_number, max_tokens)

    def _generate_introduction_with_claude(self, prompt: str, psalm_number: int, max_tokens: int) -> str:
        """Generate introduction using Claude Sonnet 4.5."""
        # Retry logic for transient network/API errors
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    import time
                    wait_time = retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    self.logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {wait_time}s delay...")
                    time.sleep(wait_time)

                stream = self.client.messages.stream(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

                # Collect response chunks
                introduction = ""
                with stream as response_stream:
                    for chunk in response_stream:
                        if hasattr(chunk, 'type') and chunk.type == 'content_block_delta':
                            if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'type'):
                                if chunk.delta.type == 'text_delta':
                                    introduction += chunk.delta.text

                    # Get final message for usage tracking
                    final_message = response_stream.get_final_message()

                self.logger.info(f"Introduction generated with Claude: {len(introduction)} chars")
                self._synthesis_model_used = self.model

                # Track usage and costs
                if hasattr(final_message, 'usage'):
                    usage = final_message.usage
                    thinking_tokens = getattr(usage, 'thinking_tokens', 0) if hasattr(usage, 'thinking_tokens') else 0
                    self.cost_tracker.add_usage(
                        model=self.model,
                        input_tokens=usage.input_tokens,
                        output_tokens=usage.output_tokens,
                        thinking_tokens=thinking_tokens
                    )

                # Log API call
                self.logger.log_api_call(
                    api_name="Anthropic Claude",
                    endpoint=self.model,
                    status_code=200,
                    response_time_ms=0
                )

                return introduction.strip()

            except Exception as e:
                # Check if it's a retryable error (network/streaming issues)
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
                    self.logger.error(f"Error generating introduction with Claude: {e}")
                    raise

    def _generate_introduction_with_gemini(self, prompt: str, psalm_number: int, max_tokens: int) -> str:
        """Generate introduction using Gemini 2.5 Pro (1M token context)."""
        from google.genai import types

        self.logger.info(f"Using Gemini 2.5 Pro for introduction (large bundle)")

        client = self._get_gemini_client()

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    import time
                    wait_time = retry_delay * (2 ** (attempt - 1))
                    self.logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {wait_time}s delay...")
                    time.sleep(wait_time)

                response = client.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        thinking_config=types.ThinkingConfig(
                            thinking_budget=8000  # Medium reasoning
                        ),
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(
                            disable=True
                        )
                    )
                )

                introduction = response.text if response.text else ""
                self.logger.info(f"Introduction generated with Gemini 2.5 Pro: {len(introduction)} chars")
                self._synthesis_model_used = "gemini-2.5-pro"

                # Track usage and costs
                if hasattr(response, 'usage_metadata'):
                    usage = response.usage_metadata
                    input_tokens = getattr(usage, 'prompt_token_count', 0) or 0
                    output_tokens = getattr(usage, 'candidates_token_count', 0) or 0
                    thinking_tokens = getattr(usage, 'thoughts_token_count', 0) or 0
                    self.cost_tracker.add_usage(
                        model="gemini-2.5-pro",
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        thinking_tokens=thinking_tokens
                    )

                # Log API call
                self.logger.log_api_call(
                    api_name="Google Gemini",
                    endpoint="gemini-2.5-pro",
                    status_code=200,
                    response_time_ms=0
                )

                return introduction.strip()

            except Exception as e:
                error_msg = str(e).lower()
                is_retryable = any(ind in error_msg for ind in ['429', 'too many requests', 'rate limit', 'try again'])

                if is_retryable and attempt < max_retries - 1:
                    self.logger.warning(f"Retryable Gemini error (attempt {attempt + 1}/{max_retries}): {e}")
                    continue
                else:
                    self.logger.error(f"Error generating introduction with Gemini: {e}")
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
        # Target: ~300K chars max (~170K tokens at 1.75:1 ratio)
        # This leaves room for intro essay + prompt template + macro/micro analysis
        research_text, deep_research_removed, needs_gemini = self._trim_research_bundle(research_bundle, max_chars=300000)

        # Track if deep research was removed for space (could happen here if intro didn't trigger it)
        if deep_research_removed:
            self._deep_research_removed_for_space = True

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

        # Choose model based on bundle size
        if needs_gemini:
            return self._generate_verse_commentary_with_gemini(prompt, psalm_number, max_tokens)
        else:
            return self._generate_verse_commentary_with_claude(prompt, psalm_number, max_tokens)

    def _generate_verse_commentary_with_claude(self, prompt: str, psalm_number: int, max_tokens: int) -> str:
        """Generate verse commentary using Claude Sonnet 4.5."""
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    import time
                    wait_time = retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    self.logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {wait_time}s delay...")
                    time.sleep(wait_time)

                stream = self.client.messages.stream(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

                # Collect response chunks
                commentary = ""
                with stream as response_stream:
                    for chunk in response_stream:
                        if hasattr(chunk, 'type') and chunk.type == 'content_block_delta':
                            if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'type'):
                                if chunk.delta.type == 'text_delta':
                                    commentary += chunk.delta.text

                    # Get final message for usage tracking
                    final_message = response_stream.get_final_message()

                self.logger.info(f"Verse commentary generated with Claude: {len(commentary)} chars")
                self._synthesis_model_used = self.model

                # Track usage and costs
                if hasattr(final_message, 'usage'):
                    usage = final_message.usage
                    thinking_tokens = getattr(usage, 'thinking_tokens', 0) if hasattr(usage, 'thinking_tokens') else 0
                    self.cost_tracker.add_usage(
                        model=self.model,
                        input_tokens=usage.input_tokens,
                        output_tokens=usage.output_tokens,
                        thinking_tokens=thinking_tokens
                    )

                # Log API call
                self.logger.log_api_call(
                    api_name="Anthropic Claude",
                    endpoint=self.model,
                    status_code=200,
                    response_time_ms=0
                )

                return commentary.strip()

            except Exception as e:
                # Check if it's a retryable error (network/streaming issues)
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
                    self.logger.error(f"Error generating verse commentary with Claude: {e}")
                    raise

    def _generate_verse_commentary_with_gemini(self, prompt: str, psalm_number: int, max_tokens: int) -> str:
        """Generate verse commentary using Gemini 2.5 Pro (1M token context)."""
        from google.genai import types

        self.logger.info(f"Using Gemini 2.5 Pro for verse commentary (large bundle)")

        client = self._get_gemini_client()

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    import time
                    wait_time = retry_delay * (2 ** (attempt - 1))
                    self.logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {wait_time}s delay...")
                    time.sleep(wait_time)

                response = client.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        thinking_config=types.ThinkingConfig(
                            thinking_budget=8000  # Medium reasoning
                        ),
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(
                            disable=True
                        )
                    )
                )

                commentary = response.text if response.text else ""
                self.logger.info(f"Verse commentary generated with Gemini 2.5 Pro: {len(commentary)} chars")
                self._synthesis_model_used = "gemini-2.5-pro"

                # Track usage and costs
                if hasattr(response, 'usage_metadata'):
                    usage = response.usage_metadata
                    input_tokens = getattr(usage, 'prompt_token_count', 0) or 0
                    output_tokens = getattr(usage, 'candidates_token_count', 0) or 0
                    thinking_tokens = getattr(usage, 'thoughts_token_count', 0) or 0
                    self.cost_tracker.add_usage(
                        model="gemini-2.5-pro",
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        thinking_tokens=thinking_tokens
                    )

                # Log API call
                self.logger.log_api_call(
                    api_name="Google Gemini",
                    endpoint="gemini-2.5-pro",
                    status_code=200,
                    response_time_ms=0
                )

                return commentary.strip()

            except Exception as e:
                error_msg = str(e).lower()
                is_retryable = any(ind in error_msg for ind in ['429', 'too many requests', 'rate limit', 'try again'])

                if is_retryable and attempt < max_retries - 1:
                    self.logger.warning(f"Retryable Gemini error (attempt {attempt + 1}/{max_retries}): {e}")
                    continue
                else:
                    self.logger.error(f"Error generating verse commentary with Gemini: {e}")
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
                # Handle both legacy string format and new structured dict format
                lexical_phrases = [
                    item['phrase'] if isinstance(item, dict) else item
                    for item in lexical
                ]
                lines.append(f"  Lexical: {', '.join(lexical_phrases)}")

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
