# Commentary Coverage Experiment

**Date**: 2025-10-22
**Goal**: Compare selective vs. comprehensive commentary coverage
**Test Psalm**: Psalm 1 (6 verses)

---

## Experiment Design

### Baseline (Previous Approach)
- **Commentators**: 6 (Rashi, Ibn Ezra, Radak, Metzudat David, Malbim, Meiri)
- **Coverage**: Selective (2-5 key verses per psalm based on interpretive puzzles)
- **Philosophy**: Request commentary only where classical interpretation adds unique value
- **Typical request count**: 2-5 verses per psalm

### Enhanced (New Approach)
- **Commentators**: 7 (adds Torah Temimah - Talmudic citations)
- **Coverage**: Comprehensive (ALL verses receive commentary)
- **Philosophy**: Provide classical grounding for every verse, let Synthesis/Editor select what's useful
- **Request count**: All 6 verses for Psalm 1

---

## Hypotheses

### H1: Research Bundle Size
**Prediction**: Research bundle will increase by 10-14%
- **Rationale**: Commentaries currently represent small fraction of bundle (lexicon + concordance + figurative dominate)
- **Torah Temimah**: ~1,085 characters per verse (comparable to existing commentators)
- **Comprehensive coverage**: ~6,000-8,000 additional characters for Psalm 1

### H2: Token Cost Impact
**Prediction**: Total pipeline cost will increase by 5-8%
- **Rationale**: Commentary is only one component of research bundle
- **Larger impact on**: Synthesis Writer (processes full bundle twice: intro + verses)
- **Smaller impact on**: Master Editor (samples first 5 verses only)

### H3: Output Quality - Citation Frequency
**Prediction**: Synthesis Writer will cite traditional commentators 2-3x more frequently
- **Baseline**: Sparse classical citations (only when specific puzzle addressed)
- **Enhanced**: Rich traditional grounding available for every verse
- **Measurement**: Count references to Rashi, Ibn Ezra, Radak, etc. in final output

### H4: Output Quality - Depth
**Prediction**: Verse commentary will integrate more traditional perspectives
- **Baseline**: Modern scholarly analysis with occasional classical reference
- **Enhanced**: Dialogue between modern and traditional interpretation
- **Measurement**: Qualitative assessment of traditional engagement

### H5: Torah Temimah Impact
**Prediction**: Torah Temimah will add unique Talmudic perspective
- **Rationale**: Only Hebrew-only source; only Talmudic citation source
- **Expected**: References to Talmudic passages linking psalms to rabbinic literature
- **Measurement**: Count Torah Temimah citations; assess whether Talmudic connections appear

---

## Metrics to Collect

### Quantitative Metrics

#### Research Bundle
- [ ] Character count (total)
- [ ] Character count (commentary section only)
- [ ] Percentage increase from baseline
- [ ] Number of commentary entries (6 verses × 7 commentators = ~42 entries)

#### Token Costs
- [ ] Macro Analysis tokens
- [ ] Micro Analysis tokens
- [ ] Research Assembly tokens
- [ ] Synthesis Writer tokens (intro)
- [ ] Synthesis Writer tokens (verses)
- [ ] Master Editor tokens
- [ ] **Total cost** (compare to baseline)
- [ ] **Percentage increase**

#### Citation Frequency (in final output)
- [ ] Introduction: Count classical commentator references
- [ ] Verse commentary: Count classical commentator references per verse
- [ ] Torah Temimah specific citations
- [ ] Talmudic passage references (tractate + page)

### Qualitative Metrics

#### Output Quality Assessment
- [ ] **Traditional grounding**: Does each verse commentary reference classical sources?
- [ ] **Talmudic connections**: Does Torah Temimah add unique insights not in other 6?
- [ ] **Synthesis depth**: Is traditional interpretation integrated or just cited?
- [ ] **Master Editor engagement**: Does GPT-5 validate/enhance classical references?

#### Comparison Questions
1. Which verses benefit most from comprehensive commentary coverage?
2. Are there verses where commentary adds minimal value?
3. Does Torah Temimah provide distinct perspective vs. existing 6?
4. Do Synthesis Writer and Master Editor effectively use additional commentary?
5. Is the cost/value ratio favorable for comprehensive coverage?

---

## Test Procedure

### Step 1: Run Enhanced Pipeline
```bash
python scripts/run_enhanced_pipeline.py 1 \
    --output-dir output/psalm_1_enhanced_commentary \
    --db-path database/tanakh.db
```

**Expected Duration**: ~15-20 minutes
**Expected Cost**: $0.60-0.85 (with commentary increase)

### Step 2: Collect Baseline Data
From previous Psalm 1 run (if available):
- `output/test_psalm_1/psalm_001_research_v2.md` - Research bundle
- `output/test_psalm_1/psalm_001_pipeline_stats.json` - Token costs
- `output/test_psalm_1/psalm_001_synthesis_verses.md` - Citations
- `output/test_psalm_1/psalm_001_edited_verses.md` - Final output

### Step 3: Collect Enhanced Data
From new run:
- `output/psalm_1_enhanced_commentary/psalm_001_research_v2.md`
- `output/psalm_1_enhanced_commentary/psalm_001_pipeline_stats.json`
- `output/psalm_1_enhanced_commentary/psalm_001_synthesis_verses.md`
- `output/psalm_1_enhanced_commentary/psalm_001_edited_verses.md`

### Step 4: Quantitative Analysis
```python
# Character count comparison
baseline_research = len(open('output/test_psalm_1/psalm_001_research_v2.md').read())
enhanced_research = len(open('output/psalm_1_enhanced_commentary/psalm_001_research_v2.md').read())
increase_pct = ((enhanced_research - baseline_research) / baseline_research) * 100

# Token cost comparison
import json
baseline_stats = json.load(open('output/test_psalm_1/psalm_001_pipeline_stats.json'))
enhanced_stats = json.load(open('output/psalm_1_enhanced_commentary/psalm_001_pipeline_stats.json'))

# Extract total costs
baseline_cost = sum([step['cost'] for step in baseline_stats['steps'].values()])
enhanced_cost = sum([step['cost'] for step in enhanced_stats['steps'].values()])
cost_increase_pct = ((enhanced_cost - baseline_cost) / baseline_cost) * 100
```

### Step 5: Qualitative Analysis
Manual review of:
1. **Research Bundle**: Scroll through commentary section, note Torah Temimah entries
2. **Introduction**: Count classical commentator names, assess integration depth
3. **Verse Commentary**: For each verse, note:
   - Classical sources cited
   - Torah Temimah references (if any)
   - Depth of traditional engagement
4. **Master Editor Output**: Compare to Synthesis, check editorial enhancement of classical references

---

## Decision Criteria

### Adopt Comprehensive Coverage If:
✅ Cost increase < 10% total pipeline cost
✅ Citation frequency increase > 2x
✅ Torah Temimah adds unique Talmudic perspective
✅ Quality assessment shows meaningful traditional engagement
✅ No verses show "commentary overload" (too many competing interpretations)

### Revert to Selective Coverage If:
❌ Cost increase > 15% total pipeline cost
❌ Synthesis Writer ignores most commentary (low utilization)
❌ Torah Temimah duplicates existing 6 commentators
❌ Output quality unchanged or decreased
❌ Research bundle becomes unwieldy (>400k characters)

### Hybrid Approach If:
⚠️ Some verses benefit greatly, others minimally
⚠️ Torah Temimah valuable but other 6 sufficient
⚠️ Cost increase marginal but quality improvement unclear

**Possible Hybrid**: Request all 7 commentators for complex/ambiguous verses only

---

## Expected Outcomes

### Most Likely Scenario
- **Cost increase**: 5-8% (within acceptable range)
- **Research bundle**: +12% size (manageable)
- **Citation frequency**: 2-3x increase (meaningful improvement)
- **Torah Temimah**: 1-2 unique Talmudic insights per psalm
- **Quality**: Richer traditional grounding, especially for Torah study themes

### Decision
**Adopt comprehensive 7-commentator coverage as new default.**

### Rationale
- Commentaries represent small fraction of total cost (~5-8% increase)
- Comprehensive coverage provides fuller scholarly grounding
- Synthesis Writer can selectively cite what's most relevant
- Torah Temimah adds unique Talmudic dimension (not available elsewhere)
- Easy to revert if empirical results show otherwise

---

## Documentation Plan

### After Test Run
1. **Create**: `COMMENTARY_EXPERIMENT_RESULTS.md` with metrics
2. **Update**: `IMPLEMENTATION_LOG.md` with findings
3. **Update**: `NEXT_SESSION_PROMPT.md` with decision
4. **Update**: `TECHNICAL_ARCHITECTURE_SUMMARY.md` if coverage policy changes

### Long-Term Tracking
- Monitor commentary utilization across 5-10 diverse psalms
- Track cost/value ratio over time
- Document verses where comprehensive coverage adds most value
- Identify patterns where selective coverage sufficient

---

## Timeline

**Experiment Setup**: 2025-10-22 (complete)
**Test Run**: Ready to execute (awaiting user approval)
**Results Analysis**: ~30 minutes after test completion
**Decision**: Same session as results analysis
**Documentation**: Same session as decision

---

## Notes

### Why This Experiment Matters
- Commentary is the only research component where coverage policy is discretionary
- Lexicon, concordance, and figurative searches are query-driven (not verse-driven)
- Classical commentators provide authoritative traditional interpretation
- Balance between cost and comprehensiveness is empirically testable

### Why Now
- Torah Temimah just added (7th commentator)
- Natural inflection point to reconsider coverage policy
- Psalm 1 is ideal test case (short, theologically rich, well-documented)
- Low cost to run experiment (~$0.80)

### Success Criteria
This experiment succeeds if it provides clear empirical data for coverage policy decision, regardless of which approach proves superior.

---

**Status**: ✅ Ready to Execute
**Blocked By**: User approval to run pipeline
**Next Action**: `python scripts/run_enhanced_pipeline.py 1 --output-dir output/psalm_1_enhanced_commentary`
