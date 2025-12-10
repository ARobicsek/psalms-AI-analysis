#!/usr/bin/env python3
"""
Interactive tool to inspect and search the chunk corpus.

Usage:
    python scripts/inspect_chunks.py                    # Interactive mode
    python scripts/inspect_chunks.py --book Genesis     # Filter by book
    python scripts/inspect_chunks.py --search "shepherd" # Search chunks
    python scripts/inspect_chunks.py --ref "Genesis 22" # Find specific ref
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.thematic.corpus_builder import load_corpus, load_metadata


def main():
    parser = argparse.ArgumentParser(description="Inspect chunk corpus")
    parser.add_argument("--book", type=str, help="Filter by book name")
    parser.add_argument("--search", type=str, help="Search in chunk text")
    parser.add_argument("--ref", type=str, help="Find chunks containing reference")
    parser.add_argument("--limit", type=int, default=10, help="Max results to show")
    parser.add_argument("--full", action="store_true", help="Show full text (not truncated)")
    args = parser.parse_args()

    corpus_dir = Path(__file__).parent.parent / "data" / "thematic_corpus"

    # Load and filter chunks
    results = []
    for chunk in load_corpus(str(corpus_dir)):
        # Apply filters
        if args.book and chunk.book.lower() != args.book.lower():
            continue

        if args.search:
            search_lower = args.search.lower()
            if (search_lower not in chunk.hebrew_text.lower() and
                search_lower not in chunk.english_text.lower()):
                continue

        if args.ref:
            if args.ref.lower() not in chunk.reference.lower():
                continue

        results.append(chunk)

        if len(results) >= args.limit:
            break

    # Display results
    print(f"\nFound {len(results)} chunks" + (f" (limited to {args.limit})" if len(results) == args.limit else ""))
    print("="*70)

    for chunk in results:
        print(f"\n[{chunk.reference}]")
        print(f"   Book: {chunk.book} ({chunk.book_category.value})")
        print(f"   Type: {chunk.chunk_type.value}")
        print(f"   Verses: {chunk.verse_count}, Tokens: ~{chunk.token_estimate}")

        if args.full:
            print(f"\n   Hebrew:\n   {chunk.hebrew_text[:200]}...")
            if chunk.english_text:
                print(f"\n   English:\n   {chunk.english_text[:200]}...")
            else:
                print(f"\n   English: [None - Hebrew-only chunk]")
        else:
            # Skip displaying Hebrew text due to console issues
            # print(f"   Hebrew: {chunk.hebrew_text[:80]}...")
            if chunk.english_text:
                print(f"   English: {chunk.english_text[:100]}...")
            else:
                print(f"   English: [None - Hebrew-only chunk]")

        print("-"*70)


if __name__ == "__main__":
    main()