#!/usr/bin/env python3
"""
Analyze linguistic quality of patterns based on Hebrew word types.
Identify patterns composed of function words vs. content words.
"""

import json
from collections import Counter, defaultdict

# Common function words in Hebrew Psalms
FUNCTION_WORDS = {
    # Prepositions
    'ב', 'בי', 'בו', 'בה', 'בם', 'בן', 'בך', 'בכם', 'בנו',
    'ל', 'לי', 'לו', 'לה', 'לם', 'לן', 'לך', 'לכם', 'לנו',
    'מ', 'מי', 'מו', 'מה', 'מם', 'מן', 'מך', 'מכם', 'מנו',
    'על', 'אל', 'את', 'עם', 'כ', 'מן',

    # Conjunctions
    'ו', 'כי', 'אם', 'פן', 'אשר', 'זה', 'זאת',

    # Particles
    'לא', 'כל', 'גם', 'רק', 'הן', 'הנה', 'נא',

    # Pronouns (short forms)
    'אנ', 'אני', 'אתה', 'את', 'הוא', 'היא', 'אנחנו', 'אתם', 'אתן', 'הם', 'הן',
    'י', 'ך', 'ו', 'ה', 'נו', 'כם', 'כן', 'ם', 'ן',

    # Common short words
    'יום', 'כן', 'עד', 'עוד', 'הד',
}

# Divine names and titles
DIVINE_NAMES = {
    'יהוה', 'יהו', 'אלהים', 'אלה', 'אל', 'אלוה', 'אדני', 'אדנ', 'יה', 'שדי', 'צבאות', 'עליון',
}

# Common liturgical/title words
LITURGICAL = {
    'מזמור', 'זמור', 'שיר', 'תפלה', 'תהלה', 'הלל', 'הללו', 'הללויה', 'סלה',
    'דוד', 'אסף', 'בני', 'קרח', 'נצח', 'למנצח',
}

def classify_word(word):
    """Classify a Hebrew word by type."""
    if word in DIVINE_NAMES:
        return 'divine_name'
    if word in LITURGICAL:
        return 'liturgical'
    if word in FUNCTION_WORDS:
        return 'function'
    # If <= 2 chars and not identified above, likely function word fragment
    if len(word) <= 2:
        return 'function_likely'
    # Otherwise assume content word (verb, noun, adjective)
    return 'content'

def analyze_pattern_composition(consonantal):
    """Analyze the composition of a pattern (function vs content words)."""
    words = consonantal.split()
    classifications = [classify_word(w) for w in words]

    return {
        'words': words,
        'classifications': classifications,
        'divine_name_count': classifications.count('divine_name'),
        'liturgical_count': classifications.count('liturgical'),
        'function_count': classifications.count('function') + classifications.count('function_likely'),
        'content_count': classifications.count('content'),
        'total_words': len(words),
    }

def determine_pattern_quality(composition):
    """Determine if a pattern is high quality based on word composition."""
    # Pure divine names + function words = formulaic/noise
    if composition['content_count'] == 0:
        if composition['divine_name_count'] > 0:
            return 'formulaic_divine'
        if composition['liturgical_count'] > 0:
            return 'formulaic_liturgical'
        return 'formulaic_function_only'

    # 1 content word with divine names/function = borderline
    if composition['content_count'] == 1:
        if composition['divine_name_count'] > 0 or composition['function_count'] >= composition['total_words'] - 1:
            return 'borderline_light_content'

    # 2+ content words = likely interesting
    if composition['content_count'] >= 2:
        return 'interesting_multi_content'

    # 1+ content words, no divine names = interesting
    if composition['content_count'] >= 1 and composition['divine_name_count'] == 0:
        return 'interesting_content_focused'

    return 'unclear'

def main():
    filepath = 'data/analysis_results/top_550_connections_skipgram_dedup_v4.json'

    print("Loading connections...")
    with open(filepath, 'r', encoding='utf-8') as f:
        connections = json.load(f)

    print(f"Loaded {len(connections)} psalm pair connections")

    # Analyze all skipgrams
    print("\n" + "="*80)
    print("SKIPGRAM LINGUISTIC QUALITY ANALYSIS")
    print("="*80)

    quality_counts = Counter()
    quality_examples = defaultdict(list)
    pattern_frequencies = Counter()

    for conn in connections:
        for skipgram in conn.get('deduplicated_skipgrams', []):
            consonantal = skipgram['consonantal']
            pattern_frequencies[consonantal] += 1

            composition = analyze_pattern_composition(consonantal)
            quality = determine_pattern_quality(composition)

            quality_counts[quality] += 1

            # Save examples
            if len(quality_examples[quality]) < 20:
                quality_examples[quality].append({
                    'consonantal': consonantal,
                    'composition': composition,
                    'pair': f"Ps {conn['psalm_a']}/{conn['psalm_b']}",
                    'hebrew': skipgram.get('hebrew', 'N/A'),
                })

    print("\nQuality Distribution:")
    for quality, count in quality_counts.most_common():
        pct = 100 * count / sum(quality_counts.values())
        print(f"  {quality:35} {count:5} ({pct:5.1f}%)")

    # Show examples
    for quality in ['formulaic_divine', 'formulaic_liturgical', 'formulaic_function_only',
                   'borderline_light_content', 'interesting_content_focused', 'interesting_multi_content']:
        examples = quality_examples.get(quality, [])
        if examples:
            print(f"\n{quality.upper().replace('_', ' ')} - Examples:")
            print("-" * 80)
            for ex in examples[:10]:
                comp = ex['composition']
                freq = pattern_frequencies[ex['consonantal']]
                print(f"  {ex['consonantal']:35} | {ex['pair']:12} | freq={freq:3}")
                print(f"    Words: {' | '.join(f'{w}[{c}]' for w, c in zip(comp['words'], comp['classifications']))}")
                print(f"    Content: {comp['content_count']}, Divine: {comp['divine_name_count']}, "
                      f"Function: {comp['function_count']}, Liturgical: {comp['liturgical_count']}")
                print()

    # Analyze contiguous phrases too
    print("\n" + "="*80)
    print("CONTIGUOUS PHRASE LINGUISTIC QUALITY ANALYSIS")
    print("="*80)

    quality_counts_cont = Counter()
    quality_examples_cont = defaultdict(list)
    pattern_frequencies_cont = Counter()

    for conn in connections:
        for phrase in conn.get('deduplicated_contiguous_phrases', []):
            consonantal = phrase['consonantal']
            pattern_frequencies_cont[consonantal] += 1

            composition = analyze_pattern_composition(consonantal)
            quality = determine_pattern_quality(composition)

            quality_counts_cont[quality] += 1

            if len(quality_examples_cont[quality]) < 20:
                quality_examples_cont[quality].append({
                    'consonantal': consonantal,
                    'composition': composition,
                    'pair': f"Ps {conn['psalm_a']}/{conn['psalm_b']}",
                    'hebrew': phrase.get('hebrew', 'N/A'),
                })

    print("\nQuality Distribution:")
    for quality, count in quality_counts_cont.most_common():
        pct = 100 * count / sum(quality_counts_cont.values())
        print(f"  {quality:35} {count:5} ({pct:5.1f}%)")

    # Recommendations
    print("\n" + "="*80)
    print("FILTERING RECOMMENDATIONS")
    print("="*80)

    # Count formulaic patterns
    formulaic_skipgrams = (quality_counts['formulaic_divine'] +
                          quality_counts['formulaic_liturgical'] +
                          quality_counts['formulaic_function_only'])
    total_skipgrams = sum(quality_counts.values())

    formulaic_contiguous = (quality_counts_cont['formulaic_divine'] +
                           quality_counts_cont['formulaic_liturgical'] +
                           quality_counts_cont['formulaic_function_only'])
    total_contiguous = sum(quality_counts_cont.values())

    print(f"\nFormulaic skipgrams: {formulaic_skipgrams}/{total_skipgrams} ({100*formulaic_skipgrams/total_skipgrams:.1f}%)")
    print(f"Formulaic contiguous: {formulaic_contiguous}/{total_contiguous} ({100*formulaic_contiguous/total_contiguous:.1f}%)")

    print("\nFiltering strategy:")
    print("1. Remove patterns with 0 content words (pure function/divine/liturgical)")
    print("2. Consider requiring 2+ content words for skipgrams (stricter)")
    print("3. Weight patterns by content word ratio")

    # Identify specific high-frequency formulaic patterns to stoplist
    print("\n" + "="*80)
    print("TOP FORMULAIC PATTERNS FOR STOPLIST")
    print("="*80)

    formulaic_skipgrams_list = []
    for ex in quality_examples['formulaic_divine']:
        freq = pattern_frequencies[ex['consonantal']]
        if freq >= 10:  # High frequency
            formulaic_skipgrams_list.append((ex['consonantal'], freq, 'skipgram'))

    for ex in quality_examples['formulaic_liturgical']:
        freq = pattern_frequencies[ex['consonantal']]
        if freq >= 10:
            formulaic_skipgrams_list.append((ex['consonantal'], freq, 'skipgram'))

    formulaic_skipgrams_list.sort(key=lambda x: x[1], reverse=True)

    print("\nSkipgram stoplist candidates (freq >= 10):")
    for cons, freq, ptype in formulaic_skipgrams_list[:30]:
        print(f"  '{cons}' - appears {freq} times")

    # Similar for contiguous
    formulaic_contiguous_list = []
    for quality in ['formulaic_divine', 'formulaic_liturgical', 'formulaic_function_only']:
        for ex in quality_examples_cont.get(quality, []):
            freq = pattern_frequencies_cont[ex['consonantal']]
            if freq >= 10:
                formulaic_contiguous_list.append((ex['consonantal'], freq, 'contiguous'))

    formulaic_contiguous_list.sort(key=lambda x: x[1], reverse=True)

    print("\nContiguous phrase stoplist candidates (freq >= 10):")
    for cons, freq, ptype in formulaic_contiguous_list[:30]:
        print(f"  '{cons}' - appears {freq} times")

if __name__ == '__main__':
    main()
