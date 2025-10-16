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

from typing import List, Set
from dataclasses import dataclass
from enum import Enum


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

    Future Enhancement:
    - Integrate OSHB morphhb database for complete coverage
    - Add root-specific patterns (hollow, geminate, etc.)
    - Add proper vowel insertion/deletion rules
    """

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

    def generate_variations(self,
                          root: str,
                          include_gender: bool = True,
                          include_number: bool = True,
                          include_verb_forms: bool = True) -> List[str]:
        """
        Generate morphological variations of a Hebrew root.

        Args:
            root: Hebrew root (consonantal, 2-4 letters typically)
            include_gender: Generate gender variations
            include_number: Generate number variations
            include_verb_forms: Generate verb tense/stem variations

        Returns:
            List of possible word forms

        Example:
            >>> gen = MorphologyVariationGenerator()
            >>> variations = gen.generate_variations("שמר")
            >>> len(variations)
            50+  # Many variations generated
        """
        variations = {root}  # Always include the base form

        if include_gender and include_number:
            variations.update(self._generate_noun_variations(root))

        if include_verb_forms:
            variations.update(self._generate_verb_variations(root))

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

        Args:
            root: Consonantal root (typically 3 letters)

        Returns:
            Set of verb form variations
        """
        variations = set()

        # Generate stem variations with prefixes
        for stem, prefixes in self.STEM_PREFIXES.items():
            for prefix in prefixes:
                variations.add(prefix + root)

        # Generate imperfect forms (prefix + root)
        for person, prefix in self.IMPERFECT_PREFIXES.items():
            variations.add(prefix + root)

            # Also with stem prefixes
            for stem, stem_prefixes in self.STEM_PREFIXES.items():
                for stem_prefix in stem_prefixes:
                    if stem_prefix:  # Skip empty prefix for Qal
                        variations.add(prefix + stem_prefix + root)

        # Add participle patterns
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
