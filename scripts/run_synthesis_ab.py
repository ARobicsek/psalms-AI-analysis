#!/usr/bin/env python3
"""A/B harness — synthesis-discovery v1 (production) vs. v2 (Synthesis Scholar).

Runs BOTH prompts over BYTE-IDENTICAL assembled inputs for one or more psalms
and writes the outputs side by side, plus a special-instruction contamination
scan, so the two prompts can be judged fairly. It performs NO Master Writer
run — only the ~2 synthesizer calls per psalm.

Why this exists: the v2 prompt is meant to surface abductive "aha"
connections (e.g. the Ps 67 נשׂיאת-פנים omission read against the psalm's
universalism). To test that fairly we must (a) feed the synthesizer exactly
the dossier it sees at Step 3.5 in the real pipeline, and (b) make sure the
author's Special Instruction — which states that very argument — is NOT in
the inputs. The SI never reaches the synthesizer by construction (it is
passed only to the Master Writer), so the only realistic contamination
vector is the dossier data itself; this harness scans for it and reports.

MUST be run where the real dossiers and key live (i.e. the local repo, not a
fresh cloud clone): needs output/psalm_NNN/{macro,micro_v2,research_v2}.* and
ANTHROPIC_API_KEY. Note: in git-bash activate the venv with
`source venv/Scripts/activate`.

Usage:
    python scripts/run_synthesis_ab.py 67 60 49
    python scripts/run_synthesis_ab.py 67 --model claude-opus-4-8
    python scripts/run_synthesis_ab.py 67 --only v2 --out output/ab_synthesis
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.master_editor_si import MasterEditorSI
from src.agents.rag_manager import RAGManager
from src.agents.synthesis_discovery import (
    SynthesisDiscoveryAgent,
    INPUTS_HEADER as V1_INPUTS_HEADER,
    SYNTHESIS_TASK as V1_SYNTHESIS_TASK,
)
from src.utils.cost_tracker import CostTracker
from scripts.synthesis_ab_prompts import V2_INPUTS_HEADER, V2_SYNTHESIS_TASK


# ---------------------------------------------------------------------------
# Special-instruction contamination terms.
# "interpretation" hits invalidate the Ps 67 favoritism canary (the SI's
# actual argument leaked into the dossier); "observation" hits are tolerable
# but worth noting (the raw textual fact — a missing third line — is fair game
# for the model to find on its own).
# ---------------------------------------------------------------------------
CONTAM_TERMS = {
    "interpretation": [
        "favoritism", "favouritism", "partiality", "particularist",
        "particularism", "נשיאת פנים", "נשׂיאת פנים", "show favor",
        "shows favor", "lifting of the face", "lift up the face",
    ],
    "observation": [
        "יִשָּׂא", "ישא פניו", "יִשָּׂא פָּנָיו", "third line", "third clause",
        "third blessing", "third verse of the priestly", "omits the third",
        "drops the third", "missing third",
    ],
}


def assemble_inputs(me: MasterEditorSI, psalm_number: int) -> dict:
    """Reproduce, byte-for-byte, the input assembly in
    MasterEditor.discover_cross_verse_observations (Step 3.5)."""
    output_path = PROJECT_ROOT / "output" / f"psalm_{psalm_number:03d}"
    macro_file = output_path / f"psalm_{psalm_number:03d}_macro.json"
    micro_file = output_path / f"psalm_{psalm_number:03d}_micro_v2.json"
    research_file = output_path / f"psalm_{psalm_number:03d}_research_v2.md"
    for f in (macro_file, micro_file, research_file):
        if not f.exists():
            raise FileNotFoundError(
                f"Missing dossier input for Psalm {psalm_number}: {f}\n"
                "Run this on the machine that holds the real pipeline outputs."
            )

    macro_analysis = me._load_json_file(macro_file)
    micro_analysis = me._load_json_file(micro_file)
    research_bundle_raw = me._load_text_file(research_file)
    research_bundle, _, _ = me.research_trimmer.trim_bundle(
        research_bundle_raw, max_chars=350000
    )
    psalm_text = me._get_psalm_text(psalm_number, micro_analysis)
    phonetic_section = me._format_phonetic_section(micro_analysis)
    macro_text = me._format_analysis_for_prompt(macro_analysis, "macro")
    micro_text = me._format_analysis_for_prompt(micro_analysis, "micro")

    try:
        analytical_framework = RAGManager("docs").load_analytical_framework()
    except Exception as e:  # mirror the agent's soft-fail
        print(f"  [warn] analytical framework unavailable: {e}")
        analytical_framework = "[Analytical framework not available]"

    fields = dict(
        psalm_number=psalm_number,
        psalm_text=psalm_text,
        macro_analysis=macro_text,
        micro_analysis=micro_text,
        research_bundle=research_bundle,
        phonetic_section=phonetic_section,
        analytical_framework=analytical_framework,
    )
    # The dossier payload only (no prompt instructions) — what we scan.
    fields["_dossier_blob"] = "\n".join(
        [psalm_text, macro_text, micro_text, research_bundle, phonetic_section]
    )
    fields["_sources"] = {
        "psalm_text": psalm_text,
        "macro": macro_text,
        "micro": micro_text,
        "research_bundle": research_bundle,
        "phonetic_section": phonetic_section,
    }
    return fields


def contamination_scan(fields: dict, psalm_number: int) -> str:
    """Scan the assembled dossier (not the prompt instructions) for SI leakage.
    Returns a human-readable report; never raises — the human decides."""
    lines = [
        f"SPECIAL-INSTRUCTION CONTAMINATION SCAN — Psalm {psalm_number}",
        f"dossier size: {len(fields['_dossier_blob']):,} chars",
        "",
    ]
    any_interp = False
    for severity in ("interpretation", "observation"):
        lines.append(f"== {severity.upper()} terms ==")
        found_any = False
        for term in CONTAM_TERMS[severity]:
            for src_name, src in fields["_sources"].items():
                low_src = src.lower()
                low_term = term.lower()
                n = low_src.count(low_term) if low_term.isascii() else src.count(term)
                if n:
                    found_any = True
                    if severity == "interpretation":
                        any_interp = True
                    idx = (low_src.find(low_term) if low_term.isascii()
                           else src.find(term))
                    ctx = src[max(0, idx - 70): idx + len(term) + 70].replace("\n", " ")
                    lines.append(f"  [{src_name}] '{term}' ×{n}  …{ctx}…")
        if not found_any:
            lines.append("  (none)")
        lines.append("")

    verdict = (
        "INVALID for Example-1 canary — the SI's INTERPRETATION is in the "
        "dossier; excise it or pick another psalm."
        if any_interp else
        "CLEAN of the interpretation; the favoritism canary is valid. "
        "(Any observation-level hits above are the raw textual fact only.)"
    )
    lines.append(f"VERDICT: {verdict}")
    return "\n".join(lines)


def run_one_prompt(agent: SynthesisDiscoveryAgent, prompt: str, tag: str) -> dict:
    text, in_tok, out_tok, think = agent._stream_call(prompt, tag=tag, retries=4)
    return {
        "full": text,
        "observations": agent._extract_observations_block(text),
        "in_tok": in_tok,
        "out_tok": out_tok,
        "think_chars": think,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="A/B the synthesis-discovery prompt (v1 vs v2).")
    ap.add_argument("psalms", nargs="+", type=int, help="Psalm numbers, e.g. 67 60 49")
    ap.add_argument("--model", default="claude-opus-4-8",
                    help="Anthropic model for BOTH arms (default: claude-opus-4-8)")
    ap.add_argument("--only", choices=["v1", "v2", "both"], default="both",
                    help="Run only one arm (default: both)")
    ap.add_argument("--out", default="output/ab_synthesis",
                    help="Output directory (default: output/ab_synthesis)")
    args = ap.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("FATAL: ANTHROPIC_API_KEY is not set.", file=sys.stderr)
        return 2

    out_dir = (PROJECT_ROOT / args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    cost_tracker = CostTracker()
    me = MasterEditorSI(main_model=args.model, cost_tracker=cost_tracker)
    agent = SynthesisDiscoveryAgent(cost_tracker=cost_tracker, model=args.model)

    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    summary = [f"# Synthesis A/B run {stamp} — model={args.model} arms={args.only}", ""]

    for n in args.psalms:
        print(f"\n=== Psalm {n} ===")
        try:
            fields = assemble_inputs(me, n)
        except FileNotFoundError as e:
            print(f"  SKIP: {e}")
            summary.append(f"- Psalm {n}: SKIPPED (missing inputs)")
            continue

        # 1) contamination scan up front
        scan = contamination_scan(fields, n)
        (out_dir / f"psalm_{n:03d}_contamination_scan.txt").write_text(scan, encoding="utf-8")
        print("  " + scan.splitlines()[-1])  # the VERDICT line

        fmt_fields = {k: v for k, v in fields.items() if not k.startswith("_")}

        # 2) build both prompts over identical inputs
        v1_prompt = V1_INPUTS_HEADER.format(**fmt_fields) + V1_SYNTHESIS_TASK
        v2_prompt = V2_INPUTS_HEADER.format(**fmt_fields) + V2_SYNTHESIS_TASK
        (out_dir / f"psalm_{n:03d}_prompt_v1.txt").write_text(v1_prompt, encoding="utf-8")
        (out_dir / f"psalm_{n:03d}_prompt_v2.txt").write_text(v2_prompt, encoding="utf-8")

        row = [f"- Psalm {n}:"]
        for arm, prompt in (("v1", v1_prompt), ("v2", v2_prompt)):
            if args.only != "both" and args.only != arm:
                continue
            print(f"  running {arm} ({len(prompt):,} char prompt)…")
            res = run_one_prompt(agent, prompt, tag=f"AB-{arm} psalm {n}")
            (out_dir / f"psalm_{n:03d}_{arm}.md").write_text(res["observations"], encoding="utf-8")
            (out_dir / f"psalm_{n:03d}_{arm}_full.txt").write_text(res["full"], encoding="utf-8")
            row.append(
                f"{arm}: out={res['out_tok']:,} tok, "
                f"~{res['think_chars']//4:,} thinking, "
                f"{len(res['observations']):,} chars obs"
            )
            print(f"    {arm} done — {row[-1]}")
        summary.append("  ".join(row))

    summary.append("")
    summary.append(f"Total cost: ${cost_tracker.get_total_cost():.4f}")
    summary.append(f"Outputs in: {out_dir}")
    (out_dir / f"_SUMMARY_{stamp}.md").write_text("\n".join(summary), encoding="utf-8")
    print("\n" + "\n".join(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
