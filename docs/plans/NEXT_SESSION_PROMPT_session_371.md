# Next Session Prompt — Session 371

**Written**: 2026-08-02 (end of Session 370)
**Author's stated plan, verbatim**: *"in our next session I'll ask you to mine recent writing for
great positive examples, and then to run an A/B/C test."*

Items (a) and (b) are the author's explicit request. Do those first.

---

## (a) Mine recent guides for great POSITIVE examples

**Why.** The writer prompt teaches largely by negation — measured at **24 negative markers**
(`WEAK:`, `BLOATED:`, `AVOID:`, `NEVER`, `DON'T`, `FORBIDDEN`) against **13 positive**
(`STRONG:`, `CLEAN:`, `FIXED`, `TARGET`). Current Anthropic guidance is consistent across Opus 4.7,
Opus 5 and Sonnet 5 that **positive examples showing the desired output outperform instructions
saying what not to do**. RULE 13 already works this way — its six "voice exemplars" are all real
sentences from prior guides — and that is the model to extend.

**The job.** Mine the finished guides (`output/psalm_*/psalm_*_copy_edited.md`, plus the
`Documents/Psalm study guide/*.docx` the author has actually kept) for real, in-house sentences that
demonstrate what the prompt currently only describes. Target the rules that are pure prohibition today:

| Rule | Currently teaches by | Wants a positive exemplar of |
|---|---|---|
| RULE 7 (blurry photograph) | a list of banned nouns | an abstract idea made concrete |
| RULE 7b (false profundity) | 2 BLOATED→CLEAN pairs | a real aphorism that *earns* its shape |
| RULE 8 (orphaned facts) | "drop the orphan" | a routine fact handled in one honest clause |
| RULE 8b (commentator's burden) | 5 gates + a budget | a commentator quote that *transforms* a verse |
| RULE 3b-2 (point, don't name) | 2 BROKEN→FIXED pairs | grammar shown, never named |
| Affective landing | a description | 2–3 landings the beta reader rated `found` |

**Sourcing note.** The beta-read files (`psalm_*_beta_read.md`) already flag "moments that landed"
with AHA/FELT tags across ~15 psalms — that is a ready-made, independently-judged candidate pool.
Prefer those over your own taste. Verify each candidate is still in the *copy-edited* text (some
were cut downstream).

**Watch:** RULE 13's exemplars carry an explicit *"NEVER quote them, echo their wording, or rebuild
their sentence-shapes"* guard, because voice exemplars invite pastiche. Any new exemplar block needs
the same guard.

## (b) The A/B/C test — three Opus-5 prompt findings

All three come from checking current Anthropic guidance during Session 370 (via the `claude-api`
skill, not from memory). **One correction to a long-standing assumption**: the "over-prescriptive
prompts reduce quality" warning is documented for **Fable 5, not Opus 5** — Session 367 recorded it
correctly, and it is *not* a reason to shorten our prompt. For Opus 5 the guidance runs the other way
on instruction-following.

The three testable arms:

| Arm | Change | Why |
|---|---|---|
| **A** | **Delete the verification scaffolding** — 16 FINAL VALIDATION CHECKLIST items, 3 `VALIDATION CHECK` blocks, 6 "before finalizing/submitting" instructions | The one Opus-5-specific *delete* in the guidance: "Claude Opus 5 verifies its own work without being asked… Removing them reduces over-verification **with no capability regression** — this is a delete, not a rewrite." Explicitly **inverts** standard prompting practice, so it needs evidence, not faith. |
| **B** | **Flip negative examples to positive** — feed in the exemplars mined in (a) | Positive examples documented to outperform "don't" instructions. Depends on (a). |
| **C** | **Add a conciseness instruction** | Documented ~20% reduction in user-facing length, and the guidance is explicit that **`effort` is NOT the lever for this** — prompting is. Directly the standing "make Opus 5 shorter" item, and cheaper than anything tried so far. |

**Harness.** `scripts/ab_writer_models.py 71 --models claude-opus-5 --beta-read` — writer stage only,
same dossier, ~$2.1 per arm (Session 370's estimate of $0.6–1 was wrong; the writer call carries
~205K input tokens). Preserved comparison arms already on disk:

- `output/psalm_71/_writer_ab/_baseline_pre_rule8b/` — pre-RULE-8b
- `output/psalm_71/_writer_ab/_run1_rule8b/` — rules v1 (tightest citations)
- `output/psalm_71/_writer_ab/claude-opus-5/` — run 2 (permissive; what the author read as rev2)

**Score on**, in order of trustworthiness: the beta reader's `INERT CITATIONS` / `UNEXPLAINED GRAMMAR`
counters and `LANDING`; then word count, commentator mentions, Tier-1 quotes per verse. **Do not**
score by pattern-matching a prior arm's wording — see the canary lesson in
`WRITER_PROMPT_RULE_8B_FINDINGS.md` §7, which produced four false "lost" verdicts in Session 370.

Arm A is the one to run first: it has an explicit no-regression claim attached, and it also shortens
the prompt.

## (c) Validate the third RULE 8b revision — carried, unvalidated

Session 370's second amendment **backfired** (permissive language rebounded length +19% and raised
inert citations 4→7). The third revision replacing it is in the prompt now and **has never been run**.
Fold it into the A/B/C baseline rather than testing separately.

Read `docs/plans/WRITER_PROMPT_RULE_8B_FINDINGS.md` before touching RULE 8b.

## (d) Carried forward from Session 369 — still untouched

- **Opus 5 adoption decision** — now 3 psalms of evidence; the conciseness gap is narrowing.
- **Colon-level doublet alignment** for the Ps 71↔31 class (Session 368's bug: the pair misses by
  0.05 because the unit is the verse, not the colon — do *not* just lower the 0.8 threshold).
- **Post-copy-edit scripture verification** (~$0.15/run; the durable fix for fabricated biblical
  claims).

## Free, no-API cleanup available

**Re-render affected DOCX files.** Session 370 fixed a shipped bug where bolded stress syllables in
phonetic transcriptions rendered flat (Psalm 41 alone had 12 empty bold runs, 0 bolded stress marks).
Any guide quoting a transcription is affected. Re-rendering is `scripts/run_docx_only.py <n>` and
costs **$0** — no writer, verifier, or copy-editor re-run. Session 366's divine-names re-render is
also still outstanding for 17 psalms; both can be done in one pass.

**One human check outstanding**: open `Documents/Psalm study guide/Psalm 71 (Opus 5) rev2.docx` and
confirm the bolded Hebrew prefix letters (e.g. the **וְ** at v.7) render without a hairline gap from
the rest of their word. The XML is correct — adjacent RTL runs, correct order — but Word's visual
join can only be verified by eye.
