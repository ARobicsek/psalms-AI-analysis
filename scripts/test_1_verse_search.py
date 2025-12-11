"""
Test script for 1-verse thematic search.

Usage:
    python scripts/test_1_verse_search.py --psalm 23
    python scripts/test_1_verse_search.py --text "שׁכם גוים קבצו למו"
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.thematic.corpus_builder import load_corpus, load_metadata
from src.thematic.embedding_service import OpenAIEmbeddings
from src.thematic.vector_store import ChromaVectorStore


def main():
    parser = argparse.ArgumentParser(description="Test 1-verse thematic search")
    parser.add_argument("--psalm", type=int, help="Test with specific psalm verse")
    parser.add_argument("--text", type=str, help="Search for specific text")
    parser.add_argument("--k", type=int, default=10, help="Number of results")
    args = parser.parse_args()

    # Paths
    project_root = Path(__file__).parent.parent
    corpus_dir = project_root / "data" / "thematic_corpus_1_verse"
    vector_db_dir = corpus_dir / "chroma_db"

    # Check if vector index exists
    if not vector_db_dir.exists():
        print(f"Vector index not found at {vector_db_dir}")
        print("Run: python scripts/build_1_verse_vector_index.py")
        return

    # Initialize services
    print("Initializing services...")
    embedder = OpenAIEmbeddings()
    vector_store = ChromaVectorStore(
        persist_directory=str(vector_db_dir),
        collection_name="tanakh_chunks_1_verse",
    )

    print(f"Vector store has {vector_store.count()} indexed verses")

    if args.psalm:
        # Load Psalm verse from corpus (to match the indexed text)
        corpus_path = corpus_dir / "tanakh_chunks.jsonl"
        verse_text = None
        verse_ref = None
        verse_eng = None

        with open(corpus_path, "r", encoding="utf-8") as f:
            for line in f:
                import json
                chunk = json.loads(line)
                if chunk["book"] == "Psalms" and chunk["chapter"] == args.psalm:
                    verse_text = chunk["hebrew_text"]
                    verse_ref = chunk["reference"]
                    verse_eng = chunk.get("english_text", "")
                    break

        if not verse_text:
            print(f"Psalm {args.psalm} not found in corpus")
            return

        # Use Hebrew only (embedding_text() now returns only Hebrew)
        query_text = verse_text

        print(f"\nSearching for {verse_ref}")
        try:
            print(f"Hebrew: {verse_text}")
        except UnicodeEncodeError:
            print("Hebrew: [Unicode display issue]")
        if verse_eng:
            print(f"English: {verse_eng}")
            print("(Note: Using Hebrew only for embedding)\n")

    elif args.text:
        query_text = args.text
        try:
            print(f"\nSearching for: {query_text}\n")
        except UnicodeEncodeError:
            print("\nSearching for: [Hebrew text]\n")

    else:
        # Default test
        query_text = "יהוה רועי לא אחסר"
        print(f"\nSearching for default text: {query_text}\n")

    # Generate embedding
    print("Generating embedding...")
    query_embedding = embedder.embed(query_text)

    # Search
    print(f"Searching for top {args.k} similar verses...")
    results = vector_store.search(query_embedding=query_embedding, k=args.k)

    # Display results
    print(f"\nFound {len(results)} results:\n")

    for i, result in enumerate(results, 1):
        print(f"{i}. {result.metadata['reference']} - Similarity: {result.score:.4f}")
        print(f"   Book: {result.metadata['book']} ({result.metadata['book_category']})")

        # Load full text
        corpus_path = corpus_dir / "tanakh_chunks.jsonl"
        with open(corpus_path, "r", encoding="utf-8") as f:
            for line in f:
                import json
                chunk = json.loads(line)
                if chunk["chunk_id"] == result.chunk_id:
                    try:
                        print(f"   Hebrew: {chunk['hebrew_text'][:100]}...")
                    except UnicodeEncodeError:
                        print("   Hebrew: [Unicode display issue]")
                    if chunk.get("english_text"):
                        print(f"   English: {chunk['english_text'][:100]}...")
                    break
        print()


if __name__ == "__main__":
    main()