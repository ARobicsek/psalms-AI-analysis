# Psalms AI Commentary Pipeline

**Session**: 362 (2026-07-01)
**Phase**: Pipeline Production — tweaks and improvements

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude (Opus 4.8, Opus 4.7, Opus 4.6, Sonnet 4.6), GPT (5.1, 5.4), and Gemini (2.5 Pro fallback) with multi-agent pipeline and Hebrew concordance integration.

## Recent Work (Last 5 Sessions)
**Session 362 (2026-07-01)**: Sonnet 5 vs Sonnet 4.6 for the micro agent — investigated, live A/B on Ps 65, NOT adopted (all code reverted)
- **Question**: shift the micro analyst (only Sonnet user; 2 calls/psalm) from Sonnet 4.6 → Sonnet 5, "high or greater" thinking. **Pricing**: Sonnet 5 is $3/$15 standard but **$2/$10 intro through 2026-08-31**; new tokenizer nominally +30% tokens (but empirically **input was flat** on Ps 65's Hebrew-heavy prompt). **Migration breaks**: Stage 1's `budget_tokens` 400s on Sonnet 5 (must go adaptive+effort, no hard thinking cap); Stage 2's omitted `thinking` silently flips to adaptive-ON (must set `disabled`).
- **A/B (Ps 65, macro reused, Stages 1–2)**: `effort` is a coarse 3.3× lever — **`xhigh`** = 27.8K out, **−35%/−57%** cost, but **thinner** than 4.6 (34 vs 41 insights, half the note prose = the user's concern); **`max`** = 92.6K out, **+29%/+93%** cost, but **richer** (51 insights, 2× figurative, 15 questions). **Can't get cheaper AND richer at once** — 4.6 ($0.77) is the middle. **Quality (manual, vv.2/4/10)**: comparable; S5 sharper on cross-verse connective catches (תהלה/תפלה near-rhyme; גבר→גבורה echo v4→v7; peleg-Elohim superlative w/ Ps 80:11/36:7), 4.6 deeper per-item (more interpretive options, longer cross-ref chains, 510 vs 269 chars/insight). Better *scout*, weaker *essayist*.
- **Not adopted**: no clean win (cheap=thinner, rich=pricier-than-4.6). Full data + reproduction: `docs/plans/SONNET5_MICRO_AB_FINDINGS.md` (pointer in Reference Docs). All code restored from HEAD (`DEFAULT_MODEL` still `claude-sonnet-4-6`); throwaway runner removed.
**Session 361 (2026-06-28)**: Shimush Tehillim integration — systematic practical-Kabbalah coverage in liturgical section
- **Goal**: Shimush Tehillim (שימוש תהלים) content was occasionally surfaced by deep research and incorporated beautifully by the Master Writer, but never systematically. Made it a standard pipeline feature: deep research now explicitly targets it, Master Writer knows to create a `#### Practical Kabbalah` subsection (only when content exists), speculating on WHY the psalm was selected for that purpose.
- **Three edits, zero cost**: (1) `docs/prompts_reference/deep_research_prompt.md` +22 words naming Shimush Tehillim; (2) `src/agents/master_editor.py` Stage 2 +1 bullet (~55 words) with subsection guidance; (3) `data/deep_research/README.md` removed stale inline prompt copy, now points to canonical prompt file. No new agents, databases, or pipeline steps. Existing 55 deep research files left as-is — coverage appears incrementally on future runs.
**Session 360 (2026-06-23)**: Pipeline cost review → A1 (dossier prompt-cache) designed, blocker found, keepalive fix designed, SHELVED + documented
- **Review**: per-psalm cost ~$6 (Opus 4.8 ~$2.61 = Macro + Synthesis Discovery + Master Writer; GPT-5.4 ~$2.16; Sonnet ~$0.64; Gemini ~$0.41; GPT-5.1 ~$0.16). Produced a tiered menu (A1 dossier caching; A2 citation→Haiku; B1 no-op `ResearchTrimmer`/selective commentary; B2 copy-editor 5.4→5.1; C1 Synthesis Discovery skip/downsize). Key waste: Synthesis Discovery + Master Writer each re-ingest the SAME ~130–180k-token dossier with **zero prompt caching** (`cache_*_tokens: 0` everywhere); phonetic analyst is free (algorithmic); insights/questions already skipped by default.
- **A1 blocker + fix**: prefix caching is EV-negative naively — cache is written at Synthesis start, read when Writer starts, but Synthesis runs **303–466s > the 300s cache TTL**, so the cache expires first. Fix (user's idea): a **keepalive ping** (cheap `max_tokens=1` cache read) fired during Synthesis refreshes the TTL → reliable hit → **~$0.30–0.45/psalm** net.
- **SHELVED** over (a) the required Master-Writer prompt reorder (dossier must lead → risk to the tuned voice) and (b) model-swap fragility (caching only works if Synthesis+Writer share the SAME Anthropic model; a GPT writer kills it). Full plan: `docs/plans/DOSSIER_CACHE_KEEPALIVE_PLAN.md` (pointer added to Reference Docs). No code changed.
**Session 359 (2026-06-21)**: Master-editor voice — grammar-term glossing + gentle scholarly wit + texture variation; Amichai poem banned from literary echoes; live writer A/B on Pss 61–62
- **Goal**: published Pss 61/62 were excellent but (a) used grammar/rhetoric terms (vocative, asyndeton) above an average reader, (b) had no wit, (c) read uniformly section-to-section; also the overused Amichai poem *God Has Pity on Kindergarten Children* kept getting selected. Hard constraint: **do not grow the master-editor prompt** (long prompts → worse output).
- **`src/agents/master_editor.py`** (`MASTER_WRITER_PROMPT_V4`, net **+1.2 KB / +1.7%** after offsets): **RULE 3** → "DEFINE — AND ILLUSTRATE": gloss ordinary grammar/rhetoric terms (vocative, asyndeton, apposition, ellipsis, anaphora, litotes, hendiadys, zeugma) in plain words *in the same breath*, not just Hebrew/scholarly labels. **RULE 13 (wit)** reworked to the user's "gentle erudite irreverence" register — three transferable moves (punch inward at the scholar's own guild; one homely word over elaboration; must carry the argument); the over-copied Ps 52 "one does not easily worship in the mode of X" gold example **deleted**; the word **"joke" purged** from the whole prompt; frequency loosened ("a few genuine moments," still never forced). **STYLISTIC GUIDANCE** gains a "Vary your texture" paragraph (cadence + explanation-mode variation; verse sections still open with full Hebrew, only *what follows* varies). Offsets: deleted a redundant cross-cultural checklist line + compressed 3 restatement lines.
- **`src/agents/copy_editor.py`** (second line of defense for goal 1): new **category 10 (unexplained technical terms)** — an undefined grammar/rhetoric term (vocative, asyndeton, apposition, …) on first use is glossed inline in plain words (preferred) or replaced with the plain description. Guardrails: keep the surrounding insight, don't double-gloss (skip if already explained nearby), explicit exception to its standing "do not add material" rule, Hebrew stems stay under category 8. Backstops the residual the writer leaks (bare "vocative" in asides); bookkeeping updated 9→10 categories.
- **Literary echoes** (`docs/prompts_reference/literary echoes pass 1 & 2 - tier override.txt`): **work-level ban** on Amichai's *God Has Pity on Kindergarten Children* in the main ban statements + every checklist (Amichai stays an Earned-Canonical-Slot author for his *other* poems).
- **Live writer-only A/B** (reused upstream dossiers, `claude-opus-4-8`, ~$1.2–1.3/psalm, gitignored `output/psalm_6X/_writer_compare_new/` via archived `archive/development_scripts/compare_writer.py`): all three goals visibly fired (Ps 62 "vocative" now leads with "speaks *to* Him… direct address"; "hapax — it occurs nowhere else"; Ps 61 essay renders יוֹם יוֹם in pure plain English; real unforced wit — "Rank does not add a single gram," "a fact worth stating plainly rather than padding," "the lexicons throw up their hands"; added O'Jays + al-Sayyab echoes for register variety). **Honest residuals**: "vocative" still slips through unglossed in quick asides (nudge, not guarantee); length is run-to-run noise (Ps 62 −10%, Ps 61 +13%); **the Amichai ban cannot show in a writer-only rerun** — the poem is already baked into `research_v2.md`, so it persists until literary echoes are regenerated (`run_literary_echoes.py 61`).
**Session 358 (2026-06-10)**: Pipeline-wide novelty review → 3-round A/B → adopted: plumbing R2-R6 + sidecar v2.1 + baseline writer; discovered LLM-judge position bias
- **Diagnosis** (`docs/plans/PIPELINE_NOVELTY_REVIEW_FINDINGS.md`): 9 ranked cost-neutral recommendations. **Adopted to main after 3 A/B rounds on Pss 58/59/60** (`docs/plans/NOVELTY_AB_TEST_RUNBOOK.md`): R2 copy-editor flagged-conjecture protection + hedge-hardening check; R3 purpose-aware concordance pinning (`†`); R4 liturgical "flag the non-obvious placement"; R5 macro devices/working-notes pass-through; R6 macro questions steer micro Stage-2; **sidecar v2.1** (flat UNRANKED output — no GOVERNING/CORE tiers, writer selects; additive distributional sweep w/ conspicuous-absence tabulation). **R1 (writer GOLD-INVENTORY mandate) tested 2 rounds and REVERTED** — the writer kept anchoring on the sidecar's governing pick; baseline writer prompt restored byte-identical.
- **Methodological finding (important for all future A/Bs)**: the blind judge picked the SECOND-presented commentary in **12 of 12** judgments (~+1–2 best-5 pts) — single-order LLM-judge verdicts are position noise. `evaluate_novelty_ab.py --order both` (now default) judges both orders + emits a position-debiased synthesis. Debiased round 3: **new +1.0 (Ps 58), tie (59), new +0.4 (60)** — parity-to-ahead, gains on the bridging/reaching-outward axis (e.g. withheld-"I" NOV-5 insight from the absence sweep). Judge noise on identical text ≈ ±1.0 best-5; read sign-consistency, not margins.
- **Tools kept**: `run_novelty_ab.py` (isolated-arm pipeline reruns; `--reuse-upstream` ~$3.7/psalm writer-only, `--regen-synthesis` ~$5.7) + `evaluate_novelty_ab.py` (debiased blind judge, ~$2/psalm both-orders). A/B artifacts remain tracked on branch `claude/sweet-fermat-pje3t7` only (main excludes `output/`). Per-psalm cost unchanged.
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
- `docs/plans/DOSSIER_CACHE_KEEPALIVE_PLAN.md` — SHELVED cost-reduction plan (A1): prompt-cache the shared dossier across Synthesis Discovery → Master Writer via a keepalive ping (~$0.30–0.45/psalm); shelved over writer-reorder + model-swap fragility
- `docs/plans/SONNET5_MICRO_AB_FINDINGS.md` — SHELVED model swap: micro agent Sonnet 4.6 → Sonnet 5. Live A/B on Ps 65; `effort=xhigh` cheaper-but-thinner, `effort=max` richer-but-pricier-than-4.6; no clean win. Not adopted; all code reverted. Read before re-investigating a Sonnet 5 micro swap

## File Organization Rules

- **Production code:** `src/`, `main.py`, `scripts/`
- **Experimental/test:** Use during session, archive immediately after
- **Archive after 1 session:** Test scripts, debug outputs, temp files → `archive/`
- **Never commit:** `*.log`, `*_output.txt`, temp analysis files (in .gitignore)

## End-of-Session Checklist

1. **Update this file (CLAUDE.md)**: Increment session number (line 3), replace oldest of 5 recent entries
2. **Update IMPLEMENTATION_LOG.md**: Add detailed session entry at top
3. **Update scriptReferences.md**: If scripts were created or significantly changed
