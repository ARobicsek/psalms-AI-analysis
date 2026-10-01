"""
The Aramaic Targum to Psalms, per Hebrew verse, from Sefaria.

Session 391. An ancient Jewish translation that interprets as it translates, the same class of
witness as the Septuagint the writer gets since S390, and it lands on the cruxes: on Ps 77:11 it
gives TWO readings (one of them "the years of the End"); on 76:5 it reads נְהִיר דְּחִיל, "luminous,
fearsome", both readings the commentators split over, where the S385 guide, knowing the Targum only
through the Alshich, reported one. The guides cite the Targum; until now it was never supplied.

Aramaic: Sefaria's Mikraot Gedolot text, all 150 psalms, in the Masoretic verse numbering
(superscription = verse 1; checked against the Hebrew for all 150 psalms, S391). English exists
on Sefaria for only 35 psalms (Edward M. Cook's translation, preferred, or the community
translation); elsewhere the writer reads the Aramaic.

Cache: data/sefaria_cache/targum/psalm_NNN.json (gitignored with the rest of data/).
"""
from __future__ import annotations

import json
import logging
import re
import time
from html import unescape
from pathlib import Path
from typing import Dict, Tuple

import requests

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT_ROOT / "data" / "sefaria_cache" / "targum"
INDEX = "Aramaic_Targum_to_Psalms"
URL = f"https://www.sefaria.org/api/v3/texts/{INDEX}"
COOK = "The Psalms Targum: An English Translation (Edward M. Cook)"
SOURCE_NOTE = ("*Targum = the Aramaic Targum to Psalms (Mikraot Gedolot text, via Sefaria); English, where "
               "given, is Edward M. Cook's translation or Sefaria's community translation.*")


def _clean(s) -> str:
    if isinstance(s, list):
        s = " ".join(_clean(x) for x in s)
    s = re.sub(r'<sup[^>]*>.*?</sup>|<i class="footnote">.*?</i>', " ", s or "", flags=re.S)
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def _fetch(psalm: int, attempts: int = 4) -> Dict:
    for attempt in range(1, attempts + 1):
        try:
            r = requests.get(f"{URL}.{psalm}", params=[("version", "hebrew"), ("version", "english|all")], timeout=60)
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError) as e:
            if attempt == attempts:
                raise
            logger.warning(f"[targum] Sefaria request failed ({e}); retry {attempt}/{attempts - 1}")
            time.sleep(2 ** attempt)


def targum_by_verse(psalm: int, cache_dir: Path = CACHE_DIR) -> Dict[int, Tuple[str, str]]:
    """{verse: (Aramaic, English or "")}, keyed by the Hebrew verse number. {} if unavailable."""
    path = Path(cache_dir) / f"psalm_{psalm:03d}.json"
    if path.exists():
        try:
            return {int(k): tuple(v) for k, v in json.loads(path.read_text(encoding="utf-8")).items()}
        except (OSError, ValueError):
            pass
    try:
        data = _fetch(psalm)
    except Exception as e:
        logger.warning(f"[targum] Psalm {psalm}: unavailable ({e})")
        return {}
    he = next((v.get("text") or [] for v in data.get("versions", []) if v.get("language") == "he"), [])
    ens = [v for v in data.get("versions", []) if v.get("language") == "en"]
    ens.sort(key=lambda v: v.get("versionTitle") != COOK)        # Cook first, then the rest
    out: Dict[int, Tuple[str, str]] = {}
    for i, a in enumerate(he):
        en = next((_clean(v["text"][i]) for v in ens if i < len(v.get("text") or []) and _clean(v["text"][i])), "")
        if _clean(a) or en:
            out[i + 1] = (_clean(a), en)
    if out:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({str(k): list(v) for k, v in out.items()}, ensure_ascii=False), encoding="utf-8")
    return out
