#!/usr/bin/env python3
"""Inspect Masoretic marker chunks for quality assessment."""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thematic.corpus_builder import load_corpus

def print_chunk(chunk, show_hebrew=False, show_english=True):
    """Print a chunk with its metadata."""
    print(f"\n{'='*60}")
    print(f"Reference: {chunk.reference}")
    print(f"Book: {chunk.book} ({chunk.book_category.value})")
    print(f"Type: {chunk.chunk_type.value}")
    print(f"Verses: {chunk.verse_count}")
    print(f"Tokens: {chunk.token_estimate}")

    if show_hebrew:
        print(f"\nHebrew:")
        print(chunk.hebrew_text[:500] + ("..." if len(chunk.hebrew_text) > 500 else ""))

    if show_english:
        print(f"\nEnglish:")
        print(chunk.english_text[:500] + ("..." if len(chunk.english_text) > 500 else ""))

def main():
    parser = argparse.ArgumentParser(description="Inspect Masoretic chunks")
    parser.add_argument("--book", help="Filter by book name")
    parser.add_argument("--limit", type=int, default=10, help="Number of chunks to show")
    parser.add_argument("--hebrew", action="store_true", help="Show Hebrew text")
    parser.add_argument("--english", action="store_true", default=True, help="Show English text")
    parser.add_argument("--search", help="Search for text in chunks")

    args = parser.parse_args()

    # Load corpus
    corpus_dir = Path(__file__).parent.parent / "data" / "thematic_corpus_masoretic"
    chunks = list(load_corpus(str(corpus_dir)))

    # Filter
    if args.book:
        chunks = [c for c in chunks if c.book.lower() == args.book.lower()]
        print(f"Filtered to {len(chunks)} chunks from {args.book}")

    if args.search:
        chunks = [c for c in chunks if args.search.lower() in c.english_text.lower()]
        print(f"Found {len(chunks)} chunks containing '{args.search}'")

    # Show limited number
    chunks = chunks[:args.limit]

    # Display
    print(f"\nShowing {len(chunks)} chunks:")

    for chunk in chunks:
        print_chunk(chunk, show_hebrew=args.hebrew, show_english=args.english)

if __name__ == "__main__":
    main()