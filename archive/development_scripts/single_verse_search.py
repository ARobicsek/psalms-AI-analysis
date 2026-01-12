#!/usr/bin/env python3
"""
Single Verse Thematic Search

Generates reports for single verses showing:
- Top 5 thematic parallels in Psalms
- Top 5 thematic parallels in other Tanakh books
- Complete Hebrew text and English translations for all matches

Requires tanakh.db database and optionally a ChromaDB vector index.
"""
import sqlite3
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "src" / "thematic"))

# Import text cleaning function
try:
    from corpus_builder import clean_hebrew_text
except ImportError:
    # Define the function here if import fails
    def clean_hebrew_text(text: str) -> str:
        """Clean Hebrew text by removing cantillation marks but preserving vowels."""
        import re

        # Remove pasuq (׀)
        text = text.replace("׀", "")

        # Remove maqqaf (־) and replace with space
        text = text.replace("־", " ")

        # Remove cantillation accents (keep only niqqud vowels and letters)
        # Pattern to keep: Hebrew letters, vowel points, and spaces
        # Remove: accents (֑, ֒, ֓, ֔, ֕, ֖, ֗, ֘, ֙, ֚, ֛, ֜, ֝, ֞, ֟, ֠, ֡, ֢, ֣, ֤, ֥, ֦, ֧, ֨, ֩, ֪, ֫, ֬, ֭, ֮, ֯)
        # Note: Match corpus_builder.py exactly - DON'T remove PASEQ (U+05A5)
        cantillation_pattern = re.compile(r'[\u0591-\u05AF\u05BD-\u05C5]')
        text = cantillation_pattern.sub('', text)

        # Normalize spaces
        text = re.sub(r'\s+', ' ', text).strip()

        return text

try:
    from src.thematic.embedding_service import OpenAIEmbeddings
    from src.thematic.vector_store import ChromaVectorStore
    CHROMA_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ChromaDB not available: {e}")
    CHROMA_AVAILABLE = False


class SingleVerseSearcher:
    """Search for thematic parallels to single verses."""

    def __init__(self, db_path: str = "database/tanakh.db"):
        """Initialize with database path."""
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

        self.conn = sqlite3.connect(str(self.db_path))

        # Initialize embedding service
        if CHROMA_AVAILABLE:
            try:
                self.embedding_service = OpenAIEmbeddings()
                # Try to connect to existing vector store
                # Check both possible locations, including chroma_db subdirectories
                vector_dirs = [
                    Path("data/thematic_corpus_1_verse/chroma_db"),
                    Path("data/thematic_corpus_1_verse"),
                    Path("data/thematic_corpus/chroma_db"),
                    Path("data/thematic_corpus")
                ]

                self.vector_store = None
                for vector_dir in vector_dirs:
                    if vector_dir.exists():
                        try:
                            # Try with default collection name first
                            self.vector_store = ChromaVectorStore(
                                persist_directory=str(vector_dir),
                                collection_name="tanakh_chunks_1_verse"  # From session 204
                            )
                            count = self.vector_store.count()
                            if count > 0:
                                logger.info(f"Connected to vector store at {vector_dir} with {count} vectors")
                                break
                        except:
                            try:
                                # Try alternative collection name
                                self.vector_store = ChromaVectorStore(
                                    persist_directory=str(vector_dir),
                                    collection_name="tanakh_chunks"
                                )
                                count = self.vector_store.count()
                                if count > 0:
                                    logger.info(f"Connected to vector store at {vector_dir} with {count} vectors")
                                    break
                            except:
                                logger.warning(f"Failed to connect to vector store at {vector_dir}")
                                self.vector_store = None

                if self.vector_store is None:
                    logger.warning("No vector store found")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {e}")
                self.embedding_service = None
                self.vector_store = None
        else:
            self.embedding_service = None
            self.vector_store = None

    def get_verse_text(self, book: str, chapter: int, verse: int) -> Tuple[Optional[str], Optional[str]]:
        """Get Hebrew and English text for a specific verse."""
        query = """
        SELECT hebrew, english
        FROM verses
        WHERE book_name = ? AND chapter = ? AND verse = ?
        """
        cursor = self.conn.execute(query, (book, chapter, verse))
        row = cursor.fetchone()

        if row:
            return row[0], row[1]
        return None, None

    def search_thematic_parallels(self, hebrew_text: str, k: int = 10) -> List[Tuple[str, float, dict]]:
        """
        Search for thematic parallels using vector similarity.

        Returns:
            List of (chunk_id, similarity_score, metadata) tuples
        """
        if not self.embedding_service or not self.vector_store:
            logger.warning("No embedding service or vector store available")
            return []

        # Clean the Hebrew text to match what was used in the corpus
        cleaned_hebrew = clean_hebrew_text(hebrew_text)
        logger.info("Creating embedding for query...")
        query_embedding = self.embedding_service.embed(cleaned_hebrew)

        # Search vector store with documents included
        logger.info(f"Searching for top {k} matches...")

        # Query the collection directly to get documents with search
        collection = self.vector_store.collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )

        # Process results
        enhanced_results = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                # Convert distance to similarity
                distance = results["distances"][0][i] if results["distances"] else 0
                similarity = 1 / (1 + distance)

                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                document = results["documents"][0][i] if results["documents"] else ""

                # Add document to metadata
                enhanced_metadata = metadata.copy()
                enhanced_metadata['hebrew_text'] = document

                enhanced_results.append((chunk_id, similarity, enhanced_metadata))

        return enhanced_results

    def generate_report(self, book: str, chapter: int, verse: int) -> str:
        """Generate a thematic parallels report for a single verse."""
        # Get the verse text
        hebrew_text, english_text = self.get_verse_text(book, chapter, verse)

        if not hebrew_text:
            return f"Error: Could not find {book} {chapter}:{verse} in database"

        # Initialize report
        report_lines = [
            f"Thematic Parallels Report for {book} {chapter}:{verse}",
            "=" * 60,
            "",
            f"Query Verse:",
            f"  Hebrew: {hebrew_text}",
            f"  English: {english_text}" if english_text else "  English: [Not available]",
            ""
        ]

        # Search for parallels
        if self.embedding_service and self.vector_store:
            parallels = self.search_thematic_parallels(hebrew_text, k=30)  # Get more to filter

            if parallels:
                # Filter by category
                psalms_parallels = []
                other_parallels = []

                for chunk_id, similarity, metadata in parallels:
                    # Skip if it's the same verse
                    ref_book = metadata.get('book', '')
                    ref_chapter = metadata.get('chapter', 0)
                    ref_verse = metadata.get('verse', 0)

                    if (ref_book == book and ref_chapter == chapter and
                        ref_verse == verse):
                        continue

                    similarity_pct = similarity * 100

                    # Get full text for this chunk
                    chunk_hebrew = metadata.get('hebrew_text', '')
                    if not chunk_hebrew:
                        # Pull Hebrew from database using metadata
                        chunk_hebrew = self._get_hebrew_from_metadata(metadata)
                    chunk_english = self._get_translation_for_chunk(metadata)

                    entry = {
                        'reference': metadata.get('reference', f"{ref_book} {ref_chapter}:{ref_verse}"),
                        'similarity': similarity_pct,
                        'hebrew': chunk_hebrew,
                        'english': chunk_english,
                        'metadata': metadata
                    }

                    # Check if it's from Psalms
                    if ref_book == 'Psalms':
                        psalms_parallels.append(entry)
                    else:
                        other_parallels.append(entry)

                # Add top 10 from each category
                report_lines.append("Top 10 Thematic Parallels in Psalms:")
                report_lines.append("-" * 40)

                for i, entry in enumerate(psalms_parallels[:10], 1):
                    report_lines.extend([
                        f"{i}. {entry['reference']} (Similarity: {entry['similarity']:.1f}%)",
                        f"   Hebrew: {entry['hebrew']}",
                        f"   English: {entry['english']}",
                        ""
                    ])

                if len(psalms_parallels) == 0:
                    report_lines.append("  No Psalms parallels found")
                    report_lines.append("")

                report_lines.append("")
                report_lines.append("Top 10 Thematic Parallels in Other Books:")
                report_lines.append("-" * 40)

                for i, entry in enumerate(other_parallels[:10], 1):
                    report_lines.extend([
                        f"{i}. {entry['reference']} (Similarity: {entry['similarity']:.1f}%)",
                        f"   Hebrew: {entry['hebrew']}",
                        f"   English: {entry['english']}",
                        ""
                    ])

                if len(other_parallels) == 0:
                    report_lines.append("  No other book parallels found")
                    report_lines.append("")

                report_lines.append("")
                report_lines.append(f"Total parallels found: {len(parallels)}")

            else:
                report_lines.extend([
                    "No thematic parallels found.",
                    "",
                    "This could be because:",
                    "- The vector index is not built",
                    "- The similarity threshold is too high",
                    "- There are no similar verses in the corpus"
                ])
        else:
            report_lines.extend([
                "Thematic search unavailable:",
                "- ChromaDB vector index not found at data/thematic_corpus_1_verse/chroma_db",
                "- OpenAI API may not be configured",
                "",
                "To build the vector index, run:",
                "  python scripts/build_thematic_corpus.py",
                "  python scripts/build_vector_index.py"
            ])

        return "\n".join(report_lines)

    def _get_hebrew_from_metadata(self, metadata: dict) -> str:
        """Get Hebrew text from database using metadata."""
        book = metadata.get('book', '')
        chapter = metadata.get('chapter', 0)
        verse = metadata.get('verse', 0)

        hebrew, _ = self.get_verse_text(book, chapter, verse)
        return hebrew or ""

    def _get_translation_for_chunk(self, metadata: dict) -> str:
        """Get English translation for a chunk from metadata."""
        # Try to get from metadata first
        if 'english_text' in metadata:
            return metadata['english_text']

        # Otherwise construct from verse ranges
        book = metadata.get('book', '')
        chapter = metadata.get('chapter', 0)
        verse = metadata.get('verse', 0)

        # For single verse
        _, english = self.get_verse_text(book, chapter, verse)
        return english or "[Translation not available]"

    def close(self):
        """Close database connection."""
        if hasattr(self, 'conn'):
            self.conn.close()


def parse_verse_reference(ref: str) -> Tuple[str, int, int]:
    """Parse verse reference like 'ps 1:1' or 'psalm 1:1'."""
    parts = ref.lower().replace('psalms', 'ps').replace('psalm', 'ps').split()
    if len(parts) != 2:
        raise ValueError(f"Invalid verse reference format: {ref}")

    book = parts[0]
    if book == 'ps':
        book = 'Psalms'

    chapter_verse = parts[1].split(':')
    if len(chapter_verse) != 2:
        raise ValueError(f"Invalid chapter:verse format: {parts[1]}")

    return book, int(chapter_verse[0]), int(chapter_verse[1])


def main():
    # Check if running interactively or with command line arguments
    if len(sys.argv) == 1:
        # Interactive mode
        run_interactive()
    else:
        # Command line mode
        run_command_line()

def run_interactive():
    """Interactive mode for running the script."""
    print("Thematic Parallels Search for Psalms")
    print("=" * 50)
    print("Enter Psalm chapter and verse (e.g., '23:1' for Psalm 23:1)")
    print("Type 'quit' or 'exit' to exit")
    print()

    # Initialize searcher once
    try:
        searcher = SingleVerseSearcher("database/tanakh.db")
        if not searcher.embedding_service or not searcher.vector_store:
            print("ERROR: Could not initialize OpenAI embeddings or connect to vector store.")
            print("   Please check:")
            print("   1. Your OpenAI API key is set: export OPENAI_API_KEY='your-key-here'")
            print("   2. The vector index exists at: data/thematic_corpus_1_verse/chroma_db")
            print("   3. You have internet access for OpenAI API calls")
            return
    except Exception as e:
        print(f"ERROR: Could not initialize searcher: {e}")
        print("   Please check your OpenAI API key and vector index directory")
        return

    # Create output directory if it doesn't exist
    output_dir = Path("output/Verses_thematic_matches_RAG")
    output_dir.mkdir(parents=True, exist_ok=True)

    while True:
        try:
            user_input = input("Enter chapter:verse (e.g., 23:1) or 'quit': ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if ':' not in user_input:
                print("ERROR: Please use the format 'chapter:verse' (e.g., '23:1')")
                continue

            chapter_str, verse_str = user_input.split(':', 1)

            try:
                chapter = int(chapter_str.strip())
                verse = int(verse_str.strip())
            except ValueError:
                print("ERROR: Invalid chapter or verse. Please use numbers (e.g., '23:1')")
                continue

            if chapter < 1 or chapter > 150:
                print("ERROR: Psalm chapter must be between 1 and 150")
                continue

            if verse < 1:
                print("ERROR: Verse number must be at least 1")
                continue

            # Generate report
            print(f"\nSearching for thematic parallels for Psalm {chapter}:{verse}...")

            try:
                report = searcher.generate_report("Psalms", chapter, verse)

                # Save to output directory
                output_filename = f"psalm_{chapter:03d}_{verse:03d}_thematic_parallels.txt"
                output_path = output_dir / output_filename

                output_path.write_text(report, encoding='utf-8')
                print(f"Report saved to: {output_path}")
                print()

            except Exception as e:
                print(f"ERROR generating report: {e}")
                print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"ERROR: {e}")
            continue

    searcher.close()

def run_command_line():
    """Command line mode for running the script."""
    parser = argparse.ArgumentParser(
        description="Generate thematic parallels reports for single verses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python single_verse_search.py ps 1:1
  python single_verse_search.py psalms 145:8
  python single_verse_search.py ps 16:8 --output report.txt
        """
    )

    parser.add_argument('book', help='Book name (e.g., ps, psalms)')
    parser.add_argument('reference', help='Chapter:verse (e.g., 1:1)')
    parser.add_argument('--output', '-o', help='Output file (default: auto-generate in output/Verses_thematic_matches_RAG)')
    parser.add_argument('--db', default='database/tanakh.db', help='Database path')

    args = parser.parse_args()

    # Parse the verse reference
    try:
        book, chapter, verse = parse_verse_reference(f"{args.book} {args.reference}")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Initialize searcher
    try:
        searcher = SingleVerseSearcher(args.db)
    except Exception as e:
        print(f"Error initializing searcher: {e}")
        sys.exit(1)

    # Generate report
    try:
        report = searcher.generate_report(book, chapter, verse)

        # Create output directory if it doesn't exist
        output_dir = Path("output/Verses_thematic_matches_RAG")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Output report
        if args.output:
            output_path = Path(args.output)
        else:
            # Auto-generate filename
            output_filename = f"psalm_{chapter:03d}_{verse:03d}_thematic_parallels.txt"
            output_path = output_dir / output_filename

        output_path.write_text(report, encoding='utf-8')
        print(f"Report saved to: {output_path}")

    finally:
        searcher.close()


if __name__ == "__main__":
    main()