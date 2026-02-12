"""
Master Editor SI (Special Instruction) — V3 Edition

This agent extends the new MasterEditor (V3) to support special, overriding instructions
from "The Author" for creating alternative versions of commentaries.

Key Features:
- Inherits functionality from MasterEditor (V3)
- Adds SPECIAL AUTHOR DIRECTIVE section to V3 prompts
- All outputs use _SI suffix (handled by pipeline script, but agent supports it)

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

# Import the new V3-based MasterEditor
from src.agents.master_editor import MasterEditor, MASTER_WRITER_PROMPT_V3, COLLEGE_WRITER_PROMPT_V3


# =============================================================================
# SI PROMPT INJECTION
# =============================================================================

# We inject the Special Instruction section into the V3 prompts
# The V3 prompts have a specific structure. We'll insert the SI section
# right before the "YOUR INPUTS" section to ensure high priority.

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

# Inject into Master Writer V3 Prompt
# We look for the "YOUR INPUTS" header and insert before it
MASTER_WRITER_PROMPT_SI = MASTER_WRITER_PROMPT_V3.replace(
    "## ═══════════════════════════════════════════════════════════════════════════\n## YOUR INPUTS",
    SI_SECTION + "## ═══════════════════════════════════════════════════════════════════════════\n## YOUR INPUTS"
)

# Inject into College Writer V3 Prompt
COLLEGE_WRITER_PROMPT_SI = COLLEGE_WRITER_PROMPT_V3.replace(
    "## ═══════════════════════════════════════════════════════════════════════════\n## YOUR INPUTS",
    SI_SECTION + "## ═══════════════════════════════════════════════════════════════════════════\n## YOUR INPUTS"
)


# =============================================================================
# MASTER EDITOR SI CLASS
# =============================================================================

class MasterEditorSI(MasterEditor):
    """
    Master Editor SI — V3 Edition.

    Inherits from MasterEditor (V3) and overrides:
    - write_commentary
    - write_college_commentary
    - _perform_writer_synthesis    → references SI V3 prompt constants
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
        Generate definitive commentary (Writer Mode) WITH Special Instruction.
        Overrides MasterEditor.write_commentary.
        """
        self.special_instruction = special_instruction
        self.logger.info("Starting Master Writer commentary generation (SI V3 Edition)")

        if special_instruction:
            self.logger.info(f"Special instruction: {special_instruction[:100]}...")
        else:
            self.logger.warning("No special instruction provided - using SI prompt with empty instruction")

        # Delegate to parent logic to load files, but we need to intercept the final call
        # Since parent's write_commentary calls _perform_writer_synthesis, and we override
        # _perform_writer_synthesis to use SI prompts, we can actually just call super().write_commentary?
        #
        # NO: Parent's write_commentary doesn't accept `special_instruction` arg.
        # We must replicate the file loading logic or modify parent to accept **kwargs.
        # Modifying parent is cleaner but `MasterEditor` is production code we just wrote.
        # Let's replicate the loading logic for safety, similar to the V2 SI implementation.
        
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

    def write_college_commentary(
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
        Generate college commentary (Writer Mode) WITH Special Instruction.
        """
        self.special_instruction = special_instruction
        self.logger.info("Starting Master Writer COLLEGE commentary generation (SI V3 Edition)")
        
        # Load inputs - duplicating logic for safety
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
            is_college=True
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
        is_college: bool
    ) -> Dict[str, str]:
        """Override to use SI V3 prompt constants."""

        # Format common inputs
        macro_text = self._format_analysis_for_prompt(macro_analysis, "macro")
        micro_text = self._format_analysis_for_prompt(micro_analysis, "micro")
        insights_text = self._format_insights_for_prompt(curated_insights)

        # Select prompt and model — use SI prompts
        if is_college:
            prompt_template = COLLEGE_WRITER_PROMPT_SI
            model = self.college_model
            debug_prefix = "college_writer_si_v3"
        else:
            prompt_template = MASTER_WRITER_PROMPT_SI
            model = self.model
            debug_prefix = "master_writer_si_v3"

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
        description='Master Editor SI (V3) - Editorial review with special instructions'
    )
    parser.add_argument('--intro', type=str,
                       help='Path to introduction essay markdown [UNUSED IN V3 WRITER MODE but kept for compat]')
    parser.add_argument('--verses', type=str,
                       help='Path to verse commentary markdown [UNUSED IN V3 WRITER MODE but kept for compat]')
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
    parser.add_argument('--college', action='store_true',
                       help='Generate college edition instead of main edition')

    args = parser.parse_args()

    try:
        editor = MasterEditorSI(main_model=args.model)

        print("=" * 80)
        print("MASTER EDITOR SI V3")
        print("=" * 80)
        print(f"Model: {args.model}")
        print(f"Edition: {'College' if args.college else 'Main'}")
        print(f"Special Instruction: {args.special_instruction[:100]}...")
        print()

        if args.college:
            result = editor.write_college_commentary(
                macro_file=Path(args.macro),
                micro_file=Path(args.micro),
                research_file=Path(args.research),
                psalm_number=None, # will be extracted
                special_instruction=args.special_instruction
            )
        else:
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
