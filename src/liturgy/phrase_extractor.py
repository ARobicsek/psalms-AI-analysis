"""
Phrase Extractor for Liturgical Librarian - Phase 3

Extracts meaningful phrases from Psalms with TF-IDF distinctiveness scoring.
Identifies searchable phrases (2-10 words) that are distinctive enough to find in liturgy.

Architecture:
- Uses tanakh.db as canonical source for Psalms
- Calculates corpus statistics from full Tanakh (23,206 verses)
- Scores phrases by distinctiveness (rare = high, common = low)
- Caches results in phrase_cache table for performance
- Supports cross-verse phrases (spanning up to 3 verses)

Created: 2025-10-26
Phase: Liturgical Librarian Phase 3
"""

import sqlite3
import re
import math
from typing import List, Tuple, Dict, Optional
from collections import defaultdict
from pathlib import Path

# Import Hebrew text processing utilities
import sys
sys.path.append(str(Path(__file__).parent.parent))
from concordance.hebrew_text_processor import (
    normalize_for_search,
    split_words,
    clean_hebrew_text,
    strip_vowels
)


class PhraseExtractor:
    """Extract and score phrases from Psalms for liturgical matching."""

    def __init__(
        self,
        tanakh_db: str = "database/tanakh.db",
        liturgy_db: str = "data/liturgy.db",
        verbose: bool = True
    ):
        """
        Initialize phrase extractor with database connections.

        Args:
            tanakh_db: Path to Tanakh database (canonical Psalms source)
            liturgy_db: Path to liturgy database (for caching)
            verbose: Print progress messages
        """
        self.tanakh_db = tanakh_db
        self.liturgy_db = liturgy_db
        self.verbose = verbose

        # Calculate corpus statistics once (expensive operation)
        if self.verbose:
            print("Calculating corpus statistics...")
        self.corpus_stats = self._calculate_corpus_stats()

        # Common Hebrew particles to filter out
        self.particles = {
            'ו', 'ה', 'ל', 'ב', 'מ', 'כ', 'את', 'על', 'אל', 'מן',
            'אשר', 'כי', 'אם', 'לא', 'גם', 'עם', 'הוא', 'היא'
        }

    def _normalize_text(self, text: str) -> str:
        """
        Normalize Hebrew text for phrase matching.

        Removes:
        - All diacritics (vowels and cantillation)
        - Maqqef (Hebrew hyphen U+05BE) -> converted to space
        - Other Hebrew punctuation (geresh U+05F3, gershayim U+05F4)
        - ASCII punctuation (commas, periods, colons, etc.)

        Args:
            text: Hebrew text with diacritics

        Returns:
            Consonantal text with normalized punctuation
        """
        if not text:
            return text

        # Replace maqqef with space (so "כל־הארץ" becomes "כל הארץ")
        text = text.replace('\u05BE', ' ')  # maqqef

        # Remove geresh and gershayim (used for abbreviations and numbers)
        text = text.replace('\u05F3', '')  # geresh
        text = text.replace('\u05F4', '')  # gershayim

        # Remove ASCII punctuation (from siddur texts: commas, periods, colons, etc.)
        text = re.sub(r'[,.:;!?\-\(\)\[\]{}\"\'`]', ' ', text)

        # Strip all diacritics (vowels and cantillation) - consonantal only
        text = strip_vowels(text)

        # Normalize whitespace (collapse multiple spaces)
        text = ' '.join(text.split())

        return text

    def extract_phrases(
        self,
        psalm_chapter: int,
        min_length: int = 2,
        max_length: int = 10,
        use_cache: bool = True
    ) -> List[Dict]:
        """
        Extract all meaningful phrases from a Psalm.

        Args:
            psalm_chapter: Psalm number (1-150)
            min_length: Minimum phrase length in words
            max_length: Maximum phrase length in words
            use_cache: Use cached distinctiveness scores

        Returns:
            List of phrase dictionaries with:
            - phrase: Hebrew text
            - phrase_normalized: Consonantal normalization
            - verse_start: Starting verse number
            - verse_end: Ending verse number (for multi-verse phrases)
            - word_count: Number of words
            - corpus_frequency: Times phrase appears in Tanakh
            - distinctiveness_score: TF-IDF score (0.0-1.0)
            - is_searchable: Boolean (meets threshold)
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Extracting phrases from Psalm {psalm_chapter}")
            print(f"{'='*60}\n")

        # Get Psalm verses
        verses = self._get_psalm_verses(psalm_chapter)

        if not verses:
            print(f"⚠ Warning: No verses found for Psalm {psalm_chapter}")
            return []

        if self.verbose:
            print(f"Found {len(verses)} verses")

        phrases = []

        # Extract within-verse n-grams
        for verse_num, verse_text in verses:
            verse_phrases = self._extract_verse_ngrams(
                verse_num=verse_num,
                verse_text=verse_text,
                min_length=min_length,
                max_length=max_length,
                use_cache=use_cache
            )
            phrases.extend(verse_phrases)

        if self.verbose:
            print(f"Extracted {len(phrases)} within-verse phrases")

        # Extract cross-verse phrases (spans 2-3 consecutive verses)
        cross_verse = self._extract_cross_verse_phrases(
            verses=verses,
            min_length=min_length,
            max_length=max_length,
            use_cache=use_cache
        )
        phrases.extend(cross_verse)

        if self.verbose:
            print(f"Extracted {len(cross_verse)} cross-verse phrases")
            searchable = sum(1 for p in phrases if p['is_searchable'])
            print(f"\nTotal phrases: {len(phrases)}")
            print(f"Searchable (meets threshold): {searchable} ({100*searchable/len(phrases):.1f}%)")

        return phrases

    def _get_psalm_verses(self, chapter: int) -> List[Tuple[int, str]]:
        """
        Fetch all verses from a Psalm.

        Args:
            chapter: Psalm number

        Returns:
            List of (verse_number, hebrew_text) tuples
        """
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

    def _extract_verse_ngrams(
        self,
        verse_num: int,
        verse_text: str,
        min_length: int,
        max_length: int,
        use_cache: bool
    ) -> List[Dict]:
        """
        Extract all n-grams from a single verse.

        Args:
            verse_num: Verse number
            verse_text: Hebrew text
            min_length: Minimum n-gram length
            max_length: Maximum n-gram length
            use_cache: Use cached scores

        Returns:
            List of phrase dictionaries
        """
        # Tokenize into words
        words = split_words(clean_hebrew_text(verse_text))

        if not words:
            return []

        phrases = []

        # Extract all n-grams
        for n in range(min_length, min(max_length + 1, len(words) + 1)):
            for i in range(len(words) - n + 1):
                phrase = ' '.join(words[i:i+n])

                # Get or calculate distinctiveness
                phrase_data = self._score_phrase(
                    phrase=phrase,
                    word_count=n,
                    use_cache=use_cache
                )

                phrases.append({
                    'phrase': phrase,
                    'phrase_normalized': phrase_data['phrase_normalized'],
                    'verse_start': verse_num,
                    'verse_end': verse_num,
                    'word_count': n,
                    'corpus_frequency': phrase_data['corpus_frequency'],
                    'distinctiveness_score': phrase_data['distinctiveness_score'],
                    'is_searchable': phrase_data['is_searchable']
                })

        return phrases

    def _extract_cross_verse_phrases(
        self,
        verses: List[Tuple[int, str]],
        min_length: int,
        max_length: int,
        use_cache: bool
    ) -> List[Dict]:
        """
        Extract phrases that span verse boundaries.

        Args:
            verses: List of (verse_num, verse_text) tuples
            min_length: Minimum phrase length
            max_length: Maximum phrase length
            use_cache: Use cached scores

        Returns:
            List of cross-verse phrase dictionaries
        """
        cross_phrases = []

        # Process consecutive verse pairs and triplets
        for span in [2, 3]:  # 2-verse and 3-verse spans
            for i in range(len(verses) - span + 1):
                verse_group = verses[i:i+span]

                # Get words from each verse
                verse_words = []
                for verse_num, verse_text in verse_group:
                    words = split_words(clean_hebrew_text(verse_text))
                    verse_words.append((verse_num, words))

                # Extract phrases crossing verse boundaries
                if span == 2:
                    # Take last N words from verse 1 + first M words from verse 2
                    verse1_num, words1 = verse_words[0]
                    verse2_num, words2 = verse_words[1]

                    for n1 in range(1, min(max_length, len(words1) + 1)):
                        for n2 in range(1, min(max_length - n1 + 1, len(words2) + 1)):
                            total_len = n1 + n2
                            if total_len < min_length or total_len > max_length:
                                continue

                            phrase = ' '.join(words1[-n1:] + words2[:n2])

                            phrase_data = self._score_phrase(
                                phrase=phrase,
                                word_count=total_len,
                                use_cache=use_cache
                            )

                            cross_phrases.append({
                                'phrase': phrase,
                                'phrase_normalized': phrase_data['phrase_normalized'],
                                'verse_start': verse1_num,
                                'verse_end': verse2_num,
                                'word_count': total_len,
                                'corpus_frequency': phrase_data['corpus_frequency'],
                                'distinctiveness_score': phrase_data['distinctiveness_score'],
                                'is_searchable': phrase_data['is_searchable']
                            })

                elif span == 3:
                    # For 3-verse spans, only take transitions (last of v1 + middle + first of v3)
                    verse1_num, words1 = verse_words[0]
                    verse2_num, words2 = verse_words[1]
                    verse3_num, words3 = verse_words[2]

                    # Sample: last 2 of v1 + all of v2 + first 2 of v3 (if within length limits)
                    for n1 in range(1, min(3, len(words1) + 1)):
                        for n3 in range(1, min(3, len(words3) + 1)):
                            # All of verse 2 or part of it
                            for n2 in range(1, len(words2) + 1):
                                total_len = n1 + n2 + n3
                                if total_len < min_length or total_len > max_length:
                                    continue

                                phrase = ' '.join(words1[-n1:] + words2[:n2] + words3[:n3])

                                phrase_data = self._score_phrase(
                                    phrase=phrase,
                                    word_count=total_len,
                                    use_cache=use_cache
                                )

                                cross_phrases.append({
                                    'phrase': phrase,
                                    'phrase_normalized': phrase_data['phrase_normalized'],
                                    'verse_start': verse1_num,
                                    'verse_end': verse3_num,
                                    'word_count': total_len,
                                    'corpus_frequency': phrase_data['corpus_frequency'],
                                    'distinctiveness_score': phrase_data['distinctiveness_score'],
                                    'is_searchable': phrase_data['is_searchable']
                                })

        return cross_phrases

    def _score_phrase(
        self,
        phrase: str,
        word_count: int,
        use_cache: bool
    ) -> Dict:
        """
        Calculate distinctiveness score for a phrase.

        Args:
            phrase: Hebrew phrase
            word_count: Number of words
            use_cache: Check cache first

        Returns:
            Dictionary with phrase_normalized, corpus_frequency,
            distinctiveness_score, is_searchable
        """
        # Normalize to consonantal for matching (with punctuation handling)
        phrase_normalized = self._normalize_text(phrase)

        # Check cache first
        if use_cache:
            cached = self._get_cached_score(phrase_normalized)
            if cached:
                return cached

        # Calculate corpus frequency
        corpus_frequency = self._count_phrase_in_corpus(phrase_normalized)

        # Calculate distinctiveness score
        distinctiveness_score = self._calculate_distinctiveness(
            frequency=corpus_frequency,
            word_count=word_count
        )

        # Determine if searchable
        is_searchable = self._is_searchable(
            phrase_normalized=phrase_normalized,
            word_count=word_count,
            score=distinctiveness_score
        )

        result = {
            'phrase_normalized': phrase_normalized,
            'corpus_frequency': corpus_frequency,
            'distinctiveness_score': distinctiveness_score,
            'is_searchable': is_searchable
        }

        # Cache result
        if use_cache:
            self._cache_score(phrase_normalized, word_count, result)

        return result

    def _calculate_corpus_stats(self) -> Dict:
        """
        Calculate TF-IDF corpus statistics from Tanakh.

        Returns:
            Dictionary with total_verses count
        """
        conn = sqlite3.connect(self.tanakh_db)
        cursor = conn.cursor()

        # Total number of verses in Tanakh
        cursor.execute("SELECT COUNT(*) FROM verses")
        total_verses = cursor.fetchone()[0]

        conn.close()

        if self.verbose:
            print(f"Corpus size: {total_verses:,} verses")

        return {
            'total_verses': total_verses
        }

    def _count_phrase_in_corpus(self, phrase_normalized: str) -> int:
        """
        Count how many verses in Tanakh contain this phrase.

        Uses concordance index for efficient searching:
        1. Search concordance for first word to find candidate verses
        2. Only check those verses for full phrase match

        Args:
            phrase_normalized: Consonantal normalized phrase

        Returns:
            Number of verses containing the phrase
        """
        # Tokenize the phrase
        words = phrase_normalized.split()

        if not words:
            return 0

        conn = sqlite3.connect(self.tanakh_db)
        cursor = conn.cursor()

        if len(words) == 1:
            # Single word: just count in concordance
            cursor.execute("""
                SELECT COUNT(DISTINCT book_name || ':' || chapter || ':' || verse)
                FROM concordance
                WHERE word_consonantal = ?
            """, (words[0],))

            count = cursor.fetchone()[0]

        else:
            # Multi-word phrase: find candidate verses via first word,
            # then check full phrase
            first_word = words[0]

            # Find all verses containing the first word
            cursor.execute("""
                SELECT DISTINCT book_name, chapter, verse
                FROM concordance
                WHERE word_consonantal = ?
            """, (first_word,))

            candidates = cursor.fetchall()

            # For each candidate verse, check if full phrase matches
            count = 0
            for book_name, chapter, verse in candidates:
                cursor.execute("""
                    SELECT hebrew
                    FROM verses
                    WHERE book_name = ? AND chapter = ? AND verse = ?
                """, (book_name, chapter, verse))

                row = cursor.fetchone()
                if row:
                    verse_text = row[0]
                    verse_normalized = self._normalize_text(verse_text)
                    if phrase_normalized in verse_normalized:
                        count += 1

        conn.close()
        return count

    def _calculate_distinctiveness(self, frequency: int, word_count: int) -> float:
        """
        Calculate distinctiveness score using corpus frequency.

        Uses a graduated scale:
        - freq <= 5: score 0.90-1.00 (very distinctive)
        - freq 6-20: score 0.70-0.90 (distinctive)
        - freq 21-50: score 0.40-0.70 (moderately distinctive)
        - freq > 50: score 0.00-0.40 (common)

        Args:
            frequency: Number of verses containing phrase
            word_count: Length of phrase in words

        Returns:
            Distinctiveness score (0.0-1.0)
        """
        if frequency == 0:
            # Unique to this context (extremely distinctive)
            return 1.0

        # Graduated scoring based on frequency bands
        if frequency <= 5:
            score = 0.9 + (0.1 * (5 - frequency) / 5)
        elif frequency <= 20:
            score = 0.7 + (0.2 * (20 - frequency) / 15)
        elif frequency <= 50:
            score = 0.4 + (0.3 * (50 - frequency) / 30)
        else:
            # Common phrases score lower
            score = max(0.0, 0.4 * (100 - frequency) / 50)

        return min(1.0, score)

    def _is_searchable(
        self,
        phrase_normalized: str,
        word_count: int,
        score: float
    ) -> bool:
        """
        Determine if a phrase is worth searching for in liturgy.

        Criteria:
        - 2 words: score > 0.75 (very distinctive)
        - 3 words: score > 0.5 (distinctive)
        - 4+ words: score > 0.3 (moderately distinctive)
        - Filter out all-particle phrases

        Args:
            phrase_normalized: Normalized phrase
            word_count: Number of words
            score: Distinctiveness score

        Returns:
            True if phrase should be searched in liturgy
        """
        # Check for all particles
        if self._is_all_particles(phrase_normalized):
            return False

        # Word count thresholds (from implementation plan)
        if word_count == 2:
            return score > 0.75
        elif word_count == 3:
            return score > 0.5
        elif word_count >= 4:
            return score > 0.3

        return False

    def _is_all_particles(self, phrase_normalized: str) -> bool:
        """
        Check if phrase consists only of common particles.

        Args:
            phrase_normalized: Consonantal normalized phrase

        Returns:
            True if all words are particles
        """
        words = phrase_normalized.split()
        return all(w in self.particles for w in words)

    def _get_cached_score(self, phrase_normalized: str) -> Optional[Dict]:
        """
        Retrieve cached phrase score from database.

        Args:
            phrase_normalized: Consonantal normalized phrase

        Returns:
            Cached result dictionary or None if not found
        """
        conn = sqlite3.connect(self.liturgy_db)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT word_count, corpus_frequency, distinctiveness_score, is_searchable
            FROM phrase_cache
            WHERE phrase_normalized = ?
        """, (phrase_normalized,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'phrase_normalized': phrase_normalized,
                'word_count': row[0],
                'corpus_frequency': row[1],
                'distinctiveness_score': row[2],
                'is_searchable': bool(row[3])
            }

        return None

    def _cache_score(
        self,
        phrase_normalized: str,
        word_count: int,
        result: Dict
    ):
        """
        Store phrase score in database cache.

        Args:
            phrase_normalized: Consonantal normalized phrase
            word_count: Number of words
            result: Score result dictionary
        """
        conn = sqlite3.connect(self.liturgy_db)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO phrase_cache
                (phrase_normalized, word_count, corpus_frequency, distinctiveness_score, is_searchable)
                VALUES (?, ?, ?, ?, ?)
            """, (
                phrase_normalized,
                word_count,
                result['corpus_frequency'],
                result['distinctiveness_score'],
                1 if result['is_searchable'] else 0
            ))

            conn.commit()
        except sqlite3.Error as e:
            print(f"⚠ Cache write error: {e}")
        finally:
            conn.close()

    def extract_all_psalms(
        self,
        output_file: Optional[str] = None,
        start_psalm: int = 1,
        end_psalm: int = 150
    ) -> Dict[int, List[Dict]]:
        """
        Extract phrases from multiple Psalms.

        Args:
            output_file: Optional JSON file to save results
            start_psalm: First Psalm to process
            end_psalm: Last Psalm to process

        Returns:
            Dictionary mapping psalm_number -> list of phrases
        """
        results = {}

        for psalm_num in range(start_psalm, end_psalm + 1):
            phrases = self.extract_phrases(psalm_num)
            results[psalm_num] = phrases

            if self.verbose:
                searchable = sum(1 for p in phrases if p['is_searchable'])
                print(f"✓ Psalm {psalm_num}: {searchable} searchable phrases\n")

        # Save to file if requested
        if output_file:
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n✓ Results saved to {output_file}")

        return results


def main():
    """CLI interface for phrase extraction."""
    import argparse
    import sys

    # Ensure UTF-8 for Hebrew output on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Extract and score phrases from Psalms for liturgical matching'
    )
    parser.add_argument(
        'psalm',
        type=int,
        nargs='?',
        help='Psalm number to process (1-150), or omit for all Psalms'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all 150 Psalms'
    )
    parser.add_argument(
        '--range',
        nargs=2,
        type=int,
        metavar=('START', 'END'),
        help='Process range of Psalms (e.g., --range 1 10)'
    )
    parser.add_argument(
        '--output',
        '-o',
        help='Save results to JSON file'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable phrase score caching'
    )
    parser.add_argument(
        '--quiet',
        '-q',
        action='store_true',
        help='Suppress verbose output'
    )

    args = parser.parse_args()

    # Initialize extractor
    extractor = PhraseExtractor(verbose=not args.quiet)

    # Process Psalms
    if args.all:
        results = extractor.extract_all_psalms(output_file=args.output)
        total_searchable = sum(
            sum(1 for p in phrases if p['is_searchable'])
            for phrases in results.values()
        )
        print(f"\n{'='*60}")
        print(f"COMPLETE: {total_searchable:,} searchable phrases across 150 Psalms")
        print(f"{'='*60}")

    elif args.range:
        start, end = args.range
        results = extractor.extract_all_psalms(
            output_file=args.output,
            start_psalm=start,
            end_psalm=end
        )
        total_searchable = sum(
            sum(1 for p in phrases if p['is_searchable'])
            for phrases in results.values()
        )
        print(f"\n{'='*60}")
        print(f"COMPLETE: {total_searchable:,} searchable phrases from Psalms {start}-{end}")
        print(f"{'='*60}")

    elif args.psalm:
        phrases = extractor.extract_phrases(
            psalm_chapter=args.psalm,
            use_cache=not args.no_cache
        )

        # Display results
        searchable = [p for p in phrases if p['is_searchable']]

        print(f"\n{'='*60}")
        print(f"SEARCHABLE PHRASES (top 20):")
        print(f"{'='*60}\n")

        for i, phrase_data in enumerate(searchable[:20], 1):
            print(f"{i}. {phrase_data['phrase']}")
            print(f"   Verse: {phrase_data['verse_start']}", end="")
            if phrase_data['verse_end'] != phrase_data['verse_start']:
                print(f"-{phrase_data['verse_end']}", end="")
            print(f" | Words: {phrase_data['word_count']}", end="")
            print(f" | Freq: {phrase_data['corpus_frequency']}", end="")
            print(f" | Score: {phrase_data['distinctiveness_score']:.3f}\n")

        print(f"Total: {len(searchable)} searchable phrases out of {len(phrases)}")

        # Save if requested
        if args.output:
            import json
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(phrases, f, ensure_ascii=False, indent=2)
            print(f"\n✓ Results saved to {args.output}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
