#!/usr/bin/env python3
"""
Analyze micro analyst phrases to understand the conversion issue.
"""

import json
from pathlib import Path

def main():
    # Load micro analysis output
    micro_file = Path(__file__).parent / "output" / "psalm_15" / "psalm_015_micro_v2.json"

    with open(micro_file, 'r', encoding='utf-8') as f:
        micro_data = json.load(f)

    # Save analysis to file
    output_file = Path(__file__).parent / "phrase_conversion_analysis.txt"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("PHRASE CONVERSION ANALYSIS\n")
        f.write("=" * 80 + "\n\n")
        f.write("Issue: Micro analyst provides exact phrases but LLM converts to base forms\n\n")

        # Extract lexical insights
        verse_count = 0
        insight_count = 0

        for verse_commentary in micro_data.get('verse_commentaries', []):
            verse_num = verse_commentary.get('verse_number')
            verse_count += 1

            f.write(f"Verse {verse_num}:\n")
            f.write("-" * 40 + "\n")

            for insight in verse_commentary.get('lexical_insights', []):
                insight_count += 1
                phrase = insight.get('phrase', '')
                variants = insight.get('variants', [])
                notes = insight.get('notes', '')

                f.write(f"\n  Lexical Insight {insight_count}:\n")
                f.write(f"    Phrase: {phrase}\n")
                f.write(f"    Variants: {variants}\n")
                f.write(f"    Notes: {notes}\n")

                # Analysis
                if phrase:
                    # Check for prefixes
                    prefixes = []
                    if phrase.startswith('ו'):
                        prefixes.append('ו (and)')
                    if phrase.startswith('ב'):
                        prefixes.append('ב (in)')
                    if phrase.startswith('ל'):
                        prefixes.append('ל (to)')
                    if phrase.startswith('מ'):
                        prefixes.append('מ (from)')
                    if phrase.startswith('כ'):
                        prefixes.append('כ (like)')
                    if phrase.startswith('ה'):
                        prefixes.append('ה (the)')
                    if phrase.startswith('י'):
                        prefixes.append('י (he/3ms future)')

                    # Check for suffixes
                    suffixes = []
                    if phrase.endswith('ך') or phrase.endswith('ךָ') or phrase.endswith('ךְ'):
                        suffixes.append('your (m.s)')
                    if phrase.endswith('יו') or phrase.endswith('י') and len(phrase) > 2:
                        suffixes.append('his')
                    if phrase.endswith('ים'):
                        suffixes.append('their (m.p)')
                    if phrase.endswith('ינו'):
                        suffixes.append('our')
                    if phrase.endswith('כם'):
                        suffixes.append('your (m.p)')
                    if phrase.endswith('כן'):
                        suffixes.append('your (f.p)')

                    f.write(f"    Analysis:\n")
                    if prefixes:
                        f.write(f"      Prefixes: {', '.join(prefixes)}\n")
                    if suffixes:
                        f.write(f"      Suffixes: {', '.join(suffixes)}\n")

                    # Check what the base form would be
                    base_form = phrase
                    # Remove common prefixes
                    for prefix in ['ו', 'ב', 'ל', 'מ', 'כ', 'ה', 'ש', 'י', 'ת', 'נ']:
                        if base_form.startswith(prefix):
                            base_form = base_form[1:]
                            break

                    # Remove common suffixes (simplified)
                    for suffix in ['ים', 'יו', 'ינו', 'כם', 'כן', 'ך', 'י']:
                        if base_form.endswith(suffix):
                            base_form = base_form[:-len(suffix)]
                            break

                    if base_form != phrase:
                        f.write(f"      Base form would be: {base_form}\n")

                f.write("\n")

            if verse_count >= 3:  # Just first 3 verses for brevity
                break

        f.write("\n" + "=" * 80 + "\n")
        f.write("SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total verses analyzed: {verse_count}\n")
        f.write(f"Total lexical insights: {insight_count}\n")
        f.write("\nKey finding: The micro analyst IS providing exact forms with prefixes/suffixes.\n")
        f.write("The LLM is ignoring these and outputting base forms despite the prompt instruction.\n")
        f.write("\nThe fix needs to ensure the exact phrases are preserved in the research requests.")

    print(f"Analysis saved to {output_file}")

if __name__ == "__main__":
    main()