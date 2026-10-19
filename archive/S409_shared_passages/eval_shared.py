import sys, json, time, logging
sys.path.insert(0, r"C:\dev\personal\psalms")
logging.disable(logging.CRITICAL)
from src.concordance import shared_passages as sp
from src.agents.related_psalms_librarian import RelatedPsalmsLibrarian

KNOWN = [(14,'Psalms',53),(40,'Psalms',70),(57,'Psalms',108),(60,'Psalms',108),(31,'Psalms',71),(115,'Psalms',135),
(135,'Psalms',136),(79,'Psalms',115),(96,'Psalms',98),(6,'Psalms',38),(106,'Psalms',107),(107,'Psalms',118),(42,'Psalms',43),
(35,'Psalms',40),(41,'Psalms',106),(115,'Psalms',118),(93,'Psalms',96),(86,'Psalms',103),(103,'Psalms',145),(18,'II Samuel',22),
(105,'I Chronicles',16),(96,'I Chronicles',16),(106,'I Chronicles',16),(132,'II Chronicles',6),(79,'Jeremiah',10),(135,'Jeremiah',10),
(107,'Job',12),(113,'I Samuel',2),(118,'Exodus',15),(77,'Habakkuk',3),(31,'Jeremiah',20),(1,'Jeremiah',17)]

out = sys.argv[1]
t0 = time.time()
allp = {ps: sp.find_shared_passages(ps) for ps in range(1, 151)}
print(f"scan {time.time()-t0:.1f}s")
found = set()
for ps, L in allp.items():
    for p in L:
        found.add((ps, p.other[0], p.other[1]))
        if p.other[0] == 'Psalms':
            found.add((p.other[1], 'Psalms', ps))
miss = [k for k in KNOWN if k not in found]
print("known:", len(KNOWN) - len(miss), "/", len(KNOWN), "missed:", miss)

lib = RelatedPsalmsLibrarian(connections_file='data/analysis_results/top_550_connections_v6.json')
rows, hits = [], []
for ps in range(1, 151):
    new, refs = sp.compute_shared_passages(ps)
    rel = lib.get_related_psalms(ps)
    old = lib.format_for_research_bundle(ps, rel, max_size_chars=50000) if rel else ""
    rows.append((ps, len(old), len(new), new.count("### DOUBLET")))
    for p in allp[ps]:
        hits.append(f"{p.matched:3} Ps {ps}:{p.ps_verses[0]}-{p.ps_verses[1]} ~ {p.other[0]} {p.other[1]}:{p.other_verses[0]}-{p.other_verses[1]}")
json.dump({"rows": rows, "hits": hits}, open(out, "w", encoding="utf-8"), ensure_ascii=False)
O = sum(r[1] for r in rows); N = sum(r[2] for r in rows)
print(f"total chars old={O:,} new={N:,} ({N/O:.1%}); passages={len(hits)}")
bigger = [r for r in rows if r[2] > r[1]]
print("psalms where new > old:", bigger)
print("largest new:", sorted(rows, key=lambda r: -r[2])[:8])
print("psalms with nothing new:", sum(1 for r in rows if r[2] == 0), " with a doublet:", [r[0] for r in rows if r[3]])
