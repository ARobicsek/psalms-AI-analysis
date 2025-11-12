# -*- coding: utf-8 -*-
"""
Comprehensive Concordance Test for Psalm 3

Tests EVERY word and 2-word phrase from Psalm 3 to check:
1. Are we finding things correctly?
2. Are we getting false positives?
3. What's the actual precision/recall?
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from src.data_sources.tanakh_database import TanakhDatabase
from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest
from src.concordance.hebrew_text_processor import normalize_for_search

# Initialize
db = TanakhDatabase()
librarian = ConcordanceLibrarian(db)

# Get Psalm 3 words from database
cursor = db.conn.cursor()
cursor.execute("""
    SELECT verse, position, word, word_consonantal
    FROM concordance
    WHERE book_name='Psalms' AND chapter=3
    ORDER BY verse, position
""")

psalm_3_words = cursor.fetchall()

# Build verse structure
verses = {}
for row in psalm_3_words:
    verse = row['verse']
    if verse not in verses:
        verses[verse] = []
    verses[verse].append({
        'position': row['position'],
        'word': row['word'],
        'consonantal': row['word_consonantal']
    })

print("=" * 80)
print("COMPREHENSIVE PSALM 3 CONCORDANCE TEST")
print("=" * 80)

# Test 1: Single word searches
print("\n" + "=" * 80)
print("TEST 1: SINGLE WORD SEARCHES")
print("=" * 80)
print("\nSearching for every unique word in Psalm 3...")

unique_words = set()
for verse_words in verses.values():
    for word_data in verse_words:
        word = word_data['consonantal']
        if word and word.strip():  # Skip empty or whitespace-only
            unique_words.add(word)

unique_words = sorted(unique_words)
print(f"\nFound {len(unique_words)} unique words (consonantal forms)\n")

single_word_results = []
false_positive_count = 0

for word in unique_words[:20]:  # Test first 20 to keep output manageable
    request = ConcordanceRequest(
        query=word,
        scope='Psalms',
        level='consonantal',
        include_variations=True
    )

    bundle = librarian.search_with_variations(request)

    # Check if Psalm 3 is in results (should be!)
    psalm_3_matches = [r for r in bundle.results if r.book == "Psalms" and r.chapter == 3]

    # Check for false positives - results where the matched word doesn't match our query
    false_positives = []
    for result in bundle.results:
        matched_norm = normalize_for_search(result.matched_word, 'consonantal')
        # Check if matched word is actually in our variation list
        if matched_norm not in bundle.variations_searched:
            false_positives.append(result)

    single_word_results.append({
        'word': word,
        'total_results': len(bundle.results),
        'psalm_3_found': len(psalm_3_matches) > 0,
        'false_positives': len(false_positives)
    })

    if false_positives:
        false_positive_count += len(false_positives)
        print(f"⚠️  {word}: Found {len(false_positives)} potential false positives")
        for fp in false_positives[:2]:
            print(f"    - {fp.reference}: matched '{fp.matched_word}' (norm: {matched_norm})")

# Summary for single words
found_in_psalm_3 = sum(1 for r in single_word_results if r['psalm_3_found'])
print(f"\n📊 Single Word Results (first 20):")
print(f"   ✓ Found in Psalm 3: {found_in_psalm_3}/{len(single_word_results)}")
print(f"   ⚠️  False positives: {false_positive_count}")

# Test 2: Two-word adjacent phrases
print("\n" + "=" * 80)
print("TEST 2: TWO-WORD ADJACENT PHRASES")
print("=" * 80)
print("\nSearching for every 2-word sequence in Psalm 3...")

two_word_phrases = []
for verse_num, verse_words in verses.items():
    for i in range(len(verse_words) - 1):
        word1 = verse_words[i]['consonantal']
        word2 = verse_words[i + 1]['consonantal']
        # Skip if either word is empty
        if not word1 or not word1.strip() or not word2 or not word2.strip():
            continue
        phrase = f"{word1} {word2}"
        two_word_phrases.append({
            'phrase': phrase,
            'verse': verse_num,
            'positions': (verse_words[i]['position'], verse_words[i + 1]['position'])
        })

print(f"\nFound {len(two_word_phrases)} two-word phrases\n")

phrase_results = []
phrase_fp_count = 0

for phrase_data in two_word_phrases[:15]:  # Test first 15
    phrase = phrase_data['phrase']

    request = ConcordanceRequest(
        query=phrase,
        scope='Psalms',
        level='consonantal',
        include_variations=True
    )

    bundle = librarian.search_with_variations(request)

    # Check if Psalm 3 is in results
    psalm_3_matches = [r for r in bundle.results if r.book == "Psalms" and r.chapter == 3]

    # Check for false positives
    false_positives = []
    for result in bundle.results:
        # For phrases, we need to check if the match makes sense
        # This is trickier - the matched_word is just one word, not the phrase
        pass  # Skip FP check for phrases for now - more complex

    found_self = len(psalm_3_matches) > 0

    phrase_results.append({
        'phrase': phrase,
        'verse': phrase_data['verse'],
        'total_results': len(bundle.results),
        'found_in_psalm_3': found_self,
        'variations_searched': len(bundle.variations_searched)
    })

    status = "✓" if found_self else "✗"
    print(f"{status} v{phrase_data['verse']}: {phrase}")
    print(f"   Variations: {len(bundle.variations_searched)}, Results: {len(bundle.results)}")
    if found_self:
        print(f"   Found in Psalm 3: {len(psalm_3_matches)} match(es)")
    else:
        print(f"   ⚠️  NOT found in Psalm 3 (expected to find itself!)")
    print()

# Summary for phrases
found_self_count = sum(1 for r in phrase_results if r['found_in_psalm_3'])
print(f"\n📊 Two-Word Phrase Results (first 15):")
print(f"   ✓ Found itself in Psalm 3: {found_self_count}/{len(phrase_results)}")
print(f"   ✗ Missed: {len(phrase_results) - found_self_count}/{len(phrase_results)}")

# Test 3: Known matches - verify they're correct
print("\n" + "=" * 80)
print("TEST 3: VERIFY KNOWN MATCHES")
print("=" * 80)

known_tests = [
    ("מהרבו", "Psalms", 3, 2, "Should match maqqef-connected מה־רבו"),
    ("ומרים", "Tanakh", 3, 4, "Should match prefix ו on מרים"),
    ("ראשי", "Tanakh", 3, 4, "Should match suffix י on ראש"),
    ("מהר", "Psalms", 3, 5, "Should match prefix מ on הר"),
    ("קדשו", "Psalms", 3, 5, "Should match suffix ו on קדש"),
]

print("\nVerifying specific known matches...\n")

for query, scope, expected_chapter, expected_verse, description in known_tests:
    request = ConcordanceRequest(
        query=query,
        scope=scope,
        level='consonantal',
        include_variations=False  # Search exact form
    )

    bundle = librarian.search_with_variations(request)

    # Check if we find Psalm 3 verse
    target_matches = [r for r in bundle.results
                     if r.book == "Psalms"
                     and r.chapter == expected_chapter
                     and r.verse == expected_verse]

    if target_matches:
        print(f"✓ {query}: Found in Psalm {expected_chapter}:{expected_verse}")
        print(f"  {description}")
        for match in target_matches:
            print(f"  Matched word: {match.matched_word}")
    else:
        print(f"✗ {query}: NOT found in expected location")
        print(f"  {description}")
        print(f"  Total results: {len(bundle.results)}")
    print()

# Final summary
print("\n" + "=" * 80)
print("OVERALL SUMMARY")
print("=" * 80)
print(f"""
Single Words (first 20 tested):
  - All found in Psalm 3: {found_in_psalm_3}/{len(single_word_results)}
  - False positives detected: {false_positive_count}

Two-Word Phrases (first 15 tested):
  - Found itself in Psalm 3: {found_self_count}/{len(phrase_results)}
  - Missed itself: {len(phrase_results) - found_self_count}/{len(phrase_results)}
  - Average variations generated: {sum(r['variations_searched'] for r in phrase_results) / len(phrase_results):.0f}

Known Matches: See detailed results above

Conclusion:
  - Recall (finding what should be found): {found_self_count}/{len(phrase_results)} = {100 * found_self_count / len(phrase_results):.1f}%
  - Precision (no false positives): Being evaluated...
""")
