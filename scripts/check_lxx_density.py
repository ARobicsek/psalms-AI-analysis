"""Score a guide against RULE 8b's Septuagint budget: the Greek in at most 2 verses in 5.

WHY
    The LXX is supplied for every verse of every psalm, so — exactly like the commentator
    dossier before RULE 8b — it is always available and always usable. Measured over the
    finished guides at the close of Session 374, before the budget existed:

        median 44% of verses carry the Greek;  23 of 42 psalms exceed 2/5;
        worst offenders 100% (Pss 55, 134), 89% (61), 86% (53), 83% (1).

    The author's judgement was that the instances are individually good and collectively
    too many, which is why this is a proportion check and not a quality one. Nothing here
    inspects whether a given citation earns its place — only how often the Greek appears.

STRUCTURAL COUNTS ONLY
    Per Session 370's canary lesson, this matches on the presence of a citation, never on
    wording. A verse counts once whether it names the Greek once or four times, so the
    number answers exactly one question: in what fraction of verses does the Septuagint
    turn up at all?

Usage:
    python scripts/check_lxx_density.py 1
    python scripts/check_lxx_density.py --all
"""

import argparse
import re
import statistics
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BUDGET = 0.40  # RULE 8b: at most 2 verses in 5

# Presence of a Septuagint citation, in any of the forms the guides use.
LXX_MARK = re.compile(r"Septuagint|\bLXX\b|Greek translator|\bthe Greek\b", re.I)
VERSE_SPLIT = re.compile(r"^\*\*Verse\s+(\d+[a-z]?)\*\*\s*$", re.M)


def guide_path(psalm: int):
    for stem in (f"output/psalm_{psalm}", f"output/psalm_{psalm:03d}"):
        base = PROJECT_ROOT / stem
        if not base.exists():
            continue
        for suffix in ("_copy_edited.md", "_edited_verses.md", "_print_ready.md"):
            p = base / f"psalm_{psalm:03d}{suffix}"
            if p.exists():
                return p
    return None


def score(psalm: int):
    path = guide_path(psalm)
    if not path:
        return None
    parts = VERSE_SPLIT.split(path.read_text(encoding="utf-8"))
    if len(parts) < 3:
        return None
    verses = {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}
    hits = [v for v, body in verses.items() if LXX_MARK.search(body)]
    return len(verses), hits


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("psalms", type=int, nargs="*")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    targets = args.psalms
    if args.all:
        seen = set()
        for p in sorted((PROJECT_ROOT / "output").glob("psalm_*")):
            m = re.search(r"psalm_(\d+)$", p.name)
            if m:
                seen.add(int(m.group(1)))
        targets = sorted(seen)
    if not targets:
        ap.error("give psalm numbers or --all")

    rows = []
    for n in targets:
        r = score(n)
        if r:
            rows.append((n, r[0], r[1]))

    print(f"{'psalm':>6} {'verses':>7} {'LXX':>4} {'frac':>6}  budget")
    for n, total, hits in sorted(rows, key=lambda r: -len(r[2]) / r[1]):
        frac = len(hits) / total
        allowed = int(total * BUDGET)
        verdict = "OK" if frac <= BUDGET else f"OVER by {len(hits) - allowed} verse(s)"
        print(f"{n:>6} {total:>7} {len(hits):>4} {frac:>5.0%}  {verdict}")
        if len(targets) == 1 and frac > BUDGET:
            print(f"         verses carrying the Greek: {', '.join(hits)}")
            print(f"         budget at {BUDGET:.0%} of {total} verses = {allowed}")

    if len(rows) > 1:
        fr = [len(h) / t for _, t, h in rows]
        print()
        print(f"psalms: {len(rows)}   median {statistics.median(fr):.0%}   "
              f"over budget: {sum(1 for f in fr if f > BUDGET)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
