# Script References

**Quick reference for all Python scripts in the Psalms AI Analysis project.**  
Always read this file first when you need to find code.

---

## Pipeline Runners (`scripts/`)

| Script | Namespace | Description | Link |
|--------|-----------|-------------|------|
| `run_enhanced_pipeline.py` | `scripts` | **NEW DEFAULT**: Master Writer pipeline (formerly TEST). Single-pass generation from research inputs. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/run_enhanced_pipeline.py) |
| `run_enhanced_pipeline_with_synthesis.py` | `scripts` | **LEGACY**: Original Synthesis Writer pipeline (Pass 3 Synthesis → Pass 4 Master Editor). | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/run_enhanced_pipeline_with_synthesis.py) |
| `run_si_pipeline.py` | `scripts` | **NEW SI**: Special Instruction pipeline using Master Writer approach. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/run_si_pipeline.py) |
| `run_si_pipeline_with_synthesis.py` | `scripts` | **LEGACY SI**: Special Instruction pipeline using Synthesis Writer approach. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/run_si_pipeline_with_synthesis.py) |
| `converse_with_editor.py` | `scripts` | Enables multi-turn conversation with Master Editor (GPT-5.1) about a completed psalm commentary with full research context. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/converse_with_editor.py) |

---

## Analysis Agents (`src/agents/`)

| Script | Namespace | Description | Link |
|--------|-----------|-------------|------|
| `macro_analyst.py` | `src.agents` | Pass 1: Produces chapter-level thesis and structural framework using Claude Opus 4.6 with RAG context. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/macro_analyst.py) |
| `micro_analyst.py` | `src.agents` | Pass 2: Discovery-driven verse-by-verse research using Claude Opus 4.6 with adaptive thinking. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/micro_analyst.py) |
| `synthesis_writer.py` | `src.agents` | Pass 3: Final commentary synthesis combining macro thesis, micro discoveries, and research bundle. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/synthesis_writer.py) |
| `master_editor.py` | `src.agents` | Pass 4: Final review and enhancement agent (Main and College editions). Includes robust question fallback logic. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/master_editor.py) |
| `master_editor_si.py` | `src.agents` | Special Instruction variant of Master Editor that supports author directives for alternative versions. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/master_editor_si.py) |
| `master_editor_old.py` | `src.agents` | Legacy Master Editor implementation (archived). | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/master_editor_old.py) |
| `phonetic_analyst.py` | `src.agents` | Transcribes Hebrew text into phonetic/syllabic structure based on reconstructed Biblical Hebrew phonology. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/phonetic_analyst.py) |

---

## Librarian Agents (`src/agents/`)

| Script | Namespace | Description | Link |
|--------|-----------|-------------|------|
| `research_assembler.py` | `src.agents` | Coordinates all librarian agents to assemble comprehensive research bundles for psalm analysis. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/research_assembler.py) |
| `bdb_librarian.py` | `src.agents` | Fetches Hebrew lexicon entries (BDB + Klein Dictionary) from Sefaria API. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/bdb_librarian.py) |
| `concordance_librarian.py` | `src.agents` | Searches Hebrew concordance database with automatic phrase variation detection. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/concordance_librarian.py) |
| `figurative_librarian.py` | `src.agents` | Queries figurative language database (Psalms + Pentateuch) with hierarchical tag support. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/figurative_librarian.py) |
| `figurative_curator.py` | `src.agents` | LLM-enhanced agent (Gemini 3 Pro) that curates and synthesizes figurative language insights. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/figurative_curator.py) |
| `liturgical_librarian.py` | `src.agents` | Queries phrase-level liturgical index with intelligent aggregation and optional LLM summarization. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/liturgical_librarian.py) |
| `liturgical_librarian_sefaria.py` | `src.agents` | Alternative liturgical librarian using Sefaria API directly. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/liturgical_librarian_sefaria.py) |
| `commentary_librarian.py` | `src.agents` | Fetches traditional Jewish commentaries (Rashi, Ibn Ezra, Radak, etc.) from Sefaria API. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/commentary_librarian.py) |
| `sacks_librarian.py` | `src.agents` | Loads and formats Rabbi Jonathan Sacks' references to Psalms from his collected works. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/sacks_librarian.py) |
| `related_psalms_librarian.py` | `src.agents` | Retrieves related psalms with shared roots, phrases, and skipgrams from top connections analysis. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/related_psalms_librarian.py) |
| `rag_manager.py` | `src.agents` | Manages RAG documents (analytical framework, psalm functions, Ugaritic parallels) for agent prompts. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/rag_manager.py) |
| `scholar_researcher.py` | `src.agents` | Coordinates research requests by generating specific requests for librarian agents from macro overview. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/scholar_researcher.py) |
| `question_curator.py` | `src.agents` | Generates "Questions for the Reader" from macro/micro analysis using Claude Opus 4.5. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/question_curator.py) |
| `insight_extractor.py` | `src.agents` | **NEW**: Filters research materials for transformative insights using Claude Opus 4.5. Now uses full psalm text and macro context. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/insight_extractor.py) |

---

## Concordance (`src/concordance/`)

| Script | Namespace | Description | Link |
|--------|-----------|-------------|------|
| `search.py` | `src.concordance` | Hebrew concordance search with single/multi-word phrase support and multiple normalization levels. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/concordance/search.py) |
| `hebrew_text_processor.py` | `src.concordance` | Text processing utilities for Hebrew normalization and word splitting. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/concordance/hebrew_text_processor.py) |
| `morphology_variations.py` | `src.concordance` | Generates morphological variations (prefixes, suffixes) for Hebrew words. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/concordance/morphology_variations.py) |
| `root_matcher.py` | `src.concordance` | Hebrew root matching utilities for concordance searches. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/concordance/root_matcher.py) |

---

## Data Sources (`src/data_sources/`)

| Script | Namespace | Description | Link |
|--------|-----------|-------------|------|
| `tanakh_database.py` | `src.data_sources` | SQLite database manager for storing biblical texts with concordance indexing. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/data_sources/tanakh_database.py) |
| `sefaria_client.py` | `src.data_sources` | API client for fetching biblical texts and commentaries from Sefaria. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/data_sources/sefaria_client.py) |
| `create_liturgy_db.py` | `src.data_sources` | Creates and populates the liturgy database from source data. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/data_sources/create_liturgy_db.py) |

---

## Hebrew Analysis (`src/hebrew_analysis/`)

| Script | Namespace | Description | Link |
|--------|-----------|-------------|------|
| `morphology.py` | `src.hebrew_analysis` | Hebrew morphological analysis utilities. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/hebrew_analysis/morphology.py) |
| `root_extractor_v2.py` | `src.hebrew_analysis` | Extracts Hebrew roots from words. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/hebrew_analysis/root_extractor_v2.py) |
| `word_classifier.py` | `src.hebrew_analysis` | Classifies Hebrew words by type and structure. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/hebrew_analysis/word_classifier.py) |
| `cache_builder.py` | `src.hebrew_analysis` | Builds caches for Hebrew analysis operations. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/hebrew_analysis/cache_builder.py) |
| `demonstrate_expected_results.py` | `src.hebrew_analysis` | Demonstrates expected results for Hebrew analysis features. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/hebrew_analysis/demonstrate_expected_results.py) |

---

## Liturgy (`src/liturgy/`)

| Script | Namespace | Description | Link |
|--------|-----------|-------------|------|
| `liturgy_indexer.py` | `src.liturgy` | Indexes liturgical texts for phrase-level searching. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/liturgy/liturgy_indexer.py) |
| `phrase_extractor.py` | `src.liturgy` | Extracts phrases from liturgical texts for indexing. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/liturgy/phrase_extractor.py) |
| `sefaria_json_parser.py` | `src.liturgy` | Parses Sefaria JSON exports for liturgical data. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/liturgy/sefaria_json_parser.py) |
| `sefaria_links_harvester.py` | `src.liturgy` | Harvests links between psalms and liturgical texts from Sefaria. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/liturgy/sefaria_links_harvester.py) |
| `sefaria_liturgy_harvester.py` | `src.liturgy` | Harvests liturgical text content from Sefaria API. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/liturgy/sefaria_liturgy_harvester.py) |
| `sefaria_metadata_scraper.py` | `src.liturgy` | Scrapes metadata about liturgical texts from Sefaria. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/liturgy/sefaria_metadata_scraper.py) |

---

## Thematic / RAG (`src/thematic/`)

| Script | Namespace | Description | Link |
|--------|-----------|-------------|------|
| `chunk_schemas.py` | `src.thematic` | Defines schemas for RAG document chunks. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/thematic/chunk_schemas.py) |
| `corpus_builder.py` | `src.thematic` | Builds thematic corpus for RAG retrieval. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/thematic/corpus_builder.py) |
| `embedding_service.py` | `src.thematic` | Embedding generation service for RAG vector search. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/thematic/embedding_service.py) |
| `vector_store.py` | `src.thematic` | Vector store management for RAG similarity search. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/thematic/vector_store.py) |

---

## Utilities (`src/utils/`)

| Script | Namespace | Description | Link |
|--------|-----------|-------------|------|
| `research_trimmer.py` | `src.utils` | **NEW**: Utility for intelligently trimming research bundles to fit token limits. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/utils/research_trimmer.py) |
| `document_generator.py` | `src.utils` | Generates print-ready Word (.docx) documents from pipeline outputs. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/utils/document_generator.py) |
| `combined_document_generator.py` | `src.utils` | Generates combined Word document with both main and college commentary versions. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/utils/combined_document_generator.py) |
| `commentary_formatter.py` | `src.utils` | Formats commentary output for various purposes. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/utils/commentary_formatter.py) |
| `divine_names_modifier.py` | `src.utils` | Modifies divine names (YHWH, etc.) according to style preferences. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/utils/divine_names_modifier.py) |
| `cost_tracker.py` | `src.utils` | Tracks API costs across all LLM calls during pipeline execution. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/utils/cost_tracker.py) |
| `pipeline_summary.py` | `src.utils` | Generates summary statistics and reports for pipeline runs. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/utils/pipeline_summary.py) |
| `logger.py` | `src.utils` | Centralized logging configuration for the project. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/utils/logger.py) |

---

## Schemas (`src/schemas/`)

| Script | Namespace | Description | Link |
|--------|-----------|-------------|------|
| `analysis_schemas.py` | `src.schemas` | Pydantic schemas for MacroAnalysis, MicroAnalysis, VerseCommentary, and other data structures. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/schemas/analysis_schemas.py) |
