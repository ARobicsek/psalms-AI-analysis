#!/usr/bin/env python3
"""
Check the status of the thematic vector index.

This script verifies:
1. Whether the ChromaDB index exists and is accessible
2. How many chunks are indexed
3. Whether the index includes Psalms
4. Index file sizes and integrity

Usage:
    python check_index_status.py
"""
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.thematic.vector_store import create_vector_store
from src.thematic.corpus_builder import load_metadata

def check_index_status():
    """Check the status of the vector index."""

    print("="*60)
    print("THEMATIC VECTOR INDEX STATUS CHECK")
    print("="*60)

    # Check corpus metadata
    corpus_dir = Path("data/thematic_corpus")
    if not corpus_dir.exists():
        print(f"❌ Corpus directory not found: {corpus_dir}")
        return

    print(f"[INFO] Corpus directory: {corpus_dir}")

    # Load metadata
    try:
        metadata = load_metadata(str(corpus_dir))
        print(f"[INFO] Total chunks in corpus: {metadata.total_chunks:,}")
        print(f"[INFO] Average tokens per chunk: {metadata.avg_token_estimate:.1f}")
    except Exception as e:
        print(f"❌ Error loading corpus metadata: {e}")
        return

    # Check ChromaDB directory
    index_dir = corpus_dir / "chroma_db"
    print(f"\n[INFO] Index directory: {index_dir}")

    if not index_dir.exists():
        print("[ERROR] Index directory not found")
        print("   Run: python scripts/build_vector_index.py")
        return

    # Check index files
    sqlite_file = index_dir / "chroma.sqlite3"
    if sqlite_file.exists():
        size_mb = sqlite_file.stat().st_size / (1024 * 1024)
        print(f"[OK] SQLite database exists ({size_mb:.1f} MB)")
    else:
        print("[ERROR] SQLite database not found")
        return

    # Check collection directories
    collection_dirs = [d for d in index_dir.iterdir() if d.is_dir() and d.name != "__pycache__"]
    print(f"[INFO] Collections found: {len(collection_dirs)}")

    for collection_dir in collection_dirs:
        print(f"   - {collection_dir.name}")
        data_file = collection_dir / "data_level0.bin"
        if data_file.exists():
            size_mb = data_file.stat().st_size / (1024 * 1024)
            print(f"     Data: {size_mb:.1f} MB")

    # Try to connect to vector store
    print(f"\n[INFO] Testing vector store connection...")
    try:
        vector_store = create_vector_store(
            provider="chroma",
            persist_directory=str(index_dir)
        )

        # Get count
        chunk_count = vector_store.count()
        print(f"[OK] Vector store connected successfully")
        print(f"[INFO] Chunks indexed: {chunk_count:,}")

        # Check if complete
        if chunk_count == metadata.total_chunks:
            print("[OK] Index is complete (all chunks indexed)")
        elif chunk_count > 0:
            percentage = 100 * chunk_count / metadata.total_chunks
            print(f"[WARN] Index partially complete ({percentage:.1f}% indexed)")
            print(f"   Missing: {metadata.total_chunks - chunk_count:,} chunks")
        else:
            print("[ERROR] No chunks indexed")

        # Check for Psalms
        print(f"\n[INFO] Checking for Psalms in index...")
        results = vector_store.search(
            query_embedding=[0.1] * 3072,  # Dummy embedding
            n_results=10,
            where={"book": "Psalms"}
        )

        psalms_count = results['total_results']
        if psalms_count > 0:
            print(f"[OK] Found {psalms_count:,} Psalms chunks")
        else:
            print("[WARN] No Psalms chunks found (may be excluded)")

        # Test search functionality
        print(f"\n[INFO] Testing search functionality...")
        try:
            # Create a dummy query embedding (all zeros)
            dummy_embedding = [0.0] * 3072
            search_results = vector_store.search(
                query_embedding=dummy_embedding,
                n_results=3
            )

            if search_results['total_results'] > 0:
                print(f"[OK] Search working (found {search_results['total_results']} results)")

                # Show top result
                if search_results['results']:
                    top = search_results['results'][0]
                    print(f"   Top result: {top['metadata']['reference']}")
                    print(f"   Book: {top['metadata']['book']}")
            else:
                print("[WARN] Search returned no results")

        except Exception as e:
            print(f"[ERROR] Search test failed: {e}")

    except Exception as e:
        print(f"[ERROR] Failed to connect to vector store: {e}")
        return

    print(f"\n" + "="*60)
    print("STATUS SUMMARY")
    print("="*60)

    # Summary
    if chunk_count == metadata.total_chunks:
        status = "[OK] COMPLETE"
        message = "Index is fully built and ready"
    elif chunk_count > 0:
        status = "[WARN] INCOMPLETE"
        message = f"Index partially built ({chunk_count:,}/{metadata.total_chunks:,})"
    else:
        status = "[ERROR] NOT BUILT"
        message = "No chunks indexed"

    print(f"Status: {status}")
    print(f"Message: {message}")

    if chunk_count < metadata.total_chunks:
        print(f"\nTo complete the index:")
        print(f"  python scripts/build_vector_index.py")

    print(f"\nTo test thematic search:")
    print(f"  python scripts/test_thematic_retrieval.py --psalm 23")


if __name__ == "__main__":
    check_index_status()