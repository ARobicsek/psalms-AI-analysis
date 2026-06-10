#!/usr/bin/env python3
"""Blind LLM judge + deterministic diff for full-commentary A/B comparisons.

Built for the Session-358 novelty A/B (R1-R6 pipeline changes vs. production),
but generic: it compares an OLD and a NEW final commentary for each psalm,
wherever they live.

Per psalm it produces:
  1. A deterministic report (no LLM): sizes, hedged-conjecture marker counts,
     copy-editor change-log stats, citation-verification issue counts, pipeline
     cost (when the artifacts exist in each arm's directory).
  2. A BLIND judge pass (Claude Opus by default): the two commentaries are
     shuffled into "Commentary A"/"Commentary B" (seeded) so the judge cannot
     know which arm is which. The judge inventories each commentary's
     distinct substantive insights and scores them on novelty / groundedness /
     aha, flags overreach and false profundity, spot-checks verse coverage,
     and names a winner. The saved report unblinds the mapping at the end.

Arm resolution (per psalm N):
  OLD: {old_dir}/psalm_{N:03d}_copy_edited.md, else edited_intro+edited_verses
       in {old_dir}, else the published DOCX "Documents/Psalm study guide/
       Psalm N.docx" (text extracted from word/document.xml).
  NEW: {new_dir}/psalm_{N:03d}_copy_edited.md, else edited_intro+edited_verses.

Usage (local machine — needs ANTHROPIC_API_KEY for the judge step):
    python scripts/evaluate_novelty_ab.py 58 59 60
    python scripts/evaluate_novelty_ab.py 58 --new-dir "output/ab_novelty/psalm_{n}" --seed 7
    python scripts/evaluate_novelty_ab.py 58 59 60 --skip-judge   # deterministic only, $0

Cost: ~$0.8-1.5/psalm for the judge call (two full commentaries in the prompt).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import random
import re
import sys
import zipfile
from pathlib import Path
from typing import Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OLD_DIR_DEFAULT = "output/psalm_{n}"
NEW_DIR_DEFAULT = "output/ab_novelty/psalm_{n}"
OUT_DIR_DEFAULT = "output/ab_novelty/eval"
DOCX_DIR = PROJECT_ROOT / "Documents" / "Psalm study guide"

# Wording that signals a deliberately hedged interpretive claim. Counted, not judged.
HEDGE_MARKERS = [
    "perhaps", "may explain", "may reflect", "suggests", "is best read",
    "one possible", "conjecture", "speculat", "it is tempting",
]

JUDGE_PROMPT = """You are a senior scholar of the Hebrew Psalms acting as a BLIND JUDGE in an
A/B test of a commentary-writing pipeline. Below are two complete published
commentaries on Psalm {psalm_number}, produced by two different pipeline
configurations from substantially the same research base. You do not know
which configuration produced which commentary, and you must not try to guess
(formatting, length, and front-matter may differ for incidental reasons —
ignore them). Judge ONLY the scholarly substance on the page.

The pipeline's goal is commentary rich in insights that are BOTH novel AND
convincing:
- NOVEL = an "aha" a learned reader of Psalms has not already had: an anomaly
  explained, known facts newly linked, a reaching-outward connection
  (intertext / idiom usage / liturgy or reception / sound-as-motive /
  world-literature echo that genuinely illuminates). NOT a restated source
  fact, NOT a dictionary gloss dressed up, NOT a competent summary.
- CONVINCING = evidentially honest and calibrated: real anchors (quoted
  Hebrew, named sources, checkable parallels), claim strength matched to
  evidence, conjecture flagged as conjecture. A thrilling overclaim is a
  failure; so is a true but inert observation.

{psalm_text_block}

═══════════════════════════════════════════════════════════════════════════
## COMMENTARY A
═══════════════════════════════════════════════════════════════════════════

{text_a}

═══════════════════════════════════════════════════════════════════════════
## COMMENTARY B
═══════════════════════════════════════════════════════════════════════════

{text_b}

═══════════════════════════════════════════════════════════════════════════
## YOUR TASK
═══════════════════════════════════════════════════════════════════════════

### Step 1 — Insight inventory (each commentary separately)

For EACH commentary, list its distinct substantive insights — the claims a
reader would remember, not routine glosses or coverage. Cap at 15 per
commentary; if there are more, keep the 15 strongest. For each insight assign
1-5 per dimension (be adversarial — rhetoric must not inflate scores):

- **NOV (novelty):** 1 = standard fare any commentary has; 5 = a connection or
  explanation a learned reader of Psalms will not have met.
- **GRD (groundedness/calibration):** anchors real and sufficient; claim
  strength matched to evidence. A clearly-flagged conjecture with honest
  anchors can score 4-5; an overclaimed certainty cannot. If you can identify
  a likely factual error, score 1-2 and name it.
- **AHA:** does it change how you read a verse or the poem, with that
  obvious-in-hindsight feel? 1 = inert even if true.

Tag each insight:
- **KIND:** INTERNAL (pattern within the psalm's text) or BRIDGING (joins the
  text to something outside it — another biblical text, idiom usage, liturgy/
  reception, sound-vs-choice, comparative literature).
- **VERDICT:** GOLD (a reader's reason to recommend the commentary), GOOD,
  or FILLER.

### Step 2 — Failure audit (each commentary separately)

- **OVERREACH:** sentences whose force depends on an overstated or unflagged
  claim (false "verbatim"/"only place", stretched lexical senses, miscounts,
  unmarked leaps presented as fact). Quote each briefly.
- **FALSE PROFUNDITY:** balanced/epigrammatic sentences that, stripped of
  cadence, only restate a definition or repeat a point. Quote up to 3.
- **LOST HEDGES:** interpretive claims that should be hedged but are worded
  as established fact.

### Step 3 — Coverage spot-check

Pick 4 verses spread across the psalm (include at least one late verse) and
compare treatment quality between the commentaries: does either visibly
under-treat verses (perfunctory lines that merely restate the translation),
and does either over-pad routine material to feign depth?

### Step 4 — Comparison

- **GOLD COUNT** and **BRIDGING-GOLD COUNT** per commentary.
- **BEST-5 MEAN:** mean total score (NOV+GRD+AHA, max 15) of each
  commentary's five strongest insights.
- **OVERREACH COUNT** per commentary.
- **OVERALL:** which commentary should the author publish, and why (4-8
  sentences naming the decisive insights/failures by their labels). Quality
  of the best material outranks volume; calibration failures are heavily
  penalized; do not reward length.

═══════════════════════════════════════════════════════════════════════════
## OUTPUT FORMAT
═══════════════════════════════════════════════════════════════════════════

A readable markdown report:

# Judge report — Psalm {psalm_number}

## Commentary A — insight inventory
| # | insight (short label) | KIND | NOV | GRD | AHA | total | verdict |
(one row per insight)

## Commentary B — insight inventory
(same table)

## Failure audit
### Commentary A
...
### Commentary B
...

## Coverage spot-check
...

## Comparison
<Step-4 analysis in prose + the numbers>

Then, on the FINAL line, a single JSON object (no code fence) exactly like:
{{"psalm": {psalm_number}, "best5_A": <float>, "best5_B": <float>, "gold_A": <int>, "gold_B": <int>, "bridging_gold_A": <int>, "bridging_gold_B": <int>, "overreach_A": <int>, "overreach_B": <int>, "winner": "<A|B|TIE>"}}
"""


# ---------------------------------------------------------------------------
# Arm text resolution
# ---------------------------------------------------------------------------

def _read_md_arm(arm_dir: Path, n: int) -> Optional[Tuple[str, str]]:
    """Return (text, source_description) for an output directory, or None."""
    ce = arm_dir / f"psalm_{n:03d}_copy_edited.md"
    if ce.exists():
        return ce.read_text(encoding="utf-8"), str(ce)
    intro = arm_dir / f"psalm_{n:03d}_edited_intro.md"
    verses = arm_dir / f"psalm_{n:03d}_edited_verses.md"
    if intro.exists() and verses.exists():
        text = (intro.read_text(encoding="utf-8") + "\n\n---\n\n"
                + verses.read_text(encoding="utf-8"))
        return text, f"{intro} + {verses}"
    return None


def _extract_docx_text(docx_path: Path) -> str:
    """Plain-text extraction from a DOCX (word/document.xml, tags stripped)."""
    with zipfile.ZipFile(docx_path) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    xml = re.sub(r"<w:p[ >]", "\n<w:p ", xml)          # paragraph breaks
    xml = re.sub(r"<w:tab[^>]*/>", "\t", xml)
    text = re.sub(r"<[^>]+>", "", xml)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def resolve_arm_text(arm_dir: Path, n: int, allow_docx_fallback: bool) -> Tuple[Optional[str], str]:
    got = _read_md_arm(arm_dir, n)
    if got:
        return got
    if allow_docx_fallback:
        for name in (f"Psalm {n}.docx", f"psalm {n}.docx"):
            p = DOCX_DIR / name
            if p.exists():
                return _extract_docx_text(p), f"{p} (published DOCX fallback)"
    return None, f"NOT FOUND under {arm_dir}"


def strip_changes_section(text: str) -> str:
    """Drop the copy editor's '## Changes' log so the judge sees prose only."""
    idx = text.find("\n## Changes")
    return text[:idx] if idx != -1 else text


# ---------------------------------------------------------------------------
# Deterministic metrics
# ---------------------------------------------------------------------------

def _count_hedges(text: str) -> dict:
    low = text.lower()
    return {m: low.count(m) for m in HEDGE_MARKERS if low.count(m)}


def _changes_stats(arm_dir: Path, n: int) -> dict:
    ce = arm_dir / f"psalm_{n:03d}_copy_edited.md"
    if not ce.exists():
        return {}
    text = ce.read_text(encoding="utf-8")
    idx = text.find("\n## Changes")
    if idx == -1:
        return {}
    changes = text[idx:]
    items = re.findall(r"^\s*\d+\.\s+(.*)$", changes, re.M)
    def hits(pat):
        return sum(1 for it in items if re.search(pat, it, re.I))
    return {
        "total_changes": len(items),
        "citation_fixes": hits(r"\[CITATION FIX\]"),
        "removals": hits(r"\bremov"),
        "conjecture_touching": hits(r"conjectur|perhaps|hedge|speculat"),
        "parallel_or_echo_touching": hits(r"parallel|comparison|echo|allusion"),
    }


def _citation_issue_count(arm_dir: Path, n: int) -> Optional[int]:
    rep = arm_dir / f"psalm_{n:03d}_citation_verification.md"
    if not rep.exists():
        return None
    text = rep.read_text(encoding="utf-8")
    m = re.search(r"(\d+)\s+issue", text)
    if m:
        return int(m.group(1))
    return text.count("NOT_SUBSTRING")


def _cost_total(arm_dir: Path, n: int) -> Optional[float]:
    cj = arm_dir / f"psalm_{n:03d}_cost.json"
    if not cj.exists():
        return None
    try:
        data = json.loads(cj.read_text(encoding="utf-8"))
    except Exception:
        return None
    for key in ("total_cost", "total_cost_usd", "grand_total"):
        if isinstance(data, dict) and key in data:
            return float(data[key])
    if isinstance(data, dict):  # sum any per-model cost fields found
        total = 0.0
        found = False
        for v in data.values():
            if isinstance(v, dict) and "cost" in v:
                total += float(v["cost"]); found = True
        if found:
            return total
    return None


def deterministic_report(n: int, old_dir: Path, new_dir: Path,
                         old_text: str, new_text: str,
                         old_src: str, new_src: str) -> str:
    lines = [f"## Deterministic metrics — Psalm {n}", ""]
    lines.append(f"- OLD source: `{old_src}`")
    lines.append(f"- NEW source: `{new_src}`")
    lines.append("")
    lines.append("| metric | OLD | NEW |")
    lines.append("|---|---|---|")
    lines.append(f"| characters (prose, changes-log stripped) | {len(old_text):,} | {len(new_text):,} |")
    lines.append(f"| words | {len(old_text.split()):,} | {len(new_text.split()):,} |")
    oh, nh = _count_hedges(old_text), _count_hedges(new_text)
    lines.append(f"| hedge markers (total) | {sum(oh.values())} | {sum(nh.values())} |")
    co, cn = _citation_issue_count(old_dir, n), _citation_issue_count(new_dir, n)
    lines.append(f"| citation issues reported | {co if co is not None else 'n/a'} | {cn if cn is not None else 'n/a'} |")
    costo, costn = _cost_total(old_dir, n), _cost_total(new_dir, n)
    lines.append(f"| pipeline cost (cost.json) | {f'${costo:.2f}' if costo is not None else 'n/a'} | {f'${costn:.2f}' if costn is not None else 'n/a'} |")
    lines.append("")
    lines.append(f"- OLD hedge breakdown: {oh}")
    lines.append(f"- NEW hedge breakdown: {nh}")
    so, sn = _changes_stats(old_dir, n), _changes_stats(new_dir, n)
    lines.append(f"- OLD copy-editor changes: {so or 'n/a'}")
    lines.append(f"- NEW copy-editor changes: {sn or 'n/a'}")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Psalm text for the judge (optional, best-effort)
# ---------------------------------------------------------------------------

def psalm_text_block(n: int, db_path: str) -> str:
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from src.data_sources.tanakh_database import TanakhDatabase
        db = TanakhDatabase(Path(db_path))
        psalm = db.get_psalm(n)
        if psalm:
            lines = [f"For reference, the text of Psalm {n}:", ""]
            for v in psalm.verses:
                lines.append(f"{v.verse}. {v.hebrew}")
                lines.append(f"   {v.english}")
            return "\n".join(lines)
    except Exception:
        pass
    return ("(Psalm text unavailable to the judge — verify claims on internal "
            "evidence and your own knowledge of the psalm.)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Blind-judge OLD vs NEW full commentaries.")
    ap.add_argument("psalms", nargs="+", type=int)
    ap.add_argument("--old-dir", default=OLD_DIR_DEFAULT,
                    help="OLD arm directory template, '{n}' = psalm number "
                         f"(default: {OLD_DIR_DEFAULT}; falls back to the published DOCX)")
    ap.add_argument("--new-dir", default=NEW_DIR_DEFAULT,
                    help=f"NEW arm directory template (default: {NEW_DIR_DEFAULT})")
    ap.add_argument("--out", default=OUT_DIR_DEFAULT)
    ap.add_argument("--model", default="claude-opus-4-8")
    ap.add_argument("--db-path", default="database/tanakh.db")
    ap.add_argument("--seed", type=int, default=58, help="Shuffle seed for blinding")
    ap.add_argument("--skip-judge", action="store_true",
                    help="Deterministic metrics only — no LLM call, $0")
    ap.add_argument("--max-arm-chars", type=int, default=300000,
                    help="Truncate each commentary beyond this many chars (guard)")
    args = ap.parse_args()

    client = None
    if not args.skip_judge:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("FATAL: ANTHROPIC_API_KEY is not set (or use --skip-judge).",
                  file=sys.stderr)
            return 2
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

    out_dir = (PROJECT_ROOT / args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    rows = []

    for n in args.psalms:
        old_dir = (PROJECT_ROOT / args.old_dir.format(n=n)).resolve()
        new_dir = (PROJECT_ROOT / args.new_dir.format(n=n)).resolve()

        old_text, old_src = resolve_arm_text(old_dir, n, allow_docx_fallback=True)
        new_text, new_src = resolve_arm_text(new_dir, n, allow_docx_fallback=False)
        if old_text is None or new_text is None:
            print(f"Psalm {n}: SKIP — OLD: {old_src}; NEW: {new_src}")
            continue

        old_text = strip_changes_section(old_text)
        new_text = strip_changes_section(new_text)
        for label, t in (("OLD", old_text), ("NEW", new_text)):
            if len(t) > args.max_arm_chars:
                print(f"Psalm {n}: [warn] {label} arm truncated "
                      f"{len(t):,} -> {args.max_arm_chars:,} chars")
        old_text = old_text[:args.max_arm_chars]
        new_text = new_text[:args.max_arm_chars]

        report_parts = [f"# Novelty A/B evaluation — Psalm {n} ({stamp})", ""]
        report_parts.append(deterministic_report(
            n, old_dir, new_dir, old_text, new_text, old_src, new_src))

        summary = {"psalm": n}
        if client is not None:
            arms = [("old", old_text), ("new", new_text)]
            rng.shuffle(arms)
            mapping = {"A": arms[0][0], "B": arms[1][0]}
            prompt = JUDGE_PROMPT.format(
                psalm_number=n,
                psalm_text_block=psalm_text_block(n, args.db_path),
                text_a=arms[0][1],
                text_b=arms[1][1],
            )
            print(f"Psalm {n}: judging (blind: A={mapping['A']}, B={mapping['B']} — "
                  f"recorded, not shown to judge)…")
            resp = client.messages.create(
                model=args.model,
                max_tokens=20000,
                thinking={"type": "adaptive"},
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(b.text for b in resp.content
                           if getattr(b, "type", "") == "text")
            report_parts.append(text)
            report_parts.append(
                f"\n---\nUNBLINDING (not seen by judge): Commentary A = {mapping['A']}, "
                f"Commentary B = {mapping['B']}\n")

            parsed = None
            for line in reversed(text.strip().splitlines()):
                line = line.strip().strip("`")
                if line.startswith("{") and line.endswith("}"):
                    try:
                        parsed = json.loads(line)
                    except json.JSONDecodeError:
                        pass
                    break
            if parsed:
                parsed["A_is"], parsed["B_is"] = mapping["A"], mapping["B"]
                w = parsed.get("winner", "?")
                parsed["winner_arm"] = mapping.get(w, "TIE" if w == "TIE" else "?")
                summary.update(parsed)
                print(f"  winner: {parsed['winner_arm']} "
                      f"(best5 A={parsed.get('best5_A')} B={parsed.get('best5_B')})")
            else:
                print("  [warn] could not parse judge JSON summary line")
                summary["winner_arm"] = "PARSE-FAIL"

        out_file = out_dir / f"psalm_{n:03d}_eval.md"
        out_file.write_text("\n".join(report_parts), encoding="utf-8")
        print(f"  saved {out_file}")
        rows.append(summary)

    if rows and client is not None:
        def by_arm(r, key_a, key_b, arm):
            return r.get(key_a if r.get("A_is") == arm else key_b, "?")
        lines = [f"# Novelty A/B — judge summary {stamp} (model={args.model}, seed={args.seed})", ""]
        lines.append("| psalm | winner | old best5 | new best5 | old gold | new gold "
                     "| old bridging-gold | new bridging-gold | old overreach | new overreach |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            lines.append(
                f"| {r.get('psalm')} | {r.get('winner_arm','?')} "
                f"| {by_arm(r,'best5_A','best5_B','old')} | {by_arm(r,'best5_A','best5_B','new')} "
                f"| {by_arm(r,'gold_A','gold_B','old')} | {by_arm(r,'gold_A','gold_B','new')} "
                f"| {by_arm(r,'bridging_gold_A','bridging_gold_B','old')} "
                f"| {by_arm(r,'bridging_gold_A','bridging_gold_B','new')} "
                f"| {by_arm(r,'overreach_A','overreach_B','old')} "
                f"| {by_arm(r,'overreach_A','overreach_B','new')} |"
            )
        summary_file = out_dir / f"_EVAL_SUMMARY_{stamp}.md"
        summary_file.write_text("\n".join(lines), encoding="utf-8")
        print("\n" + "\n".join(lines))
        print(f"\nSaved: {summary_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
