#!/usr/bin/env python3
"""
Simple test of ThematicParallelsLibrarian
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from src.agents.thematic_parallels_librarian import create_thematic_librarian

def main():
    print("Testing ThematicParallelsLibrarian")
    print("=" * 50)

    # Create librarian with lower threshold for testing
    librarian = create_thematic_librarian(similarity_threshold=0.5)

    # Get statistics
    stats = librarian.get_statistics()
    print(f"\nVector Store Stats:")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Embedding model: {stats['embedding_model']}")
    print(f"  Embedding dimension: {stats['embedding_dimension']}")
    print(f"  Similarity threshold: {stats['similarity_threshold']}")

    # Test with a simple query
    print("\nTesting query: 'שמש וירח' (sun and moon)")
    parallels = librarian.find_parallels("שמש וירח")

    if parallels:
        print(f"\n✅ Found {len(parallels)} parallels")
        for i, parallel in enumerate(parallels[:3], 1):
            print(f"\n{i}. {parallel.reference}")
            print(f"   Similarity: {parallel.similarity:.3f}")
            print(f"   Hebrew: {parallel.hebrew_text[:100]}...")
    else:
        print("\n❌ No parallels found")

    # Test with Psalm 23 first verse
    print("\n\nTesting query: First verse of Psalm 23")
    query = "יהוה רעי לא אחסר"
    parallels = librarian.find_parallels(query)

    if parallels:
        print(f"\n✅ Found {len(parallels)} parallels")
        for i, parallel in enumerate(parallels[:3], 1):
            print(f"\n{i}. {parallel.reference}")
            print(f"   Similarity: {parallel.similarity:.3f}")
            print(f"   Category: {parallel.book_category}")
            print(f"   Hebrew: {parallel.hebrew_text[:100]}...")
    else:
        print("\n❌ No parallels found")

if __name__ == "__main__":
    main()