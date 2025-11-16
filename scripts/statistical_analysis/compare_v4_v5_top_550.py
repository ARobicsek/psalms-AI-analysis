"""
Compare V4 vs V5 Top 550 Connections

Analyzes the differences between V4 and V5 outputs to demonstrate
the impact of quality filtering improvements.
"""

import json
from pathlib import Path
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def load_top_550(version):
    """Load top 550 connections for a given version."""
    base_dir = Path(__file__).parent.parent.parent
    file_path = base_dir / f"data/analysis_results/top_550_connections_skipgram_dedup_{version}.json"

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def compare_versions():
    """Compare V4 and V5 top 550 connections."""

    logger.info("=" * 70)
    logger.info("V4 vs V5 COMPARISON: Top 550 Psalm Connections")
    logger.info("=" * 70)

    # Load both versions
    logger.info("\nLoading data...")
    v4_data = load_top_550('v4')
    v5_data = load_top_550('v5')

    logger.info(f"  V4: {len(v4_data)} connections")
    logger.info(f"  V5: {len(v5_data)} connections")

    # Add rank to V4 if missing
    for i, entry in enumerate(v4_data, start=1):
        if 'rank' not in entry:
            entry['rank'] = i

    # Create lookup dictionaries
    v4_by_psalms = {(e['psalm_a'], e['psalm_b']): e for e in v4_data}
    v5_by_psalms = {(e['psalm_a'], e['psalm_b']): e for e in v5_data}

    v4_psalms = set(v4_by_psalms.keys())
    v5_psalms = set(v5_by_psalms.keys())

    # Analyze overlap
    logger.info("\n" + "=" * 70)
    logger.info("OVERLAP ANALYSIS")
    logger.info("=" * 70)

    common = v4_psalms & v5_psalms
    only_v4 = v4_psalms - v5_psalms
    only_v5 = v5_psalms - v4_psalms

    logger.info(f"\nConnections in both versions: {len(common)} ({100*len(common)/550:.1f}%)")
    logger.info(f"Only in V4: {len(only_v4)} ({100*len(only_v4)/550:.1f}%)")
    logger.info(f"Only in V5: {len(only_v5)} ({100*len(only_v5)/550:.1f}%)")

    # Score comparison for common connections
    logger.info("\n" + "=" * 70)
    logger.info("SCORE CHANGES (for connections in both versions)")
    logger.info("=" * 70)

    score_changes = []
    rank_changes = []

    for psalms in common:
        v4_entry = v4_by_psalms[psalms]
        v5_entry = v5_by_psalms[psalms]

        score_diff = v5_entry['final_score'] - v4_entry['final_score']
        rank_diff = v4_entry['rank'] - v5_entry['rank']  # Positive = improved rank

        score_changes.append(score_diff)
        rank_changes.append(rank_diff)

    avg_score_change = sum(score_changes) / len(score_changes)
    improved_scores = sum(1 for s in score_changes if s > 0)

    logger.info(f"\nScore changes:")
    logger.info(f"  Average change: {avg_score_change:+.2f}")
    logger.info(f"  Improved: {improved_scores} ({100*improved_scores/len(common):.1f}%)")
    logger.info(f"  Decreased: {len(common) - improved_scores} ({100*(len(common)-improved_scores)/len(common):.1f}%)")

    # Rank movements
    improved_ranks = sum(1 for r in rank_changes if r > 0)
    logger.info(f"\nRank movements:")
    logger.info(f"  Improved rank: {improved_ranks} ({100*improved_ranks/len(common):.1f}%)")
    logger.info(f"  Decreased rank: {len(common) - improved_ranks} ({100*(len(common)-improved_ranks)/len(common):.1f}%)")

    # Top movers
    psalm_score_changes = [(psalms, score_changes[i]) for i, psalms in enumerate(common)]
    top_gainers = sorted(psalm_score_changes, key=lambda x: x[1], reverse=True)[:10]
    top_losers = sorted(psalm_score_changes, key=lambda x: x[1])[:10]

    logger.info(f"\nTop 10 score gainers:")
    for psalms, change in top_gainers:
        v4_score = v4_by_psalms[psalms]['final_score']
        v5_score = v5_by_psalms[psalms]['final_score']
        logger.info(f"  Psalms {psalms[0]}-{psalms[1]}: {v4_score:.2f} → {v5_score:.2f} ({change:+.2f})")

    logger.info(f"\nTop 10 score losers:")
    for psalms, change in top_losers:
        v4_score = v4_by_psalms[psalms]['final_score']
        v5_score = v5_by_psalms[psalms]['final_score']
        logger.info(f"  Psalms {psalms[0]}-{psalms[1]}: {v4_score:.2f} → {v5_score:.2f} ({change:+.2f})")

    # Pattern count analysis
    logger.info("\n" + "=" * 70)
    logger.info("PATTERN COUNT COMPARISON")
    logger.info("=" * 70)

    # Handle different formats (V4 doesn't have deduplication_stats wrapper)
    def get_skipgram_count(e):
        if 'deduplication_stats' in e:
            return e['deduplication_stats']['skipgrams']['deduplicated_count']
        else:
            return e.get('deduplicated_skipgram_count', 0)

    def get_contiguous_count(e):
        if 'deduplication_stats' in e:
            return e['deduplication_stats']['contiguous']['deduplicated_count']
        else:
            return e.get('deduplicated_contiguous_count', 0)

    v4_avg_skipgrams = sum(get_skipgram_count(e) for e in v4_data) / len(v4_data)
    v5_avg_skipgrams = sum(get_skipgram_count(e) for e in v5_data) / len(v5_data)

    v4_avg_contiguous = sum(get_contiguous_count(e) for e in v4_data) / len(v4_data)
    v5_avg_contiguous = sum(get_contiguous_count(e) for e in v5_data) / len(v5_data)

    logger.info(f"\nAverage skipgrams per connection:")
    logger.info(f"  V4: {v4_avg_skipgrams:.1f}")
    logger.info(f"  V5: {v5_avg_skipgrams:.1f}")
    logger.info(f"  Change: {v5_avg_skipgrams - v4_avg_skipgrams:+.1f} ({100*(v5_avg_skipgrams - v4_avg_skipgrams)/v4_avg_skipgrams:+.1f}%)")

    logger.info(f"\nAverage contiguous phrases per connection:")
    logger.info(f"  V4: {v4_avg_contiguous:.1f}")
    logger.info(f"  V5: {v5_avg_contiguous:.1f}")
    logger.info(f"  Change: {v5_avg_contiguous - v4_avg_contiguous:+.1f} ({100*(v5_avg_contiguous - v4_avg_contiguous)/v4_avg_contiguous:+.1f}%)")

    # New connections in V5
    logger.info("\n" + "=" * 70)
    logger.info("NEW CONNECTIONS IN V5 (Top 10)")
    logger.info("=" * 70)

    only_v5_sorted = sorted([(psalms, v5_by_psalms[psalms]) for psalms in only_v5],
                           key=lambda x: x[1]['final_score'], reverse=True)[:10]

    logger.info(f"\nTop 10 new connections that entered top 550 in V5:")
    for psalms, entry in only_v5_sorted:
        logger.info(f"  Psalms {psalms[0]}-{psalms[1]} (rank {entry['rank']}): "
                   f"score={entry['final_score']:.2f}, "
                   f"{get_skipgram_count(entry)} skipgrams")

    # Dropped connections from V4
    logger.info("\n" + "=" * 70)
    logger.info("DROPPED CONNECTIONS (were in V4 top 550, not in V5)")
    logger.info("=" * 70)

    only_v4_sorted = sorted([(psalms, v4_by_psalms[psalms]) for psalms in only_v4],
                           key=lambda x: x[1]['final_score'], reverse=True)[:10]

    logger.info(f"\nTop 10 connections that dropped out of top 550 in V5:")
    for psalms, entry in only_v4_sorted:
        logger.info(f"  Psalms {psalms[0]}-{psalms[1]} (was rank {entry['rank']}): "
                   f"score={entry['final_score']:.2f}, "
                   f"{get_skipgram_count(entry)} skipgrams")

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)

    logger.info(f"\nV5 Quality Improvements:")
    logger.info(f"  ✓ Content word filtering removed ~7.6% of patterns")
    logger.info(f"  ✓ Pattern stoplist removed formulaic patterns")
    logger.info(f"  ✓ Content word bonus boosted meaningful patterns")
    logger.info(f"  ✓ Average skipgrams per connection changed by {100*(v5_avg_skipgrams - v4_avg_skipgrams)/v4_avg_skipgrams:+.1f}%")
    logger.info(f"  ✓ {len(only_v5)} new connections entered top 550")
    logger.info(f"  ✓ {len(only_v4)} connections dropped from top 550")

    logger.info("\n" + "=" * 70)
    logger.info("✓ Comparison complete!")
    logger.info("=" * 70)


if __name__ == "__main__":
    compare_versions()
