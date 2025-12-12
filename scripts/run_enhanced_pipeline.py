"""
Enhanced Pipeline Runner (Phase 4)

Complete psalm commentary generation pipeline with all enhancements:
1. MacroAnalyst - Structural analysis
2. MicroAnalyst v2 - Discovery-driven research (with enhanced figurative search)
3. SynthesisWriter - Introduction + verse commentary (with enhanced prompts)
4. MasterEditor (GPT-5.1) - Editorial review and revision to "National Book Award" level
5. Print-Ready Formatting - Final output with Hebrew/English text

Usage:
    python scripts/run_enhanced_pipeline.py PSALM_NUMBER [options]

Example:
    python scripts/run_enhanced_pipeline.py 23 --output-dir output/psalm_23

The script will:
- Generate all intermediate files
- Handle rate limiting with appropriate delays
- Produce final master-edited commentary
- Create print-ready formatted output

Author: Claude (Anthropic)
Date: 2025-10-18
"""

import sys
import os
import time
import json
import argparse
from pathlib import Path
import subprocess
import openai

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.macro_analyst import MacroAnalyst
from src.agents.micro_analyst import MicroAnalystV2
from src.agents.synthesis_writer import SynthesisWriter
from src.agents.master_editor import MasterEditor
from src.schemas.analysis_schemas import MacroAnalysis, MicroAnalysis, VerseCommentary, StructuralDivision, load_macro_analysis
from src.utils.logger import get_logger
from src.utils.pipeline_summary import PipelineSummaryTracker
from src.utils.cost_tracker import CostTracker


def _parse_research_stats_from_markdown(markdown_content: str) -> dict:
    """
    Parse research statistics from a research bundle markdown file.

    Used when skipping micro analysis to still capture stats for the bibliographical summary.

    Args:
        markdown_content: The full research bundle markdown text

    Returns:
        Dictionary with extracted stats
    """
    import re

    stats = {
        'lexicon_count': 0,
        'concordance_count': 0,
        'figurative_count': 0,
        'commentary_counts': {},
        'sacks_count': 0,
        'deep_research_available': False,
        'deep_research_chars': 0
    }

    # Count lexicon entries (## Hebrew Lexicon / BDB entries)
    lexicon_matches = re.findall(r'### \*\*([^*]+)\*\* \(', markdown_content)
    stats['lexicon_count'] = len(lexicon_matches)

    # Count concordance queries (### Query: or ### Phrase:)
    concordance_matches = re.findall(r'### (?:Query|Phrase):', markdown_content)
    stats['concordance_count'] = len(concordance_matches)

    # Count figurative language instances (- Psalm X (A-N): or similar patterns)
    figurative_matches = re.findall(r'- (?:Psalm|[A-Za-z]+) \d+[^:]*: v\.\d+', markdown_content)
    stats['figurative_count'] = len(figurative_matches)

    # Count traditional commentaries by name
    commentary_patterns = [
        (r'### Rashi', 'Rashi'),
        (r'### Ibn Ezra', 'Ibn Ezra'),
        (r'### Radak', 'Radak'),
        (r'### Metzudat David', 'Metzudat David'),
        (r'### Malbim', 'Malbim'),
        (r'### Sforno', 'Sforno'),
        (r'### Meiri', 'Meiri'),
    ]
    for pattern, name in commentary_patterns:
        matches = re.findall(pattern, markdown_content)
        if matches:
            stats['commentary_counts'][name] = len(matches)

    # Check for Rabbi Sacks references
    if '## Rabbi Sacks' in markdown_content or 'Rabbi Jonathan Sacks' in markdown_content:
        # Count individual references
        sacks_matches = re.findall(r'### [^#\n]+Sacks|Rabbi Sacks|Jonathan Sacks', markdown_content)
        stats['sacks_count'] = max(1, len(sacks_matches))

    # Check for Deep Web Research section
    if '## Deep Web Research' in markdown_content:
        stats['deep_research_available'] = True
        # Find the section and measure its length
        deep_match = re.search(r'## Deep Web Research\s*\n(.*?)(?=\n## [^#]|\Z)', markdown_content, re.DOTALL)
        if deep_match:
            stats['deep_research_chars'] = len(deep_match.group(1))

    return stats


def _parse_related_psalms_from_markdown(markdown_content: str) -> list:
    """
    Parse the related psalms section from a research bundle markdown file.

    Extracts psalm numbers from the "Related Psalms Analysis" section.
    Expected format: "### Psalm XX (Connection Score: ...)"

    Args:
        markdown_content: The full research bundle markdown text

    Returns:
        List of psalm numbers (as integers)
    """
    import re

    related_psalms = []

    # Look for the "Related Psalms Analysis" section
    if "## Related Psalms Analysis" not in markdown_content:
        return related_psalms

    # Find the section start
    start_match = re.search(r'## Related Psalms Analysis', markdown_content)
    if not start_match:
        return related_psalms

    start_pos = start_match.end()

    # Find the next ## heading (exactly ##, not ###, ####, etc.)
    end_match = re.search(r'\n## [^#]', markdown_content[start_pos:])
    if end_match:
        end_pos = start_pos + end_match.start()
        related_section = markdown_content[start_pos:end_pos]
    else:
        # No next section found, go to end of document
        related_section = markdown_content[start_pos:]

    # Find all psalm headers: "### Psalm XX (Connection Score: ...)"
    psalm_matches = re.findall(r'### Psalm (\d+)', related_section)

    for psalm_num_str in psalm_matches:
        try:
            psalm_num = int(psalm_num_str)
            related_psalms.append(psalm_num)
        except ValueError:
            pass

    return related_psalms


def run_enhanced_pipeline(
    psalm_number: int,
    output_dir: str = "output",
    db_path: str = "database/tanakh.db",
    delay_between_steps: int = 120,
    skip_macro: bool = False,
    skip_micro: bool = False,
    skip_synthesis: bool = False,
    skip_master_edit: bool = False,
    skip_college: bool = False,
    skip_print_ready: bool = False,
    skip_word_doc: bool = False,
    skip_combined_doc: bool = False,
    smoke_test: bool = False,
    skip_default_commentaries: bool = False,
    master_editor_model: str = "gpt-5"
):
    """
    Run complete enhanced pipeline for a single psalm.

    Args:
        psalm_number: Psalm number (1-150)
        output_dir: Output directory for all files
        db_path: Path to Tanakh database
        delay_between_steps: Seconds to wait between API-heavy steps (for rate limits)
        skip_macro: Skip macro analysis (use existing file)
        skip_micro: Skip micro analysis (use existing file)
        skip_synthesis: Skip synthesis (use existing file)
        skip_master_edit: Skip master editing (use existing file)
        skip_college: Skip college commentary generation (use existing file)
        skip_print_ready: Skip print-ready formatting
        skip_word_doc: Skip .docx generation
        skip_combined_doc: Skip combined .docx generation (main + college in one document)
        smoke_test: Run in smoke test mode (generates dummy data, no API calls)
        skip_default_commentaries: Use selective commentary mode (only request for specific verses)
        master_editor_model: Model to use for master editor (default: "gpt-5.1", or "claude-opus-4-5")
    """
    logger = get_logger("enhanced_pipeline")
    logger.info(f"=" * 80)
    logger.info(f"ENHANCED PIPELINE - Psalm {psalm_number}")
    if smoke_test:
        logger.info("SMOKE TEST MODE ENABLED - NO API CALLS WILL BE MADE")
    logger.info(f"=" * 80)

    # --- Initialize Pipeline Summary Tracker (with resume capability) ---
    output_path = Path(output_dir)
    summary_json_file = output_path / f"psalm_{psalm_number:03d}_pipeline_stats.json"
    
    # Check if we are resuming a run (any skip flag is true)
    is_resuming = any([skip_macro, skip_micro, skip_synthesis, skip_master_edit, skip_college, skip_print_ready, skip_word_doc]) and not smoke_test

    # Determine if this is a "true resume" (only skipping to output steps) vs "reusing research" (running fresh analysis)
    # If synthesis or master_editor are NOT skipped, this is a fresh analysis run
    is_fresh_analysis = not skip_synthesis or not skip_master_edit

    initial_data = None
    if is_resuming and summary_json_file.exists():
        try:
            logger.info(f"Resuming pipeline run. Loading existing stats from {summary_json_file}")
            with open(summary_json_file, 'r', encoding='utf-8') as f:
                initial_data = json.load(f)

            # If running fresh analysis (synthesis or master_editor), clear old pipeline dates
            # to avoid showing stale run dates from previous pipeline
            if is_fresh_analysis and initial_data:
                logger.info("Running fresh analysis with reused research. Resetting pipeline dates.")
                initial_data['pipeline_start'] = None  # Will use current time
                initial_data['pipeline_end'] = None
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load existing stats file, starting fresh. Error: {e}")

    tracker = PipelineSummaryTracker(psalm_number=psalm_number, initial_data=initial_data)
    logger.info("Pipeline summary tracking enabled.")

    # Initialize cost tracker for API usage and costs
    cost_tracker = CostTracker()
    logger.info("Cost tracking enabled for all models.")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # File paths
    macro_file = output_path / f"psalm_{psalm_number:03d}_macro.json"
    micro_file = output_path / f"psalm_{psalm_number:03d}_micro_v2.json"
    research_file = output_path / f"psalm_{psalm_number:03d}_research_v2.md"
    synthesis_intro_file = output_path / f"psalm_{psalm_number:03d}_synthesis_intro.md"
    synthesis_verses_file = output_path / f"psalm_{psalm_number:03d}_synthesis_verses.md"
    edited_intro_file = output_path / f"psalm_{psalm_number:03d}_edited_intro.md"
    edited_verses_file = output_path / f"psalm_{psalm_number:03d}_edited_verses.md"
    edited_assessment_file = output_path / f"psalm_{psalm_number:03d}_assessment.md"
    docx_output_file = output_path / f"psalm_{psalm_number:03d}_commentary.docx"
    # College edition file paths
    edited_intro_college_file = output_path / f"psalm_{psalm_number:03d}_edited_intro_college.md"
    edited_verses_college_file = output_path / f"psalm_{psalm_number:03d}_edited_verses_college.md"
    edited_assessment_college_file = output_path / f"psalm_{psalm_number:03d}_assessment_college.md"
    docx_output_college_file = output_path / f"psalm_{psalm_number:03d}_commentary_college.docx"
    # Combined document file path
    docx_output_combined_file = output_path / f"psalm_{psalm_number:03d}_commentary_combined.docx"

    # =====================================================================
    # STEP 1: Macro Analysis
    # =====================================================================
    if smoke_test:
        logger.info("\n[STEP 1] SMOKE TEST: Generating dummy MacroAnalyst output...")
        print(f"\n{'='*80}")
        print(f"STEP 1: SMOKE TEST - Macro Analysis")
        print(f"{'='*80}\n")
        step_start = time.time()

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

        tracker.track_verse_count(5) # Dummy value
        tracker.track_step_input("macro_analysis", "Smoke test input")
        macro_output = dummy_macro.to_markdown()
        step_duration = time.time() - step_start
        tracker.track_step_output("macro_analysis", macro_output, duration=step_duration)
        tracker.track_model_for_step("macro_analysis", "smoke-test-model-macro")
        tracker.track_macro_questions(dummy_macro.research_questions)

        logger.info(f"✓ SMOKE TEST: Dummy macro analysis saved to {macro_file}")
        print(f"✓ SMOKE TEST: Dummy macro analysis complete: {macro_file}\n")

    elif not skip_macro or not macro_file.exists():
        logger.info("\n[STEP 1] Running MacroAnalyst...")
        print(f"\n{'='*80}")
        print(f"STEP 1: Macro Analysis (Structural Thesis)")
        print(f"{'='*80}\n")

        step_start = time.time()

        # Get psalm text for input tracking
        from src.data_sources.tanakh_database import TanakhDatabase
        db = TanakhDatabase(Path(db_path))
        psalm = db.get_psalm(psalm_number)
        if psalm:
            tracker.track_verse_count(len(psalm.verses))
            # Track approximate input (psalm text)
            psalm_text = "\n".join([f"{v.verse}: {v.hebrew} / {v.english}" for v in psalm.verses])
            tracker.track_step_input("macro_analysis", psalm_text)

        macro_analyst = MacroAnalyst(cost_tracker=cost_tracker)
        macro_model = macro_analyst.model
        macro_analysis = macro_analyst.analyze_psalm(psalm_number)

        # Save macro analysis
        from src.schemas.analysis_schemas import save_analysis
        save_analysis(macro_analysis, str(macro_file), format="json")

        # Track output
        macro_output = macro_analysis.to_markdown()
        step_duration = time.time() - step_start
        tracker.track_step_output("macro_analysis", macro_output, duration=step_duration)
        tracker.track_model_for_step("macro_analysis", macro_model)

        # Track macro questions
        if macro_analysis.research_questions:
            tracker.track_macro_questions(macro_analysis.research_questions)

        logger.info(f"✓ Macro analysis saved to {macro_file}")
        print(f"✓ Macro analysis complete: {macro_file}\n")

        # Rate limit delay
        time.sleep(delay_between_steps)
    else:
        logger.info(f"[STEP 1] Skipping macro analysis (using existing {macro_file})")
        print(f"\nSkipping Step 1 (using existing macro analysis)\n")
        # Use default model name for tracking when skipping
        macro_model = "claude-3-5-sonnet-20241022"  # Default model
        tracker.track_model_for_step("macro_analysis", macro_model)

    # Load macro analysis
    macro_analysis = load_macro_analysis(str(macro_file))

    # =====================================================================
    # STEP 2: Micro Analysis (Enhanced Figurative Search)
    # =====================================================================
    if smoke_test:
        logger.info("\n[STEP 2] SMOKE TEST: Generating dummy MicroAnalyst output...")
        print(f"\n{'='*80}")
        print(f"STEP 2: SMOKE TEST - Micro Analysis")
        print(f"{'='*80}\n")
        step_start = time.time()

        dummy_micro = MicroAnalysis(
            psalm_number=psalm_number,
            verse_commentaries=[VerseCommentary(verse_number=1, commentary="Smoke test commentary.")],
            thematic_threads=["Smoke test theme"],
            interesting_questions=["Is this a smoke test?"]
        )
        dummy_research_bundle = "# Smoke Test Research Bundle\n\nThis is a dummy research bundle."

        from src.schemas.analysis_schemas import save_analysis
        save_analysis(dummy_micro, str(micro_file), format="json")
        with open(research_file, 'w', encoding='utf-8') as f:
            f.write(dummy_research_bundle)

        tracker.track_step_input("micro_analysis", "Smoke test input")
        micro_output = dummy_micro.to_markdown() + "\n\n" + dummy_research_bundle
        step_duration = time.time() - step_start
        tracker.track_step_output("micro_analysis", micro_output, duration=step_duration)
        tracker.track_model_for_step("micro_analysis", "smoke-test-model-micro")
        # Dummy tracking for research bundle
        # The following line is commented out because the track_research_bundle expects a ResearchBundle object
        # and creating one would require more imports and setup. For a smoke test, this is not essential.
        # tracker.track_research_bundle(dummy_research_bundle) 
        tracker.track_research_bundle_size(len(dummy_research_bundle), len(dummy_research_bundle) // 3)
        tracker.track_micro_questions(dummy_micro.interesting_questions)

        logger.info(f"✓ SMOKE TEST: Dummy micro analysis saved to {micro_file}")
        logger.info(f"✓ SMOKE TEST: Dummy research bundle saved to {research_file}")
        print(f"✓ SMOKE TEST: Dummy micro analysis complete: {micro_file}")
        print(f"✓ SMOKE TEST: Dummy research bundle complete: {research_file}\n")

    elif not skip_micro or not micro_file.exists():
        logger.info("\n[STEP 2] Running MicroAnalyst v2 (with enhanced figurative search)...")
        print(f"\n{'='*80}")
        print(f"STEP 2: Micro Analysis (Discovery + Enhanced Research)")
        print(f"{'='*80}\n")

        step_start = time.time()

        # Track input (macro analysis)
        tracker.track_step_input("micro_analysis", macro_analysis.to_markdown())

        # Determine commentary mode based on flag
        commentary_mode = "selective" if skip_default_commentaries else "all"
        logger.info(f"  Using commentary mode: {commentary_mode}")

        micro_analyst = MicroAnalystV2(db_path=db_path, commentary_mode=commentary_mode, cost_tracker=cost_tracker)
        micro_model = micro_analyst.model
        micro_analysis, research_bundle = micro_analyst.analyze_psalm(
            psalm_number,
            macro_analysis
        )

        # Save outputs
        from src.schemas.analysis_schemas import save_analysis
        save_analysis(micro_analysis, str(micro_file), format="json")

        with open(research_file, 'w', encoding='utf-8') as f:
            f.write(research_bundle.to_markdown())

        # Track output
        micro_output = micro_analysis.to_markdown() + "\n\n" + research_bundle.to_markdown()
        step_duration = time.time() - step_start
        tracker.track_step_output("micro_analysis", micro_output, duration=step_duration)
        tracker.track_model_for_step("micro_analysis", micro_model)

        # Track research requests and bundle
        tracker.track_research_requests(research_bundle.request)
        tracker.track_research_bundle(research_bundle)

        # Track research bundle size
        research_bundle_text = research_bundle.to_markdown()
        tracker.track_research_bundle_size(
            len(research_bundle_text),
            len(research_bundle_text) // 3  # Estimate ~3 chars per token
        )

        # Track micro questions
        if micro_analysis.interesting_questions:
            tracker.track_micro_questions(micro_analysis.interesting_questions)

        logger.info(f"✓ Micro analysis saved to {micro_file}")
        logger.info(f"✓ Research bundle saved to {research_file}")
        print(f"✓ Micro analysis complete: {micro_file}")
        print(f"✓ Research bundle complete: {research_file}\n")

        # Rate limit delay
        time.sleep(delay_between_steps)
    else:
        logger.info(f"[STEP 2] Skipping micro analysis (loading existing files)")
        print(f"\nSkipping Step 2 (using existing micro analysis)\n")
        # Use default model name for tracking when skipping
        micro_model = "claude-3-5-sonnet-20241022"  # Default model
        tracker.track_model_for_step("micro_analysis", micro_model)
    
    # Always load the definitive micro_analysis and research_bundle for subsequent steps
    try:
        from src.schemas.analysis_schemas import load_micro_analysis
        micro_analysis = load_micro_analysis(str(micro_file))
        with open(research_file, 'r', encoding='utf-8') as f:
            research_bundle_content = f.read()
        logger.info(f"Successfully loaded {micro_file} and {research_file} for subsequent steps.")

        # If we skipped micro analysis, we need to manually extract research stats from the markdown
        # so it gets captured in pipeline stats for the bibliographical summary
        if skip_micro:
            # Extract related psalms
            related_psalms = _parse_related_psalms_from_markdown(research_bundle_content)
            if related_psalms:
                tracker.research.related_psalms_count = len(related_psalms)
                tracker.research.related_psalms_list = related_psalms
                logger.info(f"Extracted {len(related_psalms)} related psalms from research bundle markdown")

            # Extract other research stats (lexicon, concordance, figurative, commentaries, etc.)
            research_stats = _parse_research_stats_from_markdown(research_bundle_content)
            tracker.research.lexicon_entries_count = research_stats['lexicon_count']
            tracker.research.concordance_results = {'total_queries': research_stats['concordance_count']}
            tracker.research.figurative_results = {'total_instances_used': research_stats['figurative_count']}
            tracker.research.commentary_counts = research_stats['commentary_counts']
            tracker.research.sacks_references_count = research_stats['sacks_count']
            tracker.research.deep_research_available = research_stats['deep_research_available']
            tracker.research.deep_research_included = research_stats['deep_research_available']  # If available, it was included
            tracker.research.deep_research_chars = research_stats['deep_research_chars']

            # Track research bundle size
            tracker.research.research_bundle_chars = len(research_bundle_content)
            tracker.research.research_bundle_tokens = len(research_bundle_content) // 3  # Estimate

            logger.info(f"Extracted research stats from markdown: "
                       f"lexicon={research_stats['lexicon_count']}, "
                       f"concordance={research_stats['concordance_count']}, "
                       f"figurative={research_stats['figurative_count']}, "
                       f"commentaries={len(research_stats['commentary_counts'])}, "
                       f"deep_research={'Yes' if research_stats['deep_research_available'] else 'No'}")

            # Save immediately so the update persists
            tracker.save_json(str(output_path))
            logger.info(f"Saved updated stats with research data from markdown")
    except Exception as e:
        logger.error(f"FATAL: Could not load micro analysis or research file: {e}")
        print(f"⚠ FATAL: Could not load required analysis files. Exiting.")
        sys.exit(1)


    # =====================================================================
    # STEP 3: Synthesis (Enhanced Prompts)
    # =====================================================================
    if smoke_test:
        logger.info("\n[STEP 3] SMOKE TEST: Generating dummy SynthesisWriter output...")
        print(f"\n{'='*80}")
        print(f"STEP 3: SMOKE TEST - Synthesis")
        print(f"{'='*80}\n")
        step_start = time.time()

        dummy_intro = "# Smoke Test Introduction\n\nThis is a dummy introduction."
        dummy_verses = "# Smoke Test Verse Commentary\n\nThis is dummy verse commentary."

        with open(synthesis_intro_file, 'w', encoding='utf-8') as f:
            f.write(dummy_intro)
        with open(synthesis_verses_file, 'w', encoding='utf-8') as f:
            f.write(dummy_verses)

        tracker.track_step_input("synthesis", "Smoke test input")
        synthesis_output = dummy_intro + "\n\n" + dummy_verses
        step_duration = time.time() - step_start
        tracker.track_step_output("synthesis", synthesis_output, duration=step_duration)
        tracker.track_model_for_step("synthesis", "smoke-test-model-synthesis")

        logger.info(f"✓ SMOKE TEST: Dummy introduction saved to {synthesis_intro_file}")
        logger.info(f"✓ SMOKE TEST: Dummy verse commentary saved to {synthesis_verses_file}")
        print(f"✓ SMOKE TEST: Dummy introduction complete: {synthesis_intro_file}")
        print(f"✓ SMOKE TEST: Dummy verse commentary complete: {synthesis_verses_file}\n")

    elif not skip_synthesis or not synthesis_intro_file.exists():
        logger.info("\n[STEP 3] Running SynthesisWriter (with enhanced prompts)...")
        print(f"\n{'='*80}")
        print(f"STEP 3: Synthesis (Introduction + Verse Commentary)")
        print(f"{'='*80}\n")

        step_start = time.time()

        # Track input (macro + micro + research)
        synthesis_input = macro_analysis.to_markdown() + "\n\n" + micro_analysis.to_markdown() + "\n\n" + research_bundle_content
        tracker.track_step_input("synthesis", synthesis_input)

        synthesis_writer = SynthesisWriter(cost_tracker=cost_tracker)
        synthesis_model = synthesis_writer.model
        commentary = synthesis_writer.write_commentary(
            macro_analysis=macro_analysis,
            micro_analysis=micro_analysis,
            research_bundle_content=research_bundle_content,
            psalm_number=psalm_number
        )

        # Save outputs
        with open(synthesis_intro_file, 'w', encoding='utf-8') as f:
            f.write(commentary['introduction'])

        with open(synthesis_verses_file, 'w', encoding='utf-8') as f:
            f.write(commentary['verse_commentary'])

        # Track output
        synthesis_output = commentary['introduction'] + "\n\n" + commentary['verse_commentary']
        step_duration = time.time() - step_start
        tracker.track_step_output("synthesis", synthesis_output, duration=step_duration)
        # Use the actual model used (may be Gemini if bundle was too large for Claude)
        actual_synthesis_model = synthesis_writer.synthesis_model_used
        tracker.track_model_for_step("synthesis", actual_synthesis_model)
        if actual_synthesis_model != synthesis_model:
            logger.info(f"Synthesis used {actual_synthesis_model} (fallback from {synthesis_model} due to bundle size)")

        # Update deep research status if it was removed for space during synthesis
        if synthesis_writer.deep_research_removed_for_space:
            tracker.track_deep_research_status(
                available=tracker.research.deep_research_available,
                included=False,  # It was removed
                removed_for_space=True,
                char_count=tracker.research.deep_research_chars
            )
            logger.info("Deep Web Research was removed from research bundle due to character limits")

        # Track sections that were trimmed/removed for context length
        if synthesis_writer.sections_removed:
            tracker.track_sections_trimmed(synthesis_writer.sections_removed)
            logger.info(f"Sections trimmed for context length: {', '.join(synthesis_writer.sections_removed)}")

        # Always save the trimmed research bundle when trimming occurred (has summary at bottom)
        trimmed_research_file = output_path / f"psalm_{psalm_number:03d}_research_trimmed.md"
        if synthesis_writer.trimmed_research_bundle:
            with open(trimmed_research_file, 'w', encoding='utf-8') as f:
                f.write(synthesis_writer.trimmed_research_bundle)
            logger.info(f"✓ Trimmed research bundle saved to {trimmed_research_file}")
            print(f"✓ Trimmed research bundle: {trimmed_research_file}")

        logger.info(f"✓ Introduction saved to {synthesis_intro_file}")
        logger.info(f"✓ Verse commentary saved to {synthesis_verses_file}")
        print(f"✓ Introduction complete: {synthesis_intro_file}")
        print(f"✓ Verse commentary complete: {synthesis_verses_file}\n")

        # Rate limit delay
        time.sleep(delay_between_steps)
    else:
        logger.info(f"[STEP 3] Skipping synthesis (using existing {synthesis_intro_file})")
        print(f"\nSkipping Step 3 (using existing synthesis)\n")
        # Still need to get model name for tracking
        synthesis_writer = SynthesisWriter(cost_tracker=cost_tracker)
        synthesis_model = synthesis_writer.model
        tracker.track_model_for_step("synthesis", synthesis_model)

    # =====================================================================
    # STEP 4: Master Editor (GPT-5) - NEW!
    # =====================================================================
    if smoke_test:
        logger.info("\n[STEP 4] SMOKE TEST: Generating dummy MasterEditor output...")
        print(f"\n{'='*80}")
        print(f"STEP 4: SMOKE TEST - Master Editor")
        print(f"{'='*80}\n")
        step_start = time.time()

        dummy_assessment = "# Smoke Test Assessment\n\nThis is a dummy assessment."
        dummy_revised_intro = "# Smoke Test Revised Introduction\n\nThis is a dummy revised introduction."
        dummy_revised_verses = "# Smoke Test Revised Verse Commentary\n\nThis is dummy revised verse commentary."

        with open(edited_assessment_file, 'w', encoding='utf-8') as f:
            f.write(dummy_assessment)
        with open(edited_intro_file, 'w', encoding='utf-8') as f:
            f.write(dummy_revised_intro)
        with open(edited_verses_file, 'w', encoding='utf-8') as f:
            f.write(dummy_revised_verses)

        tracker.track_step_input("master_editor", "Smoke test input")
        editor_output = dummy_assessment + "\n\n" + dummy_revised_intro + "\n\n" + dummy_revised_verses
        step_duration = time.time() - step_start
        tracker.track_step_output("master_editor", editor_output, duration=step_duration)
        tracker.track_model_for_step("master_editor", "smoke-test-model-editor")

        logger.info(f"✓ SMOKE TEST: Dummy assessment saved to {edited_assessment_file}")
        logger.info(f"✓ SMOKE TEST: Dummy revised introduction saved to {edited_intro_file}")
        logger.info(f"✓ SMOKE TEST: Dummy revised verses saved to {edited_verses_file}")
        print(f"✓ SMOKE TEST: Dummy assessment complete: {edited_assessment_file}")
        print(f"✓ SMOKE TEST: Dummy revised introduction complete: {edited_intro_file}")
        print(f"✓ SMOKE TEST: Dummy revised verses complete: {edited_verses_file}\n")

        tracker.mark_pipeline_complete()
        summary_json_file = tracker.save_json(str(output_path))
        logger.info(f"Analysis complete. Statistics with completion date saved to {summary_json_file}")

    elif not skip_master_edit or not edited_intro_file.exists():
        logger.info(f"\n[STEP 4] Running MasterEditor ({master_editor_model}) for final editorial review...")
        print(f"\n{'='*80}")
        print(f"STEP 4: Master Editorial Review ({master_editor_model})")
        print(f"{'='*80}\n")
        print(f"This step uses {master_editor_model} with high reasoning effort to elevate the commentary from 'good' to 'excellent'")
        print("Expected duration: 2-5 minutes\n")

        step_start = time.time()

        # Track input (ALL materials provided to master editor)
        # The master editor receives:
        # 1. Synthesis output (intro + verses)
        # 2. Full research bundle
        # 3. Macro analysis JSON
        # 4. Micro analysis JSON
        # 5. Psalm text (Hebrew/English/LXX from database)

        # Load synthesis output
        with open(synthesis_intro_file, 'r', encoding='utf-8') as f:
            intro_content = f.read()
        with open(synthesis_verses_file, 'r', encoding='utf-8') as f:
            verses_content = f.read()

        # Load research bundle
        with open(research_file, 'r', encoding='utf-8') as f:
            research_content = f.read()

        # Load and format macro and micro analyses to match what the MasterEditor actually receives
        from src.agents.master_editor import MasterEditor as EditorFormatter
        formatter = EditorFormatter() # Use a dummy instance for formatting
        with open(macro_file, 'r', encoding='utf-8') as f:
            macro_data = json.load(f)
            macro_formatted_content = formatter._format_analysis_for_prompt(macro_data, "macro")
        with open(micro_file, 'r', encoding='utf-8') as f:
            micro_data = json.load(f)
            micro_formatted_content = formatter._format_analysis_for_prompt(micro_data, "micro")

        # Get psalm text (same as master editor does)
        from src.data_sources.tanakh_database import TanakhDatabase
        from src.agents.rag_manager import RAGManager
        db = TanakhDatabase(Path(db_path))
        rag = RAGManager("docs")
        psalm = db.get_psalm(psalm_number)
        rag_context = rag.get_rag_context(psalm_number)
        psalm_text_content = ""
        if psalm:
            psalm_lines = [f"# Psalm {psalm_number}\n"]
            lxx_verses = {}
            if rag_context and rag_context.lxx_text:
                for line in rag_context.lxx_text.split('\n'):
                    if line.startswith('v'):
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            verse_num = int(parts[0][1:])
                            lxx_verses[verse_num] = parts[1].strip()
            for verse in psalm.verses:
                psalm_lines.append(f"\n## Verse {verse.verse}")
                psalm_lines.append(f"**Hebrew:** {verse.hebrew}")
                psalm_lines.append(f"**English:** {verse.english}")
                if verse.verse in lxx_verses:
                    psalm_lines.append(f"**LXX (Greek):** {lxx_verses[verse.verse]}")
            psalm_text_content = "\n".join(psalm_lines)

        # Get analytical framework content (same as master editor does)
        analytical_framework_content = ""
        try:
            analytical_framework_content = rag.get_analytical_framework()
        except Exception as e:
            logger.warning(f"Could not load analytical framework for tracking: {e}")

        # Combine ALL inputs that master editor receives
        editor_input = (
            intro_content + "\n\n" +
            verses_content + "\n\n" +
            research_content + "\n\n" +
            macro_formatted_content + "\n\n" +
            micro_formatted_content + "\n\n" +
            psalm_text_content + "\n\n" +
            analytical_framework_content
        )
        tracker.track_step_input("master_editor", editor_input)

        master_editor = MasterEditor(
            main_model=master_editor_model,
            cost_tracker=cost_tracker
        )
        editor_model = master_editor.model
        try:
            result = master_editor.edit_commentary(
                introduction_file=synthesis_intro_file,
                verse_file=synthesis_verses_file,
                research_file=research_file,
                macro_file=macro_file,
                micro_file=micro_file,
                psalm_number=psalm_number
            )
        except openai.RateLimitError as e:
            logger.error(f"PIPELINE HALTED: OpenAI API quota exceeded during Master Editor step. {e}")
            print(f"\n⚠️ PIPELINE HALTED: OpenAI API quota exceeded. Please check your plan and billing details.")
            sys.exit(1) # Exit gracefully

        # Save outputs
        with open(edited_assessment_file, 'w', encoding='utf-8') as f:
            f.write(f"# Editorial Assessment - Psalm {psalm_number}\n\n")
            f.write(result['assessment'])

        with open(edited_intro_file, 'w', encoding='utf-8') as f:
            f.write(result['revised_introduction'])

        with open(edited_verses_file, 'w', encoding='utf-8') as f:
            f.write(result['revised_verses'])

        # Track output
        editor_output = result['assessment'] + "\n\n" + result['revised_introduction'] + "\n\n" + result['revised_verses']
        step_duration = time.time() - step_start
        tracker.track_step_output("master_editor", editor_output, duration=step_duration)
        tracker.track_model_for_step("master_editor", editor_model)

        logger.info(f"✓ Editorial assessment saved to {edited_assessment_file}")
        logger.info(f"✓ Revised introduction saved to {edited_intro_file}")
        logger.info(f"✓ Revised verses saved to {edited_verses_file}")
        print(f"✓ Editorial assessment: {edited_assessment_file}")
        print(f"✓ Revised introduction: {edited_intro_file}")
        print(f"✓ Revised verses: {edited_verses_file}\n")

        # Rate limit delay
        time.sleep(delay_between_steps)

        # --- Mark analysis complete and save stats ---
        # This is the correct place to set the "Date Produced" timestamp,
        # as the MasterEditor has just finished its work.
        tracker.mark_pipeline_complete()
        summary_json_file = tracker.save_json(str(output_path))
        logger.info(f"Analysis complete. Statistics with completion date saved to {summary_json_file}")
    else:
        logger.info(f"[STEP 4] Skipping master edit (using existing {edited_intro_file})")
        print(f"\nSkipping Step 4 (using existing master-edited files)\n")
        # Still need to get model name for tracking
        master_editor = MasterEditor(
            main_model=master_editor_model,
            cost_tracker=cost_tracker
        )
        editor_model = master_editor.model
        tracker.track_model_for_step("master_editor", editor_model)

        # If resuming, preserve the original completion date
        if is_resuming and initial_data:
            existing_date = initial_data.get('steps', {}).get('master_editor', {}).get('completion_date')
            if existing_date:
                logger.info(f"Preserving existing completion date: {existing_date}")
                tracker.track_completion_date(existing_date)

    # If skipping, we still need to ensure the summary file is defined for later steps
    if not summary_json_file.exists():
        logger.warning(f"Stats file {summary_json_file} not found. Saving current tracker state.")
        summary_json_file = tracker.save_json(str(output_path))

    # =====================================================================
    # STEP 4b: College Commentary (Separate API Call)
    # =====================================================================
    if not skip_college and not smoke_test:
        # Check if college files need regeneration:
        # 1. College file doesn't exist, OR
        # 2. Synthesis files are newer than college files (synthesis was re-run)
        college_needs_regeneration = (
            not edited_intro_college_file.exists() or
            (synthesis_intro_file.exists() and
             synthesis_intro_file.stat().st_mtime > edited_intro_college_file.stat().st_mtime)
        )

        if college_needs_regeneration:
            logger.info(f"\n[STEP 4b] Running MasterEditor ({master_editor_model}) for COLLEGE EDITION...")
            print(f"\n{'='*80}")
            print(f"STEP 4b: College Commentary Generation ({master_editor_model})")
            print(f"{'='*80}\n")
            print(f"This step uses {master_editor_model} with high reasoning to generate a separate commentary version for college students")
            print("Expected duration: 2-5 minutes\n")

            step_start = time.time()

            # Use the same inputs as regular master editor
            # College editor uses same model as main editor for consistency
            master_editor_college = MasterEditor(
                main_model=master_editor_model,
                college_model=master_editor_model,  # Use same model for college
                cost_tracker=cost_tracker
            )

            try:
                result_college = master_editor_college.edit_commentary_college(
                    introduction_file=synthesis_intro_file,
                    verse_file=synthesis_verses_file,
                    research_file=research_file,
                    macro_file=macro_file,
                    micro_file=micro_file,
                    psalm_number=psalm_number
                )
            except openai.RateLimitError as e:
                logger.error(f"PIPELINE HALTED: OpenAI API quota exceeded during College Editor step. {e}")
                print(f"\n⚠️ PIPELINE HALTED: OpenAI API quota exceeded. Please check your plan and billing details.")
                sys.exit(1)

            # Save college outputs
            with open(edited_assessment_college_file, 'w', encoding='utf-8') as f:
                f.write(f"# Editorial Assessment (College Edition) - Psalm {psalm_number}\n\n")
                f.write(result_college['assessment'])

            with open(edited_intro_college_file, 'w', encoding='utf-8') as f:
                f.write(result_college['revised_introduction'])

            with open(edited_verses_college_file, 'w', encoding='utf-8') as f:
                f.write(result_college['revised_verses'])

            step_duration = time.time() - step_start

            logger.info(f"✓ College editorial assessment saved to {edited_assessment_college_file}")
            logger.info(f"✓ College revised introduction saved to {edited_intro_college_file}")
            logger.info(f"✓ College revised verses saved to {edited_verses_college_file}")
            print(f"✓ College editorial assessment: {edited_assessment_college_file}")
            print(f"✓ College revised introduction: {edited_intro_college_file}")
            print(f"✓ College revised verses: {edited_verses_college_file}\n")

            # Rate limit delay
            time.sleep(delay_between_steps)
        else:
            logger.info(f"[STEP 4b] Skipping college commentary (existing files are up-to-date: {edited_intro_college_file})")
            print(f"\nSkipping Step 4b (college commentary files are up-to-date)\n")
    else:
        if skip_college:
            logger.info(f"[STEP 4b] Skipping college commentary generation (--skip-college flag set)")
            print(f"\nSkipping Step 4b (college commentary not requested)\n")
        else:
            logger.info(f"[STEP 4b] Skipping college commentary in smoke test mode")

    # =====================================================================
    # STEP 5: Print-Ready Formatting
    # =====================================================================
    if not skip_print_ready:
        summary_json_file = output_path / f"psalm_{psalm_number:03d}_pipeline_stats.json"
        if not summary_json_file.exists():
            # If it doesn't exist, generate a temporary one.
            logger.warning(f"Pipeline summary JSON not found at {summary_json_file}. Generating temporary summary for formatter.")
            tracker.save_json(str(output_path))

        # Define paths for the formatter
        print_ready_file = output_path / f"psalm_{psalm_number:03d}_print_ready.md"

        logger.info("\n[STEP 5] Creating print-ready formatted output...")
        print(f"\n{'='*80}")
        print(f"STEP 5: Print-Ready Formatting")
        print(f"{'='*80}\n")

        intro_to_format = edited_intro_file if edited_intro_file.exists() else synthesis_intro_file
        verses_to_format = edited_verses_file if edited_verses_file.exists() else synthesis_verses_file

        command = [
            sys.executable,
            str(Path(__file__).parent.parent / "src" / "utils" / "commentary_formatter.py"),
            "--psalm", str(psalm_number),
            "--intro", str(intro_to_format),
            "--verses", str(verses_to_format),
            "--summary", str(summary_json_file),
            "--output", str(print_ready_file),
            "--db-path", db_path
        ]

        try:
            logger.info(f"Running formatter command: {' '.join(command)}")
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
            logger.info("Formatter stdout:\n" + result.stdout)
            if result.stderr:
                logger.warning("Formatter stderr:\n" + result.stderr)
            logger.info(f"✓ Print-ready commentary saved to {print_ready_file}")
            print(f"✓ Print-ready commentary: {print_ready_file}\n")
        except Exception as e:
            logger.error(f"Error creating print-ready commentary: {e}", exc_info=True)
            if isinstance(e, subprocess.CalledProcessError):
                logger.error(f"Formatter failed with stdout:\n{e.stdout}")
                logger.error(f"Formatter failed with stderr:\n{e.stderr}")
            print(f"⚠ Error in print-ready formatting (see logs for details)\n")
    else:
        logger.info(f"[STEP 5] Skipping print-ready formatting")
        print_ready_file = output_path / f"psalm_{psalm_number:03d}_print_ready.md" # Define for return dict
        print(f"\nSkipping Step 5 (print-ready formatting)\n")

    # =====================================================================
    # STEP 6: Generate .docx Document
    # =====================================================================
    if not skip_word_doc:
        logger.info("\n[STEP 6] Creating .docx document...")
        print(f"\n{'='*80}")
        print(f"STEP 6: Generating Word Document (.docx)")
        print(f"{'='*80}\n")

        from src.utils.document_generator import DocumentGenerator

        summary_json_file = output_path / f"psalm_{psalm_number:03d}_pipeline_stats.json"

        # Use the same logic as the print-ready formatter to select input files
        intro_for_docx = edited_intro_file if edited_intro_file.exists() else synthesis_intro_file
        verses_for_docx = edited_verses_file if edited_verses_file.exists() else synthesis_verses_file

        if intro_for_docx.exists() and verses_for_docx.exists() and summary_json_file.exists():
            try:
                generator = DocumentGenerator(
                    psalm_num=psalm_number,
                    intro_path=intro_for_docx,
                    verses_path=verses_for_docx,
                    stats_path=summary_json_file,
                    output_path=docx_output_file
                )
                generator.generate()
                logger.info(f"Successfully generated Word document for Psalm {psalm_number}.")
                print(f"✓ Word document commentary: {docx_output_file}\n")
            except Exception as e:
                logger.error(f"Failed to generate .docx file for Psalm {psalm_number}: {e}", exc_info=True)
                print(f"⚠ Error in Word document generation (see logs for details)\n")
        else:
            logger.warning("Skipping .docx generation because input files (markdown or stats) were not found.")
            print(f"⚠ Skipping Word document generation: input files not found.\n")
    else:
        logger.info(f"[STEP 6] Skipping .docx generation")
        print(f"\nSkipping Step 6 (.docx generation)\n")

    # =====================================================================
    # STEP 6b: Generate College .docx Document
    # =====================================================================
    if not skip_word_doc and not skip_college and not smoke_test:
        logger.info("\n[STEP 6b] Creating college edition .docx document...")
        print(f"\n{'='*80}")
        print(f"STEP 6b: Generating College Edition Word Document (.docx)")
        print(f"{'='*80}\n")

        from src.utils.document_generator import DocumentGenerator

        summary_json_file = output_path / f"psalm_{psalm_number:03d}_pipeline_stats.json"

        # Use college-specific files if they exist, otherwise fall back to synthesis
        intro_for_college_docx = edited_intro_college_file if edited_intro_college_file.exists() else synthesis_intro_file
        verses_for_college_docx = edited_verses_college_file if edited_verses_college_file.exists() else synthesis_verses_file

        if intro_for_college_docx.exists() and verses_for_college_docx.exists() and summary_json_file.exists():
            try:
                generator_college = DocumentGenerator(
                    psalm_num=psalm_number,
                    intro_path=intro_for_college_docx,
                    verses_path=verses_for_college_docx,
                    stats_path=summary_json_file,
                    output_path=docx_output_college_file
                )
                generator_college.generate()
                logger.info(f"Successfully generated college edition Word document for Psalm {psalm_number}.")
                print(f"✓ College edition Word document: {docx_output_college_file}\n")
            except Exception as e:
                logger.error(f"Failed to generate college .docx file for Psalm {psalm_number}: {e}", exc_info=True)
                print(f"⚠ Error in college Word document generation (see logs for details)\n")
        else:
            logger.warning("Skipping college .docx generation because input files (markdown or stats) were not found.")
            print(f"⚠ Skipping college Word document generation: input files not found.\n")
    else:
        if skip_college:
            logger.info(f"[STEP 6b] Skipping college .docx generation (--skip-college flag set)")
        elif skip_word_doc:
            logger.info(f"[STEP 6b] Skipping college .docx generation (--skip-word-doc flag set)")
        else:
            logger.info(f"[STEP 6b] Skipping college .docx in smoke test mode")

    # =====================================================================
    # STEP 6c: Generate Combined .docx Document (Main + College)
    # =====================================================================
    if not skip_combined_doc and not skip_college and not smoke_test:
        logger.info("\\n[STEP 6c] Creating combined .docx document (main + college)...")
        print(f"\\n{'='*80}")
        print(f"STEP 6c: Generating Combined Word Document (.docx)")
        print(f"{'='*80}\\n")

        from src.utils.combined_document_generator import CombinedDocumentGenerator

        summary_json_file = output_path / f"psalm_{psalm_number:03d}_pipeline_stats.json"

        # Check if all required files exist
        required_files = [
            edited_intro_file,
            edited_verses_file,
            edited_intro_college_file,
            edited_verses_college_file,
            summary_json_file
        ]

        if all(f.exists() for f in required_files):
            try:
                generator_combined = CombinedDocumentGenerator(
                    psalm_num=psalm_number,
                    main_intro_path=edited_intro_file,
                    main_verses_path=edited_verses_file,
                    college_intro_path=edited_intro_college_file,
                    college_verses_path=edited_verses_college_file,
                    stats_path=summary_json_file,
                    output_path=docx_output_combined_file
                )
                generator_combined.generate()
                logger.info(f"Successfully generated combined Word document for Psalm {psalm_number}.")
                print(f"✓ Combined Word document: {docx_output_combined_file}\\n")
            except Exception as e:
                logger.error(f"Failed to generate combined .docx file for Psalm {psalm_number}: {e}", exc_info=True)
                print(f"⚠ Error in combined Word document generation (see logs for details)\\n")
        else:
            missing = [f for f in required_files if not f.exists()]
            logger.warning(f"Skipping combined .docx generation because required files were not found: {missing}")
            print(f"⚠ Skipping combined Word document generation: required files not found.\\n")
    else:
        if skip_combined_doc:
            logger.info(f"[STEP 6c] Skipping combined .docx generation (--skip-combined-doc flag set)")
        elif skip_college:
            logger.info(f"[STEP 6c] Skipping combined .docx generation (--skip-college flag set)")
        elif skip_word_doc:
            logger.info(f"[STEP 6c] Skipping combined .docx generation (--skip-word-doc flag set)")
        else:
            logger.info(f"[STEP 6c] Skipping combined .docx in smoke test mode")

    # =====================================================================
    # COMPLETE - Generate Pipeline Summary
    # FINAL REPORTING
    # =====================================================================
    logger.info(f"\n{'=' * 80}")
    logger.info(f"ENHANCED PIPELINE COMPLETE - Psalm {psalm_number}")
    logger.info(f"{'=' * 80}\n")

    logger.info("\n[SUMMARY] Generating pipeline summary report...")
    try:
        summary_file = tracker.save_report(str(output_path))
        logger.info(f"✓ Pipeline summary saved to {summary_file}")
        # The final stats JSON is already saved in the Master Editor step
        summary_json = summary_json_file
        logger.info(f"✓ Pipeline statistics can be found at {summary_json}")
        print(f"\n✓ Pipeline summary: {summary_file}")
        print(f"✓ Pipeline statistics: {summary_json}")
    except Exception as e:
        logger.error(f"Error generating pipeline summary: {e}")
        print(f"\n⚠ Warning: Could not generate pipeline summary: {e}")

    # Display cost summary at end of pipeline
    print(cost_tracker.get_summary())

    print(f"\n{'='*80}")
    print(f"ENHANCED PIPELINE COMPLETE")
    print(f"{'='*80}\n")
    print(f"Final Output: {print_ready_file}")
    print(f"\nAll files saved to: {output_path}/\n")

    return {
        'macro': macro_file,
        'micro': micro_file,
        'research': research_file,
        'synthesis_intro': synthesis_intro_file,
        'synthesis_verses': synthesis_verses_file,
        'edited_assessment': edited_assessment_file,
        'edited_intro': edited_intro_file,
        'edited_verses': edited_verses_file,
        'edited_assessment_college': edited_assessment_college_file,
        'edited_intro_college': edited_intro_college_file,
        'edited_verses_college': edited_verses_college_file,
        'print_ready': print_ready_file,
        'word_document': docx_output_file,
        'word_document_college': docx_output_college_file,
        'word_document_combined': docx_output_combined_file,
        'pipeline_summary': str(summary_json_file).replace('.json', '.md'),
        'pipeline_stats': str(summary_json_file)
    }


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description='Run enhanced commentary generation pipeline (Phase 4)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate complete commentary for Psalm 23
  python scripts/run_enhanced_pipeline.py 23

  # Custom output directory
  python scripts/run_enhanced_pipeline.py 51 --output-dir output/psalm_51

  # Resume from synthesis step (skip macro and micro)
  python scripts/run_enhanced_pipeline.py 1 --skip-macro --skip-micro

  # Skip master editing (use existing synthesis)
  python scripts/run_enhanced_pipeline.py 2 --skip-master-edit
        """
    )

    parser.add_argument('psalm_number', type=int,
                       help='Psalm number (1-150)')
    parser.add_argument('--output-dir', type=str,
                       default=None,
                       help='Output directory (default: output/test_psalm_NNN)')
    parser.add_argument('--db-path', type=str,
                       default='database/tanakh.db',
                       help='Database path (default: database/tanakh.db)')
    parser.add_argument('--delay', type=int,
                       default=120,
                       help='Delay between API-heavy steps in seconds (default: 120)')
    parser.add_argument('--skip-macro', action='store_true',
                       help='Skip macro analysis (use existing file)')
    parser.add_argument('--skip-micro', action='store_true',
                       help='Skip micro analysis (use existing file)')
    parser.add_argument('--skip-synthesis', action='store_true',
                       help='Skip synthesis (use existing file)')
    parser.add_argument('--skip-master-edit', action='store_true',
                       help='Skip master editing (use existing file)')
    parser.add_argument('--skip-college', action='store_true',
                       help='Skip college commentary generation (use existing file)')
    parser.add_argument('--skip-print-ready', action='store_true',
                       help='Skip print-ready formatting')
    parser.add_argument('--skip-word-doc', action='store_true',
                       help='Skip the final .docx generation step')
    parser.add_argument('--skip-combined-doc', action='store_true',
                       help='Skip the combined .docx generation step (main + college in one document)')
    parser.add_argument('--smoke-test', action='store_true',
                       help='Run in smoke test mode (generates dummy data, no API calls)')
    parser.add_argument('--skip-default-commentaries', action='store_true',
                       help='Use selective commentary mode (only request commentaries for specific verses instead of all verses)')
    parser.add_argument('--master-editor-model', type=str, default='gpt-5.1',
                       choices=['gpt-5', 'gpt-5.1', 'claude-opus-4-5'],
                       help='Model to use for master editor (default: gpt-5.1 with high reasoning). Use claude-opus-4-5 for maximum thinking mode.')

    args = parser.parse_args()

    # Set output directory
    if not args.output_dir:
        args.output_dir = f"output/psalm_{args.psalm_number}"

    # Ensure UTF-8 encoding on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    try:
        print(f"\n{'='*80}")
        print(f"ENHANCED COMMENTARY PIPELINE - Psalm {args.psalm_number}")
        print(f"{'='*80}\n")
        print(f"Output Directory: {args.output_dir}")
        print(f"Database: {args.db_path}")
        print(f"Rate Limit Delay: {args.delay} seconds")
        print(f"Master Editor Model: {args.master_editor_model}")
        if args.master_editor_model == 'gpt-5.1':
            print(f"  → Using GPT-5.1 with high reasoning effort (default)")
        elif args.master_editor_model == 'claude-opus-4-5':
            print(f"  → Using Claude Opus 4.5 with extended thinking (64K budget)")
        elif args.master_editor_model == 'gpt-5':
            print(f"  → Using GPT-5 with high reasoning effort")
        print()

        result = run_enhanced_pipeline(
            psalm_number=args.psalm_number,
            output_dir=args.output_dir,
            db_path=args.db_path,
            delay_between_steps=args.delay,
            skip_macro=args.skip_macro,
            skip_micro=args.skip_micro,
            skip_synthesis=args.skip_synthesis,
            skip_master_edit=args.skip_master_edit,
            skip_college=args.skip_college,
            skip_print_ready=args.skip_print_ready,
            skip_word_doc=args.skip_word_doc,
            skip_combined_doc=args.skip_combined_doc,
            smoke_test=args.smoke_test,
            skip_default_commentaries=args.skip_default_commentaries,
            master_editor_model=args.master_editor_model
        )

        return 0

    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n\nError in pipeline: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
