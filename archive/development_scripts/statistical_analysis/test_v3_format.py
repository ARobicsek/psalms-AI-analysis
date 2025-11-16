#!/usr/bin/env python3
"""
Test V3 Format - Demonstrate Verse-Level Details

This script tests the V3 enhancement on a single psalm pair (14-53)
to show the verse-level detail format without processing all relationships.
"""

import json
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_scorer_skipgram_dedup_v3 import (
    VerseDetailExtractor,
    enhance_contiguous_phrases_with_details,
    enhance_skipgrams_with_details,
    enhance_roots_with_details,
    TANAKH_DB_PATH
)

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Test V3 format on Psalms 14-53 (rank 1 pair)."""
    
    base_dir = Path(__file__).parent.parent.parent
    
    # Load the original relationship data for Psalms 14-53
    logger.info("Loading significant relationships...")
    with open(base_dir / "data/analysis_results/significant_relationships.json", 'r', encoding='utf-8') as f:
        relationships = json.load(f)
    
    # Find Psalms 14-53
    target_rel = None
    for rel in relationships:
        if rel['psalm_a'] == 14 and rel['psalm_b'] == 53:
            target_rel = rel
            break
    
    if not target_rel:
        logger.error("Could not find Psalms 14-53 relationship")
        return
    
    logger.info(f"Found Psalms 14-53 relationship")
    logger.info(f"  Shared phrases: {len(target_rel['shared_phrases'])}")
    logger.info(f"  Shared roots: {len(target_rel['shared_roots'])}")
    
    # Initialize verse detail extractor
    logger.info("\nInitializing verse detail extractor...")
    detail_extractor = VerseDetailExtractor(TANAKH_DB_PATH)
    
    # Test 1: Enhance a contiguous phrase
    logger.info("\n=== TEST 1: Contiguous Phrase Details ===")
    if target_rel['shared_phrases']:
        sample_phrase = target_rel['shared_phrases'][0]
        logger.info(f"\nOriginal phrase (V2 format):")
        logger.info(json.dumps(sample_phrase, indent=2, ensure_ascii=False))
        
        enhanced_phrases = enhance_contiguous_phrases_with_details(
            [sample_phrase],
            14, 53,
            detail_extractor
        )
        
        logger.info(f"\nEnhanced phrase (V3 format):")
        logger.info(json.dumps(enhanced_phrases[0], indent=2, ensure_ascii=False))
    
    # Test 2: Enhance a skipgram (create a sample one)
    logger.info("\n=== TEST 2: Skipgram Details ===")
    # Create a sample skipgram pattern that exists in these psalms
    sample_skipgram = {
        'consonantal': 'אמר נבל',  # "said fool" - should appear in both
        'length': 2,
        'hebrew': 'אמר נבל'
    }
    
    logger.info(f"\nSample skipgram (V2 format):")
    logger.info(json.dumps(sample_skipgram, indent=2, ensure_ascii=False))
    
    enhanced_skipgrams = enhance_skipgrams_with_details(
        [sample_skipgram],
        14, 53,
        detail_extractor
    )
    
    if enhanced_skipgrams[0]['matches_from_a']:
        logger.info(f"\nEnhanced skipgram (V3 format):")
        logger.info(json.dumps(enhanced_skipgrams[0], indent=2, ensure_ascii=False))
    else:
        logger.info("\nNo matches found for this skipgram pattern")
    
    # Test 3: Enhance a root
    logger.info("\n=== TEST 3: Root Details ===")
    if target_rel['shared_roots']:
        sample_root = target_rel['shared_roots'][0]
        logger.info(f"\nOriginal root (V2 format):")
        logger.info(json.dumps(sample_root, indent=2, ensure_ascii=False))
        
        enhanced_roots = enhance_roots_with_details(
            [sample_root],
            14, 53,
            detail_extractor
        )
        
        logger.info(f"\nEnhanced root (V3 format):")
        logger.info(json.dumps(enhanced_roots[0], indent=2, ensure_ascii=False))
    
    # Test 4: Show concordance sample
    logger.info("\n=== TEST 4: Concordance Sample ===")
    psalm_14_words = detail_extractor.get_psalm_concordance(14)
    logger.info(f"\nFirst 10 words of Psalm 14:")
    for i, word in enumerate(psalm_14_words[:10]):
        logger.info(f"  {i}: v{word['verse']}:{word['position']} {word['hebrew']} ({word['consonantal']})")
    
    # Close extractor
    detail_extractor.close()
    
    logger.info("\n✓ V3 format test complete!")
    logger.info("\nKey V3 enhancements demonstrated:")
    logger.info("  1. Contiguous phrases: position + text for each match")
    logger.info("  2. Skipgrams: verse numbers + position ranges + full span text")
    logger.info("  3. Roots: verse numbers + positions + actual Hebrew text")


if __name__ == "__main__":
    main()
