"""
Skip-gram Pattern Extractor for Enhanced Phrase Matching

Extracts non-contiguous word patterns (skip-grams) within sliding windows.
This captures patterns like "כִּֽי חָסִ֥יתִי בָֽךְ" even when words appear with intervening text.

V3 Updates:
- Uses ROOT extraction instead of consonantal forms (consistent with contiguous phrases)
- Captures FULL Hebrew text span including gap words
- Removes paragraph markers before processing
"""

import sqlite3
from pathlib import Path
from typing import List, Tuple, Set, Dict
from itertools import combinations
import logging
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from concordance.hebrew_text_processor import strip_consonantal

# Import text cleaning and root extraction
from text_cleaning import clean_word_list, is_paragraph_marker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
TANAKH_DB_PATH = Path(__file__).parent.parent.parent / "database" / "tanakh.db"

# Import RootExtractor for root extraction
# We'll create a lightweight version here to avoid circular dependencies
from root_extractor import RootExtractor


class SkipgramExtractor:
    """Extracts skip-gram patterns from psalm text using root-based methodology."""

    def __init__(self):
        """Initialize extractor."""
        self.conn = None
        self.root_extractor = None

    def connect_db(self):
        """Connect to Tanakh database."""
        if not TANAKH_DB_PATH.exists():
            raise FileNotFoundError(f"Tanakh database not found at {TANAKH_DB_PATH}")

        self.conn = sqlite3.connect(str(TANAKH_DB_PATH))
        self.conn.row_factory = sqlite3.Row
        
        # Initialize root extractor
        self.root_extractor = RootExtractor(TANAKH_DB_PATH)
        
        logger.info(f"Connected to {TANAKH_DB_PATH}")

    def close_db(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
        if self.root_extractor:
            self.root_extractor.close()

    def get_psalm_words(self, psalm_number: int) -> List[Dict[str, str]]:
        """
        Get all words from a psalm in order.

        Args:
            psalm_number: Psalm number (1-150)

        Returns:
            List of word dictionaries with root, hebrew text, and position info
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
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
            hebrew_word = row['hebrew']
            
            # Skip paragraph markers and empty words
            if is_paragraph_marker(hebrew_word) or not hebrew_word.strip():
                continue
            
            # Extract root using root extractor
            root = self.root_extractor.extract_root(hebrew_word)
            
            # Only include words with valid roots (at least 2 chars)
            if root and len(root) >= 2:
                words.append({
                    'root': root,
                    'hebrew': hebrew_word,
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
    ) -> Set[Tuple[str, str, str]]:
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
            Set of unique skip-gram tuples: (pattern_roots, pattern_hebrew, full_span_hebrew)
        """
        skipgrams = set()
        
        for i in range(len(words)):
            # Define window: from position i to i+max_gap
            window_end = min(i + max_gap, len(words))
            window_indices = range(i, window_end)

            # Generate all n-word combinations within window
            for combo_indices in combinations(window_indices, n):
                if len(combo_indices) == n:
                    # Extract roots for the matched words
                    matched_roots = [words[idx]['root'] for idx in combo_indices]
                    pattern_roots = ' '.join(matched_roots)
                    
                    # Extract Hebrew for the matched words only
                    matched_hebrew = [words[idx]['hebrew'] for idx in combo_indices]
                    pattern_hebrew = ' '.join(matched_hebrew)
                    
                    # Extract FULL Hebrew span (from first to last index, including gaps)
                    first_idx = combo_indices[0]
                    last_idx = combo_indices[-1]
                    full_span_hebrew = ' '.join(words[idx]['hebrew'] 
                                                for idx in range(first_idx, last_idx + 1))
                    
                    # Store tuple: (roots, matched hebrew, full span hebrew)
                    skipgrams.add((pattern_roots, pattern_hebrew, full_span_hebrew))

        return skipgrams

    def extract_all_skipgrams(
        self,
        psalm_number: int
    ) -> Dict[int, Set[Tuple[str, str, str]]]:
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
            Each pattern is a tuple: (roots, matched_hebrew, full_span_hebrew)
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
        pattern_roots: str,
        words: List[Dict[str, str]],
        max_gap: int
    ) -> int:
        """
        Count occurrences of a skip-gram pattern in a psalm.

        Args:
            pattern_roots: Space-separated root forms
            words: List of word dictionaries
            max_gap: Maximum gap to search within

        Returns:
            Number of occurrences
        """
        count = 0
        roots = [w['root'] for w in words]
        pattern_list = pattern_roots.split()
        n = len(pattern_list)

        for i in range(len(roots)):
            window_end = min(i + max_gap, len(roots))
            window_indices = range(i, window_end)

            # Check all n-word combinations in window
            for combo_indices in combinations(window_indices, n):
                if len(combo_indices) == n:
                    candidate = [roots[idx] for idx in combo_indices]
                    if candidate == pattern_list:
                        count += 1

        return count

    def find_shared_skipgrams(
        self,
        psalm_a: int,
        psalm_b: int
    ) -> Dict[int, Set[Tuple[str, str, str]]]:
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
                # Find shared based on root patterns (first element of tuple)
                roots_a = {sg[0]: sg for sg in skipgrams_a[length]}
                roots_b = {sg[0]: sg for sg in skipgrams_b[length]}
                
                # Find common root patterns
                common_roots = set(roots_a.keys()) & set(roots_b.keys())
                
                # Include all tuples for common patterns
                shared[length] = {roots_a[r] for r in common_roots}
            else:
                shared[length] = set()

        return shared


def test_skipgram_extraction():
    """Test skip-gram extraction on Psalms 25 & 34."""
    logger.info("=" * 60)
    logger.info("SKIP-GRAM EXTRACTION TEST (V3 - Root-Based)")
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

    # Show some examples with full span
    if shared[3]:
        logger.info(f"\nExample 3-word shared skip-grams:")
        for i, pattern in enumerate(list(shared[3])[:5], 1):
            roots, matched_hebrew, full_span = pattern
            logger.info(f"  {i}. Roots: {roots}")
            logger.info(f"     Matched: {matched_hebrew}")
            logger.info(f"     Full span: {full_span}")
            logger.info("")

    # Test for paragraph markers
    logger.info("\nTesting for paragraph markers...")
    psalm_1 = extractor.get_psalm_words(1)
    has_markers = any(is_paragraph_marker(w['hebrew']) for w in psalm_1)
    
    if has_markers:
        logger.error("  ✗ ERROR: Paragraph markers found in word list!")
    else:
        logger.info("  ✓ SUCCESS: No paragraph markers in word list")

    extractor.close_db()


if __name__ == "__main__":
    test_skipgram_extraction()
