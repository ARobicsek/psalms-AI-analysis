"""
Thematic parallels discovery module using RAG.

This module provides functionality to find thematically similar passages
in the Tanakh (outside Psalms) using vector embeddings.
"""

# Only import what's available so far
from .corpus_builder import CorpusBuilder, load_corpus, load_metadata
from .chunk_schemas import (
    TanakhChunk,
    ChunkMetadata,
    BookCategory,
    ChunkType
)

# These will be added as they're implemented:
# from .embedding_service import EmbeddingService, OpenAIEmbeddings, MockEmbeddings
# from .vector_store import VectorStore, ChromaVectorStore, InMemoryVectorStore

__all__ = [
    # Available now:
    "CorpusBuilder",
    "load_corpus",
    "load_metadata",
    "TanakhChunk",
    "ChunkMetadata",
    "BookCategory",
    "ChunkType",
    # Coming soon:
    # "EmbeddingService",
    # "OpenAIEmbeddings",
    # "MockEmbeddings",
    # "VectorStore",
    # "ChromaVectorStore",
    # "InMemoryVectorStore",
]