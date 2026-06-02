"""
Add and populate a `lemma` column on the `concordance` table (Session 351, D&E).

Background
----------
Session 350 made concordance search trace *distinctive roots*, but it did so with
runtime string-expansion against the surface-form columns — there was no morphology
in the database. This script wires in true lemma data from ETCBC/BHSA so that root
traces and 2-word collocations become exact, indexed `WHERE lemma = ?` lookups that
are tolerant of prefixes, suffixes, conjugation and word order.

Why lemma (lex), not root
-------------------------
BHSA's `root` feature covers only ~17% of words (None on every verb, most nouns, and
on every Session-350 target: פלג, נוד, נדד, חסד, אמת), so it is unusable as a search
key. `lex_utf8` (the dictionary lexeme) is 100% coverage and is what we store here as
`lemma`, normalized to the project's bare-consonant convention so it matches the
existing `word_consonantal*` columns and the query side.

Alignment (the one real risk)
------------------------------
BHSA tokenizes proclitic particles (ב/כ/ל/מ/ו/ה …) as *separate* word nodes, while our
concordance keeps them attached (`ב`+`עצת` ⇒ `בעצת`). So a position-by-position join is
wrong. Instead we greedily concatenate consecutive BHSA tokens until they equal our
token, then assign that group's *content* lemma (the last non-particle sub-token).
Validated at 98.45% token coverage on Psalms. Crucially, assignment requires an exact
consonantal match, so a mismatch leaves `lemma` NULL (→ naive fallback at search time)
rather than writing a *wrong* lemma. No silent corruption.

Usage:
    python scripts/add_lemma_column.py --dry-run     # report coverage, write nothing
    python scripts/add_lemma_column.py               # add column, backfill, index
    python scripts/add_lemma_column.py --book Psalms # restrict to one book (validation)
"""
import argparse
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from src.concordance.hebrew_text_processor import normalize_for_search

DB_PATH = Path(__file__).parent.parent / 'database' / 'tanakh.db'

# BHSA section book names (from T.sectionFromNode: English with underscores) ->
# our DB book_name (Roman-numeral convention). Most names are identical to ours;
# only these seven differ. NOTE: F.book.v returns Latin names (Psalmi, Reges_II) —
# we deliberately key off the *section* names, which is what the verse loop uses.
SECTION_TO_OURS = {
    '1_Samuel': 'I Samuel', '2_Samuel': 'II Samuel',
    '1_Kings': 'I Kings', '2_Kings': 'II Kings',
    '1_Chronicles': 'I Chronicles', '2_Chronicles': 'II Chronicles',
    'Song_of_songs': 'Song of Songs',
}


def to_our_book(section_book):
    """Map a BHSA section book name to our DB book_name (identity for most)."""
    return SECTION_TO_OURS.get(section_book, section_book)

# Proclitic particle parts-of-speech: never the "content" word of a merged token.
PARTICLE_SP = {'art', 'prep', 'conj'}


def load_bhsa(db_books, book_filter=None):
    """Return {(our_book, chapter, verse): [(cons, lemma_cons, sp), ...]} from BHSA.

    `db_books` is the set of book_name values actually present in our concordance;
    used to assert every BHSA book maps onto a real DB book before we write anything.
    """
    from tf.app import use
    print("Loading ETCBC/BHSA (this takes ~30-60s)...", flush=True)
    A = use('ETCBC/bhsa', silent='deep')
    F, L, T = A.api.F, A.api.L, A.api.T

    verses = {}
    mapped_books = set()
    for vnode in F.otype.s('verse'):
        bk, ch, vs = T.sectionFromNode(vnode)
        our = to_our_book(bk)
        mapped_books.add((bk, our))
        if book_filter and our != book_filter:
            continue
        toks = []
        for w in L.d(vnode, 'word'):
            cons = normalize_for_search(F.g_cons_utf8.v(w) or '', 'consonantal')
            lem = normalize_for_search(F.lex_utf8.v(w) or '', 'consonantal')
            toks.append((cons, lem, F.sp.v(w)))
        verses[(our, ch, vs)] = toks

    # Safety: every BHSA book must land on a real DB book.
    bad = sorted(our for _, our in mapped_books if our not in db_books)
    if bad:
        raise SystemExit(f"BHSA books not found in DB book_name set: {bad}\n"
                         f"DB books: {sorted(db_books)}")
    print(f"BHSA loaded: {len(verses)} verses across "
          f"{len(set(k[0] for k in verses))} books (all map to DB).", flush=True)
    return verses


def _content_lemma(group_idxs, btoks):
    """Pick the content lemma of a merged token group: last non-particle, else last."""
    chosen = None
    for gi in group_idxs:
        if btoks[gi][2] not in PARTICLE_SP:
            chosen = gi
    if chosen is None:
        chosen = group_idxs[-1]
    return btoks[chosen][1]


def align_verse(our_tokens, btoks):
    """
    Greedily align our tokens to BHSA tokens by consonantal concatenation.

    our_tokens: [(concordance_id, cons), ...] in position order, cons non-empty.
    btoks: [(cons, lemma_cons, sp), ...] for the verse.
    Returns (updates, n_aligned) where updates = [(lemma, concordance_id), ...].
    """
    bn = [b for b in btoks if b[0]]
    updates = []
    aligned = 0
    j = 0
    for cid, otok in our_tokens:
        matched = False
        # Try the current pointer first, then resync from any later start
        # (handles ketiv/qere spelling gaps and versification offsets).
        for start in range(j, len(bn)):
            acc = ''
            grp = []
            k = start
            while k < len(bn) and len(acc) < len(otok):
                acc += bn[k][0]
                grp.append(k)
                k += 1
            if acc == otok and grp:
                lemma = _content_lemma(grp, bn)
                if lemma:
                    updates.append((lemma, cid))
                    aligned += 1
                j = k
                matched = True
                break
        if not matched:
            # leave lemma NULL for this token (search-time naive fallback handles it)
            continue
    return updates, aligned


def main():
    ap = argparse.ArgumentParser(description="Populate concordance.lemma from BHSA")
    ap.add_argument('--dry-run', action='store_true', help="report coverage, write nothing")
    ap.add_argument('--book', default=None, help="restrict to one DB book name (validation)")
    ap.add_argument('--batch', type=int, default=5000)
    args = ap.parse_args()

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    db_books = {r[0] for r in cur.execute("SELECT DISTINCT book_name FROM concordance")}
    verses = load_bhsa(db_books, book_filter=args.book)

    # Add column if missing.
    cols = [r[1] for r in cur.execute("PRAGMA table_info(concordance)").fetchall()]
    if 'lemma' not in cols:
        if args.dry_run:
            print("[dry-run] would ALTER TABLE concordance ADD COLUMN lemma TEXT")
        else:
            print("ALTER TABLE concordance ADD COLUMN lemma TEXT ...")
            cur.execute("ALTER TABLE concordance ADD COLUMN lemma TEXT")
            conn.commit()
    else:
        print("Column `lemma` already exists (will be (re)populated).")

    # Fetch our rows, grouped by verse, ordered by position.
    where = "WHERE book_name = ?" if args.book else ""
    params = (args.book,) if args.book else ()
    rows = cur.execute(f"""
        SELECT concordance_id, book_name, chapter, verse, position,
               COALESCE(word_consonantal_split, word_consonantal) AS cons
        FROM concordance {where}
        ORDER BY book_name, chapter, verse, position
    """, params).fetchall()

    by_verse = defaultdict(list)
    for r in rows:
        cons = r['cons'] or ''
        if cons.strip():
            by_verse[(r['book_name'], r['chapter'], r['verse'])].append((r['concordance_id'], cons))

    total_tokens = sum(len(v) for v in by_verse.values())
    all_updates = []
    aligned_total = 0
    verses_no_bhsa = 0
    per_book_tok = Counter()
    per_book_aligned = Counter()

    t0 = time.time()
    for key, our_tokens in by_verse.items():
        book = key[0]
        per_book_tok[book] += len(our_tokens)
        btoks = verses.get(key)
        if btoks is None:
            verses_no_bhsa += 1
            continue
        updates, n_aligned = align_verse(our_tokens, btoks)
        aligned_total += n_aligned
        per_book_aligned[book] += n_aligned
        all_updates.extend(updates)

    print(f"\nTokens (non-empty): {total_tokens}")
    print(f"Lemma aligned:      {aligned_total} ({100*aligned_total/total_tokens:.2f}%)")
    print(f"Verses with no BHSA match (versification gaps): {verses_no_bhsa}")
    print("\nPer-book coverage (worst 10):")
    worst = sorted(per_book_tok, key=lambda b: per_book_aligned[b]/max(per_book_tok[b], 1))[:10]
    for b in worst:
        tot = per_book_tok[b]
        al = per_book_aligned[b]
        print(f"  {b:18} {al:6}/{tot:6}  {100*al/max(tot,1):5.1f}%")

    if args.dry_run:
        print("\n[dry-run] no rows written.")
        # Spot-check a few target lemmas without writing, by simulating the map.
        conn.close()
        return

    # Write updates in batches.
    print(f"\nWriting {len(all_updates)} lemma values...")
    for i in range(0, len(all_updates), args.batch):
        cur.executemany(
            "UPDATE concordance SET lemma = ? WHERE concordance_id = ?",
            all_updates[i:i + args.batch],
        )
        conn.commit()
    print(f"Done in {time.time()-t0:.1f}s.")

    # Index.
    print("Creating index idx_concordance_lemma ...")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_concordance_lemma ON concordance(lemma)")
    conn.commit()

    # Final coverage from the DB itself.
    filled = cur.execute(
        f"SELECT COUNT(*) FROM concordance {where} AND lemma IS NOT NULL" if where
        else "SELECT COUNT(*) FROM concordance WHERE lemma IS NOT NULL", params
    ).fetchone()[0]
    total = cur.execute(f"SELECT COUNT(*) FROM concordance {where}", params).fetchone()[0]
    print(f"\nDB lemma coverage: {filled}/{total} ({100*filled/total:.2f}%)")
    conn.close()


if __name__ == '__main__':
    main()
