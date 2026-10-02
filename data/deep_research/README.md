# Deep Web Research Files

Gemini research for individual psalms, and (Session 393) its independent check and the cleaned result.

## Files per psalm (`NNN` = zero-padded psalm number)

| File | Who writes it | What it is |
|---|---|---|
| `psalm_NNN_deep_research.txt` | the author (Gemini chat 1) | the research report |
| `psalm_NNN_deep_research_check.txt` | the author (Gemini chat 2, a fresh chat) | CONFIRMED / WRONG / NOT CONFIRMED per claim, with corrections; optional `## ADDENDUM` that corrects the check itself |
| `psalm_NNN_deep_research_clean.txt` | the pipeline (`deep_research_cleaner`) | the report with the check applied: `[corrected by check]`, `[unconfirmed]` |
| `psalm_NNN_deep_research_clean_log.md` | the pipeline | every edit, applied or not, the model and the cost |

## How to create

The two prompts are in `docs/prompts_reference/deep_research_prompt.md`. Run the research prompt in one Gemini
chat, then the checker prompt on its output in a NEW chat, and save both files here.

## Integration

The research assembler (`_load_deep_research`):
- cleans the report when a check file is newer than the clean file (Sonnet 5.5, ≤ $0.10, billed to the run;
  `python scripts/clean_deep_research.py N` does the same ahead of a run, `--dry-run` at $0);
- uses the clean file when it is current, else the raw report (old label, as before);
- demotes the file's `#`/`##` headings so they stay inside the bundle's `## Deep Web Research` section;
- never overwrites a clean file edited by hand after it was written.

The methods page says "Deep Web Research: Yes (corrected against an independent check)" for a cleaned file.
A `--skip-micro` run reuses its old research bundle, so a new check only reaches the writer on a full run.

Why all this: `docs/plans/S393_DEEP_RESEARCH.md`.
