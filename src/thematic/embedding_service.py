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