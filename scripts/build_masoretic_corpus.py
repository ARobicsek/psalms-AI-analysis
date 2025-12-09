#!/usr/bin/env python3
"""Build corpus using Masoretic marker chunking for comparison."""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thematic.corpus_builder import CorpusBuilder

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def main():
    """Build corpus with Masoretic marker chunking."""
    # Paths
    db_path = Path(__file__).parent.parent / "database" / "tanakh.db"
    output_dir = Path(__file__).parent.parent / "data" / "thematic_corpus_masoretic"

    print(f"Building corpus with Masoretic marker chunking...")
    print(f"Database: {db_path}")
    print(f"Output: {output_dir}")
    print()

    # Create builder
    builder = CorpusBuilder(
        tanakh_db_path=str(db_path),
        output_dir=str(output_dir),
        window_size=5,
        window_overlap=2,
    )

    # Build corpus with Masoretic markers
    metadata = builder.build_corpus(
        exclude_psalms=True,  # Skip Psalms
        use_sefaria_sections=False,  # Don't use Sefaria sections
        use_masoretic_markers=True,  # Use Masoretic markers
    )

    # Display statistics
    print("\nCorpus Statistics:")
    print(f"  Total chunks: {metadata.total_chunks}")
    print(f"  Average verses per chunk: {metadata.avg_verse_count:.1f}")
    print(f"  Average tokens per chunk: {metadata.avg_token_estimate:.0f}")
    print()
    print("Chunks by book:")
    for book, count in sorted(metadata.chunks_by_book.items()):
        print(f"  {book}: {count}")
    print()
    print("Chunks by category:")
    for category, count in sorted(metadata.chunks_by_category.items()):
        print(f"  {category}: {count}")

    print(f"\nCorpus saved to: {output_dir}")
    print("  - tanakh_chunks.jsonl")
    print("  - chunk_metadata.json")

if __name__ == "__main__":
    main()