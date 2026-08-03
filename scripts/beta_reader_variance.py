"""
Beta-reader TEST-RETEST variance — how much of an arm's score difference is signal?

Every affect conclusion in Sessions 371-372 rests on single beta-read samples: one
arm scores `Wit: 6`, another `Wit: 3`, and the difference gets a causal story. That
inference is only valid if the judge returns a stable score for a FIXED text. Nobody
had ever measured that.

This script re-reads the SAME guide N times and reports the spread. It answers one
question: is the between-arm difference larger than the within-text noise?

Read it as a measuring-instrument calibration, not as an experiment about the guides.
If the same text scores {3, 5, 6, 4} across four reads, then a 3-vs-6 gap between two
arms is not evidence of anything, and the counters (INERT CITATIONS, UNEXPLAINED
GRAMMAR, POET'S FEELING) are the only affect-adjacent readout worth trusting.

Reports are written to a scratch directory, NEVER over the arm's real beta read.

Usage:
    python scripts/beta_reader_variance.py 71 --arms base A_no_scaffolding --repeats 4
    python scripts/beta_reader_variance.py 71 --arms E_translation --repeats 3 --out /tmp/var
"""

import argparse
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

from src.agents.beta_reader import BetaReader  # noqa: E402
from src.utils.cost_tracker import CostTracker  # noqa: E402


def main() -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    load_dotenv()

    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("psalm", type=int)
    ap.add_argument("--ab-dir", default="_prompt_ab")
    ap.add_argument("--arms", nargs="+", required=True)
    ap.add_argument("--repeats", type=int, default=4)
    ap.add_argument("--out", default=None,
                    help="Scratch dir for the repeat reports (default: <ab-dir>/_variance)")
    args = ap.parse_args()

    ab_dir = ROOT / "output" / f"psalm_{args.psalm}" / args.ab_dir
    out_root = Path(args.out) if args.out else ab_dir / "_variance"

    tracker = CostTracker()
    reader = BetaReader(cost_tracker=tracker)

    results = {}
    for arm in args.arms:
        src = ab_dir / arm / f"psalm_{args.psalm:03d}_full.md"
        if not src.exists():
            print(f"SKIP {arm}: {src} not found")
            continue
        print(f"\n=== {arm} — {args.repeats} independent reads of one fixed text ===")
        rows = []
        for i in range(args.repeats):
            d = out_root / arm / f"run{i + 1}"
            r = reader.read_commentary(
                psalm_number=args.psalm, input_file=src, output_dir=d
            )
            scores = r["scores"] or {}
            counters = _counters(Path(r["report_file"]).read_text(encoding="utf-8"))
            rows.append({**scores, **counters})
            print(f"  run {i + 1}: " + ", ".join(f"{k}={v}" for k, v in rows[-1].items()))
        results[arm] = rows

    print("\n" + "=" * 78)
    print("WITHIN-TEXT SPREAD (same text, repeated reads)")
    print("=" * 78)
    print(f"{'arm':<22} {'metric':<22} {'values':<20} {'range':>6} {'stdev':>7}")
    for arm, rows in results.items():
        keys = [k for k in rows[0] if all(k in r for r in rows)]
        for k in keys:
            vals = [r[k] for r in rows]
            rng = max(vals) - min(vals)
            sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
            print(f"{arm:<22} {k:<22} {str(vals):<20} {rng:>6} {sd:>7.2f}")

    print(f"\nCost: ${tracker.get_total_cost():.4f}")
    print(f"Reports: {out_root}")
    print("\nHOW TO READ THIS: a between-arm difference is only interpretable if it")
    print("exceeds the range above. Where it does not, the arms are indistinguishable")
    print("on that metric and no causal story should be attached to the gap.")
    return 0


def _counters(text: str) -> dict:
    import re
    out = {}
    for key, pat in (("INERT", r"INERT CITATIONS:\s*(\d+)"),
                     ("UNEXPL_GRAM", r"UNEXPLAINED GRAMMAR:\s*(\d+)"),
                     ("POETS_FEELING", r"POET'S FEELING:\s*(\d+)")):
        m = re.search(pat, text)
        if m:
            out[key] = int(m.group(1))
    return out


if __name__ == "__main__":
    sys.exit(main())
