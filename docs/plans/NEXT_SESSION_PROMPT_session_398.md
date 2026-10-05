# Next session (398) — start here

Session 397 made the fact check cheaper without losing catches: OpenAI **Flex** (same gpt-6-sol, half price) plus
compacted lookups. On Ps 79's own guide: **$2.76 → $1.22**, recall level (every disagreement read). Record:
`IMPLEMENTATION_LOG.md` Session 397, the S397 section of `docs/plans/S386_FACT_CHECK_COST.md`,
`archive/psalm_79_S397_fact_check_cost/README.md`. Nothing else in the pipeline changed.

## 1. On the next full pipeline run, check the fact check

- **Cost**: the fact-check stage in `psalm_NNN_cost.json` / the editors' report should show `gpt-6-sol@flex` (and
  `gpt-6-luna@flex`). A plain `gpt-6-sol` row means some calls fell back to the standard tier: search the log for
  "flex unavailable twice". Expect about half of the pre-S397 cost for the psalm's length (Ps 79, 13 verses: $1.22;
  Ps 78, 72 verses, was $4.49 standard → roughly $1.8–2.2 now).
- **Time**: flex can be slower. On Ps 79 it was not (stage-1 chunks 79–168 s). If a run's fact check takes much
  longer than ~10 minutes, look at the per-run `seconds` in `_fact_check_telemetry.json`.
- **Catches**: the number contradicted should stay in the usual range (Ps 79: 25–29). Liturgy claims in particular:
  the checker now sees unpointed liturgy passages, `every_ref` grouped by book, and reprints merged under `also_in`.
- The budget question for long psalms (memory: ~$1.80/psalm accepted, long psalms undecided) is now much less
  pressing. Ask the author whether they want the savings, or two merged passes (~$2.4 on Ps 79) for more recall.

## 2. Not done (recorded, not urgent)

- Compacting the supported records in the stage-1 output (≈ $0.08 a psalm at flex prices; a schema change).
- The per-verse liturgy catalogue (`liturgy_catalogue`, $0) as a fact-check lookup: it could replace many
  `search_liturgy` calls and answer sequence claims directly, but it changes what the checker sees: A/B first.
- Other OpenAI stages could take Flex the same way (macro's GPT path, the copy editor on gpt-5.4, the cleaner is
  Anthropic). Each needs an `@flex` price row and a check that its model is on OpenAI's flex list.

## 3. Carried

The whole 397 handoff (`NEXT_SESSION_PROMPT_session_397.md`), less its fact-check cost item (done): the author's
read of the Ps 79 guide; the liturgy-precision, `every_ref` and editors'-report watch items (S397 note: the
telemetry's trace stores only a SUMMARY of each lookup, so `every_ref` cannot appear there; to confirm the checker
reads it, look at the thinking file or the explanations of liturgical "only" claims); the used-works register
(left alone by the author); the deep-research cleaner's guards; remote sessions take Gemini output as Google Docs;
and the 396/395 handoffs carried inside it.
