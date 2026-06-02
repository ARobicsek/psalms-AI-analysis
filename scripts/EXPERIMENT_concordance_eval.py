"""
Session 350 — Concordance value-add evaluation (DISCARDABLE; archive after session).

Re-runs ONLY the concordance-selection + retrieval path for a set of psalms, reusing
the production Stage-1 discoveries already saved in each psalm's micro_v2.json (so no
expensive re-discovery, and the lexical insights are identical to production).

For each psalm it:
  1. Reconstructs the `discoveries` dict from psalm_XXX_micro_v2.json.
  2. Runs the (modified) Stage-2 research-request generator -> concordance_requests
     [live LLM call: claude-sonnet-4-6]. This exercises the new prompt (A/B) and the
     deterministic distinctive-root augmentation (A) + 2-word cap (B).
  3. Runs each concordance request through the librarian with source_psalm set, so the
     self-match filter (C) applies.
  4. Reports per-search external yield and compares to the Session-349 baseline.

Usage:  python scripts/EXPERIMENT_concordance_eval.py 54 55 56 57 58
"""
import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import logging
logging.disable(logging.WARNING)  # keep INFO off the console; keep errors

from dotenv import load_dotenv
load_dotenv()

from src.agents.micro_analyst import MicroAnalystV2
from src.concordance.hebrew_text_processor import split_words

LIVE_DB = "database/tanakh.db"

# Session-349 baseline (measured from existing research_v2.md), per psalm:
# external-yielding searches / total searches
BASELINE = {54: (4, 10), 55: (1, 10), 56: (0, 10), 57: (5, 10), 58: (2, 10)}


def load_discoveries(psalm: int) -> dict:
    pp = f"{psalm:03d}"
    f = Path(f"output/psalm_{psalm}/psalm_{pp}_micro_v2.json")
    data = json.loads(f.read_text(encoding="utf-8"))
    verse_discoveries = []
    for vc in data.get("verse_commentaries", []):
        verse_discoveries.append({
            "verse_number": vc.get("verse_number"),
            "observations": vc.get("commentary", ""),
            "lexical_insights": vc.get("lexical_insights", []),
            "figurative_elements": vc.get("figurative_analysis", []),
        })
    return {"verse_discoveries": verse_discoveries}


def evaluate(psalm: int, analyst: MicroAnalystV2):
    discoveries = load_discoveries(psalm)
    research_request = analyst._generate_research_requests(discoveries, psalm)
    librarian = analyst.research_assembler.concordance_librarian

    COMMON_CAP = 120  # mirror ResearchAssembler post-search distinctiveness guard (Session 351)
    rows = []
    for req in research_request.concordance_requests:
        req.source_psalm = psalm  # ensure self-filter applies
        bundle = librarian.search_with_variations(req)
        nwords = len(split_words(req.query))
        is_root = "[root trace" in (req.notes or "")
        ext = len(bundle.results)
        dropped_common = (nwords <= 1 and ext > COMMON_CAP)
        rows.append({
            "query": req.query,
            "words": nwords,
            "kind": "ROOT" if is_root else ("COLLOC" if nwords >= 2 else "word"),
            "external": ext,
            "self_dropped": bundle.self_match_count,
            "only_self": bundle.only_self,
            "dropped_common": dropped_common,
            "refs": [r.reference for r in bundle.results][:8],
        })
    return rows


def main():
    psalms = [int(a) for a in sys.argv[1:]] or [54, 55, 56, 57, 58]
    analyst = MicroAnalystV2(db_path=LIVE_DB)

    g_total = g_ext = 0
    for psalm in psalms:
        print(f"\n{'='*78}\nPSALM {psalm}\n{'='*78}")
        try:
            rows = evaluate(psalm, analyst)
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"  ERROR on psalm {psalm}: {e}")
            continue
        kept = [r for r in rows if not r["dropped_common"]]
        ext_n = sum(1 for r in kept if r["external"] > 0)
        for r in rows:
            if r["dropped_common"]:
                tag = "DROPPED-common"
            elif r["external"] > 0:
                tag = "EXTERNAL"
            elif r["only_self"]:
                tag = "only-self"
            else:
                tag = "none"
            print(f"  [{r['kind']:6} {r['words']}w] {r['query']:22} ext={r['external']:3} "
                  f"self_drop={r['self_dropped']}  {tag:14} {r['refs']}")
        b_ext, b_tot = BASELINE.get(psalm, (None, None))
        print(f"  --- Psalm {psalm}: {ext_n}/{len(kept)} kept searches with EXTERNAL matches "
              f"({len(rows)-len(kept)} common dropped; baseline was {b_ext}/{b_tot})")
        g_total += len(kept); g_ext += ext_n

    if g_total:
        bb_ext = sum(BASELINE[p][0] for p in psalms if p in BASELINE)
        bb_tot = sum(BASELINE[p][1] for p in psalms if p in BASELINE)
        print(f"\n{'='*78}\nGRAND TOTAL: {g_ext}/{g_total} searches yielded an external match "
              f"= {100*g_ext/g_total:.0f}%")
        print(f"BASELINE   : {bb_ext}/{bb_tot} = {100*bb_ext/bb_tot:.0f}%")


if __name__ == "__main__":
    main()
