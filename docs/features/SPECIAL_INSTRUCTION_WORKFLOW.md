# Special Instructions (SI) Pipeline Implementation Guide

> **V4 Update (Session 269)**: The SI pipeline now uses the unified V4 prompt (single commentary output). College-specific SI outputs have been removed. The `--college` flag on `master_editor_si.py` is a hidden no-op.

## Overview
We are creating a supplementary pipeline workflow that allows a human editor ("The Author") to inject specific, overriding instructions into the Master Editor's generation process. This allows for alternative rewrites of commentaries based on specific thematic ideas or corrections, without altering the behavior of the standard pipeline.

## Core Constraints
1.  **Safety First:** Do **NOT** modify the existing `scripts/run_enhanced_pipeline.py` or `src/agents/master_editor.py` files. We must preserve the stability of the current "V1" pipeline.
2.  **Naming Convention:** Use "**SI**" (Special Instruction) for all new files and classes.
3.  **Inheritance:** Use Python class inheritance to extend functionality rather than changing the base classes.
4.  **Directory Structure:** Special instructions are stored in `data/special_instructions`.

## Implementation Steps

### 0. Reference Files (Study These First)
Before writing any code, review the following files to understand the class structure and file handling logic:
*   `src/agents/master_editor.py`: **Primary Source.** You will be extending `MasterEditorV2` from this file. Study the `__init__`, `edit_commentary`, and `_perform_editorial_review_gpt` methods.
*   `scripts/run_enhanced_pipeline.py`: **Reference.** Look at how paths are constructed (variables like `synthesis_intro_file`, `edited_intro_file`) and how the `MasterEditor` is instantiated. Your new script will use simplified versions of these patterns.

### 1. Data Directory Setup
*   [x] Ensure the directory `data/special_instructions` exists. (Already created).
*   **Convention:** Instruction files must be named `special_instructions_Psalm_{XXX}.txt` (e.g., `special_instructions_Psalm_019.txt`).

### 2. Create `src/agents/master_editor_si.py`
Create a new file that extends the existing Master Editor to handle special instructions.

*   **Import:** Import `MasterEditorV2` from `.master_editor`.
*   **Define Prompts:** Copy `MASTER_EDITOR_PROMPT_V2` and `COLLEGE_EDITOR_PROMPT_V2` from the original file and rename them to `MASTER_EDITOR_PROMPT_SI` and `COLLEGE_EDITOR_PROMPT_SI`.
*   **Modify Prompts:** Add the following section to **BOTH** new prompts, placed immediately after the "Ground Rules" section:

```text
## ═══════════════════════════════════════════════════════════════════════════
## SPECIAL AUTHOR DIRECTIVE (HIGHEST PRIORITY)
## ═══════════════════════════════════════════════════════════════════════════

The supervising author has provided specific, overriding instructions for this revision.
You MUST prioritize these specific notes above general stylistic guidelines if they conflict.
This is the specific "idea" or "angle" the author wants this version to embody.

AUTHOR'S INSTRUCTIONS:
{special_instruction}
```

*   **Create Class `MasterEditorSI`:**
    *   Inherit from `MasterEditorV2`.
    *   **Override `edit_commentary`:**
        *   Update signature to accept `special_instruction: str`.
        *   Store this instruction in `self.special_instruction` (or pass it down).
        *   Call the internal review methods.
    *   **Override `edit_college_commentary`:**
        *   Update signature to accept `special_instruction: str`.
    *   **Override `_perform_editorial_review_gpt`** (and the Claude equivalent):
        *   Copy the logic from the parent class.
        *   Update the `prompt.format(...)` call to use `MASTER_EDITOR_PROMPT_SI` and include `special_instruction=...`.
    *   **Override `_perform_college_review`** (and sub-methods):
        *   Update to use `COLLEGE_EDITOR_PROMPT_SI` and include the instruction.

### 3. Create `scripts/run_si_pipeline.py`
Create a lightweight script dedicated to this workflow. It should **not** run the full analysis (Macro/Micro/Synthesis) but assume those files already exist.

*   **Inputs:** Accept `psalm_number` as an argument.
*   **Logic:**
    1.  **Locate Instruction:** Check for `data/special_instructions/special_instructions_Psalm_{XXX}.txt`. If missing, abort with a clear error message.
    2.  **Read Instruction:** Load the text content.
    3.  **Strict Input Validation:** Check for the existence of ALL required input files in `output/psalm_{XXX}/`:
        *   `psalm_{XXX}_macro.json`
        *   `psalm_{XXX}_micro_v2.json`
        *   `psalm_{XXX}_research_v2.md`
        *   `psalm_{XXX}_synthesis_intro.md`
        *   `psalm_{XXX}_synthesis_verses.md`
        *   **CRITICAL:** If ANY of these are missing, the script must **EXIT IMMEDIATELY** with an error. It must **NOT** attempt to generate them or run earlier pipeline stages.
    4.  **Define Outputs:** Define output paths with the `_SI` suffix:
        *   `psalm_{XXX}_edited_intro_SI.md`
        *   `psalm_{XXX}_edited_verses_SI.md`
        *   `psalm_{XXX}_assessment_SI.md`
        *   `psalm_{XXX}_pipeline_stats_SI.json`  <-- NEW
    5.  **Handle Statistics:**
        *   Load the *original* `psalm_{XXX}_pipeline_stats.json`.
        *   Initialize a `PipelineSummaryTracker` with this data.
        *   **Crucial:** You must save the updated stats to the new `_SI.json` path, NOT overwrite the original.
    6.  **Run Editor:** Instantiate `MasterEditorSI` and call `edit_commentary`.
    7.  **Update Stats:** After the editor finishes, update the tracker with the new completion date and model usage, then save to the `_SI.json` file.
    8.  **Formatting:** Generate all three document types using the new `_SI.json` stats file to ensure consistency:
        *   **Main:** `psalm_{XXX}_commentary_SI.docx` (using Main SI markdowns + SI stats)
        *   **College:** `psalm_{XXX}_commentary_college_SI.docx` (using College SI markdowns + SI stats)
        *   **Combined:** `psalm_{XXX}_commentary_combined_SI.docx` (using Main SI + College SI markdowns + SI stats)

## Usage Example for User
To run a special instruction on Psalm 19:

1.  Create `data/special_instructions/special_instructions_Psalm_019.txt` with your notes.
2.  Run: `python scripts/run_si_pipeline.py 19`

## Junior Dev Checklist

- [ ] **Directory:** Verify `data/special_instructions` exists.
- [ ] **Class:** `src/agents/master_editor_si.py` created.
- [ ] **Inheritance:** `MasterEditorSI` inherits from `MasterEditorV2`.
- [ ] **Prompts:** SI prompts defined with the "{special_instruction}" placeholder.
- [ ] **Methods:** `edit_commentary` and `edit_college_commentary` overrides accept the new string argument.
- [ ] **Script:** `scripts/run_si_pipeline.py` created.
- [ ] **File I/O:** Script correctly reads the specific instruction file.
- [ ] **Output Naming:** Script generates `_SI.md` files (does NOT overwrite originals).
- [ ] **Validation:** Run a test on a psalm (e.g., Psalm 1) to ensure the `_SI` files are created and reflect the instructions.
