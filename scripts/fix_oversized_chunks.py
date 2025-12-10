"""
Fix oversized chunks in the corpus by splitting them.
"""
import json
from pathlib import Path

def main():
    corpus_file = Path("data/thematic_corpus/tanakh_chunks.jsonl")
    fixed_corpus = Path("data/thematic_corpus/tanakh_chunks_fixed.jsonl")

    print("Loading corpus and fixing oversized chunks...")
    print("=" * 60)

    chunks_processed = 0
    chunks_fixed = 0
    chunks_added = 0

    with open(corpus_file, 'r', encoding='utf-8') as infile, \
         open(fixed_corpus, 'w', encoding='utf-8') as outfile:

        for line in infile:
            chunk = json.loads(line)
            hebrew_text = chunk.get('hebrew_text', '')
            chunks_processed += 1

            # Check if chunk is too large (simple heuristic)
            # Rough estimate: Hebrew characters are roughly 1 token each
            # with some overhead for niqqud and punctuation
            estimated_tokens = len(hebrew_text)

            if estimated_tokens > 8000:  # Leave some buffer
                print(f"\nFixing oversized chunk: {chunk['reference']}")
                print(f"  Estimated tokens: {estimated_tokens}")

                # Split the text roughly in half
                text_lines = hebrew_text.split('\n')
                mid_point = len(text_lines) // 2

                # Find a good breaking point (chapter boundary if possible)
                break_point = mid_point
                for i in range(mid_point - 5, mid_point + 5):
                    if i < len(text_lines) and i > 0:
                        # Check for chapter marker pattern (e.g., "Chapter 27")
                        if 'Chapter' in text_lines[i] or 'פרק' in text_lines[i]:
                            break_point = i
                            break

                # Create first chunk
                first_part = '\n'.join(text_lines[:break_point])
                first_chunk = chunk.copy()
                first_chunk['hebrew_text'] = first_part
                first_chunk['verse_count'] = break_point  # Rough estimate
                # Update reference to indicate it's part A
                if ' - ' in chunk['reference']:
                    parts = chunk['reference'].split(' - ')
                    first_chunk['reference'] = f"{parts[0]} - Part A"
                else:
                    first_chunk['reference'] = f"{chunk['reference']} - Part A"

                # Create second chunk
                second_part = '\n'.join(text_lines[break_point:])
                second_chunk = chunk.copy()
                second_chunk['hebrew_text'] = second_part
                second_chunk['verse_count'] = len(text_lines) - break_point
                # Update reference to indicate it's part B
                if ' - ' in chunk['reference']:
                    parts = chunk['reference'].split(' - ')
                    second_chunk['reference'] = f"{parts[0]} - Part B"
                    # Update start verse for second chunk
                    if len(parts) == 2:
                        end_ref = parts[1]
                        # Approximate new start (this is a rough estimate)
                        if ':' in end_ref:
                            chapter, verse = map(int, end_ref.split(':'))
                            new_start_verse = chapter + (verse // 20)  # Rough guess
                            second_chunk['start_verse'] = str(new_start_verse)
                else:
                    second_chunk['reference'] = f"{chunk['reference']} - Part B"

                # Write both chunks
                json.dump(first_chunk, outfile, ensure_ascii=False)
                outfile.write('\n')
                json.dump(second_chunk, outfile, ensure_ascii=False)
                outfile.write('\n')

                chunks_fixed += 1
                chunks_added += 1  # One extra chunk
                print(f"  Split into two chunks:")
                print(f"    Part A: ~{len(first_part)} characters")
                print(f"    Part B: ~{len(second_part)} characters")
            else:
                # Write chunk as-is
                json.dump(chunk, outfile, ensure_ascii=False)
                outfile.write('\n')

            # Progress
            if chunks_processed % 5000 == 0:
                print(f"Processed {chunks_processed} chunks...")

    print("\n" + "=" * 60)
    print("FIX COMPLETE")
    print("=" * 60)
    print(f"Original chunks: {chunks_processed}")
    print(f"Chunks fixed: {chunks_fixed}")
    print(f"Final chunks: {chunks_processed + chunks_added}")

    print(f"\nFixed corpus saved to: {fixed_corpus}")
    print("\nTo use the fixed corpus:")
    print("1. Backup the original: mv tanakh_chunks.jsonl tanakh_chunks_original.jsonl")
    print("2. Rename the fixed: mv tanakh_chunks_fixed.jsonl tanakh_chunks.jsonl")

if __name__ == "__main__":
    main()