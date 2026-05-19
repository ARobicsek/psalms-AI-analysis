# Next Session Brief — Session 347: Synthesis as Discovery Tool, Not Spine

**Date written**: 2026-05-19 (end of Session 346)

## The one-line goal

**Add a synthesis-discovery pass to the production one-call writer that surfaces specific cross-verse philological moves the one-call misses — as input observations the writer can weave in naturally, *not* as a mandatory structural spine.**

## How this is different from what's already been tried

Two earlier attempts to make the pipeline "more synthetic" have failed in instructive ways:

1. **The old `InsightExtractor` / "curated insights" curator** (still in `src/agents/insight_extractor.py`, retired as default). It was *extractive*, not generative — it filtered material that already existed in the research bundle. It could not *construct* cross-verse claims like the ק-ר-ב dual-lexeme reading, because that claim isn't in the bundle until someone reads multiple verses together and builds it. It also emitted one-sentence labels with `affects_verses` lists, which is structurally incapable of carrying a reasoning chain. Net effect: "no better than not having it" (your own assessment last session).

2. **The two-call experiment built this session** (`scripts/EXPERIMENT_two_call_synthesis.py` + `EXPERIMENT_two_call_finalize.py`). Did the opposite of the curator: a fully generative synthesis pass producing ≥3 cross-verse syntheses with anchor-verse assignments, then a write call forced to build essay + verse commentary around that spine. Tested on Ps 54 and Ps 55 with two variants (3–4-cap and scaled+guardrail). Empirical findings:
   - **The architecture demonstrably surfaces real insights the one-call misses** — the ק-ר-ב dual-lexeme reading (קֶרֶב "interior" / קְרָב "battle" sharing consonants); the Exod 13:22 לֹא־יָמִישׁ inversion ("the pillar that did not abandon Israel becomes the deceit that will not abandon the city"); the שׁלם v.19↔v.21 contestation. None of these are in the shipped Ps 55 one-call output. All are in both two-call versions (cap-3/4 and scaled).
   - **The architecture's cost on prose was real.** The scaled version (12 syntheses) took 32 copy-editor changes vs the cap-3/4's 20. The evidence-honesty guardrail caught the specific failure modes I targeted (no "homophony" overclaim; no "signature root" Babel; no invented Exodus 10:3 prooftext) but the writer found *new* over-reaches (חלל "stab through," עָמָל = "birth-labor," "prayer begins where evil cannot follow," plain counting errors).
   - **External evaluation was split 3-way.** Gemini #1 picked the shipped one-call (B); Gemini #2 picked scaled two-call (A); Claude Opus 4.7 picked cap-3/4 (C). Gemini also hallucinated a "fatal" Hebrew error in C that doesn't exist (a BiDi rendering failure — the text correctly uses ק-ר-ב). With that error removed, the split remains genuine. The lesson: forcing a spine doesn't produce uniformly preferred prose; the gains live in *which insights surface*, not in *how the piece is structured*.

## The proposed design — synthesis as sidecar discovery

**The synthesis pass does what only it can do (generative cross-verse discovery), and the production one-call writer continues to do what it already does well (prose, voice, distributing observations across verses by its own judgment).**

```
RESEARCH BUNDLE  ────────────┐
MACRO ANALYSIS   ────────────┤
MICRO ANALYSIS   ────────────┼──> [NEW: SYNTHESIS DISCOVERY PASS]
PSALM TEXT       ────────────┤            │
                             │            ▼
                             │     CROSS-VERSE OBSERVATIONS
                             │      (3–8 calibrated claims,
                             │       with verse anchors and
                             │       per-verse Hebrew evidence)
                             │            │
                             ▼            ▼
                       MASTER WRITER (unchanged production prompt)
                             │
                             ▼
                        prose output → downstream chain
```

The new input block sits alongside the existing `KEY INSIGHTS TO INCORPORATE` slot in the writer prompt — labelled something like `CROSS-VERSE OBSERVATIONS (use these where they fit; do NOT structure your commentary around them)`. The writer retains full authorial discretion. No anchor-verse requirement. No "develop in full" mandate. No spine.

## Why I think this works where the old curator didn't

| Failure of old curator | How sidecar discovery fixes it |
|---|---|
| Extractive — filtered material already in the bundle | Generative — constructs claims by reading across verses |
| One-sentence labels, no evidence | Full claims with per-verse Hebrew + reasoning |
| Sees same inputs, no sharper task than the writer | Has a privileged angle: cross-verse synthesis is its ONLY job, with an adversarial novelty filter as its method |
| Feeds a sidecar with no structural role | Still a sidecar — but the *content* is what the writer cannot generate alone, not a filtered subset of what it can |

And why I think this works where the spine architecture (the two-call experiment) over-corrected:

- The two-call's spine *did* surface the insights, but it also *forced anchored arcs into specific verses*, which made the verse-by-verse feel architecturally over-engineered and raised the over-claim surface area (every anchored arc needs supporting moves; some of those moves reached harder than evidence supported).
- The empirical observation that justifies sidecar: in both two-call versions, the writer's prose carried the insights wherever they belonged — the spine wasn't actually needed to land them in the prose. The insights themselves carried.

## What needs building

### 1. A new agent: `src/agents/synthesis_discovery.py`

- Single-purpose: cross-verse synthesis discovery.
- Prompt borrows the strong parts of `SYNTHESIS_TASK` from `scripts/EXPERIMENT_two_call_synthesis.py` (the brainstorm-then-adversarial-novelty-filter procedure; the "what a synthesis is and isn't" definitions; the per-verse Hebrew evidence requirement). **Drop** the anchor-verse assignments and "how to signal at other verses" fields — those exist only because the spine architecture needed them. **Keep** the governing thesis + tiered survivors structure.
- Output: a calibrated list of cross-verse observations (no fixed count — quality gate only), each with: the claim, the verses it spans, the per-verse Hebrew evidence, a novelty check.

### 2. A *better* evidence-honesty filter than I shipped

The Session-346 guardrail caught what I named but not what I didn't name. The empirical record from the Ps 55 scaled+guardrail run (`output/psalm_55/EXPERIMENT_two_call/psalm_055_copy_edit_changes.md`) is the regression test set — every change the copy editor made is a class of overclaim the synthesis prompt should pre-empt. Specifically:

- **Counting errors** ("eight movements" / "ten"; "eight words" / "five"; "the final two words"). Add: *"If you cite a number — of movements, of occurrences, of words in a clause — literally count first. The reader can count too."*
- **Strained etymology** (חלל = "stab through" the covenant). Add: *"The primary lexical meaning is what survives the copy editor. Cognate fields (חָלָל 'slain', etc.) can resonate; they are not the verb's argument."*
- **Non-sequitur synthesis** ("prayer begins where evil cannot follow"; "three over two outcovers evil"). Add: *"If your synthesis requires a step where the reader must accept a leap to feel the force, it's overreach. State the more modest claim that survives strict reading."*
- **Fabricated parallels** (Ps 88:16 "אֵמֵי מָוֶת" — doesn't contain that phrase). Add: *"Every claimed parallel must be a phrase you can quote literally from the cited verse. If the phrase isn't there, the claim isn't there."*
- **Non-uniqueness claims** ("the only other place," "exactly one comparable formula elsewhere"). All three versions over-claimed Exod 13:22's לֹא־יָמִישׁ as unique; Jer 17:8 and Josh 1:8 belong to the same family. Add: *"Uniqueness claims about formulae require checking. 'In one striking parallel' or 'most notably' carries the same force without the false uniqueness."*

The principle these collectively express: **calibration is enumerable failure modes plus a final rule that says "if you can't think of two failure modes you didn't already check, you haven't checked enough."**

### 3. Pipeline integration

- Add as an OPTIONAL pre-writer step in `scripts/run_enhanced_pipeline.py`, gated on a `--synthesis-discovery` flag (default OFF until trusted). When on, runs between micro and writer.
- Output saved to `output/psalm_NNN/psalm_NNN_synthesis_discovery.md` (transparent, debuggable, and lets a user inspect and re-run downstream without re-running synthesis).
- The writer prompt assembly (in `_perform_writer_synthesis`) needs a small change: when the discovery file exists, splice its content into the writer prompt as a new top-level INPUT block labelled `CROSS-VERSE OBSERVATIONS (use where they fit; do NOT structure your commentary around them)`. Insert it *after* `KEY INSIGHTS TO INCORPORATE` so the writer reads it as additional input, not as overriding instruction.
- Cost tracked through `CostTracker`. Model: `claude-opus-4-7` to match the writer (and because that's what the Session 346 experiment used successfully).

### 4. Testing plan

1. Build the agent, integrate behind the flag.
2. Run on Ps 55 *fresh* (delete production `output/psalm_55/psalm_055_edited_*`, `_pre_copy_edit*`, `_copy_edit*`, `_citation_verification*`, `_print_ready*`, `_commentary.docx`; then `python scripts/run_enhanced_pipeline.py 55 --resume --synthesis-discovery --skip-questions`). Resume skips macro/micro/lit-echoes (all preserved).
3. Compare the result to: shipped Ps 55 (in `psalm_055_commentary.docx`, untouched), and the two two-call DOCXs in `output/psalm_55/THREE_WAY_COMPARISON/` (key in `_MAPPING_KEY.md`).
4. Specifically check whether the new run:
   - Surfaces the ק-ר-ב dual-lexeme reading? (the headline insight from two-call)
   - Surfaces the Exod 13:22 inversion at v.12? (without claiming it's "the only" comparable formula)
   - Surfaces the שׁלם v.19↔v.21 contestation?
   - Avoids the architectural over-engineering the two-call exhibited?
   - Lowers the copy-editor correction count below scaled's 32 / cap-3/4's 20?
5. If Ps 55 result is satisfying, also test on a *short* psalm (e.g., Ps 117 or Ps 134) and a *long* one (Ps 78 if cheap; otherwise Ps 119 sections are overkill — pick from 23-verse range like Ps 18 or Ps 22) to confirm the scaling works at both ends.

## Artifacts from Session 346 to reference

- **The discardable experiment scripts** (still in `scripts/`, clearly named `EXPERIMENT_*`):
  - `scripts/EXPERIMENT_two_call_synthesis.py` — the two-call architecture. Sections to **reuse**: `SYNTHESIS_TASK` (steps 1–2b are the strong parts — brainstorm, novelty filter, evidence-honesty filter); `TRANSIENT` + retry/resume logic. Sections to **drop**: `SPINE_ADDENDUM` (the whole "build essay + verse commentary around this spine" framing — that's the part we're replacing).
  - `scripts/EXPERIMENT_two_call_finalize.py` — clean reference for invoking the production downstream chain (print-ready, scripture verifier, copy editor, DOCX) with isolated paths. Useful template if a fresh integration test needs that.

- **The 3-way comparison DOCXs** (do not modify):
  - `output/psalm_55/THREE_WAY_COMPARISON/psalm55_guide_A.docx` — two-call scaled+guardrail
  - `output/psalm_55/THREE_WAY_COMPARISON/psalm55_guide_B.docx` — shipped one-call (the production baseline you're trying to *complement*, not replace)
  - `output/psalm_55/THREE_WAY_COMPARISON/psalm55_guide_C.docx` — two-call cap-3/4
  - `_MAPPING_KEY.md` — the mapping + full provenance

- **The empirical regression set** (the copy editor's flags on the scaled+guardrail Ps 55 run):
  - `output/psalm_55/EXPERIMENT_two_call/psalm_055_copy_edit_changes.md` — 32 corrections, each a concrete instance of an overclaim class the synthesis prompt should pre-empt. Use as the test set for the new evidence-honesty filter: any change in this file the new filter would have prevented is a win.

## Session 346 rule changes still in production

These are now in `src/agents/master_editor.py` `MASTER_WRITER_PROMPT_V4` and govern the *normal* one-call writer behaviour. Do not modify in Session 347 — they're the baseline the synthesis-discovery integration must respect:

- **RULE 7b: NO FALSE PROFUNDITY** (lines ~178–198) — names the dictionary-in-epigram / tautology-with-cadence / escalating-restatement / manufactured-frame failure modes, with BLOATED/CLEAN counter-examples (the מִסְתַּתֵּר and נְדָבָה examples from Ps 54).
- **RULE 8 carve-out** (lines ~205–210) — the remedy for an orphaned fact is to CUT it or state plainly, NEVER manufacture significance.
- **STAGE 3 Phrase coverage proportionality** (lines ~382–390) — three options now: (a) develop substantively, (b) one honest proportionate sentence, (c) deferral pointer. Coverage means visible, not inflated.

These were verified working in the Session 346 Ps 54 re-run — the original two examples (the מִסְתַּתֵּר reflexive paragraph; the נְדָבָה fortune-cookie chiasmus) are gone and stayed gone.

## A note on the eval prompt I wrote

The Session 346 eval prompt told evaluators the target reader *does not read Hebrew*. The user clarified at session end that the target reader *does* read Hebrew. Both Gemini reads still produced sensible Hebrew-handling judgments (and Gemini's hallucinated Hebrew error would have been disqualifying for either kind of reader), so the outcome wasn't materially affected — but the prompt is wrong. **For any future external evaluation of these guides, update the target-reader section to: *"reads Hebrew comfortably; appreciates philological precision; will notice when a root claim or vocalization is wrong."*** That's the version that should live wherever the eval prompt gets reused.

## One non-negotiable constraint for Session 347

**Do NOT change the production master writer's behaviour for normal `run_enhanced_pipeline.py 55` invocations (i.e., the flag-off path).** The shipped one-call writer was the favourite of one of three evaluators on its own merits, and the Session 346 rule changes (RULE 7b / RULE 8 carve-out / phrase coverage) need at least one cycle of broader validation before they're disturbed. The synthesis-discovery pass goes behind a flag, not into the default path, until two or three new psalms have been run with it and reviewed.
