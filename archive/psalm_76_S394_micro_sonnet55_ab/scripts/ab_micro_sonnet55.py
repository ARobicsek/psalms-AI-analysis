"""Session 394: micro-agent A/B arm -- Sonnet 5.5 on a psalm, Stages 1-2 only.

Usage:
    python scripts/ab_micro_sonnet55.py 76 high            # one arm (~$0.3-1.2)
    python scripts/ab_micro_sonnet55.py 76 high --dry-run  # $0: shimmed Stage-1 kwargs + count_tokens

The baselines are already on disk (three Sonnet 4.6 runs of Ps 76, plus Session 382's two
Sonnet 5 arms), so only these arms cost money. Output goes to
output/psalm_N/_micro_s55_ab_<effort>/ -- production files are untouched.

Production code is NOT modified. As in Session 382's Sonnet 5 runner, a shim over
client.messages.stream applies the migration changes Sonnet 5.5 needs:
  1. Stage 1 sends thinking={"type":"enabled","budget_tokens":N} -> 400 on Sonnet 5.5.
     Rewritten to {"type":"adaptive"} with max_tokens 128000 (thinking cannot be capped and
     shares the budget with the JSON) and the arm's effort.
  2. Stage 2 sends NO thinking. On 4.6 that means OFF; on Sonnet 5.5 omitting it means adaptive
     ON, and {"type":"disabled"} is a 400. The thinking-off setting on 5.5 is
     {"type":"between_tools"}, allowed only at effort high or below -> sent with effort "high".
Each arm's shim_log.json records that both rewrites fired exactly once.
"""
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.agents.micro_analyst import MicroAnalystV2
from src.schemas.analysis_schemas import load_macro_analysis
from src.utils.cost_tracker import CostTracker

MODEL = "claude-sonnet-5-5"
EFFORTS = ("low", "medium", "high", "xhigh", "max")


class _DryRunStop(Exception):
    pass


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if len(args) != 2 or args[1] not in EFFORTS:
        sys.exit(f"usage: ab_micro_sonnet55.py <psalm> <{'|'.join(EFFORTS)}> [--dry-run]")
    psalm, effort = int(args[0]), args[1]
    out = ROOT / "output" / f"psalm_{psalm}" / f"_micro_s55_ab_{effort}"

    tracker = CostTracker()
    agent = MicroAnalystV2(db_path="database/tanakh.db", commentary_mode="all",
                           cost_tracker=tracker, model=MODEL)

    real_stream = agent.client.messages.stream
    calls = []

    def shimmed(**kw):
        note = {}
        th = kw.get("thinking")
        if isinstance(th, dict) and "budget_tokens" in th:
            note.update(stage=1, was=dict(th),
                        effort_was=(kw.get("output_config") or {}).get("effort"))
            kw["thinking"] = {"type": "adaptive"}
            kw["max_tokens"] = 128000
            kw["output_config"] = {**(kw.get("output_config") or {}), "effort": effort}
        elif th is None:
            note.update(stage=2, was=None,
                        effort_was=(kw.get("output_config") or {}).get("effort"))
            kw["thinking"] = {"type": "between_tools"}
            kw["output_config"] = {**(kw.get("output_config") or {}), "effort": "high"}
        else:
            note.update(stage="?", was=th)
        note.update(now=kw.get("thinking"), max_tokens=kw.get("max_tokens"),
                    effort_now=(kw.get("output_config") or {}).get("effort"))
        calls.append(note)
        print(f"  [shim] stage {note['stage']}: thinking {note['was']} -> {note['now']}, "
              f"effort {note['effort_was']} -> {note['effort_now']}, max_tokens {note['max_tokens']}",
              flush=True)
        if dry:
            n = agent.client.messages.count_tokens(model=kw["model"], messages=kw["messages"],
                                                   thinking=kw["thinking"])
            print(f"  [dry-run] count_tokens: {n.input_tokens:,} input tokens on {kw['model']}")
            raise _DryRunStop
        return real_stream(**kw)

    agent.client.messages.stream = shimmed

    macro = load_macro_analysis(str(ROOT / "output" / f"psalm_{psalm}" / f"psalm_{psalm:03d}_macro.json"))
    print(f"Ps {psalm}; model={MODEL}; effort={effort}; dry_run={dry}", flush=True)

    t0 = time.time()
    phonetic = agent._get_phonetic_transcriptions(psalm)
    print("[STAGE 1] discovery pass...", flush=True)
    try:
        discoveries = agent._discovery_pass(psalm, macro, phonetic)
    except _DryRunStop:
        print("\nDRY RUN OK: Stage 1 request built and accepted by count_tokens. $0 spent.")
        return
    t1 = time.time()
    print("[STAGE 2] research requests...", flush=True)
    request = agent._generate_research_requests(discoveries, psalm, macro)
    micro = agent._create_micro_analysis(psalm, discoveries, phonetic)
    t2 = time.time()

    out.mkdir(parents=True, exist_ok=True)
    d = micro.to_dict()
    d["model_used"] = MODEL
    d["_ab_effort"] = effort
    (out / f"psalm_{psalm:03d}_micro_v2.json").write_text(
        json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "cost.json").write_text(json.dumps(tracker.to_dict(), ensure_ascii=False, indent=2),
                                   encoding="utf-8")
    (out / "shim_log.json").write_text(json.dumps(
        {"calls": calls, "stage1_seconds": round(t1 - t0), "stage2_seconds": round(t2 - t1)},
        ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        (out / "research_request.json").write_text(
            json.dumps(request.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print("  (research_request not serialized:", e, ")")

    print(f"\nDONE in {(t2 - t0) / 60:.1f} min -> {out}")
    print("cost: $%.4f" % tracker.get_total_cost())


if __name__ == "__main__":
    main()
