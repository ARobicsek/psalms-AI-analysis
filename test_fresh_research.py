#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate fresh research for Psalm 15 to test if bug is fixed"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.research_assembler import ResearchAssembler, ResearchRequest
from src.data_sources.tanakh_database import TanakhDatabase
import json
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def generate_fresh_research():
    print("=" * 80)
    print("GENERATING FRESH RESEARCH FOR PSALM 15")
    print("=" * 80)

    # Initialize components
    db = TanakhDatabase()
    assembler = ResearchAssembler(db)

    # Load Psalm 15 data
    with open('output/psalm_15/psalm_015_micro_v2.json', 'r', encoding='utf-8') as f:
        micro_data = json.load(f)

    # Create research request
    request = ResearchRequest(
        psalm_chapter=15,
        lexicon_requests=[],  # Will be filled from micro data
        concordance_requests=[],  # Will be filled from micro data
        figurative_requests=[],  # Will be filled from micro data
        verse_count=5  # Psalm 15 has 5 verses
    )

    # Extract requests from micro data
    # Find concordance searches
    if 'scholar_requests' in micro_data:
        for req in micro_data['scholar_requests'].get('concordance', []):
            from src.agents.concordance_librarian import ConcordanceRequest
            concordance_req = ConcordanceRequest(
                query=req['query'],
                scope=req.get('scope', 'auto'),
                level=req.get('level', 'consonantal'),
                include_variations=True
            )
            request.concordance_requests.append(concordance_req)

    # Print the search requests
    print("\nConcordance requests:")
    for i, req in enumerate(request.concordance_requests, 1):
        print(f"  {i}. '{req.query}'")

    # Generate research
    print("\n\nGenerating research bundle...")
    bundle = assembler.assemble(request)

    # Save the research markdown
    output_dir = Path('output/psalm_15')
    output_dir.mkdir(exist_ok=True)

    research_file = output_dir / 'psalm_015_research_v2_fresh.md'
    with open(research_file, 'w', encoding='utf-8') as f:
        f.write(bundle.to_markdown())

    print(f"\n✓ Fresh research saved to: {research_file}")

    # Now check the results for "לא ימוט לעולם"
    print("\n\n" + "=" * 80)
    print("CHECKING RESULTS FOR 'לא ימוט לעולם' SEARCH")
    print("=" * 80)

    content = research_file.read_text(encoding='utf-8')

    # Find the search section
    import re
    pattern = r'### Search 7: לא ימוט לעולם.*?(?=### Search|$)'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        section = match.group(0)
        print("Found search section. Checking results...")

        # Count matches
        psalms_matches = len(re.findall(r'\*\*Psalms \d+:\d+', section))
        isaiah_matches = len(re.findall(r'\*\*Isaiah \d+:\d+', section))

        print(f"\n  Psalms matches: {psalms_matches}")
        print(f"  Isaiah matches: {isaiah_matches}")

        # Check for partial matches
        partial_matches = re.findall(r'Matched: \*[^*]*(?:לא ימוט|בל ימוט)[^*]*\*', section)
        full_matches = re.findall(r'Matched: \*לא ימוט לעולם\*', section)

        print(f"\n  Full phrase matches (3 words): {len(full_matches)}")
        print(f"  Partial matches (2 words): {len(partial_matches)}")

        if partial_matches:
            print("\n  ❌ PARTIAL MATCHES FOUND (BUG PRESENT):")
            for match in partial_matches[:5]:
                print(f"    {match}")
        else:
            print("\n  ✓ No partial matches - bug is fixed!")
    else:
        print("Search section not found!")

if __name__ == "__main__":
    generate_fresh_research()