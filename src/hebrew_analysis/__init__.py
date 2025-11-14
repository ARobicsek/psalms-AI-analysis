"""
Hebrew Morphological Analysis Package

Provides accurate root extraction for Biblical Hebrew using ETCBC Text-Fabric
with fallback to improved naive extraction for edge cases.
"""

from .morphology import extract_morphological_root, HebrewMorphologyAnalyzer
from .cache_builder import build_psalms_cache, load_cache

__all__ = [
    'extract_morphological_root',
    'HebrewMorphologyAnalyzer',
    'build_psalms_cache',
    'load_cache',
]

__version__ = '1.0.0'
