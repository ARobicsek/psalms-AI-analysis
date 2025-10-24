# Session 18 Plan: Stress-Aware Phonetic System

**Date**: 2025-10-23
**Goal**: Add stress/accent marking to phonetic transcriptions for better prosodic analysis

---

## Executive Summary

### Problem
Current phonetic transcriptions lack stress indicators, making commentary like this unhelpful:
> "The measured rhythm—kə-vōdh mal-khūth-khā yō'-mē-rū—is stately"

**Reader's question**: Which syllables are stressed? How many stresses? What's the meter?

### Solution
Extract stress from cantillation marks (already present in Hebrew text) and mark stressed syllables visually:

**Before**: `kə-vōdh mal-khūth-khā yō-mē-rū`
**After**: `kə-**VŌDH** mal-**KHŪTH**-khā **YŌ**-mē-rū` [3 stresses]

**Enhanced commentary**:
> "The first colon (kə-**VŌDH** mal-**KHŪTH**-khā **YŌ**-mē-rū) has 3 stresses falling on
> vōdh | khūth | yō, creating evenly-spaced beats that convey measured royal proclamation."

---

## Proof of Concept: Psalm 145:11

**Hebrew**: כְּב֣וֹד מַלְכוּתְךָ֣ יֹאמֵ֑רוּ וּגְבוּרָתְךָ֥ יְדַבֵּֽרוּ׃

**Cantillation marks detected**:
- ֣ (Munah) - SECONDARY STRESS - appears on בוֹד and תְךָ
- ֑ (Atnah) - PRIMARY STRESS - appears on מֵרוּ (major division)
- ֥ (Merkha) - SECONDARY STRESS - appears on תְךָ
- ֽ (Silluq/Meteg) - PRIMARY STRESS - appears on בֵּרוּ (verse end)

**Total**: 2 primary + 3 secondary = 5 stress marks

**Stress pattern**: 3+3 (balanced meter)

---

## Implementation Steps

### Step 1: Enhance PhoneticAnalyst (Core Engine)

**File**: `src/agents/phonetic_analyst.py`

**Changes**:
1. Add cantillation-to-stress mapping dictionary (30+ marks)
2. During `_transcribe_word()`, detect cantillation marks and mark stressed syllable
3. Add `stress_level` field to syllable data structure
4. Create `_format_syllables_with_stress()` method
5. Add stress-marked transcription to output JSON

**New output format**:
```python
{
    "word": "מַלְכוּתְךָ֣",
    "transcription": "malkhūthkhā",
    "syllables": [
        {"phonemes": ["m", "a", "l"], "stress": 0},      # unstressed
        {"phonemes": ["kh", "ū", "th"], "stress": 1},    # secondary
        {"phonemes": ["kh", "ā"], "stress": 2}            # PRIMARY
    ],
    "syllable_transcription": "mal-khūth-khā",
    "syllable_transcription_stressed": "mal-khūth-**KHĀ**",
    "stress_count": 1,  # This word has 1 stressed syllable
    "primary_stress_syllable": 2  # Index of primary stress
}
```

**Verse-level enhancement**:
```python
{
    "original_text": "כְּב֣וֹד מַלְכוּתְךָ֣ יֹאמֵ֑רוּ",
    "words": [...],
    "stressed_transcription": "kə-**VŌDH** mal-**KHŪTH**-**KHĀ** **YŌ**-mē-rū",
    "total_stresses": 4,
    "primary_stresses": 2,
    "secondary_stresses": 2
}
```

### Step 2: Update MicroAnalystV2 Integration

**File**: `src/agents/micro_analyst.py`

**No changes needed** - MicroAnalystV2 already calls `PhoneticAnalyst.transcribe_verse()` and
stores the result in `phonetic_transcription` field. The enhanced output will automatically flow through.

**Verification point**: Check that `stressed_transcription` field appears in micro analysis JSON

### Step 3: Update SynthesisWriter Prompts

**File**: `src/agents/synthesis_writer.py`

**Enhancement**: Modify `format_phonetic_section()` to use `stressed_transcription` instead of
plain `syllable_transcription`

**Add to VERSE_COMMENTARY_PROMPT**:
```python
### PHONETIC TRANSCRIPTIONS (with stress marking)

Stressed syllables are shown in **BOLD CAPITALS**.

**Example**:
Verse 11: kə-**VŌDH** mal-**KHŪTH**-khā **YŌ**-mē-rū  [3 stresses]

When analyzing rhythm, meter, or sound patterns:
1. **Count the stresses** - shown in BOLD CAPS
2. **Name the syllables** - cite specific stressed syllables (e.g., "vōdh | khūth | yō")
3. **Show the pattern** - use notation like "3+3" or "3+2"

✓ Good: "The first colon has 3 stresses (kə-**VŌDH** mal-**KHŪTH**-khā **YŌ**-mē-rū:
          vōdh | khūth | yō), creating a balanced, stately rhythm..."

✗ Bad:  "The rhythm is stately" (no evidence, no stress count, no syllable names)
```

### Step 4: Update MasterEditor Prompts

**File**: `src/agents/master_editor.py`

**Add validation checklist**:
```python
### PHONETIC ANALYSIS VALIDATION

When the synthesis writer discusses rhythm, meter, or prosody, verify:

1. **Stress count accuracy**: Count the BOLD CAPITAL syllables in the phonetic transcription
2. **Pattern specificity**: Require patterns like "3+3" or "2+2+2" not vague "rhythmic"
3. **Syllable naming**: Require specific syllables cited (e.g., "vōdh | khūth | yō")
4. **Evidence-based claims**: Flag unsupported claims like "flowing" or "stately" without metrics

If the synthesis writer says "the rhythm is X," require them to:
- Show the stress count
- Name the stressed syllables
- Cite the specific phonetic transcription
```

### Step 5: Update Commentary Formatter

**File**: `src/utils/commentary_formatter.py`

**Enhancement**: Show stress-marked phonetics in print-ready bilingual display

**Current format**:
```
Hebrew:     כְּב֣וֹד מַלְכוּתְךָ֣ יֹאמֵ֑רוּ
English:    They shall speak the glory of Your kingdom
```

**Enhanced format**:
```
Hebrew:     כְּב֣וֹד מַלְכוּתְךָ֣ יֹאמֵ֑רוּ
Phonetic:   kə-**VŌDH** mal-**KHŪTH**-khā **YŌ**-mē-rū  [3 stresses]
English:    They shall speak the glory of Your kingdom
```

**Implementation**: Read `stressed_transcription` field from micro analysis JSON

### Step 6: Update Document Generator

**File**: `src/utils/document_generator.py`

**Enhancement**: Render stress-marked phonetics in Word document

**Markdown parsing**: Convert `**VŌDH**` → bold uppercase in Word
**Table layout**: Add phonetic row between Hebrew and English

---

## Cantillation Mark Reference

### Primary Stress (Level 2) - Always Stressed

| Unicode | Name | Position | Function |
|---------|------|----------|----------|
| U+05BD (ֽ◌) | Silluq | Verse end | Strongest stress |
| U+0591 (֑◌) | Atnah | Mid-verse | Major division |
| U+0594 (֔◌) | Zaqef Qaton | Major | Major pause |
| U+0595 (֕◌) | Zaqef Gadol | Major | Major pause |
| U+0596 (֖◌) | Tifcha | Major | Major pause |
| U+0597 (֗◌) | R'vi'i | Major | Major pause |
| U+0598 (֘◌) | Zarqa | Major | Major pause |
| U+0599 (֙◌) | Pashta | Major | Major pause |
| U+059A (֚◌) | Yetiv | Major | Major pause |
| U+059B (֛◌) | Tevir | Major | Major pause |

### Secondary Stress (Level 1) - Sometimes Stressed

| Unicode | Name | Position | Function |
|---------|------|----------|----------|
| U+05A3 (֣◌) | Munach | Conjunctive | Minor stress |
| U+05A4 (֤◌) | Mahpakh | Conjunctive | Minor stress |
| U+05A5 (֥◌) | Mercha | Conjunctive | Minor stress |

### Implementation Notes

1. **Unicode normalization**: Use NFD to separate base characters from diacritics
2. **Syllable assignment**: Stress mark attaches to the syllable containing the marked letter
3. **Multiple marks**: If both primary and secondary on same word, primary takes precedence
4. **Proclitics**: Prepositions/conjunctions typically unstressed (no marks)

---

## Expected Outcomes

### Quantitative Improvements

**Before enhancement**:
- Vague rhythm claims: "the line is stately"
- No stress counts
- No syllable identification
- Reader can't verify claims

**After enhancement**:
- Specific stress counts: "3+3 pattern"
- Named syllables: "vōdh | khūth | yō"
- Verifiable evidence: reader can count BOLD CAPS
- Pedagogically clear

### Qualitative Example

**Psalm 145:11 - Before**:
> "The line has a measured rhythm suitable for proclamation."

**Psalm 145:11 - After**:
> "The verse exhibits a balanced 3+3 stress pattern. The first colon (kə-**VŌDH**
> mal-**KHŪTH**-khā **YŌ**-mē-rū) places stress on vōdh | khūth | yō, creating three
> evenly-spaced beats. The second colon (ū-**GHƏ**-vū-**RĀ**-thə-**KHĀ** **YƏ**-dha-bē-rū)
> mirrors this with 3 stresses (ghə | rā | khā), maintaining the stately meter that
> befits royal proclamation."

**Improvement**: Specific, verifiable, pedagogically rich

---

## Testing Plan

### Unit Tests

1. **Cantillation detection**: Verify stress marks extracted correctly
   - Test: Psalm 145:11 → expect 2 primary + 3 secondary
   - Verify: Each mark mapped to correct syllable

2. **Stress formatting**: Verify BOLD CAPS rendering
   - Test: `mal-khūth-khā` with stress on khā
   - Expect: `mal-khūth-**KHĀ**`

3. **Stress counting**: Verify total stress count
   - Test: Verse with 6 words, 4 stressed
   - Expect: `stress_count: 4`

### Integration Tests

1. **MicroAnalystV2 → JSON**: Run micro analyst on Psalm 145:11
   - Verify: `stressed_transcription` field present in JSON
   - Verify: Stress count matches manual count

2. **SynthesisWriter → Commentary**: Generate verse commentary
   - Verify: Prompt includes stress-marked phonetics
   - Verify: Commentary cites specific stress patterns

3. **MasterEditor → Validation**: Editorial review
   - Verify: Editor validates stress claims
   - Verify: Vague claims flagged

4. **Formatter → Print-ready**: Generate print-ready output
   - Verify: Phonetic row shows BOLD CAPS
   - Verify: Markdown renders correctly

### Validation Tests

1. **Manual verification**: Expert checks Psalm 145:11 stress pattern
2. **Pattern diversity**: Test various meters (3+3, 3+2, 2+2+2)
3. **Edge cases**: Verses with unusual stress patterns

---

## Timeline

**Session 18** (Current):
- [x] Create implementation plan
- [x] Test cantillation extraction (POC script)
- [ ] Enhance PhoneticAnalyst with stress detection (2 hours)
- [ ] Test on Psalm 145:11 (30 min)

**Session 19**:
- [ ] Update SynthesisWriter prompts (1 hour)
- [ ] Update MasterEditor prompts (1 hour)
- [ ] Update formatters (1 hour)
- [ ] Integration test on Psalm 145 (1 hour)

**Session 20**:
- [ ] Full pipeline test on diverse psalms
- [ ] Validate commentary quality improvement
- [ ] Document results in IMPLEMENTATION_LOG.md

---

## Files to Modify

### Core Engine
1. `src/agents/phonetic_analyst.py` - Add stress detection (150 lines)

### Prompts
2. `src/agents/synthesis_writer.py` - Update prompts + format helper (50 lines)
3. `src/agents/master_editor.py` - Add validation criteria (30 lines)

### Formatters
4. `src/utils/commentary_formatter.py` - Add phonetic row (40 lines)
5. `src/utils/document_generator.py` - Render stress marks (30 lines)

### Documentation
6. `docs/IMPLEMENTATION_LOG.md` - Session 18 entry
7. `docs/NEXT_SESSION_PROMPT.md` - Update with stress enhancement

---

## Backward Compatibility

✅ **Fully backward compatible**
- Existing `syllable_transcription` field preserved
- New `stressed_transcription` field added alongside
- Old pipelines continue to work
- New pipelines automatically use stress marking

---

## Next Steps

**Immediate (this session)**:
1. Implement stress detection in PhoneticAnalyst
2. Test on Psalm 145:11
3. Validate stress extraction accuracy

**Next session**:
1. Update all prompts
2. Update all formatters
3. Full integration test
4. Regenerate Psalm 145 with stress-aware commentary

---

## Success Criteria

✅ Phonetic transcriptions include visible stress marks
✅ Stress counts accurate (verified against manual analysis)
✅ Commentary cites specific stressed syllables
✅ Meter patterns shown explicitly (e.g., "3+3")
✅ Readers can verify prosodic claims
✅ Master Editor validates stress-based claims
