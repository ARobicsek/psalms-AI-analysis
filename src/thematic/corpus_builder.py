"""Build the Tanakh chunk corpus for thematic search (1-verse chunks)."""
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Iterator
from datetime import datetime

from .chunk_schemas import TanakhChunk, ChunkMetadata, BookCategory, ChunkType

logger = logging.getLogger(__name__)

# Book categorization
TORAH_BOOKS = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
PROPHET_BOOKS = [
    "Joshua", "Judges", "I Samuel", "II Samuel", "I Kings", "II Kings",
    "Isaiah", "Jeremiah", "Ezekiel", "Hosea", "Joel", "Amos", "Obadiah",
    "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai",
    "Zechariah", "Malachi"
]
WRITINGS_BOOKS = [
    "Psalms", "Proverbs", "Job", "Song of Songs", "Ruth", "Lamentations",
    "Ecclesiastes", "Esther", "Daniel", "Ezra", "Nehemiah",
    "I Chronicles", "II Chronicles"
]


def get_book_category(book: str) -> BookCategory:
    """Determine category for a book."""
    if book in TORAH_BOOKS:
        return BookCategory.TORAH
    elif book in PROPHET_BOOKS:
        return BookCategory.PROPHETS
    else:
        return BookCategory.WRITINGS


def clean_hebrew_text(text: str) -> str:
    """Clean Hebrew text by removing cantillation marks but preserving vowels."""
    # Remove pasuq (׀)
    text = text.replace("׀", "")

    # Remove maqqaf (־) and replace with space
    text = text.replace("־", " ")

    # Remove cantillation accents (keep only niqqud vowels and letters)
    # Pattern to keep: Hebrew letters, vowel points, and spaces
    # Remove: accents (֑, ֒, ֓, ֔, ֕, ֖, ֗, ֘, ֙, ֚, ֛, ֜, ֝, ֞, ֟, ֠, ֡, ֢, ֣, ֤, ֥, ֦, ֧, ֨, ֩, ֪, ֫, ֬, ֭, ֮, ֯)
    cantillation_pattern = re.compile(r'[\u0591-\u05AF\u05BD-\u05C5]')
    text = cantillation_pattern.sub('', text)

    # Normalize spaces
    text = re.sub(r'\s+', ' ', text).strip()

    return text


class CorpusBuilder:
    """Builds the Tanakh chunk corpus from database using 1-verse chunks."""

    def __init__(
        self,
        tanakh_db_path: str,
        output_dir: str,
    ):
        """
        Initialize corpus builder for 1-verse chunks.

        Args:
            tanakh_db_path: Path to tanakh.db SQLite database
            output_dir: Directory to write corpus files
        """
        self.tanakh_db_path = Path(tanakh_db_path)
        self.output_dir = Path(output_dir)

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_corpus(self) -> ChunkMetadata:
        """
        Build the complete corpus with 1-verse chunks.

        Returns:
            ChunkMetadata with corpus statistics
        """
        logger.info("Building 1-verse chunk corpus...")

        chunks: List[TanakhChunk] = []

        # Get all books from database
        books = self._get_all_books()

        for book in books:
            logger.info(f"Processing {book}...")
            book_chunks = self._chunk_book(book)
            chunks.extend(book_chunks)
            logger.info(f"  → {len(book_chunks)} verses")

        # Save corpus
        self._save_corpus(chunks)

        # Calculate and save metadata
        metadata = self._calculate_metadata(chunks)
        self._save_metadata(metadata)

        logger.info(f"Corpus complete: {metadata.total_chunks} verses")
        return metadata

    def _get_all_books(self) -> List[str]:
        """Get list of all books in database."""
        import sqlite3

        conn = sqlite3.connect(self.tanakh_db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT book_name FROM verses ORDER BY rowid")
        books = [row[0] for row in cursor.fetchall()]

        conn.close()
        return books

    def _get_book_text(self, book: str) -> List[Dict[str, Any]]:
        """Get all verses for a book."""
        import sqlite3

        conn = sqlite3.connect(self.tanakh_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT book_name, chapter, verse, hebrew, english
            FROM verses
            WHERE book_name = ?
            ORDER BY chapter, verse
        """, (book,))

        verses = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return verses

    def _chunk_book(self, book: str) -> List[TanakhChunk]:
        """Create 1-verse chunks for a book."""
        verses = self._get_book_text(book)

        if not verses:
            logger.warning(f"No verses found for {book}")
            return []

        chunks = []

        for verse_data in verses:
            # Clean Hebrew text
            clean_hebrew = clean_hebrew_text(verse_data["hebrew"])

            # Estimate tokens (rough: 1 token per 4 chars for Hebrew)
            token_estimate = len(clean_hebrew) // 4

            # Create chunk
            chunk = TanakhChunk(
                chunk_id=f"{book.lower().replace(' ', '_')}_{verse_data['chapter']:03d}_{verse_data['verse']:03d}",
                reference=f"{book} {verse_data['chapter']}:{verse_data['verse']}",
                book=book,
                book_category=get_book_category(book),
                chapter=verse_data["chapter"],
                verse=verse_data["verse"],
                hebrew_text=clean_hebrew,
                english_text=verse_data.get("english"),  # Optional English
                chunk_type=ChunkType.SINGLE_VERSE,
                verse_count=1,
                token_estimate=token_estimate,
            )

            chunks.append(chunk)

        return chunks

    def _save_corpus(self, chunks: List[TanakhChunk]) -> None:
        """Save chunks to JSONL file."""
        output_path = self.output_dir / "tanakh_chunks.jsonl"

        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")

        logger.info(f"Saved {len(chunks)} chunks to {output_path}")

    def _calculate_metadata(self, chunks: List[TanakhChunk]) -> ChunkMetadata:
        """Calculate corpus statistics."""
        from collections import Counter

        chunks_by_book = Counter(c.book for c in chunks)
        chunks_by_category = Counter(c.book_category.value for c in chunks)
        chunks_by_type = Counter(c.chunk_type.value for c in chunks)

        avg_verse_count = sum(c.verse_count for c in chunks) / len(chunks) if chunks else 0
        avg_token_estimate = sum(c.token_estimate for c in chunks) / len(chunks) if chunks else 0

        return ChunkMetadata(
            total_chunks=len(chunks),
            chunks_by_book=dict(chunks_by_book),
            chunks_by_category=dict(chunks_by_category),
            chunks_by_type=dict(chunks_by_type),
            avg_verse_count=round(avg_verse_count, 2),
            avg_token_estimate=round(avg_token_estimate, 2),
            created_at=datetime.now().isoformat(),
        )

    def _save_metadata(self, metadata: ChunkMetadata) -> None:
        """Save metadata to JSON file."""
        output_path = self.output_dir / "chunk_metadata.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"Saved metadata to {output_path}")


def load_corpus(corpus_dir: str) -> Iterator[TanakhChunk]:
    """Load chunks from JSONL file."""
    corpus_path = Path(corpus_dir) / "tanakh_chunks.jsonl"

    with open(corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            yield TanakhChunk.from_dict(data)


def load_metadata(corpus_dir: str) -> ChunkMetadata:
    """Load corpus metadata."""
    metadata_path = Path(corpus_dir) / "chunk_metadata.json"

    with open(metadata_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return ChunkMetadata(**data)