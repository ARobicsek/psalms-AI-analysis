"""
Enhanced Scorer with Skipgram-Aware Hierarchical Deduplication - Version 4

V4 Updates from V3:
1. Uses verse-tracked skipgrams from database
2. Properly populates matches_from_a and matches_from_b arrays for all match types
3. Removes unnecessary fields (position, empty verses_a/verses_b in skipgrams)
4. Fixes deduplication bug where overlapping patterns from same phrase counted separately
5. Cleaner, more consistent JSON output format

V4.1 Enhancement:
- Overlap-based deduplication at scoring time (not extraction time)
- Groups overlapping skipgrams (>80% overlap) within same verse
- Keeps longest pattern as representative per overlapping group
- Prevents over-counting of multiple patterns from the same phrase

This addresses all issues identified by user in V3 output.
"""

import json
import math
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import Counter, defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Constants
IDF_THRESHOLD_FOR_SINGLE_ROOTS = 0.5


def deduplicate_overlapping_matches(instances: List[Dict]) -> List[Dict]:
    """
    Deduplicate skipgram instances that overlap within the same verse.

    Groups instances by verse, then within each verse groups instances with
    substantial overlap (>80% of shorter span), keeping only the longest
    pattern from each overlapping group.

    Args:
        instances: List of skipgram instances with verse, position, full_span_hebrew

    Returns:
        Deduplicated list of instances
    """
    # Group by verse
    verse_groups = defaultdict(list)
    for inst in instances:
        verse_groups[inst['verse']].append(inst)

    deduplicated = []

    for verse, inst_list in verse_groups.items():
        # Calculate word ranges for each instance
        for inst in inst_list:
            span_word_count = len(inst['full_span_hebrew'].split())
            inst['_start_pos'] = inst['position']
            inst['_end_pos'] = inst['position'] + span_word_count - 1

        # Find substantially overlapping instances
        # Use simple pairwise comparison (not union-find) to avoid transitive merging
        kept_instances = []

        for inst in inst_list:
            # Check if this instance overlaps substantially with any kept instance
            is_redundant = False

            for kept in kept_instances:
                if _instances_overlap_substantially(inst, kept):
                    # Keep the longer one
                    if inst['length'] > kept['length'] or \
                       (inst['length'] == kept['length'] and
                        (inst['_end_pos'] - inst['_start_pos']) > (kept['_end_pos'] - kept['_start_pos'])):
                        # Replace kept with current instance
                        kept_instances.remove(kept)
                        kept_instances.append(inst)
                    is_redundant = True
                    break

            if not is_redundant:
                kept_instances.append(inst)

        # Clean up temporary fields and add to deduplicated list
        for inst in kept_instances:
            del inst['_start_pos']
            del inst['_end_pos']
            deduplicated.append(inst)

    return deduplicated


def _instances_overlap_substantially(inst1: Dict, inst2: Dict) -> bool:
    """
    Check if two skipgram instances overlap substantially (>80% of shorter span).

    Args:
        inst1, inst2: Instances with _start_pos and _end_pos

    Returns:
        True if overlap is substantial
    """
    start1, end1 = inst1['_start_pos'], inst1['_end_pos']
    start2, end2 = inst2['_start_pos'], inst2['_end_pos']

    # Calculate overlap
    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)

    if overlap_start > overlap_end:
        return False  # No overlap

    overlap_length = overlap_end - overlap_start + 1
    span1_length = end1 - start1 + 1
    span2_length = end2 - start2 + 1
    shorter_span = min(span1_length, span2_length)

    # Require >80% overlap of the shorter span
    return overlap_length > shorter_span * 0.8


def load_shared_skipgrams_with_verses(
    db_path: Path,
    psalm_a: int,
    psalm_b: int
) -> List[Dict]:
    """
    Load shared skipgrams with full verse tracking from V4 database.

    Returns skipgrams with:
    - pattern information (roots, hebrew, full_span)
    - verse lists for psalm_a and psalm_b
    - match instances for matches_from_a and matches_from_b arrays
    """
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='psalm_skipgrams'
        """)
        if not cursor.fetchone():
            conn.close()
            return []

        # Get skipgrams for psalm_a
        cursor.execute("""
            SELECT pattern_roots, pattern_hebrew, full_span_hebrew,
                   pattern_length, verse, first_position
            FROM psalm_skipgrams
            WHERE psalm_number = ?
        """, (psalm_a,))

        skipgrams_a = defaultdict(list)
        for row in cursor.fetchall():
            pattern_roots = row['pattern_roots']
            skipgrams_a[pattern_roots].append({
                'pattern_hebrew': row['pattern_hebrew'],
                'full_span_hebrew': row['full_span_hebrew'],
                'length': row['pattern_length'],
                'verse': row['verse'],
                'position': row['first_position']
            })

        # Get skipgrams for psalm_b
        cursor.execute("""
            SELECT pattern_roots, pattern_hebrew, full_span_hebrew,
                   pattern_length, verse, first_position
            FROM psalm_skipgrams
            WHERE psalm_number = ?
        """, (psalm_b,))

        skipgrams_b = defaultdict(list)
        for row in cursor.fetchall():
            pattern_roots = row['pattern_roots']
            skipgrams_b[pattern_roots].append({
                'pattern_hebrew': row['pattern_hebrew'],
                'full_span_hebrew': row['full_span_hebrew'],
                'length': row['pattern_length'],
                'verse': row['verse'],
                'position': row['first_position']
            })

        conn.close()

        # Find shared skipgrams
        shared = []
        common_patterns = set(skipgrams_a.keys()) & set(skipgrams_b.keys())

        for pattern_roots in common_patterns:
            instances_a = skipgrams_a[pattern_roots]
            instances_b = skipgrams_b[pattern_roots]

            # V4.1: Deduplicate overlapping instances within same verses
            instances_a = deduplicate_overlapping_matches(instances_a)
            instances_b = deduplicate_overlapping_matches(instances_b)

            # Use first instance for pattern info (they're all the same pattern)
            first_a = instances_a[0]

            # Collect all verses
            verses_a = sorted(set(inst['verse'] for inst in instances_a))
            verses_b = sorted(set(inst['verse'] for inst in instances_b))

            # Create match instances for arrays
            matches_from_a = [
                {
                    'verse': inst['verse'],
                    'text': inst['pattern_hebrew']
                    # Removed 'position' field per user request
                }
                for inst in instances_a
            ]

            matches_from_b = [
                {
                    'verse': inst['verse'],
                    'text': inst['pattern_hebrew']
                }
                for inst in instances_b
            ]

            # Calculate gap words
            words = first_a['pattern_hebrew'].split()
            full_span_words = first_a['full_span_hebrew'].split()
            gap_word_count = len(full_span_words) - len(words)

            shared.append({
                'consonantal': pattern_roots,  # Using 'consonantal' for consistency with V3 output
                'matched_hebrew': first_a['pattern_hebrew'],
                'full_span_hebrew': first_a['full_span_hebrew'],
                'length': first_a['length'],
                'gap_word_count': gap_word_count,
                'span_word_count': len(full_span_words),
                # Removed verses_a and verses_b per user request (empty in V3, not needed)
                'matches_from_a': matches_from_a,
                'matches_from_b': matches_from_b
            })

        return shared

    except Exception as e:
        logger.warning(f"Could not load skipgrams: {e}")
        return []


def enhance_contiguous_phrases_with_verse_info(phrases: List[Dict]) -> List[Dict]:
    """
    Enhance contiguous phrases with verse-level formatting.

    Uses existing verses_a and verses_b from source data.
    Removes 'position' field per user request.
    """
    enhanced = []

    for phrase in phrases:
        verses_a = phrase.get('verses_a', [])
        verses_b = phrase.get('verses_b', [])

        # Create enhanced format with verse details
        enhanced_phrase = {
            'consonantal': phrase['consonantal'],
            'hebrew': phrase['hebrew'],
            'length': phrase['length'],
            'count_a': phrase.get('count_a', len(verses_a)),
            'count_b': phrase.get('count_b', len(verses_b)),
            'matches_from_a': [
                {
                    'verse': v,
                    'text': phrase['hebrew']
                    # Removed 'position' field
                }
                for v in verses_a
            ],
            'matches_from_b': [
                {
                    'verse': v,
                    'text': phrase['hebrew']
                }
                for v in verses_b
            ]
        }

        enhanced.append(enhanced_phrase)

    return enhanced


def enhance_roots_with_verse_info(roots: List[Dict]) -> List[Dict]:
    """
    Enhance roots with verse-level information.

    Uses verse numbers from the source data to populate verse fields.
    Removes 'position' field per user request.
    """
    enhanced = []

    for root in roots:
        # Get verse information and examples from source data
        verses_a = root.get('verses_a', [])
        verses_b = root.get('verses_b', [])
        examples_a = root.get('examples_a', [])
        examples_b = root.get('examples_b', [])

        # Create enhanced root with verse structure
        enhanced_root = {
            'root': root['root'],
            'idf': root['idf'],
            'count_a': root.get('count_a', len(examples_a)),
            'count_b': root.get('count_b', len(examples_b)),
            'matches_from_a': [
                {
                    'verse': verses_a[i] if i < len(verses_a) else None,
                    'text': ex
                }
                for i, ex in enumerate(examples_a)
            ],
            'matches_from_b': [
                {
                    'verse': verses_b[i] if i < len(verses_b) else None,
                    'text': ex
                }
                for i, ex in enumerate(examples_b)
            ]
        }

        enhanced.append(enhanced_root)

    return enhanced


def deduplicate_skipgrams(
    skipgrams: List[Dict],
    contiguous_phrases: List[Dict]
) -> List[Dict]:
    """
    Deduplicate skipgrams (remove those already captured by contiguous phrases).

    V4: Skipgrams are already deduplicated at extraction time by (full_span, verse),
    so this only needs to remove skipgrams that match contiguous phrases.
    """
    contiguous_patterns = {p['consonantal'] for p in contiguous_phrases}
    non_contiguous = [s for s in skipgrams if s['consonantal'] not in contiguous_patterns]

    # Sort by length (longer patterns first) for hierarchical deduplication
    sorted_skipgrams = sorted(non_contiguous, key=lambda s: s['length'], reverse=True)

    deduplicated = []
    covered_patterns = set()

    for skipgram in sorted_skipgrams:
        pattern_words = skipgram['consonantal'].split()
        pattern_tuple = tuple(pattern_words)

        # Check if this pattern is a subpattern of any already-included pattern
        is_subpattern = False
        for covered in covered_patterns:
            covered_words = list(covered)
            if len(pattern_words) < len(covered_words):
                # Check if pattern_words is a subsequence of covered_words
                j = 0
                for word in pattern_words:
                    while j < len(covered_words) and covered_words[j] != word:
                        j += 1
                    if j >= len(covered_words):
                        break
                    j += 1
                else:
                    is_subpattern = True
                    break

        if not is_subpattern:
            deduplicated.append(skipgram)
            covered_patterns.add(pattern_tuple)

    return deduplicated


def calculate_skipgram_aware_deduplicated_score_v4(
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
    """Calculate enhanced score with V4 verse-level formatting and clean output."""

    # Deduplicate contiguous phrases
    if not shared_phrases:
        deduplicated_contiguous = []
        roots_in_contiguous = set()
    else:
        sorted_phrases = sorted(shared_phrases, key=lambda p: p['length'], reverse=True)
        deduplicated_contiguous = []

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

        roots_in_contiguous = set()
        for phrase in deduplicated_contiguous:
            roots = phrase['consonantal'].split()
            roots_in_contiguous.update(roots)

    # Count contiguous by length
    contiguous_2 = sum(1 for p in deduplicated_contiguous if p['length'] == 2)
    contiguous_3 = sum(1 for p in deduplicated_contiguous if p['length'] == 3)
    contiguous_4plus = sum(1 for p in deduplicated_contiguous if p['length'] >= 4)

    # Deduplicate skipgrams
    deduplicated_skipgrams = deduplicate_skipgrams(shared_skipgrams, deduplicated_contiguous)

    skipgram_2_actual = sum(1 for s in deduplicated_skipgrams if s['length'] == 2)
    skipgram_3_actual = sum(1 for s in deduplicated_skipgrams if s['length'] == 3)
    skipgram_4_actual = sum(1 for s in deduplicated_skipgrams if s['length'] >= 4)

    # Find roots in skipgrams
    roots_in_skipgrams = set()
    for skipgram in deduplicated_skipgrams:
        words = skipgram['consonantal'].split()
        roots_in_skipgrams.update(words)
    roots_in_skipgrams -= roots_in_contiguous

    # Deduplicate roots
    all_roots_in_phrases = roots_in_contiguous | roots_in_skipgrams

    deduplicated_roots = [
        r for r in shared_roots
        if r['root'] not in all_roots_in_phrases and r['idf'] >= IDF_THRESHOLD_FOR_SINGLE_ROOTS
    ]

    roots_filtered_by_idf = sum(
        1 for r in shared_roots
        if r['root'] not in all_roots_in_phrases and r['idf'] < IDF_THRESHOLD_FOR_SINGLE_ROOTS
    )

    # Enhance with V4 verse-level formatting
    enhanced_contiguous = enhance_contiguous_phrases_with_verse_info(deduplicated_contiguous)
    # Skipgrams already have proper format from load_shared_skipgrams_with_verses
    enhanced_skipgrams = deduplicated_skipgrams
    enhanced_roots = enhance_roots_with_verse_info(deduplicated_roots)

    # Calculate scores
    total_pattern_points = (
        (contiguous_2 + skipgram_2_actual) * 1 +
        (contiguous_3 + skipgram_3_actual) * 2 +
        (contiguous_4plus + skipgram_4_actual) * 3
    )

    root_idf_sum = 0.0
    for root in deduplicated_roots:
        idf = root['idf']
        if idf >= 4.0:
            root_idf_sum += idf * 2
        else:
            root_idf_sum += idf

    geometric_mean_length = math.sqrt(word_count_a * word_count_b)
    phrase_score = (total_pattern_points / geometric_mean_length) * 1000
    root_score = (root_idf_sum / geometric_mean_length) * 1000
    final_score = phrase_score + root_score

    return {
        'psalm_a': psalm_a,
        'psalm_b': psalm_b,

        # Deduplication stats
        'original_phrase_count': len(shared_phrases),
        'deduplicated_contiguous_count': len(deduplicated_contiguous),
        'phrases_removed_as_substrings': len(shared_phrases) - len(deduplicated_contiguous),

        'original_skipgram_count': len(shared_skipgrams),
        'deduplicated_skipgram_count': len(deduplicated_skipgrams),

        'original_root_count': len(shared_roots),
        'deduplicated_root_count': len(deduplicated_roots),
        'roots_in_contiguous': len(roots_in_contiguous),
        'roots_in_skipgrams': len(roots_in_skipgrams),
        'roots_filtered_by_idf': roots_filtered_by_idf,
        'total_roots_removed': len(shared_roots) - len(deduplicated_roots),

        # Pattern counts
        'contiguous_2word': contiguous_2,
        'contiguous_3word': contiguous_3,
        'contiguous_4plus': contiguous_4plus,
        'skipgram_2word_dedup': skipgram_2_actual,
        'skipgram_3word_dedup': skipgram_3_actual,
        'skipgram_4plus_dedup': skipgram_4_actual,
        'total_pattern_points': total_pattern_points,

        # Root statistics
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

        # V4: Clean matches with verse-level details (no position, no empty verses_a/b)
        'deduplicated_contiguous_phrases': enhanced_contiguous,
        'deduplicated_skipgrams': enhanced_skipgrams,
        'deduplicated_roots': enhanced_roots
    }


def main():
    """Calculate skipgram-aware deduplicated scores V4."""

    base_dir = Path(__file__).parent.parent.parent

    # Load inputs
    logger.info("Loading data files...")

    # Use V3 as input since it has all the relationship data
    with open(base_dir / "data/analysis_results/enhanced_scores_skipgram_dedup_v3.json", 'r', encoding='utf-8') as f:
        v3_scores = json.load(f)
    logger.info(f"  Loaded {len(v3_scores)} relationships from V3")

    with open(base_dir / "data/analysis_results/psalm_word_counts.json", 'r', encoding='utf-8') as f:
        word_counts_data = json.load(f)
        word_counts = word_counts_data['word_counts']
    logger.info(f"  Loaded word counts for {len(word_counts)} psalms")

    db_path = base_dir / "data/psalm_relationships.db"

    # Calculate scores
    logger.info("Calculating V4 scores with verse-tracked skipgrams...")
    logger.info(f"  Using IDF threshold {IDF_THRESHOLD_FOR_SINGLE_ROOTS}")
    deduplicated_scores = []

    for i, v3_entry in enumerate(v3_scores, 1):
        if i % 1000 == 0:
            logger.info(f"  Processing {i}/{len(v3_scores)}...")

        psalm_a = v3_entry['psalm_a']
        psalm_b = v3_entry['psalm_b']

        # Load skipgrams with verse tracking (V4 database)
        shared_skipgrams = load_shared_skipgrams_with_verses(db_path, psalm_a, psalm_b)

        # Use phrase and root data from V3, skipgram counts for stats
        skipgram_counts = {
            'skipgram_2word': v3_entry.get('original_skipgram_2', 0),
            'skipgram_3word': v3_entry.get('original_skipgram_3', 0),
            'skipgram_4plus': v3_entry.get('original_skipgram_4plus', 0)
        }

        score_data = calculate_skipgram_aware_deduplicated_score_v4(
            psalm_a=psalm_a,
            psalm_b=psalm_b,
            shared_phrases=v3_entry['deduplicated_contiguous_phrases'],
            shared_roots=v3_entry['deduplicated_roots'],
            shared_skipgrams=shared_skipgrams,
            skipgram_counts=skipgram_counts,
            word_count_a=word_counts[str(psalm_a)],
            word_count_b=word_counts[str(psalm_b)],
            original_pvalue=v3_entry['original_pvalue'],
            original_rank=v3_entry['original_rank']
        )

        deduplicated_scores.append(score_data)

    # Save results
    output_path = base_dir / "data/analysis_results/enhanced_scores_skipgram_dedup_v4.json"
    logger.info(f"Saving V4 scores to {output_path}...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(deduplicated_scores, f, indent=2, ensure_ascii=False)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"  File size: {file_size_mb:.2f} MB")

    logger.info("\n✓ Complete! V4 output includes:")
    logger.info("  - Verse-tracked skipgrams with proper deduplication")
    logger.info("  - Populated matches_from_a/b arrays for all match types")
    logger.info("  - Clean output (no position, no empty verses_a/b in skipgrams)")
    logger.info("  - Fixed overlapping pattern bug")


if __name__ == "__main__":
    main()
