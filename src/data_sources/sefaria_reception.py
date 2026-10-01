"""
How the Talmud, the midrashim and later Jewish readers used each verse of a psalm: a research-bundle
section built from Sefaria's links, selected by FIXED RULES, with no model in the loop.

Session 391. The eleven commentators read a psalm verse by verse; this is the verse IN USE: quoted
in the Talmud, preached in the midrash, returned to by Hasidic and musar writers. The writer used
to know it only from Torah Temimah and its own memory, and the memory slipped (the Ps 27 guide
called Vayikra Rabbah 21:4 "later pietistic works").

SCOPE (the author's call): Talmud, Mishnah, Tosefta, the midrashim, Second Temple (Philo,
Josephus), Hasidut, Musar, halakhah. NOT Kabbalah, NOT Jewish thought, NOT the commentaries we
already fetch, and NOT the midrash anthologies (Yalkut Shimoni, Ein Yaakov, Sekhel Tov, Lekach Tov,
Otzar Midrashim), which repeat the classical midrashim.

WHY RULES, NOT A MODEL (the author): a selection model would decide what the guide is about before
the writer does. These rules select on the KIND of source and its AGE, never on how interesting a
passage looks, and the section carries no summaries. A first version ranked passages by content
(verse words reused outside the quotation, interpretive cue words) and DROPPED the three best Ps 77
finds: Sanhedrin 19b (lost to a per-verse cap), Berakhot 59a's thunder (its reused word, שבגלגל,
is two prefixes deep) and the Hasidic line on 77:11 (which paraphrases rather than repeats). Word
overlap is now used only to drop an obvious proof-text. Record: archive/S391_sefaria_probe/.

THE RULES (`select`):
  1. Locate or drop: the verse's words must be found in the passage (consonantal skeletons, two
     prefix letters, common suffixes, divine-name spellings). This also drops Sefaria's mis-links
     (Ps 77 has links to "77:49" and "77:51", which are Ps 78's).
  2. A passage linked to several verses is ONE item with a verse range.
  3. Parallel tellings (4-gram overlap >= 0.25 around the quotation) collapse to the earliest;
     the others are named, not printed.
  4. Tier A, always kept: Talmud, Mishnah, Tosefta with a known early date; Midrash Tehillim on
     its own psalm.
  5. Tier B, classical midrash and Second Temple: per verse earliest first, at most 2, filled
     round-robin; a bare proof-text (after שנאמר/דכתיב…, no verse word reused, passage over 600
     characters) is dropped.
  6. Tier C, later readers (Hasidut, Musar, halakhah, undated works): a verse that three or more
     DIFFERENT later works return to keeps its earliest telling, with the others named; then one
     single per four verses that visibly works the verse.
  7. Budget: PER_VERSE_CHARS per verse, never more than SECTION_MAX_CHARS. Fill order: A, the
     first B of each verse, C convergence leads, the second B of each verse, C singles.

Cache: data/sefaria_cache/reception/psalm_NNN.json (gitignored with the rest of data/): the links,
the text of every in-scope passage, and the psalm's own Hebrew. A re-run, and the selection, cost
nothing and touch no network. Delete the file to refetch.
"""
from __future__ import annotations

import json
import logging
import math
import re
import time
from collections import defaultdict
from html import unescape
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT_ROOT / "data" / "sefaria_cache" / "reception"
SEFARIA = "https://www.sefaria.org"
SECTION_HEADER = "## Rabbinic and Later Reception"
CACHE_VERSION = 2   # 2: entities unescaped

SCOPE = {"Talmud", "Mishnah", "Tosefta", "Midrash", "Second Temple", "Chasidut", "Musar", "Halakhah"}
ANTHOLOGIES = {"Yalkut Shimoni on Torah", "Yalkut Shimoni on Nach", "Ein Yaakov",
               "Ein Yaakov (Glick Edition)", "Midrash Sekhel Tov", "Midrash Lekach Tov", "Otzar Midrashim"}

PER_VERSE_CHARS = 1400          # the author, S391
SECTION_MAX_CHARS = 40000       # Ps 119 would otherwise get 176 x 1,400 = 246K
PER_VERSE_B = 2
LATER_SINGLES_PER_VERSES = 4    # one tier-C single per four verses
CONVERGENCE_WORKS = 3
PARALLEL_JACCARD = 0.25
EARLY_RABBINIC_MAX_DATE = 1000  # tier A needs a known date up to here
BARE_PROOF_MIN_CHARS = 600
HE_WORDS_BEFORE, HE_WORDS_AFTER = 30, 60
EN_WHOLE_MAX = 900
UNDATED = 9999

# ---------------------------------------------------------------------------------------------
# Hebrew matching (pure)
# ---------------------------------------------------------------------------------------------
_FINALS = str.maketrans("ךםןףץ", "כמנפצ")
_DIVINE = {"יהוה", "ה", "יי", "ד", "השם", "אלקים", "אלוקים", "אלהים"}
_STOP = {"כי", "אשר", "את", "על", "אל", "לא", "כל", "גם", "אף", "עם", "סלה", "למנצח", "מזמור",
         "לדוד", "לאסף", "שיר", "בו", "לו", "הוא", "זה", "אני", "אתה", "מי", "אם", "עד", "ולא", "וכל"}
_PROOF_BEFORE = {"שנאמר", "דכתיב", "כדכתיב", "וכתיב", "שכתוב", "ככתוב", "כמש", "כמשה", "ההד",
                 "ואומר", "שנא", "כמו", "וכן", "דאמר", "כמאמר", "שנאמ", "דכתי", "כתיב", "ונאמר", "וכתוב"}
_CUE_AFTER = {"זה", "זו", "אלו", "אלה", "מהו", "מאי", "מלמד", "כלומר", "רל", "כיצד", "משל", "כביכול",
              "אלא", "פירוש", "פי", "דהיינו", "היינו", "רוצה", "ביאור", "הכוונה", "רמז", "אמר", "אמרו"}
_SUFFIXES = ("ים", "ות", "יו", "יה", "הם", "כם", "נו", "ה", "ו", "י", "ך", "ת", "מ", "נ")


def word_tokens(word: str) -> List[str]:
    """The Hebrew tokens in one whitespace-delimited word (0 for punctuation, 2 across a maqaf)."""
    w = re.sub(r"[֑-ׇ]", "", word).replace("־", " ").replace("׀", " ")
    w = re.sub(r"[\"'׳״]", "", w)
    return [t.translate(_FINALS) for t in re.sub(r"[^א-ת ]", " ", w).split()]


def tokens(text: str) -> List[str]:
    return [t for w in (text or "").split() for t in word_tokens(w)]


def skeleton(w: str) -> str:
    """Consonants without matres lectionis (rabbinic plene vs biblical defective spelling)."""
    w = "יהוה" if w in _DIVINE else w
    return w[0] + re.sub("[וי]", "", w[1:]) if len(w) > 2 else w


def stem(w: str) -> str:
    w = skeleton(w)
    for _ in range(2):
        if len(w) > 3 and w[0] in "והבלמשכד":
            w = w[1:]
    for sfx in _SUFFIXES:
        if len(w) > 3 and w.endswith(sfx):
            return w[: -len(sfx)]
    return w


def same_word(a: str, b: str) -> bool:
    return skeleton(a) == skeleton(b) or (len(stem(a)) >= 2 and stem(a) == stem(b))


def locate(verse_tokens: List[str], seg_tokens: List[str]) -> Tuple[int, int, int]:
    """(length, start, end) of the longest run of consecutive verse words found in the passage."""
    best = (0, 0, 0)
    for i in range(len(seg_tokens)):
        for j in range(len(verse_tokens)):
            k = 0
            while (i + k < len(seg_tokens) and j + k < len(verse_tokens)
                   and same_word(seg_tokens[i + k], verse_tokens[j + k])):
                k += 1
            if k > best[0]:
                best = (k, i, i + k)
    return best


# ---------------------------------------------------------------------------------------------
# Analysis and selection (pure)
# ---------------------------------------------------------------------------------------------
def analyse(link: Dict, text: Dict[str, str], psalm_hebrew: List[str], psalm: int) -> Optional[Dict]:
    """One linked passage -> an item for `select`, or None when it cannot be placed (a verse outside
    the psalm, no Hebrew, or the verse's words not found in it)."""
    try:
        verse = int(link["anchorRef"].split(":")[-1].split("-")[0])
    except (KeyError, ValueError):
        return None
    he = (text or {}).get("he") or ""
    if not he or not 1 <= verse <= len(psalm_hebrew):
        return None
    words = he.split()
    tok_word = [wi for wi, w in enumerate(words) for _ in word_tokens(w)]
    seg = [t for w in words for t in word_tokens(w)]
    vt = tokens(psalm_hebrew[verse - 1])
    k, s, e = locate(vt, seg)
    if not (k >= 2 or (k == 1 and len(vt) <= 2)):
        return None
    content = {skeleton(w) for w in vt if w not in _STOP and len(w) >= 3 and skeleton(w) != "יהוה"}
    reused = {c for idx, w in enumerate(seg) if not s <= idx < e for c in content if same_word(w, c)}
    proof = bool(set(seg[max(0, s - 3):s]) & _PROOF_BEFORE)
    cue = bool(set(seg[e:e + 4]) & _CUE_AFTER)
    a = max(0, tok_word[s] - HE_WORDS_BEFORE)
    b = min(len(words), tok_word[e - 1] + 1 + HE_WORDS_AFTER)
    for j in range(b, min(len(words), b + 15)):   # finish the sentence if it ends soon
        if words[j - 1].endswith((".", ":", "׃")):
            b = j
            break
    he_win = ("… " if a else "") + " ".join(words[a:b]) + (" …" if b < len(words) else "")
    en = (text or {}).get("en") or ""
    if len(en) > EN_WHOLE_MAX:
        m = re.search(rf"\b{psalm}:{verse}\b", en)
        c = m.start() if m else 0
        lo, hi = max(0, c - 350), c + 550
        en = ("… " if lo else "") + en[lo:hi].strip() + (" …" if hi < len(en) else "")
    date, date_label = composition_date(link.get("compDate"))
    window = [skeleton(x) for x in seg[max(0, s - 25):e + 40]]
    return {
        "ref": link["ref"], "work": link.get("index_title") or link["ref"], "category": link.get("category"),
        "date": date, "date_label": date_label, "verses": {verse},
        "reused": len(reused), "proof": proof, "cue": cue, "he_len": len(he),
        "own": (link.get("index_title") == "Midrash Tehillim" and link["ref"].startswith(f"Midrash Tehillim {psalm}:")),
        "he": he_win, "en": en, "shingles": {tuple(window[i:i + 4]) for i in range(len(window) - 3)},
        "parallels": [], "also": [],
    }


def composition_date(comp) -> Tuple[int, str]:
    """(sort key, label) from Sefaria's compDate. A range is ordered by its MIDPOINT and shown
    whole: Sefaria dates Tanchuma Buber [150, 750], and "c. 150" ranked it before the Mekhilta."""
    nums = [int(x) for x in (comp or []) if isinstance(x, (int, float))]
    if not nums:
        return UNDATED, ""
    lo, hi = min(nums), max(nums)
    fmt = lambda y: f"{-y} BCE" if y < 0 else str(y)
    return (lo + hi) // 2, (fmt(lo) if lo == hi else f"{fmt(lo)}–{fmt(hi)}")


def tier(item: Dict) -> str:
    if item["category"] in ("Talmud", "Mishnah", "Tosefta") and item["date"] <= EARLY_RABBINIC_MAX_DATE:
        return "A"
    if item["own"]:
        return "A"
    if item["category"] in ("Midrash", "Second Temple") and item["date"] < UNDATED:
        return "B"
    return "C"


def _bare_proof(it: Dict) -> bool:
    return it["proof"] and it["reused"] == 0 and not it["cue"] and it["he_len"] > BARE_PROOF_MIN_CHARS


def _size(it: Dict) -> int:
    return len(it["he"]) + len(it["en"])


def merge(items: List[Dict]) -> List[Dict]:
    """Rules 2 and 3: one item per passage, then parallel tellings collapse to the earliest."""
    byref: Dict[str, Dict] = {}
    for it in items:
        if it["ref"] in byref:
            byref[it["ref"]]["verses"] |= it["verses"]
        else:
            byref[it["ref"]] = it
    heads: List[Dict] = []
    for it in sorted(byref.values(), key=lambda x: (x["date"], -x["reused"], x["ref"])):
        for h in heads:
            union = it["shingles"] | h["shingles"]
            if (h["verses"] & it["verses"] and union
                    and len(it["shingles"] & h["shingles"]) / len(union) >= PARALLEL_JACCARD):
                h["parallels"].append(it["ref"])
                break
        else:
            heads.append(it)
    return heads


def select(items: List[Dict], n_verses: int, per_verse_chars: int = PER_VERSE_CHARS,
           max_chars: int = SECTION_MAX_CHARS) -> Tuple[List[Dict], List[Dict]]:
    """Rules 4-7. Returns (kept, dropped)."""
    heads = merge(items)
    for h in heads:
        h["tier"] = tier(h)
    A = [h for h in heads if h["tier"] == "A"]
    B = [h for h in heads if h["tier"] == "B" and not _bare_proof(h)]
    perv: Dict[int, List[Dict]] = defaultdict(list)
    for h in sorted(B, key=lambda x: (x["date"], -x["reused"], x["ref"])):
        perv[min(h["verses"])].append(h)
    b_rounds = [[hs[r] for v, hs in sorted(perv.items()) if len(hs) > r] for r in range(PER_VERSE_B)]
    C = [h for h in heads if h["tier"] == "C"]
    by_verse: Dict[int, List[Dict]] = defaultdict(list)
    for h in sorted(C, key=lambda x: (x["date"], x["ref"])):
        by_verse[min(h["verses"])].append(h)
    leads = []
    for v, hs in sorted(by_verse.items()):
        if len({h["work"] for h in hs}) >= CONVERGENCE_WORKS:
            lead = hs[0]
            lead["also"] = sorted({h["work"] for h in hs[1:]} - {lead["work"]})
            leads.append(lead)
    singles = []
    allowance = math.ceil(n_verses / LATER_SINGLES_PER_VERSES)
    for h in sorted(C, key=lambda x: (-(x["reused"] + 3 * x["cue"]), x["date"], x["ref"])):
        if len(leads) + len(singles) >= allowance:
            break
        if h not in leads and (h["reused"] >= 2 or h["cue"]) and not _bare_proof(h):
            singles.append(h)
    budget = min(per_verse_chars * n_verses, max_chars)
    kept, used = [], 0
    for h in A + b_rounds[0] + leads + sum(b_rounds[1:], []) + singles:
        if h not in kept and used + _size(h) <= budget:
            kept.append(h)
            used += _size(h)
    dropped = [h for h in heads if h not in kept]
    return kept, dropped


# ---------------------------------------------------------------------------------------------
# Rendering (pure)
# ---------------------------------------------------------------------------------------------
def _era(item: Dict) -> str:
    return f"c. {item['date_label']}" if item.get("date_label") else ""


def _verse_label(verses) -> str:
    vs = sorted(verses)
    return f"Verse {vs[0]}" if len(vs) == 1 else (
        f"Verses {vs[0]}–{vs[-1]}" if vs == list(range(vs[0], vs[-1] + 1)) else "Verses " + ", ".join(map(str, vs)))


def render(psalm: int, kept: List[Dict], n_candidates: int) -> str:
    """The bundle section. Neutral by design: what the passage is, where and when, and its words;
    no summary of what it means or why it matters."""
    if not kept:
        return ""
    lines = [SECTION_HEADER, "",
             f"Passages from the Talmud, the midrashim and later Jewish writers that quote Psalm {psalm}, "
             f"from Sefaria's links ({len(kept)} of {n_candidates} located passages). Chosen by fixed rules, "
             "not by judgment: every Talmud, Mishnah and Tosefta passage and the psalm's own Midrash Tehillim; "
             "the earliest classical midrashim for each verse; and, where three or more later works return "
             "to one verse, the earliest of them. Each is cut around the quotation. Parallel tellings are "
             "named, not repeated. English is Sefaria's translation where one exists.", ""]
    for it in sorted(kept, key=lambda x: (min(x["verses"]), x["date"], x["ref"])):
        era = _era(it)
        lines.append(f"### {_verse_label(it['verses'])} — {it['ref']} ({it['category']}{', ' + era if era else ''})")
        if it["parallels"]:
            lines.append(f"*Also told in: {'; '.join(it['parallels'])}.*")
        if it["also"]:
            lines.append(f"*Later works that also return to this verse: {', '.join(it['also'])}.*")
        lines.append(f"**Hebrew:** {it['he']}")
        if it["en"]:
            lines.append(f"**English:** {it['en']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# Sections the reception section goes BEFORE (the first one present), so it sits after the
# commentaries and the liturgy, where a reader of the bundle expects the verse's afterlife.
_INSERT_BEFORE = ("## Rabbi Jonathan Sacks on Psalm", "## Related Psalms", "## Deep Web Research",
                  "## Cross-Cultural Literary Echoes", "## Research Summary")


def insert_section(bundle: str, section: str) -> str:
    """The bundle with `section` added (replacing an existing reception section)."""
    if not section:
        return bundle
    if SECTION_HEADER in bundle:
        start = bundle.index(SECTION_HEADER)
        nxt = re.compile(r"^## ", re.M).search(bundle, start + len(SECTION_HEADER))
        bundle = bundle[:start] + (bundle[nxt.start():] if nxt else "")
    body = section.rstrip() + "\n\n---\n\n"
    for marker in _INSERT_BEFORE:
        m = re.search(rf"^{re.escape(marker)}", bundle, re.M)
        if m:
            return bundle[:m.start()] + body + bundle[m.start():]
    return bundle.rstrip() + "\n\n" + body


# ---------------------------------------------------------------------------------------------
# Network + cache
# ---------------------------------------------------------------------------------------------
def _get(session: requests.Session, url: str, params=None, attempts: int = 4) -> Optional[dict]:
    for attempt in range(1, attempts + 1):
        try:
            r = session.get(url, params=params, timeout=60)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError) as e:
            if attempt == attempts:
                raise
            logger.warning(f"[reception] Sefaria request failed ({e}); retry {attempt}/{attempts - 1}: {url}")
            time.sleep(2 ** attempt)


def _flatten(x) -> str:
    return " ".join(_flatten(i) for i in x) if isinstance(x, list) else (x or "")


def _clean(s: str) -> str:
    s = re.sub(r'<sup[^>]*>.*?</sup>|<i class="footnote">.*?</i>', " ", s or "", flags=re.S)
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def _text(session, ref: str) -> Dict[str, str]:
    d = _get(session, f"{SEFARIA}/api/v3/texts/" + requests.utils.quote(ref.replace(" ", "_"), safe="_.:,;'()-"),
             params=[("version", "hebrew"), ("version", "english")]) or {}
    out = {}
    for v in d.get("versions", []):
        if v.get("language") in ("he", "en") and v["language"] not in out:
            out[v["language"]] = _clean(_flatten(v.get("text")))
    return out


def harvest(psalm: int, cache_dir: Path = CACHE_DIR, refresh: bool = False,
            session: Optional[requests.Session] = None, pause: float = 0.1) -> Dict:
    """Links, passage texts and the psalm's Hebrew, from the cache or Sefaria (then cached)."""
    path = Path(cache_dir) / f"psalm_{psalm:03d}.json"
    if path.exists() and not refresh:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("version") == CACHE_VERSION:
                return data
        except (OSError, ValueError):
            pass
    session = session or requests.Session()
    links = _get(session, f"{SEFARIA}/api/links/Psalms.{psalm}", params={"with_text": 0}) or []
    keep = [{k: l.get(k) for k in ("ref", "anchorRef", "category", "index_title", "compDate")}
            for l in links if l.get("category") in SCOPE and l.get("index_title") not in ANTHOLOGIES]
    texts, failed = {}, []
    for l in keep:
        if l["ref"] in texts:
            continue
        try:
            texts[l["ref"]] = _text(session, l["ref"])
        except Exception as e:   # one lost passage must not sink the section; it is named
            failed.append(l["ref"])
            logger.warning(f"[reception] could not fetch {l['ref']}: {e}")
        time.sleep(pause)
    ps = _get(session, f"{SEFARIA}/api/v3/texts/Psalms.{psalm}", params=[("version", "hebrew|Tanach with Text Only")]) or {}
    psalm_he = [_clean(x) for x in (ps.get("versions") or [{}])[0].get("text", [])]
    data = {"version": CACHE_VERSION, "psalm": psalm, "fetched": time.strftime("%Y-%m-%d"),
            "links": keep, "texts": texts, "failed": failed, "psalm_hebrew": psalm_he}
    if not failed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    else:
        logger.warning(f"[reception] Psalm {psalm}: {len(failed)} passage(s) failed; NOT cached, so the next run retries")
    return data


def build_section(psalm: int, cache_dir: Path = CACHE_DIR, refresh: bool = False,
                  per_verse_chars: int = PER_VERSE_CHARS, max_chars: int = SECTION_MAX_CHARS,
                  data: Optional[Dict] = None) -> Tuple[str, Dict]:
    """(markdown section, stats). Stats: candidates, located, kept, chars, and the kept refs."""
    data = data or harvest(psalm, cache_dir=cache_dir, refresh=refresh)
    psalm_he = data["psalm_hebrew"]
    items = [a for l in data["links"]
             if (a := analyse(l, data["texts"].get(l["ref"]), psalm_he, psalm)) is not None]
    kept, dropped = select(items, len(psalm_he), per_verse_chars=per_verse_chars, max_chars=max_chars)
    section = render(psalm, kept, len({i["ref"] for i in items}))
    stats = {"links_in_scope": len(data["links"]), "located": len({i["ref"] for i in items}),
             "kept": len(kept), "chars": len(section), "failed": data.get("failed", []),
             "kept_refs": [(sorted(k["verses"]), k["tier"], k["ref"]) for k in kept]}
    logger.info(f"[reception] Psalm {psalm}: {stats['links_in_scope']} in-scope links, {stats['located']} located, "
                f"{stats['kept']} kept, {stats['chars']:,} chars")
    return section, stats
