"""Session 386: re-run ONLY the fact checker's web stage on the claims a previous run
sent there, with a different web model, and compare verdicts claim by claim.

    python archive/psalm_76_S386_fact_check_cost/web_only.py sol_v3 gemini-3.1-pro-preview high
"""
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
from dotenv import load_dotenv  # noqa: E402
load_dotenv(ROOT / ".env")

from src.agents.fact_checker import FactChecker, validate_records  # noqa: E402

HERE = Path(__file__).resolve().parent
BUNDLE = ROOT / "archive/psalm_76_S384_essay_trials/prompts/inputs_block.txt"


def main():
    src, model, effort = sys.argv[1], sys.argv[2], sys.argv[3]
    base = json.loads((HERE / src / "psalm_076_fact_check.json").read_text(encoding="utf-8"))["claims"]
    claims = [r for r in base if r.get("stage") == "web"]
    out = HERE / f"{src}_web_{model}_{effort}"
    out.mkdir(exist_ok=True)
    fc = FactChecker(db_path=ROOT / "database/tanakh.db", web_model=model, web_effort=effort)
    t0 = time.time()
    runs = fc._claims_stage("web", 76, claims, BUNDLE.read_text(encoding="utf-8"))
    recs = validate_records([r for res in runs for r in res["records"]])
    spent = {m: {"usage": v["usage"], "searches": v["searches"],
                 "cost_usd": round(fc._price(m, v["usage"], v["searches"]), 4)} for m, v in fc._spent.items()}
    (out / "web_records.json").write_text(json.dumps({"spent": spent, "seconds": round(time.time() - t0),
                                                     "records": recs,
                                                     "sources": [r.get("sources") for r in runs],
                                                     "queries": [r.get("queries") for r in runs]},
                                                    ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "thinking.txt").write_text("\n\n".join(f"## {r['label']}\n{r['thinking']}" for r in runs),
                                      encoding="utf-8")
    print(json.dumps(spent, indent=1), f"{time.time() - t0:.0f}s")
    print("baseline:", Counter(r["verdict"] for r in claims), " new:", Counter(r["verdict"] for r in recs))
    by_sent = {r["sentence"]: r for r in recs}
    for r in claims:
        n = by_sent.get(r["sentence"])
        nv = n["verdict"] if n else "MISSING"
        if nv != r["verdict"] or nv == "contradicted":
            print(f"\n[{r['verdict']} -> {nv}] {r['location']} | {r['sentence'][:120]}")
            if n:
                print("   NEW:", n["explanation"][:260])
                if n["verdict"] == "contradicted":
                    print("   EV:", json.dumps(n["evidence"], ensure_ascii=False)[:300])


if __name__ == "__main__":
    main()
