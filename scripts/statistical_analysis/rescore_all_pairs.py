"""
Rescore All Psalm Pairs with Enhanced Formula

Calculates enhanced scores for all 11,001 significant relationships
and saves results to JSON.
"""

import json
from pathlib import Path
import logging
from enhanced_scorer import EnhancedScorer
from dataclasses import asdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OUTPUT_PATH = Path(__file__).parent.parent.parent / "data" / "analysis_results" / "enhanced_scores_full.json"


def rescore_all_pairs():
    """Rescore all psalm pairs and save to JSON."""
    logger.info("=" * 60)
    logger.info("RESCORING ALL 11,001 PSALM PAIRS")
    logger.info("=" * 60)

    # Initialize scorer
    scorer = EnhancedScorer()
    scorer.connect_db()
    scorer.load_word_counts()

    # Score all relationships
    logger.info("\nCalculating enhanced scores...")
    scores = scorer.score_all_relationships()

    logger.info(f"\n✓ Scored {len(scores)} psalm pairs")

    # Add ranking based on final score
    logger.info("\nRanking by enhanced score...")
    scores.sort(key=lambda s: s.final_score, reverse=True)

    for rank, score in enumerate(scores, 1):
        score.original_rank = rank

    # Convert to JSON-serializable format
    logger.info("Converting to JSON...")
    scores_data = [asdict(score) for score in scores]

    # Save to file
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(scores_data, f, indent=2, ensure_ascii=False)

    logger.info(f"\n✓ Saved to: {OUTPUT_PATH}")
    logger.info(f"  File size: {OUTPUT_PATH.stat().st_size:,} bytes")

    # Show statistics
    logger.info("\n" + "=" * 60)
    logger.info("SCORE STATISTICS")
    logger.info("=" * 60)

    final_scores = [s.final_score for s in scores]
    logger.info(f"Min score: {min(final_scores):.2f}")
    logger.info(f"Max score: {max(final_scores):.2f}")
    logger.info(f"Median score: {sorted(final_scores)[len(final_scores)//2]:.2f}")

    # Show score thresholds
    logger.info(f"\nScore thresholds:")
    logger.info(f"  Top 10: {scores[9].final_score:.2f}")
    logger.info(f"  Top 50: {scores[49].final_score:.2f}")
    logger.info(f"  Top 100: {scores[99].final_score:.2f}")
    logger.info(f"  Top 150: {scores[149].final_score:.2f}")

    # Show top 10
    logger.info(f"\n" + "=" * 60)
    logger.info("TOP 10 CONNECTIONS")
    logger.info("=" * 60)

    for i, score in enumerate(scores[:10], 1):
        logger.info(f"{i:2d}. Psalms {score.psalm_a:3d} & {score.psalm_b:3d}: {score.final_score:8.2f}")
        logger.info(f"    Patterns: {score.total_pattern_points:.0f} pts, Roots: {score.root_idf_sum:.2f} IDF")

    # Check Psalms 25 & 34
    logger.info(f"\n" + "=" * 60)
    logger.info("VALIDATION: Psalms 25 & 34")
    logger.info("=" * 60)

    ps25_34 = next((s for s in scores if s.psalm_a == 25 and s.psalm_b == 34), None)
    if ps25_34:
        logger.info(f"Rank: {ps25_34.original_rank}")
        logger.info(f"Score: {ps25_34.final_score:.2f}")
        logger.info(f"Pattern points: {ps25_34.total_pattern_points}")
        logger.info(f"Root IDF sum: {ps25_34.root_idf_sum:.2f}")
        if ps25_34.original_rank <= 150:
            logger.info("✓ IN TOP 150 - Validation successful!")
        else:
            logger.warning(f"NOT in top 150 - rank {ps25_34.original_rank}")
    else:
        logger.error("Psalms 25 & 34 not found in results!")

    scorer.close_db()


if __name__ == "__main__":
    rescore_all_pairs()
