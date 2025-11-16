"""
Hebrew Word Classifier for Pattern Quality Analysis

Classifies Hebrew words into linguistic categories to identify
content-bearing words vs. formulaic/function words.

Categories:
- Divine names: יהוה, אלהים, אל, etc.
- Function words: prepositions, conjunctions, particles
- Liturgical: psalm titles, musical terms, etc.
- Content words: verbs, nouns, adjectives (everything else)
"""

from typing import Set, Dict, Tuple


class HebrewWordClassifier:
    """Classifies Hebrew words into linguistic categories."""

    def __init__(self):
        """Initialize word lists for classification."""

        # Divine names and epithets
        self.divine_names: Set[str] = {
            'יהוה', 'יהו', 'יה',  # YHWH variations
            'אלהים', 'אלה', 'אלהי', 'אלהיך', 'אלהינו',  # Elohim variations
            'אל',  # El
            'אדני', 'אדן',  # Adonai
            'שדי',  # Shaddai
            'עליון',  # Elyon
            'צבאות',  # Tzvaot (in YHWH Tzvaot)
        }

        # Prepositions (often appear with prefixes)
        self.prepositions: Set[str] = {
            'ב', 'בי', 'בו', 'בך', 'בכם', 'בנו', 'בה', 'בהם', 'בכן',
            'ל', 'לי', 'לו', 'לך', 'לכם', 'לנו', 'לה', 'להם', 'לכן',
            'מ', 'מן', 'מני', 'ממני', 'ממך', 'ממנו', 'ממנה', 'ממכם', 'מהם',
            'על', 'עלי', 'עליך', 'עליו', 'עליה', 'עלינו', 'עליכם', 'עליהם',
            'אל', 'אלי', 'אליך', 'אליו', 'אליה', 'אלינו', 'אליכם', 'אליהם',
            'את', 'אתי', 'אתך', 'אתו', 'אתה', 'אתכם', 'אתנו', 'אתם', 'אתן',
            'עם', 'עמי', 'עמך', 'עמו', 'עמה', 'עמנו', 'עמכם', 'עמהם',
            'כ', 'כי', 'כו', 'כך', 'כה', 'כם', 'כן', 'כהם',
            'ככה', 'כזה', 'כזאת',
            'תחת', 'אחר', 'אחרי', 'לפני', 'מפני', 'בין',
        }

        # Conjunctions and particles
        self.conjunctions: Set[str] = {
            'כי', 'אם', 'אשר', 'ש',  # Common conjunctions
            'ו', 'וה',  # Conjunction vav
            'או', 'ואם', 'כאשר', 'לכן', 'למען',
            'פן', 'הן', 'הנה',
        }

        # Negations and determiners
        self.particles: Set[str] = {
            'לא', 'אל', 'בל', 'אין',  # Negations
            'כל', 'כול',  # All
            'גם', 'אף', 'רק',  # Also, even, only
            'הן', 'הנה', 'נה',  # Behold
            'מה', 'מי', 'איה', 'אנה',  # Question words
            'ה',  # Definite article
        }

        # Liturgical and musical terms (psalm-specific)
        self.liturgical: Set[str] = {
            'מזמור', 'זמור', 'מזמ',  # Psalm
            'שיר',  # Song
            'תפלה', 'תפל',  # Prayer
            'הללויה', 'הלל',  # Hallelujah
            'סלה',  # Selah
            'למנצח', 'נצח', 'מנצח',  # For the director
            'דוד',  # David (in titles)
            'אסף',  # Asaph (in titles)
            'קרח',  # Korah (in titles)
            'בני',  # Sons of (in titles like "Sons of Korah")
            'משכיל',  # Maskil
            'מכתם',  # Michtam
            'שגיון',  # Shiggaion
        }

        # Common pronominal suffixes and pronouns
        self.pronouns: Set[str] = {
            'אני', 'אנכי', 'אנחנו',  # I, we
            'אתה', 'את', 'אתם', 'אתן',  # You (m/f, s/p)
            'הוא', 'היא', 'הם', 'הן', 'המה',  # He, she, they
            'זה', 'זאת', 'אלה', 'זו',  # This, these
        }

        # Combine all function word categories
        self.function_words: Set[str] = (
            self.prepositions | self.conjunctions |
            self.particles | self.pronouns
        )

        # Cache for classification results
        self._cache: Dict[str, str] = {}

    def classify(self, word: str) -> str:
        """
        Classify a Hebrew word into a category.

        Args:
            word: Hebrew word to classify

        Returns:
            Category: 'divine', 'function', 'liturgical', or 'content'
        """
        # Check cache
        if word in self._cache:
            return self._cache[word]

        # Normalize word (remove common prefixes for checking)
        normalized = word.strip()

        # Check categories in priority order
        if normalized in self.divine_names:
            category = 'divine'
        elif normalized in self.liturgical:
            category = 'liturgical'
        elif normalized in self.function_words:
            category = 'function'
        elif len(normalized) < 2:
            # Very short words (1 char) are usually prefixes/function
            category = 'function'
        else:
            # Everything else is considered content
            category = 'content'

        # Cache result
        self._cache[word] = category
        return category

    def analyze_pattern(self, words: list) -> Dict[str, any]:
        """
        Analyze a pattern (list of words) for content richness.

        Args:
            words: List of Hebrew words in the pattern

        Returns:
            Dictionary with analysis:
            - total_words: int
            - content_word_count: int
            - divine_count: int
            - function_count: int
            - liturgical_count: int
            - content_words: List[str]
            - content_word_ratio: float
            - category: str (overall classification)
        """
        total = len(words)
        counts = {
            'divine': 0,
            'function': 0,
            'liturgical': 0,
            'content': 0
        }
        content_words = []

        for word in words:
            category = self.classify(word)
            counts[category] += 1
            if category == 'content':
                content_words.append(word)

        content_ratio = counts['content'] / total if total > 0 else 0

        # Determine overall category
        if counts['content'] >= 2:
            overall = 'interesting_multi_content'
        elif counts['content'] == 1 and counts['divine'] == 0:
            overall = 'interesting_content_focused'
        elif counts['content'] == 1:
            overall = 'borderline'
        elif counts['liturgical'] > 0:
            overall = 'formulaic_liturgical'
        elif counts['divine'] > 0:
            overall = 'formulaic_divine'
        else:
            overall = 'formulaic_function'

        return {
            'total_words': total,
            'content_word_count': counts['content'],
            'divine_count': counts['divine'],
            'function_count': counts['function'],
            'liturgical_count': counts['liturgical'],
            'content_words': content_words,
            'content_word_ratio': content_ratio,
            'category': overall
        }

    def should_keep_pattern(self, words: list, min_content_words: int = 1) -> Tuple[bool, str]:
        """
        Determine if a pattern should be kept based on content word threshold.

        Args:
            words: List of Hebrew words in the pattern
            min_content_words: Minimum number of content words required

        Returns:
            Tuple of (should_keep: bool, reason: str)
        """
        analysis = self.analyze_pattern(words)
        content_count = analysis['content_word_count']

        if content_count >= min_content_words:
            return True, f"Has {content_count} content words (>= {min_content_words})"
        else:
            category = analysis['category']
            return False, f"Only {content_count} content words (category: {category})"


# Singleton instance for easy import
classifier = HebrewWordClassifier()


def classify_word(word: str) -> str:
    """Convenience function to classify a single word."""
    return classifier.classify(word)


def analyze_pattern(words: list) -> Dict[str, any]:
    """Convenience function to analyze a pattern."""
    return classifier.analyze_pattern(words)


def should_keep_pattern(words: list, min_content_words: int = 1) -> Tuple[bool, str]:
    """Convenience function to check if pattern should be kept."""
    return classifier.should_keep_pattern(words, min_content_words)


if __name__ == "__main__":
    # Test the classifier
    print("Testing Hebrew Word Classifier\n")

    # Test individual words
    test_words = [
        ('יהוה', 'divine'),
        ('אלהים', 'divine'),
        ('כי', 'function'),
        ('את', 'function'),
        ('מזמור', 'liturgical'),
        ('דוד', 'liturgical'),
        ('ראה', 'content'),
        ('עני', 'content'),
        ('ברך', 'content'),
    ]

    print("Individual word classification:")
    for word, expected in test_words:
        result = classify_word(word)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {word}: {result} (expected: {expected})")

    # Test patterns
    print("\nPattern analysis:")

    test_patterns = [
        (['יהוה', 'אל'], 'formulaic_divine', "יהוה אל - pure divine names"),
        (['כי', 'את'], 'formulaic_function', "כי את - pure function words"),
        (['מזמור', 'דוד'], 'formulaic_liturgical', "מזמור דוד - liturgical"),
        (['ברך', 'יהוה'], 'borderline', "ברך יהוה - 1 content + divine"),
        (['ראה', 'עני'], 'interesting_multi_content', "ראה עני - 2 content words"),
        (['לא', 'ידע'], 'interesting_multi_content', "לא ידע - content despite function word"),
    ]

    for words, expected_cat, description in test_patterns:
        analysis = analyze_pattern(words)
        status = "✓" if analysis['category'] == expected_cat else "✗"
        print(f"  {status} {description}")
        print(f"      Pattern: {' '.join(words)}")
        print(f"      Content words: {analysis['content_word_count']}")
        print(f"      Category: {analysis['category']}")
        print(f"      Should keep (min=1): {should_keep_pattern(words, 1)[0]}")
        print(f"      Should keep (min=2): {should_keep_pattern(words, 2)[0]}")
        print()
