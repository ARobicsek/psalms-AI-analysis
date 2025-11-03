# Liturgical Librarian Implementation Plan
## Option 3: Comprehensive Annotated Liturgical Corpus

**Date**: 2025-10-26
**Status**: Planning Phase
**Target**: Sub-verse phrase detection with "influenced by" capability

---

## Executive Summary

This document outlines the implementation of a comprehensive liturgical cross-reference system that will enable your Psalms Commentary Pipeline to identify where passages from Psalms appear in Jewish prayer and ritual. The system will:

- Detect exact verse quotations, sub-verse phrases, and likely influences
- Cover multiple liturgical traditions (Ashkenaz, Sefard, Edot HaMizrach)
- Provide contextual information (service, section, ritual occasion)
- Assign confidence scores to matches
- Integrate seamlessly with your existing pipeline architecture

**Implementation Time**: 3-4 weeks (can be built incrementally)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    LITURGICAL LIBRARIAN                      │
│                                                              │
│  ┌────────────────┐      ┌──────────────────┐              │
│  │  liturgy.db    │◄─────│  Harvesting      │              │
│  │  - prayers     │      │  Scripts         │              │
│  │  - index       │      │  (Sefaria API)   │              │
│  │  - metadata    │      └──────────────────┘              │
│  └────────┬───────┘                                         │
│           │                                                 │
│           │      ┌──────────────────┐                       │
│           ├─────►│  Phrase          │                       │
│           │      │  Extraction      │                       │
│           │      │  & Scoring       │                       │
│           │      └──────────────────┘                       │
│           │                                                 │
│           │      ┌──────────────────┐                       │
│           └─────►│  Search &        │                       │
│                  │  Indexing        │                       │
│                  │  Engine          │                       │
│                  └─────────┬────────┘                       │
│                            │                                │
│                  ┌─────────▼────────┐                       │
│                  │ LiturgicalLibrarian│                     │
│                  │     (Query API)   │                       │
│                  └─────────┬────────┘                       │
└────────────────────────────┼──────────────────────────────┘
                             │
                             ▼
                    Research Bundle Assembly
```

---

## Phase 0: Bootstrap from Sefaria Cross-References ⚡ QUICK WIN

### Overview

**Before building our comprehensive phrase-level index**, we can get immediate value by harvesting Sefaria's existing verse-level cross-references between Psalms and liturgical texts. This gives us:

✅ **Immediate value** - Usable liturgical references within hours
✅ **Validation dataset** - Ground truth for testing our phrase detection
✅ **Gap analysis** - Shows what our custom indexing adds
✅ **Zero manual work** - Sefaria's scholars have already curated this

**Time to implement**: 4-6 hours
**Immediate coverage**: ~74 Psalms with verse-level precision

---

### How Sefaria Cross-References Work

From my research, Sefaria's `/api/related/` endpoint returns structured connections:

```json
{
  "links": [
    {
      "ref": "Siddur Ashkenaz, Shabbat, Third Meal, Mizmor LeDavid",
      "sourceRef": "Psalms 23:1-6",
      "category": "Liturgy",
      "type": "quotation",
      "collectiveTitle": "Siddur Ashkenaz"
    }
  ]
}
```

**Key fields**:
- `ref`: The liturgical text reference
- `sourceRef`: The Psalms passage (with verse range!)
- `category`: "Liturgy" (we filter for this)
- `type`: "quotation" (exact) or "quotation_auto_tanakh" (auto-detected)

---

### Implementation

#### Step 1: Harvest Sefaria Links

```python
# File: src/liturgy/sefaria_links_harvester.py

import requests
import sqlite3
import re
import time
from typing import List, Dict, Optional, Tuple

class SefariaLinksHarvester:
    """Harvest existing Psalms→Liturgy links from Sefaria API."""

    BASE_URL = "https://www.sefaria.org/api"

    def __init__(self, db_path: str = "data/liturgy.db"):
        self.db_path = db_path

    def harvest_all_psalms_links(self):
        """Harvest liturgical links for all 150 Psalms."""

        print("Harvesting Sefaria cross-references for all Psalms...")
        print("This will take ~5-10 minutes due to rate limiting.\n")

        total_links = 0

        for psalm_num in range(1, 151):
            try:
                links = self.get_liturgical_links(psalm_num)

                if links:
                    print(f"Psalm {psalm_num:3d}: Found {len(links)} liturgical link(s)")
                    self._store_links(links)
                    total_links += len(links)
                else:
                    print(f"Psalm {psalm_num:3d}: No liturgical links")

                # Rate limiting: be respectful of Sefaria's API
                time.sleep(0.5)

            except Exception as e:
                print(f"Psalm {psalm_num:3d}: ERROR - {e}")

        print(f"\n✓ Harvesting complete! Stored {total_links} liturgical links.")

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
        """Infer nusach from liturgy reference."""
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

        return None

    def _store_links(self, links: List[Dict]):
        """Store links in database."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create temporary table for Sefaria links if it doesn't exist
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
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,

                INDEX idx_psalm (psalm_chapter, psalm_verse_start)
            )
        """)

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
    harvester = SefariaLinksHarvester()
    harvester.harvest_all_psalms_links()

if __name__ == "__main__":
    main()
```

#### Step 2: Quick Librarian for Sefaria Links

```python
# File: src/agents/liturgical_librarian_sefaria.py

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

class SefariaLiturgicalLibrarian:
    """Query Sefaria's curated Psalms→Liturgy links."""

    def __init__(self, db_path: str = "data/liturgy.db"):
        self.db_path = db_path

    def find_liturgical_usage(
        self,
        psalm_chapter: int,
        psalm_verses: Optional[List[int]] = None
    ) -> List[SefariaLiturgicalLink]:
        """
        Find liturgical usage using Sefaria's curated links.

        Args:
            psalm_chapter: Psalm number
            psalm_verses: Specific verses (None = entire chapter)

        Returns:
            List of liturgical links
        """

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if psalm_verses is None:
            # Search for entire chapter or any verse
            query = """
                SELECT psalm_chapter, psalm_verse_start, psalm_verse_end,
                       liturgy_ref, collective_title, nusach, occasion,
                       service, section, confidence
                FROM sefaria_liturgy_links
                WHERE psalm_chapter = ?
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
                WHERE psalm_chapter = ? AND ({verse_conditions})
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
        """Format for research bundle."""

        if not links:
            return "## Liturgical Usage\n\nNo liturgical usage found in Sefaria's database.\n"

        output = ["## Liturgical Usage (from Sefaria)\n"]
        output.append(f"This passage appears in **{len(links)} liturgical context(s)** according to Sefaria's curated data:\n")

        for link in links:
            # Format location
            location_parts = []
            if link.collective_title:
                location_parts.append(link.collective_title)
            if link.occasion:
                location_parts.append(link.occasion)
            if link.service:
                location_parts.append(link.service)
            if link.section:
                location_parts.append(link.section)

            location = " - ".join(location_parts) if location_parts else link.liturgy_ref

            output.append(f"**{location}**")
            output.append(f"- Reference: {link.liturgy_ref}")

            if link.psalm_verse_start:
                verse_ref = f"{link.psalm_verse_start}"
                if link.psalm_verse_end and link.psalm_verse_end != link.psalm_verse_start:
                    verse_ref += f"-{link.psalm_verse_end}"
                output.append(f"- Verses: {verse_ref}")

            if link.nusach:
                output.append(f"- Tradition: {link.nusach}")

            output.append("")

        return "\n".join(output)
```

---

### Integration

**Immediate use** (within hours):

```python
# Use this TODAY while building the comprehensive system
from src.agents.liturgical_librarian_sefaria import SefariaLiturgicalLibrarian

librarian = SefariaLiturgicalLibrarian()
links = librarian.find_liturgical_usage(psalm_chapter=23)
markdown = librarian.format_for_research_bundle(links)

# Add to research bundle
```

**Long-term** (after building Phase 1-6):

```python
# Eventually combine both sources
sefaria_links = sefaria_librarian.find_liturgical_usage(23)
custom_index = custom_librarian.find_liturgical_usage(23)

# Merge and deduplicate
all_liturgical_data = merge_liturgical_sources(sefaria_links, custom_index)
```

---

### Validation Dataset

Once we build our custom phrase-level index, we can validate against Sefaria:

```python
def validate_custom_index():
    """Check that our custom index finds everything Sefaria found."""

    sefaria = SefariaLiturgicalLibrarian()
    custom = LiturgicalLibrarian()

    for psalm in range(1, 151):
        sefaria_links = sefaria.find_liturgical_usage(psalm)

        if not sefaria_links:
            continue

        custom_matches = custom.find_liturgical_usage(psalm)

        # Check coverage
        for link in sefaria_links:
            # Did our custom index find this?
            found = any(
                m.prayer_name in link.liturgy_ref or
                link.liturgy_ref in m.sefaria_ref
                for m in custom_matches
            )

            if not found:
                print(f"MISSED: Psalm {psalm} - {link.liturgy_ref}")
```

---

### Deliverables

- [ ] `src/liturgy/sefaria_links_harvester.py` - Link harvester
- [ ] `src/agents/liturgical_librarian_sefaria.py` - Quick librarian
- [ ] `sefaria_liturgy_links` table in `liturgy.db`
- [ ] Integration with research bundle
- [ ] **USABLE TODAY** - Can start including liturgical data in commentary

**Time Estimate**: 4-6 hours

**Value**: Immediate liturgical context for ~74 Psalms with verse-level precision

---

## Phase 1: Database Design & Setup

### Database Schema

#### Table: `prayers`
Stores the complete text of all liturgical sources.

```sql
CREATE TABLE prayers (
    prayer_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Source identification
    source_text TEXT NOT NULL,        -- 'Siddur_Ashkenaz', 'Machzor_Rosh_Hashanah_Edot_HaMizrach'
    sefaria_ref TEXT NOT NULL UNIQUE, -- Full Sefaria reference

    -- Classification
    nusach TEXT NOT NULL,             -- 'Ashkenaz', 'Sefard', 'Edot_HaMizrach'
    prayer_type TEXT NOT NULL,        -- 'Siddur', 'Machzor', 'Haggadah', etc.
    occasion TEXT,                    -- 'Weekday', 'Shabbat', 'Rosh_Hashanah', 'Yom_Kippur', etc.
    service TEXT,                     -- 'Shacharit', 'Mincha', 'Maariv', 'Musaf', 'Neilah'
    section TEXT,                     -- 'Pesukei_DZimrah', 'Amidah', 'Tachanun', 'Hallel', etc.

    -- Content
    prayer_name TEXT,                 -- 'Ashrei', 'Kaddish', 'Aleinu', etc.
    hebrew_text TEXT NOT NULL,
    english_text TEXT,

    -- Context
    sequence_order INTEGER,           -- Order within service
    liturgical_notes TEXT,            -- Additional context

    -- Metadata
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_nusach (nusach),
    INDEX idx_occasion_service (occasion, service),
    INDEX idx_section (section)
);
```

#### Table: `psalms_liturgy_index`
Pre-computed index of all Psalms references in liturgy.

```sql
CREATE TABLE psalms_liturgy_index (
    index_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Psalms reference
    psalm_chapter INTEGER NOT NULL,
    psalm_verse_start INTEGER,        -- NULL for chapter-level or phrase-level
    psalm_verse_end INTEGER,          -- NULL if single verse or phrase
    psalm_phrase_hebrew TEXT,         -- Exact Hebrew phrase matched
    psalm_phrase_normalized TEXT,     -- Level 2 normalization for searching
    phrase_length INTEGER,            -- Word count (2-10+)

    -- Liturgy reference
    prayer_id INTEGER NOT NULL,
    liturgy_phrase_hebrew TEXT,       -- The matching text from liturgy
    liturgy_context TEXT,             -- Surrounding text (±20 words)

    -- Match metadata
    match_type TEXT NOT NULL,         -- 'exact_verse', 'exact_chapter', 'exact_phrase', 'near_phrase', 'likely_influence'
    normalization_level INTEGER,      -- 0=exact, 1=voweled, 2=consonantal
    confidence REAL NOT NULL,         -- 0.0 to 1.0
    distinctiveness_score REAL,       -- TF-IDF or frequency-based score

    -- Manual curation
    manually_verified BOOLEAN DEFAULT 0,
    curator_notes TEXT,

    -- Metadata
    indexed_date TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(prayer_id) REFERENCES prayers(prayer_id),

    INDEX idx_psalm_ref (psalm_chapter, psalm_verse_start),
    INDEX idx_match_type (match_type),
    INDEX idx_confidence (confidence)
);
```

#### Table: `liturgical_metadata`
Rich contextual information about services and occasions.

```sql
CREATE TABLE liturgical_metadata (
    metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,

    category TEXT NOT NULL,           -- 'service', 'occasion', 'section', 'nusach'
    key TEXT NOT NULL,                -- e.g., 'Shacharit', 'Pesukei_DZimrah'

    display_name_english TEXT,        -- 'Morning Service', 'Verses of Praise'
    display_name_hebrew TEXT,         -- 'שחרית', 'פסוקי דזמרה'
    description TEXT,                 -- Detailed explanation
    typical_timing TEXT,              -- 'Daily', 'Sabbath and Holidays', etc.

    UNIQUE(category, key)
);
```

#### Table: `harvest_log`
Track corpus building progress.

```sql
CREATE TABLE harvest_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_text TEXT NOT NULL,
    sefaria_ref TEXT,
    status TEXT NOT NULL,             -- 'success', 'failed', 'skipped'
    error_message TEXT,
    harvest_date TEXT DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_status (status)
);
```

### Implementation Steps

**File**: `src/data_sources/liturgy_db_schema.sql`

```python
# File: src/data_sources/create_liturgy_db.py

import sqlite3
from pathlib import Path

def create_liturgy_database(db_path: str = "data/liturgy.db"):
    """Create the liturgical database with all tables and indexes."""

    schema_path = Path(__file__).parent / "liturgy_db_schema.sql"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Read and execute schema
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
        cursor.executescript(schema_sql)

    # Insert metadata
    _insert_metadata(cursor)

    conn.commit()
    conn.close()

    print(f"✓ Created liturgy database: {db_path}")

def _insert_metadata(cursor):
    """Populate liturgical_metadata table with standard values."""

    metadata = [
        # Nusachim
        ('nusach', 'Ashkenaz', 'Ashkenazi', 'אשכנז', 'Central and Eastern European Jewish tradition'),
        ('nusach', 'Sefard', 'Sephardic/Hasidic', 'ספרד', 'Hasidic version based on Lurianic kabbalah'),
        ('nusach', 'Edot_HaMizrach', 'Edot HaMizrach', 'עדות המזרח', 'Middle Eastern and North African Jewish tradition'),

        # Services
        ('service', 'Shacharit', 'Morning Service', 'שחרית', 'Daily morning prayer service'),
        ('service', 'Mincha', 'Afternoon Service', 'מנחה', 'Daily afternoon prayer service'),
        ('service', 'Maariv', 'Evening Service', 'מעריב', 'Daily evening prayer service'),
        ('service', 'Musaf', 'Additional Service', 'מוסף', 'Additional service on Sabbath and holidays'),
        ('service', 'Neilah', 'Closing Service', 'נעילה', 'Final service on Yom Kippur'),

        # Major sections
        ('section', 'Pesukei_DZimrah', 'Verses of Praise', 'פסוקי דזמרה', 'Preparatory psalms and biblical verses'),
        ('section', 'Amidah', 'Standing Prayer', 'עמידה', 'Central prayer recited while standing'),
        ('section', 'Tachanun', 'Supplication', 'תחנון', 'Penitential prayers on weekdays'),
        ('section', 'Hallel', 'Praise', 'הלל', 'Psalms 113-118 recited on festivals'),
        ('section', 'Kabbalat_Shabbat', 'Welcoming Sabbath', 'קבלת שבת', 'Friday evening prayers'),
        ('section', 'Selichot', 'Penitential Prayers', 'סליחות', 'Special prayers for forgiveness'),

        # Occasions
        ('occasion', 'Weekday', 'Weekday', 'יום חול', 'Monday-Friday services'),
        ('occasion', 'Shabbat', 'Sabbath', 'שבת', 'Saturday services'),
        ('occasion', 'Rosh_Hashanah', 'Rosh Hashanah', 'ראש השנה', 'Jewish New Year'),
        ('occasion', 'Yom_Kippur', 'Yom Kippur', 'יום כיפור', 'Day of Atonement'),
        ('occasion', 'Sukkot', 'Sukkot', 'סוכות', 'Feast of Tabernacles'),
        ('occasion', 'Pesach', 'Passover', 'פסח', 'Festival of Unleavened Bread'),
        ('occasion', 'Shavuot', 'Shavuot', 'שבועות', 'Feast of Weeks'),
    ]

    cursor.executemany(
        "INSERT INTO liturgical_metadata (category, key, display_name_english, display_name_hebrew, description) VALUES (?, ?, ?, ?, ?)",
        metadata
    )
```

**Deliverables**:
- [ ] `src/data_sources/liturgy_db_schema.sql` - SQL schema
- [ ] `src/data_sources/create_liturgy_db.py` - Database creation script
- [ ] `data/liturgy.db` - Empty database with schema
- [ ] Unit tests for schema integrity

**Time Estimate**: 1 day

---

## Phase 2: Corpus Harvesting from Sefaria

### Target Liturgical Sources

**Priority 1 - Siddurim** (Daily/Weekly prayer):
1. `Siddur_Ashkenaz` (Weekday, Shabbat)
2. `Siddur_Sefard` (Weekday, Shabbat)
3. `Siddur_Edot_HaMizrach` (Weekday, Shabbat)

**Priority 2 - Machzorim** (High Holidays):
1. `Machzor_Rosh_Hashanah_Ashkenaz`
2. `Machzor_Rosh_Hashanah_Edot_HaMizrach`
3. `Machzor_Yom_Kippur_Ashkenaz`
4. `Machzor_Yom_Kippur_Edot_HaMizrach`

**Priority 3 - Other**:
1. `Haggadah` (Passover seder)
2. Additional festival prayers as available

### Harvesting Strategy

#### Step 1: Discover Structure

```python
# File: src/data_sources/sefaria_liturgy_harvester.py

import requests
import time
from typing import Dict, List, Optional
import sqlite3

class SefariaLiturgyHarvester:
    """Harvest liturgical texts from Sefaria API."""

    BASE_URL = "https://www.sefaria.org/api"
    RATE_LIMIT_DELAY = 1.0  # seconds between requests

    def __init__(self, db_path: str = "data/liturgy.db"):
        self.db_path = db_path
        self.session = requests.Session()

    def get_table_of_contents(self, text_name: str) -> Dict:
        """Fetch TOC for a liturgical text."""
        url = f"{self.BASE_URL}/v2/index/{text_name}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_text(self, ref: str) -> Dict:
        """Fetch specific liturgical text."""
        url = f"{self.BASE_URL}/texts/{ref}"
        response = self.session.get(url)
        response.raise_for_status()
        time.sleep(self.RATE_LIMIT_DELAY)
        return response.json()

    def harvest_text_recursive(self, text_name: str, nusach: str):
        """Recursively harvest all sections of a liturgical text."""

        print(f"\n{'='*60}")
        print(f"Harvesting: {text_name}")
        print(f"Nusach: {nusach}")
        print(f"{'='*60}\n")

        # Get structure
        toc = self.get_table_of_contents(text_name)

        # Determine prayer type
        if "Siddur" in text_name:
            prayer_type = "Siddur"
        elif "Machzor" in text_name:
            prayer_type = "Machzor"
        else:
            prayer_type = "Other"

        # Parse structure and harvest texts
        self._traverse_structure(
            text_name=text_name,
            structure=toc,
            nusach=nusach,
            prayer_type=prayer_type,
            path=[]
        )

    def _traverse_structure(
        self,
        text_name: str,
        structure: Dict,
        nusach: str,
        prayer_type: str,
        path: List[str],
        occasion: Optional[str] = None,
        service: Optional[str] = None,
        section: Optional[str] = None
    ):
        """Recursively traverse hierarchical structure."""

        # Extract metadata from current level
        if 'titles' in structure:
            current_title = structure['titles'][0]['text']
            path.append(current_title)

            # Infer occasion/service/section from path
            occasion = self._infer_occasion(path)
            service = self._infer_service(path)
            section = self._infer_section(path)

        # If this is a leaf node (has text), harvest it
        if 'ref' in structure or self._is_leaf(structure):
            ref = structure.get('ref') or self._build_ref(text_name, path)
            self._harvest_prayer(
                ref=ref,
                text_name=text_name,
                nusach=nusach,
                prayer_type=prayer_type,
                occasion=occasion,
                service=service,
                section=section,
                path=path
            )

        # Recurse into children
        if 'nodes' in structure:
            for child in structure['nodes']:
                self._traverse_structure(
                    text_name=text_name,
                    structure=child,
                    nusach=nusach,
                    prayer_type=prayer_type,
                    path=path.copy(),
                    occasion=occasion,
                    service=service,
                    section=section
                )

    def _harvest_prayer(
        self,
        ref: str,
        text_name: str,
        nusach: str,
        prayer_type: str,
        occasion: Optional[str],
        service: Optional[str],
        section: Optional[str],
        path: List[str]
    ):
        """Fetch and store a single prayer text."""

        try:
            data = self.get_text(ref)

            # Extract text
            hebrew = self._extract_text(data, 'he')
            english = self._extract_text(data, 'en')

            if not hebrew:
                print(f"⚠ No Hebrew text for: {ref}")
                self._log_harvest(ref, text_name, 'skipped', 'No Hebrew text')
                return

            # Determine prayer name
            prayer_name = path[-1] if path else None

            # Store in database
            self._store_prayer(
                source_text=text_name,
                sefaria_ref=ref,
                nusach=nusach,
                prayer_type=prayer_type,
                occasion=occasion,
                service=service,
                section=section,
                prayer_name=prayer_name,
                hebrew_text=hebrew,
                english_text=english,
                liturgical_notes=f"Path: {' > '.join(path)}"
            )

            print(f"✓ Harvested: {ref}")
            self._log_harvest(ref, text_name, 'success')

        except Exception as e:
            print(f"✗ Failed: {ref} - {str(e)}")
            self._log_harvest(ref, text_name, 'failed', str(e))

    def _extract_text(self, data: Dict, lang: str) -> str:
        """Extract Hebrew or English text from API response."""
        if lang == 'he':
            text = data.get('he', [])
        else:
            text = data.get('text', [])

        if isinstance(text, list):
            return '\n'.join(text)
        return text

    def _infer_occasion(self, path: List[str]) -> Optional[str]:
        """Infer occasion from path."""
        path_str = ' '.join(path).lower()

        if 'weekday' in path_str:
            return 'Weekday'
        elif 'shabbat' in path_str or 'sabbath' in path_str:
            return 'Shabbat'
        elif 'rosh hashanah' in path_str:
            return 'Rosh_Hashanah'
        elif 'yom kippur' in path_str:
            return 'Yom_Kippur'

        return None

    def _infer_service(self, path: List[str]) -> Optional[str]:
        """Infer service from path."""
        path_str = ' '.join(path).lower()

        if 'shacharit' in path_str or 'morning' in path_str:
            return 'Shacharit'
        elif 'mincha' in path_str or 'afternoon' in path_str:
            return 'Mincha'
        elif 'maariv' in path_str or 'evening' in path_str:
            return 'Maariv'
        elif 'musaf' in path_str:
            return 'Musaf'
        elif 'neilah' in path_str:
            return 'Neilah'

        return None

    def _infer_section(self, path: List[str]) -> Optional[str]:
        """Infer section from path."""
        path_str = ' '.join(path).lower()

        if 'pesukei' in path_str or 'zimrah' in path_str:
            return 'Pesukei_DZimrah'
        elif 'amidah' in path_str or 'shemoneh esrei' in path_str:
            return 'Amidah'
        elif 'tachanun' in path_str:
            return 'Tachanun'
        elif 'hallel' in path_str:
            return 'Hallel'
        elif 'kabbalat shabbat' in path_str:
            return 'Kabbalat_Shabbat'
        elif 'selichot' in path_str:
            return 'Selichot'

        return None

    def _is_leaf(self, structure: Dict) -> bool:
        """Check if this is a leaf node (contains actual text)."""
        return 'nodes' not in structure or len(structure.get('nodes', [])) == 0

    def _build_ref(self, text_name: str, path: List[str]) -> str:
        """Build Sefaria reference from path."""
        return f"{text_name}, {', '.join(path)}"

    def _store_prayer(self, **kwargs):
        """Store prayer in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO prayers (
                source_text, sefaria_ref, nusach, prayer_type,
                occasion, service, section, prayer_name,
                hebrew_text, english_text, liturgical_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            kwargs['source_text'],
            kwargs['sefaria_ref'],
            kwargs['nusach'],
            kwargs['prayer_type'],
            kwargs['occasion'],
            kwargs['service'],
            kwargs['section'],
            kwargs['prayer_name'],
            kwargs['hebrew_text'],
            kwargs['english_text'],
            kwargs['liturgical_notes']
        ))

        conn.commit()
        conn.close()

    def _log_harvest(self, ref: str, source: str, status: str, error: str = None):
        """Log harvest attempt."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO harvest_log (source_text, sefaria_ref, status, error_message)
            VALUES (?, ?, ?, ?)
        """, (source, ref, status, error))

        conn.commit()
        conn.close()

# Main harvesting script
def main():
    harvester = SefariaLiturgyHarvester()

    # Harvest Priority 1: Siddurim
    harvester.harvest_text_recursive("Siddur_Ashkenaz", "Ashkenaz")
    harvester.harvest_text_recursive("Siddur_Sefard", "Sefard")
    harvester.harvest_text_recursive("Siddur_Edot_HaMizrach", "Edot_HaMizrach")

    # Harvest Priority 2: Machzorim (can be run later)
    # harvester.harvest_text_recursive("Machzor_Rosh_Hashanah_Ashkenaz", "Ashkenaz")
    # ... etc

    print("\n✓ Harvesting complete!")

if __name__ == "__main__":
    main()
```

**Deliverables**:
- [ ] `src/data_sources/sefaria_liturgy_harvester.py` - Harvesting script
- [ ] Populated `prayers` table in `liturgy.db`
- [ ] Harvest log for debugging
- [ ] Script to verify harvest completeness

**Time Estimate**: 2-3 days (including API exploration and debugging)

---

## Phase 3: Phrase Extraction & Distinctiveness Scoring

### Approach

For each Psalm, extract all meaningful n-grams (2-10 words) and score them by distinctiveness using TF-IDF against the broader biblical corpus.

### Implementation

```python
# File: src/liturgy/phrase_extractor.py

import sqlite3
import re
from typing import List, Tuple, Dict
from collections import Counter
import math

class PhraseExtractor:
    """Extract and score phrases from Psalms for liturgical matching."""

    def __init__(
        self,
        tanakh_db: str = "data/tanakh.db",
        liturgy_db: str = "data/liturgy.db"
    ):
        self.tanakh_db = tanakh_db
        self.liturgy_db = liturgy_db

        # Calculate corpus statistics once
        self.corpus_stats = self._calculate_corpus_stats()

    def extract_phrases(
        self,
        psalm_chapter: int,
        min_length: int = 2,
        max_length: int = 10
    ) -> List[Dict]:
        """
        Extract all meaningful phrases from a Psalm.

        Returns list of dicts with:
        - phrase: Hebrew text
        - verse_start: Starting verse
        - verse_end: Ending verse (for multi-verse phrases)
        - word_count: Number of words
        - distinctiveness_score: TF-IDF score
        - is_searchable: Boolean (meets threshold)
        """

        # Get Psalm text
        verses = self._get_psalm_verses(psalm_chapter)

        phrases = []

        for verse_num, verse_text in verses:
            # Extract n-grams from this verse
            words = self._tokenize_hebrew(verse_text)

            for n in range(min_length, min(max_length + 1, len(words) + 1)):
                for i in range(len(words) - n + 1):
                    phrase = ' '.join(words[i:i+n])

                    # Calculate distinctiveness
                    score = self._calculate_distinctiveness(phrase, n)

                    # Determine if searchable
                    is_searchable = self._is_searchable(phrase, n, score)

                    phrases.append({
                        'phrase': phrase,
                        'verse_start': verse_num,
                        'verse_end': verse_num,
                        'word_count': n,
                        'distinctiveness_score': score,
                        'is_searchable': is_searchable
                    })

        # Also extract cross-verse phrases (up to 3 verses)
        phrases.extend(self._extract_cross_verse_phrases(verses, min_length, max_length))

        return phrases

    def _get_psalm_verses(self, chapter: int) -> List[Tuple[int, str]]:
        """Fetch all verses from a Psalm."""
        conn = sqlite3.connect(self.tanakh_db)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT verse, hebrew
            FROM verses
            WHERE book_name = 'Psalms' AND chapter = ?
            ORDER BY verse
        """, (chapter,))

        verses = cursor.fetchall()
        conn.close()

        return verses

    def _tokenize_hebrew(self, text: str) -> List[str]:
        """Tokenize Hebrew text into words."""
        # Remove punctuation but keep Hebrew letters and diacritics
        text = re.sub(r'[^\u0590-\u05FF\s]', '', text)
        # Split on whitespace
        words = text.split()
        # Remove empty strings
        return [w for w in words if w.strip()]

    def _calculate_corpus_stats(self) -> Dict:
        """Calculate TF-IDF corpus statistics from Tanakh."""
        conn = sqlite3.connect(self.tanakh_db)
        cursor = conn.cursor()

        # Total number of verses in Tanakh
        cursor.execute("SELECT COUNT(*) FROM verses")
        total_verses = cursor.fetchone()[0]

        # This is expensive - consider caching or pre-computing
        # For now, we'll use a simplified approach

        conn.close()

        return {
            'total_verses': total_verses
        }

    def _calculate_distinctiveness(self, phrase: str, word_count: int) -> float:
        """
        Calculate distinctiveness score using corpus frequency.

        Lower frequency = higher distinctiveness.
        Returns score 0.0-1.0.
        """

        # Count occurrences in Tanakh
        freq = self._count_phrase_in_corpus(phrase)

        # TF-IDF inspired scoring
        if freq == 0:
            return 1.0  # Unique to this Psalm (very distinctive)

        idf = math.log(self.corpus_stats['total_verses'] / (1 + freq))

        # Normalize to 0-1 range
        # Phrases that appear < 5 times are highly distinctive
        # Phrases that appear > 100 times are not distinctive
        if freq <= 5:
            score = 0.9 + (0.1 * (5 - freq) / 5)
        elif freq <= 20:
            score = 0.7 + (0.2 * (20 - freq) / 15)
        elif freq <= 50:
            score = 0.4 + (0.3 * (50 - freq) / 30)
        else:
            score = max(0.0, 0.4 * (100 - freq) / 50)

        return min(1.0, score)

    def _count_phrase_in_corpus(self, phrase: str) -> int:
        """Count how many verses in Tanakh contain this phrase."""
        from src.concordance.hebrew_utils import normalize_hebrew

        # Use level 2 normalization (consonantal)
        normalized = normalize_hebrew(phrase, level=2)

        conn = sqlite3.connect(self.tanakh_db)
        cursor = conn.cursor()

        # Search all verses
        cursor.execute("SELECT hebrew FROM verses")
        count = 0

        for (verse_text,) in cursor.fetchall():
            verse_normalized = normalize_hebrew(verse_text, level=2)
            if normalized in verse_normalized:
                count += 1

        conn.close()
        return count

    def _is_searchable(self, phrase: str, word_count: int, score: float) -> bool:
        """
        Determine if a phrase is worth searching for in liturgy.

        Criteria:
        - 2 words: score > 0.75 (very distinctive)
        - 3 words: score > 0.5
        - 4+ words: score > 0.3
        - Also filter out phrases that are all particles
        """

        # Check for all particles
        if self._is_all_particles(phrase):
            return False

        # Word count thresholds
        if word_count == 2:
            return score > 0.75
        elif word_count == 3:
            return score > 0.5
        elif word_count >= 4:
            return score > 0.3

        return False

    def _is_all_particles(self, phrase: str) -> bool:
        """Check if phrase consists only of common particles."""
        particles = {
            'ו', 'ה', 'ל', 'ב', 'מ', 'כ', 'את', 'על', 'אל', 'מן',
            'אשר', 'כי', 'אם', 'לא', 'גם', 'עם'
        }

        words = phrase.split()
        return all(self._strip_diacritics(w) in particles for w in words)

    def _strip_diacritics(self, word: str) -> str:
        """Remove all diacritics from Hebrew word."""
        from src.concordance.hebrew_utils import normalize_hebrew
        return normalize_hebrew(word, level=2)

    def _extract_cross_verse_phrases(
        self,
        verses: List[Tuple[int, str]],
        min_length: int,
        max_length: int
    ) -> List[Dict]:
        """Extract phrases that span verse boundaries."""

        cross_verse_phrases = []

        # Look at consecutive verse pairs
        for i in range(len(verses) - 1):
            verse1_num, verse1_text = verses[i]
            verse2_num, verse2_text = verses[i + 1]

            words1 = self._tokenize_hebrew(verse1_text)
            words2 = self._tokenize_hebrew(verse2_text)

            # Take last N words from verse 1 + first N words from verse 2
            for n1 in range(1, min(max_length, len(words1) + 1)):
                for n2 in range(1, min(max_length - n1 + 1, len(words2) + 1)):
                    if n1 + n2 < min_length:
                        continue

                    phrase = ' '.join(words1[-n1:] + words2[:n2])
                    score = self._calculate_distinctiveness(phrase, n1 + n2)
                    is_searchable = self._is_searchable(phrase, n1 + n2, score)

                    cross_verse_phrases.append({
                        'phrase': phrase,
                        'verse_start': verse1_num,
                        'verse_end': verse2_num,
                        'word_count': n1 + n2,
                        'distinctiveness_score': score,
                        'is_searchable': is_searchable
                    })

        return cross_verse_phrases
```

**Optimization Note**: The `_count_phrase_in_corpus` method is expensive. Consider:
1. Pre-computing a phrase frequency index
2. Using your existing concordance database with phrase search
3. Caching results

**Deliverables**:
- [ ] `src/liturgy/phrase_extractor.py` - Phrase extraction and scoring
- [ ] Unit tests with known distinctive/common phrases
- [ ] Performance optimization for corpus counting

**Time Estimate**: 3-4 days

---

## Phase 4: Indexing Algorithm

### Search Strategy

For each searchable phrase extracted from Psalms:
1. Search liturgical texts using 4-layer normalization
2. Record all matches with confidence scores
3. Store in `psalms_liturgy_index` table

```python
# File: src/liturgy/liturgy_indexer.py

import sqlite3
from typing import List, Dict, Optional
from src.concordance.hebrew_utils import normalize_hebrew

class LiturgyIndexer:
    """Build index of Psalms phrases in liturgical texts."""

    def __init__(
        self,
        liturgy_db: str = "data/liturgy.db",
        tanakh_db: str = "data/tanakh.db"
    ):
        self.liturgy_db = liturgy_db
        self.tanakh_db = tanakh_db

    def index_psalm(self, psalm_chapter: int):
        """
        Build complete index for a single Psalm.

        This can be run incrementally - one Psalm at a time.
        """
        from src.liturgy.phrase_extractor import PhraseExtractor

        print(f"\n{'='*60}")
        print(f"Indexing Psalm {psalm_chapter}")
        print(f"{'='*60}\n")

        # Extract phrases
        extractor = PhraseExtractor(self.tanakh_db, self.liturgy_db)
        phrases = extractor.extract_phrases(psalm_chapter)

        # Filter to searchable only
        searchable = [p for p in phrases if p['is_searchable']]

        print(f"Total phrases extracted: {len(phrases)}")
        print(f"Searchable phrases: {len(searchable)}")
        print(f"Filtering out {len(phrases) - len(searchable)} low-distinctiveness phrases\n")

        # Also add full verses and complete chapter
        searchable.extend(self._get_full_verses(psalm_chapter))
        searchable.append(self._get_full_chapter(psalm_chapter))

        # Search each phrase in liturgy
        total_matches = 0
        for i, phrase_data in enumerate(searchable, 1):
            print(f"[{i}/{len(searchable)}] Searching: {phrase_data['phrase'][:50]}...")

            matches = self._search_liturgy(
                phrase_hebrew=phrase_data['phrase'],
                psalm_chapter=psalm_chapter,
                psalm_verse_start=phrase_data['verse_start'],
                psalm_verse_end=phrase_data['verse_end'],
                distinctiveness_score=phrase_data['distinctiveness_score']
            )

            if matches:
                print(f"  ✓ Found {len(matches)} match(es)")
                total_matches += len(matches)

                # Store in index
                for match in matches:
                    self._store_match(match)

        print(f"\n✓ Indexing complete: {total_matches} total matches stored")

    def _get_full_verses(self, psalm_chapter: int) -> List[Dict]:
        """Get full verse texts for exact verse matching."""
        conn = sqlite3.connect(self.tanakh_db)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT verse, hebrew
            FROM verses
            WHERE book_name = 'Psalms' AND chapter = ?
        """, (psalm_chapter,))

        verses = []
        for verse_num, hebrew in cursor.fetchall():
            verses.append({
                'phrase': hebrew,
                'verse_start': verse_num,
                'verse_end': verse_num,
                'word_count': len(hebrew.split()),
                'distinctiveness_score': 0.9,  # Full verses are highly relevant
                'is_searchable': True
            })

        conn.close()
        return verses

    def _get_full_chapter(self, psalm_chapter: int) -> Dict:
        """Get full chapter text for complete Psalm matching."""
        conn = sqlite3.connect(self.tanakh_db)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT verse, hebrew
            FROM verses
            WHERE book_name = 'Psalms' AND chapter = ?
            ORDER BY verse
        """, (psalm_chapter,))

        verses = cursor.fetchall()
        full_text = '\n'.join(hebrew for _, hebrew in verses)

        conn.close()

        return {
            'phrase': full_text,
            'verse_start': verses[0][0] if verses else 1,
            'verse_end': verses[-1][0] if verses else 1,
            'word_count': len(full_text.split()),
            'distinctiveness_score': 1.0,  # Entire chapter is maximally relevant
            'is_searchable': True
        }

    def _search_liturgy(
        self,
        phrase_hebrew: str,
        psalm_chapter: int,
        psalm_verse_start: int,
        psalm_verse_end: Optional[int],
        distinctiveness_score: float
    ) -> List[Dict]:
        """
        Search for a Psalms phrase in all liturgical texts.

        Returns list of matches with metadata.
        """

        matches = []

        # Try multiple normalization levels
        for level in [0, 1, 2]:  # exact, voweled, consonantal
            level_matches = self._search_at_level(
                phrase_hebrew=phrase_hebrew,
                normalization_level=level,
                psalm_chapter=psalm_chapter,
                psalm_verse_start=psalm_verse_start,
                psalm_verse_end=psalm_verse_end,
                distinctiveness_score=distinctiveness_score
            )

            matches.extend(level_matches)

            # If we found exact matches, don't look for fuzzier ones
            if level == 0 and matches:
                break

        return matches

    def _search_at_level(
        self,
        phrase_hebrew: str,
        normalization_level: int,
        psalm_chapter: int,
        psalm_verse_start: int,
        psalm_verse_end: Optional[int],
        distinctiveness_score: float
    ) -> List[Dict]:
        """Search at a specific normalization level."""

        normalized_phrase = normalize_hebrew(phrase_hebrew, level=normalization_level)

        conn = sqlite3.connect(self.liturgy_db)
        cursor = conn.cursor()

        # Search all prayers
        cursor.execute("SELECT prayer_id, hebrew_text, sefaria_ref, nusach, occasion, service, section, prayer_name FROM prayers")

        matches = []

        for prayer_id, hebrew_text, sefaria_ref, nusach, occasion, service, section, prayer_name in cursor.fetchall():
            normalized_liturgy = normalize_hebrew(hebrew_text, level=normalization_level)

            if normalized_phrase in normalized_liturgy:
                # Extract context
                context = self._extract_context(
                    full_text=hebrew_text,
                    phrase=phrase_hebrew,
                    normalization_level=normalization_level
                )

                # Determine match type
                match_type = self._determine_match_type(
                    phrase_hebrew=phrase_hebrew,
                    verse_start=psalm_verse_start,
                    verse_end=psalm_verse_end,
                    normalization_level=normalization_level
                )

                # Calculate confidence
                confidence = self._calculate_confidence(
                    normalization_level=normalization_level,
                    distinctiveness_score=distinctiveness_score,
                    match_type=match_type
                )

                matches.append({
                    'psalm_chapter': psalm_chapter,
                    'psalm_verse_start': psalm_verse_start,
                    'psalm_verse_end': psalm_verse_end,
                    'psalm_phrase_hebrew': phrase_hebrew,
                    'psalm_phrase_normalized': normalized_phrase,
                    'phrase_length': len(phrase_hebrew.split()),
                    'prayer_id': prayer_id,
                    'liturgy_phrase_hebrew': self._extract_exact_match(hebrew_text, phrase_hebrew, normalization_level),
                    'liturgy_context': context,
                    'match_type': match_type,
                    'normalization_level': normalization_level,
                    'confidence': confidence,
                    'distinctiveness_score': distinctiveness_score
                })

        conn.close()
        return matches

    def _extract_context(
        self,
        full_text: str,
        phrase: str,
        normalization_level: int,
        context_words: int = 10
    ) -> str:
        """Extract surrounding context (±N words) around the match."""

        words = full_text.split()
        phrase_words = phrase.split()

        # Find the phrase
        normalized_full = normalize_hebrew(full_text, level=normalization_level)
        normalized_phrase = normalize_hebrew(phrase, level=normalization_level)

        idx = normalized_full.find(normalized_phrase)
        if idx == -1:
            return ""

        # Count words before match
        words_before = normalized_full[:idx].split()
        start_idx = max(0, len(words_before) - context_words)
        end_idx = min(len(words), len(words_before) + len(phrase_words) + context_words)

        return ' '.join(words[start_idx:end_idx])

    def _extract_exact_match(self, full_text: str, phrase: str, normalization_level: int) -> str:
        """Extract the exact matching text from liturgy (preserving original diacritics)."""

        words = full_text.split()
        phrase_words = phrase.split()

        normalized_full = normalize_hebrew(full_text, level=normalization_level)
        normalized_phrase = normalize_hebrew(phrase, level=normalization_level)

        idx = normalized_full.find(normalized_phrase)
        if idx == -1:
            return phrase  # Fallback

        words_before = normalized_full[:idx].split()
        match_start = len(words_before)
        match_end = match_start + len(phrase_words)

        return ' '.join(words[match_start:match_end])

    def _determine_match_type(
        self,
        phrase_hebrew: str,
        verse_start: int,
        verse_end: Optional[int],
        normalization_level: int
    ) -> str:
        """Determine the type of match."""

        # Check if it's a full verse or chapter
        conn = sqlite3.connect(self.tanakh_db)
        cursor = conn.cursor()

        if verse_end is None or verse_start == verse_end:
            # Single verse - check if it's the full verse
            cursor.execute("""
                SELECT hebrew FROM verses
                WHERE book_name = 'Psalms' AND verse = ?
            """, (verse_start,))

            verse_text = cursor.fetchone()
            if verse_text:
                if normalize_hebrew(verse_text[0], level=2) == normalize_hebrew(phrase_hebrew, level=2):
                    conn.close()
                    return 'exact_verse'

        # Check if it's a full chapter
        cursor.execute("""
            SELECT COUNT(*) FROM verses
            WHERE book_name = 'Psalms' AND chapter = ?
        """, (verse_start,))  # Assuming verse_start is chapter number for chapter matches

        conn.close()

        # Otherwise it's a phrase
        if normalization_level == 0:
            return 'exact_phrase'
        elif normalization_level == 1:
            return 'near_phrase'
        else:
            return 'likely_influence'

    def _calculate_confidence(
        self,
        normalization_level: int,
        distinctiveness_score: float,
        match_type: str
    ) -> float:
        """
        Calculate confidence score for a match.

        Factors:
        - Normalization level (exact > voweled > consonantal)
        - Distinctiveness score (rare phrases are more confident)
        - Match type (verse > phrase)
        """

        # Base confidence by normalization level
        if normalization_level == 0:
            base = 1.0  # Exact match
        elif normalization_level == 1:
            base = 0.85  # Voweled match
        else:
            base = 0.7  # Consonantal match

        # Boost for match type
        if match_type == 'exact_verse' or match_type == 'exact_chapter':
            type_boost = 0.1
        else:
            type_boost = 0.0

        # Combine with distinctiveness
        confidence = min(1.0, base + type_boost * distinctiveness_score)

        return round(confidence, 3)

    def _store_match(self, match: Dict):
        """Store a match in the index."""

        conn = sqlite3.connect(self.liturgy_db)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO psalms_liturgy_index (
                psalm_chapter, psalm_verse_start, psalm_verse_end,
                psalm_phrase_hebrew, psalm_phrase_normalized, phrase_length,
                prayer_id, liturgy_phrase_hebrew, liturgy_context,
                match_type, normalization_level, confidence, distinctiveness_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match['psalm_chapter'],
            match['psalm_verse_start'],
            match['psalm_verse_end'],
            match['psalm_phrase_hebrew'],
            match['psalm_phrase_normalized'],
            match['phrase_length'],
            match['prayer_id'],
            match['liturgy_phrase_hebrew'],
            match['liturgy_context'],
            match['match_type'],
            match['normalization_level'],
            match['confidence'],
            match['distinctiveness_score']
        ))

        conn.commit()
        conn.close()

    def index_all_psalms(self):
        """Index all 150 Psalms (can run overnight)."""
        for psalm in range(1, 151):
            try:
                self.index_psalm(psalm)
            except Exception as e:
                print(f"✗ Error indexing Psalm {psalm}: {e}")

# CLI script
def main():
    import argparse

    parser = argparse.ArgumentParser(description='Index Psalms in liturgical texts')
    parser.add_argument('--psalm', type=int, help='Index a specific Psalm')
    parser.add_argument('--all', action='store_true', help='Index all Psalms')

    args = parser.parse_args()

    indexer = LiturgyIndexer()

    if args.psalm:
        indexer.index_psalm(args.psalm)
    elif args.all:
        indexer.index_all_psalms()
    else:
        print("Please specify --psalm N or --all")

if __name__ == "__main__":
    main()
```

**Usage**:
```bash
# Index one Psalm at a time as you process them
python src/liturgy/liturgy_indexer.py --psalm 23

# Or index all at once (long-running)
python src/liturgy/liturgy_indexer.py --all
```

**Deliverables**:
- [ ] `src/liturgy/liturgy_indexer.py` - Indexing engine
- [ ] CLI for incremental indexing
- [ ] Populated `psalms_liturgy_index` table
- [ ] Index quality report

**Time Estimate**: 4-5 days

---

## Phase 5: Librarian Implementation

### LiturgicalLibrarian Class

Integrates with your existing research bundle system.

```python
# File: src/agents/liturgical_librarian.py

import sqlite3
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class LiturgicalUsage:
    """Represents a single liturgical usage of a Psalms passage."""

    # Psalms reference
    psalm_chapter: int
    psalm_verse_start: Optional[int]
    psalm_verse_end: Optional[int]
    psalm_text: str

    # Liturgy reference
    nusach: str
    prayer_type: str
    occasion: Optional[str]
    service: Optional[str]
    section: Optional[str]
    prayer_name: Optional[str]
    sefaria_ref: str

    # Match details
    match_type: str
    confidence: float
    context: str

    # Display names
    occasion_display: str
    service_display: str
    section_display: str

class LiturgicalLibrarian:
    """Query liturgical usage of Psalms passages."""

    def __init__(self, db_path: str = "data/liturgy.db"):
        self.db_path = db_path

    def find_liturgical_usage(
        self,
        psalm_chapter: int,
        psalm_verses: Optional[List[int]] = None,
        min_confidence: float = 0.7,
        include_likely_influence: bool = True
    ) -> List[LiturgicalUsage]:
        """
        Find all liturgical uses of a Psalm or specific verses.

        Args:
            psalm_chapter: Psalm number
            psalm_verses: Specific verses (None = entire chapter)
            min_confidence: Minimum confidence threshold
            include_likely_influence: Include consonantal matches

        Returns:
            List of liturgical usages, sorted by confidence
        """

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Build query
        if psalm_verses is None:
            # Search for entire chapter or any verse
            query = """
                SELECT DISTINCT
                    i.psalm_chapter,
                    i.psalm_verse_start,
                    i.psalm_verse_end,
                    i.psalm_phrase_hebrew,
                    p.nusach,
                    p.prayer_type,
                    p.occasion,
                    p.service,
                    p.section,
                    p.prayer_name,
                    p.sefaria_ref,
                    i.match_type,
                    i.confidence,
                    i.liturgy_context,
                    m_occasion.display_name_english AS occasion_display,
                    m_service.display_name_english AS service_display,
                    m_section.display_name_english AS section_display
                FROM psalms_liturgy_index i
                JOIN prayers p ON i.prayer_id = p.prayer_id
                LEFT JOIN liturgical_metadata m_occasion
                    ON m_occasion.category = 'occasion' AND m_occasion.key = p.occasion
                LEFT JOIN liturgical_metadata m_service
                    ON m_service.category = 'service' AND m_service.key = p.service
                LEFT JOIN liturgical_metadata m_section
                    ON m_section.category = 'section' AND m_section.key = p.section
                WHERE i.psalm_chapter = ?
                    AND i.confidence >= ?
            """
            params = [psalm_chapter, min_confidence]
        else:
            # Search for specific verses
            verse_conditions = " OR ".join([
                "(i.psalm_verse_start <= ? AND (i.psalm_verse_end >= ? OR i.psalm_verse_end IS NULL))"
                for _ in psalm_verses
            ])

            query = f"""
                SELECT DISTINCT
                    i.psalm_chapter,
                    i.psalm_verse_start,
                    i.psalm_verse_end,
                    i.psalm_phrase_hebrew,
                    p.nusach,
                    p.prayer_type,
                    p.occasion,
                    p.service,
                    p.section,
                    p.prayer_name,
                    p.sefaria_ref,
                    i.match_type,
                    i.confidence,
                    i.liturgy_context,
                    m_occasion.display_name_english AS occasion_display,
                    m_service.display_name_english AS service_display,
                    m_section.display_name_english AS section_display
                FROM psalms_liturgy_index i
                JOIN prayers p ON i.prayer_id = p.prayer_id
                LEFT JOIN liturgical_metadata m_occasion
                    ON m_occasion.category = 'occasion' AND m_occasion.key = p.occasion
                LEFT JOIN liturgical_metadata m_service
                    ON m_service.category = 'service' AND m_service.key = p.service
                LEFT JOIN liturgical_metadata m_section
                    ON m_section.category = 'section' AND m_section.key = p.section
                WHERE i.psalm_chapter = ?
                    AND ({verse_conditions})
                    AND i.confidence >= ?
            """

            # Flatten verse params
            params = [psalm_chapter]
            for v in psalm_verses:
                params.extend([v, v])
            params.append(min_confidence)

        if not include_likely_influence:
            query += " AND i.match_type != 'likely_influence'"

        query += " ORDER BY i.confidence DESC, p.nusach, p.occasion, p.service"

        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            results.append(LiturgicalUsage(
                psalm_chapter=row[0],
                psalm_verse_start=row[1],
                psalm_verse_end=row[2],
                psalm_text=row[3],
                nusach=row[4],
                prayer_type=row[5],
                occasion=row[6],
                service=row[7],
                section=row[8],
                prayer_name=row[9],
                sefaria_ref=row[10],
                match_type=row[11],
                confidence=row[12],
                context=row[13],
                occasion_display=row[14] or row[6],
                service_display=row[15] or row[7],
                section_display=row[16] or row[8]
            ))

        conn.close()
        return results

    def format_for_research_bundle(
        self,
        usages: List[LiturgicalUsage],
        include_hebrew: bool = True,
        include_context: bool = True
    ) -> str:
        """
        Format liturgical usages for inclusion in research bundle.

        Returns markdown-formatted string.
        """

        if not usages:
            return "## Liturgical Usage\n\nNo liturgical usage found for this passage.\n"

        output = ["## Liturgical Usage\n"]
        output.append(f"This passage appears in **{len(usages)} liturgical context(s)**:\n")

        # Group by nusach
        by_nusach = {}
        for usage in usages:
            if usage.nusach not in by_nusach:
                by_nusach[usage.nusach] = []
            by_nusach[usage.nusach].append(usage)

        for nusach in ['Ashkenaz', 'Sefard', 'Edot_HaMizrach']:
            if nusach not in by_nusach:
                continue

            output.append(f"\n### {nusach} Tradition\n")

            for usage in by_nusach[nusach]:
                # Header
                location_parts = []
                if usage.occasion_display:
                    location_parts.append(usage.occasion_display)
                if usage.service_display:
                    location_parts.append(usage.service_display)
                if usage.section_display:
                    location_parts.append(usage.section_display)
                if usage.prayer_name:
                    location_parts.append(f"'{usage.prayer_name}'")

                location = " - ".join(location_parts) if location_parts else "General prayer"

                output.append(f"**{location}**")
                output.append(f"- Reference: {usage.sefaria_ref}")
                output.append(f"- Match type: {usage.match_type.replace('_', ' ').title()}")
                output.append(f"- Confidence: {usage.confidence:.0%}")

                if usage.psalm_verse_start:
                    verse_ref = f"{usage.psalm_verse_start}"
                    if usage.psalm_verse_end and usage.psalm_verse_end != usage.psalm_verse_start:
                        verse_ref += f"-{usage.psalm_verse_end}"
                    output.append(f"- Psalm verses: {verse_ref}")

                if include_hebrew and usage.psalm_text:
                    output.append(f"- Text: {usage.psalm_text}")

                if include_context and usage.context:
                    output.append(f"- Liturgical context: ...{usage.context}...")

                output.append("")  # Blank line

        return "\n".join(output)

# Example usage in research bundle
def example_integration():
    """Example of how to integrate with your existing pipeline."""

    librarian = LiturgicalLibrarian()

    # Query for Psalm 23
    usages = librarian.find_liturgical_usage(
        psalm_chapter=23,
        min_confidence=0.7
    )

    # Format for research bundle
    markdown = librarian.format_for_research_bundle(usages)

    print(markdown)
```

### Integration with ScholarResearcher

```python
# File: src/agents/scholar_researcher.py (MODIFICATION)

class ScholarResearcher:
    def __init__(self):
        # ... existing librarians ...
        self.liturgical_librarian = LiturgicalLibrarian()  # ADD THIS

    def generate_research_bundle(
        self,
        psalm_chapter: int,
        requests: List[ResearchRequest]
    ) -> ResearchBundle:
        """Generate complete research bundle."""

        bundle_sections = []

        # ... existing sections (lexicon, concordance, etc.) ...

        # ADD LITURGICAL SECTION
        liturgical_usages = self.liturgical_librarian.find_liturgical_usage(
            psalm_chapter=psalm_chapter,
            min_confidence=0.7
        )

        liturgical_markdown = self.liturgical_librarian.format_for_research_bundle(
            usages=liturgical_usages,
            include_hebrew=True,
            include_context=True
        )

        bundle_sections.append({
            'title': 'Liturgical Usage',
            'content': liturgical_markdown,
            'word_count': len(liturgical_markdown.split())
        })

        # ... continue with bundle assembly ...

        return ResearchBundle(sections=bundle_sections)
```

**Deliverables**:
- [ ] `src/agents/liturgical_librarian.py` - Librarian class
- [ ] Integration with `scholar_researcher.py`
- [ ] Unit tests
- [ ] Example output for Psalm 23, 145, etc.

**Time Estimate**: 2-3 days

---

## Phase 6: Testing & Refinement

### Test Cases

**Known Liturgical Psalms** (for validation):
1. **Psalm 145 (Ashrei)** - Appears 3x daily in Pesukei D'Zimrah
2. **Psalm 23** - Shabbat afternoon, various occasions
3. **Psalm 92** - Shabbat morning (Mizmor Shir L'Yom HaShabbat)
4. **Psalms 113-118 (Hallel)** - Festivals and Rosh Chodesh
5. **Psalm 27** - Daily during Elul and High Holiday season
6. **Psalm 126** - Birkat HaMazon on Shabbat and festivals
7. **Psalm 150** - End of Pesukei D'Zimrah

### Testing Strategy

```python
# File: tests/test_liturgical_librarian.py

import pytest
from src.agents.liturgical_librarian import LiturgicalLibrarian

class TestLiturgicalLibrarian:

    def test_psalm_145_in_pesukei_dzimrah(self):
        """Psalm 145 (Ashrei) should appear in morning service."""
        librarian = LiturgicalLibrarian()
        usages = librarian.find_liturgical_usage(psalm_chapter=145)

        # Should find it in all three nusachim
        nusachim = {u.nusach for u in usages}
        assert 'Ashkenaz' in nusachim
        assert 'Sefard' in nusachim or 'Edot_HaMizrach' in nusachim

        # Should be in Shacharit service
        services = {u.service for u in usages}
        assert 'Shacharit' in services

        # Should be high confidence (exact verse match)
        assert any(u.confidence >= 0.95 for u in usages)

    def test_psalm_23_on_shabbat(self):
        """Psalm 23 should appear in Shabbat liturgy."""
        librarian = LiturgicalLibrarian()
        usages = librarian.find_liturgical_usage(psalm_chapter=23)

        # Should find Shabbat usage
        occasions = {u.occasion for u in usages}
        assert 'Shabbat' in occasions

    def test_psalm_126_in_birkat_hamazon(self):
        """Psalm 126 (Shir HaMaalot) should appear in Grace After Meals."""
        librarian = LiturgicalLibrarian()
        usages = librarian.find_liturgical_usage(psalm_chapter=126)

        # Should find it
        assert len(usages) > 0

        # Should be Shabbat context
        assert any('Shabbat' in (u.occasion or '') for u in usages)

    def test_hallel_psalms(self):
        """Psalms 113-118 should be identified as Hallel."""
        librarian = LiturgicalLibrarian()

        for psalm_num in range(113, 119):
            usages = librarian.find_liturgical_usage(psalm_chapter=psalm_num)

            # Should find Hallel section
            sections = {u.section for u in usages}
            assert 'Hallel' in sections, f"Psalm {psalm_num} not found in Hallel"

    def test_phrase_detection(self):
        """Test sub-verse phrase detection."""
        librarian = LiturgicalLibrarian()

        # Psalm 145:3 contains "גָּדוֹל ה' וּמְהֻלָּל מְאֹד"
        # This phrase should be findable even if only part is quoted
        usages = librarian.find_liturgical_usage(
            psalm_chapter=145,
            psalm_verses=[3]
        )

        assert len(usages) > 0

    def test_confidence_levels(self):
        """Test that confidence scoring makes sense."""
        librarian = LiturgicalLibrarian()
        usages = librarian.find_liturgical_usage(psalm_chapter=145)

        # Exact verse matches should have higher confidence than phrases
        exact_confidences = [u.confidence for u in usages if u.match_type == 'exact_verse']
        phrase_confidences = [u.confidence for u in usages if u.match_type == 'exact_phrase']

        if exact_confidences and phrase_confidences:
            assert max(exact_confidences) >= max(phrase_confidences)
```

### Manual Curation

Some matches will need manual review. Create a curation interface:

```python
# File: src/liturgy/curator.py

import sqlite3

class LiturgyIndexCurator:
    """Tool for manually reviewing and curating index entries."""

    def __init__(self, db_path: str = "data/liturgy.db"):
        self.db_path = db_path

    def review_low_confidence_matches(self, threshold: float = 0.8):
        """Review all matches below confidence threshold."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT index_id, psalm_chapter, psalm_verse_start,
                   psalm_phrase_hebrew, match_type, confidence
            FROM psalms_liturgy_index
            WHERE confidence < ? AND manually_verified = 0
            ORDER BY confidence DESC
        """, (threshold,))

        for row in cursor.fetchall():
            index_id, psalm, verse, phrase, match_type, confidence = row

            print(f"\n{'='*60}")
            print(f"Psalm {psalm}:{verse}")
            print(f"Phrase: {phrase}")
            print(f"Match type: {match_type}")
            print(f"Confidence: {confidence:.2%}")
            print(f"{'='*60}")

            action = input("Keep (k), Delete (d), or Skip (s)? ").lower()

            if action == 'k':
                self._mark_verified(index_id, True)
                print("✓ Kept and marked as verified")
            elif action == 'd':
                self._delete_match(index_id)
                print("✗ Deleted")
            else:
                print("⊘ Skipped")

        conn.close()

    def _mark_verified(self, index_id: int, verified: bool):
        """Mark an index entry as manually verified."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE psalms_liturgy_index
            SET manually_verified = ?
            WHERE index_id = ?
        """, (1 if verified else 0, index_id))

        conn.commit()
        conn.close()

    def _delete_match(self, index_id: int):
        """Delete a false positive match."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM psalms_liturgy_index WHERE index_id = ?", (index_id,))

        conn.commit()
        conn.close()
```

**Deliverables**:
- [ ] Comprehensive test suite
- [ ] Manual curation of edge cases
- [ ] Quality report on index accuracy
- [ ] Threshold tuning based on validation results

**Time Estimate**: 3-4 days

---

## Implementation Timeline

### 🚀 Quick Start Path (RECOMMENDED)

**Day 1 (4-6 hours)**: Phase 0 - Bootstrap from Sefaria
- [ ] Implement Sefaria links harvester
- [ ] Harvest all 150 Psalms cross-references (~10 minutes runtime)
- [ ] Create quick librarian
- [ ] **IMMEDIATE VALUE**: Start using liturgical data in commentary today!

Then proceed with comprehensive system at your own pace...

---

### Full Implementation Path

### Week 1
- [ ] Days 1: Phase 1 - Database design and setup
- [ ] Days 2-3: Phase 2 - Begin corpus harvesting
- [ ] Days 4-5: Phase 2 - Complete harvesting and validation

### Week 2
- [ ] Days 1-3: Phase 3 - Phrase extraction and distinctiveness scoring
- [ ] Days 4-5: Phase 4 - Begin indexing algorithm

### Week 3
- [ ] Days 1-2: Phase 4 - Complete indexing algorithm
- [ ] Days 3-5: Phase 5 - Librarian implementation and integration

### Week 4
- [ ] Days 1-3: Phase 6 - Testing and refinement
- [ ] Days 4-5: Documentation and deployment

---

### 💡 Incremental Build Strategy

**Recommended approach**:
1. **Day 1**: Build Phase 0 (Sefaria bootstrap) → **IMMEDIATE VALUE**
2. **Week 1-2**: Build infrastructure (Phases 1-3) at your own pace
3. **Ongoing**: Index Psalms one at a time as you process them for commentary
4. **Monthly**: Review quality and refine thresholds based on real-world usage

**Why this works**:
- You get 70-80% of the value on Day 1
- No pressure to complete the full system before using it
- The comprehensive index grows alongside your commentary work
- Sefaria data validates your custom index as you build it

---

## Maintenance Plan

### Updating the Corpus

As Sefaria adds new liturgical texts:
```python
# Re-run harvester for new texts
python src/data_sources/sefaria_liturgy_harvester.py --source "New_Siddur_Name"

# Re-index affected Psalms
python src/liturgy/liturgy_indexer.py --all
```

### Monitoring Quality

```python
# File: src/liturgy/quality_report.py

def generate_quality_report():
    """Generate report on index quality."""

    conn = sqlite3.connect("data/liturgy.db")
    cursor = conn.cursor()

    # Total matches
    cursor.execute("SELECT COUNT(*) FROM psalms_liturgy_index")
    total = cursor.fetchone()[0]

    # By confidence
    cursor.execute("""
        SELECT
            CASE
                WHEN confidence >= 0.9 THEN 'High (0.9+)'
                WHEN confidence >= 0.7 THEN 'Medium (0.7-0.9)'
                ELSE 'Low (<0.7)'
            END AS confidence_bucket,
            COUNT(*) as count
        FROM psalms_liturgy_index
        GROUP BY confidence_bucket
    """)

    print("Confidence Distribution:")
    for bucket, count in cursor.fetchall():
        pct = count / total * 100
        print(f"  {bucket}: {count} ({pct:.1f}%)")

    # By match type
    cursor.execute("""
        SELECT match_type, COUNT(*)
        FROM psalms_liturgy_index
        GROUP BY match_type
    """)

    print("\nMatch Type Distribution:")
    for match_type, count in cursor.fetchall():
        pct = count / total * 100
        print(f"  {match_type}: {count} ({pct:.1f}%)")

    conn.close()
```

---

## Success Metrics

### Quantitative Goals
- [ ] Index all 150 Psalms
- [ ] Achieve >90% precision on known liturgical uses (Psalms 23, 92, 113-118, 126, 145)
- [ ] Maintain confidence > 0.7 for 80%+ of matches
- [ ] Support 3 nusachim (Ashkenaz, Sefard, Edot HaMizrach)

### Qualitative Goals
- [ ] AI agents produce richer commentary citing liturgical usage
- [ ] Users gain insight into "reception history" of Psalms
- [ ] System identifies previously unknown connections

---

## Next Steps

### 🎯 RECOMMENDED: Start with Phase 0 (Quick Win)

**I can implement Phase 0 in one session** (4-6 hours):

1. **Create Sefaria links harvester** (~2 hours)
   - Implement `SefariaLinksHarvester` class
   - Add table creation and data storage logic

2. **Run harvest for all 150 Psalms** (~10 minutes)
   - Automated API calls with rate limiting
   - Store ~200-300 liturgical cross-references

3. **Build quick librarian** (~1.5 hours)
   - Implement `SefariaLiturgicalLibrarian` class
   - Add research bundle formatting

4. **Test and integrate** (~30 minutes)
   - Validate with known Psalms (23, 145, etc.)
   - Add to your existing pipeline

**Result**: You'll have liturgical data working in your commentary generation **TODAY**.

---

### Alternative: Full System from Scratch

If you prefer to build the comprehensive system first:

1. **Phase 1**: Database schema (~1 hour)
2. **Phase 2**: Corpus harvesting (~2-3 days)
3. **Phase 3-6**: Phrase detection and indexing (~2-3 weeks)

---

### My Recommendation

**Start with Phase 0**, because:
- ✅ Immediate value (hours, not weeks)
- ✅ No wasted work (Phase 0 becomes validation dataset for Phases 1-6)
- ✅ Learn what you actually need before building complex system
- ✅ Start enhancing commentary today

Then build Phases 1-6 incrementally as you discover gaps in Sefaria's coverage.

**Ready to proceed?** I can start building Phase 0 right now!
