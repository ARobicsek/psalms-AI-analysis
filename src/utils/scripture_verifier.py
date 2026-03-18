"""
Scripture Citation Verifier — Psalm Commentary Quality Control

Session 308: Verifies that Hebrew quotations paired with parenthetical
book/chapter/verse citations match the actual text in tanakh.db.

This is a zero-LLM-cost verification step that catches misquoted
biblical verses (e.g., omitted words, garbled text).

Usage:
    from src.utils.scripture_verifier import verify_citations, format_verification_report
    issues = verify_citations(text, db_path="database/tanakh.db")
    print(format_verification_report(issues))
"""

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
load_dotenv()

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CitationIssue:
    """A single citation verification failure."""
    quoted_hebrew: str        # The Hebrew text as quoted in commentary
    citation_ref: str         # The parenthetical citation, e.g. "Ex 20:7"
    actual_hebrew: str        # The actual verse text from tanakh.db (empty if not found)
    location_hint: str        # Approximate location in the document (verse header or line #)
    issue_type: str           # NOT_FOUND | NOT_SUBSTRING | BOOK_NOT_IN_DB
    line_number: int = 0      # 1-indexed line number where the citation appears
    normalized_quoted: str = ""   # Post-normalization quoted text (for debugging)
    normalized_actual: str = ""   # Post-normalization actual text (for debugging)


# ---------------------------------------------------------------------------
# Book name mappings  (abbreviation → tanakh.db book_name)
# ---------------------------------------------------------------------------

# Standard abbreviation → full DB name
_BOOK_ABBREVS = {
    # Torah
    "Gen": "Genesis", "Ge": "Genesis",
    "Ex": "Exodus", "Exod": "Exodus",
    "Lev": "Leviticus",
    "Num": "Numbers", "Nm": "Numbers",
    "Deut": "Deuteronomy", "Dt": "Deuteronomy",
    # Prophets
    "Josh": "Joshua",
    "Judg": "Judges", "Jdg": "Judges",
    "Isa": "Isaiah", "Is": "Isaiah",
    "Jer": "Jeremiah",
    "Ezek": "Ezekiel", "Eze": "Ezekiel",
    "Hos": "Hosea",
    "Am": "Amos",
    "Obad": "Obadiah", "Ob": "Obadiah",
    "Mic": "Micah",
    "Nah": "Nahum",
    "Hab": "Habakkuk",
    "Zeph": "Zephaniah",
    "Hag": "Haggai",
    "Zech": "Zechariah",
    "Mal": "Malachi",
    # Writings
    "Ps": "Psalms", "Pss": "Psalms", "Psa": "Psalms", "Psalm": "Psalms",
    "Prov": "Proverbs", "Pr": "Proverbs",
    "Song": "Song of Songs",
    "Lam": "Lamentations",
    "Eccl": "Ecclesiastes", "Qoh": "Ecclesiastes",
    "Esth": "Esther", "Est": "Esther",
    "Dan": "Daniel",
    "Neh": "Nehemiah",
    # Full names that match DB directly
    "Genesis": "Genesis",
    "Exodus": "Exodus",
    "Leviticus": "Leviticus",
    "Numbers": "Numbers",
    "Deuteronomy": "Deuteronomy",
    "Joshua": "Joshua",
    "Judges": "Judges",
    "Isaiah": "Isaiah",
    "Jeremiah": "Jeremiah",
    "Ezekiel": "Ezekiel",
    "Hosea": "Hosea",
    "Amos": "Amos",
    "Obadiah": "Obadiah",
    "Joel": "Joel",
    "Jonah": "Jonah",
    "Micah": "Micah",
    "Nahum": "Nahum",
    "Habakkuk": "Habakkuk",
    "Zephaniah": "Zephaniah",
    "Haggai": "Haggai",
    "Zechariah": "Zechariah",
    "Malachi": "Malachi",
    "Psalms": "Psalms",
    "Proverbs": "Proverbs",
    "Job": "Job",
    "Song of Songs": "Song of Songs",
    "Ruth": "Ruth",
    "Lamentations": "Lamentations",
    "Ecclesiastes": "Ecclesiastes",
    "Esther": "Esther",
    "Daniel": "Daniel",
    "Ezra": "Ezra",
    "Nehemiah": "Nehemiah",
}

# Books that need I/II prefix handling
_NUMBERED_BOOK_ABBREVS = {
    "Sam": "Samuel",
    "Samuel": "Samuel",
    "Kgs": "Kings",
    "Kings": "Kings",
    "Chr": "Chronicles",
    "Chronicles": "Chronicles",
    "Chron": "Chronicles",
}


def _resolve_book_name(raw_book: str) -> Optional[str]:
    """
    Resolve a citation book reference to the tanakh.db book_name.

    Handles:
      - Direct abbreviation lookup (Ex → Exodus)
      - Numbered books (1 Sam → I Samuel, 2 Kgs → II Kings, I Chr → I Chronicles)
    """
    raw = raw_book.strip()

    # Direct lookup first
    if raw in _BOOK_ABBREVS:
        return _BOOK_ABBREVS[raw]

    # Check for numbered prefix: "1 Sam", "2 Kgs", "I Sam", "II Kings", etc.
    numbered_match = re.match(
        r'^(1|2|I{1,2}|i{1,2})\s*(.+)$', raw
    )
    if numbered_match:
        num_str = numbered_match.group(1).upper()
        base = numbered_match.group(2).strip()

        # Normalize number prefix
        if num_str in ("1", "I"):
            prefix = "I"
        elif num_str in ("2", "II"):
            prefix = "II"
        else:
            return None

        # Look up the base name
        if base in _NUMBERED_BOOK_ABBREVS:
            return f"{prefix} {_NUMBERED_BOOK_ABBREVS[base]}"
        # Try direct lookup too (e.g., "1 Samuel" → already in _BOOK_ABBREVS as "I Samuel")
        full_try = f"{prefix} {base}"
        if full_try in _BOOK_ABBREVS:
            return _BOOK_ABBREVS[full_try]

    return None


# ---------------------------------------------------------------------------
# Hebrew text normalization for comparison
# ---------------------------------------------------------------------------

# Cantillation mark range (U+0591–U+05AF) — strip these
# Vowel point range (U+05B0–U+05BD) — KEEP these for comparison
# Meteg (U+05BD) — keep
# Additional marks: U+05BE (maqaf), U+05BF (rafe), U+05C0 (paseq),
#                   U+05C1 (shin dot), U+05C2 (sin dot), U+05C3 (sof pasuq),
#                   U+05C4-U+05C5, U+05C7 (qamats qatan)

_CANTILLATION_RANGE = set(range(0x0591, 0x05B0))  # trope/cantillation marks

# Divine name normalization patterns
_DIACRITICS_CLASS = '[\u05B0-\u05BD\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7]*'
_DIVINE_NAME_PATTERNS = [
    (re.compile(r'ה[׳\']'), 'יהוה'),            # ה׳ or ה' → יהוה
    # Full Tetragrammaton with any vowels → consonantal יהוה
    (re.compile(r'י' + _DIACRITICS_CLASS + r'ה' + _DIACRITICS_CLASS +
                r'ו' + _DIACRITICS_CLASS + r'ה'), 'יהוה'),
    (re.compile(r'אלק'), 'אלה'),                  # אלקים→אלהים, אלקי→אלהי, etc.
    (re.compile(r'צבקות'), 'צבאות'),               # reverential form → standard
]


def _normalize_hebrew(text: str) -> str:
    """
    Normalize Hebrew text for comparison:
    1. Strip cantillation/trope marks (U+0591–U+05AF)
    2. Normalize divine names
    3. Strip maqaf (־), sof-pasuq (׃), geresh (׳), paseq (׀)
    4. Collapse whitespace
    """
    result = []
    for ch in text:
        cp = ord(ch)
        # Skip cantillation marks
        if cp in _CANTILLATION_RANGE:
            continue
        # Skip meteg (stress mark, doesn't affect reading)
        if cp == 0x05BD:
            continue
        # Skip sof-pasuq
        if cp == 0x05C3:
            continue
        # Skip paseq
        if cp == 0x05C0:
            continue
        # Replace maqaf with space
        if cp == 0x05BE:
            result.append(' ')
            continue
        result.append(ch)

    normalized = ''.join(result)

    # Apply divine name normalization
    for pattern, replacement in _DIVINE_NAME_PATTERNS:
        normalized = pattern.sub(replacement, normalized)

    # Strip geresh characters used in abbreviations
    normalized = normalized.replace('׳', '').replace("'", '')

    # Collapse whitespace and strip
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    return normalized


# All Hebrew diacritics: vowels (U+05B0–U+05BD), shin/sin dots (U+05C1–U+05C2),
# dagesh (U+05BC), rafe (U+05BF), qamats qatan (U+05C7), upper/lower dots (U+05C4-U+05C5)
_ALL_DIACRITICS = set(range(0x05B0, 0x05BE)) | {0x05BF, 0x05C1, 0x05C2, 0x05C4, 0x05C5, 0x05C7}


def _strip_to_consonants(text: str) -> str:
    """
    Strip ALL diacritics from Hebrew text, leaving only consonants.
    Used as a fallback comparison when vowel pointing differs.
    Also applies divine name normalization and strips maqaf/sof-pasuq.
    """
    result = []
    for ch in text:
        cp = ord(ch)
        # Skip cantillation
        if cp in _CANTILLATION_RANGE:
            continue
        # Skip vowels and diacritics
        if cp in _ALL_DIACRITICS:
            continue
        # Skip sof-pasuq, paseq
        if cp in (0x05C3, 0x05C0):
            continue
        # Replace maqaf with space
        if cp == 0x05BE:
            result.append(' ')
            continue
        result.append(ch)

    consonantal = ''.join(result)

    # Apply divine name normalization (on consonants)
    for pattern, replacement in _DIVINE_NAME_PATTERNS:
        consonantal = pattern.sub(replacement, consonantal)

    # Strip geresh
    consonantal = consonantal.replace('׳', '').replace("'", '')

    # Strip non-Hebrew punctuation (semicolons, colons, etc. that
    # Commentary inserts but the Masoretic text does not have)
    consonantal = re.sub(r'[;:,\.!?"()\[\]{}]', '', consonantal)

    # Collapse whitespace
    consonantal = re.sub(r'\s+', ' ', consonantal).strip()

    return consonantal


def _is_hebrew_char(ch: str) -> bool:
    """Check if a character is in the Hebrew Unicode block."""
    cp = ord(ch)
    return (0x0590 <= cp <= 0x05FF) or (0xFB1D <= cp <= 0xFB4F)


def _is_hebrew_text(text: str) -> bool:
    """Check if a string contains Hebrew characters."""
    return any(_is_hebrew_char(ch) for ch in text)


# ---------------------------------------------------------------------------
# Citation extraction regex
# ---------------------------------------------------------------------------

# Pattern: Hebrew text followed by a parenthetical citation
# We need to capture:
#   1. A stretch of Hebrew text (may include spaces, vowels, maqaf, etc.)
#   2. Followed by a parenthetical like (Ex 20:7) or (Genesis 19:25)
#
# The Hebrew text may be:
#   - Wrapped in quotes: "לֹא תִשָּׂא..." or "לֹא תִשָּׂא..."
#   - A standalone inline Hebrew fragment
#
# Citation format: (Book Ch:V) or (Book Ch:V–W) for verse ranges
#
# Strategy: find citation parentheticals first, then look backward for Hebrew text.

_CITATION_PAREN_RE = re.compile(
    r'\('
    r'((?:1|2|I{1,2})?\s*'                      # optional numbered prefix
    r'(?:Gen(?:esis)?|Ex(?:od(?:us)?)?|Lev(?:iticus)?|Num(?:bers)?|'
    r'Deut(?:eronomy)?|Josh(?:ua)?|Judg(?:es)?|'
    r'(?:1|2|I{1,2})\s*(?:Sam(?:uel)?|Kgs|Kings?|Chr(?:on(?:icles)?)?)|'
    r'Isa(?:iah)?|Jer(?:emiah)?|Ezek(?:iel)?|'
    r'Hos(?:ea)?|Joel|Am(?:os)?|Obad(?:iah)?|Jonah?|Mic(?:ah)?|'
    r'Nah(?:um)?|Hab(?:akkuk)?|Zeph(?:aniah)?|Hag(?:gai)?|'
    r'Zech(?:ariah)?|Mal(?:achi)?|'
    r'Ps(?:s|a(?:lms?)?)?|Prov(?:erbs)?|Job|'
    r'Song(?:\s+of\s+Songs)?|Ruth|Lam(?:entations)?|'
    r'Eccl(?:esiastes)?|Qoh|Esth(?:er)?|Dan(?:iel)?|'
    r'Ezra|Neh(?:emiah)?)'
    r')\s+'                                       # book name + space
    r'(\d+)'                                      # chapter number
    r':'
    r'(\d+)'                                      # verse number
    r'(?:\s*[–\-]\s*\d+)?'                        # optional verse range (ignored)
    r'\)',
    re.IGNORECASE
)


# Pattern C: Hebrew text INSIDE the citation parenthetical, after a colon.
# e.g.  (Gen 27:36: עֲקָבַנִי זֶה פַעֲמַיִם, "he has supplanted me...")
# This is a separate regex so the existing Pattern A/B logic is untouched.
_CITATION_INLINE_RE = re.compile(
    r'\('
    r'((?:1|2|I{1,2})?\s*'                      # optional numbered prefix
    r'(?:Gen(?:esis)?|Ex(?:od(?:us)?)?|Lev(?:iticus)?|Num(?:bers)?|'
    r'Deut(?:eronomy)?|Josh(?:ua)?|Judg(?:es)?|'
    r'(?:1|2|I{1,2})\s*(?:Sam(?:uel)?|Kgs|Kings?|Chr(?:on(?:icles)?)?)|'
    r'Isa(?:iah)?|Jer(?:emiah)?|Ezek(?:iel)?|'
    r'Hos(?:ea)?|Joel|Am(?:os)?|Obad(?:iah)?|Jonah?|Mic(?:ah)?|'
    r'Nah(?:um)?|Hab(?:akkuk)?|Zeph(?:aniah)?|Hag(?:gai)?|'
    r'Zech(?:ariah)?|Mal(?:achi)?|'
    r'Ps(?:s|a(?:lms?)?)?|Prov(?:erbs)?|Job|'
    r'Song(?:\s+of\s+Songs)?|Ruth|Lam(?:entations)?|'
    r'Eccl(?:esiastes)?|Qoh|Esth(?:er)?|Dan(?:iel)?|'
    r'Ezra|Neh(?:emiah)?)'
    r')\s+'                                       # book name + space
    r'(\d+)'                                      # chapter number
    r':'
    r'(\d+)'                                      # verse number
    r'(?:\s*[–\-]\s*\d+)?'                        # optional verse range
    r':\s*'                                        # colon + space separating ref from content
    r'([^)]+)'                                     # content inside parens (Hebrew + optional English)
    r'\)',
    re.IGNORECASE
)

# Pattern D: Inline forward citation — book reference NOT in parentheses,
# followed by Hebrew text.  Matches patterns like:
#   2 Samuel 7:29 — וּבָרֵךְ אֶת עַבְדְּךָ ...
#   Psalm 55:13–14, ... כִּי לֹא אוֹיֵב ...
# The regex captures the reference; Hebrew extraction uses a forward scan.
_BOOK_NAMES_PATTERN = (
    r'(?:Gen(?:esis)?|Ex(?:od(?:us)?)?|Lev(?:iticus)?|Num(?:bers)?|'
    r'Deut(?:eronomy)?|Josh(?:ua)?|Judg(?:es)?|'
    r'(?:1|2|I{1,2})\s*(?:Sam(?:uel)?|Kgs|Kings?|Chr(?:on(?:icles)?)?)|'
    r'Isa(?:iah)?|Jer(?:emiah)?|Ezek(?:iel)?|'
    r'Hos(?:ea)?|Joel|Am(?:os)?|Obad(?:iah)?|Jonah?|Mic(?:ah)?|'
    r'Nah(?:um)?|Hab(?:akkuk)?|Zeph(?:aniah)?|Hag(?:gai)?|'
    r'Zech(?:ariah)?|Mal(?:achi)?|'
    r'Ps(?:alm)?s?|Prov(?:erbs)?|Job|'
    r'Song(?:\s+of\s+Songs)?|Ruth|Lam(?:entations)?|'
    r'Eccl(?:esiastes)?|Qoh|Esth(?:er)?|Dan(?:iel)?|'
    r'Ezra|Neh(?:emiah)?)'
)

_CITATION_FORWARD_RE = re.compile(
    r'(?<!\()'                                   # NOT preceded by open paren
    r'((?:1|2|I{1,2})?\s*'                       # optional numbered prefix
    + _BOOK_NAMES_PATTERN +
    r')\s+'                                       # book name + space
    r'(\d+)'                                      # chapter number
    r':'
    r'(\d+)'                                      # first verse number
    r'(?:\s*[–\-]\s*(\d+))?',                     # optional verse range end
    re.IGNORECASE
)


def _extract_hebrew_after_citation(
    text: str, citation_end: int
) -> Optional[List[str]]:
    """
    Look forward from an inline citation to find Hebrew text being quoted.

    Scans up to 300 chars forward for Hebrew words, grouping consecutive ones
    into phrases (same logic as _extract_hebrew_before_citation but forward).

    Returns a list of ALL Hebrew phrases found (ordered closest-first),
    or None if no Hebrew is found.  The caller decides which phrases to
    verify (some may be too short, others may match the verse immediately).
    """
    lookahead_end = min(len(text), citation_end + 300)
    lookahead = text[citation_end:lookahead_end]

    words = list(_HEBREW_WORD_RE.finditer(lookahead))
    if not words:
        return None

    # Group consecutive Hebrew words into phrases
    phrases = []
    phrase_words = [words[0].group()]
    for i in range(1, len(words)):
        gap = lookahead[words[i - 1].end():words[i].start()]
        has_latin = bool(re.search(r'[a-zA-Z]', gap))
        has_newline = '\n' in gap
        if has_latin or has_newline or len(gap) > 10:
            phrases.append(' '.join(phrase_words))
            phrase_words = [words[i].group()]
        else:
            phrase_words.append(words[i].group())
    phrases.append(' '.join(phrase_words))

    return phrases if phrases else None


# Minimum Hebrew words required to consider something a "quotation" vs. a
# single-word lexical reference.  A phrase like יָצוּק (1 Kgs 7:24) is a
# word reference, not a quotation; we don't verify those.
MIN_HEBREW_WORDS = 3

# Regex that matches a single Hebrew "word" — a contiguous run of characters
# in the Hebrew Unicode block (letters, vowels, cantillation, maqaf, etc.)
_HEBREW_WORD_RE = re.compile(r'[\u0590-\u05FF\uFB1D-\uFB4F]+')


def _extract_hebrew_from_inline(content: str) -> Optional[str]:
    """
    Extract the Hebrew quotation from the content portion of a Pattern C
    citation like ``(Gen 27:36: עֲקָבַנִי זֶה פַעֲמַיִם, "English")``.

    The content after the colon may contain:
      - Hebrew text (what we want)
      - English translations in quotes
      - Commas, em-dashes separating Hebrew from English

    Strategy: collect all Hebrew words, group consecutive ones into phrases
    (same logic as _extract_hebrew_before_citation), return the longest
    phrase that meets MIN_HEBREW_WORDS.
    """
    words = list(_HEBREW_WORD_RE.finditer(content))
    if not words:
        return None

    # Group consecutive Hebrew words into phrases
    phrases = []
    phrase_words = [words[0].group()]
    for i in range(1, len(words)):
        gap = content[words[i - 1].end():words[i].start()]
        has_latin = bool(re.search(r'[a-zA-Z]', gap))
        if has_latin or len(gap) > 10:
            phrases.append(phrase_words)
            phrase_words = [words[i].group()]
        else:
            phrase_words.append(words[i].group())
    phrases.append(phrase_words)

    # Return the longest phrase with enough words
    best = None
    for p in phrases:
        if len(p) >= MIN_HEBREW_WORDS:
            candidate = ' '.join(p)
            if best is None or len(p) > len(best.split()):
                best = candidate
    return best


def _extract_hebrew_before_citation(
    text: str, citation_start: int
) -> Optional[tuple]:
    """
    Look backward from a citation parenthetical to find the Hebrew text
    being quoted.

    The commentary uses two common patterns:
      A.  ...Hebrew phrase, "English translation" (Book Ch:V)
      B.  ...Hebrew phrase (Book Ch:V)

    Strategy:
      1. Find every Hebrew "word" in a 500-char lookback window.
      2. Group consecutive Hebrew words into phrases — a phrase breaks
         when the gap between two words contains Latin characters (a-zA-Z),
         exceeds 10 characters, or spans a line break.
      3. Return the phrase closest to the citation that has at least
         MIN_HEBREW_WORDS words.  This filters out one-word lexical
         references like יָצוּק (1 Kgs 7:24).

    Returns:
        (hebrew_text, absolute_end_offset) or None
    """
    lookback_start = max(0, citation_start - 500)
    lookback = text[lookback_start:citation_start]

    # Find all Hebrew words in the lookback window
    words = list(_HEBREW_WORD_RE.finditer(lookback))
    if not words:
        return None

    # Group words into phrases, working backward from the end
    # A "phrase" is a maximal sequence of Hebrew words whose inter-word
    # gaps contain no Latin characters, are ≤10 chars, and have no newlines.
    phrases = []  # list of (start_offset, end_offset) within lookback
    phrase_end = words[-1].end()
    phrase_start = words[-1].start()

    for i in range(len(words) - 2, -1, -1):
        gap_text = lookback[words[i].end():words[i + 1].start()]
        has_latin = bool(re.search(r'[a-zA-Z]', gap_text))
        has_newline = '\n' in gap_text
        gap_too_long = len(gap_text) > 10

        if has_latin or has_newline or gap_too_long:
            # Break: save current phrase and start a new one
            phrases.append((phrase_start, phrase_end))
            phrase_end = words[i].end()
            phrase_start = words[i].start()
        else:
            # Extend phrase backward
            phrase_start = words[i].start()

    phrases.append((phrase_start, phrase_end))
    # phrases[0] is the phrase closest to the citation

    # Return the closest phrase with ≥ MIN_HEBREW_WORDS words
    for start, end in phrases:
        candidate = lookback[start:end].strip()
        word_count = len(_HEBREW_WORD_RE.findall(candidate))
        if word_count >= MIN_HEBREW_WORDS:
            # Convert end offset to absolute position in the full text
            abs_end = lookback_start + end
            return (candidate, abs_end)

    return None


def _find_current_verse_header(text: str, position: int) -> str:
    """Find the most recent **Verse N** header before the given position."""
    lookback = text[:position]
    matches = list(re.finditer(r'\*\*Verses?\s+([\d–\-]+)\*\*', lookback))
    if matches:
        return f"Verse {matches[-1].group(1)}"

    # Check if we're in the Introduction
    if '## Introduction' in lookback and '## Verse-by-Verse' not in lookback:
        return "Introduction"

    # Check liturgical section
    if '---LITURGICAL-SECTION-START---' in lookback:
        return "Liturgical Section"

    return "Unknown Section"


# ---------------------------------------------------------------------------
# Pre-processing helpers
# ---------------------------------------------------------------------------

def _strip_appended_reports(text: str) -> str:
    """
    Strip any previously-appended verification report from the text.

    The pipeline appends a "SCRIPTURE CITATION CHECK" block to the
    print-ready file before handing it to the copy editor.  If the verifier
    re-reads that file later, it would match citations inside its own
    report — a "report contamination" false positive.
    """
    marker = "SCRIPTURE CITATION CHECK"
    idx = text.find(marker)
    if idx != -1:
        # Walk backward to the newline before the marker
        newline_before = text.rfind('\n', 0, idx)
        if newline_before != -1:
            text = text[:newline_before]
    return text


def _words_match(quoted_consonants: str, actual_consonants: str) -> bool:
    """
    Word-level consonantal match: every quoted word must appear as a
    *complete* word in the actual verse, in sequence.

    Unlike pure substring matching, this catches conjugation mismatches
    like עקבני (from עֲקָבַנִי) vs ויעקבני (from וַיַּעְקְבֵנִי) where the
    shorter form is a character-level substring but a different word.
    """
    q_words = quoted_consonants.split()
    a_words = actual_consonants.split()
    if not q_words:
        return True

    # Try to find q_words as a contiguous sub-sequence of a_words
    for start in range(len(a_words) - len(q_words) + 1):
        if a_words[start:start + len(q_words)] == q_words:
            return True
    return False


# ---------------------------------------------------------------------------
# Main verification function
# ---------------------------------------------------------------------------

def verify_citations(
    text: str,
    db_path: str = "database/tanakh.db",
    psalm_number: int = 0,
) -> List[CitationIssue]:
    """
    Verify all Hebrew scripture citations in the given text against tanakh.db.

    Args:
        text: Full commentary text (markdown)
        db_path: Path to the tanakh.db SQLite database
        psalm_number: The psalm being analyzed (used to filter self-quotes)

    Returns:
        List of CitationIssue objects for each failed verification
    """
    from src.data_sources.tanakh_database import TanakhDatabase

    # Strip any previously-appended verification report to avoid re-reading
    # our own output as citations (report contamination).
    text = _strip_appended_reports(text)

    db = TanakhDatabase(Path(db_path))
    issues = []

    # Build a set of consonantal text from the current psalm's verses.
    # If the quoted Hebrew belongs to the psalm being discussed (not the
    # cited verse), it is a cross-reference, not a direct quotation.
    psalm_consonants = set()
    if psalm_number > 0:
        psalm_obj = db.get_psalm(psalm_number)
        if psalm_obj:
            for v in psalm_obj.verses:
                psalm_consonants.add(_strip_to_consonants(v.hebrew))

    # Find all citation parentheticals
    for match in _CITATION_PAREN_RE.finditer(text):
        raw_book = match.group(1).strip()
        chapter = int(match.group(2))
        verse_num = int(match.group(3))
        cite_ref = match.group(0)  # full "(Book Ch:V)" string

        # Resolve book name
        db_book_name = _resolve_book_name(raw_book)
        if db_book_name is None:
            # Can't resolve — skip silently (may be a non-biblical citation)
            continue

        # Extract Hebrew text before this citation
        extraction = _extract_hebrew_before_citation(text, match.start())
        if extraction is None:
            # No Hebrew text found before citation — not a Hebrew quote, skip
            continue
        hebrew_quoted, hebrew_abs_end = extraction

        # --- Intervening-citation check ---
        # If another scripture citation parenthetical appears between the end
        # of the Hebrew phrase and the start of THIS citation, the Hebrew was
        # already "claimed" by that closer citation.  Skip to avoid matching
        # the same phrase to multiple consecutive citations like
        #   "...Hebrew..." (Ex 20:7). More text (Isa 17:5) and (1 Sam 28:4).
        gap_between = text[hebrew_abs_end:match.start()]
        if _CITATION_PAREN_RE.search(gap_between):
            continue

        # --- Self-quote filter ---
        # If the quoted Hebrew is a substring of any verse in the current psalm,
        # this is the commentary discussing a psalm phrase and citing a parallel.
        # Skip it — the citation refers to where else the word/phrase appears,
        # not to the source of the quote.
        cons_quoted = _strip_to_consonants(hebrew_quoted)
        is_self_quote = False
        if psalm_consonants:
            # Check if the quoted consonantal text is a substring of any psalm verse
            for pv_cons in psalm_consonants:
                if cons_quoted in pv_cons:
                    is_self_quote = True
                    break
        if is_self_quote:
            # Also check: is this actually citing the CURRENT psalm?
            # If so, it IS a direct quote and should still be verified.
            if db_book_name == "Psalms" and chapter == psalm_number:
                pass  # proceed with verification
            else:
                continue  # skip — it's a cross-reference

        # Look up the verse in the database
        verse_obj = db.get_verse(db_book_name, chapter, verse_num)
        if verse_obj is None:
            # Verse not in database
            line_num = text[:match.start()].count('\n') + 1
            location = _find_current_verse_header(text, match.start())
            issues.append(CitationIssue(
                quoted_hebrew=hebrew_quoted,
                citation_ref=cite_ref,
                actual_hebrew="",
                location_hint=location,
                issue_type="BOOK_NOT_IN_DB",
                line_number=line_num,
            ))
            continue

        actual_hebrew = verse_obj.hebrew

        # Normalize both for comparison
        norm_quoted = _normalize_hebrew(hebrew_quoted)
        norm_actual = _normalize_hebrew(actual_hebrew)

        # Check 1: voweled substring match
        if norm_quoted in norm_actual:
            continue  # pass

        # Check 2: consonantal word-level match
        # Handles vowel pointing differences (e.g., דַל vs דַּל) while
        # catching conjugation mismatches (e.g., עֲקָבַנִי vs וַיַּעְקְבֵנִי)
        cons_actual = _strip_to_consonants(actual_hebrew)
        if _words_match(cons_quoted, cons_actual):
            continue  # pass — consonantal word match

        # Failed both checks — record the issue
        line_num = text[:match.start()].count('\n') + 1
        location = _find_current_verse_header(text, match.start())
        issues.append(CitationIssue(
            quoted_hebrew=hebrew_quoted,
            citation_ref=cite_ref,
            actual_hebrew=actual_hebrew,
            location_hint=location,
            issue_type="NOT_SUBSTRING",
            line_number=line_num,
            normalized_quoted=norm_quoted,
            normalized_actual=norm_actual,
        ))

    # ----- Pattern C: Hebrew text INSIDE the citation parenthetical -----
    # e.g.  (Gen 27:36: עֲקָבַנִי זֶה פַעֲמַיִם, "he has supplanted...")
    # These are invisible to _CITATION_PAREN_RE (which requires ')' right
    # after the verse number), so we run a separate pass here.
    for match in _CITATION_INLINE_RE.finditer(text):
        raw_book = match.group(1).strip()
        chapter = int(match.group(2))
        verse_num = int(match.group(3))
        inline_content = match.group(4)
        cite_ref = f"({raw_book} {chapter}:{verse_num})"

        db_book_name = _resolve_book_name(raw_book)
        if db_book_name is None:
            continue

        hebrew_quoted = _extract_hebrew_from_inline(inline_content)
        if hebrew_quoted is None:
            continue

        # Self-quote filter (same logic as Pattern A/B)
        cons_quoted = _strip_to_consonants(hebrew_quoted)
        is_self_quote = False
        if psalm_consonants:
            for pv_cons in psalm_consonants:
                if cons_quoted in pv_cons:
                    is_self_quote = True
                    break
        if is_self_quote:
            if db_book_name == "Psalms" and chapter == psalm_number:
                pass
            else:
                continue

        verse_obj = db.get_verse(db_book_name, chapter, verse_num)
        if verse_obj is None:
            line_num = text[:match.start()].count('\n') + 1
            location = _find_current_verse_header(text, match.start())
            issues.append(CitationIssue(
                quoted_hebrew=hebrew_quoted,
                citation_ref=cite_ref,
                actual_hebrew="",
                location_hint=location,
                issue_type="BOOK_NOT_IN_DB",
                line_number=line_num,
            ))
            continue

        actual_hebrew = verse_obj.hebrew
        norm_quoted = _normalize_hebrew(hebrew_quoted)
        norm_actual = _normalize_hebrew(actual_hebrew)

        if norm_quoted in norm_actual:
            continue
        cons_actual = _strip_to_consonants(actual_hebrew)
        if _words_match(cons_quoted, cons_actual):
            continue

        line_num = text[:match.start()].count('\n') + 1
        location = _find_current_verse_header(text, match.start())
        issues.append(CitationIssue(
            quoted_hebrew=hebrew_quoted,
            citation_ref=cite_ref,
            actual_hebrew=actual_hebrew,
            location_hint=location,
            issue_type="NOT_SUBSTRING",
            line_number=line_num,
            normalized_quoted=norm_quoted,
            normalized_actual=norm_actual,
        ))

    # ----- Pattern D: Inline forward citations (NOT in parentheses) -----
    # e.g.  2 Samuel 7:29 — וּבָרֵךְ אֶת עַבְדְּךָ ...
    #        Psalm 55:13–14, ... כִּי לֹא אוֹיֵב ...
    # These are invisible to Patterns A/B/C which require parenthetical refs.

    # Build a set of already-checked (book, chapter, verse, line_number) to
    # avoid double-flagging citations that Pattern A/B/C already processed.
    checked_refs = set()
    for match in _CITATION_PAREN_RE.finditer(text):
        raw_book = match.group(1).strip()
        chapter = int(match.group(2))
        verse_num = int(match.group(3))
        line_num = text[:match.start()].count('\n') + 1
        checked_refs.add((raw_book.lower(), chapter, verse_num, line_num))
    for match in _CITATION_INLINE_RE.finditer(text):
        raw_book = match.group(1).strip()
        chapter = int(match.group(2))
        verse_num = int(match.group(3))
        line_num = text[:match.start()].count('\n') + 1
        checked_refs.add((raw_book.lower(), chapter, verse_num, line_num))

    for match in _CITATION_FORWARD_RE.finditer(text):
        # Skip if this match is inside a parenthetical (Pattern A/B/C territory)
        if match.start() > 0 and text[match.start() - 1] == '(':
            continue
        # Also skip if the preceding non-space char is '('
        pre = text[:match.start()].rstrip()
        if pre and pre[-1] == '(':
            continue

        raw_book = match.group(1).strip()
        chapter = int(match.group(2))
        verse_num = int(match.group(3))
        verse_end = int(match.group(4)) if match.group(4) else verse_num
        cite_ref = f"({raw_book} {chapter}:{verse_num})"

        # Skip if already checked by Pattern A/B/C on same line
        line_num = text[:match.start()].count('\n') + 1
        if (raw_book.lower(), chapter, verse_num, line_num) in checked_refs:
            continue

        db_book_name = _resolve_book_name(raw_book)
        if db_book_name is None:
            continue

        # Extract Hebrew phrases AFTER the citation (ordered closest-first)
        all_phrases = _extract_hebrew_after_citation(text, match.end())
        if all_phrases is None:
            continue

        # Find the first phrase with enough words for verification
        hebrew_quoted = None
        for phrase in all_phrases:
            if len(_HEBREW_WORD_RE.findall(phrase)) >= MIN_HEBREW_WORDS:
                hebrew_quoted = phrase
                break
        if hebrew_quoted is None:
            continue

        # --- Forward intervening-citation check ---
        # If another scripture citation (inline or parenthetical) appears
        # between this reference and the Hebrew text, the Hebrew likely belongs
        # to that closer citation, not this one.  Skip to avoid false matches.
        hebrew_pos = text.find(hebrew_quoted[:20], match.end())
        if hebrew_pos > 0:
            gap_text = text[match.end():hebrew_pos]
            has_intervening = (
                _CITATION_PAREN_RE.search(gap_text)
                or _CITATION_INLINE_RE.search(gap_text)
                or _CITATION_FORWARD_RE.search(gap_text)
            )
            if has_intervening:
                continue

        # Look up all verses in the range for early-verify and full checking
        actual_verses = {}
        for v in range(verse_num, verse_end + 1):
            verse_obj = db.get_verse(db_book_name, chapter, v)
            if verse_obj:
                actual_verses[v] = verse_obj.hebrew

        if not actual_verses:
            continue

        combined_actual = ' '.join(actual_verses.values())
        norm_actual = _normalize_hebrew(combined_actual)
        cons_actual = _strip_to_consonants(combined_actual)

        # --- Early-verify check ---
        # If a CLOSER phrase (even below MIN_HEBREW_WORDS) matches the verse,
        # the citation is verified by that short quote.  This prevents false
        # positives where a matching 2-word phrase is skipped and a distant
        # non-matching phrase is flagged instead.
        early_verified = False
        for phrase in all_phrases:
            if phrase == hebrew_quoted:
                break  # reached the phrase we'll verify — stop early-check
            # Even 1-word phrases can verify if they're a valid substring
            norm_p = _normalize_hebrew(phrase)
            if len(norm_p) >= 3 and norm_p in norm_actual:
                early_verified = True
                break
            cons_p = _strip_to_consonants(phrase)
            if len(cons_p) >= 3 and _words_match(cons_p, cons_actual):
                early_verified = True
                break
        if early_verified:
            continue

        # Self-quote filter (same logic as Pattern A/B)
        cons_quoted_full = _strip_to_consonants(hebrew_quoted)
        is_self_quote = False
        if psalm_consonants:
            for pv_cons in psalm_consonants:
                if cons_quoted_full in pv_cons:
                    is_self_quote = True
                    break
        if is_self_quote:
            if db_book_name == "Psalms" and chapter == psalm_number:
                pass
            else:
                continue

        # Split on ellipsis to get fragments for independent verification
        fragments = _split_ellipsis_fragments(hebrew_quoted)

        # Verify each fragment independently
        for fragment in fragments:
            frag_words = _HEBREW_WORD_RE.findall(fragment)
            if len(frag_words) < MIN_HEBREW_WORDS:
                continue

            norm_frag = _normalize_hebrew(fragment)
            if norm_frag in norm_actual:
                continue

            cons_frag = _strip_to_consonants(fragment)
            if _words_match(cons_frag, cons_actual):
                continue

            # Failed — record the issue
            location = _find_current_verse_header(text, match.start())
            issues.append(CitationIssue(
                quoted_hebrew=fragment,
                citation_ref=cite_ref,
                actual_hebrew=combined_actual,
                location_hint=location,
                issue_type="NOT_SUBSTRING",
                line_number=line_num,
                normalized_quoted=norm_frag,
                normalized_actual=norm_actual,
            ))

    db.close()
    return issues


def _split_ellipsis_fragments(hebrew_text: str) -> List[str]:
    """
    Split a Hebrew quotation on ellipsis markers (... or …) into
    independent fragments for separate verification.

    If no ellipsis is present, returns a single-element list with the
    original text.
    """
    # Split on ... or … (Unicode ellipsis U+2026)
    parts = re.split(r'\.{3}|…', hebrew_text)
    fragments = []
    for part in parts:
        stripped = part.strip(' ,;:\u2014\u2013-"\'')
        if stripped and _HEBREW_WORD_RE.search(stripped):
            fragments.append(stripped)
    return fragments if fragments else [hebrew_text]


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def format_verification_report(
    issues: List[CitationIssue],
    psalm_number: int = 0,
) -> str:
    """
    Format verification issues into a readable markdown report.

    Args:
        issues: List of CitationIssue objects
        psalm_number: Psalm number for the report header

    Returns:
        Markdown-formatted report string
    """
    lines = []
    header = f"# Scripture Citation Verification — Psalm {psalm_number}" if psalm_number else "# Scripture Citation Verification"
    lines.append(header)
    lines.append("")

    if not issues:
        lines.append("✅ **All citations verified successfully.** No misquotes detected.")
        return '\n'.join(lines)

    lines.append(f"⚠️ **{len(issues)} citation issue(s) detected:**")
    lines.append("")

    for i, issue in enumerate(issues, 1):
        lines.append(f"### Issue {i}: {issue.citation_ref}")
        lines.append(f"- **Location**: {issue.location_hint} (line ~{issue.line_number})")
        lines.append(f"- **Type**: `{issue.issue_type}`")
        lines.append(f"- **Quoted**: {issue.quoted_hebrew}")

        if issue.actual_hebrew:
            lines.append(f"- **Actual verse**: {issue.actual_hebrew}")

        if issue.normalized_quoted and issue.normalized_actual:
            lines.append(f"- **Normalized quoted**: `{issue.normalized_quoted}`")
            lines.append(f"- **Normalized actual**: `{issue.normalized_actual}`")

            # Try to identify what's different
            diff_hint = _describe_difference(issue.normalized_quoted, issue.normalized_actual)
            if diff_hint:
                lines.append(f"- **Likely issue**: {diff_hint}")

        lines.append("")

    return '\n'.join(lines)


def _describe_difference(norm_quoted: str, norm_actual: str) -> str:
    """Try to describe the difference between quoted and actual text."""
    q_words = norm_quoted.split()
    a_words = norm_actual.split()

    # Check if all quoted words appear in actual (but not contiguously)
    all_present = all(w in a_words for w in q_words)
    if all_present and norm_quoted not in norm_actual:
        # Words are present but not in the right order or missing words in between
        # Find which words from the actual are missing in the quoted
        missing = []
        q_set = set(q_words)
        # Walk through actual words and find gaps
        in_quote = False
        for w in a_words:
            if w in q_set:
                in_quote = True
            elif in_quote:
                missing.append(w)
        if missing:
            return f"Missing word(s) from middle of verse: {' '.join(missing)}"

    # Check if it's a reordering
    if set(q_words) == set(a_words):
        return "Words appear reordered compared to the actual verse"

    # Check if quoted text appears nowhere
    if not any(w in a_words for w in q_words):
        return "Quoted text does not match any part of the cited verse"

    return ""


# ---------------------------------------------------------------------------
# Copy editor fix prompt generation
# ---------------------------------------------------------------------------

def format_fix_prompt(issues: List[CitationIssue]) -> str:
    """
    Generate a supplementary prompt for the copy editor to fix citation errors.

    Args:
        issues: List of CitationIssue objects (only NOT_SUBSTRING issues)

    Returns:
        Text to append to the copy editor's user message
    """
    fixable = [i for i in issues if i.issue_type == "NOT_SUBSTRING"]
    if not fixable:
        return ""

    lines = [
        "",
        "SCRIPTURE CITATION CHECK (automated — apply with judgment):",
        "",
        "An automated regex-based tool compared quoted Hebrew passages against the",
        "canonical biblical text in our database.  It uses substring matching after",
        "normalizing vowels, cantillation, and divine-name variants.  This approach",
        "is useful but imperfect — it can produce FALSE POSITIVES in cases such as:",
        "  - Liturgical / piyyut texts that adapt or paraphrase biblical wording",
        "  - Deliberate partial quotes or allusions (not meant as exact citations)",
        "  - Vowel/pointing differences that survive normalization",
        "",
        "For each item below, use your own scholarly judgment:",
        "  - If the quoted Hebrew genuinely misquotes the cited verse (e.g. a word",
        "    was dropped or garbled), correct it to match the actual verse text.",
        "  - If the passage is a liturgical adaptation, allusion, or intentional",
        "    paraphrase, leave it as-is (no correction needed).",
        "  - If the commentary quotes only a fragment, ensure the fragment is a",
        "    contiguous substring of the actual verse (do not omit words from the",
        "    middle).",
        "",
        "IMPORTANT: In your ## Changes section, prefix any correction you make based",
        "on this citation check with [CITATION FIX] so the author can quickly spot",
        "citation-driven changes.  Example:",
        '  6. [CITATION FIX] [7] **Verse 7**: Corrected the Ex 20:7 quotation…',
        "",
    ]

    for i, issue in enumerate(fixable, 1):
        lines.append(f"{i}. **{issue.location_hint}** (line ~{issue.line_number}): "
                     f"Quoted {issue.quoted_hebrew} as {issue.citation_ref}")
        lines.append(f"   Actual verse: {issue.actual_hebrew}")

        diff_hint = _describe_difference(issue.normalized_quoted, issue.normalized_actual)
        if diff_hint:
            lines.append(f"   → {diff_hint}")
        lines.append("")

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Haiku false-positive filter (optional, ~$0.003 per psalm)
# ---------------------------------------------------------------------------

_HAIKU_JUDGE_SYSTEM = """You are a Hebrew scripture verification judge. You receive pairs of
(quoted Hebrew from a psalm commentary, actual verse text from a database) that an
automated tool flagged as mismatches. Determine whether each is a genuine citation
error or a false positive.

For each pair, output a JSON object with:
- "index": the pair number (1-based)
- "verdict": one of:
  - "GENUINE_ERROR" — the quoted text materially misrepresents the cited verse
    (wrong conjugation, dropped word from the middle, garbled text)
  - "FALSE_POSITIVE" — the mismatch is expected and NOT an error. Reasons include:
    - The Hebrew text is from a liturgical/piyyut source, not the cited verse
    - The citation is mentioned editorially (e.g. "parallel to Ps 72:18") and
      the Hebrew text nearby belongs to a DIFFERENT source
    - The quote is a deliberate partial quote that doesn't drop words from the middle
  - "MINOR" — a trivial orthographic difference that doesn't constitute an error
- "explanation": 1-2 sentences explaining your reasoning

IMPORTANT: Scholarly commentaries routinely quote fragments of verses. A partial quote
is NOT an error unless it drops words from the MIDDLE of a quoted phrase. Quoting only
the beginning or end of a verse is standard practice. However, if the automated tool
reports "Missing word(s) from middle of verse" — that IS typically a GENUINE_ERROR,
because the quoted text skips over words that should appear between two quoted words.
Pay close attention to this hint.

CONJUGATION DIFFERENCES ARE GENUINE ERRORS: If the quoted verb form differs from the
actual verse's verb form (e.g. עֲקָבַנִי Qal perfect vs וַיַּעְקְבֵנִי wayyiqtol, or
any prefix/suffix change that alters the conjugation), that IS a GENUINE_ERROR — not
MINOR. The commentary presents it as a direct quotation, so the verb form must match
the biblical text exactly. Do NOT classify verb conjugation mismatches as MINOR.

Also watch for this common regex false positive: the automated tool may associate Hebrew
text from a piyyut or liturgical quotation with a biblical citation that appears in a
DIFFERENT clause or sentence. If the Hebrew clearly doesn't belong to the cited verse
reference, that is a FALSE_POSITIVE.

Output ONLY a JSON array — no other text."""


def filter_false_positives(
    issues: List[CitationIssue],
    commentary_text: str = "",
) -> tuple:
    """
    Use Claude Haiku to filter false positives from the regex verifier's output.

    Sends mismatched citation pairs to Haiku for judgment, removing issues
    that Haiku classifies as FALSE_POSITIVE or MINOR.

    Args:
        issues: List of CitationIssue objects from verify_citations()
        commentary_text: Optional full commentary text for context extraction

    Returns:
        (filtered_issues, stats_dict) where filtered_issues contains only
        GENUINE_ERROR issues plus any non-NOT_SUBSTRING issues unchanged.
    """
    import json
    import os

    fixable = [i for i in issues if i.issue_type == "NOT_SUBSTRING"]
    non_fixable = [i for i in issues if i.issue_type != "NOT_SUBSTRING"]

    if not fixable:
        return issues, {"input_tokens": 0, "output_tokens": 0, "cost": 0.0,
                        "filtered_count": 0, "kept_count": 0}

    try:
        import anthropic
    except ImportError:
        return issues, {"input_tokens": 0, "output_tokens": 0, "cost": 0.0,
                        "filtered_count": 0, "kept_count": len(fixable)}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return issues, {"input_tokens": 0, "output_tokens": 0, "cost": 0.0,
                        "filtered_count": 0, "kept_count": len(fixable)}

    # Build the pairs text
    pair_lines = []
    for j, issue in enumerate(fixable, 1):
        pair_lines.append(f"\nPair {j}:")
        pair_lines.append(f"  Reference: {issue.citation_ref}")
        pair_lines.append(f"  Location: {issue.location_hint}")
        pair_lines.append(f"  Quoted Hebrew: {issue.quoted_hebrew}")
        pair_lines.append(f"  Actual verse text: {issue.actual_hebrew}")

        # Include the automated difference analysis as a hint
        if issue.normalized_quoted and issue.normalized_actual:
            diff_hint = _describe_difference(issue.normalized_quoted, issue.normalized_actual)
            if diff_hint:
                pair_lines.append(f"  Automated analysis: {diff_hint}")

        # Extract ~300 chars of context around the citation for disambiguation
        if commentary_text and issue.line_number > 0:
            lines = commentary_text.splitlines()
            line_idx = min(issue.line_number - 1, len(lines) - 1)
            context_line = lines[line_idx]
            if len(context_line) > 300:
                ref_pos = context_line.find(issue.citation_ref.strip('()'))
                if ref_pos >= 0:
                    start = max(0, ref_pos - 150)
                    end = min(len(context_line), ref_pos + 150)
                    context_line = "..." + context_line[start:end] + "..."
                else:
                    context_line = context_line[:300] + "..."
            pair_lines.append(f"  Surrounding text: {context_line}")

    user_msg = (
        f"Judge these {len(fixable)} quotation-vs-actual pairs. "
        f"Output ONLY a JSON array.\n"
        + '\n'.join(pair_lines)
    )

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=_HAIKU_JUDGE_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)

    try:
        judgments = json.loads(raw)
    except json.JSONDecodeError:
        return issues, {"input_tokens": 0, "output_tokens": 0, "cost": 0.0,
                        "filtered_count": 0, "kept_count": len(fixable),
                        "error": "JSON parse failed"}

    # Build a map of index → verdict
    verdict_map = {}
    for j in judgments:
        idx = j.get("index", 0) - 1  # 0-based
        verdict_map[idx] = (j.get("verdict", ""), j.get("explanation", ""))

    # Filter: keep only GENUINE_ERROR issues
    filtered = list(non_fixable)
    for idx, issue in enumerate(fixable):
        verdict, explanation = verdict_map.get(idx, ("GENUINE_ERROR", ""))
        if verdict == "GENUINE_ERROR":
            if explanation:
                issue.normalized_quoted = (
                    issue.normalized_quoted + f" [Haiku: {explanation}]"
                )
            filtered.append(issue)

    usage = response.usage
    input_tokens = usage.input_tokens
    output_tokens = usage.output_tokens
    cost = (input_tokens / 1_000_000) * 0.80 + (output_tokens / 1_000_000) * 4.00

    kept = len([i for i in filtered if i.issue_type == "NOT_SUBSTRING"])
    return filtered, {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": cost,
        "filtered_count": len(fixable) - kept,
        "kept_count": kept,
    }
