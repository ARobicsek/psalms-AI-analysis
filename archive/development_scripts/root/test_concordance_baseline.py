"""
Baseline Concordance Test Suite

Tests all Psalm 3 queries against CURRENT concordance system
to establish baseline match counts before making changes.
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import json
from pathlib import Path
from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest
from src.data_sources.tanakh_database import TanakhDatabase

# Initialize
db = TanakhDatabase()
lib = ConcordanceLibrarian(db=db)

# Debug: Check database has concordance data
cursor = db.conn.cursor()
cursor.execute("SELECT COUNT(*) FROM concordance")
concordance_count = cursor.fetchone()[0]
print(f"\nDatabase concordance entries: {concordance_count}")
if concordance_count == 0:
    print("WARNING: Concordance table is empty! Results will be zero.")
    print(f"Database path: {db.db_path}")
print()

# Test queries from Psalm 3
test_queries = [
    {
        "id": 1,
        "query": "מה רבו",
        "alternates": ["מה רבים", "כמה רבו", "כמה רבים"],
        "description": "How numerous (opening lament)",
        "expected_contexts": ["Psalm 3:2"]
    },
    {
        "id": 2,
        "query": "אין ישועה",
        "alternates": ["אין תשועה", "אין הישועה", "לא ישועה"],
        "description": "No salvation",
        "expected_contexts": ["Psalm 3:3"]
    },
    {
        "id": 3,
        "query": "באלהים",
        "alternates": ["בה' ", "ביהוה", "לאלהים"],
        "description": "In God",
        "expected_contexts": ["Psalm 3:3"]
    },
    {
        "id": 4,
        "query": "מגן בעד",
        "alternates": ["מגן סביב", "מגן לי", "מגן עלי"],
        "description": "Shield around",
        "expected_contexts": ["Psalm 3:4"]
    },
    {
        "id": 5,
        "query": "מרים ראש",
        "alternates": ["נשא ראש", "רום ראש", "ירים ראשי", "ונשא ראשי"],
        "description": "Lifts head (honor restoration)",
        "expected_contexts": ["Psalm 3:4"]
    },
    {
        "id": 6,
        "query": "מהר קדש",
        "alternates": ["הר קדשו", "הר קדשי", "בהר קדש"],
        "description": "From holy mountain",
        "expected_contexts": ["Psalm 3:5"]
    },
    {
        "id": 7,
        "query": "שכבתי ואישנה",
        "alternates": ["שכב וישן", "אשכב ואישן", "שכבתי וישנתי"],
        "description": "I lay down and slept",
        "expected_contexts": ["Psalm 3:6"]
    },
    {
        "id": 8,
        "query": "קומה יהוה",
        "alternates": ["קום יהוה", "קומה ה'", "קום ה'"],
        "description": "Arise, LORD",
        "expected_contexts": ["Psalm 3:8"]
    },
    {
        "id": 9,
        "query": "הכית את",
        "alternates": ["הך את", "תכה את", "הכה את"],
        "description": "You struck (MAQQEF TEST - currently failing)",
        "expected_contexts": ["Psalm 3:8"],
        "expected_issue": "Maqqef combining: ki-hikita stored as 'כיהכית'"
    },
    {
        "id": 10,
        "query": "שבר שן",
        "alternates": ["שבר שיניים", "שבור שן", "שבר שני"],
        "description": "Break tooth (NON-ADJACENT TEST - currently failing)",
        "expected_contexts": ["Psalm 3:8"],
        "expected_issue": "Words not adjacent: שני רשעים שברת"
    },
    {
        "id": 11,
        "query": "על עמך ברכתך",
        "alternates": ["עמך ברכה", "ברך עמך", "ברכת עמך"],
        "description": "Your blessing on your people",
        "expected_contexts": ["Psalm 3:9"]
    },
    # Additional single-word tests
    {
        "id": 12,
        "query": "הכית",
        "alternates": [],
        "description": "Single word: struck (should work even with maqqef)",
        "expected_contexts": ["Psalm 3:8"]
    },
    {
        "id": 13,
        "query": "שני",
        "alternates": [],
        "description": "Single word: teeth (construct form)",
        "expected_contexts": ["Psalm 3:8"]
    },
    {
        "id": 14,
        "query": "שברת",
        "alternates": [],
        "description": "Single word: you broke",
        "expected_contexts": ["Psalm 3:8"]
    }
]

print("=" * 80)
print("CONCORDANCE BASELINE TEST SUITE")
print("Running against CURRENT system (before maqqef changes)")
print("=" * 80)

results = []

for test in test_queries:
    print(f"\n### Test {test['id']}: {test['description']}")
    # Skip printing Hebrew due to Unicode issues
    if 'expected_issue' in test:
        print(f"Expected Issue: (see test definition)")

    # Run concordance search
    req = ConcordanceRequest(
        query=test['query'],
        alternate_queries=test['alternates'] if test['alternates'] else None,
        scope="Tanakh",  # Capitalized - required for scope filtering
        level="consonantal"
    )

    bundle = lib.search_with_variations(req)

    # Record results
    result = {
        "test_id": test['id'],
        "query": test['query'],
        "alternates": test['alternates'],
        "description": test['description'],
        "total_results": len(bundle.results),
        "variations_searched": len(bundle.variations_searched),
        "found_in_psalm_3": False,
        "psalm_3_matches": []
    }

    # Check if Psalm 3 is in results
    for r in bundle.results:
        if r.book == "Psalms" and r.chapter == 3:
            result["found_in_psalm_3"] = True
            result["psalm_3_matches"].append({
                "verse": r.verse,
                "matched_word": r.matched_word,
                "position": r.word_position
            })

    results.append(result)

    # Display
    print(f"  Total Results: {result['total_results']}")
    print(f"  Variations Searched: {result['variations_searched']}")
    print(f"  Found in Psalm 3: {'YES' if result['found_in_psalm_3'] else 'NO'}")
    if result['found_in_psalm_3']:
        print(f"    - Found in {len(result['psalm_3_matches'])} verse(s)")

# Save baseline results
output_path = Path("output/debug/concordance_baseline_results.json")
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 80)
print("BASELINE RESULTS SUMMARY")
print("=" * 80)

# Summary statistics
total_tests = len(results)
tests_with_results = sum(1 for r in results if r['total_results'] > 0)
tests_finding_psalm_3 = sum(1 for r in results if r['found_in_psalm_3'])

print(f"Total Tests: {total_tests}")
print(f"Tests with Results: {tests_with_results}/{total_tests}")
print(f"Tests Finding Psalm 3: {tests_finding_psalm_3}/{total_tests}")

# Problematic queries
print("\n### Tests with NO results:")
for r in results:
    if r['total_results'] == 0:
        print(f"  - Test {r['test_id']}: {r['description']}")

print("\n### Tests NOT finding expected Psalm 3:")
for r in results:
    if r['total_results'] > 0 and not r['found_in_psalm_3']:
        print(f"  - Test {r['test_id']}: {r['description']} ({r['total_results']} results elsewhere)")

print(f"\nBaseline results saved to: {output_path}")
print("\n" + "=" * 80)
print("END BASELINE TEST")
print("=" * 80)
