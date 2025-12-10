#!/usr/bin/env python3
"""
Test Thematic Parallels Integration

Tests the integration of ThematicParallelsLibrarian into ResearchAssembler.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.research_assembler import ResearchAssembler, ResearchRequest


def test_psalm_23():
    """Test thematic parallels with Psalm 23 (The Lord is my Shepherd)."""
    print("Testing Thematic Parallels Integration with Psalm 23...")
    print("=" * 60)

    # Create a minimal research request
    from src.agents.concordance_librarian import ConcordanceRequest

    request = ResearchRequest(
        psalm_chapter=23,
        lexicon_requests=[],
        concordance_requests=[
            ConcordanceRequest(query="רעה", scope="Psalms", level="consonantal"),
            ConcordanceRequest(query="שלום", scope="Psalms", level="consonantal"),
            ConcordanceRequest(query="ישב", scope="Psalms", level="consonantal")
        ],
        figurative_requests=[]
    )

    # Initialize assembler
    assembler = ResearchAssembler()

    # Assemble research bundle
    bundle = assembler.assemble(request)

    # Check if thematic parallels were fetched
    if bundle.thematic_parallels:
        print(f"✅ Found {len(bundle.thematic_parallels)} thematic parallels")
        print("\nTop 5 parallels:")
        for i, parallel in enumerate(bundle.thematic_parallels[:5], 1):
            print(f"{i}. {parallel.reference} (Similarity: {parallel.similarity:.2f})")
            print(f"   Category: {parallel.book_category}")
            print(f"   Hebrew: {parallel.hebrew_text[:100]}...")
            print()
    else:
        print("❌ No thematic parallels found")

    # Check markdown formatting
    if bundle.thematic_parallels_markdown:
        print("✅ Markdown formatting generated")
        print("\nMarkdown preview:")
        print(bundle.thematic_parallels_markdown[:500])
        print("...\n")
    else:
        print("❌ No markdown formatting generated")

    # Check to_dict includes thematic parallels
    bundle_dict = bundle.to_dict()
    if 'thematic_parallels' in bundle_dict:
        print("✅ to_dict() includes thematic_parallels")
    else:
        print("❌ to_dict() missing thematic_parallels")

    # Check markdown includes thematic parallels
    md = bundle.to_markdown()
    if "Thematic Parallels" in md:
        print("✅ to_markdown() includes Thematic Parallels section")
    else:
        print("❌ to_markdown() missing Thematic Parallels section")

    print("=" * 60)
    print("Test complete!")


if __name__ == "__main__":
    # Ensure UTF-8 for Hebrew output on Windows
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')

    test_psalm_23()