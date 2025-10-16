"""
Tanakh Database Manager

Creates and manages a local SQLite database for storing biblical texts.
This allows offline access and faster queries compared to API calls.

Schema:
- books: Book metadata
- chapters: Chapter metadata
- verses: Verse-level text storage (Hebrew and English)
- lexicon_cache: Cached BDB lookups

Usage:
    db = TanakhDatabase()
    db.store_psalm(psalm_text)
    verse = db.get_verse("Psalms", 23, 1)
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import asdict
import logging
import sys

# Handle imports for both module and script usage
if __name__ == '__main__':
    # Running as script - add parent to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from data_sources.sefaria_client import PsalmText, PsalmVerse, SefariaClient
else:
    # Running as module - use relative import
    from .sefaria_client import PsalmText, PsalmVerse, SefariaClient

logger = logging.getLogger(__name__)

# Default database location
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "database" / "tanakh.db"


class TanakhDatabase:
    """Manages local storage of biblical texts."""

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

        # Books table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                hebrew_name TEXT,
                chapter_count INTEGER,
                verse_count INTEGER,
                category TEXT,  -- Torah, Prophets, Writings
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Chapters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chapters (
                chapter_id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_name TEXT NOT NULL,
                chapter_number INTEGER NOT NULL,
                verse_count INTEGER,
                title_english TEXT,
                title_hebrew TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(book_name, chapter_number),
                FOREIGN KEY (book_name) REFERENCES books(name)
            )
        """)

        # Verses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verses (
                verse_id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_name TEXT NOT NULL,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                hebrew TEXT NOT NULL,
                english TEXT NOT NULL,
                reference TEXT NOT NULL,  -- e.g., "Psalms 23:1"
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(book_name, chapter, verse),
                FOREIGN KEY (book_name) REFERENCES books(name)
            )
        """)

        # Lexicon cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lexicon_cache (
                cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE NOT NULL,
                lexicon TEXT NOT NULL,  -- BDB, Klein, etc.
                headword TEXT,
                definition TEXT,
                raw_data TEXT,  -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indices for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verses_reference
            ON verses(book_name, chapter, verse)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lexicon_word
            ON lexicon_cache(word, lexicon)
        """)

        self.conn.commit()
        logger.info(f"Database schema created at {self.db_path}")

    def store_psalm(self, psalm: PsalmText) -> int:
        """
        Store a complete Psalm in the database.

        Args:
            psalm: PsalmText object to store

        Returns:
            Number of verses stored
        """
        cursor = self.conn.cursor()

        # Ensure book exists
        cursor.execute("""
            INSERT OR IGNORE INTO books (name, hebrew_name, category)
            VALUES (?, ?, ?)
        """, ("Psalms", "תהלים", "Writings"))

        # Store chapter metadata
        cursor.execute("""
            INSERT OR REPLACE INTO chapters
            (book_name, chapter_number, verse_count, title_english, title_hebrew)
            VALUES (?, ?, ?, ?, ?)
        """, ("Psalms", psalm.chapter, psalm.verse_count,
              psalm.title_english, psalm.title_hebrew))

        # Store verses
        stored_count = 0
        for verse in psalm.verses:
            cursor.execute("""
                INSERT OR REPLACE INTO verses
                (book_name, chapter, verse, hebrew, english, reference)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("Psalms", verse.chapter, verse.verse,
                  verse.hebrew, verse.english, verse.reference))
            stored_count += 1

        self.conn.commit()
        logger.info(f"Stored Psalm {psalm.chapter} ({stored_count} verses)")
        return stored_count

    def get_verse(self, book: str, chapter: int, verse: int) -> Optional[PsalmVerse]:
        """
        Retrieve a single verse from the database.

        Args:
            book: Book name (e.g., "Psalms")
            chapter: Chapter number
            verse: Verse number

        Returns:
            PsalmVerse object if found, None otherwise
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT chapter, verse, hebrew, english, reference
            FROM verses
            WHERE book_name = ? AND chapter = ? AND verse = ?
        """, (book, chapter, verse))

        row = cursor.fetchone()
        if row:
            return PsalmVerse(
                chapter=row['chapter'],
                verse=row['verse'],
                hebrew=row['hebrew'],
                english=row['english'],
                reference=row['reference']
            )
        return None

    def get_psalm(self, chapter: int) -> Optional[PsalmText]:
        """
        Retrieve a complete Psalm from the database.

        Args:
            chapter: Psalm number (1-150)

        Returns:
            PsalmText object if found, None otherwise
        """
        cursor = self.conn.cursor()

        # Get chapter metadata
        cursor.execute("""
            SELECT verse_count, title_english, title_hebrew
            FROM chapters
            WHERE book_name = ? AND chapter_number = ?
        """, ("Psalms", chapter))

        chapter_row = cursor.fetchone()
        if not chapter_row:
            return None

        # Get all verses
        cursor.execute("""
            SELECT chapter, verse, hebrew, english, reference
            FROM verses
            WHERE book_name = ? AND chapter = ?
            ORDER BY verse
        """, ("Psalms", chapter))

        verses = []
        for row in cursor.fetchall():
            verses.append(PsalmVerse(
                chapter=row['chapter'],
                verse=row['verse'],
                hebrew=row['hebrew'],
                english=row['english'],
                reference=row['reference']
            ))

        return PsalmText(
            chapter=chapter,
            title_hebrew=chapter_row['title_hebrew'],
            title_english=chapter_row['title_english'],
            verses=verses,
            verse_count=len(verses)
        )

    def has_psalm(self, chapter: int) -> bool:
        """
        Check if a Psalm is already in the database.

        Args:
            chapter: Psalm number

        Returns:
            True if psalm exists, False otherwise
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM chapters
            WHERE book_name = ? AND chapter_number = ?
        """, ("Psalms", chapter))

        return cursor.fetchone()['count'] > 0

    def get_psalm_count(self) -> int:
        """Get number of Psalms stored in database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM chapters
            WHERE book_name = ?
        """, ("Psalms",))

        return cursor.fetchone()['count']

    def download_all_psalms(self, force: bool = False) -> Dict[str, Any]:
        """
        Download all 150 Psalms from Sefaria and store in database.

        Args:
            force: If True, re-download even if already in database

        Returns:
            Statistics about the download
        """
        client = SefariaClient()
        stats = {
            'downloaded': 0,
            'skipped': 0,
            'failed': [],
            'total_verses': 0
        }

        logger.info("Starting download of all 150 Psalms...")

        for chapter in range(1, 151):
            try:
                # Skip if already exists (unless force=True)
                if not force and self.has_psalm(chapter):
                    logger.debug(f"Psalm {chapter} already in database, skipping")
                    stats['skipped'] += 1
                    continue

                # Fetch from API
                psalm = client.fetch_psalm(chapter)

                # Store in database
                verse_count = self.store_psalm(psalm)

                stats['downloaded'] += 1
                stats['total_verses'] += verse_count

                if chapter % 10 == 0:
                    logger.info(f"Progress: {chapter}/150 Psalms downloaded")

            except Exception as e:
                logger.error(f"Failed to download Psalm {chapter}: {e}")
                stats['failed'].append(chapter)

        logger.info(f"Download complete: {stats['downloaded']} downloaded, "
                   f"{stats['skipped']} skipped, {len(stats['failed'])} failed")

        return stats

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM books")
        book_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM chapters WHERE book_name = 'Psalms'")
        psalm_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM verses WHERE book_name = 'Psalms'")
        verse_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM lexicon_cache")
        lexicon_count = cursor.fetchone()['count']

        return {
            'books': book_count,
            'psalms': psalm_count,
            'verses': verse_count,
            'lexicon_entries': lexicon_count,
            'db_path': str(self.db_path)
        }

    def close(self):
        """Close database connection."""
        self.conn.close()

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close()


def main():
    """Command-line interface for database operations."""
    import argparse

    # Ensure UTF-8 encoding for Hebrew text on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description='Manage Tanakh database')
    parser.add_argument('--download-all', action='store_true',
                       help='Download all 150 Psalms from Sefaria')
    parser.add_argument('--force', action='store_true',
                       help='Force re-download even if already exists')
    parser.add_argument('--stats', action='store_true',
                       help='Show database statistics')
    parser.add_argument('--get-psalm', type=int,
                       help='Retrieve a specific Psalm')

    args = parser.parse_args()

    db = TanakhDatabase()

    if args.stats:
        stats = db.get_statistics()
        print("\n=== Database Statistics ===")
        for key, value in stats.items():
            print(f"{key}: {value}")

    elif args.download_all:
        stats = db.download_all_psalms(force=args.force)
        print(f"\n=== Download Complete ===")
        print(f"Downloaded: {stats['downloaded']}")
        print(f"Skipped: {stats['skipped']}")
        print(f"Total verses: {stats['total_verses']}")
        if stats['failed']:
            print(f"Failed: {stats['failed']}")

    elif args.get_psalm:
        psalm = db.get_psalm(args.get_psalm)
        if psalm:
            print(f"\n=== {psalm.title_english} ({psalm.title_hebrew}) ===")
            print(f"Verses: {psalm.verse_count}")
            for verse in psalm.verses[:3]:
                print(f"\n{verse.reference}")
                print(f"  {verse.hebrew}")
                print(f"  {verse.english}")
            if psalm.verse_count > 3:
                print(f"\n... ({psalm.verse_count - 3} more verses)")
        else:
            print(f"Psalm {args.get_psalm} not found in database")

    else:
        parser.print_help()

    db.close()


if __name__ == '__main__':
    main()
