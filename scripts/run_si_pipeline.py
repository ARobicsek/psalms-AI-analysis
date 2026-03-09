"""
SI Pipeline Runner - V4 Unified Writer

Single-audience commentary pipeline using MASTER_WRITER_PROMPT_V4.
College Writer was retired in Session 269 (merged into unified V4 writer).

Changes from original:
1. REMOVED Synthesis Writer step entirely.
2. REPLACED Master Editor step with Master Writer (creation mode).
3. College Writer RETIRED — V4 unified writer serves all audiences.

Usage:
    python scripts/run_si_pipeline.py PSALM_NUMBER [options]
"""

import sys
import os
import time
import json
import re
import argparse
from pathlib import Path
import subprocess
import openai

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.macro_analyst import MacroAnalyst
from src.agents.micro_analyst import MicroAnalystV2
# SynthesisWriter REMOVED
from src.agents.master_editor_si import MasterEditorSI
from src.agents.question_curator import QuestionCurator
from src.agents.insight_extractor import InsightExtractor
from src.agents.copy_editor import CopyEditor
from src.schemas.analysis_schemas import MacroAnalysis, MicroAnalysis, VerseCommentary, StructuralDivision, load_macro_analysis
from src.utils.logger import get_logger
from src.utils.pipeline_summary import PipelineSummaryTracker
from src.utils.cost_tracker import CostTracker
from src.utils.research_trimmer import ResearchTrimmer


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

    # Count concordance queries
    concordance_matches = re.findall(r'### (?:Query|Phrase):', markdown_content)
    stats['concordance_count'] = len(concordance_matches)

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

    # Count traditional commentaries
    commentary_patterns = [
        (r'### .*Rashi', 'Rashi'), (r'### .*Ibn Ezra', 'Ibn Ezra'), (r'### .*Radak', 'Radak'),
        (r'### .*Metzudat David', 'Metzudat David'), (r'### .*Malbim', 'Malbim'),
        (r'### .*Sforno', 'Sforno'), (r'### .*Meiri', 'Meiri'),
    ]
    for pattern, name in commentary_patterns:
        matches = re.findall(pattern, markdown_content)
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


def _extract_sections_from_copy_edited(copy_edited_path: Path) -> tuple:
    """Extract introduction and verse commentary sections from a copy-edited markdown file.
    
    The copy editor outputs each paragraph on a single line (separated by \\n).
    The DOCX generator expects \\n\\n between paragraphs. This function restores
    the double-newline paragraph breaks after extraction.
    
    Returns:
        (intro_text, verses_text) — the raw text content of each section,
        with paragraph breaks restored for DOCX generation.
    """
    content = copy_edited_path.read_text(encoding='utf-8')
    
    intro_match = re.search(
        r'^## Introduction\n(.*?)(?=^---\s*$\n^## (?:Psalm|Verse))',
        content, re.DOTALL | re.MULTILINE
    )
    intro_text = intro_match.group(1).strip() if intro_match else ''
    
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
    
    # Restore paragraph breaks: the copy editor collapses \n\n to \n.
    # Convert every single \n to \n\n so the DOCX generator sees paragraph boundaries.
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
    skip_college: bool = False,  # DEPRECATED V4: silent no-op
    skip_print_ready: bool = False,
    skip_word_doc: bool = False,
    skip_combined_doc: bool = False,  # DEPRECATED V4: no combined doc
    smoke_test: bool = False,
    skip_default_commentaries: bool = False,
    master_editor_model: str = "gpt-5.1",
    skip_insights: bool = True,      # Session 280: skipped by default, use --include-insights
    skip_questions: bool = True,     # Session 280: skipped by default, use --include-questions
    skip_copy_editor: bool = False,  # Session 280: copy editor runs by default
    special_instruction_file: str = None,
    macro_model: str = "claude-opus-4-6",
    insight_model: str = "gpt-5.4",
    question_model: str = "gpt-5.4",
    copy_model: str = "gpt-5.4",
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
    
    is_resuming = any([skip_macro, skip_micro, skip_insights, skip_writer, skip_college, skip_print_ready, skip_word_doc]) and not smoke_test
    
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

    # File paths
    macro_file = output_path / f"psalm_{psalm_number:03d}_macro.json"
    micro_file = output_path / f"psalm_{psalm_number:03d}_micro_v2.json"
    research_file = output_path / f"psalm_{psalm_number:03d}_research_v2.md"
    
    # NEW: Writer outputs (replacing synthesis/edited split)
    # We use the "edited" names for downstream compatibility
    edited_intro_file = output_path / f"psalm_{psalm_number:03d}_edited_intro.md"
    edited_verses_file = output_path / f"psalm_{psalm_number:03d}_edited_verses.md"
    # We still produce an assessment file, maybe? The Writer prompt doesn't strictly output one.
    synthesis_intro_file = output_path / f"psalm_{psalm_number:03d}_synthesis_intro_REMOVED.md"
    synthesis_verses_file = output_path / f"psalm_{psalm_number:03d}_synthesis_verses_REMOVED.md"
    
    # SI Filenames
    edited_intro_file = output_path / f"psalm_{psalm_number:03d}_intro_SI.md"
    edited_verses_file = output_path / f"psalm_{psalm_number:03d}_verses_SI.md"
    # Note: Master Writer outputs intro/verses directly, no separate "assessment" usually, 
    # but we will track it if produced.
    
    docx_output_file = output_path / f"psalm_{psalm_number:03d}_commentary_SI.docx"
    
    # College/Combined file paths — RETIRED (Session 269, V4 unified writer)
    
    # Reader questions file
    reader_questions_file = output_path / f"psalm_{psalm_number:03d}_reader_questions.json"
    # Insight extraction file
    insights_file = output_path / f"psalm_{psalm_number:03d}_insights.json"
    
    # Load Special Instruction
    # Auto-detect from data/special_instructions/ if not explicitly provided
    special_instruction = None
    if not special_instruction_file:
        project_root = Path(__file__).parent.parent
        auto_si_path = project_root / "data" / "special_instructions" / f"special_instructions_Psalm_{psalm_number:03d}.txt"
        if auto_si_path.exists():
            special_instruction_file = str(auto_si_path)
            logger.info(f"Auto-detected special instruction file: {auto_si_path}")
        else:
            logger.info(f"No special instruction file found at {auto_si_path} (this is OK)")

    if special_instruction_file:
        si_path = Path(special_instruction_file)
        if si_path.exists():
            try:
                with open(si_path, 'r', encoding='utf-8') as f:
                    special_instruction = f.read()
                logger.info(f"Loaded special instruction ({len(special_instruction):,} chars) from {si_path}")
            except Exception as e:
                logger.error(f"Failed to load special instruction file: {e}")
        else:
            logger.warning(f"Special instruction file not found: {si_path}")

    # Resume logic
    if resume and not smoke_test:
        logger.info("RESUME MODE: Auto-detecting last completed step...")
        if not edited_intro_file.exists():
             if not insights_file.exists():
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
                 skip_insights = True
        else:
             skip_macro = True
             skip_micro = True
             skip_insights = True
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
        tracker.track_step_output("macro_analysis", macro_analysis.to_markdown())
        tracker.track_model_for_step("macro_analysis", macro_analyst.model)
        time.sleep(delay_between_steps)
    else:
        logger.info("[STEP 1] Skipping macro analysis")
        if not macro_file.exists():
            logger.error(f"FATAL: Missing {macro_file}")
            sys.exit(1)
        macro_analysis = load_macro_analysis(str(macro_file))

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
        tracker.research.concordance_results = {'total_queries': research_stats['concordance_count']}
        tracker.research.figurative_results = {'total_instances_used': research_stats['figurative_count']}
        tracker.research.figurative_parallels_reviewed = research_stats.get('figurative_parallels_reviewed', {})
        tracker.research.commentary_counts = research_stats['commentary_counts']
        tracker.research.sacks_references_count = research_stats['sacks_count']
        tracker.research.deep_research_available = research_stats.get('deep_research_available', False)
        tracker.research.deep_research_included = research_stats.get('deep_research_available', False)
        tracker.research.deep_research_chars = research_stats.get('deep_research_chars', 0)
        tracker.research.literary_echoes_available = research_stats.get('literary_echoes_available', False)
        tracker.research.literary_echoes_included = research_stats.get('literary_echoes_available', False)
        tracker.research.research_bundle_chars = len(research_bundle_content)
        tracker.research.research_bundle_tokens = len(research_bundle_content) // 3

        if research_stats.get('models_used'):
            for agent, model in research_stats['models_used'].items():
                tracker.track_model_for_step(agent, model)

        related_psalms = _parse_related_psalms_from_markdown(research_bundle_content)
        if related_psalms:
            tracker.research.related_psalms_count = len(related_psalms)
            tracker.research.related_psalms_list = related_psalms

        tracker.save_json(str(output_path))
        logger.info(f"Research stats extracted from markdown and saved")

    # =====================================================================
    # STEP 2b: Question Curation
    # =====================================================================
    if skip_questions:
        logger.info("[STEP 2b] Skipping question curation")
    elif not smoke_test and not reader_questions_file.exists() and macro_file.exists() and micro_file.exists():
        logger.info("[STEP 2b] Curating questions...")
        try:
            curator = QuestionCurator(cost_tracker=cost_tracker, model=question_model)
            q, s = curator.curate_questions(psalm_number, macro_file, micro_file)
            curator.save_questions(q, s, output_path, psalm_number)
            tracker.track_model_for_step("question_curator", curator.active_model)
        except Exception as e:
            logger.warning(f"Question curation failed: {e}")

    # =====================================================================
    # STEP 2c: Research Trimming + Insight Extraction
    # =====================================================================
    curated_insights = None
    # Always trim research first and save to disk, as other steps may rely on it
    trimmed = None
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
            logger.info(f"Saved trimmed research bundle ({len(trimmed):,} chars) to {trimmed_research_file}")

    if smoke_test:
        logger.info("[STEP 2c] SMOKE TEST Insights")
        curated_insights = {"psalm_level_insights": [], "verse_insights": {}}
        with open(insights_file, 'w') as f: json.dump(curated_insights, f)
    elif not skip_insights:
        if insights_file.exists():
            logger.info("Insights exist, loading...")
            with open(insights_file, 'r', encoding='utf-8') as f: curated_insights = json.load(f)
            # Track the model even when loading existing insights
            tracker.track_model_for_step("insight_extractor", "gpt-5.4")
        else:
            logger.info("[STEP 2c] Extracting Insights...")
            try:
                extractor = InsightExtractor(cost_tracker=cost_tracker, model=insight_model)

                # Get psalm text
                db = TanakhDatabase(Path(db_path))
                p = db.get_psalm(psalm_number)
                p_text = "\n".join([f"{v.verse}: {v.hebrew}" for v in p.verses]) if p else ""

                curated_insights = extractor.extract_insights(psalm_number, p_text, micro_analysis, trimmed)
                tracker.track_model_for_step("insight_extractor", extractor.model)
                extractor.save_insights(curated_insights, insights_file)
            except Exception as e:
                logger.warning(f"Insight extraction failed: {e}")
    else:
        # skip_insights is True — still track the model if insights file exists
        if insights_file.exists():
            tracker.track_model_for_step("insight_extractor", "gpt-5.4")

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

        master_editor = MasterEditorSI(main_model=master_editor_model, cost_tracker=cost_tracker)

        try:
            result = master_editor.write_commentary(
                macro_file=macro_file,
                micro_file=micro_file,
                research_file=research_file,
                insights_file=insights_file if insights_file.exists() else None,
                psalm_number=psalm_number,
                reader_questions_file=None if skip_questions else (reader_questions_file if reader_questions_file.exists() else None),
                special_instruction=special_instruction,
                suppress_questions=skip_questions
            )
            
            # Save outputs
            with open(edited_intro_file, 'w', encoding='utf-8') as f:
                f.write(result['introduction'])
            with open(edited_verses_file, 'w', encoding='utf-8') as f:
                f.write(result['verse_commentary'])
                
            # Handle reader questions (only save if questions are enabled)
            if not skip_questions and result.get('reader_questions'):
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

        except openai.RateLimitError as e:
            logger.error(f"PIPELINE HALTED: OpenAI API quota exceeded during Master Writer step. {e}")
            print(f"\nPIPELINE HALTED: OpenAI API quota exceeded. Please check your plan and billing details.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Master Writer failed: {e}", exc_info=True)
            sys.exit(1)
            
        time.sleep(delay_between_steps)
    else:
        logger.info("[STEP 4] Skipping Master Writer")
        if not edited_intro_file.exists():
            logger.warning("[STEP 4] Main SI commentary files missing. Proceeding without them (downstream steps requiring them will be skipped).")

    # STEP 4b: College Writer — RETIRED (Session 269, V4 unified writer)

    # --- Save stats to disk before print-ready step (which reads the JSON as a subprocess) ---
    tracker.save_json(str(output_path))

    # =====================================================================
    # STEP 5: Print-Ready
    # =====================================================================
    print_ready_file = output_path / f"psalm_{psalm_number:03d}_print_ready.md"
    if not skip_print_ready:
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
    # STEP 5b: Copy Editor (Session 280)
    # =====================================================================
    copy_edited_file = output_path / f"psalm_{psalm_number:03d}_copy_edited.md"
    if not skip_copy_editor and not smoke_test and print_ready_file.exists():
        if copy_edited_file.exists():
            logger.info("[STEP 5b] Copy-edited file exists, skipping copy editor")
            tracker.track_model_for_step("copy_editor", CopyEditor.DEFAULT_MODEL)
        else:
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
                )
                tracker.track_model_for_step("copy_editor", copy_editor.model)
                logger.info(f"Copy Editor complete: {ce_result['edited_file']}")
            except Exception as e:
                logger.error(f"Copy Editor failed: {e}", exc_info=True)
                print(f"Copy Editor error (non-fatal): {e}")
    elif skip_copy_editor:
        logger.info("[STEP 5b] Skipping Copy Editor")
        if copy_edited_file.exists():
            tracker.track_model_for_step("copy_editor", CopyEditor.DEFAULT_MODEL)

    # =====================================================================
    # STEP 5c: Extract copy-edited sections for DOCX generation
    # =====================================================================
    if copy_edited_file.exists() and not skip_copy_editor:
        logger.info("[STEP 5c] Extracting sections from copy-edited file for DOCX...")
        try:
            intro_text, verses_text = _extract_sections_from_copy_edited(copy_edited_file)
            if intro_text and verses_text:
                # Preserve originals before overwriting
                pre_ce_intro = output_path / f"psalm_{psalm_number:03d}_intro_SI_pre_copy_edit.md"
                pre_ce_verses = output_path / f"psalm_{psalm_number:03d}_verses_SI_pre_copy_edit.md"
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

    # --- Save stats again after copy editor (so DOCX picks up copy_editor model) ---
    tracker.save_json(str(output_path))

    # =====================================================================
    # STEP 6: Word Doc
    # =====================================================================
    if not skip_word_doc:
        logger.info("[STEP 6] Word Doc Generation...")
        print(f"\n{'='*80}")
        print(f"STEP 6: Word Document Generation (.docx)")
        print(f"{'='*80}\n")
        from src.utils.document_generator import DocumentGenerator

        try:
            if skip_questions:
                q_file = None
            else:
                refined_q = output_path / f"psalm_{psalm_number:03d}_reader_questions_refined.json"
                q_file = refined_q if refined_q.exists() else (reader_questions_file if reader_questions_file.exists() else None)
            
            gen = DocumentGenerator(psalm_number, edited_intro_file, edited_verses_file, summary_json_file, docx_output_file, q_file)
            gen.generate()
        except Exception as e:
            logger.warning(f"Doc gen failed: {e}")
            
    # STEP 6b/6c: College/Combined Word Docs — RETIRED (Session 269, V4 unified writer)

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
    print(cost_tracker.get_summary())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SI Pipeline (Master Writer V4)")
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
    parser.add_argument("--skip-college", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--skip-print-ready", action="store_true")
    parser.add_argument("--skip-word-doc", action="store_true")
    parser.add_argument("--skip-combined-doc", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--skip-default-commentaries", action="store_true")
    parser.add_argument("--master-editor-model", type=str, default="claude-opus-4-6",
                       choices=["gpt-5", "gpt-5.1", "claude-opus-4-6"],
                       help="Model for Master Writer (default: claude-opus-4-6)")
    # Session 280: questions and insights are SKIPPED by default.
    parser.add_argument("--skip-insights", action="store_true",
                       help="(Default behavior) Skip insights generation")
    parser.add_argument("--skip-questions", action="store_true",
                       help="(Default behavior) Skip question curation")
    parser.add_argument("--include-insights", action="store_true",
                       help="Enable insights generation (overrides default skip)")
    parser.add_argument("--include-questions", action="store_true",
                       help="Enable question curation (overrides default skip)")
    parser.add_argument("--skip-copy-editor", action="store_true",
                       help="Skip the copy editor step (runs by default)")
    parser.add_argument("--special-instruction", type=str, default=None,
                       help="Path to special instruction file")
    parser.add_argument("--gpt-5-4-all", action="store_true", help="Use GPT-5.4 for all eligible agents")
    parser.add_argument("--gpt-5-4-macro", action="store_true", help="Use GPT-5.4 for Macro Analyst")
    parser.add_argument("--gpt-5-4-insight", action="store_true", help="Use GPT-5.4 for Insight Extractor")
    parser.add_argument("--gpt-5-4-question", action="store_true", help="Use GPT-5.4 for Question Curator")
    parser.add_argument("--gpt-5-4-copy", action="store_true", help="Use GPT-5.4 for Copy Editor")
    parser.add_argument("--gpt-5-4-writer", action="store_true", help="Use GPT-5.4 for Master Writer")

    args = parser.parse_args()

    # Set output directory with psalm-specific subdirectory
    if not args.output_dir:
        args.output_dir = f"output/psalm_{args.psalm_number}"

    # Resolve include/skip logic: --include-* overrides the default skip
    effective_skip_insights = not args.include_insights  # default: True (skipped)
    effective_skip_questions = not args.include_questions  # default: True (skipped)

    # Ensure UTF-8 encoding on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    print(f"\n{'='*80}")
    print(f"SI COMMENTARY PIPELINE - Psalm {args.psalm_number}")
    print(f"{'='*80}\n")
    print(f"Output Directory: {args.output_dir}")
    print(f"Database: {args.db_path}")

    macro_mdl = "gpt-5.4" if (args.gpt_5_4_all or args.gpt_5_4_macro) else "claude-opus-4-6"
    insight_mdl = "gpt-5.4" if (args.gpt_5_4_all or args.gpt_5_4_insight) else "gpt-5.4"
    question_mdl = "gpt-5.4" if (args.gpt_5_4_all or args.gpt_5_4_question) else "gpt-5.4"
    copy_mdl = "gpt-5.4" if (args.gpt_5_4_all or args.gpt_5_4_copy) else "gpt-5.4"
    
    if args.gpt_5_4_all or args.gpt_5_4_writer:
        args.master_editor_model = "gpt-5.4"
        
    print(f"Master Writer Model: {args.master_editor_model}")
    print(f"Copy Editor: {'SKIP' if args.skip_copy_editor else 'ON'}")
    print(f"Insights: {'ON' if args.include_insights else 'SKIP (default)'}")
    print(f"Questions: {'ON' if args.include_questions else 'SKIP (default)'}")
        
    if args.gpt_5_4_all or args.gpt_5_4_writer:
        print(f"Override: Master Writer using GPT-5.4")
    if args.gpt_5_4_all or args.gpt_5_4_macro:
        print(f"Override: Macro Analyst using GPT-5.4")
    if args.gpt_5_4_all or args.gpt_5_4_insight:
        print(f"Override: Insight Extractor using GPT-5.4")
    if args.gpt_5_4_all or args.gpt_5_4_question:
        print(f"Override: Question Curator using GPT-5.4")
    if args.gpt_5_4_all or args.gpt_5_4_copy:
        print(f"Override: Copy Editor using GPT-5.4")
    print()
    print(f"Rate Limit Delay: {args.delay} seconds")
    print(f"Master Writer Model: {args.master_editor_model}")
    print(f"Copy Editor: {'SKIP' if args.skip_copy_editor else 'ON'}")
    print(f"Insights: {'ON' if args.include_insights else 'SKIP (default)'}")
    print(f"Questions: {'ON' if args.include_questions else 'SKIP (default)'}")
    # Show SI status: auto-detect if not explicitly provided
    si_display = args.special_instruction if args.special_instruction else "AUTO-DETECT"
    print(f"Special Instruction: {si_display}")
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
        skip_insights=effective_skip_insights,
        skip_questions=effective_skip_questions,
        skip_copy_editor=args.skip_copy_editor,
        special_instruction_file=args.special_instruction,
        macro_model=macro_mdl,
        insight_model=insight_mdl,
        question_model=question_mdl,
        copy_model=copy_mdl,
    )
