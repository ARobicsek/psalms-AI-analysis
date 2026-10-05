"""
The liturgical catalogue of a psalm: every hit, consolidated per verse (Session 395).

`verse_matcher.find_hits` says WHERE in which text a psalm's words occur. This module
turns those rows into what a reader needs: per verse (or run of verses, or the whole
psalm), the PLACES it is said, each place listing every rite and book in which it was
found. Sefaria repeats one text in many books (the Ashkenaz Hodu is in the weekday
siddur, the Shabbat siddur and both machzorim), and its section titles are containers
("Ashrei" holds Uva LeTzion; "Weekday Arvit, Amidah" opens with Vehu Rachum), so a
place is named by the nearest well-known prayer opening before the hit (`LANDMARKS`)
when there is one, and by the section title otherwise.

The old librarian showed its model the first five of these rows, chosen by prayer name,
and never the rest (S395: 47% of all matches, a whole rite missing in 118 summaries).
`render_for_model` gives the model the complete table, with one excerpt per place.
"""

from __future__ import annotations

import re
from collections import Counter, OrderedDict, defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

from src.liturgy import verse_matcher as vm

# Well-known prayer openings, used to say where inside a long Sefaria section a hit
# falls. (label, incipit). Matching is on skeleton words, so spelling does not matter.
LANDMARKS: Sequence[Tuple[str, str, int]] = (
    # (label, incipit, reach in words: how far after the opening a hit can still be inside it)
    ("Hodu (1 Chr 16:8–36 and the verses after it)", "הודו ליהוה קראו בשמו הודיעו", 450),
    ("Yehi Chevod (Pesukei Dezimra)", "יהי כבוד יהוה לעולם ישמח", 220),
    ("Barukh She'amar", "ברוך שאמר והיה העולם", 150),
    ("Ashrei (Ps 145)", "אשרי יושבי ביתך", 260),
    ("Uva LeTzion", "ובא לציון גואל", 260),
    ("Ve'atah Kadosh (the Kedushah de-Sidra: in Uva LeTzion, and on its own on Motza'ei Shabbat)",
     "ואתה קדוש יושב תהלות ישראל", 200),
    ("Vayevarekh David (Pesukei Dezimra)", "ויברך דויד את יהוה לעיני", 220),
    ("Song of the Sea (Az Yashir)", "אז ישיר משה ובני ישראל", 260),
    ("Nishmat", "נשמת כל חי תברך", 400),
    ("Yishtabach", "ישתבח שמך לעד", 120),
    ("Yotzer Or (first blessing before the Shema)", "יוצר אור ובורא חשך", 450),
    ("El Adon", "אל אדון על כל המעשים", 120),
    ("Barchu", "ברכו את יהוה המברך", 60),
    ("Shema", "שמע ישראל יהוה אלהינו יהוה אחד", 280),
    ("Emet VeEmunah (Ma'ariv blessing after the Shema)", "אמת ואמונה כל זאת", 200),
    ("Hashkiveinu (Ma'ariv)", "השכיבנו יהוה אלהינו לשלום", 150),
    ("Barukh Hashem Le'olam (verses after Hashkiveinu, weekday Ma'ariv)", "ברוך יהוה לעולם אמן ואמן", 220),
    ("Amidah", "אדני שפתי תפתח ופי", 1500),
    ("Kedushah", "נקדש את שמך בעולם", 150),
    ("Kedushah", "נקדישך ונעריצך", 150),
    ("Kedushah", "נעריצך ונקדישך", 150),
    ("Avinu Malkeinu", "אבינו מלכנו חטאנו לפניך", 450),
    ("Vidui (Ashamnu)", "אשמנו בגדנו גזלנו", 120),
    ("Al Chet", "על חטא שחטאנו לפניך", 500),
    ("El Melekh Yoshev and the Thirteen Attributes", "אל מלך יושב על כסא רחמים", 120),
    ("Tachanun (Vayomer David)", "ויאמר דוד אל גד", 250),
    ("Nefilat Apayim", "רחום וחנון חטאתי לפניך", 200),
    ("Shomer Yisrael", "שומר ישראל שמור שארית ישראל", 120),
    ("Aleinu", "עלינו לשבח לאדון הכל", 150),
    ("Ein Keloheinu", "אין כאלהינו אין כאדונינו", 100),
    ("Lekhu Neranenah (Ps 95)", "לכו נרננה ליהוה", 120),
    ("Lekha Dodi", "לכה דודי לקראת כלה", 300),
    ("Anim Zemirot", "אנעים זמירות ושירים", 350),
    ("Adon Olam", "אדון עולם אשר מלך", 100),
    ("Yigdal", "יגדל אלהים חי", 100),
    ("Bedtime Shema (Hamapil)", "המפיל חבלי שנה", 600),
    ("Birkat HaMazon", "הזן את העולם כלו", 600),
    ("Zikhronot (Musaf of Rosh Hashanah)", "אתה זוכר מעשה עולם", 400),
    ("Shofarot (Musaf of Rosh Hashanah)", "אתה נגלית בענן כבודך", 400),
    ("Unetaneh Tokef", "ונתנה תקף קדשת היום", 350),
    ("Kol Nidrei", "כל נדרי ואסרי", 120),
    ("Korbanot: the incense (Pitum HaKetoret)", "פטום הקטרת", 400),
    ("Pirkei Avot", "משה קבל תורה מסיני", 20000),
    ("El Malei Rachamim", "אל מלא רחמים", 120),
    ("Hoshanot", "הושענא למענך אלהינו", 400),
)

# Landmarks place a hit only inside the prayer books' services. In selichot, kinnot,
# piyyutim and the other works, the section title says more (a day's selichot, a kinah).
LANDMARK_TYPES = frozenset({"Siddur", "Machzor", "Haggadah"})
JUST_BEFORE = 40         # words: a hit this close before a landmark is named by it ("just before Barchu")
# ... but only before the landmarks that open a part of the service; "just before" a verse
# that is also quoted in other chains (Ps 95) would name the wrong thing.
JUST_BEFORE_LABELS = frozenset({"Barchu", "Amidah", "Aleinu", "Kedushah", "Shema"})



@lru_cache(maxsize=1)
def _landmark_keys() -> Tuple[Tuple[str, Tuple[str, ...], int], ...]:
    return tuple((label, tuple(vm.tokenize(inc).keys), reach) for label, inc, reach in LANDMARKS)


def landmarks_in(prayer: vm.Prayer) -> List[Tuple[int, str, int]]:
    """(word index, label, reach) of every landmark opening in a prayer, in order."""
    if prayer.prayer_type not in LANDMARK_TYPES:
        return []
    keys = prayer.tokens.keys
    first = defaultdict(list)
    for label, lk, reach in _landmark_keys():
        first[lk[0]].append((label, lk, reach))
    out = []
    for i, k in enumerate(keys):
        for label, lk, reach in first.get(k, ()):
            if tuple(keys[i:i + len(lk)]) == lk:
                out.append((i, label, reach))
    return out


WHOLE_TEXT = "(the whole text)"


def short_path(prayer: vm.Prayer) -> str:
    """The Sefaria ref without its book title, the repeated leaf collapsed:
    'Siddur Ashkenaz, Weekday, Shacharit, Pesukei Dezimra, Hodu, Hodu' -> 'Weekday › Shacharit › Pesukei Dezimra › Hodu'."""
    ref = prayer.ref
    if ref.startswith(prayer.book):
        ref = ref[len(prayer.book):].lstrip(", ")
    parts = [p.strip() for p in ref.split(",") if p.strip()]
    if len(parts) >= 2 and parts[-1] == parts[-2]:
        parts = parts[:-1]
    return " › ".join(parts) or WHOLE_TEXT


def _norm(s: str) -> str:
    return re.sub(r"[^a-z]", "", s.lower().replace("the ", ""))


RITE_ORDER = ("Ashkenaz", "Sefard", "Chabad", "Edot_HaMizrach", "Universal")
RITE_NAME = {"Ashkenaz": "Ashkenaz", "Sefard": "Sefard (Hasidic)", "Chabad": "Chabad",
             "Edot_HaMizrach": "Edot HaMizrach", "Universal": "not tied to one rite"}


@dataclass
class Place:
    label: str
    hits: List[vm.Run] = field(default_factory=list)

    def rites(self) -> List[str]:
        seen = {h.prayer.nusach for h in self.hits}
        return [r for r in RITE_ORDER if r in seen] + sorted(seen - set(RITE_ORDER))


@dataclass
class Unit:
    verses: Tuple[int, int]            # first, last verse
    whole_psalm: bool
    places: "OrderedDict[str, Place]"

    @property
    def n_texts(self) -> int:
        return sum(len(p.hits) for p in self.places.values())

    def label(self, chapter: int) -> str:
        if self.whole_psalm:
            return f"Psalm {chapter}, whole or nearly whole"
        a, b = self.verses
        return f"v. {a}" if a == b else f"vv. {a}–{b}"


def place_of(hit: vm.Run, marks: List[Tuple[int, str, int]]) -> str:
    """The landmark the hit falls inside (the nearest opening before it, within that
    landmark's reach); else the section title, with the book named for works that are
    not prayer books ('Introduction' alone says nothing)."""
    after = [lab for i, lab, reach in marks
             if hit.lit_end <= i <= hit.lit_end + JUST_BEFORE and lab in JUST_BEFORE_LABELS]
    if after:            # a service's opening right after the hit outranks a landmark further back
        return f"just before {after[0]}"
    before = [lab for i, lab, reach in marks if i <= hit.lit_start and hit.lit_start - i <= reach]
    if before:
        return before[-1]
    path = short_path(hit.prayer)
    leaf = path.split(" › ")[-1] if path != WHOLE_TEXT else ""
    if hit.prayer.prayer_type in LANDMARK_TYPES and leaf:
        return leaf
    return f"{hit.prayer.book} › {leaf}" if leaf else hit.prayer.book


def build_units(chapter: int, hits: Optional[List[vm.Run]] = None, whole_share: float = 0.8) -> List[Unit]:
    """Group a psalm's hits into units (whole psalm / verse span), and each unit into places."""
    ps = vm.load_psalm(chapter)
    if hits is None:
        hits = vm.find_hits(chapter)
    real_verses = {v for v, (a, b) in ps.verse_range.items() if b - a >= 4}
    by_prayer = defaultdict(list)
    for h in hits:
        by_prayer[h.prayer.prayer_id].append(h)
    whole_prayers = set()
    for pid, hs in by_prayer.items():
        covered = {v for h in hs for v in h.verses_full}
        if real_verses and len(covered & real_verses) >= whole_share * len(real_verses):
            whole_prayers.add(pid)

    marks_cache: Dict[int, List[Tuple[int, str, int]]] = {}
    grouped: Dict[Tuple, List[Tuple[vm.Run, str]]] = defaultdict(list)
    seen_whole = set()
    for h in hits:
        pid = h.prayer.prayer_id
        if pid in whole_prayers:
            if pid in seen_whole:
                continue                                    # one row per prayer for the whole psalm
            seen_whole.add(pid)
            key = ("whole",)
        else:
            vs = list(h.verses_full) + list(h.verses_touched)
            if not vs:
                continue
            key = (min(vs), max(vs))
        if pid not in marks_cache:
            marks_cache[pid] = landmarks_in(h.prayer)
        grouped[key].append((h, place_of(h, marks_cache[pid])))

    out = []
    for key, rows in grouped.items():
        verses = (min(ps.verses), max(ps.verses)) if key == ("whole",) else key
        u = Unit(verses, key == ("whole",), OrderedDict())
        for label, members in cluster_places(rows):
            u.places[_norm(label) + f"#{len(u.places)}"] = Place(label, members)
        out.append(u)
    out.sort(key=lambda u: (0 if u.whole_psalm else 1, u.verses))
    for u in out:
        u.places = OrderedDict(sorted(u.places.items(), key=lambda kv: -len(kv[1].hits)))
    return out


CONTEXT_WORDS = 6        # words each side: two hits with the same neighbours are the same passage


def _context_keys(hit: vm.Run) -> List[Tuple]:
    """The words on BOTH sides of a hit. One side is not enough: the liturgy reuses verse chains
    (78:38 is followed by Ps 20:10 both in Yehi Chevod and before Barchu at Ma'ariv)."""
    keys = hit.prayer.tokens.keys
    if hit.lit_start >= CONTEXT_WORDS and hit.lit_end + CONTEXT_WORDS <= len(keys):
        return [("LR", tuple(keys[hit.lit_start - CONTEXT_WORDS:hit.lit_start]),
                 tuple(keys[hit.lit_end:hit.lit_end + CONTEXT_WORDS]))]
    return []


_LANDMARK_LABELS = frozenset(lab for lab, _, _ in LANDMARKS)
SIDE_OVERLAP = 3         # of CONTEXT_WORDS on each side, for two copies of a landmark to be one place


def _sides(hit: vm.Run) -> Tuple[frozenset, frozenset]:
    keys = hit.prayer.tokens.keys
    return (frozenset(keys[max(0, hit.lit_start - CONTEXT_WORDS):hit.lit_start]),
            frozenset(keys[hit.lit_end:hit.lit_end + CONTEXT_WORDS]))


def _near(a: Tuple[frozenset, frozenset], b: Tuple[frozenset, frozenset]) -> bool:
    return len(a[0] & b[0]) >= SIDE_OVERLAP and len(a[1] & b[1]) >= SIDE_OVERLAP


def cluster_places(rows: List[Tuple[vm.Run, str]]) -> List[Tuple[str, List[vm.Run]]]:
    """Group one unit's hits into PLACES: hits are one place if they have the same words on both
    sides (the same passage reprinted in another book or under another section title: a day's
    selichot, a machzor's copy of the daily Hodu), or the same landmark with nearly the same
    words on both sides (the same prayer in another rite).
    Named by the commonest landmark among the members, else their commonest label."""
    parent = list(range(len(rows)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    owner: Dict[Tuple, int] = {}
    for i, (h, label) in enumerate(rows):
        for k in _context_keys(h) + [("exact", label, h.prayer.book)]:
            if k in owner:
                parent[find(i)] = find(owner[k])
            else:
                owner[k] = i
    # The same landmark in another rite: its neighbours differ by a word or a rubric mark, so
    # join on the label only when BOTH sides largely agree (S395: on the label alone, a wrong
    # landmark merged the opening of Ma'ariv into Yehi Chevod).
    by_label: Dict[str, List[int]] = defaultdict(list)
    for i, (h, label) in enumerate(rows):
        if label in _LANDMARK_LABELS or label.startswith("just before "):
            by_label[label].append(i)
    for idx in by_label.values():
        sides = {i: _sides(rows[i][0]) for i in idx}
        for a_pos, a in enumerate(idx):
            for b in idx[a_pos + 1:]:
                if find(a) != find(b) and _near(sides[a], sides[b]):
                    parent[find(b)] = find(a)
    clusters: Dict[int, List[int]] = defaultdict(list)
    for i in range(len(rows)):
        clusters[find(i)].append(i)
    out = []
    for idx in clusters.values():
        labels = Counter(rows[i][1] for i in idx)
        land = [lab for lab, _ in labels.most_common() if lab in _LANDMARK_LABELS or lab.startswith("just before ")]
        label = land[0] if land else labels.most_common(1)[0][0]
        out.append((label, [rows[i][0] for i in idx]))
    return out


# ---------------------------------------------------------------------------
# What the model reads
# ---------------------------------------------------------------------------

LONG_QUOTE = 420         # chars: a longer quotation is shown by its beginning and end


def excerpt(hit: vm.Run, before: int = 320, after: int = 180) -> str:
    """The prayer text around a hit, the psalm's words marked ⟦…⟧, cut at spaces."""
    t = hit.prayer.text
    a, b = hit.char_span
    s = max(0, a - before)
    e = min(len(t), b + after)
    if s > 0:
        sp = t.find(" ", s)
        s = sp + 1 if 0 <= sp < a else s
    if e < len(t):
        sp = t.rfind(" ", b, e)
        e = sp if sp > b else e
    middle = t[a:b]
    if len(middle) > LONG_QUOTE:         # a whole psalm or a run of verses: its two ends are enough
        head = middle[:LONG_QUOTE // 2].rsplit(" ", 1)[0]
        tail = middle[-LONG_QUOTE // 3:].split(" ", 1)[-1]
        middle = f"{head} … {tail}"
    body = (t[s:a] + "⟦" + middle + "⟧" + t[b:e]).replace("\n", " ")
    return ("…" if s > 0 else "") + re.sub(r"\s+", " ", body).strip() + ("…" if e < len(t) else "")


def _position(hit: vm.Run) -> str:
    n = len(hit.prayer.tokens.keys)
    if hit.lit_start <= 3:
        return "opens the section"
    return f"word {hit.lit_start + 1:,} of {n:,}"


def _kind(hit: vm.Run, ps: vm.PsalmText) -> str:
    also = sorted({ps.verse_of[i] for i in hit.same_words_at})
    refrain = f" (the same words are also v. {', '.join(map(str, also))})" if also else ""
    if hit.verses_full:
        vs = hit.verses_full
        core = f"v. {vs[0]}" if len(vs) == 1 else f"vv. {vs[0]}–{vs[-1]}"
        return f"whole {core}" + (" + part of a neighbour" if hit.verses_touched else "") + refrain
    return "words: " + hit.prayer.text[slice(*hit.char_span)].replace("\n", " ") + refrain


def _rows(place: Place, ps: vm.PsalmText) -> List[str]:
    """One line per rite and book: the sections it was found in, and what was matched."""
    by_book: Dict[Tuple[str, str], List[vm.Run]] = defaultdict(list)
    for h in place.hits:
        by_book[(h.prayer.nusach, h.prayer.book)].append(h)
    order = lambda kv: (RITE_ORDER.index(kv[0][0]) if kv[0][0] in RITE_ORDER else 9, kv[0][1])  # noqa: E731
    lines = []
    for (rite, book), hs in sorted(by_book.items(), key=order):
        kinds = Counter(_kind(h, ps) for h in hs)
        common = kinds.most_common(1)[0][0]
        parts = []
        for h in sorted(hs, key=lambda h: (h.prayer.prayer_id, h.lit_start)):
            extra = [x for x in (("opens the section" if h.lit_start <= 3 else ""),
                                 ("" if _kind(h, ps) == common else _kind(h, ps)),
                                 (f"the wording follows {h.parallel}" if h.parallel and h.verses_full else "")) if x]
            parts.append(short_path(h.prayer) + (f" ({'; '.join(extra)})" if extra else ""))
        uniq = list(dict.fromkeys(parts))
        times = f" ×{len(parts)}" if len(uniq) == 1 and len(parts) > 1 else ""
        lines.append(f"- [{RITE_NAME.get(rite, rite)}] {book}: {'; '.join(uniq)}{times} — {common}")
    return lines


def _pick_excerpt(place: Place) -> vm.Run:
    """The excerpt that shows the place best: a siddur over a machzor, the longest quotation."""
    rank = {"Siddur": 0, "Machzor": 1, "Selichot": 2}
    return sorted(place.hits, key=lambda h: (rank.get(h.prayer.prayer_type, 3), -(h.matched + h.gaps)))[0]


def render_for_model(chapter: int, units: List[Unit], max_excerpts_per_unit: int = 40,
                     max_rows_per_place: int = 40) -> str:
    ps = vm.load_psalm(chapter)
    lines: List[str] = []
    for u in units:
        lines.append(f"## {u.label(chapter)} — {u.n_texts} text(s), {len(u.places)} place(s)")
        if not u.whole_psalm:
            a, b = u.verses
            for v in range(a, b + 1):
                if v in ps.verses:
                    lines.append(f"Psalm text, v. {v}: {ps.verses[v]}")
        for k, (nk, place) in enumerate(u.places.items()):
            lines.append(f"\n### Place: {place.label} — {len(place.hits)} text(s); rites: "
                         + ", ".join(RITE_NAME.get(r, r) for r in place.rites()))
            for line in _rows(place, ps)[:max_rows_per_place]:
                lines.append(line)
            if k < max_excerpts_per_unit:
                ex = _pick_excerpt(place)
                lines.append(f"Excerpt ({ex.prayer.book} › {short_path(ex.prayer)}, {_position(ex)}): {excerpt(ex)}")
        lines.append("")
    return "\n".join(lines)


def stats(units: List[Unit]) -> Dict[str, int]:
    return {"units": len(units), "places": sum(len(u.places) for u in units),
            "texts": sum(u.n_texts for u in units)}
