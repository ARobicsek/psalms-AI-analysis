"""
Enhanced Scoring Calculator

Calculates enhanced similarity scores for psalm pairs using:
1. Contiguous phrases (from database)
2. Skip-gram patterns (from database)
3. Root IDF overlap (from database)
4. Length normalization (geometric mean)

Formula:
  pattern_points = sum of points (1 for 2-word, 2 for 3-word, 3 for 4+ word)
  root_idf_sum = sum of IDF scores for shared roots
  geom_mean_length = sqrt(word_count_A × word_count_B)

  phrase_score = (pattern_points / geom_mean_length) × 1000
  root_score = (root_idf_sum / geom_mean_length) × 1000

  FINAL_SCORE = phrase_score + root_score
"""

import sqlite3
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
RELATIONSHIPS_DB_PATH = Path(__file__).parent.parent.parent / "data" / "psalm_relationships.db"
WORD_COUNTS_PATH = Path(__file__).parent.parent.parent / "data" / "analysis_results" / "psalm_word_counts.json"


@dataclass
class EnhancedScore:
    """Enhanced similarity score for a psalm pair."""
    psalm_a: int
    psalm_b: int

    # Pattern components
    contiguous_2word: int
    contiguous_3word: int
    contiguous_4plus: int
    skipgram_2word: int
    skipgram_3word: int
    skipgram_4plus: int
    total_pattern_points: float

    # Root component
    shared_roots: int
    root_idf_sum: float

    # Normalization
    word_count_a: int
    word_count_b: int
    geometric_mean_length: float

    # Final scores
    phrase_score: float
    root_score: float
    final_score: float

    # Original metrics (for comparison)
    original_pvalue: float
    original_rank: Optional[int] = None


class EnhancedScorer:
    """Calculate enhanced scores for psalm relationships."""

    def __init__(self):
        """Initialize scorer."""
        self.conn = None
        self.word_counts = None

    def connect_db(self):
        """Connect to relationships database."""
        if not RELATIONSHIPS_DB_PATH.exists():
            raise FileNotFoundError(f"Database not found: {RELATIONSHIPS_DB_PATH}")

        self.conn = sqlite3.connect(str(RELATIONSHIPS_DB_PATH))
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Connected to {RELATIONSHIPS_DB_PATH}")

    def load_word_counts(self):
        """Load psalm word counts from JSON."""
        if not WORD_COUNTS_PATH.exists():
            raise FileNotFoundError(f"Word counts not found: {WORD_COUNTS_PATH}")

        with open(WORD_COUNTS_PATH, 'r') as f:
            data = json.load(f)
            # Convert string keys to integers
            self.word_counts = {int(k): v for k, v in data['word_counts'].items()}

        logger.info(f"Loaded word counts for {len(self.word_counts)} psalms")

    def count_contiguous_phrases(
        self,
        shared_phrases: List[Dict]
    ) -> Tuple[int, int, int]:
        """
        Count contiguous phrases by length.

        Args:
            shared_phrases: List of shared phrase dictionaries

        Returns:
            Tuple of (2-word count, 3-word count, 4+ word count)
        """
        count_2 = 0
        count_3 = 0
        count_4plus = 0

        for phrase in shared_phrases:
            length = phrase.get('length', 0)
            if length == 2:
                count_2 += 1
            elif length == 3:
                count_3 += 1
            elif length >= 4:
                count_4plus += 1

        return count_2, count_3, count_4plus

    def count_skipgrams(
        self,
        psalm_a: int,
        psalm_b: int
    ) -> Tuple[int, int, int]:
        """
        Count shared skip-grams between two psalms.

        Args:
            psalm_a: First psalm number
            psalm_b: Second psalm number

        Returns:
            Tuple of (2-word count, 3-word count, 4-word count)
        """
        cursor = self.conn.cursor()

        # Get skip-grams for both psalms
        cursor.execute("""
            SELECT pattern_consonantal, pattern_length
            FROM psalm_skipgrams
            WHERE psalm_number = ?
        """, (psalm_a,))
        skipgrams_a = {(row['pattern_consonantal'], row['pattern_length']) for row in cursor.fetchall()}

        cursor.execute("""
            SELECT pattern_consonantal, pattern_length
            FROM psalm_skipgrams
            WHERE psalm_number = ?
        """, (psalm_b,))
        skipgrams_b = {(row['pattern_consonantal'], row['pattern_length']) for row in cursor.fetchall()}

        # Find shared patterns
        shared = skipgrams_a & skipgrams_b

        # Count by length
        count_2 = sum(1 for (_, length) in shared if length == 2)
        count_3 = sum(1 for (_, length) in shared if length == 3)
        count_4 = sum(1 for (_, length) in shared if length == 4)

        return count_2, count_3, count_4

    def calculate_enhanced_score(
        self,
        psalm_a: int,
        psalm_b: int,
        shared_roots_json: str,
        shared_phrases_json: str,
        original_pvalue: float
    ) -> EnhancedScore:
        """
        Calculate enhanced score for a psalm pair.

        Args:
            psalm_a: First psalm number
            psalm_b: Second psalm number
            shared_roots_json: JSON string of shared roots
            shared_phrases_json: JSON string of shared phrases
            original_pvalue: Original p-value from hypergeometric test

        Returns:
            EnhancedScore object with all components
        """
        # Parse shared data
        shared_roots = json.loads(shared_roots_json) if shared_roots_json else []
        shared_phrases = json.loads(shared_phrases_json) if shared_phrases_json else []

        # Count contiguous phrases
        cont_2, cont_3, cont_4plus = self.count_contiguous_phrases(shared_phrases)

        # Count skip-grams
        skip_2, skip_3, skip_4 = self.count_skipgrams(psalm_a, psalm_b)

        # Calculate pattern points
        # 2-word: 1 point, 3-word: 2 points, 4+ word: 3 points
        pattern_points = (
            (cont_2 + skip_2) * 1 +
            (cont_3 + skip_3) * 2 +
            (cont_4plus + skip_4) * 3
        )

        # Calculate root IDF sum with bonus weight for rare roots (IDF >= 4)
        root_idf_sum = 0
        for root in shared_roots:
            idf = root.get('idf', 0)
            if idf >= 4.0:
                # Double weight for rare roots
                root_idf_sum += idf * 2
            else:
                # Normal weight for common roots
                root_idf_sum += idf

        # Get word counts
        word_count_a = self.word_counts.get(psalm_a, 0)
        word_count_b = self.word_counts.get(psalm_b, 0)

        if word_count_a == 0 or word_count_b == 0:
            logger.warning(f"Missing word count for Psalm {psalm_a} or {psalm_b}")
            geometric_mean = 1  # Avoid division by zero
        else:
            geometric_mean = math.sqrt(word_count_a * word_count_b)

        # Calculate normalized scores
        # NOTE: Rare roots (IDF >= 4) are already doubled in root_idf_sum calculation
        phrase_score = (pattern_points / geometric_mean) * 1000 if geometric_mean > 0 else 0
        root_score = (root_idf_sum / geometric_mean) * 1000 if geometric_mean > 0 else 0

        # Final score
        final_score = phrase_score + root_score

        return EnhancedScore(
            psalm_a=psalm_a,
            psalm_b=psalm_b,
            contiguous_2word=cont_2,
            contiguous_3word=cont_3,
            contiguous_4plus=cont_4plus,
            skipgram_2word=skip_2,
            skipgram_3word=skip_3,
            skipgram_4plus=skip_4,
            total_pattern_points=pattern_points,
            shared_roots=len(shared_roots),
            root_idf_sum=root_idf_sum,
            word_count_a=word_count_a,
            word_count_b=word_count_b,
            geometric_mean_length=geometric_mean,
            phrase_score=phrase_score,
            root_score=root_score,
            final_score=final_score,
            original_pvalue=original_pvalue
        )

    def score_all_relationships(self) -> List[EnhancedScore]:
        """
        Calculate enhanced scores for all relationships in database.

        Returns:
            List of EnhancedScore objects
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                psalm_a,
                psalm_b,
                shared_roots_json,
                shared_phrases_json,
                hypergeometric_pvalue
            FROM psalm_relationships
            ORDER BY psalm_a, psalm_b
        """)

        scores = []
        total = 11001  # Known from previous analysis

        for i, row in enumerate(cursor.fetchall(), 1):
            if i % 1000 == 0:
                logger.info(f"  Progress: {i}/{total} pairs scored")

            score = self.calculate_enhanced_score(
                psalm_a=row['psalm_a'],
                psalm_b=row['psalm_b'],
                shared_roots_json=row['shared_roots_json'],
                shared_phrases_json=row['shared_phrases_json'],
                original_pvalue=row['hypergeometric_pvalue']
            )
            scores.append(score)

        return scores

    def close_db(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


def test_enhanced_scoring():
    """Test enhanced scoring on sample pairs."""
    logger.info("=" * 60)
    logger.info("ENHANCED SCORING TEST")
    logger.info("=" * 60)

    scorer = EnhancedScorer()
    scorer.connect_db()
    scorer.load_word_counts()

    # Test pairs
    test_pairs = [
        (14, 53, "Nearly identical"),
        (25, 34, "Thematic connection"),
        (1, 2, "Random pair")
    ]

    for psalm_a, psalm_b, description in test_pairs:
        cursor = scorer.conn.cursor()
        cursor.execute("""
            SELECT shared_roots_json, shared_phrases_json, hypergeometric_pvalue
            FROM psalm_relationships
            WHERE psalm_a = ? AND psalm_b = ?
        """, (psalm_a, psalm_b))

        row = cursor.fetchone()
        if not row:
            logger.warning(f"Pair {psalm_a}-{psalm_b} not found")
            continue

        score = scorer.calculate_enhanced_score(
            psalm_a, psalm_b,
            row['shared_roots_json'],
            row['shared_phrases_json'],
            row['hypergeometric_pvalue']
        )

        logger.info(f"\nPsalms {psalm_a} & {psalm_b} ({description}):")
        logger.info(f"  Contiguous: 2w={score.contiguous_2word}, 3w={score.contiguous_3word}, 4+w={score.contiguous_4plus}")
        logger.info(f"  Skip-grams: 2w={score.skipgram_2word}, 3w={score.skipgram_3word}, 4w={score.skipgram_4plus}")
        logger.info(f"  Pattern points: {score.total_pattern_points}")
        logger.info(f"  Root IDF sum: {score.root_idf_sum:.2f}")
        logger.info(f"  Geometric mean length: {score.geometric_mean_length:.1f}")
        logger.info(f"  Phrase score: {score.phrase_score:.2f}")
        logger.info(f"  Root score: {score.root_score:.2f}")
        logger.info(f"  FINAL SCORE: {score.final_score:.2f}")

    scorer.close_db()


if __name__ == "__main__":
    test_enhanced_scoring()
