"""
Shared-Vocabulary Parallels ("intertext radar") — deterministic, $0 (Session 384).

WHY THIS EXISTS
---------------
The concordance was being used as ~25 independent "look up word X" calls chosen by
an LLM. But the intertexts that made the Session-383 Psalm 76 guide original were
CLUSTERS of shared vocabulary, not single words:

    Hos 2:20    bow + sword + war + break      (Ps 76:4)
    Exod 15     horse + chariot + majestic + awesome + name
    Josh 14:15  "the land had rest from war"   (split across Ps 76:4 and 76:9)

The model found them only because it happened to search the right pair of words, and
arm A, which did not, never saw them. A database can find such clusters exhaustively.
This module scores every verse in the Bible by the summed rarity (IDF) of the
dictionary forms (BHSA lemmas) it shares with the psalm. On Ps 76 the prototype's top
45 included Hos 2:20, Ps 46:10, Exod 15:1, Nah 3:18, Isa 43:17 (chariot and horse that
"lie down, they shall not rise" — never found by either arm), Jer 30:10, Isa 7:4,
Hab 3:8 and Ezek 38:15.

WHAT IT EMITS
-------------
A markdown section for the research bundle, read by synthesis discovery and the
writer:
  1. Chapters in sustained dialogue with the psalm — one chapter sharing several
     uncommon words with several different psalm verses (how "the Song at the Sea run
     backwards" becomes visible to a computer).
  2. The closest single passages, each with its shared words and the psalm verses
     they come from, and the passage's Hebrew.

LIMITS, STATED IN THE EMITTED HEADER TOO
----------------------------------------
- Shared vocabulary is a lead, not proof of allusion. Common words are excluded by a
  frequency ceiling and everything else is weighted by rarity, but coincidence
  remains possible.
- The lemma column has no homonym markers (שם "name" = שם "there"), and ~3% of tokens
  have no lemma at all.
- A psalm heading's formula words (למנצח, מזמור, לדוד, …) are ignored, or every
  heading in the Psalter would match every other.

Degrades gracefully: returns "" when no populated tanakh.db is found (the cloud
clone ships a stub), and the caller skips the section.

Usage:
    from src.concordance.intertext_radar import compute_shared_vocabulary_parallels
    md, n = compute_shared_vocabulary_parallels(76)
"""

from __future__ import annotations

import math
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

try:
    from ..data_sources.tanakh_database import TANAKH_BOOKS
except ImportError:  # script mode
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.data_sources.tanakh_database import TANAKH_BOOKS


# --- Tunables -----------------------------------------------------------------
# A lemma found in more verses than this is too common to signal a parallel
# (ארץ 2,185, מלך 2,242, עם 2,505, שם 1,458, שמע 1,080 — all excluded; ידע 904 kept
# only because the ceiling sits above it... see below).
DF_CEILING = 800
# A shared lemma is DISTINCTIVE if it occurs in at most this many verses. A parallel
# must share at least MIN_DISTINCTIVE of them — otherwise long verses win on
# unremarkable words (גדול, הר, אדם).
DISTINCTIVE_DF = 300
MIN_DISTINCTIVE = 2
# How much of a match's weight must sit in ONE place in the psalm. The score is the
# best window of <= LOCAL_WINDOW consecutive psalm verses, plus SPREAD_WEIGHT times the
# rest, so a cohesive image cluster (Hos 2:20 <- v. 4) outranks the same words
# scattered, while a deliberate split (Josh 14:15 across vv. 4 and 9) still counts.
LOCAL_WINDOW = 2
SPREAD_WEIGHT = 0.5
MAX_PASSAGES = 20       # rows in "closest single passages"
MAX_CHAPTERS = 12       # rows in "chapters in sustained dialogue"
CHAPTER_POOL = 250      # top-scoring candidate verses aggregated into chapters
CHAPTER_MIN_VERSES = 2  # a chapter needs this many matching verses...
CHAPTER_MIN_PSALM_VERSES = 2  # ...touching this many different psalm verses...
CHAPTER_MIN_LEMMAS = 4  # ...through at least this many DISTINCTIVE shared words

# Divine names and titles carry no signal (they are everywhere, and the Elohistic
# Psalter swaps them). 'אל' is also the preposition "to" in this lemma column.
_DIVINE = frozenset({'יהוה', 'אלהים', 'אדני', 'אל', 'אלוה', 'יה'})
# Always skipped: a liturgical marker, and pronouns / particles whose frequency happens
# to sit under DF_CEILING. They carry grammar, not an image.
_ALWAYS_SKIP = frozenset({
    'סלה', 'אתה', 'אני', 'אנכי', 'הוא', 'היא', 'אנחנו', 'אתם', 'הם', 'המה', 'הן',
    'מי', 'מה', 'אז', 'זה', 'זאת', 'כה', 'כן', 'עוד', 'אך', 'רק', 'גם', 'אם', 'או',
    'אין', 'יש', 'עד', 'הנה', 'עתה', 'פן', 'בלי', 'בל', 'אל', 'אפס', 'למה', 'איך',
    'אשר', 'כי', 'לא', 'כל', 'את', 'על', 'עם', 'מן', 'תחת', 'אחר', 'בין', 'נגד',
})
# Lemmas that mark verse 1 as a heading, and the formula words ignored inside it.
_HEADING_MARKERS = frozenset({'נצח', 'מזמור', 'משכיל', 'מכתם', 'שגיון', 'מעלה'})
_HEADING_FORMULA = _HEADING_MARKERS | frozenset({
    'שיר', 'נגינה', 'תפלה', 'תהלה', 'זכר', 'ידע',
    'דוד', 'אסף', 'קרח', 'בן', 'שלמה', 'משה', 'הימן', 'איתן', 'ידותון', 'ידיתון',
})

_DEFAULT_DB_CANDIDATES = (Path("database/tanakh.db"), Path("data/tanakh.db"))

_CANON: Dict[str, int] = {}
for _section in ('Torah', 'Prophets', 'Writings'):
    for _entry in TANAKH_BOOKS.get(_section, []):
        _CANON[_entry[0]] = len(_CANON)

VerseKey = Tuple[str, int, int]

# Module-level cache: one index per database file per process.
_INDEX_CACHE: Dict[str, "_Index"] = {}


class _Index:
    """Per-verse lemma sets for the whole Bible, plus document frequencies."""

    def __init__(self, conn: sqlite3.Connection):
        self.verse_lemmas: Dict[VerseKey, Set[str]] = defaultdict(set)
        for book, ch, v, lem in conn.execute(
            "SELECT book_name, chapter, verse, lemma FROM concordance WHERE lemma IS NOT NULL"
        ):
            self.verse_lemmas[(book, ch, v)].add(lem)
        self.n_verses = len(self.verse_lemmas)
        self.df: Counter = Counter()
        for lems in self.verse_lemmas.values():
            self.df.update(lems)
        self.by_lemma: Dict[str, List[VerseKey]] = defaultdict(list)
        for key, lems in self.verse_lemmas.items():
            for lem in lems:
                if self._usable(lem):
                    self.by_lemma[lem].append(key)

    def _usable(self, lem: str) -> bool:
        return (self.df[lem] <= DF_CEILING and lem not in _DIVINE
                and lem not in _ALWAYS_SKIP)

    def idf(self, lem: str) -> float:
        return math.log(self.n_verses / max(1, self.df[lem]))


def _find_database(db_path: Optional[Path]) -> Optional[Path]:
    candidates = (Path(db_path),) if db_path else _DEFAULT_DB_CANDIDATES
    for p in candidates:
        if p.exists() and p.stat().st_size > 1_000_000:
            return p
    return None


def _get_index(db: Path) -> Optional[_Index]:
    key = str(db.resolve())
    if key not in _INDEX_CACHE:
        conn = sqlite3.connect(str(db))
        try:
            has_rows = conn.execute(
                "SELECT 1 FROM concordance WHERE lemma IS NOT NULL LIMIT 1").fetchone()
            if not has_rows:
                return None
            _INDEX_CACHE[key] = _Index(conn)
        finally:
            conn.close()
    return _INDEX_CACHE[key]


def _psalm_bag(index: _Index, psalm: int) -> Dict[str, List[int]]:
    """Usable lemma -> the psalm verses it occurs in (heading formula words dropped)."""
    verses = sorted(k[2] for k in index.verse_lemmas if k[0] == 'Psalms' and k[1] == psalm)
    bag: Dict[str, List[int]] = defaultdict(list)
    for v in verses:
        lems = index.verse_lemmas[('Psalms', psalm, v)]
        is_heading = v == 1 and bool(lems & _HEADING_MARKERS)
        for lem in lems:
            if not index._usable(lem):
                continue
            if is_heading and lem in _HEADING_FORMULA:
                continue
            bag[lem].append(v)
    return bag


def score_parallels(psalm: int, db_path: Optional[Path] = None
                    ) -> List[Tuple[float, VerseKey, FrozenSet[str]]]:
    """Every verse outside the psalm sharing >= MIN_SHARED usable lemmas with it, as
    (score, verse, shared_lemmas), best first. Score = summed IDF of the shared lemmas."""
    db = _find_database(db_path)
    if db is None:
        return []
    index = _get_index(db)
    if index is None:
        return []
    bag = _psalm_bag(index, psalm)
    hits: Dict[VerseKey, Set[str]] = defaultdict(set)
    for lem in bag:
        for key in index.by_lemma.get(lem, ()):
            if key[0] == 'Psalms' and key[1] == psalm:
                continue
            hits[key].add(lem)
    psalm_verses = sorted({v for vs in bag.values() for v in vs})
    windows = [set(psalm_verses[i:i + LOCAL_WINDOW]) for i in range(len(psalm_verses))]
    windows = [w for w in windows if max(w) - min(w) < LOCAL_WINDOW] or [set(psalm_verses)]
    scored = []
    for key, shared in hits.items():
        if sum(1 for l in shared if index.df[l] <= DISTINCTIVE_DF) < MIN_DISTINCTIVE:
            continue
        total = sum(index.idf(l) for l in shared)
        local = max(
            sum(index.idf(l) for l in shared if set(bag[l]) & w) for w in windows
        )
        score = local + SPREAD_WEIGHT * (total - local)
        scored.append((score, key, frozenset(shared)))
    scored.sort(key=lambda t: (-t[0], _CANON.get(t[1][0], 999), t[1][1], t[1][2]))
    return scored


def _verse_texts(db: Path, keys: List[VerseKey]) -> Dict[VerseKey, str]:
    out: Dict[VerseKey, str] = {}
    if not keys:
        return out
    conn = sqlite3.connect(str(db))
    try:
        for book, ch, v in keys:
            row = conn.execute(
                "SELECT hebrew FROM verses WHERE book_name = ? AND chapter = ? AND verse = ?",
                (book, ch, v)).fetchone()
            if row and row[0]:
                out[(book, ch, v)] = row[0]
    finally:
        conn.close()
    return out


def _fmt_verses(vs: List[int]) -> str:
    vs = sorted(set(vs))
    return ("v. " if len(vs) == 1 else "vv. ") + ", ".join(str(v) for v in vs)


def compute_shared_vocabulary_parallels(psalm: int, db_path: Optional[Path] = None
                                        ) -> Tuple[str, int]:
    """(markdown_section, number_of_passages_listed). ("", 0) when no data."""
    db = _find_database(db_path)
    if db is None:
        return "", 0
    index = _get_index(db)
    if index is None:
        return "", 0
    bag = _psalm_bag(index, psalm)
    scored = score_parallels(psalm, db)
    if not scored:
        return "", 0

    # --- chapters in sustained dialogue --------------------------------------
    chapters: Dict[Tuple[str, int], Dict] = {}
    for score, key, shared in scored[:CHAPTER_POOL]:
        ck = (key[0], key[1])
        c = chapters.setdefault(ck, {'verses': [], 'lemmas': set(), 'psalm_vs': set(), 'score': 0.0})
        c['verses'].append(key[2])
        c['lemmas'] |= shared
        for lem in shared:
            c['psalm_vs'].update(bag[lem])
        c['score'] += score
    for c in chapters.values():
        c['lemmas'] = {l for l in c['lemmas'] if index.df[l] <= DISTINCTIVE_DF}
        c['psalm_vs'] = {pv for l in c['lemmas'] for pv in bag[l]}
    dialogue = [
        (ck, c) for ck, c in chapters.items()
        if len(c['verses']) >= CHAPTER_MIN_VERSES and len(c['psalm_vs']) >= CHAPTER_MIN_PSALM_VERSES
        and len(c['lemmas']) >= CHAPTER_MIN_LEMMAS
    ]
    dialogue.sort(key=lambda t: -sum(index.idf(l) for l in t[1]['lemmas']))
    dialogue = dialogue[:MAX_CHAPTERS]

    # --- closest single passages ---------------------------------------------
    top = scored[:MAX_PASSAGES]
    texts = _verse_texts(db, [k for _, k, _ in top])

    md = "## Shared-Vocabulary Parallels (computed)\n\n"
    md += ("*Passages elsewhere in the Bible that share several uncommon words with this "
           "psalm, matched by dictionary form (lemma), so prefixes, suffixes and "
           "conjugation do not hide a match. Found by exhaustive search of every verse, not "
           "by recall; rarer words weigh more, and very common words, divine names and "
           "heading formulas are ignored. Shared vocabulary is a LEAD, not proof of "
           "allusion: judge each on its merits. Limits: homonyms share one lemma "
           "(שם 'name' = שם 'there'), and ~3% of words have no lemma.*\n\n")
    if dialogue:
        md += "### Chapters in sustained dialogue with the psalm\n\n"
        for (book, ch), c in dialogue:
            lemmas = sorted(c['lemmas'], key=lambda l: -index.idf(l))
            md += (f"- **{book} {ch}** — {len(lemmas)} shared distinctive words "
                   f"({', '.join(lemmas)}) touching this psalm's "
                   f"{_fmt_verses(list(c['psalm_vs']))}; matching verses "
                   f"{', '.join(f'{ch}:{v}' for v in sorted(set(c['verses'])))}\n")
        md += "\n"
    md += "### Closest single passages\n\n"
    for score, key, shared in top:
        book, ch, v = key
        lemmas = sorted(shared, key=lambda l: -index.idf(l))
        src = sorted({pv for l in shared for pv in bag[l]})
        md += (f"**{book} {ch}:{v}** — shares {', '.join(lemmas)} "
               f"(from this psalm's {_fmt_verses(src)})\n")
        if key in texts:
            md += f"{texts[key]}\n"
        md += "\n"
    return md, len(top)


if __name__ == "__main__":
    import argparse
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("psalm", type=int)
    ap.add_argument("--db", type=Path, default=None)
    args = ap.parse_args()
    text, n = compute_shared_vocabulary_parallels(args.psalm, args.db)
    print(text or "(no data)")
    print(f"[{n} passages, {len(text):,} chars]", file=sys.stderr)
