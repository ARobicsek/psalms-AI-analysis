"""
Interactive Hebrew Concordance Tool

A standalone CLI tool providing menu-driven search for Hebrew words and phrases
across the entire Tanakh. Leverages the 4-layer concordance search system,
BDB/Klein lexicon lookups, and optional AI-powered curation via Claude.

Usage:
    python scripts/concordance_tool.py

Author: Claude (Anthropic)
Date: 2026-03-08
"""

import sys
import os
import json
import random
import textwrap
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.concordance.search import ConcordanceSearch, SearchResult
from src.concordance.hebrew_text_processor import (
    normalize_for_search, is_hebrew_text, strip_vowels
)
from src.data_sources.tanakh_database import TanakhDatabase, TANAKH_BOOKS
from src.agents.bdb_librarian import BDBLibrarian, LexiconEntry

# ─── Constants ────────────────────────────────────────────────────────────────

DEFAULT_MAX_RESULTS = 50
HAIKU_MODEL = "claude-haiku-4-5-20251001"
EXPORT_DIR = Path("output/concordance")

# Haiku 4.5 pricing (per 1M tokens)
HAIKU_INPUT_COST_PER_M = 0.80
HAIKU_OUTPUT_COST_PER_M = 4.00

# Build flat book list from TANAKH_BOOKS for menus
BOOK_LIST = []
for category in ['Torah', 'Prophets', 'Writings']:
    for eng_name, heb_name, chapters in TANAKH_BOOKS[category]:
        BOOK_LIST.append((eng_name, heb_name, category))

# ─── Terminal Helpers ─────────────────────────────────────────────────────────

def print_header(title: str):
    """Print a formatted section header."""
    width = max(len(title) + 4, 50)
    print(f"\n{'═' * width}")
    print(f"  {title}")
    print(f"{'═' * width}")


def print_menu_header(title: str):
    """Print a menu sub-header."""
    print(f"\n── {title} ──")


def print_divider():
    """Print a thin divider line."""
    print(f"{'─' * 50}")


# ─── Input Handling ───────────────────────────────────────────────────────────

def get_hebrew_input() -> tuple:
    """
    Prompt user for Hebrew text, normalize, and validate.

    Returns:
        (original_input, normalized_consonantal, is_multi_word)
        or (None, None, None) if user wants to quit
    """
    while True:
        raw = input("\nEnter Hebrew word(s) (or 'q' to quit): ").strip()

        if raw.lower() in ('q', 'quit', 'exit'):
            return None, None, None

        if not raw:
            print("  Please enter a Hebrew word or phrase.")
            continue

        if not is_hebrew_text(raw):
            print("  ⚠ No Hebrew characters detected. Please enter Hebrew text.")
            print("    (English and other characters are stripped automatically)")
            continue

        # Normalize to consonantal
        normalized = normalize_for_search(raw.strip(), level='consonantal')

        if not normalized or not normalized.strip():
            print("  ⚠ Could not normalize input. Please try again.")
            continue

        # Detect multi-word
        is_multi = ' ' in normalized.strip()

        # Warn on single-character input
        if len(normalized.replace(' ', '')) == 1:
            print("  ⚠ Single-character search will return very broad results.")

        print(f"  Searching for: {normalized} (consonantal)")
        return raw, normalized, is_multi


def select_action() -> str:
    """
    Select main action: concordance search, lexicon lookup, or both.

    Returns: 'concordance', 'lexicon', or 'both'
    """
    print_menu_header("Main Menu")
    print("  [1] Concordance search")
    print("  [2] Lexicon lookup (BDB + Klein definitions)")
    print("  [3] Both (search + definitions)")

    while True:
        choice = input("\nSelect [1-3, default=1]: ").strip()
        if choice in ('', '1'):
            return 'concordance'
        elif choice == '2':
            return 'lexicon'
        elif choice == '3':
            return 'both'
        else:
            print("  Please enter 1, 2, or 3.")


def select_scope() -> str:
    """
    Select search scope.

    Returns: scope string compatible with ConcordanceSearch
    """
    print_menu_header("Search Scope")
    print("  [1] Entire Tanakh")
    print("  [2] Torah")
    print("  [3] Prophets")
    print("  [4] Writings")
    print("  [5] Pick specific books...")

    while True:
        choice = input("\nSelect [1-5, default=1]: ").strip()
        if choice in ('', '1'):
            return 'Tanakh'
        elif choice == '2':
            return 'Torah'
        elif choice == '3':
            return 'Prophets'
        elif choice == '4':
            return 'Writings'
        elif choice == '5':
            return _pick_books()
        else:
            print("  Please enter 1-5.")


def _pick_books() -> str:
    """Sub-menu for picking specific books."""
    print()

    # Group books by category with numbering
    categories = {'Torah': [], 'Prophets': [], 'Writings': []}
    for i, (eng, heb, cat) in enumerate(BOOK_LIST, 1):
        categories[cat].append((i, eng, heb))

    # Display in columns
    print(f"  {'── Torah ──':<30} {'── Prophets ──':<30} {'── Writings ──':<30}")

    max_len = max(len(categories['Torah']), len(categories['Prophets']), len(categories['Writings']))
    for row in range(max_len):
        cols = []
        for cat in ['Torah', 'Prophets', 'Writings']:
            if row < len(categories[cat]):
                num, eng, heb = categories[cat][row]
                cols.append(f"  {num:>2}. {eng:<15} {heb}")
            else:
                cols.append("")
        print(f"  {cols[0]:<30} {cols[1]:<30} {cols[2]:<30}")

    while True:
        raw = input("\nEnter book numbers (comma-separated): ").strip()
        if not raw:
            print("  Please enter at least one book number.")
            continue

        try:
            nums = [int(n.strip()) for n in raw.split(',')]
            books = []
            for n in nums:
                if 1 <= n <= len(BOOK_LIST):
                    books.append(BOOK_LIST[n - 1][0])
                else:
                    print(f"  ⚠ Invalid number: {n}")
                    break
            else:
                # All valid
                scope = ','.join(books)
                print(f"  Searching in: {scope}")
                return scope
        except ValueError:
            print("  Please enter comma-separated numbers (e.g., 1,27,15).")


def select_match_mode(is_multi_word: bool) -> str:
    """
    Select search match mode.

    Returns: 'exact', 'variations', 'substring', 'substring_filtered',
             'phrase', or 'phrase_loose'
    """
    print_menu_header("Match Mode")

    if is_multi_word:
        print("  [1] Exact consonantal match (first word)")
        print("  [2] With prefix/suffix variations (first word)")
        print("  [3] Substring/root discovery (first word)")
        print("  [4] Substring/root + AI filter (first word)")
        print("  [5] Phrase search — consecutive words")
        print("  [6] Phrase search — same verse, any order")
        default = '5'
        max_choice = '6'
        default_label = "default=5"
    else:
        print("  [1] Exact consonantal match")
        print("  [2] With prefix/suffix variations")
        print("  [3] Substring/root discovery")
        print("  [4] Substring/root + AI filter")
        default = '2'
        max_choice = '4'
        default_label = "default=2"

    mode_map = {
        '1': 'exact',
        '2': 'variations',
        '3': 'substring',
        '4': 'substring_filtered',
        '5': 'phrase',
        '6': 'phrase_loose',
    }

    while True:
        choice = input(f"\nSelect [1-{max_choice}, {default_label}]: ").strip()
        if choice == '':
            choice = default
        if choice in mode_map and int(choice) <= int(max_choice):
            return mode_map[choice]
        else:
            print(f"  Please enter 1-{max_choice}.")


def select_result_options() -> tuple:
    """
    Select result max count and ordering.

    Returns: (max_results, selection_mode)
        selection_mode: 'canonical', 'random', or 'ai_curated'
    """
    print_menu_header("Result Options")

    # Max results
    raw = input(f"\nMax results [{DEFAULT_MAX_RESULTS}]: ").strip()
    try:
        max_results = int(raw) if raw else DEFAULT_MAX_RESULTS
        if max_results < 1:
            max_results = DEFAULT_MAX_RESULTS
    except ValueError:
        max_results = DEFAULT_MAX_RESULTS

    # Selection mode
    print("\n  [1] All matches (canonical order)")
    print("  [2] Random sample")
    print("  [3] AI-curated (semantic range examples)")

    while True:
        choice = input("\nSelect [1-3, default=1]: ").strip()
        if choice in ('', '1'):
            return max_results, 'canonical'
        elif choice == '2':
            return max_results, 'random'
        elif choice == '3':
            return max_results, 'ai_curated'
        else:
            print("  Please enter 1, 2, or 3.")


# ─── Search Execution ─────────────────────────────────────────────────────────

def execute_search(
    search: ConcordanceSearch,
    word: str,
    mode: str,
    scope: str,
    max_results: int
) -> list:
    """
    Dispatch search to the correct ConcordanceSearch method.

    Returns list of SearchResult objects.
    """
    try:
        search_mode = mode if mode != 'substring_filtered' else 'substring'
        if search_mode == 'exact':
            results = search.search_word(
                word, level='consonantal', scope=scope, limit=None, use_split=True
            )
        elif search_mode == 'variations':
            results = search.search_word_with_variations(
                word, level='consonantal', scope=scope, limit=None, use_split=True
            )
        elif search_mode == 'substring':
            results = search.search_substring(
                word, level='consonantal', scope=scope, limit=None, use_split=True
            )
        elif search_mode == 'phrase':
            results = search.search_phrase(
                word, level='consonantal', scope=scope, limit=None, use_split=True
            )
        elif search_mode == 'phrase_loose':
            results = search.search_phrase_in_verse(
                word, level='consonantal', scope=scope, limit=None, use_split=True
            )
        else:
            print(f"  ⚠ Unknown mode: {mode}")
            return []
    except Exception as e:
        print(f"  ⚠ Search error: {e}")
        return []

    return results


def randomize_results(results: list, max_results: int) -> list:
    """Return a random sample of results."""
    if len(results) <= max_results:
        return results
    return random.sample(results, max_results)


# ─── Lexicon ──────────────────────────────────────────────────────────────────

def execute_lexicon(word_original: str, word_normalized: str) -> list:
    """
    Fetch BDB + Klein lexicon entries.

    Tries original (diacritics) first for better match, falls back to
    consonantal.

    Returns list of LexiconEntry objects.
    """
    librarian = BDBLibrarian()

    # Try original form first (may have diacritics for better lexicon match)
    entries = librarian.fetch_entry(word_original, lexicon="scholarly")

    # If no results with original, try consonantal
    if not entries and word_original != word_normalized:
        entries = librarian.fetch_entry(word_normalized, lexicon="scholarly")

    return entries


def display_lexicon(entries: list):
    """Display lexicon entries in formatted terminal output."""
    if not entries:
        print("\n  No lexicon entries found.")
        print("  (The word may not be in the Sefaria BDB/Klein database)")
        return

    for entry in entries:
        print(f"\n  ── {entry.lexicon_name} ──")
        if entry.headword:
            line = f"  Headword: {entry.headword}"
            if entry.strong_number:
                line += f" (Strong's {entry.strong_number})"
            print(line)
        if entry.transliteration:
            print(f"  Transliteration: {entry.transliteration}")
        if entry.morphology:
            print(f"  Morphology: {entry.morphology}")
        if entry.entry_text:
            # Wrap long definitions
            wrapped = textwrap.fill(
                entry.entry_text, width=78, initial_indent="  Definition: ",
                subsequent_indent="    "
            )
            print(wrapped)
        if entry.etymology_notes:
            wrapped = textwrap.fill(
                entry.etymology_notes, width=78, initial_indent="  Etymology: ",
                subsequent_indent="    "
            )
            print(wrapped)
        if entry.derivatives:
            wrapped = textwrap.fill(
                entry.derivatives, width=78, initial_indent="  Derivatives: ",
                subsequent_indent="    "
            )
            print(wrapped)


# ─── AI Features ──────────────────────────────────────────────────────────────

def _get_anthropic_client():
    """Get Anthropic client, or None if unavailable."""
    try:
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("  ⚠ ANTHROPIC_API_KEY not set. AI features unavailable.")
            return None
        return anthropic.Anthropic(api_key=api_key)
    except ImportError:
        print("  ⚠ anthropic package not installed. AI features unavailable.")
        return None


def _display_ai_cost(response):
    """Display cost for an AI API call."""
    usage = response.usage
    input_cost = (usage.input_tokens / 1_000_000) * HAIKU_INPUT_COST_PER_M
    output_cost = (usage.output_tokens / 1_000_000) * HAIKU_OUTPUT_COST_PER_M
    total = input_cost + output_cost
    print(f"  💰 AI cost: ${total:.4f} ({usage.input_tokens:,} in / {usage.output_tokens:,} out)")


def _format_results_for_ai(results: list, max_show: int = 100) -> str:
    """Format results as text for AI prompts."""
    lines = []
    show = results[:max_show]
    for i, r in enumerate(show, 1):
        lines.append(f"{i}. {r.reference} | {r.hebrew_text} | {r.english_text}")
    if len(results) > max_show:
        lines.append(f"... ({len(results) - max_show} more results not shown)")
    return '\n'.join(lines)


def ai_curate_results(
    word: str,
    results: list,
    max_select: int
) -> list:
    """
    Use Claude Haiku to select representative examples illustrating semantic range.

    Returns list of (SearchResult, reason_selected) tuples, or empty list on failure.
    """
    client = _get_anthropic_client()
    if not client:
        return []

    formatted = _format_results_for_ai(results)

    prompt = f"""You are a Hebrew lexicography assistant. Given the Hebrew word "{word}" \
and the following concordance results, select {max_select} examples that \
best illustrate the word's semantic range — choose verses that show \
distinctly different usages, contexts, or nuances of meaning.

For each selection, provide a brief reason (1 sentence) explaining \
what this usage illustrates about the word's meaning.

Return JSON array: [{{"index": 1, "reason": "..."}}]
Use the 1-based index numbers from the results list.

Results:
{formatted}"""

    try:
        print("  Asking Claude to curate results...")
        response = client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        _display_ai_cost(response)
        text = response.content[0].text

        # Extract JSON from response (handle markdown code blocks)
        if '```' in text:
            # Find JSON block
            start = text.find('[')
            end = text.rfind(']') + 1
            if start >= 0 and end > start:
                text = text[start:end]

        selections = json.loads(text)

        curated = []
        for sel in selections:
            idx = sel.get('index', 0) - 1  # Convert to 0-based
            reason = sel.get('reason', '')
            if 0 <= idx < len(results):
                curated.append((results[idx], reason))

        return curated

    except json.JSONDecodeError:
        print("  ⚠ AI returned invalid JSON. Falling back to canonical order.")
        return []
    except Exception as e:
        print(f"  ⚠ AI curation failed: {e}")
        return []


def ai_commentary(word: str, results: list, scope: str) -> str:
    """
    Use Claude Haiku to generate semantic range analysis.

    Returns markdown commentary string, or empty string on failure.
    """
    client = _get_anthropic_client()
    if not client:
        return ""

    # Use a sample if too many results
    sample = results[:80] if len(results) > 80 else results
    formatted = _format_results_for_ai(sample)

    prompt = f"""You are a Hebrew lexicography assistant. Analyze the following concordance \
results for the Hebrew word "{word}" (searched in {scope}).

Total matches: {len(results)}
{formatted}

Provide a concise analysis (3-5 paragraphs) covering:
1. The word's semantic range as evidenced by these results
2. Distribution patterns across books/genres
3. Notable collocations or recurring phrases
4. Any interesting observations about usage

Write in a scholarly but accessible tone."""

    try:
        print("  Generating AI commentary...")
        response = client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        _display_ai_cost(response)
        return response.content[0].text
    except Exception as e:
        print(f"  ⚠ AI commentary failed: {e}")
        return ""


def ai_filter_false_matches(
    root: str,
    results: list
) -> list:
    """
    Use Claude Haiku to filter out false substring matches.

    Sends Claude the list of unique matched words and asks which ones are
    genuinely related to the searched root.

    Returns filtered list of SearchResult objects.
    """
    client = _get_anthropic_client()
    if not client:
        return results

    # Collect unique matched words
    unique_words = {}
    for r in results:
        if r.matched_word:
            consonantal = normalize_for_search(r.matched_word, level='consonantal')
            if consonantal not in unique_words:
                unique_words[consonantal] = r.matched_word  # Keep one pointed form

    if len(unique_words) <= 1:
        return results  # Nothing to filter

    word_list = '\n'.join(f"- {pointed} ({cons})" for cons, pointed in unique_words.items())

    prompt = f"""You are a Hebrew morphology expert. I searched for the root/substring "{root}" \
using a substring match, which found words containing these consonant sequences.

Review each matched word below and determine if it is genuinely derived from or \
related to the root "{root}", or if it is a FALSE MATCH where the letters happen \
to appear as part of an unrelated word.

Matched words:
{word_list}

Return a JSON object: {{"keep": ["cons1", "cons2", ...], "remove": ["cons3", ...]}}
Use the consonantal forms (in parentheses) for the lists.
Only remove words that are clearly unrelated to the root."""

    try:
        print("  Asking Claude to filter false matches...")
        response = client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        _display_ai_cost(response)

        text = response.content[0].text

        # Extract JSON
        if '{' in text:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                text = text[start:end]

        verdict = json.loads(text)
        remove_set = set(verdict.get('remove', []))

        if not remove_set:
            print("  ✓ No false matches detected.")
            return results

        # Show what's being removed
        removed_display = [unique_words.get(c, c) for c in remove_set if c in unique_words]
        print(f"  Removing {len(remove_set)} false match(es): {', '.join(removed_display)}")

        # Filter results
        filtered = []
        for r in results:
            if r.matched_word:
                cons = normalize_for_search(r.matched_word, level='consonantal')
                if cons in remove_set:
                    continue
            filtered.append(r)

        print(f"  Kept {len(filtered)} of {len(results)} results.")
        return filtered

    except json.JSONDecodeError:
        print("  ⚠ AI returned invalid JSON. Keeping all results.")
        return results
    except Exception as e:
        print(f"  ⚠ AI filtering failed: {e}")
        return results


# ─── Display ──────────────────────────────────────────────────────────────────

def display_results(
    results: list,
    total_count: int,
    word: str,
    scope: str,
    curated: list = None
):
    """Display search results in formatted terminal output."""
    if not results and not curated:
        print(f"\n  No matches found for '{word}' in {scope}.")
        print("  Try broadening the scope or switching to substring mode.")
        return

    showing = curated if curated else results
    print_header(f"Results for '{word}' in {scope}")

    if curated:
        for i, (result, reason) in enumerate(curated, 1):
            print(f"\n  [{i}] {result.reference}")
            print(f"      {result.hebrew_text}")
            print(f"      {result.english_text}")
            if result.matched_word:
                print(f"      Matched: {result.matched_word} (position {result.word_position})")
            print(f"      ✦ AI: {reason}")
    else:
        for i, result in enumerate(showing, 1):
            print(f"\n  [{i}] {result.reference}")
            print(f"      {result.hebrew_text}")
            print(f"      {result.english_text}")
            if result.matched_word:
                print(f"      Matched: {result.matched_word} (position {result.word_position})")

    print_divider()
    display_count = len(curated) if curated else len(results)
    print(f"  Found {total_count} matches for {word} in {scope} (showing {display_count})")

    if total_count > 500:
        print("  ⚠ Large result set — consider narrowing scope for better exploration.")


# ─── Export ───────────────────────────────────────────────────────────────────

def export_to_markdown(
    word: str,
    results: list,
    total_count: int,
    scope: str,
    mode: str,
    lexicon_entries: list = None,
    commentary: str = None,
    curated: list = None
) -> str:
    """
    Export results to a markdown file.

    Returns file path string.
    """
    # Ensure output directory exists
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Use consonantal word in filename (safe for filesystem)
    safe_word = word.replace(' ', '_')
    filename = f"search_{safe_word}_{timestamp}.md"
    filepath = EXPORT_DIR / filename

    mode_labels = {
        'exact': 'Exact consonantal match',
        'variations': 'With prefix/suffix variations',
        'substring': 'Substring/root discovery',
        'substring_filtered': 'Substring/root + AI filter',
        'phrase': 'Phrase (consecutive)',
        'phrase_loose': 'Phrase (same verse, any order)',
    }

    lines = [
        f"# Concordance Search: {word}",
        f"",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Scope:** {scope}",
        f"**Mode:** {mode_labels.get(mode, mode)}",
        f"**Total matches:** {total_count} (showing {len(curated) if curated else len(results)})",
        f"",
    ]

    # Lexicon entries
    if lexicon_entries:
        lines.append("## Lexicon Entries")
        lines.append("")
        for entry in lexicon_entries:
            lines.append(f"### {entry.lexicon_name}")
            if entry.headword:
                line = f"**Headword:** {entry.headword}"
                if entry.strong_number:
                    line += f" (Strong's {entry.strong_number})"
                lines.append(line)
            if entry.transliteration:
                lines.append(f"**Transliteration:** {entry.transliteration}")
            if entry.morphology:
                lines.append(f"**Morphology:** {entry.morphology}")
            if entry.entry_text:
                lines.append(f"**Definition:** {entry.entry_text}")
            if entry.etymology_notes:
                lines.append(f"**Etymology:** {entry.etymology_notes}")
            if entry.derivatives:
                lines.append(f"**Derivatives:** {entry.derivatives}")
            lines.append("")

    # Results
    lines.append("## Results")
    lines.append("")

    if curated:
        for i, (result, reason) in enumerate(curated, 1):
            lines.append(f"### {i}. {result.reference}")
            lines.append(f"**Hebrew:** {result.hebrew_text}")
            lines.append(f"**English:** {result.english_text}")
            if result.matched_word:
                lines.append(f"**Matched word:** {result.matched_word} (position {result.word_position})")
            lines.append(f"**AI selection reason:** {reason}")
            lines.append("")
    else:
        for i, result in enumerate(results, 1):
            lines.append(f"### {i}. {result.reference}")
            lines.append(f"**Hebrew:** {result.hebrew_text}")
            lines.append(f"**English:** {result.english_text}")
            if result.matched_word:
                lines.append(f"**Matched word:** {result.matched_word} (position {result.word_position})")
            lines.append("")

    # AI Commentary
    if commentary:
        lines.append("## AI Commentary")
        lines.append("")
        lines.append(commentary)
        lines.append("")

    filepath.write_text('\n'.join(lines), encoding='utf-8')
    return str(filepath)


# ─── Post-Results Menu ────────────────────────────────────────────────────────

def post_results_menu(
    search: ConcordanceSearch,
    word_original: str,
    word_normalized: str,
    is_multi_word: bool,
    results: list,
    total_count: int,
    scope: str,
    mode: str,
    max_results: int,
    selection_mode: str,
    displayed_results: list,
    curated: list,
    lexicon_entries: list,
    commentary: str
) -> str:
    """
    Post-results action menu.

    Returns: 'refine', 'new', or 'quit'
    """
    while True:
        print_menu_header("Post-Results")
        print("  [1] Refine search (change scope/mode)")
        print("  [2] New search")
        print("  [3] Export results to markdown")
        print("  [4] AI commentary (semantic range analysis)")
        print("  [5] Lexicon lookup for searched word")
        print("  [q] Quit")

        choice = input("\nSelect: ").strip().lower()

        if choice == '1':
            return 'refine'
        elif choice == '2':
            return 'new'
        elif choice == '3':
            filepath = export_to_markdown(
                word_normalized, displayed_results, total_count,
                scope, mode, lexicon_entries, commentary, curated
            )
            print(f"\n  ✓ Exported to: {filepath}")
        elif choice == '4':
            if not results:
                print("  No results to analyze.")
                continue
            commentary = ai_commentary(word_normalized, results, scope)
            if commentary:
                print_header("AI Commentary")
                print(textwrap.indent(commentary, '  '))
        elif choice == '5':
            entries = execute_lexicon(word_original, word_normalized)
            display_lexicon(entries)
            lexicon_entries = entries  # Update for future export
        elif choice in ('q', 'quit'):
            return 'quit'
        else:
            print("  Please enter 1-5 or q.")


# ─── Main Loop ────────────────────────────────────────────────────────────────

def main():
    """Main entry point — interactive concordance search loop."""

    # Ensure UTF-8 on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    print_header("HEBREW CONCORDANCE TOOL")
    print("  Search Hebrew words and phrases across the entire Tanakh")
    print("  Diacritics (nikud/cantillation) are automatically normalized")

    # Initialize search engine
    try:
        search = ConcordanceSearch()
    except Exception as e:
        print(f"\n  ✗ Failed to initialize concordance search: {e}")
        print("  Make sure database/tanakh.db exists.")
        return 1

    while True:
        # Step 1: Get Hebrew input
        word_original, word_normalized, is_multi_word = get_hebrew_input()
        if word_original is None:
            break

        # Step 2: Select action
        action = select_action()

        lexicon_entries = None
        commentary = None

        # Handle lexicon-only mode
        if action == 'lexicon':
            entries = execute_lexicon(word_original, word_normalized)
            display_lexicon(entries)
            continue

        # Lexicon + concordance
        if action == 'both':
            print("\n  Fetching lexicon entries...")
            lexicon_entries = execute_lexicon(word_original, word_normalized)
            display_lexicon(lexicon_entries)

        # Step 3: Concordance search options
        search_active = True
        scope = None
        mode = None

        while search_active:
            # Select search parameters (or re-select for refine)
            if scope is None:
                scope = select_scope()
            if mode is None:
                mode = select_match_mode(is_multi_word)
            max_results, selection_mode = select_result_options()

            # Step 4: Execute search
            print(f"\n  Searching...")
            all_results = execute_search(search, word_normalized, mode, scope, max_results)
            total_count = len(all_results)

            # Warn on very large result sets
            if total_count > 500:
                print(f"  ⚠ {total_count} results found — consider narrowing scope.")

            # Auto-run AI filter for substring_filtered mode
            if mode == 'substring_filtered' and total_count > 0:
                all_results = ai_filter_false_matches(word_normalized, all_results)
                total_count = len(all_results)

            # Step 5: Apply selection mode
            curated = None
            if total_count == 0:
                displayed_results = []
            elif selection_mode == 'random':
                displayed_results = randomize_results(all_results, max_results)
            elif selection_mode == 'ai_curated':
                curated = ai_curate_results(word_normalized, all_results, max_results)
                if not curated:
                    # Fallback to canonical
                    displayed_results = all_results[:max_results]
                else:
                    displayed_results = [r for r, _ in curated]
            else:
                # Canonical order
                displayed_results = all_results[:max_results]

            # Step 6: Display results
            display_results(displayed_results, total_count, word_normalized, scope, curated)

            # Step 7: Post-results menu
            action = post_results_menu(
                search, word_original, word_normalized, is_multi_word,
                all_results, total_count, scope, mode, max_results,
                selection_mode, displayed_results, curated,
                lexicon_entries, commentary
            )

            if action == 'refine':
                # Reset scope/mode to re-prompt
                scope = None
                mode = None
                continue
            elif action == 'new':
                search_active = False
            elif action == 'quit':
                search.close()
                print("\n  Goodbye! 👋")
                return 0

    # Cleanup
    search.close()
    print("\n  Goodbye! 👋")
    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
