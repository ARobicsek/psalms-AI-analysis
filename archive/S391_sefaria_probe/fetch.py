import json, re, sys, requests
S = requests.Session()
def text(ref):
    d = S.get("https://www.sefaria.org/api/v3/texts/" + requests.utils.quote(ref.replace(' ', '_'), safe='_.:,-;()\'') + "?version=hebrew&version=english", timeout=60).json()
    out = {}
    for v in d.get('versions', []):
        t = v.get('text'); 
        def flat(x): return " ".join(flat(i) for i in x) if isinstance(x, list) else (x or "")
        out[v['language']] = re.sub(r'\s+', ' ', re.sub('<[^>]+>', '', flat(t))).strip()
    return out
