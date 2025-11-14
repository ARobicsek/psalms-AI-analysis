"""
Generate Top 500 Detailed Connections with Skipgram-Aware Deduplication V2

Changes from top 300 V1:
1. Generates top 500 connections (up from 300)
2. Includes deduplicated skipgrams in output (not just counts)
3. Uses V2 scoring with IDF filter for common roots

Creates comprehensive JSON showing top 500 connections using skipgram-aware
deduplicated scores where no word is counted more than once.
"""

import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Generate detailed top 500 connections with skipgram-aware deduplicated scoring V2."""

    base_dir = Path(__file__).parent.parent.parent

    # Load skipgram-aware deduplicated scores V2
    logger.info("Loading skipgram-aware deduplicated scores V2...")
    input_file = base_dir / "data/analysis_results/enhanced_scores_skipgram_dedup_v2.json"

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please run enhanced_scorer_skipgram_dedup_v2.py first.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        deduplicated_scores = json.load(f)
    logger.info(f"  Loaded {len(deduplicated_scores)} scored relationships")

    # Sort by final_score descending and take top 500
    logger.info("Sorting by final_score and selecting top 500...")
    sorted_scores = sorted(
        deduplicated_scores,
        key=lambda x: x['final_score'],
        reverse=True
    )

    # Handle case where there are fewer than 500 relationships
    n_connections = min(500, len(sorted_scores))
    top_500 = sorted_scores[:n_connections]

    logger.info(f"  Selected top {n_connections} connections")
    logger.info(f"  Score range: {top_500[0]['final_score']:.2f} to {top_500[-1]['final_score']:.2f}")

    # Add rank to each entry
    logger.info("Adding rank and preparing output...")
    top_500_detailed = []

    for i, entry in enumerate(top_500, 1):
        detailed_entry = {
            # Basic identification
            "rank": i,
            "psalm_a": entry['psalm_a'],
            "psalm_b": entry['psalm_b'],

            # Deduplication impact
            "deduplication_stats": {
                "contiguous": {
                    "original_count": entry['original_phrase_count'],
                    "deduplicated_count": entry['deduplicated_contiguous_count'],
                    "removed_as_substrings": entry['phrases_removed_as_substrings']
                },
                "skipgrams": {
                    "original_count": entry['original_skipgram_count'],
                    "original_2word": entry['original_skipgram_2'],
                    "original_3word": entry['original_skipgram_3'],
                    "original_4plus": entry['original_skipgram_4plus'],
                    "deduplicated_count": entry['deduplicated_skipgram_count'],
                    "deduplicated_2word": entry['deduplicated_skipgram_2'],
                    "deduplicated_3word": entry['deduplicated_skipgram_3'],
                    "deduplicated_4plus": entry['deduplicated_skipgram_4plus'],
                    "estimated_2word": entry.get('estimated_skipgram_2', 0),
                    "estimated_3word": entry.get('estimated_skipgram_3', 0),
                    "estimated_4plus": entry.get('estimated_skipgram_4plus', 0)
                },
                "roots": {
                    "original_count": entry['original_root_count'],
                    "deduplicated_count": entry['deduplicated_root_count'],
                    "in_contiguous_phrases": entry['roots_in_contiguous'],
                    "in_skipgrams": entry['roots_in_skipgrams'],
                    "filtered_by_idf": entry['roots_filtered_by_idf'],
                    "total_removed": entry['total_roots_removed']
                }
            },

            # Pattern counts (deduplicated)
            "contiguous_2word": entry['contiguous_2word'],
            "contiguous_3word": entry['contiguous_3word'],
            "contiguous_4plus": entry['contiguous_4plus'],
            "skipgram_2word_dedup": entry['skipgram_2word_dedup'],
            "skipgram_3word_dedup": entry['skipgram_3word_dedup'],
            "skipgram_4plus_dedup": entry['skipgram_4plus_dedup'],
            "total_pattern_points": entry['total_pattern_points'],

            # Root statistics (deduplicated - excludes roots in phrases and IDF < 0.5)
            "shared_roots_count": entry['shared_roots_count'],
            "root_idf_sum": entry['root_idf_sum'],

            # Psalm lengths
            "word_count_a": entry['word_count_a'],
            "word_count_b": entry['word_count_b'],
            "geometric_mean_length": entry['geometric_mean_length'],

            # Scores
            "phrase_score": entry['phrase_score'],
            "root_score": entry['root_score'],
            "final_score": entry['final_score'],

            # Original statistics
            "original_pvalue": entry['original_pvalue'],
            "original_rank": entry['original_rank'],

            # DETAILED MATCHES (deduplicated)
            "deduplicated_contiguous_phrases": entry['deduplicated_contiguous_phrases'],
            "deduplicated_skipgrams": entry['deduplicated_skipgrams'],
            "deduplicated_roots": entry['deduplicated_roots']
        }

        top_500_detailed.append(detailed_entry)

        if i % 100 == 0:
            logger.info(f"  Processed {i}/{n_connections} connections...")

    # Save output
    output_path = base_dir / "data/analysis_results/top_500_connections_skipgram_dedup_v2.json"
    logger.info(f"Saving detailed top {n_connections} to {output_path}...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(top_500_detailed, f, indent=2, ensure_ascii=False)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"  File size: {file_size_mb:.2f} MB")

    # Summary statistics
    logger.info("\nSummary:")
    logger.info(f"  Total entries: {len(top_500_detailed)}")
    logger.info(f"  Rank 1: Psalms {top_500_detailed[0]['psalm_a']}-{top_500_detailed[0]['psalm_b']} (score: {top_500_detailed[0]['final_score']:.2f})")
    logger.info(f"  Rank {n_connections}: Psalms {top_500_detailed[-1]['psalm_a']}-{top_500_detailed[-1]['psalm_b']} (score: {top_500_detailed[-1]['final_score']:.2f})")

    # Deduplication stats across all entries
    total_contiguous_removed = sum(e['deduplication_stats']['contiguous']['removed_as_substrings'] for e in top_500_detailed)
    total_skipgrams_removed = sum(
        e['deduplication_stats']['skipgrams']['original_count'] - e['deduplication_stats']['skipgrams']['deduplicated_count']
        for e in top_500_detailed
    )
    total_roots_removed = sum(e['deduplication_stats']['roots']['total_removed'] for e in top_500_detailed)
    total_roots_filtered_idf = sum(e['deduplication_stats']['roots']['filtered_by_idf'] for e in top_500_detailed)

    # Actual deduplicated counts
    total_dedup_contiguous = sum(len(e['deduplicated_contiguous_phrases']) for e in top_500_detailed)
    total_dedup_skipgrams = sum(len(e['deduplicated_skipgrams']) for e in top_500_detailed)
    total_dedup_roots = sum(len(e['deduplicated_roots']) for e in top_500_detailed)

    logger.info(f"\nDeduplication impact across top {n_connections}:")
    logger.info(f"  Contiguous phrases removed as substrings: {total_contiguous_removed:,}")
    logger.info(f"  Skipgrams removed (overlap + subpatterns): {total_skipgrams_removed:,}")
    logger.info(f"  Roots removed (in phrases): {total_roots_removed - total_roots_filtered_idf:,}")
    logger.info(f"  Roots filtered (IDF < 0.5): {total_roots_filtered_idf:,}")
    logger.info(f"  Total roots removed: {total_roots_removed:,}")

    logger.info(f"\nActual deduplicated matches in top {n_connections}:")
    logger.info(f"  Contiguous phrases: {total_dedup_contiguous:,} (avg {total_dedup_contiguous/n_connections:.1f} per connection)")
    logger.info(f"  Skipgrams: {total_dedup_skipgrams:,} (avg {total_dedup_skipgrams/n_connections:.1f} per connection)")
    logger.info(f"  Roots: {total_dedup_roots:,} (avg {total_dedup_roots/n_connections:.1f} per connection)")

    logger.info("\n✓ Complete!")
    logger.info(f"Output saved to: {output_path}")


if __name__ == "__main__":
    main()
