"""Essay / notes shape metrics for a copy-edited guide: words, mean sentence, % sentences 40+ words."""
import re, sys, json

HEB = re.compile(r'[֐-׿]')

def section(text, start, end_pat):
    i = text.find(start)
    if i < 0:
        return ''
    rest = text[i + len(start):]
    m = re.search(end_pat, rest, re.M)
    return rest[:m.start()] if m else rest

def prose(block):
    out = []
    for line in block.splitlines():
        s = line.strip()
        if not s or s.startswith('#') or s.startswith('>') or s.startswith('|'):
            continue
        if s.startswith('**') and s.endswith('**') and len(s) < 120:  # verse headers
            continue
        out.append(s)
    return '\n'.join(out)

def eng_words(t):
    return [w for w in re.findall(r"[A-Za-z][A-Za-z'\-]*", t)]

def sentences(t):
    t = re.sub(r'\s+', ' ', t)
    parts = re.split(r'(?<=[.!?])["”’)]*\s+(?=[A-Z"“(֐-׿])', t)
    return [p for p in parts if len(eng_words(p)) >= 3]

def stats(t):
    ss = sentences(t)
    lens = [len(re.findall(r"\S+", s)) for s in ss]
    n = len(lens) or 1
    return dict(eng_words=len(eng_words(t)), heb_words=len(re.findall(r'[֐-׿][֐-׿־"״׳\'־]*', t)),
                sentences=len(lens), mean=round(sum(lens) / n, 1), long40=f"{100*sum(l >= 40 for l in lens)/n:.0f}%")

path = sys.argv[1]
text = open(path, encoding='utf-8').read()
essay = section(text, '## Introduction', r'^(#### Full psalm|### Liturg|#### |## Psalm \d)')
notes = section(text, '## Verse-by-Verse Commentary', r'^## Methodological')
e, n = prose(essay), prose(notes)
refback = len(re.findall(r'\b[Tt]he (introduction|essay) (showed|traced|argued|noted|saw|has shown|suggested)', n))
print(json.dumps(dict(essay=stats(e), notes=stats(n), notes_refer_back=refback,
                      headings=len(re.findall(r'^###\s', essay, re.M))), ensure_ascii=False))
