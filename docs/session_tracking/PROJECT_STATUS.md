# Psalms Project Status

**Last Updated**: 2025-12-11 (Session 213)

## Current Focus: Psalm Commentary Production

### Phase: Pipeline Production - Complete Psalms 1-14, 8, 15-21
Continuing with verse-by-verse commentary generation using the established pipeline.

## Gemini 2.5 Pro Fallback for Large Psalms (Session 211) - NEW FEATURE ✅

### Overview
For large psalms where the research bundle exceeds Claude's 200K token limit even after trimming, the pipeline now automatically switches to **Gemini 2.5 Pro** (1M token context) for synthesis generation. This preserves critical research content that would otherwise be removed.

### How It Works
1. Pipeline attempts progressive trimming (Related Psalms → Figurative Language)
2. If still over limit after trimming to 50%, flags for Gemini fallback
3. Synthesis uses Gemini 2.5 Pro with medium reasoning (8000 thinking budget)
4. GPT-5.1 Master Editor remains unchanged
5. Model used is tracked in stats and shown in DOCX summary

### New Trimming Priority (Session 211)
1. **Trim** Related Psalms (remove full psalm texts, keep word relationships)
2. **Remove** Related Psalms entirely
3. Trim Figurative Language to 75%
4. Trim Figurative Language to 50%
5. **Switch to Gemini 2.5 Pro** (if still over limit)

**Never trimmed**: Lexicon, Commentaries, Liturgical, Sacks, Scholarly Context, Concordance, Deep Web Research

---

## Main DOCX Verse-by-Verse Commentary Fix (Session 213) ✅

#### Problem Discovered:
The main commentary document (`psalm_NNN_commentary.docx`) was missing verse-by-verse commentary, even though the markdown file existed and the combined document worked correctly.

#### Root Cause:
The main document generator (`src/utils/document_generator.py`) was using an outdated regex pattern that only matched `**Verse X**` (single verse) format. However, the actual verse files use `**Verses X-Y**` (verse ranges) with en dashes (e.g., `**Verses 1–3**`).

#### Solution Implemented:
1. **Copied Working Regex**: Updated `_parse_verse_commentary()` in `document_generator.py` with the working pattern from `combined_document_generator.py`

2. **Enhanced Pattern Matching**: The new regex handles all formats:
   - Single verses: `**Verse 1**`
   - Verse ranges: `**Verses 1-3**` or `**Verses 21–25**` (hyphen and en dash)
   - Optional descriptions after verse ranges
   - Heading formats: `### Verse X`, `### Verses X-Y`

3. **Range Support**: Added proper handling for verse ranges with start/end tracking

#### Result:
- Main DOCX files now correctly include verse-by-verse commentary
- 39 verse headings successfully parsed and included in Psalm 18's main commentary document
- Both main and combined DOCX files now have complete verse-by-verse content

#### Files Modified:
- `src/utils/document_generator.py` - Updated `_parse_verse_commentary()` method with working regex

---

## Deep Web Research Integration (Session 209) ✅

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

### Session 213 (2025-12-11): Main DOCX Verse-by-Verse Commentary Fix

#### Problem Discovered:
The main commentary document (`psalm_NNN_commentary.docx`) was missing verse-by-verse commentary, even though the markdown file existed and the combined document worked correctly.

#### Root Cause:
The main document generator was using an outdated regex pattern that only matched `**Verse X**` format, but actual verse files use `**Verses X-Y**` format with en dashes.

#### Solution Implemented:
1. **Copied Working Regex**: Updated `_parse_verse_commentary()` in `document_generator.py` with the working pattern from `combined_document_generator.py`
2. **Enhanced Pattern Matching**: New regex handles single verses, ranges (hyphen and en dash), and optional descriptions
3. **Range Support**: Added proper handling for verse ranges with start/end tracking

#### Result:
- Main DOCX files now correctly include verse-by-verse commentary
- 39 verse headings successfully parsed and included in Psalm 18's main commentary document
- Both main and combined DOCX files now have complete verse-by-verse content

#### Files Modified:
- `src/utils/document_generator.py` - Updated `_parse_verse_commentary()` method

---

### Session 212 (2025-12-11): Psalm 18 Pipeline Fixes + Strategic Verse Grouping

#### Problems Fixed:

1. **JSON Truncation in MicroAnalyst**
   - Problem: 51-verse Psalm 18 caused JSON truncation error (max_tokens=8192 too low)
   - Fix: Increased to 16384 tokens in `src/agents/micro_analyst.py`

2. **Max Tokens Exceeding 64K Limit**
   - Problem: 51 verses × 1800 tokens = 91,800 exceeded Claude's 64K limit
   - Fix: Added cap at 64,000 tokens in `synthesis_writer.py:_calculate_verse_token_limit()`

3. **Missing Trimmed Research File**
   - Problem: `sections_removed` was overwritten on 2nd trimming call
   - Fix: Changed to accumulate sections instead of overwrite

4. **N/A in Bibliographical Summary**
   - Problem: Stats not extracted when using `--skip-micro`
   - Fix: Added `_parse_research_stats_from_markdown()` in pipeline script

5. **DOCX Markdown Heading Format**
   - Problem: `###` headings not converted to Word heading styles
   - Fix: Added markdown heading parsing to `_add_commentary_with_bullets()` in both document generators

6. **Combined DOCX Verse Range Merging**
   - Problem: Grouped verses (e.g., "Verses 21-25") not matched correctly
   - Fix: Added range-aware matching with `college_range_map` keyed by end verse

#### New Feature: Strategic Verse Grouping with Pacing

Instead of truncation at end of long psalms, models can now strategically group verses:

- **Synthesis Writer**: Updated `VERSE_COMMENTARY_PROMPT` with pacing guidance
- **Master Editor**: Updated `MASTER_EDITOR_PROMPT` with pacing guidance
- **College Editor**: Changed from "NEVER combine" to strategic grouping with pacing

**Pacing Rules**:
- Strategic grouping allowed for 2-4 thematically related verses
- Plan from the start - if grouping needed, do it throughout
- Equal treatment for later verses - no rushing at the end
- Never write "remaining verses not included" truncation notes

#### Files Modified:
- `src/agents/micro_analyst.py` - Increased max_tokens to 16384
- `src/agents/synthesis_writer.py` - 64K cap, sections accumulation, pacing prompt
- `src/agents/master_editor.py` - Pacing guidance in both editor prompts
- `src/utils/document_generator.py` - Markdown heading handling
- `src/utils/combined_document_generator.py` - Range-aware verse matching, heading handling
- `scripts/run_enhanced_pipeline.py` - Stats extraction for skip-micro case

---

### Session 211 (2025-12-11): Gemini 2.5 Pro Fallback + Improved Trimming Strategy

#### Problem Discovered:
Session 210's aggressive trimming (210K limit for verse commentary) removed critical content from large psalms like Psalm 18, including Liturgical Usage, Rabbi Sacks references, and Scholarly Context. This was over-trimming beyond what was necessary.

#### Solution Implemented:

1. **New Trimming Strategy** - Preserves critical content:
   - Step 1: Trim Related Psalms (remove full psalm texts, keep word relationships)
   - Step 2: Remove Related Psalms entirely
   - Step 3: Trim Figurative Language to 75%
   - Step 4: Trim Figurative Language to 50%
   - Step 5: **Switch to Gemini 2.5 Pro** (1M token context)

2. **Increased Character Limits**:
   - Introduction: 280K → **350K** characters
   - Verse Commentary: 210K → **300K** characters

3. **Gemini 2.5 Pro Fallback**:
   - Automatic switch when bundle still exceeds limit after step 4
   - Uses medium reasoning (`thinking_budget=8000`)
   - GPT-5.1 Master Editor unchanged
   - Cost tracking integrated for Gemini usage

4. **Enhanced Stats Tracking**:
   - `synthesis_model_used` property tracks actual model (Claude or Gemini)
   - `sections_removed` property lists what was trimmed
   - DOCX summary shows "Sections Trimmed for Context" and actual synthesis model

#### Key Benefit:
These sections are now **NEVER trimmed** - they're preserved for Gemini to process:
- Lexicon entries
- Traditional Commentaries
- Liturgical Usage
- Rabbi Sacks references
- Scholarly Context (RAG)
- Concordance results
- Deep Web Research

#### Files Modified:
- `src/agents/synthesis_writer.py` - New trimming strategy, Gemini fallback methods
- `src/utils/pipeline_summary.py` - Added `sections_trimmed` field
- `src/utils/document_generator.py` - Added sections trimmed to bibliographical summary
- `scripts/run_enhanced_pipeline.py` - Track actual synthesis model and sections trimmed

---

### Session 210 (2025-12-11): Token Limit Fix (Superseded by Session 211)

*Note: Session 210's aggressive trimming approach has been replaced by the Gemini fallback strategy in Session 211.*

---

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
- Gemini 2.5 Pro fallback handles large psalms (51+ verses) without losing critical content
- Strategic verse grouping with pacing guidance prevents truncation in long psalms
- Phrase substring matching working correctly
- Pipeline running without performance issues
- Critical sections (Liturgical, Sacks, RAG, Concordance) are never trimmed - preserved for Gemini
