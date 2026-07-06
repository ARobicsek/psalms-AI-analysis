"""
Computed Distributional Facts — deterministic pre-pass for the Synthesis Scholar

Session 362: the synthesis-discovery sidecar's "distributional sweep" (step 3 of
the v2 prompt) asks Opus to tabulate word occurrences in its head — the one task
where an LLM is weakest and where the concordance database is exact. This module
does that counting deterministically (pure SQL, zero API cost) and emits a
compact markdown block that is spliced into the sidecar's inputs as
"COMPUTED DISTRIBUTIONAL FACTS".

What it computes for a psalm (all at the CONSONANTAL normalization level, on
exact token strings — prefixed/inflected variants of the same lemma count as
different forms; the header of the emitted block states this limitation so the
sidecar never converts "unique form" into "lexical hapax" without checking):

  1. FORM RARITY — every distinct consonantal form in the psalm with its count
     here / in Psalms / in Tanakh; forms occurring <= RARE_MAX times in the
     whole Tanakh are listed with the references of ALL other occurrences
     (these are the "only here and one other place" leads).
  2. REPEATED FORMS — forms occurring 2+ times inside the psalm, with the
     verses they land on (keyword / inclusio / cluster candidates).
  3. FIRST/LAST VERSE SHARED FORMS — inclusio candidates computed, not felt.
  4. RARE ADJACENT PAIRS — consecutive-word pairs (within a verse) occurring
     <= BIGRAM_RARE_MAX times in all of Tanakh, with the other references.
  5. DIVINE-NAME DISTRIBUTION — verse-by-verse tallies of YHWH vs Elohim
     forms (Elohistic-Psalter texture, conspicuous absences).

Degrades gracefully: if the database file is missing or its concordance table
is empty (the cloud clone ships a stub), returns "" and the caller skips the
block.

Usage:
    from src.concordance.distributional_facts import compute_distributional_facts
    block = compute_distributional_facts(60)   # "" if no data available
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Tunables — chosen to keep the emitted block compact (~3-6K chars) so it
# informs the sidecar without bloating two Opus calls.
RARE_MAX = 5            # form counts <= this in Tanakh get their refs listed
BIGRAM_RARE_MAX = 3     # adjacent pairs <= this in Tanakh get listed
MIN_FORM_LEN = 3        # skip 1-2 consonant tokens (particles, prefixes)
MAX_RARE_ROWS = 20      # cap each table so a long psalm can't flood the block
MAX_REPEAT_ROWS = 20
MAX_BIGRAM_ROWS = 15

_DEFAULT_DB_CANDIDATES = (
    Path("database/tanakh.db"),
    Path("data/tanakh.db"),
)


def _find_database(db_path: Optional[Path] = None) -> Optional[Path]:
    """Return the first tanakh.db that exists and has concordance rows."""
    candidates = [Path(db_path)] if db_path else [
        Path(__file__).resolve().parents[2] / c for c in _DEFAULT_DB_CANDIDATES
    ]
    # Also honor CWD-relative paths (production scripts run from repo root).
    if not db_path:
        candidates += list(_DEFAULT_DB_CANDIDATES)
    for cand in candidates:
        if not cand.exists():
            continue
        try:
            conn = sqlite3.connect(f"file:{cand}?mode=ro", uri=True)
            try:
                n = conn.execute("SELECT COUNT(*) FROM concordance").fetchone()[0]
            finally:
                conn.close()
            if n > 0:
                return cand
        except sqlite3.Error:
            continue
    return None


def _verse_list(verses: List[int]) -> str:
    """Render a sorted verse list compactly: [3, 4, 5, 12] -> 'vv. 3-5, 12'."""
    vs = sorted(set(verses))
    if not vs:
        return ""
    runs: List[Tuple[int, int]] = []
    start = prev = vs[0]
    for v in vs[1:]:
        if v == prev + 1:
            prev = v
            continue
        runs.append((start, prev))
        start = prev = v
    runs.append((start, prev))
    parts = [f"{a}" if a == b else f"{a}-{b}" for a, b in runs]
    prefix = "v. " if len(vs) == 1 else "vv. "
    return prefix + ", ".join(parts)


def compute_distributional_facts(
    psalm_number: int,
    db_path: Optional[Path] = None,
) -> str:
    """Compute the distributional-facts markdown block for one psalm.

    Returns "" when no populated database is available — callers treat that
    as "skip the block" (the sidecar prompt then omits the section).
    """
    found = _find_database(db_path)
    if found is None:
        return ""

    conn = sqlite3.connect(f"file:{found}?mode=ro", uri=True)
    try:
        return _compute(conn, psalm_number)
    finally:
        conn.close()


def _compute(conn: sqlite3.Connection, psalm_number: int) -> str:
    cur = conn.cursor()

    # All tokens of this psalm, in verse/position order.
    rows = cur.execute(
        """
        SELECT verse, position, word_consonantal
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = ?
        ORDER BY verse, position
        """,
        (psalm_number,),
    ).fetchall()
    if not rows:
        return ""

    # Ketiv/qere sites are stored as two adjacent tokens: the ketiv in
    # parentheses, the qere in square brackets (2,138 such tokens DB-wide).
    # Raw, the punctuation makes every such token spuriously "rare" and
    # fabricates a ketiv→qere adjacent pair. We read the qere: drop the
    # ketiv token, unwrap the qere's brackets.
    tokens: List[Tuple[int, int, str]] = []
    for v, p, w in rows:
        if not w:
            continue
        if w.startswith("(") and w.endswith(")"):
            continue
        if w.startswith("[") and w.endswith("]"):
            w = w[1:-1]
        tokens.append((v, p, w))
    verses_here = sorted({v for v, _, _ in tokens})
    first_verse, last_verse = verses_here[0], verses_here[-1]

    # Per-form occurrences within the psalm.
    here: Dict[str, List[int]] = defaultdict(list)
    for v, _, w in tokens:
        here[w].append(v)

    forms = [w for w in here if len(w) >= MIN_FORM_LEN]

    # Corpus counts per form (one query per distinct form; indexed column).
    # Each form also matches its bracketed-qere spelling elsewhere in the DB,
    # so a form that is someone else's qere still counts those occurrences.
    corpus_counts: Dict[str, Tuple[int, int]] = {}
    for w in forms:
        n_tanakh, n_psalms = cur.execute(
            """
            SELECT COUNT(*),
                   SUM(CASE WHEN book_name = 'Psalms' THEN 1 ELSE 0 END)
            FROM concordance WHERE word_consonantal IN (?, ?)
            """,
            (w, f"[{w}]"),
        ).fetchone()
        corpus_counts[w] = (n_tanakh or 0, n_psalms or 0)

    lines: List[str] = []

    # --- 1. Rare forms -------------------------------------------------------
    rare = sorted(
        (w for w in forms if corpus_counts[w][0] <= RARE_MAX),
        key=lambda w: (corpus_counts[w][0], w),
    )[:MAX_RARE_ROWS]
    if rare:
        lines.append("**Rare forms** (exact consonantal string; count in all Tanakh ≤ "
                     f"{RARE_MAX}; every other occurrence listed):")
        for w in rare:
            n_tanakh, _ = corpus_counts[w]
            others = cur.execute(
                """
                SELECT book_name, chapter, verse FROM concordance
                WHERE word_consonantal IN (?, ?)
                  AND NOT (book_name = 'Psalms' AND chapter = ?)
                ORDER BY book_name, chapter, verse
                """,
                (w, f"[{w}]", psalm_number),
            ).fetchall()
            refs = "; ".join(f"{b} {c}:{v}" for b, c, v in others) or "NOWHERE ELSE"
            label = ("unique to this psalm in all Tanakh"
                     if n_tanakh == len(here[w]) else f"elsewhere: {refs}")
            lines.append(f"- {w} ({_verse_list(here[w])}; {n_tanakh}x in Tanakh) — {label}")
        lines.append("")

    # --- 2. Repeated forms inside the psalm ----------------------------------
    repeated = sorted(
        (w for w in forms if len(here[w]) >= 2),
        key=lambda w: (-len(here[w]), min(here[w])),
    )[:MAX_REPEAT_ROWS]
    if repeated:
        lines.append("**Repeated forms within the psalm** (keyword / cluster / "
                     "inclusio candidates; count here, then in Psalms / Tanakh):")
        for w in repeated:
            n_tanakh, n_psalms = corpus_counts[w]
            lines.append(
                f"- {w} — {len(here[w])}x here ({_verse_list(here[w])}); "
                f"{n_psalms}x in Psalms, {n_tanakh}x in Tanakh"
            )
        lines.append("")

    # --- 3. First/last verse shared forms (inclusio candidates) --------------
    if first_verse != last_verse:
        first_set = {w for v, _, w in tokens if v == first_verse and len(w) >= MIN_FORM_LEN}
        last_set = {w for v, _, w in tokens if v == last_verse and len(w) >= MIN_FORM_LEN}
        shared = sorted(first_set & last_set)
        if shared:
            lines.append(
                f"**Forms shared by the first and last verse** (vv. {first_verse} and "
                f"{last_verse}; computed inclusio candidates): " + ", ".join(shared)
            )
            lines.append("")

    # --- 4. Rare adjacent pairs ----------------------------------------------
    pair_rows: List[str] = []
    seen_pairs = set()
    by_verse: Dict[int, List[Tuple[int, str]]] = defaultdict(list)
    for v, p, w in tokens:
        by_verse[v].append((p, w))
    for v in verses_here:
        seq = [w for _, w in sorted(by_verse[v])]
        for a, b in zip(seq, seq[1:]):
            if len(a) < MIN_FORM_LEN or len(b) < MIN_FORM_LEN:
                continue
            if (a, b) in seen_pairs:
                continue
            seen_pairs.add((a, b))
            hits = cur.execute(
                """
                SELECT c1.book_name, c1.chapter, c1.verse
                FROM concordance c1 JOIN concordance c2
                  ON  c2.book_name = c1.book_name
                  AND c2.chapter   = c1.chapter
                  AND c2.verse     = c1.verse
                  AND c2.position  = c1.position + 1
                WHERE c1.word_consonantal = ? AND c2.word_consonantal = ?
                ORDER BY c1.book_name, c1.chapter, c1.verse
                """,
                (a, b),
            ).fetchall()
            if 0 < len(hits) <= BIGRAM_RARE_MAX:
                others = [
                    f"{bk} {ch}:{vs}" for bk, ch, vs in hits
                    if not (bk == "Psalms" and ch == psalm_number)
                ]
                if others:
                    where = "; ".join(others)
                elif len(hits) > 1:
                    where = "NOWHERE ELSE (all occurrences within this psalm)"
                else:
                    where = "NOWHERE ELSE"
                pair_rows.append(
                    f"- {a} {b} (v. {v}; {len(hits)}x in Tanakh) — elsewhere: {where}"
                )
            if len(pair_rows) >= MAX_BIGRAM_ROWS:
                break
        if len(pair_rows) >= MAX_BIGRAM_ROWS:
            break
    if pair_rows:
        lines.append("**Rare adjacent word-pairs** (consecutive tokens in a verse; "
                     f"pair count in all Tanakh ≤ {BIGRAM_RARE_MAX}):")
        lines.extend(pair_rows)
        lines.append("")

    # --- 5. Divine-name distribution ------------------------------------------
    yhwh_vs = [v for v, _, w in tokens if w.endswith("יהוה")]
    elohim_vs = [v for v, _, w in tokens if "אלהים" in w or "אלקים" in w]
    name_bits = []
    name_bits.append(f"YHWH forms: {len(yhwh_vs)}x"
                     + (f" ({_verse_list(yhwh_vs)})" if yhwh_vs else ""))
    name_bits.append(f"Elohim forms: {len(elohim_vs)}x"
                     + (f" ({_verse_list(elohim_vs)})" if elohim_vs else ""))
    lines.append("**Divine-name tally** (prefix-tolerant string match): "
                 + "; ".join(name_bits))
    lines.append("")

    if not any(l for l in lines if l):
        return ""

    header = (
        "The counts below were computed by SQL over the full-Tanakh concordance "
        "at the CONSONANTAL level — they are exact for what they measure, and "
        "what they measure is the exact consonantal string: prefixed or "
        "inflected variants of the same lemma count as DIFFERENT forms. So a "
        "form marked 'nowhere else' is a unique FORM, not necessarily a lexical "
        "hapax — verify against the lexicon data before claiming more. Treat "
        "these tables as pre-built distributional evidence for your sweep: "
        "trust these counts over your own memory, expect most rows to be "
        "boring, and discard freely. The gold, when present, is usually a rare "
        "form or pair in a structurally loaded position, a lopsided repetition, "
        "or a conspicuous absence.\n"
    )
    return header + "\n" + "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    import sys

    # Windows consoles default to cp1252, which can't print Hebrew or '≤'.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    block = compute_distributional_facts(n)
    print(block if block else f"[no populated tanakh.db found — nothing computed for Psalm {n}]")
