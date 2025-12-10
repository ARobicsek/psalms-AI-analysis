#!/usr/bin/env python3
"""
Get the actual Hebrew text of Psalm 23 chunks from the corpus.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.thematic_parallels_librarian import ThematicParallelsLibrarian


def main():
    librarian = ThematicParallelsLibrarian(similarity_threshold=0.01, max_results=100)

    # Find all results that contain Psalm 23
    all_results = []
    queries = ['יהוה', 'רעי', 'מזמור', 'דשא', 'צלמות', 'שלחן']

    for query in queries:
        results = librarian.find_parallels(query)
        for r in results:
            if 'Psalm 23' in r.reference or 'Psalms 23' in r.reference:
                if r.reference not in [res.reference for res in all_results]:
                    all_results.append(r)

    # Save results
    with open("psalm_23_actual_chunks.txt", "w", encoding="utf-8") as f:
        f.write("ACTUAL PSALM 23 CHUNKS IN CORPUS\n")
        f.write("="*50 + "\n\n")

        for i, chunk in enumerate(all_results, 1):
            f.write(f"Chunk {i}: {chunk.reference}\n")
            f.write(f"Similarity when found: (varies)\n")
            f.write(f"Book: {chunk.book}\n")
            f.write(f"Context verses: {chunk.context_verses}\n")
            f.write("\nHebrew text:\n")
            f.write(chunk.hebrew_text)
            f.write("\n\n")
            f.write("-"*50 + "\n\n")

        # Now test exact match with the actual text
        if all_results:
            f.write("EXACT MATCH TEST\n")
            f.write("="*50 + "\n\n")

            # Use the actual Hebrew text from the first Psalm 23 chunk
            actual_text = all_results[0].hebrew_text
            f.write(f"Using actual Hebrew text from corpus:\n")
            f.write(f"Length: {len(actual_text)} characters\n")
            f.write(f"First 100 chars: {actual_text[:100]}...\n\n")

            # Search with this exact text
            exact_results = librarian.find_parallels(actual_text)

            f.write("Results when searching with exact text:\n")
            for i, r in enumerate(exact_results[:5], 1):
                f.write(f"  {i}. {r.reference} - similarity: {r.similarity:.6f}\n")
                if r.reference == all_results[0].reference:
                    f.write("     ^^^ EXACT SAME CHUNK! ^^^\n")

    print(f"Found {len(all_results)} Psalm 23 chunks")
    print("Details saved to psalm_23_actual_chunks.txt")

    # Simple console output
    if all_results:
        print("\nFirst chunk reference:", all_results[0].reference)
        print("Hebrew text length:", len(all_results[0].hebrew_text))
        print("\nTesting exact match...")
        exact = librarian.find_parallels(all_results[0].hebrew_text)
        if exact:
            print(f"Top result: {exact[0].reference}")
            print(f"Similarity: {exact[0].similarity:.6f}")
            if exact[0].reference == all_results[0].reference:
                print("✓ Found the same chunk!")
            else:
                print("✗ Different chunk found")


if __name__ == "__main__":
    main()