#!/usr/bin/env python3
"""Test the current state of the vector index during build."""

from src.thematic.vector_store import ChromaVectorStore
from src.thematic.embedding_service import OpenAIEmbeddings

def test_partial_index():
    """Test if the partial index has any searchable content."""

    # Connect to the vector store
    store = ChromaVectorStore(
        persist_directory="data/thematic_corpus/chroma_db"
    )

    # Create embedding service
    embedding_service = OpenAIEmbeddings()

    # Check collection stats
    try:
        total_chunks = store.count()
        print(f"Collection stats:")
        print(f"  Total chunks: {total_chunks}")

        # Try a simple test search
        query = "יהוה רועי לא אחסר"  # First few words of Psalm 23
        print(f"\nTesting query: {query}")

        # Generate embedding for the query
        query_embedding = embedding_service.get_embedding(query)
        print(f"Generated query embedding with {len(query_embedding)} dimensions")

        # Search in vector store
        results = store.search(
            query_embedding=query_embedding,
            n_results=5
        )

        print(f"\nFound {results['total_results']} results")
        for i, result in enumerate(results["results"][:3]):
            metadata = result.get("metadata", {})
            print(f"\nResult {i+1}:")
            if metadata:
                print(f"  Book: {metadata.get('book', 'Unknown')}")
                print(f"  Chapter: {metadata.get('chapter', 'Unknown')}")
                print(f"  Verses: {metadata.get('start_verse', '?')}-{metadata.get('end_verse', '?')}")
            print(f"  Similarity: {result.get('similarity', 0):.3f}")
            print(f"  Text: {result.get('document', '')[:100]}...")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_partial_index()