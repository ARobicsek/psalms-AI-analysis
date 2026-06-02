# Script References

**Quick reference for all Python scripts in the Psalms AI Analysis project.**  
Always read this file first when you need to find code.

---

## Pipeline Runners (`scripts/`)

| Script | Namespace | Description | Link |
|--------|-----------|-------------|------|
| `run_enhanced_pipeline.py` | `scripts` | **NEW DEFAULT**: Master Writer pipeline. Single-pass generation from research inputs. Questions and insights skipped by default (`--include-questions`/`--include-insights` to opt in). Citation verifier runs with GPT-5.1 filter by default (`--no-gpt-filter` to disable). Use `--skip-copy-editor` to skip QA output. `--exclude` flags omit existing files entirely. Session 338: added STEP 1b literary echoes generation (default on, regenerate-and-overwrite), `--skip-lit-echoes` flag. **Session 347**: added `--synthesis-discovery` flag (default OFF, experimental). When set, runs a STEP 3.5 cross-verse synthesis-discovery pass between micro and writer (`src/agents/synthesis_discovery.py`), saves observations to `output/psalm_NNN/psalm_NNN_synthesis_discovery.md`, and splices them into the writer prompt as additional input. Sidecar — does NOT structure the commentary. Adds ~$2/psalm. Default path (flag off) leaves writer prompt byte-identical. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/run_enhanced_pipeline.py) |
| `run_enhanced_pipeline_TEST.py` | `scripts` | **PHASE 1 TEST**: V3 Prompt Overhaul test pipeline. Suffixes output with `_TEST`. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/run_enhanced_pipeline_TEST.py) |
| `run_enhanced_pipeline_with_synthesis.py` | `scripts` | **LEGACY**: Original Synthesis Writer pipeline (Pass 3 Synthesis → Pass 4 Master Editor). | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/run_enhanced_pipeline_with_synthesis.py) |
| `run_docx_only.py` | `scripts` | **UTILITY**: Fast DOCX layout text generation without hitting any agents. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/run_docx_only.py) |
| `run_si_pipeline.py` | `scripts` | **NEW SI**: Special Instruction pipeline using Master Writer approach. Matches enhanced pipeline controls (including copy editor, GPT-5.1 citation filter). Session 338: added STEP 1b literary echoes generation, `--skip-lit-echoes` flag. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/run_si_pipeline.py) |
| `run_literary_echoes.py` | `scripts` | **NEW (Session 338)**: Standalone runner for the 4-pass literary echoes workflow (Gemini 3.1 Pro × 2 → GPT-5.4 verify w/ web search → GPT-5.4 reconstruct). Default behavior is regenerate-and-overwrite; `--skip-if-exists` preserves existing file. Prints per-pass cost breakdown at completion. ~$0.95/psalm, ~10 min. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/run_literary_echoes.py) |
| `run_si_pipeline_with_synthesis.py` | `scripts` | **LEGACY SI**: Special Instruction pipeline using Synthesis Writer approach. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/run_si_pipeline_with_synthesis.py) |
| `run_copy_editor.py` | `scripts` | Standalone copy editor runner. Applies 9-category error taxonomy to existing `print_ready.md`. Supports batch (`36 37 38`), `--dry-run`, `--model`. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/run_copy_editor.py) |
| `run_scripture_verifier.py` | `scripts` | Standalone scripture citation verifier. Checks quoted Hebrew against `tanakh.db`. GPT-5.1 false-positive filter runs by default (`--no-gpt-filter` to disable, `--haiku-filter` for cheaper alternative). Supports batch psalms, `--fix` for copy-editor fix pass, `--tooluse-verify` for Haiku tool-use supplementary check (~$0.04/psalm). | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/run_scripture_verifier.py) |
| `EXPERIMENT_two_call_synthesis.py` | `scripts` | **EXPERIMENTAL (Session 346) — keep for Session 347 reference, then archive**. Two-call synthesis experiment for the Master Writer. Reuses the saved production writer prompt (`output/debug/master_writer_v4_prompt_psalm_NNN.txt`) split at the `## YOUR TASK` marker; Call 1 = synthesis discovery (brainstorm + adversarial novelty filter + evidence-honesty filter, no prose); Call 2 = write using approved spine as anchor-verse skeleton. Both calls `claude-opus-4-7` (effort=max). Retry/resume hardening included. Writes only to `output/psalm_NNN/EXPERIMENT_two_call/`. Discardable — touches no production code. Session 347 plan supersedes the spine approach but the `SYNTHESIS_TASK` prompt (steps 1, 2, 2b) is the template to reuse for the new `synthesis_discovery` agent. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/EXPERIMENT_two_call_synthesis.py) |
| `EXPERIMENT_two_call_finalize.py` | `scripts` | **EXPERIMENTAL (Session 346) — keep for Session 347 reference, then archive**. Runs experiment output through the production downstream chain (print-ready → citation verifier with GPT-5.1 FP filter → copy editor at gpt-5.4 → section extraction → DOCX) with all writes isolated to `output/psalm_NNN/EXPERIMENT_two_call/`. Useful template for any future experiment that needs the production downstream chain without clobbering shipped files. Deliberately does NOT call `run_scripture_verifier.py` or `run_docx_only.py`, both of which hardcode production output paths. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/EXPERIMENT_two_call_finalize.py) |
| `EXPERIMENT_concordance_eval.py` | `scripts` | **EXPERIMENTAL (Session 350) — discardable, keep for D/E validation then archive**. Re-runs only the concordance selection + retrieval path for a set of psalms, reusing production Stage-1 discoveries from each `micro_v2.json` (no re-discovery). Runs modified Stage-2 (live sonnet) → librarian, reports per-search external yield vs the Session-349 baseline. Used to measure the 24%→~90% improvement. Usage: `python scripts/EXPERIMENT_concordance_eval.py 54 55 56 57 58`. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/EXPERIMENT_concordance_eval.py) |
| `EXPERIMENT_concordance_trace.py` | `scripts` | **EXPERIMENTAL (Session 350) — discardable**. Traces ONE psalm's concordance pipeline end to end via lightweight wrappers on the real production methods: STAGE A (raw LLM picks) → STAGE B (after `_override_llm_base_forms`) → STAGE C (after `_augment_with_root_searches`) → FINAL (searched + results). Usage: `python scripts/EXPERIMENT_concordance_trace.py 55`. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/EXPERIMENT_concordance_trace.py) |
| `converse_with_editor.py` | `scripts` | Enables multi-turn conversation with Master Editor about a completed psalm commentary with full research context. Supports multi-line copy/pasting and interactive model selection (Claude, Gemini, GPT). | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/converse_with_editor.py) |
| `concordance_tool.py` | `scripts` | Interactive Hebrew concordance CLI. 4 match modes (exact, variations, substring, substring + AI filter), lexicon lookup (BDB/Klein), AI commentary, cost tracking, markdown export. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/concordance_tool.py) |
| `add_lemma_column.py` | `scripts` | **ONE-OFF MIGRATION (Session 351)**: adds and populates the `lemma` column on `concordance` from ETCBC/BHSA `lex_utf8`. Greedy concat-alignment of BHSA word tokens to our (proclitic-attached) tokens — handles BHSA splitting ב/כ/ל/מ/ו/ה into separate nodes — assigns each token its content lemma; exact-match-required so misses stay NULL (→ naive fallback), never wrong. 96.3% coverage, builds `idx_concordance_lemma`. `--dry-run` reports per-book coverage without writing; `--book Psalms` restricts. Requires `text-fabric` + the cached BHSA 2021 data. Re-runnable (idempotent). | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/scripts/add_lemma_column.py) |

---

## Analysis Agents (`src/agents/`)

| Script | Namespace | Description | Link |
|--------|-----------|-------------|------|
| `macro_analyst.py` | `src.agents` | Pass 1: Produces chapter-level thesis and structural framework using Claude Opus 4.6 with RAG context. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/macro_analyst.py) |
| `micro_analyst.py` | `src.agents` | Pass 2: Discovery-driven verse-by-verse research using Claude Sonnet 4.6 with adaptive thinking. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/micro_analyst.py) |
| `synthesis_writer.py` | `src.agents` | Pass 3: Final commentary synthesis combining macro thesis, micro discoveries, and research bundle. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/synthesis_writer.py) |
| `master_editor.py` | `src.agents` | Pass 4: Unified Master Writer V4 — single prompt replacing Main + College. Supports **Opus 4.8** (default) with streaming for long generations. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/master_editor.py) |
| `master_editor_v3.py` | `src.agents` | **PHASE 1 TEST**: V3 Prompt Overhaul variant. Implements 9 major prompt changes. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/master_editor_v3.py) |
| `master_editor_si.py` | `src.agents` | Master Writer V4 with Special Instructions that supports author directives for alternative versions. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/master_editor_si.py) |
| `master_editor_old.py` | `src.agents` | Legacy Master Editor implementation (archived). | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/master_editor_old.py) |
| `phonetic_analyst.py` | `src.agents` | Transcribes Hebrew text into phonetic/syllabic structure based on reconstructed Biblical Hebrew phonology. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/phonetic_analyst.py) |
| `copy_editor.py` | `src.agents` | Post-generation QA: 9-category error taxonomy (structural claims, inconsistencies, form/content confusion, negative citations, Hebrew script, weak parallels, factual/textual accuracy, grammar bloat, strained arguments). gpt-5.4. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/copy_editor.py) |
| `literary_echoes_agent.py` | `src.agents` | **NEW (Session 338)**: 4-pass literary echoes orchestrator. Pass 1+2: Gemini 3.1 Pro (generation + gap-fill). Pass 3: GPT-5.4 Responses API with `web_search_preview` tool (verification with real URLs). Pass 4: GPT-5.4 Chat Completions (mechanical reconstruction — uses 5.4 not 5.1 because 5.1 self-terminated early). Builds rolling exclusion list from the 4 most-recently-rendered files by mtime; injects into both Pass 1 and Pass 2 prompts. Saves per-pass artifacts + exact prompts + cost report under `output/psalm_NNN/literary_echoes/`. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/literary_echoes_agent.py) |
| `synthesis_discovery.py` | `src.agents` | **NEW (Session 347)**: Cross-verse synthesis-DISCOVERY sidecar agent (Opus 4.8, high effort, adaptive thinking, 64K max_tokens, streaming with retry on transient drops — mirrors writer config for evidence parity). Reads the same INPUT BLOCKS the Master Writer sees (psalm text, macro, micro, research bundle, phonetics, framework) and produces a calibrated list of cross-verse OBSERVATIONS (1 governing + N core + N additional). Hardened evidence-honesty filter: 9 named failure modes (homophony-vs-overlap, echo-vs-verbatim, primary-lexical-meaning, no-invented-prooftexts, uniqueness-claims-require-checking, count-before-citing, non-sequitur-synthesis, no-signature-root-claims, match-assertion-to-evidence) PLUS a meta-rule that demands the model name two more failure modes it didn't already check. Output bracketed by `---CROSS-VERSE-OBSERVATIONS-START/END---` markers for machine extraction. Used by `MasterEditor.discover_cross_verse_observations()` and spliced into the writer prompt at `### ANALYTICAL FRAMEWORK` anchor when present. Default writer path (no observations file) leaves prompt byte-identical to production. Triggered by `--synthesis-discovery` flag on the pipeline runner. ~$1.83/psalm at Opus 4.7 max effort. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/synthesis_discovery.py) |

---

## Librarian Agents (`src/agents/`)

| Script | Namespace | Description | Link |
|--------|-----------|-------------|------|
| `research_assembler.py` | `src.agents` | Coordinates all librarian agents to assemble comprehensive research bundles for psalm analysis. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/research_assembler.py) |
| `bdb_librarian.py` | `src.agents` | Fetches Hebrew lexicon entries (BDB + Klein Dictionary) from Sefaria API. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/bdb_librarian.py) |
| `concordance_librarian.py` | `src.agents` | Searches Hebrew concordance database with automatic phrase variation detection. **Session 350**: drops source-psalm self-matches (`self_match_count`/`only_self` on the bundle) so counts report genuine external parallels; added `tanakh_frequency()`. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/concordance_librarian.py) |
| `figurative_librarian.py` | `src.agents` | Queries figurative language database (Psalms + Pentateuch) with hierarchical tag support. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/figurative_librarian.py) |
| `figurative_curator.py` | `src.agents` | LLM-enhanced agent (GPT-5.4) that curates and synthesizes figurative language insights. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/figurative_curator.py) |
| `liturgical_librarian.py` | `src.agents` | Queries phrase-level liturgical index with intelligent aggregation and optional LLM summarization. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/liturgical_librarian.py) |
| `liturgical_librarian_sefaria.py` | `src.agents` | Alternative liturgical librarian using Sefaria API directly. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/liturgical_librarian_sefaria.py) |
| `commentary_librarian.py` | `src.agents` | Fetches traditional Jewish commentaries (Rashi, Ibn Ezra, Radak, etc.) from Sefaria API. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/commentary_librarian.py) |
| `sacks_librarian.py` | `src.agents` | Loads and formats Rabbi Jonathan Sacks' references to Psalms from his collected works. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/sacks_librarian.py) |
| `related_psalms_librarian.py` | `src.agents` | Retrieves related psalms with shared roots, phrases, and skipgrams from top connections analysis. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/related_psalms_librarian.py) |
| `rag_manager.py` | `src.agents` | Manages RAG documents (analytical framework, psalm functions, Ugaritic parallels) for agent prompts. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/rag_manager.py) |
| `scholar_researcher.py` | `src.agents` | Coordinates research requests by generating specific requests for librarian agents from macro overview. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/scholar_researcher.py) |
| `question_curator.py` | `src.agents` | Generates "Questions for the Reader" from macro/micro analysis using gpt-5.4. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/question_curator.py) |
| `insight_extractor.py` | `src.agents` | **NEW**: Filters research materials for transformative insights using gpt-5.4. Now uses full psalm text and macro context. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/agents/insight_extractor.py) |

---

## Concordance (`src/concordance/`)

| Script | Namespace | Description | Link |
|--------|-----------|-------------|------|
| `search.py` | `src.concordance` | Hebrew concordance search with single/multi-word phrase support and multiple normalization levels. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/concordance/search.py) |
| `hebrew_text_processor.py` | `src.concordance` | Text processing utilities for Hebrew normalization and word splitting. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/concordance/hebrew_text_processor.py) |
| `morphology_variations.py` | `src.concordance` | Generates morphological variations (prefixes, suffixes) for Hebrew words. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/concordance/morphology_variations.py) |
| `root_matcher.py` | `src.concordance` | Hebrew root matching utilities for concordance searches. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/concordance/root_matcher.py) |
| `root_selection.py` | `src.concordance` | **NEW (Session 350)**: Picks the single most distinctive content word from a lexical insight (phrase + analyst variants) to trace on its own — "distinctive" = rarest in Tanakh within a frequency window, preferring 3-letter bare roots over rare inflections. Used by `MicroAnalystV2._augment_with_root_searches`. Surface-frequency-based (a deliberate stopgap; true lemma/root selection is the D/E work). | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/concordance/root_selection.py) |

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
| `document_generator.py` | `src.utils` | Generates print-ready Word (.docx) documents from pipeline outputs. **Now supports Arabic/Hebrew (RTL) and CJK fonts.** | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/utils/document_generator.py) |
| `combined_document_generator.py` | `src.utils` | *(Deprecated V4)* — was Main + College combined doc. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/utils/combined_document_generator.py) |
| `commentary_formatter.py` | `src.utils` | Formats commentary output for various purposes. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/utils/commentary_formatter.py) |
| `divine_names_modifier.py` | `src.utils` | Modifies divine names (YHWH, etc.) according to style preferences. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/utils/divine_names_modifier.py) |
| `cost_tracker.py` | `src.utils` | Tracks API costs across all LLM calls during pipeline execution. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/utils/cost_tracker.py) |
| `pipeline_summary.py` | `src.utils` | Generates summary statistics and reports for pipeline runs. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/utils/pipeline_summary.py) |
| `scripture_verifier.py` | `src.utils` | Scripture citation verifier. Two modes: (1) **Regex** (default, free): 4 extraction patterns A/B/C/D with normalization, word-level consonantal matching, ellipsis-fragment splitting, optional Haiku FP filter (~$0.003/psalm). (2) **Tool-use** (`verify_citations_tooluse()`, ~$0.04/psalm): Haiku identifies citations via tool-use (`lookup_verse`), Python does programmatic comparison, Haiku filters FPs. Prompt caching reduces multi-turn cost. Pipeline Step 5a½. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/utils/scripture_verifier.py) |
| `logger.py` | `src.utils` | Centralized logging configuration for the project. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/utils/logger.py) |
| `api_guard.py` | `src.utils` | **NEW (Session 342)**: API quota exhaustion detection and pipeline halt utility. `is_quota_exhaustion(exc)` distinguishes permanent billing errors (OpenAI `insufficient_quota`, Anthropic `credit balance too low`, Google `RESOURCE_EXHAUSTED`) from transient rate limits. `halt_on_quota()` saves partial costs, prints halt message, plays audible alert (Windows), exits code 2. Used by both pipeline runners at every non-fatal except block. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/utils/api_guard.py) |

---

## Schemas (`src/schemas/`)

| Script | Namespace | Description | Link |
|--------|-----------|-------------|------|
| `analysis_schemas.py` | `src.schemas` | Pydantic schemas for MacroAnalysis, MicroAnalysis, VerseCommentary, and other data structures. | [file](file:///c:/Users/ariro/OneDrive/Documents/Psalms/src/schemas/analysis_schemas.py) |
