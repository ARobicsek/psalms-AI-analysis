#!/usr/bin/env python3
"""
Session 385 fact-check test driver (Psalm 76). Experimental; archive-only.

    python archive/psalm_76_S385_fact_check/run_s385_fact_check.py probe-a
    python archive/psalm_76_S385_fact_check/run_s385_fact_check.py main --source F|B383
    python archive/psalm_76_S385_fact_check/run_s385_fact_check.py sol --source F
    python archive/psalm_76_S385_fact_check/run_s385_fact_check.py compare --source F
    python archive/psalm_76_S385_fact_check/run_s385_fact_check.py docx --source F
    python archive/psalm_76_S385_fact_check/run_s385_fact_check.py spent

Every API step is recorded in ledger.json and refused once the ledger would
pass the $12 cap. The copy editor's input (print_ready.md) is built the way
STEP 5 builds it — CommentaryFormatter over the writer's intro + verses — with
the psalm text taken from the S384 inputs block, since tanakh.db is not in the
container.
"""

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv  # noqa: E402
load_dotenv(ROOT / ".env")  # OPENAI_API_KEY (and ANTHROPIC_API_KEY), before any client is created

PSALM = 76
CAP = 12.0
LEDGER = HERE / "ledger.json"
INPUTS = ROOT / "archive/psalm_76_S384_essay_trials/prompts/inputs_block.txt"
B383 = ROOT / "archive/psalm_76_S383_opus55_ab/B_opus55"
STATS = B383 / "psalm_076_pipeline_stats.json"
SOURCES = {
    # the sibling session's two-call run: essay F + its verse commentary
    "F": ROOT / "archive/psalm_76_S385_two_call/F",
    # fallback: the S383 all-Opus-5.5 guide
    "B383": B383,
}


# -- ledger -------------------------------------------------------------------
def ledger() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def spent() -> float:
    return round(sum(e.get("cost_usd", 0) for e in ledger()["entries"]), 4)


def record(entry: dict) -> None:
    d = ledger()
    d["entries"].append(entry)
    LEDGER.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  ledger: +${entry.get('cost_usd', 0):.4f} → ${spent():.4f} of ${CAP}")


def need(estimate: float, label: str) -> None:
    if spent() + estimate > CAP:
        raise SystemExit(f"REFUSED {label}: ${spent():.2f} spent + ~${estimate:.2f} would pass the ${CAP} cap")


def budget_guard(label: str):
    base = spent()

    def check(running: float):
        if base + running > CAP - 0.25:
            raise RuntimeError(f"{label}: stopping, ${base + running:.2f} would pass the cap")
    return check


# -- inputs ---------------------------------------------------------------------
def psalm_text_data() -> dict:
    from s385_two_call_writer import psalm_verses
    return psalm_verses(INPUTS.read_text(encoding="utf-8"))


def intro_verses(source: str):
    d = SOURCES[source]
    if source == "B383":
        from s385_two_call_writer import parse_guide  # the production parser's regexes
        raw = (d / "master_writer_v4_response_psalm_76.txt").read_text(encoding="utf-8")
        g = parse_guide(raw)
        return g["introduction"], g["verse_commentary"]
    return ((d / "psalm_076_edited_intro.md").read_text(encoding="utf-8"),
            (d / "psalm_076_edited_verses.md").read_text(encoding="utf-8"))


def build_print_ready(source: str, out_dir: Path) -> Path:
    from src.utils.commentary_formatter import CommentaryFormatter
    intro, verses = intro_verses(source)
    md = CommentaryFormatter().format_commentary(
        psalm_num=PSALM, intro_text=intro, verses_text=verses,
        summary_data=json.loads(STATS.read_text(encoding="utf-8")),
        psalm_text_data=psalm_text_data())
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "psalm_076_print_ready.md"
    p.write_text(md, encoding="utf-8")
    print(f"  print_ready: {p.relative_to(ROOT)} ({len(md):,} chars)")
    return p


# -- steps ---------------------------------------------------------------------
def fact_check(guide: Path, out_dir: Path, label: str, prefix: str = "") -> dict:
    from src.agents.fact_checker import FactChecker, write_outputs
    need(4.0, label)
    fc = FactChecker(db_path=ROOT / "database/tanakh.db", budget_check=budget_guard(label))
    res = fc.check(guide.read_text(encoding="utf-8"), PSALM, INPUTS.read_text(encoding="utf-8"),
                   thinking_out=out_dir / f"{prefix}psalm_076_fact_check_thinking.txt")
    paths = write_outputs(res, PSALM, out_dir, prefix)
    m = res.meta(PSALM)
    record({"step": label, "model": res.model, "cost_usd": round(res.cost_usd, 4),
            "token_cost_usd": round(res.token_cost_usd, 4), "search_cost_usd": round(res.search_cost_usd, 4),
            "web_searches": res.web_searches, "function_calls": res.function_calls,
            "usage": res.usage, "seconds": m["seconds"], "verdicts": m["verdicts"], "claims": len(res.records)})
    return {"paths": paths, "result": res}


def copy_edit(print_ready: Path, out_dir: Path, label: str, model: str = None,
              report_json: Path = None) -> dict:
    from src.agents.copy_editor import CopyEditor
    from src.agents.fact_checker import load_copy_editor_prompt
    from src.utils.cost_tracker import CostTracker
    need(1.2, label)
    out_dir.mkdir(parents=True, exist_ok=True)
    tracker = CostTracker()
    ed = CopyEditor(model=model, cost_tracker=tracker)
    supp = load_copy_editor_prompt(report_json) if report_json else None
    if supp:
        (out_dir / "supplementary_prompt.txt").write_text(supp, encoding="utf-8")
    r = ed.edit_commentary(PSALM, input_file=print_ready, output_dir=out_dir, supplementary_prompt=supp)
    cost = tracker.calculate_cost(ed.model)["total_cost"]
    counts = ed._count_changes(r["changes_summary"])
    u = tracker.usage_by_model[ed.model]
    record({"step": label, "model": ed.model, "cost_usd": round(cost, 4),
            "usage": {"input": u.input_tokens, "output": u.output_tokens, "reasoning": u.thinking_tokens},
            "changes": counts})
    return r


def cmd_probe_a():
    out = HERE / "probe_A"
    out.mkdir(parents=True, exist_ok=True)
    fact_check(B383 / "psalm_076_copy_edited.md", out,
               "Probe A: fact check of the S383 B copy-edited guide (gpt-6-sol, web search, bundle)")


def cmd_main(source: str):
    base = HERE / f"main_{source}"
    pr = build_print_ready(source, base)
    fc = fact_check(pr, base, f"Main ({source}): fact check of print_ready")
    rep = fc["paths"]["json"]
    copy_edit(pr, base / "copy_edit_with_report", f"Main ({source}): copy edit gpt-5.4 WITH report",
              report_json=rep)
    copy_edit(pr, base / "copy_edit_control", f"Main ({source}): copy edit gpt-5.4 WITHOUT report (control)")


def cmd_sol(source: str):
    base = HERE / f"main_{source}"
    copy_edit(base / "psalm_076_print_ready.md", base / "copy_edit_sol_with_report",
              f"Main ({source}): copy edit gpt-6-sol WITH report (optional)", model="gpt-6-sol",
              report_json=base / "psalm_076_fact_check.json")


def cmd_docx(source: str):
    """Compact reading DOCX of the fact-checked, copy-edited guide, via the
    two-call writer's build_docx (production DocumentGenerator, psalm text stubbed)."""
    from s385_two_call_writer import build_docx
    from run_enhanced_pipeline import _extract_sections_from_copy_edited
    base = HERE / f"main_{source}"
    ce = base / "copy_edit_with_report" / "psalm_076_copy_edited.md"
    intro, verses = _extract_sections_from_copy_edited(ce)
    vdir = base / "docx_build"
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / "psalm_076_edited_intro.md").write_text(intro, encoding="utf-8")
    (vdir / "psalm_076_edited_verses.md").write_text(verses, encoding="utf-8")
    fc = json.loads((base / "psalm_076_fact_check.json").read_text(encoding="utf-8"))
    def plain(md: str) -> str:  # the appendix renders paragraphs, not headings
        return re.sub(r"(?m)^#{1,6}\s+(.+)$", r"**\1**", md)
    parts = [("Fact-check report (gpt-6-sol)",
              plain((base / "psalm_076_fact_check.md").read_text(encoding="utf-8"))),
             ("Copy-edit change log (gpt-5.4, with the report)",
              plain((base / "copy_edit_with_report" / "psalm_076_copy_edit_changes.md").read_text(encoding="utf-8")))]
    note = (f"Psalm 76, guide '{source}', copy-edited by gpt-5.4 with the Session 385 fact-check report. "
            f"Appendix: the fact-check report ({len(fc['claims'])} claims, {fc['meta']['verdicts']}) and "
            f"the copy editor's change log.")
    out = HERE / f"Psalm 76 - {source} fact-checked and copy-edited (S385).docx"
    build_docx(vdir, note, parts, out)


# Strings that must SURVIVE every copy-edit arm (claims from memory that are true),
# and the one that must NOT survive the arm given the report (F's Rashi on 76:11).
MUST_SURVIVE = {
    "Byron, line 1": "For the Angel of Death spread his wings on the blast",
    "Byron, line 4": "And their hearts but once heaved, and for ever grew still!",
    "Byron, 'breath of his pride'": "But through it there roll'd not the breath of his pride.",
    "Herodotus 2.141 cited": "Herodotus (2.141)",
    "Herodotus inscription": "ἐς ἐμέ τις ὁρέων εὐσεβὴς ἔστω",
    "prism: bird in a cage": "like a bird in a cage",
    "prism: talents": "thirty talents of gold, eight hundred of silver",
    "prism: daughters": "his own daughters",
}
RASHI_ERROR = "Rashi offers two readings"


def _arm_stats(arm: Path) -> dict:
    ch = (arm / "psalm_076_copy_edit_changes.md").read_text(encoding="utf-8")
    text = (arm / "psalm_076_copy_edited.md").read_text(encoding="utf-8")
    body, _, unver = ch.partition("### UNVERIFIED")
    entries = [l for l in body.splitlines() if re.match(r"^\s*\d+\.\s", l)]
    cats = {}
    for l in entries:
        for grp in re.findall(r"\[(\d+(?:,\s*\d+)*)\]", l):
            for n in grp.split(","):
                cats[int(n)] = cats.get(int(n), 0) + 1
    return {
        "changes": len(entries),
        "category_7": cats.get(7, 0),
        "by_category": dict(sorted(cats.items())),
        "fact_check_tagged": sum("[FACT-CHECK]" in l for l in entries),
        "unverified_notes": len([l for l in unver.splitlines() if l.strip().startswith(("-", "*")) or re.match(r"^\s*\d+\.", l)]),
        "survivors": {k: (v in text) for k, v in MUST_SURVIVE.items()},
        "rashi_two_readings_still_there": RASHI_ERROR in text,
        "girding_reading_present": bool(re.search(r"gird", text[text.find("Verse 11"):] if "Verse 11" in text else text, re.I)),
        "category_7_entries": [l.strip() for l in entries if re.search(r"\[[^\]]*\b7\b[^\]]*\]", l)],
    }


def cmd_compare(source: str):
    """$0. Edit counts and probe survival per copy-edit arm; writes comparison.json."""
    base = HERE / f"main_{source}"
    fc = json.loads((base / "psalm_076_fact_check.json").read_text(encoding="utf-8"))
    out = {"fact_check": fc["meta"]["verdicts"], "arms": {}}
    rashi = [c for c in fc["claims"] if "Rashi" in c["sentence"] and ("76:11" in c["location"] or "two readings" in c["sentence"])]
    out["rashi_records"] = [{k: c[k] for k in ("id", "location", "verdict", "claim")} for c in rashi]
    out["probe_records"] = {k: [{"id": c["id"], "verdict": c["verdict"]} for c in fc["claims"]
                                if v[:25] in c["sentence"] or v[:25] in c.get("claim", "")]
                            for k, v in MUST_SURVIVE.items()}
    for arm in ("copy_edit_control", "copy_edit_with_report", "copy_edit_sol_with_report"):
        if (base / arm / "psalm_076_copy_edited.md").exists():
            out["arms"][arm] = _arm_stats(base / arm)
    (base / "comparison.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for arm, st in out["arms"].items():
        lost = [k for k, ok in st["survivors"].items() if not ok]
        print(f"{arm}: {st['changes']} changes, cat-7 {st['category_7']}, [FACT-CHECK] {st['fact_check_tagged']}, "
              f"UNVERIFIED notes {st['unverified_notes']}; Rashi error still there: {st['rashi_two_readings_still_there']}; "
              f"lost probes: {lost or 'none'}")
    print(f"  → {base / 'comparison.json'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["probe-a", "main", "sol", "docx", "compare", "spent", "print-ready"])
    ap.add_argument("--source", default="F", choices=list(SOURCES))
    a = ap.parse_args()
    if a.cmd == "spent":
        print(f"${spent():.4f} of ${CAP}")
    elif a.cmd == "probe-a":
        cmd_probe_a()
    elif a.cmd == "print-ready":
        build_print_ready(a.source, HERE / f"main_{a.source}")
    elif a.cmd == "main":
        cmd_main(a.source)
    elif a.cmd == "sol":
        cmd_sol(a.source)
    elif a.cmd == "docx":
        cmd_docx(a.source)
    elif a.cmd == "compare":
        cmd_compare(a.source)


if __name__ == "__main__":
    main()
