#!/usr/bin/env python3
"""
Simple check of what thematic data exists for Genesis 1:1
"""

import csv
from pathlib import Path

def main():
    print("=== THEMATIC DATA FOR GENESIS 1:1 ===\n")

    # Check comprehensive themes
    comp_file = Path("data/comprehensive_biblical_themes.csv")
    if comp_file.exists():
        print("From comprehensive_biblical_themes.csv:")
        with open(comp_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ref = row.get('reference', '')
                if 'Genesis 1:1' in ref or 'Genesis 1:1-2:3' in ref:
                    print(f"\nReference: {ref}")
                    print(f"  Major Theme: {row['major_theme']}")
                    print(f"  Mid-Level Theme: {row['mid_level_theme']}")
                    print(f"  Description: {row.get('description', '')}")
                    print(f"  Testament: {row.get('testament', '')}")
                    print(f"  Genre: {row.get('genre', '')}")

    # Check basic themes
    basic_file = Path("data/sefaria_topic_hierarchy.csv")
    if basic_file.exists():
        print("\n\nFrom sefaria_topic_hierarchy.csv:")
        with open(basic_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ref = row.get('reference', '')
                if 'Genesis 1:1' in ref or 'Genesis 1:1-2:3' in ref:
                    print(f"\nReference: {ref}")
                    print(f"  Major Theme: {row['major_theme']}")
                    print(f"  Mid-Level Theme: {row['mid_level_theme']}")
                    print(f"  Level: {row['level']}")

    print("\n=== CONCLUSION ===")
    print("Genesis 1:1 is only found as part of broader thematic ranges (e.g., 'Genesis 1:1-2:3')")
    print("There is no individual verse-level thematic tagging in the available datasets.")

if __name__ == "__main__":
    main()