"""
Build the Tanakh chunk corpus for thematic search.

This module provides functionality to chunk the Tanakh (excluding Psalms)
into manageable pieces suitable for embedding and thematic search.
"""
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator
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


def clean_hebrew_text(text: str) -> str:
    """Clean Hebrew text by removing dividers, markers, and cantillation marks."""
    if not text:
        return text

    # Remove pasuq (verse divider)
    text = text.replace('׀', ' ')

    # Remove parsha markers {פ} and {ס}
    text = text.replace('{פ}', ' ').replace('{ס}', ' ')

    # Remove maqqif (־) and replace with space
    text = text.replace('־', ' ')

    # Define cantillation marks to remove (teamim) - these are musical notation marks
    # We specifically exclude vowel marks (nikud) from removal
    cantillation_marks = [
        # Etnachta group
        '\u0591',  # Etnahta
        '\u0592',  # Segol
        '\u0593',  # Shalshelet
        '\u0594',  # Zaqef Qaton
        '\u0595',  # Zaqef Gadol
        '\u0596',  # Zaqef Gadol (alternative)
        '\u0597',  # Tipeha
        '\u0598',  # Revia
        '\u0599',  # Zarqa
        '\u059a',  # Pashta
        '\u059b',  # Yetiv
        '\u059c',  # Tevir
        '\u059d',  # Geresh
        '\u059e',  # Geresh Muqdam
        '\u059f',  # Gershayim
        '\u05a0',  # Qarney Para
        '\u05a1',  # Telisha Gedola
        '\u05a2',  # Pazer
        '\u05a3',  # Telisha Qetana
        '\u05a4',  # Yerah ben Yomo
        '\u05a5',  # Ole
        '\u05a6',  # Iluy
        '\u05a7',  # Dehi
        '\u05a8',  # Zinor
        # Disjunctive accents in lower range
        '\u05a9',  # Munah
        '\u05aa',  # Mahpach
        '\u05ab',  # Mercha
        '\u05ac',  # Mercha Kefula
        '\u05ad',  # Darga
        '\u05ae',  # Qadma
        '\u05af',  # Telisha Qetana (alternative)
        # Additional cantillation marks
        '\u05bd',  # Meteg (sometimes considered a cantillation mark)
        # Punctuation (not cantillation but often want to remove)
        '\u05be',  # Maqaf (different from Unicode 05AD)
    ]

    # Remove cantillation marks
    for mark in cantillation_marks:
        text = text.replace(mark, '')

    # Also remove sof pasuq (colon at end of verses)
    text = text.replace('־', ' ')  # Already handled above
    text = text.replace(':', ' ')   # Remove ASCII colon sometimes used

    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    return text


def clean_english_text(text: str) -> str:
    """
    Comprehensive cleaning of Sefaria English text.

    Removes HTML footnotes, translator notes, cross-references,
    and various formatting artifacts to produce clean text.
    """
    if not text:
        return text

    # Import HTML unescape for entity conversion
    from html import unescape

    # Phase 1: HTML removal
    # Remove footnote markers and content
    text = re.sub(r'<sup class="footnote-marker">[^<]+</sup>', '', text)
    text = re.sub(r'<i class="footnote">[^<]*</i>', '', text)

    # Remove any remaining HTML tags
    text = re.sub(r'</?sup[^>]*>', '', text)
    text = re.sub(r'</?i[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)

    # Convert HTML entities to readable characters
    text = unescape(text)

    # Phase 2: Fix malformed duplicate text FIRST (before other patterns)
    # Pattern: *text*text or *text* more text
    text = re.sub(r'\*([^*]+)\*([^*]+)', r'\2', text)

    # Phase 3: Text-based footnote markers
    # Remove simple footnote indicators like .-a, ,-b, -c
    text = re.sub(r'([.,;:])?\-[a-z](?=\s|$)', r'\1', text)

    # Phase 3: Translator notes and commentary
    # Remove Hebrew language notes (with single quotes)
    text = re.sub(r'\s+Heb\.\s*\'[^\']+\'(?:\.|\s*)(?:Cf\.\s*[^.,]+\.?)?', '', text)
    text = re.sub(r'\s+Heb\s+[^.,;:]+\.\s*(?:Cf\.\s*[^.,;:]+\.?)?', '', text)

    # Remove literal translation notes
    text = re.sub(r'\s+Lit\.\s*\'[^\']+\'\.?', '', text)
    text = re.sub(r'\s+Lit\.\s*\"[^\"]+\"\.?', '', text)

    # Remove cross-references
    # Pattern 1: "Cf. Book. chapter:verse." (with period after book abbreviation)
    text = re.sub(r'\s+Cf\.\s+[A-Za-z]+\.?\s+\d+:\d+(?:\.\d+)?\.?', '', text)
    # Pattern 2: "Cf. Book. chapter:verse-chapter:verse"
    text = re.sub(r'\s+Cf\.\s+[A-Za-z]+\.?\s+\d+:\d+\s*-\s*\d+:\d+', '', text)
    # Pattern 3: "Cf. Book. chapter:verse.-letter"
    text = re.sub(r'\s+Cf\.\s+[A-Za-z]+\.?\s+\d+:\d+\.\-[a-z]', '', text)
    # Pattern 4: "Cf. Book chapter:verse." (no period after book)
    text = re.sub(r'\s+Cf\.\s+[A-Za-z]+\s+\d+:\d+(?:\.\d+)?\.?', '', text)
    # Pattern 5: Any remaining "Cf. text" up to punctuation (but allow book abbreviation with period)
    text = re.sub(r'\s+Cf\.\s+[A-Za-z]+(?:\.\s*|\s+)[^.,;:]+', '', text)

    # Remove emendation notes
    text = re.sub(r'\s+Emendation[^,.]*\.?', '', text)

    # Remove "Others" translations (but keep the word "Others" if it's part of text)
    text = re.sub(r'Others\s*[«\'""][^»\'""]*[»\'""]', 'Others', text)
    text = re.sub(r'Others\s*�[^�]*�', 'Others', text)  # Special quotes
    text = re.sub(r'Others\s*"[^"]*\.', 'Others', text)  # Handle quotes with period

    # Remove parenthetical Hebrew notes
    text = re.sub(r'\s*\([^)]*Heb[^)]*\)', '', text)

    # Phase 4: Artifact cleanup

    # Remove asterisked notes
    text = re.sub(r'\s*\*[^*]+\*\s*', ' ', text)

    # Fix editorial move notes (remove only the note part)
    text = re.sub(r'\s*Moved up from v\.\s*\d+\s+for clarity', '', text)

    # Remove any remaining isolated asterisks
    text = re.sub(r'\*+', '', text)

    # Clean up punctuation artifacts from footnote removal
    text = re.sub(r'\s*\.\s*\d+\.\-[a-z]', '', text)  # Remove ".2.-a" patterns
    text = re.sub(r'\s*\.\s*\d+\.', '', text)  # Remove ".2." patterns
    text = re.sub(r'\s+', ' ', text)  # Clean up extra spaces

    # Phase 5: Text normalization
    # Fix multiple periods
    text = re.sub(r'\.+', '.', text)

    # Fix punctuation spacing
    text = re.sub(r'\s+([,.])', r'\1', text)  # Remove space before punctuation

    # Fix word concatenation issues (e.g., "browShall" -> "brow Shall")
    text = re.sub(r'(\w)([A-Z][a-z])', r'\1 \2', text)

    # Clean whitespace
    lines = text.split('\n')
    lines = [' '.join(line.split()) for line in lines if line.strip()]
    text = '\n'.join(lines)

    # Final cleanup of any remaining multiple spaces
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    return text


def get_book_category(book: str) -> BookCategory:
    """Determine category for a book."""
    if book in TORAH_BOOKS:
        return BookCategory.TORAH
    elif book in PROPHET_BOOKS:
        return BookCategory.PROPHETS
    else:
        return BookCategory.WRITINGS


class CorpusBuilder:
    """Builds the Tanakh chunk corpus from database or Sefaria."""

    def __init__(
        self,
        tanakh_db_path: str,
        output_dir: str,
        window_size: int = 5,
        window_overlap: int = 4,
    ):
        """
        Initialize corpus builder.

        Args:
            tanakh_db_path: Path to tanakh.db SQLite database
            output_dir: Directory to write corpus files
            window_size: Default sliding window size (verses)
            window_overlap: Overlap between windows (verses)
        """
        self.tanakh_db_path = Path(tanakh_db_path)
        self.output_dir = Path(output_dir)
        self.window_size = window_size
        self.window_overlap = window_overlap

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_corpus(
        self,
        exclude_psalms: bool = True,
        use_sefaria_sections: bool = True,
        use_masoretic_markers: bool = False,
    ) -> ChunkMetadata:
        """
        Build the complete corpus.

        Args:
            exclude_psalms: Skip Psalms (we're finding parallels TO psalms)
            use_sefaria_sections: Try Sefaria sections first, fallback to windows
            use_masoretic_markers: Use Masoretic section markers (ס/פ) for chunking

        Returns:
            ChunkMetadata with corpus statistics
        """
        logger.info("Starting corpus build...")

        chunks: List[TanakhChunk] = []

        # Get all books from database
        books = self._get_all_books()

        for book in books:
            if exclude_psalms and book == "Psalms":
                logger.info(f"Skipping {book} (exclude_psalms=True)")
                continue

            logger.info(f"Processing {book}...")
            book_chunks = self._chunk_book(book, use_sefaria_sections, use_masoretic_markers)
            chunks.extend(book_chunks)
            logger.info(f"  → {len(book_chunks)} chunks")

        # Save corpus
        self._save_corpus(chunks)

        # Calculate and save metadata
        metadata = self._calculate_metadata(chunks)
        self._save_metadata(metadata)

        logger.info(f"Corpus complete: {metadata.total_chunks} chunks")
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

    def _chunk_book(
        self,
        book: str,
        use_sefaria_sections: bool,
        use_masoretic_markers: bool = False,
    ) -> List[TanakhChunk]:
        """
        Chunk a single book.

        Strategy:
        1. If use_masoretic_markers: use Masoretic section markers (ס/פ)
        2. Try Sefaria sections if enabled
        3. For Psalms: one chunk per psalm (though usually excluded)
        4. For Proverbs: use collection boundaries
        5. Fallback: sliding window
        """
        verses = self._get_book_text(book)

        if not verses:
            logger.warning(f"No verses found for {book}")
            return []

        # Special handling by book
        if use_masoretic_markers:
            # Use Masoretic section markers
            return self._masoretic_marker_chunks(book, verses)
        elif use_sefaria_sections:
            # Try Sefaria sections first
            sefaria_chunks = self._try_sefaria_sections(book, verses)
            if sefaria_chunks:
                return sefaria_chunks

        # Fallback: sliding window
        return self._sliding_window_chunks(book, verses)

    def _chunk_psalms(self, verses: List[Dict]) -> List[TanakhChunk]:
        """Each psalm is one chunk."""
        chunks = []

        # Group by chapter (each chapter = one psalm)
        chapters: Dict[int, List[Dict]] = {}
        for v in verses:
            ch = v["chapter"]
            if ch not in chapters:
                chapters[ch] = []
            chapters[ch].append(v)

        for chapter, chapter_verses in sorted(chapters.items()):
            chunk = self._create_chunk(
                book="Psalms",
                verses=chapter_verses,
                chunk_type=ChunkType.PSALM,
            )
            chunks.append(chunk)

        return chunks

    def _chunk_proverbs(self, verses: List[Dict]) -> List[TanakhChunk]:
        """
        Chunk Proverbs by known collection boundaries.

        Collections:
        - 1:1-9:18 (Father's instruction)
        - 10:1-22:16 (Solomonic proverbs I)
        - 22:17-24:22 (Words of the wise)
        - 24:23-34 (More words of the wise)
        - 25:1-29:27 (Hezekiah's collection)
        - 30:1-33 (Agur's words)
        - 31:1-31 (Lemuel's words + Woman of Valor)
        """
        collections = [
            (1, 1, 9, 18, "Father's Instruction"),
            (10, 1, 22, 16, "Solomonic Proverbs I"),
            (22, 17, 24, 22, "Words of the Wise"),
            (24, 23, 24, 34, "More Words of the Wise"),
            (25, 1, 29, 27, "Hezekiah's Collection"),
            (30, 1, 30, 33, "Agur's Words"),
            (31, 1, 31, 31, "Lemuel and Woman of Valor"),
        ]

        chunks = []

        for start_ch, start_v, end_ch, end_v, name in collections:
            collection_verses = [
                v for v in verses
                if (v["chapter"] > start_ch or
                    (v["chapter"] == start_ch and v["verse"] >= start_v))
                and (v["chapter"] < end_ch or
                     (v["chapter"] == end_ch and v["verse"] <= end_v))
            ]

            if collection_verses:
                # Large collections get sub-chunked
                if len(collection_verses) > 30:
                    sub_chunks = self._sliding_window_chunks(
                        "Proverbs",
                        collection_verses,
                        window_size=10,
                        chunk_type=ChunkType.SEFARIA_SECTION,
                    )
                    chunks.extend(sub_chunks)
                else:
                    chunk = self._create_chunk(
                        book="Proverbs",
                        verses=collection_verses,
                        chunk_type=ChunkType.SEFARIA_SECTION,
                    )
                    chunks.append(chunk)

        return chunks

    def _chunk_job(self, verses: List[Dict]) -> List[TanakhChunk]:
        """
        Chunk Job by major sections.

        Structure:
        - 1-2: Prose prologue
        - 3: Job's opening lament
        - 4-14: First cycle of dialogues
        - 15-21: Second cycle
        - 22-31: Third cycle + Job's oath
        - 32-37: Elihu's speeches
        - 38-41: God's speeches
        - 42: Epilogue
        """
        sections = [
            (1, 1, 2, 13, "Prose Prologue"),
            (3, 1, 3, 26, "Job's Opening Lament"),
            # First cycle
            (4, 1, 5, 27, "Eliphaz's First Speech"),
            (6, 1, 7, 21, "Job's First Reply"),
            (8, 1, 8, 22, "Bildad's First Speech"),
            (9, 1, 10, 22, "Job's Second Reply"),
            (11, 1, 11, 20, "Zophar's First Speech"),
            (12, 1, 14, 22, "Job's Third Reply"),
            # Second cycle
            (15, 1, 15, 35, "Eliphaz's Second Speech"),
            (16, 1, 17, 16, "Job's Fourth Reply"),
            (18, 1, 18, 21, "Bildad's Second Speech"),
            (19, 1, 19, 29, "Job's Fifth Reply"),
            (20, 1, 20, 29, "Zophar's Second Speech"),
            (21, 1, 21, 34, "Job's Sixth Reply"),
            # Third cycle (broken)
            (22, 1, 22, 30, "Eliphaz's Third Speech"),
            (23, 1, 24, 25, "Job's Seventh Reply"),
            (25, 1, 25, 6, "Bildad's Third Speech"),
            (26, 1, 31, 40, "Job's Final Defense"),
            # Elihu
            (32, 1, 33, 33, "Elihu's First Speech"),
            (34, 1, 34, 37, "Elihu's Second Speech"),
            (35, 1, 35, 16, "Elihu's Third Speech"),
            (36, 1, 37, 24, "Elihu's Fourth Speech"),
            # God
            (38, 1, 39, 30, "God's First Speech"),
            (40, 1, 40, 5, "Job's First Response"),
            (40, 6, 41, 34, "God's Second Speech"),
            (42, 1, 42, 6, "Job's Final Response"),
            (42, 7, 42, 17, "Prose Epilogue"),
        ]

        chunks = []

        for start_ch, start_v, end_ch, end_v, name in sections:
            section_verses = [
                v for v in verses
                if (v["chapter"] > start_ch or
                    (v["chapter"] == start_ch and v["verse"] >= start_v))
                and (v["chapter"] < end_ch or
                     (v["chapter"] == end_ch and v["verse"] <= end_v))
            ]

            if section_verses:
                chunk = self._create_chunk(
                    book="Job",
                    verses=section_verses,
                    chunk_type=ChunkType.SPEAKER_TURN,
                )
                chunks.append(chunk)

        return chunks

    def _try_sefaria_sections(
        self,
        book: str,
        verses: List[Dict],
    ) -> Optional[List[TanakhChunk]]:
        """
        Try to get section boundaries from Sefaria.

        This is a placeholder - actual implementation would call Sefaria API
        or use downloaded section data.
        """
        # TODO: Implement Sefaria API integration
        # For now, return None to fall back to sliding window
        return None

    def _masoretic_marker_chunks(
        self,
        book: str,
        verses: List[Dict],
    ) -> List[TanakhChunk]:
        """
        Create chunks using proper Masoretic section markers {ס} and {פ}.

        The Masoretic text includes special markers that mark paragraph boundaries:
        - {ס} (samekh in braces) marks the end of a closed section (paragraph break)
        - {פ} (peh in braces) marks the end of an open section (new line but same paragraph)

        These markers provide thematic boundaries that have been used for centuries.
        NOTE: We look for {ס} and {פ} specifically, not standalone letters.
        """
        chunks = []
        current_chunk_verses = []

        for verse in verses:
            current_chunk_verses.append(verse)
            hebrew_text = verse["hebrew"]

            # Check if this verse has a proper Masoretic marker (with braces)
            has_samekh = '{ס}' in hebrew_text
            has_peh = '{פ}' in hebrew_text

            # If we find a section marker, create a chunk
            if has_samekh or has_peh:
                # Create a copy of verses for this chunk
                chunk_verses = []
                for v in current_chunk_verses:
                    verse_copy = v.copy()
                    # Remove markers from the text for cleaner output
                    verse_copy["hebrew"] = verse_copy["hebrew"].replace('{ס}', '').replace('{פ}', '')
                    chunk_verses.append(verse_copy)

                chunk = self._create_chunk(
                    book=book,
                    verses=chunk_verses,
                    chunk_type=ChunkType.SEFARIA_SECTION,  # Reuse this type for traditional sections
                )
                chunks.append(chunk)
                current_chunk_verses = []

        # Don't forget the last verses if no marker at book end
        if current_chunk_verses:
            chunk = self._create_chunk(
                book=book,
                verses=current_chunk_verses,
                chunk_type=ChunkType.SEFARIA_SECTION,
            )
            chunks.append(chunk)

        return chunks

    def _sliding_window_chunks(
        self,
        book: str,
        verses: List[Dict],
        window_size: Optional[int] = None,
        window_overlap: Optional[int] = None,
        chunk_type: ChunkType = ChunkType.SLIDING_WINDOW,
    ) -> List[TanakhChunk]:
        """Create chunks using sliding window."""
        if window_size is None:
            window_size = self.window_size
        if window_overlap is None:
            window_overlap = self.window_overlap

        chunks = []
        step = window_size - window_overlap

        i = 0
        while i < len(verses):
            window_verses = verses[i:i + window_size]

            chunk = self._create_chunk(
                book=book,
                verses=window_verses,
                chunk_type=chunk_type,
            )
            chunks.append(chunk)

            i += step

            # Don't create tiny final chunks
            if i < len(verses) and len(verses) - i < window_overlap:
                break

        return chunks

    def _create_chunk(
        self,
        book: str,
        verses: List[Dict],
        chunk_type: ChunkType,
    ) -> TanakhChunk:
        """Create a TanakhChunk from verses."""
        if not verses:
            raise ValueError("Cannot create chunk from empty verses")

        first = verses[0]
        last = verses[-1]

        # Build reference string
        if first["chapter"] == last["chapter"]:
            if first["verse"] == last["verse"]:
                reference = f"{book} {first['chapter']}:{first['verse']}"
            else:
                reference = f"{book} {first['chapter']}:{first['verse']}-{last['verse']}"
        else:
            reference = f"{book} {first['chapter']}:{first['verse']}-{last['chapter']}:{last['verse']}"

        # Build chunk ID
        chunk_id = f"{book.lower().replace(' ', '_')}_{first['chapter']:03d}_{first['verse']:03d}_{last['chapter']:03d}_{last['verse']:03d}"

        # Combine and clean text
        hebrew_text = clean_hebrew_text(" ".join(v["hebrew"] for v in verses))
        # Hebrew-only approach - no English text to avoid footnotes
        english_text = None  # Optional: just reference for identification
        # Alternative: keep minimal reference
        # english_text = reference

        # Estimate tokens (Hebrew-only: 1 token per 4 chars)
        token_estimate = len(hebrew_text) // 4

        return TanakhChunk(
            chunk_id=chunk_id,
            reference=reference,
            book=book,
            book_category=get_book_category(book),
            start_chapter=first["chapter"],
            start_verse=first["verse"],
            end_chapter=last["chapter"],
            end_verse=last["verse"],
            hebrew_text=hebrew_text,
            english_text=english_text,
            chunk_type=chunk_type,
            verse_count=len(verses),
            token_estimate=token_estimate,
        )

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

    return ChunkMetadata.from_dict(data)