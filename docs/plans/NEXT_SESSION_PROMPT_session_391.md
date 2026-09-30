# Next session (391) — start here

Session 390 was a $0 session that closed the S390 handoff's code items: the Ps 77 methods page (four wrong lines,
plus a fifth found on the way: the DOCX printed only "Concordance Searches: 22"), the editors' report on a run
without a fact check, and the lemmatized LXX (now Brenton's inflected Greek). Details: `IMPLEMENTATION_LOG.md`,
Session 390.

## 0. Housekeeping first

- **`Documents/Psalm study guide/Psalm 77.docx` may be one version behind** (the PDF there is current). The last copy was blocked because the DOCX was open. If needed:
  `cp output/psalm_77/psalm_077_commentary.docx "Documents/Psalm study guide/Psalm 77.docx"`
- Nothing from Session 390 has been committed unless the author asked for it at the end of that session; check
  `git status`.

## 1. The author's read of the Ps 77 guide (echoes v3) — still not asked

`Documents/Psalm study guide/Psalm 77.pdf` (22 pp) vs `Psalm 77 (S387).pdf` (23 pp). Ask about the far associations
(Laetoli, memory reconsolidation, Bach's mirror fugue, catastrophic interference), the density (~20
literary-or-beyond + 4 far for 21 verses: the far lane sat exactly at its floor), and whether anything reads as
bolted on. Worth knowing when they read it: the copy editor made 6 factual edits with no fact-check report behind
them (the editors' report lists them), two of them to far-association facts (Laetoli "our own species";
grip strength).

## 2. On the next paid psalm run (S388's handoff §1–2, still open)

Check that the SD → writer dossier cache HITS; the log lines are in `NEXT_SESSION_PROMPT_session_389.md` §1 (and
the memory note `next-run-cache-check`). Report hit/miss to the author before anything else. Also watch: edits-mode
copy editor, the fact checker's free lookups (`search_liturgy`, `get_lxx`, now with Brenton's Greek), and that the
methods page shows the v3 echoes lines, no stale "Fact Check", and a full concordance description.
**New in S390, also to confirm on that run:** the first run downloads Brenton's Greek once (~5 MB, log line
`Downloading Brenton's Septuagint…`, then `LXX Psalm N … Brenton's Greek, K verses`); the micro analyst's
psalm-text block should show inflected Greek (`LXX (Greek): Φωνῇ μου …`).

## 3. The author's decisions (made in S390, all built)

- **The writer gets the LXX** (Brenton's Greek, an `**LXX:**` line per verse in `_get_psalm_text`); verify on the
  next run that the writer's prompt shows it and that SD's dossier head still matches (`[forest] dossier head …
  matches`). The MT↔LXX map is now verse-level (the old chapter table was wrong for MT 10, 114–116, 146–150).
- **Register: never reuse a QUOTATION** (passage-level for texts; non-texts still used whole). Watch the log
  lines `[echoes] N works in the used-works register` and any `located passage(s) repeat a quotation`.
- **Opus proposer**: left as is.

## 4. Open, carried from S389/S390

- Anthropic's content filter blocked one Opus proposal in v3.1 (~$0.5 unbilled); suspect the verbatim `anchor`;
  drop it if it recurs.
- The register is local (`data/literary_echoes/used_works/`, gitignored; version 3 since S390); rebuild command in
  `NEXT_SESSION_PROMPT_session_390.md` §3 (~$0.12). `data/lxx/` re-downloads itself.
- Ps 77's synthesis discovery was reused from S387 (observations made against the old dossier).
- Archive the S389 experimental scripts (`s388_echoes_packet.py`, `s388_echoes_annotated.py`) once the author has
  read the guide.
- The post-copy-edit citation re-check (STEP 5b½, $0) runs only with `--fact-check`; it could run always.
- Remaining fact-check trims (≈ $0.18/psalm) measured but not built (S388).
