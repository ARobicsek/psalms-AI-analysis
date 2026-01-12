"""
Generate Top 300 Detailed Connections

Creates a comprehensive JSON file showing the top 300 psalm-psalm connections
with complete match details including:
- All scoring statistics
- Complete list of shared roots with verse examples
- Complete list of shared phrases with verse numbers
"""

import json
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Generate detailed top 300 connections JSON."""

    # Paths
    base_dir = Path(__file__).parent.parent.parent
    enhanced_scores_path = base_dir / "data" / "analysis_results" / "enhanced_scores_full.json"
    relationships_path = base_dir / "data" / "analysis_results" / "significant_relationships.json"
    output_path = base_dir / "data" / "analysis_results" / "top_300_connections_detailed.json"

    logger.info("Loading enhanced scores...")
    with open(enhanced_scores_path, 'r', encoding='utf-8') as f:
        enhanced_scores = json.load(f)
    logger.info(f"  Loaded {len(enhanced_scores)} scored relationships")

    logger.info("Loading significant relationships (with detailed matches)...")
    with open(relationships_path, 'r', encoding='utf-8') as f:
        relationships = json.load(f)
    logger.info(f"  Loaded {len(relationships)} relationships with detailed match data")

    # Create lookup dictionary for relationships by (psalm_a, psalm_b)
    logger.info("Building relationship lookup dictionary...")
    rel_lookup = {}
    for rel in relationships:
        key = (rel['psalm_a'], rel['psalm_b'])
        rel_lookup[key] = rel
    logger.info(f"  Indexed {len(rel_lookup)} relationships")

    # Sort enhanced scores by final_score (descending) and take top 300
    logger.info("Sorting by final_score and selecting top 300...")
    enhanced_scores_sorted = sorted(
        enhanced_scores,
        key=lambda x: x['final_score'],
        reverse=True
    )
    top_300_enhanced = enhanced_scores_sorted[:300]
    logger.info(f"  Selected top 300 connections")
    logger.info(f"  Score range: {top_300_enhanced[0]['final_score']:.2f} to {top_300_enhanced[-1]['final_score']:.2f}")

    # Merge data
    logger.info("Merging enhanced scores with detailed match information...")
    top_300_detailed = []

    for i, enhanced in enumerate(top_300_enhanced, 1):
        psalm_a = enhanced['psalm_a']
        psalm_b = enhanced['psalm_b']
        key = (psalm_a, psalm_b)

        if key not in rel_lookup:
            logger.warning(f"  Warning: No detailed matches found for Psalms {psalm_a}-{psalm_b}")
            continue

        rel = rel_lookup[key]

        # Create comprehensive entry
        detailed_entry = {
            # Basic identification
            "rank": i,
            "psalm_a": psalm_a,
            "psalm_b": psalm_b,

            # Pattern counts (from enhanced_scores)
            "contiguous_2word": enhanced['contiguous_2word'],
            "contiguous_3word": enhanced['contiguous_3word'],
            "contiguous_4plus": enhanced['contiguous_4plus'],
            "skipgram_2word": enhanced['skipgram_2word'],
            "skipgram_3word": enhanced['skipgram_3word'],
            "skipgram_4plus": enhanced['skipgram_4plus'],
            "total_pattern_points": enhanced['total_pattern_points'],

            # Root overlap statistics
            "shared_roots_count": enhanced['shared_roots'],
            "root_idf_sum": enhanced['root_idf_sum'],

            # Psalm lengths
            "word_count_a": enhanced['word_count_a'],
            "word_count_b": enhanced['word_count_b'],
            "geometric_mean_length": enhanced['geometric_mean_length'],

            # Scores
            "phrase_score": enhanced['phrase_score'],
            "root_score": enhanced['root_score'],
            "final_score": enhanced['final_score'],

            # Original statistical data
            "original_pvalue": enhanced['original_pvalue'],
            "original_rank": enhanced['original_rank'],

            # DETAILED MATCHES - Shared Roots
            "shared_roots": rel['shared_roots'],

            # DETAILED MATCHES - Shared Phrases
            "shared_phrases": rel['shared_phrases']
        }

        top_300_detailed.append(detailed_entry)

        if i % 50 == 0:
            logger.info(f"  Processed {i}/300 connections...")

    # Save output
    logger.info(f"Saving detailed top 300 to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(top_300_detailed, f, indent=2, ensure_ascii=False)

    # Calculate file size
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"  File size: {file_size_mb:.2f} MB")

    # Summary statistics
    logger.info("\nSummary:")
    logger.info(f"  Total entries: {len(top_300_detailed)}")
    logger.info(f"  Rank 1: Psalms {top_300_detailed[0]['psalm_a']}-{top_300_detailed[0]['psalm_b']} (score: {top_300_detailed[0]['final_score']:.2f})")
    logger.info(f"  Rank 300: Psalms {top_300_detailed[-1]['psalm_a']}-{top_300_detailed[-1]['psalm_b']} (score: {top_300_detailed[-1]['final_score']:.2f})")

    # Sample detailed match counts
    total_roots = sum(len(entry['shared_roots']) for entry in top_300_detailed)
    total_phrases = sum(len(entry['shared_phrases']) for entry in top_300_detailed)
    logger.info(f"  Total shared roots across all 300: {total_roots}")
    logger.info(f"  Total shared phrases across all 300: {total_phrases}")
    logger.info(f"  Average roots per connection: {total_roots / len(top_300_detailed):.1f}")
    logger.info(f"  Average phrases per connection: {total_phrases / len(top_300_detailed):.1f}")

    logger.info("\n✓ Complete!")
    logger.info(f"Output saved to: {output_path}")


if __name__ == "__main__":
    main()
