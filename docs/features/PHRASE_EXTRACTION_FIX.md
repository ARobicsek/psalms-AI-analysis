# Fix Plan: Phrase Extraction Bug

## Problem Summary
The phrase preservation fix from Session 173 is not working correctly. For Psalm 15:2:
- Verse text has: "ודובר אמת בלבבו" (with vav prefix and final he)
- Micro analyst extracted: "דבר אמת בלבב" (missing vav and he)
- Search query became: "דבר בלב" (missing "אמת" entirely!)

## Root Cause Analysis

### 1. **LLM is Modifying Exact Phrases**
Despite instructions to preserve exact forms, the LLM in `_generate_research_requests()` is normalizing/modifying the phrases.

### 2. **Extraction Not Working**
The `_extract_exact_phrases_from_discoveries()` method should extract from the discoveries, but the discoveries themselves contain modified forms.

### 3. **Override Mechanism Too Weak**
The `_override_llm_base_forms()` method tries to fix this but can't find the correct match because the extracted phrase is too different.

## Solution Implementation

### Fix 1: Add Direct Verse Text Extraction
In `_override_llm_base_forms()`, add a fallback to extract directly from verse text if phrase mapping doesn't work:

```python
def _override_llm_base_forms(self, research_request, exact_phrases, variants_mapping, psalm_text):
    # ... existing code ...

    # NEW: If no match found, try to extract directly from verse text
    if fixed_count == 0 and self.logger:
        self.logger.warning("No exact phrase matches found in discoveries, attempting verse text extraction")

    for req in research_request.concordance_requests:
        original_query = req.query

        # Skip if already fixed
        if "[FIXED: Using exact phrase]" in req.notes:
            continue

        # Try to find phrase in verse text
        for verse_key, verse_data in psalm_text.items():
            if 'hebrew' in verse_data:
                hebrew_text = verse_data['hebrew']
                # Remove vowels for comparison
                hebrew_clean = re.sub(r'[\u0591-\u05C7]', '', hebrew_text)
                query_clean = re.sub(r'[\u0591-\u05C7]', '', original_query)

                # Check if query is substring of verse (allowing extra prefixes/suffixes)
                if query_clean in hebrew_text or hebrew_text in query_clean:
                    # Extract the exact form from verse
                    # Find the match and extract with context
                    match_start = hebrew_text.find(query_clean.split()[0]) if query_clean in hebrew_text else -1
                    if match_start >= 0:
                        # Extract words around match
                        words = split_words(hebrew_text)
                        query_words = split_words(query_clean)

                        # Find matching sequence
                        for i in range(len(words) - len(query_words) + 1):
                            potential = ''.join(words[i:i+len(query_words)])
                            if self._close_match(potential, query_clean):
                                exact_form = ' '.join(words[i:i+len(query_words)])
                                req.query = exact_form
                                req.notes += f" [FIXED: Extracted from verse text]"
                                fixed_count += 1
                                self.logger.info(f"    ✓ Fixed '{original_query}' → '{req.query}' (from verse)")
                                break
```

### Fix 2: Improve Phrase Matching
Add a helper method to check if phrases are close matches:

```python
def _close_match(self, phrase1: str, phrase2: str) -> bool:
    """Check if two Hebrew phrases are close matches (accounting for minor differences)."""
    # Remove all non-Hebrew characters
    p1 = re.sub(r'[^\u05D0-\u05EA]', '', phrase1)
    p2 = re.sub(r'[^\u05D0-\u05EA]', '', phrase2)

    # Check if one is substring of the other
    if p1 in p2 or p2 in p1:
        return True

    # Check if they share most characters (80% similarity)
    common = set(p1) & set(p2)
    total = set(p1) | set(p2)
    if len(common) / len(total) > 0.8:
        return True

    return False
```

### Fix 3: Add Debug Logging
Add comprehensive logging to track what's happening:

```python
def _generate_research_requests(self, psalm_number, macro_analysis, verse_commentaries):
    # ... existing code ...

    # After LLM processing:
    if self.logger:
        self.logger.info("=== Phrase Extraction Debug ===")
        for i, req in enumerate(research_request.concordance_requests):
            self.logger.info(f"Request {i+1}: query='{req.query}' notes='{req.notes}'")
            if hasattr(req, 'alternates') and req.alternates:
                self.logger.info(f"  Alternates: {req.alternates}")

    # Extract exact phrases and override
    exact_phrases, variants_mapping = self._extract_exact_phrases_from_discoveries(discoveries)

    if self.logger:
        self.logger.info(f"Extracted {len(exact_phrases)} exact phrases from discoveries")
        for key, phrase in exact_phrases.items():
            self.logger.info(f"  '{key}' → '{phrase}'")

    # Override with verse text backup
    research_request = self._override_llm_base_forms(
        research_request,
        exact_phrases,
        variants_mapping,
        verse_commentaries  # Pass verse text for fallback extraction
    )
```

### Fix 4: Strengthen Prompt Instructions
Update the RESEARCH_REQUEST_PROMPT to emphasize preserving exact forms:

```python
CRITICAL_INSTRUCTIONS = """
## CRITICAL: Preserve Exact Hebrew Forms!

When extracting phrases for concordance search:
1. NEVER modify the Hebrew form - copy EXACTLY as it appears
2. Include ALL prefixes (ו, ה, ב, ל, מ, כ)
3. Include ALL suffixes (י, ך, ו, ה, נו, כם, etc.)
4. DO NOT remove vowel points - keep full pointing
5. DO NOT normalize to base forms

Example:
- Verse has: "וְדֹבֵר אֱמֶת בִּלְבָבוֹ"
- Extract: "וְדֹבֵר אֱמֶת בִּלְבָבוֹ" (EXACT copy)
- WRONG: "דבר אמת בלב" (DO NOT DO THIS!)

The phrase preservation mechanism depends on you preserving the EXACT form!
"""
```

## Testing the Fix

1. Run Psalm 15 pipeline
2. Check logs for:
   - "Fixed X queries to preserve exact morphology" messages
   - Correct phrase extraction from verse text
   - Search queries matching verse text exactly

## Expected Results

- Psalm 15:2 should search for "ודבר אמת בלבבו" or "דבר אמת בלבבו"
- NOT "דבר בלב" or "דבר אמת בלבב"
- Search should find Psalm 15:2 quickly (not 824 failed queries)

## Files to Modify

1. `src/agents/micro_analyst.py`
   - `_override_llm_base_forms()` method (lines 979-1024)
   - Add `_close_match()` helper method
   - Update `_generate_research_requests()` with debug logging
   - Strengthen RESEARCH_REQUEST_PROMPT instructions

This fix ensures that even if the LLM fails to preserve exact forms, we have a robust fallback that extracts directly from the verse text.