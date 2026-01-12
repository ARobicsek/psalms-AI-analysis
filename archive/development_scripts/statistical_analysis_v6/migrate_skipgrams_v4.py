"""
Migration Script: Skipgrams V3 → V4 → V5

V4 Enhancements:
1. Add verse tracking for each skipgram instance
2. Enable proper deduplication by (full_span, verse) pairs
3. Support matches_from_a/b array population in scoring
4. Fix overlapping pattern issue where multiple patterns from same phrase counted separately

V5 Enhancements (Quality Filtering):
1. Add content word analysis metadata
2. Apply content word filtering (Priority 1)
3. Apply pattern stoplist filtering (Priority 2)
4. Support content word bonus in scoring (Priority 4)

Database Schema Changes (V4):
- Add 'verse' column to track verse number
- Add 'first_position' column to track word position
- Update indexes for efficient verse-based queries

Database Schema Changes (V5):
- Add 'content_word_count' column
- Add 'content_word_ratio' column
- Add 'pattern_category' column (formulaic vs interesting)
"""

import sqlite3
import json
import time
from pathlib import Path
from typing import Dict, List
import logging
from skipgram_extractor_v4 import SkipgramExtractorV4

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
RELATIONSHIPS_DB_PATH = Path(__file__).parent.parent.parent / "data" / "psalm_relationships.db"


class SkipgramMigrationV4:
    """Manages skipgram migration from V3 to V4."""

    def __init__(self):
        """Initialize migration."""
        self.conn = sqlite3.connect(str(RELATIONSHIPS_DB_PATH))
        self.conn.row_factory = sqlite3.Row

    def backup_old_data(self):
        """Backup existing skipgrams to a versioned table."""
        cursor = self.conn.cursor()

        # Check if old table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='psalm_skipgrams'
        """)

        if cursor.fetchone():
            logger.info("Backing up existing psalm_skipgrams table...")

            # Create backup table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS psalm_skipgrams_v3_backup AS
                SELECT * FROM psalm_skipgrams
            """)

            # Get count
            cursor.execute("SELECT COUNT(*) FROM psalm_skipgrams_v3_backup")
            count = cursor.fetchone()[0]

            logger.info(f"  Backed up {count:,} skipgram records to psalm_skipgrams_v3_backup")
            self.conn.commit()
        else:
            logger.info("No existing psalm_skipgrams table found (fresh install)")

    def drop_old_table(self):
        """Drop the old psalm_skipgrams table and indexes."""
        cursor = self.conn.cursor()

        logger.info("Dropping old psalm_skipgrams table...")
        cursor.execute("DROP TABLE IF EXISTS psalm_skipgrams")

        # Drop old indexes
        cursor.execute("DROP INDEX IF EXISTS idx_skipgram_lookup")
        cursor.execute("DROP INDEX IF EXISTS idx_psalm_lookup")

        self.conn.commit()
        logger.info("  Old table and indexes dropped")

    def create_new_schema(self):
        """Create new V5 schema with verse tracking, position, and content word metadata."""
        cursor = self.conn.cursor()

        logger.info("Creating new V5 schema...")

        cursor.execute("""
            CREATE TABLE psalm_skipgrams (
                skipgram_id INTEGER PRIMARY KEY AUTOINCREMENT,
                psalm_number INTEGER NOT NULL,
                pattern_roots TEXT NOT NULL,
                pattern_hebrew TEXT NOT NULL,
                full_span_hebrew TEXT NOT NULL,
                pattern_length INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                first_position INTEGER NOT NULL,
                gap_word_count INTEGER NOT NULL DEFAULT 0,
                content_word_count INTEGER DEFAULT 0,
                content_word_ratio REAL DEFAULT 0.0,
                pattern_category TEXT DEFAULT 'unknown',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(psalm_number, pattern_roots, pattern_length, verse, first_position)
            )
        """)

        # Create indexes for faster lookups
        cursor.execute("""
            CREATE INDEX idx_skipgram_lookup
            ON psalm_skipgrams(pattern_roots, pattern_length)
        """)

        cursor.execute("""
            CREATE INDEX idx_psalm_lookup
            ON psalm_skipgrams(psalm_number)
        """)

        cursor.execute("""
            CREATE INDEX idx_verse_lookup
            ON psalm_skipgrams(psalm_number, verse)
        """)

        self.conn.commit()
        logger.info("  New schema created with verse tracking and indexes")

    def store_psalm_skipgrams(
        self,
        psalm_number: int,
        skipgrams: Dict[int, List[Dict[str, any]]]
    ):
        """
        Store skip-grams for a psalm in V5 format with verse tracking and content word metadata.

        Args:
            psalm_number: Psalm number
            skipgrams: Dictionary mapping length to list of skipgram instances
        """
        cursor = self.conn.cursor()
        insert_count = 0

        for length, instances in skipgrams.items():
            for sg in instances:
                # Insert with V5 schema (includes verse, position, gap_word_count, and content word metadata)
                cursor.execute("""
                    INSERT OR REPLACE INTO psalm_skipgrams
                    (psalm_number, pattern_roots, pattern_hebrew,
                     full_span_hebrew, pattern_length, verse, first_position, gap_word_count,
                     content_word_count, content_word_ratio, pattern_category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    psalm_number,
                    sg['pattern_roots'],
                    sg['pattern_hebrew'],
                    sg['full_span_hebrew'],
                    sg['length'],
                    sg['verse'],
                    sg['first_position'],
                    sg.get('gap_word_count', 0),
                    sg.get('content_word_count', 0),
                    sg.get('content_word_ratio', 0.0),
                    sg.get('pattern_category', 'unknown')
                ))
                insert_count += 1

        self.conn.commit()
        return insert_count

    def migrate_all_psalms(self):
        """Extract and store skipgrams for all 150 psalms using V5 methodology."""
        logger.info("Extracting skipgrams for all 150 psalms (V5 with quality filtering)...")
        logger.info("  V5 Features: Content word filtering + pattern stoplist")
        logger.info("This will take several minutes...")

        # Initialize extractor with quality filtering enabled
        extractor = SkipgramExtractorV4(enable_quality_filtering=True)
        extractor.connect_db()

        # Process each psalm
        total_skipgrams = 0
        failed_psalms = []
        start_time = time.time()

        for psalm_num in range(1, 151):
            try:
                if psalm_num % 10 == 0:
                    elapsed = time.time() - start_time
                    logger.info(f"Processing Psalm {psalm_num}/150 ({elapsed:.1f}s elapsed)...")

                # Extract skip-grams using V4 methodology (with deduplication)
                skipgrams = extractor.extract_all_skipgrams(psalm_num, deduplicate=True)

                # Store in database
                count = self.store_psalm_skipgrams(psalm_num, skipgrams)
                total_skipgrams += count

            except Exception as e:
                logger.error(f"  ERROR processing Psalm {psalm_num}: {e}")
                failed_psalms.append(psalm_num)

        # Log filtering statistics
        logger.info(f"\nV5 Filtering Statistics:")
        logger.info(f"  Total patterns extracted: {extractor.stats['total_extracted']:,}")
        logger.info(f"  Filtered by content words: {extractor.stats['filtered_by_content']:,} ({100.0 * extractor.stats['filtered_by_content'] / max(extractor.stats['total_extracted'], 1):.1f}%)")
        logger.info(f"  Filtered by stoplist: {extractor.stats['filtered_by_stoplist']:,} ({100.0 * extractor.stats['filtered_by_stoplist'] / max(extractor.stats['total_extracted'], 1):.1f}%)")
        logger.info(f"  Patterns kept: {extractor.stats['kept']:,} ({100.0 * extractor.stats['kept'] / max(extractor.stats['total_extracted'], 1):.1f}%)")

        # Clean up
        extractor.close_db()

        elapsed = time.time() - start_time
        logger.info(f"\nExtraction complete in {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        logger.info(f"  Total skipgrams stored: {total_skipgrams:,}")

        if failed_psalms:
            logger.warning(f"  Failed psalms: {failed_psalms}")
        else:
            logger.info("  ✓ All 150 psalms processed successfully")

        return total_skipgrams, failed_psalms

    def verify_migration(self):
        """Verify the migration was successful."""
        cursor = self.conn.cursor()

        logger.info("\nVerifying migration...")

        # Check total count
        cursor.execute("SELECT COUNT(*) FROM psalm_skipgrams")
        total = cursor.fetchone()[0]
        logger.info(f"  Total skipgrams in database: {total:,}")

        # Check by length
        cursor.execute("""
            SELECT pattern_length, COUNT(*) as count
            FROM psalm_skipgrams
            GROUP BY pattern_length
            ORDER BY pattern_length
        """)

        logger.info(f"\n  Skipgrams by length:")
        for row in cursor.fetchall():
            length = row[0]
            count = row[1]
            logger.info(f"    {length}-word: {count:,}")

        # Check psalm coverage
        cursor.execute("""
            SELECT COUNT(DISTINCT psalm_number) as psalm_count
            FROM psalm_skipgrams
        """)
        psalm_count = cursor.fetchone()[0]
        logger.info(f"\n  Psalms with skipgrams: {psalm_count}/150")

        # Verify verse tracking
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM psalm_skipgrams
            WHERE verse IS NULL OR verse = 0
        """)
        null_verses = cursor.fetchone()[0]
        if null_verses == 0:
            logger.info(f"  ✓ All skipgrams have verse tracking")
        else:
            logger.warning(f"  ⚠ {null_verses:,} skipgrams missing verse numbers")

        # Check for overlapping patterns (should be reduced from V3)
        cursor.execute("""
            SELECT COUNT(*) as overlaps
            FROM (
                SELECT psalm_number, verse, full_span_hebrew, COUNT(*) as pattern_count
                FROM psalm_skipgrams
                GROUP BY psalm_number, verse, full_span_hebrew
                HAVING COUNT(*) > 1
            )
        """)
        overlaps = cursor.fetchone()[0]
        logger.info(f"\n  Locations with multiple patterns: {overlaps:,}")
        logger.info(f"    (This is expected for different-length patterns from same span)")

        logger.info(f"\n✓ Migration verification complete")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


def main():
    """Run V4 migration."""
    logger.info("=" * 60)
    logger.info("SKIPGRAM MIGRATION: V3 → V4")
    logger.info("=" * 60)

    migration = SkipgramMigrationV4()

    try:
        # Backup existing data
        migration.backup_old_data()

        # Drop old schema
        migration.drop_old_table()

        # Create new schema
        migration.create_new_schema()

        # Migrate all psalms
        total, failed = migration.migrate_all_psalms()

        # Verify
        migration.verify_migration()

        logger.info("\n" + "=" * 60)
        logger.info("✓ V4 MIGRATION COMPLETE")
        logger.info("=" * 60)

        if failed:
            logger.warning(f"\nNote: {len(failed)} psalms failed: {failed}")
            logger.warning("You may want to re-run migration for these psalms.")

    finally:
        migration.close()


if __name__ == "__main__":
    main()
