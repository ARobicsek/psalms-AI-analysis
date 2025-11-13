"""
Get Psalm Lengths (Word Counts)

Calculates word counts for all 150 Psalms from the concordance database.
Stores results in a JSON file for use by the enhanced scoring system.
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
TANAKH_DB_PATH = Path(__file__).parent.parent.parent / "database" / "tanakh.db"
OUTPUT_PATH = Path(__file__).parent.parent.parent / "data" / "analysis_results" / "psalm_word_counts.json"


def get_psalm_word_counts() -> Dict[int, int]:
    """
    Calculate word counts for all 150 Psalms from concordance database.

    Returns:
        Dictionary mapping psalm number to word count
    """
    logger.info(f"Connecting to database: {TANAKH_DB_PATH}")

    if not TANAKH_DB_PATH.exists():
        raise FileNotFoundError(f"Tanakh database not found at {TANAKH_DB_PATH}")

    conn = sqlite3.connect(str(TANAKH_DB_PATH))
    cursor = conn.cursor()

    # Get word counts for each psalm from concordance
    # Count distinct (chapter_number, verse_number, word_index) combinations
    logger.info("Querying concordance for word counts...")

    cursor.execute("""
        SELECT chapter, COUNT(*) as word_count
        FROM concordance
        WHERE book_name = 'Psalms'
        GROUP BY chapter
        ORDER BY chapter
    """)

    results = cursor.fetchall()
    conn.close()

    # Convert to dictionary
    word_counts = {row[0]: row[1] for row in results}

    # Validate we have all 150 psalms
    if len(word_counts) != 150:
        logger.warning(f"Expected 150 psalms, found {len(word_counts)}")
        missing = set(range(1, 151)) - set(word_counts.keys())
        if missing:
            logger.warning(f"Missing psalms: {sorted(missing)}")

    return word_counts


def calculate_statistics(word_counts: Dict[int, int]) -> Dict[str, any]:
    """Calculate summary statistics for word counts."""
    counts = list(word_counts.values())

    return {
        "total_psalms": len(word_counts),
        "total_words": sum(counts),
        "min_words": min(counts),
        "max_words": max(counts),
        "mean_words": sum(counts) / len(counts),
        "median_words": sorted(counts)[len(counts) // 2],
    }


def main():
    """Main execution."""
    logger.info("=" * 60)
    logger.info("PSALM WORD COUNT EXTRACTION")
    logger.info("=" * 60)

    # Get word counts
    word_counts = get_psalm_word_counts()

    # Calculate statistics
    stats = calculate_statistics(word_counts)

    logger.info(f"\nStatistics:")
    logger.info(f"  Total Psalms: {stats['total_psalms']}")
    logger.info(f"  Total Words: {stats['total_words']:,}")
    logger.info(f"  Min Words: {stats['min_words']} (Psalm {min(word_counts, key=word_counts.get)})")
    logger.info(f"  Max Words: {stats['max_words']} (Psalm {max(word_counts, key=word_counts.get)})")
    logger.info(f"  Mean Words: {stats['mean_words']:.1f}")
    logger.info(f"  Median Words: {stats['median_words']}")

    # Show some examples
    logger.info(f"\nExample word counts:")
    for psalm_num in [1, 23, 119]:
        if psalm_num in word_counts:
            logger.info(f"  Psalm {psalm_num}: {word_counts[psalm_num]} words")

    # Save to JSON
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "word_counts": word_counts,
        "statistics": stats,
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    logger.info(f"\n✓ Word counts saved to: {OUTPUT_PATH}")
    logger.info(f"  File size: {OUTPUT_PATH.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
