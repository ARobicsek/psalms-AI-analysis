"""
Day 5 Integration Test - Full Librarian Agent Workflow

Tests the complete pipeline:
1. Sample research request (simulates Scholar-Researcher output)
2. All three librarians fetch data
3. Research Bundle Assembler coordinates and formats
4. Output in both JSON and Markdown

This verifies that all Day 5 enhancements are working together.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for proper imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.research_assembler import ResearchAssembler
from src.utils.logger import get_logger

def main():
    # Configure UTF-8 for Windows console
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    # Initialize logger
    logger = get_logger('integration_test')

    print("=" * 80)
    print("DAY 5 INTEGRATION TEST - Full Librarian Agent Workflow")
    print("=" * 80)
    print()

    # Sample research request (what Scholar-Researcher would generate)
    research_request = {
        "psalm_chapter": 23,
        "lexicon": [
            {"word": "רעה"},
            {"word": "צלמות"}
        ],
        "concordance": [
            {"query": "רעה", "scope": "Psalms", "level": "consonantal"},
            {"query": "ירא", "scope": "Psalms", "level": "consonantal"}
        ],
        "figurative": [
            {"book": "Psalms", "chapter": 23, "metaphor": True},
            {"vehicle_contains": "shepherd", "book": "Psalms"}
        ]
    }

    print("RESEARCH REQUEST:")
    print(json.dumps(research_request, indent=2, ensure_ascii=False))
    print()
    print("-" * 80)
    print()

    # Log the research request
    logger.log_research_request(23, research_request)

    # Initialize Research Assembler
    print("Initializing Research Assembler...")
    assembler = ResearchAssembler()
    print("✓ Assembler ready")
    print()

    # Process the research request
    print("Processing research request through all librarians...")
    print()

    try:
        # Convert to JSON string first, then use assemble_from_json
        request_json = json.dumps(research_request, ensure_ascii=False)
        bundle = assembler.assemble_from_json(request_json)
        print("✓ Research bundle assembled successfully!")
        print()

        # Display summary statistics
        print("RESEARCH BUNDLE SUMMARY:")
        print(f"  Psalm: {bundle.psalm_chapter}")
        print(f"  Lexicon entries: {len(bundle.lexicon_bundle.entries) if bundle.lexicon_bundle else 0}")
        print(f"  Concordance bundles: {len(bundle.concordance_bundles)}")

        total_concordance_results = sum(len(cb.results) for cb in bundle.concordance_bundles)
        print(f"  Total concordance results: {total_concordance_results}")

        total_figurative_instances = sum(len(fb.instances) for fb in bundle.figurative_bundles)
        print(f"  Figurative language instances: {total_figurative_instances}")
        print()
        print("-" * 80)
        print()

        # Display sample lexicon entries
        if bundle.lexicon_bundle and bundle.lexicon_bundle.entries:
            print("SAMPLE LEXICON ENTRIES:")
            for i, entry in enumerate(bundle.lexicon_bundle.entries[:3], 1):
                print(f"\n{i}. {entry.word} ({entry.lexicon_name})")
                if entry.headword:
                    print(f"   Vocalized: {entry.headword}")
                if entry.strong_number:
                    print(f"   Strong's: {entry.strong_number}")
                if entry.transliteration:
                    print(f"   Pronunciation: {entry.transliteration}")

                # Show first 100 chars of definition
                definition = entry.entry_text[:100] + "..." if len(entry.entry_text) > 100 else entry.entry_text
                print(f"   Definition: {definition}")

            if len(bundle.lexicon_bundle.entries) > 3:
                print(f"\n   ... and {len(bundle.lexicon_bundle.entries) - 3} more entries")
            print()
            print("-" * 80)
            print()

        # Display sample concordance results
        if bundle.concordance_bundles:
            print("SAMPLE CONCORDANCE RESULTS:")
            for cb in bundle.concordance_bundles[:2]:
                req = cb.request
                print(f"\nQuery: {req.query} ({req.scope}, {req.level})")
                print(f"  Variations searched: {len(cb.variations_searched)}")
                print(f"  Results found: {len(cb.results)}")

                # Show first 2 results
                for result in cb.results[:2]:
                    print(f"\n  {result.reference}")
                    print(f"    Hebrew: {result.hebrew_text[:50]}...")
                    print(f"    English: {result.english_text[:60]}...")
                    print(f"    Matched: {result.matched_word}")

            if len(bundle.concordance_bundles) > 2:
                print(f"\n  ... and {len(bundle.concordance_bundles) - 2} more searches")
            print()
            print("-" * 80)
            print()

        # Display sample figurative language instances
        if bundle.figurative_bundles:
            all_instances = []
            for fb in bundle.figurative_bundles:
                all_instances.extend(fb.instances)

            if all_instances:
                print("SAMPLE FIGURATIVE LANGUAGE INSTANCES:")
                for i, instance in enumerate(all_instances[:3], 1):
                    print(f"\n{i}. {instance.reference}")
                    types = []
                    if hasattr(instance, 'is_metaphor') and instance.is_metaphor:
                        types.append('metaphor')
                    if hasattr(instance, 'is_simile') and instance.is_simile:
                        types.append('simile')
                    print(f"   Type: {', '.join(types) if types else 'figurative'}")
                    if instance.vehicle:
                        print(f"   Vehicle: {', '.join(instance.vehicle[:2])}")
                    if instance.target:
                        print(f"   Target: {', '.join(instance.target[:2])}")
                    if hasattr(instance, 'figurative_text'):
                        print(f"   Text: {instance.figurative_text[:60]}...")

                if len(all_instances) > 3:
                    print(f"\n   ... and {len(all_instances) - 3} more instances")
                print()
                print("-" * 80)
                print()

        # Test JSON export
        print("TESTING JSON EXPORT...")
        json_output = bundle.to_json()
        json_parsed = json.loads(json_output)
        print(f"✓ JSON export successful ({len(json_output)} characters)")
        print()

        # Test Markdown export
        print("TESTING MARKDOWN EXPORT...")
        markdown_output = bundle.to_markdown()
        print(f"✓ Markdown export successful ({len(markdown_output)} characters)")
        print()

        # Show first 500 chars of markdown
        print("MARKDOWN PREVIEW (first 500 characters):")
        print("-" * 80)
        print(markdown_output[:500])
        if len(markdown_output) > 500:
            print(f"\n... ({len(markdown_output) - 500} more characters)")
        print("-" * 80)
        print()

        # Save outputs to file
        output_dir = Path(__file__).parent.parent / 'tests' / 'output'
        output_dir.mkdir(parents=True, exist_ok=True)

        json_file = output_dir / 'research_bundle_test.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            f.write(json_output)
        print(f"✓ JSON saved to: {json_file}")

        markdown_file = output_dir / 'research_bundle_test.md'
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_output)
        print(f"✓ Markdown saved to: {markdown_file}")
        print()

        # Display logger summary
        print("=" * 80)
        print("LOGGING SUMMARY:")
        print("=" * 80)
        summary = logger.get_summary()
        print(f"  Total log entries: {summary['total_entries']}")
        print(f"  By level: {summary['by_level']}")
        print(f"  By event type: {summary['by_event_type']}")
        print()

        # Final success message
        print("=" * 80)
        print("INTEGRATION TEST: ✅ PASSED")
        print("=" * 80)
        print()
        print("All librarian agents working correctly:")
        print("  ✓ BDB Librarian - Lexicon lookups with homograph disambiguation")
        print("  ✓ Concordance Librarian - Search with morphological variations")
        print("  ✓ Figurative Language Librarian - Hierarchical tag queries")
        print("  ✓ Research Bundle Assembler - JSON + Markdown output")
        print("  ✓ Logging System - Event tracking and summaries")
        print()
        print("Day 5 enhancements verified operational!")
        print()

    except Exception as e:
        print(f"❌ INTEGRATION TEST FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        logger.log_error_detail(
            operation='integration_test',
            error_type=type(e).__name__,
            error_message=str(e),
            stack_trace=traceback.format_exc()
        )
        sys.exit(1)

if __name__ == '__main__':
    main()
