"""Run the production doublet detector (RelatedPsalmsLibrarian._find_shared_verse_pairs,
current thresholds) of every psalm against every psalm and every chapter of the Tanakh.
Writes a JSON of every (psalm, book, chapter) unit with any verse pair >= 0.4 Jaccard."""
import sys, json, itertools
from collections import defaultdict
sys.path.insert(0, r"C:\dev\personal\psalms")
from src.agents import related_psalms_librarian as rpl
from src.agents.related_psalms_librarian import RelatedPsalmsLibrarian

lib = RelatedPsalmsLibrarian(connections_file="nonexistent.json")
c = lib.db.conn.cursor()
c.execute("select book_name, chapter, verse, hebrew from verses")
units = defaultdict(list)  # (book, chapter) -> [{"verse","hebrew"}]
keys = {}
for b, ch, v, h in c.fetchall():
    units[(b, ch)].append({"verse": v, "hebrew": h})
    keys[(b, ch, v)] = set(lib._tokenize_verse(h)[1])

df = defaultdict(int)
for k in keys.values():
    for t in k: df[t] += 1
index = defaultdict(set)
for vid, k in keys.items():
    for t in k:
        if df[t] <= 3000:
            index[t].add(vid)

cand = defaultdict(float)  # (psalm, book, ch) -> best raw sim
for (b, ch, v), ka in keys.items():
    if b != "Psalms" or len(ka) < rpl.MIN_VERSE_TOKENS:
        continue
    counts = defaultdict(int)
    for t in ka:
        for vid in index.get(t, ()):
            counts[vid] += 1
    for vid, n in counts.items():
        if n < 2 or vid[:2] == (b, ch):
            continue
        kb = keys[vid]
        if len(kb) < rpl.MIN_VERSE_TOKENS:
            continue
        sim = len(ka & kb) / len(ka | kb)
        if sim >= 0.4:
            u = (ch, vid[0], vid[1])
            cand[u] = max(cand[u], sim)

out = []
for (ps, b, ch), best in cand.items():
    if b == "Psalms" and ch < ps:
        continue  # symmetric; keep each psalm pair once
    pairs = lib._find_shared_verse_pairs(units[("Psalms", ps)], units[(b, ch)])
    flagged = len(pairs) >= rpl.DOUBLET_MIN_VERSES or (len(pairs) == 1 and pairs[0][2] >= rpl.SINGLE_VERSE_SIMILARITY)
    kind = "DOUBLET" if len(pairs) >= rpl.DOUBLET_MIN_VERSES else ("SINGLE" if flagged else "-")
    out.append({"psalm": ps, "book": b, "chapter": ch, "best_raw": round(best, 3), "kind": kind,
                "pairs": [(a, bb, round(s, 2)) for a, bb, s in pairs]})
out.sort(key=lambda r: (r["psalm"], r["book"], r["chapter"]))
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(out), "units;", sum(r["kind"] == "DOUBLET" for r in out), "doublets;", sum(r["kind"] == "SINGLE" for r in out), "single")
