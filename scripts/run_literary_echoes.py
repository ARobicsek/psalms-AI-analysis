"""
Standalone runner for the Literary Echoes agent.

Generates the 4-pass literary echoes document for a single psalm, independent
of the main enhanced/SI pipelines. Default behavior is regenerate-and-overwrite;
use --skip-if-exists to preserve an existing file.

Usage:
    python scripts/run_literary_echoes.py 53
    python scripts/run_literary_echoes.py 53 --skip-if-exists
    python scripts/run_literary_echoes.py 53 --output-dir output/psalm_53
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.literary_echoes_agent import LiteraryEchoesAgent
from src.utils.cost_tracker import CostTracker
from src.utils.logger import get_logger


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Literary Echoes 4-pass workflow for one psalm")
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
            print(
                f"  {p.pass_name:>7}  {p.model:<28}  "
                f"in={p.input_tokens:>7,}  out={p.output_tokens:>7,}  "
                f"think={p.thinking_tokens:>6,}  ${p.cost:>7.4f}  ({p.elapsed_s:5.1f}s)"
            )
    else:
        print("(Skipped — existing file preserved)")

    # Emit cost JSON next to the other artifacts for machine consumption.
    cost_json = output_dir / "literary_echoes" / "cost_report.json"
    if cost_json.exists():
        print(f"\nCost report: {cost_json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
