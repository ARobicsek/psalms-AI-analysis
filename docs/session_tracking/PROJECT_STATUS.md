# Psalms Project Status

**Last Updated**: 2025-12-11 (Session 210)

## Current Focus: Psalm Commentary Production

### Phase: Pipeline Production - Complete Psalms 1-14, 8, 15-21
Continuing with verse-by-verse commentary generation using the established pipeline.

## Deep Web Research Integration (Session 209) - NEW FEATURE ✅

### Overview
Added support for incorporating Gemini Deep Research outputs into the research bundle. This allows manually-gathered scholarly research from web sources to enrich the AI-generated commentary.

### How to Use

1. **Run Gemini Deep Research** (manually in browser):
   - Go to [Gemini](https://gemini.google.com/) or [NotebookLM](https://notebooklm.google.com/)
   - Select "Deep Research" mode
   - Use this prompt template:
   ```
I'm preparing a scholarly essay on Psalm [] for a collection of essays that serve as a reader's guide to the book of psalms. Please assemble a deep research package on this psalm that includes ancient, medieval and modern commentary and debates; ANE scholarship; linguistics, philology, poetics, etc. Also include reception, ritual and liturgical use of the psalm or any of its verses or phrases. Also include literary and cultural influence that the psalm or its language has had. Make sure to search widely, but include thetorah.org and Sefaria as well as academic sources. When you return your results please be clear and terse, to minimize tokens. You're not writing the ultimate essay; your essay is meant to assemble key materials for the scholar.
   ```

2. **Save the output**:
   - Location: `data/deep_research/`
   - Naming: `psalm_NNN_deep_research.txt` (e.g., `psalm_017_deep_research.txt`)
   - Format: Plain text (copy/paste from Gemini output)

3. **Run the pipeline normally**:
   ```bash
   python main.py --psalm 17
   ```
   The pipeline will automatically:
   - Find and load the deep research file
   - Include it in the research bundle as "## Deep Web Research"
   - Trim other sections first if bundle exceeds character limits
   - Track status in pipeline stats and final documents

### Implementation Details

**Files Modified**:
- `src/agents/research_assembler.py` - Loads deep research, adds to ResearchBundle
- `src/agents/synthesis_writer.py` - Progressive trimming with correct priority
- `src/utils/pipeline_summary.py` - Tracks deep research metrics
- `src/utils/document_generator.py` - Shows "Deep Web Research: Yes/No" in summary
- `src/utils/combined_document_generator.py` - Same for combined docs
- `scripts/run_enhanced_pipeline.py` - Updates tracker after synthesis

**New Fields in ResearchBundle**:
- `deep_research_content: Optional[str]` - Raw content from file
- `deep_research_included: bool` - Whether included in final bundle
- `deep_research_removed_for_space: bool` - Whether removed due to limits

**Trimming Priority** (first to last - least to most important):
1. Related Psalms section (removed first)
2. Figurative Language (progressive trim: 75% → 50% → 25% → remove)
3. Concordance results (progressive trim: 75% → 50% → 25% → remove)
4. Deep Web Research (removed only if still over limit)
5. Emergency: Sacks, Liturgical, RAG sections
6. Last resort: Hard truncation

**Never trimmed**: Lexicon entries, Traditional Commentaries

**Document Summary Output**:
- "Deep Web Research: Yes" - included successfully
- "Deep Web Research: No (removed for space)" - removed due to character limits
- "Deep Web Research: No" - no file found

---

## Pipeline Phases

### Phase 1: Text Extraction (COMPLETE ✅)
- [x] Extract all Tanakh text from Sefaria
- [x] Parse into structured verses with Hebrew and English
- [x] Store in SQLite database with full-text search

### Phase 2: Macro Analysis (COMPLETE ✅)
- [x] Claude Opus analyzes psalms
- [x] Identifies key themes, structure, divine encounters
- [x] Generates CSV reports
- [x] Manual review and refinement complete

### Phase 3: Micro Analysis (COMPLETE ✅)
- [x] Sonnet 4.5 analyzes each verse individually
- [x] Extracts key words and phrases
- [x] Generates research requests
- [x] Phrase extraction with exact form preservation

### Phase 4: Research Assembly (IN PROGRESS 🟠)
- [x] Lexicon queries (BDB dictionary)
- [x] Concordance searches
- [x] Figurative language searches
- [x] Traditional commentaries
- [x] Deep Web Research integration (NEW)
- [x] Performance optimization for phrase searches

### Phase 5: Synthesis Generation (COMPLETE ✅)
- [x] Opus synthesizes research findings
- [x] Generates introduction
- [x] Generates verse-by-verse commentary
- [x] Uses biblical hermeneutic method

### Phase 6: Editing and Publication (COMPLETE ✅)
- [x] College Editor refines content
- [x] Master Editor final polish
- [x] Print-ready formatting
- [x] Word document generation

---

## Recent Accomplishments

### Session 209 (2025-12-11): Deep Web Research Integration + Progressive Trimming Fix

#### Completed:
1. **Implemented Deep Web Research Feature**:
   - Created `data/deep_research/` directory for Gemini Deep Research outputs
   - File naming convention: `psalm_NNN_deep_research.txt`
   - Auto-loads into research bundle when present

2. **Updated Research Assembler**:
   - Added `_load_deep_research()` method to find and load files
   - Added deep research fields to `ResearchBundle` dataclass
   - Included in `to_markdown()` as "## Deep Web Research" section

3. **Rewrote Research Bundle Trimming** (fixed Psalm 18 token overflow):
   - Problem: Psalm 18 (51 verses) exceeded 200K token limit (211,252 tokens)
   - Solution: Progressive trimming with correct priority order
   - Trimming order: Related Psalms → Figurative → Concordance → Deep Research
   - Progressive reduction: 75% → 50% → 25% → remove for each section
   - Emergency fallback: Sacks, Liturgical, RAG sections
   - Last resort: Hard truncation

4. **Updated Document Generators**:
   - Both `document_generator.py` and `combined_document_generator.py` updated
   - "Deep Web Research: Yes/No" now appears in Methodological Summary
   - Shows appropriate status based on availability and inclusion

5. **Updated Pipeline Tracking**:
   - `ResearchStats` now includes deep research metrics
   - JSON output includes all deep research status fields
   - Pipeline logs when deep research is removed for space

---

## Session 210 (2025-12-11): Token Limit Fix & Research Bundle Optimization

#### Problem Discovered:
Psalm 18 pipeline failed with "prompt is too long: 205995 tokens > 200000 maximum" error during introduction generation. The research bundle was 361,606 characters (~206K tokens), exceeding the limit before adding prompt template and analyses.

#### Completed:

1. **Fixed Character Limits for Token Budget**:
   - Introduction: Reduced from 400K → 280K characters (~160K tokens)
   - Verse commentary: Reduced from 350K → 210K characters (~120K tokens)
   - These limits ensure we stay within 200K token total with buffer for other content

2. **Added Trimming Summary to Research Bundles**:
   - Every trimmed bundle now includes a "## Research Bundle Processing Summary" section
   - Shows original size, final size, percentage removed
   - Lists which sections were removed/trimmed
   - Example for Psalm 18: 361,606 → 159,502 characters (56% removed)

3. **Fixed Early Returns in Trimming Logic**:
   - Removed all early returns to ensure summary is always added
   - Fixed Unicode arrows (→) causing encoding errors on Windows
   - Ensured trimming summary appears at end of every trimmed bundle

4. **Fixed Pipeline Script for Skipping Steps**:
   - Fixed API key requirement when using --skip-macro and --skip-micro
   - Now uses default model names for tracking when skipping steps
   - Allows testing without requiring API keys

#### Technical Details:

**Token Budget Calculation (200K limit)**:
- Introduction: 160K tokens (research) + 40K tokens (template + macro + micro)
- Verse commentary: 120K tokens (research) + 80K tokens (intro + template + macro + micro + phonetic)

**Character-to-Token Ratio**: 1.75 chars/token (based on actual error metrics)

**Trimming Priority Order**:
1. Related Psalms (removed first)
2. Figurative Language (trimmed progressively: 75% → 50% → 25% → remove)
3. Concordance (trimmed progressively: 75% → 50% → 25% → remove)
4. Deep Web Research (removed entirely)
5. Emergency: Rabbi Sacks, Liturgical Usage, Scholarly Context
6. Last resort: Hard truncation

#### Files Modified:
- `src/agents/synthesis_writer.py`: Fixed character limits, trimming logic, Unicode issues
- `scripts/run_enhanced_pipeline.py`: Fixed API key requirement for skipped steps

#### Test Results:
- Psalm 18 with 210K limit: Successfully trimmed to 159,502 characters
- All required content preserved while staying within token limits
- Trimming summary properly added to bundle

---

### Session 204-208 (2025-12-10): Thematic Parallels Feature - DISCONTINUED

#### Summary:
Implemented and evaluated a RAG-based thematic search system for finding biblical parallels to Psalms. After comprehensive testing, the feature was discontinued as it did not provide useful texts for the synthesis writer and master editor.

**Key Findings**:
- Built Hebrew-only corpus with 23,089 chunks using 5-verse overlapping windows
- Created vector embeddings using OpenAI text-embedding-3-large
- 1-verse chunks provided superior precision with exact verse matching
- 80% cost reduction ($0.0786 vs $0.38 for 5-verse chunks)
- Feature artifacts preserved in `docs/archive/discontinued_features/`

---

### Session 182 (2025-12-08): Lexical Insight Prompt Fix

#### Problem:
Concordance searches for "פקד לילה" and "צל כנפים" in Psalm 17 returned 0 results.

#### Root Cause:
LLM extracted conceptual/base forms instead of exact verse forms.

#### Solution:
Modified `DISCOVERY_PASS_PROMPT` in `src/agents/micro_analyst.py` with concrete wrong/right examples for exact form extraction.

---

### Session 181 (2025-12-08): Comprehensive Codebase Cleanup

- Archived 326 files into organized subdirectories
- Created CLAUDE.md for token-efficient session startup
- Root directory reduced from 145+ files → 30 files (79% reduction)

---

## Pipeline Status by Psalm

### Completed (All Phases):
- Psalms 1-14
- Psalm 15
- Psalm 20
- Psalm 8
- Psalm 97
- Psalm 145

### Next Up:
- Psalms 16-21
- Remaining psalms 22-150

---

## Database Status
- Location: `database/tanakh.db`
- Size: ~50MB
- Books: All 39 books of Tanakh
- Verses: 23,145 verses
- Indexed for fast full-text search

---

## Notes
- Deep Web Research feature ready for production use
- Progressive trimming handles large psalms (51+ verses) within token limits
- Phrase substring matching working correctly
- Pipeline running without performance issues
