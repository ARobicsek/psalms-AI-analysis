"""
Summary of findings for the three issues
"""
import sqlite3
import json
from pathlib import Path

db_path = Path("database/tanakh.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

results = {
    "issue_1_quotation_marks": {
        "status": "NOT AN ISSUE",
        "explanation": "Python displays strings with apostrophes using double quotes. This is normal Python behavior."
    },
    "issue_2_hakita_et": {
        "query": "hakita et (you struck)",
        "expected": "Common expression, many results",
        "actual": "2 results",
        "psalm_3_8_words": []
    },
    "issue_3_shavar_shen": {
        "query": "shavar shen (break tooth)",
        "expected": "At least 1 result (Psalm 3:8)",
        "actual": "0 results",
        "psalm_3_8_words": []
    }
}

# Get Psalm 3:8 words
cursor.execute("""
    SELECT position, word, word_consonantal
    FROM concordance
    WHERE book_name = 'Psalms' AND chapter = 3 AND verse = 8
    ORDER BY position
""")
psalm_words = []
for pos, word, cons in cursor.fetchall():
    psalm_words.append({
        "position": pos,
        "word": word,
        "consonantal": cons
    })

# Issue 2: hakita et
# Position 5: ki-hikita (for you struck) = "כיהכית"
# Position 6: et-kol-oyvai (all my enemies) = "אתכלאיבי"
results["issue_2_hakita_et"]["psalm_3_8_words"] = psalm_words
results["issue_2_hakita_et"]["diagnosis"] = {
    "problem": "Maqqef combining",
    "details": [
        "Position 5: 'ki-hikita' (for-you-struck) stored as 'כיהכית'",
        "Position 6: 'et-kol-oyvai' (all-my-enemies) stored as 'אתכלאיבי'",
        "'הכית' is embedded in 'כיהכית' (with prefix 'כי')",
        "'את' is embedded in 'אתכלאיבי' (combined with 'כל' and 'איבי')",
        "These are not adjacent standalone words"
    ]
}

# Count how many times "הכית" appears (with conjugation)
cursor.execute("""
    SELECT COUNT(*)
    FROM concordance
    WHERE word_consonantal LIKE '%הכית%'
""")
hakita_count = cursor.fetchone()[0]
results["issue_2_hakita_et"]["hakita_in_tanakh"] = hakita_count

# Issue 3: shavar shen
# Position 8: shinei (teeth of) = "שני"
# Position 9: resha'im (wicked ones) = "רשעים"
# Position 10: shibarta (you broke) = "שברת"
results["issue_3_shavar_shen"]["psalm_3_8_words"] = psalm_words
results["issue_3_shavar_shen"]["diagnosis"] = {
    "problem": "Non-adjacent words + morphological differences",
    "details": [
        "Position 8: 'shinei' (teeth-of) = 'שני' (construct form, not 'שן')",
        "Position 9: 'resha'im' (wicked-ones) = 'רשעים' (in between!)",
        "Position 10: 'shibarta' (you-broke) = 'שברת' (past tense, not 'שבר')",
        "Query was 'שבר שן' but text has 'שני ... שברת'",
        "Words are NOT adjacent (רשעים in between)",
        "Morphological forms differ (שני not שן, שברת not שבר)"
    ]
}

# Count individual words
cursor.execute("SELECT COUNT(*) FROM concordance WHERE word_consonantal LIKE '%שבר%'")
shavar_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM concordance WHERE word_consonantal LIKE '%שן%'")
shen_count = cursor.fetchone()[0]
results["issue_3_shavar_shen"]["individual_word_counts"] = {
    "shavar_variations": shavar_count,
    "shen_variations": shen_count
}

# Save results
output_path = Path("output/debug/investigation_findings.json")
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Findings saved to: {output_path}")
print("\n=== SUMMARY ===")
print(f"\nIssue 1: Quote marks - {results['issue_1_quotation_marks']['status']}")
print(f"\nIssue 2: hakita et")
print(f"  - Found {hakita_count} instances of 'hakita' in Tanakh")
print(f"  - Problem: Maqqef combining and embedded words")
print(f"\nIssue 3: shavar shen")
print(f"  - Found {shavar_count} instances of 'shavar' variants")
print(f"  - Found {shen_count} instances of 'shen' variants")
print(f"  - Problem: Non-adjacent words + morphological mismatch")

conn.close()
