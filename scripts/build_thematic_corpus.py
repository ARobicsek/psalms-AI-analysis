#!/usr/bin/env python3
"""
Build the Tanakh chunk corpus for thematic parallel search.

Usage:
    python scripts/build_thematic_corpus.py
    python scripts/build_thematic_corpus.py --inspect  # View sample chunks
"""
import argparse
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.thematic.corpus_builder import CorpusBuilder, load_corpus, load_metadata

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Build thematic corpus")
    parser.add_argument("--inspect", action="store_true", help="Inspect existing corpus")
    parser.add_argument("--book", type=str, help="Only process specific book")
    parser.add_argument("--sample", type=int, default=5, help="Number of sample chunks to show")
    args = parser.parse_args()

    # Paths
    project_root = Path(__file__).parent.parent
    tanakh_db = project_root / "database" / "tanakh.db"
    output_dir = project_root / "data" / "thematic_corpus"

    if args.inspect:
        # Inspect existing corpus
        logger.info("Inspecting existing corpus...")

        metadata = load_metadata(str(output_dir))
        print("\n" + "="*60)
        print("CORPUS METADATA")
        print("="*60)
        print(f"Total chunks: {metadata.total_chunks}")
        print(f"Average verses per chunk: {metadata.avg_verse_count}")
        print(f"Average tokens per chunk: {metadata.avg_token_estimate}")
        print(f"\nChunks by category:")
        for cat, count in sorted(metadata.chunks_by_category.items()):
            print(f"  {cat}: {count}")
        print(f"\nChunks by type:")
        for typ, count in sorted(metadata.chunks_by_type.items()):
            print(f"  {typ}: {count}")

        print("\n" + "="*60)
        print(f"SAMPLE CHUNKS (first {args.sample})")
        print("="*60)

        for i, chunk in enumerate(load_corpus(str(output_dir))):
            if i >= args.sample:
                break
            print(f"\n--- Chunk {i+1}: {chunk.reference} ---")
            print(f"Type: {chunk.chunk_type.value}")
            print(f"Verses: {chunk.verse_count}")
            print(f"Hebrew (first 100 chars): {chunk.hebrew_text[:100]}...")
            print(f"English (first 100 chars): {chunk.english_text[:100]}...")

        return

    # Build corpus
    logger.info("Building thematic corpus...")
    logger.info(f"Database: {tanakh_db}")
    logger.info(f"Output: {output_dir}")

    builder = CorpusBuilder(
        tanakh_db_path=str(tanakh_db),
        output_dir=str(output_dir),
        window_size=5,
        window_overlap=4,
    )

    metadata = builder.build_corpus(
        exclude_psalms=True,
        use_sefaria_sections=True,
    )

    print("\n" + "="*60)
    print("BUILD COMPLETE")
    print("="*60)
    print(f"Total chunks: {metadata.total_chunks}")
    print(f"Output directory: {output_dir}")
    print("\nRun with --inspect to view sample chunks")


if __name__ == "__main__":
    main()