# System Architecture - Psalms AI Commentary Pipeline

## Overview
This document provides technical specifications for the Psalms AI commentary generation system. It includes database schemas, API integration patterns, agent architectures, and implementation details.

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Data Sources](#data-sources)
3. [Database Schemas](#database-schemas)
4. [Hebrew Search System](#hebrew-search-system)
5. [Agent Architecture](#agent-architecture)
6. [API Integrations](#api-integrations)
7. [Output Generation](#output-generation)
8. [Cost & Performance](#cost--performance)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      PSALMS COMMENTARY                       │
│                      GENERATION PIPELINE                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   PASS 1: MACRO ANALYSIS      │
              │   (Claude Sonnet 4.5)         │
              │   Input: Chapter text only    │
              │   Output: Thesis + Structure  │
              └───────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   SCHOLAR-RESEARCHER AGENT    │
              │   (Claude Haiku 4.5)          │
              │   Output: Research requests   │
              └───────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────┴─────────────────────┐
        │              LIBRARIAN AGENTS              │
        │            (Python Scripts)                │
        ├────────────────┬──────────────┬───────────┤
        │  BDB Lexicon   │ Concordance  │ Figurative│
        │   (Sefaria)    │   (Local DB) │  Language │
        └────────────────┴──────────────┴───────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   PASS 2: MICRO ANALYSIS      │
              │   (Claude Sonnet 4.5)         │
              │   Input: Research bundle      │
              │   Output: Verse commentary    │
              └───────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   PASS 3: SYNTHESIS           │
              │   (Claude Sonnet 4.5)         │
              │   Output: Final essay         │
              └───────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   CRITIC AGENT                │
              │   (Claude Haiku 4.5)          │
              │   Output: Quality feedback    │
              └───────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   REVISION                    │
              │   (Claude Sonnet 4.5)         │
              │   Output: Final commentary    │
              └───────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────┴─────────────────────┐
        │            OUTPUT GENERATION               │
        ├────────────────┬──────────────────────────┤
        │ SQLite Storage │ Word Document (.docx)    │
        └────────────────┴──────────────────────────┘
```

### Technology Stack
- **Language**: Python 3.13+
- **AI Models**: Anthropic Claude (Sonnet 4.5, Haiku 4.5)
- **Database**: SQLite 3
- **APIs**: Sefaria (biblical texts, lexicon)
- **Document Generation**: python-docx
- **Version Control**: Git + GitHub

---

## Data Sources

### 1. Sefaria API
**Base URL**: `https://www.sefaria.org/api/`
**Authentication**: None required
**Rate Limits**: ~1 request/second (self-imposed)

**Endpoints Used**:
- Text retrieval: `/texts/Psalms.{chapter}`
- Lexicon lookup: `/words/{hebrew_word}`
- Related texts: `/related/{ref}`

### 2. Existing Figurative Language Database
**Location**: `C:\Users\ariro\OneDrive\Documents\Bible\database\Pentateuch_Psalms_fig_language.db`
**Content**: 2,863 pre-analyzed figurative instances in Psalms
**Tables**:
- `verses`: Hebrew text, English translation, metadata
- `figurative_language`: Classified instances with target/vehicle/ground

### 3. Divine Name Modification Rules
**Location**: `C:\Users\ariro\OneDrive\Documents\Bible\docs\NON_SACRED_HEBREW.md`
**Purpose**: Traditional Jewish text modifications for study
**Rules**: Tetragrammaton → ה׳, Elohim family (ה→ק), etc.

---

## Database Schemas

### Hebrew Concordance Database
**File**: `database/hebrew_concordance.db`

```sql
-- Main concordance table
CREATE TABLE hebrew_concordance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book TEXT NOT NULL,                 -- e.g., "Psalms"
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    word_position INTEGER NOT NULL,     -- Position in verse (1-indexed)

    -- Original text (preserved for display)
    word_full TEXT NOT NULL,            -- שֹׁמְרִ֥ים (with vowels + cantillation)

    -- Normalized versions for 4-layer search
    word_vowels_only TEXT NOT NULL,     -- שֹׁמְרִים (vowels, no cantillation)
    word_consonants_only TEXT NOT NULL, -- שמרים (consonants only)
    word_root TEXT,                     -- שמר (triconsonantal root, if identifiable)

    -- Linguistic metadata (optional, for lemma-based search)
    strongs_number TEXT,                -- e.g., "H8104" (if available)
    lemma TEXT,                         -- e.g., "שָׁמַר" (dictionary form)
    morphology TEXT,                    -- e.g., "Verb.Qal.Participle.M.Pl"

    -- English reference (for debugging/display)
    gloss TEXT,                         -- e.g., "keeping, guarding"

    -- Indexes for fast searching
    UNIQUE(book, chapter, verse, word_position)
);

-- Indexes for 4-layer search
CREATE INDEX idx_consonants ON hebrew_concordance(word_consonants_only, book);
CREATE INDEX idx_vowels ON hebrew_concordance(word_vowels_only, book);
CREATE INDEX idx_full ON hebrew_concordance(word_full, book);
CREATE INDEX idx_root ON hebrew_concordance(word_root, book);
CREATE INDEX idx_lemma ON hebrew_concordance(lemma, book);
CREATE INDEX idx_reference ON hebrew_concordance(book, chapter, verse);

-- Collocation tracking (words appearing near each other)
CREATE TABLE collocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word1_root TEXT NOT NULL,
    word2_root TEXT NOT NULL,
    distance INTEGER NOT NULL,          -- Words apart (1 = adjacent)
    book TEXT NOT NULL,
    occurrences INTEGER DEFAULT 1,
    UNIQUE(word1_root, word2_root, distance, book)
);

CREATE INDEX idx_collocation_lookup ON collocations(word1_root, word2_root, book);
```

### Commentary Output Database
**File**: `database/psalms_commentary.db`

```sql
-- Chapter-level analysis
CREATE TABLE chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    psalm_number INTEGER NOT NULL UNIQUE,

    -- Three-pass outputs
    macro_overview TEXT NOT NULL,       -- Pass 1: Thesis + structure
    micro_analysis TEXT NOT NULL,       -- Pass 2: Verse notes
    synthesis_essay TEXT NOT NULL,      -- Pass 3: Final essay

    -- Supporting data
    research_bundle TEXT,               -- JSON: All research data
    critic_feedback TEXT,               -- Critic's assessment
    revision_notes TEXT,                -- Changes made in revision

    -- Metadata
    processing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    token_count_input INTEGER,          -- Total input tokens used
    token_count_output INTEGER,         -- Total output tokens used
    cost_total REAL,                    -- Cost in USD

    -- Quality metrics
    quality_score_telescopic REAL,      -- How well macro/micro integrated
    quality_score_novelty REAL,         -- Insight beyond surface reading
    quality_score_support REAL,         -- Textual evidence for claims

    -- Processing time
    processing_time_seconds INTEGER
);

-- Verse-level commentary
CREATE TABLE verses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id INTEGER NOT NULL,
    verse_number INTEGER NOT NULL,

    -- Text
    hebrew_text TEXT NOT NULL,
    hebrew_text_non_sacred TEXT NOT NULL,  -- With divine name modifications
    english_text TEXT NOT NULL,

    -- Analysis
    commentary TEXT NOT NULL,            -- Verse-specific commentary
    poetic_devices TEXT,                 -- JSON: parallelism, wordplay, etc.
    figurative_language TEXT,            -- JSON: metaphors, similes, etc.
    key_words TEXT,                      -- JSON: significant Hebrew words

    -- Connection to chapter thesis
    thesis_connection TEXT,              -- How this verse advances argument

    FOREIGN KEY (chapter_id) REFERENCES chapters(id),
    UNIQUE(chapter_id, verse_number)
);

CREATE INDEX idx_chapter_verses ON verses(chapter_id);
CREATE INDEX idx_psalm_reference ON verses(chapter_id, verse_number);

-- Research requests log (for debugging/analysis)
CREATE TABLE research_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id INTEGER NOT NULL,
    request_type TEXT NOT NULL,         -- 'bdb', 'concordance', 'figurative'
    query TEXT NOT NULL,                -- What was requested
    response_summary TEXT,              -- Brief summary of response
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id)
);

-- Cost tracking
CREATE TABLE cost_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id INTEGER,
    agent_name TEXT NOT NULL,           -- 'macro', 'researcher', 'micro', etc.
    model_used TEXT NOT NULL,           -- 'claude-sonnet-4.5', 'claude-haiku-4.5'
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_usd REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id)
);

CREATE INDEX idx_cost_by_chapter ON cost_log(chapter_id);
CREATE INDEX idx_cost_by_model ON cost_log(model_used);
```

---

## Hebrew Search System

### Text Normalization Functions

```python
import re
from typing import Literal, Optional

# Unicode ranges for Hebrew
HEBREW_LETTERS = r'[\u05D0-\u05EA]'
HEBREW_VOWELS = r'[\u05B0-\u05BC\u05C7]'
HEBREW_CANTILLATION = r'[\u0591-\u05C7]'
MAQQEF = '\u05BE'  # Hebrew hyphen

def normalize_hebrew(
    text: str,
    level: Literal['exact', 'voweled', 'consonantal', 'root'] = 'consonantal'
) -> str:
    """
    Normalize Hebrew text for search.

    Args:
        text: Hebrew text to normalize
        level: Normalization level
            - 'exact': No normalization (preserve all diacritics)
            - 'voweled': Remove cantillation, keep vowels
            - 'consonantal': Remove all diacritics (consonants only)
            - 'root': Extract triconsonantal root (basic implementation)

    Returns:
        Normalized Hebrew string
    """
    if level == 'exact':
        return text

    # Remove cantillation marks
    text = re.sub(HEBREW_CANTILLATION, '', text)

    if level == 'voweled':
        return text

    # Remove vowel points
    text = re.sub(HEBREW_VOWELS, '', text)

    if level == 'consonantal':
        return text

    if level == 'root':
        # Basic root extraction (remove prefixes/suffixes)
        # TODO: Implement proper morphological analysis
        # For now, just return consonants
        return text

    raise ValueError(f"Unknown normalization level: {level}")

def strip_cantillation(text: str) -> str:
    """Remove cantillation marks only."""
    return re.sub(HEBREW_CANTILLATION, '', text)

def strip_vowels(text: str) -> str:
    """Remove vowel points and cantillation."""
    text = strip_cantillation(text)
    return re.sub(HEBREW_VOWELS, '', text)
```

### Search API

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SearchResult:
    """Single concordance search result."""
    reference: str          # e.g., "Psalms 23:1"
    book: str
    chapter: int
    verse: int
    word_position: int
    word_full: str          # Original word with diacritics
    word_normalized: str    # How it was matched
    context_before: str     # 3 words before
    context_after: str      # 3 words after
    gloss: Optional[str]    # English meaning

@dataclass
class ConcordanceResults:
    """Complete concordance search results."""
    query: str
    search_level: str       # 'consonantal', 'voweled', 'exact', 'lemma'
    scope: str              # 'Psalms', 'entire_tanakh', etc.
    matches: List[SearchResult]
    total_count: int
    unique_verses: int
    collocations: List[tuple[str, int]]  # (word, frequency)

def search_concordance(
    query: str,
    level: Literal['consonantal', 'voweled', 'exact', 'lemma'] = 'consonantal',
    scope: str = 'Psalms',
    limit: Optional[int] = None
) -> ConcordanceResults:
    """
    Search Hebrew concordance.

    Args:
        query: Hebrew word/root to search
        level: Search precision level
        scope: Book to search in ('Psalms', 'entire_tanakh', etc.)
        limit: Maximum results to return

    Returns:
        ConcordanceResults object with all matches
    """
    # Implementation will be in src/concordance/search.py
    pass
```

---

## Agent Architecture

### Overview

The system employs a hybrid agent architecture:
- **AI Agents**: Claude Sonnet/Haiku for analysis, research coordination, critique
- **Python Librarians**: Deterministic data retrieval agents (no LLM calls)

This design minimizes cost while maintaining quality through strategic AI deployment.

### Librarian Agents (Python-Based)

All librarian agents are **pure Python scripts** - no LLM calls. They retrieve data deterministically and return structured results.

#### 1. BDB Librarian

**Purpose**: Scholarly Hebrew lexicon lookups via Sefaria API

**Module**: `src/agents/bdb_librarian.py`

**Lexicon Sources** (default: "scholarly"):
- **BDB Dictionary** (Brown-Driver-Briggs): Full scholarly entry with extensive semantic ranges, parallel words, usage contexts (avg. 1000+ characters per entry)
- **Klein Dictionary**: Etymology, linguistic notes, cognates, derivatives

**Note**: Excludes "BDB Augmented Strong" (concise version) in favor of full BDB Dictionary for maximum scholarly richness.

**Capabilities**:
- **Semantic depth**: Full BDB definitions with morphological forms, parallel terminology (‖ עָנִי, ‖ דַּל), semantic ranges
- **Etymology**: Klein provides root connections, Ugaritic/Egyptian cognates, historical linguistics
- **Homograph disambiguation**: Returns vocalization, Strong's numbers, transliteration for multiple meanings
- **Clean HTML stripping**: Converts Sefaria's HTML markup to scholar-ready clean text
- **Division of labor**: NO biblical usage examples (Concordance Librarian's responsibility)

**Data Structure**:
```python
@dataclass
class LexiconEntry:
    word: str                           # אֶבְיוֹן (consonantal)
    lexicon_name: str                   # "BDB Dictionary" or "Klein Dictionary"
    entry_text: str                     # Full definition (HTML-stripped)
    # Disambiguation metadata for homographs
    headword: Optional[str]             # אֶבְיוֹן (vocalized)
    strong_number: Optional[str]        # "34"
    transliteration: Optional[str]      # "ʼebyôwn"
    morphology: Optional[str]           # "adj.", "m.n.", "v.", etc.
    # Klein-specific fields
    etymology_notes: Optional[str]      # "[Prob. from אבה meaning 'desirous'...]"
    derivatives: Optional[str]          # "Derivative: אבין"
```

**Example Output** (אֶבְיוֹן "poor, needy"):

*Klein Dictionary*:
- Definition: "needy, poor."
- Morphology: m.n.
- Etymology: "[Prob. from אבה and orig. meaning 'desirous, longing, yearning'. cp. Ugar. 'bjn. Late Egypt. and Coptic ebiēn are borrowed from Hebrew.]"
- Derivatives: "Derivative: אבין."

*BDB Dictionary*:
- Entry: "adj. in want, needy, poor,—so, always abs., Dt 15:4 + 40 times; אֶבְיֹנְךָ Ex 23:6 Dt 15:11; אֶבְיוֹנִים Am 4:1 + 14 times... needy, chiefly poor (in material things); as adj. Dt 15:7(×2), 9; 24:14 ψ 109:16 (both ‖ עָנִי); subj. to oppression & abuse Am 2:6; 5:12 (both ‖ צַדִּיק)... cared for by God Je 20:13 ψ 107:41; 132:15 Jb 5:15; 1 S 2:8 = ψ 113:7... [1247 characters total]"

**Usage**:
```python
from src.agents.bdb_librarian import BDBLibrarian

librarian = BDBLibrarian()

# Default: scholarly lexicons (BDB Dictionary + Klein)
entries = librarian.fetch_entry("אֶבְיוֹן")  # Returns 2-3 entries

# Specific lexicon
entries = librarian.fetch_entry("אֶבְיוֹן", lexicon="BDB Dictionary")
```

**CLI**:
```bash
python src/agents/bdb_librarian.py אֶבְיוֹן
```

---

#### 2. Concordance Librarian

**Purpose**: Search Hebrew concordance with automatic morphological variation generation

**Module**: `src/agents/concordance_librarian.py`

**Capabilities**:
- 4-layer Hebrew search (consonantal, voweled, exact, lemma)
- **Automatic phrase variation generation**:
  - Prefix variations: ה, ו, ב, כ, ל, מ (20 combinations)
  - **Morphological variations**: gender, number, verb stems, tenses (66 total forms)
- Phrase search (multi-word Hebrew expressions)
- Scope filtering (Torah, Prophets, Writings, specific books)
- **Hybrid search strategy**: exact + substring discovery with validation

**Morphological Variations**:
```
Root: שמר (guard/keep)
Generated: 66 variations including:
- Noun forms: שמרה, שמרו, שמרים, שמרי, שמרך
- Verb forms: ישמר, תשמר, נשמר (imperfect)
- Verb stems: נשמר (Niphal), הִשמר (Hiphil), התשמר (Hithpael)
- Final forms: ברך (root) → ברך (final ך at end)

Improvement: 3.3x more forms (20 → 66)
Estimated recall: 99%+ of relevant occurrences
```

**Search Strategy**:
```python
# Phase 1: Pattern-based exact search
variations = generate_morphological_variations("שמר")  # 66 forms
results_exact = search_each_variation(variations)

# Phase 2: Substring discovery (optional)
results_substring = search_substring("%שמר%")
validated = filter_through_validator(results_substring)

# Combine
all_results = deduplicate(results_exact + validated)
```

**Data Structure**:
```python
@dataclass
class ConcordanceBundle:
    query: str                      # Original search term
    scope: str                      # "Psalms", "Torah", etc.
    level: str                      # "consonantal", "voweled", "exact"
    variations_searched: List[str]  # All forms searched
    results: List[SearchResult]     # Matches found
    total_matches: int
    unique_verses: int
```

**Usage**:
```python
from src.agents.concordance_librarian import ConcordanceLibrarian

librarian = ConcordanceLibrarian()
bundle = librarian.search_with_variations(
    query="רעה",
    scope="Psalms",
    level="consonantal",
    generate_variations=True  # Enable morphology
)
```

**CLI**:
```bash
python src/agents/concordance_librarian.py "רעה" --scope Psalms
```

---

#### 3. Figurative Language Librarian

**Purpose**: Query pre-analyzed figurative language database

**Module**: `src/agents/figurative_librarian.py`

**Database**: `C:\Users\ariro\OneDrive\Documents\Bible\database\Pentateuch_Psalms_fig_language.db`
- 8,373 verses analyzed
- 5,865 figurative instances
- 2,863+ instances in Psalms

**Capabilities**:
- **Hierarchical tag queries**: Target/Vehicle/Ground/Posture
- Verse-level queries (get all metaphors in Psalm 23)
- Tag-based queries (find all "shepherd" vehicles)
- Combined queries (shepherd metaphors in Psalms 20-30)

**Hierarchical Tag System**:
```json
{
  "target": ["Sun's governing role", "celestial body's function", "cosmic ordering"],
  "vehicle": ["Human ruler's dominion", "conscious governance", "authoritative control"],
  "ground": ["Defining influence", "functional control"]
}
```

Query `"shepherd"` matches hierarchies like:
- `["shepherd", "pastoral caregiver", "human occupation"]`
- `["shepherd's tools", "pastoral implements"]`

**Data Structure**:
```python
@dataclass
class FigurativeInstance:
    book: str
    chapter: int
    verse: int
    hebrew_text: str
    english_text: str
    final_metaphor: str           # "yes", "no", "borderline"
    target: Optional[List[str]]   # Hierarchical tags
    vehicle: Optional[List[str]]
    ground: Optional[List[str]]
    posture: Optional[str]
    deliberation: str             # AI reasoning
```

**Usage**:
```python
from src.agents.figurative_librarian import FigurativeLibrarian

librarian = FigurativeLibrarian()

# Get all metaphors in Psalm 23
instances = librarian.fetch_by_verse("Psalms", 23)

# Find shepherd metaphors across all Psalms
instances = librarian.fetch_by_vehicle("shepherd", book="Psalms")
```

**CLI**:
```bash
python src/agents/figurative_librarian.py --book Psalms --chapter 23
python src/agents/figurative_librarian.py --vehicle shepherd --book Psalms
```

---

#### 4. Research Bundle Assembler

**Purpose**: Coordinate all three librarians and format results for LLM consumption

**Module**: `src/agents/research_assembler.py`

**Input**: Research request JSON from Scholar-Researcher agent
```json
{
  "psalm_chapter": 23,
  "lexicon": [{"word": "רעה"}],
  "concordance": [{"query": "רעה", "scope": "Psalms", "level": "consonantal"}],
  "figurative": [
    {"book": "Psalms", "chapter": 23, "metaphor": true},
    {"vehicle_contains": "shepherd"}
  ]
}
```

**Output**: Dual format
1. **JSON**: Machine-readable, preserves all metadata
2. **Markdown**: LLM-optimized, hierarchical structure

**Markdown Format**:
```markdown
# Research Bundle for Psalm 23

## Hebrew Lexicon Entries (BDB)

### רעה
**Lexicon**: BDB Augmented Strong
**Strong's**: 7462
**Transliteration**: râʻâh
**Vocalized**: רָעָה

**Definition**:
to pasture, tend, graze, feed
  to tend, pasture
    to shepherd
    of ruler, teacher (fig)
...

## Concordance Searches

### Search 1: רעה (Psalms, consonantal)
**Variations searched**: 66 forms
**Total results**: 15
**Unique verses**: 12

**Psalms 23:1**
Hebrew: יְהֹוָ֥ה רֹ֝עִ֗י לֹ֣א אֶחְסָֽר
English: The LORD is my shepherd, I shall not want
Matched: *רֹ֝עִ֗י* (position 2)

...

## Figurative Language Instances

### Instance 1: Psalms 23:1
**Type**: Metaphor
**Target**: Divine care and provision
**Vehicle**: Shepherd's care for flock
**Ground**: Protective guidance, sustenance provision

...
```

**Benefits of Markdown**:
- Hierarchical structure (##, ###) aids LLM navigation
- Bold/italic highlights key information
- More compact than JSON for same content
- Natural language flow for AI analysis

**Usage**:
```python
from src.agents.research_assembler import ResearchAssembler

assembler = ResearchAssembler()

# Process research request
bundle = assembler.assemble(research_request_json)

# Generate markdown for LLM
markdown = bundle.to_markdown()
```

---

### Logging System

**Purpose**: Complete observability of agent activities for debugging and metrics

**Module**: `src/utils/logger.py`

**Features**:
- **Dual output format**: Human-readable console + machine-readable JSON
- **Timestamped log files**: `logs/{agent_name}_{timestamp}.log` + `.json`
- **Configurable levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Event types**: research_request, librarian_query, librarian_results, phrase_variations, performance_metric, api_call, error_detail

**Specialized Methods**:
```python
from src.utils import get_logger

logger = get_logger('concordance_librarian')

# Log research request
logger.log_research_request(
    psalm_chapter=23,
    request_json={"concordance": [{"query": "רעה"}]}
)

# Log librarian query
logger.log_librarian_query(
    librarian_type='concordance',
    query='רעה',
    params={'scope': 'Psalms', 'level': 'consonantal'}
)

# Log results
logger.log_librarian_results(
    librarian_type='concordance',
    query='רעה',
    result_count=15,
    sample_results=[{'reference': 'Psalms 23:1'}]
)

# Log phrase variations
logger.log_phrase_variations(
    original='רעה',
    variations=['רעה', 'הרעה', 'ורעה', ...],
    count=66
)

# Log performance
logger.log_performance_metric(
    operation='concordance_search',
    duration_ms=127,
    metadata={'variations': 66, 'results': 15}
)

# Log API calls
logger.log_api_call(
    api_name='Sefaria',
    endpoint='/api/words/רעה',
    status_code=200,
    response_time_ms=342
)
```

**Console Output**:
```
09:44:10 | concordance_librarian | INFO | Concordance Librarian query: רעה
09:44:10 | concordance_librarian | INFO | Generated 66 morphological variations
09:44:10 | concordance_librarian | INFO | Concordance Librarian returned 15 results
```

**JSON Output**:
```json
{
  "level": "INFO",
  "message": "Concordance Librarian query: רעה",
  "event_type": "librarian_query",
  "librarian_type": "concordance",
  "query": "רעה",
  "params": {"scope": "Psalms", "level": "consonantal"},
  "timestamp": "2025-10-16T09:44:10.546462",
  "agent": "concordance_librarian"
}
```

**Log Summary**:
```python
summary = logger.get_summary()
# Returns:
{
  "total_entries": 47,
  "by_level": {"INFO": 32, "DEBUG": 15},
  "by_event_type": {
    "research_request": 1,
    "librarian_query": 3,
    "librarian_results": 3,
    "phrase_variations": 3,
    "performance_metric": 6,
    "api_call": 31
  }
}
```

---

### Morphological Variation System

**Purpose**: Generate comprehensive Hebrew word forms for maximum concordance recall

**Module**: `src/concordance/morphology_variations.py`

**Problem**: Pattern-based prefix generation (ה, ו, ב, כ, ל, מ) only finds ~95% of occurrences

**Solution**: Pattern-based morphology generation with 3.3x improvement

**Generated Patterns**:

1. **Noun Variations**:
   - Feminine: ה, ת, ית
   - Plural: ים, ות
   - Dual: יים
   - Pronominal: י (my), ך (your), ו (his), ה (her), נו (our), כם/ן (their)

2. **Verb Variations**:
   - **Perfect forms**: stem prefix + root
     - Qal: (no prefix)
     - Niphal: נ
     - Hiphil: ה, הִ
     - Hophal: הָ, הו
     - Hithpael: הת, הִת

   - **Imperfect forms**: person prefix + root ONLY
     - 1s: א (I will)
     - 2m/2f/3f: ת (you/she will)
     - 3m: י (he will)
     - 1cp: נ (we will)
     - **Note**: Stem info encoded in vowel patterns, not prefix stacking

   - **Participles**: מ prefix patterns

3. **Final Letter Forms**: כ→ך, מ→ם, נ→ן, פ→ף, צ→ץ (applied automatically)

**Linguistic Constraints**:
- ✅ Mutually-exclusive pattern sets (perfect vs imperfect vs participle)
- ✅ No impossible combinations (יהָרעה, יהִתשמר eliminated)
- ✅ Orthographically correct final letters
- ✅ Root normalization before generation (ברך → ברכ → generate → apply finals)

**Usage**:
```python
from src.concordance.morphology_variations import MorphologyVariationGenerator

gen = MorphologyVariationGenerator()
variations = gen.generate_variations("שמר")
# Returns: ['אשמר', 'הִשמר', 'ישמר', 'נשמר', 'תשמר',
#           'שמר', 'שמרה', 'שמרו', 'שמרי', 'שמרים', ...]
# Total: 66 variations (3.3x improvement over 20 prefix-only forms)
```

**Hybrid Search with Validator**:
```python
from src.concordance.morphology_variations import MorphologyValidator

# Phase 1: Exact search with generated variations
variations = gen.generate_variations("אהב")  # 38 forms
exact_results = search_concordance(variations)  # 5 results

# Phase 2: Substring discovery
substring_results = search_substring("%אהב%")  # 20 results

# Phase 2b: Validation
validator = MorphologyValidator("אהב")
validated = [r for r in substring_results
             if validator.is_plausible(r.matched_word)]  # 13 valid

# Combine (4x improvement: 5 → 13)
all_results = deduplicate(exact_results + validated)
```

**Validator Checks**:
- Root consonants appear in correct order
- Reasonable length (root + 0-6 characters)
- No impossible prefix combinations (יה, יהת, תה, אה)
- Foundation for OSHB morphology database integration

**Future Enhancement Path**:
```python
# Option 1: OSHB morphhb database (attested forms only)
from morphhb import get_word_forms
variations = get_word_forms("שמר")  # 100% accurate

# Option 2: Hybrid (best of both)
pattern_forms = gen.generate_variations("שמר")  # 66 pattern-based
oshb_forms = oshb.lookup("שמר")  # Attested forms
combined = set(pattern_forms) | set(oshb_forms)  # Maximum coverage
```

**Resources**:
- OSHB: https://github.com/openscriptures/morphhb
- Hebrew verb conjugation: https://en.wikipedia.org/wiki/Hebrew_verb_conjugation

---

### Agent Prompt Templates

*(AI agent prompts - to be expanded as Scholar agents are developed)*

#### Pass 1: Macro Analysis (Sonnet 4.5)

```markdown
You are a biblical scholar analyzing Psalm {psalm_number}.

TASK: Provide a macro-level analysis of the entire chapter BEFORE examining individual verses.

Read the full chapter below:

{hebrew_text}

{english_text}

---

Your macro analysis should identify:

1. **EMOTIONAL/NARRATIVE ARC**
   - How does the mood shift throughout the chapter?
   - What is the emotional journey? (e.g., lament → trust, anger → praise)
   - Are there clear pivot points?

2. **STRUCTURAL DIVISIONS**
   - How would you divide this chapter into sections?
   - Are there refrains, repeated phrases, or inclusios?
   - What is the logical flow of the argument?

3. **CENTRAL THESIS**
   - In ONE specific sentence, what is this Psalm about?
   - Avoid generic statements like "trust in God"
   - Be precise about the specific claim or situation

4. **GENRE CLASSIFICATION**
   - What type of Psalm is this? (lament, praise, wisdom, royal, etc.)
   - What are the typical features of this genre?

5. **POETIC ARCHITECTURE**
   - How do the parts relate to create the whole?
   - What is the psalmist's rhetorical strategy?

6. **QUESTIONS FOR MICRO-ANALYSIS**
   - What questions should verse-by-verse analysis explore?
   - Which Hebrew words or phrases deserve special attention?
   - What figurative language should we investigate?

OUTPUT: A structured overview (~800-1000 words) that will guide detailed verse analysis.

Remember: This is about seeing the FOREST. Details come later.
```

#### Scholar-Researcher Agent (Haiku 4.5)

```markdown
You are a research coordinator for biblical scholarship.

You have read the macro overview of Psalm {psalm_number}:

{macro_overview}

Now the chapter will undergo detailed verse-by-verse analysis. Your job is to identify what research data is needed.

Generate specific research requests in the following categories:

1. **BDB LEXICON REQUESTS**
   - List 5-8 key Hebrew words that deserve lexical investigation
   - For each word, explain WHY it's significant (not just "it appears")
   - Focus on: unusual choices, loaded terms, ambiguous meanings

2. **CONCORDANCE SEARCHES**
   - Identify Hebrew roots or phrases to trace across Psalms
   - What themes or motifs need tracking?
   - Specify search level for each:
     * **consonantal** (default): Finds all forms of root regardless of vocalization
     * **voweled**: Distinguishes homographs (same consonants, different meanings)
     * **exact**: Specific vocalization (only use when homograph disambiguation needed)
   - Example: "Search root רעה (shepherd) consonantally in Psalms to track pastoral imagery"

3. **FIGURATIVE LANGUAGE CHECKS**
   - Which verses likely contain metaphor, simile, personification?
   - What figurative patterns should we look for?
   - **Note**: Searches are broad and find all figurative types; do not filter by specific type

OUTPUT FORMAT: JSON structure

{{
  "bdb_requests": [
    {{"word": "שׁמר", "reason": "Appears 3x, central to protection theme"}},
    ...
  ],
  "concordance_searches": [
    {{"query": "רעה", "level": "consonantal", "scope": "Psalms", "purpose": "Track shepherd imagery"}},
    ...
  ],
  "figurative_checks": [
    {{"verse": 1, "reason": "Shepherd imagery for divine care", "vehicle": "shepherd", "vehicle_synonyms": ["pastor", "herdsman", "protector"]}},
    ...
  ]
}}

Be SPECIFIC. Vague requests waste resources.
```

---

## API Integrations

### Sefaria API Client

*(Implementation details will be added in src/data_sources/sefaria_client.py)*

**Key Functions**:
- `fetch_psalm(chapter_num: int) -> dict` - Get Hebrew + English text
- `fetch_lexicon_entry(word: str) -> dict` - Get BDB definition
- `fetch_related_texts(ref: str) -> list` - Get commentary snippets

**Error Handling**:
- Exponential backoff for rate limits
- Retry logic (max 3 attempts)
- Cache successful responses

### Anthropic Claude API

**Model Selection Strategy**:
- **Sonnet 4.5**: Deep analysis tasks (macro, micro, synthesis, revision)
- **Haiku 4.5**: Pattern recognition tasks (research requests, critique)

**Token Optimization**:
- Prompt caching for system instructions
- Structured outputs (JSON when appropriate)
- Batch API for non-urgent processing (50% discount)

---

## Output Generation

### Word Document Format

**Structure**:
1. Header: Psalm number, date generated
2. Hebrew text (right-aligned, modified divine names)
3. English translation
4. Synthesis essay (main commentary)
5. Verse-by-verse notes
6. Footer: Attribution, methodology note

**Divine Name Modifications**:
Implemented via rules from `NON_SACRED_HEBREW.md`:
- יהוה → ה׳
- אֱלֹהִים → אֱלֹקִים (ה → ק)
- אֵל → קֵל
- etc.

---

## Cost & Performance

### Target Metrics
- **Cost per chapter**: $0.20-0.25 (average 16.8 verses)
- **Processing time**: 2-3 minutes per chapter
- **Total project cost**: $30-40 for all 150 Psalms
- **Quality score**: >4.0/5.0 on telescopic integration metric

### Optimization Strategies
1. **Prompt caching**: System instructions reused
2. **Batch API**: 50% discount for non-urgent processing
3. **Model selection**: Haiku where Sonnet not needed
4. **Python librarians**: No LLM cost for data fetching

---

## Future Enhancements

*(Ideas for post-v1 improvements)*
- Lemmatizer for automatic root extraction
- Integration with HALOT (if institutional access secured)
- Parallel processing for batch runs
- Web interface for browsing commentary
- Export to additional formats (PDF, ePub, HTML)

---

## Phase 3c: SynthesisWriter + Print-Ready Formatting (COMPLETE)

### Components Built

**1. SynthesisWriter Agent** ([src/agents/synthesis_writer.py](src/agents/synthesis_writer.py))
- Pass 3 of pipeline: Final commentary synthesis
- **Introduction essay** (800-1200 words): Critically engages macro thesis with authority to revise/reject
- **Verse commentary** (150-300 words/verse): Independent scholarly angles (poetics, polemics, vorlage, Ugaritic, interpretive debates)
- Integrates macro + micro + research bundle smoothly
- Cites classical scholarship (Rashi, Targum, LXX, rabbinic, patristic)
- Makes intertextual connections across Scripture and ANE literature

**2. Divine Names Modifier** ([src/utils/divine_names_modifier.py](src/utils/divine_names_modifier.py))
- Replaces Hebrew divine names with non-sacred forms
- Transformations: יהוה → ה׳, אלהים → אלקים, אֵל → קֵל, צבאות → צבקות, שדי → שקי, אלוה → אלוק
- Applied to ALL Hebrew text throughout document (verses + commentary)

**3. Commentary Formatter** ([src/utils/commentary_formatter.py](src/utils/commentary_formatter.py))
- Fetches Hebrew and English verse text from database
- Integrates verse text with commentary for each verse
- Applies divine names modifications comprehensively
- Produces print-ready markdown documents

**4. Print-Ready Script** ([scripts/create_print_ready_commentary.py](scripts/create_print_ready_commentary.py))
- Simple CLI: `python scripts/create_print_ready_commentary.py --psalm 29`
- Generates complete formatted commentary ready for publication

### Psalm 29 Test Results

**Quality Metrics:**
- Introduction: 1,002 words (target: 800-1200) ✅
- Verse commentary: ~218 words/verse average (target: 150-300) ✅
- Total document: 26,490 characters with full formatting
- Divine names: 100% modified correctly throughout

**Commentary Quality:**
- Rich intertextual connections (Gen 1:2, Ex 40:34-35, Ps 96:7-8, Ps 114:4-6)
- Classical scholarship (Rashi, Targum, LXX readings)
- Ugaritic/ANE parallels (Baal myths, KTU references, bn 'ilm divine council)
- Lexical depth (BDB citations, semantic ranges, etymologies)
- Interpretive debates (בְּנֵי אֵלִים meanings, הַדְרַת־קֹדֶשׁ translation crux)
- Textual variants and vorlage insights
- Theological sophistication (מַבּוּל flood theology, covenant transformation)

### Pipeline Status

**Complete Passes:**
- ✅ Pass 1: MacroAnalyst - Chapter-level thesis
- ✅ Pass 2: MicroAnalyst v2 - Curiosity-driven verse discoveries
- ✅ Pass 3: SynthesisWriter - Final commentary + print-ready formatting

**Original Plan (passes 4-5 not needed):**
- Output quality sufficient for publication without additional editing passes
- SynthesisWriter produces print-ready documents directly

---

*This document will be updated as implementation progresses.*
*Last updated: 2025-10-17 (Phase 3c complete - Print-ready commentary system operational)*