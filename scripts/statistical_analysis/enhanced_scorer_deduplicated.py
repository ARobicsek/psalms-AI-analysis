"""
Enhanced Scorer with Hierarchical Deduplication

Implements scoring system where:
1. Longer phrases take priority over shorter phrases
2. Phrases take priority over individual roots
3. Each word/root is only counted once (at the highest level)

This prevents double-counting the same matches multiple times.
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Set, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def is_substring_match(shorter: str, longer: str) -> bool:
    """
    Check if shorter phrase is a substring of longer phrase (space-separated words).

    Args:
        shorter: Consonantal form of shorter phrase
        longer: Consonantal form of longer phrase

    Returns:
        True if all words in shorter appear consecutively in longer
    """
    shorter_words = shorter.split()
    longer_words = longer.split()

    if len(shorter_words) >= len(longer_words):
        return False

    # Check if shorter_words appears as consecutive sequence in longer_words
    for i in range(len(longer_words) - len(shorter_words) + 1):
        if longer_words[i:i+len(shorter_words)] == shorter_words:
            return True

    return False


def deduplicate_phrases(shared_phrases: List[Dict]) -> Tuple[List[Dict], Set[str]]:
    """
    Deduplicate phrases by removing those that are substrings of longer phrases.

    Args:
        shared_phrases: List of phrase dictionaries with 'consonantal' and 'length' fields

    Returns:
        Tuple of (deduplicated phrases, set of roots covered by phrases)
    """
    if not shared_phrases:
        return [], set()

    # Sort by length descending (prioritize longer phrases)
    sorted_phrases = sorted(shared_phrases, key=lambda p: p['length'], reverse=True)

    # Keep track of which phrases to include
    included_phrases = []
    covered_consonantals = set()  # Track which phrase patterns we've already counted

    for phrase in sorted_phrases:
        consonantal = phrase['consonantal']

        # Check if this phrase is a substring of any already-included phrase
        is_covered = False
        for included in included_phrases:
            if is_substring_match(consonantal, included['consonantal']):
                is_covered = True
                break

        if not is_covered:
            included_phrases.append(phrase)
            covered_consonantals.add(consonantal)

    # Extract all roots that appear in any phrase
    roots_in_phrases = set()
    for phrase in included_phrases:
        # Split consonantal form into individual roots (words)
        roots = phrase['consonantal'].split()
        roots_in_phrases.update(roots)

    return included_phrases, roots_in_phrases


def deduplicate_roots(shared_roots: List[Dict], roots_in_phrases: Set[str]) -> List[Dict]:
    """
    Remove roots that already appear in phrase matches.

    Args:
        shared_roots: List of root dictionaries with 'root' field
        roots_in_phrases: Set of root consonantal forms that appear in phrases

    Returns:
        List of roots that don't appear in any phrase
    """
    deduplicated = []

    for root in shared_roots:
        root_consonantal = root['root']

        # Only include if this root doesn't appear in any phrase
        if root_consonantal not in roots_in_phrases:
            deduplicated.append(root)

    return deduplicated


def calculate_deduplicated_score(
    psalm_a: int,
    psalm_b: int,
    shared_phrases: List[Dict],
    shared_roots: List[Dict],
    word_count_a: int,
    word_count_b: int,
    original_pvalue: float,
    original_rank: int
) -> Dict:
    """
    Calculate enhanced score with hierarchical deduplication.

    Args:
        psalm_a, psalm_b: Psalm numbers
        shared_phrases: List of shared phrase dictionaries
        shared_roots: List of shared root dictionaries
        word_count_a, word_count_b: Word counts for each psalm
        original_pvalue: Original hypergeometric p-value
        original_rank: Original rank by p-value

    Returns:
        Dictionary with all scoring components
    """
    # Step 1: Deduplicate phrases (remove substrings of longer phrases)
    deduplicated_phrases, roots_in_phrases = deduplicate_phrases(shared_phrases)

    # Step 2: Deduplicate roots (remove roots that appear in phrases)
    deduplicated_roots = deduplicate_roots(shared_roots, roots_in_phrases)

    # Step 3: Count pattern types in deduplicated phrases
    contiguous_2word = sum(1 for p in deduplicated_phrases if p['length'] == 2 and 'skipgram' not in p.get('type', ''))
    contiguous_3word = sum(1 for p in deduplicated_phrases if p['length'] == 3 and 'skipgram' not in p.get('type', ''))
    contiguous_4plus = sum(1 for p in deduplicated_phrases if p['length'] >= 4 and 'skipgram' not in p.get('type', ''))

    # Note: We don't have skipgram type marked in the data, so we'll count all by length
    # This is a simplification - the original data doesn't distinguish contiguous from skipgram
    # For now, we'll just count by length
    count_2word = sum(1 for p in deduplicated_phrases if p['length'] == 2)
    count_3word = sum(1 for p in deduplicated_phrases if p['length'] == 3)
    count_4plus = sum(1 for p in deduplicated_phrases if p['length'] >= 4)

    # Step 4: Calculate pattern points
    # 2-word = 1 point, 3-word = 2 points, 4+ word = 3 points
    total_pattern_points = (count_2word * 1) + (count_3word * 2) + (count_4plus * 3)

    # Step 5: Calculate root IDF sum with rare root bonus (2x for IDF >= 4.0)
    root_idf_sum = 0.0
    for root in deduplicated_roots:
        idf = root['idf']
        if idf >= 4.0:
            root_idf_sum += idf * 2  # Rare root bonus
        else:
            root_idf_sum += idf

    # Step 6: Calculate geometric mean length
    geometric_mean_length = math.sqrt(word_count_a * word_count_b)

    # Step 7: Calculate normalized scores
    phrase_score = (total_pattern_points / geometric_mean_length) * 1000
    root_score = (root_idf_sum / geometric_mean_length) * 1000
    final_score = phrase_score + root_score

    # Return comprehensive result
    return {
        'psalm_a': psalm_a,
        'psalm_b': psalm_b,

        # Deduplication stats
        'original_phrase_count': len(shared_phrases),
        'deduplicated_phrase_count': len(deduplicated_phrases),
        'phrases_removed_as_substrings': len(shared_phrases) - len(deduplicated_phrases),

        'original_root_count': len(shared_roots),
        'deduplicated_root_count': len(deduplicated_roots),
        'roots_removed_in_phrases': len(shared_roots) - len(deduplicated_roots),

        # Pattern counts (all from deduplicated phrases)
        'phrase_2word': count_2word,
        'phrase_3word': count_3word,
        'phrase_4plus': count_4plus,
        'total_pattern_points': total_pattern_points,

        # Root statistics (from deduplicated roots)
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
        'deduplicated_phrases': deduplicated_phrases,
        'deduplicated_roots': deduplicated_roots
    }


def main():
    """Calculate deduplicated scores for all psalm relationships."""

    base_dir = Path(__file__).parent.parent.parent

    # Load inputs
    logger.info("Loading data files...")

    with open(base_dir / "data/analysis_results/significant_relationships.json", 'r', encoding='utf-8') as f:
        relationships = json.load(f)
    logger.info(f"  Loaded {len(relationships)} relationships")

    with open(base_dir / "data/analysis_results/psalm_word_counts.json", 'r', encoding='utf-8') as f:
        word_counts_data = json.load(f)
        word_counts = word_counts_data['word_counts']
    logger.info(f"  Loaded word counts for {len(word_counts)} psalms")

    # Calculate deduplicated scores
    logger.info("Calculating deduplicated scores...")
    deduplicated_scores = []

    for i, rel in enumerate(relationships, 1):
        if i % 1000 == 0:
            logger.info(f"  Processing {i}/{len(relationships)}...")

        psalm_a = rel['psalm_a']
        psalm_b = rel['psalm_b']

        score_data = calculate_deduplicated_score(
            psalm_a=psalm_a,
            psalm_b=psalm_b,
            shared_phrases=rel['shared_phrases'],
            shared_roots=rel['shared_roots'],
            word_count_a=word_counts[str(psalm_a)],
            word_count_b=word_counts[str(psalm_b)],
            original_pvalue=rel['pvalue'],
            original_rank=i
        )

        deduplicated_scores.append(score_data)

    # Save results
    output_path = base_dir / "data/analysis_results/enhanced_scores_deduplicated.json"
    logger.info(f"Saving deduplicated scores to {output_path}...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(deduplicated_scores, f, indent=2, ensure_ascii=False)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"  File size: {file_size_mb:.2f} MB")

    # Summary statistics
    logger.info("\nDeduplication Statistics:")

    total_phrases_removed = sum(s['phrases_removed_as_substrings'] for s in deduplicated_scores)
    total_roots_removed = sum(s['roots_removed_in_phrases'] for s in deduplicated_scores)

    logger.info(f"  Total phrases removed as substrings: {total_phrases_removed:,}")
    logger.info(f"  Total roots removed (in phrases): {total_roots_removed:,}")

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
