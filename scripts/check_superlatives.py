"""
UNGROUNDED SUPERLATIVE audit — ranking and uniqueness claims the guide cannot support.

Session 380, from the author on the Psalm 73 guide: "I'm seeing multiple examples
of an 'LLM verbal tic' — describing something as 'the most' something. Calderon's
quote is 'the most famous soliloquy in Spanish'. (really?)"

The patterns live in `src/utils/superlatives.py` and are shared with the copy
editor, which is given the rule as error category 9(h). This script is the
backstop, same role as `check_banned_phrases.py`.

TWO TIERS, AND THE DIFFERENCE MATTERS
-------------------------------------
DEFAULT (reception claims) — appeals to fame, canonicity or scholarly consensus:
"the most famous soliloquy in Spanish," "the most argued clause in the psalm."
A guide that cites its sources for everything else cannot source these, so they
are wrong essentially every time. Exit status is 1 when any are found, so this
can gate a run.

--all (review mode) — the broader ranking/uniqueness family. These are NOT
errors and the exit status ignores them. Hand-classifying all 20 hits in Psalm 73
put only about 30% in the tic bucket; eight were verifiable concordance findings
("דּוֹר בָּנֶיךָ occurs nowhere else in the Bible," "the poem's single
Tetragrammaton") that are among the best lines in the guide, and six were not
superlatives at all ("the Most High" renders עֶלְיוֹן). Use this to skim, never
to gate.

The script REPORTS; it never rewrites.

Usage:
    python scripts/check_superlatives.py 73
    python scripts/check_superlatives.py 71 72 73
    python scripts/check_superlatives.py 73 --all
    python scripts/check_superlatives.py --delivered
    python scripts/check_superlatives.py path/to/guide.docx
"""

import argparse
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.superlatives import (  # noqa: E402
    RECEPTION_PATTERNS,
    find_candidates,
    find_reception_claims,
)

DELIVERED_DIR = ROOT / "Documents" / "Psalm study guide"


def docx_text(path: Path) -> str:
    """Paragraph text from a .docx, one paragraph per line.

    Line numbers reported against a DOCX are therefore paragraph numbers, which is
    what a human scanning the document can actually find.
    """
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<[^>]+>", "", xml)
    return xml


def resolve_psalm(number: int) -> Path:
    """The finished markdown for a psalm, preferring the copy-edited text."""
    psalm_dir = ROOT / "output" / f"psalm_{number}"
    copy_edited = psalm_dir / f"psalm_{number:03d}_copy_edited.md"
    print_ready = psalm_dir / f"psalm_{number:03d}_print_ready.md"
    if copy_edited.exists():
        return copy_edited
    if print_ready.exists():
        return print_ready
    raise FileNotFoundError(
        f"No finished markdown for psalm {number} — looked for {copy_edited.name} "
        f"and {print_ready.name} in {psalm_dir}"
    )


def read(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        return docx_text(path)
    return path.read_text(encoding="utf-8")


def _excerpt(hit, width: int = 160) -> str:
    """Centre on hit.col, not on a re-search for the matched text: a paragraph
    holding two hits would otherwise print the same excerpt for both."""
    text = hit.context
    if len(text) <= width:
        return text
    start = max(0, hit.col - width // 2)
    end = start + width
    return ("..." if start else "") + text[start:end] + ("..." if end < len(text) else "")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("targets", nargs="*",
                    help="psalm numbers and/or paths to .md or .docx files")
    ap.add_argument("--delivered", action="store_true",
                    help=f"scan every .docx in {DELIVERED_DIR.relative_to(ROOT)}")
    ap.add_argument("--all", action="store_true", dest="review",
                    help="ALSO list the broad ranking/uniqueness family for human "
                         "review. These are not errors and do not affect exit status.")
    ap.add_argument("--quiet", action="store_true", help="print only files with hits")
    args = ap.parse_args()

    paths: list[Path] = []
    for t in args.targets:
        if t.isdigit():
            paths.append(resolve_psalm(int(t)))
        else:
            p = Path(t)
            if not p.is_absolute():
                p = ROOT / p
            if not p.exists():
                print(f"ERROR: no such file: {t}", file=sys.stderr)
                return 2
            paths.append(p)
    if args.delivered:
        paths.extend(sorted(DELIVERED_DIR.glob("*.docx")))

    if not paths:
        ap.error("nothing to scan — give psalm numbers, paths, or --delivered")

    labels = ", ".join(p.label for p in RECEPTION_PATTERNS)
    print(f"Reception-claim patterns: {labels}")
    print(f"Scanning {len(paths)} file(s)\n")

    total = 0
    files_with_hits = 0
    review_total = 0
    for path in paths:
        try:
            text = read(path)
        except (zipfile.BadZipFile, KeyError, UnicodeDecodeError) as e:
            print(f"SKIP  {path.name}: unreadable ({type(e).__name__}: {e})")
            continue

        hits = find_reception_claims(text)
        unit = "paragraph" if path.suffix.lower() == ".docx" else "line"

        if hits:
            files_with_hits += 1
            total += len(hits)
            print(f"HIT   {path.name} — {len(hits)} reception claim(s)")
            for hit in hits:
                print(f'        {unit} {hit.line_no}: [{hit.label}] {_excerpt(hit)}')
        elif not args.quiet:
            print(f"ok    {path.name}")

        if args.review:
            # Reception hits are a subset of the candidate sweep; drop them so the
            # review list is only what the gate did NOT already report.
            reported = {(h.line_no, h.col) for h in hits}
            candidates = [c for c in find_candidates(text)
                          if (c.line_no, c.col) not in reported]
            review_total += len(candidates)
            if candidates:
                print(f"      review — {len(candidates)} candidate(s), NOT errors:")
                for c in candidates:
                    print(f'        {unit} {c.line_no}: [{c.label}] {_excerpt(c, 120)}')
        if hits or (args.review and args.targets):
            print()

    print(f"{'-' * 60}")
    print(f"{total} reception claim(s) in {files_with_hits} of {len(paths)} file(s)")
    if args.review:
        print(f"{review_total} review candidate(s) — most are legitimate; "
              f"they do not affect exit status")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
