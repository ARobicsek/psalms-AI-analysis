"""
Enhanced Root Extractor V2 - Using Real Morphological Analysis

This module provides a drop-in replacement for the naive root extraction in V2,
using ETCBC morphological data for accurate root extraction.

Usage:
    # Instead of:
    from scripts.statistical_analysis.root_extractor import RootExtractor
    
    # Use:
    from src.hebrew_analysis.root_extractor_v2 import EnhancedRootExtractor as RootExtractor
    
    # API is backwards compatible
    extractor = RootExtractor(tanakh_db_path)
    roots = extractor.extract_psalm_roots(23)
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
import logging

# Import original root extractor
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts' / 'statistical_analysis'))
from root_extractor import RootExtractor as NaiveRootExtractor

# Import new morphology
sys.path.insert(0, str(Path(__file__).parent.parent))
from hebrew_analysis.morphology import HebrewMorphologyAnalyzer

logger = logging.getLogger(__name__)


class EnhancedRootExtractor(NaiveRootExtractor):
    """
    Enhanced root extractor using ETCBC morphological analysis.
    
    This class extends the original RootExtractor with accurate morphological
    analysis, while maintaining API compatibility for drop-in replacement.
    
    Improvements over V2:
    - Uses ETCBC scholarly morphological data (high accuracy for Biblical Hebrew)
    - Caches lookups for performance
    - Falls back to improved naive extraction for edge cases
    - Filters false positives (minimum length, function words)
    """
    
    def __init__(self, tanakh_db_path: Path, cache_path: Path = None):
        """
        Initialize enhanced root extractor.
        
        Args:
            tanakh_db_path: Path to tanakh.db database (inherited from parent)
            cache_path: Optional path to morphology cache (uses default if None)
        """
        # Initialize parent (database connection, etc.)
        super().__init__(tanakh_db_path)
        
        # Initialize morphology analyzer
        self.morphology = HebrewMorphologyAnalyzer(cache_path)
        
        # Log cache status
        stats = self.morphology.get_cache_stats()
        if stats['cache_loaded']:
            logger.info(f"Enhanced morphology loaded: {stats['cache_size']} entries")
        else:
            logger.warning("Morphology cache not loaded, using fallback extraction")
    
    def extract_root(self, word: str) -> str:
        """
        Extract the root form of a Hebrew word using morphological analysis.
        
        This method overrides the parent's naive implementation with
        morphologically-aware extraction.
        
        Args:
            word: Hebrew word (may have vowels)
        
        Returns:
            Extracted root (morphologically accurate)
        """
        if not word or not word.strip():
            return ''
        
        # Use morphology analyzer (cache + fallback)
        root = self.morphology.extract_root(word)
        
        # Quality check: minimum length (avoid false matches)
        if len(root) < 2:
            # Too short, likely noise
            return self.normalize_word(word)  # Use normalized form instead
        
        return root
    
    def get_morphology_stats(self) -> Dict[str, Any]:
        """
        Get statistics about morphology usage.
        
        Returns:
            Dictionary with stats about cache hits, fallbacks, etc.
        """
        return self.morphology.get_cache_stats()


class MorphologyV3Extractor(EnhancedRootExtractor):
    """
    Alias for V3 naming clarity.
    
    This is the same as EnhancedRootExtractor but with a clearer name
    for use in V3 statistical analysis.
    """
    pass


if __name__ == '__main__':
    # Test the enhanced extractor
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    # Find tanakh.db
    db_path = Path(__file__).parent.parent.parent / 'database' / 'tanakh.db'
    
    if not db_path.exists():
        print(f"ERROR: tanakh.db not found at {db_path}")
        sys.exit(1)
    
    print("Enhanced Root Extractor V2 - Test")
    print("=" * 60)
    print(f"Using database: {db_path}\n")
    
    # Test with Psalm 23
    print("Testing on Psalm 23...")
    print("-" * 60)
    
    with EnhancedRootExtractor(db_path) as extractor:
        # Show morphology stats
        stats = extractor.get_morphology_stats()
        print(f"\nMorphology Status:")
        print(f"  Cache loaded: {stats['cache_loaded']}")
        print(f"  Cache size: {stats['cache_size']} entries")
        
        # Extract roots
        result = extractor.extract_psalm_roots(23, include_phrases=False)
        
        print(f"\nPsalm 23 Analysis:")
        print(f"  Total unique roots: {len(result['roots'])}")
        
        # Show top 10 most frequent roots
        print("\n  Top 10 Most Frequent Roots:")
        sorted_roots = sorted(
            result['roots'].items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:10]
        
        for i, (root, data) in enumerate(sorted_roots, 1):
            examples = ', '.join(data['examples'][:2])
            print(f"    {i:2d}. {root:10} (count={data['count']}) - Examples: {examples}")
    
    print("\n" + "=" * 60)
    print("✓ Enhanced root extractor test complete!")
    print("=" * 60)
