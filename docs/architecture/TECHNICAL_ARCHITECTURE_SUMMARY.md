# Technical Architecture Summary: Psalms Commentary Pipeline

**Date**: 2025-12-22
**Version**: Enhanced Pipeline V6.2 (Phase 4, Sessions 200-220)
**Status**: Production System with SI Pipeline, Gemini Fallback, V2 Prompts

---

## Executive Summary

The Psalms Commentary Pipeline is a sophisticated AI-powered system that generates scholarly biblical commentary through a six-step agent architecture. The system combines multiple Large Language Models (Claude Sonnet 4.5, GPT-5.1) with eight specialized Python librarians to produce publication-quality commentary that rivals traditional scholarly work.

**Key Innovation**: The system prevents common AI failure modes through a "telescopic analysis" approach—breaking complex tasks into specialized passes, each building on previous work while maintaining focus on specific aspects of analysis.

**Latest Enhancements (Sessions 200-220)**:
- **Special Instruction Pipeline**: Author-directed commentary revisions without altering standard pipeline (Session 220)
- **Master Editor V2**: Restructured prompt with explicit Deep Research guidance, now default (Session 215)
- **Gemini 2.5 Pro Fallback**: Automatic switching for large psalms (51+ verses) with 1M token context (Session 211)
- **Resume Feature**: `--resume` flag for automatic step detection (Session 219)
- **Strategic Verse Grouping**: Prevents truncation in long psalms (Session 212)
- **Deep Web Research Integration**: Manual Gemini Deep Research outputs auto-load into research bundle (Session 209)

**Recent Enhancements (Sessions 150-180)**:
- **Phrase Substring Matching**: Multi-word phrases use substring matching while preserving exact matching for single words (Session 176)
- **Performance Optimization**: Eliminated exponential query growth for phrase searches (824 → 5 queries) (Session 175)
- **Figurative Vehicle Search Fix**: Removed morphological variants from vehicle searches, added exact match prioritization (Session 179)
- **Maqqef Handling**: Improved word boundary detection with maqqef (־) in compound words (Session 174)
- **Enhanced Phrase Extraction**: Added exact form preservation with fallback extraction from verse text (Session 173)

**Earlier Enhancements (Sessions 105-123)**:
- **V6 Scoring System**: Fresh statistical analysis with improved Hebrew morphology (Sessions 115-117)
- **Related Psalms Integration**: Automatic identification and integration of top 5 related psalms (Sessions 107-119)
- **Enhanced Quotation Emphasis**: Prompts designed to encourage generous quotation from sources (Session 122)
- **Poetic Punctuation**: LLM-generated verse presentation with poetic punctuation (Session 121)
- **Token Optimization**: 50-60% reduction in research bundle size through intelligent formatting (Sessions 118-119)
- **Pipeline Tracking**: Comprehensive statistics tracking with resume capability

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
    [Research Bundle Assembly - 10 Python Librarians]
    → Lexicon, concordance, figurative analysis, commentary,
      liturgical usage, related psalms, Sacks, Hirsch, Deep Web Research
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
2. **Librarian Agents** (10 deterministic Python data retrieval systems)
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
- **Model Options**: GPT-5.1 (`gpt-5.1`), GPT-5 (`gpt-5`), or Claude Opus 4.5 (`claude-opus-4-5`)
  - **Default**: GPT-5.1 with high reasoning effort
  - **Alternative**: Claude Opus 4.5 with extended thinking (64K token budget)
- **Prompt Versions** (Session 215):
  - **V2 (default)**: Restructured prompt with:
    - Consolidated "Ground Rules" section with unmissable Hebrew+English requirement
    - Explicit Deep Research guidance (cultural afterlife, reception history)
    - Reduced redundancy (~40% reduction in repeated instructions)
    - "Aha! moment" focus for curious lay readers
  - **OLD**: Available via `--master-editor-old` flag
- **Purpose**: Final editorial review and quality enhancement
- **Dual Output**:
  - **Pass 4**: Main edition for sophisticated lay readers (New Yorker/Atlantic audience)
  - **Pass 4b**: College edition with more accessible language for undergraduate students
- **Input**: Complete commentary, research bundle, analysis objects, psalm text
- **Output**:
  - Main: Revised introduction + verse commentary + editorial assessment
  - College: Revised introduction + verse commentary + editorial assessment (more accessible)
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
  - Phrase search via position matching
  - Scope filtering for relevant contexts

#### Figurative Language Librarian
- **Function**: Queries pre-analyzed figurative language database
- **Database**: Hierarchical JSON tags system
- **Implementation**: `src/data_sources/figurative_search.py`
- **Key Features**:
  - Hierarchical tag matching via SQL LIKE
  - Vehicle and tenor-based searches
  - Metaphor family expansion
  - Usage pattern analysis

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
  - Claude Haiku 4.5 LLM-powered intelligent summarization
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
    - Compact occurrence format: "(×1)" instead of "(1 occurrence(s))"
    - Word context extraction (±3 words) for roots instead of full verse
    - IDF filtering (only roots with IDF ≥ 1.0)
    - Removed redundant labels and scores
  - Bidirectional matching (psalm_a ↔ psalm_b)


#### Sacks Librarian
- **Function**: Retrieves Rabbi Jonathan Sacks' references to Psalms
- **Source**: Collected works and essays
- **Implementation**: `src/agents/sacks_librarian.py`
- **Key Features**:
  - Modern British Orthodox perspective
  - Philosophical and ethical interpretations
  - Contemporary relevance emphasis

#### Hirsch Librarian
- **Function**: Retrieves R. Samson Raphael Hirsch's 19th-century German commentary
- **Source**: OCR-extracted commentary from Hirsch's Psalms volume
- **Implementation**: `src/agents/hirsch_librarian.py`
- **Key Features**:
  - 19th-century German Orthodox perspective
  - Philosophical and symbolic interpretations
  - Linguistic analysis with ethical applications
  - ALWAYS included when available (no explicit request needed)

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
- **Function**: Coordinates all 10 librarians and formats results
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
  9. Hirsch Librarian (19th-century German Orthodox perspective)
  10. Deep Web Research Librarian (cultural afterlife, reception history)
- **Key Features**:
  - JSON and Markdown serialization
  - Token limit management (700,000 character capacity - Session 109)
  - **Priority-based content trimming**:
    * Lexicon and commentary always preserved
    * Concordance results trimmed first
    * Figurative language trimmed second (Psalms examples prioritized - Session 111)
  - Comprehensive research statistics tracking

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
     - `שמך` → `שם` (מ → ם final mem)
     - `שניו` → `שן` (נ → ן final nun)
- **Quality Metrics**:
  - 93.75% test pass rate (15/16 comprehensive tests)
  - 80% improvement on root extraction test cases vs. V4
  - All user-reported problem cases fixed

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
   - **Quality Filters** (Session 111):
     * Content word filtering (requires 1+ content words for 2-word patterns)
     * Pattern stoplist (excludes 41 formulaic patterns)
     * Gap penalty (10% per gap word, max 50%)

#### V6 Statistical Analysis Files (Sessions 115-117)
- **`psalm_patterns_v6.json`**: Fresh root and phrase extraction (39.67 MB)
  - 11,170 psalm pairs with patterns
  - 2,738 unique roots with IDF scores
  - Generated using Session 115 morphology fixes

- **`enhanced_scores_v6.json`**: Comprehensive scoring (107.97 MB)
  - 11,170 scored psalm pairs
  - Fresh roots + phrases from V6 patterns
  - V5 skipgrams from database (quality-filtered)
  - Full Hebrew text in all matches arrays
  - Gap penalty and content word bonus applied

- **`top_550_connections_v6.json`**: Top relationships (13.35 MB)
  - Score range: 19,908.71 to 211.50
  - Top connection: Psalms 14-53 (nearly identical)
  - Used by Related Psalms Librarian

#### RAG Document Integration
- **Analytical Framework**: `docs/analytical_framework_for_RAG.md`
- **Psalm Function Database**: `docs/psalm_function_for_RAG.json`
- **Ugaritic Comparisons**: `docs/ugaritic.json`
- **LXX Text**: Integrated via Sefaria API

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
  - **Step-by-step tracking**:
    * Input/output character and token counts for each step
    * Duration tracking for each pipeline step
    * Model usage recording (which LLM used for each step)
  - **Research statistics**:
    * Lexicon, concordance, figurative, commentary request counts
    * Research bundle size metrics
    * Related psalms count and list
    * Ugaritic parallels tracking
  - **Analysis metrics**:
    * Macro and micro questions tracked
    * Verse count
    * Completion timestamps
  - **Resume capability**:
    * Saves JSON snapshot after each step
    * Can resume from any step using `--skip-*` flags
    * Preserves existing statistics when resuming
  - **Output formats**:
    * JSON format: `psalm_NNN_pipeline_stats.json` (machine-readable)
    * Markdown report: `psalm_NNN_pipeline_summary.md` (human-readable)

#### Pipeline Control Flags
- **`--skip-macro`**: Use existing macro analysis file
- **`--skip-micro`**: Use existing micro analysis file
- **`--skip-synthesis`**: Use existing synthesis files
- **`--skip-master-edit`**: Use existing master-edited files
- **`--skip-college`**: Skip college commentary generation (use existing file)
- **`--skip-print-ready`**: Skip print-ready formatting step
- **`--skip-word-doc`**: Skip .docx generation step
- **`--skip-combined-doc`**: Skip combined .docx generation (main + college in one document)
- **`--resume`**: **NEW (Session 219)** - Resume from last completed step (auto-detects based on existing files)
- **`--smoke-test`**: Generate dummy data without API calls
- **`--skip-default-commentaries`**: Use selective commentary mode
- **`--master-editor-model`**: Model to use for master editor (choices: gpt-5, gpt-5.1, claude-opus-4-5)
- **`--master-editor-old`**: **NEW (Session 215)** - Use OLD prompt (V2 is now default)
- **`--delay SECONDS`**: Rate limit delay between API-heavy steps (default: 120)

#### Special Instruction Pipeline (Session 220)
- **Script**: `python scripts/run_si_pipeline.py PSALM_NUMBER`
- **Input**: Special instruction file at `data/special_instructions/special_instructions_Psalm_NNN.txt`
- **Output Files** (all with `_SI` suffix):
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
- **Key Design**:
  - Extends `MasterEditorV2` via inheritance (`MasterEditorSI` class)
  - SPECIAL AUTHOR DIRECTIVE section in prompt (highest priority)
  - Never overwrites original pipeline files
  - Separate stats tracking

### 6. Output Generation Pipeline

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
  1. **Main Edition** (`psalm_NNN_commentary.docx`): Full scholarly commentary for sophisticated lay readers
  2. **College Edition** (`psalm_NNN_commentary_college.docx`): More accessible version for undergraduates
  3. **Combined Edition** (`psalm_NNN_commentary_combined.docx`): Both main and college in one document
- **Features**:
  - Professional formatting with Hebrew fonts
  - Print-ready layout
  - **Metadata inclusion**:
    * Pipeline statistics (models used, durations, token counts)
    * Related psalms count and list (Session 110)
    * Research bundle statistics
    * Date produced timestamp
  - **Sefaria footnote stripping** (Session 109): Removes `-c`, `-d` markers from English text
  - Phonetic transcription italicization
  - Divine name formatting
  - Bidirectional text handling for Hebrew/English

### 7. Logging and Observability

#### Dual-Format Logging System
- **Console Output**: Human-readable progress tracking
- **JSON Logs**: Machine-readable metrics and debugging
- **Implementation**: `src/utils/logger.py`

#### Key Metrics Tracked
- Agent completion times
- Token usage and costs
- API call success rates
- Research bundle statistics
- Figurative language utilization rates

#### Cost Tracking System
- **Function**: Real-time API usage and cost monitoring
- **Implementation**: `src/utils/cost_tracker.py`
- **Key Features**:
  - Tracks token usage (input and output) for all LLM calls
  - Calculates costs based on model-specific pricing
  - Supports multiple models (Claude Sonnet 4.5, Haiku 4.5, GPT-5, GPT-5.1, Claude Opus 4.5)
  - Provides cost summaries at end of pipeline
  - Enables cost projections and budgeting
- **Models Tracked**:
  - Claude Sonnet 4.5 (MacroAnalyst, MicroAnalyst, SynthesisWriter)
  - Claude Haiku 4.5 (Liturgical Librarian summaries)
  - GPT-5.1 or GPT-5 (MasterEditor main and college editions)
  - Claude Opus 4.5 (Alternative MasterEditor with extended thinking)
- **Output**: Summary table showing per-model usage and total costs

---

## Latest Enhancements (Sessions 200-220)

### Session 220 (2025-12-22): Special Instruction Pipeline
**Objective**: Create supplementary pipeline for author-directed commentary revisions

**Problems Identified**:
- Need for "V2" rewrites based on specific thematic ideas without altering standard pipeline
- Author wants ability to inject overriding instructions into Master Editor generation

**Solutions Implemented**:
1. Created `src/agents/master_editor_si.py` extending `MasterEditorV2` via inheritance
2. Added `MASTER_EDITOR_PROMPT_SI` and `COLLEGE_EDITOR_PROMPT_SI` with "SPECIAL AUTHOR DIRECTIVE" section
3. Created `scripts/run_si_pipeline.py` for dedicated SI workflow
4. All outputs use `_SI` suffix (never overwrites original files)
5. Copies original pipeline stats to new `_SI.json` file
6. Generates three .docx documents: Main SI, College SI, Combined SI

**Key Design Constraints**:
- NO modifications to `scripts/run_enhanced_pipeline.py` or `src/agents/master_editor.py`
- Uses "SI" naming convention throughout
- Strict input validation (exits if analysis files missing)

### Session 219 (2025-12-21): Pipeline Skip Logic Fix & Resume Feature
**Objective**: Fix skip flags being ignored and add resume functionality

**Problems Identified**:
- Skip flags used OR condition: `elif not skip_step OR not file_exists()`
- Users surprised when explicit skip commands were ignored

**Solutions Implemented**:
1. Fixed skip logic to simple condition: `elif not skip_step:`
2. Added `--resume` flag for automatic step detection
3. Added dependency checking for skipped steps
4. Updated help documentation

### Session 218 (2025-12-21): Prioritized Figurative Language Search & Output Simplification
**Objective**: Fix figurative language search dominated by random matches

**Solutions Implemented**:
1. Implemented `_priority_search` for sequential term processing
2. Removed "Core pattern" and "Top 3" sections
3. Simplified to list up to 20 instances directly
4. Updated `.gitignore` to exclude `output/` and `logs/`

### Session 217 (2025-12-13): Sections Trimmed Duplication Fix
**Objective**: Fix duplicate entries when sections trimmed multiple times

**Solutions Implemented**:
1. Intelligent section replacement logic
2. Handle Related Psalms format changes
3. Prevent duplicates before adding

### Session 216 (2025-12-13): Figurative Language Counting Fix
**Objective**: Fix figurative language count showing 0 when skipping steps

**Solutions Implemented**:
1. Updated regex to match actual markdown format
2. Added `re.MULTILINE` flag
3. Count unique verse references appropriately

### Session 215 (2025-12-13): Master Editor V2 Prompt Restructure
**Objective**: Restructure prompt for better Deep Research utilization

**Problems Identified**:
- ~440 lines with accumulated cruft
- Hebrew+English rule repeated 15+ times
- Deep Research not explicitly surfaced

**Solutions Implemented**:
1. Created restructured prompt with clear organization
2. Explicit Deep Research guidance section
3. "Aha! Moment" focus framing
4. Made V2 the default
5. Fixed liturgical section formatting

**Results**:
- A/B testing on Psalm 126 showed significantly better output
- Richer integration of research materials
- More provocative section headers

### Session 214 (2025-12-11): Pipeline Stats Tracking Fix
**Objective**: Fix zeros in DOCX methods section when skipping steps

**Solutions Implemented**:
1. Fixed lexicon count regex to match `### עַנְוָה` format
2. Added verse count tracking from database when `--skip-macro`

### Session 213 (2025-12-11): Main DOCX Verse-by-Verse Commentary Fix
**Objective**: Fix missing verse commentary in main DOCX

**Solutions Implemented**:
1. Copied working regex from combined document generator
2. Enhanced pattern for all formats (single, ranges, descriptions)
3. Added range support with start/end tracking

### Session 212 (2025-12-11): Psalm 18 Pipeline Fixes + Strategic Verse Grouping
**Objective**: Fix multiple issues with 51-verse psalm processing

**Solutions Implemented**:
1. Fixed JSON truncation in MicroAnalyst (max_tokens too low)
2. Fixed max tokens exceeding 64K limit
3. Fixed missing trimmed research file
4. Fixed N/A in bibliographical summary
5. Fixed DOCX markdown heading format
6. Fixed combined DOCX verse range merging

**Strategic Verse Grouping Feature**:
- Updated prompts with pacing guidance
- College Editor changed from "NEVER combine" to strategic grouping
- Equal treatment for all verses, no rushing

### Session 211 (2025-12-11): Gemini 2.5 Pro Fallback + Improved Trimming Strategy
**Objective**: Prevent critical content loss in large psalms

**Problems Identified**:
- Session 210's aggressive trimming removed Liturgical Usage, Sacks, RAG

**Solutions Implemented**:
1. New trimming strategy preserving critical content
2. Increased character limits (350K intro, 300K verse commentary)
3. Gemini 2.5 Pro fallback with 1M token context
4. Enhanced stats tracking

**Key Benefit**: Never trim Lexicon, Commentaries, Liturgical, Sacks, RAG, Concordance, Deep Research

### Session 209 (2025-12-11): Deep Web Research Integration + Progressive Trimming Fix
**Objective**: Add support for Gemini Deep Research outputs

**Completed**:
1. Deep Web Research Feature:
   - Created `data/deep_research/` directory
   - File naming: `psalm_NNN_deep_research.txt`
   - Auto-loads into research bundle

2. Progressive Trimming Rewrite:
   - Fixed Psalm 18 token overflow (211,252 tokens)
   - Progressive reduction: 75% → 50% → 25% → remove
   - Trimming order: Related Psalms → Figurative → Concordance → Deep Research

---

## Enhancements (Sessions 105-123)

### Session 123: User Guide Documentation Updates
- Created comprehensive suggestions for updating "How Psalms Readers Guide works.docx"
- Documented all user-facing enhancements from Sessions 105-122
- Maintained friendly, accessible voice for educated lay readers

### Session 122: Enhanced Quotation Emphasis
**Problem**: Final output mentioned interesting sources but didn't quote them enough
**Solution**: Strengthened prompts in both SynthesisWriter and MasterEditor to:
- Require quoting biblical parallels in Hebrew + English (not just citing)
- Require quoting liturgical texts when mentioned
- Require showing linguistic patterns with quoted examples
- Added WEAK vs. STRONG examples throughout prompts
**Impact**: Readers now see actual Hebrew texts, not just citations

### Session 121: Poetic Punctuation in Verse Presentation
**Change**: Removed programmatic verse insertion, rely on LLM to provide punctuated verses
**Implementation**:
- Updated master_editor.py prompts (3 locations)
- Updated synthesis_writer.py prompts (2 locations)
- Removed programmatic insertion from document_generator.py and commentary_formatter.py
**Impact**: Verses now include poetic punctuation (semicolons, periods, commas) showing structure
**Example**: "בְּקׇרְאִי עֲנֵנִי אֱלֹקֵי צִדְקִי; בַּצָּר הִרְחַבְתָּ לִּי; חׇנֵּנִי וּשְׁמַע תְּפִלָּתִי."

### Session 120: Repository Cleanup
- Removed 47 files from V6 development (test scripts, validation artifacts, old V4/V5 data)
- Freed ~200MB disk space
- Repository now clean and production-ready

### Sessions 118-119: Token Optimization for Related Psalms
**Optimizations**:
1. Removed IDF scores from root displays (~10 chars/root saved)
2. Compact occurrence format: "(×1)" instead of "(1 occurrence(s))"
3. Removed "Consonantal:" prefix
4. Simplified psalm references: "Psalm X" instead of "In Psalm X"
5. Smart context extraction for roots (matched word ±3 words instead of full verse)
6. Reduced max matching psalms from 8 → 5
7. Filtered low-IDF roots (only display IDF ≥ 1.0)
**Impact**: 50-60% total token reduction in related psalms section while improving clarity

### Sessions 115-117: V6 Complete Regeneration
**Objective**: Fix root extraction errors by regenerating all statistical data with improved morphology
**V6 Improvements**:
1. **Session 115 Morphology Fixes**:
   - Hybrid stripping approach (adaptive prefix/suffix order)
   - Plural ending protection (stricter minimums for ים/ות)
   - Final letter normalization (ך ם ן ף ץ)
   - 93.75% test pass rate, all user-reported errors fixed

2. **Session 117 Fresh Generation**:
   - `psalm_patterns_v6.json`: 11,170 pairs, 2,738 unique roots (39.67 MB)
   - `enhanced_scores_v6.json`: Fresh patterns + V5 skipgrams (107.97 MB)
   - `top_550_connections_v6.json`: Score range 19,908.71 to 211.50 (13.35 MB)

**Validation Results** - All passed:
- `שִׁ֣יר חָדָ֑שׁ` → "שיר חדש" ✓ (was "יר חדש" in V5)
- `וּמִשְׁפָּ֑ט` → "שפט" ✓ (was "פט" in V5)
- `שָׁמַ֣יִם` → "שמים" ✓ (was "מים" in V5)
- `שִׁנָּ֣יו` → "שן" ✓ (was "ני" in V5)

### Session 111: Skipgram Quality Filtering (V5)
**Implemented Three Priority Improvements**:
1. **Content Word Filtering**: Created Hebrew word classifier, filtered 7.6% of formulaic patterns
2. **Pattern Stoplist**: 41 high-frequency formulaic patterns removed
3. **Content Word Bonus**: 25-50% scoring boost for multi-content patterns
**Impact**: 34.2% reduction in average skipgrams per connection (4.4 → 2.9)

### Sessions 109-110: UI and Configuration Updates
- Fixed footnote markers in DOCX English translation
- Increased synthesis character limit to 700,000 (350K tokens)
- Limited related psalms to top 8 (later reduced to 5 in Session 119)
- Added related psalms list to JSON export and DOCX display

### Sessions 107-108: Related Psalms Integration
**New Feature**: Automatic identification and integration of related psalms
**Implementation**:
- Created `related_psalms_librarian.py`
- Integrated into ResearchBundle
- Added pipeline stats tracking
- Fixed bugs: shared roots loading, display formatting, field names
**Impact**: Provides cross-psalm intertextual connections for synthesis and editing

### Session 105: ETCBC Morphology & Gap Penalty
**Two Major Improvements**:
1. **ETCBC Morphology Cache**: 5,353 authoritative mappings from BHSA 2021 database
2. **Gap Penalty for Skipgrams**: 10% per gap word (max 50%), values contiguous patterns higher
**Impact**: 80% improvement in root extraction on test cases

---

## Technical Challenges and Solutions

### 1. Hebrew Text Processing Complexity

**Challenge**: Hebrew diacritics, cantillation marks, and morphological variations create search complexity.

**Solution**: 4-layer normalization system
```python
# Example: Search for "כל" (all)
# Level 0: כָּל (exact with vowels)
# Level 1: כל (voweled, no cantillation)
# Level 2: כל (consonantal)
# Level 3: כל (root form)
```

**Technical Pitfall Avoided**: Shin/sin dots (U+05C1–U+05C2) were initially stripped by vowel removal regex. Fixed by refining Unicode ranges.

### 2. Morphological Variation Explosion

**Challenge**: Early prototype generated 200+ variations by combining all patterns.

**Solution**: Strategic pattern selection
- Nouns: suffixes only
- Verbs: stems + imperfect prefixes  
- Particles: prefix patterns only
- Result: 66 optimized variations

### 3. Sefaria API Response Handling

**Challenge**: Sefaria lexicon endpoint returns list structure, not dictionary.

**Solution**: Recursive extraction from nested "senses" arrays
```python
def extract_definitions(entry_list):
    """Handle Sefaria's list-based response format."""
    definitions = []
    for entry in entry_list:
        if 'senses' in entry:
            definitions.extend(extract_definitions(entry['senses']))
        else:
            definitions.append(entry.get('definition', ''))
    return definitions
```

### 4. Windows Console UTF-8 Encoding

**Challenge**: Hebrew text caused `UnicodeEncodeError` on Windows console.

**Solution**: Explicit encoding configuration
```python
import sys
sys.stdout.reconfigure(encoding='utf-8')
```

### 5. SQLite Multi-Column DISTINCT Limitation

**Challenge**: SQLite doesn't support `COUNT(DISTINCT col1, col2)`.

**Solution**: String concatenation approach
```sql
SELECT COUNT(DISTINCT book_name || '-' || chapter || '-' || verse)
FROM concordance
```

### 6. Context Length Management

**Challenge**: Research bundles can exceed LLM token limits.

**Solution**: Intelligent, prioritized trimming strategy
- **Priority Order**: Lexicon and Commentary sections are always preserved. Concordance results are trimmed first. If more space is needed, the Figurative Language section is trimmed next.
- **Prioritized Figuration Trimming**: When the Figurative Language section is trimmed, the logic now prioritizes keeping examples from the Book of Psalms. Instances from other biblical books are discarded first, ensuring the most relevant context is preserved for the LLM.
- **Preservation of Critical Information**: This multi-level strategy ensures that the most critical information (lexicon, commentary, and Psalms-specific figuration) is protected from truncation.
- **Character Limit Increase** (Session 109): Raised from 250K-330K to 700,000 characters (~350K tokens)

### 7. Hebrew Root Extraction Complexity (Sessions 112-115)

**Challenge**: Algorithmic root extraction from inflected Hebrew words is complex due to:
- Multiple prefix/suffix combinations (ב, ל, מ, ש, etc.)
- Dual/plural endings that shouldn't be stripped (שמים is "heavens", not שם + plural)
- Final letter normalization requirements (מ → ם, נ → ן, etc.)
- ש-initial roots being over-stripped (שקרים → "קר" instead of "שקר")

**Solutions Applied (V6)**:
1. **ETCBC Morphology Cache** (Session 105): 5,353 authoritative mappings for cache hits
2. **Hybrid Stripping Approach** (Session 115): Adaptive strategy
   - Prefix-first for simple prefixes: `בשמים` → `שמים`
   - Suffix-first for ש-words: `שקרים` → `שקר`
3. **Plural Protection** (Session 115): Stricter minimums to prevent over-stripping
4. **Final Letter Normalization** (Session 115): Automatic conversion to final forms

**Results**: 93.75% test pass rate, 80% improvement on test cases, all user-reported errors fixed

---

## Performance and Cost Optimization

### Model Selection Strategy
- **Claude Sonnet 4.5** (`claude-sonnet-4-20250514`):
  - MacroAnalyst (Pass 1): Structural analysis with extended thinking
  - MicroAnalystV2 (Pass 2): Discovery-driven research with extended thinking
  - SynthesisWriter (Pass 3): Commentary synthesis
    - **Gemini 2.5 Pro fallback** for large psalms (research bundle > 350K chars)
    - Gemini provides 1M token context vs Claude's 200K
- **GPT-5.1** (`gpt-5.1`) or **GPT-5** (`gpt-5`) or **Claude Opus 4.5** (`claude-opus-4-5`):
  - MasterEditor (Pass 4 & 4b): Final editorial review with 350K character capacity
    - **Default**: GPT-5.1 with high reasoning effort
    - **Alternative**: Claude Opus 4.5 with extended thinking (64K token budget)
    - **V2 prompt**: Default (Session 215) - restructured with explicit Deep Research guidance
    - **OLD prompt**: Available via `--master-editor-old` flag
  - Dual output: Main edition + College edition
- **Gemini 2.5 Pro** (`gemini-2.5-pro`):
  - SynthesisWriter fallback for large psalms (Session 211)
  - 1M token context window
- **Claude Haiku 4.5**:
  - Liturgical Librarian: Intelligent summarization of liturgical usage
- **Python Librarians**: 10 deterministic data retrieval systems (no LLM costs for core research)

### Cost Management
- **10 Python Librarians**: Deterministic data retrieval without LLM costs
  - BDB, Concordance, Figurative, Commentary, Liturgical (Phase 4/5), Liturgical Sefaria (Phase 0 fallback), Related Psalms, Sacks, Hirsch, Deep Web Research
- **Cost Tracking System**: Real-time monitoring of API usage and costs across all models
  - Tracks input/output tokens for each LLM call
  - Calculates costs based on model-specific pricing
  - Provides end-of-pipeline cost summary
- **Structured Outputs**: JSON schema validation reduces token usage
- **Efficient Research**: Targeted queries vs. broad searches
- **Token Optimization** (Sessions 118-119): 50-60% reduction in related psalms section
- **Prompt Efficiency**: Enhanced prompts focus on quotations without excessive length
- **Resume Capability**: Skip completed steps to avoid redundant API calls

### Performance Metrics (V6 System)
- **Average Runtime**: 20-40 minutes per psalm (varies with complexity, includes dual editions)
- **Pipeline Steps**: 8 steps (Macro → Micro → Synthesis → Master Edit → College Edit → Print-Ready → Main DOCX → College DOCX → Combined DOCX)
- **Research Bundle Size**: Up to 700,000 characters (~350K tokens) with intelligent trimming
- **Related Psalms**: Top 5 most related (down from 8, optimized for token efficiency)
- **Morphology Accuracy**: 93.75% test pass rate with V6 improvements
- **Success Rate**: >95% completion rate
- **Token Tracking**: Comprehensive per-step tracking with PipelineSummaryTracker
- **Cost Tracking**: Real-time monitoring via CostTracker for all LLM calls

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
- Requires liturgical texts to be quoted when mentioned
- Validates linguistic patterns shown with quoted examples

### 3. Poetic Punctuation Verification (Session 121)
- **MasterEditor**: Ensures verses include poetic punctuation
- Verses presented with semicolons, periods, commas showing structure
- LLM-generated punctuation (not programmatic insertion)
- Example: "בְּקׇרְאִי עֲנֵנִי אֱלֹקֵי צִדְקִי; בַּצָּר הִרְחַבְתָּ לִּי; חׇנֵּנִי וּשְׁמַע תְּפִלָּתִי."

### 4. Phonetic Accuracy Verification
- MasterEditor explicitly checks phonetic claims against authoritative transcriptions
- Reference transcriptions provided to all agents
- Common error detection (p/f, kh/sh, etc.)
- Stress marking from cantillation preserved in transcriptions

### 5. Factual Error Detection
- Biblical accuracy verification
- Historical claim validation
- Grammatical analysis checking
- Cross-reference accuracy
- Misattribution detection

### 6. Source Integration and Cross-Validation
- 8 librarians provide multiple perspectives
- Traditional Jewish commentaries (7 sources)
- Related psalms statistical validation (V6 scoring)
- Liturgical usage verification
- Intertextual connection verification
- ANE parallel validation

---

## Scalability and Maintenance

### Modular Architecture
- Each agent is independently testable
- Clear separation of concerns
- Easy addition of new agents

### Database Design
- Normalized schema for efficient queries
- Indexed fields for fast searches
- Extensible structure for new data types

### Error Handling
- Graceful degradation on API failures
- Comprehensive logging for debugging
- Retry mechanisms for transient failures

### Testing Framework
- Unit tests for individual components
- Integration tests for full pipeline
- **Smoke testing mode** (`--smoke-test`): Generates dummy data without API calls
  - Validates pipeline flow without LLM costs
  - Tests file I/O and formatting logic
  - Rapid iteration during development
- Morphology test suite (93.75% pass rate)
- Resume capability testing (can restart from any step)

---

## Future Enhancements

### Completed (Sessions 105-123)
1. ✅ **ETCBC Morphology Integration**: 5,353 authoritative mappings (Session 105)
2. ✅ **Related Psalms Integration**: Statistical analysis with V6 scoring (Sessions 107-119)
3. ✅ **Quality Filtering**: Content word filtering and pattern stoplist (Session 111)
4. ✅ **Root Extraction Accuracy**: 93.75% test pass rate (Sessions 112-115)
5. ✅ **Enhanced Quotation Emphasis**: Prompts encourage Hebrew + English quotations (Session 122)
6. ✅ **Poetic Punctuation**: LLM-generated verse presentation (Session 121)
7. ✅ **Token Optimization**: 50-60% reduction in related psalms section (Sessions 118-119)
8. ✅ **Pipeline Tracking**: Comprehensive statistics with resume capability

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

The Psalms Commentary Pipeline represents a sophisticated integration of AI capabilities with traditional biblical scholarship. The system's success lies in its eight-step architecture (with dual-edition output), which prevents common AI failure modes while leveraging the strengths of different models for specialized tasks.

The technical implementation addresses complex challenges in Hebrew text processing, morphological analysis, and scholarly research integration. The result is a system that produces commentary of sufficient quality for scholarly publication while maintaining efficiency and cost-effectiveness.

**Key Technical Achievements (V6.2 System)**:
- **10 Specialized Librarians**: BDB, Concordance, Figurative, Commentary, Liturgical (Phase 4/5), Liturgical Sefaria (Phase 0 fallback), Related Psalms, Sacks, Hirsch, Deep Web Research
- **Dual-Edition Output**: Main scholarly edition + accessible college edition + combined document
- **Flexible Master Editor**: Support for GPT-5.1, GPT-5, or Claude Opus 4.5 with configurable model selection
- **V2 Prompt (Session 215)**: Restructured with explicit Deep Research guidance, now default
- **Gemini 2.5 Pro Fallback (Session 211)**: Automatic switching for large psalms with 1M token context
- **Special Instruction Pipeline (Session 220)**: Author-directed revisions without altering standard pipeline
- **Resume Feature (Session 219)**: `--resume` flag for automatic step detection
- **V6 Statistical Analysis**: Fresh root extraction with 93.75% accuracy, 11,170 psalm pairs analyzed
- **Related Psalms Integration**: Top 5 connections with intelligent token optimization (50-60% reduction)
- **Enhanced Quotation System**: Prompts encourage generous Hebrew + English quotations
- **Poetic Punctuation**: LLM-generated verse presentation with structural markers
- **Pipeline Tracking**: Comprehensive statistics with resume capability
- **Cost Tracking**: Real-time API usage and cost monitoring across all models
- **Robust Hebrew Processing**: 4-layer normalization, ETCBC cache, hybrid root extraction
- **Quality Assurance**: Multi-pass validation with quotation and punctuation verification
- **Cost Optimization**: Strategic model selection, deterministic librarians, token efficiency

**Recent Evolution (Sessions 200-220)**:
The system has undergone significant enhancement through 21 development sessions, implementing a Special Instruction pipeline for author-directed revisions, adding Gemini 2.5 Pro fallback for large psalms, restructuring the Master Editor prompt to V2, adding resume capability, and implementing strategic verse grouping to prevent truncation. These enhancements demonstrate the system's continued refinement and adaptation to production use.

The system demonstrates that AI can be effectively integrated into scholarly workflows when properly architected with domain expertise, technical rigor, and continuous iterative improvement based on real-world usage and feedback.

---

## See Also

- **[CONTEXT.md](CONTEXT.md)** - Quick project overview and command reference
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current phase, tasks, and metrics
- **[IMPLEMENTATION_LOG.md](IMPLEMENTATION_LOG.md)** - Development history and learnings
- **[PHONETIC_SYSTEM.md](PHONETIC_SYSTEM.md)** - Phonetic transcription reference
- **[PHONETIC_DEVELOPER_GUIDE.md](PHONETIC_DEVELOPER_GUIDE.md)** - Phonetic implementation guide
- **[LIBRARIAN_USAGE_EXAMPLES.md](LIBRARIAN_USAGE_EXAMPLES.md)** - Research librarian examples

