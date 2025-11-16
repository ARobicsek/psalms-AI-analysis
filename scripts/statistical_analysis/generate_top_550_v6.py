"""
V6 Top 550 Connections Generator

Extracts the top 550 psalm connections from V6 scores.
Provides easier analysis of the highest-scoring relationships.

Input: data/analysis_results/enhanced_scores_v6.json
Output: data/analysis_results/top_550_connections_v6.json
"""

import sys
from pathlib import Path
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Generate top 550 connections from V6 scores."""
    base_dir = Path(__file__).parent.parent.parent

    # Paths
    scores_file = base_dir / "data" / "analysis_results" / "enhanced_scores_v6.json"
    output_file = base_dir / "data" / "analysis_results" / "top_550_connections_v6.json"

    # Load V6 scores
    logger.info(f"Loading V6 scores from {scores_file.name}...")
    with open(scores_file, 'r', encoding='utf-8') as f:
        all_scores = json.load(f)
    logger.info(f"  Loaded {len(all_scores)} psalm pairs")

    # Verify scores are sorted
    if all_scores[0]['final_score'] < all_scores[-1]['final_score']:
        logger.info("  Sorting scores by final_score (descending)...")
        all_scores.sort(key=lambda x: x['final_score'], reverse=True)

    # Extract top 550
    top_550 = all_scores[:550]

    # Report score range
    logger.info(f"\nTop 550 Statistics:")
    logger.info(f"  Rank #1: Psalms {top_550[0]['psalm_a']}-{top_550[0]['psalm_b']} (score: {top_550[0]['final_score']:.2f})")
    logger.info(f"  Rank #550: Psalms {top_550[549]['psalm_a']}-{top_550[549]['psalm_b']} (score: {top_550[549]['final_score']:.2f})")
    logger.info(f"  Score range: {top_550[0]['final_score']:.2f} to {top_550[549]['final_score']:.2f}")

    # Save to JSON
    logger.info(f"\nSaving top 550 to {output_file.name}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(top_550, f, ensure_ascii=False, indent=2)

    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    logger.info(f"✓ Saved {output_file.name} ({file_size_mb:.2f} MB)")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("V6 TOP 550 GENERATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Output file: {output_file}")
    logger.info("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
