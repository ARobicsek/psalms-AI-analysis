"""
Enhanced Scorer with Skipgram-Aware Hierarchical Deduplication - Version 3 (Simplified)

Updates from V2:
1. Adds verse-level details using existing verse data from significant_relationships.json
2. Reformats output to include verse lists for all match types
3. Maintains all V2 deduplication logic (IDF filter, hierarchical deduplication)

This simplified V3 uses the verse information already present in the source data
rather than attempting complex morphological re-matching.
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


def enhance_contiguous_phrases_with_verse_info(phrases: List[Dict]) -> List[Dict]:
    """
    Enhance contiguous phrases with verse-level formatting.
    
    Uses existing verses_a and verses_b from source data.
    """
    enhanced = []
    
    for phrase in phrases:
        # Phrases already have verses_a and verses_b in source data
        verses_a = phrase.get('verses_a', [])
        verses_b = phrase.get('verses_b', [])
        
        # Create enhanced format with verse details
        enhanced_phrase = phrase.copy()
        
        # Add matches_from_a and matches_from_b with verse info
        enhanced_phrase['matches_from_a'] = [
            {
                'verse': v,
                'text': phrase['hebrew'],  # Use the canonical Hebrew form
                'position': None  # Position would require complex morphological matching
            }
            for v in verses_a
        ]
        
        enhanced_phrase['matches_from_b'] = [
            {
                'verse': v,
                'text': phrase['hebrew'],
                'position': None
            }
            for v in verses_b
        ]
        
        enhanced.append(enhanced_phrase)
    
    return enhanced


def enhance_skipgrams_with_verse_info(skipgrams: List[Dict]) -> List[Dict]:
    """
    Enhance skipgrams with verse-level information.

    Note: Skipgrams in current data don't have verse info, so we provide
    the structure but with empty verse lists.
    """
    enhanced = []

    for skipgram in skipgrams:
        consonantal = skipgram['consonantal']
        words = consonantal.split()
        pattern_length = len(words)

        # Get full_span_hebrew from skipgram data
        full_span_hebrew = skipgram.get('full_span_hebrew', '')
        full_span_words = full_span_hebrew.split() if full_span_hebrew else []
        span_word_count = len(full_span_words)

        # Calculate gap_word_count as difference between span and pattern
        gap_word_count = span_word_count - pattern_length if span_word_count > pattern_length else 0

        # Create enhanced skipgram with structure
        enhanced_skipgram = {
            'consonantal': consonantal,
            'matched_hebrew': skipgram.get('pattern_hebrew', consonantal),
            'full_span_hebrew': full_span_hebrew,
            'length': pattern_length,
            'gap_word_count': gap_word_count,
            'span_word_count': span_word_count,
            'verses_a': [],  # Skipgrams don't have verse info in current data
            'verses_b': [],
            'matches_from_a': [],
            'matches_from_b': []
        }

        enhanced.append(enhanced_skipgram)

    return enhanced


def enhance_roots_with_verse_info(roots: List[Dict]) -> List[Dict]:
    """
    Enhance roots with verse-level information.

    Uses verse numbers from the source data (via pairwise_comparator)
    to populate verse fields for each example.
    """
    enhanced = []

    for root in roots:
        # Create enhanced root with verse structure
        enhanced_root = root.copy()

        # Get verse information from source data
        verses_a = root.get('verses_a', [])
        verses_b = root.get('verses_b', [])
        examples_a = root.get('examples_a', [])
        examples_b = root.get('examples_b', [])

        # Pair examples with verse numbers (one verse number per example)
        enhanced_root['matches_from_a'] = [
            {
                'verse': verses_a[i] if i < len(verses_a) else None,
                'text': ex,
                'position': None
            }
            for i, ex in enumerate(examples_a)
        ]
        enhanced_root['matches_from_b'] = [
            {
                'verse': verses_b[i] if i < len(verses_b) else None,
                'text': ex,
                'position': None
            }
            for i, ex in enumerate(examples_b)
        ]

        enhanced.append(enhanced_root)

    return enhanced


def load_shared_skipgrams(db_path: Path, psalm_a: int, psalm_b: int) -> List[Dict]:
    """Load shared skipgrams with full_span_hebrew from database."""
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

        # Get skipgrams for both psalms with all required columns
        cursor.execute("""
            SELECT pattern_roots, pattern_hebrew, full_span_hebrew, pattern_length
            FROM psalm_skipgrams
            WHERE psalm_number = ?
        """, (psalm_a,))
        skipgrams_a = {row['pattern_roots']: row for row in cursor.fetchall()}

        cursor.execute("""
            SELECT pattern_roots, pattern_hebrew, full_span_hebrew, pattern_length
            FROM psalm_skipgrams
            WHERE psalm_number = ?
        """, (psalm_b,))
        skipgrams_b = {row['pattern_roots']: row for row in cursor.fetchall()}

        conn.close()

        # Find shared skipgrams
        shared = []
        for consonantal, row_a in skipgrams_a.items():
            if consonantal in skipgrams_b:
                row_b = skipgrams_b[consonantal]
                # Use data from psalm_a (they should be identical for shared skipgrams)
                shared.append({
                    'consonantal': consonantal,
                    'pattern_hebrew': row_a['pattern_hebrew'],
                    'full_span_hebrew': row_a['full_span_hebrew'],
                    'length': row_a['pattern_length']
                })

        return shared
    except Exception as e:
        logger.warning(f"Could not load skipgrams: {e}")
        return []


def deduplicate_skipgrams(
    skipgrams: List[Dict],
    contiguous_phrases: List[Dict]
) -> List[Dict]:
    """Deduplicate skipgrams (same logic as V2)."""
    contiguous_patterns = {p['consonantal'] for p in contiguous_phrases}
    non_contiguous = [s for s in skipgrams if s['consonantal'] not in contiguous_patterns]
    
    sorted_skipgrams = sorted(non_contiguous, key=lambda s: s['length'], reverse=True)
    
    deduplicated = []
    covered_patterns = set()
    
    for skipgram in sorted_skipgrams:
        pattern_words = skipgram['consonantal'].split()
        pattern_tuple = tuple(pattern_words)
        
        is_subpattern = False
        for covered in covered_patterns:
            covered_words = list(covered)
            if len(pattern_words) < len(covered_words):
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


def estimate_skipgram_deduplication(
    skipgram_2: int,
    skipgram_3: int,
    skipgram_4plus: int,
    contiguous_2: int,
    contiguous_3: int,
    contiguous_4plus: int
) -> Tuple[int, int, int]:
    """Estimate deduplicated skipgram counts."""
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
    """Estimate which roots appear in skipgrams."""
    if not deduplicated_skipgrams:
        return set()
    
    roots_in_skipgrams = set()
    for skipgram in deduplicated_skipgrams:
        words = skipgram['consonantal'].split()
        roots_in_skipgrams.update(words)
    
    return roots_in_skipgrams - roots_in_contiguous


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
    """Calculate enhanced score with V3 verse-level formatting."""
    
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
    
    skipgram_2_est, skipgram_3_est, skipgram_4_est = estimate_skipgram_deduplication(
        skipgram_2=skipgram_counts.get('skipgram_2word', 0),
        skipgram_3=skipgram_counts.get('skipgram_3word', 0),
        skipgram_4plus=skipgram_counts.get('skipgram_4plus', 0),
        contiguous_2=contiguous_2,
        contiguous_3=contiguous_3,
        contiguous_4plus=contiguous_4plus
    )
    
    # Find additional roots in skipgrams
    additional_roots_in_skipgrams = estimate_roots_in_skipgrams(
        shared_roots=shared_roots,
        roots_in_contiguous=roots_in_contiguous,
        deduplicated_skipgrams=deduplicated_skipgrams
    )
    
    # Deduplicate roots
    all_roots_in_phrases = roots_in_contiguous | additional_roots_in_skipgrams
    
    deduplicated_roots = [
        r for r in shared_roots
        if r['root'] not in all_roots_in_phrases and r['idf'] >= IDF_THRESHOLD_FOR_SINGLE_ROOTS
    ]
    
    roots_filtered_by_idf = sum(
        1 for r in shared_roots
        if r['root'] not in all_roots_in_phrases and r['idf'] < IDF_THRESHOLD_FOR_SINGLE_ROOTS
    )
    
    # Enhance with V3 verse-level formatting
    enhanced_contiguous = enhance_contiguous_phrases_with_verse_info(deduplicated_contiguous)
    enhanced_skipgrams = enhance_skipgrams_with_verse_info(deduplicated_skipgrams)
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
        
        # V3: Enhanced matches with verse-level details
        'deduplicated_contiguous_phrases': enhanced_contiguous,
        'deduplicated_skipgrams': enhanced_skipgrams,
        'deduplicated_roots': enhanced_roots
    }


def main():
    """Calculate skipgram-aware deduplicated scores V3."""
    
    base_dir = Path(__file__).parent.parent.parent
    
    # Load inputs
    logger.info("Loading data files...")
    
    with open(base_dir / "data/analysis_results/significant_relationships.json", 'r', encoding='utf-8') as f:
        relationships = json.load(f)
    logger.info(f"  Loaded {len(relationships)} relationships")
    
    with open(base_dir / "data/analysis_results/enhanced_scores_full.json", 'r', encoding='utf-8') as f:
        enhanced_scores = json.load(f)
    logger.info(f"  Loaded {len(enhanced_scores)} enhanced scores")
    
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
    
    db_path = base_dir / "data/psalm_relationships.db"
    
    # Calculate scores
    logger.info("Calculating V3 scores with verse-level formatting...")
    logger.info(f"  Using IDF threshold {IDF_THRESHOLD_FOR_SINGLE_ROOTS}")
    deduplicated_scores = []
    
    for i, rel in enumerate(relationships, 1):
        if i % 1000 == 0:
            logger.info(f"  Processing {i}/{len(relationships)}...")
        
        psalm_a = rel['psalm_a']
        psalm_b = rel['psalm_b']
        key = (psalm_a, psalm_b)
        
        if key not in skipgram_lookup:
            continue
        
        shared_skipgrams = load_shared_skipgrams(db_path, psalm_a, psalm_b)
        
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
    output_path = base_dir / "data/analysis_results/enhanced_scores_skipgram_dedup_v3.json"
    logger.info(f"Saving V3 scores to {output_path}...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(deduplicated_scores, f, indent=2, ensure_ascii=False)
    
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"  File size: {file_size_mb:.2f} MB")
    
    logger.info("\n✓ Complete! V3 output includes verse-level formatting for all matches.")


if __name__ == "__main__":
    main()
