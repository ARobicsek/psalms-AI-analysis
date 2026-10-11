# Session 401: Ps 29, the writer revises its own guide after the fact check; the S401 writer-prompt edits

Two runs of `run_enhanced_pipeline.py 29 --skip-macro --skip-micro --skip-lit-echoes --reuse-synthesis-discovery`
(writer onward; the bundle, echoes dossier and synthesis discovery of the 2026-10-09 run reused), against the
2026-10-09 guide as the baseline. The two full output folders are kept locally, untracked, as
`archive/psalm_29_S400_baseline/` and `archive/psalm_29_S401_run1/`; run 2 is `output/psalm_29/`.
`compare29.py` (here) prints the counts below ($0).

## What changed between the arms

| | Baseline (Oct 9) | Run 1 | Run 2 |
|---|---|---|---|
| Writer prompt | S400 | S401 edits | S401 edits |
| Fact-check corrections made by | copy editor (GPT-5.4) | the writer, effort `medium` | the writer, effort `high` |
| Citation check on the revised text | – | no | yes (`STEP 5a⅞`) |

## Results

| | Baseline | Run 1 | Run 2 |
|---|---|---|---|
| Run cost (writer onward) | ($7.85 whole run) | $3.91 | $3.80 |
| Writer (cache cold: SD reused, so no keep-alive) | $0.89 (cache warm) | $2.02 | $2.06 |
| Fact check: claims / contradicted | 234 / 20 | 279 / 25 | 226 / 19 |
| Revision cost | – | $0.33 (73 s; in 31K, out 10K) | $0.29 + 1¢ filter (66 s; in 28K, out 9K) |
| Contradicted claims handled by the writer | – | 25 / 25 (21 paragraphs, 0 rejected, 0 kept) | 19 / 19 (17 paragraphs, 0 rejected, 0 kept) |
| Copy editor | $0.52 (13 of 14 changes were fact-check patches) | $0.36 (11 style changes) | $0.37 |
| Citation mismatches introduced after the writer | – | 2 (both from the revision; 1 real, 1 false alarm) | 0 |
| Words, whole guide / essay | 7,196 / 2,918 | 7,804 / 2,639 | 7,586 / 2,799 |
| "the same" | 19 | 29 | 26 |
| Traditional commentator mentions | 43 | 53 | 37 |
| Verse notes using the Greek | 5 | 5 | 5 |
| First-person judgments | 0 | 0 | 3 |

**Net cost of the revision**: about +$0.15–0.20 per psalm (the copy editor no longer patches facts).

**Revision quality.** At `medium` the writer still edited sentence by sentence in places ("הָבוּ is *not only* the
language of hymns. It is *also* …"; "the serpent may strike, unless Israel repents now, and he means …") and
inserted a quotation mid-argument: it copied Rashi's loose quotation of Ps 18:14 (יַרְעֵם מִשָּׁמַיִם, closer to
2 Sam 22:14) out of the checker's evidence and printed it as the verse, which also left "That sounds like a
whim" pointing at the wrong sentence. At `high`, at the same cost, the rewrites rebuild the argument: the
"seven voices are singular" paragraph (the seam the author's reviewer found in the baseline) now reads "All
around it the poem is crowded with plurals … The voice alone is never plural"; the Flood correction became a
new point (Gen 9:15 has לְמַבּוּל, "a Flood"; the psalm לַמַּבּוּל, "the Flood, the one already known").

**The S401 prompt edits** (one run each, so within run-to-run variance):
- Echoes: the lead-ins vary more ("Twenty-eight centuries later a Hebrew poet ran this verse backwards"), but the
  relation-announcing move persists ("makes nearly the same turn", "the same convulsion … the opposite
  verdict"). Part of it is fed from upstream: 12 of the 32 *Why it might belong* notes in the echoes dossier
  are compare-and-contrast ("Like the psalm … the difference is … whereas …"), and the Shijing entry came out as
  "same convulsion, opposite conclusion" in all three guides because its note says almost exactly that.
- Other voices: run 1 used Ginsberg's contrafactum hypothesis in the argument ("If Ginsberg is right …") and
  Rev 4:6; run 2 the Swedish hymn behind "How Great Thou Art". Light. No Qumran; Basil, Augustine and the
  Baptism of the Lord (all in the deep research) unused.
- The Greek: 5 verse notes in every guide (the ration allows ~4 in 11 verses); most uses are the interesting
  kind (the Sukkot title, ἀποκαλύψει).
- Own judgment: "The midrash has the facts of Sinai wrong in the way midrash often does, and it has the psalm
  exactly right" (run 1); "I take a third course", "I think the poem intends both" (run 2). Not scheduled.
- Humour: nothing visibly funny in either run; no verdict.
