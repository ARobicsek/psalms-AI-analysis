"""
Test script: Generate ONLY the introduction essay using the Master Writer V4 prompt.

Reuses the same input construction as the full pipeline but asks Claude
to generate only the intro + liturgical section (skipping verse commentary).
This saves ~70% of output tokens and runs much faster.

Usage:
    python scripts/test_intro_only.py PSALM_NUMBER [--output FILE]
"""

import sys
import os
import json
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv
import anthropic

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

from src.agents.master_editor import MasterEditor, MASTER_WRITER_PROMPT_V4
from src.utils.research_trimmer import ResearchTrimmer
from src.utils.logger import get_logger


def run_intro_only(psalm_number: int, output_file: str = None):
    logger = get_logger("intro_test")
    
    output_dir = Path(f"output/psalm_{psalm_number:02d}")
    macro_file = output_dir / f"psalm_{psalm_number:03d}_macro.json"
    micro_file = output_dir / f"psalm_{psalm_number:03d}_micro_v2.json"
    research_file = output_dir / f"psalm_{psalm_number:03d}_research_v2.md"
    insights_file = output_dir / f"psalm_{psalm_number:03d}_insights.json"
    
    # Verify files exist
    for f in [macro_file, micro_file, research_file]:
        if not f.exists():
            print(f"ERROR: Missing {f}")
            sys.exit(1)
    
    # --- Build inputs exactly as MasterEditor does ---
    editor = MasterEditor(main_model="claude-opus-4-6")
    
    # Load analyses
    with open(macro_file, 'r', encoding='utf-8') as f:
        macro_analysis = json.load(f)
    with open(micro_file, 'r', encoding='utf-8') as f:
        micro_analysis = json.load(f)
    
    # Get psalm text
    psalm_text = editor._get_psalm_text(psalm_number, micro_analysis)
    logger.info(f"Psalm text: {len(psalm_text)} chars")
    
    # Load and trim research
    with open(research_file, 'r', encoding='utf-8') as f:
        research_bundle = f.read()
    trimmer = ResearchTrimmer(logger=logger)
    research_bundle, _, _ = trimmer.trim_bundle(research_bundle, max_chars=400000)
    logger.info(f"Research bundle: {len(research_bundle)} chars")
    
    # Format analyses
    macro_text = editor._format_analysis_for_prompt(macro_analysis, "macro")
    micro_text = editor._format_analysis_for_prompt(micro_analysis, "micro")
    
    # Load insights
    curated_insights = {}
    if insights_file.exists():
        with open(insights_file, 'r', encoding='utf-8') as f:
            curated_insights = json.load(f)
    insights_text = editor._format_insights_for_prompt(curated_insights)
    
    # Phonetic section
    phonetic_section = editor._format_phonetic_section(micro_analysis)
    
    # Analytical framework
    framework_path = Path("docs/architecture/analytical_framework_for_RAG.md")
    analytical_framework = framework_path.read_text(encoding='utf-8') if framework_path.exists() else ""
    
    # Build the full prompt
    prompt = MASTER_WRITER_PROMPT_V4.format(
        psalm_number=psalm_number,
        psalm_text=psalm_text,
        macro_analysis=macro_text,
        micro_analysis=micro_text,
        research_bundle=research_bundle,
        phonetic_section=phonetic_section,
        curated_insights=insights_text,
        analytical_framework=analytical_framework,
        reader_questions="[No reader questions provided]"
    )
    
    # Strip question sections (same as main pipeline)
    prompt = prompt.replace(
        "### READER QUESTIONS (initial questions)\n[No reader questions provided]\n", ""
    )
    prompt = prompt.replace(
        "**HOOK FIRST — AND CONNECT TO READER QUESTIONS**: Open with something surprising, counterintuitive, or puzzling about this psalm. Look at the READER QUESTIONS — your hook should set up one or more of these questions. Avoid bland summary openings.",
        "**HOOK FIRST**: Open with something surprising, counterintuitive, or puzzling about this psalm. Avoid bland summary openings."
    )
    
    # NOW: Replace the task section to only ask for the intro essay
    # Find and replace the output format section
    intro_only_task = """
## ═══════════════════════════════════════════════════════════════════════════
## SCOPE: INTRODUCTION ESSAY ONLY
## ═══════════════════════════════════════════════════════════════════════════

For this run, write ONLY the Introduction Essay and the Liturgical Section.
Do NOT write the verse-by-verse commentary or reader questions.

Return your response with ONLY these sections:

### INTRODUCTION ESSAY
[Essay text (800-1400 words)]

---LITURGICAL-SECTION-START---

#### Full psalm
...
#### Key verses
...
"""
    
    # Replace everything from OUTPUT FORMAT to end of prompt
    import re
    prompt = re.sub(
        r'## ═+\n## OUTPUT FORMAT.*$',
        intro_only_task,
        prompt,
        flags=re.DOTALL
    )
    
    # Also strip STAGE 3 (verse commentary) and STAGE 4 (questions) from the task
    prompt = re.sub(
        r'### STAGE 3: VERSE-BY-VERSE COMMENTARY.*?(?=## ═)',
        '',
        prompt,
        flags=re.DOTALL
    )
    prompt = re.sub(
        r'### STAGE 4: REFINED READER QUESTIONS.*?(?=## ═)',
        '',
        prompt,
        flags=re.DOTALL
    )
    # Strip validation checks for verses/questions
    prompt = re.sub(
        r'### VALIDATION CHECK — Figurative Language:.*?(?=### VALIDATION CHECK|## ═|\Z)',
        '',
        prompt,
        flags=re.DOTALL
    )
    prompt = re.sub(
        r'### VALIDATION CHECK — Reader Questions:.*?(?=## ═|\Z)',
        '',
        prompt,
        flags=re.DOTALL
    )
    
    # Save prompt for debugging
    debug_file = Path(f"output/debug/intro_only_prompt_psalm_{psalm_number}.txt")
    debug_file.parent.mkdir(parents=True, exist_ok=True)
    debug_file.write_text(prompt, encoding='utf-8')
    logger.info(f"Prompt saved to {debug_file} ({len(prompt):,} chars)")
    
    # --- Call Claude ---
    print(f"\n{'='*60}")
    print(f"  Generating intro essay for Psalm {psalm_number}")
    print(f"  Model: claude-opus-4-6 (adaptive thinking)")
    print(f"  Prompt: {len(prompt):,} chars")
    print(f"{'='*60}\n")
    
    client = anthropic.Anthropic()
    start_time = time.time()
    
    response_text = ""
    input_tokens = 0
    output_tokens = 0
    
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=16000,  # Much smaller — only need intro
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            response_text += text
        
        final_message = stream.get_final_message()
        input_tokens = final_message.usage.input_tokens
        output_tokens = final_message.usage.output_tokens
    
    elapsed = time.time() - start_time
    
    # Calculate cost (Claude Opus 4.6 pricing)
    input_cost = input_tokens * 5.0 / 1_000_000   # $5/M input
    output_cost = output_tokens * 15.0 / 1_000_000  # $15/M output (thinking included)
    # Check for thinking tokens
    thinking_tokens = 0
    if hasattr(final_message.usage, 'cache_creation_input_tokens'):
        pass
    # Opus 4.6 uses $25/M for output with thinking
    output_cost = output_tokens * 25.0 / 1_000_000
    total_cost = input_cost + output_cost
    
    print(f"\n{'='*60}")
    print(f"  COMPLETE — Psalm {psalm_number} Intro Essay")
    print(f"{'='*60}")
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Input tokens:  {input_tokens:,}")
    print(f"  Output tokens: {output_tokens:,}")
    print(f"  Input cost:  ${input_cost:.4f}")
    print(f"  Output cost: ${output_cost:.4f}")
    print(f"  TOTAL COST:  ${total_cost:.4f}")
    print(f"{'='*60}\n")
    
    # Save response
    response_file = Path(f"output/debug/intro_only_response_psalm_{psalm_number}.txt")
    response_file.write_text(response_text, encoding='utf-8')
    logger.info(f"Response saved to {response_file}")
    
    # Extract just the intro essay
    intro_match = re.search(
        r'###?\s*INTRODUCTION ESSAY\s*\n(.*?)$',
        response_text, re.DOTALL | re.IGNORECASE
    )
    
    if intro_match:
        intro_text = intro_match.group(1).strip()
        
        # Save to output file
        out_path = Path(output_file) if output_file else output_dir / f"psalm_{psalm_number:03d}_intro_plan_test.md"
        out_path.write_text(intro_text, encoding='utf-8')
        print(f"  Intro essay saved to: {out_path}")
        print(f"  Essay length: {len(intro_text):,} chars")
    else:
        print("  WARNING: Could not parse intro from response")
        out_path = output_dir / f"psalm_{psalm_number:03d}_intro_plan_test_raw.md"
        out_path.write_text(response_text, encoding='utf-8')
        print(f"  Raw response saved to: {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate intro essay only")
    parser.add_argument("psalm_number", type=int)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()
    
    run_intro_only(args.psalm_number, args.output)
