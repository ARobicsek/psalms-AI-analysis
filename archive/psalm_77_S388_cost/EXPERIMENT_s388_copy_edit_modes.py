"""Session 388 experiment: the copy editor in "edits" mode on the Ps 77 guide, with the same
inputs the S387 production copy edit had (print_ready.md + the Ps 57:9 citation fix + the
fact-check report), written to output/psalm_77/_s388_copy_edit_<mode>/ so nothing in the
psalm's own folder changes (the one shared file, the copy editor's thinking capture, is
backed up and restored).

    python scripts/EXPERIMENT_s388_copy_edit_modes.py 77 --mode edits
"""
import argparse
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from src.agents.copy_editor import CopyEditor  # noqa: E402
from src.agents.fact_checker import combine_supplementary, format_copy_editor_prompt  # noqa: E402
from src.utils.cost_tracker import CostTracker  # noqa: E402
from src.utils.debug_paths import thinking_file  # noqa: E402
from src.utils.scripture_verifier import format_fix_prompt, verify_citations  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("psalm", type=int)
    ap.add_argument("--mode", choices=("full", "edits"), default="edits")
    ap.add_argument("--keep-citation", default="57:9",
                    help="the citation issue(s) the paid false-positive filter kept in production")
    a = ap.parse_args()
    ps = a.psalm
    d = Path(f"output/psalm_{ps}")
    out = d / f"_s388_copy_edit_{a.mode}"
    out.mkdir(exist_ok=True)
    print_ready = d / f"psalm_{ps:03d}_print_ready.md"

    issues = verify_citations(print_ready.read_text(encoding="utf-8"), db_path=Path("database/tanakh.db"),
                              psalm_number=ps)
    kept = [i for i in issues if a.keep_citation in i.citation_ref]
    citation_prompt = format_fix_prompt(kept) if kept else None
    recs = json.loads((d / f"psalm_{ps:03d}_fact_check.json").read_text(encoding="utf-8"))["claims"]
    fc_prompt = format_copy_editor_prompt(recs) or None
    saved = (d / f"psalm_{ps:03d}_fact_check_copy_editor_prompt.txt")
    if saved.exists():
        print("fact-check prompt identical to the one saved at run time:",
              saved.read_text(encoding="utf-8").strip() == (fc_prompt or "").strip())
    print(f"citation issues: {len(issues)} found, {len(kept)} kept ({[i.citation_ref for i in kept]})")

    thinking = thinking_file(ps, "copy_editor")
    backup = thinking.with_suffix(".s388bak")
    if thinking.exists():
        shutil.copy2(thinking, backup)
    tracker = CostTracker()
    t0 = time.time()
    try:
        ed = CopyEditor(cost_tracker=tracker, edit_mode=a.mode)
        ed.edit_commentary(ps, input_file=print_ready, output_dir=out,
                           supplementary_prompt=combine_supplementary(citation_prompt, fc_prompt))
    finally:
        if backup.exists():
            shutil.move(backup, thinking)
    summary = {"mode": a.mode, "model": ed.model, "seconds": round(time.time() - t0),
               "cost_usd": round(tracker.get_total_cost(), 4), "usage": tracker.to_dict().get(ed.model),
               "edit_stats": ed.last_edit_stats}
    (out / "run_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
