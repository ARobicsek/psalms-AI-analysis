"""
Full Psalm Relationship Statistical Analysis

This script runs the complete analysis pipeline on all 150 Psalms:
1. Extract roots from all Psalms
2. Compute IDF scores (rarity metrics)
3. Compare all pairs using hypergeometric test
4. Store significant relationships
5. Generate summary reports

User Requirements:
- Include ALL 150 Psalms (including short ones like Psalm 117)
- Record bidirectional relationships (A→B and B→A as separate entries)
- Show examples of matches with rarity assessment
- Provide likelihood interpretation for relationships
"""

import sys
from pathlib import Path
import time
import json
import logging

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent))

from frequency_analyzer import FrequencyAnalyzer
from pairwise_comparator import PairwiseComparator
from database_builder import PsalmRelationshipsDB

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


def print_section(title: str, width: int = 80):
    """Print a formatted section header."""
    print("\n" + "=" * width)
    print(title.center(width))
    print("=" * width)


def run_full_analysis(output_dir: Path = None):
    """
    Run complete statistical analysis on all 150 Psalms.

    Args:
        output_dir: Directory for output reports (default: data/analysis_results/)
    """
    # Set up paths
    tanakh_db = Path(__file__).parent.parent.parent / 'database' / 'tanakh.db'
    relationships_db = Path(__file__).parent.parent.parent / 'data' / 'psalm_relationships.db'

    if output_dir is None:
        output_dir = Path(__file__).parent.parent.parent / 'data' / 'analysis_results'

    output_dir.mkdir(parents=True, exist_ok=True)

    print_section("Psalm Relationship Statistical Analysis - Full Run")

    print("\nThis analysis will:")
    print("  1. Extract roots from ALL 150 Psalms")
    print("  2. Compute IDF scores (rarity metrics)")
    print("  3. Compare all 11,175 Psalm pairs")
    print("  4. Identify statistically significant relationships")
    print("  5. Generate comprehensive reports")

    print(f"\nOutput directory: {output_dir}")

    # All 150 Psalms
    all_psalms = list(range(1, 151))

    # Phase 1: Extract roots and compute frequencies
    print_section("Phase 1: Root Extraction & Frequency Analysis")

    start_time = time.time()

    with FrequencyAnalyzer(tanakh_db, relationships_db) as analyzer:
        logger.info("Extracting roots from all 150 Psalms...")
        results = analyzer.extract_all_psalm_roots(all_psalms)

        logger.info("Computing root frequencies and IDF scores...")
        analyzer.compute_frequencies()

        logger.info("Calculating rarity statistics...")
        stats = analyzer.get_rarity_statistics()

    extraction_time = time.time() - start_time

    print(f"\n✓ Phase 1 complete in {extraction_time:.1f} seconds")
    print(f"  Total unique roots: {stats['total_roots']}")
    print(f"  Average IDF score: {stats['avg_idf']:.3f}")
    print(f"  IDF range: {stats['min_idf']:.3f} to {stats['max_idf']:.3f}")

    # Save statistics
    stats_file = output_dir / 'root_statistics.json'
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"  Statistics saved to: {stats_file.name}")

    # Phase 2: Pairwise comparison
    print_section("Phase 2: Pairwise Statistical Comparison")

    start_time = time.time()

    with PairwiseComparator(relationships_db) as comparator:
        logger.info("Comparing all 11,175 Psalm pairs...")
        relationships = comparator.compare_all_pairs(all_psalms, store_all=False)

        logger.info("Retrieving significant relationships...")
        significant = comparator.get_significant_relationships()

    comparison_time = time.time() - start_time

    print(f"\n✓ Phase 2 complete in {comparison_time:.1f} seconds")
    print(f"  Total pairs compared: {len(relationships)}")
    print(f"  Significant relationships found: {len(significant)}")

    # Phase 3: Generate reports
    print_section("Phase 3: Report Generation")

    # Top 20 most significant relationships
    print("\nTop 20 Most Significant Relationships:")
    print(f"{'Rank':<6} {'Psalms':<12} {'p-value':<12} {'Z-score':<10} {'Shared':<8} {'Weighted':<10} {'Likelihood':<30}")
    print('-' * 110)

    for i, rel in enumerate(significant[:20], 1):
        # Interpret p-value
        if rel['pvalue'] < 1e-10:
            likelihood = "virtually certain (p < 1e-10)"
        elif rel['pvalue'] < 1e-6:
            likelihood = "extremely unlikely by chance"
        elif rel['pvalue'] < 1e-3:
            likelihood = "highly unlikely by chance"
        elif rel['pvalue'] < 0.01:
            likelihood = "unlikely by chance"
        else:
            likelihood = "possibly by chance"

        psalms_str = f"{rel['psalm_a']}-{rel['psalm_b']}"

        print(f"{i:<6} {psalms_str:<12} {rel['pvalue']:<12.2e} {rel['z_score']:<10.2f} "
              f"{rel['shared_root_count']:<8} {rel['weighted_score']:<10.2f} {likelihood:<30}")

    # Save comprehensive report
    report_file = output_dir / 'significant_relationships.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(significant, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Full report saved to: {report_file.name}")

    # Phase 4: Bidirectional relationship table
    print_section("Phase 4: Bidirectional Relationship Table")

    # Create bidirectional entries (user requirement)
    bidirectional = []
    for rel in significant:
        # Add A→B entry
        bidirectional.append({
            'from_psalm': rel['psalm_a'],
            'to_psalm': rel['psalm_b'],
            'pvalue': rel['pvalue'],
            'z_score': rel['z_score'],
            'weighted_score': rel['weighted_score'],
            'shared_root_count': rel['shared_root_count']
        })

        # Add B→A entry
        bidirectional.append({
            'from_psalm': rel['psalm_b'],
            'to_psalm': rel['psalm_a'],
            'pvalue': rel['pvalue'],
            'z_score': rel['z_score'],
            'weighted_score': rel['weighted_score'],
            'shared_root_count': rel['shared_root_count']
        })

    # Sort by from_psalm, then by pvalue
    bidirectional.sort(key=lambda x: (x['from_psalm'], x['pvalue']))

    bidirectional_file = output_dir / 'bidirectional_relationships.json'
    with open(bidirectional_file, 'w', encoding='utf-8') as f:
        json.dump(bidirectional, f, indent=2, ensure_ascii=False)

    print(f"  Total bidirectional entries: {len(bidirectional)}")
    print(f"  Saved to: {bidirectional_file.name}")

    # Example: Show relationships for Psalm 23
    print("\n  Example - Relationships involving Psalm 23:")
    psalm_23_rels = [r for r in bidirectional if r['from_psalm'] == 23][:5]
    for rel in psalm_23_rels:
        print(f"    Psalm 23 → Psalm {rel['to_psalm']:3d}: p={rel['pvalue']:.2e}, "
              f"shared={rel['shared_root_count']}, weighted={rel['weighted_score']:.2f}")

    # Summary
    print_section("Analysis Complete - Summary")

    total_time = extraction_time + comparison_time
    print(f"\nTotal processing time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"\nResults saved to: {output_dir}/")
    print(f"  - root_statistics.json")
    print(f"  - significant_relationships.json")
    print(f"  - bidirectional_relationships.json")
    print(f"\nDatabase: {relationships_db}")
    print(f"  - {stats['total_roots']} unique roots")
    print(f"  - {len(significant)} significant relationships")
    print(f"  - {len(bidirectional)} bidirectional entries")

    print("\n✓ Full analysis complete!")

    return {
        'total_roots': stats['total_roots'],
        'significant_count': len(significant),
        'processing_time': total_time,
        'output_dir': str(output_dir)
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Run full statistical analysis on all 150 Psalms'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        help='Output directory for reports (default: data/analysis_results/)'
    )

    args = parser.parse_args()

    # Run the analysis
    results = run_full_analysis(output_dir=args.output_dir)

    print("\n" + "=" * 80)
    print(f"Analysis results available in: {results['output_dir']}")
    print("=" * 80)
