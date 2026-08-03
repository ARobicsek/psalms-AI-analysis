# Opus-5 writer-prompt A/B/C — Psalm 71 (Session 371, 2026-08-02)

Seven writer arms (base, A, B, C, B2, B3, B4), one model (`claude-opus-5`), one dossier,
writer stage only. Arms differ
**only** in the prompt. Harness: `scripts/ab_writer_prompts.py`, variants in
`scripts/writer_prompt_variants.py`, scoring in `scripts/score_prompt_ab.py`.

A **baseline** arm was run because A/B/C are deltas from the current prompt, which
carries the third RULE 8b revision that had never been executed. Without it every
delta would have been confounded against run 2 (a different prompt).

Total spend: **~$20.5** (7 writer runs ≈ $13.2 including one killed early, 6 beta reads
≈ $0.5, 6 finishing passes ≈ $5.2). Sections 1–4 cover the original four arms; 4b–4e
cover the later passes.

---

## 1. The arms

| arm | change | prompt Δ |
|---|---|---|
| `base` | current prompt, unchanged (validates RULE 8b rev3) | 0 |
| `A_no_scaffolding` | delete FINAL VALIDATION CHECKLIST (24 items) + 2 inline `VALIDATION CHECK` blocks | **−7,101** |
| `B_positive_examples` | add 6 `WORKED EXAMPLES` blocks (RULE 7, 7b, 8, 8b, 3b-2, affective landing) | **+7,325** |
| `C_conciseness` | add a sentence-level conciseness instruction to STYLISTIC GUIDANCE | +728 |

Arm A deliberately kept RULE 11, PHRASE COVERAGE, RULE 8b's "state the gloss flatly",
and the essay/commentary rule: those are phrased as questions but carry content stated
nowhere else, and phrase coverage is an explicit author requirement. A is therefore a
delete of **verification passes**, not of rules.

Arm B is **add-only** — no negative example was removed, since removing them would
conflate B with A.

---

## 2. Quantitative

Scored on RAW writer output (`psalm_*_full.md`), before copy edit. All metrics are
structural counts, never matches against a prior arm's wording (see
`WRITER_PROMPT_RULE_8B_FINDINGS.md` §7).

| metric | base | A | **B** | C |
|---|---|---|---|---|
| prompt Δchars | 0 | −7,101 | +7,325 | +728 |
| **verse words** | 9,507 | 10,759 (1.13×) | **8,507 (0.89×)** | 9,880 (1.04×) |
| words / verse | 396.1 | 448.3 | **354.5** | 411.7 |
| intro words | 1,971 | 2,257 | 2,111 | 2,301 |
| **INERT CITATIONS** | 7 | **6** | 7 | 7 |
| **UNEXPLAINED GRAMMAR** | 11 | 9 | **6** | 9 |
| **LANDING** | found | found | found | found |
| commentator mentions | 38 | 36 | 35 | 40 |
| Tier-1 quotes / verse | 1.00 | 1.21 | **1.00** | 1.17 |
| grammar terms named | 8 | 12 | 9 | 9 |
| bolded Hebrew | 8 | 6 | **9** | 5 |
| redundancy markers | 1 | 0 | 0 | 0 |
| quoted lines (echoes) | 27 | 31 | **25** | 35 |
| output tokens | 45,946 | 46,040 | **41,354** | 49,711 |
| cost | $2.18 | $2.17 | **$2.08** | $2.28 |
| seconds | 839 | 859 | **759** | 934 |
| beta wit score | 3/10 | 6/10 | 5/10 | 3/10 |

### Three headline results

**1. Arm C backfired — the conciseness instruction made the guide LONGER.**
+373 verse words, +8% output tokens, the slowest run, the most quoted lines (35), and
the most commentator mentions (40). The documented ~20% length reduction did not
replicate. This is the **third** consecutive instance of a prompt addition intended to
constrain instead relaxing the constraint — Session 368's copy-editor "burden of
proof" block, Session 370's RULE 8b permissive amendment, now this. The pattern is
strong enough to be a standing prior: **on this prompt, an added instruction about
restraint reliably buys length.**

**2. Arm A backfired on length but NOT on quality.**
Deleting the scaffolding cost +13% length and broke the Tier-1 budget (1.21/verse
against a ~1.00 ceiling — the checklist item enforcing it was among the 24 deleted).
But the "no capability regression" claim survived: `INERT CITATIONS` 7→6,
`UNEXPLAINED GRAMMAR` 11→9, `LANDING` still found, and the beta reader's wit score
went 3→6 despite the WIT checklist item being deleted. A is a genuine trade, not a
loss.

**3. Arm B won on every axis measured.**
The only arm to shorten (−1,000 verse words, −10.5%), the only arm to move
`UNEXPLAINED GRAMMAR` materially (11→6, −45%), Tier-1 exactly on budget, the most
bolded Hebrew, the cheapest, and the fastest. **It achieved this by making the prompt
7,325 characters LONGER** — the direct opposite of the shorter-prompt intuition, and
consistent with the guidance that Opus 5 rewards instruction density and that positive
examples outperform prohibitions.

---

## 3. Qualitative (beta reader §5 / §5b / §5c, four independent reads)

**base — unlocatable referents, and a metronome.** Its `UNEXPLAINED GRAMMAR: 11` is
almost entirely the failure RULE 3b-2 exists to prevent: *"The little letter at the
front of בְּצִדְקָתְךָ … which letter, exactly?"*; *"מָעוֹז becomes מָעוֹן … without
identifying which consonant changed"*; *"the guide asserts these are plurals, but a
reader has no way to see where the plural is."* Separately, the literary-comparator
move runs **seven times** — *"a clock you can set your watch by."*

**A — best structural variety, worst term discipline.** *"Largely free of template
feel, which is its main structural achievement."* It bolds correctly (the reader
explicitly clears v.2 and v.16: *"explained in the same breath; no flag needed"*), but
leans on **"completed tense" six times** without ever defining it, plus "causative
form," "finite verb," "strengthened stem." The extra 1,252 words bought range, not
padding.

**B — cleanest teaching, thinnest reach.** The 5c list is the shortest and mildest of
the four, and several entries are self-cancelling (*"this one is fine"*, *"clear"*,
*"no problem here"*). The cost shows up elsewhere: **four consecutive verses (13–16)
with no literary comparison at all**, and two visibly underdeveloped entries — v.17
(*"the slimmest entry in the whole commentary"*) and v.21, which the guide itself calls
*"the boldest request"* in the psalm while giving it one short paragraph. B bought its
10% by trimming the literary echoes (25 quoted lines, the fewest) as much as by
trimming commentary.

**C — the template the instruction was supposed to break.** *"The template becomes
visible at roughly verse 13 and runs through verse 16."* Smart at v.8 *"not tight
enough to earn seven lines of Jubilate Agno"*; the tziduk ha-din observation stated
twice. A conciseness instruction produced the most padded arm.

---

## 4. Pastiche check on arm B — and a flaw in my exemplar selection

Voice exemplars invite imitation; each block shipped with RULE 13's guard. Checked all
four arms for verbatim reuse of 21 exemplar phrases:

- **Cross-psalm exemplars (Pss 65–70): ZERO reuse in any arm.** "The theology lives in
  the cut," "Character here is appetite plus voice," "No foothold becomes a homeland,"
  "the favor lands as weather," "I have nothing, and I cannot wait," "the room is
  empty," "The suffix is the turn" — none appear anywhere. The guard held.
- **Ps 71-native exemplars: partial reuse, and this is my error.** A recount later gave
  **nine of twenty** (2 in RULE 8, 3 in RULE 8b, 3 in RULE 3b-2, 1 landing); my first
  report of "four" was wrong. They were mined from Psalm 71 itself — the psalm being tested. B reproduced two
  sentences verbatim that no other arm produced (*"modest work here and heavy work
  there"*, *"the grip has tightened while the sentence…"*). Two others
  (*"son of the grabber"*, *"the part that closes"*, *"a process, not an event"*)
  appear in arms with **no** exemplars at all, so those are dossier-driven, not copied.

**Consequence:** B's exemplar set was partly contaminated for this specific test psalm
— it was handed near-answers for two of its own verses. Two reused sentences cannot
explain a 1,000-word reduction, so the direction of the result stands, but the effect
size is not clean.

**Fix before adopting:** re-mine the Ps 71 exemplars from other psalms, and re-test on
a psalm none of the exemplars come from.

---

## 4b. PHRASE COVERAGE — B bought its concision partly from coverage

`scripts/check_phrase_coverage.py`, ground truth `tanakh.db`, consonantal-skeleton
match, prefixes stripped, the printed verse line excluded:

| arm | verse words | coverage |
|---|---|---|
| pre-RULE-8b baseline | 10,047 | 82.0% |
| C | 9,880 | 82.0% |
| run 2 | 9,846 | 80.3% |
| A | 10,759 | 79.2% |
| base | 9,507 | 77.6% |
| run 1 | 8,251 | 73.2% |
| Opus 4.8 | 6,060 | 73.2% |
| **B** | **8,507** | **69.9%** |

**B is the lowest of all eight arms ever measured on Psalm 71** — 7.7 points below its
own baseline, 14 more uncovered words out of 183. The beta reader found the same thing
independently and locally: v.17 *"the slimmest entry in the whole commentary"*, v.21
*"doesn't match the billing"*, four consecutive verses (13–16) with no literary
comparison.

This matters because coverage is the author's explicit requirement — *"I DO want the
verse by verse commentary to treat each word/phrase at least briefly"* — and a change
that buys concision by dropping coverage is by definition the wrong change.

**Metric caveats, both found by inspection and fixed mid-audit:** the checker
originally (i) let markdown bold split a word, penalising the RULE 3b-2 technique of
bolding a prefix — worst for whichever arm bolds most, which is B; and (ii) demanded
the prefixed form, so a guide discussing בְכִנּוֹר under the bare noun כִּנּוֹר scored a
miss. Both are fixed; the numbers above are post-fix, and B moved 61.7 → 63.9 → 69.9%
across the two corrections. The residual limitation is that this measures **Hebrew
re-quotation**, not conceptual treatment — a word glossed only in English scores as
uncovered. Absolute values therefore understate every arm equally; the *ranking* is
the finding.

## 4c. Second pass — arm B2 (three changes at once)

After the first four arms, three fixes went in: (i) the cross-verse observations
suppressors retuned in `master_editor.py` — the essay may now be built on the best
observation, and CONJECTURE hedging is scoped to the inference rather than the facts;
(ii) a **WORD-LEVEL FLOOR** added to PHRASE COVERAGE and the checklist; (iii) all nine
Ps 71-sourced exemplars replaced with material from Pss 65/67/69, since B had
reproduced two of them verbatim and this run is a Ps 71 deliverable.

(An intermediate version capped essay promotion at "at most ONE observation." That was
a suppressor reintroduced while removing one — only one idea can be a *spine*, which
STAGE 1 already governs, and a quota invites spending it on the first plausible
candidate. Caught before delivery; that run was killed ~3 minutes in and re-run.)

| | base | B | **B2** |
|---|---|---|---|
| word coverage | 77.6% | 69.9% | **78.1%** |
| UNEXPLAINED GRAMMAR | 11 | 6 | **5** |
| verse words | 9,507 | 8,507 | 9,853 |
| Tier-1 quotes / verse | 1.00 | 1.00 | **1.42** |
| grammar terms named | 8 | 9 | **7** |
| quoted lines (echoes) | 27 | 25 | 23 |
| cost / seconds | $2.18 / 839 | $2.08 / 759 | $2.48 / 1,066 |

**The word-level floor worked.** Coverage 69.9 → 78.1% (second-best arm, above
baseline) and `UNEXPLAINED GRAMMAR` = 5, the lowest recorded on this psalm.

**B's concision was lost, and the Tier-1 budget blew out to 1.42/verse** — the worst of
any arm. Likely cause, and a fourth instance of the standing pattern: B's "IDEAL CUT"
was a **concrete exemplar** (a real sentence showing an insight kept and its citation
dropped); because that sentence was Ps 71 material it had to be removed, and I replaced
it with an **abstract statement of the same principle**. Abstract restraint language
backfires on this prompt; demonstrations work. **Fix: source a real ideal-cut sentence
from a non-Ps-71 guide.** Note B2 changed three things at once, so the length rebound
cannot be cleanly attributed between the word floor and the lost exemplars.

**The essay promotion failed — and the suppressors were not the cause.** The anthology
idea is still 0 in the essay, 1 in the verse commentary. But B2's essay shows Opus 5
knows the fact and rejects the framing: *"What makes Psalm 71 more than a collection of
borrowed pieties is that the speaker accepts the terms of the argument and then reverses
its direction."* Opus 5 treats the anthological character as a deficit to defend
against; Opus 4.8 treated it as the design. **Across five Opus 5 runs (run 2, base, B,
C, B2) it has never chosen the compositional thesis**, consistently preferring the
lexical/legal one. This is a model preference, not a suppressed instruction. The
suppressor fix was still correct on its own terms — it just does not buy this essay.

**Implication:** the intervention that would actually produce the author's favourite
Ps 71 essay is a **split-model run — Opus 4.8 for the introduction, Opus 5 for the
verse commentary** — which is exactly what Sessions 367/368 concluded independently
("Opus 5 = better GUIDE, 4.8 = better ESSAY"). Untested; a bigger change than a prompt
tweak.

## 4d. Third and fourth passes — B3 and B4 (author-directed)

The author asked for two things: raise the word/phrase floor further, and kill weak /
boring / obvious / redundant citations. Ps 71-sourced exemplars were explicitly
permitted again at this point.

**B3 changes.** Production side: the floor became the **WORD-AND-PHRASE FLOOR** and now
names the three places words go dark, ranked — the verse's **last clause** (commonest),
a **word repeated** from an earlier verse (a gloss at v.5 does not cover v.17; a
four-word back-reference discharges it), and words **swallowed by a long quotation or
literary echo**. Plus *"if you are over length, cut a paragraph of analysis — never a
word's gloss."* B variant: the **concrete IDEAL CUT restored** (the מִ**כַּ**ף sentence),
a gallery of **four real failed quotations** caught by the independent reader, an
explicit count instruction, and a **worked example of a whole verse swept** (Ps 71:21 —
four words, four handled, unequal time but no silence).

The sharpest of the four failures, and the one worth keeping permanently: on v.2 the
guide quoted Metzudat David *"to listen to my prayer"* **having already written in its
own prose that there is nothing more to be had from it.** Hence the rule: *if you find
yourself writing that a gloss adds little, you have already completed the admission
test — delete the quotation. Do not print the verdict and the evidence together.*

| | base | B | B2 | **B3** |
|---|---|---|---|---|
| word coverage | 77.6% | 69.9% | 78.1% | **85.2%** |
| verse words | 9,507 | 8,507 | 9,853 | **9,101 (0.96×)** |
| bolded Hebrew | 8 | 9 | 8 | **12** |
| INERT CITATIONS | 7 | 7 | 7 | **8** |
| UNEXPLAINED GRAMMAR | 11 | 6 | 5 | 11 |
| commentator mentions | 38 | 35 | 41 | **44** |
| commentators / 1k words | 4.0 | 4.1 | 4.2 | **4.8** |
| Tier-1 / verse | 1.00 | 1.00 | 1.42 | 1.33 |

**Coverage goal achieved** — 85.2%, best of any arm by 3 points, reached while coming in
SHORTER than baseline. **Citation goal failed** — INERT 8, mentions 44, density 4.8, all
worst-ever.

**These are almost certainly the same event.** Strengthening coverage demand hands the
model a reason to reach for a commentator on every dull word — the channel
`WRITER_PROMPT_RULE_8B_FINDINGS.md` §3 named a session earlier: *"PHRASE COVERAGE creates
demand — and the cheapest way to make a dull phrase visible is to quote the commentator
who paraphrases it."* The beta reader's own top finding fits: Radak on v.2, where *"the
introduction stole this commentator's best moment; by the time we reach v.2 he's
repeating what the reader already knows"* — a citation filling a slot, not changing a
reading. `UNEXPLAINED GRAMMAR` reverting 5 → 11 fits too: more words touched briefly
means more terms named in passing.

**B4 — the decoupling fix (run at session end; SCORECARD NOT YET READ).** Both halves
are live in `master_editor.py`:
- Floor: **"COVER IN YOUR OWN WORDS — a commentator is never the instrument of
  coverage… Coverage is a translation duty, not a research duty."**
- RULE 8b: **"COVERAGE IS NEVER AN ADMISSION TICKET… If the only reason a gloss is in
  front of you is that its word needed covering, it fails this test by construction."**

Success criterion set in advance: coverage holds near 85% AND `INERT CITATIONS` drops
below 7 with Tier-1/verse back toward 1.0.

**RESULT — it failed both halves.** Beta counters came in after the structural scores:
`INERT CITATIONS: 7` (unchanged from baseline, so the fix bought nothing on the metric it
was written for), `UNEXPLAINED GRAMMAR: 12` (worst of any arm), `LANDING: found`.

| | base | B3 | **B4** |
|---|---|---|---|
| verse words | 9,507 | 9,101 | **8,413** (shortest of all seven arms) |
| word coverage | 77.6% | **85.2%** | **76.5%** |
| commentator mentions | 38 | 44 | **48** (worst) |
| commentators / 1k words | 4.0 | 4.8 | **5.7** (worst by a wide margin) |
| Tier-1 / verse | 1.00 | 1.33 | **1.42** (worst) |

Coverage fell back 8.7 points *and* citation density rose to its worst level yet — the
opposite of the intervention's purpose on both axes. The shape of the failure is
informative: the guide became the **shortest** of any arm while carrying the **most**
commentators. It appears the model cut its own coverage prose rather than its citations
— plausibly because *"coverage is a translation duty, not a research duty"* read as a
licence to do less covering, while the additional RULE 8b text raised commentator
salience again (the standing five-instance pattern, now arguably six).

**Therefore the §4d diagnosis is not established.** The prediction was that severing the
coverage→citation channel would hold coverage and drop citations; neither happened. Either
the channel is not the mechanism, or this wording attacked the wrong side of it. Do not
carry the diagnosis forward as settled — re-derive it. **B3 remains the best arm on
coverage and `Psalm 71 (final).docx` remains B3's text.**

## 4e. The affect audit (Session 371 close)

Prompted by the author: *"do we say enough about finding the pathos, wonder, humor?"*

| | Wit | Emotional impact |
|---|---|---|
| Opus 5 arms base / B / B2 / B3 / C | 3 / 5 / 3 / 3 / 3 | **7 / 8 / 7 / 7 / 7** |
| Opus 5 arm A | **6** | 7 |
| 4.8-era production Pss 65–68, 70 | 7, 7, 7, 7, 7 | 7, 7, 6, 6, 7 |

- **Pathos capped, not broken.** `LANDING: found` everywhere; `Emotional impact` is 7 in
  every single arm. The "exactly one landing" rule sets a ceiling. The author is
  explicitly sceptical of the cap.
- **Wit broken, Opus-5-specific.** Same RULE 13: 4.8 = 7, Opus 5 = 3. Not absence but
  register — *"eloquent and warm rather than deadpan."* Arm A (WIT checklist item
  deleted) scored 6, the only Opus 5 arm near 4.8.
- **Wonder unnamed.** And per the author's correction this means the **poet's** sense of
  wonder or other powerful emotion, NOT the reader's AHA. No rule, exemplar, or
  checklist item exists for it.

Full agenda in `NEXT_SESSION_PROMPT_session_372.md` (a).

## 5. Recommendation

1. **Adopt B only after fixing the coverage regression** — and swap out the four
   Ps 71-sourced exemplars. It is the only change that shortened the guide and the
   only one that moved the grammar counter, but it is also the worst arm on coverage
   ever measured, which disqualifies it as-is. The likely cause is that every RULE 8
   exemplar demonstrates *brevity* (one clause, a deferral pointer) and none
   demonstrates the *floor* — option (a), a phrase that genuinely rewards depth.
   Adding one or two "this phrase earned a paragraph" exemplars should restore it.
2. **Reject C.** The conciseness instruction is counter-productive on this prompt.
   Record it with the other two backfires; do not retry a restraint-shaped instruction
   without a mechanism for why this one would differ.
3. **A is a judgment call, not a clear win.** It improves quality signals and removes
   7,101 chars, but costs 13% length and breaks the Tier-1 budget. The untested
   candidate is **A+B combined** — B supplies positive instances of exactly what the
   deleted checklist items were policing, so B may pay for A's cost. That is the next
   single experiment worth running.
4. **RULE 8b rev3 (agenda item c) is validated as directionally right but weak.**
   Baseline 9,507 verse words vs run 2's 9,846 — the third revision recovered about
   3.4% of the 19% the permissive amendment gave away. It did not undo the rebound.

## 6. Deliverables

Four DOCX in `Documents/Psalm study guide/`:
`Psalm 71 (Baseline).docx`, `Psalm 71 (Arm A - no verification scaffolding).docx`,
`Psalm 71 (Arm B - positive exemplars).docx`, `Psalm 71 (Arm C - conciseness instruction).docx`.

Raw arms, beta reads, per-arm prompt templates, and `scorecard.md` in
`output/psalm_71/_prompt_ab/`.
