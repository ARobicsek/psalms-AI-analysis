"""
Extract Skip-grams for All 150 Psalms and Store in Database

V3 Update:
- Uses root-based extraction (consistent with contiguous phrases)
- Stores full Hebrew text spans (matched words + gaps)
- Removes paragraph markers before processing

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
    """Manages skip-gram storage in database (V3 schema)."""

    def __init__(self):
        """Initialize database connection."""
        self.conn = sqlite3.connect(str(RELATIONSHIPS_DB_PATH))
        self.conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self):
        """Create psalm_skipgrams table if it doesn't exist (V3 schema)."""
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS psalm_skipgrams (
                skipgram_id INTEGER PRIMARY KEY AUTOINCREMENT,
                psalm_number INTEGER NOT NULL,
                pattern_roots TEXT NOT NULL,
                pattern_hebrew TEXT NOT NULL,
                full_span_hebrew TEXT NOT NULL,
                pattern_length INTEGER NOT NULL,
                occurrence_count INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(psalm_number, pattern_roots, pattern_length)
            )
        """)

        # Create indexes for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_skipgram_lookup
            ON psalm_skipgrams(pattern_roots, pattern_length)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_psalm_lookup
            ON psalm_skipgrams(psalm_number)
        """)

        self.conn.commit()
        logger.info("Skip-gram table created/verified (V3 schema)")

    def store_psalm_skipgrams(
        self,
        psalm_number: int,
        skipgrams: Dict[int, Set[Tuple[str, str, str]]]
    ):
        """
        Store skip-grams for a psalm.

        Args:
            psalm_number: Psalm number
            skipgrams: Dictionary mapping length to set of (roots, matched_hebrew, full_span) tuples
        """
        cursor = self.conn.cursor()

        for length, patterns in skipgrams.items():
            for pattern in patterns:
                roots, matched_hebrew, full_span = pattern
                
                # Note: occurrence_count set to 1 for now
                # Could be calculated more accurately if needed
                cursor.execute("""
                    INSERT OR REPLACE INTO psalm_skipgrams
                    (psalm_number, pattern_roots, pattern_hebrew, 
                     full_span_hebrew, pattern_length, occurrence_count)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (psalm_number, roots, matched_hebrew, full_span, length))

        self.conn.commit()

    def get_psalm_skipgrams(
        self,
        psalm_number: int
    ) -> Dict[int, Set[Tuple[str, str, str]]]:
        """
        Get skip-grams for a psalm from database.

        Args:
            psalm_number: Psalm number

        Returns:
            Dictionary mapping length to set of patterns
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT pattern_roots, pattern_hebrew, full_span_hebrew, pattern_length
            FROM psalm_skipgrams
            WHERE psalm_number = ?
        """, (psalm_number,))

        skipgrams = {2: set(), 3: set(), 4: set()}

        for row in cursor.fetchall():
            roots = row['pattern_roots']
            matched = row['pattern_hebrew']
            full_span = row['full_span_hebrew']
            length = row['pattern_length']

            skipgrams[length].add((roots, matched, full_span))

        return skipgrams

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
            Dictionary mapping length to set of shared patterns
        """
        skipgrams_a = self.get_psalm_skipgrams(psalm_a)
        skipgrams_b = self.get_psalm_skipgrams(psalm_b)

        shared = {}
        for length in [2, 3, 4]:
            # Find shared based on root patterns (first element of tuple)
            roots_a = {sg[0]: sg for sg in skipgrams_a[length]}
            roots_b = {sg[0]: sg for sg in skipgrams_b[length]}
            
            # Find common root patterns
            common_roots = set(roots_a.keys()) & set(roots_b.keys())
            
            # Include tuples for common patterns
            shared[length] = {roots_a[r] for r in common_roots}

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
    """Extract skip-grams for all 150 psalms and store in database (V3)."""
    logger.info("=" * 60)
    logger.info("EXTRACTING SKIP-GRAMS FOR ALL 150 PSALMS (V3)")
    logger.info("=" * 60)
    logger.info("Using root-based extraction with full text spans")
    logger.info("")

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

            # Extract skip-grams (V3 methodology)
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
    
    # Show sample with full spans
    if shared[2]:
        logger.info("\nSample 2-word shared skipgrams with full spans:")
        for i, pattern in enumerate(list(shared[2])[:3], 1):
            roots, matched, full_span = pattern
            logger.info(f"  {i}. Roots: {roots}")
            logger.info(f"     Matched: {matched}")
            logger.info(f"     Full span: {full_span}")

    # Clean up
    extractor.close_db()
    db.close()

    logger.info("\n✓ Skip-gram extraction complete!")


if __name__ == "__main__":
    extract_all_skipgrams()
