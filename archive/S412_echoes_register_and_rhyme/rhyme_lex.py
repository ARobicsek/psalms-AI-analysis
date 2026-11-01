import random, sys
sys.path.insert(0, r"C:\Users\ariro\AppData\Local\Temp\claude\c--dev-personal-psalms\50cada51-6538-4093-af8c-46ce314b4668\scratchpad")
import rhyme_scan as R, sqlite3
from collections import Counter
MORPH = {"i-מ", "a-י", "a-מ", "o-ת", "a-יו", "e-מ", "a-ת", "e-י"}
def lex(words):
    cl = R.clusters(words)
    # same word repeated (אל/האל/ואל) is repetition, not rhyme
    return {k: v for k, v in cl.items() if k not in MORPH and len({w.lstrip("והבלכמ") for w in v}) >= 3}
c = sqlite3.connect(R.DB)
for book in ["Psalms", None]:
    q = "select book_name, chapter, verse, hebrew from verses" + (" where book_name='Psalms'" if book else "")
    rows = c.execute(q).fetchall()
    vs = [(b, ch, v, R.verse_words(h)) for b, ch, v, h in rows]
    hits = [(b, ch, v, lex(ws)) for b, ch, v, ws in vs]
    hits = [h for h in hits if h[3]]
    allw = [w for *_, ws in vs for w in ws]
    base = []
    for seed in range(10 if book else 3):
        random.Random(seed).shuffle(allw); pos = n = 0
        for *_, ws in vs:
            n += bool(lex(allw[pos:pos + len(ws)])); pos += len(ws)
        base.append(n)
    print(book or "Whole Bible", "verses", len(vs), "lexical 3+ clusters", len(hits), "shuffle mean", sum(base)/len(base), base)
    if book:
        for b, ch, v, cl in hits: print(f"  {ch}:{v}", {k: sorted(s) for k, s in cl.items()})
