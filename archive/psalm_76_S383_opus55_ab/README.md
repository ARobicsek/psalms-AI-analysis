# Psalm 76 — Opus 5.5 A/B (Session 383, 2026-09-24)

**A** = production run of 2026-09-17: macro `claude-opus-4-8`, synthesis discovery `claude-opus-4-8`, writer `claude-opus-5`, all effort `high`.
**B** = every Opus stage on `claude-opus-5-5`, effort `high` (explicit — its API default is `medium`).

B re-ran only what depends on the Opus stages: macro → micro + research bundle (micro consumes the macro) → synthesis discovery → writer → print-ready → copy editor → DOCX. Literary echoes were **reused** from A (they have no upstream dependency, and the step overwrites the canonical `data/literary_echoes/` file). Driver: `run_opus55_B.py`. It patches `debug_paths.psalm_output_dir` because the thinking capture ignores `--output-dir` and would have overwritten A's. The five `output/debug/*_psalm_76.txt` single slots were backed up and restored afterwards, and a hash manifest of 7,178 files confirmed nothing else outside `output/psalm_76/_opus55_B/` changed.

Deliverable: `Documents/Psalm study guide/Psalm 76 (B - Opus 5.5).docx`.

## Confounds
- Because the macro changed, B has its **own research bundle**: 280,610 vs 270,614 chars, 828 vs 529 concordance entries. That is inherent to swapping the macro.
- A Sefaria 503 dropped **one** commentary entry from B (Romemot El 76:3): 92 vs 93. A's v. 3 note never cited it.
- N = 1 psalm and one reader. See `docs/plans/SESSION_372_TRANSLATION_SLOT_AND_JUDGE_VARIANCE.md` on judge variance.

## Cost (Opus 5.5 = $4 / $20, cache read $0.20 = 0.05x; verified on the pricing page 2026-09-24)
| Stage | A tokens in/out | A $ | B tokens in/out | B $ |
|---|---|---|---|---|
| Macro | 4,926 / 4,261 (4.8) | 0.13 | 4,928 / 10,459 | 0.23 |
| Synthesis discovery | 164,932 / 24,508 (4.8) | 1.44 | 178,827 / 46,330 | 1.64 |
| Writer | 187,958 / 34,770 (5) | 1.81 | 208,573 / 54,930 | 1.93 |
| **Opus subtotal** | 357,816 / 63,539 | **3.38** | 392,328 / 111,719 | **3.80** |

Opus 5.5 is 20% cheaper per token but emitted **+76% output tokens**. At Opus 5 rates, B's volume would have cost $4.76. Downstream re-runs moved by noise: micro +$0.13 (larger macro → more requests), liturgical −$0.04, copy editor −$0.03. Full run: B $5.78 without literary echoes, which is about **$6.9 production-equivalent against A's $6.42, roughly +$0.5/psalm (+7–8%)**. A's figurative-curator cost was not logged separately, so the literary-echoes share is estimated.

## Where the quality difference comes from
Nearly every distinctive B finding appears first in **B's synthesis-discovery file**, not in the writer's output: Hosea 2:20, the Song-at-the-Sea reversal, Isa 37:33, Josh 14:15, Pss 9–10, Deut 4:36, the Zech 14 haftarah, Song 4:8, the absent "we", and Gen 49:24. The stage that moved most is the one pinned to 4.8 "for cost". The obvious next arm is **SD-only on 5.5**, with A's macro and bundle kept fixed.

## Pipeline defects surfaced (not model defects)
- `CopyEditor._reassemble` splits intro/verses at the first `^\*\*Verses?\s+\d+`. B's writer labelled its liturgical key verses `**Verse 2.** …`, so the Key-verses and Practical-Kabbalah blocks were filed under verse commentary in `copy_edited.md`. `_extract_sections_from_copy_edited`'s RECOVERY moved them back, so **the DOCX is correct**. Real verse headers sit alone on their line, so anchoring the pattern with `\*\*\s*$` would fix it.
- The copy editor (gpt-5.4, the same model in both arms) introduced four defects into B: it turned a correct claim ("the only other occurrence of the form רִשְׁפֵי is Song 8:6") into a false one ("the only other plural use", but Ps 78:48 has לָרְשָׁפִים); it mangled two quotation marks; and it added one redundant sentence (v. 5).

## Print edition (follow-up, same session)
The DOCX in Documents is now a compact print layout with the writer's summarized thinking appended as a two-column appendix. It was rebuilt at $0 by `build_compact_B.py`, a `DocumentGenerator` subclass, and nothing in `src/` changed. Guide: 25 → 15 pages; with the appendix, 25 pages total. The pipeline's original rendering is still at `output/psalm_76/_opus55_B/psalm_076_commentary.docx`.
