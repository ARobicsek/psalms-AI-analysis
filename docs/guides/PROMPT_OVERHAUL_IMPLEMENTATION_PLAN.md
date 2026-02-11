# Prompt Overhaul Implementation Plan

**Created:** Session 210 (2026-02-10)
**Purpose:** Fix seven identified quality problems in the master writer / college writer output
**Scope:** New v3 prompt file + test pipeline script (Phase 1: no original files touched). Merge into originals only after validation (Phase 2).
**Test strategy:** All changes live in NEW files only (`master_editor_v3.py` + `run_enhanced_pipeline_TEST.py`). Outputs go to `_TEST` suffixed files. Original `master_editor.py`, `master_editor_si.py`, and pipeline scripts are NEVER modified during testing.
**Primary pipeline:** `run_enhanced_pipeline.py` → `MasterEditorV2` from `master_editor.py` (this is the 95% use case). The SI pipeline is secondary and will be updated after validation.

---

## Table of Contents

1. [Problems Diagnosed](#problems-diagnosed)
2. [Files to Modify](#files-to-modify)
3. [Test Pipeline Setup](#test-pipeline-setup)
4. [Change 1: Eliminate Pipeline Language Leakage](#change-1-eliminate-pipeline-language-leakage)
5. [Change 2: Require Structural Outline Early](#change-2-require-structural-outline-early)
6. [Change 3: Mandate a Governing Argument](#change-3-mandate-a-governing-argument)
7. [Change 4: Redefine Essay/Commentary Relationship](#change-4-redefine-essaycommentary-relationship)
8. [Change 5: Enforce Insight Incorporation](#change-5-enforce-insight-incorporation)
9. [Change 6: Add "Coherence from Apparent Formlessness" Framing](#change-6-add-coherence-from-apparent-formlessness-framing)
10. [Change 7: Add Human Experience and Poetic Intentionality](#change-7-add-human-experience-and-poetic-intentionality)
11. [Change 8: Add "The One Thing" Closing Requirement](#change-8-add-the-one-thing-closing-requirement)
12. [Change 9: New Stylistic Guidance Example](#change-9-new-stylistic-guidance-example)
13. [Full Prompt Text: New Sections](#full-prompt-text-new-sections)
14. [Validation Checklist Updates](#validation-checklist-updates)
15. [Testing Protocol](#testing-protocol)

---

## Problems Diagnosed

| # | Problem | Root Cause | Fix |
|---|---------|------------|-----|
| 1 | Pipeline language leakage ("your macro thesis is right...") | Input sections labeled with pipeline terminology; prompt tells model to "engage the macro thesis" by name | Rename input sections; add explicit prohibition |
| 2 | Missing or misplaced structural outline | No explicit requirement for early placement | Add structural map requirement in first 300 words |
| 3 | Mini-essays instead of cohesive argument | Prompt lists 9 priorities as a checklist; model writes a section for each | Mandate a single governing argument with 2-3 sections max |
| 4 | Verse commentary feels redundant after essay | Essay scatters observations across all verses, leaving nothing for commentary to add | Redefine essay = argument, commentary = evidence room |
| 5 | Opus 4.6 insights not reliably incorporated | Insights buried in 108K tokens of input; no validation that they were used | Add checklist item; reformat insights prominently |
| 6 | Essays don't resolve the psalm into a coherent work | No instruction to show how apparent "word salad" of pious sentiments is actually skilled, intentional poetic craft | Add explicit framing instruction |
| 7 | Missing human connection, poetic intentionality, "why this psalm matters" | Prompt doesn't encourage connecting to recognizable human experience or treating the poet as an intentional craftsman | Add specific instructions |

---

## Files to Modify

### ⚠️ CRITICAL: DO NOT MODIFY ORIGINAL FILES DURING TESTING

During the testing phase, **only two new files are created**. The originals remain untouched:

| File | Action During Testing | Action After Validation |
|------|----------------------|------------------------|
| `src/agents/master_editor.py` | **DO NOT TOUCH** | Merge v3 prompts into it |
| `src/agents/master_editor_si.py` | **DO NOT TOUCH** | Update SI prompts to match (secondary) |
| `scripts/run_enhanced_pipeline.py` | **DO NOT TOUCH** | No changes needed |
| `scripts/run_si_pipeline.py` | **DO NOT TOUCH** | No changes needed |
| **`src/agents/master_editor_v3.py`** | **CREATE NEW** — contains new prompts + overridden methods | Delete after merging |
| **`scripts/run_enhanced_pipeline_TEST.py`** | **CREATE NEW** — imports from v3, writes `_TEST` output files | Delete after merging |

### Reference: What the original files contain (for context only)

**Primary pipeline** (`run_enhanced_pipeline.py`):

1. **`src/agents/master_editor.py`** — Contains:
   - `MASTER_WRITER_PROMPT` (line 766) — main audience writer prompt
   - `COLLEGE_WRITER_PROMPT` (line 1046) — college audience writer prompt
   - `MASTER_EDITOR_PROMPT_V2` (line 54) — editor-mode prompt
   - `COLLEGE_EDITOR_PROMPT_V2` (line 443) — college editor-mode prompt
   - `MasterEditorV2` class with:
     - `write_commentary()` — calls `_perform_writer_synthesis()` with `is_college=False`
     - `write_college_commentary()` — calls `_perform_writer_synthesis()` with `is_college=True`
     - `_perform_writer_synthesis()` (line 2011) — selects `MASTER_WRITER_PROMPT` or `COLLEGE_WRITER_PROMPT` based on `is_college`, formats inputs via `_format_analysis_for_prompt()`, calls model
     - `_format_analysis_for_prompt()` (line 2270) — injects `**Thesis:**`, `**Research Questions:**` labels
     - `_format_insights_for_prompt()` (line 2313) — formats curated insights

**Secondary pipeline** (`run_si_pipeline.py`) — update AFTER primary is validated:

2. **`src/agents/master_editor_si.py`** — Contains:
   - `MASTER_WRITER_PROMPT_SI` / `COLLEGE_WRITER_PROMPT_SI` — identical to base + SI directive
   - `MasterEditorSI` class inheriting from `MasterEditorV2`, with its own `_perform_writer_synthesis_si()` that references the SI prompt constants

---

## Test Pipeline Setup

### Create `scripts/run_enhanced_pipeline_TEST.py`

This is a copy of `run_enhanced_pipeline.py` (or `run_si_pipeline.py`, whichever is being used for the test psalms) with the following modifications:

**Option A (recommended): Minimal fork — just change output file suffixes**

1. Copy `scripts/run_enhanced_pipeline.py` → `scripts/run_enhanced_pipeline_TEST.py`
2. Change the import to use the v3 class:
   ```python
   # In run_enhanced_pipeline_TEST.py, change:
   from src.agents.master_editor import MasterEditorV2 as MasterEditor
   # to:
   from src.agents.master_editor_v3 import MasterEditorV3 as MasterEditor
   ```
   Everything else in the pipeline script refers to `MasterEditor` (the alias), so this one-line change swaps in the v3 class with zero other modifications to the pipeline logic.
3. Change ALL output file names to use `_TEST` suffix:
   ```python
   # Change these lines (around lines 208-225):
   edited_intro_file = output_path / f"psalm_{psalm_number:03d}_edited_intro_TEST.md"
   edited_verses_file = output_path / f"psalm_{psalm_number:03d}_edited_verses_TEST.md"
   edited_intro_college_file = output_path / f"psalm_{psalm_number:03d}_edited_intro_college_TEST.md"
   edited_verses_college_file = output_path / f"psalm_{psalm_number:03d}_edited_verses_college_TEST.md"
   docx_output_file = output_path / f"psalm_{psalm_number:03d}_commentary_TEST.docx"
   docx_output_college_file = output_path / f"psalm_{psalm_number:03d}_commentary_college_TEST.docx"
   ```
4. The pipeline should reuse existing macro, micro, research, and insights files (no need to regenerate those) by adding `--skip-macro --skip-micro --skip-insights` as defaults or making them always true.

**Option B: Parameter-based**

Add a `--test-mode` flag to the existing pipeline that appends `_TEST` to output filenames. Less clean but avoids a separate file.

**Recommendation:** Option A. A separate script file makes it impossible to accidentally overwrite production outputs, and the file can be deleted after testing is complete.

### New prompt file: `src/agents/master_editor_v3.py`

Create this as a NEW file containing:
- `MASTER_WRITER_PROMPT_V3` — the new main-audience prompt with all Changes 1-9
- `COLLEGE_WRITER_PROMPT_V3` — the new college-audience prompt with all Changes 1-9
- `MasterEditorV3` class inheriting from `MasterEditorV2`

This keeps the v2 prompts in `master_editor.py` entirely untouched during testing. After validation, the v3 prompts replace the v2 prompts in the original file and the v3 file is deleted.

**Why inherit from MasterEditorV2?** The primary pipeline (`run_enhanced_pipeline.py`) uses `MasterEditorV2` directly — no SI class involved. The v3 class inherits all the machinery (file loading, API calls, research trimming, cost tracking) and only overrides:
1. `_format_analysis_for_prompt()` — to fix pipeline-vocabulary labels
2. `_perform_writer_synthesis()` — to reference the V3 prompt constants instead of the V2 ones

**IMPORTANT — Override `_format_analysis_for_prompt`:**

`MasterEditorV2._format_analysis_for_prompt()` (in the ORIGINAL `master_editor.py`) injects labels like `**Thesis:**` and `**Research Questions:**` into the formatted text — which is part of the pipeline language problem.

The v3 class **MUST override this method** to use the new labels (`**Central Reading:**`, `**Open Questions:**`). Otherwise the prompt will say `### STRUCTURAL OVERVIEW` as the section header, but the injected content will still start with `**Thesis:**` — a contradictory signal.

**IMPORTANT — Override `_perform_writer_synthesis`:**

`MasterEditorV2._perform_writer_synthesis()` (line 2011) hard-codes references to the module-level constants `MASTER_WRITER_PROMPT` and `COLLEGE_WRITER_PROMPT`. The v3 class must override this method to reference `MASTER_WRITER_PROMPT_V3` and `COLLEGE_WRITER_PROMPT_V3` instead. The override is a near-copy of the original — just swap the two prompt constant names.

```python
from src.agents.master_editor import MasterEditorV2

# New V3 prompt constants defined here (see Changes 1-9 for full text)
MASTER_WRITER_PROMPT_V3 = """..."""
COLLEGE_WRITER_PROMPT_V3 = """..."""

class MasterEditorV3(MasterEditorV2):
    """v3 test version with overhauled prompts. DO NOT use in production."""

    def _format_analysis_for_prompt(self, analysis: Dict, analysis_type: str) -> str:
        """Override to use v3 labels (no pipeline terminology)."""
        if analysis_type == "macro":
            lines = []
            lines.append(f"**Central Reading:** {analysis.get('thesis_statement', 'N/A')}")
            lines.append(f"**Genre:** {analysis.get('genre', 'N/A')}")
            lines.append(f"**Context:** {analysis.get('historical_context', 'N/A')}")

            structure = analysis.get('structural_outline', [])
            if structure:
                lines.append("\n**Structure:**")
                for div in structure:
                    section = div.get('section', '')
                    theme = div.get('theme', '')
                    lines.append(f"  - {section}: {theme}")

            questions = analysis.get('research_questions', [])
            if questions:
                lines.append("\n**Open Questions:**")
                for i, q in enumerate(questions, 1):
                    lines.append(f"  {i}. {q}")

            return "\n".join(lines)

        elif analysis_type == "micro":
            lines = []
            verses = analysis.get('verse_commentaries', analysis.get('verses', []))

            for v in verses:
                verse_num = v.get('verse_number', v.get('verse', 0))
                commentary = v.get('commentary', '')
                lines.append(f"**Verse {verse_num}:** {commentary[:500]}...")

            questions = analysis.get('interesting_questions', [])
            if questions:
                lines.append("\n**Open Questions:**")
                for i, q in enumerate(questions, 1):
                    lines.append(f"  {i}. {q}")

            return "\n".join(lines)

        return str(analysis)

    def _perform_writer_synthesis(
        self,
        psalm_number, macro_analysis, micro_analysis, research_bundle,
        psalm_text, phonetic_section, curated_insights, analytical_framework,
        reader_questions, is_college
    ):
        """Override to use V3 prompt constants."""
        # Format common inputs
        macro_text = self._format_analysis_for_prompt(macro_analysis, "macro")
        micro_text = self._format_analysis_for_prompt(micro_analysis, "micro")
        insights_text = self._format_insights_for_prompt(curated_insights)

        # Select prompt and model — ONLY DIFFERENCE from parent: V3 constants
        if is_college:
            prompt_template = COLLEGE_WRITER_PROMPT_V3
            model = self.college_model
            debug_prefix = "college_writer_v3"
        else:
            prompt_template = MASTER_WRITER_PROMPT_V3
            model = self.model
            debug_prefix = "master_writer_v3"

        prompt = prompt_template.format(
            psalm_number=psalm_number,
            psalm_text=psalm_text,
            macro_analysis=macro_text,
            micro_analysis=micro_text,
            research_bundle=research_bundle,
            phonetic_section=phonetic_section,
            curated_insights=insights_text,
            analytical_framework=analytical_framework,
            reader_questions=reader_questions
        )

        # Save prompt for debugging
        from pathlib import Path
        prompt_file = Path(f"output/debug/{debug_prefix}_prompt_psalm_{psalm_number}.txt")
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_text(prompt, encoding='utf-8')
        self.logger.info(f"Saved {debug_prefix} prompt to {prompt_file}")

        # Call model (inherited methods handle the actual API call)
        if "claude" in model.lower():
            return self._call_claude_writer(model, prompt, psalm_number, debug_prefix)
        else:
            return self._call_gpt_writer(model, prompt, psalm_number, debug_prefix)
```

`write_commentary()` and `write_college_commentary()` do NOT need to be overridden — they call `self._perform_writer_synthesis()` which Python resolves to the v3 override automatically.

---

## Change 1: Eliminate Pipeline Language Leakage

### Problem
The model writes things like "The macro thesis you were given — that Psalm 33 is unified by the motif of God's word — stands up well" because:
- Input sections are labeled `### MACRO THESIS (structural analysis)` and `### MICRO DISCOVERIES (verse-level observations)` and `### PRIORITIZED INSIGHTS (FROM INSIGHT EXTRACTOR)`
- The Stage 1 instructions say "Engages the macro thesis critically"
- The stylistic example (line 866-870) shows a sentence that *begins* "While the macro thesis correctly identifies..."

### Changes Required

#### A. Rename input section headers in ALL FOUR writer prompts

**Current (in MASTER_WRITER_PROMPT, MASTER_WRITER_PROMPT_SI, COLLEGE_WRITER_PROMPT, COLLEGE_WRITER_PROMPT_SI):**
```
### MACRO THESIS (structural analysis)
{macro_analysis}

### MICRO DISCOVERIES (verse-level observations)
{micro_analysis}

### PRIORITIZED INSIGHTS (FROM INSIGHT EXTRACTOR)
{curated_insights}
```

**New:**
```
### STRUCTURAL OVERVIEW
{macro_analysis}

### VERSE-LEVEL NOTES
{micro_analysis}

### KEY INSIGHTS TO INCORPORATE
{curated_insights}
```

#### B. Override `_format_analysis_for_prompt` in the v3 class

The original method lives in `MasterEditorV2` (`master_editor.py` line 2270). **DO NOT modify the original.** Instead, override it in `MasterEditorV3` (in `master_editor_v3.py`).

The override changes these labels:
- `**Thesis:**` → `**Central Reading:**`
- `**Research Questions:**` → `**Open Questions:**`
- `**Interesting Questions:**` → `**Open Questions:**`

(Full override code is provided in the [Test Pipeline Setup](#test-pipeline-setup) section above.)

**Phase 2 (after validation):** Apply these same label changes to the original `_format_analysis_for_prompt` method in `master_editor.py` lines 2274, 2288, 2305.

#### C. Rewrite Stage 1 item #1 in MASTER_WRITER_PROMPT and MASTER_WRITER_PROMPT_SI

**Current (line 936 in SI, line 915 in base):**
```
1. **Engages the macro thesis critically**: You have FULL AUTHORITY to revise or reject it if evidence warrants. If it holds up, defend it; if flawed, offer an alternative.
```

**New:**
```
1. **Develops a governing argument about the psalm**: The STRUCTURAL OVERVIEW section below offers one reading. You may adopt it, revise it, or propose an entirely different reading based on the evidence. Either way, YOUR essay must present a coherent, original argument — not a response to someone else's analysis.
```

#### D. Rewrite the college equivalent

**Current (line 1153 in SI, line 1124 in base):**
```
- **Synthesize**: Combine Macro, Micro, Research, and Insights. Show how lexical evidence supports or challenges the thesis.
```

**New:**
```
- **Build an argument**: The background materials below offer structural observations and verse-level notes. Use them as raw material — adopt, revise, or discard as you see fit. Your essay must present a coherent, original argument that is entirely your own voice, not a response to an upstream analysis.
```

#### E. Add explicit prohibition — new RULE 11 in GROUND RULES section (all four prompts)

Add after RULE 10 (THE TRANSLATION TEST):

```
### RULE 11: YOU ARE A SCHOLAR, NOT A PIPELINE ENDPOINT

You are writing for publication. Your output must read as if written by a single, authoritative scholar — NOT as a response to an analytical brief.

**NEVER reference:**
- "The thesis," "the macro analysis," "the structural analysis," "the micro discoveries"
- "The research suggests," "the concordance data shows," "the insight extractor identified"
- "Your phonetic transcriptions," "the curated insights," "the research bundle"
- Any language that implies you are reviewing, editing, responding to, or building on someone else's prior analysis

**NEVER address the reader as if they have seen your source materials:**
- "As noted above," "the thesis you were given," "the heading gave you"

**INSTEAD:** Present all observations as YOUR OWN scholarly analysis. If the structural overview contains a good insight, adopt it seamlessly — don't credit it. You are the author. Write like one.
```

#### F. Rewrite the stylistic example (MASTER_WRITER_PROMPT line 866-871, MASTER_WRITER_PROMPT_SI line 887-891)

**Current:**
```
**Excessively "LLM-ish" (AVOID):**
"While the macro thesis correctly identifies this psalm as a 'liturgical polemic' that appropriates Baal theology, the evidence suggests an even more sophisticated literary achievement: Psalm 29 functions as a theological tour de force that systematically dismantles polytheistic cosmology..."

**Target style:**
"Scholars often describe Psalm 29 as a 'liturgical polemic,' a poem that co-opts the language of Canaanite storm-god worship to declare the supremacy of Israel's God. This is true, but it doesn't capture the poem's full artistry. The poet does more than just borrow; they dismantle and rebuild..."
```

**New:**
```
**Pipeline voice (FORBIDDEN):**
"The macro thesis correctly identifies this psalm as a 'liturgical polemic' that appropriates Baal theology, and the evidence supports this reading. The research bundle shows that the concordance data confirms..."

**Report voice (AVOID — sounds like a term paper):**
"Scholars often describe Psalm 29 as a 'liturgical polemic.' This paper will argue that the evidence suggests an even more sophisticated literary achievement..."

**Authorial voice (TARGET):**
"On first hearing, Psalm 29 sounds like a thunderstorm — seven peals of divine voice, each one shattering something. But listen again and you notice something stranger: the poet has taken the language of Canaanite storm-god worship and rebuilt it from the inside. Every attribute of Baal — the thunder, the shattered cedars, the writhing wilderness — now belongs to Israel's God. The poem doesn't just borrow; it annexes."
```

---

## Change 2: Require Structural Outline Early

### Problem
The prompt never explicitly requires a structural map of the psalm in the first portion of the essay. Sometimes one appears; sometimes it's buried or absent.

### Changes Required

#### A. Add structural map requirement to Stage 1 (MASTER_WRITER_PROMPT and SI variant)

**Insert as the FIRST item in the Stage 1 numbered list (before current item 1), renumbering all subsequent items:**

```
### STAGE 1: INTRODUCTION ESSAY (800-1200 words)

**HOOK FIRST—AND CONNECT TO READER QUESTIONS**: Open with something surprising, counterintuitive, or puzzling about this psalm. Look at the READER QUESTIONS—your hook should set up one or more of these questions. Avoid bland summary openings.

**STRUCTURAL MAP (within first 300 words)**: After your hook, give the reader a clear, concise map of how the psalm moves — its sections, its arc, its logic. Think of this as the legend on a museum guide: before the reader enters the detailed rooms, they need to see the floor plan. This should be brief (a short paragraph or a compact list) but decisive — it should make the psalm's architecture visible at a glance. The rest of your essay will then develop the most interesting aspects of this structure.

Write a scholarly introduction essay that:
1. **Develops a governing argument about the psalm**: [new text from Change 1C above]
2. **Synthesizes all sources**: ...
[etc., renumbered]
```

#### B. Add structural map requirement to Stage 1 (COLLEGE_WRITER_PROMPT and SI variant)

**Insert after the hook instruction:**

```
### STAGE 1: INTRODUCTION ESSAY (800-1400 words)
- **Hook first—and connect to READER QUESTIONS**: Open with a puzzle, surprise, or counterintuitive observation.
- **Structural map (within first 300 words)**: Right after your hook, give the reader a clear, quick map of how this psalm moves. What are its sections? Where does it turn? What's the arc? Keep it compact — a short paragraph or a tight list — but make it decisive. The reader should be able to see the psalm's architecture before diving into details.
- **Build an argument**: [new text from Change 1D above]
[etc.]
```

---

## Change 3: Mandate a Governing Argument

### Problem
The essay reads like 6-9 mini-essays on separate topics (a section on "the genre question," a section on "the key verb," a section on "liturgical context," etc.) rather than a single argument that builds cumulatively. This is because the prompt lists 9 priorities and the model treats them as a checklist.

### Changes Required

#### A. Replace the 9-item checklist with a narrative arc instruction (MASTER_WRITER_PROMPT and SI)

**Current items 1-9** (lines 915-923 in base, 936-944 in SI) should be replaced with:

```
Write a scholarly introduction essay that:

1. **Develops a governing argument about the psalm**: The STRUCTURAL OVERVIEW section below offers one reading. You may adopt it, revise it, or propose an entirely different reading based on the evidence. Either way, YOUR essay must present a coherent, original argument — not a response to someone else's analysis.

2. **Builds cumulatively toward a single conclusion**: Your essay should have ONE governing insight or question that every paragraph advances. Do NOT write a series of mini-essays on separate topics (structure, then imagery, then liturgy, then theology). Instead, weave these strands into a single argument. Use no more than 2-3 section headers. If you find yourself writing a new header every 200 words, you are listing observations, not building an argument.

3. **Draws on all available evidence**: Your argument should be supported by lexical analysis, traditional commentary (Rashi, Ibn Ezra, Radak, Malbim, etc.), concordance patterns, figurative language parallels, ANE context, textual criticism (MT vs LXX), Deep Web Research (cultural afterlife, reception history, scholarly debates), and liturgical usage. But these are EVIDENCE for your argument, not separate topics.

4. **Shows evidence through generous quotation**: Quote liberally from all sources (biblical parallels, liturgy, traditional commentaries). Don't just cite — SHOW the reader the actual text in Hebrew + English.

5. **Surfaces unique findings**: Highlight "only here" factors (hapax legomena, unusual constructions, surprising concordance patterns) — but only when they serve your argument.
```

#### B. Equivalent change for college prompts

Replace the current bullet-point list with:

```
- **Build an argument**: The background materials below offer structural observations and verse-level notes. Use them as raw material. Your essay must present a coherent, original argument that is entirely your own voice.
- **One argument, not many topics**: Your essay should build ONE cumulative case — not a series of mini-lessons. Weave lexical analysis, traditional commentary, parallels, and cultural context into a single line of reasoning. Use no more than 2-3 section headers. If you're writing a new header every 200 words, you're listing rather than arguing.
- **Draw on everything**: Lexical analysis, traditional commentators, concordance patterns, Deep Web Research, ANE parallels, liturgical usage — but as EVIDENCE for your argument, not separate topics.
- **Show**: Quote Hebrew + English liberally. Don't just cite — SHOW the reader the actual text.
- **Explain**: Define all terms on first use.
- **Connect**: Make intertextual connections explicit. Review the 'Related Psalms Analysis' in the research bundle.
```

---

## Change 4: Redefine Essay/Commentary Relationship

### Problem
Because the essay scatters observations across every verse, the verse commentary inevitably retreads the same ground.

### Changes Required

#### A. Add an explicit "argument vs. evidence room" framing (all four prompts)

**Insert at the boundary between Stage 1 and Stage 3 instructions, immediately before the verse commentary instructions:**

```
### THE ESSAY/COMMENTARY RELATIONSHIP

The introduction essay and the verse commentary serve fundamentally different purposes:

- **The ESSAY** is where you make your ARGUMENT. It presents your governing insight, develops it with selected evidence, and leaves the reader with a clear framework for understanding the psalm. It should be readable on its own.

- **The VERSE COMMENTARY** is the EVIDENCE ROOM. This is where you provide the detailed philological, textual, liturgical, and comparative analysis that supports, complicates, or enriches the essay's argument. It's also where you add discoveries that would have derailed the essay's momentum — a fascinating textual variant, an illuminating Rashi comment, a surprising concordance pattern, an ANE parallel.

**The test:** A reader who reads only the essay should understand the psalm's significance. A reader who also reads the verse commentary should feel they've been given a scholar's toolkit — and should encounter genuinely new material, not a rehash of the essay in verse-by-verse form.

**Practical rule:** Before writing each verse's commentary, ask: "Did the essay already say this?" If yes, either skip it or approach it from a completely different angle (a different commentator, a different parallel, a textual variant, a liturgical deployment).
```

#### B. Strengthen the existing "complement" instruction

**Current (line 989-990 in base, 1010-1011 in SI):**
```
**3. RELATIONSHIP TO INTRODUCTION:**
   - Complement the introduction. Don't simply repeat it. Before writing about each verse, ask: "What can I add that the intro didn't say?" Add different commentator views, liturgical deployments not mentioned, textual variants, specific philological oddities.
```

**New (replaces the above):**
```
**3. RELATIONSHIP TO INTRODUCTION:**
   - The essay made your argument. The verse commentary is where you open the toolkit. For each verse, ask: "What can I show the reader here that the essay didn't — and couldn't without losing momentum?" Prioritize: different commentator voices, liturgical deployments, textual variants, philological surprises, concordance patterns, and figurative language parallels not mentioned in the essay. If a verse was central to the essay's argument, the commentary should add a NEW angle on it, not summarize the essay's treatment.
```

---

## Change 5: Enforce Insight Incorporation

### Problem
The Opus 4.6 insight extractor produces excellent psalm-level and verse-level insights, but they are formatted as a small JSON section buried in 108K tokens of input. No validation ensures they were actually used.

### Changes Required

#### A. Reformat insights input section header (already done in Change 1A)

The header changes from `### PRIORITIZED INSIGHTS (FROM INSIGHT EXTRACTOR)` to `### KEY INSIGHTS TO INCORPORATE`.

#### B. Add a new instruction between the insights header and the content

**In all four prompts, immediately after the insights input section, add a note:**

(This is in the "YOUR INPUTS" section, after the `{curated_insights}` placeholder)

No change needed here — the header rename plus the checklist addition (below) is sufficient.

#### C. Add to the final validation checklist (all four prompts)

Add to the checklist / final validation section:

```
☐ KEY INSIGHTS: Each psalm-level insight from KEY INSIGHTS TO INCORPORATE is either woven into your essay or verse commentary, or you have a clear reason why it doesn't merit inclusion. Do not ignore these — they represent the most important analytical discoveries about this psalm.
```

---

## Change 6: Add "Coherence from Apparent Formlessness" Framing

### Problem
Many psalms don't have a popular "misconception" to debunk — they simply read, on a casual encounter, as a "word salad" of pious sentiments. The essay's most valuable contribution is resolving this apparent formlessness into a coherent work of skilled sacred poetic craft.

### Changes Required

#### A. Add new instruction to Stage 1, AFTER the structural map requirement and BEFORE the numbered checklist (all four prompts)

**For MASTER_WRITER_PROMPT and SI variant:**

```
**THE CENTRAL TASK — RESOLVE THE PSALM INTO A COHERENT WORK**:

Many psalms, on a casual reading, seem like a collection of pious sentiments — beautiful phrases strung together without an obvious argument or narrative. Your most important job is to show the reader that this is not the case. Show how the psalm is a coherent, intentional work of poetic craft: how its parts relate to each other, why its sequence matters, what the poet is building toward, and what holds it together.

This does NOT require "debunking a misconception." Some psalms simply need a skilled guide to make their internal logic visible. Others have genuine structural puzzles or theological tensions that reward careful attention. In either case, the reader should finish your essay thinking: "I had no idea this psalm was doing all that."

Ask yourself: "What is this psalm actually ABOUT — not as a list of themes, but as a single act of communication? What is the poet trying to DO to the reader or to God? Why does it begin where it begins and end where it ends?"
```

**For COLLEGE_WRITER_PROMPT and SI variant:**

```
**YOUR CENTRAL TASK — MAKE THE PSALM MAKE SENSE**:

Here's the thing about psalms: on a first read, many of them sound like a string of nice religious phrases — "Praise the Lord," "His mercy endures," "the righteous shall flourish." Your job is to show the student that this is actually a carefully constructed poem with a logic, an arc, and a purpose. Show them what the poet is DOING — not just saying — and why the sequence matters. The student should finish your essay thinking: "Oh — that's what this psalm is about. I never would have seen that on my own."

Ask yourself: "If a student asked me 'what is this psalm ABOUT?', could I answer in one sentence? And would that answer surprise them?"
```

---

## Change 7: Add Human Experience and Poetic Intentionality

### Problem
The commentary treats the psalm as a text to be analyzed rather than as a work created by a poet with specific intentions, addressing specific human experiences. The best biblical scholarship (Alter, Davis, Brueggemann) connects the text to recognizable human situations.

### Changes Required

#### A. Add to the numbered instruction list in Stage 1 (after the current items), both main and college prompts:

**For MASTER_WRITER_PROMPT / SI:**

```
6. **Names the human experience**: The best commentary connects the psalm to recognizable human situations — loneliness, gratitude, bewilderment at injustice, the terror of mortality, the vertigo of unmerited grace. Where appropriate, name the experience the psalmist is articulating and show how the poetic craft serves that experience. This is not sentimentality; it is the reason these poems have survived three millennia.

7. **Treats the poet as a craftsman with intentions**: Don't just catalog poetic devices ("this is a chiasm"). Show WHY the poet made this choice. What does the chiasm DO to the reader? What effect does the word order create? What would be lost if the poet had said the same thing in prose? The poet is a character in your essay — someone making deliberate, skilled decisions.
```

**For COLLEGE_WRITER_PROMPT / SI:**

```
- **Name the human experience**: Connect the psalm to real life. What is it like to feel what the psalmist is feeling? Loneliness, gratitude, rage, awe, bewilderment? The reason these poems survived 3,000 years is that they articulate experiences people still have. Don't be sentimental about it — just be honest.
- **Show the poet at work**: Don't just identify poetic devices ("this is a chiasm"). Show WHY the poet chose this structure. What does it DO? What would be lost without it? Treat the poet as a skilled craftsman making deliberate choices, not as a channel for abstract theological ideas.
```

---

## Change 8: Add "The One Thing" Closing Requirement

### Problem
Essays trail off or end with generic summary. The reader doesn't leave with a single, memorable takeaway.

### Changes Required

#### A. Add closing instruction at the end of Stage 1 (all four prompts):

**For MASTER_WRITER_PROMPT / SI:**

```
**CLOSING**: End your essay with the ONE insight you most want the reader to carry away — the single observation that makes this psalm impossible to read the same way again. This should feel like a destination your essay has been building toward, not a tacked-on summary. One or two sentences.
```

**For COLLEGE_WRITER_PROMPT / SI:**

```
- **End with "The One Thing"**: Close your essay with a single, memorable insight — the one observation that changes how the student reads this psalm. Not a summary. A destination. One or two sentences that the student will remember next time they encounter this text.
```

---

## Change 9: New Stylistic Guidance Example

Already specified in Change 1F above. The new example shows three levels (pipeline voice = forbidden, report voice = avoid, authorial voice = target) and the target example demonstrates the kind of vivid, first-person-authoritative prose we want.

---

## Full Prompt Text: New Sections

Below is the **complete rewritten Stage 1 instruction block** for MASTER_WRITER_PROMPT (and MASTER_WRITER_PROMPT_SI, which is identical except for the SPECIAL AUTHOR DIRECTIVE section that appears elsewhere).

This replaces everything from `### STAGE 1: INTRODUCTION ESSAY` through the end of Stage 1 (before `### STAGE 2: MODERN JEWISH LITURGICAL USE`):

```
### STAGE 1: INTRODUCTION ESSAY (800-1200 words)

**HOOK FIRST — AND CONNECT TO READER QUESTIONS**: Open with something surprising, counterintuitive, or puzzling about this psalm. Look at the READER QUESTIONS — your hook should set up one or more of these questions. Avoid bland summary openings.

**STRUCTURAL MAP (within first 300 words)**: After your hook, give the reader a clear, concise map of how the psalm moves — its sections, its arc, its logic. Think of this as the legend on a museum guide: before the reader enters the detailed rooms, they need to see the floor plan. This should be brief (a short paragraph or a compact list) but decisive — it should make the psalm's architecture visible at a glance. The rest of your essay will then develop the most interesting aspects of this structure.

**THE CENTRAL TASK — RESOLVE THE PSALM INTO A COHERENT WORK**:

Many psalms, on a casual reading, seem like a collection of pious sentiments — beautiful phrases strung together without an obvious argument or narrative. Your most important job is to show the reader that this is not the case. Show how the psalm is a coherent, intentional work of poetic craft: how its parts relate to each other, why its sequence matters, what the poet is building toward, and what holds it together.

This does NOT require "debunking a misconception." Some psalms simply need a skilled guide to make their internal logic visible. Others have genuine structural puzzles or theological tensions that reward careful attention. In either case, the reader should finish your essay thinking: "I had no idea this psalm was doing all that."

Ask yourself: "What is this psalm actually ABOUT — not as a list of themes, but as a single act of communication? What is the poet trying to DO to the reader or to God? Why does it begin where it begins and end where it ends?"

Write a scholarly introduction essay that:

1. **Develops a governing argument about the psalm**: The STRUCTURAL OVERVIEW section below offers one reading. You may adopt it, revise it, or propose an entirely different reading based on the evidence. Either way, YOUR essay must present a coherent, original argument — not a response to someone else's analysis.

2. **Builds cumulatively toward a single conclusion**: Your essay should have ONE governing insight or question that every paragraph advances. Do NOT write a series of mini-essays on separate topics (structure, then imagery, then liturgy, then theology). Instead, weave these strands into a single argument. Use no more than 2-3 section headers. If you find yourself writing a new header every 200 words, you are listing observations, not building an argument.

3. **Draws on all available evidence**: Your argument should be supported by lexical analysis, traditional commentary (Rashi, Ibn Ezra, Radak, Malbim, etc.), concordance patterns, figurative language parallels, ANE context, textual criticism (MT vs LXX), Deep Web Research (cultural afterlife, reception history, scholarly debates), and liturgical usage. But these are EVIDENCE for your argument, not separate topics to cover.

4. **Shows evidence through generous quotation**: Quote liberally from all sources (biblical parallels, liturgy, traditional commentaries). Don't just cite — SHOW the reader the actual text in Hebrew + English.

5. **Surfaces unique findings**: Highlight "only here" factors (hapax legomena, unusual constructions, surprising concordance patterns) — but only when they serve your argument.

6. **Names the human experience**: The best commentary connects the psalm to recognizable human situations — loneliness, gratitude, bewilderment at injustice, the terror of mortality, the vertigo of unmerited grace. Where appropriate, name the experience the psalmist is articulating and show how the poetic craft serves that experience. This is not sentimentality; it is the reason these poems have survived three millennia.

7. **Treats the poet as a craftsman with intentions**: Don't just catalog poetic devices ("this is a chiasm"). Show WHY the poet made this choice. What does the chiasm DO to the reader? What effect does the word order create? What would be lost if the poet had said the same thing in prose? The poet is a character in your essay — someone making deliberate, skilled decisions.

**CLOSING**: End your essay with the ONE insight you most want the reader to carry away — the single observation that makes this psalm impossible to read the same way again. This should feel like a destination your essay has been building toward, not a tacked-on summary. One or two sentences.
```

And the **complete rewritten Stage 1 for COLLEGE_WRITER_PROMPT / SI**:

```
### STAGE 1: INTRODUCTION ESSAY (800-1400 words)

- **Hook first — and connect to READER QUESTIONS**: Open with a puzzle, surprise, or counterintuitive observation. Look at the READER QUESTIONS — your hook should set up one or more of these questions.

- **Structural map (within first 300 words)**: Right after your hook, give the reader a clear, quick map of how this psalm moves. What are its sections? Where does it turn? What's the arc? Keep it compact — a short paragraph or a tight list — but make it decisive. The reader should be able to see the psalm's architecture before diving into details.

- **YOUR CENTRAL TASK — MAKE THE PSALM MAKE SENSE**: Here's the thing about psalms: on a first read, many of them sound like a string of nice religious phrases — "Praise the Lord," "His mercy endures," "the righteous shall flourish." Your job is to show the student that this is actually a carefully constructed poem with a logic, an arc, and a purpose. Show them what the poet is DOING — not just saying — and why the sequence matters. The student should finish your essay thinking: "Oh — that's what this psalm is about. I never would have seen that on my own."

  Ask yourself: "If a student asked me 'what is this psalm ABOUT?', could I answer in one sentence? And would that answer surprise them?"

- **Build an argument**: The background materials below offer structural observations and verse-level notes. Use them as raw material — adopt, revise, or discard as you see fit. Your essay must present a coherent, original argument that is entirely your own voice, not a response to an upstream analysis.

- **One argument, not many topics**: Your essay should build ONE cumulative case — not a series of mini-lessons with separate headers. Weave lexical analysis, traditional commentary, parallels, and cultural context into a single line of reasoning. Use no more than 2-3 section headers. If you're writing a new header every 200 words, you're listing rather than arguing.

- **Draw on everything**: Lexical analysis, traditional commentators (Rashi, Ibn Ezra, Radak, Malbim, etc.), concordance patterns, Deep Web Research (cultural afterlife, reception history), ANE parallels, liturgical usage — but as EVIDENCE for your argument, not separate topics to survey.

- **Show**: Quote Hebrew + English liberally. Don't just cite — SHOW the reader the actual text.

- **Explain**: Define all terms on first use.

- **Connect**: Make intertextual connections explicit. Review the 'Related Psalms Analysis' in the research bundle.

- **Name the human experience**: Connect the psalm to real life. What is it like to feel what the psalmist is feeling? Loneliness, gratitude, rage, awe, bewilderment? The reason these poems survived 3,000 years is that they articulate experiences people still have. Don't be sentimental about it — just be honest.

- **Show the poet at work**: Don't just identify poetic devices ("this is a chiasm"). Show WHY the poet chose this structure. What does it DO? What would be lost without it? Treat the poet as a skilled craftsman making deliberate choices, not as a channel for abstract theological ideas.

- **End with "The One Thing"**: Close your essay with a single, memorable insight — the one observation that changes how the student reads this psalm. Not a summary. A destination. One or two sentences that the student will remember next time they encounter this text.
```

---

## Validation Checklist Updates

### Current checklist items (at end of MASTER_WRITER_PROMPT):

These are implied by the various "VALIDATION CHECK" sections. Add/modify the following:

**New checklist (replaces current scattered validation checks, consolidated at end of prompt):**

```
## FINAL VALIDATION CHECKLIST

Before submitting, verify:

☐ RULE 11 (SCHOLAR, NOT PIPELINE): Does your text read as if written by a single authoritative scholar? Search for: "thesis," "macro," "micro," "pipeline," "research bundle," "concordance data shows," "insight extractor." If any appear, rewrite.
☐ STRUCTURAL MAP: Does the reader see the psalm's architecture within the first 300 words?
☐ GOVERNING ARGUMENT: Can you state your essay's central argument in one sentence? Does every paragraph advance it?
☐ SECTION HEADERS: Do you have 2-3 or fewer? (More = mini-essay problem)
☐ ESSAY vs COMMENTARY: Does the verse commentary contain substantial material NOT in the essay?
☐ KEY INSIGHTS: Each psalm-level insight from KEY INSIGHTS TO INCORPORATE is either woven into your essay or verse commentary, or you have a clear reason why it doesn't merit inclusion.
☐ HEBREW + ENGLISH: Every Hebrew quotation has an English translation alongside it.
☐ CITATIONS = QUOTATIONS: Every biblical citation is accompanied by an actual quotation, not just a reference.
☐ TECHNICAL TERMS: Defined on first use.
☐ NO BREATHLESSNESS: No "masterpiece," "breathtaking," "stunning," "remarkable," "tour de force."
☐ NO BLURRY PHOTOGRAPHS: No abstract nouns (density, resonance, dynamics, contours) without concrete verbs.
☐ THE ONE THING: Does the essay end with a single, memorable takeaway?
☐ READER QUESTIONS: Each question from READER QUESTIONS is addressed somewhere in the essay or commentary.
☐ FIGURATIVE LANGUAGE: Each verse with figurative language cites at least ONE biblical parallel (Hebrew + English) and generates an insight.
☐ TRANSLATION TEST: Each verse commentary contains at least one observation not derivable from English translation alone.
☐ THE POET: Have you shown the poet making at least 2-3 deliberate craft choices and explained WHY those choices matter?
```

---

## Testing Protocol

### Test Psalms
Run 2-3 psalms that already have macro, micro, research, and insight files:
- **Psalm 100** (short, 5 verses — fast/cheap test)
- **Psalm 33** (longer, 22 verses — tests pacing and argument sustained over length)
- Optionally a third psalm with deep research available

### Test Command
```bash
python scripts/run_enhanced_pipeline_TEST.py --psalm 100 --skip-macro --skip-micro --skip-insights
python scripts/run_enhanced_pipeline_TEST.py --psalm 33 --skip-macro --skip-micro --skip-insights
```

### Evaluation Criteria
For each test output, evaluate:

1. **Pipeline language:** Search for "thesis," "macro," "micro," "research bundle," "concordance data," "insight extractor," "you were given," "the heading gave you." Should find ZERO instances.

2. **Structural map:** Is there a clear structural outline within the first 300 words of the intro essay?

3. **Governing argument:** Can you state the essay's central argument in one sentence? Does the essay feel like it's going somewhere, or like a collection of observations?

4. **Section headers:** Count them. Target: 2-3. Red flag: 5+.

5. **Essay/commentary overlap:** Read the verse commentary for the psalm's "key" verse (e.g., v.3 of Psalm 100). Does it substantially repeat the essay, or does it add new material?

6. **Insight incorporation:** Check the `_insights.json` file. Are the psalm-level insights visible in the output?

7. **Human experience:** Does the essay connect the psalm to a recognizable human situation?

8. **Poetic intentionality:** Does the essay show the poet making deliberate choices (not just cataloging devices)?

9. **The One Thing:** Does the essay end with a single memorable insight?

10. **Overall feel:** Does this read like a published essay by a distinguished scholar, or like structured analytical notes?

### Comparison
Place the `_TEST` and production files side by side for the same psalm. The TEST version should feel:
- More cohesive (one argument, not many topics)
- More authoritative (scholar's voice, not pipeline endpoint)
- More interesting (human experience, poetic intentionality)
- Less redundant (commentary adds to essay, doesn't repeat it)

### After Validation
If the TEST outputs are clearly better:
1. Copy the new prompts from `master_editor_v3.py` into `master_editor.py`, replacing the v2 prompts and updating `_format_analysis_for_prompt`
2. Apply the same prompt changes to `master_editor_si.py` (secondary — for the SI pipeline)
3. Delete `master_editor_v3.py`
4. Delete `run_enhanced_pipeline_TEST.py`
5. Re-run any psalms that need the improved output

---

## Summary of All Changes by Phase

### PHASE 1: Testing (create new files ONLY — no original files touched)

| New File | What Goes In It |
|----------|----------------|
| `src/agents/master_editor_v3.py` | `MASTER_WRITER_PROMPT_V3` and `COLLEGE_WRITER_PROMPT_V3` prompt constants with all Changes 1-9 applied |
| | `MasterEditorV3` class inheriting from `MasterEditorV2`, overriding: |
| | — `_format_analysis_for_prompt()` with new labels (`**Central Reading:**`, `**Open Questions:**`) |
| | — `_perform_writer_synthesis()` to use the V3 prompt constants |
| `scripts/run_enhanced_pipeline_TEST.py` | Copy of `run_enhanced_pipeline.py` with: |
| | — Import changed to `from src.agents.master_editor_v3 import MasterEditorV3 as MasterEditor` |
| | — All output filenames suffixed with `_TEST` |
| | — Everything else identical (pipeline logic, skip flags, etc.) |

**Files NOT modified during Phase 1:**
- ❌ `src/agents/master_editor.py` — untouched
- ❌ `src/agents/master_editor_si.py` — untouched
- ❌ `scripts/run_enhanced_pipeline.py` — untouched
- ❌ `scripts/run_si_pipeline.py` — untouched

### PHASE 2: After Validation (merge into originals, then clean up)

Only after reviewing `_TEST` outputs and confirming they are better:

**Step 1 — Primary pipeline (do this first):**

| Original File | Changes to Merge |
|---------------|-----------------|
| `master_editor.py` `MASTER_WRITER_PROMPT` | Rename input headers, add RULE 11, replace stylistic example, replace Stage 1, add essay/commentary relationship section, replace commentary complement instruction |
| `master_editor.py` `COLLEGE_WRITER_PROMPT` | Same category of changes as above, college-adapted |
| `master_editor.py` `_format_analysis_for_prompt` | `**Thesis:**` → `**Central Reading:**`, `**Research Questions:**` → `**Open Questions:**`, `**Interesting Questions:**` → `**Open Questions:**` |
| `master_editor.py` `MASTER_EDITOR_PROMPT_V2` | Rename input headers for consistency (if editor mode is used) |
| `master_editor.py` `COLLEGE_EDITOR_PROMPT_V2` | Rename input headers for consistency (if editor mode is used) |

**Step 2 — SI pipeline (secondary, do after primary is confirmed working):**

| Original File | Changes to Merge |
|---------------|-----------------|
| `master_editor_si.py` `MASTER_WRITER_PROMPT_SI` | All same changes as `MASTER_WRITER_PROMPT` |
| `master_editor_si.py` `COLLEGE_WRITER_PROMPT_SI` | All same changes as `COLLEGE_WRITER_PROMPT` |
| `master_editor_si.py` `MASTER_EDITOR_PROMPT_SI` | Rename input headers (if editor mode is used) |
| `master_editor_si.py` `COLLEGE_EDITOR_PROMPT_SI` | Rename input headers (if editor mode is used) |

**Files to delete after merging:**
- 🗑️ `src/agents/master_editor_v3.py`
- 🗑️ `scripts/run_enhanced_pipeline_TEST.py`
- 🗑️ Any `_TEST` output files no longer needed

---

*This document contains all information needed to implement the changes. No additional codebase exploration is required. Remember: Phase 1 creates only NEW files. Phase 2 (after validation) is the only time original files are modified.*
