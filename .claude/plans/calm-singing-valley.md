# Plan: Fix Tanakh Corpus - Hebrew-Only Approach

## Problem Summary
The English text from Sefaria API contains extensive academic footnotes (e.g., "God יהוה formed the Human*the Human I.e., the progenitor... Heb. ha-'adam..."). These footnotes are deeply embedded and complex, making regex-based cleaning unreliable.

## Root Cause Analysis
1. **Sefaria Returns Academic Text**: The API provides scholarly translations with extensive inline commentary
2. **Cleaning is Fragile**: Regex patterns cannot reliably distinguish between text and footnotes
3. **Complex Patterns**: Footnotes use various formats (asterisks, "Heb.", "Lit.", parenthetical notes, etc.)
4. **Test Results**: Genesis 2:7 contains 3 "Heb." notes in a single verse

## Recommended Solution: Hebrew-Only Chunks

### Phase 1: Modify Corpus Builder for Hebrew-Only Chunks
1. **Update `src/thematic/corpus_builder.py`**:
   - Remove English text from chunks entirely
   - Keep only Hebrew text for semantic search
   - Update the `TanakhChunk` schema to make `english_text` optional or null

2. **Key Changes**:
   ```python
   # In _create_chunk method:
   hebrew_text = clean_hebrew_text(" ".join(v["hebrew"] for v in verses))
   english_text = None  # Or empty string if schema requires it

   # Or keep minimal English for reference only
   english_text = f"{reference}"  # Just the reference
   ```

### Phase 2: Update Chunk Schema
1. **Modify `src/thematic/chunk_schemas.py`**:
   - Make `english_text` optional
   - Add `hebrew_only` flag to indicate chunks without English

### Phase 3: Regenerate Corpus
1. **Backup current corpus**:
   ```bash
   mv data/thematic_corpus data/thematic_corpus_with_english
   ```

2. **Regenerate Hebrew-only corpus**:
   ```bash
   python scripts/build_thematic_corpus.py
   ```

### Phase 4: Update Search and Processing
1. **Update any code that expects English text**:
   - Search algorithms
   - Display functions
   - Embedding generation (if it uses English)

### Phase 5: Benefits of Hebrew-Only Approach
1. **Clean Data**: No footnote contamination
2. **Authentic Text**: Working with original Hebrew
3. **Smaller Corpus**: Reduced storage and processing
4. **Better Semantic Search**: Hebrew keywords and concepts without translation noise

## Alternative: Minimal English Reference
If some English is needed for reference:
1. Keep only verse references (e.g., "Genesis 2:7")
2. Or fetch clean English from a different source (e.g., World English Bible)
3. Or maintain a separate clean English index

## Files to Modify
1. `src/thematic/corpus_builder.py` - Remove English text from chunks
2. `src/thematic/chunk_schemas.py` - Make english_text optional
3. Any search/display code that expects English text

## Success Criteria
- Hebrew text chunks are clean and footnote-free
- Corpus generation is faster and more reliable
- Search works effectively with Hebrew-only content
- No complex regex cleaning needed