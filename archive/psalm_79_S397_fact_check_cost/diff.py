import json, sys, re
sys.path.insert(0, sys.argv[3])
from compare import load, same
A, B = load(sys.argv[1]), load(sys.argv[2])
def only(src, other, tag):
    print(f'\n######## {tag}')
    for r in src:
        if r['verdict'] != 'contradicted': continue
        m = [o for o in other if same(r, o)]
        if any(o['verdict'] == 'contradicted' for o in m): continue
        ov = '; '.join(f"{o['verdict']}: {o['explanation'][:200]}" for o in m) or '(no record)'
        ev = ' | '.join(f"{e['source']}: {e['quote'][:250]}" for e in r.get('evidence', []))
        print(f"\n* [{r['location']}] {r['sentence'][:300]}\n  CLAIM: {r['claim']}\n  WHY: {r['explanation'][:400]}\n  EVID: {ev[:500]}\n  FIX: {(r.get('suggested_fix') or '')[:250]}\n  OTHER RUN: {ov[:400]}")
only(A, B, 'ORIGINAL (A) contradicted, new run (B) did not')
only(B, A, 'NEW (B) contradicted, original (A) did not')
