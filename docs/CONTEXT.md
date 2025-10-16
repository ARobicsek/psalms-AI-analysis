# Psalms AI Commentary Project - Quick Context

## What is this?
An AI-powered pipeline generating scholarly verse-by-verse commentary for all 150 Psalms using Claude Sonnet 4.5 + Haiku 4.5. The system employs a multi-agent framework with telescopic analysis (macro → micro → synthesis) to produce deep insights that go beyond surface readings.

## Current Phase
See [PROJECT_STATUS.md](PROJECT_STATUS.md) for current task and progress.

## Key Documents
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)**: Where are we in the plan?
- **[IMPLEMENTATION_LOG.md](IMPLEMENTATION_LOG.md)**: What have we learned?
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Technical reference
- **[../planning_prompt.md](../planning_prompt.md)**: Original vision
- **Divine name modifications**: `C:\Users\ariro\OneDrive\Documents\Bible\docs\NON_SACRED_HEBREW.md`

## Key Resources
- **Existing figurative language DB**: `C:\Users\ariro\OneDrive\Documents\Bible\database\Pentateuch_Psalms_fig_language.db`
  - Contains 2,863 figurative language instances in Psalms
  - 2,527 verses analyzed
- **GitHub**: https://github.com/ARobicsek/psalms-AI-analysis
- **Sefaria API**: https://www.sefaria.org/api/ (no auth required)
- **BDB Lexicon via Sefaria**: https://www.sefaria.org/BDB

## Common Commands
```bash
# Activate virtual environment
cd /c/Users/ariro/OneDrive/Documents/Psalms
source venv/Scripts/activate  # Windows Git Bash

# Fetch a psalm
python src/data_sources/sefaria_client.py --psalm 23

# Search Hebrew concordance
python src/concordance/search.py --root שמר --scope Psalms

# Run full pipeline on one psalm
python main.py --psalm 23 --full-analysis

# Check current costs
python scripts/cost_report.py
```

## Agent Architecture

### Three-Pass Telescopic Analysis
1. **Pass 1: Macro Analysis** (Sonnet 4.5)
   - Reads entire chapter
   - Identifies emotional/narrative arc
   - Proposes thesis and structural outline
   - Output: Chapter Overview Document (~1,000 tokens)

2. **Scholar-Researcher** (Haiku 4.5)
   - Reviews macro overview
   - Generates specific research requests
   - Output: JSON requests for BDB, concordance, figurative language

3. **Librarians** (Python scripts - not LLMs!)
   - **BDB Librarian**: Fetches Hebrew lexicon entries via Sefaria
   - **Concordance Librarian**: Searches 4-layer Hebrew concordance
   - **Figurative Librarian**: Queries existing analysis database
   - Output: Assembled research bundle

4. **Pass 2: Micro Analysis** (Sonnet 4.5)
   - Receives research bundle + macro overview
   - Analyzes each verse with thesis in mind
   - Examines poetic devices, word choice, figurative language
   - Output: Verse-by-verse commentary (~3,000 tokens)

5. **Pass 3: Synthesis** (Sonnet 4.5)
   - Receives all prior work
   - Zooms back out to chapter level
   - Writes final essay showing forest AND trees
   - Output: Coherent essay (~1,200 tokens)

6. **Critic** (Haiku 4.5)
   - Reviews synthesis for telescopic integration
   - Checks for cliches, unsupported claims
   - Ensures macro-micro connection
   - Output: Structured feedback (~800 tokens)

7. **Revision** (Sonnet 4.5)
   - Addresses critic's feedback
   - Refines final output

## Hebrew Concordance: 4-Layer Search

Our concordance supports multiple search modes for flexibility:

1. **Consonantal Root Search** (most flexible)
   - Strips ALL diacritics (vowels + cantillation)
   - Example: שמר → finds שָׁמַר, שֹׁמֵר, שׁוֹמְרִים, etc.
   - Use: "Show all forms of guard/keep root"

2. **Vowel-Preserved Search** (semantic precision)
   - Strips cantillation only, preserves vowels
   - Example: אֵל → finds God, NOT preposition אֶל (to/toward)
   - Use: "Distinguish homographs by meaning"

3. **Exact Match Search** (morphological precision)
   - Preserves everything including cantillation
   - Use: "Find this specific verb form with accent"

4. **Lemma-Based Search** (linguistic)
   - Search by dictionary form
   - Use: "All instances regardless of inflection"

## Cost Estimates

### Per Chapter (average 16.8 verses)
- Sonnet 4.5 input: 36,850 tokens × $3/M = $0.11
- Sonnet 4.5 output: 6,200 tokens × $15/M = $0.09
- Haiku 4.5 input: 17,000 tokens × $1/M = $0.02
- Haiku 4.5 output: 1,300 tokens × $5/M = $0.007
- **Total: ~$0.23 per chapter**

### Entire Project
- 150 chapters × $0.23 = ~$35
- With prompt caching: ~$25-30
- Psalm 119 (176 verses): ~$2.50

## Quality Metrics

Commentary must demonstrate:
- ✅ **Telescopic thinking**: Connects micro details to macro thesis
- ✅ **Specific thesis**: Not generic ("this psalm is about trust")
- ✅ **Textual support**: Claims backed by evidence
- ✅ **Poetic awareness**: Analyzes parallelism, word choice, structure
- ✅ **Novelty**: Goes beyond surface/cliche readings
- ✅ **Coherence**: Shows how verses build chapter's argument

## Quick Start for New Session

### MANDATORY: Read These First (in order)
1. **docs/PROJECT_STATUS.md** - Current task and progress
2. **docs/IMPLEMENTATION_LOG.md** - Recent learnings (last 2-3 entries)
3. **docs/CONTEXT.md** - This file (project overview)

### Session Start Prompt
When starting a new conversation with an AI assistant, use this **exact prompt**:

```
I'm continuing work on the Psalms AI commentary pipeline.

Please read these files in order:
1. docs/CONTEXT.md (project overview)
2. docs/PROJECT_STATUS.md (current status)
3. docs/IMPLEMENTATION_LOG.md (scroll to most recent entry)

Based on PROJECT_STATUS.md, what is the next task I should work on?
```

### Session End Protocol (CRITICAL)
**ALWAYS do this before ending a session:**

1. **Update IMPLEMENTATION_LOG.md** with session summary:
   - Date, duration, tasks completed
   - Key learnings and decisions
   - Issues encountered and solutions
   - Next steps

2. **Update PROJECT_STATUS.md**:
   - Check completed tasks ✅
   - Update progress percentages
   - Update metrics (costs, psalms processed)
   - Update "Last session" field with today's date

3. **Git commit** with descriptive message:
   ```bash
   git add .
   git commit -m "Day X: [description]

   - [achievement 1]
   - [achievement 2]

   Next: [next task]"
   ```

**See [SESSION_MANAGEMENT.md](SESSION_MANAGEMENT.md) for complete protocol.**

## File Naming Conventions
- Python modules: `snake_case.py`
- Documentation: `SCREAMING_SNAKE_CASE.md`
- Data files: `lowercase_with_underscores.db`
- Scripts: `verb_noun.py` (e.g., `fetch_tanakh.py`)

## Development Workflow
1. Check PROJECT_STATUS.md for current task
2. Update IMPLEMENTATION_LOG.md with learnings as you go
3. Run tests after significant changes
4. Update PROJECT_STATUS.md when completing tasks
5. Commit frequently with descriptive messages

## Helpful Unicode Ranges
- Hebrew letters: U+05D0 to U+05EA
- Hebrew vowels (niqqud): U+05B0 to U+05BC
- Cantillation marks (te'amim): U+0591 to U+05C7
- Maqqef (hyphen): U+05BE
- Geresh: U+05F3 (׳)
- Gershayim: U+05F4 (״)

## Project Goals
1. Generate scholarly commentary for all 150 Psalms
2. Demonstrate telescopic analysis (both forest and trees)
3. Produce new insights using AI's embedded linguistic knowledge
4. Create professionally formatted study guides
5. Apply traditional Jewish divine name modifications
6. Keep total cost under $50
7. Complete in 8-9 weeks