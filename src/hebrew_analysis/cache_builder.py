"""
Morphology Cache Builder

Builds a lookup cache of Hebrew word → root mappings from ETCBC Text-Fabric data.
Run this once to create the cache, then use morphology.py for fast lookups.

Usage:
    python cache_builder.py
    
    # Or from Python:
    from cache_builder import build_psalms_cache
    build_psalms_cache()
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

# Text-Fabric import (optional dependency)
try:
    from tf.app import use
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logger.warning("Text-Fabric not installed. Install with: pip install text-fabric")


def build_psalms_cache(output_path: Optional[Path] = None, 
                       include_all_bible: bool = False) -> Dict[str, str]:
    """
    Build morphology cache from ETCBC Text-Fabric data.
    
    Creates a lookup table mapping consonantal Hebrew words to their lemmas (roots)
    based on scholarly morphological analysis from the ETCBC BHSA dataset.
    
    Args:
        output_path: Where to save cache JSON file. If None, uses default location.
        include_all_bible: If True, cache entire Hebrew Bible. If False, only Psalms.
    
    Returns:
        Dictionary mapping consonantal form → lemma
    
    Raises:
        ImportError: If text-fabric is not installed
        RuntimeError: If BHSA data cannot be loaded
    """
    if not TF_AVAILABLE:
        raise ImportError(
            "text-fabric is required to build cache. "
            "Install with: pip install text-fabric"
        )
    
    logger.info("Loading ETCBC BHSA data (this may take a minute on first run)...")
    
    try:
        # Load Hebrew Bible with morphology
        # checkout="clone" ensures we get the full dataset
        A = use('ETCBC/bhsa', checkout="clone", silent=True)
    except Exception as e:
        raise RuntimeError(f"Failed to load BHSA data: {e}")
    
    logger.info("BHSA data loaded successfully")
    
    # Build cache
    cache = {}
    word_count = 0
    collision_count = 0
    
    # Determine which books to process
    if include_all_bible:
        # Get all book nodes
        books = A.F.book.s('Genesis')  # Start from Genesis
        logger.info("Building cache for entire Hebrew Bible...")
        book_filter = None  # Process all
    else:
        # Only Psalms
        logger.info("Building cache for Psalms only...")
        book_filter = 'Psalms'
    
    # Iterate through all words
    for word_node in A.F.otype.s('word'):
        # Check if word is in desired book(s)
        book_node = A.L.u(word_node, 'book')[0]  # Get parent book
        book_name = A.F.book.v(book_node)
        
        if book_filter and book_name != book_filter:
            continue  # Skip this word
        
        # Get word data
        consonantal = A.F.g_cons.v(word_node)  # Consonantal form (without vowels)
        lemma = A.F.lex.v(word_node)  # Lexeme (root/lemma)
        
        if not consonantal or not lemma:
            continue
        
        word_count += 1
        
        # Handle collisions (same consonantal, different lemmas)
        # Strategy: Keep first occurrence (could be improved with frequency)
        if consonantal in cache:
            if cache[consonantal] != lemma:
                collision_count += 1
                # For now, keep first lemma
                # Could be improved: use frequency, context, etc.
        else:
            cache[consonantal] = lemma
    
    logger.info(f"Processed {word_count} words")
    logger.info(f"Unique consonantal forms: {len(cache)}")
    logger.info(f"Collisions (same consonantal, different lemmas): {collision_count}")
    
    # Save cache to JSON
    if output_path is None:
        output_path = Path(__file__).parent / 'data' / 'psalms_morphology_cache.json'
    
    # Create directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare metadata
    cache_data = {
        'version': '1.0.0',
        'source': 'ETCBC/bhsa',
        'source_license': 'CC BY-NC 4.0',
        'books': 'all' if include_all_bible else 'Psalms',
        'word_count': word_count,
        'unique_forms': len(cache),
        'collisions': collision_count,
        'morphology': cache
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Cache saved to {output_path}")
    logger.info(f"Cache size: {output_path.stat().st_size / 1024:.1f} KB")
    
    return cache


def load_cache(cache_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load morphology cache from JSON file.
    
    Args:
        cache_path: Path to cache file. If None, uses default location.
    
    Returns:
        Dictionary mapping consonantal form → lemma
    
    Raises:
        FileNotFoundError: If cache file doesn't exist
    """
    if cache_path is None:
        cache_path = Path(__file__).parent / 'data' / 'psalms_morphology_cache.json'
    
    if not cache_path.exists():
        raise FileNotFoundError(
            f"Cache file not found: {cache_path}\n"
            f"Run build_psalms_cache() to create it."
        )
    
    with open(cache_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('morphology', {})


def analyze_cache_coverage(cache_path: Optional[Path] = None):
    """
    Analyze cache coverage and statistics.
    
    Args:
        cache_path: Path to cache file. If None, uses default location.
    """
    cache = load_cache(cache_path)
    
    print("Cache Analysis")
    print("=" * 60)
    print(f"Total entries: {len(cache)}")
    
    # Analyze root lengths
    root_lengths = defaultdict(int)
    for consonantal, lemma in cache.items():
        root_lengths[len(lemma)] += 1
    
    print("\nRoot Length Distribution:")
    for length in sorted(root_lengths.keys()):
        count = root_lengths[length]
        pct = count / len(cache) * 100
        print(f"  {length} letters: {count:5d} ({pct:5.1f}%)")
    
    # Show sample entries
    print("\nSample Entries (first 20):")
    for i, (consonantal, lemma) in enumerate(list(cache.items())[:20], 1):
        print(f"  {i:2d}. {consonantal:15} → {lemma}")
    
    print("=" * 60)


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    import sys
    
    print("ETCBC Morphology Cache Builder")
    print("=" * 60)
    
    # Check if Text-Fabric is available
    if not TF_AVAILABLE:
        print("\nERROR: text-fabric not installed")
        print("Install with: pip install text-fabric")
        sys.exit(1)
    
    # Build cache
    print("\nBuilding morphology cache from ETCBC BHSA data...")
    print("(First run will download ~100MB of data)")
    print()
    
    try:
        cache = build_psalms_cache(include_all_bible=False)
        
        print("\n" + "=" * 60)
        print("✓ Cache built successfully!")
        print("=" * 60)
        
        # Analyze cache
        print()
        analyze_cache_coverage()
        
    except Exception as e:
        print(f"\n✗ Error building cache: {e}")
        sys.exit(1)
