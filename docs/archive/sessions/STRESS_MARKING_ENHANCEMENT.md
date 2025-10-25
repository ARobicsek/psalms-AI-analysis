# Stress Marking Enhancement - Implementation Plan

**Date**: 2025-10-23
**Session**: 18
**Goal**: Add stress/accent marking to phonetic transcriptions for better scholarly analysis

---

## Problem Statement

Current phonetic transcriptions lack stress indicators, making it difficult to:
1. Analyze meter and rhythm patterns
2. Identify prosodic structures
3. Explain sound patterns in commentary

**Example of unclear commentary**:
> "The measured rhythm of the line—kə-vōdh mal-khūth-khā yō'-mē-rū // ūgh-vū-rā-thə-khā yə-dha-bē-rū—is stately"

Without stress marks, readers can't verify this claim or understand the actual rhythm.

---

## Solution: Three-Tier Stress Marking System

### Tier 1: Extract Stress from Cantillation Marks

Hebrew cantillation marks (te'amim) indicate prosodic stress. Key markers:

**Primary Disjunctive Accents** (major pauses, always stressed):
- Silluq (ֽ◌) - verse end, strongest stress
- Atnah (֑◌) - major mid-verse division
- Segolta (֒◌), Zaqef Qaton (֔◌), Zaqef Gadol (֕◌)
- Tifcha (֖◌), R'vi'i (֗◌), Zarqa (֘◌)
- Pashta (֙◌), Yetiv (֚◌), Tevir (֛◌)

**Secondary Conjunctive Accents** (minor pauses, sometimes stressed):
- Munach (֣◌), Mahpakh (֤◌), Mercha (֥◌)
- Some conjunctives don't carry stress

**Implementation Strategy**:
1. Map each cantillation mark to stress level (0=unstressed, 1=secondary, 2=primary)
2. During word transcription, mark syllable containing stress marker
3. Represent in output with visual indicators

### Tier 2: Visual Stress Indicators

**Three Output Formats**:

#### Format A: Uppercase + Bold (for Markdown/DOCX)
```
**kə-VŌDH** mal-**KHŪTH**-khā **YŌ**-mē-rū
```
- Stressed syllables: UPPERCASE + bold
- Provides visual "pop" in printed/digital text
- Easy to parse for readers

#### Format B: Acute Accent (for IPA-style)
```
kə-vṓdh mal-khū́th-khā yṓ-mē-rū
```
- Unicode combining acute accent (U+0301)
- Scholarly convention
- Cleaner for inline text

#### Format C: Stress Count Annotation
```
kə-vōdh mal-khūth-khā yō-mē-rū  [3 stresses: vōdh | khūth | yō]
```
- Explicit count for analysis
- Shows which syllables carry prosodic weight

**Recommendation**: Use Format A for print-ready output, Format C for agent prompts

### Tier 3: Prompt Integration

#### For Synthesis Writer:
```markdown
### PHONETIC TRANSCRIPTIONS WITH STRESS MARKING

Each verse includes phonetic transcription with STRESSED syllables marked.

**Example**:
Hebrew: כְּב֣וֹד מַלְכוּתְךָ֣ יֹאמֵ֑רוּ
Phonetic: kə-**VŌDH** mal-**KHŪTH**-khā **YŌ**-mē-rū  [3 stresses]

When discussing rhythm, meter, or sound patterns:
1. **Count the stresses** in each colon (half-line)
2. **Show the pattern** using the phonetic transcription
3. **Name the syllables** that carry prosodic weight

Good example:
"The verse has a balanced 3+3 stress pattern. In the first colon (kə-**VŌDH** mal-**KHŪTH**-khā),
the stresses fall on vōdh | khūth | khā, creating a measured, stately rhythm..."

Bad example:
"The rhythm is stately" (no evidence, no syllable identification)
```

#### For Master Editor:
```markdown
### VALIDATING PHONETIC ANALYSIS

The synthesis writer has access to stress-marked phonetic transcriptions.

**Review checklist**:
- [ ] Are stress counts accurate? (Count CAPITALIZED syllables)
- [ ] Are prosodic claims supported by actual stress patterns?
- [ ] Are meter descriptions specific (e.g., "3+2" not "rhythmic")?
- [ ] Are stressed syllables named when discussing sound patterns?

If the synthesis writer makes vague claims like "the rhythm is X,"
require them to show the actual stress pattern using the phonetic data.
```

---

## Implementation Steps

### Step 1: Enhance `PhoneticAnalyst` Class

**File**: `src/agents/phonetic_analyst.py`

**Changes**:
1. Add cantillation-to-stress mapping dictionary
2. Track stress level during `_transcribe_word()`
3. Store stress info in syllable data structure
4. Add `_format_syllables_with_stress()` method
5. Include stress-marked transcription in output

**New Data Structure**:
```python
{
    "word": "מַלְכוּתְךָ֣",
    "transcription": "malkhūthkhā",
    "syllables": [
        {"phonemes": ["m", "a", "l"], "stress": 0},      # mal
        {"phonemes": ["kh", "ū", "th"], "stress": 2},    # KHŪTH (primary)
        {"phonemes": ["kh", "ā"], "stress": 1}            # khā (secondary)
    ],
    "syllable_transcription": "mal-khūth-khā",
    "syllable_transcription_stressed": "mal-**KHŪTH**-khā",
    "stress_count": 2,
    "stress_pattern": "0-2-1"
}
```

### Step 2: Update Verse-Level Transcription

**Enhancement**: Add stress summary at verse level
```python
{
    "original_text": "כְּב֣וֹד מַלְכוּתְךָ֣ יֹאמֵ֑רוּ",
    "words": [...],
    "stressed_transcription": "kə-**VŌDH** mal-**KHŪTH**-khā **YŌ**-mē-rū",
    "total_stresses": 3,
    "colon_structure": [
        {"text": "kə-**VŌDH** mal-**KHŪTH**-khā", "stresses": 2},
        {"text": "**YŌ**-mē-rū", "stresses": 1}
    ]
}
```

### Step 3: Update Synthesis Writer Prompts

**File**: `src/agents/synthesis_writer.py`

**Add to VERSE_COMMENTARY_PROMPT**:
```python
VERSE_COMMENTARY_PROMPT = """
...

### PHONETIC TRANSCRIPTIONS (with stress marking)
{phonetic_section}

When analyzing sound patterns, rhythm, or meter:
- **Count the stresses** using CAPITALIZED syllables
- **Show your work** by citing the specific syllables
- **Use the pattern** (e.g., "3+2 stress pattern") not vague descriptions

Example: "The first colon has 3 stresses (kə-**VŌDH** mal-**KHŪTH**-khā:
vōdh | khūth | khā), creating a stately, measured rhythm that befits royal proclamation."
...
"""
```

### Step 4: Update Master Editor Prompts

**File**: `src/agents/master_editor.py`

**Add validation criteria**:
```python
MASTER_EDITOR_PROMPT = """
...

### PHONETIC ANALYSIS VALIDATION

Check if sound/rhythm claims are supported:
1. Count the actual stresses in the phonetic transcription
2. Verify the synthesis writer's stress count matches
3. Ensure specific syllables are named (not generic descriptions)
4. Require meter patterns to be shown (e.g., "3+3" not "balanced")

Flag vague claims like "rhythmic," "flowing," "stately" without evidence.
Require: **VŌDH** | **KHŪTH** | **khā** → "3 stresses creating X effect"
...
"""
```

### Step 5: Update Print-Ready Formatter

**File**: `src/utils/commentary_formatter.py`

**Enhancement**: Show stress-marked phonetics in bilingual display

**Before**:
```
Hebrew:     כְּב֣וֹד מַלְכוּתְךָ֣ יֹאמֵ֑רוּ
English:    They shall speak the glory of Your kingdom
```

**After**:
```
Hebrew:     כְּב֣וֹד מַלְכוּתְךָ֣ יֹאמֵ֑רוּ
Phonetic:   kə-**VŌDH** mal-**KHŪTH**-khā **YŌ**-mē-rū  [3 stresses]
English:    They shall speak the glory of Your kingdom
```

---

## Cantillation Mark Reference

### Primary Stress Markers (Level 2):

| Mark | Unicode | Name | Position | Always Stressed |
|------|---------|------|----------|-----------------|
| ֽ◌ | U+05BD | Silluq | Final word | Yes |
| ֑◌ | U+0591 | Atnah | Mid-verse | Yes |
| ֔◌ | U+0594 | Zaqef Qaton | Major | Yes |
| ֕◌ | U+0595 | Zaqef Gadol | Major | Yes |
| ֖◌ | U+0596 | Tifcha | Major | Yes |
| ֗◌ | U+0597 | R'vi'i | Major | Yes |
| ֘◌ | U+0598 | Zarqa | Major | Yes |
| ֙◌ | U+0599 | Pashta | Major | Yes |
| ֚◌ | U+059A | Yetiv | Major | Yes |
| ֛◌ | U+059B | Tevir | Major | Yes |

### Secondary Stress Markers (Level 1):

| Mark | Unicode | Name | Position | Sometimes Stressed |
|------|---------|------|----------|-------------------|
| ֣◌ | U+05A3 | Munach | Conjunctive | Sometimes |
| ֤◌ | U+05A4 | Mahpakh | Conjunctive | Sometimes |
| ֥◌ | U+05A5 | Mercha | Conjunctive | Sometimes |

### Unstressed (Level 0):
- Words with no cantillation marks
- Proclitic particles (prepositions, conjunctions)

---

## Expected Outcomes

### Before Enhancement:
```
Commentary: "The measured rhythm of the line—kə-vōdh mal-khūth-khā yō'-mē-rū
// ūgh-vū-rā-thə-khā yə-dha-bē-rū—is stately"
```
**Problem**: Can't verify; no stress indicators; vague claim

### After Enhancement:
```
Commentary: "The verse exhibits a balanced 3+3 stress pattern. The first colon
(kə-**VŌDH** mal-**KHŪTH**-khā **YŌ**-mē-rū) places primary stress on vōdh | khūth | yō,
creating three evenly-spaced beats that convey the measured solemnity of royal proclamation.
The second colon mirrors this with **ŪGHVŪ**-rā-thə-khā **YƏDHA**-bē-rū (3 stresses:
ūghvū | khā | yə), maintaining the stately meter."
```
**Improvement**: Verifiable, specific, pedagogically clear

---

## Testing Plan

1. **Unit Test**: Verify stress extraction on Psalm 145:11 (known cantillation)
2. **Integration Test**: Run phonetic analyst on full verse, check stress output
3. **Prompt Test**: Generate commentary for verse with complex meter
4. **Validation Test**: Have master editor verify stress claims
5. **Formatter Test**: Ensure stress marks render correctly in markdown/DOCX

---

## Timeline

- **Session 18**: Implement cantillation mapping + stress extraction (2-3 hours)
- **Session 19**: Add stress-aware formatting + prompt updates (1-2 hours)
- **Session 20**: Test on Psalm 145, validate output quality (1 hour)

---

## Notes

- Cantillation marks already present in Sefaria Hebrew text - no new data needed
- Stress extraction is deterministic (rule-based, no AI needed)
- Enhancement is backward-compatible (doesn't break existing phonetics)
- Provides scholarly rigor matching academic biblical commentaries

---

## References

- Gesenius' Hebrew Grammar §15: Accentuation
- Yeivin, *Introduction to the Tiberian Masorah*: Complete cantillation guide
- Biblical Hebrew Reference Grammar (van der Merwe): Prosodic structure
