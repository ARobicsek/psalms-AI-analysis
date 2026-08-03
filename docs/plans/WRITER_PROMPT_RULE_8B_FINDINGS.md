# RULE 8b / RULE 3b-2 — Findings (Session 370, 2026-08-02)

**Read this before editing `RULE 8b`, `RULE 3b-2`, or the commentator-quoting instructions in
`src/agents/master_editor.py`.** It records the measurement that motivated them, the two live A/B
runs, and — most importantly — **an amendment that backfired**, so it is not retried.

---

## 1. The problem, as the author put it

> "Often in the verse by verse commentary, there are perhaps 5 points that are made, 3 of which are
> good, one of which is fine, and then one of which leaves me going 'why did you include this — it's
> obvious, boring, pointless.' Often but not always these humdrum points involve mechanically quoting
> a commentary that really adds nothing to a simple translation of the text."

Crucially the author also said: **"I DO want the verse by verse commentary to treat each word/phrase
at least briefly."** Any fix that buys concision by dropping coverage is the wrong fix.

## 2. The measurement (this is the load-bearing evidence)

Verse commentary only, Opus 5 vs Opus 4.8, **same dossier**, writer stage only:

| metric | Ps 71 ratio | Ps 70 ratio |
|---|---|---|
| words | 1.67× | 1.78× |
| **commentator citations** | **2.21×** | **2.62×** |
| LXX / Greek | 0.93× | 0.00× |
| Talmud / midrash | 1.17× | — |
| biblical cross-refs | 2.14× | 1.50× |

Commentator citation is the **only** category that outgrows overall expansion in *both* psalms, and
it is a **density** rise too (7.5 vs 5.7 per 1k words on Ps 71). Opus 5 used 47% of the dossier's 158
commentator entries; 4.8 used 22%.

**Opus 5 does not choose worse — it chooses more.** At Ps 71 v.14 it keeps Malbim's genuinely
interesting hope-in-tranquility reading *and* adds Rashi's bare paraphrase of the verse.

## 3. Why the old prompt produced it

Three compounding causes:

1. **The dossier is an unranked dump.** `commentary_mode="all"` (`micro_analyst.py`) requests all 7
   commentators on all verses — ~130 entries for Ps 71, 5.4 per verse — rendered uniformly with no
   quality signal. Much of it is running paraphrase *by design*: that is what a peshat commentary is.
2. **The prompt said take it, and never said leave it.** "Quote liberally … traditional commentaries"
   and "Engage … review and incorporate these materials", with no selection criterion anywhere.
3. **Every anti-padding rule was scoped to the writer's own prose.** RULE 7b hunts *sentences*;
   RULE 8 governs "observations" (a quotation doesn't read as one); RULE 11's translation test is
   trivially passed by a quote ("they wouldn't know Radak said it"). The floor was enforced per verse;
   the ceiling never per point. Meanwhile PHRASE COVERAGE creates demand — and the cheapest way to
   make a dull phrase *visible* is to quote the commentator who paraphrases it.

## 4. What shipped

- **RULE 8b — The Commentator's Burden.** One admission test: *does the reader read the verse
  differently than they did thirty seconds ago?* Cut by default. Five categories as illustrations,
  not a checklist. Apply the test to the **gloss**, not the framing verb. RULE 7b extended over the
  sentences around a quote. Never two commentators for one point. Two tiers, with failing the test
  meaning **silence, not demotion**. A ~1 Tier-1 quote per verse budget, used as a **ranking**
  instrument (rank across the whole psalm; protect Torah Temimah / Talmudic material; keep the
  insight and drop the citation without refilling the room).
- **RULE 3b-2 — Point, Don't Name.** Assume noun/verb/subject/object/tenses and nothing further.
  Bold the letters, or name them in words. No bare-predicate grammar. **Bolding does not license
  keeping the term.**
- **Beta reader `5b` / `5c`** — measurement only, no extra API call: `INERT CITATIONS: N` and
  `UNEXPLAINED GRAMMAR: N`.

## 5. The two runs

| | baseline | run 1 (rules v1) | run 2 (amended) |
|---|---|---|---|
| verse words | 9,994 | 8,251 (−17%) | 9,846 |
| commentator mentions | 75 | 34 | 42 |
| Tier-1 quotes / verse | 3.09 | 1.41 | 1.45 |
| redundancy markers | 8 | 2 | 2 |
| bolded Hebrew | 0 | 7 | 8 |
| `INERT CITATIONS` | — | **4** | **7** |
| `UNEXPLAINED GRAMMAR` | — | **10** | **6** |
| `LANDING` | near-miss | found | found |

All four author-flagged duds are gone in both runs.

## 6. ⚠️ THE AMENDMENT THAT BACKFIRED — do not reintroduce

Run 1 lost two first-rank citations (v.9's *evidential* old age; Doeg and Ahitophel). The fix added
ranking guidance — correct — **but also two permissive clauses**:

- *"Losing it to stay under budget is a worse outcome than going over."*
- *"Spend what you save."* (room recovered goes to other material)

**Result:** the guide re-expanded 19% back toward baseline and the beta reader's inert-citation count
rose **4 → 7**. Language added to *protect* quality instead relaxed the constraint — the same shape
as Session 368's copy-editor prompt fix, which also had to be reverted.

**What replaced them (currently in the prompt, UNVALIDATED):**

- "This is a SWAP, not an exemption… **The budget is a ceiling. Nothing in this rule licenses
  exceeding it.**"
- "**Keep the insight, drop the citation — and do NOT refill the room.** … the verse gets SHORTER."

The parts of the amendment that *worked* and should stay: rank across the whole psalm before cutting;
protect Torah Temimah / Talmudic material (this recovered Doeg and Ahitophel).

## 7. Methodology lesson — canary regexes must match the INSIGHT, not the attribution

My first scoring script keyed on the baseline's exact phrasing and cried "LOST" **four times** on
content that had survived, reworded:

- **v.4** — Malbim's palm-vs-hand citation dropped, but the observation kept and *improved*:
  `מִ**כַּ**ף, with the מ of "from" prefixed to כַּף, is the hollow of the palm`, plus a new Ps 18
  parallel. **This is the ideal outcome, and it scored as a loss.**
- **v.7** — richer in run 2 (Rashi quoted + Ibn Ezra + Radak, a true three-way split).
- **v.16** — Radak's battlefield reading quoted in full, as "might of the mighty men".

**The beta reader's independent `INERT CITATIONS` count is the trustworthy signal.** Pattern matching
against a prior arm's wording is not.

## 8. Open

- The third RULE 8b revision (§6) has **never been run**.
- `Psalm 71 (Opus 5) rev2.docx` is **run 2's** text — the permissive end of the range.
- Three Opus-5 prompt findings await an A/B/C test: delete the verification scaffolding (16 checklist
  items + 3 VALIDATION CHECK blocks + 6 "before finalizing"), flip the 2:1 negative example ratio to
  positive, add a conciseness instruction. See `NEXT_SESSION_PROMPT_session_371.md`.
