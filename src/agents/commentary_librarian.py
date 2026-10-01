"""
Commentary Librarian Agent

Fetches traditional Jewish commentaries on Psalms verses from Sefaria API.
Provides classical interpretations to put AI analysis in dialogue with established scholarship.

Supported Commentators:
- Rashi (Rabbi Shlomo Yitzchaki, 11th century, France)
- Ibn Ezra (Rabbi Abraham ibn Ezra, 12th century, Spain)
- Radak (Rabbi David Kimchi, 12th-13th century, Provence)
- Malbim (Rabbi Meir Leibush ben Yehiel Michel Wisser, 19th century, Ukraine)
- Meiri (Rabbi Menachem ben Solomon Meiri, 13th-14th century, Provence)
- Torah Temimah (Rabbi Baruch Epstein, 19th-20th century, Lithuania/Belarus)
- Romemot El (Alshich, Rabbi Moshe Alshich, 16th century, Safed) — homiletical
- Minchat Shai (Rabbi Yedidiah Shlomo Norzi, 16th-17th century, Mantua) — Masoretic text criticism
- Metzudat Zion (Altschuler, 18th century, Prague/Jaworów) — one-line word glossary
- Chomat Anakh (Chida, Rabbi Chaim Yosef David Azulai, 18th century, Jerusalem/Livorno)
- Malbim Beur Hamilot (the Malbim's word-level half, as distinct from `Malbim` above)

Usage:
    from src.agents.commentary_librarian import CommentaryLibrarian

    librarian = CommentaryLibrarian()

    # Fetch all available commentaries for a verse
    commentaries = librarian.fetch_commentaries(
        psalm=23,
        verse=1,
        commentators=['Rashi', 'Ibn Ezra']
    )

    # Process multiple verse requests
    requests = [
        {"psalm": 23, "verse": 1, "reason": "Rare metaphor"},
        {"psalm": 23, "verse": 4, "reason": "Perplexing imagery"}
    ]
    bundle = librarian.process_requests(requests)
"""

import json
import requests
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from html import unescape
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
SEFARIA_API_BASE = "https://www.sefaria.org/api"
RATE_LIMIT_DELAY = 0.5  # seconds between requests
# Session 391: one request per commentator per PSALM (was one per commentator per VERSE: 231 on
# Ps 77), each retried. The old 10 s timeout with no retry is how Session 387 silently lost
# Ibn Ezra on 77:9: a timeout returned None and the entry simply was not in the bundle.
REQUEST_TIMEOUT = 30  # seconds
MAX_ATTEMPTS = 4      # backoff 2, 4, 8 s between attempts
CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "sefaria_cache" / "commentary"

# ---------------------------------------------------------------------------
# Session 380: per-entry ceiling on a commentary quotation as rendered into the
# research bundle.
#
# This lives HERE, next to CommentaryEntry, rather than in research_assembler,
# because the dependency runs assembler -> librarian and both modules render
# these entries. A second hand-maintained copy is exactly the failure this
# project has now hit three times (S377's third duplicate pricing table, S379's
# hand-copied splice that had drifted for eight sessions). One definition.
#
# The cap was 400 chars and silently cut 23% of every commentary entry in the
# corpus (1,119 of 4,907). Measured against Sefaria on Psalm 73: 19,273
# characters discarded across 67 entries, median 222, worst 2,395 — Malbim on
# 73:17, the sanctuary pivot, i.e. the psalm's structural hinge.
#
# Tokens were never the argument. Restoring everything grows the median bundle
# by 2,877 chars and the worst by 19,273, and NO bundle in the corpus crosses
# the writer's 350,000-char trim ceiling as a result. The real cost was that
# the writer READ the fragments and threw them away: the Psalm 73 thinking
# capture shows it rating Malbim on v.15 and Torah Temimah on v.17 as Tier 1
# and then discarding both as "cut off mid-thought". We paid for the fetch,
# paid input tokens on the fragment, and paid thinking tokens on the writer
# working out that it was broken.
#
# 2,000 recovers 66 of Psalm 73's 67 truncated entries whole while still
# bounding the pathological case (a Torah Temimah entry can quote an entire
# Talmudic sugya). Raise it if real entries are seen hitting the ceiling — the
# marker is what makes that visible.
COMMENTARY_ENTRY_MAX_CHARS = 2000

# A bare "..." is indistinguishable from an ellipsis the commentator wrote, so
# the writer had to INFER that the text was cut rather than being told. Say it.
COMMENTARY_TRUNCATION_MARKER = " […truncated]"


def truncate_commentary(text: str, max_chars: int = COMMENTARY_ENTRY_MAX_CHARS) -> str:
    """Cap one commentary quotation, marking the cut so the reader knows it happened.

    Returns `text` unchanged when it fits (including when it is empty or None-ish).
    The marker is deliberately explicit: see COMMENTARY_TRUNCATION_MARKER.
    """
    if not text or len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + COMMENTARY_TRUNCATION_MARKER

# Supported commentators (Sefaria text names)
COMMENTATORS = {
    "Rashi": "Rashi on Psalms",
    "Ibn Ezra": "Ibn Ezra on Psalms",
    "Radak": "Radak on Psalms",
    # METZUDAT DAVID WAS DROPPED IN SESSION 373 (author's call), and the corpus backs
    # it. Measured over the 71 production guides, dossier entries SUPPLIED vs names
    # actually cited in the finished commentary:
    #
    #     Radak           636 supplied -> 444 cited (70%)
    #     Rashi           470            -> 365 (78%)
    #     Ibn Ezra        627            -> 241 (38%)
    #     Malbim          452            -> 210 (46%)
    #     Meiri           622            -> 107 (17%)
    #     Torah Temimah   163            ->  72 (44%)
    #     Metzudat David  610            ->  60 (10%)   <- least used, by 7x
    #
    # It was the THIRD most supplied commentator and the least used one — under one
    # citation per guide from a supply the size of Ibn Ezra's. The reason is
    # structural, not accidental: Metzudat David is running paraphrase by design —
    # the thing RULE 8b exists to reject — so it almost never clears the admission
    # test. (RULE 8b used to name it as the example; that naming is gone too.) Fetching it
    # cost a Sefaria round-trip per verse and put ~8.6 dead glosses per psalm into an
    # unranked dossier the writer has to read past — the exact dilution Session 370
    # traced from coverage pressure to inert citation.
    #
    # NOT A CONTRADICTION with Metzudat Zion below: the Metzudot are two separate
    # works by the same family. Metzudat DAVID is the running paraphrase (dropped);
    # Metzudat ZION is the glossary — a bare definition of one hard word, ~65 chars,
    # on half the verses. The paraphrase is what failed the admission test; a word
    # gloss is a different thing and is cheap.
    "Malbim": "Malbim on Psalms",
    "Meiri": "Meiri on Psalms",
    "Torah Temimah": "Torah Temimah on Psalms",

    # --- Added Session 373 (author's request) ----------------------------------
    # Sefaria index names verified live before wiring; coverage measured over 36
    # verses (all of Ps 71, plus Ps 23:1-6 and Ps 1:1-6). All Hebrew-only — none
    # of these five carries an English translation on Sefaria, so the writer is
    # reading and rendering them itself.
    #
    #   Romemot El           100% of verses, ~763 Hebrew chars  (the big one)
    #   Minchat Shai          58%,           ~598
    #   Metzudat Zion         50%,            ~65
    #   Malbim Beur Hamilot   36%,           ~119
    #   Chomat Anakh          19%,           ~838
    #
    # Note the shape: Chomat Anakh and Minchat Shai are naturally SELECTIVE — they
    # speak only where they have something to say, which is why they cost little.
    # Romemot El is the opposite and is on every verse; it is the one that can
    # crowd a dossier, which is why RULE 8b now characterises it explicitly.
    "Romemot El": "Romemot El on Psalms",              # Alshich — homiletical/derash
    "Minchat Shai": "Minchat Shai on Psalms",          # Masoretic spelling, vocalization, accents
    "Metzudat Zion": "Metzudat Zion on Psalms",        # bare lexical glosses (the Metzudot's glossary half)
    "Chomat Anakh": "Chomat Anakh on Psalms",          # Chida — eclectic, kabbalistic-leaning
    "Malbim Beur Hamilot": "Malbim Beur Hamilot on Psalms",  # Malbim on the WORDS; `Malbim` above is on the matter
}


# Session 391: the text VERSIONS, pinned. They are exactly what Sefaria served by default on
# 2026-10-01, i.e. what every production bundle so far has contained. Unpinned, a change of
# default on Sefaria's side would change our text silently (it has happened to Psalms itself:
# the default English is now the 2023 JPS Gender-Sensitive Edition). (Hebrew title, English
# title or None). If a pinned title disappears, the fetch falls back to Sefaria's default for
# that language and logs a WARNING naming both.
# English None = the commentator has no complete English, only PARTIAL translations (community,
# Feuer's Jerusalem Anthology, a Radak translation) covering scattered verses. The old per-verse
# request got whichever of them had the verse, and production bundles carry those (Ibn Ezra,
# Radak and Malbim on Ps 76:3), MERGED comment by comment (Ibn Ezra on 1:1: one comment from
# Wikisource, six from the community translation). So for these the fetch takes ALL English
# versions and, comment by comment, the first in Sefaria's order that has it: verified identical
# to the old output on every verse of Pss 1, 23, 27, 76 and 77 (660 verse-commentator pairs).
PINNED_VERSIONS: Dict[str, Tuple[str, Optional[str]]] = {
    "Rashi": ("Sefaria vocalized edition",
              "The Judaica Press complete Tanach with Rashi, translated by A. J. Rosenberg"),
    "Ibn Ezra": ("Ibn Ezra on Psalms -- Daat", None),
    "Radak": ("Derekh Mesilah, Furth 1843", None),
    "Malbim": ("On Your Way", None),
    "Meiri": ("Jerusalem, 1936", None),
    "Torah Temimah": ("On Your Way", None),
    "Romemot El": ("Romemot El, Warsaw 1875", None),
    "Minchat Shai": ("Minchat Shai", None),
    "Metzudat Zion": ("On Your Way", None),
    "Chomat Anakh": ("Chomat Anakh, Jerusalem 1965", None),
    "Malbim Beur Hamilot": ("On Your Way - new", None),
}


def _join_segments(x) -> str:
    """One verse's comments as the librarian has always rendered them: each segment cleaned, empty
    ones dropped, joined with ' | '. Nested lists are flattened (the old per-verse code raised on
    them and lost the entry)."""
    if isinstance(x, list):
        parts = [_join_segments(i) for i in x]
        return ' | '.join(p for p in parts if p)
    return clean_html_text(x) if x else ""


# How each source is NAMED in the finished guide's methodological summary.
# `commentary_counts` is keyed by the short lookup name above, which is fine for
# Rashi and Radak and useless for the rest: a reader who meets "Chomat Anakh (5)"
# in the bibliography has no way to know that is the Chida. Works whose title is
# not their author's name get the author appended; everything else is left alone.
COMMENTATOR_DISPLAY = {
    "Romemot El": "Romemot El (Alshich)",
    "Chomat Anakh": "Chomat Anakh (Chida)",
    "Minchat Shai": "Minchat Shai (Norzi)",
    "Metzudat Zion": "Metzudat Zion (Altschuler)",
    "Torah Temimah": "Torah Temimah (Epstein)",
}


def display_name(commentator: str) -> str:
    """Bibliography label for a commentator key (see COMMENTATOR_DISPLAY)."""
    return COMMENTATOR_DISPLAY.get(commentator, commentator)


def clean_html_text(text: str) -> str:
    """
    Remove HTML markup from commentary text.

    Args:
        text: Raw text with HTML tags and entities

    Returns:
        Clean text with HTML removed
    """
    if not text:
        return text

    # Remove HTML tags (but keep their content)
    text = re.sub(r'<[^>]+>', '', text)

    # Convert HTML entities
    text = unescape(text)

    # Clean up extra whitespace
    text = ' '.join(text.split())

    return text


@dataclass
class CommentaryEntry:
    """Represents a single commentary on a verse."""
    commentator: str          # Name (e.g., "Rashi")
    psalm: int                # Psalm number
    verse: int                # Verse number
    hebrew: str               # Hebrew commentary text
    english: str              # English translation
    reference: str            # Sefaria reference (e.g., "Rashi on Psalms 23:1:1")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "commentator": self.commentator,
            "psalm": self.psalm,
            "verse": self.verse,
            "hebrew": self.hebrew,
            "english": self.english,
            "reference": self.reference
        }


@dataclass
class CommentaryBundle:
    """Bundle of commentaries for a verse."""
    psalm: int
    verse: int
    reason: str                           # Why this verse needs commentary
    commentaries: List[CommentaryEntry]   # All fetched commentaries

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "psalm": self.psalm,
            "verse": self.verse,
            "reason": self.reason,
            "commentaries": [c.to_dict() for c in self.commentaries]
        }

    def to_markdown(self) -> str:
        """Format as markdown for LLM consumption."""
        lines = [
            f"### Psalms {self.psalm}:{self.verse}",
            f"**Reason for commentary request**: {self.reason}",
            ""
        ]

        # Session 380: this path is NOT the production bundle — that is
        # ResearchAssembler._generate_markdown, which owns
        # COMMENTARY_ENTRY_MAX_CHARS. `format_bundle_as_markdown` has no callers
        # outside this module's own main(). Kept in step with the live cap
        # anyway so a debug dump does not misrepresent what the writer sees.
        for comm in self.commentaries:
            lines.append(f"#### {comm.commentator}")
            lines.append(f"**Hebrew**: {truncate_commentary(comm.hebrew)}")
            lines.append(f"**English**: {truncate_commentary(comm.english)}")
            lines.append("")

        return "\n".join(lines)


class CommentaryLibrarian:
    """
    Fetches traditional Jewish commentaries on Psalms verses.

    This agent is NOT an LLM - it's a pure Python script that queries Sefaria API.
    """

    def __init__(self, rate_limit_delay: float = RATE_LIMIT_DELAY,
                 cache_dir: Optional[Path] = None, use_cache: bool = True):
        """
        Initialize Commentary Librarian.

        Args:
            rate_limit_delay: Seconds to wait between API requests
        """
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Psalms-AI-Commentary/1.0 (Educational Research)'
        })
        self.cache_dir = Path(cache_dir) if cache_dir else CACHE_DIR
        self.use_cache = use_cache
        self._chapters: Dict[Tuple[str, int], Dict[int, CommentaryEntry]] = {}

    def _wait_for_rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params=None) -> Optional[Dict]:
        """A rate-limited GET with retries. Returns None on a 404 (Sefaria has no such text, e.g. a
        commentator silent on a whole psalm); raises after MAX_ATTEMPTS on anything else."""
        url = f"{SEFARIA_API_BASE}/{endpoint}"
        for attempt in range(1, MAX_ATTEMPTS + 1):
            self._wait_for_rate_limit()
            try:
                response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, ValueError) as e:
                status = getattr(getattr(e, 'response', None), 'status_code', None)
                if status is not None and 400 <= status < 500 and status != 429:
                    raise
                if attempt == MAX_ATTEMPTS:
                    raise
                wait = 2 ** attempt
                logger.warning(f"Sefaria request failed ({e}); retry {attempt}/{MAX_ATTEMPTS - 1} in {wait}s: {endpoint}")
                time.sleep(wait)

    def _cache_file(self, commentator: str, psalm: int) -> Path:
        return self.cache_dir / f"{commentator.replace(' ', '_')}" / f"psalm_{psalm:03d}.json"

    def fetch_chapter(self, psalm: int, commentator: str) -> Dict[int, CommentaryEntry]:
        """Every entry `commentator` has on `psalm`, keyed by verse: one Sefaria request (pinned
        versions), cached in memory and on disk. A verse the commentator passes over is simply
        absent. A fetch that fails after all retries is logged as a WARNING naming the lost
        commentator and returns {} (the bundle then lacks him, visibly in the log)."""
        key = (commentator, psalm)
        if key in self._chapters:
            return self._chapters[key]
        index = COMMENTATORS[commentator]
        he_title, en_title = PINNED_VERSIONS[commentator]
        cache_file = self._cache_file(commentator, psalm)
        raw = None
        if self.use_cache and cache_file.exists():
            try:
                cached = json.loads(cache_file.read_text(encoding='utf-8'))
                if cached.get('pinned') == [he_title, en_title]:
                    raw = cached
            except (OSError, ValueError):
                raw = None
        if raw is None:
            raw = self._fetch_chapter_raw(index, psalm, commentator, he_title, en_title)
            if raw is None:
                self._chapters[key] = {}
                return {}
            if self.use_cache:
                try:
                    cache_file.parent.mkdir(parents=True, exist_ok=True)
                    cache_file.write_text(json.dumps(raw, ensure_ascii=False), encoding='utf-8')
                except OSError as e:
                    logger.warning(f"Could not write commentary cache {cache_file}: {e}")
        he, en = raw.get('he') or [], raw.get('en') or []
        entries: Dict[int, CommentaryEntry] = {}
        for i in range(max(len(he), len(en))):
            hebrew = _join_segments(he[i]) if i < len(he) else ""
            english = _join_segments(en[i]) if i < len(en) else ""
            if hebrew or english:
                entries[i + 1] = CommentaryEntry(commentator=commentator, psalm=psalm, verse=i + 1,
                                                 hebrew=hebrew, english=english,
                                                 reference=f"{index} {psalm}:{i + 1}")
        self._chapters[key] = entries
        return entries

    def _fetch_chapter_raw(self, index: str, psalm: int, commentator: str,
                           he_title: str, en_title: Optional[str]) -> Optional[Dict]:
        endpoint = f"v3/texts/{index.replace(' ', '_')}.{psalm}"
        wanted = [('he', he_title)] + ([('en', en_title)] if en_title else [])
        try:
            params = [('version', f"{'hebrew' if l == 'he' else 'english'}|{t}") for l, t in wanted]
            if not en_title:
                params.append(('version', 'english|all'))
            data = self._make_request(endpoint, params=params)
            if data is None:
                logger.info(f"Sefaria has no {index} on Psalm {psalm} (404)")
                return {'pinned': [he_title, en_title], 'he': [], 'en': []}
            got = {}
            partial_en = []
            for v in data.get('versions', []):
                if v.get('language') == 'en' and not en_title:
                    partial_en.append(v)
                elif v.get('language') not in got:
                    got[v.get('language')] = v
            for lang, title in wanted:
                if lang not in got:   # the pinned title is gone: take Sefaria's default, loudly
                    logger.warning(f"[commentary] pinned {lang} version {title!r} of {index} is unavailable; "
                                   f"falling back to Sefaria's default {lang} version")
                    alt = self._make_request(endpoint, params=[('version', 'hebrew' if lang == 'he' else 'english')])
                    for v in (alt or {}).get('versions', []):
                        if v.get('language') == lang:
                            got[lang] = v
                            logger.warning(f"[commentary] {index} Psalm {psalm}: using {v.get('versionTitle')!r}")
            en_text = (got.get('en') or {}).get('text') or []
            en_sources = {}
            if partial_en:   # comment by comment, the first partial English version that has it
                def seg(v, i, j):
                    t = v.get('text') or []
                    if i >= len(t): return None
                    verse = t[i] if isinstance(t[i], list) else [t[i]]
                    return verse[j] if j < len(verse) and _join_segments(verse[j]) else None
                n = max(len(v.get('text') or []) for v in partial_en)
                en_text = []
                for i in range(n):
                    width = max((len(v['text'][i]) if isinstance(v['text'][i], list) else 1)
                                for v in partial_en if i < len(v.get('text') or []))
                    merged, used = [], []
                    for j in range(width):
                        pick = next((v for v in partial_en if seg(v, i, j) is not None), None)
                        merged.append(seg(pick, i, j) if pick else "")
                        if pick and pick.get('versionTitle') not in used:
                            used.append(pick.get('versionTitle'))
                    en_text.append(merged)
                    if used:
                        en_sources[str(i + 1)] = used
            return {'pinned': [he_title, en_title],
                    'he': (got.get('he') or {}).get('text') or [],
                    'en': en_text,
                    'versions': {l: (got.get(l) or {}).get('versionTitle') for l, _ in wanted},
                    'partial_english_by_verse': en_sources}
        except Exception as e:
            logger.warning(f"[commentary] {commentator} on Psalm {psalm}: Sefaria failed after {MAX_ATTEMPTS} "
                           f"attempts ({e}); {commentator} is MISSING from this bundle")
            return None

    def fetch_commentary(self,
                         psalm: int,
                         verse: int,
                         commentator: str = "Rashi") -> Optional[CommentaryEntry]:
        """One commentator on one verse, from the psalm's cached chapter (see `fetch_chapter`).
        None when he has nothing on the verse, or his chapter could not be fetched."""
        if commentator not in COMMENTATORS:
            logger.warning(f"Unknown commentator: {commentator}")
            return None
        return self.fetch_chapter(psalm, commentator).get(verse)

    def fetch_commentaries(self,
                          psalm: int,
                          verse: int,
                          commentators: Optional[List[str]] = None) -> List[CommentaryEntry]:
        """
        Fetch multiple commentaries on a verse.

        Args:
            psalm: Psalm number (1-150)
            verse: Verse number
            commentators: List of commentator names (default: all available)

        Returns:
            List of CommentaryEntry objects (may be empty)
        """
        if commentators is None:
            commentators = list(COMMENTATORS.keys())

        entries = []
        for commentator in commentators:
            entry = self.fetch_commentary(psalm, verse, commentator)
            if entry:
                entries.append(entry)

        return entries

    def process_requests(self,
                        requests: List[Dict[str, Any]],
                        commentators: Optional[List[str]] = None) -> List[CommentaryBundle]:
        """
        Process multiple commentary requests.

        Args:
            requests: List of request dicts with keys:
                     - psalm (int): Psalm number
                     - verse (int): Verse number
                     - reason (str): Why this verse needs commentary
            commentators: List of commentator names (default: all 6 available commentators)

        Returns:
            List of CommentaryBundle objects
        """
        if commentators is None:
            # Default to all available commentators for comprehensive coverage
            commentators = list(COMMENTATORS.keys())

        logger.info(f"Processing {len(requests)} commentary requests...")

        bundles = []
        for req in requests:
            psalm = req.get('psalm')
            verse = req.get('verse')
            reason = req.get('reason', 'Requested by Scholar-Researcher')

            if not psalm or not verse:
                logger.warning(f"Invalid request (missing psalm or verse): {req}")
                continue

            commentaries = self.fetch_commentaries(psalm, verse, commentators)

            bundle = CommentaryBundle(
                psalm=psalm,
                verse=verse,
                reason=reason,
                commentaries=commentaries
            )
            bundles.append(bundle)

        logger.info(f"Fetched {sum(len(b.commentaries) for b in bundles)} commentaries total")
        return bundles

    def format_bundle_as_markdown(self, bundles: List[CommentaryBundle]) -> str:
        """
        Format commentary bundles as markdown for LLM consumption.

        Args:
            bundles: List of CommentaryBundle objects

        Returns:
            Formatted markdown string
        """
        if not bundles:
            return "No commentaries requested.\n"

        lines = [
            "# Traditional Commentaries",
            "",
            "The following commentaries provide classical interpretations of verses "
            "identified by the Scholar-Researcher as particularly interesting or perplexing.",
            ""
        ]

        for bundle in bundles:
            lines.append(bundle.to_markdown())

        return "\n".join(lines)


def main():
    """Command-line interface for testing the Commentary Librarian."""
    import argparse
    import sys
    import json

    # Ensure UTF-8 encoding for Hebrew text on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description='Fetch traditional commentaries on Psalms verses')
    parser.add_argument('--psalm', type=int, required=True, help='Psalm number (1-150)')
    parser.add_argument('--verse', type=int, required=True, help='Verse number')
    parser.add_argument('--commentator', type=str, default='Rashi',
                       choices=list(COMMENTATORS.keys()),
                       help='Commentator name')
    parser.add_argument('--all', action='store_true',
                       help='Fetch all available commentators')
    parser.add_argument('--format', choices=['json', 'markdown'], default='markdown',
                       help='Output format')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    librarian = CommentaryLibrarian()

    if args.all:
        commentaries = librarian.fetch_commentaries(args.psalm, args.verse)
    else:
        commentary = librarian.fetch_commentary(args.psalm, args.verse, args.commentator)
        commentaries = [commentary] if commentary else []

    if not commentaries:
        print(f"No commentaries found for Psalms {args.psalm}:{args.verse}")
        return

    if args.format == 'json':
        print(json.dumps([c.to_dict() for c in commentaries], indent=2, ensure_ascii=False))
    else:
        bundle = CommentaryBundle(
            psalm=args.psalm,
            verse=args.verse,
            reason="Command-line test",
            commentaries=commentaries
        )
        print(bundle.to_markdown())


if __name__ == '__main__':
    main()
