"""
Fact Checker — evidence-backed verification of a finished guide (Session 385).

WHY THIS EXISTS. The copy editor (gpt-5.4) corrects facts from memory, and that
is how the pipeline's worst copy-edit errors happened: Session 368's Terra run
invented a Hebrew reading (Ps 40:17's waw) and "corrected" a true claim about
Herbert; Session 383's gpt-5.4 run turned the writer's CORRECT "the only other
occurrence of the form רִשְׁפֵי is Song 8:6" into a FALSE "the only other plural
use" (Ps 78:48 has לָרְשָׁפִים). A sterner prompt rule made it worse
(docs/plans/COPY_EDITOR_TERRA_FINDINGS.md). The "forest" writer prompt also
asks Opus to bring Herodotus, Byron and Assyrian inscriptions from its own
knowledge, so more of the guide rests on claims no pipeline source vouches for.

The durable answer is ground truth, not a rule: this pass lists every checkable
claim, verifies each against evidence, and returns verdicts WITH the evidence.
The copy editor is then told to correct facts ONLY where this report says
`contradicted` (see `format_copy_editor_prompt`). Its system prompt is untouched.

Models (Session 386, staged for cost; the note above DIVINE_NAMES_NOTE has the
measurements), all on the OpenAI Responses API, a different family from the writer
so they do not share the writer's false memories:
  stage 1  gpt-6-luna, research bundle + $0 lookups, no web: every claim the
           materials, the Bible and the commentators can settle;
  stage 2  gpt-6-sol + web search: only the claims stage 1 hands on as needs_web;
  stage 3  gpt-6-sol: re-judges every stage-1 `contradicted` before it can reach
           the copy editor.
$0 lookup tools:
  - get_verse(ref)          tanakh.db when present, else Sefaria;
  - get_commentary(c, ref)  the research bundle first, else Sefaria;
  - search_tanakh(hebrew)   occurrence lists for "only here" claims
                            (tanakh.db when present, else Sefaria's search);
  - get_text(ref)           any Sefaria text (Talmud, midrash, siddur).
Biblical-quotation WORDING is not checked here: verify_citations does it at $0.

Stage 1 checks the guide in section-aligned CHUNKS, each call carrying the whole
research bundle as a cached prefix (bundle + instructions first, excerpt last).

Pure functions (chunking, ref parsing, bundle lookup, JSON validation, report
and prompt formatting) are unit-tested in tests/test_fact_checker.py.
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import requests

from src.utils.cost_tracker import price_tokens
from src.utils.openai_usage import split_input_tokens, split_output_tokens

try:  # the project's .env (OPENAI_API_KEY) wherever the checker is imported from
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except ImportError:  # pragma: no cover
    pass

# Stage models (Session 386; see the note above DIVINE_NAMES_NOTE).
DEFAULT_MODEL = "gpt-6-sol"           # stage 1, local evidence (no web)
DEFAULT_EFFORT = "high"
DEFAULT_WEB_MODEL = "gpt-6-luna"         # stage 2a: GATHERS sources with OpenAI web search (no verdicts)
DEFAULT_WEB_EFFORT = "medium"
DEFAULT_WEB_JUDGE_MODEL = "gpt-6-sol"    # stage 2b: judges the claims from the gathered quotes
DEFAULT_REVIEW_MODEL = None           # stage 3: only when stage 1 runs on a weaker model (luna)
DEFAULT_REVIEW_EFFORT = "high"
WEB_CONTEXT_SIZE = "low"              # search content is ~all of the web stage's input tokens
# Session 397: OpenAI's Flex tier is the SAME model at Batch prices, half of standard on every
# token class (gpt-6-sol: $1 / $0.10 cached / $1.25 cache write / $5), for slower answers and
# an occasional 429 "Resource Unavailable" that is not billed (`_create` retries, then falls
# back to the standard tier). A pipeline step does not need the speed. None = standard.
DEFAULT_SERVICE_TIER = "flex"
WEB_BATCH = 8
REVIEW_BATCH = 12
VERDICTS = ("supported", "contradicted", "unverifiable")
CLAIM_TYPES = (
    "biblical_quotation",
    "commentator_reading",      # what a commentator says, and the SHAPE of his argument
    "rabbinic_or_liturgical",
    "literary_quotation",
    "ancient_source_or_inscription",
    "count_or_uniqueness",      # "only here", "the only other", "twice"
    "grammar_or_textual",       # a form, a dagesh, a ketiv/qere, what the LXX reads
    "date_name_or_history",
    "other",
)

# OpenAI pricing page (developers.openai.com/api/docs/pricing, read 2026-09-29):
# "Web search (all models) | $10.00 / 1k calls + Search content tokens billed at
# model rates." The content tokens arrive inside the response's input_tokens, so
# they are already priced by price_tokens(); only the per-call fee is added here.
WEB_SEARCH_USD_PER_CALL = 10.00 / 1000
# Gemini API pricing page (ai.google.dev/gemini-api/docs/pricing, read 2026-09-28), Gemini
# 3.x: "5,000 free search requests per month (shared across all Gemini 3.x models), then
# $14 per 1,000 requests", and "Retrieved context (text or images) provided by Grounding
# with Google Search is not charged as input tokens." That second sentence is the whole
# reason the web stage moved to Gemini in Session 386: on OpenAI the search content
# (~7.9K tokens a search, billed as input) was ~half of the web stage's cost. Queries are
# counted and reported; cost_usd counts them as FREE (inside the monthly allowance), and
# `gemini_search_cost_if_paid` says what they would cost past it.
GEMINI_SEARCH_USD_PER_QUERY_PAID = 14.00 / 1000

SEFARIA = "https://www.sefaria.org"
REPORT_MARKER = "FACT-CHECK REPORT (evidence-based"

# Chunk target. Big enough that a verse's note is never split, small enough that
# the model attends to every claim in it.
DEFAULT_CHUNK_CHARS = 13000
MAX_TOOL_ROUNDS = 24


# =============================================================================
# Guide preparation (pure)
# =============================================================================

def checkable_text(markdown: str) -> str:
    """The parts of a guide a reader reads as prose: the introduction (with its
    liturgical section) and the verse commentary. Drops the `## Psalm N` text
    block (it IS the source) and everything from `## Methodological` on."""
    text = markdown.replace("\r\n", "\n")
    m = re.search(r"^## Methodological.*$", text, re.M)
    if m:
        text = text[:m.start()]
    # `## Psalm N` block: from its header to the next `## ` header.
    text = re.sub(r"^## Psalm \d+\s*\n.*?(?=^## )", "", text, flags=re.M | re.S)
    return text.strip() + "\n"


_VERSE_HEADER = re.compile(r"^\*\*Verses?\s+\d+(?:\s*[–\-]\s*\d+)?\*\*\s*$")


def _section_label(line: str, current: str) -> Optional[str]:
    s = line.strip()
    if s.startswith("---LITURGICAL-SECTION-START"):
        return "Liturgy"
    if _VERSE_HEADER.match(s):
        return s.strip("*").strip()
    m = re.match(r"^#{2,4}\s+(.+)$", s)
    if m:
        h = m.group(1).strip()
        if h.startswith("Verse-by-Verse"):
            return "Verse commentary"
        if h == "Introduction" or current.startswith("Verse"):
            return h
        return f"Introduction › {h}"
    return None


def split_guide_for_checking(text: str, max_chars: int = DEFAULT_CHUNK_CHARS) -> List[Dict[str, str]]:
    """Split a guide into chunks at section boundaries (## headers, the liturgy
    marker, **Verse N** headers), packing whole sections up to `max_chars`.
    A single section longer than max_chars becomes its own chunk (never cut
    mid-section). Returns [{'label': 'Introduction … Verse 3', 'text': ...}]."""
    sections: List[Tuple[str, List[str]]] = []
    label = "Introduction"
    buf: List[str] = []
    for line in text.split("\n"):
        new = _section_label(line, label)
        if new is not None and buf and any(x.strip() for x in buf):
            sections.append((label, buf))
            buf = []
        if new is not None:
            label = new
        buf.append(line)
    if any(x.strip() for x in buf):
        sections.append((label, buf))

    chunks: List[Dict[str, str]] = []
    cur_labels: List[str] = []
    cur_text = ""
    for lab, lines in sections:
        body = "\n".join(lines).strip("\n") + "\n"
        if cur_text and len(cur_text) + len(body) > max_chars:
            chunks.append(_mk_chunk(cur_labels, cur_text))
            cur_labels, cur_text = [], ""
        cur_labels.append(lab)
        cur_text += body + "\n"
    if cur_text.strip():
        chunks.append(_mk_chunk(cur_labels, cur_text))
    return chunks


def _mk_chunk(labels: List[str], text: str) -> Dict[str, str]:
    first, last = labels[0], labels[-1]
    return {"label": first if first == last else f"{first} … {last}", "text": text.strip() + "\n"}


# =============================================================================
# References and lookups
# =============================================================================

# Sefaria spells the books the way tanakh.db does, so one resolver serves both.
def parse_ref(ref: str) -> Optional[Tuple[str, int, int, Optional[int]]]:
    """'Ps 78:48' / 'Psalms 78:48' / 'Song 8:6' / '2 Kgs 19:35' / 'Ps 76:5-6' →
    (book, chapter, verse, end_verse). None when the book is unknown."""
    from src.utils.scripture_verifier import _resolve_book_name

    m = re.match(r"^\s*(.+?)\.?\s+(\d+)\s*[:.]\s*(\d+)(?:\s*[–\-]\s*(\d+))?\s*$", ref or "")
    if not m:
        return None
    book = _resolve_book_name(m.group(1).strip())
    if book is None:
        # Sefaria-style names the resolver does not list ("I Kings", "Song of Songs").
        raw = m.group(1).strip()
        book = {"Canticles": "Song of Songs", "Song of Solomon": "Song of Songs"}.get(raw, None)
        if book is None and re.match(r"^(I|II)\s+(Samuel|Kings|Chronicles)$", raw):
            book = raw
        if book is None:
            return None
    end = int(m.group(4)) if m.group(4) else None
    return book, int(m.group(2)), int(m.group(3)), end


def _strip_html(s: str) -> str:
    s = re.sub(r"<br\s*/?>", " ", s)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _flatten(x) -> str:
    if isinstance(x, list):
        return " ".join(_flatten(i) for i in x if i)
    return _strip_html(str(x or ""))


def _sefaria_text(tref: str, versions=("hebrew", "english"), timeout: int = 30) -> Dict[str, str]:
    qs = "&".join(f"version={v}" for v in versions)
    url = f"{SEFARIA}/api/v3/texts/{requests.utils.quote(tref.replace(' ', '_'), safe='_.:,-')}?{qs}"
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    d = r.json()
    out = {"ref": d.get("ref", tref), "url": f"{SEFARIA}/{tref.replace(' ', '_')}"}
    for v in d.get("versions", []):
        lang = v.get("language")
        key = {"he": "hebrew", "en": "english"}.get(lang, lang)
        if key and key not in out:
            out[key] = _flatten(v.get("text"))
            out[f"{key}_version"] = v.get("versionTitle", "")
    return out


def usable_db(db_path: Optional[Path]) -> bool:
    """True only for a tanakh.db that exists AND holds verses. Opened read-only:
    TanakhDatabase's constructor CREATES an empty schema at a missing path, and
    an empty db must never answer a count ("zero occurrences") — Session 385
    lost a run to exactly that when a test collection left one behind."""
    if not db_path or not Path(db_path).exists():
        return False
    try:
        con = _ro_connect(db_path)
        try:
            return con.execute("SELECT COUNT(*) FROM verses").fetchone()[0] > 0
        finally:
            con.close()
    except sqlite3.Error:
        return False


def _ro_connect(db_path: Path) -> sqlite3.Connection:
    # as_uri() gives file:///C:/... on Windows and file:///home/... elsewhere.
    return sqlite3.connect(Path(db_path).resolve().as_uri() + "?mode=ro", uri=True)


def _db_rows(db_path: Path, sql: str, params=()) -> list:
    con = _ro_connect(db_path)
    try:
        return con.execute(sql, params).fetchall()
    finally:
        con.close()


def lookup_verse(ref: str, db_path: Optional[Path] = None) -> Dict[str, str]:
    parsed = parse_ref(ref)
    if not parsed:
        return {"error": f"could not parse reference {ref!r}; use e.g. 'Psalms 78:48'"}
    book, ch, v, end = parsed
    tref = f"{book} {ch}:{v}" + (f"-{end}" if end else "")
    if usable_db(db_path):
        rows = _db_rows(db_path, "SELECT hebrew, english FROM verses WHERE book_name=? AND chapter=? "
                        "AND verse BETWEEN ? AND ? ORDER BY verse", (book, ch, v, end or v))
        if rows:
            return {"ref": tref, "source": "tanakh.db",
                    "hebrew": " ".join(r[0] for r in rows), "english": " ".join(r[1] for r in rows)}
    try:
        out = _sefaria_text(tref)
        out["source"] = "Sefaria"
        return out
    except Exception as e:  # network / 404
        return {"error": f"lookup failed for {tref}: {e}"}


def bundle_commentary(bundle: str, commentator: str, ref: str) -> Optional[str]:
    """The research bundle's entry for `commentator` on `ref`, from its
    `### 76:11 — Rashi` sections. Only the verse part of `ref` is used, since
    the bundle covers one psalm. None if absent."""
    if not bundle:
        return None
    m = re.search(r"(\d+)\s*[:.]\s*(\d+)\s*$", ref or "")
    if not m:
        return None
    ch, v = m.group(1), m.group(2)
    name = re.escape(commentator.strip())
    pat = re.compile(rf"^### {ch}:{v} — {name}\s*$\n(.*?)(?=^### |^## |\Z)", re.M | re.S | re.I)
    hit = pat.search(bundle)
    return hit.group(1).strip() if hit else None


_SEFARIA_COMMENTARY_NAMES = {
    "rashi": "Rashi", "ibn ezra": "Ibn Ezra", "radak": "Radak", "malbim": "Malbim",
    "meiri": "Meiri", "metzudat david": "Metzudat David", "metzudat zion": "Metzudat Zion",
    "sforno": "Sforno", "minchat shai": "Minchat Shai", "torah temimah": "Torah Temimah",
}


def lookup_commentary(commentator: str, ref: str, bundle: str = "") -> Dict[str, str]:
    found = bundle_commentary(bundle, commentator, ref)
    if found:
        return {"commentator": commentator, "ref": ref, "source": "research bundle", "text": found}
    parsed = parse_ref(ref)
    if not parsed:
        return {"error": f"could not parse reference {ref!r}"}
    book, ch, v, _ = parsed
    name = _SEFARIA_COMMENTARY_NAMES.get(commentator.strip().lower(), commentator.strip())
    tref = f"{name} on {book} {ch}:{v}"
    try:
        out = _sefaria_text(tref)
        if not (out.get("hebrew") or out.get("english")):
            return {"error": f"Sefaria has no text for {tref}"}
        out["source"] = "Sefaria"
        return out
    except requests.HTTPError as e:
        if getattr(e.response, "status_code", None) == 404:
            # Session 388: usually a verse the commentator passes over, which is itself evidence.
            return {"error": f"no entry: neither the research bundle nor Sefaria has {name} on {book} "
                             f"{ch}:{v}; he most likely does not comment on this verse"}
        return {"error": f"lookup failed for {tref}: {e}"}
    except Exception as e:
        return {"error": f"lookup failed for {tref}: {e}"}


_HEB_MARKS = re.compile(r"[֑-ׇ]")


def _consonants(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    s = _HEB_MARKS.sub(lambda m: "" if m.group(0) not in "־" else " ", s)
    return re.sub(r"[^א-ת ]", "", s).strip()


def search_tanakh(query: str, db_path: Optional[Path] = None, limit: int = 60) -> Dict:
    """Verses containing a Hebrew word/phrase. tanakh.db (consonantal substring,
    exact) when present; else Sefaria's search, which is prefix/suffix-tolerant
    (naive lemmatizer) — so confirm the exact FORM with get_verse."""
    q = _consonants(query)
    if not q:
        return {"error": "query must be Hebrew"}
    if usable_db(db_path):
        rows = _db_rows(db_path, "SELECT book_name, chapter, verse, hebrew FROM verses")
        hits = [f"{b} {c}:{v}" for b, c, v, h in rows if q in _consonants(h)]
        return {"query": query, "source": "tanakh.db (consonantal substring)",
                "count": len(hits), "refs": hits[:limit]}
    body = {"query": q, "type": "text", "field": "naive_lemmatizer", "filters": ["Tanakh"],
            "filter_fields": ["path"], "size": 200, "source_proj": True, "slop": 0}
    try:
        r = requests.post(f"{SEFARIA}/api/search-wrapper", json=body, timeout=30)
        r.raise_for_status()
        refs = sorted({h["_source"].get("ref") for h in r.json()["hits"]["hits"]},
                      key=lambda x: x or "")
        return {"query": query, "source": "Sefaria search (naive lemmatizer: tolerant of "
                "prefixes/suffixes/plural; confirm forms with get_verse)",
                "count": len(refs), "refs": refs[:limit]}
    except Exception as e:
        return {"error": f"search failed: {e}"}


# =============================================================================
# Model output: validation and formatting (pure)
# =============================================================================

def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s or "")).strip()


def _strip_md(s: str) -> str:
    return re.sub(r"[*_`]", "", s)


def sentence_in_guide(sentence: str, guide: str) -> bool:
    a, b = _strip_md(_norm_ws(sentence)), _strip_md(_norm_ws(guide))
    if not a:
        return False
    if a in b:
        return True
    # Tolerate curly/straight quote drift and a trimmed end.
    tr = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})
    a2, b2 = a.translate(tr), b.translate(tr)
    return a2 in b2 or (len(a2) > 60 and a2[:60] in b2)


def expand_sentence(sentence: str, guide: str) -> str:
    """The full guide sentence that `sentence` opens (pure). Stage 1 writes only the FIRST SIX
    WORDS of a supported claim's sentence, and a claim it hands to the web keeps that stub
    through the judge, so a contradicted record could reach the copy editor as "In 1773, on
    the edge of" (Ps 77, Session 387). Returns `sentence` unchanged when it is already whole
    or cannot be found."""
    s = (sentence or "").strip()
    if not s or re.search(r"[.!?:\"”’)]\s*$", s):
        return sentence
    g = (guide or "").replace("\r\n", "\n")
    i = g.find(s)
    if i < 0:
        return sentence
    m = re.search(r"[.!?:](?=[\"”’)]?(?:\s|$))[\"”’)]?|\n\s*\n", g[i + len(s):])
    end = i + len(s) + (m.end() if m else len(g) - i - len(s))
    full = " ".join(g[i:end].split())
    return full if len(full) <= 1200 else sentence


def validate_records(raw: List[Dict], guide: str = "", allowed: Tuple[str, ...] = VERDICTS) -> List[Dict]:
    """Normalise model records and enforce the evidence rule: a `contradicted`
    verdict with no quoted evidence is DOWNGRADED to `unverifiable` and marked,
    never passed to the copy editor as a licence to change the text."""
    out = []
    for i, r in enumerate(raw or [], 1):
        rec = {
            "id": r.get("id") or f"C{i}",
            "location": (r.get("location") or "").strip(),
            "sentence": (r.get("sentence") or "").strip(),
            "claim": (r.get("claim") or "").strip(),
            "claim_type": r.get("claim_type") if r.get("claim_type") in CLAIM_TYPES else "other",
            "verdict": (r.get("verdict") or "").strip().lower(),
            "evidence": [e for e in (r.get("evidence") or [])
                         if isinstance(e, dict) and ((e.get("quote") or "").strip() or (e.get("url") or "").strip())],
            "explanation": (r.get("explanation") or "").strip(),
            "suggested_fix": (r.get("suggested_fix") or None),
            "notes": [],
        }
        if rec["verdict"] not in allowed:
            rec["notes"].append(f"invalid verdict {rec['verdict']!r} → unverifiable")
            rec["verdict"] = "unverifiable"
        if rec["verdict"] == "contradicted" and not any((e.get("quote") or "").strip() for e in rec["evidence"]):
            rec["notes"].append("contradicted without quoted evidence → downgraded to unverifiable")
            rec["verdict"] = "unverifiable"
        if guide:
            rec["sentence_found"] = sentence_in_guide(rec["sentence"], guide)
        out.append(rec)
    return out


def parse_fact_check_json(text: str) -> List[Dict]:
    """Records from the model's JSON (tolerates a ```json fence or leading prose)."""
    t = (text or "").strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if fence:
        t = fence.group(1).strip()
    if not t.startswith(("{", "[")):
        start = min([i for i in (t.find("{"), t.find("[")) if i >= 0] or [0])
        t = t[start:]
    data = json.loads(t)
    if isinstance(data, dict):
        data = data.get("claims", [])
    return list(data)


def salvage_records(text: str) -> List[Dict]:
    """The complete records at the head of a TRUNCATED `{"claims": [ ... ` response (pure).
    Session 387: Ps 77's verses 10-15 chunk ended mid-string at char 21,448, and the
    json.loads error took the whole fact check down with it."""
    t = text or ""
    m = re.search(r'"claims"\s*:\s*\[', t)
    i = m.end() if m else (t.find("[") + 1 if "[" in t else 0)
    dec, out = json.JSONDecoder(), []
    while True:
        while i < len(t) and t[i] in " \t\r\n,":
            i += 1
        if i >= len(t) or t[i] != "{":
            break
        try:
            obj, i = dec.raw_decode(t, i)
        except json.JSONDecodeError:
            break
        if isinstance(obj, dict):
            out.append(obj)
    return out


def verdict_counts(records: List[Dict]) -> Dict[str, int]:
    c = {v: 0 for v in VERDICTS}
    for r in records:
        c[r["verdict"]] = c.get(r["verdict"], 0) + 1
    return c


def _evidence_md(ev: List[Dict]) -> List[str]:
    lines = []
    for e in ev:
        src = (e.get("source") or "").strip()
        q = (e.get("quote") or "").strip()
        url = (e.get("url") or "").strip()
        bit = f"   - *{src}*" if src else "   -"
        if q:
            bit += f": “{q}”"
        if url:
            bit += f" <{url}>"
        lines.append(bit)
    return lines


def format_report_markdown(records: List[Dict], meta: Optional[Dict] = None) -> str:
    meta = meta or {}
    c = verdict_counts(records)
    out = [f"# Fact-check report — Psalm {meta.get('psalm', '?')}", ""]
    if meta:
        out.append(
            f"Model: {meta.get('model', '?')} (effort {meta.get('effort', '?')}). "
            f"Claims: {len(records)} — {c['supported']} supported, {c['contradicted']} contradicted, "
            f"{c['unverifiable']} unverifiable. Web searches: {meta.get('web_searches', 0)}. "
            f"Tool calls: {meta.get('function_calls', 0)}. Cost: ${meta.get('cost_usd', 0):.4f}."
        )
        out.append("")
    for verdict, title in (("contradicted", "Contradicted"), ("unverifiable", "Unverifiable"),
                           ("supported", "Supported")):
        group = [r for r in records if r["verdict"] == verdict]
        out += [f"## {title} ({len(group)})", ""]
        for r in group:
            out.append(f"**{r['id']}** · {r['location']} · `{r['claim_type']}`")
            out.append(f"> {r['sentence']}")
            if r.get("claim"):
                out.append(f"- Claim: {r['claim']}")
            if r.get("explanation"):
                out.append(f"- {r['explanation']}")
            if r["evidence"]:
                out.append("- Evidence:")
                out += _evidence_md(r["evidence"])
            if verdict == "contradicted" and r.get("suggested_fix"):
                out.append(f"- Suggested fix: {r['suggested_fix']}")
            for n in r.get("notes", []):
                out.append(f"- ⚠ {n}")
            if r.get("sentence_found") is False:
                out.append("- ⚠ sentence not found verbatim in the guide")
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def _clip(s: str, n: int) -> str:
    s = _norm_ws(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def format_copy_editor_prompt(records: List[Dict]) -> str:
    """The supplementary block the copy editor receives. It carries the ONLY
    licence for factual corrections; the copy editor's system prompt is not
    touched (a test pins it byte-for-byte). Empty string for no records."""
    if not records:
        return ""
    contra = [r for r in records if r["verdict"] == "contradicted"]
    unver = [r for r in records if r["verdict"] == "unverifiable"]
    supp = [r for r in records if r["verdict"] == "supported"]
    lines = [
        "",
        f"{REPORT_MARKER} — this governs every factual correction you make):",
        "",
        "A separate fact-check pass listed the checkable claims in this guide and verified each",
        "one against sources: the research materials, the biblical text, the commentators' own",
        "texts, and web search. For FACTUAL claims, follow these rules instead of your own memory:",
        "",
        "1. Correct a factual claim ONLY where an item below is marked CONTRADICTED, and only as",
        "   far as its quoted evidence supports. Make the smallest change that makes the sentence",
        "   true; keep the author's wording, figures and argument around it. The suggested fix is",
        "   a starting point, not a script. Prefix each such change-log entry with [FACT-CHECK].",
        "2. Do NOT correct any other factual claim from memory. If you doubt a claim that is not",
        "   listed as contradicted, leave the text unchanged and list the doubt at the end of your",
        "   ## Changes section under a line reading `### UNVERIFIED` (one line each: location,",
        "   the claim, why you doubt it). Those lines are notes for the author, not edits.",
        "3. Leave claims marked SUPPORTED or UNVERIFIABLE alone as matters of fact.",
        "",
        "Your other categories (style of argument, clarity, Hebrew script, glosses, banned phrases)",
        "are unaffected.",
        "",
    ]
    lines.append(f"CONTRADICTED ({len(contra)}):" if contra else "CONTRADICTED: none.")
    for i, r in enumerate(contra, 1):
        lines.append(f"{i}. {r['location']}: \"{_clip(r['sentence'], 400)}\"")
        if r.get("claim"):
            lines.append(f"   Claim: {r['claim']}")
        if r.get("explanation"):
            lines.append(f"   Finding: {r['explanation']}")
        for e in r["evidence"]:
            q = _clip(e.get("quote") or "", 700)
            src = e.get("source") or ""
            url = f" ({e['url']})" if e.get("url") else ""
            lines.append(f"   Evidence — {src}{url}: \"{q}\"" if q else f"   Evidence — {src}{url}")
        if r.get("suggested_fix"):
            lines.append(f"   Suggested fix: {r['suggested_fix']}")
        lines.append("")
    if supp:
        lines.append(f"SUPPORTED ({len(supp)}) — verified; do not change these facts:")
        for r in supp:
            lines.append(f"- {r['location']}: {_clip(r.get('claim') or r['sentence'], 160)}")
        lines.append("")
    if unver:
        lines.append(f"UNVERIFIABLE ({len(unver)}) — no evidence either way; do not change on factual grounds:")
        for r in unver:
            lines.append(f"- {r['location']}: {_clip(r.get('claim') or r['sentence'], 160)}")
        lines.append("")
    return "\n".join(lines)


# =============================================================================
# The model call
# =============================================================================

RECORD_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "location": {"type": "string"},
                    "sentence": {"type": "string"},
                    "claim": {"type": "string"},
                    "claim_type": {"type": "string", "enum": list(CLAIM_TYPES)},
                    "verdict": {"type": "string", "enum": list(VERDICTS)},
                    "evidence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "source": {"type": "string"},
                                "quote": {"type": "string"},
                                "url": {"type": ["string", "null"]},
                            },
                            "required": ["source", "quote", "url"],
                        },
                    },
                    "explanation": {"type": "string"},
                    "suggested_fix": {"type": ["string", "null"]},
                },
                "required": ["location", "sentence", "claim", "claim_type", "verdict",
                             "evidence", "explanation", "suggested_fix"],
            },
        }
    },
    "required": ["claims"],
}


# Session 386: the call section is STAGED for cost. Session 385's single pass ran
# gpt-6-sol with web search over every claim, with the ~130K-token research bundle
# replayed on every tool round: $4.87 on Ps 76 (Probe A), 51% of it uncached input,
# 16% web-search fees. Measured on the same guide, gpt-6-luna ran the SAME pass for
# $0.59 and matched Sol on the claims the local evidence settles, but missed nearly
# every claim that needed the web and over-flagged spelling technicalities. So:
#   stage 1  LOCAL   gpt-6-luna, bundle + $0 lookups, NO web. Settles what the
#                    materials, the Bible and the commentators can settle; hands the
#                    rest on as `needs_web`.
#   stage 2  WEB     gpt-6-sol + web search, ONLY the needs_web claims, no bundle.
#   stage 3  REVIEW  gpt-6-sol, $0 lookups, re-judges every stage-1 `contradicted`
#                    before the copy editor may act on it (Luna's false alarms).
# Biblical-quotation WORDING is not the checker's job at all: the pipeline's $0
# verify_citations checks it against tanakh.db (divine-name aware).

DIVINE_NAMES_NOTE = """### The guide's spelling of divine names (never an error)
The guide writes divine names in full or in a reverential form, in its own prose AND inside
quotations, and may mix the two (the writer spells names in full; quoted commentators often
abbreviate them): ה׳ for the Tetragrammaton, אֱלֹקִים / אֱלֹקֵי (etc.) for אֱלֹהִים, קֵל for אֵל, צְבָקוֹת for
צְבָאוֹת, שַׁקַּי for שַׁדַּי, אֱלוֹקַּ for אֱלוֹהַּ. Treat each as identical to the Masoretic form. Never
list, flag or "correct" either spelling."""

MATERIALITY_NOTE = """### What counts as contradicted
Contradicted means a careful reader would come away believing something false: a wrong source,
verse, speaker, date, count or reading; a commentator's argument split, merged, reversed or
misattributed; a quotation whose words are wrong. It does NOT cover technicalities that leave the
point true: a root or consonantal skeleton given without its vowel letters (ו, י) or suffixes when
the sentence is not about spelling; a fair English rendering worded differently from a published
one; a paraphrase presented as a paraphrase; a broad but defensible description ("the past-tense
story"). A paraphrase of a commentator is fine; a change in the SHAPE of his argument (which is
his reading, which his proof, which his alternative, what he gives as his reason) is not."""

LOCAL_INSTRUCTIONS = """## YOUR TASK: FACT-CHECK AN EXCERPT OF THE GUIDE

You are the fact-checker for a study guide on Psalm {psalm}, written for an educated general
audience by an AI writer who worked from a research bundle AND from its own memory. Find the
checkable factual claims in the EXCERPT below and verify each against evidence. You do not edit
prose, judge style, or assess interpretations.

### What to list (every one; skip common knowledge)
Go through the excerpt sentence by sentence. Most errors hide in confident, specific sentences:
who said something, in which source, in what order, how many times.
- QUOTATIONS other than biblical verses: rabbinic texts, commentators, liturgy, poems,
  inscriptions, classical authors. Check the wording AND the attribution (who; which work,
  section, line).
- Do NOT list the WORDING of a quoted biblical verse: that is verified separately against the
  Masoretic text. Do list claims ABOUT verses: what a verse says or means literally, which
  verse says it, which word or form it uses, where else a word occurs.
- WHAT A COMMENTATOR SAYS, AND THE SHAPE OF HIS ARGUMENT: his reading, his proof text, whether
  he gives one reading or two, which is his main reading and which his alternative, and
  whether the guide splits, merges, reorders or drops his readings. Read the commentator's
  whole entry before judging. Presenting one reading's two steps as two alternatives, or
  dropping his stated alternative while describing "his readings", is a misrepresentation
  (contradicted).
- COUNTS AND UNIQUENESS: "only here", "the only other occurrence", "twice", "N times". Verify
  with search_tanakh, then confirm the exact forms with get_verse. Say exactly what word, form
  or lemma you counted: "the only other occurrence of the FORM X" and "the only other PLURAL
  use of the NOUN" are different claims.
- TEXTUAL AND GRAMMATICAL FACTS stated as fact: a form, a dagesh, a ketiv/qere, what the LXX
  or Targum reads, a psalm heading.
- DATES, NAMES, PLACES, NUMBERS, historical events, titles and dates of works.
Do NOT list interpretations, figures of speech, the guide's own arguments, or claims about what
the poem "does". For a flagged conjecture ("perhaps", "may"), list only the facts it rests on.

{divine_names}

### How to verify
0. ABOVE, you already have the commentators' full entries on the verses this excerpt covers
   (on every verse, for the introduction) and the text of every biblical verse the excerpt
   cites. Use them first; do not look up what is already there. Every lookup costs time and
   money: make one only when a specific claim needs it.
1. get_commentary(commentator, ref) fetches an entry that is not above. search_research(query) searches the writer's research bundle (lexicons, concordance,
   liturgical notes, the literary-echoes dossier) for a word or phrase. The bundle's
   SUMMARIES of liturgy, literature and history were written by other AI agents and can be
   wrong: they show what the writer relied on, not what is true. For those claims, verify
   against the text itself (get_text) or hand the claim on (step 3).
2. get_verse(ref) for a biblical verse; search_tanakh(hebrew) for occurrences;
   get_commentary(commentator, ref) for a commentary entry; get_text(ref) for any other text
   Sefaria holds (Talmud, midrash, halakhic works), e.g. "Shabbat 88a".
   - PRAYERS AND THEIR ORDER (siddur, machzor, selichot, Ne'ilah, the Haggadah): search_liturgy,
     with a Hebrew phrase from the prayer or the prayer's name. Do not guess siddur or machzor
     refs for get_text; use the refs search_liturgy returns.
   - A claim that RESTRICTS a liturgical use ("only", "in certain selichot", "in the Sefard and
     Edot HaMizrach forms of", "on Shabbat and festivals") is a claim about where the words are
     NOT. Search the Hebrew and read the whole list of refs (`every_ref`): if the passage is also
     in rites or services the claim excludes, the claim is contradicted, even though the place it
     names is right.
   - THE SEPTUAGINT: get_lxx(ref), with the Hebrew-Bible reference. Sefaria has none.
   - A get_text that fails lists Sefaria's closest titles: try one of those at most once. A work
     Sefaria does not hold (a modern poem, a folk custom) is settled as in step 3.
3. You have NO web search. For a claim that can only be settled outside these sources (a
   classical or Near Eastern text, an inscription, a poem or other literature, a historical fact
   or date, a liturgical custom the materials do not document):
   - give it the verdict `needs_web` (empty evidence) when its exact wording, attribution,
     order, date, number or custom is the point of the sentence AND you have a specific doubt
     about it: something you half-remember differently, a detail that seems too neat, a
     quotation you cannot place. A second checker searches the web for these, at a cost per
     claim, so hand on the doubtful ones only: typically one claim in ten or fewer;
   - otherwise, if you know it to be right (a famous date, a well-known work, a standard fact),
     mark it supported with the explanation "known".
   Never mark such a claim contradicted from memory. A claim the Hebrew Bible, a commentator or a
   Sefaria text can settle (a genealogy in Chronicles, a Talmudic attribution) is never needs_web:
   check it yourself with the tools.
Batch your tool calls: request several lookups at once.

### Verdicts
- supported: the evidence says what the guide says. Keep the record SHORT, because there are
  many: `sentence` is only the FIRST SIX WORDS of the sentence, `claim` at most eight words,
  evidence [], explanation "" (or "known").
- contradicted: the evidence says something materially different. You MUST quote the source
  text that contradicts the claim and name the source. If you cannot quote such evidence, the
  verdict is unverifiable (or needs_web). Give a suggested_fix: the smallest change to the
  guide's sentence that makes it true, keeping its style, figures and argument.
- unverifiable: the sources above should settle it but do not. Never mark a claim
  contradicted because it is unfamiliar to you or on memory alone.
- needs_web: see "How to verify", step 3.

{materiality}

### Output
Return JSON matching the schema. `sentence` is the full sentence containing the claim, copied
EXACTLY from the excerpt. One record per distinct claim; a sentence with two claims gets two
records. `location` is the section the claim is in (e.g. "Introduction", "Liturgy",
"Verse 11"). For anything but contradicted, set suggested_fix to null.
"""

WEB_INSTRUCTIONS = """## YOUR TASK: VERIFY CLAIMS THAT NEED OUTSIDE SOURCES

These claims come from a study guide on Psalm {psalm}, written for an educated general audience by
an AI writer drawing partly on its own memory. A first checker, working from the Hebrew Bible and
the traditional commentators, could not settle them. Verify each one against evidence.

Tools: web search (prefer primary texts and standard references: a translation of the ancient
text itself, a museum or library catalogue, a scholarly edition); get_text(ref) for anything on
Sefaria (Talmud, midrash); search_liturgy for the siddur and machzor; get_lxx for the Septuagint;
get_verse(ref) for a biblical verse. Search for
each claim once, twice at most; batch lookups; do not search for what the sentence does not
claim.

{divine_names}

### Verdicts
- supported: the evidence says what the guide says. Give its URL or ref, with no quotation.
- contradicted: the evidence says something materially different. You MUST quote the source and
  give its URL or ref, and a suggested_fix: the smallest change to the sentence that makes it
  true, keeping its style, figures and argument.
- unverifiable: you found no evidence either way. Never mark a claim contradicted on memory
  alone or because it is unfamiliar.

{materiality}

### Output
Return JSON matching the schema: one record per claim below, in the same order, with `location`,
`sentence` and `claim` copied unchanged. For anything but contradicted, set suggested_fix to null.

## CLAIMS
{claims}
"""

GATHER_INSTRUCTIONS = """## YOUR TASK: FIND THE SOURCES THAT SETTLE THESE CLAIMS

These claims come from a study guide on Psalm {psalm}. A fact-checker will judge them from what
you find, so your job is RETRIEVAL, not judgment.

For EACH claim: search the web for the primary source or a standard reference that settles it,
and copy the passages that bear on it VERBATIM, with the page's URL. Prefer the text itself (a
translation of the ancient work, the poem, the prayer or piyyut, on sefaria.org, wikisource, a
library, museum or university site), then a scholarly reference. Search for every claim; one
search may serve several claims about the same source. Use AT MOST ONE search per claim: each
search is paid for. Copy enough of each passage to show what
it says about the claim's specific point (the wording, the order, the attribution, the date,
the custom), including anything that disagrees with the claim.

Do NOT answer from memory and do NOT give verdicts. A claim for which you retrieved nothing gets
"sources": []. `note` is one line, only if the sources disagree with each other or say something
the claim does not.

Return JSON: one item per claim below, with its `n`.

## CLAIMS
{claims}
"""

GATHER_SCHEMA = {
    "type": "object",
    "properties": {"claims": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "n": {"type": "integer"},
            "sources": {"type": "array", "items": {
                "type": "object",
                "properties": {"title": {"type": "string"}, "url": {"type": "string"},
                               "quote": {"type": "string"}},
                "required": ["title", "url", "quote"]}},
            "note": {"type": "string"}},
        "required": ["n", "sources", "note"]}}},
    "required": ["claims"],
}

GATHER_SCHEMA_STRICT = {
    "type": "object", "additionalProperties": False, "required": ["claims"],
    "properties": {"claims": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["n", "sources", "note"],
        "properties": {
            "n": {"type": "integer"},
            "sources": {"type": "array", "items": {
                "type": "object", "additionalProperties": False, "required": ["title", "url", "quote"],
                "properties": {"title": {"type": "string"}, "url": {"type": "string"},
                               "quote": {"type": "string"}}}},
            "note": {"type": "string"}}}}},
}

WEB_JUDGE_INSTRUCTIONS = """## YOUR TASK: JUDGE CLAIMS AGAINST THE SOURCES GATHERED FOR THEM

These claims come from a study guide on Psalm {psalm}, written by an AI writer drawing partly on
its own memory. A researcher looked for sources on each one and copied passages with URLs
(`sources`). Each passage was then checked against its live page (`check`):
- "quote found on the page": evidence, for any verdict.
- "page could not be fetched or read" (a PDF, a blocked site): the page came from a real search
  but the passage could not be re-checked. It may SUPPORT a claim; it may NOT establish a
  contradiction.
- "quote NOT found on the page": the passage may be misquoted or invented. It is not evidence.
Judge each claim from that evidence. You may also use get_text (Sefaria:
Talmud, midrash), search_liturgy (the siddur and machzor, with their order), get_lxx (the
Septuagint) and get_verse. You have no web search.

{divine_names}

### Verdicts
- supported: the verified passages (or your Sefaria lookups) say what the guide says. Give the
  URL or ref, with no quotation.
- contradicted: a passage FOUND ON ITS PAGE (or a Sefaria lookup) says something materially different. You
  MUST quote it and give its URL or ref, and a suggested_fix: the smallest change to the sentence
  that makes it true, keeping its style, figures and argument.
- unverifiable: no verified passage settles it. Never decide from memory.

{materiality}

### Output
Return JSON matching the schema: one record per claim below, in the same order, with `location`,
`sentence` and `claim` copied unchanged. For anything but contradicted, set suggested_fix to null.

## CLAIMS, WITH THE SOURCES FOUND FOR EACH
{claims}
"""

REVIEW_INSTRUCTIONS = """## YOUR TASK: REVIEW CLAIMS A FIRST CHECKER MARKED CONTRADICTED

These claims come from a study guide on Psalm {psalm}. A first, fast checker marked each one
contradicted and gave its evidence. A contradicted verdict licenses the copy editor to change the
guide, and a wrong "correction" is worse than a missed error, so re-judge each one yourself.

For each claim: read the sentence as a careful reader would, re-check the evidence with the tools
(get_verse, search_tanakh, get_commentary for a commentator's full entry, get_text for Talmud,
midrash, siddur), and decide.

{divine_names}

{materiality}

### Verdicts
- contradicted: confirmed. Quote the source that shows the sentence is false, name it, and give
  a suggested_fix: the smallest change to the sentence that makes it true, keeping its style,
  figures and argument.
- supported: the first checker was wrong or pedantic; say why in one sentence.
- unverifiable: the evidence does not settle it either way.

### Output
Return JSON matching the schema: one record per claim below, in the same order, with `location`,
`sentence` and `claim` copied unchanged. For anything but contradicted, set suggested_fix to null.

## CLAIMS
{claims}
"""


def _schema(verdicts) -> Dict:
    s = json.loads(json.dumps(RECORD_SCHEMA))
    s["properties"]["claims"]["items"]["properties"]["verdict"]["enum"] = list(verdicts)
    return s


LOCAL_SCHEMA = _schema(VERDICTS + ("needs_web",))
FINAL_SCHEMA = _schema(VERDICTS)


def claims_block(records: List[Dict], with_evidence: bool = False) -> str:
    """The claims handed to stage 2/3, as numbered JSON (pure)."""
    items = []
    for i, r in enumerate(records, 1):
        it = {"n": i, "location": r.get("location", ""), "sentence": r.get("sentence", ""),
              "claim": r.get("claim", ""), "claim_type": r.get("claim_type", "other")}
        if with_evidence:
            it["first_checker_finding"] = r.get("explanation", "")
            it["first_checker_evidence"] = r.get("evidence", [])
        items.append(it)
    return json.dumps(items, ensure_ascii=False, indent=1)


def merge_stage_results(local: List[Dict], web: List[Dict], review: List[Dict],
                        reviewed: bool = True) -> List[Dict]:
    """Stage-1 records, with every `needs_web` replaced by its stage-2 record and every
    `contradicted` by its stage-3 record (when `reviewed`; otherwise stage 1's verdict
    stands, as when stage 1 already ran on gpt-6-sol), in the guide's order (pure). A stage-2/3 batch
    that returned the wrong number of records is matched by sentence; an unmatched
    claim falls back to `unverifiable`, never to its stage-1 contradicted verdict."""
    web_q, rev_q = list(web), list(review)

    def take(queue: List[Dict], rec: Dict, stage: str) -> Dict:
        for j, cand in enumerate(queue):
            if _norm_ws(cand.get("sentence", "")) == _norm_ws(rec.get("sentence", "")) \
                    and _norm_ws(cand.get("claim", "")) == _norm_ws(rec.get("claim", "")):
                out = dict(queue.pop(j))
                out["stage"] = stage
                return out
        for j, cand in enumerate(queue):
            if _norm_ws(cand.get("sentence", "")) == _norm_ws(rec.get("sentence", "")):
                out = dict(queue.pop(j))
                out["stage"] = stage
                return out
        out = dict(rec, verdict="unverifiable", evidence=rec.get("evidence", []), suggested_fix=None,
                   stage=stage, explanation=(rec.get("explanation", "") + f" [no {stage} result]").strip())
        return out

    merged = []
    for r in local:
        if r.get("verdict") == "needs_web":
            merged.append(take(web_q, r, "web"))
        elif r.get("verdict") == "contradicted" and reviewed:
            rec = take(rev_q, r, "review")
            rec["first_verdict"] = "contradicted"
            merged.append(rec)
        else:
            merged.append(dict(r, stage="local"))
    return merged


def _fn(name: str, desc: str, props: Dict, required: List[str]) -> Dict:
    return {"type": "function", "name": name, "description": desc, "strict": True,
            "parameters": {"type": "object", "properties": props, "required": required,
                           "additionalProperties": False}}


FUNCTION_TOOLS = [
    _fn("get_verse", "The Hebrew (Masoretic) and English text of a biblical verse or verse range. "
        "Use a standard reference, e.g. 'Psalms 78:48', 'Song of Songs 8:6', 'II Kings 19:35'.",
        {"ref": {"type": "string"}}, ["ref"]),
    _fn("get_commentary", "A traditional commentator's full entry on a verse (Rashi, Ibn Ezra, Radak, "
        "Malbim, Meiri, Metzudat Zion, Minchat Shai, …): the research bundle's copy first, else Sefaria.",
        {"commentator": {"type": "string"}, "ref": {"type": "string"}}, ["commentator", "ref"]),
    _fn("search_tanakh", "Verses in the Hebrew Bible containing a Hebrew word or short phrase "
        "(consonants are enough). Returns the list of references; confirm exact forms with get_verse.",
        {"hebrew": {"type": "string"}}, ["hebrew"]),
    _fn("search_research", "Search the writer's research bundle (lexicons, concordance, liturgical notes, "
        "literary echoes, commentators) for a word or phrase, Hebrew or English. Returns the matching passages.",
        {"query": {"type": "string"}}, ["query"]),
    _fn("get_text", "Any text Sefaria holds, by its Sefaria reference: Talmud ('Shabbat 88a'), midrash "
        "('Bereishit Rabbah 56:10'), halakhic works, or a prayer by the exact ref search_liturgy gave. "
        "Hebrew and English where available. A ref Sefaria lacks returns its closest titles.",
        {"ref": {"type": "string"}}, ["ref"]),
    # Session 388: both $0.
    _fn("search_liturgy", "The siddur and machzor (Ashkenaz, Sefard, Chabad, Edot HaMizrach; Rosh Hashanah "
        "and Yom Kippur; the full selichot; kinnot and Tisha B'Av; the Haggadah; Ma'avar Yabbok). A Hebrew "
        "phrase returns the passage around it in each prayer that has it (and every matching ref); a name "
        "('Neilah', 'Fast of Esther', 'Maariv Aleinu') returns matching prayers and their exact refs. Every "
        "hit names the prayers before and after it in its service.",
        {"query": {"type": "string"}}, ["query"]),
    _fn("get_lxx", "The Septuagint for a verse, by its HEBREW-Bible reference ('Psalms 77:11'): Brenton's "
        "Greek text and his English translation (1851). For a few books without Brenton's Greek, the Greek "
        "comes as dictionary forms (lemmas) and the result says so: those show which word the translators "
        "used but not its case, tense or person. Sefaria holds no Septuagint.",
        {"ref": {"type": "string"}}, ["ref"]),
]


_COMMENTARY_SECTION = re.compile(r"^### (\d+):(\d+) — (.+?)\s*$\n(.*?)(?=^### |^## |\Z)", re.M | re.S)
# "(Ps 78:48)", "Isa 10:5", "Song 8:6-7", "2 Kgs 19:35", "Deut 32:24" in running text.
_CITED_REF = re.compile(r"(?<![\w:])((?:[1-3I]{1,3}\s)?[A-Z][a-z]+\.?)\s+(\d{1,3}):(\d{1,3})(?:\s*[–\-]\s*(\d{1,3}))?")


def commentary_entries(bundle: str, verses: Optional[set] = None) -> str:
    """Every `### ch:v — Commentator` entry of the bundle, verbatim (pure); only those on
    `verses` when given. ~52K chars for all of Ps 76, against a 284K bundle: the rest is
    concordance, lexicon and notes."""
    parts = [f"### {m.group(1)}:{m.group(2)} — {m.group(3)}\n{m.group(4).strip()}"
             for m in _COMMENTARY_SECTION.finditer(bundle or "")
             if verses is None or int(m.group(2)) in verses]
    return "\n\n".join(parts)


def chunk_verses(chunk_text: str) -> set:
    """The psalm verses a chunk's `**Verse N**` / `**Verses N–M**` headers cover (pure).
    Empty for the introduction and liturgy, which range over the whole psalm."""
    out = set()
    for m in re.finditer(r"^\*\*Verses?\s+(\d+)(?:\s*[–\-]\s*(\d+))?\*\*\s*$", chunk_text, re.M):
        lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
        out.update(range(lo, hi + 1))
    return out


def cited_refs(text: str) -> List[str]:
    """Biblical references cited in the guide, in order of first mention, deduplicated,
    unknown book names dropped (pure except for the book-name table)."""
    seen, out = set(), []
    for m in _CITED_REF.finditer(text or ""):
        ref = f"{m.group(1).rstrip('.')} {m.group(2)}:{m.group(3)}" + (f"-{m.group(4)}" if m.group(4) else "")
        parsed = parse_ref(ref)
        if not parsed:
            continue
        key = parsed
        if key not in seen:
            seen.add(key)
            out.append(ref)
    return out


def psalm_text(psalm: int, db_path: Optional[Path]) -> str:
    """The whole psalm, verse by verse, in Hebrew numbering (tanakh.db, else Sefaria)."""
    if usable_db(db_path):
        rows = _db_rows(db_path, "SELECT verse, hebrew, english FROM verses WHERE book_name='Psalms' "
                        "AND chapter=? ORDER BY verse", (psalm,))
        if rows:
            return "\n".join(f"**{psalm}:{v}** {h}\n{e}" for v, h, e in rows)
    try:
        out = _sefaria_text(f"Psalms {psalm}")
        return f"{out.get('hebrew', '')}\n{out.get('english', '')}".strip()
    except Exception:
        return ""


def shared_evidence(guide_text: str, bundle: str, db_path: Optional[Path], max_verses: int = 150,
                    verses: Optional[set] = None, psalm: Optional[int] = None) -> str:
    """The evidence a stage-1 call starts with: the commentators' entries (all of them, or
    those on `verses`) and the text of every verse `guide_text` cites (tanakh.db, else
    Sefaria). Session 386: handing these over up front replaced ~560 lookups whose outputs
    were each paid for on every later round; scoping them to the chunk keeps the prefix
    that every round replays small. Session 388: with `psalm`, the psalm itself comes first
    (~1.3K tokens for Ps 77), which the checker had fetched 17 times on Ps 77."""
    out = []
    if psalm:
        whole = psalm_text(psalm, db_path)
        if whole:
            out += [f"## PSALM {psalm} ITSELF (Masoretic text and a translation; the guide numbers verses "
                    "as the Hebrew does, heading included, so English Bibles may be one lower)", "", whole, ""]
    comm = commentary_entries(bundle, verses)
    if comm:
        out += ["## THE COMMENTATORS' ENTRIES ON THIS PSALM (full text, as the writer had them)", "", comm, ""]
    verses = []
    for ref in cited_refs(guide_text)[:max_verses]:
        v = lookup_verse(ref, db_path)
        if v.get("error"):
            continue
        verses.append(f"**{v.get('ref', ref)}**\n{v.get('hebrew', '')}\n{v.get('english', '')}")
    if verses:
        out += ["## EVERY BIBLICAL VERSE THE GUIDE CITES (Masoretic text and a translation)", "",
                "\n\n".join(verses), ""]
    return "\n".join(out)


def search_bundle(bundle: str, query: str, max_hits: int = 3, window: int = 500) -> Dict:
    """Passages of the research bundle around each match of `query` (pure). Hebrew is
    matched on consonants, so pointing and cantillation on either side do not matter."""
    q = (query or "").strip()
    if not bundle:
        return {"error": "no research bundle"}
    if not q:
        return {"error": "empty query"}
    if re.search(r"[א-ת]", q):
        qc = _consonants(q)
        # A consonants-and-single-spaces copy of the bundle, with each position mapped back.
        flat_chars, idx_map, prev_space = [], [], True
        for i, ch in enumerate(unicodedata.normalize("NFC", bundle)):
            if "א" <= ch <= "ת":
                flat_chars.append(ch)
                idx_map.append(i)
                prev_space = False
            elif ch in " \n\t־" and not prev_space:
                flat_chars.append(" ")
                idx_map.append(i)
                prev_space = True
        flat = "".join(flat_chars)
        starts = [idx_map[m.start()] for m in re.finditer(re.escape(qc), flat)] if qc else []
    else:
        starts = [m.start() for m in re.finditer(re.escape(q), bundle, re.I)]
    hits, last_end = [], -1
    for st in starts:
        if st < last_end:
            continue
        a, b = max(0, st - window // 2), min(len(bundle), st + window)
        head = bundle.rfind("\n#", 0, st)
        section = bundle[head + 1: bundle.find("\n", head + 1)].strip("# ").strip() if head >= 0 else ""
        hits.append({"section": section, "text": bundle[a:b]})
        last_end = b
        if len(hits) >= max_hits:
            break
    return {"query": q, "matches": len(starts), "passages": hits}


# -- quote verification ($0) ---------------------------------------------------------
# Session 386: with Google Search switched on, Gemini 3.8 Flash, 3.5 Flash and 3.1 Pro (at
# low thinking) returned "verbatim" passages and URLs WITHOUT searching -- no grounding
# metadata, a few hundred input tokens. Whether a model searches is its own choice, so the
# guard is not a model: every gathered passage is checked against the live page, and only
# a passage found there counts as evidence.

_VERIFY_UA = {"User-Agent": "Mozilla/5.0 (fact-check; psalms study guides)"}


def _norm_for_match(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))          # accents, nikud, te'amim
    s = s.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "־": " ", "–": "-", "—": "-"}))
    s = re.sub(r"[^\w\s]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def quote_on_page(quote: str, page_text: str, min_share: float = 0.6) -> bool:
    """True if the quote is on the page (pure): exact after normalisation, or at least
    `min_share` of its 5-word shingles appear (tolerates an ellipsis, a line break, a
    variant spelling). A quote of fewer than five words must match exactly."""
    q, t = _norm_for_match(quote), _norm_for_match(page_text)
    if not q or not t:
        return False
    if q in t:
        return True
    w = q.split()
    if len(w) < 5:
        return False
    shingles = [" ".join(w[i:i + 5]) for i in range(len(w) - 4)]
    return sum(1 for sh in shingles if sh in t) / len(shingles) >= min_share


def fetch_page_text(url: str, timeout: int = 20) -> Optional[str]:
    """Visible text of a web page, or None (network error, non-HTML, PDF text not
    extractable). Plain requests: no JavaScript."""
    try:
        r = requests.get(url, timeout=timeout, headers=_VERIFY_UA, allow_redirects=True)
        if r.status_code >= 400:
            return None
        ctype = r.headers.get("content-type", "")
        if "pdf" in ctype or url.lower().endswith(".pdf"):
            try:
                import io
                import logging
                logging.getLogger("pypdf").setLevel(logging.ERROR)
                from pypdf import PdfReader
                return " ".join((pg.extract_text() or "") for pg in PdfReader(io.BytesIO(r.content)).pages[:200])
            except Exception:
                return None
        r.encoding = r.encoding or r.apparent_encoding
        html = r.text
        html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
        text = re.sub(r"(?s)<[^>]+>", " ", html)
        import html as _html
        return _html.unescape(text)
    except Exception:
        return None


def verify_sources(items: List[Dict], parallel: int = 8) -> Dict[str, int]:
    """Mark every gathered source `verified` True/False in place by fetching its URL
    once and looking for its quote. Returns counts."""
    urls = sorted({src.get("url", "") for it in items for src in it.get("sources", []) if src.get("url")})
    with ThreadPoolExecutor(max_workers=parallel) as ex:
        pages = dict(zip(urls, ex.map(fetch_page_text, urls)))
    counts = {"sources": 0, "verified": 0, "page_unreadable": 0}
    for it in items:
        for src in it.get("sources", []):
            counts["sources"] += 1
            page = pages.get(src.get("url", ""))
            if page is None:
                src["verified"] = False
                src["check"] = "page could not be fetched or read"
                counts["page_unreadable"] += 1
            elif quote_on_page(src.get("quote", ""), page):
                src["verified"] = True
                src["check"] = "quote found on the page"
                counts["verified"] += 1
            else:
                src["verified"] = False
                src["check"] = "quote NOT found on the page"
    return counts


def summarize_tool_result(name: str, result: Dict, n: int = 240) -> str:
    """One line on what a $0 lookup returned, for the telemetry report (pure)."""
    if not isinstance(result, dict):
        return _clip(str(result), n)
    if result.get("error"):
        return "ERROR: " + _clip(str(result["error"]), n)
    if name == "search_tanakh":
        refs = result.get("refs") or result.get("results") or result.get("verses") or []
        total = result.get("count", result.get("total", len(refs) if isinstance(refs, list) else "?"))
        shown = ", ".join(str(r if not isinstance(r, dict) else r.get("ref", r)) for r in list(refs)[:12]) \
            if isinstance(refs, list) else ""
        return f"{total} verse(s)" + (f": {shown}" + (" …" if isinstance(refs, list) and len(refs) > 12 else "")
                                      if shown else "")
    if name == "search_research":
        hits = result.get("passages") or []
        where = "; ".join(dict.fromkeys(h.get("section", "") for h in hits if h.get("section")))
        first = _norm_ws(hits[0].get("text", "")) if hits else ""
        return (f"{result.get('matches', len(hits))} match(es) in the research bundle"
                + (f" (in: {_clip(where, 120)})" if where else "")
                + (f"; first: {_clip(first, n)}" if first else ""))
    if name == "search_liturgy":
        ps = result.get("prayers") or []
        first = ps[0] if ps else {}
        return (f"{result.get('matches', len(ps))} prayer(s) in the liturgy database"
                + (": " + _clip("; ".join(p.get("ref", "") for p in ps), 200) if ps else "")
                + (f"; first: {_clip(_norm_ws(first.get('text') or first.get('opening') or ''), n)}"
                   if first else ""))
    if name == "get_lxx":
        return (f"ref={result.get('ref')} (LXX ch. {result.get('lxx_chapter')}); Brenton: "
                f"{_clip(result.get('english_brenton', ''), n)}; Greek ({result.get('greek_form', '')}): "
                f"{_clip(result.get('greek', ''), 120)}")
    parts = []
    for k in ("ref", "source", "commentator"):
        if result.get(k):
            parts.append(f"{k}={result[k]}")
    for k in ("hebrew", "english", "text"):
        if result.get(k):
            # a bundle entry opens with the analyst's italic reason for requesting it; skip it
            body = re.sub(r"^\*[^\n]*\n", "", str(result[k]).lstrip())
            parts.append(f"{k}: {_clip(_norm_ws(body), n)}")
    return "; ".join(parts) or _clip(json.dumps(result, ensure_ascii=False), n)


def _web_action(item) -> Dict:
    """What an OpenAI web_search_call did: a search (query), an open_page (url), a find."""
    a = getattr(item, "action", None)
    if a is None:
        return {"type": "search", "query": ""}
    get = (lambda k: a.get(k)) if isinstance(a, dict) else (lambda k: getattr(a, k, None))
    out = {"type": get("type") or "search"}
    for k in ("query", "queries", "url", "pattern"):
        v = get(k)
        if v:
            out[k] = v if isinstance(v, (str, list)) else str(v)
    return out


# -- free lookups added in Session 388 ------------------------------------------------
# On Ps 77, 29 of 315 stage-1 lookups failed: 13 guessed siddur/machzor refs in a form Sefaria
# rejects, 5 asked Sefaria for the Septuagint (it has none), 8 named works Sefaria does not hold
# or spells differently, 3 were commentary entries that do not exist. Four liturgical claims then
# passed as "supported" with no stated basis. The prayer texts were on disk all along.

LITURGY_DB = Path(__file__).resolve().parents[2] / "data" / "liturgy.db"
_LITURGY_COLS = ("sefaria_ref", "source_text", "nusach", "occasion", "service", "section",
                 "prayer_name", "canonical_prayer_name", "sequence_order", "hebrew_text", "english_text")
_liturgy_cache: Dict[str, List[Dict]] = {}


def _norm_name(s: str) -> str:
    """Lower-case, apostrophes and hyphens dropped: "Ne'ilah" == "Neilah", "Ta'anit" == "Taanit"."""
    s = unicodedata.normalize("NFKD", s or "").lower()
    s = re.sub(r"[̀-ͯ'’ʼ`\-_]", "", s)
    return re.sub(r"[^a-z0-9א-ת ]+", " ", s).strip()


def _liturgy_rows(db_path: Optional[Path] = None) -> List[Dict]:
    """Every prayer in liturgy.db (harvested from Sefaria's siddurim and machzorim), loaded once."""
    path = Path(db_path or LITURGY_DB)
    key = str(path)
    if key not in _liturgy_cache:
        if not path.exists():
            _liturgy_cache[key] = []
        else:
            rows = _db_rows(path, f"SELECT {', '.join(_LITURGY_COLS)} FROM prayers ORDER BY source_text, "
                                  "service, sequence_order")
            out = []
            for r in rows:
                d = dict(zip(_LITURGY_COLS, r))
                d["_names"] = _norm_name(" ".join(str(d[k] or "") for k in (
                    "sefaria_ref", "source_text", "nusach", "occasion", "service", "section",
                    "prayer_name", "canonical_prayer_name")))
                out.append(d)
            _liturgy_cache[key] = out
    return _liturgy_cache[key]


def _flat_consonants(text: str):
    """(consonants-and-single-spaces copy of `text`, index map back into it) — as search_bundle."""
    flat, idx, prev_space = [], [], True
    for i, ch in enumerate(unicodedata.normalize("NFC", text or "")):
        if "א" <= ch <= "ת":
            flat.append(ch)
            idx.append(i)
            prev_space = False
        elif ch in " \n\t־" and not prev_space:
            flat.append(" ")
            idx.append(i)
            prev_space = True
    return "".join(flat), idx


# Session 397: what a lookup hands the checker is written into the prompt cache at 1.25x and
# re-read on every later round, and on Ps 79 the liturgy and get_text results were 87% of it.
# Vowels and accents roughly double a Hebrew passage's tokens and settle nothing a liturgical or
# rabbinic claim turns on, so those passages go out unpointed (a verse's pointing: get_verse).
# The maqaf, paseq, sof pasuq and nun hafukha stay: they are punctuation, not pointing.
_POINTING = re.compile("[֑-ׇֽֿׁׂׅׄ]")


def unpoint(text: str) -> str:
    """Hebrew without niqqud or cantillation (pure)."""
    return _POINTING.sub("", unicodedata.normalize("NFC", text or ""))


def short_ref(ref: str) -> str:
    """A liturgy ref without the place repeated at its end: Sefaria's siddur refs end
    'Amidah, Amidah' (section, then the prayer of the same name). Pure."""
    parts = [p.strip() for p in (ref or "").split(",")]
    while len(parts) > 2 and parts[-1] == parts[-2]:
        parts.pop()
    return ", ".join(parts)


def group_refs(refs: List[str]) -> Dict[str, List[str]]:
    """{book: [place, ...]} in first-seen order, places shortened by short_ref: the same list
    without the book's name repeated on every line (Ps 79: 6K chars -> under half). Pure."""
    out: Dict[str, List[str]] = {}
    for r in refs:
        book, _, place = short_ref(r).partition(", ")
        out.setdefault(book, []).append(place or "(the whole book)")
    return out


def _prayer_place(rows: List[Dict], d: Dict) -> Dict:
    """Where a prayer sits: its rite and service, and the prayers before and after it there.
    A prayer filed under no service gets no neighbours: the rest of that pile is unrelated."""
    if not d["service"]:
        return {"book": d["source_text"], "service": "", "before": "", "after": ""}
    same = [r for r in rows if r["source_text"] == d["source_text"] and r["service"] == d["service"]]
    i = next((k for k, r in enumerate(same) if r["sefaria_ref"] == d["sefaria_ref"]), -1)
    name = lambda r: r["canonical_prayer_name"] or r["prayer_name"]  # noqa: E731
    return {"book": d["source_text"], "service": d["service"] or "",
            "before": name(same[i - 1]) if i > 0 else "", "after": name(same[i + 1]) if 0 <= i < len(same) - 1 else ""}


def search_liturgy(query: str, db_path: Optional[Path] = None, max_hits: int = 6,
                   window: int = 600) -> Dict:
    """The siddur and machzor texts in liturgy.db ($0). A Hebrew query is matched on consonants
    against every prayer's text and returns a passage around each match; any other query is
    matched against the prayers' titles, rite and service ("Neilah", "Fast of Esther selichot")
    and returns their exact Sefaria refs, for get_text. Each hit says which prayers come before
    and after it in its service."""
    rows = _liturgy_rows(db_path)
    if not rows:
        return {"error": "the liturgy database is not available"}
    q = (query or "").strip()
    if not q:
        return {"error": "empty query"}
    hits = []
    if re.search(r"[א-ת]", q):
        qc = _consonants(q)
        for d in rows:
            if "_flat" not in d:   # built once per process; ~1,100 prayers, 5.4M chars
                d["_flat"], d["_idx"] = _flat_consonants(d["hebrew_text"])
            flat, idx = d["_flat"], d["_idx"]
            pos = flat.find(qc) if qc else -1
            if pos < 0:
                continue
            st = idx[pos]
            a, b = max(0, st - window // 2), min(len(d["hebrew_text"]), st + window // 2)
            hits.append({"ref": d["sefaria_ref"], **_prayer_place(rows, d),
                         "occurrences": flat.count(qc),
                         "text": unpoint(("…" if a else "") + d["hebrew_text"][a:b]
                                         + ("…" if b < len(d["hebrew_text"]) else ""))})
    else:
        # Every word must match; failing that, the prayers matching the most words ("Neilah
        # selichot": the Ashkenaz selichot of Ne'ilah sit inside a block titled otherwise).
        words = _norm_name(q).split()
        scored = [(sum(w in d["_names"] for w in words), d) for d in rows] if words else []
        best = max((sc for sc, _ in scored), default=0)
        partial = 0 < best < len(words)
        for sc, d in scored:
            if best and sc == best:
                hits.append({"ref": d["sefaria_ref"], **_prayer_place(rows, d),
                             "opening": _clip(_norm_ws(unpoint(d["hebrew_text"] or d["english_text"] or "")), 200)})
    partial = locals().get("partial", False)
    # Session 395: every hit's ref, not just the first max_hits: a claim that a verse is said ONLY
    # in one rite or service is a claim about where it is not, and needs the whole list.
    # Session 397: grouped by book (group_refs), the same refs in half the tokens.
    every = ({"every_ref": group_refs([h["ref"] for h in hits][:150]),
              "every_ref_note": "every match, grouped by book; get_text takes 'book, place'"}
             if len(hits) > max_hits else {})
    # Session 397: a passage reprinted word for word BETWEEN THE SAME NEIGHBOURS (the Rosh Hashanah
    # Amidah of each service, both days) is shown once, its other places under also_in; the slots
    # it would have taken go to passages that differ. Neighbours are part of the key: the order of
    # prayers is what most liturgical errors get wrong (Ps 79: 12 of 78 claims, mostly sequence).
    shown: Dict[str, Dict] = {}
    for h in hits:
        key = "|".join((_consonants(h.get("text") or h.get("opening") or "") or h["ref"],
                        h.get("before", ""), h.get("after", "")))
        if key in shown:
            shown[key].setdefault("also_in", []).append(short_ref(h["ref"]))
        elif len(shown) < max_hits:
            shown[key] = dict(h)
    return {"query": q, "source": "liturgy.db (siddurim, machzorim, selichot, kinnot harvested from Sefaria)",
            "matches": len(hits), "prayers": list(shown.values()), **every,
            **({"partial": "no prayer matches every word; these match the most"} if partial else {}),
            **({"note": f"{len(hits) - max_hits} more; narrow the query"} if len(hits) > max_hits else {})}


def sefaria_suggestions(name: str, limit: int = 6) -> List[str]:
    """Sefaria's own completions for a title that did not resolve (texts only, not topics), $0."""
    try:
        r = requests.get(f"{SEFARIA}/api/name/{requests.utils.quote(name.strip())}",
                         params={"limit": limit}, timeout=15)
        r.raise_for_status()
        objs = r.json().get("completion_objects") or []
        return [o.get("key") or o.get("title") for o in objs if o.get("type") == "ref"][:limit]
    except Exception:
        return []


# Bolls.life's "LXXE" is Brenton's 1851 English translation of the Septuagint. Its Greek
# ("LXX") is LEMMATIZED -- dictionary forms, not the inflected text -- so since Session 390
# the Greek comes from Brenton's own Greek text (src/data_sources/lxx_brenton.py; same LXX
# numbering), with Bolls's lemmas only for books Brenton's file lacks, labelled as such.
# Psalms are numbered by the Greek (MT 77 = LXX 76).
BOLLS = "https://bolls.life"
_BOLLS_BOOK = {"Genesis": 1, "Exodus": 2, "Leviticus": 3, "Numbers": 4, "Deuteronomy": 5, "Joshua": 6,
               "Judges": 7, "Ruth": 8, "I Samuel": 9, "II Samuel": 10, "I Kings": 11, "II Kings": 12,
               "I Chronicles": 13, "II Chronicles": 14, "Job": 18, "Psalms": 19, "Proverbs": 20,
               "Ecclesiastes": 21, "Song of Songs": 22, "Isaiah": 23, "Lamentations": 25, "Ezekiel": 26,
               "Daniel": 27, "Hosea": 28, "Joel": 29, "Amos": 30, "Obadiah": 31, "Jonah": 32, "Micah": 33,
               "Nahum": 34, "Habakkuk": 35, "Zephaniah": 36, "Haggai": 37, "Zechariah": 38, "Malachi": 39}


def lookup_lxx(ref: str) -> Dict:
    """The Septuagint for a verse (MT reference): Brenton's English and Brenton's Greek (Bolls's
    lemmas where his Greek is missing). Sefaria holds no Septuagint. A Psalm is mapped to the Greek
    verse by verse (S390: MT 10, 115, 116, 147 fall inside or across Greek chapters), and Brenton's
    English, which leaves the heading unnumbered, is aligned by the chapter's last verse number."""
    parsed = parse_ref(ref)
    if not parsed:
        return {"error": f"could not parse reference {ref!r}; use e.g. 'Psalms 77:11'"}
    book, ch, v, end = parsed
    bid = _BOLLS_BOOK.get(book)
    if bid is None:
        return {"error": f"no Septuagint lookup for {book} (its chapters differ from the Hebrew)"}
    from src.data_sources import lxx_brenton
    mt_verses = range(v, (end or v) + 1)
    targets = ([lxx_brenton.mt_to_lxx(ch, x) for x in mt_verses] if book == "Psalms"
               else [(ch, x) for x in mt_verses])
    g_parts, e_parts, forms = [], [], []
    for lch in dict.fromkeys(c for c, _ in targets):
        want = {lv for c, lv in targets if c == lch}
        grk, form = [], "Brenton's Greek text (1851)"
        try:
            code = lxx_brenton.BOOK_CODES.get(book)
            grk = [{"verse": n, "text": t} for n, t in sorted(lxx_brenton.chapter(code, lch).items())] if code else []
        except Exception:
            grk = []
        try:
            if not grk:
                form = "LEMMAS only (dictionary forms; no case, tense or person)"
                grk = requests.get(f"{BOLLS}/get-chapter/LXX/{bid}/{lch}/", timeout=20).json()
            eng = requests.get(f"{BOLLS}/get-chapter/LXXE/{bid}/{lch}/", timeout=20).json()
        except Exception as e:
            return {"error": f"Septuagint lookup failed: {e}"}
        last = lambda rows: max([x.get("verse", 0) for x in rows] or [0])
        shift = max(0, last(grk) - last(eng)) if book == "Psalms" else 0
        g_parts += [x["text"] for x in grk if x.get("verse") in want]
        e_parts += [_strip_html(x["text"]) for x in eng if x.get("verse", 0) + shift in want]
        forms.append(form)
    g, e = " ".join(g_parts), " ".join(e_parts)
    if not (g or e):
        return {"error": f"no Septuagint text found for {ref}"}
    greek_form = " / ".join(dict.fromkeys(forms))
    return {"ref": f"{book} {ch}:{v}" + (f"-{end}" if end else ""), "lxx_chapter": targets[0][0],
            "lxx_ref": "; ".join(f"{c}:{lv}" for c, lv in targets),
            "source": f"Brenton's English Septuagint (1851, via Bolls.life); Greek: {greek_form}",
            "english_brenton": e, "greek": g, "greek_form": greek_form}


def lookup_text(ref: str, liturgy_db: Optional[Path] = None) -> Dict[str, str]:
    r = (ref or "").strip()
    # A ref from search_liturgy: answer it from disk, with no network call. Session 397: also in
    # the shortened 'book, place' form every_ref lists.
    rows = _liturgy_rows(liturgy_db)
    local = (next((d for d in rows if d["sefaria_ref"] == r), None)
             or next((d for d in rows if short_ref(d["sefaria_ref"]) == short_ref(r)), None))
    if local:
        r = local["sefaria_ref"]
        out = {"ref": r, "source": "liturgy.db (harvested from Sefaria)", "url": f"{SEFARIA}/{r.replace(' ', '_')}",
               **{k: v for k, v in _prayer_place(_liturgy_rows(liturgy_db), local).items()},
               "hebrew": local["hebrew_text"] or "", "english": local["english_text"] or ""}
    else:
        try:
            out = _sefaria_text(r)
            if not (out.get("hebrew") or out.get("english")):
                raise ValueError("no text")
            out["source"] = "Sefaria"
        except Exception as e:
            return _text_not_found(r, e)
    for k in ("hebrew", "english"):
        if len(out.get(k, "")) > 2500:
            out[k] = out[k][:2500] + " […truncated; for a passage inside a prayer, use search_liturgy]"
    # Session 397: unpointed AFTER the cut, so the passage is the same span as before, in fewer tokens.
    if re.search("[֑-ׇ]", out.get("hebrew", "")):
        out["hebrew"] = unpoint(out["hebrew"])
        out["hebrew_pointing"] = "removed; for a biblical verse's vowels and accents use get_verse"
    return out


_LITURGICAL = re.compile(r"siddur|machzor|mahzor|selich|slich|neilah|ne.ilah|maariv|shacharit|mussaf|musaf|"
                         r"minchah|mincha|kinot|haggadah|piyyut", re.I)


def _text_not_found(ref: str, err: Exception) -> Dict[str, str]:
    """A failed get_text that says what to try instead, so the checker does not guess variants."""
    msg = f"Sefaria has no text at {ref!r} ({str(err)[:80]})."
    if re.search(r"septuagint|\blxx\b", ref, re.I):
        return {"error": msg + " Sefaria holds no Septuagint: use get_lxx."}
    if _LITURGICAL.search(ref):
        return {"error": msg + " For the siddur and machzor, use search_liturgy (a prayer's name, or a "
                "Hebrew phrase from it); it returns the exact refs."}
    title = re.split(r"[,:]|\s\d", ref)[0].strip()
    sugg = sefaria_suggestions(title)
    if sugg:
        return {"error": msg + " Sefaria titles like it: " + "; ".join(sugg) + "."}
    return {"error": msg + " Sefaria does not seem to hold this work: settle the claim from the other "
            "sources, or hand it on as needs_web if it is doubtful."}


@dataclass
class FactCheckResult:
    records: List[Dict]
    chunks: List[Dict]
    usage: Dict[str, int] = field(default_factory=dict)
    web_searches: int = 0
    function_calls: int = 0
    cost_usd: float = 0.0
    token_cost_usd: float = 0.0
    search_cost_usd: float = 0.0
    seconds: float = 0.0
    model: str = DEFAULT_MODEL
    effort: str = DEFAULT_EFFORT
    stages: Dict[str, Dict] = field(default_factory=dict)
    # Session 387: what each call looked up and found, the gathered web passages and their
    # page checks, and the evidence handed over up front. Written to *_telemetry.json.
    telemetry: Dict = field(default_factory=dict)

    def meta(self, psalm: int) -> Dict:
        return {"psalm": psalm, "model": self.model, "effort": self.effort,
                "web_searches": self.web_searches, "function_calls": self.function_calls,
                "cost_usd": self.cost_usd, "token_cost_usd": self.token_cost_usd,
                "search_cost_usd": self.search_cost_usd, "usage": self.usage,
                "seconds": round(self.seconds), "chunks": [c["label"] for c in self.chunks],
                "stages": self.stages, "verdicts": verdict_counts(self.records)}


def billing_model(model: str, service_tier: Optional[str]) -> str:
    """The cost_tracker.PRICING row a response is billed under: `<model>@flex` when the API
    says it ran on flex and that row exists, else the model's own (standard) row. Read from
    the RESPONSE, not the request: a call that fell back to the standard tier is billed as one."""
    if service_tier == "flex":
        from src.utils.cost_tracker import PRICING
        if f"{model}@flex" in PRICING:
            return f"{model}@flex"
    return model


def is_flex_unavailable(err: Exception) -> bool:
    """A 429 meaning flex has no capacity now (not billed), not a rate limit of ours."""
    s = str(err).lower()
    return getattr(err, "status_code", None) == 429 and ("resource" in s or "unavailable" in s or "flex" in s)


def _billed(run: Dict) -> Dict[str, Dict]:
    """A run's usage per price row; a run without the split (Gemini) is billed on its model."""
    return run.get("billed") or {run["model"]: run["usage"]}


def _empty_usage() -> Dict[str, int]:
    # cache_write (Session 388): GPT-5.6+ bills a cache write at 1.25x input.
    return {"input": 0, "cached": 0, "cache_write": 0, "output": 0, "reasoning": 0}


class FactChecker:
    def __init__(self, model: str = DEFAULT_MODEL, effort: str = DEFAULT_EFFORT,
                 db_path: Optional[Path] = Path("database/tanakh.db"), logger=None,
                 cost_tracker=None, client=None, chunk_chars: int = DEFAULT_CHUNK_CHARS,
                 web_search: bool = True, parallel: int = 3,
                 budget_check: Optional[Callable[[float], None]] = None,
                 web_model: str = DEFAULT_WEB_MODEL, web_effort: str = DEFAULT_WEB_EFFORT,
                 web_judge_model: str = DEFAULT_WEB_JUDGE_MODEL, web_judge_effort: str = "high",
                 review_model: Optional[str] = DEFAULT_REVIEW_MODEL,
                 review_effort: str = DEFAULT_REVIEW_EFFORT,
                 web_batch: int = WEB_BATCH, review_batch: int = REVIEW_BATCH,
                 bundle_in_context: bool = False,
                 service_tier: Optional[str] = DEFAULT_SERVICE_TIER):
        for m in (model, review_model, web_judge_model):
            if m and not m.startswith("gpt-"):
                raise ValueError("stages 1 and 3 run on the OpenAI Responses API; use gpt-* models")
        if web_model and not web_model.startswith(("gpt-", "gemini-")):
            raise ValueError("the web stage runs on gpt-* (OpenAI web search) or gemini-* (Google Search)")
        self.model, self.effort = model, effort
        self.web_model, self.web_effort = web_model, web_effort
        self.web_judge_model, self.web_judge_effort = web_judge_model, web_judge_effort
        self.review_model, self.review_effort = review_model, review_effort
        self.web_batch, self.review_batch = max(1, web_batch), max(1, review_batch)
        self.service_tier = service_tier
        # Session 386: OFF. Replaying the ~130K-token bundle on every tool round was most of
        # Session 385's $4.87; the model now pulls what it needs through the tools.
        self.bundle_in_context = bundle_in_context
        self.db_path = Path(db_path) if db_path else None
        self.logger = logger
        self.cost_tracker = cost_tracker
        self.chunk_chars = chunk_chars
        self.web_search = web_search
        self.parallel = max(1, parallel)
        self.budget_check = budget_check
        self._spent: Dict[str, Dict] = {}   # per model: usage + searches, for budget_check
        self._trace: List[Dict] = []         # every lookup and web action, for the telemetry report
        self._gathered: List[Dict] = []
        if client is None:
            from openai import OpenAI
            client = OpenAI(timeout=1800, max_retries=2)
        self.client = client
        self._gemini_client = None

    def _log(self, msg: str):
        if self.logger:
            self.logger.info(msg)
        else:
            print(msg, flush=True)

    # -- tools ---------------------------------------------------------------
    def _run_tool(self, name: str, args: Dict, bundle: str) -> Dict:
        if name == "get_verse":
            return lookup_verse(args.get("ref", ""), self.db_path)
        if name == "get_commentary":
            return lookup_commentary(args.get("commentator", ""), args.get("ref", ""), bundle)
        if name == "search_tanakh":
            return search_tanakh(args.get("hebrew", ""), self.db_path)
        if name == "get_text":
            return lookup_text(args.get("ref", ""))
        if name == "search_research":
            return search_bundle(bundle, args.get("query", ""))
        if name == "search_liturgy":
            return search_liturgy(args.get("query", ""))
        if name == "get_lxx":
            return lookup_lxx(args.get("ref", ""))
        return {"error": f"unknown tool {name}"}

    # -- one tool loop ---------------------------------------------------------
    def _loop(self, label: str, model: str, effort: str, content: List[Dict], tools: List[Dict],
              schema: Dict, bundle: str, cache_key: str) -> Dict:
        common = dict(model=model, tools=tools,
                      reasoning={"effort": effort, "summary": "auto"},
                      text={"format": {"type": "json_schema", "name": "fact_check",
                                       "schema": schema, "strict": True}},
                      max_output_tokens=64000, prompt_cache_key=cache_key)
        if self.service_tier:
            common["service_tier"] = self.service_tier
        usage = _empty_usage()
        billed: Dict[str, Dict[str, int]] = {}   # per price row (model, or model@flex): what it costs
        searches = fcalls = 0
        tool_counts: Dict[str, int] = {}
        summaries: List[str] = []
        t0 = time.time()
        resp = self._create(input=[{"role": "user", "content": content}], **common)
        for rnd in range(MAX_TOOL_ROUNDS + 1):
            u = resp.usage
            fresh, cached, write = split_input_tokens(u)
            out, rsn = split_output_tokens(u)
            step = {"input": fresh, "cached": cached, "cache_write": write, "output": out, "reasoning": rsn}
            for k in usage:
                usage[k] += step[k]
            row = billing_model(model, getattr(resp, "service_tier", None))
            b = billed.setdefault(row, _empty_usage())
            for k in b:
                b[k] += step[k]
            calls = []
            step_searches = 0
            for it in resp.output:
                if it.type == "web_search_call":
                    act = _web_action(it)
                    if act.get("type", "search") == "search":
                        step_searches += 1
                    self._trace.append({"run": label, "model": model, "kind": "web", **act})
                elif it.type == "function_call":
                    calls.append(it)
                elif it.type == "reasoning":
                    summaries += [s.text for s in (it.summary or [])]
            searches += step_searches
            self._account(row, step, step_searches)
            if not calls:
                break
            fcalls += len(calls)
            outputs = []
            for c in calls:
                tool_counts[c.name] = tool_counts.get(c.name, 0) + 1
                try:
                    args = json.loads(c.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = self._run_tool(c.name, args, bundle)
                self._trace.append({"run": label, "model": model, "kind": "lookup", "tool": c.name,
                                    "args": args, "found": summarize_tool_result(c.name, result)})
                outputs.append({"type": "function_call_output", "call_id": c.call_id,
                                "output": json.dumps(result, ensure_ascii=False)[:20000]})
            self._log(f"  {label}: round {rnd + 1}, {len(calls)} lookup(s), {searches} search(es) so far")
            extra = {"tool_choice": "none"} if rnd + 1 >= MAX_TOOL_ROUNDS else {}
            resp = self._create(previous_response_id=resp.id, input=outputs, **common, **extra)
        text = resp.output_text or ""
        status = getattr(resp, "status", "completed")
        truncated = False
        try:
            records = parse_fact_check_json(text) if text.strip() else []
        except (json.JSONDecodeError, ValueError) as e:
            records, truncated = salvage_records(text), True
            self._log(f"  {label}: final answer is not valid JSON ({str(e)[:80]}; status={status}, "
                      f"{len(text):,} chars); salvaged {len(records)} complete record(s)")
        if status == "incomplete":
            truncated = True
        self._log(f"  {label}: {len(records)} records, {searches} searches, {fcalls} lookups, "
                  f"{time.time() - t0:.0f}s, status={status}")
        return {"records": records, "usage": usage, "billed": billed, "searches": searches, "fcalls": fcalls,
                "tool_counts": tool_counts, "status": status, "thinking": "\n\n".join(summaries),
                "label": label, "model": model, "effort": effort, "seconds": round(time.time() - t0),
                "truncated": truncated}

    def _account(self, model: str, step: Dict, searches: int) -> None:
        s = self._spent.setdefault(model, {"usage": _empty_usage(), "searches": 0})
        for k in s["usage"]:
            s["usage"][k] += step[k]
        s["searches"] += searches
        if self.budget_check:
            self.budget_check(sum(self._price(m, v["usage"], v["searches"]) for m, v in self._spent.items()))

    def _create(self, **kw):
        last = None
        for attempt in range(3):
            try:
                r = self.client.responses.create(**kw)
                if getattr(r, "status", "completed") == "incomplete" and not (r.output_text or "").strip() \
                        and not any(it.type == "function_call" for it in r.output):
                    raise RuntimeError(f"incomplete response: {getattr(r, 'incomplete_details', None)}")
                return r
            except Exception as e:  # overload / network / empty incomplete (seen in S384)
                last = e
                self._log(f"  attempt {attempt + 1} failed: {str(e)[:200]}")
                # Session 397: flex has no capacity right now (429, not billed). Wait longer; on
                # the last try ask for the standard tier, so a busy hour costs money, not the check.
                if kw.get("service_tier") == "flex" and is_flex_unavailable(e):
                    if attempt == 1:
                        self._log("  flex unavailable twice; this call goes to the standard tier")
                        kw = {**kw, "service_tier": "default"}
                    time.sleep(30 * (attempt + 1))
                    continue
                time.sleep(10 * (attempt + 1))
        raise RuntimeError(f"fact-check call failed: {last}")

    def _cost_of(self, billed: Dict[str, Dict], searches: int) -> float:
        """A run's (or stage's) cost from its usage per price row, plus its search fees."""
        return sum(self._price(row, u, 0) for row, u in billed.items()) +             self._price(next(iter(billed), self.model), _empty_usage(), searches)

    @staticmethod
    def _price(model: str, usage: Dict, searches: int) -> float:
        fee = 0.0 if model.startswith("gemini-") else searches * WEB_SEARCH_USD_PER_CALL
        return price_tokens(model, input_tokens=usage["input"], output_tokens=usage["output"],
                            thinking_tokens=usage["reasoning"], cached_input_tokens=usage["cached"],
                            cache_write_tokens=usage.get("cache_write", 0)) + fee

    # -- the web stage on Gemini ----------------------------------------------------
    def _gemini(self):
        if self._gemini_client is None:
            import os
            from google import genai
            key = os.environ.get("GEMINI_API_KEY")
            if not key:
                raise ValueError("GEMINI_API_KEY not set")
            self._gemini_client = genai.Client(api_key=key)
        return self._gemini_client

    def _gemini_web(self, label: str, model: str, effort: str, text: str,
                    schema: Optional[Dict] = None) -> Dict:
        """One grounded Gemini call over a batch of claims. Google runs the searches inside
        the call, so there is no tool loop and nothing is replayed."""
        from google.genai import types
        cfg = dict(tools=[types.Tool(google_search=types.GoogleSearch())],
                   thinking_config=types.ThinkingConfig(thinking_level=effort, include_thoughts=True),
                   response_mime_type="application/json", response_json_schema=schema or FINAL_SCHEMA)
        t0, last, resp = time.time(), None, None
        for attempt in range(3):
            try:
                resp = self._gemini().models.generate_content(
                    model=model, contents=text, config=types.GenerateContentConfig(**cfg))
                if (resp.text or "").strip():
                    break
                last = RuntimeError(f"empty response (finish={getattr(resp.candidates[0], 'finish_reason', '?') if resp.candidates else '?'})")
            except Exception as e:  # 429 / 503 / transient
                last = e
            self._log(f"  {label}: attempt {attempt + 1} failed: {str(last)[:200]}")
            time.sleep(10 * (attempt + 1))
        if resp is None or not (resp.text or "").strip():
            raise RuntimeError(f"{label}: Gemini web check failed: {last}")
        um = resp.usage_metadata
        cached = getattr(um, "cached_content_token_count", 0) or 0
        usage = {"input": (um.prompt_token_count or 0) - cached, "cached": cached, "cache_write": 0,
                 "output": um.candidates_token_count or 0, "reasoning": um.thoughts_token_count or 0}
        gm = getattr(resp.candidates[0], "grounding_metadata", None) if resp.candidates else None
        queries = list(getattr(gm, "web_search_queries", None) or [])
        sources = [{"title": getattr(c.web, "title", ""), "uri": getattr(c.web, "uri", "")}
                   for c in (getattr(gm, "grounding_chunks", None) or []) if getattr(c, "web", None)]
        self._account(model, usage, len(queries))
        thoughts = [pt.text for pt in resp.candidates[0].content.parts
                    if getattr(pt, "thought", False) and pt.text] if resp.candidates else []
        records = parse_fact_check_json(resp.text)
        self._log(f"  {label}: {len(records)} records, {len(queries)} Google searches, "
                  f"{time.time() - t0:.0f}s")
        return {"records": records, "usage": usage, "searches": len(queries), "fcalls": 0,
                "tool_counts": {}, "status": "completed", "thinking": "\n\n".join(thoughts),
                "label": label, "model": model, "queries": queries, "sources": sources}

    # -- the three stages ----------------------------------------------------
    def _local_chunk(self, psalm: int, chunk: Dict, bundle: str, idx: int, n: int,
                     evidence: str = "") -> Dict:
        content = []
        if bundle and self.bundle_in_context:
            content.append({"type": "input_text", "text": bundle})
        if evidence:
            content.append({"type": "input_text", "text": evidence})
        content.append({"type": "input_text", "text": LOCAL_INSTRUCTIONS.format(
            psalm=psalm, divine_names=DIVINE_NAMES_NOTE, materiality=MATERIALITY_NOTE)})
        content.append({"type": "input_text", "text": f"## EXCERPT ({chunk['label']})\n\n{chunk['text']}"})
        return self._loop(f"local {idx}/{n} [{chunk['label']}]", self.model, self.effort, content,
                          FUNCTION_TOOLS, LOCAL_SCHEMA, bundle, f"fact-check-ps{psalm}")

    def _local_chunk_safe(self, psalm: int, chunk: Dict, bundle: str, idx: int, n: int,
                          evidence: str = "") -> List[Dict]:
        """_local_chunk, re-run in halves (split at verse headers) when its answer was cut off:
        a shorter excerpt means a shorter answer. The truncated run's salvaged records are
        kept only if the halves fail too. Returns every run made, for the accounting."""
        first = self._local_chunk(psalm, chunk, bundle, idx, n, evidence)
        if not first.get("truncated"):
            return [first]
        halves = split_guide_for_checking(chunk["text"], max(2000, len(chunk["text"]) // 2 + 1))
        if len(halves) < 2:
            return [first]
        self._log(f"  local {idx}/{n}: answer truncated; re-checking in {len(halves)} parts")
        runs = []
        for j, h in enumerate(halves, 1):
            ev = shared_evidence(h["text"], bundle, self.db_path, verses=chunk_verses(h["text"]) or None,
                                 psalm=psalm)
            runs.append(self._local_chunk(psalm, h, bundle, f"{idx}.{j}", n, ev))
        if any(r.get("truncated") for r in runs):
            return [first] + runs          # keep what was salvaged from every attempt
        first = dict(first, records=[], superseded=True)   # billed, but its records are replaced
        return [first] + runs

    def _gather_then_judge(self, psalm: int, claims: List[Dict], bundle: str) -> List[Dict]:
        """Stage 2: a cheap model GATHERS passages with web search (no verdicts), every
        passage is checked against its live page ($0), and the judge model rules from the
        checked passages without searching. Session 386 measurements on Ps 76's 71 web
        claims: Sol searching and judging itself cost $3.79; Gemini (Google Search content
        is not billed) mostly did NOT search when asked -- 3.8 Flash returned passages from
        memory, 33 of 71 claims with a passage that was really on its page, and its
        copyright filter blocked whole batches -- so the default gatherer is gpt-6-luna,
        whose search is real and whose rates make the ~8K tokens of results a search
        nearly free (the $0.01 fee per search remains)."""
        size = self.web_batch
        batches = [claims[i:i + size] for i in range(0, len(claims), size)]

        def gather(i: int) -> Dict:
            text = GATHER_INSTRUCTIONS.format(psalm=psalm, claims=claims_block(batches[i]))
            label = f"gather {i + 1}/{len(batches)}"
            if self.web_model.startswith("gemini-"):
                return self._gemini_web(label, self.web_model, self.web_effort, text, GATHER_SCHEMA)
            tools = [{"type": "web_search", "search_context_size": WEB_CONTEXT_SIZE}]
            return self._loop(label, self.web_model, self.web_effort, [{"type": "input_text", "text": text}],
                              tools, GATHER_SCHEMA_STRICT, bundle, f"fact-check-gather-ps{psalm}")

        with ThreadPoolExecutor(max_workers=max(self.parallel, len(batches))) as ex:
            gathered = list(ex.map(gather, range(len(batches))))
        items = []
        for bi, run in enumerate(gathered):
            by_n = {g.get("n"): g for g in run["records"] if isinstance(g, dict)}
            for j, rec in enumerate(batches[bi], 1):
                g = by_n.get(j, {})
                items.append({"location": rec.get("location", ""), "sentence": rec.get("sentence", ""),
                              "claim": rec.get("claim", ""), "claim_type": rec.get("claim_type", "other"),
                              "sources": g.get("sources", []), "researcher_note": g.get("note", "")})
        vc = verify_sources(items)
        self._log(f"  gathered sources checked against their pages: {vc}")
        self._verify_counts = vc
        self._gathered = items
        jb = self.review_batch
        jbatches = [items[i:i + jb] for i in range(0, len(items), jb)]

        def judge(i: int) -> Dict:
            block = json.dumps([dict(it, n=k) for k, it in enumerate(jbatches[i], 1)], ensure_ascii=False, indent=1)
            text = WEB_JUDGE_INSTRUCTIONS.format(psalm=psalm, divine_names=DIVINE_NAMES_NOTE,
                                                 materiality=MATERIALITY_NOTE, claims=block)
            return self._loop(f"judge {i + 1}/{len(jbatches)}", self.web_judge_model, self.web_judge_effort,
                              [{"type": "input_text", "text": text}], FUNCTION_TOOLS, FINAL_SCHEMA, bundle,
                              f"fact-check-judge-ps{psalm}")

        with ThreadPoolExecutor(max_workers=self.parallel) as ex:
            judged = list(ex.map(judge, range(len(jbatches))))
        return gathered + judged

    def _claims_stage(self, stage: str, psalm: int, claims: List[Dict], bundle: str) -> List[Dict]:
        """Stage 2 (web) or 3 (review) over `claims`, in parallel batches."""
        if stage == "web" and self.web_judge_model:
            return self._gather_then_judge(psalm, claims, bundle)
        if stage == "web":
            model, effort, size = self.web_model, self.web_effort, self.web_batch
            tools = [{"type": "web_search", "search_context_size": WEB_CONTEXT_SIZE}] + FUNCTION_TOOLS
            template, with_ev = WEB_INSTRUCTIONS, False
        else:
            model, effort, size = self.review_model, self.review_effort, self.review_batch
            tools, template, with_ev = FUNCTION_TOOLS, REVIEW_INSTRUCTIONS, True
        batches = [claims[i:i + size] for i in range(0, len(claims), size)]

        def run(i: int) -> Dict:
            text = template.format(psalm=psalm, divine_names=DIVINE_NAMES_NOTE,
                                   materiality=MATERIALITY_NOTE,
                                   claims=claims_block(batches[i], with_evidence=with_ev))
            return self._loop(f"{stage} {i + 1}/{len(batches)}", model, effort,
                              [{"type": "input_text", "text": text}], tools, FINAL_SCHEMA, bundle,
                              f"fact-check-{stage}-ps{psalm}")

        with ThreadPoolExecutor(max_workers=self.parallel) as ex:
            return list(ex.map(run, range(len(batches))))

    # -- public ---------------------------------------------------------------
    def _bill_tracker(self) -> None:
        """Hand everything spent so far to the cost tracker, once: tokens per model and the
        web-search fee. Session 387: this used to happen only at the end of a successful
        check, so a check that raised (Ps 77, first attempt) left its spend out of the run's
        cost file entirely."""
        if self.cost_tracker is None or getattr(self, "_billed", False):
            return
        self._billed = True
        fee_searches = 0
        for m, v in self._spent.items():
            self.cost_tracker.add_usage(m, input_tokens=v["usage"]["input"], output_tokens=v["usage"]["output"],
                                        thinking_tokens=v["usage"]["reasoning"],
                                        cache_read_tokens=v["usage"]["cached"],
                                        cache_write_tokens=v["usage"].get("cache_write", 0))
            if not m.startswith("gemini-"):
                fee_searches += v["searches"]
        if fee_searches:
            # The per-search fee is money too; before Session 387 it lived only in this report.
            self.cost_tracker.add_charge("web search (OpenAI, $10 per 1,000)",
                                         fee_searches * WEB_SEARCH_USD_PER_CALL,
                                         model=self.web_model, detail=f"{fee_searches} searches")

    def check(self, guide_markdown: str, psalm_number: int, bundle_text: str = "",
              thinking_out: Optional[Path] = None) -> FactCheckResult:
        self._billed = False
        try:
            return self._check(guide_markdown, psalm_number, bundle_text, thinking_out)
        except Exception:
            self._bill_tracker()   # a failed check was still paid for
            raise

    def _check(self, guide_markdown: str, psalm_number: int, bundle_text: str = "",
              thinking_out: Optional[Path] = None) -> FactCheckResult:
        text = checkable_text(guide_markdown)
        chunks = split_guide_for_checking(text, self.chunk_chars)
        self._log(f"Fact check — Psalm {psalm_number}: {len(text):,} chars in {len(chunks)} chunk(s); "
                  f"bundle {len(bundle_text):,} chars; local {self.model} ({self.effort}), "
                  f"web {self.web_model if self.web_search else 'OFF'}, review {self.review_model or 'OFF'}")
        t0 = time.time()
        self._spent, self._trace, self._gathered, self._verify_counts = {}, [], [], {}
        self._failed_chunks: List[Dict] = []
        # Stage 1: the first chunk alone, to write the bundle into the cache; the rest in parallel.
        local: List[Optional[List[Dict]]] = [None] * len(chunks)
        evid = [shared_evidence(ch["text"], bundle_text, self.db_path, verses=chunk_verses(ch["text"]) or None,
                                psalm=psalm_number)
                for ch in chunks]
        self._log("  evidence per chunk: " + ", ".join(f"{len(e):,}" for e in evid) + " chars")
        with ThreadPoolExecutor(max_workers=max(self.parallel, len(chunks))) as ex:
            futs = {ex.submit(self._local_chunk_safe, psalm_number, ch, bundle_text, i + 1, len(chunks),
                              evid[i]): i for i, ch in enumerate(chunks)}
            for f, i in futs.items():
                try:
                    local[i] = f.result()
                except Exception as e:  # one chunk must never sink the rest (Session 387)
                    self._log(f"  local {i + 1}/{len(chunks)} [{chunks[i]['label']}] FAILED: {str(e)[:200]}")
                    self._failed_chunks.append({"chunk": chunks[i]["label"], "error": str(e)[:300]})
                    local[i] = []
        runs = [r for rs in local for r in rs]
        local_recs = validate_records([r for res in runs for r in res["records"]], text,
                                      allowed=VERDICTS + ("needs_web",))

        need_web = [r for r in local_recs if r["verdict"] == "needs_web"]
        contra = [r for r in local_recs if r["verdict"] == "contradicted"]
        web_recs: List[Dict] = []
        if need_web and self.web_search and self.web_model:
            web_runs = self._claims_stage("web", psalm_number, need_web, bundle_text)
            runs += web_runs
            web_recs = validate_records([r for res in web_runs if not res["label"].startswith("gather")
                                         for r in res["records"]], text)
        elif need_web:
            web_recs = [dict(r, verdict="unverifiable") for r in need_web]
        rev_recs: List[Dict] = []
        if contra and self.review_model:
            rev_runs = self._claims_stage("review", psalm_number, contra, bundle_text)
            runs += rev_runs
            rev_recs = validate_records([r for res in rev_runs for r in res["records"]], text)
        records = merge_stage_results(local_recs, web_recs, rev_recs,
                                      reviewed=bool(contra and self.review_model))
        checked_by = {"local": f"{self.model} ({self.effort}), no web",
                      "web": (f"{self.web_judge_model} ({self.web_judge_effort}) judging passages gathered "
                              f"by {self.web_model} ({self.web_effort}) with web search"
                              if self.web_judge_model else f"{self.web_model} ({self.web_effort}) with web search"),
                      "review": f"{self.review_model} ({self.review_effort})"}
        for i, rec in enumerate(records, 1):
            rec["id"] = f"C{i}"
            rec["checked_by"] = checked_by.get(rec.get("stage", "local"), "")
            if rec.get("verdict") != "supported":   # the copy editor needs the whole sentence
                full = expand_sentence(rec.get("sentence", ""), text)
                if full != rec.get("sentence"):
                    rec["sentence"], rec["sentence_expanded"] = full, True

        usage, token_cost, searches, fcalls = _empty_usage(), 0.0, 0, 0
        for m, v in self._spent.items():
            for k in usage:
                usage[k] += v["usage"].get(k, 0)
            token_cost += price_tokens(m, input_tokens=v["usage"]["input"], output_tokens=v["usage"]["output"],
                                       thinking_tokens=v["usage"]["reasoning"],
                                       cached_input_tokens=v["usage"]["cached"],
                                       cache_write_tokens=v["usage"].get("cache_write", 0))
            searches += v["searches"]
        fcalls = sum(r["fcalls"] for r in runs)
        per_stage: Dict[str, Dict] = {}
        for r in runs:
            st = per_stage.setdefault(r["label"].split()[0], {"model": r["model"], "usage": _empty_usage(),
                                                               "billed": {}, "searches": 0, "tools": {}})
            for k in st["usage"]:
                st["usage"][k] += r["usage"].get(k, 0)
            for row, u in _billed(r).items():
                b = st["billed"].setdefault(row, _empty_usage())
                for k in b:
                    b[k] += u.get(k, 0)
            st["searches"] += r["searches"]
            for name, c in r.get("tool_counts", {}).items():
                st["tools"][name] = st["tools"].get(name, 0) + c
        for st in per_stage.values():
            st["cost_usd"] = round(self._cost_of(st["billed"], st["searches"]), 4)
        stages = {
            "local": {"claims": len(local_recs), "needs_web": len(need_web), "contradicted": len(contra)},
            "per_stage": per_stage,
            "per_model": {m: {"usage": v["usage"], "searches": v["searches"],
                              "cost_usd": round(self._price(m, v["usage"], v["searches"]), 4)}
                          for m, v in self._spent.items()},
        }
        gem_q = sum(v["searches"] for m, v in self._spent.items() if m.startswith("gemini-"))
        stages["gemini_search_queries"] = gem_q
        stages["gemini_search_cost_if_paid"] = round(gem_q * GEMINI_SEARCH_USD_PER_QUERY_PAID, 4)
        search_cost = (searches - gem_q) * WEB_SEARCH_USD_PER_CALL
        self._bill_tracker()
        telemetry = {
            "failed_chunks": self._failed_chunks,
            "runs": [{k: r.get(k) for k in ("label", "model", "effort", "seconds", "status", "usage",
                                             "searches", "fcalls", "tool_counts", "truncated", "superseded")}
                     | {"records": len(r["records"]),
                        "billed_as": sorted(_billed(r)),
                        "cost_usd": round(self._cost_of(_billed(r), r["searches"]), 4)}
                     for r in runs],
            "trace": self._trace,
            "gathered": self._gathered,
            "page_check": getattr(self, "_verify_counts", {}),
            "prefetched_evidence": [
                {"chunk": ch["label"], "chars": len(evid[i]),
                 "commentator_entries": len(_COMMENTARY_SECTION.findall(evid[i])),
                 "cited_verses": cited_refs(ch["text"])}
                for i, ch in enumerate(chunks)],
            "models": {"local": [self.model, self.effort], "web_gather": [self.web_model, self.web_effort],
                       "web_judge": [self.web_judge_model, self.web_judge_effort],
                       "review": [self.review_model, self.review_effort]},
        }
        if thinking_out:
            thinking_out.write_text("\n\n".join(f"## {r['label']} ({r['model']})\n\n{r['thinking']}"
                                                for r in runs), encoding="utf-8")
        return FactCheckResult(records=records, chunks=chunks, usage=usage, web_searches=searches,
                               function_calls=fcalls, cost_usd=token_cost + search_cost,
                               token_cost_usd=token_cost, search_cost_usd=search_cost,
                               seconds=time.time() - t0, model=self.model, effort=self.effort,
                               stages=stages, telemetry=telemetry)


def write_outputs(result: FactCheckResult, psalm_number: int, out_dir: Path, prefix: str = "") -> Dict[str, Path]:
    """<prefix>psalm_NNN_fact_check.json / .md / _prompt.txt in out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{prefix}psalm_{psalm_number:03d}_fact_check"
    meta = result.meta(psalm_number)
    paths = {"json": out_dir / f"{stem}.json", "md": out_dir / f"{stem}.md",
             "prompt": out_dir / f"{stem}_copy_editor_prompt.txt",
             "telemetry": out_dir / f"{stem}_telemetry.json"}
    paths["telemetry"].write_text(json.dumps(result.telemetry, ensure_ascii=False, indent=1), encoding="utf-8")
    paths["json"].write_text(json.dumps({"meta": meta, "claims": result.records}, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    paths["md"].write_text(format_report_markdown(result.records, meta), encoding="utf-8")
    paths["prompt"].write_text(format_copy_editor_prompt(result.records), encoding="utf-8")
    return paths


def load_copy_editor_prompt(report_json: Path) -> str:
    """The copy editor's supplementary block from a saved psalm_NNN_fact_check.json.
    Re-validates, so a hand-edited or older report cannot smuggle an
    evidence-free `contradicted` through."""
    data = json.loads(Path(report_json).read_text(encoding="utf-8"))
    records = validate_records(data.get("claims", []) if isinstance(data, dict) else data)
    return format_copy_editor_prompt(records)


def combine_supplementary(*blocks: Optional[str]) -> Optional[str]:
    """Join the citation report and the fact-check report for supplementary_prompt."""
    parts = [b.strip("\n") for b in blocks if b and b.strip()]
    return "\n\n".join(parts) if parts else None
