"""Compare two fact-check reports on the same guide: which flagged claims each catches."""
import json, sys, re
def load(p):
    return json.load(open(p, encoding='utf-8'))['claims']
def key(s):
    return re.sub(r'\W+', ' ', s or '').strip().lower()
def same(a, b):
    ka, kb = key(a['sentence']), key(b['sentence'])
    return ka[:50] == kb[:50] or (len(ka) > 30 and (ka[:40] in kb or kb[:40] in ka))
if __name__ == "__main__":
  A, B = load(sys.argv[1]), load(sys.argv[2])
  for name, x in (('A', A), ('B', B)):
      v = {}
      for r in x: v[r['verdict']] = v.get(r['verdict'], 0) + 1
      print(name, len(x), v)
  def show(src, other, label):
      print(f'\n### {label}')
      for r in src:
          if r['verdict'] != 'contradicted': continue
          m = [o for o in other if same(r, o)]
          mv = sorted({o['verdict'] for o in m}) or ['(no record)']
          print(f"- [{'/'.join(mv)}] {r['location'][:30]} | {r['claim'][:110]}")
  show(A, B, 'A contradicted -> B verdicts on that sentence')
  show(B, A, 'B contradicted -> A verdicts on that sentence')
