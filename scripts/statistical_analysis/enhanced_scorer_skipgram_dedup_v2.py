"""
Enhanced Scorer with Skipgram-Aware Hierarchical Deduplication - Version 2

Updates from V1:
1. Filters out single root matches with IDF < 0.5 (very common words)
2. Includes deduplicated skipgram details in output (not just counts)

Implements comprehensive deduplication where:
1. Contiguous phrases take absolute priority (they're the most specific)
2. Skipgrams are deduplicated (no double-counting of subpatterns)
3. Roots appearing in phrases (contiguous or skipgram) are excluded
4. Very common roots (IDF < 0.5) are excluded from single root matches
   (but still counted if they appear in phrase/skipgram matches)
"""

import json
import math
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import Counter
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Constants
IDF_THRESHOLD_FOR_SINGLE_ROOTS = 0.5  # Very common words excluded from single root matches


def load_shared_skipgrams(db_path: Path, psalm_a: int, psalm_b: int) -> List[Dict]:
    """
    Load shared skipgrams between two psalms from database.

    Args:
        db_path: Path to psalm_relationships.db
        psalm_a, psalm_b: Psalm numbers

    Returns:
        List of shared skipgram dictionaries with pattern and length
    """
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get skipgrams for psalm A
    cursor.execute("""
        SELECT pattern_consonantal, pattern_length
        FROM psalm_skipgrams
        WHERE psalm_number = ?
    """, (psalm_a,))
    skipgrams_a = {(row['pattern_consonantal'], row['pattern_length'])
                   for row in cursor.fetchall()}

    # Get skipgrams for psalm B
    cursor.execute("""
        SELECT pattern_consonantal, pattern_length
        FROM psalm_skipgrams
        WHERE psalm_number = ?
    """, (psalm_b,))
    skipgrams_b = {(row['pattern_consonantal'], row['pattern_length'])
                   for row in cursor.fetchall()}

    conn.close()

    # Find shared skipgrams
    shared = []
    for (consonantal, length) in skipgrams_a:
        if (consonantal, length) in skipgrams_b:
            shared.append({
                'consonantal': consonantal,
                'length': length,
                'hebrew': consonantal  # Use consonantal as Hebrew (can be enhanced later)
            })

    return shared


def deduplicate_skipgrams(
    skipgrams: List[Dict],
    contiguous_phrases: List[Dict]
) -> List[Dict]:
    """
    Deduplicate skipgrams by removing:
    1. Skipgrams that are identical to contiguous phrases (gap=0)
    2. Shorter skipgrams that are subpatterns of longer skipgrams

    Args:
        skipgrams: List of skipgram dictionaries
        contiguous_phrases: List of contiguous phrase dictionaries

    Returns:
        List of deduplicated skipgram dictionaries
    """
    # Create set of contiguous patterns for fast lookup
    contiguous_patterns = {p['consonantal'] for p in contiguous_phrases}

    # Remove skipgrams that are identical to contiguous phrases
    non_contiguous = [s for s in skipgrams if s['consonantal'] not in contiguous_patterns]

    # Sort by length descending for deduplication
    sorted_skipgrams = sorted(non_contiguous, key=lambda s: s['length'], reverse=True)

    deduplicated = []
    covered_patterns = set()

    for skipgram in sorted_skipgrams:
        pattern_words = skipgram['consonantal'].split()
        pattern_tuple = tuple(pattern_words)

        # Check if this is a subpattern of any already-included skipgram
        is_subpattern = False
        for covered in covered_patterns:
            covered_words = list(covered)
            # Check if pattern_words is a subsequence of covered_words
            if len(pattern_words) < len(covered_words):
                # Use a simple subsequence check
                j = 0
                for word in pattern_words:
                    while j < len(covered_words) and covered_words[j] != word:
                        j += 1
                    if j >= len(covered_words):
                        break
                    j += 1
                else:
                    # Found all words in order - this is a subpattern
                    is_subpattern = True
                    break

        if not is_subpattern:
            deduplicated.append(skipgram)
            covered_patterns.add(pattern_tuple)

    return deduplicated


def estimate_skipgram_deduplication(
    skipgram_2: int,
    skipgram_3: int,
    skipgram_4plus: int,
    contiguous_2: int,
    contiguous_3: int,
    contiguous_4plus: int
) -> Tuple[int, int, int]:
    """
    Estimate deduplicated skipgram counts (for statistics).

    This is kept for backward compatibility with reports,
    but actual deduplication is now done on real patterns.
    """
    skip_2_minus_contig = max(0, skipgram_2 - contiguous_2)
    skip_3_minus_contig = max(0, skipgram_3 - contiguous_3)
    skip_4_minus_contig = max(0, skipgram_4plus - contiguous_4plus)

    from_4_to_3 = skip_4_minus_contig * 4
    from_4_to_2 = skip_4_minus_contig * 6

    skip_3_dedup = max(0, skip_3_minus_contig - from_4_to_3)
    from_3_to_2 = skip_3_dedup * 3
    skip_2_dedup = max(0, skip_2_minus_contig - from_4_to_2 - from_3_to_2)
    skip_4_dedup = skip_4_minus_contig

    return skip_2_dedup, skip_3_dedup, skip_4_dedup


def estimate_roots_in_skipgrams(
    shared_roots: List[Dict],
    roots_in_contiguous: Set[str],
    deduplicated_skipgrams: List[Dict]
) -> Set[str]:
    """
    Estimate which additional roots appear in deduplicated skipgrams.

    Now uses actual skipgram patterns instead of just counts.
    """
    if not deduplicated_skipgrams:
        return set()

    # Extract roots from skipgram patterns
    roots_in_skipgrams = set()
    for skipgram in deduplicated_skipgrams:
        words = skipgram['consonantal'].split()
        roots_in_skipgrams.update(words)

    # Remove roots already in contiguous
    additional_roots = roots_in_skipgrams - roots_in_contiguous

    return additional_roots


def calculate_skipgram_aware_deduplicated_score(
    psalm_a: int,
    psalm_b: int,
    shared_phrases: List[Dict],
    shared_roots: List[Dict],
    shared_skipgrams: List[Dict],
    skipgram_counts: Dict[str, int],
    word_count_a: int,
    word_count_b: int,
    original_pvalue: float,
    original_rank: int
) -> Dict:
    """
    Calculate enhanced score with skipgram-aware hierarchical deduplication.

    Version 2 changes:
    - Filters out roots with IDF < 0.5 from single root matches
    - Returns actual deduplicated skipgram patterns
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

    # Step 2: Deduplicate skipgrams (remove overlap with contiguous and subpatterns)
    deduplicated_skipgrams = deduplicate_skipgrams(shared_skipgrams, deduplicated_contiguous)

    # Count deduplicated skipgrams by length
    skipgram_2_actual = sum(1 for s in deduplicated_skipgrams if s['length'] == 2)
    skipgram_3_actual = sum(1 for s in deduplicated_skipgrams if s['length'] == 3)
    skipgram_4_actual = sum(1 for s in deduplicated_skipgrams if s['length'] >= 4)

    # Also calculate estimated counts for comparison
    skipgram_2_est, skipgram_3_est, skipgram_4_est = estimate_skipgram_deduplication(
        skipgram_2=skipgram_counts.get('skipgram_2word', 0),
        skipgram_3=skipgram_counts.get('skipgram_3word', 0),
        skipgram_4plus=skipgram_counts.get('skipgram_4plus', 0),
        contiguous_2=contiguous_2,
        contiguous_3=contiguous_3,
        contiguous_4plus=contiguous_4plus
    )

    # Step 3: Find additional roots in skipgrams
    additional_roots_in_skipgrams = estimate_roots_in_skipgrams(
        shared_roots=shared_roots,
        roots_in_contiguous=roots_in_contiguous,
        deduplicated_skipgrams=deduplicated_skipgrams
    )

    # Step 4: Deduplicate roots
    # Exclude roots that appear in any phrase (contiguous or skipgram)
    all_roots_in_phrases = roots_in_contiguous | additional_roots_in_skipgrams

    # ALSO exclude very common roots (IDF < 0.5) from single root matches
    deduplicated_roots = [
        r for r in shared_roots
        if r['root'] not in all_roots_in_phrases and r['idf'] >= IDF_THRESHOLD_FOR_SINGLE_ROOTS
    ]

    # Count how many were filtered for IDF
    roots_filtered_by_idf = sum(
        1 for r in shared_roots
        if r['root'] not in all_roots_in_phrases and r['idf'] < IDF_THRESHOLD_FOR_SINGLE_ROOTS
    )

    # Step 5: Calculate pattern points (deduplicated)
    total_pattern_points = (
        (contiguous_2 + skipgram_2_actual) * 1 +
        (contiguous_3 + skipgram_3_actual) * 2 +
        (contiguous_4plus + skipgram_4_actual) * 3
    )

    # Step 6: Calculate root IDF sum with rare root bonus (2x for IDF >= 4.0)
    # Only from roots that passed the IDF >= 0.5 filter
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

        'original_skipgram_count': len(shared_skipgrams),
        'original_skipgram_2': skipgram_counts.get('skipgram_2word', 0),
        'original_skipgram_3': skipgram_counts.get('skipgram_3word', 0),
        'original_skipgram_4plus': skipgram_counts.get('skipgram_4plus', 0),
        'deduplicated_skipgram_count': len(deduplicated_skipgrams),
        'deduplicated_skipgram_2': skipgram_2_actual,
        'deduplicated_skipgram_3': skipgram_3_actual,
        'deduplicated_skipgram_4plus': skipgram_4_actual,
        'estimated_skipgram_2': skipgram_2_est,
        'estimated_skipgram_3': skipgram_3_est,
        'estimated_skipgram_4plus': skipgram_4_est,

        'original_root_count': len(shared_roots),
        'deduplicated_root_count': len(deduplicated_roots),
        'roots_in_contiguous': len(roots_in_contiguous),
        'roots_in_skipgrams': len(additional_roots_in_skipgrams),
        'roots_filtered_by_idf': roots_filtered_by_idf,
        'total_roots_removed': len(shared_roots) - len(deduplicated_roots),

        # Pattern counts (deduplicated)
        'contiguous_2word': contiguous_2,
        'contiguous_3word': contiguous_3,
        'contiguous_4plus': contiguous_4plus,
        'skipgram_2word_dedup': skipgram_2_actual,
        'skipgram_3word_dedup': skipgram_3_actual,
        'skipgram_4plus_dedup': skipgram_4_actual,
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
        'deduplicated_skipgrams': deduplicated_skipgrams,
        'deduplicated_roots': deduplicated_roots
    }


def main():
    """Calculate skipgram-aware deduplicated scores V2 for all psalm relationships."""

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

    # Path to relationships database (for skipgrams)
    db_path = base_dir / "data/psalm_relationships.db"
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        logger.error("Please ensure psalm_relationships.db exists with skipgram data.")
        return

    # Calculate skipgram-aware deduplicated scores V2
    logger.info("Calculating skipgram-aware deduplicated scores V2...")
    logger.info(f"  Using IDF threshold {IDF_THRESHOLD_FOR_SINGLE_ROOTS} for single root matches")
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

        # Load shared skipgrams from database
        try:
            shared_skipgrams = load_shared_skipgrams(db_path, psalm_a, psalm_b)
        except Exception as e:
            logger.warning(f"  Error loading skipgrams for Psalms {psalm_a}-{psalm_b}: {e}")
            shared_skipgrams = []

        score_data = calculate_skipgram_aware_deduplicated_score(
            psalm_a=psalm_a,
            psalm_b=psalm_b,
            shared_phrases=rel['shared_phrases'],
            shared_roots=rel['shared_roots'],
            shared_skipgrams=shared_skipgrams,
            skipgram_counts=skipgram_lookup[key],
            word_count_a=word_counts[str(psalm_a)],
            word_count_b=word_counts[str(psalm_b)],
            original_pvalue=rel['pvalue'],
            original_rank=i
        )

        deduplicated_scores.append(score_data)

    # Save results
    output_path = base_dir / "data/analysis_results/enhanced_scores_skipgram_dedup_v2.json"
    logger.info(f"Saving skipgram-aware deduplicated scores V2 to {output_path}...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(deduplicated_scores, f, indent=2, ensure_ascii=False)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"  File size: {file_size_mb:.2f} MB")

    # Summary statistics
    logger.info("\nDeduplication Statistics:")

    total_phrases_removed = sum(s['phrases_removed_as_substrings'] for s in deduplicated_scores)
    total_skipgrams_removed = sum(
        s['original_skipgram_count'] - s['deduplicated_skipgram_count']
        for s in deduplicated_scores
    )
    total_roots_removed = sum(s['total_roots_removed'] for s in deduplicated_scores)
    total_roots_filtered_idf = sum(s['roots_filtered_by_idf'] for s in deduplicated_scores)

    logger.info(f"  Contiguous phrases removed as substrings: {total_phrases_removed:,}")
    logger.info(f"  Skipgrams removed (overlap + subpatterns): {total_skipgrams_removed:,}")
    logger.info(f"  Roots removed (appear in phrases): {total_roots_removed - total_roots_filtered_idf:,}")
    logger.info(f"  Roots filtered (IDF < {IDF_THRESHOLD_FOR_SINGLE_ROOTS}): {total_roots_filtered_idf:,}")
    logger.info(f"  Total roots removed: {total_roots_removed:,}")

    # Score comparison
    scores = [s['final_score'] for s in deduplicated_scores]
    scores.sort(reverse=True)

    logger.info(f"\nScore Distribution:")
    logger.info(f"  Maximum: {scores[0]:.2f}")
    if len(scores) >= 100:
        logger.info(f"  Top 100 cutoff: {scores[99]:.2f}")
    if len(scores) >= 300:
        logger.info(f"  Top 300 cutoff: {scores[299]:.2f}")
    if len(scores) >= 500:
        logger.info(f"  Top 500 cutoff: {scores[499]:.2f}")
    logger.info(f"  Minimum: {scores[-1]:.2f}")

    logger.info("\n✓ Complete!")


if __name__ == "__main__":
    main()
