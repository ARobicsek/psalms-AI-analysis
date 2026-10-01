import json, re, sys, time, requests
sys.path.insert(0, '.')
from fetch import text
KEEP = {"Talmud", "Midrash", "Mishnah", "Tosefta", "Targum", "Jewish Thought", "Musar", "Chasidut", "Kabbalah", "Halakhah", "Second Temple", "Responsa"}
ANTHOLOGIES = {"Yalkut Shimoni on Torah", "Yalkut Shimoni on Nach", "Ein Yaakov", "Ein Yaakov (Glick Edition)", "Midrash Sekhel Tov", "Midrash Lekach Tov", "Otzar Midrashim"}
def window(s, needles, w=700):
    for n in needles:
        i = s.find(n)
        if i >= 0:
            a, b = max(0, i - w), min(len(s), i + len(n) + w)
            return ("…" if a else "") + s[a:b] + ("…" if b < len(s) else "")
    return s[:2 * w] + ("…" if len(s) > 2 * w else "")
def harvest(p):
    L = json.load(open('links_all.json'))[str(p)]
    rows = []
    for l in L:
        if l['category'] not in KEEP: continue
        if l['index_title'] in ANTHOLOGIES: continue
        t = text(l['ref'])
        v = l['anchorRef'].split(':')[-1].split('-')[0]
        needles = [f"Psalms {p}:{v}", f"Ps. {p}:{v}", f"תהלים {p}", f"תהילים"]
        en = window(t.get('en', ''), needles); he = window(t.get('he', ''), needles)
        rows.append({**{k: l[k] for k in ('ref', 'anchorRef', 'category', 'index_title', 'compDate')}, 'en': en, 'he': he,
                     'en_full': len(t.get('en', '')), 'he_full': len(t.get('he', ''))})
        time.sleep(0.15)
    return rows
if __name__ == '__main__':
    p = int(sys.argv[1]); rows = harvest(p)
    json.dump(rows, open(f'harvest_{p}.json', 'w'), ensure_ascii=False)
    from collections import Counter
    print(len(rows), Counter(r['category'] for r in rows))
    print('chars windowed en', sum(len(r['en']) for r in rows), 'he', sum(len(r['he']) for r in rows),
          '| full en', sum(r['en_full'] for r in rows), 'he', sum(r['he_full'] for r in rows))
    print('with English', sum(1 for r in rows if r['en']))
