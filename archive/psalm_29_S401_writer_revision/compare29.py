"""Compare the S401 Ps 29 guide with the S400 baseline ($0)."""
import re, sys
from pathlib import Path

ROOT = Path(r"C:\dev\personal\psalms")
A = ROOT / "archive/psalm_29_S400_baseline/psalm_029_copy_edited.md"
B = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "output/psalm_29/psalm_029_copy_edited.md")

def body(t):
    t = t.split("## Methodological")[0]
    return t

def stats(t):
    t = body(t)
    words = len(re.findall(r"[A-Za-z']+", t))
    intro, _, verses = t.partition("## Verse-by-Verse Commentary")
    # the sentence just before each block quote that is not a verse translation (poem/echo quotes)
    lines = t.split("\n")
    echo_intros = []
    for i, ln in enumerate(lines):
        if ln.startswith(">") and i and not lines[i - 1].startswith(">") and lines[i - 1].strip():
            prev = lines[i - 1].strip()
            if re.search(r"[A-Za-z]", prev) and not prev.startswith("**Verse") and not re.match(r"^[\u0590-\u05FF\s;,.:׳־]+$", prev):
                if not re.match(r"^[\u0590-\u05FF]", prev):
                    echo_intros.append(prev[-160:])
    same = len(re.findall(r"\bthe same\b", t, re.I))
    opposite = len(re.findall(r"\bopposite\b|\bdid not take\b|\btoo\b[,:]", t, re.I))
    lxx = len(re.findall(r"Septuagint|LXX|Greek translat|the Greek", t))
    lxx_verses = sum(1 for note in re.split(r"\*\*Verses? \d", verses)[1:] if re.search(r"Septuagint|LXX|the Greek|Greek translat", note))
    other = {k: len(re.findall(p, t)) for k, p in {
        "Christian/church": r"Christian|church|Church|Augustine|Basil|Luther|Calvin|liturg(y|ical) of the|Baptism",
        "Qumran/Scrolls": r"Qumran|Dead Sea",
        "scholars/modern": r"\bscholar|\bmodern (reader|critic|study|scholar)|critic(s|al)\b",
        "Ugarit/ANE": r"Ugarit|Baal|Amarna|Canaanite",
    }.items()}
    trad = len(re.findall(r"Rashi|Radak|Ibn Ezra|Malbim|Meiri|Alshich|Midrash|Talmud|Targum|Minchat Shai|Torah Temimah", t))
    first_person = len(re.findall(r"\bI (think|read|find|suspect|would|take|believe|doubt|prefer)\b|\bto my ear\b|\bmy reading\b", t))
    judg = len(re.findall(r"\b(more convincing|stronger reading|better read|wrong|mistaken|misses|I think)\b", t))
    funny = 0
    return dict(words=words, intro_words=len(re.findall(r"[A-Za-z']+", intro)), echo_intros=echo_intros,
                same=same, opposite_markers=opposite, lxx_mentions=lxx, lxx_verses=lxx_verses, other=other,
                trad=trad, first_person=first_person, judgment_words=judg)

for name, f in (("BASELINE (S400)", A), ("NEW (S401)", B)):
    s = stats(f.read_text(encoding="utf-8"))
    print(f"===== {name}")
    for k, v in s.items():
        if k == "echo_intros":
            print(f"echo/quote lead-ins ({len(v)}):")
            for x in v:
                print("   …" + x)
        else:
            print(f"{k}: {v}")
