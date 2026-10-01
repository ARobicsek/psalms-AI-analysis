# Next session (393) — start here

Session 392 ran the Ps 76 reception/Targum A/B ($9.78), checked every rabbinic citation in both guides ($0), proved
the SD → writer cache, fixed the "0 verses" methods page, and rebuilt Rabbi Sacks from Sefaria. Details:
`IMPLEMENTATION_LOG.md`, Session 392; the A/B record: `archive/S392_reception_ab/` (README + claim check).

## 1. The author's read of the Ps 76 A/B (not yet asked)

Both guides: `output/_s391_reception_ab/psalm_76/Psalm 76 - A - today's pipeline.docx|pdf` and
`… - B - with reception and Targum.docx|pdf`. The $0 claim check says B is right where A repeated two known errors
(A: 11/2/1 of 14; B: 20/1/0 of 21). N = 1 per arm, so style differences are mostly noise (S372).

Then the decision S391 left open: **make `--reception` / `--targum` the defaults?** Knobs: `PER_VERSE_CHARS` (1,400),
`SECTION_MAX_CHARS` (40K), tier C scope (Hasidut, Musar, halakhah). B cost +$0.45 in synthesis discovery and −$0.24
at the writer on this run.

## 2. The rebuilt Sacks section has not met a writer

`python scripts/build_sacks_index.py 92 --show` prints what the writer would get. The pipeline needs no change
(the research assembler calls the same two methods), but a `--skip-micro` run keeps a reused bundle's OLD Sacks
section. Natural test: a full run of a psalm with prayer-book commentary (Ps 92, 27, 130, 145; Ps 76/77 have none).
Watch: does the writer use the prayer-book commentary, and does it ever render a Hebrew-translation passage
(labelled) as an English quotation of Sacks? The cache (`data/sacks/`, gitignored) is built for all 150 on the
author's machine; elsewhere it builds on first use (~10–20 s a psalm).

## 3. Small, $0

- **Ps 77's methods page** still says "Rabbi Jonathan Sacks References Reviewed: 4" (S391 §4.5): set
  `research.sacks_references_count` to 0 in `output/psalm_77/psalm_077_pipeline_stats.json`, then
  `python scripts/run_docx_only.py 77 --pdf`.
- `output/debug/master_writer_v4_forest_prompt_psalm_76.txt` is arm B's prompt (the A/B driver had no production
  original to restore); harmless, delete if it confuses.
- The A/B driver's `README.md` lives under `output/` (gitignored); its copy is in the archive.

## 4. Still open from earlier prompts

`NEXT_SESSION_PROMPT_session_391.md` §1 (the author's read of the Ps 77 echoes-v3 guide) and §4 (content-filter
watch, archiving the S389 experimental scripts, the post-copy-edit citation re-check, the fact-check trims).
