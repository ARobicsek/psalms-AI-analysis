# Next session (389) — start here

## 1. On the next psalm run, CHECK THAT THE SHARED DOSSIER CACHE WORKS (the author asked)

Session 388 made synthesis discovery (SD) and the forest writer share one prompt cache for the ~214K-token
dossier head (psalm text, macro, micro, research bundle, phonetics). Expected saving ≈ $0.7/psalm on Opus 5.5.
It was built, broke once in a paid test (trailing-whitespace trimming; see
`archive/psalm_77_S388_cost/README.md`), was fixed, and **has not yet run end to end**.

Run the psalm normally (`python scripts/run_enhanced_pipeline.py N --fact-check`), then read the log:

| Log line | Working | Broken |
|---|---|---|
| `[SYNTHESIS DISCOVERY] dossier head … cache shared with the writer: yes` | present | `no` → check the model/`--writer-prompt` condition in `run_enhanced_pipeline.py` |
| `[SYNTHESIS-DISCOVERY psalm N] done in …s - in=… cache read=0 cache write=~214,000` | write ≈ dossier size | — |
| `dossier cache keep-alive: read ~214,000, wrote 0` (every 200 s, and maybe once at the end) | **read** | `wrote ~214,000` + `keep-alive stopped (no cache hit)` → prefix mismatch |
| `[forest] dossier head (… chars) matches what synthesis discovery cached` | present | `DIFFERS` → the SD and writer heads diverged (compare builders) |
| `[forest] essay: …; in … + cache read ~214,000 + cache write ~16,000` | **read ≈ 214K** | read 0, write ≈ 230K → the entry expired or the key differs |

Also in `psalm_NNN_cost.json`: the `synthesis discovery` stage should show `cache_write_tokens` ≈ 214K and a
little `cache_read_tokens` (the keep-alives); the writer stage `cache_read_tokens` ≈ 2 × 214K plus the essay
block, `cache_write_tokens` ≈ 16–20K. If the keep-alive READ works but the writer misses, suspect timing: the
writer must start within 5 minutes of the last keep-alive (the end-of-run keep-alive fires if the last read is
> 120 s old). Things that are part of the cache key and must match: model, `thinking` (both use
`model_effort.adaptive_thinking`), effort, no system prompt, no tools, the head text byte for byte.

## 2. Also new in S388, to watch on that run

- **Copy editor now defaults to "edits" mode** (FIND/REPLACE, applied in Python). Check the log line
  `Edits mode: N change(s), M edit(s): … applied, … not found, … ambiguous, … refused`; anything NOT APPLIED is
  marked in `psalm_NNN_copy_edit_changes.md`. Ps 77 test: $0.45 vs $0.56, 337 s vs 542 s, same fact-check uptake.
  `--copy-edit-mode full` restores the old behaviour.
- **Fact checker's free lookups** (`search_liturgy`, `get_lxx`, helpful `get_text` failures, "no entry" for
  skipped commentary verses, the psalm's text in every chunk) have **not been measured in a paid run**. Look in
  the editors' report for fewer ERROR lookups and for liturgical claims settled from `liturgy.db`.
- **Pricing**: gpt-6-sol is $2/$10 standard (the S384 "$4/$20 durable" was a mix-up with GPT-5.6 Sol);
  GPT-5.6+ bills cache writes at 1.25× (now tracked). The report's "at durable rates" section should not appear.

## 3. Open items carried forward

- **Bolls.life's Greek LXX is lemmatized** (dictionary forms). `sefaria_client.fetch_lxx_psalm` feeds it to the
  pipeline as "the LXX", so the writer may be reading lemmas as the Greek text. Worth checking what the writer's
  psalm-text block shows and whether an inflected source exists.
- The S387 watch list still stands: curated figurative insights and SD observation 15+ were missing from the
  Ps 77 guide; Sefaria timed out on Ibn Ezra 77:9; methods page "Concordance Searches: N/A" after `--skip-micro`;
  literary echoes $1.41.
- Remaining fact-check trims measured but not built (≈ $0.18/psalm): scope each chunk's commentator evidence to
  the commentators it names (+ a who-commented-where index), and a one-line format for supported records.
