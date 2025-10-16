# Next Session: Day 5 Final Refinements

**Date**: Next session after 2025-10-16
**Context**: Day 5 (Integration & Documentation) is 95% complete. Four refinements identified from Psalm 27:1 demo before moving to Phase 2 (Scholar agents).

---

## Quick Context

**Current Status**: Phase 1 (Foundation) at 95%

**What's Working**:
- ✅ All 4 librarian agents operational (BDB, Concordance, Figurative, Assembler)
- ✅ Morphological variations generating 66 forms per root (99%+ recall)
- ✅ Homograph disambiguation in BDB (vocalization, Strong's numbers)
- ✅ Comprehensive logging system
- ✅ Integration test passed
- ✅ Complete documentation (ARCHITECTURE.md, LIBRARIAN_USAGE_EXAMPLES.md)
- ✅ **Demo working end-to-end** (Psalm 27:1 - see `tests/output/DEMO_PSALM_27_1.md`)

**What's Needed**: Four refinements identified from real-world usage → Then Phase 1 is 100% complete

---

## Start Next Session With This Prompt

```
I'm continuing work on the Psalms AI commentary pipeline - Day 5 Final Refinements.

I just ran a full demo of all 4 librarian agents on Psalm 27:1. The demo worked beautifully and revealed four specific refinements that would make the system production-ready.

Please read:
1. tests/output/DEMO_SUMMARY.md (demo results + analysis)
2. docs/NEXT_SESSION_REFINEMENTS.md (this file - the 4 refinements)
3. docs/PROJECT_STATUS.md (we're at 95% of Phase 1)

The four refinements are:
1. Figurative Language: Synonym expansion (stronghold → fortress, refuge, etc.)
2. Figurative Language: Complete verse context (full Hebrew + English for every match)
3. Concordance: Phrase search support (מָעוֹז־חַיַּי as phrase, not just מעוז as word)
4. BDB: Usage examples extraction (biblical citations from BDB entries)

Let's implement these four refinements and complete Phase 1!
```

---

## The Four Refinements

### Refinement 1: Figurative Language - Synonym Expansion

**Current Behavior**:
```python
request = FigurativeRequest(vehicle_contains="stronghold")
# Searches only: "stronghold" in vehicle hierarchy
# Misses: "fortress", "refuge", "citadel" metaphors with same meaning
```

**Desired Behavior**:
```python
request = FigurativeRequest(vehicle_contains="stronghold")
# Searches: "stronghold", "fortress", "refuge", "citadel", "fortification", "rampart", "bulwark"
# Finds ALL military protection metaphors, not just exact word match
```

**Implementation**:

Add synonym dictionary to `src/agents/figurative_librarian.py`:

```python
VEHICLE_SYNONYMS = {
    "stronghold": ["stronghold", "fortress", "refuge", "citadel", "fortification", "rampart", "bulwark", "tower", "bastion"],
    "shepherd": ["shepherd", "pastor", "pastoral caregiver", "herder", "guide"],
    "light": ["light", "illumination", "lamp", "sun", "fire", "torch", "brightness"],
    "rock": ["rock", "stone", "cliff", "crag", "boulder"],
    "shield": ["shield", "buckler", "protection", "defense", "guard"],
    "water": ["water", "river", "stream", "fountain", "spring", "well"],
    "king": ["king", "ruler", "sovereign", "monarch"],
    "warrior": ["warrior", "soldier", "fighter", "champion"],
    "father": ["father", "parent", "progenitor"],
    "mother": ["mother", "parent", "nurturer"],
    # Add more as needed
}
```

Update `_build_query()` method:
```python
def _expand_search_terms(self, term: str) -> List[str]:
    """Expand search term to include synonyms."""
    if term.lower() in VEHICLE_SYNONYMS:
        return VEHICLE_SYNONYMS[term.lower()]
    return [term]

# Then in _build_query():
if self.vehicle_contains:
    search_terms = self._expand_search_terms(self.vehicle_contains)
    # Build query with OR logic for all terms
```

**Test**:
```python
request = FigurativeRequest(vehicle_contains="stronghold")
bundle = librarian.search(request)
# Should return 20+ instances (not just 13) including "fortress", "refuge", etc.
```

**Files**:
- `src/agents/figurative_librarian.py` (add synonyms + expansion logic)
- `docs/ARCHITECTURE.md` (document feature)

---

### Refinement 2: Figurative Language - Complete Verse Context

**Current Behavior**:
```python
FigurativeInstance(
    reference="Psalms 27:1",
    figurative_text="The LORD is the stronghold of my life",  # Snippet only
    vehicle=["defensive fortification"],
    target=["divine protection"]
)
```

**Desired Behavior**:
```python
FigurativeInstance(
    reference="Psalms 27:1",
    figurative_text="The LORD is the stronghold of my life",
    hebrew_verse="יְהֹוָה ׀ אוֹרִי וְיִשְׁעִי מִמִּי אִירָא יְהֹוָה מָעוֹז־חַיַּי מִמִּי אֶפְחָד׃",  # FULL
    english_verse="The LORD is my light and my salvation; whom shall I fear? The LORD is the stronghold of my life; of whom shall I be afraid?",  # FULL
    vehicle=["defensive fortification"],
    target=["divine protection"]
)
```

**Implementation**:

The figurative language database already has `hebrew_text` and `english_text` columns. Ensure these are always populated and renamed for clarity:

```python
@dataclass
class FigurativeInstance:
    reference: str
    figurative_text: str  # Keep snippet for highlighting
    hebrew_verse: str  # NEW: Full verse Hebrew
    english_verse: str  # NEW: Full verse English
    vehicle: Optional[List[str]]
    target: Optional[List[str]]
    ground: Optional[List[str]]
    # ... other fields
```

Update `search()` method to ensure full verses are fetched from database.

Update `to_markdown()` in ResearchAssembler to display full verses:
```markdown
### Instance 1: Psalms 27:1
**Type**: metaphor
**Figurative phrase**: "The LORD is the stronghold of my life"

**Hebrew**: יְהֹוָה ׀ אוֹרִי וְיִשְׁעִי מִמִּי אִירָא יְהֹוָה מָעוֹז־חַיַּי מִמִּי אֶפְחָד׃
**English**: The LORD is my light and my salvation; whom shall I fear? The LORD is the stronghold of my life; of whom shall I be afraid?

**Vehicle**: defensive fortification, military fortress
**Target**: divine protection, God's protective nature
```

**Files**:
- `src/agents/figurative_librarian.py` (update dataclass + query)
- `src/agents/research_assembler.py` (update markdown formatter)
- `docs/ARCHITECTURE.md` (document full verse inclusion)

---

### Refinement 3: Concordance - Phrase Search Support

**Current Behavior**:
```python
request = ConcordanceRequest(query="מעוז חיי")
# Treats as single word (removes space/maqqef)
# Searches only: מעוזחיי (nonsense)
# FAILS to find phrase "מעוז־חיי" in Ps 27:1
```

**Desired Behavior**:
```python
request = ConcordanceRequest(query="מעוז חיי")
# Detects 2-word phrase
# Searches for sequential words: "מעוז" at position N, "חיי" at position N+1
# Applies variations to each word: (מעוז, במעוז, ומעוז) × (חיי, חייך, חיים)
# Finds: "מָעוֹז־חַיַּי" in Psalm 27:1
```

**Implementation Strategy**:

**Phase 1**: Simple sequential matching (no variations)
```python
def is_phrase(query: str) -> bool:
    """Check if query contains multiple words."""
    return ' ' in query or '־' in query

def search_phrase(phrase: str, scope: str, level: str) -> List[SearchResult]:
    """Search for multi-word phrase."""
    words = phrase.replace('־', ' ').split()

    # Search for first word
    first_word_results = search_word(words[0], scope, level)

    # Filter to results where subsequent words appear at N+1, N+2, etc.
    phrase_results = []
    for result in first_word_results:
        if _check_words_sequential(result, words[1:]):
            phrase_results.append(result)

    return phrase_results
```

**Phase 2** (Optional): Phrase variations
```python
# Generate variations for each word
word1_vars = generate_variations(words[0])  # 20 variations
word2_vars = generate_variations(words[1])  # 20 variations

# Combine: 20 × 20 = 400 phrase variations (expensive!)
# Alternative: Only vary prefixes on first word (reduces to 20 total)
```

**Recommendation**: Implement Phase 1 first (exact phrase match), add Phase 2 if needed.

**Test**:
```python
request = ConcordanceRequest(query="מעוז חיי")
bundle = librarian.search_with_variations(request)
# Should find Psalm 27:1: "מָעוֹז־חַיַּי"
```

**Files**:
- `src/concordance/search.py` (add `search_phrase()` method)
- `src/agents/concordance_librarian.py` (detect and route phrases)
- `docs/ARCHITECTURE.md` (document phrase search)

---

### Refinement 4: BDB - Usage Examples Extraction

**Current Behavior**:
```python
LexiconEntry(
    word="מעוז",
    entry_text="place or means of safety, protection, refuge, stronghold..."
    # No usage examples
)
```

**Desired Behavior**:
```python
LexiconEntry(
    word="מעוז",
    entry_text="place or means of safety, protection, refuge, stronghold...",
    usage_examples=[
        "Judges 6:26",
        "Isaiah 25:4",
        "Psalms 27:1",
        "Psalms 28:8"
    ]  # Biblical citations from BDB
)
```

**Implementation**:

**Step 1**: Investigate Sefaria API response
```python
# Check if /api/words/מעוז returns citations in structured format
response = requests.get("https://www.sefaria.org/api/words/מעוז")
data = response.json()
# Look for citation fields
```

**Step 2**: If not structured, extract with regex
```python
BIBLICAL_REFERENCE_PATTERN = re.compile(
    r'\b([1-3]?\s?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(\d+):(\d+)(?:-(\d+))?\b'
)

def extract_citations(entry_text: str) -> List[str]:
    """Extract biblical references from BDB entry text."""
    matches = BIBLICAL_REFERENCE_PATTERN.findall(entry_text)
    citations = [f"{book} {chapter}:{verse}" for book, chapter, verse, _ in matches]
    return citations

# Examples it matches:
# "Judges 6:26", "1 Samuel 15:29", "Isaiah 25:4", "Ps 27:1", "Psalms 27:1-3"
```

**Step 3**: Add field to LexiconEntry
```python
@dataclass
class LexiconEntry:
    word: str
    lexicon_name: str
    entry_text: str
    headword: Optional[str] = None
    strong_number: Optional[str] = None
    transliteration: Optional[str] = None
    usage_examples: Optional[List[str]] = None  # NEW
```

**Step 4**: Update BDB Librarian to populate
```python
def fetch_entry(self, word: str) -> List[LexiconEntry]:
    entries = self.client.fetch_lexicon_entry(word)

    for entry in entries:
        # Extract citations
        entry.usage_examples = extract_citations(entry.entry_text)

    return entries
```

**Test**:
```python
entries = bdb.fetch_entry("מעוז")
print(entries[0].usage_examples)
# Output: ["Judges 6:26", "Isaiah 25:4", "Psalms 27:1", ...]
```

**Files**:
- `src/data_sources/sefaria_client.py` (add citation extractor)
- `src/agents/bdb_librarian.py` (populate usage_examples)
- `docs/ARCHITECTURE.md` (document usage examples)

---

## Implementation Checklist

**Estimated time**: 2-3 hours total

- [ ] **Refinement 1**: Synonym expansion (~30 min)
  - [ ] Add `VEHICLE_SYNONYMS` dictionary
  - [ ] Implement `_expand_search_terms()` method
  - [ ] Update query builder to use synonyms
  - [ ] Test with "stronghold" → finds "fortress", "refuge"

- [ ] **Refinement 2**: Full verse context (~30 min)
  - [ ] Update `FigurativeInstance` dataclass
  - [ ] Ensure database query fetches full verses
  - [ ] Update markdown formatter to display verses
  - [ ] Test all instances include complete context

- [ ] **Refinement 3**: Phrase search (~60 min)
  - [ ] Add `is_phrase()` helper
  - [ ] Implement `search_phrase()` in search.py
  - [ ] Add `_check_words_sequential()` validator
  - [ ] Update concordance librarian to detect phrases
  - [ ] Test with "מעוז חיי" → finds Psalm 27:1

- [ ] **Refinement 4**: Usage examples (~30 min)
  - [ ] Investigate Sefaria API citation structure
  - [ ] Implement `extract_citations()` with regex
  - [ ] Add `usage_examples` field to LexiconEntry
  - [ ] Update BDB Librarian to populate field
  - [ ] Test with "מעוז", "אור", "ישע"

- [ ] **Integration & Testing** (~30 min)
  - [ ] Run full integration test with all refinements
  - [ ] Re-run Psalm 27:1 demo to verify improvements
  - [ ] Update ARCHITECTURE.md with refinements
  - [ ] Update IMPLEMENTATION_LOG.md

- [ ] **Git Commit**
  - [ ] Commit: "Day 5 Final Refinements: Synonyms, Phrases, Examples, Full Verses"
  - [ ] Push to origin

---

## Expected Outcomes

After implementing these refinements:

### Before Refinements:
- **Figurative search**: 13 "stronghold" instances (exact word only)
- **Concordance search**: Single words only, no phrases
- **BDB entries**: Definitions only, no usage examples
- **Figurative context**: Snippet only, no full verse

### After Refinements:
- **Figurative search**: 20+ instances (stronghold + fortress + refuge + citadel...)
- **Concordance search**: "מעוז חיי" finds Psalm 27:1 phrase
- **BDB entries**: Includes biblical citations (Judges 6:26, Isaiah 25:4, etc.)
- **Figurative context**: Full Hebrew + English verse for every instance

---

## Phase 1 Completion

Once these refinements are complete:
- ✅ Phase 1 (Foundation) is **100% complete**
- ✅ All librarian infrastructure **production-ready**
- ✅ Ready to begin **Phase 2: Scholar Agents**

**Phase 2 Preview**: Scholar-Researcher agent (generates research requests) + Scholar-Writer agents (Pass 1-3)

---

## Files Modified

**Will modify**:
- `src/agents/figurative_librarian.py` (synonyms + full verses)
- `src/agents/concordance_librarian.py` (phrase detection)
- `src/agents/bdb_librarian.py` (usage examples)
- `src/concordance/search.py` (phrase search logic)
- `src/data_sources/sefaria_client.py` (citation extraction)
- `src/agents/research_assembler.py` (markdown formatter)
- `docs/ARCHITECTURE.md` (documentation)
- `docs/IMPLEMENTATION_LOG.md` (session summary)

---

## Quick Start Commands

```bash
# Activate environment
cd /c/Users/ariro/OneDrive/Documents/Psalms
source venv/Scripts/activate

# Current demo (before refinements)
python scripts/demo_psalm_27_1.py

# After implementing refinements, run again to see improvements
python scripts/demo_psalm_27_1.py > tests/output/DEMO_AFTER_REFINEMENTS.md

# Compare before/after
diff tests/output/DEMO_PSALM_27_1.md tests/output/DEMO_AFTER_REFINEMENTS.md
```

---

## Success Criteria

**Refinements complete when**:
1. ✅ "stronghold" search finds 20+ instances (not 13)
2. ✅ "מעוז חיי" phrase search finds Psalm 27:1
3. ✅ BDB entries include biblical citations
4. ✅ Figurative instances include full Hebrew + English verses
5. ✅ Integration test passes
6. ✅ Demo shows all improvements
7. ✅ Documentation updated

**Then**: Phase 1 is 100% complete, Phase 2 (Scholar agents) can begin! 🚀

---

## Notes

- These are **enhancements**, not fixes - system already works
- Each refinement is independent - can implement in any order
- Estimated 2-3 hours total for all four
- All refinements are straightforward (no complex algorithms)
- Foundation is solid, this is polish to make it excellent

**Let's finish Phase 1 strong!**
