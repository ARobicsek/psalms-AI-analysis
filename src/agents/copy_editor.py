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

CRITICAL READING STANCE — apply throughout:

For every substantive paragraph, pause and identify: (1) the core claim or
point being made, and (2) the evidence or reasoning offered for it. Then ask:
"If I were a thoughtful reader encountering this for the first time, would
this argument convince me? Can I follow each step of the reasoning without
needing outside knowledge the text hasn't provided?"

If the answer is no — if there is a gap between evidence and conclusion, if
a comparison feels forced, if a conjunction implies a tension that doesn't
exist, if a scholarly citation leads to a conclusion through steps the text
doesn't spell out — then the paragraph contains an error. Diagnose it using
the categories below and fix it.

This stance catches problems that category-level pattern-matching misses:
arguments that are technically well-formed but substantively unconvincing.

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
   the biblical/rabbinic tradition is introduced, the connection must run
   deeper than a shared word or surface concept. Test: does the parallel
   illuminate something specific about the psalm? If the two contexts are so different that the comparison
   requires extensive qualification ("but where X does Y, the psalmist
   does Z"), the parallel is likely obscuring rather than illuminating.
   Keep parallels where the connection is substantive and the contrast
   (if any) genuinely illuminates the psalm's distinctive theological
   move. Remove or replace parallels that share only a keyword.

7. FACTUAL AND TEXTUAL ACCURACY. Verify claims about biblical texts
   against the actual text. If the commentary claims two passages share
   identical phrasing, check that claim. If a verse is described as "third-person" or "first-person," check that claim. Correct factual
   errors; do not remove the observation if it can be salvaged with
   accurate wording.

8. HEBREW GRAMMAR BLOAT. The audience are NOT grammarians! The more technical the grammatical statement, the more it must be earned.
If a Hebrew verb or noun is annotated with
grammatical parsing (esp. stem name)
   and the grammatical label adds no interpretive value, remove the
   label while keeping the translation and any interpretive point.
   Retain grammar labels ONLY when the form itself is the point of
   analysis (e.g., naming the Hiphil because causation matters, or
   noting a Niphal because passivity is the insight). Remove labels
   that are pure annotation — e.g., "(Niphal perfect, third-person
   plural)" when the commentary makes no interpretive use of that
   information. Terms like 'first person' and 'plural' are fine if they are relevant to the point being made.

9. STRAINED ARGUMENTS AND POORLY REASONED CLAIMS. Claims must be convincing! If the commentary
   makes an argument (e.g. about a specific causal chain, progression,
   contrast, equivalence, use of a poetic device, etc.) check whether the evidence supports the claim.
    Throughout, ask yourself — does this argument actually hold water?
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
   (d) FALSE CONTRASTS. A sentence uses "yet," "but," "however,"
       "nevertheless," or "although" to imply a tension or
       contradiction between two statements — but the two statements
       are not actually in tension. If A does not contradict or
       complicate B, then linking them with an adversative conjunction
       is misleading. Test: cover the conjunction and read the two
       statements — are they complementary rather than opposed? If so,
       the contrast is false. Remove the false contrast or replace the
       conjunction with a neutral connector ("and," "moreover," a
       semicolon).
   (e) OVERCLAIMED SCOPE. A sentence claims a verse or image "spans
       the entire cosmos," "encompasses all of human experience,"
       "covers the full range of X," or uses similar totalizing
       language — but the actual evidence in the paragraph is much
       more limited. Scale the claim down to match the evidence.
   (f) OPAQUE SCHOLARLY LOGIC. A rabbinic or scholarly source is cited
       and a conclusion is drawn, but the reasoning that connects the
       source to the conclusion is not explained. The reader cannot
       follow the argument without already knowing the source. Test:
       can you explain, from what is written in the text alone, each
       logical step from citation to conclusion? If a step requires
       knowledge the text does not provide, the logic is opaque.
       Either fill in the missing logical steps so the reader can
       follow, or remove the citation if the logic cannot be made
       clear in a sentence or two.
   (g) FACTUALLY WRONG ANALOGIES. A comparison to the physical world
       or common experience is factually incorrect (e.g., calling
       head-hairs "the most countable thing on the human body" when
       fingers and toes are far more countable). Fix the analogy or
       remove it.
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

After the corrected text, append a "## Changes" section. Number each change
and include:
- Category number(s) in square brackets
- The verse number or section where the change occurs (e.g., "Verse 6",
  "Introduction", "Liturgical — Full Psalm")
- A brief description of what was changed
- A sentence explaining WHY the change was needed — what was wrong with the
  original and what principle or evidence motivated the correction

Format example:
1. [8] **Verse 2**: Removed "Hiphil participle" label from מַשְׂכִּיל — the
   stem name wasn't driving any interpretive point; it added grammatical jargon
   without illumination.
2. [7] **Verse 3**: Corrected LXX rendering from plural "hands of enemies" to
   singular "hands of his enemy" — the LXX reads ἐχθροῦ αὐτοῦ (singular).
3. [6] **Verse 2**: Removed Whitman comparison — the parallel shared only a
   surface keyword ("attention") and required extensive qualification,
   obscuring rather than illuminating the psalm's point.

If no changes are needed, still append "## Changes\nNo changes required."
"""


# =============================================================================
# COPY EDITOR CLASS
# =============================================================================

class CopyEditor:
    """Applies the 9-category error taxonomy to existing psalm commentary."""

    # Default model for copy editing (requires high nuance and precision)
    DEFAULT_MODEL = "gpt-5.4"

    def __init__(self, model: str = None, logger=None, cost_tracker=None):
        self.model = model or self.DEFAULT_MODEL
        self.logger = logger or get_logger("copy_editor")
        self.cost_tracker = cost_tracker or CostTracker()
        
        self.anthropic_client = None
        self.openai_client = None
        
        if "gpt" in self.model.lower() or self.model.startswith("o"):
            from openai import OpenAI
            self.openai_client = OpenAI()
        else:
            self.anthropic_client = anthropic.Anthropic()

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def edit_commentary(
        self,
        psalm_number: int,
        input_file: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        supplementary_prompt: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Run the copy editor on an existing psalm commentary.

        Args:
            psalm_number: The psalm number (e.g., 38).
            input_file: Path to print_ready.md. Defaults to standard location.
            output_dir: Where to save outputs. Defaults to psalm's output dir.
            supplementary_prompt: Optional extra context (e.g., citation verification
                report) to append to the LLM prompt.

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
        edited_content, raw_response, usage = self._call_editor(
            editable_content, psalm_number,
            supplementary_prompt=supplementary_prompt,
        )

        # 3b. Strip any echoed supplementary prompt from the response
        edited_content = self._strip_echoed_supplementary(edited_content)

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
        # Add cross-reference to diff file in changes output
        if changes_text.startswith('## Changes'):
            changes_output = changes_text.replace(
                '## Changes\n',
                f'## Changes\n*For exact before/after text, see [{prefix}_copy_edit_diff.md]({prefix}_copy_edit_diff.md).*\n\n',
                1
            )
        else:
            changes_output = changes_text
        changes_path.write_text(changes_output, encoding='utf-8')
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

    def _call_editor(self, editable_content: str, psalm_number: int,
                     supplementary_prompt: Optional[str] = None) -> Tuple[str, str, dict]:
        """Call Claude Opus 4.6 with the copy editor prompt. Retries on connection errors."""
        self.logger.info(f"Calling {self.model} with adaptive thinking...")

        user_message = f"""Here is the commentary for Psalm {psalm_number}. Apply the copy editing rules from your system prompt. Return the FULL corrected text followed by a ## Changes section.

{editable_content}"""

        # Append supplementary context (e.g., citation verification report)
        if supplementary_prompt:
            user_message += f"\n\n{supplementary_prompt}"
            self.logger.info(f"Appended supplementary prompt ({len(supplementary_prompt):,} chars)")

        max_retries = 3
        retry_delays = [10, 30, 60]  # seconds between retries

        for attempt in range(max_retries):
            try:
                start_time = time.time()

                full_text = ""
                thinking_text = ""
                usage_data = {}
                last_progress_time = time.time()
                progress_interval = 5  # seconds between progress updates

                if self.openai_client:
                    kwargs = {
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": COPY_EDITOR_SYSTEM_PROMPT},
                            {"role": "user", "content": user_message}
                        ]
                    }
                    if "gpt-5" in self.model.lower() or self.model.startswith("o"):
                        kwargs["reasoning_effort"] = "high"
                        kwargs["max_completion_tokens"] = 65536
                    else:
                        kwargs["max_tokens"] = 16000
                        
                    response = self.openai_client.chat.completions.create(**kwargs)
                    full_text = response.choices[0].message.content
                    
                    reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0) or 0
                    if reasoning_tokens:
                        thinking_text = "Reasoning used " + str(reasoning_tokens) + " tokens."

                    usage_data = {
                        'input_tokens': getattr(response.usage, 'prompt_tokens', 0),
                        'output_tokens': getattr(response.usage, 'completion_tokens', 0),
                        'thinking_tokens': reasoning_tokens,
                    }
                else:
                    with self.anthropic_client.messages.stream(
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
                self.cost_tracker.add_usage(self.model, input_tokens=input_tokens, output_tokens=output_tokens,
                                            thinking_tokens=usage_data.get('thinking_tokens', 0))
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

    @staticmethod
    def _strip_echoed_supplementary(text: str) -> str:
        """Remove any echoed citation-check instructions the LLM copied into its output."""
        marker = "SCRIPTURE CITATION CHECK (automated"
        idx = text.find(marker)
        if idx == -1:
            return text
        # Find the end: the block ends at the last numbered issue line + blank,
        # or at the next major section (## Changes, or a verse/intro header).
        # Safest: cut from marker to the next "## " header or end of text.
        after = text[idx:]
        # Look for the next markdown heading that signals real content resumes
        end_match = re.search(r'^(?:## |\*\*Verse|\*\*Introduction|---)', after, re.MULTILINE)
        if end_match:
            remove_end = idx + end_match.start()
        else:
            remove_end = len(text)
        stripped = text[:idx] + text[remove_end:]
        return stripped.strip() + "\n"

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

        # Check for displaced liturgical key verse content
        # If the intro has #### Key Verses and Phrases but the content after it
        # is < 100 chars, the key verse entries may have been displaced
        if '#### Key Verses and Phrases' in corrected:
            key_verses_pos = corrected.find('#### Key Verses and Phrases')
            # Find the first **Verse N** header (start of verse commentary)
            first_verse_match = re.search(r'\*\*Verse[s]?\s+\d+', corrected[key_verses_pos:])
            if first_verse_match:
                content_between = corrected[key_verses_pos + len('#### Key Verses and Phrases'):key_verses_pos + first_verse_match.start()].strip()
                if len(content_between) < 100:
                    self.logger.warning(
                        f"⚠️  Liturgical key verse content may be displaced! "
                        f"Only {len(content_between)} chars between '#### Key Verses and Phrases' "
                        f"header and first **Verse** header. Expected substantial liturgical content here."
                    )

    # -------------------------------------------------------------------------
    # Diff generation
    # -------------------------------------------------------------------------

    def _generate_diff(self, original: str, corrected: str, psalm_number: int) -> str:
        """Generate a focused, word-level diff between original and corrected content."""
        # Normalize trailing whitespace
        orig_lines = [line.rstrip() for line in original.split('\n')]
        edit_lines = [line.rstrip() for line in corrected.split('\n')]

        # Track section context for each original line
        orig_sections = self._track_sections(orig_lines)

        # Match lines using SequenceMatcher
        sm = difflib.SequenceMatcher(None, orig_lines, edit_lines)

        changes = []

        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                continue

            if tag == 'replace':
                n_orig = i2 - i1
                n_edit = j2 - j1
                pairs = min(n_orig, n_edit)

                # Paired replacements — do word-level diff within each line
                for k in range(pairs):
                    oi = i1 + k
                    ei = j1 + k
                    if orig_lines[oi].rstrip() == edit_lines[ei].rstrip():
                        continue  # whitespace-only change
                    section = orig_sections[oi] if oi < len(orig_sections) else "Unknown"
                    word_changes = self._find_word_changes(orig_lines[oi], edit_lines[ei])
                    for wc in word_changes:
                        changes.append({
                            'section': section,
                            'before': wc['before'],
                            'after': wc['after'],
                        })

                # Extra original lines (deletions)
                for k in range(pairs, n_orig):
                    oi = i1 + k
                    if orig_lines[oi].strip():
                        section = orig_sections[oi] if oi < len(orig_sections) else "Unknown"
                        changes.append({
                            'section': section,
                            'before': self._truncate(orig_lines[oi], 200),
                            'after': '*(line removed)*',
                        })

                # Extra edited lines (insertions)
                for k in range(pairs, n_edit):
                    ei = j1 + k
                    if edit_lines[ei].strip():
                        changes.append({
                            'section': '(inserted)',
                            'before': '*(none)*',
                            'after': self._truncate(edit_lines[ei], 200),
                        })

            elif tag == 'delete':
                for idx in range(i1, i2):
                    if orig_lines[idx].strip():
                        section = orig_sections[idx] if idx < len(orig_sections) else "Unknown"
                        changes.append({
                            'section': section,
                            'before': self._truncate(orig_lines[idx], 200),
                            'after': '*(line removed)*',
                        })

            elif tag == 'insert':
                for idx in range(j1, j2):
                    if edit_lines[idx].strip():
                        changes.append({
                            'section': '(inserted)',
                            'before': '*(none)*',
                            'after': self._truncate(edit_lines[idx], 200),
                        })

        if not changes:
            return (
                f"# Copy Editor Diff — Psalm {psalm_number}\n\n"
                f"No differences found. The commentary passed copy editing without changes.\n"
            )

        # Format output
        prefix = f"psalm_{psalm_number:03d}"
        output = []
        output.append(f"# Copy Editor Diff — Psalm {psalm_number}\n")
        output.append(f"**{len(changes)} changes found**  ")
        output.append(
            f"See [{prefix}_copy_edit_changes.md]({prefix}_copy_edit_changes.md) "
            f"for rationale behind each change.\n"
        )

        for i, c in enumerate(changes, 1):
            output.append("---\n")
            output.append(f"### Diff {i} — {c['section']}\n")
            output.append(f"**Before:** {c['before']}  ")
            output.append(f"**After:** {c['after']}\n")

        return '\n'.join(output)

    def _track_sections(self, lines: list) -> list:
        """Track the section label for each line based on headers."""
        sections = []
        current_label = "Introduction"

        for line in lines:
            stripped = line.strip()
            verse_match = re.match(r'\*\*Verse[s]?\s+([\d–\-]+)\*\*', stripped)
            if verse_match:
                current_label = f"Verse {verse_match.group(1)}"
            elif stripped.startswith('#### '):
                sub = stripped.lstrip('# ').strip()
                current_label = f"Liturgical — {sub}"
            elif stripped.startswith('### '):
                current_label = stripped.lstrip('# ').strip()
            elif stripped == '---LITURGICAL-SECTION-START---':
                current_label = "Liturgical"
            sections.append(current_label)

        return sections

    def _find_word_changes(self, orig_line: str, edit_line: str) -> list:
        """Find word-level changes between two lines, returning focused before/after snippets.

        Merges nearby changes (within MERGE_GAP words) into a single diff entry
        so that one logical edit doesn't produce multiple scattered entries.
        """
        CONTEXT_WORDS = 12
        MAX_HIGHLIGHT_WORDS = 30
        MERGE_GAP = 6  # merge changes within this many words of each other

        orig_words = orig_line.split()
        edit_words = edit_line.split()
        sm = difflib.SequenceMatcher(None, orig_words, edit_words)

        # Collect non-equal opcodes
        raw_changes = []
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != 'equal':
                raw_changes.append((i1, i2, j1, j2))

        if not raw_changes:
            return []

        # Merge nearby changes so one logical edit = one diff entry
        merged = [list(raw_changes[0])]
        for i1, i2, j1, j2 in raw_changes[1:]:
            prev = merged[-1]
            gap = i1 - prev[1]  # gap in original between end of prev and start of current
            if gap <= MERGE_GAP:
                merged[-1] = [prev[0], i2, prev[2], j2]
            else:
                merged.append([i1, i2, j1, j2])

        # Build snippets for each merged change
        changes = []
        for i1, i2, j1, j2 in merged:
            # --- Build "before" snippet ---
            ctx_start = max(0, i1 - CONTEXT_WORDS)
            ctx_end = min(len(orig_words), i2 + CONTEXT_WORDS)

            highlighted = orig_words[i1:i2]
            if len(highlighted) > MAX_HIGHLIGHT_WORDS:
                hl_display = (
                    ' '.join(highlighted[:12]) + ' … '
                    + ' '.join(highlighted[-8:])
                )
            else:
                hl_display = ' '.join(highlighted)

            before_parts = []
            if ctx_start > 0:
                before_parts.append('...')
            ctx_before = orig_words[ctx_start:i1]
            if ctx_before:
                before_parts.append(' '.join(ctx_before))
            if hl_display:
                before_parts.append(f'**{hl_display}**')
            ctx_after = orig_words[i2:ctx_end]
            if ctx_after:
                before_parts.append(' '.join(ctx_after))
            if ctx_end < len(orig_words):
                before_parts.append('...')
            before_snippet = ' '.join(before_parts)

            # --- Build "after" snippet ---
            ectx_start = max(0, j1 - CONTEXT_WORDS)
            ectx_end = min(len(edit_words), j2 + CONTEXT_WORDS)

            highlighted_edit = edit_words[j1:j2]
            if len(highlighted_edit) > MAX_HIGHLIGHT_WORDS:
                hl_edit_display = (
                    ' '.join(highlighted_edit[:12]) + ' … '
                    + ' '.join(highlighted_edit[-8:])
                )
            else:
                hl_edit_display = ' '.join(highlighted_edit)

            after_parts = []
            if ectx_start > 0:
                after_parts.append('...')
            ectx_before = edit_words[ectx_start:j1]
            if ectx_before:
                after_parts.append(' '.join(ectx_before))
            if hl_edit_display:
                after_parts.append(f'**{hl_edit_display}**')
            ectx_after = edit_words[j2:ectx_end]
            if ectx_after:
                after_parts.append(' '.join(ectx_after))
            if ectx_end < len(edit_words):
                after_parts.append('...')
            after_snippet = ' '.join(after_parts)

            changes.append({
                'before': before_snippet,
                'after': after_snippet,
            })

        return changes

    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text to max_len characters with ellipsis."""
        if len(text) <= max_len:
            return text
        return text[:max_len] + '...'

    # -------------------------------------------------------------------------
    # Summary and reporting
    # -------------------------------------------------------------------------

    def _count_changes(self, changes_text: str) -> Dict[str, int]:
        """Count changes by category from the Changes section."""
        counts = {f"Category {i}": 0 for i in range(1, 10)}
        counts['total'] = 0

        for line in changes_text.split('\n'):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('*'):
                continue
            # Look for category markers in [N] or [N,M] format
            bracket_matches = re.findall(r'\[(\d+(?:,\s*\d+)*)\]', line)
            if bracket_matches:
                counts['total'] += 1
                for match in bracket_matches:
                    for num_str in match.split(','):
                        num = int(num_str.strip())
                        if 1 <= num <= 9:
                            counts[f'Category {num}'] += 1

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
