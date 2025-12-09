#!/usr/bin/env python3
"""Demonstrate Sefaria's topic/subject-based chunking approach."""

import json
import sys
from pathlib import Path
import requests

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thematic.corpus_builder import TanakhChunk, ChunkType, BookCategory

# Sefaria API base URL
SEFARIA_API = "https://www.sefaria.org/api"

# Topic to text mappings that would be typical for thematic search
TOPIC_MAPPINGS = {
    # Nature/Cosmology
    "Creation": [
        ("Genesis", 1, 1, 31),
        ("Genesis", 2, 1, 25),
        ("Psalm", 104, 1, 35),
        ("Isaiah", 40, 12, 26),
        ("Job", 38, 1, 41)
    ],

    # Covenant
    "Divine Covenant": [
        ("Genesis", 9, 8, 17),  # Noahic covenant
        ("Genesis", 15, None, None),  # Abrahamic covenant
        ("Genesis", 17, None, None),  # Covenant of circumcision
        ("Exodus", 19, 5, 6),  # Sinai covenant
        ("Jeremiah", 31, 31, 34),  # New covenant
    ],

    # Wisdom
    "Wisdom Literature": [
        ("Proverbs", 1, None, None),
        ("Proverbs", 2, None, None),
        ("Proverbs", 3, None, None),
        ("Proverbs", 8, None, None),
        ("Proverbs", 9, None, None),
        ("Ecclesiastes", 1, None, None),
        ("Ecclesiastes", 12, None, None),
        ("Job", 28, None, None),
    ],

    # Suffering
    "Suffering of the Righteous": [
        ("Job", 1, None, None),
        ("Job", 2, None, None),
        ("Job", 3, None, None),
        ("Psalm", 22, None, None),
        ("Psalm", 44, None, None),
        ("Lamentations", 3, None, None),
        ("Isaiah", 53, None, None),
    ],

    # Divine Justice
    "Divine Justice": [
        ("Deuteronomy", 32, None, None),  # Song of Moses
        ("Psalm", 1, None, None),
        ("Psalm", 73, None, None),
        ("Jeremiah", 12, 1, 4),
        ("Habakkuk", 1, None, None),
        ("Malachi", 3, None, None),
    ],

    # Prophecy
    "Prophetic Calling": [
        ("Isaiah", 6, None, None),
        ("Jeremiah", 1, None, None),
        ("Ezekiel", 1, None, None),
        ("Ezekiel", 2, None, None),
        ("Ezekiel", 3, None, None),
        ("Amos", 7, 14, 15),
        ("Jonah", 1, None, None),
    ],

    # Kingship
    "Davidic Kingship": [
        ("2 Samuel", 7, None, None),  # Davidic covenant
        ("Psalm", 2, None, None),     # Coronation psalm
        ("Psalm", 89, None, None),    # Davidic covenant
        ("Psalm", 110, None, None),   # Messianic king
        ("Isaiah", 11, None, None),   # Ideal king
        ("Jeremiah", 23, 5, 6),
    ],

    # Exile
    "Exile and Restoration": [
        ("2 Kings", 25, None, None),
        ("Jeremiah", 29, None, None),
        ("Jeremiah", 31, None, None),
        ("Ezekiel", 37, None, None),  # Valley of dry bones
        ("Isaiah", 40, None, None),   # Comfort in exile
        ("Daniel", 9, None, None),
    ]
}

def get_sefaria_text(book, chapter, verse_start=None, verse_end=None):
    """Get text from Sefaria API."""
    # Map English book names to Sefaria format
    sefaria_books = {
        "Genesis": "Genesis",
        "Exodus": "Exodus",
        "Leviticus": "Leviticus",
        "Numbers": "Numbers",
        "Deuteronomy": "Deuteronomy",
        "Joshua": "Joshua",
        "Judges": "Judges",
        "I Samuel": "I Samuel",
        "II Samuel": "II Samuel",
        "I Kings": "I Kings",
        "II Kings": "II Kings",
        "Isaiah": "Isaiah",
        "Jeremiah": "Jeremiah",
        "Ezekiel": "Ezekiel",
        "Hosea": "Hosea",
        "Joel": "Joel",
        "Amos": "Amos",
        "Jonah": "Jonah",
        "Micah": "Micah",
        "Nahum": "Nahum",
        "Habakkuk": "Habakkuk",
        "Zephaniah": "Zephaniah",
        "Haggai": "Haggai",
        "Zechariah": "Zechariah",
        "Malachi": "Malachi",
        "Psalms": "Psalms",
        "Proverbs": "Proverbs",
        "Job": "Job",
        "Song of Songs": "Song of Songs",
        "Ruth": "Ruth",
        "Lamentations": "Lamentations",
        "Ecclesiastes": "Ecclesiastes",
        "Esther": "Esther",
        "Daniel": "Daniel",
        "Ezra": "Ezra",
        "Nehemiah": "Nehemiah",
        "I Chronicles": "I Chronicles",
        "II Chronicles": "II Chronicles"
    }

    sefaria_book = sefaria_books.get(book, book)

    if verse_start and verse_end:
        ref = f"{sefaria_book} {chapter}:{verse_start}-{verse_end}"
    elif verse_start:
        ref = f"{sefaria_book} {chapter}:{verse_start}"
    else:
        # Get whole chapter
        ref = f"{sefaria_book} {chapter}"

    try:
        url = f"{SEFARIA_API}/texts/{ref}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if 'he' in data and 'text' in data:
                return data['he'], data.get('text', '')
            elif 'text' in data:
                return data['text'], ''
    except Exception as e:
        print(f"Error fetching {ref}: {e}")

    return None, None

def create_topic_chunks():
    """Create chunks based on Sefaria topic mappings."""
    chunks = []
    chunk_id = 1

    print("SEFARIA TOPIC-BASED CHUNKING DEMO")
    print("=" * 60)
    print("\nExample chunks based on thematic topics:")
    print("-" * 60)

    for topic, passages in TOPIC_MAPPINGS.items():
        print(f"\n{topic}:")
        print("-" * 40)

        for book, chapter, verse_start, verse_end in passages:
            # Get the reference string
            if verse_start and verse_end:
                ref = f"{book} {chapter}:{verse_start}-{verse_end}"
            elif verse_start:
                ref = f"{book} {chapter}:{verse_start}"
            else:
                ref = f"{book} {chapter}"

            print(f"  {ref}")

            # Create a chunk object (without actual text for demo)
            chunk = TanakhChunk(
                chunk_id=f"sefaria_topic_{chunk_id:04d}",
                reference=ref,
                book=book,
                book_category=get_book_category(book),
                start_chapter=chapter,
                start_verse=verse_start or 1,
                end_chapter=chapter,
                end_verse=verse_end or 999,
                hebrew_text="[Sefaria Hebrew text would go here]",
                english_text="[Sefaria English text would go here]",
                chunk_type=ChunkType.SEFARIA_SECTION,
                verse_count=1,  # Would calculate from actual text
                token_estimate=100,  # Would calculate from actual text
                sefaria_topics=[topic]
            )

            chunks.append(chunk)
            chunk_id += 1

    return chunks

def get_book_category(book):
    """Map book to category."""
    torah = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
    prophets = ["Joshua", "Judges", "I Samuel", "II Samuel", "I Kings", "II Kings",
                "Isaiah", "Jeremiah", "Ezekiel", "Hosea", "Joel", "Amos", "Obadiah",
                "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai",
                "Zechariah", "Malachi"]

    if book in torah:
        return BookCategory.TORAH
    elif book in prophets:
        return BookCategory.PROPHETS
    else:
        return BookCategory.WRITINGS

def analyze_approach():
    """Analyze the topic-based approach."""
    chunks = create_topic_chunks()

    print("\n" + "=" * 60)
    print("ANALYSIS OF TOPIC-BASED CHUNKING")
    print("=" * 60)

    print(f"\nTotal topic chunks created: {len(chunks)}")
    print(f"Unique topics: {len(TOPIC_MAPPINGS)}")

    # Count chunks per topic
    topic_counts = {}
    for topic, passages in TOPIC_MAPPINGS.items():
        topic_counts[topic] = len(passages)

    print("\nChunks per topic:")
    for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {topic}: {count} passages")

    print("\n" + "=" * 60)
    print("ADVANTAGES OF TOPIC-BASED CHUNKING:")
    print("-" * 40)
    print("✓ Thematically coherent by design")
    print("✓ Based on scholarly consensus about thematic connections")
    print("✓ Handles problematic books (Job, Ecclesiastes) gracefully")
    print("✓ Natural for thematic parallel searching")
    print("✓ Can include cross-textual connections (e.g., Psalms with Torah)")
    print("✓ Flexible - can add/remove topics as needed")

    print("\nDISADVANTAGES:")
    print("-" * 40)
    print("✗ Requires manual curation of topic mappings")
    print("✗ May miss unexpected thematic connections")
    print("✗ Limited by available topic classifications")
    print("✗ Needs regular updates to maintain relevance")

    print("\n" + "=" * 60)
    print("IMPLEMENTATION NOTES:")
    print("-" * 40)
    print("1. Can fetch actual text via Sefaria API")
    print("2. Topics can be hierarchical (e.g., 'Covenant' > 'Abrahamic')")
    print("3. Multiple topics per passage possible")
    print("4. Dynamic topic discovery possible via API")
    print("5. Could combine with semantic similarity for expansion")

if __name__ == "__main__":
    analyze_approach()