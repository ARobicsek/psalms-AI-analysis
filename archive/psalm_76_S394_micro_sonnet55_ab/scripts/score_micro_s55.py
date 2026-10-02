"""Session 394: score the Ps 76 micro arms -- 3 x Sonnet 4.6, 2 x Sonnet 5 (S382), Sonnet 5.5 arms.

$0. Usage: python scripts/score_micro_s55.py [psalm] [--list-new]

"New ground" is measured against the UNION of all three 4.6 runs (a phrase target counts as new
only if no 4.6 run touched any of its consonantal words in that verse). Each 4.6 run is also
scored against the OTHER two, which is the noise floor: what a fresh 4.6 run finds "new" by
chance.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.cost_tracker import price_tokens
from src.concordance.hebrew_text_processor import normalize_for_search as N

args = [a for a in sys.argv[1:] if not a.startswith("--")]
PSALM = int(args[0]) if args else 76
LIST_NEW = "--list-new" in sys.argv
P = f"output/psalm_{PSALM}"
S382 = "archive/psalm_76_S382_micro_sonnet5_ab"

# (label, micro json, cost json, model, family)
ARMS = ([] if PSALM != 76 else [
    ("4.6 Sep17", f"{P}/psalm_{PSALM:03d}_micro_v2.json", f"{P}/psalm_{PSALM:03d}_cost.json", "claude-sonnet-4-6", "4.6"),
    ("4.6 Sep24", f"{P}/_opus55_B/psalm_{PSALM:03d}_micro_v2.json", f"{P}/_opus55_B/psalm_{PSALM:03d}_cost.json", "claude-sonnet-4-6", "4.6"),
    ("4.6 Sep30", f"output/_s391_reception_ab/psalm_{PSALM}/A/psalm_{PSALM}/psalm_{PSALM:03d}_micro_v2.json",
                  f"output/_s391_reception_ab/psalm_{PSALM}/A/psalm_{PSALM}/psalm_{PSALM:03d}_cost.json", "claude-sonnet-4-6", "4.6"),
    ("S5 xhigh", f"{S382}/arm_sonnet5_xhigh/psalm_{PSALM:03d}_micro_v2.json", f"{S382}/arm_sonnet5_xhigh/cost.json", "claude-sonnet-5", "5"),
    ("S5 max", f"{S382}/arm_sonnet5_max/psalm_{PSALM:03d}_micro_v2.json", f"{S382}/arm_sonnet5_max/cost.json", "claude-sonnet-5", "5"),
]) + ([] if PSALM == 76 else [
    ("4.6 prod", f"{P}/psalm_{PSALM:03d}_micro_v2.json", f"{P}/psalm_{PSALM:03d}_cost.json", "claude-sonnet-4-6", "4.6"),
]) + [(f"S5.5 {e}", f"{P}/_micro_s55_ab_{e}/psalm_{PSALM:03d}_micro_v2.json", f"{P}/_micro_s55_ab_{e}/cost.json",
      "claude-sonnet-5-5", "5.5") for e in ("low", "medium", "high", "xhigh", "max")]


def words(phrase):
    return set(N(phrase or "", "consonantal").split())


def coverage(vc):
    cov = {}
    for v in vc:
        s = set()
        for li in v.get("lexical_insights") or []:
            s |= words(li.get("phrase"))
        cov[v["verse_number"]] = s
    return cov


rows = []
for name, mp, cp, model, fam in ARMS:
    mp, cp = ROOT / mp, ROOT / cp
    if not mp.exists():
        continue
    d = json.load(open(mp, encoding="utf-8"))
    vc = d["verse_commentaries"]
    u = json.load(open(cp, encoding="utf-8")).get(model) if cp.exists() else None
    if u:  # S387's Ps 77 run never recorded its Sonnet tokens -> cost/tokens shown as "—"
        cost = price_tokens(model, input_tokens=u["input_tokens"], output_tokens=u["output_tokens"],
                            thinking_tokens=u.get("thinking_tokens", 0))
    else:
        cost, u = None, {"output_tokens": None}
    shim = mp.parent / "shim_log.json"
    secs = None
    if shim.exists():
        sl = json.load(open(shim, encoding="utf-8"))
        if isinstance(sl, dict):
            secs = sl.get("stage1_seconds", 0) + sl.get("stage2_seconds", 0)
    lex = sum(len(v.get("lexical_insights") or []) for v in vc)
    detail = sum(len(li.get("notes") or "") for v in vc for li in (v.get("lexical_insights") or []))
    figs = [len(v.get("figurative_analysis") or []) for v in vc]
    rows.append(dict(name=name, fam=fam, vc=vc, lex=lex, detail=detail, per=detail // max(lex, 1),
                     fig=sum(figs), figs=figs, q=len(d.get("interesting_questions") or []),
                     prose=sum(len(v.get("commentary") or "") for v in vc),
                     size=os.path.getsize(mp), cost=cost, o=u["output_tokens"], secs=secs,
                     cov=coverage(vc)))

base46 = [r for r in rows if r["fam"] == "4.6"]
union46 = {}
for r in base46:
    for vn, s in r["cov"].items():
        union46.setdefault(vn, set()).update(s)


def new_targets(r, ref):
    return [(v["verse_number"], li.get("phrase", ""), li.get("notes", ""))
            for v in r["vc"] for li in (v.get("lexical_insights") or [])
            if not (words(li.get("phrase")) & ref.get(v["verse_number"], set()))]


for r in rows:
    if r["fam"] == "4.6" and len(base46) > 1:
        others = {}
        for o in base46:
            if o is not r:
                for vn, s in o["cov"].items():
                    others.setdefault(vn, set()).update(s)
        r["new"] = new_targets(r, others)
    elif r["fam"] == "4.6":
        r["new"] = []
    else:
        r["new"] = new_targets(r, union46)

lbl = 26
w = "{:<%d}" % lbl + "{:>11}" * len(rows)
print(f"PSALM {PSALM} MICRO ARMS (new ground: 4.6 rows vs the other two 4.6 runs; others vs all three)\n")
print(w.format("", *[r["name"] for r in rows]))
print("-" * (lbl + 11 * len(rows)))
for k, label in [("cost", "cost $"), ("o", "output tokens"), ("secs", "wall clock (min)"),
                 ("lex", "lexical insights"), ("detail", "lexical notes (chars)"),
                 ("per", "chars per insight"), ("fig", "figurative flags"),
                 ("q", "interesting questions"), ("prose", "verse commentary (chars)"),
                 ("size", "JSON bytes"), ("newn", "new phrase targets")]:
    vals = []
    for r in rows:
        v = len(r["new"]) if k == "newn" else r[k]
        if v is None:
            vals.append("—")
        elif k == "cost":
            vals.append(f"{v:.3f}")
        elif k == "secs":
            vals.append(f"{v / 60:.1f}")
        else:
            vals.append(f"{v:,}")
    print(w.format(label, *vals))
print("\nfigurative flags per verse:")
for r in rows:
    print(f"  {r['name']:<10} {r['figs']}")

if LIST_NEW:
    for r in rows:
        if r["fam"] == "4.6":
            continue
        print(f"\n=== {r['name']}: {len(r['new'])} new phrase targets ===")
        for vn, p, notes in r["new"]:
            print(f"  v{vn}: {p}\n      {notes[:400]}")
