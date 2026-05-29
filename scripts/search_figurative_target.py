"""
Figurative Language Target Search (full-quotation report)

Searches the Biblical figurative-language database for instances whose TARGET
is a given concept and writes a Markdown report containing the full verse
quotations (Hebrew + English) and every tagging field (target, vehicle,
ground, posture, explanation, speaker, purpose, confidence, deliberations).

Default concept group is "wilderness" / מִדְבָּר and its synonyms
(desert, wasteland, steppe, arabah, negeb, jeshimon, parched/arid land, ...).

The target field stores hierarchical English analytical tags as a JSON array,
so matching is done in English with WORD-BOUNDARY regex to avoid false
positives such as "desertion" / "deserter" / "just deserts". A separate,
optional Hebrew-root cross-check surfaces figurative verses whose Hebrew text
contains מדבר / ישימון / ערבה / ציה / נגב even if the English target tag did
not use a wilderness word.

Usage:
    python scripts/search_figurative_target.py
    python scripts/search_figurative_target.py --book Psalms
    python scripts/search_figurative_target.py --broad
    python scripts/search_figurative_target.py --terms wilderness desert wasteland
    python scripts/search_figurative_target.py --hebrew-crosscheck
    python scripts/search_figurative_target.py --output output/my_search.md

Output (default): output/figurative_search_wilderness.md
"""

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

# Allow running from project root and reuse the canonical DB path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.agents.figurative_librarian import FIGURATIVE_DB_PATH


# Core terrain synonyms (precise — minimal noise). Matched whole-word against
# any element of the hierarchical target array.
CORE_TERMS = [
    "wilderness",
    "desert",        # \bdeserts?\b only — excludes desertion/deserter/deserted
    "wasteland",
    "steppe",
    "arabah",
    "aravah",
    "negeb",
    "negev",
    "jeshimon",
    "badlands",
    "arid",
    "parched",
]

# Broader land-condition words. These overlap with non-terrain meanings
# ("barren woman", "desolate heart", "wild animals"), so they are opt-in
# via --broad.
BROAD_TERMS = [
    "barren",
    "desolate",
    "desolation",
    "wild",
    "drought",
]

# Maximal net (--maximal). Deliberately over-inclusive across the whole
# wilderness / wild-area / desert / uninhabited-land semantic field. Expect
# many false positives ("salt of the covenant", "empty words", "sand of the
# sea", "thirst for God") — these are intended to be removed by a downstream
# LLM filtering pass, not by the keyword layer.
MAXIMAL_EXTRA = [
    "waste",
    "ruin",
    "uninhabited",
    "deserted",
    "dry",
    "thirst",
    "thirsty",
    "waterless",
    "trackless",
    "pathless",
    "solitary",
    "solitude",
    "howling",
    "scrub",
    "scrubland",
    "thicket",
    "remote",
    "inhospitable",
    "empty",
    "emptiness",
    "void",
    "formless",
    "chaos",
    "bleak",
    "untamed",
    "untilled",
    "fallow",
    "salt",
    "sand",
]

# Idiomatic phrases that contain a synonym but are never about terrain.
# If a candidate's target text matches a wilderness term ONLY because of one
# of these phrases, the instance is dropped.
SKIP_PHRASES = [
    "just desert",   # "just deserts under royal justice"
]

# Hebrew roots/words for the supplementary cross-check (vowel-stripped text).
# Restricted to genuine "wilderness" words. נגב / חרבה / שממה are deliberately
# excluded: they are polysemous (south-region / generic ruin / generic
# desolation) and flood the cross-check with off-topic figurative verses.
HEBREW_ROOTS = {
    "מדבר": "midbar (wilderness)",
    "ישימון": "yeshimon (wasteland/desert)",
    "ערבה": "aravah (desert plain)",
    "ציה": "tziyyah (parched land)",
}


def build_term_regex(term: str) -> re.Pattern:
    """Whole-word, case-insensitive matcher for a synonym.

    'desert' is special-cased to deserts? so it never matches
    desertion / deserting / deserter / deserted.
    """
    if term == "desert":
        return re.compile(r"\bdeserts?\b", re.IGNORECASE)
    return re.compile(r"\b" + re.escape(term) + r"\w*", re.IGNORECASE)


def matched_terms(target_list, term_regexes):
    """Return the list of synonyms that match anywhere in the target array."""
    if not target_list:
        return []
    joined = " | ".join(str(t) for t in target_list)
    hits = []
    for term, rx in term_regexes.items():
        if rx.search(joined):
            hits.append(term)
    return hits


def is_skip_only(target_list, hits):
    """True if the only reason this matched is an idiomatic skip phrase."""
    if hits != ["desert"]:
        return False
    joined = " | ".join(str(t) for t in (target_list or [])).lower()
    return any(p in joined for p in SKIP_PHRASES)


def fetch_field_matches(conn, terms, book, field):
    """Pull candidate rows (broad LIKE) then filter with word-boundary regex.

    `field` is 'target' or 'vehicle' — the hierarchical tag the synonyms are
    matched against. All tag fields are still selected and displayed.
    """
    term_regexes = {t: build_term_regex(t) for t in terms}

    where = ["1=1"]
    params = []
    if book:
        where.append("v.book = ?")
        params.append(book)
    # Broad OR of LIKE %term% to pull candidates; precise filtering in Python.
    like_clauses = []
    for t in terms:
        like_clauses.append(f"f.{field} LIKE ? COLLATE NOCASE")
        params.append(f"%{t}%")
    where.append("(" + " OR ".join(like_clauses) + ")")

    sql = f"""
        SELECT f.id AS fig_id, v.reference, v.book, v.chapter, v.verse,
               v.hebrew_text, v.english_text,
               v.figurative_detection_deliberation,
               f.final_simile, f.final_metaphor, f.final_personification,
               f.final_idiom, f.final_hyperbole, f.final_metonymy, f.final_other,
               f.figurative_text, f.figurative_text_in_hebrew,
               f.target, f.vehicle, f.ground, f.posture,
               f.explanation, f.speaker, f.purpose, f.confidence,
               f.tagging_analysis_deliberation, f.model_used
        FROM figurative_language f
        JOIN verses v ON f.verse_id = v.id
        WHERE {' AND '.join(where)}
        ORDER BY v.book, v.chapter, v.verse, f.id
    """
    cur = conn.cursor()
    cur.execute(sql, params)

    results = []
    for row in cur.fetchall():
        field_val = json.loads(row[field]) if row[field] else None
        hits = matched_terms(field_val, term_regexes)
        if not hits:
            continue
        if is_skip_only(field_val, hits):
            continue
        results.append((row, hits))
    return results


def fetch_hebrew_crosscheck(conn, book, already_fig_ids):
    """Figurative verses whose Hebrew text contains a wilderness root but whose
    English target tag was NOT caught by the synonym search."""
    where = ["1=1"]
    params = []
    if book:
        where.append("v.book = ?")
        params.append(book)
    heb_clauses = []
    for root in HEBREW_ROOTS:
        heb_clauses.append("v.hebrew_text_stripped LIKE ?")
        params.append(f"%{root}%")
    where.append("(" + " OR ".join(heb_clauses) + ")")

    sql = f"""
        SELECT f.id AS fig_id, v.reference, v.book, v.chapter, v.verse,
               v.hebrew_text, v.english_text, v.hebrew_text_stripped,
               v.figurative_detection_deliberation,
               f.final_simile, f.final_metaphor, f.final_personification,
               f.final_idiom, f.final_hyperbole, f.final_metonymy, f.final_other,
               f.figurative_text, f.figurative_text_in_hebrew,
               f.target, f.vehicle, f.ground, f.posture,
               f.explanation, f.speaker, f.purpose, f.confidence,
               f.tagging_analysis_deliberation, f.model_used
        FROM figurative_language f
        JOIN verses v ON f.verse_id = v.id
        WHERE {' AND '.join(where)}
        ORDER BY v.book, v.chapter, v.verse, f.id
    """
    cur = conn.cursor()
    cur.execute(sql, params)

    results = []
    for row in cur.fetchall():
        if row["fig_id"] in already_fig_ids:
            continue
        stripped = row["hebrew_text_stripped"] or ""
        roots_found = [lbl for rt, lbl in HEBREW_ROOTS.items() if rt in stripped]
        if not roots_found:
            continue
        results.append((row, roots_found))
    return results


def fmt_tag(value):
    if not value:
        return "_(none)_"
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return value
    if isinstance(value, list):
        return " → ".join(str(v) for v in value)
    return str(value)


def render_instance(md, row, badge):
    md.append(f"#### {row['reference']}  —  {badge}")
    md.append("")
    if row["speaker"]:
        md.append(f"- **Speaker:** {row['speaker']}")
    if row["purpose"]:
        md.append(f"- **Purpose:** {row['purpose']}")
    md.append("")
    md.append("**Hebrew (full verse):**")
    md.append("")
    md.append(f"> {row['hebrew_text'] or '_(missing)_'}")
    md.append("")
    md.append("**English (full verse):**")
    md.append("")
    md.append(f"> {row['english_text'] or '_(missing)_'}")
    md.append("")
    md.append(f"**Figurative phrase:** {row['figurative_text'] or '_(n/a)_'}")
    if row["figurative_text_in_hebrew"]:
        md.append("")
        md.append(f"**Figurative phrase (Hebrew):** {row['figurative_text_in_hebrew']}")
    md.append("")
    md.append(f"- **Target:** {fmt_tag(row['target'])}")
    md.append(f"- **Vehicle:** {fmt_tag(row['vehicle'])}")
    md.append(f"- **Ground:** {fmt_tag(row['ground'])}")
    md.append(f"- **Posture:** {fmt_tag(row['posture'])}")
    md.append("")
    md.append("---")
    md.append("")


def group_by_book(rows):
    grouped = {}
    for item in rows:
        grouped.setdefault(item[0]["book"], []).append(item)
    return grouped


def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Figurative-language target search with full quotations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--field", choices=["target", "vehicle"], default="target",
                        help="Which hierarchical tag to match synonyms against. "
                             "'target' = the thing being described; 'vehicle' = "
                             "the source-domain image (e.g. wilderness used to "
                             "describe something else). Default: target.")
    parser.add_argument("--book", type=str, default=None,
                        help="Limit to one book (e.g. Psalms). Default: all books.")
    parser.add_argument("--terms", nargs="+", default=None,
                        help="Override the synonym list entirely.")
    parser.add_argument("--broad", action="store_true",
                        help="Add broad terms (barren, desolate, wild, drought).")
    parser.add_argument("--maximal", action="store_true",
                        help="Maximal over-inclusive net (core + broad + waste/"
                             "ruin/dry/thirst/empty/chaos/salt/sand/... ). "
                             "Intended for downstream LLM filtering.")
    parser.add_argument("--hebrew-crosscheck", action="store_true",
                        help="Add a lower-precision Hebrew-root section: figurative "
                             "verses containing מדבר/ישימון/ערבה/ציה whose English "
                             "target tag did NOT trigger the synonym search.")
    parser.add_argument("--concept", type=str, default="wilderness",
                        help="Label for the report header / default filename.")
    parser.add_argument("--output", type=str, default=None,
                        help="Output .md path. Default: output/figurative_search_<concept>.md")
    args = parser.parse_args()

    if args.terms:
        terms = [t.lower() for t in args.terms]
    else:
        terms = list(CORE_TERMS)
        if args.broad or args.maximal:
            terms += BROAD_TERMS
        if args.maximal:
            terms += MAXIMAL_EXTRA
        # dedupe, preserve order
        terms = list(dict.fromkeys(terms))

    db_path = FIGURATIVE_DB_PATH
    if not db_path.exists():
        print(f"Error: figurative database not found at {db_path}", file=sys.stderr)
        return 1

    field = args.field
    field_title = field.title()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        field_rows = fetch_field_matches(conn, terms, args.book, field)
        seen_ids = {r[0]["fig_id"] for r in field_rows}
        if args.hebrew_crosscheck:
            heb_rows = fetch_hebrew_crosscheck(conn, args.book, seen_ids)
        else:
            heb_rows = []
    finally:
        conn.close()

    concept_slug = args.concept.lower().replace(" ", "_")
    out_path = Path(args.output) if args.output else Path(
        f"output/figurative_search_{concept_slug}_{field}.md"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    md = []
    md.append(f"# Figurative Language Search — {field_title}: {args.concept.title()}")
    md.append("")
    md.append(f"**Database:** `{db_path}`  ")
    scope = args.book if args.book else "All books (Tanakh)"
    md.append(f"**Scope:** {scope}  ")
    md.append(f"**Matched field:** `{field}`  ")
    md.append(f"**Synonyms searched ({field} field, whole-word):** {', '.join(terms)}  ")
    md.append(f"**{field_title} matches:** {len(field_rows)}  ")
    if args.hebrew_crosscheck:
        md.append(f"**Hebrew-root cross-check (extra, not {field}-tagged):** {len(heb_rows)}  ")
    md.append("")
    note = (f"> Matching is whole-word on the English hierarchical *{field}* tag. "
            "`desert` is restricted to `desert`/`deserts` (never desertion/"
            "deserter). Idiomatic `just deserts` is excluded.")
    if args.maximal:
        note += (" **Maximal mode: this net is deliberately over-inclusive.** "
                 "Many entries (e.g. salt-of-the-covenant, empty words, sand of "
                 "the sea, thirst for God) are NOT about wilderness terrain and "
                 "are expected to be removed by a downstream LLM filtering pass. "
                 "Each instance includes the complete verse (Hebrew + English) "
                 "so the filter has full context.")
    if args.hebrew_crosscheck:
        roots_str = " / ".join(HEBREW_ROOTS.keys())
        note += (" Part 2 lists figurative verses whose Hebrew text contains a "
                 f"wilderness root ({roots_str}) but whose English {field} tag "
                 "did *not* trigger the synonym search — lower precision, "
                 "review by hand.")
    md.append(note)
    md.append("")
    md.append("---")
    md.append("")

    md.append(f"## Part 1 — {field_title}-tagged {args.concept} instances")
    md.append("")
    if not field_rows:
        md.append("_No instances found._")
        md.append("")
    else:
        for book, items in group_by_book(field_rows).items():
            md.append(f"## {book}  ({len(items)})")
            md.append("")
            for row, hits in items:
                badge = f"{field} hits: " + ", ".join(hits)
                render_instance(md, row, badge)

    if args.hebrew_crosscheck:
        md.append(f"## Part 2 — Hebrew-root cross-check "
                  f"(figurative verses with a wilderness root, {field} NOT tagged {args.concept})")
        md.append("")
        if not heb_rows:
            md.append("_No additional Hebrew-root instances found._")
            md.append("")
        else:
            for book, items in group_by_book(heb_rows).items():
                md.append(f"## {book}  ({len(items)})")
                md.append("")
                for row, roots in items:
                    badge = "Hebrew root: " + ", ".join(roots)
                    render_instance(md, row, badge)

    out_path.write_text("\n".join(md), encoding="utf-8")

    print(f"Search concept     : {args.concept}")
    print(f"Matched field      : {field}")
    print(f"Scope              : {scope}")
    print(f"Synonyms           : {', '.join(terms)}")
    print(f"{field_title} matches{' ' * max(0, 5 - len(field_title))}: {len(field_rows)}")
    if args.hebrew_crosscheck:
        print(f"Hebrew cross-check : {len(heb_rows)}")
    print(f"Report written to  : {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
