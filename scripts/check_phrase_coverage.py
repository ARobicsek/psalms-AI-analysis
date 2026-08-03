"""
PHRASE COVERAGE audit — is every word of every verse visible in that verse's commentary?

The author's standing requirement (Session 370): "I DO want the verse by verse
commentary to treat each word/phrase at least briefly." Any change that buys concision
by dropping coverage is the wrong change — so every length-reducing prompt experiment
needs this check before it can be called a win.

Method. Ground truth is `tanakh.db`, not the guide's own printed verse line, so that a
verse the writer printed incompletely still counts every word against it. Hebrew is
compared on the CONSONANTAL SKELETON: cantillation, vowel points, and maqqef are
stripped, so a word quoted in a different vocalisation still counts as covered. The
printed verse line that opens each block is excluded — otherwise every word would
match itself trivially.

A word counts as covered if its skeleton appears anywhere in that verse's commentary
body, including inside a longer quoted phrase.

Known limitation: this measures VISIBILITY, not quality of treatment. A word inside a
block quotation the guide never unpacks scores as covered. It answers "did anything
get silently dropped", which is the question a shortening experiment raises.

Usage:
    python scripts/check_phrase_coverage.py 71 --ab-dir _prompt_ab
    python scripts/check_phrase_coverage.py 71 --ab-dir _prompt_ab --arm B_positive_examples --detail
"""

import argparse
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Hebrew points and accents: cantillation U+0591-U+05AF, vowels U+05B0-U+05BD,
# U+05BF-U+05C2, U+05C4-U+05C7. U+05BE is maqqef (a separator, handled below).
_MARKS = re.compile(r"[֑-ְ֯-ֽֿ-ׂׄ-ׇ]")
_HEBREW_TOKEN = re.compile(r"[א-ת]+")

# Words too short or too common to be meaningful evidence of coverage.
_STOP = {"את", "אל", "על", "כי", "לא", "מן", "עם", "כל", "אשר", "הוא", "אני", "ו", "ה", "ב", "ל", "כ", "מ", "ש"}


def skeleton(text: str) -> str:
    """Consonants only, maqqef and sof-pasuq turned into separators.

    Markdown emphasis is deleted FIRST and without leaving a gap. RULE 3b-2's primary
    technique bolds a prefix inside a word (`**בְּ**צִדְקָתְךָ`), which splits the
    consonantal run and would make the word look uncovered — penalising precisely the
    behaviour the rule asks for, and hardest on whichever arm bolds most.
    """
    t = unicodedata.normalize("NFC", text)
    t = t.replace("*", "").replace("_", "")
    t = t.replace("־", " ").replace("׃", " ").replace("׀", " ")
    return _MARKS.sub("", t)


def verse_words(hebrew: str) -> list:
    return [w for w in _HEBREW_TOKEN.findall(skeleton(hebrew)) if len(w) > 1]


# Inseparable prefixes. In Hebrew these are separate words written joined, so a guide
# that discusses בְכִנּוֹר by quoting the bare noun כִּנּוֹר has covered it. Requiring the
# prefixed form counts real treatment as a miss (observed on Ps 71 v.22, where the
# instruments are discussed at length under their absolute forms).
_PREFIXES = "והבכלמש"


def _is_covered(word: str, block_skeleton: str) -> bool:
    if word in block_skeleton:
        return True
    stem = word
    for _ in range(2):  # up to two stacked prefixes, e.g. וְלַ-
        if len(stem) > 3 and stem[0] in _PREFIXES:
            stem = stem[1:]
            if stem in block_skeleton:
                return True
        else:
            break
    return False


def load_psalm(psalm: int, db_path: Path) -> dict:
    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT verse, hebrew FROM verses WHERE book_name=? AND chapter=? ORDER BY verse",
        ("Psalms", psalm),
    ).fetchall()
    con.close()
    return {int(v): h for v, h in rows}


def split_verse_blocks(text: str) -> dict:
    """Map each verse number to its commentary body.

    Headers may group verses ('**Verses 10-11**'); a grouped block is credited to
    every verse it names, which is correct — grouping is explicitly permitted.
    """
    marker = "## Verse-by-Verse Commentary"
    i = text.find(marker)
    body = text[i + len(marker):] if i >= 0 else text

    hits = list(re.finditer(r"\*\*Verses?\s+(\d+)(?:\s*[-–—]\s*(\d+))?\*\*", body))
    blocks = {}
    for n, m in enumerate(hits):
        end = hits[n + 1].start() if n + 1 < len(hits) else len(body)
        chunk = body[m.end(): end]
        # Drop the printed Hebrew verse line(s) that open the block, else every
        # word trivially matches itself.
        lines = [ln for ln in chunk.splitlines()]
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and len(_HEBREW_TOKEN.findall(skeleton(lines[0]))) >= 3 \
                and len(re.findall(r"[A-Za-z]", lines[0])) < 10:
            lines.pop(0)
            while lines and not lines[0].strip():
                lines.pop(0)
        chunk_body = "\n".join(lines)

        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) else lo
        for v in range(lo, hi + 1):
            blocks.setdefault(v, "")
            blocks[v] += "\n" + chunk_body
    return blocks


def _is_hebrew_line(line: str) -> bool:
    """A printed verse line: several Hebrew tokens and almost no Latin."""
    return (len(_HEBREW_TOKEN.findall(skeleton(line))) >= 3
            and len(re.findall(r"[A-Za-z]", line)) < 10)


def leading_blockquotes(chunk: str) -> list:
    """Block-quote lines in the block's OPENING region, before any real prose.

    Session 372's arm E prints the verse's English translation as a `> ` line under
    the Hebrew. Block quotes also carry literary echoes deep inside a section, so
    only the leading region counts — we stop at the first line that is neither
    blank, nor a printed Hebrew line, nor a block quote.
    """
    quotes = []
    for raw in chunk.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(">"):
            quotes.append(line.lstrip("> ").strip())
            continue
        if _is_hebrew_line(line):
            continue
        break
    return quotes


def translation_audit(text: str, psalm_text: dict) -> dict:
    """Per verse: does a full-verse English translation sit at the top of its block?

    This is the guarantee arm E buys. A translation counts when it carries no Hebrew
    and is not conspicuously short against the verse it renders (English on Hebrew
    normally runs LONGER, so 0.7x the Hebrew token count is a generous floor that
    still catches a summary or an ellipsis).
    """
    marker = "## Verse-by-Verse Commentary"
    i = text.find(marker)
    body = text[i + len(marker):] if i >= 0 else text
    hits = list(re.finditer(r"\*\*Verses?\s+(\d+)(?:\s*[-–—]\s*(\d+))?\*\*", body))

    ok, short, absent = [], [], []
    for n, m in enumerate(hits):
        end = hits[n + 1].start() if n + 1 < len(hits) else len(body)
        chunk = body[m.end(): end]
        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) else lo
        verses = list(range(lo, hi + 1))

        quotes = leading_blockquotes(chunk)
        # A grouped block must carry one translation per verse it names.
        for k, v in enumerate(verses):
            heb_n = len(verse_words(psalm_text.get(v, "")))
            if k >= len(quotes):
                absent.append(v)
                continue
            q = quotes[k]
            if _HEBREW_TOKEN.search(skeleton(q)):
                short.append(v)          # Hebrew leaked into the translation slot
            elif heb_n and len(q.split()) < 0.7 * heb_n:
                short.append(v)
            else:
                ok.append(v)
    return {"ok": sorted(ok), "short": sorted(short), "absent": sorted(absent),
            "n": len(psalm_text)}


def audit(text: str, psalm_text: dict) -> dict:
    blocks = split_verse_blocks(text)
    total = covered = 0
    missing = {}
    for v, heb in psalm_text.items():
        words = [w for w in verse_words(heb) if w not in _STOP]
        if not words:
            continue
        block = blocks.get(v)
        if block is None:
            missing[v] = ["(NO COMMENTARY BLOCK)"] + words
            total += len(words)
            continue
        skel = skeleton(block)
        miss = [w for w in words if not _is_covered(w, skel)]
        total += len(words)
        covered += len(words) - len(miss)
        if miss:
            missing[v] = miss
    return {
        "verses": len(psalm_text),
        "blocks": len(blocks),
        "words": total,
        "covered": covered,
        "pct": round(100.0 * covered / total, 1) if total else 0.0,
        "missing": missing,
    }


def main() -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("psalm", type=int)
    ap.add_argument("--ab-dir", default="_prompt_ab")
    ap.add_argument("--arm", default=None, help="Audit one arm only")
    ap.add_argument("--detail", action="store_true", help="List the uncovered words")
    ap.add_argument("--db-path", default="database/tanakh.db")
    args = ap.parse_args()

    psalm_text = load_psalm(args.psalm, ROOT / args.db_path)
    if not psalm_text:
        print(f"ERROR: no verses for Psalm {args.psalm} in {args.db_path}", file=sys.stderr)
        return 1

    ab_dir = ROOT / "output" / f"psalm_{args.psalm}" / args.ab_dir
    dirs = sorted(d for d in ab_dir.iterdir() if d.is_dir())
    if args.arm:
        dirs = [d for d in dirs if d.name == args.arm]

    print(f"PHRASE COVERAGE — Psalm {args.psalm} "
          f"({len(psalm_text)} verses, ground truth = tanakh.db)\n")
    print(f"{'arm':<24} {'blocks':>6} {'words':>6} {'covered':>8} {'pct':>7}  {'xlat':>7}  uncovered")
    results, xlats = {}, {}
    for d in dirs:
        f = d / f"psalm_{args.psalm:03d}_full.md"
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        r = audit(text, psalm_text)
        x = translation_audit(text, psalm_text)
        results[d.name], xlats[d.name] = r, x
        nmiss = sum(len(v) for v in r["missing"].values())
        xcol = f"{len(x['ok'])}/{x['n']}" if (x["ok"] or x["short"]) else "-"
        print(f"{d.name:<24} {r['blocks']:>6} {r['words']:>6} {r['covered']:>8} "
              f"{r['pct']:>6.1f}%  {xcol:>7}  {nmiss}")

    # An arm that prints a translation per verse has discharged word coverage
    # STRUCTURALLY, so its Hebrew-skeleton `pct` no longer answers "did anything go
    # dark" — it answers "how much of the verse did the commentary choose to engage".
    # Say so, rather than let the column be read as a regression.
    slotted = [n for n, x in xlats.items() if len(x["ok"]) >= 0.8 * x["n"]]
    if slotted:
        print(f"\nNOTE — translation slot active in: {', '.join(slotted)}")
        print("  For these arms `pct` measures COMMENTARY ENGAGEMENT (how much Hebrew the")
        print("  commentary re-quotes), not coverage: the reader's coverage guarantee is the")
        print("  `xlat` column. A lower pct alongside a full xlat is the intended trade.")
        for n in slotted:
            x = xlats[n]
            if x["short"]:
                print(f"  {n}: SHORT/suspect translation at v.{x['short']}")
            if x["absent"]:
                print(f"  {n}: NO translation line at v.{x['absent']}")

    if args.detail:
        for name, r in results.items():
            if not r["missing"]:
                continue
            print(f"\n--- {name}: uncovered words by verse ---")
            for v in sorted(r["missing"]):
                print(f"  v.{v}: {' '.join(r['missing'][v])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
