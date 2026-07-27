# Session 369 — next-session prompt

Read `docs/session_tracking/IMPLEMENTATION_LOG.md` § Session 368 first; everything
below assumes it.

**State at hand-off**: the copy editor is pinned to **`gpt-5.4`** and validated on
three full-length texts (`docs/plans/COPY_EDITOR_TERRA_FINDINGS.md`, marked
SETTLED — do not re-run that A/B). Terra remains in production everywhere else.
The Master Writer is still **`claude-opus-4-8`**; Opus 5 is now recommended on
**two** psalms' evidence but still NOT adopted — no default has changed.

Session 368's agenda item (a) is closed. Items (b) and (c) below are the
inherited ones.

---

## (a) THE DECISION: adopt Opus 5 as Master Writer?

**This is the one that matters, and it is now well evidenced.** Ps 70 and Ps 71
agree to within 3% on every cost axis:

| | Ps 70 | Ps 71 |
|---|---|---|
| output tokens | 1.97× | 1.99× |
| words | 1.55× | 1.60× |
| wall time | 1.87× | 1.86× |
| writer-stage delta | +$0.37 | +$0.59 |

And they agree on the verdict: **Opus 5 is the better GUIDE, 4.8 the better
ESSAY.** On Ps 71 the librarian never flagged the Ps 71↔31 relationship, yet
from the identical dossier Opus 5 engaged every verse-level variant and 4.8
engaged none (`מָעוֹז` 2/0, `מְהֵרָה` 2/0, `לְבֵית מְצוּדוֹת` 1/0, "Psalm 31"
11/3). **Zero hallucination on both psalms** — every added cross-reference
verified against `tanakh.db`, including one that reads through a ketiv/qere site
(Ps 71:12 ketiv `חישה`, qere `[חֽוּשָׁה]`). 4.8 wins the affective landing both
times (`found` vs `near-miss` on Ps 71).

**Recommendation: adopt, after landing (b).** The cost is ~+$1.5/run if macro and
synthesis discovery follow the writer. Note the two arms' strengths are not
symmetric: the scholarship Opus 5 adds is *unrecoverable by prompt* (it comes
from harder reading of the same dossier), whereas 4.8's compression advantage is
a prompt problem — which is exactly what (b) attacks.

If adopting, change `--master-editor-model` defaults in **both** runners and
price-check `cost_tracker`.

---

## (b) Make Opus 5 shorter without losing the scholarship

Inherited from Session 368; now with a **systematic, 2-for-2 target**.

1. **Kill the `###` intro headers.** Opus 5 introduced 2 body headers in the
   intro on Ps 70 AND 2 on Ps 71; 4.8 produced 0 both times. Production intros
   do not use them. This is a writer-prompt rule and the cheapest win available.
2. **Cap literary echoes at 2–3.** Largest single block of cuttable text.
3. **Conciseness instruction** per the Opus 5 migration guide. Do **not** try to
   solve this by dropping `effort` to `medium` — that trades away the reasoning
   that produced the good material.
4. Beta reader flagged more **template feel** in Opus 5's Ps 71 (Rashi→Radak→
   Malbim survey, in that order, repeatedly). Worth a variety rule.

**Success criterion: word count down, insight count flat.** Count doublet
variants, cross-references and distinct arguments before and after — not just
length. Ps 71's Opus 5 arm is the baseline to beat (12,495 words). This is a
*prompt* A/B on one model, so run two invocations against the same psalm and
diff; `ab_writer_models.py` takes arbitrary `--models` but not prompt variants.

---

## (c) Doublet detector — colon-level alignment

**New bug, fully diagnosed in Session 368.** Ps 71:1–3 is Ps 31:2–4a
redistributed across *different verse divisions*, and the detector missed it
despite Ps 31 scoring 370.46 (highest of any related psalm) with a 5-word
verbatim run.

Measured Jaccard (`related_psalms_librarian._find_shared_verse_pairs`):

```
71:1 vs 31:2 = 0.75   <- clears DOUBLET_VERSE_SIMILARITY (0.70)
71:2 vs 31:3 = 0.19
71:3 vs 31:4 = 0.25
```

Exactly one pair clears 0.70, so it falls to the single-verse branch requiring
`SINGLE_VERSE_SIMILARITY = 0.8` — **missing by 0.05** — and no second pair can
form because the half-verse offset puts neighbours far below the
`GAP_FILL_SIMILARITY = 0.4` bar, while gap-fill assumes a *constant* offset that
drifts here.

**Do not just lower 0.8** — that threshold guards against false positives, and
the root cause is the *unit*: the shared material spans 3 verses of Ps 71 but
~2.2 of Ps 31. Fix at colon/hemistich level (the `׀` paseq and athnach give
natural split points) or with a sliding window over the consonantal token
stream. Regression-check against Session 365's verified cases: 60↔108, 57↔108,
53↔14, 70↔40, and zero false flags on the 11 clean psalms.

---

## (d) Post-copy-edit scripture verification (~$0.15/run)

The durable fix for the highest-stakes failure class. The citation verifier runs
**before** the copy editor (STEP 5a½) and feeds it as `supplementary_prompt`, but
never after — so **the copy editor's own factual assertions are checked by
nothing.** Session 368 caught it fabricating a Hebrew reading (asserting Ps 40:17
has וְיֹאמְרוּ when it does not), which `tanakh.db` settles in one query.

Deferred at the time because Ps 71 produced **zero** instances under `gpt-5.4`,
so the class may be rare enough not to justify the wiring. Re-evaluate after a
couple more production psalms; if it recurs even once, build it.

---

## Carried forward

- **Session 366 leftovers**: **יָהּ has no divine-names rule at all** (design
  call — convention would be קָהּ or י־ה, and הַלְלוּיָהּ needs its own answer);
  and **16 psalm outputs affected by the prefixed-El fix have not been
  re-rendered** — this costs **no AI spend**, the modifier runs at DOCX-build
  time (`document_generator.py:1589`).
- **Prompt caching** (`docs/plans/DOSSIER_CACHE_KEEPALIVE_PLAN.md`) is where the
  remaining money is: ~$1.98/run of un-cached Opus input tokens,
  `cache_read_tokens: 0` on every run to date. Opus 5 halves the cacheable-prefix
  minimum (1024 → 512), improving the case.
- **Gemini 3.6 Flash** for literary-echoes passes 1–2: −$0.12/run. Cleanup, not a
  cost program.
- **Copy editor's run summary under-counts changes** (reports 10/11/13 where the
  change files list 16/28/28). Cosmetic, in the category tally.
- **Housekeeping**: archive `scripts/EXPERIMENT_micro_terra_probe.py` per the
  File Organization Rules; delete the redundant
  `Documents/Psalm study guide/Psalm 70 (Opus 5).docx` (superseded by the
  `CORRECTED` copy — it holds both the false Herbert claim and the pre-fix
  writer attribution); the two DOCX under `output/psalm_71/_writer_ab/` are
  stale because Word held them locked during the Session-368 attribution fix,
  and any future run overwrites them.
