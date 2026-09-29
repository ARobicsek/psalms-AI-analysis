"""Session 386: how many gathered passages are REAL (found on the live page) per Gemini model?
Gather only, no judge.  python archive/psalm_76_S386_fact_check_cost/gather_probe.py gemini-3.8-flash low
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
from dotenv import load_dotenv  # noqa: E402
load_dotenv(ROOT / ".env")
from src.agents.fact_checker import (FactChecker, GATHER_INSTRUCTIONS, GATHER_SCHEMA,  # noqa: E402
                                     claims_block, verify_sources)

HERE = Path(__file__).resolve().parent


def main():
    model, effort = sys.argv[1], sys.argv[2]
    base = json.loads((HERE / "sol_v3" / "psalm_076_fact_check.json").read_text(encoding="utf-8"))["claims"]
    claims = [r for r in base if r.get("stage") == "web"]
    fc = FactChecker(db_path=ROOT / "database/tanakh.db", web_model=model, web_effort=effort)
    batches = [claims[i:i + 8] for i in range(0, len(claims), 8)]
    t0 = time.time()

    def gather(i):
        return fc._gemini_web(f"gather {i + 1}", model, effort,
                              GATHER_INSTRUCTIONS.format(psalm=76, claims=claims_block(batches[i])), GATHER_SCHEMA)
    with ThreadPoolExecutor(max_workers=9) as ex:
        runs = list(ex.map(gather, range(len(batches))))
    items = [{"sources": g.get("sources", [])} for r in runs for g in r["records"]]
    vc = verify_sources(items)
    with_src = sum(1 for it in items if it["sources"])
    with_ver = sum(1 for it in items if any(s.get("verified") for s in it["sources"]))
    spent = {m: round(fc._price(m, v["usage"], v["searches"]), 4) for m, v in fc._spent.items()}
    out = {"model": model, "effort": effort, "cost": spent, "seconds": round(time.time() - t0),
           "google_queries": sum(r["searches"] for r in runs), "claims": len(claims), "items": len(items),
           "claims_with_sources": with_src, "claims_with_a_verified_source": with_ver, "verify": vc}
    print(json.dumps(out, indent=1))
    (HERE / f"gather_probe_{model}_{effort}.json").write_text(
        json.dumps({"summary": out, "items": items}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
