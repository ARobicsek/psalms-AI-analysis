"""
Writer-PROMPT A/B/C (Session 371).

Sibling of ab_writer_models.py: that script holds the prompt fixed and varies the
model; this one holds the model fixed (Opus 5) and varies the PROMPT. Everything
expensive and shared upstream — macro, micro, research dossier, literary echoes,
synthesis discovery — is computed once by a normal pipeline run and re-read here, so
the only variable between arms is the prompt text.

Arms are defined in scripts/writer_prompt_variants.py.

Usage:
    python scripts/ab_writer_prompts.py 71 --arms A_no_scaffolding
    python scripts/ab_writer_prompts.py 71 --arms base A_no_scaffolding C_conciseness --beta-read
    python scripts/ab_writer_prompts.py 71 --arms A_no_scaffolding --dry-run

Outputs (production files are never touched):
    output/psalm_<N>/_prompt_ab/<arm>/psalm_<NNN>_edited_intro.md
    output/psalm_<N>/_prompt_ab/<arm>/psalm_<NNN>_edited_verses.md
    output/psalm_<N>/_prompt_ab/<arm>/psalm_<NNN>_full.md         (beta-reader input)
    output/psalm_<N>/_prompt_ab/<arm>/_prompt_template.txt        (audit trail)
    output/psalm_<N>/_prompt_ab/ab_summary.{json,md}

Finish an arm through copy edit + DOCX with:
    python scripts/ab_finish_arms.py 71 --ab-dir _prompt_ab --arms <arm> \\
        --writer-model claude-opus-5

Cost: ~$2.1 per arm (the writer call carries ~205K input tokens), +$0.08 with
--beta-read. Session 370's $0.6-1 estimate was wrong.
"""

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from src.agents import master_editor as me_module
from src.agents.master_editor import MasterEditor
from src.utils.cost_tracker import CostTracker
from src.utils.logger import get_logger
from src.utils.model_effort import effort_for
from scripts.writer_prompt_variants import VARIANTS, LABELS

DEFAULT_MODEL = "claude-opus-5"

# Captured at import, before any arm can patch the module constant.
PRISTINE_PROMPT = me_module.MASTER_WRITER_PROMPT_V4


def _upstream_files(psalm: int) -> dict:
    out = ROOT / "output" / f"psalm_{psalm}"
    return {
        "macro_file": out / f"psalm_{psalm:03d}_macro.json",
        "micro_file": out / f"psalm_{psalm:03d}_micro_v2.json",
        "research_file": out / f"psalm_{psalm:03d}_research_v2.md",
        "synthesis_discovery_file": out / f"psalm_{psalm:03d}_synthesis_discovery.md",
    }


def _model_usage(tracker: CostTracker, model: str) -> dict:
    usage = getattr(tracker, "usage_by_model", None) or {}
    row = usage.get(model)
    if row is None:
        return {"input_tokens": None, "output_tokens": None, "call_count": None}
    return {
        "input_tokens": getattr(row, "input_tokens", None),
        "output_tokens": getattr(row, "output_tokens", None),
        "call_count": getattr(row, "call_count", None),
    }


def build_prompt(arm: str) -> str:
    """Apply the arm's transform to the pristine prompt.

    Reads the ORIGINAL module constant every time rather than whatever is currently
    patched in, so arms can never compound if several run in one process.
    """
    return VARIANTS[arm](PRISTINE_PROMPT)


def run_arm(psalm: int, arm: str, model: str, files: dict, ab_dir: Path, logger) -> dict:
    arm_dir = ab_dir / arm
    arm_dir.mkdir(parents=True, exist_ok=True)

    prompt_template = build_prompt(arm)
    (arm_dir / "_prompt_template.txt").write_text(prompt_template, encoding="utf-8")

    tracker = CostTracker()
    editor = MasterEditor(main_model=model, cost_tracker=tracker)

    delta = len(prompt_template) - len(PRISTINE_PROMPT)
    logger.info(
        f"[prompt-ab] psalm={psalm} arm={arm} model={model} effort={effort_for(model)} "
        f"template={len(prompt_template):,} chars ({delta:+,} vs base)"
    )

    # The writer reads the module-level constant directly, so patch it for the call
    # and restore in `finally` — a leaked patch would silently contaminate later arms.
    original = me_module.MASTER_WRITER_PROMPT_V4
    me_module.MASTER_WRITER_PROMPT_V4 = prompt_template
    t0 = time.time()
    try:
        result = editor.write_commentary(
            psalm_number=psalm,
            insights_file=None,
            reader_questions_file=None,
            suppress_questions=False,
            **files,
        )
    finally:
        me_module.MASTER_WRITER_PROMPT_V4 = original
    elapsed = time.time() - t0

    intro = result.get("introduction", "") or ""
    verses = result.get("verse_commentary", "") or ""

    (arm_dir / f"psalm_{psalm:03d}_edited_intro.md").write_text(intro, encoding="utf-8")
    (arm_dir / f"psalm_{psalm:03d}_edited_verses.md").write_text(verses, encoding="utf-8")
    full = (
        f"# Commentary on Psalm {psalm}\n\n---\n\n## Introduction\n\n{intro}\n\n"
        f"---\n\n## Verse-by-Verse Commentary\n\n{verses}\n"
    )
    full_path = arm_dir / f"psalm_{psalm:03d}_full.md"
    full_path.write_text(full, encoding="utf-8")

    metrics = {
        "arm": arm,
        "label": LABELS.get(arm, arm),
        "model": model,
        "effort": effort_for(model),
        "prompt_chars": len(prompt_template),
        "prompt_delta_chars": delta,
        "elapsed_s": round(elapsed, 1),
        "cost_usd": round(tracker.get_total_cost(), 4),
        "intro_words": len(intro.split()),
        "verse_words": len(verses.split()),
        "total_words": len(intro.split()) + len(verses.split()),
        "full_file": str(full_path.relative_to(ROOT)),
        **_model_usage(tracker, model),
    }
    logger.info(
        f"[prompt-ab] {arm}: ${metrics['cost_usd']:.4f} "
        f"{metrics['total_words']} words {metrics['elapsed_s']}s"
    )
    return metrics


def run_beta_reads(psalm: int, arms: list, ab_dir: Path, logger) -> None:
    """Beta-read each arm. Per Session 370 the numeric scores do not discriminate;
    the trustworthy signals are the prose plus the 5b/5c counters
    (INERT CITATIONS / UNEXPLAINED GRAMMAR) and LANDING."""
    from src.agents.beta_reader import BetaReader

    for a in arms:
        if a.get("error"):
            continue
        tracker = CostTracker()
        reader = BetaReader(cost_tracker=tracker, logger=logger)
        try:
            res = reader.read_commentary(
                psalm_number=psalm,
                input_file=ROOT / a["full_file"],
                output_dir=ab_dir / a["arm"],
            )
            a["beta_scores"] = res.get("scores") or {}
            a["beta_report"] = str(Path(res["report_file"]).relative_to(ROOT))
            a["beta_cost_usd"] = round(tracker.get_total_cost(), 4)
            logger.info(f"[prompt-ab] beta read {a['arm']}: {a['beta_scores']}")
        except Exception as e:
            logger.error(f"[prompt-ab] beta read failed for {a['arm']}: {e}")
            a["beta_error"] = str(e)


def write_summary(psalm: int, arms: list, ab_dir: Path) -> Path:
    """Merge into any existing summary so arms run in separate invocations accumulate
    instead of clobbering each other."""
    path_json = ab_dir / "ab_summary.json"
    existing = {}
    if path_json.exists():
        try:
            for a in json.loads(path_json.read_text(encoding="utf-8")).get("arms", []):
                existing[a.get("arm")] = a
        except Exception:
            pass
    for a in arms:
        existing[a["arm"]] = a
    merged = list(existing.values())

    path_json.write_text(
        json.dumps({"psalm": psalm, "arms": merged}, indent=2), encoding="utf-8"
    )

    ok = [a for a in merged if not a.get("error")]
    lines = [
        f"# Writer PROMPT A/B/C — Psalm {psalm}",
        "",
        "Model is fixed; only the prompt differs between arms. All upstream artifacts",
        "(macro, micro, dossier, synthesis discovery) are shared.",
        "",
        "| arm | prompt Δchars | cost | in tok | out tok | words | intro w | verses w | secs |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for a in ok:
        lines.append(
            f"| {a['label']} | {a['prompt_delta_chars']:+,} | ${a['cost_usd']:.4f} | "
            f"{a['input_tokens']} | {a['output_tokens']} | {a['total_words']:,} | "
            f"{a['intro_words']:,} | {a['verse_words']:,} | {a['elapsed_s']} |"
        )

    base = next((a for a in ok if a["arm"] == "base"), None)
    if base:
        lines += ["", "**vs baseline:**", ""]
        for a in ok:
            if a["arm"] == "base":
                continue
            lines.append(
                f"- {a['label']}: words {a['total_words'] / base['total_words']:.2f}x "
                f"({a['total_words'] - base['total_words']:+,}), "
                f"output tokens {(a['output_tokens'] or 0) / (base['output_tokens'] or 1):.2f}x, "
                f"cost ${a['cost_usd'] - base['cost_usd']:+.2f}"
            )

    for a in ok:
        if a.get("beta_scores"):
            lines += ["", f"Beta read — {a['label']}: {a['beta_scores']} "
                          f"(scores do NOT discriminate between arms; the counters and "
                          f"prose at `{a.get('beta_report')}` are the readout)"]

    for a in merged:
        if a.get("error"):
            lines += ["", f"**{a.get('label', a.get('arm'))} FAILED**: {a['error']}"]

    path = ab_dir / "ab_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(
        description="Writer-prompt A/B/C on shared upstream artifacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("psalm", type=int, help="Psalm number (needs a completed pipeline run)")
    ap.add_argument("--arms", nargs="+", required=True,
                    help=f"Arms to run. Available: {', '.join(VARIANTS)}")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--beta-read", action="store_true",
                    help="Also run the beta reader on each arm (~$0.08 each)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Build and diff each arm's prompt, spend nothing")
    args = ap.parse_args()

    unknown = [a for a in args.arms if a not in VARIANTS]
    if unknown:
        print(f"ERROR: unknown arm(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"       available: {', '.join(VARIANTS)}", file=sys.stderr)
        return 1

    logger = get_logger("ab_writer_prompts")
    psalm = args.psalm

    files = _upstream_files(psalm)
    missing = [str(p.relative_to(ROOT)) for p in files.values() if not p.exists()]
    if missing:
        print(f"ERROR: Psalm {psalm} is missing upstream artifacts:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        return 1

    # Build every arm BEFORE spending anything, so a stale anchor fails for free.
    built = {}
    for arm in args.arms:
        try:
            built[arm] = build_prompt(arm)
        except ValueError as e:
            print(f"ERROR building arm {arm}:\n  {e}", file=sys.stderr)
            return 1

    print(f"\nWriter PROMPT A/B/C — Psalm {psalm}  (model: {args.model})")
    print(f"  shared upstream: {files['research_file'].name} "
          f"({files['research_file'].stat().st_size:,} bytes)")
    print(f"  base prompt: {len(PRISTINE_PROMPT):,} chars")
    for arm, tmpl in built.items():
        d = len(tmpl) - len(PRISTINE_PROMPT)
        print(f"  {arm:<22} {len(tmpl):>7,} chars  ({d:+,})")
    print()

    if args.dry_run:
        print("--dry-run: nothing spent.")
        return 0

    ab_dir = ROOT / "output" / f"psalm_{psalm}" / "_prompt_ab"
    ab_dir.mkdir(parents=True, exist_ok=True)

    arms = []
    for arm in args.arms:
        try:
            arms.append(run_arm(psalm, arm, args.model, files, ab_dir, logger))
        except Exception as e:
            # One arm failing must not discard another arm's paid output.
            logger.error(f"[prompt-ab] arm {arm} failed: {e}")
            traceback.print_exc()
            arms.append({"arm": arm, "label": LABELS.get(arm, arm), "error": str(e)})

    if args.beta_read:
        run_beta_reads(psalm, arms, ab_dir, logger)

    summary = write_summary(psalm, arms, ab_dir)
    print("\n" + summary.read_text(encoding="utf-8"))
    print(f"-> {summary.relative_to(ROOT)}")
    return 0 if any(not a.get("error") for a in arms) else 1


if __name__ == "__main__":
    sys.exit(main())
