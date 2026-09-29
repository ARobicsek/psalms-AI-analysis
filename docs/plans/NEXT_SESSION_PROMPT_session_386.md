# Next session (386), LOCAL in VS Code: run the two-call forest writer, then test the fact check

## Where Session 385 left things
- **The author's blind reading of the S384 essay trials is recorded** in
  `archive/psalm_76_S384_essay_trials/AUTHOR_READING_S385.md`: F and C best (both forest essays by Opus 5.5), D top of
  the middle group; every Sol essay in the middle or below; the production essays in the middle (K) or weakest (B).
  F mis-explains Rashi on 76:11.
- **Two things are built, and neither has run.** Cloud sessions never saw the API keys (the environment-variable
  setup did not reach new sessions), so the author moved to running locally.
  1. **The two-call forest writer**, `scripts/s385_two_call_writer.py`. Design:
     `docs/plans/S385_two_call_writer_and_fact_check.md`.
  2. **The fact-check step and copy-editor change**, built by a child cloud session. It lives in
     `src/agents/fact_checker.py` and `scripts/run_fact_checker.py`, with the copy editor taking the report through
     `supplementary_prompt` and `--fact-check` in `run_enhanced_pipeline.py` (default OFF). Handoff, commands and PASS
     criteria: **`docs/plans/S385_FACT_CHECK_RESULTS.md`**.
- **All of this is on branch `claude/exciting-mendel-77ecwv`, not on main.**

## Do this first (locally)
1. `git fetch origin`, `git checkout claude/exciting-mendel-77ecwv`, `git pull`.
2. Keys: the project's `.env` supplies `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`. Both runners load it themselves. The
   cloud-only `PSALMS_ANTHROPIC_API_KEY` name is not needed locally; the writer falls back to `ANTHROPIC_API_KEY`.
3. `python scripts/s385_two_call_writer.py --dry-run`, then `python scripts/s385_two_call_writer.py` (≈ $3.1; cap
   $8; about 10–15 min).
   - Confirm that each `verses_*` call in `archive/psalm_76_S385_two_call/ledger.json` shows `cache_read` ≈ 185K and
     `cache_write` ≈ 0.
   - Read the structure check each variant prints.
4. Copy the two DOCXs from `archive/psalm_76_S385_two_call/{new,F}/` into `Documents/Psalm study guide/` for the
   author. Neither is copy edited. Report the metrics against K descriptively, with no scores unless asked.
5. Then follow `docs/plans/S385_FACT_CHECK_RESULTS.md`: Probe A, then the main test on
   `archive/psalm_76_S385_two_call/F/`, with and without the report, plus the optional gpt-6-sol arm.
   - The headline probe is F's Rashi on 76:11 (must be caught).
   - Byron, Herodotus 2.141 and Sennacherib's prism must survive.
6. Commit the outputs under `archive/` and record the session (CLAUDE.md, IMPLEMENTATION_LOG, scriptReferences).

## Then, the author chooses
- Adopt the fact check (flip `--fact-check` on by default) and/or move the copy editor to GPT-6 Sol. That move is
  roughly cost-neutral at ±$0.2/psalm, but first run the Terra probe cases in `COPY_EDITOR_TERRA_FINDINGS.md`, whose
  saved Ps 70 input is in the local `output/`.
- Take the two-call writer into `MasterEditor` for a fresh psalm, if the Ps 76 read is good.
- The S384 queue still stands: regenerate the Ps 76 bundle on the fixed concordance and radar (~$2–3), and literary
  echoes v3 (now with evidence: no top-three essay used a dossier echo).

## Gotchas
- **Effort must be identical in both writer calls** (it is part of the cached prefix), and so must the first user
  turn, byte for byte, `cache_control` included.
- Opus 5.5 thinking blocks are replayed unchanged. Never edit or strip earlier turns, or the preserved-thinking check
  400s on new accounts.
- The writer's DOCX builder stubs `TanakhDatabase` with the psalm text from the inputs block, so it works with or
  without `tanakh.db`.
- In a Claude Code CLOUD session, do not store the Anthropic key as `ANTHROPIC_API_KEY`: Claude Code itself reads that
  name.
