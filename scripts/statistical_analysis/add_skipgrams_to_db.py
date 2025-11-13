"""
Extract Skip-grams for All 150 Psalms and Store in Database

Processes all psalms and stores skip-gram patterns in psalm_relationships.db
for use in enhanced scoring.
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, Set, Tuple
import logging
from skipgram_extractor import SkipgramExtractor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
RELATIONSHIPS_DB_PATH = Path(__file__).parent.parent.parent / "data" / "psalm_relationships.db"


class SkipgramDatabase:
    """Manages skip-gram storage in database."""

    def __init__(self):
        """Initialize database connection."""
        self.conn = sqlite3.connect(str(RELATIONSHIPS_DB_PATH))
        self.conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self):
        """Create psalm_skipgrams table if it doesn't exist."""
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS psalm_skipgrams (
                skipgram_id INTEGER PRIMARY KEY AUTOINCREMENT,
                psalm_number INTEGER NOT NULL,
                pattern_consonantal TEXT NOT NULL,
                pattern_length INTEGER NOT NULL,
                occurrence_count INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(psalm_number, pattern_consonantal, pattern_length)
            )
        """)

        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_skipgram_lookup
            ON psalm_skipgrams(pattern_consonantal, pattern_length)
        """)

        self.conn.commit()
        logger.info("Skip-gram table created/verified")

    def store_psalm_skipgrams(
        self,
        psalm_number: int,
        skipgrams: Dict[int, Set[Tuple[str, ...]]]
    ):
        """
        Store skip-grams for a psalm.

        Args:
            psalm_number: Psalm number
            skipgrams: Dictionary mapping length to set of patterns
        """
        cursor = self.conn.cursor()

        for length, patterns in skipgrams.items():
            for pattern in patterns:
                # Convert tuple to space-separated string
                pattern_str = ' '.join(pattern)

                # Note: occurrence_count set to 1 for now
                # Could be calculated more accurately if needed
                cursor.execute("""
                    INSERT OR REPLACE INTO psalm_skipgrams
                    (psalm_number, pattern_consonantal, pattern_length, occurrence_count)
                    VALUES (?, ?, ?, 1)
                """, (psalm_number, pattern_str, length))

        self.conn.commit()

    def get_psalm_skipgrams(
        self,
        psalm_number: int
    ) -> Dict[int, Set[Tuple[str, ...]]]:
        """
        Get skip-grams for a psalm from database.

        Args:
            psalm_number: Psalm number

        Returns:
            Dictionary mapping length to set of patterns
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT pattern_consonantal, pattern_length
            FROM psalm_skipgrams
            WHERE psalm_number = ?
        """, (psalm_number,))

        skipgrams = {2: set(), 3: set(), 4: set()}

        for row in cursor.fetchall():
            pattern_str = row['pattern_consonantal']
            length = row['pattern_length']

            # Convert space-separated string back to tuple
            pattern = tuple(pattern_str.split())
            skipgrams[length].add(pattern)

        return skipgrams

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
            Dictionary mapping length to set of shared patterns
        """
        skipgrams_a = self.get_psalm_skipgrams(psalm_a)
        skipgrams_b = self.get_psalm_skipgrams(psalm_b)

        shared = {}
        for length in [2, 3, 4]:
            shared[length] = skipgrams_a[length] & skipgrams_b[length]

        return shared

    def get_statistics(self) -> Dict[str, int]:
        """Get skip-gram database statistics."""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM psalm_skipgrams")
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT pattern_length, COUNT(*) as count
            FROM psalm_skipgrams
            GROUP BY pattern_length
        """)

        by_length = {row[0]: row[1] for row in cursor.fetchall()}

        return {
            'total': total,
            'by_length': by_length
        }

    def close(self):
        """Close database connection."""
        self.conn.close()


def extract_all_skipgrams():
    """Extract skip-grams for all 150 psalms and store in database."""
    logger.info("=" * 60)
    logger.info("EXTRACTING SKIP-GRAMS FOR ALL 150 PSALMS")
    logger.info("=" * 60)

    # Initialize extractor and database
    extractor = SkipgramExtractor()
    extractor.connect_db()

    db = SkipgramDatabase()

    # Process each psalm
    total_skipgrams = 0
    failed_psalms = []

    for psalm_num in range(1, 151):
        try:
            logger.info(f"Processing Psalm {psalm_num}...")

            # Extract skip-grams
            skipgrams = extractor.extract_all_skipgrams(psalm_num)

            # Store in database
            db.store_psalm_skipgrams(psalm_num, skipgrams)

            # Count
            count = sum(len(patterns) for patterns in skipgrams.values())
            total_skipgrams += count

            if psalm_num % 10 == 0:
                logger.info(f"  Progress: {psalm_num}/150 psalms, {total_skipgrams:,} skip-grams")

        except Exception as e:
            logger.error(f"  ERROR processing Psalm {psalm_num}: {e}")
            failed_psalms.append(psalm_num)

    # Get final statistics
    stats = db.get_statistics()

    logger.info("\n" + "=" * 60)
    logger.info("EXTRACTION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total skip-grams stored: {stats['total']:,}")
    logger.info(f"By length:")
    for length, count in sorted(stats['by_length'].items()):
        logger.info(f"  {length}-word: {count:,}")

    if failed_psalms:
        logger.warning(f"Failed psalms: {failed_psalms}")
    else:
        logger.info("✓ All 150 psalms processed successfully")

    # Test retrieval on Psalms 25 & 34
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION TEST: Psalms 25 & 34")
    logger.info("=" * 60)

    shared = db.find_shared_skipgrams(25, 34)
    logger.info(f"Shared 2-word skip-grams: {len(shared[2])}")
    logger.info(f"Shared 3-word skip-grams: {len(shared[3])}")
    logger.info(f"Shared 4-word skip-grams: {len(shared[4])}")
    logger.info(f"Total shared: {sum(len(s) for s in shared.values())}")

    # Clean up
    extractor.close_db()
    db.close()

    logger.info("\n✓ Skip-gram extraction complete!")


if __name__ == "__main__":
    extract_all_skipgrams()
