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
import openai

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.macro_analyst import MacroAnalyst
from src.agents.micro_analyst import MicroAnalystV2
# SynthesisWriter REMOVED
from src.agents.master_editor import MasterEditor
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

    # Count concordance results by parsing actual query headers: "### <query> (N results, ...)"
    concordance_result_counts = re.findall(r'^### .+\((\d+) results', markdown_content, re.MULTILINE)
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

    # Count traditional commentaries
    commentary_patterns = [
        (r'### .*Rashi', 'Rashi'), (r'### .*Ibn Ezra', 'Ibn Ezra'), (r'### .*Radak', 'Radak'),
        (r'### .*Metzudat David', 'Metzudat David'), (r'### .*Malbim', 'Malbim'),
        (r'### .*Sforno', 'Sforno'), (r'### .*Meiri', 'Meiri'),
        (r'### .*Torah Temimah', 'Torah Temimah'),
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
    # -----------------------------------------------------------------------
    has_liturgical_marker = '---LITURGICAL-SECTION-START---' in intro_text
    has_key_verses_header = '#### Key Verses and Phrases' in intro_text
    
    if has_liturgical_marker and has_key_verses_header:
        # Check if intro's Key Verses section has actual content after the header
        key_verses_pos = intro_text.find('#### Key Verses and Phrases')
        content_after_key_verses = intro_text[key_verses_pos + len('#### Key Verses and Phrases'):].strip()
        
        # If the Key Verses header has no substantial content after it (< 100 chars),
        # the content was likely displaced
        if len(content_after_key_verses) < 100:
            # Check if the displaced content is at the start of verses_text
            # (before the first **Verse N** header)
            first_verse_match = re.search(r'^\*\*Verse[s]?\s+\d+', verses_text, re.MULTILINE)
            if first_verse_match and first_verse_match.start() > 50:
                # There's substantial content before the first verse header —
                # this is likely the displaced liturgical key verse content
                displaced_content = verses_text[:first_verse_match.start()].strip()
                
                # Verify it looks like liturgical content (bold verse references)
                if re.search(r'\*\*Verse\s+\d+\s+(?:in|on|before|during)', displaced_content):
                    _log(f"  ⚠️  RECOVERY: Detected displaced liturgical content ({len(displaced_content):,} chars) "
                         f"at start of verse commentary. Moving back to introduction.")
                    
                    # Move it back: append to intro, remove from verses
                    intro_text = intro_text.rstrip() + '\n' + displaced_content
                    verses_text = verses_text[first_verse_match.start():].strip()
                    
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
    master_editor_model: str = "claude-opus-4-6",
    skip_insights: bool = True,      # Session 280: skipped by default, use --include-insights
    skip_questions: bool = True,     # Session 280: skipped by default, use --include-questions
    exclude_insights: bool = False,
    exclude_questions: bool = False,
    skip_copy_editor: bool = False,  # Session 280: copy editor runs by default
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
    
    is_resuming = any([skip_macro, skip_micro, skip_insights, skip_writer, skip_print_ready, skip_word_doc]) and not smoke_test
    
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
            logger.warning(f"Question curation failed: {e}")

    # =====================================================================
    # STEP 2c: Insight Extraction
    # =====================================================================
    curated_insights = None
    # Always trim research first, as other steps (or the user) may rely on it
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

    if smoke_test:
        logger.info("[STEP 2c] SMOKE TEST Insights")
        curated_insights = {"psalm_level_insights": [], "verse_insights": {}}
        with open(insights_file, 'w') as f: json.dump(curated_insights, f)
    elif not skip_insights:
        logger.info("[STEP 2c] Extracting Insights...")
        try:
            extractor = InsightExtractor(cost_tracker=cost_tracker, model=insight_model)

            # Get rich psalm text from micro_analysis for prompt
            p_text = ""
            verses = []
            if hasattr(micro_analysis, 'verse_commentaries'):
                verses = micro_analysis.verse_commentaries
            elif isinstance(micro_analysis, dict):
                verses = micro_analysis.get('verse_commentaries', [])

            # Build psalm text from database (hebrew_text/english_text don't exist in micro JSON)
            # and add phonetics from micro analysis
            if verses:
                # Handle Pydantic object or dict
                def get_attr(obj, name, default=''):
                    if isinstance(obj, dict): return obj.get(name, default)
                    return getattr(obj, name, default)

                # Build phonetic lookup from micro analysis
                phonetic_map = {}
                for v in verses:
                    v_num = get_attr(v, 'verse_number') or get_attr(v, 'verse', 0)
                    phon = get_attr(v, 'phonetic_transcription', '')
                    if phon:
                        phonetic_map[v_num] = phon

                # Get actual text from database
                db = TanakhDatabase(Path(db_path))
                p = db.get_psalm(psalm_number)
                if p:
                    verse_texts = []
                    for pv in p.verses:
                        phon = phonetic_map.get(pv.verse, '')
                        verse_block = f"Verse {pv.verse}:\nHebrew: {pv.hebrew}\nEnglish: {pv.english}"
                        if phon:
                            verse_block += f"\nPhonetic: {phon}"
                        verse_texts.append(verse_block)
                    p_text = "\n\n".join(verse_texts)

            if not p_text:
                db = TanakhDatabase(Path(db_path))
                p = db.get_psalm(psalm_number)
                p_text = "\n".join([f"{v.verse}: {v.hebrew}" for v in p.verses]) if p else ""

            curated_insights = extractor.extract_insights(psalm_number, p_text, micro_analysis, macro_analysis, trimmed)
            tracker.track_model_for_step("insight_extractor", extractor.model)
            extractor.save_insights(curated_insights, insights_file)
        except Exception as e:
            logger.warning(f"Insight extraction failed: {e}")
    else:
        # skip_insights is True — still track the model if insights file exists
        if insights_file.exists():
            tracker.track_model_for_step("insight_extractor", insight_model)

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
                insights_file=None if exclude_insights else (insights_file if insights_file.exists() else None),
                psalm_number=psalm_number,
                reader_questions_file=None if (exclude_questions or skip_questions) else (reader_questions_file if reader_questions_file.exists() else None),
                suppress_questions=(exclude_questions or skip_questions)
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
            )
            tracker.track_model_for_step("copy_editor", copy_editor.model)
            logger.info(f"Copy Editor complete: {ce_result['edited_file']}")
        except Exception as e:
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
    print(cost_tracker.get_summary())

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
    parser.add_argument("--master-editor-model", type=str, default="claude-opus-4-6",
                       choices=["claude-opus-4-6"],
                       help="Model for Master Writer (default: claude-opus-4-6)")
    # Session 280: questions and insights are SKIPPED by default.
    # --include-* flags opt back in; --skip-* flags remain for backward compat.
    parser.add_argument("--skip-insights", action="store_true",
                       help="(Default behavior) Skip insights generation; use existing file if present")
    parser.add_argument("--skip-questions", action="store_true",
                       help="(Default behavior) Skip question curation; use existing file if present")
    parser.add_argument("--include-insights", action="store_true",
                       help="Enable insights generation (overrides default skip)")
    parser.add_argument("--include-questions", action="store_true",
                       help="Enable question curation (overrides default skip)")
    parser.add_argument("--exclude-insights", action="store_true",
                       help="Skip insights generation and exclude from writer even if file exists")
    parser.add_argument("--exclude-questions", action="store_true",
                       help="Skip question curation and exclude from writer/doc even if file exists")
    parser.add_argument("--skip-copy-editor", action="store_true",
                       help="Skip the copy editor step (runs by default)")
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
    print(f"ENHANCED COMMENTARY PIPELINE - Psalm {args.psalm_number}")
    print(f"{'='*80}\n")
    print(f"Output Directory: {args.output_dir}")
    print(f"Database: {args.db_path}")
    print(f"Rate Limit Delay: {args.delay} seconds")
    print(f"Master Writer Model: {args.master_editor_model}")
    print(f"Copy Editor: {'SKIP' if args.skip_copy_editor else 'ON'}")
    print(f"Insights: {'ON' if args.include_insights else 'SKIP (default)'}")
    print(f"Questions: {'ON' if args.include_questions else 'SKIP (default)'}")
    
    macro_mdl = "gpt-5.4" if (args.gpt_5_4_all or args.gpt_5_4_macro) else "claude-opus-4-6"
    insight_mdl = "gpt-5.4" if (args.gpt_5_4_all or args.gpt_5_4_insight) else "gpt-5.4"
    question_mdl = "gpt-5.4" if (args.gpt_5_4_all or args.gpt_5_4_question) else "gpt-5.4"
    copy_mdl = "gpt-5.4" if (args.gpt_5_4_all or args.gpt_5_4_copy) else "gpt-5.4"
    
    if args.gpt_5_4_all or args.gpt_5_4_writer:
        args.master_editor_model = "gpt-5.4"
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
        exclude_insights=args.exclude_insights,
        exclude_questions=args.exclude_questions,
        skip_copy_editor=args.skip_copy_editor,
        macro_model=macro_mdl,
        insight_model=insight_mdl,
        question_model=question_mdl,
        copy_model=copy_mdl,
    )
