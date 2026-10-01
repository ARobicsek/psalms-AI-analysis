import json, time, requests, sys
out = {}
s = requests.Session()
for p in range(1, 151):
    for attempt in range(4):
        try:
            r = s.get(f"https://www.sefaria.org/api/links/Psalms.{p}", params={"with_text": 0}, timeout=120)
            r.raise_for_status()
            out[p] = [{k: l.get(k) for k in ("ref", "anchorRef", "category", "index_title", "type", "sourceHasEn", "compDate", "collectiveTitle")} for l in r.json()]
            break
        except Exception as e:
            print(p, "retry", e, file=sys.stderr); time.sleep(2 ** attempt)
    time.sleep(0.3)
    if p % 10 == 0:
        print(p, len(out.get(p, [])), flush=True)
json.dump(out, open("links_all.json", "w"))
print("done")
