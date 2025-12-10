"""Vector store implementation using ChromaDB for similarity search."""
import logging
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Iterator
from pathlib import Path
import uuid

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None

import numpy as np
from .embedding_service import EmbeddingService, OpenAIEmbeddings
from .chunk_schemas import TanakhChunk

logger = logging.getLogger(__name__)


class VectorStore(ABC):
    """Abstract base class for vector stores."""

    @abstractmethod
    def add_chunks(self, chunks: List[TanakhChunk], embeddings: List[List[float]]) -> None:
        """Add chunks with their embeddings to the store."""
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Search for similar chunks."""
        pass

    @abstractmethod
    def get(self, ids: List[str]) -> Dict[str, Any]:
        """Get chunks by IDs."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Get total number of chunks in store."""
        pass


class ChromaVectorStore(VectorStore):
    """ChromaDB implementation of vector store."""

    def __init__(
        self,
        collection_name: str = "tanakh_thematics",
        persist_directory: Optional[str] = None,
        embedding_function: Optional[Any] = None,
    ):
        """Initialize ChromaDB vector store.

        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist the database
            embedding_function: Optional embedding function (we'll use our own)
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("chromadb is not installed. Install with: pip install chromadb")

        self.collection_name = collection_name

        # Configure ChromaDB settings
        settings = Settings(
            allow_reset=True,
            is_persistent=persist_directory is not None,
        )

        # Create client
        if persist_directory:
            self.client = chromadb.PersistentClient(path=persist_directory, settings=settings)
        else:
            self.client = chromadb.Client(settings=settings)

        # Always create collection without embedding function since we provide our own
        # First delete if it exists to avoid conflicts
        try:
            self.client.delete_collection(name=collection_name)
        except:
            pass

        self.collection = self.client.create_collection(
            name=collection_name,
            metadata={"description": "Tanakh thematic chunks for parallel search"}
        )

    def add_chunks(self, chunks: List[TanakhChunk], embeddings: List[List[float]]) -> None:
        """Add chunks with their embeddings to the store.

        Args:
            chunks: List of TanakhChunk objects
            embeddings: List of embedding vectors matching chunks
        """
        if len(chunks) != len(embeddings):
            raise ValueError(f"Number of chunks ({len(chunks)}) must match number of embeddings ({len(embeddings)})")

        # Prepare data for ChromaDB
        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.hebrew_text for chunk in chunks]  # Use Hebrew text as document
        metadatas = []

        for chunk in chunks:
            metadata = {
                "reference": chunk.reference,
                "book": chunk.book,
                "book_category": chunk.book_category.value,
                "start_chapter": chunk.start_chapter,
                "start_verse": chunk.start_verse,
                "end_chapter": chunk.end_chapter,
                "end_verse": chunk.end_verse,
                "verse_count": chunk.verse_count,
                "chunk_type": chunk.chunk_type.value,
                "token_estimate": chunk.token_estimate,
            }
            # Add English text if available
            if chunk.english_text:
                metadata["english_text"] = chunk.english_text
            metadatas.append(metadata)

        # Add to collection in batches to avoid memory issues
        batch_size = 1000
        for i in range(0, len(chunks), batch_size):
            batch_end = min(i + batch_size, len(chunks))
            logger.info(f"Adding batch {i//batch_size + 1}: chunks {i}-{batch_end-1}")

            self.collection.add(
                ids=ids[i:batch_end],
                documents=documents[i:batch_end],
                metadatas=metadatas[i:batch_end],
                embeddings=embeddings[i:batch_end]
            )

        logger.info(f"Added {len(chunks)} chunks to vector store")

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Search for similar chunks.

        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            where: Optional filter criteria
            include: Fields to include in results

        Returns:
            Dictionary containing search results
        """
        if include is None:
            include = ["metadatas", "documents", "distances"]

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=include
        )

        # Convert results to a more convenient format
        formatted_results = []
        if results["ids"]:
            for i in range(len(results["ids"][0])):
                result = {
                    "id": results["ids"][0][i],
                    "metadata": results["metadatas"][0][i] if "metadatas" in results else None,
                    "document": results["documents"][0][i] if "documents" in results else None,
                    "distance": results["distances"][0][i] if "distances" in results else None,
                    "similarity": 1 - results["distances"][0][i] if "distances" in results and results["distances"][0][i] is not None else None,
                }
                formatted_results.append(result)

        return {
            "results": formatted_results,
            "total_results": len(formatted_results)
        }

    def get(self, ids: List[str]) -> Dict[str, Any]:
        """Get chunks by IDs."""
        results = self.collection.get(ids=ids, include=["metadatas", "documents"])

        formatted_results = []
        for i in range(len(results["ids"])):
            result = {
                "id": results["ids"][i],
                "metadata": results["metadatas"][i] if "metadatas" in results else None,
                "document": results["documents"][i] if "documents" in results else None,
            }
            formatted_results.append(result)

        return {"results": formatted_results}

    def count(self) -> int:
        """Get total number of chunks in store."""
        return self.collection.count()

    def persist(self) -> None:
        """Persist the database to disk (if persistent client)."""
        if hasattr(self.client, "persist"):
            self.client.persist()

    def reset(self) -> None:
        """Reset the collection (delete all data)."""
        self.client.reset()


class InMemoryVectorStore(VectorStore):
    """Simple in-memory vector store for testing and small datasets."""

    def __init__(self):
        """Initialize in-memory vector store."""
        self.embeddings: List[List[float]] = []
        self.chunks: List[TanakhChunk] = []
        self.id_to_index: Dict[str, int] = {}

    def add_chunks(self, chunks: List[TanakhChunk], embeddings: List[List[float]]) -> None:
        """Add chunks with their embeddings to the store."""
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")

        for chunk, embedding in zip(chunks, embeddings):
            if chunk.chunk_id in self.id_to_index:
                logger.warning(f"Chunk {chunk.chunk_id} already exists, skipping")
                continue

            self.id_to_index[chunk.chunk_id] = len(self.chunks)
            self.chunks.append(chunk)
            self.embeddings.append(embedding)

        logger.info(f"Added {len(chunks)} chunks to in-memory store")

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Search for similar chunks using cosine similarity."""
        if not self.embeddings:
            return {"results": [], "total_results": 0}

        # Calculate cosine similarity
        query_norm = np.linalg.norm(query_embedding)
        if query_norm == 0:
            return {"results": [], "total_results": 0}

        similarities = []
        for i, embedding in enumerate(self.embeddings):
            # Apply filter if provided
            if where:
                chunk = self.chunks[i]
                match = True
                for key, value in where.items():
                    if key == "book" and chunk.book != value:
                        match = False
                        break
                    elif key == "book_category" and chunk.book_category.value != value:
                        match = False
                        break
                    # Add more filters as needed
                if not match:
                    continue

            # Cosine similarity
            emb_norm = np.linalg.norm(embedding)
            if emb_norm == 0:
                continue
            similarity = np.dot(query_embedding, embedding) / (query_norm * emb_norm)
            similarities.append((i, float(similarity)))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Format results
        formatted_results = []
        for i, similarity in similarities[:n_results]:
            chunk = self.chunks[i]
            result = {
                "id": chunk.chunk_id,
                "metadata": {
                    "reference": chunk.reference,
                    "book": chunk.book,
                    "book_category": chunk.book_category.value,
                    "start_chapter": chunk.start_chapter,
                    "start_verse": chunk.start_verse,
                    "end_chapter": chunk.end_chapter,
                    "end_verse": chunk.end_verse,
                    "verse_count": chunk.verse_count,
                    "chunk_type": chunk.chunk_type.value,
                    "token_estimate": chunk.token_estimate,
                },
                "document": chunk.hebrew_text,
                "similarity": similarity,
                "distance": 1 - similarity,  # Convert to distance for consistency
            }
            formatted_results.append(result)

        return {
            "results": formatted_results,
            "total_results": len(formatted_results)
        }

    def get(self, ids: List[str]) -> Dict[str, Any]:
        """Get chunks by IDs."""
        formatted_results = []
        for chunk_id in ids:
            if chunk_id in self.id_to_index:
                idx = self.id_to_index[chunk_id]
                chunk = self.chunks[idx]
                result = {
                    "id": chunk.chunk_id,
                    "metadata": {
                        "reference": chunk.reference,
                        "book": chunk.book,
                        "book_category": chunk.book_category.value,
                    },
                    "document": chunk.hebrew_text,
                }
                formatted_results.append(result)

        return {"results": formatted_results}

    def count(self) -> int:
        """Get total number of chunks in store."""
        return len(self.chunks)


def create_vector_store(
    provider: str = "chroma",
    collection_name: str = "tanakh_thematics",
    persist_directory: Optional[str] = None,
) -> VectorStore:
    """Factory function to create vector store.

    Args:
        provider: Provider name ("chroma" or "memory")
        collection_name: Name of the collection (for ChromaDB)
        persist_directory: Directory to persist ChromaDB

    Returns:
        VectorStore instance
    """
    if provider == "chroma":
        return ChromaVectorStore(
            collection_name=collection_name,
            persist_directory=persist_directory
        )
    elif provider == "memory":
        return InMemoryVectorStore()
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'chroma' or 'memory'")