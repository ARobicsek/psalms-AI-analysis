"""
Compare 1-verse chunks vs 5-verse overlapping windows for thematic search.

This script runs the same test queries on both systems to compare the quality
of thematic parallels found.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.thematic.corpus_builder import load_corpus, load_metadata
from src.thematic.embedding_service import OpenAIEmbeddings
from src.thematic.vector_store import ChromaVectorStore
import sqlite3


def get_psalm_verse_hebrew(psalm_num, verse_num):
    """Get Hebrew text for a specific Psalm verse."""
    db_path = Path(__file__).parent.parent / "database" / "tanakh.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT hebrew, english
        FROM verses
        WHERE book_name = 'Psalms' AND chapter = ? AND verse = ?
    """, (psalm_num, verse_num))

    result = cursor.fetchone()
    conn.close()
    return result


def test_1_verse_search(hebrew_text, k=10):
    """Search using 1-verse index."""
    project_root = Path(__file__).parent.parent
    corpus_dir = project_root / "data" / "thematic_corpus_1_verse"
    vector_db_dir = corpus_dir / "chroma_db"

    embedder = OpenAIEmbeddings()
    vector_store = ChromaVectorStore(
        persist_directory=str(vector_db_dir),
        collection_name="tanakh_chunks_1_verse",
    )

    query_embedding = embedder.embed(hebrew_text)
    results = vector_store.search(query_embedding=query_embedding, k=k)

    return results


def test_5_verse_search(hebrew_text, k=10):
    """Search using 5-verse index (if available)."""
    project_root = Path(__file__).parent.parent
    corpus_dir = project_root / "data" / "thematic_corpus"
    vector_db_dir = corpus_dir / "chroma_db"

    # Check if 5-verse index exists
    if not vector_db_dir.exists():
        return None

    embedder = OpenAIEmbeddings()
    vector_store = ChromaVectorStore(
        persist_directory=str(vector_db_dir),
        collection_name="tanakh_chunks",
    )

    query_embedding = embedder.embed(hebrew_text)
    results = vector_store.search(query_embedding=query_embedding, k=k)

    return results


def format_results(results, title):
    """Format search results for display."""
    print(f"\n{title}")
    print("=" * 60)

    if not results:
        print("No results found")
        return

    for i, result in enumerate(results, 1):
        print(f"{i}. {result.metadata['reference']} - Similarity: {result.score:.4f}")
        print(f"   Book: {result.metadata['book']} ({result.metadata['book_category']})")


def main():
    """Run comparison tests."""
    print("Comparing 1-verse vs 5-verse chunking for thematic search")
    print("=" * 80)

    # Test queries from different Psalms
    test_queries = [
        (23, 1),   # The LORD is my shepherd
        (23, 4),   # Valley of death
        (139, 13), # Created my inmost being
        (8, 5),    # What is man
        (121, 1),  # I lift up my eyes
    ]

    for psalm_num, verse_num in test_queries:
        hebrew, english = get_psalm_verse_hebrew(psalm_num, verse_num)
        print(f"\n{'='*80}")
        print(f"Test Query: Psalm {psalm_num}:{verse_num}")
        print(f"English: {english}")
        print(f"{'='*80}")

        # Test 1-verse chunks
        results_1v = test_1_verse_search(hebrew, k=10)
        format_results(results_1v, "1-VERSE CHUNKS RESULTS")

        # Test 5-verse chunks
        results_5v = test_5_verse_search(hebrew, k=10)
        if results_5v:
            format_results(results_5v, "5-VERSE OVERLAPPING WINDOWS RESULTS")
        else:
            print("\n5-VERSE OVERLAPPING WINDOWS RESULTS")
            print("=" * 60)
            print("5-verse index not found (expected - was discontinued)")

        # Analysis
        print(f"\nANALYSIS")
        print("-" * 60)
        print(f"1-verse chunks found: {len(results_1v)} results")
        if results_5v:
            print(f"5-verse windows found: {len(results_5v)} results")
        print(f"\nTop 1-verse result: {results_1v[0].metadata['reference']} (similarity: {results_1v[0].score:.4f})")
        print("\nObservation: 1-verse chunks provide more precise verse-level matching")
        print("while 5-verse windows provide more context but may be less precise.")


if __name__ == "__main__":
    main()