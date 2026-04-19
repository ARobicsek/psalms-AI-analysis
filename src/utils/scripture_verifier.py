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
    (re.compile(r'(א' + _DIACRITICS_CLASS + r'ל' + _DIACRITICS_CLASS + r')ק'), r'\1ה'),  # אלקים→אלהים, אלקי→אלהי, etc.
    (re.compile(r'צבקות'), 'צבאות'),               # reverential form → standard
    # Reverse El-with-tzere modification: קֵלִי→אֵלִי, קֵל→אֵל
    (re.compile(r'קֵ' + _DIACRITICS_CLASS + r'לִ' + _DIACRITICS_CLASS + r'י'), 'אֵלִי'),
    (re.compile(r'(?<![א-ת])קֵ' + _DIACRITICS_CLASS + r'ל(?![א-ת])'), 'אֵל'),
    # Reverse Shaddai modification: שקי→שדי
    (re.compile(r'שקי'), 'שדי'),
    # Reverse Eloah modification: אלוק→אלוה (standalone, not אלקים which is handled above)
    (re.compile(r'אלוק(?!י)'), 'אלוה'),
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

    # NFC normalization — ensures diacritics ordering is consistent
    # (e.g., dagesh+kamatz vs kamatz+dagesh on the same consonant)
    normalized = unicodedata.normalize('NFC', normalized)

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
    # Strip any LLM judge annotations (e.g., "[GPT-5.1: ...]") before analysis
    norm_quoted = re.sub(r'\s*\[(?:GPT-5\.1|Haiku):.*$', '', norm_quoted)

    q_words = norm_quoted.split()
    a_words = norm_actual.split()

    # --- Check for added/doubled words ---
    from collections import Counter
    q_counts = Counter(q_words)
    a_counts = Counter(a_words)
    doubled = [w for w, c in q_counts.items() if c > a_counts.get(w, 0)]
    if doubled:
        # Distinguish truly doubled words from words not found in the verse at all
        not_in_verse = [w for w in doubled if a_counts.get(w, 0) == 0]
        genuinely_doubled = [w for w in doubled if a_counts.get(w, 0) > 0]
        parts = []
        if not_in_verse:
            parts.append(f"Quote contains word(s) not found in the cited verse: "
                         f"{' '.join(not_in_verse)}")
        if genuinely_doubled:
            parts.append(f"Word(s) appear more times in quote than in actual verse: "
                         f"{' '.join(genuinely_doubled)}")
        if parts:
            return '; '.join(parts)

    # --- Check for missing middle words ---
    # Try to align quoted words onto actual words as a subsequence,
    # then report any actual words skipped BETWEEN matched positions.
    all_present = all(w in a_words for w in q_words)
    if all_present and norm_quoted not in norm_actual:
        # Greedy left-to-right alignment of q_words onto a_words
        match_positions = []
        search_from = 0
        for qw in q_words:
            for i in range(search_from, len(a_words)):
                if a_words[i] == qw:
                    match_positions.append(i)
                    search_from = i + 1
                    break

        if len(match_positions) == len(q_words) and len(match_positions) >= 2:
            # Collect words between matched positions (the gaps)
            missing = []
            for k in range(len(match_positions) - 1):
                gap_start = match_positions[k] + 1
                gap_end = match_positions[k + 1]
                if gap_end > gap_start:
                    missing.extend(a_words[gap_start:gap_end])
            if missing:
                return (f"Missing word(s) from middle of quote: "
                        f"{' '.join(missing)}")

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
the beginning or end of a verse is standard practice.

AUTOMATED ANALYSIS HINTS — treat these as strong signals, not weak suggestions:

1. "Missing word(s) from middle of quote: X" means the quoted text bridges over word(s)
   that actually appear between two quoted words in the biblical text. This is almost
   always a GENUINE_ERROR. Example: quoting "וּבָרֵךְ אֶת עַבְדְּךָ" when the actual
   verse reads "וּבָרֵךְ אֶת בֵּית עַבְדְּךָ" — the reader is misled into thinking
   "אֶת" directly precedes "עַבְדְּךָ" in the Bible, but it doesn't.
   DEFAULT: GENUINE_ERROR unless the Hebrew clearly belongs to a different source.

2. "Word(s) appear more times in quote than in actual verse: X" means the quote
   fabricates a repetition not present in the biblical text (e.g. "רֵקִים רֵקִים"
   when the verse has only one "רֵקִים"). DEFAULT: GENUINE_ERROR unless the surrounding
   text shows this is a piyyut/liturgical adaptation rather than a biblical citation.

3. CONJUGATION DIFFERENCES ARE GENUINE ERRORS: If the quoted verb form differs from the
   actual verse's verb form (e.g. עֲקָבַנִי Qal perfect vs וַיַּעְקְבֵנִי wayyiqtol),
   that IS a GENUINE_ERROR — not MINOR. The commentary presents it as a direct quotation,
   so the verb form must match the biblical text exactly.

REGEX FALSE POSITIVE PATTERN: The automated tool may associate Hebrew text from a
piyyut or liturgical quotation with a biblical citation that appears in a DIFFERENT
clause or sentence. Check the "Surrounding text" — if the citation is a structural
cross-reference (e.g. "parallel formulas at the end of Books II (Ps 72:18–19)") rather
than attributing the nearby Hebrew, that is a FALSE_POSITIVE.

Output ONLY a JSON array — no other text."""


def _build_judge_pairs(
    fixable: List[CitationIssue],
    commentary_text: str = "",
) -> str:
    """Build the pairs text for the false-positive judge (shared by all backends)."""
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

    return (
        f"Judge these {len(fixable)} quotation-vs-actual pairs. "
        f"Output ONLY a JSON array.\n"
        + '\n'.join(pair_lines)
    )


def _apply_judgments(
    raw_json: str,
    fixable: List[CitationIssue],
    non_fixable: List[CitationIssue],
    model_label: str,
) -> List[CitationIssue]:
    """Parse JSON judgments and filter issues (shared by all backends)."""
    import json

    if raw_json.startswith("```"):
        raw_json = re.sub(r'^```(?:json)?\s*', '', raw_json)
        raw_json = re.sub(r'\s*```$', '', raw_json)

    judgments = json.loads(raw_json)  # caller handles JSONDecodeError

    verdict_map = {}
    for j in judgments:
        idx = j.get("index", 0) - 1  # 0-based
        verdict_map[idx] = (j.get("verdict", ""), j.get("explanation", ""))

    filtered = list(non_fixable)
    for idx, issue in enumerate(fixable):
        verdict, explanation = verdict_map.get(idx, ("GENUINE_ERROR", ""))
        if verdict == "GENUINE_ERROR":
            if explanation:
                issue.normalized_quoted = (
                    issue.normalized_quoted + f" [{model_label}: {explanation}]"
                )
            filtered.append(issue)

    return filtered


def filter_false_positives(
    issues: List[CitationIssue],
    commentary_text: str = "",
    model: str = "haiku",
    cost_tracker=None,
) -> tuple:
    """
    Use an LLM judge to filter false positives from the regex verifier's output.

    Sends mismatched citation pairs to the judge model, removing issues
    classified as FALSE_POSITIVE or MINOR.

    Args:
        issues: List of CitationIssue objects from verify_citations()
        commentary_text: Optional full commentary text for context extraction
        model: Judge model — "haiku" (Claude Haiku 4.5) or "gpt" (GPT-5.1)

    Returns:
        (filtered_issues, stats_dict) where filtered_issues contains only
        GENUINE_ERROR issues plus any non-NOT_SUBSTRING issues unchanged.
    """
    import json
    import os

    fixable = [i for i in issues if i.issue_type == "NOT_SUBSTRING"]
    non_fixable = [i for i in issues if i.issue_type != "NOT_SUBSTRING"]
    empty_stats = {"input_tokens": 0, "output_tokens": 0, "cost": 0.0,
                   "filtered_count": 0, "kept_count": 0}

    if not fixable:
        return issues, empty_stats

    user_msg = _build_judge_pairs(fixable, commentary_text)

    if model == "gpt":
        return _filter_via_gpt(fixable, non_fixable, user_msg, cost_tracker=cost_tracker)
    else:
        return _filter_via_haiku(fixable, non_fixable, user_msg, cost_tracker=cost_tracker)


def _filter_via_haiku(
    fixable: List[CitationIssue],
    non_fixable: List[CitationIssue],
    user_msg: str,
    cost_tracker=None,
) -> tuple:
    """Run false-positive filter using Claude Haiku 4.5."""
    import json
    import os

    try:
        import anthropic
    except ImportError:
        return fixable + non_fixable, {
            "input_tokens": 0, "output_tokens": 0, "cost": 0.0,
            "filtered_count": 0, "kept_count": len(fixable)}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return fixable + non_fixable, {
            "input_tokens": 0, "output_tokens": 0, "cost": 0.0,
            "filtered_count": 0, "kept_count": len(fixable)}

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=_HAIKU_JUDGE_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = response.content[0].text.strip()
    try:
        filtered = _apply_judgments(raw, fixable, non_fixable, "Haiku")
    except json.JSONDecodeError:
        return fixable + non_fixable, {
            "input_tokens": 0, "output_tokens": 0, "cost": 0.0,
            "filtered_count": 0, "kept_count": len(fixable),
            "error": "JSON parse failed"}

    usage = response.usage
    input_tokens = usage.input_tokens
    output_tokens = usage.output_tokens
    cost = (input_tokens / 1_000_000) * 0.80 + (output_tokens / 1_000_000) * 4.00

    if cost_tracker is not None:
        cost_tracker.add_usage(
            model="claude-haiku-4-5-20251001",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thinking_tokens=0,
        )

    kept = len([i for i in filtered if i.issue_type == "NOT_SUBSTRING"])
    return filtered, {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": cost,
        "filtered_count": len(fixable) - kept,
        "kept_count": kept,
    }


def _filter_via_gpt(
    fixable: List[CitationIssue],
    non_fixable: List[CitationIssue],
    user_msg: str,
    cost_tracker=None,
) -> tuple:
    """Run false-positive filter using GPT-5.1 with moderate thinking."""
    import json
    import os

    try:
        from openai import OpenAI
    except ImportError:
        return fixable + non_fixable, {
            "input_tokens": 0, "output_tokens": 0, "cost": 0.0,
            "filtered_count": 0, "kept_count": len(fixable)}

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return fixable + non_fixable, {
            "input_tokens": 0, "output_tokens": 0, "cost": 0.0,
            "filtered_count": 0, "kept_count": len(fixable)}

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model="gpt-5.1",
        instructions=_HAIKU_JUDGE_SYSTEM,
        input=user_msg,
        reasoning={"effort": "medium"},
    )

    raw = response.output_text.strip()
    try:
        filtered = _apply_judgments(raw, fixable, non_fixable, "GPT-5.1")
    except json.JSONDecodeError:
        return fixable + non_fixable, {
            "input_tokens": 0, "output_tokens": 0, "cost": 0.0,
            "filtered_count": 0, "kept_count": len(fixable),
            "error": "JSON parse failed"}

    usage = response.usage
    input_tokens = usage.input_tokens
    output_tokens = usage.output_tokens
    thinking_tokens = getattr(usage, 'output_tokens_details', None)
    thinking_cost_tokens = 0
    if thinking_tokens:
        thinking_cost_tokens = getattr(thinking_tokens, 'reasoning_tokens', 0)
    non_thinking_output = output_tokens - thinking_cost_tokens
    cost = ((input_tokens / 1_000_000) * 1.25 +
            (non_thinking_output / 1_000_000) * 10.00 +
            (thinking_cost_tokens / 1_000_000) * 10.00)

    if cost_tracker is not None:
        cost_tracker.add_usage(
            model="gpt-5.1",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thinking_tokens=thinking_cost_tokens,
        )

    kept = len([i for i in filtered if i.issue_type == "NOT_SUBSTRING"])
    return filtered, {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": cost,
        "filtered_count": len(fixable) - kept,
        "kept_count": kept,
    }


# ---------------------------------------------------------------------------
# Haiku tool-use citation verifier  (~$0.01–0.02 per psalm)
# ---------------------------------------------------------------------------

_TOOLUSE_EXTRACT_SYSTEM = """You are a Hebrew scripture citation extractor for scholarly psalm commentary.

Your job: read the commentary text and find every place the author quotes Hebrew scripture
(3+ Hebrew words) and attributes it to a specific biblical verse. For each citation found,
call lookup_verse to get the actual verse text from the database.

STEP-BY-STEP INSTRUCTIONS:
1. Read through the commentary carefully.
2. Identify every Hebrew quotation of 3+ words paired with a biblical reference.
   Citations may appear as:
   - Parenthetical: "...Hebrew text... (Ex 20:7)"
   - Inline after colon: "(Gen 27:36: Hebrew text, 'English')"
   - Forward reference: "2 Samuel 7:29 — Hebrew text..."
3. For EACH citation, call lookup_verse to retrieve the actual verse.
   IMPORTANT: Batch as many lookup_verse calls as possible into each response.
4. After ALL lookups are complete, call report_citations once with every citation
   you found, including the quoted Hebrew EXACTLY as it appears in the commentary.

WHAT TO EXTRACT:
- Direct quotations: Hebrew text presented as quoting a specific verse
- Partial quotations: Fragments attributed to a verse

WHAT TO SKIP:
- Single-word or two-word Hebrew terms (lexical glosses, not quotations)
- Hebrew text from Psalm {psalm_number} itself (the psalm being discussed)
- Liturgical/piyyut Hebrew that is NOT directly attributed to a verse citation

CRITICAL: Copy the Hebrew text EXACTLY as it appears in the document, character for
character. Do NOT correct, fix, or normalize the Hebrew in any way. If the author
wrote a word incorrectly or omitted a word, copy it exactly as written. The whole
point of this extraction is to verify whether the author quoted correctly — if you
"fix" the quote, we cannot detect errors."""

# Tool definitions for the Anthropic API
_TOOLUSE_TOOLS = [
    {
        "name": "lookup_verse",
        "description": (
            "Look up the actual Hebrew text of a biblical verse from the Tanakh database. "
            "Use standard English book names: Genesis, Exodus, Leviticus, Numbers, "
            "Deuteronomy, Joshua, Judges, I Samuel, II Samuel, I Kings, II Kings, "
            "Isaiah, Jeremiah, Ezekiel, Hosea, Joel, Amos, Obadiah, Jonah, Micah, "
            "Nahum, Habakkuk, Zephaniah, Haggai, Zechariah, Malachi, Psalms, "
            "Proverbs, Job, Song of Songs, Ruth, Lamentations, Ecclesiastes, "
            "Esther, Daniel, Ezra, Nehemiah, I Chronicles, II Chronicles."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "book": {
                    "type": "string",
                    "description": "Book name (e.g. 'Exodus', 'I Samuel', 'Psalms')"
                },
                "chapter": {
                    "type": "integer",
                    "description": "Chapter number"
                },
                "verse": {
                    "type": "integer",
                    "description": "Verse number"
                }
            },
            "required": ["book", "chapter", "verse"]
        }
    },
    {
        "name": "report_citations",
        "description": (
            "Report ALL citations found in the commentary. Call this ONCE after "
            "all lookup_verse calls are complete. Include EVERY citation you found, "
            "regardless of whether it seems to match or not. The comparison will be "
            "done programmatically after you report."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "citations": {
                    "type": "array",
                    "description": "List of all Hebrew scripture citations found",
                    "items": {
                        "type": "object",
                        "properties": {
                            "citation_ref": {
                                "type": "string",
                                "description": "The biblical reference (e.g. 'Ex 20:7', '2 Samuel 7:29')"
                            },
                            "quoted_hebrew": {
                                "type": "string",
                                "description": "The Hebrew text as quoted in the commentary — COPY EXACTLY, do NOT fix"
                            },
                            "location_hint": {
                                "type": "string",
                                "description": "Approximate location (e.g. 'Verse 7 section', 'Introduction')"
                            },
                            "quote_type": {
                                "type": "string",
                                "enum": ["direct", "partial", "liturgical", "allusion"],
                                "description": "Type of citation"
                            }
                        },
                        "required": ["citation_ref", "quoted_hebrew"]
                    }
                },
                "total_found": {
                    "type": "integer",
                    "description": "Total number of citations found and reported"
                }
            },
            "required": ["citations", "total_found"]
        }
    }
]


def verify_citations_tooluse(
    text: str,
    db_path: str = "database/tanakh.db",
    psalm_number: int = 0,
    haiku_filter: bool = True,
    cost_tracker=None,
) -> tuple:
    """
    Verify Hebrew scripture citations using a hybrid Haiku tool-use approach.

    Architecture:
      1. Haiku reads the commentary and identifies all citations (tool-use with
         lookup_verse to get actual text from tanakh.db)
      2. Python does programmatic comparison (normalization + word-level matching)
      3. Optionally, Haiku filters false positives from the mismatches

    This eliminates regex pattern coverage gaps while maintaining reliable
    Hebrew text comparison.

    Args:
        text: Full commentary text (markdown)
        db_path: Path to the tanakh.db SQLite database
        psalm_number: The psalm being analyzed (for self-quote filtering)
        haiku_filter: Whether to run Haiku false-positive filter on mismatches

    Returns:
        (issues: List[CitationIssue], stats: dict)
    """
    import json
    import os
    import time

    # Strip any previously-appended verification report
    text = _strip_appended_reports(text)

    try:
        import anthropic
    except ImportError:
        return [], {"error": "anthropic package not installed"}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return [], {"error": "ANTHROPIC_API_KEY not set"}

    from src.data_sources.tanakh_database import TanakhDatabase
    db = TanakhDatabase(Path(db_path))

    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = _TOOLUSE_EXTRACT_SYSTEM.format(psalm_number=psalm_number)

    # Use structured content blocks with cache_control for prompt caching.
    system_blocks = [
        {
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        }
    ]

    user_msg_blocks = [
        {
            "type": "text",
            "text": (
                f"Find all Hebrew scripture citations in this Psalm {psalm_number} commentary. "
                f"For each citation of 3+ Hebrew words paired with a biblical reference, "
                f"call lookup_verse to retrieve the actual verse text. "
                f"IMPORTANT: Batch as many lookup_verse calls as possible into each response.\n"
                f"After all lookups, call report_citations with every citation you found.\n\n"
                f"---\n\n{text}"
            ),
            "cache_control": {"type": "ephemeral"},
        }
    ]

    messages = [{"role": "user", "content": user_msg_blocks}]

    total_input_tokens = 0
    total_output_tokens = 0
    total_cache_read_tokens = 0
    total_cache_creation_tokens = 0
    lookups_performed = 0
    # Store lookup results for programmatic comparison
    lookup_cache = {}  # (book, chapter, verse) → hebrew text
    start_time = time.time()
    report_result = None

    # Phase 1: Haiku extracts citations via tool-use
    MAX_TURNS = 30
    for turn in range(MAX_TURNS):
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=8192,
            system=system_blocks,
            messages=messages,
            tools=_TOOLUSE_TOOLS,
        )

        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens
        total_cache_read_tokens += getattr(response.usage, 'cache_read_input_tokens', 0) or 0
        total_cache_creation_tokens += getattr(response.usage, 'cache_creation_input_tokens', 0) or 0

        if response.stop_reason == "end_turn":
            break
        if response.stop_reason != "tool_use":
            break

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            if block.name == "lookup_verse":
                book_raw = block.input.get("book", "")
                chapter = block.input.get("chapter", 0)
                verse_num = block.input.get("verse", 0)

                db_book_name = _resolve_book_name(book_raw)
                if db_book_name is None:
                    db_book_name = book_raw

                verse_obj = db.get_verse(db_book_name, chapter, verse_num)
                if verse_obj:
                    lookup_cache[(db_book_name, chapter, verse_num)] = verse_obj.hebrew
                    result_text = json.dumps({
                        "book": db_book_name,
                        "chapter": chapter,
                        "verse": verse_num,
                        "hebrew": verse_obj.hebrew,
                        "reference": verse_obj.reference,
                    }, ensure_ascii=False)
                else:
                    result_text = json.dumps({
                        "error": f"Verse not found: {db_book_name} {chapter}:{verse_num}"
                    })

                lookups_performed += 1
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_text,
                })

            elif block.name == "report_citations":
                report_result = block.input
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": "Citations received. Programmatic comparison will follow.",
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        if report_result is not None:
            break

    db.close()
    extraction_elapsed = time.time() - start_time

    if cost_tracker is not None:
        cost_tracker.add_usage(
            model="claude-haiku-4-5-20251001",
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            thinking_tokens=0,
            cache_read_tokens=total_cache_read_tokens,
            cache_write_tokens=total_cache_creation_tokens,
        )

    # Phase 2: Programmatic comparison of each citation
    raw_citations = report_result.get("citations", []) if report_result else []
    total_found = report_result.get("total_found", len(raw_citations)) if report_result else 0

    # Build psalm self-quote set for filtering
    psalm_consonants = set()
    if psalm_number > 0:
        db2 = TanakhDatabase(Path(db_path))
        psalm_obj = db2.get_psalm(psalm_number)
        if psalm_obj:
            for v in psalm_obj.verses:
                psalm_consonants.add(_strip_to_consonants(v.hebrew))
        db2.close()

    issues = []
    auto_passed = 0
    skipped = 0

    for cit in raw_citations:
        quoted_hebrew = cit.get("quoted_hebrew", "")
        ref_str = cit.get("citation_ref", "")
        location = cit.get("location_hint", "Unknown")
        quote_type = cit.get("quote_type", "direct")

        # Skip liturgical/allusion types
        if quote_type in ("liturgical", "allusion"):
            skipped += 1
            continue

        # Check word count
        word_count = len(_HEBREW_WORD_RE.findall(quoted_hebrew))
        if word_count < MIN_HEBREW_WORDS:
            skipped += 1
            continue

        # Parse the reference to look up actual text
        ref_match = re.match(
            r'((?:1|2|I{1,2})?\s*[A-Za-z]+(?:\s+of\s+[A-Za-z]+)?)\s+(\d+):(\d+)',
            ref_str
        )
        if not ref_match:
            skipped += 1
            continue

        raw_book = ref_match.group(1).strip()
        chapter = int(ref_match.group(2))
        verse_num = int(ref_match.group(3))

        db_book_name = _resolve_book_name(raw_book)
        if db_book_name is None:
            skipped += 1
            continue

        # Get actual verse text from lookup cache
        actual_hebrew = lookup_cache.get((db_book_name, chapter, verse_num))
        if not actual_hebrew:
            skipped += 1
            continue

        # Self-quote filter
        cons_quoted = _strip_to_consonants(quoted_hebrew)
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
                skipped += 1
                continue

        # Split on ellipsis for fragment verification
        fragments = _split_ellipsis_fragments(quoted_hebrew)

        for fragment in fragments:
            frag_words = _HEBREW_WORD_RE.findall(fragment)
            if len(frag_words) < MIN_HEBREW_WORDS:
                continue

            # Programmatic comparison (same logic as verify_citations)
            norm_frag = _normalize_hebrew(fragment)
            norm_actual = _normalize_hebrew(actual_hebrew)

            if norm_frag in norm_actual:
                auto_passed += 1
                continue

            cons_frag = _strip_to_consonants(fragment)
            cons_actual = _strip_to_consonants(actual_hebrew)
            if _words_match(cons_frag, cons_actual):
                auto_passed += 1
                continue

            # Mismatch found — record as issue
            cite_ref = f"({ref_str})"
            issues.append(CitationIssue(
                quoted_hebrew=fragment,
                citation_ref=cite_ref,
                actual_hebrew=actual_hebrew,
                location_hint=location,
                issue_type="NOT_SUBSTRING",
                normalized_quoted=norm_frag,
                normalized_actual=norm_actual,
            ))

    # Phase 3: Optional Haiku false-positive filter
    filter_stats = {"input_tokens": 0, "output_tokens": 0, "cost": 0.0,
                    "filtered_count": 0, "kept_count": len(issues)}
    if haiku_filter and issues:
        issues, filter_stats = filter_false_positives(issues, commentary_text=text)

    # Cost calculation
    non_cached_input = total_input_tokens - total_cache_read_tokens - total_cache_creation_tokens
    extraction_cost = (
        (non_cached_input / 1_000_000) * 0.80
        + (total_cache_read_tokens / 1_000_000) * 0.08
        + (total_cache_creation_tokens / 1_000_000) * 1.00
        + (total_output_tokens / 1_000_000) * 4.00
    )
    total_cost = extraction_cost + filter_stats["cost"]

    stats = {
        "input_tokens": total_input_tokens + filter_stats["input_tokens"],
        "output_tokens": total_output_tokens + filter_stats["output_tokens"],
        "cache_read_tokens": total_cache_read_tokens,
        "cache_creation_tokens": total_cache_creation_tokens,
        "cost": total_cost,
        "extraction_cost": extraction_cost,
        "filter_cost": filter_stats["cost"],
        "elapsed": time.time() - start_time,
        "lookups_performed": lookups_performed,
        "total_citations_found": total_found,
        "auto_passed": auto_passed,
        "skipped": skipped,
        "mismatches_before_filter": filter_stats.get("kept_count", 0) + filter_stats.get("filtered_count", 0),
        "filtered_count": filter_stats.get("filtered_count", 0),
        "turns": turn + 1,
    }

    return issues, stats
