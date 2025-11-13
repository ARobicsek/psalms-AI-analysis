"""
Test Phrase Extraction

Quick test to verify phrase extraction works before running full analysis.
"""

import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent))

from root_extractor import RootExtractor
from pairwise_comparator import PairwiseComparator
from database_builder import PsalmRelationshipsDB

logging.basicConfig(level=logging.INFO)

# Test on Psalms 14 & 53 (known to be nearly identical)
tanakh_db = Path(__file__).parent.parent.parent / 'database' / 'tanakh.db'
relationships_db = Path(__file__).parent.parent.parent / 'data' / 'psalm_relationships_test.db'

print("=" * 80)
print("Testing Phrase Extraction on Psalms 14 & 53")
print("=" * 80)

# Clean up any existing test db
if relationships_db.exists():
    relationships_db.unlink()

# Extract roots and phrases
extractor = RootExtractor(tanakh_db)

print("\n1. Extracting from Psalm 14...")
result_14 = extractor.extract_psalm_roots(14, include_phrases=True)
print(f"   Roots: {len(result_14['roots'])}")
print(f"   Phrases: {len(result_14['phrases'])}")

print("\n2. Extracting from Psalm 53...")
result_53 = extractor.extract_psalm_roots(53, include_phrases=True)
print(f"   Roots: {len(result_53['roots'])}")
print(f"   Phrases: {len(result_53['phrases'])}")

# Show sample phrases from Psalm 14
print("\n3. Sample phrases from Psalm 14:")
for i, phrase in enumerate(result_14['phrases'][:5], 1):
    print(f"   {i}. {phrase['hebrew']} ({phrase['consonantal']}) [v.{phrase['verse']}]")

# Store in test database
print("\n4. Storing in test database...")
db = PsalmRelationshipsDB(relationships_db)

# Group phrases by consonantal form
phrase_groups_14 = {}
for phrase in result_14['phrases']:
    key = phrase['consonantal']
    if key not in phrase_groups_14:
        phrase_groups_14[key] = {
            'consonantal': phrase['consonantal'],
            'hebrew': phrase['hebrew'],
            'length': phrase['length'],
            'count': 0,
            'verses': []
        }
    phrase_groups_14[key]['count'] += 1
    phrase_groups_14[key]['verses'].append(phrase['verse'])

db.store_psalm_roots(14, result_14['roots'])
db.store_psalm_phrases(14, list(phrase_groups_14.values()))

phrase_groups_53 = {}
for phrase in result_53['phrases']:
    key = phrase['consonantal']
    if key not in phrase_groups_53:
        phrase_groups_53[key] = {
            'consonantal': phrase['consonantal'],
            'hebrew': phrase['hebrew'],
            'length': phrase['length'],
            'count': 0,
            'verses': []
        }
    phrase_groups_53[key]['count'] += 1
    phrase_groups_53[key]['verses'].append(phrase['verse'])

db.store_psalm_roots(53, result_53['roots'])
db.store_psalm_phrases(53, list(phrase_groups_53.values()))

print(f"   ✓ Stored roots and phrases")

# Test phrase comparison
print("\n5. Testing phrase comparison...")
comparator = PairwiseComparator(relationships_db)

# Update IDF scores
db.update_root_frequencies()

result = comparator.compare_pair(14, 53)

print(f"\n6. Comparison Results:")
print(f"   Shared roots: {result['shared_root_count']}")
print(f"   Shared phrases: {result['shared_phrase_count']}")
print(f"   p-value: {result['pvalue']:.2e}")

if result['shared_phrases']:
    print(f"\n7. Sample shared phrases:")
    for i, phrase in enumerate(result['shared_phrases'][:5], 1):
        print(f"   {i}. {phrase['hebrew']} ({phrase['consonantal']})")
        print(f"      Length: {phrase['length']}, Ps 14: {phrase['count_a']}x, Ps 53: {phrase['count_b']}x")
else:
    print(f"\n⚠ No shared phrases found")

print("\n" + "=" * 80)
print("✓ Test complete!")
print("=" * 80)

# Clean up test db
db.close()
comparator.close()
if relationships_db.exists():
    relationships_db.unlink()
    print(f"✓ Cleaned up test database")
