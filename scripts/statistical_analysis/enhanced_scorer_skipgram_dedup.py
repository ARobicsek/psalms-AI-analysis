"""
Enhanced Scorer with Skipgram-Aware Hierarchical Deduplication

Implements comprehensive deduplication where:
1. Contiguous phrases take absolute priority (they're the most specific)
2. Skipgrams are deduplicated (no double-counting of subpatterns)
3. Roots appearing in phrases (contiguous or skipgram) are excluded

Deduplication approach:
- Remove contiguous from skipgram counts (contiguous phrases ARE skipgrams with gap=0)
- Apply combinatorial deduplication to skipgrams (longer patterns contain shorter ones)
- Exclude roots that appear in any phrase match
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import Counter
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def estimate_skipgram_deduplication(
    skipgram_2: int,
    skipgram_3: int,
    skipgram_4plus: int,
    contiguous_2: int,
    contiguous_3: int,
    contiguous_4plus: int
) -> Tuple[int, int, int]:
    """
    Estimate deduplicated skipgram counts.

    Rules:
    1. Contiguous phrases are also skipgrams - subtract them
    2. Longer skipgrams contain multiple shorter subpatterns - apply combinatorial deduction

    For a 4-word skipgram like "A...B...C...D":
    - Contains C(4,3) = 4 three-word subpatterns
    - Contains C(4,2) = 6 two-word subpatterns

    Args:
        skipgram_2, skipgram_3, skipgram_4plus: Skipgram counts by length
        contiguous_2, contiguous_3, contiguous_4plus: Contiguous phrase counts

    Returns:
        Tuple of (dedup_skip_2, dedup_skip_3, dedup_skip_4plus)
    """
    # Step 1: Remove contiguous from skipgrams (they're double-counted)
    skip_2_minus_contig = max(0, skipgram_2 - contiguous_2)
    skip_3_minus_contig = max(0, skipgram_3 - contiguous_3)
    skip_4_minus_contig = max(0, skipgram_4plus - contiguous_4plus)

    # Step 2: Apply combinatorial deduplication
    # Each 4-word skipgram generates:
    #   - C(4,3) = 4 three-word subpatterns
    #   - C(4,2) = 6 two-word subpatterns
    # Each 3-word skipgram generates:
    #   - C(3,2) = 3 two-word subpatterns

    # Estimate how many 3-word and 2-word skipgrams come from 4-word patterns
    from_4_to_3 = skip_4_minus_contig * 4  # C(4,3) = 4
    from_4_to_2 = skip_4_minus_contig * 6  # C(4,2) = 6

    # Deduplicate 3-word skipgrams
    skip_3_dedup = max(0, skip_3_minus_contig - from_4_to_3)

    # Estimate how many 2-word skipgrams come from remaining 3-word patterns
    from_3_to_2 = skip_3_dedup * 3  # C(3,2) = 3

    # Deduplicate 2-word skipgrams
    skip_2_dedup = max(0, skip_2_minus_contig - from_4_to_2 - from_3_to_2)

    # 4-word skipgrams are already at the top of hierarchy
    skip_4_dedup = skip_4_minus_contig

    return skip_2_dedup, skip_3_dedup, skip_4_dedup


def estimate_roots_in_skipgrams(
    shared_roots: List[Dict],
    roots_in_contiguous: Set[str],
    skipgram_pattern_count: int,
    contiguous_pattern_count: int
) -> Set[str]:
    """
    Estimate which additional roots appear in skipgrams beyond contiguous matches.

    Conservative approach: Assume skipgrams use similar vocabulary to contiguous,
    scaled by relative pattern counts.

    Args:
        shared_roots: All shared roots between the two psalms
        roots_in_contiguous: Set of roots that appear in contiguous phrases
        skipgram_pattern_count: Total number of skipgram patterns
        contiguous_pattern_count: Total number of contiguous patterns

    Returns:
        Set of root consonantal forms that likely appear in skipgrams
    """
    if skipgram_pattern_count == 0:
        return set()

    if contiguous_pattern_count == 0:
        # No contiguous phrases - be very conservative
        # Assume top 50% of roots by IDF might be in skipgrams
        sorted_roots = sorted(shared_roots, key=lambda r: r['idf'], reverse=True)
        n_roots_in_skipgrams = max(1, len(sorted_roots) // 2)
        return {r['root'] for r in sorted_roots[:n_roots_in_skipgrams]}

    # Estimate additional roots in skipgrams based on pattern ratio
    # If skipgrams are 3x as numerous as contiguous, assume they might use more vocabulary
    ratio = skipgram_pattern_count / contiguous_pattern_count

    # Conservative scaling: assume skipgrams use sqrt(ratio) times as many additional roots
    # (not linear because skipgrams share vocabulary)
    additional_root_fraction = min(0.5, math.sqrt(ratio) * 0.2)

    # Select highest IDF roots not in contiguous
    remaining_roots = [r for r in shared_roots if r['root'] not in roots_in_contiguous]
    sorted_remaining = sorted(remaining_roots, key=lambda r: r['idf'], reverse=True)

    n_additional = int(len(remaining_roots) * additional_root_fraction)
    additional_roots = {r['root'] for r in sorted_remaining[:n_additional]}

    return additional_roots


def calculate_skipgram_aware_deduplicated_score(
    psalm_a: int,
    psalm_b: int,
    shared_phrases: List[Dict],
    shared_roots: List[Dict],
    skipgram_counts: Dict[str, int],
    word_count_a: int,
    word_count_b: int,
    original_pvalue: float,
    original_rank: int
) -> Dict:
    """
    Calculate enhanced score with skipgram-aware hierarchical deduplication.

    Args:
        psalm_a, psalm_b: Psalm numbers
        shared_phrases: List of contiguous phrase dictionaries
        shared_roots: List of shared root dictionaries
        skipgram_counts: Dict with skipgram_2word, skipgram_3word, skipgram_4plus
        word_count_a, word_count_b: Word counts for each psalm
        original_pvalue: Original hypergeometric p-value
        original_rank: Original rank by p-value

    Returns:
        Dictionary with all scoring components
    """
    # Step 1: Deduplicate contiguous phrases (remove substrings)
    if not shared_phrases:
        deduplicated_contiguous = []
        roots_in_contiguous = set()
    else:
        sorted_phrases = sorted(shared_phrases, key=lambda p: p['length'], reverse=True)
        deduplicated_contiguous = []
        covered = set()

        for phrase in sorted_phrases:
            consonantal = phrase['consonantal']
            is_substring = False
            for included in deduplicated_contiguous:
                # Check if this phrase is substring of already-included phrase
                shorter_words = consonantal.split()
                longer_words = included['consonantal'].split()
                if len(shorter_words) < len(longer_words):
                    for i in range(len(longer_words) - len(shorter_words) + 1):
                        if longer_words[i:i+len(shorter_words)] == shorter_words:
                            is_substring = True
                            break
                if is_substring:
                    break

            if not is_substring:
                deduplicated_contiguous.append(phrase)

        # Extract roots from contiguous phrases
        roots_in_contiguous = set()
        for phrase in deduplicated_contiguous:
            roots = phrase['consonantal'].split()
            roots_in_contiguous.update(roots)

    # Count contiguous by length
    contiguous_2 = sum(1 for p in deduplicated_contiguous if p['length'] == 2)
    contiguous_3 = sum(1 for p in deduplicated_contiguous if p['length'] == 3)
    contiguous_4plus = sum(1 for p in deduplicated_contiguous if p['length'] >= 4)

    # Step 2: Deduplicate skipgrams
    skipgram_2_dedup, skipgram_3_dedup, skipgram_4_dedup = estimate_skipgram_deduplication(
        skipgram_2=skipgram_counts.get('skipgram_2word', 0),
        skipgram_3=skipgram_counts.get('skipgram_3word', 0),
        skipgram_4plus=skipgram_counts.get('skipgram_4plus', 0),
        contiguous_2=contiguous_2,
        contiguous_3=contiguous_3,
        contiguous_4plus=contiguous_4plus
    )

    # Step 3: Estimate additional roots in skipgrams
    total_skipgrams_dedup = skipgram_2_dedup + skipgram_3_dedup + skipgram_4_dedup
    total_contiguous = contiguous_2 + contiguous_3 + contiguous_4plus

    additional_roots_in_skipgrams = estimate_roots_in_skipgrams(
        shared_roots=shared_roots,
        roots_in_contiguous=roots_in_contiguous,
        skipgram_pattern_count=total_skipgrams_dedup,
        contiguous_pattern_count=total_contiguous
    )

    # Step 4: Deduplicate roots (exclude those in any phrase)
    all_roots_in_phrases = roots_in_contiguous | additional_roots_in_skipgrams
    deduplicated_roots = [r for r in shared_roots if r['root'] not in all_roots_in_phrases]

    # Step 5: Calculate pattern points (deduplicated)
    total_pattern_points = (
        (contiguous_2 + skipgram_2_dedup) * 1 +
        (contiguous_3 + skipgram_3_dedup) * 2 +
        (contiguous_4plus + skipgram_4_dedup) * 3
    )

    # Step 6: Calculate root IDF sum with rare root bonus (2x for IDF >= 4.0)
    root_idf_sum = 0.0
    for root in deduplicated_roots:
        idf = root['idf']
        if idf >= 4.0:
            root_idf_sum += idf * 2  # Rare root bonus
        else:
            root_idf_sum += idf

    # Step 7: Calculate geometric mean length
    geometric_mean_length = math.sqrt(word_count_a * word_count_b)

    # Step 8: Calculate normalized scores
    phrase_score = (total_pattern_points / geometric_mean_length) * 1000
    root_score = (root_idf_sum / geometric_mean_length) * 1000
    final_score = phrase_score + root_score

    # Return comprehensive result
    return {
        'psalm_a': psalm_a,
        'psalm_b': psalm_b,

        # Deduplication stats
        'original_phrase_count': len(shared_phrases),
        'deduplicated_contiguous_count': len(deduplicated_contiguous),
        'phrases_removed_as_substrings': len(shared_phrases) - len(deduplicated_contiguous),

        'original_skipgram_2': skipgram_counts.get('skipgram_2word', 0),
        'original_skipgram_3': skipgram_counts.get('skipgram_3word', 0),
        'original_skipgram_4plus': skipgram_counts.get('skipgram_4plus', 0),
        'deduplicated_skipgram_2': skipgram_2_dedup,
        'deduplicated_skipgram_3': skipgram_3_dedup,
        'deduplicated_skipgram_4plus': skipgram_4_dedup,

        'original_root_count': len(shared_roots),
        'deduplicated_root_count': len(deduplicated_roots),
        'roots_in_contiguous': len(roots_in_contiguous),
        'roots_in_skipgrams_est': len(additional_roots_in_skipgrams),
        'total_roots_removed': len(shared_roots) - len(deduplicated_roots),

        # Pattern counts (deduplicated)
        'contiguous_2word': contiguous_2,
        'contiguous_3word': contiguous_3,
        'contiguous_4plus': contiguous_4plus,
        'skipgram_2word_dedup': skipgram_2_dedup,
        'skipgram_3word_dedup': skipgram_3_dedup,
        'skipgram_4plus_dedup': skipgram_4_dedup,
        'total_pattern_points': total_pattern_points,

        # Root statistics (deduplicated)
        'shared_roots_count': len(deduplicated_roots),
        'root_idf_sum': root_idf_sum,

        # Psalm lengths
        'word_count_a': word_count_a,
        'word_count_b': word_count_b,
        'geometric_mean_length': geometric_mean_length,

        # Scores
        'phrase_score': phrase_score,
        'root_score': root_score,
        'final_score': final_score,

        # Original statistics
        'original_pvalue': original_pvalue,
        'original_rank': original_rank,

        # Deduplicated matches (for detailed output)
        'deduplicated_contiguous_phrases': deduplicated_contiguous,
        'deduplicated_roots': deduplicated_roots
    }


def main():
    """Calculate skipgram-aware deduplicated scores for all psalm relationships."""

    base_dir = Path(__file__).parent.parent.parent

    # Load inputs
    logger.info("Loading data files...")

    with open(base_dir / "data/analysis_results/significant_relationships.json", 'r', encoding='utf-8') as f:
        relationships = json.load(f)
    logger.info(f"  Loaded {len(relationships)} relationships")

    with open(base_dir / "data/analysis_results/enhanced_scores_full.json", 'r', encoding='utf-8') as f:
        enhanced_scores = json.load(f)
    logger.info(f"  Loaded {len(enhanced_scores)} enhanced scores with skipgram counts")

    # Create lookup for skipgram counts
    skipgram_lookup = {
        (s['psalm_a'], s['psalm_b']): {
            'skipgram_2word': s['skipgram_2word'],
            'skipgram_3word': s['skipgram_3word'],
            'skipgram_4plus': s['skipgram_4plus']
        }
        for s in enhanced_scores
    }

    with open(base_dir / "data/analysis_results/psalm_word_counts.json", 'r', encoding='utf-8') as f:
        word_counts_data = json.load(f)
        word_counts = word_counts_data['word_counts']
    logger.info(f"  Loaded word counts for {len(word_counts)} psalms")

    # Calculate skipgram-aware deduplicated scores
    logger.info("Calculating skipgram-aware deduplicated scores...")
    deduplicated_scores = []

    for i, rel in enumerate(relationships, 1):
        if i % 1000 == 0:
            logger.info(f"  Processing {i}/{len(relationships)}...")

        psalm_a = rel['psalm_a']
        psalm_b = rel['psalm_b']
        key = (psalm_a, psalm_b)

        if key not in skipgram_lookup:
            logger.warning(f"  No skipgram data for Psalms {psalm_a}-{psalm_b}, skipping")
            continue

        score_data = calculate_skipgram_aware_deduplicated_score(
            psalm_a=psalm_a,
            psalm_b=psalm_b,
            shared_phrases=rel['shared_phrases'],
            shared_roots=rel['shared_roots'],
            skipgram_counts=skipgram_lookup[key],
            word_count_a=word_counts[str(psalm_a)],
            word_count_b=word_counts[str(psalm_b)],
            original_pvalue=rel['pvalue'],
            original_rank=i
        )

        deduplicated_scores.append(score_data)

    # Save results
    output_path = base_dir / "data/analysis_results/enhanced_scores_skipgram_dedup.json"
    logger.info(f"Saving skipgram-aware deduplicated scores to {output_path}...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(deduplicated_scores, f, indent=2, ensure_ascii=False)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"  File size: {file_size_mb:.2f} MB")

    # Summary statistics
    logger.info("\nDeduplication Statistics:")

    total_phrases_removed = sum(s['phrases_removed_as_substrings'] for s in deduplicated_scores)
    total_roots_removed = sum(s['total_roots_removed'] for s in deduplicated_scores)
    total_skipgrams_removed = sum(
        (s['original_skipgram_2'] - s['deduplicated_skipgram_2']) +
        (s['original_skipgram_3'] - s['deduplicated_skipgram_3']) +
        (s['original_skipgram_4plus'] - s['deduplicated_skipgram_4plus'])
        for s in deduplicated_scores
    )

    logger.info(f"  Contiguous phrases removed as substrings: {total_phrases_removed:,}")
    logger.info(f"  Skipgrams removed (overlap with contiguous + internal dedup): {total_skipgrams_removed:,}")
    logger.info(f"  Roots removed (appear in phrases): {total_roots_removed:,}")

    # Score comparison
    scores = [s['final_score'] for s in deduplicated_scores]
    scores.sort(reverse=True)

    logger.info(f"\nScore Distribution:")
    logger.info(f"  Maximum: {scores[0]:.2f}")
    logger.info(f"  Top 100 cutoff: {scores[99]:.2f}")
    logger.info(f"  Top 300 cutoff: {scores[299]:.2f}")
    logger.info(f"  Minimum: {scores[-1]:.2f}")

    logger.info("\n✓ Complete!")


if __name__ == "__main__":
    main()
