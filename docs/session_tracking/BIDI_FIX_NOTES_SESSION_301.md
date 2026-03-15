# BiDi Fix Attempt — Session 301

**Status**: Reverted due to regressions. Retry in next session.

## Problem

Two BiDi rendering issues in Psalm 40 output:

1. **Markdown (Issue 6)**: In `Here the third חפץ: חֲפֵצֵי רָעָתִי` (verse 15), the colon after the first Hebrew word gets absorbed into the RTL run, visually scrambling the word order.

2. **DOCX (Issue 7)**: In `Here the second חפץ: חָפָצְתִּי` (verse 9), bare inline Hebrew without parentheses/brackets lacks directional isolation, causing Word's BiDi algorithm to misplace neutral characters (colons, commas).

## Attempted Fix 1: Markdown LRM Insertion (copy_editor.py)

Added `_fix_markdown_bidi()` static method and integrated as Step 7 in the copy editor pipeline.

```python
@staticmethod
def _fix_markdown_bidi(text: str) -> str:
    """
    Insert LRM (Left-to-Right Mark, U+200E) after punctuation that follows
    Hebrew text in markdown. This prevents BiDi renderers from absorbing
    colons, commas, and semicolons into RTL Hebrew runs, which scrambles
    the visual display order in mixed Hebrew/English inline text.

    Example: "חפץ: חָפָצְתִּי" -> "חפץ:\u200E חָפָצְתִּי"
    """
    LRM = '\u200E'
    # Match: Hebrew word (with optional nikud/marks) followed by colon, semicolon, or comma
    # Insert LRM after the punctuation to anchor it to the LTR context
    pattern = r'([\u05D0-\u05EA][\u0590-\u05FF]*)([:;,])'
    return re.sub(pattern, rf'\1\2{LRM}', text)
```

**Integration point**: After `_reassemble()` (step 6), before `_generate_diff()`.

**Result**: Introduced regressions. Needs more careful testing.

## Attempted Fix 2: DOCX RLI/PDI Wrapping (document_generator.py)

Added bare inline Hebrew wrapping with RLI/PDI to `_process_text_rtl()`, with placeholder protection to avoid double-wrapping already-processed LRO/PDF blocks.

```python
# Added to _process_text_rtl() after verse_ref_pattern handling:

# Bare inline Hebrew — wrap with RLI/PDI for bidirectional isolation
# This prevents Word's BiDi algorithm from absorbing neutral characters
# (colons, commas) into Hebrew RTL runs, which scrambles display order.
# First, protect existing LRO...PDF blocks from being re-processed.
placeholders = {}
def _save_lro_block(match):
    key = f'\x00BIDI{len(placeholders)}\x00'
    placeholders[key] = match.group(0)
    return key
modified = re.sub(r'\u202D[^\u202C]*\u202C', _save_lro_block, modified)

RLI = '\u2067'  # RIGHT-TO-LEFT ISOLATE
PDI = '\u2069'  # POP DIRECTIONAL ISOLATE
bare_hebrew_pattern = r'([\u05D0-\u05EA][\u0590-\u05FF]*(?:\s+[\u05D0-\u05EA][\u0590-\u05FF]*)*)'
if re.search(bare_hebrew_pattern, modified):
    def _wrap_bare_hebrew(match):
        return f'{RLI}{match.group(1)}{PDI}'
    modified = re.sub(bare_hebrew_pattern, _wrap_bare_hebrew, modified)

# Restore protected LRO...PDF blocks
for key, value in placeholders.items():
    modified = modified.replace(key, value)
```

**Result**: Introduced regressions. Needs more careful testing.

## Attempted Fix 3: Code Deduplication (document_generator.py)

Replaced 4 duplicated inline BiDi code blocks (~160 lines total) with single calls to `self._process_text_rtl()`:
- `_process_markdown_formatting()` plain text branch (was ~45 lines)
- `_add_formatted_content()` nested formatting branch (was ~40 lines)
- `_add_formatted_content()` no-nested-formatting branch (was ~40 lines)
- `_add_paragraph_with_soft_breaks()` (was ~40 lines)

Each block was replaced with:
```python
modified_part = self._process_text_rtl(part)
run = paragraph.add_run(modified_part)
```

**Result**: Reverted along with the RLI/PDI fix since the deduplication depends on the new code in `_process_text_rtl()`. The deduplication itself was sound but can't be separated from the broken BiDi additions.

## Notes for Next Session

- The core idea (isolating bare Hebrew with RLI/PDI) is correct in principle but the regex is too aggressive — it wraps ALL Hebrew text, including text that's already handled by `_is_primarily_hebrew()` / `_reverse_primarily_hebrew_line()`.
- The deduplication collapsed 4 code paths that had slightly different behaviors (some check `_is_primarily_hebrew()` first, some handle `text` vs `part` vs `line`) into one — this may have been the source of regressions.
- The LRM fix for markdown may interact badly with existing Hebrew text that doesn't need anchoring.
- Test with specific psalms (40, 22) and check both MD rendering AND DOCX output in Word before committing.

## Session 302 Plan (Ready to Implement)

**Approach**: Use **LRM (U+200E)** instead of RLI/PDI. LRM is a zero-width character supported since Unicode 1.0 that Word handles reliably. RLI/PDI (Unicode 6.3 isolates) are rendered as visible dashed boxes in Word — do NOT use them.

**Root cause**: When a neutral character (colon, semicolon, comma) appears between two RTL (Hebrew) segments in an LTR paragraph, the Unicode BiDi algorithm resolves the neutral character to RTL. This causes the entire Hebrew+neutral+Hebrew sequence to be displayed as one RTL run, visually scrambling the word order.

**Fix**: Insert LRM after Hebrew+punctuation sequences. The LRM creates an explicit LTR boundary that prevents the neutral character from joining the RTL run.

```python
# Add to _process_text_rtl() after verse_ref_pattern handling,
# BEFORE trailing punctuation RLM:
LRM = '\u200E'
bare_hebrew_punct = r'([\u05D0-\u05EA][\u0590-\u05FF]*)([:;,])'
modified = re.sub(bare_hebrew_punct, rf'\1\2{LRM}', modified)
```

**Where to add** (5 code paths in document_generator.py):
1. `_process_text_rtl()` line ~203 — the centralized function
2. `_process_markdown_formatting()` else branch, line ~962 — plain text
3. `_add_formatted_content()` nested formatting else branch, line ~1064 — nested plain text
4. `_add_formatted_content()` no-nested else branch, line ~1112 — no-nested plain text
5. `_add_paragraph_with_soft_breaks()` else branch, line ~1188 — soft breaks

**Why this is safe**:
- LRM is zero-width and invisible — cannot produce visible "RLI/PDI" dashes
- Runs AFTER paren/bracket processing, so LRO/PDF-wrapped Hebrew won't match (LRO breaks the `[\u05D0-\u05EA]` regex)
- Full Hebrew lines are already handled by `_is_primarily_hebrew()` check before reaching this code
- Even in cases where the LRM is unnecessary (e.g., Hebrew+comma+English), it merely reinforces the existing LTR context — no visual change

**Deduplication** (optional, separate step): The 4 duplicate code blocks can be replaced with calls to `_process_text_rtl(part)`, but `_process_text_rtl()` includes `_is_hebrew_dominant()` which the duplicate branches intentionally skip. Either add a `check_hebrew_dominant=True` parameter, or keep the duplicates. Do this as a separate commit after verifying the LRM fix works.

**Testing**: Regenerate Psalm 40 DOCX, check verses 9, 15, 16–18 in Word. Also spot-check Psalm 22.
