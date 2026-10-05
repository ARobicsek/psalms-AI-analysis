"""
Where a psalm's words occur in the liturgy: a word-level matcher (Session 395).

Replaces, for the librarian, the Session-1xx phrase index (`psalms_liturgy_index`),
whose two matching faults reached the guides:

* it matched consonant SUBSTRINGS with no word boundaries, so "ציון אשר" (78:68) was
  found in the header "ובא לציון אשרי" and "אל וקדוש" (78:41) in "אל וקדושתו";
* its normalisation kept the zero-width joiner Sefaria writes in עָו‍ֹן (111 of the
  1,123 texts), so a verse quoted whole in the Ashkenaz machzorim was indexed as
  fragments, and each fragment became a separate summary.

Here both texts are cut into WORDS and compared word by word on a spelling-tolerant
key (`skeleton`: consonants, final letters folded, ו/י dropped after the first
letter, divine-name spellings unified). A match is a maximal run of equal words;
runs broken by a small variant (one or two words) are merged. Every run is then
tested against the whole Tanakh (`attribute`): if the liturgy's wording around it
matches ANOTHER verse for longer than it matches ours, the prayer is quoting that
verse, and a fragment is dropped (a whole verse is kept, with the parallel named:
the siddur's Hodu is 1 Chronicles 16, the Chronicler's copy of Psalm 105).

Pure functions plus two corpus loaders; no model calls. `find_hits` is the entry point.
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

LITURGY_DB = "data/liturgy.db"
TANAKH_DB = "database/tanakh.db"

FINALS = str.maketrans("ךםןףץ", "כמנפצ")
_HEB = re.compile(r"[א-ת]+")
# Divine-name spellings the prayer books use for the tetragrammaton and Elohim.
_YHWH = {"יהוה", "יהוה", "יי", "ייי", "יקוק", "ידוד", "הויה"}

# Function words, pronouns, forms of היה and divine names: a fragment made only of
# these (or with one content word) is idiom, not quotation. Compared as skeletons.
_STOP = """
ולא לא כי וכי אשר כאשר באשר את ואת אתו אותו אתם אל על ועל אלי עלי עליו עליהם מן מאת עד ועד
כל וכל לכל בכל ככל הכל מכל הוא והוא היא והיא הם הם המה והם אני ואני אנכי ואנכי אתה ואתה את אנחנו
גם וגם אף ואף אם ואם הנה והנה זה וזה זאת וזאת אלה ואלה הלא למה ולמה מה ומה מי ומי כן וכן
לו לה להם להן לנו לי לך לכם בו בה בם בהם בנו בי בך עם ועם עמו עמנו עמי לפני לפניו לפניך אחרי
היה היו יהיה יהיו ויהי ויהיו תהיה נהיה היתה הייתי היית והיה ויהיה תהי יהי ויהי
יהוה אלהים אלהי אלהינו אלהיך אלהיו אל אדני יה שדי עליון ה
"""
STOP = frozenset()  # filled below, once skeleton() exists


def strip_marks(text: str) -> str:
    """Letters, spaces and the marks that separate words; vowels, accents, ZWJ etc. dropped."""
    text = unicodedata.normalize("NFKD", text or "")
    # divine-name abbreviations: ה' / ה׳ / ה’ as a whole word
    text = re.sub(r"(?<![א-ת])ה[֑-ׇ]*['׳’](?![א-ת])", " יהוה ", text)
    out = []
    for ch in text:
        if "א" <= ch <= "ת":
            out.append(ch)
        elif "֑" <= ch <= "ׇ" and ch not in "־׀׃":
            continue                       # vowel / accent (maqaf, paseq, sof pasuq separate words)
        elif unicodedata.category(ch) in ("Cf", "Mn"):
            continue                       # ZWJ, ZWNJ, RLM, CGJ, combining marks
        else:
            out.append(" ")
    return "".join(out)


def skeleton(word: str) -> str:
    """Spelling-tolerant key: finals folded, ו/י dropped after the first letter, divine names unified."""
    w = word.translate(FINALS)
    if w in _YHWH:
        return "יהה"
    w = re.sub(r"^([ובלכמהש]{0,3})אלק", r"\1אלה", w)   # אלקים / אלקינו -> אלהים / אלהינו
    if w == "קל":
        w = "אל"
    k = w[0] + re.sub("[וי]", "", w[1:]) if w else w
    return k or w


STOP = frozenset(skeleton(w) for w in _STOP.split())


@dataclass
class Tokens:
    """A text cut into words: skeleton keys, and each word's character span in the original."""
    keys: List[str]
    spans: List[Tuple[int, int]]


def tokenize(text: str) -> Tokens:
    """Word tokens of an original (pointed) text with their char spans in THAT text.

    The spans index the original string, so excerpts keep their vowels. Marks are
    stripped per word; maqaf, paseq, punctuation and whitespace separate words."""
    keys, spans = [], []
    src = text or ""
    # A "word" is a maximal stretch of Hebrew letters, points, accents and invisible
    # format characters (ZWJ inside עָו‍ֹן must not split it); everything else separates.
    for m in re.finditer(r"[א-ת֑-ֽֿׁׂׄ-ׇ​-‏⁠﻿͏"
                         r"יִ-ﭏ]+['׳’]?", src):
        raw = m.group()
        if raw[-1] in "'׳’":
            letters = _HEB.findall(strip_marks(raw[:-1]))
            if letters == ["ה"]:
                keys.append("יהה")
                spans.append(m.span())
                continue
            raw = raw[:-1]
        for w in _HEB.findall(strip_marks(raw)):
            keys.append(skeleton(w))
            spans.append(m.span())
    return Tokens(keys, spans)


# ---------------------------------------------------------------------------
# The psalm
# ---------------------------------------------------------------------------

def clean_masoretic(h: str) -> str:
    """tanakh.db verse -> the text as read: qere kept, ketiv and *(textual notes) dropped."""
    h = re.sub(r"\*\([^)]*\)", "", h or "")
    h = re.sub(r"\(([^)]*)\)\s*\[([^\]]*)\]", r"\2", h)    # (ketiv) [qere] -> qere
    h = re.sub(r"[\(\)\[\]]", "", h)
    return h


@dataclass
class PsalmText:
    chapter: int
    verses: Dict[int, str]              # verse -> pointed Hebrew (qere)
    keys: List[str]                     # all words of the psalm, in order
    verse_of: List[int]                 # verse number of each word
    verse_range: Dict[int, Tuple[int, int]]   # verse -> [start, end) word indexes


def load_psalm(chapter: int, tanakh_db: str = TANAKH_DB) -> PsalmText:
    with sqlite3.connect(tanakh_db) as c:
        rows = c.execute("SELECT verse, hebrew FROM verses WHERE book_name='Psalms' AND chapter=? ORDER BY verse",
                         (chapter,)).fetchall()
    verses, keys, verse_of, rng = {}, [], [], {}
    for v, h in rows:
        text = clean_masoretic(h)
        verses[v] = text
        t = tokenize(text)
        rng[v] = (len(keys), len(keys) + len(t.keys))
        keys.extend(t.keys)
        verse_of.extend([v] * len(t.keys))
    return PsalmText(chapter, verses, keys, verse_of, rng)


# ---------------------------------------------------------------------------
# The two corpora (cached per process)
# ---------------------------------------------------------------------------

@dataclass
class Prayer:
    prayer_id: int
    ref: str
    book: str
    nusach: str
    prayer_type: str
    text: str
    tokens: Tokens


@lru_cache(maxsize=2)
def load_liturgy(db_path: str = LITURGY_DB) -> Tuple[Prayer, ...]:
    with sqlite3.connect(db_path) as c:
        rows = c.execute("SELECT prayer_id, sefaria_ref, source_text, nusach, prayer_type, hebrew_text "
                         "FROM prayers WHERE hebrew_text IS NOT NULL AND hebrew_text != '' "
                         "ORDER BY prayer_id").fetchall()
    return tuple(Prayer(pid, ref, book, nus, pt, h, tokenize(h)) for pid, ref, book, nus, pt, h in rows)


@dataclass
class TanakhIndex:
    keys: List[str]
    loc: List[Tuple[str, int, int]]        # (book, chapter, verse) of each word
    bigrams: Dict[Tuple[str, str], List[int]]


@lru_cache(maxsize=1)
def load_tanakh(tanakh_db: str = TANAKH_DB) -> TanakhIndex:
    with sqlite3.connect(tanakh_db) as c:
        rows = c.execute("SELECT book_name, chapter, verse, hebrew FROM verses ORDER BY verse_id").fetchall()
    keys, loc = [], []
    for b, ch, v, h in rows:
        for k in tokenize(clean_masoretic(h)).keys:
            keys.append(k)
            loc.append((b, ch, v))
    big = defaultdict(list)
    for i in range(len(keys) - 1):
        big[(keys[i], keys[i + 1])].append(i)
    return TanakhIndex(keys, loc, dict(big))


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

@dataclass
class Run:
    """A stretch of a prayer that matches a stretch of the psalm, word for word (or nearly)."""
    prayer: Prayer
    lit_start: int
    lit_end: int            # exclusive (word index in the prayer)
    ps_start: int
    ps_end: int             # exclusive (word index in the psalm)
    matched: int            # words matched (lit_end - lit_start minus the gaps of a merge)
    gaps: int = 0           # words skipped by merges (variants)
    verses_full: Tuple[int, ...] = ()
    verses_touched: Tuple[int, ...] = ()
    parallel: Optional[str] = None       # another verse the liturgy matches as well or better
    parallel_longer: bool = False        # ... strictly better: the prayer quotes that verse
    dropped: Optional[str] = None        # why a fragment was set aside
    same_words_at: Tuple[int, ...] = ()  # psalm word positions with the identical words (a refrain)

    @property
    def char_span(self) -> Tuple[int, int]:
        sp = self.prayer.tokens.spans
        return sp[self.lit_start][0], sp[self.lit_end - 1][1]


def _maximal_runs(ps: PsalmText, prayer: Prayer, psalm_bigrams: Dict[Tuple[str, str], List[int]]) -> List[Run]:
    lk, pk = prayer.tokens.keys, ps.keys
    out = []
    for j in range(len(lk) - 1):
        starts = psalm_bigrams.get((lk[j], lk[j + 1]))
        if not starts:
            continue
        for i in starts:
            if i > 0 and j > 0 and pk[i - 1] == lk[j - 1]:
                continue                                  # not left-maximal: found from an earlier start
            n = 2
            while i + n < len(pk) and j + n < len(lk) and pk[i + n] == lk[j + n]:
                n += 1
            out.append(Run(prayer, j, j + n, i, i + n, n))
    return out


def _merge(runs: List[Run], max_gap: int = 2) -> List[Run]:
    """Join runs a small variant split: next run starts ≤ max_gap words later in BOTH texts."""
    runs = sorted(runs, key=lambda r: (r.lit_start, r.ps_start))
    merged: List[Run] = []
    for r in runs:
        if merged:
            m = merged[-1]
            dl, dp = r.lit_start - m.lit_end, r.ps_start - m.ps_end
            if 0 <= dl <= max_gap and 0 <= dp <= max_gap:
                merged[-1] = Run(m.prayer, m.lit_start, r.lit_end, m.ps_start, r.ps_end,
                                 m.matched + r.matched, m.gaps + max(dl, dp))
                continue
        merged.append(r)
    return merged


def _dedupe_overlaps(runs: List[Run]) -> List[Run]:
    """A prayer span matched at two places in the psalm: keep the longest. When two places tie
    for the SAME span (a refrain: 46:8 = 46:12, 118:1 = 118:29), keep both and mark each with
    the other's position, so the hit is listed under both verses."""
    runs = sorted(runs, key=lambda r: (-r.matched, r.lit_start, r.ps_start))
    kept: List[Run] = []
    for r in runs:
        twins = [k for k in kept if (k.lit_start, k.lit_end, k.matched) == (r.lit_start, r.lit_end, r.matched)]
        if twins:
            for k in twins:
                k.same_words_at += (r.ps_start,)
                r.same_words_at += (k.ps_start,)
            kept.append(r)
            continue
        if any(r.lit_start < k.lit_end and k.lit_start < r.lit_end for k in kept):
            continue
        kept.append(r)
    return sorted(kept, key=lambda r: (r.lit_start, r.ps_start))


def _classify(ps: PsalmText, r: Run) -> None:
    full, touched = [], []
    for v, (a, b) in ps.verse_range.items():
        if b <= r.ps_start or a >= r.ps_end:
            continue
        overlap = min(b, r.ps_end) - max(a, r.ps_start)
        if a >= r.ps_start and b <= r.ps_end:
            full.append(v)
        elif overlap >= 2:
            touched.append(v)
    r.verses_full, r.verses_touched = tuple(full), tuple(touched)


def is_distinctive(keys: Sequence[str]) -> bool:
    """Can these words, alone, show that a prayer quotes the psalm? (≥ 3 words with two
    content words; 2 only if both are content words.) Whether another verse has the same
    words is `attribute`'s question, asked next."""
    content = [k for k in keys if k not in STOP and len(k) > 1]
    if len(keys) >= 4:
        return len(content) >= 2
    if len(keys) == 3:
        return len(content) >= 2
    return len(keys) == 2 and len(content) == 2


def _ref(loc: Tuple[str, int, int]) -> str:
    b, ch, v = loc
    return f"{b} {ch}:{v}"


def attribute(r: Run, ps: PsalmText, tanakh: TanakhIndex, window: int = 12) -> None:
    """Does the prayer's wording around this run match ANOTHER verse at least as well?

    Takes the prayer's words from `window` before to `window` after the run and finds the
    longest common stretch with any other place in the Bible that overlaps the run. Sets
    `parallel` (that verse) and `parallel_longer` (it matches for longer than ours does)."""
    lk = r.prayer.tokens.keys
    a, b = max(0, r.lit_start - window), min(len(lk), r.lit_end + window)
    w = lk[a:b]
    own = ("Psalms", ps.chapter)
    best_len, best_loc = 0, None
    for k in range(len(w) - 1):
        for t in tanakh.bigrams.get((w[k], w[k + 1]), ()):
            book, ch, _ = tanakh.loc[t]
            if (book, ch) == own:
                continue
            if k > 0 and t > 0 and tanakh.keys[t - 1] == w[k - 1]:
                continue
            n = 2
            while k + n < len(w) and t + n < len(tanakh.keys) and tanakh.keys[t + n] == w[k + n]:
                n += 1
            # must overlap at least half of the run, in prayer coordinates
            s, e = a + k, a + k + n
            ov = min(e, r.lit_end) - max(s, r.lit_start)
            if ov * 2 < (r.lit_end - r.lit_start):
                continue
            if n > best_len:
                best_len, best_loc = n, tanakh.loc[t]
    if best_loc and best_len >= min(r.matched, 3):
        r.parallel = _ref(best_loc)
        r.parallel_longer = best_len > r.matched + r.gaps


def find_hits(chapter: int, liturgy_db: str = LITURGY_DB, tanakh_db: str = TANAKH_DB,
              keep_dropped: bool = False) -> List[Run]:
    """Every place in the liturgy that quotes Psalm `chapter`: whole verses, runs of verses,
    and distinctive fragments, each tested against the rest of the Bible."""
    ps = load_psalm(chapter, tanakh_db)
    tanakh = load_tanakh(tanakh_db)
    big = defaultdict(list)
    for i in range(len(ps.keys) - 1):
        big[(ps.keys[i], ps.keys[i + 1])].append(i)
    big = dict(big)
    hits: List[Run] = []
    for prayer in load_liturgy(liturgy_db):
        runs = _maximal_runs(ps, prayer, big)
        if not runs:
            continue
        for r in _dedupe_overlaps(_merge(runs)):
            _classify(ps, r)
            whole = [v for v in r.verses_full if (lambda ab: ab[1] - ab[0])(ps.verse_range[v]) >= 4]
            if not whole and not is_distinctive(ps.keys[r.ps_start:r.ps_end]):
                continue                               # idiom-length overlap: not even a candidate
            attribute(r, ps, tanakh)
            if not whole and r.parallel_longer:
                r.dropped = f"the prayer quotes {r.parallel}, which shares these words"
            elif not whole and r.parallel and r.matched + r.gaps <= 3:
                r.dropped = f"too short to tell from {r.parallel}, which has the same words"
            if r.dropped and not keep_dropped:
                continue
            hits.append(r)
    return hits
