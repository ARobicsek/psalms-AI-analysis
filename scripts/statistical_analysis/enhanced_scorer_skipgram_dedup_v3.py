"""
Enhanced Scorer with Skipgram-Aware Hierarchical Deduplication - Version 3

Updates from V2:
1. Adds verse-level details for contiguous phrases (position, Hebrew text for each match)
2. Adds verse-level details for skipgrams (verse numbers, position ranges, full span Hebrew)
3. Adds verse-level details for roots (verse numbers, positions)
4. Maintains all V2 deduplication logic (IDF filter, hierarchical deduplication)

Output JSON now includes WHERE in each psalm the matches occur.
"""

import json
import math
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import Counter, defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Constants
IDF_THRESHOLD_FOR_SINGLE_ROOTS = 0.5  # Very common words excluded from single root matches
TANAKH_DB_PATH = Path(__file__).parent.parent.parent / "database" / "tanakh.db"


class VerseDetailExtractor:
    """Extracts verse-level details for phrase matches."""
    
    def __init__(self, tanakh_db_path: Path):
        """Initialize with database connection."""
        self.conn = sqlite3.connect(str(tanakh_db_path))
        self.conn.row_factory = sqlite3.Row
        # Cache for psalm concordances
        self.psalm_cache = {}
    
    def get_psalm_concordance(self, psalm_number: int) -> List[Dict]:
        """
        Get full concordance for a psalm (all words with positions).
        
        Returns:
            List of {consonantal, hebrew, verse, position} dictionaries
        """
        if psalm_number in self.psalm_cache:
            return self.psalm_cache[psalm_number]
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                word_consonantal_split as consonantal,
                word as hebrew,
                verse,
                position
            FROM concordance
            WHERE book_name = 'Psalms' AND chapter = ?
            ORDER BY verse, position
        """, (psalm_number,))
        
        words = []
        for row in cursor.fetchall():
            words.append({
                'consonantal': row['consonantal'],
                'hebrew': row['hebrew'],
                'verse': row['verse'],
                'position': row['position']
            })
        
        self.psalm_cache[psalm_number] = words
        return words
    
    def find_contiguous_phrase_matches(
        self, 
        psalm_number: int, 
        phrase_consonantal: str
    ) -> List[Dict]:
        """
        Find all occurrences of a contiguous phrase in a psalm.
        
        Returns:
            List of {verse, text, position} for each match
        """
        words = self.get_psalm_concordance(psalm_number)
        phrase_words = phrase_consonantal.split()
        matches = []
        
        for i in range(len(words) - len(phrase_words) + 1):
            # Check if phrase matches at this position
            if all(
                words[i + j]['consonantal'] == phrase_words[j]
                for j in range(len(phrase_words))
            ):
                # Found a match - get verse and Hebrew text
                verse = words[i]['verse']
                hebrew_text = ' '.join(words[i + j]['hebrew'] for j in range(len(phrase_words)))
                position = words[i]['position']
                
                matches.append({
                    'verse': verse,
                    'text': hebrew_text,
                    'position': position
                })
        
        return matches
    
    def find_skipgram_matches(
        self,
        psalm_number: int,
        skipgram_consonantal: str
    ) -> List[Dict]:
        """
        Find all occurrences of a skipgram pattern in a psalm.
        
        Returns:
            List of {verse, full_text, start_pos, end_pos} for each match
        """
        words = self.get_psalm_concordance(psalm_number)
        skipgram_words = skipgram_consonantal.split()
        matches = []
        
        # Use sliding window approach (max gap from skipgram_extractor)
        max_gaps = {2: 5, 3: 7, 4: 10}
        max_gap = max_gaps.get(len(skipgram_words), 10)
        
        for i in range(len(words)):
            # Try to match skipgram starting at position i
            matched_positions = [i]
            skipgram_idx = 1
            
            if words[i]['consonantal'] != skipgram_words[0]:
                continue
            
            # Look for remaining words in skipgram within max_gap window
            for j in range(i + 1, min(i + max_gap, len(words))):
                if skipgram_idx >= len(skipgram_words):
                    break
                if words[j]['consonantal'] == skipgram_words[skipgram_idx]:
                    matched_positions.append(j)
                    skipgram_idx += 1
            
            # Check if we matched all skipgram words
            if len(matched_positions) == len(skipgram_words):
                verse = words[i]['verse']
                start_pos = words[matched_positions[0]]['position']
                end_pos = words[matched_positions[-1]]['position']
                
                # Get full span Hebrew text
                full_text = ' '.join(
                    words[k]['hebrew'] 
                    for k in range(matched_positions[0], matched_positions[-1] + 1)
                )
                
                matches.append({
                    'verse': verse,
                    'full_text': full_text,
                    'start_pos': start_pos,
                    'end_pos': end_pos
                })
        
        return matches
    
    def find_root_matches(
        self,
        psalm_number: int,
        root_consonantal: str
    ) -> List[Dict]:
        """
        Find all occurrences of a root in a psalm.
        
        Returns:
            List of {verse, text, position} for each occurrence
        """
        words = self.get_psalm_concordance(psalm_number)
        matches = []
        
        for word in words:
            if word['consonantal'] == root_consonantal:
                matches.append({
                    'verse': word['verse'],
                    'text': word['hebrew'],
                    'position': word['position']
                })
        
        return matches
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


def enhance_contiguous_phrases_with_details(
    phrases: List[Dict],
    psalm_a: int,
    psalm_b: int,
    detail_extractor: VerseDetailExtractor
) -> List[Dict]:
    """
    Add verse-level details to contiguous phrases.
    
    Adds matches_from_a and matches_from_b with position and text info.
    """
    enhanced = []
    
    for phrase in phrases:
        consonantal = phrase['consonantal']
        
        # Find all matches in both psalms
        matches_a = detail_extractor.find_contiguous_phrase_matches(psalm_a, consonantal)
        matches_b = detail_extractor.find_contiguous_phrase_matches(psalm_b, consonantal)
        
        # Add to phrase data
        enhanced_phrase = phrase.copy()
        enhanced_phrase['matches_from_a'] = matches_a
        enhanced_phrase['matches_from_b'] = matches_b
        
        enhanced.append(enhanced_phrase)
    
    return enhanced


def enhance_skipgrams_with_details(
    skipgrams: List[Dict],
    psalm_a: int,
    psalm_b: int,
    detail_extractor: VerseDetailExtractor
) -> List[Dict]:
    """
    Add verse-level details to skipgrams.
    
    Adds verse numbers, position ranges, and full span Hebrew text.
    """
    enhanced = []
    
    for skipgram in skipgrams:
        consonantal = skipgram['consonantal']
        
        # Find all matches in both psalms
        matches_a = detail_extractor.find_skipgram_matches(psalm_a, consonantal)
        matches_b = detail_extractor.find_skipgram_matches(psalm_b, consonantal)
        
        # Calculate gap and span statistics
        words = consonantal.split()
        length = len(words)
        
        # Estimate gaps (actual gaps would need per-match calculation)
        avg_gap = 0
        avg_span = length
        if matches_a:
            # Use first match as representative
            first_match = matches_a[0]
            span_words = len(first_match['full_text'].split())
            avg_gap = span_words - length
            avg_span = span_words
        
        # Create enhanced skipgram
        enhanced_skipgram = {
            'consonantal': consonantal,
            'matched_hebrew': skipgram.get('hebrew', consonantal),
            'full_span_hebrew': matches_a[0]['full_text'] if matches_a else '',
            'length': length,
            'gap_word_count': avg_gap,
            'span_word_count': avg_span,
            'verses_a': sorted(set(m['verse'] for m in matches_a)),
            'verses_b': sorted(set(m['verse'] for m in matches_b)),
            'matches_from_a': matches_a,
            'matches_from_b': matches_b
        }
        
        enhanced.append(enhanced_skipgram)
    
    return enhanced


def enhance_roots_with_details(
    roots: List[Dict],
    psalm_a: int,
    psalm_b: int,
    detail_extractor: VerseDetailExtractor
) -> List[Dict]:
    """
    Add verse-level details to roots.
    
    Adds verse numbers and positions for each occurrence.
    """
    enhanced = []
    
    for root in roots:
        consonantal = root['root']
        
        # Find all matches in both psalms
        matches_a = detail_extractor.find_root_matches(psalm_a, consonantal)
        matches_b = detail_extractor.find_root_matches(psalm_b, consonantal)
        
        # Create enhanced root
        enhanced_root = root.copy()
        enhanced_root['verses_a'] = sorted(set(m['verse'] for m in matches_a))
        enhanced_root['verses_b'] = sorted(set(m['verse'] for m in matches_b))
        enhanced_root['matches_from_a'] = matches_a
        enhanced_root['matches_from_b'] = matches_b
        
        enhanced.append(enhanced_root)
    
    return enhanced


def load_shared_skipgrams(db_path: Path, psalm_a: int, psalm_b: int) -> List[Dict]:
    """
    Load shared skipgrams between two psalms from database.
    
    NOTE: If database tables don't exist yet, this returns empty list.
    The skipgram data is currently stored in enhanced_scores_full.json.
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
        
        # Get skipgrams for psalm A
        cursor.execute("""
            SELECT pattern_roots, pattern_length
            FROM psalm_skipgrams
            WHERE psalm_number = ?
        """, (psalm_a,))
        skipgrams_a = {(row['pattern_roots'], row['pattern_length'])
                       for row in cursor.fetchall()}

        # Get skipgrams for psalm B
        cursor.execute("""
            SELECT pattern_roots, pattern_length
            FROM psalm_skipgrams
            WHERE psalm_number = ?
        """, (psalm_b,))
        skipgrams_b = {(row['pattern_roots'], row['pattern_length'])
                       for row in cursor.fetchall()}
        
        conn.close()
        
        # Find shared skipgrams
        shared = []
        for (consonantal, length) in skipgrams_a:
            if (consonantal, length) in skipgrams_b:
                shared.append({
                    'consonantal': consonantal,
                    'length': length,
                    'hebrew': consonantal
                })
        
        return shared
    except Exception as e:
        logger.warning(f"Could not load skipgrams from database: {e}")
        return []


def deduplicate_skipgrams(
    skipgrams: List[Dict],
    contiguous_phrases: List[Dict]
) -> List[Dict]:
    """
    Deduplicate skipgrams by removing:
    1. Skipgrams that are identical to contiguous phrases (gap=0)
    2. Shorter skipgrams that are subpatterns of longer skipgrams
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
    """Estimate deduplicated skipgram counts (for statistics)."""
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
    """Estimate which additional roots appear in deduplicated skipgrams."""
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
    original_rank: int,
    detail_extractor: VerseDetailExtractor
) -> Dict:
    """
    Calculate enhanced score with skipgram-aware hierarchical deduplication.
    
    Version 3 adds verse-level details to all matches.
    """
    # Step 1: Deduplicate contiguous phrases (remove substrings)
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
    deduplicated_skipgrams = deduplicate_skipgrams(shared_skipgrams, deduplicated_contiguous)
    
    # Count deduplicated skipgrams by length
    skipgram_2_actual = sum(1 for s in deduplicated_skipgrams if s['length'] == 2)
    skipgram_3_actual = sum(1 for s in deduplicated_skipgrams if s['length'] == 3)
    skipgram_4_actual = sum(1 for s in deduplicated_skipgrams if s['length'] >= 4)
    
    # Calculate estimated counts for comparison
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
    all_roots_in_phrases = roots_in_contiguous | additional_roots_in_skipgrams
    
    deduplicated_roots = [
        r for r in shared_roots
        if r['root'] not in all_roots_in_phrases and r['idf'] >= IDF_THRESHOLD_FOR_SINGLE_ROOTS
    ]
    
    # Count how many were filtered for IDF
    roots_filtered_by_idf = sum(
        1 for r in shared_roots
        if r['root'] not in all_roots_in_phrases and r['idf'] < IDF_THRESHOLD_FOR_SINGLE_ROOTS
    )
    
    # Step 5: Add verse-level details to all matches
    enhanced_contiguous = enhance_contiguous_phrases_with_details(
        deduplicated_contiguous, psalm_a, psalm_b, detail_extractor
    )
    
    enhanced_skipgrams = enhance_skipgrams_with_details(
        deduplicated_skipgrams, psalm_a, psalm_b, detail_extractor
    )
    
    enhanced_roots = enhance_roots_with_details(
        deduplicated_roots, psalm_a, psalm_b, detail_extractor
    )
    
    # Step 6: Calculate pattern points (deduplicated)
    total_pattern_points = (
        (contiguous_2 + skipgram_2_actual) * 1 +
        (contiguous_3 + skipgram_3_actual) * 2 +
        (contiguous_4plus + skipgram_4_actual) * 3
    )
    
    # Step 7: Calculate root IDF sum with rare root bonus (2x for IDF >= 4.0)
    root_idf_sum = 0.0
    for root in deduplicated_roots:
        idf = root['idf']
        if idf >= 4.0:
            root_idf_sum += idf * 2
        else:
            root_idf_sum += idf
    
    # Step 8: Calculate geometric mean length
    geometric_mean_length = math.sqrt(word_count_a * word_count_b)
    
    # Step 9: Calculate normalized scores
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
        
        # ENHANCED: Deduplicated matches with verse-level details
        'deduplicated_contiguous_phrases': enhanced_contiguous,
        'deduplicated_skipgrams': enhanced_skipgrams,
        'deduplicated_roots': enhanced_roots
    }


def main():
    """Calculate skipgram-aware deduplicated scores V3 for all psalm relationships."""
    
    base_dir = Path(__file__).parent.parent.parent
    
    # Verify tanakh.db exists
    if not TANAKH_DB_PATH.exists():
        logger.error(f"Tanakh database not found: {TANAKH_DB_PATH}")
        logger.error("Please ensure tanakh.db exists.")
        return
    
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
    
    # Initialize verse detail extractor
    logger.info("Initializing verse detail extractor...")
    detail_extractor = VerseDetailExtractor(TANAKH_DB_PATH)
    
    # Calculate skipgram-aware deduplicated scores V3
    logger.info("Calculating skipgram-aware deduplicated scores V3 with verse details...")
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
        
        # Load shared skipgrams from database (or empty if not available)
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
            original_rank=i,
            detail_extractor=detail_extractor
        )
        
        deduplicated_scores.append(score_data)
    
    # Close extractor
    detail_extractor.close()
    
    # Save results
    output_path = base_dir / "data/analysis_results/enhanced_scores_skipgram_dedup_v3.json"
    logger.info(f"Saving skipgram-aware deduplicated scores V3 to {output_path}...")
    
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
    
    logger.info("\n✓ Complete! V3 output now includes verse-level details for all matches.")


if __name__ == "__main__":
    main()
