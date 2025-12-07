#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Root-based Hebrew word matching utilities.
Handles morphological variations where vowel letters are inserted.
"""

def is_root_match(search_word: str, target_word: str) -> bool:
    """
    Check if two words are root-based matches.

    This handles cases like:
    - הלך matches הולך (vav inserted)
    - גור matches יגור (prefix added)
    - בלב matches בלבבו (suffix added)

    Args:
        search_word: The word being searched for
        target_word: The word to match against

    Returns:
        True if the words are root-based matches
    """
    # Exact match
    if search_word == target_word:
        return True

    # Check if search_word is a substring of target_word
    if search_word in target_word:
        return True

    # Check if target_word is a substring of search_word
    if target_word in search_word:
        return True

    # Check root-based matching: remove vowel letters (ו, י) and compare
    # This handles cases like הלך -> הולך
    search_no_vowels = ''.join(c for c in search_word if c not in 'ויןםןץצףפך')
    target_no_vowels = ''.join(c for c in target_word if c not in 'ויןםןץצףפך')

    if search_no_vowels and target_no_vowels:
        if search_no_vowels in target_no_vowels or target_no_vowels in search_no_vowels:
            return True

    # Check if all letters of search_word appear in target_word in order
    # This handles root matching with insertions
    if is_subsequence(search_word, target_word):
        return True

    if is_subsequence(target_word, search_word):
        return True

    return False

def is_subsequence(shorter: str, longer: str) -> bool:
    """
    Check if shorter is a subsequence of longer (letters appear in order).

    Args:
        shorter: The shorter string
        longer: The longer string

    Returns:
        True if all characters in shorter appear in longer in order
    """
    if not shorter or len(shorter) > len(longer):
        return False

    it = iter(longer)
    return all(c in it for c in shorter)

def find_root_matches(search_word: str, word_list: list) -> list:
    """
    Find all words in word_list that are root-based matches with search_word.

    Args:
        search_word: The word to search for
        word_list: List of words to check

    Returns:
        List of matching words
    """
    matches = []
    for word in word_list:
        if is_root_match(search_word, word):
            matches.append(word)
    return matches