"""
Generate Top Connections Report

Creates comprehensive report of top 100-150 psalm connections
based on enhanced scoring system.
"""

import json
from pathlib import Path
import logging
from typing import List, Dict
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCORES_PATH = Path(__file__).parent.parent.parent / "data" / "analysis_results" / "enhanced_scores_full.json"
TOP_100_PATH = Path(__file__).parent.parent.parent / "data" / "analysis_results" / "top_100_connections.json"
REPORT_PATH = Path(__file__).parent.parent.parent / "data" / "analysis_results" / "TOP_100_CONNECTIONS_REPORT.md"
OLD_RELATIONSHIPS_PATH = Path(__file__).parent.parent.parent / "data" / "analysis_results" / "significant_relationships.json"


def load_scores() -> List[Dict]:
    """Load enhanced scores from JSON."""
    with open(SCORES_PATH, 'r') as f:
        return json.load(f)


def load_old_rankings() -> Dict[tuple, int]:
    """
    Load original rankings from significant_relationships.json.

    Returns:
        Dictionary mapping (psalm_a, psalm_b) to original rank
    """
    with open(OLD_RELATIONSHIPS_PATH, 'r') as f:
        old_data = json.load(f)

    rankings = {}
    # Sort by p-value (ascending) to get original ranking
    sorted_data = sorted(old_data, key=lambda x: x['pvalue'])

    for rank, item in enumerate(sorted_data, 1):
        psalms = (item['psalm_a'], item['psalm_b'])
        rankings[psalms] = rank

    return rankings


def generate_report():
    """Generate comprehensive top connections report."""
    logger.info("=" * 60)
    logger.info("GENERATING TOP CONNECTIONS REPORT")
    logger.info("=" * 60)

    # Load data
    logger.info("\nLoading data...")
    scores = load_scores()
    old_rankings = load_old_rankings()

    logger.info(f"  Loaded {len(scores)} enhanced scores")
    logger.info(f"  Loaded {len(old_rankings)} original rankings")

    # Get top 150
    top_150 = scores[:150]

    # Save top 100 JSON
    with open(TOP_100_PATH, 'w', encoding='utf-8') as f:
        json.dump(top_150[:100], f, indent=2, ensure_ascii=False)

    logger.info(f"\n✓ Saved top 100 to: {TOP_100_PATH}")

    # Generate markdown report
    logger.info("\nGenerating markdown report...")

    report_lines = []
    report_lines.append("# Top 100 Psalm Connections - Enhanced Scoring System")
    report_lines.append("")
    report_lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("## Methodology")
    report_lines.append("")
    report_lines.append("This report uses an enhanced scoring system that combines:")
    report_lines.append("")
    report_lines.append("1. **Contiguous phrases** (2, 3, 4+ words)")
    report_lines.append("2. **Skip-gram patterns** (non-contiguous patterns within windows)")
    report_lines.append("3. **Root IDF overlap** (rarity-weighted vocabulary sharing)")
    report_lines.append("4. **Length normalization** (adjusted for psalm word counts)")
    report_lines.append("")
    report_lines.append("### Scoring Formula")
    report_lines.append("")
    report_lines.append("```")
    report_lines.append("pattern_points = (2-word × 1) + (3-word × 2) + (4+ word × 3)")
    report_lines.append("root_idf_sum = sum of IDF scores for shared roots")
    report_lines.append("geom_mean_length = sqrt(word_count_A × word_count_B)")
    report_lines.append("")
    report_lines.append("phrase_score = (pattern_points / geom_mean_length) × 1000")
    report_lines.append("root_score = (root_idf_sum / geom_mean_length) × 1000")
    report_lines.append("")
    report_lines.append("FINAL_SCORE = phrase_score + root_score")
    report_lines.append("```")
    report_lines.append("")

    # Statistics
    report_lines.append("## Score Statistics")
    report_lines.append("")
    final_scores = [s['final_score'] for s in scores]
    report_lines.append(f"- **Minimum score**: {min(final_scores):.2f}")
    report_lines.append(f"- **Maximum score**: {max(final_scores):.2f}")
    report_lines.append(f"- **Median score**: {sorted(final_scores)[len(final_scores)//2]:.2f}")
    report_lines.append(f"- **Top 100 threshold**: {scores[99]['final_score']:.2f}")
    report_lines.append(f"- **Top 150 threshold**: {scores[149]['final_score']:.2f}")
    report_lines.append("")

    # Validation section
    report_lines.append("## Validation: Known Connections")
    report_lines.append("")

    known_pairs = [
        (14, 53, "Nearly identical Psalms"),
        (60, 108, "Composite Psalm (57+60)"),
        (40, 70, "Shared passage"),
        (42, 43, "Originally one Psalm"),
        (25, 34, "Thematic connection (scholarly consensus)"),
    ]

    report_lines.append("| Psalms | Description | New Rank | Score | Old Rank | Status |")
    report_lines.append("|--------|-------------|----------|-------|----------|--------|")

    for psalm_a, psalm_b, desc in known_pairs:
        score_data = next((s for s in scores if s['psalm_a'] == psalm_a and s['psalm_b'] == psalm_b), None)
        if score_data:
            new_rank = score_data['original_rank']
            score = score_data['final_score']
            old_rank = old_rankings.get((psalm_a, psalm_b), "N/A")

            status = "✓" if new_rank <= 150 else "✗"
            report_lines.append(f"| {psalm_a} & {psalm_b} | {desc} | #{new_rank} | {score:.2f} | #{old_rank} | {status} |")

    report_lines.append("")

    # Top 100 table
    report_lines.append("## Top 100 Connections")
    report_lines.append("")
    report_lines.append("| Rank | Psalms | Score | Patterns | Roots | Old Rank | Change |")
    report_lines.append("|------|--------|-------|----------|-------|----------|--------|")

    for score_data in top_150[:100]:
        rank = score_data['original_rank']
        psalm_a = score_data['psalm_a']
        psalm_b = score_data['psalm_b']
        score = score_data['final_score']
        patterns = score_data['total_pattern_points']
        roots = score_data['shared_roots']
        old_rank = old_rankings.get((psalm_a, psalm_b), 99999)

        change = old_rank - rank
        if change > 0:
            change_str = f"+{change} ↑"
        elif change < 0:
            change_str = f"{change} ↓"
        else:
            change_str = "="

        report_lines.append(
            f"| {rank} | {psalm_a} & {psalm_b} | {score:.2f} | {patterns:.0f} | {roots} | {old_rank} | {change_str} |"
        )

    report_lines.append("")

    # Detailed breakdown for top 10
    report_lines.append("## Detailed Breakdown: Top 10")
    report_lines.append("")

    for i, score_data in enumerate(top_150[:10], 1):
        report_lines.append(f"### {i}. Psalms {score_data['psalm_a']} & {score_data['psalm_b']}")
        report_lines.append("")
        report_lines.append(f"**Final Score**: {score_data['final_score']:.2f}")
        report_lines.append("")
        report_lines.append("**Pattern Analysis**:")
        report_lines.append(f"- Contiguous phrases: 2w={score_data['contiguous_2word']}, 3w={score_data['contiguous_3word']}, 4+w={score_data['contiguous_4plus']}")
        report_lines.append(f"- Skip-grams: 2w={score_data['skipgram_2word']}, 3w={score_data['skipgram_3word']}, 4w={score_data['skipgram_4plus']}")
        report_lines.append(f"- **Total pattern points**: {score_data['total_pattern_points']:.0f}")
        report_lines.append("")
        report_lines.append("**Root Analysis**:")
        report_lines.append(f"- Shared roots: {score_data['shared_roots']}")
        report_lines.append(f"- Root IDF sum: {score_data['root_idf_sum']:.2f}")
        report_lines.append("")
        report_lines.append("**Normalization**:")
        report_lines.append(f"- Psalm {score_data['psalm_a']} length: {score_data['word_count_a']} words")
        report_lines.append(f"- Psalm {score_data['psalm_b']} length: {score_data['word_count_b']} words")
        report_lines.append(f"- Geometric mean: {score_data['geometric_mean_length']:.1f}")
        report_lines.append("")
        report_lines.append("**Component Scores**:")
        report_lines.append(f"- Phrase score: {score_data['phrase_score']:.2f}")
        report_lines.append(f"- Root score: {score_data['root_score']:.2f}")
        report_lines.append("")

    # Save report
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    logger.info(f"\n✓ Saved report to: {REPORT_PATH}")
    logger.info(f"  File size: {REPORT_PATH.stat().st_size:,} bytes")

    # Summary statistics
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total relationships: {len(scores)}")
    logger.info(f"Reduced to top 100: {100}")
    logger.info(f"Reduction: {(1 - 100/len(scores))*100:.1f}%")

    # Check if Psalms 25 & 34 made it
    ps25_34 = next((s for s in scores if s['psalm_a'] == 25 and s['psalm_b'] == 34), None)
    if ps25_34:
        rank = ps25_34['original_rank']
        if rank <= 150:
            logger.info(f"\n✓ Psalms 25 & 34 validated: Rank #{rank}")
        else:
            logger.warning(f"\n✗ Psalms 25 & 34 NOT in top 150: Rank #{rank}")
            logger.warning(f"  Score: {ps25_34['final_score']:.2f}")
            logger.warning(f"  Threshold: {scores[149]['final_score']:.2f}")
            logger.warning(f"  Gap: {scores[149]['final_score'] - ps25_34['final_score']:.2f} points")


if __name__ == "__main__":
    generate_report()
