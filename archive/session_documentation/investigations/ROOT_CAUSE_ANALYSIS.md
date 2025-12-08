# Root Cause Analysis: Phrase Search Non-Matching

## Issue Summary
Concordance searches are returning 0 results for phrases that exist in the source psalm, despite the micro analyst providing exact phrases from the text.

## Key Findings

### 1. Database Content Confirmed
- Psalm 15:1 contains: **יגור** (position 4) and **באהלך** (position 5)
- Psalm 15:2 contains: **הולך** (position 1) and **תמים** (position 2)

### 2. Micro Analyst Output is Correct
The micro analyst IS providing exact phrases with variants:

```json
{
  "phrase": "יָגוּר",
  "variants": ["גור", "גר", "יגור", "תגור"]
},
{
  "phrase": "בְּאׇהֳלֶךָ",
  "variants": ["אהל", "אהלי", "אהלך", "באהל"]
}
```

### 3. Searches Are Using Base Forms
The actual searches being performed are:
- **"גור באהל"** (base forms) - 0 results
- **"הלך תמים"** (base forms) - 0 results

Instead of:
- **"יגור באהלך"** (exact forms) - should find matches

### 4. Root Cause Identified

The issue is in the **conversion pipeline** from micro analyst to librarian:

1. Micro analyst provides: `"phrase": "יָגוּר"` with full vocalization
2. Scholar researcher converts to: `"גור"` (base consonantal form)
3. Librarian searches for: `"גור באהל"` instead of `"יגור באהלך"`

The conversion process is stripping prefixes and suffixes, defeating the purpose of having the exact phrase from the micro analyst.

## Technical Details

### Expected Flow
```
Micro Analyst: "יָגוּר בְּאׇהֳלֶךָ" → Librarian: Search for exact phrase + variations
```

### Actual Flow
```
Micro Analyst: "יָגוּר בְּאׇהֳלֶךָ" → Scholar Researcher: "גור באהל" → Librarian: 0 results
```

## Fix Location

The issue is in the **scholar_researcher.py** file, specifically in the `to_research_request` method where it processes the micro analyst's phrase/variants structure. It appears to be using only the base variants instead of the primary phrase.

## Solution Strategy

1. **Primary Search**: Always use the exact phrase provided by micro analyst as the primary search term
2. **Variant Searches**: Use the provided variants as additional searches
3. **Preserve Morphology**: Don't normalize away prefixes/suffixes that are in the original text

## Impact

This is a critical issue affecting:
- All phrase searches from source psalms
- Research quality (missing key textual connections)
- User trust in the system's accuracy

## Next Steps

1. Examine `scholar_researcher.py` to find where the conversion happens
2. Ensure the primary phrase from micro analyst is preserved
3. Test with Psalm 15 phrases to verify fix