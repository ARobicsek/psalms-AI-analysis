"""Proof of concept: IDF-weighted shared-lemma intertext detection (pure SQL/Python, $0)."""
import sqlite3, math, sys, collections
PS = int(sys.argv[1]) if len(sys.argv) > 1 else 76
c = sqlite3.connect('database/tanakh.db')
STOP = set('אשר כל לא כי על אל את מן ב ל ו ה עם גם הוא היה אמר עשה נתן בוא הלך יהוה אלהים אדני אני אתה הוא היא הם אנחנו זה זאת מה מי אם או פנה סלה יום איש ארץ שמים לב יד עין פה דבר אדם בן עם ראה שמע ידע'.split())
rows = c.execute("select book_name, chapter, verse, lemma from concordance where lemma is not null").fetchall()
verse_lem = collections.defaultdict(set)
for b, ch, v, l in rows:
    verse_lem[(b, ch, v)].add(l)
N = len(verse_lem)
df = collections.Counter()
for s in verse_lem.values():
    df.update(s)
idf = {l: math.log(N / d) for l, d in df.items()}
def content(s):
    return {l for l in s if l not in STOP and df[l] < 1500}
ps_verses = sorted([k for k in verse_lem if k[0] == 'Psalms' and k[1] == PS], key=lambda k: k[2])
# windows of 1 and 2 consecutive psalm verses
windows = [[k] for k in ps_verses] + [[a, b] for a, b in zip(ps_verses, ps_verses[1:])]
index = collections.defaultdict(set)
for k, s in verse_lem.items():
    for l in content(s):
        index[l].add(k)
hits = []
for w in windows:
    L = set().union(*(content(verse_lem[k]) for k in w))
    cand = collections.Counter()
    for l in L:
        for k in index[l]:
            if k[0] == 'Psalms' and k[1] == PS:
                continue
            cand[k] += 1
    for k, n in cand.items():
        if n < 3 and not (n == 2 and len(w) == 1):
            continue
        shared = L & content(verse_lem[k])
        score = sum(idf[l] for l in shared)
        if len(shared) >= 2:
            hits.append((score, tuple(x[2] for x in w), k, sorted(shared, key=lambda l: -idf[l])))
best = {}
for h in hits:
    key = h[2]
    if key not in best or h[0] > best[key][0]:
        best[key] = h
top = sorted(best.values(), key=lambda h: -h[0])[:45]
for score, wv, k, shared in top:
    print(f"{score:5.1f}  Ps{PS}:{'-'.join(map(str, wv)):5}  {k[0]} {k[1]}:{k[2]:<3}  shared: {' '.join(shared)}")
