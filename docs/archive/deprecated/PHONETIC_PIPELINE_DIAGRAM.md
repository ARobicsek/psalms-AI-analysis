# Phonetic Transcription Pipeline Integration Diagram

**Visual representation of how phonetic data flows through the pipeline**

---

## Current Pipeline (Before Enhancement)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MACRO ANALYST (Pass 1)                       │
│  Input: Psalm text, RAG context                                     │
│  Output: Thesis, structure, poetic devices                          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ MacroAnalysis JSON
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        MICRO ANALYST (Pass 2)                       │
│  Input: Psalm text, MacroAnalysis, RAG context                      │
│  Output: Verse discoveries, research requests                       │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ VerseCommentary (per verse):                               │    │
│  │  - verse_number                                             │    │
│  │  - commentary                                               │    │
│  │  - lexical_insights                                         │    │
│  │  - figurative_analysis                                      │    │
│  │  - thesis_connection                                        │    │
│  └────────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ MicroAnalysis JSON + ResearchBundle
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SYNTHESIS WRITER (Pass 3)                      │
│  Input: Macro + Micro + ResearchBundle                              │
│  Output: Introduction essay + Verse commentary                      │
│                                                                      │
│  ⚠️  PHONETIC CLAIMS MADE WITHOUT VERIFICATION                      │
│  Example: "The soft f and sh sounds..."  ← ERROR!                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Introduction + Verse Commentary
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       MASTER EDITOR (Pass 4)                        │
│  Model: GPT-5                                                  │
│  Task: Review and enhance commentary                                │
│                                                                      │
│  ⚠️  NO PHONETIC DATA AVAILABLE TO VERIFY CLAIMS                    │
│  Result: Phonetic errors slip through                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Enhanced Pipeline (After Implementation)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MACRO ANALYST (Pass 1)                       │
│  Input: Psalm text, RAG context                                     │
│  Output: Thesis, structure, poetic devices                          │
│  [No changes]                                                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ MacroAnalysis JSON
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        MICRO ANALYST (Pass 2)                       │
│  Input: Psalm text, MacroAnalysis, RAG context                      │
│  Output: Verse discoveries + PHONETIC TRANSCRIPTIONS                │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ VerseCommentary (per verse):                               │    │
│  │  - verse_number                                             │    │
│  │  - commentary                                               │    │
│  │  - lexical_insights                                         │    │
│  │  - figurative_analysis                                      │    │
│  │  - thesis_connection                                        │    │
│  │  - phonetic_transcription  ◄── NEW FIELD                   │    │
│  │                                                             │    │
│  │  Example (v16):                                             │    │
│  │  "phonetic": "po-te-akh et-ya-de-kha..."                   │    │
│  │               ▲          ▲                                  │    │
│  │              "p" not "f" │                                  │    │
│  │                        "kh" not "sh"                        │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  NEW PROMPT SECTION:                                                │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ PHONETIC TRANSCRIPTION TASK                              │      │
│  │                                                           │      │
│  │ For each verse, provide ACCURATE transcription:          │      │
│  │  - Consonants: distinguish dagesh (p/f, b/v, k/kh)       │      │
│  │  - Vowels: a, e, i, o, u                                 │      │
│  │  - Format: syllable breaks with hyphens                  │      │
│  │  - Special: maqqef, divine names, doubled consonants     │      │
│  │                                                           │      │
│  │ Examples:                                                 │      │
│  │  פּוֹתֵחַ = po-te-akh (p not f, kh not h)                │      │
│  │  חַנּוּן = khan-nun (kh not h, doubled n)                │      │
│  └──────────────────────────────────────────────────────────┘      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ MicroAnalysis JSON (with phonetics)
                             │ + ResearchBundle
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SYNTHESIS WRITER (Pass 3)                      │
│  Input: Macro + Micro (w/ phonetics) + ResearchBundle               │
│  Output: Introduction + Verse commentary                            │
│                                                                      │
│  NEW PROMPT SECTION:                                                │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ PHONETIC TRANSCRIPTIONS                                  │      │
│  │                                                           │      │
│  │ Verse 16: po-te-akh et-ya-de-kha u-mas-bi-a...          │      │
│  │                                                           │      │
│  │ ALWAYS CONSULT before making phonetic claims!            │      │
│  │                                                           │      │
│  │ Common errors to avoid:                                  │      │
│  │  ❌ Claiming "f" when it's "p" (פּ with dagesh)          │      │
│  │  ❌ Claiming "sh" when it's "kh" (ך final khaf)          │      │
│  │                                                           │      │
│  │ Example CORRECT usage:                                   │      │
│  │  "The hard plosive p in potēaḥ..."                      │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                      │
│  ✅ PHONETIC CLAIMS NOW GROUNDED IN ACCURATE DATA                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Introduction + Verse Commentary
                             │ (with accurate phonetic claims)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       MASTER EDITOR (Pass 4)                        │
│  Model: GPT-5                                                  │
│  Input: Commentary + Macro + Micro (w/ phonetics) + ResearchBundle │
│  Task: Review, verify, enhance                                      │
│                                                                      │
│  NEW PROMPT SECTION:                                                │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ PHONETIC TRANSCRIPTIONS                                  │      │
│  │                                                           │      │
│  │ Verse 16: po-te-akh et-ya-de-kha...                     │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                      │
│  EDITORIAL CRITERIA (UPDATED):                                      │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ 1. FACTUAL ERRORS                                        │      │
│  │    - Phonetic errors (HIGH PRIORITY)                     │      │
│  │      ✓ Check all sound-pattern claims vs. transcriptions│      │
│  │      ✓ Verify dagesh distinctions (p/f, b/v, k/kh)      │      │
│  │      ✓ Verify shin/sin, chet/he, final forms            │      │
│  │                                                           │      │
│  │    Before approving:                                     │      │
│  │    "Does this commentary claim sounds not in the         │      │
│  │     phonetic transcription?"                             │      │
│  │                                                           │      │
│  │    Example error to catch:                               │      │
│  │    ❌ "soft f and sh sounds" (when p and kh)             │      │
│  │    ✅ "hard p and guttural kh sounds"                    │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                      │
│  ✅ PHONETIC ERRORS CAUGHT AND CORRECTED                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Final Commentary
                             │ (phonetically accurate)
                             ▼
                   ┌─────────────────────┐
                   │  PRINT-READY OUTPUT │
                   │  ✅ No phonetic errors│
                   └─────────────────────┘
```

---

## Data Flow Detail

### 1. Micro Analyst Generates Phonetic Data

```
INPUT: Hebrew verse
פּוֹתֵחַ אֶת־יָדֶךָ וּמַשְׂבִּיעַ לְכׇל־חַי רָצוֹן

       │
       │ Phonetic analysis
       │  - Check dagesh: פּ = p, not f
       │  - Check finals: ך = kh, not sh
       │  - Syllable breaks: po-te-akh
       │  - Maqqef joins: et-ya-de-kha
       ▼

OUTPUT: Phonetic transcription
"phonetic": "po-te-akh et-ya-de-kha u-mas-bi-a le-khol-khai ra-tson"

       │
       │ Stored in VerseCommentary
       ▼

MicroAnalysis JSON
{
  "verse_commentaries": [
    {
      "verse_number": 16,
      "phonetic_transcription": "po-te-akh et-ya-de-kha..."
    }
  ]
}
```

### 2. Synthesis Writer Uses Phonetic Data

```
INPUT: MicroAnalysis (with phonetics)

       │
       │ Format phonetic section for prompt
       ▼

PROMPT SECTION:
┌────────────────────────────────────────┐
│ PHONETIC TRANSCRIPTIONS                │
│                                         │
│ Verse 16: po-te-akh et-ya-de-kha...   │
│                                         │
│ ALWAYS CONSULT before phonetic claims! │
└────────────────────────────────────────┘

       │
       │ LLM references during generation
       │  "I see v16 has 'po-te-akh' with hard p..."
       ▼

OUTPUT: Verse commentary
"The verse opens with the hard plosive p in potēaḥ,
creating decisive action..."
                    ▲
                    │
          ✅ ACCURATE (checked against transcription)
```

### 3. Master Editor Verifies Phonetic Claims

```
INPUT: Commentary + Phonetic transcriptions

       │
       │ Check: Does commentary claim sounds
       │        not in transcription?
       ▼

VERIFICATION:
Commentary says: "soft f and sh sounds"
Transcription shows: "po-te-akh et-ya-de-kha"
                      ▲         ▲
                      p         kh
                   (not f)   (not sh)

       │
       │ ERROR DETECTED
       ▼

CORRECTION:
Replace: "soft f and sh"
With: "hard plosive p and guttural kh"

       │
       │ Corrected commentary
       ▼

OUTPUT: Final commentary (accurate)
"The verse opens with the hard plosive p in potēaḥ,
followed by the guttural kh in yadekha..."
                          ✅ VERIFIED
```

---

## Schema Changes

### Before
```python
@dataclass
class VerseCommentary:
    verse_number: int
    commentary: str
    lexical_insights: List[str]
    figurative_analysis: List[str]
    thesis_connection: str
```

### After
```python
@dataclass
class VerseCommentary:
    verse_number: int
    commentary: str
    lexical_insights: List[str]
    figurative_analysis: List[str]
    thesis_connection: str
    phonetic_transcription: str = ""  # ◄── NEW FIELD
```

---

## Prompt Integration Points

### Point 1: Micro Analyst Discovery Prompt

**Location**: `src/agents/micro_analyst.py` → `DISCOVERY_PASS_PROMPT`

**Addition**: Phonetic transcription task with full instructions

```python
DISCOVERY_PASS_PROMPT = """
...existing discovery tasks...

---

## PHONETIC TRANSCRIPTION TASK

For each verse, provide ACCURATE phonetic transcription...
[Full instructions from PHONETIC_PROMPT_TEXT.md]

---

OUTPUT FORMAT:
{
  "verse_discoveries": [
    {
      "verse_number": 1,
      "phonetic": "te-hil-la le-da-vid..."  # ◄── NEW FIELD
    }
  ]
}
"""
```

### Point 2: Synthesis Writer Prompt

**Location**: `src/agents/synthesis_writer.py` → `VERSE_SYNTHESIS_PROMPT`

**Addition**: Phonetic section + accuracy guidelines

```python
VERSE_SYNTHESIS_PROMPT = """
...existing context sections...

---

{phonetic_section}  # ◄── FORMATTED PHONETIC DATA

**PHONETIC ACCURACY GUIDELINES**:
When making claims about sound patterns:
1. Always consult phonetic transcriptions above
2. Common errors to avoid:
   - Confusing פּ (hard p) with פ (soft f)
   - Confusing ך (kh) with ש (sh)

---

...rest of prompt...
"""
```

### Point 3: Master Editor Prompt

**Location**: `src/agents/master_editor.py` → `MASTER_EDITOR_PROMPT`

**Addition**: Phonetic section + error checking criteria

```python
MASTER_EDITOR_PROMPT = """
...existing inputs...

---

{phonetic_section}  # ◄── FORMATTED PHONETIC DATA

---

## EDITORIAL REVIEW CRITERIA

### 1. FACTUAL ERRORS

**Phonetic Errors (HIGH PRIORITY)**:
- Claiming "soft f" when text has hard "p" (פּ with dagesh)
- Claiming "sh" when text has "kh" (ך final khaf)
...

Before approving ANY phonetic commentary:
✓ Verify against phonetic transcriptions

---

...rest of criteria...
"""
```

---

## Error Prevention Flow

```
┌────────────────────────────────────────────────────────────┐
│ Synthesis Writer generates verse commentary                │
│                                                             │
│ Draft: "The soft f and sh sounds create gentleness..."     │
└─────────────────────────┬──────────────────────────────────┘
                          │
                          │ Commentary sent to Master Editor
                          ▼
┌────────────────────────────────────────────────────────────┐
│ Master Editor reviews with phonetic transcriptions         │
│                                                             │
│ Checks:                                                     │
│  1. Commentary claims: "soft f and sh"                      │
│  2. Transcription shows: "po-te-akh et-ya-de-kha"         │
│                           ▲          ▲                      │
│                           p          kh                     │
│                        (not f)    (not sh)                  │
│                                                             │
│ ❌ ERROR DETECTED: Phonetic claim contradicts data         │
└─────────────────────────┬──────────────────────────────────┘
                          │
                          │ Master Editor corrects
                          ▼
┌────────────────────────────────────────────────────────────┐
│ Corrected commentary:                                       │
│                                                             │
│ "The verse opens with the hard plosive p in potēaḥ,       │
│  creating decisive action, followed by the guttural kh     │
│  in yadekha, which adds intimacy..."                       │
│                                                             │
│ ✅ ACCURATE: Matches phonetic transcription                │
└────────────────────────────────────────────────────────────┘
```

---

## Quality Assurance Checkpoints

### Checkpoint 1: Micro Analyst Output
```
Verify:
✓ All verses have phonetic_transcription field
✓ Transcriptions are non-empty
✓ Dagesh distinctions are accurate (p/f, b/v, k/kh)
✓ Final forms are correct (ך=kh, ף=f, ץ=ts)
✓ Syllable breaks present
✓ Maqqef-joined words hyphenated
```

### Checkpoint 2: Synthesis Writer Input
```
Verify:
✓ Phonetic section appears in prompt
✓ Transcriptions are accessible to LLM
✓ Accuracy guidelines are present
✓ Examples of correct/incorrect usage provided
```

### Checkpoint 3: Synthesis Writer Output
```
Verify:
✓ Phonetic claims reference specific transcriptions
✓ Sound-pattern analysis is accurate
✓ No unsupported phonetic claims
```

### Checkpoint 4: Master Editor Review
```
Verify:
✓ All phonetic claims checked against transcriptions
✓ Errors caught and corrected
✓ Corrected claims are accurate
✓ Final output has no phonetic errors
```

---

## Success Metrics

### Quantitative
- **0** phonetic errors in final output
- **100%** of verses have accurate transcriptions
- **100%** of phonetic claims verified against data

### Qualitative
- Commentary demonstrates mastery of Hebrew phonology
- Readers learn correct pronunciation
- Scholarly credibility enhanced
- Educational value increased

---

## Rollout Plan

### Stage 1: Single Psalm Test (Psalm 145)
1. Implement schema changes
2. Update Micro Analyst prompt
3. Run on Psalm 145
4. Verify transcription accuracy manually
5. Check downstream agent integration

### Stage 2: Validation (Psalms 1, 23, 29)
1. Run on diverse psalm types
2. Verify transcriptions with Hebrew expert
3. Test error detection (introduce intentional errors)
4. Refine system based on findings

### Stage 3: Full Deployment (All 150 Psalms)
1. Run complete pipeline with phonetic enhancement
2. Monitor for any edge cases
3. Validate random sample with Hebrew expert
4. Document lessons learned

---

## Maintenance

### Regular Tasks
- Spot-check transcription accuracy
- Monitor for new edge cases
- Update examples as needed
- Refine prompt instructions based on output quality

### Update Triggers
- Hebrew expert feedback
- User reports of pronunciation questions
- Discovery of new edge cases
- Improvements to transcription system

---

**This enhancement ensures that every phonetic claim in the commentary is grounded in accurate linguistic data, preventing errors and enhancing the scholarly credibility of the entire pipeline.**
