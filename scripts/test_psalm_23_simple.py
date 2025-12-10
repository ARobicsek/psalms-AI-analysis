#!/usr/bin/env python3
"""
Simple test to confirm Psalm 23 appears as #1 match for its verses.
Outputs to a file to avoid console encoding issues.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.thematic_parallels_librarian import ThematicParallelsLibrarian


def main():
    # Create librarian with lower threshold
    librarian = ThematicParallelsLibrarian(
        similarity_threshold=0.3,
        max_results=10
    )

    # Test Psalm 23:1
    query = "יהוה רעי לא אחסר The LORD is my shepherd; I shall not want"

    print("Finding parallels for Psalm 23:1...")
    parallels = librarian.find_parallels(query)

    # Output to file
    with open("psalm_23_results.txt", "w", encoding="utf-8") as f:
        f.write("PSALM 23:1 THEMATIC SEARCH RESULTS\n")
        f.write("="*50 + "\n\n")
        f.write(f"Query: {query}\n")
        f.write(f"Found {len(parallels)} parallels:\n\n")

        psalm_23_found = False

        for i, parallel in enumerate(parallels, 1):
            f.write(f"{i}. {parallel.reference}\n")
            f.write(f"   Similarity: {parallel.similarity:.4f}\n")
            f.write(f"   Book: {parallel.book} ({parallel.book_category})\n")
            f.write(f"   Hebrew: {parallel.hebrew_text}\n\n")

            if "Psalm 23" in parallel.reference and i == 1:
                psalm_23_found = True

        f.write("-"*50 + "\n")
        f.write(f"RESULT: Psalm 23 is #1 match: {'YES' if psalm_23_found else 'NO'}\n")

    print("Results saved to psalm_23_results.txt")

    # Also print a simple version to console
    print("\nFirst 5 results:")
    for i, parallel in enumerate(parallels[:5], 1):
        marker = " <-- PSALM 23!" if "Psalm 23" in parallel.reference else ""
        print(f"{i}. {parallel.reference} (similarity: {parallel.similarity:.4f}){marker}")


if __name__ == "__main__":
    main()