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
                    limit: Optional[int] = None) -> List[SearchResult]:
        """
        Search for a Hebrew word in the concordance.

        Args:
            word: Hebrew word to search for
            level: Normalization level - 'exact', 'voweled', or 'consonantal'
            scope: Search scope - 'Tanakh', 'Torah', 'Prophets', 'Writings', or book name
            limit: Maximum number of results (None for all)

        Returns:
            List of SearchResult objects

        Examples:
            >>> search = ConcordanceSearch()
            >>> results = search.search_word("שמר", level='consonantal', scope='Psalms')
        """
        if not is_hebrew_text(word):
            raise ValueError(f"Input must contain Hebrew text: {word}")

        # Normalize the search word
        normalized = normalize_for_search(word, level)

        # Determine column to search based on level
        if level == 'exact':
            column = 'word'
        elif level == 'voweled':
            column = 'word_voweled'
        else:  # consonantal
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
                      limit: Optional[int] = None) -> List[SearchResult]:
        """
        Search for a multi-word Hebrew phrase in the concordance.

        Args:
            phrase: Hebrew phrase (space-separated words)
            level: Normalization level
            scope: Search scope
            limit: Maximum number of results

        Returns:
            List of SearchResult objects where the phrase appears

        Example:
            >>> search.search_phrase("יהוה רעי", level='consonantal')
            # Returns matches for "The LORD is my shepherd"
        """
        if not is_hebrew_text(phrase):
            raise ValueError(f"Input must contain Hebrew text: {phrase}")

        # Split and normalize phrase words
        words = split_words(phrase)
        if len(words) < 2:
            # Single word - use word search instead
            return self.search_word(words[0] if words else phrase, level, scope, limit)

        normalized_words = normalize_word_sequence(words, level)

        # Determine column based on level
        if level == 'exact':
            column = 'word'
        elif level == 'voweled':
            column = 'word_voweled'
        else:
            column = 'word_consonantal'

        # Strategy: Find first word, then check if following words match
        results = []

        # Search for first word
        first_word_results = self.search_word(words[0], level, scope, limit=None)

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

        Args:
            book, chapter, verse: Verse location
            start_position: Position of first word
            normalized_words: List of normalized words to match
            column: Column to check (word, word_voweled, or word_consonantal)

        Returns:
            True if phrase matches at this position
        """
        cursor = self.db.conn.cursor()

        # Get words from this verse at sequential positions
        for i, expected_word in enumerate(normalized_words):
            cursor.execute(f"""
                SELECT {column}
                FROM concordance
                WHERE book_name = ? AND chapter = ? AND verse = ? AND position = ?
            """, (book, chapter, verse, start_position + i))

            row = cursor.fetchone()
            if not row or row[column] != expected_word:
                return False

        return True

    def _add_scope_filter(self, query: str, params: List, scope: str) -> tuple:
        """
        Add scope filtering to a query.

        Args:
            query: SQL query string
            params: Query parameters list
            scope: Scope to filter by

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

        else:
            # Assume it's a book name
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
                        limit: Optional[int] = None) -> List[SearchResult]:
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

        Returns:
            List of SearchResult objects

        Example:
            >>> search.search_substring("אהב", level='consonantal')
            # Finds: אהב, אהבה, אהבו, ואהבתם, etc.
        """
        if not is_hebrew_text(root):
            raise ValueError(f"Input must contain Hebrew text: {root}")

        # Normalize the root
        normalized = normalize_for_search(root, level)

        # Determine column based on level
        if level == 'exact':
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
