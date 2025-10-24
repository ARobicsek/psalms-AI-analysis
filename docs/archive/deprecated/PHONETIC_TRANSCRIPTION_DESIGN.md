# Phonetic Transcription Enhancement for Micro Analyst

**Date**: 2025-10-19
**Purpose**: Prevent phonetic errors in commentary by providing accurate pronunciation data

## Problem Statement

The Master Editor (GPT-5) made an incorrect phonetic claim about Psalm 145:16:
> "The line's sound—the soft f and sh—matches the gentleness of the act it describes."

This is factually wrong:
- **פּוֹתֵחַ** has **פּ with dagesh** = hard **"p"** (not soft "f")
- **יָדֶךָ** has **ך (final khaf)** = guttural **"kh"** (not "sh")

The error occurred because the Master Editor lacked access to accurate phonetic data. We need to add phonetic transcriptions to the Micro Analyst output so that downstream agents (Synthesizer, Master Editor) can make accurate phonetic claims.

---

## 1. Phonetic Transcription Format

### Design Principles
1. **Simple and accessible**: IPA-like but readable for non-linguists
2. **Consonant precision**: Distinguish dagesh/no dagesh, final forms, gutturals
3. **Vowel clarity**: Indicate all vowels with reasonable precision
4. **Word-level**: Transcribe each word separately
5. **Syllable breaks**: Use hyphens to show syllable boundaries

### Transcription System

#### Consonants
| Hebrew | With Dagesh | Without Dagesh | Final Form | Notes |
|--------|-------------|----------------|------------|-------|
| ב | **b** | **v** | - | bet/vet |
| ג | **g** | **g** | - | gimel (always hard in this system) |
| ד | **d** | **d** | - | dalet |
| ה | **h** | **h** | - | he (often silent at end) |
| ו | **v** | - | - | vav |
| ז | **z** | - | - | zayin |
| ח | **kh** | - | - | chet (guttural) |
| ט | **t** | - | - | tet |
| י | **y** | - | - | yod |
| כ | **k** | **kh** | **kh** (ך) | kaf/khaf |
| ל | **l** | - | - | lamed |
| מ | **m** | - | **m** (ם) | mem |
| נ | **n** | - | **n** (ן) | nun |
| ס | **s** | - | - | samekh |
| ע | **'** | - | - | ayin (glottal, often silent) |
| פ | **p** | **f** | **f** (ף) | pe/fe |
| צ | **ts** | - | **ts** (ץ) | tsade |
| ק | **k** | - | - | qof |
| ר | **r** | - | - | resh |
| שׁ | **sh** | - | - | shin |
| שׂ | **s** | - | - | sin |
| ת | **t** | **t** | - | tav |

#### Vowels
| Vowel Name | Symbol | Transcription | Example |
|------------|--------|---------------|---------|
| Patakh | ַ◌ | **a** | **pa-takh** |
| Qamets | ָ◌ | **a** | **ka-mets** |
| Tsere | ֵ◌ | **e** | **tse-re** |
| Segol | ֶ◌ | **e** | **se-gol** |
| Khiriq | ִ◌ | **i** | **khi-rik** |
| Kholam | ֹ◌ / וֹ | **o** | **kho-lam** |
| Qamets Khatuf | ָ◌ | **o** | **kom** |
| Qibbuts | ֻ◌ | **u** | **ku-buts** |
| Shureq | וּ | **u** | **shu-ruk** |
| Shewa (vocal) | ְ◌ | **e** | **she-va** |
| Shewa (silent) | ְ◌ | **-** | (not transcribed) |
| Khatef Patakh | ֲ◌ | **a** | **kha-taf pa-takh** |
| Khatef Segol | ֱ◌ | **e** | **kha-taf se-gol** |
| Khatef Qamets | ֳ◌ | **o** | **kha-taf ka-mets** |

#### Special Cases
- **Syllable breaks**: Use hyphens (`-`)
- **Silent shewa**: Don't transcribe
- **Maqqef** (word joiner): Use a single hyphen between words (e.g., `et-ya-de-kha`)
- **Divine name (YHVH)**: Transcribe as pronounced: **a-do-nai** or **[YHVH]** with note
- **Doubled consonants** (dagesh forte): Double the letter (e.g., **ham-me-lekh**)

### Example Transcriptions

**Psalm 145:1** - תְּהִלָּה לְדָוִד
```
te-hil-la le-da-vid
```

**Psalm 145:16** - פּוֹתֵחַ אֶת־יָדֶךָ וּמַשְׂבִּיעַ לְכׇל־חַי רָצוֹן
```
po-te-akh et-ya-de-kha u-mas-bi-a le-khol-khai ra-tson
```
**Breakdown**:
- **פּוֹתֵחַ** = `po-te-akh` — **p** (dagesh), not "f"
- **אֶת־יָדֶךָ** = `et-ya-de-kha` — final **kh** (ך), not "sh"
- **וּמַשְׂבִּיעַ** = `u-mas-bi-a` — **s** (sin), not "sh"
- **לְכׇל־חַי** = `le-khol-khai` — **kh** (chet) and **kh** (yod)
- **רָצוֹן** = `ra-tson`

**Psalm 145:8** - חַנּוּן וְרַחוּם יְהוָה אֶרֶךְ אַפַּיִם וּגְדׇל־חָסֶד
```
khan-nun ve-ra-khum a-do-nai e-rekh a-pa-yim ug-dol-kha-sed
```

---

## 2. Integration into Pipeline

### Where to Add Phonetic Data

**Option A: Add to `VerseCommentary` in MicroAnalysis schema** (RECOMMENDED)
- Add a new field: `phonetic_transcription: Optional[str]`
- Each verse gets its own phonetic transcription
- Downstream agents can easily reference it

**Option B: Add to Research Bundle**
- Create a new section in `ResearchBundle.to_markdown()` called "Phonetic Transcriptions"
- Include verse-by-verse phonetic data

**Recommendation**: Use **Option A** (schema addition) because:
1. Phonetic data is verse-specific, like lexical insights
2. It integrates naturally with existing `VerseCommentary` structure
3. Easy to serialize/deserialize with the rest of the analysis
4. Downstream agents already consume `MicroAnalysis` directly

### Schema Changes

**File**: `c:\Users\ariro\OneDrive\Documents\Psalms\src\schemas\analysis_schemas.py`

```python
@dataclass
class VerseCommentary:
    """Detailed commentary for a single verse from Pass 2."""
    verse_number: int
    commentary: str  # Full verse-by-verse analysis
    lexical_insights: List[str] = field(default_factory=list)
    figurative_analysis: List[str] = field(default_factory=list)
    thesis_connection: str = ""
    phonetic_transcription: str = ""  # NEW: IPA-like phonetic transcription
```

### Research Bundle Formatting

**File**: `c:\Users\ariro\OneDrive\Documents\Psalms\src\agents\research_assembler.py`

Add a new section to `ResearchBundle.to_markdown()`:

```python
# In to_markdown() method, after RAG Context section:

# Phonetic Transcriptions section
if any(vc.phonetic_transcription for vc in micro_analysis.verse_commentaries):
    md += "## Phonetic Transcriptions (Verse-by-Verse)\n\n"
    md += "*Use these transcriptions to make accurate phonetic claims.*\n\n"
    for vc in micro_analysis.verse_commentaries:
        if vc.phonetic_transcription:
            md += f"**v{vc.verse_number}**: `{vc.phonetic_transcription}`\n\n"
```

However, since `ResearchBundle` doesn't currently have access to `MicroAnalysis`, we should instead:

**Add phonetic section to Synthesis/Master Editor prompts directly** by formatting it from `MicroAnalysis`:

```python
# In synthesis_writer.py and master_editor.py
def format_phonetic_section(micro_analysis: MicroAnalysis) -> str:
    """Format phonetic transcriptions for inclusion in prompts."""
    lines = ["## PHONETIC TRANSCRIPTIONS\n"]
    lines.append("*Reference these for accurate phonetic commentary.*\n")
    for vc in micro_analysis.verse_commentaries:
        if vc.phonetic_transcription:
            lines.append(f"**Verse {vc.verse_number}**: `{vc.phonetic_transcription}`\n")
    return "\n".join(lines)
```

---

## 3. Prompt Addition for Micro Analyst

### Location
**File**: `c:\Users\ariro\OneDrive\Documents\Psalms\src\agents\micro_analyst.py`

**Prompt Section**: `DISCOVERY_PASS_PROMPT`

### New Instruction Block

Add this section after "DISCOVERY TASK:" and before "OUTPUT FORMAT:":

```python
---

PHONETIC TRANSCRIPTION TASK:

For each verse, provide an ACCURATE PHONETIC TRANSCRIPTION of the Hebrew text.

**Why this matters**: Downstream editors need accurate phonetic data to avoid errors like claiming "soft f" when the text has a hard "p" (פּ with dagesh), or "sh" when it's actually "kh" (ך final khaf).

**Transcription system**:

CONSONANTS:
- ב with dagesh = **b**, without = **v**
- כ with dagesh = **k**, without = **kh**, final ך = **kh**
- פ with dagesh = **p**, without = **f**, final ף = **f**
- ת with dagesh = **t**, without = **t** (no change)
- ד with dagesh = **d**, without = **d** (no change)
- ג = **g** (always)
- ח = **kh** (guttural)
- ע = **'** (glottal, often silent)
- ק = **k**
- שׁ = **sh**, שׂ = **s**
- צ = **ts**
- Other consonants: straightforward (m, n, l, r, z, s, h, y, v)

VOWELS:
- Patakh (ַ◌), Qamets (ָ◌) = **a**
- Tsere (ֵ◌), Segol (ֶ◌) = **e**
- Khiriq (ִ◌) = **i**
- Kholam (ֹ◌, וֹ), Qamets Khatuf (ָ◌ in closed syllable) = **o**
- Qibbuts (ֻ◌), Shureq (וּ) = **u**
- Vocal shewa (ְ◌) = **e**
- Silent shewa = (don't transcribe)
- Khatef vowels (ֲ◌, ֱ◌, ֳ◌) = **a**, **e**, **o**

FORMATTING:
- Use hyphens for syllable breaks: `po-te-akh`
- Maqqef joins words with hyphen: `et-ya-de-kha`
- Divine name: Use `a-do-nai` (as pronounced)
- Doubled consonants (dagesh forte): Double the letter: `khan-nun`

**Examples**:

Hebrew: **פּוֹתֵחַ אֶת־יָדֶךָ**
Phonetic: `po-te-akh et-ya-de-kha`
Notes: פּ with dagesh = **p** (not f), ך final = **kh** (not sh)

Hebrew: **חַנּוּן וְרַחוּם**
Phonetic: `khan-nun ve-ra-khum`
Notes: נּ doubled = **nn**, ח = **kh**

Hebrew: **תְּהִלָּה לְדָוִד**
Phonetic: `te-hil-la le-da-vid`
Notes: תּ with dagesh = **t**, לּ doubled = **ll**

**Include the full verse transcription** in your JSON output for each verse.

---
```

### Updated JSON Output Format

Modify the example in `DISCOVERY_PASS_PROMPT`:

```python
OUTPUT FORMAT: Return ONLY valid JSON:

{
  "verse_discoveries": [
    {
      "verse_number": 1,
      "observations": "Quick summary of what's interesting/curious in this verse (2-4 sentences). Focus on discoveries, not analysis.",
      "curious_words": ["קוֹל", "בְּנֵי אֵלִים"],  // Hebrew words worth investigating
      "poetic_features": ["anaphora setup", "divine council imagery"],
      "figurative_elements": ["sons of gods - metaphor or literal?"],
      "puzzles": ["Why 'sons of gods' (plural) in monotheistic psalm?"],
      "lxx_insights": "LXX uses 'υἱοὶ θεοῦ' - shows early plural divine beings interpretation",
      "macro_relation": "Supports divine council framework from thesis",
      "phonetic": "te-hil-la le-da-vid a-ro-mim-kha e-lo-hai ham-me-lekh"  // NEW FIELD
    },
    {
      "verse_number": 2,
      "observations": "...",
      "phonetic": "be-khol-yom a-va-re-khe-ka va-a-ha-le-la shim-kha le-o-lam va-ed",
      ...
    },
    ... (all verses)
  ],
  ...
}
```

---

## 4. Example Output for Psalm 145:16

### Hebrew Text
```
פּוֹתֵחַ אֶת־יָדֶךָ וּמַשְׂבִּיעַ לְכׇל־חַי רָצוֹן
```

### Phonetic Transcription
```
po-te-akh et-ya-de-kha u-mas-bi-a le-khol-khai ra-tson
```

### Word-by-Word Breakdown

| Word | Transcription | Key Features |
|------|---------------|--------------|
| פּוֹתֵחַ | `po-te-akh` | **פּ** with dagesh = **p** (NOT "f"), final **ח** = **kh** |
| אֶת־יָדֶךָ | `et-ya-de-kha` | Maqqef joins; final **ך** = **kh** (NOT "sh") |
| וּמַשְׂבִּיעַ | `u-mas-bi-a` | **שׂ** (sin) = **s**, **בּ** doubled = **bb** → **bi** |
| לְכׇל־חַי | `le-khol-khai` | **ח** = **kh** (guttural chet) |
| רָצוֹן | `ra-tson` | **צ** = **ts** |

### Accurate Phonetic Description (for commentary)

**CORRECT**:
> "The verse opens with the hard plosive **p** in *potēaḥ* (פּוֹתֵחַ), emphasizing the decisive action of opening, followed by the guttural **kh** sound in *et-yadekha* (אֶת־יָדֶךָ) which creates a softer, more intimate quality as it refers to God's hand."

**INCORRECT** (what GPT-5 actually said):
> "The line's sound—the soft f and sh—matches the gentleness of the act it describes."

---

## 5. Edge Cases & Special Handling

### 5.1 Divine Names

**Question**: Should we transcribe the Tetragrammaton (יהוה)?

**Answer**: Yes, but indicate how it's pronounced liturgically:

| Hebrew | Standard Reading | Transcription | Note |
|--------|------------------|---------------|------|
| יְהוָה | Adonai | `a-do-nai` | Most common |
| יֱהֹוִה | Elohim | `e-lo-him` | When יְהוָה appears near אֲדֹנָי |

**Recommendation**: Always use `a-do-nai` unless the text specifically indicates otherwise.

**Alternative**: Mark it clearly as unpronounceable:
```
[YHVH]
```
This signals to the editor that it's the divine name and should be handled with care.

### 5.2 Maqqef (Word Joiners)

**Hebrew**: אֶת־יָדֶךָ (et-yadekha)

**Transcription**: `et-ya-de-kha`

**Rationale**: Treat maqqef-joined words as a single prosodic unit with internal syllable breaks.

### 5.3 Silent vs. Vocal Shewa

**Silent shewa**: Don't transcribe (e.g., יְרוּשָׁלַם = `ye-ru-sha-la-yim`, not `ye-re-ru-sha-la-yim`)

**Vocal shewa**: Transcribe as **e** (e.g., בְּרֵאשִׁית = `be-re-shit`)

**Rule of thumb**:
- At beginning of word: usually vocal (`be-`, `le-`, `ve-`)
- After first consonant: usually silent
- After vocal shewa: usually vocal (two consecutive vocal shewas)

**When in doubt**: Prefer vocal shewa in transcription (over-transcribing is safer than under-transcribing for phonetic accuracy).

### 5.4 Qamets vs. Qamets Khatuf

Both look identical (ָ◌), but:
- **Qamets**: long "a" sound
- **Qamets Khatuf**: short "o" sound (in closed, unaccented syllables)

**Example**:
- **כָּל** (all) = `kol` (qamets khatuf in closed syllable)
- **כָּבוֹד** (glory) = `ka-vod` (qamets in open syllable)

**Transcription**: Both → **a** (let context determine, or note as **o** when certain)

### 5.5 Begadkefat Letters

The six letters **בגדכפת** (begadkefat) can have dagesh lene (hard) or be soft:

| Letter | Hard (with dagesh) | Soft (without) |
|--------|-------------------|----------------|
| ב | **b** | **v** |
| ג | **g** | **g** (or **gh** in traditional pronunciation) |
| ד | **d** | **d** (or **dh** in traditional pronunciation) |
| כ | **k** | **kh** |
| פ | **p** | **f** |
| ת | **t** | **t** (or **th** in traditional pronunciation) |

**Recommendation**: Use simplified system (b/v, k/kh, p/f, and always g/d/t) for accessibility.

### 5.6 Hatef Vowels (Composite Shewas)

| Vowel | Symbol | Transcription |
|-------|--------|---------------|
| Khatef Patakh | ֲ◌ | **a** |
| Khatef Segol | ֱ◌ | **e** |
| Khatef Qamets | ֳ◌ | **o** |

**Example**: אֱלֹהִים = `e-lo-him`

---

## 6. Prompt Instructions for Downstream Agents

### For Synthesis Writer

Add to the synthesis writer prompt:

```markdown
## PHONETIC TRANSCRIPTIONS AVAILABLE

Phonetic transcriptions are provided for each verse in the Micro Analysis.

**USE THESE** when making claims about:
- Sound patterns (alliteration, assonance, consonance)
- Phonetic symbolism (harsh vs. soft sounds)
- Rhythmic qualities
- Wordplay based on similar-sounding words

**DO NOT** make phonetic claims without consulting the transcriptions. Common errors to avoid:
- Confusing פּ (hard p) with פ (soft f)
- Confusing ך (final khaf = kh) with ש (shin = sh)
- Missing dagesh distinctions (b/v, k/kh, p/f)
- Claiming sounds that aren't actually present

**Example of correct usage**:
"The opening word *potēaḥ* (פּוֹתֵחַ) features the hard plosive **p**, creating a sense of decisive action as God 'opens' His hand."

**Example of incorrect usage** (to avoid):
"The soft **f** sound in *potēaḥ* creates gentleness." ← WRONG: it's a hard **p**, not soft **f**.
```

### For Master Editor

Add to the master editor prompt (in the "FACTUAL ERRORS" section):

```markdown
### 1. FACTUAL ERRORS

- Biblical errors (e.g., "Jacob had brothers" when he had only one - Esau)
- **Phonetic errors** (e.g., claiming "soft f" when the text has hard "p" with dagesh, or "sh" when it's "kh")
  * **Always check phonetic transcriptions** before making claims about sound patterns
  * Common errors: confusing פּ (p) with פ (f), ך (kh) with ש (sh), כּ (k) with כ (kh)
- Misattributions of texts or quotations
- Incorrect historical or cultural claims
- Mistaken grammatical analysis
- Wrong verse references

**Phonetic Accuracy Check**:
Before approving any commentary that discusses sound patterns, rhythm, or phonetic symbolism, verify against the provided phonetic transcriptions. If the transcription shows `po-te-akh` (with hard **p**), do not allow claims about "soft f sounds."
```

---

## 7. Implementation Checklist

### Phase 1: Schema Update
- [ ] Add `phonetic_transcription: str = ""` to `VerseCommentary` in `analysis_schemas.py`
- [ ] Update `VerseCommentary.to_dict()` to include phonetic field
- [ ] Update `VerseCommentary.from_dict()` to handle phonetic field
- [ ] Update `MicroAnalysis.to_markdown()` to display phonetic transcriptions

### Phase 2: Micro Analyst Prompt Update
- [ ] Add phonetic transcription instructions to `DISCOVERY_PASS_PROMPT`
- [ ] Add phonetic transcription examples to prompt
- [ ] Update JSON output format to include `"phonetic"` field
- [ ] Update `_create_micro_analysis()` to extract phonetic data from discoveries

### Phase 3: Downstream Agent Updates
- [ ] Add phonetic transcription section to `SynthesisWriter` prompt
- [ ] Add phonetic error checking to `MasterEditor` prompt
- [ ] Create `format_phonetic_section()` helper function for prompts

### Phase 4: Testing
- [ ] Test Micro Analyst with Psalm 145 (verify accurate transcription of v16)
- [ ] Verify phonetic data appears in `MicroAnalysis` JSON output
- [ ] Verify Synthesis Writer references phonetic data
- [ ] Verify Master Editor catches phonetic errors
- [ ] Test edge cases: divine names, maqqef, shewa variations

### Phase 5: Documentation
- [ ] Document phonetic transcription system in README
- [ ] Add examples to developer documentation
- [ ] Create quick reference guide for transcription symbols

---

## 8. Expected Benefits

1. **Prevent factual errors**: No more claims about "soft f" when it's hard "p"
2. **Enable accurate phonetic analysis**: Synthesis and Master Editor can confidently discuss sound patterns
3. **Educational value**: Readers learn correct pronunciation of Hebrew verses
4. **Scholarly credibility**: Accurate phonetics demonstrate attention to linguistic detail
5. **Quality control**: Master Editor can verify phonetic claims against transcriptions

---

## 9. Future Enhancements

### 9.1 Stress/Accent Marks
Add primary stress markers:
```
po-TE-akh (stress on second syllable)
```

### 9.2 Full IPA Option
Offer true IPA transcription for linguistic precision:
```
poˈteax ʔɛt jaˈdɛxa
```

### 9.3 Audio Integration
Generate audio files from transcriptions using TTS for Hebrew.

### 9.4 Automated Transcription
Use a Hebrew morphological analyzer to auto-generate transcriptions, then have LLM verify.

---

## Conclusion

This phonetic transcription enhancement will prevent the exact type of error encountered in Psalm 145:16, where the Master Editor incorrectly claimed "soft f and sh sounds" when the Hebrew actually has hard "p" and guttural "kh" sounds.

By adding phonetic transcriptions to the Micro Analyst output and instructing downstream agents to reference them, we ensure that all phonetic commentary is grounded in accurate linguistic data rather than LLM guesswork.

**Implementation Priority**: HIGH — This directly addresses a factual error and improves scholarly credibility of the entire pipeline.
