"""
Test MicroAnalyst Agent (Pass 2)

Tests the two-stage micro analysis process:
1. Research request generation
2. Verse-by-verse analysis with research integration

Test Psalm: Psalm 29 (already has MacroAnalysis from Pass 1)

Author: Claude (Anthropic)
Date: 2025 (Phase 3b)
"""

import sys
import os
from pathlib import Path

# Ensure UTF-8 for Hebrew/Greek output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.micro_analyst import MicroAnalyst
from src.schemas.analysis_schemas import MacroAnalysis, load_macro_analysis, save_analysis


def test_micro_analyst_psalm_29():
    """Test MicroAnalyst with Psalm 29 (full end-to-end)."""

    print("=" * 80)
    print("TEST: MicroAnalyst Agent - Psalm 29")
    print("=" * 80)

    # Load MacroAnalysis from Phase 3a
    macro_path = Path("output/phase3_test/psalm_029_macro.json")
    if not macro_path.exists():
        print(f"ERROR: MacroAnalysis not found at {macro_path}")
        print("Please run test_macro_analyst.py first to generate Pass 1 output.")
        return False

    print(f"\n[1] Loading MacroAnalysis from {macro_path}...")
    macro_analysis = load_macro_analysis(str(macro_path))

    print(f"✓ Loaded MacroAnalysis for Psalm {macro_analysis.psalm_number}")
    print(f"  Thesis: {macro_analysis.thesis_statement[:100]}...")
    print(f"  Structural divisions: {len(macro_analysis.structural_outline)}")
    print(f"  Poetic devices: {len(macro_analysis.poetic_devices)}")
    print(f"  Research questions: {len(macro_analysis.research_questions)}")

    # Initialize MicroAnalyst
    print(f"\n[2] Initializing MicroAnalyst agent...")
    analyst = MicroAnalyst(
        db_path="data/tanakh.db",
        docs_dir="docs"
    )
    print("✓ MicroAnalyst initialized")

    # Perform two-stage analysis
    print(f"\n[3] Performing two-stage micro analysis...")
    print("    Stage 1: Generating research requests...")
    print("    Stage 2: Assembling research bundle...")
    print("    Stage 3: Analyzing verses with research...")
    print()
    print("    (This will take 2-3 minutes with API calls and research assembly)")
    print()

    try:
        micro_analysis, research_bundle = analyst.analyze_psalm(29, macro_analysis)

        print("✓ Micro analysis complete!")

        # Display results summary
        print(f"\n[4] Analysis Results:")
        print(f"  Verses analyzed: {len(micro_analysis.verse_commentaries)}")
        print(f"  Thematic threads: {len(micro_analysis.thematic_threads)}")

        # Research bundle summary
        summary = research_bundle.to_dict()['summary']
        print(f"\n  Research Bundle:")
        print(f"    Lexicon entries: {summary['lexicon_entries']}")
        print(f"    Concordance searches: {summary['concordance_searches']}")
        print(f"    Concordance results: {summary['concordance_results']}")
        print(f"    Figurative instances: {summary['figurative_instances']}")
        print(f"    Commentary entries: {summary['commentary_entries']}")

        # Show sample verse commentary
        if micro_analysis.verse_commentaries:
            v1 = micro_analysis.verse_commentaries[0]
            print(f"\n  Sample: Verse {v1.verse_number} Commentary")
            print(f"    Length: {len(v1.commentary)} characters")
            print(f"    Lexical insights: {len(v1.lexical_insights)}")
            print(f"    Figurative analysis: {len(v1.figurative_analysis)}")
            print(f"    Thesis connection: {'Yes' if v1.thesis_connection else 'No'}")

            print(f"\n    Commentary excerpt:")
            excerpt = v1.commentary[:300] + "..." if len(v1.commentary) > 300 else v1.commentary
            print(f"    \"{excerpt}\"")

        # Show thematic threads
        if micro_analysis.thematic_threads:
            print(f"\n  Thematic Threads:")
            for i, thread in enumerate(micro_analysis.thematic_threads[:3], 1):
                print(f"    {i}. {thread}")

        # Save outputs
        print(f"\n[5] Saving outputs...")
        output_dir = Path("output/phase3_test")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save MicroAnalysis (JSON + Markdown)
        micro_json = output_dir / "psalm_029_micro.json"
        micro_md = output_dir / "psalm_029_micro.md"

        save_analysis(micro_analysis, str(micro_json), format="json")
        save_analysis(micro_analysis, str(micro_md), format="markdown")

        # Save Research Bundle (Markdown)
        bundle_md = output_dir / "psalm_029_research.md"
        with open(bundle_md, 'w', encoding='utf-8') as f:
            f.write(research_bundle.to_markdown())

        print(f"✓ Outputs saved:")
        print(f"    {micro_json}")
        print(f"    {micro_md}")
        print(f"    {bundle_md}")

        # Validation checks
        print(f"\n[6] Validation:")

        checks = []

        # Check 1: All verses analyzed
        psalm_verse_count = 11  # Psalm 29 has 11 verses
        all_verses = len(micro_analysis.verse_commentaries) == psalm_verse_count
        checks.append(("All verses analyzed", all_verses))

        # Check 2: Comprehensive lexicon requests (2-4 per verse = 22-44 expected)
        lexicon_count = summary['lexicon_entries']
        comprehensive_lexicon = 20 <= lexicon_count <= 50
        checks.append((f"Comprehensive lexicon requests ({lexicon_count})", comprehensive_lexicon))

        # Check 3: Research integrated in commentaries
        first_verse = micro_analysis.verse_commentaries[0]
        research_integrated = (
            len(first_verse.lexical_insights) > 0 and
            len(first_verse.commentary) > 200
        )
        checks.append(("Research integrated in commentaries", research_integrated))

        # Check 4: Thesis connections present
        thesis_connections = all(
            vc.thesis_connection for vc in micro_analysis.verse_commentaries
        )
        checks.append(("All verses have thesis connections", thesis_connections))

        # Check 5: Thematic threads identified
        has_threads = len(micro_analysis.thematic_threads) >= 3
        checks.append(("Thematic threads identified", has_threads))

        # Display validation results
        all_passed = True
        for check_name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {check_name}")
            if not passed:
                all_passed = False

        if all_passed:
            print(f"\n{'=' * 80}")
            print("✓ ALL TESTS PASSED - MicroAnalyst working correctly!")
            print(f"{'=' * 80}")
            return True
        else:
            print(f"\n{'=' * 80}")
            print("✗ SOME VALIDATION CHECKS FAILED")
            print(f"{'=' * 80}")
            return False

    except Exception as e:
        print(f"\n✗ ERROR during micro analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\nMICROANALYST AGENT TESTS")
    print("Testing Pass 2: Verse-by-Verse Analysis with Research Integration")
    print()

    success = test_micro_analyst_psalm_29()

    if success:
        print("\n" + "=" * 80)
        print("PHASE 3b COMPLETE: MicroAnalyst + LXX Integration")
        print("=" * 80)
        print()
        print("Next steps:")
        print("1. Review output/phase3_test/psalm_029_micro.md")
        print("2. Verify verse commentaries integrate research effectively")
        print("3. Check that thesis connections are clear")
        print("4. Proceed to Phase 3c: SynthesisWriter agent")
        return 0
    else:
        print("\n" + "=" * 80)
        print("TESTS FAILED - See errors above")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
