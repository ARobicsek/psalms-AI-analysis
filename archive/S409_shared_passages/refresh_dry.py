import glob, re, sys, logging
from pathlib import Path
logging.disable(logging.CRITICAL)
sys.path.insert(0, '.')
from src.concordance.shared_passages import refresh_bundle_shared_passages, SECTION_HEADER, parse_shared_passages_refs
tot_old = tot_new = 0; rows = []
for f in sorted(glob.glob('output/psalm_*/psalm_*_research_v2.md')):
    b = open(f, encoding='utf-8').read()
    m = re.fullmatch(r'psalm_(\d+)', Path(f).parent.name)
    if not m: continue
    n = int(m.group(1))
    new, changed = refresh_bundle_shared_passages(b, n)
    h_old = re.findall(r'^## (.+)$', b, re.M); h_new = re.findall(r'^## (.+)$', new, re.M)
    lost = [h for h in h_old if h not in h_new and not h.startswith('Related Psalms')]
    tot_old += len(b); tot_new += len(new)
    rows.append((n, len(b) - len(new), changed, lost))
print("bundles:", len(rows), " changed:", sum(r[2] for r in rows), " lost headers:", [r for r in rows if r[3]])
s = sorted(r[1] for r in rows)
print(f"total {tot_old:,} -> {tot_new:,} chars (-{tot_old - tot_new:,}); saved per bundle min/median/max: {s[0]:,} / {s[len(s)//2]:,} / {s[-1]:,}")
print("bundles that grew:", [r[0] for r in rows if r[1] < 0])
b = open(glob.glob('output/psalm_79/psalm_*_research_v2.md')[0], encoding='utf-8').read()
new, _ = refresh_bundle_shared_passages(b, 79)
print("Ps 79 sections:", [h[:28] for h in re.findall(r'^## (.+)$', new, re.M)])
print("Ps 79 refs:", parse_shared_passages_refs(new))
