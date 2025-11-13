"""
Frequency Analyzer for Psalm Roots

Computes root frequencies across all 150 Psalms and calculates
IDF (Inverse Document Frequency) scores to identify rare vs. common roots.

IDF Formula: log(150 / psalm_count)
- Higher IDF = rarer root (appears in few Psalms)
- Lower IDF = common root (appears in many Psalms)
"""

import sys
from pathlib import Path
import math
from typing import Dict, List, Tuple, Any
from collections import Counter
import logging

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent))

from root_extractor import RootExtractor
from database_builder import PsalmRelationshipsDB

logger = logging.getLogger(__name__)


class FrequencyAnalyzer:
    """Analyzes root frequencies across the Psalter."""

    def __init__(self, tanakh_db_path: Path, relationships_db_path: Path = None):
        """
        Initialize frequency analyzer.

        Args:
            tanakh_db_path: Path to tanakh.db
            relationships_db_path: Path to psalm_relationships.db (optional)
        """
        self.tanakh_db_path = tanakh_db_path
        self.extractor = RootExtractor(tanakh_db_path)
        self.relationships_db = PsalmRelationshipsDB(relationships_db_path)

    def extract_all_psalm_roots(self, psalm_numbers: List[int] = None) -> Dict[int, Dict[str, Any]]:
        """
        Extract roots from specified Psalms (or all 150 by default).

        Args:
            psalm_numbers: List of psalm numbers to process, or None for all 150

        Returns:
            Dict mapping psalm_number -> {roots, phrases}
        """
        if psalm_numbers is None:
            psalm_numbers = list(range(1, 151))  # All 150 Psalms

        results = {}

        for psalm_num in psalm_numbers:
            logger.info(f"Extracting roots from Psalm {psalm_num}...")

            result = self.extractor.extract_psalm_roots(psalm_num, include_phrases=True)
            results[psalm_num] = result

            # Store in database
            self.relationships_db.store_psalm_roots(psalm_num, result['roots'])

            if result['phrases']:
                # Group phrases by unique consonantal form
                phrase_groups = {}
                for phrase in result['phrases']:
                    key = phrase['consonantal']
                    if key not in phrase_groups:
                        phrase_groups[key] = {
                            'consonantal': phrase['consonantal'],
                            'hebrew': phrase['hebrew'],  # Keep first example
                            'length': phrase['length'],
                            'count': 0,
                            'verses': []
                        }
                    phrase_groups[key]['count'] += 1
                    phrase_groups[key]['verses'].append(phrase['verse'])

                self.relationships_db.store_psalm_phrases(
                    psalm_num,
                    list(phrase_groups.values())
                )

        logger.info(f"Extracted roots from {len(results)} Psalms")
        return results

    def compute_frequencies(self):
        """
        Compute root frequencies and IDF scores across all Psalms.
        Updates the database with calculated values.
        """
        logger.info("Computing root frequencies and IDF scores...")
        self.relationships_db.update_root_frequencies()
        logger.info("✓ Frequencies computed and stored")

    def get_rarity_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about root rarity distribution.

        Returns:
            Dict with percentile thresholds and counts
        """
        cursor = self.relationships_db.conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_roots,
                AVG(idf_score) as avg_idf,
                MIN(idf_score) as min_idf,
                MAX(idf_score) as max_idf
            FROM root_frequencies
            WHERE psalm_count > 0
        """)

        row = cursor.fetchone()

        # Get percentile thresholds
        cursor.execute("""
            SELECT idf_score
            FROM root_frequencies
            WHERE psalm_count > 0
            ORDER BY idf_score
        """)

        idf_values = [r['idf_score'] for r in cursor.fetchall()]

        def percentile(values, p):
            idx = int(len(values) * p / 100)
            return values[min(idx, len(values) - 1)]

        stats = {
            'total_roots': row['total_roots'],
            'avg_idf': row['avg_idf'],
            'min_idf': row['min_idf'],
            'max_idf': row['max_idf'],
            'idf_percentiles': {
                '25th': percentile(idf_values, 25),
                '50th': percentile(idf_values, 50),
                '75th': percentile(idf_values, 75),
                '90th': percentile(idf_values, 90),
                '95th': percentile(idf_values, 95),
            }
        }

        return stats

    def get_rarest_roots(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get the rarest roots (highest IDF scores).

        Args:
            limit: Number of roots to return

        Returns:
            List of root dicts with idf_score, psalm_count, total_occurrences
        """
        cursor = self.relationships_db.conn.cursor()

        cursor.execute("""
            SELECT
                root_consonantal,
                idf_score,
                psalm_count,
                total_occurrences
            FROM root_frequencies
            WHERE psalm_count > 0
            ORDER BY idf_score DESC
            LIMIT ?
        """, (limit,))

        results = []
        for row in cursor.fetchall():
            results.append({
                'root': row['root_consonantal'],
                'idf': row['idf_score'],
                'psalm_count': row['psalm_count'],
                'total_occurrences': row['total_occurrences']
            })

        return results

    def get_commonest_roots(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get the most common roots (lowest IDF scores).

        Args:
            limit: Number of roots to return

        Returns:
            List of root dicts with idf_score, psalm_count, total_occurrences
        """
        cursor = self.relationships_db.conn.cursor()

        cursor.execute("""
            SELECT
                root_consonantal,
                idf_score,
                psalm_count,
                total_occurrences
            FROM root_frequencies
            WHERE psalm_count > 0
            ORDER BY idf_score ASC
            LIMIT ?
        """, (limit,))

        results = []
        for row in cursor.fetchall():
            results.append({
                'root': row['root_consonantal'],
                'idf': row['idf_score'],
                'psalm_count': row['psalm_count'],
                'total_occurrences': row['total_occurrences']
            })

        return results

    def classify_rarity(self, idf_score: float, stats: Dict[str, Any]) -> str:
        """
        Classify a root's rarity based on its IDF score.

        Args:
            idf_score: IDF score for the root
            stats: Rarity statistics from get_rarity_statistics()

        Returns:
            Rarity classification string
        """
        percentiles = stats['idf_percentiles']

        if idf_score >= percentiles['95th']:
            return "extremely rare (top 5%)"
        elif idf_score >= percentiles['90th']:
            return "very rare (top 10%)"
        elif idf_score >= percentiles['75th']:
            return "rare (top 25%)"
        elif idf_score >= percentiles['50th']:
            return "moderately rare (above median)"
        elif idf_score >= percentiles['25th']:
            return "somewhat common"
        else:
            return "very common (bottom 25%)"

    def close(self):
        """Close all connections."""
        self.extractor.close()
        self.relationships_db.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


if __name__ == '__main__':
    import sys
    from pathlib import Path

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    # Database paths
    tanakh_db = Path(__file__).parent.parent.parent / 'database' / 'tanakh.db'
    relationships_db = Path(__file__).parent.parent.parent / 'data' / 'psalm_relationships.db'

    if not tanakh_db.exists():
        print(f"ERROR: tanakh.db not found at {tanakh_db}")
        sys.exit(1)

    print("=" * 70)
    print("Frequency Analysis Demo - Sample Psalms")
    print("=" * 70)
    print("\nProcessing sample Psalms: 1, 23, 117 (shortest), 119 (longest)...\n")

    with FrequencyAnalyzer(tanakh_db, relationships_db) as analyzer:
        # Extract from sample psalms
        sample_psalms = [1, 23, 117, 119]
        results = analyzer.extract_all_psalm_roots(sample_psalms)

        print(f"✓ Extracted roots from {len(results)} sample Psalms")

        # Compute frequencies
        analyzer.compute_frequencies()

        # Get statistics
        stats = analyzer.get_rarity_statistics()

        print("\n" + "=" * 70)
        print("Root Rarity Statistics (based on sample)")
        print("=" * 70)
        print(f"Total unique roots: {stats['total_roots']}")
        print(f"Average IDF score: {stats['avg_idf']:.3f}")
        print(f"IDF range: {stats['min_idf']:.3f} to {stats['max_idf']:.3f}")
        print("\nIDF Percentiles:")
        for percentile, value in stats['idf_percentiles'].items():
            print(f"  {percentile}: {value:.3f}")

        # Show rarest roots
        print("\n" + "=" * 70)
        print("Top 10 Rarest Roots (highest IDF scores)")
        print("=" * 70)
        rarest = analyzer.get_rarest_roots(10)
        for i, root in enumerate(rarest, 1):
            rarity = analyzer.classify_rarity(root['idf'], stats)
            print(f"{i:2d}. {root['root']:8s} | IDF={root['idf']:.3f} | "
                  f"Appears in {root['psalm_count']} Psalm(s), "
                  f"{root['total_occurrences']} occurrence(s) | {rarity}")

        # Show commonest roots
        print("\n" + "=" * 70)
        print("Top 10 Most Common Roots (lowest IDF scores)")
        print("=" * 70)
        commonest = analyzer.get_commonest_roots(10)
        for i, root in enumerate(commonest, 1):
            rarity = analyzer.classify_rarity(root['idf'], stats)
            print(f"{i:2d}. {root['root']:8s} | IDF={root['idf']:.3f} | "
                  f"Appears in {root['psalm_count']} Psalm(s), "
                  f"{root['total_occurrences']} occurrence(s) | {rarity}")

    print("\n" + "=" * 70)
    print("✓ Frequency analysis demo complete!")
    print("=" * 70)
