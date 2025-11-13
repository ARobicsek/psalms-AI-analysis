"""
Database Builder for Psalm Relationships

Creates and manages the psalm_relationships.db SQLite database.
Stores root frequencies, psalm-root mappings, phrases, and relationship scores.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Default database location
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "psalm_relationships.db"


class PsalmRelationshipsDB:
    """Manages the psalm relationships database."""

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file (creates if doesn't exist)
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Enable column access by name

        self._create_schema()

    def _create_schema(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Root frequency data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS root_frequencies (
                root_id INTEGER PRIMARY KEY AUTOINCREMENT,
                root_consonantal TEXT UNIQUE NOT NULL,
                total_occurrences INTEGER NOT NULL,
                psalm_count INTEGER NOT NULL,
                idf_score REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Roots in each Psalm
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS psalm_roots (
                psalm_root_id INTEGER PRIMARY KEY AUTOINCREMENT,
                psalm_number INTEGER NOT NULL,
                root_id INTEGER NOT NULL,
                occurrence_count INTEGER NOT NULL,
                example_words TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (root_id) REFERENCES root_frequencies(root_id),
                UNIQUE(psalm_number, root_id)
            )
        """)

        # Phrases in each Psalm
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS psalm_phrases (
                phrase_id INTEGER PRIMARY KEY AUTOINCREMENT,
                psalm_number INTEGER NOT NULL,
                phrase_consonantal TEXT NOT NULL,
                phrase_hebrew TEXT NOT NULL,
                phrase_length INTEGER NOT NULL,
                occurrence_count INTEGER NOT NULL,
                verse_references TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Pairwise Psalm relationships
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS psalm_relationships (
                relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
                psalm_a INTEGER NOT NULL,
                psalm_b INTEGER NOT NULL,
                shared_root_count INTEGER NOT NULL,
                total_roots_a INTEGER NOT NULL,
                total_roots_b INTEGER NOT NULL,
                hypergeometric_pvalue REAL NOT NULL,
                weighted_overlap_score REAL NOT NULL,
                z_score REAL NOT NULL,
                is_significant BOOLEAN NOT NULL,
                shared_roots_json TEXT NOT NULL,
                shared_phrases_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK (psalm_a < psalm_b),
                UNIQUE(psalm_a, psalm_b)
            )
        """)

        # Multi-Psalm clusters
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS psalm_clusters (
                cluster_id INTEGER PRIMARY KEY AUTOINCREMENT,
                psalm_numbers TEXT NOT NULL,
                cluster_size INTEGER NOT NULL,
                core_vocabulary_json TEXT NOT NULL,
                avg_pairwise_pvalue REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for fast queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_relationships_psalm_a
            ON psalm_relationships(psalm_a)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_relationships_psalm_b
            ON psalm_relationships(psalm_b)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_relationships_significance
            ON psalm_relationships(is_significant)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_psalm_roots_psalm
            ON psalm_roots(psalm_number)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_psalm_roots_root
            ON psalm_roots(root_id)
        """)

        self.conn.commit()
        logger.info(f"Database schema created at {self.db_path}")

    def get_or_create_root(self, root_consonantal: str) -> int:
        """
        Get existing root_id or create new root entry.

        Args:
            root_consonantal: Consonantal form of Hebrew root

        Returns:
            root_id for this root
        """
        cursor = self.conn.cursor()

        # Try to find existing
        cursor.execute("""
            SELECT root_id FROM root_frequencies
            WHERE root_consonantal = ?
        """, (root_consonantal,))

        row = cursor.fetchone()
        if row:
            return row['root_id']

        # Create new (placeholder values, will be updated in frequency analysis)
        cursor.execute("""
            INSERT INTO root_frequencies
            (root_consonantal, total_occurrences, psalm_count, idf_score)
            VALUES (?, 0, 0, 0.0)
        """, (root_consonantal,))

        self.conn.commit()
        return cursor.lastrowid

    def store_psalm_roots(self, psalm_number: int, roots: Dict[str, Dict[str, Any]]):
        """
        Store root data for a single Psalm.

        Args:
            psalm_number: Psalm number (1-150)
            roots: Dict mapping root_consonantal to {count, examples}
        """
        cursor = self.conn.cursor()

        for root_consonantal, data in roots.items():
            root_id = self.get_or_create_root(root_consonantal)

            # Store psalm-root relationship
            cursor.execute("""
                INSERT OR REPLACE INTO psalm_roots
                (psalm_number, root_id, occurrence_count, example_words)
                VALUES (?, ?, ?, ?)
            """, (
                psalm_number,
                root_id,
                data['count'],
                json.dumps(data['examples'], ensure_ascii=False)
            ))

        self.conn.commit()
        logger.debug(f"Stored {len(roots)} roots for Psalm {psalm_number}")

    def store_psalm_phrases(self, psalm_number: int, phrases: List[Dict[str, Any]]):
        """
        Store phrase data for a single Psalm.

        Args:
            psalm_number: Psalm number (1-150)
            phrases: List of phrase dicts with consonantal, hebrew, length, count, verses
        """
        cursor = self.conn.cursor()

        for phrase in phrases:
            cursor.execute("""
                INSERT INTO psalm_phrases
                (psalm_number, phrase_consonantal, phrase_hebrew, phrase_length,
                 occurrence_count, verse_references)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                psalm_number,
                phrase['consonantal'],
                phrase['hebrew'],
                phrase['length'],
                phrase['count'],
                json.dumps(phrase['verses'], ensure_ascii=False)
            ))

        self.conn.commit()
        logger.debug(f"Stored {len(phrases)} phrases for Psalm {psalm_number}")

    def update_root_frequencies(self):
        """
        Compute and update IDF scores for all roots.
        Should be called after all psalm roots have been stored.
        """
        cursor = self.conn.cursor()

        # Update total_occurrences and psalm_count
        cursor.execute("""
            UPDATE root_frequencies
            SET total_occurrences = (
                SELECT SUM(occurrence_count)
                FROM psalm_roots
                WHERE psalm_roots.root_id = root_frequencies.root_id
            ),
            psalm_count = (
                SELECT COUNT(DISTINCT psalm_number)
                FROM psalm_roots
                WHERE psalm_roots.root_id = root_frequencies.root_id
            )
        """)

        # Compute IDF scores: log(150 / psalm_count)
        import math
        cursor.execute("SELECT root_id, psalm_count FROM root_frequencies")
        for row in cursor.fetchall():
            if row['psalm_count'] > 0:
                idf = math.log(150.0 / row['psalm_count'])
                cursor.execute("""
                    UPDATE root_frequencies
                    SET idf_score = ?
                    WHERE root_id = ?
                """, (idf, row['root_id']))

        self.conn.commit()
        logger.info("Updated root frequencies and IDF scores")

    def get_psalm_roots(self, psalm_number: int) -> List[Dict[str, Any]]:
        """
        Get all roots for a specific Psalm with their IDF scores.

        Args:
            psalm_number: Psalm number (1-150)

        Returns:
            List of dicts with root_consonantal, occurrence_count, idf_score
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                rf.root_consonantal,
                pr.occurrence_count,
                rf.idf_score,
                pr.example_words
            FROM psalm_roots pr
            JOIN root_frequencies rf ON pr.root_id = rf.root_id
            WHERE pr.psalm_number = ?
            ORDER BY rf.idf_score DESC
        """, (psalm_number,))

        results = []
        for row in cursor.fetchall():
            results.append({
                'root': row['root_consonantal'],
                'count': row['occurrence_count'],
                'idf': row['idf_score'],
                'examples': json.loads(row['example_words']) if row['example_words'] else []
            })

        return results

    def get_psalm_phrases(self, psalm_number: int) -> List[Dict[str, Any]]:
        """
        Get all phrases for a specific Psalm.

        Args:
            psalm_number: Psalm number (1-150)

        Returns:
            List of dicts with phrase_consonantal, phrase_hebrew, phrase_length,
                          occurrence_count, verse_references
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                phrase_consonantal,
                phrase_hebrew,
                phrase_length,
                occurrence_count,
                verse_references
            FROM psalm_phrases
            WHERE psalm_number = ?
            ORDER BY phrase_length DESC, occurrence_count DESC
        """, (psalm_number,))

        results = []
        for row in cursor.fetchall():
            results.append({
                'consonantal': row['phrase_consonantal'],
                'hebrew': row['phrase_hebrew'],
                'length': row['phrase_length'],
                'count': row['occurrence_count'],
                'verses': json.loads(row['verse_references']) if row['verse_references'] else []
            })

        return results

    def store_relationship(self, relationship: Dict[str, Any]):
        """
        Store a pairwise Psalm relationship.

        Args:
            relationship: Dict with psalm_a, psalm_b, statistics, shared_roots, etc.
        """
        cursor = self.conn.cursor()

        # Ensure psalm_a < psalm_b
        psalm_a = min(relationship['psalm_a'], relationship['psalm_b'])
        psalm_b = max(relationship['psalm_a'], relationship['psalm_b'])

        cursor.execute("""
            INSERT OR REPLACE INTO psalm_relationships
            (psalm_a, psalm_b, shared_root_count, total_roots_a, total_roots_b,
             hypergeometric_pvalue, weighted_overlap_score, z_score, is_significant,
             shared_roots_json, shared_phrases_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            psalm_a,
            psalm_b,
            relationship['shared_root_count'],
            relationship['total_roots_a'],
            relationship['total_roots_b'],
            relationship['pvalue'],
            relationship['weighted_score'],
            relationship['z_score'],
            relationship['is_significant'],
            json.dumps(relationship['shared_roots'], ensure_ascii=False),
            json.dumps(relationship.get('shared_phrases', []), ensure_ascii=False)
        ))

        self.conn.commit()

    def get_relationships_for_psalm(self, psalm_number: int,
                                   significant_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get all relationships involving a specific Psalm.

        Args:
            psalm_number: Psalm number (1-150)
            significant_only: If True, only return significant relationships

        Returns:
            List of relationship dicts
        """
        cursor = self.conn.cursor()

        query = """
            SELECT *
            FROM psalm_relationships
            WHERE (psalm_a = ? OR psalm_b = ?)
        """

        if significant_only:
            query += " AND is_significant = 1"

        query += " ORDER BY hypergeometric_pvalue ASC"

        cursor.execute(query, (psalm_number, psalm_number))

        results = []
        for row in cursor.fetchall():
            # Determine which is the "other" psalm
            other_psalm = row['psalm_b'] if row['psalm_a'] == psalm_number else row['psalm_a']

            results.append({
                'psalm_number': psalm_number,
                'related_psalm': other_psalm,
                'pvalue': row['hypergeometric_pvalue'],
                'weighted_score': row['weighted_overlap_score'],
                'z_score': row['z_score'],
                'shared_root_count': row['shared_root_count'],
                'total_roots_this': row['total_roots_a'] if row['psalm_a'] == psalm_number else row['total_roots_b'],
                'total_roots_other': row['total_roots_b'] if row['psalm_a'] == psalm_number else row['total_roots_a'],
                'shared_roots': json.loads(row['shared_roots_json']),
                'shared_phrases': json.loads(row['shared_phrases_json']) if row['shared_phrases_json'] else []
            })

        return results

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
    # Test database creation
    logging.basicConfig(level=logging.INFO)

    print("Creating psalm_relationships.db...")
    db = PsalmRelationshipsDB()

    print(f"✓ Database created at: {db.db_path}")
    print(f"✓ Schema initialized")

    # Test basic operations
    test_roots = {
        'מלך': {'count': 5, 'examples': ['מֶלֶךְ', 'מַלְכִּי', 'הַמֶּלֶךְ']},
        'שמע': {'count': 3, 'examples': ['שְׁמַע', 'שָׁמַעְתִּי']}
    }

    db.store_psalm_roots(1, test_roots)
    print("✓ Test roots stored for Psalm 1")

    db.update_root_frequencies()
    print("✓ Root frequencies updated")

    roots = db.get_psalm_roots(1)
    print(f"✓ Retrieved {len(roots)} roots for Psalm 1")
    for root in roots:
        print(f"  - {root['root']}: count={root['count']}, idf={root['idf']:.3f}")

    db.close()
    print("\n✓ Database test complete!")
