# V3 Output Format Documentation

## Overview
Version 3 enhances the output format with verse-level details for all phrase, skipgram, and root matches. This allows users to see exactly WHERE in each psalm the matches occur.

## Key Changes from V2

### 1. Contiguous Phrases - Enhanced Format

**V2 Format** (had verse numbers but no position/text details):
```json
{
  "consonantal": "אין עש טוב",
  "hebrew": "אֵ֣ין עֹֽשֵׂה טֽוֹב׃",
  "length": 3,
  "count_a": 2,
  "count_b": 2,
  "verses_a": [1, 3],
  "verses_b": [2, 4]
}
```

**V3 Format** (adds position and Hebrew text for each occurrence):
```json
{
  "consonantal": "אין עש טוב",
  "hebrew": "אֵ֣ין עֹֽשֵׂה טֽוֹב׃",
  "length": 3,
  "count_a": 2,
  "count_b": 2,
  "verses_a": [1, 3],
  "verses_b": [2, 4],
  "matches_from_a": [
    {
      "verse": 1,
      "text": "אֵ֣ין עֹֽשֵׂה־טֽוֹב׃",
      "position": 15
    },
    {
      "verse": 3,
      "text": "אֵ֤ין עֹֽשֵׂה־ט֑וֹב",
      "position": 7
    }
  ],
  "matches_from_b": [
    {
      "verse": 2,
      "text": "אֵ֣ין עֹֽשֵׂה־טֽוֹב׃",
      "position": 16
    },
    {
      "verse": 4,
      "text": "אֵ֤ין עֹֽשֵׂה־ט֑וֹב",
      "position": 7
    }
  ]
}
```

**New Fields**:
- `matches_from_a`: List of all occurrences in Psalm A
  - `verse`: Verse number where match occurs
  - `text`: Actual Hebrew text of this occurrence (with vowels/cantillation)
  - `position`: Word position in the verse (0-indexed)
- `matches_from_b`: List of all occurrences in Psalm B

### 2. Skipgrams - Enhanced Format

**V2 Format** (minimal information):
```json
{
  "consonantal": "קראו שם  פחדו",
  "length": 4,
  "hebrew": "קראו שם  פחדו"
}
```

**V3 Format** (adds verse details, position ranges, full span text):
```json
{
  "consonantal": "קראו שם  פחדו",
  "matched_hebrew": "קראו שם  פחדו",
  "full_span_hebrew": "קָ֘רְא֤וּ בְשֵׁם־יְהֹוָה֮ שָׁ֤ם ׀ פָּ֣חֲדוּ פָ֑חַד",
  "length": 4,
  "gap_word_count": 3,
  "span_word_count": 7,
  "verses_a": [1, 5],
  "verses_b": [1],
  "matches_from_a": [
    {
      "verse": 1,
      "full_text": "קָ֘רְא֤וּ בְשֵׁם־יְהֹוָה֮ שָׁ֤ם ׀ פָּ֣חֲדוּ פָ֑חַד",
      "start_pos": 0,
      "end_pos": 7
    },
    {
      "verse": 5,
      "full_text": "קָ֘רְא֤וּ בְשֵׁם־יְהֹוָה֮ שָׁ֤ם ׀ פָּ֣חֲדוּ פָ֑חַד",
      "start_pos": 2,
      "end_pos": 9
    }
  ],
  "matches_from_b": [
    {
      "verse": 1,
      "full_text": "קָ֘רְא֤וּ בְשֵׁם־יְהֹוָה֮ שָׁ֤ם ׀ פָּ֣חֲדוּ פָ֑חַד",
      "start_pos": 0,
      "end_pos": 7
    }
  ]
}
```

**New Fields**:
- `full_span_hebrew`: Complete Hebrew text from first to last matched word (including gaps)
- `gap_word_count`: Number of words in the gaps (span - matched)
- `span_word_count`: Total words from first to last matched word
- `verses_a`, `verses_b`: Lists of verse numbers where skipgram appears
- `matches_from_a`, `matches_from_b`: Position ranges for each occurrence
  - `verse`: Verse number
  - `full_text`: Complete span including matched words and gaps
  - `start_pos`: Position of first matched word
  - `end_pos`: Position of last matched word

### 3. Roots - Enhanced Format

**V2 Format** (had examples but no verse details):
```json
{
  "root": "נצח",
  "idf": 0.8997614299229445,
  "count_a": 1,
  "count_b": 1,
  "examples_a": ["לַמְנַצֵּ֗חַ"],
  "examples_b": ["לַמְנַצֵּ֥חַ"]
}
```

**V3 Format** (adds verse numbers and positions):
```json
{
  "root": "נצח",
  "idf": 0.8997614299229445,
  "count_a": 1,
  "count_b": 1,
  "examples_a": ["לַמְנַצֵּ֗חַ"],
  "examples_b": ["לַמְנַצֵּ֥חַ"],
  "verses_a": [1],
  "verses_b": [1],
  "matches_from_a": [
    {
      "verse": 1,
      "text": "לַמְנַצֵּ֗חַ",
      "position": 0
    }
  ],
  "matches_from_b": [
    {
      "verse": 1,
      "text": "לַמְנַצֵּ֥חַ",
      "position": 0
    }
  ]
}
```

**New Fields**:
- `verses_a`, `verses_b`: Lists of verse numbers where root appears
- `matches_from_a`, `matches_from_b`: Details for each occurrence
  - `verse`: Verse number
  - `text`: Actual Hebrew word with vowels/cantillation
  - `position`: Word position in verse

## Implementation Details

### Database Structure

V3 queries the **tanakh.db** database:
- **verses table**: Full Hebrew text by verse
- **concordance table**: Individual words with positions
  - `word_consonantal_split`: Consonantal form (for matching)
  - `word`: Hebrew with vowels/cantillation
  - `verse`: Verse number
  - `position`: Word position in verse

### Helper Class: VerseDetailExtractor

The `VerseDetailExtractor` class provides methods to:
1. `get_psalm_concordance(psalm_number)`: Load all words for a psalm
2. `find_contiguous_phrase_matches(psalm_number, phrase)`: Find phrase occurrences
3. `find_skipgram_matches(psalm_number, skipgram)`: Find skipgram occurrences
4. `find_root_matches(psalm_number, root)`: Find root occurrences

All methods return verse-level details including:
- Verse numbers
- Hebrew text (with vowels/cantillation)
- Position information

### Performance Considerations

**Caching**: The `VerseDetailExtractor` caches concordance data for each psalm to avoid redundant database queries.

**File Size**: V3 output is larger than V2 due to verse-level details:
- V2: ~5 MB for top 500
- V3: ~6-7 MB for top 500 (estimated)

## Use Cases

### 1. Verse Context Analysis
With V3, you can:
- See which verses contain specific phrase matches
- Identify patterns that span multiple verses
- Analyze position patterns (beginning/middle/end of verses)

### 2. Comparative Study
Compare how the same phrase appears in different psalms:
- Different vowel pointing
- Different positions in verse structure
- Different verse contexts

### 3. Skipgram Gap Analysis
Understand skipgram patterns:
- How many words are in the gaps?
- What's the full context around matched words?
- Are gaps consistent across occurrences?

### 4. Comprehensive Research
Generate citations with exact verse and position references:
- "Phrase X appears in Psalm 14:1 at position 15"
- "Skipgram Y spans positions 0-7 in Psalm 14:1"

## Example Output

See `/data/analysis_results/top_500_connections_skipgram_dedup_v3.json` for complete examples.

Sample entry (Psalms 14-53, rank 1):
```json
{
  "rank": 1,
  "psalm_a": 14,
  "psalm_b": 53,
  "final_score": 72862.78,
  "deduplicated_contiguous_phrases": [
    {
      "consonantal": "אין עש טוב",
      "hebrew": "אֵ֣ין עֹֽשֵׂה טֽוֹב׃",
      "length": 3,
      "count_a": 2,
      "count_b": 2,
      "verses_a": [1, 3],
      "verses_b": [2, 4],
      "matches_from_a": [
        {"verse": 1, "text": "אֵ֣ין עֹֽשֵׂה־טֽוֹב׃", "position": 15},
        {"verse": 3, "text": "אֵ֤ין עֹֽשֵׂה־ט֑וֹב", "position": 7}
      ],
      "matches_from_b": [
        {"verse": 2, "text": "אֵ֣ין עֹֽשֵׂה־טֽוֹב׃", "position": 16},
        {"verse": 4, "text": "אֵ֤ין עֹֽשֵׂה־ט֑וֹב", "position": 7}
      ]
    }
  ],
  ...
}
```

## Running V3 Scripts

1. **Generate V3 scores**:
   ```bash
   python3 scripts/statistical_analysis/enhanced_scorer_skipgram_dedup_v3.py
   ```

2. **Generate top 500 with verse details**:
   ```bash
   python3 scripts/statistical_analysis/generate_top_500_skipgram_dedup_v3.py
   ```

## Dependencies

- Python 3.7+
- sqlite3 (standard library)
- json (standard library)
- tanakh.db database with concordance data

## Notes

- All position indices are 0-based
- Hebrew text includes vowels and cantillation marks
- Verse numbers are 1-based (matching biblical convention)
- Position information allows exact location within verses
