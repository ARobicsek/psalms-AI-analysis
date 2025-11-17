"""
Related Psalms Librarian

Loads and formats related psalm information from the top connections analysis.
For any given psalm, retrieves matching psalms with their full text and detailed
information about shared roots, contiguous phrases, and skipgrams.

This librarian provides comprehensive context about potentially related psalms
to help the synthesis and editor agents make connections.
"""

import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

# Handle imports for both module and script usage
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.data_sources.tanakh_database import TanakhDatabase
else:
    from ..data_sources.tanakh_database import TanakhDatabase


@dataclass
class RelatedPsalmMatch:
    """Information about a related psalm and its connections."""
    psalm_number: int
    final_score: float
    full_text_hebrew: List[Dict[str, Any]]  # List of {"verse": int, "hebrew": str}
    full_text_english: List[Dict[str, Any]]  # List of {"verse": int, "english": str}
    shared_roots: List[Dict[str, Any]]
    contiguous_phrases: List[Dict[str, Any]]
    skipgrams: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'psalm_number': self.psalm_number,
            'final_score': self.final_score,
            'full_text_hebrew': self.full_text_hebrew,
            'full_text_english': self.full_text_english,
            'shared_roots': self.shared_roots,
            'contiguous_phrases': self.contiguous_phrases,
            'skipgrams': self.skipgrams
        }


class RelatedPsalmsLibrarian:
    """
    Retrieves and formats related psalms from the top connections analysis.

    This librarian identifies psalms that have significant word and phrase
    relationships with the psalm being analyzed, providing the synthesis and
    master editor agents with potentially relevant connections.
    """

    def __init__(
        self,
        connections_file: str = "data/analysis_results/top_550_connections_v6.json",
        db: Optional[TanakhDatabase] = None
    ):
        """
        Initialize Related Psalms Librarian.

        Args:
            connections_file: Path to the top connections JSON file
            db: TanakhDatabase instance (creates new if None)
        """
        self.connections_file = Path(connections_file)
        self.db = db or TanakhDatabase()
        self.connections_data = self._load_connections()

    def _load_connections(self) -> List[Dict[str, Any]]:
        """Load the connections data from JSON file."""
        if not self.connections_file.exists():
            return []

        with open(self.connections_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_related_psalms(self, psalm_number: int) -> List[RelatedPsalmMatch]:
        """
        Get all related psalms for a given psalm number.

        Args:
            psalm_number: The psalm number to find connections for

        Returns:
            List of RelatedPsalmMatch objects with full psalm text and connection details
        """
        related = []

        for connection in self.connections_data:
            # Check if this psalm is psalm_a or psalm_b in the connection
            if connection['psalm_a'] == psalm_number:
                related_psalm_num = connection['psalm_b']
            elif connection['psalm_b'] == psalm_number:
                related_psalm_num = connection['psalm_a']
            else:
                continue

            # Get the full text of the related psalm
            psalm = self.db.get_psalm(related_psalm_num)
            if not psalm:
                continue

            # Extract Hebrew and English text
            hebrew_text = [{"verse": v.verse, "hebrew": v.hebrew} for v in psalm.verses]
            english_text = [{"verse": v.verse, "english": v.english} for v in psalm.verses]

            # Extract connection details
            # Note: The data structure uses matches_from_a and matches_from_b
            # We need to preserve these as they show where matches occur in each psalm

            match = RelatedPsalmMatch(
                psalm_number=related_psalm_num,
                final_score=connection.get('final_score', 0.0),
                full_text_hebrew=hebrew_text,
                full_text_english=english_text,
                shared_roots=connection.get('deduplicated_roots', []),
                contiguous_phrases=connection.get('deduplicated_contiguous_phrases', []),
                skipgrams=connection.get('deduplicated_skipgrams', [])
            )

            related.append(match)

        # Sort by score (highest first)
        related.sort(key=lambda x: x.final_score, reverse=True)

        # Limit to top 5 most related psalms
        return related[:5]

    def format_for_research_bundle(
        self,
        psalm_number: int,
        related_matches: List[RelatedPsalmMatch]
    ) -> str:
        """
        Format related psalms as markdown for inclusion in research bundle.

        Args:
            psalm_number: The psalm being analyzed
            related_matches: List of related psalm matches

        Returns:
            Formatted markdown string
        """
        if not related_matches:
            return ""

        md = f"## Related Psalms Analysis\n\n"

        # Build list of related psalm numbers for display
        psalm_numbers = ", ".join([str(m.psalm_number) for m in related_matches])

        md += f"The librarian has found that the psalm you're analyzing (Psalm {psalm_number}) has some POSSIBLY interesting word and phrase relationships with other psalms (Psalms {psalm_numbers}).\n\n"

        md += "To understand the potential value of these connections, consider the scholarly consensus regarding Psalm 25 and Psalm 34. These two acrostics are a classic example of a \"diptych,\" or deliberate pair, linked by numerous structural and thematic echoes.\n"
        md += "- **Structural Anomaly**: They both share the unique acrostic structure of omitting the Vav (ו) stanza and adding a final Pe (פ) stanza, which links them conceptually through the root פדה (padah - to redeem).\n"
        md += "- **The \"Call and Response\" Arc**: This structural link is reinforced by a clear theological arc:\n"
        md += "  - **The Plea (Ps 25:22)**: Concludes with the petition פְּדֵה... מִכֹּל צָרוֹתָיו (pedeh... mikol tzarotav - \"Redeem... from all his troubles\").\n"
        md += "  - **The Response (Ps 34:7, 18)**: Answers with the assurance וּמִכׇּל־צָרוֹתָיו הוֹשִׁיעוֹ (u'mikol-tzarotav hoshio - \"and from all his troubles He saved him\") and the final capstone statement פֹּדֶה יְהֹוָה (podeh Adonai - \"The Lord redeems\").\n"
        md += "- **Shared Wisdom Theme**: Both psalms pivot to wisdom instruction using the nearly identical rhetorical question מִי־הָאִישׁ (mi ha-ish - \"Who is the man...\") (Ps 25:12, Ps 34:13).\n"
        md += "- **Shared Thematic Vocabulary**: They are further bound by a specific vocabulary of piety and instruction, including:\n"
        md += "  - \"Fear of the LORD\" (Ps 25:12, 14; Ps 34:8, 10, 12)\n"
        md += "  - \"The humble/afflicted\" (עֲנָוִים - anavim) (Ps 25:9; Ps 34:3)\n"
        md += "  - \"Good\" (טוֹב - tov) (Ps 25:13; Ps 34:9, 11, 13)\n\n"

        md += "As you review the data below, ask yourself if a similar structural, thematic, or \"call-and-response\" dynamic is at play here, where one psalm seems to complete or answer the other.\n\n"

        md += f"Below is the full text of the psalms potentially related to Psalm {psalm_number}, and for each psalm, a list of POSSIBLY related words and phrases that were algorithmically detected. These relationships might deepen your insights into the meaning, intent, posture, history, and poetics of the psalm you are analyzing. Feel free to REJECT these possible connections as spurious, but DO incorporate them into your work where relevant.\n\n"

        md += "---\n\n"

        for match in related_matches:
            md += self._format_single_match(psalm_number, match)

        return md

    def _remove_nikud(self, text: str) -> str:
        """Remove Hebrew vowel points (nikud) and cantillation marks."""
        # Unicode ranges for Hebrew vowel points and cantillation marks
        nikud_pattern = r'[\u0591-\u05C7]'
        return re.sub(nikud_pattern, '', text)

    def _extract_word_context(self, verse_text: str, root: str, context_words: int = 3) -> str:
        """
        Extract a snippet showing the root word with context_words on either side.

        Args:
            verse_text: Full verse text in Hebrew
            root: The root to find in the verse
            context_words: Number of words to show on either side (default 3)

        Returns:
            Snippet with the matched word and surrounding context
        """
        if not verse_text or not root:
            return "..."

        # Split verse into words
        words = verse_text.split()

        # Remove nikud from root for comparison
        root_consonantal = self._remove_nikud(root)

        # Find the first word containing the root (consonantal match)
        matched_index = -1
        for i, word in enumerate(words):
            word_consonantal = self._remove_nikud(word)
            if root_consonantal in word_consonantal:
                matched_index = i
                break

        # If no match found, just return first few words
        if matched_index == -1:
            snippet_words = words[:min(7, len(words))]
            return " ".join(snippet_words) + ("..." if len(words) > 7 else "")

        # Extract context: matched_index ± context_words
        start_idx = max(0, matched_index - context_words)
        end_idx = min(len(words), matched_index + context_words + 1)

        snippet_words = words[start_idx:end_idx]

        # Add ellipsis if truncated
        prefix = "..." if start_idx > 0 else ""
        suffix = "..." if end_idx < len(words) else ""

        return prefix + " ".join(snippet_words) + suffix

    def _format_single_match(self, analyzing_psalm: int, match: RelatedPsalmMatch) -> str:
        """Format a single related psalm match."""
        md = f"### Psalm {match.psalm_number} (Connection Score: {match.final_score:.2f})\n\n"

        # Filter roots early so we can check if we have any displayable content
        filtered_roots = [r for r in match.shared_roots if r.get('idf', 0) >= 1]

        # Full text of the related psalm (Hebrew only)
        md += f"#### Full Text of Psalm {match.psalm_number}\n\n"

        for verse_data in match.full_text_hebrew:
            verse_num = verse_data['verse']
            hebrew = verse_data['hebrew']

            md += f"**Verse {verse_num}**: {hebrew}\n\n"

        # Shared patterns
        md += f"#### Shared Patterns\n\n"

        # Contiguous phrases FIRST
        if match.contiguous_phrases:
            md += f"**Contiguous Phrases** ({len(match.contiguous_phrases)} found):\n\n"
            for phrase in match.contiguous_phrases:
                md += f"- **{phrase.get('hebrew', phrase.get('consonantal', 'N/A'))}** "
                md += f"({phrase.get('length', 0)}-word)\n"

                # Show matches from the analyzed psalm with verse context
                matches_a = phrase.get('matches_from_a', [])
                if matches_a:
                    md += f"  - Psalm {analyzing_psalm if analyzing_psalm < match.psalm_number else match.psalm_number} (×{len(matches_a)}): "
                    verses = []
                    for m in matches_a[:3]:
                        text = m.get('hebrew', m.get('text', 'N/A'))
                        # Truncate if over 100 chars
                        if len(text) > 100:
                            text = text[:100] + "..."
                        verses.append(f"v.{m.get('verse', '?')} {text}")
                    md += ", ".join(verses)
                    md += "\n"

                # Show matches from the related psalm with verse context
                matches_b = phrase.get('matches_from_b', [])
                if matches_b:
                    md += f"  - Psalm {match.psalm_number if analyzing_psalm < match.psalm_number else analyzing_psalm} (×{len(matches_b)}): "
                    verses = []
                    for m in matches_b[:3]:
                        text = m.get('hebrew', m.get('text', 'N/A'))
                        # Truncate if over 100 chars
                        if len(text) > 100:
                            text = text[:100] + "..."
                        verses.append(f"v.{m.get('verse', '?')} {text}")
                    md += ", ".join(verses)
                    md += "\n"

                md += "\n"

        # Skipgrams SECOND
        if match.skipgrams:
            md += f"**Skipgrams** ({len(match.skipgrams)} found):\n\n"
            md += "*Patterns where words appear in the same order but not necessarily adjacent*\n\n"
            for skipgram in match.skipgrams:
                # Use hebrew field from skipgram, fall back to consonantal
                skipgram_display = skipgram.get('hebrew', skipgram.get('matched_hebrew', skipgram.get('consonantal', 'N/A')))
                md += f"- **{skipgram_display}** "
                md += f"({skipgram.get('length', 0)}-word, "
                md += f"{skipgram.get('gap_word_count', 0)} gap)\n"

                # Show matches from the analyzed psalm with verse context
                matches_a = skipgram.get('matches_from_a', [])
                if matches_a:
                    md += f"  - Psalm {analyzing_psalm if analyzing_psalm < match.psalm_number else match.psalm_number} (×{len(matches_a)}): "
                    verses = []
                    for m in matches_a[:2]:
                        # V6 skipgrams use 'full_span_hebrew' not 'hebrew' or 'text'
                        text = m.get('full_span_hebrew', m.get('hebrew', m.get('text', 'N/A')))
                        # Truncate if over 100 chars
                        if len(text) > 100:
                            text = text[:100] + "..."
                        verses.append(f"v.{m.get('verse', '?')} {text}")
                    md += ", ".join(verses)
                    md += "\n"

                # Show matches from the related psalm with verse context
                matches_b = skipgram.get('matches_from_b', [])
                if matches_b:
                    md += f"  - Psalm {match.psalm_number if analyzing_psalm < match.psalm_number else analyzing_psalm} (×{len(matches_b)}): "
                    verses = []
                    for m in matches_b[:2]:
                        # V6 skipgrams use 'full_span_hebrew' not 'hebrew' or 'text'
                        text = m.get('full_span_hebrew', m.get('hebrew', m.get('text', 'N/A')))
                        # Truncate if over 100 chars
                        if len(text) > 100:
                            text = text[:100] + "..."
                        verses.append(f"v.{m.get('verse', '?')} {text}")
                    md += ", ".join(verses)
                    md += "\n"

                md += "\n"

        # Shared roots THIRD (sorted by IDF descending - best matches first)
        if filtered_roots:
            # Sort by IDF descending
            sorted_roots = sorted(filtered_roots, key=lambda r: r.get('idf', 0), reverse=True)

            md += f"**Shared Roots** ({len(sorted_roots)} found, sorted by relevance):\n\n"

            for root in sorted_roots:
                md += f"- Root: `{root.get('root', 'N/A')}`\n"

                # Show matches from analyzed psalm with context (matched word ± 3 words)
                matches_a = root.get('matches_from_a', [])
                if matches_a:
                    md += f"  - Psalm {analyzing_psalm if analyzing_psalm < match.psalm_number else match.psalm_number} (×{len(matches_a)}): "
                    snippets = []
                    for m in matches_a[:3]:
                        snippet = self._extract_word_context(m.get('hebrew', m.get('text', '')), root.get('root', ''), 3)
                        snippets.append(f"v.{m.get('verse', '?')} {snippet}")
                    md += ", ".join(snippets)
                    md += "\n"

                # Show matches from related psalm with context
                matches_b = root.get('matches_from_b', [])
                if matches_b:
                    md += f"  - Psalm {match.psalm_number if analyzing_psalm < match.psalm_number else analyzing_psalm} (×{len(matches_b)}): "
                    snippets = []
                    for m in matches_b[:3]:
                        snippet = self._extract_word_context(m.get('hebrew', m.get('text', '')), root.get('root', ''), 3)
                        snippets.append(f"v.{m.get('verse', '?')} {snippet}")
                    md += ", ".join(snippets)
                    md += "\n"

                md += "\n"

        # If no patterns found at all (shouldn't happen, but just in case)
        if not filtered_roots and not match.contiguous_phrases and not match.skipgrams:
            md += "*No specific patterns documented, but overall connection score suggests potential relationship.*\n\n"

        md += "---\n\n"

        return md


def main():
    """Command-line interface for testing."""
    import argparse

    parser = argparse.ArgumentParser(description='Find related psalms')
    parser.add_argument('psalm', type=int, help='Psalm number')
    parser.add_argument('--connections-file',
                       default='data/analysis_results/top_550_connections_v6.json',
                       help='Path to connections file')

    args = parser.parse_args()

    librarian = RelatedPsalmsLibrarian(connections_file=args.connections_file)
    matches = librarian.get_related_psalms(args.psalm)

    if matches:
        print(f"\nFound {len(matches)} related psalms for Psalm {args.psalm}:\n")
        for match in matches:
            print(f"  - Psalm {match.psalm_number}: Score {match.final_score:.2f}")
            print(f"    Contiguous phrases: {len(match.contiguous_phrases)}")
            print(f"    Skipgrams: {len(match.skipgrams)}")

        print("\n" + "="*80)
        print("\nFormatted for research bundle:\n")
        print(librarian.format_for_research_bundle(args.psalm, matches))
    else:
        print(f"\nNo related psalms found for Psalm {args.psalm}")


if __name__ == '__main__':
    main()
