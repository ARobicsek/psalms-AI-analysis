"""
Rabbi Jonathan Sacks on each psalm, harvested from Sefaria: his liturgical commentary, aligned to the
psalm by the prayer-book paragraph it comments on, and the passages of his books that quote it.

Session 392 (designed in S391, `docs/plans/S391_SEFARIA_EVALUATION.md` §3.3). It replaces
`sacks_on_psalms.json` (Session 68): a 7 MB snapshot of raw API payloads, book excerpts only, each a
±1,000-character window cut mid-sentence, and NONE of his prayer-book commentary, which is the
closest thing to "Sacks on Psalms" that exists.

THREE SOURCES, in the order the bundle uses them:
  1. LITURGICAL: *Rabbi Sacks on Siddur*, *… on Rosh HaShana Mahzor*, *… on Yom Kippur Mahzor*,
     *The Jonathan Sacks Haggadah* (Koren, CC-BY-NC; personal use, the author's S391 call). Sefaria
     does NOT link these comments to Psalms. Each comment IS linked to the Koren prayer-book
     paragraph it sits beside, and that paragraph's Hebrew is the liturgy's own text, so the
     alignment is exact: the psalm verses found inside the paragraph (consonantal matching, the
     reception module's `locate`) are the verses the comment is about. S391's prototype matched
     the comment's Hebrew lemma against the psalms instead, and it matched a Ne'ilah piyyut to 76:8.
  2. BOOKS: `/api/links/Psalms.N` restricted to his works (from Sefaria's catalogue, not a list of
     titles), minus the Hebrew and Family editions, which repeat the English essays. Each passage is
     the linked paragraph, whole, with its neighbours while they fit (never a character window).
  3. SEARCH: a Hebrew phrase search of his English works for quotations Sefaria never linked
     (first and last four words of each verse). A hit counts only if the verse is then found in the
     paragraph's text.

The harvest is $0 and cached under data/sacks/ (gitignored). `liturgical.json` holds the whole
aligned liturgical commentary (one download, ~211 sections); `psalm_NNN.json` holds one psalm's items.
"""
from __future__ import annotations

import json
import logging
import re
import sqlite3
import time
from html import unescape
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import requests

from src.data_sources.sefaria_reception import SEFARIA, _get, locate, same_word, stem, tokens

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT_ROOT / "data" / "sacks"
DB_PATH = PROJECT_ROOT / "database" / "tanakh.db"
LITURGICAL_VERSION = 1
PSALM_CACHE_VERSION = 3   # 2: liturgical items carry whole_elsewhere; 3: Hebrew-only books kept (lang)

LITURGICAL_WORKS = ("Rabbi Sacks on Siddur", "Rabbi Sacks on Rosh HaShana Mahzor",
                    "Rabbi Sacks on Yom Kippur Mahzor", "The Jonathan Sacks Haggadah")
SACKS_CATEGORY_MARKERS = ("Jonathan Sacks",)           # catalogue paths: "…/Jonathan Sacks/…", "…/Rabbi Lord Jonathan Sacks"
DUPLICATE_EDITIONS = ("Hebrew Edition", "Family Edition")   # repeat the English essays
SEARCH_PATHS = ["Tanakh/Modern Commentary on Tanakh/Jonathan Sacks", "Jewish Thought/Modern/Rabbi Lord Jonathan Sacks"]


# ---------------------------------------------------------------------------------------------
# Text helpers (pure)
# ---------------------------------------------------------------------------------------------
def strip_footnotes(s: str) -> str:
    """Remove footnote markers and footnote bodies. A body is `<i class="footnote">` and can hold
    its own <i>…</i> (a book title), so it is matched by depth, not by the first </i>."""
    s = re.sub(r"<sup[^>]*>.*?</sup>", " ", s or "", flags=re.S)
    out, i = [], 0
    while True:
        j = s.find('<i class="footnote">', i)
        if j < 0:
            out.append(s[i:])
            return "".join(out)
        out.append(s[i:j])
        depth, k = 0, j
        for m in re.finditer(r"<i\b[^>]*>|</i>", s[j:]):
            depth += -1 if m.group(0) == "</i>" else 1
            if depth == 0:
                k = j + m.end()
                break
        else:
            k = len(s)
        i = k


def clean(s: str) -> str:
    """Sefaria HTML to plain text; <b>/<i> survive as Markdown so a lemma stays visible."""
    s = strip_footnotes(s)
    s = re.sub(r"</?(b|strong)>", "**", s)
    s = re.sub(r"</?(i|em)>", "*", s)
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = unescape(re.sub(r"<[^>]+>", " ", s))
    s = re.sub(r"\*\*\s*\*\*|\*\s+\*", " ", s)
    return re.sub(r"[ \t]+", " ", re.sub(r"\s*\n\s*", "\n", s)).strip()


def segments(x, path=()) -> Iterable[Tuple[Tuple[int, ...], str]]:
    """(1-based index path, text) for every non-empty leaf of a Sefaria text array."""
    if isinstance(x, list):
        for i, y in enumerate(x, 1):
            yield from segments(y, path + (i,))
    elif x:
        yield path, x


def split_ref(ref: str) -> Tuple[str, List[int]]:
    """'Work, Section 4' -> ('Work, Section', [4]); '… 4-6' -> (…, [4, 5, 6]); '… 3:2' -> (…, [3])."""
    m = re.match(r"^(.*\D)\s(\d+)(?::\d+)?(?:-(\d+)(?::\d+)?)?$", ref.strip())
    if not m:
        return ref, []
    a = int(m.group(2))
    b = int(m.group(3)) if m.group(3) else a
    return m.group(1).strip(), list(range(a, max(a, b) + 1))


def hebrew_lemma(comment: str, max_words: int = 12) -> str:
    """The Hebrew words a comment opens with (Koren prints the lemma first), or ''."""
    m = re.match(r"^\s*([֐-׿][֐-׿\s־׳״,.;:'\"()־]*)", comment or "")
    return " ".join(m.group(1).split()[:max_words]).strip(" ,.;:") if m else ""


# ---------------------------------------------------------------------------------------------
# Psalm alignment (pure, given the psalms' Hebrew)
# ---------------------------------------------------------------------------------------------
class PsalmAligner:
    """Which psalm verses a Hebrew passage contains. A verse counts when a run of at least
    `min_run(n)` of its consecutive words is found in the passage (all of it for a short verse)."""

    def __init__(self, psalms: Dict[int, List[str]]):
        self.verses: Dict[Tuple[int, int], List[str]] = {}
        self.index: Dict[Tuple[str, str, str], set] = {}
        for p, vs in psalms.items():
            for v, he in enumerate(vs, 1):
                toks = tokens(he)
                if not toks:
                    continue
                self.verses[(p, v)] = toks
                st = [stem(t) for t in toks]
                for i in range(len(st) - 2):
                    self.index.setdefault(tuple(st[i:i + 3]), set()).add((p, v))
        self.psalm_len = {p: len(vs) for p, vs in psalms.items()}

    @staticmethod
    def min_run(n: int) -> int:
        return n if n <= 4 else max(4, -(-6 * n // 10))     # 60%, at least 4 words

    def verses_in(self, hebrew: str) -> Dict[int, List[int]]:
        seg = tokens(hebrew)
        if len(seg) < 3:
            return {}
        st = [stem(t) for t in seg]
        cands = set()
        for i in range(len(st) - 2):
            cands |= self.index.get(tuple(st[i:i + 3]), set())
        found: Dict[int, List[int]] = {}
        for (p, v) in cands:
            vt = self.verses[(p, v)]
            if locate(vt, seg)[0] >= self.min_run(len(vt)):
                found.setdefault(p, []).append(v)
        return {p: sorted(vs) for p, vs in found.items()}


def load_psalms(db_path: Path = DB_PATH) -> Dict[int, List[str]]:
    con = sqlite3.connect(str(db_path))
    try:
        rows = con.execute("SELECT chapter, verse, hebrew FROM verses WHERE book_name = 'Psalms' "
                           "ORDER BY chapter, verse").fetchall()
    finally:
        con.close()
    out: Dict[int, List[str]] = {}
    for ch, v, he in rows:
        out.setdefault(ch, []).append(he or "")
    return out


def classify(verses: List[int], psalm_len: int, other_psalms: int) -> str:
    """How much of the psalm the commented paragraph holds: 'whole' (>= 60% of its verses),
    'passage' (2+ verses), or 'verse' (one verse, the paragraph built of other texts too)."""
    if psalm_len and len(verses) >= max(2, 0.6 * psalm_len):
        return "whole"
    return "passage" if len(verses) >= 2 else "verse"


# ---------------------------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------------------------
def _quote(ref: str) -> str:
    # '?' must be escaped: an essay titled "What Do We Sacrifice?" otherwise starts the query string (400)
    return requests.utils.quote(ref.replace(" ", "_"), safe="_.:,;'()-!")


def fetch_section(session, ref: str, lang: str) -> list:
    """The text array of one section in one language ([] when absent)."""
    d = _get(session, f"{SEFARIA}/api/v3/texts/{_quote(ref)}",
             params={"version": "hebrew" if lang == "he" else "english"}) or {}
    for v in d.get("versions", []):
        if v.get("language") == lang:
            t = v.get("text")
            return t if isinstance(t, list) else [t]
    return []


def harvest_liturgical(cache_dir: Path = CACHE_DIR, refresh: bool = False, session=None,
                       db_path: Path = DB_PATH, pause: float = 0.15) -> Dict:
    """Every non-empty liturgical comment, with the psalm verses its prayer-book paragraph holds."""
    path = Path(cache_dir) / "liturgical.json"
    if path.exists() and not refresh:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("version") == LITURGICAL_VERSION:
                return data
        except (OSError, ValueError):
            pass
    session = session or requests.Session()
    aligner = PsalmAligner(load_psalms(db_path))
    comments, failed = [], []
    for work in LITURGICAL_WORKS:
        links = _get(session, f"{SEFARIA}/api/links/{_quote(work)}", params={"with_text": 0}) or []
        by_comment: Dict[str, List[str]] = {}
        for l in links:
            by_comment.setdefault(l["anchorRef"], []).append(l["ref"])
        sections = sorted({split_ref(c)[0] for c in by_comment})
        base_cache: Dict[str, list] = {}
        for sec in sections:
            try:
                text = fetch_section(session, sec, "en")
            except Exception as e:
                failed.append(sec)
                logger.warning(f"[sacks] could not fetch {sec}: {e}")
                continue
            time.sleep(pause)
            for (i,), raw in ((p, s) for p, s in segments(text) if len(p) == 1):
                cref = f"{sec} {i}"
                body = clean(raw)
                if len(body) < 40:
                    continue
                psalms: Dict[str, List[int]] = {}
                base_refs = []
                for target in by_comment.get(cref, []):
                    tsec, nums = split_ref(target)
                    m = re.match(r"^Psalms (\d+)", target)
                    if m:                                            # the Haggadah links verses directly
                        p = int(m.group(1))
                        psalms.setdefault(str(p), [])
                        psalms[str(p)] = sorted(set(psalms[str(p)]) | set(nums or []))
                        continue
                    if any(target.startswith(b) for b in ("Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy")):
                        continue
                    base_refs.append(target)
                    if tsec not in base_cache:
                        try:
                            base_cache[tsec] = fetch_section(session, tsec, "he")
                        except Exception as e:
                            failed.append(tsec)
                            logger.warning(f"[sacks] could not fetch {tsec}: {e}")
                            base_cache[tsec] = []
                        time.sleep(pause)
                    paras = base_cache[tsec]
                    he = " ".join(clean(paras[n - 1]) if isinstance(paras[n - 1], str) else ""
                                  for n in nums if 0 < n <= len(paras))
                    for p, vs in aligner.verses_in(he).items():
                        psalms[str(p)] = sorted(set(psalms.get(str(p), [])) | set(vs))
                comments.append({"work": work, "ref": cref, "section": sec[len(work):].strip(" ,") or work,
                                 "base_refs": base_refs, "lemma": hebrew_lemma(body), "text": body,
                                 "psalms": psalms})
    data = {"version": LITURGICAL_VERSION, "fetched": time.strftime("%Y-%m-%d"),
            "comments": comments, "failed": failed}
    if not failed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    else:
        logger.warning(f"[sacks] {len(failed)} section(s) failed; liturgical index NOT cached, so the next run retries")
    return data


# ---------------------------------------------------------------------------------------------
# Books and search (per psalm)
# ---------------------------------------------------------------------------------------------
ITEM_TARGET_CHARS = 1600   # a book passage: the linked paragraph, plus neighbours while under this
ITEM_HARD_MAX = 3200       # a single paragraph longer than this is cut at a sentence, marked […]


def book_titles(toc: list) -> List[str]:
    """Sacks's books in Sefaria's catalogue: every title under a '…Jonathan Sacks' category,
    minus the liturgical commentary (aligned separately) and the duplicate editions."""
    out = []

    def walk(nodes, path):
        for n in nodes:
            if "contents" in n:
                walk(n["contents"], path + [n.get("category", "")])
            elif "title" in n:
                p = "/".join(path)
                t = n["title"]
                if (any(m in p for m in SACKS_CATEGORY_MARKERS) and t not in LITURGICAL_WORKS
                        and not any(d in t for d in DUPLICATE_EDITIONS)):
                    out.append(t)
    walk(toc, [])
    return sorted(set(out))


def compose_passage(paras: List[str], n: int, target: int = ITEM_TARGET_CHARS,
                    hard_max: int = ITEM_HARD_MAX) -> Tuple[str, Tuple[int, int]]:
    """Paragraph n (1-based) whole, then its neighbours (nearest first, before then after) while
    the passage stays under `target`. Returns (text, (first, last) paragraph numbers)."""
    texts = [clean(p) if isinstance(p, str) else "" for p in paras]
    if not 0 < n <= len(texts) or not texts[n - 1]:
        return "", (n, n)
    body = texts[n - 1]
    if len(body) > hard_max:
        cut = body.rfind(". ", 0, hard_max)
        return body[: cut + 1 if cut > hard_max // 2 else hard_max].rstrip() + " […]", (n, n)
    first = last = n
    for step in range(1, 4):
        for j in (n - step, n + step):
            if 0 < j <= len(texts) and texts[j - 1]:
                lo, hi = min(first, j), max(last, j)
                if hi - lo == (last - first) + 1 and sum(len(texts[k - 1]) for k in range(lo, hi + 1)) <= target:
                    first, last = lo, hi
    # a trailing neighbour that ends on a colon announces a quotation we do not have
    while last > n and texts[last - 1].rstrip().endswith(":"):
        last -= 1
    return "\n\n".join(t for t in texts[first - 1:last] if t), (first, last)


def shingles(text: str, n: int = 5) -> set:
    w = re.findall(r"[a-z]+", (text or "").lower())
    return {" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}


def overlap(a: str, b: str) -> float:
    sa, sb = shingles(a), shingles(b)
    return len(sa & sb) / min(len(sa), len(sb)) if sa and sb else 0.0


def _section_versions(session, sec: str) -> Dict[str, list]:
    d = _get(session, f"{SEFARIA}/api/v3/texts/{_quote(sec)}",
             params=[("version", "english"), ("version", "hebrew")]) or {}
    out = {}
    for v in d.get("versions", []):
        if v.get("language") in ("en", "he") and v["language"] not in out:
            t = v.get("text")
            out[v["language"]] = t if isinstance(t, list) else [t]
    return out


_FINAL_FORMS = str.maketrans("כמנפצ", "ךםןףץ")


def query_word(token: str) -> str:
    """`tokens()` folds final letters into medial ones for matching; Sefaria's search needs them back
    (a query with אלכ for אלך finds nothing)."""
    return token[:-1] + token[-1].translate(_FINAL_FORMS) if len(token) > 1 else token


def search_quotations(session, psalm_tokens: List[List[str]], pause: float = 0.1) -> Dict[str, set]:
    """ref -> verses, from a Hebrew phrase search of his books (first and last 4 words of each verse).
    The hits are in the Hebrew translations of his English books, under the same refs."""
    found: Dict[str, set] = {}
    for v, toks in enumerate(psalm_tokens, 1):
        if len(toks) < 4:
            continue
        words = [query_word(t) for t in toks]
        for q in {" ".join(words[:4]), " ".join(words[-4:])}:
            body = {"query": q, "type": "text", "field": "naive_lemmatizer", "size": 50, "slop": 0,
                    "source_proj": ["ref", "path", "lang"], "filters": SEARCH_PATHS,
                    "filter_fields": ["path"] * len(SEARCH_PATHS)}
            for attempt in range(3):
                try:
                    r = session.post(f"{SEFARIA}/api/search-wrapper", json=body, timeout=60)
                    r.raise_for_status()
                    for h in r.json().get("hits", {}).get("hits", []):
                        ref = h.get("_source", {}).get("ref")
                        if ref:
                            found.setdefault(ref, set()).add(v)
                    break
                except (requests.RequestException, ValueError):
                    if attempt == 2:
                        raise
                    time.sleep(2 ** (attempt + 1))
            time.sleep(pause)
    return found


def _work_of(ref: str, titles: Iterable[str]) -> Optional[str]:
    return next((t for t in sorted(titles, key=len, reverse=True) if ref.startswith(t)), None)


def harvest_psalm(psalm: int, cache_dir: Path = CACHE_DIR, refresh: bool = False, session=None,
                  db_path: Path = DB_PATH, search: bool = True, pause: float = 0.1) -> Dict:
    """One psalm's Sacks items (liturgical comments, linked book passages, search finds), cached."""
    path = Path(cache_dir) / f"psalm_{psalm:03d}.json"
    if path.exists() and not refresh:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("version") == PSALM_CACHE_VERSION and (data.get("searched") or not search):
                return data
        except (OSError, ValueError):
            pass
    session = session or requests.Session()
    lit = harvest_liturgical(cache_dir=cache_dir, session=session, db_path=db_path)
    psalms = load_psalms(db_path)
    ptoks = [tokens(h) for h in psalms.get(psalm, [])]
    n_verses = len(ptoks)
    liturgical = [{**{k: c[k] for k in ("work", "ref", "section", "lemma", "text")},
                   "verses": c["psalms"][str(psalm)],
                   # the other psalms its prayer-book paragraph holds in full (then it is about them)
                   "whole_elsewhere": sorted(int(q) for q, vs in c["psalms"].items() if q != str(psalm)
                                             and classify(vs, len(psalms.get(int(q), [])), 0) == "whole")}
                  for c in lit["comments"] if str(psalm) in c["psalms"]]

    works_path = Path(cache_dir) / "works.json"
    try:
        titles = json.loads(works_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        titles = book_titles(_get(session, f"{SEFARIA}/api/index") or [])
        works_path.parent.mkdir(parents=True, exist_ok=True)
        works_path.write_text(json.dumps(titles, ensure_ascii=False, indent=0), encoding="utf-8")

    targets: Dict[str, set] = {}          # paragraph ref -> verses
    sources: Dict[str, str] = {}          # paragraph ref -> 'link' | 'search'
    links = _get(session, f"{SEFARIA}/api/links/Psalms.{psalm}", params={"with_text": 0}) or []
    for l in links:
        if l.get("index_title") not in titles:
            continue
        m = re.match(rf"^Psalms {psalm}:(\d+)(?:-(\d+))?", l.get("anchorRef", ""))
        if not m:
            continue
        a, b = int(m.group(1)), int(m.group(2) or m.group(1))
        vs = {v for v in range(a, b + 1) if v <= n_verses}
        if vs:
            targets.setdefault(l["ref"], set()).update(vs)
            sources[l["ref"]] = "link"
    failed = []
    searched = False
    if search:
        try:
            for ref, vs in search_quotations(session, ptoks, pause=pause).items():
                if _work_of(ref, titles):
                    targets.setdefault(ref, set()).update(vs)
                    sources.setdefault(ref, "search")
            searched = True
        except Exception as e:
            failed.append("search")
            logger.warning(f"[sacks] Psalm {psalm}: phrase search failed ({e}); linked passages only")

    sec_cache: Dict[str, Dict[str, list]] = {}
    books = []
    for ref in sorted(targets):
        sec, nums = split_ref(ref)
        if not nums:
            continue
        if sec not in sec_cache:
            try:
                sec_cache[sec] = _section_versions(session, sec)
            except Exception as e:
                failed.append(ref)
                logger.warning(f"[sacks] could not fetch {sec}: {e}")
                sec_cache[sec] = {}
            time.sleep(pause)
        en, he = sec_cache[sec].get("en") or [], sec_cache[sec].get("he") or []
        n = nums[0]
        verses = sorted(targets[ref])
        if sources[ref] == "search":       # a search hit counts only if the verse is in the paragraph
            para_he = clean(he[n - 1]) if 0 < n <= len(he) and isinstance(he[n - 1], str) else ""
            seg = tokens(para_he)
            verses = [v for v in verses if locate(ptoks[v - 1], seg)[0] >= min(4, len(ptoks[v - 1]))]
            if not verses:
                continue
        # Sefaria holds most of his Jewish-thought books only in Maggid's Hebrew translation; the
        # English is used whenever it exists, and a Hebrew passage is labelled as a translation.
        lang = "en"
        text, span = compose_passage(en, n)
        if not text:
            lang = "he"
            text, span = compose_passage(he, n)
        if not text:
            continue
        work = _work_of(sec, titles) or sec
        books.append({"work": work, "ref": ref, "section": sec[len(work):].strip(" ,"),
                      "paragraph": n, "span": list(span), "verses": verses, "source": sources[ref],
                      "lang": lang, "text": text})
    data = {"version": PSALM_CACHE_VERSION, "psalm": psalm, "fetched": time.strftime("%Y-%m-%d"),
            "verses": n_verses, "liturgical": liturgical, "books": books, "searched": searched,
            "failed": failed}
    if not failed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    else:
        logger.warning(f"[sacks] Psalm {psalm}: {len(failed)} fetch(es) failed; NOT cached, so the next run retries")
    return data
