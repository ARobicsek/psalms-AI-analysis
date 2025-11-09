"""
Test -50px margin on problem pages
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from extract_hirsch_commentary_enhanced import process_single_page

# Test problem pages
test_pages = [
    ("page_0049", "moment in the form of misfortunate"),
    ("page_0056", "V. 9."),
    ("page_0267", "beast, however, is present only when"),
]

OUTPUT_DIR = "output/test_margin_50px"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/text", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/metadata", exist_ok=True)

print("="*70)
print("Testing -50px margin on problem pages")
print("="*70)

for page, expected_start in test_pages:
    print(f"\n{page}:")
    print(f"  Expected start: {expected_start}")

    # Process the page
    success = process_single_page(
        f"data/hirsch_images/{page}.png",
        f"{OUTPUT_DIR}/text",
        f"{OUTPUT_DIR}/metadata"
    )

    if success:
        # Read the result
        with open(f"{OUTPUT_DIR}/text/{page}.txt", 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            print(f"  Got: {first_line[:70]}...")

            # Check if expected text is in first line
            if expected_start.lower() in first_line.lower():
                print(f"  ✓ CORRECT!")
            else:
                print(f"  ✗ Still wrong")

print("\n" + "="*70)
