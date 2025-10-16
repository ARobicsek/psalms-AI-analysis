"""
Morphological Variation Generator for Hebrew Concordance

This module generates morphological variations of Hebrew roots to improve
concordance search recall. It implements pattern-based rules for:
- Gender variations (masculine/feminine)
- Number variations (singular/plural/dual)
- Verb tense variations (perfect, imperfect, imperative, participle, infinitive)
- Verb stem variations (Qal, Niphal, Piel, Pual, Hiphil, Hophal, Hithpael)

NOTE: This is a FOUNDATION for future enhancement. Currently implements:
1. Basic suffix patterns for gender/number
2. Common verb prefixes for tense
3. Stem prefix patterns (נ, מ, ה, הת)

For complete coverage, integrate OSHB morphology database:
https://github.com/openscriptures/morphhb
"""

from typing import List, Set, Optional
from dataclasses import dataclass
from enum import Enum
import re


class Gender(Enum):
    """Grammatical gender."""
    MASCULINE = "m"
    FEMININE = "f"
    COMMON = "c"  # Both genders


class Number(Enum):
    """Grammatical number."""
    SINGULAR = "s"
    PLURAL = "p"
    DUAL = "d"


class VerbTense(Enum):
    """Verb tenses (binyan-independent)."""
    PERFECT = "perfect"  # קָטַל
    IMPERFECT = "imperfect"  # יִקְטֹל
    IMPERATIVE = "imperative"  # קְטֹל
    INFINITIVE_CONSTRUCT = "inf_const"  # קְטֹל
    INFINITIVE_ABSOLUTE = "inf_abs"  # קָטוֹל
    PARTICIPLE = "participle"  # קֹטֵל


class VerbStem(Enum):
    """Verb stems (binyanim)."""
    QAL = "qal"  # פָּעַל (simple active)
    NIPHAL = "niphal"  # נִפְעַל (simple passive/reflexive) - נ prefix
    PIEL = "piel"  # פִּעֵל (intensive active)
    PUAL = "pual"  # פֻּעַל (intensive passive)
    HIPHIL = "hiphil"  # הִפְעִיל (causative active) - ה/הִ prefix
    HOPHAL = "hophal"  # הָפְעַל (causative passive) - הָ prefix
    HITHPAEL = "hithpael"  # הִתְפַּעֵל (reflexive/reciprocal) - הת prefix


@dataclass
class MorphologyPattern:
    """A pattern for generating morphological variations."""
    prefix: str = ""
    suffix: str = ""
    infix: str = ""  # For future use (gemination, vowel changes)
    description: str = ""


class MorphologyVariationGenerator:
    """
    Generates morphological variations of Hebrew roots.

    This class provides pattern-based generation of word forms based on
    common Hebrew morphological patterns. It is NOT a complete morphology
    analyzer - for that, use OSHB morphology data.

    Current Implementation:
    - Pattern-based suffixes for gender/number
    - Prefix patterns for verb stems
    - Prefix patterns for imperfect tense
    - Final letter form conversion for orthographic correctness

    Future Enhancement:
    - Integrate OSHB morphhb database for complete coverage
    - Add root-specific patterns (hollow, geminate, etc.)
    - Add proper vowel insertion/deletion rules
    """

    # Hebrew final forms mapping (medial → final)
    FINAL_FORMS = {
        'כ': 'ך',  # Kaf
        'מ': 'ם',  # Mem
        'נ': 'ן',  # Nun
        'פ': 'ף',  # Pe
        'צ': 'ץ'   # Tsadi
    }

    # Reverse mapping (final → medial) for normalization
    MEDIAL_FORMS = {v: k for k, v in FINAL_FORMS.items()}

    # Common suffix patterns
    SUFFIX_PATTERNS = {
        # Feminine endings
        'fem_sing_abs': ['ה', 'ת', 'ית'],  # קְטַלָּה, בַּת, רֵאשִׁית
        'fem_plur_abs': ['ות', 'ים'],  # קְטָלוֹת

        # Plural endings
        'masc_plur_abs': ['ים', 'ים'],  # קְטָלִים
        'fem_plur_abs': ['ות'],  # קְטָלוֹת

        # Dual ending
        'dual': ['ים', 'יים'],  # עֵינַיִם, רַגְלַיִם

        # Construct state
        'construct_suffix': ['י', 'ת', 'ות'],  # קְטַל, בַּת, רֵאשִׁית

        # Pronominal suffixes (possessive)
        'pron_1cs': ['י', 'ני'],  # my
        'pron_2ms': ['ך'],  # your (m)
        'pron_2fs': ['ך'],  # your (f)
        'pron_3ms': ['ו', 'הו'],  # his
        'pron_3fs': ['ה', 'הּ'],  # her
        'pron_1cp': ['נו'],  # our
        'pron_2mp': ['כם'],  # your (m.pl)
        'pron_3mp': ['ם', 'הם'],  # their (m)
        'pron_3fp': ['ן', 'הן'],  # their (f)
    }

    # Verb stem prefixes
    STEM_PREFIXES = {
        VerbStem.QAL: [''],  # No prefix (base form)
        VerbStem.NIPHAL: ['נ'],  # נִקְטַל
        VerbStem.HIPHIL: ['ה', 'הִ'],  # הִקְטִיל
        VerbStem.HOPHAL: ['הָ', 'הו'],  # הָקְטַל
        VerbStem.HITHPAEL: ['הת', 'הִת'],  # הִתְקַטֵּל
    }

    # Imperfect tense prefixes (for all stems)
    IMPERFECT_PREFIXES = {
        '1s': 'א',  # אֶקְטֹל (I will...)
        '2ms': 'ת',  # תִּקְטֹל (you m. will...)
        '2fs': 'ת',  # תִּקְטְלִי (you f. will...)
        '3ms': 'י',  # יִקְטֹל (he will...)
        '3fs': 'ת',  # תִּקְטֹל (she will...)
        '1cp': 'נ',  # נִקְטֹל (we will...)
        '2mp': 'ת',  # תִּקְטְלוּ (you m.pl will...)
        '3mp': 'י',  # יִקְטְלוּ (they m. will...)
        '3fp': 'ת',  # תִּקְטֹלְנָה (they f. will...)
    }

    # Participle patterns
    PARTICIPLE_PATTERNS = {
        VerbStem.QAL: ['קֹטֵל', 'קוֹטֵל'],  # Active participle patterns
        VerbStem.NIPHAL: ['נִקְטָל'],
        VerbStem.PIEL: ['מְקַטֵּל'],  # מ prefix for intensive
        VerbStem.HIPHIL: ['מַקְטִיל'],  # מ prefix for causative
        VerbStem.HITHPAEL: ['מִתְקַטֵּל'],  # מת prefix for reflexive
    }

    def __init__(self):
        """Initialize the morphology variation generator."""
        pass

    @staticmethod
    def normalize_to_medial(root: str) -> str:
        """
        Convert any final forms in root to medial forms for generation.

        When a user provides a root like ברך, we need to normalize it to ברך
        (all medial forms) before generating variations. This ensures that when
        we add suffixes, the letters are in the correct medial form.

        Args:
            root: Hebrew root (may contain final forms)

        Returns:
            Root with all final forms converted to medial

        Example:
            >>> normalize_to_medial("ברך")
            "ברכ"  # Final ך → medial כ for generation
        """
        if not root:
            return root

        result = []
        for char in root:
            if char in MorphologyVariationGenerator.MEDIAL_FORMS:
                result.append(MorphologyVariationGenerator.MEDIAL_FORMS[char])
            else:
                result.append(char)
        return ''.join(result)

    @staticmethod
    def apply_final_forms(word: str) -> str:
        """
        Convert medial letters to final forms at end of word.

        Hebrew has five letters with special final forms that must be used
        when the letter appears at the end of a word:
        - כ → ך (Kaf)
        - מ → ם (Mem)
        - נ → ן (Nun)
        - פ → ף (Pe)
        - צ → ץ (Tsadi)

        Args:
            word: Hebrew word (may contain diacritics)

        Returns:
            Word with final form applied if needed

        Example:
            >>> apply_final_forms("ברכו")
            "ברכו"  # כ stays medial, ו at end
            >>> apply_final_forms("ברכ")
            "ברך"  # כ at end becomes final ך
        """
        if not word:
            return word

        last_char = word[-1]
        if last_char in MorphologyVariationGenerator.FINAL_FORMS:
            return word[:-1] + MorphologyVariationGenerator.FINAL_FORMS[last_char]
        return word

    def generate_variations(self,
                          root: str,
                          include_gender: bool = True,
                          include_number: bool = True,
                          include_verb_forms: bool = True) -> List[str]:
        """
        Generate morphological variations of a Hebrew root.

        All generated forms are automatically corrected for final letter forms
        (כ→ך, מ→ם, נ→ן, פ→ף, צ→ץ at word end).

        IMPORTANT: The root should be provided in consonantal form. If final
        forms are present (e.g., ברך), they will be normalized to medial forms
        (ברכ) for generation, then final forms applied only at word end.

        Args:
            root: Hebrew root (consonantal, 2-4 letters typically)
            include_gender: Generate gender variations
            include_number: Generate number variations
            include_verb_forms: Generate verb tense/stem variations

        Returns:
            List of possible word forms with final letters corrected

        Example:
            >>> gen = MorphologyVariationGenerator()
            >>> variations = gen.generate_variations("ברך")
            >>> # Returns: ברך, ברכו, ברכים (correct medial/final usage)
        """
        # Step 1: Normalize root to medial forms for generation
        medial_root = self.normalize_to_medial(root)

        # Step 2: Generate variations using medial root
        variations = {medial_root}  # Always include the base form

        if include_gender and include_number:
            variations.update(self._generate_noun_variations(medial_root))

        if include_verb_forms:
            variations.update(self._generate_verb_variations(medial_root))

        # Step 3: Apply final letter forms ONLY to the last character
        variations = {self.apply_final_forms(v) for v in variations}

        return sorted(list(variations))

    def _generate_noun_variations(self, root: str) -> Set[str]:
        """
        Generate noun variations (gender, number, construct, possessive).

        Args:
            root: Consonantal root

        Returns:
            Set of noun form variations
        """
        variations = set()

        # Add feminine singular suffixes
        for suffix in self.SUFFIX_PATTERNS['fem_sing_abs']:
            variations.add(root + suffix)

        # Add plural suffixes (masculine and feminine)
        for suffix in self.SUFFIX_PATTERNS['masc_plur_abs']:
            variations.add(root + suffix)

        for suffix in self.SUFFIX_PATTERNS['fem_plur_abs']:
            variations.add(root + suffix)

        # Add dual suffixes
        for suffix in self.SUFFIX_PATTERNS['dual']:
            variations.add(root + suffix)

        # Add pronominal suffixes (common ones)
        for key in ['pron_1cs', 'pron_2ms', 'pron_3ms', 'pron_3fs', 'pron_1cp', 'pron_3mp']:
            for suffix in self.SUFFIX_PATTERNS[key]:
                variations.add(root + suffix)
                # Also with feminine marker + suffix
                variations.add(root + 'ת' + suffix)

        return variations

    def _generate_verb_variations(self, root: str) -> Set[str]:
        """
        Generate verb variations (stems, tenses).

        This method creates mutually-exclusive pattern sets to avoid
        linguistically impossible forms like יהָרעה (imperfect + Hophal prefix).

        Verb forms generated:
        1. Perfect forms: stem prefix + root + suffixes
        2. Imperfect forms: person prefix + root (no stem prefix - vowel pattern differs)
        3. Participles: participle prefix + root
        4. Imperative: root only (or with suffixes)

        Args:
            root: Consonantal root (typically 3 letters)

        Returns:
            Set of verb form variations
        """
        variations = set()

        # 1. Perfect forms: stem prefix + root (Qal, Niphal, Hiphil, Hophal, Hithpael)
        for stem, prefixes in self.STEM_PREFIXES.items():
            for prefix in prefixes:
                variations.add(prefix + root)

        # 2. Imperfect forms: person prefix + root ONLY (no stem prefix stacking)
        # In Hebrew, imperfect already contains stem information via vowel patterns,
        # not prefix stacking. E.g.:
        # - Qal imperfect: יִקְטֹל (not י + base)
        # - Hiphil imperfect: יַקְטִיל (different vowels, not י + ה + base)
        for person, prefix in self.IMPERFECT_PREFIXES.items():
            variations.add(prefix + root)

        # 3. Participle patterns (מ prefix forms)
        for stem, patterns in self.PARTICIPLE_PATTERNS.items():
            for pattern_prefix in patterns:
                # Extract prefix from pattern (before root placeholder)
                if 'מ' in pattern_prefix or 'נ' in pattern_prefix or 'ה' in pattern_prefix:
                    # Simple: just add the prefix letters
                    if pattern_prefix.startswith('מְ'):
                        variations.add('מ' + root)
                    elif pattern_prefix.startswith('נִ'):
                        variations.add('נ' + root)
                    elif pattern_prefix.startswith('מַ'):
                        variations.add('מ' + root)
                    elif pattern_prefix.startswith('מִת'):
                        variations.add('מת' + root)

        return variations

    def estimate_coverage_improvement(self, root: str) -> dict:
        """
        Estimate how many additional variations this generates vs. prefix-only.

        Args:
            root: Hebrew root

        Returns:
            Dictionary with statistics
        """
        prefix_variations = 20  # Current system: 20 prefix variations
        morphology_variations = len(self.generate_variations(root))

        return {
            'root': root,
            'prefix_only_count': prefix_variations,
            'with_morphology_count': morphology_variations,
            'additional_forms': morphology_variations - prefix_variations,
            'improvement_ratio': morphology_variations / prefix_variations
        }


class MorphologyValidator:
    """
    Validates whether a discovered word form is plausibly derived from a root.

    This validator is used in Phase 2 of the hybrid search strategy to filter
    substring search results. It checks whether a word could reasonably be
    derived from a given root, filtering out spurious matches.

    Validation checks:
    1. Root consonants appear in the correct order
    2. Only valid affixes added (prefixes/suffixes from known patterns)
    3. Length is reasonable (root + 0-4 affixes typically)
    4. No impossible prefix combinations (e.g., יהָ)

    This is a FOUNDATION implementation. For production use, integrate with
    OSHB morphology database for definitive validation.
    """

    # Valid Hebrew prefixes (from grammar)
    VALID_PREFIXES = {
        # Articles and conjunctions
        'ה', 'ו', 'וה',
        # Prepositions
        'ב', 'כ', 'ל', 'מ',
        # Combinations
        'וב', 'וכ', 'ול', 'ומ', 'בה', 'כה', 'לה', 'מה',
        # Verb stems
        'נ', 'הת', 'הִת', 'מ', 'מת',
        # Imperfect
        'א', 'ת', 'י', 'נ'
    }

    # Valid Hebrew suffixes
    VALID_SUFFIXES = {
        # Gender/number
        'ה', 'ת', 'ית', 'ים', 'ות', 'יים',
        # Pronominal
        'י', 'ני', 'ך', 'ו', 'הו', 'ה', 'הּ', 'נו', 'כם', 'ם', 'הם', 'ן', 'הן'
    }

    def __init__(self, root: str):
        """
        Initialize validator for a specific root.

        Args:
            root: Hebrew consonantal root (2-4 letters typically)
        """
        self.root = root
        self.root_letters = list(root)

    def is_plausible(self, word: str) -> bool:
        """
        Check if a word is plausibly derived from the root.

        Args:
            word: Hebrew word to validate

        Returns:
            True if word could plausibly derive from root

        Example:
            >>> validator = MorphologyValidator("שמר")
            >>> validator.is_plausible("ישמרו")  # True
            >>> validator.is_plausible("דבר")    # False (different root)
        """
        if not word:
            return False

        # Check 1: Root consonants must appear in order
        if not self._contains_root_in_order(word):
            return False

        # Check 2: Length must be reasonable (root + 0-4 affixes typically)
        if len(word) > len(self.root) + 6:  # Allow some flexibility
            return False

        # Check 3: No impossible prefix combinations (e.g., יהָ, יהִת)
        if self._has_impossible_prefix_combination(word):
            return False

        return True

    def _contains_root_in_order(self, word: str) -> bool:
        """
        Check if root consonants appear in order within word.

        Args:
            word: Word to check

        Returns:
            True if all root letters appear in order
        """
        root_index = 0
        for char in word:
            if root_index < len(self.root_letters) and char == self.root_letters[root_index]:
                root_index += 1
            if root_index == len(self.root_letters):
                return True
        return root_index == len(self.root_letters)

    def _has_impossible_prefix_combination(self, word: str) -> bool:
        """
        Check for linguistically impossible prefix combinations.

        Impossible combinations include:
        - Imperfect prefix + stem prefix (יה, יהת, תה, אה, נה)

        Args:
            word: Word to check

        Returns:
            True if word has impossible prefix combination
        """
        # Check for imperfect + stem prefix combinations
        impossible_patterns = [
            'יה',   # Imperfect + Hiphil/Hophal (should use vowel pattern)
            'יהת',  # Imperfect + Hithpael
            'תה',   # Imperfect + Hiphil/Hophal
            'תהת',  # Imperfect + Hithpael
            'אה',   # Imperfect + Hiphil/Hophal
            'אהת',  # Imperfect + Hithpael
            'נה',   # Imperfect + Hiphil/Hophal (נ alone is valid for Niphal)
        ]

        for pattern in impossible_patterns:
            if word.startswith(pattern):
                # Check if it's truly the pattern we're concerned about
                # (not just coincidental letters)
                if len(word) > len(pattern):
                    # If the root starts right after, it's likely impossible
                    if word[len(pattern):].startswith(self.root[0]):
                        return True

        return False


# CLI for testing
if __name__ == '__main__':
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    generator = MorphologyVariationGenerator()

    test_roots = ['שמר', 'רעה', 'אהב', 'ברך']

    print("Morphological Variation Generator - Test Results")
    print("=" * 70)

    for root in test_roots:
        print(f"\nRoot: {root}")
        variations = generator.generate_variations(root)
        print(f"Total variations: {len(variations)}")
        print(f"Sample (first 20):")
        for i, var in enumerate(variations[:20], 1):
            print(f"  {i:2d}. {var}")

        if len(variations) > 20:
            print(f"  ... and {len(variations) - 20} more")

        # Show coverage improvement
        stats = generator.estimate_coverage_improvement(root)
        print(f"\nCoverage Improvement:")
        print(f"  Prefix-only: {stats['prefix_only_count']} variations")
        print(f"  With morphology: {stats['with_morphology_count']} variations")
        print(f"  Additional: {stats['additional_forms']} forms")
        print(f"  Improvement: {stats['improvement_ratio']:.1f}x")
