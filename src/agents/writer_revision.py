"""
The writer revises its own guide after the fact check (Session 401).

Until Session 401 the copy editor (GPT-5.4, FIND/REPLACE, "the smallest change that makes the
sentence true") made every fact-check correction. It patched the sentence and left the argument
around it, and the seams showed: on Ps 29 a paragraph lost the claim its logic rested on ("the
seven voices are all singular" ... ending in a non sequitur) and Radak gained an aside bolted
into the middle of a sentence. The author: "is there an inexpensive way to have the writer see
the checker issues and then do the rewrite itself?"

So, between the fact check and the copy edit, the writer (Opus 5.5) gets back its own guide and
the claims the checker CONTRADICTED, each with the checker's evidence, and rewrites the whole
paragraph that holds each one. The cheapest form, chosen by the author: no research dossier
(the evidence travels with each correction, and keeping the writer's 230K-token cache warm
through the fact check would cost more than it saves), and only the paragraphs it changes come
back. Effort `high` since its second run: at `medium` (Ps 29, $0.33) it still edited sentence by
sentence in places ("not only ... also ...") and inserted a citation mid-argument.

The guard rails are code, not prompt (the S396 lesson: models break prompt rules):
  * paragraphs are numbered and only prose paragraphs are numbered: verse headers, the Hebrew
    of each verse, translation lines, quoted poems and headings cannot be touched;
  * a replacement is accepted only for a paragraph holding a contradicted claim or the prose
    paragraph next to one in the same section (a cut can break the bridge to a neighbour);
  * a contradicted claim the writer neither rewrote nor explicitly kept, or that sits outside
    any numbered paragraph, goes on to the copy editor exactly as before;
  * the $0 citation check (and its false-positive filter) runs again on the revised text, so a
    quotation the revision got wrong reaches the copy editor (the pipeline does this).

The writer may KEEP a sentence it is sure is right (the checker raises about one false alarm a
run); it must say why, and the editors' report prints the reason for the author.

`print_ready.md` is never overwritten: the editors' report treats a fact check older than it as
stale. The revised text is `psalm_NNN_revised.md`, which the copy editor reads instead.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from src.agents.fact_checker import _norm_ws, _strip_md

REVISION_MODEL = "claude-opus-5-5"
REVISION_EFFORT = "high"       # S401: "medium" still patched sentences; never "max"
REVISION_MAX_TOKENS = 64000

# Sections of print_ready.md the writer sees. The psalm-text table and the methods page are
# left out (they are not the writer's prose, and the table is the bulkiest Hebrew in the file).
_SKIP_SECTION = re.compile(r"^## (Psalm \d+|Methodological)")
_VERSE_HEADER = re.compile(r"^\*\*Verses?\s+\d")
_LATIN = re.compile(r"[A-Za-z]")
_MARKER = re.compile(r"^\s*\[P(\d+)\]\s*(.*)$")
_LOG_HEAD = re.compile(r"^\s*#{1,4}\s*LOG\s*$", re.I)
_LOG_LINE = re.compile(r"^\s*[-*]?\s*\**\s*(C\d+)\**\s*[:—–-]+\s*\**(fixed|kept)\**\b[\s:—–-]*(.*)$", re.I)


# ---------------------------------------------------------------------------
# Paragraphs (pure)
# ---------------------------------------------------------------------------

@dataclass
class Para:
    line: int          # index into the file's lines
    pid: int           # the [Pn] number shown to the writer
    unit: int          # section / verse note it belongs to (neighbours must share it)


def number_paragraphs(text: str) -> Tuple[List[str], List[Para], List[bool]]:
    """(lines, numbered prose paragraphs, shown-to-the-writer mask). print_ready.md has one
    paragraph per line. A paragraph is numbered when it is prose (has a Latin letter) and is not
    a heading, a verse header, a block quote or a rule."""
    lines = text.split("\n")
    paras: List[Para] = []
    shown = [False] * len(lines)
    unit, skipping, started = 0, False, False
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("## "):
            skipping = bool(_SKIP_SECTION.match(s))
            started = True
            unit += 1
        if not started or skipping:
            continue
        shown[i] = True
        if s.startswith("#") or _VERSE_HEADER.match(s):
            if not s.startswith("## "):
                unit += 1
            continue
        if not s or s.startswith((">", "---", "|")) or not _LATIN.search(s):
            continue
        paras.append(Para(line=i, pid=len(paras) + 1, unit=unit))
    return lines, paras, shown


def render_for_writer(lines: List[str], paras: List[Para], shown: List[bool]) -> str:
    tag = {p.line: p.pid for p in paras}
    out = []
    for i, ln in enumerate(lines):
        if shown[i]:
            out.append(f"[P{tag[i]}] {ln}" if i in tag else ln)
    return "\n".join(out).strip()


def _norm(s: str) -> str:
    tr = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})
    return _strip_md(_norm_ws(s)).translate(tr)


def locate(sentence: str, lines: List[str], paras: List[Para]) -> Optional[Para]:
    """The numbered paragraph that holds a claim's sentence (whole, or its first 60 chars)."""
    a = _norm(sentence)
    if not a:
        return None
    for p in paras:
        b = _norm(lines[p.line])
        if a in b or (len(a) > 60 and a[:60] in b):
            return p
    return None


def allowed_pids(flagged: List[Para], paras: List[Para]) -> Dict[int, str]:
    """pid -> why it may change: 'flagged', or 'neighbour' (the prose paragraph just before or
    after a flagged one, in the same section or verse note)."""
    by_pid = {p.pid: p for p in paras}
    ok: Dict[int, str] = {}
    for f in flagged:
        ok[f.pid] = "flagged"
    for f in flagged:
        for q in (f.pid - 1, f.pid + 1):
            n = by_pid.get(q)
            if n and n.unit == f.unit and q not in ok:
                ok[q] = "neighbour"
    return ok


# ---------------------------------------------------------------------------
# The writer's answer (pure)
# ---------------------------------------------------------------------------

def parse_response(text: str) -> Tuple[Dict[int, Optional[List[str]]], Dict[str, Tuple[str, str]]]:
    """({pid: new lines, or None for DELETE}, {claim id: (fixed|kept, note)})."""
    blocks: Dict[int, Optional[List[str]]] = {}
    log: Dict[str, Tuple[str, str]] = {}
    cur: Optional[int] = None
    in_log = False
    for ln in text.split("\n"):
        if _LOG_HEAD.match(ln):
            in_log, cur = True, None
            continue
        if in_log:
            m = _LOG_LINE.match(ln)
            if m:
                log[m.group(1).upper()] = (m.group(2).lower(), m.group(3).strip())
            continue
        m = _MARKER.match(ln)
        if m:
            cur = int(m.group(1))
            rest = m.group(2).strip()
            if rest.upper().strip("*[]() ") == "DELETE":
                blocks[cur] = None
                cur = None
            else:
                blocks[cur] = [rest] if rest else []
            continue
        if cur is not None and ln.strip():
            blocks[cur].append(ln.strip())
    return blocks, log


def apply_changes(lines: List[str], paras: List[Para], blocks: Dict[int, Optional[List[str]]],
                  allowed: Dict[int, str]) -> Tuple[str, List[Dict], List[Dict]]:
    """(revised text, applied changes, rejected changes)."""
    by_pid = {p.pid: p for p in paras}
    new = {}
    applied, rejected = [], []
    for pid, repl in sorted(blocks.items()):
        p = by_pid.get(pid)
        if p is None or pid not in allowed:
            rejected.append({"pid": pid, "reason": "not a paragraph it was allowed to change",
                             "new": "\n".join(repl or [])})
            continue
        old = lines[p.line]
        if repl is not None and not repl:
            rejected.append({"pid": pid, "reason": "empty replacement (DELETE was not written)", "new": ""})
            continue
        bad = [r for r in (repl or []) if r.startswith("#") or _VERSE_HEADER.match(r) or r.startswith("---")]
        if bad:
            rejected.append({"pid": pid, "reason": f"replacement contains a heading or verse header: {bad[0][:80]}",
                             "new": "\n".join(repl)})
            continue
        if repl is not None and "\n".join(repl).strip() == old.strip():
            continue  # returned unchanged
        new[p.line] = repl
        applied.append({"pid": pid, "why_allowed": allowed[pid], "old": old,
                        "new": None if repl is None else "\n".join(repl)})
    out = []
    for i, ln in enumerate(lines):
        if i in new:
            out.extend(new[i] or [])
        else:
            out.append(ln)
    return "\n".join(out), applied, rejected


# ---------------------------------------------------------------------------
# The prompt (pure)
# ---------------------------------------------------------------------------

SYSTEM = """You are the author of a study guide to a psalm, written for one intelligent, curious reader who reads Hebrew and is not a specialist. You read Hebrew poetry with a poet's ear and a scholar's precision. You are now revising your own finished guide."""

INSTRUCTIONS = """A fact checker has checked the guide's claims against the sources: the biblical text, the commentators' own texts, the Talmud and midrash, the prayer books, and the web. It found the claims listed under CORRECTIONS to be wrong. Each comes with the checker's evidence. Fix them yourself, as the author.

For each correction:
- Rewrite the whole paragraph that holds the claim, so that it reads as if you had known the facts from the start. Where the corrected fact no longer supports the point the paragraph was making, change the point or cut it, and repair the logic around it: never leave a sentence whose reason has gone, and never bolt a qualification onto the old sentence.
- Take the new facts only from the evidence given with the correction. Add nothing else new: no new sources, quotations or claims of fact.
- Keep the rest of the paragraph as it was: its other claims, its quotations (the Hebrew and the English), its voice. Every Hebrew quotation keeps its English, and every English quotation of a Hebrew source keeps its Hebrew. Write divine names exactly as the text in front of you spells them.
- You may also change the paragraph just before or just after a flagged one, in the same section, when your fix leaves the link between them broken. Change nothing else.
- If you are certain the checker is wrong, keep your sentence and say why in the log, answering its evidence.
- Never mention the fact check, a correction, or anything behind the guide.

Only numbered paragraphs ([P1], [P2], ...) can be changed.

## OUTPUT

For each paragraph you change, its number on a line of its own, then the whole new paragraph, without the number:

[P12]
The new paragraph.

To remove a paragraph entirely, write `[P12] DELETE`. Then a line `## LOG`, and one line for every correction:
C17: fixed in P12 — what you changed, in a few words
C18: kept — why the checker is wrong

Nothing else: no preamble, no unchanged paragraphs."""


def _clip(s: str, n: int) -> str:
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1] + "…"


def corrections_block(items: List[Tuple[Dict, Para]]) -> str:
    out = []
    for r, p in items:
        out.append(f"{r['id']} — in [P{p.pid}] ({r.get('location', '')})")
        out.append(f"The guide says: \"{_clip(r.get('sentence', ''), 600)}\"")
        if r.get("claim"):
            out.append(f"The claim checked: {r['claim']}")
        if r.get("explanation"):
            out.append(f"Finding: {r['explanation']}")
        for e in r.get("evidence", []):
            q = _clip(e.get("quote") or "", 900)
            src = (e.get("source") or "") + (f" ({e['url']})" if e.get("url") else "")
            out.append(f"Evidence — {src}: \"{q}\"" if q else f"Evidence — {src}")
        if r.get("suggested_fix"):
            out.append(f"The checker's suggested wording (a starting point, not a script): {r['suggested_fix']}")
        out.append("")
    return "\n".join(out).strip()


def build_user_turn(psalm_number: int, guide: str, items: List[Tuple[Dict, Para]]) -> str:
    return (f"# YOUR GUIDE TO PSALM {psalm_number}\n\n{guide}\n\n"
            f"# CORRECTIONS ({len(items)})\n\n{corrections_block(items)}\n\n"
            f"# WHAT TO DO\n\n{INSTRUCTIONS}")


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

@dataclass
class RevisionResult:
    revised_text: str
    applied: List[Dict] = field(default_factory=list)
    rejected: List[Dict] = field(default_factory=list)
    log: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    sent: List[str] = field(default_factory=list)        # claim ids sent to the writer
    unlocated: List[str] = field(default_factory=list)   # contradicted, outside any numbered paragraph
    handled: List[str] = field(default_factory=list)     # fixed (paragraph changed) or explicitly kept
    usage: Dict[str, int] = field(default_factory=dict)
    cost_usd: float = 0.0
    seconds: float = 0.0
    thinking: str = ""
    raw: str = ""

    def to_json(self) -> Dict:
        return {"applied": self.applied, "rejected": self.rejected,
                "log": {k: {"status": v[0], "note": v[1]} for k, v in self.log.items()},
                "sent": self.sent, "unlocated": self.unlocated, "handled": self.handled,
                "usage": self.usage, "cost_usd": round(self.cost_usd, 4), "seconds": round(self.seconds),
                "model": REVISION_MODEL, "effort": REVISION_EFFORT}


def plan(print_ready: str, records: List[Dict]):
    """Everything up to the call: (lines, paras, shown, [(record, para)], unlocated ids)."""
    lines, paras, shown = number_paragraphs(print_ready)
    items, unlocated = [], []
    for r in records:
        if r.get("verdict") != "contradicted":
            continue
        p = locate(r.get("sentence", ""), lines, paras)
        if p is None:
            unlocated.append(r["id"])
        else:
            items.append((r, p))
    return lines, paras, shown, items, unlocated


def handled_ids(items: List[Tuple[Dict, Para]], applied: List[Dict], log: Dict[str, Tuple[str, str]]) -> List[str]:
    changed = {a["pid"] for a in applied}
    return [r["id"] for r, p in items
            if p.pid in changed or log.get(r["id"].upper(), ("", ""))[0] == "kept"]


def remaining_records(records: List[Dict], handled: List[str]) -> List[Dict]:
    """What the copy editor still gets: every record except the contradicted ones the writer
    rewrote or kept (supported / unverifiable stay, so it knows not to touch those facts)."""
    h = set(handled)
    return [r for r in records if not (r.get("verdict") == "contradicted" and r["id"] in h)]


def report_markdown(psalm_number: int, res: RevisionResult, records: List[Dict]) -> str:
    by_id = {r["id"]: r for r in records}
    L = [f"# Psalm {psalm_number}: the writer's revision after the fact check", "",
         f"{REVISION_MODEL} (effort {REVISION_EFFORT}), ${res.cost_usd:.4f}, {round(res.seconds)} s. "
         f"Contradicted claims sent: {len(res.sent)}; handled (rewritten or kept): {len(res.handled)}; "
         f"left for the copy editor: {len(res.sent) - len(res.handled) + len(res.unlocated)} "
         f"({len(res.unlocated)} outside any prose paragraph).", ""]
    L += ["## The writer's log", ""]
    for cid in res.sent:
        st, note = res.log.get(cid.upper(), ("(no log line)", ""))
        L += [f"- **{cid}** ({by_id.get(cid, {}).get('location', '')}): {st}" + (f" — {note}" if note else "")]
    L += [""]
    if res.rejected:
        L += ["## Rejected by code", ""]
        L += [f"- P{r['pid']}: {r['reason']}" for r in res.rejected] + [""]
    L += ["## Paragraphs changed", ""]
    for a in res.applied:
        L += [f"### P{a['pid']} ({a['why_allowed']})", "", "**Before:**", "", a["old"], "", "**After:**", "",
              a["new"] if a["new"] is not None else "*(deleted)*", ""]
    return "\n".join(L)


class WriterRevision:
    def __init__(self, cost_tracker=None, logger=None, model: str = REVISION_MODEL):
        import anthropic
        import os
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"), timeout=1800)
        self.cost_tracker = cost_tracker
        self.logger = logger
        self.model = model

    def _log(self, msg: str, level: str = "info"):
        if self.logger:
            getattr(self.logger, level)(f"[revision] {msg}")

    def _call(self, user: str) -> Tuple[str, str, Dict[str, int], float]:
        from src.utils.model_effort import adaptive_thinking
        kw = {"model": self.model, "max_tokens": REVISION_MAX_TOKENS, "system": SYSTEM,
              "thinking": adaptive_thinking(self.model), "output_config": {"effort": REVISION_EFFORT},
              "messages": [{"role": "user", "content": user}]}
        last = None
        for attempt in range(3):
            try:
                t0 = time.time()
                with self.client.messages.stream(**kw) as stream:
                    msg = stream.get_final_message()
                us = msg.usage
                u = {"input": us.input_tokens or 0, "output": us.output_tokens or 0,
                     "cache_read": getattr(us, "cache_read_input_tokens", 0) or 0,
                     "cache_write": getattr(us, "cache_creation_input_tokens", 0) or 0}
                if self.cost_tracker is not None:
                    self.cost_tracker.add_usage(model=self.model, input_tokens=u["input"],
                                                output_tokens=u["output"], thinking_tokens=0,
                                                cache_read_tokens=u["cache_read"],
                                                cache_write_tokens=u["cache_write"])
                text = "".join(b.text for b in msg.content if b.type == "text")
                thinking = "\n\n".join(b.thinking for b in msg.content if b.type == "thinking" and b.thinking)
                if msg.stop_reason != "end_turn" or not text.strip():
                    raise RuntimeError(f"stop_reason={msg.stop_reason}, text chars={len(text)}")
                return text, thinking, u, time.time() - t0
            except Exception as e:  # billed above if a response came back
                last = e
                self._log(f"attempt {attempt + 1} failed: {str(e)[:200]}", "warning")
                time.sleep(15 * (attempt + 1))
        raise RuntimeError(f"writer revision: all attempts failed: {last}")

    def revise(self, psalm_number: int, print_ready: str, records: List[Dict]) -> RevisionResult:
        from src.utils.cost_tracker import resolve_pricing
        lines, paras, shown, items, unlocated = plan(print_ready, records)
        res = RevisionResult(revised_text=print_ready, unlocated=unlocated, sent=[r["id"] for r, _ in items])
        if not items:
            self._log(f"no contradicted claim inside a prose paragraph ({len(unlocated)} elsewhere); no call")
            return res
        allowed = allowed_pids([p for _, p in items], paras)
        user = build_user_turn(psalm_number, render_for_writer(lines, paras, shown), items)
        self._log(f"{len(items)} contradicted claim(s) in {len({p.pid for _, p in items})} paragraph(s) "
                  f"sent to {self.model} (effort {REVISION_EFFORT}); {len(unlocated)} outside prose; "
                  f"prompt {len(user):,} chars")
        text, thinking, u, secs = self._call(user)
        p = resolve_pricing(self.model) or {}
        res.cost_usd = (u["input"] * p.get("input", 0) + u["output"] * p.get("output", 0)
                        + u["cache_read"] * p.get("cache_read", 0)
                        + u["cache_write"] * p.get("cache_write", 0)) / 1_000_000
        res.usage, res.seconds, res.thinking, res.raw = u, secs, thinking, text
        blocks, res.log = parse_response(text)
        res.revised_text, res.applied, res.rejected = apply_changes(lines, paras, blocks, allowed)
        res.handled = handled_ids(items, res.applied, res.log)
        self._log(f"{len(res.applied)} paragraph(s) rewritten, {len(res.rejected)} rejected; "
                  f"{len(res.handled)}/{len(items)} claims handled; ${res.cost_usd:.4f}, {round(secs)} s; "
                  f"in {u['input']:,}, out {u['output']:,}")
        for r in res.rejected:
            self._log(f"rejected P{r['pid']}: {r['reason']}", "warning")
        return res
