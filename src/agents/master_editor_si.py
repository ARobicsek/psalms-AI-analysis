"""
Master Editor SI (Special Instruction) — V4 Unified Edition

Session 269: Updated for unified V4 prompt. The college edition has been retired;
this agent now injects special instructions into the single MASTER_WRITER_PROMPT_V4.

Key Features:
- Inherits functionality from MasterEditor (V4)
- Adds SPECIAL AUTHOR DIRECTIVE section to V4 prompt
- All outputs use _SI suffix (handled by pipeline script)

Usage:
    from src.agents.master_editor_si import MasterEditorSI
"""

import sys
from pathlib import Path
from typing import Optional, Dict

# Handle imports for both module and script usage
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.utils.logger import get_logger
    from src.utils.cost_tracker import CostTracker
else:
    from src.utils.logger import get_logger
    from src.utils.cost_tracker import CostTracker

# Import the V4-based MasterEditor and unified prompt
from src.agents.master_editor import MasterEditor, MASTER_WRITER_PROMPT_V4

# Backward-compat alias (V3 names still importable)
MASTER_WRITER_PROMPT_V3 = MASTER_WRITER_PROMPT_V4
COLLEGE_WRITER_PROMPT_V3 = MASTER_WRITER_PROMPT_V4


# =============================================================================
# SI PROMPT INJECTION
# =============================================================================

# We inject the Special Instruction section into the V4 prompt.
# Insert the SI section right before the "YOUR INPUTS" section to ensure high priority.

SI_SECTION = """
## ═══════════════════════════════════════════════════════════════════════════
## SPECIAL AUTHOR DIRECTIVE (HIGHEST PRIORITY)
## ═══════════════════════════════════════════════════════════════════════════

The supervising author has provided specific, overriding instructions for this revision.
You MUST prioritize these specific notes and incorporate them into your work.

AUTHOR'S INSTRUCTIONS:
{special_instruction}

---
"""

# Inject into the unified V4 prompt
MASTER_WRITER_PROMPT_SI = MASTER_WRITER_PROMPT_V4.replace(
    "## ═══════════════════════════════════════════════════════════════════════════\n## YOUR INPUTS",
    SI_SECTION + "## ═══════════════════════════════════════════════════════════════════════════\n## YOUR INPUTS"
)

# Backward-compat alias — college SI prompt is the same as main SI prompt in V4
COLLEGE_WRITER_PROMPT_SI = MASTER_WRITER_PROMPT_SI


# =============================================================================
# MASTER EDITOR SI CLASS
# =============================================================================

class MasterEditorSI(MasterEditor):
    """
    Master Editor SI — V4 Unified Edition.

    Inherits from MasterEditor (V4) and overrides:
    - write_commentary         -> accepts special_instruction parameter
    - _perform_writer_synthesis -> uses SI V4 prompt with injected instruction
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        college_model: Optional[str] = None,
        main_model: Optional[str] = None,
        logger=None,
        cost_tracker=None
    ):
        super().__init__(
            api_key=api_key,
            college_model=college_model,
            main_model=main_model,
            logger=logger,
            cost_tracker=cost_tracker
        )
        self.special_instruction = None

    def write_commentary(
        self,
        macro_file: Path,
        micro_file: Path,
        research_file: Path,
        insights_file: Optional[Path] = None,
        psalm_number: Optional[int] = None,
        reader_questions_file: Optional[Path] = None,
        special_instruction: str = None
    ) -> Dict[str, str]:
        """
        Generate unified commentary WITH Special Instruction.
        Overrides MasterEditor.write_commentary.
        """
        self.special_instruction = special_instruction
        self.logger.info("Starting Master Writer commentary generation (SI V4 Edition)")

        if special_instruction:
            self.logger.info(f"Special instruction: {special_instruction[:100]}...")
        else:
            self.logger.warning("No special instruction provided - using SI prompt with empty instruction")

        # Load all inputs (replicating parent logic for safety since
        # parent's write_commentary doesn't accept special_instruction arg)
        macro_analysis = self._load_json_file(macro_file)
        micro_analysis = self._load_json_file(micro_file)
        if not psalm_number:
            psalm_number = macro_analysis.get('psalm_number', 0)

        psalm_text = self._get_psalm_text(psalm_number, micro_analysis)

        research_bundle_raw = self._load_text_file(research_file)
        research_bundle, _, _ = self.research_trimmer.trim_bundle(research_bundle_raw, max_chars=350000)

        curated_insights = None
        if insights_file and insights_file.exists():
            curated_insights = self._load_json_file(insights_file)

        try:
            from src.agents.rag_manager import RAGManager
            rag_manager = RAGManager("docs")
            analytical_framework = rag_manager.load_analytical_framework()
        except Exception:
            analytical_framework = "[Analytical framework not available]"

        phonetic_section = self._format_phonetic_section(micro_analysis)

        reader_questions = "[No reader questions provided]"
        if reader_questions_file and Path(reader_questions_file).exists():
           try:
               with open(reader_questions_file, 'r', encoding='utf-8') as f:
                   import json
                   rq_data = json.load(f)
               questions = rq_data.get('curated_questions', [])
               if questions:
                   reader_questions = "\\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1))
           except Exception as e:
               self.logger.warning(f"Could not load reader questions: {e}")

        if reader_questions == "[No reader questions provided]":
             reader_questions_list = macro_analysis.get('research_questions', []) + micro_analysis.get('interesting_questions', [])
             if reader_questions_list:
                 reader_questions = "\\n".join(f"{i+1}. {q}" for i, q in enumerate(reader_questions_list[:10]))

        self.logger.info(f"Writing (SI) commentary for Psalm {psalm_number}")

        return self._perform_writer_synthesis(
            psalm_number=psalm_number,
            macro_analysis=macro_analysis,
            micro_analysis=micro_analysis,
            research_bundle=research_bundle,
            psalm_text=psalm_text,
            phonetic_section=phonetic_section,
            curated_insights=curated_insights,
            analytical_framework=analytical_framework,
            reader_questions=reader_questions,
            is_college=False
        )

    def _perform_writer_synthesis(
        self,
        psalm_number: int,
        macro_analysis: Dict,
        micro_analysis: Dict,
        research_bundle: str,
        psalm_text: str,
        phonetic_section: str,
        curated_insights: Dict,
        analytical_framework: str,
        reader_questions: str,
        is_college: bool = False  # Kept for backward compat — ignored in V4
    ) -> Dict[str, str]:
        """Override to use SI V4 prompt with injected special instruction."""

        # Format common inputs
        macro_text = self._format_analysis_for_prompt(macro_analysis, "macro")
        micro_text = self._format_analysis_for_prompt(micro_analysis, "micro")
        insights_text = self._format_insights_for_prompt(curated_insights)

        # V4: Single unified SI prompt
        prompt_template = MASTER_WRITER_PROMPT_SI
        model = self.model
        debug_prefix = "master_writer_si_v4"

        prompt = prompt_template.format(
            psalm_number=psalm_number,
            psalm_text=psalm_text,
            macro_analysis=macro_text,
            micro_analysis=micro_text,
            research_bundle=research_bundle,
            phonetic_section=phonetic_section,
            curated_insights=insights_text,
            analytical_framework=analytical_framework,
            reader_questions=reader_questions,
            special_instruction=self.special_instruction or "[No special instruction provided]"
        )

        # Save prompt for debugging
        prompt_file = Path(f"output/debug/{debug_prefix}_prompt_psalm_{psalm_number}.txt")
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_text(prompt, encoding='utf-8')
        self.logger.info(f"Saved {debug_prefix} prompt to {prompt_file}")

        # Call model
        if "claude" in model.lower():
            return self._call_claude_writer(model, prompt, psalm_number, debug_prefix)
        else:
            return self._call_gpt_writer(model, prompt, psalm_number, debug_prefix)


def main():
    """Command-line interface for MasterEditorSI."""
    import argparse
    import sys

    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Master Editor SI (V4) - Editorial review with special instructions'
    )
    parser.add_argument('--intro', type=str,
                       help='Path to introduction essay markdown [UNUSED IN V4 WRITER MODE but kept for compat]')
    parser.add_argument('--verses', type=str,
                       help='Path to verse commentary markdown [UNUSED IN V4 WRITER MODE but kept for compat]')
    parser.add_argument('--research', type=str, required=True,
                       help='Path to research bundle markdown')
    parser.add_argument('--macro', type=str, required=True,
                       help='Path to macro analysis JSON')
    parser.add_argument('--micro', type=str, required=True,
                       help='Path to micro analysis JSON')
    parser.add_argument('--psalm-text', type=str, default=None,
                       help='Path to psalm text file (optional)')
    parser.add_argument('--special-instruction', type=str, required=True,
                       help='Special instruction from the author')
    parser.add_argument('--output-dir', type=str, default='output',
                       help='Output directory')
    parser.add_argument('--model', type=str, default='gpt-5.1',
                       choices=['gpt-5', 'gpt-5.1', 'claude-opus-4-5'],
                       help='Model to use for editing')
    # --college: hidden no-op for backward compatibility (deprecated V4)
    parser.add_argument('--college', action='store_true',
                       help=argparse.SUPPRESS)

    args = parser.parse_args()

    # Deprecation notice if --college was used
    if args.college:
        print("NOTE: --college flag is deprecated (V4 unified writer). Using unified prompt.")

    try:
        editor = MasterEditorSI(main_model=args.model)

        print("=" * 80)
        print("MASTER EDITOR SI V4 (Unified)")
        print("=" * 80)
        print(f"Model: {args.model}")
        print(f"Special Instruction: {args.special_instruction[:100]}...")
        print()

        result = editor.write_commentary(
            macro_file=Path(args.macro),
            micro_file=Path(args.micro),
            research_file=Path(args.research),
            psalm_number=None, # will be extracted
            special_instruction=args.special_instruction
        )

        print("RESULT PREVIEW:")
        if 'introduction' in result:
             print(result['introduction'][:500] + "...")
        print()
        print("=" * 80)
        print("Commentary generation complete!")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
