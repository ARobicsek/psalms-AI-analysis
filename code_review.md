# Code Review: Master Writer Integration

## Overview
This PR/Update removes the `SynthesisWriter` agent entirely from the pipeline and upgrades the `MasterEditor` to a **Master Writer**. The goal is to eliminate the "telephone game" effect where the editor merely polished the synthesis writer's draft. Instead, the Master Writer now generates the definitive commentary directly from the research bundle, macro analysis, and micro analysis.

## Key Changes

### 1. `src/agents/master_editor.py`
We transformed the Editor from a review agent into a creation agent.

#### New Prompts
Two new definitive prompts were added:
*   **`MASTER_WRITER_PROMPT`**: Merges the creation logic of the old Synthesis writer with the high stylistic standards of the old Master Editor.
    *   **Ground Rules**: Enforces Hebrew/English always together, no orphaned facts, and "Blurry Photograph Check".
    *   **Structure**: Introduction Essay -> Liturgical Section -> Verse Commentary -> Reader Questions.
*   **`COLLEGE_WRITER_PROMPT`**: Tailored for college students (sophisticated but accessible).
    *   **Focus**: Explaining technical terms, engaging "Deep Web Research" connections.

#### New Methods
*   **`write_commentary(...)`**: The main entry point. Loads inputs (Macro, Micro, Research, Insights), formats them, and calls the LLM with `MASTER_WRITER_PROMPT`.
*   **`write_college_commentary(...)`**: Similar workflow but uses `COLLEGE_WRITER_PROMPT` and the college-specific model.
*   **`_perform_writer_synthesis(...)`**: Helper to handle prompt formatting and API calls.
*   **Model Compatibility**: Added conditional logic to support non-reasoning models (like `gpt-4o`) by handling `reasoning_effort` and `max_completion_tokens` vs `max_tokens` dynamically.

### 2. `scripts/run_enhanced_pipeline_TEST.py`
A new orchestration script was created to test this flow without breaking the existing production pipeline.

*   **Removed**: `SynthesisWriter` instantiation and step.
*   **Replaced**: Step 4 (Master Editor) now calls `master_editor.write_commentary()` instead of `edit_commentary()`.
*   **Replaced**: Step 4b (College Editor) now calls `master_editor.write_college_commentary()`.
*   **Inputs**: The Writer now receives the **raw** `research_bundle`, `macro_analysis`, and `micro_analysis` directly.

## Detailed Prompt Logic (Master Writer)

The new prompt is structured to force synthesis. Key sections include:

```python
MASTER_WRITER_PROMPT = """
...
Your mission: Write a definitive commentary on Psalm {psalm_number} that synthesizes detailed research into a coherent, compelling narrative.
...
### RULE 1: HEBREW AND ENGLISH — ALWAYS TOGETHER
Every time you reference a Hebrew word, phrase, or quotation, you MUST provide:
- The Hebrew text, AND
- An English translation
...
### STAGE 1: INTRODUCTION ESSAY (800-1200 words)
- Engages the macro thesis critically.
- Synthesizes all sources.
- Uses Deep Web Research.
...
### STAGE 3: VERSE-BY-VERSE COMMENTARY
For EACH verse:
1. START with the Hebrew text, punctuated.
2. Provide commentary (Target: 1-3 transformative angles per verse).
...
"""
```

## Verification
*   **Smoke Test**: Verified on Psalm 117 (dummy data) -> **PASSED**.
*   **Model Logic**: Verified conditional handling for `gpt-4o` vs `o1/gpt-5` (reasoning models) -> **FIXED** (addressed `reasoning_effort` and token limit errors).

## How to Run
Use the test script to verify the new pipeline:

```bash
# Full run on Psalm 117 (skipping analysis if files exist)
python scripts/run_enhanced_pipeline_TEST.py 117 --master-editor-model gpt-4o --skip-macro --skip-micro --skip-insights
```
