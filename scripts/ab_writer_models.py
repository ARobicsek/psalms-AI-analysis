"""
Writer-only model A/B (Session 367).

Runs ONLY the Master Writer stage twice — once per model — against a single set
of already-computed upstream artifacts. Everything expensive and shared (macro,
micro, research dossier, literary echoes, synthesis discovery) is computed once
by a normal pipeline run and simply re-read here, so the ONLY variable between
the two arms is the writer's model.

Motivating question (Session 367): Claude Opus 5 carries the same sticker price
as Opus 4.8 ($5/$25) but measured ~2.2x the output tokens on a real pipeline
prompt, because Anthropic folds thinking into billed output. So it is a quality
purchase at roughly +$1.5/run, not a free swap. This harness measures both
halves of that trade on a real psalm.

Prerequisite: a completed pipeline run for the psalm, i.e. these must exist:
    output/psalm_<N>/psalm_<NNN>_macro.json
    output/psalm_<N>/psalm_<NNN>_micro_v2.json
    output/psalm_<N>/psalm_<NNN>_research_v2.md
    output/psalm_<N>/psalm_<NNN>_synthesis_discovery.md

Usage:
    python scripts/ab_writer_models.py 70
    python scripts/ab_writer_models.py 70 --beta-read
    python scripts/ab_writer_models.py 70 --models claude-opus-4-8 claude-opus-5

Outputs (production files are never touched):
    output/psalm_<N>/_writer_ab/<model>/psalm_<NNN>_edited_intro.md
    output/psalm_<N>/_writer_ab/<model>/psalm_<NNN>_edited_verses.md
    output/psalm_<N>/_writer_ab/<model>/psalm_<NNN>_full.md   (beta-reader input)
    output/psalm_<N>/_writer_ab/ab_summary.json
    output/psalm_<N>/_writer_ab/ab_summary.md
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

from src.agents.master_editor import MasterEditor
from src.utils.cost_tracker import CostTracker
from src.utils.logger import get_logger
from src.utils.model_effort import effort_for

DEFAULT_MODELS = ["claude-opus-4-8", "claude-opus-5"]


def _upstream_files(psalm: int) -> dict:
    out = ROOT / "output" / f"psalm_{psalm}"
    return {
        "macro_file": out / f"psalm_{psalm:03d}_macro.json",
        "micro_file": out / f"psalm_{psalm:03d}_micro_v2.json",
        "research_file": out / f"psalm_{psalm:03d}_research_v2.md",
        "synthesis_discovery_file": out / f"psalm_{psalm:03d}_synthesis_discovery.md",
    }


def _model_usage(tracker: CostTracker, model: str) -> dict:
    """Pull the per-model usage row out of a tracker holding exactly one arm."""
    usage = getattr(tracker, "usage_by_model", None) or {}
    row = usage.get(model)
    if row is None:
        return {"input_tokens": None, "output_tokens": None, "call_count": None}
    return {
        "input_tokens": getattr(row, "input_tokens", None),
        "output_tokens": getattr(row, "output_tokens", None),
        "call_count": getattr(row, "call_count", None),
    }


def run_arm(psalm: int, model: str, files: dict, ab_dir: Path, logger) -> dict:
    """Run the writer once with `model`; return a metrics dict."""
    arm_dir = ab_dir / model
    arm_dir.mkdir(parents=True, exist_ok=True)

    tracker = CostTracker()
    editor = MasterEditor(main_model=model, cost_tracker=tracker)

    logger.info(f"[ab] psalm={psalm} model={model} effort={effort_for(model)}")
    t0 = time.time()
    result = editor.write_commentary(
        psalm_number=psalm,
        insights_file=None,
        reader_questions_file=None,
        suppress_questions=False,
        **files,
    )
    elapsed = time.time() - t0

    intro = result.get("introduction", "") or ""
    verses = result.get("verse_commentary", "") or ""

    (arm_dir / f"psalm_{psalm:03d}_edited_intro.md").write_text(intro, encoding="utf-8")
    (arm_dir / f"psalm_{psalm:03d}_edited_verses.md").write_text(verses, encoding="utf-8")
    # Composite in the shape BetaReader expects from a finished guide.
    full = (
        f"# Commentary on Psalm {psalm}\n\n---\n\n## Introduction\n\n{intro}\n\n"
        f"---\n\n## Verse-by-Verse Commentary\n\n{verses}\n"
    )
    full_path = arm_dir / f"psalm_{psalm:03d}_full.md"
    full_path.write_text(full, encoding="utf-8")

    metrics = {
        "model": model,
        "effort": effort_for(model),
        "elapsed_s": round(elapsed, 1),
        "cost_usd": round(tracker.get_total_cost(), 4),
        "intro_words": len(intro.split()),
        "verse_words": len(verses.split()),
        "total_words": len(intro.split()) + len(verses.split()),
        "intro_chars": len(intro),
        "verse_chars": len(verses),
        "full_file": str(full_path.relative_to(ROOT)),
        **_model_usage(tracker, model),
    }
    logger.info(
        f"[ab] {model}: ${metrics['cost_usd']:.4f} "
        f"{metrics['total_words']} words {metrics['elapsed_s']}s"
    )
    return metrics


def run_beta_reads(psalm: int, arms: list, ab_dir: Path, logger) -> None:
    """Beta-read each arm. Per Session 364 the PROSE is the readout; the numeric
    scores are known not to discriminate between arms, so they are recorded but
    should not be used to pick a winner."""
    from src.agents.beta_reader import BetaReader

    for arm in arms:
        if arm.get("error"):
            continue
        model = arm["model"]
        tracker = CostTracker()
        reader = BetaReader(cost_tracker=tracker, logger=logger)
        try:
            res = reader.read_commentary(
                psalm_number=psalm,
                input_file=ROOT / arm["full_file"],
                output_dir=ab_dir / model,
            )
            arm["beta_scores"] = res.get("scores") or {}
            arm["beta_report"] = str(Path(res["report_file"]).relative_to(ROOT))
            arm["beta_cost_usd"] = round(tracker.get_total_cost(), 4)
            logger.info(f"[ab] beta read {model}: {arm['beta_scores']}")
        except Exception as e:
            logger.error(f"[ab] beta read failed for {model}: {e}")
            arm["beta_error"] = str(e)


def write_summary(psalm: int, arms: list, ab_dir: Path) -> Path:
    (ab_dir / "ab_summary.json").write_text(
        json.dumps({"psalm": psalm, "arms": arms}, indent=2), encoding="utf-8"
    )

    ok = [a for a in arms if not a.get("error")]
    lines = [
        f"# Writer model A/B — Psalm {psalm}",
        "",
        "Only the Master Writer stage differs between arms; all upstream",
        "artifacts (macro, micro, dossier, synthesis discovery) are shared.",
        "",
        "| model | effort | cost | in tok | out tok | words | intro w | verses w | secs |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for a in ok:
        lines.append(
            f"| {a['model']} | {a['effort']} | ${a['cost_usd']:.4f} | "
            f"{a['input_tokens']} | {a['output_tokens']} | {a['total_words']} | "
            f"{a['intro_words']} | {a['verse_words']} | {a['elapsed_s']} |"
        )

    if len(ok) == 2:
        a, b = ok
        def ratio(x, y):
            return f"{y / x:.2f}x" if x else "n/a"
        lines += [
            "",
            f"**{b['model']} vs {a['model']}**: "
            f"cost {ratio(a['cost_usd'], b['cost_usd'])}, "
            f"output tokens {ratio(a['output_tokens'] or 0, b['output_tokens'] or 0)}, "
            f"words {ratio(a['total_words'], b['total_words'])}, "
            f"wall time {ratio(a['elapsed_s'], b['elapsed_s'])}.",
            "",
            f"Per-run projection: the writer is 1 of 3 Opus calls, so a full-run "
            f"delta will exceed this stage's "
            f"${b['cost_usd'] - a['cost_usd']:+.2f} if macro and synthesis "
            f"discovery move to the same model.",
        ]

    for a in ok:
        if a.get("beta_scores"):
            lines += ["", f"Beta read — {a['model']}: {a['beta_scores']} "
                          f"(scores do NOT discriminate between arms; read the prose "
                          f"at `{a.get('beta_report')}`)"]

    failed = [a for a in arms if a.get("error")]
    for a in failed:
        lines += ["", f"**{a['model']} FAILED**: {a['error']}"]

    path = ab_dir / "ab_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> int:
    # Ensure UTF-8 for Hebrew / em-dashes on Windows (cp1252 stdout otherwise
    # raises UnicodeEncodeError when the summary is echoed — same failure the
    # Session 364/365 CLI fixes addressed).
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(
        description="Writer-only model A/B on shared upstream artifacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("psalm", type=int, help="Psalm number (needs a completed pipeline run)")
    ap.add_argument("--models", nargs="+", default=DEFAULT_MODELS,
                    help=f"Models to compare (default: {' '.join(DEFAULT_MODELS)})")
    ap.add_argument("--beta-read", action="store_true",
                    help="Also run the beta reader on each arm (~$0.08 each)")
    args = ap.parse_args()

    logger = get_logger("ab_writer_models")
    psalm = args.psalm

    files = _upstream_files(psalm)
    missing = [str(p.relative_to(ROOT)) for p in files.values() if not p.exists()]
    if missing:
        print(f"ERROR: Psalm {psalm} is missing upstream artifacts:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        print("\nRun the full pipeline first:", file=sys.stderr)
        print(f"  python scripts/run_enhanced_pipeline.py {psalm}", file=sys.stderr)
        return 1

    ab_dir = ROOT / "output" / f"psalm_{psalm}" / "_writer_ab"
    ab_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nWriter A/B — Psalm {psalm}")
    print(f"  shared upstream: {files['research_file'].name} "
          f"({files['research_file'].stat().st_size:,} bytes)")
    print(f"  arms: {', '.join(args.models)}\n")

    arms = []
    for model in args.models:
        try:
            arms.append(run_arm(psalm, model, files, ab_dir, logger))
        except Exception as e:
            # One arm failing must not discard the other arm's paid output.
            logger.error(f"[ab] arm {model} failed: {e}")
            traceback.print_exc()
            arms.append({"model": model, "error": str(e)})

    if args.beta_read:
        run_beta_reads(psalm, arms, ab_dir, logger)

    summary = write_summary(psalm, arms, ab_dir)
    print("\n" + summary.read_text(encoding="utf-8"))
    print(f"-> {summary.relative_to(ROOT)}")
    return 0 if any(not a.get("error") for a in arms) else 1


if __name__ == "__main__":
    sys.exit(main())
