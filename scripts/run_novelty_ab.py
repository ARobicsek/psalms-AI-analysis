#!/usr/bin/env python3
"""Session-358 novelty A/B runner — re-run psalms through the R1-R6 pipeline.

Runs the UNCHANGED production harness (`scripts/run_enhanced_pipeline.py`, same
defaults, same steps) for each psalm, but:

  1. Writes into an isolated arm directory (default `output/ab_novelty/psalm_N`)
     so existing production outputs are never touched.
  2. Copies the baseline run's macro JSON into the arm dir and passes
     `--skip-macro`, holding the macro analysis CONSTANT across arms (the R
     changes alter how macro output is *consumed* — R5/R6 — not how it is
     produced, so a fresh macro would only add run-to-run noise and ~$0.36).
     Use `--fresh-macro` to override.
  3. Passes `--skip-lit-echoes`, so both arms read the SAME existing
     `data/literary_echoes/psalm_NNN_literary_echoes.txt` (R1-R6 do not touch
     the echoes pipeline; regenerating would overwrite the shared file AND
     introduce uncontrolled variation). Use `--with-lit-echoes` to override —
     WARNING: that overwrites the shared echoes file.

Everything else — micro, research assembly, synthesis-discovery sidecar,
master writer, scripture verifier, copy editor, DOCX — runs exactly as the
production pipeline runs it today, on THIS branch's code (R1-R6).

This script must be run from the branch carrying the R1-R6 changes
(`claude/sweet-fermat-pje3t7`); it warns if the current branch looks wrong.

Usage (local machine, with API keys):
    python scripts/run_novelty_ab.py 58 59 60
    python scripts/run_novelty_ab.py 58 --dry-run        # print commands only
    python scripts/run_novelty_ab.py 58 --delay 60

Then evaluate (tool lives on main and on this branch):
    python scripts/evaluate_novelty_ab.py 58 59 60

Approx cost per psalm: ~$5.5-6 (micro+research ~$1-1.5, sidecar ~$2,
writer ~$3.2, copy editor ~$0.5; macro and echoes skipped).
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "claude/sweet-fermat-pje3t7"
OUT_ROOT_DEFAULT = "output/ab_novelty"
BASELINE_DIR_TEMPLATE = "output/psalm_{n}"
ECHOES_FILE_TEMPLATE = "data/literary_echoes/psalm_{n:03d}_literary_echoes.txt"


def current_branch() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=PROJECT_ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        return "(unknown)"


def main() -> int:
    ap = argparse.ArgumentParser(description="Run psalms through the R1-R6 pipeline into an isolated A/B arm dir.")
    ap.add_argument("psalms", nargs="+", type=int)
    ap.add_argument("--out-root", default=OUT_ROOT_DEFAULT,
                    help=f"Root for arm output dirs (default: {OUT_ROOT_DEFAULT})")
    ap.add_argument("--baseline-dir", default=BASELINE_DIR_TEMPLATE,
                    help="Baseline output dir template for the macro copy "
                         f"(default: {BASELINE_DIR_TEMPLATE})")
    ap.add_argument("--fresh-macro", action="store_true",
                    help="Run macro fresh instead of copying the baseline macro JSON")
    ap.add_argument("--with-lit-echoes", action="store_true",
                    help="Regenerate literary echoes (WARNING: overwrites the shared "
                         "data/literary_echoes file and adds ~$0.95 + variance)")
    ap.add_argument("--delay", type=int, default=None,
                    help="Pass through to run_enhanced_pipeline.py --delay")
    ap.add_argument("--allow-any-branch", action="store_true",
                    help="Skip the branch check (NOT recommended)")
    ap.add_argument("--dry-run", action="store_true", help="Print commands without running")
    args = ap.parse_args()

    branch = current_branch()
    if branch != EXPECTED_BRANCH and not args.allow_any_branch:
        print(f"FATAL: current branch is '{branch}', expected '{EXPECTED_BRANCH}'.")
        print("The point of this run is to exercise the R1-R6 changes on that branch.")
        print("Checkout the branch, or pass --allow-any-branch if you know what you're doing.")
        return 2

    failures = []
    for n in args.psalms:
        print(f"\n{'='*80}\nNOVELTY A/B — Psalm {n} (branch: {branch})\n{'='*80}")
        arm_dir = PROJECT_ROOT / args.out_root / f"psalm_{n}"
        arm_dir.mkdir(parents=True, exist_ok=True)
        baseline_dir = PROJECT_ROOT / args.baseline_dir.format(n=n)

        # Preflight: warn about anything that weakens the comparison.
        baseline_ce = baseline_dir / f"psalm_{n:03d}_copy_edited.md"
        docx = PROJECT_ROOT / "Documents" / "Psalm study guide" / f"Psalm {n}.docx"
        if not baseline_ce.exists() and not docx.exists():
            print(f"  [warn] no baseline found ({baseline_ce} / published DOCX) — "
                  "the eval tool will have nothing to compare against")
        echoes_file = PROJECT_ROOT / ECHOES_FILE_TEMPLATE.format(n=n)
        if not args.with_lit_echoes and not echoes_file.exists():
            print(f"  [warn] {echoes_file} missing — the new arm's bundle will have "
                  "no literary echoes while the baseline did. Consider --with-lit-echoes "
                  "(accepts the overwrite + variance) or restore the file first.")

        # Hold macro constant by copying the baseline macro JSON.
        skip_macro = False
        if not args.fresh_macro:
            src_macro = baseline_dir / f"psalm_{n:03d}_macro.json"
            dst_macro = arm_dir / f"psalm_{n:03d}_macro.json"
            if src_macro.exists():
                if not args.dry_run:
                    shutil.copy2(src_macro, dst_macro)
                skip_macro = True
                print(f"  macro held constant: copied {src_macro.name} from baseline")
            else:
                print(f"  [warn] {src_macro} not found — macro will run fresh "
                      "(adds ~$0.36 and arm-to-arm macro variance)")

        cmd = [sys.executable, "scripts/run_enhanced_pipeline.py", str(n),
               "--output-dir", str(arm_dir)]
        if skip_macro:
            cmd.append("--skip-macro")
        if not args.with_lit_echoes:
            cmd.append("--skip-lit-echoes")
        if args.delay is not None:
            cmd += ["--delay", str(args.delay)]

        print(f"  $ {' '.join(cmd)}")
        if args.dry_run:
            continue
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        if result.returncode != 0:
            print(f"  [FAIL] Psalm {n} pipeline exited {result.returncode}")
            failures.append(n)
        else:
            print(f"  [OK] Psalm {n} complete -> {arm_dir}")

    print(f"\n{'='*80}")
    if failures:
        print(f"FAILED psalms: {failures}")
    done = [n for n in args.psalms if n not in failures]
    if done and not args.dry_run:
        print("Next step — blind evaluation vs. the baseline:")
        print(f"  python scripts/evaluate_novelty_ab.py {' '.join(str(n) for n in done)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
