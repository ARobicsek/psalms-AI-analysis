# NEXT SESSION — remove the Analytical Framework from the writer prompt

**Set by**: the author at the close of Session 378, after reading the Psalm 27 A/B.
**Decision already made**: the framework goes. This document is the *how*, not the *whether*.

---

## What was decided and why

`docs/architecture/analytical_framework_for_RAG.md` — 10,691 chars of Alter/Kugel/Lowth
material (parallelism, terseness, paronomasia, merism, chiasmus, inclusio, refrain,
meter) — reaches the Master Writer as the `{analytical_framework}` block in its INPUTS.

Session 378 ran it as a two-arm A/B on Psalm 27, **twice**, on two different dossiers:

| | thin dossier (Jan-2026 artifacts) | full fresh pipeline |
|---|---|---|
| words, base → no-framework | 7,562 → 7,547 | 8,838 → 8,014 |
| verse coverage | 14/14 both | 14/14 both |
| **poetic-device vocabulary** | **18 → 16** | **5 → 5** |
| commentator citations | 29 → 30 | 23 → 21 |
| framework cost | 5,370 tok ≈ $0.027 | 4,601 tok ≈ $0.023 |

**No capability difference either time.** The decisive evidence is not the counts but the
convergence: on the full dossier both arms independently found the six hapax `־נִי`
verbs, the סתר reversal (hide *me* = salvation / hide *Your face* = ruin), Psalm 31 as
the control case proving the split deliberate, the twice-only `אֲבַקֵּשׁ` equating "the one
thing" with "the face", the Rabia al-Adawiyya echo, and the Proverbs `יָפִיחַ` perjury
formula. Removing a poetics primer removed none of them. Arm F's own reasoning capture,
written with **no** poetics reference in its prompt, used *parallel* ×6, *inclusio*,
*wordplay* ×2, *metaphor* ×3, *imagery* ×2, and its verse 1 turned on the `אוֹרִי`/`אִירָא`
near-anagram — the framework's own §III.1 Paronomasia, arrived at without it.

Cost is **not** the reason ($0.023/psalm). The reasons are prompt hygiene:

1. **No rule invokes it.** In the 75,777-char prompt the only other appearances of
   "framework" are a warning to keep *"over-explanation of the analytical framework"*
   inside the reasoning phase, and **framework** listed as a BLURRY WORD TO WATCH.
2. **It teaches the taxonomy the house stance rejects** — declares Alter's "seconding
   sequence" in its preamble, then lays out Lowth's three-fold scheme whose
   "synonymous = 2nd colon restates/echoes 1st" is the reading Alter and Kugel wrote
   against. If anything nudges the writer toward "the second line restates the first",
   this does, and RULE 8b would reject the result.
3. **It is an uncleaned Deep Research export** — 33 dangling `[Ref##]` markers and ~40
   trailing superscript digits pointing at a bibliography that was never included.
4. It has already been cut twice on **cost** grounds and never once on merit: S66 added
   it to the research bundle (27,678-char prose version), S256 rewrote it telegraphically
   (−61%), S257 deleted the bundle copy as a *"duplication bug"* — the writer had been
   reading the whole thing **twice**.

**Honest framing for the log:** the A/B shows removal costs nothing. It does not show
removal gains anything. Ship it for hygiene, not for measured improvement.

**The evidence is on disk**: `archive/psalm_27_S378_abrun2_full_pipeline/` holds both
arms' raw writer output, both prompt templates (diff them — 80 chars), the shared
synthesis-discovery block, arm F's thinking capture, and a README. Run 1 is at
`archive/psalm_27_S378_abrun1_writeronly/`. `output/` is gitignored, so these archives
are the only surviving record.

---

## THE WORK

### 1. The blocker — SI's splice anchor (DO THIS FIRST)

`### ANALYTICAL FRAMEWORK (poetic conventions reference)` is not only a heading, it is
the **splice anchor for the Session-347 cross-verse observations block**. Delete the
heading without moving the anchor and the writer silently loses the whole
synthesis-discovery sidecar — **~$1.50/psalm of analysis, on a code path that only logs
a warning**. Session 378 hit exactly this as an experimental confound and caught it only
because arm F was killed one minute into a paid run.

- `src/agents/master_editor.py` — **ALREADY FIXED** in S378. The anchor is now a
  fallback chain: `### ANALYTICAL FRAMEWORK …` then `### READER QUESTIONS (initial
  questions)`. Both land the block in the same position relative to every block that
  exists in both variants, and prompts still carrying the framework are byte-identical.
- `src/agents/master_editor_si.py:247` — **NOT FIXED.** It has its own copy of the
  splice with the old single anchor. Apply the identical fallback chain. **The SI
  pipeline will silently lose cross-verse observations if you skip this.**

### 2. The removal itself

`MASTER_WRITER_PROMPT_SI` is derived from `MASTER_WRITER_PROMPT_V4` by a `.replace()`
that inserts the SI section before `## YOUR INPUTS` (`master_editor_si.py:59`) and does
**not** touch the framework block — so **one template edit covers both pipelines**.

Delete these 80 chars from `master_editor.py` (~line 466):

```
### ANALYTICAL FRAMEWORK (poetic conventions reference)
{analytical_framework}

```

Then clean the now-dead plumbing:
- `master_editor.py` — the `rag_manager.load_analytical_framework()` call (~912) with its
  try/except, the `analytical_framework=` kwarg (~951), the `analytical_framework: str`
  parameter (~1029), the `.format()` kwarg (~1058).
- `master_editor_si.py` — the same four sites (167, 200, 214, 238).

`str.format()` ignores extra kwargs, so a half-done removal will not raise — which is
precisely why it must be finished rather than left half-done.

### 3. Do NOT delete the .md file

`RAGManager._verify_files()` raises `FileNotFoundError` when
`docs/architecture/analytical_framework_for_RAG.md` is missing, and `get_rag_context()`
calls `load_analytical_framework()` unconditionally. That path is live for
**macro_analyst, micro_analyst, and research_assembler** — all three construct a
RAGManager. Deleting the document breaks three agents that never use its contents.

Either leave the file on disk (cheapest, recommended) or, as a separate change, drop the
framework from `RAGContext` / `_verify_files` / `format_for_prompt` and delete
`macro_analyst`'s dead `include_full_framework` flag (default `False`; no runner passes
`True`).

### 4. Verify

- `MASTER_WRITER_PROMPT_V4` is **75,697** chars (75,777 − 80).
- Both splice anchors resolve; on a psalm **with** a synthesis-discovery file, build the
  prompt and confirm the CROSS-VERSE OBSERVATIONS block is present. This is the check
  that would have caught the S378 confound.
- `python scripts/ab_writer_prompts.py <N> --arms F_no_framework --dry-run` must now
  **raise** in pre-flight — `variant_f` calls `_cut` on a block that is gone, and `_cut`
  raises on a count of 0. That is the intended end state, exactly like `variant_b`/`d`/`e`
  after their arms shipped. Leave it in the registry as the audit trail.

### 5. The legacy bundles — the one that will bite later

**56 research bundles still carry the framework inline** as
`## Analytical Framework for Biblical Poetry` (the old **27,730-char prose** version):
psalms 1–34 plus the legacy test/rerun directories. A full pipeline re-run regenerates
the bundle without it (S257), but a **writer-only** re-run on an old bundle feeds the
framework straight back in through the dossier — 2.6× the size of the block being
removed. S378 hit this on Ps 27 and had to strip the section from the bundle for both
arms before the A/B measured anything at all.

Options: strip the section at load time in `_load_text_file`/`ResearchTrimmer`, or accept
it and require a full re-run for those psalms. Recommend the former; it is ~5 lines and
removes a trap that only fires on old psalms.

---

## Separate items found in Session 378 (not blockers)

- **The LXX budget is not biting.** `check_lxx_density.py 27` scores the delivered Ps 27
  at **64% — OVER by 4 verses** against RULE 8b's ≤40% ceiling, on the first fresh
  full-pipeline psalm measured since S375 set the budget. Worth an audit of whether the
  ceiling language ever changed behaviour.
- **The thinking capture collides across A/B arms.** `writer_thinking_path()` has no arm
  in the path, so each arm overwrites the previous one's reasoning
  (`output/psalm_N/psalm_0NN_master_writer_v4_thinking.txt`). Both S378 A/B runs lost the
  base arm's reasoning this way. Add the arm, or write it beside the arm's own output.
- **Prompt caching for A/Bs — worth building at N≥3 arms, NOT at 2.** The arms share a
  ~95% prefix (they diverge after the research bundle, so no reordering is needed —
  contrary to the shelved dossier-cache plan, which was about a shared *middle*). But a
  writer call runs ~10–12 min against a 5-minute default TTL, and the 1-hour TTL costs 2×
  on write: at two arms that is 2.0× + 0.1× versus 2.0× uncached, a **loss**. At five arms
  it is 2.0× + 4×0.1× = 2.4× versus 5.0×. Implementing means splitting the single user
  message in `_call_claude_writer` into content blocks with a `cache_control` breakpoint
  at the end of the shared prefix — a change to the path every production psalm uses.
  Session 377 reached the same conclusion from the other direction.
