#!/usr/bin/env python3
"""
Test if Psalm 23 appears as #1 match for its verses.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.thematic_parallels_librarian import ThematicParallelsLibrarian


def main():
    # Create librarian
    librarian = ThematicParallelsLibrarian(
        similarity_threshold=0.3,
        max_results=10
    )

    # Test each verse
    print("TESTING PSALM 23 SELF-REFERENCES")
    print("="*50)

    # Psalm 23:1
    query1 = "The LORD is my shepherd"
    parallels1 = librarian.find_parallels(query1)
    print("\nPsalm 23:1 - 'The LORD is my shepherd'")
    print(f"Top match: {parallels1[0].reference if parallels1 else 'None'}")
    similarity1 = parallels1[0].similarity if parallels1 else 0
    print(f"Similarity: {similarity1:.4f}")
    is_psalm_23_1 = parallels1 and ("Psalm 23" in parallels1[0].reference or "Psalms 23" in parallels1[0].reference)
    print(f"Psalm 23 is #1: {is_psalm_23_1}")

    # Psalm 23:4
    query4 = "valley of the shadow of death"
    parallels4 = librarian.find_parallels(query4)
    print("\nPsalm 23:4 - 'valley of the shadow of death'")
    print(f"Top match: {parallels4[0].reference if parallels4 else 'None'}")
    similarity4 = parallels4[0].similarity if parallels4 else 0
    print(f"Similarity: {similarity4:.4f}")
    is_psalm_23_4 = parallels4 and ("Psalm 23" in parallels4[0].reference or "Psalms 23" in parallels4[0].reference)
    print(f"Psalm 23 is #1: {is_psalm_23_4}")

    # Psalm 23:5
    query5 = "preparest a table before me"
    parallels5 = librarian.find_parallels(query5)
    print("\nPsalm 23:5 - 'preparest a table before me'")
    print(f"Top match: {parallels5[0].reference if parallels5 else 'None'}")
    similarity5 = parallels5[0].similarity if parallels5 else 0
    print(f"Similarity: {similarity5:.4f}")
    is_psalm_23_5 = parallels5 and ("Psalm 23" in parallels5[0].reference or "Psalms 23" in parallels5[0].reference)
    print(f"Psalm 23 is #1: {is_psalm_23_5}")

    # Summary
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"Psalm 23:1 - {'PASS' if is_psalm_23_1 else 'FAIL'}")
    print(f"Psalm 23:4 - {'PASS' if is_psalm_23_4 else 'FAIL'}")
    print(f"Psalm 23:5 - {'PASS' if is_psalm_23_5 else 'FAIL'}")
    all_passed = is_psalm_23_1 and is_psalm_23_4 and is_psalm_23_5
    print(f"\nOverall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")


if __name__ == "__main__":
    main()