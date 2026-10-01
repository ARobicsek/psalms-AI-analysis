import json, re, time, requests
S = requests.Session()
def leaves(node, prefix):
    titles = [t['text'] for t in node.get('titles', []) if t.get('lang') == 'en' and t.get('primary')]
    name = titles[0] if titles else None
    here = prefix + ([name] if name and not node.get('default') else [])
    if node.get('nodes'):
        for c in node['nodes']:
            yield from leaves(c, here)
    else:
        yield ", ".join(here)
out = {}
for title in ["Rabbi Sacks on Siddur", "Rabbi Sacks on Rosh HaShana Mahzor", "Rabbi Sacks on Yom Kippur Mahzor", "The Jonathan Sacks Haggadah"]:
    idx = S.get(f"https://www.sefaria.org/api/v2/raw/index/{title.replace(' ', '_')}", timeout=60).json()
    refs = list(leaves(idx['schema'], []))
    for ref in refs:
        for a in range(3):
            try:
                d = S.get("https://www.sefaria.org/api/v3/texts/" + requests.utils.quote(ref.replace(' ', '_'), safe="_,;'()") + "?version=english", timeout=60).json()
                break
            except Exception as e:
                time.sleep(2)
        t = d.get('versions', [{}])[0].get('text', []) if d.get('versions') else []
        def flat(x, path):
            if isinstance(x, list):
                for i, y in enumerate(x, 1): yield from flat(y, path + [i])
            elif x: yield path, x
        out[ref] = [(".".join(map(str, p)), re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', s)).strip()) for p, s in flat(t, [])]
        time.sleep(0.2)
    print(title, len(refs), sum(len(out[r]) for r in refs), flush=True)
json.dump(out, open("sacks_liturgical.json", "w"), ensure_ascii=False)
