#!/usr/bin/env python3
"""Blind LLM judge for the synthesis-discovery A/B (v1 vs v2).

Reads the observation files produced by scripts/run_synthesis_ab.py
(output/ab_synthesis/psalm_NNN_{v1,v2}.md), presents them to a judge model
BLIND (shuffled into "Set A"/"Set B" so the judge cannot know which arm is
which), scores every observation on a fixed rubric, and writes a per-psalm
report plus a cross-psalm summary that unblinds the mapping at the end.

The judge also runs the two Psalm-67 "canary" checks (favoritism-omission;
overdetermined Omer custom) against BOTH sets — these are scored on presence,
not quality, and reported separately from the rubric.

Usage:
    python scripts/judge_synthesis_ab.py 67 60 49
    python scripts/judge_synthesis_ab.py 67 --model claude-opus-4-8 --seed 7
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import random
import re
import sys
from pathlib import Path

import anthropic

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AB_DIR_DEFAULT = "output/ab_synthesis"


JUDGE_PROMPT = """You are a senior scholar of the Hebrew Psalms acting as a BLIND JUDGE in a
prompt A/B test. Two different systems each produced a list of "synthesis
observations" about Psalm {psalm_number} from the same research dossier. You
do not know which system produced which set, and you must not try to guess.
Judge only what is on the page.

{psalm_text_block}

═══════════════════════════════════════════════════════════════════════════
## SET A
═══════════════════════════════════════════════════════════════════════════

{set_a}

═══════════════════════════════════════════════════════════════════════════
## SET B
═══════════════════════════════════════════════════════════════════════════

{set_b}

═══════════════════════════════════════════════════════════════════════════
## YOUR TASK
═══════════════════════════════════════════════════════════════════════════

### Step 1 — Score EVERY observation in both sets

For each observation (governing, core, additional), assign 1-5 on each
dimension. Be adversarial: rhetoric must not inflate scores.

- **LINKAGE NOVELTY (1-5):** Is the CONNECTION itself non-standard — something
  a learned reader of Psalms has not already made? (Famous constituent facts
  are fine; a famous linkage is not.) 1 = standard fare or restated source
  material; 5 = a genuinely new joining.
- **AHA (1-5):** Does holding the observation change how you read at least
  one verse, or the whole poem — with that "obvious in hindsight" feel?
  1 = inert/dull even if true; 5 = cannot un-see it afterwards.
- **ECONOMY (1-5):** How much does one connection explain? 1 = explains only
  itself; 5 = several independent facts (an omission AND a theme AND a
  custom) click at once.
- **GROUNDEDNESS (1-5):** Are the anchors real, sufficient, and is the
  claim's strength calibrated to its evidence? Penalize: stretched lexical
  senses, overstated parallels ("verbatim", "the only"), miscounts you can
  catch, unstated leaps presented as fact. A clearly-flagged conjecture
  with honest anchors can still score 4-5; an overclaimed certainty cannot.
  If you can identify a likely factual error, score 1-2 and name it.

Also tag each observation:
- **KIND:** INTERNAL (pattern within the psalm's own text) or BRIDGING
  (joins the text to something outside it — another biblical text, an idiom's
  wider usage, liturgy/reception, sound-vs-choice, comparative material).
- **VERDICT:** KEEP (a Master Writer should want this), MARGINAL, or CUT
  (redundant, inert, or unsound).

### Step 2 — Canary checks (apply to BOTH sets; presence, not quality)

- **CANARY-1 (favoritism omission):** Does any observation note that the
  adaptation of the Priestly Blessing (Numbers 6:24-26) omits its third
  line (יִשָּׂא ה' פָּנָיו), AND connect that omission to the idiom נשׂיאת
  פנים meaning favoritism/partiality, AND read the omission against the
  psalm's universalism? Score FULL / PARTIAL (notes the omission with some
  interpretation but misses the favoritism idiom) / ABSENT.
- **CANARY-2 (overdetermined Omer):** Does any observation give the psalm's
  Omer-recitation custom a SECOND internal support beyond the famous
  49-word count — specifically the harvest content (v.7) aligning with the
  Omer's harvest season — treating the custom as overdetermined? Score
  FULL / PARTIAL / ABSENT.
(For psalms other than 67 these will normally both be ABSENT for both sets —
that is fine; do not strain to find them.)

### Step 3 — Set-level comparison

- **BEST-3 MEAN:** for each set, the mean total score (sum of 4 dimensions,
  max 20) of its three strongest observations. Quality beats quantity.
- **KEEP COUNT** and **CUT COUNT** per set.
- **BRIDGING KEEPS:** number of KEEP-verdict BRIDGING observations per set.
- **REDUNDANCY:** observations that substantially duplicate each other or
  merely restate the dossier.
- **OVERREACH:** observations whose force depends on an overstated or
  unflagged claim.
- **OVERALL:** which set would a Master Writer rather receive, and why
  (3-5 sentences, naming the decisive observations by their set labels).

═══════════════════════════════════════════════════════════════════════════
## OUTPUT FORMAT
═══════════════════════════════════════════════════════════════════════════

First a readable markdown report:

# Judge report — Psalm {psalm_number}

## Set A observations
| # | label | KIND | NOV | AHA | ECO | GRD | total | verdict | one-line justification |
(one row per observation)

## Set B observations
(same table)

## Canaries
- Set A: CANARY-1 <FULL|PARTIAL|ABSENT> — <evidence>; CANARY-2 <...> — <evidence>
- Set B: CANARY-1 <...>; CANARY-2 <...>

## Comparison
<the Step-3 analysis in prose + the numbers>

Then, on the FINAL line, a single JSON object (no code fence) exactly like:
{{"psalm": {psalm_number}, "best3_A": <float>, "best3_B": <float>, "keeps_A": <int>, "keeps_B": <int>, "bridging_keeps_A": <int>, "bridging_keeps_B": <int>, "canary1_A": "<FULL|PARTIAL|ABSENT>", "canary1_B": "...", "canary2_A": "...", "canary2_B": "...", "winner": "<A|B|TIE>"}}
"""


def extract_psalm_text_block(ab_dir: Path, n: int) -> str:
    """Pull the PSALM TEXT section out of a saved harness prompt, so the judge
    can sanity-check claims against the text without the whole dossier."""
    for arm in ("v1", "v2"):
        p = ab_dir / f"psalm_{n:03d}_prompt_{arm}.txt"
        if p.exists():
            txt = p.read_text(encoding="utf-8")
            m = re.search(
                r"### PSALM TEXT.*?\n(.*?)\n### STRUCTURAL OVERVIEW", txt, re.S
            )
            if m:
                body = m.group(1).strip()
                return (
                    "For reference, the psalm text both sets worked from:\n\n"
                    "### PSALM TEXT\n" + body + "\n"
                )
    return "(Psalm text unavailable — judge claims on internal evidence only.)"


def main() -> int:
    ap = argparse.ArgumentParser(description="Blind-judge the synthesis A/B outputs.")
    ap.add_argument("psalms", nargs="+", type=int)
    ap.add_argument("--model", default="claude-opus-4-8")
    ap.add_argument("--ab-dir", default=AB_DIR_DEFAULT)
    ap.add_argument("--seed", type=int, default=67, help="Shuffle seed for blinding")
    args = ap.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("FATAL: ANTHROPIC_API_KEY is not set.", file=sys.stderr)
        return 2
    client = anthropic.Anthropic(api_key=api_key)

    ab_dir = (PROJECT_ROOT / args.ab_dir).resolve()
    rng = random.Random(args.seed)
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")

    rows = []
    for n in args.psalms:
        f_v1 = ab_dir / f"psalm_{n:03d}_v1.md"
        f_v2 = ab_dir / f"psalm_{n:03d}_v2.md"
        if not (f_v1.exists() and f_v2.exists()):
            print(f"Psalm {n}: SKIP — missing {f_v1.name} or {f_v2.name}")
            continue

        arms = [("v1", f_v1.read_text(encoding="utf-8")),
                ("v2", f_v2.read_text(encoding="utf-8"))]
        rng.shuffle(arms)
        mapping = {"A": arms[0][0], "B": arms[1][0]}

        prompt = JUDGE_PROMPT.format(
            psalm_number=n,
            psalm_text_block=extract_psalm_text_block(ab_dir, n),
            set_a=arms[0][1],
            set_b=arms[1][1],
        )

        print(f"Psalm {n}: judging (blind: A={mapping['A']}, B={mapping['B']} — "
              f"recorded, not shown to judge)…")
        resp = client.messages.create(
            model=args.model,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")

        # Unblind in the saved report (appended AFTER the judge's verdict).
        report = (
            text
            + f"\n\n---\nUNBLINDING (not seen by judge): Set A = {mapping['A']}, "
              f"Set B = {mapping['B']}\n"
        )
        out_file = ab_dir / f"psalm_{n:03d}_judge_report.md"
        out_file.write_text(report, encoding="utf-8")
        print(f"  saved {out_file.name}")

        # Parse the trailing JSON line for the cross-psalm table.
        summary = None
        for line in reversed(text.strip().splitlines()):
            line = line.strip().strip("`")
            if line.startswith("{") and line.endswith("}"):
                try:
                    summary = json.loads(line)
                except json.JSONDecodeError:
                    pass
                break
        if summary:
            summary["set_A_is"] = mapping["A"]
            summary["set_B_is"] = mapping["B"]
            w = summary.get("winner", "?")
            summary["winner_arm"] = mapping.get(w, "TIE" if w == "TIE" else "?")
            rows.append(summary)
            print(f"  winner: {summary['winner_arm']} "
                  f"(best3 A={summary.get('best3_A')} B={summary.get('best3_B')})")
        else:
            print("  [warn] could not parse judge JSON summary line")
            rows.append({"psalm": n, "set_A_is": mapping["A"],
                         "set_B_is": mapping["B"], "winner_arm": "PARSE-FAIL"})

    if rows:
        lines = [f"# Synthesis A/B — judge summary {stamp} (model={args.model})", ""]
        lines.append("| psalm | winner | v1 best3 | v2 best3 | v1 keeps | v2 keeps | "
                     "v1 bridging | v2 bridging | canary1 v2 | canary2 v2 |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            def by_arm(key_a, key_b, arm):
                return r.get(key_a if r.get("set_A_is") == arm else key_b, "?")
            lines.append(
                f"| {r.get('psalm')} | {r.get('winner_arm')} "
                f"| {by_arm('best3_A','best3_B','v1')} | {by_arm('best3_A','best3_B','v2')} "
                f"| {by_arm('keeps_A','keeps_B','v1')} | {by_arm('keeps_A','keeps_B','v2')} "
                f"| {by_arm('bridging_keeps_A','bridging_keeps_B','v1')} "
                f"| {by_arm('bridging_keeps_A','bridging_keeps_B','v2')} "
                f"| {by_arm('canary1_A','canary1_B','v2')} "
                f"| {by_arm('canary2_A','canary2_B','v2')} |"
            )
        summary_file = ab_dir / f"_JUDGE_SUMMARY_{stamp}.md"
        summary_file.write_text("\n".join(lines), encoding="utf-8")
        print("\n" + "\n".join(lines))
        print(f"\nSaved: {summary_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
