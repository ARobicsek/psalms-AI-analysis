# Session 388 — editor cost work on Ps 77 (records)

Everything here was run on the finished Ps 77 guide from Session 387. `output/` is gitignored, so the run
records that matter are copied here. Spend: **≈ $6.54** (copy-edit test $0.45, synthesis discovery with the
failed cache $5.78, cache whitespace probe $0.31, one sub-cent OpenAI usage probe).

## 1. Copy editor, "edits" mode vs "full" mode (same inputs as the S387 production copy edit)

`EXPERIMENT_s388_copy_edit_modes.py 77 --mode edits` — gpt-5.4, the same `print_ready.md`, the same
fact-check prompt (verified byte-identical to the one saved at run time) and the one citation issue the paid
filter kept (Ps 57:9).

| | full (S387 production) | edits (S388) |
|---|---|---|
| cost | $0.556 | **$0.449** |
| seconds | 542 | **337** |
| visible output tokens | 21,371 | 5,261 |
| reasoning tokens | 9,728 | **18,690** |
| contradicted sentences changed | 26 / 28 | 26 / 28 (the same two left: C2, C175) |
| edits applied | — | 35 / 35 verbatim (0 loose, 0 not found) |

Output fell by three quarters but reasoning doubled (N=1; may be variance), so the saving was 19%, not the
~45% predicted. Edits mode also made 4 changes full mode did not: two ungrounded superlatives (9h), a real
error ("the last word of the first half" for וְהַאֲזִין, which is in the second half of v. 2), and ONE WRONG
"fix": it removed the dagesh in רָאוּךָ מַּיִם (77:17), which the Masoretic text has. That led to
`copy_editor.pointing_regression`, a $0 guard only edits mode makes possible: an edit that changes ONLY Hebrew
pointing is refused if the original word pair is in tanakh.db and the replacement's is not. Re-applied to this
run's saved response (`copy_edit_edits_raw_response.txt`), it refuses exactly that edit. The author made edits
mode the default.

## 2. Synthesis discovery, dossier-first layout with the dossier cache shared with the writer

`EXPERIMENT_s388_shared_cache.py 77`. Result: **the cache never hit** ($5.78 instead of ≈ $2.5).

- SD wrote 214,085 tokens; the keep-alive at +200 s WROTE 214,084 (not read); the end-of-run keep-alive wrote
  again; the writer probe (max_tokens=0 on the writer's real first turn) wrote 240,192 and read 0.
- Cause, found from the one-token difference and confirmed with `cache_whitespace_probe.py` ($0.31): **the API
  trims trailing whitespace from the last block of a message.** The shared head ended in a blank line; sent
  alone (the keep-alive) it was one token shorter than when a block followed it (SD, the writer). Probe:

  | request | write | read |
  |---|---|---|
  | A1 head+`\n\n`, then a tail | 20,174 | 0 |
  | A2 the same head alone | 20,173 | 0 ← miss |
  | A3 the same head + a DIFFERENT tail | 0 | 20,174 ← SD → writer works |
  | B1 head without trailing whitespace, then `\n\n`+tail | 20,174 | 0 |
  | B2 that head alone | 0 | 20,174 ← keep-alive works |

- Fixed: `forest_writer.split_inputs` rstrips the head (the whitespace opens the tail); after one keep-alive
  miss no further keep-alive runs (the end-of-run one had ignored the miss). **Not yet re-run end to end** —
  the next pipeline run is the test (see `docs/plans/NEXT_SESSION_PROMPT_session_389.md`).
- Quality of the dossier-first prompt (one run, descriptive): 31 complete observations, finished normally
  (65,276 output tokens; S387's run was cut at 14 complete by the old 64K cap). It re-found S387's main
  connections (Habakkuk, Lam 2:7, Ne'ilah after the Thirteen Attributes, אֶזְכְּרָה ×4 with Ps 42, Num 33:1,
  Tikkun HaKlali) and added new ones (no enemy anywhere; no praise verb or vow; אֱלֹהִים absent vv. 5–13;
  Lamentations 3's network in order; Gen 25:26 and 48; Exod 3:15; Neh 9:17–19; Ps 142; Zech 10).
  `sd_dossier_first_observations.md`.
