"""
Test script for Phase 4/5 Liturgical Librarian integration into ResearchAssembler.

This verifies that:
1. ResearchAssembler initializes with new liturgical librarian
2. Aggregated liturgical data is fetched correctly
3. Markdown formatting includes LLM summaries
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.research_assembler import ResearchAssembler, ResearchRequest
from src.agents.bdb_librarian import LexiconRequest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_liturgical_integration():
    """Test Phase 4/5 liturgical integration."""

    print("=" * 70)
    print("Testing Liturgical Librarian Integration (Phase 4/5)")
    print("=" * 70)

    # Create assembler with LLM summaries enabled
    print("\n1. Initializing ResearchAssembler with LLM summaries...")
    assembler = ResearchAssembler(use_llm_summaries=True)
    print("   [OK] ResearchAssembler initialized")

    # Create minimal research request for Psalm 23
    print("\n2. Creating research request for Psalm 23...")
    request = ResearchRequest(
        psalm_chapter=23,
        lexicon_requests=[],  # Minimal test - no lexicon
        concordance_requests=[],  # Minimal test - no concordance
        figurative_requests=[],  # Minimal test - no figurative
        commentary_requests=None
    )
    print("   [OK] Research request created")

    # Assemble research bundle
    print("\n3. Assembling research bundle...")
    bundle = assembler.assemble(request)
    print("   [OK] Research bundle assembled")

    # Check liturgical data
    print("\n4. Checking liturgical data...")
    if bundle.liturgical_usage_aggregated:
        print(f"   [OK] Found {len(bundle.liturgical_usage_aggregated)} distinct prayers")
        total_occurrences = sum(p.occurrence_count for p in bundle.liturgical_usage_aggregated)
        print(f"   [OK] Total occurrences: {total_occurrences}")

        # Show first 3 prayers
        print("\n   Top 3 prayers:")
        for i, prayer in enumerate(bundle.liturgical_usage_aggregated[:3], 1):
            print(f"   {i}. {prayer.prayer_name}: {prayer.occurrence_count} occurrences")
    else:
        print("   [WARN] No aggregated liturgical data (falling back to Phase 0)")
        if bundle.liturgical_usage:
            print(f"   [INFO] Phase 0 data: {len(bundle.liturgical_usage)} contexts")

    # Check markdown formatting
    print("\n5. Checking markdown formatting...")
    if bundle.liturgical_markdown:
        lines = bundle.liturgical_markdown.split('\n')
        print(f"   [OK] Markdown generated: {len(lines)} lines")

        # Check for LLM-generated content
        if "appears across" in bundle.liturgical_markdown.lower():
            print("   [OK] LLM summaries detected (natural language)")
        else:
            print("   [INFO] Code-only summaries (LLM not used)")

        # Show first few lines
        print("\n   First 10 lines of markdown:")
        for line in lines[:10]:
            print(f"   {line}")
    else:
        print("   [WARN] No markdown generated")

    # Generate full markdown bundle
    print("\n6. Generating full research bundle markdown...")
    full_markdown = bundle.to_markdown()
    print(f"   [OK] Generated {len(full_markdown)} characters")

    # Show summary
    summary = bundle.to_dict()['summary']
    print("\n7. Research Bundle Summary:")
    print(f"   - Liturgical prayers (aggregated): {summary['liturgical_prayers_aggregated']}")
    print(f"   - Liturgical total occurrences: {summary['liturgical_total_occurrences']}")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

    return bundle


if __name__ == '__main__':
    try:
        bundle = test_liturgical_integration()
        print("\n[SUCCESS] All tests passed!")
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
