#!/usr/bin/env python3
"""Analyze Masoretic marker coverage across the Tanakh."""

import sys
from pathlib import Path
import statistics

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thematic.corpus_builder import load_corpus, load_metadata

def analyze_chunks(chunks):
    """Analyze chunk sizes for potential issues."""
    sizes = [c.verse_count for c in chunks]

    # Basic stats
    min_size = min(sizes)
    max_size = max(sizes)
    median_size = statistics.median(sizes)
    avg_size = sum(sizes) / len(sizes)

    # Problematic chunks
    very_large = [c for c in chunks if c.verse_count > 20]
    very_small = [c for c in chunks if c.verse_count == 1]

    return {
        'count': len(chunks),
        'min_size': min_size,
        'max_size': max_size,
        'median_size': median_size,
        'avg_size': avg_size,
        'very_large': very_large,
        'very_small': very_small,
        'pct_very_large': len(very_large) / len(chunks) * 100,
        'pct_very_small': len(very_small) / len(chunks) * 100
    }

def main():
    # Load the Masoretic corpus
    corpus_dir = Path(__file__).parent.parent / "data" / "thematic_corpus_masoretic"
    chunks = list(load_corpus(str(corpus_dir)))
    metadata = load_metadata(str(corpus_dir))

    print("MASORETIC MARKER ANALYSIS")
    print("=" * 60)

    # Group by book
    books = {}
    for chunk in chunks:
        if chunk.book not in books:
            books[chunk.book] = []
        books[chunk.book].append(chunk)

    print("\nBOOK-BY-BOOK ANALYSIS:")
    print("-" * 60)
    print(f"{'Book':<15} {'Chunks':<8} {'Min':<5} {'Max':<5} {'Median':<7} {'Avg':<5} {'>20v':<6} {'1v':<6}")
    print("-" * 60)

    problematic_books = []

    for book in sorted(books.keys()):
        book_chunks = books[book]
        stats = analyze_chunks(book_chunks)

        # Mark problematic books
        is_problematic = stats['max_size'] > 50 or stats['pct_very_large'] > 5 or stats['pct_very_small'] > 80
        if is_problematic:
            problematic_books.append(book)
            prefix = "* "
        else:
            prefix = "  "

        print(f"{prefix}{book:<15} {stats['count']:<8} {stats['min_size']:<5} {stats['max_size']:<5} "
              f"{stats['median_size']:<7.1f} {stats['avg_size']:<5.1f} {len(stats['very_large']):<6} "
              f"{len(stats['very_small']):<6}")

    print("\n* Potentially problematic books")

    # Show worst examples
    print("\n" + "=" * 60)
    print("LARGEST CHUNKS (>30 verses):")
    print("-" * 60)

    all_large = sorted(chunks, key=lambda x: x.verse_count, reverse=True)[:10]
    for chunk in all_large:
        print(f"{chunk.book} {chunk.reference}: {chunk.verse_count} verses")

    # Books with no markers
    print("\n" + "=" * 60)
    print("BOOKS WITH POTENTIAL ISSUES:")
    print("-" * 60)

    # Check for books that might have sparse markers
    for book in sorted(books.keys()):
        book_chunks = books[book]
        stats = analyze_chunks(book_chunks)

        issues = []
        if stats['max_size'] > 50:
            issues.append(f"Very large chunks (max: {stats['max_size']} verses)")
        if stats['pct_very_large'] > 5:
            issues.append(f"{stats['pct_very_large']:.1f}% chunks >20 verses")
        if stats['pct_very_small'] > 80:
            issues.append(f"{stats['pct_very_small']:.1f}% single verses")

        if issues:
            print(f"\n{book}:")
            for issue in issues:
                print(f"  - {issue}")

    # Specific check for very sparse marking
    print("\n" + "=" * 60)
    print("BOOKS WITH SPARSE MARKERS (few chunks):")
    print("-" * 60)

    sparse_books = [(book, len(chunks)) for book, chunks in books.items() if len(chunks) < 20]
    sparse_books.sort(key=lambda x: x[1])

    for book, count in sparse_books:
        print(f"{book}: {count} chunks total")
        # Show average
        book_chunks = books[book]
        avg_verses = sum(c.verse_count for c in book_chunks) / len(book_chunks)
        print(f"  Average: {avg_verses:.1f} verses per chunk")

if __name__ == "__main__":
    main()