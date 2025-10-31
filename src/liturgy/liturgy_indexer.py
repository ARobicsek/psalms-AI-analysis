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

# Import Aho-Corasick for efficient multi-pattern matching
try:
    import ahocorasick
except ImportError:
    print("Error: pyahocorasick library not found.")
    print("Please install it by running: pip install pyahocorasick")
    import sys
    sys.exit(1)

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
                print(f"[!] No phrases found for Psalm {psalm_chapter}")
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

        # Search all phrases using Aho-Corasick automaton (OPTIMIZED!)
        # This replaces the old loop that searched each phrase individually
        if self.verbose:
            print(f"Searching all phrases using Aho-Corasick automaton...\n")

        all_matches = self._search_consonantal_optimized(
            phrases=searchable,
            psalm_chapter=psalm_chapter
        )

        if self.verbose and all_matches:
            print(f"\n[+] Found {len(all_matches)} total matches (before deduplication)")

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
            print(f"[+] Indexing complete for Psalm {psalm_chapter}")
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

    def _build_search_automaton(self, phrases: List[Dict], apply_ktiv: bool = False) -> ahocorasick.Automaton:
        """
        Build Aho-Corasick automaton for all normalized phrases.

        This allows searching all phrases simultaneously in a single pass through each prayer,
        dramatically reducing search time from O(phrases × prayers) to O(phrases + prayers).

        Args:
            phrases: List of phrase dicts with 'phrase' field and metadata
            apply_ktiv: If True, apply ktiv male/haser normalization for fuzzy matching

        Returns:
            Compiled automaton ready for searching
        """
        A = ahocorasick.Automaton()

        for i, phrase_data in enumerate(phrases):
            normalized = self._full_normalize(phrase_data['phrase'], apply_ktiv_normalization=apply_ktiv)
            if normalized:  # Skip empty normalized phrases
                # Store (index, original_data) tuple as metadata
                A.add_word(normalized, (i, phrase_data))

        A.make_automaton()
        return A

    def _search_consonantal_optimized(
        self,
        phrases: List[Dict],
        psalm_chapter: int
    ) -> List[Dict]:
        """
        Search all phrases in all prayers using Aho-Corasick automaton.

        This is a MAJOR performance optimization over the old _search_consonantal():
        - Old: O(phrases × prayers × text_length) - search each phrase against each prayer
        - New: O(phrases + prayers × text_length) - build automaton once, search each prayer once
        - Expected speedup: 5-10x (from ~60s to ~6-15s per Psalm)

        Args:
            phrases: List of phrase dicts with metadata (verse_start, verse_end, etc.)
            psalm_chapter: Psalm number (1-150)

        Returns:
            List of match dictionaries (same format as old _search_consonantal)
        """
        if not phrases:
            return []

        # Step 1: Build automatons - one for exact matching, one for fuzzy (ktiv) matching
        if self.verbose:
            print(f"  Building Aho-Corasick automatons for {len(phrases)} phrases...")

        automaton_exact = self._build_search_automaton(phrases, apply_ktiv=False)
        automaton_fuzzy = self._build_search_automaton(phrases, apply_ktiv=True)

        # Step 2: Search each prayer once against both automatons
        matches = []

        conn = sqlite3.connect(self.liturgy_db)
        cursor = conn.cursor()

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

        all_prayers = cursor.fetchall()
        conn.close()

        if self.verbose:
            print(f"  Searching {len(all_prayers)} prayers (two-pass: exact + fuzzy)...")

        for prayer_id, hebrew_text, sefaria_ref, nusach, occasion, service, section, prayer_name in all_prayers:
            # Normalize prayer text twice - once for exact, once for fuzzy
            normalized_prayer_exact = self._full_normalize(hebrew_text, apply_ktiv_normalization=False)
            normalized_prayer_fuzzy = self._full_normalize(hebrew_text, apply_ktiv_normalization=True)

            # Track which phrases we've already matched (to avoid duplicates from fuzzy pass)
            matched_phrases = set()

            # PASS 1: Exact matching (returns all matching phrases in one pass!)
            for end_pos, (phrase_idx, phrase_data) in automaton_exact.iter(normalized_prayer_exact):
                phrase_hebrew = phrase_data['phrase']
                normalized_phrase = self._full_normalize(phrase_hebrew, apply_ktiv_normalization=False)

                # Mark this phrase as matched
                matched_phrases.add(phrase_idx)

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
                    verse_start=phrase_data.get('verse_start'),
                    verse_end=phrase_data.get('verse_end')
                )

                # Calculate confidence
                confidence = self._calculate_confidence(
                    distinctiveness_score=phrase_data.get('distinctiveness_score', 0.0),
                    match_type=match_type
                )

                matches.append({
                    'psalm_chapter': psalm_chapter,
                    'psalm_verse_start': phrase_data.get('verse_start'),
                    'psalm_verse_end': phrase_data.get('verse_end'),
                    'psalm_phrase_hebrew': phrase_hebrew,
                    'psalm_phrase_normalized': normalized_phrase,
                    'phrase_length': len(phrase_hebrew.split()),
                    'prayer_id': prayer_id,
                    'liturgy_phrase_hebrew': liturgy_phrase,
                    'liturgy_context': context,
                    'match_type': match_type,
                    'normalization_level': 2,  # consonantal = 2 (for database compatibility)
                    'confidence': confidence,
                    'distinctiveness_score': phrase_data.get('distinctiveness_score', 0.0)
                })

            # PASS 2: Fuzzy matching with ktiv normalization (only for unmatched phrases)
            for end_pos, (phrase_idx, phrase_data) in automaton_fuzzy.iter(normalized_prayer_fuzzy):
                # Skip if we already matched this phrase in exact pass
                if phrase_idx in matched_phrases:
                    continue

                phrase_hebrew = phrase_data['phrase']
                normalized_phrase = self._full_normalize(phrase_hebrew, apply_ktiv_normalization=True)

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
                    verse_start=phrase_data.get('verse_start'),
                    verse_end=phrase_data.get('verse_end')
                )

                # Calculate confidence
                confidence = self._calculate_confidence(
                    distinctiveness_score=phrase_data.get('distinctiveness_score', 0.0),
                    match_type=match_type
                )

                matches.append({
                    'psalm_chapter': psalm_chapter,
                    'psalm_verse_start': phrase_data.get('verse_start'),
                    'psalm_verse_end': phrase_data.get('verse_end'),
                    'psalm_phrase_hebrew': phrase_hebrew,
                    'psalm_phrase_normalized': normalized_phrase,
                    'phrase_length': len(phrase_hebrew.split()),
                    'prayer_id': prayer_id,
                    'liturgy_phrase_hebrew': liturgy_phrase,
                    'liturgy_context': context,
                    'match_type': match_type,
                    'normalization_level': 2,  # consonantal = 2 (for database compatibility)
                    'confidence': confidence,
                    'distinctiveness_score': phrase_data.get('distinctiveness_score', 0.0)
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
        """
        DEPRECATED: Use _search_consonantal_optimized() instead.

        This method searches one phrase at a time (slow).
        Kept for backward compatibility only.
        """

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

    def _full_normalize(self, text: str, apply_ktiv_normalization: bool = False) -> str:
        """
        Complete normalization pipeline for matching.

        CRITICAL: Must replace maqqef BEFORE stripping vowels, otherwise
        maqqef-connected words become joined (עלמי instead of על מי).

        Order:
        1. Normalize divine name abbreviations (ה' → יהוה)
        2. Handle ktiv-kri notation (remove written, keep read)
        3. Replace maqqef with space (BEFORE vowel stripping)
        4. Strip vowels/cantillation (consonantal)
        5. [Optional] Normalize ktiv male/haser (remove vowel letters)
        6. Remove other punctuation
        7. Normalize whitespace

        Args:
            text: Hebrew text with diacritics
            apply_ktiv_normalization: If True, apply aggressive ktiv male/haser normalization
                                     (removes ו and י vowel letters). Default False for
                                     backward compatibility.

        Returns:
            Normalized consonantal text
        """
        if not text:
            return text

        # STEP 1: Normalize divine name abbreviations (BEFORE vowel stripping!)
        # Replace ה' (hey with geresh) with the full tetragrammaton
        # This ensures liturgical texts match canonical texts
        text = text.replace("ה'", "יהוה")  # divine name abbreviation -> full form

        # STEP 2: Handle ktiv-kri (written/read) variants
        # Pattern: (ktiv) [kri] where ktiv is written form, kri is read form
        # Liturgical texts use the kri (read) form, so remove ktiv and keep kri
        # Example: (וגדלותיך) [וּגְדֻלָּתְךָ֥] -> וּגְדֻלָּתְךָ֥

        # Remove ktiv (written) - anything in parentheses
        text = re.sub(r'\([^)]*\)', '', text)

        # Remove brackets from kri (read) but keep the text
        text = re.sub(r'\[([^\]]*)\]', r'\1', text)

        # STEP 3: Replace maqqef with space (BEFORE stripping vowels!)
        text = text.replace('\u05BE', ' ')  # maqqef -> space

        # STEP 4: Strip vowels and cantillation (consonantal normalization)
        text = normalize_for_search(text, level='consonantal')

        # STEP 5: [Optional] Normalize ktiv male/haser (full vs defective spelling)
        # Only apply if explicitly requested (e.g., for fuzzy matching of spelling variants)
        if apply_ktiv_normalization:
            text = self._normalize_ktiv_male_haser(text)

        # STEP 6: Remove remaining punctuation and markers
        text = text.replace('\u05C0', ' ')  # paseq (|) -> space
        text = text.replace('\u05F3', '')  # geresh
        text = text.replace('\u05F4', '')  # gershayim
        # Note: Parentheses and brackets already handled in ktiv-kri step
        text = re.sub(r'[,.:;!?\-{}\"\'`]', ' ', text)
        # Remove paragraph markers (פ and ס) when standalone
        text = re.sub(r'\s+[פס]\s+', ' ', text)  # Surrounded by whitespace
        text = re.sub(r'\s+[פס]$', '', text)  # At end of text

        # STEP 7: Normalize whitespace
        text = ' '.join(text.split())

        return text

    def _normalize_ktiv_male_haser(self, text: str) -> str:
        """
        Normalize ktiv male/haser (full vs defective spelling) by removing vowel letters.

        Matres lectionis (vowel letters) are consonant letters used to indicate vowels:
        - ו (vav) can represent 'v' (consonant) or 'o'/'u' (vowel)
        - י (yod) can represent 'y' (consonant) or 'i'/'e' (vowel)

        This function removes these letters in contexts where they're most likely vowels.

        Examples:
            נוראותיך → נוראתיך (removes ו representing 'o' sound)
            גדוליך → גדליך (removes ו representing 'o' sound)
            אלוהים → אלהים (removes ו representing 'o' sound)

        Strategy: Remove all ו except at word boundaries (start/end)
                  Remove all י except at word boundaries (start/end)

        This is aggressive but effective for matching spelling variants.

        Args:
            text: Consonantal Hebrew text (already vowel-stripped)

        Returns:
            Text with vowel letters removed
        """
        if not text:
            return text

        # Process each word separately to preserve word boundaries
        words = text.split()
        normalized_words = []

        for word in words:
            if len(word) <= 2:
                # Keep short words as-is to avoid over-normalization
                normalized_words.append(word)
                continue

            # Keep first and last characters, normalize middle
            # This preserves consonantal ו/י at word boundaries while removing internal vowel letters
            if len(word) == 3:
                # For 3-letter words, only normalize middle character if it's ו or י
                first, middle, last = word[0], word[1], word[2]
                if middle in 'וי':
                    # Check if it's likely a vowel (between two consonants)
                    normalized_word = first + last
                else:
                    normalized_word = word
            else:
                # For longer words, remove all internal ו and י
                first = word[0]
                last = word[-1]
                middle = word[1:-1]

                # Remove vowel letters from middle
                # Keep ו at start of middle section if followed by another consonant
                # (e.g., וְ prefix)
                normalized_middle = ''
                i = 0
                while i < len(middle):
                    char = middle[i]
                    if char in 'וי':
                        # Check if this is a consonantal use
                        # If י or ו is at the very start of the middle and followed by ה, keep it
                        # (e.g., יהוה should stay as-is)
                        if i == 0 and char == 'י' and len(middle) > 1 and middle[1] == 'ה':
                            normalized_middle += char
                        # Otherwise, skip vowel letters
                        else:
                            pass  # Skip this vowel letter
                    else:
                        normalized_middle += char
                    i += 1

                normalized_word = first + normalized_middle + last

            normalized_words.append(normalized_word)

        return ' '.join(normalized_words)

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
        """
        Extract surrounding context (±N words) around the match.

        FIXED (Session 45): Completely rewritten to handle all edge cases.
        Previous sliding window approach failed because it tried to match exact
        word counts, but normalization changes word boundaries (paseq, maqqef, etc).

        New approach:
        1. Find position in NORMALIZED text (character-level)
        2. Map back to approximate position in ORIGINAL text
        3. Extract context around that position
        """

        if not full_text or not phrase:
            return ""

        # Full normalization of both texts
        normalized_phrase = self._full_normalize(phrase)
        normalized_text = self._full_normalize(full_text)

        # Find position in normalized text
        pos = normalized_text.find(normalized_phrase)

        if pos == -1:
            # FIX (Session 51): Don't return early! The simple find() fails for many cases.
            # Instead, proceed to the robust sliding window approach below.
            # Use middle of text as starting point for the search.
            ratio = 0.5
        else:
            # Calculate approximate position ratio in original text
            # This works because normalization preserves most text length
            ratio = pos / len(normalized_text) if len(normalized_text) > 0 else 0

        approx_char_pos = int(ratio * len(full_text))

        # Find nearest word boundary before the approximate position
        words = full_text.split()

        # Build cumulative character positions for each word
        char_positions = []
        cumulative_pos = 0
        for word in words:
            char_positions.append(cumulative_pos)
            cumulative_pos += len(word) + 1  # +1 for space

        # Find word index closest to approximate position
        word_idx = 0
        for i, char_pos in enumerate(char_positions):
            if char_pos <= approx_char_pos:
                word_idx = i
            else:
                break

        # Now search forward/backward from this approximate position using sliding window
        # to find the exact match
        normalized_phrase_words = normalized_phrase.split()
        phrase_word_count = len(normalized_phrase_words)

        # Search in a window around the approximate position
        search_start = max(0, word_idx - 50)
        search_end = min(len(words), word_idx + 50 + phrase_word_count)

        match_word_idx = None

        # Try different window sizes to handle normalization edge cases
        for window_size in [phrase_word_count, phrase_word_count + 1, phrase_word_count + 2,
                           phrase_word_count - 1, phrase_word_count + 3]:
            if window_size < 1:
                continue

            for i in range(search_start, min(search_end, len(words) - window_size + 1)):
                window = words[i:i + window_size]
                window_text = ' '.join(window)
                normalized_window = self._full_normalize(window_text)

                if normalized_window == normalized_phrase:
                    match_word_idx = i
                    phrase_word_count = window_size  # Update to actual matched size
                    break

            if match_word_idx is not None:
                break

        if match_word_idx is None:
            # Fallback: If still not found, use approximate position
            # This shouldn't happen often, but provides graceful degradation
            match_word_idx = word_idx

        # Extract context: ±context_words around the match
        start_idx = max(0, match_word_idx - context_words)
        end_idx = min(len(words), match_word_idx + phrase_word_count + context_words)

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

        FIXED (Session 45): Uses improved position-based search like _extract_context.
        """

        if not full_text or not phrase:
            return phrase

        # Full normalization of both texts
        normalized_phrase = self._full_normalize(phrase)
        normalized_text = self._full_normalize(full_text)

        # Find position in normalized text
        pos = normalized_text.find(normalized_phrase)

        if pos == -1:
            return phrase  # Phrase not found, return original

        # Calculate approximate position ratio in original text
        ratio = pos / len(normalized_text) if len(normalized_text) > 0 else 0
        approx_char_pos = int(ratio * len(full_text))

        # Find nearest word boundary
        words = full_text.split()

        # Build cumulative character positions
        char_positions = []
        cumulative_pos = 0
        for word in words:
            char_positions.append(cumulative_pos)
            cumulative_pos += len(word) + 1

        # Find word index closest to approximate position
        word_idx = 0
        for i, char_pos in enumerate(char_positions):
            if char_pos <= approx_char_pos:
                word_idx = i
            else:
                break

        # Search around approximate position with different window sizes
        normalized_phrase_words = normalized_phrase.split()
        phrase_word_count = len(normalized_phrase_words)

        search_start = max(0, word_idx - 20)
        search_end = min(len(words), word_idx + 20 + phrase_word_count)

        # Try different window sizes
        for window_size in [phrase_word_count, phrase_word_count + 1, phrase_word_count + 2,
                           phrase_word_count - 1, phrase_word_count + 3]:
            if window_size < 1:
                continue

            for i in range(search_start, min(search_end, len(words) - window_size + 1)):
                window = words[i:i + window_size]
                window_text = ' '.join(window)
                normalized_window = self._full_normalize(window_text)

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

        # SECOND PASS: Check if merged phrases equal full verses and upgrade to exact_verse
        # Also remove phrase matches when verse match exists for same verse-prayer pair
        verse_groups = defaultdict(list)
        for match in deduplicated:
            key = (
                match['psalm_chapter'],
                match['psalm_verse_start'],
                match['psalm_verse_end'],
                match['prayer_id']
            )
            verse_groups[key].append(match)

        # Connect to Tanakh DB to compare with full verses
        conn_tanakh = sqlite3.connect(self.tanakh_db)
        cursor_tanakh = conn_tanakh.cursor()

        final_deduplicated = []
        for (psalm_ch, verse_start, verse_end, prayer_id), group_matches in verse_groups.items():
            # Check if any match is exact_verse
            has_exact_verse = any(m['match_type'] == 'exact_verse' for m in group_matches)

            if has_exact_verse:
                # Keep only exact_verse matches
                final_deduplicated.extend([m for m in group_matches if m['match_type'] == 'exact_verse'])
            else:
                # Check if phrase matches should be upgraded to exact_verse
                # This handles cases where deduplication merged overlapping phrases
                # that together equal a full verse
                upgraded = False

                # Only check single-verse matches (verse_start == verse_end)
                if verse_start == verse_end and verse_start is not None:
                    # Get full verse text
                    cursor_tanakh.execute("""
                        SELECT hebrew FROM verses
                        WHERE book_name = 'Psalms' AND chapter = ? AND verse = ?
                    """, (psalm_ch, verse_start))

                    verse_result = cursor_tanakh.fetchone()
                    if verse_result:
                        verse_text = verse_result[0]
                        normalized_verse = self._full_normalize(verse_text)

                        # Check each phrase match to see if it equals the full verse
                        for match in group_matches:
                            normalized_phrase = match['psalm_phrase_normalized']

                            if normalized_verse == normalized_phrase:
                                # Upgrade to exact_verse!
                                match['match_type'] = 'exact_verse'
                                match['confidence'] = 1.0
                                match['distinctiveness_score'] = 1.0
                                upgraded = True
                                if self.verbose:
                                    print(f"  [^] Upgraded phrase to exact_verse: Psalm {psalm_ch}:{verse_start}")

                # Keep all matches (with possible upgrades)
                final_deduplicated.extend(group_matches)

        conn_tanakh.close()

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

            # Also get verse texts for comparison
            cursor_temp.execute("""
                SELECT verse, hebrew FROM verses
                WHERE book_name = 'Psalms' AND chapter = ?
                ORDER BY verse
            """, (psalm_chapter,))
            verse_texts = {verse_num: hebrew for verse_num, hebrew in cursor_temp.fetchall()}
            conn_temp.close()

            # ISSUE #3 & #4 FIX: Check phrase_match entries to see if they're actually
            # complete verses (>95% match) and upgrade them before chapter detection
            for match in matches:
                if match['match_type'] == 'phrase_match' and match['psalm_verse_start'] == match['psalm_verse_end']:
                    verse_num = match['psalm_verse_start']
                    if verse_num in verse_texts:
                        full_verse = verse_texts[verse_num]
                        normalized_verse = self._full_normalize(full_verse)
                        normalized_phrase = match['psalm_phrase_normalized']

                        # Calculate match percentage
                        verse_words = set(normalized_verse.split())
                        phrase_words = set(normalized_phrase.split())

                        if len(verse_words) > 0:
                            overlap = len(verse_words & phrase_words)
                            match_pct = overlap / len(verse_words)

                            # If >80% of verse words are present, upgrade to exact_verse
                            if match_pct >= 0.80:
                                match['match_type'] = 'exact_verse'
                                match['confidence'] = round(match_pct, 3)
                                if self.verbose:
                                    print(f"  [^] Upgraded near-complete phrase to exact_verse: Psalm {psalm_chapter}:{verse_num} ({match_pct*100:.0f}%)")

            # Get unique verse numbers covered by exact_verse matches (after upgrades)
            exact_verse_matches = [m for m in matches if m['match_type'] == 'exact_verse']
            covered_verses = set()
            for m in exact_verse_matches:
                # Count ALL verses in the match range, not just single-verse matches
                # This fixes the bug where multi-verse exact_verse matches weren't counted
                for v in range(m['psalm_verse_start'], m['psalm_verse_end'] + 1):
                    covered_verses.add(v)

            # Check if all or nearly all verses are covered
            coverage_pct = len(covered_verses) / total_verses if total_verses > 0 else 0

            # FIX (Session 51): VALIDATE that the actual verse CONTENT matches
            # before claiming entire_chapter. This prevents false positives where
            # phrases from different psalms get confused (e.g., Psalm 25 vs Psalm 86).
            #
            # The bug: If Psalm 25 phrases get mislabeled as Psalm 86, we might see
            # 16 "covered verses" that match Psalm 86's verse count, but the actual
            # Hebrew text in the prayer is from Psalm 25, not Psalm 86.
            #
            # Solution: STRICT validation - check ALL verses using substring matching.
            # Word counting can give false positives if two psalms share common vocabulary.
            if coverage_pct >= 0.90 and total_verses > 0:
                # Get the prayer text for verification
                conn_temp_verify = sqlite3.connect(self.liturgy_db)
                cursor_temp_verify = conn_temp_verify.cursor()
                cursor_temp_verify.execute("SELECT hebrew_text FROM prayers WHERE prayer_id = ?", (prayer_id,))
                prayer_text_for_verify = cursor_temp_verify.fetchone()[0]
                conn_temp_verify.close()

                # Normalize the prayer text once
                normalized_prayer = self._full_normalize(prayer_text_for_verify)

                # STRICT VALIDATION: Check ALL covered verses, not just a sample
                verification_passed = True
                failed_verses = []

                for verse_num in covered_verses:
                    if verse_num not in verse_texts:
                        # Verse number doesn't exist in this psalm!
                        verification_passed = False
                        if self.verbose:
                            print(f"  [!] VALIDATION FAILED: Psalm {psalm_chapter} verse {verse_num} doesn't exist (psalm has {total_verses} verses)")
                        break

                    # Get canonical verse text and normalize it
                    canonical_verse = verse_texts[verse_num]
                    normalized_canonical = self._full_normalize(canonical_verse)

                    # STRICT CHECK: The entire normalized verse must appear as a substring
                    # in the normalized prayer. Not just word overlap!
                    if normalized_canonical not in normalized_prayer:
                        # Try lenient check: 95% of verse must be present as contiguous substring
                        verse_words = normalized_canonical.split()
                        if len(verse_words) < 3:
                            # For very short verses, require exact match
                            failed_verses.append(verse_num)
                            continue

                        # Check if at least 90% of the verse text is present as contiguous substring
                        # (Lowered from 95% to handle edge cases like missing paragraph markers)
                        min_length = int(len(normalized_canonical) * 0.90)
                        found_substring = False
                        for i in range(len(verse_words)):
                            for j in range(i+1, len(verse_words)+1):
                                substring = ' '.join(verse_words[i:j])
                                if len(substring) >= min_length and substring in normalized_prayer:
                                    found_substring = True
                                    break
                            if found_substring:
                                break

                        if not found_substring:
                            failed_verses.append(verse_num)

                if failed_verses:
                    verification_passed = False
                    failed_str = ', '.join(map(str, sorted(failed_verses)))
                    if self.verbose:
                        print(f"  [!] VALIDATION FAILED: Psalm {psalm_chapter} verses {failed_str} not found in prayer")
                        print(f"      ({len(failed_verses)}/{len(covered_verses)} verses failed substring check)")

                if not verification_passed:
                    # Verification failed - this is a false positive
                    if self.verbose:
                        print(f"  [!] Skipping entire_chapter for Psalm {psalm_chapter} in Prayer {prayer_id} - verification failed")
                    # Fall through to add individual matches instead
                    coverage_pct = 0  # Force skip of entire_chapter logic

            if coverage_pct >= 0.90 and total_verses > 0:
                # All verses or nearly all (≥90%) present! Replace with single entire_chapter match
                is_complete = (len(covered_verses) == total_verses)

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

                # Determine context message based on completeness
                if is_complete:
                    context_msg = f"Complete text of Psalm {psalm_chapter} appears in this prayer"
                    confidence = 1.0
                else:
                    missing_verses = sorted(set(range(1, total_verses + 1)) - covered_verses)
                    missing_str = ", ".join(map(str, missing_verses))
                    context_msg = f"LIKELY complete text of Psalm {psalm_chapter} appears in this prayer ({coverage_pct*100:.0f}% coverage; missing verses: {missing_str})"
                    confidence = round(coverage_pct, 3)
                    if self.verbose:
                        print(f"  [^] Near-complete psalm detected: {coverage_pct*100:.0f}% coverage (missing {missing_str})")

                # Add entire_chapter entry (replacing individual matches for THIS prayer)
                # This prevents duplicate entries when the full psalm is present
                result.append({
                    'psalm_chapter': psalm_chapter,
                    'psalm_verse_start': 1,
                    'psalm_verse_end': total_verses,
                    'psalm_phrase_hebrew': f"[Entire Psalm {psalm_chapter}]",
                    'psalm_phrase_normalized': self._full_normalize(chapter_text),
                    'phrase_length': total_verses,  # Number of verses
                    'prayer_id': prayer_id,
                    'liturgy_phrase_hebrew': f"[Entire Psalm {psalm_chapter}]",
                    'liturgy_context': context_msg,
                    'match_type': 'entire_chapter',
                    'normalization_level': 2,
                    'confidence': confidence,
                    'distinctiveness_score': 1.0
                })
                # Continue to next prayer - skip adding individual matches for this prayer
                continue
            else:
                # Not a complete chapter, check for consecutive verse ranges (Issue #5)
                # Sort exact_verse matches by verse number
                sorted_verses = sorted(
                    [m for m in exact_verse_matches if m['psalm_verse_start'] == m['psalm_verse_end']],
                    key=lambda m: m['psalm_verse_start']
                )

                # Find consecutive sequences (minimum 2 verses for consolidation)
                if len(sorted_verses) >= 2:
                    sequences = []
                    current_seq = [sorted_verses[0]]

                    for match in sorted_verses[1:]:
                        if match['psalm_verse_start'] == current_seq[-1]['psalm_verse_start'] + 1:
                            current_seq.append(match)
                        else:
                            if len(current_seq) >= 2:
                                sequences.append(current_seq)
                            current_seq = [match]

                    # Don't forget the last sequence
                    if len(current_seq) >= 2:
                        sequences.append(current_seq)

                    # Replace sequences with verse_range entries
                    if sequences:
                        # Keep matches that are not part of sequences
                        verse_nums_in_sequences = set()
                        for seq in sequences:
                            for match in seq:
                                verse_nums_in_sequences.add(match['psalm_verse_start'])

                        # Add non-sequence matches
                        for match in matches:
                            if match not in sorted_verses or match['psalm_verse_start'] not in verse_nums_in_sequences:
                                result.append(match)

                        # Add verse_range entries for each sequence
                        # CRITICAL FIX: Validate ALL verses in range before creating the verse_range entry
                        for seq in sequences:
                            first_verse = seq[0]['psalm_verse_start']
                            last_verse = seq[-1]['psalm_verse_start']

                            # VALIDATION: Check that ALL verses in the range actually exist in prayer
                            # This prevents false positives where verse numbers are consecutive
                            # but some verses are actually missing/mismatched
                            conn_temp_validate = sqlite3.connect(self.liturgy_db)
                            cursor_temp_validate = conn_temp_validate.cursor()
                            cursor_temp_validate.execute("SELECT hebrew_text FROM prayers WHERE prayer_id = ?", (prayer_id,))
                            prayer_text_validate = cursor_temp_validate.fetchone()[0]
                            conn_temp_validate.close()

                            normalized_prayer_validate = self._full_normalize(prayer_text_validate)

                            # Get all verses in the range from Tanakh
                            conn_temp_tanakh = sqlite3.connect(self.tanakh_db)
                            cursor_temp_tanakh = conn_temp_tanakh.cursor()
                            cursor_temp_tanakh.execute("""
                                SELECT verse, hebrew FROM verses
                                WHERE book_name = 'Psalms' AND chapter = ?
                                  AND verse >= ? AND verse <= ?
                                ORDER BY verse
                            """, (psalm_chapter, first_verse, last_verse))
                            verses_in_range = {verse_num: hebrew for verse_num, hebrew in cursor_temp_tanakh.fetchall()}
                            conn_temp_tanakh.close()

                            # Validate each verse in the range
                            all_valid = True
                            failed_verse_nums = []
                            for verse_num in range(first_verse, last_verse + 1):
                                if verse_num not in verses_in_range:
                                    all_valid = False
                                    failed_verse_nums.append(verse_num)
                                    continue

                                canonical_verse = verses_in_range[verse_num]
                                normalized_canonical = self._full_normalize(canonical_verse)

                                # Check if verse appears in prayer (same logic as entire_chapter validation)
                                if normalized_canonical not in normalized_prayer_validate:
                                    # Try lenient check: 90% of verse must be present
                                    verse_words = normalized_canonical.split()
                                    if len(verse_words) < 3:
                                        all_valid = False
                                        failed_verse_nums.append(verse_num)
                                        continue

                                    min_length = int(len(normalized_canonical) * 0.90)
                                    found_substring = False
                                    for i in range(len(verse_words)):
                                        for j in range(i+1, len(verse_words)+1):
                                            substring = ' '.join(verse_words[i:j])
                                            if len(substring) >= min_length and substring in normalized_prayer_validate:
                                                found_substring = True
                                                break
                                        if found_substring:
                                            break

                                    if not found_substring:
                                        all_valid = False
                                        failed_verse_nums.append(verse_num)

                            # Only create verse_range if ALL verses validated
                            if all_valid:
                                if self.verbose:
                                    print(f"  [^] Consolidated consecutive verses to verse_range: Psalm {psalm_chapter}:{first_verse}-{last_verse}")

                                result.append({
                                    'psalm_chapter': psalm_chapter,
                                    'psalm_verse_start': first_verse,
                                    'psalm_verse_end': last_verse,
                                    'psalm_phrase_hebrew': f"[Psalm {psalm_chapter}:{first_verse}-{last_verse}]",
                                    'psalm_phrase_normalized': '',  # Not needed for range
                                    'phrase_length': len(seq),  # Number of verses
                                    'prayer_id': prayer_id,
                                    'liturgy_phrase_hebrew': f"[Psalm {psalm_chapter}:{first_verse}-{last_verse}]",
                                    'liturgy_context': f"Verses {first_verse}-{last_verse} of Psalm {psalm_chapter} appear consecutively",
                                    'match_type': 'verse_range',
                                    'normalization_level': 2,
                                    'confidence': 1.0,
                                    'distinctiveness_score': 1.0
                                })
                            else:
                                # Validation failed - keep only the valid individual verse matches
                                failed_str = ', '.join(map(str, failed_verse_nums))
                                if self.verbose:
                                    print(f"  [!] Cannot consolidate verses {first_verse}-{last_verse}: validation failed for verses {failed_str}")
                                    print(f"      Keeping individual validated matches only")

                                # Add back only the verse matches that would have passed validation
                                for match in seq:
                                    verse_num = match['psalm_verse_start']
                                    if verse_num not in failed_verse_nums:
                                        result.append(match)
                    else:
                        # No sequences found, keep all matches
                        result.extend(matches)
                else:
                    # Not enough verses for sequences, keep all matches
                    result.extend(matches)

            # THIRD PASS: Consolidate multiple verse_range/exact_verse into discontinuous verse_set
            # This creates entries like "Psalm 145: verses 13, 17, 21" or "1-5, 7-10, 14"
            # Only apply if there are multiple verse-level entries (not including phrase_match)
            verse_level_entries = [m for m in result if m['prayer_id'] == prayer_id and
                                    m['match_type'] in ('exact_verse', 'verse_range')]

            if len(verse_level_entries) >= 2:
                # Extract verse ranges/numbers
                ranges = []
                for entry in verse_level_entries:
                    if entry['psalm_verse_start'] == entry['psalm_verse_end']:
                        ranges.append(str(entry['psalm_verse_start']))
                    else:
                        ranges.append(f"{entry['psalm_verse_start']}-{entry['psalm_verse_end']}")

                # Create verse_set entry
                discontinuous_range_str = ", ".join(ranges)
                all_verses = set()
                for entry in verse_level_entries:
                    for v in range(entry['psalm_verse_start'], entry['psalm_verse_end'] + 1):
                        all_verses.add(v)

                if self.verbose:
                    print(f"  [^] Consolidated to discontinuous verse_set: Psalm {psalm_chapter}: {discontinuous_range_str}")

                # Remove the individual verse entries for THIS prayer
                result = [m for m in result if not (m['prayer_id'] == prayer_id and
                                                     m['match_type'] in ('exact_verse', 'verse_range'))]

                # Add the consolidated verse_set entry
                # Store actual verses in locations field as JSON for accurate coverage calculation
                import json
                result.append({
                    'psalm_chapter': psalm_chapter,
                    'psalm_verse_start': min(all_verses),
                    'psalm_verse_end': max(all_verses),
                    'psalm_phrase_hebrew': f"[Psalm {psalm_chapter}: {discontinuous_range_str}]",
                    'psalm_phrase_normalized': '',
                    'phrase_length': len(all_verses),
                    'prayer_id': prayer_id,
                    'liturgy_phrase_hebrew': f"[Psalm {psalm_chapter}: {discontinuous_range_str}]",
                    'liturgy_context': f"Verses {discontinuous_range_str} of Psalm {psalm_chapter}",
                    'match_type': 'verse_set',  # New match type for discontinuous ranges
                    'normalization_level': 2,
                    'confidence': 1.0,
                    'distinctiveness_score': 1.0,
                    'locations': json.dumps(sorted(all_verses))  # Store actual verses for coverage calc
                })

            # SECOND PASS: After consolidation, check if verse_range + exact_verse now cover entire chapter
            # This handles cases where consolidation created verse_range entries that, together with
            # any remaining exact_verse or high-confidence phrase_match, cover all verses (Issue #8)
            if result:  # Only check if we have matches
                # Get all matches that represent verified verses
                # Include: exact_verse, verse_range, verse_set, AND high-confidence (>=80%) phrase_match
                verified_matches = [
                    m for m in result
                    if m['match_type'] in ('exact_verse', 'verse_range', 'verse_set')
                    or (m['match_type'] == 'phrase_match' and m.get('confidence', 0) >= 0.80)
                ]
                covered_verses_v2 = set()
                for m in verified_matches:
                    if m['match_type'] == 'verse_set' and m.get('locations'):
                        # For verse_set, use the actual verses from locations field
                        import json
                        covered_verses_v2.update(json.loads(m['locations']))
                    else:
                        # For continuous ranges, use start to end
                        for v in range(m['psalm_verse_start'], m['psalm_verse_end'] + 1):
                            covered_verses_v2.add(v)

                # Check if all or nearly all verses are now covered
                coverage_pct_v2 = len(covered_verses_v2) / total_verses if total_verses > 0 else 0

                # FIX (Session 51): VALIDATION for second pass too!
                # Same strict validation as first pass - check verse content, not just counts
                if coverage_pct_v2 >= 0.90 and total_verses > 0:
                    # Get the prayer text for verification
                    conn_temp_verify = sqlite3.connect(self.liturgy_db)
                    cursor_temp_verify = conn_temp_verify.cursor()
                    cursor_temp_verify.execute("SELECT hebrew_text FROM prayers WHERE prayer_id = ?", (prayer_id,))
                    prayer_text_for_verify = cursor_temp_verify.fetchone()[0]
                    conn_temp_verify.close()

                    # Get verse texts for validation
                    conn_temp_tanakh = sqlite3.connect(self.tanakh_db)
                    cursor_temp_tanakh = conn_temp_tanakh.cursor()
                    cursor_temp_tanakh.execute("""
                        SELECT verse, hebrew FROM verses
                        WHERE book_name = 'Psalms' AND chapter = ?
                        ORDER BY verse
                    """, (psalm_chapter,))
                    verse_texts_v2 = {verse_num: hebrew for verse_num, hebrew in cursor_temp_tanakh.fetchall()}
                    conn_temp_tanakh.close()

                    # Normalize the prayer text once
                    normalized_prayer_v2 = self._full_normalize(prayer_text_for_verify)

                    # STRICT VALIDATION: Check ALL covered verses
                    verification_passed_v2 = True
                    failed_verses_v2 = []

                    for verse_num in covered_verses_v2:
                        if verse_num not in verse_texts_v2:
                            verification_passed_v2 = False
                            if self.verbose:
                                print(f"  [!] VALIDATION FAILED (2nd pass): Psalm {psalm_chapter} verse {verse_num} doesn't exist")
                            break

                        canonical_verse = verse_texts_v2[verse_num]
                        normalized_canonical = self._full_normalize(canonical_verse)

                        # STRICT CHECK: verse must appear as substring
                        if normalized_canonical not in normalized_prayer_v2:
                            # Try lenient check: 95% of verse as contiguous substring
                            verse_words = normalized_canonical.split()
                            if len(verse_words) < 3:
                                failed_verses_v2.append(verse_num)
                                continue

                            # Check if at least 90% of the verse text is present as contiguous substring
                            # (Lowered from 95% to handle edge cases like missing paragraph markers)
                            min_length = int(len(normalized_canonical) * 0.90)
                            found_substring = False
                            for i in range(len(verse_words)):
                                for j in range(i+1, len(verse_words)+1):
                                    substring = ' '.join(verse_words[i:j])
                                    if len(substring) >= min_length and substring in normalized_prayer_v2:
                                        found_substring = True
                                        break
                                if found_substring:
                                    break

                            if not found_substring:
                                failed_verses_v2.append(verse_num)

                    if failed_verses_v2:
                        verification_passed_v2 = False
                        failed_str_v2 = ', '.join(map(str, sorted(failed_verses_v2)))
                        if self.verbose:
                            print(f"  [!] VALIDATION FAILED (2nd pass): Psalm {psalm_chapter} verses {failed_str_v2} not found")
                            print(f"      ({len(failed_verses_v2)}/{len(covered_verses_v2)} verses failed substring check)")

                    if not verification_passed_v2:
                        if self.verbose:
                            print(f"  [!] Skipping entire_chapter (2nd pass) for Psalm {psalm_chapter} in Prayer {prayer_id}")
                        coverage_pct_v2 = 0  # Force skip

                if coverage_pct_v2 >= 0.90 and total_verses > 0:
                    # All verses or nearly all (≥90%) present after consolidation!
                    is_complete = (len(covered_verses_v2) == total_verses)

                    if self.verbose:
                        if is_complete:
                            print(f"  [^] Second pass: Detected entire chapter after consolidation (Psalm {psalm_chapter})")
                        else:
                            print(f"  [^] Second pass: Detected near-complete chapter ({coverage_pct_v2*100:.0f}% coverage, Psalm {psalm_chapter})")

                    # Find the prayer text to extract context
                    conn_temp = sqlite3.connect(self.liturgy_db)
                    cursor_temp = conn_temp.cursor()
                    cursor_temp.execute("SELECT hebrew_text FROM prayers WHERE prayer_id = ?", (prayer_id,))
                    prayer_text = cursor_temp.fetchone()[0]
                    conn_temp.close()

                    # Get chapter text from Tanakh for normalization
                    conn_tanakh = sqlite3.connect(self.tanakh_db)
                    cursor_tanakh = conn_tanakh.cursor()
                    cursor_tanakh.execute("""
                        SELECT GROUP_CONCAT(hebrew, ' ')
                        FROM verses
                        WHERE book_name = 'Psalms' AND chapter = ?
                        ORDER BY verse
                    """, (psalm_chapter,))
                    chapter_text = cursor_tanakh.fetchone()[0]
                    conn_tanakh.close()

                    # Determine context message based on completeness
                    if is_complete:
                        context_msg = f"Complete text of Psalm {psalm_chapter} appears in this prayer"
                        confidence = 1.0
                    else:
                        missing_verses_v2 = sorted(set(range(1, total_verses + 1)) - covered_verses_v2)
                        missing_str_v2 = ", ".join(map(str, missing_verses_v2))
                        context_msg = f"LIKELY complete text of Psalm {psalm_chapter} appears in this prayer ({coverage_pct_v2*100:.0f}% coverage; missing verses: {missing_str_v2})"
                        confidence = round(coverage_pct_v2, 3)

                    # Clear THIS prayer's entries and replace with single entire_chapter entry
                    # This prevents duplicate entries when the full psalm is present
                    # Filter out all entries for this specific prayer, then add entire_chapter
                    result = [r for r in result if r['prayer_id'] != prayer_id]
                    result.append({
                        'psalm_chapter': psalm_chapter,
                        'psalm_verse_start': 1,
                        'psalm_verse_end': total_verses,
                        'psalm_phrase_hebrew': f"[Entire Psalm {psalm_chapter}]",
                        'psalm_phrase_normalized': self._full_normalize(chapter_text),
                        'phrase_length': total_verses,  # Number of verses
                        'prayer_id': prayer_id,
                        'liturgy_phrase_hebrew': f"[Entire Psalm {psalm_chapter}]",
                        'liturgy_context': context_msg,
                        'match_type': 'entire_chapter',
                        'normalization_level': 2,
                        'confidence': confidence,
                        'distinctiveness_score': 1.0
                    })

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
                distinctiveness_score,
                locations
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            match['distinctiveness_score'],
            match.get('locations')  # Optional field for verse_set entries
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
                    print(f"[X] Error indexing {error_msg}\n")

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
