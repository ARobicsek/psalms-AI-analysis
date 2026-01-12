"""
V6 Score Generation - Fresh Patterns + V5 Skipgrams

Generates V6 scores using:
- Fresh roots and phrases from psalm_patterns_v6.json (Session 115 morphology)
- V5 skipgram database (correct, with quality filtering)

Why V6:
- V5 reused old V4 roots/phrases (wrong)
- V5 skipgrams are correct (in database)
- V6 = fresh roots/phrases + V5 skipgrams

Scoring Features:
- Cross-pattern deduplication (contiguous vs skipgrams)
- Gap penalty for skipgrams (10% per gap word, max 50%)
- Content word bonus (25% for 2 content, 50% for 3+)
- IDF filtering for roots (threshold 0.5)
- Rare root bonus (2x for IDF >= 4.0)

Output: data/analysis_results/enhanced_scores_v6.json
"""

import sys
from pathlib import Path
import sqlite3
import json
import math
from typing import Dict, List, Tuple
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
IDF_THRESHOLD_FOR_SINGLE_ROOTS = 0.5


def load_shared_skipgrams_with_verses(
    db_path: Path,
    psalm_a: int,
    psalm_b: int
) -> List[Dict]:
    """
    Load shared skipgrams from V5 database with verse tracking.

    V5 database stores skipgrams per psalm, not per pair.
    We need to find skipgrams that appear in both psalms.

    Returns skipgrams with:
    - pattern information (pattern_roots, hebrew, full_span)
    - content_word_count, gap_word_count
    - verse lists for psalm_a and psalm_b
    - match instances with verse tracking
    """
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get skipgrams from psalm_a
        cursor.execute("""
            SELECT
                pattern_roots,
                pattern_hebrew,
                full_span_hebrew,
                pattern_length,
                content_word_count,
                gap_word_count,
                verse,
                first_position
            FROM psalm_skipgrams
            WHERE psalm_number = ?
        """, (psalm_a,))

        skipgrams_a = defaultdict(list)
        for row in cursor.fetchall():
            key = row['pattern_roots']
            skipgrams_a[key].append({
                'verse': row['verse'],
                'position': row['first_position'],
                'full_span_hebrew': row['full_span_hebrew'],
                'hebrew': row['pattern_hebrew'],
                'length': row['pattern_length'],
                'content_word_count': row['content_word_count'],
                'gap_word_count': row['gap_word_count']
            })

        # Get skipgrams from psalm_b
        cursor.execute("""
            SELECT
                pattern_roots,
                pattern_hebrew,
                full_span_hebrew,
                pattern_length,
                content_word_count,
                gap_word_count,
                verse,
                first_position
            FROM psalm_skipgrams
            WHERE psalm_number = ?
        """, (psalm_b,))

        skipgrams_b = defaultdict(list)
        for row in cursor.fetchall():
            key = row['pattern_roots']
            skipgrams_b[key].append({
                'verse': row['verse'],
                'position': row['first_position'],
                'full_span_hebrew': row['full_span_hebrew'],
                'hebrew': row['pattern_hebrew'],
                'length': row['pattern_length'],
                'content_word_count': row['content_word_count'],
                'gap_word_count': row['gap_word_count']
            })

        conn.close()

        # Find shared skipgrams
        shared_patterns = set(skipgrams_a.keys()) & set(skipgrams_b.keys())

        skipgrams = []
        for pattern in shared_patterns:
            instances_a = skipgrams_a[pattern]
            instances_b = skipgrams_b[pattern]

            # Get first instance for metadata
            first_a = instances_a[0]
            first_b = instances_b[0]

            skipgrams.append({
                'consonantal': pattern,
                'hebrew': first_a['hebrew'],
                'length': first_a['length'],
                'content_word_count': first_a['content_word_count'],
                'gap_word_count': first_a['gap_word_count'],
                'verses_a': sorted(set(inst['verse'] for inst in instances_a)),
                'verses_b': sorted(set(inst['verse'] for inst in instances_b)),
                'matches_from_a': [{'verse': inst['verse'], 'position': inst['position'], 'full_span_hebrew': inst['full_span_hebrew']} for inst in instances_a],
                'matches_from_b': [{'verse': inst['verse'], 'position': inst['position'], 'full_span_hebrew': inst['full_span_hebrew']} for inst in instances_b]
            })

        return skipgrams

    except Exception as e:
        logger.warning(f"Could not load skipgrams for Psalms {psalm_a}-{psalm_b}: {e}")
        return []


def deduplicate_across_match_types(
    contiguous_phrases: List[Dict],
    skipgrams: List[Dict]
) -> Tuple[List[Dict], List[Dict]]:
    """
    Deduplicate contiguous phrases and skipgrams ACROSS match types.

    Removes any pattern (contiguous or skipgram) that is a subsequence
    of a longer pattern, regardless of match type.

    Returns:
        Tuple of (deduplicated_contiguous, deduplicated_skipgrams)
    """
    # Tag each pattern with its type and combine them
    all_patterns = []
    for phrase in contiguous_phrases:
        all_patterns.append({
            'type': 'contiguous',
            'data': phrase,
            'consonantal': phrase['phrase'],  # V6 uses 'phrase' field
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


def enhance_contiguous_phrases_with_verse_info(phrases: List[Dict], tanakh_db_path: Path, psalm_a: int, psalm_b: int) -> List[Dict]:
    """
    Format contiguous phrases for V6 output with verse tracking and Hebrew text.

    Input: V6 phrases with 'phrase', 'length', 'verses_a', 'verses_b'
    Output: Formatted for final JSON with Hebrew text from tanakh.db
    """
    # Load verse texts from tanakh.db
    try:
        conn = sqlite3.connect(str(tanakh_db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get verses for psalm_a
        cursor.execute("SELECT verse, hebrew FROM verses WHERE book_name = 'Psalms' AND chapter = ? ORDER BY verse", (psalm_a,))
        verses_a = {row['verse']: row['hebrew'] for row in cursor.fetchall()}

        # Get verses for psalm_b
        cursor.execute("SELECT verse, hebrew FROM verses WHERE book_name = 'Psalms' AND chapter = ? ORDER BY verse", (psalm_b,))
        verses_b = {row['verse']: row['hebrew'] for row in cursor.fetchall()}

        conn.close()
    except Exception as e:
        logger.warning(f"Could not load verse texts for phrases: {e}")
        verses_a = {}
        verses_b = {}

    enhanced = []
    for phrase in phrases:
        enhanced.append({
            'consonantal': phrase['phrase'],
            'length': phrase['length'],
            'matches_from_a': [{'verse': v, 'hebrew': verses_a.get(v, '')} for v in phrase['verses_a']],
            'matches_from_b': [{'verse': v, 'hebrew': verses_b.get(v, '')} for v in phrase['verses_b']]
        })
    return enhanced


def enhance_roots_with_verse_info(roots: List[Dict], tanakh_db_path: Path, psalm_a: int, psalm_b: int) -> List[Dict]:
    """
    Format roots for V6 output with verse tracking and Hebrew text.

    Input: V6 roots with 'root', 'idf', 'verses_a', 'verses_b'
    Output: Formatted for final JSON with Hebrew text from tanakh.db
    """
    # Load verse texts from tanakh.db
    try:
        conn = sqlite3.connect(str(tanakh_db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get verses for psalm_a
        cursor.execute("SELECT verse, hebrew FROM verses WHERE book_name = 'Psalms' AND chapter = ? ORDER BY verse", (psalm_a,))
        verses_a = {row['verse']: row['hebrew'] for row in cursor.fetchall()}

        # Get verses for psalm_b
        cursor.execute("SELECT verse, hebrew FROM verses WHERE book_name = 'Psalms' AND chapter = ? ORDER BY verse", (psalm_b,))
        verses_b = {row['verse']: row['hebrew'] for row in cursor.fetchall()}

        conn.close()
    except Exception as e:
        logger.warning(f"Could not load verse texts for roots: {e}")
        verses_a = {}
        verses_b = {}

    enhanced = []
    for root in roots:
        enhanced.append({
            'root': root['root'],
            'idf': root['idf'],
            'matches_from_a': [{'verse': v, 'hebrew': verses_a.get(v, '')} for v in root['verses_a']],
            'matches_from_b': [{'verse': v, 'hebrew': verses_b.get(v, '')} for v in root['verses_b']]
        })
    return enhanced


def calculate_v6_score(
    psalm_a: int,
    psalm_b: int,
    shared_phrases: List[Dict],
    shared_roots: List[Dict],
    shared_skipgrams: List[Dict],
    word_count_a: int,
    word_count_b: int,
    tanakh_db_path: Path
) -> Dict:
    """Calculate V6 score with all scoring features."""

    # Cross-pattern deduplication
    deduplicated_contiguous, deduplicated_skipgrams = deduplicate_across_match_types(
        shared_phrases,
        shared_skipgrams
    )

    # Extract roots from deduplicated patterns
    roots_in_contiguous = set()
    for phrase in deduplicated_contiguous:
        roots = phrase['phrase'].split()
        roots_in_contiguous.update(roots)

    # Count contiguous by length
    contiguous_2 = sum(1 for p in deduplicated_contiguous if p['length'] == 2)
    contiguous_3 = sum(1 for p in deduplicated_contiguous if p['length'] == 3)
    contiguous_4plus = sum(1 for p in deduplicated_contiguous if p['length'] >= 4)

    # Calculate skipgram values with gap penalty and content word bonus
    def calculate_skipgram_value(skipgram: Dict) -> float:
        """Calculate skipgram value with gap penalty and content bonus."""
        length = skipgram['length']
        gap_count = skipgram.get('gap_word_count', 0)
        content_word_count = skipgram.get('content_word_count', 1)

        # Base value by length
        if length == 2:
            base_value = 1.0
        elif length == 3:
            base_value = 2.0
        else:  # 4+
            base_value = 3.0

        # Gap penalty: 10% per word in gap, max 50%
        gap_penalty = min(0.1 * gap_count, 0.5)

        # Content word bonus
        if content_word_count >= 3:
            content_bonus = 1.5  # 50% bonus
        elif content_word_count == 2:
            content_bonus = 1.25  # 25% bonus
        else:
            content_bonus = 1.0

        return base_value * (1.0 - gap_penalty) * content_bonus

    skipgram_2_actual = sum(1 for s in deduplicated_skipgrams if s['length'] == 2)
    skipgram_3_actual = sum(1 for s in deduplicated_skipgrams if s['length'] == 3)
    skipgram_4_actual = sum(1 for s in deduplicated_skipgrams if s['length'] >= 4)

    # Calculate skipgram contribution
    skipgram_score_contribution = sum(
        calculate_skipgram_value(s) for s in deduplicated_skipgrams
    )

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

    # Enhance with verse info and Hebrew text
    enhanced_contiguous = enhance_contiguous_phrases_with_verse_info(deduplicated_contiguous, tanakh_db_path, psalm_a, psalm_b)
    enhanced_skipgrams = deduplicated_skipgrams  # Already have proper format from database
    enhanced_roots = enhance_roots_with_verse_info(deduplicated_roots, tanakh_db_path, psalm_a, psalm_b)

    # Calculate scores
    contiguous_score_contribution = (
        contiguous_2 * 1 +
        contiguous_3 * 2 +
        contiguous_4plus * 3
    )
    total_pattern_points = contiguous_score_contribution + skipgram_score_contribution

    root_idf_sum = 0.0
    for root in deduplicated_roots:
        idf = root['idf']
        if idf >= 4.0:
            root_idf_sum += idf * 2  # Rare root bonus
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

        # Matches with verse tracking
        'deduplicated_contiguous_phrases': enhanced_contiguous,
        'deduplicated_skipgrams': enhanced_skipgrams,
        'deduplicated_roots': enhanced_roots
    }


def main():
    """Generate V6 scores."""
    base_dir = Path(__file__).parent.parent.parent

    # Paths
    patterns_file = base_dir / "data" / "analysis_results" / "psalm_patterns_v6.json"
    skipgram_db = base_dir / "data" / "psalm_relationships.db"
    tanakh_db = base_dir / "database" / "tanakh.db"
    word_counts_file = base_dir / "data" / "analysis_results" / "psalm_word_counts.json"
    output_file = base_dir / "data" / "analysis_results" / "enhanced_scores_v6.json"

    # Load inputs
    logger.info("Loading V6 patterns...")
    with open(patterns_file, 'r', encoding='utf-8') as f:
        v6_patterns = json.load(f)
    logger.info(f"  Loaded {len(v6_patterns['psalm_pairs'])} psalm pairs")

    logger.info("Loading word counts...")
    with open(word_counts_file, 'r', encoding='utf-8') as f:
        word_counts_data = json.load(f)
        word_counts = word_counts_data['word_counts']
    logger.info(f"  Loaded word counts for {len(word_counts)} psalms")

    # Create lookup for psalm pairs
    logger.info("Indexing psalm pairs...")
    pair_lookup = {}
    for pair in v6_patterns['psalm_pairs']:
        key = (pair['psalm_a'], pair['psalm_b'])
        pair_lookup[key] = pair

    # Calculate scores
    logger.info("\nCalculating V6 scores...")
    logger.info(f"  Using IDF threshold {IDF_THRESHOLD_FOR_SINGLE_ROOTS}")
    logger.info("  V6 Features: Fresh patterns + V5 skipgrams + gap penalty + content bonus")

    v6_scores = []
    processed = 0
    total = len(pair_lookup)

    for (psalm_a, psalm_b), pair_data in pair_lookup.items():
        processed += 1
        if processed % 1000 == 0:
            logger.info(f"  Processing {processed}/{total}...")

        # Load skipgrams from V5 database
        shared_skipgrams = load_shared_skipgrams_with_verses(skipgram_db, psalm_a, psalm_b)

        # Get fresh roots and phrases from V6 patterns
        shared_roots = pair_data['shared_roots']
        shared_phrases = pair_data['shared_phrases']

        # Calculate score
        score_data = calculate_v6_score(
            psalm_a=psalm_a,
            psalm_b=psalm_b,
            shared_phrases=shared_phrases,
            shared_roots=shared_roots,
            shared_skipgrams=shared_skipgrams,
            word_count_a=word_counts.get(str(psalm_a), 0),
            word_count_b=word_counts.get(str(psalm_b), 0),
            tanakh_db_path=tanakh_db
        )

        v6_scores.append(score_data)

    # Sort by final score (descending)
    v6_scores.sort(key=lambda x: x['final_score'], reverse=True)

    # Save to JSON
    logger.info(f"\nSaving V6 scores to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(v6_scores, f, ensure_ascii=False, indent=2)

    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    logger.info(f"✓ Saved {output_file.name} ({file_size_mb:.2f} MB)")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("V6 SCORE GENERATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total scored psalm pairs: {len(v6_scores)}")
    logger.info(f"Top score: {v6_scores[0]['final_score']:.2f} (Psalms {v6_scores[0]['psalm_a']}-{v6_scores[0]['psalm_b']})")
    logger.info(f"Output file: {output_file}")
    logger.info("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
