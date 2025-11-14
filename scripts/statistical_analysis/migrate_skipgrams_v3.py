"""
Migration Script: Skipgrams V2 → V3

V3 Changes:
1. Switch from consonantal forms to ROOT-based extraction
2. Add full_span_hebrew column to capture complete text spans
3. Remove paragraph markers from all data

This migration:
- Drops existing psalm_skipgrams table
- Creates new schema with additional columns
- Re-extracts all skipgrams using root-based methodology
- Verifies data integrity
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


class SkipgramMigration:
    """Manages skipgram migration from V2 to V3."""

    def __init__(self):
        """Initialize migration."""
        self.conn = sqlite3.connect(str(RELATIONSHIPS_DB_PATH))
        self.conn.row_factory = sqlite3.Row

    def backup_old_data(self):
        """Backup existing skipgrams to a temporary table."""
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
                CREATE TABLE IF NOT EXISTS psalm_skipgrams_v2_backup AS
                SELECT * FROM psalm_skipgrams
            """)
            
            # Get count
            cursor.execute("SELECT COUNT(*) FROM psalm_skipgrams_v2_backup")
            count = cursor.fetchone()[0]
            
            logger.info(f"  Backed up {count:,} skipgram records to psalm_skipgrams_v2_backup")
            self.conn.commit()
        else:
            logger.info("No existing psalm_skipgrams table found (fresh install)")

    def drop_old_table(self):
        """Drop the old psalm_skipgrams table."""
        cursor = self.conn.cursor()
        
        logger.info("Dropping old psalm_skipgrams table...")
        cursor.execute("DROP TABLE IF EXISTS psalm_skipgrams")
        
        # Also drop old indexes
        cursor.execute("DROP INDEX IF EXISTS idx_skipgram_lookup")
        
        self.conn.commit()
        logger.info("  Old table and indexes dropped")

    def create_new_schema(self):
        """Create new V3 schema with full_span_hebrew column."""
        cursor = self.conn.cursor()
        
        logger.info("Creating new V3 schema...")
        
        cursor.execute("""
            CREATE TABLE psalm_skipgrams (
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
            CREATE INDEX idx_skipgram_lookup
            ON psalm_skipgrams(pattern_roots, pattern_length)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_psalm_lookup
            ON psalm_skipgrams(psalm_number)
        """)

        self.conn.commit()
        logger.info("  New schema created with indexes")

    def store_psalm_skipgrams(
        self,
        psalm_number: int,
        skipgrams: Dict[int, Set[Tuple[str, str, str]]]
    ):
        """
        Store skip-grams for a psalm in V3 format.

        Args:
            psalm_number: Psalm number
            skipgrams: Dictionary mapping length to set of (roots, matched_hebrew, full_span) tuples
        """
        cursor = self.conn.cursor()

        for length, patterns in skipgrams.items():
            for pattern in patterns:
                roots, matched_hebrew, full_span = pattern
                
                # Store with new schema
                cursor.execute("""
                    INSERT OR REPLACE INTO psalm_skipgrams
                    (psalm_number, pattern_roots, pattern_hebrew, 
                     full_span_hebrew, pattern_length, occurrence_count)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (psalm_number, roots, matched_hebrew, full_span, length))

        self.conn.commit()

    def migrate_all_psalms(self):
        """Extract and store skipgrams for all 150 psalms using V3 methodology."""
        logger.info("Extracting skipgrams for all 150 psalms (V3 root-based)...")
        logger.info("This will take several minutes...")
        
        # Initialize extractor
        extractor = SkipgramExtractor()
        extractor.connect_db()

        # Process each psalm
        total_skipgrams = 0
        failed_psalms = []

        for psalm_num in range(1, 151):
            try:
                if psalm_num % 10 == 0:
                    logger.info(f"Processing Psalm {psalm_num}/150...")

                # Extract skip-grams using V3 methodology
                skipgrams = extractor.extract_all_skipgrams(psalm_num)

                # Store in database
                self.store_psalm_skipgrams(psalm_num, skipgrams)

                # Count
                count = sum(len(patterns) for patterns in skipgrams.values())
                total_skipgrams += count

            except Exception as e:
                logger.error(f"  ERROR processing Psalm {psalm_num}: {e}")
                failed_psalms.append(psalm_num)

        # Clean up
        extractor.close_db()

        logger.info(f"\nExtraction complete!")
        logger.info(f"  Total skipgrams: {total_skipgrams:,}")
        
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
        
        logger.info("  Skipgrams by length:")
        for row in cursor.fetchall():
            logger.info(f"    {row[0]}-word: {row[1]:,}")
        
        # Check for paragraph markers (should be ZERO!)
        cursor.execute("""
            SELECT COUNT(*) FROM psalm_skipgrams
            WHERE pattern_roots LIKE '%{%' 
               OR pattern_hebrew LIKE '%{%'
               OR full_span_hebrew LIKE '%{%'
        """)
        marker_count = cursor.fetchone()[0]
        
        if marker_count > 0:
            logger.error(f"  ✗ ERROR: Found {marker_count} skipgrams with paragraph markers!")
            return False
        else:
            logger.info("  ✓ No paragraph markers found in data")
        
        # Check that all psalms are represented
        cursor.execute("""
            SELECT COUNT(DISTINCT psalm_number) FROM psalm_skipgrams
        """)
        psalm_count = cursor.fetchone()[0]
        
        if psalm_count == 150:
            logger.info(f"  ✓ All 150 psalms represented")
        else:
            logger.warning(f"  ⚠ Only {psalm_count} psalms represented (expected 150)")
        
        # Sample some data
        logger.info("\n  Sample V3 skipgrams:")
        cursor.execute("""
            SELECT psalm_number, pattern_roots, pattern_hebrew, full_span_hebrew
            FROM psalm_skipgrams
            WHERE pattern_length = 3
            LIMIT 3
        """)
        
        for row in cursor.fetchall():
            logger.info(f"    Psalm {row[0]}:")
            logger.info(f"      Roots: {row[1]}")
            logger.info(f"      Matched: {row[2]}")
            logger.info(f"      Full span: {row[3]}")
        
        return True

    def close(self):
        """Close database connection."""
        self.conn.close()


def run_migration():
    """Run the full migration process."""
    logger.info("=" * 60)
    logger.info("SKIPGRAMS V2 → V3 MIGRATION")
    logger.info("=" * 60)
    logger.info("")
    logger.info("This migration will:")
    logger.info("  1. Backup existing data")
    logger.info("  2. Drop old table and create new V3 schema")
    logger.info("  3. Re-extract all skipgrams using root-based methodology")
    logger.info("  4. Verify data integrity")
    logger.info("")
    
    # Confirm
    response = input("Continue with migration? [y/N]: ")
    if response.lower() not in ['y', 'yes']:
        logger.info("Migration cancelled")
        return
    
    logger.info("\nStarting migration...")
    
    migration = SkipgramMigration()
    
    try:
        # Step 1: Backup
        migration.backup_old_data()
        
        # Step 2: Drop and recreate
        migration.drop_old_table()
        migration.create_new_schema()
        
        # Step 3: Migrate data
        total, failed = migration.migrate_all_psalms()
        
        # Step 4: Verify
        success = migration.verify_migration()
        
        logger.info("\n" + "=" * 60)
        if success and not failed:
            logger.info("✓ MIGRATION COMPLETE - SUCCESS!")
        else:
            logger.warning("⚠ MIGRATION COMPLETE - WITH WARNINGS")
        logger.info("=" * 60)
        
        logger.info(f"\nDatabase: {RELATIONSHIPS_DB_PATH}")
        logger.info(f"Backup table: psalm_skipgrams_v2_backup (can be dropped later)")
        
    except Exception as e:
        logger.error(f"\n✗ MIGRATION FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        migration.close()


if __name__ == "__main__":
    run_migration()
