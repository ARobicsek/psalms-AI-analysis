"""
Sefaria Links Harvester - Phase 0 Bootstrap

Harvests existing Psalms→Liturgy cross-references from Sefaria's curated database.
This provides immediate value (70-80% coverage) before building the full phrase-level index.

Usage:
    python -m src.liturgy.sefaria_links_harvester
"""

import requests
import sqlite3
import re
import time
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class SefariaLinksHarvester:
    """Harvest existing Psalms→Liturgy links from Sefaria API."""

    BASE_URL = "https://www.sefaria.org/api"

    def __init__(self, db_path: str = "data/liturgy.db"):
        self.db_path = db_path
        self._ensure_database()

    def _ensure_database(self):
        """Ensure database and table exist."""

        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create table for Sefaria links
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sefaria_liturgy_links (
                link_id INTEGER PRIMARY KEY AUTOINCREMENT,
                psalm_chapter INTEGER NOT NULL,
                psalm_verse_start INTEGER,
                psalm_verse_end INTEGER,
                liturgy_ref TEXT NOT NULL,
                collective_title TEXT,
                link_type TEXT,
                nusach TEXT,
                occasion TEXT,
                service TEXT,
                section TEXT,
                confidence REAL,
                source TEXT DEFAULT 'sefaria_api',
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create index for efficient lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_psalm_lookup
            ON sefaria_liturgy_links (psalm_chapter, psalm_verse_start)
        """)

        conn.commit()
        conn.close()

    def harvest_all_psalms_links(self):
        """Harvest liturgical links for all 150 Psalms."""

        print("=" * 70)
        print("SEFARIA LITURGICAL LINKS HARVESTER")
        print("=" * 70)
        print("\nHarvesting Sefaria cross-references for all 150 Psalms...")
        print("This will take ~5-10 minutes due to rate limiting.\n")

        total_links = 0
        psalms_with_links = 0

        for psalm_num in range(1, 151):
            try:
                links = self.get_liturgical_links(psalm_num)

                if links:
                    print(f"Psalm {psalm_num:3d}: Found {len(links):2d} liturgical link(s)")
                    self._store_links(links)
                    total_links += len(links)
                    psalms_with_links += 1
                else:
                    print(f"Psalm {psalm_num:3d}: No liturgical links")

                # Rate limiting: be respectful of Sefaria's API
                time.sleep(0.5)

            except Exception as e:
                print(f"Psalm {psalm_num:3d}: ERROR - {e}")

        print("\n" + "=" * 70)
        print(f"✓ Harvesting complete!")
        print(f"  - Total links: {total_links}")
        print(f"  - Psalms with liturgical usage: {psalms_with_links}/150")
        print(f"  - Database: {self.db_path}")
        print("=" * 70)

    def get_liturgical_links(self, psalm_chapter: int) -> List[Dict]:
        """
        Fetch all liturgical links for a Psalm chapter.

        Returns list of link objects with parsed metadata.
        """

        # Query the /related/ endpoint for entire chapter
        ref = f"Psalms.{psalm_chapter}"
        url = f"{self.BASE_URL}/related/{ref}"

        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Filter for liturgical links
        liturgical_links = []

        for link in data.get('links', []):
            category = link.get('category', '')

            if category == 'Liturgy':
                parsed = self._parse_link(link, psalm_chapter)
                if parsed:
                    liturgical_links.append(parsed)

        return liturgical_links

    def _parse_link(self, link: Dict, psalm_chapter: int) -> Optional[Dict]:
        """
        Parse a Sefaria link into structured data.

        Returns None if link cannot be parsed.
        """

        try:
            # Extract basic fields
            liturgy_ref = link.get('ref', '')
            source_ref = link.get('sourceRef', '')
            link_type = link.get('type', 'quotation')
            collective_title = link.get('collectiveTitle', {})

            if isinstance(collective_title, dict):
                collective_title = collective_title.get('en', '')

            # Parse source_ref to extract verse range
            # Format: "Psalms 23:1-6" or "Psalms 145:3"
            verse_start, verse_end = self._parse_verse_range(source_ref)

            # Infer metadata from liturgy_ref
            nusach = self._infer_nusach(liturgy_ref)
            occasion = self._infer_occasion(liturgy_ref)
            service = self._infer_service(liturgy_ref)
            section = self._infer_section(liturgy_ref)

            return {
                'psalm_chapter': psalm_chapter,
                'psalm_verse_start': verse_start,
                'psalm_verse_end': verse_end,
                'liturgy_ref': liturgy_ref,
                'collective_title': collective_title,
                'link_type': link_type,
                'nusach': nusach,
                'occasion': occasion,
                'service': service,
                'section': section,
                'source': 'sefaria_api',
                'confidence': 1.0 if link_type == 'quotation' else 0.95
            }

        except Exception as e:
            print(f"  Warning: Could not parse link - {e}")
            return None

    def _parse_verse_range(self, source_ref: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Parse verse range from sourceRef.

        Examples:
        - "Psalms 23:1-6" → (1, 6)
        - "Psalms 145:3" → (3, 3)
        - "Psalms 119" → (None, None)  # Entire chapter
        """

        # Pattern: "Psalms X:Y" or "Psalms X:Y-Z"
        match = re.search(r'Psalms \d+:(\d+)(?:-(\d+))?', source_ref)

        if match:
            verse_start = int(match.group(1))
            verse_end = int(match.group(2)) if match.group(2) else verse_start
            return verse_start, verse_end

        # No verse specified = entire chapter
        return None, None

    def _infer_nusach(self, liturgy_ref: str) -> Optional[str]:
        """Infer nusach (liturgical tradition) from liturgy reference."""
        ref_lower = liturgy_ref.lower()

        if 'ashkenaz' in ref_lower:
            return 'Ashkenaz'
        elif 'sefard' in ref_lower:
            return 'Sefard'
        elif 'edot hamizrach' in ref_lower or 'edot mizrach' in ref_lower:
            return 'Edot_HaMizrach'

        return None

    def _infer_occasion(self, liturgy_ref: str) -> Optional[str]:
        """Infer occasion from liturgy reference."""
        ref_lower = liturgy_ref.lower()

        if 'weekday' in ref_lower:
            return 'Weekday'
        elif 'shabbat' in ref_lower or 'sabbath' in ref_lower:
            return 'Shabbat'
        elif 'rosh hashanah' in ref_lower:
            return 'Rosh_Hashanah'
        elif 'yom kippur' in ref_lower:
            return 'Yom_Kippur'
        elif 'sukkot' in ref_lower:
            return 'Sukkot'
        elif 'pesach' in ref_lower or 'passover' in ref_lower:
            return 'Pesach'
        elif 'shavuot' in ref_lower:
            return 'Shavuot'

        return None

    def _infer_service(self, liturgy_ref: str) -> Optional[str]:
        """Infer service from liturgy reference."""
        ref_lower = liturgy_ref.lower()

        if 'shacharit' in ref_lower or 'morning' in ref_lower:
            return 'Shacharit'
        elif 'mincha' in ref_lower or 'afternoon' in ref_lower:
            return 'Mincha'
        elif 'maariv' in ref_lower or 'evening' in ref_lower:
            return 'Maariv'
        elif 'musaf' in ref_lower:
            return 'Musaf'

        return None

    def _infer_section(self, liturgy_ref: str) -> Optional[str]:
        """Infer section from liturgy reference."""
        ref_lower = liturgy_ref.lower()

        if 'pesukei' in ref_lower or 'zimrah' in ref_lower:
            return 'Pesukei_DZimrah'
        elif 'hallel' in ref_lower:
            return 'Hallel'
        elif 'kabbalat shabbat' in ref_lower:
            return 'Kabbalat_Shabbat'
        elif 'selichot' in ref_lower:
            return 'Selichot'
        elif 'tashlich' in ref_lower:
            return 'Tashlich'

        return None

    def _store_links(self, links: List[Dict]):
        """Store links in database."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Insert links
        for link in links:
            cursor.execute("""
                INSERT INTO sefaria_liturgy_links (
                    psalm_chapter, psalm_verse_start, psalm_verse_end,
                    liturgy_ref, collective_title, link_type,
                    nusach, occasion, service, section, confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                link['psalm_chapter'],
                link['psalm_verse_start'],
                link['psalm_verse_end'],
                link['liturgy_ref'],
                link['collective_title'],
                link['link_type'],
                link['nusach'],
                link['occasion'],
                link['service'],
                link['section'],
                link['confidence']
            ))

        conn.commit()
        conn.close()


# CLI
def main():
    """Command-line interface for harvesting."""
    harvester = SefariaLinksHarvester()
    harvester.harvest_all_psalms_links()


if __name__ == "__main__":
    main()
