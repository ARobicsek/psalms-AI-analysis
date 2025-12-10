#!/usr/bin/env python3
"""
Test ChromaDB directly
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import chromadb

def main():
    print("Testing ChromaDB directly")
    print("=" * 50)

    # Connect to ChromaDB
    client = chromadb.PersistentClient(path="data/thematic_corpus/chroma_db")

    # List collections
    collections = client.list_collections()
    print(f"\nFound {len(collections)} collections:")
    for col in collections:
        print(f"  - {col.name}")

    if collections:
        # Get the first collection
        collection = collections[0]
        print(f"\nCollection: {collection.name}")
        print(f"  Count: {collection.count()}")

        # Get a sample of documents
        if collection.count() > 0:
            print("\nSample documents:")
            results = collection.get(limit=3, include=['documents', 'metadatas'])
            for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas']), 1):
                print(f"\n{i}. Document: {doc[:100]}...")
                print(f"   Metadata: {meta}")

    # Test a direct query
    print("\n\nTesting direct query...")
    if collections:
        collection = collections[0]
        query_results = collection.query(
            query_texts=["אדם וחוה"],  # Adam and Eve
            n_results=3
        )

        if query_results['documents'][0]:
            print(f"✅ Found {len(query_results['documents'][0])} results")
            for i, (doc, dist) in enumerate(zip(query_results['documents'][0], query_results['distances'][0]), 1):
                print(f"\n{i}. Distance: {dist:.4f}")
                print(f"   Document: {doc[:100]}...")
        else:
            print("❌ No results found")

if __name__ == "__main__":
    main()