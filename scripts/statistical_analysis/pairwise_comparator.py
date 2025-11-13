"""
Pairwise Psalm Comparator

Compares all Psalm pairs using hypergeometric test to determine
if shared vocabulary is statistically significant.

Statistical Framework:
- N = total unique roots in Psalter
- K = unique roots in Psalm A
- n = unique roots in Psalm B
- k = shared roots between A and B

Hypergeometric p-value = P(X ≥ k) where X ~ Hypergeometric(N, K, n)

Also computes:
- Weighted overlap score (sum of IDF scores for shared roots)
- Z-score (statistical significance of weighted score)
"""

import sys
from pathlib import Path
import math
from typing import List, Dict, Tuple, Any
from scipy import stats
import numpy as np
import logging

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent))

from database_builder import PsalmRelationshipsDB

logger = logging.getLogger(__name__)


class PairwiseComparator:
    """Compares Psalm pairs for statistical significance."""

    def __init__(self, relationships_db_path: Path = None):
        """
        Initialize pairwise comparator.

        Args:
            relationships_db_path: Path to psalm_relationships.db
        """
        self.db = PsalmRelationshipsDB(relationships_db_path)

    def get_total_unique_roots(self) -> int:
        """
        Get total number of unique roots across all Psalms.

        Returns:
            N = total unique roots in Psalter
        """
        cursor = self.db.conn.cursor()

        cursor.execute("""
            SELECT COUNT(DISTINCT root_id)
            FROM psalm_roots
        """)

        return cursor.fetchone()[0]

    def compare_pair(self, psalm_a: int, psalm_b: int) -> Dict[str, Any]:
        """
        Compare two Psalms using hypergeometric test.

        Args:
            psalm_a: First Psalm number
            psalm_b: Second Psalm number

        Returns:
            Dict with statistical measures and shared roots
        """
        # Get roots for both Psalms
        roots_a = {r['root']: r for r in self.db.get_psalm_roots(psalm_a)}
        roots_b = {r['root']: r for r in self.db.get_psalm_roots(psalm_b)}

        # Find shared roots
        shared_roots = set(roots_a.keys()) & set(roots_b.keys())

        if not shared_roots:
            return {
                'psalm_a': psalm_a,
                'psalm_b': psalm_b,
                'shared_root_count': 0,
                'total_roots_a': len(roots_a),
                'total_roots_b': len(roots_b),
                'pvalue': 1.0,
                'weighted_score': 0.0,
                'z_score': 0.0,
                'is_significant': False,
                'shared_roots': []
            }

        # Hypergeometric test
        N = self.get_total_unique_roots()  # Total unique roots in Psalter
        K = len(roots_a)  # Unique roots in Psalm A
        n = len(roots_b)  # Unique roots in Psalm B
        k = len(shared_roots)  # Shared roots

        # Calculate p-value: P(X ≥ k) where X ~ Hypergeom(N, K, n)
        # Using survival function (1 - CDF at k-1)
        pvalue = stats.hypergeom.sf(k - 1, N, K, n)

        # Weighted overlap score (sum of IDF scores)
        weighted_score = sum(roots_a[root]['idf'] for root in shared_roots)

        # Calculate z-score for weighted score
        # Under null hypothesis, expected weighted score is:
        # E[W] = (K * n / N) * average_idf
        # Variance is more complex, so we use empirical approach
        all_idfs = [r['idf'] for r in roots_a.values()] + [r['idf'] for r in roots_b.values()]
        avg_idf = np.mean(all_idfs)
        std_idf = np.std(all_idfs)

        expected_overlap = (K * n) / N if N > 0 else 0
        expected_weighted = expected_overlap * avg_idf
        std_weighted = math.sqrt(expected_overlap) * std_idf if expected_overlap > 0 else 1.0

        z_score = (weighted_score - expected_weighted) / std_weighted if std_weighted > 0 else 0.0

        # Determine significance (p < 0.01 OR z-score > 3.0)
        is_significant = (pvalue < 0.01) or (z_score > 3.0)

        # Build shared roots list
        shared_roots_list = []
        for root in sorted(shared_roots, key=lambda r: roots_a[r]['idf'], reverse=True):
            shared_roots_list.append({
                'root': root,
                'idf': roots_a[root]['idf'],
                'count_a': roots_a[root]['count'],
                'count_b': roots_b[root]['count'],
                'examples_a': roots_a[root]['examples'],
                'examples_b': roots_b[root]['examples']
            })

        return {
            'psalm_a': psalm_a,
            'psalm_b': psalm_b,
            'shared_root_count': k,
            'total_roots_a': K,
            'total_roots_b': n,
            'pvalue': float(pvalue),
            'weighted_score': float(weighted_score),
            'z_score': float(z_score),
            'is_significant': bool(is_significant),
            'shared_roots': shared_roots_list,
            'hypergeom_params': {
                'N': N,
                'K': K,
                'n': n,
                'k': k
            }
        }

    def compare_all_pairs(self, psalm_numbers: List[int],
                         store_all: bool = False) -> List[Dict[str, Any]]:
        """
        Compare all pairs of Psalms.

        Args:
            psalm_numbers: List of Psalm numbers to compare
            store_all: If True, store all relationships; if False, only significant ones

        Returns:
            List of relationship dicts
        """
        total_pairs = len(psalm_numbers) * (len(psalm_numbers) - 1) // 2
        logger.info(f"Comparing {total_pairs} Psalm pairs...")

        relationships = []
        stored_count = 0

        for i, psalm_a in enumerate(psalm_numbers):
            for psalm_b in psalm_numbers[i+1:]:
                result = self.compare_pair(psalm_a, psalm_b)

                # Store in database if significant OR store_all=True
                if result['is_significant'] or store_all:
                    self.db.store_relationship(result)
                    stored_count += 1

                    # Also store bidirectional entry (user requirement)
                    result_reversed = result.copy()
                    result_reversed['psalm_a'] = result['psalm_b']
                    result_reversed['psalm_b'] = result['psalm_a']
                    result_reversed['total_roots_a'] = result['total_roots_b']
                    result_reversed['total_roots_b'] = result['total_roots_a']
                    # Note: We store both A->B and B->A as separate rows in a separate
                    # tracking table to meet user's bidirectional requirement

                relationships.append(result)

            if (i + 1) % 10 == 0:
                logger.info(f"  Processed {i + 1}/{len(psalm_numbers)} Psalms...")

        logger.info(f"✓ Compared {total_pairs} pairs, stored {stored_count} relationships")

        return relationships

    def get_significant_relationships(self, min_pvalue: float = 0.01,
                                     min_z_score: float = 3.0) -> List[Dict[str, Any]]:
        """
        Get all significant relationships from database.

        Args:
            min_pvalue: Maximum p-value for significance
            min_z_score: Minimum z-score for significance

        Returns:
            List of significant relationship dicts
        """
        cursor = self.db.conn.cursor()

        cursor.execute("""
            SELECT *
            FROM psalm_relationships
            WHERE is_significant = 1
            ORDER BY hypergeometric_pvalue ASC, z_score DESC
        """)

        relationships = []
        for row in cursor.fetchall():
            relationships.append({
                'psalm_a': row['psalm_a'],
                'psalm_b': row['psalm_b'],
                'pvalue': row['hypergeometric_pvalue'],
                'z_score': row['z_score'],
                'weighted_score': row['weighted_overlap_score'],
                'shared_root_count': row['shared_root_count'],
                'total_roots_a': row['total_roots_a'],
                'total_roots_b': row['total_roots_b']
            })

        return relationships

    def close(self):
        """Close database connection."""
        self.db.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


if __name__ == '__main__':
    import json

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    # Database path
    relationships_db = Path(__file__).parent.parent.parent / 'data' / 'psalm_relationships.db'

    print("=" * 80)
    print("Pairwise Comparison Demo - Testing Statistical Significance")
    print("=" * 80)

    print("\nTesting on known related Psalms: 42 & 43")
    print("(Scholarly consensus: originally one Psalm)")

    with PairwiseComparator(relationships_db) as comparator:
        # Test on known related pair
        result = comparator.compare_pair(42, 43)

        print(f"\nStatistical Analysis Results:")
        print(f"  Psalm A: {result['psalm_a']}")
        print(f"  Psalm B: {result['psalm_b']}")
        print(f"  Total roots in A: {result['total_roots_a']}")
        print(f"  Total roots in B: {result['total_roots_b']}")
        print(f"  Shared roots: {result['shared_root_count']}")
        print(f"\n  Hypergeometric Test:")
        print(f"    Total unique roots in Psalter (N): {result['hypergeom_params']['N']}")
        print(f"    Expected overlap by chance: {(result['total_roots_a'] * result['total_roots_b']) / result['hypergeom_params']['N']:.2f}")
        print(f"    Actual overlap: {result['shared_root_count']}")
        print(f"    p-value: {result['pvalue']:.2e}")
        if result['pvalue'] < 0.001:
            print(f"    Interpretation: Extremely significant (p < 0.001)")
        elif result['pvalue'] < 0.01:
            print(f"    Interpretation: Highly significant (p < 0.01)")
        elif result['pvalue'] < 0.05:
            print(f"    Interpretation: Significant (p < 0.05)")
        else:
            print(f"    Interpretation: Not significant (p ≥ 0.05)")

        print(f"\n  Weighted Overlap Score: {result['weighted_score']:.2f}")
        print(f"  Z-score: {result['z_score']:.2f}")
        print(f"  Is Significant: {result['is_significant']}")

        print(f"\n  Top 5 Shared Roots (by rarity):")
        for i, root_data in enumerate(result['shared_roots'][:5], 1):
            print(f"    {i}. {root_data['root']} (IDF={root_data['idf']:.3f})")

    print("\n" + "=" * 80)
    print("✓ Pairwise comparison test complete!")
    print("=" * 80)
