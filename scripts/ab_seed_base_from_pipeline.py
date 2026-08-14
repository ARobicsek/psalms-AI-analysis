"""Seed a writer-prompt A/B's `base` arm from a completed pipeline run (Session 378).

WHY THIS EXISTS
---------------
`ab_writer_prompts.py` runs every arm itself, so a two-arm A/B pays for the writer
twice (~$2/arm on Opus 5). But a normal `run_enhanced_pipeline.py <N>` has ALREADY
run the production prompt over the same dossier — that IS the base arm. This script
recovers it from the response the pipeline already saved and drops it into the arm
layout `ab_finish_arms.py` expects, so you only pay for the arms that actually vary.

Session 378 measured the saving at $1.95 on Psalm 27 — about 20% of a two-arm A/B,
and it grows with nothing (the base arm is free no matter how many arms you add).

WHEN IT IS VALID
----------------
Only when the pipeline fed the writer exactly what the harness would. Both pass
`insights_file=None` unconditionally, and both pass the synthesis-discovery file when
it exists, so the single divergence is reader questions: the pipeline passes
`psalm_NNN_reader_questions.json` when present, the harness always passes None. This
script REFUSES to seed when that file exists, rather than producing an arm that
differs from its comparators by a second variable. That is the whole failure mode
this project keeps rediscovering — a comparison with two variables in it.

It also refuses when the saved writer response is older than the dossier, which means
the response came from a different dossier than the one the other arms will read.

NOTE ON CACHING (the other cost lever, NOT implemented)
-------------------------------------------------------
Prompt caching does not pay at two arms: the arms share a ~95% prefix, but a writer
call runs ~10-12 minutes against a 5-minute default TTL, and the 1-hour TTL costs 2x
on write, so 2.0x + 0.1x LOSES to 2.0x uncached. It turns profitable from three arms
up. See docs/plans/NEXT_SESSION_PROMPT_session_378.md.

Usage:
    python scripts/run_enhanced_pipeline.py 27
    python scripts/ab_seed_base_from_pipeline.py 27
    python scripts/ab_writer_prompts.py 27 --arms F_no_framework
    python scripts/ab_finish_arms.py 27 --ab-dir _prompt_ab \\
        --arms base F_no_framework --writer-model claude-opus-5 --copy-to-documents
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.agents.master_editor import MasterEditor, MASTER_WRITER_PROMPT_V4
from src.utils.logger import get_logger


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("psalm", type=int)
    ap.add_argument("--ab-dir", default="_prompt_ab",
                    help="Subdirectory of output/psalm_<N>/ holding the arms")
    ap.add_argument("--arm", default="base", help="Arm directory name to write")
    ap.add_argument("--response", default=None,
                    help="Writer response file (default: the pipeline's saved debug copy)")
    ap.add_argument("--force", action="store_true",
                    help="Seed even if the validity checks fail. You are asserting the "
                         "pipeline fed the writer what the harness would.")
    args = ap.parse_args()

    pn = args.psalm
    logger = get_logger("ab_seed_base")
    out = ROOT / "output" / f"psalm_{pn}"
    response_file = Path(args.response) if args.response else (
        ROOT / "output" / "debug" / f"master_writer_v4_response_psalm_{pn}.txt"
    )

    if not response_file.exists():
        print(f"ERROR: no saved writer response at {response_file}", file=sys.stderr)
        return 1

    problems = []
    resp_mtime = response_file.stat().st_mtime

    # Divergence 1: reader questions. See module docstring.
    rq = out / f"psalm_{pn:03d}_reader_questions.json"
    if rq.exists():
        problems.append(
            f"{rq.name} exists — the pipeline passed it to the writer but "
            "ab_writer_prompts.py passes reader_questions_file=None, so this arm would "
            "differ from the others by reader questions AS WELL AS the prompt delta."
        )

    # Divergence 2: THE DEBUG RESPONSE FILE IS A SINGLE SLOT, overwritten by every
    # writer call including each A/B arm. Seed BEFORE running any arm. Caught in
    # this script's own self-test, where seeding after arm F had run silently filled
    # `base` with arm F's text — an A/B whose two arms are the same arm, which is the
    # exact failure this file exists to prevent elsewhere.
    ab_root = out / args.ab_dir
    if ab_root.exists():
        for d in sorted(ab_root.iterdir()):
            if not d.is_dir() or d.name == args.arm:
                continue
            other = d / f"psalm_{pn:03d}_edited_verses.md"
            if other.exists() and other.stat().st_mtime >= resp_mtime:
                problems.append(
                    f"arm '{d.name}' already has writer output at least as new as the "
                    f"saved response — {response_file.name} is a single slot overwritten "
                    f"by every writer call, so it probably holds '{d.name}' output, not "
                    "the pipeline's. Seed before running any arm."
                )

    # Divergence 3: a response older than the dossier is a response to a different
    # dossier. Compare against the files the writer actually reads.
    for name in (f"psalm_{pn:03d}_research_v2.md", f"psalm_{pn:03d}_macro.json",
                 f"psalm_{pn:03d}_micro_v2.json", f"psalm_{pn:03d}_synthesis_discovery.md"):
        f = out / name
        if f.exists() and f.stat().st_mtime > resp_mtime:
            problems.append(
                f"{name} is NEWER than the saved response — the response was written "
                "against a different dossier than the other arms will read."
            )

    if problems:
        print("REFUSING to seed — the recovered arm would not be comparable:\n",
              file=sys.stderr)
        for p in problems:
            print(f"  - {p}\n", file=sys.stderr)
        if not args.force:
            print("Re-run the base arm through ab_writer_prompts.py instead, or pass "
                  "--force if you are certain.", file=sys.stderr)
            return 1
        print("--force given; seeding anyway.\n", file=sys.stderr)

    text = response_file.read_text(encoding="utf-8")
    editor = MasterEditor.__new__(MasterEditor)
    editor.logger = logger
    parsed = editor._parse_writer_response(text, pn)

    intro, verses = parsed["introduction"], parsed["verse_commentary"]
    if not intro or not verses:
        print(f"ERROR: the response parsed to an empty section "
              f"(intro {len(intro):,} chars, verses {len(verses):,} chars). "
              f"Inspect {response_file}.", file=sys.stderr)
        return 1

    arm_dir = out / args.ab_dir / args.arm
    arm_dir.mkdir(parents=True, exist_ok=True)
    (arm_dir / f"psalm_{pn:03d}_edited_intro.md").write_text(intro, encoding="utf-8")
    (arm_dir / f"psalm_{pn:03d}_edited_verses.md").write_text(verses, encoding="utf-8")
    (arm_dir / "_prompt_template.txt").write_text(MASTER_WRITER_PROMPT_V4, encoding="utf-8")
    (arm_dir / f"psalm_{pn:03d}_full.md").write_text(
        f"# Commentary on Psalm {pn}\n\n---\n\n## Introduction\n\n{intro}\n\n"
        f"---\n\n## Verse-by-Verse Commentary\n\n{verses}\n",
        encoding="utf-8",
    )

    print(f"Seeded arm '{args.arm}' for Psalm {pn} from {response_file.name} "
          f"(no API call, ~$2 saved):")
    for p in sorted(arm_dir.iterdir()):
        print(f"  {p.name:<34} {p.stat().st_size:>9,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
