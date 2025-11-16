#!/usr/bin/env python3
"""Verify that the fixes for Psalm 69-76 are working."""

import json

# Load the NEW V5 top 550
with open('data/analysis_results/top_550_connections_skipgram_dedup_v5.json', 'r', encoding='utf-8') as f:
    top_550 = json.load(f)

# Find connection 69-76
for conn in top_550:
    if conn['psalm_a'] == 69 and conn['psalm_b'] == 76:
        print("=" * 70)
        print(f"PSALM 69-76 CONNECTION (NEW V5) - Rank #{conn['rank']}")
        print("=" * 70)

        print(f"\n📊 STATS:")
        print(f"  Contiguous phrases: {len(conn['deduplicated_contiguous_phrases'])}")
        print(f"  Skipgrams: {len(conn['deduplicated_skipgrams'])}")
        print(f"  Roots: {len(conn['deduplicated_roots'])}")

        # Issue #1: Check for duplicate patterns (contiguous appearing in skipgrams)
        print(f"\n🔍 ISSUE #1: Duplicate Patterns Check")
        contiguous_patterns = {p['consonantal'] for p in conn['deduplicated_contiguous_phrases']}
        skipgram_patterns = {s['consonantal'] for s in conn['deduplicated_skipgrams']}
        overlap = contiguous_patterns & skipgram_patterns
        if overlap:
            print(f"  ⚠️  FOUND DUPLICATES: {overlap}")
        else:
            print(f"  ✅ No duplicate patterns between contiguous and skipgrams")

        # Issue #1b: Check for gap_word_count=0 in skipgrams
        print(f"\n🔍 ISSUE #1b: Gap_word_count=0 in Skipgrams")
        gap_zero = [s for s in conn['deduplicated_skipgrams'] if s.get('gap_word_count', 0) == 0]
        if gap_zero:
            print(f"  ⚠️  FOUND {len(gap_zero)} skipgrams with gap=0:")
            for s in gap_zero:
                print(f"      - {s['consonantal']} (gap={s['gap_word_count']})")
        else:
            print(f"  ✅ All skipgrams have gap_word_count > 0")

        # Issue #2: Check for problematic roots
        print(f"\n🔍 ISSUE #2: Root Extraction Errors")
        roots = {r['root'] for r in conn['deduplicated_roots']}
        problematic = roots & {'יר', 'מע', 'נא'}
        if problematic:
            print(f"  ⚠️  FOUND PROBLEMATIC ROOTS: {problematic}")
            for r in conn['deduplicated_roots']:
                if r['root'] in problematic:
                    print(f"      - {r['root']} (IDF: {r['idf']:.2f})")
        else:
            print(f"  ✅ No problematic roots (יר, מע, נא) found")

        # Issue #3: Check for divine name patterns
        print(f"\n🔍 ISSUE #3: Divine Name Patterns")
        divine_patterns = {'את יהו', 'יהו לא', 'יהו אלה'}
        found_divine = contiguous_patterns & divine_patterns
        if found_divine:
            print(f"  ⚠️  FOUND DIVINE NAME PATTERNS: {found_divine}")
        else:
            print(f"  ✅ No divine name patterns found (stoplist working)")

        print("\n" + "=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70)

        issues_fixed = []
        issues_remaining = []

        if not overlap and not gap_zero:
            issues_fixed.append("✅ Issue #1: No duplicate/gap=0 patterns")
        else:
            issues_remaining.append("⚠️  Issue #1: Duplicates or gap=0 still present")

        if not problematic:
            issues_fixed.append("✅ Issue #2: Root extraction fixed")
        else:
            issues_remaining.append("⚠️  Issue #2: Root extraction still has errors")

        if not found_divine:
            issues_fixed.append("✅ Issue #3: Divine name patterns filtered")
        else:
            issues_remaining.append("⚠️  Issue #3: Divine name patterns not filtered")

        for issue in issues_fixed:
            print(f"  {issue}")
        for issue in issues_remaining:
            print(f"  {issue}")

        print("=" * 70)
        break
