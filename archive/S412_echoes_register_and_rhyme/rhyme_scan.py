"""Scan the Psalter for clusters of 3+ words in one verse sharing a closed final syllable
(vowel class + final consonant), excluding plural/suffix endings. Compare to a shuffle baseline."""
import random, re, sqlite3, sys, unicodedata
from collections import Counter, defaultdict

DB = r"C:\dev\personal\psalms\database\tanakh.db"
CANT = re.compile(r"[\u0591-\u05AF\u05BD\u05BF\u05C0\u05C3-\u05C6]")
VOW = {"\u05B4": "i", "\u05B5": "e", "\u05B6": "e", "\u05B7": "a", "\u05B8": "a", "\u05C7": "o",
       "\u05B9": "o", "\u05BA": "o", "\u05BB": "u", "\u05B1": "e", "\u05B2": "a", "\u05B3": "o"}
FINAL = str.maketrans("ךםןףץ", "כמנפצ")
SUFFIX_KEYS = {("i", "ימ"), ("o", "ות")}


def letters(word):
    """[(consonant, marks)] for a pointed word."""
    out = []
    for ch in word:
        if "\u05D0" <= ch <= "\u05EA":
            out.append([ch, ""])
        elif out and "\u0591" <= ch <= "\u05C7":
            out[-1][1] += ch
    return out


def rhyme_key(word):
    L = letters(word)
    if len(L) < 2:
        return None
    trail = []
    i = len(L) - 1
    while i >= 0:
        c, m = L[i]
        v = next((VOW[x] for x in m if x in VOW and x not in "\u05B1\u05B2\u05B3"), None)
        if c == "ו" and "\u05B9" in m:
            v = "o"
        if c == "ו" and "\u05BC" in m and not any(x in VOW for x in m) and i > 0 and not any(x in VOW for x in L[i - 1][1]):
            v = "u"
        if v:
            # furtive patah under a final guttural after a long vowel: skip it
            if v == "a" and i == len(L) - 1 and c in "חעה" and i > 0:
                trail.append(c); i -= 1; continue
            break
        trail.append(c)
        i -= 1
    if i < 0 or not trail:
        return None
    cons = "".join(reversed(trail)).translate(FINAL)
    # drop matres: yod after i/e, vav after o/u, he/aleph alone at end => open syllable
    cons = cons.lstrip("י") if v in "ie" else cons
    cons = cons.lstrip("ו") if v in "ou" else cons
    cons = cons.rstrip("הא") if cons.endswith(("ה", "א")) and "\u05BC" not in L[-1][1] else cons
    if not cons:
        return None
    if (v, cons) in SUFFIX_KEYS or cons.endswith("ימ") or cons.endswith("ות"):
        return None
    if cons in ("כמ", "המ") or word.endswith(("כֶם", "הֶם", "תֶּם", "תֶם")):
        return None
    return v + "-" + cons


def cons_form(word):
    s = "".join(c for c, _ in letters(word)).translate(FINAL)
    return s[1:] if s.startswith("ו") and len(s) > 3 else s


def verse_words(heb):
    heb = CANT.sub("", unicodedata.normalize("NFC", heb))
    heb = re.sub(r"\{[^}]*\}", " ", heb).replace("\u05BE", " ")
    return [w for w in re.split(r"\s+", heb) if w]


def clusters(words):
    by = defaultdict(set)
    for w in words:
        k = rhyme_key(w)
        if k:
            by[k].add(cons_form(w))
    return {k: v for k, v in by.items() if len(v) >= 3}


def main():
    c = sqlite3.connect(DB)
    rows = c.execute("select chapter, verse, hebrew from verses where book_name='Psalms' order by chapter, verse").fetchall()
    verses = [(ch, v, verse_words(h)) for ch, v, h in rows]
    hits = [(ch, v, clusters(ws)) for ch, v, ws in verses]
    hits = [h for h in hits if h[2]]
    print(f"Psalter verses: {len(verses)}; verses with a 3+ cluster: {len(hits)}")
    keys = Counter(k for *_, cl in hits for k in cl)
    print("commonest cluster keys:", keys.most_common(12))
    for ch, v, cl in hits:
        if ch == 84:
            print("Ps 84:", v, cl)
    # baseline: shuffle words across verses, keep lengths
    allw = [w for *_, ws in verses for w in ws]
    base = []
    for seed in range(20):
        random.Random(seed).shuffle(allw)
        pos, n = 0, 0
        for *_, ws in verses:
            if clusters(allw[pos:pos + len(ws)]):
                n += 1
            pos += len(ws)
        base.append(n)
    print("shuffle baseline (20 runs): mean", sum(base) / len(base), "min", min(base), "max", max(base))
    ek = "e-נ"
    obs = sum(1 for *_, cl in hits if ek in cl)
    print("verses with a 3+ e-n cluster:", obs, [f"{ch}:{v}" for ch, v, cl in hits if ek in cl])
    freq = Counter(rhyme_key(w) for w in allw)
    print("share of Psalter words keyed e-n:", round(freq[ek] / len(allw), 4), "of", len(allw))
    if "--list" in sys.argv:
        for ch, v, cl in hits:
            print(f"{ch}:{v}", {k: sorted(s) for k, s in cl.items()})


if __name__ == "__main__":
    main()
