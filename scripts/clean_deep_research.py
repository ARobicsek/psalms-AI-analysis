"""Clean a psalm's Gemini deep research against its independent check (Session 393).

Needs data/deep_research/psalm_NNN_deep_research.txt AND psalm_NNN_deep_research_check.txt.
Writes psalm_NNN_deep_research_clean.txt (what the research bundle then uses) and
psalm_NNN_deep_research_clean_log.md (every change, applied or not, and the cost).
Claude Haiku 4.5, capped at $0.10 per psalm. The pipeline runs this by itself when the check
is newer than the clean file; use this script to run it ahead of a paid run and read the log.

    python scripts/clean_deep_research.py 78              # clean (skips if the clean file is current)
    python scripts/clean_deep_research.py 78 --force      # re-clean anyway
    python scripts/clean_deep_research.py 78 --dry-run    # count input tokens and the cost cap, $0
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv  # noqa: E402

from src.agents import deep_research_cleaner as drc  # noqa: E402
from src.utils.cost_tracker import resolve_pricing  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("psalms", type=int, nargs="+")
    ap.add_argument("--force", action="store_true", help="re-clean even when the clean file is current")
    ap.add_argument("--dry-run", action="store_true", help="count tokens only ($0)")
    ap.add_argument("--model", default=drc.MODEL, help=f"default {drc.MODEL}; e.g. claude-sonnet-5-5, gpt-6-luna")
    ap.add_argument("--sweep", dest="sweep", action="store_true", default=None, help="force the second pass")
    ap.add_argument("--no-sweep", dest="sweep", action="store_false", help="single pass")
    args = ap.parse_args()
    load_dotenv()
    for n in args.psalms:
        p = drc.paths(n)
        if not (p.raw.exists() and p.check.exists()):
            print(f"Psalm {n}: needs both {p.raw.name} and {p.check.name}")
            continue
        if args.dry_run:
            user = drc.build_user_message(p.raw.read_text(encoding="utf-8"), p.check.read_text(encoding="utf-8"))
            n_in = drc._count_input(drc._make_client(args.model), args.model, drc.SYSTEM_PROMPT, user)
            budget = drc.output_budget(n_in, model=args.model)
            price = resolve_pricing(args.model)
            print(f"Psalm {n}: {n_in:,} input tokens (${n_in * price['input'] / 1e6:.4f}); "
                  f"max_tokens {budget:,} -> at most ${(n_in * price['input'] + budget * price['output']) / 1e6:.4f}; "
                  f"clean file current: {drc.clean_is_current(p)}")
            continue
        r = drc.clean(n, force=args.force, model=args.model, sweep=args.sweep)
        print(f"Psalm {n}: {r.status} {r.message}".rstrip())
        if r.status == "cleaned":
            s = r.stats
            print(f"  {r.input_tokens:,} in / {r.output_tokens:,} out = ${r.cost:.4f}; "
                  f"{s.get('applied', 0)}/{s.get('edits', 0)} edits applied "
                  f"({s.get('not_found', 0)} not found, {s.get('ambiguous', 0)} ambiguous)")
            print(f"  -> {p.clean}\n  -> {p.log}")


if __name__ == "__main__":
    main()
