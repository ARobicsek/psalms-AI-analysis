"""
The Septuagint's Greek, INFLECTED: Brenton's 1851 edition (public domain), from eBible.org.

Session 390. Until now the pipeline's Greek came from Bolls.life's "LXX", which is LEMMATIZED
(dictionary forms: Ps 77:2 arrives as "φωνή ἐγώ πρός κύριος κράζω ... καί προςἔχω ἐγώ" for
"Φωνῇ μου πρὸς Κύριον ἐκέκραξα ... καὶ προσέσχε μοι"). From lemmas no model can see a case, a
tense or a person, and the micro analyst read "προςἔχω ἐγώ" ("I attend") as an LXX reading in
which the psalmist is the listener; the Greek says "He gave heed to me".

Brenton's Greek uses the same LXX chapter and verse numbering as Bolls (the heading is verse 1;
checked for all 150 psalms: 0 mismatches), and it is the text Brenton's English translates.

The eBible download (~5 MB zip) is fetched once and cached as JSON under data/lxx/ (gitignored,
like the rest of data/): {"PSA": {"76": {"1": "...", ...}}, ...}. Book codes are USFM.
"""
from __future__ import annotations

import io
import json
import logging
import re
import threading
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_FILE = PROJECT_ROOT / "data" / "lxx" / "brenton_greek.json"
SOURCE_URL = "https://ebible.org/Scriptures/grcbrent_vpl.zip"
SOURCE_NAME = "Brenton's Septuagint, Greek text (1851; public domain; eBible.org grcbrent)"

# Hebrew-Bible book names as the fact checker parses them -> USFM codes in the eBible file.
# eBible's Brenton has no separate Song of Songs or Nehemiah; Daniel and Esther are the Greek
# books (DNG, ESG), whose extra chapters shift the numbering, so they are left out.
BOOK_CODES = {"Genesis": "GEN", "Exodus": "EXO", "Leviticus": "LEV", "Numbers": "NUM",
              "Deuteronomy": "DEU", "Joshua": "JOS", "Judges": "JDG", "Ruth": "RUT", "I Samuel": "1SA",
              "II Samuel": "2SA", "I Kings": "1KI", "II Kings": "2KI", "I Chronicles": "1CH",
              "II Chronicles": "2CH", "Job": "JOB", "Psalms": "PSA", "Proverbs": "PRO",
              "Ecclesiastes": "ECC", "Isaiah": "ISA", "Lamentations": "LAM", "Ezekiel": "EZE",
              "Hosea": "HOS", "Joel": "JOE", "Amos": "AMO", "Obadiah": "OBA", "Jonah": "JON",
              "Micah": "MIC", "Nahum": "NAH", "Habakkuk": "HAB", "Zephaniah": "ZEP", "Haggai": "HAG",
              "Zechariah": "ZEC", "Malachi": "MAL"}

_VPL_LINE = re.compile(r"^(\w{3}) (\d+):(\d+) (.*)$")
_lock = threading.Lock()
_data: Optional[Dict[str, Dict[str, Dict[str, str]]]] = None


def parse_vpl(text: str) -> Dict[str, Dict[str, Dict[str, str]]]:
    """eBible's verse-per-line format ("PSA 76:2 Φωνῇ μου ...") -> {book: {chapter: {verse: text}}}."""
    out: Dict[str, Dict[str, Dict[str, str]]] = {}
    for line in text.splitlines():
        m = _VPL_LINE.match(line.strip())
        if m and m.group(4).strip():
            out.setdefault(m.group(1), {}).setdefault(m.group(2), {})[m.group(3)] = m.group(4).strip()
    return out


def _download() -> Dict[str, Dict[str, Dict[str, str]]]:
    logger.info(f"Downloading {SOURCE_NAME} from {SOURCE_URL} (once; cached at {CACHE_FILE})")
    r = requests.get(SOURCE_URL, timeout=60)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    name = next(n for n in z.namelist() if n.endswith("_vpl.txt"))
    data = parse_vpl(z.read(name).decode("utf-8-sig"))
    if "PSA" not in data or len(data["PSA"]) < 150:
        raise RuntimeError(f"unexpected contents in {SOURCE_URL}: {sorted(data)[:5]}")
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def load() -> Dict[str, Dict[str, Dict[str, str]]]:
    """The whole text, from the cache (downloading it the first time). Raises if unavailable."""
    global _data
    with _lock:
        if _data is None:
            _data = (json.loads(CACHE_FILE.read_text(encoding="utf-8")) if CACHE_FILE.exists()
                     else _download())
        return _data


def chapter(book_code: str, lxx_chapter: int) -> Dict[int, str]:
    """{verse: Greek} for one chapter in LXX numbering; {} if the book or chapter is absent."""
    ch = load().get(book_code, {}).get(str(lxx_chapter), {})
    return {int(v): t for v, t in ch.items()}


def psalm_verses(lxx_chapter: int) -> List[str]:
    """A psalm's verses in order (heading = verse 1), in LXX numbering."""
    ch = chapter("PSA", lxx_chapter)
    return [ch[v] for v in sorted(ch)]


# --- Hebrew (MT) <-> Greek (LXX) psalm numbering, verse by verse ------------------------------
# MT 9-10 = LXX 9 (MT 10:1 = LXX 9:22); MT 11-113 = LXX 10-112; MT 114-115 = LXX 113 (MT 115:1 =
# LXX 113:9); MT 116:1-9 = LXX 114, 116:10-19 = LXX 115; MT 117-146 = LXX 116-145; MT 147:1-11 =
# LXX 146, 147:12-20 = LXX 147; MT 1-8 and 148-150 are the same. Headings are verse 1 in both.
# Checked against tanakh.db and Brenton (S390): every MT psalm's verse count matches its Greek,
# except that the LXX has no MT 116:14 (Brenton's LXX 115 skips verse 5).

def mt_to_lxx(mt_psalm: int, mt_verse: int) -> Tuple[int, int]:
    p, v = mt_psalm, mt_verse
    if p <= 9 or p >= 148:
        return p, v
    if p == 10:
        return 9, v + 21
    if 11 <= p <= 113 or 117 <= p <= 146:
        return p - 1, v
    if p == 114:
        return 113, v
    if p == 115:
        return 113, v + 8
    if p == 116:
        return (114, v) if v <= 9 else (115, v - 9)
    return (146, v) if v <= 11 else (147, v - 11)          # 147


def lxx_to_mt(lxx_chapter: int, lxx_verse: int) -> Tuple[int, int]:
    c, v = lxx_chapter, lxx_verse
    if c <= 8 or c >= 148:
        return c, v
    if c == 9:
        return (9, v) if v <= 21 else (10, v - 21)
    if 10 <= c <= 112 or 116 <= c <= 145:
        return c + 1, v
    if c == 113:
        return (114, v) if v <= 8 else (115, v - 8)
    if c == 114:
        return 116, v
    if c == 115:
        return 116, v + 9
    return (147, v) if c == 146 else (147, v + 11)          # 146, 147


def lxx_chapters_for_mt(mt_psalm: int) -> List[int]:
    """The Greek chapter(s) that hold a Hebrew psalm (two for MT 116 and 147)."""
    return {116: [114, 115], 147: [146, 147]}.get(mt_psalm, [mt_to_lxx(mt_psalm, 1)[0]])


def greek_by_mt_verse(mt_psalm: int) -> Dict[int, str]:
    """{MT verse: Brenton's Greek} for a Hebrew psalm. A verse the LXX lacks (MT 116:14) is absent."""
    out: Dict[int, str] = {}
    for c in lxx_chapters_for_mt(mt_psalm):
        for lv, text in chapter("PSA", c).items():
            p, v = lxx_to_mt(c, lv)
            if p == mt_psalm:
                out[v] = text
    return out
