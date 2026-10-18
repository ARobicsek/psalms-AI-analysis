# Next session (409) — start here

Session 408 (record: `IMPLEMENTATION_LOG.md` Session 408; `archive/S408_sd_argon_ab/README.md`) tested synthesis
discovery on Gemini 4 Argon, at the author's request, to win back the SD → writer cache saving lost when the writer
moved to Argon. **Rejected**: Argon's observation lists were 30–35% contradicted on the fact checker (Opus 5.5:
6–7%), marked nothing CONJECTURE, and Ps 78 overran the 65,536-token cap (Ps 82 used 91%). The trial code was
removed at the author's request; the tree is as at S407. Synthesis discovery, macro and the SI pipeline stay on
Opus 5.5; the writer and its revision stay on Argon. Nothing is pending from S408.

## 1. Offered, not built (carried from the 408 prompt §2)

- **`--skip-micro` never refreshes a bundle's deep research.** Echoes and liturgy have in-place swaps
  (`replace_literary_echoes_section`, `refresh_bundle_liturgy`); deep research has none, so a new
  `psalm_NNN_deep_research.txt` is silently ignored by a skip-micro re-run. S407 spliced it by hand. A
  `replace_deep_research_section` beside the echoes one would close it.
- **The deep-research cleaner's $0.10 cap fails on a long check** (Ps 29: 24K-char check, "pass 1 edit list was cut
  off; nothing written"; $0.11 at a $0.30 cap). Inside the pipeline that failure leaves the bundle on the UNCHECKED
  report without stopping. A `--max-cost` flag on `clean_deep_research.py`, or a higher cap, would fix it.

## 2. Watch on the next Argon run (now every run; carried from the 408 prompt §3)

- **The appendix**: the first production guide with streamed thought summaries. Check it reads as reasoning (several
  headed summaries per call), not draft prose, and that its note names Gemini 4 Argon.
- **The essay edit turn**: keep it as it is (memory `essay-edit-turn-keep`).
- **The 65,536 cap** on the verse call for long psalms (Ps 81 used 32.7K; Ps 82 20.9K). S408 showed Argon thinking
  up to ~48K on synthesis work, so a long psalm's verse call is the place to look first.
- **Price**: re-check the `gemini-4-argon` row after 2026-11-30 (`INTRO_PRICING`).
- Argon's notes run long-sentenced (26–33% of sentences 40+ words vs Opus 4%); the author has seen it and chose
  Argon anyway, so mention it only if it gets worse.
- **Calibration**: S408 found Argon labelling interpretive syntheses ESTABLISHED; as the writer, watch whether
  guide conjectures arrive as conjectures (the fact check's "absolutes" finds are the signal).

## 3. Carried

The 407 handoff (`NEXT_SESSION_PROMPT_session_407.md`): §3 the shared-dossier errors (offer to trace them upstream,
do not build unasked); §4 the watch items (the block-quote guard keeps firing on Argon's revision; the Rashi
lead-in citation false alarm); §5 the 406 handoff and its carried items (the batch re-render offer for the S405
DOCX changes). Production `output/psalm_N/` guides written before 2026-10-17 are Opus; `output/psalm_29/` is still
the S401 Opus guide (the Argon one is in `archive/psalm_29_S407_argon/`).
