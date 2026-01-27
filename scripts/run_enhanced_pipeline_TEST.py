"""
Enhanced Pipeline Runner - TEST VERSION (Master Writer Integration)

Changes from original:
1. REMOVED Synthesis Writer step entirely.
2. REPLACED Master Editor step with Master Writer (creation mode).
3. UPDATED College step to use College Writer (creation mode).

Usage:
    python scripts/run_enhanced_pipeline_TEST.py PSALM_NUMBER [options]
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
from src.agents.master_editor import MasterEditorV2 as MasterEditor
from src.agents.question_curator import QuestionCurator
from src.agents.insight_extractor import InsightExtractor
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
        'deep_research_chars': 0
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
        (r'### Rashi', 'Rashi'), (r'### Ibn Ezra', 'Ibn Ezra'), (r'### Radak', 'Radak'),
        (r'### Metzudat David', 'Metzudat David'), (r'### Malbim', 'Malbim'),
        (r'### Sforno', 'Sforno'), (r'### Meiri', 'Meiri'),
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


def run_enhanced_pipeline(
    psalm_number: int,
    output_dir: str = "output",
    db_path: str = "database/tanakh.db",
    delay_between_steps: int = 120,
    resume: bool = False,
    skip_macro: bool = False,
    skip_micro: bool = False,
    skip_writer: bool = False,  # Changed from skip_synthesis/skip_master_edit
    skip_college: bool = False,
    skip_print_ready: bool = False,
    skip_word_doc: bool = False,
    skip_combined_doc: bool = False,
    smoke_test: bool = False,
    skip_default_commentaries: bool = False,
    master_editor_model: str = "gpt-5.1",
    skip_insights: bool = False
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
            if initial_data and 'model_usage' in initial_data:
                if 'synthesis' in initial_data['model_usage']:
                    logger.info("Removing stale 'synthesis' model data from loaded stats")
                    del initial_data['model_usage']['synthesis']
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
    # We'll skip it or create a placeholder.
    edited_assessment_file = output_path / f"psalm_{psalm_number:03d}_assessment.md"
    
    docx_output_file = output_path / f"psalm_{psalm_number:03d}_commentary.docx"
    
    edited_intro_college_file = output_path / f"psalm_{psalm_number:03d}_edited_intro_college.md"
    edited_verses_college_file = output_path / f"psalm_{psalm_number:03d}_edited_verses_college.md"
    edited_assessment_college_file = output_path / f"psalm_{psalm_number:03d}_assessment_college.md"
    docx_output_college_file = output_path / f"psalm_{psalm_number:03d}_commentary_college.docx"
    docx_output_combined_file = output_path / f"psalm_{psalm_number:03d}_commentary_combined.docx"
    
    reader_questions_file = output_path / f"psalm_{psalm_number:03d}_reader_questions.json"
    insights_file = output_path / f"psalm_{psalm_number:03d}_insights.json"

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

        macro_analyst = MacroAnalyst(cost_tracker=cost_tracker)
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
        tracker.research.deep_research_available = research_stats['deep_research_available']
        tracker.research.deep_research_included = research_stats['deep_research_available']
        tracker.research.deep_research_chars = research_stats['deep_research_chars']
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
    if not smoke_test and not reader_questions_file.exists() and macro_file.exists() and micro_file.exists():
        logger.info("[STEP 2b] Curating questions...")
        try:
            curator = QuestionCurator(cost_tracker=cost_tracker)
            q, s = curator.curate_questions(psalm_number, macro_file, micro_file)
            curator.save_questions(q, s, output_path, psalm_number)
        except Exception as e:
            logger.warning(f"Question curation failed: {e}")

    # =====================================================================
    # STEP 2c: Insight Extraction
    # =====================================================================
    curated_insights = None
    if smoke_test:
        logger.info("[STEP 2c] SMOKE TEST Insights")
        curated_insights = {"psalm_level_insights": [], "verse_insights": {}}
        with open(insights_file, 'w') as f: json.dump(curated_insights, f)
    elif not skip_insights:
        if insights_file.exists():
            logger.info("Insights exist, loading...")
            with open(insights_file, 'r', encoding='utf-8') as f: curated_insights = json.load(f)
        else:
            logger.info("[STEP 2c] Extracting Insights...")
            try:
                # Load content if needed
                if 'research_bundle_content' not in locals():
                    with open(research_file, 'r', encoding='utf-8') as f: research_bundle_content = f.read()
                
                trimmed, _, _ = research_trimmer.trim_bundle(research_bundle_content, max_chars=400000)
                extractor = InsightExtractor(cost_tracker=cost_tracker)
                
                # Get psalm text
                db = TanakhDatabase(Path(db_path))
                p = db.get_psalm(psalm_number)
                p_text = "\n".join([f"{v.verse}: {v.hebrew}" for v in p.verses]) if p else ""
                
                curated_insights = extractor.extract_insights(psalm_number, p_text, micro_analysis, trimmed)
                extractor.save_insights(curated_insights, insights_file)
            except Exception as e:
                logger.warning(f"Insight extraction failed: {e}")

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

        try:
            result = master_editor.write_commentary(
                macro_file=macro_file,
                micro_file=micro_file,
                research_file=research_file,
                insights_file=insights_file if insights_file.exists() else None,
                psalm_number=psalm_number,
                reader_questions_file=reader_questions_file if reader_questions_file.exists() else None
            )
            
            # Save outputs
            with open(edited_intro_file, 'w', encoding='utf-8') as f:
                f.write(result['introduction'])
            with open(edited_verses_file, 'w', encoding='utf-8') as f:
                f.write(result['verse_commentary'])
                
            # Handle reader questions
            if result.get('reader_questions'):
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
            logger.error("FATAL: Missing edited files")
            sys.exit(1)

    # =====================================================================
    # STEP 4b: College Writer
    # =====================================================================
    if not skip_college and not smoke_test:
        logger.info(f"\n[STEP 4b] Running College WRITER ({master_editor_model})...")
        print(f"\n{'='*80}")
        print(f"STEP 4b: College Writer ({master_editor_model})")
        print(f"{'='*80}\n")

        # Reuse existing MasterEditor instance if available, otherwise create one
        if 'master_editor' not in locals() or master_editor is None:
            master_editor = MasterEditor(main_model=master_editor_model, college_model=master_editor_model, cost_tracker=cost_tracker)

        try:
            result = master_editor.write_college_commentary(
                macro_file=macro_file,
                micro_file=micro_file,
                research_file=research_file,
                insights_file=insights_file if insights_file.exists() else None,
                psalm_number=psalm_number
            )
            
            # Track college writer stats
            # We treat this as a separate step or part of master_writer logic, 
            # but usually pipeline_summary tracks main steps.
            # If we want to track it, we'd need a new step name or just log it.
            if 'input_char_count' in result:
                logger.info(f"College Writer usage: {result['input_char_count']} chars input, {result.get('input_token_count', 0)} tokens")
            
            with open(edited_intro_college_file, 'w', encoding='utf-8') as f:
                f.write(result['introduction'])
            with open(edited_verses_college_file, 'w', encoding='utf-8') as f:
                f.write(result['verse_commentary'])

            logger.info(f"College Writer complete for Psalm {psalm_number}")
            print(f"  College Introduction: {edited_intro_college_file}")
            print(f"  College Verses: {edited_verses_college_file}\n")

        except openai.RateLimitError as e:
            logger.error(f"PIPELINE HALTED: OpenAI API quota exceeded during College Writer step. {e}")
            print(f"\nPIPELINE HALTED: OpenAI API quota exceeded. Please check your plan and billing details.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"College Writer failed: {e}", exc_info=True)

        time.sleep(delay_between_steps)

    # =====================================================================
    # STEP 5: Print-Ready
    # =====================================================================
    if not skip_print_ready:
        logger.info("[STEP 5] Print-Ready Formatting...")
        print(f"\n{'='*80}")
        print(f"STEP 5: Print-Ready Formatting")
        print(f"{'='*80}\n")
        print_ready_file = output_path / f"psalm_{psalm_number:03d}_print_ready.md"
        
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
    # STEP 6: Word Doc
    # =====================================================================
    if not skip_word_doc:
        logger.info("[STEP 6] Word Doc Generation...")
        print(f"\n{'='*80}")
        print(f"STEP 6: Word Document Generation (.docx)")
        print(f"{'='*80}\n")
        from src.utils.document_generator import DocumentGenerator
        
        try:
            refined_q = output_path / f"psalm_{psalm_number:03d}_reader_questions_refined.json"
            q_file = refined_q if refined_q.exists() else (reader_questions_file if reader_questions_file.exists() else None)
            
            gen = DocumentGenerator(psalm_number, edited_intro_file, edited_verses_file, summary_json_file, docx_output_file, q_file)
            gen.generate()
        except Exception as e:
            logger.warning(f"Doc gen failed: {e}")
            
    # =====================================================================
    # STEP 6b: College Word Doc
    # =====================================================================
    if not skip_word_doc and not smoke_test and edited_intro_college_file.exists():
        logger.info("[STEP 6b] College Word Doc...")
        print(f"\n{'='*80}")
        print(f"STEP 6b: College Word Document (.docx)")
        print(f"{'='*80}\n")
        try:
            gen = DocumentGenerator(psalm_number, edited_intro_college_file, edited_verses_college_file, summary_json_file, docx_output_college_file, None)
            gen.generate()
            print(f"  College Word doc: {docx_output_college_file}\n")
        except Exception as e:
            logger.warning(f"College Doc gen failed: {e}")

    # =====================================================================
    # STEP 6c: Generate Combined .docx Document (Main + College)
    # =====================================================================
    if not skip_combined_doc and not smoke_test:
        if skip_college and not (edited_intro_college_file.exists() and edited_verses_college_file.exists()):
            logger.info(f"[STEP 6c] Skipping combined .docx generation (--skip-college flag set and college files not found)")
        else:
            logger.info("\n[STEP 6c] Creating combined .docx document (main + college)...")
            print(f"\n{'='*80}")
            print(f"STEP 6c: Generating Combined Word Document (.docx)")
            print(f"{'='*80}\n")

            from src.utils.combined_document_generator import CombinedDocumentGenerator

            required_files = [
                edited_intro_file,
                edited_verses_file,
                edited_intro_college_file,
                edited_verses_college_file,
                summary_json_file
            ]

            if all(f.exists() for f in required_files):
                try:
                    refined_questions_file = output_path / f"psalm_{psalm_number:03d}_reader_questions_refined.json"
                    refined_questions_college_file = output_path / f"psalm_{psalm_number:03d}_reader_questions_college_refined.json"

                    main_questions = refined_questions_file if refined_questions_file.exists() else (reader_questions_file if reader_questions_file.exists() else None)
                    college_questions = refined_questions_college_file if refined_questions_college_file.exists() else None

                    generator_combined = CombinedDocumentGenerator(
                        psalm_num=psalm_number,
                        main_intro_path=edited_intro_file,
                        main_verses_path=edited_verses_file,
                        college_intro_path=edited_intro_college_file,
                        college_verses_path=edited_verses_college_file,
                        stats_path=summary_json_file,
                        output_path=docx_output_combined_file,
                        reader_questions_path=main_questions,
                        college_questions_path=college_questions
                    )
                    generator_combined.generate()
                    logger.info(f"Successfully generated combined Word document for Psalm {psalm_number}.")
                    print(f"  Combined Word document: {docx_output_combined_file}\n")
                except Exception as e:
                    logger.error(f"Failed to generate combined .docx file for Psalm {psalm_number}: {e}", exc_info=True)
                    print(f"  Error in combined Word document generation (see logs for details)\n")
            else:
                missing = [f for f in required_files if not f.exists()]
                logger.warning(f"Skipping combined .docx generation because required files were not found: {missing}")
                print(f"  Skipping combined Word document generation: required files not found.\n")
    elif skip_combined_doc:
        logger.info(f"[STEP 6c] Skipping combined .docx generation (--skip-combined-doc flag set)")

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
    parser = argparse.ArgumentParser(description="Run Enhanced Pipeline TEST (Master Writer)")
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
    parser.add_argument("--skip-college", action="store_true")
    parser.add_argument("--skip-print-ready", action="store_true")
    parser.add_argument("--skip-word-doc", action="store_true")
    parser.add_argument("--skip-combined-doc", action="store_true")
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--skip-default-commentaries", action="store_true")
    parser.add_argument("--master-editor-model", type=str, default="gpt-5.1",
                       choices=["gpt-5", "gpt-5.1", "claude-opus-4-5"],
                       help="Model for Master Writer (default: gpt-5.1)")
    parser.add_argument("--skip-insights", action="store_true")

    args = parser.parse_args()

    # Set output directory with psalm-specific subdirectory
    if not args.output_dir:
        args.output_dir = f"output/psalm_{args.psalm_number}"

    # Ensure UTF-8 encoding on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    print(f"\n{'='*80}")
    print(f"ENHANCED COMMENTARY PIPELINE (TEST - MASTER WRITER) - Psalm {args.psalm_number}")
    print(f"{'='*80}\n")
    print(f"Output Directory: {args.output_dir}")
    print(f"Database: {args.db_path}")
    print(f"Rate Limit Delay: {args.delay} seconds")
    print(f"Master Writer Model: {args.master_editor_model}")
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
        skip_insights=args.skip_insights
    )
