"""
V6 Pattern Extraction - Fresh Generation from tanakh.db

Extracts roots and contiguous phrases for all psalm pairs using Session 115
morphology fixes. Generates completely fresh data with no dependency on V3/V4/V5.

Why V6:
- V5 reused old V4 roots/phrases (generated before Session 115 morphology fixes)
- V5 database skipgrams are correct, but JSON deduplicated_roots/phrases are wrong
- V6 generates everything fresh using current morphology.py

Features:
- Uses HebrewMorphologyAnalyzer with Session 115 fixes (hybrid stripping, plural
  protection, final letter normalization)
- Fresh IDF calculation for all roots
- Verse-level tracking for all matches
- No dependency on previous version files

Output: data/analysis_results/psalm_patterns_v6.json
"""

import sys
from pathlib import Path
import sqlite3
import json
import math
from typing import Dict, List, Tuple, Set, Any
from collections import defaultdict, Counter
import logging

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent))

from concordance.hebrew_text_processor import strip_consonantal, split_on_maqqef, split_words
from hebrew_analysis.morphology import HebrewMorphologyAnalyzer
from text_cleaning import clean_hebrew_text, clean_word_list

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class V6PatternExtractor:
    """Extracts fresh roots and phrases for V6."""

    def __init__(self, tanakh_db_path: Path):
        """
        Initialize V6 pattern extractor.

        Args:
            tanakh_db_path: Path to tanakh.db database
        """
        self.tanakh_db_path = tanakh_db_path
        self.conn = sqlite3.connect(str(tanakh_db_path))
        self.conn.row_factory = sqlite3.Row
        self.analyzer = HebrewMorphologyAnalyzer()

        # Cache for all psalm data
        self.psalm_roots: Dict[int, Dict[str, List[int]]] = {}  # psalm -> {root: [verses]}
        self.psalm_phrases: Dict[int, Dict[str, List[int]]] = {}  # psalm -> {phrase: [verses]}
        self.root_psalm_counts: Dict[str, int] = {}  # root -> number of psalms containing it

    def get_psalm_text(self, psalm_number: int) -> List[Dict[str, Any]]:
        """
        Get Hebrew text for a Psalm from database.

        Args:
            psalm_number: Psalm number (1-150)

        Returns:
            List of verse dicts with verse, hebrew
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT verse, hebrew
            FROM verses
            WHERE book_name = 'Psalms' AND chapter = ?
            ORDER BY verse
        """, (psalm_number,))

        verses = []
        for row in cursor.fetchall():
            verses.append({
                'verse': row['verse'],
                'hebrew': row['hebrew'] or ''
            })

        return verses

    def extract_roots_from_verse(self, hebrew_text: str, verse_number: int) -> Dict[str, List[int]]:
        """
        Extract roots from a Hebrew verse with verse tracking.

        Args:
            hebrew_text: Hebrew verse text
            verse_number: Verse number

        Returns:
            Dict mapping root -> [verse_number]
        """
        # Clean text
        cleaned_text = clean_hebrew_text(hebrew_text)
        text_split = split_on_maqqef(cleaned_text)
        words = split_words(text_split)
        words = clean_word_list(words)

        # Extract roots using Session 115 morphology
        root_to_verses = defaultdict(list)
        for word in words:
            if not word or len(word) < 2:
                continue
            root = self.analyzer.extract_root(word)
            if root and len(root) >= 2:
                root_to_verses[root].append(verse_number)

        return dict(root_to_verses)

    def extract_phrases_from_verse(self, hebrew_text: str, verse_number: int,
                                   min_length: int = 2, max_length: int = 6) -> Dict[str, List[int]]:
        """
        Extract contiguous phrases from a Hebrew verse.

        Args:
            hebrew_text: Hebrew verse text
            verse_number: Verse number
            min_length: Minimum phrase length (words)
            max_length: Maximum phrase length (words)

        Returns:
            Dict mapping phrase_roots -> [verse_number]
        """
        # Clean text
        cleaned_text = clean_hebrew_text(hebrew_text)
        text_split = split_on_maqqef(cleaned_text)
        words = split_words(text_split)
        words = clean_word_list(words)

        if len(words) < min_length:
            return {}

        # Extract roots for all words
        roots = []
        for word in words:
            if not word or len(word) < 2:
                continue
            root = self.analyzer.extract_root(word)
            if root and len(root) >= 2:
                roots.append(root)

        # Extract n-grams
        phrase_to_verses = defaultdict(list)
        for n in range(min_length, min(max_length + 1, len(roots) + 1)):
            for i in range(len(roots) - n + 1):
                phrase_roots = ' '.join(roots[i:i+n])
                phrase_to_verses[phrase_roots].append(verse_number)

        return dict(phrase_to_verses)

    def extract_psalm_data(self, psalm_number: int) -> None:
        """
        Extract all roots and phrases from a Psalm and cache them.

        Args:
            psalm_number: Psalm number (1-150)
        """
        verses = self.get_psalm_text(psalm_number)

        if not verses:
            logger.warning(f"No verses found for Psalm {psalm_number}")
            self.psalm_roots[psalm_number] = {}
            self.psalm_phrases[psalm_number] = {}
            return

        # Aggregate roots across all verses
        all_roots = defaultdict(list)
        all_phrases = defaultdict(list)

        for verse_data in verses:
            verse_num = verse_data['verse']
            hebrew = verse_data['hebrew']

            # Extract roots
            verse_roots = self.extract_roots_from_verse(hebrew, verse_num)
            for root, verses_list in verse_roots.items():
                all_roots[root].extend(verses_list)

            # Extract phrases
            verse_phrases = self.extract_phrases_from_verse(hebrew, verse_num)
            for phrase, verses_list in verse_phrases.items():
                all_phrases[phrase].extend(verses_list)

        # Deduplicate verse lists (same root/phrase can appear multiple times in same verse)
        for root in all_roots:
            all_roots[root] = sorted(set(all_roots[root]))
        for phrase in all_phrases:
            all_phrases[phrase] = sorted(set(all_phrases[phrase]))

        self.psalm_roots[psalm_number] = dict(all_roots)
        self.psalm_phrases[psalm_number] = dict(all_phrases)

    def calculate_idf_scores(self) -> Dict[str, float]:
        """
        Calculate IDF scores for all roots.

        IDF Formula: log(150 / psalm_count)
        - Higher IDF = rarer root
        - Lower IDF = common root

        Returns:
            Dict mapping root -> IDF score
        """
        # Count psalms containing each root
        root_psalm_counts = defaultdict(set)
        for psalm_num, roots_dict in self.psalm_roots.items():
            for root in roots_dict.keys():
                root_psalm_counts[root].add(psalm_num)

        # Calculate IDF
        idf_scores = {}
        for root, psalm_set in root_psalm_counts.items():
            psalm_count = len(psalm_set)
            idf_scores[root] = math.log(150 / psalm_count) if psalm_count > 0 else 0.0

        self.root_psalm_counts = {root: len(psalm_set) for root, psalm_set in root_psalm_counts.items()}

        return idf_scores

    def find_shared_roots(self, psalm_a: int, psalm_b: int, idf_scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Find shared roots between two psalms.

        Args:
            psalm_a: First psalm number
            psalm_b: Second psalm number
            idf_scores: IDF scores for all roots

        Returns:
            List of shared root dicts with root, idf, verses_a, verses_b
        """
        roots_a = self.psalm_roots.get(psalm_a, {})
        roots_b = self.psalm_roots.get(psalm_b, {})

        shared_roots = []
        for root in set(roots_a.keys()) & set(roots_b.keys()):
            shared_roots.append({
                'root': root,
                'idf': idf_scores.get(root, 0.0),
                'verses_a': roots_a[root],
                'verses_b': roots_b[root]
            })

        # Sort by IDF (rarest first)
        shared_roots.sort(key=lambda x: x['idf'], reverse=True)

        return shared_roots

    def find_shared_phrases(self, psalm_a: int, psalm_b: int) -> List[Dict[str, Any]]:
        """
        Find shared contiguous phrases between two psalms.

        Args:
            psalm_a: First psalm number
            psalm_b: Second psalm number

        Returns:
            List of shared phrase dicts with phrase, length, verses_a, verses_b
        """
        phrases_a = self.psalm_phrases.get(psalm_a, {})
        phrases_b = self.psalm_phrases.get(psalm_b, {})

        shared_phrases = []
        for phrase in set(phrases_a.keys()) & set(phrases_b.keys()):
            shared_phrases.append({
                'phrase': phrase,
                'length': len(phrase.split()),
                'verses_a': phrases_a[phrase],
                'verses_b': phrases_b[phrase]
            })

        # Sort by length (longest first), then alphabetically
        shared_phrases.sort(key=lambda x: (-x['length'], x['phrase']))

        return shared_phrases

    def extract_all_patterns(self) -> Dict[str, Any]:
        """
        Extract patterns for all 150 psalms and all psalm pairs.

        Returns:
            Dict with all pattern data for V6
        """
        logger.info("Starting V6 pattern extraction...")
        logger.info("Using Session 115 morphology fixes (hybrid stripping, plural protection, final letters)")

        # Step 1: Extract roots and phrases from all 150 psalms
        logger.info("\nStep 1: Extracting roots and phrases from all 150 Psalms...")
        for psalm_num in range(1, 151):
            if psalm_num % 10 == 0:
                logger.info(f"  Processing Psalm {psalm_num}/150...")
            self.extract_psalm_data(psalm_num)

        logger.info(f"✓ Extracted data from 150 Psalms")

        # Step 2: Calculate IDF scores
        logger.info("\nStep 2: Calculating IDF scores for all roots...")
        idf_scores = self.calculate_idf_scores()
        logger.info(f"✓ Calculated IDF for {len(idf_scores)} unique roots")

        # Step 3: Find shared patterns for all psalm pairs
        logger.info("\nStep 3: Finding shared patterns for all psalm pairs...")
        all_pairs = []
        pair_count = 0
        total_pairs = 150 * 149 // 2  # 11,175 pairs

        for psalm_a in range(1, 151):
            for psalm_b in range(psalm_a + 1, 151):
                pair_count += 1
                if pair_count % 1000 == 0:
                    logger.info(f"  Processing pair {pair_count}/{total_pairs}...")

                shared_roots = self.find_shared_roots(psalm_a, psalm_b, idf_scores)
                shared_phrases = self.find_shared_phrases(psalm_a, psalm_b)

                # Only include pairs with some shared content
                if shared_roots or shared_phrases:
                    all_pairs.append({
                        'psalm_a': psalm_a,
                        'psalm_b': psalm_b,
                        'shared_roots': shared_roots,
                        'shared_phrases': shared_phrases
                    })

        logger.info(f"✓ Found patterns for {len(all_pairs)} psalm pairs")

        # Prepare output
        output = {
            'version': 'V6',
            'description': 'Fresh pattern extraction using Session 115 morphology fixes',
            'total_pairs': len(all_pairs),
            'total_roots': len(idf_scores),
            'psalm_pairs': all_pairs,
            'root_idf_scores': idf_scores,
            'root_psalm_counts': self.root_psalm_counts
        }

        return output


def main():
    """Extract V6 patterns and save to JSON."""
    base_dir = Path(__file__).parent.parent.parent

    # Paths
    tanakh_db = base_dir / "database" / "tanakh.db"
    output_file = base_dir / "data" / "analysis_results" / "psalm_patterns_v6.json"

    if not tanakh_db.exists():
        logger.error(f"Database not found: {tanakh_db}")
        return 1

    # Extract patterns
    extractor = V6PatternExtractor(tanakh_db)
    try:
        patterns = extractor.extract_all_patterns()
    finally:
        extractor.conn.close()

    # Save to JSON
    logger.info(f"\nSaving patterns to {output_file}...")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(patterns, f, ensure_ascii=False, indent=2)

    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    logger.info(f"✓ Saved {output_file.name} ({file_size_mb:.2f} MB)")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("V6 PATTERN EXTRACTION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total psalm pairs with patterns: {patterns['total_pairs']}")
    logger.info(f"Total unique roots: {patterns['total_roots']}")
    logger.info(f"Output file: {output_file}")
    logger.info("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
