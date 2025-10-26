"""
Sefaria JSON Parser - Extract liturgical texts from Sefaria-Export JSON files
Parses hierarchical JSON structure and matches to database sefaria_ref entries

Created: 2025-10-26 (Session 28 - Liturgical Librarian Phase 2)
"""

import json
import sqlite3
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ParsedPrayer:
    """Represents a parsed prayer entry from JSON"""
    source_text: str
    sefaria_ref: str
    hebrew_text: str
    path_components: List[str]


class SefariaJSONParser:
    """Parse Sefaria-Export JSON files and extract liturgical texts"""

    def __init__(self, json_dir: Path, db_path: Path):
        self.json_dir = Path(json_dir)
        self.db_path = Path(db_path)
        self.parsed_prayers: List[ParsedPrayer] = []
        self.stats = {
            'files_processed': 0,
            'prayers_extracted': 0,
            'prayers_matched': 0,
            'prayers_updated': 0,
            'errors': []
        }

    def clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        if not text:
            return ""
        # Remove HTML tags but preserve content
        text = re.sub(r'<[^>]+>', '', text)
        # Normalize whitespace
        text = ' '.join(text.split())
        return text

    def parse_json_file(self, json_path: Path, source_name: str) -> List[ParsedPrayer]:
        """
        Parse a single JSON file and extract all prayers

        Args:
            json_path: Path to the JSON file
            source_name: Source identifier (e.g., 'Siddur Ashkenaz')

        Returns:
            List of ParsedPrayer objects
        """
        print(f"\nParsing {source_name}...")

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        title = data.get('title', source_name)
        text_root = data.get('text', {})

        prayers = []

        # Recursively traverse the text hierarchy
        def traverse(node: Any, path: List[str]) -> None:
            """Recursively traverse JSON structure and extract text"""

            if isinstance(node, list):
                # Leaf node - this is actual prayer text
                if node and isinstance(node[0], str):
                    # Build sefaria_ref from path
                    # Format: "Source, Level1, Level2, ..., LeafName, LeafName"
                    # The leaf name appears twice in the database refs
                    if path:
                        last_component = path[-1]
                        full_path = [title] + path + [last_component]
                        sefaria_ref = ', '.join(full_path)

                        # Combine all verses into single text
                        hebrew_verses = [self.clean_html(v) for v in node if v]
                        hebrew_text = ' '.join(hebrew_verses)

                        if hebrew_text:
                            prayers.append(ParsedPrayer(
                                source_text=source_name,
                                sefaria_ref=sefaria_ref,
                                hebrew_text=hebrew_text,
                                path_components=path.copy()
                            ))

            elif isinstance(node, dict):
                # Intermediate node - recurse into children
                for key, value in node.items():
                    traverse(value, path + [key])

            elif isinstance(node, str):
                # Sometimes a single string (rare)
                if node.strip():
                    if path:
                        last_component = path[-1]
                        full_path = [title] + path + [last_component]
                        sefaria_ref = ', '.join(full_path)

                        hebrew_text = self.clean_html(node)
                        if hebrew_text:
                            prayers.append(ParsedPrayer(
                                source_text=source_name,
                                sefaria_ref=sefaria_ref,
                                hebrew_text=hebrew_text,
                                path_components=path.copy()
                            ))

        # Start traversal from root
        traverse(text_root, [])

        print(f"  Extracted {len(prayers)} prayer texts")
        return prayers

    def match_and_update_database(self, prayers: List[ParsedPrayer]) -> int:
        """
        Match parsed prayers to database entries and update hebrew_text

        Args:
            prayers: List of ParsedPrayer objects

        Returns:
            Number of database records updated
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        updated_count = 0
        matched_count = 0

        for prayer in prayers:
            # Try exact match first
            cur.execute(
                "SELECT prayer_id FROM prayers WHERE sefaria_ref = ?",
                (prayer.sefaria_ref,)
            )
            result = cur.fetchone()

            if result:
                matched_count += 1
                prayer_id = result[0]

                # Update hebrew_text
                cur.execute(
                    "UPDATE prayers SET hebrew_text = ? WHERE prayer_id = ?",
                    (prayer.hebrew_text, prayer_id)
                )
                updated_count += 1
            else:
                # Log unmatched prayers for debugging
                if len(prayer.sefaria_ref) < 100:  # Only log if not too long
                    self.stats['errors'].append(
                        f"No match: {prayer.sefaria_ref[:100]}"
                    )

        conn.commit()
        conn.close()

        self.stats['prayers_matched'] += matched_count
        self.stats['prayers_updated'] += updated_count

        print(f"  Matched: {matched_count}, Updated: {updated_count}")

        return updated_count

    def process_all_files(self) -> Dict[str, Any]:
        """
        Process all JSON files in the directory

        Returns:
            Statistics dictionary
        """
        # Map of JSON filenames to source names
        sources = {
            'Siddur_Ashkenaz.json': 'Siddur Ashkenaz',
            'Siddur_Sefard.json': 'Siddur Sefard',
            'Siddur_Edot_HaMizrach.json': 'Siddur Edot HaMizrach',
            'Machzor_Rosh_Hashanah_Ashkenaz.json': 'Machzor Rosh Hashanah Ashkenaz',
            'Machzor_Yom_Kippur_Ashkenaz.json': 'Machzor Yom Kippur Ashkenaz',
            'Machzor_Rosh_Hashanah_Edot_HaMizrach.json': 'Machzor Rosh Hashanah Edot HaMizrach',
            'Machzor_Yom_Kippur_Edot_HaMizrach.json': 'Machzor Yom Kippur Edot HaMizrach',
            'Pesach_Haggadah.json': 'Pesach Haggadah',
        }

        print("="*60)
        print("Sefaria JSON Parser - Extracting Liturgical Texts")
        print("="*60)

        for filename, source_name in sources.items():
            json_path = self.json_dir / filename

            if not json_path.exists():
                print(f"WARNING: {filename} not found, skipping...")
                continue

            try:
                # Parse JSON file
                prayers = self.parse_json_file(json_path, source_name)
                self.stats['prayers_extracted'] += len(prayers)

                # Match and update database
                self.match_and_update_database(prayers)

                self.stats['files_processed'] += 1

            except Exception as e:
                error_msg = f"Error processing {filename}: {e}"
                print(f"  ERROR: {error_msg}")
                self.stats['errors'].append(error_msg)

        return self.stats

    def print_summary(self) -> None:
        """Print processing summary"""
        print("\n" + "="*60)
        print("Processing Complete - Summary")
        print("="*60)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Prayers extracted from JSON: {self.stats['prayers_extracted']}")
        print(f"Prayers matched to database: {self.stats['prayers_matched']}")
        print(f"Database records updated: {self.stats['prayers_updated']}")

        if self.stats['errors']:
            print(f"\nErrors/Warnings: {len(self.stats['errors'])}")
            # Show first 10 errors
            for error in self.stats['errors'][:10]:
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")

        # Query database for final statistics
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        total_entries = cur.execute("SELECT COUNT(*) FROM prayers").fetchone()[0]
        populated = cur.execute(
            "SELECT COUNT(*) FROM prayers WHERE hebrew_text IS NOT NULL AND hebrew_text != ''"
        ).fetchone()[0]

        conn.close()

        print(f"\nDatabase Statistics:")
        print(f"  Total prayer entries: {total_entries}")
        print(f"  Entries with Hebrew text: {populated}")
        print(f"  Coverage: {populated/total_entries*100:.1f}%")
        print("="*60)


def main():
    """Main entry point"""
    # Paths
    json_dir = Path("data/sefaria_export/liturgy")
    db_path = Path("data/liturgy.db")

    # Create parser
    parser = SefariaJSONParser(json_dir, db_path)

    # Process all files
    stats = parser.process_all_files()

    # Print summary
    parser.print_summary()

    return stats


if __name__ == "__main__":
    main()
