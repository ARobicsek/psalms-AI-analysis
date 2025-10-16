# Next Session Prompt: Morphology Enhancement Refinements

## Context
Continuing work on the Psalms AI commentary pipeline. Day 5 enhancements were completed (BDB fix, logging system, morphology variations), but three critical issues were identified with the morphology variation generator that need refinement.

## Start the Next Session With This Prompt

```
I'm continuing work on the Psalms AI commentary pipeline.

Please read these files in order:
1. docs/CONTEXT.md (project overview)
2. docs/PROJECT_STATUS.md (current status)
3. docs/IMPLEMENTATION_LOG.md (scroll to Day 5 entry - most recent)
4. docs/DAY_5_ENHANCEMENTS.md (completed enhancements)

## Critical Issues to Address

We completed 3 enhancements before Day 5, but the morphology variation generator
(src/concordance/morphology_variations.py) has three problems that need fixing:

### Issue 1: Nonsense Word Generation
**Problem**: The generator creates morphologically invalid forms like "יהָרעה"
(combining imperfect prefix י + Hophal prefix הָ + root).

**Root Cause**: Pattern-based generation combines ALL patterns without linguistic rules.
- Imperfect prefixes (י, ת, א, נ) are being combined with stem prefixes (הָ, הִ, נ)
- This creates impossible combinations

**Solution Needed**:
- Implement linguistic constraints
- Imperfect tense already contains stem information (don't add stem prefix)
- Qal imperfect: יִקְטֹל (prefix only)
- Hiphil imperfect: יַקְטִיל (different vowel pattern, not prefix stacking)
- Either use vowel patterns OR use mutually-exclusive prefix sets

**Recommendation**: Create separate variation sets:
1. Perfect forms: stem prefix + root + suffixes
2. Imperfect forms: person prefix + root (no stem prefix needed)
3. Participles: participle prefix + root
4. Nouns: root + suffixes only

### Issue 2: Final Letter Forms Not Handled
**Problem**: Generated "ברךו" instead of "ברכו" (using medial ך instead of final כ).

**Root Cause**: Generator doesn't handle Hebrew final forms:
- כ (medial) → ך (final)
- מ (medial) → ם (final)
- נ (medial) → ן (final)
- פ (medial) → ף (final)
- צ (medial) → ץ (final)

**Solution Needed**:
Add function to convert final letters when they appear at word end:
```python
FINAL_FORMS = {
    'כ': 'ך',
    'מ': 'ם',
    'נ': 'ן',
    'פ': 'ף',
    'צ': 'ץ'
}

def apply_final_forms(word: str) -> str:
    """Convert medial letters to final forms at end of word."""
    if not word:
        return word

    last_char = word[-1]
    if last_char in FINAL_FORMS:
        return word[:-1] + FINAL_FORMS[last_char]
    return word
```

Apply this to ALL generated variations before returning.

### Issue 3: Hybrid Search Strategy Needed
**Current Approach**: Generate variations, search for exact matches.
**Problem**: Misses valid forms, includes invalid forms.

**Proposed Enhancement**: Two-phase search strategy:

**Phase 1: Pattern-based generation** (current approach)
- Generate ~50-70 core variations using refined patterns
- Search concordance for these specific forms

**Phase 2: String-based discovery** (NEW)
- Do broader substring search on root consonants
- Example: For root "אהב", search concordance for ANY word containing "אהב"
- Filter results through morphological validator
- Validator checks: root consonants present, valid affixes, linguistic plausibility

**Implementation Sketch**:
```python
def hybrid_search(root: str, level: str = 'consonantal') -> List[SearchResult]:
    """Two-phase search: generated variations + discovered forms."""

    # Phase 1: Search generated variations
    variations = generate_variations(root)
    results = search_concordance(variations, level)

    # Phase 2: Discover additional forms
    # Search for any word containing root consonants
    discovered = search_substring(root, level)  # Broader search

    # Filter discovered forms through validator
    validator = MorphologyValidator(root)
    validated = [w for w in discovered if validator.is_plausible(w)]

    # Combine and deduplicate
    return deduplicate(results + validated)

class MorphologyValidator:
    """Validates whether a word is plausibly derived from a root."""

    def is_plausible(self, word: str, root: str) -> bool:
        # Check 1: Root consonants appear in order
        # Check 2: Only valid affixes added
        # Check 3: Length reasonable (root + 0-4 affixes)
        # Check 4: No impossible prefix combinations
        pass
```

## Tasks for This Session

1. **Fix nonsense word generation**:
   - Refactor `_generate_verb_variations()` to use mutually-exclusive pattern sets
   - Test: Ensure no יהָ, יהִת, אה combinations

2. **Fix final letter forms**:
   - Add `apply_final_forms()` function
   - Apply to all generated variations
   - Test: "ברך" + "ו" → "ברכו" (not "ברךו")

3. **Implement hybrid search (foundation)**:
   - Add substring search to concordance_search.py
   - Create MorphologyValidator class stub
   - Document the two-phase strategy

4. **Testing**:
   - Test roots: שמר, אהב, ברך, רעה
   - Verify no nonsense forms
   - Verify final letters correct
   - Compare Phase 1 vs Phase 1+2 recall

5. **Update documentation**:
   - Update DAY_5_ENHANCEMENTS.md with refinements
   - Add entry to IMPLEMENTATION_LOG.md

## Files to Modify

- `src/concordance/morphology_variations.py` (main fixes)
- `src/concordance/search.py` (add substring search)
- `src/concordance/hebrew_text_processor.py` (may need helper functions)
- `docs/DAY_5_ENHANCEMENTS.md` (document refinements)
- `docs/IMPLEMENTATION_LOG.md` (add session entry)

## Success Criteria

✅ No linguistically impossible forms generated
✅ All final letter forms correct
✅ Foundation for hybrid search in place
✅ Test suite demonstrates improvement
✅ Documentation updated

## Reference Materials

- Hebrew final forms: https://en.wikipedia.org/wiki/Hebrew_alphabet
- Verb conjugation patterns: https://en.wikipedia.org/wiki/Hebrew_verb_conjugation
- Current morphology code: src/concordance/morphology_variations.py:1
- Current test output showing issues in terminal history

## Additional Notes

The morphology generator was created as a FOUNDATION. These refinements will:
1. Make it linguistically valid (no nonsense words)
2. Make it orthographically correct (final forms)
3. Add discovery capability (find forms we didn't think to generate)

This brings us closer to 99%+ recall while maintaining precision.
```

## End of Next Session Prompt

Save this file and refer to it when starting the next conversation.
