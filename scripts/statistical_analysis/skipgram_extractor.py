"""
Skip-gram Pattern Extractor for Enhanced Phrase Matching

Extracts non-contiguous word patterns (skip-grams) within sliding windows.
This captures patterns like "כִּֽי חָסִ֥יתִי בָֽךְ" even when words appear with intervening text.
"""

import sqlite3
from pathlib import Path
from typing import List, Tuple, Set, Dict
from itertools import combinations
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
TANAKH_DB_PATH = Path(__file__).parent.parent.parent / "database" / "tanakh.db"


class SkipgramExtractor:
    """Extracts skip-gram patterns from psalm text."""

    def __init__(self):
        """Initialize extractor."""
        self.conn = None

    def connect_db(self):
        """Connect to Tanakh database."""
        if not TANAKH_DB_PATH.exists():
            raise FileNotFoundError(f"Tanakh database not found at {TANAKH_DB_PATH}")

        self.conn = sqlite3.connect(str(TANAKH_DB_PATH))
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Connected to {TANAKH_DB_PATH}")

    def close_db(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def get_psalm_words(self, psalm_number: int) -> List[Dict[str, str]]:
        """
        Get all words from a psalm in order.

        Args:
            psalm_number: Psalm number (1-150)

        Returns:
            List of word dictionaries with consonantal and Hebrew text
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                word_consonantal_split as consonantal,
                word as hebrew,
                chapter,
                verse,
                position
            FROM concordance
            WHERE book_name = 'Psalms' AND chapter = ?
            ORDER BY chapter, verse, position
        """, (psalm_number,))

        words = []
        for row in cursor.fetchall():
            words.append({
                'consonantal': row['consonantal'],
                'hebrew': row['hebrew'],
                'chapter': row['chapter'],
                'verse': row['verse'],
                'position': row['position']
            })

        return words

    def extract_skipgrams(
        self,
        words: List[Dict[str, str]],
        n: int,
        max_gap: int
    ) -> Set[Tuple[str, ...]]:
        """
        Extract n-word skip-grams within max_gap window.

        For n=2, max_gap=5: extracts all word pairs where the second word
        appears within 5 words of the first.

        For n=3, max_gap=7: extracts all word triples where the third word
        appears within 7 words of the first.

        Args:
            words: List of word dictionaries
            n: Number of words in pattern (2, 3, or 4+)
            max_gap: Maximum distance between first and last word

        Returns:
            Set of unique skip-gram tuples (consonantal forms)
        """
        skipgrams = set()
        consonantal_words = [w['consonantal'] for w in words]

        for i in range(len(consonantal_words)):
            # Define window: from position i to i+max_gap
            window_end = min(i + max_gap, len(consonantal_words))
            window_indices = range(i, window_end)

            # Generate all n-word combinations within window
            for combo_indices in combinations(window_indices, n):
                if len(combo_indices) == n:
                    # Extract consonantal forms for this pattern
                    pattern = tuple(consonantal_words[idx] for idx in combo_indices)
                    skipgrams.add(pattern)

        return skipgrams

    def extract_all_skipgrams(
        self,
        psalm_number: int
    ) -> Dict[int, Set[Tuple[str, ...]]]:
        """
        Extract all skip-gram patterns for a psalm.

        Extracts:
        - 2-word skip-grams (within 5-word window)
        - 3-word skip-grams (within 7-word window)
        - 4-word skip-grams (within 10-word window)

        Args:
            psalm_number: Psalm number (1-150)

        Returns:
            Dictionary mapping pattern length to set of patterns
        """
        words = self.get_psalm_words(psalm_number)

        if not words:
            logger.warning(f"No words found for Psalm {psalm_number}")
            return {}

        skipgrams = {}

        # Extract 2-word skip-grams (window=5)
        skipgrams[2] = self.extract_skipgrams(words, n=2, max_gap=5)

        # Extract 3-word skip-grams (window=7)
        skipgrams[3] = self.extract_skipgrams(words, n=3, max_gap=7)

        # Extract 4-word skip-grams (window=10)
        skipgrams[4] = self.extract_skipgrams(words, n=4, max_gap=10)

        return skipgrams

    def count_pattern_in_psalm(
        self,
        pattern: Tuple[str, ...],
        words: List[Dict[str, str]],
        max_gap: int
    ) -> int:
        """
        Count occurrences of a skip-gram pattern in a psalm.

        Args:
            pattern: Tuple of consonantal forms
            words: List of word dictionaries
            max_gap: Maximum gap to search within

        Returns:
            Number of occurrences
        """
        count = 0
        consonantal_words = [w['consonantal'] for w in words]
        n = len(pattern)

        for i in range(len(consonantal_words)):
            window_end = min(i + max_gap, len(consonantal_words))
            window_indices = range(i, window_end)

            # Check all n-word combinations in window
            for combo_indices in combinations(window_indices, n):
                if len(combo_indices) == n:
                    candidate = tuple(consonantal_words[idx] for idx in combo_indices)
                    if candidate == pattern:
                        count += 1

        return count

    def find_shared_skipgrams(
        self,
        psalm_a: int,
        psalm_b: int
    ) -> Dict[int, Set[Tuple[str, ...]]]:
        """
        Find skip-grams shared between two psalms.

        Args:
            psalm_a: First psalm number
            psalm_b: Second psalm number

        Returns:
            Dictionary mapping pattern length to set of shared patterns
        """
        skipgrams_a = self.extract_all_skipgrams(psalm_a)
        skipgrams_b = self.extract_all_skipgrams(psalm_b)

        shared = {}

        for length in [2, 3, 4]:
            if length in skipgrams_a and length in skipgrams_b:
                shared[length] = skipgrams_a[length] & skipgrams_b[length]
            else:
                shared[length] = set()

        return shared


def test_skipgram_extraction():
    """Test skip-gram extraction on Psalms 25 & 34."""
    logger.info("=" * 60)
    logger.info("SKIP-GRAM EXTRACTION TEST")
    logger.info("=" * 60)

    extractor = SkipgramExtractor()
    extractor.connect_db()

    # Test on Psalms 25 & 34
    psalm_25 = 25
    psalm_34 = 34

    logger.info(f"\nExtracting skip-grams from Psalm {psalm_25}...")
    skipgrams_25 = extractor.extract_all_skipgrams(psalm_25)

    logger.info(f"  2-word skip-grams: {len(skipgrams_25[2]):,}")
    logger.info(f"  3-word skip-grams: {len(skipgrams_25[3]):,}")
    logger.info(f"  4-word skip-grams: {len(skipgrams_25[4]):,}")
    logger.info(f"  Total: {sum(len(s) for s in skipgrams_25.values()):,}")

    logger.info(f"\nExtracting skip-grams from Psalm {psalm_34}...")
    skipgrams_34 = extractor.extract_all_skipgrams(psalm_34)

    logger.info(f"  2-word skip-grams: {len(skipgrams_34[2]):,}")
    logger.info(f"  3-word skip-grams: {len(skipgrams_34[3]):,}")
    logger.info(f"  4-word skip-grams: {len(skipgrams_34[4]):,}")
    logger.info(f"  Total: {sum(len(s) for s in skipgrams_34.values()):,}")

    logger.info(f"\nFinding shared skip-grams...")
    shared = extractor.find_shared_skipgrams(psalm_25, psalm_34)

    logger.info(f"  Shared 2-word skip-grams: {len(shared[2]):,}")
    logger.info(f"  Shared 3-word skip-grams: {len(shared[3]):,}")
    logger.info(f"  Shared 4-word skip-grams: {len(shared[4]):,}")
    logger.info(f"  Total shared: {sum(len(s) for s in shared.values()):,}")

    # Show some examples
    if shared[3]:
        logger.info(f"\nExample 3-word shared skip-grams:")
        for i, pattern in enumerate(list(shared[3])[:5], 1):
            logger.info(f"  {i}. {' '.join(pattern)}")

    extractor.close_db()


if __name__ == "__main__":
    test_skipgram_extraction()
