"""Pydantic schemas for thematic corpus chunks (1-verse chunks)."""
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
    SINGLE_VERSE = "single_verse"  # One verse per chunk


@dataclass
class TanakhChunk:
    """A single retrievable chunk of Tanakh text (1 verse)."""

    # Identification
    chunk_id: str                    # Unique ID: "genesis_001_001"
    reference: str                   # Human-readable: "Genesis 1:1"

    # Location
    book: str                        # "Genesis"
    book_category: BookCategory      # Torah/Prophets/Writings
    chapter: int                     # 1
    verse: int                       # 1

    # Content
    hebrew_text: str                 # Full Hebrew text (cleaned)
    english_text: Optional[str]      # Full English translation (optional)

    # Metadata
    chunk_type: ChunkType            # Always SINGLE_VERSE for this experiment
    verse_count: int                 # Always 1
    token_estimate: int              # Approximate tokens

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "chunk_id": self.chunk_id,
            "reference": self.reference,
            "book": self.book,
            "book_category": self.book_category.value,
            "chapter": self.chapter,
            "verse": self.verse,
            "hebrew_text": self.hebrew_text,
            "english_text": self.english_text,
            "chunk_type": self.chunk_type.value,
            "verse_count": self.verse_count,
            "token_estimate": self.token_estimate,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TanakhChunk":
        """Create from dictionary."""
        return cls(
            chunk_id=data["chunk_id"],
            reference=data["reference"],
            book=data["book"],
            book_category=BookCategory(data["book_category"]),
            chapter=data["chapter"],
            verse=data["verse"],
            hebrew_text=data["hebrew_text"],
            english_text=data.get("english_text"),
            chunk_type=ChunkType(data["chunk_type"]),
            verse_count=data["verse_count"],
            token_estimate=data["token_estimate"],
        )

    def embedding_text(self) -> str:
        """Text to embed (Hebrew only)."""
        return self.hebrew_text


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