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
        collection_name: str = "tanakh_chunks_1_verse",
    ):
        import chromadb
        from chromadb.config import Settings

        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )

        # Get or create collection without embedding function
        # since we'll provide pre-computed embeddings
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
        # ChromaDB returns results
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter,
            include=["metadatas", "distances"],
        )

        # Convert to SearchResult objects
        search_results = []

        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                # ChromaDB returns distance, convert to similarity
                # For cosine, similarity = 1 / (1 + distance)
                distance = results["distances"][0][i] if results["distances"] else 0
                similarity = 1 / (1 + distance)

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
                    if item["metadata"].get(key) != value:
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