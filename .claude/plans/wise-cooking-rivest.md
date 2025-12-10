# Plan: Fix English Text Cleaning in Thematic Corpus

## Problem
The English text cleaning in `src/thematic/corpus_builder.py` is not properly removing footnotes and annotations, resulting in messy text with artifacts like:
- `*dust Heb. 'afar. Cf. the second note at 2.7.*`
- `humankindhumankind Moved up from v. 24 for clarity`
- `humushumus Lit. "soil." See the second note at 2.7.`

## Solution Approach

### 1. Update clean_english_text() function in src/thematic/corpus_builder.py
Replace the current implementation with a more robust version that:
- Handles asterisk-prefixed footnotes correctly
- Prevents duplicate word artifacts
- Processes text sequentially to avoid pattern conflicts

### 2. Key Pattern Improvements
- **Asterisk duplicates**: Fix pattern to handle `*word text*word` → `word`
- **Hebrew notes**: Handle `*word Heb. 'text'.*` and variations
- **Cross-references**: Remove `Cf. reference.` patterns
- **Editorial notes**: Remove "Moved up from v. X" and "Lit. 'text'" notes
- **Duplicate prevention**: Add post-processing to fix concatenated words

### 3. Implementation Steps
1. Copy the improved cleaning logic from `scripts/debug_cleaning.py`
2. Adapt it for use in the corpus builder
3. Add comprehensive comments explaining each pattern
4. Test with the problematic Genesis 3:19-23 chunk

### 4. Files to Modify
- `src/thematic/corpus_builder.py` - Update clean_english_text() function

### 5. Testing
- Rebuild the corpus after updating
- Verify the Genesis 3:19-23 chunk is properly cleaned
- Check a sample of other chunks to ensure no regressions

## Expected Outcome
The cleaned text should look like:
"By the sweat of your brow Shall you get bread to eat, Until you return to the ground—For from it you were taken. For dust you are, And to dust you shall return." The Human named his wife Eve, because she was the mother of all the living. And God LORD made garments of skins for Adam and his wife, and clothed them. And God LORD said, "Now that humankind has become like any of us, knowing good and bad, what if one should stretch out a hand and take also from the tree of life and eat, and live forever!" So God LORD banished humankind from the garden of Eden, to till the soil from which it was taken: