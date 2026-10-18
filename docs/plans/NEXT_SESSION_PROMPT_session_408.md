# Next session (408) — start here

Session 407 (record: `IMPLEMENTATION_LOG.md` Session 407; `archive/psalm_29_S407_argon/README.md`) ran Ps 29 on
Gemini 4 Argon with the author's new deep research ($4.51; 20 of 219 claims contradicted, 20/20 revised), made
Argon's calls stream so the writer's-reasoning appendix gets every thought summary (`src/utils/gemini_stream.py`),
and, at the author's request, made **Gemini 4 Argon the default writer** (forest calls + post-fact-check revision).
Synthesis discovery, macro and the SI pipeline stay on Opus 5.5.

## 1. Synthesis discovery on Argon: the author asked for this test

The author: "am I right that IF we switch the synthesis step to argon also we could realize savings?" Yes, mostly
until the intro price ends; then: "let's do that in our next session."

**The estimate** (per ~17-verse psalm; SD has no writer cache-share now that the writer is Argon):

| | SD cost | Saving |
|---|---|---|
| Opus 5.5 now (Ps 29: 251K in, 40K out at $4/$20) | ~$1.8–2.0 | — |
| Argon through 2026-11-30 ($2/$10; Gemini counts ~30% fewer input tokens) | ~$0.75–0.90 | ~$1.0–1.2 |
| Argon from 2026-12-01 ($4/$20, the same as Opus 5.5) | ~$1.5–1.8 | ~$0.3 |

A possible extra ~$0.34 (later $0.68): Gemini's implicit cache, IF SD's prompt opens with the same bytes as the
writer's first turn and the cache outlives SD's ~7 minutes. Unverified; measure it (the essay call's
`cache read` in the log) rather than assume it.

**Build**: a Gemini path in `src/agents/synthesis_discovery.py` through `gemini_stream.stream_generate` (as the
writer and revision do); keep `DEFAULT_MODEL` Opus 5.5 and select Argon with `--synthesis-discovery-model
gemini-4-argon` (add it to the pipeline's choices if it has any); bill like `_forest_gemini` (cached input out of
`prompt_token_count`, thinking as output); the Claude-only keep-alive and `share_cache_with_writer` must stay off
for Gemini. **The cap is the trap**: Argon's output limit is 65,536 tokens INCLUDING thinking, and Opus SD has used
up to 66,585 (Ps 82) and hit a 64K cap once (Ps 77); raise a MAX_TOKENS stop, never retry it, and watch the long
psalms (78, 89, 104–107, 119).

**Test**: Ps 29, whose S407 bundle and Opus SD are in `archive/psalm_29_S407_argon/psalm_29/`
(`psalm_029_research_v2.md`, `psalm_029_synthesis_discovery.md` = the Opus 5.5 run on the new deep research). Run
Argon SD into a NEW folder (copy the inputs; never overwrite the S407 files), ~$0.8. Compare the two observation
lists for the author (count, which are new, which are wrong). If they look as good, a writer-onward run on the Argon
SD (~$3) shows whether the guide changes. The author decides by reading; S383 traced Ps 76's originality lift to
this stage, and Argon makes more factual slips, which SD would hand straight to the writer.

## 2. Offered, not built

- **`--skip-micro` never refreshes a bundle's deep research.** Echoes and liturgy have in-place swaps
  (`replace_literary_echoes_section`, `refresh_bundle_liturgy`); deep research has none, so a new
  `psalm_NNN_deep_research.txt` is silently ignored by a skip-micro re-run. S407 spliced it by hand. A
  `replace_deep_research_section` beside the echoes one would close it.
- **The deep-research cleaner's $0.10 cap fails on a long check** (Ps 29: 24K-char check, "pass 1 edit list was cut
  off; nothing written"; $0.11 at a $0.30 cap). Inside the pipeline that failure leaves the bundle on the UNCHECKED
  report without stopping. A `--max-cost` flag on `clean_deep_research.py`, or a higher cap, would fix it.

## 3. Watch on the next Argon run (now every run)

- **The appendix**: the first guide with streamed thought summaries. Check it reads as reasoning (several headed
  summaries per call), not draft prose, and that its note names Gemini 4 Argon.
- **The essay edit turn**: keep it as it is (memory `essay-edit-turn-keep`: the author liked the Ps 29 edit; the
  word counter's ~7% high bias is part of that calibration, left alone on purpose).
- **The 65,536 cap** on the verse call for long psalms (Ps 81 used 32.7K; Ps 82 20.9K).
- **Price**: re-check the `gemini-4-argon` row after 2026-11-30 (`INTRO_PRICING`).
- Argon's notes run long-sentenced (26–33% of sentences 40+ words vs Opus 4%); the author has seen it and chose
  Argon anyway, so mention it only if it gets worse.

## 4. Carried

The 407 handoff (`NEXT_SESSION_PROMPT_session_407.md`): §1–2 are settled (the author chose Argon); §3 the
shared-dossier errors (offer to trace them upstream, do not build unasked); §4 the watch items (the block-quote
guard keeps firing on Argon's revision; the Rashi lead-in citation false alarm); §5 the 406 handoff and its
carried items (the batch re-render offer for the S405 DOCX changes). Production `output/psalm_N/` guides written
before 2026-10-17 are Opus; `output/psalm_29/` is still the S401 Opus guide (the Argon one is in the archive).
