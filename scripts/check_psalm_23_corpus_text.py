#!/usr/bin/env python3
"""
Check what the actual Hebrew text is in the Psalm 23 chunks.
"""
import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.thematic_parallels_librarian import ThematicParallelsLibrarian


def main():
    # Create librarian
    librarian = ThematicParallelsLibrarian(similarity_threshold=0.1, max_results=50)

    # Search for any Psalm 23 content
    query = "יהוה רעי"
    parallels = librarian.find_parallels(query)

    # Find Psalm 23 chunks
    psalm_23_chunks = []
    for p in parallels:
        if "Psalm 23" in p.reference:
            psalm_23_chunks.append(p)

    # Output to file
    with open("psalm_23_corpus_text.txt", "w", encoding="utf-8") as f:
        f.write("PSALM 23 CHUNKS IN CORPUS\n")
        f.write("="*50 + "\n\n")

        f.write(f"Found {len(psalm_23_chunks)} Psalm 23 chunks:\n\n")

        for i, chunk in enumerate(psalm_23_chunks, 1):
            f.write(f"{i}. {chunk.reference}\n")
            f.write(f"   Hebrew text: {chunk.hebrew_text}\n")
            f.write(f"   Length: {len(chunk.hebrew_text)} chars\n")
            f.write(f"   Context verses: {chunk.context_verses}\n\n")

        # Also show the first 100 chars of each to see variations
        f.write("FIRST 100 CHARACTERS OF EACH CHUNK:\n")
        f.write("-"*40 + "\n\n")

        for i, chunk in enumerate(psalm_23_chunks, 1):
            preview = chunk.hebrew_text[:100]
            f.write(f"{i}. {chunk.reference}:\n")
            f.write(f"   {preview}...\n\n")

    print(f"Found {len(psalm_23_chunks)} Psalm 23 chunks")
    print("Details saved to psalm_23_corpus_text.txt")


if __name__ == "__main__":
    main()