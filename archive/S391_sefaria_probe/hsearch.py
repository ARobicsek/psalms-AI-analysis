import json, re, requests, time
ps={int(k):v for k,v in json.load(open('psalms_he_textonly.json')).items()}
SP=["Tanakh Commentary/Modern Commentary on Tanakh/Jonathan Sacks","Jewish Thought/Modern/Rabbi Lord Jonathan Sacks","Liturgy/Siddur/Rabbi Sacks on Siddur","Liturgy/High Holidays/Rabbi Sacks on Rosh HaShana Mahzor","Liturgy/High Holidays/Rabbi Sacks on Yom Kippur Mahzor","Liturgy/Haggadah/Commentary/The Jonathan Sacks Haggadah"]
def cons(s):
    s=re.sub(r'[֑-ׇ]','',s).replace('־',' ').replace('׀',' ')
    return ' '.join(re.sub(r'[^א-ת ]',' ',s).split())
def search(q, filters, size=50):
    body={"query":q,"type":"text","field":"naive_lemmatizer","size":size,"source_proj":["ref","path"],"slop":0,"filters":filters,"filter_fields":["path"]*len(filters)}
    for a in range(3):
        try:
            r=requests.post("https://www.sefaria.org/api/search-wrapper",json=body,timeout=60); r.raise_for_status()
            return [h['_source'].get('ref') for h in r.json()['hits']['hits']]
        except Exception: time.sleep(2)
    return []
def psalm_hits(p, filters=SP, n=4):
    found={}
    for i,v in enumerate(ps[p],1):
        w=cons(v).split()
        if len(w)<n: continue
        # two probes per verse: first n words, last n words
        for q in {' '.join(w[:n]), ' '.join(w[-n:])}:
            for ref in search(q, filters):
                found.setdefault(ref,set()).add(i)
        time.sleep(0.1)
    return found
if __name__=='__main__':
    import sys
    for p in map(int, sys.argv[1:]):
        f=psalm_hits(p); print(p, len(f)); [print('   ',r, sorted(v)) for r,v in list(f.items())[:15]]
