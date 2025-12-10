#!/usr/bin/env python3
"""Check the corpus output."""
import json

# Read first few lines
with open('data/thematic_corpus/tanakh_chunks.jsonl', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 2:
            break
        data = json.loads(line)
        print(f"\nChunk {i+1}: {data['reference']}")
        print(f"English: {data['english_text'][:200]}...")
        print(f"Hebrew (first 50 chars): {data['hebrew_text'][:50]}...")