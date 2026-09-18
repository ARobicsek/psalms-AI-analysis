"""Micro-agent A/B arm: Sonnet 5 on Psalm 76, Stages 1-2 only.

Baseline is the existing production run (claude-sonnet-4-6), already on disk, so
only this arm costs money. Isolated output dir -- production files untouched.

Implements the two migration changes documented in SONNET5_MICRO_AB_FINDINGS.md
as a SHIM over client.messages.stream, so no production code is modified:
  1. Stage 1 sends thinking={"type":"enabled","budget_tokens":N} -> 400 on Sonnet 5.
     Rewrite to {"type":"adaptive"} and raise max_tokens (thinking is uncappable now
     and shares the budget with the JSON).
  2. Stage 2 sends NO thinking config. On 4.6 that means OFF; on Sonnet 5 omitting it
     defaults to adaptive ON. Send {"type":"disabled"} explicitly to match 4.6.
"""
import json, sys, time
from pathlib import Path

ROOT = Path(r"c:/dev/personal/psalms")
sys.path.insert(0, str(ROOT))
import os
os.chdir(ROOT)

from src.agents.micro_analyst import MicroAnalystV2
from src.schemas.analysis_schemas import load_macro_analysis
from src.utils.cost_tracker import CostTracker

PSALM = 76
MODEL = "claude-sonnet-5"
EFFORT = sys.argv[1] if len(sys.argv) > 1 else "max"
SUFFIX = "" if EFFORT == "max" else f"_{EFFORT}"
OUT = ROOT / "output" / f"psalm_{PSALM}" / f"_micro_s5_ab{SUFFIX}"
OUT.mkdir(parents=True, exist_ok=True)

tracker = CostTracker()
agent = MicroAnalystV2(db_path="database/tanakh.db", commentary_mode="all",
                      cost_tracker=tracker, model=MODEL)

# ---- the shim -------------------------------------------------------------
_real_stream = agent.client.messages.stream
calls = []

def shimmed(**kw):
    note = {}
    th = kw.get("thinking")
    if isinstance(th, dict) and "budget_tokens" in th:
        note["stage"] = 1
        note["was"] = dict(th)
        kw["thinking"] = {"type": "adaptive"}          # migration change 1
        kw["max_tokens"] = 128000                       # headroom: thinking is uncapped
        oc = dict(kw.get("output_config") or {})
        note["effort_was"] = oc.get("effort")
        oc["effort"] = EFFORT                           # arm variable
        kw["output_config"] = oc
        note["now"] = kw["thinking"]; note["max_tokens"] = kw["max_tokens"]
        note["effort_now"] = EFFORT
    elif th is None:
        note["stage"] = 2
        note["was"] = None
        kw["thinking"] = {"type": "disabled"}           # migration change 2
        note["now"] = kw["thinking"]
    calls.append(note)
    print(f"  [shim] stage {note.get('stage')}: thinking {note.get('was')} -> {note.get('now')}", flush=True)
    return _real_stream(**kw)

agent.client.messages.stream = shimmed
# ---------------------------------------------------------------------------

macro = load_macro_analysis(str(ROOT / "output" / f"psalm_{PSALM}" / f"psalm_{PSALM:03d}_macro.json"))
print(f"loaded macro for Ps {PSALM}; model={MODEL}; effort={EFFORT}", flush=True)

t0 = time.time()
phonetic = agent._get_phonetic_transcriptions(PSALM)
print("[STAGE 1] discovery pass...", flush=True)
discoveries = agent._discovery_pass(PSALM, macro, phonetic)
print("[STAGE 2] research requests...", flush=True)
request = agent._generate_research_requests(discoveries, PSALM, macro)
micro = agent._create_micro_analysis(PSALM, discoveries, phonetic)
elapsed = time.time() - t0

d = micro.to_dict()
d["model_used"] = MODEL
d["_ab_effort"] = EFFORT
(OUT / f"psalm_{PSALM:03d}_micro_v2.json").write_text(
    json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "cost.json").write_text(
    json.dumps(tracker.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "shim_log.json").write_text(
    json.dumps(calls, ensure_ascii=False, indent=2), encoding="utf-8")
try:
    (OUT / "research_request.json").write_text(
        json.dumps(request.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
except Exception as e:
    print("  (research_request not serialized:", e, ")")

print(f"\nDONE in {elapsed/60:.1f} min -> {OUT}")
print("cost: $%.4f" % tracker.get_total_cost())
print(tracker.get_summary())
