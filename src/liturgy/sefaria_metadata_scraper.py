"""
Sefaria Metadata Scraper

Collects complete liturgical hierarchy and metadata from Sefaria API.
Even without full text access, this provides:
- Complete liturgical structure (occasions, services, sections)
- Prayer names and their contexts
- Where each prayer appears across different nusachim

This metadata is valuable for:
1. Understanding liturgical organization
2. Knowing which contexts to search when we build phrase index
3. Validation dataset for our phrase detection

Usage:
    python src/liturgy/sefaria_metadata_scraper.py
"""

import requests
import sqlite3
import json
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class SefariaMetadataScraper:
    """Scrape liturgical hierarchy and metadata from Sefaria API."""

    BASE_URL = "https://www.sefaria.org/api"
    RATE_LIMIT_DELAY = 1.0

    # All liturgical sources available on Sefaria
    LITURGICAL_SOURCES = [
        ("Siddur Ashkenaz", "Ashkenaz", "Siddur"),
        ("Siddur Sefard", "Sefard", "Siddur"),
        ("Siddur Edot HaMizrach", "Edot_HaMizrach", "Siddur"),
        ("Machzor Rosh Hashanah Ashkenaz", "Ashkenaz", "Machzor"),
        ("Machzor Rosh Hashanah Edot HaMizrach", "Edot_HaMizrach", "Machzor"),
        ("Machzor Yom Kippur Ashkenaz", "Ashkenaz", "Machzor"),
        ("Machzor Yom Kippur Edot HaMizrach", "Edot_HaMizrach", "Machzor"),
        ("Pesach Haggadah", "Universal", "Haggadah"),
    ]

    def __init__(self, db_path: str = "data/liturgy.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.metadata_collected = 0

    def scrape_all_sources(self):
        """Scrape metadata from all liturgical sources."""

        print("\n" + "=" * 70)
        print("SEFARIA METADATA SCRAPER")
        print("Collecting liturgical hierarchy and prayer names from all sources")
        print("=" * 70)

        for source_text, nusach, prayer_type in self.LITURGICAL_SOURCES:
            print(f"\n{'='*70}")
            print(f"Source: {source_text}")
            print(f"Nusach: {nusach} | Type: {prayer_type}")
            print(f"{'='*70}\n")

            try:
                toc = self.get_table_of_contents(source_text)

                if toc and 'schema' in toc:
                    self._scrape_schema(
                        source_text=source_text,
                        schema=toc['schema'],
                        nusach=nusach,
                        prayer_type=prayer_type,
                        path=[],
                        occasion=None,
                        service=None,
                        section=None,
                        sequence_order=0
                    )
                else:
                    print(f"   [WARNING] No schema found for {source_text}")

            except Exception as e:
                print(f"   [ERROR] Failed to scrape {source_text}: {e}")

            time.sleep(self.RATE_LIMIT_DELAY)

        print(f"\n{'='*70}")
        print(f"SCRAPING COMPLETE")
        print(f"{'='*70}")
        print(f"Metadata entries collected: {self.metadata_collected}")

    def get_table_of_contents(self, text_name: str) -> Optional[Dict]:
        """Fetch TOC for a liturgical text."""

        try:
            url = f"{self.BASE_URL}/v2/index/{text_name.replace(' ', '_')}"
            response = self.session.get(url)

            if response.status_code == 200:
                return response.json()

            print(f"   [WARNING] TOC request failed: HTTP {response.status_code}")
            return None

        except Exception as e:
            print(f"   [ERROR] Exception getting TOC: {e}")
            return None

    def _scrape_schema(
        self,
        source_text: str,
        schema: Dict,
        nusach: str,
        prayer_type: str,
        path: List[str],
        occasion: Optional[str],
        service: Optional[str],
        section: Optional[str],
        sequence_order: int
    ):
        """
        Recursively scrape schema structure.

        Collects:
        - Prayer names and their hierarchical location
        - Occasion, service, section context
        - Sequence order
        """

        # If this is a leaf node (has 'key' but no 'nodes'), store it
        if 'key' in schema and 'nodes' not in schema:
            title = schema.get('title', schema.get('key', 'Unknown'))
            key = schema.get('key')

            # Build full Sefaria reference path
            sefaria_ref = f"{source_text}, {', '.join(path + [title])}" if path else f"{source_text}, {title}"

            # Store metadata
            self._store_prayer_metadata(
                source_text=source_text,
                sefaria_ref=sefaria_ref,
                prayer_name=title,
                prayer_key=key,
                nusach=nusach,
                prayer_type=prayer_type,
                occasion=occasion,
                service=service,
                section=section,
                path_depth=len(path) + 1,
                sequence_order=sequence_order
            )

            print(f"   [OK] {sefaria_ref}")
            return

        # If this has child nodes, traverse them
        if 'nodes' in schema:
            for i, node in enumerate(schema['nodes']):
                node_title = node.get('title', node.get('key', f'Node{i}'))

                # Infer context from title
                new_occasion = self._infer_occasion(node_title) or occasion
                new_service = self._infer_service(node_title) or service
                new_section = self._infer_section(node_title) or section

                # Recurse
                self._scrape_schema(
                    source_text=source_text,
                    schema=node,
                    nusach=nusach,
                    prayer_type=prayer_type,
                    path=path + [node_title],
                    occasion=new_occasion,
                    service=new_service,
                    section=new_section,
                    sequence_order=sequence_order + i
                )

    def _store_prayer_metadata(
        self,
        source_text: str,
        sefaria_ref: str,
        prayer_name: str,
        prayer_key: str,
        nusach: str,
        prayer_type: str,
        occasion: Optional[str],
        service: Optional[str],
        section: Optional[str],
        path_depth: int,
        sequence_order: int
    ):
        """Store prayer metadata in prayers table (without text)."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Store with empty text fields - we'll mark this as metadata-only
            cursor.execute("""
                INSERT INTO prayers (
                    source_text, sefaria_ref, nusach, prayer_type,
                    occasion, service, section, prayer_name,
                    hebrew_text, english_text, sequence_order, liturgical_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source_text, sefaria_ref, nusach, prayer_type,
                occasion, service, section, prayer_name,
                '', '',  # Empty text fields
                sequence_order,
                f"Metadata only (depth={path_depth}, key={prayer_key})"
            ))

            conn.commit()
            self.metadata_collected += 1

        except sqlite3.IntegrityError:
            # Already exists - skip
            pass

        except Exception as e:
            print(f"   [ERROR] Database error for {sefaria_ref}: {e}")

        finally:
            conn.close()

    def _infer_occasion(self, title: str) -> Optional[str]:
        """Infer occasion from title."""
        title_lower = title.lower()

        occasions = {
            'weekday': 'Weekday',
            'shabbat': 'Shabbat',
            'sabbath': 'Shabbat',
            'rosh hashanah': 'Rosh_Hashanah',
            'yom kippur': 'Yom_Kippur',
            'sukkot': 'Sukkot',
            'pesach': 'Pesach',
            'passover': 'Pesach',
            'shavuot': 'Shavuot',
            'chanukah': 'Chanukah',
            'purim': 'Purim',
            'rosh chodesh': 'Rosh_Chodesh',
            'festivals': 'Festivals',
        }

        for keyword, occasion in occasions.items():
            if keyword in title_lower:
                return occasion

        return None

    def _infer_service(self, title: str) -> Optional[str]:
        """Infer service from title."""
        title_lower = title.lower()

        services = {
            'shacharit': 'Shacharit',
            'morning': 'Shacharit',
            'mincha': 'Mincha',
            'afternoon': 'Mincha',
            'maariv': 'Maariv',
            'evening': 'Maariv',
            'arvit': 'Maariv',
            'musaf': 'Musaf',
            'neilah': 'Neilah',
        }

        for keyword, service in services.items():
            if keyword in title_lower:
                return service

        return None

    def _infer_section(self, title: str) -> Optional[str]:
        """Infer section from title."""
        title_lower = title.lower()

        sections = {
            'pesukei': 'Pesukei_DZimrah',
            'dezimra': 'Pesukei_DZimrah',
            'shema': 'Shema',
            'kriat shema': 'Shema',
            'amidah': 'Amidah',
            'shemoneh esrei': 'Amidah',
            'tachanun': 'Tachanun',
            'hallel': 'Hallel',
            'kabbalat shabbat': 'Kabbalat_Shabbat',
            'selichot': 'Selichot',
            'torah reading': 'Torah_Reading',
            'kiddush': 'Kiddush',
            'havdalah': 'Havdalah',
        }

        for keyword, section in sections.items():
            if keyword in title_lower:
                return section

        return None

    def print_summary(self):
        """Print summary of collected metadata."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        print("\n" + "=" * 70)
        print("METADATA SUMMARY")
        print("=" * 70)

        # Total prayers
        cursor.execute("SELECT COUNT(*) FROM prayers")
        total = cursor.fetchone()[0]
        print(f"\nTotal prayer entries: {total}")

        # By source
        print("\nBy source:")
        cursor.execute("""
            SELECT source_text, COUNT(*)
            FROM prayers
            GROUP BY source_text
            ORDER BY COUNT(*) DESC
        """)
        for source, count in cursor.fetchall():
            print(f"  {source}: {count}")

        # By nusach
        print("\nBy nusach:")
        cursor.execute("""
            SELECT nusach, COUNT(*)
            FROM prayers
            GROUP BY nusach
            ORDER BY COUNT(*) DESC
        """)
        for nusach, count in cursor.fetchall():
            print(f"  {nusach}: {count}")

        # By service
        print("\nBy service (where specified):")
        cursor.execute("""
            SELECT service, COUNT(*)
            FROM prayers
            WHERE service IS NOT NULL
            GROUP BY service
            ORDER BY COUNT(*) DESC
        """)
        for service, count in cursor.fetchall():
            print(f"  {service}: {count}")

        # By section
        print("\nBy section (where specified):")
        cursor.execute("""
            SELECT section, COUNT(*)
            FROM prayers
            WHERE section IS NOT NULL
            GROUP BY section
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        for section, count in cursor.fetchall():
            print(f"  {section}: {count}")

        conn.close()


if __name__ == "__main__":
    scraper = SefariaMetadataScraper()
    scraper.scrape_all_sources()
    scraper.print_summary()
