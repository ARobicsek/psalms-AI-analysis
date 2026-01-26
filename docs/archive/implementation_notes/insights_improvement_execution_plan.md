# Insight Quality Improvements — Detailed Execution Plan

**Prepared:** Session 240 (2026-01-26)
**Status:** APPROVED — Ready for implementation in Session 241
**Source document:** `docs/archive/implementation_notes/insights_improvement.md`

---

## Table of Contents

1. [Objectives & Justification](#1-objectives--justification)
2. [Scope & Session Boundaries](#2-scope--session-boundaries)
3. [Phase 1: Prompt Changes — Exact Specifications](#3-phase-1-prompt-changes)
4. [Phase 2a: Insight Extractor Agent](#4-phase-2a-insight-extractor-agent)
5. [Phase 2b-2c: Pipeline Integration (Session 242)](#5-phase-2b-2c-pipeline-integration)
6. [Verification Checklist](#6-verification-checklist)
7. [Risk & Mitigation](#7-risk--mitigation)

---

## 1. Objectives & Justification

### The Problem

The pipeline successfully automates the "gathering" phase of scholarship — lexicon, concordance, liturgy, figurative parallels. But the transition from **Data Aggregation** to **Interpretive Synthesis** is weak. Agents act like **Librarians** (stacking relevant facts) rather than **Curators** (explaining why specific facts change meaning).

The result: paragraphs that sound scholarly but deliver no interpretive payoff. Specifically:

1. **Orphaned facts** — Hebrew roots cited without explaining what they change ("רָצוֹן is a key biblical term" tells the reader nothing)
2. **Hedge-blending** — Multiple readings merged into vague syntheses instead of explicitly named and resolved ("The phrase suggests both X and Y, reflecting the rich theological texture")
3. **Blurry prose** — Abstract nouns without concrete verbs ("the atmosphere in which life thrives," "reflects the covenantal dynamics")
4. **Breadth over depth** — Covering 8-10 scholarly angles superficially instead of 2-3 deeply
5. **Obvious observations** — Stating things derivable from English translation alone

### The Fix

Two-phase approach:

**Phase 1 (Prompt Engineering):** Add five "Insight Quality Rules" (A-E) to all 6 prompts across the synthesis and editing stages. These rules create explicit quality gates with concrete bad/good examples so the LLMs self-correct during generation.

**Phase 2 (Architectural):** Add a new "Insight Extractor" agent between Micro Analysis and Synthesis. This agent uses Claude Opus 4.5 to ruthlessly filter research materials down to the 20% of insights that deliver 80% of the value, giving the Synthesis Writer a prioritized list of cruxes instead of an overwhelming data dump.

### Why Both Phases

Phase 1 alone may be insufficient because the Synthesis Writer is overwhelmed by data volume (research bundles can exceed 300K characters). Telling it to "be insightful" while drowning it in data is like telling someone to write a brilliant essay while firehosing them with reference material. The Insight Extractor (Phase 2) forces *decision-making* before *writing*, ensuring the most transformative observations are surfaced before the synthesis stage begins.

### Expected Outcomes

| Metric | Current | Target |
|--------|---------|--------|
| "Hedge-blend" sentences per psalm | 5-10 | 0-2 |
| Hebrew citations with payoff within 2 sentences | ~60% | >90% |
| Verses where reader learns something beyond translation | ~50% | >80% |
| Reader engagement (anecdotal) | "give up halfway" | "finish and remember insights" |

---

## 2. Scope & Session Boundaries

### Session 241: Phase 1 + Phase 2a

**Phase 1 — Prompt changes to 6 prompts across 3 files:**

| # | File | Prompt | Lines |
|---|------|--------|-------|
| 1 | `src/agents/synthesis_writer.py` | `INTRODUCTION_ESSAY_PROMPT` | 45-221 |
| 2 | `src/agents/synthesis_writer.py` | `VERSE_COMMENTARY_PROMPT` | 225-453 |
| 3 | `src/agents/master_editor.py` | `MASTER_EDITOR_PROMPT_V2` | 52-387 |
| 4 | `src/agents/master_editor.py` | `COLLEGE_EDITOR_PROMPT_V2` | 395-664 |
| 5 | `src/agents/master_editor_si.py` | `MASTER_EDITOR_PROMPT_SI` | 46-395 |
| 6 | `src/agents/master_editor_si.py` | `COLLEGE_EDITOR_PROMPT_SI` | 402-688 |

**Phase 2a — Create new agent file:**

| # | File | Action |
|---|------|--------|
| 7 | `src/agents/insight_extractor.py` | CREATE new file |

### Session 242: Phase 2b-2c

**Phase 2b — Pipeline integration:**
- Add Step 2c (Insight Extraction) to `scripts/run_enhanced_pipeline.py`
- Output: `psalm_NNN_insights.json`

**Phase 2c — SynthesisWriter parameter changes:**
- Add `insights` parameter to `write_commentary()`, `_generate_introduction()`, `_generate_verse_commentary()`
- Format insights as "PRIORITIZED INSIGHTS" section in prompts
- Update pipeline synthesis call to load and pass insights

### Session 243+: Testing & Validation

- Run pipeline on Psalm 30 (the example psalm from the design document) and compare output
- A/B comparison with previous output
- Regression checks on orphaned citations, ambiguity handling

---

## 3. Phase 1: Prompt Changes

### 3.1 The "Insight Quality Rules" Block (Rules A-E)

This block is inserted into both synthesis_writer.py prompts. The exact text:

```
## ═══════════════════════════════════════════════════════════════════════════
## INSIGHT QUALITY RULES (NON-NEGOTIABLE)
## ═══════════════════════════════════════════════════════════════════════════

These rules exist because the greatest risk in biblical commentary is sounding scholarly while saying nothing. Our readers are intelligent and will notice when we're filling space.

### RULE A: NO ORPHANED FACTS (The "So What?" Test)

Every linguistic, historical, or philological observation MUST have an immediate interpretive payoff. You are FORBIDDEN from stating a fact without explaining how it changes the reader's understanding.

**Test:** After writing any sentence that mentions a Hebrew root, grammatical form, or parallel text, ask: "So what? What does the reader now understand that they didn't before?"

If you cannot answer in one sentence, either:
1. Develop the observation until it has payoff, OR
2. Delete it

**ORPHANED (BAD):**
> "The root רצה appears in cultic contexts for sacrificial acceptance. Here it conveys divine favor."

**PAYOFF (GOOD):**
> "The root רצה is altar-language — it's what makes a sacrifice 'accepted' rather than rejected (Lev 1:3). By applying this term to life itself, the psalmist suggests that existence is a daily offering, either accepted or refused."

---

### RULE B: COMMIT TO AMBIGUITY (Don't Hedge-Blend)

When a verse admits multiple readings, you MUST explicitly name the tension and then:
- **Commit** to one reading with reasons, OR
- **Explain** why the ambiguity itself is theologically productive

**FORBIDDEN (the hedge-blend):**
> "The phrase suggests both X and Y, reflecting the rich theological texture of the verse."

This commits to nothing. It is the enemy.

**REQUIRED (explicit + resolution):**
> "The Hebrew sustains two readings: X (supported by the parallelism) and Y (supported by the cultic vocabulary). The ambiguity may be intentional — by refusing to resolve it, the psalmist forces the reader to hold both claims simultaneously: favor is both durable AND constitutive of life itself."

---

### RULE C: THE BLURRY PHOTOGRAPH CHECK

Abstract nouns without concrete verbs produce sentences that sound profound but show nothing.

**BLURRY WORDS TO WATCH:** atmosphere, density, resonance, texture, dimensions, contours, dynamics, framework, matrix, tapestry

If you find yourself using these words, STOP. Ask: "What is God actually DOING? What is the psalmist actually CLAIMING?" Rewrite with concrete verbs.

**BLURRY:** "The verse reflects the covenantal dynamics of divine presence."
**SHARP:** "God's presence, the psalmist claims, is not passive — it actively constitutes the difference between life and mere existence."

---

### RULE D: DEPTH BEATS BREADTH

You have access to many scholarly angles. DO NOT try to cover all of them for every verse.

For each verse, choose the 1-3 angles that actually TRANSFORM the reading. Pursue those deeply. Ignore the rest.

**Ask:**
- Which angle makes this verse *surprising*?
- Which angle would make a reader say "I never thought of it that way"?
- Which angle connects to something the reader already cares about?

A reader who learns ONE transformative thing will remember it. A reader shown TEN mildly interesting facts will remember none.

---

### RULE E: THE TRANSLATION TEST

Before finalizing any verse commentary, ask: "Could the reader figure this out from a good English translation alone?"

If yes → the observation is too obvious. Either cut it or develop it further.
If no → good. This is what we're here for.
```

**IMPORTANT: Template variable safety.** This block contains no `{` or `}` characters, so it is safe for Python `.format()` string templates.

---

### 3.2 Task 1: INTRODUCTION_ESSAY_PROMPT

**File:** `src/agents/synthesis_writer.py`
**Action:** INSERT the Rules A-E block (section 3.1 above) immediately BEFORE the `## CRITICAL REQUIREMENTS` header at line 184.
**Insertion point:** Between line 183 (end of the stylistic example) and line 184.

No other changes to this prompt.

---

### 3.3 Task 2: VERSE_COMMENTARY_PROMPT

**File:** `src/agents/synthesis_writer.py`
**Two actions:**

1. **INSERT** the Rules A-E block (section 3.1 above) immediately BEFORE `### IMPORTANT NOTES:` at line 409.
   - Insertion point: Between line 407 (end of figurative language validation check) and line 409.

2. **REMOVE** the existing "Depth over breadth" bullet at line 416:
   ```
   - **Depth over breadth**: Better to explore 2-3 angles deeply than mention everything superficially
   ```
   This single line is fully superseded by RULE D in the new block. Keeping both creates redundancy.

---

### 3.4 Task 3: MASTER_EDITOR_PROMPT_V2

**File:** `src/agents/master_editor.py`
**Four insertions (no removals):**

#### 3.4.1 Syntactic Flow Rule (under RULE 1)

**Insert after line 90** (the `**Mental checkpoint:**` paragraph that ends RULE 1), before the `---` separator:

```

**Syntactic Flow Rule:**

The English sentence must make complete grammatical sense if the Hebrew were removed. Use Hebrew as a parenthetical anchor, not a speed bump that derails the sentence.

**CLUNKY (Hebrew interrupts the logic):**
> "The word הֶעֱמַדְתָּה (`he'emadta`, 'You made stand'), which is a Hiphil form implying causation, suggests that the stability..."

**FLOWING (Hebrew supports without interrupting):**
> "God 'made the mountain stand' (הֶעֱמַדְתָּה) — the causative verb implies that the psalmist's stability was never self-generated but always a gift."

The reader should feel the Hebrew enriches the sentence, not that they're jumping over hurdles.
```

#### 3.4.2 RULE 6: Blurry Photograph Check

**Insert after line 141** (the `---` separator after RULE 5):

```

### RULE 6: THE BLURRY PHOTOGRAPH CHECK

Abstract nouns without concrete verbs produce sentences that sound profound but show nothing.

**BLURRY WORDS TO WATCH:** atmosphere, density, resonance, texture, dimensions, contours, dynamics, framework, matrix, tapestry

If you find yourself using these words, STOP. Ask: "What is God actually DOING? What is the psalmist actually CLAIMING?" Rewrite with concrete verbs.

**BLURRY:** "The verse reflects the covenantal dynamics of divine presence."
**SHARP:** "God's presence, the psalmist claims, is not passive — it actively constitutes the difference between life and mere existence."

**Self-check:** If your sentence contains abstract nouns (density, resonance, atmosphere, dynamics, contours, dimensions) without a concrete verb showing what God or the psalmist *does*, STOP. Rewrite until you can see the action.

---
```

#### 3.4.3 Section 5: Reader Transformation (assessment criterion)

**Insert after line 227** (end of `### 4. STRUCTURAL ISSUES` content), before the `---` separator:

```

### 5. READER TRANSFORMATION

For each verse commentary, ask: **"After reading this, does the reader understand the verse differently than they would from the translation alone?"**

- If the commentary merely confirms what the translation already shows → WEAK, needs rewriting
- If the commentary adds historical trivia but no interpretive shift → WEAK, needs rewriting
- If the commentary reveals something the reader couldn't see without the Hebrew/context → STRONG

**For the introduction essay, ask:** "Does the reader now have a framework for understanding the whole psalm that they didn't have before?"

Flag any verse commentary that fails the transformation test in your assessment.
```

#### 3.4.4 Insight Delivery Checklist Items

**Insert after line 364** (the last checklist item `☐ READER QUESTIONS: ...`), before `### STAGE 4`:

```
☐ Every Hebrew citation has an interpretive payoff within 2 sentences (no orphaned facts)
☐ Ambiguous verses explicitly name the tension and resolve or explain it (no hedge-blending)
☐ No "blurry photograph" sentences (abstract nouns without concrete verbs)
☐ Each verse commentary contains at least one observation not derivable from English translation alone
```

**Result:** Checklist grows from 10 items to 14 items.

---

### 3.5 Task 4: COLLEGE_EDITOR_PROMPT_V2

**File:** `src/agents/master_editor.py`
**Same 4 insertions, adapted for college tone:**

#### 3.5.1 Syntactic Flow Rule

**Insert after line 430** (the `**Checkpoint:**` paragraph under RULE 1):

```

**Syntactic Flow Rule:**

Your students should be able to follow the English without tripping over the Hebrew. The English sentence must make complete grammatical sense if the Hebrew were removed.

**CLUNKY:**
> "The word הֶעֱמַדְתָּה (`he'emadta`, 'You made stand'), which is a Hiphil form implying causation, suggests that the stability..."

**FLOWING:**
> "God 'made the mountain stand' (הֶעֱמַדְתָּה) — the causative verb implies that the psalmist's stability was never self-generated but always a gift."

Hebrew should enrich the sentence, not make it harder to read.
```

#### 3.5.2 RULE 6: Blurry Photograph Check

**Insert after line 474** (the `---` separator after RULE 5):

```

### RULE 6: THE BLURRY PHOTOGRAPH CHECK

Abstract nouns without concrete verbs produce sentences that sound impressive but explain nothing.

**WATCH FOR:** atmosphere, density, resonance, texture, dimensions, contours, dynamics, framework, tapestry

If you catch yourself using these words, stop and ask: "What is actually happening in this verse?" Rewrite with concrete verbs.

**BLURRY:** "The verse reflects the covenantal dynamics of divine presence."
**SHARP:** "God's presence here isn't passive background — the psalmist claims it actively makes the difference between life and mere existence."

---
```

#### 3.5.3 Section 5: Reader Transformation

**Insert after line 537** (end of `### 4. UNDEFINED TERMS` content), before the `---` separator:

```

### 5. READER TRANSFORMATION

For each verse, ask: **"After reading this, does the student understand the verse differently than they would from a good English translation?"**

- If the commentary merely restates what the translation shows → WEAK, rewrite
- If it adds trivia without an interpretive shift → WEAK, rewrite
- If it reveals something students couldn't see without Hebrew or scholarly context → STRONG
```

#### 3.5.4 Insight Delivery Checklist Items

**Insert after line 641** (the last checklist item `☐ Would a bright first-year student...`), before `### STAGE 4`:

```
☐ Every Hebrew citation has an interpretive payoff — not just "this word means X"
☐ When a verse has multiple readings, both are named and the tension is explained
☐ No "blurry" sentences — abstract nouns always paired with concrete verbs
☐ Each verse has at least one insight a student couldn't get from the English translation alone
```

**Result:** College checklist grows from 9 items to 13 items.

---

### 3.6 Task 5: MASTER_EDITOR_PROMPT_SI

**File:** `src/agents/master_editor_si.py`
**Mirror Task 3 changes exactly.** The SI main prompt (`MASTER_EDITOR_PROMPT_SI`, lines 46-395) has the same structure as `MASTER_EDITOR_PROMPT_V2` with an added "SPECIAL AUTHOR DIRECTIVE" section.

**Exact insertion points (approximate — verify by matching surrounding text):**

1. **Syntactic Flow Rule** — after the `**Mental checkpoint:**` paragraph in RULE 1 (around line 83)
2. **RULE 6** — after the `---` separator closing RULE 5 (around line 135)
3. **Reader Transformation** — after `### 4. STRUCTURAL ISSUES` content (around line 233)
4. **4 checklist items** — after `☐ **The Author's Special Instruction has been followed...**` at line 371

**Use identical text** to Task 3 (sections 3.4.1-3.4.4).

**Result:** SI checklist grows from 11 items to 15 items.

---

### 3.7 Task 6: COLLEGE_EDITOR_PROMPT_SI

**File:** `src/agents/master_editor_si.py`
**Mirror Task 4 changes exactly.** The SI college prompt (`COLLEGE_EDITOR_PROMPT_SI`, lines 402-688) has the same structure as `COLLEGE_EDITOR_PROMPT_V2` with an added "SPECIAL AUTHOR DIRECTIVE" section.

**Exact insertion points (approximate — verify by matching surrounding text):**

1. **Syntactic Flow Rule** — after the `**Checkpoint:**` paragraph in RULE 1
2. **RULE 6** — after the `---` separator closing RULE 5
3. **Reader Transformation** — after the editorial criteria section (after UNDEFINED TERMS)
4. **4 checklist items** — after `☐ **The Author's Special Instruction has been followed...**` at line 665

**Use identical text** to Task 4 (sections 3.5.1-3.5.4).

**Result:** SI college checklist grows from 10 items to 14 items.

---

## 4. Phase 2a: Insight Extractor Agent

### Task 7: Create `src/agents/insight_extractor.py`

**Pattern to follow:** `src/agents/question_curator.py` (simple agent, JSON output, cost tracking)

### 4.1 Model Selection

**Claude Opus 4.5** (`claude-opus-4-5`) — the specification document calls for a "SMART" model. This is a filtering/judgment task requiring deep comprehension of Hebrew scholarship, not a generation task. Opus 4.5 has a 200,000-token context window.

### 4.2 Input/Output Contract

**Input:**
- `psalm_number` (int)
- `psalm_text` (str) — Hebrew + English verse text
- `micro_analysis_data` (dict) — parsed MicroAnalysis JSON
- `research_bundle_content` (str) — full research bundle markdown

**Output (JSON):**
```json
{
  "psalm_number": 30,
  "psalm_level_insights": [
    {
      "insight": "The verb דָּלָה (draw up) is used for hauling water from wells — the psalmist is a bucket, not a climber",
      "evidence": "BDB lexicon + Exodus 2:16",
      "affects_verses": [2, 4],
      "why_it_matters": "Transforms rescue from active achievement to helpless extraction"
    }
  ],
  "verse_insights": {
    "1": "STANDARD",
    "2": "The rare well-drawing verb transforms the rescue metaphor from 'deliverance' to 'helpless extraction'",
    "6": "Ambiguity between duration reading (favor lasts a lifetime) and existential reading (life exists only within favor) — both are theologically productive"
  }
}
```

### 4.3 Prompt

Use the full `INSIGHT_EXTRACTOR_PROMPT` from `insights_improvement.md` Appendix A.2 (lines 454-518). Key elements:
- Template variables: `{psalm_number}`, `{psalm_text}`, `{micro_analysis}`, `{research_bundle}`
- Double-braces `{{` `}}` for JSON examples in the f-string template
- "Be ruthless" filtering instructions
- 5 categories of high-value insights: reading-changers, puzzle-solvers, productive ambiguities, surprising parallels, commentator gems
- 5 categories of what does NOT count: unhelpful etymology, confirming parallels, "interesting" non-insights, standard grammar, obvious consensus

### 4.4 Class Structure

```python
"""
Insight Extractor Agent (Pre-Synthesis Pass)

Filters research materials to identify high-value interpretive insights
that would make a reader say "I never saw it that way."

Runs between Question Curation (Step 2b) and Synthesis (Step 3).

Model: Claude Opus 4.5 (claude-opus-4-5)
Input: Psalm text + MicroAnalysis JSON + Research Bundle
Output: JSON with psalm-level insights and per-verse cruxes

Author: Claude (Anthropic)
Date: 2026-01-XX
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# Handle imports for both module and script usage
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.utils.logger import get_logger
    from src.utils.cost_tracker import CostTracker
else:
    from ..utils.logger import get_logger
    from ..utils.cost_tracker import CostTracker

INSIGHT_EXTRACTOR_PROMPT = """..."""  # Full prompt from Appendix A.2

class InsightExtractor:
    DEFAULT_MODEL = "claude-opus-4-5"

    def __init__(self, api_key=None, logger=None, cost_tracker=None):
        # Initialize Anthropic client
        # Follow question_curator.py pattern

    def extract_insights(self, psalm_number, psalm_text, micro_analysis_data, research_bundle_content) -> dict:
        # 1. Format micro_analysis_data as readable text
        # 2. Trim research bundle to max 300K chars
        # 3. Build prompt with .format()
        # 4. Call Anthropic API (non-streaming, max_tokens=4096)
        # 5. Parse JSON response
        # 6. Track cost
        # 7. Return parsed dict

    def _format_micro_analysis(self, micro_data: dict) -> str:
        # Convert micro analysis JSON to readable string for prompt
        # Extract verse discoveries, interesting questions, phrases

    def _trim_research_bundle(self, content: str, max_chars: int = 300000) -> str:
        # Simplified version of SynthesisWriter's trimming
        # Priority: remove Related Psalms sections, then trim Figurative Language

    def _parse_response(self, response_text: str) -> dict:
        # Extract JSON from response (handle ```json code blocks)
        # Validate structure: psalm_level_insights list, verse_insights dict
        # Fallback: return empty structure if parsing fails

    def save_insights(self, insights: dict, output_path: Path, psalm_number: int) -> Path:
        # Save to psalm_NNN_insights.json
        # Follow question_curator.save_questions pattern
```

### 4.5 API Call Details

- **Non-streaming**: Output is small JSON (~1-2K chars), no need for streaming
- **max_tokens**: 4096 (sufficient for the JSON output)
- **No extended thinking**: This is a filtering task, not a complex reasoning task
- **Cost estimate**: ~$3-5 per psalm (Opus 4.5 processes ~300K chars input)

### 4.6 Research Bundle Trimming

The Opus 4.5 context window is 200K tokens. Research bundles can exceed 600K characters. The `_trim_research_bundle` method should:

1. Check if content exceeds `max_chars` (default 300K)
2. If so, look for `## Related Psalms` section and remove full psalm texts (keep summaries)
3. If still too long, look for `## Figurative Language` section and trim to 75%, then 50%
4. Never trim: Lexicon, Commentaries, Liturgical, Concordance, Deep Web Research

This mirrors the existing `SynthesisWriter._trim_research_bundle()` logic — refer to that method for the exact section-detection regex patterns.

---

## 5. Phase 2b-2c: Pipeline Integration (Session 242)

### 5.1 Step 2c in run_enhanced_pipeline.py

**Insert between Step 2b (Question Curation, ends ~line 714) and Step 3 (Synthesis, starts ~line 717).**

Follow the Step 2b pattern:
1. Import `InsightExtractor` at the top of the file
2. Define `insights_file = output_path / f"psalm_{psalm_number:03d}_insights.json"` in the file paths section
3. Add the step with conditions: smoke test / already exists / prerequisites met / prerequisites missing
4. Non-fatal: `try/except` with `logger.warning()` on failure

### 5.2 SynthesisWriter Parameter Changes

Add `insights=None` parameter to:
- `write_commentary()` (line 596)
- `_generate_introduction()` (line 1087)
- `_generate_verse_commentary()` (line 1302)

When `insights` is provided, format as a `## PRIORITIZED INSIGHTS` section and append to the research bundle text before building the prompt. This avoids adding new template variables to the prompt strings.

### 5.3 Pipeline Synthesis Call Update

In `run_enhanced_pipeline.py`, before calling `synthesis_writer.write_commentary()`:
- Check if `insights_file.exists()`
- If so, load JSON and pass as `insights=insights_data`
- If not, pass `insights=None` (backward compatible)

---

## 6. Verification Checklist

### After Phase 1 (Prompt Changes)

- [ ] **Template safety**: Search each modified prompt for `RULE A:` and `RULE E:` to confirm insertion (synthesis_writer.py only)
- [ ] **Template safety**: Search each modified prompt for `RULE 6:` and `BLURRY PHOTOGRAPH` to confirm insertion (all 4 editor prompts)
- [ ] **No broken format()**: Search for stray `{` or `}` that would break `.format()` calls
- [ ] **Checklist counts**:
  - V2 main: 14 items (was 10)
  - V2 college: 13 items (was 9)
  - SI main: 15 items (was 11)
  - SI college: 14 items (was 10)
- [ ] **Removed redundancy**: Old "Depth over breadth" single-line note at VERSE_COMMENTARY_PROMPT ~line 416 is gone

### After Phase 2a (Insight Extractor)

- [ ] **Import check**: `python -c "from src.agents.insight_extractor import InsightExtractor; print('OK')"`
- [ ] **Class structure**: Has `extract_insights()`, `_trim_research_bundle()`, `_parse_response()`, `save_insights()` methods

### After Phase 2b-2c (Pipeline Integration — Session 242)

- [ ] **Smoke test**: `python scripts/run_enhanced_pipeline.py [psalm] --smoke-test` creates `psalm_NNN_insights.json`
- [ ] **Full run**: Pipeline produces insights and passes them to Synthesis Writer
- [ ] **Backward compatibility**: Pipeline works normally when no insights file exists

---

## 7. Risk & Mitigation

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| **Template variable breakage** — stray `{` or `}` in inserted text causes `KeyError` | Medium | All inserted text reviewed for brace safety. JSON examples in Insight Extractor prompt use `{{` `}}` |
| **Prompt too long** — Rules A-E add ~2,500 chars to each prompt | Low | Research bundles are 300K+ chars; an extra 2.5K is <1% of total prompt size |
| **Insight Extractor cost** — Opus 4.5 at ~$3-5/psalm | Low | Step is non-fatal (`try/except`), can be skipped. Cost is minor vs. total pipeline cost ($15-30/psalm) |
| **Insight Extractor token limit** — research bundle exceeds 200K token context | Medium | Trimming logic mirrors SynthesisWriter's proven approach. Target 300K chars (~150K tokens + prompt) |
| **College prompt tone mismatch** — V2 rule text too editorial for college audience | Low | College versions use adapted wording ("your students" instead of "the reader") |
| **SI prompt drift** — SI prompts diverge from V2 prompts after changes | Low | Implementation mirrors V2 changes exactly; same text blocks used |

---

*Document prepared: Session 240 (2026-01-26)*
*Implementation begins: Session 241*
