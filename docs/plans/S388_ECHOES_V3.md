# Session 388 — Echoes v3: aptness first, three proposers, a judge, text cut from the page

*This is **Session 389**'s work: it ran in parallel with Session 388 and began before S388 committed, so it carries the S388 label here and in code comments. Handoff: `NEXT_SESSION_PROMPT_session_390.md`.*

**Status: EXPERIMENTAL, not wired into the pipeline.** Code: `src/agents/echoes_v3.py`,
`scripts/run_echoes_v3.py`, tests `tests/test_echoes_v3.py`. Writes only to
`output/psalm_N/echoes_v3/`; never touches `data/literary_echoes/` or the author ledger.
Reading packet: `scripts/s388_echoes_packet.py` → `Documents/Psalm study guide/Psalms 76 and 77 - Echoes trial (S388).docx/.pdf`.

## Why (measured on the production dossiers)

- **The Ps 77 writer's best echoes came from its own memory.** Hopkins ×2 ("No worst", "I wake and
  feel the fell of dark") and Dickinson ("After great pain") sit on vv. 3–7, the psalm's core. Both
  authors are banned from the dossier by the ledger (Hopkins 6 psalms, Dickinson 8), and Dickinson
  was Gemini's "Default bypassed" for 77:3–5. The bans kept apt echoes out of the *dossier*, not the
  *guides*; they arrived unchecked instead. S385's blind read: none of the top three Ps 76 essays
  used a dossier echo.
- **Chosen for distance, not fit.** The Ps 77 writer framed several dossier entries as opposites
  ("the psalmist's memory is the opposite", "the meaning is reversed", "something like un-making").
- **The generator reads the psalm blind** (text only) and clusters by topic.
- **It quotes from memory.** 8–13 of ~20 entries corrected per psalm; verification is 55–70% of a
  bill that rose from $0.85–1.05 (to Ps 72) to $1.18–1.41 (Pss 73–77).

## Shape

1. **Propose** — Opus 5.5, GPT-6 Sol, Gemini 3.1 Pro in parallel, each with the psalm AND the macro
   reading. Each names 8–14 MOVES (what the poem does, not its topic), then proposes candidates in
   two lanes: literature (~0.9/verse) and beyond literature (~0.6/verse: math, science, art, music,
   history, archaeology, anthropology, sociology, psychology, law, film...). **No quotations** — work,
   locus, ≤10-word anchor. No bans; "obvious" allowed and marked. Hebrew Bible excluded (the
   commentary's job).
2. **Judge** — Opus 5.5, anonymised + shuffled pool, rubric: specific shared move → psalm reads
   differently → force → surprise → quotability → **series diversity as tie-break only** (the author's
   decision). Picks ~0.75/verse literature + ~0.6/verse beyond, plus alternates.
3. **Locate** — gpt-6-luna + web search returns up to 3 URLs per passage (original / translation) and
   the first/last line as search keys. **It does not copy text.**
4. **Cut ($0)** — Python fetches each page, keeps its line structure (drops line numbers, zero-width
   marks, layout blanks), finds the first/last lines fuzzily and cuts the passage. A quotation is on
   its page by construction. Guards reject page furniture (repeated lines, one-word UI labels,
   space-less PDF text, a non-Latin original that runs into Latin menus). Beyond-literature entries
   keep the gather-and-page-check of the S386 fact checker.
5. **Retry once, promote alternates**; anything still without text appears as *reference only*
   (move + locus), never as an unconfirmed quotation.

## What went wrong while building it (kept, because each is a trap)

- **`fact_checker.parse_fact_check_json` reads the top-level key `claims`.** A schema with `items`
  parsed to zero records silently (run 1 lost its retrieval; ~$0.10).
- **Luna will not copy long passages** even when public domain: it returned ONE line of Hopkins's
  sonnet, one of Celan, one of Walcott ("only a brief excerpt is provided here"). Hence locate-then-cut.
- **Substring page checks fail correct text** on pages that print line numbers (RPO Cowper) or render
  with JavaScript (Folger, Princeton Dante). Hence line-structured extraction and 3 URLs per passage.
- **HTML source newlines are whitespace**; treating them as line breaks double-spaced every poem.
- Opus proposals omit optional keys (no schema is enforced on Opus); read every field with `.get`.

## Ps 77 (first trial)

Pool 96 (32 per proposer). Judge chose 16 literary + 13 beyond. Hopkins was proposed by ALL THREE
families; Dickinson and Cowper also surfaced — none named in any prompt.
**Self-preference watch:** 14 of 16 literary finalists were Opus's own proposals (0 Gemini).
Cost of the design on Ps 77: propose $0.85 (Opus $0.53, Sol $0.14, Gemini $0.18), judge $0.39,
locate $0.25 → **$1.48** (production: $1.41). Development false starts added $0.36.

## Ps 76 (second trial, the finished design end to end)

Pool 60. **Every held-out answer surfaced unprompted:** Byron's *Destruction of Sennacherib* (all
three proposers; production had discarded it as "Default bypassed"), the Iliad (Opus, Gemini;
Homer is banned in production), Sennacherib's prism (Opus, Sol), Herodotus 2.141, the Lachish
reliefs, the Black Obelisk. The judge kept Byron, the Iliad, Herodotus, the prism.
Literature: 10/10 finalists with text (7 original + translation where needed, 3 translation only).
Beyond: 2 of 8 page-verified; 5 flagged (British Museum, ResearchGate, dokumen.pub return 403 to any
script); **the prism was not located** and stands as reference only.
**Cost: $1.17** (propose $0.80, judge $0.26, locate ~$0.12) vs production **$1.18**.

## v3.1 (the author's review of v3, same session)

The author's asks → changes: (1) one locus per entry — the judge's `retrieve` is authoritative, and two
passages of one work are separate candidates; (2) a SECOND JUDGE, Gemini 3.1 Pro — every Gemini
non-literary item the author liked in v3 (Chelyabinsk, Illerup bog, Durkheim, tsunami drawback, Kelvin
wake, Creation of Adam) had been discarded by the Opus judge; (4) a FAR-ASSOCIATIONS lane (abstract the
move to a bare pattern, then find it in a distant field; each proposer gets a different random draw of
15 fields from 203); (5) ≥2 Jewish/Hebrew poems per proposer, ≥1 in the dossier (merge rule); (6) the
judges SCORE every candidate 0–5 on illumination, truth, craft, interest, humour, haunting, memorable,
originality, thought-provoking; gates are truth-or-fixable and illumination, and a fixable error is
corrected (`fix`), not rejected; (7) a WORK-level used-works ledger read from the finished guides by
gpt-6-luna ($0.11 once, then cached in `output/_echoes_used_works/`): 411 quoted works in 47 guides;
used works are filtered before judging. It found Hopkins's "I wake and feel" already in Ps 43's guide
(Ps 77's guide repeated it) and Celan's "Psalm" in 41, 43, 44. Authors stay a tie-break.

Results (`output/psalm_N/echoes_v3_1/`; report: `Psalms 76 and 77 - Echoes v3.1 annotated (S388).pdf`):
- Ps 76: $2.01 — 14 literary / 10 beyond / 8 far in the dossier; 3 Hebrew poems (HaNagid, Bialik,
  Amichai); 1 dropped as used (Kalir, Ps 74).
- Ps 77: $2.66 (+ ~$0.5 unrecorded: Opus's first proposal was **blocked by Anthropic's output content
  filter** and the blocked stream never reached the tracker; the retry passed) — 25 / 19 / 11, i.e.
  **55 entries for 21 verses: too many** (the ×1.35 union cap plus promoted alternates). 2 dropped as used.
- Cost moved up: two judges scoring every candidate = $0.80–1.10 (was $0.26–0.39); Opus proposer
  $0.64–0.74. Levers: score only a shortlist; cap the union at 1.0×; Opus proposer at `medium`.
- The Opus content-filter block is new in v3.1 (v3 ran twice clean). Suspect: the ≤10-word verbatim
  `anchor` per candidate across ~40 candidates; the anchor is now nearly redundant (the judge's locus
  drives retrieval) and is the first thing to drop if it recurs.

## v3.2 — PRODUCTION (the author's cost decision, same session)

**No judge.** Opus 5.5 + Gemini 3.1 Pro propose all three lanes at counts proportional to the psalm
(`budgets_writer`: 0.6 / 0.4 / 0.25 per verse per proposer); duplicates of the same PASSAGE merge
(`same_passage`), other passages of a work stay; the used-works register filters; gpt-6-luna locates
EVERY candidate and the text is cut from its page ($0); one retry. The whole unfiltered dossier goes to
the writer (`assemble_writer_dossier`, headings from `###` so it nests under the bundle's `##` section),
ending with the register as "never quote or cite these".
- **Writer** (`forest_writer.S388_ECHO_EDITS`, applied to the approved S384–S386 texts; the tests still
  pin everything else byte for byte): choose by illumination AND beauty, humour, haunting, originality;
  ≥ 1 Jewish/Hebrew poem; ≥ 1 far association per 5 verses; 0.5–1.5 literary-or-beyond per verse; space
  no object; never a register work.
- **Register** (`data/literary_echoes/used_works/psalm_NNN.json`, one file per guide, re-read when the
  guide changes or `USED_WORKS_VERSION` bumps): every work a guide quotes OR cites as a comparison, but
  not the psalm's own liturgical settings (v1 had filled it with "Yom Kippur Vidui", "Sefard Siddur").
  Work-level: Dante's *Inferno* (Ps 40) now blocks every canto. 382 works / 48 guides after Ps 77.
- **Pipeline**: `--echoes v3` (default) / `legacy`. On `--skip-micro` the reused bundle's echoes section
  is replaced (`research_assembler.replace_literary_echoes_section`). Every echoes call is recorded in the
  pipeline's CostTracker (`EchoesV3Agent(cost_tracker=...)`).
- **Editors' report fix**: a `fact_check.json` older than `print_ready.md` belongs to an earlier guide and
  is ignored (it was pairing the S387 guide's 316 claims with this guide's copy edit). The report's intro
  and its "cost of the whole run" (cumulative across attempts) are still wrong for a run without
  `--fact-check` — open.

**Ps 77 test** (`--skip-macro --skip-micro --reuse-synthesis-discovery`, no fact check): **$4.11** —
echoes $1.22 (Opus $0.65, Gemini $0.23, locate ~$0.34; 47 candidates: 22/15/10; 4 dropped by the
register), writer $2.29 (cache write 251K vs 231K: the bigger dossier adds ~$0.08), citations $0.07,
copy editor $0.54 (15 changes; one corrected a far-association fact, the hand-anatomy analogy).
The guide used ~20 literary-or-beyond items (range 11–32), 4 far associations (floor 4), Yedid Nefesh as
the Hebrew poem, and none of the register's works (0 Hopkins/Dickinson/Celan/Larkin). Previous guide:
`archive/psalm_77_S387_guide/` and `Documents/…/Psalm 77 (S387).pdf`. Synthesis discovery was REUSED from
S387, so its observations were made against the old dossier.
- Cost lever not yet pulled: the Opus proposer is ~$0.65 of the $1.22, almost all thinking (28.7K
  output tokens); effort `medium` is untested.

## Session spend

Ps 77 $1.84 (design $1.48 + $0.36 of false starts) + Ps 76 $1.17 = **$3.01**.

## Open

- Self-preference: try a Sol judge (≈ $0.10) or a two-judge union on the same pool at $0 re-propose.
- Cost levers: Opus proposer at effort `medium`; judge on Sol. Neither measured.
- Wiring into the pipeline (and the writer prompt's handling of a "Resonances beyond literature"
  section) waits for the author's read of the packet.
