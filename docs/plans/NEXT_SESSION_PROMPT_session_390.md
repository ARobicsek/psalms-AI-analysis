# Next session (390) — start here

**Two sessions ran in parallel on 2026-09-29/30.** Session 388 (editor cost work: Sol's price, OpenAI cache
writes, edits-mode copy editor, free lookups, SD↔writer shared dossier cache) committed first; its handoff,
`NEXT_SESSION_PROMPT_session_389.md`, is **still entirely open** — read it too. Session 389 (this one) rebuilt the
literary-echoes stage ("echoes v3"). Because it began before S388 committed, its code comments say "Session 388"
/ "S388" and its design record is `docs/plans/S388_ECHOES_V3.md`. Treat those labels as Session 389.

## 1. The author's read of the new Ps 77 guide

`Documents/Psalm study guide/Psalm 77.pdf` (22 pp, the v3 echoes, S389) vs `Psalm 77 (S387).pdf` (23 pp, the
previous guide). Ask what they think of the echoes in the guide: the far associations (Laetoli, memory
reconsolidation, Bach's mirror fugue, catastrophic interference), the density (~20 literary-or-beyond items +
4 far for 21 verses), and whether anything reads as bolted on. Their earlier review of the dossiers themselves:
"wow. I really liked the entries" (the v3.1 annotated PDF).

## 2. THE METHODS PAGE IS WRONG IN FOUR PLACES (the author asked; not fixed)

On the new Ps 77 guide's "Methodological & Bibliographical Summary":

| Line on the page | Truth | Cause |
|---|---|---|
| **Literary Echoes (Pass 3 — Source Verification): gpt-5.6-terra** | gpt-6-luna locates the sources; the text is cut from the page at $0 | `psalm_077_pipeline_stats.json` `models_used` still holds the S387 run's `literary_echoes_pass_1a/_2/_3` (the tracker keeps a psalm's earlier keys), and on `--skip-micro` the pipeline copies the bundle's own `models_used` (where `research_assembler` writes `literary_echoes_pass_3 = GPT_VERIFY_MODEL` whenever echoes exist) over what STEP 1b tracked |
| The two labels **"Passes 1-2 — Generation" / "Pass 3 — Source Verification"** | v3 has no passes: proposal (Opus 5.5 + Gemini 3.1 Pro) and locating (gpt-6-luna); the WRITER selects | the renderers (`document_generator.py` ~2124, `combined_document_generator.py` ~1779, `commentary_formatter.py` ~279) hard-code the legacy wording |
| **Fact Check: gpt-6-sol** | no fact check ran on this guide | same stale `models_used` key from S387 |
| **Concordance Searches: N/A** | 22 searches, 514 results (the bundle's Research Summary) | known since S387: after `--skip-micro` the stats have `concordance_requests: []` |

Everything else on that page checks out (21 verses; 21 LXX; 148 commentary entries with those per-commentator
counts; 251 figurative; 4 Sacks; similar psalms; macro/micro/liturgical/SD/writer/citation/copy-editor models;
prompt size 447,105 = inputs 423,987 + essay instructions 14,347 + verse instructions 8,771).

**Fix sketch** (~$0): in `run_enhanced_pipeline.py`, when STEP 1b runs, DELETE the stale echoes keys
(`literary_echoes_pass_1a/_1b/_2/_3`) and set v3 keys AFTER the skip-micro `models_used` copy (or make that copy
skip `literary_echoes_*` when STEP 1b ran); drop `fact_check` from `models_used` when `--fact-check` is off; teach
the three renderers v3 labels ("Echoes — proposal", "Echoes — locating sources"); fix the concordance count on
`--skip-micro` (parse the bundle's `Concordance searches` line). Then `python scripts/run_docx_only.py 77 --pdf`.

## 3. Echoes v3 — what is production now, and what is open

Production (`--echoes v3`, the default; `--echoes legacy` = the old Gemini + terra pipeline): Opus 5.5 + Gemini
3.1 Pro propose literary echoes, resonances beyond literature and far associations at counts proportional to the
psalm; no judge; every candidate located by gpt-6-luna and its text cut from its page at $0; the used-works
register filters; the WRITER chooses, with the author's targets in `forest_writer.S388_ECHO_EDITS` (≥ 1
Jewish/Hebrew poem, ≥ 1 far association per 5 verses, 0.5–1.5 literary-or-beyond per verse, space no object,
never a register work). Ps 77: echoes $1.22 (legacy $1.41), whole test run $4.11.

Open:
- **The editors' report on a run WITHOUT `--fact-check`**: the stale fact check is now ignored (S389 fix), but the
  report still opens "Three things checked or changed it… a fact checker", and "Cost of the whole run" sums every
  attempt in the cost file ($13.77 on Ps 77). Make both conditional; not put in Documents this time.
- **Opus proposer cost**: ~$0.65 of the $1.22, almost all thinking (28.7K output tokens). Effort `medium` is the
  untested lever; any change there is a quality question for the author.
- **Anthropic's output content filter** blocked one Opus proposal in v3.1 (retry passed; the blocked call's cost,
  ~$0.5, never reached the tracker). Suspect: the ≤ 10-word verbatim `anchor` per candidate. It has not recurred
  in v3.2, and the anchor is now nearly redundant (retrieval uses the locus) — first thing to drop if it recurs.
- **The register is local**: `data/literary_echoes/used_works/psalm_NNN.json` (one per guide) — `data/` is
  gitignored, so a fresh clone starts empty; rebuilding reads every guide once (~$0.11): `python -c "from
  dotenv import load_dotenv; load_dotenv('.env'); from src.agents.echoes_v3 import EchoesV3Agent;
  EchoesV3Agent().used_works(0)"`. It is WORK-level by the author's choice (Dante's *Inferno*, used in Ps 40,
  now blocks every canto); the author said "never reuse" — confirm they are content with that for epics/plays.
- **Ps 77's synthesis discovery was REUSED** from S387 to save ~$2, so its observations were made against the old
  dossier. S388's shared SD↔writer cache therefore was NOT exercised by this run — S389's handoff item 1 stands.
- **Far lane at the floor**: the writer used exactly 4 far associations (floor 4). Watch on the next psalms.
- **Legacy code kept**: `literary_echoes_agent.py` (+ its `AuthorLedger`) serves `--echoes legacy` only; v3
  dossiers use `###`/`####` headings, so the author ledger no longer counts them (the register replaces it).
- Experimental S389 scripts (`s388_echoes_packet.py`, `s388_echoes_annotated.py`) read the trial dirs
  `output/psalm_7[67]/echoes_v3/` and `echoes_v3_1/`; archive them once the author has read the new guide.

## 4. Also observed on the S389 Ps 77 run (for S388's items)

- **Edits-mode copy editor** (S388 default) ran cleanly: `Edits mode: 15 change(s), 17 edit(s): 17 applied, 0 not
  found, 0 ambiguous, 0 refused`; $0.535. One change corrected a far-association fact (hand anatomy).
