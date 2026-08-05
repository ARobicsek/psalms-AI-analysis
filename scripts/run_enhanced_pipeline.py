"""
Enhanced Pipeline Runner - Production (Master Writer V4 Integration)

Changes from original:
1. REMOVED Synthesis Writer step entirely.
2. REPLACED Master Editor step with Master Writer V4 (unified creation mode).
3. College Writer RETIRED (Session 269) — single unified prompt.

Usage:
    python scripts/run_enhanced_pipeline.py PSALM_NUMBER [options]
"""

import sys
import os
import time
import json
import re
import argparse
from pathlib import Path
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.macro_analyst import MacroAnalyst
from src.agents.micro_analyst import MicroAnalystV2
# SynthesisWriter REMOVED
from src.agents.master_editor import MasterEditor
from src.agents.question_curator import QuestionCurator
# InsightExtractor REMOVED (Session 374): the agent existed to keep the
# Synthesis Writer from drowning in research, and the Synthesis Writer was
# removed in V4. Unused in production since Psalm 30 (2026-03-08); the last 13
# runs (Pss 60-72) produced no insights file at all. Archived to
# src/agents/archive/insight_extractor.py. Not to be confused with the
# synthesis-discovery sidecar (STEP 3.5), which is very much alive.
from src.agents.copy_editor import CopyEditor
from src.agents.literary_echoes_agent import (
    LiteraryEchoesAgent,
    GEMINI_MODEL as LIT_ECHOES_GEMINI_MODEL,
    GPT_VERIFY_MODEL as LIT_ECHOES_VERIFY_MODEL,
)
from src.schemas.analysis_schemas import MacroAnalysis, MicroAnalysis, VerseCommentary, StructuralDivision, load_macro_analysis
from src.utils.logger import get_logger
from src.utils.pipeline_summary import PipelineSummaryTracker
from src.utils.cost_tracker import CostTracker
from src.utils.research_trimmer import ResearchTrimmer
from src.utils.api_guard import halt_on_quota


def _parse_research_stats_from_markdown(markdown_content: str) -> dict:
    """Parse research statistics from a research bundle markdown file."""
    stats = {
        'lexicon_count': 0,
        'concordance_count': 0,
        'figurative_count': 0,
        'figurative_parallels_reviewed': {},
        'commentary_counts': {},
        'sacks_count': 0,
        'deep_research_available': False,
        'deep_research_chars': 0,
        'literary_echoes_available': False
    }

    # Count lexicon entries
    lexicon_section = re.search(r'## Hebrew Lexicon Entries.*?(?=\n## [^#]|\Z)', markdown_content, re.DOTALL)
    if lexicon_section:
        lexicon_matches = re.findall(r'^### [^\n]+$', lexicon_section.group(0), re.MULTILINE)
        stats['lexicon_count'] = len(lexicon_matches)

    # Count concordance results by parsing actual query headers, e.g.
    # "### <query> (28 external results, auto, consonantal)". Scope to the
    # Concordance Searches section so figurative/other ### headers can't leak
    # in, and tolerate an optional word (e.g. "external") between the count and
    # "results" — the header format the micro analyst emits gained "external"
    # (honest external counts), which the old bare "(N results" regex missed,
    # yielding a spurious 0 → "N/A" on resume.
    concordance_section = re.search(
        r'## Concordance Searches(.*?)(?=\n## [^#]|\Z)', markdown_content, re.DOTALL
    )
    if concordance_section:
        concordance_result_counts = re.findall(
            r'^### .+?\((\d+)(?:\s+\w+)? results', concordance_section.group(1), re.MULTILINE
        )
        stats['concordance_count'] = sum(int(n) for n in concordance_result_counts)

    # Count figurative language instances
    curated_section = re.search(r'## Figurative Language Insights \(Curated\)(.*?)(?=\n## [^#]|\Z)', markdown_content, re.DOTALL)
    if curated_section:
        section_text = curated_section.group(1)
        total_match = re.search(r'\*Total results reviewed\*: (\d+)', section_text)
        if total_match:
            stats['figurative_count'] = int(total_match.group(1))
        breakdown_match = re.search(r'\*\*Figurative Parallels Reviewed\*\*:(.*?)(?=\n\n|\Z)', section_text, re.DOTALL)
        if breakdown_match:
            breakdown_text = breakdown_match.group(1)
            parallels = re.findall(r'- \*\*(.*?)\*\*: (\d+) results', breakdown_text)
            for vehicle, count in parallels:
                stats['figurative_parallels_reviewed'][vehicle] = int(count)
    else:
        figurative_matches = re.findall(r'^\*\*[A-Za-z]+ \d+:\d+\*\*', markdown_content, re.MULTILINE)
        stats['figurative_count'] = len(figurative_matches)

    # Count traditional commentaries.
    #
    # Patterns are DERIVED from the librarian's own commentator list so this can never
    # drift out of sync again, and each is ANCHORED to the end of the dossier's header
    # line (`### 71:5 — Malbim`). Both matter as of Session 373: the old hand-maintained
    # list still carried `Sforno`, which is never fetched, and its unanchored
    # `### .*Malbim` now also matches `### 71:5 — Malbim Beur Hamilot`, double-counting
    # every Malbim entry and silently inflating the bibliography in the finished DOCX.
    from src.agents.commentary_librarian import COMMENTATORS
    for name in COMMENTATORS:
        matches = re.findall(rf'^### .*— {re.escape(name)}\s*$', markdown_content, re.MULTILINE)
        if matches:
            stats['commentary_counts'][name] = len(matches)

    # Check for Rabbi Sacks
    if '## Rabbi Sacks' in markdown_content or 'Rabbi Jonathan Sacks' in markdown_content:
        sacks_matches = re.findall(r'### [^#\n]+Sacks|Rabbi Sacks|Jonathan Sacks', markdown_content)
        stats['sacks_count'] = max(1, len(sacks_matches))

    # Check for Deep Web Research
    if '## Deep Web Research' in markdown_content:
        stats['deep_research_available'] = True
        deep_match = re.search(r'## Deep Web Research\s*\n(.*?)(?=\n## [^#]|\Z)', markdown_content, re.DOTALL)
        if deep_match:
            stats['deep_research_chars'] = len(deep_match.group(1))

    # Check for Literary Echoes
    if '## Cross-Cultural Literary Echoes' in markdown_content:
        stats['literary_echoes_available'] = True

    # Check for Models Used
    models_used = {}
    models_section = re.search(r'### Models Used in Research(.*?)(?=\n## [^#]|\Z)', markdown_content, re.DOTALL)
    if models_section:
        section_text = models_section.group(1)
        model_matches = re.findall(r'- \*\*(.*?)\*\*: (.*?)(?:\n|$)', section_text)
        for agent, model in model_matches:
            if "Literary Echoes" in agent:
                # Both label vocabularies are accepted. Session 374 removed Pass 4
                # (reconstruction is deterministic now) and added Pass 1b, but
                # bundles written before that still say "Passes 3 & 4" and resume
                # must keep reading them.
                if "1b" in agent:
                    models_used['literary_echoes_pass_1b'] = model.strip()
                elif "Passes 1" in agent:
                    models_used['literary_echoes_pass_1'] = model.strip()
                    models_used['literary_echoes_pass_2'] = model.strip()
                elif "Pass 3" in agent or "Passes 3" in agent:
                    models_used['literary_echoes_pass_3'] = model.strip()
            else:
                agent_key = agent.lower().replace(' ', '_')
                models_used[agent_key] = model.strip()
    stats['models_used'] = models_used

    return stats


def _parse_related_psalms_from_markdown(markdown_content: str) -> list:
    """Parse related psalms section."""
    related_psalms = []
    if "## Related Psalms Analysis" not in markdown_content:
        return related_psalms

    start_match = re.search(r'## Related Psalms Analysis', markdown_content)
    if not start_match:
        return related_psalms

    start_pos = start_match.end()
    end_match = re.search(r'\n## [^#]', markdown_content[start_pos:])
    if end_match:
        end_pos = start_pos + end_match.start()
        related_section = markdown_content[start_pos:end_pos]
    else:
        related_section = markdown_content[start_pos:]

    psalm_matches = re.findall(r'### Psalm (\d+)', related_section)
    for psalm_num_str in psalm_matches:
        try:
            related_psalms.append(int(psalm_num_str))
        except ValueError:
            pass
    return related_psalms


def _extract_sections_from_copy_edited(copy_edited_path: Path, logger=None) -> tuple:
    """Extract introduction and verse commentary sections from a copy-edited markdown file.
    
    The copy_edited.md has the same structure as print_ready.md:
      # Commentary on Psalm N
      ---
      ## Introduction
      <intro text including liturgical section>
      ---
      ## Psalm N
      <psalm text>
      ---
      ## Verse-by-Verse Commentary
      <verse commentary>
      ------
      ## Methodological...
    
    The copy editor outputs each paragraph on a single line (separated by \\n).
    The DOCX generator expects \\n\\n between paragraphs. This function restores
    the double-newline paragraph breaks after extraction.
    
    This function also detects and corrects a known LLM failure mode where the
    copy editor displaces liturgical key verse content from the introduction
    section into the verse commentary section.
    
    Returns:
        (intro_text, verses_text) — the raw text content of each section,
        with paragraph breaks restored for DOCX generation.
    """
    _log = logger or (lambda msg: None)
    if logger:
        _log = logger.info
    
    content = copy_edited_path.read_text(encoding='utf-8')
    
    # Extract introduction: from "## Introduction\n" to the first standalone "---" line
    # that precedes "## Psalm" or "## Verse-by-Verse"
    intro_match = re.search(
        r'^## Introduction\n(.*?)(?=^---\s*$\n^## (?:Psalm|Verse))',
        content, re.DOTALL | re.MULTILINE
    )
    intro_text = intro_match.group(1).strip() if intro_match else ''
    
    # Extract verse commentary: from "## Verse-by-Verse Commentary\n" to the end marker
    # The end marker may be "------\n## Methodological" or just "## Methodological" directly
    verses_match = re.search(
        r'^## Verse-by-Verse Commentary\n(.*?)(?=^-{3,}\s*$\n^## Methodo|^## Methodo|\Z)',
        content, re.DOTALL | re.MULTILINE
    )
    verses_text = verses_match.group(1).strip() if verses_match else ''
    
    # Strip any trailing section separators (--- lines) from extracted text.
    # The separator may be on its own line (\n---) or concatenated to text (word---)
    if intro_text:
        intro_text = re.sub(r'-{3,}\s*$', '', intro_text).strip()
    if verses_text:
        verses_text = re.sub(r'-{3,}\s*$', '', verses_text).strip()
    
    # -----------------------------------------------------------------------
    # HARDENING: Detect and recover displaced liturgical content
    # The copy editor LLM sometimes moves liturgical key verse content from
    # the intro (after #### Key Verses and Phrases) to the start of the verse
    # commentary section. Detect this and move it back.
    #
    # Detection strategy: find the first "standalone" verse header in the
    # verses section — one where **Verse N** is the entire line content,
    # not followed by same-line text. Liturgical key verse entries look like
    #   **Verse 9** is the most liturgically mobile verse...
    #   **Verse 2's** imagery of the thirsting deer...
    # while actual verse commentary headers look like
    #   **Verse 1**
    #   <Hebrew text on next line>
    # If there is content before the first standalone header, it is
    # displaced liturgical content that belongs in the introduction.
    # -----------------------------------------------------------------------
    has_liturgical_marker = '---LITURGICAL-SECTION-START---' in intro_text
    has_key_verses_header = bool(re.search(r'####\s*Key\s+[Vv]erse', intro_text))

    if has_liturgical_marker and has_key_verses_header:
        # Find the first standalone verse header: **Verse N** (or **Verses N-M**)
        # as the entire content of a line (no trailing text on the same line).
        standalone_verse_re = re.compile(
            r'^\*\*Verses?\s+\d+(?:\s*[-–]\s*\d+)?\*\*\s*$',
            re.MULTILINE
        )
        first_standalone = standalone_verse_re.search(verses_text)

        if first_standalone and first_standalone.start() > 50:
            # There's substantial content before the first actual verse header —
            # this is likely the displaced liturgical key verse content
            displaced_content = verses_text[:first_standalone.start()].strip()

            # Verify it contains bold verse references (typical of liturgical entries)
            if re.search(r'\*\*Verse\s+\d+', displaced_content):
                _log(f"  ⚠️  RECOVERY: Detected displaced liturgical content ({len(displaced_content):,} chars) "
                     f"at start of verse commentary. Moving back to introduction.")

                # Move it back: append to intro, remove from verses
                intro_text = intro_text.rstrip() + '\n' + displaced_content
                verses_text = verses_text[first_standalone.start():].strip()

                _log(f"  ✅ Liturgical content restored to introduction section")
    
    # Restore paragraph breaks: the copy editor collapses \n\n to \n.
    # Convert every single \n to \n\n so the DOCX generator sees paragraph boundaries.
    # First collapse any existing \n\n to \n (normalize), then expand all to \n\n.
    if intro_text:
        intro_text = re.sub(r'\n+', '\n', intro_text)  # normalize
        intro_text = intro_text.replace('\n', '\n\n')   # restore double-newlines
    if verses_text:
        verses_text = re.sub(r'\n+', '\n', verses_text)  # normalize
        verses_text = verses_text.replace('\n', '\n\n')   # restore double-newlines
    
    return intro_text, verses_text


def run_enhanced_pipeline(
    psalm_number: int,
    output_dir: str = "output",
    db_path: str = "database/tanakh.db",
    delay_between_steps: int = 120,
    resume: bool = False,
    skip_macro: bool = False,
    skip_micro: bool = False,
    skip_writer: bool = False,  # Changed from skip_synthesis/skip_master_edit
    skip_college: bool = False,  # DEPRECATED V4: silent no-op (unified writer)
    skip_print_ready: bool = False,
    skip_word_doc: bool = False,
    skip_combined_doc: bool = False,  # DEPRECATED V4: no combined doc
    smoke_test: bool = False,
    skip_default_commentaries: bool = False,
    master_editor_model: str = "claude-opus-5",
    synthesis_discovery_model: str = None,   # None -> synthesis_discovery.DEFAULT_MODEL (Opus 4.8)
    skip_questions: bool = True,     # Session 280: skipped by default, use --include-questions
    exclude_questions: bool = False,
    skip_copy_editor: bool = False,  # Session 280: copy editor runs by default
    skip_lit_echoes: bool = False,   # Session 338: literary echoes runs by default (regenerates on every run)
    macro_model: str = "claude-opus-4-8",
    question_model: str = "gpt-5.6-terra",
    copy_model: str = "gpt-5.6-terra",
    synthesis_discovery: bool = True,
    reuse_synthesis_discovery: bool = False,  # Session 358: reuse an existing observations file instead of regenerating (~$2 saved)
    skip_beta_reader: bool = True,   # Session 372: OFF by default — see --beta-reader below
    beta_model: str = None,          # Session 362: default lives in BetaReader.DEFAULT_MODEL
):
    logger = get_logger("enhanced_pipeline_test")
    logger.info(f"=" * 80)
    logger.info(f"ENHANCED PIPELINE (TEST - MASTER WRITER) - Psalm {psalm_number}")
    if smoke_test:
        logger.info("SMOKE TEST MODE ENABLED - NO API CALLS WILL BE MADE")
    logger.info(f"=" * 80)

    # --- Initialize Pipeline Summary Tracker ---
    output_path = Path(output_dir)
    summary_json_file = output_path / f"psalm_{psalm_number:03d}_pipeline_stats.json"
    
    # A now-deleted `skip_insights` used to be in this list. Session 280 had made
    # insights opt-in, so it defaulted to True -- which made EVERY plain run look
    # like a resume and load the psalm's previous stats file. That was not
    # harmless: track_research_requests APPENDS, so a fresh run inherited and then
    # duplicated the old run's request lists. --resume is what actually means
    # resume; the skip_* flags are the manual partial-rerun form of the same thing.
    is_resuming = any([resume, skip_macro, skip_micro, skip_writer, skip_print_ready, skip_word_doc]) and not smoke_test
    
    initial_data = None
    if is_resuming and summary_json_file.exists():
        try:
            logger.info(f"Resuming pipeline run. Loading existing stats from {summary_json_file}")
            with open(summary_json_file, 'r', encoding='utf-8') as f:
                initial_data = json.load(f)
                
            # CLEANUP: If we are running the TEST pipeline, we should remove stale synthesis data
            # even if we loaded it from a previous run.
            if initial_data:
                if 'model_usage' in initial_data and 'synthesis' in initial_data['model_usage']:
                    logger.info("Removing stale 'synthesis' model data from loaded stats")
                    del initial_data['model_usage']['synthesis']
                if 'steps' in initial_data and 'synthesis' in initial_data['steps']:
                    logger.info("Removing stale 'synthesis' step data from loaded stats")
                    del initial_data['steps']['synthesis']
        except Exception as e:
            logger.warning(f"Could not load existing stats file, starting fresh. Error: {e}")

    tracker = PipelineSummaryTracker(psalm_number=psalm_number, initial_data=initial_data)
    logger.info("Pipeline summary tracking enabled.")

    cost_tracker = CostTracker()
    research_trimmer = ResearchTrimmer(logger=logger)
    output_path.mkdir(parents=True, exist_ok=True)
    lit_echoes_cost = 0.0  # Populated by STEP 1b; printed in the final tally
    synthesis_discovery_cost = 0.0  # Populated by STEP 3.5; printed in the final tally

    # File paths
    macro_file = output_path / f"psalm_{psalm_number:03d}_macro.json"
    micro_file = output_path / f"psalm_{psalm_number:03d}_micro_v2.json"
    research_file = output_path / f"psalm_{psalm_number:03d}_research_v2.md"
    
    # NEW: Writer outputs (replacing synthesis/edited split)
    # We use the "edited" names for downstream compatibility
    edited_intro_file = output_path / f"psalm_{psalm_number:03d}_edited_intro.md"
    edited_verses_file = output_path / f"psalm_{psalm_number:03d}_edited_verses.md"
    # We still produce an assessment file, maybe? The Writer prompt doesn't strictly output one.
    # We'll skip it or create a placeholder.
    edited_assessment_file = output_path / f"psalm_{psalm_number:03d}_assessment.md"
    
    docx_output_file = output_path / f"psalm_{psalm_number:03d}_commentary.docx"
    
    # College/combined file paths RETIRED (Session 269 — V4 unified writer)
    # Kept as comments for reference only:
    # edited_intro_college_file = output_path / f"psalm_{psalm_number:03d}_edited_intro_college.md"
    # edited_verses_college_file = output_path / f"psalm_{psalm_number:03d}_edited_verses_college.md"
    # docx_output_college_file = output_path / f"psalm_{psalm_number:03d}_commentary_college.docx"
    # docx_output_combined_file = output_path / f"psalm_{psalm_number:03d}_commentary_combined.docx"
    
    reader_questions_file = output_path / f"psalm_{psalm_number:03d}_reader_questions.json"

    # Resume logic
    if resume and not smoke_test:
        logger.info("RESUME MODE: Auto-detecting last completed step...")

        # Check if literary echoes is already completed
        lit_echoes_file = Path("data") / "literary_echoes" / f"psalm_{psalm_number:03d}_literary_echoes.txt"
        if lit_echoes_file.exists():
            skip_lit_echoes = True

        # Session 374: the insights tier was removed from this ladder along with
        # STEP 2c. It sat between research and the writer and set the same two
        # skips the research branch already sets, so collapsing it loses nothing.
        if not edited_intro_file.exists():
             if not research_file.exists():
                 if not macro_file.exists():
                     logger.info("No existing files found. Starting from beginning.")
                 else:
                     skip_macro = True
             else:
                 skip_macro = True
                 skip_micro = True
        else:
             skip_macro = True
             skip_micro = True
             skip_writer = True
             logger.info("Writer output exists. Moving to downstream steps.")
        resume = False

    # =====================================================================
    # STEP 1: Macro Analysis
    # =====================================================================
    if smoke_test:
        logger.info("\n[STEP 1] SMOKE TEST: Generating dummy MacroAnalyst output...")
        dummy_macro = MacroAnalysis(
            psalm_number=psalm_number,
            thesis_statement="This is a smoke test thesis.",
            genre="Smoke Test Genre",
            historical_context="Smoke test historical context.",
            structural_outline=[StructuralDivision(section="v. 1", theme="Smoke test theme")],
            research_questions=["Is this a smoke test?"]
        )
        from src.schemas.analysis_schemas import save_analysis
        save_analysis(dummy_macro, str(macro_file), format="json")
        tracker.track_step_output("macro_analysis", dummy_macro.to_markdown())

    elif not skip_macro:
        logger.info("\n[STEP 1] Running MacroAnalyst...")
        print(f"\n{'='*80}")
        print(f"STEP 1: Macro Analysis")
        print(f"{'='*80}\n")
        
        # Track input
        from src.data_sources.tanakh_database import TanakhDatabase
        db = TanakhDatabase(Path(db_path))
        psalm = db.get_psalm(psalm_number)
        if psalm:
            psalm_text = "\n".join([f"{v.verse}: {v.hebrew} / {v.english}" for v in psalm.verses])
            tracker.track_step_input("macro_analysis", psalm_text)
            tracker.track_verse_count(len(psalm.verses))

        macro_analyst = MacroAnalyst(cost_tracker=cost_tracker, model=macro_model)
        macro_analysis = macro_analyst.analyze_psalm(psalm_number)
        from src.schemas.analysis_schemas import save_analysis
        save_analysis(macro_analysis, str(macro_file), format="json")
        
        # Append model_used to the JSON for persistence across pipeline resumes
        with open(macro_file, 'r', encoding='utf-8') as f:
            macro_json = json.load(f)
        macro_json['model_used'] = macro_analyst.model
        with open(macro_file, 'w', encoding='utf-8') as f:
            json.dump(macro_json, f, ensure_ascii=False, indent=2)
        
        tracker.track_step_output("macro_analysis", macro_analysis.to_markdown())
        tracker.track_model_for_step("macro_analysis", macro_analyst.model)
        time.sleep(delay_between_steps)
    else:
        logger.info("[STEP 1] Skipping macro analysis")
        if not macro_file.exists():
            logger.error(f"FATAL: Missing {macro_file}")
            sys.exit(1)
        macro_analysis = load_macro_analysis(str(macro_file))
        
        # Track the model even when skipping - try to read from JSON or use default
        try:
            with open(macro_file, 'r', encoding='utf-8') as f:
                macro_json = json.load(f)
                # Check if model was stored in the JSON (new format)
                model_used = macro_json.get('model_used', MacroAnalyst.DEFAULT_MODEL)
        except Exception:
            model_used = MacroAnalyst.DEFAULT_MODEL
        tracker.track_model_for_step("macro_analysis", model_used)

    # =====================================================================
    # STEP 1b: Literary Echoes Generation (Session 338)
    # Default: regenerate and overwrite data/literary_echoes/psalm_NNN_literary_echoes.txt
    # so downstream research_assembler picks up fresh content.
    # Skipped silently if --skip-lit-echoes is passed.
    # Non-fatal on failure — downstream research_assembler tolerates missing file.
    # =====================================================================
    if not skip_lit_echoes and not smoke_test:
        logger.info("\n[STEP 1b] Generating Literary Echoes...")
        print(f"\n{'='*80}")
        print(
            f"STEP 1b: Literary Echoes ({LIT_ECHOES_GEMINI_MODEL} generates → "
            f"{LIT_ECHOES_VERIFY_MODEL} verifies per entry → deterministic rebuild)"
        )
        print(f"{'='*80}\n")
        try:
            lit_echoes_agent = LiteraryEchoesAgent(
                cost_tracker=cost_tracker,
                db_path=db_path,
                logger=logger,
            )
            lit_result = lit_echoes_agent.generate(
                psalm_number=psalm_number,
                psalm_output_dir=output_path,
                skip_if_exists=False,   # Default overwrite
            )
            tracker.track_model_for_step("literary_echoes_pass_1a", LIT_ECHOES_GEMINI_MODEL)
            tracker.track_model_for_step("literary_echoes_pass_2", LIT_ECHOES_GEMINI_MODEL)
            tracker.track_model_for_step("literary_echoes_pass_3", LIT_ECHOES_VERIFY_MODEL)
            lit_echoes_cost = lit_result.total_cost
            logger.info(
                f"[STEP 1b] Literary echoes complete — ${lit_result.total_cost:.4f} "
                f"({len(lit_result.exclusion_authors)} authors excluded from last "
                f"{len(lit_result.exclusion_source_files)} files)"
            )
        except Exception as e:
            halt_on_quota(e, "STEP 1b: Literary Echoes", logger, cost_tracker, output_path, psalm_number)
            logger.warning(f"[STEP 1b] Literary echoes failed (non-fatal): {e}", exc_info=True)
    elif skip_lit_echoes:
        logger.info("[STEP 1b] Skipping literary echoes (--skip-lit-echoes)")
        # If the canonical file exists, assume it was generated with the standard pipeline models
        lit_echoes_file = Path("data") / "literary_echoes" / f"psalm_{psalm_number:03d}_literary_echoes.txt"
        if lit_echoes_file.exists():
            tracker.track_model_for_step("literary_echoes_pass_1a", LIT_ECHOES_GEMINI_MODEL)
            tracker.track_model_for_step("literary_echoes_pass_2", LIT_ECHOES_GEMINI_MODEL)
            tracker.track_model_for_step("literary_echoes_pass_3", LIT_ECHOES_VERIFY_MODEL)

    # =====================================================================
    # STEP 2: Micro Analysis
    # =====================================================================
    if smoke_test:
        logger.info("\n[STEP 2] SMOKE TEST: Generating dummy MicroAnalyst output...")
        dummy_micro = MicroAnalysis(
            psalm_number=psalm_number,
            verse_commentaries=[VerseCommentary(verse_number=1, commentary="Smoke test commentary.")],
            thematic_threads=["Smoke test theme"],
            interesting_questions=["Is this a smoke test?"]
        )
        dummy_research_bundle = "# Smoke Test Research Bundle\n\nDummy content."
        from src.schemas.analysis_schemas import save_analysis
        save_analysis(dummy_micro, str(micro_file), format="json")
        with open(research_file, 'w', encoding='utf-8') as f:
            f.write(dummy_research_bundle)
        tracker.track_step_output("micro_analysis", dummy_micro.to_markdown())

    elif not skip_micro:
        logger.info("\n[STEP 2] Running MicroAnalyst v2...")
        print(f"\n{'='*80}")
        print(f"STEP 2: Micro Analysis + Research Bundle")
        print(f"{'='*80}\n")
        tracker.track_step_input("micro_analysis", macro_analysis.to_markdown())
        
        micro_analyst = MicroAnalystV2(db_path=db_path, commentary_mode="all" if not skip_default_commentaries else "selective", cost_tracker=cost_tracker)
        micro_analysis, research_bundle = micro_analyst.analyze_psalm(psalm_number, macro_analysis)
        
        from src.schemas.analysis_schemas import save_analysis
        save_analysis(micro_analysis, str(micro_file), format="json")
        
        # Append model_used to the JSON for persistence across pipeline resumes
        with open(micro_file, 'r', encoding='utf-8') as f:
            micro_json = json.load(f)
        micro_json['model_used'] = micro_analyst.model
        with open(micro_file, 'w', encoding='utf-8') as f:
            json.dump(micro_json, f, ensure_ascii=False, indent=2)
        
        with open(research_file, 'w', encoding='utf-8') as f:
            f.write(research_bundle.to_markdown())
            
        tracker.track_step_output("micro_analysis", micro_analysis.to_markdown())
        tracker.track_model_for_step("micro_analysis", micro_analyst.model)
        tracker.track_research_bundle(research_bundle)
        time.sleep(delay_between_steps)
    else:
        logger.info("[STEP 2] Skipping micro analysis")
        if not micro_file.exists() or not research_file.exists():
            logger.error("FATAL: Missing micro/research files")
            sys.exit(1)
            
        from src.schemas.analysis_schemas import load_micro_analysis
        micro_analysis = load_micro_analysis(str(micro_file))
        with open(research_file, 'r', encoding='utf-8') as f:
            research_bundle_content = f.read()
        
        # Track stats from markdown (same approach as original pipeline)
        research_stats = _parse_research_stats_from_markdown(research_bundle_content)
        tracker.research.lexicon_entries_count = research_stats['lexicon_count']
        tracker.research.concordance_results = {'total_results': research_stats['concordance_count']}
        tracker.research.figurative_results = {'total_instances_used': research_stats['figurative_count']}
        tracker.research.figurative_parallels_reviewed = research_stats.get('figurative_parallels_reviewed', {})
        tracker.research.commentary_counts = research_stats['commentary_counts']
        tracker.research.sacks_references_count = research_stats['sacks_count']
        tracker.research.deep_research_available = research_stats['deep_research_available']
        tracker.research.deep_research_included = research_stats['deep_research_available']
        tracker.research.deep_research_chars = research_stats['deep_research_chars']
        tracker.research.literary_echoes_available = research_stats.get('literary_echoes_available', False)
        tracker.research.literary_echoes_included = research_stats.get('literary_echoes_available', False)
        if tracker.research.literary_echoes_available:
            le_match = re.search(r'## Cross-Cultural Literary Echoes\s*\n(.*?)(?=\n## [^#]|\Z)', research_bundle_content, re.DOTALL)
            if le_match:
                tracker.research.literary_echoes_chars = len(le_match.group(1))
        
        tracker.research.research_bundle_chars = len(research_bundle_content)
        tracker.research.research_bundle_tokens = len(research_bundle_content) // 3

        if research_stats.get('models_used'):
            for agent, model in research_stats['models_used'].items():
                tracker.track_model_for_step(agent, model)

        # Track micro_analysis model when skipping - try to read from JSON or use default
        try:
            with open(micro_file, 'r', encoding='utf-8') as mf:
                micro_json = json.load(mf)
                micro_model_used = micro_json.get('model_used', MicroAnalystV2.DEFAULT_MODEL)
        except Exception:
            micro_model_used = MicroAnalystV2.DEFAULT_MODEL
        tracker.track_model_for_step("micro_analysis", micro_model_used)

        related_psalms = _parse_related_psalms_from_markdown(research_bundle_content)
        if related_psalms:
            tracker.research.related_psalms_count = len(related_psalms)
            tracker.research.related_psalms_list = related_psalms

        tracker.save_json(str(output_path))
        logger.info(f"Research stats extracted from markdown and saved")

    # =====================================================================
    # STEP 2b: Question Curation
    # =====================================================================
    if skip_questions or exclude_questions:
        logger.info("[STEP 2b] Skipping question curation")
    elif not smoke_test and macro_file.exists() and micro_file.exists():
        logger.info("[STEP 2b] Curating questions...")
        try:
            curator = QuestionCurator(cost_tracker=cost_tracker, model=question_model)
            q, s = curator.curate_questions(psalm_number, macro_file, micro_file)
            curator.save_questions(q, s, output_path, psalm_number)
            tracker.track_model_for_step("question_curator", curator.active_model)
        except Exception as e:
            halt_on_quota(e, "STEP 2b: Question Curator", logger, cost_tracker, output_path, psalm_number)
            logger.warning(f"Question curation failed: {e}")

    # =====================================================================
    # STEP 2c: Research Trimming
    #
    # Session 374: this step used to be "Insight Extraction" and the trimming
    # was a preamble to it. The InsightExtractor is gone (see the import at the
    # top of this file) but the trimming stays: converse_with_editor.py prefers
    # psalm_NNN_research_trimmed.md over research_v2.md when it exists.
    # NB the ResearchTrimmer is currently a no-op in practice -- the 400k cap
    # never trips on our ~215k bundles, so the two files come out identical.
    # =====================================================================
    if not smoke_test:
        if 'research_bundle_content' not in locals():
            if research_file.exists():
                with open(research_file, 'r', encoding='utf-8') as f: research_bundle_content = f.read()
            else:
                research_bundle_content = ""

        if research_bundle_content:
            trimmed, _, _ = research_trimmer.trim_bundle(research_bundle_content, max_chars=400000)
            trimmed_research_file = output_path / f"psalm_{psalm_number:03d}_research_trimmed.md"
            with open(trimmed_research_file, 'w', encoding='utf-8') as f:
                f.write(trimmed)
            logger.info(f"[STEP 2c] Saved trimmed research bundle ({len(trimmed):,} chars)")

    # =====================================================================
    # STEP 3: Synthesis (REMOVED)
    # =====================================================================
    logger.info("[STEP 3] Synthesis Writer - REMOVED (Replaced by Master Writer)")

    # =====================================================================
    # STEP 4: Master Writer (Drafting & Editing)
    # =====================================================================
    if smoke_test:
        logger.info("\n[STEP 4] SMOKE TEST: Master Writer...")
        with open(edited_intro_file, 'w', encoding='utf-8') as f: f.write("# Smoke Test Intro")
        with open(edited_verses_file, 'w', encoding='utf-8') as f: f.write("# Smoke Test Verses")
        tracker.track_step_output("master_editor", "Smoke test output")
        
    elif not skip_writer:
        logger.info(f"\n[STEP 4] Running Master WRITER ({master_editor_model})...")
        print(f"\n{'='*80}")
        print(f"STEP 4: Master Writer ({master_editor_model})")
        print(f"{'='*80}\n")

        master_editor = MasterEditor(main_model=master_editor_model, cost_tracker=cost_tracker)

        # STEP 3.5 (Session 347): Cross-verse synthesis discovery sidecar.
        # Produces a calibrated observation list that gets spliced into the writer
        # prompt as additional input. Runs by default; skipped with
        # --skip-synthesis-discovery. ALWAYS overwrites any prior observations
        # file so each pipeline run gets fresh cross-verse analysis.
        synthesis_discovery_file = None
        if synthesis_discovery:
            logger.info("\n[STEP 3.5] Cross-Verse Synthesis Discovery (sidecar)")
            print(f"\n{'='*80}")
            print(f"STEP 3.5: Cross-Verse Synthesis Discovery (Session 347)")
            print(f"{'='*80}\n")
            # SYNTHESIS DISCOVERY IS PINNED TO ITS OWN DEFAULT (Opus 4.8) and no longer
            # follows the writer. This line used to read `master_editor_model if "claude"
            # in ...`, so flipping the writer to Opus 5 in Session 373 would have silently
            # dragged the discovery sidecar along with it. Author's call: only the WRITER
            # was designed and A/B'd on Opus 5; discovery stays on 4.8 for cost. Override
            # with --synthesis-discovery-model if that is ever worth testing.
            from src.agents.synthesis_discovery import DEFAULT_MODEL as SD_DEFAULT_MODEL
            sd_model = synthesis_discovery_model or SD_DEFAULT_MODEL
            sd_cost_before = cost_tracker.get_total_cost()
            try:
                synthesis_discovery_file = master_editor.discover_cross_verse_observations(
                    macro_file=macro_file,
                    micro_file=micro_file,
                    research_file=research_file,
                    psalm_number=psalm_number,
                    output_path=output_path,
                    # Default: force overwrite on every run. Session 358:
                    # --reuse-synthesis-discovery keeps an existing observations
                    # file (writer still receives it), for writer-only reruns.
                    skip_if_exists=reuse_synthesis_discovery,
                    model=sd_model,
                )
                synthesis_discovery_cost = cost_tracker.get_total_cost() - sd_cost_before
                tracker.track_model_for_step("synthesis_discovery", sd_model)
                logger.info(
                    f"[STEP 3.5] Synthesis discovery complete — ${synthesis_discovery_cost:.4f}"
                )
                print(f"  Observations: {synthesis_discovery_file}")
                print(f"  Cost: ${synthesis_discovery_cost:.4f}\n")
            except Exception as e:
                halt_on_quota(e, "STEP 3.5: Synthesis Discovery", logger, cost_tracker, output_path, psalm_number)
                logger.error(
                    f"Synthesis discovery failed: {e}",
                    exc_info=True,
                )
                sys.exit(1)
        else:
            logger.info("[STEP 3.5] Skipping Cross-Verse Synthesis Discovery (--skip-synthesis-discovery)")

        try:
            result = master_editor.write_commentary(
                macro_file=macro_file,
                micro_file=micro_file,
                research_file=research_file,
                # Session 374: always None. The {curated_insights} slot in
                # MASTER_WRITER_PROMPT_V4 is deliberately LEFT IN PLACE and
                # renders the constant "[No curated insights provided]", which is
                # byte-identical to what every run since Ps 60 has sent. Removing
                # the slot would be an un-A/B'd delta to the arm-E template.
                insights_file=None,
                psalm_number=psalm_number,
                reader_questions_file=None if (exclude_questions or skip_questions) else (reader_questions_file if reader_questions_file.exists() else None),
                suppress_questions=(exclude_questions or skip_questions),
                synthesis_discovery_file=synthesis_discovery_file,
            )
            
            # Save outputs
            with open(edited_intro_file, 'w', encoding='utf-8') as f:
                f.write(result['introduction'])
            with open(edited_verses_file, 'w', encoding='utf-8') as f:
                f.write(result['verse_commentary'])
                
            # Handle reader questions (only save if questions are enabled)
            if not exclude_questions and not skip_questions and result.get('reader_questions'):
                refined_q_file = output_path / f"psalm_{psalm_number:03d}_reader_questions_refined.json"
                questions_text = result['reader_questions']
                questions = []
                for line in questions_text.strip().split('\n'):
                    line = line.strip()
                    match = re.match(r'^(\d+)\.\s+(.+)$', line)
                    if match:
                        q = match.group(2).strip()
                        if q and len(q) > 10:
                            questions.append(q)

                if questions:
                    with open(refined_q_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'psalm_number': psalm_number,
                            'curated_questions': questions,
                            'source': 'master_writer_refined'
                        }, f, ensure_ascii=False, indent=2)
                    logger.info(f"Extracted {len(questions)} refined reader questions")

            # Track output
            editor_output = result.get('introduction', '') + "\n\n" + result.get('verse_commentary', '')
            tracker.track_step_output("master_editor", editor_output)
            tracker.track_model_for_step("master_writer", master_editor.model)

            # Track usage stats explicitly to ensure prompt size is captured
            if 'input_char_count' in result:
                tracker.track_step_usage(
                    "master_editor",
                    input_chars=result['input_char_count'],
                    input_tokens=result.get('input_token_count', 0),
                    output_chars=len(editor_output),
                    output_tokens=result.get('output_token_count', 0)
                )

            logger.info(f"Master Writer complete for Psalm {psalm_number}")
            print(f"  Introduction: {edited_intro_file}")
            print(f"  Verses: {edited_verses_file}\n")

        except Exception as e:
            halt_on_quota(e, "STEP 4: Master Writer", logger, cost_tracker, output_path, psalm_number)
            logger.error(f"Master Writer failed: {e}", exc_info=True)
            sys.exit(1)
            
        time.sleep(delay_between_steps)
    else:
        logger.info("[STEP 4] Skipping Master Writer")
        if not edited_intro_file.exists():
            logger.warning("[STEP 4] Main commentary files missing. Proceeding without them (downstream steps requiring them will be skipped).")

    # STEP 4b: College Writer — RETIRED (Session 269, V4 unified writer)
    # See src/agents/archive/master_editor_v3_prompts.py for archived college prompt

    # --- Save stats to disk before print-ready step (which reads the JSON as a subprocess) ---
    tracker.mark_pipeline_complete() # Ensure completion date is recorded for docs
    tracker.save_json(str(output_path))

    # =====================================================================
    # STEP 5: Print-Ready
    # =====================================================================
    print_ready_file = output_path / f"psalm_{psalm_number:03d}_print_ready.md"
    if not skip_print_ready and edited_intro_file.exists() and edited_verses_file.exists():
        logger.info("[STEP 5] Print-Ready Formatting...")
        print(f"\n{'='*80}")
        print(f"STEP 5: Print-Ready Formatting")
        print(f"{'='*80}\n")
        
        command = [
            sys.executable,
            str(Path(__file__).parent.parent / "src" / "utils" / "commentary_formatter.py"),
            "--psalm", str(psalm_number),
            "--intro", str(edited_intro_file),
            "--verses", str(edited_verses_file),
            "--summary", str(summary_json_file),
            "--output", str(print_ready_file),
            "--db-path", db_path
        ]
        subprocess.run(command, check=False) # Don't crash on format error

    # =====================================================================
    # STEP 5a½: Scripture Citation Verification (Session 308)
    # Zero-cost DB-only check for misquoted biblical verses.
    # Runs BEFORE the copy editor so findings can feed into it.
    # =====================================================================
    citation_fix_prompt = None
    if not smoke_test and print_ready_file.exists():
        logger.info("[STEP 5a½] Scripture Citation Verification...")
        try:
            from src.utils.scripture_verifier import (
                verify_citations, format_verification_report, format_fix_prompt,
                filter_false_positives, verify_citations_tooluse,
            )
            verify_text = print_ready_file.read_text(encoding='utf-8')
            citation_issues = verify_citations(
                verify_text, db_path=db_path, psalm_number=psalm_number,
            )

            # LLM false-positive filter (GPT-5.1 by default, Haiku if --haiku-filter)
            use_gpt = getattr(args, 'gpt_filter', True) and not getattr(args, 'no_gpt_filter', False)
            use_haiku = getattr(args, 'haiku_filter', False)
            filter_model = None
            if use_haiku:
                filter_model = "haiku"
            elif use_gpt:
                filter_model = "gpt"

            if filter_model and citation_issues:
                fixable_count = len([i for i in citation_issues if i.issue_type == "NOT_SUBSTRING"])
                if fixable_count > 0:
                    label = "GPT-5.1" if filter_model == "gpt" else "Haiku"
                    logger.info(f"[STEP 5a½] Running {label} filter on {fixable_count} issue(s)...")
                    citation_issues, filter_stats = filter_false_positives(
                        citation_issues, commentary_text=verify_text, model=filter_model,
                        cost_tracker=cost_tracker,
                    )
                    logger.info(
                        f"[STEP 5a½] {label}: kept {filter_stats['kept_count']}, "
                        f"filtered {filter_stats['filtered_count']} "
                        f"(${filter_stats['cost']:.4f})"
                    )
                    filter_model_name = "gpt-5.1" if filter_model == "gpt" else "claude-haiku-4-5"
                    tracker.track_model_for_step("citation_filter", filter_model_name)

            # Optional tool-use verifier for broader citation coverage
            if getattr(args, 'tooluse_verify', False):
                logger.info("[STEP 5a½] Running Haiku tool-use verifier...")
                tooluse_issues, tooluse_stats = verify_citations_tooluse(
                    verify_text, db_path=db_path, psalm_number=psalm_number,
                    haiku_filter=True, cost_tracker=cost_tracker,
                )
                logger.info(
                    f"[STEP 5a½] Tool-use: {tooluse_stats.get('total_citations_found', 0)} citations, "
                    f"{len(tooluse_issues)} issue(s) "
                    f"(${tooluse_stats['cost']:.4f})"
                )
                # Merge tool-use issues with regex issues (deduplicate by reference)
                existing_refs = {i.citation_ref.strip("()").lower() for i in citation_issues}
                for ti in tooluse_issues:
                    ref_key = ti.citation_ref.strip("()").lower()
                    if ref_key not in existing_refs:
                        citation_issues.append(ti)
                        existing_refs.add(ref_key)
                        logger.info(f"[STEP 5a½] Tool-use found additional: {ti.citation_ref}")

            report = format_verification_report(citation_issues, psalm_number=psalm_number)
            report_path = output_path / f"psalm_{psalm_number:03d}_citation_verification.md"
            report_path.write_text(report, encoding='utf-8')
            if citation_issues:
                logger.warning(
                    f"[STEP 5a½] {len(citation_issues)} citation issue(s) detected "
                    f"— see {report_path.name}"
                )
                for issue in citation_issues:
                    logger.warning(f"  {issue.issue_type}: {issue.citation_ref} at {issue.location_hint}")
                # Build a fix prompt for the copy editor
                citation_fix_prompt = format_fix_prompt(citation_issues)
                if citation_fix_prompt:
                    logger.info("[STEP 5a½] Fix prompt generated for Copy Editor")
            else:
                logger.info("[STEP 5a½] All citations verified — no misquotes detected")
        except Exception as e:
            halt_on_quota(e, "STEP 5a½: Scripture Verifier", logger, cost_tracker, output_path, psalm_number)
            logger.warning(f"[STEP 5a½] Citation verification failed (non-fatal): {e}")

    # =====================================================================
    # STEP 5b: Copy Editor (Session 280)
    # =====================================================================
    copy_edited_file = output_path / f"psalm_{psalm_number:03d}_copy_edited.md"
    if not skip_copy_editor and not smoke_test and print_ready_file.exists():
        logger.info("[STEP 5b] Running Copy Editor...")
        print(f"\n{'='*80}")
        print(f"STEP 5b: Copy Editor")
        print(f"{'='*80}\n")
        try:
            copy_editor = CopyEditor(cost_tracker=cost_tracker, model=copy_model)
            ce_result = copy_editor.edit_commentary(
                psalm_number=psalm_number,
                input_file=print_ready_file,
                output_dir=output_path,
                supplementary_prompt=citation_fix_prompt,
            )
            tracker.track_model_for_step("copy_editor", copy_editor.model)
            logger.info(f"Copy Editor complete: {ce_result['edited_file']}")
        except Exception as e:
            halt_on_quota(e, "STEP 5b: Copy Editor", logger, cost_tracker, output_path, psalm_number)
            logger.error(f"Copy Editor failed: {e}", exc_info=True)
            print(f"Copy Editor error (non-fatal): {e}")
    elif skip_copy_editor:
        logger.info("[STEP 5b] Skipping Copy Editor")
        # Still track model if copy-edited file exists from a previous run
        if copy_edited_file.exists():
            tracker.track_model_for_step("copy_editor", CopyEditor.DEFAULT_MODEL)

    # =====================================================================
    # STEP 5c: Extract copy-edited sections for DOCX generation
    # =====================================================================
    if copy_edited_file.exists():
        logger.info("[STEP 5c] Extracting sections from copy-edited file for DOCX...")
        try:
            intro_text, verses_text = _extract_sections_from_copy_edited(copy_edited_file, logger=logger)
            if intro_text and verses_text:
                # Preserve originals before overwriting
                pre_ce_intro = output_path / f"psalm_{psalm_number:03d}_edited_intro_pre_copy_edit.md"
                pre_ce_verses = output_path / f"psalm_{psalm_number:03d}_edited_verses_pre_copy_edit.md"
                if edited_intro_file.exists() and not pre_ce_intro.exists():
                    import shutil
                    shutil.copy2(edited_intro_file, pre_ce_intro)
                    logger.info(f"  Preserved original intro → {pre_ce_intro.name}")
                if edited_verses_file.exists() and not pre_ce_verses.exists():
                    import shutil
                    shutil.copy2(edited_verses_file, pre_ce_verses)
                    logger.info(f"  Preserved original verses → {pre_ce_verses.name}")
                
                # Overwrite with copy-edited content
                edited_intro_file.write_text(intro_text, encoding='utf-8')
                edited_verses_file.write_text(verses_text, encoding='utf-8')
                logger.info(f"  Updated intro ({len(intro_text):,} chars) and verses ({len(verses_text):,} chars) from copy-edited source")
            else:
                logger.warning("Could not extract sections from copy-edited file; using original writer output for DOCX")
        except Exception as e:
            logger.warning(f"Failed to extract copy-edited sections: {e}; using original writer output for DOCX")

    # =====================================================================
    # STEP 5d: Beta Reader (Session 362) — reader-experience measurement.
    # NOT an editor: the report feeds no revision pass and no downstream
    # step consumes it. Non-fatal on failure.
    # =====================================================================
    if not skip_beta_reader and not smoke_test:
        beta_input = copy_edited_file if copy_edited_file.exists() else print_ready_file
        if beta_input.exists():
            logger.info("[STEP 5d] Running Beta Reader (measurement only)...")
            print(f"\n{'='*80}")
            print(f"STEP 5d: Beta Reader (reader-experience report)")
            print(f"{'='*80}\n")
            try:
                from src.agents.beta_reader import BetaReader
                beta_reader = BetaReader(cost_tracker=cost_tracker, model=beta_model)
                br_result = beta_reader.read_commentary(
                    psalm_number=psalm_number,
                    input_file=beta_input,
                    output_dir=output_path,
                )
                tracker.track_model_for_step("beta_reader", beta_reader.model)
                if br_result["scores"]:
                    logger.info(
                        "[STEP 5d] Beta-read scores: "
                        + ", ".join(f"{k} {v}/10" for k, v in br_result["scores"].items())
                    )
            except Exception as e:
                halt_on_quota(e, "STEP 5d: Beta Reader", logger, cost_tracker, output_path, psalm_number)
                logger.warning(f"Beta Reader failed (non-fatal): {e}")
    elif skip_beta_reader:
        logger.info("[STEP 5d] Skipping Beta Reader")

    # --- Save stats again after copy editor (so DOCX picks up copy_editor model) ---
    tracker.save_json(str(output_path))

    # =====================================================================
    # STEP 6: Word Doc
    # =====================================================================
    if not skip_word_doc and edited_intro_file.exists() and edited_verses_file.exists():
        logger.info("[STEP 6] Word Doc Generation...")
        print(f"\n{'='*80}")
        print(f"STEP 6: Word Document Generation (.docx)")
        print(f"{'='*80}\n")
        from src.utils.document_generator import DocumentGenerator
        
        try:
            if exclude_questions or skip_questions:
                q_file = None
            else:
                refined_q = output_path / f"psalm_{psalm_number:03d}_reader_questions_refined.json"
                q_file = refined_q if refined_q.exists() else (reader_questions_file if reader_questions_file.exists() else None)

            gen = DocumentGenerator(psalm_number, edited_intro_file, edited_verses_file, summary_json_file, docx_output_file, q_file)
            gen.generate()
        except Exception as e:
            halt_on_quota(e, "STEP 6: DOCX Generation", logger, cost_tracker, output_path, psalm_number)
            logger.error(f"Doc gen failed: {e}", exc_info=True)
            print(f"Error generating Word document: {e}")
            
    # STEP 6b: College Word Doc — RETIRED (Session 269, V4 unified writer)
    # STEP 6c: Combined .docx — RETIRED (Session 269, V4 unified writer)

    # =====================================================================
    # COMPLETE - Pipeline Summary
    # =====================================================================
    tracker.mark_pipeline_complete()
    summary_json_file = tracker.save_json(str(output_path))
    tracker.save_report(str(output_path))

    logger.info(f"\n{'=' * 80}")
    logger.info(f"ENHANCED PIPELINE (TEST) COMPLETE - Psalm {psalm_number}")
    logger.info(f"{'=' * 80}\n")

    print(f"\n{'='*80}")
    print(f"PIPELINE COMPLETE - Psalm {psalm_number}")
    print(f"{'='*80}")
    cost_file = output_path / f"psalm_{psalm_number:03d}_cost.json"
    cost_file.write_text(
        json.dumps(cost_tracker.to_dict(), indent=2, ensure_ascii=False),
        encoding='utf-8'
    )
    logger.info(f"Cost data saved to {cost_file.name}")
    print(cost_tracker.get_summary())
    if lit_echoes_cost > 0:
        print(f"Literary Echoes subtotal (Passes 1-4): ${lit_echoes_cost:.4f}")
        print("  (already included in the grand total above — shown separately "
              "because pass costs are lumped with other uses of gemini-3.1-pro-preview / gpt-5.6-terra)\n")
    if synthesis_discovery_cost > 0:
        print(f"Synthesis Discovery subtotal: ${synthesis_discovery_cost:.4f}")
        print("  (already included in the grand total above — shown separately "
              "because its model is shared with the Master Writer)\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Enhanced Pipeline (Master Writer V4)")
    parser.add_argument("psalm_number", type=int, help="Psalm number")
    parser.add_argument("--output-dir", type=str, default=None,
                       help="Output directory (default: output/psalm_NNN)")
    parser.add_argument("--db-path", type=str, default="database/tanakh.db",
                       help="Database path (default: database/tanakh.db)")
    parser.add_argument("--delay", type=int, default=120,
                       help="Delay between API-heavy steps in seconds (default: 120)")
    parser.add_argument("--resume", action="store_true",
                       help="Auto-detect last completed step and resume from there")
    parser.add_argument("--skip-macro", action="store_true")
    parser.add_argument("--skip-micro", action="store_true")
    parser.add_argument("--skip-writer", action="store_true", help="Skip Master Writer step")
    parser.add_argument("--skip-college", action="store_true", help=argparse.SUPPRESS)  # Deprecated V4: silent no-op
    parser.add_argument("--skip-print-ready", action="store_true")
    parser.add_argument("--skip-word-doc", action="store_true")
    parser.add_argument("--skip-combined-doc", action="store_true", help=argparse.SUPPRESS)  # Deprecated V4: no combined doc
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--skip-default-commentaries", action="store_true")
    # Session 373: PRODUCTION WRITER IS OPUS 5. Every prompt change from Session 370
    # onward (RULE 8b, RULE 3b-2, arm B's exemplars, arm E's translation slot, RULE 5)
    # was designed and A/B'd on Opus 5 via ab_writer_prompts.py, whose DEFAULT_MODEL is
    # claude-opus-5 — while this default silently stayed on 4.8 for six sessions. Ps 72
    # shipped arm E's prompt on the model it was not written for. Do not "restore" 4.8.
    parser.add_argument("--master-editor-model", type=str, default="claude-opus-5",
                       choices=["claude-opus-5", "claude-opus-4-8", "claude-opus-4-7", "claude-opus-4-6"],
                       help="Model for Master Writer (default: claude-opus-5)")
    parser.add_argument("--synthesis-discovery-model", type=str, default=None,
                       help="Model for the cross-verse synthesis sidecar "
                            "(default: synthesis_discovery.DEFAULT_MODEL, currently claude-opus-4-8). "
                            "Deliberately independent of --master-editor-model.")
    # Session 280: questions are SKIPPED by default.
    # --include-* opts back in; --skip-* remains for backward compat.
    parser.add_argument("--skip-questions", action="store_true",
                       help="(Default behavior) Skip question curation; use existing file if present")
    parser.add_argument("--include-questions", action="store_true",
                       help="Enable question curation (overrides default skip)")
    parser.add_argument("--exclude-questions", action="store_true",
                       help="Skip question curation and exclude from writer/doc even if file exists")
    # Session 374: the Insight Extractor was removed from the pipeline. These are
    # accepted so existing invocations and scripts keep working; --skip/--exclude
    # are now the only behaviour, so they are silent no-ops. --include-insights
    # WARNS rather than passing silently -- quietly ignoring a request for
    # insights would be worse than saying they no longer exist.
    parser.add_argument("--skip-insights", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--exclude-insights", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--include-insights", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--skip-copy-editor", action="store_true",
                       help="Skip the copy editor step (runs by default)")
    parser.add_argument("--skip-lit-echoes", action="store_true",
                       help="Skip the literary echoes generation step (runs by default, regenerating the file on every pipeline run)")
    parser.add_argument("--gpt-5-4-all", action="store_true", help="Use GPT-5.4 for all eligible agents")
    parser.add_argument("--gpt-5-4-macro", action="store_true", help="Use GPT-5.4 for Macro Analyst")
    parser.add_argument("--gpt-5-4-insight", action="store_true", help=argparse.SUPPRESS)  # Session 374: insight extractor removed; accepted, ignored
    parser.add_argument("--gpt-5-4-question", action="store_true", help="Use GPT-5.4 for Question Curator")
    parser.add_argument("--gpt-5-4-copy", action="store_true", help="Use GPT-5.4 for Copy Editor")
    parser.add_argument("--gpt-5-4-writer", action="store_true", help="Use GPT-5.4 for Master Writer")
    parser.add_argument("--haiku-filter", action="store_true",
                       help="Use Claude Haiku to filter citation verifier false positives (~$0.003/psalm)")
    parser.add_argument("--gpt-filter", action="store_true", default=True,
                       help="Use GPT-5.1 to filter citation verifier false positives (~$0.05/psalm, default)")
    parser.add_argument("--no-gpt-filter", action="store_true",
                       help="Disable the default GPT-5.1 false-positive filter")
    parser.add_argument("--tooluse-verify", action="store_true",
                       help="Also run Haiku tool-use citation verifier for broader coverage (~$0.04/psalm)")
    parser.add_argument("--skip-synthesis-discovery", action="store_true",
                       help="Skip the cross-verse synthesis discovery sidecar (Session 347). "
                            "Runs by default before the Master Writer; when run it overwrites any "
                            "prior observations file. Output: output/psalm_NNN/psalm_NNN_synthesis_discovery.md")
    parser.add_argument("--synthesis-discovery", action="store_true", help=argparse.SUPPRESS)  # legacy no-op (default-on now)
    parser.add_argument("--reuse-synthesis-discovery", action="store_true",
                       help="Reuse an existing psalm_NNN_synthesis_discovery.md in the output dir "
                            "instead of regenerating it (~$2 saved). The writer still receives the "
                            "observations. Ignored if the file is missing (fresh generation runs).")
    parser.add_argument("--beta-reader", action="store_true",
                       help="Run the beta-reader step (~$0.08). OFF BY DEFAULT since Session 372: "
                            "measured against a FIXED text its scores move by up to 3 points and its "
                            "UNEXPLAINED GRAMMAR counter by up to 6, so a single read carries little "
                            "information and repeated reads cost more than they are worth. Kept "
                            "available for deliberate one-off reads. Output: psalm_NNN_beta_read.md")
    parser.add_argument("--skip-beta-reader", action="store_true",
                       help="Deprecated no-op — the beta reader is already off by default "
                            "(Session 372). Accepted so existing invocations keep working.")
    parser.add_argument("--beta-model", type=str, default=None,
                       help="Override the beta-reader model (default: claude-sonnet-4-6)")

    args = parser.parse_args()

    # Set output directory with psalm-specific subdirectory
    if not args.output_dir:
        args.output_dir = f"output/psalm_{args.psalm_number}"

    # Resolve include/skip logic: --include-* overrides the default skip
    effective_skip_questions = not args.include_questions  # default: True (skipped)

    # Session 374: the Insight Extractor is gone. Say so instead of ignoring it.
    if args.include_insights:
        print("WARNING: --include-insights has no effect. The Insight Extractor was "
              "removed in Session 374 (unused in production since Psalm 30, 2026-03-08).")

    # Ensure UTF-8 encoding on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    print(f"\n{'='*80}")
    print(f"ENHANCED COMMENTARY PIPELINE - Psalm {args.psalm_number}")
    print(f"{'='*80}\n")
    print(f"Output Directory: {args.output_dir}")
    print(f"Database: {args.db_path}")
    print(f"Rate Limit Delay: {args.delay} seconds")
    print(f"Master Writer Model: {args.master_editor_model}")
    print(f"Copy Editor: {'SKIP' if args.skip_copy_editor else 'ON'}")
    print(f"Synthesis Discovery: {'SKIP' if args.skip_synthesis_discovery else 'ON'}")
    print(f"Beta Reader: {'ON' if args.beta_reader else 'OFF (default since S372)'}")
    print(f"Questions: {'ON' if args.include_questions else 'SKIP (default)'}")
    
    # Session 367: the GPT default moved gpt-5.4 -> gpt-5.6-terra (same tier,
    # same price). The --gpt-5-4-* flags keep their names and now act as
    # "pin back to the pre-367 model" escape hatches.
    macro_mdl = "gpt-5.4" if (args.gpt_5_4_all or args.gpt_5_4_macro) else "claude-opus-4-8"
    question_mdl = "gpt-5.4" if (args.gpt_5_4_all or args.gpt_5_4_question) else "gpt-5.6-terra"
    # Session 368: the copy editor is the one GPT agent NOT on Terra — Terra
    # overreaches as an editor (docs/plans/COPY_EDITOR_TERRA_FINDINGS.md), so it
    # follows CopyEditor.DEFAULT_MODEL rather than the Terra default above.
    copy_mdl = "gpt-5.4" if (args.gpt_5_4_all or args.gpt_5_4_copy) else CopyEditor.DEFAULT_MODEL
    
    if args.gpt_5_4_all or args.gpt_5_4_writer:
        args.master_editor_model = "gpt-5.4"
    if args.gpt_5_4_all or args.gpt_5_4_writer:
        print(f"Override: Master Writer using GPT-5.4")
    if args.gpt_5_4_all or args.gpt_5_4_macro:
        print(f"Override: Macro Analyst using GPT-5.4")
    if args.gpt_5_4_all or args.gpt_5_4_question:
        print(f"Override: Question Curator using GPT-5.4")
    if args.gpt_5_4_all or args.gpt_5_4_copy:
        print(f"Override: Copy Editor using GPT-5.4")
    print()

    run_enhanced_pipeline(
        psalm_number=args.psalm_number,
        output_dir=args.output_dir,
        db_path=args.db_path,
        delay_between_steps=args.delay,
        resume=args.resume,
        skip_macro=args.skip_macro,
        skip_micro=args.skip_micro,
        skip_writer=args.skip_writer,
        skip_college=args.skip_college,
        skip_print_ready=args.skip_print_ready,
        skip_word_doc=args.skip_word_doc,
        skip_combined_doc=args.skip_combined_doc,
        smoke_test=args.smoke_test,
        skip_default_commentaries=args.skip_default_commentaries,
        master_editor_model=args.master_editor_model,
        synthesis_discovery_model=args.synthesis_discovery_model,
        skip_questions=effective_skip_questions,
        exclude_questions=args.exclude_questions,
        skip_copy_editor=args.skip_copy_editor,
        skip_lit_echoes=args.skip_lit_echoes,
        macro_model=macro_mdl,
        question_model=question_mdl,
        copy_model=copy_mdl,
        synthesis_discovery=not args.skip_synthesis_discovery,
        reuse_synthesis_discovery=args.reuse_synthesis_discovery,
        skip_beta_reader=not args.beta_reader,
        beta_model=args.beta_model,
    )
