# Technical Architecture Summary: Psalms Commentary Pipeline

**Date**: 2025-12-26
**Version**: Enhanced Pipeline V6.3 (Phase 4, Sessions 200-222)
**Status**: Production System with SI Pipeline, Gemini Fallback, V2 Prompts

---

## Executive Summary

The Psalms Commentary Pipeline is a sophisticated AI-powered system that generates scholarly biblical commentary through a six-step agent architecture. The system combines multiple Large Language Models (Claude Sonnet 4.5, GPT-5.1) with ten specialized Python librarians to produce publication-quality commentary that rivals traditional scholarly work.

**Key Innovation**: The system prevents common AI failure modes through a "telescopic analysis" approach—breaking complex tasks into specialized passes, each building on previous work while maintaining focus on specific aspects of analysis.

**Latest Enhancements (Sessions 200-220)**:
- **Special Instruction Pipeline**: Author-directed commentary revisions without altering standard pipeline (Session 220)
- **Master Editor V2**: Restructured prompt with explicit Deep Research guidance, now default (Session 215)
- **Gemini 2.5 Pro Fallback**: Automatic switching for large psalms (51+ verses) with 1M token context (Session 211)
- **Resume Feature**: `--resume` flag for automatic step detection (Session 219)
- **Strategic Verse Grouping**: Prevents truncation in long psalms (Session 212)
- **Deep Web Research Integration**: Manual Gemini Deep Research outputs auto-load into research bundle (Session 209)

---

## System Architecture Overview

### High-Level Flow

```
Input: Psalm Number
    ↓
[1] Macro Analysis (Claude Sonnet 4.5)
    → Structural thesis, poetic devices, research questions
    ↓
[2] Micro Analysis + Research Request Generation (Claude Sonnet 4.5)
    → Discovery-driven verse analysis, research requests
    ↓
    [Research Bundle Assembly - 9 Python Librarians]
    → Lexicon, concordance, figurative analysis, commentary,
      liturgical usage, related psalms, Sacks, Deep Web Research
    ↓
[3] Synthesis Writing (Claude Sonnet 4.5 OR Gemini 2.5 Pro)
    → Introduction essay + verse commentary with quotations
    → Gemini fallback for large psalms (51+ verses, 1M token context)
    ↓
[4] Master Editorial Review (GPT-5.1 or Claude Opus 4.5)
    → V2 prompt (default): Restructured with explicit Deep Research guidance
    → OLD prompt: Available via --master-editor-old flag
    → Critical review, fact-checking, enhancement to "National Book Award" level
    ↓
[4b] College Commentary Generation (GPT-5.1 or Claude Opus 4.5)
    → Separate, more accessible version for college students
    ↓
[5] Print-Ready Formatting (Python)
    → Markdown with divine name modifications, verse numbering
    ↓
[6] Document Generation (Python)
    → Three .docx outputs: main commentary, college edition, combined
    ↓
[OPTIONAL] Special Instruction Pipeline
    → Author-directed revisions using MasterEditorSI
    → Separate _SI suffixed outputs (main, college, combined)
    ↓
Output: Scholarly Commentary (.docx + .md, with college edition)
```

### Core Components

1. **AI Agents** (4 specialized LLM-based analyzers with dual-edition output)
2. **Librarian Agents** (9 deterministic Python data retrieval systems)
3. **Data Sources** (SQLite databases, Sefaria API, RAG documents, V6 statistical analysis)
4. **Pipeline Tracking** (Comprehensive statistics with resume capability)
5. **Cost Tracking** (API usage and cost monitoring across all models)
6. **Output Generation** (Markdown → Multiple Word document formats)
7. **Logging & Metrics** (Dual-format observability system)

---

## Technical Implementation Details

### 1. AI Agent Architecture

#### MacroAnalyst (Pass 1)
- **Model**: Claude Sonnet 4.5 (`claude-sonnet-4-20250514`)
- **Purpose**: High-level thesis formation and structural analysis
- **Input**: Psalm text (Hebrew/English), RAG context
- **Output**: `MacroAnalysis` object (JSON schema)
- **Key Features**:
  - Genre identification and contextual analysis
  - Structural framework with poetic devices
  - Research question generation
  - Thesis formation with supporting evidence

#### MicroAnalyst v2 (Pass 2)
- **Model**: Claude Sonnet 4.5 (`claude-sonnet-4-20250514`)
- **Purpose**: Verse-by-verse discovery and research request generation
- **Input**: `MacroAnalysis`, Psalm text, phonetic transcriptions
- **Output**: `MicroAnalysis` object + `ResearchBundle` requests
- **Commentary Mode**: `all` (default) or `selective` (request only for specific verses)
- **Key Features**:
  - Discovery-driven (not thesis-driven) verse analysis
  - Curiosity-focused approach to find patterns, puzzles, surprises
  - Phonetic transcription integration for sound pattern analysis
  - Research request generation (lexicon, concordance, figurative, commentary)
  - Pattern recognition and interesting question formulation
  - Three-stage process: Discovery → Research Requests → Bundle Assembly

#### SynthesisWriter (Pass 3)
- **Model**: Claude Sonnet 4.5 (`claude-sonnet-4-20250514`) with **Gemini 2.5 Pro fallback**
- **Purpose**: Integration of all analysis into coherent commentary
- **Input**: `MacroAnalysis`, `MicroAnalysis`, `ResearchBundle`
- **Output**: Introduction essay + verse-by-verse commentary
- **Gemini Fallback** (Session 211):
  - Automatic switching to `gemini-2.5-pro` when research bundle exceeds ~350K chars
  - Gemini 2.5 Pro provides 1M token context vs Claude's 200K limit
  - Progressive trimming before fallback: Related Psalms → Figurative Language (75% → 50%)
  - Never trimmed: Lexicon, Commentaries, Liturgical, Sacks, RAG, Concordance, Deep Research
  - `synthesis_model_used` property tracks which model was actually used
- **Key Features**:
  - 800-1200 word introduction essay
  - 150-400+ words per verse commentary
  - **Enhanced quotation emphasis** (Session 122): Generous quoting from sources in Hebrew + English
  - Critical engagement with sources and prior scholarship
  - Intertextual connections with biblical parallels
  - Integration of liturgical usage and related psalms insights
  - **Poetic punctuation** (Session 121): LLM-generated verses with semicolons, periods, commas
  - Accessible scholarly voice (Robert Alter, Ellen Davis style)
  - **Strategic Verse Grouping** (Session 212): For long psalms (35+ verses), 2-4 related verses can be grouped with pacing guidance

#### MasterEditor (Pass 4 & 4b)
- **Model Options**:
  - **Default**: GPT-5.1 (`gpt-5.1`) with high reasoning effort
  - **Alternative**: GPT-5 (`gpt-5`) with high reasoning effort (legacy)
  - **Alternative**: Claude Opus 4.5 (`claude-opus-4-5`) with extended thinking (64K token budget)
- **Prompt Versions** (Session 215):
  - **V2 (default)**: Restructured prompt with consolidated "Ground Rules," explicit Deep Research guidance, reduced redundancy
  - **OLD**: Available via `--master-editor-old` flag
- **Purpose**: Final editorial review and quality enhancement
- **Dual Output**:
  - **Pass 4**: Main edition for sophisticated lay readers (New Yorker/Atlantic audience)
  - **Pass 4b**: College edition with more accessible language for undergraduate students
- **Input**: Complete commentary, research bundle, analysis objects, psalm text
- **Output**: Revised introduction + verse commentary + editorial assessment (main and college versions)
- **Character Limit**: 350,000 characters (~175K tokens) for comprehensive review
- **Key Features**:
  - "National Book Award" quality standards
  - **Enhanced quotation checking** (Session 122): Ensures sources are quoted, not just cited
  - **Poetic punctuation verification** (Session 121): Ensures verses include punctuation
  - Phonetic accuracy verification using authoritative transcriptions
  - Factual error detection (biblical, historical, grammatical)
  - Missed opportunities identification (unused research, unanswered questions)
  - Style refinement (avoiding LLM-ish breathlessness, academic jargon)
  - Coherence and argumentation strengthening
  - **College Edition Adaptations**: Simplified language, fewer technical terms, more context

### 2. Librarian Agent System

#### BDB Librarian
- **Function**: Hebrew lexicon lookups via Sefaria API
- **Sources**: BDB Dictionary, Klein Dictionary
- **Implementation**: `src/data_sources/sefaria_client.py`
- **Key Features**:
  - Handles Sefaria API response format (list structure)
  - Recursive extraction from nested "senses" arrays
  - HTML cleaning for clean text output

#### Concordance Librarian
- **Function**: Hebrew concordance search with morphological variations
- **Database**: `hebrew_concordance.db` (SQLite)
- **Implementation**: `src/concordance/search.py`
- **Key Features**:
  - 4-layer normalization system (exact, voweled, consonantal, root)
  - Automatic morphological variation generation (66 variations)
  - **Phrase substring matching** (Session 176): Multi-word phrases use substring matching while preserving exact matching for single words
  - **Word order flexibility** (Session 180): Phrases found regardless of word sequence
  - **Maqqef handling** (Session 180): Maqqef (־) properly replaced with space before normalization
  - Phrase searches guaranteed to find source verse
  - Scope filtering for relevant contexts

#### Figurative Language Librarian
- **Function**: Queries pre-analyzed figurative language database
- **Database**: Hierarchical JSON tags system
- **Implementation**: `src/data_sources/figurative_search.py`
- **Key Features**:
  - Hierarchical tag matching via SQL LIKE
  - **Vehicle terms as conceptual tags, not inflected words** (Session 179): Morphological variants NOT used for vehicle searches
  - **Priority search** (Session 218): Sequential term processing for ordered search results
  - **Priority-based sorting and trimming** (Session 222): Results tagged with `term_priority`, sorted by priority with randomization within groups, trimmed from lowest priority first
  - Vehicle and tenor-based searches
  - Metaphor family expansion
  - Usage pattern analysis
  - Substring matching with word boundaries prevents false positives

#### Commentary Librarian
- **Function**: Fetches traditional Jewish commentaries
- **Sources**: Rashi, Ibn Ezra, Radak, Metzudat David, Malbim, Meiri, Torah Temimah
- **Implementation**: `src/agents/commentary_librarian.py`
- **Key Features**:
  - Multiple commentary integration
  - Historical perspective inclusion
  - Traditional interpretation synthesis

#### Liturgical Librarian (Dual-Phase Implementation)
- **Function**: Identifies where Psalm passages appear in Jewish liturgy
- **Databases**: `liturgy.db` with prayers and phrase-level index
- **Implementation**: Dual-phase approach
  - Phase 0: `liturgical_librarian_sefaria.py` - Bootstrap from Sefaria cross-references
  - Phase 4/5: `liturgical_librarian.py` - Comprehensive phrase-level matching
- **Key Features**:
  - Verse-level and sub-verse phrase detection
  - Coverage across 3 traditions (Ashkenaz, Sefard, Edot HaMizrach)
  - Gemini 2.5 Pro LLM-powered intelligent summarization (primary), with Claude Sonnet 4.5 fallback
  - Aggregation by prayer name (prevents duplicate contexts)
  - Quality validation with automatic retry logic
  - Misattribution detection (prevents wrong psalm references)
  - Generates narrative summaries of liturgical usage for research bundle

#### Related Psalms Librarian (Sessions 107-119)
- **Function**: Identifies and retrieves related psalms from statistical analysis
- **Database**: V6 top 550 connections analysis
- **Implementation**: `src/agents/related_psalms_librarian.py`
- **Key Features**:
  - Loads top 5 most related psalms by final score
  - **V6 Scoring** (Sessions 115-117): Fresh statistical analysis with improved Hebrew morphology
  - Retrieves full psalm text (Hebrew only for token efficiency)
  - Provides shared roots with IDF scores
  - Shows contiguous phrases (2-6 word exact matches)
  - Displays skipgrams (gappy patterns) with full span Hebrew
  - **Token optimization** (Sessions 118-119): 50-60% reduction through smart formatting
  - Bidirectional matching (psalm_a ↔ psalm_b)

#### Sacks Librarian
- **Function**: Retrieves Rabbi Jonathan Sacks' references to Psalms
- **Source**: Collected works and essays
- **Implementation**: `src/agents/sacks_librarian.py`
- **Key Features**:
  - Modern British Orthodox perspective
  - Philosophical and ethical interpretations
  - Contemporary relevance emphasis

#### Deep Web Research Librarian (Session 209)
- **Function**: Loads manually prepared Gemini Deep Research outputs into research bundle
- **Source**: `data/deep_research/psalm_NNN_deep_research.txt`
- **Implementation**: `src/agents/research_assembler.py`
- **Key Features**:
  - Material prepared via Gemini browser interface
  - Auto-loads into research bundle after Concordance
  - Included in priority (never trimmed unless all else fails)
  - Cultural and artistic afterlife, scholarly debates, political reception
  - Pipeline stats track "Deep Web Research: Yes/No"

#### Research Bundle Assembler
- **Function**: Coordinates all 9 librarians and formats results
- **Output**: Markdown format for LLM consumption
- **Implementation**: `src/agents/research_assembler.py`
- **Librarians Coordinated**:
  1. BDB Librarian (lexicon entries)
  2. Concordance Librarian (word/phrase searches)
  3. Figurative Language Librarian (metaphor analysis)
  4. Commentary Librarian (traditional Jewish commentaries)
  5. Liturgical Librarian (liturgical usage - Phase 4/5 aggregated)
  6. Liturgical Librarian Sefaria (liturgical usage - Phase 0 fallback, deprecated)
  7. Related Psalms Librarian (statistical connections)
  8. Sacks Librarian (modern British Orthodox perspective)
  9. Deep Web Research Librarian (cultural afterlife, reception history)
- **Key Features**:
  - JSON and Markdown serialization
  - Token limit management (700,000 character capacity - Session 109)
  - **Priority-based content trimming**: Lexicon and commentary always preserved; Related Psalms trimmed first; Figurative trimmed second (lowest-priority terms removed first, Session 222)

### 3. Hebrew Text Processing System

#### Normalization Pipeline
```python
def normalize_hebrew(text: str, level: int) -> str:
    """
    4-layer Hebrew text normalization:
    - Level 0: Exact match (preserve all diacritics)
    - Level 1: Voweled (strip cantillation, keep vowels)
    - Level 2: Consonantal (strip vowels, keep consonants)
    - Level 3: Root/Lemma (morphological root)
    """
```

#### Morphological Variation Generator
- **Function**: Automatic generation of Hebrew word forms
- **Implementation**: `src/concordance/morphology_variations.py`
- **Features**:
  - 66 strategic variations (optimized from 200+)
  - Prefix patterns (prepositions, articles)
  - Suffix patterns (pronouns, verb endings)
  - Verb stem variations (Qal, Niphal, Piel, etc.)
  - Tense and aspect modifications

#### Root Extraction System (V6 - Sessions 112-115)
- **Function**: Extract morphological roots from inflected Hebrew words
- **Implementation**: `src/hebrew_analysis/morphology.py`
- **Data Sources**:
  - **ETCBC Morphology Cache** (Session 105): 5,353 authoritative mappings from ETCBC BHSA 2021
  - **Fallback Extraction**: Algorithmic stripping for words not in cache
- **V6 Improvements (Session 115)**:
  1. **Hybrid Stripping Approach**: Adaptive strategy based on word structure
     - Prefix-first for simple prefixes: `בשמים` → `שמים`
     - Suffix-first for ש-words to protect ש-roots: `שקרים` → `שקר`
  2. **Plural Ending Protection**: Stricter minimums for ים/ות endings
     - Prevents over-stripping of dual/plural nouns
     - `שמים` → `שמים` (dual "heavens", not שם + plural)
  3. **Final Letter Normalization**: Converts to proper final forms (ך ם ן ף ץ)
- **Quality Metrics**: 93.75% test pass rate (15/16 comprehensive tests), 80% improvement on root extraction test cases vs. V4

#### Phonetic Transcription System
- **Function**: Hebrew text to phonetic representation
- **Implementation**: `src/agents/phonetic_analyst.py`
- **Features**:
  - Reconstructed Biblical Hebrew phonology
  - Dagesh distinction handling (b/v, k/kh, p/f)
  - Divine name modifications (יהוה → ה׳)
  - Syllable structure analysis

### 4. Data Storage Architecture

#### SQLite Databases
1. **`tanakh.db`**: Complete Hebrew Bible text
   - Tables: `chapters`, `verses`
   - Fields: `book_name`, `chapter`, `verse`, `hebrew`, `english`

2. **`hebrew_concordance.db`**: Word-level concordance
   - Tables: `concordance`
   - Fields: `word_full`, `word_vowels_only`, `word_consonants_only`, `word_root`, `strongs_number`, `lemma`, `morphology`, `gloss`, `collocations`

3. **`psalms_commentary.db`**: Pipeline output storage
   - Tables: `chapters`, `verses`, `research_requests`, `cost_log`
   - Fields: Analysis results, research bundles, cost tracking

4. **`liturgy.db`**: Liturgical texts and Psalms cross-reference index
   - Tables: `prayers`, `psalms_liturgy_index`, `sefaria_liturgy_links`, `liturgical_metadata`
   - Fields: Prayer classification (nusach, occasion, service, section), phrase matches, confidence scores

5. **`psalm_relationships.db`**: V6 Skipgram patterns database (Session 113-115)
   - Tables: `psalm_skipgrams`
   - Fields: `psalm_a`, `psalm_b`, `skipgram_hebrew`, `gap_word_count`, `pattern_roots`, `content_word_count`, `pattern_category`
   - Size: 130 MB, 335,720 quality-filtered skipgrams
   - **Quality Filters** (Session 111): Content word filtering, pattern stoplist (41 formulaic patterns), gap penalty (10% per gap word, max 50%)

#### V6 Statistical Analysis Files (Sessions 115-117)
- **`psalm_patterns_v6.json`**: Fresh root and phrase extraction (39.67 MB)
  - 11,170 psalm pairs with patterns
  - 2,738 unique roots with IDF scores
- **`enhanced_scores_v6.json`**: Comprehensive scoring (107.97 MB)
  - 11,170 scored psalm pairs
  - Fresh roots + phrases from V6 patterns
  - V5 skipgrams from database (quality-filtered)
- **`top_550_connections_v6.json`**: Top relationships (13.35 MB)
  - Score range: 19,908.71 to 211.50
  - Top connection: Psalms 14-53 (nearly identical)

#### ETCBC Morphology Cache (Session 105)
- **File**: `src/hebrew_analysis/data/psalms_morphology_cache.json`
- **Size**: 147.7 KB
- **Entries**: 5,353 morphological mappings from Psalms
- **Source**: ETCBC BHSA 2021 scholarly database
- **Purpose**: Authoritative root extraction for Hebrew words

### 5. Pipeline Tracking and Management

#### Pipeline Summary Tracker
- **Function**: Comprehensive statistics tracking throughout pipeline execution
- **Implementation**: `src/utils/pipeline_summary.py`
- **Key Features**:
  - Step-by-step tracking with input/output character and token counts
  - Duration tracking for each pipeline step
  - Model usage recording (which LLM used for each step)
  - Research statistics (lexicon, concordance, figurative, commentary request counts)
  - Research bundle size metrics
  - Related psalms count and list
  - Resume capability with `--resume` flag for automatic step detection
  - JSON and Markdown output formats

#### Pipeline Control Flags
- **`--skip-macro`**: Use existing macro analysis file
- **`--skip-micro`**: Use existing micro analysis file
- **`--skip-synthesis`**: Use existing synthesis files
- **`--skip-master-edit`**: Use existing master-edited files
- **`--skip-college`**: Skip college commentary generation (use existing file)
- **`--skip-print-ready`**: Skip print-ready formatting step
- **`--skip-word-doc`**: Skip .docx generation step
- **`--skip-combined-doc`**: Skip combined .docx generation
- **`--resume`**: Resume from last completed step (auto-detects based on existing files)
- **`--smoke-test`**: Generate dummy data without API calls
- **`--skip-default-commentaries`**: Use selective commentary mode
- **`--master-editor-model`**: Model to use for master editor (choices: gpt-5, gpt-5.1, claude-opus-4-5)
- **`--master-editor-old`**: Use OLD prompt (V2 is now default)
- **`--delay SECONDS`**: Rate limit delay between API-heavy steps (default: 120)

### 6. Special Instruction Pipeline (Session 220)

**Purpose**: Generate alternative commentary versions with author-directed thematic revisions without modifying the standard pipeline outputs.

**When to Use**: When you want to explore a specific theme or angle in a psalm without altering the standard scholarly commentary.

**How It Works**:
1. Create a text file with your instructions at `data/special_instructions/special_instructions_Psalm_NNN.txt`
2. Run: `python scripts/run_si_pipeline.py NNN`
3. The pipeline re-runs only the Master Editor step with your special instructions

**Outputs**: All outputs use `_SI` suffix to prevent overwriting originals:
- `psalm_NNN_edited_intro_SI.md`
- `psalm_NNN_edited_verses_SI.md`
- `psalm_NNN_assessment_SI.md`
- `psalm_NNN_edited_intro_college_SI.md`
- `psalm_NNN_edited_verses_college_SI.md`
- `psalm_NNN_assessment_college_SI.md`
- `psalm_NNN_pipeline_stats_SI.json`
- `psalm_NNN_commentary_SI.docx`
- `psalm_NNN_commentary_college_SI.docx`
- `psalm_NNN_commentary_combined_SI.docx`

**Key Design**:
- Extends `MasterEditorV2` via inheritance (`MasterEditorSI` class)
- SPECIAL AUTHOR DIRECTIVE section in prompt (highest priority)
- Never overwrites original pipeline files
- Separate stats tracking

### 7. Tribal Blessings Analyzer (Session 229) - Reusable Non-Psalm Analysis

**Purpose**: Analyze figurative language in structured biblical passages outside the Psalms (e.g., Genesis 49's tribal blessings, Deuteronomy 33, Numbers 23-24).

**Architecture**: Adapts the FigurativeCurator pattern for non-Psalm passages organized by named segments (tribes, nations, etc.).

**Components**:
- **`src/agents/tribal_curator.py`**: Core curator class with configurable passage analysis
- **`scripts/tribal_blessings_analyzer.py`**: CLI script for running analysis

**Key Features**:
- **Configurable Passages**: Uses `PassageAnalysisConfig` dataclass for any book/chapter/segment structure
- **Segment-Based Analysis**: Analyzes by named segments (tribes, nations) rather than verse-by-verse
- **Vehicle + Target Searches**: Searches for figurative vehicles AND segment names as targets
- **3-Iteration Refinement**: Uses Gemini 3 Pro with iterative search refinement
- **1000-2000 Word Insights**: Scholarly essays with Hebrew quotations
- **Reception History**: Includes cultural impact, art, politics, interpretive traditions
- **5+ Biblical Parallels**: Curated examples with relevance explanations
- **Deep Research Integration**: Auto-loads from `data/deep_research/` directory

**Pre-Configured Passages**:
```python
GENESIS_49_CONFIG = PassageAnalysisConfig(
    book="Genesis",
    chapter=49,
    name="Jacob's Tribal Blessings",
    segments={
        "Reuben": SegmentConfig(verses=[3, 4], blessing_type="rebuke"),
        "Simeon and Levi": SegmentConfig(verses=[5, 6, 7], blessing_type="rebuke"),
        "Judah": SegmentConfig(verses=[8, 9, 10, 11, 12], blessing_type="royal_blessing"),
        # ... etc.
    }
)
```

**Usage**:
```bash
# Analyze single tribe
python scripts/tribal_blessings_analyzer.py --tribe Judah

# Analyze all tribes
python scripts/tribal_blessings_analyzer.py --all --verbose

# List available tribes
python scripts/tribal_blessings_analyzer.py --list
```

**Output**:
- Individual tribe markdown files: `output/genesis_49/tribe_judah.md`
- Combined summary: `output/genesis_49/tribal_analysis_summary.md`
- Statistics: `output/genesis_49/analysis_stats.json`

**Future Applications**: The `PassageAnalysisConfig` pattern can be extended for:
- Deuteronomy 33 (Moses' Blessings)
- Numbers 23-24 (Balaam's Oracles)
- Isaiah 13-23 (Oracles Against Nations)
- Ezekiel 27-28 (Laments)

### 8. Output Generation Pipeline

#### Commentary Formatter
- **Function**: Markdown to structured commentary
- **Implementation**: `src/utils/commentary_formatter.py`
- **Features**:
  - Divine name modifications for study (יהוה → ה׳)
  - **LLM-generated verse presentation** (Session 121): Relies on LLM to provide punctuated verses
  - Pipeline statistics integration
  - Sefaria footnote stripping (Session 109)
  - Cross-reference integration

#### Document Generator
- **Function**: Word document creation (.docx)
- **Implementations**:
  - `src/utils/document_generator.py` - Main and college editions
  - `src/utils/combined_document_generator.py` - Combined edition
- **Three Output Formats**:
  1. **Main Edition** (`psalm_NNN_commentary.docx`): Full scholarly commentary
  2. **College Edition** (`psalm_NNN_commentary_college.docx`): More accessible version
  3. **Combined Edition** (`psalm_NNN_commentary_combined.docx`): Both in one document
- **Features**:
  - Professional formatting with Hebrew fonts
  - Print-ready layout
  - Pipeline statistics, related psalms, research bundle statistics
  - Sefaria footnote stripping
  - Phonetic transcription italicization
  - Divine name formatting
  - Bidirectional text handling

### 8. Logging and Observability

#### Dual-Format Logging System
- **Console Output**: Human-readable progress tracking
- **JSON Logs**: Machine-readable metrics and debugging
- **Implementation**: `src/utils/logger.py`

#### Cost Tracking System
- **Function**: Real-time API usage and cost monitoring
- **Implementation**: `src/utils/cost_tracker.py`
- **Models Tracked**:
  - Claude Sonnet 4.5 (MacroAnalyst, MicroAnalyst, SynthesisWriter)
  - Gemini 2.5 Pro (Liturgical Librarian summaries - primary)
  - Claude Sonnet 4.5 (Liturgical Librarian summaries - fallback)
  - GPT-5.1 or GPT-5 (MasterEditor main and college editions)
  - Claude Opus 4.5 (Alternative MasterEditor with extended thinking)
- **Output**: Summary table showing per-model usage and total costs

---

## Recent Enhancements

### Sessions 200-222

| Session | Date | Feature | Description |
|---------|------|---------|-------------|
| 222 | 2025-12-26 | Priority-Based Figurative Trimming | LLM-decided term priority, sorted results, lowest-priority trimmed first |
| 220 | 2025-12-22 | Special Instruction Pipeline | Author-directed commentary revisions without altering standard pipeline |
| 219 | 2025-12-21 | Resume Feature | `--resume` flag for automatic step detection |
| 218 | 2025-12-21 | Figurative Priority Search | Sequential term processing, output simplification |
| 217 | 2025-12-13 | Trimming Duplication Fix | Intelligent section replacement logic |
| 216 | 2025-12-13 | Figurative Counting Fix | Fixed regex for parsing figurative instances |
| 215 | 2025-12-13 | Master Editor V2 | Restructured prompt, now default |
| 214 | 2025-12-11 | Stats Tracking Fix | Fixed zeros in DOCX when skipping steps |
| 213 | 2025-12-11 | Verse Commentary Fix | Fixed missing commentary in main DOCX |
| 212 | 2025-12-11 | Strategic Verse Grouping | Prevents truncation in long psalms |
| 211 | 2025-12-11 | Gemini 2.5 Pro Fallback | 1M token context for large psalms |
| 209 | 2025-12-11 | Deep Web Research | Integration of Gemini Deep Research outputs |

### Sessions 105-180 (Brief Summary)

- **Session 176**: Phrase substring matching for multi-word phrases
- **Session 175**: Performance optimization (824 → 5 queries for phrases)
- **Session 179**: Removed morphological variants from vehicle searches
- **Session 174**: Improved maqqef (־) handling in compound words
- **Session 173**: Enhanced phrase extraction with exact form preservation
- **Session 122**: Enhanced quotation emphasis (Hebrew + English)
- **Session 121**: Poetic punctuation in verse presentation
- **Session 120**: Repository cleanup (removed 47 V6 test files)
- **Sessions 118-119**: Token optimization for related psalms (50-60% reduction)
- **Sessions 115-117**: V6 complete regeneration with fresh morphology
- **Session 111**: Skipgram quality filtering
- **Sessions 109-110**: UI and configuration updates
- **Sessions 107-108**: Related Psalms integration
- **Session 105**: ETCBC morphology cache and gap penalty

---

## Technical Challenges and Solutions

### 1. Hebrew Text Processing Complexity

**Challenge**: Hebrew diacritics, cantillation marks, and morphological variations create search complexity.

**Solution**: 4-layer normalization system
- Level 0: Exact match (preserve all diacritics)
- Level 1: Voweled (strip cantillation, keep vowels)
- Level 2: Consonantal (strip vowels, keep consonants)
- Level 3: Root/Lemma (morphological root)

**Technical Pitfall Avoided**: Shin/sin dots (U+05C1–U+05C2) were initially stripped by vowel removal regex. Fixed by refining Unicode ranges.

### 2. Context Length Management

**Challenge**: Research bundles can exceed LLM token limits.

**Solution**: Intelligent, prioritized trimming strategy
- **Priority Order**: Lexicon and Commentary always preserved; Concordance trimmed first; Figurative Language trimmed second (Psalms examples prioritized)
- **Gemini Fallback**: Automatic switching to Gemini 2.5 Pro with 1M token context for large psalms
- **Character Limit**: 700,000 characters (~350K tokens)

---

## Performance and Cost Optimization

### Model Selection Strategy
| Model | Usage | Context |
|-------|-------|---------|
| Claude Sonnet 4.5 (`claude-sonnet-4-20250514`) | MacroAnalyst, MicroAnalyst, SynthesisWriter | 200K tokens |
| Gemini 2.5 Pro (`gemini-2.5-pro`) | SynthesisWriter fallback (large psalms) | 1M tokens |
| GPT-5.1 (`gpt-5.1`) | MasterEditor (default) | High reasoning effort |
| GPT-5 (`gpt-5`) | MasterEditor (legacy option) | High reasoning effort |
| Claude Opus 4.5 (`claude-opus-4-5`) | MasterEditor alternative | 64K extended thinking |
| Gemini 2.5 Pro | Liturgical Librarian summaries (primary) | Extended thinking |
| Claude Sonnet 4.5 | Liturgical Librarian summaries (fallback) | Extended thinking |

### Cost Management
- **9 Python Librarians**: Deterministic data retrieval without LLM costs
- **Cost Tracking System**: Real-time monitoring across all models
- **Token Optimization** (Sessions 118-119): 50-60% reduction in related psalms section
- **Resume Capability**: Skip completed steps to avoid redundant API calls

### Performance Metrics (V6 System)
- **Average Runtime**: 20-40 minutes per psalm (varies with complexity, includes dual editions)
- **Pipeline Steps**: 8 steps with dual-edition output
- **Research Bundle Size**: Up to 700,000 characters with intelligent trimming
- **Related Psalms**: Top 5 most related
- **Morphology Accuracy**: 93.75% test pass rate
- **Success Rate**: >95% completion rate

---

## Quality Assurance Mechanisms

### 1. Multi-Pass Validation
- Each pass builds on previous work
- Cross-validation between agents
- Consistency checking across passes
- Pipeline statistics tracking for transparency

### 2. Enhanced Quotation Verification (Session 122)
- **SynthesisWriter**: Prompts require quoting sources in Hebrew + English
- **MasterEditor**: Checks for insufficient quotations as missed opportunities
- Ensures biblical parallels are quoted, not just cited

### 3. Poetic Punctuation Verification (Session 121)
- **MasterEditor**: Ensures verses include poetic punctuation
- Verses presented with semicolons, periods, commas showing structure

### 4. Phonetic Accuracy Verification
- MasterEditor explicitly checks phonetic claims against authoritative transcriptions
- Reference transcriptions provided to all agents
- Common error detection (p/f, kh/sh, etc.)

### 5. Factual Error Detection
- Biblical accuracy verification
- Historical claim validation
- Grammatical analysis checking
- Cross-reference accuracy
- Misattribution detection

---

## Scalability and Maintenance

### Modular Architecture
- Each agent is independently testable
- Clear separation of concerns
- Easy addition of new agents

### Error Handling
- Graceful degradation on API failures
- Comprehensive logging for debugging
- Retry mechanisms for transient failures

### Testing Framework
- **Smoke testing mode** (`--smoke-test`): Generates dummy data without API calls
- Morphology test suite (93.75% pass rate)
- Resume capability testing (can restart from any step)

---

## Future Enhancements

### Completed (Sessions 105-222)
1. ✅ ETCBC Morphology Integration (Session 105)
2. ✅ Related Psalms Integration (Sessions 107-119)
3. ✅ Quality Filtering (Session 111)
4. ✅ Root Extraction Accuracy (Sessions 112-115)
5. ✅ Enhanced Quotation Emphasis (Session 122)
6. ✅ Poetic Punctuation (Session 121)
7. ✅ Token Optimization (Sessions 118-119)
8. ✅ Pipeline Tracking (Sessions 200-220)
9. ✅ Special Instruction Pipeline (Session 220)
10. ✅ Gemini 2.5 Pro Fallback (Session 211)
11. ✅ Master Editor V2 (Session 215)
12. ✅ Resume Feature (Session 219)
13. ✅ Priority-Based Figurative Trimming (Session 222)

### Planned Improvements
1. **Figurative Language Database Utilization**: Increase from current levels to 15-25% utilization
2. **Enhanced Phonetic Analysis**: Deeper prosodic and stress pattern analysis
3. **Multi-Language Support**: Improved LXX integration and analysis
4. **Advanced Morphology**: Additional rare word handling beyond ETCBC cache
5. **Performance Optimization**: Additional caching and query optimization
6. **Expanded Commentary Sources**: Integration of additional modern commentaries
7. **Cross-Testament Connections**: New Testament quotation and allusion detection

### Known Limitations
1. **Figurative Language Utilization**: Currently lower than desired hit rate
2. **Morphology Edge Cases**: 6.25% of test cases still challenging (very rare words)
3. **LXX Integration**: Text available but limited analysis integration
4. **Computational Cost**: GPT-5.1 usage for master editing is expensive

---

## Conclusion

The Psalms Commentary Pipeline represents a sophisticated integration of AI capabilities with traditional biblical scholarship. The system's success lies in its multi-step architecture with dual-edition output, which prevents common AI failure modes while leveraging the strengths of different models for specialized tasks.

**Key Technical Achievements (V6.3 System)**:
- **9 Specialized Librarians**: BDB, Concordance, Figurative, Commentary, Liturgical (Phase 4/5), Liturgical Sefaria (Phase 0 fallback), Related Psalms, Sacks, Deep Web Research
- **Dual-Edition Output**: Main scholarly edition + accessible college edition + combined document
- **Flexible Master Editor**: Support for GPT-5.1 (default), GPT-5 (legacy), or Claude Opus 4.5
- **V2 Prompt**: Restructured with explicit Deep Research guidance (Session 215)
- **Gemini 2.5 Pro Fallback**: Automatic switching for large psalms with 1M token context (Session 211)
- **Special Instruction Pipeline**: Author-directed revisions without altering standard pipeline (Session 220)
- **Resume Feature**: `--resume` flag for automatic step detection (Session 219)
- **V6 Statistical Analysis**: Fresh root extraction with 93.75% accuracy, 11,170 psalm pairs analyzed
- **Enhanced Phrase Matching**: Substring matching for phrases, word order flexibility, maqqef handling (Sessions 176-180)
- **Figurative Language Search**: Vehicle terms as hierarchical tags, priority search with LLM-decided ordering, lowest-priority trimmed first (Sessions 218-222)
- **Quality Assurance**: Multi-pass validation with quotation and punctuation verification

The system demonstrates that AI can be effectively integrated into scholarly workflows when properly architected with domain expertise, technical rigor, and continuous iterative improvement based on real-world usage and feedback.

---

## See Also

- **[CONTEXT.md](CONTEXT.md)** - Quick project overview and command reference
- **[PROJECT_STATUS.md](../session_tracking/PROJECT_STATUS.md)** - Current phase, tasks, and metrics
- **[IMPLEMENTATION_LOG.md](../session_tracking/IMPLEMENTATION_LOG.md)** - Development history and learnings
- **[PHONETIC_SYSTEM.md](PHONETIC_SYSTEM.md)** - Phonetic transcription reference
- **[PHONETIC_DEVELOPER_GUIDE.md](PHONETIC_DEVELOPER_GUIDE.md)** - Phonetic implementation guide
- **[LIBRARIAN_USAGE_EXAMPLES.md](LIBRARIAN_USAGE_EXAMPLES.md)** - Research librarian examples
- **[archived_session_details.md](../archive/documentation_cleanup/archived_session_details.md)** - Archived pre-200 session details
