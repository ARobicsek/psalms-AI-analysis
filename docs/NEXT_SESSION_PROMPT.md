# Next Session: Test Pipeline on Selected Psalms

## Context: Where We Are

**Phase 3e: Introduction Context Integration Complete** (2025-10-17):

### Major Update: Verse Commentary Now Sees Introduction

✅ **CRITICAL FIX: Verse commentator can now see the introduction essay**
- Modified `SynthesisWriter` to pass introduction to verse commentary generation
- Verse commentary now complements (not repeats) the introduction
- Results in richer technical detail and better overall coherence

**Test Results (Psalm 20 v3 - WITH introduction context):**
- Introduction essay: **850 words** - Concise, focused, scholarly
- Verse commentary: **11,496 chars** (~115 words/verse)
- Quality improvements:
  - ✅ More technical lexical detail (Septuagint, Ugaritic parallels)
  - ✅ Addresses interpretive debates not covered in introduction
  - ✅ Complements rather than duplicates introduction themes
  - ✅ Better awareness of psalm's overall theological framework

**Comparison (Psalm 20):**
- **v2 (no intro context):** Generic observations, some repetition with intro
- **v3 (with intro context):** Specific textual variants, deeper ANE parallels, awareness of introduction's arguments

### Complete Pipeline Status

✅ **All Components Operational:**
1. ✅ MacroAnalyst - Generates structural thesis
2. ✅ MicroAnalyst - Verse-by-verse discoveries with curiosity-driven research
3. ✅ ResearchBundle - Complete lexicon, concordances, traditional commentary
4. ✅ SynthesisWriter - **NOW includes introduction → verse commentary flow**
5. ✅ Print-Ready Formatter - Divine names, verse text integration

✅ **Pipeline Data Flow (UPDATED):**
```
MacroAnalyst → MicroAnalyst → ResearchBundle
         ↓            ↓              ↓
         +---------+  |              |
                   ↓  ↓              ↓
    Introduction ← [All 3 sources]
         |
         ↓
    Verses       ← [All 3 sources + Introduction] ← NEW!
         ↓
    Print-Ready (Hebrew/English text + divine names)
```

✅ **Bug Fixes Applied:**
- Empty micro discoveries (schema mismatch)
- Aggressive truncation (removed limits)
- Rate limit handling (delay scripts)
- Unicode encoding (UTF-8 for Hebrew)

✅ **Documentation:**
- `docs/PIPELINE_UPDATE_20251017.md` - Full technical details
- `docs/FIXES_APPLIED_20251017.md` - All bug fixes
- `scripts/generate_verse_commentary_only_with_intro.py` - Utility for regenerating verses

---

## Goals for Next Session

### Primary Goal: Test Pipeline on Diverse Psalm Types

**Run 3-5 selected psalms through the COMPLETE pipeline** to validate:
1. Quality across different genres (lament, praise, royal, wisdom)
2. Verse commentary integration with introduction
3. Readiness for full production run

### Recommended Test Psalms

**Essential Set (3 psalms minimum):**
1. **Psalm 23** - Pastoral/Trust (6 verses, most famous psalm)
2. **Psalm 1** - Wisdom/Torah (6 verses, Psalter introduction)
3. **Psalm 51** - Individual Lament (21 verses, penitential)

**Extended Set (5 psalms):**
4. **Psalm 2** - Royal/Messianic (12 verses, enthronement)
5. **Psalm 8** - Creation Hymn (10 verses, human dignity)

**Why these psalms:**
- Cover major psalm genres (wisdom, trust, lament, royal, praise)
- Range of lengths (6-21 verses)
- Theologically significant
- Different structural patterns
- High scholarly interest

### Session Workflow

For EACH selected psalm, run the complete pipeline:

```bash
# Example: Psalm 23

# STEP 1: MacroAnalyst
python src/agents/macro_analyst.py 23 --output-dir output/test_psalm_23

# STEP 2: MicroAnalyst (with database for LXX integration)
python src/agents/micro_analyst.py 23 output/test_psalm_23/psalm_023_macro.json \
  --output-dir output/test_psalm_23 --db-path database/tanakh.db

# STEP 3: SynthesisWriter (with delay for rate limits)
python scripts/run_synthesis_with_delay.py \
  --macro output/test_psalm_23/psalm_023_macro.json \
  --micro output/test_psalm_23/psalm_023_micro_v2.json \
  --research output/test_psalm_23/psalm_023_research_v2.md \
  --output-dir output/test_psalm_23 \
  --output-name psalm_023_synthesis \
  --delay 90

# STEP 4: Print-Ready Formatting
python scripts/create_print_ready_commentary.py \
  --psalm 23 \
  --test-dir output/test_psalm_23 \
  --output psalm_023_print_ready.md

# STEP 5: Review output
cat output/test_psalm_23/psalm_023_print_ready.md | less
```

**IMPORTANT:** Wait 90-120 seconds between running synthesis on different psalms to avoid rate limits.

### Quality Checklist for Each Psalm

After generating each psalm commentary, verify:

**Introduction Essay:**
- [ ] 800-1200 words
- [ ] Cites concordance parallels
- [ ] References traditional commentators (Rashi, Ibn Ezra, Radak, etc.)
- [ ] Integrates micro discoveries
- [ ] Scholarly but accessible tone
- [ ] ANE parallels when relevant

**Verse Commentary:**
- [ ] 100-300 words per verse
- [ ] Varies scholarly angles (poetics, vorlage, Ugaritic, lexical, etc.)
- [ ] Complements (doesn't repeat) introduction
- [ ] Cites specific biblical parallels
- [ ] Engages interpretive debates

**Overall:**
- [ ] Divine names modified correctly (יהוה → ה׳)
- [ ] Hebrew and English verse text integrated
- [ ] Coherent flow from introduction to verse commentary
- [ ] No obvious errors or hallucinations

---

## Production Decision Point

### After testing 3-5 psalms, decide:

**Option A: Full Production Run (All 150 Psalms)**
- Use Message Batches API (recommended)
- 50% cost savings (~$5.25 vs ~$10.50)
- 24-hour async processing
- No rate limits

**Option B: Iterative Refinement**
- Process more test psalms (10-20)
- Fine-tune prompts based on output quality
- Identify and fix edge cases
- Then move to full production

**Option C: Selective Production**
- Process only high-priority psalms (50-75 most famous)
- Faster completion, lower cost
- Focus on psalms with most scholarly interest

### Batch API Implementation (if choosing Option A)

**Workflow:**
1. Generate all macro/micro/research files for Psalms 1-150
2. Create batch request JSON with 300 synthesis calls (150 intro + 150 verses)
3. Submit to Anthropic Batches API
4. Wait ~24 hours
5. Download results and run print-ready formatting
6. Review and iterate

**Script to create:** `scripts/create_batch_request.py`
- Reads all macro/micro/research files
- Generates batch request JSON
- Submits to Anthropic API

**Reference:** `docs/BATCH_API_GUIDE.md` (to be created)

---

## Quick Start Commands for Next Session

### Process Psalm 23 (Essential Test)

```bash
# Full pipeline for Psalm 23
python src/agents/macro_analyst.py 23 --output-dir output/test_psalm_23

python src/agents/micro_analyst.py 23 output/test_psalm_23/psalm_023_macro.json \
  --output-dir output/test_psalm_23 --db-path database/tanakh.db

# Wait 90 seconds after any previous synthesis run
python scripts/run_synthesis_with_delay.py \
  --macro output/test_psalm_23/psalm_023_macro.json \
  --micro output/test_psalm_23/psalm_023_micro_v2.json \
  --research output/test_psalm_23/psalm_023_research_v2.md \
  --output-dir output/test_psalm_23 \
  --output-name psalm_023_synthesis \
  --delay 90

python scripts/create_print_ready_commentary.py \
  --psalm 23 \
  --test-dir output/test_psalm_23
```

### Process Psalm 1 (Wisdom Test)

```bash
# Full pipeline for Psalm 1
python src/agents/macro_analyst.py 1 --output-dir output/test_psalm_1

python src/agents/micro_analyst.py 1 output/test_psalm_1/psalm_001_macro.json \
  --output-dir output/test_psalm_1 --db-path database/tanakh.db

# Wait 90 seconds
python scripts/run_synthesis_with_delay.py \
  --macro output/test_psalm_1/psalm_001_macro.json \
  --micro output/test_psalm_1/psalm_001_micro_v2.json \
  --research output/test_psalm_1/psalm_001_research_v2.md \
  --output-dir output/test_psalm_1 \
  --output-name psalm_001_synthesis \
  --delay 90

python scripts/create_print_ready_commentary.py \
  --psalm 1 \
  --test-dir output/test_psalm_1
```

### Process Psalm 51 (Lament Test)

```bash
# Full pipeline for Psalm 51
python src/agents/macro_analyst.py 51 --output-dir output/test_psalm_51

python src/agents/micro_analyst.py 51 output/test_psalm_51/psalm_051_macro.json \
  --output-dir output/test_psalm_51 --db-path database/tanakh.db

# Wait 90 seconds
python scripts/run_synthesis_with_delay.py \
  --macro output/test_psalm_51/psalm_051_macro.json \
  --micro output/test_psalm_51/psalm_051_micro_v2.json \
  --research output/test_psalm_51/psalm_051_research_v2.md \
  --output-dir output/test_psalm_51 \
  --output-name psalm_051_synthesis \
  --delay 90

python scripts/create_print_ready_commentary.py \
  --psalm 51 \
  --test-dir output/test_psalm_51
```

---

## Success Criteria

### For Next Session:
1. ✅ Generate complete commentaries for 3-5 test psalms
2. ✅ Verify introduction-verse integration working across genres
3. ✅ Confirm quality standards met across different psalm types
4. ✅ Make production decision (full run, selective, or more testing)

### Production Ready Indicators:
- ✅ Tested on 5+ different psalm types
- ✅ Output quality consistently meets scholarly standards
- ✅ Tone appropriate (analytical, not sensationalistic)
- ✅ Introduction-verse integration working smoothly
- ✅ No systematic errors or quality issues
- ✅ Ready to commit to full production run

---

## Current Test Outputs

**Completed Psalms:**
- ✅ **Psalm 29** (nature hymn) - `output/phase3_test/psalm_029_print_ready.md`
- ✅ **Psalm 20 v2** (royal, no intro context) - `output/test_psalm_20_fixed/psalm_020_print_ready_v2.md`
- ✅ **Psalm 20 v3** (royal, WITH intro context) - `output/test_psalm_20_fixed/psalm_020_print_ready_v3.md`

**To Generate:**
- ⏳ Psalm 23 (pastoral/trust)
- ⏳ Psalm 1 (wisdom)
- ⏳ Psalm 51 (lament)
- ⏳ Psalm 2 (royal/messianic) - optional
- ⏳ Psalm 8 (creation) - optional

---

## Technical Notes

### Rate Limits
- **Limit:** 30,000 input tokens per minute
- **Solution:** 90-second delay between synthesis runs
- **Estimate:** ~3 minutes per complete psalm (macro + micro + synthesis + print-ready)

### Token Usage
- **Macro analysis:** ~5K tokens
- **Micro analysis:** ~15K tokens
- **Synthesis (intro):** ~25K tokens (input)
- **Synthesis (verses):** ~30K tokens (input, now includes introduction)
- **Total per psalm:** ~75K input tokens across all API calls

### File Sizes
- **Research bundle:** 150-250K chars (complete lexicon, concordances, commentary)
- **Introduction:** 5-8K chars (800-1200 words)
- **Verse commentary:** 10-25K chars (varies by psalm length)
- **Print-ready:** 15-40K chars (complete with Hebrew/English text)

### Debug Outputs
All synthesis prompts saved to `output/debug/` for inspection:
- `intro_prompt_psalm_NNN.txt` - What intro generation received
- `verse_prompt_psalm_NNN.txt` - What verse generation received (now includes intro!)

---

## System Status

✅ **All systems operational**
✅ **Pipeline validated on 2 psalm types**
✅ **Introduction-verse integration working**
✅ **Divine names modification functional**
✅ **Rate limit handling in place**
✅ **Ready for extended testing**

**Next milestone:** Test 3-5 diverse psalms → Production decision

🎯 **Goal:** Complete commentaries for selected psalms and decide on production approach!
