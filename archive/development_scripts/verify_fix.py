"""Verify that the fix is working and texts are identical."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from src.thematic.corpus_builder import load_corpus
from src.thematic.embedding_service import OpenAIEmbeddings
from src.thematic.vector_store import ChromaVectorStore
import numpy as np

# Load the corpus text for Psalm 23:1
corpus_path = Path("data/thematic_corpus_1_verse/tanakh_chunks.jsonl")
psalm_text = None

with open(corpus_path, "r", encoding="utf-8") as f:
    for line in f:
        chunk = json.loads(line)
        if chunk["chunk_id"] == "psalms_023_001":
            psalm_text = chunk["hebrew_text"]
            break

output = []
output.append(f"Psalm 23:1 text length: {len(psalm_text)}")

# Embed the text twice
embedder = OpenAIEmbeddings()

output.append("\nEmbedding the same text twice...")
emb1 = embedder.embed(psalm_text)
emb2 = embedder.embed(psalm_text)

# Calculate similarity
vec1 = np.array(emb1)
vec2 = np.array(emb2)

# Normalize
vec1_norm = vec1 / np.linalg.norm(vec1)
vec2_norm = vec2 / np.linalg.norm(vec2)

similarity = np.dot(vec1_norm, vec2_norm)
output.append(f"Self-similarity (should be 1.0): {similarity:.6f}")

# Check vector store
output.append("\nChecking vector store...")
vector_store = ChromaVectorStore(
    persist_directory="data/thematic_corpus_1_verse/chroma_db",
    collection_name="tanakh_chunks_1_verse",
)

# Search for the exact text
results = vector_store.search(query_embedding=emb1, k=1)

if results:
    output.append(f"Top result: {results[0].metadata['reference']}")
    output.append(f"Similarity: {results[0].score:.6f}")
    output.append(f"Chunk ID: {results[0].chunk_id}")

    # Check if it's the same chunk
    if results[0].chunk_id == "psalms_023_001":
        output.append("\n✓ Found the exact same chunk!")
    else:
        output.append(f"\n✗ Found different chunk: {results[0].chunk_id}")

    # The similarity should be very close to 1.0 if it's the same text
    if results[0].score > 0.999:
        output.append("✓ Similarity is close to 1.0 - texts match!")
    elif results[0].score > 0.95:
        output.append("? Similarity is high but not perfect - minor difference")
    else:
        output.append("✗ Similarity is low - significant difference")

# Save to file
with open("verification_results.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("Verification complete. See verification_results.txt")