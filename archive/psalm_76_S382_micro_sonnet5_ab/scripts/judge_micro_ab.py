"""Score the Ps 76 micro A/B: Sonnet 4.6 (production) vs Sonnet 5 (arm).

Metrics chosen to match SONNET5_MICRO_AB_FINDINGS.md so the two psalms are
commensurable. Cost is priced through the shared table, at the NEW permanent
Sonnet 5 rate ($2/$10), not the retired $3/$15.
"""
import json, sys
from pathlib import Path
ROOT = Path(r"c:/dev/personal/psalms"); sys.path.insert(0, str(ROOT))
from src.utils.cost_tracker import price_tokens

BASE = ROOT/"output/psalm_76/psalm_076_micro_v2.json"
ARM  = ROOT/"output/psalm_76/_micro_s5_ab/psalm_076_micro_v2.json"
ARM_COST = ROOT/"output/psalm_76/_micro_s5_ab/cost.json"
RUN_COST = ROOT/"output/psalm_76/psalm_076_cost.json"

def stats(p):
    d = json.load(open(p, encoding="utf-8"))
    vc = d["verse_commentaries"]
    li = sum(len(v.get("lexical_insights") or []) for v in vc)
    fa = sum(len(v.get("figurative_analysis") or []) for v in vc)
    prose = sum(len(v.get("commentary") or "") for v in vc)
    notes = sum(len(json.dumps(v.get("lexical_insights") or [], ensure_ascii=False)) for v in vc)
    return dict(verses=len(vc), lexical=li, figurative=fa,
                questions=len(d.get("interesting_questions") or []),
                threads=len(d.get("thematic_threads") or []),
                prose=prose, lexdetail=notes,
                per_insight=prose/li if li else 0, model=d.get("model_used"))

b, a = stats(BASE), stats(ARM)
bc = json.load(open(RUN_COST, encoding="utf-8"))["claude-sonnet-4-6"]
ac = json.load(open(ARM_COST, encoding="utf-8"))

# arm tokens
arm_row = ac.get("claude-sonnet-5", {})
b_in, b_out, b_th = bc["input_tokens"], bc["output_tokens"], bc.get("thinking_tokens", 0)
a_in, a_out, a_th = arm_row.get("input_tokens",0), arm_row.get("output_tokens",0), arm_row.get("thinking_tokens",0)
b_cost = price_tokens("claude-sonnet-4-6", input_tokens=b_in, output_tokens=b_out, thinking_tokens=b_th)
a_cost = price_tokens("claude-sonnet-5",   input_tokens=a_in, output_tokens=a_out, thinking_tokens=a_th)

def pct(n, o): return "—" if not o else f"{(n-o)/o*100:+.0f}%"

print("PSALM 76 MICRO A/B — Sonnet 4.6 (production) vs Sonnet 5 @ effort=max\n")
print(f"{'metric':<26}{'4.6':>12}{'S5':>12}{'delta':>10}")
print("-"*60)
for k, lbl in [("lexical","lexical insights"),("figurative","figurative flags"),
               ("questions","interesting questions"),("prose","commentary prose (ch)"),
               ("lexdetail","lexical detail (ch)"),("per_insight","chars per insight")]:
    print(f"{lbl:<26}{b[k]:>12.0f}{a[k]:>12.0f}{pct(a[k],b[k]):>10}")
print("-"*60)
print(f"{'input tokens':<26}{b_in:>12,}{a_in:>12,}{pct(a_in,b_in):>10}")
print(f"{'output tokens':<26}{b_out:>12,}{a_out:>12,}{pct(a_out,b_out):>10}")
print(f"{'thinking tokens':<26}{b_th:>12,}{a_th:>12,}")
print(f"{'COST':<26}{'$'+format(b_cost,'.4f'):>12}{'$'+format(a_cost,'.4f'):>12}{pct(a_cost,b_cost):>10}")
print(f"\ndelta vs the $6.4206 Ps 76 run total: {a_cost-b_cost:+.4f}  ({(a_cost-b_cost)/6.4206*100:+.1f}% of run)")
print(f"\ncalls: 4.6={bc['call_count']}  S5={arm_row.get('call_count')}")
