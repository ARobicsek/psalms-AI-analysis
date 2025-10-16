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

### Agent Prompt Templates

*(This section will be expanded as agents are developed)*

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
   - Specify search level for each (consonantal, voweled, exact)
   - Example: "Search root רעה (shepherd) consonantally in Psalms to track pastoral imagery"

3. **FIGURATIVE LANGUAGE CHECKS**
   - Which verses likely contain metaphor, simile, personification?
   - What figurative patterns should we look for?

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
    {{"verse": 1, "likely_type": "metaphor", "reason": "Shepherd imagery for divine care"}},
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

*This document will be updated as implementation progresses.*
*Last updated: 2025-10-15*