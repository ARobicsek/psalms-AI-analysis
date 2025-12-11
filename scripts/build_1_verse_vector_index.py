"""
Build the vector index from the 1-verse chunk corpus.

Usage:
    python scripts/build_1_verse_vector_index.py
    python scripts/build_1_verse_vector_index.py --dry-run  # Estimate cost without embedding
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
    parser = argparse.ArgumentParser(description="Build 1-verse vector index")
    parser.add_argument("--dry-run", action="store_true", help="Estimate cost only")
    parser.add_argument("--batch-size", type=int, default=100, help="Embedding batch size")
    args = parser.parse_args()

    # Paths
    project_root = Path(__file__).parent.parent
    corpus_dir = project_root / "data" / "thematic_corpus_1_verse"
    vector_db_dir = corpus_dir / "chroma_db"

    if args.dry_run:
        print("\n" + "="*60)
        print("DRY RUN - Cost Estimate")
        print("="*60)

        estimate = estimate_cost(str(corpus_dir))
        print(f"Total chunks (verses): {estimate['total_chunks']}")
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
        collection_name="tanakh_chunks_1_verse",
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
    logger.info("Loading 1-verse corpus...")
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
            "chapter": chunk.chapter,
            "verse": chunk.verse,
        }
        for chunk in chunks
    ]

    # Embed
    logger.info("Generating embeddings for 1-verse chunks (this may take a few minutes)...")
    embeddings = embedder.embed_batch(texts, batch_size=args.batch_size)

    # Store
    logger.info("Storing vectors...")
    vector_store.add(ids=ids, embeddings=embeddings, metadatas=metadatas)

    print("\n" + "="*60)
    print("1-VERSE INDEX BUILD COMPLETE")
    print("="*60)
    print(f"Vectors indexed: {vector_store.count()}")
    print(f"Vector DB location: {vector_db_dir}")


if __name__ == "__main__":
    main()