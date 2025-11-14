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

V4.2 Enhancement:
- Cross-pattern deduplication across ALL shared patterns
- Full verse text from tanakh.db (not just matched words)

V4.3 Enhancement:
- Cross-match-type deduplication (contiguous vs skipgrams)
- Removes any pattern that is a subsequence of a longer pattern
- Regardless of whether it's contiguous or skipgram
- Example: If skipgram "זמור דוד יהו תיסר" exists, removes contiguous "זמור דוד"

This addresses all issues identified by user in V3, V4, V4.1, and V4.2 output.
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


def load_psalm_verses(db_path: Path, psalm_number: int) -> Dict[int, str]:
    """
    Load all verse texts for a given psalm from tanakh.db.

    Args:
        db_path: Path to database directory (will look for tanakh.db)
        psalm_number: Psalm number

    Returns:
        Dict mapping verse number to full Hebrew text
    """
    # tanakh.db is in database/ directory, psalm_relationships.db is in data/
    tanakh_db = db_path.parent.parent / "database" / "tanakh.db"

    try:
        conn = sqlite3.connect(str(tanakh_db))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT verse, hebrew
            FROM verses
            WHERE book_name = 'Psalms' AND chapter = ?
            ORDER BY verse
        """, (psalm_number,))

        verses = {}
        for row in cursor.fetchall():
            verses[row['verse']] = row['hebrew'] or ''

        conn.close()
        return verses

    except Exception as e:
        logger.warning(f"Could not load verses for Psalm {psalm_number}: {e}")
        return {}


def load_shared_skipgrams_with_verses(
    db_path: Path,
    psalm_a: int,
    psalm_b: int
) -> List[Dict]:
    """
    Load shared skipgrams with full verse tracking from V4 database.

    V4.2 FIX:
    1. Deduplicates across ALL shared patterns (not just within each pattern)
    2. Uses full verse text from tanakh.db (not just matched words)

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

        # Load verse texts for both psalms
        verses_text_a = load_psalm_verses(db_path, psalm_a)
        verses_text_b = load_psalm_verses(db_path, psalm_b)

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
                'pattern_roots': pattern_roots,
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
                'pattern_roots': pattern_roots,
                'pattern_hebrew': row['pattern_hebrew'],
                'full_span_hebrew': row['full_span_hebrew'],
                'length': row['pattern_length'],
                'verse': row['verse'],
                'position': row['first_position']
            })

        conn.close()

        # Find shared patterns
        common_patterns = set(skipgrams_a.keys()) & set(skipgrams_b.keys())

        # V4.2 FIX #1: Collect ALL instances of shared patterns together
        # (not grouped by pattern) so we can deduplicate ACROSS patterns
        all_instances_a = []
        all_instances_b = []

        for pattern_roots in common_patterns:
            all_instances_a.extend(skipgrams_a[pattern_roots])
            all_instances_b.extend(skipgrams_b[pattern_roots])

        # V4.2 FIX #1: Deduplicate overlapping instances ACROSS ALL patterns
        deduped_instances_a = deduplicate_overlapping_matches(all_instances_a)
        deduped_instances_b = deduplicate_overlapping_matches(all_instances_b)

        # Group deduplicated instances back by pattern for output
        deduped_by_pattern_a = defaultdict(list)
        deduped_by_pattern_b = defaultdict(list)

        for inst in deduped_instances_a:
            deduped_by_pattern_a[inst['pattern_roots']].append(inst)

        for inst in deduped_instances_b:
            deduped_by_pattern_b[inst['pattern_roots']].append(inst)

        # Build output list - only include patterns that still have instances after dedup
        shared = []
        for pattern_roots in common_patterns:
            instances_a = deduped_by_pattern_a.get(pattern_roots, [])
            instances_b = deduped_by_pattern_b.get(pattern_roots, [])

            # Skip if either side has no instances after deduplication
            if not instances_a or not instances_b:
                continue

            # Use first instance for pattern info (they're all the same pattern)
            first_a = instances_a[0]

            # V4.2 FIX #2: Create match instances with FULL VERSE TEXT
            matches_from_a = [
                {
                    'verse': inst['verse'],
                    'text': verses_text_a.get(inst['verse'], inst['pattern_hebrew'])
                }
                for inst in instances_a
            ]

            matches_from_b = [
                {
                    'verse': inst['verse'],
                    'text': verses_text_b.get(inst['verse'], inst['pattern_hebrew'])
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


def deduplicate_across_match_types(
    contiguous_phrases: List[Dict],
    skipgrams: List[Dict]
) -> Tuple[List[Dict], List[Dict]]:
    """
    Deduplicate contiguous phrases and skipgrams ACROSS match types.

    V4.3 Fix: Removes any pattern (contiguous or skipgram) that is a subsequence
    of a longer pattern, regardless of match type.

    Example: If skipgram "זמור דוד יהו תיסר" (4 words) exists,
    remove contiguous phrase "זמור דוד" (2 words) because it's contained.

    Returns:
        Tuple of (deduplicated_contiguous, deduplicated_skipgrams)
    """
    # Tag each pattern with its type and combine them
    all_patterns = []
    for phrase in contiguous_phrases:
        all_patterns.append({
            'type': 'contiguous',
            'data': phrase,
            'consonantal': phrase['consonantal'],
            'length': phrase['length']
        })
    for skipgram in skipgrams:
        all_patterns.append({
            'type': 'skipgram',
            'data': skipgram,
            'consonantal': skipgram['consonantal'],
            'length': skipgram['length']
        })

    # Sort by length (longer patterns first) for hierarchical deduplication
    sorted_patterns = sorted(all_patterns, key=lambda p: p['length'], reverse=True)

    deduplicated = []
    covered_patterns = set()

    for pattern in sorted_patterns:
        pattern_words = pattern['consonantal'].split()
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
            deduplicated.append(pattern)
            covered_patterns.add(pattern_tuple)

    # Separate back into contiguous and skipgrams
    deduplicated_contiguous = [p['data'] for p in deduplicated if p['type'] == 'contiguous']
    deduplicated_skipgrams = [p['data'] for p in deduplicated if p['type'] == 'skipgram']

    return deduplicated_contiguous, deduplicated_skipgrams


def deduplicate_skipgrams(
    skipgrams: List[Dict],
    contiguous_phrases: List[Dict]
) -> List[Dict]:
    """
    DEPRECATED in V4.3: Use deduplicate_across_match_types() instead.

    This function is kept for reference but should not be used.
    V4.3 fix requires deduplicating across match types, not just within skipgrams.
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

    # V4.3: Deduplicate ACROSS match types (contiguous and skipgrams)
    # This removes any pattern that is a subsequence of a longer pattern,
    # regardless of whether it's contiguous or skipgram
    deduplicated_contiguous, deduplicated_skipgrams = deduplicate_across_match_types(
        shared_phrases,
        shared_skipgrams
    )

    # Extract roots from deduplicated patterns
    roots_in_contiguous = set()
    for phrase in deduplicated_contiguous:
        roots = phrase['consonantal'].split()
        roots_in_contiguous.update(roots)

    # Count contiguous by length
    contiguous_2 = sum(1 for p in deduplicated_contiguous if p['length'] == 2)
    contiguous_3 = sum(1 for p in deduplicated_contiguous if p['length'] == 3)
    contiguous_4plus = sum(1 for p in deduplicated_contiguous if p['length'] >= 4)

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
