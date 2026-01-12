"""
Compare IDF vs Exponential IDF Transformation

This script compares two methods for calculating weighted overlap scores:
1. Current method: sum of IDF scores
2. Exponential method: sum of e^IDF scores

The goal is to determine which method better spreads out the distribution
and reduces bunching in statistical significance.
"""

import sys
from pathlib import Path
import math
from typing import List, Dict, Tuple, Any
from scipy import stats
import numpy as np
import json
import sqlite3
from collections import defaultdict

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent))

from database_builder import PsalmRelationshipsDB


def calculate_exponential_weighted_score(shared_roots: List[Dict], method='linear') -> float:
    """
    Calculate weighted score using different methods.

    Args:
        shared_roots: List of shared root dicts with 'idf' field
        method: 'linear' (sum of IDF) or 'exponential' (sum of e^IDF)

    Returns:
        Weighted score
    """
    if not shared_roots:
        return 0.0

    if method == 'linear':
        return sum(root['idf'] for root in shared_roots)
    elif method == 'exponential':
        return sum(math.exp(root['idf']) for root in shared_roots)
    else:
        raise ValueError(f"Unknown method: {method}")


def calculate_significance_exponential(
    shared_roots: List[Dict],
    roots_a: Dict,
    roots_b: Dict,
    N: int
) -> Tuple[float, float, bool]:
    """
    Calculate statistical significance using exponential IDF method.

    Args:
        shared_roots: List of shared roots with IDF scores
        roots_a: All roots in Psalm A
        roots_b: All roots in Psalm B
        N: Total unique roots in Psalter

    Returns:
        (weighted_score, z_score, is_significant)
    """
    K = len(roots_a)
    n = len(roots_b)
    k = len(shared_roots)

    if k == 0:
        return 0.0, 0.0, False

    # Calculate exponential weighted score
    weighted_score = sum(math.exp(root['idf']) for root in shared_roots)

    # Calculate expected exponential weighted score
    # Under null hypothesis, we expect (K * n / N) shared roots
    # with average exponential IDF
    all_roots = list(roots_a.values()) + list(roots_b.values())
    all_exp_idfs = [math.exp(r['idf']) for r in all_roots]
    avg_exp_idf = np.mean(all_exp_idfs)
    std_exp_idf = np.std(all_exp_idfs)

    expected_overlap = (K * n) / N if N > 0 else 0
    expected_weighted = expected_overlap * avg_exp_idf
    std_weighted = math.sqrt(expected_overlap) * std_exp_idf if expected_overlap > 0 else 1.0

    z_score = (weighted_score - expected_weighted) / std_weighted if std_weighted > 0 else 0.0

    # Hypergeometric p-value (same as current method - based on count not weight)
    pvalue = stats.hypergeom.sf(k - 1, N, K, n)

    # Determine significance
    is_significant = (pvalue < 0.01) or (z_score > 3.0)

    return weighted_score, z_score, is_significant


def analyze_all_relationships(db_path: Path):
    """
    Analyze all psalm pairs using both methods and compare results.
    """
    print("=" * 80)
    print("IDF vs Exponential IDF Comparison")
    print("=" * 80)

    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all stored relationships
    cursor.execute("""
        SELECT psalm_a, psalm_b, shared_roots_json,
               hypergeometric_pvalue, weighted_overlap_score, z_score, is_significant
        FROM psalm_relationships
        WHERE psalm_a < psalm_b
        ORDER BY psalm_a, psalm_b
    """)

    relationships = cursor.fetchall()
    print(f"\nTotal psalm pairs in database: {len(relationships)}")

    # Create database connection for getting roots
    db = PsalmRelationshipsDB(db_path)
    N = len([row for row in cursor.execute("SELECT DISTINCT root_id FROM psalm_roots").fetchall()])

    # Track results for both methods
    current_significant = 0
    exponential_significant = 0
    both_significant = 0
    current_only = []
    exponential_only = []

    # Store results for each psalm pair
    comparison_results = []

    print(f"\nAnalyzing {len(relationships)} psalm pairs...")

    for idx, row in enumerate(relationships):
        if (idx + 1) % 1000 == 0:
            print(f"  Processed {idx + 1}/{len(relationships)} pairs...")

        psalm_a = row['psalm_a']
        psalm_b = row['psalm_b']

        # Parse shared roots
        if row['shared_roots_json']:
            shared_roots = json.loads(row['shared_roots_json'])
        else:
            shared_roots = []

        # Get all roots for both psalms
        roots_a = {r['root']: r for r in db.get_psalm_roots(psalm_a)}
        roots_b = {r['root']: r for r in db.get_psalm_roots(psalm_b)}

        # Current method results (from database)
        current_significant_flag = bool(row['is_significant'])
        current_pvalue = row['hypergeometric_pvalue']
        current_weighted = row['weighted_overlap_score']
        current_z = row['z_score']

        # Exponential method results (recalculate)
        exp_weighted, exp_z, exp_significant = calculate_significance_exponential(
            shared_roots, roots_a, roots_b, N
        )

        # Track counts
        if current_significant_flag:
            current_significant += 1
        if exp_significant:
            exponential_significant += 1
        if current_significant_flag and exp_significant:
            both_significant += 1

        # Track differences
        if current_significant_flag and not exp_significant:
            current_only.append({
                'psalm_a': psalm_a,
                'psalm_b': psalm_b,
                'current_pvalue': current_pvalue,
                'current_z': current_z,
                'current_weighted': current_weighted,
                'exp_z': exp_z,
                'exp_weighted': exp_weighted,
                'shared_roots': len(shared_roots)
            })
        elif not current_significant_flag and exp_significant:
            exponential_only.append({
                'psalm_a': psalm_a,
                'psalm_b': psalm_b,
                'current_pvalue': current_pvalue,
                'current_z': current_z,
                'current_weighted': current_weighted,
                'exp_z': exp_z,
                'exp_weighted': exp_weighted,
                'shared_roots': len(shared_roots)
            })

        # Store for later analysis
        comparison_results.append({
            'psalm_a': psalm_a,
            'psalm_b': psalm_b,
            'current_sig': current_significant_flag,
            'exp_sig': exp_significant,
            'current_z': current_z,
            'exp_z': exp_z,
            'current_weighted': current_weighted,
            'exp_weighted': exp_weighted,
            'shared_roots': len(shared_roots)
        })

    print(f"\n{'=' * 80}")
    print("RESULTS SUMMARY")
    print(f"{'=' * 80}")
    print(f"\nTotal pairs analyzed: {len(relationships)}")
    print(f"\nCurrent method (linear IDF):")
    print(f"  Significant relationships: {current_significant}")
    print(f"  Percentage: {100 * current_significant / len(relationships):.1f}%")
    print(f"\nExponential method (e^IDF):")
    print(f"  Significant relationships: {exponential_significant}")
    print(f"  Percentage: {100 * exponential_significant / len(relationships):.1f}%")
    print(f"\nOverlap:")
    print(f"  Significant in both methods: {both_significant}")
    print(f"  Significant in current only: {len(current_only)}")
    print(f"  Significant in exponential only: {len(exponential_only)}")

    # Show examples of differences
    print(f"\n{'=' * 80}")
    print("EXAMPLES: Significant with CURRENT method but NOT exponential")
    print(f"{'=' * 80}")
    if current_only:
        for i, example in enumerate(current_only[:10], 1):
            print(f"\n{i}. Psalms {example['psalm_a']} & {example['psalm_b']}")
            print(f"   Shared roots: {example['shared_roots']}")
            print(f"   Current:     p={example['current_pvalue']:.2e}, z={example['current_z']:.2f}, weighted={example['current_weighted']:.2f}")
            print(f"   Exponential:                           z={example['exp_z']:.2f}, weighted={example['exp_weighted']:.2f}")
    else:
        print("\nNone found.")

    print(f"\n{'=' * 80}")
    print("EXAMPLES: Significant with EXPONENTIAL method but NOT current")
    print(f"{'=' * 80}")
    if exponential_only:
        for i, example in enumerate(exponential_only[:10], 1):
            print(f"\n{i}. Psalms {example['psalm_a']} & {example['psalm_b']}")
            print(f"   Shared roots: {example['shared_roots']}")
            print(f"   Current:     p={example['current_pvalue']:.2e}, z={example['current_z']:.2f}, weighted={example['current_weighted']:.2f}")
            print(f"   Exponential:                           z={example['exp_z']:.2f}, weighted={example['exp_weighted']:.2f}")
    else:
        print("\nNone found.")

    # Create psalm-by-psalm table
    print(f"\n{'=' * 80}")
    print("PSALM-BY-PSALM COMPARISON TABLE")
    print(f"{'=' * 80}")

    # Build mapping: psalm -> list of significant matches
    current_matches = defaultdict(list)
    exp_matches = defaultdict(list)

    for result in comparison_results:
        if result['current_sig']:
            current_matches[result['psalm_a']].append(result['psalm_b'])
            current_matches[result['psalm_b']].append(result['psalm_a'])
        if result['exp_sig']:
            exp_matches[result['psalm_a']].append(result['psalm_b'])
            exp_matches[result['psalm_b']].append(result['psalm_a'])

    # Sort matches for each psalm
    for psalm in current_matches:
        current_matches[psalm].sort()
    for psalm in exp_matches:
        exp_matches[psalm].sort()

    # Save detailed table to file
    output_file = Path(__file__).parent.parent.parent / 'data' / 'analysis_results' / 'idf_comparison_table.txt'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 120 + "\n")
        f.write("PSALM-BY-PSALM COMPARISON: Current IDF vs Exponential e^IDF\n")
        f.write("=" * 120 + "\n\n")

        for psalm in range(1, 151):
            current_list = current_matches.get(psalm, [])
            exp_list = exp_matches.get(psalm, [])

            f.write(f"Psalm {psalm:3d}:\n")
            f.write(f"  Current method ({len(current_list)} matches):     {current_list if current_list else 'None'}\n")
            f.write(f"  Exponential method ({len(exp_list)} matches):  {exp_list if exp_list else 'None'}\n")

            # Show differences
            current_only_set = set(current_list) - set(exp_list)
            exp_only_set = set(exp_list) - set(current_list)

            if current_only_set or exp_only_set:
                f.write(f"  DIFFERENCES:\n")
                if current_only_set:
                    f.write(f"    Lost with exponential: {sorted(current_only_set)}\n")
                if exp_only_set:
                    f.write(f"    Gained with exponential: {sorted(exp_only_set)}\n")

            f.write("\n")

    print(f"\nDetailed table saved to: {output_file}")
    print(f"  (Shows all 150 psalms with their significant matches under each method)")

    # Save summary statistics
    summary_file = Path(__file__).parent.parent.parent / 'data' / 'analysis_results' / 'idf_comparison_summary.json'
    summary = {
        'total_pairs': len(relationships),
        'current_method': {
            'significant_count': current_significant,
            'percentage': 100 * current_significant / len(relationships)
        },
        'exponential_method': {
            'significant_count': exponential_significant,
            'percentage': 100 * exponential_significant / len(relationships)
        },
        'overlap': {
            'both_significant': both_significant,
            'current_only': len(current_only),
            'exponential_only': len(exponential_only)
        },
        'examples_current_only': current_only[:20],
        'examples_exponential_only': exponential_only[:20]
    }

    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    print(f"\nSummary statistics saved to: {summary_file}")

    db.close()
    conn.close()

    print(f"\n{'=' * 80}")
    print("Analysis complete!")
    print(f"{'=' * 80}\n")


if __name__ == '__main__':
    db_path = Path(__file__).parent.parent.parent / 'data' / 'psalm_relationships.db'

    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}")
        sys.exit(1)

    analyze_all_relationships(db_path)
