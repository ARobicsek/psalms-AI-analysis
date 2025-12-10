"""
Find oversized chunks in the corpus.
"""
import json
import tiktoken
from pathlib import Path

def count_tokens(text: str, model: str = "text-embedding-3-large") -> int:
    """Count actual tokens using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback to cl100k_base (used by text-embedding-3-large)
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

def main():
    corpus_file = Path("data/thematic_corpus/tanakh_chunks.jsonl")

    print("Loading corpus and checking token counts...")
    print("=" * 60)

    max_tokens = 0
    max_chunk = None
    large_chunks = []

    with open(corpus_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            chunk = json.loads(line)
            hebrew_text = chunk.get('hebrew_text', '')

            # Count actual tokens
            token_count = count_tokens(hebrew_text)

            # Update max
            if token_count > max_tokens:
                max_tokens = token_count
                max_chunk = {
                    'index': i,
                    'reference': chunk['reference'],
                    'token_count': token_count,
                    'text_preview': hebrew_text[:200] + '...' if len(hebrew_text) > 200 else hebrew_text
                }

            # Track large chunks
            if token_count > 8192:
                large_chunks.append({
                    'index': i,
                    'reference': chunk['reference'],
                    'token_count': token_count
                })

            # Progress
            if (i + 1) % 5000 == 0:
                print(f"Processed {i + 1} chunks...")

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total chunks processed: {i + 1}")
    print(f"Maximum tokens found: {max_tokens}")
    print(f"Chunk with most tokens:")
    print(f"  Reference: {max_chunk['reference']}")
    print(f"  Token count: {max_chunk['token_count']}")
    print(f"  Text preview: {max_chunk['text_preview']}")

    if large_chunks:
        print(f"\nFound {len(large_chunks)} chunks exceeding 8192 tokens:")
        for chunk in large_chunks:
            print(f"  {chunk['reference']}: {chunk['token_count']} tokens")
    else:
        print("\nNo chunks exceed 8192 tokens")

    # Check if the issue is with chunk ID format
    print("\n" + "=" * 60)
    print("CHECKING CHUNK ID FORMAT")
    print("=" * 60)

    # Re-open and check first few chunk IDs
    with open(corpus_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 5:
                break
            chunk = json.loads(line)
            print(f"Chunk {i+1} ID format: {chunk['reference']}")

if __name__ == "__main__":
    main()