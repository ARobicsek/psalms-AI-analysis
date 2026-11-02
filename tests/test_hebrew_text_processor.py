"""Session 413: qamats qatan (U+05C7) is a vowel, never cantillation (src/concordance/hebrew_text_processor.py)."""

import sqlite3
from pathlib import Path

import pytest

from src.concordance.hebrew_text_processor import normalize_for_search, strip_cantillation, strip_vowels

DB = Path(__file__).parent.parent / "database" / "tanakh.db"
needs_db = pytest.mark.skipif(not (DB.exists() and DB.stat().st_size > 1_000_000), reason="no tanakh.db")

QAMATS_QATAN = "ׇ"


def test_the_voweled_level_keeps_qamats_qatan_and_drops_the_accent():
    assert strip_cantillation("אׇ֭זְנֶיךָ") == "אׇזְנֶיךָ"
    assert normalize_for_search("כׇּל־", "voweled") == "כׇּל־"


def test_the_consonantal_level_still_drops_it():
    assert strip_vowels("אׇזְנֶיךָ") == "אזניך"
    assert normalize_for_search("חׇכְמָה", "consonantal") == "חכמה"


@needs_db
def test_the_concordance_carries_it():
    # Before S413 the build stripped it from every token: 0 of 312,479.
    with sqlite3.connect(DB) as conn:
        words = [w for (w,) in conn.execute(
            "SELECT word_voweled FROM concordance WHERE book_name = 'Psalms' AND chapter = 130 AND verse = 2 "
            "ORDER BY position")]
        assert "אׇזְנֶיךָ" in words
        missing = conn.execute(
            "SELECT COUNT(*) FROM concordance WHERE word LIKE ? AND word_voweled NOT LIKE ?",
            (f"%{QAMATS_QATAN}%", f"%{QAMATS_QATAN}%")).fetchone()[0]
        assert missing == 0
