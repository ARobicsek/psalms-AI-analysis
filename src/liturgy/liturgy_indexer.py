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

        # Apply additional quality filters
        before_filtering = len(searchable)

        # Filter 1: Remove single-word phrases (Issue 1)
        searchable = [p for p in searchable if self._count_meaningful_hebrew_words(p['phrase']) >= 2]

        # Filter 2: Remove cross-verse phrases with verse-end marker (Issue 2)
        searchable = [p for p in searchable if '\u05C3' not in p['phrase']]  # sof pasuq

        if self.verbose:
            print(f"Cached phrases: {len(phrases)}")
            print(f"Searchable phrases (before filters): {before_filtering} ({before_filtering/len(phrases)*100:.1f}%)")
            filtered_count = before_filtering - len(searchable)
            if filtered_count > 0:
                print(f"Filtered out {filtered_count} phrases (single-word or cross-verse)")
            print(f"Final searchable phrases: {len(searchable)}")
            print(f"Filtering out {len(phrases) - len(searchable)} total phrases\n")

        # Also index full verses (exact quotations)
        full_verses = self._get_full_verses(psalm_chapter)
        searchable.extend(full_verses)

        if self.verbose:
            print(f"Added {len(full_verses)} full verses for exact matching")
            print(f"Total searchable items: {len(searchable)}\n")

        # Clear existing index for this Psalm (allows re-indexing)
        self._clear_existing_index(psalm_chapter)

        # Search each phrase in liturgy
        all_matches = []

        for i, phrase_data in enumerate(searchable, 1):
            phrase_text = phrase_data['phrase'][:60] + ('...' if len(phrase_data['phrase']) > 60 else '')

            if self.verbose:
                print(f"[{i}/{len(searchable)}] {phrase_text}")

            matches = self._search_consonantal(
                phrase_hebrew=phrase_data['phrase'],
                psalm_chapter=psalm_chapter,
                psalm_verse_start=phrase_data.get('verse_start'),
                psalm_verse_end=phrase_data.get('verse_end'),
                distinctiveness_score=phrase_data.get('distinctiveness_score', 0.0)
            )

            if matches:
                if self.verbose:
                    print(f"  ✓ Found {len(matches)} match(es)")
                all_matches.extend(matches)

        # Deduplicate overlapping matches BEFORE storing
        if self.verbose and all_matches:
            print(f"\n{'='*70}")
            print(f"Deduplicating matches...")
            print(f"  Before: {len(all_matches)} matches")

        deduplicated_matches = self._deduplicate_matches(all_matches)

        if self.verbose and all_matches:
            print(f"  After: {len(deduplicated_matches)} unique contexts")
            reduction_pct = (1 - len(deduplicated_matches)/len(all_matches)) * 100 if all_matches else 0
            print(f"  Removed {len(all_matches) - len(deduplicated_matches)} overlapping matches ({reduction_pct:.1f}% reduction)")
            print(f"{'='*70}\n")

        # Now store deduplicated matches and track statistics
        total_matches = 0
        match_details = {}

        for match in deduplicated_matches:
            self._store_match(match)
            total_matches += 1

            # Track match types
            match_type = match['match_type']
            match_details[match_type] = match_details.get(match_type, 0) + 1

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
        This is the main search function that now orchestrates the corrected matching logic.
        """
        conn = sqlite3.connect(self.liturgy_db)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT prayer_id, hebrew_text
            FROM prayers
            WHERE hebrew_text IS NOT NULL AND hebrew_text != ''
        """)
        
        all_prayers = cursor.fetchall()
        conn.close()

        matches = []

        for prayer_id, hebrew_text in all_prayers:
            found_occurrences = self._find_all_occurrences(hebrew_text, phrase_hebrew)

            if not found_occurrences:
                continue

            prayer_words = hebrew_text.split()
            phrase_word_count = len(phrase_hebrew.split())
            word_start_chars = [m.start() for m in re.finditer(r'\S+', hebrew_text)]

            for liturgy_phrase, start_word_index in found_occurrences:
                match_type = self._determine_match_type(
                    phrase_hebrew=phrase_hebrew,
                    psalm_chapter=psalm_chapter,
                    verse_start=psalm_verse_start,
                    verse_end=psalm_verse_end
                )

                if match_type == 'phrase_match':
                    if start_word_index < len(word_start_chars):
                        char_start_index = word_start_chars[start_word_index]
                        context_start = max(0, char_start_index - 500)
                        context_end = min(len(hebrew_text), char_start_index + len(liturgy_phrase) + 500)
                        context = hebrew_text[context_start:context_end]
                    else:
                        # Fallback for safety if word index is out of bounds
                        context = self._extract_context_from_words(
                            prayer_words,
                            start_word_index,
                            phrase_word_count
                        )
                else:  # exact_verse
                    context = self._extract_context_from_words(
                        prayer_words,
                        start_word_index,
                        phrase_word_count
                    )

                confidence = self._calculate_confidence(
                    distinctiveness_score=distinctiveness_score,
                    match_type=match_type
                )

                # Use _full_normalize to handle maqqef correctly (replace BEFORE stripping vowels)
                normalized_phrase = self._full_normalize(phrase_hebrew)

                matches.append({
                    'psalm_chapter': psalm_chapter,
                    'psalm_verse_start': psalm_verse_start,
                    'psalm_verse_end': psalm_verse_end,
                    'psalm_phrase_hebrew': phrase_hebrew,
                    'psalm_phrase_normalized': normalized_phrase,
                    'phrase_length': phrase_word_count,
                    'prayer_id': prayer_id,
                    'liturgy_phrase_hebrew': liturgy_phrase,
                    'liturgy_context': context,
                    'match_type': match_type,
                    'normalization_level': 2,
                    'confidence': confidence,
                    'distinctiveness_score': distinctiveness_score
                })
        
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

        # Full normalization (maqqef->space, then consonantal, then punctuation)
        normalized_phrase = self._full_normalize(phrase_hebrew)

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
            # Full normalization of liturgy text
            normalized_liturgy = self._full_normalize(hebrew_text)

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

    def _full_normalize(self, text: str) -> str:
        """
        Complete normalization pipeline for matching.

        CRITICAL: Must replace maqqef BEFORE stripping vowels, otherwise
        maqqef-connected words become joined (עלמי instead of על מי).

        Order:
        1. Normalize divine name abbreviations (ה' → יהוה)
        2. Replace maqqef with space (BEFORE vowel stripping)
        3. Strip vowels/cantillation (consonantal)
        4. Remove other punctuation
        5. Normalize whitespace

        Args:
            text: Hebrew text with diacritics

        Returns:
            Normalized consonantal text
        """
        if not text:
            return text

        # STEP 1: Normalize divine name abbreviations (BEFORE vowel stripping!)
        # Replace ה' (hey with geresh) with the full tetragrammaton
        # This ensures liturgical texts match canonical texts
        text = text.replace("ה'", "יהוה")  # divine name abbreviation -> full form

        # STEP 2: Replace maqqef with space (BEFORE stripping vowels!)
        text = text.replace('\u05BE', ' ')  # maqqef -> space

        # STEP 3: Strip vowels and cantillation (consonantal normalization)
        text = normalize_for_search(text, level='consonantal')

        # STEP 4: Remove remaining punctuation and markers
        text = text.replace('\u05C0', ' ')  # paseq (|) -> space
        text = text.replace('\u05F3', '')  # geresh
        text = text.replace('\u05F4', '')  # gershayim
        text = re.sub(r'[,.:;!?\-\(\)\[\]{}\"\'`]', ' ', text)
        # Remove paragraph markers (פ and ס) when standalone
        text = re.sub(r'\s+[פס]\s+', ' ', text)  # Surrounded by whitespace
        text = re.sub(r'\s+[פס]$', '', text)  # At end of text

        # STEP 5: Normalize whitespace
        text = ' '.join(text.split())

        return text

    def _normalize_text(self, text: str) -> str:
        """
        DEPRECATED: Use _full_normalize() instead.

        This method is kept for backward compatibility but should not be used
        for new code. It doesn't handle maqqef correctly because it expects
        text to already be consonantal, but maqqef gets stripped by
        normalize_for_search before this method can replace it with a space.
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

    def _count_meaningful_hebrew_words(self, phrase: str) -> int:
        """
        Count meaningful Hebrew words in a phrase.

        Excludes punctuation marks, cantillation, and separators like paseq (׀).

        Args:
            phrase: Hebrew text with diacritics

        Returns:
            Number of meaningful Hebrew words (not punctuation)
        """
        if not phrase:
            return 0

        # Split by whitespace
        words = phrase.split()

        # Count only words that contain Hebrew letters (not just punctuation/marks)
        hebrew_letter_pattern = re.compile(r'[\u05D0-\u05EA]')  # Hebrew letters (aleph-tav)
        meaningful_count = 0

        for word in words:
            # Check if word contains at least one Hebrew letter
            if hebrew_letter_pattern.search(word):
                meaningful_count += 1

        return meaningful_count

    def _extract_context(
        self,
        full_text: str,
        phrase: str,
        context_words: int = 10
    ) -> str:
        """Extract surrounding context (±N words) around the match."""

        words = full_text.split()
        phrase_words = phrase.split()

        # Full normalization
        normalized_full = self._full_normalize(full_text)
        normalized_phrase = self._full_normalize(phrase)

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
        """
        Extract the exact matching text from liturgy (preserving original diacritics).

        Uses sliding window approach to find the correct word sequence that matches
        the phrase at consonantal level, ensuring we return the actual matched phrase
        from the liturgy text (not a different phrase from the same context).
        """

        words = full_text.split()
        phrase_words = phrase.split()
        phrase_length = len(phrase_words)

        # Full normalization of target phrase
        normalized_phrase = self._full_normalize(phrase)

        # Use sliding window to find the matching sequence in original text
        for i in range(len(words) - phrase_length + 1):
            # Get window of words from original text
            window = words[i:i + phrase_length]
            window_text = ' '.join(window)

            # Full normalization of window
            normalized_window = self._full_normalize(window_text)

            # Check if this window matches the phrase
            if normalized_window == normalized_phrase:
                return window_text

        # Fallback: return the original phrase if no match found
        return phrase

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
                verse_normalized = self._full_normalize(verse_text[0])
                phrase_normalized = self._full_normalize(phrase_hebrew)

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

        Fixed: Exact verse matches now return 1.0 (perfect confidence)
        """

        # Exact verse matches are perfect confidence
        if match_type == 'exact_verse':
            return 1.0

        # For phrase matches, use graduated scoring
        # Base confidence for consonantal matching
        base = 0.75

        # Combine with distinctiveness (weighted)
        # High distinctiveness adds up to 0.25 to confidence
        distinctiveness_boost = distinctiveness_score * 0.25

        confidence = min(1.0, base + distinctiveness_boost)

        return round(confidence, 3)

    def _deduplicate_matches(self, matches: List[Dict]) -> List[Dict]:
        """
        Consolidate overlapping n-grams to unique contexts.

        When multiple phrases match the same location in a prayer
        (e.g., "לדוד", "לדוד יהוה", "לדוד יהוה רעי"),
        keep only the longest/most distinctive match.

        Strategy:
        1. Group matches by (prayer_id, approximate_location)
        2. For each group, select the best match based on:
           - Match type priority (exact_verse > phrase_match)
           - Phrase length (longer is better)
           - Confidence score (higher is better)
        3. Remove phrase matches when full verse match exists for same verse-prayer pair
        """
        if not matches:
            return []

        # Group matches by prayer and approximate location
        from collections import defaultdict

        # First pass: find position of each match in its prayer
        conn = sqlite3.connect(self.liturgy_db)
        cursor = conn.cursor()

        match_positions = []
        for match in matches:
            # Get the full prayer text
            cursor.execute("""
                SELECT hebrew_text FROM prayers WHERE prayer_id = ?
            """, (match['prayer_id'],))

            result = cursor.fetchone()
            if not result:
                continue

            prayer_text = result[0]

            # Find position using full normalization
            normalized_prayer = self._full_normalize(prayer_text)
            normalized_phrase = match['psalm_phrase_normalized']

            # Find all occurrences (there might be multiple)
            pos = normalized_prayer.find(normalized_phrase)

            if pos != -1:
                match_positions.append({
                    'match': match,
                    'position': pos,
                    'length': len(normalized_phrase)
                })

        conn.close()

        # Group matches by prayer_id
        by_prayer = defaultdict(list)
        for item in match_positions:
            prayer_id = item['match']['prayer_id']
            by_prayer[prayer_id].append(item)

        # For each prayer, merge overlapping intervals
        deduplicated = []

        for prayer_id, items in by_prayer.items():
            # Sort by position
            items.sort(key=lambda x: x['position'])

            # Merge overlapping intervals using interval merging
            merged_groups = []
            current_group = [items[0]]

            for item in items[1:]:
                # Check if this item overlaps with any item in current group
                overlaps = False
                for existing in current_group:
                    existing_end = existing['position'] + existing['length']
                    item_end = item['position'] + item['length']

                    # Two intervals overlap if one starts before the other ends
                    if item['position'] <= existing_end and existing['position'] <= item_end:
                        overlaps = True
                        break

                if overlaps:
                    # Add to current group
                    current_group.append(item)
                else:
                    # Start new group
                    merged_groups.append(current_group)
                    current_group = [item]

            # Don't forget the last group
            merged_groups.append(current_group)

            # For each merged group, select the best match
            for group in merged_groups:
                # Sort by priority:
                # 1. Match type (exact_verse > phrase_match)
                # 2. Phrase length (longer is better)
                # 3. Confidence (higher is better)
                best = max(group, key=lambda x: (
                    1 if x['match']['match_type'] == 'exact_verse' else 0,
                    x['match']['phrase_length'],
                    x['match']['confidence']
                ))
                deduplicated.append(best['match'])

        # SECOND PASS: Remove phrase matches when verse match exists for same verse-prayer pair
        # Group by (psalm_chapter, verse_start, verse_end, prayer_id)
        verse_groups = defaultdict(list)
        for match in deduplicated:
            key = (
                match['psalm_chapter'],
                match['psalm_verse_start'],
                match['psalm_verse_end'],
                match['prayer_id']
            )
            verse_groups[key].append(match)

        # Filter out phrase matches when exact_verse exists
        final_deduplicated = []
        for group_matches in verse_groups.values():
            # Check if any match is exact_verse
            has_exact_verse = any(m['match_type'] == 'exact_verse' for m in group_matches)

            if has_exact_verse:
                # Keep only exact_verse matches
                final_deduplicated.extend([m for m in group_matches if m['match_type'] == 'exact_verse'])
            else:
                # Keep all matches (no verse match exists)
                final_deduplicated.extend(group_matches)

        # THIRD PASS: Detect entire chapter appearances
        # Group by (psalm_chapter, prayer_id)
        chapter_prayer_groups = defaultdict(list)
        for match in final_deduplicated:
            key = (match['psalm_chapter'], match['prayer_id'])
            chapter_prayer_groups[key].append(match)

        # Check each group for complete chapter coverage
        result = []
        for (psalm_chapter, prayer_id), matches in chapter_prayer_groups.items():
            # Get total number of verses in this Psalm
            conn_temp = sqlite3.connect(self.tanakh_db)
            cursor_temp = conn_temp.cursor()
            cursor_temp.execute("""
                SELECT COUNT(*) FROM verses
                WHERE book_name = 'Psalms' AND chapter = ?
            """, (psalm_chapter,))
            total_verses = cursor_temp.fetchone()[0]
            conn_temp.close()

            # Get unique verse numbers covered by exact_verse matches
            exact_verse_matches = [m for m in matches if m['match_type'] == 'exact_verse']
            covered_verses = set()
            for m in exact_verse_matches:
                if m['psalm_verse_start'] == m['psalm_verse_end']:
                    covered_verses.add(m['psalm_verse_start'])

            # Check if all verses are covered
            if len(covered_verses) == total_verses and total_verses > 0:
                # All verses present! Create single entire_chapter match
                # Find the prayer text to extract context
                conn_temp = sqlite3.connect(self.liturgy_db)
                cursor_temp = conn_temp.cursor()
                cursor_temp.execute("SELECT hebrew_text FROM prayers WHERE prayer_id = ?", (prayer_id,))
                prayer_text = cursor_temp.fetchone()[0]
                conn_temp.close()

                # Extract full chapter from prayer (first verse to last verse)
                first_match = min(exact_verse_matches, key=lambda m: m['psalm_verse_start'])
                last_match = max(exact_verse_matches, key=lambda m: m['psalm_verse_end'])

                # Combine all verse texts to create the chapter phrase
                conn_temp = sqlite3.connect(self.tanakh_db)
                cursor_temp = conn_temp.cursor()
                cursor_temp.execute("""
                    SELECT GROUP_CONCAT(hebrew, ' ')
                    FROM verses
                    WHERE book_name = 'Psalms' AND chapter = ?
                    ORDER BY verse
                """, (psalm_chapter,))
                chapter_text = cursor_temp.fetchone()[0]
                conn_temp.close()

                # Create entire_chapter match
                result.append({
                    'psalm_chapter': psalm_chapter,
                    'psalm_verse_start': 1,
                    'psalm_verse_end': total_verses,
                    'psalm_phrase_hebrew': f"[Entire Psalm {psalm_chapter}]",
                    'psalm_phrase_normalized': self._full_normalize(chapter_text),
                    'phrase_length': total_verses,  # Number of verses
                    'prayer_id': prayer_id,
                    'liturgy_phrase_hebrew': f"[Entire Psalm {psalm_chapter}]",
                    'liturgy_context': f"Complete text of Psalm {psalm_chapter} appears in this prayer",
                    'match_type': 'entire_chapter',
                    'normalization_level': 2,
                    'confidence': 1.0,
                    'distinctiveness_score': 1.0
                })
            else:
                # Not a complete chapter, keep individual matches
                result.extend(matches)

        return result

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
