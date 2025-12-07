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
    from src.concordance.hebrew_text_processor import normalize_for_search, split_words, normalize_word_sequence
    from src.data_sources.tanakh_database import TanakhDatabase
else:
    from ..concordance.search import ConcordanceSearch, SearchResult
    from ..concordance.hebrew_text_processor import normalize_for_search, split_words, normalize_word_sequence
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
    auto_scope_threshold: int = 30  # Results threshold for applying intelligent filtering
    alternate_queries: Optional[List[str]] = None  # Additional forms to search (e.g., different conjugations)
    source_psalm: Optional[int] = None  # Current psalm being analyzed (to ensure inclusion in scope)
    # Phase 2 tracking fields
    lexical_insight_id: Optional[str] = None  # ID to group searches from same lexical insight
    is_primary_search: Optional[bool] = None  # True if this is the primary phrase, False if variant
    insight_notes: Optional[str] = None  # Notes about the lexical insight (from micro analyst)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConcordanceRequest':
        """Create from dictionary."""
        return cls(
            query=data['query'],
            scope='auto',  # Always use auto - librarian will determine optimal scope
            level=data.get('level', 'consonantal'),
            include_variations=data.get('include_variations', True),
            notes=data.get('notes'),
            max_results=data.get('max_results', 50),
            auto_scope_threshold=data.get('auto_scope_threshold', 30),
            alternate_queries=data.get('alternate_queries', data.get('alternates')),  # Support both names
            source_psalm=data.get('source_psalm'),  # Current psalm being analyzed
            # Phase 2 tracking fields
            lexical_insight_id=data.get('lexical_insight_id'),
            is_primary_search=data.get('is_primary_search'),
            insight_notes=data.get('insight_notes')
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
                    'matched_word': r.matched_phrase if r.is_phrase_match else r.matched_word,
                    'position': r.word_position,
                    'is_phrase_match': r.is_phrase_match,
                    'phrase_positions': r.phrase_positions
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

    def __init__(self, db: Optional[TanakhDatabase] = None, logger=None):
        """
        Initialize Concordance Librarian.

        Args:
            db: TanakhDatabase instance (creates new if None)
            logger: Optional logger instance
        """
        self.db = db or TanakhDatabase()
        self.search = ConcordanceSearch(self.db)
        self.logger = logger

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

        # NEW: Handle maqqef splitting in original phrase
        # If phrase contains maqqef (־), generate split version
        if '־' in phrase:
            # Split on maqqefs and rejoin with spaces
            split_phrase = phrase.replace('־', ' ')
            # Remove any extra spaces
            split_phrase = ' '.join(split_phrase.split())
            variations.add(split_phrase)
            if self.logger:
                self.logger.debug(f"Added split form for maqqef phrase: '{phrase}' → '{split_phrase}'")

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

            # NEW: Add systematic prefix+suffix combinations
            variations.update(self._generate_combination_variations(words, level))

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

        # For 3-word phrases, only generate full combination
        elif len(words) == 3:
            # All three combined as single token (rare but possible)
            variations.add(words[0] + words[1] + words[2])

        return variations

    def _generate_suffix_variations(self, words: List[str], level: str) -> Set[str]:
        """
        Generate variations with pronominal suffixes on ANY word in the phrase.

        Hebrew nouns and verbs often take pronominal suffixes. For example:
        - "ראש" (head) → "ראשי" (my head)
        - "מלך" (king) → "מלכו" (his king)
        - "הר קדש" (holy mountain) → "בהר קדשך" (in your holy mountain)

        This generates combinations with:
        - Suffixes on each word independently
        - Suffixes on multiple words simultaneously
        - Prefixes on first word combined with suffixes on any word

        Args:
            words: List of Hebrew words
            level: Normalization level

        Returns:
            Set of phrase variations with suffixes on any/all words
        """
        variations = set()

        if len(words) < 2:
            return variations

        # Strategy: Generate suffix variations for EACH word independently,
        # then also generate combinations with suffixes on multiple words

        # 1. Add suffix to each word independently (one at a time)
        for word_idx in range(len(words)):
            for suffix in self.PRONOMINAL_SUFFIXES:
                # Create variation with suffix on this word only
                modified_words = words.copy()
                modified_words[word_idx] = words[word_idx] + suffix
                variation = ' '.join(modified_words)
                variations.add(variation)

                # Also try common prefix patterns on the FIRST word
                # (even when suffix is on a different word)
                if word_idx > 0:
                    # Suffix is not on first word, so try prefixes on first word

                    # Conjunction on first word
                    prefixed_words = [self.CONJUNCTION + words[0]] + modified_words[1:]
                    variations.add(' '.join(prefixed_words))

                    # Prepositions on first word
                    for prep in self.PREPOSITIONS:
                        prefixed_words = [prep + words[0]] + modified_words[1:]
                        variations.add(' '.join(prefixed_words))

                        # Conjunction + preposition on first word
                        prefixed_words = [self.CONJUNCTION + prep + words[0]] + modified_words[1:]
                        variations.add(' '.join(prefixed_words))

                    # Definite article on first word
                    prefixed_words = [self.DEFINITE_ARTICLE + words[0]] + modified_words[1:]
                    variations.add(' '.join(prefixed_words))

                    # Conjunction + definite on first word
                    prefixed_words = [self.CONJUNCTION + self.DEFINITE_ARTICLE + words[0]] + modified_words[1:]
                    variations.add(' '.join(prefixed_words))

                    # Preposition + definite on first word
                    for prep in self.PREPOSITIONS:
                        prefixed_words = [prep + self.DEFINITE_ARTICLE + words[0]] + modified_words[1:]
                        variations.add(' '.join(prefixed_words))

                # When suffix IS on first word, also try prefixes on that same word
                elif word_idx == 0:
                    # Conjunction before suffix
                    prefixed_words = [self.CONJUNCTION + modified_words[0]] + modified_words[1:]
                    variations.add(' '.join(prefixed_words))

                    # Prepositions before suffix
                    for prep in self.PREPOSITIONS:
                        prefixed_words = [prep + modified_words[0]] + modified_words[1:]
                        variations.add(' '.join(prefixed_words))

                        # Conjunction + preposition before suffix
                        prefixed_words = [self.CONJUNCTION + prep + modified_words[0]] + modified_words[1:]
                        variations.add(' '.join(prefixed_words))

                    # Definite article before suffix
                    prefixed_words = [self.DEFINITE_ARTICLE + modified_words[0]] + modified_words[1:]
                    variations.add(' '.join(prefixed_words))

                    # Conjunction + definite before suffix
                    prefixed_words = [self.CONJUNCTION + self.DEFINITE_ARTICLE + modified_words[0]] + modified_words[1:]
                    variations.add(' '.join(prefixed_words))

                    # Preposition + definite before suffix
                    for prep in self.PREPOSITIONS:
                        prefixed_words = [prep + self.DEFINITE_ARTICLE + modified_words[0]] + modified_words[1:]
                        variations.add(' '.join(prefixed_words))

        # 2. For 2-word phrases, also generate variations with suffixes on BOTH words
        # (Common pattern: "מלכי צדקי" = "my king of my righteousness")
        if len(words) == 2:
            for suffix1 in self.PRONOMINAL_SUFFIXES:
                for suffix2 in self.PRONOMINAL_SUFFIXES:
                    modified_words = [words[0] + suffix1, words[1] + suffix2]
                    variation = ' '.join(modified_words)
                    variations.add(variation)

                    # Also with common prefixes on first word
                    for prefix in ['ו', 'ב', 'כ', 'ל', 'מ']:
                        prefixed_words = [prefix + modified_words[0], modified_words[1]]
                        variations.add(' '.join(prefixed_words))

        # CRITICAL FIX: Filter out incomplete variations
        # Ensure all variations have the same number of words as the original phrase
        original_word_count = len(words)
        variations = {v for v in variations if len(v.split()) == original_word_count}

        return variations

    def _generate_combination_variations(self, words: List[str], level: str) -> Set[str]:
        """
        Generate ALL combinations of prefixes on first word with suffixes on other words.

        This ensures we capture cases like:
        - "דבר אמת בלב" → "ודבר אמת בלבבו" (prefix + suffix)
        - "הר קדש" → "בהר קדשך" (prefix + suffix)

        Args:
            words: List of Hebrew words
            level: Normalization level

        Returns:
            Set of phrase variations with all prefix+suffix combinations
        """
        variations = set()

        if len(words) < 2:
            return variations

        # Generate all prefix variations for first word
        prefix_variants = {words[0]}  # Include original without prefix

        # Add common prefixes
        common_prepositions = list(self.PREPOSITIONS)[:5]  # Take first 5
        for prefix in [self.CONJUNCTION, self.DEFINITE_ARTICLE] + common_prepositions:
            prefix_variants.add(prefix + words[0])

        # Generate suffix variations for each word (except first)
        suffix_variants_by_word = []
        for i in range(1, len(words)):
            word_variants = {words[i]}  # Include original without suffix
            for suffix in list(self.PRONOMINAL_SUFFIXES)[:5]:  # Limit to most common
                word_variants.add(words[i] + suffix)
            suffix_variants_by_word.append(word_variants)

        # Generate ALL combinations
        for prefix_variant in prefix_variants:
            # Start with just the prefix variant on first word
            base_phrase = [prefix_variant] + words[1:]
            variations.add(' '.join(base_phrase))

            # Now add suffix combinations for each position
            for i in range(1, len(words)):
                for suffix_variant in suffix_variants_by_word[i-1]:  # i-1 because suffix_variants_by_word excludes first word
                    combo_words = [prefix_variant] + words[1:i] + [suffix_variant] + words[i+1:]
                    variations.add(' '.join(combo_words))

        # Special case: Generate the most common combination (conjunction + suffix)
        # This handles cases like "ודבר אמת בלבבו"
        conjunction_variant = self.CONJUNCTION + words[0]
        for i in range(1, len(words)):
            for suffix in list(self.PRONOMINAL_SUFFIXES)[:3]:  # Most common suffixes
                combo_words = [conjunction_variant] + words[1:i] + [words[i] + suffix] + words[i+1:]
                variations.add(' '.join(combo_words))

        return variations

    def _generate_limited_variations(self, phrase: str, level: str) -> List[str]:
        """
        Generate limited variations for alternate queries (basic prefixes only).

        This prevents query explosion by only generating the most common
        prefix variations for alternate phrases, not the full set of
        combinations that we generate for the main exact phrase.

        Args:
            phrase: Hebrew phrase to generate variations for
            level: Normalization level

        Returns:
            List of phrase variations (limited set)
        """
        words = split_words(phrase)
        variations = {phrase}

        if not words:
            return [normalize_for_search(phrase, level)] if phrase else []

        # Only add single prefixes to first word (no combinations)
        for prefix in ['ה', 'ו', 'ב', 'ל', 'מ']:  # 5 most common
            var_words = [prefix + words[0]] + words[1:]
            variations.add(' '.join(var_words))

        # Normalize and return limited set
        normalized = []
        for var in variations:
            norm = normalize_for_search(var, level)
            if norm:  # Only add non-empty
                normalized.append(norm)

        return sorted(normalized)

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
            ...     scope="Tanakh",  # Always searches full Tanakh first
            ...     level="consonantal",
            ...     include_variations=True,
            ...     auto_scope_threshold=30  # Filter if >30 results
            ... )
            >>> bundle = librarian.search_with_variations(req)
            >>> print(f"Found {len(bundle.results)} results")
            >>> print(f"Searched {len(bundle.variations_searched)} variations")

        Search Behavior:
            1. Always searches full Tanakh first to get accurate result counts
            2. If results > auto_scope_threshold, applies intelligent filtering
               prioritizing key books (Torah, Psalms, Prophets, etc.)
            3. If explicit scope requested (not 'auto'), filters to that scope
               after counting all results
        """
        all_results = []
        variations_searched = []
        original_query = request.query

        # Determine if this is a phrase or single word
        words = split_words(original_query)
        is_phrase = len(words) > 1

        # ALWAYS search full Tanakh first for ALL queries
        # This ensures we get accurate counts before any filtering
        initial_scope = 'Tanakh'
        use_post_search_filtering = True

        # Store original requested scope for later filtering
        original_requested_scope = request.scope
        is_explicit_scope = request.scope != 'auto'

        if self.logger:
            self.logger.info(f"Searching '{original_query}' in full Tanakh first (will filter after if needed)")
            self.logger.info(f"Query type: {'phrase' if is_phrase else 'single word'}")
            if is_explicit_scope:
                self.logger.info(f"Will filter to requested scope: '{original_requested_scope}'")

        # ENSURE SOURCE PSALM INCLUSION
        # If source_psalm is specified and scope might exclude Psalms, add it
        if request.source_psalm and 'Psalms' not in initial_scope and initial_scope != 'Tanakh':
            if ',' in initial_scope:
                initial_scope += ',Psalms'
            else:
                initial_scope = f"{initial_scope},Psalms"
            if self.logger:
                self.logger.info(f"Added Psalms to scope to ensure source psalm {request.source_psalm} is included")

        # CRITICAL FIX: Only generate variations for single words, NOT phrases
        if request.include_variations:
            if is_phrase:
                # For phrases, only search the exact phrase (no variations)
                queries = [original_query]
                if self.logger:
                    self.logger.info(f"Phrase search: only searching exact phrase '{original_query}' (no variations)")
            else:
                # For single words, generate variations as before
                queries = self.generate_phrase_variations(original_query, request.level)
                if self.logger:
                    self.logger.info(f"Generated {len(queries)} variations for word '{original_query}'")
        else:
            queries = [original_query]

        # Add alternate queries
        if request.alternate_queries:
            # CRITICAL FIX: Limit number of alternates to prevent explosion
            max_alternates = 10  # Reasonable limit
            if len(request.alternate_queries) > max_alternates:
                if self.logger:
                    self.logger.warning(f"Limiting alternates to {max_alternates} (was {len(request.alternate_queries)})")
                limited_alternates = request.alternate_queries[:max_alternates]
            else:
                limited_alternates = request.alternate_queries

            if self.logger:
                self.logger.info(f"Processing {len(limited_alternates)} alternate queries")

            for alt_query in limited_alternates:
                # Check if alternate is a phrase
                alt_words = split_words(alt_query)
                alt_is_phrase = len(alt_words) > 1

                if request.include_variations and not alt_is_phrase:
                    # For single words, generate variations
                    alt_variations = self._generate_limited_variations(alt_query, request.level)
                    if self.logger:
                        self.logger.info(f"Generated {len(alt_variations)} variations for word alternate '{alt_query}'")
                    queries.extend(alt_variations)
                else:
                    # For phrases, no variations
                    if alt_is_phrase and self.logger:
                        self.logger.info(f"Phrase alternate: using exact form '{alt_query}' (no variations)")
                    queries.append(alt_query)

        # Log total queries to be searched
        if self.logger:
            total_queries = len(queries)
            if total_queries > 5000:  # Warning threshold
                self.logger.warning(f"Generated {total_queries} total queries (may cause performance issues)")
            else:
                self.logger.info(f"Total queries to search: {total_queries}")

        # Search each variation
        seen_verses = set()  # Deduplicate: (book, chapter, verse)
        phrase_results_count = 0
        total_variations = len(queries)

        for i, query in enumerate(queries, 1):
            variations_searched.append(query)

            # Log progress at intervals
            if self.logger and (i == 1 or i % 500 == 0 or i == total_variations):
                self.logger.info(f"Searching variation {i}/{total_variations}: '{query[:30]}{'...' if len(query) > 30 else ''}'")

            if is_phrase:
                # Phrase search - try strict matching first
                results = self.search.search_phrase(
                    phrase=query,
                    level=request.level,
                    scope=initial_scope,
                    use_split=True  # Use maqqef-split column for better phrase matching
                )
            else:
                # Word search
                results = self.search.search_word(
                    word=query,
                    level=request.level,
                    scope=initial_scope,
                    use_split=True  # Use maqqef-split column for better word matching
                )

            # Log result count for first few and last variation
            if self.logger and (i <= 5 or i == total_variations):
                self.logger.info(f"  Found {len(results)} results")

            # Add results, deduplicating by verse reference
            for result in results[:request.max_results]:
                verse_key = (result.book, result.chapter, result.verse)
                if verse_key not in seen_verses:
                    seen_verses.add(verse_key)
                    all_results.append(result)

            # Count phrase results (only for the main query, not variations)
            if query == original_query or query == queries[0]:  # First variation is usually the original
                phrase_results_count = len(results)

        # POST-SEARCH FILTERING FOR COMMON PHRASES AND WORDS
        # If we found too many results, apply intelligent filtering
        # This applies to ALL searches now since we always search full Tanakh first
        if use_post_search_filtering and phrase_results_count > request.auto_scope_threshold:
            if self.logger:
                search_type = "Phrase" if is_phrase else "Word"
                self.logger.info(f"{search_type} '{original_query}' found {phrase_results_count} results (threshold: {request.auto_scope_threshold})")
                self.logger.info("Applying intelligent filtering to prioritize key books")

            # Priority book ordering for common phrases
            priority_books = [
                # Torah (Foundational books)
                'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
                # Psalms and Wisdom (Primary poetic/theological books)
                'Psalms', 'Proverbs', 'Job',
                # Major Prophets
                'Isaiah', 'Jeremiah', 'Ezekiel',
                # Historical books
                'Joshua', 'Judges', '1 Samuel', '2 Samuel', '1 Kings', '2 Kings',
                # Minor Prophets (key themes)
                'Hosea', 'Joel', 'Amos', 'Jonah', 'Micah',
                # Other Writings
                'Song of Songs', 'Ruth', 'Lamentations', 'Ecclesiastes', 'Esther', 'Daniel',
                # Post-exilic
                'Ezra', 'Nehemiah', '1 Chronicles', '2 Chronicles',
                # Remaining Minor Prophets
                'Obadiah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi'
            ]

            # Filter results maintaining priority order
            filtered_results = []
            seen_priority_books = set()

            # First pass: get results from priority books in order
            for result in all_results:
                if result.book in priority_books and len(filtered_results) < request.max_results:
                    filtered_results.append(result)
                    seen_priority_books.add(result.book)

            # Second pass: if still under max_results, add from remaining books
            for result in all_results:
                if len(filtered_results) >= request.max_results:
                    break
                if result.book not in seen_priority_books:
                    filtered_results.append(result)

            all_results = filtered_results
            if self.logger:
                self.logger.info(f"Filtered to {len(all_results)} results using priority book ordering")

        # APPLY EXPLICIT SCOPE FILTERING (if requested)
        # If user requested a specific scope (not 'auto'), filter to that scope
        if is_explicit_scope and original_requested_scope != 'Tanakh':
            if self.logger:
                self.logger.info(f"Filtering {len(all_results)} results to requested scope: '{original_requested_scope}'")

            scope_filtered_results = []
            # Use the search class's scope filtering logic
            for result in all_results:
                if self._book_in_scope(result.book, original_requested_scope):
                    scope_filtered_results.append(result)

            all_results = scope_filtered_results
            if self.logger:
                self.logger.info(f"Scope filtering resulted in {len(all_results)} results")

        # FALLBACK: If strict phrase matching found nothing, try "same verse" search
        # This finds verses where all words appear (any order, not necessarily adjacent)
        if not all_results and is_phrase:
            if self.logger:
                self.logger.info(f"Strict phrase matching failed for '{original_query}', trying 'same verse' search")
            fallback_results = self.search.search_phrase_in_verse(
                phrase=original_query,
                level=request.level,
                scope=initial_scope,
                limit=request.max_results,
                use_split=True
            )
            for result in fallback_results:
                verse_key = (result.book, result.chapter, result.verse)
                if verse_key not in seen_verses:
                    seen_verses.add(verse_key)
                    all_results.append(result)

        # CRITICAL FIX: Final validation to ensure all phrase results contain ALL words
        # This is a safety net to prevent partial matches from getting through
        if is_phrase and all_results:
            # Get normalized words from original query
            original_words = split_words(original_query)
            if request.level == 'consonantal':
                normalized_words = normalize_word_sequence(original_words, request.level)
            else:
                normalized_words = original_words

            validated_results = []
            for result in all_results:
                # Check if this verse contains ALL the words from the original phrase
                if self.search._verse_contains_all_words(
                    result.book, result.chapter, result.verse,
                    normalized_words,
                    'word_consonantal_split' if request.level == 'consonantal' and True else 'word_consonantal'
                ):
                    validated_results.append(result)
                elif self.logger:
                    self.logger.debug(
                        f"Filtered out result {result.reference}: missing words from phrase '{original_query}'"
                    )

            all_results = validated_results
            if self.logger and len(all_results) < len(all_results) + 0:  # Count was incorrect
                self.logger.info(
                    f"Final validation filtered results to ensure all words are present"
                )

        # Log final results
        if self.logger:
            self.logger.info(f"Search completed: {total_variations} queries, {len(all_results)} total unique results")

        return ConcordanceBundle(
            results=all_results,
            variations_searched=variations_searched,
            request=request
        )

    def _book_in_scope(self, book: str, scope: str) -> bool:
        """
        Check if a book is within the specified scope.

        Args:
            book: Book name (e.g., 'Genesis', 'Psalms')
            scope: Scope string (e.g., 'Torah', 'Psalms,Proverbs', 'Tanakh')

        Returns:
            True if book is in scope
        """
        if scope == 'Tanakh':
            return True

        # Check category scopes
        if scope == 'Torah':
            return book in ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']
        elif scope == 'Prophets':
            from ..data_sources.tanakh_database import TANAKH_BOOKS
            return book in [b[0] for b in TANAKH_BOOKS['Prophets']]
        elif scope == 'Writings':
            from ..data_sources.tanakh_database import TANAKH_BOOKS
            return book in [b[0] for b in TANAKH_BOOKS['Writings']]

        # Check comma-separated book list
        if ',' in scope:
            scope_books = [b.strip() for b in scope.split(',')]
            return book in scope_books

        # Check single book
        return book == scope

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
