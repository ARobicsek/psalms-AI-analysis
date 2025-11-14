#!/usr/bin/env python3
"""
Compare V2 vs V3 Results

Generates a comparison report showing differences between V2 and V3:
- Top 10 rankings comparison
- Score changes for known duplicates
- Deduplication effectiveness
- Example from rank 500 issue (Psalms 50-82)
"""

import json
import sys
from pathlib import Path

def load_json(filepath):
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    # Load V2 and V3 results
    v2_top_500 = load_json('../../data/analysis_results/top_500_connections_skipgram_dedup_v2.json')
    v3_top_500 = load_json('../../data/analysis_results/top_500_connections_skipgram_dedup_v3.json')

    # Create lookup dicts
    v2_dict = {(entry['psalm_a'], entry['psalm_b']): entry for entry in v2_top_500}
    v3_dict = {(entry['psalm_a'], entry['psalm_b']): entry for entry in v3_top_500}

    print("=" * 80)
    print("V2 VS V3 COMPARISON REPORT")
    print("=" * 80)
    print()

    # Top 10 comparison
    print("TOP 10 RANKINGS COMPARISON")
    print("-" * 80)
    print(f"{'Rank':<6} {'V2 Pair':<15} {'V2 Score':<12} {'V3 Pair':<15} {'V3 Score':<12}")
    print("-" * 80)

    for i in range(min(10, len(v2_top_500), len(v3_top_500))):
        v2_entry = v2_top_500[i]
        v3_entry = v3_top_500[i]

        v2_pair = f"{v2_entry['psalm_a']}-{v2_entry['psalm_b']}"
        v3_pair = f"{v3_entry['psalm_a']}-{v3_entry['psalm_b']}"

        print(f"{i+1:<6} {v2_pair:<15} {v2_entry['final_score']:<12.2f} {v3_pair:<15} {v3_entry['final_score']:<12.2f}")

    print()
    print()

    # Known duplicate pairs comparison
    print("KNOWN DUPLICATE PAIRS - SCORE CHANGES")
    print("-" * 80)
    known_pairs = [(14, 53), (60, 108), (40, 70), (42, 43)]

    print(f"{'Pair':<12} {'V2 Score':<15} {'V3 Score':<15} {'Change':<15} {'% Change':<10}")
    print("-" * 80)

    for pair in known_pairs:
        if pair in v2_dict and pair in v3_dict:
            v2_score = v2_dict[pair]['final_score']
            v3_score = v3_dict[pair]['final_score']
            change = v3_score - v2_score
            pct_change = (change / v2_score) * 100 if v2_score > 0 else 0

            pair_str = f"{pair[0]}-{pair[1]}"
            print(f"{pair_str:<12} {v2_score:<15.2f} {v3_score:<15.2f} {change:+15.2f} {pct_change:+10.1f}%")

    print()
    print()

    # Rank 500 issue example (Psalms 50-82)
    print("RANK 500 ISSUE EXAMPLE: Psalms 50-82 (Asaph Collection)")
    print("-" * 80)

    pair_50_82 = (50, 82)
    if pair_50_82 in v2_dict:
        v2_entry = v2_dict[pair_50_82]
        print(f"V2 Rank: {v2_top_500.index(v2_entry) + 1}")
        print(f"V2 Score: {v2_entry['final_score']:.2f}")
        print(f"V2 Deduplicated Contiguous: {len(v2_entry.get('deduplicated_contiguous_phrases', []))}")
        print(f"V2 Deduplicated Skipgrams: {len(v2_entry.get('deduplicated_skipgrams', []))}")

    if pair_50_82 in v3_dict:
        v3_entry = v3_dict[pair_50_82]
        print(f"\nV3 Rank: {v3_top_500.index(v3_entry) + 1}")
        print(f"V3 Score: {v3_entry['final_score']:.2f}")
        print(f"V3 Deduplicated Contiguous: {len(v3_entry.get('deduplicated_contiguous_phrases', []))}")
        print(f"V3 Deduplicated Skipgrams: {len(v3_entry.get('deduplicated_skipgrams', []))}")

        if pair_50_82 in v2_dict:
            score_diff = v3_entry['final_score'] - v2_entry['final_score']
            print(f"\nScore Change: {score_diff:+.2f} ({(score_diff/v2_entry['final_score'])*100:+.1f}%)")

    print()
    print()

    # Overall statistics
    print("OVERALL STATISTICS")
    print("-" * 80)

    print("\nV2 Statistics:")
    v2_scores = [entry['final_score'] for entry in v2_top_500]
    print(f"  Top score: {max(v2_scores):.2f}")
    print(f"  Cutoff score (rank 500): {min(v2_scores):.2f}")
    print(f"  Average score: {sum(v2_scores)/len(v2_scores):.2f}")

    print("\nV3 Statistics:")
    v3_scores = [entry['final_score'] for entry in v3_top_500]
    print(f"  Top score: {max(v3_scores):.2f}")
    print(f"  Cutoff score (rank 500): {min(v3_scores):.2f}")
    print(f"  Average score: {sum(v3_scores)/len(v3_scores):.2f}")

    print()
    print()

    # Deduplication effectiveness
    print("DEDUPLICATION EFFECTIVENESS")
    print("-" * 80)

    v2_total_dedup = sum(entry.get('deduplication_stats', {}).get('total_removed', 0) for entry in v2_top_500)
    v3_total_dedup = sum(entry.get('deduplication_stats', {}).get('total_removed', 0) for entry in v3_top_500)

    print(f"V2 Total items deduplicated: {v2_total_dedup:,}")
    print(f"V3 Total items deduplicated: {v3_total_dedup:,}")
    print(f"Difference: {v3_total_dedup - v2_total_dedup:+,} ({((v3_total_dedup - v2_total_dedup)/v2_total_dedup)*100:+.1f}%)")

    print()
    print("=" * 80)
    print("KEY IMPROVEMENTS IN V3:")
    print("=" * 80)
    print("1. Text cleaning: Paragraph markers ({פ}, {ס}) removed from analysis")
    print("2. Root consistency: Skipgrams now use root extraction (like contiguous)")
    print("3. Better deduplication: Contiguous phrases properly removed when subsumed by skipgrams")
    print("4. Verse-level details: Shows which verses contain each phrase/root match")
    print("=" * 80)

if __name__ == '__main__':
    main()
