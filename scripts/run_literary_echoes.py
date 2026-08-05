"""
Standalone runner for the Literary Echoes agent.

Generates the literary echoes document for a single psalm, independent of the
main enhanced/SI pipelines. Default behavior is regenerate-and-overwrite; use
--skip-if-exists to preserve an existing file.

Usage:
    python scripts/run_literary_echoes.py 53
    python scripts/run_literary_echoes.py 53 --skip-if-exists
    python scripts/run_literary_echoes.py 53 --no-second-generator
    python scripts/run_literary_echoes.py 53 --output-dir output/psalm_53
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.literary_echoes_agent import (
    SECOND_GEN_EFFORT,
    SECOND_GEN_MODEL,
    VERIFY_WORKERS,
    LiteraryEchoesAgent,
)
from src.utils.cost_tracker import CostTracker
from src.utils.logger import get_logger


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Literary Echoes workflow for one psalm")
    parser.add_argument("psalm_number", type=int, help="Psalm number (1-150)")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: output/psalm_NNN)",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="database/tanakh.db",
        help="Tanakh database path (default: database/tanakh.db)",
    )
    parser.add_argument(
        "--skip-if-exists",
        action="store_true",
        help="Skip if data/literary_echoes/psalm_NNN_literary_echoes.txt already exists "
             "(default behavior is regenerate-and-overwrite)",
    )
    parser.add_argument(
        "--second-generator",
        action="store_true",
        help="EXPERIMENTAL, off by default. Also run Pass 1 on a second model and merge, "
             f"for author diversity. No Anthropic model currently works with the Pass-1 "
             f"prompt: high/medium effort trips an output content filter, and "
             f"{SECOND_GEN_MODEL} at effort={SECOND_GEN_EFFORT} (the only setting that "
             "completes) writes its deliberation into the document. A failure degrades "
             "to Gemini-only rather than failing the psalm. See the measurement table in "
             "literary_echoes_agent.py.",
    )
    parser.add_argument(
        "--second-generator-model",
        type=str,
        default=SECOND_GEN_MODEL,
        help=f"Model for the Pass 1b second generator (default: {SECOND_GEN_MODEL})",
    )
    parser.add_argument(
        "--verify-workers",
        type=int,
        default=VERIFY_WORKERS,
        help=f"Parallel Pass 3 verification calls (default: {VERIFY_WORKERS})",
    )
    args = parser.parse_args()

    # UTF-8 on Windows
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    output_dir = Path(args.output_dir or f"output/psalm_{args.psalm_number}")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger = get_logger("run_literary_echoes")
    cost_tracker = CostTracker()
    agent = LiteraryEchoesAgent(
        cost_tracker=cost_tracker,
        db_path=args.db_path,
        logger=logger,
        second_generator=args.second_generator,
        second_gen_model=args.second_generator_model,
        verify_workers=args.verify_workers,
    )

    print(f"\n{'='*80}")
    print(f"LITERARY ECHOES — Psalm {args.psalm_number}")
    print(f"{'='*80}\n")

    try:
        result = agent.generate(
            psalm_number=args.psalm_number,
            psalm_output_dir=output_dir,
            skip_if_exists=args.skip_if_exists,
        )
    except Exception as e:
        logger.error(f"[lit_echoes] FAILED: {e}", exc_info=True)
        return 1

    print(f"\nFinal file: {result.final_path}")
    print(f"Total cost: ${result.total_cost:.4f}")

    if result.passes:
        print("\nPer-pass breakdown:")
        for p in result.passes:
            calls = f" x{p.call_count}" if p.call_count > 1 else ""
            cached = f" (cached {p.cached_input_tokens:,})" if p.cached_input_tokens else ""
            print(
                f"  {p.pass_name:>8}{calls:<5} {p.model:<24} "
                f"in={p.input_tokens:>7,}{cached}  out={p.output_tokens:>7,}  "
                f"${p.cost:>7.4f}  ({p.elapsed_s:5.1f}s)"
            )

        stats = result.entry_stats
        print("\nEntry accounting:")
        print(
            f"  pass 1: {stats.get('pass_1_gemini', 0)} gemini + {stats.get('pass_1_opus', 0)} opus "
            f"-> {stats.get('pass_1_merged', 0)} merged"
        )
        print(f"  pass 2 added: {stats.get('pass_2', 0)}")
        print(
            f"  verified: {stats.get('verified_input', 0)} in -> {stats.get('final', 0)} out "
            f"({stats.get('rejected', 0)} rejected, {stats.get('corrected', 0)} corrected)"
        )
        if result.provenance:
            mix = ", ".join(f"{k}={v}" for k, v in sorted(result.provenance.items()))
            print(f"  surviving entries by source: {mix}")
        if result.notes:
            print("\nNotes:")
            for note in result.notes:
                print(f"  - {note}")
    else:
        print("(Skipped — existing file preserved)")

    cost_json = output_dir / "literary_echoes" / "cost_report.json"
    if cost_json.exists():
        print(f"\nCost report: {cost_json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
