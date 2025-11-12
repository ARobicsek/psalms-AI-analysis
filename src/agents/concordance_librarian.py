"""
Concordance Librarian Agent

Searches the Hebrew concordance database with automatic phrase variation detection.
This is a pure Python data retriever (not an LLM agent).

Key Features:
- Automatic phrase variations (definite/indefinite, with/without prefixes)
- Multi-level normalization (consonantal, voweled, exact)
- Scope filtering (Psalms, Torah, Prophets, Writings, or entire Tanakh)
- Context display with surrounding verses

Hebrew Prefix Variations Tested:
- ה (definite article: "the")
- ו (conjunction: "and")
- ב (preposition: "in/with")
- כ (preposition: "like/as")
- ל (preposition: "to/for")
- מ (preposition: "from")
- Common combinations: וה, וב, וכ, ול, ומ, בה, כה, לה, מה
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass
import json

# Handle imports for both module and script usage
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.concordance.search import ConcordanceSearch, SearchResult
    from src.concordance.hebrew_text_processor import normalize_for_search, split_words
    from src.data_sources.tanakh_database import TanakhDatabase
else:
    from ..concordance.search import ConcordanceSearch, SearchResult
    from ..concordance.hebrew_text_processor import normalize_for_search, split_words
    from ..data_sources.tanakh_database import TanakhDatabase


@dataclass
class ConcordanceRequest:
    """A request for concordance search."""
    query: str  # Hebrew word or phrase
    scope: str = 'Tanakh'  # Psalms, Torah, Prophets, Writings, Tanakh, or 'auto'
    level: str = 'consonantal'  # exact, voweled, or consonantal
    include_variations: bool = True  # Auto-search phrase variations
    notes: Optional[str] = None  # Why this search is being requested
    max_results: int = 50  # Limit results per variation
    auto_scope_threshold: int = 30  # If 'auto' scope: words with >N results get limited scope
    alternate_queries: Optional[List[str]] = None  # Additional forms to search (e.g., different conjugations)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConcordanceRequest':
        """Create from dictionary."""
        return cls(
            query=data['query'],
            scope=data.get('scope', 'Tanakh'),
            level=data.get('level', 'consonantal'),
            include_variations=data.get('include_variations', True),
            notes=data.get('notes'),
            max_results=data.get('max_results', 50),
            auto_scope_threshold=data.get('auto_scope_threshold', 30),
            alternate_queries=data.get('alternate_queries', data.get('alternates'))  # Support both names
        )


@dataclass
class ConcordanceBundle:
    """Bundle of concordance search results."""
    results: List[SearchResult]
    variations_searched: List[str]  # All variations that were searched
    request: ConcordanceRequest

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'results': [
                {
                    'reference': r.reference,
                    'book': r.book,
                    'chapter': r.chapter,
                    'verse': r.verse,
                    'hebrew': r.hebrew_text,
                    'english': r.english_text,
                    'matched_word': r.matched_word,
                    'position': r.word_position
                }
                for r in self.results
            ],
            'total_results': len(self.results),
            'variations_searched': self.variations_searched,
            'request': {
                'query': self.request.query,
                'scope': self.request.scope,
                'level': self.request.level,
                'include_variations': self.request.include_variations
            }
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class ConcordanceLibrarian:
    """
    Fetches concordance results with automatic phrase variation detection.

    This is a pure Python data retriever - no LLM calls are made.
    It intelligently searches for variations of Hebrew phrases:
    - With/without definite article (ה)
    - With/without conjunction (ו = "and")
    - With/without prepositions (ב, כ, ל, מ)
    - Common prefix combinations

    Example:
        If searching for "רועי יהוה" (my shepherd, the LORD):
        - Searches base phrase: "רועי יהוה"
        - Searches with ה: "הרועי היהוה"
        - Searches with ו: "ורועי ויהוה"
        - Searches combinations: "והרועי והיהוה"
        - And more creative variations...
    """

    # Common Hebrew prefixes
    DEFINITE_ARTICLE = 'ה'  # "the"
    CONJUNCTION = 'ו'  # "and"
    PREPOSITIONS = {
        'ב': 'in/with',
        'כ': 'like/as',
        'ל': 'to/for',
        'מ': 'from'
    }

    # Common Hebrew pronominal suffixes (consonantal form)
    PRONOMINAL_SUFFIXES = [
        'י',    # my
        'ך',    # your (m.s.)
        'ו',    # his/its
        'ה',    # her/its
        'נו',   # our
        'כם',   # your (m.pl.)
        'כן',   # your (f.pl.)
        'הם',   # their (m.)
        'הן',   # their (f.)
    ]

    def __init__(self, db: Optional[TanakhDatabase] = None):
        """
        Initialize Concordance Librarian.

        Args:
            db: TanakhDatabase instance (creates new if None)
        """
        self.db = db or TanakhDatabase()
        self.search = ConcordanceSearch(self.db)

    def determine_smart_scope(self, query: str, level: str = 'consonantal', threshold: int = 30) -> str:
        """
        Determine optimal search scope based on word frequency.

        Common words (high frequency) → Limited scope: Genesis, Psalms, Proverbs
        Rare words (low frequency) → Full scope: Entire Tanakh

        Args:
            query: Hebrew word or phrase
            level: Normalization level
            threshold: Frequency threshold (default: 30 occurrences)

        Returns:
            Recommended scope: 'Tanakh' or comma-separated book list

        Example:
            >>> determine_smart_scope("אור")  # "light" - very common
            'Genesis,Psalms,Proverbs'
            >>> determine_smart_scope("מעוז")  # "stronghold" - rare
            'Tanakh'
        """
        # Quick frequency check in Tanakh
        words = split_words(query)
        if len(words) > 1:
            # For phrases, check first word frequency
            query = words[0]

        # Search for word in entire Tanakh to get frequency
        results = self.search.search_word(
            word=query,
            level=level,
            scope='Tanakh',
            limit=threshold + 1,  # Just need to know if it exceeds threshold
            use_split=True  # Use maqqef-split column
        )

        frequency = len(results)

        if frequency > threshold:
            # Common word - limit to key books
            return 'Genesis,Psalms,Proverbs'
        else:
            # Rare word - search entire Tanakh
            return 'Tanakh'

    def generate_phrase_variations(self, phrase: str, level: str = 'consonantal') -> List[str]:
        """
        Generate variations of a Hebrew phrase with different prefixes.

        Enhanced to handle:
        - Maqqef-connected words (combined forms like "מהרבו" from "מה רבו")
        - Pronominal suffixes on final words
        - Various prefix combinations

        Args:
            phrase: Original Hebrew phrase
            level: Normalization level (consonantal, voweled, exact)

        Returns:
            List of phrase variations to search

        Example:
            >>> generate_phrase_variations("רועי יהוה")
            ["רועי יהוה", "הרועי היהוה", "ורועי ויהוה", ...]
        """
        words = split_words(phrase)
        variations = set()

        # Handle empty input
        if not words:
            return []

        # Always include original
        variations.add(phrase)

        # Single-word phrases: generate word-level variations
        if len(words) == 1:
            variations.update(self._generate_word_variations(words[0]))

        # Multi-word phrases: generate phrase-level variations
        else:
            # Add definite article to each word
            with_def = ' '.join([self.DEFINITE_ARTICLE + w for w in words])
            variations.add(with_def)

            # Add conjunction to each word
            with_conj = ' '.join([self.CONJUNCTION + w for w in words])
            variations.add(with_conj)

            # Add conjunction + definite to each word
            with_both = ' '.join([self.CONJUNCTION + self.DEFINITE_ARTICLE + w for w in words])
            variations.add(with_both)

            # Try each preposition on first word only (common pattern)
            for prep in self.PREPOSITIONS:
                var_words = [prep + words[0]] + words[1:]
                variations.add(' '.join(var_words))

                # With conjunction before preposition (ו + preposition)
                var_words = [self.CONJUNCTION + prep + words[0]] + words[1:]
                variations.add(' '.join(var_words))

            # NEW: Generate maqqef-combined versions (words joined as single token)
            # This handles cases like "מה־רבו" stored as "מהרבו"
            variations.update(self._generate_maqqef_combined_variations(words, level))

            # NEW: Add pronominal suffix variations to last word
            variations.update(self._generate_suffix_variations(words, level))

        # Normalize all variations at the requested level
        normalized = set()
        for var in variations:
            norm = normalize_for_search(var, level)
            if norm:  # Only add non-empty
                normalized.add(norm)

        return sorted(list(normalized))

    def _generate_word_variations(self, word: str) -> Set[str]:
        """
        Generate variations for a single word.

        Args:
            word: Hebrew word

        Returns:
            Set of word variations
        """
        variations = {word}

        # Add definite article
        variations.add(self.DEFINITE_ARTICLE + word)

        # Add conjunction
        variations.add(self.CONJUNCTION + word)

        # Add conjunction + definite
        variations.add(self.CONJUNCTION + self.DEFINITE_ARTICLE + word)

        # Add each preposition
        for prep in self.PREPOSITIONS:
            variations.add(prep + word)
            variations.add(self.CONJUNCTION + prep + word)
            variations.add(prep + self.DEFINITE_ARTICLE + word)
            variations.add(self.CONJUNCTION + prep + self.DEFINITE_ARTICLE + word)

        return variations

    def _generate_maqqef_combined_variations(self, words: List[str], level: str) -> Set[str]:
        """
        Generate variations where words are combined as maqqef-connected single tokens.

        In Hebrew text, words connected by maqqef (hyphen) are often stored as single
        tokens in the database. For example:
        - "מה רבו" (two words) may be stored as "מהרבו" (single token)
        - "מרים ראש" may be stored as "מרימראש"

        Args:
            words: List of Hebrew words
            level: Normalization level

        Returns:
            Set of combined variations as single words
        """
        variations = set()

        # For 2-word phrases, generate the combined form
        if len(words) == 2:
            # Direct concatenation (how maqqef words appear in DB)
            combined = words[0] + words[1]
            variations.add(combined)

            # With common prefixes on first word
            for prefix in ['ו', 'ה', 'ב', 'כ', 'ל', 'מ', 'וה', 'וב', 'וכ', 'ול', 'ום']:
                combined_with_prefix = prefix + words[0] + words[1]
                variations.add(combined_with_prefix)

        # For 3-word phrases, try combining pairs
        elif len(words) == 3:
            # First two combined
            variations.add(words[0] + words[1] + ' ' + words[2])
            # Last two combined
            variations.add(words[0] + ' ' + words[1] + words[2])
            # All three combined (rare but possible)
            variations.add(words[0] + words[1] + words[2])

        return variations

    def _generate_suffix_variations(self, words: List[str], level: str) -> Set[str]:
        """
        Generate variations with pronominal suffixes on the last word.

        Hebrew nouns and verbs often take pronominal suffixes. For example:
        - "ראש" (head) → "ראשי" (my head)
        - "מלך" (king) → "מלכו" (his king)

        This also generates combinations with prefixes on the first word,
        since phrases like "מהר קדשו" (from his holy mountain) are common.

        Args:
            words: List of Hebrew words
            level: Normalization level

        Returns:
            Set of phrase variations with suffixes on last word
        """
        variations = set()

        if len(words) < 2:
            return variations

        # Generate variations with each common suffix on the last word
        for suffix in self.PRONOMINAL_SUFFIXES:
            modified_words = words[:-1] + [words[-1] + suffix]
            variation = ' '.join(modified_words)
            variations.add(variation)

            # Try with conjunction on first word
            modified_words_with_vav = [self.CONJUNCTION + words[0]] + words[1:-1] + [words[-1] + suffix]
            variations.add(' '.join(modified_words_with_vav))

            # Try with prepositions on first word (very common pattern)
            for prep in self.PREPOSITIONS:
                modified_words_with_prep = [prep + words[0]] + words[1:-1] + [words[-1] + suffix]
                variations.add(' '.join(modified_words_with_prep))

                # Conjunction + preposition on first word
                modified_words_both = [self.CONJUNCTION + prep + words[0]] + words[1:-1] + [words[-1] + suffix]
                variations.add(' '.join(modified_words_both))

            # Try with definite article on first word
            modified_words_def = [self.DEFINITE_ARTICLE + words[0]] + words[1:-1] + [words[-1] + suffix]
            variations.add(' '.join(modified_words_def))

            # Conjunction + definite on first word
            modified_words_vav_def = [self.CONJUNCTION + self.DEFINITE_ARTICLE + words[0]] + words[1:-1] + [words[-1] + suffix]
            variations.add(' '.join(modified_words_vav_def))

            # Preposition + definite on first word (like מהר -> מ+ה+ר)
            for prep in self.PREPOSITIONS:
                modified_words_prep_def = [prep + self.DEFINITE_ARTICLE + words[0]] + words[1:-1] + [words[-1] + suffix]
                variations.add(' '.join(modified_words_prep_def))

        return variations

    def search_with_variations(self, request: ConcordanceRequest) -> ConcordanceBundle:
        """
        Search concordance with automatic phrase variations.

        Supports smart scoping: Set scope='auto' to automatically limit common words
        to Genesis/Psalms/Proverbs while searching rare words across full Tanakh.

        Args:
            request: ConcordanceRequest specifying query and parameters

        Returns:
            ConcordanceBundle with all results and variations searched

        Example:
            >>> req = ConcordanceRequest(
            ...     query="רעה",
            ...     scope="auto",  # Smart scoping based on frequency
            ...     level="consonantal",
            ...     include_variations=True
            ... )
            >>> bundle = librarian.search_with_variations(req)
            >>> print(f"Found {len(bundle.results)} results")
            >>> print(f"Searched {len(bundle.variations_searched)} variations")
        """
        all_results = []
        variations_searched = []

        # Determine actual scope (handle 'auto' smart scoping)
        actual_scope = request.scope
        if request.scope == 'auto':
            actual_scope = self.determine_smart_scope(
                request.query,
                request.level,
                request.auto_scope_threshold
            )

        # Generate variations if requested
        if request.include_variations:
            queries = self.generate_phrase_variations(request.query, request.level)
        else:
            queries = [request.query]

        # Add alternate queries with their variations
        if request.alternate_queries:
            for alt_query in request.alternate_queries:
                if request.include_variations:
                    alt_variations = self.generate_phrase_variations(alt_query, request.level)
                    queries.extend(alt_variations)
                else:
                    queries.append(alt_query)

        # Search each variation
        seen_verses = set()  # Deduplicate: (book, chapter, verse)

        for query in queries:
            variations_searched.append(query)

            # Determine if this is a phrase or single word
            words = split_words(query)

            if len(words) > 1:
                # Phrase search
                results = self.search.search_phrase(
                    phrase=query,
                    level=request.level,
                    scope=actual_scope,  # Use actual_scope (may be auto-determined)
                    use_split=True  # Use maqqef-split column for better phrase matching
                )
            else:
                # Word search
                results = self.search.search_word(
                    word=query,
                    level=request.level,
                    scope=actual_scope,  # Use actual_scope (may be auto-determined)
                    use_split=True  # Use maqqef-split column for better word matching
                )

            # Add results, deduplicating by verse reference
            for result in results[:request.max_results]:
                verse_key = (result.book, result.chapter, result.verse)
                if verse_key not in seen_verses:
                    seen_verses.add(verse_key)
                    all_results.append(result)

        return ConcordanceBundle(
            results=all_results,
            variations_searched=variations_searched,
            request=request
        )

    def search_multiple(self, requests: List[ConcordanceRequest]) -> List[ConcordanceBundle]:
        """
        Search concordance for multiple queries.

        Args:
            requests: List of ConcordanceRequest objects

        Returns:
            List of ConcordanceBundle objects (one per request)

        Example:
            >>> requests = [
            ...     ConcordanceRequest(query="שמר", scope="Psalms"),
            ...     ConcordanceRequest(query="צדק", scope="Torah"),
            ... ]
            >>> bundles = librarian.search_multiple(requests)
        """
        return [self.search_with_variations(req) for req in requests]

    def search_from_json(self, json_str: str) -> List[ConcordanceBundle]:
        """
        Search concordance from JSON request.

        Args:
            json_str: JSON string with search requests
                Format: {
                    "searches": [
                        {
                            "query": "שמר",
                            "scope": "Psalms",
                            "level": "consonantal",
                            "include_variations": true,
                            "notes": "guard/keep root"
                        }
                    ]
                }

        Returns:
            List of ConcordanceBundle objects

        Example:
            >>> json_request = '''
            ... {
            ...   "searches": [
            ...     {"query": "שמר", "scope": "Psalms", "notes": "guard/keep"}
            ...   ]
            ... }
            ... '''
            >>> bundles = librarian.search_from_json(json_request)
        """
        data = json.loads(json_str)

        requests = []
        for item in data.get('searches', []):
            requests.append(ConcordanceRequest.from_dict(item))

        return self.search_multiple(requests)


def main():
    """Command-line interface for Concordance Librarian."""
    import argparse

    # Ensure UTF-8 for Hebrew output on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Search Hebrew concordance with automatic phrase variations'
    )
    parser.add_argument('query', type=str, nargs='?',
                       help='Hebrew word or phrase to search')
    parser.add_argument('--scope', type=str, default='Tanakh',
                       choices=['Tanakh', 'Torah', 'Prophets', 'Writings', 'Psalms'],
                       help='Search scope (default: Tanakh)')
    parser.add_argument('--level', type=str, default='consonantal',
                       choices=['exact', 'voweled', 'consonantal'],
                       help='Normalization level (default: consonantal)')
    parser.add_argument('--no-variations', action='store_true',
                       help='Disable automatic phrase variations')
    parser.add_argument('--max-results', type=int, default=50,
                       help='Maximum results per variation (default: 50)')
    parser.add_argument('--json', type=str,
                       help='JSON file with multiple search requests')
    parser.add_argument('--output', type=str,
                       help='Output file for results (default: stdout)')

    args = parser.parse_args()

    librarian = ConcordanceLibrarian()

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

    elif args.query:
        # Single search
        request = ConcordanceRequest(
            query=args.query,
            scope=args.scope,
            level=args.level,
            include_variations=not args.no_variations,
            max_results=args.max_results
        )

        bundle = librarian.search_with_variations(request)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(bundle.to_json())
            print(f"Results written to {args.output}")
        else:
            # Display results in human-readable format
            print(f"\n=== Concordance Search: {args.query} ===")
            print(f"Scope: {args.scope}")
            print(f"Level: {args.level}")
            print(f"Variations searched: {len(bundle.variations_searched)}")
            print(f"Total results: {len(bundle.results)}\n")

            if bundle.variations_searched:
                print("Variations searched:")
                for var in bundle.variations_searched[:10]:
                    print(f"  - {var}")
                if len(bundle.variations_searched) > 10:
                    print(f"  ... and {len(bundle.variations_searched) - 10} more")
                print()

            print(f"Results (showing first 10 of {len(bundle.results)}):\n")
            for i, result in enumerate(bundle.results[:10], 1):
                print(f"{i}. {result.reference}")
                print(f"   Hebrew: {result.hebrew_text}")
                print(f"   English: {result.english_text}")
                print(f"   Matched: {result.matched_word} (position {result.word_position})")
                print()

            if len(bundle.results) > 10:
                print(f"... and {len(bundle.results) - 10} more results")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
