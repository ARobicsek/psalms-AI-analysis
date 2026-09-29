# Next session (387): the whole updated pipeline on Psalm 77, with editor telemetry and full cost tracking

## What the author asked for (2026-09-29)
> "in the next session I'd like to try our whole updated pipeline on psalm 77 with detailed telemetry of what the
> editor(s) did presented to me so I can read it, plus detailed cost tracking."

Three deliverables:
1. **A finished Ps 77 guide** from the updated pipeline (DOCX in `Documents/Psalm study guide/`).
2. **A readable editors' report**: everything the fact checker and the copy editor did, for the author to read.
3. **A detailed cost report**: every stage, every model, every token class, **including web-search fees**.

## State after Session 386
- **Writer**: the author is satisfied with the two-call "forest" approach (S385; read on Ps 76). **It is NOT in the
  production pipeline.** It exists only as `scripts/s385_two_call_writer.py`, hard-wired to Ps 76: it reads the S384
  inputs block (`archive/psalm_76_S384_essay_trials/prompts/inputs_block.txt`) and essay F. Production STEP 4 is still
  `MasterEditor` (one call, `--master-editor-model claude-opus-5`, the 77K prompt).
- **Reader questions are retired**: the S385 verse instructions asked for them by mistake; removed in S386. Do not bring
  them back.
- **Fact checker** (S386, `docs/plans/S386_FACT_CHECK_COST.md`): v5 is the default, **≈ $1.83 on Ps 76**, accepted by the
  author at ~$1.80. `run_enhanced_pipeline.py --fact-check` runs it (STEP 5a¾) and, with it, the post-copy-edit citation
  re-check (STEP 5b½). **Still default OFF**, so pass the flag.
- **Copy editor**: gpt-5.4, takes the fact-check report as supplementary context. Its system prompt is unchanged.
- **Untested on Ps 76**: the fact check on essay F (the Rashi 76:11 probe) and the copy edit with vs without the report.
  Ps 77 is now the first real test of both.
- **Also untested on any full guide**: S384's concordance fixes, the intertext radar and the echo budget.

## Do this first
1. `git pull`. Confirm `python -m pytest -q` passes (223 at the end of S386).
2. **Decide with the author, before spending**:
   - which models run macro and synthesis discovery. They are still Opus 4.8; S383 traced the originality lift to SD on
     Opus 5.5. Is Ps 77 the moment to move SD to 5.5 (≈ +$0.5)?
   - the writer: port the two-call forest writer into production (recommended), or run the pipeline to the research
     bundle and then drive a Ps-77 generalisation of the S385 script.
3. **Port the two-call writer** (if chosen). Keep it one shared code path, never a hand-copied duplicate (the S379
   splice lesson):
   - build the inputs block from production's research bundle;
   - call 1 = P1 essay (`P1_INSTRUCTIONS` in `scripts/s384_essay_trials.py`), call 2 = `VERSE_INSTRUCTIONS`
     (`scripts/s385_two_call_writer.py`), 5-minute cache on the first turn, keep-alive past 240 s;
   - replay call 1's thinking blocks unchanged into call 2 (the "new" variant);
   - Opus 5.5 at effort **`high`**, set explicitly. Never `max`: S384 burned 128K tokens thinking and wrote nothing;
   - output in the shape `_parse_writer_response` and the copy editor expect (the liturgical marker, `### VERSE
     COMMENTARY`, `**Verse N**` headers alone on their lines);
   - thinking capture to `output/psalm_77/psalm_077_master_writer_v4_thinking.txt` through `debug_paths`.
4. `python scripts/run_enhanced_pipeline.py 77 --fact-check` (+ the writer choice). Estimate: ~$8–10 for the pipeline, of
   which ~$1.8 is the fact check and ~$0.65 the copy editor; measure, don't trust this.

## The editors' report (build it; the author reads it)
One document per psalm, e.g. `Documents/Psalm study guide/Psalm 77 - What the editors did.docx`, from files the pipeline
already writes:
- `psalm_077_fact_check.json` / `.md`: every claim checked, grouped by verdict. For each CONTRADICTED item: the sentence, the
  finding, the quoted evidence with its source/URL, the suggested fix, and **whether the copy editor applied it** (match
  the `[FACT-CHECK]` entries in the change log). Also the claims sent to the web, what the gatherer found, and which
  passages were verified on their pages (`meta.stages`, the gathered sources).
- the copy editor's change log and diff (`psalm_077_copy_edit_changes.md`, `…_diff.md`): every change with category and
  before → after, **untagged factual edits called out separately** (the Terra failure shape), and its `### UNVERIFIED`
  notes.
- `psalm_077_post_copy_edit_citations.md`: any citation the copy editor broke.
- the citation verifier's pre-copy-edit report, and what the copy editor did with it.
Keep it descriptive (the author judges). Put the counts on one summary page first: claims checked, contradicted,
applied, not applied, untagged factual edits, UNVERIFIED notes, citations broken.

## The cost report
- The pipeline writes `output/psalm_77/psalm_077_cost.json` and `_pipeline_stats.json`. Check they carry every stage
  and model, including the fact checker's three models (sol local, luna gather, sol judge) as separate lines.
- **Web-search fees are NOT in CostTracker** (tokens only). The fact checker reports them in `FactCheckResult.search_cost_usd`
  and `meta.stages.per_stage`. Add them to the cost report as their own line, and ideally to CostTracker as a non-token
  charge.
- Report per stage: model, input / cached / output / thinking tokens, $ and share of the total. Flag where a promo price
  was used (`INTRO_PRICING`: gpt-6-sol through 2026-11-21, gemini-3.8-flash through 2026-12-31) and what the durable
  price would be.

## Gotchas
- **GPT-6 Sol's price after 2026-11-21 is uncertain** (see S386 doc). Re-check OpenAI's page before quoting durable costs.
- The fact checker needs `OPENAI_API_KEY`; pypdf is installed in the venv for the page check.
- `--output-dir` does not isolate the thinking captures or `output/debug/` (S383). Ps 77 is a fresh psalm, so this only
  matters if you run a second arm.
- The fact check reads `print_ready.md` and the research bundle (`research_trimmed.md` / `research_v2.md`); the
  commentators' entries must keep the `### 77:N — Name` headers for per-chunk evidence to work.
