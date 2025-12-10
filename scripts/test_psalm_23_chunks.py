#!/usr/bin/env python3
"""
Test Psalm 23 using the actual 5-verse chunks from the corpus.
This should return similarity ~1.0 for exact matches.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.thematic_parallels_librarian import ThematicParallelsLibrarian
from src.thematic.vector_store import ChromaVectorStore


def main():
    # Connect to vector store to get the actual Psalm 23 chunks
    store = ChromaVectorStore("data/thematic_corpus/chroma_db")

    # Search for Psalm 23 chunks
    psalms_results = store.store.query(
        query_texts=["Psalm 23"],
        n_results=10
    )

    print("PSALM 23 CHUNK VERIFICATION")
    print("="*50)
    print("\nFinding all Psalm 23 chunks in the corpus...")

    # Get all Psalm 23 chunks
    psalm_23_chunks = []
    for i, ref in enumerate(psalms_results["metadatas"][0]):
        if "Psalm 23" in ref["reference"] or "Psalms 23" in ref["reference"]:
            psalm_23_chunks.append({
                "reference": ref["reference"],
                "document": psalms_results["documents"][0][i],
                "metadata": ref
            })

    print(f"\nFound {len(psalm_23_chunks)} Psalm 23 chunks:")
    for i, chunk in enumerate(psalm_23_chunks, 1):
        print(f"\n{i}. {chunk['reference']}")
        print(f"   Hebrew: {chunk['document'][:100]}...")

    # Now test each chunk against itself
    print("\n\nSELF-REFERENCE TEST (each chunk searched against itself)")
    print("="*60)

    librarian = ThematicParallelsLibrarian(
        similarity_threshold=0.9,  # High threshold
        max_results=5
    )

    all_perfect = True

    for i, chunk in enumerate(psalm_23_chunks, 1):
        print(f"\nTest {i}: {chunk['reference']}")
        print(f"Searching with: {chunk['document'][:50]}...")

        # Search for the exact chunk text
        parallels = librarian.find_parallels(chunk['document'])

        if parallels:
            top_match = parallels[0]
            is_same = chunk['reference'] == top_match.reference
            similarity = top_match.similarity

            print(f"Top result: {top_match.reference}")
            print(f"Similarity: {similarity:.6f}")
            print(f"Exact match: {'YES' if is_same else 'NO'}")

            if similarity < 0.99:
                all_perfect = False
                print(f"⚠️  WARNING: Similarity is less than 0.99!")
            elif not is_same:
                all_perfect = False
                print(f"⚠️  WARNING: Top result is not the same chunk!")
        else:
            print("❌ ERROR: No results found!")
            all_perfect = False

    print("\n" + "="*60)
    if all_perfect:
        print("✅ ALL TESTS PASSED - Exact matches found with ~1.0 similarity")
    else:
        print("❌ SOME TESTS FAILED - Check warnings above")


if __name__ == "__main__":
    main()