# Psalms Project Status

**Last Updated**: 2025-12-11 (Session 209)

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
   I'm preparing a scholarly essay on Psalm [NUMBER] for a collection of essays
   that serve as a reader's guide to the book of psalms. Please assemble a deep
   research package on this psalm that includes ancient, medieval and modern
   commentary and debates; ANE scholarship; linguistics, philology, etc. Also
   include reception, ritual and liturgical use of the psalm or any of its verses
   or phrases. Also include literary and cultural influence that the psalm or its
   language has had. Make sure to search widely, but include thetorah.org and
   Sefaria as well as academic sources. When you return your results please be
   clear and terse, to minimize tokens. You're not writing the essay; you're
   assembling the materials for the scholar.
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
   - Remove it if the bundle exceeds character limits (600K chars)
   - Track status in pipeline stats and final documents

### Implementation Details

**Files Modified**:
- `src/agents/research_assembler.py` - Loads deep research, adds to ResearchBundle
- `src/agents/synthesis_writer.py` - Trims deep research first if bundle too large
- `src/utils/pipeline_summary.py` - Tracks deep research metrics
- `src/utils/document_generator.py` - Shows "Deep Web Research: Yes/No" in summary
- `src/utils/combined_document_generator.py` - Same for combined docs
- `scripts/run_enhanced_pipeline.py` - Updates tracker after synthesis

**New Fields in ResearchBundle**:
- `deep_research_content: Optional[str]` - Raw content from file
- `deep_research_included: bool` - Whether included in final bundle
- `deep_research_removed_for_space: bool` - Whether removed due to limits

**Trimming Priority** (least to most important):
1. Deep Web Research (removed first)
2. Concordance results
3. Figurative language examples
4. Commentary entries
5. Lexicon entries (never trimmed)

**Document Summary Output**:
- "Deep Web Research: Yes" - included successfully
- "Deep Web Research: No (removed for space)" - removed due to character limits
- "Deep Web Research: No" - no file found

---

## Thematic Parallels Feature (Sessions 183-208) - DISCONTINUED

### Summary (2025-12-09 to 2025-12-10):
Implemented and evaluated a RAG-based thematic search system for finding biblical parallels to Psalms.

**Main Implementation (Sessions 183-203)**:
- Built Hebrew-only corpus with 23,089 chunks using 5-verse overlapping windows
- Created vector embeddings using OpenAI text-embedding-3-large
- Implemented ThematicParallelsLibrarian for semantic search
- Integrated into ResearchAssembler pipeline
- Tested on multiple Psalms (23, 8, 121, 145)

**1-Verse Chunk Experimentation (Sessions 204-208)**:
After discontinuing the main feature, experimented with 1-verse chunks as an alternative approach:

- **Session 204**: Built complete 1-verse chunking system with 23,206 individual verses
- **Session 205**: Fixed similarity scores from ~0.79 to ~0.997 by using Hebrew-only embeddings
- **Session 206**: Created single verse search script with database integration
- **Session 207**: Enhanced script with interactive mode and top 10 matches; fixed parsing bugs
- **Session 208**: Final fixes made script fully functional for thematic verse search

**Key Findings from 1-Verse Experiment**:
- 1-verse chunks provide superior precision with exact verse matching
- 80% cost reduction ($0.0786 vs $0.38 for 5-verse chunks)
- High similarity scores (0.77-0.84) for self-matches
- Script available as `single_verse_search.py` for future use

**Final Decision**: Feature discontinued - artifacts preserved in `docs/archive/discontinued_features/`
- 1-verse approach proved technically viable but not needed for current pipeline
- All evaluation scripts retained for potential future scholarly applications

### Next Phase
Continue with production commentary pipeline

**Root Cause**:
- LLM extracts **conceptual phrases** (base/dictionary forms) instead of **exact forms**
- Verse has "פקדת לילה" (conjugated) but LLM extracted "פקד לילה" (infinitive)
- Verse has "בצל כנפיך" (with prefix/suffix) but LLM extracted "צל כנפים" (base plural)
- Downstream matching can't recover from morphological mismatch (כנפים ≠ כנפיך)

**Solution Implemented (Session 182)**:
- Improved `DISCOVERY_PASS_PROMPT` in micro_analyst.py (lines 98-107)
- Added concrete wrong/right examples for exact form extraction
- Added phrase-level morphological variation guidance (person, number, tense, prefix)

### Status: ✅ FIXED - Testing on Psalm 17

## Phase 1: Text Extraction (COMPLETE ✅)
- [x] Extract all Tanakh text from Sefaria
- [x] Parse into structured verses with Hebrew and English
- [x] Store in SQLite database with full-text search

## Phase 2: Macro Analysis (COMPLETE ✅)
- [x) Claude Opus analyzes psalms
- [x] Identifies key themes, structure, divine encounters
- [x] Generates CSV reports
- [x] Manual review and refinement complete

## Phase 3: Micro Analysis (COMPLETE ✅)
- [x] Sonnet 4.5 analyzes each verse individually
- [x] Extracts key words and phrases
- [x] Generates research requests
- [x] **NEW**: Phrase extraction with exact form preservation

## Phase 4: Research Assembly (IN PROGRESS 🟠)
- [x] Lexicon queries (BDB dictionary)
- [x] Concordance searches
- [x] Figurative language searches
- [x] Traditional commentaries
- [x] **NEW**: Performance optimization for phrase searches

## Phase 5: Synthesis Generation (COMPLETE ✅)
- [x] Opus synthesizes research findings
- [x] Generates introduction
- [x] Generates verse-by-verse commentary
- [x] Uses biblical hermeneutic method

## Phase 6: Editing and Publication (COMPLETE ✅)
- [x] College Editor refines content
- [x] Master Editor final polish
- [x] Print-ready formatting
- [x] Word document generation

## Recent Accomplishments

### Session 209 (2025-12-11): Deep Web Research Integration

#### Completed:
1. **Implemented Deep Web Research Feature**:
   - Created `data/deep_research/` directory for Gemini Deep Research outputs
   - File naming convention: `psalm_NNN_deep_research.txt`
   - Auto-loads into research bundle when present

2. **Updated Research Assembler**:
   - Added `_load_deep_research()` method to find and load files
   - Added deep research fields to `ResearchBundle` dataclass
   - Included in `to_markdown()` as "## Deep Web Research" section

3. **Implemented Smart Trimming**:
   - Deep research removed first if bundle exceeds 600K character limit
   - Added `deep_research_removed_for_space` property to synthesis writer
   - Pipeline tracks removal status for reporting

4. **Updated Document Generators**:
   - Both `document_generator.py` and `combined_document_generator.py` updated
   - "Deep Web Research: Yes/No" now appears in Methodological Summary
   - Shows appropriate status based on availability and inclusion

5. **Updated Pipeline Tracking**:
   - `ResearchStats` now includes deep research metrics
   - JSON output includes all deep research status fields
   - Pipeline logs when deep research is removed for space

---

### Session 204 (2025-12-10): Thematic Parallels Feature Closure

#### Completed:
1. **Evaluated and Discontinued Thematic Parallels Feature**:
   - RAG-based semantic search did not provide useful texts for synthesis writer and master editor
   - Parallels were too generic and did not enhance scholarly commentary
   - Decision made after comprehensive testing (Sessions 183-203)

2. **Code Cleanup**:
   - Removed all thematic_parallels code from research_assembler.py
   - Deleted src/thematic/ directory and all thematic test scripts
   - Archived documentation to docs/archive/discontinued_features/
   - Preserved evaluation artifacts: generate_all_requested_reports.py and psalm_reports_summary.md

3. **Updated Documentation**:
   - Marked feature as discontinued with closure summary
   - Updated PROJECT_STATUS.md with thematic parallels sessions summary
   - Total cost incurred: $0.45 for evaluation

---

### Session 182 (2025-12-08): Lexical Insight Prompt Fix

#### Problem:
Concordance searches for "פקד לילה" and "צל כנפים" in Psalm 17 returned 0 results.

#### Root Cause:
LLM extracted conceptual/base forms instead of exact verse forms:
- "צל כנפים" instead of "בצל כנפיך" (missing prefix, wrong suffix)
- "פקד לילה" instead of "פקדת לילה" (unconjugated verb)

#### Solution:
Modified `DISCOVERY_PASS_PROMPT` in `src/agents/micro_analyst.py` (lines 98-107):
- Added concrete wrong/right example showing exact extraction requirement
- Added phrase-level morphological variation guidance:
  - Person: "בצל כנפי" (my), "בצל כנפיך" (your), "בצל כנפיו" (his)
  - Number: "בצל כנף" (singular), "בצל כנפים" (plural)
  - With/without prefix: "צל כנפיך" (without ב)
  - Verb tenses: "פקדת לילה" (perfect), "תפקד לילה" (imperfect)

---

### Session 179 (2025-12-07): Figurative Vehicle Search Fix Implementation

#### Completed:
1. **Fixed Vehicle Search - Removed Morphological Variants**:
   - Modified `src/agents/figurative_librarian.py` (lines 475-530)
   - Removed `_get_morphological_variants()` calls for both vehicle_search_terms and vehicle_contains
   - Vehicle concepts now treated as hierarchical tags, not inflected words
   - Only exact term and simple plural are searched (e.g., "tent", "tents")
   - Eliminates false positives from bad variants (e.g., "living" from "live")

2. **Added Exact Match Prioritization**:
   - Modified `src/agents/research_assembler.py` (lines 540-565)
   - Added conditional prioritization logic to `_filter_figurative_bundle()`
   - Only activates when vehicle_contains is set AND results exceed max_results
   - Prioritizes instances where vehicle field exactly matches search term
   - Ensures "tent" exact matches appear before "shepherd's tent" or "tents"

3. **Expected Improvements**:
   - Accuracy: No more "living beings" when searching for "tent"
   - Precision: Only relevant vehicle matches returned
   - Prioritization: Best matches first when results exceed limit

### Session 178 (2025-12-07): Figurative Language Search Bug Investigation

#### Completed:
1. **Discovered False Positive Issue**: "Vehicle contains: tent" returning unrelated results
2. **Root Cause Analysis**:
   - Micro analyst's bad variant "live" → librarian's "living" variant
   - Matched "living" in ["...living creatures"] and ["...living beings"]
3. **Database Verification**: Confirmed 20 legitimate tent entries exist
4. **Solution Design**: Remove morphological variants for vehicle searches
5. **Implementation Plan Created**: `C:\Users\ariro\.claude\plans\deep-sparking-hartmanis.md`

### Session 176 (2025-12-07): Phrase Substring Matching Fix

#### Completed:
1. **Identified Root Cause**: Phrase searches using exact word matching
   - "דבר אמת בלב" couldn't match "וְדֹבֵ֥ר אֱ֝מֶ֗ת בִּלְבָבֽוֹ׃"
   - Exact matching prevented matches with prefixes/suffixes
   - Psalm 15:2 not found for its own phrase

2. **Implemented Phrase Substring Matching**:
   - Modified `src/concordance/search.py` - `_verse_contains_phrase` method
   - **Key Change**: Phrases use substring matching, single words use exact matching
   - Allows "דבר" to match in "ודובר" and "בלב" to match in "בלבבו"
   - Words must appear in order within the verse

3. **Enhanced Exact Phrase Preservation**:
   - Modified `src/agents/micro_analyst.py` - `_override_llm_base_forms` method
   - Match queries with stored phrases using substring matching
   - Add both exact phrase AND variations to search list
   - Ensures original verse phrases are always searched

4. **Fixed Supporting Infrastructure**:
   - Added missing `get_available_books` method to FigurativeLibrarian
   - Added graceful handling for missing figurative_language table
   - Created test scripts to verify the fix

### Session 177 (2025-12-07): Figurative Language Search Bug Investigation

#### Completed:
1. **Discovered False Positive Issue**: "Vehicle contains: tent" returning unrelated results
2. **Root Cause Analysis**:
   - Micro analyst's bad variant "live" → librarian's "living" variant
   - Matched "living" in ["...living creatures"] and ["...living beings"]
3. **Database Verification**: Confirmed 20 legitimate tent entries exist
4. **Solution Design**: Remove morphological variants for vehicle searches
5. **Implementation Plan Created**: `C:\Users\ariro\.claude\plans\deep-sparking-hartmanis.md`

### Session 176 (2025-12-07): Phrase Substring Matching Fix

#### Completed:
1. **Identified Root Cause**: Phrase searches using exact word matching
   - "דבר אמת בלב" couldn't match "וְדֹבֵ֥ר אֱ֝מֶ֗ת בִּלְבָבֽוֹ׃"
   - Exact matching prevented matches with prefixes/suffixes
   - Psalm 15:2 not found for its own phrase

2. **Implemented Phrase Substring Matching**:
   - Modified `src/concordance/search.py` - `_verse_contains_phrase` method
   - **Key Change**: Phrases use substring matching, single words use exact matching
   - Allows "דבר" to match in "ודובר" and "בלב" to match in "בלבבו"
   - Words must appear in order within the verse

3. **Enhanced Exact Phrase Preservation**:
   - Modified `src/agents/micro_analyst.py` - `_override_llm_base_forms` method
   - Match queries with stored phrases using substring matching
   - Add both exact phrase AND variations to search list
   - Ensures original verse phrases are always searched

4. **Fixed Supporting Infrastructure**:
   - Added missing `get_available_books` method to FigurativeLibrarian
   - Added graceful handling for missing figurative_language table
   - Created test scripts to verify the fix

### Session 175 (2025-12-07): Performance Fix Implementation

#### Completed:
1. **Identified Root Cause**: Phrase preservation fix causing exponential query growth
2. **Implemented Performance Fix**: No variations for phrases, only exact forms
3. **Enhanced Phrase Extraction**: Added fallback extraction from verse text
4. **Added Comprehensive Debug Logging**: Track performance and query counts

## Pipeline Status by Psalm

### Completed (All Phases):
- Psalms 1-14
- Psalm 20
- Psalm 8
- Psalm 97
- Psalm 145

### Completed (All Phases):
- Psalms 1-14
- Psalm 15: **Pipeline complete, revealed figurative search bug**
- Psalm 20
- Psalm 8
- Psalm 97
- Psalm 145

### Next Up:
- Psalms 16-21
- Remaining psalms 16-150

## Performance Metrics

### Before Fix:
- Phrase searches: 800+ variations per phrase
- Total queries for "גור באהל": 824
- Time per phrase search: 30+ minutes
- Status: Hanging indefinitely

### After Fix:
- Phrase searches: 1 query (exact form only)
- Total queries for "גור באהל": 5
- Expected time per phrase search: Seconds
- Status: Should complete quickly

## Technical Debt

### Resolved:
1. ~~**Micro Analyst Structure Alignment**~~ (Session 176)
   - Fixed lexical_insights format handling
   - Phrase preservation working correctly

### Medium Priority:
2. **Search Optimization**
   - Consider caching frequent searches
   - Optimize database queries for phrase matching

### Low Priority:
3. **Enhanced Variant Generation**
   - Improve morphological variant detection
   - Add more sophisticated phrase matching

## Files Modified Recently

### `src/agents/figurative_librarian.py` (Session 179)
- Lines 475-511: Removed morphological variants from vehicle_search_terms
- Lines 509-530: Removed morphological variants from vehicle_contains
- Vehicle concepts now treated as hierarchical tags, not inflected words
- Only exact term and simple plural searched

### `src/agents/research_assembler.py` (Session 179)
- Lines 540-565: Added exact vehicle match prioritization
- Conditional logic only activates when vehicle_contains set AND results exceed max
- Prioritizes exact matches before compound or plural matches

### `src/concordance/search.py` (Session 176)
- Lines 244-269: Updated `_verse_contains_phrase` method
- Implemented substring matching for phrases
- Preserved exact matching for single words

### `src/agents/micro_analyst.py` (Session 176)
- Lines 1071-1159: Enhanced `_override_llm_base_forms` with substring matching
- Lines 984-1070: Phrase extraction helper methods
- Lines 720-726: Debug logging for LLM output

### `src/agents/concordance_librarian.py` (Session 175)
- Lines 613-625: Prevent phrase variations
- Lines 627-656: Handle alternate queries efficiently

## Database Status
- Location: `database/tanakh.db`
- Size: ~50MB
- Books: All 39 books of Tanakh
- Verses: 23,145 verses
- Indexed for fast full-text search

## Next Steps
1. Complete Psalm 15 analysis review
2. Test phrase matching fix with other psalms
3. Continue with remaining psalms (16-21 next)

## Notes
- Phrase substring matching working correctly
- Both exact phrase and variations are being searched
- Single word searches maintain precision
- Pipeline running without performance issues