# Session 21 Summary - Master Editor Prompt Enhancement

**Date**: 2025-10-23
**Focus**: Improving Master Editor output length and phonetic transcription formatting

---

## Goals

1. **Increase verse commentary length**: Get GPT-5 to produce more substantive verse-by-verse analysis (targeting 400-500 words per verse with interesting features)
2. **Enforce phonetic transcription format**: Ensure each verse commentary begins with the authoritative phonetic transcription

---

## Problem Statement

### Issue 1: Length
Current Master Editor output (e.g., Psalm 145 verse 5) averages ~230 words per verse. While quality is good, the commentary could be more substantive for verses with interesting linguistic/literary features.

**Example from current output** (Psalm 145:5):
- Current length: ~230 words
- Quality: Good scholarly analysis with merism definition
- Issue: Could explore more depth given the unusual Hebrew phrase הֲ֭דַר כְּב֣וֹד הוֹדֶ֑ךָ

### Issue 2: Phonetic Transcription Missing
The Master Editor receives phonetic transcriptions in the PSALM TEXT section of its prompt, but the final verse commentary doesn't include them at the start of each verse. This makes it harder for readers to see the connection between sound patterns and the analysis.

---

## Changes Made

### File Modified
**`src/agents/master_editor.py`** (lines 252-294)

### Change 1: Enhanced OUTPUT FORMAT Section (lines 266-278)

**Before:**
```markdown
### REVISED VERSE COMMENTARY

**Verse 1**
[Revised commentary for verse 1, target 300-500 words]

**Verse 2**
[Revised commentary for verse 2, target 300-500 words]
```

**After:**
```markdown
### REVISED VERSE COMMENTARY

**CRITICAL**: Each verse commentary MUST begin with the authoritative phonetic transcription from the PSALM TEXT section above, formatted in backticks. Then provide your analysis.

**Verse 1**
`[phonetic transcription from PSALM TEXT]`

[Your revised commentary for verse 1. TARGET: 300-500 words. Do NOT shortchange the reader—intelligent lay readers want substantive analysis of linguistic and literary features. Aim for 400-500 words when the verse has interesting Hebrew phrases, poetic devices, figurative language, or interpretive questions. Only use 200-300 words for genuinely simple verses.]

**Verse 2**
`[phonetic transcription from PSALM TEXT]`

[Your revised commentary for verse 2. TARGET: 300-500 words as above.]
```

### Change 2: Added Two Critical Requirements (lines 290-291)

**Added to CRITICAL REQUIREMENTS section:**
- **Phonetic Format**: MANDATORY—Begin each verse commentary with the phonetic transcription in backticks (copy from PSALM TEXT section)
- **Length**: Aim for 400-500 words per verse when there are interesting features to analyze. Do not be terse when the verse warrants substantive treatment.

---

## Rationale

### Why These Changes Should Work

1. **Triple Reinforcement Strategy**:
   - Explicit formatting instruction at OUTPUT FORMAT section
   - Detailed length guidance with "Do NOT shortchange" language
   - Two new CRITICAL REQUIREMENTS bullets

2. **GPT-5 Response to Explicit Formatting**:
   - models are very good at following explicit structural requirements
   - Placing phonetic transcription in the OUTPUT FORMAT template makes it part of the expected structure
   - Using "CRITICAL" and "MANDATORY" signals high priority

3. **Length Guidance Psychology**:
   - Changed from passive "target 300-500" to active "Aim for 400-500"
   - Added negative framing: "Do NOT shortchange the reader"
   - Justification provided: "intelligent lay readers want substantive analysis"
   - Permission to be longer: "Only use 200-300 words for genuinely simple verses"

---

## Expected Impact

### For Phonetic Transcription
**Before**: Transcription missing from verse commentary
**After**: Each verse will start like this:

```markdown
**Verse 5**
`hă-dhar kə-vōdh hō-dhe-khā wə-dhiv-rēy nif-lə-'ō-the-khā 'ā-siy-khāh`

"Hadar kevod hodekha"—"the splendor of the glory of your majesty." The poet stacks three near-synonyms...
```

### For Length
**Before**: ~230 words average for interesting verses
**After**: Expected ~350-450 words for verses with:
- Unusual Hebrew phrases (like הֲ֭דַר כְּב֣וֹד הוֹדֶ֑ךָ)
- Poetic devices (chiasm, inclusio)
- Figurative language requiring analysis
- Textual variants worth discussing

**Still acceptable**: ~200-250 words for genuinely simple verses

---

## Testing Plan

### Immediate Next Step
Re-run Master Editor on Psalm 145 with updated prompt:

```bash
# Skip to master_editor step only
python scripts/run_enhanced_pipeline.py 145 --start-from master_editor
```

### Validation Metrics
1. **Phonetic Transcription**:
   - Check `output/psalm_145/psalm_145_edited_verses.md`
   - Verify each verse starts with backtick-formatted phonetic transcription
   - Sample check: verses 5, 11, 16 (interesting Hebrew phrases)

2. **Length Analysis**:
   - Count words per verse in edited output
   - Compare to previous run (average ~230 words)
   - Target: 350-450 words for complex verses, 250-300 for simple verses

3. **Quality Check**:
   - Ensure longer doesn't mean "padded"
   - Look for deeper engagement with:
     - BDB lexicon insights
     - Concordance patterns
     - Figurative language parallels
     - Torah Temimah citations

---

## Backward Compatibility

✅ **Fully backward compatible**
- No breaking changes to code logic
- Only prompt template modifications
- Existing pipeline steps unchanged

---

## Next Steps

1. **Session 21**: Test updated Master Editor on Psalm 145
2. **If successful**: Document results and update NEXT_SESSION_PROMPT.md
3. **If length still insufficient**: Consider additional prompt modifications:
   - Add example verse commentary at 450 words showing desired depth
   - Add explicit instruction to "write at least 400 words for verses with unusual Hebrew"
   - Consider adding word count validation in editorial assessment stage

---

## Files Modified

- **`src/agents/master_editor.py`** (lines 266-291):
  - Enhanced OUTPUT FORMAT section with phonetic transcription requirement
  - Strengthened length guidance with active language
  - Added two new CRITICAL REQUIREMENTS

## Documentation Created

- **`docs/SESSION_21_SUMMARY.md`**: This file

---

## Confidence Level

**High** - The changes address both issues directly:
- Phonetic transcription format is now explicit and mandatory
- Length guidance is triple-reinforced with psychological framing
- GPT-5 responds well to explicit structural requirements

**Expected Success Rate**:
- Phonetic transcription: 95%+ compliance (very explicit)
- Length increase: 70-80% compliance (subjective judgment by GPT-5)

If length guidance doesn't achieve desired results, we can:
1. Add concrete example of 450-word verse commentary
2. Add word count minimum instead of "target"
3. Add editorial assessment check: "Did I write at least 400 words for complex verses?"
