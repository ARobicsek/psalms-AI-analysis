"""
Hebrew Morphological Analysis

Provides accurate root extraction for Biblical Hebrew using cached morphological
data from ETCBC Text-Fabric, with fallback to improved naive extraction.

Usage:
    from src.hebrew_analysis.morphology import extract_morphological_root
    
    root = extract_morphological_root("מָחִיתָ")
    # Returns: "מחה" (correct root)
"""

import re
import json
from pathlib import Path
from typing import Dict, Optional, Set
import logging

logger = logging.getLogger(__name__)

# Add parent path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from concordance.hebrew_text_processor import strip_consonantal
except ImportError:
    # Fallback implementation
    def strip_consonantal(text: str) -> str:
        """Strip Hebrew diacritics to get consonantal form."""
        import unicodedata
        # Remove combining characters (nikud, teamim)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        # Remove specific Hebrew marks
        marks_to_remove = '\u05B0-\u05BD\u05BF-\u05C7'
        text = re.sub(f'[{marks_to_remove}]', '', text)
        return text.strip()


class HebrewMorphologyAnalyzer:
    """
    Biblical Hebrew morphological analyzer using cached ETCBC data.
    
    This analyzer uses a pre-built cache of morphological data from the
    ETCBC Text-Fabric Biblical Hebrew dataset, providing fast and accurate
    root extraction for Biblical Hebrew words.
    
    For words not in cache, falls back to improved naive extraction.
    """
    
    # Common Hebrew function words (single letters) - don't strip to these
    FUNCTION_WORDS: Set[str] = {'ב', 'ל', 'כ', 'מ', 'ו', 'ה', 'ש', 'א', 'י', 'ת', 'נ'}
    
    # Common prefixes to try stripping (ordered by length, longest first)
    COMMON_PREFIXES = [
        'וה',   # conjunction + article
        'וב',   # conjunction + preposition
        'וכ',   # conjunction + preposition
        'ול',   # conjunction + preposition
        'ומ',   # conjunction + preposition
        'ה',    # definite article
        'ו',    # conjunction (and)
        'ב',    # preposition (in, with)
        'כ',    # preposition (like, as)
        'ל',    # preposition (to, for)
        'מ',    # preposition (from)
        'ש',    # relative pronoun (that, which)
    ]
    
    # Common suffixes to try stripping (ordered by length, longest first)
    COMMON_SUFFIXES = [
        'הם',   # their (m.)
        'הן',   # their (f.)
        'כם',   # your (m.p.)
        'כן',   # your (f.p.)
        'ים',   # plural (m.)
        'ות',   # plural (f.)
        'נו',   # our
        'יו',   # his (archaic/poetic)
        'יך',   # your (poetic)
        'ני',   # me (object suffix)
        'תי',   # I (perfect verb)
        'נה',   # we/they (imperfect verb)
        'ית',   # feminine ending
        'י',    # my
        'ך',    # your (m.s./f.s.)
        'ו',    # his
        'ה',    # her
        'ת',    # you/feminine marker
    ]
    
    def __init__(self, cache_path: Optional[Path] = None):
        """
        Initialize morphology analyzer.
        
        Args:
            cache_path: Path to morphology cache JSON file.
                       If None, looks for default location.
        """
        self.cache: Dict[str, str] = {}
        self.cache_loaded = False
        
        if cache_path is None:
            # Default cache location
            cache_path = Path(__file__).parent / 'data' / 'psalms_morphology_cache.json'
        
        self.cache_path = cache_path
        
        # Try to load cache
        self._load_cache()
    
    def _load_cache(self):
        """Load morphology cache from JSON file."""
        if not self.cache_path.exists():
            logger.warning(f"Morphology cache not found at {self.cache_path}")
            logger.warning("Will use fallback extraction only. Run build_psalms_cache() to create cache.")
            return
        
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.cache = data.get('morphology', {})
                self.cache_loaded = True
                logger.info(f"Loaded morphology cache with {len(self.cache)} entries")
        except Exception as e:
            logger.error(f"Failed to load morphology cache: {e}")
    
    def extract_root(self, word: str) -> str:
        """
        Extract the morphological root of a Hebrew word.
        
        Process:
        1. Normalize to consonantal form
        2. Look up in cache (ETCBC morphology data)
        3. If not found, use improved naive extraction
        
        Args:
            word: Hebrew word (may include vowels/cantillation)
        
        Returns:
            Root/lemma (consonantal form)
        
        Examples:
            >>> analyzer = HebrewMorphologyAnalyzer()
            >>> analyzer.extract_root("מָחִיתָ")
            "מחה"
            >>> analyzer.extract_root("חַיִּים")
            "חיה"
        """
        if not word or not word.strip():
            return ''
        
        # Step 1: Normalize to consonantal form
        consonantal = strip_consonantal(word.strip())
        
        if not consonantal:
            return ''
        
        # Step 2: Check cache (high accuracy for Biblical Hebrew)
        if consonantal in self.cache:
            return self.cache[consonantal]
        
        # Step 3: Fallback to improved naive extraction
        return self._fallback_extraction(consonantal)
    
    def _fallback_extraction(self, consonantal: str) -> str:
        """
        Improved naive root extraction for words not in cache.

        Improvements over V2:
        - Minimum length filtering (avoid "בי", "ית" false matches)
        - Function word protection (don't strip to single letters)
        - Smarter prefix/suffix stripping with 3-letter minimum
        - Multi-prefix/suffix handling (try combinations)

        Args:
            consonantal: Hebrew word in consonantal form

        Returns:
            Extracted root
        """
        # Filter 1: If too short, don't strip anything
        if len(consonantal) < 3:
            return consonantal

        # Filter 2: Remove paragraph markers if present
        consonantal = re.sub(r'\{[^}]+\}', '', consonantal).strip()

        if not consonantal:
            return ''

        # Try stripping prefixes (max 2, trying combinations)
        result = consonantal
        prefixes_removed = 0

        while prefixes_removed < 2:
            found_prefix = False
            for prefix in self.COMMON_PREFIXES:
                if result.startswith(prefix):
                    stripped = result[len(prefix):]
                    # Be more conservative: require at least 3 letters after stripping prefix
                    # For "ש" specifically, require at least 4 letters since ש-initial roots are very common
                    # (e.g., שנא, שמר, שלח, שמע) and "ש" as a prefix is relatively rare
                    # ADAPTIVE FIX: If we already stripped a prefix, require 5+ letters for ש
                    # This prevents "ומשנאיו" → "שנאיו" (5 letters) → "נאיו" (incorrect)
                    # because after stripping "ום", we need more certainty before stripping ש
                    if prefix == 'ש':
                        min_length = 5 if prefixes_removed > 0 else 4
                    else:
                        min_length = 3
                    if stripped not in self.FUNCTION_WORDS and len(stripped) >= min_length:
                        result = stripped
                        prefixes_removed += 1
                        found_prefix = True
                        break  # Only strip one prefix at a time
            if not found_prefix:
                break  # No more prefixes to strip

        # Try stripping suffixes (max 2, trying combinations)
        suffixes_removed = 0

        while suffixes_removed < 2:
            found_suffix = False
            for suffix in self.COMMON_SUFFIXES:
                if result.endswith(suffix):
                    stripped = result[:-len(suffix)]
                    # For suffixes, require at least 2 letters (roots can be 2 letters)
                    # But avoid single letters
                    if stripped not in self.FUNCTION_WORDS and len(stripped) >= 2:
                        result = stripped
                        suffixes_removed += 1
                        found_suffix = True
                        break  # Only strip one suffix at a time
            if not found_suffix:
                break  # No more suffixes to strip

        # Final check: Don't return single function words
        if result in self.FUNCTION_WORDS:
            return consonantal  # Return original

        # Final check: Minimum length (2 letters for Biblical Hebrew roots)
        if len(result) < 2:
            return consonantal  # Return original

        return result
    
    def get_cache_stats(self) -> Dict[str, any]:
        """
        Get statistics about the morphology cache.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'cache_loaded': self.cache_loaded,
            'cache_size': len(self.cache),
            'cache_path': str(self.cache_path),
            'cache_exists': self.cache_path.exists() if self.cache_path else False
        }


# Global analyzer instance (singleton pattern for performance)
_global_analyzer: Optional[HebrewMorphologyAnalyzer] = None


def extract_morphological_root(word: str, cache_path: Optional[Path] = None) -> str:
    """
    Convenience function for extracting morphological root.
    
    Uses a global analyzer instance for performance (avoids reloading cache).
    
    Args:
        word: Hebrew word (may include vowels/cantillation)
        cache_path: Optional path to cache file (uses default if None)
    
    Returns:
        Root/lemma (consonantal form)
    
    Examples:
        >>> extract_morphological_root("מָחִיתָ")
        "מחה"
        >>> extract_morphological_root("חַיִּים")
        "חיה"
    """
    global _global_analyzer
    
    if _global_analyzer is None:
        _global_analyzer = HebrewMorphologyAnalyzer(cache_path)
    
    return _global_analyzer.extract_root(word)


# For backwards compatibility with existing code
def get_analyzer() -> HebrewMorphologyAnalyzer:
    """
    Get the global analyzer instance.
    
    Returns:
        Global HebrewMorphologyAnalyzer instance
    """
    global _global_analyzer
    
    if _global_analyzer is None:
        _global_analyzer = HebrewMorphologyAnalyzer()
    
    return _global_analyzer


if __name__ == '__main__':
    # Test the analyzer
    import sys
    
    analyzer = HebrewMorphologyAnalyzer()
    
    print("Hebrew Morphology Analyzer - Test")
    print("=" * 60)
    print(f"\nCache stats: {analyzer.get_cache_stats()}")
    
    # Test cases from false positive examples
    test_cases = [
        ("מָחִיתָ", "makhita", "you destroyed"),
        ("חַיִּים", "khayim", "life"),
        ("לִבִּי", "libi", "my heart"),
        ("בְּבֵית", "b'veit", "in house"),
        ("מְאֹד", "me'od", "very"),
        ("אֲדֹנָי", "Adonai", "Lord"),
    ]
    
    print("\n\nTest Cases:")
    print("-" * 60)
    for hebrew, transliteration, meaning in test_cases:
        root = analyzer.extract_root(hebrew)
        print(f"{hebrew:12} ({transliteration:12}) '{meaning:15}' → {root}")
    
    print("\n" + "=" * 60)
