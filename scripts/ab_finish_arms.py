"""
Finish both writer-A/B arms through the rest of the pipeline (Session 367).

ab_writer_models.py stops at the Master Writer. This takes each arm the rest of
the way — print-ready formatting, scripture citation verification, copy editor,
section re-extraction, and DOCX generation — so the two models can be compared as
finished Word documents rather than as raw writer output.

It mirrors run_enhanced_pipeline.py STEP 5 -> 5a½ -> 5b -> 5c -> STEP 6, calling
the same formatter, verifier, CopyEditor and DocumentGenerator with the same
arguments. Every step is pointed at the arm's own directory, so production files
for the psalm are never touched. (DocumentGenerator constructs a
DivineNamesModifier internally, so both arms get the Session-366 divine-names
conversion automatically.)

Usage:
    python scripts/ab_finish_arms.py 70
    python scripts/ab_finish_arms.py 70 --skip-verify        # cheaper, skips 5a½
    python scripts/ab_finish_arms.py 70 --copy-to-documents  # also drop labelled
                                                             # .docx in Documents/

Cost: roughly $0.35-0.60 per arm (copy editor dominates; citation verification
adds ~$0.15). Both arms together land near $1.

Archive after the session.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from src.agents.copy_editor import CopyEditor
from src.utils.cost_tracker import CostTracker
from src.utils.document_generator import DocumentGenerator
from src.utils.logger import get_logger
# Reuse the pipeline's own extractor so 5c behaves identically here.
from scripts.run_enhanced_pipeline import _extract_sections_from_copy_edited

# Human-readable labels for the printed .docx, so the two are distinguishable
# on paper without opening properties.
ARM_LABELS = {
    "claude-opus-4-8": "Opus 4.8",
    "claude-opus-5": "Opus 5",
}


def run_print_ready(pn: int, arm_dir: Path, stats_file: Path, db_path: str, logger) -> Path:
    """STEP 5 — same subprocess call the pipeline makes."""
    intro = arm_dir / f"psalm_{pn:03d}_edited_intro.md"
    verses = arm_dir / f"psalm_{pn:03d}_edited_verses.md"
    out = arm_dir / f"psalm_{pn:03d}_print_ready.md"
    cmd = [
        sys.executable,
        str(ROOT / "src" / "utils" / "commentary_formatter.py"),
        "--psalm", str(pn),
        "--intro", str(intro),
        "--verses", str(verses),
        "--summary", str(stats_file),
        "--output", str(out),
        "--db-path", db_path,
    ]
    subprocess.run(cmd, check=False)
    if not out.exists():
        raise RuntimeError(f"print-ready formatting produced no output at {out}")
    logger.info(f"  print-ready: {out.name} ({out.stat().st_size:,} bytes)")
    return out


def run_citation_verification(pn: int, print_ready: Path, arm_dir: Path, db_path: str,
                              tracker: CostTracker, logger) -> str:
    """STEP 5a½ — regex verify, then the GPT-5.1 false-positive filter the
    pipeline runs by default. Returns a fix prompt for the copy editor, or ''.

    Note verify_citations() takes NO cost_tracker (it is pure DB work); only the
    LLM filter is billable. The report is written into the arm's own directory.
    """
    from src.utils.scripture_verifier import (
        verify_citations, format_verification_report, format_fix_prompt,
        filter_false_positives,
    )
    text = print_ready.read_text(encoding="utf-8")
    issues = verify_citations(text, db_path=db_path, psalm_number=pn)

    fixable = [i for i in issues if i.issue_type == "NOT_SUBSTRING"]
    if fixable:
        issues, stats = filter_false_positives(
            issues, commentary_text=text, model="gpt", cost_tracker=tracker,
        )
        logger.info(f"  citation filter (GPT-5.1): kept {stats['kept_count']}, "
                    f"filtered {stats['filtered_count']} (${stats['cost']:.4f})")

    report_path = arm_dir / f"psalm_{pn:03d}_citation_verification.md"
    report_path.write_text(format_verification_report(issues, psalm_number=pn), encoding="utf-8")

    if not issues:
        logger.info("  citations: clean")
        return ""
    logger.info(f"  citations: {len(issues)} issue(s) -> fix prompt for copy editor")
    for i in issues:
        logger.info(f"    {i.issue_type}: {i.citation_ref}")
    return format_fix_prompt(issues)


def _arm_stats_file(pn: int, model: str, arm_dir: Path, stats_file: Path,
                    copy_editor_model: str, logger) -> Path:
    """
    Copy the production pipeline stats into the arm, correcting the models this
    arm actually used. Only the writer (and the copy editor, when overridden)
    differ from production; every other entry is genuinely shared, since
    ab_writer_models.py re-reads the same upstream artifacts.

    Falls back to the original file if anything is unreadable — a wrong
    methodology line must never cost the arm its document.
    """
    try:
        stats = json.loads(stats_file.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"  could not patch stats for methodology block ({e}); using production stats")
        return stats_file

    usage = stats.setdefault("model_usage", {})
    was = usage.get("master_writer")
    usage["master_writer"] = model
    if copy_editor_model:
        usage["copy_editor"] = copy_editor_model
    out = arm_dir / f"psalm_{pn:03d}_pipeline_stats.json"
    out.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    if was != model:
        logger.info(f"  methodology: master_writer {was} -> {model}")
    return out


def finish_arm(pn: int, model: str, ab_dir: Path, stats_file: Path,
               db_path: str, skip_verify: bool, logger,
               copy_editor_model: str = None) -> dict:
    arm_dir = ab_dir / model
    label = ARM_LABELS.get(model, model)
    print(f"\n{'='*70}\nFinishing arm: {model}  ({label})\n{'='*70}")

    intro = arm_dir / f"psalm_{pn:03d}_edited_intro.md"
    verses = arm_dir / f"psalm_{pn:03d}_edited_verses.md"
    for f in (intro, verses):
        if not f.exists():
            raise FileNotFoundError(f"missing writer output: {f}")

    tracker = CostTracker()
    result = {"model": model, "label": label}

    # STEP 5 — the methodology block the formatter renders reads model_usage
    # straight out of the pipeline stats file, which belongs to the PRODUCTION
    # run and names the PRODUCTION writer. Feeding it unpatched makes every arm
    # credit its commentary to whichever model happened to run in production
    # (Session 368: both Ps 70 and Ps 71 Opus-5 documents said
    # "Master Writer: claude-opus-4-8"). Patch a per-arm copy instead.
    arm_stats = _arm_stats_file(pn, model, arm_dir, stats_file, copy_editor_model, logger)
    print_ready = run_print_ready(pn, arm_dir, arm_stats, db_path, logger)

    # STEP 5a½
    supplementary = ""
    if not skip_verify:
        try:
            supplementary = run_citation_verification(pn, print_ready, arm_dir, db_path,
                                                      tracker, logger)
        except Exception as e:
            logger.warning(f"  citation verification failed (non-fatal): {e}")

    # STEP 5b — output_dir pins the copy editor to THIS arm, not the psalm dir.
    copy_edited = arm_dir / f"psalm_{pn:03d}_copy_edited.md"
    try:
        editor = CopyEditor(cost_tracker=tracker, model=copy_editor_model)
        editor.edit_commentary(
            psalm_number=pn,
            input_file=print_ready,
            output_dir=arm_dir,
            supplementary_prompt=supplementary or None,
        )
        logger.info(f"  copy editor: {editor.model}")
        result["copy_editor_model"] = editor.model
    except Exception as e:
        logger.error(f"  copy editor FAILED (continuing with uncopy-edited text): {e}")
        result["copy_editor_error"] = str(e)

    # STEP 5c — fold copy-edited prose back into intro/verses for the DOCX,
    # preserving the pre-copy-edit originals exactly as the pipeline does.
    if copy_edited.exists():
        try:
            intro_text, verses_text = _extract_sections_from_copy_edited(copy_edited, logger=logger)
            if intro_text and verses_text:
                for src, dst_name in ((intro, f"psalm_{pn:03d}_edited_intro_pre_copy_edit.md"),
                                      (verses, f"psalm_{pn:03d}_edited_verses_pre_copy_edit.md")):
                    dst = arm_dir / dst_name
                    if src.exists() and not dst.exists():
                        shutil.copy2(src, dst)
                intro.write_text(intro_text, encoding="utf-8")
                verses.write_text(verses_text, encoding="utf-8")
                logger.info(f"  merged copy-edited sections ({len(intro_text):,} + {len(verses_text):,} chars)")
            else:
                logger.warning("  could not extract copy-edited sections; DOCX uses writer output")
        except Exception as e:
            logger.warning(f"  section extraction failed: {e}; DOCX uses writer output")

    # STEP 6 — filename carries the model label so the printouts are tellable apart.
    docx = arm_dir / f"Psalm {pn} ({label}).docx"
    # arm_stats, not stats_file — DocumentGenerator rebuilds the methodology
    # block from model_usage independently of the formatter (document_generator
    # :1632), so both readers need the arm-corrected copy.
    gen = DocumentGenerator(pn, intro, verses, arm_stats, docx, None)
    gen.generate()
    logger.info(f"  DOCX: {docx.name} ({docx.stat().st_size:,} bytes)")

    result["docx"] = docx
    result["cost_usd"] = round(tracker.get_total_cost(), 4)
    result["words"] = len(intro.read_text(encoding="utf-8").split()) + \
                      len(verses.read_text(encoding="utf-8").split())
    return result


def main() -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("psalm", type=int)
    ap.add_argument("--arms", nargs="+", default=None,
                    help="Arm subdirectory names (default: every arm present)")
    ap.add_argument("--skip-verify", action="store_true",
                    help="Skip STEP 5a½ scripture citation verification")
    ap.add_argument("--db-path", default="database/tanakh.db")
    ap.add_argument("--copy-editor-model", default=None,
                    help="Override the copy editor model for both arms "
                         "(e.g. gpt-5.4). Default: CopyEditor.DEFAULT_MODEL.")
    ap.add_argument("--copy-to-documents", action="store_true",
                    help="Also copy each .docx into 'Documents/Psalm study guide/'")
    args = ap.parse_args()
    pn = args.psalm

    logger = get_logger("ab_finish_arms")
    ab_dir = ROOT / "output" / f"psalm_{pn}" / "_writer_ab"
    if not ab_dir.exists():
        print(f"ERROR: no A/B output at {ab_dir.relative_to(ROOT)}. "
              f"Run: python scripts/ab_writer_models.py {pn}", file=sys.stderr)
        return 1

    arms = args.arms or sorted(d.name for d in ab_dir.iterdir() if d.is_dir())
    if not arms:
        print(f"ERROR: no arm directories inside {ab_dir.relative_to(ROOT)}", file=sys.stderr)
        return 1

    stats_file = ROOT / "output" / f"psalm_{pn}" / f"psalm_{pn:03d}_pipeline_stats.json"
    if not stats_file.exists():
        print(f"ERROR: missing {stats_file.relative_to(ROOT)}", file=sys.stderr)
        return 1

    results, failures = [], []
    for model in arms:
        try:
            results.append(finish_arm(pn, model, ab_dir, stats_file, args.db_path,
                                      args.skip_verify, logger,
                                      copy_editor_model=args.copy_editor_model))
        except Exception as e:
            # One arm failing must not cost you the other arm's finished document.
            logger.error(f"arm {model} failed: {e}", exc_info=True)
            failures.append((model, str(e)))

    if args.copy_to_documents and results:
        dest = ROOT / "Documents" / "Psalm study guide"
        dest.mkdir(parents=True, exist_ok=True)
        for r in results:
            target = dest / r["docx"].name
            shutil.copy2(r["docx"], target)
            print(f"  copied -> {target.relative_to(ROOT)}")

    print(f"\n{'='*70}\nFINISHED — Psalm {pn}\n{'='*70}")
    for r in results:
        print(f"  {r['label']:<10} {r['words']:>6,} words  ${r['cost_usd']:.4f}  {r['docx'].name}")
        print(f"             {r['docx'].relative_to(ROOT)}")
    for model, err in failures:
        print(f"  {model}: FAILED — {err}")
    if results:
        print(f"\n  finishing cost: ${sum(r['cost_usd'] for r in results):.4f}")
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
