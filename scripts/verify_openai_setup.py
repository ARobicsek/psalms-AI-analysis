#!/usr/bin/env python3
"""
Verify OpenAI API access for embeddings.

This script tests that the OpenAI API is properly configured for generating
embeddings using text-embedding-3-large.

Usage:
    python scripts/verify_openai_setup.py
"""
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from openai import OpenAI
except ImportError:
    print("X OpenAI not installed. Run: pip install openai")
    sys.exit(1)


def verify_api():
    """Test OpenAI API access."""
    print("Verifying OpenAI API setup...")

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\nX OPENAI_API_KEY environment variable not found")
        print("Please set your OpenAI API key:")
        print("  export OPENAI_API_KEY='your-key-here'  # Linux/Mac")
        print("  set OPENAI_API_KEY=your-key-here     # Windows")
        return False

    try:
        client = OpenAI()

        # Test embedding generation
        print("\nTesting embedding generation...")
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input="Test embedding for Psalms project"
        )

        embedding = response.data[0].embedding

        print(f"+ OpenAI API working")
        print(f"+ Embedding dimension: {len(embedding)}")
        print(f"+ Model: text-embedding-3-large")
        print(f"+ First 5 values: {embedding[:5]}")

        return True

    except Exception as e:
        print(f"\nX Error accessing OpenAI API: {e}")
        print("\nPlease check:")
        print("  1. Your API key is valid")
        print("  2. You have credits available")
        print("  3. Your internet connection is working")
        return False


if __name__ == "__main__":
    success = verify_api()
    if not success:
        sys.exit(1)

    print("\n* Setup verified! You can proceed with building the thematic corpus.")