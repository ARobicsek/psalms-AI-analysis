"""
Sefaria liturgy books harvester (Session 395).

The Session-1xx harvester (`sefaria_liturgy_harvester.py`) took 3 siddurim, the
Ashkenaz and Edot HaMizrach Rosh Hashanah / Yom Kippur machzorim and one
Haggadah. Sefaria holds more liturgy than that, and the gaps showed in the
guides: with no daily selichot in the corpus, a verse said in every selichot
service was reported as "in certain selichot".

This module adds whole books to the same `prayers` table, one row per leaf of
the book's schema (a day's selichot, a kinah, a section of Ma'avar Yabbok), so
the liturgical librarian and the fact checker's `search_liturgy` see them with
no other change. Rows it writes carry `liturgical_notes = HARVEST_NOTE`.

    python -m src.liturgy.sefaria_book_harvester --list          # the books and their leaf counts
    python -m src.liturgy.sefaria_book_harvester                 # harvest every book not yet present
    python -m src.liturgy.sefaria_book_harvester "Perek Shirah"  # one book
"""

from __future__ import annotations

import argparse
import html
import re
import sqlite3
import sys
import time
from typing import Iterator, List, Optional, Tuple
from urllib.parse import quote

import requests

API = "https://www.sefaria.org/api"
HARVEST_NOTE = "S395 book harvest"
DEFAULT_DB = "data/liturgy.db"

# (Sefaria title, nusach, prayer_type). The nusach labels match the existing rows:
# 'Sefard' is the Hasidic rite; 'Universal' is a work not tied to one rite.
# Left out on purpose: the "Linear" editions (the same texts again), the Koren
# siddur and mahzorim (the Ashkenaz texts again), the stand-alone Hallel /
# Kabbalat Shabbat / Birkat Hamazon / Lekha Dodi (already inside every siddur),
# and the Haggadah commentaries (commentary, not liturgy).
BOOKS: List[Tuple[str, str, str]] = [
    ("Selichot Nusach Ashkenaz Lita", "Ashkenaz", "Selichot"),
    ("Selichot Nusach Polin", "Ashkenaz", "Selichot"),
    ("Selichot Edot HaMizrach", "Edot_HaMizrach", "Selichot"),
    ("Machzor Rosh Hashanah Sefard", "Sefard", "Machzor"),
    ("Machzor Yom Kippur Sefard", "Sefard", "Machzor"),
    ("Kinnot for Tisha B'Av (Ashkenaz)", "Ashkenaz", "Kinnot"),
    ("Seder Tisha B'Av (Edot HaMizrach)", "Edot_HaMizrach", "Kinnot"),
    ("Pesach Haggadah Edot Hamizrah", "Edot_HaMizrach", "Haggadah"),
    ("Weekday Siddur Chabad", "Chabad", "Siddur"),
    ("Machzor Yom Ha'atzmaut & Yom Yerushalyim", "Universal", "Machzor"),
    ("Yizkor", "Universal", "Other"),
    ("Ma'avar Yabbok", "Universal", "Other"),
    ("Ma'aneh Lashon Chabad", "Chabad", "Other"),
    ("Tikkun HaKlali", "Universal", "Other"),
    ("Seder Ma'amadot", "Universal", "Other"),
    ("Perek Shirah", "Universal", "Other"),
    ("Akdamut Milin", "Ashkenaz", "Piyyut"),
    ("Keter Malkhut", "Universal", "Piyyut"),
    ("Azharot of Solomon ibn Gabirol", "Universal", "Piyyut"),
]

_TAG = re.compile(r"<[^>]+>")


def clean(s: str) -> str:
    """Sefaria segment HTML -> plain text (footnote markers and their bodies dropped)."""
    s = re.sub(r"<sup[^>]*>.*?</sup>\s*<i class=\"footnote\">.*?</i>", "", s or "", flags=re.S)
    s = re.sub(r"<i class=\"footnote\">.*?</i>", "", s, flags=re.S)
    s = s.replace("<br>", "\n").replace("<br/>", "\n")
    return html.unescape(_TAG.sub("", s)).strip()


def flatten(x) -> Iterator[str]:
    if isinstance(x, str):
        if x.strip():
            yield x
    elif isinstance(x, list):
        for y in x:
            yield from flatten(y)


def leaves(node: dict, path: List[str]) -> Iterator[List[str]]:
    """Every text-bearing node of a schema, as its title path (default nodes take the parent's)."""
    if "nodes" in node:
        for child in node["nodes"]:
            if child.get("key") == "default" or child.get("default"):
                yield from leaves(child, path)
            else:
                title = child.get("title") or next(
                    (t["text"] for t in child.get("titles", []) if t.get("lang") == "en" and t.get("primary")),
                    child.get("key", ""))
                yield from leaves(child, path + [title])
    else:
        yield path


class BookHarvester:
    def __init__(self, db_path: str = DEFAULT_DB, delay: float = 0.4):
        self.db_path = db_path
        self.delay = delay
        self.http = requests.Session()

    def _get(self, url: str, tries: int = 4) -> Optional[dict]:
        for k in range(tries):
            try:
                r = self.http.get(url, timeout=60)
                if r.status_code == 200:
                    return r.json()
                if r.status_code == 404:
                    return None
            except requests.RequestException:
                pass
            time.sleep(2 * (k + 1))
        return None

    def book_leaves(self, title: str) -> List[List[str]]:
        idx = self._get(f"{API}/v2/raw/index/{quote(title.replace(' ', '_'))}")
        if not idx:
            raise ValueError(f"Sefaria has no index for {title!r}")
        if "schema" not in idx:        # a simple text (Perek Shirah): one leaf, the whole book
            return [[idx["title"]]]
        return list(leaves(idx["schema"], [idx["title"]]))

    def leaf_text(self, ref: str) -> Tuple[str, str]:
        """(Hebrew, English) of one leaf, segments joined by newlines."""
        d = self._get(f"{API}/v3/texts/{quote(ref.replace(' ', '_'))}?version=hebrew&version=english"
                      "&return_format=text_only")
        he, en = "", ""
        for v in (d or {}).get("versions", []):
            body = "\n".join(clean(s) for s in flatten(v.get("text")))
            if v.get("language") == "he" and not he:
                he = body
            elif v.get("language") == "en" and not en:
                en = body
        return he, en

    def present(self, title: str) -> int:
        with sqlite3.connect(self.db_path) as c:
            return c.execute("SELECT COUNT(*) FROM prayers WHERE source_text = ?", (title,)).fetchone()[0]

    def harvest(self, title: str, nusach: str, prayer_type: str, verbose: bool = True) -> int:
        paths = self.book_leaves(title)
        rows = []
        for seq, path in enumerate(paths):
            ref = ", ".join(path)
            he, en = self.leaf_text(ref)
            time.sleep(self.delay)
            if not he.strip():
                if verbose:
                    print(f"   [skip, no Hebrew] {ref}")
                continue
            parent = ", ".join(path[1:-1]) or None
            rows.append((title, ref, nusach, prayer_type, path[1] if len(path) > 2 else None, parent,
                         path[-2] if len(path) > 2 else None, path[-1], he, en or None, seq, HARVEST_NOTE))
            if verbose:
                print(f"   {seq + 1}/{len(paths)} {ref} ({len(he):,} chars)")
        with sqlite3.connect(self.db_path) as c:
            c.executemany(
                "INSERT OR IGNORE INTO prayers (source_text, sefaria_ref, nusach, prayer_type, occasion, service, "
                "section, prayer_name, hebrew_text, english_text, sequence_order, liturgical_notes) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows)
        return len(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("books", nargs="*", help="Sefaria titles (default: every book in BOOKS)")
    ap.add_argument("--list", action="store_true", help="list the books and their leaf counts, fetch no text")
    ap.add_argument("--db", default=DEFAULT_DB)
    args = ap.parse_args(argv)
    h = BookHarvester(args.db)
    chosen = [b for b in BOOKS if not args.books or b[0] in args.books]
    for title, nusach, ptype in chosen:
        have = h.present(title)
        try:
            if args.list:
                print(f"{title:45} {nusach:15} {len(h.book_leaves(title)):4} leaves; {have} in the db")
                continue
            if have:
                print(f"{title}: already harvested ({have} rows)")
                continue
            print(f"Harvesting {title} ({nusach}, {ptype}) ...")
            n = h.harvest(title, nusach, ptype)
            print(f"{title}: {n} rows written")
        except Exception as e:   # one unavailable book must not stop the rest
            print(f"{title}: FAILED ({type(e).__name__}: {e})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
