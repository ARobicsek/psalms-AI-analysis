#!/usr/bin/env python3
"""Check the final cleaning result."""
import json

# Check a specific chunk
with open('data/thematic_corpus/tanakh_chunks.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        if data['chunk_id'] == 'genesis_003_019_003_023':
            print(f"Reference: {data['reference']}")
            print(f"English: {data['english_text'][:400]}...")
            print(f"\nExpected cleaning quality:")
            print("- Most footnotes removed")
            print("- Text largely preserved")
            print("- Some minor artifacts may remain")
            break