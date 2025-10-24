# Quick Start (2 minutes)

**You are here**: Phase 4, 85% complete. Core pipeline fully operational.

## What is This?

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude AI (Sonnet 4.5) and GPT-5 o1.

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

4. MasterEditor (GPT-5 o1)
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

*Built with Claude Sonnet 4.5 and GPT-5 o1*
