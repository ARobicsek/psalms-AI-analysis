"""Build (or refresh) the Rabbi Sacks cache from Sefaria, $0 (Session 392).

The pipeline builds a psalm's entry on first use, so this script is only needed to pre-build, to
refresh after Sefaria adds material, or to survey coverage.

    python scripts/build_sacks_index.py 23 92              # those psalms (their section printed with --show)
    python scripts/build_sacks_index.py --all              # all 150 (about 25 minutes, mostly the phrase search)
    python scripts/build_sacks_index.py --all --refresh    # re-download the liturgical commentary too
    python scripts/build_sacks_index.py 23 --show          # print the bundle section the writer would get

Cache: data/sacks/liturgical.json (the aligned prayer-book commentary), works.json, psalm_NNN.json.
"""
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from src.agents.sacks_librarian import SacksLibrarian  # noqa: E402
from src.data_sources import sacks_index  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("psalms", type=int, nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--refresh", action="store_true", help="re-fetch even when cached (liturgical index too)")
    ap.add_argument("--no-search", action="store_true", help="skip the Hebrew phrase search")
    ap.add_argument("--show", action="store_true", help="print each psalm's bundle section")
    args = ap.parse_args()
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    psalms = list(range(1, 151)) if args.all else args.psalms
    if not psalms:
        ap.error("give psalm numbers or --all")

    lit = sacks_index.harvest_liturgical(refresh=args.refresh)
    print(f"Liturgical commentary: {len(lit['comments'])} comments, "
          f"{sum(1 for c in lit['comments'] if c['psalms'])} aligned to a psalm")
    lib = SacksLibrarian(search=not args.no_search)
    totals = {"with": 0, "pb": 0, "chars": 0}
    for p in psalms:
        sacks_index.harvest_psalm(p, refresh=args.refresh, search=not args.no_search)
        refs = lib.get_psalm_references(p)
        md = lib.format_for_research_bundle(refs, p)
        pb = sum(r.kind == "prayer book" for r in refs)
        totals["with"] += bool(refs)
        totals["pb"] += bool(pb)
        totals["chars"] += len(md)
        print(f"Psalm {p:3d}: {len(refs):2d} passages ({pb} prayer book, {len(refs) - pb} books), {len(md):6,} chars",
              flush=True)
        if args.show and md:
            print(md)
    print(f"\n{totals['with']} of {len(psalms)} psalms have a Sacks section ({totals['pb']} with prayer-book "
          f"commentary); {totals['chars']:,} chars in all")


if __name__ == "__main__":
    main()
