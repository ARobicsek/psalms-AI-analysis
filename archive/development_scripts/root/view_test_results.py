"""
Display test canonicalization results in a readable format.
"""

import json
from pathlib import Path

OUTPUT_FILE = "output/test_canonical_sample.jsonl"

def display_prayer(prayer_data, index):
    """Display a single canonicalized prayer in a readable format."""

    print(f"\n{'=' * 80}")
    print(f"PRAYER #{index}: {prayer_data.get('canonical_prayer_name', 'N/A')}")
    print(f"{'=' * 80}")

    # Original metadata
    print(f"\nORIGINAL METADATA:")
    print(f"   Prayer ID: {prayer_data.get('original_prayer_id', 'N/A')}")
    print(f"   Source Corpus: {prayer_data.get('source_corpus', 'N/A')}")

    # Hierarchical categorization
    print(f"\nHIERARCHICAL CATEGORIZATION:")
    print(f"   L1 (Occasion):   {prayer_data.get('L1_Occasion', 'N/A')}")
    print(f"   L2 (Service):    {prayer_data.get('L2_Service', 'N/A')}")
    print(f"   L3 (Signpost):   {prayer_data.get('L3_Signpost', 'N/A')}")
    print(f"   L4 (SubSection): {prayer_data.get('L4_SubSection', 'N/A')}")

    # Prayer details
    print(f"\nPRAYER DETAILS:")
    print(f"   Nusach: {prayer_data.get('nusach', 'N/A')}")
    print(f"   Canonical Name: {prayer_data.get('canonical_prayer_name', 'N/A')}")
    print(f"   Usage Type: {prayer_data.get('usage_type', 'N/A')}")

    # Location description
    print(f"\nLOCATION DESCRIPTION:")
    desc = prayer_data.get('relative_location_description', 'N/A')
    # Wrap long descriptions
    if len(desc) > 75:
        words = desc.split()
        lines = []
        current_line = "   "
        for word in words:
            if len(current_line) + len(word) + 1 <= 78:
                current_line += word + " "
            else:
                lines.append(current_line)
                current_line = "   " + word + " "
        lines.append(current_line)
        print("\n".join(lines))
    else:
        print(f"   {desc}")

    # Hebrew text (truncated)
    hebrew_text = prayer_data.get('hebrew_text', '')
    if len(hebrew_text) > 100:
        print(f"\nHEBREW TEXT (truncated):")
        print(f"   {hebrew_text[:100]}...")
    else:
        print(f"\nHEBREW TEXT:")
        print(f"   {hebrew_text}")


def main():
    """Display all test results."""

    if not Path(OUTPUT_FILE).exists():
        print(f"Error: {OUTPUT_FILE} not found. Run test_liturgical_canonicalizer.py first.")
        return

    print("\n" + "=" * 80)
    print("LITURGICAL CANONICALIZATION TEST RESULTS")
    print("Model: gemini-2.5-pro")
    print("=" * 80)

    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        prayers = [json.loads(line) for line in f if line.strip()]

    print(f"\nTotal prayers processed: {len(prayers)}")

    for i, prayer in enumerate(prayers, 1):
        display_prayer(prayer, i)

    print(f"\n{'=' * 80}")
    print("END OF RESULTS")
    print("=" * 80)

    # Summary comparison
    print("\nHIERARCHICAL CONSISTENCY CHECK:")
    print(f"   All prayers have L3_Signpost: {all('L3_Signpost' in p for p in prayers)}")
    print(f"   All prayers have canonical_name: {all('canonical_prayer_name' in p for p in prayers)}")
    print(f"   All prayers have location_description: {all('relative_location_description' in p for p in prayers)}")

    # Show L3 categories used
    l3_categories = set(p.get('L3_Signpost', 'N/A') for p in prayers)
    print(f"\n   L3 Signpost categories used:")
    for cat in sorted(l3_categories):
        print(f"      - {cat}")

    print()


if __name__ == "__main__":
    main()
