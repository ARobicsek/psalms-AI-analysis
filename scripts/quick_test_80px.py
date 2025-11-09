"""Quick test of -80px margin"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from extract_hirsch_commentary_enhanced import process_single_page
import os

# Test page 49
os.makedirs("output/quick_test", exist_ok=True)
os.makedirs("output/quick_test/text", exist_ok=True)
os.makedirs("output/quick_test/metadata", exist_ok=True)

print("Testing page 49 with -80px margin...")
process_single_page(
    "data/hirsch_images/page_0049.png",
    "output/quick_test/text",
    "output/quick_test/metadata"
)

print("\nFirst 5 lines:")
with open("output/quick_test/text/page_0049.txt", encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i < 5:
            print(f"{i+1}: {line.strip()[:80]}")
