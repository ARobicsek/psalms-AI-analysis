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

Model: gpt-6-sol on the OpenAI Responses API, reasoning effort `high`, a
different family from the writer so it does not share the writer's false
memories. Tools:
  - OpenAI's built-in web search (outside-the-Bible claims);
  - get_verse(ref)          tanakh.db when present, else Sefaria;
  - get_commentary(c, ref)  the research bundle first, else Sefaria;
  - search_tanakh(hebrew)   occurrence lists for "only here" claims
                            (tanakh.db when present, else Sefaria's search).

The guide is checked in section-aligned CHUNKS, each call carrying the whole
research bundle as a cached prefix (bundle + instructions first, excerpt last),
so every chunk after the first reads the ~130K-token bundle at the cache rate.

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

DEFAULT_MODEL = "gpt-6-sol"
DEFAULT_EFFORT = "high"
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
        con = sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True)
        try:
            return con.execute("SELECT COUNT(*) FROM verses").fetchone()[0] > 0
        finally:
            con.close()
    except sqlite3.Error:
        return False


def _db_rows(db_path: Path, sql: str, params=()) -> list:
    con = sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True)
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


def validate_records(raw: List[Dict], guide: str = "") -> List[Dict]:
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
        if rec["verdict"] not in VERDICTS:
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

INSTRUCTIONS = """## YOUR TASK: FACT-CHECK AN EXCERPT OF THE GUIDE

You are the fact-checker for a study guide on Psalm {psalm}, written for an educated general
audience by an AI writer who worked from the research materials above AND from its own memory.
Find the checkable factual claims in the EXCERPT below and verify each against evidence. You do
not edit prose, judge style, or assess interpretations.

### What to list (every one; skip common knowledge)
- QUOTATIONS: biblical verses (Hebrew or English), rabbinic texts, commentators, liturgy, poems,
  inscriptions, classical authors. Check the wording AND the attribution (who; which work,
  verse, section, line).
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
- Anything that looks quoted from memory.
Do NOT list interpretations, figures of speech, the guide's own arguments, or claims about what
the poem "does". For a flagged conjecture ("perhaps", "may"), list only the facts it rests on.

### How to verify (cheapest source first)
1. The RESEARCH MATERIALS above: the psalm text, commentators' full entries, lexicons,
   concordance results, the literary-echoes dossier.
2. get_verse(ref) for any biblical verse; search_tanakh(hebrew) for occurrences;
   get_commentary(commentator, ref) for a commentary entry not in the materials.
3. Web search for claims outside the Bible and the commentators (classical authors,
   inscriptions, poems, history, dates). Prefer primary texts and standard references.
Batch your tool calls: request several lookups at once when you can.

### Verdicts
- supported: the evidence says what the guide says. Quote it.
- contradicted: the evidence says something materially different. You MUST quote the source
  text that contradicts the claim and name the source (ref or URL). If you cannot quote such
  evidence, the verdict is unverifiable. Give a suggested_fix: the smallest change to the
  guide's sentence that makes it true, keeping its style, figures and argument.
- unverifiable: you found no evidence either way. Never mark a claim contradicted because it
  is unfamiliar to you or on memory alone.
Be exacting about near-misses that matter (a wrong verse number, a misattributed line, a count
off by one, a reading presented backwards or split in two). Be relaxed about ones that don't: a
translation worded differently from a published one that renders the original fairly is
supported (say so), and a paraphrase presented as paraphrase is fine.

### Output
Return JSON matching the schema. `sentence` is the full sentence containing the claim, copied
EXACTLY from the excerpt. One record per distinct claim; a sentence with two claims gets two
records. `location` is the section the claim is in (e.g. "Introduction", "Liturgy",
"Verse 11"). For supported and unverifiable claims set suggested_fix to null.
"""

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
]


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

    def meta(self, psalm: int) -> Dict:
        return {"psalm": psalm, "model": self.model, "effort": self.effort,
                "web_searches": self.web_searches, "function_calls": self.function_calls,
                "cost_usd": self.cost_usd, "token_cost_usd": self.token_cost_usd,
                "search_cost_usd": self.search_cost_usd, "usage": self.usage,
                "seconds": round(self.seconds), "chunks": [c["label"] for c in self.chunks],
                "verdicts": verdict_counts(self.records)}


class FactChecker:
    def __init__(self, model: str = DEFAULT_MODEL, effort: str = DEFAULT_EFFORT,
                 db_path: Optional[Path] = Path("database/tanakh.db"), logger=None,
                 cost_tracker=None, client=None, chunk_chars: int = DEFAULT_CHUNK_CHARS,
                 web_search: bool = True, parallel: int = 3,
                 budget_check: Optional[Callable[[float], None]] = None):
        if not model.startswith("gpt-"):
            raise ValueError("FactChecker runs on the OpenAI Responses API; use a gpt-* model")
        self.model, self.effort = model, effort
        self.db_path = Path(db_path) if db_path else None
        self.logger = logger
        self.cost_tracker = cost_tracker
        self.chunk_chars = chunk_chars
        self.web_search = web_search
        self.parallel = max(1, parallel)
        self.budget_check = budget_check
        if client is None:
            from openai import OpenAI
            client = OpenAI(timeout=1800, max_retries=2)
        self.client = client

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
        return {"error": f"unknown tool {name}"}

    def _tools(self) -> List[Dict]:
        return ([{"type": "web_search"}] if self.web_search else []) + FUNCTION_TOOLS

    # -- one chunk -------------------------------------------------------------
    def _check_chunk(self, psalm: int, chunk: Dict, bundle: str, idx: int, n: int) -> Dict:
        label = f"chunk {idx}/{n} [{chunk['label']}]"
        content = []
        if bundle:
            content.append({"type": "input_text", "text": bundle})
        content.append({"type": "input_text", "text": INSTRUCTIONS.format(psalm=psalm)})
        content.append({"type": "input_text",
                        "text": f"## EXCERPT ({chunk['label']})\n\n{chunk['text']}"})
        common = dict(model=self.model, tools=self._tools(),
                      reasoning={"effort": self.effort, "summary": "auto"},
                      text={"format": {"type": "json_schema", "name": "fact_check",
                                       "schema": RECORD_SCHEMA, "strict": True}},
                      max_output_tokens=64000, prompt_cache_key=f"fact-check-ps{psalm}")
        usage = {"input": 0, "cached": 0, "output": 0, "reasoning": 0}
        searches = fcalls = 0
        summaries: List[str] = []
        t0 = time.time()
        resp = self._create(input=[{"role": "user", "content": content}], **common)
        for rnd in range(MAX_TOOL_ROUNDS + 1):
            u = resp.usage
            cached = getattr(getattr(u, "input_tokens_details", None), "cached_tokens", 0) or 0
            rsn = getattr(getattr(u, "output_tokens_details", None), "reasoning_tokens", 0) or 0
            usage["input"] += u.input_tokens - cached
            usage["cached"] += cached
            usage["output"] += u.output_tokens - rsn
            usage["reasoning"] += rsn
            calls = []
            for it in resp.output:
                if it.type == "web_search_call":
                    searches += 1
                elif it.type == "function_call":
                    calls.append(it)
                elif it.type == "reasoning":
                    summaries += [s.text for s in (it.summary or [])]
            if self.budget_check:
                self.budget_check(self._price(usage, searches))
            if not calls:
                break
            fcalls += len(calls)
            outputs = []
            for c in calls:
                try:
                    args = json.loads(c.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = self._run_tool(c.name, args, bundle)
                outputs.append({"type": "function_call_output", "call_id": c.call_id,
                                "output": json.dumps(result, ensure_ascii=False)[:20000]})
            self._log(f"  {label}: round {rnd + 1}, {len(calls)} lookup(s), {searches} search(es) so far")
            extra = {"tool_choice": "none"} if rnd + 1 >= MAX_TOOL_ROUNDS else {}
            resp = self._create(previous_response_id=resp.id, input=outputs, **common, **extra)
        text = resp.output_text or ""
        status = getattr(resp, "status", "completed")
        records = parse_fact_check_json(text) if text.strip() else []
        self._log(f"  {label}: {len(records)} claims, {searches} searches, {fcalls} lookups, "
                  f"{time.time() - t0:.0f}s, status={status}")
        return {"records": records, "usage": usage, "searches": searches, "fcalls": fcalls,
                "status": status, "thinking": "\n\n".join(summaries), "label": chunk["label"]}

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
                time.sleep(10 * (attempt + 1))
        raise RuntimeError(f"fact-check call failed: {last}")

    def _price(self, usage: Dict, searches: int) -> float:
        return price_tokens(self.model, input_tokens=usage["input"], output_tokens=usage["output"],
                            thinking_tokens=usage["reasoning"], cached_input_tokens=usage["cached"]) \
            + searches * WEB_SEARCH_USD_PER_CALL

    # -- public ---------------------------------------------------------------
    def check(self, guide_markdown: str, psalm_number: int, bundle_text: str = "",
              thinking_out: Optional[Path] = None) -> FactCheckResult:
        text = checkable_text(guide_markdown)
        chunks = split_guide_for_checking(text, self.chunk_chars)
        self._log(f"Fact check — Psalm {psalm_number}: {len(text):,} chars in {len(chunks)} chunk(s); "
                  f"bundle {len(bundle_text):,} chars; model {self.model} ({self.effort})")
        t0 = time.time()
        results: List[Optional[Dict]] = [None] * len(chunks)
        # First chunk alone, to write the bundle into the cache; the rest in parallel.
        results[0] = self._check_chunk(psalm_number, chunks[0], bundle_text, 1, len(chunks))
        if len(chunks) > 1:
            with ThreadPoolExecutor(max_workers=self.parallel) as ex:
                futs = {ex.submit(self._check_chunk, psalm_number, ch, bundle_text, i + 1, len(chunks)): i
                        for i, ch in enumerate(chunks) if i > 0}
                for f, i in futs.items():
                    results[i] = f.result()
        usage = {"input": 0, "cached": 0, "output": 0, "reasoning": 0}
        raw, searches, fcalls = [], 0, 0
        for r in results:
            for k in usage:
                usage[k] += r["usage"][k]
            searches += r["searches"]
            fcalls += r["fcalls"]
            raw += r["records"]
        records = validate_records(raw, text)
        for i, rec in enumerate(records, 1):
            rec["id"] = f"C{i}"
        token_cost = price_tokens(self.model, input_tokens=usage["input"], output_tokens=usage["output"],
                                  thinking_tokens=usage["reasoning"], cached_input_tokens=usage["cached"])
        search_cost = searches * WEB_SEARCH_USD_PER_CALL
        if self.cost_tracker is not None:
            self.cost_tracker.add_usage(self.model, input_tokens=usage["input"], output_tokens=usage["output"],
                                        thinking_tokens=usage["reasoning"], cache_read_tokens=usage["cached"])
        if thinking_out:
            thinking_out.write_text("\n\n".join(f"## {r['label']}\n\n{r['thinking']}" for r in results),
                                    encoding="utf-8")
        return FactCheckResult(records=records, chunks=chunks, usage=usage, web_searches=searches,
                               function_calls=fcalls, cost_usd=token_cost + search_cost,
                               token_cost_usd=token_cost, search_cost_usd=search_cost,
                               seconds=time.time() - t0, model=self.model, effort=self.effort)


def write_outputs(result: FactCheckResult, psalm_number: int, out_dir: Path, prefix: str = "") -> Dict[str, Path]:
    """<prefix>psalm_NNN_fact_check.json / .md / _prompt.txt in out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{prefix}psalm_{psalm_number:03d}_fact_check"
    meta = result.meta(psalm_number)
    paths = {"json": out_dir / f"{stem}.json", "md": out_dir / f"{stem}.md",
             "prompt": out_dir / f"{stem}_copy_editor_prompt.txt"}
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
