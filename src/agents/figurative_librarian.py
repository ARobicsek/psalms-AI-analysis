"""
Figurative Language Librarian Agent

Queries the existing figurative language database (Pentateuch + Psalms + Proverbs).
This is a pure Python data retriever (not an LLM agent).

Key Features:
- Search by book, chapter, verse range
- Filter by figurative type (metaphor, simile, personification, idiom, hyperbole, metonymy)
- Hierarchical Target/Vehicle/Ground/Posture querying
- Full AI deliberation and explanation retrieval

Hierarchical Tag System:
- Target/Vehicle/Ground/Posture stored as JSON arrays: ["specific", "general", "broader", ...]
- Example Target: ["Sun's governing role", "celestial body's function", "cosmic ordering"]
- Queries match at ANY level in the hierarchy
- Search for "animal" finds entries tagged ["fox", "animal", "creature"]
- Search for "fox" finds only fox-specific entries

Database Location:
- C:/Users/ariro/OneDrive/Documents/Bible/database/Pentateuch_Psalms_Proverbs_fig_language.db
- Contains 2,863 figurative instances in Psalms (from CONTEXT.md)
- Includes full AI deliberations and validations
"""

import sys
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from collections import Counter
import json

# Database path
FIGURATIVE_DB_PATH = Path("C:/Users/ariro/OneDrive/Documents/Bible/database/Pentateuch_Psalms_Proverbs_fig_language.db")


@dataclass
class FigurativeInstance:
    """A single instance of figurative language."""
    verse_id: int
    reference: str  # e.g., "Psalms 23:1"
    book: str
    chapter: int
    verse: int
    hebrew_text: str
    english_text: str

    # Figurative type flags
    is_simile: bool
    is_metaphor: bool
    is_personification: bool
    is_idiom: bool
    is_hyperbole: bool
    is_metonymy: bool
    is_other: bool

    # Metadata
    figurative_text: str  # The specific figurative phrase
    figurative_text_hebrew: Optional[str]
    explanation: str
    target: Optional[List[str]]  # Hierarchical tags as list
    vehicle: Optional[List[str]]
    ground: Optional[List[str]]
    posture: Optional[List[str]]
    confidence: float
    speaker: Optional[str]
    purpose: Optional[str]

    # AI transparency
    detection_deliberation: Optional[str]
    tagging_deliberation: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'reference': self.reference,
            'book': self.book,
            'chapter': self.chapter,
            'verse': self.verse,
            'hebrew_text': self.hebrew_text,
            'english_text': self.english_text,
            'types': {
                'simile': self.is_simile,
                'metaphor': self.is_metaphor,
                'personification': self.is_personification,
                'idiom': self.is_idiom,
                'hyperbole': self.is_hyperbole,
                'metonymy': self.is_metonymy,
                'other': self.is_other
            },
            'figurative_text': self.figurative_text,
            'figurative_text_hebrew': self.figurative_text_hebrew,
            'explanation': self.explanation,
            'metadata': {
                'target': self.target,
                'vehicle': self.vehicle,
                'ground': self.ground,
                'posture': self.posture,
                'confidence': self.confidence,
                'speaker': self.speaker,
                'purpose': self.purpose
            },
            'ai_deliberations': {
                'detection': self.detection_deliberation,
                'tagging': self.tagging_deliberation
            }
        }


@dataclass
class FigurativeRequest:
    """A request for figurative language instances."""
    book: Optional[str] = None  # e.g., "Psalms", "Genesis"
    books: Optional[List[str]] = None  # e.g., ["Psalms", "Pentateuch"] for multi-book search
    chapter: Optional[int] = None
    verse_start: Optional[int] = None
    verse_end: Optional[int] = None

    # Filter by type (any can be True)
    simile: bool = False
    metaphor: bool = False
    personification: bool = False
    idiom: bool = False
    hyperbole: bool = False
    metonymy: bool = False

    # Hierarchical metadata filters (matches ANY level in hierarchy)
    target_contains: Optional[str] = None
    vehicle_contains: Optional[str] = None
    ground_contains: Optional[str] = None
    posture_contains: Optional[str] = None

    # Hierarchical vehicle search (NEW for Phase 4)
    vehicle_search_terms: Optional[List[str]] = None  # List of vehicle terms to search (synonyms + broader terms)

    # Text search
    text_search: Optional[str] = None  # Search in figurative_text or explanation

    max_results: int = 500  # Increased from 100 to capture more results
    notes: Optional[str] = None  # Why this search is being requested

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FigurativeRequest':
        """Create from dictionary."""
        return cls(
            book=data.get('book'),
            books=data.get('books'),
            chapter=data.get('chapter'),
            verse_start=data.get('verse_start'),
            verse_end=data.get('verse_end'),
            simile=data.get('simile', False),
            metaphor=data.get('metaphor', False),
            personification=data.get('personification', False),
            idiom=data.get('idiom', False),
            hyperbole=data.get('hyperbole', False),
            metonymy=data.get('metonymy', False),
            target_contains=data.get('target_contains'),
            vehicle_contains=data.get('vehicle_contains'),
            ground_contains=data.get('ground_contains'),
            posture_contains=data.get('posture_contains'),
            vehicle_search_terms=data.get('vehicle_search_terms'),
            text_search=data.get('text_search'),
            max_results=data.get('max_results', 100),
            notes=data.get('notes')
        )


@dataclass
class FigurativeBundle:
    """Bundle of figurative language instances."""
    instances: List[FigurativeInstance]
    request: FigurativeRequest

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'instances': [inst.to_dict() for inst in self.instances],
            'total_results': len(self.instances),
            'request': {
                'book': self.request.book,
                'chapter': self.request.chapter,
                'verse_range': f"{self.request.verse_start}-{self.request.verse_end}" if self.request.verse_start else None,
                'filters': {
                    'types': [t for t in ['simile', 'metaphor', 'personification', 'idiom', 'hyperbole', 'metonymy']
                             if getattr(self.request, t)],
                    'target': self.request.target_contains,
                    'vehicle': self.request.vehicle_contains,
                    'ground': self.request.ground_contains,
                    'posture': self.request.posture_contains
                }
            }
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def get_top_instances(self, limit: int = 3) -> List['FigurativeInstance']:
        """
        Get top N instances sorted by confidence score.

        Args:
            limit: Number of top instances to return (default: 3)

        Returns:
            List of top N FigurativeInstance objects sorted by confidence
        """
        sorted_instances = sorted(self.instances, key=lambda x: x.confidence, reverse=True)
        return sorted_instances[:limit]

    def get_vehicle_frequency(self) -> Dict[str, int]:
        """
        Count frequency of each vehicle (first-level vehicle tag).

        Returns:
            Dictionary mapping vehicle strings to occurrence counts
        """
        vehicles = []
        for inst in self.instances:
            if inst.vehicle and len(inst.vehicle) > 0:
                # Get first-level vehicle tag
                vehicles.append(inst.vehicle[0])
        return dict(Counter(vehicles))

    def get_pattern_summary(self) -> str:
        """
        Generate a brief pattern summary for quick reference.

        Returns:
            Formatted string describing the core pattern and frequency
        """
        total = len(self.instances)
        if total == 0:
            return "No instances found"

        vehicle_freq = self.get_vehicle_frequency()

        # Find most common vehicle
        if vehicle_freq:
            top_vehicle = max(vehicle_freq.items(), key=lambda x: x[1])
            top_vehicle_name, top_vehicle_count = top_vehicle

            # Calculate percentage
            percentage = int((top_vehicle_count / total) * 100)

            return f"**Core pattern**: {top_vehicle_name} metaphor ({top_vehicle_count}/{total} instances, {percentage}%)"
        else:
            return f"**Total instances**: {total}"


class FigurativeLibrarian:
    """
    Queries the figurative language database with hierarchical tag support.

    This is a pure Python data retriever - no LLM calls are made.
    It provides access to 2,863+ figurative language instances from Psalms
    (and thousands more from Torah), with full AI analysis and metadata.

    Key Features:
    - Search by verse reference or range
    - Filter by figurative type(s)
    - Hierarchical Target/Vehicle/Ground/Posture queries
    - Full AI deliberation transparency

    Example:
        >>> librarian = FigurativeLibrarian()
        >>> request = FigurativeRequest(
        ...     book="Psalms",
        ...     metaphor=True,
        ...     vehicle_contains="shepherd"
        ... )
        >>> bundle = librarian.search(request)
        >>> print(f"Found {len(bundle.instances)} shepherd metaphors in Psalms")
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize Figurative Language Librarian.

        Args:
            db_path: Path to figurative language database (uses default if None)
        """
        self.db_path = db_path or FIGURATIVE_DB_PATH

        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Figurative language database not found at {self.db_path}"
            )

    def search(self, request: FigurativeRequest) -> FigurativeBundle:
        """
        Search for figurative language instances.

        Args:
            request: FigurativeRequest specifying search criteria

        Returns:
            FigurativeBundle with matching instances

        Example:
            >>> request = FigurativeRequest(
            ...     book="Psalms",
            ...     chapter=23,
            ...     metaphor=True
            ... )
            >>> bundle = librarian.search(request)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query
        query = """
            SELECT
                f.id as fig_id,
                f.verse_id,
                v.reference,
                v.book,
                v.chapter,
                v.verse,
                v.hebrew_text,
                v.english_text,
                f.final_simile,
                f.final_metaphor,
                f.final_personification,
                f.final_idiom,
                f.final_hyperbole,
                f.final_metonymy,
                f.final_other,
                f.figurative_text,
                f.figurative_text_in_hebrew,
                f.explanation,
                f.target,
                f.vehicle,
                f.ground,
                f.posture,
                f.confidence,
                f.speaker,
                f.purpose,
                v.figurative_detection_deliberation,
                f.tagging_analysis_deliberation
            FROM figurative_language f
            JOIN verses v ON f.verse_id = v.id
            WHERE 1=1
        """

        params = []

        # Filter by book(s)
        if request.books:
            # Multi-book search
            book_placeholders = ", ".join("?" * len(request.books))
            query += f" AND v.book IN ({book_placeholders})"
            params.extend(request.books)
        elif request.book:
            # Single book search
            query += " AND v.book = ?"
            params.append(request.book)

        # Filter by chapter
        if request.chapter is not None:
            query += " AND v.chapter = ?"
            params.append(request.chapter)

        # Filter by verse range
        if request.verse_start is not None:
            query += " AND v.verse >= ?"
            params.append(request.verse_start)

        if request.verse_end is not None:
            query += " AND v.verse <= ?"
            params.append(request.verse_end)

        # Filter by figurative types (OR condition)
        type_conditions = []
        if request.simile:
            type_conditions.append("f.final_simile = 'yes'")
        if request.metaphor:
            type_conditions.append("f.final_metaphor = 'yes'")
        if request.personification:
            type_conditions.append("f.final_personification = 'yes'")
        if request.idiom:
            type_conditions.append("f.final_idiom = 'yes'")
        if request.hyperbole:
            type_conditions.append("f.final_hyperbole = 'yes'")
        if request.metonymy:
            type_conditions.append("f.final_metonymy = 'yes'")

        if type_conditions:
            query += " AND (" + " OR ".join(type_conditions) + ")"

        # Hierarchical metadata filters (use LIKE to match within JSON array)
        # Now supports case-insensitive partial matching for flexibility
        if request.target_contains:
            query += " AND (f.target LIKE ? COLLATE NOCASE)"
            params.append(f'%{request.target_contains}%')

        # Hierarchical vehicle search: search for ANY of the provided terms
        if request.vehicle_search_terms and len(request.vehicle_search_terms) > 0:
            # Build OR conditions for all search terms (specific + synonyms + broader)
            # Use word-boundary patterns to avoid false positives (e.g., "arm" matching "swarm" or "army")
            vehicle_conditions = []
            for term in request.vehicle_search_terms:
                # Create patterns to match whole words in JSON array, with word boundaries:
                # JSON format: ["item1", "item2", "item3"]
                # To prevent false positives (e.g., "arm" matching "army" or "swarm"):
                # - Match term followed by: " (end of element), space, comma, →
                # - Match term preceded by: [", ", " (space)
                # Patterns:
                # 1. ["term"   - term as complete first element
                # 2. ["term    - term at start (may have suffix in same element)
                # 3. ", "term" - term as complete middle/last element
                # 4. ", "term  - term at start of middle/last element
                # 5. " term"   - term after space, at end of element
                # 6. " term    - term after space (in compound)
                patterns = [
                    f'%["{term.lower()}"%',    # Matches ["term"
                    f'%["{term.lower()} %',    # Matches ["term ...
                    f'%["{term.lower()},% ',   # Matches ["term, (rare but possible)
                    f'%, "{term.lower()}"%',   # Matches , "term"
                    f'%, "{term.lower()} %',   # Matches , "term ...
                    f'%, "{term.lower()},% ',  # Matches , "term, (rare)
                    f'% {term.lower()}"%',     # Matches  term" (end of compound)
                    f'% {term.lower()} %',     # Matches  term  (middle of compound)
                ]
                # Combine with OR
                pattern_condition = "(" + " OR ".join(["f.vehicle LIKE ? COLLATE NOCASE"] * len(patterns)) + ")"
                vehicle_conditions.append(pattern_condition)
                params.extend(patterns)
            query += " AND (" + " OR ".join(vehicle_conditions) + ")"
        elif request.vehicle_contains:
            # Fallback to single vehicle search with word boundaries
            term = request.vehicle_contains
            patterns = [
                f'%["{term.lower()}%',
                f'%, "{term.lower()}%',
                f'%"{term.lower()}"%',
                f'% {term.lower()}%',
            ]
            query += " AND (" + " OR ".join(["f.vehicle LIKE ? COLLATE NOCASE"] * len(patterns)) + ")"
            params.extend(patterns)

        if request.ground_contains:
            query += " AND (f.ground LIKE ? COLLATE NOCASE)"
            params.append(f'%{request.ground_contains}%')

        if request.posture_contains:
            query += " AND (f.posture LIKE ? COLLATE NOCASE)"
            params.append(f'%{request.posture_contains}%')

        # Text search in figurative_text or explanation
        if request.text_search:
            query += " AND (f.figurative_text LIKE ? OR f.explanation LIKE ?)"
            search_param = f"%{request.text_search}%"
            params.append(search_param)
            params.append(search_param)

        # Limit results
        query += f" LIMIT {request.max_results}"

        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert to FigurativeInstance objects
        instances = []
        for row in rows:
            # Parse JSON arrays for hierarchical tags
            target = json.loads(row['target']) if row['target'] else None
            vehicle = json.loads(row['vehicle']) if row['vehicle'] else None
            ground = json.loads(row['ground']) if row['ground'] else None
            posture = json.loads(row['posture']) if row['posture'] else None

            instance = FigurativeInstance(
                verse_id=row['verse_id'],
                reference=row['reference'],
                book=row['book'],
                chapter=row['chapter'],
                verse=row['verse'],
                hebrew_text=row['hebrew_text'],
                english_text=row['english_text'],
                is_simile=(row['final_simile'] == 'yes'),
                is_metaphor=(row['final_metaphor'] == 'yes'),
                is_personification=(row['final_personification'] == 'yes'),
                is_idiom=(row['final_idiom'] == 'yes'),
                is_hyperbole=(row['final_hyperbole'] == 'yes'),
                is_metonymy=(row['final_metonymy'] == 'yes'),
                is_other=(row['final_other'] == 'yes'),
                figurative_text=row['figurative_text'] or '',
                figurative_text_hebrew=row['figurative_text_in_hebrew'],
                explanation=row['explanation'] or '',
                target=target,
                vehicle=vehicle,
                ground=ground,
                posture=posture,
                confidence=row['confidence'],
                speaker=row['speaker'],
                purpose=row['purpose'],
                detection_deliberation=row['figurative_detection_deliberation'],
                tagging_deliberation=row['tagging_analysis_deliberation']
            )
            instances.append(instance)

        conn.close()

        return FigurativeBundle(
            instances=instances,
            request=request
        )

    def search_multiple(self, requests: List[FigurativeRequest]) -> List[FigurativeBundle]:
        """
        Search for multiple figurative language queries.

        Args:
            requests: List of FigurativeRequest objects

        Returns:
            List of FigurativeBundle objects (one per request)
        """
        return [self.search(req) for req in requests]

    def search_from_json(self, json_str: str) -> List[FigurativeBundle]:
        """
        Search from JSON request.

        Args:
            json_str: JSON string with search requests
                Format: {
                    "searches": [
                        {
                            "book": "Psalms",
                            "chapter": 23,
                            "metaphor": true,
                            "vehicle_contains": "shepherd",
                            "notes": "Explore shepherd imagery"
                        }
                    ]
                }

        Returns:
            List of FigurativeBundle objects
        """
        data = json.loads(json_str)

        requests = []
        for item in data.get('searches', []):
            requests.append(FigurativeRequest.from_dict(item))

        return self.search_multiple(requests)


def main():
    """Command-line interface for Figurative Language Librarian."""
    import argparse

    # Ensure UTF-8 for Hebrew output on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Query figurative language database with hierarchical tags'
    )
    parser.add_argument('--book', type=str,
                       help='Book name (e.g., "Psalms", "Genesis")')
    parser.add_argument('--chapter', type=int,
                       help='Chapter number')
    parser.add_argument('--verse-start', type=int,
                       help='Starting verse number')
    parser.add_argument('--verse-end', type=int,
                       help='Ending verse number')
    parser.add_argument('--metaphor', action='store_true',
                       help='Filter for metaphors')
    parser.add_argument('--simile', action='store_true',
                       help='Filter for similes')
    parser.add_argument('--personification', action='store_true',
                       help='Filter for personifications')
    parser.add_argument('--idiom', action='store_true',
                       help='Filter for idioms')
    parser.add_argument('--hyperbole', action='store_true',
                       help='Filter for hyperboles')
    parser.add_argument('--metonymy', action='store_true',
                       help='Filter for metonymies')
    parser.add_argument('--target', type=str,
                       help='Filter by target (hierarchical match)')
    parser.add_argument('--vehicle', type=str,
                       help='Filter by vehicle (hierarchical match)')
    parser.add_argument('--ground', type=str,
                       help='Filter by ground (hierarchical match)')
    parser.add_argument('--posture', type=str,
                       help='Filter by posture (hierarchical match)')
    parser.add_argument('--text', type=str,
                       help='Search in figurative text or explanation')
    parser.add_argument('--max-results', type=int, default=20,
                       help='Maximum results (default: 20)')
    parser.add_argument('--json', type=str,
                       help='JSON file with search requests')
    parser.add_argument('--output', type=str,
                       help='Output file for results (default: stdout)')

    args = parser.parse_args()

    try:
        librarian = FigurativeLibrarian()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.json:
        # Load requests from JSON file
        with open(args.json, 'r', encoding='utf-8') as f:
            json_str = f.read()
        bundles = librarian.search_from_json(json_str)

        # Output all bundles
        output = json.dumps(
            [b.to_dict() for b in bundles],
            ensure_ascii=False,
            indent=2
        )

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Results written to {args.output}")
        else:
            print(output)

    else:
        # Build request from command-line args
        request = FigurativeRequest(
            book=args.book,
            chapter=args.chapter,
            verse_start=args.verse_start,
            verse_end=args.verse_end,
            simile=args.simile,
            metaphor=args.metaphor,
            personification=args.personification,
            idiom=args.idiom,
            hyperbole=args.hyperbole,
            metonymy=args.metonymy,
            target_contains=args.target,
            vehicle_contains=args.vehicle,
            ground_contains=args.ground,
            posture_contains=args.posture,
            text_search=args.text,
            max_results=args.max_results
        )

        bundle = librarian.search(request)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(bundle.to_json())
            print(f"Results written to {args.output}")
        else:
            # Display results in human-readable format
            print(f"\n=== Figurative Language Search ===")
            if args.book:
                print(f"Book: {args.book}")
            if args.chapter:
                print(f"Chapter: {args.chapter}")
            print(f"Total results: {len(bundle.instances)}\n")

            for i, inst in enumerate(bundle.instances, 1):
                print(f"{i}. {inst.reference}")
                print(f"   Types: {', '.join([t for t in ['simile', 'metaphor', 'personification', 'idiom', 'hyperbole', 'metonymy'] if getattr(inst, f'is_{t}')])}")
                print(f"   Text: {inst.figurative_text}")
                if inst.figurative_text_hebrew:
                    print(f"   Hebrew: {inst.figurative_text_hebrew}")
                print(f"   Explanation: {inst.explanation[:150]}...")
                if inst.target:
                    print(f"   Target: {' → '.join(inst.target[:3])}")
                if inst.vehicle:
                    print(f"   Vehicle: {' → '.join(inst.vehicle[:3])}")
                if inst.ground:
                    print(f"   Ground: {' → '.join(inst.ground[:3])}")
                print(f"   Confidence: {inst.confidence:.2f}")
                print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
