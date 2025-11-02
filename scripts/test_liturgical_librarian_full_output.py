"""
Test script to run liturgical librarian for specific psalms and capture full output.

This script:
1. Runs the liturgical librarian for specified psalms (1 and 145)
2. Captures all LLM prompts and responses
3. Outputs everything to a detailed text file
4. Shows the full research bundle data

Usage:
    python scripts/test_liturgical_librarian_full_output.py
"""

import sys
import os
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents.liturgical_librarian import LiturgicalLibrarian


def format_match(match, index):
    """Format a single LiturgicalMatch for display."""
    lines = []
    lines.append(f"\n{'='*80}")
    lines.append(f"MATCH #{index}")
    lines.append(f"{'='*80}")
    lines.append(f"Match Type: {match.match_type}")
    lines.append(f"Confidence: {match.confidence}")
    lines.append(f"Prayer ID: {match.prayer_id}")
    lines.append(f"Prayer Name: {match.prayer_name}")
    lines.append(f"Nusach: {match.nusach}")
    lines.append(f"Occasion: {match.occasion}")
    lines.append(f"Service: {match.service}")
    lines.append(f"Section: {match.section}")

    # Canonical fields
    lines.append(f"\nCanonical Classification:")
    lines.append(f"  Main prayer in this liturgical block: {match.canonical_prayer_name}")
    lines.append(f"  L1 (Occasion): {match.canonical_L1_Occasion}")
    lines.append(f"  L2 (Service): {match.canonical_L2_Service}")
    lines.append(f"  L3 (Signpost): {match.canonical_L3_Signpost}")
    lines.append(f"  L4 (SubSection): {match.canonical_L4_SubSection}")
    lines.append(f"  Location Description: {match.canonical_location_description}")

    lines.append(f"\nVerse Range: {match.psalm_verse_start}-{match.psalm_verse_end}")
    lines.append(f"Psalm Phrase: {match.psalm_phrase_hebrew[:200]}..." if len(match.psalm_phrase_hebrew) > 200 else f"Psalm Phrase: {match.psalm_phrase_hebrew}")
    lines.append(f"\nLiturgy Context ({len(match.liturgy_context)} chars):")
    lines.append(f"{match.liturgy_context}")

    return "\n".join(lines)


def format_phrase_group(phrase, matches, summary, validation_notes):
    """Format a phrase group with its matches and summary."""
    lines = []
    lines.append(f"\n{'#'*80}")
    lines.append(f"PHRASE GROUP")
    lines.append(f"{'#'*80}")
    lines.append(f"Phrase: {phrase}")
    lines.append(f"Number of matches: {len(matches)}")
    if validation_notes:
        lines.append(f"Validation Notes: {validation_notes}")

    # Show all matches in this group
    lines.append(f"\n{'-'*80}")
    lines.append(f"ALL MATCHES IN THIS GROUP:")
    lines.append(f"{'-'*80}")
    for i, match in enumerate(matches, 1):
        lines.append(format_match(match, i))

    # Show the LLM summary
    lines.append(f"\n{'-'*80}")
    lines.append(f"LLM SUMMARY FOR THIS PHRASE GROUP:")
    lines.append(f"{'-'*80}")
    lines.append(summary if summary else "(No summary generated)")

    return "\n".join(lines)

def format_full_psalm_section(matches, summary):
    """Format the full psalm recitation section."""
    lines = []
    lines.append(f"\n{'#'*80}")
    lines.append(f"FULL PSALM RECITATIONS")
    lines.append(f"{'#'*80}")
    lines.append(f"Number of matches: {len(matches)}")

    # Show all matches
    lines.append(f"\n{'-'*80}")
    lines.append(f"ALL FULL PSALM MATCHES:")
    lines.append(f"{'-'*80}")
    for i, match in enumerate(matches, 1):
        lines.append(format_match(match, i))

    # Show the LLM summary
    lines.append(f"\n{'-'*80}")
    lines.append(f"LLM SUMMARY FOR FULL PSALM RECITATIONS:")
    lines.append(f"{'-'*80}")
    lines.append(summary if summary else "(No summary generated)")

    return "\n".join(lines)


def capture_llm_data(librarian, psalm_chapter):
    """
    Capture all the data that would be sent to the LLM.
    This requires modifying the librarian to expose internal prompt data.
    For now, we'll reconstruct what we can from the matches.
    """
    lines = []
    lines.append(f"\n{'*'*80}")
    lines.append(f"LLM PROMPT DATA FOR PSALM {psalm_chapter}")
    lines.append(f"{'*'*80}")

    # Get all matches for this psalm
    all_matches = []

    # Get phrase matches
    try:
        conn = librarian._get_db_connection()
        cursor = conn.cursor()

        # Get all unique phrases for this psalm
        cursor.execute("""
            SELECT DISTINCT psalm_phrase_hebrew
            FROM psalms_liturgy_index
            WHERE psalm_chapter = ?
            AND match_type = 'phrase_match'
            AND is_unique = 1
            ORDER BY psalm_verse_start
        """, (psalm_chapter,))

        phrases = [row[0] for row in cursor.fetchall()]
        conn.close()

        lines.append(f"\nTotal unique phrases to be summarized: {len(phrases)}")

        for phrase in phrases[:5]:  # Show first 5 as examples
            lines.append(f"\nExample phrase: {phrase[:100]}...")

    except Exception as e:
        lines.append(f"\nError capturing phrase data: {e}")

    return "\n".join(lines)


def test_psalm(psalm_chapter, output_file):
    """Test liturgical librarian for a specific psalm."""

    print(f"\n{'='*80}")
    print(f"TESTING PSALM {psalm_chapter}")
    print(f"{'='*80}\n")

    output_file.write(f"\n\n{'='*100}\n")
    output_file.write(f"PSALM {psalm_chapter} - LITURGICAL ANALYSIS\n")
    output_file.write(f"{'='*100}\n")
    output_file.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Initialize librarian
    librarian = LiturgicalLibrarian(verbose=True)

    # Get the research bundle (this is what gets passed to commentary generation)
    print(f"Generating research bundle for Psalm {psalm_chapter}...")
    try:
        research_bundle = librarian.generate_research_bundle(psalm_chapter)

        output_file.write(f"\n{'='*80}\n")
        output_file.write(f"RESEARCH BUNDLE STRUCTURE\n")
        output_file.write(f"{'='*80}\n")
        output_file.write(f"Full Psalm Recitations: {len(research_bundle.get('full_psalm_recitations', []))} matches\n")
        output_file.write(f"Full Psalm Summary: {len(research_bundle.get('full_psalm_summary', ''))} chars\n")
        output_file.write(f"Phrase Groups: {len(research_bundle.get('phrase_groups', []))}\n")

        # Show full psalm recitations section
        if research_bundle.get('full_psalm_recitations'):
            output_file.write(format_full_psalm_section(
                research_bundle['full_psalm_recitations'],
                research_bundle.get('full_psalm_summary', '')
            ))

        # Show each phrase group
        for phrase_data in research_bundle.get('phrase_groups', []):
            phrase = phrase_data.get('phrase', '')
            matches = phrase_data.get('matches', [])
            summary = phrase_data.get('summary', '')
            validation_notes = phrase_data.get('validation_notes', '')

            output_file.write(format_phrase_group(phrase, matches, summary, validation_notes))

        # Show the complete JSON research bundle (compact)
        output_file.write(f"\n\n{'='*80}\n")
        output_file.write(f"COMPLETE RESEARCH BUNDLE (JSON)\n")
        output_file.write(f"{'='*80}\n")

        # Convert to serializable format
        serializable_bundle = {
            'psalm_chapter': research_bundle.get('psalm_chapter'),
            'full_psalm_summary': research_bundle.get('full_psalm_summary', ''),
            'full_psalm_recitations_count': len(research_bundle.get('full_psalm_recitations', [])),
            'phrase_groups': []
        }

        for pg in research_bundle.get('phrase_groups', []):
            serializable_bundle['phrase_groups'].append({
                'phrase': pg.get('phrase', ''),
                'matches_count': len(pg.get('matches', [])),
                'summary': pg.get('summary', ''),
                'verses': pg.get('verses', []),
                'validation_notes': pg.get('validation_notes', '')
            })

        output_file.write(json.dumps(serializable_bundle, indent=2, ensure_ascii=False))

        # Capture what was sent to LLM
        output_file.write(capture_llm_data(librarian, psalm_chapter))

        print(f"[OK] Research bundle generated successfully")
        print(f"  - Full psalm recitations: {len(research_bundle.get('full_psalm_recitations', []))}")
        print(f"  - Phrase groups: {len(research_bundle.get('phrase_groups', []))}")

    except Exception as e:
        error_msg = f"ERROR generating research bundle: {e}"
        print(error_msg)
        output_file.write(f"\n\n{error_msg}\n")
        import traceback
        traceback.print_exc()
        output_file.write(traceback.format_exc())


def main():
    """Main test function."""

    # Create output directory if needed
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(output_dir, exist_ok=True)

    # Create output file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(output_dir, f'liturgical_librarian_full_output_{timestamp}.txt')

    print(f"\nLiturgical Librarian Full Output Test")
    print(f"======================================")
    print(f"Output file: {output_path}")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("LITURGICAL LIBRARIAN - FULL OUTPUT TEST\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*100 + "\n")

        # Test Psalm 1
        test_psalm(1, f)

        # Test Psalm 145
        # test_psalm(145, f)

        f.write(f"\n\n{'='*100}\n")
        f.write(f"TEST COMPLETE\n")
        f.write(f"{'='*100}\n")

    print(f"\n[OK] Output written to: {output_path}")
    print(f"\nTo view the output:")
    print(f"  type {output_path}")


if __name__ == '__main__':
    main()
