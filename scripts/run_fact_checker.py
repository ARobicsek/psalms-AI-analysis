#!/usr/bin/env python3
"""
Standalone fact check (Session 385): verify a guide's checkable claims against
evidence, and write a report the copy editor can take as supplementary context.

    python scripts/run_fact_checker.py 76                       # output/psalm_76/psalm_076_print_ready.md
    python scripts/run_fact_checker.py 76 --input-file X.md --bundle inputs.txt --output-dir DIR
    python scripts/run_fact_checker.py 76 --dry-run             # show the chunks, no API call
    python scripts/run_copy_editor.py 76 --fact-check-report DIR/psalm_076_fact_check.json

Writes psalm_NNN_fact_check.json (records + cost), .md (readable) and
_copy_editor_prompt.txt (the block the copy editor receives). Staged (Session 386):
gpt-6-luna on local evidence, gpt-6-sol with web search on what needs the web, and
gpt-6-sol reviewing every contradiction. See src/agents/fact_checker.py.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv  # noqa: E402
load_dotenv(ROOT / ".env")  # OPENAI_API_KEY, before any client is created

from src.agents.fact_checker import (  # noqa: E402
    DEFAULT_EFFORT, DEFAULT_MODEL, DEFAULT_REVIEW_MODEL, DEFAULT_WEB_MODEL, FactChecker,
    checkable_text, split_guide_for_checking, write_outputs,
)


def default_bundle(psalm: int) -> Path:
    d = Path(f"output/psalm_{psalm}")
    for name in (f"psalm_{psalm:03d}_research_trimmed.md", f"psalm_{psalm:03d}_research_v2.md"):
        if (d / name).exists():
            return d / name
    return d / f"psalm_{psalm:03d}_research_v2.md"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("psalm", type=int)
    ap.add_argument("--input-file", type=Path, help="guide markdown (default: the psalm's print_ready.md)")
    ap.add_argument("--bundle", type=Path, help="research bundle (default: the psalm's research_trimmed/_v2.md)")
    ap.add_argument("--no-bundle", action="store_true", help="check without the research bundle")
    ap.add_argument("--output-dir", type=Path, help="default: the input file's folder")
    ap.add_argument("--prefix", default="", help="filename prefix for the outputs")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--effort", default=DEFAULT_EFFORT)
    ap.add_argument("--web-model", default=DEFAULT_WEB_MODEL)
    ap.add_argument("--review-model", default=DEFAULT_REVIEW_MODEL, help="'none' to skip the review stage")
    ap.add_argument("--db-path", type=Path, default=ROOT / "database" / "tanakh.db")
    ap.add_argument("--no-web-search", action="store_true")
    ap.add_argument("--chunk-chars", type=int, default=None)
    ap.add_argument("--service-tier", default="flex",
                    help="OpenAI tier: 'flex' (Session 397 default, half price, slower) or 'default' (standard)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    inp = a.input_file or Path(f"output/psalm_{a.psalm}/psalm_{a.psalm:03d}_print_ready.md")
    if not inp.exists():
        print(f"Not found: {inp}")
        return 1
    bundle_path = None if a.no_bundle else (a.bundle or default_bundle(a.psalm))
    bundle = bundle_path.read_text(encoding="utf-8") if bundle_path and bundle_path.exists() else ""
    if bundle_path and not bundle:
        print(f"WARNING: bundle {bundle_path} not found; checking without it")
    guide = inp.read_text(encoding="utf-8")

    kw = {"chunk_chars": a.chunk_chars} if a.chunk_chars else {}
    if a.dry_run:
        chunks = split_guide_for_checking(checkable_text(guide), **({"max_chars": a.chunk_chars} if a.chunk_chars else {}))
        print(f"{inp}: {len(checkable_text(guide)):,} checkable chars → {len(chunks)} chunk(s); bundle {len(bundle):,} chars")
        for c in chunks:
            print(f"  [{c['label']}] {len(c['text']):,} chars")
        return 0

    out_dir = a.output_dir or inp.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    fc = FactChecker(model=a.model, effort=a.effort, db_path=a.db_path, web_search=not a.no_web_search,
                     web_model=a.web_model,
                     review_model=None if (a.review_model or "none").lower() == "none" else a.review_model,
                     service_tier=None if a.service_tier == "default" else a.service_tier, **kw)
    res = fc.check(guide, a.psalm, bundle, thinking_out=out_dir / f"{a.prefix}psalm_{a.psalm:03d}_fact_check_thinking.txt")
    paths = write_outputs(res, a.psalm, out_dir, a.prefix)
    m = res.meta(a.psalm)
    print(f"\nClaims: {len(res.records)}  {m['verdicts']}")
    print(f"Web searches: {res.web_searches}  lookups: {res.function_calls}  "
          f"cost: ${res.cost_usd:.4f} (tokens ${res.token_cost_usd:.4f} + searches ${res.search_cost_usd:.4f})")
    for m, v in (m_ := res.meta(a.psalm))["stages"].get("per_stage", {}).items():
        print(f"  {m} ({v['model']}): ${v['cost_usd']:.4f}; {v['searches']} searches; tools {v['tools']}; "
              f"tokens {v['usage']}")
    print(f"  stage 1: {m_['stages']['local']}")
    for p in paths.values():
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
