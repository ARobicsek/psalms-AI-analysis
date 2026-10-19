# Next session (410) — start here

Session 409 (record: `IMPLEMENTATION_LOG.md` Session 409; `archive/S409_shared_passages/README.md`;
`archive/psalm_83_S409_run/README.md`):
- the Related Psalms Analysis section is replaced by **Shared Passages** (`src/concordance/shared_passages.py`: doublets
  and shared lines over the whole Bible; 2.7% of the old section's size over all 150 psalms, none for 66);
- the deep-research cleaner's cap is **$0.20** and a failed cleanup **stops the run** before STEP 1 (the author's choice);
- **Ps 83** ran end to end on both ($7.44), guide at `Documents/Psalm study guide/Psalm 83.docx` (+ PDF).

## 1. The author's read of Ps 83

Ask for it. Things the author may notice, already known:
- **The essay is long**: 3,084 words after the edit turn (draft 3,499; target 2,000–2,400). Earlier Argon edits landed
  2,516 (Ps 29) and 2,618 (Ps 82 B). The author asked to keep the edit turn as it is (memory `essay-edit-turn-keep`), so
  only raise it if the author finds the essay too long; if so, the lever is the edit request's length line, not the
  `essay_measures` counter (~7% high, deliberately left).
- Fact check 36/261 contradicted (13.8/100), all handled by the revision; counting slips and absolutes again lead.

## 2. Offered, not built

- **Re-render the methods page of Pss 29, 81, 82** ($0): full runs never recorded `deep_research_checked` (fixed in S409),
  so their methods pages say "Deep Web Research: Yes" for checked reports. Fix = set `research.deep_research_checked`
  in each `psalm_NNN_pipeline_stats.json` where the bundle loaded the clean file, then `run_docx_only.py N --pdf` (and
  re-copy to `Documents/` if the author wants). Production `output/psalm_29/` is the S401 Opus guide: check its bundle.
- **The citation checker's pairing** (`STEP 5a½`): on Ps 83 it raised 16 NOT_SUBSTRING flags before the revision, almost
  all a quote checked against a neighbouring citation in a sentence that carries several, or a midrash/piyyut quote
  checked against the verse it comments on; after the revision 1. Harmless this time (the copy editor sees the
  post-revision report, and the revision changed no citation), but the pre-revision report is noisy. Offer to look at
  how quotes are paired with citations; do not build unasked.
- **`--skip-micro` never refreshes a bundle's deep research** (carried from the 409 prompt §1): echoes, liturgy and now
  shared passages have in-place swaps; deep research has none. A `replace_deep_research_section` would close it.

## 3. Watch on the next runs

- **Shared Passages** on a doublet psalm (108 is the natural one; 96, 105, 106, 115, 135, 136 too): the section must lead
  with the DOUBLET and the guide must name it. On a psalm with none, nothing is printed.
- **The cleaner pre-flight**: the next psalm with a new check runs the cleanup before STEP 1 (a `[COST] deep research
  cleanup` line). A failure stops the run with exit 3 and the fix in the message.
- Carried from the 409 prompt §2: the 65,536 cap on long psalms' verse calls; Argon's long sentences; calibration of
  conjectures; re-check the `gemini-4-argon` price row after 2026-11-30.

## 4. Carried

The 409 prompt §3 (the 407 handoff: shared-dossier errors, the block-quote guard on Argon's revision — it fired on 12 of
27 paragraphs on Ps 83, every dropped line an unchanged quotation — and the batch re-render offer).
