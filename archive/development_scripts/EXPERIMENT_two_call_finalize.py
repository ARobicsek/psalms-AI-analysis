"""
EXPERIMENT — Finalize the two-call output through the real downstream pipeline
==============================================================================

Takes the two-call experiment writer output and runs it through the SAME
downstream steps production uses — Print-Ready -> Scripture Verifier ->
Copy Editor -> section extraction -> DOCX — so the result is the .docx the
user actually reads for review.

ISOLATION GUARANTEE (discardable, non-destructive)
--------------------------------------------------
Every file this script *writes* lands inside:
      output/psalm_<N>/EXPERIMENT_two_call/
The ONLY production files touched are READ-ONLY:
  - output/psalm_<N>/psalm_0<N>_pipeline_stats.json  (for DOCX methodology)
  - database/tanakh.db                                (citation verification)
It does NOT call run_scripture_verifier.py or run_docx_only.py (both hardcode
production output paths). Instead it invokes the same underlying classes /
functions with experiment-isolated paths, mirroring run_enhanced_pipeline.py
steps 5 -> 5a1/2 -> 5b -> 5c -> 6 exactly.

To discard: delete scripts/EXPERIMENT_two_call_*.py and the
output/psalm_<N>/EXPERIMENT_two_call/ directory.

Usage
-----
    python scripts/EXPERIMENT_two_call_finalize.py 55
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

DB_PATH = "database/tanakh.db"


def main() -> None:
    psalm = int(sys.argv[1]) if len(sys.argv) > 1 else 55
    pp = f"{psalm:03d}"
    exp = ROOT / f"output/psalm_{psalm}/EXPERIMENT_two_call"
    prod = ROOT / f"output/psalm_{psalm}"

    intro_md = exp / "TWO_CALL_intro.md"
    verses_md = exp / "TWO_CALL_verses.md"
    for f in (intro_md, verses_md):
        if not f.exists():
            sys.exit(f"Missing experiment input: {f} (run EXPERIMENT_two_call_synthesis.py first)")

    # Read-only production artifact used by the DOCX for methodology/model info.
    summary_json = prod / f"psalm_{pp}_pipeline_stats.json"
    if not summary_json.exists():
        summary_json = prod / f"psalm_{pp}_summary.json"

    print(f"\n{'='*70}\n  FINALIZE two-call Psalm {psalm}  (isolated -> {exp})\n{'='*70}")

    # ---- STEP 5: Print-Ready (subprocess, identical to production) --------
    print_ready = exp / f"psalm_{pp}_print_ready.md"
    print("[5] Print-Ready formatting...")
    cmd = [
        sys.executable,
        str(ROOT / "src" / "utils" / "commentary_formatter.py"),
        "--psalm", str(psalm),
        "--intro", str(intro_md),
        "--verses", str(verses_md),
        "--summary", str(summary_json),
        "--output", str(print_ready),
        "--db-path", DB_PATH,
    ]
    subprocess.run(cmd, check=False)
    if not print_ready.exists():
        sys.exit("[5] Print-Ready failed — no output produced.")
    print(f"    -> {print_ready.name} ({print_ready.stat().st_size:,} bytes)")

    # ---- STEP 5a1/2: Scripture Citation Verifier -------------------------
    from src.utils.cost_tracker import CostTracker
    from src.utils.scripture_verifier import (
        verify_citations,
        filter_false_positives,
        format_verification_report,
        format_fix_prompt,
    )

    cost = CostTracker()
    print("[5a.5] Scripture citation verification (GPT-5.1 FP filter, pipeline default)...")
    verify_text = print_ready.read_text(encoding="utf-8")
    issues = verify_citations(verify_text, db_path=DB_PATH, psalm_number=psalm)

    citation_fix_prompt = None
    if issues:
        fixable = [i for i in issues if i.issue_type == "NOT_SUBSTRING"]
        if fixable:
            issues, fstats = filter_false_positives(
                issues, commentary_text=verify_text, model="gpt", cost_tracker=cost
            )
            print(f"    GPT-5.1 filter: kept {fstats['kept_count']}, "
                  f"filtered {fstats['filtered_count']} (${fstats['cost']:.4f})")
    report = format_verification_report(issues, psalm_number=psalm)
    (exp / "citation_verification.md").write_text(report, encoding="utf-8")
    if issues:
        print(f"    {len(issues)} issue(s) -> citation_verification.md")
        for it in issues:
            print(f"      {it.issue_type}: {it.citation_ref} at {it.location_hint}")
        citation_fix_prompt = format_fix_prompt(issues)
    else:
        print("    All citations verified — no misquotes detected.")

    # ---- STEP 5b: Copy Editor (isolated output_dir) ----------------------
    from src.agents.copy_editor import CopyEditor

    print("[5b] Copy Editor (gpt-5.4 default, citation fixes fed in)...")
    editor = CopyEditor(cost_tracker=cost)
    ce = editor.edit_commentary(
        psalm_number=psalm,
        input_file=print_ready,
        output_dir=exp,
        supplementary_prompt=citation_fix_prompt,
    )
    copy_edited = Path(ce["edited_file"])
    print(f"    -> {copy_edited.name}")

    # ---- STEP 5c: Extract copy-edited sections (pure helper, no writes) ---
    from scripts.run_enhanced_pipeline import _extract_sections_from_copy_edited

    print("[5c] Extracting copy-edited intro/verses for DOCX...")
    intro_text, verses_text = _extract_sections_from_copy_edited(copy_edited)
    if not (intro_text and verses_text):
        print("    WARNING: extraction returned empty; falling back to copy_edited as both.")
        intro_text = verses_text = copy_edited.read_text(encoding="utf-8")
    ce_intro = exp / f"psalm_{pp}_edited_intro.md"
    ce_verses = exp / f"psalm_{pp}_edited_verses.md"
    ce_intro.write_text(intro_text, encoding="utf-8")
    ce_verses.write_text(verses_text, encoding="utf-8")

    # ---- STEP 6: DOCX (q_file=None — Psalm 55 had questions suppressed) ---
    from src.utils.document_generator import DocumentGenerator

    docx_out = exp / f"psalm_{psalm}_TWO_CALL_commentary.docx"
    print("[6] DOCX generation...")
    DocumentGenerator(
        psalm, ce_intro, ce_verses, summary_json, docx_out, None
    ).generate()

    print(f"\n[DONE] Review artifact: {docx_out}")
    print(f"       Costs this run: {cost.get_summary()}")
    print(f"\nCompare against shipped baseline DOCX:")
    print(f"  {prod / ('psalm_' + pp + '_commentary.docx')}")


if __name__ == "__main__":
    main()
