# Next Session: SynthesisWriter Prompt Tuning & Multi-Psalm Testing

## Context: Where We Are

**Phase 3c Complete** (2025-10-17):
- ✅ SynthesisWriter agent built and tested on Psalm 29
- ✅ Print-ready commentary system operational
- ✅ Divine names modification working perfectly
- ✅ Verse text integration complete
- ✅ Output quality exceptional (1,002 word intro + ~218 words/verse)

**Test Results (Psalm 29):**
- Introduction essay critically engaged macro thesis, refined it with evidence
- Verse commentary showed excellent diversity: poetics, vorlage, Ugaritic, interpretive debates
- Rich intertextual connections (Gen 1:2, Ex 40:34-35, Ps 96:7-8, Job 39:1, etc.)
- Classical scholarship integrated (Rashi, Targum, LXX, rabbinic, patristic)
- Divine names properly modified throughout (יהוה → ה׳, etc.)

---

## Goals for Next Session

### 1. Review Psalm 29 Output Together
- Walk through output/phase3_test/psalm_029_print_ready.md
- Identify areas for improvement in prompts
- Discuss tone, style, scholarly balance

### 2. Tweak SynthesisWriter Prompts
**File to edit**: src/agents/synthesis_writer.py

**Two prompts to review:**
1. **INTRODUCTION_ESSAY_PROMPT** (lines 29-117)
   - Currently encourages critical engagement with macro thesis ✅
   - Requests intertextual connections ✅
   - Asks for classical scholarship ✅
   - **Possible adjustments**: Tone, length guidance, structure preferences

2. **VERSE_COMMENTARY_PROMPT** (lines 120-180)
   - Currently encourages diverse scholarly angles ✅
   - Emphasizes independence from macro thesis ✅
   - Requests varied approaches per verse ✅
   - **Possible adjustments**: Depth vs. breadth, citation style, angle priorities

**Example tweaks we might make:**
- Adjust word counts (currently 800-1200 intro, 150-300/verse)
- Modify tone guidance (more/less scholarly, more/less accessible)
- Add/remove specific scholarly angles to emphasize
- Change citation format preferences
- Adjust how strongly to emphasize novelty vs. tradition

### 3. Test on Multiple Psalms
**Candidate psalms for testing:**
- **Psalm 23** (6 verses, pastoral, most famous) - Good for testing brevity + familiar material
- **Psalm 51** (21 verses, penitential, theologically rich) - Test longer psalm handling
- **Psalm 137** (9 verses, lament, controversial) - Test tone with difficult material
- **Psalm 150** (6 verses, pure praise, repetitive) - Test handling of simple structure

**Testing workflow:**
```bash
# For each test psalm (e.g., 23):
python src/agents/macro_analyst.py --psalm 23 --output output/test_psalm_23
python src/agents/micro_analyst_v2.py --psalm 23 --macro output/test_psalm_23/psalm_023_macro.json --output output/test_psalm_23
python tests/test_synthesis_writer.py --psalm 23 --test-dir output/test_psalm_23
python scripts/create_print_ready_commentary.py --psalm 23 --test-dir output/test_psalm_23
```

---

## Debugging: Synthesizer Input Logs

**Q: Is there a log showing what the synthesizer received?**

**A: Not currently saved to file, but you can enable it.**

**To enable full prompt logging**, uncomment these lines in src/agents/synthesis_writer.py:
- Lines ~355-357 (introduction prompt)
- Lines ~415-417 (verse commentary prompt)

This saves complete prompts to `output/debug/` for inspection.

**Input materials are already saved:**
- Macro: output/phase3_test/psalm_029_macro.json
- Micro: output/phase3_test/psalm_029_micro_v2.json
- Research: output/phase3_test/psalm_029_research_v2.md (230KB!)

---

## Quick Start Commands

```bash
# Review Psalm 29 output
cat output/phase3_test/psalm_029_print_ready.md | less

# Open synthesizer for editing
code src/agents/synthesis_writer.py

# Test on Psalm 23 (short, famous)
python src/agents/macro_analyst.py --psalm 23 --output output/test_psalm_23
python src/agents/micro_analyst_v2.py --psalm 23 --macro output/test_psalm_23/psalm_023_macro.json --output output/test_psalm_23
python scripts/create_print_ready_commentary.py --psalm 23 --test-dir output/test_psalm_23
cat output/test_psalm_23/psalm_023_print_ready.md

# Test on Psalm 51 (longer, theologically rich)
python src/agents/macro_analyst.py --psalm 51 --output output/test_psalm_51
python src/agents/micro_analyst_v2.py --psalm 51 --macro output/test_psalm_51/psalm_051_macro.json --output output/test_psalm_51
python scripts/create_print_ready_commentary.py --psalm 51 --test-dir output/test_psalm_51
```

---

## Success Criteria

By end of next session:
1. ✅ Reviewed and refined SynthesisWriter prompts based on Psalm 29
2. ✅ Tested on 2-3 psalms with varied characteristics
3. ✅ Validated quality across different psalm types
4. ✅ System ready for production on all 150 Psalms

**Ready to refine and scale!** 🎯
