"""
Validation Script - Root Matching with Rarity Assessment

This script demonstrates the root extraction and rarity assessment
by analyzing a sample set of Psalms and showing examples of:
1. Roots extracted from each Psalm
2. Shared roots between Psalm pairs
3. IDF scores (rarity metric) for each root
4. Assessment of whether shared vocabulary is statistically significant

User will see concrete examples before running full analysis on all 150 Psalms.
"""

import sys
from pathlib import Path
import logging

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent))

from root_extractor import RootExtractor
from frequency_analyzer import FrequencyAnalyzer
from database_builder import PsalmRelationshipsDB

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)


def print_section(title: str, width: int = 80):
    """Print a formatted section header."""
    print("\n" + "=" * width)
    print(title.center(width))
    print("=" * width)


def analyze_psalm_pair(psalm_a: int, psalm_b: int, db: PsalmRelationshipsDB, stats: dict):
    """
    Analyze shared roots between two Psalms.

    Args:
        psalm_a: First Psalm number
        psalm_b: Second Psalm number
        db: Database connection
        stats: Rarity statistics
    """
    print(f"\n{'─' * 80}")
    print(f"Psalm {psalm_a} ↔ Psalm {psalm_b}: Shared Root Analysis")
    print('─' * 80)

    # Get roots for both Psalms
    roots_a = {r['root']: r for r in db.get_psalm_roots(psalm_a)}
    roots_b = {r['root']: r for r in db.get_psalm_roots(psalm_b)}

    # Find shared roots
    shared = set(roots_a.keys()) & set(roots_b.keys())

    if not shared:
        print(f"  No shared roots found between Psalm {psalm_a} and Psalm {psalm_b}")
        return

    print(f"  Total roots in Psalm {psalm_a}: {len(roots_a)}")
    print(f"  Total roots in Psalm {psalm_b}: {len(roots_b)}")
    print(f"  Shared roots: {len(shared)}")

    # Sort shared roots by IDF (rarest first)
    shared_with_idf = [(root, roots_a[root]['idf']) for root in shared]
    shared_with_idf.sort(key=lambda x: x[1], reverse=True)

    # Calculate weighted overlap score (sum of IDF scores)
    weighted_score = sum(idf for _, idf in shared_with_idf)

    print(f"  Weighted overlap score: {weighted_score:.2f}")
    print(f"\n  Top 10 Shared Roots (by rarity):")
    print(f"  {'Root':<12} {'IDF':<8} {'Rarity':<30} {'Examples (Ps {psalm_a})':<25} {'Examples (Ps {psalm_b})':<25}")
    print(f"  {'-'*12} {'-'*8} {'-'*30} {'-'*25} {'-'*25}")

    from frequency_analyzer import FrequencyAnalyzer
    analyzer = FrequencyAnalyzer.__new__(FrequencyAnalyzer)

    for i, (root, idf) in enumerate(shared_with_idf[:10], 1):
        rarity = analyzer.classify_rarity(idf, stats)

        # Get example words from both Psalms
        examples_a = roots_a[root]['examples'][:2]
        examples_b = roots_b[root]['examples'][:2]

        examples_a_str = ', '.join(examples_a)
        examples_b_str = ', '.join(examples_b)

        print(f"  {root:<12} {idf:<8.3f} {rarity:<30} {examples_a_str:<25} {examples_b_str:<25}")


def main():
    """Main validation routine."""

    # Database paths
    tanakh_db = Path(__file__).parent.parent.parent / 'database' / 'tanakh.db'
    relationships_db = Path(__file__).parent.parent.parent / 'data' / 'psalm_relationships.db'

    if not tanakh_db.exists():
        print(f"ERROR: tanakh.db not found at {tanakh_db}")
        return

    print_section("Root Matching Validation with Rarity Assessment")

    print("\nThis script demonstrates:")
    print("  1. Root extraction from sample Psalms")
    print("  2. IDF score computation (rarity metric)")
    print("  3. Shared root detection between Psalm pairs")
    print("  4. Rarity assessment for each shared root")

    # Sample Psalms covering different types
    sample_psalms = [
        1,    # Torah meditation
        2,    # Royal psalm
        3,    # Lament
        23,   # Shepherd psalm
        42,   # Part of 42-43 pair (known relationship)
        43,   # Part of 42-43 pair (known relationship)
        117,  # Shortest psalm
        119,  # Longest psalm (acrostic)
    ]

    print(f"\nProcessing {len(sample_psalms)} sample Psalms:")
    print(f"  {', '.join(map(str, sample_psalms))}")
    print("\nThis may take 30-60 seconds...")

    # Extract roots and compute frequencies
    with FrequencyAnalyzer(tanakh_db, relationships_db) as analyzer:
        print("\n  → Extracting roots from sample Psalms...")
        results = analyzer.extract_all_psalm_roots(sample_psalms)

        print("  → Computing IDF scores (rarity metrics)...")
        analyzer.compute_frequencies()

        print("  → Calculating rarity statistics...")
        stats = analyzer.get_rarity_statistics()

    print("\n✓ Extraction and analysis complete!")

    # Show overall statistics
    print_section("Overall Root Statistics")
    print(f"  Total unique roots: {stats['total_roots']}")
    print(f"  Average IDF score: {stats['avg_idf']:.3f}")
    print(f"  IDF range: {stats['min_idf']:.3f} to {stats['max_idf']:.3f}")

    # Show rarity classification thresholds
    print("\n  Rarity Classification Thresholds (IDF scores):")
    print(f"    Extremely rare (top 5%):     IDF ≥ {stats['idf_percentiles']['95th']:.3f}")
    print(f"    Very rare (top 10%):         IDF ≥ {stats['idf_percentiles']['90th']:.3f}")
    print(f"    Rare (top 25%):              IDF ≥ {stats['idf_percentiles']['75th']:.3f}")
    print(f"    Moderately rare (median):    IDF ≥ {stats['idf_percentiles']['50th']:.3f}")
    print(f"    Somewhat common:             IDF ≥ {stats['idf_percentiles']['25th']:.3f}")
    print(f"    Very common (bottom 25%):    IDF < {stats['idf_percentiles']['25th']:.3f}")

    # Analyze specific Psalm pairs
    print_section("Shared Root Examples - Specific Psalm Pairs")

    # Known related pair: Psalms 42-43
    print("\n📖 Known Related Pair: Psalms 42 & 43")
    print("   (Scholarly consensus: originally one Psalm)")
    with PsalmRelationshipsDB(relationships_db) as db:
        analyze_psalm_pair(42, 43, db, stats)

    # Different genre pair: Psalm 1 & 23
    print("\n📖 Different Genres: Psalm 1 (Torah meditation) & Psalm 23 (Shepherd psalm)")
    with PsalmRelationshipsDB(relationships_db) as db:
        analyze_psalm_pair(1, 23, db, stats)

    # Extreme length difference: Psalm 117 & 119
    print("\n📖 Extreme Length Difference: Psalm 117 (shortest) & Psalm 119 (longest)")
    with PsalmRelationshipsDB(relationships_db) as db:
        analyze_psalm_pair(117, 119, db, stats)

    # Royal psalms: Psalm 2 & 3
    print("\n📖 Sequential Psalms: Psalm 2 & Psalm 3")
    with PsalmRelationshipsDB(relationships_db) as db:
        analyze_psalm_pair(2, 3, db, stats)

    print_section("Validation Complete")
    print("\n✓ You can now see:")
    print("  • How roots are extracted from Hebrew text")
    print("  • How IDF scores measure rarity (higher = rarer)")
    print("  • Which roots are shared between Psalm pairs")
    print("  • Rarity classifications for each shared root")
    print("\nNext step: Run full analysis on all 150 Psalms to detect")
    print("          statistically significant relationships!")


if __name__ == '__main__':
    main()
