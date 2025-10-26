"""
Liturgical Librarian (Sefaria Bootstrap) - Phase 0

Queries Sefaria's curated Psalms→Liturgy cross-references.
This provides immediate liturgical context while the comprehensive phrase-level system is built.

Usage:
    from src.agents.liturgical_librarian_sefaria import SefariaLiturgicalLibrarian

    librarian = SefariaLiturgicalLibrarian()
    links = librarian.find_liturgical_usage(psalm_chapter=23)
    markdown = librarian.format_for_research_bundle(links)
"""

import sqlite3
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class SefariaLiturgicalLink:
    """Liturgical link from Sefaria's curated data."""

    psalm_chapter: int
    psalm_verse_start: Optional[int]
    psalm_verse_end: Optional[int]
    liturgy_ref: str
    collective_title: str
    nusach: Optional[str]
    occasion: Optional[str]
    service: Optional[str]
    section: Optional[str]
    confidence: float

    def format_verse_range(self) -> str:
        """Format verse range for display."""
        if not self.psalm_verse_start:
            return "Entire chapter"

        if self.psalm_verse_end and self.psalm_verse_end != self.psalm_verse_start:
            return f"{self.psalm_verse_start}-{self.psalm_verse_end}"

        return str(self.psalm_verse_start)

    def format_location(self) -> str:
        """Format liturgical location for display."""
        location_parts = []

        if self.collective_title:
            location_parts.append(self.collective_title)
        if self.occasion:
            location_parts.append(self.occasion)
        if self.service:
            location_parts.append(self.service)
        if self.section:
            location_parts.append(self.section)

        return " - ".join(location_parts) if location_parts else self.liturgy_ref


class SefariaLiturgicalLibrarian:
    """Query Sefaria's curated Psalms→Liturgy links."""

    def __init__(self, db_path: str = "data/liturgy.db"):
        self.db_path = db_path

    def find_liturgical_usage(
        self,
        psalm_chapter: int,
        psalm_verses: Optional[List[int]] = None,
        curated_only: bool = True
    ) -> List[SefariaLiturgicalLink]:
        """
        Find liturgical usage using Sefaria's curated links.

        Args:
            psalm_chapter: Psalm number (1-150)
            psalm_verses: Specific verses (None = entire chapter)
            curated_only: If True (default), only return manually curated quotations.
                         If False, return all links including auto-detected.

        Returns:
            List of liturgical links
        """

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Build WHERE clause with optional curated filter
        curated_filter = "AND link_type = 'quotation'" if curated_only else ""

        if psalm_verses is None:
            # Search for entire chapter or any verse
            query = f"""
                SELECT psalm_chapter, psalm_verse_start, psalm_verse_end,
                       liturgy_ref, collective_title, nusach, occasion,
                       service, section, confidence
                FROM sefaria_liturgy_links
                WHERE psalm_chapter = ? {curated_filter}
                ORDER BY confidence DESC, liturgy_ref
            """
            params = [psalm_chapter]
        else:
            # Search for specific verses
            verse_conditions = " OR ".join([
                "(psalm_verse_start <= ? AND (psalm_verse_end >= ? OR psalm_verse_end IS NULL))"
                for _ in psalm_verses
            ])

            query = f"""
                SELECT psalm_chapter, psalm_verse_start, psalm_verse_end,
                       liturgy_ref, collective_title, nusach, occasion,
                       service, section, confidence
                FROM sefaria_liturgy_links
                WHERE psalm_chapter = ? AND ({verse_conditions}) {curated_filter}
                ORDER BY confidence DESC, liturgy_ref
            """

            params = [psalm_chapter]
            for v in psalm_verses:
                params.extend([v, v])

        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            results.append(SefariaLiturgicalLink(
                psalm_chapter=row[0],
                psalm_verse_start=row[1],
                psalm_verse_end=row[2],
                liturgy_ref=row[3],
                collective_title=row[4],
                nusach=row[5],
                occasion=row[6],
                service=row[7],
                section=row[8],
                confidence=row[9]
            ))

        conn.close()
        return results

    def format_for_research_bundle(self, links: List[SefariaLiturgicalLink]) -> str:
        """
        Format liturgical links for research bundle (optimized for AI agents).

        Returns:
            Markdown-formatted section for research bundle
        """

        if not links:
            return "## Liturgical Usage\n\nNo liturgical usage found in Sefaria's manually curated database.\n"

        output = ["## Liturgical Usage (from Sefaria)\n"]
        output.append(f"This passage appears in **{len(links)} liturgical context(s)** according to Sefaria's manually curated quotations:\n")

        for link in links:
            output.append(f"**{link.format_location()}**")
            output.append(f"- Reference: {link.liturgy_ref}")
            output.append(f"- Verses: {link.format_verse_range()}")

            if link.nusach:
                output.append(f"- Tradition: {link.nusach}")

            output.append("")

        return "\n".join(output)

    def get_statistics(self) -> dict:
        """Get database statistics."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total links
        cursor.execute("SELECT COUNT(*) FROM sefaria_liturgy_links")
        total_links = cursor.fetchone()[0]

        # Curated links only
        cursor.execute("SELECT COUNT(*) FROM sefaria_liturgy_links WHERE link_type = 'quotation'")
        curated_links = cursor.fetchone()[0]

        # By link type
        cursor.execute("""
            SELECT link_type, COUNT(*) as count
            FROM sefaria_liturgy_links
            GROUP BY link_type
            ORDER BY count DESC
        """)
        by_link_type = cursor.fetchall()

        # Psalms with links (curated only)
        cursor.execute("SELECT COUNT(DISTINCT psalm_chapter) FROM sefaria_liturgy_links WHERE link_type = 'quotation'")
        psalms_with_curated = cursor.fetchone()[0]

        # Psalms with any links
        cursor.execute("SELECT COUNT(DISTINCT psalm_chapter) FROM sefaria_liturgy_links")
        psalms_with_links = cursor.fetchone()[0]

        # Top 10 Psalms (curated only)
        cursor.execute("""
            SELECT psalm_chapter, COUNT(*) as link_count
            FROM sefaria_liturgy_links
            WHERE link_type = 'quotation'
            GROUP BY psalm_chapter
            ORDER BY link_count DESC
            LIMIT 10
        """)
        top_psalms_curated = cursor.fetchall()

        # By tradition (curated only)
        cursor.execute("""
            SELECT nusach, COUNT(*) as count
            FROM sefaria_liturgy_links
            WHERE nusach IS NOT NULL AND link_type = 'quotation'
            GROUP BY nusach
            ORDER BY count DESC
        """)
        by_tradition = cursor.fetchall()

        # By occasion (curated only)
        cursor.execute("""
            SELECT occasion, COUNT(*) as count
            FROM sefaria_liturgy_links
            WHERE occasion IS NOT NULL AND link_type = 'quotation'
            GROUP BY occasion
            ORDER BY count DESC
        """)
        by_occasion = cursor.fetchall()

        conn.close()

        return {
            'total_links': total_links,
            'curated_links': curated_links,
            'by_link_type': by_link_type,
            'psalms_with_curated': psalms_with_curated,
            'psalms_with_links': psalms_with_links,
            'psalms_total': 150,
            'curated_coverage_percent': round(100 * psalms_with_curated / 150, 1),
            'top_psalms_curated': top_psalms_curated,
            'by_tradition': by_tradition,
            'by_occasion': by_occasion
        }


# CLI for testing
def main():
    """Command-line interface for testing."""
    import sys

    librarian = SefariaLiturgicalLibrarian()

    # Display statistics
    print("\n" + "=" * 70)
    print("LITURGICAL LIBRARIAN (SEFARIA BOOTSTRAP)")
    print("=" * 70)

    stats = librarian.get_statistics()
    print(f"\nDatabase Statistics:")
    print(f"  Total links in database: {stats['total_links']:,}")
    print(f"  Manually curated (quotation): {stats['curated_links']:,}")

    print(f"\n  By Link Type:")
    for link_type, count in stats['by_link_type']:
        type_display = link_type if link_type else "(empty)"
        print(f"    {type_display}: {count:,}")

    print(f"\n  Psalms with curated links: {stats['psalms_with_curated']}/{stats['psalms_total']} ({stats['curated_coverage_percent']}%)")
    print(f"  Psalms with any links: {stats['psalms_with_links']}/{stats['psalms_total']}")

    print(f"\n  Top 10 Psalms by curated liturgical usage:")
    for psalm, count in stats['top_psalms_curated']:
        print(f"    Psalm {psalm:3d}: {count:3d} curated links")

    if stats['by_tradition']:
        print(f"\n  By Tradition (curated only):")
        for tradition, count in stats['by_tradition']:
            print(f"    {tradition}: {count:,} links")

    if stats['by_occasion']:
        print(f"\n  By Occasion (curated only):")
        for occasion, count in stats['by_occasion']:
            print(f"    {occasion}: {count:,} links")

    # Test with specific Psalm if provided
    if len(sys.argv) > 1:
        psalm_num = int(sys.argv[1])
        print("\n" + "=" * 70)
        print(f"LITURGICAL USAGE FOR PSALM {psalm_num} (CURATED ONLY)")
        print("=" * 70)

        links = librarian.find_liturgical_usage(psalm_num)  # curated_only=True by default

        if links:
            print(f"\nFound {len(links)} manually curated liturgical context(s):\n")
            for i, link in enumerate(links, 1):
                print(f"{i}. {link.format_location()}")
                print(f"   Verses: {link.format_verse_range()}")
                print(f"   Reference: {link.liturgy_ref}")
                if link.nusach:
                    print(f"   Tradition: {link.nusach}")
                print()
        else:
            print("\nNo liturgical usage found for this Psalm.")

        # Show research bundle format
        print("\n" + "-" * 70)
        print("RESEARCH BUNDLE FORMAT:")
        print("-" * 70)
        print(librarian.format_for_research_bundle(links))

    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
