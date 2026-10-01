"""PROTOTYPE v2: structural rules first (source class, age, parallels), word overlap only to drop bare proof-texts."""
import json, re, sys, math
from collections import defaultdict
import rules as R

SUFFIX = ('ים', 'ות', 'יו', 'יה', 'הם', 'כם', 'נו', 'ה', 'ו', 'י', 'ך', 'ת', 'מ', 'נ')
def stem(w):
    w = R.skel(w)
    for _ in range(2):
        if len(w) > 3 and w[0] in 'והבלמשכד': w = w[1:]
    for sfx in SUFFIX:
        if len(w) > 3 and w.endswith(sfx): w = w[:-len(sfx)]; break
    return w
R.same = lambda a, b: R.skel(a) == R.skel(b) or (len(stem(a)) >= 2 and stem(a) == stem(b))

CLASSICAL_MAX_DATE = 1250   # the rabbinic midrashim; later works go to the "later readers" allowance
def klass(it, p):
    if it['cat'] in ('Talmud', 'Mishnah', 'Tosefta') and it['date'] <= 1000: return 'A'   # a known, early date
    if it['own']: return 'A'
    if it['cat'] in ('Midrash', 'Second Temple') and it['date'] <= CLASSICAL_MAX_DATE: return 'B'
    if it['cat'] in ('Midrash', 'Second Temple') and it['date'] < 9999: return 'B'
    return 'C'   # Hasidut, Musar, Halakhah, undated   # Hasidut, Musar, Halakhah

def bare_proof(it, he_len):
    return it['proof'] and it['recur'] == 0 and not it['cue'] and he_len > 600

def select(p, per_verse_B=2, later_per_verses=4, budget_per_verse=1100):
    rows = json.load(open(f'full_{p}.json'))
    byref = {}
    for r in rows:
        if not r['he']: continue
        a = R.analyse(r, p)
        if a is None or not a['found']: continue          # mislinks and unlocatable quotes
        a.update(ref=r['ref'], work=r['index_title'], cat=r['category'], date=(r.get('compDate') or [9999])[0],
                 he_len=len(r['he']))
        a['sh'] = R.shingles(a['stoks'], *a['span'])
        if a['ref'] in byref:                               # one passage citing several verses = one item
            byref[a['ref']]['verses'].add(a['verse']); continue
        a['verses'] = {a['verse']}; byref[a['ref']] = a
    items = sorted(byref.values(), key=lambda x: x['date'])
    heads = []
    for it in items:                                        # parallels: keep the earliest telling
        for h in heads:
            if h['verses'] & it['verses'] and it['sh'] and h['sh'] and len(it['sh'] & h['sh']) / len(it['sh'] | h['sh']) >= 0.25:
                h['parallels'].append(it['ref']); break
        else:
            it['parallels'] = []; heads.append(it)
    nverses = len(R.PS[p]); budget = budget_per_verse * nverses
    for h in heads: h['k'] = klass(h, p); h['size'] = len(h['he_win']) + len(h['en_win'])
    A = [h for h in heads if h['k'] == 'A']
    B = [h for h in heads if h['k'] == 'B' and not bare_proof(h, h['he_len'])]
    C = [h for h in heads if h['k'] == 'C' and (h['recur'] >= 2 or h['cue']) and not bare_proof(h, h['he_len'])]
    # B: per verse, earliest first (age is the tie we trust), at most per_verse_B, round-robin across verses
    perv = defaultdict(list)
    for h in sorted(B, key=lambda x: (x['date'], -x['recur'])): perv[min(h['verses'])].append(h)
    Bq = [[hs[rank] for v, hs in sorted(perv.items()) if len(hs) > rank] for rank in range(per_verse_B)]
    # C: a verse that >= 3 DIFFERENT later works keep returning to has a reception tradition of its own:
    # keep its earliest telling and name the others. Then the best-engaged singles, up to the allowance.
    allC = [h for h in heads if h['k'] == 'C']
    byv = defaultdict(list)
    for h in sorted(allC, key=lambda x: x['date']): byv[min(h['verses'])].append(h)
    Cq = []
    for v, hs in sorted(byv.items()):
        if len({h['work'] for h in hs}) >= 3:
            lead = hs[0]; lead['also'] = sorted({h['work'] for h in hs[1:]} - {lead['work']}); Cq.append(lead)
    for h in sorted(C, key=lambda x: (-(x['recur'] + 3 * x['cue']), x['date'])):
        if len(Cq) >= math.ceil(nverses / later_per_verses): break
        if h not in Cq: Cq.append(h)
    kept, used = [], 0
    leads = [h for h in Cq if h.get('also')]; singles = [h for h in Cq if not h.get('also')]
    order = A + Bq[0] + leads + sum(Bq[1:], []) + singles
    for h in order:
        if used + h['size'] <= budget: kept.append(h); used += h['size']
    dropped = [h for h in heads if h not in kept]
    return kept, dropped, used, budget, len(byref), len(heads)

if __name__ == '__main__':
    p = int(sys.argv[1])
    kept, dropped, used, budget, n, nh = select(p)
    print(f"Ps {p}: {n} located passages -> {nh} after parallels -> kept {len(kept)} ({used} chars of {budget})")
    for h in sorted(kept, key=lambda x: (min(x['verses']), x['date'])):
        vs = ','.join(map(str, sorted(h['verses'])))
        print(f"  KEEP {h['k']} v{vs:<8} {h['date']:>5} r{h['recur']} {'cue' if h['cue'] else '   '} {h['ref']}" + (f"  [+{len(h['parallels'])} parallel: {'; '.join(h['parallels'])}]" if h['parallels'] else '') + (f"  [also: {', '.join(h['also'])}]" if h.get('also') else ''))
    print("  dropped:", '; '.join(f"{h['ref']}(v{min(h['verses'])},{h['k']})" for h in sorted(dropped, key=lambda x: min(x['verses']))))
