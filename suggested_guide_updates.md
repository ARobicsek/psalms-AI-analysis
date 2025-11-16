# Suggested Updates to "How Psalms Readers Guide Works"

## Overview
This document suggests additions and modifications to reflect enhancements made between October 2024 and November 2025 (Sessions 105-122). Suggestions maintain the original document's friendly, explanatory voice for educated lay readers.

---

## SECTION 1: Updates to "How the System Works"

### Current Text (to modify):
> "This is accomplished using four Large Language Model (LLM) agents working in series, aided by seven digital 'librarians' with research tool access covering lexicons, concordances, figurative language, traditional commentaries, and liturgical usage."

### Suggested Revision:
> "This is accomplished using four Large Language Model (LLM) agents working in series, aided by eight digital 'librarians' with research tool access covering lexicons, concordances, figurative language, traditional commentaries, liturgical usage, **and related psalm connections**."

**Rationale**: Session 107 added the Related Psalms Librarian as an eighth librarian component.

---

## SECTION 2: New Subsection to Add After "Stage 2: Second Agent - Micro Analysis"

### Insert New Stage:

**Stage 2.5: Related Psalms Research**

Before the research librarians begin their work, a specialized 'Related Psalms Librarian' identifies the top five most closely related psalms based on shared linguistic patterns. This librarian draws on a comprehensive statistical analysis of all 150 psalms, examining:

- **Shared roots**: Hebrew word roots that appear in both psalms (weighted by distinctiveness—rare roots count more than common ones)
- **Shared phrases**: Multi-word expressions that appear verbatim in both texts
- **Skipgrams**: Patterns where the same words appear in the same sequence, even when not adjacent (e.g., "light of your face" appearing as "light... your face")

The system uses inverse document frequency (IDF) scoring to prioritize distinctive connections. A rare root appearing in only a handful of psalms signals a stronger thematic link than a ubiquitous word like "LORD." The librarian retrieves the full text and pattern details for these related psalms, which are then incorporated into the research bundle. This allows the Synthesis Writer to note intertextual connections and echoes—for instance, how Psalm 25's theme of trust amid enemies resonates with Psalm 34's similar vocabulary and structure.

**Rationale**: Sessions 106-119 developed this entire subsystem, which is now a core feature of the pipeline. This addition:
- Explains the Related Psalms Librarian (Session 107)
- Describes the V6 statistical analysis (Session 117)
- Notes the top 5 limit (Session 119)
- Introduces key concepts (roots, phrases, skipgrams, IDF scoring)
- Maintains the accessible voice of the original document

---

## SECTION 3: Updates to "Stage 3: Research Assembly"

### Current Text:
> "This stage operates automatically without using language models (except for liturgical summarization, which uses Claude Haiku 4.5), ensuring consistent and comprehensive data collection."

### Suggested Addition (append to end of paragraph):
> "The assembly now includes the related psalms data identified in Stage 2.5, providing the Synthesis Writer with cross-textual connections to draw upon. To optimize processing costs, the system filters the related psalms data to focus on the most meaningful connections: only roots with high distinctiveness scores (IDF ≥ 1) are included, and skipgrams receive modest penalties based on the number of intervening words, prioritizing tighter linguistic patterns."

**Rationale**: Sessions 118-119 implemented significant token optimizations. This addition:
- Notes the inclusion of related psalms in the research bundle
- Explains the IDF filtering (Session 119)
- Mentions the gap penalty system (Session 105)
- Keeps the explanation accessible without overwhelming technical detail

---

## SECTION 4: Updates to "Stage 4: Third Agent – Synthesis Writer"

### Current Text:
> "This agent (Claude Sonnet 4.5) receives the output of the prior three stages (including the research bundle) and is instructed to create a coherent commentary. It drafts an introductory essay (800–1200 words) and detailed verse-by-verse commentary (150–400 words per verse), integrating all the research materials into a unified scholarly narrative."

### Suggested Revision:
> "This agent (Claude Sonnet 4.5) receives the output of the prior stages (including the research bundle) and is instructed to create a coherent commentary. It drafts an introductory essay (800–1200 words) and detailed verse-by-verse commentary (150–400 words per verse), integrating all the research materials into a unified scholarly narrative. **The agent is specifically instructed to quote generously from its sources—when mentioning biblical parallels, liturgical contexts, or traditional commentaries, it provides the actual Hebrew texts with English translations rather than mere citations. This 'show, don't just tell' approach lets readers see the textual evidence directly.**

**Additionally, each verse's commentary begins with the Hebrew text of that verse, punctuated to show its poetic structure. The agent uses semicolons, periods, and commas to reveal how the verse naturally divides into cola (poetic lines), helping readers immediately grasp the verse's architecture before diving into the analysis.**"

**Rationale**:
- Session 122 implemented major enhancements to encourage quotations from sources—this is a significant user-facing improvement worth highlighting
- Session 121 changed to LLM-provided poetically punctuated verses—another visible enhancement to the final product
- Both changes improve the reader experience and deserve mention

---

## SECTION 5: Updates to "Stage 5: Fourth Agent - Editorial Review"

### Current Text:
> "This agent (GPT-5) receives the output of all the prior stages, typically amounting to 150,000 characters or more."

### Suggested Revision:
> "This agent (GPT-5) receives the output of all the prior stages, typically amounting to **up to 350,000 characters** (roughly 175,000 tokens)."

**Rationale**: Session 109 increased the synthesis editor character limit to 700,000 characters. The editor receives roughly half of that (the synthesis writer's output). This reflects the system's current capacity.

---

## SECTION 6: New Subsection to Add Under "Sources Available to the System"

### Insert After "Comparative Materials":

**Intertextual Psalm Connections**

Custom statistical database analyzing linguistic patterns across all 11,175 psalm pairs (every possible combination of the 150 psalms)

Pattern types tracked:
- Shared Hebrew roots with inverse document frequency (IDF) scores measuring distinctiveness
- Contiguous multi-word phrases (2-6 words)
- Skipgram patterns (non-adjacent word sequences)

Quality filtering to exclude formulaic patterns (e.g., "Psalm of David" headers)

Top 550 strongest connections identified for research use

Scoring system incorporating:
- Gap penalties favoring tighter patterns
- Content word bonuses promoting semantically rich connections
- IDF weighting emphasizing distinctive over ubiquitous vocabulary

**Rationale**: Sessions 105-117 built this entire analytical infrastructure (V6 system). It's now a core component of the system's capabilities and deserves documentation alongside other sources. This addition:
- Describes the scope (all psalm pairs)
- Explains the three pattern types
- Notes the quality filtering (Sessions 111, 113)
- Mentions the scoring sophistication (Sessions 105, 111, 118-119)
- Maintains accessible language

---

## SECTION 7: Technical Detail Enhancement (Optional Addition)

### Suggested New Subsection (before "Examples of Analysis"):

**Technical Note: Morphological Analysis**

The system's ability to identify shared roots across psalms depends on sophisticated Hebrew morphological analysis. Hebrew words wear their grammar on the outside: prefixes mark prepositions, suffixes indicate possession or gender, and internal vowel patterns distinguish verb forms. To find shared roots, the system must strip away this grammatical clothing.

For example, the word וּבְתוֹרָתוֹ (uv'torato, "and in his teaching") must be analyzed to extract the root תור (torah/teaching):
- Strip the conjunction prefix וּ ("and")
- Strip the preposition prefix בְּ ("in")
- Strip the possessive suffix וֹ ("his")
- Identify the remaining root: תור

The system uses a multi-layered approach: it first consults a cache of 5,353 morphological mappings from the ETCBC BHSA 2021 scholarly database, which provides expert analysis of every word in the Psalms. When it encounters words from other biblical books, it applies sophisticated fallback algorithms that handle:

- **Hybrid stripping strategies**: Different prefix/suffix removal orders for different word patterns
- **Plural protection**: Recognizing when ים or ות endings are integral to a word rather than plural markers
- **Final letter normalization**: Converting letters to their proper word-final forms (ך → כ, ם → מ, ן → נ, ף → פ, ץ → צ)

This morphological precision ensures that the system identifies genuine thematic connections rather than superficial string matches.

**Rationale**: Sessions 105, 112-117 involved extensive morphological improvements that are technically sophisticated and intellectually interesting. This optional addition:
- Explains a key technical challenge in accessible terms
- Provides a concrete example
- Notes the ETCBC scholarly resource (Session 105)
- Mentions the sophisticated algorithms (Sessions 115-117)
- Could appeal to readers interested in the "under the hood" workings
- Is marked optional because it adds technical depth the original document intentionally kept light

---

## SECTION 8: Suggested Date Correction

### Current Text:
> "October 21, 2025"

### Suggested Revision:
> "October 21, 2024 (Updated November 2025)"

**Rationale**: The original date is likely a typo. If updates are incorporated, noting the update date maintains transparency.

---

## SECTION 9: Additional Example Enhancement (Optional)

### Suggested Addition to Examples Section:

Consider adding a brief example showing the **related psalms** feature in action. After your Psalm 2:11 example, you could add:

**Cross-Psalm Connections: Psalms 25 and 34**

The system's statistical analysis identifies Psalm 34 as one of the most closely related to Psalm 25, sharing distinctive roots and phrases that suggest common themes. Both psalms use the relatively rare root בוש (shame/disappointment) in contexts of trust:

- Psalm 25:2-3: "אֱלֹקַי בְּךָ בָטַחְתִּי אַל־אֵבוֹשָׁה... כֹּל קוֶֹיךָ לֹא יֵבֹשׁוּ" ("My God, I trust in You; let me not be disappointed... none who look to You are disappointed")
- Psalm 34:6: "הִבִּיטוּ אֵלָיו וְנָהָרוּ וּפְנֵיהֶם אַל־יֶחְפָּרוּ" ("Look to Him and be radiant; your faces shall not be shamed")

This connection between psalms of trust and deliverance helps readers see how the Psalter develops recurring theological vocabulary across different compositions.

**Rationale**: This would demonstrate the related psalms feature (Sessions 106-119) in the same accessible, example-driven style as the rest of the document. It shows readers what this feature adds to their understanding.

---

## Summary of Suggested Changes

1. **Update "four librarians" to "eight librarians"** (added Related Psalms Librarian)
2. **Add Stage 2.5** explaining related psalms research
3. **Enhance Stage 3** to mention related psalms data and optimization
4. **Enhance Stage 4** to highlight quotation emphasis and poetic punctuation
5. **Update Stage 5** with increased character capacity
6. **Add new source category** documenting the intertextual psalm connections database
7. **Optional: Add technical note** on morphological analysis for interested readers
8. **Fix date** and note update
9. **Optional: Add example** showing related psalms feature

All suggestions maintain the document's friendly, accessible voice while accurately reflecting the system's current capabilities and recent enhancements.
