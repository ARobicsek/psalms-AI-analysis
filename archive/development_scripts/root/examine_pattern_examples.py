#!/usr/bin/env python3
"""
Examine specific examples of skipgrams and contiguous phrases to understand quality.
"""

import json
import random

def load_connections(filepath):
    """Load the top 550 connections file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_pattern_examples(connections, consonantal, pattern_type='skipgram', max_examples=5):
    """Find examples of a specific pattern in the connections."""
    examples = []

    for conn in connections:
        pair_id = f"Ps {conn['psalm_a']}/{conn['psalm_b']}"
        patterns = conn.get(f'deduplicated_{pattern_type}s', [])

        for pattern in patterns:
            if pattern['consonantal'] == consonantal:
                examples.append({
                    'pair': pair_id,
                    'pattern': pattern,
                    'score': conn.get('final_score', 0)
                })
                if len(examples) >= max_examples:
                    return examples

    return examples

def display_pattern(pattern_info):
    """Display a pattern with its details."""
    pattern = pattern_info['pattern']
    print(f"  Pair: {pattern_info['pair']} (score: {pattern_info['score']:.1f})")
    print(f"  Consonantal: {pattern['consonantal']}")
    print(f"  Hebrew: {pattern.get('hebrew', 'N/A')}")
    print(f"  Length: {pattern['length']}")

    if 'gap_word_count' in pattern:
        print(f"  Gap: {pattern['gap_word_count']} words")

    # Show first couple matches
    matches_a = pattern.get('matches_from_a', [])
    matches_b = pattern.get('matches_from_b', [])

    if matches_a:
        print(f"  First match from Psalm {pattern_info['pair'].split('/')[0].split()[1]}:")
        match = matches_a[0]
        print(f"    Verse {match['verse']}: {match['text']}")

    if matches_b:
        print(f"  First match from Psalm {pattern_info['pair'].split('/')[1]}:")
        match = matches_b[0]
        print(f"    Verse {match['verse']}: {match['text']}")

def main():
    filepath = 'data/analysis_results/top_550_connections_skipgram_dedup_v4.json'

    print("Loading connections...")
    connections = load_connections(filepath)

    print("\n" + "="*80)
    print("EXAMINING NOISE PATTERNS (High Frequency)")
    print("="*80)

    noise_patterns = [
        ('יהוה אל', 'skipgram', 'YHWH + El (divine names)'),
        ('כי יהוה', 'skipgram', 'ki + YHWH (function word + divine name)'),
        ('כי אתה', 'skipgram', 'ki + atah (because you)'),
        ('את יהו', 'contiguous', 'et + YHWH (object marker + divine name)'),
        ('זמור דוד', 'contiguous', 'mizmor david (psalm title)'),
        ('כי את', 'contiguous', 'ki + et (function words)'),
    ]

    for consonantal, ptype, description in noise_patterns:
        print(f"\n{description.upper()}: '{consonantal}' ({ptype})")
        print("-" * 80)
        examples = find_pattern_examples(connections, consonantal, ptype, 3)
        for ex in examples:
            display_pattern(ex)
            print()

    print("\n" + "="*80)
    print("EXAMINING POTENTIALLY INTERESTING PATTERNS")
    print("="*80)

    interesting_patterns = [
        ('לא ידע', 'skipgram', 'lo yada (not know)'),
        ('פעל און', 'contiguous', 'poel aven (workers of iniquity)'),
        ('בקש נפש', 'contiguous', 'biqesh nefesh (seek soul/life)'),
        ('ענ אביון', 'contiguous', 'ani evyon (poor/needy)'),
        ('ראה עני', 'skipgram', 'raah oni (see affliction)'),
    ]

    for consonantal, ptype, description in interesting_patterns:
        print(f"\n{description.upper()}: '{consonantal}' ({ptype})")
        print("-" * 80)
        examples = find_pattern_examples(connections, consonantal, ptype, 3)
        for ex in examples:
            display_pattern(ex)
            print()

    # Sample some unique interesting patterns
    print("\n" + "="*80)
    print("RANDOM SAMPLE OF UNIQUE/RARE PATTERNS (1-4 psalm pairs)")
    print("="*80)

    # Collect all unique patterns
    unique_patterns = []
    pattern_counts = {}

    for conn in connections:
        for skipgram in conn.get('deduplicated_skipgrams', []):
            cons = skipgram['consonantal']
            pattern_counts[cons] = pattern_counts.get(cons, 0) + 1

    # Get patterns appearing 1-4 times
    for cons, count in pattern_counts.items():
        if 1 <= count <= 4:
            unique_patterns.append(cons)

    # Sample 10 random ones
    if unique_patterns:
        sampled = random.sample(unique_patterns, min(10, len(unique_patterns)))
        for consonantal in sampled:
            print(f"\nPATTERN: '{consonantal}'")
            print("-" * 80)
            examples = find_pattern_examples(connections, consonantal, 'skipgram', 2)
            for ex in examples:
                display_pattern(ex)
                print()

if __name__ == '__main__':
    main()
