# Psalm 27 — analytical-framework A/B, run 2 (full pipeline), Session 378

The experimental record behind Session 378's conclusion that the writer prompt's
`{analytical_framework}` block earns nothing. Preserved here because `output/` is
gitignored in its entirety, so nothing in this A/B would otherwise survive in the repo.

**Question**: does removing `docs/architecture/analytical_framework_for_RAG.md` from the
Master Writer's INPUTS degrade the guide?

**Design**: one variable. Both arms read the same dossier, produced by a single
`python scripts/run_enhanced_pipeline.py 27` on 2026-08-14 ($6.6231, including literary
echoes $1.1517 and synthesis discovery $1.5037). Model fixed at `claude-opus-5`.

| arm | prompt | writer cost | input tok | words |
|---|---|---|---|---|
| `base` | production, 75,777 chars | $1.9454 | 225,691 | 8,838 |
| `F_no_framework` | −80 chars (block deleted) | $1.9594 | 221,090 | 8,014 |

The framework itself is the 4,601-token difference — **≈ $0.023/psalm**.

`base` was **not** paid for twice: the pipeline's own writer pass IS the base arm
(verified identical inputs — `insights_file=None` both, `reader_questions_file=None`
both, same synthesis-discovery file, same template), recovered with
`scripts/ab_seed_base_from_pipeline.py`.

## Result

No capability difference. Device vocabulary 5 → 5; verse coverage 14/14 both;
commentator citations 23 → 21. The real evidence is convergence: both arms
independently found the six hapax `־נִי` verbs, the סתר reversal (hide *me* = salvation /
hide *Your face* = ruin), Psalm 31 as the control case proving the split deliberate, the
twice-only `אֲבַקֵּשׁ` equating "the one thing" with "the face", the Rabia al-Adawiyya echo,
and the Proverbs `יָפִיחַ` perjury formula.

**Stated honestly: this shows removal COSTS nothing. It does not show removal GAINS
anything.** The case for cutting is prompt hygiene — see
`docs/plans/NEXT_SESSION_PROMPT_session_378.md`.

## Files

- `<arm>/_prompt_template.txt` — the exact template that arm ran (diff them: 80 chars)
- `<arm>/psalm_027_edited_{intro,verses}_pre_copy_edit.md` — **raw writer output**, the
  actual comparison; everything downstream is shared machinery
- `<arm>/psalm_027_copy_edited.md` — after the gpt-5.4 copy editor
- `<arm>/psalm_027_copy_edit_changes.md` — the copy editor's own change list, an
  independent quality signal (base 6 changes, F 13; the category-10 flags are trivial
  glosses like "Masoretes", not poetics)
- `psalm_027_synthesis_discovery.md` — the 17,318-char cross-verse block **both** arms
  received. It nearly went missing from arm F: the block is spliced at the
  `### ANALYTICAL FRAMEWORK` header, which arm F deletes, and a missing anchor only
  logged a warning. `master_editor.py` now uses a fallback chain
- `psalm_027_master_writer_v4_thinking_F_no_framework.txt` — **arm F's reasoning**, the
  single most direct piece of evidence: written with no poetics reference in the prompt,
  it uses *parallel* ×6, *inclusio*, *wordplay* ×2, *metaphor* ×3. Read it as a
  model-generated **summary**, not a raw chain of thought
- `ab_summary.{md,json}` — the harness's own tally

**Arm `base` has no thinking capture.** `writer_thinking_path()` carries no arm in its
path, so arm F overwrote it. Fixing that is an open item in the next-session plan.

## Related

- `archive/psalm_27_PRE_S378/` — the Jan-2026 originals this psalm started from
- `archive/psalm_27_S378_abrun1_writeronly/` — run 1, the same A/B on the old thin
  dossier (words 7,562 → 7,547, device vocabulary 18 → 16). Its bundle still carried the
  legacy 27,730-char inline framework copy, which had to be stripped from **both** arms
  or the A/B would have measured nothing
- Finished guides: `Documents/Psalm study guide/Psalm 27 (Baseline).docx` and
  `Psalm 27 (no analytical framework).docx`
