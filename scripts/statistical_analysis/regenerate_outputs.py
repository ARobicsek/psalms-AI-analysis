"""
Regenerate Output Files with Shared Roots and Phrases

This script regenerates the output JSON files from the existing database,
now including shared roots and phrases for each relationship.
"""

import sys
from pathlib import Path
import json
import logging

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent))

from pairwise_comparator import PairwiseComparator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


def regenerate_outputs():
    """Regenerate output files with shared roots and phrases included."""

    # Set up paths
    relationships_db = Path(__file__).parent.parent.parent / 'data' / 'psalm_relationships.db'
    output_dir = Path(__file__).parent.parent.parent / 'data' / 'analysis_results'

    print("=" * 80)
    print("Regenerating Output Files with Shared Roots and Phrases")
    print("=" * 80)

    print(f"\nDatabase: {relationships_db}")
    print(f"Output directory: {output_dir}")

    # Get significant relationships with shared items
    print("\nRetrieving relationships from database...")
    with PairwiseComparator(relationships_db) as comparator:
        # Get relationships WITH shared roots and phrases
        significant = comparator.get_significant_relationships(include_shared_items=True)

    print(f"✓ Retrieved {len(significant)} significant relationships")

    # Check if we have phrases
    has_phrases = any(len(rel.get('shared_phrases', [])) > 0 for rel in significant[:10])
    total_phrases = sum(len(rel.get('shared_phrases', [])) for rel in significant)

    print(f"\nPhrase data status:")
    print(f"  Total shared phrases across all relationships: {total_phrases}")
    if has_phrases:
        print(f"  ✓ Phrase data found in database")
    else:
        print(f"  ⚠ No phrase data found - database may need to be rebuilt")

    # Save significant relationships with full data
    report_file = output_dir / 'significant_relationships.json'
    print(f"\nSaving significant relationships to {report_file.name}...")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(significant, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved {len(significant)} relationships")

    # Create bidirectional table
    print(f"\nGenerating bidirectional relationships...")
    bidirectional = []
    for rel in significant:
        phrase_count = rel.get('shared_phrase_count', len(rel.get('shared_phrases', [])))

        # Add A→B entry
        bidirectional.append({
            'from_psalm': rel['psalm_a'],
            'to_psalm': rel['psalm_b'],
            'pvalue': rel['pvalue'],
            'z_score': rel['z_score'],
            'weighted_score': rel['weighted_score'],
            'shared_root_count': rel['shared_root_count'],
            'shared_phrase_count': phrase_count
        })

        # Add B→A entry
        bidirectional.append({
            'from_psalm': rel['psalm_b'],
            'to_psalm': rel['psalm_a'],
            'pvalue': rel['pvalue'],
            'z_score': rel['z_score'],
            'weighted_score': rel['weighted_score'],
            'shared_root_count': rel['shared_root_count'],
            'shared_phrase_count': phrase_count
        })

    # Sort by from_psalm, then by pvalue
    bidirectional.sort(key=lambda x: (x['from_psalm'], x['pvalue']))

    bidirectional_file = output_dir / 'bidirectional_relationships.json'
    print(f"Saving bidirectional relationships to {bidirectional_file.name}...")
    with open(bidirectional_file, 'w', encoding='utf-8') as f:
        json.dump(bidirectional, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved {len(bidirectional)} bidirectional entries")

    # Display top 10 relationships with details
    print("\n" + "=" * 80)
    print("Top 10 Most Significant Relationships")
    print("=" * 80)
    print(f"\n{'Rank':<6} {'Psalms':<12} {'p-value':<12} {'Roots':<8} {'Phrases':<9} {'Top Shared Roots':<40}")
    print('-' * 100)

    for i, rel in enumerate(significant[:10], 1):
        psalms_str = f"{rel['psalm_a']}-{rel['psalm_b']}"
        phrase_count = rel.get('shared_phrase_count', len(rel.get('shared_phrases', [])))

        # Get top 3 shared roots
        top_roots = ', '.join([r['root'] for r in rel.get('shared_roots', [])[:3]])
        if len(rel.get('shared_roots', [])) > 3:
            top_roots += f" (+{len(rel['shared_roots']) - 3} more)"

        print(f"{i:<6} {psalms_str:<12} {rel['pvalue']:<12.2e} {rel['shared_root_count']:<8} "
              f"{phrase_count:<9} {top_roots:<40}")

    # Show example with full details
    print("\n" + "=" * 80)
    print("Example: Psalms 14 & 53 (Most Significant Relationship)")
    print("=" * 80)

    top_rel = significant[0]
    print(f"\nStatistical Measures:")
    print(f"  p-value: {top_rel['pvalue']:.2e}")
    print(f"  Z-score: {top_rel['z_score']:.2f}")
    print(f"  Weighted score: {top_rel['weighted_score']:.2f}")
    print(f"  Shared root count: {top_rel['shared_root_count']}")
    print(f"  Shared phrase count: {top_rel.get('shared_phrase_count', len(top_rel.get('shared_phrases', [])))}")

    print(f"\nTop 10 Shared Roots (by rarity/IDF):")
    for i, root in enumerate(top_rel.get('shared_roots', [])[:10], 1):
        print(f"  {i:2d}. {root['root']:8s} (IDF={root['idf']:.3f}, "
              f"occurs {root['count_a']}x in Ps {top_rel['psalm_a']}, "
              f"{root['count_b']}x in Ps {top_rel['psalm_b']})")

    if top_rel.get('shared_phrases'):
        print(f"\nTop 5 Shared Phrases:")
        for i, phrase in enumerate(top_rel.get('shared_phrases', [])[:5], 1):
            print(f"  {i}. {phrase['hebrew']} ({phrase['consonantal']})")
            print(f"     Length: {phrase['length']} words, "
                  f"occurs {phrase['count_a']}x in Ps {top_rel['psalm_a']}, "
                  f"{phrase['count_b']}x in Ps {top_rel['psalm_b']}")
    else:
        print(f"\n⚠ No phrase data available for this relationship")

    print("\n" + "=" * 80)
    print("✓ Output regeneration complete!")
    print("=" * 80)
    print(f"\nFiles updated:")
    print(f"  - {report_file}")
    print(f"  - {bidirectional_file}")
    print()


if __name__ == '__main__':
    regenerate_outputs()
