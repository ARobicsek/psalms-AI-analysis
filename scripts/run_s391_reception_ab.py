"""Session 391: does the writer do better with the rabbinic reception and the Targum? A paired A/B.

The author's design: both arms on TODAY's research bundle (concordance fixes, the shared-vocabulary
radar, Brenton's Greek, the hardened commentary fetch) and the SAME fresh echoes v3 dossier; they
differ ONLY in what Sefaria now adds.

    Arm A: macro reused -> echoes v3 -> micro + research bundle -> synthesis discovery -> writer
           -> print-ready -> copy editor -> DOCX/PDF                         (the production pipeline)
    Arm B: A's macro, micro and research bundle (with A's echoes) + the reception section + a
           Targum line per verse -> synthesis discovery -> writer -> print-ready -> copy editor -> DOCX/PDF

Each arm is a plain `scripts/run_enhanced_pipeline.py` subprocess, so every option is resolved
exactly as in production; arm B adds `--skip-macro --skip-micro --skip-lit-echoes --reception
--targum`. Isolation: each arm writes into its own folder (`--output-dir`) and its own
PSALMS_OUTPUT_ROOT (the writer's thinking, saved essay and telemetry; without it, it overwrites the
production psalm's). The two shared files the pipeline writes outside both, the canonical echoes
dossier (data/literary_echoes/psalm_NNN_literary_echoes.txt) and the flat output/debug/*_psalm_N.txt
dumps, are backed up first, copied into each arm after it runs, and restored at the end.

    python scripts/run_s391_reception_ab.py 76 --dry-run      # $0: builds the reception section and Targum, prints the plan
    python scripts/run_s391_reception_ab.py 76                # both arms (~$10-11 for Ps 76)
    python scripts/run_s391_reception_ab.py 76 --arms B       # only B (needs A's files); --redo to re-run a finished arm

Results: output/_s391_reception_ab/psalm_N/ (README.md with costs and files; both DOCX/PDF at the top).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
os.chdir(REPO)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from src.utils.debug_paths import psalm_output_dir  # noqa: E402  (the PRODUCTION folder: no env override here)

TRIM_CEILING = 350000   # MasterEditor / synthesis discovery: trim_bundle(max_chars=350000)
EST = {"micro": (1.0, 2.0), "echoes": (1.0, 1.4), "sd_writer": (3.3, 4.3), "copy_edit": (0.4, 0.6)}


def files(psalm: int, out: Path) -> dict:
    s = f"psalm_{psalm:03d}"
    return {"macro": out / f"{s}_macro.json", "micro": out / f"{s}_micro_v2.json",
            "research": out / f"{s}_research_v2.md", "cost": out / f"{s}_cost.json",
            "docx": out / f"{s}_commentary.docx", "pdf": out / f"{s}_commentary.pdf"}


def debug_dumps(psalm: int):
    d = REPO / "output" / "debug"
    return sorted(d.glob(f"*_psalm_{psalm}.txt")) if d.is_dir() else []


def run_arm(name: str, psalm: int, root: Path, extra: list, delay: int, skip_copy_edit: bool) -> int:
    out = root / f"psalm_{psalm}"
    cmd = [sys.executable, "scripts/run_enhanced_pipeline.py", str(psalm), "--output-dir", str(out),
           "--skip-macro", "--delay", str(delay)] + extra + (["--skip-copy-editor"] if skip_copy_edit else [])
    env = {**os.environ, "PSALMS_OUTPUT_ROOT": str(root)}
    print(f"\n{'=' * 80}\nARM {name}: {' '.join(cmd)}\n  PSALMS_OUTPUT_ROOT={root}\n{'=' * 80}", flush=True)
    t0 = time.time()
    code = subprocess.call(cmd, env=env)
    print(f"ARM {name} finished with exit code {code} after {(time.time() - t0) / 60:.1f} min", flush=True)
    return code


def arm_numbers(psalm: int, root: Path) -> dict:
    f = files(psalm, root / f"psalm_{psalm}")
    cost = json.loads(f["cost"].read_text(encoding="utf-8")) if f["cost"].exists() else {}
    stages = {}
    for st in cost.get("stages") or []:        # a stage can repeat (attempts): sum them
        stages[st.get("stage", "?")] = stages.get(st.get("stage", "?"), 0) + st.get("cost_usd", 0)
    return {"total": cost.get("total_cost"), "stages": stages,
            "bundle": len(f["research"].read_text(encoding="utf-8")) if f["research"].exists() else None,
            "docx": f["docx"] if f["docx"].exists() else None}


def summarize(psalm: int, ab: Path, section_stats: dict, n_targum: int):
    a, b = arm_numbers(psalm, ab / "A"), arm_numbers(psalm, ab / "B")
    money = lambda x: f"${x:.2f}" if isinstance(x, (int, float)) else "—"
    lines = [f"# Psalm {psalm}: reception + Targum A/B (Session 391)", "",
             "Arm A = today's pipeline. Arm B = the same macro, micro, research bundle and echoes, plus the "
             "Sefaria reception section and a Targum line per verse; synthesis discovery and the writer ran "
             "fresh in both. Design: `docs/plans/S391_SEFARIA_EVALUATION.md` §5a.", "",
             f"Reception section: {section_stats.get('kept')} passages of {section_stats.get('located')} located, "
             f"{section_stats.get('chars', 0):,} chars (`reception_section.md`). Targum verses: {n_targum}.", "",
             "| | Arm A | Arm B |", "|---|---|---|",
             f"| Total cost | {money(a['total'])} | {money(b['total'])} |"]
    for stage in list(dict.fromkeys(list(a["stages"]) + list(b["stages"]))):
        lines.append(f"| {stage} | {money(a['stages'].get(stage))} | {money(b['stages'].get(stage))} |")
    fmt = lambda n: f"{n:,}" if n else "—"
    lines.append(f"| Research bundle (chars) | {fmt(a['bundle'])} | {fmt(b['bundle'])} |")
    lines += ["", "Read both guides (the copies at the top of this folder). The $0 claim check of every "
              "rabbinic / Targum / midrash attribution in both arms is the next step (ask Claude)."]
    (ab / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for arm, label in (("A", "A - today's pipeline"), ("B", "B - with reception and Targum")):
        f = files(psalm, ab / arm / f"psalm_{psalm}")
        for key in ("docx", "pdf"):
            if f[key].exists():
                shutil.copy2(f[key], ab / f"Psalm {psalm} - {label}{f[key].suffix}")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("psalm", type=int, nargs="?", default=76)
    ap.add_argument("--arms", nargs="+", choices=["A", "B"], default=["A", "B"])
    ap.add_argument("--dry-run", action="store_true", help="$0: build the reception section and Targum, print the plan")
    ap.add_argument("--redo", action="store_true", help="re-run an arm that already produced its DOCX")
    ap.add_argument("--skip-copy-edit", action="store_true", help="no copy editor (saves ~$0.5 per arm)")
    ap.add_argument("--delay", type=int, default=5, help="seconds between pipeline steps (production default 120)")
    args = ap.parse_args()
    psalm = args.psalm

    prod = psalm_output_dir(psalm)
    prod_macro = files(psalm, prod)["macro"]
    ab = REPO / "output" / "_s391_reception_ab" / f"psalm_{psalm}"
    A, B = ab / "A", ab / "B"
    problems = [p for p in (prod_macro, REPO / "database" / "tanakh.db") if not p.exists()]
    if problems:
        sys.exit(f"Missing: {', '.join(map(str, problems))}")

    from src.data_sources.sefaria_reception import build_section
    from src.data_sources.targum import targum_by_verse
    section, stats = build_section(psalm)
    targum = targum_by_verse(psalm)
    ab.mkdir(parents=True, exist_ok=True)
    (ab / "reception_section.md").write_text(section, encoding="utf-8")
    print(f"Reception section: {stats['kept']} of {stats['located']} located passages, {stats['chars']:,} chars; "
          f"failed fetches: {stats['failed'] or 'none'}")
    for verses, tier, ref in stats["kept_refs"]:
        print(f"   {tier} v{','.join(map(str, verses)):<10} {ref}")
    print(f"Targum: {len(targum)} verses, {sum(1 for _, e in targum.values() if e)} with English")
    print(f"Macro reused from: {prod_macro}")
    lo = EST["micro"][0] + EST["echoes"][0] + 2 * EST["sd_writer"][0]
    hi = EST["micro"][1] + EST["echoes"][1] + 2 * EST["sd_writer"][1]
    if not args.skip_copy_edit:
        lo, hi = lo + 2 * EST["copy_edit"][0], hi + 2 * EST["copy_edit"][1]
    print(f"Estimated spend for arms {args.arms}: ~${lo:.0f}-{hi:.0f} (Ps 76 scale; both arms)")
    if args.dry_run:
        print("Dry run: nothing paid. Results would go to", ab)
        return

    backup = ab / "_backup"
    backup.mkdir(parents=True, exist_ok=True)
    canonical_echoes = REPO / "data" / "literary_echoes" / f"psalm_{psalm:03d}_literary_echoes.txt"
    had_echoes = canonical_echoes.exists()
    if had_echoes:
        shutil.copy2(canonical_echoes, backup / canonical_echoes.name)
    dumps = debug_dumps(psalm)
    for d in dumps:
        shutil.copy2(d, backup / d.name)

    def keep_shared(root: Path):
        if canonical_echoes.exists():
            shutil.copy2(canonical_echoes, root / f"psalm_{psalm}" / "echoes_dossier_used.txt")
        (root / "debug").mkdir(exist_ok=True)
        for d in debug_dumps(psalm):
            shutil.copy2(d, root / "debug" / d.name)

    try:
        if "A" in args.arms:
            fa = files(psalm, A / f"psalm_{psalm}")
            if fa["docx"].exists() and not args.redo:
                print(f"Arm A already finished ({fa['docx']}); --redo to re-run")
            else:
                fa["macro"].parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(prod_macro, fa["macro"])
                if run_arm("A", psalm, A, ["--no-reception", "--no-targum", "--no-fact-check"],  # S394: these became defaults
                           args.delay, args.skip_copy_edit) != 0:
                    sys.exit("Arm A failed; arm B needs its bundle. Fix and re-run.")
                keep_shared(A)
        if "B" in args.arms:
            fa, fb = files(psalm, A / f"psalm_{psalm}"), files(psalm, B / f"psalm_{psalm}")
            if fb["docx"].exists() and not args.redo:
                print(f"Arm B already finished ({fb['docx']}); --redo to re-run")
            else:
                missing = [k for k in ("macro", "micro", "research") if not fa[k].exists()]
                if missing:
                    sys.exit(f"Arm B needs arm A's {missing}; run arm A first")
                if fb["macro"].parent.exists() and args.redo:
                    shutil.rmtree(fb["macro"].parent)
                fb["macro"].parent.mkdir(parents=True, exist_ok=True)
                for k in ("macro", "micro", "research"):     # NOT the cost/stats files: B's cost is B's
                    shutil.copy2(fa[k], fb[k])
                # The writer and synthesis discovery trim a bundle over TRIM_CEILING (Related Psalms
                # first). Over it in B only, B would lose material A kept: a confound, so refuse.
                from src.data_sources.sefaria_reception import insert_section
                b_size = len(insert_section(fa["research"].read_text(encoding="utf-8"), section))
                print(f"Arm B bundle will be {b_size:,} chars (A: {fa['research'].stat().st_size:,} bytes); "
                      f"trim ceiling {TRIM_CEILING:,}")
                if b_size > TRIM_CEILING:
                    sys.exit(f"Arm B's bundle ({b_size:,} chars) would be TRIMMED and arm A's not: the arms "
                             "would differ in more than the new material. Lower PER_VERSE_CHARS or raise the "
                             "ceiling in both arms first.")
                if (A / f"psalm_{psalm}" / "echoes").is_dir():
                    shutil.copytree(A / f"psalm_{psalm}" / "echoes", B / f"psalm_{psalm}" / "echoes", dirs_exist_ok=True)
                code = run_arm("B", psalm, B, ["--skip-micro", "--skip-lit-echoes", "--reception", "--targum", "--no-fact-check"],
                               args.delay, args.skip_copy_edit)
                keep_shared(B)
                if code != 0:
                    print("Arm B failed; see its log above.")
    finally:
        if had_echoes:
            shutil.copy2(backup / canonical_echoes.name, canonical_echoes)
        elif canonical_echoes.exists():
            canonical_echoes.unlink()
        for d in dumps:
            shutil.copy2(backup / d.name, d)
        print(f"Restored the production echoes dossier and {len(dumps)} debug dumps for Psalm {psalm}.")
    summarize(psalm, ab, stats, len(targum))


if __name__ == "__main__":
    main()
