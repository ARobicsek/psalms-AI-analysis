# Implementation Plan: converse_with_editor.py

**Created**: 2025-12-23
**Status**: Ready to implement

## Overview

A CLI script enabling multi-turn conversation with the "Master Editor" (GPT-5.1) about a completed psalm commentary. The user selects which context elements to include, then has a natural conversation with full memory.

## Usage

```bash
python scripts/converse_with_editor.py 19 --edition main
python scripts/converse_with_editor.py 19 --edition college
```

---

## Step-by-Step Implementation

### Step 1: Create File Skeleton

Create `scripts/converse_with_editor.py` with this structure:

```python
"""
Master Editor Conversation Script

Enables multi-turn conversation with the Master Editor (GPT-5.1) about
a completed psalm commentary, with full context from research materials.

Usage:
    python scripts/converse_with_editor.py PSALM_NUMBER [--edition main|college]

Author: Claude (Anthropic)
Date: 2025-12-23
"""

import sys
import os
import json
import argparse
import sqlite3
import re
from pathlib import Path
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# GPT-5.1 pricing (per 1M tokens) - update if needed
GPT51_INPUT_COST_PER_M = 2.00   # $2.00 per 1M input tokens
GPT51_OUTPUT_COST_PER_M = 8.00  # $8.00 per 1M output tokens


def main():
    """Main entry point."""
    pass  # Implement in steps below


if __name__ == '__main__':
    sys.exit(main() or 0)
```

---

### Step 2: Implement Argument Parsing

Add this function and call it from `main()`:

```python
def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Have a conversation with the Master Editor about a psalm commentary',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/converse_with_editor.py 19
  python scripts/converse_with_editor.py 19 --edition college
  python scripts/converse_with_editor.py 23 --edition main
        """
    )

    parser.add_argument('psalm_number', type=int,
                        help='Psalm number (1-150)')
    parser.add_argument('--edition', type=str, default='main',
                        choices=['main', 'college'],
                        help='Which edition to discuss (default: main)')

    return parser.parse_args()
```

---

### Step 3: Implement File Path Resolution

Add function to resolve all file paths for a psalm:

```python
def resolve_file_paths(psalm_number: int, edition: str) -> dict:
    """
    Resolve all file paths for the given psalm.

    Returns dict with keys:
        - output_dir: Path to psalm output directory
        - macro: Path to macro analysis JSON
        - micro: Path to micro analysis JSON
        - research: Path to research bundle markdown
        - edited_intro: Path to edited introduction
        - edited_verses: Path to edited verses
        - assessment: Path to editorial assessment
        - edition_suffix: '' for main, '_college' for college
    """
    # Try both naming conventions (psalm_N and psalm_NNN)
    base_dir = Path("output")
    psalm_dir = base_dir / f"psalm_{psalm_number}"
    if not psalm_dir.exists():
        psalm_dir = base_dir / f"psalm_{psalm_number:03d}"

    if not psalm_dir.exists():
        raise FileNotFoundError(
            f"Psalm output directory not found. Tried:\n"
            f"  - output/psalm_{psalm_number}\n"
            f"  - output/psalm_{psalm_number:03d}\n"
            f"Please run the full pipeline first."
        )

    # Determine edition suffix
    edition_suffix = "" if edition == "main" else "_college"

    # Build paths dict
    paths = {
        'output_dir': psalm_dir,
        'macro': psalm_dir / f"psalm_{psalm_number:03d}_macro.json",
        'micro': psalm_dir / f"psalm_{psalm_number:03d}_micro_v2.json",
        'research': psalm_dir / f"psalm_{psalm_number:03d}_research_v2.md",
        'edited_intro': psalm_dir / f"psalm_{psalm_number:03d}_edited_intro{edition_suffix}.md",
        'edited_verses': psalm_dir / f"psalm_{psalm_number:03d}_edited_verses{edition_suffix}.md",
        'assessment': psalm_dir / f"psalm_{psalm_number:03d}_assessment{edition_suffix}.md",
        'edition_suffix': edition_suffix,
    }

    return paths
```

---

### Step 4: Implement Psalm Text Loading from Database

Add function to load psalm text from tanakh.db:

```python
def load_psalm_text(psalm_number: int) -> str:
    """
    Load psalm text (Hebrew + English) from tanakh.db.

    Returns formatted string with all verses.
    """
    db_path = Path("database/tanakh.db")
    if not db_path.exists():
        return "[Psalm text not available - database not found]"

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Query verses for this psalm
    cursor.execute("""
        SELECT verse, hebrew, english
        FROM verses
        WHERE book_name = 'Psalms' AND chapter = ?
        ORDER BY verse
    """, (psalm_number,))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return f"[Psalm {psalm_number} not found in database]"

    # Format output
    lines = [f"## Psalm {psalm_number} Text\n"]
    for verse_num, hebrew, english in rows:
        lines.append(f"**Verse {verse_num}**")
        lines.append(f"Hebrew: {hebrew}")
        lines.append(f"English: {english}")
        lines.append("")

    return '\n'.join(lines)
```

---

### Step 5: Implement Research Bundle Parsing

Add function to parse research bundle markdown into sections:

```python
def parse_research_bundle(filepath: Path) -> dict:
    """
    Parse research bundle markdown into sections by ## headers.

    Returns dict mapping section name to content string.
    Section names are cleaned (e.g., "Hebrew Lexicon Entries (BDB)" -> "Lexicon")
    """
    if not filepath.exists():
        return {}

    content = filepath.read_text(encoding='utf-8')

    # Define section name mappings for cleaner display
    section_name_map = {
        "Hebrew Lexicon Entries (BDB)": "Lexicon",
        "Concordance Searches": "Concordance",
        "Figurative Language": "Figurative language",
        "Traditional Jewish Commentaries": "Traditional commentaries",
        "Liturgical Usage": "Liturgical usage",
        "Related Psalms": "Related psalms",
        "Rabbi Jonathan Sacks References": "Sacks references",
        "Deep Web Research": "Deep web research",
        "Scholarly Context (RAG)": "Scholarly context (RAG)",
    }

    sections = {}
    current_header = None
    current_content = []

    for line in content.split('\n'):
        if line.startswith('## '):
            # Save previous section
            if current_header:
                display_name = section_name_map.get(current_header, current_header)
                sections[display_name] = '\n'.join(current_content).strip()

            # Start new section
            current_header = line[3:].strip()
            current_content = []
        elif current_header:
            current_content.append(line)

    # Save last section
    if current_header:
        display_name = section_name_map.get(current_header, current_header)
        sections[display_name] = '\n'.join(current_content).strip()

    return sections
```

---

### Step 6: Implement Context Loading

Add function to load all context with character counts:

```python
def load_all_context(paths: dict, psalm_number: int) -> dict:
    """
    Load all available context files.

    Returns dict with structure:
    {
        'core': {
            'psalm_text': (content, char_count),
            'edited_intro': (content, char_count),
            'edited_verses': (content, char_count),
            'assessment': (content, char_count),
        },
        'analysis': {
            'Macro analysis': (content, char_count),
            'Micro analysis': (content, char_count),
        },
        'research': {
            'Lexicon': (content, char_count),
            'Concordance': (content, char_count),
            ...
        }
    }
    """
    context = {
        'core': {},
        'analysis': {},
        'research': {},
    }

    # Load core materials (always included)
    psalm_text = load_psalm_text(psalm_number)
    context['core']['Psalm text'] = (psalm_text, len(psalm_text))

    for key, display_name in [('edited_intro', 'Edited introduction'),
                               ('edited_verses', 'Edited verses'),
                               ('assessment', 'Editorial assessment')]:
        if paths[key].exists():
            content = paths[key].read_text(encoding='utf-8')
            context['core'][display_name] = (content, len(content))
        else:
            context['core'][display_name] = (f"[{display_name} not found]", 0)

    # Load analysis files (selectable)
    if paths['macro'].exists():
        content = paths['macro'].read_text(encoding='utf-8')
        context['analysis']['Macro analysis'] = (content, len(content))

    if paths['micro'].exists():
        content = paths['micro'].read_text(encoding='utf-8')
        context['analysis']['Micro analysis'] = (content, len(content))

    # Load research bundle sections (selectable)
    research_sections = parse_research_bundle(paths['research'])
    for name, content in research_sections.items():
        if content.strip():  # Only include non-empty sections
            context['research'][name] = (content, len(content))

    return context
```

---

### Step 7: Implement Interactive Section Selection

Add function for interactive section selection:

```python
def select_context_sections(context: dict) -> tuple:
    """
    Interactive selection of which context sections to include.

    Returns:
        - included_analysis: list of analysis section names to include
        - included_research: list of research section names to include
        - total_chars: total character count of selected content
    """
    print("\n" + "=" * 70)
    print("CONTEXT SELECTION")
    print("=" * 70)

    # Show core materials (always included)
    print("\nCore Materials (always included):")
    core_total = 0
    for name, (content, char_count) in context['core'].items():
        print(f"  [included] {name:.<45} {char_count:>10,} chars")
        core_total += char_count

    # Select analysis files
    print("\nAnalysis Files (ENTER=include, 'x'=exclude):")
    included_analysis = []
    for name, (content, char_count) in context['analysis'].items():
        response = input(f"  [{name}] ({char_count:,} chars): ").strip().lower()
        if response != 'x':
            included_analysis.append(name)
            print(f"    -> included")
        else:
            print(f"    -> excluded")

    # Select research bundle sections
    print("\nResearch Bundle Sections (ENTER=include, 'x'=exclude):")
    included_research = []
    for name, (content, char_count) in context['research'].items():
        response = input(f"  [{name}] ({char_count:,} chars): ").strip().lower()
        if response != 'x':
            included_research.append(name)
            print(f"    -> included")
        else:
            print(f"    -> excluded")

    # Calculate totals
    total_chars = core_total
    for name in included_analysis:
        total_chars += context['analysis'][name][1]
    for name in included_research:
        total_chars += context['research'][name][1]

    return included_analysis, included_research, total_chars
```

---

### Step 8: Implement System Prompt Builder

Add function to build the system prompt:

```python
def build_system_prompt(psalm_number: int, edition: str, context: dict,
                        included_analysis: list, included_research: list) -> str:
    """Build the system prompt with selected context."""

    # Header
    prompt_parts = [f"""You are the Master Editor who wrote this commentary on Psalm {psalm_number} ({edition} edition).

You have complete recall of all the research materials, analysis, and editorial decisions that informed your work. You can discuss:
- Why you made specific translation choices
- How you interpreted particular Hebrew words or phrases
- Which sources influenced your reading
- Alternative interpretations you considered
- Connections between verses and themes
- Anything in the research bundle you chose to use or not use

Speak as yourself—the editor who crafted this commentary. Be direct, scholarly, and willing to explain or defend your choices. If asked about something you didn't address in the commentary, you can offer your view based on the research materials.

---

## YOUR COMMENTARY (what you produced)
"""]

    # Add core materials
    for name in ['Psalm text', 'Edited introduction', 'Edited verses', 'Editorial assessment']:
        if name in context['core']:
            content, _ = context['core'][name]
            prompt_parts.append(f"\n### {name}\n{content}\n")

    # Add selected analysis
    if included_analysis:
        prompt_parts.append("\n---\n\n## ANALYSIS MATERIALS\n")
        for name in included_analysis:
            if name in context['analysis']:
                content, _ = context['analysis'][name]
                prompt_parts.append(f"\n### {name}\n{content}\n")

    # Add selected research
    if included_research:
        prompt_parts.append("\n---\n\n## RESEARCH MATERIALS\n")
        for name in included_research:
            if name in context['research']:
                content, _ = context['research'][name]
                prompt_parts.append(f"\n### {name}\n{content}\n")

    return ''.join(prompt_parts)
```

---

### Step 9: Implement Cost Tracking

Add class for cost tracking:

```python
class CostTracker:
    """Track API costs during conversation."""

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.exchanges = 0
        self.last_warning_threshold = 0  # Last $ threshold we warned at

    def add_usage(self, input_tokens: int, output_tokens: int):
        """Add token usage from an API call."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.exchanges += 1

    def get_total_cost(self) -> float:
        """Calculate total cost in dollars."""
        input_cost = (self.total_input_tokens / 1_000_000) * GPT51_INPUT_COST_PER_M
        output_cost = (self.total_output_tokens / 1_000_000) * GPT51_OUTPUT_COST_PER_M
        return input_cost + output_cost

    def check_threshold_warning(self) -> str | None:
        """Check if we crossed a $1 threshold. Returns warning message or None."""
        current_cost = self.get_total_cost()
        current_threshold = int(current_cost)  # Floor to nearest dollar

        if current_threshold > self.last_warning_threshold:
            self.last_warning_threshold = current_threshold
            return f"\n*** Cost warning: Conversation has now cost ${current_cost:.2f} ***\n"
        return None

    def get_summary(self) -> str:
        """Get final cost summary."""
        total = self.get_total_cost()
        return (
            f"\n{'=' * 50}\n"
            f"CONVERSATION SUMMARY\n"
            f"{'=' * 50}\n"
            f"Exchanges: {self.exchanges}\n"
            f"Input tokens: {self.total_input_tokens:,}\n"
            f"Output tokens: {self.total_output_tokens:,}\n"
            f"Total cost: ${total:.2f}\n"
        )
```

---

### Step 10: Implement Transcript Saving

Add function to save conversation transcript:

```python
def save_transcript(output_dir: Path, psalm_number: int, edition: str,
                    included_sections: list, messages: list,
                    cost_tracker: CostTracker) -> Path:
    """
    Save conversation transcript to markdown file.

    Returns path to saved file.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"conversation_{timestamp}.md"
    filepath = output_dir / filename

    lines = [
        f"# Conversation with Master Editor - Psalm {psalm_number} ({edition.title()} Edition)",
        f"",
        f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Model**: GPT-5.1 (high reasoning)",
        f"",
        f"## Context Included",
        "",
    ]

    for section in included_sections:
        lines.append(f"- {section}")

    lines.extend([
        "",
        "## Conversation",
        "",
    ])

    # Add conversation exchanges (skip system message)
    for msg in messages[1:]:  # Skip system prompt
        role = msg['role']
        content = msg['content']

        if role == 'user':
            lines.append(f"### You")
            lines.append(f"{content}")
            lines.append("")
        elif role == 'assistant':
            lines.append(f"### Master Editor")
            lines.append(f"{content}")
            lines.append("")

    # Add cost summary
    lines.extend([
        "---",
        "",
        f"**Total exchanges**: {cost_tracker.exchanges}",
        f"**Approximate cost**: ${cost_tracker.get_total_cost():.2f}",
    ])

    filepath.write_text('\n'.join(lines), encoding='utf-8')
    return filepath
```

---

### Step 11: Implement Conversation Loop

Add the main conversation loop:

```python
def run_conversation(client: OpenAI, system_prompt: str,
                     output_dir: Path, psalm_number: int, edition: str,
                     included_sections: list) -> None:
    """Run the interactive conversation loop."""

    messages = [{"role": "system", "content": system_prompt}]
    cost_tracker = CostTracker()

    print("\n" + "=" * 70)
    print("CONVERSATION READY")
    print("=" * 70)
    print("Commands: 'quit' to exit | 'save' to save transcript")
    print("=" * 70 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            user_input = "quit"

        if not user_input:
            continue

        # Handle commands
        if user_input.lower() == 'quit':
            print(cost_tracker.get_summary())
            break

        if user_input.lower() == 'save':
            filepath = save_transcript(
                output_dir, psalm_number, edition,
                included_sections, messages, cost_tracker
            )
            print(f"\nTranscript saved to: {filepath}\n")
            continue

        # Add user message
        messages.append({"role": "user", "content": user_input})

        # Call API
        try:
            print("\nMaster Editor: ", end="", flush=True)

            response = client.chat.completions.create(
                model="gpt-5.1",
                messages=messages,
                reasoning_effort="high",
                max_completion_tokens=4096
            )

            assistant_message = response.choices[0].message.content
            messages.append({"role": "assistant", "content": assistant_message})

            # Track cost
            usage = response.usage
            cost_tracker.add_usage(
                input_tokens=getattr(usage, 'prompt_tokens', 0),
                output_tokens=getattr(usage, 'completion_tokens', 0)
            )

            # Print response
            print(assistant_message)
            print()

            # Check for cost warning
            warning = cost_tracker.check_threshold_warning()
            if warning:
                print(warning)

        except Exception as e:
            print(f"\nError calling API: {e}")
            # Remove the user message we just added since we didn't get a response
            messages.pop()
            continue
```

---

### Step 12: Implement Main Function

Tie everything together in `main()`:

```python
def main():
    """Main entry point."""

    # Ensure UTF-8 on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    # Parse arguments
    args = parse_arguments()
    psalm_number = args.psalm_number
    edition = args.edition

    # Validate psalm number
    if not 1 <= psalm_number <= 150:
        print(f"Error: Psalm number must be between 1 and 150, got {psalm_number}")
        return 1

    print("\n" + "=" * 70)
    print(f"MASTER EDITOR CONVERSATION - Psalm {psalm_number} ({edition.title()} Edition)")
    print("=" * 70)

    # Resolve file paths
    try:
        paths = resolve_file_paths(psalm_number, edition)
        print(f"\nLoading from: {paths['output_dir']}")
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        return 1

    # Validate required files exist
    required = ['edited_intro', 'edited_verses', 'assessment']
    missing = [name for name in required if not paths[name].exists()]
    if missing:
        print(f"\nError: Required files missing:")
        for name in missing:
            print(f"  - {paths[name]}")
        print(f"\nPlease run the pipeline for Psalm {psalm_number} first.")
        return 1

    # Load all context
    print("\nLoading context...")
    context = load_all_context(paths, psalm_number)

    # Interactive selection
    included_analysis, included_research, total_chars = select_context_sections(context)

    # Build included sections list for transcript
    included_sections = (
        list(context['core'].keys()) +
        included_analysis +
        included_research
    )

    # Show summary and get confirmation
    estimated_tokens = total_chars // 4  # Rough estimate
    estimated_cost = (estimated_tokens / 1_000_000) * GPT51_INPUT_COST_PER_M

    print("\n" + "-" * 50)
    print(f"Total context: ~{total_chars:,} characters (~{estimated_tokens:,} tokens)")
    print(f"Estimated cost per exchange: ${estimated_cost:.2f} - ${estimated_cost * 2:.2f}")
    print("-" * 50)

    confirm = input("\nProceed with conversation? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return 0

    # Build system prompt
    system_prompt = build_system_prompt(
        psalm_number, edition, context,
        included_analysis, included_research
    )

    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\nError: OPENAI_API_KEY environment variable not set.")
        return 1

    client = OpenAI(api_key=api_key)

    print("\nInitializing conversation with GPT-5.1...")

    # Run conversation
    run_conversation(
        client, system_prompt,
        paths['output_dir'], psalm_number, edition,
        included_sections
    )

    return 0
```

---

## Testing Checklist

After implementation, verify:

1. [ ] `python scripts/converse_with_editor.py 19` loads psalm 19 main edition
2. [ ] `python scripts/converse_with_editor.py 19 --edition college` loads college edition
3. [ ] All context sections display with character counts
4. [ ] Pressing ENTER includes a section, 'x' excludes it
5. [ ] Token/cost estimate displays before confirmation
6. [ ] Conversation loop accepts user input and returns responses
7. [ ] Conversation maintains memory (reference previous exchanges)
8. [ ] `save` command creates properly formatted transcript
9. [ ] `quit` command displays cost summary and exits
10. [ ] Cost warnings appear when crossing $1 thresholds
11. [ ] Missing files show clear error messages
12. [ ] Ctrl+C exits gracefully

---

## Error Handling Notes

- If psalm directory doesn't exist: clear error pointing to pipeline
- If edited files missing: suggest running pipeline first
- If research bundle missing: continue without research sections
- If database missing: use placeholder text for psalm
- If API call fails: show error, keep conversation going
- If user hits Ctrl+C: treat as 'quit' command

---

## GPT-5.1 Pricing Reference

As of implementation date (verify current pricing):
- Input: $2.00 per 1M tokens
- Output: $8.00 per 1M tokens
- Reasoning tokens: counted as output

Update `GPT51_INPUT_COST_PER_M` and `GPT51_OUTPUT_COST_PER_M` constants if pricing changes.
