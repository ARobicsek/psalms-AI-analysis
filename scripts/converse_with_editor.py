"""
Master Editor Conversation Script

Enables multi-turn conversation with the Master Editor (GPT-5.1) about
a completed psalm commentary, with full context from research materials.

As of V4 (Session 269), the dual Main/College edition system has been replaced
by a single unified writer. The --edition flag is retained as a hidden no-op
for backward compatibility.

Usage:
    python scripts/converse_with_editor.py PSALM_NUMBER

Author: Claude (Anthropic)
Date: 2025-12-23
"""

import sys
import os
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

load_dotenv()

# Add project root to path
# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.cost_tracker import PRICING



def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Have a conversation with the Master Editor about a psalm commentary',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/converse_with_editor.py 19
  python scripts/converse_with_editor.py 23
        """
    )

    parser.add_argument('psalm_number', type=int,
                        help='Psalm number (1-150)')
    parser.add_argument('--edition', type=str, default='main',
                        choices=['main', 'college'],
                        help=argparse.SUPPRESS)
    parser.add_argument('--model', type=str, default='gpt-5.1',
                        help='Model to converse with (default: gpt-5.1)')

    return parser.parse_args()


def resolve_file_paths(psalm_number: int) -> dict:
    """
    Resolve all file paths for the given psalm.
    Detects standard V4, SI, and fallback to legacy depending on what exists.

    Returns dict with keys:
        - output_dir: Path to psalm output directory
        - macro: Path to macro analysis JSON
        - micro: Path to micro analysis JSON
        - research: Path to research bundle markdown
        - edited_intro: Path to edited introduction
        - edited_verses: Path to edited verses
        - insights: Path to insights JSON (optional)
        - questions: Path to reader questions JSON (optional)
        - edition_name: e.g. "Standard V4", "Special Instruction", or "Legacy"
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

    # Determine paths and edition
    # Standard V4
    intro_v4 = psalm_dir / f"psalm_{psalm_number:03d}_edited_intro.md"
    verses_v4 = psalm_dir / f"psalm_{psalm_number:03d}_edited_verses.md"
    
    # SI V4
    intro_si = psalm_dir / f"psalm_{psalm_number:03d}_intro_SI.md"
    verses_si = psalm_dir / f"psalm_{psalm_number:03d}_verses_SI.md"
    
    # Legacy / Old Synthesis
    intro_old = psalm_dir / f"psalm_{psalm_number:03d}_synthesis_intro.md"
    verses_old = psalm_dir / f"psalm_{psalm_number:03d}_synthesis_verses.md"
    
    if intro_v4.exists() and verses_v4.exists():
        edited_intro = intro_v4
        edited_verses = verses_v4
        edition_name = "Standard V4"
    elif intro_si.exists() and verses_si.exists():
        edited_intro = intro_si
        edited_verses = verses_si
        edition_name = "Special Instruction"
    elif intro_old.exists() and verses_old.exists():
        edited_intro = intro_old
        edited_verses = verses_old
        edition_name = "Legacy"
    else:
        raise FileNotFoundError(f"Could not find introduction and verse commentary files in {psalm_dir}")

    # Determine research bundle (prefer trimmed)
    research_trimmed = psalm_dir / f"psalm_{psalm_number:03d}_research_trimmed.md"
    research_standard = psalm_dir / f"psalm_{psalm_number:03d}_research_v2.md"
    research_file = research_trimmed if research_trimmed.exists() else research_standard

    # Insights and Questions
    insights_file = psalm_dir / f"psalm_{psalm_number:03d}_insights.json"
    questions_refined = psalm_dir / f"psalm_{psalm_number:03d}_reader_questions_refined.json"
    questions_standard = psalm_dir / f"psalm_{psalm_number:03d}_reader_questions.json"
    questions_file = questions_refined if questions_refined.exists() else questions_standard

    # Build paths dict
    paths = {
        'output_dir': psalm_dir,
        'macro': psalm_dir / f"psalm_{psalm_number:03d}_macro.json",
        'micro': psalm_dir / f"psalm_{psalm_number:03d}_micro_v2.json",
        'research': research_file,
        'edited_intro': edited_intro,
        'edited_verses': edited_verses,
        'insights': insights_file,
        'questions': questions_file,
        'edition_name': edition_name,
    }

    return paths


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


def load_all_context(paths: dict, psalm_number: int) -> dict:
    """
    Load all available context files.

    Returns dict with structure:
    {
        'core': {
            'psalm_text': (content, char_count),
            'edited_intro': (content, char_count),
            'edited_verses': (content, char_count),
        },
        'analysis': {
            'Macro analysis': (content, char_count),
            'Micro analysis': (content, char_count),
            'Insights (JSON)': (content, char_count),
            'Reader Questions': (content, char_count),
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

    for key, display_name in [('edited_intro', 'Intro / Theme'),
                               ('edited_verses', 'Commentary verses')]:
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
        
    if 'insights' in paths and paths['insights'].exists():
        try:
            with open(paths['insights'], 'r', encoding='utf-8') as f:
                insights_data = json.load(f)
                
            formatted = ["## Extracted Insights\n"]
            if 'psalm_level_insights' in insights_data:
                formatted.append("### Psalm-Level Insights")
                for insight in insights_data['psalm_level_insights']:
                    formatted.append(f"- **{insight.get('type', 'Insight')}**: {insight.get('description', '')}")
            
            if 'verse_insights' in insights_data:
                formatted.append("\n### Verse Insights")
                for v_num, v_insights in insights_data['verse_insights'].items():
                    formatted.append(f"\n#### Verse {v_num}")
                    for insight in v_insights:
                        formatted.append(f"- **{insight.get('type', 'Insight')}**: {insight.get('description', '')}")
                        
            content = '\n'.join(formatted)
            context['analysis']['Insights'] = (content, len(content))
        except Exception as e:
            msg = f"[Could not parse insights JSON: {e}]"
            context['analysis']['Insights'] = (msg, len(msg))
            
    if 'questions' in paths and paths['questions'].exists():
        try:
            with open(paths['questions'], 'r', encoding='utf-8') as f:
                questions_data = json.load(f)
                
            formatted = ["## Reader Questions\n"]
            if 'curated_questions' in questions_data:
                for i, q in enumerate(questions_data['curated_questions'], 1):
                    formatted.append(f"{i}. {q}")
            
            content = '\n'.join(formatted)
            context['analysis']['Reader Questions'] = (content, len(content))
        except Exception as e:
            msg = f"[Could not parse questions JSON: {e}]"
            context['analysis']['Reader Questions'] = (msg, len(msg))

    # Load research bundle sections (selectable)
    research_sections = parse_research_bundle(paths['research'])
    for name, content in research_sections.items():
        if content.strip():  # Only include non-empty sections
            context['research'][name] = (content, len(content))

    return context


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
    
    # We can just use standard input() here since it's just single-char responses
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


class CostTracker:
    """Track API costs during conversation."""

    def __init__(self, model: str):
        self.model = model
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.exchanges = 0
        self.last_warning_threshold = 0  # Last $ threshold we warned at
        
        # Get pricing from master dict, fallback if not found
        pricing = PRICING.get(model, {"input": 1.25, "output": 10.00, "thinking": 10.00})
        self.input_cost_per_m = pricing["input"]
        self.output_cost_per_m = pricing["output"]

    def add_usage(self, input_tokens: int, output_tokens: int):
        """Add token usage from an API call."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.exchanges += 1

    def get_total_cost(self) -> float:
        """Calculate total cost in dollars."""
        input_cost = (self.total_input_tokens / 1_000_000) * self.input_cost_per_m
        output_cost = (self.total_output_tokens / 1_000_000) * self.output_cost_per_m
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
        f"**Model**: {cost_tracker.model} (high reasoning)",
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


def run_conversation(system_prompt: str,
                     output_dir: Path, psalm_number: int, edition: str,
                     included_sections: list, model: str) -> None:
    """Run the interactive conversation loop."""

    # Initialize appropriate client
    client_type = ""
    client = None
    if "claude" in model.lower():
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print(f"\nError: ANTHROPIC_API_KEY environment variable not set for {model}.")
            return
        client = anthropic.Anthropic(api_key=api_key)
        client_type = "anthropic"
    elif "gemini" in model.lower():
        from google import genai
        from google.genai import types
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print(f"\nError: GEMINI_API_KEY environment variable not set for {model}.")
            return
        client = genai.Client(api_key=api_key)
        client_type = "gemini"
    else:  # Assume OpenAI (gpt-*)
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print(f"\nError: OPENAI_API_KEY environment variable not set for {model}.")
            return
        client = OpenAI(api_key=api_key)
        client_type = "openai"

    messages = [{"role": "system", "content": system_prompt}]
    cost_tracker = CostTracker(model)

    print("\n" + "=" * 70)
    print("CONVERSATION INSTRUCTIONS")
    print("=" * 70)
    print("- Type your message and press [Alt+Enter] or [Esc] then [Enter] to submit.")
    print("- You can freely copy and paste multi-line content into the dialog.")
    print("- Commands: type 'quit' to exit, or 'save' to save transcript.")
    print("=" * 70 + "\n")

    style = Style.from_dict({
        'prompt': 'ansicyan bold',
    })
    session = PromptSession(style=style)

    while True:
        try:
            user_input = session.prompt("You: ", multiline=True).strip()
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

        # Call API with streaming for real-time feedback
        try:
            print("\nMaster Editor: ", end="", flush=True)

            assistant_message = ""
            input_tokens = 0
            output_tokens = 0

            if client_type == "openai":
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "max_completion_tokens": 4096,
                    "stream": True,
                    "stream_options": {"include_usage": True}
                }
                if "gpt-5" in model:
                    kwargs["reasoning_effort"] = "high"

                stream = client.chat.completions.create(**kwargs)

                for chunk in stream:
                    if chunk.usage:
                        input_tokens = chunk.usage.prompt_tokens
                        output_tokens = chunk.usage.completion_tokens
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if delta and delta.content:
                            print(delta.content, end="", flush=True)
                            assistant_message += delta.content

            elif client_type == "anthropic":
                system_msg = messages[0]["content"]
                anthropic_msgs = messages[1:]
                
                with client.messages.stream(
                    model=model,
                    max_tokens=4096,
                    system=system_msg,
                    messages=anthropic_msgs
                ) as stream:
                    for text in stream.text_stream:
                        print(text, end="", flush=True)
                        assistant_message += text
                    
                    final_msg = stream.get_final_message()
                    input_tokens = final_msg.usage.input_tokens
                    output_tokens = final_msg.usage.output_tokens

            elif client_type == "gemini":
                from google.genai import types
                
                system_instruction = messages[0]["content"]
                gemini_msgs = []
                for m in messages[1:]:
                    role = "user" if m["role"] == "user" else "model"
                    gemini_msgs.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))
                
                stream = client.models.generate_content_stream(
                    model=model,
                    contents=gemini_msgs,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        max_output_tokens=4096,
                    )
                )
                for chunk in stream:
                    if chunk.text:
                        print(chunk.text, end="", flush=True)
                        assistant_message += chunk.text
                    if chunk.usage_metadata:
                        input_tokens = chunk.usage_metadata.prompt_token_count
                        output_tokens = chunk.usage_metadata.candidates_token_count
                
                # Fallback if usage is 0
                if input_tokens == 0:
                    input_tokens = len(str(gemini_msgs) + system_instruction) // 4
                    output_tokens = len(assistant_message) // 4

            print()  # Newline after streamed response

            messages.append({"role": "assistant", "content": assistant_message})

            # Track cost
            cost_tracker.add_usage(
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )

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

    # V4 unified writer: --edition is a deprecated no-op
    if edition != 'main':
        print(f"Note: --edition {edition} is deprecated. "
              "V4 uses a unified writer (no separate college edition). "
              "Using main edition.")

    # Validate psalm number
    if not 1 <= psalm_number <= 150:
        print(f"Error: Psalm number must be between 1 and 150, got {psalm_number}")
        return 1

    # Resolve file paths (this auto-detects Standard/SI/Legacy)
    try:
        paths = resolve_file_paths(psalm_number)
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        return 1
        
    edition_name = paths.get('edition_name', 'Unknown')

    print("\n" + "=" * 70)
    print(f"MASTER EDITOR CONVERSATION - Psalm {psalm_number} ({edition_name} Edition)")
    print("=" * 70)
    print(f"\nLoading from: {paths['output_dir']}")

    # Validate required files exist
    required = ['edited_intro', 'edited_verses']
    missing = [name for name in required if not paths[name].exists()]
    if missing:
        print(f"\nError: Required files missing:")
        for name in missing:
            print(f"  - {paths[name]}")
        print(f"\nPlease run the pipeline for Psalm {psalm_number} first.")
        return 1

    # Interactive Model Selection
    print("\n" + "=" * 50)
    print("MODEL SELECTION")
    print("=" * 50)
    models = list(PRICING.keys())
    for i, m in enumerate(models, 1):
        default_marker = " (default)" if m == args.model else ""
        print(f"  {i}. {m}{default_marker}")
    
    selected_model = args.model
    while True:
        choice = input(f"\nSelect model (1-{len(models)}) or press ENTER for {args.model}: ").strip()
        if not choice:
            break
        if choice.isdigit() and 1 <= int(choice) <= len(models):
            selected_model = models[int(choice)-1]
            break
        print("Invalid selection.")

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
    
    pricing = PRICING.get(selected_model, {"input": 1.25, "output": 10.00, "thinking": 10.00})
    estimated_cost = (estimated_tokens / 1_000_000) * pricing["input"]

    print("\n" + "-" * 50)
    print(f"Total context: ~{total_chars:,} characters (~{estimated_tokens:,} tokens)")
    print(f"Estimated cost per exchange using {selected_model}: ${estimated_cost:.2f} - ${estimated_cost * 2:.2f}")
    print("-" * 50)

    confirm = input("\nProceed with conversation? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return 0

    # Build system prompt
    system_prompt = build_system_prompt(
        psalm_number, edition_name, context,
        included_analysis, included_research
    )

    print(f"\nInitializing conversation with {selected_model}...")

    # Run conversation
    run_conversation(
        system_prompt,
        paths['output_dir'], psalm_number, edition_name,
        included_sections, selected_model
    )

    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
