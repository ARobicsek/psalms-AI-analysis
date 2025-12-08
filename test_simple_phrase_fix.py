#!/usr/bin/env python3
"""
Simple test to verify the phrase preservation fix.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_simple():
    """Simple test without complex Unicode handling."""
    from src.agents.micro_analyst import MicroAnalystV2

    # Simple test data
    test_discoveries = {
        'verse_discoveries': [
            {
                'verse_number': 1,
                'lexical_insights': [
                    {
                        'phrase': 'יָגוּר',
                        'variants': ['גור', 'גר'],
                        'notes': 'Dwell'
                    }
                ]
            }
        ]
    }

    analyst = MicroAnalystV2.__new__(MicroAnalystV2)
    phrases, variants = analyst._extract_exact_phrases_from_discoveries(test_discoveries)

    # Check that we got the expected phrase
    print(f"Found {len(phrases)} phrases")
    for key, value in phrases.items():
        print(f"  {key} -> {value}")

    # Should have 'יגור' as key
    if 'יגור' not in phrases:
        print("ERROR: 'יגור' not found in phrases!")
        return False

    if phrases['יגור'] != 'יגור':
        print(f"ERROR: Expected 'יגור', got '{phrases['יגור']}'")
        return False

    # Check variants
    if 'יגור' not in variants:
        print("ERROR: No variants for 'יגור'!")
        return False

    print(f"Found variants for 'יגור': {variants['יגור']}")

    if 'גור' not in variants['יגור']:
        print("ERROR: 'גור' not in variants!")
        return False

    print("SUCCESS: All checks passed!")
    return True

if __name__ == '__main__':
    try:
        if test_simple():
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)