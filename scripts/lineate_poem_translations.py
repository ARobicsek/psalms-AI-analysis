"""Restore the line breaks of a quoted poem's English translation, from the dossier.

WHY THIS EXISTS
    The literary-echoes dossier lineates every translation it supplies, using ' / '
    as the line-break mark:

        > אױפֿן װעג שטײט אַ בױם,
        > ...
        > "[On the road stands a tree, / it stands bent over, / ...]"

    The writer keeps that mark about half the time. The other half it flattens the
    translation into a single line of prose, and the reader gets a paragraph where the
    poem had four lines. The DOCX generator renders ' / ' inside a quoted poem as a real
    line break (see _add_quote_text), so restoring the mark is all that is needed.

    RULE 12 now specifies the lineated form, so new psalms should not need this. This is
    a backfill for guides already written, and it is deterministic: the line breaks come
    from the dossier, never from a model.

HOW THE MAPPING WORKS
    The writer paraphrases the dossier's translation rather than copying it (Psalm 1's
    Borges: dossier "granted me at once", guide "gave me at once"), so the break
    positions cannot be transplanted by string offset. The two token streams are aligned
    with difflib; inside an EQUAL run the offset carries over exactly, and inside a
    rewritten run the break is placed at the START of the rewrite rather than after it —
    which is what puts the Borges break before "gave" instead of after it.

SAFETY
    Every insertion is round-tripped: stripping the inserted ' / ' marks must reproduce
    the guide's text character for character, so this can reflow a translation but can
    never alter a word of it. A block that fails the round-trip, or whose dossier match
    is weak, is skipped and reported.

Usage:
    python scripts/lineate_poem_translations.py 1
    python scripts/lineate_poem_translations.py --all --dry-run
"""

import argparse
import difflib
import re
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ECHOES_DIR = PROJECT_ROOT / "data" / "literary_echoes"

# Every markdown the DOCX generator may read, kept in step so a rerender and an audit
# see the same text. run_docx_only prefers the split edited_* pair and falls back to
# copy_edited, so patching only one of them would silently do nothing.
GUIDE_FILES = ("_edited_intro.md", "_edited_verses.md", "_copy_edited.md", "_print_ready.md")

MIN_RATIO = 0.55  # token-similarity floor for accepting a dossier translation as the match


def toks(s: str):
    return re.findall(r"\w+|[^\w\s]", s)


def load_dossier_translations(psalm: int):
    """Return [(original_first_line, lineated_translation), ...] from the echoes dossier."""
    path = ECHOES_DIR / f"psalm_{psalm:03d}_literary_echoes.txt"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r'^>\s*"?\[?([^\n]*?/[^\n]*?)\]?"?\s*$', text, flags=re.M):
        body = m.group(1).strip()
        if " / " not in body:
            continue
        prev = text[: m.start()].rstrip().split("\n")[-1].lstrip("> ").strip()
        out.append((prev, body))
    return out


def map_cuts(dossier_line: str, flat: str):
    """Map the dossier's break positions onto the guide's paraphrase of it."""
    parts = dossier_line.split(" / ")
    cuts, run = [], 0
    for p in parts[:-1]:
        run += len(toks(p))
        cuts.append(run)
    a, b = toks(dossier_line.replace(" / ", " ")), toks(flat)
    ops = difflib.SequenceMatcher(a=a, b=b).get_opcodes()
    mapped = []
    for c in cuts:
        for tag, i1, i2, j1, j2 in ops:
            if i1 <= c < i2 or (c == i2 and tag == "equal"):
                mapped.append(j1 + (c - i1) if tag == "equal" else j1)
                break
    # A line of verse breaks AT its punctuation. If the mapped break leaves a one- or
    # two-word fragment dangling after a dash or comma, the writer's rephrasing moved
    # the mark, not the line: pull the break back to just past that punctuation.
    fixed = []
    for pos in mapped:
        for back in (2, 3):
            k = pos - back
            if 0 <= k < len(b) and b[k] in (",", ";", "—", ":"):
                pos = k + 1
                break
        fixed.append(pos)
    return sorted(set(p for p in fixed if 0 < p < len(b)))


def insert_breaks(flat: str, cuts):
    """Rebuild `flat` with ' / ' at the given token indices, preserving all whitespace."""
    b = toks(flat)
    out, pos = [], 0
    for ti, tok in enumerate(b):
        j = flat.index(tok, pos)
        if ti in cuts:
            out.append(" / ")
        out.append(flat[pos:j])
        out.append(tok)
        pos = j + len(tok)
    out.append(flat[pos:])
    return re.sub(r"\s*/\s*", " / ", "".join(out))


def find_poem_blocks(text: str):
    """Yield (original_lines, flat_translation, span) for poems whose translation is unlineated.

    Handles both shapes the writer produces: the translation as a quoted line inside the
    block quote, and the translation opening the prose paragraph after it (which the DOCX
    generator lifts into the block at render time).
    """
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        if not lines[i].strip().startswith(">"):
            i += 1
            continue
        start, quoted = i, []
        while i < len(lines) and (
            lines[i].strip().startswith(">")
            or (not lines[i].strip() and i + 1 < len(lines) and lines[i + 1].strip().startswith(">"))
        ):
            if lines[i].strip().startswith(">"):
                quoted.append((i, lines[i].strip()[1:].strip()))
            i += 1

        body = [(n, t) for n, t in quoted if t]
        if len(body) < 2:
            continue
        originals = [t for _, t in body if not t.startswith(('"', "“"))]
        if not originals:
            continue

        # (a) translation already inside the block, but on one line
        for n, t in body:
            if t.startswith(('"', "“")) and " / " not in t and len(t) > 60:
                yield originals, t, ("line", n)
                break
        else:
            # (b) translation left in the prose paragraph that follows
            k = i
            while k < len(lines) and not lines[k].strip():
                k += 1
            if k < len(lines):
                m = re.match(r'^["“]([^"“”]{60,})["”]', lines[k].strip())
                if m and " / " not in m.group(1):
                    yield originals, m.group(1), ("prose", k)


def lineate_text(text: str, dossier, report):
    """Return `text` with every matchable poem translation lineated."""
    edits = []
    for originals, flat, (kind, lineno) in find_poem_blocks(text):
        if not dossier:
            continue
        scored = [
            (difflib.SequenceMatcher(a=toks(d.replace(" / ", " ")), b=toks(flat)).ratio(), o, d)
            for o, d in dossier
        ]
        ratio, orig_key, best = max(scored, key=lambda r: r[0])
        tag = f"{flat[:46]}..."
        if ratio < MIN_RATIO:
            report.append(f"    SKIP (no dossier match, best ratio {ratio:.2f}): {tag}")
            continue
        cuts = map_cuts(best, flat)
        if not cuts:
            report.append(f"    SKIP (no usable break positions): {tag}")
            continue
        rebuilt = insert_breaks(flat, cuts)
        if re.sub(r"\s+", " ", re.sub(r"\s+/\s+", " ", rebuilt)) != re.sub(r"\s+", " ", flat):
            report.append(f"    SKIP (round-trip failed — text would change): {tag}")
            continue
        n_orig = len(originals)
        report.append(
            f"    {len(cuts) + 1} lines (original has {n_orig}, dossier match {ratio:.2f}): {tag}"
        )
        edits.append((flat, rebuilt))

    for flat, rebuilt in edits:
        text = text.replace(flat, rebuilt, 1)
    return text, len(edits)


def process(psalm: int, dry_run: bool, report):
    base = PROJECT_ROOT / "output" / f"psalm_{psalm}"
    if not base.exists():
        base = PROJECT_ROOT / "output" / f"psalm_{psalm:03d}"
    if not base.exists():
        report.append(f"  psalm {psalm}: no output directory")
        return 0

    dossier = load_dossier_translations(psalm)
    if not dossier:
        report.append(f"  psalm {psalm}: no lineated translations in the echoes dossier")
        return 0

    total = 0
    for suffix in GUIDE_FILES:
        path = base / f"psalm_{psalm:03d}{suffix}"
        if not path.exists():
            continue
        original = path.read_text(encoding="utf-8")
        file_report = []
        new, n = lineate_text(original, dossier, file_report)
        if n:
            report.append(f"  {path.name}: {n} translation(s) lineated")
            report.extend(file_report)
            total += n
            if not dry_run:
                backup = path.with_suffix(path.suffix + ".pre_lineation")
                if not backup.exists():
                    shutil.copy2(path, backup)
                path.write_text(new, encoding="utf-8")
        elif file_report:
            report.append(f"  {path.name}:")
            report.extend(file_report)
    return total


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("psalms", type=int, nargs="*", help="psalm number(s)")
    ap.add_argument("--all", action="store_true", help="every psalm with an echoes dossier")
    ap.add_argument("--dry-run", action="store_true", help="report without writing")
    args = ap.parse_args()

    targets = args.psalms
    if args.all:
        targets = sorted(
            int(p.stem.split("_")[1]) for p in ECHOES_DIR.glob("psalm_*_literary_echoes.txt")
        )
    if not targets:
        ap.error("give psalm numbers or --all")

    report, grand = [], 0
    for n in targets:
        r = []
        grand += process(n, args.dry_run, r)
        if r:
            report.append(f"Psalm {n}")
            report.extend(r)
    print("\n".join(report) if report else "nothing to do")
    print(f"\n{'would lineate' if args.dry_run else 'lineated'}: {grand} translation(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
