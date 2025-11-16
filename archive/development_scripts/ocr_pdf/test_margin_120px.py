"""
Test -120px margin on user-specified pages
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from extract_hirsch_commentary_enhanced import process_single_page

# Test pages specified by user
test_pages = [
    (33, "Page 33 (header page)"),
    (34, "Page 34 (continuation)"),
    (35, "Page 35 (continuation)"),
    (260, "Page 260 (user said correct)"),
    (49, "Page 49 (should start with 'moment in the form of misfortunate')"),
    (56, "Page 56 (should start with 'V. 9.')"),
    (267, "Page 267 (should start with 'beast, however, is present only when')"),
]

OUTPUT_DIR = "output/test_margin_120px"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/text", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/metadata", exist_ok=True)

print("="*70)
print("Testing -120px margin on specified pages")
print("="*70)

for page_num, description in test_pages:
    page_name = f"page_{page_num:04d}"
    print(f"\n{description}")
    print("-"*70)

    # Process the page
    success = process_single_page(
        f"data/hirsch_images/{page_name}.png",
        f"{OUTPUT_DIR}/text",
        f"{OUTPUT_DIR}/metadata"
    )

    if success:
        # Show first 3 lines
        print(f"\nFirst 3 lines of {page_name}:")
        with open(f"{OUTPUT_DIR}/text/{page_name}.txt", 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i < 3:
                    # Truncate to avoid Unicode errors in console
                    clean_line = line.strip()[:100]
                    try:
                        print(f"  {i+1}: {clean_line}")
                    except UnicodeEncodeError:
                        print(f"  {i+1}: [Line with Hebrew characters]")

print("\n" + "="*70)
print(f"Output directory: {OUTPUT_DIR}/text/")
print("="*70)
