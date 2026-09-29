# Next session (388): the author's read of Ps 77, and what the S387 run left open

## Where things stand (end of Session 387, 2026-09-29)
- **Production is now** Opus 5.5 (effort `high`) for macro, synthesis discovery and the writer, and the writer is the
  **two-call forest writer** (`src/agents/forest_writer.py`, `MasterEditor._call_forest_writer`; `--writer-prompt v4`
  restores the one-call prompt). `--fact-check` is still opt-in; pass it.
- **Ps 77** is finished: `Documents/Psalm study guide/Psalm 77.docx` / `.pdf` (compact layout, writer's-reasoning
  appendix) and `Psalm 77 - What the editors did.docx` / `.pdf` (fact check, copy edit, $0 checks, per-stage cost).
  Measured cost **$9.66**, plus ≈ $2 of a crashed first fact check that was never recorded.
- The DOCX layout is compact by default and a PDF is written beside it (Word via PowerShell COM).

## Start by asking the author
1. Their read of the Ps 77 guide (the first full guide from the forest writer on Opus 5.5) and of the editors' report:
   is the report the right shape and length (60 pp; most of it is the supported-claims table and the lookup
   appendix)? Anything to cut, or to move to a companion file?
2. **Whether to re-run synthesis discovery + the writer for Ps 77** (≈ $4.4, then fact check + copy edit ≈ $2.1).
   This guide was written WITHOUT the figurative curator's curated insights (phase 2 timed out) and with synthesis
   discovery cut off inside observation 15 (64K cap). Both are fixed now. Re-running also replaces the essay.
3. Whether to make `--fact-check` the default.

## Open items (not yet done)
- **Timeouts elsewhere**: `liturgical_librarian`, `question_curator` and macro's GPT path still build `OpenAI()` with
  the 600 s default. Same fix as the curator/copy editor if any of them runs long.
- **Methods page after a `--skip-micro` resume** shows "Concordance Searches: N/A" (`_parse_research_stats_from_markdown`
  does not recover the count from the bundle).
- **Literary echoes cost $1.41 on Ps 77** (high vs earlier psalms); one entry kept unverified after an incomplete
  verifier response. Worth a look at pass costs in `output/psalm_77/literary_echoes/`.
- **The prompt-A/B scripts** (`ab_writer_prompts.py`, `ab_seed_base_from_pipeline.py`) vary the V4 prompt, which
  production no longer uses. Forest-writer A/Bs need arms built on `forest_writer.py`.
- **Copy edit with vs without the report** is still unmeasured (run 1's no-report arm timed out). The editors' report
  renders the comparison automatically if `output/psalm_NNN/_copy_edit_without_report/` holds a no-report copy edit.
- GPT-6 Sol's durable price is still an assumption ($4/$20 after 2026-11-21); re-check OpenAI's page before then.

## Gotchas learned in S387
- A non-streamed high-effort OpenAI call sends nothing until done: under the SDK's 600 s read timeout a call that
  needs 11 minutes fails every time, and each retry starts from scratch. Use `OpenAI(timeout=1800, …)`.
- Opus 5.5 writes ~75% more than 4.8: any Opus call with `max_tokens` < 128K can be cut off. Check `stop_reason`.
- A stage that raises must still bill what it spent (`FactChecker._bill_tracker` is the pattern); per-call fees go
  in `CostTracker.add_charge`; a resumed run continues the cost file (`load_dict`).
- Fact-check stage 1 writes only six words of a supported claim's sentence; `expand_sentence` restores full sentences
  for non-supported records. Match gathered web items to records by CLAIM, not sentence.
- Heredoc edits in Git Bash mangled `\n` / `\\` in Python source twice; write edit scripts to a file instead.
