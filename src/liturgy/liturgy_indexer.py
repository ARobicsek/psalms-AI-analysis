"""
Liturgy Indexer for Liturgical Librarian - Phase 4

Indexes Psalms phrases against the liturgical corpus (1,113 prayers).
Searches each phrase extracted in Phase 3 using consonantal normalization
and stores matches with confidence scores.

Architecture:
- Uses phrase cache from Phase 3 (12,253 phrases)
- Searches in prayers table (1,113 liturgical texts)
- Consonantal normalization (ignores vowels, cantillation, punctuation, maqqef)
- Confidence scoring based on distinctiveness
- Stores matches in psalms_liturgy_index table

Created: 2025-10-26
Phase: Liturgical Librarian Phase 4
"""

import sqlite3
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# Import Hebrew text processing utilities
import sys
sys.path.append(str(Path(__file__).parent.parent))
from concordance.hebrew_text_processor import (
    normalize_for_search,
    split_words,
    strip_vowels
)


class LiturgyIndexer:
    """Build index of Psalms phrases in liturgical texts."""

    def __init__(
        self,
        liturgy_db: str = "data/liturgy.db",
        tanakh_db: str = "database/tanakh.db",
        verbose: bool = True
    ):
        """
        Initialize liturgy indexer with database connections.

        Args:
            liturgy_db: Path to liturgy database (prayers + phrase cache + index)
            tanakh_db: Path to Tanakh database (canonical Psalms source)
            verbose: Print progress messages
        """
        self.liturgy_db = liturgy_db
        self.tanakh_db = tanakh_db
        self.verbose = verbose

        # Normalization level mapping
        self.NORM_LEVELS = {
            0: 'exact',      # Exact match (all diacritics)
            1: 'voweled',    # Vowels only (no cantillation)
            2: 'consonantal' # Consonants only
        }

    def index_psalm(self, psalm_chapter: int) -> Dict:
        """
        Build complete index for a single Psalm.

        Args:
            psalm_chapter: Psalm number (1-150)

        Returns:
            Dictionary with indexing statistics
        """
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"Indexing Psalm {psalm_chapter} against liturgical corpus")
            print(f"{'='*70}\n")

        # Extract phrases for this Psalm
        phrases = self._extract_phrases(psalm_chapter)

        if not phrases:
            if self.verbose:
                print(f"⚠ No phrases found for Psalm {psalm_chapter}")
            return {'psalm_chapter': psalm_chapter, 'total_matches': 0, 'error': 'No phrases extracted'}

        # Filter to searchable only
        searchable = [p for p in phrases if p['is_searchable']]

        if self.verbose:
            print(f"Cached phrases: {len(phrases)}")
            print(f"Searchable phrases: {len(searchable)} ({len(searchable)/len(phrases)*100:.1f}%)")
            print(f"Filtering out {len(phrases) - len(searchable)} low-distinctiveness phrases\n")

        # Also index full verses (exact quotations)
        full_verses = self._get_full_verses(psalm_chapter)
        searchable.extend(full_verses)

        if self.verbose:
            print(f"Added {len(full_verses)} full verses for exact matching")
            print(f"Total searchable items: {len(searchable)}\n")

        # Clear existing index for this Psalm (allows re-indexing)
        self._clear_existing_index(psalm_chapter)

        # Search each phrase in liturgy
        total_matches = 0
        match_details = {}

        for i, phrase_data in enumerate(searchable, 1):
            phrase_text = phrase_data['phrase'][:60] + ('...' if len(phrase_data['phrase']) > 60 else '')

            if self.verbose:
                print(f"[{i}/{len(searchable)}] {phrase_text}")

            matches = self._search_liturgy(
                phrase_hebrew=phrase_data['phrase'],
                psalm_chapter=psalm_chapter,
                psalm_verse_start=phrase_data.get('verse_start'),
                psalm_verse_end=phrase_data.get('verse_end'),
                distinctiveness_score=phrase_data.get('distinctiveness_score', 0.0)
            )

            if matches:
                if self.verbose:
                    print(f"  ✓ Found {len(matches)} match(es)")
                total_matches += len(matches)

                # Track match types
                for match in matches:
                    match_type = match['match_type']
                    match_details[match_type] = match_details.get(match_type, 0) + 1

                # Store in index
                for match in matches:
                    self._store_match(match)

        if self.verbose:
            print(f"\n{'='*70}")
            print(f"✓ Indexing complete for Psalm {psalm_chapter}")
            print(f"{'='*70}")
            print(f"Total matches: {total_matches}")
            if match_details:
                print(f"\nMatch breakdown:")
                for match_type, count in sorted(match_details.items(), key=lambda x: -x[1]):
                    print(f"  {match_type.replace('_', ' ').title()}: {count}")
            print()

        return {
            'psalm_chapter': psalm_chapter,
            'total_phrases': len(phrases),
            'searchable_phrases': len(searchable),
            'total_matches': total_matches,
            'match_details': match_details
        }

    def _extract_phrases(self, psalm_chapter: int) -> List[Dict]:
        """Extract phrases for this Psalm using PhraseExtractor."""
        from liturgy.phrase_extractor import PhraseExtractor

        extractor = PhraseExtractor(
            tanakh_db=self.tanakh_db,
            liturgy_db=self.liturgy_db,
            verbose=False  # Don't spam output during indexing
        )

        phrases = extractor.extract_phrases(psalm_chapter)
        return phrases

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
                'distinctiveness_score': 0.95,  # Full verses are highly distinctive
                'is_searchable': True
            })

        conn.close()
        return verses

    def _clear_existing_index(self, psalm_chapter: int):
        """Clear existing index entries for this Psalm (allows re-indexing)."""
        conn = sqlite3.connect(self.liturgy_db)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM psalms_liturgy_index
            WHERE psalm_chapter = ?
        """, (psalm_chapter,))

        conn.commit()
        conn.close()

    def _search_liturgy(
        self,
        phrase_hebrew: str,
        psalm_chapter: int,
        psalm_verse_start: Optional[int],
        psalm_verse_end: Optional[int],
        distinctiveness_score: float
    ) -> List[Dict]:
        """
        Search for a Psalms phrase in all liturgical texts.

        Uses consonantal normalization only (robust across vocalization traditions).
        Returns list of matches with metadata.
        """
        matches = self._search_consonantal(
            phrase_hebrew=phrase_hebrew,
            psalm_chapter=psalm_chapter,
            psalm_verse_start=psalm_verse_start,
            psalm_verse_end=psalm_verse_end,
            distinctiveness_score=distinctiveness_score
        )

        return matches

    def _search_consonantal(
        self,
        phrase_hebrew: str,
        psalm_chapter: int,
        psalm_verse_start: Optional[int],
        psalm_verse_end: Optional[int],
        distinctiveness_score: float
    ) -> List[Dict]:
        """Search using consonantal normalization."""

        # Normalize to consonants only
        normalized_phrase = normalize_for_search(phrase_hebrew, level='consonantal')

        # Further normalize (remove punctuation, maqqef, etc.)
        normalized_phrase = self._normalize_text(normalized_phrase)

        conn = sqlite3.connect(self.liturgy_db)
        cursor = conn.cursor()

        # Search all prayers
        cursor.execute("""
            SELECT
                prayer_id,
                hebrew_text,
                sefaria_ref,
                nusach,
                occasion,
                service,
                section,
                prayer_name
            FROM prayers
            WHERE hebrew_text IS NOT NULL AND hebrew_text != ''
        """)

        matches = []

        for prayer_id, hebrew_text, sefaria_ref, nusach, occasion, service, section, prayer_name in cursor.fetchall():
            # Normalize liturgy text to consonantal
            normalized_liturgy = normalize_for_search(hebrew_text, level='consonantal')
            normalized_liturgy = self._normalize_text(normalized_liturgy)

            # Search for phrase in normalized liturgy
            if normalized_phrase in normalized_liturgy:
                # Extract context
                context = self._extract_context(
                    full_text=hebrew_text,
                    phrase=phrase_hebrew
                )

                # Extract exact match from liturgy (preserving original diacritics)
                liturgy_phrase = self._extract_exact_match(
                    full_text=hebrew_text,
                    phrase=phrase_hebrew
                )

                # Determine match type
                match_type = self._determine_match_type(
                    phrase_hebrew=phrase_hebrew,
                    psalm_chapter=psalm_chapter,
                    verse_start=psalm_verse_start,
                    verse_end=psalm_verse_end
                )

                # Calculate confidence
                confidence = self._calculate_confidence(
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
                    'liturgy_phrase_hebrew': liturgy_phrase,
                    'liturgy_context': context,
                    'match_type': match_type,
                    'normalization_level': 2,  # consonantal = 2 (for database compatibility)
                    'confidence': confidence,
                    'distinctiveness_score': distinctiveness_score
                })

        conn.close()
        return matches

    def _normalize_text(self, text: str) -> str:
        """
        Additional normalization for robust matching.

        Removes:
        - Maqqef (Hebrew hyphen) -> converted to space
        - Hebrew punctuation (geresh, gershayim)
        - ASCII punctuation
        """
        if not text:
            return text

        # Replace maqqef with space
        text = text.replace('\u05BE', ' ')

        # Remove geresh and gershayim
        text = text.replace('\u05F3', '')
        text = text.replace('\u05F4', '')

        # Remove ASCII punctuation
        text = re.sub(r'[,.:;!?\-\(\)\[\]{}\"\'`]', ' ', text)

        # Normalize whitespace
        text = ' '.join(text.split())

        return text

    def _extract_context(
        self,
        full_text: str,
        phrase: str,
        context_words: int = 10
    ) -> str:
        """Extract surrounding context (±N words) around the match."""

        words = full_text.split()
        phrase_words = phrase.split()

        # Find the phrase using consonantal normalization
        normalized_full = normalize_for_search(full_text, level='consonantal')
        normalized_full = self._normalize_text(normalized_full)

        normalized_phrase = normalize_for_search(phrase, level='consonantal')
        normalized_phrase = self._normalize_text(normalized_phrase)

        # Find position in normalized text
        idx = normalized_full.find(normalized_phrase)
        if idx == -1:
            return ""

        # Count words before match to find position in original
        words_before = normalized_full[:idx].split()
        start_idx = max(0, len(words_before) - context_words)
        end_idx = min(len(words), len(words_before) + len(phrase_words) + context_words)

        context = ' '.join(words[start_idx:end_idx])

        # Truncate if too long (database field limit)
        if len(context) > 300:
            context = context[:297] + '...'

        return context

    def _extract_exact_match(
        self,
        full_text: str,
        phrase: str
    ) -> str:
        """Extract the exact matching text from liturgy (preserving original diacritics)."""

        words = full_text.split()
        phrase_words = phrase.split()

        normalized_full = normalize_for_search(full_text, level='consonantal')
        normalized_full = self._normalize_text(normalized_full)

        normalized_phrase = normalize_for_search(phrase, level='consonantal')
        normalized_phrase = self._normalize_text(normalized_phrase)

        idx = normalized_full.find(normalized_phrase)
        if idx == -1:
            return phrase  # Fallback to original phrase

        # Find word boundaries
        words_before = normalized_full[:idx].split()
        match_start = len(words_before)
        match_end = match_start + len(phrase_words)

        if match_end > len(words):
            return phrase

        return ' '.join(words[match_start:match_end])

    def _determine_match_type(
        self,
        phrase_hebrew: str,
        psalm_chapter: int,
        verse_start: Optional[int],
        verse_end: Optional[int]
    ) -> str:
        """Determine the type of match."""

        # Check if it's a full verse match
        if verse_start is not None and (verse_end is None or verse_start == verse_end):
            # Single verse - check if phrase is the full verse
            conn = sqlite3.connect(self.tanakh_db)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT hebrew FROM verses
                WHERE book_name = 'Psalms' AND chapter = ? AND verse = ?
            """, (psalm_chapter, verse_start))

            verse_text = cursor.fetchone()
            conn.close()

            if verse_text:
                # Compare at consonantal level (most reliable)
                verse_normalized = normalize_for_search(verse_text[0], level='consonantal')
                phrase_normalized = normalize_for_search(phrase_hebrew, level='consonantal')

                verse_normalized = self._normalize_text(verse_normalized)
                phrase_normalized = self._normalize_text(phrase_normalized)

                if verse_normalized == phrase_normalized:
                    return 'exact_verse'

        # Otherwise it's a phrase match
        return 'phrase_match'

    def _calculate_confidence(
        self,
        distinctiveness_score: float,
        match_type: str
    ) -> float:
        """
        Calculate confidence score for a match.

        Factors:
        - Distinctiveness score (rare phrases are more confident)
        - Match type (verse > phrase)
        """

        # Base confidence for consonantal matching
        base = 0.75

        # Boost for exact verse matches
        if match_type == 'exact_verse':
            type_boost = 0.10
        else:
            type_boost = 0.0

        # Combine with distinctiveness (weighted)
        # High distinctiveness adds up to 0.15 to confidence
        distinctiveness_boost = distinctiveness_score * 0.15

        confidence = min(1.0, base + type_boost + distinctiveness_boost)

        return round(confidence, 3)

    def _store_match(self, match: Dict):
        """Store a match in the psalms_liturgy_index table."""

        conn = sqlite3.connect(self.liturgy_db)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO psalms_liturgy_index (
                psalm_chapter,
                psalm_verse_start,
                psalm_verse_end,
                psalm_phrase_hebrew,
                psalm_phrase_normalized,
                phrase_length,
                prayer_id,
                liturgy_phrase_hebrew,
                liturgy_context,
                match_type,
                normalization_level,
                confidence,
                distinctiveness_score
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

    def index_all_psalms(self, start_psalm: int = 1, end_psalm: int = 150) -> Dict:
        """
        Index multiple Psalms (can run overnight for all 150).

        Args:
            start_psalm: First Psalm to index
            end_psalm: Last Psalm to index (inclusive)

        Returns:
            Summary statistics
        """
        total_matches = 0
        total_searchable = 0
        errors = []

        for psalm in range(start_psalm, end_psalm + 1):
            try:
                result = self.index_psalm(psalm)
                total_matches += result.get('total_matches', 0)
                total_searchable += result.get('searchable_phrases', 0)
            except Exception as e:
                error_msg = f"Psalm {psalm}: {str(e)}"
                errors.append(error_msg)
                if self.verbose:
                    print(f"✗ Error indexing {error_msg}\n")

        if self.verbose:
            print(f"\n{'='*70}")
            print(f"INDEXING COMPLETE: Psalms {start_psalm}-{end_psalm}")
            print(f"{'='*70}")
            print(f"Total searchable phrases: {total_searchable}")
            print(f"Total matches found: {total_matches}")
            if errors:
                print(f"Errors: {len(errors)}")
                for error in errors:
                    print(f"  - {error}")
            print()

        return {
            'start_psalm': start_psalm,
            'end_psalm': end_psalm,
            'total_searchable': total_searchable,
            'total_matches': total_matches,
            'errors': errors
        }

    def get_index_statistics(self) -> Dict:
        """Get comprehensive statistics about the index."""
        conn = sqlite3.connect(self.liturgy_db)
        cursor = conn.cursor()

        stats = {}

        # Total matches
        cursor.execute("SELECT COUNT(*) FROM psalms_liturgy_index")
        stats['total_matches'] = cursor.fetchone()[0]

        # Unique Psalms indexed
        cursor.execute("SELECT COUNT(DISTINCT psalm_chapter) FROM psalms_liturgy_index")
        stats['psalms_indexed'] = cursor.fetchone()[0]

        # Matches by type
        cursor.execute("""
            SELECT match_type, COUNT(*)
            FROM psalms_liturgy_index
            GROUP BY match_type
        """)
        stats['by_match_type'] = dict(cursor.fetchall())

        # All matches use consonantal (normalization_level = 2)
        stats['normalization'] = 'consonantal'

        # Average confidence
        cursor.execute("SELECT AVG(confidence) FROM psalms_liturgy_index")
        stats['avg_confidence'] = round(cursor.fetchone()[0] or 0, 3)

        # Top Psalms by matches
        cursor.execute("""
            SELECT psalm_chapter, COUNT(*) as count
            FROM psalms_liturgy_index
            GROUP BY psalm_chapter
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['top_psalms'] = cursor.fetchall()

        conn.close()
        return stats


# CLI script
def main():
    """Command-line interface for liturgy indexer."""
    import argparse
    import sys

    # Configure UTF-8 output for Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Index Psalms phrases in liturgical texts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Index a single Psalm
  python src/liturgy/liturgy_indexer.py --psalm 23

  # Index a range of Psalms
  python src/liturgy/liturgy_indexer.py --range 1-10

  # Index all Psalms (long-running)
  python src/liturgy/liturgy_indexer.py --all

  # Show index statistics
  python src/liturgy/liturgy_indexer.py --stats
        """
    )

    parser.add_argument(
        '--psalm',
        type=int,
        help='Index a specific Psalm (1-150)'
    )
    parser.add_argument(
        '--range',
        type=str,
        help='Index a range of Psalms (e.g., "1-10")'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Index all 150 Psalms'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show index statistics'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress output'
    )

    args = parser.parse_args()

    indexer = LiturgyIndexer(verbose=not args.quiet)

    if args.stats:
        print("\n" + "="*70)
        print("LITURGICAL INDEX STATISTICS")
        print("="*70 + "\n")

        stats = indexer.get_index_statistics()

        print(f"Total matches: {stats['total_matches']:,}")
        print(f"Psalms indexed: {stats['psalms_indexed']}/150")
        print(f"Average confidence: {stats['avg_confidence']:.3f}")

        print(f"\nNormalization: {stats['normalization']}")

        print(f"\nBy match type:")
        for match_type, count in sorted(stats['by_match_type'].items()):
            pct = count / stats['total_matches'] * 100
            print(f"  {match_type.replace('_', ' ').title()}: {count:,} ({pct:.1f}%)")

        print(f"\nTop 10 Psalms by matches:")
        for psalm, count in stats['top_psalms']:
            print(f"  Psalm {psalm}: {count:,} matches")

        print()

    elif args.psalm:
        indexer.index_psalm(args.psalm)

    elif args.range:
        try:
            start, end = map(int, args.range.split('-'))
            if start < 1 or end > 150 or start > end:
                print("Error: Range must be between 1-150 and start <= end")
                return
            indexer.index_all_psalms(start, end)
        except ValueError:
            print("Error: Range must be in format 'start-end' (e.g., '1-10')")

    elif args.all:
        confirm = input("Index all 150 Psalms? This may take a while. (y/N): ")
        if confirm.lower() == 'y':
            indexer.index_all_psalms()
        else:
            print("Cancelled.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
