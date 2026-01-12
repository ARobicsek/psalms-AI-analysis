"""
Generate Top 300 Detailed Connections with Skipgram-Aware Deduplication

Creates comprehensive JSON showing top 300 connections using skipgram-aware
deduplicated scores where no word is counted more than once.
"""

import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Generate detailed top 300 connections with skipgram-aware deduplicated scoring."""

    base_dir = Path(__file__).parent.parent.parent

    # Load skipgram-aware deduplicated scores
    logger.info("Loading skipgram-aware deduplicated scores...")
    with open(base_dir / "data/analysis_results/enhanced_scores_skipgram_dedup.json", 'r', encoding='utf-8') as f:
        deduplicated_scores = json.load(f)
    logger.info(f"  Loaded {len(deduplicated_scores)} scored relationships")

    # Sort by final_score descending and take top 300
    logger.info("Sorting by final_score and selecting top 300...")
    sorted_scores = sorted(
        deduplicated_scores,
        key=lambda x: x['final_score'],
        reverse=True
    )
    top_300 = sorted_scores[:300]
    logger.info(f"  Selected top 300 connections")
    logger.info(f"  Score range: {top_300[0]['final_score']:.2f} to {top_300[-1]['final_score']:.2f}")

    # Add rank to each entry
    logger.info("Adding rank and preparing output...")
    top_300_detailed = []

    for i, entry in enumerate(top_300, 1):
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
                    "original_2word": entry['original_skipgram_2'],
                    "original_3word": entry['original_skipgram_3'],
                    "original_4plus": entry['original_skipgram_4plus'],
                    "deduplicated_2word": entry['deduplicated_skipgram_2'],
                    "deduplicated_3word": entry['deduplicated_skipgram_3'],
                    "deduplicated_4plus": entry['deduplicated_skipgram_4plus']
                },
                "roots": {
                    "original_count": entry['original_root_count'],
                    "deduplicated_count": entry['deduplicated_root_count'],
                    "in_contiguous_phrases": entry['roots_in_contiguous'],
                    "in_skipgrams_estimated": entry['roots_in_skipgrams_est'],
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

            # Root statistics (deduplicated - excludes roots in phrases)
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
            "deduplicated_roots": entry['deduplicated_roots']
        }

        top_300_detailed.append(detailed_entry)

        if i % 50 == 0:
            logger.info(f"  Processed {i}/300 connections...")

    # Save output
    output_path = base_dir / "data/analysis_results/top_300_connections_skipgram_dedup.json"
    logger.info(f"Saving detailed top 300 to {output_path}...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(top_300_detailed, f, indent=2, ensure_ascii=False)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"  File size: {file_size_mb:.2f} MB")

    # Summary statistics
    logger.info("\nSummary:")
    logger.info(f"  Total entries: {len(top_300_detailed)}")
    logger.info(f"  Rank 1: Psalms {top_300_detailed[0]['psalm_a']}-{top_300_detailed[0]['psalm_b']} (score: {top_300_detailed[0]['final_score']:.2f})")
    logger.info(f"  Rank 300: Psalms {top_300_detailed[-1]['psalm_a']}-{top_300_detailed[-1]['psalm_b']} (score: {top_300_detailed[-1]['final_score']:.2f})")

    # Deduplication stats
    total_skipgrams_removed = sum(
        (e['deduplication_stats']['skipgrams']['original_2word'] - e['deduplication_stats']['skipgrams']['deduplicated_2word']) +
        (e['deduplication_stats']['skipgrams']['original_3word'] - e['deduplication_stats']['skipgrams']['deduplicated_3word']) +
        (e['deduplication_stats']['skipgrams']['original_4plus'] - e['deduplication_stats']['skipgrams']['deduplicated_4plus'])
        for e in top_300_detailed
    )
    total_roots_removed = sum(e['deduplication_stats']['roots']['total_removed'] for e in top_300_detailed)
    total_dedup_roots = sum(len(e['deduplicated_roots']) for e in top_300_detailed)
    total_dedup_phrases = sum(len(e['deduplicated_contiguous_phrases']) for e in top_300_detailed)

    logger.info(f"\n  Deduplication impact across top 300:")
    logger.info(f"    Skipgrams removed: {total_skipgrams_removed:,}")
    logger.info(f"    Roots removed: {total_roots_removed:,}")
    logger.info(f"    Total deduplicated roots: {total_dedup_roots} (avg {total_dedup_roots/300:.1f} per connection)")
    logger.info(f"    Total deduplicated contiguous phrases: {total_dedup_phrases} (avg {total_dedup_phrases/300:.1f} per connection)")

    logger.info("\n✓ Complete!")
    logger.info(f"Output saved to: {output_path}")


if __name__ == "__main__":
    main()
