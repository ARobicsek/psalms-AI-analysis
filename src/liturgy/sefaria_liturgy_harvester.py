"""
Sefaria Liturgy Harvester - Phase 2

Harvests complete liturgical texts from Sefaria API:
- Siddurim (daily/weekly prayer books)
- Machzorim (High Holiday prayer books)
- Haggadot (Passover seder texts)

Usage:
    from src.liturgy.sefaria_liturgy_harvester import SefariaLiturgyHarvester

    harvester = SefariaLiturgyHarvester()
    harvester.harvest_priority_1()  # 3 Siddurim
    harvester.harvest_priority_2()  # 4 Machzorim
"""

import requests
import sqlite3
import time
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class SefariaLiturgyHarvester:
    """Harvest liturgical texts from Sefaria API."""

    BASE_URL = "https://www.sefaria.org/api"
    RATE_LIMIT_DELAY = 1.0  # seconds between requests

    # Priority 1: Siddurim (daily/weekly prayer)
    PRIORITY_1_SOURCES = [
        ("Siddur Ashkenaz", "Ashkenaz", "Siddur"),
        ("Siddur Sefard", "Sefard", "Siddur"),
        ("Siddur Edot HaMizrach", "Edot_HaMizrach", "Siddur"),
    ]

    # Priority 2: Machzorim (High Holidays)
    PRIORITY_2_SOURCES = [
        ("Machzor Rosh Hashanah Ashkenaz", "Ashkenaz", "Machzor"),
        ("Machzor Rosh Hashanah Edot HaMizrach", "Edot_HaMizrach", "Machzor"),
        ("Machzor Yom Kippur Ashkenaz", "Ashkenaz", "Machzor"),
        ("Machzor Yom Kippur Edot HaMizrach", "Edot_HaMizrach", "Machzor"),
    ]

    def __init__(self, db_path: str = "data/liturgy.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.prayers_harvested = 0
        self.errors = []

    def harvest_priority_1(self):
        """Harvest Priority 1: 3 Siddurim."""
        print("\n" + "=" * 70)
        print("PHASE 2: HARVESTING PRIORITY 1 SOURCES (SIDDURIM)")
        print("=" * 70)

        for source_text, nusach, prayer_type in self.PRIORITY_1_SOURCES:
            try:
                self.harvest_text(source_text, nusach, prayer_type)
            except Exception as e:
                error_msg = f"Failed to harvest {source_text}: {e}"
                print(f"\n[ERROR] {error_msg}")
                self.errors.append(error_msg)
                self._log_harvest("failed", source_text, None, str(e))

        self._print_summary("PRIORITY 1")

    def harvest_priority_2(self):
        """Harvest Priority 2: 4 Machzorim."""
        print("\n" + "=" * 70)
        print("PHASE 2: HARVESTING PRIORITY 2 SOURCES (MACHZORIM)")
        print("=" * 70)

        for source_text, nusach, prayer_type in self.PRIORITY_2_SOURCES:
            try:
                self.harvest_text(source_text, nusach, prayer_type)
            except Exception as e:
                error_msg = f"Failed to harvest {source_text}: {e}"
                print(f"\n[ERROR] {error_msg}")
                self.errors.append(error_msg)
                self._log_harvest("failed", source_text, None, str(e))

        self._print_summary("PRIORITY 2")

    def harvest_text(
        self,
        source_text: str,
        nusach: str,
        prayer_type: str
    ):
        """
        Harvest complete liturgical text from Sefaria.

        Args:
            source_text: Name in Sefaria API (e.g., "Siddur Ashkenaz")
            nusach: Tradition (Ashkenaz, Sefard, Edot_HaMizrach)
            prayer_type: Type (Siddur, Machzor, Haggadah)
        """

        print(f"\n{'='*70}")
        print(f"Harvesting: {source_text}")
        print(f"Nusach: {nusach} | Type: {prayer_type}")
        print(f"{'='*70}")

        # Get table of contents to understand structure
        toc = self.get_table_of_contents(source_text)

        if not toc:
            raise ValueError(f"Failed to retrieve TOC for {source_text}")

        # Traverse structure recursively
        self._traverse_structure(
            source_text=source_text,
            structure=toc,
            nusach=nusach,
            prayer_type=prayer_type,
            path_components=[],
            occasion=None,
            service=None,
            section=None,
            sequence_order=0
        )

    def get_table_of_contents(self, text_name: str) -> Optional[Dict]:
        """
        Fetch table of contents for a liturgical text.

        Returns:
            TOC structure or None if failed
        """

        try:
            # Try v3 API first
            url = f"{self.BASE_URL}/v3/texts/{text_name.replace(' ', '_')}"
            response = self.session.get(url)

            if response.status_code == 200:
                return response.json()

            # Fall back to v2
            url = f"{self.BASE_URL}/v2/index/{text_name.replace(' ', '_')}"
            response = self.session.get(url)

            if response.status_code == 200:
                return response.json()

            print(f"   [WARNING] Failed to get TOC: HTTP {response.status_code}")
            return None

        except Exception as e:
            print(f"   [WARNING] Exception getting TOC: {e}")
            return None

    def get_text(self, ref: str) -> Optional[Dict]:
        """
        Fetch specific liturgical text from Sefaria.

        Args:
            ref: Sefaria reference (e.g., "Siddur Ashkenaz, Weekday, Shacharit, Pesukei Dezimrah, Ashrei 1")

        Returns:
            Text data or None if failed
        """

        try:
            # URL-encode the reference
            encoded_ref = ref.replace(" ", "_")
            url = f"{self.BASE_URL}/texts/{encoded_ref}"

            response = self.session.get(url)
            time.sleep(self.RATE_LIMIT_DELAY)

            if response.status_code == 200:
                return response.json()

            print(f"   [WARNING] Failed to get text '{ref}': HTTP {response.status_code}")
            return None

        except Exception as e:
            print(f"   [WARNING] Exception getting text '{ref}': {e}")
            return None

    def _traverse_structure(
        self,
        source_text: str,
        structure: Dict,
        nusach: str,
        prayer_type: str,
        path_components: List[str],
        occasion: Optional[str],
        service: Optional[str],
        section: Optional[str],
        sequence_order: int
    ):
        """
        Recursively traverse Sefaria's nested structure.

        Sefaria organizes texts hierarchically:
        - Siddur Ashkenaz
          - Weekday
            - Shacharit
              - Pesukei Dezimrah
                - Ashrei
                  - Verse 1, 2, 3, ...

        We need to traverse this tree and extract the actual text at the leaves.
        """

        # Check if this is a text node (has 'he' Hebrew text)
        if 'he' in structure or 'text' in structure:
            # This is a leaf node with actual text
            self._store_prayer(
                source_text=source_text,
                path_components=path_components,
                structure=structure,
                nusach=nusach,
                prayer_type=prayer_type,
                occasion=occasion,
                service=service,
                section=section,
                sequence_order=sequence_order
            )
            return

        # Check for 'schema' (v2 API)
        if 'schema' in structure:
            self._traverse_schema(
                source_text=source_text,
                schema=structure['schema'],
                nusach=nusach,
                prayer_type=prayer_type,
                path_components=path_components,
                occasion=occasion,
                service=service,
                section=section,
                sequence_order=sequence_order
            )

        # Check for 'nodes' (nested structure)
        if 'nodes' in structure:
            for i, node in enumerate(structure['nodes']):
                node_title = node.get('title', node.get('heTitle', f'Node{i}'))

                # Update context based on title
                new_occasion = self._infer_occasion(node_title) or occasion
                new_service = self._infer_service(node_title) or service
                new_section = self._infer_section(node_title) or section

                # Recurse
                self._traverse_structure(
                    source_text=source_text,
                    structure=node,
                    nusach=nusach,
                    prayer_type=prayer_type,
                    path_components=path_components + [node_title],
                    occasion=new_occasion,
                    service=new_service,
                    section=new_section,
                    sequence_order=sequence_order + i
                )

    def _traverse_schema(
        self,
        source_text: str,
        schema: Dict,
        nusach: str,
        prayer_type: str,
        path_components: List[str],
        occasion: Optional[str],
        service: Optional[str],
        section: Optional[str],
        sequence_order: int
    ):
        """Traverse schema structure (v2 API format)."""

        # Similar logic to _traverse_structure but for schema format
        if 'nodes' in schema:
            for i, node in enumerate(schema['nodes']):
                node_title = node.get('title', f'SchemaNode{i}')

                # Update context
                new_occasion = self._infer_occasion(node_title) or occasion
                new_service = self._infer_service(node_title) or service
                new_section = self._infer_section(node_title) or section

                # If this node has a key, fetch the actual text
                if 'key' in node:
                    ref = f"{source_text}, {', '.join(path_components + [node_title])}"
                    text_data = self.get_text(ref)

                    if text_data:
                        self._store_prayer(
                            source_text=source_text,
                            path_components=path_components + [node_title],
                            structure=text_data,
                            nusach=nusach,
                            prayer_type=prayer_type,
                            occasion=new_occasion,
                            service=new_service,
                            section=new_section,
                            sequence_order=sequence_order + i
                        )

                # Recurse if there are child nodes
                if 'nodes' in node:
                    self._traverse_schema(
                        source_text=source_text,
                        schema=node,
                        nusach=nusach,
                        prayer_type=prayer_type,
                        path_components=path_components + [node_title],
                        occasion=new_occasion,
                        service=new_service,
                        section=new_section,
                        sequence_order=sequence_order + i
                    )

    def _store_prayer(
        self,
        source_text: str,
        path_components: List[str],
        structure: Dict,
        nusach: str,
        prayer_type: str,
        occasion: Optional[str],
        service: Optional[str],
        section: Optional[str],
        sequence_order: int
    ):
        """Store a single prayer text in the database."""

        # Build Sefaria reference
        sefaria_ref = f"{source_text}, {', '.join(path_components)}"

        # Extract Hebrew and English text
        hebrew_text = self._extract_text(structure, 'he')
        english_text = self._extract_text(structure, 'text')

        if not hebrew_text:
            print(f"   [SKIP] No Hebrew text: {sefaria_ref}")
            return

        # Prayer name is the last component
        prayer_name = path_components[-1] if path_components else None

        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO prayers (
                    source_text, sefaria_ref, nusach, prayer_type,
                    occasion, service, section, prayer_name,
                    hebrew_text, english_text, sequence_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source_text, sefaria_ref, nusach, prayer_type,
                occasion, service, section, prayer_name,
                hebrew_text, english_text, sequence_order
            ))

            conn.commit()
            self.prayers_harvested += 1

            print(f"   [OK] Stored: {sefaria_ref} ({len(hebrew_text)} chars)")

            # Log success
            self._log_harvest("success", source_text, sefaria_ref, None)

        except sqlite3.IntegrityError:
            print(f"   [SKIP] Already exists: {sefaria_ref}")

        except Exception as e:
            error_msg = f"Database error: {e}"
            print(f"   [ERROR] {sefaria_ref}: {error_msg}")
            self.errors.append(error_msg)
            self._log_harvest("failed", source_text, sefaria_ref, str(e))

        finally:
            conn.close()

    def _extract_text(self, structure: Dict, key: str) -> str:
        """
        Extract text from Sefaria structure.

        Sefaria returns text in various formats:
        - Simple string: "text"
        - List of strings: ["line1", "line2"]
        - Nested lists: [["para1_line1"], ["para2_line1"]]
        """

        text = structure.get(key, '')

        if isinstance(text, str):
            return text.strip()

        if isinstance(text, list):
            return self._flatten_text_list(text)

        return ''

    def _flatten_text_list(self, text_list: List) -> str:
        """Recursively flatten nested text lists."""

        result = []

        for item in text_list:
            if isinstance(item, str):
                result.append(item.strip())
            elif isinstance(item, list):
                result.append(self._flatten_text_list(item))

        return ' '.join(result)

    def _infer_occasion(self, title: str) -> Optional[str]:
        """Infer occasion from section title."""
        title_lower = title.lower()

        if 'weekday' in title_lower:
            return 'Weekday'
        elif 'shabbat' in title_lower or 'sabbath' in title_lower:
            return 'Shabbat'
        elif 'rosh hashanah' in title_lower:
            return 'Rosh_Hashanah'
        elif 'yom kippur' in title_lower:
            return 'Yom_Kippur'
        elif 'sukkot' in title_lower:
            return 'Sukkot'
        elif 'pesach' in title_lower or 'passover' in title_lower:
            return 'Pesach'

        return None

    def _infer_service(self, title: str) -> Optional[str]:
        """Infer service from section title."""
        title_lower = title.lower()

        if 'shacharit' in title_lower or 'morning' in title_lower:
            return 'Shacharit'
        elif 'mincha' in title_lower or 'afternoon' in title_lower:
            return 'Mincha'
        elif 'maariv' in title_lower or 'evening' in title_lower:
            return 'Maariv'
        elif 'musaf' in title_lower:
            return 'Musaf'
        elif 'neilah' in title_lower:
            return 'Neilah'

        return None

    def _infer_section(self, title: str) -> Optional[str]:
        """Infer section from title."""
        title_lower = title.lower()

        if 'pesukei' in title_lower or 'dezimrah' in title_lower:
            return 'Pesukei_DZimrah'
        elif 'shema' in title_lower:
            return 'Shema'
        elif 'amidah' in title_lower or 'shemoneh esrei' in title_lower:
            return 'Amidah'
        elif 'tachanun' in title_lower:
            return 'Tachanun'
        elif 'hallel' in title_lower:
            return 'Hallel'
        elif 'kabbalat shabbat' in title_lower:
            return 'Kabbalat_Shabbat'
        elif 'selichot' in title_lower:
            return 'Selichot'
        elif 'torah reading' in title_lower:
            return 'Torah_Reading'

        return None

    def _log_harvest(
        self,
        status: str,
        source_text: str,
        sefaria_ref: Optional[str],
        error_message: Optional[str]
    ):
        """Log harvest attempt to harvest_log table."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO harvest_log (source_text, sefaria_ref, status, error_message)
            VALUES (?, ?, ?, ?)
        """, (source_text, sefaria_ref, status, error_message))

        conn.commit()
        conn.close()

    def _print_summary(self, priority_label: str):
        """Print harvest summary."""

        print(f"\n{'='*70}")
        print(f"{priority_label} HARVEST COMPLETE")
        print(f"{'='*70}")
        print(f"Prayers harvested: {self.prayers_harvested}")
        print(f"Errors: {len(self.errors)}")

        if self.errors:
            print("\nErrors encountered:")
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"  - {error}")


if __name__ == "__main__":
    # Test harvester
    harvester = SefariaLiturgyHarvester()

    print("Testing Sefaria Liturgy Harvester...")
    print("This will attempt to harvest liturgical texts from Sefaria.\n")

    # For testing, just try one source
    try:
        harvester.harvest_text("Siddur Ashkenaz", "Ashkenaz", "Siddur")
        print(f"\n[OK] Test successful: {harvester.prayers_harvested} prayers harvested")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
