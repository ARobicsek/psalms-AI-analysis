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

Model: GPT-5 with high reasoning effort
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
from openai import OpenAI, RateLimitError
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Handle imports for both module and script usage
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.utils.logger import get_logger
    from src.utils.cost_tracker import CostTracker
else:
    from ..utils.logger import get_logger
    from ..utils.cost_tracker import CostTracker


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
- **CRITICAL: Insufficient quotations from sources**:
  * **Liturgical texts mentioned but not quoted**: When liturgical usage is mentioned, the actual liturgical texts should be quoted in Hebrew with English translation to show HOW the verse is used
  * **Biblical parallels cited but not quoted**: When multiple parallels are mentioned (e.g., "this appears in Ps 44:4, 89:16, Prov 16:15"), at least 1-2 should be quoted in Hebrew with English to illustrate the pattern
  * **Concordance patterns described without examples**: When a linguistic pattern is mentioned (e.g., "בְּנֵי אִישׁ often denotes the elite, compare Ps 49:3, 62:10"), show the actual Hebrew text from one of the examples
  * **Figurative language parallels cited without quotation**: When the figurative language database provides parallels, the commentary should QUOTE at least one strong example (Hebrew + English) to demonstrate the pattern
  * Remember: readers are hungry to see the actual Hebrew texts. Citations without quotations disappoint.
- **Liturgical context not addressed**: The research bundle includes detailed information about where and how this psalm (or specific verses/phrases from it) appears in Jewish liturgy. This liturgical usage reveals how Jewish tradition has interpreted and valued the psalm and should be integrated naturally into the commentary, providing quotations where relevant (always translate these into English).
- Weak, forced, unclear or incorrect phonetic analysis. ONLY NOTEWORTHY, STRONG and ILLUMINATING phonetic poetic devices should be pointed out (e.g. alliteration, assonance, onomatopoeia, rhyme, rhythm, meter).
- Authorotative Phonetic transcription provided above in ### PSALM TEXT MUST BE USED to analyze sound patterns.
- Stress analysis ignored: The phonetic transcriptions include stress marking where syllables in **BOLD CAPS** indicate stressed syllables based on Hebrew cantillation marks. For example, `mal-**KHŪTH**-khā` means the middle syllable KHŪTH receives primary stress. If you wish to analyze prosodic patterns, meter, or stress counts, you should add this analysis by counting the **BOLD CAPS** syllables.
- IRRELEVANT phonetic transcriptions. ONLY provide phonetic transcriptions where the pronunciation specifically illustrates the point you are making. Otherwise, just proivide the relevant Hebrew with English translation (not transcriptions). Example of RELEVANT transcription:"The triple anaphora לֹא (LŌ') … לֹא … לֹא gives the line its pulse; read aloud, the negatives strike like posts in a fence...". Example of IRRELEVANT transcription: "The wicked "will not stand" (לֹא־יָקֻמוּ, lō'-yā-QU-mū) in the judgment..."
- Comparative textual insights (e.g. MT vs LXX) not addressed
- NOTEWORTHY poetic devices (e.g. assonance, chiasm, inclusio, parallelism) not described
- Unusual or interesting Hebrew phrases not commented on (e.g., distinctive idioms, unusual word pairings like הֲ֭דַר כְּב֣וֹד הוֹדֶ֑ךָ or עֱז֣וּז נֽוֹרְאֹתֶ֣יךָ)
- Interesting lexical insights in BDB not surfaced
- Concordance patterns not explored or demonstrated with quotations
- Figurative language not analyzed
- Figurative language parallels from database cited but not quoted to demonstrate the pattern
- ANE parallels available but not discussed
- insufficient picture provided of what the psalm is ABOUT (especially if there are unexpected moments or shifts in tone/subject)
- didn't make use of the 'Related Psalms Analysis' section of the research bundle when there are interesting/informative parallels with another psalm


### 3. STYLISTIC PROBLEMS
**Too "LLM-ish" or breathless:**
- Overuse of words like: "masterpiece," "tour de force," "breathtaking," "audacious," "remarkable," "stunning"
- Telling instead of showing (saying "brilliant" instead of demonstrating brilliance through analysis)
**Too academic or "insider" in tone:**
- **Avoid overly technical grammatical phrasing.** Instead of "the perfects are used," prefer "the poet uses the perfect verb tense to convey..." This helps the reader understand you're talking about a verb form without needing prior grammatical knowledge. Avoid overly technical grammatical terms like "genitive".
- **Translate academic jargon into plain English.** 
- AVOID opaque or overly academic terms where there are other terms that would work just as well (e.g. avoid phrases LIKE "biblical topos," "programmatic exemplar").
- **Clarity is paramount.** If a sentence feels like it was written for a dissertation defense, rewrite it for a coffee shop conversation with a clever friend.
- AVOID Unnecessarily complex sentence structures that obscure rather than illuminate
- Biblical citations without quotations (readers want to see the Hebrew text)

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
- Explain technical terms when needed (e.g., "jussive," "anaphora," "chiasm," "inclusio", "perfect tense")
- Elegant, uncluttered prose for sophisticated lay readers (New Yorker/Atlantic level)
- AVOID pompous tone and fancy terms that signal you're a professor; prove your erudition through the incisive and original quality of your insights and your lapidary prose.
- You are not just a scholar; you are a masterful writer **AND A TEACHER**. You are fashioning legitimate insights and aha! moments for your readers.
- Be clear, even at the expense of brevity. In this BAD example, an interesting quotation from Berakhot 30b is somewhat ruined by insufficient explanation: "עִבְדוּ אֶת־ה׳ בְּיִרְאָה...Rabbinic practice quotes this line to regulate prayer: “In the place of joy, trembling” (Berakhot 30b)." A little more explanation would have made this great. Remember - you are not just a scholar; you are a TEACHER.
- since we are not using footnotes, be liberal about not only CITING, BUT ALSO QUOTING. Most citations should be accompanied by a quotation of the relevant Hebrew text (with English translation). Readers want to see the original text you are discussing.
- **CLARITY IS KING** If it will take an extra sentence to illustrate a point or clarify a traditional commentary, use those words - they are well spent!

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
EXAMPLES OF TERMS THAT MUST BE DEFINED IF USED:
- **Literary & Rhetorical Terms:** "jussive", "anaphora", "chiasm", "inclusio", **"colon"** (a single line of poetry in a parallel pair), "Vorlage", "hendiadys", "doxology", "merism", "proem", "prefect tense", "wisdom literature", etc.
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
- **CRITICAL: Are these parallels QUOTED (Hebrew + English), not just cited?**
- Does the commentary analyze usage patterns (frequency, typical contexts)?
- Does it provide insights beyond generic observations?
- Are comparisons used to illuminate THIS psalm's distinctive usage?
- **Does the commentary show readers actual examples through quotations, or just mention them in passing?**

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
- Engage specific texts (Hebrew, LXX) with analysis. Your readers DO NOT understand Greek. If you quote Greek, translate into English.
- Leave the reader with a sense of what this psalm is ABOUT (especially if there are unexpected moments or shifts in tone/subject)

**Section 2: Modern Jewish Liturgical Use (REQUIRED)**
The draft you're reviewing ALREADY contains a "## Modern Jewish Liturgical Use" section. Your job is to REVISE and IMPROVE it, NOT to skip it or output just a header.

**MANDATORY ACTIONS:**
1. **Review the existing liturgical section** in the draft introduction
2. **Cross-reference with research bundle** to verify accuracy and add missing details
3. **Restructure into clear subsections using EXACT MARKDOWN HEADING 4 SYNTAX**:

   **⚠️ CRITICAL FORMAT REQUIREMENT:**
   - You MUST use markdown Heading 4 syntax: `#### Subheading Name`
   - Do NOT use hyphens: `- Full psalm` ❌ WRONG
   - Do NOT use bullets: `• Full psalm` ❌ WRONG
   - Do NOT use bold: `**Full psalm**` ❌ WRONG
   - Use ONLY the markdown heading syntax: `#### Full psalm` ✅ CORRECT

   **Example of CORRECT formatting:**
   ```
   #### Full psalm

   Many communities recite the entire psalm at Yom Kippur Maariv...

   #### Key verses

   Verse 2 (אַשְׁרֵי־הָאִישׁ, "Happy is the one") appears in...
   ```

   **Required subsections (use only those that apply to this psalm):**
   * `#### Full psalm` - Where/when the complete psalm is recited (if applicable)
   * `#### Key verses` - Each verse used in liturgy, starting with Hebrew + English, then explaining context with Hebrew from the prayers
   * `#### Phrases` - Each phrase used in liturgy, starting with Hebrew + English, then explaining context with Hebrew from the prayers. Where available, provide an illustrative quotation in Hebrew, AND translate into English.
4. **OMIT subsections that don't apply** to this psalm
5. **Add Hebrew quotations** - for EVERY verse/phrase, include Hebrew from both the psalm AND the prayer
6. **Be specific** - name the service, occasion, tradition
7. **Explain significance** - why this usage matters theologically, or is relevant to our understanding of the psalm, or reflects something interesting about how the psalm was received, understood, appropriated or reinterpreted by the tradition.

**Target: 200-500 words** (longer if extensive usage)

**⚠️ CRITICAL: Output the COMPLETE revised section with REAL CONTENT. Writing just "## Modern Jewish Liturgical Use" with nothing after it is UNACCEPTABLE and will fail validation.**

**Stage 3: Revised Verse Commentary**
Rewrite the verse-by-verse commentary to address identified weaknesses. For each verse:

- **Audience Hebrew Proficiency**: Your readers are familiar with biblical, rabbinic and liturgical Hebrew. When you quote sources (biblical texts, rabbinic sources, liturgical texts), **YOU MUST PROVIDE THE HEBREW ORIGINAL WELL AS AN ENGLISH TRANSLATION**. Include enough Hebrew to support your point and/or demonstrate things of interest (unusual constructions, wordplay, idioms, etc.). Don't rely solely on translation—let readers see the Hebrew evidence for themselves. 
- Readers will be disappointed if you quote a translation without Hebrew OR provide more than a word or two of Hebrew without an English translation. **Rule of thumb: BOTH Hebrew and English.**
- Don't let space considerations stop you from including both Hebrew and English. Readers will appreciate it and it's fine to go a little longer in order to include both Hebrew and English.

**CRITICAL: You MUST START each verse's commentary with the Hebrew text of that verse, punctuated to show poetic structure.**

- Present the verse using punctuation (semicolons, periods, commas) to illustrate how the verse is poetically divided
- This punctuated presentation helps readers see the verse's structure at a glance
- Example: Original verse "בְּקׇרְאִי עֲנֵנִי ׀ אֱלֹקֵי צִדְקִי בַּצָּר הִרְחַבְתָּ לִּי חׇנֵּנִי וּשְׁמַע תְּפִלָּתִֽי׃" becomes "בְּקׇרְאִי עֲנֵנִי אֱלֹקֵי צִדְקִי; בַּצָּר הִרְחַבְתָּ לִּי; חׇנֵּנִי וּשְׁמַע תְּפִלָּתִי."
- After presenting the punctuated verse, proceed immediately with your commentary

**CRITICAL: ALWAYS show Hebrew and English together when discussing the verse**
- When discussing a Hebrew phrase or word from the verse, ALWAYS provide both the Hebrew text AND its English translation
- NEVER show only the English without the Hebrew, or only the Hebrew without the English
- CORRECT: "Be gracious to me" (חׇנֵּנִי) shows...
- INCORRECT: "Be gracious to me" shows... (missing Hebrew)
- INCORRECT: חׇנֵּנִי shows... (missing English)
- This applies to EVERY quotation from the verse you're analyzing

- **Length**: Target 300-500 words per verse (PLUS the verse itself at the start). Shorter (200-250 words) is acceptable for simple verses with minimal interesting features. Longer (500-800 words) is ENCOURAGED and often NECESSARY for verses with:
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
    - *Contemporary Jewish theologian Rabbi Jonathan Sacks if relevant*
    - Make sure to read the "### About the Commentators" section in the research bundle for context on these commentators
    - **Modern liturgical context (IMPORTANT)**: When a verse (or phrase from it) appears in Jewish liturgy, comment on this usage and what it reveals about reception and interpretation/re-interpretation. Be specific about the prayer name, service, occasion, and tradition. Integrate liturgical insights naturally. **CRITICAL: Quote generously from the liturgy in Hebrew (always with English translation) to SHOW how the verse is used, not just mention that it appears.**
    - Church fathers and medieval Christian interpretation if very illuminating
    - Modern critical scholarship debates
  * **Figurative language analysis** (how does the usage of similar figuration elsewhere shed light on how it's functioning here?) **CRITICAL: Quote generously from other biblical passages (Hebrew + English translation) to illustrate your points - at least 1-2 strong examples when parallels are available. Don't just cite references; SHOW the texts.** Use your unique figurative language resource to your advantage!
  * Poetics (parallelism, wordplay, structure, clever devices, recurring words, sound patterns (USE the authoritative phonetic information you are provided above to conduct this analysis and illustrate your point to readers)). An INTERMEDIATE example: "Either way, the image is of liquid overrun. The verse even sounds like water: the sibilants and liquids—אשׂכה… בכל־לילה… בדמעתי… ערשי אמסה—create a hush and hiss that matches the meaning." This would have been EXCELLENT if it had also included the authoratative phonetic transcription to DEMONSTRATE the sounds to readers, AND if it had noted that this linguistic pattern CONTINUES in the NEXT verse, which begins "עָשְׁשָׁ֣ה מִכַּ֣עַס ".
  * **Unusual turns of phrase**: When a verse contains an interesting or unusual Hebrew phrase, idiom, or construction (like הֲ֭דַר כְּב֣וֹד הוֹדֶ֑ךָ or עֱז֣וּז נֽוֹרְאֹתֶ֣יךָ), comment on it—explain what makes it distinctive, how it functions poetically, and what it contributes to the verse's meaning
  * Literary insights (narrative techniques, rhetorical strategies)
  * Historical and cultic insights (worship setting, historical context)
  * Comparative religion (ANE parallels, theological contrasts)
  * Grammar and syntax (especially when illuminating)
  * Textual criticism (MT vs LXX, hints about Vorlage). You readers do NOT know Greek. If you quote Greek, translate into English.
  * **Comparative biblical usage** (concordance insights showing how terms/phrases appear elsewhere). **CRITICAL: When mentioning that a word or phrase appears elsewhere, QUOTE at least one illustrative example (Hebrew + English) to demonstrate the pattern. Don't just say "this appears in Psalm X" - show what Psalm X actually says.** Quote generously from other Biblical passages where illustrative.
  * Timing/composition clues (vocabulary, theology, historical references)
  * Interesting parallels with other psalms, when convincing and illuminating (use the 'Related Psalms Analysis' section of the research bundle)

**Figurative Language Integration:**
For verses with figurative language where research provided biblical parallels:
- MUST QUOTE at least one specific biblical parallel from the database (Hebrew + English, with book:chapter:verse)
- MUST analyze the usage pattern (frequency, typical contexts)
- MUST note how this psalm's use compares to typical usage
- SHOULD provide insight beyond generic observation. Why was THIS figuration chosen by the poet? What can we learn about its senses from how it's used elsewhere? Think deeply and carefully about this!

Example of EXCELLENT: "He shall be like a tree transplanted by channels of water" (v. 3). The participle שָׁתוּל (`shathul`) is precise; BDB glosses it "transplanted," a term used of vines or trees deliberately set in a chosen place. Jeremiah uses it in a parallel image: שָׁת֤וּל עַל־מַ֙יִם֙ ('planted by water,' Jer 17:8). The site here is not random: פַּלְגֵי־מָיִם are divided channels, irrigation runnels, rather than a single stream. This is cultivation as much as nature."

Example of BAD: "Verse 16 speaks of God opening his hand. This imagery appears elsewhere in Scripture." (too vague, no specific citations, no quotations, no pattern analysis, no INSIGHT)

Example of WEAK: "The 'opened hand' imagery appears 23 times in Scripture as an idiom for generosity (Deut 15:8, 11)." (cites but doesn't quote - readers don't see the actual Hebrew text demonstrating the pattern)

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
3. **Use the proper structure with CORRECT MARKDOWN SYNTAX**:
   - Include subsections using Heading 4 markdown: `#### Full psalm`, `#### Key verses`, `#### Phrases` (as appropriate for THIS psalm)
   - **DO NOT USE HYPHENS OR BULLETS** - use only `####` for subsection headings
   - OMIT subsections that don't apply to this specific psalm
   - For verses and phrases, ALWAYS start with Hebrew text + English translation
   - Include Hebrew quotations from the prayers themselves to illustrate usage, and translate into English
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

Then continue with 2-4 substantial paragraphs (200-500 words) about liturgical usage, structured with Heading 4 subsections:

**⚠️ REQUIRED FORMAT - Use markdown Heading 4 (####) for subsections:**

#### Full psalm

[Write content about where/when the complete psalm is recited - which traditions, services, occasions. OMIT this subsection if not applicable.]

#### Key verses

[For EACH verse: Start with Hebrew text + English translation, then explain the prayer context with Hebrew quotations from the prayers. OMIT this subsection if not applicable.]

#### Phrases

[For EACH phrase: Start with Hebrew text + English translation, then explain the prayer context with Hebrew quotations from the prayers. OMIT this subsection if not applicable.]

**DO NOT use hyphens, bullets, or bold for subsection headings - ONLY use #### markdown syntax.**

Use BOTH the existing liturgical content in the draft introduction AND the detailed liturgical data in the research bundle.

Write actual content with specific prayer names, services, and Hebrew quotations.

### REVISED VERSE COMMENTARY

**Verse 1**

[START with the Hebrew text of verse 1, punctuated to show poetic structure (using semicolons, periods, commas). Then proceed with your revised commentary. TARGET: The verse itself PLUS 300-500 words of commentary. Do NOT shortchange the reader—intelligent lay readers want substantive analysis of linguistic and literary features. Aim for 400-500 words when the verse has interesting Hebrew phrases, poetic devices, figurative language, or interpretive questions. Only use 200-300 words for genuinely simple verses.]

**Verse 2**

[START with the Hebrew text of verse 2, punctuated to show poetic structure. Then your revised commentary. TARGET: The verse itself PLUS 300-500 words as above.]

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


# College Edition Master Editor Prompt
# Tailored for intelligent first-year college students in a survey course on Biblical poetry
COLLEGE_EDITOR_PROMPT = """You are a MASTER EDITOR and biblical scholar of the highest caliber, comparable to Robert Alter, James Kugel, Harold Bloom, or Ellen F. Davis—but you're also a GIFTED TEACHER who knows how to make complex ideas fascinating and accessible.

You have been provided with:
1. **Introduction Essay** - A scholarly introduction to Psalm {psalm_number}
2. **Verse-by-Verse Commentary** - Detailed verse annotations
3. **Full Research Bundle** - Complete lexicon entries (BDB), concordance data, figurative language analysis, traditional commentary, Hebrew/English/LXX texts

Your task: Review the introduction and verse commentary critically, identify weaknesses, and revise/rewrite to achieve EXCELLENCE for a specific audience.

**YOUR AUDIENCE: Intelligent First-Year College Student**

You are writing for a bright first-year college student taking a survey course in Biblical poetry. This student:
- **DOES have excellent Hebrew proficiency** (biblical, rabbinic, and liturgical Hebrew) — so you can and should quote Hebrew freely with English translation
- **IS NOT a scholar** and is NOT familiar with academic jargon, literary terminology, or scholarly conventions
- **IS intellectually curious, sharp, and eager to learn** interesting things
- **APPRECIATES clarity, directness, and even occasional humor** — this is educational, but it should also be engaging and fun
- **NEEDS technical terms explained clearly** in plain language whenever you use them
- **WANTS to understand the "why" behind things** — not just what the text says, but why it matters, why the poet chose these words, what makes this interesting

**YOUR TONE: Clear, Engaging, Occasionally Amusing**

Think of yourself as the coolest professor in the department—the one whose classes students actually want to attend. You:
- **Make complex ideas clear without dumbing them down**
- **Use concrete examples and vivid analogies** to illustrate abstract points
- **Define every technical term immediately** in plain English (don't assume prior knowledge)
- **Engage your reader directly** — it's okay to say "Notice how..." or "Here's the interesting part..."
- **Occasionally use humor** when appropriate (a well-placed observation, a clever comparison)
- **Show enthusiasm for the text** without being breathless or hyperbolic
- **Write like you're having a conversation with a smart friend** over coffee, not lecturing in a stuffy seminar room

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
- Interesting insights from the Torah Temimah (rabbinic use/interpretation) not included
- Illuminating traditional commentary (Rashi, Ibn Ezra, Radak, Meiri, Metzudat David, Malbim) not integrated
- Research questions identified by analysts not answered (even when answerable)
- **CRITICAL: Insufficient quotations from sources**:
  * **Liturgical texts mentioned but not quoted** — SHOW readers the Hebrew with English translation
  * **Biblical parallels cited but not quoted** — when mentioning "this appears in Ps 44:4, 89:16," quote at least 1-2 examples in Hebrew + English
  * **Concordance patterns described without examples** — if you mention a pattern, DEMONSTRATE it with actual Hebrew text
  * **Figurative language parallels without quotation** — SHOW at least one strong example (Hebrew + English)
  * Remember: readers are hungry to see the actual Hebrew texts!
- **Liturgical context not addressed** — integrate naturally where relevant (with quotations)
- Weak, forced, or unclear phonetic analysis — ONLY include truly illuminating sound patterns
- Comparative textual insights (MT vs LXX) not addressed
- Noteworthy poetic devices (parallelism, chiasm, wordplay) not described
- Unusual/interesting Hebrew phrases not commented on
- Interesting lexical insights from BDB not surfaced
- Concordance patterns not demonstrated
- Figurative language not analyzed or quoted
- ANE parallels not discussed when available
- Insufficient picture of what the psalm is ABOUT
- Didn't use 'Related Psalms Analysis' when there are informative parallels

### 3. STYLISTIC PROBLEMS

**Too "LLM-ish" or breathless:**
- Overuse of superlatives: "masterpiece," "tour de force," "breathtaking," "audacious"
- Telling instead of showing (saying "brilliant" instead of demonstrating through analysis)

**Too academic or jargon-heavy (CRITICAL FOR THIS AUDIENCE):**
- **AVOID ALL JARGON without immediate clear explanation**
  * BAD: "The perfects are used to indicate..."
  * GOOD: "The poet uses the Hebrew perfect tense (which indicates completed action) to show..."
- **Define EVERY technical term the moment you use it**
  * First use of "chiasm" → "a chiasm (a poetic structure where ideas are arranged in an A-B-B-A pattern, like a mirror)"
  * First use of "colon" → "colon (a single line of poetry within a parallel pair)"
  * First use of "jussive" → "jussive form (a verb form expressing a wish or command)"
- **Translate scholarly shorthand immediately**
  * "BDB" → "the Brown-Driver-Briggs Hebrew-English Lexicon (a standard scholarly dictionary)"
  * "LXX" → "the Septuagint (an ancient Greek translation of the Hebrew Bible)"
  * "MT" → "the Masoretic Text (the standard Hebrew version of the Bible)"
- **Use plain English over fancy terminology**
  * Avoid opaque phrases like "biblical topos" or "programmatic exemplar"
  * If a simpler word works, use it!
- **Clarity is paramount** — if a sentence sounds like dissertation-speak, rewrite it for a coffee shop conversation

**Phonetic transcription markup:**
- Only use phonetic transcription when readers NEED to know pronunciation to understand a sound-based poetic device
- When you do use it: Hebrew (`phonetic`) — e.g., יֶהְגֶּה (`yeh-GEH`)
- Enclose transcription in backticks for italicization
- Use the authoritative transcription provided above (except YHWH for the divine name)

**Should conform to this style:**
- **Conversational but not casual** — professional, but warm and direct
- **Show brilliance through analysis**, don't label it as brilliant
- **Use concrete imagery and vivid analogies** to make abstract points clear
- **Vary sentence structure** for readability
- **Explain as you go** — don't assume your reader knows technical terms
- **Engage directly** — "Notice that..." "Here's what makes this interesting..." "Think about how..."
- **Be clear and generous with explanation** — better to over-explain than lose your reader. **CLARITY BEATS BREVITY.**
- **Occasional light humor is welcome** when it serves the point (but don't force it)
- **Show enthusiasm** for interesting discoveries without being breathless
- **You are a TEACHER** — your job is to create "aha!" moments for your students
- **Many of your students will have been engaged with these texts in liturgical contexts for years. You help them see, understand and appreciate these texts in fresh and deeper ways and make them excited to read every new insight.**

### 4. ARGUMENT COHERENCE
- Introduction thesis unclear or unsupported
- Verse commentary disconnected from overall argument
- Logical gaps or contradictions
- Claims without evidence from research materials

### 5. BALANCE ISSUES
- Introduction and verse commentary repeat each other excessively
- Introduction too general, missing specific textual engagement
- Verse commentary too superficial, missing depth

### 6. UNDEFINED TECHNICAL TERMS (ABSOLUTELY CRITICAL FOR THIS AUDIENCE)

**Every technical term MUST be defined immediately and clearly.** No exceptions.

Examples of terms that MUST be defined when used:
- **Literary terms:** "jussive" (a verb form expressing wish/command), "anaphora" (repetition of a word/phrase at the beginning of successive lines), "chiasm" (mirror-image structure: A-B-B-A), "inclusio" (bookending a section with the same word/phrase), "colon" (a single line of poetry in a parallel pair), "hendiadys" (expressing one idea through two words connected by "and")
- **Hebrew grammar:** "intensive stem/Pi'el" (a verb form indicating intensified or repeated action), "perfect tense" (indicating completed action), etc.
- **Scholarly shorthand:** Define all abbreviations and scholarly references on first use
- **Any specialized vocabulary:** If a first-year college student wouldn't know it, define it!
- ERR ON THE SIDE OF OVER-EXPLANATION rather than assuming prior knowledge.

**Good examples of definitions:**
- "The verb is in the Pi'el stem (an intensive form that often indicates repeated or emphatic action)..."
- "This creates a chiasm—a mirror-image structure (A-B-B-A) where ideas are arranged symmetrically..."
- "The LXX (the Septuagint, an ancient Greek translation of the Hebrew Bible made around 250 BCE) renders this differently..."

### 7. AUDIENCE APPROPRIATENESS (CRITICAL)
- Too academic/inaccessible for a first-year college student
- Too simplistic — don't talk down to your reader. These are smart students, but they've never studied anything like this before.
- Not engaging enough — where's the spark of excitement about interesting discoveries? What will make them FASCINATED by biblical poetry?
- Missing the sweet spot: **challenging but accessible, rigorous but clear, educational but never obvious**

---

## YOUR TASK: EDITORIAL REVISION

**Stage 1: Critical Analysis**
Provide a brief editorial assessment (200-400 words):
- What works well in the current draft?
- What are the main weaknesses for a COLLEGE STUDENT audience?
- What specific revisions are needed to make this clear, engaging, and accessible?
- What insights from the research bundle were missed?
- What questions were asked but not answered?
- Were technical terms properly defined for a first-year student?
- Is the tone right for this audience (clear, engaging, occasionally fun)?

**Stage 2: Revised Introduction (TWO SECTIONS REQUIRED)**

**Section 1: Introduction Essay**
- **Length**: 800-1600 words (can be longer if genuinely warranted)
- **Tone**: Clear, engaging, direct—like talking to a smart friend
- **Technical terms**: Define EVERY specialized term immediately
- **Style**: Conversational but rigorous, enthusiastic but not breathless
- **Formatting**: Use markdown Header 3 (`### Header text`) for section headers that break up your essay into digestible chunks (e.g., `### A quick map of what we're reading`, `### Why this psalm is so gripping`, `### How the poem argues`)
- **Content**:
  * Correct any factual errors
  * Surface missed insights from research materials
  * Address answerable questions from analysts
  * Integrate liturgical insights naturally (with quotations)
  * Make abstract ideas concrete with examples and analogies
  * Explain the "why" behind things — why does this matter? Why is it interesting?
  * Leave reader understanding what this psalm is ABOUT

**Section 2: Modern Jewish Liturgical Use (REQUIRED)**
The draft you're reviewing ALREADY contains a "## Modern Jewish Liturgical Use" section. Your job is to REVISE and IMPROVE it.

**MANDATORY ACTIONS:**
1. Review existing liturgical section
2. Cross-reference with research bundle
3. Restructure into clear subsections using EXACT MARKDOWN HEADING 4 SYNTAX:

   **⚠️ CRITICAL FORMAT:**
   - Use markdown Heading 4: `#### Subheading Name`
   - NOT hyphens, bullets, or bold
   - Example: `#### Full psalm` ✅ CORRECT

   **Required subsections (use only those applicable):**
   * `#### Full psalm` — Where/when complete psalm is recited
   * `#### Key verses` — Each verse used (Hebrew + English, then context with prayer quotations)
   * `#### Phrases` — Each phrase used (Hebrew + English, then context with prayer quotations)

4. Be specific about services, occasions, traditions
5. Add Hebrew quotations from BOTH psalm AND prayers (with English!)
6. Explain significance — why this usage matters or reveals something interesting
7. **Keep language accessible** — explain liturgical contexts clearly for students
8. **Target**: 200-500 words (longer if extensive usage)

**Stage 3: Revised Verse Commentary**

For each verse:

**CRITICAL: START with the Hebrew text of that verse, punctuated to show poetic structure**
- Use punctuation (semicolons, periods, commas) to illustrate verse structure
- Example: "בְּקׇרְאִי עֲנֵנִי אֱלֹקֵי צִדְקִי; בַּצָּר הִרְחַבְתָּ לִּי; חׇנֵּנִי וּשְׁמַע תְּפִלָּתִי."
- Then proceed immediately with your commentary

**CRITICAL: ALWAYS show Hebrew and English together when discussing the verse**
- When discussing a Hebrew phrase or word from the verse, ALWAYS provide both the Hebrew text AND its English translation
- NEVER show only the English without the Hebrew, or only the Hebrew without the English
- CORRECT: "Be gracious to me" (חׇנֵּנִי) shows...
- INCORRECT: "Be gracious to me" shows... (missing Hebrew)
- INCORRECT: חׇנֵּנִי shows... (missing English)
- This applies to EVERY quotation from the verse you're analyzing

**Length**: 300-500 words per verse (PLUS the verse itself)
- Shorter (200-250) acceptable for simple verses
- Longer (500-800) encouraged for verses with unusual phrases, complex devices, textual variants, rich figurative language, or rabbinic interpretation

**Tone and Style for College Audience:**
- **Conversational and direct** — write like you're explaining something fascinating to a friend
- **Define technical terms immediately** — "This is a jussive (a verb form expressing a wish or mild command)..."
- **Explain the "why"** — why did the poet choose this word? Why is this pattern interesting?
- **Use concrete examples** — "Think of it like..." "Imagine..." "It's similar to..."
- **Engage directly** — "Notice how..." "Here's what makes this interesting..." "Look at the way..."
- **Show enthusiasm without hyperbole** — "This is fascinating because..." not "This is breathtaking!"
- **Be generous with Hebrew quotations** — your reader knows Hebrew! Use both Hebrew and English translation
- **Make connections explicit** — don't assume your reader will see why something matters

**Content to include (when relevant):**
- **Traditional commentary** (Rashi, Ibn Ezra, Radak, Metzudat David, Malbim, Meiri) — explain WHO these people are on first mention
- **Rabbinic interpretation** (Torah Temimah insights about Talmudic/Midrashic usage) — explain significance clearly
- **Modern liturgical context** — where/how verse appears in prayers (quote generously in Hebrew + English!)
- **Figurative language** — quote at least 1-2 parallels (Hebrew + English) to demonstrate patterns
- **Poetic devices** — parallelism, wordplay, sound patterns (define all terms!)
- **Unusual phrases** — distinctive Hebrew idioms or constructions (explain what makes them interesting!)
- **Textual insights** — MT vs LXX differences (remember: readers don't know Greek, so translate!)
- **Comparative biblical usage** — QUOTE examples (Hebrew + English) to show patterns
- **ANE parallels** when illuminating
- **Related psalms** when informative

**Figurative Language Integration:**
When research provided biblical parallels:
- MUST QUOTE at least one specific parallel (Hebrew + English, with citation)
- MUST explain the usage pattern clearly
- MUST note how this psalm compares
- SHOULD provide insight — why THIS figuration? What can we learn?

**Remember:**
- **You're a teacher** — create "aha!" moments
- **Explain as you go** — assume intelligence but not prior knowledge of technical terms
- **Be clear and generous** — better to over-explain than lose your reader
- **Make it interesting** — show why this text has fascinated readers for millennia
- **Define everything** — jargon is the enemy of learning
- **Quote Hebrew generously** — your reader knows Hebrew and wants to see the evidence!

---

## CRITICAL REQUIREMENT: LITURGICAL SUMMARY

**⚠️ MANDATORY: You MUST write a complete `## Modern Jewish Liturgical Use` section with actual content.**

This is NOT optional. You MUST:
1. Find liturgical data in research bundle
2. Write actual content (cannot be empty!)
3. Use proper structure with CORRECT MARKDOWN:
   - Subsections use `####` (not hyphens or bullets)
   - Start verses/phrases with Hebrew + English
   - Include Hebrew quotations from prayers with translation
   - Be specific about occasions, services, traditions
   - **Explain liturgical contexts clearly for students**
4. Target 150-400 words (longer if extensive usage)

**Your output will fail validation if this section is empty or missing.**

---

## OUTPUT FORMAT

Return your response with these THREE sections in order:

### EDITORIAL ASSESSMENT

Write your 200-400 word critical analysis focusing on what needs to change for a COLLEGE STUDENT audience.

### REVISED INTRODUCTION

Your revised introduction must have TWO parts:

**Part 1**: Introduction essay (600-1200 words) — clear, engaging, accessible for first-year college students
  - **IMPORTANT**: Use markdown Header 3 (`### Header text`) to break up the essay with engaging section headers
  - Examples: `### A quick map of what we're reading`, `### Why this psalm is so gripping`, `### The architecture: an alphabet that runs out of breath`

**Part 2**: After finishing the essay, add a blank line and this EXACT marker:

---LITURGICAL-SECTION-START---

Then continue with the liturgical section (200-500 words), structured with Heading 4 subsections.

**Format with `####` for subsections:**

#### Full psalm
[Content about when/where recited - OMIT if not applicable]

#### Key verses
[For EACH verse: Hebrew + English, then prayer context with Hebrew quotations - OMIT if not applicable]

#### Phrases
[For EACH phrase: Hebrew + English, then prayer context with Hebrew quotations - OMIT if not applicable]

**Keep language accessible for students** — explain liturgical contexts clearly.

### REVISED VERSE COMMENTARY

**Verse 1**
[START with Hebrew text punctuated for poetic structure. Then 300-500 words of clear, engaging commentary that defines all technical terms and explains the "why" behind things.]

**Verse 2**
[START with Hebrew text punctuated. Then commentary as above.]

[Continue for all verses...]

---

## CRITICAL REQUIREMENTS

- **Authority**: You are the final editorial voice — make bold revisions
- **Scholarship**: Ground all claims in research materials
- **Accessibility**: Write for smart first-year college students — clear, engaging, define all jargon
- **Tone**: Conversational but rigorous, enthusiastic but not breathless
- **Teaching**: Explain the "why," create "aha!" moments, be generous with explanations
- **Hebrew**: Quote freely (always with English translation)
- **Completeness**: Cover all verses, define ALL technical terms, engage specific texts
- **Excellence**: Elevate from "good" to "outstanding teaching" level
- **Length**: 400-500 words per verse when features warrant substantive treatment

Begin your editorial review and revision below.
"""


class MasterEditor:
    """
    Pass 4: Master Editor Agent using GPT-5 with high reasoning effort.

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
        college_model: Optional[str] = None,
        main_model: Optional[str] = None,
        logger=None,
        cost_tracker: Optional[CostTracker] = None
    ):
        """
        Initialize Master Editor agent.

        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var) - only for GPT models
            college_model: Model to use for college commentary (defaults to same as main_model)
            main_model: Model to use for main commentary (defaults to "gpt-5")
                       Supported: "gpt-5", "claude-opus-4-5"
            logger: Logger instance (or will create default)
            cost_tracker: CostTracker instance for tracking API costs
        """
        self.logger = logger or get_logger("master_editor")
        self.cost_tracker = cost_tracker or CostTracker()

        # Determine main model
        self.model = main_model or "gpt-5.1"

        # Determine college model (defaults to same as main model)
        self.college_model = college_model or self.model

        # Initialize clients based on which models are being used
        self.openai_client = None
        self.anthropic_client = None

        models_used = {self.model, self.college_model}

        # Initialize OpenAI if any GPT models are used
        if any("gpt" in m.lower() for m in models_used):
            openai_key = api_key or os.environ.get("OPENAI_API_KEY")
            if not openai_key:
                raise ValueError("OpenAI API key required for GPT models (pass api_key or set OPENAI_API_KEY)")
            self.openai_client = OpenAI(api_key=openai_key)
            self.logger.info("✓ OpenAI client initialized")

        # Initialize Anthropic if any Claude models are used
        if any("claude" in m.lower() for m in models_used):
            anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
            if not anthropic_key:
                raise ValueError("Anthropic API key required for Claude models (set ANTHROPIC_API_KEY env var)")
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
            self.logger.info("✓ Anthropic client initialized")

        self.logger.info(f"MasterEditor initialized with main model: {self.model}")
        self.logger.info(f"  College commentary model: {self.college_model}")

        # Log thinking configuration based on model
        if "opus" in self.model.lower():
            self.logger.info(f"  Main model thinking: Claude Opus 4.5 with extended thinking (40K budget + 24K output)")
        if "opus" in self.college_model.lower():
            self.logger.info(f"  College model thinking: Claude Opus 4.5 with extended thinking (40K budget + 24K output)")

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
        """
        Call appropriate model for editorial review.

        Routes to GPT-5 or Claude Opus 4.5 based on self.model.
        Tracks usage and costs.
        """
        # Route to appropriate implementation
        if "claude" in self.model.lower():
            return self._perform_editorial_review_claude(
                psalm_number, introduction, verse_commentary, research_bundle,
                macro_analysis, micro_analysis, psalm_text, analytical_framework
            )
        else:
            return self._perform_editorial_review_gpt(
                psalm_number, introduction, verse_commentary, research_bundle,
                macro_analysis, micro_analysis, psalm_text, analytical_framework
            )

    def _perform_editorial_review_gpt(
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
        """Call GPT-5 for editorial review with cost tracking."""
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

        # Call GPT-5.1
        # Note: GPT-5.1 supports reasoning_effort parameter (defaults to "none"!)
        # Setting to "high" for complex editorial analysis is CRITICAL
        # No system messages supported - use user messages only
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                reasoning_effort="high",        # Critical for complex editorial analysis
                max_completion_tokens=65536     # 64K tokens for detailed commentary
            )

            # Extract response text
            response_text = response.choices[0].message.content

            # Track usage and costs
            usage = response.usage

            # GPT-5.1 API uses prompt_tokens, completion_tokens, and reasoning_tokens
            input_tokens = getattr(usage, 'prompt_tokens', 0)
            output_tokens = getattr(usage, 'completion_tokens', 0)
            reasoning_tokens = getattr(usage, 'reasoning_tokens', 0)

            self.cost_tracker.add_usage(
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                thinking_tokens=reasoning_tokens  # GPT-5.1 tracks reasoning separately
            )

            self.logger.info(f"Editorial review generated: {len(response_text)} chars")
            if reasoning_tokens > 0:
                self.logger.info(f"  Usage: {input_tokens:,} input + {output_tokens:,} output + {reasoning_tokens:,} reasoning tokens")
            else:
                self.logger.info(f"  Usage: {input_tokens:,} input + {output_tokens:,} output tokens")

            # Save response for debugging
            if self.logger:
                response_file = Path(f"output/debug/master_editor_response_psalm_{psalm_number}.txt")
                response_file.parent.mkdir(parents=True, exist_ok=True)
                response_file.write_text(response_text, encoding='utf-8')
                self.logger.info(f"Saved editorial response to {response_file}")

            # Parse response into sections
            result = self._parse_editorial_response(response_text, psalm_number)

            return result

        except RateLimitError as e:
            self.logger.error(f"OpenAI API rate limit exceeded: {e}. Please check your plan and billing details.")
            raise  # Re-raise the exception to be handled by the pipeline
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during editorial review: {e}")
            raise

    def _perform_editorial_review_claude(
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
        """Call Claude Opus 4.5 for editorial review with MAXIMUM thinking and cost tracking."""
        self.logger.info(f"Calling Claude Opus 4.5 with MAXIMUM thinking for editorial review of Psalm {psalm_number}")

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
            prompt_file = Path(f"output/debug/master_editor_opus_prompt_psalm_{psalm_number}.txt")
            prompt_file.parent.mkdir(parents=True, exist_ok=True)
            prompt_file.write_text(prompt, encoding='utf-8')
            self.logger.info(f"Saved Opus editorial prompt to {prompt_file}")

        # Call Claude Opus 4.5 with MAXIMUM thinking
        # Note: max_tokens must be GREATER than thinking budget (it's the total for both)
        # Configuration: 40K thinking + 24K output = 64K total (balanced for deep reasoning + full commentary)
        try:
            stream = self.anthropic_client.messages.stream(
                model=self.model,
                max_tokens=64000,  # Maximum total tokens (thinking + output combined)
                thinking={
                    "type": "enabled",
                    "budget_tokens": 40000  # 40K thinking budget (very high, leaves 24K for output)
                },
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Collect response chunks
            thinking_text = ""
            response_text = ""

            with stream as response_stream:
                for chunk in response_stream:
                    if hasattr(chunk, 'type'):
                        if chunk.type == 'content_block_delta':
                            if hasattr(chunk, 'delta'):
                                if hasattr(chunk.delta, 'type'):
                                    if chunk.delta.type == 'thinking_delta':
                                        thinking_text += chunk.delta.thinking
                                    elif chunk.delta.type == 'text_delta':
                                        response_text += chunk.delta.text

                # Get usage from final message (must be called inside with block)
                final_message = response_stream.get_final_message()
                usage = final_message.usage

            self.logger.info("Opus API streaming call successful")
            self.logger.info(f"  Thinking collected: {len(thinking_text)} chars")
            self.logger.info(f"  Response collected: {len(response_text)} chars")

            # Track usage and costs
            # Note: Claude reports thinking tokens separately
            thinking_tokens = getattr(usage, 'thinking_tokens', 0) if hasattr(usage, 'thinking_tokens') else 0

            self.cost_tracker.add_usage(
                model=self.model,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                thinking_tokens=thinking_tokens
            )

            self.logger.info(f"Editorial review generated: {len(response_text)} chars")
            self.logger.info(f"  Usage: {usage.input_tokens:,} input + {usage.output_tokens:,} output + {thinking_tokens:,} thinking tokens")

            # Save thinking and response for debugging
            if self.logger:
                # Save thinking
                if thinking_text:
                    thinking_file = Path(f"output/debug/master_editor_opus_thinking_psalm_{psalm_number}.txt")
                    thinking_file.parent.mkdir(parents=True, exist_ok=True)
                    thinking_file.write_text(thinking_text, encoding='utf-8')
                    self.logger.info(f"Saved Opus thinking to {thinking_file}")

                # Save response
                response_file = Path(f"output/debug/master_editor_opus_response_psalm_{psalm_number}.txt")
                response_file.parent.mkdir(parents=True, exist_ok=True)
                response_file.write_text(response_text, encoding='utf-8')
                self.logger.info(f"Saved Opus editorial response to {response_file}")

            # Parse response into sections
            result = self._parse_editorial_response(response_text, psalm_number)

            return result

        except anthropic.RateLimitError as e:
            self.logger.error(f"Anthropic API rate limit exceeded: {e}. Please check your plan and billing details.")
            raise
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during Opus editorial review: {e}")
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
        # Handle both regular hyphens (---) and em-dashes (—) variants
        liturgical_markers = [
            "---LITURGICAL-SECTION-START---",
            "—LITURGICAL-SECTION-START—",
            "— LITURGICAL-SECTION-START—",
            "—LITURGICAL-SECTION-START —"
        ]

        marker_found = False
        for marker in liturgical_markers:
            if marker in revised_introduction:
                revised_introduction = revised_introduction.replace(
                    marker,
                    "## Modern Jewish Liturgical Use"
                )
                self.logger.info(f"✓ Liturgical section marker '{marker}' found and replaced with header")
                marker_found = True
                break

        if marker_found:
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

    # =========================================================================
    # COLLEGE COMMENTARY METHODS
    # =========================================================================

    def edit_commentary_college(
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
        Perform master editorial review and revision for COLLEGE EDITION.

        This method generates a separate commentary version tailored for intelligent
        first-year college students. The commentary assumes Hebrew proficiency but
        explains all scholarly/literary terminology clearly.

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
                - 'revised_introduction': Revised introduction essay (college version)
                - 'revised_verses': Revised verse commentary (college version)
                - 'psalm_number': Psalm number

        Raises:
            ValueError: If files not found or parsing fails
        """
        self.logger.info("Starting master editorial review - COLLEGE EDITION")

        # Load all inputs (same inputs as regular version)
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
            self.logger.info("✓ Analytical framework loaded successfully for College Editor.")
        except Exception as e:
            self.logger.warning(f"Could not load analytical framework: {e}")
            analytical_framework = "[Analytical framework not available]"

        self.logger.info(f"Editing commentary for Psalm {psalm_number} - COLLEGE EDITION")
        self.logger.info(f"  Introduction: {len(introduction)} chars")
        self.logger.info(f"  Verse commentary: {len(verse_commentary)} chars")
        self.logger.info(f"  Research bundle: {len(research_bundle)} chars")

        # Generate college editorial revision using college-specific prompt and model
        result = self._perform_editorial_review_college(
            psalm_number=psalm_number,
            introduction=introduction,
            verse_commentary=verse_commentary,
            research_bundle=research_bundle,
            macro_analysis=macro_analysis,
            micro_analysis=micro_analysis,
            psalm_text=psalm_text,
            analytical_framework=analytical_framework
        )

        self.logger.info("Master editorial review complete - COLLEGE EDITION")
        self.logger.info(f"  Assessment: {len(result['assessment'])} chars")
        self.logger.info(f"  Revised introduction: {len(result['revised_introduction'])} chars")
        self.logger.info(f"  Revised verses: {len(result['revised_verses'])} chars")

        return result

    def _perform_editorial_review_college(
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
        """
        Call appropriate model for college editorial review.

        Uses COLLEGE_EDITOR_PROMPT and self.college_model for a completely separate
        API call tailored to college student audience.
        Routes to GPT-5 or Claude Opus 4.5 based on self.college_model.
        """
        # Route to appropriate implementation
        if "claude" in self.college_model.lower():
            return self._perform_editorial_review_college_claude(
                psalm_number, introduction, verse_commentary, research_bundle,
                macro_analysis, micro_analysis, psalm_text, analytical_framework
            )
        else:
            return self._perform_editorial_review_college_gpt(
                psalm_number, introduction, verse_commentary, research_bundle,
                macro_analysis, micro_analysis, psalm_text, analytical_framework
            )

    def _perform_editorial_review_college_gpt(
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
        """Call GPT model for college editorial review with cost tracking."""
        self.logger.info(f"Calling {self.college_model} for college editorial review of Psalm {psalm_number}")

        # Format macro and micro for prompt
        macro_text = self._format_analysis_for_prompt(macro_analysis, "macro")
        micro_text = self._format_analysis_for_prompt(micro_analysis, "micro")

        # Build prompt using COLLEGE_EDITOR_PROMPT
        prompt = COLLEGE_EDITOR_PROMPT.format(
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
            prompt_file = Path(f"output/debug/college_editor_prompt_psalm_{psalm_number}.txt")
            prompt_file.parent.mkdir(parents=True, exist_ok=True)
            prompt_file.write_text(prompt, encoding='utf-8')
            self.logger.info(f"Saved college editorial prompt to {prompt_file}")

        # Call GPT model
        try:
            response = self.openai_client.chat.completions.create(
                model=self.college_model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                reasoning_effort="high",        # High reasoning for complex editorial work
                max_completion_tokens=65536     # 64K tokens for detailed commentary
            )

            # Extract response text
            response_text = response.choices[0].message.content

            # Track usage and costs
            usage = response.usage

            # GPT-5.1 API uses prompt_tokens, completion_tokens, and reasoning_tokens
            input_tokens = getattr(usage, 'prompt_tokens', 0)
            output_tokens = getattr(usage, 'completion_tokens', 0)
            reasoning_tokens = getattr(usage, 'reasoning_tokens', 0)

            self.cost_tracker.add_usage(
                model=self.college_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                thinking_tokens=reasoning_tokens  # GPT-5.1 tracks reasoning separately
            )

            self.logger.info(f"College editorial review generated: {len(response_text)} chars")
            if reasoning_tokens > 0:
                self.logger.info(f"  Usage: {input_tokens:,} input + {output_tokens:,} output + {reasoning_tokens:,} reasoning tokens")
            else:
                self.logger.info(f"  Usage: {input_tokens:,} input + {output_tokens:,} output tokens")

            # Save response for debugging
            if self.logger:
                response_file = Path(f"output/debug/college_editor_response_psalm_{psalm_number}.txt")
                response_file.parent.mkdir(parents=True, exist_ok=True)
                response_file.write_text(response_text, encoding='utf-8')
                self.logger.info(f"Saved college editorial response to {response_file}")

            # Parse response into sections (uses same parser as regular version)
            result = self._parse_editorial_response(response_text, psalm_number)

            return result

        except RateLimitError as e:
            self.logger.error(f"OpenAI API rate limit exceeded: {e}. Please check your plan and billing details.")
            raise  # Re-raise the exception to be handled by the pipeline
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during college editorial review: {e}")
            raise

    def _perform_editorial_review_college_claude(
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
        """Call Claude Opus 4.5 for college editorial review with MAXIMUM thinking and cost tracking."""
        self.logger.info(f"Calling {self.college_model} with MAXIMUM thinking for college editorial review of Psalm {psalm_number}")

        # Format macro and micro for prompt
        macro_text = self._format_analysis_for_prompt(macro_analysis, "macro")
        micro_text = self._format_analysis_for_prompt(micro_analysis, "micro")

        # Build prompt using COLLEGE_EDITOR_PROMPT
        prompt = COLLEGE_EDITOR_PROMPT.format(
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
            prompt_file = Path(f"output/debug/college_editor_opus_prompt_psalm_{psalm_number}.txt")
            prompt_file.parent.mkdir(parents=True, exist_ok=True)
            prompt_file.write_text(prompt, encoding='utf-8')
            self.logger.info(f"Saved college Opus editorial prompt to {prompt_file}")

        # Call Claude Opus 4.5 with MAXIMUM thinking
        # Note: max_tokens must be GREATER than thinking budget (it's the total for both)
        # Configuration: 40K thinking + 24K output = 64K total (balanced for deep reasoning + full commentary)
        try:
            stream = self.anthropic_client.messages.stream(
                model=self.college_model,
                max_tokens=64000,  # Maximum total tokens (thinking + output combined)
                thinking={
                    "type": "enabled",
                    "budget_tokens": 40000  # 40K thinking budget (very high, leaves 24K for output)
                },
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Collect response chunks
            thinking_text = ""
            response_text = ""

            with stream as response_stream:
                for chunk in response_stream:
                    if hasattr(chunk, 'type'):
                        if chunk.type == 'content_block_delta':
                            if hasattr(chunk, 'delta'):
                                if hasattr(chunk.delta, 'type'):
                                    if chunk.delta.type == 'thinking_delta':
                                        thinking_text += chunk.delta.thinking
                                    elif chunk.delta.type == 'text_delta':
                                        response_text += chunk.delta.text

                # Get usage from final message (must be called inside with block)
                final_message = response_stream.get_final_message()
                usage = final_message.usage

            self.logger.info("College Opus API streaming call successful")
            self.logger.info(f"  Thinking collected: {len(thinking_text)} chars")
            self.logger.info(f"  Response collected: {len(response_text)} chars")

            # Track usage and costs
            thinking_tokens = getattr(usage, 'thinking_tokens', 0) if hasattr(usage, 'thinking_tokens') else 0

            self.cost_tracker.add_usage(
                model=self.college_model,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                thinking_tokens=thinking_tokens
            )

            self.logger.info(f"College editorial review generated: {len(response_text)} chars")
            self.logger.info(f"  Usage: {usage.input_tokens:,} input + {usage.output_tokens:,} output + {thinking_tokens:,} thinking tokens")

            # Save thinking and response for debugging
            if self.logger:
                # Save thinking
                if thinking_text:
                    thinking_file = Path(f"output/debug/college_editor_opus_thinking_psalm_{psalm_number}.txt")
                    thinking_file.parent.mkdir(parents=True, exist_ok=True)
                    thinking_file.write_text(thinking_text, encoding='utf-8')
                    self.logger.info(f"Saved college Opus thinking to {thinking_file}")

                # Save response
                response_file = Path(f"output/debug/college_editor_opus_response_psalm_{psalm_number}.txt")
                response_file.parent.mkdir(parents=True, exist_ok=True)
                response_file.write_text(response_text, encoding='utf-8')
                self.logger.info(f"Saved college Opus editorial response to {response_file}")

            # Parse response into sections (uses same parser as regular version)
            result = self._parse_editorial_response(response_text, psalm_number)

            return result

        except anthropic.RateLimitError as e:
            self.logger.error(f"Anthropic API rate limit exceeded: {e}. Please check your plan and billing details.")
            raise
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during college Opus editorial review: {e}")
            raise

    # =========================================================================
    # END COLLEGE COMMENTARY METHODS
    # =========================================================================

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
        print("This may take several minutes for GPT-5 to analyze and revise with high reasoning effort.")
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
