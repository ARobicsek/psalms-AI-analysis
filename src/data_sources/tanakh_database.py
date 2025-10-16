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
    from data_sources.sefaria_client import PsalmText, PsalmVerse, Verse, BookText, SefariaClient
else:
    # Running as module - use relative import
    from .sefaria_client import PsalmText, PsalmVerse, Verse, BookText, SefariaClient

logger = logging.getLogger(__name__)

# Default database location
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "database" / "tanakh.db"

# Tanakh structure: book names and chapter counts
# Based on Hebrew Bible (Tanakh) structure
TANAKH_BOOKS = {
    # Torah (5 books)
    'Torah': [
        ('Genesis', 'בראשית', 50),
        ('Exodus', 'שמות', 40),
        ('Leviticus', 'ויקרא', 27),
        ('Numbers', 'במדבר', 36),
        ('Deuteronomy', 'דברים', 34),
    ],
    # Nevi'im - Prophets (21 books)
    'Prophets': [
        ('Joshua', 'יהושע', 24),
        ('Judges', 'שופטים', 21),
        ('I Samuel', 'שמואל א', 31),
        ('II Samuel', 'שמואל ב', 24),
        ('I Kings', 'מלכים א', 22),
        ('II Kings', 'מלכים ב', 25),
        ('Isaiah', 'ישעיהו', 66),
        ('Jeremiah', 'ירמיהו', 52),
        ('Ezekiel', 'יחזקאל', 48),
        ('Hosea', 'הושע', 14),
        ('Joel', 'יואל', 4),
        ('Amos', 'עמוס', 9),
        ('Obadiah', 'עובדיה', 1),
        ('Jonah', 'יונה', 4),
        ('Micah', 'מיכה', 7),
        ('Nahum', 'נחום', 3),
        ('Habakkuk', 'חבקוק', 3),
        ('Zephaniah', 'צפניה', 3),
        ('Haggai', 'חגי', 2),
        ('Zechariah', 'זכריה', 14),
        ('Malachi', 'מלאכי', 3),
    ],
    # Ketuvim - Writings (13 books)
    'Writings': [
        ('Psalms', 'תהלים', 150),
        ('Proverbs', 'משלי', 31),
        ('Job', 'איוב', 42),
        ('Song of Songs', 'שיר השירים', 8),
        ('Ruth', 'רות', 4),
        ('Lamentations', 'איכה', 5),
        ('Ecclesiastes', 'קהלת', 12),
        ('Esther', 'אסתר', 10),
        ('Daniel', 'דניאל', 12),
        ('Ezra', 'עזרא', 10),
        ('Nehemiah', 'נחמיה', 13),
        ('I Chronicles', 'דברי הימים א', 29),
        ('II Chronicles', 'דברי הימים ב', 36),
    ]
}


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

        # Concordance table - word-level index for fast Hebrew searching
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concordance (
                concordance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,              -- Original word with all diacritics
                word_consonantal TEXT NOT NULL,  -- Consonants only (for flexible search)
                word_voweled TEXT NOT NULL,      -- Consonants + vowels (for precise search)
                book_name TEXT NOT NULL,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                position INTEGER NOT NULL,       -- Word position in verse (0-indexed)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (book_name, chapter, verse)
                    REFERENCES verses(book_name, chapter, verse)
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

        # Concordance indices - critical for fast Hebrew word searches
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_concordance_consonantal
            ON concordance(word_consonantal)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_concordance_voweled
            ON concordance(word_voweled)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_concordance_exact
            ON concordance(word)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_concordance_reference
            ON concordance(book_name, chapter, verse)
        """)

        self.conn.commit()
        logger.info(f"Database schema created at {self.db_path}")

    def store_book_chapter(self, book_text: BookText, category: str = None) -> int:
        """
        Store a complete chapter from any biblical book.

        Args:
            book_text: BookText object to store
            category: Book category (Torah, Prophets, Writings)

        Returns:
            Number of verses stored
        """
        cursor = self.conn.cursor()

        # Ensure book exists
        cursor.execute("""
            INSERT OR IGNORE INTO books (name, hebrew_name, category)
            VALUES (?, ?, ?)
        """, (book_text.book, book_text.title_hebrew, category or "Unknown"))

        # Store chapter metadata
        cursor.execute("""
            INSERT OR REPLACE INTO chapters
            (book_name, chapter_number, verse_count, title_english, title_hebrew)
            VALUES (?, ?, ?, ?, ?)
        """, (book_text.book, book_text.chapter, book_text.verse_count,
              book_text.title_english, book_text.title_hebrew))

        # Store verses
        stored_count = 0
        for verse in book_text.verses:
            cursor.execute("""
                INSERT OR REPLACE INTO verses
                (book_name, chapter, verse, hebrew, english, reference)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (book_text.book, verse.chapter, verse.verse,
                  verse.hebrew, verse.english, verse.reference))
            stored_count += 1

        self.conn.commit()
        logger.debug(f"Stored {book_text.book} {book_text.chapter} ({stored_count} verses)")
        return stored_count

    def store_psalm(self, psalm: PsalmText) -> int:
        """
        Store a complete Psalm in the database.

        Args:
            psalm: PsalmText object to store

        Returns:
            Number of verses stored
        """
        return self.store_book_chapter(psalm, category="Writings")

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

    def download_entire_tanakh(self, force: bool = False) -> Dict[str, Any]:
        """
        Download the entire Tanakh (Hebrew Bible) from Sefaria.

        Args:
            force: If True, re-download even if already in database

        Returns:
            Statistics about the download
        """
        client = SefariaClient()
        stats = {
            'downloaded_chapters': 0,
            'skipped_chapters': 0,
            'failed_chapters': [],
            'total_verses': 0,
            'books_processed': 0
        }

        logger.info("Starting download of entire Tanakh...")

        for category, books in TANAKH_BOOKS.items():
            logger.info(f"\n=== Processing {category} ===")

            for book_name, hebrew_name, chapter_count in books:
                logger.info(f"Downloading {book_name} ({chapter_count} chapters)...")

                for chapter in range(1, chapter_count + 1):
                    try:
                        # Check if chapter already exists
                        cursor = self.conn.cursor()
                        cursor.execute("""
                            SELECT COUNT(*) as count
                            FROM chapters
                            WHERE book_name = ? AND chapter_number = ?
                        """, (book_name, chapter))

                        if not force and cursor.fetchone()['count'] > 0:
                            logger.debug(f"{book_name} {chapter} already exists, skipping")
                            stats['skipped_chapters'] += 1
                            continue

                        # Fetch chapter
                        book_text = client.fetch_book_chapter(book_name, chapter)

                        # Store in database
                        verse_count = self.store_book_chapter(book_text, category=category)

                        stats['downloaded_chapters'] += 1
                        stats['total_verses'] += verse_count

                        # Progress update every 20 chapters
                        if stats['downloaded_chapters'] % 20 == 0:
                            logger.info(f"Progress: {stats['downloaded_chapters']} chapters, "
                                       f"{stats['total_verses']} verses downloaded")

                    except Exception as e:
                        logger.error(f"Failed to download {book_name} {chapter}: {e}")
                        stats['failed_chapters'].append(f"{book_name} {chapter}")

                stats['books_processed'] += 1
                logger.info(f"Completed {book_name} ({chapter_count} chapters)")

        logger.info(f"\n=== Tanakh Download Complete ===")
        logger.info(f"Downloaded: {stats['downloaded_chapters']} chapters")
        logger.info(f"Skipped: {stats['skipped_chapters']} chapters")
        logger.info(f"Total verses: {stats['total_verses']}")
        logger.info(f"Books processed: {stats['books_processed']}")

        if stats['failed_chapters']:
            logger.warning(f"Failed chapters ({len(stats['failed_chapters'])}): {stats['failed_chapters'][:10]}")

        return stats

    def build_concordance_index(self, force: bool = False) -> Dict[str, Any]:
        """
        Build concordance index from all verses in the database.
        Parses each verse into words and stores normalized forms.

        Args:
            force: If True, rebuild even if concordance already exists

        Returns:
            Statistics about the indexing process
        """
        # Import here to avoid circular dependency
        if __name__ == '__main__':
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from concordance.hebrew_text_processor import split_words, normalize_for_search
        else:
            from ..concordance.hebrew_text_processor import split_words, normalize_for_search

        cursor = self.conn.cursor()

        # Check if concordance already exists
        cursor.execute("SELECT COUNT(*) as count FROM concordance")
        existing_count = cursor.fetchone()['count']

        if existing_count > 0 and not force:
            logger.info(f"Concordance already exists with {existing_count} entries. Use force=True to rebuild.")
            return {
                'skipped': True,
                'existing_entries': existing_count
            }

        # Clear existing concordance if rebuilding
        if force:
            logger.info("Clearing existing concordance...")
            cursor.execute("DELETE FROM concordance")
            self.conn.commit()

        logger.info("Building concordance index from all verses...")

        stats = {
            'verses_processed': 0,
            'words_indexed': 0,
            'failed_verses': []
        }

        # Get all verses
        cursor.execute("""
            SELECT book_name, chapter, verse, hebrew
            FROM verses
            ORDER BY book_name, chapter, verse
        """)

        verses = cursor.fetchall()
        total_verses = len(verses)

        for i, row in enumerate(verses):
            try:
                book_name = row['book_name']
                chapter = row['chapter']
                verse_num = row['verse']
                hebrew_text = row['hebrew']

                # Skip empty verses
                if not hebrew_text or not hebrew_text.strip():
                    continue

                # Split into words
                words = split_words(hebrew_text)

                # Index each word
                for position, word in enumerate(words):
                    # Normalize at different levels
                    word_consonantal = normalize_for_search(word, 'consonantal')
                    word_voweled = normalize_for_search(word, 'voweled')

                    # Insert into concordance
                    cursor.execute("""
                        INSERT INTO concordance
                        (word, word_consonantal, word_voweled, book_name, chapter, verse, position)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (word, word_consonantal, word_voweled, book_name, chapter, verse_num, position))

                    stats['words_indexed'] += 1

                stats['verses_processed'] += 1

                # Progress update
                if (i + 1) % 1000 == 0:
                    self.conn.commit()  # Commit periodically
                    logger.info(f"Progress: {i + 1}/{total_verses} verses processed, "
                               f"{stats['words_indexed']} words indexed")

            except Exception as e:
                logger.error(f"Failed to index {book_name} {chapter}:{verse_num}: {e}")
                stats['failed_verses'].append(f"{book_name} {chapter}:{verse_num}")

        # Final commit
        self.conn.commit()

        logger.info(f"Concordance indexing complete!")
        logger.info(f"  Verses processed: {stats['verses_processed']}/{total_verses}")
        logger.info(f"  Words indexed: {stats['words_indexed']}")

        if stats['failed_verses']:
            logger.warning(f"  Failed verses: {len(stats['failed_verses'])}")

        return stats

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM books")
        book_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM chapters")
        chapter_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM verses")
        verse_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM lexicon_cache")
        lexicon_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM concordance")
        concordance_count = cursor.fetchone()['count']

        return {
            'books': book_count,
            'chapters': chapter_count,
            'verses': verse_count,
            'concordance_words': concordance_count,
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
    parser.add_argument('--download-tanakh', action='store_true',
                       help='Download entire Tanakh (all books)')
    parser.add_argument('--build-concordance', action='store_true',
                       help='Build concordance index from all verses')
    parser.add_argument('--force', action='store_true',
                       help='Force re-download/rebuild even if already exists')
    parser.add_argument('--stats', action='store_true',
                       help='Show database statistics')
    parser.add_argument('--get-psalm', type=int,
                       help='Retrieve a specific Psalm')

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    db = TanakhDatabase()

    if args.stats:
        stats = db.get_statistics()
        print("\n=== Database Statistics ===")
        for key, value in stats.items():
            print(f"{key}: {value}")

    elif args.build_concordance:
        print("\n=== Building Concordance Index ===")
        print("This will index all Hebrew words in the database.")
        print("Estimated time: 2-3 minutes\n")
        stats = db.build_concordance_index(force=args.force)
        if stats.get('skipped'):
            print(f"Concordance already exists with {stats['existing_entries']} entries.")
            print("Use --force to rebuild.")
        else:
            print(f"\n=== Concordance Build Complete ===")
            print(f"Verses processed: {stats['verses_processed']}")
            print(f"Words indexed: {stats['words_indexed']}")
            if stats.get('failed_verses'):
                print(f"Failed: {len(stats['failed_verses'])} verses")

    elif args.download_tanakh:
        print("\n=== Downloading Entire Tanakh ===")
        print("This will download all books of the Hebrew Bible.")
        print("Estimated time: 5-10 minutes\n")
        stats = db.download_entire_tanakh(force=args.force)
        print(f"\n=== Download Complete ===")
        print(f"Chapters downloaded: {stats['downloaded_chapters']}")
        print(f"Chapters skipped: {stats['skipped_chapters']}")
        print(f"Total verses: {stats['total_verses']}")
        print(f"Books processed: {stats['books_processed']}")
        if stats['failed_chapters']:
            print(f"Failed: {len(stats['failed_chapters'])} chapters")

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
