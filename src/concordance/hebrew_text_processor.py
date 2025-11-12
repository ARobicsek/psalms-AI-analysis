"""
Hebrew Text Processor

Provides utilities for normalizing Hebrew text at different levels.
Supports 4-layer normalization strategy for concordance searching:
1. Consonantal: Strip all diacritics (vowels + cantillation)
2. Voweled: Strip cantillation only, preserve vowels
3. Exact: Preserve everything
4. Lemma: Search by dictionary form (future implementation)

Unicode Ranges:
- Hebrew letters: U+05D0 to U+05EA
- Vowels (niqqud): U+05B0 to U+05BC
- Cantillation (te'amim): U+0591 to U+05C7
- Maqqef (hyphen): U+05BE
- Special marks: Geresh (U+05F3), Gershayim (U+05F4)
"""

import re
from typing import List, Tuple


# Unicode ranges for Hebrew text components
# Based on Unicode Hebrew block (U+0590-U+05FF)
CANTILLATION_RANGE = r'[\u0591-\u05AF\u05BD\u05BF\u05C0\u05C3-\u05C7]'  # te'amim marks
VOWEL_RANGE = r'[\u05B0-\u05BC\u05C1\u05C2]'  # niqqud points + shin/sin dots
COMBINED_DIACRITICS = r'[\u0591-\u05C7]'  # both cantillation and vowels (simplified)


def strip_cantillation(text: str) -> str:
    """
    Remove cantillation marks (te'amim) while preserving vowels and consonants.

    Args:
        text: Hebrew text with cantillation marks

    Returns:
        Text with cantillation removed, vowels and consonants preserved

    Example:
        >>> strip_cantillation("בְּרֵאשִׁ֖ית בָּרָ֣א")
        'בְּרֵאשִׁית בָּרָא'
    """
    if not text:
        return text

    # Remove only cantillation marks (U+0591-U+05C7), preserve vowels
    return re.sub(CANTILLATION_RANGE, '', text)


def strip_vowels(text: str) -> str:
    """
    Remove vowel points (niqqud) while preserving consonants.
    Also removes cantillation marks.

    Args:
        text: Hebrew text with vowels

    Returns:
        Text with only consonants (unpointed)

    Example:
        >>> strip_vowels("בְּרֵאשִׁ֖ית")
        'בראשית'
    """
    if not text:
        return text

    # Remove both cantillation and vowels
    return re.sub(COMBINED_DIACRITICS, '', text)


def strip_consonantal(text: str) -> str:
    """
    Alias for strip_vowels - returns consonants only.

    Args:
        text: Hebrew text with diacritics

    Returns:
        Text with consonants only
    """
    return strip_vowels(text)


def split_on_maqqef(text: str) -> str:
    """
    Replace maqqef (־) with space for searchability.

    This allows maqqef-connected morphemes to be found as individual words.
    Maqqef (U+05BE) traditionally connects words into single prosodic units,
    but for concordance searching, treating them as separate words improves
    searchability dramatically.

    Args:
        text: Hebrew text potentially containing maqqef

    Returns:
        Text with maqqef replaced by spaces

    Example:
        >>> split_on_maqqef("כִּֽי־הִכִּ֣יתָ")
        'כִּֽי הִכִּ֣יתָ'
    """
    return text.replace('\u05BE', ' ')


def normalize_for_search(text: str, level: str = 'consonantal') -> str:
    """
    Normalize Hebrew text at specified level for concordance searching.

    Args:
        text: Hebrew text to normalize
        level: Normalization level - 'exact', 'voweled', 'consonantal', or 'lemma'

    Returns:
        Normalized text ready for search/comparison

    Raises:
        ValueError: If level is not recognized

    Examples:
        >>> normalize_for_search("בְּרֵאשִׁ֖ית", level='exact')
        'בְּרֵאשִׁ֖ית'

        >>> normalize_for_search("בְּרֵאשִׁ֖ית", level='voweled')
        'בְּרֵאשִׁית'

        >>> normalize_for_search("בְּרֵאשִׁ֖ית", level='consonantal')
        'בראשית'
    """
    if not text:
        return text

    if level == 'exact':
        return text
    elif level == 'voweled':
        return strip_cantillation(text)
    elif level == 'consonantal':
        return strip_consonantal(text)
    elif level == 'lemma':
        # Future: implement lemmatization
        # For now, use consonantal as fallback
        return strip_consonantal(text)
    else:
        raise ValueError(f"Unknown normalization level: {level}. "
                        f"Use 'exact', 'voweled', 'consonantal', or 'lemma'")


def normalize_for_search_split(text: str, level: str = 'consonantal') -> str:
    """
    Normalize Hebrew text for search with maqqef splitting.

    This variant replaces maqqef with spaces BEFORE normalization,
    allowing maqqef-connected words to be searchable as separate tokens.

    Args:
        text: Hebrew text to normalize
        level: Normalization level

    Returns:
        Normalized text with maqqefs replaced by spaces

    Example:
        >>> normalize_for_search_split("כִּֽי־הִכִּ֣יתָ", level='consonantal')
        'כי הכית'
    """
    # First split on maqqef
    text = split_on_maqqef(text)
    # Then normalize normally
    return normalize_for_search(text, level)


def split_words(text: str) -> List[str]:
    """
    Split Hebrew text into individual words.

    Args:
        text: Hebrew text (verse or phrase)

    Returns:
        List of words (whitespace-separated)

    Example:
        >>> split_words("יְהוָה רֹעִי לֹא אֶחְסָר")
        ['יְהוָה', 'רֹעִי', 'לֹא', 'אֶחְסָר']
    """
    if not text:
        return []

    # Split on whitespace and filter empty strings
    return [word for word in text.split() if word.strip()]


def normalize_word_sequence(words: List[str], level: str = 'consonantal') -> List[str]:
    """
    Normalize a sequence of Hebrew words at specified level.

    Args:
        words: List of Hebrew words
        level: Normalization level

    Returns:
        List of normalized words

    Example:
        >>> normalize_word_sequence(['יְהוָה', 'רֹעִי'], level='consonantal')
        ['יהוה', 'רעי']
    """
    return [normalize_for_search(word, level) for word in words]


def normalize_phrase(phrase: str, level: str = 'consonantal') -> Tuple[str, List[str]]:
    """
    Normalize a Hebrew phrase for searching.

    Args:
        phrase: Multi-word Hebrew phrase
        level: Normalization level

    Returns:
        Tuple of (normalized_phrase, list_of_normalized_words)

    Example:
        >>> normalize_phrase("יְהוָה רֹעִי", level='consonantal')
        ('יהוה רעי', ['יהוה', 'רעי'])
    """
    words = split_words(phrase)
    normalized_words = normalize_word_sequence(words, level)
    normalized_phrase = ' '.join(normalized_words)

    return normalized_phrase, normalized_words


def is_hebrew_text(text: str) -> bool:
    """
    Check if text contains Hebrew characters.

    Args:
        text: Text to check

    Returns:
        True if text contains Hebrew letters

    Example:
        >>> is_hebrew_text("בראשית")
        True
        >>> is_hebrew_text("Genesis")
        False
    """
    if not text:
        return False

    # Check for Hebrew letters (U+05D0 to U+05EA)
    hebrew_pattern = r'[\u05D0-\u05EA]'
    return bool(re.search(hebrew_pattern, text))


def clean_hebrew_text(text: str) -> str:
    """
    Clean Hebrew text by removing non-Hebrew characters and extra whitespace.
    Preserves Hebrew letters, vowels, cantillation, and common punctuation.

    Args:
        text: Hebrew text potentially with extraneous characters

    Returns:
        Cleaned Hebrew text

    Example:
        >>> clean_hebrew_text("  בְּרֵאשִׁ֖ית  123  ")
        'בְּרֵאשִׁ֖ית'
    """
    if not text:
        return text

    # Keep Hebrew letters, vowels, cantillation, and basic punctuation
    # Hebrew range: U+0590-U+05FF
    pattern = r'[^\u0590-\u05FF\s]'
    cleaned = re.sub(pattern, '', text)

    # Normalize whitespace
    cleaned = ' '.join(cleaned.split())

    return cleaned


def main():
    """Demo of Hebrew text processing capabilities."""
    import sys

    # Ensure UTF-8 for Hebrew output on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print("=== Hebrew Text Processor Demo ===\n")

    # Example text: "In the beginning" (Genesis 1:1 opening)
    sample = "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים"

    print(f"Original text: {sample}\n")

    print("Normalization Levels:")
    print(f"  Exact:        {normalize_for_search(sample, 'exact')}")
    print(f"  Voweled:      {normalize_for_search(sample, 'voweled')}")
    print(f"  Consonantal:  {normalize_for_search(sample, 'consonantal')}\n")

    # Phrase search example: "The LORD is my shepherd"
    phrase = "יְהוָה רֹעִי"
    print(f"Phrase: {phrase}")
    normalized, words = normalize_phrase(phrase, 'consonantal')
    print(f"  Normalized: {normalized}")
    print(f"  Words: {words}\n")

    # Word splitting
    verse = "יְהוָה רֹעִי לֹא אֶחְסָר"
    print(f"Verse: {verse}")
    print(f"  Words: {split_words(verse)}\n")

    # Text validation
    print("Text validation:")
    print(f"  is_hebrew_text('שָׁלוֹם'): {is_hebrew_text('שָׁלוֹם')}")
    print(f"  is_hebrew_text('Shalom'): {is_hebrew_text('Shalom')}")


if __name__ == '__main__':
    main()
