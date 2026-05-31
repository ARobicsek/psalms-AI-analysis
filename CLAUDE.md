# Psalms AI Commentary Pipeline

**Session**: 349 (2026-05-30)
**Phase**: Pipeline Production — tweaks and improvements

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude (Opus 4.8, Opus 4.7, Opus 4.6, Sonnet 4.6), GPT (5.1, 5.4), and Gemini (2.5 Pro fallback) with multi-agent pipeline and Hebrew concordance integration.

## Recent Work (Last 5 Sessions)
**Session 349 (2026-05-30)**: Remove JSON Dependencies from Pipeline
- Removed `psalm_function_for_RAG.json` and `ugaritic.json` data loading from `RAGManager` as they are now superseded by deep research.
- Removed Ugaritic metrics from DOCX methodological summaries in `document_generator.py` and `combined_document_generator.py`.
- Cleaned up documentation references in `CONTEXT.md` and `DEVELOPER_GUIDE.md`.
**Session 348 (2026-05-29)**: Switch Default Master Writer to Opus 4.8
- Conducted reversible experiment on Psalm 57 to compare Opus 4.8 vs 4.7 with high effort configuration.
- Permanently updated `master_editor.py`, `synthesis_discovery.py`, and runner scripts to use `claude-opus-4-8` as default.
- Added Opus 4.8 pricing to `cost_tracker.py` and updated architecture documentation.

**Session 347 (2026-05-20)**: Synthesis-Discovery Sidecar — production wiring + Ps 55 validation
- Built `src/agents/synthesis_discovery.py` (Opus 4.7, mirrors writer's max-effort config) as a sidecar that feeds cross-verse OBSERVATIONS into the production one-call writer. Replaces the Session-346 two-call SPINE approach per `NEXT_SESSION_BRIEF.md`: the writer keeps full authorial discretion (no anchor verses, no "develop in full" mandate). Hardened the evidence-honesty filter to 9 named failure modes (a–i) plus a meta-rule that demands the model name two more failure modes it didn't already check. Extended `MasterEditor.write_commentary(synthesis_discovery_file=...)` and added `discover_cross_verse_observations()`. New `--synthesis-discovery` flag in `run_enhanced_pipeline.py` runs STEP 3.5 between micro and writer. Default path (flag off) leaves the writer prompt byte-identical to production.
- Validated on Ps 55 in `output/psalm_55/EXPERIMENT_synthesis_discovery/` (sidecar dir, shipped baseline untouched). Discovery produced 14 calibrated observations (1 governing + 9 core + 4 additional). The three insights the Session-346 brief identified as "must-recover" all landed in the final copy-edited prose: **ק-ר-ב dual-lexeme** as the intro's headline argument with all 6 occurrences traced; **Exod 13:22 לֹא־יָמִישׁ inversion** developed at vv. 11 and 12 (calibrated as "most famous biblical use," not "the only"); **שׁלם v.19↔v.21 contestation** at both verses. Copy editor: **23 changes** — better than two-call A's 32, in the same ballpark as C's 20. New failure modes the copy editor still caught (Ps 88:16 invented phrase, בלע/בלל false consonantal claim, חצה/פלג false cognate) were writer-side, not seeded by the spine — exactly the population the evidence-honesty filter is *not* designed to prevent.
- Total run cost: **$5.80** (Opus 4.7 discovery $1.83 + writer $3.16; gpt-5.4 copy editor $0.76; gpt-5.1 citation FP filter $0.05). Sidecar adds ~$2 per psalm vs the bare writer chain — basically the cost of the discovery call. Three artifacts now exist side-by-side in `output/psalm_55/EXPERIMENT_synthesis_discovery/psalm_055_commentary.docx` for comparison against THREE_WAY_COMPARISON guides A/B/C. Flag default remains OFF pending broader validation across 2–3 more psalms.

**Session 346 (2026-05-19)**: RULE 7b / Phrase-Coverage Proportionality + Two-Call Synthesis Experiment
- Added **RULE 7b (NO FALSE PROFUNDITY)** + **RULE 8 carve-out** + **STAGE 3 phrase-coverage proportionality option** to `MASTER_WRITER_PROMPT_V4` in `src/agents/master_editor.py`. Driven by two passages the user flagged in Ps 54: the מִסְתַּתֵּר reflexive paragraph and the נְדָבָה fortune-cookie chiasmus. Verified clean on a Ps 54 re-run. The Session-345 phrase-coverage rule was over-correcting — coverage now permits option (b): one honest proportionate sentence for a routine phrase. The fixes are live in production.
- Built and ran a **discardable two-call synthesis experiment** (`scripts/EXPERIMENT_two_call_synthesis.py` + `EXPERIMENT_two_call_finalize.py`) on Ps 54 and Ps 55. The two-call architecture (synthesis-discovery → write-with-spine) surfaced cross-verse insights the one-call misses (ק-ר-ב dual-lexeme reading; Exod 13:22 לֹא־יָמִישׁ inversion; שׁלם v.19↔v.21 contestation), but raised copy-editor correction load (32 vs 20 on scaled vs cap-3/4) and the evidence-honesty guardrail caught the specific failure modes I named, not the ones I didn't (חלל "stab through," counting errors, "prayer outcovers evil" non-sequiturs). Three blind external evaluations (Gemini ×2, Claude Opus 4.7) split 3-way — including one hallucinated "fatal" Hebrew error from Gemini that doesn't exist (BiDi rendering failure).
- **`docs/session_tracking/NEXT_SESSION_BRIEF.md`** has the Session-347 design proposal: rebuild the synthesis pass as a *discovery tool* feeding the production one-call writer (sidecar, behind a flag), not as a *structural spine*. Three DOCXs preserved in `output/psalm_55/THREE_WAY_COMPARISON/` (mapping sealed). All Session 346 prod rule changes verified stable.

**Session 345 (2026-05-13)**: Verse-Coverage + Anti-Jargon Rules in Master Writer Prompt
- Added "Phrase coverage (CRITICAL — read this twice)" bullet to STAGE 3 of `MASTER_WRITER_PROMPT_V4` in `src/agents/master_editor.py`, requiring every distinct phrase/clause in each verse to receive either a substantive analytical sentence or a brief inline deferral pointer to where it lands later. Driven by Psalm 53 v2 verse 2 fully developing the נָבָל / בְּלִבּוֹ / אֵין אֱלֹקִים first half while letting הִשְׁחִיתוּ / וְהִתְעִיבוּ / עָוֶל / אֵין עֹשֵׂה־טוֹב evaporate into a single grammatical aside. Matching FINAL VALIDATION CHECKLIST item added.
- Added RULE 3c (NO LINGUISTICS JARGON — NAME THE PHENOMENON, NOT THE TECHNICAL TERM FOR THE PHENOMENON). The Psalm 53 v2 verse 6 opening — "abrupt deixis ... deictic ruptures function as stage directions in prophetic poetry ... the judgment archetypal scope ... wherever the conditions of vv. 2-5 obtain ... the geography is moral, not Cartesian" — is now in the prompt verbatim as the BLOATED counter-example, with a "cinematic cut into a scene already in progress" rewrite as the CLEAN one. Explicit anti-list: Latinate verbs (obtain→hold, render→make, evince→show), abstract nominalizations (foregrounding of, deployment of), and bare linguistics terms (deixis, anaphora, paratactic, telic, isocolon).
- Added matching DINNER-PARTY REGISTER / READ-ALOUD TEST item to FINAL VALIDATION CHECKLIST: the test is not "is this defensible scholarship?" but "would I actually say this sentence to a friend over dinner?" Awaiting user verification on a re-run of Psalm 53 with the new prompt.



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

- **`docs/session_tracking/NEXT_SESSION_BRIEF.md` — Hit-the-ground-running plan for the upcoming session (check here first if present)**
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
