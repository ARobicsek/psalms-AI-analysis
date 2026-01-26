# Insight Quality Improvements: Implementation Guide

**Date:** January 26, 2026  
**Purpose:** Transform the Psalms Commentary Pipeline from data aggregation to interpretive synthesis  
**Priority:** High — addresses core quality issue affecting reader engagement

---

## Executive Summary

The pipeline successfully automates the "gathering" phase of scholarship (lexicon, concordance, liturgy, parallels). The problem is the transition from **Data Aggregation** to **Interpretive Synthesis**.

Currently, agents act like **Librarians** (stacking relevant facts on the table) rather than **Curators** (explaining why this specific arrangement of facts changes meaning). The result: paragraphs that sound scholarly but deliver no interpretive payoff—"smart-sounding fluff."

**The Core Fix:** Every linguistic observation must answer "So what?" Every ambiguity must be either resolved or explained as generative. Depth beats breadth.

---

## Table of Contents

1. [Diagnosis: The Fluff Problem](#1-diagnosis-the-fluff-problem)
2. [Phase 1: Immediate Prompt Changes](#2-phase-1-immediate-prompt-changes)
3. [Phase 2: Architectural Addition](#3-phase-2-architectural-addition)
4. [Phase 3: Validation & Testing](#4-phase-3-validation--testing)
5. [Appendix: Full Prompt Insertions](#appendix-full-prompt-insertions)

---

## 1. Diagnosis: The Fluff Problem

### Example (Psalm 30:6)

**Current output:**
> "The first colon compresses a doctrine of divine character into four words. רֶגַע ("moment") contrasts with חַיִּים ("life/lifetime"). אַף ("anger") is an anthropomorphism, literally "nose" — flared nostrils. רָצוֹן (favor, goodwill, acceptance) is a key biblical term. In the sacrificial laws, offerings are brought לִרְצוֹנוֹ לִפְנֵי ה׳ — "for his acceptance before YHWH" (Leviticus 1:3). Here, it is the atmosphere in which life thrives: 'life is in His ratzon.'"

**Problems identified:**
1. **Orphaned facts:** "רָצוֹן is a key biblical term" tells us nothing
2. **No interpretive commitment:** The verse has two possible readings (duration vs. existential dependence) — the commentary straddles both without illuminating either
3. **Blurry conclusion:** "the atmosphere in which life thrives" sounds profound but is conceptually empty
4. **Cataloguing over insight:** Lists features (anthropomorphism, cultic usage) without explaining what they *do*

**Target output:**
> "The parallelism creates a puzzle. The first half contrasts 'moment' with 'lifetime' — we expect a simple duration claim: anger is brief, favor is lasting. But the Hebrew of the second half (*chayim birtzono*) admits a more radical reading: not just that favor *lasts* a lifetime, but that life itself *exists only within* God's favor. The word *ratzon* is technical cultic language — a sacrifice is either 'accepted' (*lirtzon*) or rejected (Lev 1:3). By applying altar-language to daily existence, the psalmist suggests that 'life' is not merely biological survival but the state of being acceptable to God. Outside that acceptance, one may exist, but one is not truly alive."

**What changed:**
- Named the ambiguity explicitly
- Committed to showing why both readings matter
- Connected the cultic parallel to an interpretive payoff
- Gave the reader something they couldn't get from the translation alone

---

## 2. Phase 1: Immediate Prompt Changes

### 2.1 Add "No Orphaned Facts" Rule

**Files to modify:**
- `src/agents/synthesis_writer.py` — both `INTRODUCTION_ESSAY_PROMPT` and `VERSE_COMMENTARY_PROMPT`
- `src/agents/master_editor.py` — `MASTER_EDITOR_PROMPT_V2`

**Insert the following block** in the "Critical Requirements" or "Ground Rules" section of each prompt:

```markdown
### RULE: NO ORPHANED FACTS (The "So What?" Test)

Every linguistic, historical, or philological observation MUST have an immediate interpretive payoff. You are FORBIDDEN from stating a fact without explaining how it changes the reader's understanding.

**ORPHANED FACT (BAD):**
> "The word *ratzon* implies acceptance, used in Leviticus for sacrifices. Here it suggests life is in his favor."

This is fluff — it lists a fact and then drifts into vagueness. The reader learns nothing.

**SEMANTIC PAYOFF (GOOD):**
> "The word *ratzon* is technical cultic language for a sacrifice being 'accepted' (Lev 1:3). By applying this altar-language to daily existence, the psalmist suggests that 'life' is not merely biological survival, but the state of being acceptable to God."

**Self-check before finalizing any paragraph:** 
- Can the reader understand this observation from the English translation alone? If yes, cut it or develop it.
- Does this observation change HOW the verse reads, or just ADD trivia? If just trivia, cut it.
- Would a curious reader say "I never thought of it that way" or just "okay, interesting"? Aim for the former.
```

---

### 2.2 Add Ambiguity Handling Protocol

**Files to modify:** Same as above

**Insert immediately after the "No Orphaned Facts" rule:**

```markdown
### RULE: COMMIT TO AMBIGUITY (Don't Blend, Explain)

When a verse admits multiple readings, DO NOT blend them into a vague synthesis that hedges between positions. This produces sentences that sound smart but say nothing.

**Instead, you MUST do one of the following:**

**Option A — Commit to one reading:**
> "The phrase can be read two ways, but X is more compelling because [evidence]. The alternative reading (Y) falters because [reason]."

**Option B — Explain why the ambiguity is generative:**
> "The Hebrew sustains two readings simultaneously: X and Y. This is not carelessness but craft — the ambiguity forces the reader to hold both ideas in tension, which [explain the theological/poetic effect]."

**Option C — Show how context resolves it:**
> "In isolation, the phrase is ambiguous between X and Y. But the surrounding verses favor X because [structural/thematic evidence]."

**NEVER do this (the hedge-blend):**
> "The phrase suggests both duration and existential dependence, reflecting the theological density of the psalm's vision."

This sentence commits to nothing. It is the enemy. Kill it.
```

---

### 2.3 Add the "Blurry Photograph" Check

**File to modify:** `src/agents/master_editor.py` — `MASTER_EDITOR_PROMPT_V2`

**Add to the "Ground Rules" section, after RULE 4 (Show, Don't Tell):**

```markdown
### RULE 5: THE BLURRY PHOTOGRAPH CHECK

Abstract nouns without concrete verbs produce "blurry" sentences — they sound profound but show nothing.

**BLURRY (delete or rewrite):**
> "Here, it is the atmosphere in which life thrives: 'life is in His ratzon.'"
> "The verse reflects the theological density of the covenantal relationship."
> "This creates resonance with the broader Israelite worldview."

These sentences use impressive words ("atmosphere," "density," "resonance," "worldview") as a substitute for actual explanation.

**SHARP (this is what we want):**
> "Divine favor is not just an event but the oxygen of existence — without it, the psalmist implies, you may breathe but you are not alive."
> "The psalmist makes God's acceptance the precondition for life itself, not just its enhancement."

**Self-check:** If your sentence contains abstract nouns (density, resonance, atmosphere, dynamics, contours, dimensions) without a concrete verb showing what God or the psalmist *does*, STOP. Rewrite until you can see the action.
```

---

### 2.4 Add Depth-Over-Breadth Instruction

**Files to modify:** 
- `src/agents/synthesis_writer.py` — `VERSE_COMMENTARY_PROMPT`
- `src/agents/master_editor.py` — `MASTER_EDITOR_PROMPT_V2`

**Find the section listing scholarly angles** (poetics, Vorlage, comparative religion, etc.) **and add:**

```markdown
### DEPTH BEATS BREADTH

You have access to many scholarly angles: poetics, textual criticism, ANE parallels, figurative language, traditional commentaries, liturgical usage, etc.

**DO NOT try to cover all angles for every verse.** This produces shallow cataloguing.

**INSTEAD:** For each verse, choose the 1-3 angles that actually transform the reading. A reader who learns ONE thing that changes how they see the verse will remember it. A reader shown TEN mildly interesting facts will remember none.

**Ask yourself:**
- Which angle makes this verse *surprising*?
- Which angle resolves a puzzle or creates a productive tension?
- Which angle connects this verse to something the reader already cares about?

Pursue THOSE angles deeply. Ignore the rest for this verse.
```

---

### 2.5 Improve Hebrew Integration Syntax

**File to modify:** `src/agents/master_editor.py` — under RULE 1 (Hebrew and English)

**Add this sub-rule:**

```markdown
**Syntactic Flow Rule:** 

The English sentence must make complete grammatical sense if the Hebrew were removed. Use Hebrew as a parenthetical anchor, not a speed bump that derails the sentence.

**CLUNKY (Hebrew interrupts the logic):**
> "The word הֶעֱמַדְתָּה (`he'emadta`, 'You made stand'), which is a Hiphil form implying causation, suggests that the stability..."

**FLOWING (Hebrew supports without interrupting):**
> "God 'made the mountain stand' (הֶעֱמַדְתָּה) — the causative verb implies that the psalmist's stability was never self-generated but always a gift."

The reader should feel the Hebrew enriches the sentence, not that they're jumping over hurdles.
```

---

### 2.6 Add "Reader Transformation" Success Criterion

**File to modify:** `src/agents/master_editor.py` — add to the assessment criteria

```markdown
### ASSESSMENT CRITERION: READER TRANSFORMATION

For each verse commentary, ask: **"After reading this, does the reader understand the verse differently than they would from the translation alone?"**

- If the commentary merely confirms what the translation already shows → WEAK, needs rewriting
- If the commentary adds historical trivia but no interpretive shift → WEAK, needs rewriting  
- If the commentary reveals something the reader couldn't see without the Hebrew/context → STRONG

**For the introduction essay, ask:** "Does the reader now have a framework for understanding the whole psalm that they didn't have before?"

Flag any verse commentary that fails the transformation test in your assessment.
```

---

## 3. Phase 2: Architectural Addition

### 3.1 The "Insight Extractor" Pass

**Rationale:** The Synthesis Writer is overwhelmed by data volume (Research Bundle + Micro + Macro). It defaults to safe summarization rather than bold interpretation. An intermediate filtering step forces *decision-making* before *writing*.

**Implementation:**

Create a new agent: `src/agents/insight_extractor.py`

**Which LLM:** 
-needs to be SMART. Suggest Claude Opus 4.5 (claude-opus-4-5), effort: "high". Note a 200,000 token limit.

**Input:** 
- MicroAnalysis JSON
- ResearchBundle markdown (or a trimmed version)
- Psalm text

**Output:** 
- JSON object with:
  - `psalm_level_insights`: List of 3-5 "aha!" moments for the whole psalm
  - `verse_insights`: Dict mapping verse numbers to their single most important crux (or "STANDARD" if nothing remarkable)

**Prompt core logic:**

```markdown
You are an Insight Curator for biblical commentary. Your job is to FILTER, not to write.

You will receive research materials for Psalm {psalm_number}. Most of this material is useful background but not transformative. Your task is to identify ONLY the moments where:

1. A standard reading is wrong or incomplete
2. A Hebrew nuance fundamentally changes the meaning
3. A parallel or allusion creates unexpected resonance
4. An ambiguity is theologically productive (not just unclear)
5. A traditional commentator says something genuinely surprising

**For the whole psalm, identify 3-5 "Aha!" insights** — the things that would make a thoughtful reader say "I never saw it that way."

**For each verse, identify at most ONE crux** — the single most important thing to explain. If a verse has only standard philology with no transformative insight, output "STANDARD" for that verse.

**Output format:**
```json
{
  "psalm_level_insights": [
    {
      "insight": "The verb דָּלָה (draw up) is used for hauling water from wells — the psalmist is a bucket, not a climber",
      "source": "BDB lexicon + Exodus 2:16",
      "affects_verses": [2, 4]
    },
    ...
  ],
  "verse_insights": {
    "1": "STANDARD",
    "2": "The rare well-drawing verb transforms the rescue metaphor from 'deliverance' to 'helpless extraction'",
    "6": "Ambiguity between duration reading (favor lasts a lifetime) and existential reading (life exists only within favor) — both are theologically productive",
    ...
  }
}
```

**Critical instruction:** Be ruthless. If an observation is merely "interesting" but doesn't change how the verse reads, DO NOT include it. We want the 20% of insights that deliver 80% of the value.
```

**Pipeline integration:**

Modify `run_pipeline.py` to insert this step between MicroAnalysis and SynthesisWriter:

```
[2] Micro Analysis
    ↓
[2b] Insight Extraction (NEW)
    ↓
[3] Synthesis Writing (now receives curated insights)
```

**Modify SynthesisWriter** to receive the curated insights and include this instruction:

```markdown
### PRIORITIZED INSIGHTS

You have received a curated list of high-value insights from the Insight Extractor. These represent the most transformative observations from the research materials.

**PRIORITIZE THESE INSIGHTS** above all other data. Your verse commentaries should be built around these cruxes. Other material from the Research Bundle is supporting evidence, not the main event.

For verses marked "STANDARD" in the insight list, keep the commentary brief and functional — don't pad with low-value observations.
```

---

### 3.2 Modify Master Editor to Check for Insight Delivery

**Add to assessment criteria in `MASTER_EDITOR_PROMPT_V2`:**

```markdown
### INSIGHT DELIVERY CHECK

Before finalizing, review the commentary against this checklist:

**For the Introduction:**
- [ ] Does it have a clear central argument (not just a summary of the psalm's contents)?
- [ ] Does it answer at least one of the Reader Questions in a substantive way?
- [ ] Would a reader who finished it be able to explain "what this psalm is really about" to someone else?

**For each verse commentary:**
- [ ] Does it contain at least one observation the reader couldn't derive from the English translation?
- [ ] Does every Hebrew citation have an interpretive payoff?
- [ ] If ambiguity exists, is it explicitly addressed (not hedge-blended)?
- [ ] Does the paragraph have a point, or is it just a list of features?

**Flag in your assessment** any verse that fails these checks. Prioritize rewriting those verses.
```

---

## 4. Phase 3: Validation & Testing

### 4.1 Create a "Fluff Detection" Test Suite

After implementing changes, run the pipeline on 3-5 psalms and manually evaluate:

**Fluff Indicators (should decrease):**
- Sentences with abstract nouns but no concrete verbs
- Hebrew citations without interpretive payoff within 2 sentences
- Phrases like "reflects the theological density," "resonates with," "suggests the atmosphere of"
- Paragraphs that could be reduced to one sentence without losing meaning

**Quality Indicators (should increase):**
- Explicit "This verse can be read two ways" formulations followed by resolution
- "This changes how we read..." or "The reader now sees..." transitions
- Concrete verbs: "God does X," "The psalmist claims Y," "This implies Z"
- Reader could explain the insight to someone else in one sentence

### 4.2 A/B Comparison

For one psalm, generate commentary with:
- **Version A:** Current prompts (control)
- **Version B:** Updated prompts with all Phase 1 changes

Have 3 target readers (ideally matching your audience: intellectually curious, not biblical scholars) read both and identify:
1. Which version had more "aha!" moments?
2. Which version felt longer than it needed to be?
3. Which version would they finish vs. abandon?

### 4.3 Specific Regression Tests

After changes, verify these specific improvements:

| Test Case | Current Behavior | Target Behavior |
|-----------|------------------|-----------------|
| Ps 30:6 "life in His favor" | Vague "atmosphere" language | Explicit duration vs. existential reading |
| Any verse with Hebrew citation | Citation often orphaned | Citation always has payoff within 2 sentences |
| Long verse commentaries (400+ words) | Sometimes padded with low-value observations | Length justified by insight density |
| Verses with ambiguity | Hedge-blend | Explicit "two readings" + resolution |

---

## Appendix: Full Prompt Insertions

### A.1 Complete "Insight Quality Rules" Block

Insert this complete block into both `VERSE_COMMENTARY_PROMPT` and `MASTER_EDITOR_PROMPT_V2`:

```markdown
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

---

### A.2 Insight Extractor Full Prompt

```python
INSIGHT_EXTRACTOR_PROMPT = """You are an Insight Curator for biblical commentary on Psalm {psalm_number}.

Your job is to FILTER, not to write. You will receive extensive research materials. Most of this material is useful background but not transformative. 

**Your task:** Identify ONLY the insights that would make a thoughtful reader say "I never saw it that way."

## WHAT COUNTS AS A HIGH-VALUE INSIGHT

1. **Reading-changers:** A Hebrew nuance that fundamentally alters meaning (not just adds color)
2. **Puzzle-solvers:** Something that explains why the text says X instead of the expected Y
3. **Productive ambiguities:** Cases where the text deliberately sustains multiple readings
4. **Surprising parallels:** Connections to other texts that create unexpected meaning
5. **Commentator gems:** Traditional interpretations that are genuinely illuminating (not just pious)

## WHAT DOES NOT COUNT

- Etymology that doesn't change interpretation
- Parallels that merely confirm what we already see
- "Interesting" facts that don't alter reading
- Standard grammatical observations
- Consensus scholarly views that are already obvious

## YOUR INPUTS

### PSALM TEXT
{psalm_text}

### MICRO ANALYSIS (verse discoveries)
{micro_analysis}

### RESEARCH BUNDLE (lexicon, concordance, commentaries, etc.)
{research_bundle}

## YOUR OUTPUT

Return a JSON object with this structure:

```json
{{
  "psalm_level_insights": [
    {{
      "insight": "[One sentence describing the transformative observation]",
      "evidence": "[Source: BDB, Rashi, concordance pattern, etc.]",
      "affects_verses": [list of verse numbers this insight illuminates],
      "why_it_matters": "[One sentence on interpretive payoff]"
    }}
  ],
  "verse_insights": {{
    "1": "[Single most important crux for this verse, or 'STANDARD' if nothing remarkable]",
    "2": "[...]",
    ...
  }}
}}
```

## CRITICAL INSTRUCTIONS

1. **Be ruthless.** If an observation is merely "interesting" but doesn't change how the verse reads, DO NOT include it.
2. **Quality over quantity.** 3 transformative insights beat 10 mild ones.
3. **Psalm-level insights:** Maximum 5. These are the "big ideas" that organize the whole psalm.
4. **Verse insights:** Maximum 1 per verse. If a verse has only standard content, mark it "STANDARD" — this is useful information (tells the writer not to pad that verse).
5. **Be specific.** "The water-drawing verb changes the rescue metaphor" is good. "Interesting vocabulary" is useless.

Return ONLY the JSON object. No preamble or explanation.
"""
```

---

## Implementation Checklist

### Phase 1: Prompt Changes (Implement First)
- [ ] Add "Insight Quality Rules" block to `synthesis_writer.py` — `VERSE_COMMENTARY_PROMPT`
- [ ] Add "Insight Quality Rules" block to `synthesis_writer.py` — `INTRODUCTION_ESSAY_PROMPT`  
- [ ] Add "Insight Quality Rules" block to `master_editor.py` — `MASTER_EDITOR_PROMPT_V2`
- [ ] Add "Syntactic Flow Rule" to master editor Hebrew integration section
- [ ] Add "Reader Transformation" assessment criterion to master editor
- [ ] Add "Insight Delivery Check" to master editor assessment section

### Phase 2: Architectural Changes (If Phase 1 insufficient)
- [ ] Create `insight_extractor.py` agent
- [ ] Modify `run_pipeline.py` to insert Insight Extraction step
- [ ] Modify Synthesis Writer to receive and prioritize curated insights
- [ ] Test pipeline with new step on 2-3 psalms

### Phase 3: Validation
- [ ] Run A/B comparison on one psalm
- [ ] Check regression tests (Ps 30:6, orphaned citations, ambiguity handling)
- [ ] Get reader feedback on insight density vs. fluff

---

## Success Metrics

After implementation, commentary should show:

| Metric | Before | Target |
|--------|--------|--------|
| "Hedge-blend" sentences per psalm | 5-10 | 0-2 |
| Hebrew citations with payoff within 2 sentences | ~60% | >90% |
| Verses where reader learns something beyond translation | ~50% | >80% |
| Reader completion rate (anecdotal) | "give up halfway" | "finish and remember insights" |

---

*Document prepared: January 26, 2026*
*For questions, contact the commentary pipeline team.*