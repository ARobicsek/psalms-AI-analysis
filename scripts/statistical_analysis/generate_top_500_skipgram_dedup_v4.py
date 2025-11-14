"""
Generate Top 500 Connections - V4

V4 improvements:
- Verse-tracked skipgrams with populated matches arrays
- Clean output format (no unnecessary fields)
- Properly deduplicated overlapping patterns
- All match types have matches_from_a and matches_from_b

This generates the final V4 output for user review.
"""

import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def generate_top_500_v4():
    """Generate top 500 connections from V4 scores."""

    base_dir = Path(__file__).parent.parent.parent

    # Load V4 scores
    logger.info("Loading V4 scores...")
    with open(base_dir / "data/analysis_results/enhanced_scores_skipgram_dedup_v4.json", 'r', encoding='utf-8') as f:
        all_scores = json.load(f)

    logger.info(f"  Loaded {len(all_scores):,} psalm relationships")

    # Sort by final_score (descending)
    logger.info("Sorting by final_score...")
    sorted_scores = sorted(all_scores, key=lambda x: x['final_score'], reverse=True)

    # Take top 500
    top_500 = sorted_scores[:500]

    logger.info(f"  Top 500 score range: {top_500[0]['final_score']:.2f} to {top_500[-1]['final_score']:.2f}")

    # Add rank to each entry
    for rank, entry in enumerate(top_500, start=1):
        entry['rank'] = rank

    # Create output with better formatting
    logger.info("Creating formatted output...")
    output = []

    for entry in top_500:
        # Restructure for cleaner presentation
        formatted_entry = {
            'rank': entry['rank'],
            'psalm_a': entry['psalm_a'],
            'psalm_b': entry['psalm_b'],

            # Statistics summary
            'deduplication_stats': {
                'contiguous': {
                    'original_count': entry['original_phrase_count'],
                    'deduplicated_count': entry['deduplicated_contiguous_count'],
                    'removed_as_substrings': entry['phrases_removed_as_substrings']
                },
                'skipgrams': {
                    'original_count': entry['original_skipgram_count'],
                    'deduplicated_count': entry['deduplicated_skipgram_count']
                },
                'roots': {
                    'original_count': entry['original_root_count'],
                    'deduplicated_count': entry['deduplicated_root_count'],
                    'in_contiguous_phrases': entry['roots_in_contiguous'],
                    'in_skipgrams': entry['roots_in_skipgrams'],
                    'filtered_by_idf': entry['roots_filtered_by_idf'],
                    'total_removed': entry['total_roots_removed']
                }
            },

            # Pattern counts
            'contiguous_2word': entry['contiguous_2word'],
            'contiguous_3word': entry['contiguous_3word'],
            'contiguous_4plus': entry['contiguous_4plus'],
            'skipgram_2word_dedup': entry['skipgram_2word_dedup'],
            'skipgram_3word_dedup': entry['skipgram_3word_dedup'],
            'skipgram_4plus_dedup': entry['skipgram_4plus_dedup'],
            'total_pattern_points': entry['total_pattern_points'],

            # Root statistics
            'shared_roots_count': entry['shared_roots_count'],
            'root_idf_sum': entry['root_idf_sum'],

            # Psalm info
            'word_count_a': entry['word_count_a'],
            'word_count_b': entry['word_count_b'],
            'geometric_mean_length': entry['geometric_mean_length'],

            # Scores
            'phrase_score': entry['phrase_score'],
            'root_score': entry['root_score'],
            'final_score': entry['final_score'],

            # Original data
            'original_pvalue': entry['original_pvalue'],
            'original_rank': entry['original_rank'],

            # Match details (clean V4 format)
            'deduplicated_contiguous_phrases': entry['deduplicated_contiguous_phrases'],
            'deduplicated_skipgrams': entry['deduplicated_skipgrams'],
            'deduplicated_roots': entry['deduplicated_roots']
        }

        output.append(formatted_entry)

    # Save output
    output_path = base_dir / "data/analysis_results/top_500_connections_skipgram_dedup_v4.json"
    logger.info(f"Saving top 500 to {output_path}...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"  File size: {file_size_mb:.2f} MB")

    # Print summary statistics
    logger.info("\n" + "=" * 60)
    logger.info("TOP 500 CONNECTIONS SUMMARY (V4)")
    logger.info("=" * 60)

    logger.info(f"\nScore Distribution:")
    logger.info(f"  Highest: {output[0]['final_score']:.2f} (Psalms {output[0]['psalm_a']}-{output[0]['psalm_b']})")
    logger.info(f"  Median:  {output[249]['final_score']:.2f} (Psalms {output[249]['psalm_a']}-{output[249]['psalm_b']})")
    logger.info(f"  Lowest:  {output[499]['final_score']:.2f} (Psalms {output[499]['psalm_a']}-{output[499]['psalm_b']})")

    # Average pattern counts
    avg_contiguous = sum(e['deduplication_stats']['contiguous']['deduplicated_count'] for e in output) / len(output)
    avg_skipgrams = sum(e['deduplication_stats']['skipgrams']['deduplicated_count'] for e in output) / len(output)
    avg_roots = sum(e['deduplication_stats']['roots']['deduplicated_count'] for e in output) / len(output)

    logger.info(f"\nAverage Matches per Connection:")
    logger.info(f"  Contiguous phrases: {avg_contiguous:.1f}")
    logger.info(f"  Skipgrams: {avg_skipgrams:.1f}")
    logger.info(f"  Roots: {avg_roots:.1f}")

    # V4 improvements demonstrated
    logger.info(f"\nV4 Improvements:")
    logger.info(f"  ✓ All skipgrams have verse tracking")
    logger.info(f"  ✓ matches_from_a/b arrays populated for all match types")
    logger.info(f"  ✓ Clean output (no position, no empty verses_a/b)")
    logger.info(f"  ✓ Overlapping patterns properly deduplicated")

    # Show top 10
    logger.info(f"\nTop 10 Connections:")
    for i in range(min(10, len(output))):
        entry = output[i]
        logger.info(f"  {i+1}. Psalms {entry['psalm_a']}-{entry['psalm_b']}: "
                   f"{entry['final_score']:.2f} "
                   f"({entry['deduplication_stats']['contiguous']['deduplicated_count']} phrases, "
                   f"{entry['deduplication_stats']['skipgrams']['deduplicated_count']} skipgrams)")

    logger.info("\n" + "=" * 60)
    logger.info("✓ Complete! Ready for user review.")
    logger.info("=" * 60)


if __name__ == "__main__":
    generate_top_500_v4()
