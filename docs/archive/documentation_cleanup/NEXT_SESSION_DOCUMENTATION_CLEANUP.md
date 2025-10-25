# Next Session Prompt: Documentation Critical Fixes

**Date**: 2025-10-24
**Task**: Execute Phase 1 (Critical Fixes) from Documentation Consolidation Plan
**Duration**: 30 minutes
**Risk Level**: Low

---

## Context

A comprehensive documentation review was completed on 2025-10-24 using 4 parallel AI agents. The analysis found:

- **133 markdown files** with ~70% content redundancy
- **Conflicting pipeline descriptions** across multiple docs
- **Outdated README.md** (shows "Phase 1, Day 1 - 1%" when actually "Phase 4 - 85%")
- **8 phonetic documents** with 40-60% overlap
- **1,485-line NEXT_SESSION_PROMPT.md** (should be ~300 lines)

Three comprehensive planning documents were created:
1. [DOCUMENTATION_REVIEW_SUMMARY.md](docs/DOCUMENTATION_REVIEW_SUMMARY.md) - Executive summary
2. [DOCUMENTATION_CONSOLIDATION_PLAN.md](docs/DOCUMENTATION_CONSOLIDATION_PLAN.md) - Detailed plan
3. [DOCUMENTATION_AGENTS_WORKFLOW.md](docs/DOCUMENTATION_AGENTS_WORKFLOW.md) - Agentic workflow

---

## Your Mission: Phase 1 Critical Fixes

Execute the **30-minute critical fixes** that address the most visible documentation problems with minimal risk.

### Four Actions to Complete

#### Action 1: Fix README.md Development Status ⭐ CRITICAL

**Problem**: README.md shows incorrect development status

**Current content** (lines ~196-198):
```markdown
## Development Status

**Current Phase**: Phase 1, Day 1 - Foundation Setup
**Progress**: 1% (Day 1 of ~45 days)
```

**Required change**:
```markdown
## Development Status

**Current Phase**: Phase 4 - Commentary Enhancement & Experimentation
**Progress**: 85% (Sessions 1-21 complete, production-ready pipeline)
**Last Updated**: 2025-10-24

**Recent Accomplishments** (Sessions 18-21):
- Session 18: Stress-aware phonetic transcription system
- Session 19: Maqqef stress domain corrections
- Session 20: Stress marking pipeline integration
- Session 21: Master Editor prompt enhancements
```

**File**: [README.md](README.md)

---

#### Action 2: Add Warning to ARCHITECTURE.md ⚠️

**Problem**: ARCHITECTURE.md describes a 5-pass pipeline with Critic + Revision agents that were never implemented

**Add to top of file** (after title, line ~3):
```markdown
---

## ⚠️ DEPRECATION NOTICE

**This document describes the original Phase 3 design specification.**

**For current Phase 4 implementation, see**: [TECHNICAL_ARCHITECTURE_SUMMARY.md](TECHNICAL_ARCHITECTURE_SUMMARY.md)

**Key differences from current implementation**:
- ❌ **Critic Agent (Pass 4)** described in this doc was never implemented
- ❌ **Final Polisher (Pass 5)** described in this doc was never implemented
- ✅ **Actual Pass 4** uses MasterEditor (GPT-5) instead
- ✅ **Current pipeline**: Macro → Micro → Synthesis → MasterEditor (4 passes, not 5)

This document is preserved for historical reference and design context.

---
```

**File**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

#### Action 3: Create QUICK_START.md 🆕

**Purpose**: Create a 1-page entry point for new developers

**Create new file**: `QUICK_START.md` in project root

**Content**:
```markdown
# Quick Start (2 minutes)

**You are here**: Phase 4, 85% complete. Core pipeline fully operational.

## What is This?

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude AI (Sonnet 4.5) and GPT-5.

## Installation

```bash
# Clone and setup
git clone https://github.com/ARobicsek/psalms-AI-analysis.git
cd psalms-AI-analysis
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash
pip install -r requirements.txt

# Add API key to .env
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

## Run Your First Psalm

```bash
python scripts/run_enhanced_pipeline.py 23  # Process Psalm 23
```

Output will be in `output/psalm_23/psalm_023_print_ready.md`

## 4-Pass Pipeline Overview

```
1. MacroAnalyst (Sonnet 4.5)
   └─→ Structural analysis, genre, emotional arc

2. MicroAnalyst (Sonnet 4.5)
   └─→ Verse-by-verse research with Hebrew concordance

3. SynthesisWriter (Sonnet 4.5)
   └─→ Commentary generation (intro + verse commentary)

4. MasterEditor (GPT-5)
   └─→ Critical editorial review and enhancement
```

## Key Features

- **Hebrew Concordance**: 4-layer search (consonantal, voweled, exact, lemma)
- **Phonetic Transcription**: Accurate pronunciation with stress marking
- **Figurative Language**: Database of 2,863 analyzed instances
- **Quality**: National Book Award-level scholarly commentary
- **Cost**: ~$0.60 per psalm (Claude + GPT-5)

## Common Commands

```bash
# Process multiple psalms
python scripts/run_enhanced_pipeline.py 1-10

# Check costs without processing
python scripts/run_enhanced_pipeline.py 119 --dry-run

# View cost report
python scripts/cost_report.py
```

## Documentation Map

**Getting Started**:
- This file (QUICK_START.md) - You are here
- [CONTEXT.md](docs/CONTEXT.md) - Project overview (5 min read)

**Technical Reference**:
- [TECHNICAL_ARCHITECTURE_SUMMARY.md](docs/TECHNICAL_ARCHITECTURE_SUMMARY.md) - System architecture
- [PHONETIC_ENHANCEMENT_SUMMARY.md](docs/PHONETIC_ENHANCEMENT_SUMMARY.md) - Phonetic system
- [STRESS_MARKING_ENHANCEMENT.md](docs/STRESS_MARKING_ENHANCEMENT.md) - Stress marking

**Development**:
- [SESSION_MANAGEMENT.md](docs/SESSION_MANAGEMENT.md) - Workflow protocols
- [IMPLEMENTATION_LOG.md](docs/IMPLEMENTATION_LOG.md) - Development history (Sessions 1-21)
- [PROJECT_STATUS.md](docs/PROJECT_STATUS.md) - Current progress tracking

## Example Output

Commentary includes:
- **Introduction essay** (800-1200 words) - Psalm's structure, thesis, poetic devices
- **Verse-by-verse commentary** (300-500 words per verse) - Detailed scholarly analysis
- **Hebrew insights** - Phonetic transcription, word studies, concordance patterns
- **Intertextual connections** - Figurative language parallels across biblical corpus

## For Contributors

See [SESSION_MANAGEMENT.md](docs/SESSION_MANAGEMENT.md) for development workflow and coding standards.

---

**Questions?** See [CONTEXT.md](docs/CONTEXT.md) for comprehensive project overview.

*Built with Claude Sonnet 4.5 and GPT-5*
```

**File**: Create `QUICK_START.md` in root directory

---

#### Action 4: Update CONTEXT.md Phase References 📝

**Problem**: CONTEXT.md references "Phase 3 - CURRENT" when actually Phase 4

**Find and replace**:
- Search for: "Phase 3"
- Replace with: "Phase 4"
- Verify there are no incorrect phase references remaining

**Specific areas to check**:
1. Top section that says "Phase 3 - CURRENT"
2. Any cost estimates mentioning Phase 3
3. Pipeline descriptions referencing Phase 3

**File**: [docs/CONTEXT.md](docs/CONTEXT.md)

---

## Implementation Approach

### Use the Edit Tool

For each action:

1. **Read the file first** to verify current content
2. **Use Edit tool** to make precise changes
3. **Verify the change** worked correctly

### Example for Action 1:

```
1. Read README.md to find current Development Status section
2. Edit README.md - replace old status with new status
3. Read the updated section to verify
```

---

## Validation Checklist

After completing all four actions, verify:

- [ ] README.md shows "Phase 4 - 85%" (not "Phase 1, Day 1")
- [ ] README.md includes Sessions 18-21 accomplishments
- [ ] ARCHITECTURE.md has deprecation warning at top
- [ ] QUICK_START.md exists in root directory
- [ ] QUICK_START.md is properly formatted and readable
- [ ] CONTEXT.md references "Phase 4" (not "Phase 3")
- [ ] All edits use correct line numbers and exact strings

---

## Expected Duration

- **Action 1** (README.md): 5 minutes
- **Action 2** (ARCHITECTURE.md warning): 5 minutes
- **Action 3** (Create QUICK_START.md): 10 minutes
- **Action 4** (Update CONTEXT.md): 10 minutes

**Total**: ~30 minutes

---

## Success Criteria

When complete:

✅ README.md accurately reflects Phase 4, 85% progress
✅ ARCHITECTURE.md clearly warns about obsolete content
✅ New developers have clear 1-page entry point (QUICK_START.md)
✅ CONTEXT.md consistently references Phase 4
✅ No conflicting phase information in core docs

---

## What Comes Next

After completing these critical fixes, the user can decide whether to:

**Option A**: Stop here (quick wins achieved)
**Option B**: Continue with Phase 2 - Consolidation (2 hours)
- Consolidate 8 phonetic docs → 4 docs
- Reduce NEXT_SESSION_PROMPT.md (1485 → 300 lines)
- Archive 20+ session summary files

**Option C**: Full documentation cleanup (4-6 hours total)
- Complete all phases from DOCUMENTATION_CONSOLIDATION_PLAN.md

---

## Reference Documents

If you need more context:

- **[DOCUMENTATION_REVIEW_SUMMARY.md](docs/DOCUMENTATION_REVIEW_SUMMARY.md)** - Why these fixes matter
- **[DOCUMENTATION_CONSOLIDATION_PLAN.md](docs/DOCUMENTATION_CONSOLIDATION_PLAN.md)** - Complete plan (this is Phase 1)
- **[DOCUMENTATION_CLEANUP_QUICKSTART.md](DOCUMENTATION_CLEANUP_QUICKSTART.md)** - 2-minute overview

---

## Important Notes

### Git Safety

Before starting, create backup:
```bash
git add .
git commit -m "Pre-documentation-cleanup backup (Phase 1)"
git branch documentation-cleanup-backup
```

### Risk Assessment

**Low Risk** - These changes:
- Fix factual errors (wrong phase/status)
- Add helpful warnings
- Create new documentation
- Don't delete or move existing files

### If Something Goes Wrong

All changes can be reverted:
```bash
git checkout HEAD -- README.md  # Revert specific file
# or
git reset --hard HEAD  # Revert all changes
```

---

## Ready to Start!

You have all the information needed to complete Phase 1 (Critical Fixes).

**Just begin with Action 1** and work through Actions 1-4 sequentially.

Good luck! 🚀
