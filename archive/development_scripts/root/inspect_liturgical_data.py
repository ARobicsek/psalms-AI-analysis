"""
Inspect Liturgical Data Structure (No LLM calls)

This script shows what data the liturgical librarian collects
for specific psalms WITHOUT making LLM API calls.

Use this to inspect the raw match data and understand what would
be sent to the LLM for summarization.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.liturgical_librarian import LiturgicalLibrarian


def inspect_psalm_data(psalm_number: int):
    """Inspect liturgical data for a psalm without LLM calls."""

    print("\n" + "=" * 80)
    print(f"INSPECTING DATA FOR PSALM {psalm_number}")
    print("=" * 80)

    # Initialize without LLM to avoid API calls
    librarian = LiturgicalLibrarian(
        use_llm_summaries=False,  # No LLM calls
        verbose=False
    )

    # Get raw matches
    print(f"\nFetching raw matches for Psalm {psalm_number}...")
    raw_matches = librarian._get_raw_matches(
        psalm_chapter=psalm_number,
        psalm_verses=None,
        min_confidence=0.75
    )

    print(f"\n[OK] Found {len(raw_matches)} raw matches")

    if not raw_matches:
        print(f"No liturgical usage found for Psalm {psalm_number}.")
        return

    # Show match type breakdown
    match_types = {}
    for m in raw_matches:
        match_types[m.match_type] = match_types.get(m.match_type, 0) + 1

    print("\nMatch Type Breakdown:")
    for match_type, count in sorted(match_types.items()):
        print(f"  {match_type}: {count}")

    # Show is_unique distribution for phrase_match
    phrase_matches = [m for m in raw_matches if m.match_type == 'phrase_match']
    if phrase_matches:
        unique_count = sum(1 for m in phrase_matches if m.is_unique == 1)
        print(f"\nPhrase Matches: {len(phrase_matches)} total")
        print(f"  Unique (is_unique=1): {unique_count}")
        print(f"  Non-unique (is_unique=0): {len(phrase_matches) - unique_count}")
        print(f"  Note: Non-unique phrase matches are filtered out by SQL query")

    # Show canonical field coverage
    canonical_populated = sum(1 for m in raw_matches if m.canonical_prayer_name or m.canonical_L1_Occasion)
    print(f"\nCanonical Fields Populated: {canonical_populated}/{len(raw_matches)} matches")

    # Show sample matches with full details
    print("\n" + "=" * 80)
    print("SAMPLE MATCHES (first 5 with full details)")
    print("=" * 80)

    for i, match in enumerate(raw_matches[:5], 1):
        print(f"\n--- Match {i} ---")
        print(f"Index ID: {match.index_id}")
        print(f"Psalm Verse Range: {match.psalm_verse_start}-{match.psalm_verse_end}")
        print(f"Psalm Phrase (Hebrew): {match.psalm_phrase_hebrew}")
        print(f"Match Type: {match.match_type}")
        print(f"Confidence: {match.confidence:.2f}")
        print(f"is_unique: {match.is_unique}")
        print(f"\nPrayer Metadata:")
        print(f"  Prayer ID: {match.prayer_id}")
        print(f"  Prayer Name (Sefaria): {match.prayer_name or 'N/A'}")
        print(f"  Canonical Prayer Name: {match.canonical_prayer_name or 'N/A'}")
        print(f"  L1 Occasion: {match.canonical_L1_Occasion or 'N/A'}")
        print(f"  L2 Service: {match.canonical_L2_Service or 'N/A'}")
        print(f"  L3 Signpost: {match.canonical_L3_Signpost or 'N/A'}")
        print(f"  L4 SubSection: {match.canonical_L4_SubSection or 'N/A'}")
        print(f"\nLocation Description:")
        if match.canonical_location_description:
            desc = match.canonical_location_description
            print(f"  {desc[:300]}{'...' if len(desc) > 300 else ''}")
        else:
            print(f"  N/A")
        print(f"\nLiturgy Context (excerpt):")
        print(f"  {match.liturgy_context[:200]}...")

    # Show what would be sent to LLM
    print("\n" + "=" * 80)
    print("WHAT WOULD BE SENT TO LLM FOR SUMMARIZATION")
    print("=" * 80)

    # Group by phrase (simulating what find_liturgical_usage_by_phrase does)
    from collections import defaultdict

    grouped = defaultdict(list)
    for match in raw_matches:
        if match.match_type != 'phrase_match':
            continue  # Skip non-phrase matches for this example
        key = match.psalm_phrase_hebrew.strip()
        grouped[key].append(match)

    print(f"\nGrouped into {len(grouped)} unique phrases")

    # Show first 3 phrase groups
    for i, (phrase_key, matches) in enumerate(list(grouped.items())[:3], 1):
        print(f"\n--- Phrase Group {i} ---")
        print(f"Phrase: {phrase_key}")
        print(f"Occurrences: {len(matches)}")

        # Extract metadata that would be sent to LLM
        occasions = sorted(set(m.canonical_L1_Occasion for m in matches if m.canonical_L1_Occasion))
        services = sorted(set(m.canonical_L2_Service for m in matches if m.canonical_L2_Service))
        signposts = sorted(set(m.canonical_L3_Signpost for m in matches if m.canonical_L3_Signpost))

        print(f"\nMetadata for LLM:")
        print(f"  L1 Occasions: {', '.join(occasions) if occasions else 'N/A'}")
        print(f"  L2 Services: {', '.join(services) if services else 'N/A'}")
        print(f"  L3 Signposts: {', '.join(signposts) if signposts else 'N/A'}")

        print(f"\nDetailed Match Information (first 2 matches):")
        for j, match in enumerate(matches[:2], 1):
            print(f"  Match {j}:")
            print(f"    Canonical Prayer Name: {match.canonical_prayer_name or 'N/A'}")
            print(f"    Location Description: {match.canonical_location_description[:150] if match.canonical_location_description else 'N/A'}...")
            print(f"    L1 Occasion: {match.canonical_L1_Occasion or 'N/A'}")
            print(f"    L2 Service: {match.canonical_L2_Service or 'N/A'}")
            print(f"    L3 Signpost: {match.canonical_L3_Signpost or 'N/A'}")
            print(f"    L4 SubSection: {match.canonical_L4_SubSection or 'N/A'}")
            print(f"    Liturgy Context: {match.liturgy_context[:100]}...")


def main():
    """Inspect data for Psalms 1, 2, 20, and 145."""

    # Configure UTF-8 output for Windows console
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    test_psalms = [1, 2, 20, 145]

    print("\n" + "=" * 80)
    print("LITURGICAL DATA INSPECTION (No LLM calls)")
    print("=" * 80)
    print("\nThis script shows what data is collected and what would be sent to the LLM")
    print("for summarization, WITHOUT actually calling the LLM API.")
    print("\n" + "=" * 80)

    for psalm_num in test_psalms:
        try:
            inspect_psalm_data(psalm_num)
        except Exception as e:
            print(f"\n[ERROR] Failed to inspect Psalm {psalm_num}: {e}")
            import traceback
            traceback.print_exc()

        print("\n\n")  # Space between psalms

    print("=" * 80)
    print("INSPECTION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
