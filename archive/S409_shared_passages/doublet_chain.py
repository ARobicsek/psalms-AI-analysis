"""Prototype: verse-boundary-free shared-passage detector on LEMMA streams.
Matching lemmas between a psalm and another chapter are chained in order with gaps
<= MAX_GAP on both sides; a chain with >= MIN_MATCH counted matches is a shared passage.
Heading-formula lemmas never count. Candidates come from shared rare lemma bigrams."""
import sys, json, sqlite3, re
from collections import defaultdict

MAX_GAP, MIN_MATCH, RARE_BIGRAM_DF = 3, 5, 40
NIKUD = re.compile(r'[\u0591-\u05C7]')
HEADING = set("למנצח מנצח מזמור דוד שיר בן קרח משכיל מכתם אסף שלמה הימן איתן ידותון נגינה שמינית גתית תפלה סלה הללויה".split())

con = sqlite3.connect(r"C:\dev\personal\psalms\database\tanakh.db")
rows = con.execute("select book_name, chapter, verse, position, lemma, word_consonantal from concordance "
                   "order by book_name, chapter, verse, position").fetchall()
units = defaultdict(list)  # (book, ch) -> [(verse, lemma)]
for b, ch, v, pos, lem, cons in rows:
    l = NIKUD.sub('', (lem or cons or '')).strip()
    if l:
        units[(b, ch)].append((v, l))

bdf = defaultdict(set)
for u, toks in units.items():
    for i in range(len(toks) - 1):
        bdf[(toks[i][1], toks[i + 1][1])].add(u)

def chains(a, b):
    """Longest gap-bounded in-order match chains between token lists a, b."""
    pos_b = defaultdict(list)
    for j, (_, l) in enumerate(b):
        pos_b[l].append(j)
    pts = sorted((i, j) for i, (_, l) in enumerate(a) for j in pos_b.get(l, ()))
    best = {}  # (i,j) -> (score, prev)
    for i, j in pts:
        cnt = 0 if a[i][1] in HEADING else 1
        s, prev = cnt, None
        for di in range(1, MAX_GAP + 2):
            for dj in range(1, MAX_GAP + 2):
                p = best.get((i - di, j - dj))
                if p and p[0] + cnt > s:
                    s, prev = p[0] + cnt, (i - di, j - dj)
        best[(i, j)] = (s, prev)
    # extract maximal non-overlapping chains, highest first
    used_i, out = set(), []
    for (i, j), (s, _) in sorted(best.items(), key=lambda kv: -kv[1][0]):
        if s < MIN_MATCH or i in used_i:
            continue
        path, node = [], (i, j)
        while node:
            path.append(node); node = best[node][1]
        path.reverse()
        if any(p[0] in used_i for p in path):
            continue
        used_i.update(p[0] for p in path)
        out.append((s, path))
    return out

res = []
for ps in range(1, 151):
    a = units[("Psalms", ps)]
    cands = set()
    for i in range(len(a) - 1):
        us = bdf[(a[i][1], a[i + 1][1])]
        if len(us) <= RARE_BIGRAM_DF:
            cands |= us
    for u in cands:
        if u == ("Psalms", ps) or (u[0] == "Psalms" and u[1] < ps):
            continue
        for s, path in chains(a, units[u]):
            va = sorted({a[i][0] for i, _ in path}); vb = sorted({units[u][j][0] for _, j in path})
            res.append({"psalm": ps, "book": u[0], "chapter": u[1], "matched": s,
                        "ps_verses": f"{va[0]}-{va[-1]}" if len(va) > 1 else str(va[0]),
                        "other_verses": f"{vb[0]}-{vb[-1]}" if len(vb) > 1 else str(vb[0]),
                        "text": " ".join(a[i][1] for i, _ in path)})
json.dump(res, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(res), "shared passages")
