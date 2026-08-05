"""
BANNED PHRASE audit — does the finished guide contain house-style vocabulary the
author has ruled out?

Session 374. The list lives in `src/utils/banned_phrases.py` and is shared with
the copy editor, which is given it as error category 11. This script is the
backstop: the copy editor is a model and will sometimes miss one, and a tic that
ships silently is exactly what the author does not want to meet in the DOCX.

The script REPORTS; it never rewrites. The repair differs at every site, and some
occurrences are legitimate metaphor rather than tic — see the module docstring of
`src/utils/banned_phrases.py` for the measurement behind that decision.

Sources it can read:
  - a psalm number, resolved to that psalm's finished markdown in `output/`
    (`_copy_edited.md`, falling back to `_print_ready.md` when the copy editor
    has not run yet)
  - any explicit .md path
  - any .docx path, and `--delivered` for every guide in the Documents folder,
    because the delivered guides are what the author actually reads and `output/`
    is not always populated in a given checkout

Exit status is 1 when anything is found, so this can gate a run.

Usage:
    python scripts/check_banned_phrases.py 71
    python scripts/check_banned_phrases.py 71 72 73
    python scripts/check_banned_phrases.py --delivered
    python scripts/check_banned_phrases.py path/to/guide.docx path/to/other.md
"""

import argparse
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.banned_phrases import BANNED_PHRASES, find_banned  # noqa: E402

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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="*",
                    help="psalm numbers and/or paths to .md or .docx files")
    ap.add_argument("--delivered", action="store_true",
                    help=f"scan every .docx in {DELIVERED_DIR.relative_to(ROOT)}")
    ap.add_argument("--quiet", action="store_true",
                    help="print only files with hits")
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

    banned_names = ", ".join(f'"{b.label}"' for b in BANNED_PHRASES)
    print(f"Banned phrases: {banned_names}")
    print(f"Scanning {len(paths)} file(s)\n")

    total = 0
    files_with_hits = 0
    for path in paths:
        try:
            text = read(path)
        except (zipfile.BadZipFile, KeyError, UnicodeDecodeError) as e:
            print(f"SKIP  {path.name}: unreadable ({type(e).__name__}: {e})")
            continue
        hits = find_banned(text)
        if not hits:
            if not args.quiet:
                print(f"ok    {path.name}")
            continue
        files_with_hits += 1
        total += len(hits)
        unit = "paragraph" if path.suffix.lower() == ".docx" else "line"
        print(f"HIT   {path.name} — {len(hits)} occurrence(s)")
        for hit in hits:
            excerpt = hit.context
            if len(excerpt) > 160:
                # Centre on hit.col, not on a re-search for the matched text: a
                # paragraph holding the phrase twice would otherwise print the
                # same excerpt for both hits.
                start = max(0, hit.col - 70)
                end = start + 160
                excerpt = (
                    ("..." if start else "")
                    + excerpt[start:end]
                    + ("..." if end < len(hit.context) else "")
                )
            print(f'        {unit} {hit.line_no}: [{hit.label}] {excerpt}')
        print()

    print(f"{'-' * 60}")
    print(f"{total} occurrence(s) in {files_with_hits} of {len(paths)} file(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
