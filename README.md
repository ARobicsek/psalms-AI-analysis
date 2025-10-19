# Psalms AI Commentary Pipeline

An AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms, employing a multi-agent framework with telescopic analysis to produce deep insights that go beyond surface readings.

## Project Overview

This project uses Claude AI (Sonnet 4.5 and Haiku 4.5) to generate comprehensive biblical commentary on the Book of Psalms. The system employs a three-pass telescopic analysis approach:

1. **Macro Analysis**: Identifies chapter-level structure, emotional arc, and central thesis
2. **Micro Analysis**: Detailed verse-by-verse examination with poetic and linguistic insights
3. **Synthesis**: Integration showing how individual details support the overall argument

## Key Features

- **Multi-agent architecture**: Specialized AI agents for different analysis tasks
- **Hebrew concordance**: 4-layer search system (consonantal, voweled, exact, lemma-based)
- **Free scholarly resources**: Integration with Sefaria API, BDB lexicon, existing figurative language database
- **Cost-optimized**: Strategic model selection (Sonnet vs Haiku) keeps total cost under $50 for all 150 Psalms
- **Quality control**: Critic agent ensures telescopic integration and depth
- **Traditional formatting**: Divine name modifications following Jewish scholarly conventions

## Quick Start

### Prerequisites
- Python 3.13+
- Anthropic API key (for Claude)
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/ARobicsek/psalms-AI-analysis.git
cd psalms-AI-analysis

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash
# or: venv\Scripts\activate  # Windows CMD

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Usage

```bash
# Process a single Psalm
python main.py --psalm 23

# Process a range
python main.py --psalms 1-10

# Check costs without processing
python main.py --psalm 119 --dry-run

# View cost report
python scripts/cost_report.py
```

## Project Structure

```
psalms-AI-analysis/
├── docs/                   # Project documentation
│   ├── CONTEXT.md         # Quick reference guide
│   ├── PROJECT_STATUS.md  # Current progress tracking
│   ├── IMPLEMENTATION_LOG.md  # Development journal
│   ├── ARCHITECTURE.md    # Technical specifications
│   └── SESSION_MANAGEMENT.md  # Workflow protocols
├── src/
│   ├── data_sources/      # API clients (Sefaria, etc.)
│   ├── agents/            # AI agent implementations
│   ├── concordance/       # Hebrew search system
│   └── output/            # Document generation
├── database/              # SQLite databases
├── tests/                 # Unit and integration tests
├── scripts/               # Utility scripts
└── requirements.txt       # Python dependencies
```

## Documentation

- **[CONTEXT.md](docs/CONTEXT.md)**: Quick project overview and command reference
- **[PROJECT_STATUS.md](docs/PROJECT_STATUS.md)**: Current phase, tasks, and metrics
- **[IMPLEMENTATION_LOG.md](docs/IMPLEMENTATION_LOG.md)**: Development history and learnings
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: Technical specifications and schemas
- **[SESSION_MANAGEMENT.md](docs/SESSION_MANAGEMENT.md)**: Workflow and maintenance protocols

## System Architecture

### Agent Pipeline (Current - Phase 4)

```
1. MacroAnalyst (Sonnet 4.5) → Structural thesis, genre, poetic devices
   ↓
2. MicroAnalyst v2 (Sonnet 4.5) → Verse-by-verse curiosity-driven research
   ├─→ Generates research questions per verse
   ├─→ Enhanced hierarchical figurative language search (vehicle + synonyms + broader terms)
   ├─→ Queries research bundle (lexicon, concordances, LXX, commentary)
   └─→ Produces verse discoveries + thematic threads
   ↓
3. ResearchBundle Assembly (Python)
   ├─→ BDB Lexicon entries (Sefaria API)
   ├─→ Hebrew Concordance (4-layer search: consonantal/voweled/exact/lemma)
   ├─→ Figurative Language analysis (local DB) - NOW: broader multi-book search
   └─→ Traditional Commentary excerpts (Rashi, Ibn Ezra, etc.)
   ↓
4. SynthesisWriter (Sonnet 4.5)
   ├─→ Introduction Essay (800-1200 words)
   │   └─→ Uses: MacroAnalysis + MicroAnalysis + ResearchBundle
   ↓
   └─→ Verse Commentary (150-400+ words/verse) - ENHANCED PROMPTS
       └─→ Uses: MacroAnalysis + MicroAnalysis + ResearchBundle + Introduction
       └─→ 11 categories of scholarly interest (poetics, textual criticism, etc.)
   ↓
5. MasterEditor (GPT-5 o1) → [NEW IN PHASE 4]
   ├─→ Critical editorial review (7 categories of issues)
   ├─→ Identifies: factual errors, missed insights, style problems
   ├─→ Revises introduction and verse commentary
   └─→ Elevates from "good" to "National Book Award" level
   ↓
6. Print-Ready Formatter (Python)
   ├─→ Integrates Hebrew/English verse text from database
   ├─→ Applies divine names modifications (יהוה → ה׳)
   └─→ Produces publication-ready markdown
```

**Phase 4 Enhancements** (2025-10-18):
1. **Master Editor Agent (GPT-5)** - Final editorial pass for excellence
2. **Enhanced Figurative Search** - Hierarchical 3-level search (vehicle + synonyms + broader terms), multi-book scope
3. **Expanded Synthesis Prompts** - 11 categories of scholarly interest, 150-400+ words per verse

See [docs/PHASE_4_ENHANCEMENTS.md](docs/PHASE_4_ENHANCEMENTS.md) for complete details.

### Hebrew Search: 4-Layer System

1. **Consonantal** (most flexible): Finds all forms of a root
2. **Voweled** (semantic precision): Distinguishes homographs
3. **Exact** (morphological precision): Specific verb forms
4. **Lemma-based** (linguistic): Dictionary form lookup

## Cost Estimates

- **Per chapter** (avg 16.8 verses): ~$0.23
- **Total project** (150 Psalms): ~$25-35 with prompt caching
- **Psalm 119** (176 verses): ~$2.50

## Quality Metrics

Commentary demonstrates:
- ✅ Telescopic thinking (macro-micro integration)
- ✅ Specific thesis (not generic observations)
- ✅ Textual support for claims
- ✅ Poetic awareness (parallelism, word choice, structure)
- ✅ Novel insights beyond surface readings
- ✅ Coherent argument showing how verses build meaning

## Development Status

**Current Phase**: Phase 1, Day 1 - Foundation Setup
**Progress**: 1% (Day 1 of ~45 days)

See [PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for detailed progress.

## Data Sources

- **Sefaria API**: Masoretic text, English translations, BDB lexicon (free, no auth)
- **Existing Figurative Language DB**: 2,863 pre-analyzed instances in Psalms
- **OpenScriptures**: Hebrew linguistic data
- **Archive.org**: Robert Alter's "Art of Biblical Poetry"

## License

This project is for scholarly and educational purposes.

## Acknowledgments

- Built on existing figurative language analysis from the Bible project
- Leverages Sefaria.org's freely accessible biblical texts and lexicons
- Inspired by Robert Alter's work on biblical poetry
- Uses Anthropic's Claude AI for scholarly analysis

## Contributing

This is a research project. See documentation for development workflow and coding standards.

## Contact

GitHub: https://github.com/ARobicsek/psalms-AI-analysis

---

*Generating deep insights into the Psalms through the power of contemporary AI technologies.*