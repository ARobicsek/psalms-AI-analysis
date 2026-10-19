"""
Shared Passages (doublets and shared lines) — deterministic, $0 (Session 409).

WHY THIS EXISTS
---------------
It replaces the "Related Psalms Analysis" section (related_psalms_librarian), which listed
the five psalms with the most shared vocabulary and every word and two-word phrase they
shared: 5-23K chars per bundle, mostly noise (כִּי אַתָּה, אני, a "root" עד that matched
בַּעֲדַת), and on eleven guides (Pss 29, 73-82) only three related psalms reached a guide
through it alone. Its one unique service was the Session-365 DOUBLET alert (a finished
Ps 60 guide never mentioned Ps 108). That alert compared whole verses as word SETS, so on a
scan of the whole Bible it missed a short verse inside a longer one (79:10 ~ 115:2), a
prefix variant (6:2 ~ 38:2), and differently divided verses (96:9-13 ~ 1 Chr 16:29-33,
135 ~ 136, 132:8-10 ~ 2 Chr 6:41-42), and flagged eight psalm headings as shared verses.

HOW IT WORKS
------------
Each chapter of the Bible is a stream of dictionary forms (BHSA lemmas; the bare
consonants where a word has none), so prefixes, suffixes and verse divisions do not hide
a match. Matching words between the psalm and another chapter are chained IN ORDER with
at most MAX_GAP unmatched words between links on either side. A chain is a shared
passage when it holds MIN_CONTENT uncommon words (outside the COMMON_TOP most frequent
lemmas), or when a near-contiguous stretch of it (gaps <= TIGHT_GAP) matches TIGHT_MIN
words, common or not (that is how "לָמָּה יֹאמְרוּ הַגּוֹיִם אַיֵּה אֱלֹהֵיהֶם" is found).
A pair of texts sharing DOUBLET_MIN words in passages is a DOUBLET and is printed with its
word variants; anything less is a shared line, printed with the other text's wording.

Calibrated on 32 known doublets and shared verses (tests/test_shared_passages.py). It
does not find paraphrases (Ps 1:3 ~ Jer 17:8, Ps 77 ~ Hab 3) or a quotation split across
distant verses (Ps 107:40 ~ Job 12:21, 24); the shared-vocabulary section is the place
for those leads.

Degrades gracefully: returns ("", []) when no populated tanakh.db is found.

Usage:
    from src.concordance.shared_passages import compute_shared_passages
    md, refs = compute_shared_passages(96)
"""

from __future__ import annotations

import re
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from ..data_sources.tanakh_database import TANAKH_BOOKS
except ImportError:  # script mode
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.data_sources.tanakh_database import TANAKH_BOOKS


# --- Tunables (pinned by tests/test_shared_passages.py) -----------------------------
MAX_GAP = 3          # unmatched words allowed between two links of a chain, on either side
COMMON_TOP = 100     # the most frequent lemmas are "common": they link a chain but never count as content
MIN_CONTENT = 4      # a chain is a shared passage with this many uncommon words in it...
TIGHT_GAP = 1        # ...or with a stretch whose links skip at most this many words...
TIGHT_MIN = 5        # ...matching at least this many words
SEED_MAX_CHAPTERS = 40  # a chapter is compared when it shares a lemma pair found in <= this many chapters
DOUBLET_MIN = 12     # words shared in passages that make a pair of texts a DOUBLET
MAX_VARIANTS = 30    # variant lines printed per doublet
MAX_SHARED_LINES = 6  # shared-line entries printed (doublets are never cut)

SECTION_HEADER = "## Shared Passages (computed)"

# Heading formula words weigh nothing inside a psalm heading (verse 1 carrying a marker),
# or every למנצח מזמור לדוד would match every other. Same lists as intertext_radar.
_HEADING_MARKERS = frozenset({'נצח', 'מזמור', 'משכיל', 'מכתם', 'שגיון', 'מעלה'})
_HEADING_FORMULA = _HEADING_MARKERS | frozenset({
    'שיר', 'נגינה', 'תפלה', 'תהלה', 'זכר', 'ידע', 'דוד', 'אסף', 'קרח', 'בן', 'שלמה',
    'משה', 'הימן', 'איתן', 'ידותון', 'ידיתון', 'למנצח',
})
_NIKUD = re.compile(r'[֑-ׇ]')
_DEFAULT_DB_CANDIDATES = (Path("database/tanakh.db"), Path("data/tanakh.db"))

_CANON: Dict[str, int] = {}
for _section in ('Torah', 'Prophets', 'Writings'):
    for _entry in TANAKH_BOOKS.get(_section, []):
        _CANON[_entry[0]] = len(_CANON)

Unit = Tuple[str, int]  # (book, chapter)


@dataclass
class _Tok:
    verse: int
    lemma: str
    word: str      # pointed, without cantillation
    weight: int    # 0 = heading formula (never matched); 1 = common; 2 = content


@dataclass
class Passage:
    other: Unit
    links: List[Tuple[int, int]]       # (psalm token index, other token index)
    matched: int
    ps_verses: Tuple[int, int]
    other_verses: Tuple[int, int]


@dataclass
class _Index:
    units: Dict[Unit, List[_Tok]] = field(default_factory=dict)
    seeds: Dict[Tuple[str, str], List[Unit]] = field(default_factory=dict)


_INDEX_CACHE: Dict[str, _Index] = {}


def _find_database(db_path: Optional[Path]) -> Optional[Path]:
    candidates = (Path(db_path),) if db_path else _DEFAULT_DB_CANDIDATES
    for p in candidates:
        if p.exists() and p.stat().st_size > 1_000_000:
            return p
    return None


def _build_index(conn: sqlite3.Connection) -> Optional[_Index]:
    rows = conn.execute(
        "SELECT book_name, chapter, verse, lemma, word_consonantal, word_voweled "
        "FROM concordance ORDER BY book_name, chapter, verse, position").fetchall()
    if not rows:
        return None
    raw: Dict[Unit, List[Tuple[int, str, str]]] = defaultdict(list)
    for book, ch, v, lem, cons, voweled in rows:
        l = _NIKUD.sub('', lem or cons or '').strip()
        if l:
            raw[(book, ch)].append((v, l, voweled or cons or l))
    freq = Counter(l for toks in raw.values() for _, l, _ in toks)
    common = {l for l, _ in freq.most_common(COMMON_TOP)}
    idx = _Index()
    for unit, toks in raw.items():
        heading_v1 = unit[0] == 'Psalms' and any(
            v == 1 and l in _HEADING_MARKERS for v, l, _ in toks)
        idx.units[unit] = [
            _Tok(v, l, w, 0 if (heading_v1 and v == 1 and l in _HEADING_FORMULA)
                 else (1 if l in common else 2))
            for v, l, w in toks]
    seeds: Dict[Tuple[str, str], set] = defaultdict(set)
    for unit, toks in idx.units.items():
        for a, b in zip(toks, toks[1:]):
            if a.weight and b.weight:
                seeds[(a.lemma, b.lemma)].add(unit)
    idx.seeds = {k: sorted(v) for k, v in seeds.items() if len(v) <= SEED_MAX_CHAPTERS}
    return idx


def _get_index(db: Path) -> Optional[_Index]:
    key = str(db.resolve())
    if key not in _INDEX_CACHE:
        conn = sqlite3.connect(str(db))
        try:
            idx = _build_index(conn)
        finally:
            conn.close()
        if idx is None:
            return None
        _INDEX_CACHE[key] = idx
    return _INDEX_CACHE[key]


def _chains(a: List[_Tok], b: List[_Tok]) -> List[List[Tuple[int, int]]]:
    """Maximal in-order chains of matching lemmas, best first, no psalm word in two."""
    pos_b: Dict[str, List[int]] = defaultdict(list)
    for j, t in enumerate(b):
        if t.weight:
            pos_b[t.lemma].append(j)
    best: Dict[Tuple[int, int], Tuple[int, Optional[Tuple[int, int]]]] = {}
    for i, t in enumerate(a):
        if not t.weight:
            continue
        for j in pos_b.get(t.lemma, ()):
            score, prev = 1, None
            for di in range(1, MAX_GAP + 2):
                for dj in range(1, MAX_GAP + 2):
                    p = best.get((i - di, j - dj))
                    if p and p[0] + 1 > score:
                        score, prev = p[0] + 1, (i - di, j - dj)
            best[(i, j)] = (score, prev)
    used, out = set(), []
    for end, (score, _) in sorted(best.items(), key=lambda kv: (-kv[1][0], kv[0])):
        if score < TIGHT_MIN and score < MIN_CONTENT:
            break
        path, node = [], end
        while node:
            path.append(node)
            node = best[node][1]
        path.reverse()
        if any(i in used for i, _ in path):
            continue
        used.update(i for i, _ in path)
        out.append(path)
    return out


def _qualifying(path, a, b) -> List[List[Tuple[int, int]]]:
    """The parts of a chain that are shared passages (see the module docstring)."""
    # Common words dangling at either end are where a chain wanders into noise.
    lo, hi = 0, len(path)
    while lo < hi and a[path[lo][0]].weight < 2:
        lo += 1
    while hi > lo and a[path[hi - 1][0]].weight < 2:
        hi -= 1
    core = path[lo:hi]
    if sum(1 for i, _ in core if a[i].weight == 2) >= MIN_CONTENT:
        return [core]
    runs, run = [], [path[0]]
    for p, q in zip(path, path[1:]):
        if q[0] - p[0] - 1 <= TIGHT_GAP and q[1] - p[1] - 1 <= TIGHT_GAP:
            run.append(q)
        else:
            runs.append(run)
            run = [q]
    runs.append(run)
    return [r for r in runs if len(r) >= TIGHT_MIN and any(a[i].weight == 2 for i, _ in r)]


def find_shared_passages(psalm: int, db_path: Optional[Path] = None) -> List[Passage]:
    """Every shared passage between the psalm and another chapter of the Bible."""
    db = _find_database(db_path)
    idx = _get_index(db) if db else None
    if idx is None:
        return []
    a = idx.units.get(('Psalms', psalm))
    if not a:
        return []
    cands = set()
    for x, y in zip(a, a[1:]):
        if x.weight and y.weight:
            cands.update(idx.seeds.get((x.lemma, y.lemma), ()))
    cands.discard(('Psalms', psalm))
    found = []
    for unit in sorted(cands, key=lambda u: (_CANON.get(u[0], 999), u[1])):
        b = idx.units[unit]
        for path in _chains(a, b):
            for links in _qualifying(path, a, b):
                found.append(Passage(
                    other=unit, links=links, matched=len(links),
                    ps_verses=(a[links[0][0]].verse, a[links[-1][0]].verse),
                    other_verses=(b[links[0][1]].verse, b[links[-1][1]].verse)))
    return found


# --- Rendering ------------------------------------------------------------------------

def _short_book(book: str) -> str:
    return "Ps" if book == "Psalms" else book


def _vrange(ch: int, vs: Tuple[int, int]) -> str:
    return f"{ch}:{vs[0]}" if vs[0] == vs[1] else f"{ch}:{vs[0]}–{vs[1]}"


def _span_words(toks: List[_Tok], lo: int, hi: int) -> str:
    return " ".join(t.word for t in toks[lo:hi + 1])


def _variants(p: Passage, a: List[_Tok], b: List[_Tok]) -> List[str]:
    out = []
    for (i0, j0), (i1, j1) in zip(p.links, p.links[1:]):
        if i1 - i0 == 1 and j1 - j0 == 1:
            continue
        here = _span_words(a, i0 + 1, i1 - 1) or "—"
        there = _span_words(b, j0 + 1, j1 - 1) or "—"
        out.append(f"v. {a[i0 + 1].verse if i1 - i0 > 1 else a[i1].verse}: {here} ↔ {there}")
    return out


def compute_shared_passages(psalm: int, db_path: Optional[Path] = None
                            ) -> Tuple[str, List[str]]:
    """(markdown_section, references_listed). ("", []) when nothing is shared or no data."""
    passages = find_shared_passages(psalm, db_path)
    if not passages:
        return "", []
    idx = _get_index(_find_database(db_path))
    a = idx.units[('Psalms', psalm)]

    by_unit: Dict[Unit, List[Passage]] = defaultdict(list)
    for p in passages:
        by_unit[p.other].append(p)
    # A doublet needs ONE passage of DOUBLET_MIN words: a refrain shared twice (118:1 and
    # 118:29 ~ 136:1) adds up to as many words but is a shared line, not the same passage twice.
    doublets = sorted(((u, ps) for u, ps in by_unit.items()
                       if max(p.matched for p in ps) >= DOUBLET_MIN),
                      key=lambda t: -sum(p.matched for p in t[1]))
    doublet_units = {u for u, _ in doublets}

    # Shared lines: one entry per psalm verse where the sharing starts, listing every text
    # that shares it, quoted from the closest one. Strongest first, and each other text in
    # one entry only, so a refrain is one line, not one per place it recurs (Ps 136 ~ 118).
    lines: Dict[int, Dict] = {}
    placed: set = set()
    for p in sorted(passages, key=lambda p: -p.matched):
        if p.other in doublet_units or p.other in placed:
            continue
        placed.add(p.other)
        e = lines.setdefault(p.ps_verses[0], {'p': p, 'refs': []})
        e['refs'].append(f"{_short_book(p.other[0])} {_vrange(p.other[1], p.other_verses)}")
    shared = sorted(lines.values(), key=lambda e: (-e['p'].matched, e['p'].ps_verses))
    shown = shared[:MAX_SHARED_LINES]

    md = SECTION_HEADER + "\n\n"
    md += ("*Wording this psalm shares, in the same order, with another text of the Bible "
           "(compared word by word in dictionary forms across every chapter; paraphrase is not "
           "detected). A DOUBLET is the same passage twice: the guide must name it and say what "
           "each setting does with it. A shared line is a lead: use it only if it serves the "
           "argument.*\n\n")
    refs: List[str] = []
    for unit, ps in doublets:
        ps.sort(key=lambda p: p.links[0][0])
        b = idx.units[unit]
        here = ", ".join(_vrange(psalm, p.ps_verses) for p in ps)
        there = ", ".join(_vrange(unit[1], p.other_verses) for p in ps)
        ref = f"{_short_book(unit[0])} {there}"
        refs.append(ref)
        md += (f"### DOUBLET: Psalm {here} ≈ {unit[0]} {there} "
               f"({sum(p.matched for p in ps)} words shared in order)\n\n")
        var = [v for p in ps for v in _variants(p, a, b)]
        if var:
            md += "Variants (this psalm ↔ the other text):\n"
            md += "".join(f"- {v}\n" for v in var[:MAX_VARIANTS])
            if len(var) > MAX_VARIANTS:
                md += f"- …and {len(var) - MAX_VARIANTS} more\n"
        else:
            md += "Word for word the same.\n"
        md += "\n"
    if shown:
        md += "### Shared lines\n\n"
        for e in shown:
            refs.extend(e['refs'])
            p = e['p']
            wording = _span_words(idx.units[p.other], p.links[0][1], p.links[-1][1])
            md += f"- **{_vrange(psalm, p.ps_verses)}** ~ {'; '.join(e['refs'])}: {wording}\n"
        if len(shared) > len(shown):
            md += f"- …and {len(shared) - len(shown)} shorter shared lines\n"
        md += "\n"
    return md, refs


_LEGACY_SECTION = "## Related Psalms Analysis"
_SECTION_RE = re.compile(r'^## .*?(?=^## |\Z)', re.M | re.S)


def _section_span(bundle: str, header: str) -> Optional[Tuple[int, int]]:
    """(start, end) of a level-2 section: its header line up to the next level-2 header."""
    for m in _SECTION_RE.finditer(bundle):
        if m.group(0).startswith(header):
            return m.start(), m.end()
    return None


def parse_shared_passages_refs(bundle: str) -> List[str]:
    """The references a bundle's Shared Passages section lists (for the methods page)."""
    span = _section_span(bundle, SECTION_HEADER)
    if not span:
        return []
    text = bundle[span[0]:span[1]]
    refs = [_short_book(m.group(1)) + " " + m.group(2) for m in re.finditer(
        r'^### DOUBLET: .*? ≈ (.+?) (\d+:\S+(?:, \d+:\S+)*) \(\d+ words', text, re.M)]
    for m in re.finditer(r'^- \*\*[^*]+\*\* ~ (.+?): ', text, re.M):
        refs.extend(m.group(1).split('; '))
    return refs


def refresh_bundle_shared_passages(bundle: str, psalm: int, db_path: Optional[Path] = None
                                   ) -> Tuple[str, bool]:
    """A reused bundle (--skip-micro / --resume) built before Session 409 carries the old
    Related Psalms Analysis section: remove it and add the Shared Passages section after the
    shared-vocabulary section. (bundle, changed); a current bundle comes back unchanged."""
    changed = False
    span = _section_span(bundle, _LEGACY_SECTION)
    if span:
        bundle = bundle[:span[0]] + bundle[span[1]:]
        bundle = re.sub(r'(\n---\n\n)(?:---\n\n)+', r'\1', bundle)
        bundle = re.sub(r'^- \*\*Related psalms analyzed\*\*: .*\n', '', bundle, flags=re.M)
        changed = True
    if changed and _section_span(bundle, SECTION_HEADER) is None:
        md, _ = compute_shared_passages(psalm, db_path)
        if md:
            radar = _section_span(bundle, "## Shared-Vocabulary Parallels")
            figurative = _section_span(bundle, "## Figurative Language")
            at = radar[1] if radar else (figurative[0] if figurative else len(bundle))
            bundle = bundle[:at] + md + "---\n\n" + bundle[at:]
    return bundle, changed


if __name__ == "__main__":
    import argparse
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("psalm", type=int)
    ap.add_argument("--db", type=Path, default=None)
    args = ap.parse_args()
    text, refs = compute_shared_passages(args.psalm, args.db)
    print(text or "(nothing shared)")
    print(f"[{len(refs)} references, {len(text):,} chars]", file=sys.stderr)
