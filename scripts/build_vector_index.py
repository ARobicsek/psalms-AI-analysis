"""
Build vector index for thematic parallel search.

This script:
1. Loads the Tanakh chunk corpus
2. Generates embeddings using OpenAI
3. Stores them in ChromaDB for fast retrieval
4. Saves index metadata

Usage:
    python scripts/build_vector_index.py --dry-run      # Check costs
    python scripts/build_vector_index.py --mock         # Use mock embeddings
    python scripts/build_vector_index.py                # Build with OpenAI
    python scripts/build_vector_index.py --batch-size 500  # Custom batch size
"""
import argparse
import logging
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.thematic.corpus_builder import load_corpus, load_metadata
from src.thematic.embedding_service import create_embedding_service, OpenAIEmbeddings
from src.thematic.vector_store import create_vector_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def estimate_costs(metadata, avg_tokens_per_chunk=150):
    """Estimate API costs for embedding the corpus."""
    if not hasattr(OpenAIEmbeddings, 'estimate_cost'):
        # Fallback if method doesn't exist
        pricing = {
            "text-embedding-3-large": 0.00013 / 1000,  # $0.00013 per 1K tokens
            "text-embedding-3-small": 0.00002 / 1000,  # $0.00002 per 1K tokens
            "text-embedding-ada-002": 0.0001 / 1000,   # $0.0001 per 1K tokens
        }

        total_tokens = metadata.total_chunks * avg_tokens_per_chunk
        costs = {}
        for model, price_per_token in pricing.items():
            costs[model] = total_tokens * price_per_token

        return costs

    # Use the method if available
    service = OpenAIEmbeddings()
    cost_large = service.estimate_cost(metadata.total_chunks, avg_tokens_per_chunk)
    service_small = OpenAIEmbeddings(model="text-embedding-3-small")
    cost_small = service_small.estimate_cost(metadata.total_chunks, avg_tokens_per_chunk)
    service_ada = OpenAIEmbeddings(model="text-embedding-ada-002")
    cost_ada = service_ada.estimate_cost(metadata.total_chunks, avg_tokens_per_chunk)

    return {
        "text-embedding-3-large": cost_large,
        "text-embedding-3-small": cost_small,
        "text-embedding-ada-002": cost_ada,
    }


def build_index(
    corpus_dir: str,
    index_dir: str,
    provider: str = "openai",
    model: str = "text-embedding-3-large",
    batch_size: int = 100,
    dry_run: bool = False,
):
    """Build the vector index.

    Args:
        corpus_dir: Directory containing the corpus
        index_dir: Directory to store the index
        provider: Embedding provider ("openai" or "mock")
        model: OpenAI model to use
        batch_size: Number of chunks to process at once
        dry_run: If True, only estimate costs without building
    """
    # Load corpus metadata
    logger.info(f"Loading corpus from {corpus_dir}")
    metadata = load_metadata(corpus_dir)
    logger.info(f"Corpus has {metadata.total_chunks} chunks")
    logger.info(f"Average tokens per chunk: {metadata.avg_token_estimate}")

    # Show cost estimate
    logger.info("\n" + "="*60)
    logger.info("COST ESTIMATE")
    logger.info("="*60)
    costs = estimate_costs(metadata, int(metadata.avg_token_estimate))
    for model_name, cost in costs.items():
        status = " [SELECTED]" if model_name == model else ""
        logger.info(f"{model_name:20} ${cost:.2f}{status}")
    logger.info("="*60)

    if dry_run:
        logger.info("Dry run mode - not building index")
        return

    # Create embedding service
    logger.info(f"\nCreating embedding service: {provider}")
    embedding_service = create_embedding_service(
        provider=provider,
        model=model,
        dimension=3072 if provider == "mock" else None
    )
    logger.info(f"Model: {embedding_service.model_name}")
    logger.info(f"Dimension: {embedding_service.dimension}")

    # Create vector store
    logger.info(f"\nCreating vector store at {index_dir}")
    vector_store = create_vector_store(
        provider="chroma" if not dry_run else "memory",
        persist_directory=index_dir
    )

    # Process chunks
    logger.info(f"\nProcessing {metadata.total_chunks} chunks...")
    start_time = time.time()

    chunks_processed = 0
    batch_num = 0

    # Load and process in batches
    batch_texts = []
    batch_chunks = []

    for chunk in load_corpus(corpus_dir):
        batch_texts.append(chunk.hebrew_text)
        batch_chunks.append(chunk)

        if len(batch_texts) >= batch_size:
            batch_num += 1
            logger.info(f"\nBatch {batch_num}: Processing {len(batch_texts)} chunks...")

            # Generate embeddings
            logger.info("  Generating embeddings...")
            embeddings_start = time.time()
            embeddings = embedding_service.get_embeddings(batch_texts)
            embeddings_time = time.time() - embeddings_start
            logger.info(f"  Generated {len(embeddings)} embeddings in {embeddings_time:.2f}s")

            # Add to vector store
            logger.info("  Adding to vector store...")
            vector_store.add_chunks(batch_chunks, embeddings)

            chunks_processed += len(batch_chunks)
            logger.info(f"  Progress: {chunks_processed}/{metadata.total_chunks} ({100*chunks_processed/metadata.total_chunks:.1f}%)")

            # Clear batch
            batch_texts = []
            batch_chunks = []

    # Process final batch if any
    if batch_texts:
        logger.info(f"\nFinal batch: Processing {len(batch_texts)} chunks...")
        embeddings = embedding_service.get_embeddings(batch_texts)
        vector_store.add_chunks(batch_chunks, embeddings)
        chunks_processed += len(batch_chunks)

    # Persist if needed
    if hasattr(vector_store, "persist"):
        logger.info("\nPersisting vector store...")
        vector_store.persist()

    # Summary
    total_time = time.time() - start_time
    logger.info("\n" + "="*60)
    logger.info("BUILD COMPLETE")
    logger.info("="*60)
    logger.info(f"Total chunks processed: {chunks_processed}")
    logger.info(f"Total time: {total_time:.2f} seconds")
    logger.info(f"Average time per chunk: {total_time/chunks_processed:.3f} seconds")
    logger.info(f"Chunks per second: {chunks_processed/total_time:.1f}")

    # Verify
    if hasattr(vector_store, "count"):
        stored_count = vector_store.count()
        logger.info(f"Chunks in store: {stored_count}")
        if stored_count != chunks_processed:
            logger.warning(f"Mismatch! Expected {chunks_processed}, got {stored_count}")

    # Test search
    logger.info("\nTesting search with sample query...")
    test_query = "יהוה רעי לא אחסר"  # "The Lord is my shepherd, I shall not want" in Hebrew
    test_embedding = embedding_service.get_embedding(test_query)
    results = vector_store.search(test_embedding, n_results=3)

    logger.info(f"Found {results['total_results']} results")
    for i, result in enumerate(results["results"][:3]):
        logger.info(f"\nResult {i+1}:")
        logger.info(f"  Reference: {result['metadata']['reference']}")
        logger.info(f"  Similarity: {result['similarity']:.3f}")
        logger.info(f"  Text: {result['document'][:100]}...")

    logger.info("\n✓ Vector index built successfully!")


def main():
    parser = argparse.ArgumentParser(description="Build vector index for thematic search")
    parser.add_argument(
        "--corpus-dir",
        default="data/thematic_corpus",
        help="Directory containing the corpus (default: data/thematic_corpus)"
    )
    parser.add_argument(
        "--index-dir",
        default="data/thematic_corpus/chroma_db",
        help="Directory to store the index (default: data/thematic_corpus/chroma_db)"
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "mock"],
        default="openai",
        help="Embedding provider (default: openai)"
    )
    parser.add_argument(
        "--model",
        default="text-embedding-3-large",
        choices=["text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"],
        help="OpenAI embedding model (default: text-embedding-3-large)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for processing (default: 100)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only estimate costs, don't build index"
    )

    args = parser.parse_args()

    # Create index directory if needed
    Path(args.index_dir).mkdir(parents=True, exist_ok=True)

    # Build index
    build_index(
        corpus_dir=args.corpus_dir,
        index_dir=args.index_dir,
        provider=args.provider,
        model=args.model,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()