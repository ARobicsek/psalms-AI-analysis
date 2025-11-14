"""
Text Cleaning Utility for Hebrew Psalm Analysis

Removes paragraph markers and non-word elements from Hebrew text
before root extraction and phrase analysis.
"""

import re
from typing import List


# Paragraph markers to remove
PARAGRAPH_MARKERS = [
    '{פ}',   # Petucha (open paragraph)
    '{ס}',   # Setuma (closed paragraph)
    '{ש}',   # Shir (song marker)
    '{ר}',   # Revi'i (quarter marker)
]

# Other marks to remove
NON_WORD_MARKS = [
    '׀',     # Paseq (separating mark)
    '׃',     # Sof pasuq (end of verse) - handled by strip
    '־',     # Maqqef is preserved as word connector (handled separately)
]


def clean_hebrew_text(text: str) -> str:
    """
    Remove paragraph markers and non-word elements from Hebrew text.
    
    This function removes:
    - Paragraph markers: {פ}, {ס}, {ש}, {ר}, etc.
    - Brackets and parentheses that aren't part of actual text
    - Paseq marks (׀)
    - Empty strings from processing
    
    Preserves:
    - Actual Hebrew text with nikud (vowel points)
    - Maqqef (־) as word connector (handled by caller)
    - Sof pasuq and other terminal punctuation
    
    Args:
        text: Hebrew text (may contain markers and diacritics)
    
    Returns:
        Cleaned Hebrew text with markers removed
    
    Examples:
        >>> clean_hebrew_text("אַ֥שְֽׁרֵי הָאִ֗ישׁ {פ}")
        "אַ֥שְֽׁרֵי הָאִ֗ישׁ"
        
        >>> clean_hebrew_text("כִּ֤י אִ֥ם ׀ בְּתוֹרַ֥ת")
        "כִּ֤י אִ֥ם בְּתוֹרַ֥ת"
    """
    if not text:
        return ""
    
    cleaned = text
    
    # Remove paragraph markers (with braces)
    for marker in PARAGRAPH_MARKERS:
        cleaned = cleaned.replace(marker, '')
    
    # Remove any remaining braces with Hebrew letters
    # Pattern: { followed by Hebrew letters followed by }
    cleaned = re.sub(r'\{[\u0590-\u05FF]+\}', '', cleaned)
    
    # Remove paseq marks
    cleaned = cleaned.replace('׀', '')
    
    # Remove empty braces
    cleaned = cleaned.replace('{}', '')
    cleaned = cleaned.replace('{', '').replace('}', '')
    
    # Clean up multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Strip leading/trailing whitespace
    cleaned = cleaned.strip()
    
    return cleaned


def clean_word_list(words: List[str]) -> List[str]:
    """
    Remove paragraph markers and empty words from a word list.
    
    This is for cleaning word lists extracted from the database,
    where markers might appear as separate "words".
    
    Args:
        words: List of Hebrew words (may include markers)
    
    Returns:
        Cleaned list with markers and empty strings removed
    
    Examples:
        >>> clean_word_list(['אַשְׁרֵי', 'הָאִישׁ', '{פ}', 'כִּי'])
        ['אַשְׁרֵי', 'הָאִישׁ', 'כִּי']
        
        >>> clean_word_list(['word1', '׀', '', 'word2'])
        ['word1', 'word2']
    """
    cleaned = []
    
    for word in words:
        # Skip if empty
        if not word or not word.strip():
            continue
        
        # Skip if it's a paragraph marker
        if word in PARAGRAPH_MARKERS:
            continue
        
        # Skip if it's only braces with Hebrew
        if re.match(r'^\{[\u0590-\u05FF]+\}$', word):
            continue
        
        # Skip if it's only paseq
        if word == '׀':
            continue
        
        # Skip if it's only whitespace or punctuation
        if re.match(r'^[\s\u0590-\u05AF\u05C0\u05C3\u05C6\u05F3\u05F4]+$', word):
            # This matches only cantillation, vowels, and marks
            # (but not letters)
            continue
        
        cleaned.append(word)
    
    return cleaned


def is_paragraph_marker(word: str) -> bool:
    """
    Check if a word is a paragraph marker.
    
    Args:
        word: Word to check
    
    Returns:
        True if word is a paragraph marker, False otherwise
    
    Examples:
        >>> is_paragraph_marker('{פ}')
        True
        
        >>> is_paragraph_marker('אלהים')
        False
    """
    if not word:
        return False
    
    # Check exact matches
    if word in PARAGRAPH_MARKERS:
        return True
    
    # Check pattern: braces with Hebrew letters
    if re.match(r'^\{[\u0590-\u05FF]+\}$', word):
        return True
    
    # Check if it's only paseq
    if word == '׀':
        return True
    
    return False


# Tests
def test_clean_hebrew_text():
    """Test clean_hebrew_text function."""
    print("Testing clean_hebrew_text()...")
    
    tests = [
        # (input, expected_output, description)
        ("אַ֥שְֽׁרֵי הָאִ֗ישׁ {פ}", "אַ֥שְֽׁרֵי הָאִ֗ישׁ", "Remove {פ} marker"),
        ("כִּ֤י אִ֥ם ׀ בְּתוֹרַ֥ת", "כִּ֤י אִ֥ם בְּתוֹרַ֥ת", "Remove paseq"),
        ("text {ס} more text", "text more text", "Remove {ס} marker"),
        ("מִזְמוֹר {פ} לְדָוִד", "מִזְמוֹר לְדָוִד", "Remove marker between words"),
        ("", "", "Empty string"),
        ("   spaces   ", "spaces", "Trim spaces"),
        ("word1  word2", "word1 word2", "Normalize multiple spaces"),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected, description in tests:
        result = clean_hebrew_text(input_text)
        if result == expected:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ {description}")
            print(f"    Expected: '{expected}'")
            print(f"    Got:      '{result}'")
            failed += 1
    
    print(f"\n  Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_clean_word_list():
    """Test clean_word_list function."""
    print("Testing clean_word_list()...")
    
    tests = [
        # (input, expected_output, description)
        (['אַשְׁרֵי', 'הָאִישׁ', '{פ}'], ['אַשְׁרֵי', 'הָאִישׁ'], "Remove {פ} from list"),
        (['word1', '׀', 'word2'], ['word1', 'word2'], "Remove paseq from list"),
        (['word1', '', 'word2'], ['word1', 'word2'], "Remove empty strings"),
        (['{פ}', '{ס}', 'word'], ['word'], "Remove multiple markers"),
        ([], [], "Empty list"),
        (['word'], ['word'], "Single word"),
    ]
    
    passed = 0
    failed = 0
    
    for input_list, expected, description in tests:
        result = clean_word_list(input_list)
        if result == expected:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ {description}")
            print(f"    Expected: {expected}")
            print(f"    Got:      {result}")
            failed += 1
    
    print(f"\n  Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_is_paragraph_marker():
    """Test is_paragraph_marker function."""
    print("Testing is_paragraph_marker()...")
    
    tests = [
        # (input, expected_output, description)
        ('{פ}', True, "{פ} is a marker"),
        ('{ס}', True, "{ס} is a marker"),
        ('׀', True, "Paseq is a marker"),
        ('אלהים', False, "Hebrew word is not a marker"),
        ('', False, "Empty string is not a marker"),
        ('test', False, "English word is not a marker"),
    ]
    
    passed = 0
    failed = 0
    
    for input_word, expected, description in tests:
        result = is_paragraph_marker(input_word)
        if result == expected:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ {description}")
            print(f"    Expected: {expected}")
            print(f"    Got:      {result}")
            failed += 1
    
    print(f"\n  Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_real_data():
    """Test with real data from database."""
    print("Testing with real Psalm data...")
    
    import sqlite3
    from pathlib import Path
    
    db_path = Path(__file__).parent.parent.parent / 'database' / 'tanakh.db'
    
    if not db_path.exists():
        print("  ⚠ Database not found, skipping real data test")
        return True
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Test on Psalm 1 (contains {פ} at end)
    cursor.execute("""
        SELECT word, word_consonantal_split
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 1
        ORDER BY verse, position
    """)
    
    words = [row[0] for row in cursor.fetchall()]
    
    print(f"  Original word count: {len(words)}")
    print(f"  Sample words: {words[:5]}")
    
    # Clean the word list
    cleaned = clean_word_list(words)
    
    print(f"  Cleaned word count: {len(cleaned)}")
    print(f"  Removed: {len(words) - len(cleaned)} markers")
    
    # Check that {פ} was removed
    has_markers = any(is_paragraph_marker(w) for w in cleaned)
    
    if has_markers:
        print("  ✗ Markers still present after cleaning!")
        return False
    else:
        print("  ✓ All markers successfully removed")
        return True


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("TEXT CLEANING UTILITY - TEST SUITE")
    print("=" * 60)
    print()
    
    results = []
    
    results.append(("clean_hebrew_text", test_clean_hebrew_text()))
    results.append(("clean_word_list", test_clean_word_list()))
    results.append(("is_paragraph_marker", test_is_paragraph_marker()))
    results.append(("real_data", test_real_data()))
    
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    
    return all_passed


if __name__ == '__main__':
    run_all_tests()
