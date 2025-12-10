"""Embedding service for generating text embeddings using OpenAI or mock provider."""
import logging
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Union, Optional
import os
from openai import OpenAI

logger = logging.getLogger(__name__)


class EmbeddingService(ABC):
    """Abstract base class for embedding services."""

    @abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass

    @abstractmethod
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding dimension."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model name identifier."""
        pass


class OpenAIEmbeddings(EmbeddingService):
    """OpenAI embedding service using text-embedding-3-large."""

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-large"):
        """Initialize OpenAI embedding service.

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            model: OpenAI embedding model to use.
        """
        self.model = model
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

        # Map models to their dimensions
        self._dimensions = {
            "text-embedding-3-large": 3072,
            "text-embedding-3-small": 1536,
            "text-embedding-ada-002": 1536,
        }

        if model not in self._dimensions:
            raise ValueError(f"Unknown model: {model}. Known models: {list(self._dimensions.keys())}")

    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently."""
        if not texts:
            return []

        # Process in batches to handle rate limits
        batch_size = 100
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                if len(batch) < batch_size:
                    # Small batch, no need to sleep
                    continue

                # Add small delay to respect rate limits
                import time
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error generating embeddings for batch {i//batch_size}: {e}")
                # Fallback: generate one by one
                for text in batch:
                    all_embeddings.append(self.get_embedding(text))

        return all_embeddings

    @property
    def dimension(self) -> int:
        """Embedding dimension."""
        return self._dimensions[self.model]

    @property
    def model_name(self) -> str:
        """Model name identifier."""
        return self.model

    def estimate_cost(self, num_texts: int, avg_tokens_per_text: int = 150) -> float:
        """Estimate cost for embedding texts in USD.

        Args:
            num_texts: Number of texts to embed
            avg_tokens_per_text: Average token count per text

        Returns:
            Estimated cost in USD
        """
        # Pricing as of 2024-12
        pricing = {
            "text-embedding-3-large": 0.00013 / 1000,  # $0.00013 per 1K tokens
            "text-embedding-3-small": 0.00002 / 1000,  # $0.00002 per 1K tokens
            "text-embedding-ada-002": 0.0001 / 1000,   # $0.0001 per 1K tokens
        }

        total_tokens = num_texts * avg_tokens_per_text
        cost_per_token = pricing[self.model]
        return total_tokens * cost_per_token


class MockEmbeddings(EmbeddingService):
    """Mock embedding service for testing without API calls.

    Generates deterministic pseudo-random embeddings based on text hash.
    """

    def __init__(self, dimension: int = 3072, seed: int = 42):
        """Initialize mock embedding service.

        Args:
            dimension: Embedding dimension (default: 3072 to match OpenAI large)
            seed: Random seed for reproducibility
        """
        self._dimension = dimension
        self._model_name = f"mock-{dimension}d"
        np.random.seed(seed)

    def _hash_to_embedding(self, text: str) -> List[float]:
        """Convert text hash to deterministic embedding."""
        # Use text hash as seed
        hash_val = hash(text)
        rng = np.random.RandomState(hash_val % (2**32))

        # Generate random embedding with unit norm
        embedding = rng.normal(0, 1, self._dimension)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding.tolist()

    def get_embedding(self, text: str) -> List[float]:
        """Generate mock embedding for a single text."""
        return self._hash_to_embedding(text)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings for multiple texts."""
        return [self.get_embedding(text) for text in texts]

    @property
    def dimension(self) -> int:
        """Embedding dimension."""
        return self._dimension

    @property
    def model_name(self) -> str:
        """Model name identifier."""
        return self._model_name


def create_embedding_service(
    provider: str = "openai",
    api_key: Optional[str] = None,
    model: str = "text-embedding-3-large",
    dimension: int = 3072,
    seed: int = 42,
) -> EmbeddingService:
    """Factory function to create embedding service.

    Args:
        provider: Provider name ("openai" or "mock")
        api_key: API key for OpenAI (optional)
        model: Model name for OpenAI
        dimension: Dimension for mock embeddings
        seed: Random seed for mock embeddings

    Returns:
        EmbeddingService instance
    """
    if provider == "openai":
        return OpenAIEmbeddings(api_key=api_key, model=model)
    elif provider == "mock":
        return MockEmbeddings(dimension=dimension, seed=seed)
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'openai' or 'mock'")