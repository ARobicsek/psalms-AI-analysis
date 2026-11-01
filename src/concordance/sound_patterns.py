"""
Sound Patterns (rhyme clusters) — deterministic, $0 (Session 412).

WHY THIS EXISTS
---------------
The author, reading the Ps 84 guide: verse 12 rings — וּמָגֵן … חֵן … יִתֵּן — and "sometimes rhymes of
this sort explain why the poet chose one word over another." Nothing in the pipeline looks for
it (the micro analyst caught the מגן / ימנע consonants of the same verse, not the rhyme). The
author's bar: such things are rare, so flag them without adding junk that distracts the writer.

HOW IT WORKS
------------
A word's rhyme is its last CLOSED syllable: the vowel (by class: a, e, i, o, u) and the
consonants after it, with vowel letters (matres) dropped, so מָגֵן, חֵן and יִתֵּן all rhyme on
"e-n". A verse is flagged when THREE or more words of different forms share a rhyme.
Grammatical endings rhyme for free and are left out (MORPHOLOGICAL: plural -im / -ot, the
pronoun suffixes -ay, -av, -am, -em, -ekh, construct -ei / -at, paragogic -un), and so are
function words (FUNCTION_WORDS: אֲשֶׁר, the preposition אֶל, עַל ...), which repeat in
formulas (144:8 = 144:11).

WHAT IT FINDS (measured over the 2,527 verses of the Psalter)
------------------------------------------------------------
Four verses: 78:24 (מָן / וּדְגַן / נָתַן), 84:12, 90:2 (וַתְּחוֹלֵל / וְתֵבֵל / אֵל) and 147:16
(כַּצָּמֶר / כָּאֵפֶר / יְפַזֵּר). The same words shuffled at random between verses give 3.9 on
average (SHUFFLE_BASELINE; `python -m src.concordance.sound_patterns --all`), so the Psalter
holds no more of these than chance would: nothing shows the poets sought them. An earlier,
looser count (9 against 5) was inflated by refrains repeated word for word (144:8 = 144:11,
130:7 ~ 131:3) and the paragogic -un of 104:29. The sound is real all the same, and a reader
hears it, so the section offers it as what the line sounds like and warns the writer not to
claim that the sound chose the words. It prints the words and the ending, nothing more.

Pairs, alliteration and consonance were not added: they are far commoner and would be noise.

Degrades gracefully: returns ("", []) when no populated tanakh.db is found.

Usage:
    from src.concordance.sound_patterns import compute_sound_patterns
    md, verses = compute_sound_patterns(84)
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

SECTION_HEADER = "## Sound Patterns (computed)"
MIN_WORDS = 3            # words of different forms sharing one rhyme in a verse
SHUFFLE_BASELINE = 3.9   # flagged Psalter verses when its words are shuffled between verses (mean of 20)

_DEFAULT_DB_CANDIDATES = (Path("database/tanakh.db"),
                          Path(__file__).parent.parent.parent / "database" / "tanakh.db")

# Cantillation, meteg, rafe, paseq, sof pasuq, upper/lower dots: everything but letters,
# vowels, dagesh and the shin/sin dots.
_MARKS = re.compile(r"[֑-ֽֿ֯׀׃-׆]")
_VOWEL = {"ִ": "i", "ֵ": "e", "ֶ": "e", "ַ": "a", "ָ": "a", "ׇ": "o",
          "ֹ": "o", "ֺ": "o", "ֻ": "u"}
_HOLAM, _DAGESH, _SEGOL = "ֹ", "ּ", "ֶ"
_FINALS = str.maketrans("ךםןףץ", "כמנפצ")
_PREFIXES = "והבלכמש"

# Endings that rhyme because they are grammar, not choice.
MORPHOLOGICAL = frozenset({"i-מ", "o-ת", "a-י", "a-יו", "a-מ", "e-מ", "e-י", "a-ת", "u-נ", "a-כ", "e-כ"})
# Function words (consonants, a leading ו removed). The preposition אֶל is matched by its
# segol so that אֵל 'God' (90:2) still counts.
FUNCTION_WORDS = frozenset({"אשר", "על", "עם", "אם", "מן", "את", "כן", "לכן"})

_LATIN = {"ב": "v", "ג": "g", "ד": "d", "ז": "z", "ח": "ḥ", "ט": "t", "כ": "kh", "ל": "l", "מ": "m",
          "נ": "n", "ס": "s", "ע": "ʿ", "פ": "f", "צ": "ts", "ק": "q", "ר": "r", "ש": "sh", "ת": "t",
          "א": "", "ה": "h", "ו": "v", "י": "y"}


def _letters(word: str) -> List[List[str]]:
    """[[letter, its marks]] for a pointed word."""
    out: List[List[str]] = []
    for ch in word:
        if "א" <= ch <= "ת":
            out.append([ch, ""])
        elif out and "֑" <= ch <= "ׇ":
            out[-1][1] += ch
    return out


def consonants(word: str) -> str:
    return "".join(c for c, _ in _letters(word)).translate(_FINALS)


def rhyme_key(word: str) -> Optional[str]:
    """'e-נ' for מָגֵן: the last full vowel and the consonants after it. None for a word ending in
    a vowel (open syllable) or too short to have a closed final syllable."""
    L = _letters(word)
    if len(L) < 2:
        return None
    trail: List[str] = []
    i, vowel = len(L) - 1, None
    while i >= 0:
        c, m = L[i]
        vowel = next((_VOWEL[x] for x in m if x in _VOWEL), None)
        if c == "ו" and _HOLAM in m:
            vowel = "o"
        elif c == "ו" and _DAGESH in m and vowel is None and i > 0 and not any(x in _VOWEL for x in L[i - 1][1]):
            vowel = "u"                                   # shuruk
        if vowel:
            if vowel == "a" and i == len(L) - 1 and c in "חעה" and i > 0:
                trail.append(c)                           # furtive patah: the vowel before it counts
                i -= 1
                vowel = None
                continue
            break
        trail.append(c)
        i -= 1
    if i < 0 or not trail:
        return None
    cons = "".join(reversed(trail)).translate(_FINALS)
    if vowel in "ie":
        cons = cons.lstrip("י")                           # hiriq / tsere male
    if vowel in "ou":
        cons = cons.lstrip("ו")
    if cons.endswith(("ה", "א")) and _DAGESH not in L[-1][1]:
        cons = cons[:-1]                                  # silent final he / aleph
    return f"{vowel}-{cons}" if cons else None


def _is_function_word(word: str) -> bool:
    cons = consonants(word)
    bare = cons[1:] if cons.startswith("ו") and len(cons) > 2 else cons
    if bare in FUNCTION_WORDS:
        return True
    return bare == "אל" and _SEGOL in word


def verse_words(hebrew: str) -> List[str]:
    text = _MARKS.sub("", unicodedata.normalize("NFC", hebrew))
    text = re.sub(r"\{[^}]*\}", " ", text).replace("־", " ")
    return [w for w in re.split(r"\s+", text) if w]


def clusters(words: List[str]) -> Dict[str, List[str]]:
    """{rhyme: [words in verse order]} for every rhyme shared by MIN_WORDS words of different
    forms (prefix letters ignored when telling forms apart, so אֵל / הָאֵל / וְאֵל is one word)."""
    by: Dict[str, List[str]] = defaultdict(list)
    forms: Dict[str, Set[str]] = defaultdict(set)
    for w in words:
        k = rhyme_key(w)
        if not k or k in MORPHOLOGICAL or _is_function_word(w):
            continue
        f = consonants(w).lstrip(_PREFIXES) or consonants(w)
        if f not in forms[k]:
            forms[k].add(f)
            by[k].append(w)
    return {k: ws for k, ws in by.items() if len(forms[k]) >= MIN_WORDS}


def _find_database(db_path: Optional[Path]) -> Optional[Path]:
    for p in ((Path(db_path),) if db_path else _DEFAULT_DB_CANDIDATES):
        if p.exists() and p.stat().st_size > 1_000_000:
            return p
    return None


def psalm_verses(psalm: int, db_path: Optional[Path] = None) -> List[Tuple[int, str]]:
    db = _find_database(db_path)
    if db is None:
        return []
    with sqlite3.connect(str(db)) as conn:
        return conn.execute("SELECT verse, hebrew FROM verses WHERE book_name = 'Psalms' AND chapter = ? "
                            "ORDER BY verse", (psalm,)).fetchall()


def _ending(key: str) -> str:
    vowel, cons = key.split("-", 1)
    return "-" + vowel + "".join(_LATIN.get(c, c) for c in cons)


def compute_sound_patterns(psalm: int, db_path: Optional[Path] = None) -> Tuple[str, List[int]]:
    """(markdown_section, verses_flagged). ("", []) when no verse rings or no data."""
    rows = [(v, clusters(verse_words(h))) for v, h in psalm_verses(psalm, db_path)]
    rows = [(v, cl) for v, cl in rows if cl]
    if not rows:
        return "", []
    md = (f"{SECTION_HEADER}\n\n"
          "*Verses in which three or more different words end in the same closed syllable, not counting "
          "grammatical endings (plurals, pronoun suffixes) or small function words. Only four verses in the "
          "Psalter do this, and that is about as many as chance would produce, so nothing shows the poet "
          "sought the rhyme. The sound is real all the same, and a reader hears it: say what the line sounds "
          "like if it serves the reading, but do not claim the sound chose the words, which usually have "
          "other reasons (an idiom, a word taken up from an earlier verse).*\n\n")
    for v, cl in rows:
        for key, ws in cl.items():
            md += f"- **{psalm}:{v}**: {' · '.join(ws)} (all end in *{_ending(key)}*)\n"
    return md + "\n", [v for v, _ in rows]


def refresh_bundle_sound_patterns(bundle: str, psalm: int, db_path: Optional[Path] = None) -> Tuple[str, bool]:
    """A reused bundle (--skip-micro / --resume) built before Session 412 has no Sound Patterns
    section: add it (only when the psalm has one) after the Shared Passages section, else after
    the shared-vocabulary section. (bundle, changed)."""
    if SECTION_HEADER in bundle:
        return bundle, False
    md, _ = compute_sound_patterns(psalm, db_path)
    if not md:
        return bundle, False
    from src.concordance.shared_passages import SECTION_HEADER as SHARED, _section_span
    span = (_section_span(bundle, SHARED) or _section_span(bundle, "## Shared-Vocabulary Parallels")
            or _section_span(bundle, "## Figurative Language"))
    at = (span[0] if span and bundle[span[0]:].startswith("## Figurative") else span[1]) if span else len(bundle)
    return bundle[:at] + md + "---\n\n" + bundle[at:], True


if __name__ == "__main__":
    import argparse
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("psalm", type=int, nargs="?", help="omit with --all")
    ap.add_argument("--all", action="store_true", help="every psalm, then the shuffle baseline")
    ap.add_argument("--db", type=Path, default=None)
    args = ap.parse_args()
    if not args.all:
        text, verses = compute_sound_patterns(args.psalm, args.db)
        print(text or "(no sound pattern)")
        print(f"[{len(verses)} verse(s), {len(text):,} chars]", file=sys.stderr)
        sys.exit(0)
    import random
    allv = [verse_words(h) for p in range(1, 151) for _, h in psalm_verses(p, args.db)]
    for p in range(1, 151):
        text, verses = compute_sound_patterns(p, args.db)
        if verses:
            print(text.split("\n\n", 2)[2].rstrip())
    words = [w for ws in allv for w in ws]
    runs = []
    for seed in range(20):
        random.Random(seed).shuffle(words)
        pos = n = 0
        for ws in allv:
            n += bool(clusters(words[pos:pos + len(ws)]))
            pos += len(ws)
        runs.append(n)
    print(f"shuffle baseline over {len(allv)} verses, 20 runs: mean {sum(runs) / len(runs):.1f} "
          f"(min {min(runs)}, max {max(runs)})")
