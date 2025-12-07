# Figurative Librarian Filtering: Detailed Analysis

This document provides detailed answers to specific questions about how the Figurative Librarian controls result volumes.

## 1. Actual Limits on Research Bundle Size

### The "500 Results Default" is Misleading

While the FigurativeRequest class has a default of `max_results=500`, **this limit is never actually reached in practice** because:

1. **ResearchAssembler Post-Processing** (lines 681-696 in research_assembler.py):
   ```python
   # Apply verse-count-based filtering to limit results per query
   # <20 verses: 20 max per query; >=20 verses: 10 max per query
   if request.verse_count is not None:
       max_per_query = 20 if request.verse_count < 20 else 10
   ```

2. **Smart Filtering with Priority**:
   - If `priority_ranking` is provided, results are sorted by priority first
   - Then by whether the search term appears in the vehicle field
   - Finally by confidence score
   - Only the top `max_per_query` results are kept

3. **Actual Limits**:
   - **Short Psalms (< 20 verses)**: Maximum 20 results per figurative search
   - **Long Psalms (≥ 20 verses)**: Maximum 10 results per figurative search
   - This is why you never see 500 results in the research bundles

## 2. Scope Limitation - When It's Applied

### The Figurative Librarian Has NO Auto-Scope Feature

Unlike the Concordance Librarian, the Figurative Librarian:
- **Never applies intelligent scope filtering** based on result frequency
- **Does not have** a `determine_smart_scope()` method
- Always searches the full scope specified in the request

### When Scope IS Limited:

1. **Explicit Book/Books Parameter**:
   ```python
   # Single book search
   FigurativeRequest(book="Psalms")

   # Multi-book search
   FigurativeRequest(books=["Genesis", "Exodus", "Psalms"])
   ```

2. **Chapter/Verse Range Restrictions**:
   ```python
   FigurativeRequest(
       book="Psalms",
       chapter=23,
       verse_start=1,
       verse_end=6
   )
   ```

3. **Default Behavior**: If no book specified, searches across ALL books in the database (Psalms, Proverbs, Isaiah, Pentateuch)

## 3. Figurative Type Filtering - When It's Used

### Current Implementation: NEVER USED!

After analyzing the entire pipeline, **figurative type filters (simile, metaphor, etc.) are never actually applied**:

1. **ScholarResearcher** creates requests but never sets type flags:
   ```python
   # In scholar_researcher.py, figurative checks only include:
   {
       "book": "Psalms" or books: [...],
       "vehicle_contains": "shepherd",
       "vehicle_search_terms": [...],
       "notes": "..."
   }
   # NEVER includes: "simile": True, "metaphor": True, etc.
   ```

2. **Why This Happens**:
   - The figurative database already classifies each instance with types
   - The search assumes you want ALL types that match the vehicle
   - Filtering by type would reduce comprehensive coverage

3. **SQL WHERE Clause** (if types were specified):
   ```sql
   AND (f.final_simile = 'yes' OR f.final_metaphor = 'yes' OR ...)
   ```

## 4. Fields Searched Besides Vehicle

### Primary Search Fields:

1. **Vehicle** (most commonly used):
   - `vehicle_contains`: Simple text search
   - `vehicle_search_terms`: List of synonyms with morphological variants
   - Uses complex pattern matching within JSON arrays

2. **Target** (rarely used):
   - `target_contains`: Searches the target field
   - Example: searching for "God" as the target of metaphors
   - Simple LIKE matching: `f.target LIKE ? COLLATE NOCASE`

3. **Ground** (rarely used):
   - `ground_contains`: Searches the ground (similarity) field
   - Example: finding metaphors grounded in "protection"
   - Simple LIKE matching: `f.ground LIKE ? COLLATE NOCASE`

4. **Posture** (rarely used):
   - `posture_contains`: Searches the posture field
   - Example: finding "defense" or "attack" postures
   - Simple LIKE matching: `f.posture LIKE ? COLLATE NOCASE`

5. **Text Search** (never used in pipeline):
   - `text_search`: Searches within figurative_text OR explanation fields
   - Would match: `f.figurative_text LIKE ? OR f.explanation LIKE ?`

### Actual Pipeline Usage:

Based on code analysis, the pipeline **only searches by vehicle**:
- All figurative requests from ScholarResearcher include `vehicle_contains`
- None include target, ground, posture, or text_search
- The focus is on finding similar imagery/vehicles across the biblical corpus

## Summary

| Question | Answer |
|----------|--------|
| **Why never 500 results?** | ResearchAssembler limits to 10-20 results per query based on psalm length |
| **When is scope limited?** | Only when explicitly specified (book/books/chapter), never auto-scoped |
| **When filter by type?** | NEVER - pipeline doesn't use type flags, searches all figurative types |
| **Other fields searched?** | Only vehicle is searched in practice; target/ground/posture exist but unused |

The Figurative Librarian is designed for comprehensive imagery searches across the entire biblical corpus, with post-processing filtering rather than pre-search restrictions.