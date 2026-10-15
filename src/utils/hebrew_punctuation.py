"""Modern punctuation for biblical quotations in the printed guide (Session 405).

Writers quote a verse without its accents, and with the accents goes the only punctuation
biblical Hebrew has: the Hebrew of a quotation runs straight through the place where its
English translation has a comma or a full stop. The accents are still in tanakh.db, so this
is a lookup, not a judgment (the same reasoning as the divine-name converter, S398): find the
quoted words in the Bible and put back

- a comma after the word carrying the etnachta (the verse's main pause), and in the poetic
  books (Psalms, Proverbs, Job) after the word carrying ole ve-yored (the main pause of the
  first half of a long verse);
- a full stop where the quotation runs across the end of a verse.

Nothing is added at the end of a quotation: the English sentence goes on there with its own
punctuation. Guard rails: (0) a span carrying cantillation is a printed verse whose accents ARE
its punctuation, and is left alone (the guides' full-psalm sections; found by the S405 sweep);
(1) a span that already holds any punctuation is left alone,
so a verse the writer punctuated itself (every verse header) is never re-punctuated; (2) a
span must be at least MIN_WORDS words and match the Bible word for word, consecutively;
(3) a span found in more than one place is punctuated only if every place gives the same
pauses. Used by document_generator on the essay and verse text before the divine-name
converter; the markdown files are not changed.
"""

from __future__ import annotations

import re
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

MIN_WORDS = 4
POETIC_BOOKS = {"Psalms", "Proverbs", "Job"}
DB_PATH = Path(__file__).resolve().parents[2] / "database" / "tanakh.db"

ETNACHTA = "֑"
OLE = "֫"
YORED = "֥"          # merkha; with ole on the same word it is ole ve-yored
_MARKS = re.compile(r"[֑-ׇ͏]")   # points, accents, maqaf, paseq, sof pasuq, CGJ

# A Hebrew word in the guide: letters with points and accents, perhaps bold letters inside
# (**ו**), a geresh or apostrophe (ה׳). Maqaf, paseq and sof pasuq are separators.
_WORD = r"\**[א-ת][א-ת֑-ֽֿׁׂׄ-ׇ׳״'*͏]*"
_SEP = r"(?:[ \t]*[,;:.׃][ \t]+|[ \t]*־[ \t]*|[ \t]*׀[ \t]*|[ \t]+)"
_SPAN = re.compile(rf"{_WORD}(?:{_SEP}{_WORD})*")
_WORD_RE = re.compile(_WORD)
_PUNCT_SEP = re.compile(r"[,;:.׃]")
_ACCENTS = re.compile(r"[֑-֯]")

_DIVINE = re.compile(r"^([ובלכמשה]*)(?:ה['׳]|יקוק|ידוד)$")


def norm(token: str) -> str:
    """Consonants only, divine names in their biblical spelling (both sides of the match)."""
    t = _MARKS.sub("", token).replace("*", "")
    m = _DIVINE.match(t)
    if m:
        return m.group(1) + "יהוה"
    t = t.replace("'", "").replace("׳", "").replace("״", "")
    return t.replace("אלק", "אלה")


@lru_cache(maxsize=1)
def _bible(db_path: str = str(DB_PATH)):
    """Per book: the word stream (normalised) and the mark that follows each word."""
    con = sqlite3.connect(db_path)
    rows = con.execute("SELECT book_name, chapter, verse, hebrew FROM verses ORDER BY verse_id").fetchall()
    con.close()
    streams: Dict[str, Tuple[List[str], List[Optional[str]]]] = {}
    index: Dict[str, List[Tuple[str, int]]] = {}
    for book, _ch, _v, heb in rows:
        words, marks = streams.setdefault(book, ([], []))
        heb = re.sub(r"\{[^}]*\}", " ", heb)          # parasha marks
        heb = re.sub(r"\([^)]*\)", " ", heb)          # ketiv: the qere [..] is what is read
        heb = heb.replace("[", " ").replace("]", " ")
        toks = [t for t in re.split(r"[\s־׀]+", heb) if t and re.search("[א-ת]", t)]
        for i, t in enumerate(toks):
            mark = None
            if i == len(toks) - 1:
                mark = "."
            elif ETNACHTA in t or (book in POETIC_BOOKS and OLE in t and YORED in t):
                mark = ","
            index.setdefault(norm(t), []).append((book, len(words)))
            words.append(norm(t))
            marks.append(mark)
    return streams, index


def breaks_for(tokens: List[str], db_path: str = str(DB_PATH)) -> Optional[Dict[int, str]]:
    """{i: mark} to put after tokens[i] (never the last), or None if the words are not a
    unique-enough biblical quotation."""
    if len(tokens) < MIN_WORDS:
        return None
    streams, index = _bible(db_path)
    n = [norm(t) for t in tokens]
    k = min(range(len(n)), key=lambda i: len(index.get(n[i], ())))   # rarest word anchors
    found = None
    for book, pos in index.get(n[k], ()):
        start = pos - k
        words, marks = streams[book]
        if start < 0 or start + len(n) > len(words) or words[start:start + len(n)] != n:
            continue
        br = {i: marks[start + i] for i in range(len(n) - 1) if marks[start + i]}
        if found is None:
            found = br
        elif found != br:
            return None          # the same words, paused differently elsewhere: leave it
    return found or None


def punctuate_biblical_quotations(text: str, db_path: str = str(DB_PATH)) -> str:
    """Insert the commas and full stops a biblical quotation's accents call for (see module doc)."""
    def fix(m: re.Match) -> str:
        span = m.group(0)
        words = list(_WORD_RE.finditer(span))
        if len(words) < MIN_WORDS:
            return span
        seps = [span[a.end():b.start()] for a, b in zip(words, words[1:])]
        if any(_PUNCT_SEP.search(s) for s in seps):
            return span          # the writer punctuated this one
        if _ACCENTS.search(span):
            return span          # a cantillated verse: its accents are its punctuation
        br = breaks_for([w.group(0) for w in words], db_path)
        if not br:
            return span
        out = []
        for i, w in enumerate(words):
            out.append(w.group(0))
            if i < len(seps):
                mark = br.get(i)
                out.append(mark + seps[i] if mark and "־" not in seps[i] else seps[i])
        return "".join(out)
    return _SPAN.sub(fix, text)
