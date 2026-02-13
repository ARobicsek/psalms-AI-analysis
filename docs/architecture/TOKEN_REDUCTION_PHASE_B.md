# Token Reduction Phase B — Implementation Guide

**Created**: Session 257 (2026-02-12)
**Purpose**: Ready-to-execute instructions for Phase B token reduction. All planning was done in Session 257; this document contains everything needed to implement without re-exploring the codebase.

---

## What Was Already Done (Phase A, Session 257)

| Win | Change | File | Savings |
|-----|--------|------|---------|
| Win 1 | Commentator bios → dates only | `research_assembler.py` | ~10,500 chars |
| Win 3 | Removed duplicate analytical framework from bundle | `research_assembler.py` | ~9-25K chars |
| Win 8 | Strip `working_notes` from macro→micro | `analysis_schemas.py`, `micro_analyst.py` | ~27K chars |

**Total Phase A savings**: ~45K tokens per psalm

---

## Phase B Tasks (This Session)

### B1. Win 4 — Always Trim Related Psalms (no full texts)

**Problem**: Related Psalms section = 49,129 chars (16.8% of PS34 bundle). Includes full Hebrew+English texts of 5 related psalms. Full texts are rarely cited verbatim in output.

**Current behavior**: `RelatedPsalmsLibrarian.format_for_research_bundle()` (line 137 of `src/agents/related_psalms_librarian.py`) includes full text by default, only strips them progressively if section exceeds `max_size_chars` (100K default).

**Fix**: Add a `include_full_text=False` default to `format_for_research_bundle()`, or simply pass `max_size_chars=0` (but cleaner to add a flag). The method already has `_format_single_match()` which accepts `include_full_text` boolean — we just need the outer loop to default to `False`.

**Option A (cleanest)**: Add parameter `include_full_text: bool = False` to `format_for_research_bundle()`:
```python
def format_for_research_bundle(
    self,
    psalm_number: int,
    related_matches: List[RelatedPsalmMatch],
    max_size_chars: int = 100000,
    include_full_text: bool = False  # NEW: default to compact
) -> str:
```
Then when `include_full_text=False`, skip the progressive loop and just format all matches with `include_full_text=False`:
```python
if not include_full_text:
    md = preamble
    for match in related_matches:
        md += self._format_single_match(psalm_number, match, include_full_text=False)
    return md
```

**Callers**: `research_assembler.py` line 910 calls `format_for_research_bundle()`. No change needed there if we change the default.

**Expected savings**: ~30-40K chars (full texts removed, relationship metadata + shared phrases retained)

**Verification**: After change, run `len(related_psalms_markdown)` in a quick test and compare to PS34's 49,129.

---

### B2. Win 2 — Truncate BDB Lexicon Entries to ~500 chars

**Problem**: Full BDB entries average ~2,400 chars each. PS34 has 25 entries = 33,677 chars. Entries include exhaustive inflection tables, every biblical reference, Aramaic/Arabic cognates.

**Location**: `research_assembler.py` `to_markdown()` method, lines 176-202. This is where lexicon entries are formatted. The raw entry text comes from `entry['entry']` (the full BDB text).

**Current formatting** (lines ~185-202):
```python
md += f"**Lexicon**: {entry.get('lexicon_name', 'Unknown')}\n"
md += f"**Vocalized**: {entry.get('headword', '')}\n"
md += f"**Strong's**: {entry.get('strong_number', '')}\n"
md += f"**Pronunciation**: {entry.get('transliteration', '')}\n\n"
md += f"{entry.get('entry', '')}\n\n"
# ... etymology, derivatives, URL
```

**Fix**: Truncate `entry.get('entry', '')` to ~500 chars. Strategy:
1. Take first 700 chars of the entry text
2. Find the last complete sentence or line break within that range (don't cut mid-word)
3. Append `[...]` to indicate truncation
4. Only truncate if entry > 800 chars (leave short entries intact)

**Implementation** — add a helper function in `research_assembler.py`:
```python
def _truncate_bdb_entry(text: str, max_chars: int = 500) -> str:
    """Truncate a BDB lexicon entry to max_chars, preserving complete lines."""
    if len(text) <= max_chars + 100:  # Small buffer to avoid cutting near end
        return text
    # Find last newline or period before max_chars
    truncated = text[:max_chars]
    # Try to break at a newline
    last_newline = truncated.rfind('\n')
    last_period = truncated.rfind('. ')
    break_point = max(last_newline, last_period + 1)
    if break_point > max_chars * 0.5:  # Only use natural break if it's past halfway
        truncated = text[:break_point + 1]
    return truncated.rstrip() + "\n[...]"
```

Then in `to_markdown()` where `entry.get('entry', '')` is used, replace with:
```python
md += f"{_truncate_bdb_entry(entry.get('entry', ''))}\n\n"
```

**Expected savings**: ~33K → ~12K = ~21K chars

---

### B3. Win 6 — Compact Markdown Formatting

**Problem**: Research bundle uses verbose markdown formatting. Every lexicon entry has 4 labeled lines before the content even starts. Concordance results have multi-line headers. Commentary entries have verbose labels.

**Location**: All within `research_assembler.py` `to_markdown()` method (line 167+).

**Changes by section**:

#### Lexicon entries (lines 176-202):
**Before**:
```
### טַעַם
**Lexicon**: BDB Dictionary
**Vocalized**: טַ֫עַם
**Strong's**: H2940
**Pronunciation**: ta'am

[full entry text...]

**Etymology (Klein)**: [text]
**Derivatives**: [text]
```

**After**:
```
### טַעַם [BDB H2940] *ta'am*
[truncated entry text...]
Klein: [etymology]. Derivatives: [derivatives]
```

#### Concordance results (lines 204-303):
**Before**:
```
### Concordance Search: [phrase]
**Primary phrase**: טַעַם
**Variants searched**: טעם, טַעְמוֹ
**Total results**: 15 results
**Scope**: Full Tanakh
**Level**: word

| Ref | Hebrew | English | Match | Pos |
```

**After**:
```
### [phrase] (15 results, Full Tanakh, word)
Variants: טעם, טַעְמוֹ

Ref | Hebrew | English | Match
```

#### Commentary entries (lines 458-488):
**Before**:
```
### Psalm 34:2
**Why this verse**: [reason]
**Commentator**: Rashi
**Hebrew**: [text]
**English**: [text]
```

**After**:
```
### 34:2 — Rashi
*[reason]*
[Hebrew text]
[English text]
```

**Target**: ~15-20% reduction across all sections. Focus on removing redundant labels, merging single-value lines, using inline notation.

**Important**: The Master Writer prompt does NOT reference specific markdown formatting patterns in the research bundle (it references section headers like `## Hebrew Lexicon` but not internal field labels). So compact formatting won't break prompt parsing.

---

### B4. Win 9 — Telegraphic Style for Macro/Micro Outputs

**Problem**: Macro and micro analyst outputs use full flowing prose. These outputs feed downstream agents that can parse fragments equally well. Full prose = ~20% more tokens.

**Files**:
- `src/agents/macro_analyst.py`: `MACRO_ANALYST_PROMPT` starts at line 46
- `src/agents/micro_analyst.py`: `DISCOVERY_PASS_PROMPT` starts at line 72

**Fix**: Add telegraphic writing instructions to both prompts.

**For MACRO_ANALYST_PROMPT** — add near the end of the prompt, before the output format section:
```
## Writing Style
Your output will be consumed by downstream AI agents, not humans. Write telegraphically:
- Sentence fragments and bullets over full sentences
- Drop articles (the, a, an) and filler words where meaning is preserved
- No transition sentences ("Moving on to...", "As we can see...")
- Dense notation: use abbreviations, compact references
- Exception: thesis_statement should still be a complete, clear sentence
```

**For DISCOVERY_PASS_PROMPT** — similar instruction, but note that observations are already constrained to "2-4 sentences" (line 143). Add:
```
## Writing Density
Output consumed by downstream AI agents. Maximize information density:
- Fragments over full sentences in all fields except where JSON schema requires sentences
- Drop articles/filler. E.g., "Chiastic structure vv.3-9, pivot at v.6" not "There is a chiastic structure spanning verses 3-9, with the pivot point at verse 6"
- Lexical insights: word + meaning + significance only. No "interestingly" or "it is worth noting"
```

**Risk**: Medium. Macro output (46K chars) feeds micro analyst and Master Writer. Micro output (71K chars) feeds Master Writer. The Master Writer prompt says to use these as source material — it should handle telegraphic input fine. But verify on a test psalm that output quality doesn't degrade.

**Expected savings**: Macro 46K × 20% = ~9K chars; Micro 71K × 20% = ~14K chars

---

## Verification Plan

After implementing all Phase B changes:

1. **Quick check**: Run research assembly only for a psalm (e.g., Psalm 1 or 34) and compare bundle size before/after
2. **Full pipeline test**: Run the complete pipeline on a short psalm to verify:
   - No crashes or parsing errors
   - Commentary quality is maintained
   - Cost tracking reflects reduced input sizes
3. **Before/after comparison**:
   - PS34 bundle was 291,731 chars → target: ~180-200K chars (30-35% reduction)
   - PS34 micro analyst input was ~50K chars → should drop by ~9K (working notes already removed) + ~9K (telegraphic macro)

---

## Summary Table

| Win | Task | File(s) | Est. Savings | Risk |
|-----|------|---------|-------------|------|
| B1 (Win 4) | Related psalms: no full texts | `related_psalms_librarian.py` | 30-40K chars | Low |
| B2 (Win 2) | BDB entries: truncate to 500 chars | `research_assembler.py` | ~21K chars | Medium |
| B3 (Win 6) | Compact markdown formatting | `research_assembler.py` | 15-20% (~45-60K) | Low |
| B4 (Win 9) | Telegraphic macro/micro outputs | `macro_analyst.py`, `micro_analyst.py` | ~23K chars | Medium |

**Combined Phase A + B target**: ~$5.00 → ~$4.00-4.25 per psalm (15-20% cost reduction)

---

## Items Explicitly Deferred (Do NOT Implement)

- **Win 5** (slim IE bundle): User worried about insight quality degradation
- **Win 7** (macro/micro dedup for Master Writer): Macro content NOT fully captured in micro — unsafe
- **JSON conversion**: Content-level reductions are higher impact; defer pending results
