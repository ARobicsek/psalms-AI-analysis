"""
Sacks Librarian: Rabbi Jonathan Sacks on a psalm, for the research bundle.

Session 392 rebuild (S391's evaluation, `docs/plans/S391_SEFARIA_EVALUATION.md` §3.3). The data comes
from `src/data_sources/sacks_index.py` (Sefaria, $0, cached under data/sacks/):

  1. His PRAYER-BOOK COMMENTARY (Koren siddur, Rosh HaShana and Yom Kippur mahzorim, the Haggadah),
     aligned to the psalm through the prayer-book paragraph each comment sits beside. This is the
     closest thing to "Sacks on Psalms" that exists, and the old file had none of it.
  2. Passages of his BOOKS that Sefaria links to the psalm, plus quotations its links miss (a Hebrew
     phrase search, confirmed in the paragraph).

What changed from Session 68's `sacks_on_psalms.json`: whole paragraphs (the linked paragraph and
its neighbours) instead of ±1,000-character windows cut mid-sentence; a one-sentence introduction
instead of a 2,243-character biography; repeats merged (the same comment printed in the siddur and
a mahzor, the same essay in two collections); a character budget; and items labelled by where he
wrote them. Selection is by rules on SOURCE and SCOPE, never by a model or by how a passage reads.

Usage (unchanged):
    librarian = SacksLibrarian()
    refs = librarian.get_psalm_references(23)
    markdown = librarian.format_for_research_bundle(refs, 23)
"""

import logging
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from src.data_sources import sacks_index
from src.data_sources.sefaria_reception import locate, tokens

logger = logging.getLogger(__name__)

SECTION_MAX_CHARS = 20000   # Ps 145 or 92 could otherwise carry 40K+; most psalms carry far less
DUPLICATE_OVERLAP = 0.6     # 5-gram overlap at which two items are the same text printed twice
BOOKS_PER_VERSE = 4         # Ps 23:4 alone has 10: he uses it as a motto, and 10 mottoes teach nothing

INTRO = ("Rabbi Lord Jonathan Sacks (1948–2020), Chief Rabbi of the United Hebrew Congregations of the "
         "Commonwealth from 1991 to 2013, wrote a running commentary on the prayer book and some forty "
         "books of Jewish thought. Below are his own words on this psalm, whole paragraphs and not "
         "summaries: first his prayer-book commentary on the psalm as the liturgy uses it, then passages "
         "from his books that quote it.")

WORK_LABELS = {
    "Rabbi Sacks on Siddur": "Koren Siddur",
    "Rabbi Sacks on Rosh HaShana Mahzor": "Koren Rosh HaShana Mahzor",
    "Rabbi Sacks on Yom Kippur Mahzor": "Koren Yom Kippur Mahzor",
    "The Jonathan Sacks Haggadah": "The Jonathan Sacks Haggadah",
}

# Session 391: the section `format_for_research_bundle` writes, and one `#### Reference N:` per
# excerpt inside it. The pipeline runners used to count every "Rabbi Sacks" / "Jonathan Sacks"
# string ANYWHERE in a reused bundle (the biography, the Research Summary's own
# "Rabbi Sacks references: 0" line, an echoes candidate), so Ps 77's methods page said
# "Rabbi Jonathan Sacks References Reviewed: 4" for a psalm with no Sacks excerpt at all.
_BUNDLE_SECTION_RE = re.compile(r"^## Rabbi Jonathan Sacks on Psalm \d+[ \t]*$(.*?)(?=^## |\Z)", re.M | re.S)
_BUNDLE_ENTRY_RE = re.compile(r"^#### Reference \d+:", re.M)


def count_references_in_bundle(markdown: str) -> int:
    """How many Sacks excerpts a research bundle carries: the `#### Reference N:` entries inside its
    `## Rabbi Jonathan Sacks on Psalm N` section; 0 when there is no such section."""
    section = _BUNDLE_SECTION_RE.search(markdown or "")
    return len(_BUNDLE_ENTRY_RE.findall(section.group(1))) if section else 0


@dataclass
class SacksReference:
    """One Sacks passage on a psalm."""
    kind: str                     # 'prayer book' | 'book'
    work: str                     # Sefaria title of the work
    section: str                  # where in the work (prayer-book rubric, or chapter/essay)
    ref: str                      # Sefaria ref of the comment / linked paragraph
    verses: List[int]             # the psalm's verses it is on
    scope: str                    # 'whole' | 'passage' | 'verse'
    text: str                     # his words, whole paragraphs
    source: str = "alignment"     # 'alignment' (prayer book) | 'link' | 'search'
    lang: str = "en"              # 'he': Sefaria has only the Hebrew translation of this book
    also: List[str] = field(default_factory=list)   # the same text printed elsewhere

    def to_dict(self) -> Dict:
        return asdict(self)


def _verse_label(verses: List[int], scope: str) -> str:
    if scope == "whole":
        return "on the whole psalm"
    if not verses:
        return ""
    if len(verses) == 1:
        return f"v. {verses[0]}"
    runs, start = [], verses[0]
    for a, b in zip(verses, verses[1:] + [None]):
        if b != a + 1:
            runs.append(f"{start}" if start == a else f"{start}–{a}")
            start = b
    return "vv. " + ", ".join(runs)


def _lemma_in_verse(lemma: str, verse_tokens: List[str]) -> bool:
    """At least two consecutive words of the comment's Hebrew lemma are in the verse (one word, such
    as לַמְנַצֵּחַ, is in too many verses to mean anything)."""
    lt = tokens(lemma)
    return len(lt) >= 2 and locate(verse_tokens, lt)[0] >= 2


def select(data: Dict, psalm_hebrew: List[str], max_chars: int = SECTION_MAX_CHARS) -> List[SacksReference]:
    """The rules. Prayer-book comments first (his commentary ON the psalm), then book passages by
    verse, round-robin, at most BOOKS_PER_VERSE per verse, until the budget is spent. A comment whose prayer-book paragraph holds only
    one verse of the psalm among other texts (a mosaic such as Pesukei DeZimra's Hodu) is about the
    mosaic, so it is kept only when it names the psalm, or when two words of its Hebrew lemma are in
    that verse and the paragraph is not some other psalm in full."""
    psalm = data["psalm"]
    n = data.get("verses") or len(psalm_hebrew)
    ptoks = [tokens(h) for h in psalm_hebrew]

    prayer: List[SacksReference] = []
    for c in data.get("liturgical", []):
        verses = [v for v in c["verses"] if 0 < v <= n] or c["verses"]
        scope = sacks_index.classify(verses, n, 0)
        named = re.search(rf"\bPsalms? {psalm}\b", c["text"])
        if scope == "verse" and not named:
            v = verses[0]
            if c.get("whole_elsewhere") or not (0 < v <= n and _lemma_in_verse(c.get("lemma", ""), ptoks[v - 1])):
                continue
        prayer.append(SacksReference("prayer book", c["work"], c["section"], c["ref"], verses, scope,
                                     c["text"], "alignment"))
    order = {"whole": 0, "passage": 1, "verse": 2}
    prayer.sort(key=lambda r: (order[r.scope], r.verses[:1], list(WORK_LABELS).index(r.work)
                               if r.work in WORK_LABELS else 9))

    books: List[SacksReference] = []
    for b in sorted(data.get("books", []), key=lambda b: (b["verses"][:1], b.get("lang", "en") != "en",
                                                         b["source"] != "link", b["ref"])):
        scope = sacks_index.classify(b["verses"], n, 0)
        books.append(SacksReference("book", b["work"], b["section"], b["ref"], b["verses"],
                                    "verse" if scope == "whole" else scope, b["text"], b["source"],
                                    lang=b.get("lang", "en")))

    def dedupe(items: List[SacksReference]) -> List[SacksReference]:
        kept: List[SacksReference] = []
        for it in items:
            twin = next((k for k in kept if sacks_index.overlap(k.text, it.text) >= DUPLICATE_OVERLAP), None)
            if twin:
                twin.also.append(it.ref)
                twin.verses = sorted(set(twin.verses) | set(it.verses))
            else:
                kept.append(it)
        return kept

    prayer, books = dedupe(prayer), dedupe(books)

    out, used = [], 0
    for r in prayer:
        if used + len(r.text) > max_chars and out:
            continue
        out.append(r)
        used += len(r.text)
    queues: Dict[int, List[SacksReference]] = {}
    for r in books:            # English before a Hebrew translation, linked before a search find
        q = queues.setdefault(r.verses[0] if r.verses else 0, [])
        if len(q) < BOOKS_PER_VERSE:
            q.append(r)
    while any(queues.values()):
        for v in sorted(queues):
            if queues[v]:
                r = queues[v].pop(0)
                if used + len(r.text) <= max_chars:
                    out.append(r)
                    used += len(r.text)
    return out


class SacksLibrarian:
    """Rabbi Sacks on a psalm, from the Sefaria-built cache (data/sacks/)."""

    def __init__(self, cache_dir: Optional[Path] = None, db_path: Optional[Path] = None,
                 max_chars: int = SECTION_MAX_CHARS, search: bool = True):
        self.cache_dir = Path(cache_dir) if cache_dir else sacks_index.CACHE_DIR
        self.db_path = Path(db_path) if db_path else sacks_index.DB_PATH
        self.max_chars = max_chars
        self.search = search

    def get_psalm_references(self, psalm_chapter: int) -> List[SacksReference]:
        try:
            data = sacks_index.harvest_psalm(psalm_chapter, cache_dir=self.cache_dir, db_path=self.db_path,
                                             search=self.search)
            hebrew = sacks_index.load_psalms(self.db_path).get(psalm_chapter, [])
        except Exception as e:   # a Sefaria outage must not sink the research bundle; it is logged
            logger.warning(f"[sacks] Psalm {psalm_chapter}: could not build the Sacks section ({e}); omitted")
            return []
        refs = select(data, hebrew, self.max_chars)
        logger.info(f"Sacks: {len(refs)} passage(s) for Psalm {psalm_chapter} "
                    f"({sum(r.kind == 'prayer book' for r in refs)} prayer book, "
                    f"{sum(r.kind == 'book' for r in refs)} books; "
                    f"{len(data.get('liturgical', []))} aligned comments, {len(data.get('books', []))} book passages found)")
        return refs

    @staticmethod
    def _title(r: SacksReference) -> str:
        where = _verse_label(r.verses, r.scope)
        if r.kind == "prayer book":
            rubric = r.section.split(", ")[-1] if r.section else ""
            head = f"{WORK_LABELS.get(r.work, r.work)}, {rubric}" if rubric else WORK_LABELS.get(r.work, r.work)
        else:
            head = f"{r.work.split(';')[0]}" + (f", {r.section}" if r.section else "")
        return f"{head} ({where})" if where else head

    def format_for_research_bundle(self, references: List[SacksReference], psalm_chapter: int) -> str:
        if not references:
            return ""
        lines = [f"## Rabbi Jonathan Sacks on Psalm {psalm_chapter}", "", INTRO, ""]
        n = 0
        for kind, heading in (("prayer book", "### In his prayer-book commentary"), ("book", "### In his books")):
            group = [r for r in references if r.kind == kind]
            if not group:
                continue
            lines += [heading, ""]
            for r in group:
                n += 1
                note = f"*{r.ref}*"
                if r.source == "search":
                    note += " *(a quotation found by phrase search; Sefaria does not link it)*"
                if r.lang == "he":
                    note += (" *Hebrew translation (Maggid); Sefaria lacks his English original, so an "
                             "English rendering of it is not his wording.*")
                if r.also:
                    note += f" *Also printed in: {'; '.join(r.also)}.*"
                lines += [f"#### Reference {n}: {self._title(r)}", note, "", r.text, ""]
        return "\n".join(lines).rstrip() + "\n"
