# Psalms AI Commentary Pipeline

**Session**: 358 (2026-06-10)
**Phase**: Pipeline Production — tweaks and improvements

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude (Opus 4.8, Opus 4.7, Opus 4.6, Sonnet 4.6), GPT (5.1, 5.4), and Gemini (2.5 Pro fallback) with multi-agent pipeline and Hebrew concordance integration.

## Recent Work (Last 5 Sessions)
**Session 358 (2026-06-10)**: Pipeline-wide novelty review → 3-round A/B → adopted: plumbing R2-R6 + sidecar v2.1 + baseline writer; discovered LLM-judge position bias
- **Diagnosis** (`docs/plans/PIPELINE_NOVELTY_REVIEW_FINDINGS.md`): 9 ranked cost-neutral recommendations. **Adopted to main after 3 A/B rounds on Pss 58/59/60** (`docs/plans/NOVELTY_AB_TEST_RUNBOOK.md`): R2 copy-editor flagged-conjecture protection + hedge-hardening check; R3 purpose-aware concordance pinning (`†`); R4 liturgical "flag the non-obvious placement"; R5 macro devices/working-notes pass-through; R6 macro questions steer micro Stage-2; **sidecar v2.1** (flat UNRANKED output — no GOVERNING/CORE tiers, writer selects; additive distributional sweep w/ conspicuous-absence tabulation). **R1 (writer GOLD-INVENTORY mandate) tested 2 rounds and REVERTED** — the writer kept anchoring on the sidecar's governing pick; baseline writer prompt restored byte-identical.
- **Methodological finding (important for all future A/Bs)**: the blind judge picked the SECOND-presented commentary in **12 of 12** judgments (~+1–2 best-5 pts) — single-order LLM-judge verdicts are position noise. `evaluate_novelty_ab.py --order both` (now default) judges both orders + emits a position-debiased synthesis. Debiased round 3: **new +1.0 (Ps 58), tie (59), new +0.4 (60)** — parity-to-ahead, gains on the bridging/reaching-outward axis (e.g. withheld-"I" NOV-5 insight from the absence sweep). Judge noise on identical text ≈ ±1.0 best-5; read sign-consistency, not margins.
- **Tools kept**: `run_novelty_ab.py` (isolated-arm pipeline reruns; `--reuse-upstream` ~$3.7/psalm writer-only, `--regen-synthesis` ~$5.7) + `evaluate_novelty_ab.py` (debiased blind judge, ~$2/psalm both-orders). A/B artifacts remain tracked on branch `claude/sweet-fermat-pje3t7` only (main excludes `output/`). Per-psalm cost unchanged.
**Session 357 (2026-06-10)**: Synthesis-discovery agent → v2 "Synthesis Scholar" (abductive cross-source synthesis), validated by A/B
- **Diagnosis**: user asked whether the synthesizer would produce deep "aha" insights (e.g., Ps 67: priestly-blessing third line omitted ≈ נשׂיאת פנים/favoritism vs. universalism; Omer recitation overdetermined by 49 words + harvest). Audit showed the v1 prompt was pattern-only (text-internal, cross-verse), its novelty filter cut candidates whose *constituent facts* were famous (killing known-facts-newly-linked insights), and filter (g) banned the hedged interpretive leap outright. Empirically (published DOCX), reaching-outward insights came from Liturgical Librarian / Literary Echoes / Deep Research + Master Writer — Ps 67 ran with the sidecar OFF and still had both example insights (the SI supplied #1).
- **v2 prompt** (`src/agents/synthesis_discovery.py`; design doc `docs/plans/SYNTHESIS_SCHOLAR_PROMPT_V2_DRAFT.md`): TYPE P (patterns, kept) + TYPE C (cross-source connections); surprise inventory → per-source substrate → collision pass (incl. sound-as-motive sweep over phonetics, per user); novelty tested on the **linkage**; conjecture licensed if flagged CONJECTURE + explanatory; aha/boredom audit; output adds Type/Confidence/Anchors/Payoff (extraction markers unchanged). Writer splice (`master_editor.py`) now orders CONJECTURE items rendered as conjecture. Post-A/B addition: reconstruct-and-diff reworked source formulas so **omissions** surface (the one canary v2 missed). Honesty filter (a)-(j) kept intact.
- **A/B (user-run locally, ~$12)**: `scripts/run_synthesis_ab.py` (byte-identical Step-3.5 inputs via MasterEditorSI loaders; SI never reaches the synthesizer by construction — verified; contamination scan incl.) + `scripts/synthesis_ab_prompts.py` (as-tested v2, preserved) + `scripts/judge_synthesis_ab.py` (blind judge, unused this session). Pss 67/60/49: v2 kept v1-grade patterns AND added real TYPE C finds (Ps 49 Korah↔beit-avel, Shekalim↔כפר נפש; Ps 60 seal-verse↔Qere vote, Shushan-Purim overdetermined; Ps 67 Birkat-Kohanim reinsertion; caught dossier's "7× Elohim" error — it's 6). Omer canary: engaged but contrarian (argues autumn harvest ≠ spring Omer season, per macro's Sukkot Sitz). Calibration held — conjectures all flagged. **Adopted to production.**
**Session 356 (2026-06-09)**: DOCX BiDi — verse header in `[qere]׃` rendered in wrong typeface
- User report (Ps 60): the verse-7 Hebrew header above its commentary rendered in **Aptos 13** while every other verse header was **Times New Roman 13**. Root cause in `src/utils/document_generator.py`: v7 ends in a **ketiv/qere** — `…יְמִינְךָ (ועננו) [וַעֲנֵנִי]׃`. The closing `]` ends the matched Hebrew run *before* the sof-pasuq, so the `'׃' in hebrew` guard in `_split_long_hebrew_block` (which only checked `match.group(1)`) missed it. The line was misclassified as a "long bare Hebrew block" → routed to `_add_hebrew_block_paragraph`, which both **forced Aptos** (via the `is_verse_header` branch) **and** right-aligned + indented it 0.3″ like a block quote. Every other verse (ending in a bare `…ם׃`) keeps the ׃ inside the match → correctly routed to the native-RTL `_add_primarily_hebrew_line` (TNR). Affects any psalm whose verse closes with a bracketed qere before the sof-pasuq (common in Psalms).
- **Fix (two parts)**: (1) **Guard** — `_split_long_hebrew_block` now also checks a 5-char trailing window for ׃, so `[qere]׃` verses are recognized as complete verses and route through the **same** header path as everything else (fixes font *and* alignment/indent together). (2) **Font safety net** — the two `is_verse_header`/"whole-line" block branches that hardcoded `'Aptos'` (in `_add_paragraph_with_soft_breaks` + `_add_paragraph_with_markdown`) now use `self.HEBREW_FONT` (Times New Roman), so no standalone Hebrew block can ever come out Aptos.
- **Verified** (no LLM cost): unit-traced the exact v7 line — `_split_long_hebrew_block` now returns `None`, v7 renders byte-identical to v6 (cs=Times New Roman, default alignment, no indent). Regenerated `output/psalm_60/psalm_060_commentary.docx` via `scripts/run_docx_only.py 60` → **0 Aptos-fonted Hebrew runs** (was 1: the v7 header). The only remaining right-aligned/indented Hebrew block is a legitimate long-quote of v7 in the intro's "Key verses and phrases" (intended block rendering, now TNR). No scripts created/changed. (Earlier in-session detour chased the same symptom on Ps 67, whose v7 ends in a bare ׃ and was already uniform — the Ps 67 SI DOCX was harmlessly regenerated, no change.)
**Session 355 (2026-06-08)**: Post-migration path fix — figurative-language DB
- Pipeline crashed in **Step 2 (Micro Analysis)** constructing `FigurativeLibrarian`: the hardcoded OneDrive path `C:/Users/ariro/OneDrive/Documents/Bible/database/Biblical_fig_language.db` was dead after the OneDrive→C-drive repo migration. That DB lives in the **separate `bible` repo**, which was also migrated to `C:\dev\personal\bible` (now a sibling of `psalms`).
- Fix (`src/agents/figurative_librarian.py:35`): replaced the hardcoded absolute path with a **repo-relative default** — `Path(__file__).resolve().parents[2].parent / "bible" / "database" / "Biblical_fig_language.db"` — plus a `FIGURATIVE_DB_PATH` **env-var override**. Resolves to the live migrated copy (152 MB, byte-identical to the OneDrive `_Archive\Migrated repos (originals)` backup), *not* the OneDrive archive. Verified: path resolves + exists; `FigurativeLibrarian` and the full `MicroAnalystV2`→`ResearchAssembler`→`FigurativeLibrarian` chain construct cleanly.
- Swept `src/` + `scripts/` for other dead paths: **this was the only OneDrive/`C:/Users` reference in production code** (all others live in `archive/`, `scratch/`, which the pipeline never touches). Standing dependency: psalms needs the sibling `bible` repo; if the two are ever moved apart, set `FIGURATIVE_DB_PATH`. Env note: in **git bash**, activate the venv with `source venv/Scripts/activate` (the bare `C:\…\activate` path fails — bash eats the backslashes); **PowerShell** auto-resolves the venv. No scripts created/changed.
**Session 354 (2026-06-04)**: DOCX BiDi — verse-table Hebrew 13pt + final size/format tweaks
- Bumped verse-table Hebrew (top-of-DOCX psalm text table) from 12pt → **13pt** (`_format_psalm_text`, both `font.size` and `szCs`). All Hebrew now uniformly 13pt across the document.
- No new scripts. Production Ps 67 DOCX regenerated; committed and pushed to `main`.
## Quick Commands

```bash
python scripts/run_enhanced_pipeline.py 23                             # Process single psalm (synthesis-discovery sidecar ON by default, ~+$2)
python scripts/run_enhanced_pipeline.py 23 --resume                     # Resume from last step
python scripts/run_enhanced_pipeline.py 23 --skip-synthesis-discovery   # Disable the Session-347 cross-verse synthesis sidecar
python scripts/run_si_pipeline.py 19                 # Special Instruction pipeline (synthesis-discovery sidecar ON by default)
python scripts/run_literary_echoes.py 53             # Standalone 4-pass literary echoes (default: regenerate)
python scripts/run_copy_editor.py 36 37 38           # Standalone copy editor
python scripts/run_scripture_verifier.py 41          # Standalone citation verifier
python scripts/converse_with_editor.py 21            # Chat with Master Editor
```

## Key Directories

- `src/agents/` — AI agent implementations (macro, micro, synthesis, editors, copy editor)
- `src/concordance/` — 4-layer Hebrew search system
- `database/` — SQLite databases (tanakh.db, psalm_relationships.db)
- `data/deep_research/` — Gemini Deep Research outputs
- `data/special_instructions/` — Author directive files for SI pipeline
- `output/psalm_*/` — Generated commentary (production)
- `scripts/` — Pipeline runners and utilities

## Reference Docs (read only when needed)

- `docs/session_tracking/scriptReferences.md` — All scripts with descriptions
- `docs/session_tracking/PROJECT_STATUS.md` — Pipeline phases, active features, databases
- `docs/session_tracking/IMPLEMENTATION_LOG.md` — Detailed session history (300+)
- `docs/session_tracking/FEATURE_ARCHIVE.md` — Detailed docs for completed features
- `docs/architecture/TECHNICAL_ARCHITECTURE_SUMMARY.md` — Full system architecture
- `docs/architecture/TOKEN_REDUCTION_PHASE_B.md` — Ready-to-implement token reduction tasks

## File Organization Rules

- **Production code:** `src/`, `main.py`, `scripts/`
- **Experimental/test:** Use during session, archive immediately after
- **Archive after 1 session:** Test scripts, debug outputs, temp files → `archive/`
- **Never commit:** `*.log`, `*_output.txt`, temp analysis files (in .gitignore)

## End-of-Session Checklist

1. **Update this file (CLAUDE.md)**: Increment session number (line 3), replace oldest of 5 recent entries
2. **Update IMPLEMENTATION_LOG.md**: Add detailed session entry at top
3. **Update scriptReferences.md**: If scripts were created or significantly changed
