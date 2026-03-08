"""
Copy Editor Agent — Psalm Commentary Quality Control

Session 279: Standalone agent that applies a 9-category error taxonomy to existing
commentary output, making minimal, targeted corrections while preserving all formatting.

Error Categories:
  1. False structural claims (chiasmus, inclusio, merism)
  2. Internal inconsistencies (self-contradicting claims)
  3. Form/content confusion (phonosemantic overreach)
  4. Negative or empty citations (citing a scholar's silence)
  5. Hebrew script integrity (romanized substitutions)
  6. Weak cross-cultural parallels (surface-level comparisons)
  7. Factual/textual accuracy (misquoted texts, wrong grammatical person, inverted logic)
  8. Hebrew grammar bloat (unnecessary stem/tense/person annotations)
  9. Strained arguments (e.g. evidence does not support the claim)

Usage:
    from src.agents.copy_editor import CopyEditor
    editor = CopyEditor()
    result = editor.edit_commentary(psalm_number=38)
"""

import os
import re
import sys
import difflib
import time
from pathlib import Path
from typing import Optional, Dict, Tuple

# Handle imports for both module and script usage
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.utils.logger import get_logger
    from src.utils.cost_tracker import CostTracker
else:
    from src.utils.logger import get_logger
    from src.utils.cost_tracker import CostTracker

import anthropic
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# SYSTEM PROMPT — from docs/features/Copy_editor_plan.md
# =============================================================================

COPY_EDITOR_SYSTEM_PROMPT = """You are a copy editor for scholarly psalm commentary written for an educated
general audience. Make minimal, targeted corrections. Do not rewrite for
style or voice. Do not add material. Do not remove content that is merely
debatable — only correct content that is demonstrably wrong, empty, or
self-contradicting.

Preserve parenthetical definitions of technical terms (e.g., defining
"inclusio," "LXX," "Hiphil," "chiasmus" on first use within a psalm
commentary). Readers may be reading only one psalm guide. Remove a
definition only if the same term was already defined earlier in the same
psalm's commentary.

Correct the following categories of error:

1. STRUCTURAL CLAIMS. If the text labels a pattern as chiasmus, verify
   A-B-B'-A' element order in the cited text. If the order is A-B-A'-B',
   relabel it as parallelism or antithetical parallelism as appropriate.
   If inclusio is claimed, verify the opening and closing elements are
   the same word or phrase actually appearing in both positions — a word
   doing "double duty" across two cola is not the same as the word
   appearing twice. If merism is claimed, verify the two named poles
   represent a genuine complete spectrum. Correct the label or remove the
   claim. Remove any parenthetical definition that now contradicts the
   corrected label.

2. INTERNAL INCONSISTENCIES. If a claim contradicts something stated
   earlier in the same commentary (e.g., describing a verse as having a
   "double X" when the earlier analysis showed it has one X doing double
   duty), correct the later statement to be consistent with the earlier,
   more detailed analysis.

3. FORM/CONTENT CONFUSION. If the text claims that sound, syntax,
   morphology, or grammar "performs," "enacts," "mimics," or "embodies"
   a meaning, check two things: (a) is a specific formal feature
   identified? (b) does the effect genuinely arise from that formal
   feature rather than from what the words mean? If the meaning comes
   from semantics rather than form, rewrite the sentence to attribute the
   effect correctly. Do not remove the observation — just reattribute it.
   Note: reduplication (pe'al'al forms), cognate accusatives, and
   onomatopoeia are legitimate form-meaning connections when correctly
   identified.

4. NEGATIVE CITATIONS. If a scholar is cited only to report that they
   do not address the topic, or is mentioned only as a foil without
   engaging their actual view, remove the sentence. Exception: retain
   if the silence is itself the point of analysis (e.g., a conspicuous
   absence among commentators who all address a crux).

5. HEBREW SCRIPT. Hebrew words in running text must use Hebrew Unicode
   characters. Transliterations in parentheses as pronunciation aids
   are fine and should be preserved. If a Hebrew letter name has been
   substituted for the character itself within Hebrew text, restore the
   character. Fix inconsistent vowel pointing within a single word.

6. WEAK CROSS-CULTURAL PARALLELS. If a literary parallel from outside
   the biblical/rabbinic tradition is introduced the connection should feel strong and not forced. Keep parallels where the connection is substantive and
   the contrast (if any) genuinely illuminates the psalm's distinctive
   theological move.

7. FACTUAL AND TEXTUAL ACCURACY. Verify claims about biblical texts
   against the actual text. If the commentary claims two passages share
   identical phrasing, check that claim. If a verse is described as "third-person" or "first-person," check that claim. Correct factual
   errors; do not remove the observation if it can be salvaged with
   accurate wording.

8. HEBREW GRAMMAR BLOAT. The audience are NOT grammarians! The more technical the grammatial statement, the more it must be earned.
If a Hebrew verb or noun is annotated with
grammatical parsing (esp. stem name)
   and the grammatical label adds no interpretive value, remove the
   label while keeping the translation and any interpretive point.
   Retain grammar labels ONLY when the form itself is the point of
   analysis (e.g., naming the Hiphil because causation matters, or
   noting a Niphal because passivity is the insight). Remove labels
   that are pure annotation — e.g., "(Niphal perfect, third-person
   plural)" when the commentary makes no interpretive use of that
   information. Terms like 'first persion' and 'pleural' are fine if they are relevant to the point being made.

9. STRAINED ARGUMENTS AND POORLY REASONED CLAIMS. Claims must be convincing! If the commentary
   makes an argument (e.g. about a specificausal chain, progression,
   contrast, equivalence, use of a poetic device. etc.) check whether the evidence supports the claim.
    Throughout, ask yourself - does this argument actually hold water?
    Examples of common failures:
   (a) REVERSED CAUSATION. A chain like "divine wrath → sin → folly"
       presents effects as causes. If folly leads to sin which
       provokes wrath, the arrows point the wrong way. Reverse the
       chain or (usually better) reword the argument.
   (b) NON SEQUITUR CONCLUSIONS. A paragraph builds an observation
       (wordplay, intertextual link, structural pattern) but then
       draws a conclusion that does not follow from the evidence
       presented, or overstates what the evidence supports.
   (c) STRAINED INTERTEXTUAL LOGIC. Citing a parallel passage and
       asserting a relationship (influence, allusion, contrast) that
       the shared language does not actually sustain.
   Do not remove arguments that can be salvaged; fix them. If the argument
   cannot be salvaged, remove entirely but maintain smooth flow of the text.

CRITICAL FORMATTING RULES — YOU MUST OBEY THESE:

- Do NOT change any markdown header levels (e.g., ##, ###, ####).
- Do NOT change **Verse N** or **Verses N–M** header formatting.
- Do NOT remove, add, or modify the ---LITURGICAL-SECTION-START--- marker.
- Do NOT modify Hebrew verse text lines that appear alone on their own line
  before verse commentary paragraphs. These are structural elements.
- Do NOT alter markdown bold (**text**) or italic (*text*) markers unless
  you are correcting the *content* inside them.
- Do NOT change backtick formatting (used for phonetic transcriptions).
- Do NOT change verse reference formats like (vv. 14–15) or (v. 10).
- Do NOT alter parenthetical Hebrew transliterations.
- Do NOT restructure the liturgical sections (marked by ---LITURGICAL-SECTION-START---).
- Do NOT revert or alter modified divine names (e.g., Kel, Elokim, Hashem, G-d, L-rd, and their Hebrew equivalents like קֵל, אלקים, ה׳, צבקות, שקי, אלוק). Leave them exactly as written.
- Preserve all line breaks and paragraph structure exactly as given.

After the corrected text, append a "## Changes" section listing each change
with its category number and a one-line explanation. If no changes are needed,
still append a "## Changes" section stating "No changes required."
"""


# =============================================================================
# COPY EDITOR CLASS
# =============================================================================

class CopyEditor:
    """Applies the 9-category error taxonomy to existing psalm commentary."""

    DEFAULT_MODEL = "claude-opus-4-6"

    def __init__(self, model: str = None, logger=None, cost_tracker=None):
        self.model = model or self.DEFAULT_MODEL
        self.logger = logger or get_logger("copy_editor")
        self.client = anthropic.Anthropic()
        self.cost_tracker = cost_tracker or CostTracker()

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def edit_commentary(
        self,
        psalm_number: int,
        input_file: Optional[Path] = None,
        output_dir: Optional[Path] = None,
    ) -> Dict[str, str]:
        """
        Run the copy editor on an existing psalm commentary.

        Args:
            psalm_number: The psalm number (e.g., 38).
            input_file: Path to print_ready.md. Defaults to standard location.
            output_dir: Where to save outputs. Defaults to psalm's output dir.

        Returns:
            Dict with keys: 'edited_file', 'changes_file', 'diff_file', 'changes_summary'
        """
        # Resolve paths
        psalm_dir = Path(f"output/psalm_{psalm_number}")
        if input_file is None:
            input_file = psalm_dir / f"psalm_{psalm_number:03d}_print_ready.md"
        if output_dir is None:
            output_dir = psalm_dir

        if not input_file.exists():
            raise FileNotFoundError(f"Commentary file not found: {input_file}")

        self.logger.info(f"═══ COPY EDITOR — Psalm {psalm_number} ═══")
        self.logger.info(f"Input: {input_file}")

        # 1. Load and parse the file into zones
        full_text = input_file.read_text(encoding='utf-8')
        zones = self._parse_zones(full_text, psalm_number)

        # 2. Extract editable content
        editable_content = self._assemble_editable_content(zones)
        self.logger.info(f"Editable content: {len(editable_content):,} chars")

        # 3. Call the LLM
        edited_content, raw_response, usage = self._call_editor(editable_content, psalm_number)

        # 4. Separate corrected text from Changes section
        corrected_text, changes_text = self._split_changes(edited_content)

        # 5. Validate structural integrity
        self._validate_structure(editable_content, corrected_text, psalm_number)

        # 6. Reassemble the full document
        full_edited = self._reassemble(zones, corrected_text)

        # 7. Generate diff
        diff_text = self._generate_diff(editable_content, corrected_text, psalm_number)

        # 8. Save output files
        prefix = f"psalm_{psalm_number:03d}"
        edited_path = output_dir / f"{prefix}_copy_edited.md"
        changes_path = output_dir / f"{prefix}_copy_edit_changes.md"
        diff_path = output_dir / f"{prefix}_copy_edit_diff.md"

        edited_path.write_text(full_edited, encoding='utf-8')
        changes_path.write_text(changes_text, encoding='utf-8')
        diff_path.write_text(diff_text, encoding='utf-8')

        self.logger.info(f"Saved: {edited_path}")
        self.logger.info(f"Saved: {changes_path}")
        self.logger.info(f"Saved: {diff_path}")

        # 9. Print cost summary
        changes_count = self._count_changes(changes_text)
        self._print_summary(psalm_number, usage, changes_count, changes_text)

        return {
            'edited_file': str(edited_path),
            'changes_file': str(changes_path),
            'diff_file': str(diff_path),
            'changes_summary': changes_text,
        }

    # -------------------------------------------------------------------------
    # Zone parsing — split print_ready.md into protected/editable zones
    # -------------------------------------------------------------------------

    def _parse_zones(self, text: str, psalm_number: int) -> list:
        """
        Parse print_ready.md into structural zones.

        Each zone is a dict: {'type': 'protected'|'editable', 'label': str, 'content': str}

        Structure of print_ready.md:
          # Commentary on Psalm N           <- protected header
          ---                               <- protected
          ## Introduction                   <- protected header
          [intro + liturgical content]      <- EDITABLE (intro_body)
          ---                               <- protected
          ## Psalm N                        <- protected
          [psalm text]                      <- protected
          ---                               <- protected
          ## Verse-by-Verse Commentary      <- protected header
          [verse commentary]                <- EDITABLE (verses_body)
          ---                               <- protected
          ## Methodological...              <- protected (entire section)
        """
        zones = []

        # Normalize line endings
        text = text.replace('\r\n', '\n')

        # Find section boundaries using regex
        # Pattern: ## Header at start of line
        section_pattern = re.compile(r'^(## .+)$', re.MULTILINE)
        sections = list(section_pattern.finditer(text))

        if len(sections) < 3:
            self.logger.warning(f"Expected at least 3 ## sections, found {len(sections)}")

        # Identify key section positions
        intro_idx = None
        psalm_idx = None
        verse_idx = None
        method_idx = None

        for i, m in enumerate(sections):
            header = m.group(1)
            if header.startswith('## Introduction'):
                intro_idx = i
            elif header.startswith(f'## Psalm {psalm_number}') or header.startswith(f'## Psalm'):
                psalm_idx = i
            elif header.startswith('## Verse-by-Verse Commentary') or header.startswith('## Verse'):
                verse_idx = i
            elif header.startswith('## Methodological'):
                method_idx = i

        if intro_idx is None or verse_idx is None:
            raise ValueError(f"Could not find required sections in print_ready.md. Found: {[m.group(1) for m in sections]}")

        # Build zones
        # Everything before "## Introduction" header → protected
        intro_start = sections[intro_idx].start()
        if intro_start > 0:
            zones.append({
                'type': 'protected',
                'label': 'preamble',
                'content': text[:intro_start]
            })

        # "## Introduction" header → protected
        intro_header_end = sections[intro_idx].end() + 1  # +1 for newline
        zones.append({
            'type': 'protected',
            'label': 'intro_header',
            'content': text[intro_start:intro_header_end]
        })

        # Intro body + liturgical content (from after header to before psalm section separator)
        # Find the --- separator before psalm section
        if psalm_idx is not None:
            psalm_start = sections[psalm_idx].start()
            # Find the --- right before ## Psalm
            sep_before_psalm = text.rfind('\n---\n', intro_header_end, psalm_start)
            if sep_before_psalm == -1:
                sep_before_psalm = text.rfind('\n---', intro_header_end, psalm_start)
            if sep_before_psalm == -1:
                # No separator found; use psalm start directly
                intro_body_end = psalm_start
            else:
                intro_body_end = sep_before_psalm + 1  # include the newline before ---

            zones.append({
                'type': 'editable',
                'label': 'intro_body',
                'content': text[intro_header_end:intro_body_end]
            })

            # Separator + psalm section (protected through to verse commentary header)
            verse_start = sections[verse_idx].start()
            verse_header_end = sections[verse_idx].end() + 1
            zones.append({
                'type': 'protected',
                'label': 'psalm_section',
                'content': text[intro_body_end:verse_header_end]
            })

        else:
            # No psalm text section — intro goes directly to verse commentary
            verse_start = sections[verse_idx].start()
            verse_header_end = sections[verse_idx].end() + 1

            # Find separator before verse section
            sep_before_verse = text.rfind('\n---\n', intro_header_end, verse_start)
            if sep_before_verse == -1:
                intro_body_end = verse_start
            else:
                intro_body_end = sep_before_verse + 1

            zones.append({
                'type': 'editable',
                'label': 'intro_body',
                'content': text[intro_header_end:intro_body_end]
            })
            zones.append({
                'type': 'protected',
                'label': 'verse_header',
                'content': text[intro_body_end:verse_header_end]
            })

        # Verse commentary body (editable)
        if method_idx is not None:
            method_start = sections[method_idx].start()
            # Find separator before methodology
            sep_before_method = text.rfind('\n---\n', verse_header_end, method_start)
            if sep_before_method == -1:
                verse_body_end = method_start
            else:
                verse_body_end = sep_before_method + 1

            zones.append({
                'type': 'editable',
                'label': 'verses_body',
                'content': text[verse_header_end:verse_body_end]
            })

            # Everything from separator through end → protected
            zones.append({
                'type': 'protected',
                'label': 'methodology',
                'content': text[verse_body_end:]
            })
        else:
            # No methodology section — everything after verse header is verse body
            zones.append({
                'type': 'editable',
                'label': 'verses_body',
                'content': text[verse_header_end:]
            })

        # Log zones
        for z in zones:
            self.logger.info(f"  Zone [{z['type']:9s}] {z['label']:15s} — {len(z['content']):,} chars")

        return zones

    def _assemble_editable_content(self, zones: list) -> str:
        """Assemble editable zones into a single text block for the LLM."""
        parts = []
        for z in zones:
            if z['type'] == 'editable':
                parts.append(z['content'])
        return '\n'.join(parts)

    def _reassemble(self, zones: list, corrected_text: str) -> str:
        """
        Reassemble the full document by replacing editable zones with corrected content.

        The corrected_text contains the edited intro_body and verses_body concatenated.
        We need to split it back into the original editable zones.
        """
        editable_labels = [z['label'] for z in zones if z['type'] == 'editable']
        original_editables = {z['label']: z['content'] for z in zones if z['type'] == 'editable'}

        if len(editable_labels) == 2 and 'intro_body' in editable_labels and 'verses_body' in editable_labels:
            # Split the corrected text back into intro_body and verses_body
            # The verses_body starts with **Verse 1** or **Verse** pattern
            verse_start_pattern = re.compile(r'^\*\*Verse[s]?\s+\d+', re.MULTILINE)
            match = verse_start_pattern.search(corrected_text)

            if match:
                split_pos = match.start()
                corrected_intro = corrected_text[:split_pos]
                corrected_verses = corrected_text[split_pos:]
            else:
                # Fallback: use original proportional split
                self.logger.warning("Could not find verse boundary in corrected text; using proportional split")
                orig_intro_len = len(original_editables['intro_body'])
                orig_total = sum(len(v) for v in original_editables.values())
                ratio = orig_intro_len / orig_total if orig_total > 0 else 0.5
                split_pos = int(len(corrected_text) * ratio)
                corrected_intro = corrected_text[:split_pos]
                corrected_verses = corrected_text[split_pos:]

            corrected_map = {'intro_body': corrected_intro, 'verses_body': corrected_verses}
        elif len(editable_labels) == 1:
            corrected_map = {editable_labels[0]: corrected_text}
        else:
            # Multiple editable zones — just use proportional split
            self.logger.warning(f"Unexpected editable zones: {editable_labels}")
            corrected_map = {editable_labels[0]: corrected_text}

        # Reassemble
        result_parts = []
        for z in zones:
            if z['type'] == 'protected':
                result_parts.append(z['content'])
            else:
                result_parts.append(corrected_map.get(z['label'], z['content']))

        return ''.join(result_parts)

    # -------------------------------------------------------------------------
    # LLM call
    # -------------------------------------------------------------------------

    def _call_editor(self, editable_content: str, psalm_number: int) -> Tuple[str, str, dict]:
        """Call Claude Opus 4.6 with the copy editor prompt. Retries on connection errors."""
        self.logger.info(f"Calling {self.model} with adaptive thinking...")

        user_message = f"""Here is the commentary for Psalm {psalm_number}. Apply the copy editing rules from your system prompt. Return the FULL corrected text followed by a ## Changes section.

{editable_content}"""

        max_retries = 3
        retry_delays = [10, 30, 60]  # seconds between retries

        for attempt in range(max_retries):
            try:
                start_time = time.time()

                # Use streaming (required for Opus 4.6 long generations)
                full_text = ""
                thinking_text = ""
                usage_data = {}
                last_progress_time = time.time()
                progress_interval = 5  # seconds between progress updates

                with self.client.messages.stream(
                    model=self.model,
                    max_tokens=65536,
                    thinking={
                        "type": "adaptive"
                    },
                    system=COPY_EDITOR_SYSTEM_PROMPT,
                    messages=[
                        {"role": "user", "content": user_message}
                    ]
                ) as stream:
                    for event in stream:
                        if hasattr(event, 'type'):
                            if event.type == 'content_block_delta':
                                if hasattr(event.delta, 'text'):
                                    full_text += event.delta.text
                                elif hasattr(event.delta, 'thinking'):
                                    thinking_text += event.delta.thinking

                        # Periodic progress update
                        now = time.time()
                        if now - last_progress_time >= progress_interval:
                            elapsed = now - start_time
                            if thinking_text and not full_text:
                                phase = "thinking"
                                chars = len(thinking_text)
                            else:
                                phase = "writing"
                                chars = len(full_text)
                            self.logger.info(
                                f"  ⏳ {elapsed:.0f}s — {phase}: {chars:,} chars received"
                            )
                            last_progress_time = now

                    # Get final message for usage stats
                    final_message = stream.get_final_message()
                    if final_message and final_message.usage:
                        usage_data = {
                            'input_tokens': final_message.usage.input_tokens,
                            'output_tokens': final_message.usage.output_tokens,
                        }
                        if hasattr(final_message.usage, 'cache_creation_input_tokens'):
                            usage_data['cache_creation_input_tokens'] = final_message.usage.cache_creation_input_tokens
                        if hasattr(final_message.usage, 'cache_read_input_tokens'):
                            usage_data['cache_read_input_tokens'] = final_message.usage.cache_read_input_tokens

                elapsed = time.time() - start_time
                self.logger.info(f"Response received in {elapsed:.1f}s")

                if thinking_text:
                    self.logger.info(f"Thinking tokens used: ~{len(thinking_text) // 4} tokens")

                # Track cost
                input_tokens = usage_data.get('input_tokens', 0)
                output_tokens = usage_data.get('output_tokens', 0)
                self.cost_tracker.add_usage(self.model, input_tokens=input_tokens, output_tokens=output_tokens)
                cost_breakdown = self.cost_tracker.calculate_cost(self.model)
                cost = cost_breakdown['total_cost']
                self.logger.info(f"Tokens: {input_tokens:,} in / {output_tokens:,} out — Cost: ${cost:.4f}")

                usage_data['cost'] = cost
                usage_data['elapsed_seconds'] = elapsed

                # Save debug files
                debug_dir = Path("output/debug")
                debug_dir.mkdir(parents=True, exist_ok=True)
                (debug_dir / f"copy_editor_thinking_psalm_{psalm_number}.txt").write_text(
                    thinking_text, encoding='utf-8'
                )
                (debug_dir / f"copy_editor_response_psalm_{psalm_number}.txt").write_text(
                    full_text, encoding='utf-8'
                )

                return full_text, thinking_text, usage_data

            except (ConnectionError, OSError, Exception) as e:
                error_name = type(e).__name__
                # Only retry on connection-related errors
                is_connection_error = any(kw in str(e).lower() for kw in [
                    'connection', 'timeout', 'read error', '10054', 'reset',
                    'closed', 'eof', 'broken pipe'
                ])

                if not is_connection_error:
                    raise  # Re-raise non-connection errors immediately

                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    self.logger.warning(
                        f"⚠️  {error_name} on attempt {attempt + 1}/{max_retries}: {e}"
                    )
                    self.logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    self.logger.error(
                        f"❌ {error_name} on attempt {attempt + 1}/{max_retries}: {e}"
                    )
                    raise

    # -------------------------------------------------------------------------
    # Response parsing
    # -------------------------------------------------------------------------

    def _split_changes(self, response: str) -> Tuple[str, str]:
        """Split the LLM response into corrected text and Changes section."""
        # Look for ## Changes header
        changes_pattern = re.compile(r'^## Changes\s*$', re.MULTILINE)
        match = changes_pattern.search(response)

        if match:
            corrected = response[:match.start()].rstrip('\n')
            changes = response[match.start():]
        else:
            self.logger.warning("No '## Changes' section found in response")
            corrected = response
            changes = "## Changes\n\nNo changes section was returned by the editor.\n"

        return corrected, changes

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def _validate_structure(self, original: str, corrected: str, psalm_number: int):
        """Validate that corrected text preserves critical structural elements."""
        checks = {
            'Liturgical marker': '---LITURGICAL-SECTION-START---',
        }

        # Check verse headers
        orig_verse_headers = re.findall(r'\*\*Verse[s]?\s+[\d–\-]+\*\*', original)
        edit_verse_headers = re.findall(r'\*\*Verse[s]?\s+[\d–\-]+\*\*', corrected)

        if len(orig_verse_headers) != len(edit_verse_headers):
            self.logger.warning(
                f"⚠️  Verse header count mismatch: {len(orig_verse_headers)} → {len(edit_verse_headers)}"
            )
        else:
            self.logger.info(f"✅ Verse headers preserved: {len(orig_verse_headers)}")

        # Check liturgical sub-headers
        orig_lit = re.findall(r'####\s+(?:Full|Key|Phrases)', original)
        edit_lit = re.findall(r'####\s+(?:Full|Key|Phrases)', corrected)

        if len(orig_lit) != len(edit_lit):
            self.logger.warning(f"⚠️  Liturgical subheader count mismatch: {len(orig_lit)} → {len(edit_lit)}")
        else:
            self.logger.info(f"✅ Liturgical subheaders preserved: {len(orig_lit)}")

        # Check fixed markers
        for name, marker in checks.items():
            if marker in original and marker not in corrected:
                self.logger.warning(f"⚠️  {name} MISSING from corrected text!")
            elif marker in original:
                self.logger.info(f"✅ {name} preserved")

    # -------------------------------------------------------------------------
    # Diff generation
    # -------------------------------------------------------------------------

    def _generate_diff(self, original: str, corrected: str, psalm_number: int) -> str:
        """Generate a readable diff between original and corrected content."""
        # Normalize trailing whitespace to avoid phantom diffs from
        # the LLM not reproducing invisible trailing spaces
        orig_lines = [line.rstrip() + '\n' for line in original.splitlines()]
        edit_lines = [line.rstrip() + '\n' for line in corrected.splitlines()]

        diff = difflib.unified_diff(
            orig_lines,
            edit_lines,
            fromfile=f"psalm_{psalm_number:03d}_print_ready.md (original)",
            tofile=f"psalm_{psalm_number:03d}_copy_edited.md (edited)",
            lineterm=''
        )

        diff_lines = list(diff)

        if not diff_lines:
            return f"# Copy Editor Diff — Psalm {psalm_number}\n\nNo differences found. The commentary passed copy editing without changes.\n"

        # Count changes
        additions = sum(1 for l in diff_lines if l.startswith('+') and not l.startswith('+++'))
        deletions = sum(1 for l in diff_lines if l.startswith('-') and not l.startswith('---'))

        header = f"# Copy Editor Diff — Psalm {psalm_number}\n\n"
        header += f"**Lines added:** {additions}  \n"
        header += f"**Lines removed:** {deletions}  \n\n"
        header += "```diff\n"
        footer = "\n```\n"

        return header + ''.join(diff_lines) + footer

    # -------------------------------------------------------------------------
    # Summary and reporting
    # -------------------------------------------------------------------------

    def _count_changes(self, changes_text: str) -> Dict[str, int]:
        """Count changes by category from the Changes section."""
        counts = {f"Category {i}": 0 for i in range(1, 10)}
        counts['total'] = 0

        # Look for patterns like "1." or "Category 1" or "[1]" etc.
        for line in changes_text.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            for i in range(1, 10):
                if re.search(rf'(?:^|\b){i}[.:\])]', line) or f'Category {i}' in line:
                    counts[f'Category {i}'] += 1
                    counts['total'] += 1
                    break

        return counts

    def _print_summary(self, psalm_number: int, usage: dict, changes_count: dict, changes_text: str):
        """Print a formatted summary of the copy edit run."""
        print("\n" + "=" * 60)
        print(f"  COPY EDITOR SUMMARY - Psalm {psalm_number}")
        print("=" * 60)
        print(f"  Model: {self.model}")
        print(f"  Input tokens:  {usage.get('input_tokens', 0):,}")
        print(f"  Output tokens: {usage.get('output_tokens', 0):,}")
        print(f"  Cost: ${usage.get('cost', 0):.4f}")
        print(f"  Time: {usage.get('elapsed_seconds', 0):.1f}s")
        print()
        print(f"  Total changes: {changes_count.get('total', 0)}")
        for i in range(1, 10):
            cat_labels = {
                1: "Structural claims",
                2: "Internal inconsistencies",
                3: "Form/content confusion",
                4: "Negative citations",
                5: "Hebrew script",
                6: "Weak parallels",
                7: "Factual/textual accuracy",
                8: "Hebrew grammar bloat",
                9: "Strained arguments",
            }
            count = changes_count.get(f'Category {i}', 0)
            if count > 0:
                print(f"    [{i}] {cat_labels[i]}: {count}")
        print("=" * 60 + "\n")
