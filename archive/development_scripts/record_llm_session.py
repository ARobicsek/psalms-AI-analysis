import sys
import io
from src.agents.liturgical_librarian import LiturgicalLibrarian

def record_session(psalm_chapter: int, output_file: str = None):
    """
    Runs the Liturgical Librarian for a single Psalm with verbose output
    to capture all LLM interactions.

    Args:
        psalm_chapter: Psalm number to analyze
        output_file: Optional output file path. If provided, writes to file with UTF-8 encoding.
                     If None, prints to stdout.
    """
    # Configure UTF-8 output for Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    # If output file specified, redirect stdout to file with explicit UTF-8 encoding
    original_stdout = sys.stdout
    if output_file:
        sys.stdout = open(output_file, 'w', encoding='utf-8')

    try:
        print(f"Starting verbose session for Psalm {psalm_chapter}...\n")

        # Initialize librarian with verbose output enabled
        librarian = LiturgicalLibrarian(use_llm_summaries=True, verbose=True)

        # The verbose output will be printed directly to stdout
        librarian.find_liturgical_usage_by_phrase(
            psalm_chapter=psalm_chapter,
            min_confidence=0.7,
            separate_full_psalm=True
        )

        print(f"\nVerbose session for Psalm {psalm_chapter} complete.")
    finally:
        # Restore original stdout if we redirected it
        if output_file:
            sys.stdout.close()
            sys.stdout = original_stdout
            print(f"Output written to {output_file}")

if __name__ == "__main__":
    # For now, this script is hardcoded for Psalm 1 as requested.
    # It could be modified to accept command-line arguments if needed.
    record_session(psalm_chapter=1, output_file='logs/psalm1_full_prompts_log.txt')
