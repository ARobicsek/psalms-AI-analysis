# Session 408: synthesis discovery on Gemini 4 Argon vs Opus 5.5

Question (the author): with Argon as the writer, can synthesis discovery move to Argon too, (a) logistically,
(b) at Opus's quality, and (c) inside Argon's 65,536-token output cap (thinking included)?

Code (built for the trial, then REMOVED at the author's request; nothing of it is in the tree): a Gemini path in
`SynthesisDiscoveryAgent` (a `_gemini_call` twin of `MasterEditor._forest_gemini`: `gemini_stream.stream_generate`,
`ThinkingConfig(thinking_level="high", include_thoughts=True)`, `max_output_tokens=65536`, cached input split out
of `prompt_token_count`, thinking billed as output, a MAX_TOKENS stop raised and never retried; the dossier head
sent as its own first Part so Gemini's implicit cache could carry it to the writer; no cache_control or keep-alive).
Note for a rebuild: the pipeline sets `share_cache_with_writer` whenever SD and writer models are equal, so a Gemini
SD must ignore it. A one-off runner (also removed) ran SD on each frozen dossier via
`MasterEditor.discover_cross_verse_observations(..., model="gemini-4-argon", share_cache_with_writer=False)`.

Layout: `psalm_N/opus/` = the production Opus 5.5 list on that dossier; `psalm_N/run1/` = Argon (list, full
response, streamed thinking, run log, cost). Fact checks: `scripts/run_fact_checker.py N --input-file <list>
--bundle <the dossier's research_trimmed.md> --output-dir .../factcheck` (flex tier).

## Stage 0 ($0): the answer alone, in Gemini tokens

Opus observation lists, `count_tokens` on gemini-4-argon: Pss 77-82 8.4K-11.8K tokens. Opus's total output
on the same psalms was 35K-67K, so the rest is thinking; Argon has ~53K for thinking if it answers at Opus's length.

## Stage 1: the cap

| Psalm (verses) | Argon thinking | Argon answer | % of cap | finish | Argon $ | Opus $ (same dossier) |
|---|---|---|---|---|---|---|
| 29 (11) | 29,960 | 14,350 | 68% | STOP | 0.79 | 1.81 |
| 82 (8)  | 46,302 | 13,276 | 91% | STOP | 0.91 | 2.60 |
| 78 (72) | 47,888 | 17,648+ | 100% | **MAX_TOKENS** | 1.22 (nothing usable) | 1.00 (retry run) |

Argon's answers run 1.3-1.8x Opus's length in tokens; an 8-verse psalm used 91% of the cap.

## Stage 2: quality

| | Ps 29 Opus | Ps 29 Argon | Ps 82 Opus | Ps 82 Argon |
|---|---|---|---|---|
| observations | 20 | 13 | 27 | 11 |
| labelled ESTABLISHED / PROBABLE / CONJECTURE | 2 / 12 / 6 | 9 / 4 / 0 | 3 / 18 / 6 | 7 / 4 / 0 |
| claims checked | 113 | 104 | 160 | 68 |
| **contradicted** | **8 (7%)** | **31 (30%)** | **9 (6%)** | **24 (35%)** |

- Opus's errors are precision slips (a wish read as narration; "ends with" = last verb; Meiri "dates" when he
  compares). Argon's include invented specifics: Greek verb forms absent from LXX Exod 32:20 / Deut 9:21 (the
  whole Golden-Calf observation rests on them), a five-item list of masculine forest plurals that are mostly
  singulars or a place name, "Zevachim explicitly cites Gen 9:15" (it does not), "four tractates" (three),
  Ibn Ezra's alternative reading presented as his only one, the Masoretic Deut 32:8 quoted with the Qumran
  variant's divine sons.
- Argon labels interpretive syntheses ESTABLISHED and never CONJECTURE; the writer is told to render
  CONJECTURE as conjecture, so this calibration loss would reach the guide.
- Argon's list is fewer, longer, single arguments; a few are good material (Ps 82: v. 5 as the council's
  silence, the death-then-inheritance chain of vv. 6-8, b. RH 31a's "in His wisdom" via Prov 8:29). Opus's is
  broader (Ps 82: Ps 94 diptych, Zeph 3, Ps 79's superscription, Isa 24, Lam 3) and flags "minor texture".
- Argon text glitches: "endlich" (German) and a Hebrew letter inside a Greek word in the Ps 29 list.

## Verdict

Not adopted; synthesis discovery stays on Opus 5.5. Argon's synthesis pass makes ~5x Opus's errors per claim,
hides its conjectures, and overruns the cap on long psalms. Stage 3 (a writer-onward guide on the Argon SD) was
not run: the stage-2 result made it moot. The SD -> writer implicit-cache saving (~$0.34, later ~$0.68/psalm)
therefore stays unclaimed. Cost: SD $2.92 + fact checks $3.10 (Ps 78's Opus check was wasted once Argon failed)
= $6.02.

If a later Gemini is tried here: measure the cap on Ps 78 first (cheapest decisive test), and fact-check the list
before reading it; Opus's lists run 6-7% contradicted on this checker.
