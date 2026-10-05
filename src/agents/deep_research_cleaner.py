"""
Deep-research cleanup (Session 393): apply an independent check to a Gemini research
report BEFORE the report enters the research bundle.

Workflow (the author's, in Gemini, free): one chat writes
`data/deep_research/psalm_NNN_deep_research.txt`; a fresh chat, told the report contains
errors, writes `psalm_NNN_deep_research_check.txt` (CONFIRMED / WRONG / NOT CONFIRMED per
claim, with corrections). This module has a small model turn the check into FIND/REPLACE
edits on the report, and Python applies them (`copy_editor.apply_edit_list`), so nothing
the check does not address can change. The result is
`psalm_NNN_deep_research_clean.txt` + `psalm_NNN_deep_research_clean_log.md`, and the
bundle uses the clean file whenever it is newer than both inputs.

Why a separate step and not "give the writer both files": synthesis discovery, the writer
and the fact checker all read the bundle; each would have to reconcile a wrong claim on one
page with its correction on another. On Ps 78 the worst error (the Old Deluder Satan Act)
was a TOP FINDING and its rebuttal item 7 of the check.

Rules the prompt enforces (Ps 78, S393, why each exists):
  - WRONG -> the corrected fact, tagged [corrected by check]; no correction -> delete.
  - NOT CONFIRMED -> tag [unconfirmed]; the claim stays (it may be true).
  - CONFIRMED -> untouched. The checker's own "quotations" are NOT copied in: several were
    generated (a Selig page, a Schuetz catalogue entry), and the checker makes its own
    errors ("the Shulchan Arukh has no chapter 237" -- it does), so an addendum may
    correct the check and wins over it.
Two of those rules are also enforced in code (`guard_edit_list`, S396), because on Ps 79 the
model broke them: a placeholder-only replacement (`</DEL>`) is a deletion, and a correction
that quotes the CHECK is withheld and the original marked [unconfirmed] instead. Cost of the
second guard, measured on Ps 79: it caught all five copied quotations and also one correction
that quoted the psalm in the checker's words ("to the beasts of the earth", 1 Macc 7:17).

Model (Ps 78, S393, same report and check): Sonnet 5.5 in one pass, effort low, 7.0 cents,
fixed every WRONG item everywhere it appeared and added nothing. Haiku 4.5 needed a second
"sweep" pass (5.1 cents) and still left a softened Old Deluder claim, over-tagged two bullets
and invented "an Ashkenazic custom"; gpt-6-luna (0.3 cents) left TOP FINDING #11 untouched.
Cost: the input is counted first (free endpoint, or a 2-chars-a-token estimate for OpenAI)
and max_tokens is cut so input + the most output we allow stays under MAX_COST_USD. When a
long report leaves Sonnet less than MIN_SINGLE_PASS_OUTPUT tokens, the run falls back to
Haiku with the sweep; if even that cannot fit, the call is refused.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple

from src.agents.copy_editor import apply_edit_list
from src.utils.cost_tracker import price_tokens, resolve_pricing

logger = logging.getLogger(__name__)

DEEP_RESEARCH_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "deep_research"
MODEL = "claude-sonnet-5-5"
FALLBACK_MODEL = "claude-haiku-4-5-20251001"
MAX_COST_USD = 0.10
MIN_SINGLE_PASS_OUTPUT = 4000             # Sonnet's Ps 78 edit list: 3,049 tokens incl. thinking
SWEEP_MODELS = {FALLBACK_MODEL}           # Haiku misses repeats without a second pass (Ps 78)
LOW_EFFORT_MODELS = {"claude-sonnet-5-5", "claude-sonnet-5"}
MAX_OUTPUT_TOKENS = 12000

_INTRO = """You apply an independent fact-check to a research report about a psalm. The report will be read by a writer who cannot check it, so a wrong claim left in will be printed.

You receive the REPORT and the CHECK. The CHECK lists claims from the REPORT with a verdict (CONFIRMED, WRONG, NOT CONFIRMED) and, for WRONG ones, the correction. It may end with an ADDENDUM that corrects the CHECK itself; where they disagree, the ADDENDUM wins.
"""

OUTPUT_FORMAT = """OUTPUT: return ONLY a "## Changes" section. Number each change, start with the verdict in square brackets, say where and what, then give the exact edit:

## Changes
1. [WRONG] **Jewish practice, Ma'ariv**: wrong source (Berakhot 4b) replaced with Tur OC 237 and its two reasons.
<<<FIND
the original text, copied character for character from the REPORT (Hebrew, punctuation, markdown and all), long enough to occur only once -- usually the whole sentence or bullet
===
the text that replaces it
>>>

- One FIND/REPLACE block per place changed; a change that touches two places gets two blocks under one number.
- Copy each FIND from the REPORT; never retype it from memory. A FIND that does not match the REPORT exactly is not applied.
- To delete, leave the text after === empty.
- If nothing needs changing, return "## Changes" followed by "No changes required."
"""

SYSTEM_PROMPT = _INTRO + """
Turn the CHECK into edits on the REPORT:

1. WRONG: find EVERY place in the REPORT that makes the wrong claim. The TOP FINDINGS list restates claims from the numbered sections below it, so most claims appear at least twice: search the TOP FINDINGS, every section, and the closing lists, and edit each place. Replace the wrong part with the corrected fact as the CHECK states it, briefly, in the REPORT's own style, and end the corrected sentence or bullet with " [corrected by check]". Keep any source citation that is still right; replace a wrong citation with the right one from the CHECK. If the CHECK shows the claim is false and gives no replacement fact, delete the claim (the whole bullet if nothing true is left in it).
2. NEVER downgrade a WRONG claim to [unconfirmed], and never reword it into a vaguer version of the same claim. If the CHECK says it is false, the false part goes.
3. NOT CONFIRMED: leave the claim and add " [unconfirmed]" at the end of its sentence or bullet, in every place it appears.
4. CONFIRMED: change nothing.
5. Change nothing the CHECK does not address. Do not add facts the CHECK does not give. Do not copy the CHECK's long quotations into the REPORT; a short corrected citation (work and section) is enough. Never touch Hebrew or Greek you are not correcting.
6. If a verdict is about a claim you cannot find in the REPORT, skip it and say so in the change list (no FIND/REPLACE block for it).

""" + OUTPUT_FORMAT

# Pass 2 (the sweep). On Ps 78 the first Haiku pass made one edit per check item, so a claim
# the TOP FINDINGS restated stayed wrong in the body (the 13 x 3 lashes, the Old Deluder Act),
# and it once turned a WRONG claim into a softer one tagged [unconfirmed]. The sweep re-reads
# the corrected report against the check, inside what is left of the cost cap.
SWEEP_PROMPT = _INTRO + """
The REPORT below has ALREADY been corrected once against the CHECK; corrected places end with [corrected by check] or [unconfirmed]. Your job is to find what that pass missed:

1. Any sentence or bullet, anywhere in the REPORT, that still states a claim the CHECK marks WRONG, in any wording, including a softened, hedged or [unconfirmed] version of it. Correct it as the CHECK says (end with " [corrected by check]"), or delete it if the CHECK gives no replacement fact.
2. Any place that states a NOT CONFIRMED claim without " [unconfirmed]".
3. Leave every other sentence alone, including all places already corrected correctly.

""" + OUTPUT_FORMAT


@dataclass
class Paths:
    raw: Path
    check: Path
    clean: Path
    log: Path


def paths(psalm: int, directory: Path = DEEP_RESEARCH_DIR) -> Paths:
    stem = f"psalm_{psalm:03d}_deep_research"
    d = Path(directory)
    return Paths(d / f"{stem}.txt", d / f"{stem}_check.txt", d / f"{stem}_clean.txt",
                 d / f"{stem}_clean_log.md")


def clean_is_current(p: Paths) -> bool:
    """The clean file exists and is at least as new as the report and the check."""
    if not p.clean.exists():
        return False
    t = p.clean.stat().st_mtime
    return all(t >= f.stat().st_mtime for f in (p.raw, p.check) if f.exists())


def needs_cleaning(psalm: int, directory: Path = DEEP_RESEARCH_DIR) -> bool:
    p = paths(psalm, directory)
    return p.raw.exists() and p.check.exists() and not clean_is_current(p)


def build_user_message(report: str, check: str) -> str:
    return f"<REPORT>\n{report.strip()}\n</REPORT>\n\n<CHECK>\n{check.strip()}\n</CHECK>"


def output_budget(input_tokens: int, max_cost: float = MAX_COST_USD, model: str = MODEL,
                  ceiling: int = MAX_OUTPUT_TOKENS) -> int:
    """The largest max_tokens that keeps input + output under `max_cost` (0 = cannot afford)."""
    price = resolve_pricing(model)
    left = max_cost - input_tokens * price["input"] / 1e6
    if left <= 0:
        return 0
    return max(0, min(ceiling, int(left * 1e6 / price["output"])))


def demote_headings(text: str, top: int = 3) -> str:
    """Shift every markdown heading down so the shallowest is `top` (###). The report sits
    under the bundle's '## Deep Web Research'; a '#'/'##' inside it ends that section for
    every reader that splits on '## ' (the trimmer, the pipeline's section counts)."""
    levels = [len(m.group(1)) for m in re.finditer(r"^(#{1,6})\s", text, re.M)]
    if not levels or min(levels) >= top:
        return text
    shift = top - min(levels)
    return re.sub(r"^(#{1,6})(?=\s)", lambda m: "#" * min(6, len(m.group(1)) + shift), text, flags=re.M)


@dataclass
class CleanResult:
    status: str                     # "cleaned" | "skipped" | "refused" | "failed"
    changes: str = ""
    stats: Dict = field(default_factory=dict)
    cost: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    message: str = ""
    model: str = ""


@dataclass
class CallResult:
    text: str
    fresh_in: int          # uncached input
    cached_in: int
    write_in: int          # OpenAI cache writes (GPT-5.6+), 0 for Claude
    out: int               # visible output (excludes reasoning for OpenAI)
    reasoning: int         # OpenAI reasoning; Claude thinking is already inside `out`
    cut_off: bool
    cost: float

    @property
    def input_tokens(self) -> int:
        return self.fresh_in + self.cached_in + self.write_in

    @property
    def output_tokens(self) -> int:
        return self.out + self.reasoning


def _is_openai(model: str) -> bool:
    return model.startswith("gpt-")


def _make_client(model: str):
    if _is_openai(model):
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY not set")
        from openai import OpenAI
        return OpenAI(timeout=1800)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    import anthropic
    return anthropic.Anthropic(timeout=600)


def _count_input(client, model: str, system: str, user: str) -> int:
    if _is_openai(model):
        # No free counting endpoint: assume 2 characters a token (Hebrew-heavy text runs
        # ~2.5-3); over-counting only makes the cost cap stricter.
        return (len(system) + len(user)) // 2
    return client.messages.count_tokens(
        model=model, system=system, messages=[{"role": "user", "content": user}]).input_tokens


def _call(client, model: str, system: str, report: str, check: str, max_cost: float) -> Optional[CallResult]:
    """One edit-list call, or None when `max_cost` cannot cover the input plus 1,000 output
    tokens (nothing is sent then)."""
    user = build_user_message(report, check)
    budget = output_budget(_count_input(client, model, system, user), max_cost, model)
    if budget < 1000:
        return None
    if _is_openai(model):
        from src.utils.openai_usage import split_input_tokens, split_output_tokens
        r = client.responses.create(model=model, instructions=system, input=user,
                                    max_output_tokens=budget, reasoning={"effort": "low"})
        fresh, cached, write = split_input_tokens(r.usage)
        out, reasoning = split_output_tokens(r.usage)
        cost = price_tokens(model, input_tokens=fresh, output_tokens=out, thinking_tokens=reasoning,
                            cached_input_tokens=cached, cache_write_tokens=write)
        return CallResult(r.output_text or "", fresh, cached, write, out, reasoning,
                          getattr(r, "status", "completed") == "incomplete", cost)
    kw = dict(model=model, max_tokens=budget, system=system, messages=[{"role": "user", "content": user}])
    if model in LOW_EFFORT_MODELS:
        kw["output_config"] = {"effort": "low"}  # an edit list needs little thinking; keep it inside the cap
    resp = client.messages.create(**kw)
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    u = resp.usage
    cost = price_tokens(model, input_tokens=u.input_tokens, output_tokens=u.output_tokens)
    return CallResult(text, u.input_tokens, 0, 0, u.output_tokens, 0, resp.stop_reason == "max_tokens", cost)


# -- two $0 guards on the edit list (Session 396) ---------------------------------------------
# Ps 79: the prompt already said "to delete, leave the text after === empty" and "do not copy
# the CHECK's long quotations into the REPORT", and Sonnet 5.5 broke both. (1) Two deletions
# came back as literal `</DEL>` / `</UNCERTAIN_PLACEHOLDER>` lines, which landed in the report.
# (2) Five corrections carried the checker's own "actual text" (Hossfeld-Zenger p. 305, Calvin,
# Soferim, the Esarhaddon curse, Shimush Tehillim) -- the S393 trap: the checker invents
# quotations -- and the Shimush one reached the printed guide. Code enforces both rules now.
_PLACEHOLDER = re.compile(r"^(?:\s*(?:</?[A-Za-z][\w\-]*\s*/?>|\[(?:DEL|DELETE|DELETED|REMOVE|REMOVED)\]))+\s*$", re.I)
_QUOTED = re.compile(r'"([^"\n]+)"|“([^”\n]+)”|«([^»\n]+)»|„([^“”\n]+)[“”]')
_GERSHAYIM = re.compile(r'(?<=[א-ת])"(?=[א-ת])')   # ע"ט, הקב"ה: not quotation marks
_DR_WORD = re.compile(r"[^\W_]+", re.U)
QUOTE_MIN_WORDS = 5    # Ps 79's shortest imported quotation: "to cast down one's enemies"


def _dr_words(s: str) -> list:
    """Words, lower-cased, with accents and Hebrew points removed."""
    import unicodedata
    s = unicodedata.normalize("NFD", (s or "").lower())
    return _DR_WORD.findall("".join(ch for ch in s if not unicodedata.combining(ch)))


def _ngrams(words: list, n: int) -> set:
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def imported_quotation(repl: str, report: str, check: str, n: int = QUOTE_MIN_WORDS) -> Optional[str]:
    """The first quoted span in `repl` that was copied from the CHECK: at least `n` words in
    quotation marks sharing an `n`-word run with the CHECK that the original REPORT lacks.
    Unquoted wording borrowed from the check (a corrected citation) is not a quotation."""
    check_grams = _ngrams(_dr_words(check), n)
    report_grams = _ngrams(_dr_words(report), n)
    for m in _QUOTED.finditer(_GERSHAYIM.sub("״", repl)):
        span = next(g for g in m.groups() if g is not None)
        grams = _ngrams(_dr_words(span), n)
        if grams & (check_grams - report_grams):
            return span.replace("״", '"')
    return None


def guard_edit_list(response: str, report: str, check: str) -> Tuple[str, Dict]:
    """Rewrite the model's FIND/REPLACE blocks before they are applied (pure). A replacement
    that is only a placeholder tag becomes a deletion; one that imports a quotation from the
    CHECK is withheld and the original text is marked [unconfirmed] instead, with a note in
    the change's own line. `report` is the ORIGINAL report, also for the sweep pass."""
    from src.agents.copy_editor import _EDIT_BLOCK
    counts = {"placeholder_deletions": 0, "quotations_withheld": 0}

    def fix(m: "re.Match") -> str:
        find, repl = m.group(1), m.group(2)
        if repl.strip() and _PLACEHOLDER.match(repl):
            counts["placeholder_deletions"] += 1
            return f"<<<FIND\n{find}\n===\n\n>>>\n*(guard: the placeholder {repl.strip()[:40]} was read as a deletion)*"
        q = imported_quotation(repl, report, check) if find.strip() else None
        if q:
            counts["quotations_withheld"] += 1
            short = " ".join(q.split()[:8]) + ("…" if len(q.split()) > 8 else "")
            marked = find.rstrip() + " [unconfirmed]"
            return (f"<<<FIND\n{find}\n===\n{marked}\n>>>\n*(guard: the correction quoted the check "
                    f"(“{short}”), whose quotations are not trusted; the original is marked [unconfirmed] instead)*")
        return m.group(0)

    return _EDIT_BLOCK.sub(fix, response), counts


def _stats_line(stats: Dict) -> str:
    line = (f"{stats.get('applied', 0)} applied of {stats.get('edits', 0)} "
            f"({stats.get('not_found', 0)} not found, {stats.get('ambiguous', 0)} ambiguous)")
    guards = [f"{stats[k]} {label}" for k, label in (("placeholder_deletions", "placeholder(s) read as deletions"),
                                                    ("quotations_withheld", "quotation(s) from the check withheld"))
              if stats.get(k)]
    return line + (f"; guard: {', '.join(guards)}" if guards else "")


def clean(psalm: int, directory: Path = DEEP_RESEARCH_DIR, cost_tracker=None, client=None,
          max_cost: float = MAX_COST_USD, force: bool = False, model: str = MODEL,
          sweep: Optional[bool] = None) -> CleanResult:
    """Write the clean report and its log. Needs both input files; never raises.

    With the sweep (default for Haiku), pass 1 may spend at most half of `max_cost` and the
    sweep gets what is left; without it pass 1 may spend all of it. Either way the run never
    exceeds `max_cost`."""
    p = paths(psalm, directory)
    if not (p.raw.exists() and p.check.exists()):
        return CleanResult("skipped", message="no report or no check file")
    if not force and clean_is_current(p):
        return CleanResult("skipped", message="clean file is current")
    if sweep is None:
        sweep = model in SWEEP_MODELS
    total = CleanResult("failed")

    def bill(c: CallResult):
        total.cost += c.cost
        total.input_tokens += c.input_tokens
        total.output_tokens += c.output_tokens
        if cost_tracker is not None:
            cost_tracker.add_usage(model=model, input_tokens=c.fresh_in, output_tokens=c.out,
                                   thinking_tokens=c.reasoning, cache_read_tokens=c.cached_in,
                                   cache_write_tokens=c.write_in)

    try:
        report = p.raw.read_text(encoding="utf-8")
        check = p.check.read_text(encoding="utf-8")
        given_client = client
        if client is None:
            client = _make_client(model)
        if not sweep and model != FALLBACK_MODEL:
            n_in = _count_input(client, model, SYSTEM_PROMPT, build_user_message(report, check))
            if output_budget(n_in, max_cost, model) < MIN_SINGLE_PASS_OUTPUT:
                logger.info(f"Deep research cleanup, Psalm {psalm}: {n_in:,} tokens leave {model} too little "
                            f"room under ${max_cost:.2f}; falling back to {FALLBACK_MODEL} with the sweep")
                model, sweep = FALLBACK_MODEL, True
                client = given_client or _make_client(model)
        total.model = model

        first_cap = max_cost / 2 if sweep else max_cost
        first = _call(client, model, SYSTEM_PROMPT, report, check, first_cap)
        if first is None:
            return CleanResult("refused", message=f"the input leaves no room under ${first_cap:.2f} for pass 1")
        bill(first)
        if first.cut_off:
            total.message = "pass 1 edit list was cut off; nothing written"
            return total
        edits1, guard1 = guard_edit_list(first.text, report, check)
        cleaned, changes1, stats1 = apply_edit_list(report, edits1)
        stats1.update(guard1)

        sweep_note, changes2, stats2 = "", "", {}
        if not sweep:
            sweep_note = "No sweep (single pass)."
        else:
            second = _call(client, model, SWEEP_PROMPT, cleaned, check, max_cost - total.cost)
            if second is None:
                sweep_note = "Sweep skipped: not enough of the cost cap left."
            else:
                bill(second)
                if second.cut_off:
                    sweep_note = "Sweep cut off; its edits were NOT applied."
                else:
                    edits2, guard2 = guard_edit_list(second.text, report, check)
                    cleaned, changes2, stats2 = apply_edit_list(cleaned, edits2)
                    stats2.update(guard2)

        p.clean.write_text(cleaned, encoding="utf-8")
        body1 = changes1.replace("## Changes", "").strip()
        body2 = changes2.replace("## Changes", "").strip()
        log = (f"# Deep research cleanup, Psalm {psalm}\n\n"
               f"Model {model}: {total.input_tokens:,} in, {total.output_tokens:,} out, "
               f"${total.cost:.4f} (cap ${max_cost:.2f}).\n\n"
               f"## Pass 1: edits from the check -- {_stats_line(stats1)}\n\n{body1}\n\n"
               f"## Pass 2: sweep for what pass 1 missed")
        log += f" -- {_stats_line(stats2)}\n\n{body2}\n" if (stats2 or body2) else f"\n\n{sweep_note}\n"
        p.log.write_text(log, encoding="utf-8")
        stats = {k: stats1.get(k, 0) + stats2.get(k, 0) for k in set(stats1) | set(stats2)}
        total.status, total.changes, total.stats, total.message = "cleaned", changes1 + changes2, stats, sweep_note
        return total
    except Exception as e:  # a failed cleanup must never stop a pipeline run
        logger.warning(f"Deep research cleanup failed for Psalm {psalm}: {e}")
        total.message = str(e)
        return total


def load_for_bundle(psalm: int, directory: Path = DEEP_RESEARCH_DIR, cost_tracker=None,
                    auto_clean: bool = True) -> Tuple[Optional[str], str]:
    """(content for the bundle or None, kind) where kind is 'checked' (the clean file) or
    'unchecked' (the raw report). Runs the cleanup first when a check file is newer than the
    clean file. Headings are demoted either way."""
    p = paths(psalm, directory)
    if auto_clean and needs_cleaning(psalm, directory):
        r = clean(psalm, directory, cost_tracker=cost_tracker)
        logger.info(f"Deep research cleanup for Psalm {psalm}: {r.status} {r.message}".rstrip())
    if clean_is_current(p) and p.raw.exists():
        text = p.clean.read_text(encoding="utf-8").strip()
        if text:
            return demote_headings(text), "checked"
    if p.raw.exists():
        text = p.raw.read_text(encoding="utf-8").strip()
        if text:
            return demote_headings(text), "unchecked"
    return None, "none"
