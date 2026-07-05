"""
Standalone Beta Reader Runner

Run the beta-reader agent (Session 360) against one or more finished psalm
guides. The beta reader simulates the target audience reading the final guide
start to finish and reports the reader EXPERIENCE — engagement curve, moments
that landed (aha / wit / felt), the affective landing, sag points, confusion,
and 5 scored dimensions. It is measurement-only: no edits are proposed and
nothing downstream consumes the report automatically.

Usage:
    python scripts/run_beta_reader.py 60
    python scripts/run_beta_reader.py 58 59 60
    python scripts/run_beta_reader.py 60 --input-file output/psalm_60/psalm_060_print_ready.md
    python scripts/run_beta_reader.py 60 --model claude-sonnet-4-6

Output (per psalm):
    output/psalm_NNN/psalm_NNN_beta_read.md

Cost: ~$0.08/psalm (one Sonnet call over the finished guide).
"""

import argparse
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.beta_reader import BetaReader
from src.utils.cost_tracker import CostTracker
from src.utils.logger import get_logger


def main():
    parser = argparse.ArgumentParser(
        description="Run the beta reader on finished psalm guides",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_beta_reader.py 60
  python scripts/run_beta_reader.py 58 59 60
""",
    )
    parser.add_argument(
        "psalms", type=int, nargs="+",
        help="Psalm number(s) to beta-read (e.g., 60 or 58 59 60)",
    )
    parser.add_argument(
        "--input-file", type=Path, default=None,
        help="Override the default input file (only valid with a single psalm)",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="Override the default output directory",
    )
    parser.add_argument(
        "--model", type=str, default=None,
        help=f"Override the model (default: {BetaReader.DEFAULT_MODEL})",
    )
    args = parser.parse_args()
    logger = get_logger("run_beta_reader")

    if args.input_file and len(args.psalms) > 1:
        parser.error("--input-file only makes sense with a single psalm")

    for n in args.psalms:
        if not 1 <= n <= 150:
            parser.error(f"Invalid psalm number: {n}")

    cost_tracker = CostTracker()
    reader = BetaReader(model=args.model, cost_tracker=cost_tracker, logger=logger)

    failures = []
    for n in args.psalms:
        try:
            result = reader.read_commentary(
                psalm_number=n,
                input_file=args.input_file,
                output_dir=args.output_dir,
            )
            scores = result["scores"]
            if scores:
                logger.info(
                    f"Psalm {n} scores: "
                    + ", ".join(f"{k} {v}/10" for k, v in scores.items())
                )
        except FileNotFoundError as e:
            logger.error(str(e))
            failures.append(n)
        except Exception as e:
            logger.error(f"Beta read failed for Psalm {n}: {e}")
            failures.append(n)

    print(cost_tracker.get_summary())

    if failures:
        logger.error(f"Failed psalms: {failures}")
        sys.exit(1)


if __name__ == "__main__":
    main()
