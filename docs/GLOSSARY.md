# Project Glossary

**Purpose**: Definitions of project-specific technical terms used throughout the Psalms Commentary Pipeline documentation.

**Last Updated**: 2025-10-24

---

## A

### Agent
A software component that performs a specific analytical or data retrieval task. Agents fall into two categories:
- **AI Agents**: LLM-powered components (MacroAnalyst, MicroAnalyst, SynthesisWriter, MasterEditor) that perform complex analysis
- **Librarian Agents**: Deterministic Python scripts (BDB, Concordance, Figurative, Commentary) that retrieve data without making LLM calls

---

## B

### Begadkefat
A set of six Hebrew consonants (ב ג ד כ פ ת) that change pronunciation based on the presence or absence of dagesh:
- **With dagesh (hard)**: b, g, d, k, p, t
- **Without dagesh (soft)**: v, gh, dh, kh, f, th

**Example**: בַּיִת (ba-yit, "house") has hard **b**, while אֵיבָה (ē-vāh, "enmity") has soft **v**.

**Why it matters**: Critical for accurate phonetic transcription and analysis of sound patterns in Hebrew poetry.

---

## C

### Consonantal Search
One of four concordance search modes that strips all vowel points and cantillation marks, searching only consonantal text. This is the **default and most useful mode** for thematic analysis.

**Example**: Searching שמר (consonantal) finds שָׁמַר, שֹׁמֵר, שׁוֹמְרִים, etc.

**Why it matters**: Hebrew vowel points were added centuries after composition. Consonantal search captures all thematic uses of a root regardless of grammatical form.

See also: Exact Search, Voweled Search, Lemma Search

---

## E

### Exact Search
The most restrictive concordance search mode that preserves all diacritics, including cantillation marks.

**When to use**: Only when you need to find a specific morphological form with a particular stress pattern.

See also: Consonantal Search, Voweled Search, Lemma Search

---

## F

### Figurative Language Database
A pre-analyzed SQLite database containing 2,863+ figurative language instances from the Psalms (and 8,373 verses from Psalms + Pentateuch total). Each instance includes:
- **Target**: What is being described (e.g., "God", "righteous person")
- **Vehicle**: The image used (e.g., "shepherd", "rock", "light")
- **Ground**: The shared attributes that justify the comparison
- **Type**: Metaphor, simile, personification, etc.

**Example**: Psalm 23:1 — Target: "Divine care", Vehicle: "Shepherd", Ground: "Protective guidance and provision"

**How it's used**: The FigurativeLibrarian queries this database during the research phase to find parallel figurative uses across Scripture, enriching commentary with intertextual connections.

**Location**: `C:\Users\ariro\OneDrive\Documents\Bible\database\Pentateuch_Psalms_fig_language.db`

---

## G

### Gemination
Consonant doubling indicated by dagesh forte (a dot inside a Hebrew letter). The geminated consonant is **ambisyllabic**—it simultaneously closes one syllable and opens the next.

**Examples**:
- **חַנּוּן** → khan-nūn (the doubled נ splits across syllables)
- **הַלְלוּיָהּ** → hal-lū-yāh (the doubled ל splits across syllables)

**Detection rules**:
1. Non-begadkefat letters with dagesh → always gemination
2. Begadkefat letters with dagesh in post-vocalic position → gemination
3. Word-initial begadkefat + dagesh → hardening only (NOT gemination)

**Why it matters**: Affects syllable structure and stress patterns critical for analyzing Hebrew meter and rhythm.

---

## L

### Lemma Search
A concordance search mode that looks for the dictionary form (lemma) of a word, finding all grammatical variations.

**Example**: Searching the lemma שָׁמַר finds all conjugations and inflections of "guard/keep" regardless of tense, number, or person.

**Technical note**: Requires morphological tagging data (Strong's numbers or OSHB morphhb database).

See also: Consonantal Search, Voweled Search, Exact Search

### Librarian Agent
A **deterministic Python script** that retrieves data from databases or APIs **without making LLM calls**. This is a core architectural decision to ensure:
- **Speed**: No API latency for data retrieval
- **Cost efficiency**: ~$0.15 saved per psalm
- **Accuracy**: 100% reliable data (no hallucination risk)

**The five librarians**:
1. **BDBLibrarian**: Hebrew lexicon lookups (Sefaria API)
2. **ConcordanceLibrarian**: Hebrew concordance searches (local SQLite DB)
3. **FigurativeLibrarian**: Figurative language database queries (local SQLite DB)
4. **CommentaryLibrarian**: Classical Jewish commentaries (Sefaria API)
5. **ResearchAssembler**: Coordinates all librarians and formats results

**Contrast with AI Agent**: Librarians perform deterministic data retrieval; AI agents perform creative analysis and synthesis.

---

## M

### Macro Analysis
The **first pass** of the telescopic pipeline, performed by the MacroAnalyst agent (Claude Sonnet 4.5). Analyzes the psalm at the chapter level to establish:
- **Genre** (lament, praise, wisdom, royal, etc.)
- **Emotional arc** (e.g., despair → trust → praise)
- **Structural divisions** (stanzas, refrains, inclusios)
- **Central thesis** (a specific, non-generic statement of what the psalm is about)
- **Poetic architecture** (how the parts create the whole)

**Example thesis** (Psalm 29): "A liturgical polemic that systematically transfers Baal's storm-god attributes to YHWH."

**Purpose**: Prevents verse-by-verse analysis from becoming disconnected generic paraphrasing by establishing a controlling framework.

See also: Micro Analysis, Telescopic Analysis

### Maqqef
The Hebrew word joiner (־, Unicode U+05BE), similar to a hyphen, that connects two or more words into a single **prosodic unit** or **stress domain**.

**Key linguistic principle**: Maqqef creates **ONE ACCENT DOMAIN**. Only the final word in a maqqef compound receives the primary stress.

**Examples**:
- **אֶת־יָדֶךָ** → et-yā-dhe-khā (one stress on final syllable)
- **לְכׇל־הַנֹּפְלִים** → lə-khol-han-nō-fə-LIY-m (one stress on final word)

**Why it matters**: Critical for accurate stress counting and meter analysis. Words joined by maqqef do not receive independent stresses.

**Implementation**: The PhoneticAnalyst handles maqqef compounds specially, transcribing each component but only marking stress on the final word.

### MasterEditor
The **fourth pass** of the pipeline, using **GPT-5** (or GPT-5) for final editorial review. Acts as a rigorous critic and reviser with the persona of "a biblical scholar of the highest caliber, akin to Robert Alter or James Kugel."

**Key responsibilities**:
1. **Factual verification**: Checks all claims against research data
2. **Phonetic accuracy**: Verifies sound pattern claims against authoritative transcriptions
3. **Missed opportunities**: Identifies overlooked insights from research bundle
4. **Style refinement**: Elevates prose to "National Book Award" quality
5. **Coherence check**: Ensures arguments flow logically

**Example correction**: If SynthesisWriter claims "alliteration of 'f' sounds" but the phonetic transcription shows 'p' sounds, MasterEditor flags and corrects it.

**Why this role matters**: Prevents the accumulation of small errors that would undermine scholarly credibility. Acts as the "MASTER EDITOR" imposing final quality control before publication.

### Micro Analysis
The **second pass** of the telescopic pipeline, performed by the MicroAnalystV2 agent (Claude Sonnet 4.5). Takes a **curiosity-driven** approach to verse-by-verse analysis:

**Process**:
1. **Discovery Pass**: Examines each verse for linguistic puzzles, surprising imagery, and poetic devices
2. **Research Request Generation**: Based on discoveries, generates detailed requests for the Librarian agents
   - Lexicon requests (BDB entries for key Hebrew words)
   - Concordance searches (word usage patterns across Scripture)
   - Figurative language checks (metaphor/simile parallel passages)
   - Commentary requests (traditional interpretive perspectives)

**Design philosophy**: The MicroAnalyst deliberately keeps the macro thesis in "peripheral vision only" to avoid confirmation bias. This allows it to discover evidence that might challenge or refine the initial thesis.

**Example research requests** (Psalm 29): 31 lexicon entries, 7 concordance searches, 11 figurative language checks, 4 commentary requests.

See also: Macro Analysis, Research Bundle

---

## P

### Pass
One stage in the **five-pass pipeline architecture**. Each pass is a complete analytical step performed by a specialized agent:

**Pass 1**: MacroAnalyst - Chapter-level thesis and structure
**Pass 2**: MicroAnalystV2 - Verse-level discoveries and research generation
**Pass 3**: SynthesisWriter - Integration and final commentary writing
**Pass 4**: MasterEditor - Editorial review and quality enhancement
**Pass 5**: CommentaryFormatter - Print-ready formatting (Python, not an AI agent)

**Why "pass" terminology**: Each stage makes a complete "pass" through the psalm, building on previous work while maintaining a distinct focus.

**Historical note**: Originally planned as a 5-pass system (Macro → Micro → Synthesis → Critic → FinalPolisher), but the quality of Pass 3 output made Passes 4-5 redundant. The current implementation uses a different Pass 4 (MasterEditor with GPT-5) for final quality control.

### Phonetic Transcription
The conversion of Hebrew text into a phonetic representation using **reconstructed Biblical Hebrew pronunciation** (not modern Israeli pronunciation). Includes:
- Consonant sounds (including begadkefat distinctions)
- Vowel sounds (long and short)
- Syllable breaks (hyphenated: bə-rē-shīt)
- Stress marking (UPPERCASE + bold: bə-**RĒ**-shīt)

**Key features**:
- Uses dagesh to distinguish hard/soft sounds (b/v, k/kh, p/f, etc.)
- Transcribes divine name as "a-dō-nāy" (liturgical reading)
- Marks gemination (doubled consonants)
- Handles maqqef compounds as single prosodic units

**Example**: פּוֹתֵחַ אֶת־יָדֶךָ → pō-**TĒ**-akh et-yā-dhe-**KHĀ**

**Why it matters for commentary**: Enables precise analysis of sound patterns, alliteration, assonance, and meter—critical features of Hebrew poetry that are invisible in English translation.

**Implementation**: The PhoneticAnalyst agent (Python) performs deterministic phonetic transcription based on linguistic rules from Gesenius' Hebrew Grammar.

---

## R

### Research Bundle
A comprehensive, structured document (formatted as Markdown) containing all the data retrieved by the Librarian agents during Pass 2. Assembled by the ResearchAssembler and provided to the SynthesisWriter for commentary writing.

**Contents**:
1. **Hebrew Lexicon Entries**: BDB and Klein dictionary definitions with etymology and semantic ranges
2. **Concordance Searches**: Word usage patterns across Scripture with context
3. **Figurative Language Instances**: Parallel metaphors, similes, and imagery from the database
4. **Classical Commentaries**: Traditional Jewish interpretive perspectives (Rashi, Ibn Ezra, etc.)
5. **Phonetic Transcriptions**: Stress-marked phonetic data for sound pattern analysis

**Format**: Markdown with hierarchical structure (##, ###) optimized for LLM parsing.

**Size**: Typically 20,000-40,000 tokens, intelligently trimmed if necessary to fit within context limits.

**Example section**:
```markdown
## Hebrew Lexicon Entries (BDB)

### רעה
**Lexicon**: BDB Dictionary
**Strong's**: 7462
**Definition**: to pasture, tend, graze, feed
  - to tend, pasture
    - to shepherd
    - of ruler, teacher (fig)
...
```

---

## S

### Stress Marking
Visual indication of which syllables receive prosodic stress in Hebrew phonetic transcription. Stress is extracted from **cantillation marks** (te'amim) in the Masoretic text.

**Three stress levels**:
- **Primary stress** (Level 2): Major disjunctive accents (silluq, atnah, zaqef, etc.) — marked with UPPERCASE + bold
- **Secondary stress** (Level 1): Minor conjunctive accents (munach, mahpakh, mercha)
- **Unstressed** (Level 0): No marking

**Format**: kə-**VŌDH** mal-**KHŪTH**-khā **YŌ**-mē-rū [3 stresses]

**Why it matters**: Enables objective analysis of Hebrew meter and rhythm. Without stress marking, claims like "the rhythm is stately" are unverifiable. With stress marking, we can say "the verse has a balanced 3+3 stress pattern" with evidence.

**Implementation**: The PhoneticAnalyst extracts stress automatically from cantillation marks during transcription. No manual annotation required.

---

## T

### Telescopic Analysis
The core methodological principle of the pipeline: analyzing a text at multiple levels of magnification and then integrating the results. Inspired by Robert Alter's literary approach to biblical narrative.

**The metaphor**: Like a telescope that can zoom in (micro) and zoom out (macro), the pipeline:
1. **Zooms out** (Pass 1): Sees the "forest"—overall structure, genre, thesis
2. **Zooms in** (Pass 2): Sees the "trees"—verse-level details, word choices, poetic devices
3. **Integrates** (Pass 3): Synthesizes macro and micro into coherent commentary

**What it prevents**:
- Generic verse-by-verse paraphrasing disconnected from chapter thesis
- Tunnel vision that misses the forest for the trees
- Confirmation bias (micro analysis is curiosity-driven, can challenge macro thesis)

**Example**: A macro thesis might propose Psalm 29 transfers storm-god imagery from Baal to YHWH. Micro analysis examines specific lexical choices (בְּנֵי אֵלִים, קוֹל יְהוָה) to test this thesis. Synthesis integrates both levels to show how verse-level details support (or complicate) the macro argument.

---

## V

### Voweled Search
A concordance search mode that strips cantillation marks but preserves vowel points. Used to distinguish homographs (words with identical consonants but different meanings).

**Example**: Distinguishes אֵל (God) from אֶל (to/toward) based on vowel differences.

**When to use**: When semantic precision is needed to separate different meanings of the same consonantal root.

See also: Consonantal Search, Exact Search, Lemma Search

---

## Related Documents

- **[PHONETIC_SYSTEM.md](PHONETIC_SYSTEM.md)**: Detailed phonetic transcription rules
- **[TECHNICAL_ARCHITECTURE_SUMMARY.md](TECHNICAL_ARCHITECTURE_SUMMARY.md)**: Technical system architecture
- **[CONTEXT.md](CONTEXT.md)**: Project overview and quick start guide

---

**Total Entries**: 20
**Lines**: ~185
