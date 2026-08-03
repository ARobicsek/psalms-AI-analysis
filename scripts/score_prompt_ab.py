"""
Score the Session-371 writer-prompt A/B/C arms.

Reads each arm's `psalm_<NNN>_full.md` — the RAW writer output, composed at writer
time and never rewritten by ab_finish_arms.py. (Do not score `_edited_verses.md`:
after finishing, that file holds COPY-EDITED text, so scoring it would measure the
copy editor as much as the prompt.)

Every metric here is STRUCTURAL — a count of forms, not a match against a prior arm's
phrasing. Session 370's scoring script keyed on the baseline's exact wording and cried
"LOST" four times on content that had survived reworded, including the single best
outcome in the run (see WRITER_PROMPT_RULE_8B_FINDINGS.md §7).

⚠️  SESSION 372 — READ BEFORE INTERPRETING ANY BETA-READER ROW.

Sessions 370-371 treated the beta reader's INERT CITATIONS / UNEXPLAINED GRAMMAR
counters as "the trustworthy quality signal." They are not, at n=1. Four independent
reads of ONE FIXED TEXT (`beta_reader_variance.py`, Psalm 71) gave:

    base   UNEXPLAINED GRAMMAR  [6, 6, 1, 5]   range 5
    A      UNEXPLAINED GRAMMAR  [14, 9, 11, 15] range 6
    base   INERT CITATIONS      [8, 9, 6, 6]   range 3
    base   Wit                  [4, 6, 3, 4]   range 3
    base   Emotional impact     [8, 6, 6, 7]   range 2

Two consequences, both load-bearing:

  1. Every between-arm gap of 1-3 on these rows in the Session 370-372 record is
     inside the judge's own noise and means nothing.
  2. Session 371's recorded "UNEXPLAINED GRAMMAR 11 -> 9, arm A shows no capability
     regression" is INVERTED. On repeated measurement base averages 4.5 and arm A
     averages 12.25 — deleting the checklist made grammar explanation markedly worse,
     and single-sampling hid it because both originals happened to be off in
     opposite directions.

The rows that ARE trustworthy are the deterministic ones — every regex count in this
file, plus `check_phrase_coverage.py`. They have zero variance by construction: the
same text always yields the same number. Arm E's Session-372 result rests entirely on
those.

Rows sourced from the beta reader are marked with a dagger in the output table, and
carry their measured noise band in the label. Treat a dagger row as evidence only when
the gap exceeds that band.

The beta reader is now OFF by default in both production pipelines (Session 372) —
`run_enhanced_pipeline.py --beta-reader` / `run_si_pipeline.py --beta-reader` opt back
in for a deliberate one-off read. Repeat-sampling to beat the noise was considered and
rejected: it multiplies cost for a judge whose output we do not trust at any n. The
dagger rows below are therefore historical for existing arms and will be blank for new
runs — read the deterministic rows instead.

Usage:
    python scripts/score_prompt_ab.py 71
    python scripts/score_prompt_ab.py 71 --out docs/plans/SESSION_371_AB_RESULTS.md
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

HEB = r"֐-׿"
HEB_RUN = re.compile(rf"[{HEB}][{HEB}\s־'\"־]{{3,}}")

COMMENTATORS = [
    "Rashi", "Ibn Ezra", "Radak", "Meiri", "Malbim",
    # Session 373 additions. "Malbim Beur Hamilot" deliberately absent: it contains
    # "Malbim", so counting both would double-count every mention of either.
    "Alshich", "Romemot El", "Minchat Shai", "Metzudat Zion", "Chomat Anakh", "Chida",
    "Torah Temimah",
]

# RULE 7's own banned list.
BLURRY = ["atmosphere", "density", "resonance", "texture", "dimensions",
          "contours", "dynamics", "framework", "matrix", "tapestry"]

# RULE 3b-2's own list of terms the reader is assumed NOT to know.
GRAMMAR_TERMS = [
    "conjunction", "particle", "preposition", "participle", "perfect",
    "imperfect", "passive", "causative", "reflexive", "construct", "vocative",
    "apposition", "imperative", "cohortative", "jussive", "enclitic",
    "antecedent", "predicate",
]

# RULE 8b's explicit tells that a second commentator is carrying one point.
REDUNDANCY = ["says the same", "reads it the same", "agrees", "similarly",
              "likewise", "compresses it", "makes the same point"]


def split_full(text: str):
    marker = "## Verse-by-Verse Commentary"
    i = text.find(marker)
    if i < 0:
        return text, ""
    return text[:i], text[i + len(marker):]


def verses_covered(verse_text: str) -> int:
    """Count distinct verse numbers claimed by headers, since the writer may group
    ('**Verses 10-11**')."""
    seen = set()
    for m in re.finditer(r"\*\*Verses?\s+(\d+)(?:\s*[-–—]\s*(\d+))?\*\*", verse_text):
        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) else lo
        seen.update(range(lo, hi + 1))
    return len(seen)


def tier1_quotes(text: str) -> int:
    """A commentator named with a real Hebrew quotation attached: at least four
    Hebrew words within 250 chars after the name. Approximates 'full quotation'
    (Hebrew + translation + unfolding) versus a bare Tier-2 clause."""
    n = 0
    for name in COMMENTATORS:
        for m in re.finditer(re.escape(name), text):
            window = text[m.end(): m.end() + 250]
            heb = HEB_RUN.findall(window)
            if heb and sum(len(h.split()) for h in heb) >= 4:
                n += 1
    return n


def count_words(patterns, text, word_boundary=True) -> int:
    t = text.lower()
    n = 0
    for p in patterns:
        pat = rf"\b{re.escape(p.lower())}\b" if word_boundary else re.escape(p.lower())
        n += len(re.findall(pat, t))
    return n


def bolded_hebrew(text: str) -> int:
    return sum(
        1 for m in re.finditer(r"\*\*[^*\n]{1,14}\*\*", text)
        if re.search(rf"[{HEB}]", m.group(0))
    )


def beta_counters(arm_dir: Path, psalm: int) -> dict:
    f = arm_dir / f"psalm_{psalm:03d}_beta_read.md"
    out = {"inert_citations": None, "unexplained_grammar": None,
           "landing": None, "scores": None}
    if not f.exists():
        return out
    t = f.read_text(encoding="utf-8")
    out["poets_feeling"] = None
    for key, pat in (("inert_citations", r"INERT CITATIONS:\s*(\d+)"),
                     ("unexplained_grammar", r"UNEXPLAINED GRAMMAR:\s*(\d+)"),
                     # Session 372: the author's "wonder" item — the POET's own
                     # powerful emotion conveyed, not the reader's AHA. Measured
                     # before any prompt intervention, deliberately: five attempts
                     # to legislate an affect have produced the opposite.
                     ("poets_feeling", r"POET'S FEELING:\s*(\d+)")):
        m = re.search(pat, t)
        if m:
            out[key] = int(m.group(1))
    m = re.search(r"LANDING:\s*([a-z\-]+)", t)
    if m:
        out["landing"] = m.group(1)
    scores = dict(re.findall(r"^-\s*([A-Za-z ]+?):\s*(\d+)/10", t, re.M))
    if scores:
        out["scores"] = {k.strip(): int(v) for k, v in scores.items()}
    return out


def score_arm(arm_dir: Path, psalm: int) -> dict:
    full = arm_dir / f"psalm_{psalm:03d}_full.md"
    if not full.exists():
        return {}
    text = full.read_text(encoding="utf-8")
    intro, verses = split_full(text)
    nverses = verses_covered(verses) or 1
    vwords = len(verses.split())

    t1 = tier1_quotes(verses)
    mentions = count_words(COMMENTATORS, verses, word_boundary=False)

    row = {
        "arm": arm_dir.name,
        "intro_words": len(intro.split()),
        "verse_words": vwords,
        "total_words": len(text.split()),
        "verses_covered": nverses,
        "words_per_verse": round(vwords / nverses, 1),
        "commentator_mentions": mentions,
        "tier1_quotes": t1,
        "tier1_per_verse": round(t1 / nverses, 2),
        "commentator_density_per_1k": round(mentions / (vwords / 1000), 1),
        "bolded_hebrew": bolded_hebrew(text),
        "grammar_terms": count_words(GRAMMAR_TERMS, text),
        "blurry_nouns": count_words(BLURRY, text),
        "redundancy_markers": count_words(REDUNDANCY, text, word_boundary=False),
        "blockquote_lines": len(re.findall(r"^>", text, re.M)),
    }
    row.update(beta_counters(arm_dir, psalm))
    return row


def load_run_stats(ab_dir: Path) -> dict:
    f = ab_dir / "ab_summary.json"
    if not f.exists():
        return {}
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {a["arm"]: a for a in data.get("arms", []) if "arm" in a}


ORDER = ["base", "A_no_scaffolding", "B_positive_examples", "C_conciseness"]


def main() -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("psalm", type=int)
    ap.add_argument("--ab-dir", default="_prompt_ab")
    ap.add_argument("--out", default=None, help="Also write the table to this path")
    args = ap.parse_args()

    ab_dir = ROOT / "output" / f"psalm_{args.psalm}" / args.ab_dir
    if not ab_dir.exists():
        print(f"ERROR: {ab_dir} does not exist", file=sys.stderr)
        return 1

    stats = load_run_stats(ab_dir)
    dirs = [d for d in ab_dir.iterdir() if d.is_dir()]
    dirs.sort(key=lambda d: ORDER.index(d.name) if d.name in ORDER else 99)

    rows = []
    for d in dirs:
        r = score_arm(d, args.psalm)
        if not r:
            continue
        s = stats.get(d.name, {})
        r["cost_usd"] = s.get("cost_usd")
        r["output_tokens"] = s.get("output_tokens")
        r["elapsed_s"] = s.get("elapsed_s")
        r["prompt_delta_chars"] = s.get("prompt_delta_chars")
        rows.append(r)

    if not rows:
        print("No scoreable arms found.", file=sys.stderr)
        return 1

    def cell(v):
        return "—" if v is None else str(v)

    metrics = [
        ("prompt Δchars", "prompt_delta_chars"),
        ("verse words", "verse_words"),
        ("words / verse", "words_per_verse"),
        ("intro words", "intro_words"),
        # † = beta-reader sourced. High test-retest variance at n=1 — see the module
        # docstring. A gap of 1-3 on these rows is noise, not a finding.
        ("† INERT CITATIONS (±3)", "inert_citations"),
        ("† UNEXPLAINED GRAMMAR (±6)", "unexplained_grammar"),
        ("† POET'S FEELING (no signal)", "poets_feeling"),
        ("† LANDING", "landing"),
        ("commentator mentions", "commentator_mentions"),
        ("Tier-1 quotes", "tier1_quotes"),
        ("Tier-1 / verse", "tier1_per_verse"),
        ("commentators / 1k words", "commentator_density_per_1k"),
        ("grammar terms named", "grammar_terms"),
        ("bolded Hebrew", "bolded_hebrew"),
        ("blurry nouns", "blurry_nouns"),
        ("redundancy markers", "redundancy_markers"),
        ("quoted lines (echoes)", "blockquote_lines"),
        ("output tokens", "output_tokens"),
        ("cost $", "cost_usd"),
        ("seconds", "elapsed_s"),
    ]

    hdr = "| metric | " + " | ".join(r["arm"] for r in rows) + " |"
    sep = "|---|" + "---|" * len(rows)
    lines = [f"# Writer-prompt A/B/C — Psalm {args.psalm}", "",
             "Scored on RAW writer output (`psalm_*_full.md`), before copy edit.",
             "All metrics are structural counts, never matches against a prior arm's",
             "wording — see WRITER_PROMPT_RULE_8B_FINDINGS.md §7.", "", hdr, sep]
    for label, key in metrics:
        lines.append(f"| {label} | " + " | ".join(cell(r.get(key)) for r in rows) + " |")

    base = next((r for r in rows if r["arm"] == "base"), None)
    if base:
        lines += ["", "**Verse-word change vs baseline:** " + ", ".join(
            f"{r['arm']} {r['verse_words'] - base['verse_words']:+,} "
            f"({r['verse_words'] / base['verse_words']:.2f}x)"
            for r in rows if r["arm"] != "base")]

    out = "\n".join(lines) + "\n"
    print(out)
    (ab_dir / "scorecard.md").write_text(out, encoding="utf-8")
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
        print(f"-> {args.out}")
    print(f"-> {(ab_dir / 'scorecard.md').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
