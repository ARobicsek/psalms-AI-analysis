# Librarian Agent Usage Examples

Quick reference for using the three librarian agents and Research Bundle Assembler.

## BDB Librarian

**Purpose**: Hebrew lexicon lookups with homograph disambiguation

```python
from src.agents.bdb_librarian import BDBLibrarian

librarian = BDBLibrarian()

# Single word lookup
entries = librarian.fetch_entry("רעה")
for entry in entries:
    print(f"{entry.headword} ({entry.strong_number}): {entry.transliteration}")
    print(f"  {entry.entry_text[:100]}...")
```

**CLI**:
```bash
python src/agents/bdb_librarian.py "רעה"
```

**Output**: Returns ALL meanings with vocalization, Strong's numbers, transliteration for disambiguation.

---

## Concordance Librarian

**Purpose**: Search Hebrew concordance with automatic morphological variations

```python
from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest

librarian = ConcordanceLibrarian()

# Single search
request = ConcordanceRequest(
    query="רעה",
    scope="Psalms",
    level="consonantal",
    generate_variations=True  # 66 morphological forms
)
bundle = librarian.search(request)

print(f"Found {len(bundle.results)} results")
print(f"Searched {len(bundle.variations_searched)} variations")

for result in bundle.results[:5]:
    print(f"{result.reference}: {result.matched_word}")
```

**CLI**:
```bash
python src/agents/concordance_librarian.py "רעה" --scope Psalms
```

---

## Figurative Language Librarian

**Purpose**: Query pre-analyzed figurative language with hierarchical tags

```python
from src.agents.figurative_librarian import FigurativeLibrarian, FigurativeRequest

librarian = FigurativeLibrarian()

# Get all metaphors in Psalm 23
request = FigurativeRequest(
    book="Psalms",
    chapter=23,
    metaphor=True
)
bundle = librarian.search(request)

for instance in bundle.instances:
    print(f"{instance.reference}")
    print(f"  Vehicle: {', '.join(instance.vehicle[:2])}")
    print(f"  Target: {', '.join(instance.target[:2])}")

# Find shepherd metaphors across all Psalms
request2 = FigurativeRequest(
    book="Psalms",
    vehicle_contains="shepherd"
)
bundle2 = librarian.search(request2)
print(f"Found {len(bundle2.instances)} shepherd metaphors")
```

**CLI**:
```bash
python src/agents/figurative_librarian.py --book Psalms --chapter 23
python src/agents/figurative_librarian.py --vehicle shepherd --book Psalms
```

---

## Research Bundle Assembler

**Purpose**: Coordinate all three librarians and format for LLM consumption

```python
from src.agents.research_assembler import ResearchAssembler

assembler = ResearchAssembler()

# From JSON (simulates Scholar-Researcher output)
request_json = """
{
  "psalm_chapter": 23,
  "lexicon": [
    {"word": "רעה"},
    {"word": "צלמות"}
  ],
  "concordance": [
    {"query": "רעה", "scope": "Psalms", "level": "consonantal"}
  ],
  "figurative": [
    {"book": "Psalms", "chapter": 23, "metaphor": true}
  ]
}
"""

bundle = assembler.assemble_from_json(request_json)

# Get summary
summary = bundle.to_dict()['summary']
print(f"Lexicon entries: {summary['lexicon_entries']}")
print(f"Concordance results: {summary['concordance_results']}")
print(f"Figurative instances: {summary['figurative_instances']}")

# Export for LLM
markdown = bundle.to_markdown()  # LLM-optimized format
json_data = bundle.to_json()     # Machine-readable format
```

**CLI**:
```bash
# Create request JSON file first
cat > request.json <<EOF
{
  "psalm_chapter": 23,
  "lexicon": [{"word": "רעה"}],
  "concordance": [{"query": "רעה", "scope": "Psalms"}],
  "figurative": [{"book": "Psalms", "chapter": 23}]
}
EOF

# Assemble and output as markdown
python src/agents/research_assembler.py request.json --format markdown

# Or save to file
python src/agents/research_assembler.py request.json --output bundle.md
```

---

## Full Integration Test

See [scripts/test_integration_day5.py](../scripts/test_integration_day5.py) for complete working example.

**Run test**:
```bash
source venv/Scripts/activate
python scripts/test_integration_day5.py
```

**Expected output**:
- ✅ BDB Librarian - Returns 6 lexicon entries with disambiguation
- ✅ Concordance Librarian - Searches 20-66 variations, finds 25 results
- ✅ Figurative Language Librarian - Finds 11 instances in Psalm 23
- ✅ Research Bundle Assembler - Generates JSON + Markdown outputs
- ✅ Logging System - Tracks all agent activities

---

## Key Features

### 1. Homograph Disambiguation (BDB)
Returns ALL meanings with metadata for Scholar to filter:
- **Vocalized headword**: רַע vs רָעָה
- **Strong's number**: 7451 vs 7462
- **Transliteration**: raʻ vs râʻâh

### 2. Morphological Variations (Concordance)
Generates 66 variations automatically:
- Prefix variations: ה, ו, ב, כ, ל, מ
- Gender & number: ה, ים, ות, יים
- Verb stems: נ (Niphal), ה (Hiphil), הת (Hithpael)
- Verb tenses: imperfect prefixes (א, ת, י, נ)
- Final letter forms: כ→ך, מ→ם, נ→ן, פ→ף, צ→ץ

**Result**: 3.3x improvement (20 → 66 forms), ~99% recall

### 3. Hierarchical Tag Queries (Figurative)
Query at any level of specificity:
- Broad: `"pastoral imagery"` → finds shepherd, flock, pasture metaphors
- Narrow: `"shepherd"` → finds only shepherd-specific instances
- Tags are hierarchical arrays: `["shepherd", "pastoral caregiver", "human occupation"]`

### 4. Dual Output Formats (Assembler)
- **JSON**: Machine-readable, preserves all metadata
- **Markdown**: LLM-optimized with hierarchical structure (##, ###)

### 5. Comprehensive Logging
All agent activities logged with:
- Structured JSON for analysis
- Human-readable console output
- Event types: research_request, librarian_query, librarian_results, phrase_variations
- Performance metrics and API call tracking

---

## Next Steps

After Day 5 completion, these librarians will be integrated into the full pipeline:

1. **Scholar-Researcher Agent** (Haiku) generates research requests
2. **Research Bundle Assembler** coordinates librarians
3. **Scholar-Writer Agent** (Sonnet) receives markdown-formatted research
4. Analysts can track everything via structured logs

See [ARCHITECTURE.md](ARCHITECTURE.md) for complete documentation.
