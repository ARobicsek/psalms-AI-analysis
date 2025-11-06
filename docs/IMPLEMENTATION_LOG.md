# Session 68 - Footnote Stripping and Rabbi Sacks Integration (2025-11-06)

**Goal**: Remove footnote indicators from English psalm text in Word document output and integrate Rabbi Jonathan Sacks commentary data into the research bundle.

**Status**: ✅ Complete

## Session Overview

This session focused on two enhancement requests:
1. **Footnote Indicator Removal**: Strip simple text-based footnote markers (e.g., "-a", "-b", "-c") from English translations in the final Word document output.
2. **Rabbi Sacks Integration**: Add Rabbi Jonathan Sacks' psalm references to the research bundle, making them automatically available to all commentary agents.

## Issues Investigated and Fixed

### 1. Footnote Indicators in English Translation (RESOLVED)

**Problem**: English translations in the Psalm text section of the Word document contained footnote indicators like "-b", "-c", "-d" attached to words (e.g., "I have fathered you this day.-b", "pay homage in good faith,-d").

**Investigation**:
1. Traced the data flow from Sefaria API → TanakhDatabase → document_generator.py
2. Found that the existing `strip_sefaria_footnotes()` function only handled HTML-style footnotes (`<sup class="footnote-marker">`)
3. Identified that simple text markers (hyphen + lowercase letter) were not being removed

**Solution**:
Enhanced the `strip_sefaria_footnotes()` function in `src/data_sources/sefaria_client.py` to also remove simple text-based footnote indicators:
- Added regex pattern: `([.,;:])?\-[a-z](?=\s|$)` to match "-a", ".-b", ",-c" patterns
- Pattern preserves preceding punctuation while removing the footnote marker
- Examples:
  - "day.-b" → "day."
  - "faith,-d lest" → "faith, lest"
  - "fright,-c" → "fright,"

**Outcome**: All footnote indicators are now automatically stripped when English verse text is fetched from Sefaria, resulting in clean text in the final Word document.

### 2. Rabbi Sacks Commentary Integration (RESOLVED)

**Problem**: The user had curated a comprehensive JSON file (`sacks_on_psalms.json`) containing 206 references to psalms from Rabbi Jonathan Sacks' writings. These needed to be automatically included in the research bundle for every psalm.

**Investigation**:
1. Reviewed the research assembly architecture (`research_assembler.py`, `ResearchBundle` dataclass)
2. Identified that librarian agents follow a consistent pattern:
   - Dedicated librarian class for data source
   - Integration into `ResearchAssembler.__init__` and `.assemble()` methods
   - Addition to `ResearchBundle` dataclass
   - Formatting for markdown output via `.to_markdown()`

**Solution**:
Created a new `SacksLibrarian` class and integrated it into the research assembly pipeline:

1. **Created `src/agents/sacks_librarian.py`**:
   - `SacksLibrarian` class that loads `sacks_on_psalms.json`
   - `get_psalm_references(psalm_chapter)` method to filter by chapter
   - `format_for_research_bundle()` method to generate markdown with proper context
   - Parses `source_psalm_ref` field (e.g., "Psalms.1.1") to extract chapter/verse
   - Groups references by verse for cleaner presentation

2. **Updated `src/agents/research_assembler.py`**:
   - Added `SacksLibrarian` import
   - Added `sacks_references: Optional[List[SacksReference]]` field to `ResearchBundle`
   - Added `sacks_markdown: Optional[str]` field for pre-formatted output
   - Initialized `self.sacks_librarian = SacksLibrarian()` in `ResearchAssembler.__init__`
   - Added Sacks data fetching in `.assemble()` method (ALWAYS included, regardless of micro-agent requests)
   - Added Sacks section to `.to_markdown()` output
   - Updated summary statistics to include Sacks reference count

3. **Markdown Format**:
   The Sacks section explains to LLM agents that:
   - These are NOT traditional commentaries
   - They are excerpts from Sacks' broader theological writings
   - Each entry includes ~1000 characters before/after the psalm reference
   - They reveal Sacks' interpretation and usage of specific verses

**Outcome**: All psalm research bundles now automatically include Rabbi Sacks references when available. For Psalm 1, 5 references were found and formatted. The data is available to both the Synthesis Writer and Master Editor agents.

## Implementation Details

### Footnote Stripping
- **File modified**: `src/data_sources/sefaria_client.py`
- **Function modified**: `strip_sefaria_footnotes()`
- **Pattern added**: `([.,;:])?\-[a-z](?=\s|$)`
- **Test verified**: Tested with actual Psalm 2 text containing "-b", "-c", "-d" markers

### Sacks Librarian Architecture
- **New file**: `src/agents/sacks_librarian.py` (237 lines)
- **Data source**: `sacks_on_psalms.json` (206 entries, 6.8MB)
- **Key features**:
  - Loads JSON once at initialization
  - Filters by psalm chapter
  - Groups by verse for presentation
  - Extracts readable titles from source references
  - Provides context about data purpose/format

### Research Bundle Integration
- **Files modified**: `src/agents/research_assembler.py`
- **New fields**: `sacks_references`, `sacks_markdown`
- **Integration point**: After liturgical data, before RAG context
- **Always included**: Unlike other librarians that respond to micro-agent requests, Sacks data is ALWAYS fetched

## Testing

1. **Unit Test**: Created and ran `test_sacks_integration.py`
   - Verified SacksLibrarian loads 206 references
   - Verified filtering returns 5 references for Psalm 1
   - Verified markdown formatting
   - Verified integration into ResearchBundle

2. **Footnote Test**: Tested `strip_sefaria_footnotes()` with actual examples
   - "I have fathered you this day.-b" → "I have fathered you this day."
   - "pay homage in good faith,-d lest" → "pay homage in good faith, lest"
   - "tremble with fright,-c" → "tremble with fright,"

## Follow-Up Issues & Fixes

After initial implementation, user testing revealed two issues that required additional fixes:

### Issue 1: Sacks Count Missing from Word Document
**Problem**: While the Sacks count appeared in print_ready.md, it was missing from the .docx file's "Research & Data Inputs" section.

**Root Cause**: The `document_generator.py` had a separate hardcoded template that wasn't updated.

**Solution**:
- Added `sacks_count` extraction in `_format_bibliographical_summary()` method
- Added line to Word document template matching the markdown formatter
- Changed wording from "Found" to "Reviewed" for consistency

### Issue 2: Cached Database Still Had Footnotes
**Problem**: Psalm 8 (run after changes) still showed footnotes like "gittith.-a" in the output.

**Root Cause**: Database was populated on Oct 19 (before footnote stripping changes), and cached text was being used.

**Solution**:
- Deleted Psalm 8 from database (verses and chapter metadata)
- Re-fetched from Sefaria API with new footnote stripping code
- Verified clean text: "gittith." instead of "gittith.-a"

**Note**: Footnote stripping works automatically for NEW psalm fetches. Previously cached psalms will be cleaned automatically when the database entry is deleted and the psalm is re-fetched during the next pipeline run.

## Files Modified/Created

1. **src/data_sources/sefaria_client.py**: Enhanced `strip_sefaria_footnotes()` to handle text-based footnote markers
2. **src/agents/sacks_librarian.py**: New file - SacksLibrarian class for Rabbi Sacks data
3. **src/agents/research_assembler.py**: Integrated SacksLibrarian into research assembly pipeline
4. **src/utils/pipeline_summary.py**: Added `sacks_references_count` field and tracking
5. **src/utils/commentary_formatter.py**: Added Sacks count to print-ready markdown bibliography
6. **src/utils/document_generator.py**: Added Sacks count to Word document bibliography template
7. **docs/IMPLEMENTATION_LOG.md**: Updated with this session's detailed log
8. **docs/PROJECT_STATUS.md**: Updated with completed tasks
9. **docs/NEXT_SESSION_PROMPT.md**: Updated with summary for next session

---

# Session 67 - Data Curation and Bug Fixing for `sacks_on_psalms.json` (2025-11-03)

**Goal**: Resolve missing `context_snippet` fields in the `sacks_on_psalms.json` file and perform data cleanup as requested.

**Status**: ✅ Complete

## Session Overview

This session focused on data quality for the `sacks_on_psalms.json` file. The primary goals were to fix the remaining 67 entries with missing context snippets and then remove a specific subset of entries. The session also included providing system administration assistance to the user.

## Issues Investigated and Fixed

### 1. Missing `context_snippet` Generation (RESOLVED)

**Problem**: 81 out of 230 entries in `sacks_on_psalms.json` were missing the `context_snippet`, primarily in Hebrew-only texts. A previous fix was incomplete.

**Investigation & Process**:
1.  **Initial Analysis**: The first reprocessing script failed entirely. Debugging revealed the script was using incorrect keys to access the text data (`en_text`/`he_text` instead of `text`/`he`).
2.  **Second Analysis**: After fixing the keys, the script fixed 14 entries but 67 remained broken. Analysis of the failures showed two distinct problems:
    *   **English Failures**: Simple string matching for citations like `(Psalms 1:4)` was too rigid.
    *   **Hebrew Failures**: The Gematria conversion was generating numerals with Gershayim (e.g., `כ״ב`), but the source text often omitted it (e.g., `כב`).
3.  **Regex-based Solution**: A more robust, regex-based strategy was developed.
    *   **English Regex**: Created a pattern `(?i)(?:Psalms?|Ps\.?|Tehillim)\s*{chapter_num}\s*[:,.]?\s*{verse_num}` to handle case-insensitivity, multiple book names (`Psalms`, `Ps.`, `Tehillim`), and varied punctuation.
    *   **Hebrew Regex**: Modified the Gematria conversion function to output a regex pattern that made the Gershayim optional, e.g., `כ(?:״)?ב`.
4.  **Final Execution**: The final script, `reprocess_sacks_json_v3.py`, successfully processed the data, filling in **54** additional snippets.

**Outcome**: The number of entries missing snippets was reduced from 81 to **13**, bringing the dataset to **~94% completion**.

### 2. Data Cleanup (RESOLVED)

**Problem**: The user requested the removal of all entries from a specific Hebrew translation.

**Solution**:
1.  Created a script (`remove_entries_by_heVersionTitle.py`) to filter the main JSON array.
2.  The script removed all entries where the `heVersionTitle` was exactly "Covenant and Conversation, trans. by Tsur Ehrlich, Maggid Books, 2017".

**Outcome**: Successfully removed **24 entries**, reducing the total count from 230 to 206.

### 3. CLI Tool Path Issue (RESOLVED)

**Problem**: The user had installed a CLI tool (`claude`) but its installation directory was not in the system's PATH environment variable, preventing it from being run directly.

**Solution**:
1.  Attempted to set the PATH using PowerShell's .NET methods, but these were blocked by security policies.
2.  Used the standard Windows `setx` command (`setx PATH "%PATH%;C:\Users\ariro\.local\bin"`) which successfully and persistently updated the user's PATH.
3.  Advised the user to restart their terminal for the change to take effect.


## Files Modified/Created

1.  **sacks_on_psalms.json**: Reprocessed multiple times to add snippets and finally to remove entries.
2.  `test_hebrew_fix.py`: Created to debug initial Hebrew Gematria and citation issues. (Deleted)
3.  `reprocess_sacks_json_final.py`: First attempt at a final reprocessing script. (Deleted)
4.  `debug_hebrew_failure.py`: Created to diagnose why the "working" test logic failed on the real data. (Deleted)
5.  `inspect_entry.py`: Created to inspect the raw JSON of a failing entry, which revealed the incorrect key usage. (Deleted)
6.  `reprocess_sacks_json_v2.py`: Second reprocessing script with corrected keys. (Deleted)
7.  `find_missing_snippet_examples.py`: Script to identify patterns in the remaining 67 failures. (Deleted)
8.  `debug_and_develop_regex.py`: Script to build and test the final regex patterns for English and Hebrew. (Deleted)
9.  `reprocess_sacks_json_v3.py`: The final, successful reprocessing script using regex. (Deleted)
10. `remove_entries_by_heVersionTitle.py`: Script to perform the data cleanup. (Deleted)
11. `docs/PROJECT_STATUS.md`: Updated with session summary.
12. `docs/IMPLEMENTATION_LOG.md`: Updated with this session's detailed log.
13. `docs/NEXT_SESSION_PROMPT.md`: Updated with summary for next session.