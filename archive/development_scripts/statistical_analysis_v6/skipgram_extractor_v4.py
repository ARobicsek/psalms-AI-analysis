"""
Skip-gram Pattern Extractor V4 - With Verse Tracking and Enhanced Deduplication

V4 Enhancements:
1. Tracks verse numbers for each skipgram occurrence
2. Enables proper deduplication by (full_span, verse) pairs
3. Supports populating matches_from_a/b arrays in output
4. Groups overlapping patterns from the same location

This fixes the V3 issue where multiple overlapping skipgrams from the same phrase
(e.g., "מר אל כי בך", "מר אל כי חסי", etc.) were all counted separately.
"""

import sqlite3
from pathlib import Path
from typing import List, Tuple, Set, Dict
from itertools import combinations
from collections import defaultdict
import logging
import sys
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from concordance.hebrew_text_processor import strip_consonantal

# Import text cleaning and root extraction
from text_cleaning import clean_word_list, is_paragraph_marker

# Import word classifier for content word filtering
from hebrew_analysis.word_classifier import HebrewWordClassifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
TANAKH_DB_PATH = Path(__file__).parent.parent.parent / "database" / "tanakh.db"

# Import sophisticated RootExtractor with ETCBC morphology
# This provides more accurate root extraction and reduces false positives
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
    from hebrew_analysis.root_extractor_v2 import EnhancedRootExtractor as RootExtractor
    logger.info("Using enhanced root extractor with ETCBC morphology")
except ImportError:
    # Fallback to basic root extractor if enhanced version unavailable
    from root_extractor import RootExtractor
    logger.warning("Enhanced root extractor unavailable, using basic version")


class SkipgramExtractorV4:
    """
    Extracts skip-gram patterns with verse tracking for V4.

    Key improvement: Each skipgram instance is now tracked by verse number,
    enabling proper deduplication of overlapping patterns from the same location.

    V5 Enhancement: Content word filtering and pattern stoplist
    - Filters patterns based on content word count
    - Applies stoplist to remove high-frequency formulaic patterns
    """

    def __init__(self, enable_quality_filtering: bool = True):
        """
        Initialize extractor.

        Args:
            enable_quality_filtering: If True, apply content word filtering and stoplist
        """
        self.conn = None
        self.root_extractor = None
        self.enable_quality_filtering = enable_quality_filtering

        # Initialize word classifier for content word analysis
        self.word_classifier = HebrewWordClassifier()

        # Load pattern stoplist
        self.stoplist_skipgrams = set()
        self.stoplist_contiguous = set()
        self._load_pattern_stoplist()

        # Statistics for filtering
        self.stats = {
            'total_extracted': 0,
            'filtered_by_content': 0,
            'filtered_by_stoplist': 0,
            'kept': 0
        }

    def _load_pattern_stoplist(self):
        """Load pattern stoplist from JSON file."""
        stoplist_path = Path(__file__).parent.parent.parent / "src" / "hebrew_analysis" / "data" / "pattern_stoplist.json"

        if not stoplist_path.exists():
            logger.warning(f"Pattern stoplist not found at {stoplist_path}, continuing without stoplist")
            return

        try:
            with open(stoplist_path, 'r', encoding='utf-8') as f:
                stoplist_data = json.load(f)
                self.stoplist_skipgrams = set(stoplist_data.get('skipgrams', []))
                self.stoplist_contiguous = set(stoplist_data.get('contiguous', []))
                logger.info(f"Loaded pattern stoplist: {len(self.stoplist_skipgrams)} skipgram patterns, {len(self.stoplist_contiguous)} contiguous patterns")
        except Exception as e:
            logger.warning(f"Error loading pattern stoplist: {e}, continuing without stoplist")

    def _should_keep_pattern(self, pattern_roots: str, gap_word_count: int) -> Tuple[bool, str]:
        """
        Determine if a pattern should be kept based on quality filters.

        Applies:
        1. Content word filtering (Priority 1)
        2. Pattern stoplist (Priority 2)

        Args:
            pattern_roots: Space-separated root words
            gap_word_count: Number of gap words (0 for contiguous)

        Returns:
            Tuple of (should_keep: bool, reason: str)
        """
        if not self.enable_quality_filtering:
            return True, "Filtering disabled"

        self.stats['total_extracted'] += 1

        # Split pattern into words
        words = pattern_roots.split()
        is_contiguous = (gap_word_count == 0)

        # Check stoplist first (most efficient)
        stoplist = self.stoplist_contiguous if is_contiguous else self.stoplist_skipgrams
        if pattern_roots in stoplist:
            self.stats['filtered_by_stoplist'] += 1
            return False, f"In stoplist ({'contiguous' if is_contiguous else 'skipgram'})"

        # Analyze content words
        analysis = self.word_classifier.analyze_pattern(words)
        content_count = analysis['content_word_count']
        pattern_length = len(words)

        # Apply content word thresholds (Priority 1)
        # OPTION A: Conservative (recommended starting point)
        if is_contiguous:
            # Contiguous phrases: require >= 1 content word
            min_content = 1
        else:
            # Skipgrams: require >= 1 content word for 2-word, >= 2 for 3+ word
            if pattern_length == 2:
                min_content = 1
            else:
                min_content = 2

        if content_count < min_content:
            self.stats['filtered_by_content'] += 1
            category = analysis['category']
            return False, f"Only {content_count} content words (need >= {min_content}, category: {category})"

        self.stats['kept'] += 1
        return True, f"Has {content_count} content words (>= {min_content})"

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

    def get_psalm_words(self, psalm_number: int) -> List[Dict[str, any]]:
        """
        Get all words from a psalm in order with verse tracking.

        Args:
            psalm_number: Psalm number (1-150)

        Returns:
            List of word dictionaries with root, hebrew text, verse, and position
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

    def extract_skipgrams_with_verse(
        self,
        words: List[Dict[str, any]],
        n: int,
        max_gap: int
    ) -> List[Dict[str, any]]:
        """
        Extract n-word skip-grams with verse tracking.

        V4 Enhancement: Returns list of skipgram instances (not deduplicated set),
        each with verse number and position information.

        Args:
            words: List of word dictionaries
            n: Number of words in pattern (2, 3, or 4)
            max_gap: Maximum distance between first and last word

        Returns:
            List of skipgram dictionaries with:
            - pattern_roots: space-separated roots
            - pattern_hebrew: matched words only
            - full_span_hebrew: full text including gaps
            - verse: verse number where this instance appears
            - first_position: position of first word
            - length: number of words in pattern
        """
        skipgrams = []

        for i in range(len(words)):
            # Define window: from position i to i+max_gap
            window_end = min(i + max_gap, len(words))
            window_indices = range(i, window_end)

            # Generate all n-word combinations within window
            for combo_indices in combinations(window_indices, n):
                if len(combo_indices) == n:
                    # CRITICAL FIX: Ensure all words are from the SAME verse
                    # Skip combinations that cross verse boundaries
                    verses_in_combo = set(words[idx]['verse'] for idx in combo_indices)
                    if len(verses_in_combo) > 1:
                        # This combination crosses verse boundaries - skip it
                        continue

                    # Extract roots for the matched words
                    matched_roots = [words[idx]['root'] for idx in combo_indices]
                    pattern_roots = ' '.join(matched_roots)

                    # Extract Hebrew for the matched words only
                    matched_hebrew = [words[idx]['hebrew'] for idx in combo_indices]
                    pattern_hebrew = ' '.join(matched_hebrew)

                    # Extract FULL Hebrew span (from first to last index, including gaps)
                    first_idx = combo_indices[0]
                    last_idx = combo_indices[-1]

                    # CRITICAL FIX: Only include words from the same verse in full span
                    # This prevents including words from the next verse
                    verse = words[first_idx]['verse']
                    full_span_hebrew = ' '.join(words[idx]['hebrew']
                                                for idx in range(first_idx, last_idx + 1)
                                                if words[idx]['verse'] == verse)

                    first_position = words[first_idx]['position']

                    # Calculate gap size (number of words between first and last matched word)
                    # For contiguous words (no gap), this is 0
                    # For words with gaps, this is the span minus the matched words
                    gap_word_count = (last_idx - first_idx + 1) - n

                    # Skip patterns with gap_word_count=0 - these are contiguous phrases
                    # By definition, skipgrams must have at least one word gap between matched words
                    # Contiguous patterns should be extracted by the contiguous phrase extractor
                    if gap_word_count == 0:
                        continue

                    # V5: Check quality filters before adding
                    should_keep, reason = self._should_keep_pattern(pattern_roots, gap_word_count)

                    if should_keep:
                        # Analyze content words for metadata
                        analysis = self.word_classifier.analyze_pattern(matched_roots)

                        # Create skipgram instance with V5 enhancements
                        skipgrams.append({
                            'pattern_roots': pattern_roots,
                            'pattern_hebrew': pattern_hebrew,
                            'full_span_hebrew': full_span_hebrew,
                            'verse': verse,
                            'first_position': first_position,
                            'length': n,
                            'gap_word_count': gap_word_count,
                            # V5: Add content word metadata
                            'content_word_count': analysis['content_word_count'],
                            'content_word_ratio': analysis['content_word_ratio'],
                            'pattern_category': analysis['category']
                        })

        return skipgrams

    def deduplicate_skipgrams(
        self,
        skipgrams: List[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """
        Deduplicate exact duplicate skipgrams only.

        V4.1: Moved overlap-based deduplication to scoring time, since different
        psalm pairs may share different subsets of overlapping skipgrams.
        At extraction time, we only remove exact duplicates.

        Args:
            skipgrams: List of skipgram instances

        Returns:
            List with exact duplicates removed
        """
        # Use a set to track unique skipgrams
        # Key: (pattern_roots, verse, first_position)
        seen = set()
        deduplicated = []

        for sg in skipgrams:
            key = (sg['pattern_roots'], sg['verse'], sg['first_position'])
            if key not in seen:
                seen.add(key)
                deduplicated.append(sg)

        return deduplicated

    def _find_overlapping_groups(self, skipgrams: List[Dict]) -> List[List[Dict]]:
        """
        Find groups of skipgrams with substantial overlap (>50% of shorter span).

        This prevents over-aggressive transitive merging while still catching
        multiple patterns extracted from the same phrase.

        Args:
            skipgrams: List of skipgrams with _start_pos and _end_pos fields

        Returns:
            List of groups, where each group contains substantially overlapping skipgrams
        """
        if not skipgrams:
            return []

        # Use a more conservative approach: group by overlap similarity
        # Build an adjacency structure for skipgrams that overlap substantially
        n = len(skipgrams)
        overlaps = set()

        for i in range(n):
            for j in range(i + 1, n):
                if self._has_substantial_overlap(skipgrams[i], skipgrams[j]):
                    overlaps.add((i, j))

        # Use union-find to group connected skipgrams
        parent = list(range(n))

        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        for i, j in overlaps:
            union(i, j)

        # Group skipgrams by their root parent
        groups_dict = defaultdict(list)
        for i, sg in enumerate(skipgrams):
            root = find(i)
            groups_dict[root].append(sg)

        return list(groups_dict.values())

    def _has_substantial_overlap(self, sg1: Dict, sg2: Dict) -> bool:
        """
        Check if two skipgrams have substantial overlap (>50% of shorter span).

        Args:
            sg1, sg2: Skipgrams with _start_pos and _end_pos

        Returns:
            True if overlap is substantial
        """
        start1, end1 = sg1['_start_pos'], sg1['_end_pos']
        start2, end2 = sg2['_start_pos'], sg2['_end_pos']

        # Calculate overlap
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)

        if overlap_start > overlap_end:
            return False  # No overlap

        overlap_length = overlap_end - overlap_start + 1
        span1_length = end1 - start1 + 1
        span2_length = end2 - start2 + 1
        shorter_span = min(span1_length, span2_length)

        # Require >80% overlap of the shorter span (conservative)
        return overlap_length > shorter_span * 0.8

    def extract_all_skipgrams(
        self,
        psalm_number: int,
        deduplicate: bool = True
    ) -> Dict[int, List[Dict[str, any]]]:
        """
        Extract all skip-gram patterns for a psalm with verse tracking.

        Extracts:
        - 2-word skip-grams (within 5-word window)
        - 3-word skip-grams (within 7-word window)
        - 4-word skip-grams (within 10-word window)

        Args:
            psalm_number: Psalm number (1-150)
            deduplicate: If True, deduplicate overlapping patterns

        Returns:
            Dictionary mapping pattern length to list of skipgram instances
        """
        words = self.get_psalm_words(psalm_number)

        if not words:
            logger.warning(f"No words found for Psalm {psalm_number}")
            return {}

        # Extract skipgrams with verse tracking
        skipgrams_2 = self.extract_skipgrams_with_verse(words, n=2, max_gap=5)
        skipgrams_3 = self.extract_skipgrams_with_verse(words, n=3, max_gap=7)
        skipgrams_4 = self.extract_skipgrams_with_verse(words, n=4, max_gap=10)

        # Combine all skipgrams
        all_skipgrams = skipgrams_2 + skipgrams_3 + skipgrams_4

        # Deduplicate overlapping patterns if requested
        if deduplicate:
            all_skipgrams = self.deduplicate_skipgrams(all_skipgrams)

        # Group by length for output
        skipgrams_by_length = defaultdict(list)
        for sg in all_skipgrams:
            skipgrams_by_length[sg['length']].append(sg)

        return dict(skipgrams_by_length)

    def find_shared_skipgrams(
        self,
        psalm_a: int,
        psalm_b: int
    ) -> Dict[int, List[Tuple[Dict, Dict]]]:
        """
        Find skip-grams shared between two psalms with verse tracking.

        Args:
            psalm_a: First psalm number
            psalm_b: Second psalm number

        Returns:
            Dictionary mapping pattern length to list of (instance_a, instance_b) tuples
        """
        skipgrams_a = self.extract_all_skipgrams(psalm_a, deduplicate=True)
        skipgrams_b = self.extract_all_skipgrams(psalm_b, deduplicate=True)

        shared = defaultdict(list)

        for length in [2, 3, 4]:
            if length in skipgrams_a and length in skipgrams_b:
                # Group by pattern_roots
                patterns_a = defaultdict(list)
                patterns_b = defaultdict(list)

                for sg in skipgrams_a[length]:
                    patterns_a[sg['pattern_roots']].append(sg)

                for sg in skipgrams_b[length]:
                    patterns_b[sg['pattern_roots']].append(sg)

                # Find common patterns
                common_patterns = set(patterns_a.keys()) & set(patterns_b.keys())

                # For each common pattern, pair up instances
                for pattern in common_patterns:
                    for inst_a in patterns_a[pattern]:
                        for inst_b in patterns_b[pattern]:
                            shared[length].append((inst_a, inst_b))

        return dict(shared)


def test_v4_deduplication():
    """Test V4 deduplication on example from user."""
    logger.info("=" * 60)
    logger.info("V4 SKIPGRAM DEDUPLICATION TEST")
    logger.info("=" * 60)

    extractor = SkipgramExtractorV4()
    extractor.connect_db()

    # Test on Psalm 16 (user's example: "שמרני אל כי חסיתי בך")
    psalm_16 = 16

    logger.info(f"\nExtracting skipgrams from Psalm {psalm_16} with deduplication...")
    skipgrams_dedup = extractor.extract_all_skipgrams(psalm_16, deduplicate=True)

    logger.info(f"\nExtracting skipgrams from Psalm {psalm_16} WITHOUT deduplication...")
    skipgrams_no_dedup = extractor.extract_all_skipgrams(psalm_16, deduplicate=False)

    # Compare counts
    total_dedup = sum(len(instances) for instances in skipgrams_dedup.values())
    total_no_dedup = sum(len(instances) for instances in skipgrams_no_dedup.values())

    logger.info(f"\nResults:")
    logger.info(f"  Without deduplication: {total_no_dedup:,} skipgrams")
    logger.info(f"  With deduplication: {total_dedup:,} skipgrams")
    logger.info(f"  Removed by deduplication: {total_no_dedup - total_dedup:,}")
    logger.info(f"  Reduction: {100 * (total_no_dedup - total_dedup) / total_no_dedup:.1f}%")

    # Show example of overlapping patterns that were deduplicated
    logger.info(f"\nExample: Looking for patterns from verse 1...")
    verse_1_patterns = [sg for sg in skipgrams_no_dedup.get(4, []) if sg['verse'] == 1]

    if verse_1_patterns:
        # Group by full_span
        by_span = defaultdict(list)
        for sg in verse_1_patterns:
            by_span[sg['full_span_hebrew']].append(sg['pattern_roots'])

        for full_span, patterns in list(by_span.items())[:3]:  # Show first 3 examples
            if len(patterns) > 1:
                logger.info(f"\n  Full span: {full_span}")
                logger.info(f"  Generated {len(patterns)} overlapping patterns:")
                for p in patterns[:5]:  # Show first 5
                    logger.info(f"    - {p}")
                if len(patterns) > 5:
                    logger.info(f"    ... and {len(patterns) - 5} more")

    extractor.close_db()
    logger.info("\n" + "=" * 60)


if __name__ == "__main__":
    test_v4_deduplication()
