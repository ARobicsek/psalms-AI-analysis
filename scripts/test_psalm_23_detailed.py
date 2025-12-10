#!/usr/bin/env python3
"""
Detailed test of Psalm 23 thematic search.

This script:
1. Finds all Psalm 23 chunks in the corpus
2. For each chunk, performs thematic search
3. Shows the target chunk and its top matches
4. Analyzes quality of parallels

Usage:
    python scripts/test_psalm_23_detailed.py
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.thematic.vector_store import create_vector_store
from src.thematic.corpus_builder import load_corpus, ChunkType, BookCategory
from src.thematic.embedding_service import create_embedding_service
from src.agents.thematic_parallels_librarian import ThematicParallelsLibrarian, create_thematic_librarian

def test_psalm_23():
    """Test Psalm 23 thematic search with detailed output."""

    print("="*70)
    print("PSALM 23 THEMATIC SEARCH - DETAILED ANALYSIS")
    print("="*70)

    # Initialize services
    print("\n[SETUP] Initializing services...")
    embedding_service = create_embedding_service(provider="openai")
    librarian = create_thematic_librarian(provider="openai")

    # Find all Psalm 23 chunks
    print("\n[SEARCH] Finding Psalm 23 chunks...")
    psalm_23_chunks = []
    corpus_dir = Path("data/thematic_corpus")

    for chunk in load_corpus(str(corpus_dir)):
        if chunk.book == "Psalms" and chunk.start_chapter == 23:
            psalm_23_chunks.append(chunk)

    print(f"\nFound {len(psalm_23_chunks)} Psalm 23 chunks:")
    for i, chunk in enumerate(psalm_23_chunks, 1):
        print(f"  {i}. {chunk.reference} ({chunk.verse_count} verses)")

    if not psalm_23_chunks:
        print("\n[ERROR] No Psalm 23 chunks found!")
        return

    print("\n" + "="*70)
    print("DETAILED SEARCH RESULTS")
    print("="*70)

    # Test each chunk
    for i, target_chunk in enumerate(psalm_23_chunks, 1):
        print(f"\n[{i}] TARGET CHUNK: {target_chunk.reference}")
        print("-" * 60)
        print(f"Text: {target_chunk.hebrew_text}")
        print(f"Tokens: {target_chunk.token_estimate}")
        print(f"Type: {target_chunk.chunk_type.value}")

        # Search for thematic parallels
        print(f"\nSearching for parallels...")
        try:
            parallels = librarian.search_thematic_parallels(
                query_text=target_chunk.hebrew_text,
                n_results=5,
                exclude_psalms=True,  # Show cross-references only
                similarity_threshold=0.3
            )

            if parallels:
                print(f"\nFound {len(parallels)} parallels:")
                for j, parallel in enumerate(parallels, 1):
                    print(f"\n  [{i}-{j}] {parallel.reference}")
                    print(f"      Book: {parallel.book}")
                    print(f"      Category: {parallel.book_category}")
                    print(f"      Similarity: {parallel.similarity_score:.3f}")
                    print(f"      Text: {parallel.hebrew_text[:150]}...")
                    if parallel.verses:
                        print(f"      Verses: {parallel.verses}")
            else:
                print("\n  No parallels found above threshold")

        except Exception as e:
            print(f"\n  [ERROR] Search failed: {e}")

        print("\n" + "="*70)

    # Summary analysis
    print("\n" + "="*70)
    print("SUMMARY ANALYSIS")
    print("="*70)

    # Count matches by book category
    category_counts = {}
    total_matches = 0

    print("\nAnalyzing all matches...")
    for target_chunk in psalm_23_chunks:
        try:
            parallels = librarian.search_thematic_parallels(
                query_text=target_chunk.hebrew_text,
                n_results=10,
                exclude_psalms=True,
                similarity_threshold=0.3
            )

            for parallel in parallels:
                category = parallel.book_category
                category_counts[category] = category_counts.get(category, 0) + 1
                total_matches += 1

        except:
            pass  # Skip if search fails

    print(f"\nTotal matches across all Psalm 23 chunks: {total_matches}")
    print("\nMatches by book category:")
    for category, count in sorted(category_counts.items()):
        print(f"  {category}: {count}")

    # Find top matches overall
    print("\nTop 10 overall matches for Psalm 23:")
    all_parallels = []

    for target_chunk in psalm_23_chunks:
        try:
            parallels = librarian.search_thematic_parallels(
                query_text=target_chunk.hebrew_text,
                n_results=20,
                exclude_psalms=True,
                similarity_threshold=0.3
            )
            all_parallels.extend(parallels)
        except:
            pass

    # Sort by similarity
    all_parallels.sort(key=lambda x: x.similarity_score, reverse=True)

    for i, parallel in enumerate(all_parallels[:10], 1):
        print(f"\n  {i}. {parallel.reference} - {parallel.similarity_score:.3f}")
        print(f"     {parallel.hebrew_text[:100]}...")

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    test_psalm_23()