"""PROTOTYPE size-limiting rules for the reception layer. No model. See S391 doc."""
import json, re, sys
from collections import defaultdict
PS = {int(k): v for k, v in json.load(open('psalms_he_textonly.json')).items()}
FINALS = str.maketrans('ךםןףץ', 'כמנפצ')
DIVINE = {'יהוה', 'ה', 'יי', 'ד', 'השם', 'אלקים', 'אלוקים', 'אלהים', 'אלקים'}
STOP = {'כי', 'אשר', 'את', 'על', 'אל', 'לא', 'כל', 'גם', 'אף', 'עם', 'סלה', 'למנצח', 'מזמור', 'לדוד', 'לאסף', 'שיר', 'בו', 'לו', 'הוא', 'זה', 'אני', 'אתה', 'מי', 'אם', 'עד', 'ולא', 'וכל'}
PROOF_BEFORE = {'שנאמר', 'דכתיב', 'כדכתיב', 'וכתיב', 'שכתוב', 'ככתוב', 'כמש', 'כמשה', 'ההד', 'ואומר', 'שנא', 'כמו', 'וכן', 'דאמר', 'כמאמר', 'שנאמ', 'דכתי', 'כתיב', 'ונאמר', 'וכתוב'}
CUE_AFTER = {'זה', 'זו', 'אלו', 'אלה', 'מהו', 'מאי', 'מלמד', 'כלומר', 'רל', 'כיצד', 'משל', 'כביכול', 'אלא', 'פירוש', 'פי', 'דהיינו', 'היינו', 'רוצה', 'ביאור', 'הכוונה', 'רמז', 'אמר', 'אמרו'}
TIER = {'Talmud': 1, 'Mishnah': 1, 'Tosefta': 1, 'Midrash': 2, 'Second Temple': 2, 'Chasidut': 3, 'Musar': 3, 'Halakhah': 3}

def toks(s):
    s = re.sub(r'[֑-ׇ]', '', s).replace('־', ' ').replace('׀', ' ')
    s = re.sub(r"[\"'׳״]", '', s)
    return [w.translate(FINALS) for w in re.sub(r'[^א-ת ]', ' ', s).split()]
def skel(w):
    w = 'יהוה' if w in DIVINE else w
    return w[0] + re.sub('[וי]', '', w[1:]) if len(w) > 2 else w
def same(a, b):
    a, b = skel(a), skel(b)
    if a == b: return True
    for x, y in ((a, b), (b, a)):
        if len(x) == len(y) + 1 and x[0] in 'והבלמשכ' and x[1:] == y and len(y) >= 2: return True
    return False

def analyse(row, p):
    v = int(row['anchorRef'].split(':')[-1].split('-')[0])
    if not 1 <= v <= len(PS[p]): return None
    vt = toks(PS[p][v - 1]); st = toks(row['he'])
    best = (0, 0, 0)  # length, start in segment, end
    for i in range(len(st)):
        for j in range(len(vt)):
            k = 0
            while i + k < len(st) and j + k < len(vt) and same(st[i + k], vt[j + k]): k += 1
            if k > best[0]: best = (k, i, i + k)
    k, s, e = best
    found = k >= 2 or (k == 1 and len(vt) <= 2)
    content = {skel(w) for w in vt if w not in STOP and len(w) >= 3 and skel(w) != 'יהוה'}
    outside = set()
    for idx, w in enumerate(st):
        if found and s <= idx < e: continue
        for c in content:
            if same(w, c): outside.add(c)
    before = set(st[max(0, s - 3):s]) if found else set()
    after = set(st[e:e + 4]) if found else set()
    proof = bool(before & PROOF_BEFORE); cue = bool(after & CUE_AFTER)
    own = row['index_title'] == 'Midrash Tehillim' and row['ref'].startswith(f'Midrash Tehillim {p}:')
    recur = len(outside)
    reads = own or recur >= 2 or (cue and recur >= 1) or (cue and not proof)
    score = recur * 2 + (3 if cue else 0) - (2 if proof and recur == 0 else 0) + (5 if own else 0) + (3 - TIER[row['category']])
    # Hebrew window: 30 tokens before the quote, 60 after (the interpretation follows the verse)
    raw = row['he'].split()
    # map token index approx by proportional position in raw words (raw split ~ token split)
    a, b = (max(0, s - 30), min(len(raw), e + 60)) if found else (0, 90)
    hewin = ('… ' if a else '') + ' '.join(raw[a:b]) + (' …' if b < len(raw) else '')
    en = row['en']
    if len(en) > 900:
        m = re.search(rf'\b{p}:{v}\b', en)
        c = m.start() if m else 0
        en = ('… ' if c > 350 else '') + en[max(0, c - 350):c + 550] + ' …'
    return dict(verse=v, found=found, quote_len=k, recur=recur, cue=cue, proof=proof, own=own, reads=reads,
                score=score, he_win=hewin, en_win=en, span=(s, e), stoks=st)

def shingles(st, s, e):
    w = [skel(x) for x in st[max(0, s - 25):e + 40]]
    return {tuple(w[i:i + 4]) for i in range(len(w) - 3)}

def select(p, per_verse=2, budget_per_verse=1100):
    rows = json.load(open(f'full_{p}.json'))
    items = []
    for r in rows:
        if not r['he']: continue
        a = analyse(r, p)
        if a is None or not a['found']: continue
        a.update(ref=r['ref'], work=r['index_title'], cat=r['category'],
                                   date=(r.get('compDate') or [9999])[0])
        a['sh'] = shingles(a['stoks'], *a['span'])
        items.append(a)
    # parallels: cluster by Jaccard on shingles, keep the earliest
    items.sort(key=lambda x: x['date'])
    clusters = []
    for it in items:
        for c in clusters:
            h = c[0]
            if it['verse'] == h['verse'] and it['sh'] and h['sh'] and len(it['sh'] & h['sh']) / len(it['sh'] | h['sh']) >= 0.25:
                c.append(it); break
        else:
            clusters.append([it])
    heads = []
    for c in clusters:
        h = c[0]; h['parallels'] = [x['ref'] for x in c[1:]]
        h['score'] += min(2, len(c) - 1)   # a reading the tradition repeated
        heads.append(h)
    kept, dropped = [], []
    by_v = defaultdict(list)
    for h in heads:
        (by_v[h['verse']] if h['reads'] else dropped).append(h)
    pool = []
    for v, hs in by_v.items():
        hs.sort(key=lambda x: (-x['score'], x['date']))
        pool += hs[:per_verse]; dropped += hs[per_verse:]
    budget = budget_per_verse * len(PS[p])
    # fill round-robin by rank within verse, so every verse gets its best before any gets its second
    pool.sort(key=lambda x: (sorted(by_v[x['verse']], key=lambda y: (-y['score'], y['date'])).index(x), -x['score']))
    used = 0
    for h in pool:
        size = len(h['he_win']) + len(h['en_win'])
        if used + size <= budget: kept.append(h); used += size
        else: dropped.append(h)
    return kept, dropped, used, budget, len(items), len(heads)

if __name__ == '__main__':
    p = int(sys.argv[1])
    kept, dropped, used, budget, n, nh = select(p)
    print(f"Ps {p}: {n} passages -> {nh} after merging parallels -> kept {len(kept)} ({used} chars of {budget} budget)")
    for h in sorted(kept, key=lambda x: (x['verse'], x['date'])):
        print(f"  KEEP v{h['verse']:>2} s{h['score']:>2} r{h['recur']} {'cue' if h['cue'] else '   '} {'proof' if h['proof'] else '     '} {h['ref']}" + (f"  [+{len(h['parallels'])} parallels]" if h['parallels'] else ''))
    print("  -- dropped (reads=False or over cap/budget):")
    for h in sorted(dropped, key=lambda x: (x['verse'], -x['score'])):
        print(f"  drop v{h['verse']:>2} s{h['score']:>2} r{h['recur']} {'cue' if h['cue'] else '   '} {'proof' if h['proof'] else '     '} reads={h['reads']!s:5} {h['ref']}")
