#!/usr/bin/env python3
"""
Test the Thematic Parallels Librarian.

This script tests the thematic parallel search functionality with sample queries.
"""
import argparse
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.thematic_parallels_librarian import create_thematic_librarian

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_psalm_23(librarian):
    """Test Psalm 23 - Shepherd imagery."""
    print("\n" + "="*80)
    print("TEST: Psalm 23:1 - 'The Lord is my shepherd'")
    print("="*80)

    hebrew = "יהוה רעי לא אחסר"
    english = "The Lord is my shepherd; I shall not want"

    parallels = librarian.find_parallels(hebrew + " " + english)

    print(f"\nFound {len(parallels)} parallels:")
    for i, parallel in enumerate(parallels[:5], 1):
        print(f"\n{i}. {parallel.reference}")
        print(f"   Similarity: {parallel.similarity:.3f}")
        print(f"   Book: {parallel.book} ({parallel.book_category})")
        print(f"   Hebrew: {parallel.hebrew_text[:150]}...")


def test_psalm_139(librarian):
    """Test Psalm 139 - Creation in womb."""
    print("\n" + "="*80)
    print("TEST: Psalm 139:13 - 'You knit me in my mother's womb'")
    print("="*80)

    hebrew = "כי אתה קראתי במעי תצרני"
    english = "For you created my inmost being; you knit me together in my mother's womb"

    parallels = librarian.find_parallels(hebrew + " " + english)

    print(f"\nFound {len(parallels)} parallels:")
    for i, parallel in enumerate(parallels[:5], 1):
        print(f"\n{i}. {parallel.reference}")
        print(f"   Similarity: {parallel.similarity:.3f}")
        print(f"   Book: {parallel.book} ({parallel.book_category})")
        print(f"   Hebrew: {parallel.hebrew_text[:150]}...")


def test_psalm_1(librarian):
    """Test Psalm 1 - Tree by water."""
    print("\n" + "="*80)
    print("TEST: Psalm 1:3 - 'Tree planted by streams of water'")
    print("="*80)

    hebrew = "והיה כעץ שתול על פלגי מים"
    english = "That person is like a tree planted by streams of water"

    parallels = librarian.find_parallels(hebrew + " " + english)

    print(f"\nFound {len(parallels)} parallels:")
    for i, parallel in enumerate(parallels[:5], 1):
        print(f"\n{i}. {parallel.reference}")
        print(f"   Similarity: {parallel.similarity:.3f}")
        print(f"   Book: {parallel.book} ({parallel.book_category})")
        print(f"   Hebrew: {parallel.hebrew_text[:150]}...")


def test_psalm_73(librarian):
    """Test Psalm 73 - Prosperity of the wicked."""
    print("\n" + "="*80)
    print("TEST: Psalm 73:3 - 'The wicked seem to have no burdens'")
    print("="*80)

    hebrew = "כי קנאתי להוללים שלום רשעים ראיתי"
    english = "For I envied the arrogant when I saw the prosperity of the wicked"

    parallels = librarian.find_parallels(hebrew + " " + english)

    print(f"\nFound {len(parallels)} parallels:")
    for i, parallel in enumerate(parallels[:5], 1):
        print(f"\n{i}. {parallel.reference}")
        print(f"   Similarity: {parallel.similarity:.3f}")
        print(f"   Book: {parallel.book} ({parallel.book_category})")
        print(f"   Hebrew: {parallel.hebrew_text[:150]}...")


def main():
    parser = argparse.ArgumentParser(description="Test thematic parallels retrieval")
    parser.add_argument(
        "--psalm",
        type=int,
        choices=[1, 23, 73, 139],
        help="Test specific psalm (1, 23, 73, or 139)"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Custom query text (Hebrew or English)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Similarity threshold (default: 0.7)"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum results (default: 10)"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock embeddings instead of OpenAI"
    )

    args = parser.parse_args()

    # Create librarian
    print("Creating Thematic Parallels Librarian...")
    librarian = create_thematic_librarian(
        embedding_provider="mock" if args.mock else "openai",
        similarity_threshold=args.threshold,
        max_results=args.max_results
    )

    # Print statistics
    stats = librarian.get_statistics()
    print("\nVector Store Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Run tests
    if args.query:
        print("\n" + "="*80)
        print(f"CUSTOM QUERY: {args.query}")
        print("="*80)
        parallels = librarian.find_parallels(args.query)
        print(f"\nFound {len(parallels)} parallels:")
        for i, parallel in enumerate(parallels, 1):
            print(f"\n{i}. {parallel.reference}")
            print(f"   Similarity: {parallel.similarity:.3f}")
            print(f"   Book: {parallel.book} ({parallel.book_category})")
            print(f"   Hebrew: {parallel.hebrew_text[:150]}...")
    elif args.psalm:
        if args.psalm == 1:
            test_psalm_1(librarian)
        elif args.psalm == 23:
            test_psalm_23(librarian)
        elif args.psalm == 73:
            test_psalm_73(librarian)
        elif args.psalm == 139:
            test_psalm_139(librarian)
    else:
        # Run all tests
        print("\nRunning all test cases...")
        test_psalm_23(librarian)
        test_psalm_139(librarian)
        test_psalm_1(librarian)
        test_psalm_73(librarian)

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()