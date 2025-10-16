"""
Demo: Librarian Agents in Action - Psalm 27:1

Shows what each librarian returns for a real research request.

Verse: לְדָוִד ׀ יְהֹוָה ׀ אוֹרִי וְיִשְׁעִי מִמִּי אִירָא יְהֹוָה מָעוֹז־חַיַּי מִמִּי אֶפְחָד׃
Translation: "Of David. The LORD is my light and my salvation; whom shall I fear?
             The LORD is the stronghold of my life; of whom shall I be afraid?"

Scholar's Research Request:
- Lexicon: אורי (my light), וישעי (my salvation), איראֿ (I fear), מעוז־חיי (stronghold of my life), אפחד (I be afraid)
- Concordance: Search for these words/phrases in Psalms
- Figurative: "stronghold" metaphor and any other figurative language in Psalm 27:1
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.bdb_librarian import BDBLibrarian
from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest
from src.agents.figurative_librarian import FigurativeLibrarian, FigurativeRequest
from src.agents.research_assembler import ResearchAssembler

def print_separator(title):
    """Print a nice separator with title."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def main():
    # Configure UTF-8 for Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print_separator("PSALM 27:1 - LIBRARIAN AGENTS DEMO")

    print("VERSE (Hebrew):")
    print("לְדָוִד ׀ יְהֹוָה ׀ אוֹרִי וְיִשְׁעִי מִמִּי אִירָא יְהֹוָה מָעוֹז־חַיַּי מִמִּי אֶפְחָד׃")
    print()
    print("VERSE (English):")
    print("Of David. The LORD is my light and my salvation; whom shall I fear?")
    print("The LORD is the stronghold of my life; of whom shall I be afraid?")
    print()

    print("SCHOLAR'S RESEARCH REQUEST:")
    print("  Words to investigate: אורי, וישעי, איראֿ, מעוז־חיי, אפחד")
    print("  Figurative interest: 'stronghold' metaphor")

    # ========================================================================
    # LIBRARIAN 1: BDB LEXICON LOOKUPS
    # ========================================================================

    print_separator("LIBRARIAN 1: BDB LEXICON (Hebrew Definitions)")

    bdb = BDBLibrarian()
    words_to_lookup = ["אור", "ישע", "ירא", "מעוז", "פחד"]

    for word in words_to_lookup:
        print(f"\n--- Looking up: {word} ---\n")
        entries = bdb.fetch_entry(word)

        if entries:
            for i, entry in enumerate(entries[:2], 1):  # Show first 2 meanings
                print(f"{i}. {entry.lexicon_name}")
                if entry.headword:
                    print(f"   Vocalized: {entry.headword}")
                if entry.strong_number:
                    print(f"   Strong's: {entry.strong_number}")
                if entry.transliteration:
                    print(f"   Pronunciation: {entry.transliteration}")

                # Show first 150 chars of definition
                definition = entry.entry_text.replace('\n', ' ')[:150]
                print(f"   Definition: {definition}...")
                print()

            if len(entries) > 2:
                print(f"   ... and {len(entries) - 2} more meanings\n")
        else:
            print(f"   No entries found for {word}\n")

    # ========================================================================
    # LIBRARIAN 2: CONCORDANCE SEARCHES
    # ========================================================================

    print_separator("LIBRARIAN 2: CONCORDANCE (Where else do these words appear?)")

    concordance = ConcordanceLibrarian()

    # Search each word
    words_to_search = [
        ("אור", "light"),
        ("ישע", "salvation"),
        ("ירא", "fear"),
        ("מעוז", "stronghold"),
        ("פחד", "afraid")
    ]

    for word, gloss in words_to_search:
        print(f"\n--- Searching: {word} ({gloss}) ---\n")

        request = ConcordanceRequest(
            query=word,
            scope="Psalms",
            level="consonantal",
            include_variations=True
        )

        bundle = concordance.search_with_variations(request)

        print(f"Variations searched: {len(bundle.variations_searched)}")
        print(f"Results found: {len(bundle.results)}")
        print(f"Sample variations: {', '.join(bundle.variations_searched[:8])}...")
        print()

        # Show first 3 results
        print("Top matches:")
        for result in bundle.results[:3]:
            print(f"\n  {result.reference}")
            hebrew = result.hebrew_text[:60] + "..." if len(result.hebrew_text) > 60 else result.hebrew_text
            english = result.english_text[:60] + "..." if len(result.english_text) > 60 else result.english_text
            print(f"    Hebrew: {hebrew}")
            print(f"    English: {english}")
            print(f"    Matched: {result.matched_word}")

        if len(bundle.results) > 3:
            print(f"\n  ... and {len(bundle.results) - 3} more matches")

    # ========================================================================
    # LIBRARIAN 3: FIGURATIVE LANGUAGE
    # ========================================================================

    print_separator("LIBRARIAN 3: FIGURATIVE LANGUAGE (Metaphors & Imagery)")

    figurative = FigurativeLibrarian()

    # Request 1: All figurative language in Psalm 27:1
    print("--- Request 1: All figurative language in Psalm 27:1 ---\n")

    request1 = FigurativeRequest(
        book="Psalms",
        chapter=27,
        verse_start=1,
        verse_end=1,
        metaphor=True
    )

    bundle1 = figurative.search(request1)

    if bundle1.instances:
        print(f"Found {len(bundle1.instances)} figurative instance(s) in Psalm 27:1\n")

        for i, instance in enumerate(bundle1.instances, 1):
            print(f"{i}. {instance.reference}")

            types = []
            if hasattr(instance, 'is_metaphor') and instance.is_metaphor:
                types.append('metaphor')
            if hasattr(instance, 'is_simile') and instance.is_simile:
                types.append('simile')
            print(f"   Type: {', '.join(types) if types else 'figurative'}")

            if instance.vehicle:
                print(f"   Vehicle: {', '.join(instance.vehicle)}")
            if instance.target:
                print(f"   Target: {', '.join(instance.target)}")
            if instance.ground:
                print(f"   Ground: {', '.join(instance.ground)}")

            if hasattr(instance, 'figurative_text'):
                fig_text = instance.figurative_text[:80] + "..." if len(instance.figurative_text) > 80 else instance.figurative_text
                print(f"   Text: {fig_text}")

            print()
    else:
        print("No figurative language found in Psalm 27:1")

    # Request 2: "Stronghold" metaphors across all Psalms
    print("\n--- Request 2: 'Stronghold' metaphors across all Psalms ---\n")

    request2 = FigurativeRequest(
        book="Psalms",
        vehicle_contains="stronghold"
    )

    bundle2 = figurative.search(request2)

    if bundle2.instances:
        print(f"Found {len(bundle2.instances)} 'stronghold' metaphor(s) across Psalms\n")

        for i, instance in enumerate(bundle2.instances[:5], 1):  # Show first 5
            print(f"{i}. {instance.reference}")
            if instance.vehicle:
                print(f"   Vehicle: {', '.join(instance.vehicle[:2])}")
            if instance.target:
                print(f"   Target: {', '.join(instance.target[:2])}")
            if hasattr(instance, 'figurative_text'):
                fig_text = instance.figurative_text[:60] + "..." if len(instance.figurative_text) > 60 else instance.figurative_text
                print(f"   Text: {fig_text}")
            print()

        if len(bundle2.instances) > 5:
            print(f"... and {len(bundle2.instances) - 5} more stronghold metaphors")
    else:
        print("No 'stronghold' metaphors found")

    # ========================================================================
    # LIBRARIAN 4: RESEARCH BUNDLE ASSEMBLER
    # ========================================================================

    print_separator("LIBRARIAN 4: RESEARCH BUNDLE ASSEMBLER (Complete Package)")

    print("Creating complete research bundle for Scholar agent...\n")

    # Create full research request
    research_request = {
        "psalm_chapter": 27,
        "lexicon": [
            {"word": "אור"},
            {"word": "ישע"},
            {"word": "ירא"},
            {"word": "מעוז"},
            {"word": "פחד"}
        ],
        "concordance": [
            {"query": "אור", "scope": "Psalms", "level": "consonantal"},
            {"query": "מעוז", "scope": "Psalms", "level": "consonantal"}
        ],
        "figurative": [
            {"book": "Psalms", "chapter": 27, "verse_start": 1, "verse_end": 1, "metaphor": True},
            {"book": "Psalms", "vehicle_contains": "stronghold"}
        ]
    }

    assembler = ResearchAssembler()
    request_json = json.dumps(research_request, ensure_ascii=False)
    bundle = assembler.assemble_from_json(request_json)

    # Show summary
    summary = bundle.to_dict()['summary']
    print("RESEARCH BUNDLE SUMMARY:")
    print(f"  Lexicon entries: {summary['lexicon_entries']}")
    print(f"  Concordance searches: {summary['concordance_searches']}")
    print(f"  Concordance results: {summary['concordance_results']}")
    print(f"  Figurative searches: {summary['figurative_searches']}")
    print(f"  Figurative instances: {summary['figurative_instances']}")
    print()

    # Generate markdown output
    markdown = bundle.to_markdown()
    print(f"Generated markdown bundle: {len(markdown)} characters")
    print()

    # Show preview of markdown (first 800 chars)
    print("MARKDOWN PREVIEW (for Scholar agent):")
    print("-" * 80)
    print(markdown[:800])
    print("\n... (continues for", len(markdown) - 800, "more characters)")
    print("-" * 80)

    # Save to file
    output_dir = Path(__file__).parent.parent / 'tests' / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)

    markdown_file = output_dir / 'psalm_27_1_research_bundle.md'
    json_file = output_dir / 'psalm_27_1_research_bundle.json'

    with open(markdown_file, 'w', encoding='utf-8') as f:
        f.write(markdown)

    with open(json_file, 'w', encoding='utf-8') as f:
        f.write(bundle.to_json())

    print()
    print(f"✅ Full research bundle saved:")
    print(f"   Markdown: {markdown_file}")
    print(f"   JSON: {json_file}")
    print()

    print_separator("DEMO COMPLETE")

    print("WHAT HAPPENS NEXT:")
    print()
    print("1. Scholar-Writer receives the markdown bundle")
    print("2. Scholar analyzes the verse with:")
    print("   - 5 Hebrew words defined with multiple meanings")
    print("   - Concordance showing where these words appear elsewhere")
    print("   - Figurative language analysis of metaphors")
    print("3. Scholar writes verse-by-verse commentary")
    print("4. Commentary integrates:")
    print("   - Lexical nuances (אור = light, but what KIND of light?)")
    print("   - Intertextual connections (where else is God called 'stronghold'?)")
    print("   - Figurative analysis (military fortress → divine protection)")
    print()
    print("This is what 'research-backed commentary' looks like! 📚")
    print()

if __name__ == '__main__':
    main()
