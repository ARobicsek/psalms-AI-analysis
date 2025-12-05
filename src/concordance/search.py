"""
Hebrew Concordance Search

Provides search functionality for the Hebrew concordance database.
Supports:
- Single word search at different normalization levels
- Multi-word phrase search
- Scope filtering (Psalms, Torah, Prophets, Writings, or entire Tanakh)
"""

import sqlite3
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

# Handle imports for both module and script usage
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.concordance.hebrew_text_processor import (
        normalize_for_search, split_words, normalize_word_sequence, is_hebrew_text
    )
    from src.data_sources.tanakh_database import TanakhDatabase, TANAKH_BOOKS
else:
    from .hebrew_text_processor import (
        normalize_for_search, split_words, normalize_word_sequence, is_hebrew_text
    )
    from ..data_sources.tanakh_database import TanakhDatabase, TANAKH_BOOKS


@dataclass
class SearchResult:
    """A single concordance search result."""
    book: str
    chapter: int
    verse: int
    reference: str
    hebrew_text: str
    english_text: str
    matched_word: str
    word_position: int


class ConcordanceSearch:
    """Search interface for Hebrew concordance."""

    # Hebrew pronominal suffixes for matching word variations
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

    # Hebrew preposition prefixes
    PREPOSITIONS = [
        'ב',    # in/at/with
        'ל',    # to/for
        'מ',    # from
        'כ',    # like/as
        'ה',    # the (definite article)
        'ו',    # and (conjunction)
        'ש',    # that/which (relative)
    ]

    # Combined prefixes (conjunction + preposition)
    COMBINED_PREFIXES = [
        'וב',   # and in
        'ול',   # and to
        'ומ',   # and from
        'וכ',   # and like
        'וה',   # and the
        'בה',   # in the
        'לה',   # to the
        'מה',   # from the
        'כה',   # like the
    ]

    def __init__(self, db: Optional[TanakhDatabase] = None):
        """
        Initialize concordance search.

        Args:
            db: TanakhDatabase instance (creates new if None)
        """
        self.db = db or TanakhDatabase()
        self._own_db = db is None  # Track if we own the db connection

    def search_word(self,
                    word: str,
                    level: str = 'consonantal',
                    scope: str = 'Tanakh',
                    limit: Optional[int] = None,
                    use_split: bool = True) -> List[SearchResult]:
        """
        Search for a Hebrew word in the concordance.

        Args:
            word: Hebrew word to search for
            level: Normalization level - 'exact', 'voweled', or 'consonantal'
            scope: Search scope - 'Tanakh', 'Torah', 'Prophets', 'Writings', or book name
            limit: Maximum number of results (None for all)
            use_split: If True and level='consonantal', use maqqef-split column (default: True)

        Returns:
            List of SearchResult objects

        Examples:
            >>> search = ConcordanceSearch()
            >>> results = search.search_word("שמר", level='consonantal', scope='Psalms')
        """
        if not is_hebrew_text(word):
            raise ValueError(f"Input must contain Hebrew text: {word}")

        # Normalize the search word (use split normalization if requested)
        if use_split and level == 'consonantal':
            from .hebrew_text_processor import normalize_for_search_split
            normalized = normalize_for_search_split(word, level)
        else:
            normalized = normalize_for_search(word, level)

        # Determine column to search based on level and use_split flag
        if use_split and level == 'consonantal':
            column = 'word_consonantal_split'
        elif level == 'exact':
            column = 'word'
        elif level == 'voweled':
            column = 'word_voweled'
        else:  # consonantal without split
            column = 'word_consonantal'

        # Build query
        query = f"""
            SELECT DISTINCT
                c.book_name, c.chapter, c.verse, c.word, c.position,
                v.hebrew, v.english, v.reference
            FROM concordance c
            JOIN verses v ON
                c.book_name = v.book_name AND
                c.chapter = v.chapter AND
                c.verse = v.verse
            WHERE c.{column} = ?
        """

        params = [normalized]

        # Add scope filtering
        query, params = self._add_scope_filter(query, params, scope)

        # Add ordering
        query += " ORDER BY c.book_name, c.chapter, c.verse, c.position"

        # Add limit
        if limit:
            query += f" LIMIT {limit}"

        # Execute query
        cursor = self.db.conn.cursor()
        cursor.execute(query, params)

        # Convert to SearchResult objects
        results = []
        for row in cursor.fetchall():
            result = SearchResult(
                book=row['book_name'],
                chapter=row['chapter'],
                verse=row['verse'],
                reference=row['reference'],
                hebrew_text=row['hebrew'],
                english_text=row['english'],
                matched_word=row['word'],
                word_position=row['position']
            )
            results.append(result)

        return results

    def search_phrase(self,
                      phrase: str,
                      level: str = 'consonantal',
                      scope: str = 'Tanakh',
                      limit: Optional[int] = None,
                      use_split: bool = True) -> List[SearchResult]:
        """
        Search for a multi-word Hebrew phrase in the concordance.

        Args:
            phrase: Hebrew phrase (space-separated words)
            level: Normalization level
            scope: Search scope
            limit: Maximum number of results
            use_split: If True and level='consonantal', use maqqef-split column (default: True)

        Returns:
            List of SearchResult objects where the phrase appears

        Example:
            >>> search.search_phrase("יהוה רעי", level='consonantal')
            # Returns matches for "The LORD is my shepherd"
        """
        if not is_hebrew_text(phrase):
            raise ValueError(f"Input must contain Hebrew text: {phrase}")

        # Split and normalize phrase words (use split normalization if requested)
        if use_split and level == 'consonantal':
            from .hebrew_text_processor import normalize_for_search_split, split_on_maqqef
            # First split on maqqef, then split into words
            phrase_split = split_on_maqqef(phrase)
            words = split_words(phrase_split)
        else:
            words = split_words(phrase)

        if len(words) < 2:
            # Single word - use word search instead
            return self.search_word(words[0] if words else phrase, level, scope, limit, use_split)

        # Normalize each word
        if use_split and level == 'consonantal':
            from .hebrew_text_processor import normalize_for_search_split
            normalized_words = [normalize_for_search_split(w, level) for w in words]
        else:
            normalized_words = normalize_word_sequence(words, level)

        # Determine column based on level and use_split flag
        if use_split and level == 'consonantal':
            column = 'word_consonantal_split'
        elif level == 'exact':
            column = 'word'
        elif level == 'voweled':
            column = 'word_voweled'
        else:
            column = 'word_consonantal'

        # Strategy: Find first word, then check if following words match
        results = []

        # Search for first word
        first_word_results = self.search_word(words[0], level, scope, limit=None, use_split=use_split)

        for first_match in first_word_results:
            # Check if this verse contains the full phrase
            if self._verse_contains_phrase(
                first_match.book,
                first_match.chapter,
                first_match.verse,
                first_match.word_position,
                normalized_words,
                column
            ):
                # Add to results (avoid duplicates)
                if not any(r.reference == first_match.reference for r in results):
                    results.append(first_match)

                    # Check limit
                    if limit and len(results) >= limit:
                        return results

        return results

    def _verse_contains_phrase(self,
                                book: str,
                                chapter: int,
                                verse: int,
                                start_position: int,
                                normalized_words: List[str],
                                column: str) -> bool:
        """
        Check if a verse contains a phrase starting at a specific position.

        Enhanced to skip empty positions (paseq marks, etc.) when matching.

        Args:
            book, chapter, verse: Verse location
            start_position: Position of first word
            normalized_words: List of normalized words to match
            column: Column to check (word, word_voweled, or word_consonantal)

        Returns:
            True if phrase matches at this position
        """
        cursor = self.db.conn.cursor()

        # Get ALL words from this verse starting from start_position
        cursor.execute(f"""
            SELECT position, {column}
            FROM concordance
            WHERE book_name = ? AND chapter = ? AND verse = ? AND position >= ?
            ORDER BY position
        """, (book, chapter, verse, start_position))

        verse_words = cursor.fetchall()

        # Filter out empty positions (paseq marks, etc.)
        non_empty_words = [(pos, word) for pos, word in verse_words if word and word.strip()]

        # Check if we have enough words
        if len(non_empty_words) < len(normalized_words):
            return False

        # Match normalized words against the first N non-empty words
        for i, expected_word in enumerate(normalized_words):
            if i >= len(non_empty_words):
                return False
            actual_word = non_empty_words[i][1]
            if actual_word != expected_word:
                return False

        return True

    def search_phrase_in_verse(self,
                               phrase: str,
                               level: str = 'consonantal',
                               scope: str = 'Tanakh',
                               limit: Optional[int] = None,
                               use_split: bool = True) -> List[SearchResult]:
        """
        Search for verses containing ALL words of a phrase (any order, not necessarily adjacent).

        This is a fallback/broader search when strict phrase matching fails.
        Useful for finding conceptual matches where words appear in the same verse
        but not necessarily next to each other.

        Args:
            phrase: Hebrew phrase (space-separated words)
            level: Normalization level
            scope: Search scope
            limit: Maximum number of results
            use_split: If True and level='consonantal', use maqqef-split column

        Returns:
            List of SearchResult objects where ALL phrase words appear in the verse
        """
        if not is_hebrew_text(phrase):
            raise ValueError(f"Input must contain Hebrew text: {phrase}")

        # Split and normalize phrase words
        if use_split and level == 'consonantal':
            from .hebrew_text_processor import normalize_for_search_split, split_on_maqqef
            phrase_split = split_on_maqqef(phrase)
            words = split_words(phrase_split)
        else:
            words = split_words(phrase)

        if len(words) < 2:
            return self.search_word(words[0] if words else phrase, level, scope, limit, use_split)

        # Normalize each word
        if use_split and level == 'consonantal':
            from .hebrew_text_processor import normalize_for_search_split
            normalized_words = [normalize_for_search_split(w, level) for w in words]
        else:
            normalized_words = normalize_word_sequence(words, level)

        # Determine column
        if use_split and level == 'consonantal':
            column = 'word_consonantal_split'
        elif level == 'exact':
            column = 'word'
        elif level == 'voweled':
            column = 'word_voweled'
        else:
            column = 'word_consonantal'

        # Find verses containing ALL words (any position)
        # Strategy: Find first word (with suffix variations), then check if verse contains all other words
        results = []
        first_word_results = self.search_word_with_variations(words[0], level, scope, limit=None, use_split=use_split)

        for first_match in first_word_results:
            # Check if this verse contains ALL other words
            if self._verse_contains_all_words(
                first_match.book,
                first_match.chapter,
                first_match.verse,
                normalized_words[1:],  # All words except first
                column
            ):
                # Avoid duplicates
                if not any(r.reference == first_match.reference for r in results):
                    results.append(first_match)
                    if limit and len(results) >= limit:
                        return results

        return results

    # Hebrew final letter to regular letter mapping
    FINAL_TO_REGULAR = {
        'ך': 'כ',  # final kaf → kaf
        'ם': 'מ',  # final mem → mem
        'ן': 'נ',  # final nun → nun
        'ף': 'פ',  # final peh → peh
        'ץ': 'צ',  # final tsade → tsade
    }

    def _get_word_variations(self, word: str) -> set:
        """
        Generate all prefix and suffix variations for a word.
        Handles:
        - Prefix additions (ב, ל, מ, כ, ה, ו, ש and combinations)
        - Suffix additions (pronominal suffixes)
        - Final letter conversion (e.g., ף → פ when suffix added)
        - Internal vowel letter removal (e.g., לשון → לשנו, not לשונו)

        Args:
            word: Normalized Hebrew word

        Returns:
            Set of word variations including prefixed and suffixed forms
        """
        variations = {word}  # Include original word

        # === PREFIX VARIATIONS ===
        # Add single prefixes
        for prefix in self.PREPOSITIONS:
            variations.add(prefix + word)

        # Add combined prefixes
        for prefix in self.COMBINED_PREFIXES:
            variations.add(prefix + word)

        # === SUFFIX VARIATIONS ===
        # Check if word ends with a final letter
        if word and word[-1] in self.FINAL_TO_REGULAR:
            # Convert final letter to regular form for suffix additions
            base = word[:-1] + self.FINAL_TO_REGULAR[word[-1]]
        else:
            base = word

        # Add suffix variations (standard)
        for suffix in self.PRONOMINAL_SUFFIXES:
            variations.add(base + suffix)
            # Also add prefixed + suffixed forms
            for prefix in self.PREPOSITIONS:
                variations.add(prefix + base + suffix)

        # Also try removing internal vowel letters (vav/yod) before adding suffix
        # This handles patterns like לשון → לשנו (where internal vav is removed)
        if len(word) >= 3:
            for i in range(1, len(word) - 1):  # Check internal positions only
                if word[i] in ('ו', 'י'):  # Vowel letters vav or yod
                    # Remove the vowel letter
                    shortened = word[:i] + word[i+1:]
                    # Handle final letter conversion on shortened form
                    if shortened and shortened[-1] in self.FINAL_TO_REGULAR:
                        short_base = shortened[:-1] + self.FINAL_TO_REGULAR[shortened[-1]]
                    else:
                        short_base = shortened
                    # Add suffix variations for shortened form
                    for suffix in self.PRONOMINAL_SUFFIXES:
                        variations.add(short_base + suffix)
                        # Also add prefixed + suffixed forms
                        for prefix in self.PREPOSITIONS:
                            variations.add(prefix + short_base + suffix)

        return variations

    def search_word_with_variations(self,
                                     word: str,
                                     level: str = 'consonantal',
                                     scope: str = 'Tanakh',
                                     limit: Optional[int] = None,
                                     use_split: bool = True) -> List[SearchResult]:
        """
        Search for a Hebrew word and all its suffix variations.

        Args:
            word: Hebrew word to search for
            level: Normalization level
            scope: Search scope
            limit: Maximum number of results
            use_split: If True and level='consonantal', use maqqef-split column

        Returns:
            List of SearchResult objects matching the word or any suffix variation
        """
        # Get all suffix variations
        if use_split and level == 'consonantal':
            from .hebrew_text_processor import normalize_for_search_split
            normalized = normalize_for_search_split(word, level)
        else:
            normalized = normalize_for_search(word, level)

        variations = self._get_word_variations(normalized)

        # Determine column
        if use_split and level == 'consonantal':
            column = 'word_consonantal_split'
        elif level == 'exact':
            column = 'word'
        elif level == 'voweled':
            column = 'word_voweled'
        else:
            column = 'word_consonantal'

        # Build query with IN clause for all variations
        placeholders = ','.join('?' * len(variations))
        query = f"""
            SELECT DISTINCT
                c.book_name, c.chapter, c.verse, c.word, c.position,
                v.hebrew, v.english, v.reference
            FROM concordance c
            JOIN verses v ON
                c.book_name = v.book_name AND
                c.chapter = v.chapter AND
                c.verse = v.verse
            WHERE c.{column} IN ({placeholders})
        """

        params = list(variations)

        # Add scope filtering
        query, params = self._add_scope_filter(query, params, scope)

        # Add ordering
        query += " ORDER BY c.book_name, c.chapter, c.verse, c.position"

        # Add limit
        if limit:
            query += f" LIMIT {limit}"

        # Execute query
        cursor = self.db.conn.cursor()
        cursor.execute(query, params)

        # Convert to SearchResult objects
        results = []
        for row in cursor.fetchall():
            result = SearchResult(
                book=row['book_name'],
                chapter=row['chapter'],
                verse=row['verse'],
                reference=row['reference'],
                hebrew_text=row['hebrew'],
                english_text=row['english'],
                matched_word=row['word'],
                word_position=row['position']
            )
            results.append(result)

        return results

    def _verse_contains_all_words(self,
                                   book: str,
                                   chapter: int,
                                   verse: int,
                                   normalized_words: List[str],
                                   column: str) -> bool:
        """
        Check if a verse contains ALL specified words (any position).
        Supports suffix variations - a word matches if any suffix form appears.

        Args:
            book, chapter, verse: Verse location
            normalized_words: List of normalized words that must all appear
            column: Column to check

        Returns:
            True if ALL words (or their suffix variations) appear somewhere in the verse
        """
        cursor = self.db.conn.cursor()

        # Get all words in this verse
        cursor.execute(f"""
            SELECT {column}
            FROM concordance
            WHERE book_name = ? AND chapter = ? AND verse = ?
        """, (book, chapter, verse))

        verse_words = set(row[0] for row in cursor.fetchall() if row[0] and row[0].strip())

        # Check if all required words (or their suffix variations) are present
        for word in normalized_words:
            word_variations = self._get_word_variations(word)
            # Check if ANY variation of this word appears in the verse
            if not any(variation in verse_words for variation in word_variations):
                return False

        return True

    def _add_scope_filter(self, query: str, params: List, scope: str) -> tuple:
        """
        Add scope filtering to a query.

        Args:
            query: SQL query string
            params: Query parameters list
            scope: Scope to filter by - can be 'Tanakh', 'Torah', 'Prophets', 'Writings',
                   a single book name, or comma-separated book names (e.g., 'Genesis,Psalms,Proverbs')

        Returns:
            Tuple of (modified_query, modified_params)
        """
        if scope == 'Tanakh':
            # No filter needed
            return query, params

        elif scope in ['Torah', 'Prophets', 'Writings']:
            # Filter by category
            books_in_category = [book[0] for book in TANAKH_BOOKS[scope]]
            placeholders = ','.join('?' * len(books_in_category))
            query += f" AND c.book_name IN ({placeholders})"
            params.extend(books_in_category)

        elif ',' in scope:
            # Multiple books specified (e.g., "Genesis,Psalms,Proverbs")
            books = [book.strip() for book in scope.split(',')]
            placeholders = ','.join('?' * len(books))
            query += f" AND c.book_name IN ({placeholders})"
            params.extend(books)

        else:
            # Assume it's a single book name
            query += " AND c.book_name = ?"
            params.append(scope)

        return query, params

    def get_statistics(self, scope: str = 'Tanakh') -> Dict[str, Any]:
        """
        Get statistics about concordance coverage.

        Args:
            scope: Scope to get statistics for

        Returns:
            Dictionary with word counts, verse counts, etc.
        """
        cursor = self.db.conn.cursor()

        # Build base query
        query_base = "FROM concordance c"
        params = []

        # Add scope filter
        if scope != 'Tanakh':
            if scope in ['Torah', 'Prophets', 'Writings']:
                books = [book[0] for book in TANAKH_BOOKS[scope]]
                placeholders = ','.join('?' * len(books))
                query_base += f" WHERE c.book_name IN ({placeholders})"
                params.extend(books)
            else:
                query_base += " WHERE c.book_name = ?"
                params.append(scope)

        # Get statistics
        cursor.execute(f"SELECT COUNT(*) as count {query_base}", params)
        total_words = cursor.fetchone()['count']

        cursor.execute(f"SELECT COUNT(DISTINCT word_consonantal) as count {query_base}", params)
        unique_consonantal = cursor.fetchone()['count']

        cursor.execute(f"SELECT COUNT(DISTINCT book_name || '-' || chapter || '-' || verse) as count {query_base}", params)
        verses_with_words = cursor.fetchone()['count']

        return {
            'scope': scope,
            'total_words': total_words,
            'unique_roots': unique_consonantal,
            'verses_indexed': verses_with_words
        }

    def search_substring(self,
                        root: str,
                        level: str = 'consonantal',
                        scope: str = 'Tanakh',
                        limit: Optional[int] = None,
                        use_split: bool = True) -> List[SearchResult]:
        """
        Search for words containing a root substring (broader discovery).

        This is Phase 2 of the hybrid search strategy. Unlike search_word()
        which looks for exact matches, this finds ANY word containing the
        root consonants, enabling discovery of forms not generated by
        pattern-based morphology.

        Args:
            root: Hebrew root consonants to search for
            level: Normalization level (typically 'consonantal' for root search)
            scope: Search scope
            limit: Maximum number of results
            use_split: If True and level='consonantal', use maqqef-split column (default: True)

        Returns:
            List of SearchResult objects

        Example:
            >>> search.search_substring("אהב", level='consonantal')
            # Finds: אהב, אהבה, אהבו, ואהבתם, etc.
        """
        if not is_hebrew_text(root):
            raise ValueError(f"Input must contain Hebrew text: {root}")

        # Normalize the root (use split normalization if requested)
        if use_split and level == 'consonantal':
            from .hebrew_text_processor import normalize_for_search_split
            normalized = normalize_for_search_split(root, level)
        else:
            normalized = normalize_for_search(root, level)

        # Determine column based on level and use_split flag
        if use_split and level == 'consonantal':
            column = 'word_consonantal_split'
        elif level == 'exact':
            column = 'word'
        elif level == 'voweled':
            column = 'word_voweled'
        else:
            column = 'word_consonantal'

        # Build query with LIKE for substring matching
        query = f"""
            SELECT DISTINCT
                c.book_name, c.chapter, c.verse, c.word, c.position,
                v.hebrew, v.english, v.reference
            FROM concordance c
            JOIN verses v ON
                c.book_name = v.book_name AND
                c.chapter = v.chapter AND
                c.verse = v.verse
            WHERE c.{column} LIKE ?
        """

        # Use SQL wildcards for substring search
        params = [f"%{normalized}%"]

        # Add scope filtering
        query, params = self._add_scope_filter(query, params, scope)

        # Add ordering
        query += " ORDER BY c.book_name, c.chapter, c.verse, c.position"

        # Add limit
        if limit:
            query += f" LIMIT {limit}"

        # Execute query
        cursor = self.db.conn.cursor()
        cursor.execute(query, params)

        # Convert to SearchResult objects
        results = []
        for row in cursor.fetchall():
            result = SearchResult(
                book=row['book_name'],
                chapter=row['chapter'],
                verse=row['verse'],
                reference=row['reference'],
                hebrew_text=row['hebrew'],
                english_text=row['english'],
                matched_word=row['word'],
                word_position=row['position']
            )
            results.append(result)

        return results

    def close(self):
        """Close database connection if we own it."""
        if self._own_db:
            self.db.close()

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close()


def main():
    """Command-line interface for concordance search."""
    import argparse

    # Ensure UTF-8 for Hebrew output on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description='Search Hebrew concordance')
    parser.add_argument('--word', type=str, help='Hebrew word to search for')
    parser.add_argument('--phrase', type=str, help='Hebrew phrase to search for')
    parser.add_argument('--level', type=str, default='consonantal',
                       choices=['exact', 'voweled', 'consonantal'],
                       help='Normalization level (default: consonantal)')
    parser.add_argument('--scope', type=str, default='Tanakh',
                       help='Search scope: Tanakh, Torah, Prophets, Writings, or book name')
    parser.add_argument('--limit', type=int, default=10,
                       help='Maximum results to show (default: 10, use 0 for all)')
    parser.add_argument('--stats', action='store_true',
                       help='Show concordance statistics')

    args = parser.parse_args()

    with ConcordanceSearch() as search:
        if args.stats:
            stats = search.get_statistics(args.scope)
            print(f"\n=== Concordance Statistics ({stats['scope']}) ===")
            print(f"Total words indexed: {stats['total_words']:,}")
            print(f"Unique roots: {stats['unique_roots']:,}")
            print(f"Verses indexed: {stats['verses_indexed']:,}")

        elif args.phrase:
            print(f"\n=== Searching for phrase: {args.phrase} ===")
            print(f"Level: {args.level}, Scope: {args.scope}\n")

            limit = args.limit if args.limit > 0 else None
            results = search.search_phrase(args.phrase, args.level, args.scope, limit)

            print(f"Found {len(results)} matches:\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.reference}")
                print(f"   Hebrew: {result.hebrew_text}")
                print(f"   English: {result.english_text}\n")

        elif args.word:
            print(f"\n=== Searching for word: {args.word} ===")
            print(f"Level: {args.level}, Scope: {args.scope}\n")

            limit = args.limit if args.limit > 0 else None
            results = search.search_word(args.word, args.level, args.scope, limit)

            print(f"Found {len(results)} matches:\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.reference}")
                print(f"   Hebrew: {result.hebrew_text}")
                print(f"   English: {result.english_text}\n")

        else:
            parser.print_help()


if __name__ == '__main__':
    main()
