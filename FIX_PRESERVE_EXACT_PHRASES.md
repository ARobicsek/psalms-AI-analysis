# Fix: Preserve Exact Phrases from Micro Analyst

## Root Cause Confirmed

The micro analyst correctly provides exact phrases with morphological prefixes/suffixes:
- `יָגוּר` (not `גור`)
- `בְּאׇהֳלֶךָ` (not `אהל`)
- `הוֹלֵךְ תָּמִים` (not `הלך תמים`)

But the LLM in `_generate_research_requests()` is converting these to base forms, causing 0 search results.

## Solution Options

### Option 1: Strengthen the LLM Prompt
Add explicit warnings and examples to the RESEARCH_REQUEST_PROMPT:

```python
# Add to line 231-232:
CRITICAL WARNING: DO NOT strip prefixes or suffixes!
If the micro analyst provides "יָגוּר", you MUST search for "יָגוּר" (not "גור").
The database contains these exact forms, and stripping them will cause 0 results.

Example:
- Micro analyst: "יָגוּר" → Search: "יָגוּר" (NOT "גור")
- Micro analyst: "בְּאׇהֳלֶךָ" → Search: "באהלך" (NOT "אהל")
```

### Option 2: Post-Processing Fix (Recommended)
Process the LLM output to extract exact phrases from the discoveries and override the LLM's base forms:

```python
def _extract_exact_phrases_from_discoveries(self, discoveries: dict) -> Dict[str, str]:
    """Extract exact phrases from discoveries to override LLM base forms."""
    phrase_mapping = {}

    for verse_disc in discoveries.get('verse_discoveries', []):
        for insight in verse_disc.get('lexical_insights', []):
            phrase = insight.get('phrase', '')
            # Remove vowel points but keep prefixes/suffixes
            import re
            # Remove niqqud but keep consonants and sheva na
            clean_phrase = re.sub(r'[\u0591-\u05C7]', '', phrase)

            # Create a normalized key for matching
            key = re.sub(r'[^\u05D0-\u05EA]', '', clean_phrase)  # Only Hebrew letters

            if key and clean_phrase:
                phrase_mapping[key] = clean_phrase

    return phrase_mapping

def _fix_research_requests(self, research_request: ScholarResearchRequest, discoveries: dict):
    """Fix research requests to use exact phrases from discoveries."""
    # Get exact phrases
    exact_phrases = self._extract_exact_phrases_from_discoveries(discoveries)

    # Fix concordance searches
    for search in research_request.concordance_searches:
        query = search.get('query', '')
        # Normalize query for matching
        normalized = re.sub(r'[^\u05D0-\u05EA]', '', query)

        # Check if we have an exact phrase for this
        if normalized in exact_phrases:
            search['query'] = exact_phrases[normalized]
            search['notes'] += " [FIXED: Using exact phrase from micro analyst]"
```

### Option 3: Bypass LLM for Phrase Extraction
Don't rely on the LLM to extract phrases from lexical_insights. Extract them programmatically:

```python
def _generate_concordance_requests_directly(self, discoveries: dict) -> List[Dict]:
    """Generate concordance requests directly from lexical insights, bypassing LLM."""
    requests = []

    for verse_disc in discoveries.get('verse_discoveries', []):
        for insight in verse_disc.get('lexical_insights', []):
            phrase = insight.get('phrase', '')
            if phrase:
                # Remove vowel points for searching
                import re
                clean_phrase = re.sub(r'[\u0591-\u05C7]', '', phrase)

                request = {
                    "query": clean_phrase,
                    "scope": "auto",
                    "level": "consonantal",
                    "purpose": insight.get('notes', ''),
                    "source": "lexical_insight"
                }

                # Add variants as alternates
                variants = insight.get('variants', [])
                if variants:
                    # Remove vowel points from variants too
                    clean_variants = [re.sub(r'[\u0591-\u05C7]', '', v) for v in variants]
                    # Remove duplicates with main phrase
                    clean_variants = [v for v in clean_variants if v != clean_phrase]
                    if clean_variants:
                        request['alternate_queries'] = clean_variants

                requests.append(request)

    return requests
```

## Recommended Implementation

Use **Option 2** (Post-Processing Fix) because:
1. It preserves the existing LLM workflow
2. It guarantees exact phrases are used
3. It's easy to implement and test
4. It provides fallback if LLM improves

## Testing

After implementing the fix:
1. Run Psalm 15 pipeline
2. Check that searches use exact phrases:
   - `יגור באהלך` instead of `גור באהל`
   - `הולך תמים` instead of `הלך תמים`
3. Verify results are found (should be > 0 for these phrases)