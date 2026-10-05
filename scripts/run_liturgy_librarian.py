"""Session 395: write a psalm's liturgy section on its own (the pipeline does this inside the bundle).

    python scripts/run_liturgy_librarian.py 78                    # catalogue + model -> output/psalm_78/psalm_078_liturgy_section.md
    python scripts/run_liturgy_librarian.py 78 --no-llm           # the catalogue only ($0)
    python scripts/run_liturgy_librarian.py 78 --model claude-sonnet-5-5 --out some/dir
"""

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agents.liturgy_librarian_v2 import DEFAULT_EFFORT, DEFAULT_MODEL, LiturgicalLibrarianV2  # noqa: E402
from src.utils.cost_tracker import CostTracker  # noqa: E402
from src.utils.debug_paths import psalm_output_dir  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("psalms", nargs="+", type=int)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--effort", default=DEFAULT_EFFORT)
    ap.add_argument("--no-llm", action="store_true", help="write the catalogue only ($0)")
    ap.add_argument("--out", help="directory for the section (default: the psalm's output folder)")
    args = ap.parse_args()
    for n in args.psalms:
        tracker = CostTracker()
        lib = LiturgicalLibrarianV2(cost_tracker=tracker, model=args.model, effort=args.effort,
                                    use_llm=not args.no_llm)
        t = time.time()
        units = lib.find_liturgical_usage_aggregated(n)
        md = lib.format_for_research_bundle(units, n)
        out_dir = Path(args.out) if args.out else psalm_output_dir(n, create=True)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"psalm_{n:03d}_liturgy_section.md"
        path.write_text(md, encoding="utf-8")
        cost = tracker.get_total_cost() if hasattr(tracker, "get_total_cost") else None
        print(f"Ps {n}: {len(units)} units, {sum(u.occurrence_count for u in units)} texts, "
              f"{len(md):,} chars, {len(lib.last_set_aside)} set aside, {time.time() - t:.0f}s"
              + (f", ${cost:.3f}" if cost is not None else "") + f" -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
