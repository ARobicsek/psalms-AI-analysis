# Next-Session Prompt — Pipeline-wide review: more novel AND convincing finds, cost-neutral

> Paste the section below to a fresh session. Everything it needs to start is here;
> it should still read the cited files before proposing anything.

---

## Task

Review the **entire** Psalms commentary pipeline end to end and identify modifications that would increase the number of **novel AND convincing** insights in the *final published output* — **without increasing per-psalm cost**. Produce a prioritized, evidence-backed set of recommendations. **Do not implement anything this session** unless I approve a specific item; the deliverable is a diagnosis + ranked proposal (use plan mode / a written plan doc).

## What "novel AND convincing" means (both, not either)

- **Novel** = an "aha" a learned reader of Psalms hasn't already made: an anomaly explained, known facts newly linked, a reaching-outward connection (intertext / idiom / reception / sound-as-motive). NOT a restated source fact, NOT a dictionary gloss dressed up.
- **Convincing** = evidentially honest and calibrated: real anchors, claim strength matched to evidence, conjecture flagged as conjecture. A thrilling false claim is a failure; so is a true but inert one.
- These trade off. The goal is to move BOTH up at once, so favor changes that strengthen generation *and* calibration together, and be suspicious of anything that buys novelty with overreach (or safety with dullness).

## The hard constraint: cost-neutral

No increase in per-psalm \$. Treat these as **out of bounds**: adding new LLM passes/agents, enabling bigger thinking/effort budgets, upgrading a model purely for more spend, or widening token budgets. Treat these as **in bounds** (the interesting space): prompt changes; reallocating budget from low-yield to high-yield work; killing redundant or near-zero-yield steps and redirecting that spend; smarter trimming/prioritization of what existing material reaches the writer; net-neutral model-routing swaps; cheap routing/feedback that lets existing agents' outputs seed each other. For each proposal, label cost impact explicitly: **SAVES / NEUTRAL / COSTS** (anything COSTS must justify itself or be cut).

## Essential context from Session 357 (read these first)

- `docs/session_tracking/IMPLEMENTATION_LOG.md` (Session 357 entry at top) — the synthesis-discovery agent was just redesigned v1→v2 ("Synthesis Scholar"): abductive cross-source synthesis (TYPE P patterns + TYPE C connections), novelty-tested-on-the-linkage, flagged-conjecture licensed, aha/boredom audit, calibration intact. Validated by blind A/B. **Don't re-litigate the synthesizer** except to consider its interaction with the rest of the pipeline.
- `docs/plans/SYNTHESIS_SCHOLAR_PROMPT_V2_DRAFT.md` — the framework and vocabulary (surprise inventory → substrate → collision pass; "specialists who don't talk to each other"; generate-boldly-in-advisory-agents-verify-hard-downstream). Reuse this conceptual toolkit across the whole pipeline.
- `docs/architecture/TECHNICAL_ARCHITECTURE_SUMMARY.md` and `docs/HOW_THE_PSALMS_COMMENTARY_PIPELINE_WORKS.md` — full pipeline map.
- Key empirical finding to carry: the richest reaching-outward insights in the *published* guides come from the **Liturgical Librarian, Literary Echoes, and Deep Research, consolidated by the Master Writer** — not from any single "insight" step. Ps 67 (the best example) was published having run with the synthesis sidecar OFF. So **the Master Writer is the consolidation chokepoint**, and the upstream librarians are the raw-material suppliers. Weigh both.

## Scope — walk the whole chain and ask the same two questions at each stage

For every stage, ask: **(a) does it CREATE novel+convincing material?** and **(b) does it DROP or DILUTE such material that exists?** Stages: Macro (Opus) → Micro (Sonnet) → Research Assembly (concordance 4-layer, figurative librarian, lexicon, **research_trimmer** `max_chars`) → Deep Research (Gemini) → Literary Echoes (Gemini+GPT, 4-pass) → Liturgical Librarian (GPT-5.1) → Synthesis-Discovery sidecar (Opus, v2) → **Master Writer (Opus)** → Copy Editor (GPT-5.4) → Scripture Verifier. Pricing/routing as of S357 is in CLAUDE.md.

## Specific hypotheses worth testing (verify or kill each — don't assume)

1. **Master Writer mandate.** Read its prompt assembly (`src/agents/master_editor.py`, `master_editor_si.py`). Is it driven mainly by *coverage* (hit every verse/angle) rather than *selectivity for the best finds*? Does it have any explicit novelty/aha mandate, or does breadth crowd out depth (the very failure that motivated the synthesizer)? Cost-neutral lever: prompt rebalancing.
2. **Downstream over-pruning.** Do the Copy Editor and Scripture Verifier cut *calibrated, correct* bold finds as false positives (a convincing-killer that also wastes upstream craft)? Audit their prompts/taxonomies for hostility to flagged conjecture or to legitimately rare claims. Cost-neutral: prompt tuning.
3. **Trimming throws away bridging gold.** `research_trimmer.trim_bundle(max_chars=350000)` — what gets cut, and is high-value reaching-outward material (idiom usage, reception facts, intertexts) being trimmed before the writer/synthesizer ever sees it? Cost-neutral: re-prioritize what survives the trim.
4. **The "specialists don't talk" tax.** Macro's open-questions and micro's cruxes are anomaly-seeds; are they harvested anywhere downstream or wasted? Cheap feedback (e.g., macro questions steering research/micro emphasis; synthesis output informing the writer's selection) may be near-zero-cost and high-yield.
5. **Budget reallocation.** Any redundant or near-zero-yield steps whose spend could move to higher-yield generation? (e.g., overlapping research layers, low-hit concordance searches.) SAVES or NEUTRAL.
6. **Routing mismatches.** Any synthesis-critical work on a model too weak for it, or expensive reasoning spent where it doesn't pay — fixable with a net-neutral swap?
7. **Sound/phonetics underuse beyond the synthesizer** (a known gap I flagged): are the phonetic transcriptions used as explanatory evidence anywhere else they should be?

## Method & deliverable

- **Investigate before proposing.** Read the actual prompts and code; don't theorize from the architecture doc alone. Where useful, inspect real published output by extracting text from `Documents/Psalm study guide/*.docx` (zip → `word/document.xml`, strip tags — see how Session 357 did it).
- **Deliverable**: a findings doc under `docs/plans/` with, for each recommendation: the problem (with file/line evidence), the proposed change, **cost impact (SAVES/NEUTRAL/COSTS)**, expected effect on novelty vs. convincingness, confidence, and **how to test it cheaply** — ideally a prompt-only A/B reusing the Session-357 harness pattern (`scripts/run_synthesis_ab.py` + `scripts/judge_synthesis_ab.py` are the template for blind, byte-identical-input prompt A/Bs on *any* agent). Rank by (impact × confidence ÷ effort). End with a recommended first move.

## Environment note

In the cloud session the gitignored dossiers (`output/`, `data/`), databases, and API keys are **not present** — code/prompt investigation works fully, but any actual pipeline runs or A/Bs must happen on my local machine. Plan accordingly (design the tests; I'll run them).
