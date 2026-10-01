import json, re, sys, time, requests
S = requests.Session()
SCOPE = {"Talmud", "Midrash", "Mishnah", "Tosefta", "Second Temple", "Chasidut", "Musar", "Halakhah"}
ANTH = {"Yalkut Shimoni on Torah", "Yalkut Shimoni on Nach", "Ein Yaakov", "Ein Yaakov (Glick Edition)",
        "Midrash Sekhel Tov", "Midrash Lekach Tov", "Otzar Midrashim"}
def flat(x): return " ".join(flat(i) for i in x) if isinstance(x, list) else (x or "")
def clean(s):
    s = re.sub(r'<sup[^>]*>.*?</sup>|<i class="footnote">.*?</i>', ' ', s, flags=re.S)
    return re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', s)).strip()
def get(ref):
    for a in range(4):
        try:
            d = S.get("https://www.sefaria.org/api/v3/texts/" + requests.utils.quote(ref.replace(' ', '_'), safe="_.:,;'()-"),
                      params=[("version", "hebrew"), ("version", "english")], timeout=60).json()
            out = {}
            for v in d.get('versions', []):
                out[v['language']] = clean(flat(v.get('text')))
            return out
        except Exception:
            time.sleep(2 ** a)
    return {}
p = int(sys.argv[1])
L = json.load(open('links_all.json'))[str(p)]
rows = []
for l in L:
    if l['category'] not in SCOPE or l['index_title'] in ANTH: continue
    t = get(l['ref'])
    rows.append({**l, 'he': t.get('he', ''), 'en': t.get('en', '')})
    time.sleep(0.1)
json.dump(rows, open(f'full_{p}.json', 'w'), ensure_ascii=False)
from collections import Counter
print(p, len(rows), Counter(r['category'] for r in rows))
