"""
Pydantic schemas for thematic corpus chunks.

This module defines the data structures for representing chunks of Tanakh text
that will be embedded and searched for thematic parallels.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class BookCategory(Enum):
    """Category of biblical book."""
    TORAH = "Torah"
    PROPHETS = "Prophets"
    WRITINGS = "Writings"


class ChunkType(Enum):
    """How the chunk was created."""
    SEFARIA_SECTION = "sefaria_section"  # Native Sefaria section
    SLIDING_WINDOW = "sliding_window"     # Fallback windowing
    PSALM = "psalm"                       # Individual psalm
    SPEAKER_TURN = "speaker_turn"         # Dialogue chunk (Job)


@dataclass
class TanakhChunk:
    """A single retrievable chunk of Tanakh text."""

    # Identification
    chunk_id: str                    # Unique ID: "genesis_001_001_005"
    reference: str                   # Human-readable: "Genesis 1:1-5"

    # Location
    book: str                        # "Genesis"
    book_category: BookCategory      # Torah/Prophets/Writings
    start_chapter: int               # 1
    start_verse: int                 # 1
    end_chapter: int                 # 1
    end_verse: int                   # 5

    # Content
    hebrew_text: str                 # Full Hebrew text
    english_text: str                # Full English translation

    # Metadata
    chunk_type: ChunkType            # How this chunk was created
    verse_count: int                 # Number of verses
    token_estimate: int              # Approximate tokens (Hebrew + English)

    # Optional enrichment
    sefaria_topics: List[str] = field(default_factory=list)  # Topic tags if available

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "chunk_id": self.chunk_id,
            "reference": self.reference,
            "book": self.book,
            "book_category": self.book_category.value,
            "start_chapter": self.start_chapter,
            "start_verse": self.start_verse,
            "end_chapter": self.end_chapter,
            "end_verse": self.end_verse,
            "hebrew_text": self.hebrew_text,
            "english_text": self.english_text,
            "chunk_type": self.chunk_type.value,
            "verse_count": self.verse_count,
            "token_estimate": self.token_estimate,
            "sefaria_topics": self.sefaria_topics,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TanakhChunk":
        """Create from dictionary."""
        return cls(
            chunk_id=data["chunk_id"],
            reference=data["reference"],
            book=data["book"],
            book_category=BookCategory(data["book_category"]),
            start_chapter=data["start_chapter"],
            start_verse=data["start_verse"],
            end_chapter=data["end_chapter"],
            end_verse=data["end_verse"],
            hebrew_text=data["hebrew_text"],
            english_text=data["english_text"],
            chunk_type=ChunkType(data["chunk_type"]),
            verse_count=data["verse_count"],
            token_estimate=data["token_estimate"],
            sefaria_topics=data.get("sefaria_topics", []),
        )

    def embedding_text(self) -> str:
        """Text to embed (Hebrew + English combined)."""
        return f"{self.hebrew_text}\n{self.english_text}"


@dataclass
class ChunkMetadata:
    """Statistics about the corpus."""
    total_chunks: int
    chunks_by_book: Dict[str, int]
    chunks_by_category: Dict[str, int]
    chunks_by_type: Dict[str, int]
    avg_verse_count: float
    avg_token_estimate: float
    created_at: str  # ISO timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_chunks": self.total_chunks,
            "chunks_by_book": self.chunks_by_book,
            "chunks_by_category": self.chunks_by_category,
            "chunks_by_type": self.chunks_by_type,
            "avg_verse_count": self.avg_verse_count,
            "avg_token_estimate": self.avg_token_estimate,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChunkMetadata":
        """Create from dictionary."""
        return cls(
            total_chunks=data["total_chunks"],
            chunks_by_book=data["chunks_by_book"],
            chunks_by_category=data["chunks_by_category"],
            chunks_by_type=data["chunks_by_type"],
            avg_verse_count=data["avg_verse_count"],
            avg_token_estimate=data["avg_token_estimate"],
            created_at=data["created_at"],
        )