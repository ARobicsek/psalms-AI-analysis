# Pipeline-Wide Review — More Novel AND Convincing Finds, Cost-Neutral

**Session:** 358 (2026-06-10)
**Brief:** `docs/plans/NEXT_SESSION_PROMPT_pipeline_novelty_review.md`
**Status:** DIAGNOSIS + RANKED PROPOSALS — nothing implemented. All claims below are
from reading the production code/prompts in this repo (cloud clone: no dossiers,
DBs, or published DOCX available, so output-level claims rely on the Session-357
record and are labeled as such).

---

## 0. Summary of the diagnosis

The pipeline's *generation* side is in good shape after Session 357: the synthesis
sidecar now hunts anomalies cross-source, the literary-echoes generator has a real
novelty engine (the "Second Echo Principle"), and the librarians supply grounded
reaching-outward facts. The weak links are now **selection and survival**:

1. **The Master Writer — the consolidation chokepoint — has a coverage mandate and
   no selection mandate.** Its prompt contains ~6 hard completeness requirements
   ("cover ALL verses," "EVERY liturgical reference," per-verse phrase coverage,
   per-verse figurative validation) and zero instructions to first identify the
   dossier's *best* finds and guarantee they get developed. The "aha" language is
   one sentence of mission statement; everything enforceable is breadth.
2. **The Copy Editor has no concept of flagged conjecture.** Session 357
   deliberately licensed hedged abductive claims ("perhaps…") end-to-end — but the
   one agent whose whole job is cutting unconvincing arguments was never told the
   convention exists. Its category 6 also directly contradicts the writer's
   mandated contrast-unfolding pattern for literary echoes.
3. **Deterministic plumbing silently drops paid-for gold**: macro's
   `poetic_devices` + `working_notes` reach no downstream agent; macro's research
   questions steer no retrieval; the concordance shows a *random* 10-hit sample
   that can exclude the very intertext the micro asked the search to confirm; the
   trimmer's first victim is the Related Psalms section (statistical intertexts —
   bridging material), and its figurative trim preferentially discards cross-book
   (reaching-outward) instances.

All high-ranked proposals below are prompt edits or deterministic plumbing —
NEUTRAL or SAVES. The recommended first move is a single A/B round on the two
chokepoints (writer selection mandate + copy-editor calibration rules).

### Per-step cost baseline (from IMPLEMENTATION_LOG, Sessions 339–352)

| Step | Model | Approx. $ / psalm |
|---|---|---|
| Macro | Opus 4.8 high | $0.36 |
| Micro + research assembly | Sonnet 4.6 (+ Figurative Curator GPT-5.4 high) | ~$1–1.5 |
| Literary Echoes (4-pass, regenerated per run) | Gemini 3.1 Pro ×2, GPT-5.4 ×2 | $0.94 |
| Synthesis-Discovery sidecar | Opus 4.8 high | ~$1.8–2 |
| Master Writer | Opus 4.8 (effort=max via S347 path) | ~$3.2 |
| Copy Editor | GPT-5.4 high | ~$0.5 |
| Scripture Verifier + GPT-5.1 filter | regex + GPT-5.1 | ~$0.04 |
| **Full run (Ps 59 reference)** | | **$6.81** |

---

## 1. Stage-by-stage walk: (a) does it CREATE novel+convincing material? (b) does it DROP/DILUTE it?

| Stage | (a) Creates? | (b) Drops/Dilutes? |
|---|---|---|
| **Macro** (Opus) | Yes — thesis, device-function analysis, working notes, 5–10 research questions (`macro_analyst.py:46-186`) | **Its own output is dropped downstream**: `poetic_devices` and `working_notes` reach nothing (writer/sidecar formatter `master_editor.py:558-577` includes only thesis/genre/context/structure/questions; `working_notes` excluded even from micro's view, `micro_analyst.py:535`). Research questions steer no retrieval (§3, H4). |
| **Micro** (Sonnet) | Yes — discovery-mode notes, lexical insights, interesting questions, and the structured research requests that steer all retrieval (`micro_analyst.py:73-381`) | Writer sees per-verse `commentary[:500]` (`master_editor.py:586`) — mild; micro is told to write dense fragments. Lexical-insight notes pass in full. |
| **Research assembly** (deterministic + Figurative Curator) | Yes — grounded intertexts; curator explicitly hunts "surprising patterns, absences, or INVERSIONS" (`figurative_curator.py:563`) | **Random 10-hit concordance display** can drop the requested seed intertext (`research_assembler.py:75,95-112,325-333`); English glosses stripped (S350); BDB entries cut at 500 chars, commentaries at 400 chars/language (`research_assembler.py:60-71,501,505`); related psalms capped 50K / top-5. |
| **research_trimmer** (350K cap, writer + sidecar) | — | When it fires, kills **Related Psalms first**, then figurative — and the figurative trim keeps Psalms-internal instances over cross-book ones (`research_trimmer.py:36-41,241-254`). Deep Research protected (good). Trigger frequency unknown (measure locally; dossiers run 200–320K, so it may fire rarely). |
| **Deep Research** (pre-paid file) | Yes — reception/afterlife facts the model can't recall | Protected from trimming. No issues found. |
| **Literary Echoes** (4-pass) | Yes — strong novelty engine: Second Echo Principle, banned-default list, diversity quotas (`docs/prompts_reference/literary echoes pass 1`) | Verify pass cuts only unverifiable *facts*, not bold-but-true finds (`pass 3.txt`: "Do NOT evaluate whether the comparisons are good"). Healthy. Sees only psalm text (deliberate independence — fine). |
| **Liturgical Librarian** (GPT-5.1 summaries over liturgy.db) | Partly — supplies the placement *facts* behind several published gems | Summary prompt is purely descriptive — WHERE/WHEN/HOW (`liturgical_librarian.py:910-1004,1429+`). It never asks "is this placement *surprising*? why THIS psalm THERE?" — the anomaly goes unlabeled, so writer/sidecar must rediscover it inside 300K chars. |
| **Synthesis-Discovery v2** (Opus) | Yes (S357, A/B-validated) — not re-litigated | Output is spliced into the writer as deliberately weak advisory input ("use where they fit; do NOT structure your commentary around them," `master_editor.py:862-877`). Right for structure; arguably over-meek for *selection* (§2, R1b). |
| **Master Writer** (Opus) | The prose, and consolidation-stage connections | **The central finding**: coverage crowds out selection (§2, R1). |
| **Copy Editor** (GPT-5.4) | — (convincingness guard) | Two pruning hazards for calibrated bold finds (§2, R2). Also adjudicates sound-pattern claims (category 3) with no phonetic data in hand. |
| **Scripture Verifier** | — | **Healthy.** Explicitly false-positive-aware: protects allusions, liturgical adaptations, deliberate partial quotes (`scripture_verifier.py:1144-1170,1189-1236`). Hypothesis 2 is KILLED for this stage. |

Orphan check: `insight_extractor` and `question_curator` are **already off by
default** (`run_enhanced_pipeline.py:291-292`, Session 280); `scholar_researcher`
and `synthesis_writer` are not called by either production runner. No live dead
steps to kill — the cheap SAVES are boilerplate, not whole stages.

---

## 2. Ranked recommendations

Ranking = impact × confidence ÷ effort. Cost labels per the brief.

---

### R1. Master Writer: add a "find the gold first" selection mandate — **NEUTRAL** — RANK 1

**Problem (evidence).** `MASTER_WRITER_PROMPT_V4` (`master_editor.py:38-526`) is
structurally a coverage contract:

- "**Completeness:** Cover ALL verses. No truncation." (line 383)
- "**Phrase coverage (CRITICAL — read this twice)**" + checklist enforcement
  (lines 384, 522) — every clause of every verse must be visibly handled.
- "You MUST incorporate EVERY specific liturgical reference" (line 405).
- Per-verse figurative validation: every verse with figurative language must cite
  ≥1 database parallel (lines 441-445, 518).
- A 12-item "items of interest" menu per verse (lines 386-439).

Against that, the novelty machinery is: one mission-statement clause ("genuine
'aha!' moments," line 40), the Translation Test (line 210 — a *floor* against
obviousness, not a selector for the best), and RULE 10 ("depth beats breadth,"
line 206 — scoped to choosing angles *within* a verse). **Nowhere is the writer
told to first rank the dossier's findings by surprise/explanatory power and
guarantee the best ones get developed.** The reasoning-phase instruction (line 46)
asks for argument planning, not a surprise inventory. This is precisely the
breadth-crowds-out-depth failure that motivated the synthesis sidecar — operating
at the consolidation chokepoint, where the published output is decided.

The sidecar's observations are then spliced with deliberately passive framing:
"use where they fit; do NOT structure your commentary around them… ADDITIONAL
INPUT" (lines 862-877). Correct for *structure* (S347 decision), but it gives the
writer no nudge to *prefer* a vetted top-tier observation over its own
hundredth-priority coverage obligation.

**Proposed change (prompt-only, both `master_editor.py` and `master_editor_si.py`):**

1. Add a short reasoning-phase step before outlining (mirrors the Synthesis
   Scholar's surprise inventory, reusing S357 vocabulary): *"GOLD INVENTORY: before
   outlining, list the 6–10 most surprising, explanatory, or connection-rich finds
   anywhere in your inputs — any source, any altitude (a placement anomaly, a
   reworked formula, an idiom avoided, a sound-driven word choice, a cross-source
   linkage). For each: where it will live (essay / which verse) or why you are
   consciously rejecting it. Your hook and your closing 'ONE thing' must come from
   this list. Coverage rules govern the floor of the commentary; this list governs
   its ceiling — a verse that hosts a gold find gets the depth budget, and routine
   phrases around it get exactly one plain sentence (RULE 7b/8 already permit
   this)."*
2. One added line in the splice block: *"Treat the observations below as
   candidates for your GOLD INVENTORY — weigh each against your own finds; adopt,
   demote, or reject deliberately rather than by omission."* (Keeps full authorial
   discretion; changes the default from drift to decision.)
3. Add one validation-checklist line: "GOLD INVENTORY: did each kept item land
   where you planned it?"

**Effect.** Novelty ↑ (best finds reliably developed instead of probabilistically
surviving breadth); convincingness ≈ flat (no license to overclaim is added; all
calibration rules untouched). **Confidence: HIGH** that the mandate is currently
absent (textual fact); MEDIUM-HIGH that adding it moves published novelty — this
is the same intervention shape that worked on the synthesizer in S357.

**Cheap test.** Writer-level prompt A/B on the S357 harness pattern:
byte-identical inputs via the `MasterEditorSI` loaders (the
`run_synthesis_ab.py` template generalizes — swap the agent call), Psalms 67/60/49,
1 run per arm (~$3.2 × 2 × 3 ≈ **$19**, or 2 psalms ≈ $13). Blind judge with the
`judge_synthesis_ab.py` rubric adapted to prose (count: distinct gold finds
developed ≥1 paragraph; coverage regressions; calibration violations).

---

### R2. Copy Editor: calibration-aware pruning rules — **NEUTRAL** — RANK 2

**Problem (evidence).** The system prompt (`copy_editor.py:50-233`) is broadly
well-designed ("Do not remove content that is merely debatable," line 52). Two
specific hazards for *calibrated, correct bold finds*:

1. **No flagged-conjecture concept.** Session 357 licensed hedged abductive
   claims end-to-end: the sidecar ships CONFIDENCE: CONJECTURE items, and the
   writer is instructed to render them as "perhaps / may explain" (splice block,
   `master_editor.py:870-875`). The copy editor was never told this convention
   exists. Its critical reading stance ("would this argument convince me? Can I
   follow each step…", lines 64-68) plus category 9(b) NON SEQUITUR and 9(c)
   STRAINED INTERTEXTUAL LOGIC give it every reason to treat a hedged abductive
   leap — whose *point* is that the evidence is suggestive, not demonstrative —
   as a reasoning gap to "fix." The S357 design says generate-boldly /
   verify-hard-downstream; downstream verification must verify *anchors and
   honesty of the hedge*, not delete the leap.
2. **Category 6 contradicts the writer's echo mandate.** The writer is required
   to unfold contrasts: "What differs, and what does the difference reveal about
   each poet's project?" (`master_editor.py:434`). The copy editor is told the
   opposite: "If the two contexts are so different that the comparison requires
   extensive qualification ('but where X does Y, the psalmist does Z'), the
   parallel is likely obscuring rather than illuminating" (lines 124-126) — that
   quoted pattern is literally the writer's instructed move. Upstream craft
   (generated by Gemini, web-verified by GPT-5.4, framed by Opus) can be cut by a
   sentence-level taxonomy collision.

**Proposed change (prompt-only).** Add to the system prompt:

- Under the reading stance: *"Distinguish DEMONSTRATION from CONJECTURE. A claim
  explicitly framed as conjecture ('perhaps,' 'may explain,' 'suggests,' 'is best
  read as') is NOT a reasoning error to fix or delete. For such claims verify only
  that (a) the facts it rests on are accurate and (b) the hedge is honest — do not
  de-hedge it, do not 'complete' its logic, do not remove it for being
  conjectural. Removing a correctly-hedged conjecture is itself an error."*
- Amend category 6: *"A developed contrast — where the DIFFERENCE between the two
  works is itself the insight — is a legitimate parallel; judge it by whether the
  shared element is specific (image, syntactic move, rhetorical structure), not by
  the amount of qualification. Remove only parallels whose shared element is a
  bare keyword or generic theme."*
- (From R9, optional) Append the psalm's phonetic transcription table as reference
  input so category-3 sound-claim adjudication is evidence-based in both
  directions (~2-4K input tokens ≈ $0.01).

**Effect.** Convincingness ↑ (fewer wrong cuts AND retained hedges stay honest —
the rule polices de-hedging too); novelty ↑ at the output (survival rate of bold
finds). **Confidence: HIGH** on the textual conflict; MEDIUM on frequency (we
could not diff published changes-files in the cloud clone — the test below
measures it).

**Cheap test.** Re-run the standalone copy editor (`scripts/run_copy_editor.py`)
on 2–3 already-written psalms with old vs. new prompt (~$0.5 × 2 × 3 = **$3**);
diff the `## Changes` logs for (i) conjecture deletions/de-hedges, (ii) echo
removals, (iii) any loosening on genuinely bad claims (regression check). The
existing `_pre_copy_edit` file pairs on your machine are a free retrospective
audit before spending anything.

---

### R3. Concordance display: purpose-aware pinning, not blind random sampling — **NEUTRAL** — RANK 3

**Problem (evidence).** Micro names the intertext a search is meant to confirm in
its `purpose` field — e.g. "PRIMARY root trace: wander/flee root from 'arḥiq
nedod' — Cain's נוד (Gen 4:16)" (`micro_analyst.py:361`). The assembler then
renders a **seeded random sample of 10** hits (`research_assembler.py:75,95-112`)
— purpose-blind. The named target verse can be sampled out, so the writer reads
"…and 37 more results (random spread shown)" while the one hit the search was
*for* sits invisible. The S350 gloss-stripping also means the 10 shown hits are
bare Hebrew lines with no hint of which ones matter.

**Proposed change (deterministic code, ~30 lines).** In `_sample_for_display`:
parse book/chapter/verse references out of the request's `purpose` +
`insight_notes`; **pin any matching results into the shown set**, fill the
remainder randomly as today. Optionally re-add the English gloss for pinned hits
only (2–3 lines/search — restores the targeted fraction of what S350 cut, ≈1-2%
of the 47% savings).

**Effect.** Novelty ↑ (intended intertexts reliably reach writer + sidecar — these
are exactly the "reaching-outward" anchors); convincingness ↑ (writer cites the
seed parallel instead of an accidental one). **Confidence: HIGH** (mechanical).

**Cheap test.** Zero-LLM: regenerate one research bundle locally, grep that each
purpose-named ref appears among shown hits; then eyeball one writer run already
scheduled for other tests.

---

### R4. Liturgical Librarian: ask the anomaly question — **NEUTRAL** — RANK 4

**Problem (evidence).** Both summary prompts (`liturgical_librarian.py:910-1004`
phrase-level; `1429+` full-psalm) request WHERE/WHEN/HOW in narrative prose —
nothing interpretive. Yet the published gems (per the S357 brief) come precisely
from *placement anomalies* (why THIS psalm before the Omer count? why reinserted
into Birkat Kohanim?). Today the anomaly must be rediscovered by the writer or
sidecar from a descriptive paragraph buried in a 300K-char dossier; the agent
closest to the data never labels it.

**Proposed change (prompt-only, same call).** Add one numbered requirement to
both prompts: *"9. FLAG THE NON-OBVIOUS. If the placement is not self-explanatory
— the psalm/phrase's plain sense does not obviously match the occasion, the rite
chose THIS psalm where several others would serve, or traditions diverge — say so
in one explicit sentence ('The choice of this psalm for X is not obvious: …') and
give the standard stated reason if one exists. Do NOT invent an explanation;
flagging the anomaly is the deliverable."* This is upstream-of-synthesis anomaly
*labeling* — it feeds the sidecar's surprise inventory (step 1 of the v2 prompt
explicitly hunts "a reception fact whose standard explanation feels thin") and
the writer's hook, at zero added calls.

**Effect.** Novelty ↑ (the highest-yield raw-material supplier starts marking its
own gold); convincingness neutral (facts unchanged; explanation explicitly *not*
invented). **Confidence: MEDIUM-HIGH.**

**Cheap test.** Re-run the liturgical summaries for 2–3 psalms with the new
prompt (GPT-5.1, cents) and check the flags against known cases (67's Omer
connection; 60's seal-verse custom).

---

### R5. Feed macro's `working_notes` + `poetic_devices` to the sidecar (and devices to the writer) — **NEUTRAL** — RANK 5

**Problem (evidence).** Macro (Opus, $0.36/psalm) produces device-function
analysis and "working notes — ambiguities, interpretive challenges… raw thinking"
(`macro_analyst.py:107-124` of the prompt). Consumers: **none**.
`_format_analysis_for_prompt` (`master_editor.py:558-577`) — used by BOTH the
writer and the sidecar (`master_editor.py:716`) — emits only thesis / genre /
context / structure / questions. `working_notes` is even excluded from micro's
view (`micro_analyst.py:535`, `include_working_notes=False`). The only consumer of
`poetic_devices` is the retired `synthesis_writer.py:1401`. Macro's
ambiguities-and-challenges are literally a pre-paid surprise inventory being
discarded at the door of the agent whose first step is building one.

**Proposed change (one formatter edit).** In `_format_analysis_for_prompt`
("macro" branch): append a compact `**Poetic Devices:**` list
(device/verses/function, one line each) and `**Analyst's Working Notes:**`
(verbatim). Adds roughly 1–2K tokens to two Opus calls ≈ $0.01–0.02/psalm —
within rounding, and more than offset by R7's boilerplate SAVES.

**Effect.** Novelty ↑ modestly (anomaly seeds reach the anomaly-hunter; device
functions reach the writer instead of being re-derived or lost). Convincingness
neutral-to-↑ (device claims originate from the high-effort pass instead of being
re-guessed). **Confidence: HIGH** that the drop exists; MEDIUM on yield size.

**Cheap test.** Free first look: print the formatter output for an existing macro
JSON and read what was being dropped. Then fold into the R1 writer A/B (same
runs, no extra cost) by including the enriched macro block in the B arm.

---

### R6. Route macro's research questions into the research-request stage — **NEUTRAL** — RANK 6

**Problem (evidence).** Macro's questions are titled "RESEARCH QUESTIONS FOR
PASS 2… that detailed verse-by-verse analysis should address" — but
`RESEARCH_REQUEST_PROMPT` receives **only** micro's Stage-1 discoveries
(`micro_analyst.py:208-212`); macro is "peripheral vision" for the discovery pass
only. So the questions steer zero retrieval; they surface again only as "Open
Questions" text in the writer/sidecar prompts. If macro asks "does the sevenfold
קול relate to creation theology?", no concordance search is guaranteed to exist
for it — the writer is invited to answer questions the librarians were never
asked.

**Proposed change (prompt-only, same Stage-2 call).** Inject macro's
`research_questions` into `RESEARCH_REQUEST_PROMPT` with: *"For each macro
research question answerable by lookup, ensure at least one targeted request
(lexicon / concordance / figurative / commentary) exists; tag it with the
question it serves. Do not exceed the existing request limits — fold these into
your quota, prioritizing them when in tension."* (Keeping the caps keeps cost
flat; the change is allocation, not volume.)

**Effect.** Novelty ↑ (research targets the structural puzzles, not only
verse-local curiosities — Opus-grade questions start pulling evidence);
convincingness ↑ (writer's answers to macro questions become grounded).
**Confidence: MEDIUM-HIGH.**

**Cheap test.** Regenerate micro Stage 2 for one psalm with/without the
injection (one Sonnet call, cents) and diff the request lists against the macro
questions.

---

### R7. Trimmer + bundle hygiene: cut boilerplate before gold; fix the figurative trim bias — **SAVES** — RANK 7

**Problem (evidence).** When `trim_bundle` fires (`research_trimmer.py:36-41`),
the order of sacrifice is: Related Psalms full texts → **Related Psalms entirely**
→ figurative to 75% → 50%. Related Psalms is the *statistical intertext* section —
the "diptych" material, a bridging-gold source. Meanwhile the bundle carries
known per-psalm boilerplate that is never trimmed: the ~250-word Sacks preamble
repeated every psalm (`sacks_librarian.py:191-198`), the Related-Psalms
instructional preamble ("Your task: Look for…", `related_psalms_librarian.py:221-232`
— writer guidance living in a data section), the commentator-roster header
(`research_assembler.py:490-492`), and the trimmer's own processing-summary
footer. The figurative ratio-trim also keeps Psalms-internal instances and drops
cross-book ones first (`research_trimmer.py:241-254`) — for reaching-outward
purposes this is backwards (the Deuteronomy/Job/Isaiah uses are what turn a gloss
into an intertext), and it ignores micro's explicit `priority_ranking`.

**Proposed change.**
1. New trim step 0: strip the boilerplate blocks above (pure SAVES, ~2-4K chars
   every psalm even when no trim fires — these are paid input tokens on two Opus
   calls; move the Related-Psalms guidance text into the writer prompt where it
   belongs).
2. Demote "remove Related Psalms entirely" to last resort (after figurative 50%);
   step 2 becomes "Related Psalms: keep relationship tables + top shared-root
   evidence for all 5, drop verse-context blocks."
3. Figurative trim: drop lowest-`priority_ranking` instances first; break ties
   *keeping* cross-book diversity rather than discarding it.
4. First, **measure**: log `original_size` for the last ~10 psalms locally
   (`psalm_NNN_research_bundle` file sizes) to learn how often >350K actually
   happens. If it's rare, items 2–3 are insurance and item 1 is still free money.

**Effect.** Novelty ↑ when trims fire (bridging material survives);
cost ↓ always (boilerplate). Convincingness neutral. **Confidence: HIGH** on
mechanics, MEDIUM on frequency-of-impact (hence the measurement step).

**Cheap test.** Zero-LLM: run the trimmer on saved bundles before/after and diff
what survives.

---

### R8. Misc SAVES to bank against the pennies spent above — **SAVES** — RANK 8

- **Literary echoes regeneration default.** Step 1b regenerates the full 4-pass
  workflow (~$0.94, ~10 min) on every non-resume run even when
  `data/literary_echoes/psalm_NNN_literary_echoes.txt` exists
  (`run_enhanced_pipeline.py:485`, `skip_if_exists=False`). If deliberate
  (freshness + exclusion-window rotation), keep; if not, flipping the default for
  existing files banks ~$1 on every rerun psalm. **Decision needed from author.**
- **Vestigial prompt scaffolding.** With insights/questions off by default, the
  writer prompt still ships the `KEY INSIGHTS TO INCORPORATE` input header and
  its checklist line when the insights file is absent (questions are stripped,
  insights are not — `master_editor.py:887-931` handles only questions). Strip
  symmetrically. Tiny, free.
- **Sidecar/writer double-read.** The sidecar reads the same 350K-char dossier as
  the writer (~$0.75 of its ~$1.9 is input). NOT proposing consolidation — the
  two-call separation is the S347/357 design and it works. Noted only to
  foreclose it as a future "optimization": the cheap wins above don't require it.

---

### R9. Give the Copy Editor the phonetic table (fold into R2) — **COSTS ~$0.01/psalm** — RANK 9

Category 3 (form/content confusion) requires the editor to judge whether "the
sound performs the meaning" claims are real, but its input is the finished prose
only — no transcriptions (`copy_editor.py:98-107`; pipeline passes just the
print-ready file, `run_enhanced_pipeline.py` step 5b). It is currently guessing
phonology from consonantal spelling — the exact failure the Phonetic Analyst
exists to prevent. Appending the per-verse transcription table (~2-4K tokens,
GPT-5.4 input ≈ $0.01) justifies its cost: it protects true sound-claims from
deletion (novelty survival) and catches false ones (convincingness) at once.

---

## 3. Hypothesis verdicts (from the brief)

| # | Hypothesis | Verdict |
|---|---|---|
| 1 | Master Writer is coverage-driven, no aha mandate | **CONFIRMED** — see R1 evidence. ~6 enforced completeness mandates vs. zero selection machinery; checklist polices breadth and style, never "did the best finds get developed." |
| 2 | Copy Editor / Scripture Verifier over-prune calibrated bold finds | **HALF-CONFIRMED.** Copy Editor: two concrete hazards (no conjecture concept; category-6 vs. writer-echo contradiction) — R2. Scripture Verifier: **killed** — its fix prompt and judge are explicitly false-positive-aware and protect allusion/adaptation/partial quotes. |
| 3 | Trimming throws away bridging gold | **CONFIRMED IN DESIGN, FREQUENCY UNKNOWN.** Priority order kills Related Psalms first and biases figurative cuts against cross-book instances; whether it fires at 350K on current dossiers needs a local measurement (R7). |
| 4 | "Specialists don't talk" tax | **CONFIRMED, THREE INSTANCES**: macro questions steer no retrieval (R6); macro devices/working-notes reach nobody (R5); liturgical anomalies unlabeled for the sidecar's surprise inventory (R4). Counterpoint: micro→librarians steering is real and good, and the curator's iterative loop is a working feedback example. |
| 5 | Redundant/near-zero-yield spend to reallocate | **MOSTLY ALREADY DONE** (insights/questions off since S280; synthesis_writer retired). Remaining: boilerplate (R7.1), echoes-regeneration default (R8), vestigial scaffolding (R8). No whole step worth killing. |
| 6 | Routing mismatches | **NONE COMPELLING.** Synthesis-critical work (macro, sidecar, writer) is all on Opus; GPT-5.1 on liturgical narration and citation filtering is appropriate; echoes Pass 3/4 on GPT-5.4 was forced by tested GPT-5.1 failures (S339). The leverage is in prompts/plumbing, not swaps. |
| 7 | Phonetics underused beyond the synthesizer | **MOSTLY RESOLVED BY S357.** Micro receives transcriptions; the sidecar has the sound-as-motive sweep; the writer has RULE 2 + items-of-interest #1. Remaining gaps: Copy Editor adjudicates sound claims blind (R9); Macro identifies "sound patterns" from unpointed text only (minor — micro re-checks with data). |

---

## 4. Recommended first move

**One A/B round on the two chokepoints, run locally (~$16–22 total):**

1. Implement R1 (writer gold-inventory mandate) + R5's macro enrichment as the
   B-arm writer prompt; A-arm = current prompt. Byte-identical dossiers via the
   `MasterEditorSI` loaders (S357 harness pattern). Psalms 67 and 60 (full
   dossiers, known gold: Omer/Birkat-Kohanim; seal-verse/Qere) + one
   never-run psalm as a no-prior-baseline control. ~$13–19.
2. In the same round, run R2's copy-editor prompt on both arms' outputs (~$3)
   and diff the changes-logs for conjecture/echo cuts.
3. Blind evaluation: author read + adapted `judge_synthesis_ab.py` rubric
   (novel finds developed; calibration violations; coverage regressions).

R3, R4, R6, R7 are independent, near-zero-cost, and testable without LLM spend or
for cents — they can land in the same session as the A/B implementation but
should be committed separately so the A/B isolates the writer/editor prompts.

**Decision points for the author:** (a) approve the A/B; (b) R8 echoes-regeneration
default — intentional freshness or rerun waste?; (c) whether R1's splice-block
nudge (item 2) goes in the same arm or a follow-up (it slightly couples the
sidecar's influence to the writer's selection — recommended together, since the
empirical S357 finding is that consolidation, not generation, is the bottleneck).
