"""
Test -150px margin on problematic pages 56 and 267
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from extract_hirsch_commentary_enhanced import process_single_page

test_pages = [
    (56, "V. 9."),
    (267, "beast, however, is present only when"),
]

OUTPUT_DIR = "output/test_150px"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/text", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/metadata", exist_ok=True)

print("="*70)
print("Testing -150px margin on pages 56 and 267")
print("="*70)

for page_num, expected_start in test_pages:
    page_name = f"page_{page_num:04d}"
    print(f"\nPage {page_num} (should start with: {expected_start})")
    print("-"*70)

    # Process the page
    process_single_page(
        f"data/hirsch_images/{page_name}.png",
        f"{OUTPUT_DIR}/text",
        f"{OUTPUT_DIR}/metadata"
    )

    # Show first 5 lines
    print(f"\nFirst 5 lines:")
    with open(f"{OUTPUT_DIR}/text/{page_name}.txt", 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i < 5:
                clean_line = line.strip()[:90]
                try:
                    print(f"  {i+1}: {clean_line}")
                except UnicodeEncodeError:
                    print(f"  {i+1}: [Hebrew text]")

print("\n" + "="*70)
