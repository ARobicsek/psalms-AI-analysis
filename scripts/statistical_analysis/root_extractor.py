"""
Root Extractor for Psalm Statistical Analysis

Extracts Hebrew word roots from Psalms using consonantal normalization
and morphological analysis (prefix/suffix stripping).

Strategy:
1. Load Hebrew text from tanakh.db
2. Clean text to remove paragraph markers ({פ}, {ס}, etc.)
3. Split on maqqef and whitespace
4. Normalize to consonantal form
5. Strip common prefixes (ה, ו, ב, כ, ל, מ, ש)
6. Strip common suffixes (pronominal, plural, etc.)
7. Extract n-grams (2-word and 3-word phrases)
"""

import sys
from pathlib import Path
import sqlite3
import re
from typing import List, Dict, Set, Tuple, Any
from collections import Counter, defaultdict
import logging

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from concordance.hebrew_text_processor import (
    strip_consonantal,
    split_on_maqqef,
    split_words
)

# Import text cleaning utilities
from text_cleaning import clean_hebrew_text, clean_word_list, is_paragraph_marker

logger = logging.getLogger(__name__)

# Common Hebrew prefixes (inseparable and separable)
COMMON_PREFIXES = [
    'ה',   # definite article
    'ו',   # conjunction (and)
    'ב',   # preposition (in, with)
    'כ',   # preposition (like, as)
    'ל',   # preposition (to, for)
    'מ',   # preposition (from)
    'ש',   # relative pronoun (that, which)
    'וה',  # conjunction + article
    'וב',  # conjunction + preposition
    'וכ',  # conjunction + preposition
    'ול',  # conjunction + preposition
    'ומ',  # conjunction + preposition
]

# Common Hebrew suffixes (pronominal, plural, etc.)
COMMON_SUFFIXES = [
    'י',    # my
    'ך',    # your (m.s.)
    'ך',    # your (f.s.)
    'ו',    # his
    'ה',    # her
    'נו',   # our
    'כם',   # your (m.p.)
    'כן',   # your (f.p.)
    'הם',   # their (m.)
    'הן',   # their (f.)
    'ים',   # plural (m.)
    'ות',   # plural (f.)
    'יו',   # his (archaic/poetic)
    'יך',   # your (poetic)
    'ני',   # me (object suffix)
    'תי',   # I (perfect verb)
    'ת',    # you (perfect verb)
    'נה',   # we/they (imperfect verb)
]


class RootExtractor:
    """Extracts Hebrew roots from Psalms."""

    def __init__(self, tanakh_db_path: Path):
        """
        Initialize root extractor.

        Args:
            tanakh_db_path: Path to tanakh.db database
        """
        self.tanakh_db_path = tanakh_db_path
        self.conn = sqlite3.connect(str(tanakh_db_path))
        self.conn.row_factory = sqlite3.Row

    def get_psalm_text(self, psalm_number: int) -> List[Dict[str, Any]]:
        """
        Get Hebrew text for a Psalm from database.

        Args:
            psalm_number: Psalm number (1-150)

        Returns:
            List of verse dicts with verse_number, hebrew, english
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT verse, hebrew, english
            FROM verses
            WHERE book_name = 'Psalms' AND chapter = ?
            ORDER BY verse
        """, (psalm_number,))

        verses = []
        for row in cursor.fetchall():
            verses.append({
                'verse': row['verse'],
                'hebrew': row['hebrew'] or '',
                'english': row['english'] or ''
            })

        return verses

    def normalize_word(self, word: str) -> str:
        """
        Normalize a Hebrew word to consonantal form.

        Args:
            word: Hebrew word (may have vowels/cantillation)

        Returns:
            Consonantal form (no diacritics)
        """
        return strip_consonantal(word)

    def strip_prefixes(self, word: str, max_prefixes: int = 2) -> str:
        """
        Strip common Hebrew prefixes from a word.

        Args:
            word: Consonantal Hebrew word
            max_prefixes: Maximum number of prefixes to strip

        Returns:
            Word with prefixes removed
        """
        if len(word) < 3:
            # Don't strip if word would become too short
            return word

        original = word
        prefixes_stripped = 0

        # Try to strip prefixes in order of length (longest first)
        for prefix in sorted(COMMON_PREFIXES, key=len, reverse=True):
            if prefixes_stripped >= max_prefixes:
                break

            if word.startswith(prefix) and len(word) > len(prefix) + 1:
                word = word[len(prefix):]
                prefixes_stripped += 1

        return word

    def strip_suffixes(self, word: str, max_suffixes: int = 1) -> str:
        """
        Strip common Hebrew suffixes from a word.

        Args:
            word: Consonantal Hebrew word
            max_suffixes: Maximum number of suffixes to strip

        Returns:
            Word with suffixes removed
        """
        if len(word) < 3:
            # Don't strip if word would become too short
            return word

        original = word
        suffixes_stripped = 0

        # Try to strip suffixes in order of length (longest first)
        for suffix in sorted(COMMON_SUFFIXES, key=len, reverse=True):
            if suffixes_stripped >= max_suffixes:
                break

            if word.endswith(suffix) and len(word) > len(suffix) + 1:
                word = word[:-len(suffix)]
                suffixes_stripped += 1

        return word

    def extract_root(self, word: str) -> str:
        """
        Extract the root form of a Hebrew word.

        Process:
        1. Normalize to consonantal
        2. Strip prefixes
        3. Strip suffixes

        Args:
            word: Hebrew word (may have vowels)

        Returns:
            Extracted root (consonantal, no affixes)
        """
        # Step 1: Normalize to consonantal
        normalized = self.normalize_word(word)

        if not normalized:
            return ''

        # Step 2: Strip prefixes (max 2)
        without_prefixes = self.strip_prefixes(normalized, max_prefixes=2)

        # Step 3: Strip suffixes (max 1)
        root = self.strip_suffixes(without_prefixes, max_suffixes=1)

        # Quality check: root should be at least 2 characters
        if len(root) < 2:
            # Use normalized form if stripping made it too short
            return normalized

        return root

    def extract_roots_from_verse(self, hebrew_text: str) -> Dict[str, List[str]]:
        """
        Extract all roots from a Hebrew verse.

        Args:
            hebrew_text: Hebrew verse text

        Returns:
            Dict mapping root -> list of original word forms
        """
        # STEP 1: Clean text to remove paragraph markers
        cleaned_text = clean_hebrew_text(hebrew_text)
        
        # Split on maqqef first
        text_split = split_on_maqqef(cleaned_text)

        # Split into words
        words = split_words(text_split)
        
        # STEP 2: Clean word list to remove any remaining markers
        words = clean_word_list(words)

        # Extract roots
        root_to_words = defaultdict(list)

        for word in words:
            if not word.strip():
                continue

            root = self.extract_root(word)

            if root and len(root) >= 2:
                root_to_words[root].append(word)

        return dict(root_to_words)

    def extract_ngrams(self, hebrew_text: str, n: int) -> List[Dict[str, Any]]:
        """
        Extract n-grams (consecutive word sequences) from Hebrew text.

        Args:
            hebrew_text: Hebrew verse text
            n: N-gram size (2 or 3)

        Returns:
            List of n-gram dicts with 'consonantal' and 'hebrew' forms
        """
        # STEP 1: Clean text to remove paragraph markers
        cleaned_text = clean_hebrew_text(hebrew_text)
        
        # Split on maqqef first
        text_split = split_on_maqqef(cleaned_text)

        # Split into words
        words = split_words(text_split)
        
        # STEP 2: Clean word list to remove any remaining markers
        words = clean_word_list(words)

        if len(words) < n:
            return []

        ngrams = []

        for i in range(len(words) - n + 1):
            ngram_words = words[i:i+n]

            # Create consonantal form (space-separated roots)
            roots = [self.extract_root(w) for w in ngram_words]
            consonantal = ' '.join(roots)

            # Keep original Hebrew (for display)
            hebrew = ' '.join(ngram_words)

            if all(len(r) >= 2 for r in roots):
                ngrams.append({
                    'consonantal': consonantal,
                    'hebrew': hebrew,
                    'length': n
                })

        return ngrams

    def extract_psalm_roots(self, psalm_number: int,
                           include_phrases: bool = True) -> Dict[str, Any]:
        """
        Extract all roots and phrases from a Psalm.

        Args:
            psalm_number: Psalm number (1-150)
            include_phrases: If True, also extract 2-grams and 3-grams

        Returns:
            Dict with 'roots' and 'phrases' data
        """
        verses = self.get_psalm_text(psalm_number)

        if not verses:
            logger.warning(f"No verses found for Psalm {psalm_number}")
            return {'roots': {}, 'phrases': []}

        # Accumulate roots across all verses
        all_roots = defaultdict(lambda: {'count': 0, 'examples': []})
        all_phrases = []

        for verse in verses:
            hebrew_text = verse['hebrew']

            # Extract roots from this verse
            verse_roots = self.extract_roots_from_verse(hebrew_text)

            for root, examples in verse_roots.items():
                all_roots[root]['count'] += len(examples)

                # Keep first 3 examples of each root
                if len(all_roots[root]['examples']) < 3:
                    all_roots[root]['examples'].extend(
                        examples[:3 - len(all_roots[root]['examples'])]
                    )

            # Extract phrases if requested
            if include_phrases:
                # 2-grams
                for ngram in self.extract_ngrams(hebrew_text, 2):
                    ngram['verse'] = verse['verse']
                    all_phrases.append(ngram)

                # 3-grams
                for ngram in self.extract_ngrams(hebrew_text, 3):
                    ngram['verse'] = verse['verse']
                    all_phrases.append(ngram)

        # Convert to regular dict
        roots_dict = {root: data for root, data in all_roots.items()}

        return {
            'psalm_number': psalm_number,
            'roots': roots_dict,
            'phrases': all_phrases
        }

    def close(self):
        """Close database connection."""
        self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


if __name__ == '__main__':
    # Test on sample Psalms
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    # Find tanakh.db
    db_path = Path(__file__).parent.parent.parent / 'database' / 'tanakh.db'

    if not db_path.exists():
        print(f"ERROR: tanakh.db not found at {db_path}")
        sys.exit(1)

    print(f"Using database: {db_path}\n")

    # Test with Psalm 23 (short, familiar psalm)
    print("=" * 60)
    print("Testing Root Extraction on Psalm 23 (with text cleaning)")
    print("=" * 60)

    with RootExtractor(db_path) as extractor:
        result = extractor.extract_psalm_roots(23, include_phrases=True)

        print(f"\nPsalm 23 Analysis:")
        print(f"  Total unique roots: {len(result['roots'])}")
        print(f"  Total phrases (2-grams + 3-grams): {len(result['phrases'])}")

        # Show top 10 most frequent roots
        print("\n  Top 10 Most Frequent Roots:")
        sorted_roots = sorted(
            result['roots'].items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:10]

        for i, (root, data) in enumerate(sorted_roots, 1):
            examples = ', '.join(data['examples'][:2])
            print(f"    {i}. {root} (count={data['count']}) - Examples: {examples}")

        # Show sample phrases
        print("\n  Sample 2-gram Phrases (first 5):")
        for phrase in result['phrases'][:5]:
            if phrase['length'] == 2:
                print(f"    {phrase['consonantal']} | {phrase['hebrew']} (v.{phrase['verse']})")

    # Test with Psalm 1 (contains {פ} marker)
    print("\n" + "=" * 60)
    print("Testing Root Extraction on Psalm 1 (contains {פ})")
    print("=" * 60)
    
    with RootExtractor(db_path) as extractor:
        result = extractor.extract_psalm_roots(1, include_phrases=False)
        
        print(f"\nPsalm 1 Analysis:")
        print(f"  Total unique roots: {len(result['roots'])}")
        
        # Check if {פ} appears in roots (it shouldn't!)
        has_marker = '{פ}' in result['roots'] or any('{' in root for root in result['roots'])
        
        if has_marker:
            print("  ✗ ERROR: Paragraph markers found in roots!")
        else:
            print("  ✓ SUCCESS: No paragraph markers in roots")

    print("\n" + "=" * 60)
    print("✓ Root extraction test complete!")
    print("=" * 60)
