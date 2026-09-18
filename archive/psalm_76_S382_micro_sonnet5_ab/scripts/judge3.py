"""Three-arm scorer: Sonnet 4.6 (production) vs Sonnet 5 @ max vs Sonnet 5 @ xhigh, Ps 76."""
import json, os, sys
from pathlib import Path
ROOT = Path(r"c:/dev/personal/psalms"); sys.path.insert(0, str(ROOT))
from src.utils.cost_tracker import price_tokens
from src.concordance.hebrew_text_processor import normalize_for_search as N

ARMS = [("Sonnet 4.6", "output/psalm_76/psalm_076_micro_v2.json", None, "claude-sonnet-4-6"),
        ("S5 max",     "output/psalm_76/_micro_s5_ab/psalm_076_micro_v2.json",
                       "output/psalm_76/_micro_s5_ab/cost.json", "claude-sonnet-5"),
        ("S5 xhigh",   "output/psalm_76/_micro_s5_ab_xhigh/psalm_076_micro_v2.json",
                       "output/psalm_76/_micro_s5_ab_xhigh/cost.json", "claude-sonnet-5")]
RUN = json.load(open(ROOT/"output/psalm_76/psalm_076_cost.json", encoding="utf-8"))

rows=[]
for name, mp, cp, model in ARMS:
    mp = ROOT/mp
    if not mp.exists():
        print(f"!! {name}: missing {mp}"); continue
    d=json.load(open(mp,encoding="utf-8")); vc=d["verse_commentaries"]
    u = RUN[model] if cp is None else json.load(open(ROOT/cp,encoding="utf-8"))[model]
    cost = price_tokens(model, input_tokens=u["input_tokens"], output_tokens=u["output_tokens"],
                        thinking_tokens=u.get("thinking_tokens",0))
    rows.append(dict(name=name, d=d, vc=vc,
        lex=sum(len(v.get("lexical_insights") or []) for v in vc),
        fig=sum(len(v.get("figurative_analysis") or []) for v in vc),
        q=len(d.get("interesting_questions") or []),
        prose=sum(len(v.get("commentary") or "") for v in vc),
        detail=sum(len(json.dumps(v.get("lexical_insights") or [],ensure_ascii=False)) for v in vc),
        size=os.path.getsize(mp), cost=cost,
        i=u["input_tokens"], o=u["output_tokens"], calls=u["call_count"]))

base=rows[0]
def pc(v,b): return "—" if v==b else f"{(v-b)/b*100:+.0f}%"
w="{:<24}"+"{:>16}"*len(rows)
print("PSALM 76 MICRO — THREE ARMS\n")
print(w.format("", *[r["name"] for r in rows]))
print("-"*(24+16*len(rows)))
for k,lbl in [("lex","lexical insights"),("fig","figurative flags"),("q","interesting questions"),
              ("detail","lexical detail (ch)"),("prose","commentary prose (ch)"),("size","JSON bytes"),
              ("i","input tokens"),("o","output tokens")]:
    print(w.format(lbl, *[f"{r[k]:,} {pc(r[k],base[k])}" if r is not base else f"{r[k]:,}" for r in rows]))
print("-"*(24+16*len(rows)))
print(w.format("COST", *[f"${r['cost']:.4f} {pc(r['cost'],base['cost'])}" if r is not base else f"${r['cost']:.4f}" for r in rows]))
print(w.format("vs $6.4206 run", *[("—" if r is base else f"{(r['cost']-base['cost'])/6.4206*100:+.1f}%") for r in rows]))

# re-cut analysis vs the 4.6 baseline
bv={v["verse_number"]: set().union(*([set(N(li.get("phrase",""),"consonantal").split())
      for li in (v.get("lexical_insights") or [])] or [set()])) for v in base["vc"]}
print("\nphrase targets 4.6 never touched (higher = more genuinely new ground):")
for r in rows[1:]:
    new=[(v["verse_number"], li.get("phrase",""))
         for v in r["vc"] for li in (v.get("lexical_insights") or [])
         if not (set(N(li.get("phrase",""),"consonantal").split()) & bv.get(v["verse_number"],set()))]
    print(f"  {r['name']:<10} {len(new):>3} new / {r['lex']} total  ({100*(r['lex']-len(new))/r['lex']:.0f}% re-cut)")
    for vn,p in new: print(f"        v{vn}: {p}")
