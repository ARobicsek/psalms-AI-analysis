#!/usr/bin/env python3
"""
Analyze skipgram and contiguous phrase quality in top_550_connections file.
Identify patterns of interesting vs. trivial/formulaic connections.
"""

import json
from collections import Counter, defaultdict
import re

def load_connections(filepath):
    """Load the top 550 connections file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_pattern_frequencies(connections):
    """Count frequency of each pattern across all psalm pairs."""
    contiguous_patterns = Counter()
    skipgram_patterns = Counter()

    # Track which psalm pairs each pattern appears in
    contiguous_psalm_pairs = defaultdict(set)
    skipgram_psalm_pairs = defaultdict(set)

    for conn in connections:
        pair_id = f"{conn['psalm_a']}-{conn['psalm_b']}"

        # Analyze contiguous phrases
        for phrase in conn.get('deduplicated_contiguous_phrases', []):
            consonantal = phrase['consonantal']
            length = phrase['length']
            contiguous_patterns[(consonantal, length)] += 1
            contiguous_psalm_pairs[(consonantal, length)].add(pair_id)

        # Analyze skipgrams
        for skipgram in conn.get('deduplicated_skipgrams', []):
            consonantal = skipgram['consonantal']
            length = skipgram['length']
            skipgram_patterns[(consonantal, length)] += 1
            skipgram_psalm_pairs[(consonantal, length)].add(pair_id)

    return (contiguous_patterns, skipgram_patterns,
            contiguous_psalm_pairs, skipgram_psalm_pairs)

def is_divine_name_pattern(consonantal):
    """Check if pattern contains only divine names and function words."""
    divine_names = ['יהוה', 'אלהים', 'אדני', 'אל', 'שדי']

    # Split into words
    words = consonantal.split()

    # Check if all words are either divine names or very short (likely function words)
    for word in words:
        if word in divine_names:
            continue
        # If word is very short (1-2 chars), likely function word
        if len(word) <= 2:
            continue
        # Otherwise, it's content - not pure divine name pattern
        return False

    return True

def classify_pattern(consonantal, length, psalm_pair_count, hebrew_text=None):
    """Classify a pattern as interesting, formulaic, or noise."""

    # Very common patterns (appearing in many psalm pairs) are likely formulaic
    if psalm_pair_count >= 50:
        return "formulaic_high_frequency"

    # Divine name patterns
    if is_divine_name_pattern(consonantal):
        return "divine_name_formulaic"

    # Common 2-word patterns
    common_2word = [
        'אל יהוה',  # to YHWH
        'כי יהוה',  # for/because YHWH
        'יהוה אלהים',  # YHWH God
        'כל הארץ',  # all the earth
        'בני ישראל',  # sons of Israel
    ]

    if length == 2 and consonantal in common_2word:
        return "common_2word_phrase"

    # If appears in 20-49 pairs, moderately common - likely formulaic
    if psalm_pair_count >= 20:
        return "formulaic_moderate"

    # If appears in 10-19 pairs, could be interesting or formulaic
    if psalm_pair_count >= 10:
        return "borderline_formulaic"

    # If appears in 5-9 pairs, likely interesting
    if psalm_pair_count >= 5:
        return "likely_interesting"

    # If appears in 1-4 pairs, very likely interesting/unique
    return "unique_interesting"

def main():
    filepath = 'data/analysis_results/top_550_connections_skipgram_dedup_v4.json'

    print("Loading connections...")
    connections = load_connections(filepath)
    print(f"Loaded {len(connections)} psalm pair connections")

    print("\nAnalyzing pattern frequencies...")
    (cont_patterns, skip_patterns,
     cont_pairs, skip_pairs) = analyze_pattern_frequencies(connections)

    print(f"\nTotal unique contiguous patterns: {len(cont_patterns)}")
    print(f"Total unique skipgram patterns: {len(skip_patterns)}")

    # Classify contiguous patterns
    print("\n" + "="*80)
    print("CONTIGUOUS PHRASE ANALYSIS")
    print("="*80)

    contiguous_classified = defaultdict(list)
    for (consonantal, length), count in cont_patterns.items():
        pair_count = len(cont_pairs[(consonantal, length)])
        classification = classify_pattern(consonantal, length, pair_count)
        contiguous_classified[classification].append((consonantal, length, count, pair_count))

    for classification in ['formulaic_high_frequency', 'divine_name_formulaic',
                          'common_2word_phrase', 'formulaic_moderate',
                          'borderline_formulaic', 'likely_interesting', 'unique_interesting']:
        patterns = contiguous_classified[classification]
        if patterns:
            print(f"\n{classification.upper().replace('_', ' ')} ({len(patterns)} patterns):")
            # Sort by psalm pair count (descending)
            patterns.sort(key=lambda x: x[3], reverse=True)
            for consonantal, length, count, pair_count in patterns[:15]:  # Show top 15
                print(f"  {consonantal:40} | len={length} | appears {count}x | in {pair_count} pairs")

    # Classify skipgram patterns
    print("\n" + "="*80)
    print("SKIPGRAM ANALYSIS")
    print("="*80)

    skipgram_classified = defaultdict(list)
    for (consonantal, length), count in skip_patterns.items():
        pair_count = len(skip_pairs[(consonantal, length)])
        classification = classify_pattern(consonantal, length, pair_count)
        skipgram_classified[classification].append((consonantal, length, count, pair_count))

    for classification in ['formulaic_high_frequency', 'divine_name_formulaic',
                          'common_2word_phrase', 'formulaic_moderate',
                          'borderline_formulaic', 'likely_interesting', 'unique_interesting']:
        patterns = skipgram_classified[classification]
        if patterns:
            print(f"\n{classification.upper().replace('_', ' ')} ({len(patterns)} patterns):")
            patterns.sort(key=lambda x: x[3], reverse=True)
            for consonantal, length, count, pair_count in patterns[:15]:
                print(f"  {consonantal:40} | len={length} | appears {count}x | in {pair_count} pairs")

    # Generate statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)

    print("\nContiguous Phrases by Classification:")
    for classification in sorted(contiguous_classified.keys()):
        count = len(contiguous_classified[classification])
        total_appearances = sum(x[2] for x in contiguous_classified[classification])
        print(f"  {classification:30} | {count:5} patterns | {total_appearances:6} total appearances")

    print("\nSkipgrams by Classification:")
    for classification in sorted(skipgram_classified.keys()):
        count = len(skipgram_classified[classification])
        total_appearances = sum(x[2] for x in skipgram_classified[classification])
        print(f"  {classification:30} | {count:5} patterns | {total_appearances:6} total appearances")

    # Identify most problematic patterns
    print("\n" + "="*80)
    print("TOP 30 MOST COMMON PATTERNS (Likely Noise)")
    print("="*80)

    print("\nContiguous:")
    all_cont = [(cons, length, count, len(cont_pairs[(cons, length)]))
                for (cons, length), count in cont_patterns.items()]
    all_cont.sort(key=lambda x: x[3], reverse=True)  # Sort by psalm pair count
    for consonantal, length, count, pair_count in all_cont[:30]:
        print(f"  {consonantal:40} | len={length} | {count:4}x | {pair_count:3} pairs")

    print("\nSkipgrams:")
    all_skip = [(cons, length, count, len(skip_pairs[(cons, length)]))
                for (cons, length), count in skip_patterns.items()]
    all_skip.sort(key=lambda x: x[3], reverse=True)
    for consonantal, length, count, pair_count in all_skip[:30]:
        print(f"  {consonantal:40} | len={length} | {count:4}x | {pair_count:3} pairs")

if __name__ == '__main__':
    main()
