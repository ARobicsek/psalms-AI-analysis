# Phrase Search Bug Summary

## Root Cause Identified

After extensive debugging, I've found the root cause of why phrase searches return 0 results despite the micro analyst providing exact phrases from the text.

### The Issue

1. **Micro Analyst provides**: `יָגוּר` and `בְּאׇהֳלֶךָ` (exact forms from Psalm 15:1)
2. **Database contains**: `יגור` and `באהלך` at Psalm 15:1 positions 4-5
3. **Search performed**: `גור באהל` (base forms) → **0 RESULTS**

### Key Discovery

The micro analyst's output shows it correctly identifies the exact phrase and provides variants:

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

But the search results show:
- **Search 2: גור באהל** - 0 results (using base forms)
- **Search 4: הלך תמים** - 0 results (base forms)

### Where the Bug Occurs

The conversion happens between the micro analyst and the librarian. The system is:
1. Taking the exact phrase from micro analyst: `יָגוּר`
2. Converting it to a base form: `גור`
3. Losing the prefix `י` that exists in the actual text
4. Searching for the wrong form

### Why This Is Critical

- The micro analyst is doing its job correctly by providing exact forms
- The librarian has good variation generation that would find matches
- But something in the middle is stripping the morphological information
- This defeats the entire purpose of having exact phrases

### The Fix Needed

We need to ensure that:
1. The **primary phrase** from micro analyst is used as-is (not normalized)
2. The **variants** are used as alternative searches
3. The librarian searches for: `יגור באהלך` first (exact match)
4. Then searches variants: `גור באהל`, `יגור אהל`, etc.

### Technical Location

The issue is likely in the data transformation pipeline where micro analyst output is converted to librarian requests. This could be in:
- `scholar_researcher.py` - when processing micro analyst lexical insights
- `research_assembler.py` - when creating concordance requests
- The data model itself if it's storing normalized forms

### Impact

This affects ALL phrase searches from source psalms, severely compromising research quality. The system is missing the very connections it's designed to find.

### Next Steps

1. Trace the data flow from micro analyst JSON to librarian request
2. Identify where the normalization/stripping occurs
3. Preserve the exact phrase as the primary search term
4. Test with Psalm 15 to verify the fix