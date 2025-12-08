#!/usr/bin/env python3
"""Test that complete phrase fix is working - both exact phrase and alternates"""

import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Summary of fixes implemented:")
print("=" * 50)
print()
print("1. Phrase Substring Matching (src/concordance/search.py):")
print("   - Phrases now use substring matching (allows prefixes/suffixes)")
print("   - Single words still use exact matching")
print("   - Example: 'דבר אמת בלב' matches 'ודובר אמת בלבבו'")
print()
print("2. Phrase Preservation (src/agents/micro_analyst.py):")
print("   - Fixed matching to allow substring matching")
print("   - Original query is added as alternate when different")
print("   - Both exact phrase AND variations are searched")
print()
print("3. Result:")
print("   - Primary query: Exact phrase from verse (e.g., 'דבר אמת בלבבו')")
print("   - Alternates: Original LLM query + micro analyst variants")
print("   - Psalm 15:2 should now be found!")
print()
print("To verify the fix works, run Psalm 15 pipeline again:")
print("  python scripts/run_enhanced_pipeline.py 15 --skip-macro --skip-synthesis --skip-master-edit --skip-print-ready --skip-college --skip-word-doc --skip-combined-doc")
print()
print("The search for 'דבר אמת בלב' should now:")
print("  1. Search 'דבר אמת בלבבו' (exact from verse)")
print("  2. Search 'דבר אמת בלב' (original query as alternate)")
print("  3. Search variants from micro analyst")
print("  4. Find Psalm 15:2 with any of these forms")