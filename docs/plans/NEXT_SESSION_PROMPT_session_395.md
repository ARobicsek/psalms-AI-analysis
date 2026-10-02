# Next session (395) — start here

Session 394 moved the micro agent to Sonnet 5.5 at `xhigh` (A/B on Pss 76 and 77), made the fact check, the
Sefaria reception section and the Targum pipeline defaults, scaled the writer-side trim ceiling with verse count,
taught the verse commentary to carry the thread between notes and to group verses, ran **Ps 78 in full ($15.31)**,
and removed reader questions from the whole pipeline (the cross-verse observations now fill a template slot).
Details: `IMPLEMENTATION_LOG.md`, Session 394; the micro A/B: `archive/psalm_76_S394_micro_sonnet55_ab/README.md`.

## 1. The author's read of the Ps 78 guide (not yet asked)

`Documents/Psalm study guide/Psalm 78.docx|pdf` and `Psalm 78 - What the editors did.docx`. The first guide built
on everything at once. Worth asking about specifically:
- **the thread between notes and the grouping** (S394's new verse instructions): 32 notes for 72 verses, 25 of
  them groups; does the commentary now read as one walk, and is any group too long (vv. 44–48 is five verses)?
- **the Sonnet 5.5 micro material**, which reached the writer thinner on this long psalm (below);
- the reception section (41 passages) and the Targum in use (vv. 66, 69);
- length: essay ≈ 2,900 words, verse commentary ≈ 17,400 (with Hebrew).

## 2. Chunk the micro discovery pass for long psalms (before Pss 89, 104–107, 119)

Sonnet 5.5 at `xhigh` compresses a long psalm: Ps 78 got 127 chars per insight (Ps 77: 254; Sonnet 4.6 on Ps 37
wrote ~2.5 KB per verse against 5.5's ~1 KB here) and 27 of 72 verses had no figurative flag. Sketch: in
`MicroAnalystV2._discovery_pass`, above ~30 verses, run Stage 1 per verse range (say 20–25 verses, the same
macro analysis in each) and merge `verse_discoveries` and `interesting_questions`; Stage 2 unchanged. Test on
Ps 78 micro-only (macro is on disk; ~$1–1.5) and compare density with the S394 run.

## 3. The fact-check budget on long psalms (the author's decision)

The fact check is now ON by default. Ps 78 cost **$4.49** (652 claims; all 44 contradicted were fixed) against
the recorded ~$1.80 (≤ $2) per-psalm budget; it scales with length. Options: accept it for long psalms; or
build the S388 trims (scope evidence to named commentators ~$0.10, one-line supported records ~$0.08 on Ps 77).

## 4. Watch: synthesis discovery's empty answer

Ps 78's first SD call returned 9,179 output tokens and 0 chars of text (likely a mid-stream refusal on a
plague-heavy 650K dossier); the retry on the same input succeeded. SD now logs `stop_reason` and `stop_details`:
if it recurs, read the category before designing anything (a retry, or a fallback model).

## 5. Small, $0

- Past V4 writer-prompt A/Bs seeded from production (`ab_seed_base_from_pipeline.py` + `ab_writer_prompts.py`)
  compared arms that also differed by a questions block (fixed in S394): treat their prose-level verdicts as
  confounded. Forest-writer trials (S384–S386) were not affected.
- Ps 78's guide has one surviving "most famous" (line 571, the Haggadah use of v. 38), flagged by the
  superlatives check.

## 6. Carried from earlier handoffs

`NEXT_SESSION_PROMPT_session_394.md` §2–3 → the 393 handoff: the author's read of the Ps 76 reception A/B (moot
as a default decision now, but the guides are unread); the rebuilt Sacks section's first writer run (Ps 78 had 2
Sacks references; a psalm with prayer-book commentary — Ps 92, 27 — is still the real test); Ps 77's methods-page
Sacks count (`research.sacks_references_count` → 0, then `run_docx_only.py 77 --pdf`); the deep-research
liturgy-and-practice table and the two unsourced sentences in the Ps 76/77 guides; the older 391 items.
