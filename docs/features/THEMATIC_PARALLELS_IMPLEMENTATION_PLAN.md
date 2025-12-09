# Thematic Parallels Librarian - Implementation Plan

**Feature**: RAG-based thematic parallel discovery for Tanakh passages
**Created**: 2025-12-09 (Session 183)
**Status**: Planning Complete → Ready for Implementation

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Directory Structure](#3-directory-structure)
4. [Phase 0: Environment Setup](#4-phase-0-environment-setup)
5. [Phase 1: Corpus Preparation](#5-phase-1-corpus-preparation)
6. [Phase 2: Embedding & Indexing](#6-phase-2-embedding--indexing)
7. [Phase 3: Retrieval Implementation](#7-phase-3-retrieval-implementation)
8. [Phase 4: Pipeline Integration](#8-phase-4-pipeline-integration)
9. [Phase 5: Testing & Validation](#9-phase-5-testing--validation)
10. [Session Management Protocol](#10-session-management-protocol)
11. [Appendix A: Data Schemas](#appendix-a-data-schemas)
12. [Appendix B: Test Cases](#appendix-b-test-cases)
13. [Appendix C: Troubleshooting](#appendix-c-troubleshooting)

---

## 1. Executive Summary

### Goal
Build a **Thematic Parallels Librarian** that finds passages in the Tanakh (outside Psalms) that are thematically similar to psalm verses being analyzed—even when they share no common vocabulary.

### Why This Matters
Current pipeline finds cross-references via:
- Concordance (lexical matches)
- Related Psalms (statistical linguistic overlap)
- Figurative database (shared metaphors)

**Gap**: None of these catch thematic resonance without lexical overlap.

Example: Psalm 139 "you knit me in my mother's womb" should surface Job 10:8-12 "Your hands shaped me and made me"—but they share no Hebrew roots.

### Approach
Use **vector embeddings** to capture semantic meaning. Passages with similar themes cluster together in embedding space, regardless of vocabulary.

### Key Design Decisions
1. **Chunk by Sefaria sections** (native literary units) with fallback to sliding windows
2. **Embed Hebrew + English together** for bilingual semantic capture
3. **Filter AFTER retrieval** against existing research bundle (not during)
4. **Testable from Day 1** with mock components and visual inspection tools

### Estimated Effort
- Phase 0 (Setup): 2 hours
- Phase 1 (Corpus): 4-6 hours
- Phase 2 (Embedding): 2-3 hours
- Phase 3 (Retrieval): 4-6 hours
- Phase 4 (Integration): 3-4 hours
- Phase 5 (Testing): 4-6 hours

**Total**: ~20-27 hours across multiple sessions

### Cost Estimate
- One-time embedding: ~$0.10-0.20
- Per-psalm retrieval: < $0.001
- Vector DB: Free (ChromaDB local)

---

## 2. Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     THEMATIC PARALLELS SYSTEM                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────┐     ┌─────────────────────┐                    │
│  │   CORPUS BUILDER    │     │   CHUNK INSPECTOR   │                    │
│  │   (One-Time Setup)  │     │   (Debug/QA Tool)   │                    │
│  └──────────┬──────────┘     └─────────────────────┘                    │
│             │                                                           │
│             ▼                                                           │
│  ┌─────────────────────────────────────────────────┐                    │
│  │              TANAKH CHUNK CORPUS                │                    │
│  │  ┌─────────────────────────────────────────┐   │                    │
│  │  │ data/thematic_corpus/                   │   │                    │
│  │  │   tanakh_chunks.jsonl     (text data)   │   │                    │
│  │  │   chunk_metadata.json     (stats)       │   │                    │
│  │  │   chroma_db/              (vectors)     │   │                    │
│  │  └─────────────────────────────────────────┘   │                    │
│  └─────────────────────────────────────────────────┘                    │
│                          │                                              │
│                          ▼                                              │
│  ┌─────────────────────────────────────────────────┐                    │
│  │         THEMATIC PARALLELS LIBRARIAN            │                    │
│  │  ┌─────────────────┐  ┌─────────────────────┐  │                    │
│  │  │ EmbeddingService│  │    VectorStore      │  │                    │
│  │  │  (Protocol)     │  │    (Protocol)       │  │                    │
│  │  │  - OpenAI       │  │    - ChromaDB       │  │                    │
│  │  │  - Mock         │  │    - InMemory       │  │                    │
│  │  └─────────────────┘  └─────────────────────┘  │                    │
│  └──────────────────────────┬──────────────────────┘                    │
│                             │                                           │
│                             ▼                                           │
│  ┌─────────────────────────────────────────────────┐                    │
│  │            RESEARCH ASSEMBLER                   │                    │
│  │  - Receives raw thematic parallels              │                    │
│  │  - Filters against existing bundle refs         │                    │
│  │  - Adds filtered results to ResearchBundle      │                    │
│  └─────────────────────────────────────────────────┘                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Implemented In |
|-----------|---------------|----------------|
| CorpusBuilder | Fetch Tanakh, chunk by book, save JSONL | `scripts/build_thematic_corpus.py` |
| ChunkInspector | View/search chunks for QA | `scripts/inspect_chunks.py` |
| EmbeddingService | Convert text → vectors | `src/thematic/embedding_service.py` |
| VectorStore | Store/search vectors | `src/thematic/vector_store.py` |
| ThematicParallelsLibrarian | Orchestrate retrieval | `src/agents/thematic_parallels_librarian.py` |
| ResearchAssembler | Filter & integrate | `src/agents/research_assembler.py` (modify) |

---

## 3. Directory Structure

### New Files to Create

```
C:\Users\ariro\OneDrive\Documents\Psalms\
├── data/
│   └── thematic_corpus/           # NEW: Corpus data
│       ├── tanakh_chunks.jsonl    # All chunks with text
│       ├── chunk_metadata.json    # Corpus statistics
│       └── chroma_db/             # Vector database
│           └── (ChromaDB files)
│
├── src/
│   ├── thematic/                  # NEW: Thematic parallels module
│   │   ├── __init__.py
│   │   ├── embedding_service.py   # Embedding abstraction
│   │   ├── vector_store.py        # Vector DB abstraction
│   │   ├── corpus_builder.py      # Chunking logic
│   │   └── chunk_schemas.py       # Pydantic models
│   │
│   └── agents/
│       ├── thematic_parallels_librarian.py  # NEW: Main librarian
│       └── research_assembler.py            # MODIFY: Add integration
│
├── scripts/
│   ├── build_thematic_corpus.py   # NEW: One-time corpus builder
│   ├── inspect_chunks.py          # NEW: QA/debug tool
│   └── test_thematic_retrieval.py # NEW: Manual testing script
│
├── tests/
│   └── thematic/                  # NEW: Test directory
│       ├── __init__.py
│       ├── test_corpus_builder.py
│       ├── test_embedding_service.py
│       ├── test_vector_store.py
│       ├── test_thematic_librarian.py
│       └── conftest.py            # Shared fixtures
│
└── docs/
    └── features/
        └── THEMATIC_PARALLELS_IMPLEMENTATION_PLAN.md  # This file
```

### Existing Files to Modify

| File | Modification |
|------|-------------|
| `src/agents/research_assembler.py` | Add ThematicParallelsLibrarian integration |
| `src/agents/__init__.py` | Export new librarian |
| `CLAUDE.md` | Add feature documentation |
| `docs/session_tracking/PROJECT_STATUS.md` | Update with progress |
| `requirements.txt` | Add chromadb, openai dependencies |

---

## 4. Phase 0: Environment Setup

### Duration: ~2 hours

### Step 0.1: Install Dependencies

```bash
# Activate virtual environment
cd C:\Users\ariro\OneDrive\Documents\Psalms
source venv/Scripts/activate  # Windows Git Bash

# Install new dependencies
pip install chromadb openai tiktoken

# Verify installations
python -c "import chromadb; print(f'ChromaDB {chromadb.__version__}')"
python -c "import openai; print(f'OpenAI {openai.__version__}')"
```

**Add to `requirements.txt`**:
```
chromadb>=0.4.0
openai>=1.0.0
tiktoken>=0.5.0
```

### Step 0.2: Create Directory Structure

```bash
# Create new directories
mkdir -p data/thematic_corpus
mkdir -p src/thematic
mkdir -p tests/thematic
```

### Step 0.3: Verify API Access

```python
# scripts/verify_openai_setup.py
"""Verify OpenAI API access for embeddings."""
import os
from openai import OpenAI

def verify_api():
    client = OpenAI()  # Uses OPENAI_API_KEY env var

    # Test embedding
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input="Test embedding for Psalms project"
    )

    embedding = response.data[0].embedding
    print(f"✓ OpenAI API working")
    print(f"✓ Embedding dimension: {len(embedding)}")
    print(f"✓ Model: text-embedding-3-large")

if __name__ == "__main__":
    verify_api()
```

**Run**: `python scripts/verify_openai_setup.py`

### Step 0.4: Create Module Init Files

```python
# src/thematic/__init__.py
"""Thematic parallels discovery module using RAG."""
from .embedding_service import EmbeddingService, OpenAIEmbeddings, MockEmbeddings
from .vector_store import VectorStore, ChromaVectorStore, InMemoryVectorStore
from .corpus_builder import CorpusBuilder
from .chunk_schemas import TanakhChunk, ChunkMetadata

__all__ = [
    "EmbeddingService",
    "OpenAIEmbeddings",
    "MockEmbeddings",
    "VectorStore",
    "ChromaVectorStore",
    "InMemoryVectorStore",
    "CorpusBuilder",
    "TanakhChunk",
    "ChunkMetadata",
]
```

### Checkpoint: Phase 0 Complete
- [ ] Dependencies installed
- [ ] Directories created
- [ ] OpenAI API verified
- [ ] Init files created

---

## 5. Phase 1: Corpus Preparation

### Duration: 4-6 hours

### Step 1.1: Define Data Schemas

```python
# src/thematic/chunk_schemas.py
"""Pydantic schemas for thematic corpus chunks."""
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
```

### Step 1.2: Implement Corpus Builder

```python
# src/thematic/corpus_builder.py
"""Build the Tanakh chunk corpus for thematic search."""
import json
import logging
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
        window_overlap: int = 2,
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
    ) -> ChunkMetadata:
        """
        Build the complete corpus.

        Args:
            exclude_psalms: Skip Psalms (we're finding parallels TO psalms)
            use_sefaria_sections: Try Sefaria sections first, fallback to windows

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
            book_chunks = self._chunk_book(book, use_sefaria_sections)
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
    ) -> List[TanakhChunk]:
        """
        Chunk a single book.

        Strategy:
        1. Try Sefaria sections if enabled
        2. For Psalms: one chunk per psalm (though usually excluded)
        3. For Proverbs: use collection boundaries
        4. Fallback: sliding window
        """
        verses = self._get_book_text(book)

        if not verses:
            logger.warning(f"No verses found for {book}")
            return []

        # Special handling by book
        if book == "Psalms":
            return self._chunk_psalms(verses)
        elif book == "Proverbs":
            return self._chunk_proverbs(verses)
        elif book == "Job":
            return self._chunk_job(verses)
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

        # Combine text
        hebrew_text = " ".join(v["hebrew"] for v in verses)
        english_text = " ".join(v["english"] for v in verses)

        # Estimate tokens (rough: 1 token per 4 chars for Hebrew, per 4 chars for English)
        token_estimate = (len(hebrew_text) + len(english_text)) // 4

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

    return ChunkMetadata(**data)
```

### Step 1.3: Create Corpus Build Script

```python
# scripts/build_thematic_corpus.py
"""
Build the Tanakh chunk corpus for thematic parallel search.

Usage:
    python scripts/build_thematic_corpus.py
    python scripts/build_thematic_corpus.py --inspect  # View sample chunks
"""
import argparse
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.thematic.corpus_builder import CorpusBuilder, load_corpus, load_metadata

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Build thematic corpus")
    parser.add_argument("--inspect", action="store_true", help="Inspect existing corpus")
    parser.add_argument("--book", type=str, help="Only process specific book")
    parser.add_argument("--sample", type=int, default=5, help="Number of sample chunks to show")
    args = parser.parse_args()

    # Paths
    project_root = Path(__file__).parent.parent
    tanakh_db = project_root / "database" / "tanakh.db"
    output_dir = project_root / "data" / "thematic_corpus"

    if args.inspect:
        # Inspect existing corpus
        logger.info("Inspecting existing corpus...")

        metadata = load_metadata(str(output_dir))
        print("\n" + "="*60)
        print("CORPUS METADATA")
        print("="*60)
        print(f"Total chunks: {metadata.total_chunks}")
        print(f"Average verses per chunk: {metadata.avg_verse_count}")
        print(f"Average tokens per chunk: {metadata.avg_token_estimate}")
        print(f"\nChunks by category:")
        for cat, count in sorted(metadata.chunks_by_category.items()):
            print(f"  {cat}: {count}")
        print(f"\nChunks by type:")
        for typ, count in sorted(metadata.chunks_by_type.items()):
            print(f"  {typ}: {count}")

        print("\n" + "="*60)
        print(f"SAMPLE CHUNKS (first {args.sample})")
        print("="*60)

        for i, chunk in enumerate(load_corpus(str(output_dir))):
            if i >= args.sample:
                break
            print(f"\n--- Chunk {i+1}: {chunk.reference} ---")
            print(f"Type: {chunk.chunk_type.value}")
            print(f"Verses: {chunk.verse_count}")
            print(f"Hebrew (first 100 chars): {chunk.hebrew_text[:100]}...")
            print(f"English (first 100 chars): {chunk.english_text[:100]}...")

        return

    # Build corpus
    logger.info("Building thematic corpus...")
    logger.info(f"Database: {tanakh_db}")
    logger.info(f"Output: {output_dir}")

    builder = CorpusBuilder(
        tanakh_db_path=str(tanakh_db),
        output_dir=str(output_dir),
        window_size=5,
        window_overlap=2,
    )

    metadata = builder.build_corpus(
        exclude_psalms=True,
        use_sefaria_sections=True,
    )

    print("\n" + "="*60)
    print("BUILD COMPLETE")
    print("="*60)
    print(f"Total chunks: {metadata.total_chunks}")
    print(f"Output directory: {output_dir}")
    print("\nRun with --inspect to view sample chunks")


if __name__ == "__main__":
    main()
```

### Step 1.4: Create Chunk Inspector Tool

```python
# scripts/inspect_chunks.py
"""
Interactive tool to inspect and search the chunk corpus.

Usage:
    python scripts/inspect_chunks.py                    # Interactive mode
    python scripts/inspect_chunks.py --book Genesis     # Filter by book
    python scripts/inspect_chunks.py --search "shepherd" # Search chunks
    python scripts/inspect_chunks.py --ref "Genesis 22" # Find specific ref
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.thematic.corpus_builder import load_corpus, load_metadata


def main():
    parser = argparse.ArgumentParser(description="Inspect chunk corpus")
    parser.add_argument("--book", type=str, help="Filter by book name")
    parser.add_argument("--search", type=str, help="Search in chunk text")
    parser.add_argument("--ref", type=str, help="Find chunks containing reference")
    parser.add_argument("--limit", type=int, default=10, help="Max results to show")
    parser.add_argument("--full", action="store_true", help="Show full text (not truncated)")
    args = parser.parse_args()

    corpus_dir = Path(__file__).parent.parent / "data" / "thematic_corpus"

    # Load and filter chunks
    results = []
    for chunk in load_corpus(str(corpus_dir)):
        # Apply filters
        if args.book and chunk.book.lower() != args.book.lower():
            continue

        if args.search:
            search_lower = args.search.lower()
            if (search_lower not in chunk.hebrew_text.lower() and
                search_lower not in chunk.english_text.lower()):
                continue

        if args.ref:
            if args.ref.lower() not in chunk.reference.lower():
                continue

        results.append(chunk)

        if len(results) >= args.limit:
            break

    # Display results
    print(f"\nFound {len(results)} chunks" + (f" (limited to {args.limit})" if len(results) == args.limit else ""))
    print("="*70)

    for chunk in results:
        print(f"\n📖 {chunk.reference}")
        print(f"   Book: {chunk.book} ({chunk.book_category.value})")
        print(f"   Type: {chunk.chunk_type.value}")
        print(f"   Verses: {chunk.verse_count}, Tokens: ~{chunk.token_estimate}")

        if args.full:
            print(f"\n   Hebrew:\n   {chunk.hebrew_text}")
            print(f"\n   English:\n   {chunk.english_text}")
        else:
            print(f"   Hebrew: {chunk.hebrew_text[:80]}...")
            print(f"   English: {chunk.english_text[:80]}...")

        print("-"*70)


if __name__ == "__main__":
    main()
```

### Checkpoint: Phase 1 Complete
- [ ] Schemas defined (`chunk_schemas.py`)
- [ ] CorpusBuilder implemented (`corpus_builder.py`)
- [ ] Build script working (`build_thematic_corpus.py`)
- [ ] Inspect script working (`inspect_chunks.py`)
- [ ] `tanakh_chunks.jsonl` generated
- [ ] `chunk_metadata.json` generated
- [ ] **VISUAL INSPECTION**: Review 20+ chunks across different books to verify quality

---

## 6. Phase 2: Embedding & Indexing

### Duration: 2-3 hours

### Step 2.1: Implement Embedding Service

```python
# src/thematic/embedding_service.py
"""Embedding service abstraction for testability."""
from abc import ABC, abstractmethod
from typing import List, Protocol
import hashlib
import logging

logger = logging.getLogger(__name__)


class EmbeddingService(Protocol):
    """Protocol for embedding services."""

    def embed(self, text: str) -> List[float]:
        """Embed a single text."""
        ...

    def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Embed multiple texts."""
        ...

    @property
    def dimension(self) -> int:
        """Embedding dimension."""
        ...


class OpenAIEmbeddings:
    """OpenAI embedding service using text-embedding-3-large."""

    def __init__(self, model: str = "text-embedding-3-large"):
        from openai import OpenAI
        self.client = OpenAI()
        self.model = model
        self._dimension = 3072 if "large" in model else 1536

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, text: str) -> List[float]:
        """Embed a single text."""
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding

    def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Embed multiple texts in batches."""
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Embedding batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")

            response = self.client.embeddings.create(
                model=self.model,
                input=batch
            )

            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)

        return embeddings


class MockEmbeddings:
    """
    Mock embedding service for testing.

    Generates deterministic embeddings based on text hash.
    Texts with similar words will NOT have similar embeddings
    (this is for testing structure, not semantic similarity).
    """

    def __init__(self, dimension: int = 3072):
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, text: str) -> List[float]:
        """Generate deterministic embedding from text hash."""
        # Use hash to generate deterministic "random" values
        hash_bytes = hashlib.sha256(text.encode()).digest()

        # Expand hash to fill dimension
        embedding = []
        for i in range(self._dimension):
            # Cycle through hash bytes
            byte_val = hash_bytes[i % len(hash_bytes)]
            # Normalize to [-1, 1]
            embedding.append((byte_val / 127.5) - 1.0)

        return embedding

    def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Embed multiple texts."""
        return [self.embed(text) for text in texts]


class SemanticMockEmbeddings:
    """
    Mock embeddings with basic semantic similarity for testing.

    Texts containing the same words will have more similar embeddings.
    """

    def __init__(self, dimension: int = 3072):
        self._dimension = dimension
        self._word_vectors: dict = {}

    @property
    def dimension(self) -> int:
        return self._dimension

    def _get_word_vector(self, word: str) -> List[float]:
        """Get or create a vector for a word."""
        if word not in self._word_vectors:
            # Generate deterministic vector for word
            hash_bytes = hashlib.sha256(word.encode()).digest()
            vector = []
            for i in range(self._dimension):
                byte_val = hash_bytes[i % len(hash_bytes)]
                vector.append((byte_val / 127.5) - 1.0)
            self._word_vectors[word] = vector
        return self._word_vectors[word]

    def embed(self, text: str) -> List[float]:
        """Generate embedding as average of word vectors."""
        words = text.lower().split()
        if not words:
            return [0.0] * self._dimension

        # Average word vectors
        result = [0.0] * self._dimension
        for word in words:
            word_vec = self._get_word_vector(word)
            for i in range(self._dimension):
                result[i] += word_vec[i]

        # Normalize
        for i in range(self._dimension):
            result[i] /= len(words)

        return result

    def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        return [self.embed(text) for text in texts]
```

### Step 2.2: Implement Vector Store

```python
# src/thematic/vector_store.py
"""Vector store abstraction for testability."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Protocol
from pathlib import Path
import logging
import math

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Result from vector search."""
    chunk_id: str
    score: float  # Similarity score (higher = more similar)
    metadata: Dict[str, Any]


class VectorStore(Protocol):
    """Protocol for vector stores."""

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """Add vectors to the store."""
        ...

    def search(
        self,
        query_embedding: List[float],
        k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar vectors."""
        ...

    def count(self) -> int:
        """Return number of vectors in store."""
        ...


class ChromaVectorStore:
    """ChromaDB-backed vector store."""

    def __init__(
        self,
        persist_directory: str,
        collection_name: str = "tanakh_chunks",
    ):
        import chromadb
        from chromadb.config import Settings

        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )

        logger.info(f"ChromaDB initialized at {self.persist_directory}")
        logger.info(f"Collection '{collection_name}' has {self.count()} vectors")

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """Add vectors to ChromaDB."""
        # ChromaDB has batch limits, chunk if needed
        batch_size = 5000

        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]

            self.collection.add(
                ids=batch_ids,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas,
            )

            logger.info(f"Added batch {i//batch_size + 1}: {len(batch_ids)} vectors")

    def search(
        self,
        query_embedding: List[float],
        k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar vectors."""
        # Convert filter to ChromaDB where clause
        where = None
        if filter:
            where = filter

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where,
            include=["metadatas", "distances"],
        )

        # Convert to SearchResult objects
        search_results = []

        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                # ChromaDB returns distance, convert to similarity
                # For cosine, similarity = 1 - distance
                distance = results["distances"][0][i] if results["distances"] else 0
                similarity = 1 - distance

                metadata = results["metadatas"][0][i] if results["metadatas"] else {}

                search_results.append(SearchResult(
                    chunk_id=chunk_id,
                    score=similarity,
                    metadata=metadata,
                ))

        return search_results

    def count(self) -> int:
        """Return number of vectors."""
        return self.collection.count()

    def clear(self) -> None:
        """Clear all vectors (for testing)."""
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name,
            metadata={"hnsw:space": "cosine"}
        )


class InMemoryVectorStore:
    """
    In-memory vector store for testing.

    Uses brute-force cosine similarity search.
    """

    def __init__(self):
        self.vectors: List[Dict[str, Any]] = []

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """Add vectors to memory."""
        for i in range(len(ids)):
            self.vectors.append({
                "id": ids[i],
                "embedding": embeddings[i],
                "metadata": metadatas[i],
            })

    def search(
        self,
        query_embedding: List[float],
        k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search using brute-force cosine similarity."""
        scored = []

        for item in self.vectors:
            # Apply filter
            if filter:
                match = True
                for key, value in filter.items():
                    if key.startswith("$"):
                        # Handle special operators
                        if key == "$ne":
                            # This is wrong - need to handle nested
                            pass
                    elif item["metadata"].get(key) != value:
                        match = False
                        break
                if not match:
                    continue

            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, item["embedding"])
            scored.append((item, similarity))

        # Sort by similarity (descending)
        scored.sort(key=lambda x: x[1], reverse=True)

        # Return top k
        results = []
        for item, score in scored[:k]:
            results.append(SearchResult(
                chunk_id=item["id"],
                score=score,
                metadata=item["metadata"],
            ))

        return results

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def count(self) -> int:
        return len(self.vectors)

    def clear(self) -> None:
        self.vectors = []
```

### Step 2.3: Create Index Building Script

```python
# scripts/build_vector_index.py
"""
Build the vector index from the chunk corpus.

Usage:
    python scripts/build_vector_index.py
    python scripts/build_vector_index.py --dry-run  # Estimate cost without embedding
"""
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.thematic.corpus_builder import load_corpus, load_metadata
from src.thematic.embedding_service import OpenAIEmbeddings
from src.thematic.vector_store import ChromaVectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def estimate_cost(corpus_dir: str) -> dict:
    """Estimate embedding cost without making API calls."""
    metadata = load_metadata(corpus_dir)

    # text-embedding-3-large: $0.13 per 1M tokens
    total_tokens = metadata.total_chunks * metadata.avg_token_estimate
    cost = (total_tokens / 1_000_000) * 0.13

    return {
        "total_chunks": metadata.total_chunks,
        "avg_tokens_per_chunk": metadata.avg_token_estimate,
        "estimated_total_tokens": total_tokens,
        "estimated_cost_usd": round(cost, 4),
    }


def main():
    parser = argparse.ArgumentParser(description="Build vector index")
    parser.add_argument("--dry-run", action="store_true", help="Estimate cost only")
    parser.add_argument("--batch-size", type=int, default=100, help="Embedding batch size")
    args = parser.parse_args()

    # Paths
    project_root = Path(__file__).parent.parent
    corpus_dir = project_root / "data" / "thematic_corpus"
    vector_db_dir = corpus_dir / "chroma_db"

    if args.dry_run:
        print("\n" + "="*60)
        print("DRY RUN - Cost Estimate")
        print("="*60)

        estimate = estimate_cost(str(corpus_dir))
        print(f"Total chunks: {estimate['total_chunks']}")
        print(f"Avg tokens/chunk: {estimate['avg_tokens_per_chunk']}")
        print(f"Estimated total tokens: {estimate['estimated_total_tokens']:,.0f}")
        print(f"Estimated cost: ${estimate['estimated_cost_usd']}")
        print("\nRun without --dry-run to build index")
        return

    # Initialize services
    logger.info("Initializing embedding service...")
    embedder = OpenAIEmbeddings(model="text-embedding-3-large")

    logger.info("Initializing vector store...")
    vector_store = ChromaVectorStore(
        persist_directory=str(vector_db_dir),
        collection_name="tanakh_chunks",
    )

    # Check if already indexed
    existing_count = vector_store.count()
    if existing_count > 0:
        response = input(f"Vector store already has {existing_count} vectors. Clear and rebuild? [y/N]: ")
        if response.lower() != 'y':
            print("Aborted.")
            return
        vector_store.clear()

    # Load chunks
    logger.info("Loading corpus...")
    chunks = list(load_corpus(str(corpus_dir)))
    logger.info(f"Loaded {len(chunks)} chunks")

    # Prepare for embedding
    texts = [chunk.embedding_text() for chunk in chunks]
    ids = [chunk.chunk_id for chunk in chunks]
    metadatas = [
        {
            "reference": chunk.reference,
            "book": chunk.book,
            "book_category": chunk.book_category.value,
            "chunk_type": chunk.chunk_type.value,
            "verse_count": chunk.verse_count,
            "start_chapter": chunk.start_chapter,
            "start_verse": chunk.start_verse,
            "end_chapter": chunk.end_chapter,
            "end_verse": chunk.end_verse,
        }
        for chunk in chunks
    ]

    # Embed
    logger.info("Generating embeddings (this may take a few minutes)...")
    embeddings = embedder.embed_batch(texts, batch_size=args.batch_size)

    # Store
    logger.info("Storing vectors...")
    vector_store.add(ids=ids, embeddings=embeddings, metadatas=metadatas)

    print("\n" + "="*60)
    print("INDEX BUILD COMPLETE")
    print("="*60)
    print(f"Vectors indexed: {vector_store.count()}")
    print(f"Vector DB location: {vector_db_dir}")


if __name__ == "__main__":
    main()
```

### Checkpoint: Phase 2 Complete
- [ ] EmbeddingService implemented with OpenAI and Mock variants
- [ ] VectorStore implemented with ChromaDB and InMemory variants
- [ ] Index build script working
- [ ] Dry-run cost estimate accurate
- [ ] Vectors successfully indexed in ChromaDB
- [ ] **VERIFICATION**: Run test search to confirm vectors are retrievable

---

## 7. Phase 3: Retrieval Implementation

### Duration: 4-6 hours

### Step 3.1: Implement Thematic Parallels Librarian

```python
# src/agents/thematic_parallels_librarian.py
"""
Thematic Parallels Librarian - finds thematically similar passages using RAG.

This librarian uses vector embeddings to find passages in the Tanakh that are
thematically similar to psalm verses, even when they share no common vocabulary.
"""
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Protocol
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ThematicParallel:
    """A thematically similar passage found via RAG."""

    reference: str              # "Job 10:8-12"
    hebrew_text: str            # Full Hebrew text
    english_text: str           # Full English translation
    similarity_score: float     # 0.0-1.0 (cosine similarity)
    source_verse: int           # Which psalm verse triggered this match
    book: str                   # "Job"
    book_category: str          # "Writings"
    chunk_type: str             # "speaker_turn"
    verse_count: int            # Number of verses in chunk

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reference": self.reference,
            "hebrew_text": self.hebrew_text,
            "english_text": self.english_text,
            "similarity_score": self.similarity_score,
            "source_verse": self.source_verse,
            "book": self.book,
            "book_category": self.book_category,
            "chunk_type": self.chunk_type,
            "verse_count": self.verse_count,
        }


@dataclass
class VerseText:
    """Verse text for embedding."""
    number: int
    hebrew: str
    english: str


class ThematicParallelsLibrarian:
    """
    Finds thematically similar passages in the Tanakh using vector similarity.

    Key design decisions:
    1. Searches the entire Tanakh (except Psalms) for each verse
    2. Returns raw results WITHOUT filtering against research bundle
       (filtering happens in ResearchAssembler)
    3. Deduplicates by reference (same passage may match multiple verses)
    4. Configurable similarity thresholds and result limits
    """

    def __init__(
        self,
        embedding_service,  # EmbeddingService protocol
        vector_store,       # VectorStore protocol
        chunk_corpus_path: Optional[str] = None,  # For loading full text
        min_similarity: float = 0.3,
        default_k_per_verse: int = 5,
        default_max_total: int = 20,
    ):
        """
        Initialize the librarian.

        Args:
            embedding_service: Service for generating embeddings
            vector_store: Vector database for similarity search
            chunk_corpus_path: Path to tanakh_chunks.jsonl for full text retrieval
            min_similarity: Minimum similarity score to include (0.0-1.0)
            default_k_per_verse: Default number of results per verse
            default_max_total: Default maximum total results
        """
        self.embedder = embedding_service
        self.store = vector_store
        self.chunk_corpus_path = chunk_corpus_path
        self.min_similarity = min_similarity
        self.default_k_per_verse = default_k_per_verse
        self.default_max_total = default_max_total

        # Cache for chunk full text (loaded lazily)
        self._chunk_text_cache: Optional[Dict[str, Dict[str, str]]] = None

    def _load_chunk_text_cache(self) -> Dict[str, Dict[str, str]]:
        """Load full text for all chunks (lazy, cached)."""
        if self._chunk_text_cache is not None:
            return self._chunk_text_cache

        if not self.chunk_corpus_path:
            logger.warning("No chunk corpus path provided, returning empty cache")
            return {}

        import json

        cache = {}
        corpus_path = Path(self.chunk_corpus_path)

        if corpus_path.exists():
            with open(corpus_path, "r", encoding="utf-8") as f:
                for line in f:
                    chunk = json.loads(line)
                    cache[chunk["chunk_id"]] = {
                        "hebrew_text": chunk["hebrew_text"],
                        "english_text": chunk["english_text"],
                    }

        self._chunk_text_cache = cache
        logger.info(f"Loaded text cache for {len(cache)} chunks")
        return cache

    def find_parallels(
        self,
        psalm_chapter: int,
        psalm_verses: List[VerseText],
        k_per_verse: Optional[int] = None,
        max_total: Optional[int] = None,
        exclude_books: Optional[List[str]] = None,
    ) -> List[ThematicParallel]:
        """
        Find thematic parallels for a psalm.

        Args:
            psalm_chapter: The psalm being analyzed
            psalm_verses: List of verses with Hebrew and English text
            k_per_verse: Number of results to fetch per verse
            max_total: Maximum total results to return
            exclude_books: Books to exclude (default: ["Psalms"])

        Returns:
            List of ThematicParallel objects, sorted by similarity (descending)
        """
        if k_per_verse is None:
            k_per_verse = self.default_k_per_verse
        if max_total is None:
            max_total = self.default_max_total
        if exclude_books is None:
            exclude_books = ["Psalms"]

        logger.info(f"Finding thematic parallels for Psalm {psalm_chapter} ({len(psalm_verses)} verses)")

        all_parallels: List[ThematicParallel] = []
        seen_refs: Set[str] = set()

        for verse in psalm_verses:
            # Create embedding text (Hebrew + English)
            query_text = f"{verse.hebrew}\n{verse.english}"

            # Generate embedding
            query_embedding = self.embedder.embed(query_text)

            # Search vector store
            # Note: ChromaDB filter syntax
            filter_clause = {"book": {"$nin": exclude_books}} if exclude_books else None

            results = self.store.search(
                query_embedding=query_embedding,
                k=k_per_verse * 2,  # Fetch extra for deduplication
                filter=filter_clause,
            )

            # Convert to ThematicParallel objects
            for result in results:
                # Skip if below threshold
                if result.score < self.min_similarity:
                    continue

                # Skip duplicates
                ref = result.metadata.get("reference", result.chunk_id)
                if ref in seen_refs:
                    continue
                seen_refs.add(ref)

                # Get full text from cache
                text_cache = self._load_chunk_text_cache()
                chunk_text = text_cache.get(result.chunk_id, {})

                parallel = ThematicParallel(
                    reference=ref,
                    hebrew_text=chunk_text.get("hebrew_text", ""),
                    english_text=chunk_text.get("english_text", ""),
                    similarity_score=result.score,
                    source_verse=verse.number,
                    book=result.metadata.get("book", ""),
                    book_category=result.metadata.get("book_category", ""),
                    chunk_type=result.metadata.get("chunk_type", ""),
                    verse_count=result.metadata.get("verse_count", 0),
                )

                all_parallels.append(parallel)

        # Sort by similarity and limit
        all_parallels.sort(key=lambda p: p.similarity_score, reverse=True)
        limited = all_parallels[:max_total]

        logger.info(f"Found {len(all_parallels)} parallels, returning top {len(limited)}")

        return limited

    def find_parallels_for_text(
        self,
        text: str,
        k: int = 10,
        exclude_books: Optional[List[str]] = None,
    ) -> List[ThematicParallel]:
        """
        Find parallels for arbitrary text (useful for testing).

        Args:
            text: Text to find parallels for
            k: Number of results
            exclude_books: Books to exclude

        Returns:
            List of ThematicParallel objects
        """
        if exclude_books is None:
            exclude_books = ["Psalms"]

        query_embedding = self.embedder.embed(text)

        filter_clause = {"book": {"$nin": exclude_books}} if exclude_books else None

        results = self.store.search(
            query_embedding=query_embedding,
            k=k,
            filter=filter_clause,
        )

        parallels = []
        text_cache = self._load_chunk_text_cache()

        for result in results:
            if result.score < self.min_similarity:
                continue

            chunk_text = text_cache.get(result.chunk_id, {})

            parallel = ThematicParallel(
                reference=result.metadata.get("reference", result.chunk_id),
                hebrew_text=chunk_text.get("hebrew_text", ""),
                english_text=chunk_text.get("english_text", ""),
                similarity_score=result.score,
                source_verse=0,
                book=result.metadata.get("book", ""),
                book_category=result.metadata.get("book_category", ""),
                chunk_type=result.metadata.get("chunk_type", ""),
                verse_count=result.metadata.get("verse_count", 0),
            )
            parallels.append(parallel)

        return parallels

    def format_as_markdown(
        self,
        parallels: List[ThematicParallel],
        max_text_length: int = 500,
    ) -> str:
        """
        Format parallels as markdown for research bundle.

        Args:
            parallels: List of ThematicParallel objects
            max_text_length: Max characters for Hebrew/English text

        Returns:
            Markdown-formatted string
        """
        if not parallels:
            return "## Thematic Parallels\n\nNo thematic parallels found.\n"

        lines = [
            "## Thematic Parallels (Non-Lexical)",
            "",
            f"*Found {len(parallels)} thematically similar passages outside Psalms.*",
            "",
        ]

        for i, p in enumerate(parallels, 1):
            lines.append(f"### {i}. {p.reference}")
            lines.append(f"**Book**: {p.book} ({p.book_category})")
            lines.append(f"**Similarity**: {p.similarity_score:.2%}")
            lines.append(f"**Matched psalm verse**: {p.source_verse}")
            lines.append("")

            # Truncate long text
            hebrew = p.hebrew_text
            if len(hebrew) > max_text_length:
                hebrew = hebrew[:max_text_length] + "..."

            english = p.english_text
            if len(english) > max_text_length:
                english = english[:max_text_length] + "..."

            lines.append(f"**Hebrew**: {hebrew}")
            lines.append("")
            lines.append(f"**English**: {english}")
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)


# Factory function for easy instantiation
def create_thematic_librarian(
    corpus_dir: Optional[str] = None,
    use_mock: bool = False,
) -> ThematicParallelsLibrarian:
    """
    Create a ThematicParallelsLibrarian with default configuration.

    Args:
        corpus_dir: Path to corpus directory (default: data/thematic_corpus)
        use_mock: Use mock embeddings/store for testing

    Returns:
        Configured ThematicParallelsLibrarian
    """
    from pathlib import Path

    if corpus_dir is None:
        # Default path relative to project root
        project_root = Path(__file__).parent.parent.parent
        corpus_dir = str(project_root / "data" / "thematic_corpus")

    corpus_path = Path(corpus_dir)

    if use_mock:
        from src.thematic.embedding_service import MockEmbeddings
        from src.thematic.vector_store import InMemoryVectorStore

        return ThematicParallelsLibrarian(
            embedding_service=MockEmbeddings(),
            vector_store=InMemoryVectorStore(),
            chunk_corpus_path=str(corpus_path / "tanakh_chunks.jsonl"),
        )
    else:
        from src.thematic.embedding_service import OpenAIEmbeddings
        from src.thematic.vector_store import ChromaVectorStore

        return ThematicParallelsLibrarian(
            embedding_service=OpenAIEmbeddings(),
            vector_store=ChromaVectorStore(
                persist_directory=str(corpus_path / "chroma_db"),
            ),
            chunk_corpus_path=str(corpus_path / "tanakh_chunks.jsonl"),
        )
```

### Step 3.2: Create Manual Test Script

```python
# scripts/test_thematic_retrieval.py
"""
Manual testing script for thematic parallels retrieval.

Usage:
    python scripts/test_thematic_retrieval.py                    # Interactive
    python scripts/test_thematic_retrieval.py --psalm 23         # Test specific psalm
    python scripts/test_thematic_retrieval.py --text "shepherd"  # Search by text
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.thematic_parallels_librarian import (
    ThematicParallelsLibrarian,
    VerseText,
    create_thematic_librarian,
)


def test_with_psalm(psalm_num: int, librarian: ThematicParallelsLibrarian):
    """Test retrieval for a specific psalm."""
    import sqlite3

    # Load psalm text from database
    db_path = Path(__file__).parent.parent / "database" / "tanakh.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT verse, hebrew, english
        FROM verses
        WHERE book_name = 'Psalms' AND chapter = ?
        ORDER BY verse
    """, (psalm_num,))

    verses = [
        VerseText(number=row[0], hebrew=row[1], english=row[2])
        for row in cursor.fetchall()
    ]
    conn.close()

    if not verses:
        print(f"Psalm {psalm_num} not found in database")
        return

    print(f"\n{'='*70}")
    print(f"TESTING PSALM {psalm_num} ({len(verses)} verses)")
    print('='*70)

    # Find parallels
    parallels = librarian.find_parallels(
        psalm_chapter=psalm_num,
        psalm_verses=verses,
        k_per_verse=3,
        max_total=15,
    )

    # Display results
    print(f"\nFound {len(parallels)} thematic parallels:\n")

    for i, p in enumerate(parallels, 1):
        print(f"{i}. {p.reference} (similarity: {p.similarity_score:.2%})")
        print(f"   Book: {p.book} ({p.book_category})")
        print(f"   Matched verse: {p.source_verse}")
        print(f"   English: {p.english_text[:100]}...")
        print()


def test_with_text(text: str, librarian: ThematicParallelsLibrarian):
    """Test retrieval for arbitrary text."""
    print(f"\n{'='*70}")
    print(f"SEARCHING FOR: {text}")
    print('='*70)

    parallels = librarian.find_parallels_for_text(text, k=10)

    print(f"\nFound {len(parallels)} thematic parallels:\n")

    for i, p in enumerate(parallels, 1):
        print(f"{i}. {p.reference} (similarity: {p.similarity_score:.2%})")
        print(f"   Book: {p.book}")
        print(f"   English: {p.english_text[:150]}...")
        print()


def main():
    parser = argparse.ArgumentParser(description="Test thematic retrieval")
    parser.add_argument("--psalm", type=int, help="Test with specific psalm")
    parser.add_argument("--text", type=str, help="Search for specific text")
    parser.add_argument("--mock", action="store_true", help="Use mock services")
    args = parser.parse_args()

    # Create librarian
    print("Initializing thematic parallels librarian...")
    librarian = create_thematic_librarian(use_mock=args.mock)
    print(f"Vector store has {librarian.store.count()} vectors")

    if args.psalm:
        test_with_psalm(args.psalm, librarian)
    elif args.text:
        test_with_text(args.text, librarian)
    else:
        # Interactive mode
        print("\nInteractive mode. Enter psalm number or text to search.")
        print("Type 'quit' to exit.\n")

        while True:
            query = input("Search (psalm number or text): ").strip()

            if query.lower() == 'quit':
                break

            try:
                psalm_num = int(query)
                test_with_psalm(psalm_num, librarian)
            except ValueError:
                test_with_text(query, librarian)


if __name__ == "__main__":
    main()
```

### Checkpoint: Phase 3 Complete
- [ ] ThematicParallelsLibrarian implemented
- [ ] Factory function working
- [ ] Manual test script working
- [ ] **VISUAL INSPECTION**: Run test with Psalms 23, 139, 73 and verify results are sensible

---

## 8. Phase 4: Pipeline Integration

### Duration: 3-4 hours

### Step 4.1: Add to ResearchAssembler

Modify `src/agents/research_assembler.py` to integrate thematic parallels:

```python
# Add to imports at top of research_assembler.py
from src.agents.thematic_parallels_librarian import (
    ThematicParallelsLibrarian,
    ThematicParallel,
    VerseText,
    create_thematic_librarian,
)

# Add to ResearchBundle dataclass (around line 92-149)
@dataclass
class ResearchBundle:
    # ... existing fields ...

    # NEW: Thematic parallels
    thematic_parallels: Optional[List[ThematicParallel]] = None
    thematic_parallels_markdown: Optional[str] = None

# Add to ResearchAssembler.__init__ (create librarian)
class ResearchAssembler:
    def __init__(self, ...):
        # ... existing initialization ...

        # Initialize thematic parallels librarian
        try:
            self.thematic_librarian = create_thematic_librarian()
            logger.info("Thematic parallels librarian initialized")
        except Exception as e:
            logger.warning(f"Could not initialize thematic librarian: {e}")
            self.thematic_librarian = None

# Add method to collect all references from bundle
def _collect_all_references(self, bundle: ResearchBundle) -> Set[str]:
    """Collect all verse references already in the bundle."""
    refs = set()

    # From concordance results
    if bundle.concordance_bundles:
        for cb in bundle.concordance_bundles:
            if cb.results:
                for result in cb.results:
                    refs.add(result.reference)

    # From figurative results
    if bundle.figurative_bundles:
        for fb in bundle.figurative_bundles:
            if fb.instances:
                for inst in fb.instances:
                    refs.add(inst.reference)

    # From commentary results
    if bundle.commentary_bundles:
        for cb in bundle.commentary_bundles:
            refs.add(f"Psalms {cb.chapter}:{cb.verse}")

    # From related psalms
    if bundle.related_psalms:
        for rp in bundle.related_psalms:
            # Add individual verse references if available
            pass

    return refs

# Add method to filter thematic parallels
def _filter_thematic_parallels(
    self,
    parallels: List[ThematicParallel],
    existing_refs: Set[str],
) -> List[ThematicParallel]:
    """
    Filter thematic parallels against existing bundle content.

    Removes parallels that overlap with references already in the bundle
    (from concordance, figurative, etc.).
    """
    filtered = []

    for parallel in parallels:
        # Check if this reference overlaps with existing
        overlaps = self._reference_overlaps(parallel.reference, existing_refs)

        if not overlaps:
            filtered.append(parallel)
        else:
            logger.debug(f"Filtering thematic parallel {parallel.reference} (already in bundle)")

    return filtered

def _reference_overlaps(self, ref: str, existing_refs: Set[str]) -> bool:
    """Check if reference overlaps with any existing reference."""
    # Simple string containment check
    # Could be enhanced with verse-range parsing
    ref_lower = ref.lower()

    for existing in existing_refs:
        existing_lower = existing.lower()

        # Check for overlap (simplified)
        if ref_lower in existing_lower or existing_lower in ref_lower:
            return True

        # Check book+chapter overlap
        # e.g., "Job 10:8-12" overlaps with "Job 10:10"
        try:
            ref_book = ref.split()[0]
            existing_book = existing.split()[0]

            if ref_book == existing_book:
                # Same book - check chapter
                ref_chapter = ref.split()[1].split(":")[0]
                existing_chapter = existing.split()[1].split(":")[0] if ":" in existing else ""

                if ref_chapter == existing_chapter:
                    return True
        except (IndexError, ValueError):
            pass

    return False

# Add to assemble() method (around line 631-783)
def assemble(self, request: ResearchRequest) -> ResearchBundle:
    # ... existing assembly code ...

    # After all other librarians, fetch thematic parallels
    thematic_parallels = None
    thematic_markdown = None

    if self.thematic_librarian:
        try:
            # Convert psalm verses to VerseText format
            psalm_verses = [
                VerseText(
                    number=v.verse,
                    hebrew=v.hebrew,
                    english=v.english,
                )
                for v in self._get_psalm_verses(request.psalm_chapter)
            ]

            # Get raw parallels
            raw_parallels = self.thematic_librarian.find_parallels(
                psalm_chapter=request.psalm_chapter,
                psalm_verses=psalm_verses,
                k_per_verse=3,
                max_total=20,
            )

            # Collect existing references from bundle
            existing_refs = self._collect_all_references(bundle)

            # Filter against existing content
            thematic_parallels = self._filter_thematic_parallels(
                raw_parallels,
                existing_refs,
            )

            # Format as markdown
            thematic_markdown = self.thematic_librarian.format_as_markdown(
                thematic_parallels
            )

            logger.info(f"Thematic parallels: {len(raw_parallels)} raw, {len(thematic_parallels)} after filtering")

        except Exception as e:
            logger.error(f"Error fetching thematic parallels: {e}")

    # Add to bundle
    bundle.thematic_parallels = thematic_parallels
    bundle.thematic_parallels_markdown = thematic_markdown

    return bundle

# Add to to_markdown() method
def to_markdown(self) -> str:
    # ... existing markdown generation ...

    # Add thematic parallels section
    if self.thematic_parallels_markdown:
        sections.append(self.thematic_parallels_markdown)

    return "\n\n".join(sections)
```

### Step 4.2: Update Pipeline Statistics

Add thematic parallels tracking to pipeline summary:

```python
# In src/utils/pipeline_summary.py

# Add field to track thematic parallels count
# In the statistics tracking
```

### Checkpoint: Phase 4 Complete
- [ ] ResearchBundle updated with thematic_parallels field
- [ ] ResearchAssembler fetches and filters parallels
- [ ] Markdown formatting integrated
- [ ] Pipeline statistics track thematic parallels
- [ ] **INTEGRATION TEST**: Run full pipeline on one psalm, verify thematic parallels appear in bundle

---

## 9. Phase 5: Testing & Validation

### Duration: 4-6 hours

### Step 5.1: Unit Tests

```python
# tests/thematic/conftest.py
"""Shared fixtures for thematic tests."""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.thematic.embedding_service import MockEmbeddings, SemanticMockEmbeddings
from src.thematic.vector_store import InMemoryVectorStore
from src.thematic.chunk_schemas import TanakhChunk, BookCategory, ChunkType


@pytest.fixture
def mock_embedder():
    """Simple mock embedder."""
    return MockEmbeddings(dimension=128)


@pytest.fixture
def semantic_embedder():
    """Mock embedder with basic semantic similarity."""
    return SemanticMockEmbeddings(dimension=128)


@pytest.fixture
def memory_store():
    """In-memory vector store."""
    return InMemoryVectorStore()


@pytest.fixture
def sample_chunks():
    """Sample chunks for testing."""
    return [
        TanakhChunk(
            chunk_id="genesis_001_001_001_005",
            reference="Genesis 1:1-5",
            book="Genesis",
            book_category=BookCategory.TORAH,
            start_chapter=1, start_verse=1,
            end_chapter=1, end_verse=5,
            hebrew_text="בְּרֵאשִׁית בָּרָא אֱלֹהִים",
            english_text="In the beginning God created",
            chunk_type=ChunkType.SLIDING_WINDOW,
            verse_count=5,
            token_estimate=100,
        ),
        TanakhChunk(
            chunk_id="job_010_008_010_012",
            reference="Job 10:8-12",
            book="Job",
            book_category=BookCategory.WRITINGS,
            start_chapter=10, start_verse=8,
            end_chapter=10, end_verse=12,
            hebrew_text="יָדֶיךָ עִצְּבוּנִי וַיַּעֲשׂוּנִי",
            english_text="Your hands shaped me and made me",
            chunk_type=ChunkType.SPEAKER_TURN,
            verse_count=5,
            token_estimate=120,
        ),
        TanakhChunk(
            chunk_id="isaiah_040_011_040_011",
            reference="Isaiah 40:11",
            book="Isaiah",
            book_category=BookCategory.PROPHETS,
            start_chapter=40, start_verse=11,
            end_chapter=40, end_verse=11,
            hebrew_text="כְּרֹעֶה עֶדְרוֹ יִרְעֶה",
            english_text="He tends his flock like a shepherd",
            chunk_type=ChunkType.SEFARIA_SECTION,
            verse_count=1,
            token_estimate=50,
        ),
    ]
```

```python
# tests/thematic/test_embedding_service.py
"""Tests for embedding service."""
import pytest


class TestMockEmbeddings:
    """Tests for MockEmbeddings."""

    def test_embed_returns_correct_dimension(self, mock_embedder):
        embedding = mock_embedder.embed("test text")
        assert len(embedding) == mock_embedder.dimension

    def test_embed_is_deterministic(self, mock_embedder):
        text = "same text"
        embedding1 = mock_embedder.embed(text)
        embedding2 = mock_embedder.embed(text)
        assert embedding1 == embedding2

    def test_different_text_different_embedding(self, mock_embedder):
        embedding1 = mock_embedder.embed("text one")
        embedding2 = mock_embedder.embed("text two")
        assert embedding1 != embedding2

    def test_embed_batch(self, mock_embedder):
        texts = ["text one", "text two", "text three"]
        embeddings = mock_embedder.embed_batch(texts)
        assert len(embeddings) == 3
        assert all(len(e) == mock_embedder.dimension for e in embeddings)


class TestSemanticMockEmbeddings:
    """Tests for SemanticMockEmbeddings."""

    def test_similar_text_similar_embedding(self, semantic_embedder):
        """Texts with shared words should have similar embeddings."""
        import math

        text1 = "the shepherd tends his flock"
        text2 = "the shepherd guards his sheep"
        text3 = "the king sits on his throne"

        emb1 = semantic_embedder.embed(text1)
        emb2 = semantic_embedder.embed(text2)
        emb3 = semantic_embedder.embed(text3)

        def cosine_sim(a, b):
            dot = sum(x*y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x*x for x in a))
            norm_b = math.sqrt(sum(x*x for x in b))
            return dot / (norm_a * norm_b) if norm_a and norm_b else 0

        sim_1_2 = cosine_sim(emb1, emb2)  # shepherd texts
        sim_1_3 = cosine_sim(emb1, emb3)  # shepherd vs king

        # Shepherd texts should be more similar
        assert sim_1_2 > sim_1_3
```

```python
# tests/thematic/test_vector_store.py
"""Tests for vector store."""
import pytest


class TestInMemoryVectorStore:
    """Tests for InMemoryVectorStore."""

    def test_add_and_count(self, memory_store, mock_embedder):
        ids = ["chunk_1", "chunk_2"]
        embeddings = [mock_embedder.embed("text 1"), mock_embedder.embed("text 2")]
        metadatas = [{"book": "Genesis"}, {"book": "Exodus"}]

        memory_store.add(ids, embeddings, metadatas)

        assert memory_store.count() == 2

    def test_search_returns_results(self, memory_store, mock_embedder):
        # Add vectors
        ids = ["chunk_1", "chunk_2", "chunk_3"]
        embeddings = [mock_embedder.embed(f"text {i}") for i in range(3)]
        metadatas = [{"book": "Genesis"}] * 3

        memory_store.add(ids, embeddings, metadatas)

        # Search
        query_emb = mock_embedder.embed("text 1")
        results = memory_store.search(query_emb, k=2)

        assert len(results) == 2
        assert results[0].chunk_id == "chunk_1"  # Exact match should be first

    def test_clear(self, memory_store, mock_embedder):
        memory_store.add(["chunk_1"], [mock_embedder.embed("text")], [{}])
        assert memory_store.count() == 1

        memory_store.clear()
        assert memory_store.count() == 0
```

```python
# tests/thematic/test_thematic_librarian.py
"""Tests for ThematicParallelsLibrarian."""
import pytest
from src.agents.thematic_parallels_librarian import (
    ThematicParallelsLibrarian,
    VerseText,
)


class TestThematicParallelsLibrarian:
    """Tests for the librarian."""

    @pytest.fixture
    def librarian(self, semantic_embedder, memory_store, sample_chunks, tmp_path):
        """Create librarian with seeded data."""
        import json

        # Save chunks to temp file
        corpus_file = tmp_path / "tanakh_chunks.jsonl"
        with open(corpus_file, "w") as f:
            for chunk in sample_chunks:
                f.write(json.dumps(chunk.to_dict()) + "\n")

        # Create librarian
        lib = ThematicParallelsLibrarian(
            embedding_service=semantic_embedder,
            vector_store=memory_store,
            chunk_corpus_path=str(corpus_file),
            min_similarity=0.0,  # Accept all for testing
        )

        # Index chunks
        ids = [c.chunk_id for c in sample_chunks]
        embeddings = [semantic_embedder.embed(c.embedding_text()) for c in sample_chunks]
        metadatas = [
            {
                "reference": c.reference,
                "book": c.book,
                "book_category": c.book_category.value,
                "chunk_type": c.chunk_type.value,
                "verse_count": c.verse_count,
            }
            for c in sample_chunks
        ]
        memory_store.add(ids, embeddings, metadatas)

        return lib

    def test_find_parallels_for_text(self, librarian):
        """Test finding parallels for arbitrary text."""
        results = librarian.find_parallels_for_text(
            "shepherd tends flock",
            k=3,
            exclude_books=[],  # Don't exclude anything for test
        )

        assert len(results) > 0
        # Isaiah shepherd passage should be highly ranked
        refs = [r.reference for r in results]
        assert any("Isaiah" in r for r in refs)

    def test_excludes_specified_books(self, librarian):
        """Test that excluded books are filtered."""
        results = librarian.find_parallels_for_text(
            "test query",
            k=10,
            exclude_books=["Genesis"],
        )

        for r in results:
            assert r.book != "Genesis"

    def test_find_parallels_for_psalm(self, librarian):
        """Test finding parallels for psalm verses."""
        verses = [
            VerseText(number=1, hebrew="יהוה רעי", english="The LORD is my shepherd"),
        ]

        results = librarian.find_parallels(
            psalm_chapter=23,
            psalm_verses=verses,
            k_per_verse=3,
            max_total=5,
        )

        assert len(results) > 0

    def test_deduplicates_results(self, librarian):
        """Test that duplicate references are removed."""
        # Search with multiple similar verses
        verses = [
            VerseText(number=1, hebrew="רועה", english="shepherd"),
            VerseText(number=2, hebrew="רועה צאן", english="shepherd of sheep"),
        ]

        results = librarian.find_parallels(
            psalm_chapter=23,
            psalm_verses=verses,
            k_per_verse=5,
            max_total=10,
        )

        # Check no duplicate references
        refs = [r.reference for r in results]
        assert len(refs) == len(set(refs))

    def test_format_as_markdown(self, librarian):
        """Test markdown formatting."""
        results = librarian.find_parallels_for_text("test", k=2)

        markdown = librarian.format_as_markdown(results)

        assert "## Thematic Parallels" in markdown
        assert "Similarity" in markdown
```

### Step 5.2: Integration Tests

```python
# tests/thematic/test_integration.py
"""Integration tests with real services (marked slow)."""
import pytest


@pytest.mark.integration
@pytest.mark.slow
class TestRealIntegration:
    """Tests with real embedding service and corpus."""

    @pytest.fixture(scope="class")
    def real_librarian(self):
        """Create librarian with real services."""
        from src.agents.thematic_parallels_librarian import create_thematic_librarian
        return create_thematic_librarian(use_mock=False)

    def test_psalm_23_finds_shepherd_passages(self, real_librarian):
        """Psalm 23 should find other shepherd imagery."""
        results = real_librarian.find_parallels_for_text(
            "יהוה רעי לא אחסר\nThe LORD is my shepherd, I shall not want",
            k=10,
        )

        # Should find shepherd passages
        refs = [r.reference for r in results]
        books = [r.book for r in results]

        # At least one should be from Isaiah or Ezekiel (shepherd imagery)
        assert any(b in ["Isaiah", "Ezekiel", "Jeremiah"] for b in books), \
            f"Expected prophetic shepherd passages, got: {refs}"

    def test_psalm_139_finds_creation_passages(self, real_librarian):
        """Psalm 139 womb imagery should find Job creation passages."""
        results = real_librarian.find_parallels_for_text(
            "כי אתה קנית כליתי תסכני בבטן אמי\nFor you created my inmost being; you knit me together in my mother's womb",
            k=10,
        )

        refs = [r.reference for r in results]
        books = [r.book for r in results]

        # Should find Job's creation language
        assert "Job" in books, f"Expected Job, got: {refs}"
```

### Step 5.3: Run Test Suite

```bash
# Run all tests
pytest tests/thematic/ -v

# Run only unit tests (fast)
pytest tests/thematic/ -v -m "not integration"

# Run integration tests (slow, uses API)
pytest tests/thematic/ -v -m integration

# Run with coverage
pytest tests/thematic/ --cov=src/thematic --cov-report=html
```

### Checkpoint: Phase 5 Complete
- [ ] All unit tests passing
- [ ] Integration tests passing (mark as slow)
- [ ] Coverage > 80% for new code
- [ ] **MANUAL VALIDATION**: Run on 5 diverse psalms (lament, praise, wisdom, royal, creation) and review results

---

## 10. Session Management Protocol

### Enhanced Session Tracking

The existing `PROJECT_STATUS.md` and `CLAUDE.md` work well for single-feature work. For this multi-phase feature, I recommend adding a **feature-specific tracking file**.

### New File: `docs/features/THEMATIC_PARALLELS_STATUS.md`

```markdown
# Thematic Parallels Feature - Status Tracker

**Feature Branch**: [branch name if applicable]
**Implementation Plan**: `docs/features/THEMATIC_PARALLELS_IMPLEMENTATION_PLAN.md`
**Started**: [date]
**Target Completion**: [date]

---

## Phase Progress

| Phase | Status | Started | Completed | Notes |
|-------|--------|---------|-----------|-------|
| 0. Environment Setup | ⬜ Not Started | - | - | |
| 1. Corpus Preparation | ⬜ Not Started | - | - | |
| 2. Embedding & Indexing | ⬜ Not Started | - | - | |
| 3. Retrieval Implementation | ⬜ Not Started | - | - | |
| 4. Pipeline Integration | ⬜ Not Started | - | - | |
| 5. Testing & Validation | ⬜ Not Started | - | - | |

**Legend**: ⬜ Not Started | 🟡 In Progress | ✅ Complete | ❌ Blocked

---

## Session Log

### Session [N] - [Date]

**Phase**: [current phase]
**Duration**: [hours]
**Developer**: [name]

**Completed**:
- [ ] Task 1
- [ ] Task 2

**Blockers**:
- None

**Next Session**:
- [ ] Next task 1
- [ ] Next task 2

---

## Checkpoints Verified

### Phase 0
- [ ] Dependencies installed
- [ ] Directories created
- [ ] OpenAI API verified

### Phase 1
- [ ] Schemas defined
- [ ] CorpusBuilder working
- [ ] Chunks visually inspected (20+ samples)
- [ ] JSONL file generated

### Phase 2
- [ ] Embeddings working
- [ ] Vector store working
- [ ] Cost estimate verified

### Phase 3
- [ ] Librarian working
- [ ] Test script working
- [ ] Results sensible for Psalms 23, 139, 73

### Phase 4
- [ ] ResearchBundle updated
- [ ] ResearchAssembler integrated
- [ ] Full pipeline test passed

### Phase 5
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Manual validation complete

---

## Known Issues

| Issue | Severity | Status | Notes |
|-------|----------|--------|-------|
| - | - | - | - |

---

## Quality Validation Results

### Psalm 23 (Shepherd imagery)
- Top parallels found: [list]
- Quality assessment: [good/needs work]

### Psalm 139 (Creation in womb)
- Top parallels found: [list]
- Quality assessment: [good/needs work]

### Psalm 73 (Prosperity of wicked)
- Top parallels found: [list]
- Quality assessment: [good/needs work]
```

### Session Start Protocol

At the start of each session working on this feature:

1. **Read the implementation plan** (this document)
2. **Check the status tracker** (`THEMATIC_PARALLELS_STATUS.md`)
3. **Identify current phase and next task**
4. **Update status to "In Progress"**

### Session End Protocol

At the end of each session:

1. **Update status tracker** with:
   - Tasks completed
   - Time spent
   - Blockers encountered
   - Next tasks

2. **Verify checkpoints** if phase completed

3. **Commit with descriptive message**:
   ```bash
   git commit -m "Thematic Parallels: Phase [N] - [description]

   - [accomplishment 1]
   - [accomplishment 2]

   Next: [next task]"
   ```

### Update CLAUDE.md

Add this feature to the "Recent Major Changes" section when complete:

```markdown
**Session [N] (YYYY-MM-DD)**: Thematic Parallels Librarian
- Added RAG-based thematic parallel discovery using vector embeddings
- Chunks Tanakh by literary units (pericopes, speaker turns)
- Finds thematically similar passages without lexical overlap
- Integrated into research bundle with post-retrieval filtering
```

---

## Appendix A: Data Schemas

### tanakh_chunks.jsonl Schema

```json
{
  "chunk_id": "genesis_001_001_001_005",
  "reference": "Genesis 1:1-5",
  "book": "Genesis",
  "book_category": "Torah",
  "start_chapter": 1,
  "start_verse": 1,
  "end_chapter": 1,
  "end_verse": 5,
  "hebrew_text": "בְּרֵאשִׁית בָּרָא אֱלֹהִים...",
  "english_text": "In the beginning God created...",
  "chunk_type": "sliding_window",
  "verse_count": 5,
  "token_estimate": 150,
  "sefaria_topics": ["creation", "god"]
}
```

### chunk_metadata.json Schema

```json
{
  "total_chunks": 2500,
  "chunks_by_book": {
    "Genesis": 150,
    "Exodus": 120
  },
  "chunks_by_category": {
    "Torah": 500,
    "Prophets": 1200,
    "Writings": 800
  },
  "chunks_by_type": {
    "sliding_window": 2000,
    "sefaria_section": 300,
    "speaker_turn": 200
  },
  "avg_verse_count": 5.2,
  "avg_token_estimate": 180,
  "created_at": "2025-12-09T10:30:00"
}
```

### ThematicParallel Schema

```python
@dataclass
class ThematicParallel:
    reference: str           # "Job 10:8-12"
    hebrew_text: str         # Full Hebrew
    english_text: str        # Full English
    similarity_score: float  # 0.0-1.0
    source_verse: int        # Psalm verse that matched
    book: str                # "Job"
    book_category: str       # "Writings"
    chunk_type: str          # "speaker_turn"
    verse_count: int         # Number of verses
```

---

## Appendix B: Test Cases

### Must-Find Parallels

These are known thematic parallels that the system SHOULD find:

| Psalm | Verse | Theme | Expected Parallel | Lexical Overlap |
|-------|-------|-------|-------------------|-----------------|
| 23 | 1 | Shepherd | Isaiah 40:11 | Moderate |
| 23 | 4 | Valley of death | Job 10:21-22 | Low |
| 139 | 13 | Formed in womb | Job 10:8-12 | Low |
| 73 | 3 | Wicked prosper | Ecclesiastes 8:14 | Low |
| 8 | 4 | What is man | Job 7:17-18 | High |
| 1 | 3 | Tree by water | Jeremiah 17:7-8 | Moderate |
| 104 | 2-4 | Creation imagery | Job 38-39 | Moderate |

### Must-NOT-Find (Negative Cases)

The system should NOT return:
- Other Psalms (excluded by design)
- Passages with only formulaic overlap ("and the LORD said")
- Completely unrelated passages (similarity < 0.3)

---

## Appendix C: Troubleshooting

### Common Issues

#### "No module named 'chromadb'"
```bash
pip install chromadb
```

#### "OpenAI API key not found"
```bash
export OPENAI_API_KEY="your-key-here"
```

#### "Vector store is empty"
Run the index build script:
```bash
python scripts/build_vector_index.py
```

#### "Poor retrieval quality"
1. Check chunk sizes (too small = lost context, too large = diluted signal)
2. Verify embeddings are being generated correctly
3. Try adjusting `min_similarity` threshold
4. Review chunking strategy for the relevant book

#### "Duplicate results in bundle"
The filtering logic in ResearchAssembler should handle this. Check:
1. `_collect_all_references()` is capturing all sources
2. `_reference_overlaps()` is detecting overlaps correctly

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-09 | Claude | Initial implementation plan |

---

*This document should be treated as the authoritative guide for implementing the Thematic Parallels feature. Update the Session Log and Checkpoints as work progresses.*
