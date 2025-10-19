# Quick Start Guide: Phase 4 Enhanced Pipeline

**Goal:** Generate National Book Award-level psalm commentary with GPT-5 master editing

---

## Prerequisites

### 1. API Keys (in `.env` file)

```bash
ANTHROPIC_API_KEY=sk-ant-...  # For Claude Sonnet 4.5
OPENAI_API_KEY=sk-proj-...     # For GPT-5
```

### 2. Database Files

- ✅ `database/tanakh.db` - Hebrew Bible with LXX
- ✅ `C:/Users/ariro/OneDrive/Documents/Bible/database/Pentateuch_Psalms_fig_language.db`

---

## Single Command: Run Complete Enhanced Pipeline

```bash
# Generate complete master-edited commentary for Psalm 23
python scripts/run_enhanced_pipeline.py 23
```

**Output:**
- `output/test_psalm_23/psalm_023_macro.json` - Structural analysis
- `output/test_psalm_23/psalm_023_micro_v2.json` - Verse discoveries
- `output/test_psalm_23/psalm_023_research_v2.md` - Full research bundle
- `output/test_psalm_23/psalm_023_synthesis_intro.md` - Introduction (Claude)
- `output/test_psalm_23/psalm_023_synthesis_verses.md` - Verses (Claude)
- `output/test_psalm_23/psalm_023_assessment.md` - Editorial notes (GPT-5)
- `output/test_psalm_23/psalm_023_edited_intro.md` - **Revised introduction (GPT-5)**
- `output/test_psalm_23/psalm_023_edited_verses.md` - **Revised verses (GPT-5)**
- `output/test_psalm_23/psalm_023_print_ready.md` - **FINAL OUTPUT**

**Duration:** ~8-10 minutes per psalm (includes 120-second delays for rate limiting)

---

## Pipeline Steps Explained

### Step 1: MacroAnalyst (Claude Sonnet 4.5)
- Generates structural thesis
- Identifies poetic devices
- Creates verse outline
- **Duration:** ~30 seconds

### Step 2: MicroAnalyst v2 (Claude Sonnet 4.5)
- Verse-by-verse discovery pass
- **Enhanced figurative language search** (hierarchical, broader terms)
- Generates research requests
- Assembles research bundle
- **Duration:** ~60 seconds

### Step 3: SynthesisWriter (Claude Sonnet 4.5)
- Writes introduction essay (800-1200 words)
- Writes verse commentary (150-400+ words per verse)
- **Enhanced prompts** with 11 categories of scholarly interest
- **Duration:** ~90-120 seconds

### Step 4: MasterEditor (GPT-5 o1) ← NEW!
- Critical editorial review
- Identifies factual errors, missed insights, style issues
- **Revises introduction and verses to "National Book Award" level**
- **Duration:** ~2-5 minutes

### Step 5: Print-Ready Formatting
- Integrates Hebrew/English verse text
- Modifies divine names (יהוה → ה׳)
- Creates final formatted output
- **Duration:** ~5 seconds

---

## Common Usage Patterns

### Test on Essential Psalms

```bash
# Psalm 23 (Pastoral/Trust - 6 verses)
python scripts/run_enhanced_pipeline.py 23

# Psalm 1 (Wisdom - 6 verses)
python scripts/run_enhanced_pipeline.py 1

# Psalm 51 (Lament - 21 verses)
python scripts/run_enhanced_pipeline.py 51
```

### Custom Output Directory

```bash
python scripts/run_enhanced_pipeline.py 23 --output-dir output/psalm_23_final
```

### Resume from Specific Step

```bash
# Skip macro and micro (use existing files)
python scripts/run_enhanced_pipeline.py 23 --skip-macro --skip-micro

# Skip master editing (use Claude synthesis only)
python scripts/run_enhanced_pipeline.py 23 --skip-master-edit
```

### Adjust Rate Limiting

```bash
# Default is 120 seconds (recommended for Phase 4)
# Reduce for faster testing (may hit rate limits on longer psalms):
python scripts/run_enhanced_pipeline.py 51 --delay 90

# Increase for extra safety (longer psalms, network issues):
python scripts/run_enhanced_pipeline.py 51 --delay 150
```

---

## Output Quality Comparison

### Before Phase 4 (Claude Only)

```markdown
**Verse 1**
The opening verse establishes the shepherd metaphor that dominates
the psalm. The Hebrew רעה (to shepherd) appears throughout the
Psalter in contexts of divine care...

[~200 words, good but somewhat generic]
```

### After Phase 4 (Claude + GPT-5 Master Edit)

```markdown
**Verse 1**
The poet opens with a deceptively simple declaration: יהוה רעי
("YHWH is my shepherd"). But this is not pastoral sentimentality—
it's a radical theological claim. In the Ancient Near East, "shepherd"
(רעה) was royal language. Hammurabi calls himself "the shepherd"
of Babylon; Egyptian pharaohs bore the epithet "good shepherd."
By appropriating this imagery for Israel's God, the psalmist makes
a counter-cultural assertion: the true king is not a human monarch
but the divine shepherd who provides rather than demands...

The verb רעה, from the root ר-ע-ה, carries a semantic range that
extends beyond literal shepherding to include "tend," "feed," "lead,"
and "pasture." The BDB lexicon notes its use in royal contexts (Ezek
34:2-10) where failed kings are condemned as "shepherds who feed
themselves." Here, by contrast, is the shepherd who feeds his flock.

The LXX renders this as ὁ κύριος ποιμαίνει με, using the present
tense to emphasize ongoing action. This is not a one-time act but
a continuous reality...

[~350 words, specific, engaging, grounded in research]
```

**Key Improvements:**
- Specific ANE parallels (Hammurabi, Egyptian pharaohs)
- Lexical depth (BDB semantic range, root analysis)
- LXX insights (Greek tense choice)
- Theological nuance (counter-cultural claim)
- Intertextual connections (Ezek 34)
- Accessible scholarly tone (no undefined jargon)

---

## Troubleshooting

### Rate Limit Errors

**Problem:** `RateLimitError: Request too large for token bucket`

**Solution:**
```bash
# Increase delay between steps
python scripts/run_enhanced_pipeline.py 23 --delay 120
```

### GPT-5 Timeout

**Problem:** Master editing takes >5 minutes or times out

**Solution:**
- This is normal for longer psalms (20+ verses)
- GPT-5 (o1) does extended reasoning
- Wait patiently or use `--skip-master-edit` for testing

### Missing Database

**Problem:** `FileNotFoundError: Figurative language database not found`

**Solution:**
```bash
# Verify figurative database exists
ls "C:/Users/ariro/OneDrive/Documents/Bible/database/Pentateuch_Psalms_fig_language.db"

# If missing, check path in src/agents/figurative_librarian.py
```

---

## Next Steps After Testing

### Option A: Full Production Run (All 150 Psalms)

**Recommended:** Use Anthropic Message Batches API
- 50% cost savings (~$60 vs ~$120)
- 24-hour async processing
- No rate limits

**Steps:**
1. Generate all macro/micro/research for Psalms 1-150
2. Create batch request for all synthesis calls
3. Submit to Anthropic Batches API
4. Wait ~24 hours
5. Run master editing on all outputs (can be parallelized)
6. Generate print-ready for all

### Option B: Selective Production

Process only high-priority psalms:
- Psalm 1 (Psalter introduction)
- Psalms 2, 8, 22, 23 (Most famous)
- Psalms 51, 90, 103, 104 (Theological importance)
- Psalms 119, 150 (Structural significance)

### Option C: Iterative Refinement

- Process 10-20 more test psalms
- Fine-tune prompts based on output
- Identify and fix edge cases
- Then move to full production

---

## Cost Estimates

### Per Psalm (Average 12 verses)

- **Claude Sonnet 4.5:** ~$0.07 (macro + micro + synthesis)
- **GPT-5 o1:** ~$0.50-0.75 (master editing)
- **Total:** ~$0.57-0.82 per psalm

### Full 150 Psalms

- **Claude only:** ~$10.50
- **Claude + GPT-5:** ~$85-$123
- **With Batch API (Claude 50% off):** ~$60-$85

---

## Quality Checklist

After generating each psalm, verify:

### Introduction Essay (800-1200 words)
- [ ] Cites concordance parallels with specific verses
- [ ] References traditional commentators (Rashi, Ibn Ezra, etc.)
- [ ] Integrates micro discoveries smoothly
- [ ] Scholarly but accessible tone
- [ ] ANE parallels when relevant
- [ ] No undefined jargon
- [ ] No factual errors

### Verse Commentary (150-400+ words/verse)
- [ ] Varies scholarly angles (poetics, textual criticism, figurative analysis, etc.)
- [ ] Complements (doesn't repeat) introduction
- [ ] Cites specific biblical parallels
- [ ] Engages interpretive debates
- [ ] Defines technical terms for lay readers
- [ ] Grounded in research materials

### Overall Quality
- [ ] Divine names modified correctly (יהוה → ה׳)
- [ ] Hebrew and English verse text integrated
- [ ] Coherent flow from introduction to verses
- [ ] No obvious LLM-ish breathlessness
- [ ] National Book Award-level writing

---

## Support

**Documentation:**
- [docs/PHASE_4_ENHANCEMENTS.md](PHASE_4_ENHANCEMENTS.md) - Full technical details
- [docs/NEXT_SESSION_PROMPT.md](NEXT_SESSION_PROMPT.md) - Previous session context
- [README.md](../README.md) - Project overview

**Issues:**
- Check logs in terminal output
- Review debug prompts in `output/debug/`
- Verify API keys in `.env`

---

**Ready to begin?**

```bash
python scripts/run_enhanced_pipeline.py 23
```

Expected output: `output/test_psalm_23/psalm_023_print_ready.md` (~6-8 minutes)

**Goal:** National Book Award-level commentary that would make Robert Alter proud! 🎯
