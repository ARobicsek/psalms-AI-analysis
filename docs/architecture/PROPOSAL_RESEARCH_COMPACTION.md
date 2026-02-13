# Research Content Compaction Proposal

This document outlines a two-pronged strategy to maximize the context window efficiency for the Master Writer, ensuring that input tokens are spent on *content* rather than formatting or filler.

## 1. Telegraphic Style (Maximum Content Density)

**Goal:** Increase the information density of all upstream agent outputs (Macro Analyst, Micro Analyst, and Librarians) by enforcing a "Telegraphic" writing style.

**Strategy:**
*   **Prompt Engineering:** Instruct upstream agents to write in an "LLM-native" style that prioritizes content over readability.
    *   **Drop Stop Words:** Remove "the", "a", "an", "is", "of" where not strictly necessary for meaning.
    *   **Use Fragments:** Prefer sentence fragments and bullet points over full flowing sentences.
    *   **No Fluff:** Strictly forbid "Here is the analysis", "In conclusion", or other conversational fillers.
    *   **Dense Headers:** Use abbreviated headers (e.g., `## LEX` instead of `## Hebrew Lexicon Entries`).

**Benefit:** Reduces token usage by 15-25% across all text inputs without losing any semantic information.

## 2. JSON for Research Bundle

**Goal:** Switch the `ResearchBundle` data representation from Markdown to JSON.

**Strategy:**
*   **Raw Data Transfer:** Instead of formatting research findings (Lexicon, Concordance, Commentary) into a human-readable Markdown document, pass the raw structured data (dictionaries/lists) directly to the Master Writer as a JSON string.
*   **Efficiency:**
    *   **Comparison Results:** Tests show that the JSON representation is **~34% the size of the equivalent Markdown** (66% reduction).
    *   **Eliminates Formatting Overhead:** Removes all markdown table syntax (`|`, `-`, spacing), bolding (`**`), and section spacing.
*   **Implementation:**
    *   Update `ResearchAssembler` to output JSON.
    *   Update `MasterEditor` (Writer) prompts to accept and parse this JSON structure.

**Benefit:** Massive reduction in token overhead for the largest input component (Research Bundle), freeing up ~3000+ tokens per call for actual reasoning and synthesis.

---
**Status:** PARTIALLY IMPLEMENTED (Session 257)

### Implemented (Session 257 — Phase A):
- Removed static commentator biographical essays from bundle (10,724 chars → 200 chars)
- Fixed analytical framework duplication (removed from bundle; kept as separate prompt variable)
- Added `include_working_notes=False` to strip macro working notes from micro analyst input

### Remaining (Phase B — Next Session):
- Telegraphic style for macro/micro outputs (this proposal's item 1)
- Compact markdown formatting in research bundle (dense headers, reduced separators)
- BDB lexicon entry truncation (~500 chars max per entry)
- Related psalms default trimming (no full texts)

### Deferred Indefinitely:
- JSON for Research Bundle (this proposal's item 2) — content-level reductions are higher impact

### Full Plan: See `C:\Users\ariro\.claude\plans\purring-marinating-token.md`
