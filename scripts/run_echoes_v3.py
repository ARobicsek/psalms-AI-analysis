"""
Echoes v3 (Session 388, EXPERIMENTAL): propose (Opus 5.5 + GPT-6 Sol + Gemini 3.1 Pro,
no quotations) -> judge (Opus 5.5, aptness first) -> retrieve (gpt-6-luna + web) -> $0
page check -> deterministic dossier. See src/agents/echoes_v3.py.

Writes ONLY to output/psalm_N/echoes_v3/ (or --out-dir). Never touches
data/literary_echoes/, so the production dossier and the author ledger are unchanged.

    python scripts/run_echoes_v3.py 77 --dry-run      # prompt + budgets, $0
    python scripts/run_echoes_v3.py 77                # ~$1 (estimate)
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from src.agents.echoes_v3 import (  # noqa: E402
    PROPOSE_PROMPT, PROPOSER_MODELS, EchoesV3Agent, budgets, cost_report, reading_from_macro,
)
from src.data_sources.tanakh_database import TanakhDatabase  # noqa: E402


def psalm_text(n: int, db_path: str = "database/tanakh.db"):
    psalm = TanakhDatabase(Path(db_path)).get_psalm(n)
    if not psalm:
        raise SystemExit(f"Psalm {n} not found in {db_path}")
    lines = []
    for v in psalm.verses:
        lines += [f"**{n}:{v.verse}** {v.hebrew}", v.english, ""]
    return "\n".join(lines).strip(), len(psalm.verses)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("psalm", type=int)
    ap.add_argument("--out-dir", type=Path)
    ap.add_argument("--proposers", nargs="+", default=list(PROPOSER_MODELS))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume", action="store_true", help="reuse saved proposals + judge; redo retrieval")
    ap.add_argument("--reextract", action="store_true", help="$0: re-cut passages from the saved page locations")
    a = ap.parse_args()

    text, n_verses = psalm_text(a.psalm)
    macro_path = Path(f"output/psalm_{a.psalm}/psalm_{a.psalm:03d}_macro.json")
    macro = json.loads(macro_path.read_text(encoding="utf-8")) if macro_path.exists() else {}
    if not macro:
        print(f"WARNING: no macro analysis at {macro_path}; the proposers read the text only")
    b = budgets(n_verses)
    if a.dry_run:
        import random
        from src.agents.echoes_v3 import FAR_DOMAINS
        rng = random.Random(f"{a.psalm}-{a.proposers[0]}")
        print(PROPOSE_PROMPT.format(psalm=a.psalm, psalm_text=text, reading=reading_from_macro(macro),
                                    used_works="(built at run time from the finished guides)",
                                    n_lit=b["propose_lit"], n_beyond=b["propose_beyond"], n_far=b["propose_far"],
                                    domains=", ".join(rng.sample(FAR_DOMAINS, 15))))
        print(f"\n--- {n_verses} verses; budgets {b}; proposers {a.proposers}")
        return

    out = a.out_dir or Path(f"output/psalm_{a.psalm}/echoes_v3_1")   # v3's trial stays in echoes_v3/
    if a.reextract:
        res = EchoesV3Agent().reextract(a.psalm, out)
        print(json.dumps(cost_report(res)["entry_status"], indent=1))
        return
    res = EchoesV3Agent(proposers=a.proposers).run(a.psalm, text, n_verses, macro, out, resume=a.resume)
    rep = cost_report(res)
    print(json.dumps(rep, indent=1))
    print(f"\nDossier: {out / 'final.md'}   Total ${res.total_usd:.2f}")


if __name__ == "__main__":
    main()
