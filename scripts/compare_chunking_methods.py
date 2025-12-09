#!/usr/bin/env python3
"""Compare sliding window vs Masoretic marker chunking methods."""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thematic.corpus_builder import load_corpus, load_metadata

def print_chunk_preview(chunk, max_verses=3):
    """Print a preview of a chunk."""
    print(f"  Reference: {chunk.reference}")
    print(f"  Verses: {chunk.verse_count}")
    print(f"  Tokens: {chunk.token_estimate}")

    # Show first few verses
    lines = chunk.english_text.split('\n')
    for i, line in enumerate(lines[:max_verses]):
        print(f"    {line}")
    if len(lines) > max_verses:
        print(f"    ... ({len(lines)-max_verses} more verses)")
    print()

def compare_book(book_name: str, sliding_chunks, masoretic_chunks):
    """Compare chunks for a specific book."""
    print(f"\n=== {book_name} ===\n")

    # Get chunks for this book
    sliding_book = [c for c in sliding_chunks if c.book == book_name][:3]
    masoretic_book = [c for c in masoretic_chunks if c.book == book_name][:3]

    print(f"Sliding Window (first 3 chunks):")
    print("-" * 40)
    for chunk in sliding_book:
        print_chunk_preview(chunk)

    print(f"\nMasoretic Markers (first 3 chunks):")
    print("-" * 40)
    for chunk in masoretic_book:
        print_chunk_preview(chunk)

def main():
    """Compare the two chunking methods."""
    # Paths
    sliding_dir = Path(__file__).parent.parent / "data" / "thematic_corpus"
    masoretic_dir = Path(__file__).parent.parent / "data" / "thematic_corpus_masoretic"

    print("Loading corpora...")

    # Load corpora
    sliding_chunks = list(load_corpus(str(sliding_dir)))
    masoretic_chunks = list(load_corpus(str(masoretic_dir)))

    # Load metadata
    sliding_meta = load_metadata(str(sliding_dir))
    masoretic_meta = load_metadata(str(masoretic_dir))

    # Overall comparison
    print("\n" + "="*60)
    print("OVERALL COMPARISON")
    print("="*60)

    print(f"\nSliding Window Corpus:")
    print(f"  Total chunks: {sliding_meta.total_chunks}")
    print(f"  Average verses per chunk: {sliding_meta.avg_verse_count:.1f}")
    print(f"  Average tokens per chunk: {sliding_meta.avg_token_estimate:.0f}")

    print(f"\nMasoretic Marker Corpus:")
    print(f"  Total chunks: {masoretic_meta.total_chunks}")
    print(f"  Average verses per chunk: {masoretic_meta.avg_verse_count:.1f}")
    print(f"  Average tokens per chunk: {masoretic_meta.avg_token_estimate:.0f}")

    # Key differences
    print("\nKey Differences:")
    print(f"  • Masoretic creates {masoretic_meta.total_chunks - sliding_meta.total_chunks:,} MORE chunks")
    print(f"  • Average chunk size: Masoretic ({masoretic_meta.avg_verse_count:.1f} verses) vs Sliding ({sliding_meta.avg_verse_count:.1f} verses)")
    print(f"  • Masoretic chunks are more granular, following traditional section breaks")

    # Book-by-book comparison for selected books
    print("\n" + "="*60)
    print("SELECTED BOOK COMPARISON")
    print("="*60)

    # Compare Genesis (Torah)
    compare_book("Genesis", sliding_chunks, masoretic_chunks)

    # Compare Isaiah (Prophets)
    compare_book("Isaiah", sliding_chunks, masoretic_chunks)

    # Compare Job (Writings)
    compare_book("Job", sliding_chunks, masoretic_chunks)

    # Analyze chunk size distribution
    print("\n" + "="*60)
    print("CHUNK SIZE ANALYSIS")
    print("="*60)

    # Sliding window distribution
    sliding_sizes = [c.verse_count for c in sliding_chunks]
    masoretic_sizes = [c.verse_count for c in masoretic_chunks]

    print("\nSliding Window - Verse count distribution:")
    print(f"  Min: {min(sliding_sizes)} verses")
    print(f"  Max: {max(sliding_sizes)} verses")
    print(f"  Median: {sorted(sliding_sizes)[len(sliding_sizes)//2]} verses")

    print("\nMasoretic Markers - Verse count distribution:")
    print(f"  Min: {min(masoretic_sizes)} verses")
    print(f"  Max: {max(masoretic_sizes)} verses")
    print(f"  Median: {sorted(masoretic_sizes)[len(masoretic_sizes)//2]} verses")

    # Show distribution ranges
    print("\nMasoretic chunk breakdown:")
    single_verses = sum(1 for s in masoretic_sizes if s == 1)
    two_verses = sum(1 for s in masoretic_sizes if s == 2)
    three_plus = sum(1 for s in masoretic_sizes if s >= 3)

    print(f"  1-verse chunks: {single_verses:,} ({single_verses/len(masoretic_sizes)*100:.1f}%)")
    print(f"  2-verse chunks: {two_verses:,} ({two_verses/len(masoretic_sizes)*100:.1f}%)")
    print(f"  3+ verse chunks: {three_plus:,} ({three_plus/len(masoretic_sizes)*100:.1f}%)")

    print("\n" + "="*60)
    print("RECOMMENDATION")
    print("="*60)
    print("""
The Masoretic marker chunking has advantages:
• Follows traditional paragraph boundaries established over centuries
• Creates more focused, thematically coherent chunks
• 75% of chunks are 1-2 verses, providing precise thematic units
• Aligns with how Jewish scholars have traditionally read the text

The sliding window approach:
• Creates consistent 5-verse chunks with overlap
• Simpler to implement
• May cut across thematic boundaries

Consider: Masoretic chunking appears superior for thematic parallels
as it respects the text's own internal structure.
    """)

if __name__ == "__main__":
    main()