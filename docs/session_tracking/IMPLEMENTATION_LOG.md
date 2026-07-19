# Implementation Log

This file contains detailed session history for sessions 300 and later.

**Archived Sessions**:
- Sessions 1-149: [IMPLEMENTATION_LOG_sessions_1-149_2025-12-04.md](../archive/documentation_cleanup/IMPLEMENTATION_LOG_sessions_1-149_2025-12-04.md)
- Sessions 150-199: [IMPLEMENTATION_LOG_sessions_150-199_2026-01-12.md](../archive/documentation_cleanup/IMPLEMENTATION_LOG_sessions_150-199_2026-01-12.md)
- Sessions 241-299: [IMPLEMENTATION_LOG_sessions_241-299_2026-03-18.md](../archive/documentation_cleanup/IMPLEMENTATION_LOG_sessions_241-299_2026-03-18.md)

---

## Session 366 (2026-07-19): Divine-names converter — prefixed אֵל and three sibling misses

**Objective**: Author read the Ps 68 output and suspected the divine-names converter had missed instances of אֵל. Confirmed, root-caused, fixed four defects in the same family, and verified against the whole corpus. Spend: **$0** (deterministic; no model calls).

---

### The report, confirmed

Ps 68 shipped with **7 unconverted `הָאֵל`** — in `psalm_068_copy_edited.md`, `psalm_068_commentary.docx`, and both `Psalm 68 (OLD/NEW pipeline).docx`. The giveaway is v.21, where a single clause converts one El and not the other:

> הָאֵל לָנוּ **קֵל** לְמוֹשָׁעוֹת

Plus **1 unconverted `שַׁדַּי`** (v.15 discussion, in `אֲנִי־קֵל שַׁדַּי)` — El converted, Shaddai not, in the same phrase).

Corpus-wide scan: **44 prefixed-El misses across 17 psalm outputs** (Ps 42 ×8, Ps 68 ×7, Ps 57 ×5, Ps 69 ×4, then a tail of 1–2).

### Root cause (`src/utils/divine_names_modifier.py`)

`_modify_el_tzere` required whitespace/punctuation **immediately** before אֵ:

```
r'(^|[\s\-\u05BE*_.,;:!?...])אֵ([\u0591-\u05C7]*)ל(?=...)'
```

Any attached prefix letter therefore killed the match. Elohim has had a prefixed-forms rule since Session ~200 (Pattern 2b, `[ובכלמ]`); El never got the equivalent. `יִשְׂרָאֵל` was correctly untouched, which is why the gap survived so long — the pattern looked deliberately conservative.

### Four fixes

1. **Prefixed El** — new module-level `_PREFIX` allows up to two stacked prefix letters (ה/ו/ל/ב/כ/מ) with their own vowel/dagesh marks. The prefix must itself sit on a word boundary, so `יִשְׂרָאֵל`, `יוֹאֵל`, `מִיכָאֵל`, `גַּבְרִיאֵל`, `גֹּאֵל` stay untouched. Applied to both the base and the Eli (`אֵלִי`) patterns.
2. **Shaddai boundary class** — was `[\s\-־.,;:!?]` while El's included parens/quotes/markdown, so `שַׁדַּי)` never converted. Both now share one `_BOUNDARY` constant (also applied to the two doc comments and the `has_divine_names` detection patterns, which had drifted the same way).
3. **Trailing cantillation on the final letter** blocked the boundary lookahead — `אֶל־אֵל֮` (Ps 43:4), `גַּם־אֵל֮` (Ps 52:7). Lookahead now tolerates marks before the boundary; safe because real letters still block, and regex backtracking preserves the maqaf case.
4. **Two-letter prefixes** — `וְלָאֵל` (Ps 53).

Fixes 3–4 surfaced while verifying 1–2 and are the same defect the author reported, so they were folded in rather than deferred.

### Demonstrative guard (judgment call — flagged to author)

The corpus A/B caught a **real false positive the prefix fix would have introduced**, in Ps 30:

> וַיַּהֲפֹךְ אֶת הֶעָרִים **הָאֵל**, "He overturned those cities" (Gen 19:25)

That `הָאֵל` is the archaic plural demonstrative *"those"*, not the divine name — same consonants and vowels, no regex can separate them lexically. In **every** biblical instance (Gen 19:8, 19:25; Lev 18:27; Deut 4:42, 7:22, 19:11; 1 Chr 20:8) it follows the definite plural noun it modifies, which makes it guardable: `_is_archaic_demonstrative` skips conversion when the immediately preceding word is a definite plural noun (`ה…ים` / `ה…ות`, optionally carrying its own vav). "Immediately preceding" matters — checking anywhere earlier in the line misreads Hebrew quoted after English prose (verified against the Ps 30 line that quotes Ps 18:33 after a colon, which must still convert).

This is a heuristic on a genuinely ambiguous form. Revisit if it ever suppresses a real name.

### Verification

- **46-case suite** (scratch): all pass. Must-preserve cases include `אֵלַי`, `פְּנֵה־אֵלַי`, `אֵלֵךְ`, `הָאֵלֶּה`, `הַדְּבָרִים הָאֵלֶּה`, the angel names, `שָׂדָֽי` (SIN) and `שְׁדּי` (breasts).
- **Archived `test_divine_names_shin_sin.py`**: green. One expectation was stale — it asserted `וְאֵל שַׁדַּי` → `וְאֵל שַׁקַּי`, i.e. it encoded the bug. Updated to `וְקֵל שַׁקַּי`. (Run with `PYTHONPATH=.`.)
- **Corpus A/B**: loaded the HEAD modifier and the patched one side by side, ran both over all `output/psalm_*/psalm_*_copy_edited.md`. **37 word-level changes, all genuine divine names**; the Gen 19:25 demonstrative correctly preserved. Diffing against HEAD (not against the files) was necessary — older psalm finals predate the modifier being applied at this stage, so a naive file-vs-output diff conflates pre-existing behavior with the change.

### Deferred by author

**יָהּ** — the modifier has **no Yah rule at all**. 4 occurrences in Ps 68 alone, including `בְּיָהּ שְׁמוֹ` (v.5) and v.19. This is a design call rather than a regex bug: convention would be `קָהּ` or `י־ה`, and `הַלְלוּיָהּ` needs its own answer. Author chose to leave it.

### Not done — outputs not regenerated

The modifier runs at **DOCX-build time** on the edited markdown (`document_generator.py:1589`, plus the paragraph/table helpers), not at pipeline time. So Ps 68 and the 16 other affected psalms can be corrected by **re-rendering the DOCX at zero AI spend** — no pipeline re-run. Not yet done; offered to the author.

**Files changed**: `src/utils/divine_names_modifier.py` (+81/−24), `archive/development_scripts/root/test_divine_names_shin_sin.py` (1 stale expectation).

---

## Session 365 (2026-07-06): Related Psalms section — value audit, then doublet detection + noise-floor fixes

**Objective**: Author asked whether the "similar psalms" analysis (the `## Related Psalms Analysis` dossier section from `related_psalms_librarian.py`) is net raising or lowering final-guide quality. Audited 13 recent runs (Pss 55–68), then implemented the three approved fixes. Spend: **$0** (all deterministic + prompt edit).

**Audit findings (evidence in outputs/)**:
- **Section cost**: 0–23% of dossier chars (median ~8%; Ps 60 was 50.8K chars = 23.4%, truncated at the 50K cap; Ps 67 has no connections entry at all). Read by three paid models per run (GPT-5.4 synthesis, Opus SD sidecar, Opus writer).
- **Verdict: net positive but inefficient.** Of 38 librarian-suggested psalms, ~13 got any final-guide mention, and only some of those are librarian-attributable. All traced wins came from *distinctive* material (verbatim phrases, rare-root clusters); the low-IDF shared-root tail (קרא, שמע, אם, ולא…) — the bulk of every section — was used exactly zero times in 13 runs. No harm found: no guide ever adopted a spurious connection.
- **Gold case (Ps 66→81)**: librarian's cluster (רוע אל phrase, שמע…בקול skipgram, roots יכחש+בחן) → SD OBSERVATION 10 ("hearing vector reversed", anchored on "related-psalms section") → writer's v.19 paragraph → beta reader "LEANED IN… exactly the kind of intra-Psalter connection I can't get from footnotes" + cited in Freshness 9/10. Unavailable from any other source. Also real: 64→140 ("Psalm 140 supplies the snake"), 62→49; 65→74/36 produced two excellent SD observations the writer dropped.
- **Catastrophic miss (Ps 60→108)**: Ps 108 = Ps 57:8-12 + 60:7-14 nearly verbatim. The section spent 50.8K chars on this one connection (score 7454, eleven 6-word verbatim phrases) and **the production guide contains zero mention of Psalm 108** — no "doublet", no "reused", nothing; SD missed it too. Root cause: the format atomizes verse-level duplication into thousands of trivially-true matches and never states the conclusion. Same lesson as distributional facts: state computed conclusions, don't dump atoms.

**Fix 1 — deterministic doublet detection** (`related_psalms_librarian.py`): per related psalm, verses are aligned by consonantal token-set Jaccard (≥0.7; tokenizer splits maqaf, reads qere/drops ketiv per the distributional_facts convention; verses <4 tokens excluded so generic superscriptions can't match), then an iterative gap-fill extends runs to same-offset neighbors at ≥0.4 (mid-run redaction variants — e.g. 57:10//108:4 where אדני→יהוה — score 0.43–0.63 and are the *most* interesting verses). ≥2 pairs = **DOUBLET**: alert line in the preamble + a headline block with per-verse status and word-level diffs (difflib on consonantal keys, pointed text displayed), and the atom listings for that pair are suppressed entirely. A lone pair ≥0.8 gets a "Near-verbatim shared verse" flag above normal listings.
- **Verified**: 60↔108 full 8-verse run w/ variants surfaced (וְלִי↔לִי, הִתְרוֹעָעִי↔אֶתְרוֹעָע person shift, מָצוֹר↔מִבְצָר, dropped אַתָּה + plene בְּצִבְאוֹתֵינוּ↔בְּצִבְאֹתֵינוּ); 57↔108 offset run 57:8–12//108:2–6 incl. the Elohistic אדני↔יהוה diff; 53↔14 and 70↔40:14–18 caught bidirectionally; bonus legit catch 70:3//35:4. Zero false flags on 55/56/58/59/61/62/63/64/65/66/68.
- Ps 60's section: **50,758 → 3,451 chars (−93%)**.

**Fix 2 — noise floor**: shared roots keep full verse contexts only for the top `MAX_DETAILED_ROOTS = 10` by IDF; the common tail is named in one line ("*Also shared (17 more common roots, contexts omitted): …*") so clusters stay visible at ~2% of the cost. Skipgrams deliberately untouched — the audit initially proposed cutting 2-word skipgrams, but the 66→81 gold case *used* one (שמע…בקול); they're few and cheap. Section sizes across Pss 55–68: median −24% (57: −66%, 68: −60%, 55: −43%, 66: −34%); 66→81 cluster verified intact post-change. CLI `main()` also got the UTF-8 stdout fix (same as distributional_facts).

**Fix 3 — writer prompt** (`master_editor.py` item 9, Comparative Biblical Usage): psalm-level relationships (doublet / sustained mirror from distinctive shared vocabulary) declared first-rank material — name the psalm, quote the shared Hebrew, make the difference mean something; "a doublet flagged in the research but absent from the guide is a scholarship gap any reviewer would catch." Prompt 49,075 → 49,589 chars (+1.0%); SI inheritance verified (derives via `.replace` on an untouched anchor).

**Verification**: py_compile both files; e2e on the exact production call path (`format_for_research_bundle(psalm, matches, max_size_chars=50000)`) plus full-text mode for Pss 60/66 — doublet block present in both modes, no exceptions. No unit-test file exists for the librarian (none did before).

**Watch next production psalm**: whether SD/writer actually engage a doublet when one fires (next doublet psalms upcoming: 70/40 pair is far off; the flag also benefits reruns of 53/57/60/108), and whether the root-cap tail line ever needs to grow back to 12–15 if SD starts citing capped roots by name.

---

## Session 364 (2026-07-05): Local validation of Session-363 features — distributional facts vs real DB, wit-exemplar completion, beta-reader meta-evaluation

**Objective**: Execute `docs/plans/NEXT_SESSION_PROMPT_session_364_local_validation.md` (written by the Session-363 cloud instance): (1) smoke-test `distributional_facts.py` against the real tanakh.db; (2) read the last 7 finals and finish `voice_exemplars.md`; (3) run the beta reader on recent outputs and evaluate THE AGENT as an instrument. Spend: **$0.76** (9 beta reads); Tasks 1–2 free.

**Prompt-era map (established from git + mtimes; underpins everything below)**: The Session-359 wit/gloss prompt was committed 2026-06-21 09:39 (`4fb8da4`). Local production finals exist for Pss 61–67 (the cloud brief thought 61/62 existed only as compare outputs). **Pre-359 productions**: 67 (6/03), 61 (6/17), 62 (6/19). **Post-359 productions**: 63 (run started 09:42 on 6/21 — three minutes after the commit), 64 (6/23), 65 (6/27), 66 (7/03). The author-praised 61/62 wit lives in gitignored `output/psalm_6X/_writer_compare_new/`. ALL outputs predate the Session-363 affective-landing prompt → all are valid "before" baselines.

**Task 1 — Distributional facts: WORKS (+ two small fixes shipped)**:
- `database/tanakh.db` is the real DB (312,479 concordance rows); `data/tanakh.db` is the empty stub. Auto-search order finds the right one.
- Runs in **<1s per psalm** (vs the 60s worry threshold); blocks ~4.0K chars (in the 3–6K target).
- **Known facts confirmed**: פצמתה (Ps 60:4) and שבלול (Ps 58:9) flagged as unique forms; Ps 58 divine tally correctly catches the single YHWH in v.7; Ps 60 shows 0 YHWH (Elohistic). Ps 60:12's doubled אלהים explains the 5x-across-4-verses tally.
- **Signal check: real, not noise.** Ps 60's rare-form table lights up the Ps 108 doublet (6+ rows pointing at Ps 108); זנחתנו 2x (vv. 3, 12) is the published seal-verse catch; Ps 58 shows its famous hapax cluster (14 unique forms) and כמו 6x = the simile chain. These would have fed real published insights.
- **Fix 1 (cp1252)**: the CLI crashed printing Hebrew/≤ on Windows consoles — `__main__` now reconfigures stdout to UTF-8.
- **Fix 2 (ketiv/qere)**: the DB stores ketiv/qere as two adjacent bracketed tokens (`(ועננו)` `[וענני]`; 2,138 DB-wide), producing spurious "unique form" rows, fake ketiv→qere adjacent pairs, and undercounts. The module now reads the qere (drops the ketiv token, unwraps brackets) and corpus counts match plain + `[bracketed]` spellings together. Verified: Ps 60:7's qere וענני correctly rises to 6x and exits the rare table; אלהים 680→681 (a qere occurrence); freed cap seats surfaced 3 legit rare rows (יחלצון, ליראיך, מחקקי).
- Notes: the first/last-verse inclusio section rarely fires on superscripted psalms (v.1 = superscription; the repeated-forms table catches those cases, e.g. זנחתנו); superscription bigrams dominate Ps 60's pair table (header licenses discarding); no unit-test file for the module exists locally (the Session-363 test was a cloud-side throwaway). Sidecar splice activates automatically next pipeline run.

**Task 2 — voice_exemplars.md completed (all 5 known candidates verified verbatim + 12 new Tier-1 entries)**:
- All five Session-359 author-praised passages verified in situ in the compare outputs, quoted exactly with locations (Tier-1 #11–15): "Rank does not add a single gram"; "the lexicons throw up their hands ('text dubious,' says BDB)"; "Sanctuary-access is the estate God deeds to the landless"; "tomorrow, and the day after that"; + new find "Horace's emperor shines; the psalmist's king is merely kept."
- Post-359 productions 63–66 harvested (Tier-1 #16–22), best of session: **"There is no battle here, no equal cosmic rival, no narrative of war. There is a participle."** (Ps 65 v.8); "You cannot photograph an answered prayer. You can only be told." (Ps 66); "The shark at least shows its teeth. The slanderer, like Macheath, smiles." (Ps 64).
- **Wit density post-359 ≈ 4–7 genuine moments/guide vs ~1–2 in pre-359 productions 61/62** (67 is pre-359 but wit-positive — RULE 13 predates 359; the 359 complaint was specifically 61/62). **The "One does not…" mold appears in ZERO of the 61–67 outputs — the Session-359 deletion killed it.** New anti-pattern family flagged: essay-opening deadpan setup now has 4 members; a sampler should include at most one.
- The Amichai poem persists in compare-61 v.9 (baked into research_v2.md, exactly as Session 359 predicted — clears only when literary echoes regenerate).
- **Affective-landing near-miss baseline** (informal "before" data): 65 has the closest thing to a landing ("the relief of watching a force that has been crushing you change sides"); 61/63/66 close (Amichai close; Shamlou/Arendt close; Rachel Bluwstein "what is spent when suffering is made into shareable speech?"); 64/62 medium; **67 none** (cerebral throughout).

**Task 3 — Beta reader meta-evaluation (9 reads: Pss 61–67 productions + Ps 65 repeat + compare-62 via `--input-file`)**:

Baseline score table (the "before" numbers for the affective-landing feature):

| Psalm | Era | Engage | Clarity | Fresh | Wit | Emotional |
|---|---|---|---|---|---|---|
| 61 | pre-359 | 8 | 8 | 9 | 7 | 7 |
| 62 | pre-359 | 8 | 7 | 9 | 6 | 7 |
| 63 | post-359 | 8 | 8 | 9 | 6 | 7 |
| 64 | post-359 | 7 | 8 | 8 | 6 | 7 |
| 65 run1 | post-359 | 8 | 8 | 9 | 7 | 7 |
| 65 run2 | post-359 | 8 | 7 | 9 | 7 | 7 |
| 66 | post-359 | 8 | 8 | 9 | 7 | 7 |
| 67 | pre-359 | 8 | 8 | 9 | 7 | 6 |
| 62-compare | post-359 A/B | 8 | 9 | 9 | 6 | 7 |

Check-by-check against the brief's table:
- **Quote fidelity: PASS** (~30 quotes spot-verified across 7 reports; all verbatim except two word-level morphs — Ps 63 "asks"→"asked", Ps 62 "self"→"soul" inside quotation marks. No fabricated quotes).
- **Discrimination: FAIL at the score level.** Nine reads span Engagement 7–8, Clarity 7–9, Freshness 8–9, Wit 6–7, Emotional 6–7 — the classic clump. The "competent but forgettable = 5-6" anchor is not being used.
- **Known-contrast calibration: FAIL.** Pre-359 Wit (7, 6, 7) vs post-359 (6, 6, 7, 7) — no gap, if anything inverted. Decisive same-psalm test: **compare-62 (containing the author's favorite wit) scored Wit 6, identical to pre-359 production 62.** The reader's wit-quoting also diverges from the author's taste: it favors comparison-payoff lines and missed the flagship deadpans ("Rank does not add a single gram" unquoted in its own report; "You cannot photograph an answered prayer" unquoted) though it did catch "There is a participle" and "same eye, opposite emotional charge."
- **Affective-landing honesty: MIXED, threshold too permissive — but the detector tracks real material.** Found a "landing" in 8/9 reads; never used the licensed "Nothing moved me" (67 hedged: "close enough to count" — and 67 is exactly the guide my own read scored as having none; its EI 6 is also the only sub-7). Strong validity signal: **both readings of Psalm 62 — production and compare, different texts — independently picked the same insight as the landing** ("certainty migrates from outcome to ground"), and its picks match my own near-miss baseline in ~5/7 guides.
- **Sag-point plausibility: PASS.** Ps 61 v.6 re-treads-the-intro (agree); Ps 63 v.11 "traffic-jam of parallels" (agree); Ps 66 vv.11–15 "four literary comparisons in five verses" (exact and true); both Ps 65 runs agree on the v.6-area template feel + Purim Krovetz padding. It also caught real defects the pipeline missed: dangling JPS footnote markers "-a"/"-c" in Ps 64's psalm text, unglossed "precative perfect" (Ps 67 — a copy-editor category-10 leak), unglossed "Ugaritic" (Ps 61).
- **Stays in role: PASS with hairline exceptions** ("belongs in the introduction rather than buried here", "the setup could be tighter" — edit-flavored but framed as experience; no fix proposals).
- **Noise: PASS on scores** (repeat run: 4/5 dimensions identical, Clarity ±1). **Qualitative content is noisier**: the two Ps 65 runs picked different affective landings, and directly contradict each other on which literary comparison is weakest (run 1: Kafka weak/Du Fu good; run 2: Du Fu weak/Kafka good). Consistent with the Session-358 judge-noise finding: trust only what reproduces across runs/psalms.

**VERDICT: usable as-is as a PROSE instrument; do not use the scores to measure prompt-change deltas.** The reports' sag calls, confusion catches, and defect catches are specific, mostly reproducible, and match an independent close read; the five scores clump too tightly and failed the wit known-contrast, so they can serve only as a floor-alarm (a guide scoring 5s would mean something). For the affective-landing before/after, read the reports qualitatively: what passage it quotes and with what intensity language — require sign-consistency across two runs before trusting a delta. If the author wants to tighten the prompt (small edits, not growth): (i) harden the score anchor (e.g. "the median guide scores 5; justify every point above"); (ii) define Wit as RULE-13 deadpan (argument-carrying) vs warmth, ideally with 1–2 approved exemplars; (iii) require a machine-readable `LANDING: found / near-miss / none` line; (iv) explicitly ban edit-flavored phrasing. These are advisory — the agent already feeds nothing downstream.

**Files modified**: `src/concordance/distributional_facts.py` (UTF-8 CLI, ketiv/qere normalization + combined counting), `docs/prompts_reference/voice_exemplars.md` (Tier-1 #11–22, texture additions, anti-pattern status, provenance update). **Files created**: `output/psalm_6*/psalm_*_beta_read.md` (61–67). **Brief archived** to `docs/plans/archive/`. Minor observation for a future session: Ps 66's methodological summary shows "Psalm Verses Analyzed: 0 / LXX: 0 / Concordance: N/A" — a stats artifact worth a look.

**Part 2 (same day, author decisions): voice sampler WIRED + live writer A/B on Ps 66 ($1.47 + $0.09 beta read)**

- **Voice sampler wired** (`master_editor.py` RULE 13): the single Ps 48 "real-estate listing" gold example DELETED (one example = one mold to over-copy — the same failure mode as the Ps 52 example Session 359 removed) and replaced with six Tier-1 exemplars from the pipeline's own output, each annotated with its move, capped by an explicit anti-copy clause ("if a sentence of yours could be mistaken for a variation on one of these, cut it"). Net +621 chars (+1.3%, 48,082 → 48,703); propagates automatically to the SI prompt (verified by import). Final set: "keeps good books" (Ps 58) / "single gram" (62) / "There is a participle" (65) / "lexicons throw up their hands" (62) / "shark…Macheath smiles" (64) / "emperor shines…merely kept" (61).
- **Writer-only A/B on Ps 66** (via a corrected wrapper for the archived `compare_writer.py` — its self-computed ROOT broke after archiving; wrapper lives in the session scratchpad, not the repo). Opus 4.8, $1.47, output in gitignored `output/psalm_66/_writer_compare_new/`. Results:
  - **Affective landing: FIRED.** Both stages built the same landing (essay ¶: "the prayer bounce off the ceiling… Everything grand in the first half hangs on whether that one flat sentence is true"; v.19: "Strip away the craft for a moment… the fear that the room was empty, that no one was on the other end… The poet has spent nineteen verses earning the right to say it simply, and then says it simply."). Mild dilution artifact: the landing is duplicated across intro and v.19 with recycled imagery ("bounce off the ceiling" / "bounce back unheard") — Stage 1/Stage 2 don't see each other's prose. Watch whether the duplication recurs.
  - **Beta-reader cross-check ($0.09)**: its landing pick on the new guide = the engineered v.19 landing, quoted verbatim, with stronger intensity language than its production-66 report ("I felt recognized rather than instructed" vs "for a moment it felt like it mattered"). Feature fired AND the instrument detected it. Scores stayed flat (E8 C8 F9 W6 EI7) — re-confirming scores are deaf, prose is the readout.
  - **Human-mouth scene: inconclusive** — no new concrete use-scene appeared, but Ps 66's dossier appears to contain none to narrate (the feature is conditional on research content). Needs a psalm with known use-history for a real test.
  - **Sampler effects**: fresh wit in NEW molds ("This is liturgy quoting its own libretto"; "The musical rest is a runway"; "the psalm stages the maximalist gesture first, and lets the ethics catch up"; "a threat or a comfort depending entirely on whether you are a rebel or a sparrow"); zeugma glossed inline (RULE 3 visibly firing); no "One does not…". **Two phrase-level exemplar echoes**: (1) "You cannot see an answered prayer…" + v.16 "cannot be photographed… can only be *reported*" — exemplar #17's shape, but CONFOUNDED (that exemplar was mined from production 66 itself; the insight belongs to this psalm); (2) intro "no cosmic combat here, no equal rival" borrows #16's wording in service of a genuinely NEW observation (the enemies never receive a completed verb — no adversary finishes a verb in the whole psalm). Mitigation applied: **swapped exemplar #17 → the Ps 64 shark/Macheath line** — the photograph exemplar is topically about prayer, which recurs in most psalms, making it structurally the most parrot-prone of the six.
  - **Length**: verses −23% vs production (34.1KB vs 44.0KB). The cut fell almost entirely on literary echoes (≈10 → 5: Boito, Clytemnestra, McKay, Rachel Bluwstein, Lea Goldberg gone; Faiz Ahmad Faiz's *Subh-e-Azadi* and Nelly Sachs new). It thinned exactly the vv.11–15 comparison pile-up the beta reader flagged in production 66 — but also lost Rachel Bluwstein, production 66's affective highlight. Whether this is the texture rule working, the landing crowding out echoes, or run noise cannot be attributed from n=1. Watch length/echo-count on the next production psalm.
- **Beta-reader Q&A (author asked)**: it improves the writing only via the author (measurement-only by design — no revision loop); its per-run cost stays ~$0.08/psalm regardless of any prompt tightening, and any writer-prompt rewrites it motivates are ~free at run time.
- **State going forward**: the next production psalm runs with affective landing + human-mouth (363) + corrected distributional facts (364) + voice sampler (364 pt 2). Watch list: landing duplication across stages, exemplar echoes on non-66 psalms, echo-count/length drop.

**Part 3 (same day, author request): head-to-head OLD vs NEW pipeline on Psalm 68 (~$14.2 total)**

- **Design**: shared stages ran ONCE with current code (macro → 4-pass literary echoes → micro/research, 20:24–21:29, 36 verses, 386KB bundle — code for these stages unchanged between versions). OLD branch = git worktree at `6fd428f` (last pre-fable commit; the exact tree that produced Ps 66), seeded with the shared artifacts + echoes file, run with `--resume`; needed `.env` + `database/tanakh.db` copied in (untracked). Both branches ran their divergent halves in parallel (own sidecar → own writer → copy editor → citation check → DOCX; beta reader in NEW only). Costs: NEW full run $9.35 (incl. shared upstream), OLD branch $4.79, + $0.08 old-guide beta read. The archived `compare_writer.py` gotcha recurred in a new form: worktree needs untracked assets copied in; resume seeding works exactly as designed.
- **Deliverables**: `Documents/Psalm study guide/Psalm 68 (NEW pipeline).docx` + `Psalm 68 (OLD pipeline).docx` (from each branch's `psalm_068_commentary.docx`).
- **Findings (watch-list items from Part 2, now at n=2)**:
  - **Affective landing: FIRED, once, no duplication** (unlike the 66 A/B) — essay close: "If you have ever been the person without a place at anyone's table, this verse is doing something the storm cannot: it is turning the whole apparatus of cosmic power toward the one who has no one." Beta reader picked it verbatim: "The guide moved me here, and almost nowhere else — but once is enough to matter." OLD guide has no plain-landing equivalent (its most affective moment per its beta read: the Frances Harper reframe at v.32, analysis-embedded).
  - **Sampler echoes: ZERO on a non-66 psalm** — the anti-copy clause held; no "One does not…"; fresh wit in new molds ("The victory anthem ends by arming the congregation"; "Albright counted incipits; he missed the through-line"; "the size of a courtroom and a nursery"). Note: OLD guide independently wrote Albright "threw up his hands" — that idiom is native house style predating the sampler, but it is now ALSO in the prompt (exemplar #12), so it's double-primed; watch for over-use.
  - **Human-mouth: UNDER-FIRED (the one miss).** NEW renders Harper/Rastafari as reception analysis, and DROPPED the Huguenots-singing-at-Poitiers detail that the OLD writer used in its intro — scene-material was in the dossier and the feature didn't seize it. Neither guide narrates a full who/when/stakes scene. n=2 verdict on this feature: not yet observed firing; consider strengthening the #11 instruction or testing on a psalm with richer documented use-scenes.
  - **Distributional facts: visibly flowed through** — NEW sidecar makes exact-count claims ("occurs 2x in all Tanakh, both in this verse — a unique doubled form"); OLD sidecar argues from memory/tradition.
  - **Length**: NEW copy_edited 77.7KB vs OLD 85.9KB (−9.5% — within run noise; the 66 A/B's −23% did not recur).
  - **Beta scores**: OLD E8 C7 F9 W7 EI7 vs NEW E8 C7 F9 W7 **EI6** — identical except Emotional, where NEW scored LOWER despite its detected-and-praised landing. Final confirmation the score axis is unusable for deltas; the prose sections are the instrument.
  - **Both guides converge on the same thesis** (power redistributed downward; R. Yohanan's greatness/humility paradox; the עז arc) — the dossier drives the argument, the prompt drives the rendering. Both are strong; the differences are register-level, exactly where the features aim.
- **Cleanup pending author verdict**: worktree `../psalms_old_pipeline` retained for inspection (remove later with `git worktree remove ../psalms_old_pipeline --force`).

**Part 4 (session close, author-approved): three lessons-to-edits before finalizing the new pipeline**

1. **Landing dedup guard** (`master_editor.py`, One-affective-landing ¶, +~40 words): the writer is a SINGLE call producing essay+verses, so the Ps 66 duplication was an instruction gap, not architecture. Added: "One means one across the WHOLE guide: if the essay carries the landing, the corresponding verse's commentary may point at it in a single plain sentence with different imagery — never rebuild it."
2. **Human-mouth made a planning step** (`master_editor.py` items-of-interest #11, reworded): was passive ("when the research records…"), never fired in two live tests, and missed real material on Ps 68 (Huguenots/Poitiers in dossier, dropped). Now: "while planning, scan the liturgical and reception material for the single best documented scene… If one exists, narrate it… a passing clause ('the Huguenots sang it') is a missed scene, not a told one. If the research records none, skip without substitute."
3. **Beta reader tightened** (`beta_reader.py`, two edits): section 4 must end with a machine-readable `LANDING: found / near-miss / none` line ("found" reserved for genuinely moved; "interesting and well-made" = near-miss); Wit score redefined as DRY DEADPAN that carries the argument — warmth/eloquence/vivid images explicitly don't count (root cause of the failed wit known-contrast).

Writer prompt net across the whole session: 48,082 → 49,075 chars (+2.1%; sampler + dedup guard + #11 rewording). SI prompt inherits all edits (verified by import). Deliberately NOT changed: sampler set (2 clean live tests), distributional-facts tunables, anything length-related (variance is noise at n=2). Session total spend: ~$16.5 (meta-eval $0.76 + 66 A/B $1.56 + 68 head-to-head ~$14.2).

---

## Session 363 (2026-07-05): Engagement/insight upgrades — affective landing + human-mouth scenes (writer), computed distributional facts (sidecar), beta-reader agent, wit-exemplar mining

**Objective**: Follow-up to a quality review of the pipeline ("is the writing missing spark? are we fully exploiting LLMs for new insight? can guides be more engaging, insightful, moving?"). The author approved five items: (1) designate one affective landing per guide; (2) mine reception history for "the psalm in a human mouth"; (3) let the database do the counting the LLM does in its head; (4) a beta-reader evaluation (measurement, not another editor; <$0.30/psalm); (5) mine the most recent final outputs for wit exemplars. Explicitly REJECTED (author decision): the cross-psalm "insights ledger / book-ness" proposal — many readers read a single psalm's guide, not the collection, so guides must stay self-contained.

**1+2 — Writer prompt (`src/agents/master_editor.py`, `MASTER_WRITER_PROMPT_V4`, net +1,455 chars / +3.2%)**:
- **One affective landing** (new STYLISTIC GUIDANCE paragraph + one checklist line + CLOSING amendment): while planning, locate the psalm's emotional center of gravity; build ONE passage there where analysis stops carrying the sentences and the human point lands plainly — two or three sentences with no device named, no source cited, no cleverness — then return to work. RULE 7b still governs (no manufactured profundity); exactly one per guide ("spread it thinner and nothing lands"; checklist: "zero is a miss; two is a dilution"). The essay CLOSING now licenses the affective landing as the final takeaway where the material supports it (human recognition instead of scholarly point).
- **The Psalm in a Human Mouth** — items-of-interest #11 ("Historical & Cultural points of interest", a vague one-liner with typos) rewritten: when the research records a concrete scene of the psalm being *used* — a specific person/community praying, singing, quoting these words at a specific moment (deathbed, siege, Continental Congress, civil-rights march, German lied, R&B recording) — treat that scene as first-rank material, ahead of one more lexical parallel, and tell it AS a scene (who, when, what was at stake, the psalm's words quoted at the moment of use). Rationale: the liturgical/Deep-Research inputs already carry this material but it was being rendered as placement facts; narrated use is the most reliably moving material in the genre.
- Verified: SI prompt (`master_editor_si.py`) derives via `.replace` on the untouched "YOUR INPUTS" header, so both edits propagate; imports clean; all placeholders intact.

**3 — Computed distributional facts (`src/concordance/distributional_facts.py`, NEW, zero API cost)**: the sidecar's distributional sweep asked Opus to tabulate occurrences mentally — the one task where the LLM is weakest and the concordance table is exact. New deterministic module computes per psalm (consonantal level, read-only SQL over `tanakh.db`'s `concordance` table): (a) **rare forms** (≤5x in Tanakh, all other refs listed; "unique to this psalm" flagged); (b) **repeated forms** within the psalm with verse lists + Psalms/Tanakh counts (keyword/cluster candidates); (c) **first/last-verse shared forms** (computed inclusio candidates); (d) **rare adjacent word-pairs** (≤3x in Tanakh, other refs listed); (e) **divine-name tally** (YHWH vs Elohim forms by verse). Output is a compact markdown block (~3-6K chars, capped) with an honesty header: counts are exact for **forms**, not lemmas — "nowhere else" means unique consonantal string, verify against lexicon before claiming lexical hapax. Spliced into the Synthesis Scholar as a new input section `### COMPUTED DISTRIBUTIONAL FACTS` (`synthesis_discovery.py` gains a `computed_facts` param; the distributional-sweep bullet now says: start from this block, trust its counts over your memory, spend reasoning on which rows are load-bearing). Integration point: `MasterEditor.discover_cross_verse_observations` (covers both production runners). **Degrades gracefully**: returns "" when no populated tanakh.db exists (the cloud clone ships a stub — module was unit-tested against a synthetic DB exercising all five tables; NOT yet smoke-tested against the real local DB — do that next local run and eyeball the block for one psalm).

**4 — Beta Reader (`src/agents/beta_reader.py` + `scripts/run_beta_reader.py`, NEW; pipeline STEP 5d in both `run_enhanced_pipeline.py` and `run_si_pipeline.py`, ON by default, `--skip-beta-reader` / `--beta-model` flags)**: simulates the guide's target audience reading the FINISHED guide (copy_edited, fallback print_ready; methodological tail stripped) once, start to finish, and reports the reader **experience** in 8 fixed sections: reading experience narrative; engagement curve (LEANED IN / STEADY / SKIMMED per stretch); moments that landed (quoted, tagged AHA/WIT/FELT); the affective landing (did anything make you FEEL — "Nothing in this guide moved me" is explicitly licensed); sag points & template feel; confusion (only actual stumbles); 5 scores with calibration anchor ("competent but forgettable = 5-6"; parsed into `{dimension: int}` for future cross-psalm aggregation); verdict. **Measurement-only BY DESIGN**: proposes no edits, feeds no revision pass (revision loops flatten voice) — it exists to (a) tell the author whether goals 1-2 actually land and (b) surface systematic patterns (e.g. back-half sag) across psalms. Model: `claude-sonnet-4-6`, ~$0.08/psalm (~45K chars in / ~3K tokens out), non-fatal on failure. Output: `psalm_NNN_beta_read.md`.

**5 — Wit exemplars (`docs/prompts_reference/voice_exemplars.md`, NEW)**: mined every final guide reachable from the cloud session — Pss 58/59/60 production + all three Session-358 A/B rounds (12 documents, branch `claude/sweet-fermat-pje3t7`); Pss 61/62 (post-359 wit rule) exist only on the author's machine and should be added by hand. Yield: **10 Tier-1 sampler candidates** (each mapped to its RULE-13 move), e.g. "Psalm 58 carries, in its very first line, an instruction it spends the next eleven verses cheerfully ignoring"; "The oddly redundant 'in their mouth' — where else would teeth be?"; "Evil here is meticulous. It keeps good books."; "quietly files Saul's surveillance squad under the same heading as a global rebellion"; "A corpse instructs no one."; 6 Tier-2 voice/texture passages; and **anti-patterns**: the "One does not…" syntactic template recurs across independent runs (same mold Session 359 caught and deleted from the prompt — any future sampler must exclude it or the model re-anchors), the self-announcing pun ("war-song / war-*wound*"), cadence-exceeds-claim epigrams. The file is raw material for a possible future "voice sampler" prompt block (replace RULE-13 descriptive text, don't grow the prompt) — NOT wired into any prompt this session.

**Files created**: `src/concordance/distributional_facts.py`, `src/agents/beta_reader.py`, `scripts/run_beta_reader.py`, `docs/prompts_reference/voice_exemplars.md`. **Files modified**: `src/agents/master_editor.py` (prompt edits + distributional-facts splice in `discover_cross_verse_observations`), `src/agents/synthesis_discovery.py` (new input section + param), `scripts/run_enhanced_pipeline.py` + `scripts/run_si_pipeline.py` (STEP 5d + flags). All compile; unit tests passed (synthetic-DB distributional facts incl. degradation paths; beta-reader score parsing + file resolution; prompt formatting round-trips). Per-psalm cost delta: +~$0.08 (beta reader only; distributional facts are free).

**Next-session pointers**: (a) smoke-test `python -m src.concordance.distributional_facts 60` locally against the real tanakh.db (timing + eyeball the block); (b) run the beta reader retrospectively on already-published psalms to get a baseline score distribution before the affective-landing change ships output; (c) after Pss 61/62 passages are added, decide whether to wire the voice sampler into the writer prompt (as replacement, not growth); (d) the affective-landing + human-mouth edits are un-A/B'd — a writer-only rerun via `archive/development_scripts/compare_writer.py` on one psalm (~$1.3) would show whether they fire.

---

## Session 362 (2026-07-01): Sonnet 5 vs Sonnet 4.6 for the micro agent — investigated, live A/B on Ps 65, NOT adopted

**Objective**: Evaluate the cost (and, after a user concern, the quality) implications of moving the micro analyst (`src/agents/micro_analyst.py` — the pipeline's only Sonnet user; 2 LLM calls/psalm: Stage 1 discovery + Stage 2 research-request generation) from Sonnet 4.6 to the newly released Sonnet 5, assuming "high or greater" thinking.

**Pricing / API facts established**:
- Sonnet 5 = **$3/$15 per 1M standard**, but **$2/$10 intro through 2026-08-31**. Sonnet 4.6 = $3/$15.
- Sonnet 5's new tokenizer nominally emits ~30% more tokens for the same text, but this is an average — **empirically input was flat** (+0%) on Ps 65's Hebrew/Greek/structured-text prompt.
- **Two required migration breaks** (a bare model-string swap fails): (1) Stage 1's `thinking={"type":"enabled","budget_tokens":N}` (Session-294 "reserve 50% for JSON" safeguard) **400s on Sonnet 5** — must go `adaptive` + `output_config.effort`, with **no way to hard-cap thinking**; give extra `max_tokens` (used 128K) so thinking + JSON fit. (2) Stage 2 sends **no** `thinking` config → on 4.6 that means OFF, but on **Sonnet 5 omitting `thinking` defaults to adaptive-ON** (silent output-token cost) — must set `{"type":"disabled"}` explicitly.
- `effort` levels `low/medium/high/xhigh/max` are **coarse** — nothing between `xhigh` and `max`.

**A/B methodology**: Throwaway runner reused `output/psalm_65/psalm_065_macro.json` (only the micro stage differs), ran Stages 1–2 only (Stage 3 research assembly is not a Sonnet call — ~16 min + non-Sonnet cost, skipped), `commentary_mode="all"` to match the pipeline default, priced via a temporary `claude-sonnet-5` entry in `cost_tracker.py`. Baseline = the Sonnet 4.6 production run for Ps 65 (`psalm_065_cost.json` → `claude-sonnet-4-6`: 2 calls, 27,888 in / 45,758 out, **$0.770**).

**Results** (Ps 65 micro, cost intro / standard):
| | 4.6 (max, thinking capped 50%) | S5 `xhigh` | S5 `max` |
|---|--:|--:|--:|
| Output tokens | 45,758 | 27,753 (−39%) | 92,619 (+102%) |
| Cost | $0.770 | $0.333 / $0.500 (−57% / −35%) | $0.990 / $1.485 (+29% / +93%) |
| Lexical insights | 41 | 34 | 51 |
| Figurative / questions | 13 / 11 | – / 12 | 27 / 15 |
| Chars per insight | 510 | 288 | 269 |

- **`effort` is a 3.3× output-token lever** (mostly uncapped adaptive thinking): `xhigh` is cheaper but **genuinely thinner** than 4.6 (the user's concern); `max` restores/exceeds breadth (51 insights) but costs **more** than 4.6. **No setting is both cheaper and richer** — the session-start "Sonnet 5 is cheaper" thesis reverses at the density-preserving effort.

**Quality judgment** (manual, verses 2/4/10, S5 `max` vs 4.6): comparable; different profiles. Sonnet 5 **sharper on cross-verse connective insight** — the pipeline's highest-value axis — catching items 4.6 missed (v2 תְּהִלָּה/תְפִלָּה ה↔פ near-rhyme; v4→v7 גָּבְרוּ→גְּבוּרָה contrastive echo; v4 כפר-with-direct-object anomaly; v10 פֶּלֶג אֱלֹהִים superlative construction w/ Ps 80:11, 36:7). 4.6 **deeper per item** — more enumerated interpretive options (3 readings of דֻּמִיָּה vs 1), longer cross-ref chains (Ps 22/66/116). S5 = better *scout*, weaker *essayist*.

**Decision**: **NOT adopted.** No clean win. The `max` premium is tiny in absolute terms (+$0.22/psalm intro, +$0.71/psalm standard; ~$33–107 across all 150) and arguably feeds better raw material to the writer, but it is not the cost win that triggered the investigation. Untested levers for a future revisit: (a) a model-gated nudge to the shared `DISCOVERY_PASS_PROMPT` density block (Sonnet 5 follows length instructions literally, defaults terse) to get 4.6-level depth at `xhigh` cost; (b) full-pipeline DOCX diff + blind position-debiased judge (`evaluate_novelty_ab.py` pattern) instead of a manual read.

**Files**: `docs/plans/SONNET5_MICRO_AB_FINDINGS.md` created (full data + reproduction notes; pointer added to CLAUDE.md Reference Docs). **All code reverted from HEAD** — `src/agents/micro_analyst.py` and `src/utils/cost_tracker.py` byte-identical to session start (`MicroAnalystV2.DEFAULT_MODEL` still `claude-sonnet-4-6`); throwaway runner `archive/development_scripts/compare_micro_sonnet5.py` and A/B artifacts `output/psalm_65/_micro_compare_sonnet5/` removed. **No production code changed.**

**Reproduction gotcha**: `MicroAnalystV2` default `db_path="data/tanakh.db"` is wrong for standalone use — the populated DB is `database/tanakh.db` (87 MB). Passing the wrong path silently auto-creates an empty DB → "Psalm N not found."

---

## Session 361 (2026-06-28): Shimush Tehillim integration — systematic practical-Kabbalah coverage in liturgical section

**Objective**: Make Shimush Tehillim (שימוש תהלים) a standard part of the pipeline so every psalm's deep research covers its prescribed practical-Kabbalistic use and the Master Writer incorporates this into the liturgical section with speculation on why the psalm was selected for that purpose.

**Problems Identified**:
- Shimush Tehillim content was occasionally surfaced by Gemini Deep Research and incorporated beautifully by the Master Writer, but this was accidental — the deep research prompt didn't name the source, the writer didn't know the category existed, and zero of the 55 existing deep research files contained Shimush Tehillim content.

**Solutions Implemented**:
1. **Deep research prompt** (`docs/prompts_reference/deep_research_prompt.md`): Added ~22 words explicitly naming Shimush Tehillim in the "ritual and liturgical use" clause, asking what purpose the tradition assigns and why the psalm was selected. Zero cost impact (manual Gemini Deep Research mode).
2. **Master Writer prompt** (`src/agents/master_editor.py`, Stage 2 "Modern Jewish Liturgical Use"): Added 1 bullet (~55 words) instructing the writer to create a `#### Practical Kabbalah` subsection when Shimush Tehillim content is present in the research bundle. States the prescribed use, then speculates on WHY the psalm was selected — "what in its language, imagery, or traditional, creative or midrashic reading makes the association intelligible." Subsection omitted entirely when no content exists. Cost: ~$0.00075/psalm.
3. **Deep research README** (`data/deep_research/README.md`): Removed stale inline prompt copy (was divergent from the canonical `docs/prompts_reference/deep_research_prompt.md`), replaced with a pointer to the canonical file. Eliminates confusion from having two prompt versions.

**Design Decisions**:
- Shimush Tehillim placed within the existing "Modern Jewish Liturgical Use" section (not a new top-level section) because it's ritual use broadly and avoids structural changes to the DOCX output.
- Gets its own `#### Practical Kabbalah` subsection heading (not woven into prose) per user preference, but only when content exists.
- Tone left to writer's judgment — "speculate concisely on why" without prescribing a register. The writer has already handled this well when it discovered the material organically.
- Existing 55 deep research files left as-is — Shimush coverage will appear incrementally on future deep research runs.

**Files Modified**:
- `docs/prompts_reference/deep_research_prompt.md` — Added Shimush Tehillim to research areas (+22 words)
- `src/agents/master_editor.py` — Added Practical Kabbalah subsection guidance to Stage 2 (+1 bullet, ~55 words)
- `data/deep_research/README.md` — Removed stale inline prompt, pointed to canonical prompt file

**Files NOT Modified** (by design):
- No changes to Liturgical Librarian, macro/micro analysts, copy editor, synthesis writer, or DOCX generator
- No new agents, pipeline steps, scripts, or databases created

---

## Session 360 (2026-06-23): Pipeline cost-reduction review → "A1" dossier prompt-cache designed, cache-TTL blocker found, keepalive fix designed, SHELVED + documented

**Objective**: Review the production pipeline for ways to cut per-psalm cost without sacrificing quality (situations where a model generates output we don't use, or more input than we need to pay for); deliver a menu of options with savings and tradeoffs. User then picked "A1" (dossier prompt-caching) to implement.

**Findings (cost review, grounded in 3 recent cost JSONs — Pss 62/63/64)**:
- Per-psalm ~$6. Model split: **Opus 4.8 ~$2.61** (Macro + Synthesis Discovery + Master Writer, 3 calls), **GPT-5.4 ~$2.16** (Literary Echoes passes 3&4 + Copy Editor), **Sonnet 4.6 ~$0.64** (Micro), **Gemini 3.1 Pro ~$0.41** (Lit Echoes passes 1&2, thinking ≈ $0.3 of it), **GPT-5.1 ~$0.16** (citation false-positive filter).
- **Prime waste**: Synthesis Discovery and Master Writer each separately ingest the SAME ~130–180k-token dossier (psalm + macro + micro + ~215KB research bundle + phonetics + framework), and **prompt caching is entirely unused** (`cache_read_tokens`/`cache_write_tokens` = 0 in every cost file).
- Supporting facts: the `ResearchTrimmer` is a **no-op** (400k-char cap never trips on ~215k bundles → `research_v2.md` == `research_trimmed.md` byte-for-byte); the phonetic analyst is **algorithmic** (no API cost); insights/questions already skipped by default.
- Delivered a tiered menu: **A1** dossier caching (~$0.30–0.45); **A2** citation filter GPT-5.1→Haiku (~$0.05–0.15, ~16× cheaper, near-zero risk); **A3** reuse lit-echoes/synthesis on reruns (~$1.8/iteration); **B1** make trimmer bind / selective commentary; **B2** copy-editor 5.4→5.1; **B3** Gemini thinking-budget trim; **C1** Synthesis Discovery skip/downsize (~$1.0–1.3, measured-quality tradeoff).

**Problems Identified**:
- **A1 is EV-negative naively.** Anthropic prompt caching is prefix-based with a **300s (5-min) default TTL**; the cache is written at the *start* of Synthesis Discovery and read when the Master Writer *starts*, but the Writer only begins after Synthesis fully completes. Measured Synthesis durations (logs, last 8 production runs Pss 58–64) are **226–466s, with the current-prompt runs 61–64 consistently 303–330s — past the 300s TTL** → cache expires before the Writer reads it → Writer re-pays full price AND the 0.25× write premium is wasted (≈ break-even to −$0.16/psalm). 1-hour TTL also loses (2.0× write premium for a single read).

**Solutions Designed (NOT implemented — shelved by user)**:
1. **Keepalive fix (user's idea, validated against cache semantics)**: a cache *read* refreshes the TTL, so a cheap `max_tokens=1` "keepalive" ping of the dossier prefix, fired on a background thread *during* Synthesis (first ping ~120s in to avoid a double-write race, then ~every 250s), keeps the cache alive until the Writer reads it. Three calls (Synthesis = write, ping = read, Writer = read) share one byte-identical cached dossier block. Net **~$0.30–0.45/psalm**, reliable across 250–466s Synthesis durations.
2. **Shelved** over two user concerns, both documented: (a) prefix caching forces the dossier to LEAD the Master Writer prompt (a reorder of the heavily-tuned `MASTER_WRITER_PROMPT_V4` → small but real voice risk, would need a one-psalm A/B gate); (b) **model-swap fragility** — Anthropic caching only works when Synthesis and Writer run on the *same Claude model*; a future GPT writer (e.g. GPT-5.6) kills the mechanism entirely and leaves the reorder as dead weight. Recommended guard if revived: enable only when `sd_model == writer_model and is-Claude`, else fall back to today's path.

**Files Modified** (documentation only — no code touched):
- `docs/plans/DOSSIER_CACHE_KEEPALIVE_PLAN.md` — **NEW**: self-contained shelved plan (goal, the TTL blocker with measured durations, the keepalive fix + economics, implementation shape, validation gate, both shelving concerns, context snapshot).
- `CLAUDE.md` — session 359→360 + date; new Recent-Work entry at top (dropped Session 355); added a pointer to the plan doc in the "Reference Docs" list so it surfaces in the always-loaded index.
- `docs/session_tracking/IMPLEMENTATION_LOG.md` — this entry.

---

## Session 359 (2026-06-21): Master-editor voice — grammar-term glossing + gentle scholarly wit + texture variation; Amichai poem banned from literary echoes; live writer A/B on Pss 61–62

**Objective**: The two most recent published commentaries (Pss 61, 62) were excellent but the user flagged four issues: (1) they lean on grammar/rhetoric terms an average adult wouldn't know or remember from college English (e.g. Ps 62 "this single **vocative**"; Ps 61 "the **asyndeton** enacts what it means") without teaching them; (2) the prompt's wit guidance illustrated its target with a Ps 52 example ("one does not easily worship in the mode of X") that the writer then **reused nearly verbatim across psalms** — and even so the recent outputs had no wit at all; (3) the prose reads uniformly section-to-section and psalm-to-psalm; (4) Amichai's *God Has Pity on Kindergarten Children* is overused and keeps getting selected. **Hard constraint from the user**: do NOT increase the net length of the master-editor prompt (long prompts → inferior output).

**Changes — `src/agents/master_editor.py` (`MASTER_WRITER_PROMPT_V4`)** — net **+741 chars / +119 words after the first round, +1.2 KB / +1.7%** after the second wit round, offsetting additions against deletions/compressions throughout:
- **RULE 3** "DEFINE EVERY TECHNICAL TERM" → "**DEFINE — AND ILLUSTRATE** EVERY TECHNICAL TERM": explicitly names the ordinary-looking grammar/rhetoric terms readers half-recall (vocative, asyndeton, apposition, ellipsis, anaphora, litotes, hendiadys, zeugma) — not just Hebrew/scholarly labels — and requires a plain-language gloss *in the same breath* ("the single vocative — David stops talking *about* God and turns to address Him directly"). Reinforced by appending a grammar-gloss clause to the existing DINNER-PARTY REGISTER checklist line (no new bullet).
- **RULE 13 (wit)** reworked to the user's supplied register ("gentle erudite irreverence" of Johnson/Gibbon/Housman/Lewis) across two rounds. Round 1 added a "wit must grow out of THIS psalm; never carry a frame psalm-to-psalm" rule; the user then had me **delete it** (the writer has no cross-psalm memory, so it's not actionable, and it re-quoted the banned phrase). Final RULE 13: opening states the core mechanic (flat serious register while content does something quietly absurd; always underplays; never winks/telegraphs) + **three transferable moves** (punch inward at the scholar's own guild, not at the text; one homely concrete word over elaboration — Housman's "dog hunting for fleas," Keynes's "defunct economist"; must carry the argument). The over-copied **Ps 52 gold example deleted**; **the word "joke" purged from the entire prompt** (4 occurrences → "witticism"/"quip"/"the deadpan accuracy is what makes it land"); frequency loosened from "one or two per essay" to "a few genuine moments… wherever the material itself turns dry-funny," guardrails (never forced, never two per paragraph, no stand-up voice, no exclamation-point jokes) kept.
- **STYLISTIC GUIDANCE** gains a compact "**Vary your texture**" paragraph: vary sentence length/shape and explanation mode (a blunt sentence after a winding one, a question where you'd assert, a concrete scene instead of another abstract gloss), don't let every verse paragraph run one template — but **every verse section still opens with the verse's full Hebrew text** (per the user's explicit requirement), only *what follows* varies; never at the cost of clarity.
- **Token offsets** (to honor the no-growth constraint): deleted the redundant CROSS-CULTURAL ECHOES "BASICS" checklist line (subsumed by the CONTEXT line), compressed the CONTEXT / NO-FALSE-PROFUNDITY / PHRASE-COVERAGE checklist restatements, and trimmed a florid sentence in the RULE 13 preamble. Verified after every round: prompt still `.format()`s with all 9 named placeholders intact and the file parses (`ast.parse`).

**Changes — literary echoes** (`docs/prompts_reference/literary echoes pass 1 - tier override.txt`, `…pass 2 - tier override.txt`): **work-level ban** on Yehuda Amichai's *God Has Pity on Kindergarten Children* — added to the main FULLY-BANNED statement in both passes and to every checklist that lists banned authors. Amichai himself **remains an Earned-Canonical-Slot author** for his other poems; only this single poem is off-limits. The ban acts at literary-echoes generation only.

**Live writer-only A/B (user-requested, paid)**: re-ran ONLY the master-editor stage for Pss 62 then 61 on byte-identical existing upstream dossiers (macro/micro/research_v2/synthesis_discovery sidecar), `claude-opus-4-8`, via throwaway `compare_writer.py` (archived to `archive/development_scripts/`). New writer output written to gitignored `output/psalm_6X/_writer_compare_new/`; compared against the pristine `*_edited_*_pre_copy_edit.md`. Cost ~$1.34 (Ps 62) + ~$1.22 (Ps 61). Confirmed the live prompt carried all edits and zero "joke"/old-frame.
- **Goal 1 (glossing)**: Ps 62 "vocative" sentence now leads with the plain meaning ("the poet turns and speaks *to* Him… this single moment of **direct address**") and demotes the term to a tag; "hapax" now glossed inline ("a hapax — it occurs nowhere else"); Ps 61 essay renders יוֹם יוֹם in pure plain English ("no conjunction, no preposition, the bare daily beat") and reserves "asyndetic"+gloss for the detailed verse note. **Residual**: "vocative" still appears unglossed in quick literary-echo asides (Ps 61, 2×) — the rule is a reliable nudge, not a guarantee.
- **Goal 3 (wit)**: real, dry, unforced wit appeared where the old had none — "Rank does not add a single gram," "a fact worth stating plainly rather than padding" (self-implicating/guild-aware), "the lexicons throw up their hands ('text dubious,' says BDB)," "Sanctuary-access is the estate God deeds to the landless," closing "the word for it is *tomorrow, and the day after that*." No stand-up voice, no exclamation jokes.
- **Goal 4 (variation)**: distinct intro architectures across the two psalms; varied section heads and imperatives ("Listen to the opening," "Notice the sound"); blunt fragments against long sentences; added an O'Jays "Back Stabbers" (1972 soul) echo on Ps 62 v5 and a Badr Shakir al-Sayyab (Arabic) echo on Ps 61 vv.2–3 for register diversity. Length is run-to-run **noise** (Ps 62 −10% words, Ps 61 +13%) — not a prompt effect.
- **Amichai ban — expected non-effect in this test**: the new Ps 61 still quoted the banned poem (3×) because it is already embedded in the existing `research_v2.md`; the writer-prompt edits cannot remove what is baked into its inputs. To actually purge it for a psalm: regenerate literary echoes (`run_literary_echoes.py 61`) → re-assemble research → re-run the writer.

**Follow-on — copy-editor backstop (`src/agents/copy_editor.py`)**: the writer-only A/B showed RULE 3 is a strong nudge but leaks bare terms in quick asides ("vocative" 2× in Ps 61), so glossing was made a **two-pass guarantee** rather than a single-pass rule. Added a new, independent **category 10 (UNEXPLAINED TECHNICAL TERMS)** to the copy-editor taxonomy: an undefined grammar/rhetoric/literary term (vocative, asyndeton, polysyndeton, apposition, ellipsis, anaphora, epistrophe, litotes, hendiadys, zeugma, deixis, parataxis, enjambment, …) must, on first use, be (a) glossed inline in plain words (preferred light fix) or (b) replaced with the plain description and the label dropped. Guardrails: keep the surrounding insight (never just delete it), don't double-gloss (skip if glossed nearby or explained earlier in the same psalm — consistent with the existing "preserve definitions" rule), Hebrew stem names stay governed by category 8. Made "adding a brief gloss is a sanctioned exception to 'do not add material'" explicit in two places so the new rule doesn't fight the copy editor's minimal-intervention stance. Bookkeeping updated so `[10]`-tagged edits are tallied/reported (docstring 9→10-category; `_count_changes` range 1→1-10; `_print_summary` label added). Verified: file parses; the change-counter handles a `[10]` tag.

**Files modified**: `src/agents/master_editor.py`; `src/agents/copy_editor.py`; `docs/prompts_reference/literary echoes pass 1 - tier override.txt`; `docs/prompts_reference/literary echoes pass 2 - tier override.txt`. **Archived** (reusable): `archive/development_scripts/compare_writer.py` (writer-only A/B runner: `python … compare_writer.py <psalm>`). No production scripts created/changed. Comparison outputs left in gitignored `output/psalm_6X/_writer_compare_new/` for review.

**Lessons recorded**: (1) a writer-only A/B isolates writer-prompt changes but cannot reflect upstream prompt changes (literary-echoes bans, etc.) — the research bundle is already fixed; (2) prompt rules that presuppose memory the model doesn't have ("never reuse across psalms") are not actionable — target the lever (prefer psalm-specific over portable) instead; (3) re-quoting a banned phrase even as a negative example risks latch-on and wastes tokens — delete it; (4) glossing rules nudge strongly on flagged/headline cases but leak on quick asides — expect ~90%, not 100%, from a single pass; (5) for a leak-prone style rule, enforce it in two independent passes — the writer (RULE 3, first line) plus the copy editor (category 10, backstop) — rather than over-tightening one prompt.

---

## Session 358 (2026-06-10): Pipeline-wide novelty review → 3-round A/B → adoption (R2-R6 + sidecar v2.1 + baseline writer); LLM-judge position bias discovered

**Objective**: Per the Session-357 handoff brief (`docs/plans/NEXT_SESSION_PROMPT_pipeline_novelty_review.md`), walk the entire pipeline end to end and identify modifications that would increase **novel AND convincing** insights in the final published output without increasing per-psalm cost. Deliverable only — no production code or prompts changed.

**Deliverable**: `docs/plans/PIPELINE_NOVELTY_REVIEW_FINDINGS.md` — stage-by-stage create/drop audit, verdicts on the brief's 7 hypotheses, 9 ranked recommendations (each with file:line evidence, SAVES/NEUTRAL/COSTS label, expected novelty-vs-convincingness effect, confidence, and a cheap test), and a recommended first move (one local A/B round, ~$16–22).

**Key findings** (all from code/prompt reading; cloud clone had no dossiers/DBs/DOCX):
1. **Master Writer is coverage-driven with no selection mandate** (hypothesis 1 CONFIRMED). `MASTER_WRITER_PROMPT_V4` enforces ~6 completeness mandates (cover ALL verses; per-verse phrase coverage "read this twice"; "EVERY specific liturgical reference"; per-verse figurative validation) but contains zero machinery to first rank the dossier's best finds and guarantee they get developed. The sidecar splice is deliberately passive ("use where they fit"). → R1 (rank 1): add a reasoning-phase "GOLD INVENTORY" step mirroring the Synthesis Scholar's surprise inventory; hook + closing "ONE thing" must come from it. NEUTRAL.
2. **Copy Editor has no flagged-conjecture concept and contradicts the writer's echo mandate** (hypothesis 2 half-confirmed). S357 licensed CONJECTURE-flagged claims end-to-end, but `copy_editor.py`'s categories 9(b)/(c) can read a hedged abductive claim as a non-sequitur to "fix," and category 6 calls the writer's *instructed* contrast-unfolding pattern ("but where X does Y, the psalmist does Z") "likely obscuring." Scripture Verifier is healthy — explicitly false-positive-aware (hypothesis killed for that stage). → R2 (rank 2): conjecture-protection + category-6 amendment, prompt-only. NEUTRAL.
3. **Deterministic plumbing drops paid-for gold** (hypothesis 4 confirmed, three instances): macro's `poetic_devices` + `working_notes` reach NO downstream agent (`_format_analysis_for_prompt` emits only thesis/genre/context/structure/questions; only consumer of devices is the retired synthesis_writer); macro's research questions steer no retrieval (`RESEARCH_REQUEST_PROMPT` receives only micro Stage-1 discoveries); the concordance renders a purpose-blind seeded-random 10-hit sample that can exclude the very intertext micro's `purpose` field named (e.g. "Cain's נוד, Gen 4:16"). → R3/R5/R6, all NEUTRAL.
4. **Trimmer kills bridging material first** (hypothesis 3 confirmed in design, frequency unmeasured): Related Psalms (statistical intertexts) is the first full-section sacrifice; figurative ratio-trim keeps Psalms-internal instances and drops cross-book (reaching-outward) ones, ignoring micro's `priority_ranking`. Untouched boilerplate (Sacks preamble, Related-Psalms instructional preamble, commentator-roster headers) rides every bundle. → R7: strip boilerplate first (SAVES), reorder sacrifices, priority-aware figurative trim; measure >350K trigger frequency locally first.
5. **Liturgical Librarian summaries are purely descriptive** (WHERE/WHEN/HOW) — never flag a *surprising* placement, though placement anomalies are exactly where the published gems came from. → R4: one-sentence "FLAG THE NON-OBVIOUS" requirement, same call. NEUTRAL.
6. Hypotheses 5/6 (reallocation, routing): mostly already done (insights/questions off since S280; synthesis_writer retired; no compelling model swaps — echoes Pass 3/4 GPT-5.4 was forced by tested GPT-5.1 failures). Remaining SAVES: literary-echoes regenerates (~$0.94) on every non-resume run even when the file exists (`skip_if_exists=False` — author decision needed), vestigial KEY-INSIGHTS scaffolding when insights are skipped. Hypothesis 7 (phonetics): mostly resolved by S357; residual gap = Copy Editor adjudicates sound claims with no transcription data (R9, ~$0.01/psalm, justifies itself).

**Cost baseline assembled** (from S339–352 logs): macro $0.36, echoes $0.94, sidecar ~$1.9, writer ~$3.2, copy editor ~$0.5, citation filter ~$0.04; Ps 59 full run $6.81.

**Recommended first move**: one local A/B round — B-arm = R1 writer prompt (+R5 macro enrichment) vs. current, byte-identical dossiers via the S357 harness pattern, Pss 67/60 + one never-run control (~$13–19); R2 copy-editor prompt diffed on both arms' outputs (~$3); blind judging via adapted `judge_synthesis_ab.py` rubric. R3/R4/R6/R7 are independently testable for ~zero LLM cost.

**Part 2 (same session, user-approved): A/B implementation.** Findings doc + a new **`scripts/evaluate_novelty_ab.py`** (blind full-commentary judge + deterministic diff; OLD arm falls back to the published DOCX) committed to **`main`**. On branch **`claude/sweet-fermat-pje3t7`** only: implemented **R1–R6** — R1 GOLD-INVENTORY mandate in `MASTER_WRITER_PROMPT_V4` (+checklist line; splice block now frames sidecar observations as gold-inventory candidates; SI splice gains the missing S357 CONJECTURE sentence), R2 copy-editor flagged-conjecture protection + category-6 contrast rewrite, R3 purpose-aware concordance pinning (`_sample_for_display` pins purpose-named refs, `†`-marked), R4 "FLAG THE NON-OBVIOUS PLACEMENT" in all four liturgical summary prompts (4→4-7 sentences; QC accepts ≤7), R5 macro `poetic_devices`+`working_notes` passed through `_format_analysis_for_prompt` to writer+sidecar, R6 macro research questions injected into micro Stage-2 within existing quotas. Plus **`scripts/run_novelty_ab.py`** (re-runs Pss 58/59/60 through the unchanged production harness into `output/ab_novelty/psalm_N`, macro held constant from baseline, echoes file reused) and **`docs/plans/NOVELTY_AB_TEST_RUNBOOK.md`** (commands, design rationale, caveats — incl. that the published 58/59 baselines predate sidecar v2, with an optional main-arm control procedure). Verified: all files compile; R3 pinning unit-tested (extracts "Gen 4:16"-style refs, pins matching results, no-pin path unchanged); R1/R5/R2 asserted on the assembled prompts via stubbed-SDK import; question-strip `.replace()` anchors confirmed intact; runner dry-run OK. **To run locally**: `python scripts/run_novelty_ab.py 58 59 60` (~$17) then `python scripts/evaluate_novelty_ab.py 58 59 60` (~$3).

**Part 3 (same session): three A/B rounds, the position-bias discovery, and adoption.**

- **Round 1** (full R1–R6 chain on Pss 58/59/60 vs. published baselines, judged blind): OLD won 3–0 (best-5 margins −1.0/−1.0/−0.2). Forensics: every R fired (R3 `†` pins fed sidecar anchors; the R4 "not self-evident" flag on Perek Shirah produced the test's best single insight — the snail-hapax explanation); but in all three new arms the essay's spine was the sidecar's GOVERNING OBSERVATION adopted uncritically, and every overreach complaint traced to it — Ps 59's "the phonetics confirm" was inherited **verbatim** from the sidecar's governing claim (the splice's "keep its phrasing strength as you find it" locked the overclaim in); Ps 60's bow-genre hedge hardened into fact by the close.
- **Round 2** (writer-empowerment patch: re-rank/adapt/ignore + one-way calibration; copy-editor hedge-hardening check; writer-only rerun ~$3.7/psalm via new `--reuse-synthesis-discovery` flag): OLD won 3–0 again; the writer still anchored on the governing pick; **R1 falsified across two variants**. Free judge-noise measurement: the byte-identical OLD text's scores moved up to ±1.0 best-5 / ±4 gold between rounds.
- **Round 3** (user-approved redesign): **R1 fully reverted** (writer prompt byte-identical to baseline; thesis selection entirely the writer's call) + **sidecar v2.1** — (a) flat UNRANKED output ordered by primary verse, no GOVERNING/CORE/ADDITIONAL tiers ("selecting and weighting is the Master Writer's job"; the agent demonstrably ranks badly — it had found the judges' favorite ־מוֹ-badge observation in round 1 and tiered it ADDITIONAL); (b) additive DISTRIBUTIONAL sweep — tabulate psalm-suggested axes incl. CONSPICUOUS ABSENCES, explicitly a generator not a gate (qualitative TYPE P patterns exempt, per author's anti-overfitting concern); honesty filters untouched; extraction markers unchanged. Result: Ps 58 became a statistical tie with the new arm owning the strongest single insight in either text (the withheld-"I" / "lawsuit with no plaintiff," a NOV-5 absence-sweep product); 59/60 narrow OLD wins; overreach gap eliminated; spines moved off the strained picks.
- **Position-bias control (THE methodological finding)**: re-judging the identical round-3 files with presentation order reversed flipped all three verdicts — **the judge picked the second-presented commentary in 12 of 12 judgments across all rounds** (a fixed-seed shuffle had presented new-first every time). All single-order verdicts were dominated by position bias (~+1–2 best-5 points). **Position-debiased round 3 (mean of both orders): new +1.0 (Ps 58), tie (Ps 59), new +0.4 (Ps 60)** — parity-to-ahead, with the new configuration's consistent edge on bridging/reaching-outward gold (the axis the author's brief prioritized). Rounds 1–2's "losses" (old in the favored position all nine times) were likely near-ties; their content-level diagnoses remain valid.
- **Tooling**: `evaluate_novelty_ab.py --order both` is now the default — each psalm judged twice (old-first + new-first), report carries both passes plus a position-debiased synthesis (averaged metrics, per-order winners, AGREE/SPLIT flag, winner at ≥0.3 debiased best-5 margin else TIE). Single-order modes retained for cheap looks only.
- **ADOPTED TO MAIN** (user decision): R2 (copy-editor conjecture protection + category-6 contrast fix + hedge-hardening check), R3 (purpose-aware concordance pinning), R4 (liturgical non-obvious-placement flag), R5 (macro devices/working-notes pass-through), R6 (macro questions → micro Stage-2), sidecar v2.1, SI-splice conjecture drift fix, `--reuse-synthesis-discovery` pipeline flag, and both A/B tools (`run_novelty_ab.py`, `evaluate_novelty_ab.py`). **R1 reverted** (Master Writer prompt = pre-session baseline). Per-psalm cost unchanged. The A/B artifacts (rounds 1–3 outputs, judge reports) remain tracked on branch `claude/sweet-fermat-pje3t7` only; main's merge excludes `output/`.

**Files Modified** (net, as merged to main):
- `src/agents/synthesis_discovery.py` — v2.1 prompt: flat untiered output; distributional/absence sweep
- `src/agents/copy_editor.py` — flagged-conjecture protection; category-6 contrast rewrite; hedge-hardening pass
- `src/agents/research_assembler.py` — purpose-aware concordance display pinning (`†` + legend)
- `src/agents/liturgical_librarian.py` — "flag the non-obvious placement" in all four summary prompts
- `src/agents/micro_analyst.py` — macro research questions injected into Stage-2 request generation
- `src/agents/master_editor.py` — R5 macro `poetic_devices`/`working_notes` pass-through ONLY (writer prompt = baseline)
- `src/agents/master_editor_si.py` — SI splice gains the S357 CONJECTURE sentence (drift fix)
- `scripts/run_enhanced_pipeline.py` — `--reuse-synthesis-discovery` flag
- `scripts/run_novelty_ab.py` (new) — isolated-arm A/B pipeline runner (`--reuse-upstream`, `--regen-synthesis`)
- `scripts/evaluate_novelty_ab.py` (new) — position-debiased blind full-commentary judge (`--order both` default)
- `docs/plans/PIPELINE_NOVELTY_REVIEW_FINDINGS.md`, `docs/plans/NOVELTY_AB_TEST_RUNBOOK.md` (new) — diagnosis; full experimental record

**Lessons recorded for future sessions**: (1) single-order LLM-judge verdicts are unreliable — always judge both presentation orders and read sign-consistency, not margins (judge noise on identical text ≈ ±1.0 best-5, ±4 gold); (2) prompt-mandated selection ("gold inventory") underperformed the writer's native judgment two rounds running — prefer removing bad signals (tiers) over adding instructions; (3) salience labels from advisory agents are obeyed even when told otherwise — if an upstream agent ranks badly, strip the ranking rather than coach the consumer; (4) a fresh sidecar draw is stochastic (the ־מוֹ badge appeared in round 1, vanished in round 3) while a published baseline is a best-of-draw — single-draw-vs-fixed-text contests understate the live configuration.

---

## Session 357 (2026-06-10): Synthesis-discovery agent → v2 "Synthesis Scholar" (abductive cross-source synthesis), validated by blind A/B

**Objective**: Scrutinize whether the synthesis-discovery sidecar can produce deep, novel "aha" insights — the user's two Ps 67 exemplars: (1) the Priestly Blessing's third line (יִשָּׂא ה' פָּנָיו) is absent from the psalm's adaptation, perhaps because נשׂיאת פנים = favoritism clashes with a universalist psalm; (2) the psalm's Omer recitation is overdetermined (49 words AND a harvest ending) — and, if not, redesign it to do "original synthesis scholarship."

**Problems Identified**:
- The v1 prompt was **pattern-only**: its single organizing question ("what becomes visible holding ≥2 verses together") and its brainstorm menu were entirely text-internal. Both exemplar insights are **abductive explanations** (anomaly → best explanation; known facts whose *linkage* is new), often joining facts from different dossier sections plus a connecting concept from general scholarship — a class the prompt never requested.
- The **novelty filter tested constituents, not linkages**: any candidate containing a famous fact (e.g., "49 words = Omer") was cut, even when the novel part was the connection between famous facts.
- **Filter (g) banned the interpretive leap outright** ("perhaps the poet dropped X because of Y"), the exact move the deepest insights require.
- Empirical check of published DOCX output (Pss 67/60/49, extracted from `Documents/Psalm study guide/`): the reaching-outward insights in production came from the Liturgical Librarian, Literary Echoes, and Deep Research, woven by the Master Writer — Ps 67 (the richest example) had run with the sidecar **OFF** entirely, and its favoritism insight came from the user's Special Instruction file. The v1 sidecar was marginal.
- Pipeline underuses **phonetic transcriptions as explanations for lexical choice** (rhyme/near-rhyme, alliteration, sound enacting sense) — user note, folded into the redesign.

**Solutions Implemented**:
1. **v2 "Synthesis Scholar" prompt** (design doc `docs/plans/SYNTHESIS_SCHOLAR_PROMPT_V2_DRAFT.md`, now marked ADOPTED): two observation species — TYPE P (cross-verse patterns, v1's scope, kept) and TYPE C (cross-source connections); generation reworked to surprise inventory → per-source synthesis substrate → deliberate collision pass (incl. a sound-as-motive sweep over the phonetic transcriptions); novelty tested on the **linkage**, with explicit instruction that famous constituents don't disqualify; conjecture **licensed** if flagged CONJECTURE and explanatory (filter (g) rewritten from "ban the leap" to "ban the unmarked leap"); new aha/boredom audit (surprise / explanatory economy / hindsight-inevitability); output adds Type / Confidence (ESTABLISHED|PROBABLE|CONJECTURE) / Anchors-with-footing / Payoff fields. Evidence-honesty failure modes (a)-(j) kept intact; anchors must sit in dossier/text, connectors from training only at stake-it-in-print confidence. Extraction markers and placeholders unchanged → no downstream code changes needed.
2. **A/B harness**: `scripts/run_synthesis_ab.py` runs v1 and v2 over byte-identical Step-3.5 inputs (reuses `MasterEditorSI` loaders, `research_trimmer.trim_bundle(350000)`, `RAGManager`, and the agent's `_stream_call`), with an up-front Special-Instruction contamination scan (code audit confirmed the SI never reaches the synthesizer — it's passed only to the Master Writer — so the only leak vector is dossier data; Ps 67 scan: favoritism interpretation NOT in dossier, omission not even mentioned → canary fully valid; the scan's verdict line was a false positive on generic "particularism" vocabulary). `scripts/synthesis_ab_prompts.py` preserves the as-tested v2 verbatim. `scripts/judge_synthesis_ab.py` adds a blind LLM judge (shuffled Set A/B, per-observation rubric: linkage novelty / aha / economy / groundedness, INTERNAL-vs-BRIDGING + KEEP/CUT tags, canary checks, best-3-mean comparison) — built but not needed this session.
3. **A/B results** (user ran locally on Pss 67/60/49, both arms `claude-opus-4-8`, ~$12; results reviewed qualitatively file-by-file): **v2 decisively better.** It retained v1-grade pattern quality where the arms overlapped (Ps 49 פדה/לקח hinge, Ps 60 Edom-in-three-registers, צ-ר knot ≈ equal) and added genuine TYPE C finds v1 structurally cannot make: Ps 49 Korahites-from-Sheol ↔ house-of-mourning custom (explicitly framed as a second, psalm-specific support — the user's overdetermination move, unprompted); Ps 49 Shekalim ↔ כֹּפֶר נֶפֶשׁ of Ex 30:12 verbatim-denied in v.8; Ps 60 post-Amidah seal-verse custom as a reception-historical vote for the Qere וַעֲנֵנִי; Ps 60 Shushan-Purim overdetermined (title שׁוּשַׁן + body עִיר מָצוֹר); Ps 67 psalm-reinserted-into-Birkat-Kohanim; plus an independent fact-check catching the dossier's "sevenfold Elohim" claim (recount = 6, verified correct). Calibration held — all leaps flagged CONJECTURE, root-distinctness caveats unprompted. **Canary results**: favoritism-omission MISSED by both arms (dossier never quotes Num 6 in full; v2 caught the *altered* preposition but not the *absent* line); Omer canary engaged but contrarian (argued autumn-harvest Sitz ≠ spring Omer season → "the arithmetic, not the agronomy, won the slot").
4. **Adoption**: v2 pasted into `src/agents/synthesis_discovery.py` (programmatically from the as-tested module, byte-identical + one post-A/B strengthening targeting the missed canary: when a psalm reworks a known source formula, **reconstruct the source in full and diff it — list what is altered AND what is entirely absent**). Module docstring + prompt-block comment rewritten. Master Writer splice (`master_editor.py` `_perform_writer_synthesis`) now instructs: observations marked CONJECTURE must be rendered as conjecture in prose. All files compile; production constants verified to format with the agent's exact call-site fields, markers intact.

**Files Modified**:
- `src/agents/synthesis_discovery.py` - v2 "Synthesis Scholar" prompt (INPUTS_HEADER + SYNTHESIS_TASK), new docstring/comments; agent machinery untouched
- `src/agents/master_editor.py` - CONJECTURE-rendering caveat added to the cross-verse observations splice block
- `scripts/run_synthesis_ab.py` - NEW: v1-vs-v2 A/B harness (byte-identical inputs, SI contamination scan; supports non-padded `output/psalm_N` dirs)
- `scripts/synthesis_ab_prompts.py` - NEW: as-tested v2 prompt preserved verbatim for A/B reproducibility (docstring marks ADOPTED status + the production delta)
- `scripts/judge_synthesis_ab.py` - NEW: blind LLM judge with rubric, canaries, cross-psalm summary
- `docs/plans/SYNTHESIS_SCHOLAR_PROMPT_V2_DRAFT.md` - NEW: full design doc (v2 prompt text, v1→v2 change map, A/B spec) — status ADOPTED
- `CLAUDE.md`, `docs/session_tracking/scriptReferences.md` - session docs

**Notes**: A/B artifacts (`output/ab_synthesis/*`) were force-committed on the feature branch for review and removed from tracking before merge to main (output/ is gitignored policy); they remain on the user's machine and in feature-branch history. Future options: rerun `judge_synthesis_ab.py` for a quantitative check; consider whether the contrarian Omer-season reading should be steered (it follows the macro's Sukkot Sitz im Leben — a scholarly judgment call, not an agent error).

---

## Session 356 (2026-06-09): DOCX BiDi — verse header ending in a ketiv/qere rendered in the wrong typeface

**Objective**: User reported that in a generated DOCX, the verse-7 Hebrew header above its commentary rendered in a *different typeface* (Aptos 13) than every other Hebrew in the document (Times New Roman 13). Initially reported as Ps 67, later corrected to **Ps 60**.

**Root cause** (`src/utils/document_generator.py`):
- Verse-header Hebrew has two render paths: the native-RTL `_add_primarily_hebrew_line` (→ Times New Roman, LTR paragraph, no indent — the normal path) and the "long bare Hebrew block" `_add_hebrew_block_paragraph` (→ a right-aligned, 0.3″-indented RTL block, and for `is_verse_header` it **hardcoded Aptos**).
- `_split_long_hebrew_block` decides between them. It matches 6+ consecutive Hebrew words and is supposed to bail (`return None`) on anything containing a sof-pasuq ׃ (a complete verse), so verses route to the normal path. **But the guard only checked the matched group** (`match.group(1)`).
- Ps 60 v7 ends in a **ketiv/qere**: `לְמַעַן יֵחָלְצוּן יְדִידֶיךָ; הוֹשִׁיעָה יְמִינְךָ (ועננו) [וַעֲנֵנִי]׃`. The closing `]` is not a Hebrew character, so the regex's final `heb_word` ends at `וַעֲנֵנִי` and the trailing `]׃` falls **outside** `group(1)`. The guard saw no ׃ → treated the header as a bare Hebrew block → Aptos + block indentation. Every other verse ends in a bare `…ם׃` (the ׃ glued to the last word, inside the match) → guard fires → normal TNR path. Hence exactly one header looked wrong.
- This affects **any** psalm whose verse closes with a bracketed qere before the sof-pasuq — common in Psalms — not a Ps-60-specific fluke.

**Forensics**:
- Confirmed the symptom by scanning the actual DOCX XML: `output/psalm_60/psalm_060_commentary.docx` had exactly **1 Aptos-fonted Hebrew run** — the v7 header (`לְמַעַן יֵחָלְצוּן…`) — out of ~248 Hebrew runs (rest Times New Roman).
- The earlier Ps 67 detour was a false lead: Ps 67 v7 ends in a bare `…אֱלֹקֵינוּ׃`, so its guard fires and it was already uniform TNR. Verified byte-identical v6/v7 run properties in both the pipeline `_SI.docx` and the Word-resaved `Psalm 67 v2.docx` (0 Aptos Hebrew). That file simply doesn't exhibit the bug; the real case was Ps 60.

**Fix (two parts)**:
1. **Guard** (`_split_long_hebrew_block`): also inspect a 5-char trailing window past the match — `trailing = text[match.end():match.end()+5]` — and bail if `'׃' in hebrew or '׃' in trailing`. A `[qere]׃` verse is now recognized as a complete verse and routes through `_add_primarily_hebrew_line` like every other header, fixing **both** the font and the alignment/indent in one move.
2. **Font safety net**: the two block-path branches that hardcoded `'Aptos'` — the `is_verse_header` branch in `_add_paragraph_with_soft_breaks` and the "whole-line at string start" branch in `_add_paragraph_with_markdown` — now use `self.HEBREW_FONT` (Times New Roman). So even a genuinely punctuation-less long Hebrew header can never render Aptos.

**Verification** (deterministic, no LLM cost):
- Unit-traced the exact v7 string through the real `DocumentGenerator`: `_split_long_hebrew_block(...) is None` now True; rendering v7 vs a normal header (v6) yields identical run/paragraph properties (`cs=Times New Roman`, `bidi`, no alignment override, no indent).
- Regenerated `output/psalm_60/psalm_060_commentary.docx` (`python scripts/run_docx_only.py 60`) and rescanned: **0 Aptos-fonted Hebrew runs** (234 explicit Times New Roman + 14 inherited→TNR). The v7 header paragraph is now `align=default, indent=False`. The one remaining right-aligned/indented Hebrew block is a legitimate long-quote of v7 under the intro heading "Key verses and phrases" — intended block-quote rendering, now Times New Roman.

**Files changed**: `src/utils/document_generator.py` only. No scripts created or changed. Pipeline artifact `output/psalm_60/psalm_060_commentary.docx` regenerated; the user's study-guide copy (`Documents/Psalm study guide/Psalm 60.docx`) left untouched for the user to re-copy.

## Session 355 (2026-06-08): Post-migration path fix — figurative-language DB

**Objective**: Get the pipeline running again after the repo was migrated from OneDrive to the C drive (`C:\dev\personal\psalms`). Two failures surfaced when the user ran `python scripts/run_enhanced_pipeline.py 60`.

**Problems Identified**:
1. **Environment (not a code bug)**: In **git bash**, `python` resolved to the *global* `C:\Python313` install (loading `anthropic` from `AppData\Roaming\Python\Python313\site-packages`) instead of the venv — the slow import was Ctrl-C'd (the `KeyboardInterrupt` in the traceback, not a crash). The user's `c:\dev\…\venv\Scripts\activate` also failed because git bash treats backslashes as escapes. The venv itself is healthy (`pyvenv.cfg` → `C:\Python313`, `anthropic 0.79.0` imports in ~1.7s). Resolution is to activate with `source venv/Scripts/activate` (forward slashes) in git bash; PowerShell already auto-resolves the venv.
2. **Real migration casualty**: Step 2 (Micro Analysis) crashed with `FileNotFoundError: Figurative language database not found at C:\Users\ariro\OneDrive\Documents\Bible\database\Biblical_fig_language.db`. The figurative-language DB is **not** in the psalms repo — it lives in a **separate `bible` repo** that was also migrated to `C:\dev\personal\bible` (sibling of `psalms`). `FIGURATIVE_DB_PATH` in `src/agents/figurative_librarian.py` was hardcoded to the now-dead OneDrive location.

**Solutions Implemented**:
1. **`figurative_librarian.py` path made migration-resilient** (`src/agents/figurative_librarian.py:35`): replaced the hardcoded absolute path with a repo-relative default plus an env-var override:
   ```python
   _DEFAULT_FIGURATIVE_DB_PATH = (
       Path(__file__).resolve().parents[2].parent / "bible" / "database" / "Biblical_fig_language.db"
   )
   FIGURATIVE_DB_PATH = Path(os.environ.get("FIGURATIVE_DB_PATH", _DEFAULT_FIGURATIVE_DB_PATH))
   ```
   `parents[2]` is the psalms repo root, `.parent` is the repos root (`C:\dev\personal`), so it finds `…/bible/database/Biblical_fig_language.db` regardless of where the repos root sits, as long as `bible` and `psalms` remain siblings. Added `import os` and updated the module docstring's "Database Location" note.
2. **Chose the live migrated copy, not the OneDrive archive**: the user suggested `C:\Users\ariro\OneDrive\Documents\_Archive\Migrated repos (originals)`, but that is a backup still inside OneDrive (the location being abandoned). The live copy at `C:\dev\personal\bible\database\Biblical_fig_language.db` is byte-identical (152 MB, 2026-01-10) and lives in the properly migrated repo, so the repo-relative default points there.

**Verification** (no LLM cost):
- `FIGURATIVE_DB_PATH` resolves to `C:\dev\personal\bible\database\Biblical_fig_language.db`, `.exists()` → True; DB opens (tables: `verses`, `figurative_language`).
- `FigurativeLibrarian()` instantiates, and the full construction chain that died — `MicroAnalystV2(...)` → `ResearchAssembler` → `FigurativeLibrarian` (line 535 of `run_enhanced_pipeline.py`) — builds cleanly, with the Sacks / tanakh / liturgical librarians all resolving their paths inside the psalms repo.
- Grepped `src/` + `scripts/` for `OneDrive` / `C:/Users` paths: **this was the only such reference in production code**; all remaining ones are in `archive/` and `scratch/` (not used by the pipeline).

**Files Modified**:
- `src/agents/figurative_librarian.py` — `import os`; `FIGURATIVE_DB_PATH` now repo-relative with `FIGURATIVE_DB_PATH` env override; docstring updated
- `CLAUDE.md` — session number → 355, new entry, dropped oldest (Session 350)
- `docs/session_tracking/IMPLEMENTATION_LOG.md` — this entry

**Standing note for future migrations**: the psalms pipeline has a hard runtime dependency on the sibling `bible` repo for the figurative-language DB. If the two repos are ever separated, set the `FIGURATIVE_DB_PATH` env var to bridge them. No scripts created/changed → `scriptReferences.md` untouched.

---

## Session 354 (2026-06-04): DOCX BiDi — verse-table Hebrew size + final polish

**Objective**: Complete the Session 353 BiDi work by bumping the verse-table Hebrew (top-of-DOCX full-psalm table) to 13pt, matching all other Hebrew in the document, and applying the dash-bound concordance format and body-Hebrew size bump that were done interactively in Session 353.

**Problems Identified**:
- The verse-table Hebrew (top-of-DOCX psalm text, two-column table) was still at 12pt while all other Hebrew had been moved to 13pt during Session 353. This inconsistency was caught on DOCX review.

**Solutions Implemented**:
1. **Verse-table Hebrew 13pt** (`_format_psalm_text` in `document_generator.py`): bumped `heb_run.font.size` from `Pt(12)` to `Pt(13)` and the explicit `w:szCs` value from `24` (12pt in half-points) to `26` (13pt). This makes all Hebrew in the document uniformly 13pt — verse table, verse headers, body prose, block quotes. English in the verse table is unchanged.

**Files Modified**:
- `src/utils/document_generator.py` — `_format_psalm_text`: verse-table Hebrew 12→13pt (font.size + szCs)
- `CLAUDE.md` — session number → 354, new entry, dropped oldest
- `docs/session_tracking/IMPLEMENTATION_LOG.md` — this entry

**Note**: The concordance dash-bound format, global Hebrew +1pt, and verse-header single-RTL-run fixes were all implemented and committed in Session 353 (commit `21a7d53`). This session adds only the verse-table size fix and wraps up the documentation.

---

## Session 353 (2026-06-04): DOCX BiDi — native RTL runs replace the reverse+LRO engine

**Objective**: Fix three long-standing Hebrew rendering bugs in the generated DOCX (reported on the Ps 67 run): (1) inline Hebrew quotes garbled into the wrong word order; (2) any Hebrew quote that straddles a line break wraps *backwards* (end of phrase on the upper line); (3) the "Concordance Entries Reviewed" methodological-summary line is an unreadable scramble of roots, counts, and semicolons.

**Root cause (all three, one mechanism)**: `document_generator.py` rendered inline Hebrew by **pre-reversing it into visual order by grapheme cluster and wrapping it in a LEFT-TO-RIGHT OVERRIDE** (`U+202D … U+202C`). This defeats Word's bidi engine, so: (1) when a markdown bold/italic marker split a Hebrew phrase, the pieces got inconsistent direction handling (some reversed+LRO, some not) and Word ordered them as separate islands; (2) LRO forces LTR layout, so pre-reversed text wraps English-style and the *end* of the phrase lands on the upper line — inherent, hits any wrapping quote; (3) the concordance value has zero Latin letters, so `_is_hebrew_dominant` misfired and the whole digit/paren/semicolon string was positionally reversed.

**Fix — switch inline Hebrew to native RTL runs** (the same mechanism the verse table and the Arabic path already use): keep Hebrew in **logical order** and mark each Hebrew run with `w:rtl` + a complex-script font; the paragraph stays LTR (English base). Word's own bidi engine then handles ordering, nikud, and line-wrapping correctly.
- New funnel `_add_inline_runs()` + helpers `_segment_by_script()` (splits text into Hebrew/non-Hebrew segments in logical order; glues intra-phrase spaces/maqqef/hyphen, and an apostrophe glued to a preceding Hebrew letter — the geresh-style `ה'` divine-name mark — so it doesn't split the run, while leaving English `king's` alone) and `_mark_run_hebrew()` (cs font + `w:rtl`). All ~6 duplicated reverse+LRO code paths (`_process_markdown_formatting`, `_add_formatted_content` ×2 branches, `_add_paragraph_with_soft_breaks`, the italic spans, `_process_text_rtl`) now route through it.
- **Inter-Hebrew whitespace fix** `_join_rtl_runs_across_whitespace()` (doc-wide post-pass, called in `generate()` before `_fix_complex_script_fonts`): when a bold/italic marker splits a Hebrew phrase, the boundary space lands in its own run; if it stayed LTR, Word treated the two Hebrew runs as separate islands and reordered them. The pass marks any pure-whitespace run **whose both neighbours are RTL** as RTL too (Hebrew↔English boundary spaces stay LTR — correct).
- **Issue 3**: `_add_summary_paragraph()` now detects a Hebrew-containing value, keeps the label + numeric total on the LTR line, and renders the parenthesized breakdown as a separate **native RTL paragraph** (`w:bidi=1`, right-aligned). An LTR-base list of `root (count);` items scrambles when it wraps; a true RTL paragraph pairs every root with its count and reads right-to-left.
- **Cleanup**: removed the now-orphaned reversal methods (`_split_into_grapheme_clusters`, `_reverse_hebrew_by_clusters`, `_reverse_bare_hebrew_segments`, `_process_text_rtl`, `_reverse_primarily_hebrew_line`, `_is_hebrew_dominant`; ~227 lines). Kept `_is_primarily_hebrew` (still used for consecutive-Hebrew-block detection).

**Verification method (new, reusable)**: rendered the regenerated DOCX → PDF via Word COM automation (PowerShell `Word.Application` → `SaveAs` wdFormatPDF), then read the PDF visually AND extracted glyph **x-coordinates** with PyMuPDF to confirm true visual left-to-right order (eyeballing nikud-laden Hebrew in a downscaled image is unreliable). Word-COM render is the ground truth (same engine the user reads in). All regeneration used existing markdown only — **no LLM steps, no cost** (`run_docx_only.py`-style harness).
- **Ps 67** (the reported psalm, regenerated from `intro_SI.md`/`verses_SI.md`): issue 1 coordinate-verified (`יָאֵר ה' פָּנָיו אֵלֶיךָ` reads R→L in correct order, apostrophe-divine-name intact); the 4-word quote that wraps reads correctly across the break; issue 3 list renders cleanly with every count paired.
- **Edge cases** (Ps 51, 9, 50, 18): ketiv/qere `[הֶרֶב]` and editorial `[מִפְּנֵי]` brackets, multi-line block quotes (Ps 50 piyyut, with internal periods/ellipses), parens, smart quotes, paseq `׀`, sof-pasuq, and long verse superscriptions (Ps 18:1) — all render in correct order, no garbling, no dotted-circle nikud, no backwards wraps. Color-coded experiments (per-word RGB) independently confirmed: native RTL gives correct order and correct multi-line wrap; the old reverse+LRO reproduced both bugs.

**Round 2 — three more issues found on reviewing the regenerated Ps 67 DOCX** (same session):
1. **Garbled verse-header verse lines** (the Hebrew verse at the top of each commentary section): a `;` between the two cola was a non-Hebrew run between two Hebrew runs, so in the LTR paragraph Word reordered the cola (second cola printed before first). Fix: render a standalone primarily-Hebrew line (verse header, or any Hebrew-dominant line — now detected even without a sof-pasuq, via the `is_verse_header` flag) as a **single native RTL run per soft-break line** (`_add_primarily_hebrew_line`). Keeping the whole line in one RTL run gives correct native placement to the `;` cola separator, ketiv/qere `[brackets]` (verified on Ps 51 v.4 — `[הֶרֶב]` sits correctly at the right with the period at the left), and the final sof-pasuq. (An inline render instead pushes the leading `[` / trailing `.` to the wrong side.)
2. **Verse headers should be 13pt** — `_add_primarily_hebrew_line` sets each run's `szCs` to 26.
3. **Inline body Hebrew was ~11pt, should be 12pt** — python-docx's `font.size` sets `w:sz` (Latin) but not `w:szCs` (complex script), so Hebrew fell back to Word's default complex-script size. Added `_set_style_complex_size()` and set `szCs` on the `Normal`/`BodySans` (12pt) and `SummaryText` (9pt) styles so inline Hebrew matches the body.
- Also **generalized `_join_rtl_runs_across_whitespace`**: it now marks any *neutral-only* run (whitespace + separators like `;`/`:`/`,`/`.`, no Latin letters/digits, and **not** brackets/parens which are directional) RTL when both neighbours are RTL — so an inline prose Hebrew phrase split by a `;` between cola also stays ordered. Verified by Word→PDF render + PyMuPDF size/coordinate extraction on Ps 67 (v.2 header: 13pt, cola in order; body Hebrew 12pt; `ה'` apostrophe-name 12pt inline) and Ps 51 (v.3 & v.4 headers 13pt, v.4 brackets correct; concordance summary still clean at 9pt).

**Round 3 — concordance readability + global Hebrew size** (same session, after further DOCX review):
- **Concordance breakdown reformatted** (`_add_summary_paragraph`): the parenthesized inline form (`root (count); …`) was unreadable — the count floated ambiguously between two roots and entries split across line wraps. Now parsed into `(root, count)` pairs (regex tolerant of multi-word roots, nikud, shin-dot) and rendered in the native RTL paragraph as `root — count;` entries where **each entry is a single RTL run** (em-dash + count fully NBSP-bound). Critically, root and count must be in the *same* run: a separate LTR `— count` run breaks at the RTL/LTR directional boundary even with an NBSP, which is what split `לאם — 26` across lines. The only breakable point is the plain space between entries, so wraps now fall cleanly between entries (verified: `…יודה—50;` ends a line, `ישועה—49…` starts the next; every root paired with its correct count).
- **All Hebrew bumped +1pt to match the English** (per user — Times New Roman Hebrew reads visually smaller than Aptos at the same size): body/`Normal`/`BodySans` complex-script size 12→**13pt**, `SummaryText` 9→**10pt** (via `_set_style_complex_size`). Verse headers and block quotes were already 13pt. Verified all body + verse-header Hebrew renders at 13pt and the concordance roots at 10pt.
- **`scripts/run_docx_only.py` confirmed** to use the updated `DocumentGenerator` (no separate rendering path); ran it on Ps 51 successfully.

**Decision — `combined_document_generator.py` left unchanged (per user)**: it carries its own older copy of the reverse+LRO logic but is **retired** from the current pipeline (only the Session-300-era `run_si_pipeline_with_synthesis.py`/`*_TEST.py` reference it; `run_si_pipeline.py`/`run_enhanced_pipeline.py` do not produce combined/college docs, and no current psalm has college files to verify against). Added a prominent ⚠️ docstring on `CombinedDocumentGenerator` flagging the outdated BiDi and pointing to the helpers to port if that path is ever revived.

**Files touched**: `src/utils/document_generator.py` (native-RTL helpers, rewired all inline paths, summary RTL line, join-pass, removed dead reversal methods); `src/utils/combined_document_generator.py` (warning docstring only). No DB/schema changes. Dev dependency `pymupdf` installed locally for verification only (not imported by production code, not added to requirements). Production DOCX outputs were **not** overwritten — regenerate any psalm's DOCX with `python scripts/run_docx_only.py N` (no LLM cost) to pick up the fix.

---

## Session 352 (2026-06-02): Macro → Opus 4.8 (adaptive/high) + lemma-dedup of augmented root traces

**Objective**: Execute the two follow-ups queued at the end of Session 351 (from the Ps 59 end-to-end run + a macro/micro cost analysis): (1) move the Macro agent from `claude-opus-4-6` to `claude-opus-4-8`, matching the Master Writer's adaptive/high config; (2) make `_augment_with_root_searches` dedup added root traces by their resolved lemma rather than by surface string. Micro agent stays `claude-sonnet-4-6` (per user, the earlier gpt-5.4 idea is dropped). Also: retire the `NEXT_SESSION_BRIEF.md` doc from the workflow (per user).

**Task 1 — Macro agent → Opus 4.8.**
- **Budget-neutral**: all Opus tiers (4-5/4-6/4-7/4-8) are priced identically ($5/$25 per 1M in/out); macro avg ≈ 4.7K in / 13.4K out ⇒ ~$0.36/psalm before and after (Session-351 analysis of Ps 54–58 `psalm_0NN_cost.json`).
- This was **two changes**, not just a model-ID swap. The macro previously ran adaptive + effort `"max"` unconditionally; the Master Writer (`src/agents/archive/master_editor_v2.py:2246-2249`) gates effort by model — opus-4-7 → `"max"`, opus-4-8 → `"high"`. So I (a) flipped the default model and (b) replaced the unconditional `output_config={"effort":"max"}` with the same model-gated `stream_kwargs` pattern: `opus-4-8 → {"effort":"high"}`, `opus-4-7 → {"effort":"max"}`, and **`output_config` omitted for opus-4-6** (older models reject the param — the prior code only got away with passing it because the API tolerated it for 4-6).
- **Change spots**: `MacroAnalyst.DEFAULT_MODEL` and the streaming call in `analyze_psalm` (`src/agents/macro_analyst.py`); the `macro_model` keyword default and the `macro_mdl = … else "claude-opus-4-8"` fallback in both `scripts/run_enhanced_pipeline.py` and `scripts/run_si_pipeline.py`. Also refreshed stale "Opus 4.6" docstrings/comments in `macro_analyst.py`.
- **Verification**: zero-cost wiring check confirmed `DEFAULT_MODEL == claude-opus-4-8` and the effort gating (4-8→high, 4-7→max, 4-6→omitted). No live pipeline run — brief flagged it low-risk (same family, *lighter* effort) with no formal quality gate needed; a 1-psalm macro sanity run (~$0.36) remains available on request.

**Task 2 — dedup augmented root traces by RESOLVED LEMMA** (`src/agents/micro_analyst.py` `_augment_with_root_searches`).
- **Problem** (seen in the Session-351 Ps 59 run): the dedup keyed on the consonantal *surface string* (`existing = {to_consonantal(req.query) …}`). After Session 351, several different surface spellings resolve to one lemma, so the same lemma got traced in separate bundles — identical verse-lists under different headers, pure token noise for the writer/synthesis. Confirmed against `output/psalm_59/psalm_059_research_v2.md`: `משגב` and `משגבי` (both 13 external results → lemma מִשְׂגָּב) and `נוע` and `ינועו` (both 32 → lemma נוע) were duplicate-lemma bundles.
- **Fix**: resolve each candidate root's lemma via `librarian.search._resolve_lemma`; build the `existing`/`seen` sets from **lemmas**. Existing single-word picks contribute the full set of lemmas they actually trace — their own plus their single-word alternates' (the librarian folds sibling roots in via its single-word lemma path); 2-word collocation requests trace a conjunction (different result set) so they're excluded from the existing-lemma set. Keep a consonantal fallback (`existing_consonantal`/`seen_consonantal`) for candidate roots whose lemma doesn't resolve.
- **Verification** (deterministic, no LLM call — local DB only; throwaway `scripts/_verify_task2_dedup.py`, since deleted): drove the real `_augment_with_root_searches` on Ps 59's fixed `micro_v2.json` discoveries. CASE 1 (no existing picks): **0 duplicated lemmas** across the 12 root traces (was: משגב+משגבי and נוע+ינועו both present) — `משגבי` and `נוע`-surface collapsed into their lemmas, freeing cap slots for other distinct lemmas (כחש, לעג, …). CASE 2 (seeded a single-word `נוע` primary pick): the derived `ינועו` is suppressed because lemma נוע is now in `existing_lemmas`, and `הקיץ` takes the freed slot. External yield is unchanged by construction — a retained trace and the dropped same-lemma variant search the identical lemma → identical verses.

**Files touched**: `src/agents/macro_analyst.py`, `src/agents/micro_analyst.py`, `scripts/run_enhanced_pipeline.py`, `scripts/run_si_pipeline.py`; **deleted** `docs/session_tracking/NEXT_SESSION_BRIEF.md` and scrubbed its references in `CLAUDE.md`, `scriptReferences.md`, and `src/agents/synthesis_discovery.py` (redirected to this log). Doc updates: `CLAUDE.md`, this log. No DB or schema changes.

---

## Session 351 (2026-06-02): Lemma-Aware Concordance (D & E) — true morphology wired into search

**Objective**: Execute D & E from `NEXT_SESSION_BRIEF.md` — replace Session-350's runtime string-expansion against surface columns with real morphology from ETCBC/BHSA, so root traces and 2-word collocations become exact, indexed lookups (prefix/suffix/conjugation/word-order tolerant) and the brittle heuristics (`is_root_match`, prefix/suffix variation explosion, surface-frequency root selection) can retire.

**Two findings that corrected the brief before any code was written** (investigation pass against the locally-cached BHSA 2021 data):
1. **BHSA `root` is unusable as a search key.** Full-Bible coverage is only **16.9%** (72,051 / 426,590 words): `None` on *all* 73,141 verbs, all prepositions/conjunctions, most nouns (subs), and proper names — and `None` on *every* Session-350 marquee target (פלג, נוד, נדד, חסד, אמת). It is also ETCBC-transliterated (`>CR`, `J<Y`) with no `Transcription` converter in the installed TF version. **`lex_utf8` (lemma) is 100% coverage** and clean Hebrew. → Shipped a **`lemma`** column (lex), not `root`. Lemma grouping (affix/conjugation tolerant) delivers all the brief's target intertexts anyway.
2. **The brief's "positional join" (proposal §4 step 2) is broken.** BHSA tokenizes proclitic particles (ב/כ/ל/מ/ו/ה) as *separate* word nodes while our concordance keeps them attached (`ב`+`עצת` ⇒ our `בעצת`). Position-by-position match is only **26%**, equal-word-count only 9.9%. But our token is always the *concatenation of consecutive BHSA tokens*, so a **greedy concat-alignment** (merge BHSA tokens until they equal our token; assign the group's content lemma = last non-particle sub-token) hits **96.3%**. Exact-match required ⇒ a miss leaves `lemma` NULL (→ naive fallback at search time), never a *wrong* lemma. Also discovered: `T.sectionFromNode` returns English book names (`2_Kings`, `Song_of_songs`, `1_Chronicles`), **not** the Latin `F.book.v` names (`Reges_II`, `Canticum`) — map off the section names (only 7 differ from our DB names).

**Implementation**:
1. **Migration** — new `scripts/add_lemma_column.py`: loads BHSA, builds per-`(book,ch,vs)` token lists, `ALTER TABLE concordance ADD COLUMN lemma TEXT`, greedy-aligns each verse, `UPDATE` per `concordance_id` in batches, `CREATE INDEX idx_concordance_lemma`. Lemma stored via `normalize_for_search(lex_utf8,'consonantal')` so it matches the existing `word_consonantal*` convention (shin/sin dots stripped) and the query side. `--dry-run` (per-book coverage, no writes) and `--book` (single-book validation) flags. Result: **300,835 / 312,479 rows = 96.3%** lemma coverage, 0 versification gaps, worst book Lamentations 88% (acrostic spellings). DB backed up to `database/tanakh.db.pre_lemma_bak` first.
2. **Search layer** (`src/concordance/search.py`): `_resolve_lemma(word)` (most-common lemma among tokens sharing the surface form; else the word itself if it's a stored lemma; cached), `search_lemma(lemma)` (`WHERE lemma = ?`), `verse_lemmas()`, `search_lemmas_in_verse(lemmas)` (verse contains ALL lemmas — morphology-aware collocation).
3. **Librarian** (`src/agents/concordance_librarian.py`): in `search_with_variations`, single-word root traces resolve to a lemma and run one `search_lemma` (no variation explosion; single-word alternates folded in as sibling-lemma traces); 2-word collocations resolve both lemmas and run `search_lemmas_in_verse` (rarest lemma anchored first). Surface-only phrase fallback + final surface validation are skipped under `lemma_mode` (they would wrongly discard genuine lemma matches like חסד אמת ↔ חסדו ואמתו). Falls back to the legacy surface path when a lemma can't be resolved. New `lemma_frequency(word)` (count of `WHERE lemma = ?`).
4. **Selection** (`src/concordance/root_selection.py`, `src/agents/micro_analyst.py`): `_augment_with_root_searches` now passes `librarian.lemma_frequency` to `select_distinctive_roots`; ranking is by true lemma frequency (rarest = most distinctive), retiring the "prefer 3-letter forms" length-bucket hack (length kept only as a deterministic tie-break). `is_root_match` (`root_matcher.py`) is now bypassed in the production pipeline; left in place for the standalone `concordance_tool.py` CLI.
5. **Post-search guard** (`src/agents/research_assembler.py`): `COMMON_CAP` raised 60→120 to match the selection frequency window — now a thin safety net for surface-fallback searches rather than the primary distinctiveness gate.

**Validation** (`scripts/EXPERIMENT_concordance_eval.py 54 55 56 57 58`, reusing production Stage-1 discoveries; harness `COMMON_CAP` also aligned to 120): external-match yield **24% → 96%** (110/115 searches, **0 common-dropped** because lemma-frequency gating now keeps over-common roots from being selected at all). Per-psalm e.g. Ps 57 24/24, Ps 58 21/23. Direct spot-checks of the brief's previously-broken cases all pass: `ימיש`→Exod 13:22 (hollow verb resolved to lemma **מוש** — impossible under surface matching), `בצל כנפיך`→**צל**+**כנף** (Ps 17:8/36:8/63:8; Ps source self-dropped), `חסד אמת`→**Exod 34:6** (catches suffixed/conjoined חסדו ואמתו), `פלג`→Gen 10-11 Babel, `נוד`→Gen 4 Cain; genuine hapaxes honestly reported as "appears only in this psalm" (e.g. שבלול). Junk/non-resolving input degrades gracefully (0 results, no crash).

**Open decisions (per brief), resolved with the user**: ship **lemma** with **lemma-default** search (user: "use the lemma column approach"); **skip the `root` column** (unusable for the target cases — my recommendation, accepted); **keep the bare-form** Methods "Concordance Entries Reviewed" rendering (no `lemma ⟵ phrase`, my recommendation, accepted — trivial to add later).

**Production validation (Ps 59, full `run_enhanced_pipeline.py 59`, $6.81)**: ran end-to-end after watching the concordance bundle land (and confirming it before the Opus spend). Every search took the lemma path (`Lemma search (single|colloc)`, 1–2 queries each — no variation explosion); affixes/inflections resolved (`הקיץ`→`קיץ`, `ינועו`→`נוע`, `משגבי`→`משגב`, `בשררי`→`שורר`), sibling lemmas folded (`שגב`→{שגב,משגב}). The Methods "Concordance Entries Reviewed" line rendered correctly (bare-form + counts). Crucially the intertexts **landed in the final prose**: `שחק`+`לעג` → Ps 2:4 (divine laughter, fused into one argument from two separate searches); `שגב`→מִשְׂגָּב fortress cluster citing 2 Sam 22:3; `נוע`→"wander/totter" motif. The known homograph noise (`עזז` 61 = strength+goats, `שחק` = laugh+sky) did **not** mislead the writer (prose used עֻזֶּךָ "Your strength" correctly). DOCX generated (62 KB).

**Next-session decisions (captured in `NEXT_SESSION_BRIEF.md`)**: (1) **macro → claude-opus-4-8, adaptive + effort `high`** (matching the Master Writer's opus-4-8 setting, confirmed at `master_editor_v2.py:2243-2249`; macro currently runs effort `max`, so it's a model-ID *and* effort change) — budget-neutral. Micro **stays claude-sonnet-4-6** (a gpt-5.4 swap was considered then dropped). (2) **Dedupe augmented root traces by RESOLVED LEMMA** — the Ps 59 Methods line shows the redundancy (`משגב`/`משגבי`, `נוע`/`ינועו` traced separately because `_augment_with_root_searches` dedups by consonantal string, not lemma).

**Files changed**: `scripts/add_lemma_column.py` (new), `src/concordance/search.py`, `src/agents/concordance_librarian.py`, `src/agents/micro_analyst.py`, `src/concordance/root_selection.py`, `src/agents/research_assembler.py`; docs: `LEMMA_ROOT_SEARCH_PROPOSAL.md` (STATUS banner), `NEXT_SESSION_BRIEF.md` (now the next plan), `CLAUDE.md`, `scriptReferences.md`; harnesses: `EXPERIMENT_concordance_eval.py`, `EXPERIMENT_concordance_trace.py` (COMMON_CAP→120). DB: `lemma` column added + indexed in `database/tanakh.db` (gitignored; rebuild via `scripts/add_lemma_column.py`). `is_root_match`/`root_matcher.py` retained (CLI only).

**Not done / possible follow-ups**: BHSA `root` (cognate grouping beyond lemma) remains unwired (low value here); the `lemma ⟵ source phrase` Methods rendering deferred; lemma-dedup of augmented roots (Task 2 in the brief); a known precision limit — consonantal/dot-stripped lemmas collapse true homographs (עֹז "strength" / עֵז "goat"; שׂחק "laugh" / שׁחק "sky"), consistent with the pipeline's existing `word_consonantal` convention and low-risk (the writer reads Hebrew).

---

## Session 350 (2026-06-02): Concordance Value-Add — Distinctive-Root Searches

**Objective**: The concordance was suspected of leaving value on the table — searches were lifting verbatim multi-word phrases from each verse, which rarely recur elsewhere in Tanakh.

**Diagnosis** (measured across the last 5 psalms run, 54–58; 50 searches):
- **62%** returned ONLY the source verse (self-match, zero marginal value), **14%** returned nothing, only **24%** surfaced any external parallel. 3-word queries: **0/12** external.
- Root causes: (1) the Stage-2 prompt forced the *exact phrase* and **explicitly forbade** single-word searches (`micro_analyst.py`); (2) `_override_llm_base_forms` clobbered any query into the verse phrase and force-added verse forms to *guarantee* a self-match; (3) phrase matching is surface-exact with no morphological expansion (e.g. `פלג לשון` → 0, can't even match its own `פַּלַּג לְשׁוֹנָם`); (4) a latent bug — analyst variants were written to `req.alternates` but the librarian reads `req.alternate_queries`, so they were never searched.

**Solutions (A/B/C, all shipped to production)**:
1. **A — distinctive-root searches**: rewrote the Stage-2 concordance prompt to trace the single most distinctive root per insight (with a common-word avoid-list); fixed `_override_llm_base_forms` to leave ≤2-word queries untouched; added `_augment_with_root_searches` (deterministic rarest-distinctive-root derivation) + new helper `src/concordance/root_selection.py`. Root traces are independent top-level requests that bypass the alternates bug.
2. **B — 2-word cap** on collocations (3-word queries had 0% external yield).
3. **C — honest reporting**: `ConcordanceLibrarian` drops source-psalm self-matches (`self_match_count`/`only_self` on the bundle); `research_assembler.py` reports "external" counts and "appears only in this psalm"; post-search distinctiveness guard drops single words with >`COMMON_CAP`(=60) external matches (bare frequency proved unreliable — Hebrew roots surface as inflections).
4. **Follow-ups from review**: random (seeded, reproducible) canon-spread sampling of which ≤10 matches are displayed (`_sample_for_display`, replacing the clustered `[:10]`); dropped the English gloss from concordance result lines (Hebrew only, ~47% token saving per line); stopped expanding 2-word collocations to the verse form (was legacy self-match behavior, caused drift).

**Validation** (reusing production Stage-1 discoveries via `scripts/EXPERIMENT_concordance_eval.py`; trace via `scripts/EXPERIMENT_concordance_trace.py`): external-match yield **24% → ~90%** (Ps 54: 4/10→20/22; 55: 1/10→~22/22; 56: 0/10→21/23; 57: 5/10→23/24; 58: 2/10→19/23). Recovered non-obvious intertexts the old pipeline missed: `פלג`→Gen 10-11 (Babel), `נוד`→Gen 4 (Cain/Nod), `מוש`→Exod 13:22 (pillar that did not depart), `נאד`→Ps 119:83 (wineskin in smoke), `חסד אמת`→Exod 34:6 (Thirteen Attributes).

**Token cost**: concordance section grows from ~2.7% of the research bundle to ~15–20% (≈ +8–11K tokens/psalm pre-English-drop; ~half that after). Full bundle still well under the 350K-char writer trim cap, so the whole (larger) concordance reaches both the synthesis-discovery and master-writer calls.

**Methods/DOCX note**: the "Concordance Entries Reviewed" line now lists roots/collocations (e.g. `פלג (10)`) instead of the verse phrase, with honest external counts.

**Deferred to next session (D & E)**: true morphology-aware root + 2-word search via a `lemma`/`root` column on the `concordance` table, populated from the already-built-but-unwired ETCBC/BHSA data. Full design in `docs/architecture/LEMMA_ROOT_SEARCH_PROPOSAL.md`; plan in `docs/session_tracking/NEXT_SESSION_BRIEF.md`.

**Files changed**: `src/agents/micro_analyst.py`, `src/agents/concordance_librarian.py`, `src/agents/research_assembler.py`, `src/concordance/root_selection.py` (new); docs: `LEMMA_ROOT_SEARCH_PROPOSAL.md`, `NEXT_SESSION_BRIEF.md`; harnesses: `scripts/EXPERIMENT_concordance_eval.py`, `scripts/EXPERIMENT_concordance_trace.py`.

---

## Session 349 (2026-05-30): Remove JSON Dependencies from Pipeline

**Objective**: Remove `psalm_function_for_RAG.json` and `ugaritic.json` dependencies from the pipeline as they are now superseded by deep research.

**Problems Identified**:
- The pipeline was still parsing and preparing Ugaritic parallels and psalm functions from static JSON databases in `rag_manager.py` to inject into the `RAGContext`.
- The document generators were displaying statistics for Ugaritic parallels that were no longer relevant to the actual deep research results.
- Old references to these files existed in the architecture and developer documentation.

**Solutions Implemented**:
1. Cleaned up `src/agents/rag_manager.py` by removing the loading and parsing logic for the two JSON files, along with formatting code for the prompt context.
2. Modified `src/utils/document_generator.py` and `src/utils/combined_document_generator.py` to remove the Ugaritic count from the "Research & Data Inputs" methodological summary in generated DOCX output.
3. Removed mentions of these obsolete RAG components from `docs/architecture/CONTEXT.md` and `docs/guides/DEVELOPER_GUIDE.md`.
4. Updated session history and tracking in `CLAUDE.md`.

**Files Modified**:
- `src/agents/rag_manager.py` - Removed JSON loading and processing
- `src/utils/document_generator.py` - Removed Ugaritic count
- `src/utils/combined_document_generator.py` - Removed Ugaritic count
- `docs/architecture/CONTEXT.md` - Cleaned up docs
- `docs/guides/DEVELOPER_GUIDE.md` - Cleaned up docs
- `CLAUDE.md` - Updated session log

---

## Session 347 (2026-05-20): Synthesis-Discovery Sidecar — Production Wiring + Ps 55 Validation

**Objective**: Execute the design proposed in `NEXT_SESSION_BRIEF.md` — replace the Session-346 two-call SPINE architecture with a sidecar synthesis-DISCOVERY pass that feeds cross-verse observations into the production one-call writer as additional input (not overriding instruction), behind a flag, with no impact on the default writer path. Validate end-to-end on Ps 55 (full chain: discovery → writer → print-ready → citation verifier → copy editor → DOCX) into a sidecar directory so the shipped Ps 55 baseline stays untouched.

**Problems Identified**:

1. **Two failed earlier attempts at "more synthesis."** The retired `InsightExtractor` was *extractive*: it could only filter what was already in the research bundle, which structurally cannot construct cross-verse claims like the ק-ר-ב dual-lexeme reading (that claim isn't *in* the bundle — it emerges only when you read multiple verses together). The Session-346 two-call experiment was *generative* but over-engineered the prose: forcing anchored arcs into specific verses raised the over-claim surface area (32 copy-editor changes on scaled-with-guardrail vs. 20 on cap-3/4). The lesson from the 3-way blind eval was that the *insights themselves* carried; the spine wasn't actually needed to land them in the prose.

2. **The Session-346 evidence-honesty filter was incomplete.** It caught the failure modes I named (no "homophony" overclaim, no "signature root" Babel, no invented Exod 10:3 prooftext) but missed an entire population the writer found: counting errors ("eight movements" / "ten"), strained etymology (חלל "stab through" the covenant), non-sequitur synthesis ("prayer begins where evil cannot follow"), fabricated parallels (Ps 88:16 "אֵמֵי מָוֶת" — phrase doesn't exist), non-uniqueness claims (Exod 13:22 "the only" comparable formula — Jer 17:8 and Josh 1:8 are cousins). Calibration needs to be enumerable failure modes *plus* a meta-rule that demands self-audit beyond the named modes.

3. **Production must not regress while we experiment.** The shipped one-call writer was one evaluator's favourite in the 3-way blind eval; the Session-346 RULE 7b / RULE 8 carve-out / phrase-coverage changes need broader validation before they're disturbed. So the discovery sidecar must go behind a flag, the writer prompt must be byte-identical on the default path, and the sidecar's output must be a separate inspectable file the user can review before committing to a fresh writer call.

**Solutions Implemented**:

### Part 1 — New agent: `src/agents/synthesis_discovery.py`

Single-purpose generative cross-verse discovery agent (Opus 4.7, max effort, adaptive thinking, 64K max_tokens, streaming with retry/resume on transient drops — same config family as the writer for evidence parity). Reuses the Session-346 `SYNTHESIS_TASK` prompt structure but with two deliberate changes per the brief:

- **DROPPED**: anchor-verse assignments and "how to signal at other verses" fields. Those existed only because the two-call spine architecture needed them; here the writer decides where things land.
- **KEPT**: tiered survivors (governing + core + additional), per-verse Hebrew evidence, novelty check.
- **HARDENED** the evidence-honesty filter to 9 named failure modes (a–i) plus a meta-rule (j) — exactly the regression set from the Session-346 Ps 55 scaled-with-guardrail copy-edit log:
  - (a) homophony vs. consonantal overlap; (b) echo vs. verbatim; (c) primary lexical meaning is what survives (named חלל "stab through" explicitly); (d) no invented or stretched prooftexts (every claimed parallel must be a literal contiguous quotation); (e) uniqueness claims require checking ("the only place" is almost always wrong — name 3-5 cousins as default); (f) count before you cite a number; (g) non-sequitur synthesis (named "prayer begins where evil cannot follow" explicitly); (h) no "signature root" / etymology claims unless certain; (i) match assertion strength to evidence.
  - (j) META-RULE: "Can I name two failure modes from (a)–(i) that I did NOT already check on this particular observation? If yes, check them. If you can't generate two more failure modes you haven't already audited, you haven't checked enough."

Output format: machine-extractable block bracketed by `---CROSS-VERSE-OBSERVATIONS-START---` / `---CROSS-VERSE-OBSERVATIONS-END---`. Agent's `discover()` method returns dict with `observations_markdown` (the parsed block), `full_response`, and exact token counts. Cost tracker registers as `claude-opus-4-7` automatically. Debug prompt and response saved to `output/debug/synthesis_discovery_{prompt,response}_psalm_NNN.txt` for inspection.

### Part 2 — Master Editor extension (no default-path regression)

Modified `src/agents/master_editor.py`:

- `write_commentary(synthesis_discovery_file: Optional[Path] = None)` — new optional kwarg. When provided and the file exists with content, the file's text is stored on `self._cross_verse_observations` for the prompt assembly step.

- `_perform_writer_synthesis()` — after rendering the standard writer prompt, if `self._cross_verse_observations` is non-empty, splice a new INPUT block ("**CROSS-VERSE OBSERVATIONS** *(use where they fit; do NOT structure your commentary around them)*") into the prompt at a stable anchor (`### ANALYTICAL FRAMEWORK`). The splice header explicitly tells the writer: keep phrasing strength as-is, RULE 7b / RULE 8 / phrase coverage / dinner-party register all still apply. Default path (file is None or empty): the prompt is byte-identical to production. Verified: on the Ps 55 sidecar run the log reports "Spliced cross-verse observations block (16,258 chars) into writer prompt before ANALYTICAL FRAMEWORK."

- New `discover_cross_verse_observations(macro_file, micro_file, research_file, psalm_number, output_path, skip_if_exists=True)` — orchestrator method that loads the inputs (same code paths as `write_commentary` so the discovery pass sees byte-identical evidence to the writer), runs `SynthesisDiscoveryAgent`, validates the response is non-trivial (≥100 chars), writes to `output/psalm_NNN/psalm_NNN_synthesis_discovery.md`, and returns the path. `skip_if_exists=True` makes the call resume-safe.

### Part 3 — Pipeline runner: `--synthesis-discovery` flag

Modified `scripts/run_enhanced_pipeline.py`:

- New CLI flag `--synthesis-discovery` (default OFF, marked experimental).
- New STEP 3.5 between STEP 2 (micro) and STEP 4 (writer): when the flag is set, calls `master_editor.discover_cross_verse_observations()` and passes the returned path into `master_editor.write_commentary(synthesis_discovery_file=...)`. Quota guard wraps the call. Fatal on failure (the flag was explicitly set, so silent fallthrough would defeat the purpose). Cost tracked through the existing `cost_tracker`; tracker registers `synthesis_discovery: claude-opus-4-7` in the pipeline summary.

### Part 4 — End-to-end Ps 55 validation in a sidecar directory

Ran the full pipeline (discovery → writer → print-ready → citation verifier → copy editor → DOCX) on Ps 55, into `output/psalm_55/EXPERIMENT_synthesis_discovery/`, with `--resume --synthesis-discovery --skip-lit-echoes --output-dir output/psalm_55/EXPERIMENT_synthesis_discovery`. Macro / micro / research_v2.md copied into the sidecar so resume mode skipped the upstream steps cleanly. Shipped Ps 55 baseline untouched.

**Discovery results**: 14 calibrated observations (1 governing + 9 core + 4 additional, 16,258 chars). The governing observation is the ק-ר-ב dual-lexeme reading: "the psalm of betrayal is silently structured by a question its surface never names: what does proximity mean when a friend's nearness is itself the wound?" Discovery cost: $1.83 (153,781 in / 42,604 out at Opus 4.7).

**Writer pass with spliced observations**: 32-minute Opus 4.7 max-effort call (173,743 in / 91,466 out). Cost: $3.16. Output picked up the observations naturally — all three brief-mandated insights landed in the final copy-edited prose:
- **ק-ר-ב dual-lexeme**: front-and-center in the intro essay ("The consonants ק-ר-ב appear six times in Psalm 55 — more times than in any comparable Davidic psalm — and they do quiet, devastating double duty"), with full migration narrative through all 6 occurrences (vv. 5, 11, 12, 16, 19, 22) developed across the verse commentary.
- **Exod 13:22 לֹא־יָמִישׁ inversion**: at v. 11 *and* v. 12, calibrated as "Its most famous biblical use is Exod 13:22" — no "the only" overclaim.
- **שׁלם v.19↔v.21 contestation**: at v. 19 ("Two verses, two appearances of שׁלם, contested ownership") *and* v. 21 ("owned by divine rescue on one side and human violation on the other"). Same calibrated framing the discovery shipped.

The B/A-shared v.4↔v.23 מוט reversal also lands in the intro. The prose feels organic rather than spine-organized — the writer wove the observations in where they fit, exactly the brief's intent.

**Copy editor count: 23 changes** — between two-call A's 32 (scaled+guardrail) and C's 20 (cap-3/4). Two `[CITATION FIX]` items in the changes: Ps 88:16 invented phrase corrected to actual singular אֵימֶיךָ; Jer 23:18 phrase corrected to actual contiguous מִי עָמַד בְּסוֹד ה׳. The hardened evidence-honesty filter prevented the failure modes it was designed for (no homophony overclaim survived discovery, no Babel/פלג signature-root claim, no invented Exodus prooftexts) — but the writer freshly introduced new overreaches (בלע/בלל "same consonants" — wrong; חצה "near-cognate" of פלג — wrong; ק-ר-ב "more than any comparable Davidic psalm" — unverified). These are writer-side errors, not seeded by the discovery output, and they confirm the filter's failure-mode coverage is sound for what it can control.

**Total cost: $5.80** (sidecar exact, from `psalm_055_cost.json`). Apples-to-apples increment over the bare writer chain: ~$2/psalm — essentially the discovery call cost. Cost compared to May-14 shipped Ps 55 baseline ($7.16, which included macro/micro/lit-echoes that this run cached): sidecar's incremental cost is similar magnitude to running lit-echoes once.

### Part 5 — Production-default invariant verified

The Session-346 rule changes (RULE 7b, RULE 8 carve-out, phrase-coverage proportionality) are untouched. With the flag OFF the writer prompt remains byte-identical to what shipped May 14. Independent of the discovery sidecar, the production path continues working exactly as it did at the end of Session 346.

**Files Modified**:

- `src/agents/synthesis_discovery.py` — **NEW** (435 lines). The discovery agent with hardened evidence-honesty filter and meta-rule.
- `src/agents/master_editor.py` — added `synthesis_discovery_file` kwarg to `write_commentary()`; new `discover_cross_verse_observations()` method; splice logic in `_perform_writer_synthesis()` (no-op on default path).
- `scripts/run_enhanced_pipeline.py` — new `--synthesis-discovery` flag; new STEP 3.5 between micro and writer; flag plumbed through `run_enhanced_pipeline()` signature.
- `docs/session_tracking/CLAUDE.md` — session header bumped to 347; new entry at top of Recent Work; Session 341 removed (kept rolling 5); new `--synthesis-discovery` quick command.
- `docs/session_tracking/scriptReferences.md` — added `synthesis_discovery.py` entry under Analysis Agents; updated `run_enhanced_pipeline.py` to mention the new flag.

**Artifacts for inspection / comparison**:

- `output/psalm_55/EXPERIMENT_synthesis_discovery/psalm_055_synthesis_discovery.md` — the 14 calibrated observations.
- `output/psalm_55/EXPERIMENT_synthesis_discovery/psalm_055_commentary.docx` — the final guide, comparable to `output/psalm_55/THREE_WAY_COMPARISON/psalm55_guide_{A,B,C}.docx`.
- `output/psalm_55/EXPERIMENT_synthesis_discovery/psalm_055_copy_edit_changes.md` — the 23 copy-editor changes (regression test set for any future filter tightening).
- `output/psalm_55/EXPERIMENT_synthesis_discovery/psalm_055_cost.json` — exact cost breakdown.
- Shipped `output/psalm_55/psalm_055_commentary.docx` and `THREE_WAY_COMPARISON/` untouched.

**Pending for next session**: run the flag on 2–3 more psalms (the brief suggested a short one like Ps 117/134, plus a long one like Ps 18 or 22) to confirm scaling at both ends before considering the flag as a production default.

---

## Session 346 (2026-05-19): RULE 7b / Phrase-Coverage Proportionality + Two-Call Synthesis Experiment

**Objective**: Investigate two Ps 54 passages the user flagged as "trivial points dressed in stilted language," diagnose where the prompt went astray, fix it, then go further and test whether a dedicated cross-verse synthesis architecture would systematically address the missing-synthesis pattern.

**Problems Identified**:

1. **Ps 54 inflation regression.** The user flagged two passages: (a) the מִסְתַּתֵּר reflexive paragraph ("the reflexive verb names David's last remaining agency in the narrative — and that agency is precisely what gets handed to Saul"), and (b) the נְדָבָה closing ("Religion at its required minimum gives what is owed; gratitude at its peak gives what was not asked for"). Both are aphoristic-inflation — a small true observation dressed in balanced, chiastic, "sounds-profound-but-restates-the-definition" prose. Diagnosis: Session 345's new **Phrase Coverage** rule combined with the pre-existing **RULE 8 absolutism** ("FORBIDDEN from stating a fact without an immediate interpretive payoff") was structurally forcing the writer to manufacture significance for routine phrases. RULE 13's "epigrammatic wit" was the available register for that manufactured significance. No rule named the aphoristic-inflation failure mode.

2. **Insight density on long psalms.** Even with the inflation fixed, the deeper question: does the pipeline maximize its capacity for genuine cross-verse syntheses? The shipped one-call writer was *good* — but the verse-by-verse commentary kept losing syntheses that lived only across multiple verses (the v.3↔v.18 שׂיח/המה mirror, the v.4↔v.23 מוט reversal, the ק-ר-ב dual-lexeme reading). The verse-by-verse format's coverage mandate rewarded cataloguing; cross-verse syntheses fell into the gap between essay (which forces ONE governing argument) and verse commentary (which forces *coverage*).

**Solutions Implemented**:

### Part 1 — Production prompt fixes (live in `src/agents/master_editor.py`)

1. **RULE 7b: NO FALSE PROFUNDITY** — added between RULE 7 (Blurry Photograph) and RULE 8. Names the failure mode explicitly: "dictionary in epigram's clothing," "tautology with a cadence," "escalating restatement," "manufactured frame" (the "X at its minimum / Y at its peak" / "not A but B" / "not a place — a pattern" structures). Includes the user's two flagged Ps 54 passages **verbatim as BLOATED counter-examples**, each paired with a CLEAN rewrite in the prompt's existing house style. Provides a strip-the-cadence test: "Read the sentence with its balance removed. Does the reader know something the plain verse did not already tell them — or only the definition of a word?" Plus matching FINAL VALIDATION CHECKLIST item.

2. **RULE 8 carve-out** — the rule was absolutist ("FORBIDDEN from stating a fact without payoff," with "explain the payoff" as the only offered remedy). Added: *"The remedy for a fact that has no real payoff is to CUT it or state it in one plain clause — NEVER to manufacture a payoff by dressing the fact in profound-sounding language (see RULE 7b). 'No orphaned facts' means *drop the orphan*, not *adopt it with a grand speech*."*

3. **Phrase Coverage proportionality option** — Session 345's "each phrase must either (a) receive a substantive analytical sentence or (b) be deferred" was over-correcting. Added option **(b): one honest proportionate sentence when the phrase is a routine construction**, with explicit instruction to NOT manufacture significance. The new framing: *"Coverage means the phrase is visible to the reader as something the commentary saw — NOT that every phrase must be made to sound profound."* Plus updated FINAL VALIDATION CHECKLIST item that flags forced inflation as a misapplication of the coverage rule.

These three changes flow through `MasterEditorSI` automatically via the shared `MASTER_WRITER_PROMPT_V4` template. **Verified on a Ps 54 re-run via the two-call experiment's Call 2 (which uses the same prompt with the new rules injected as an addendum on top of the saved May-14 prompt body):** the מִסְתַּתֵּר paragraph is now one calibrated sentence ("מִסְתַּתֵּר is reflexive — 'hiding himself,' not merely 'hidden.' The active form quietly registers that David's concealment is something he is *doing*, and it is exactly that doing the Ziphites hand to Saul"), and the נְדָבָה passage is now ("A נְדָבָה is by definition the offering no law compels — which is the point: the psalmist vows not the sacrifice he owes but one he is under no obligation to bring"). Both regressions held.

### Part 2 — Two-call synthesis architecture (experimental, discardable)

Built two standalone scripts, **deliberately not touching production code**, to test whether a dedicated cross-verse synthesis pass would address the missing-synthesis problem.

- **`scripts/EXPERIMENT_two_call_synthesis.py`** — reuses the EXACT saved production writer prompt (`output/debug/master_writer_v4_prompt_psalm_NNN.txt`) split at the `## YOUR TASK: WRITE THE COMMENTARY` marker. Call 1 = persona + ground rules + ALL inputs + custom **synthesis-discovery task** (brainstorm 8–10 candidates, adversarial novelty filter, output a structured spine of governing thesis + secondary/core syntheses with anchor-verse assignments). Call 2 = full saved prompt + live-extracted new rule text (RULE 7b, RULE 8 carve-out, phrase-coverage update from the current `MASTER_WRITER_PROMPT_V4`) + the approved spine as an addendum + instructions to build essay and verse commentary around the spine with veto license retained. Same model both calls: `claude-opus-4-7` with `effort=max`, adaptive thinking, 128k max_tokens, streaming, with retry/resume hardening (Call 2 dropped 3× on the 24-verse Ps 55 run and succeeded on attempt 4).

- **`scripts/EXPERIMENT_two_call_finalize.py`** — mirrors production STEP 5 → 5a½ → 5b → 5c → 6 (print-ready → scripture verifier with GPT-5.1 FP filter → copy editor at gpt-5.4 with citation-fix prompt → section extraction → DOCX). **All writes isolated to `output/psalm_NNN/EXPERIMENT_two_call/`**; touched only read-only production files (the existing `psalm_NNN_pipeline_stats.json` for DOCX methodology, `database/tanakh.db` for citation checks). Deliberately did NOT use `scripts/run_scripture_verifier.py` or `scripts/run_docx_only.py` — both hardcode production output paths and would overwrite shipped files.

**Iteration**:

- **Run 1 — Ps 54, 3–4 syntheses cap, no evidence-honesty guardrail.** Result: produced a strong spine including my "verb-mood migration is the plot" insight (Secondary 2) and the שֵׁם syntactic-flip reading (Secondary 1, sharper than the shipped essay's "tool→destination"). Call 2 carried the spine well: each secondary thesis developed at its anchor verse with explicit signals at touched verses. The RULE 7b regressions stayed fixed. The Arabic *ṣammata* cognate claim (Secondary 3 acoustic architecture) flagged as the confabulation-risk zone.

- **Run 2a — Ps 55, 3–4 syntheses cap, no guardrail.** The 24-verse breadth test. Result: 5 syntheses, with 2 genuinely new ones (the שׁלם v.19↔v.21 contestation; the counter-Pentateuch city reading at vv.10–12+16 including the Exod 13:22 לֹא־יָמִישׁ inversion). Lost two cross-verse moves the shipped one-call had on its own: the v.3↔v.18 שׂיח+המה mirror and the מוט reversal (the cap was discarding real syntheses). Copy editor: **20 changes**, including walking back "homophony" → "consonantal overlap" (the spine had overclaimed phonetic identity), softening "verbatim" Korah formula to "clear echo," and removing an *invented Exodus 10:3 prooftext* the writer fabricated.

- **Run 2b — Ps 55, scaled + evidence-honesty guardrail.** Removed the count cap (target: ~1 core synthesis per 3–4 verses, no ceiling, two-tier CORE/ADDITIONAL structure). Added Step 2b "Evidence-Honesty Filter" to the synthesis prompt addressing: homophony vs. consonantal overlap, echo vs. verbatim, no invented or stretched prooftexts, no "signature root" claims, match assertion strength to evidence. Result: spine produced **1 governing + 8 core + 3 additional = 12 syntheses**, recovering both syntheses the cap dropped (the שׂיח+המה mirror became the *governing* thesis; מוט reversal became Core 5). The guardrail caught the specific failure modes I named (no "homophony" overclaim; Babel handled via Gen 10:25 Peleg without claiming פלג is Babel's "signature root"; no invented Exodus 10:3 prooftext; "near-verbatim" instead of "verbatim" for Korah). **But the copy editor still made 32 changes** — the writer found *new* over-reaches the rule list didn't anticipate (חלל = "stab through" the covenant, עָמָל = "birth-labor," "prayer begins where evil cannot follow" non-sequitur, three plain counting errors — "eight movements" → "ten"; "eight words" → "five"; "the final two words" → "the closing clause"). 3 citation issues (vs cap-3/4's 1). Lesson: the synthesis pass needs a more *general* calibration principle than an enumerable list of forbidden patterns.

### Part 3 — Blind 3-way external evaluation

Assembled `output/psalm_55/THREE_WAY_COMPARISON/` with the three DOCXs randomized A/B/C and a sealed `_MAPPING_KEY.md`. Composed a structured evaluation prompt (target reader, 6 criteria, required quoted evidence, contrarian-honesty probes). User ran it through two external LLMs.

**Results**:
- **Gemini Pro Extended (first read) → picked B (shipped one-call)**: "best blend of compelling prose, illuminating literary echoes, and solid structural analysis."
- **Gemini Pro Extended (second read) → picked A (scaled+guardrail)**: "the most disciplined; A earns every single claim it makes, ensuring the reader's trust is never broken."
- **Claude Opus 4.7 → picked C (cap-3/4)**: "the ק-ר-ב insight is the largest single thing a reader will carry. The trade-off I'm accepting: B is a smoother reading experience hour-for-hour and has the most genuinely thoughtful world-literature comparisons."

**Critical finding**: **Gemini twice hallucinated a "fatal" Hebrew error in C** — claimed the source spelled the root as ב-ר-ק (*baraq*, "lightning") instead of ק-ר-ב, calling this "disqualifying." The actual file source uses ק-ר-ב correctly throughout (lines 7, 19, 123, 177, 191, 231, 252, 277 of `psalm_055_copy_edited.md` in the cap-3/4 dir). This is a BiDi (right-to-left) rendering failure mode — Gemini misread the visual order in mixed Hebrew/English text. Claude Opus 4.7 did NOT make this error and correctly recognized C's ק-ר-ב insight as the most original. The hallucination drove both Gemini reads' "Weak" trustworthiness and Hebrew-handling judgments against C; with it removed, the 3-way split remains genuine but C's substance ranking should rise.

**Convergent findings worth banking**:
- Claude caught that **all three guides over-claim the Exod 13:22 לֹא־יָמִישׁ uniqueness** ("the only other place" / "exactly one comparable formula") — Jeremiah 17:8 and Joshua 1:8 belong to the same family. The synthesis spine seeded this in A and C; B picked it up independently.
- Cross-cultural echoes are uniformly the weak spot: Manger in A, Wang Wei in B, Milton in C each flagged as decorative by at least one evaluator. The "Smiling Faces Sometimes" Motown reference appears in all three.
- The architecture's gain is *concentrated*: a small number of specific cross-verse philological moves (ק-ר-ב dual-lexeme; Exod 13:22 inversion; שׁלם contestation) that the one-call demonstrably does not surface. The prose-quality gain is not consistent.

### Part 4 — Design proposal for Session 347 (in `NEXT_SESSION_BRIEF.md`)

**Synthesis as discovery tool, not structural spine.** The two-call architecture's spine-deployment over-corrected: it forced anchored arcs, raised over-claim surface area, and produced a more "architecturally engineered" reading that two of three external evaluators ranked below the shipped one-call on prose quality. But the *insights themselves* are real and load-bearing. The fix: build a synthesis-discovery agent (`src/agents/synthesis_discovery.py`) whose output sits in the writer prompt as a sidecar `CROSS-VERSE OBSERVATIONS (use where they fit; do NOT structure your commentary around them)` block — alongside the existing `KEY INSIGHTS TO INCORPORATE` slot. Gated behind a `--synthesis-discovery` flag, default OFF, until validated on 2–3 psalms. Why this works where the old `InsightExtractor` curator didn't (it was extractive and emitted one-sentence labels; this is generative and emits full claims with per-verse Hebrew evidence). Why this works where the spine architecture over-corrected (the spine wasn't actually needed to land the insights in prose — the writer carried them wherever they belonged). Full design in `NEXT_SESSION_BRIEF.md`.

**Files Modified**:

- `src/agents/master_editor.py` — added RULE 7b, RULE 8 carve-out, STAGE 3 phrase-coverage option (b), plus two new FINAL VALIDATION CHECKLIST items (NO FALSE PROFUNDITY; updated PHRASE COVERAGE). All within `MASTER_WRITER_PROMPT_V4`.

**Files Created**:

- `scripts/EXPERIMENT_two_call_synthesis.py` — discardable two-call experiment runner.
- `scripts/EXPERIMENT_two_call_finalize.py` — discardable downstream-finalize runner with isolated paths.
- `docs/session_tracking/NEXT_SESSION_BRIEF.md` — overwritten with Session-347 design proposal (was stale from Session 337).
- `output/psalm_55/THREE_WAY_COMPARISON/` — three DOCXs (A/B/C, randomized) + sealed `_MAPPING_KEY.md`.
- `output/psalm_54/EXPERIMENT_two_call/` and `output/psalm_55/EXPERIMENT_two_call_v1_cap34/`, `output/psalm_55/EXPERIMENT_two_call/` — all experimental output, untouched production files.

**Files NOT Modified** (deliberately):

- No production pipeline runners. The experiment lives entirely in `scripts/EXPERIMENT_*.py` and writes only under `output/psalm_NN/EXPERIMENT_*/`. To discard the entire experiment: delete those two scripts and the experiment subdirs. The Session-346 production rule changes (RULE 7b, RULE 8 carve-out, phrase coverage option b) are independent and stand on their own.
- `src/agents/insight_extractor.py` was diagnosed (its filter-not-synthesizer architecture; its one-sentence-label output; its sidecar-not-spine deployment) but not touched. The Session-347 plan superseding it is in `NEXT_SESSION_BRIEF.md`.

**Verification**:

- The Ps 54 re-run (via Call 2 with the new rules injected) confirmed the מִסְתַּתֵּר and נְדָבָה regressions are fixed.
- The cap-3/4 Ps 54 review DOCX exists at `output/psalm_54/EXPERIMENT_two_call/psalm_54_TWO_CALL_commentary.docx` (the user has it).
- The Ps 55 three-way comparison is in `output/psalm_55/THREE_WAY_COMPARISON/` with sealed mapping.

---

## Session 345 (2026-05-13): Verse-Coverage + Anti-Jargon Rules in Master Writer Prompt

**Objective**: Fix two qualitative failures the user identified in the Session-344 Psalm 53 v2 output: (1) verse 2's commentary developed the נָבָל / בְּלִבּוֹ / אֵין אֱלֹקִים first half richly while letting the second half's vocabulary (הִשְׁחִיתוּ / וְהִתְעִיבוּ / עָוֶל / אֵין עֹשֵׂה־טוֹב) evaporate into a passing grammatical note; (2) the prose register slipped from "scholar at dinner" into "quarterly biblical journal" under syntactic pressure, especially in verse 6's "abrupt deixis ... deictic ruptures ... archetypal scope ... wherever the conditions obtain ... moral, not Cartesian" paragraph.

**Problems Identified**:

1. **Verse-half neglect.** RULE 10 (depth beats breadth: "choose the 1-3 angles that actually transform the reading") plus no explicit verse-coverage check were combining to license the writer to pick three angles in a verse's first clause and treat the second clause as already-handled-elsewhere. Verse 2's second half names the Flood vocabulary (שחת — Gen 6:11–12) and Levitical/Deuteronomic moral-purity vocabulary (תעב), and adds a third moral term (עָוֶל) distinct from חטא/פשע/רע. None of that lexical/intertextual material was unpacked. The phrase אֵין עֹשֵׂה־טוֹב was implicitly saved for v.4 where it recurs — but its v.2 occurrence has different work to do (it lands the second-half cascade), and that cross-reference between the two appearances is itself an analytical move that went unmade.

2. **Linguistics-jargon register slip.** The prompt's "scholar at dinner" framing (line 44) and "Authorial voice (TARGET)" example (line 235) ARE dinner-party-warm — and the model proves it can hit that register when it wants to (verse 1's "Three technical instructions stack atop the poem like rigging on a ship" is exactly the voice). But under syntactic-feature pressure, the model reaches for journal vocabulary: *abrupt deixis, deictic ruptures, archetypal scope, obtain, Cartesian*. RULE 3 ("define every technical term") only triggers on terms the writer notices are technical — and *deixis* apparently slipped past as ambient vocabulary. No checklist item enforces the dinner-party voice itself.

**Solutions Implemented**:

1. **`src/agents/master_editor.py` — `MASTER_WRITER_PROMPT_V4` — STAGE 3: VERSE-BY-VERSE COMMENTARY** (after the "Completeness" bullet at line ~347):
   - **New bullet "Phrase coverage (CRITICAL — read this twice)"**: instructs the writer to mentally list each verse's distinct phrases/clauses (typically 2-4 per verse, separated by atnach, zaqef, or semicolon in the punctuated Hebrew) before finalizing. EACH must either (a) receive at least one substantive analytical sentence, OR (b) be deliberately deferred with a brief inline pointer to the later verse where it lands (example given: *"the phrase אֵין עֹשֵׂה־טוֹב returns in v.4, where its grammar of total negation does its main work"*). The bullet explicitly names the failure mode (developing the first half through commentary + lexicon + literary echo and letting the second half evaporate) and reconciles with RULE 10: depth-beats-breadth governs WHICH phrases get *most* attention, NOT whether phrases can be skipped entirely. *"Every distinct lexical unit must be visible to the reader as something the commentary saw."*

2. **`src/agents/master_editor.py` — `MASTER_WRITER_PROMPT_V4` — new RULE 3c** (inserted after RULE 3b at line ~138):
   - **Title**: "NO LINGUISTICS JARGON — NAME THE PHENOMENON, NOT THE TECHNICAL TERM FOR THE PHENOMENON".
   - Names the offending vocabulary explicitly: **deixis, deictic, anaphora, anaphoric, cataphora, paratactic, hypotactic, telic, atelic, performative, illocutionary, semiosis, isocolon, polyptoton**.
   - Uses the user's verse 6 paragraph verbatim as the BLOATED example, with a "cinematic cut into a scene already in progress / Not a place. A pattern." rewrite as the CLEAN example. Both versions name the same phenomenon; the clean one names what the text is *doing* in plain English rather than reaching for the Greek-derived technical name.
   - Calls out two related register problems with specific substitutions: Latinate verbs (*obtain → hold, constitute → make up or are, render → make or produce, evince → show, instantiate → show up as*) and abstract nominalizations (*the foregrounding of the divine name → the poem puts God's name first; the deployment of triple negation → the verse says "no" three times*).
   - Pay-its-keep test: *"If you find yourself writing a sentence and the closest plain-English equivalent would be significantly clearer, the plain-English version IS the version."*

3. **`src/agents/master_editor.py` — `MASTER_WRITER_PROMPT_V4` — FINAL VALIDATION CHECKLIST** (added after the WIT (RULE 13) item):
   - **PHRASE COVERAGE (verse commentary)**: forces the writer to point to either an analytical sentence or a deferral pointer for every phrase in each verse.
   - **DINNER-PARTY REGISTER / READ-ALOUD TEST (RULE 3c)**: *"Mentally read each verse paragraph aloud in the voice of a brilliant professor friend talking to smart friends after dinner."* Specific flags listed (Latinate verbs, abstract nominalizations, bare linguistics jargon). The test framed not as *"is this defensible scholarship?"* but *"would I actually say this sentence to a friend over dinner?"*

**Why these particular fixes, and tradeoff acknowledgment**:

The phrase-coverage rule could theoretically tilt verses back toward bloat (more phrases covered = more sentences per verse), which the prompt has been actively fighting since the V4 unification. The "deferred with a one-line pointer" escape valve is the mitigation: when a phrase genuinely belongs in a later verse's analysis, the writer is licensed to say so in a sentence and move on. Net effect should be: phrases never silently disappear, but the verse's analytical center of gravity is still chosen.

The anti-jargon rule is pure-win in expectation, low risk. Model behavior on style rules is always somewhat probabilistic — the "scholar at dinner" framing was already there and only partially landing — but adding a *verbatim BLOATED counter-example* (the actual paragraph the user objected to) plus a paired CLEAN rewrite gives the model a concrete pattern to learn from in a way that abstract guidance has not.

**Verification plan**:

The user will re-run Master Writer onwards on Psalm 53 (instructions provided in conversation: delete `psalm_053_edited_*`, `_pre_copy_edit*`, `_copy_edit*`, `_citation_verification`, `_print_ready`, `_commentary.docx` from `output/psalm_53/`; then `python scripts/run_enhanced_pipeline.py 53 --resume --skip-questions`). Resume mode auto-skips macro / micro / literary echoes / insights (all files intact in `output/psalm_53/` and `data/literary_echoes/psalm_053_literary_echoes.txt`). Expected cost: ~$2.85 (writer + copy editor + citation filter).

**Specific things to look for in the v3 output**:
- **Verse 2**: does הִשְׁחִיתוּ now trigger the Gen 6:11–12 Flood-vocabulary intertext (וַתִּשָּׁחֵת הָאָרֶץ ... כִּי הִשְׁחִית כָּל בָּשָׂר)? Does תעב get framed as Levitical/Deuteronomic moral-purity vocabulary? Does עָוֶל get distinguished from חטא/פשע/רע? Does the v.2 vs v.4 occurrence of אֵין עֹשֵׂה־טוֹב get cross-referenced explicitly?
- **Verse 6**: does the opening paragraph still use *deixis / deictic*? Does it still use *obtain* where *hold* would work, or *Cartesian* where *a pattern* would? Or has the model produced something closer to the CLEAN rewrite that lives in the prompt?

**Files Modified**:
- `src/agents/master_editor.py` — added "Phrase coverage" bullet to STAGE 3, added RULE 3c (NO LINGUISTICS JARGON), added two new FINAL VALIDATION CHECKLIST items (PHRASE COVERAGE, DINNER-PARTY REGISTER / READ-ALOUD TEST). All three additions flow through `MasterEditorSI` automatically since the SI agent injects its directive into the same V4 template via string replacement.

**Files NOT modified** (deliberately):
- The literary-echoes pass-1 and pass-2 tier-override prompts were left untouched; today's failures were about the master writer's *handling* of source material, not about the source material itself. Session 344's loosening of quote/analysis caps (which made the 7-echoes v2 output possible) remains correct.
- No script changes; `scripts/run_enhanced_pipeline.py` resume logic already correctly auto-skips upstream steps when their output files exist, so no plumbing was required.

---

## Session 344 (2026-05-10): Improve Wit + Literary Echoes Context in Master Writer Prompt

**Objective**: Address two qualitative weaknesses in production commentary output: (1) the final essay/commentary rarely deploys gentle, dry wit even when the material rewards it, and (2) cross-cultural literary echoes are introduced too economically — author + work title + a sliver of a line — without enough context for the reader to feel the resonance.

**Reference examples supplied by the user** (gold-standard wit from prior commentaries):
- Psalm 48: *"Psalm 48 opens with the most extravagant real-estate listing in ancient literature. In the space of a single verse, it declares a modest Judahite hilltop to be יְפֵה נוֹף, ..."* — fresh modern frame ("real-estate listing") applied to ancient material with a straight face.
- Psalm 52: *"...one does not easily worship in the mode of 'Why do you boast of evil, warrior?'"* — dry litotes acknowledging the obvious.

The user's diagnosis was that wit needs to be observational and accuracy-driven (the joke is the accuracy), and that echoes need both fuller source-context (when written, under what circumstances) and fuller unfolding (3-5 sentences naming what's shared and what differs).

**Solutions Implemented**:

1. **`src/agents/master_editor.py` — `MASTER_WRITER_PROMPT_V4`**:
   - **Added RULE 13: WIT — DRY, GENTLE, SPARING.** The new rule defines the desired register (dry, observational, sober naming of something the reader hadn't quite noticed was funny or strange about the psalm), shows both user-supplied gold-standard examples with annotation explaining *why* each works, and lists explicit failure modes to avoid (stand-up comedian voice, knowing winks to modernity, jokes that need exclamation points or "spoiler alert" framing). The rationing test: *"good wit is invisible until you re-read."*
   - **Punched up the `**Your tone**` line** at the top of the prompt to reference RULE 13 explicitly (`occasionally witty in a dry and observational register (see RULE 13)`).
   - **Restructured item 12 (Cross-Cultural Literary Echoes)** from a one-paragraph hand-wave into a four-step structural pattern with a fourth iteration added during the session after reviewing v1/v2 of Psalm 53:
     1. **Set up the echo before quoting it** — name the specific psalm-element that triggered the comparison.
     2. **Frame the source itself for the reader** — date, historical/biographical context (Akhmatova writing during the Stalinist purges; Hardy on the eve of WWI; Auden's *Shield of Achilles* reimagining Homer's shield as modern atrocity; Lorca's *cante jondo* as a flamenco-derived "deep song" form), and what the source work is doing in broad strokes. *"Treat the source poet as a character whose situation matters — not just a name attached to lines."* (This bullet was added after spot-checking the v2 output revealed half the echoes still came in flat.)
     3. **Quote 3-6 lines** in original language + English — not a single half-line.
     4. **Unfold the resonance across 3-5 sentences** — formal feature shared, what differs, why the comparison enriches.
     - Explicit length permission: *"a well-handled literary echo may add 4-8 sentences to a verse's commentary. That is fine — and preferable to three rushed echoes the reader cannot feel."*
   - **Added three new FINAL VALIDATION CHECKLIST items**: WIT (RULE 13), CROSS-CULTURAL ECHOES — CONTEXT (depth + source framing), CROSS-CULTURAL ECHOES — BASICS (the original quote/anchor/insight check, kept as a separate floor).
   - The changes flow through `MasterEditorSI` automatically since the SI agent injects its directive into the same V4 template via string replacement.

2. **`docs/prompts_reference/literary echoes pass 1 - tier override.txt`** and **`pass 2 - tier override.txt`**:
   - **Quotation cap**: `2-4 lines maximum` → `4-8 lines, tight cluster`. Rationale baked into the new prose: *"downstream consumers of this document expand each echo into reader-facing prose, and they need a tight cluster to work from."*
   - **Analysis cap**: `EXACTLY 2-3 sentences` → `3-5 sentences`. New language: *"Give a downstream writer enough interpretive scaffolding to expand the echo into reader-facing prose without inventing material."*
   - All matching mentions in the output-format templates and final checklists were updated for consistency.
   - Pass 3 (verification) and Pass 4 (reconstruction) prompts were left untouched — they don't impose length caps; they preserve what came before.

**Verification — A/B comparison on Psalm 53**:

The user supplied `Psalm 53 v1.docx` (run before changes) and `Psalm 53 v2.docx` (run after). Extracted text via `python-docx`:

| Metric | v1 | v2 |
|---|---|---|
| Document length | 19,276 chars | 26,073 chars (+35%) |
| Cross-cultural echoes | 2 (Amichai v.3, Lu Xun v.5) | 7 (Lorca v.1, Stevens v.2, Hardy v.3, Auden v.4, Miller v.5, Akhmatova v.6, Farrokhzad v.7) |
| Typical source-quote length | 1-2 lines | 4-6 lines (e.g., Lorca *cante jondo* opening = 6 lines + translation; Hardy "Channel Firing" = 6 lines; Auden "Shield of Achilles" = 6 lines) |
| Setup before quote | One sentence | One to two sentences naming the trigger |
| Unfolding after quote | 1 sentence | 3-5 sentences naming shared formal feature + difference + insight |

**Wit examples that landed in v2** (in the requested register — none of these were in v1):
- *"every reader who can hear the wordplay is being invited to become what God could not find. The text positions you as the answer to its own search. (One could call this the world's most polite recruiting pitch.)"*
- *"Their hearts speak the same sentence; only their footnotes differ."*
- *"Diagnosis becomes taunt-song."*
- *"Practical atheism with imperial reach scales the damage."*
- *"The label brackets futility with confidence."*

The wit is sparingly placed (~5 distinct moments across the document, never two in the same paragraph), no stand-up voice, no exclamation-point jokes.

**Echoes that received strong source-context in v2**: Akhmatova (*Requiem*, "composed during the Stalinist purges"), Hardy ("Channel Firing" 1914, "God speaks to the dead in their graves about the gunnery practice that has woken them"), Miller (Willy Loman's situation sketched in one sentence). Echoes still thin on context (the gap that motivated adding the explicit "Frame the source itself" bullet mid-session): Lorca, Stevens, Auden, Farrokhzad — each named only with author + work title without date or thematic context. The added bullet + checklist requirement should close this gap on the next run.

**Files Modified**:
- `src/agents/master_editor.py` — RULE 13, tone-line tweak, restructured item 12 (with mid-session "Frame the source" bullet added), three new FINAL VALIDATION CHECKLIST items.
- `docs/prompts_reference/literary echoes pass 1 - tier override.txt` — quotation cap 2-4 → 4-8 lines, analysis cap 2-3 → 3-5 sentences, output-format and checklist updates.
- `docs/prompts_reference/literary echoes pass 2 - tier override.txt` — same caps relaxed in HARD CONSTRAINTS, output-format example, and final checklist.

**Verification**: `ast.parse` clean on `master_editor.py`; both `MASTER_WRITER_PROMPT_V4` and `MASTER_WRITER_PROMPT_SI` `.format()` cleanly with all expected placeholders (no rogue braces in new Hebrew quotations or example text); prompt files no longer contain the old caps. End-to-end production run on Psalm 53 produced the comparison data above.

**Open follow-ups** (not blocking):
- v2 placed all 7 echoes in verse commentary; the prompt suggests "1-2 in the essay if they fit" — consider tightening to "include at least 1 in the essay" if the next test psalm shows the same pattern.
- Confirm on a second psalm (e.g. one without 7 vivid verse-image clusters) that the wit + echo-context improvements aren't an artifact of Psalm 53 specifically.

---

## Session 343 (2026-05-05): Fix Resume-Mode Literary Echoes Model Tracking

**Objective**: Ensure "Literary Echoes" models appear in the DOCX Methodological Summary even when the pipeline is resumed and the generation step is skipped.

**Problems Identified**:
- When the pipeline was resumed, the `skip_lit_echoes` logic bypassed the model tracking calls.
- The `ResearchAssembler` did not include the Literary Echoes models in the `research_v2.md` bundle, preventing `_parse_research_stats_from_markdown` from recovering them during Step 2 skips.

**Solutions Implemented**:
1. Added explicit `tracker.track_model_for_step` calls for Passes 1-4 inside the `skip_lit_echoes` block of both `run_enhanced_pipeline.py` and `run_si_pipeline.py`.
2. Updated `_parse_research_stats_from_markdown` in both pipeline scripts to accurately parse "Literary Echoes" models from the `research_v2.md` file.
3. Modified `src/agents/research_assembler.py` to permanently inject `GEMINI_MODEL` and `GPT_VERIFY_MODEL` into the `models_used` dictionary of the `ResearchBundle`.

**Files Modified**:
- `src/agents/research_assembler.py` - Injected Literary Echoes models into the research bundle metadata.
- `scripts/run_enhanced_pipeline.py` - Added model tracking during skip and improved markdown parsing.
- `scripts/run_si_pipeline.py` - Same changes as enhanced pipeline.
- `CLAUDE.md` - Session updated.
- `docs/session_tracking/IMPLEMENTATION_LOG.md` - This entry.

---

## Session 342 (2026-04-26): API Quota Guard — Fail-Fast on Billing Exhaustion

**Objective**: Prevent silent pipeline degradation when API billing quota is exhausted — ensure immediate halt with clear notification instead of producing incomplete DOCX files.

**Problems Identified**:
- The Psalm 67 pipeline ran with an exhausted OpenAI balance. 6 of 8 pipeline steps used non-fatal `except Exception` blocks that caught `429 insufficient_quota` errors, logged warnings, and continued. The pipeline produced a final DOCX that appeared complete but was missing Literary Echoes (passes 3-4), Scripture Citation Verification, and Copy Editor processing.
- Only Step 4 (Master Writer) had a specific `openai.RateLimitError` catch — but it only detected OpenAI quota errors, not Anthropic or Google/Gemini billing exhaustion.

**Solutions Implemented**:
1. Created `src/utils/api_guard.py` — centralized quota-detection utility with three exports:
   - `is_quota_exhaustion(exc)` — inspects exception type + message to distinguish permanent billing errors from transient rate limits. Covers OpenAI (`insufficient_quota`, `billing hard limit`), Anthropic (`credit balance is too low`), and Google (`RESOURCE_EXHAUSTED` + quota language). Returns `(True, "ProviderName")` or `(False, "")`.
   - `halt_on_quota(exc, step_name, ...)` — if quota detected: saves partial cost JSON, logs clear halt message, plays 3 descending beeps via `winsound.Beep()` (Windows), exits with code 2.
   - `QuotaExhaustionError` — exception class for programmatic use.
2. Modified `scripts/run_enhanced_pipeline.py` — added `halt_on_quota()` call to all 7 `except` blocks (Steps 1b, 2b, 2c, 4, 5a½, 5b, 6). Replaced the Step 4 hand-coded `except openai.RateLimitError` with the unified utility. Removed `import openai`.
3. Applied identical changes to `scripts/run_si_pipeline.py`.
4. Created `scripts/test_api_guard.py` — 8 unit tests covering OpenAI quota, billing hard limit, transient rate limits (should NOT trigger), Anthropic credit balance, Google RESOURCE_EXHAUSTED, generic non-API errors, and the exception class. All pass.

**Files Modified**:
- `src/utils/api_guard.py` — **[NEW]** Centralized API quota detection and pipeline halt utility
- `scripts/run_enhanced_pipeline.py` — Added `halt_on_quota()` import and calls in 7 except blocks; removed `import openai` and hand-coded `RateLimitError` catch
- `scripts/run_si_pipeline.py` — Same changes as enhanced pipeline
- `scripts/test_api_guard.py` — **[NEW]** Unit tests for api_guard.py (8 tests)

**Verification**: All 3 modified files pass `ast.parse` syntax check. All 8 unit tests pass.

---

## Session 341 (2026-04-26): Investigate Psalm 67 Pipeline + Fix Resume-Mode Literary Echoes

**Objective**: Diagnose why Psalm 67's pipeline run cost only $2.43 (lower than expected), and fix a resume-mode bug that caused unnecessary Literary Echoes regeneration.

**Problems Identified**:
- Three pipeline steps failed silently due to OpenAI API `429 insufficient_quota` errors: Literary Echoes passes 3-4 (GPT-5.4), Scripture Citation Verifier (GPT-5.1), and Copy Editor (GPT-5.4). All were caught by non-fatal error handling, so the pipeline completed but produced output without copy editing or citation verification.
- The `--resume` flag in `run_enhanced_pipeline.py` correctly auto-detected and skipped Macro, Micro, and Master Writer steps, but had no awareness of Literary Echoes. Since Literary Echoes defaults to regenerate-and-overwrite, every `--resume` run re-executed the full 4-pass workflow (~$0.95, ~10 minutes) even when the output file already existed.

**Solutions Implemented**:
1. Diagnosed the cost discrepancy by examining `psalm_067_pipeline_stats.json`, `psalm_067_cost.json`, and the enhanced pipeline log. Confirmed all core steps (Macro, Micro, Master Writer) ran successfully; only the GPT-dependent downstream steps failed.
2. Added Literary Echoes skip logic to the `--resume` block in `run_enhanced_pipeline.py`: checks for `data/literary_echoes/psalm_NNN_literary_echoes.txt` and sets `skip_lit_echoes = True` if the file exists. This is scoped entirely within the `if resume` block, so full fresh runs (without `--resume`) still regenerate Literary Echoes as intended.

**Files Modified**:
- `scripts/run_enhanced_pipeline.py` — Added Literary Echoes file-existence check to the `--resume` auto-detection logic (lines 362-365).

---

## Session 340 (2026-04-25): Evaluated GPT-5.5 Pro for Master Editor

**Objective**: Integrate and evaluate the new `gpt-5.5-pro` model as the Master Editor for the Psalms AI pipeline to determine if it outperforms the Claude Opus 4.7 baseline.

**Problems Identified**:
- `gpt-5.5-pro` requires the OpenAI Responses API rather than the traditional chat completions endpoint.
- Unicode checkmarks in loggers were causing `UnicodeEncodeError` crashes on Windows.
- The massive 200,000-token input prompt with high reasoning effort triggered immense, invisible "thinking token" generation billed at output token rates, costing ~$12.60 per psalm instead of the typical ~$2.00, rapidly draining API quota.
- `CombinedDocumentGenerator` initialization changed recently, requiring all arguments in `__init__`, breaking the DOCX generation fallback in the test script.

**Solutions Implemented**:
1. Updated `scripts/run_master_editor_gpt5_5_test.py` to correctly parse outputs and utilize the standard `DocumentGenerator` instead of `CombinedDocumentGenerator`.
2. Replaced the `✓` symbol with `[OK]` in `src/agents/archive/master_editor_v2.py` logging to ensure Windows stability.
3. Extracted the successfully generated `gpt-5.5-pro` commentary output from local cache after the pipeline crashed mid-run, preventing a duplicate $12 charge.
4. Concluded that the quality of the `gpt-5.5-pro` output did not justify the 6x cost increase over Claude Opus 4.7.

**Files Modified**:
- `scripts/run_master_editor_gpt5_5_test.py` - Fixed key parsing and switched to `DocumentGenerator`.
- `src/agents/archive/master_editor_v2.py` - Fixed Unicode logging crash.

## Session 339 (2026-04-24): Surface Literary Echoes Models in DOCX + Lit Echoes Cost Subtotal in Terminal Tally

**Objective**: Ensure the DOCX "Models Used" section lists the Gemini 3.1 Pro model used for Literary Echoes passes 1 & 2 (and, by extension, the GPT-5.4 model used for passes 3 & 4), and ensure the Literary Echoes cost is visible as its own line in the pipeline's final terminal tally rather than being buried inside the per-model roll-up.

**Problems Identified**:
1. **"Models Used" section omitted Literary Echoes.** The pipeline runners already called `tracker.track_model_for_step("literary_echoes_pass_1", ...)` through `pass_4` in STEP 1b, so the keys were present in `pipeline_stats.json`. But none of the three renderers that emit the Methodological Summary (`document_generator.py`, `combined_document_generator.py`, `commentary_formatter.py`) referenced those keys — they only looked for `macro_analysis`, `micro_analysis`, `liturgical_librarian`, `figurative_curator`, `question_curator`, `insight_extractor`, `synthesis`/`master_editor`/`master_writer`, `citation_filter`, and `copy_editor`. So the Gemini 3.1 Pro attribution for the creative generation passes never made it into the final DOCX.
2. **Literary Echoes cost buried in per-model rollup.** `CostTracker.get_summary()` aggregates every API call under its model key. Since Pass 3+4 of lit_echoes use `gpt-5.4` (shared with the Figurative Curator and other GPT components) and Pass 1+2 use `gemini-3.1-pro-preview` (not used elsewhere), there was no way to read off the lit_echoes-specific cost from the terminal output without cross-referencing `output/psalm_NNN/literary_echoes/cost_report.json`.

**Solutions Implemented**:
1. In all three renderers, added two conditional lines to the "Models Used" block, placed after the existing `copy_editor` check:
   ```python
   if 'literary_echoes_pass_1' in model_usage:
       summary_text += f"\n**Literary Echoes (Passes 1 & 2 — Generation)**: {model_usage.get('literary_echoes_pass_1', 'N/A')}"
   if 'literary_echoes_pass_3' in model_usage:
       summary_text += f"\n**Literary Echoes (Passes 3 & 4 — Verify + Reconstruct)**: {model_usage.get('literary_echoes_pass_3', 'N/A')}"
   ```
   (commentary_formatter.py uses `lines.append(...)` instead of string concatenation but is otherwise identical.) Both lines are guarded by presence checks so older psalms whose pipeline_stats.json predates Session 338 still render cleanly.
2. In both pipeline runners, introduced a `lit_echoes_cost = 0.0` local variable right after `cost_tracker = CostTracker()`, set it to `lit_result.total_cost` inside STEP 1b's try block (only on success, so a failure leaves it at 0), and printed the subtotal after `cost_tracker.get_summary()`:
   ```python
   if lit_echoes_cost > 0:
       print(f"Literary Echoes subtotal (Passes 1-4): ${lit_echoes_cost:.4f}")
       print("  (already included in the grand total above — shown separately "
             "because pass costs are lumped with other uses of gemini-3.1-pro-preview / gpt-5.4)\n")
   ```
   The subtotal is sourced from `lit_result.total_cost` (summed from all 4 `PassResult` objects using their recorded token counts) rather than a re-query of the cost_tracker, so the number is authoritative for the lit_echoes agent itself.

**Files Modified**:
- `src/utils/document_generator.py` — Added two conditional lines to the Models Used section of `_format_bibliographical_summary`'s caller (around L1864-1867).
- `src/utils/combined_document_generator.py` — Same two lines (around L1777-1780).
- `src/utils/commentary_formatter.py` — Same two lines in the markdown formatter (around L271-274).
- `scripts/run_enhanced_pipeline.py` — Declared `lit_echoes_cost = 0.0` near the cost_tracker init, captured `lit_result.total_cost` in STEP 1b, printed subtotal after `cost_tracker.get_summary()`.
- `scripts/run_si_pipeline.py` — Same three changes mirrored from the enhanced pipeline.

**Verification**: `python -c "import ast; ast.parse(...)"` on all 5 edited files returned clean. No new scripts created; no changes to pipeline step ordering or to the `LiteraryEchoesAgent` itself.

---

## Session 338 (2026-04-23): Built `lit_echoes` Agent — Automated 4-Pass Literary Echoes in the Pipeline

**Objective**: Replace the manual Gemini-web 4-pass literary-echoes workflow with an automated in-pipeline agent that (a) solves the cross-psalm author-repetition problem via a rolling exclusion list, (b) integrates into both `run_enhanced_pipeline.py` and `run_si_pipeline.py` as a default-on step, and (c) can also be run standalone for a single psalm.

**Design decisions**:
1. **Per-pass model assignments** (final, after live testing on Psalm 53):
   - Pass 1 (generation): Gemini 3.1 Pro (`gemini-3.1-pro-preview`), `thinking_budget=24000`.
   - Pass 2 (gap-fill): Gemini 3.1 Pro, same thinking budget. Target bumped 3-6 → 5-10 new comparisons.
   - Pass 3 (verification): GPT-5.4 via **Responses API** with `tools=[{"type":"web_search_preview"}]` — real web lookups with inline citation URLs returned in the verification notes.
   - Pass 4 (reconstruction): Originally spec'd as `gpt-5.1` for cheapness; had to switch to `gpt-5.4` (see bug (1) below). Chat Completions API, `reasoning_effort="medium"`, `max_completion_tokens=32000`.
2. **Exclusion scan** = last 4 files by mtime (NOT by psalm number) in `data/literary_echoes/`, excluding the current psalm's own file. Authors extracted via `^####\s+([^,\n*]+?)\s*,` regex and deduped case-insensitively.
3. **Default behavior is regenerate-and-overwrite.** `--skip-lit-echoes` on the pipeline, or `--skip-if-exists` on the standalone runner, preserves the existing file.
4. **Non-fatal on failure**: downstream `research_assembler._load_literary_echoes` already tolerates a missing file, so any Gemini/GPT failure logs a warning and the pipeline continues.

**Problems Identified and Fixed During Testing on Psalm 53**:
1. **`gpt-5.1` self-terminated at every `reasoning.effort` on the 30K-char Pass 4 prompt.** At `minimal` the API rejects the value outright (`gpt-5.1` supports `{none, low, medium, high}`, not `minimal`). At `low`, `medium`, and `high`, the model produced only the first verse cluster (~800 chars) then stopped. Separately, the Responses-API content filter flagged the combined multilingual religious/literary Pass 4 input as `incomplete_details.reason='content_filter'` with zero usage tokens. Resolution: switched Pass 4 to `gpt-5.4` via `client.chat.completions.create` (no content-filter rejection, produces the full 14K-char reconstruction reliably). Net cost ~$0.04 higher per psalm — acceptable.
2. **Pass 2 used canonical-slot authors already on the exclusion list.** Aeschylus and Paul Celan appeared in both Psalm 53's output and in the 45-author exclusion block built from Psalms 49-52. Pass 2 picked them as Earned Canonical Slot choices because the exclusion block was only being injected into Pass 1. Fixed by also injecting the exclusion block into Pass 2's prompt, with explicit language: "This applies even to Earned Canonical Slot authors — if a canonical-slot author appears below, skip them and pick a different second-tier voice." The Psalm 53 test output still has those two names; the fix applies on next run.

**Solutions Implemented**:
1. Built `src/agents/literary_echoes_agent.py` with:
   - `LiteraryEchoesAgent.generate(psalm_number, psalm_output_dir, skip_if_exists)` orchestration method returning a `LiteraryEchoesResult` with per-pass `PassResult` entries (model, in/out/thinking tokens, cost, elapsed).
   - Gemini client via `google-genai` (same pattern as `synthesis_writer.py`). OpenAI client via the standard SDK. `load_dotenv()` at module top.
   - Exponential backoff retry (3 attempts) on 429/rate/5xx errors for Gemini.
   - Prompt builders that substitute `{NUMBER}` and `[PSALM FULL TEXT]` in Pass 1, and prepend psalm + prior-pass outputs to Pass 2/3/4 templates.
   - Per-pass cost calculated from pricing in `cost_tracker.py` (Gemini 3.1 Pro: $2/$12/$12; GPT-5.4: $2.50/$15/$15) and also pushed into the shared `CostTracker` so the psalm-level `cost.json` picks it up.
   - Per-psalm output artifacts written to `output/psalm_NNN/literary_echoes/`: `pass_{1,2}_raw.txt`, `pass_3_verification.txt`, `pass_4_final.txt`, `exclusion_list.txt`, `cost_report.json`, and `gemini_prompts/pass_{1,2,3,4}_full.txt` (exact resolved prompts). Final file also copied to canonical `data/literary_echoes/psalm_NNN_literary_echoes.txt`.
2. Created `scripts/run_literary_echoes.py` — standalone runner with `--skip-if-exists`, `--output-dir`, `--db-path` flags. Prints per-pass cost breakdown at the end.
3. Wired new **STEP 1b** into both `scripts/run_enhanced_pipeline.py` and `scripts/run_si_pipeline.py` between Macro (STEP 1) and Micro (STEP 2). Added `--skip-lit-echoes` CLI flag and `skip_lit_echoes: bool = False` to the pipeline function signatures. STEP 1b is `not skip_lit_echoes and not smoke_test`, wrapped in try/except so a Gemini/GPT failure logs a warning but doesn't halt the pipeline. Models registered with the pipeline tracker so per-pass costs show up in the psalm summary.
4. Edited `docs/prompts_reference/literary echoes pass 1 - tier override.txt` and `literary echoes pass 2 - tier override.txt`:
   - Removed Kendrick Lamar from the "Earned Canonical Slots" allowlist.
   - Added Kendrick Lamar to the fully-banned list (previously: Homer, Dante, Virgil, Ovid).
   - Swapped the hip-hop palette anchor from "past Kendrick" to "past Jay-Z / Tupac" (kept the second-tier alternatives: Mos Def, Rakim, Nas, Ghostface, MF DOOM, Jean Grae, Saul Williams, Gil Scott-Heron, The Last Poets).
   - Added an "Offensive-Language Filter" hard-constraint block — deliberately narrow: only the three most-severe four-letter words (sex act, excrement, female anatomy) and direct cognates/slurs. Explicitly allows historical mild scatology (Rabelais, Chaucer, Luther's "Scheisse", "damn", "hell", "piss", "ass" as mild insult).
   - Updated both final-checklist sections with the new constraint lines.
   - Pass 2: target comparison count bumped from 3-6 to 5-10.
5. Edited `docs/prompts_reference/literary echoes pass 3.txt`: added a "PROFANITY FILTER" section instructing the verifier to flag quotations containing severe profanity as ❌ (so Pass 4 strips them) or 🔄 (if a sanitized radio-edit version exists).
6. Archived three pre-tier-override templates via `git mv` to `docs/prompts_reference/archive/` for provenance: the original non-tier-override Pass 1, 2, 4 templates renamed with "(pre-tier-override)" suffixes. (The tier-override versions are now canonical; `docs/prompts_reference/literary echoes pass 3.txt` stays in place — it's the only Pass 3 template.)

**Live test on Psalm 53** (clean run, no existing file preserved):
- Exclusion scan found 45 unique authors from Psalms 52, 51, 50, 49 (sorted by mtime).
- Pass 1: 142.8s, $0.2153 (4,630 in / 4,296 out / 12,871 thinking).
- Pass 2: 95.0s, $0.1600 (7,823 in / 1,524 out / 10,509 thinking).
- Pass 3: 280.4s, $0.4585 (114,232 in / 11,525 out / 9,403 reasoning — note the 114K input is from web-search tool results injected into context).
- Pass 4: 85.6s, $0.1107 (9,713 in / 5,759 out / 1,635 reasoning).
- **Total: ~10 minutes, $0.9445.**
- Final output: 7 verse clusters (53:1 through 53:7), 21 authors, 14,193 chars. Zero Homer/Dante/Virgil/Ovid/Kendrick. All `*Default bypassed:*` lines stripped. Pass 2 audit paragraph stripped. All ✅/⚠️/❌/🔄 verification markers stripped. No severe profanity.
- Pass 3's web search actually caught a real fabrication: the Moyshe-Leyb Halpern quotation Pass 1 produced couldn't be verified in searchable sources — flagged ❌ and stripped by Pass 4. Also corrected Dunash ben Labrat's Hebrew wording (`שִׁמְכֶם` → `שִׁירְכֶם`), Randy Newman's lyric phrasing, Różewicz's Polish (`słowami` → `wyrazami`), and the Lucretius line number.
- Cross-psalm diversity visibly improved: traditions represented include Greek, Persian, Arabic, Polish, Spanish, Chinese, American prose, reggae, musical theater, medieval Andalusian Hebrew, modern Hebrew (Rachel Bluwstein), German (Celan).

**Files Modified / Created**:
- `src/agents/literary_echoes_agent.py` — NEW, 490 lines. Main agent.
- `scripts/run_literary_echoes.py` — NEW. Standalone runner.
- `scripts/run_enhanced_pipeline.py` — added import, STEP 1b, `--skip-lit-echoes` flag, `skip_lit_echoes` param threading.
- `scripts/run_si_pipeline.py` — same changes as enhanced pipeline.
- `docs/prompts_reference/literary echoes pass 1 - tier override.txt` — Kendrick ban + profanity filter + checklist updates.
- `docs/prompts_reference/literary echoes pass 2 - tier override.txt` — same edits + target 3-6 → 5-10.
- `docs/prompts_reference/literary echoes pass 3.txt` — added profanity-flag instruction.
- `docs/prompts_reference/archive/literary echoes pass {1,2,4} (pre-tier-override).txt` — MOVED via `git mv`.
- `docs/prompts_reference/literary echoes pass 4 - tier override.txt` — unchanged (used as-is by agent).

**Open risks for future sessions**:
- The exclusion-list regex (`^####\s+([^,\n*]+?)\s*,`) assumes all final outputs keep the "#### Author, *Work* (date)" convention. If Pass 4 ever emits an author block without a trailing comma (e.g., just "#### Author (date)"), that author will not be captured in future exclusion scans.
- GPT-5.4 Responses API `web_search_preview` tool is still "preview" — if it's deprecated or the content-filter behavior tightens, Pass 3 may need to switch to a different provider or drop web search.
- Pass 3 cost is dominated by input ($0.2856 of $0.4585 on Psalm 53). If this becomes too expensive across 150 psalms (~$70 just for Pass 3), downgrading to `gpt-5.1` via Responses API is possible but tested-likely to hit the same content-filter problem that forced the Pass 4 switch. User asked about this at end of session and we explicitly left Pass 3 on `gpt-5.4` for reliability.

---

## Session 337 (2026-04-22): Tier-Override Prompts for Literary Echoes + Plan for `lit_echoes` Agent

**Objective**: Diagnose the monotony problem in the literary echoes outputs (Baudelaire, Cohen, Halevi, Amichai, Dylan, Celan, Molodowsky, Kendrick recurring across almost every psalm), design a prompt-level fix, test it, and decide next steps.

**Problem Diagnosed**:
- Pass 1 and Pass 2 prompts named the repeating poets as examples ("Hebrew poetry — e.g. Halevi, Amichai, Molodowsky…", "song lyrics — e.g. Dylan, Cohen, Cave, Kendrick…"). Cross-checking usage data against the prompt text showed every heavy repeater was an example. The prompts were self-anchoring to the same names across every run — the model was doing exactly what it was told.
- Compounding: LLM training-data gravity pulls toward famous names (Baudelaire 7/10, Shakespeare 5/10, Aeschylus 4/10) even when not named in the prompt.

**Solutions Implemented**:
1. Designed a "tier-override" prompt approach attacking three distinct mechanisms:
   - **The Second Echo Principle** — explicit framing that the first name to surface is the reflex to bypass, the second name is the target.
   - **Default Moves to Avoid** — 15 named reflex pairings (Rilke for awe, Cohen for Davidic psalms, Amichai for Jerusalem, Celan for catastrophe, Kendrick for judgment, etc.) so the model recognizes its own reflex.
   - **Earned Canonical Slots** — 15 named heavy-repeater poets soft-capped at 2 combined uses across Pass 1 + Pass 2, usable only for genuinely uncanny fits.
   - **Tier-specification palette** — 18 traditions with explicit "past X → try these" redirections (e.g., American theater: past Shakespeare/O'Neill → Miller, Williams, Kushner, Parks, Churchill; hip-hop: past Kendrick → Mos Def, Rakim, Nas, MF DOOM, Saul Williams, Gil Scott-Heron).
   - **`*Default bypassed:*` cognitive-forcing line** required per verse cluster — model must explicitly name the canonical reflex it's avoiding. Pass 4 strips these lines before final output.

2. Created three new prompt templates at `docs/prompts_reference/`:
   - `literary echoes pass 1 - tier override.txt` (generation, 12-18 comparison target)
   - `literary echoes pass 2 - tier override.txt` (gap-fill, opens with a quota audit; enforces combined Pass 1+2 Earned Canonical Slot cap ≤ 2)
   - `literary echoes pass 4 - tier override.txt` (final reconstruction; strips `*Default bypassed:*` scaffolding and the Pass 2 audit block)
   - Pass 3 (verification) not modified — style-agnostic.

3. Split the Hebrew/Yiddish quota into two separate constraints: ≥1 medieval Hebrew/Andalusian + ≥1 modern Hebrew or Yiddish. Prevents a single Yiddish poem from satisfying the whole Hebrew slot.

4. Bumped target comparison count from 8-14 to 12-18 to compensate for higher Pass 3 rejection risk when the model is pushed past its training-data comfort zone.

**Testing** (manual, Gemini 3.1 Pro web UI — Pass 1 only):
- Ran on Psalms 48, 49, 50, 52. Compared side-by-side to existing old-prompt outputs.
- **Within-psalm variety**: dramatically improved. 13-14 authors per psalm vs 9-12 old. Non-Anglo-European-Hebrew representation (Persian, Chinese, Hindi, Arabic, Hungarian, Polish, Peruvian, Urdu, Yoruba…) went from near-zero to consistent and plural.
- **Aptness**: subjectively better on most verse clusters. Standout picks: Li Qingzhao's imperative to the wind for the Tarshish fleet (Ps 48:7-8); Różewicz's "I saw: / carts of chopped-up people" against "what we heard we have witnessed" (Ps 48:9); Zbigniew Herbert's "carry the city within himself on the roads of exile" for the walk-around-Zion verse (Ps 48:13-15); Rivka Miriam's "I put on the city, walls upon walls" (same cluster); Nicanor Parra's "God doesn't need your alms, just don't bust His balls" for the hungry-God mockery (Ps 50:12-13); Agi Mishol's "swollen liver of the geese" for the sacrifice rejection (same verse); Lu Xun's "eat people!" scrawled over Confucian morality for the covenant-hypocrite verse (Ps 50:18-20); Celan's "Psalm" ("Gelobt seist du, Niemand") as an earned canonical slot for Ps 50:21-23.
- **`*Default bypassed:*` lines worked as designed**: the labels (Shelley/Ozymandias, Keats/Grecian Urn, Rilke/First Elegy, Molière/Tartuffe, Calvino/Invisible Cities) were exactly the authors the OLD Pass 1 actually picked. Confirms the cognitive-forcing is doing real work, not just decorative.
- **Cross-psalm second-tier repetition emerged**: across just 3 new psalms (48, 49, 50), 7 authors repeated in 2 of 3 — Faiz Ahmed Faiz, César Vallejo, Abraham Ibn Ezra, Kabir, Saadi Shirazi, Frederick Douglass, Thomas A. Dorsey. The old first-tier canonical-gravity problem (Baudelaire 7/10, Cohen 7/10) was eliminated, but a new second-tier pattern is forming at a comparable rate. This confirms the session-start hypothesis: **prompt-craft moves the center of mass but cannot solve cross-psalm memory** — the model has no knowledge of what it used in the previous psalm.

**Plan pivot at end of session**:
- Original plan: build a standalone Python script that generates per-psalm prompts with exclusion lists, for the user to paste manually into Gemini (manual workflow).
- User decided to pivot: **incorporate the full 4-pass literary echoes workflow into the main pipeline as a `lit_echoes` agent** using Gemini 3.1 Pro API. Rolling exclusion from last N=4 psalms. Per-pass raw outputs logged separately for debuggability.
- Session 338 brief with full design and testing plan written to `NEXT_SESSION_BRIEF.md`.

**Also applied**: bumped Earned Canonical Slot cap from 1 → 2 (combined Pass 1 + Pass 2) in response to user feedback that single slot was too restrictive.

**Files Modified**:
- `docs/prompts_reference/literary echoes pass 1 - tier override.txt` (created)
- `docs/prompts_reference/literary echoes pass 2 - tier override.txt` (created)
- `docs/prompts_reference/literary echoes pass 4 - tier override.txt` (created)
- `docs/session_tracking/NEXT_SESSION_BRIEF.md` (rewrote with Session 338 plan)

**No code changes this session.** All work was prompt design and evaluation. Agent implementation deferred to Session 338.

---

## Session 336 (2026-04-21): Stabilize Aptos Fonts and Methodology Summary for DOCX

**Objective**: Strictly differentiate primary verse headings from inline Hebrew quotes to stabilize font rendering, and fix missing methodology pages on manual DOCX generation runs.

**Problems Identified**:
- Because Psalm 51 dropped the explicit *sof-pasuq* marker at the end of verses, the structural verse headings (6+ words) were incorrectly captured by the generic _split_long_hebrew_block chunker, forcing verses that should be rendered in Aptos into Times New Roman.
- The DOCX-only regeneration script mistakenly pointed to a deprecated file summary.json instead of the current pipeline_stats.json, causing the Methodology page to silently strip from manually regenerated documents.
- The previous text-based heuristic for distinguishing standalone inline quotes from primary verse headings broke consistently for multi-line LLM outputs.

**Solutions Implemented**:
1. Corrected scripts/run_docx_only.py to point to pipeline_stats.json, then gracefully fallback to summary.json if missing. 
2. Set up an explicit Boolean typing chain (is_verse_commentary -> is_verse_header) cascading down from _parse_verse_commentary to precisely target primary commentary block verse headings.
3. Updated _add_hebrew_block_paragraph to conditionally support an Aptos override if triggered by the flag.

**Files Modified**:
- scripts/run_docx_only.py - Pointed summary_json_file correctly to pipeline_stats.json.
- src/utils/document_generator.py - Rewrote logic across _add_hebrew_block_paragraph, _add_paragraph_with_soft_breaks, and _add_commentary_with_bullets to programmatically protect primary verses in Aptos.
---

## Session 335 (2026-04-21): Complete Fix Hebrew Verse Punctuation Alignment in DOCX

**Objective**: Complete the fix for Word BiDi rendering issue where trailing punctuation on verses erroneously appeared on the visual right edge, which still affected short continuous verses without sof-pasuq.

**Problems Identified**:
- In the previous session, although _is_hebrew_dominant was used to ensure LRO reverse parsing was applied for short inline verses, this check was critically missing in the _add_paragraph_with_soft_breaks handler function in document_generator.py and across multiple methods in combined_document_generator.py. This caused short formatting verse blocks like Ps 51:1 (3 words) to bypass reverse processing and leak punctuation to the wrong visual side.

**Solutions Implemented**:
1. Added or self._is_hebrew_dominant(line) inside the primary Hebrew check loop of _add_paragraph_with_soft_breaks within document_generator.py, effectively resolving the placement of trailing periods on brief verse extracts.
2. Formally propagated the _is_hebrew_dominant logic across the same parallel formatting functions in combined_document_generator.py to ensure cross-generator formatting stability.

**Files Modified**:
- src/utils/document_generator.py
- src/utils/combined_document_generator.py

---

## Session 334 (2026-04-21): Fix Hebrew Verse Punctuation Alignment in DOCX

**Objective**: Resolve a Word BiDi rendering issue where trailing punctuation on verses erroneously appeared on the visual right edge.

**Problems Identified**:
- Trailing periods on native RTL block paragraphs (long verse quotes) were visually rendering on the right side because Word natively parses punctuation without an explicit semantic direction sequence into neutral placement.
- Trailing periods on LTR short verse paragraphs were visually rendering on the right side because they bypassed `_is_hebrew_dominant` formatting blocks due to lacking the `sof-pasuq`, sending them to the legacy bare-Hebrew chunker which left trailing punctuation outside the reversing Left-To-Right Override block.

**Solutions Implemented**:
1. Added explicit RLM (`\u200F`) injection to `_add_hebrew_block_paragraph` when text trails in periods, colons, or semicolons, anchoring trailing dots natively to the left edge inside RTL paragraphs.
2. Modified the formatting sub-parser in `_add_nested_formatting_with_breaks` to check `_is_hebrew_dominant(part)` exactly like `_process_markdown_formatting` does, so standalone verses missing sof-pasuq uniformly reverse their textual strings completely instead of piecemeal.
3. Created `scripts/run_docx_only.py` to allow isolated regeneration of Word documents without re-running earlier pipeline modules like the Copy Editor.

**Files Modified**:
- `src/utils/document_generator.py` - Fixed punctuation and LRO bugs for rendering verse blocks and added `_is_hebrew_dominant` logic to the internal nested format loop.
- `scripts/run_docx_only.py` - New generic DOCX-only executor created for fast output iteration.

---

## Session 333 (2026-04-21): Verified Psalm 51 Pipeline Fixes

**Objective**: Verify that the Session 332 fixes properly addressed the Psalm 51 pipeline truncation and figurative curator issues.

**Solutions Implemented**:
1. Monitored the end-to-end processing of Psalm 51 (`scripts/run_enhanced_pipeline.py 51 --skip-macro`).
2. Confirmed that the `max_tokens=128000` increase on the Master Writer gave enough budget for Opus 4.7 to generate the full commentary for all 21 verses without the verse 8 truncation issue.
3. Verified the `cost_tracker` initialization fix in the `ResearchAssembler`, which restored the `FigurativeCurator`. This eliminated 82K characters of raw instance data from the research bundle and successfully restored the curated per-vehicle breakdown within the generated pipeline stats and the final DOCX methodology section.

**Files Modified**:
- (No code modifications this session; verified previous fixes)

---

## Session 332 (2026-04-21): Fix Psalm 51 Pipeline — Curator Bug, Token Limit, Input Bloat

**Objective**: Diagnose and fix three interconnected issues causing Psalm 51's truncated verse commentary, missing figurative vehicle breakdown, and inflated Master Writer input size.

**Problems Identified**:
- **Truncation**: Master Writer (Claude Opus 4.7 with adaptive thinking + max effort) hit the hard `max_tokens=64000` ceiling. ~34K tokens consumed by internal reasoning left insufficient budget for the full 21-verse commentary, causing a hard cutoff mid-sentence during verse 8.
- **Curator regression (Session 327)**: Commit `04b78e8` (April 18) changed `FigurativeCurator(verbose=False)` to `FigurativeCurator(verbose=False, cost_tracker=self.cost_tracker)` in `research_assembler.py:720`. But `self.cost_tracker` was never assigned as an instance attribute — the `cost_tracker` parameter is a local variable. This raised `AttributeError`, caught silently by the `try/except` block, disabling the curator for ALL pipeline runs since Session 327.
- **Input bloat**: Without the curator, raw figurative instances (118K chars) replaced curated output (36K chars) — **+82K chars** of prompt bloat. This inflated the Master Writer input from an expected ~280K to 407K chars, making token limit exhaustion much more likely.
- **Missing figurative breakdown**: `figurative_parallels_reviewed` in `pipeline_stats.json` was empty because the curator (which populates it) never ran. The bibliographical summary showed `120 total instances` but no per-vehicle breakdown.

**Root Cause Timeline**:
- March 28: Psalm 50 ran fine — curator created as `FigurativeCurator(verbose=False)` (no cost_tracker)
- April 18 (Session 327): commit added `cost_tracker=self.cost_tracker` — `AttributeError` → curator silently disabled
- April 21: Psalm 51 ran without curator → raw data flooded prompt → token limit hit → truncation

**Solutions Implemented**:
1. **Curator bug fix** (`research_assembler.py:720`): Changed `self.cost_tracker` → `cost_tracker` (use local parameter instead of non-existent instance attribute).
2. **Token limit increase** (`master_editor_v2.py:2204`): Changed `max_tokens` from `64000` to `128000`. Opus 4.7 supports up to 128K output tokens; this provides sufficient budget for both extended thinking and full verse commentary even for long psalms.

**Files Modified**:
- `src/agents/research_assembler.py` — Line 720: `self.cost_tracker` → `cost_tracker` (curator init fix)
- `src/agents/archive/master_editor_v2.py` — Line 2204: `max_tokens: 64000` → `128000`

**Verification Plan**: Re-run Psalm 51 pipeline with `--skip-macro` (triggered during this session). Expected:
- Research bundle contains `## Figurative Language Insights (Curated)` (not raw instances)
- Research bundle size drops from ~394K to ~280-300K
- Master Writer output covers all 21 verses without truncation
- `figurative_parallels_reviewed` populated with per-vehicle counts
- Bibliographical summary shows vehicle breakdown

---

## Session 331 (2026-04-19): Opus 4.7 Prompt Polish — Parenthetical Translations + Stray Quotes Around Hebrew

**Objective**: Stop Opus 4.7 from wrapping every English translation in parentheses (e.g., `אַל־יֶחֱרַשׁ ("let Him not be silent")`) — a regression vs. Opus 4.6 — and eliminate stray straight quotes around long Hebrew citations that orphan visually in DOCX output.

**Problems Identified**:
- After the Session 325 switch to Opus 4.7 as Master Writer, every Hebrew quotation in Psalm 50's output had its English translation in parens (`Hebrew ("English")`). Opus 4.6 hadn't done this. User preference: English in parens ONLY when the whole Hebrew+English unit is itself a parenthetical aside.
- Root cause: `MASTER_WRITER_PROMPT_V4` Rule 1 "CORRECT examples" at `master_editor.py:60-63` inconsistent — line 61 used the comma pattern (`Hebrew, "English"`) but lines 62-63 used the parens pattern (`Hebrew ("English")`). Opus 4.7 pattern-matched on the examples literally; Opus 4.6 inferred the intent better from adjacent language like "Use Hebrew as a parenthetical anchor."
- Related bug: Opus 4.7 sometimes wraps long Hebrew citations in straight double quotes (e.g., `"רָם וְנִשָּׂא דִּבֶּר וַיִּקְרָא אָרֶץ מְלֹא כָל הָאָרֶץ"`). In DOCX, BiDi line-wrapping often sets long Hebrew on its own line, orphaning the quotes as floating marks before and after the Hebrew block.
- Confirmed via `output/debug/master_writer_v4_response_psalm_50.txt` that the parentheses come straight from the Master Writer — not introduced by the Copy Editor.

**Solutions Implemented**:
1. **Rewrote Rule 1 in `MASTER_WRITER_PROMPT_V4`** with an explicit **Parentheses Rule (CRITICAL)** section that offers three acceptable patterns and explicitly forbids the Opus-4.7 default:
   - **Pattern A — FLOWING** (preferred for mid-sentence embedding): English in quotes in main clause, Hebrew in parens as anchor — e.g., `The plea "let Him not be silent" (אַל־יֶחֱרַשׁ) is the psalm's ironic engine.`
   - **Pattern B — APPOSITION**: `Hebrew, "English," ...` — e.g., `The psalm ends with יֵשַׁע אֱלֹקִים, "the salvation of God."`
   - **Pattern C — WHOLE UNIT PARENTHETICAL**: `(Hebrew, "English")` — used only when the apposition is genuinely an aside; no nested parens.
   - Added a rhythm test: "Read the sentence aloud with the Hebrew removed. If you have a stranded `("...")` fragment, you've defaulted to the forbidden annotation style — rewrite as A or B."
   - Rule covers Greek (LXX), Aramaic, Latin translations too.
2. **Added explicit "Never wrap source text in quotation marks" rule** to Rule 1 with a correct/incorrect pair using the Psalm 50 Kedushah example. The source script is already visually distinct; surrounding quotes orphan under BiDi line-wrapping.
3. **Fixed two matching STRONG examples** at `master_editor.py:306, 317` that still showed `Hebrew ('English', Deut 15:8)` — rewrote as `Hebrew, 'English' (Deut 15:8)`.
4. **Added `CopyEditor._strip_quotes_around_source_text`** static method (`copy_editor.py:742`) — regex strips matched-pair straight or curly quotes when the body contains at least one Hebrew (U+0590-U+05FF) or Greek (U+0370-U+03FF, U+1F00-U+1FFF) letter AND no ASCII Latin letters. Rejects mismatched pairings (e.g., `"` opening with `'` closing) to avoid false positives.
5. **Wired into `edit_commentary` as step 7b** (`copy_editor.py:323-329`) — runs after diff generation but before saving, so the copy-edit diff stays clean and shows only substantive LLM edits, not deterministic cleanup. Logs strip count.
6. **Archived `master_editor_v2.py` also updated** (`MASTER_EDITOR_PROMPT_V2`, `COLLEGE_EDITOR_PROMPT_V2`, `MASTER_WRITER_PROMPT`, `COLLEGE_WRITER_PROMPT`) for consistency even though those prompts are no longer wired into the production pipeline (production uses `master_editor.py:MASTER_WRITER_PROMPT_V4`, and `master_editor_si.py` inherits via `.replace()`).

**Verification**:
- Regex tested against 5 representative inputs:
  - ✓ Strips `"רָם וְנִשָּׂא...הָאָרֶץ"` (Psalm 50 Kedushah case)
  - ✓ Strips `"θεὸς θεῶν κύριος"` (pure Greek)
  - ✓ Strips `("אֱלֹקִים")` when Hebrew sits inside parens
  - ✗ Leaves `"I love יְהוָה"` untouched (mixed script)
  - ✗ Leaves `יֵשַׁע אֱלֹקִים, "the salvation of God"` untouched (Pattern B — English is what's quoted)
- User declined to re-run Psalm 50 for verification — effects will show on next pipeline run.

**Files Modified**:
- `src/agents/master_editor.py` — Rewrote Rule 1 in `MASTER_WRITER_PROMPT_V4` with the Parentheses Rule (3 patterns) + "never wrap source text in quotes" rule; fixed 2 STRONG examples at lines 306 and 317.
- `src/agents/copy_editor.py` — Added `_strip_quotes_around_source_text` static method; wired as post-processing step 7b in `edit_commentary`.
- `src/agents/archive/master_editor_v2.py` — Same Parentheses Rule applied to `MASTER_EDITOR_PROMPT_V2`, `COLLEGE_EDITOR_PROMPT_V2`, `MASTER_WRITER_PROMPT`, `COLLEGE_WRITER_PROMPT` for consistency (archived file, not in production path).

---

## Session 330 (2026-04-19): Concordance Entries Breakdown in DOCX Methods Section

**Objective**: Add per-query breakdown to the "Concordance Entries Reviewed" line in the DOCX methods section, matching the existing format used by "Figurative Concordance Matches Reviewed."

**Solutions Implemented**:
1. **Concordance breakdown string**: In all 3 formatters, replaced the bare total with a total + parenthesized per-query breakdown. Reads from `concordance_results` in `pipeline_stats.json` (dict of `query → count`). Filters out the legacy `total_results` key (used by older pipeline runs that didn't store per-query data). Output format: `13 (אלהי מעוזי (1); הר קדשׁך (3); ...)`.
2. **Divine names modifier**: All concordance search terms are now passed through `self.modifier.modify_text()` before display, ensuring divine names like יהוה are properly modified in the methods section output.
3. **Backward compatibility**: Legacy stats files (Psalms ≤42, 50) that only have `{"total_results": N}` display just the total with no breakdown — same as before.

**Files Modified**:
- `src/utils/document_generator.py` — Added concordance breakdown with divine names modification (single-psalm DOCX)
- `src/utils/combined_document_generator.py` — Same change (combined main+college DOCX)
- `src/utils/commentary_formatter.py` — Same change (markdown print-ready formatter)

---

## Session 328 (2026-04-18): Fix Displaced-Liturgical-Content Recovery for Opus 4.7 Headers

**Objective**: Diagnose and fix a Psalm 50 DOCX formatting bug where "Key verses" liturgical entries were misplaced under the verse-by-verse commentary section after the Opus 4.7 Master Writer upgrade.

**Problems Identified**:
- Psalm 50 DOCX showed the `Modern Jewish Liturgical Use → Key verses` subsection empty except for a one-sentence intro, while the bold `**Verse 1** (...) appears in Ashkenazi Yom Kippur...` entries (and 5 more like it) appeared above the first real verse commentary, rendered by the DocumentGenerator as a bogus "Verse 1" header with no content.
- Root cause traced through the pipeline: Master Writer output (Opus 4.7) places the entries correctly in the intro. Print-ready file preserves the structure. **Copy Editor displaces the content** — it moves the 6 bold verse entries out of `## Introduction` and into `## Verse-by-Verse Commentary` (separated by `---` from the real verse commentary that follows).
- A recovery routine for this displacement exists in `_extract_sections_from_copy_edited` in both pipeline scripts. It gates on `has_liturgical_marker AND has_key_verses_header`. The `has_key_verses_header` check used `re.search(r'####\s*Key Verse', ...)` — **case-sensitive**. The old Opus 4.6 header was `#### Key Verses and Phrases` (capital V), which matched as a substring; Opus 4.7 emits `#### Key verses` (lowercase v, faithfully following the prompt at `master_editor.py:255`), which does not match. Recovery branch never fired; displaced content stayed in the verses file; DOCX rendered incorrectly.

**Solutions Implemented**:
1. `scripts/run_enhanced_pipeline.py:226` — changed `re.search(r'####\s*Key Verse', intro_text)` to `re.search(r'####\s*Key\s+[Vv]erse', intro_text)` so both old and new header formats match.
2. `scripts/run_si_pipeline.py:229` — converted exact-string check `'#### Key Verses and Phrases' in intro_text` to the same regex `re.search(r'####\s*Key\s+[Vv]erse', intro_text)` for consistency with the enhanced pipeline.
3. `src/agents/copy_editor.py:818-832` — the displacement-warning check also hard-coded `#### Key Verses and Phrases`. Rewrote using `re.search(r'####\s*Key\s+[Vv]erse[^\n]*', corrected)` to capture whichever header variant is present and use `header_len = len(match.group(0))` for slicing. Warning message now includes the matched header string for clarity.
4. Re-ran the post-copy-edit extraction and DOCX regeneration on Psalm 50 without a new API call (copy-edited file already contained the data). Log confirmed: `RECOVERY: Detected displaced liturgical content (2,888 chars) at start of verse commentary. Moving back to introduction.` → `Liturgical content restored to introduction section`. Verified: `edited_intro.md` now ends with the 6 `**Verse N** (...)` liturgical entries after `#### Key verses`; `edited_verses.md` now starts cleanly with `**Verse 1**` on its own line (real commentary).

**Files Modified**:
- `scripts/run_enhanced_pipeline.py` — case-insensitive regex for "Key verses"/"Key Verses and Phrases" header detection in the displacement-recovery branch
- `scripts/run_si_pipeline.py` — same fix for the SI pipeline's copy of the extraction function
- `src/agents/copy_editor.py` — same fix for the post-edit displacement-warning check; capture header variant in the match object and use it for slicing + logging
- `output/psalm_50/psalm_050_edited_intro.md`, `psalm_050_edited_verses.md`, `psalm_050_commentary.docx` — regenerated via the fixed extraction path

---

## Session 327 (2026-04-18): Fix Pipeline Cost Accounting for GPT/Gemini Thinking Tokens

**Objective**: Implement all 5 fixes identified in Session 326's audit: 4 billing bugs, cost JSON persistence, and Master Writer thinking visibility.

**Solutions Implemented**:

1. **Fix 4 — Cost JSON persistence** (`run_enhanced_pipeline.py`, `run_si_pipeline.py`): Before printing the summary, both scripts now serialize `cost_tracker.to_dict()` to `output/psalm_NNN/psalm_NNN_cost.json`. Enables after-the-fact cost comparisons between runs.

2. **Fix 1 — `copy_editor.py` GPT reasoning tokens**: Extracted `reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0) or 0` in the GPT branch, stored as `usage_data['thinking_tokens']`, and passed as `thinking_tokens=usage_data.get('thinking_tokens', 0)` to `cost_tracker.add_usage()`. Claude branch unaffected (correctly passes 0).

3. **Fix 2 — `figurative_curator.py` never logged to tracker**: Added `cost_tracker=None` param to `__init__`, stored as `self.cost_tracker`. In `_call_llm`, after the local cost calculation, calls `self.cost_tracker.add_usage(model="gpt-5.4", ...)` if tracker provided. In `research_assembler.py` line 720, changed `FigurativeCurator(verbose=False)` to `FigurativeCurator(verbose=False, cost_tracker=self.cost_tracker)`.

4. **Fix 3 — `scripture_verifier.py` three silent sites**: Added `cost_tracker=None` to `filter_false_positives` (public wrapper), `_filter_via_haiku`, `_filter_via_gpt`, and `verify_citations_tooluse`. Each logs to `cost_tracker.add_usage()` after its API call. Tool-use verifier logs aggregated totals across all turns after the loop. Pipeline scripts (`run_enhanced_pipeline.py`, `run_si_pipeline.py`) updated to pass `cost_tracker=cost_tracker` at both call sites.

5. **Fix 5 — Master Writer thinking visibility** (`src/agents/archive/master_editor_v2.py`): Switched `_call_claude_writer` from `stream.text_stream` to full event iteration. Accumulates `thinking_chars` from `thinking_delta` events alongside response text. After stream closes, logs: `"Master Writer used ~N thinking tokens (included in the M output total)"`. `thinking_tokens=0` in `add_usage()` kept intentional — Anthropic folds thinking into `output_tokens`; passing it would double-bill.

**Files Modified**:
- `src/agents/copy_editor.py` — Fix 1: capture GPT reasoning_tokens and pass to cost_tracker
- `src/agents/figurative_curator.py` — Fix 2: add cost_tracker param and log usage
- `src/agents/research_assembler.py` — Fix 2 plumbing: pass cost_tracker to FigurativeCurator
- `src/utils/scripture_verifier.py` — Fix 3: add cost_tracker to 4 functions, log usage at all 3 sites
- `scripts/run_enhanced_pipeline.py` — Fix 3 plumbing + Fix 4 (cost JSON)
- `scripts/run_si_pipeline.py` — Fix 3 plumbing + Fix 4 (cost JSON)
- `src/agents/archive/master_editor_v2.py` — Fix 5: event-based stream iteration for thinking visibility

---

## Session 326 (2026-04-18): Audit of Pipeline Cost Accounting

**Objective**: Audit the enhanced + SI pipelines for places where LLM cost tracking silently drops reasoning/thinking tokens, and produce a clear implementation plan for the next session.

**Research**:
- Confirmed via Anthropic's [extended thinking docs](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) that `usage.output_tokens` on Claude API responses **already includes thinking tokens** (billed at output rate). So Claude call sites that pass `thinking_tokens=0` to `cost_tracker.add_usage()` are NOT billing bugs — billing stays accurate via `output_tokens × output_rate`.
- OpenAI GPT-5.x exposes `reasoning_tokens` as a SEPARATE field from `completion_tokens` — these must be passed explicitly or they're missing from billing.
- Google Gemini exposes `thoughts_token_count` as a SEPARATE field from `candidates_token_count` — same consideration as OpenAI.

**Problems Identified**:
- `src/agents/copy_editor.py:691` — GPT branch extracts `reasoning_tokens` at line 628 but doesn't pass them to `add_usage()`. Billing bug when `self.model` is GPT-5.x.
- `src/agents/figurative_curator.py` — Never calls `cost_tracker.add_usage()` at all. Constructed without a tracker at `src/agents/research_assembler.py:720`. Entire GPT-5.4 cost (with `reasoning_effort="high"`) is missing from the pipeline summary.
- `src/utils/scripture_verifier.py:1429` (`_filter_via_gpt`) — Never logs to `cost_tracker`. GPT-5.1 reasoning tokens invisible.
- `src/utils/scripture_verifier.py:1380` (`_filter_via_haiku`) — Never logs to `cost_tracker`.
- `src/utils/scripture_verifier.py:1674` (tool-use verifier, opt-in flag) — Never logs to `cost_tracker`.
- Both pipeline scripts — `cost_tracker.get_summary()` is `print()`-ed to stdout but never persisted as JSON, making after-the-fact run comparisons impossible.

**Solutions Implemented** (this session — planning only):
1. Wrote `docs/session_tracking/NEXT_SESSION_BRIEF.md` with a detailed, sequential implementation plan: punch list of 5 fixes, exact patterns to follow, files/lines to touch, and verification steps.
2. Added a prominent pointer to the brief at the top of `CLAUDE.md` so the next session picks it up immediately.
3. Recommended Claude Sonnet 4.6 for the implementation session (mechanical plumbing work, clear patterns already in the codebase — Opus is overkill).

**Files Modified**:
- `docs/session_tracking/NEXT_SESSION_BRIEF.md` — NEW: detailed implementation plan for Session 327
- `CLAUDE.md` — Added next-session pointer; bumped session number; updated recent-5 list; added brief to Reference Docs section
- `docs/session_tracking/IMPLEMENTATION_LOG.md` — This entry

**Next session (327)**: Implement the 5 fixes in `NEXT_SESSION_BRIEF.md`. Expected output: 6–7 files modified, commit as "Session 327: Fix pipeline cost accounting for GPT/Gemini thinking tokens".

---

## Session 325 (2026-04-18): Master Writer on Opus 4.7 — Max Effort

**Objective**: Verify the recommended thinking configuration for Claude Opus 4.7 (now the Master Writer's default model) and tune it for maximum reasoning depth.

**Research**:
- Anthropic removed `budget_tokens` on Opus 4.7 — `thinking: {"type": "enabled", "budget_tokens": N}` returns a 400 error
- Adaptive thinking is the only supported thinking-on mode; interleaved thinking is auto-enabled with no beta header required
- A new `effort` parameter replaces `budget_tokens` with five tiers: `low`, `medium`, `high` (default), `xhigh` (Claude Code default), `max`
- Anthropic's internal evals: adaptive thinking "reliably outperforms extended thinking with a fixed budget_tokens" on bimodal and long-horizon tasks
- Recommended `max_tokens=64000` for high/xhigh/max effort — matches our existing setting

**Problems Identified**:
- Prior to this session, the Master Writer was running on adaptive + default (`high`) effort with no explicit `output_config`. For a long-form synthesis task, max effort is a better trade-off.
- Opus 4.6 callers (e.g., Macro Analyst) cannot receive `output_config` without error, so the change must be gated.

**Solutions Implemented**:
1. In `_call_claude_writer` (`src/agents/archive/master_editor_v2.py`), refactored the `messages.stream(...)` call to build a `stream_kwargs` dict
2. Added `stream_kwargs["output_config"] = {"effort": "max"}` conditionally when `"opus-4-7" in model_id`
3. Left `thinking={"type": "adaptive"}` unchanged (correct and only supported mode on 4.7)
4. Left `max_tokens=64000` unchanged (matches Anthropic's recommendation for max effort)

**Files Modified**:
- `src/agents/archive/master_editor_v2.py` — Added model-gated `output_config={"effort": "max"}` in `_call_claude_writer` streaming call

**Follow-ups / Watch-outs**:
- Max effort at 64k max_tokens will run hotter than plain adaptive. Monitor token usage on the first 1–2 psalms before a batch run.
- Requires a reasonably current `anthropic` Python SDK. If an `unexpected keyword` error surfaces, `pip install -U anthropic`.

---

## Session 324 (2026-04-17): Upgrade Master Writer to Claude Opus 4.7

**Objective**: Switch the Master Writer's default model from Claude Opus 4.6 to the newly released Claude Opus 4.7, keeping the Macro Analyst on Opus 4.6.

**Research**:
- Opus 4.7 released 2026-04-16; same per-token pricing ($5/$25 per MTok) but new tokenizer may increase token count 0–35%, especially on non-English text (Hebrew)
- Confirmed the DOCX methodology page reads the model string dynamically from `stats_data['model_usage']` — no code change needed for DOCX flow

**Solutions Implemented**:
1. Changed `master_editor_model` default from `"claude-opus-4-6"` to `"claude-opus-4-7"` in both `run_enhanced_pipeline.py` and `run_si_pipeline.py`
2. Updated argparse `choices` to `["claude-opus-4-7", "claude-opus-4-6"]` so 4.6 remains available as a fallback
3. Added `"claude-opus-4-7"` pricing entry to `cost_tracker.py` (same rates as 4.6)
4. Updated all documentation: CLAUDE.md, TECHNICAL_ARCHITECTURE_SUMMARY.md, scriptReferences.md, How to Run the Pipeline.txt

**Files Modified**:
- `scripts/run_enhanced_pipeline.py` — Default master editor model → `claude-opus-4-7`, updated choices
- `scripts/run_si_pipeline.py` — Same changes as enhanced pipeline
- `src/utils/cost_tracker.py` — Added `claude-opus-4-7` pricing entry
- `CLAUDE.md` — Updated model list and session info
- `docs/architecture/TECHNICAL_ARCHITECTURE_SUMMARY.md` — 6 edits: exec summary, flow diagram, Master Editor options, CLI flags, cost tracking, model table, key achievements
- `docs/session_tracking/scriptReferences.md` — master_editor.py description updated to Opus 4.7
- `Documents/How to Run the Pipeline.txt` — Clarified 4.6 is now the fallback option

---

## Session 323 (2026-04-14): Master Editor Outline Prompt Documentation

**Objective**: Archive the experimental paragraph outline prompt iteration for the master editor and restore the active production version.

**Changes Implemented**:
1. **Archived Experimental Prompt**: Saved the test prompt instructions (which forced the master editor to outline each paragraph's argument and its relationship to the thesis before writing) to `docs/archive/deprecated/OLD_master_editor_paragraph_outline_prompt.md`.
2. **Reverted Pipeline**: Used `git restore` on `src/agents/master_editor.py` to remove the outline instructions and return the production prompt to its prior state.

**Files Modified**:
- `docs/archive/deprecated/OLD_master_editor_paragraph_outline_prompt.md` — **[NEW]** Archived prompt text
- `src/agents/master_editor.py` — Reverted test changes via git restore

---

## Session 322 (2026-04-09): ASCII Hyphen BiDi Fix for DOCX Hebrew Processing

**Objective**: Fix two DOCX rendering bugs in Psalm 47 caused by ASCII hyphens (U+002D) being used as maqqaf substitutes in the edited verses markdown.

**Problems Identified**:
1. **Verse header maqqafs vanishing**: Hebrew verse lines like `כׇּל-הָעַמִּים תִּקְעוּ-כָף` had their hyphens silently dropped, producing `כׇּלהָעַמִּים תִּקְעוּכָף` (words missing spaces). This only affected Psalm 47 because its markdown uses ASCII hyphens (U+002D) while other psalms (46, 48, etc.) use actual Hebrew maqqaf (U+05BE).
2. **Inline Hebrew garbling**: Multi-word Hebrew like `מֶלֶךְ גָּדוֹל עַל-כׇּל-הָאָרֶץ` was only partially matched by `_reverse_bare_hebrew_segments` (3 of 5 words, stopping at the first `-`), leaving orphaned unreversed Hebrew that Word's BiDi algorithm garbled.

**Root Cause**: Three regex patterns in `document_generator.py` handled Hebrew maqqaf (U+05BE) but not ASCII hyphen (U+002D):
- `_split_into_grapheme_clusters`: base character class didn't include `-`, so hyphens were silently dropped during cluster extraction
- `_reverse_bare_hebrew_segments`: separator pattern didn't include `-`, so hyphen-separated words weren't recognized as part of the same Hebrew segment
- `_reverse_primarily_hebrew_line`: tokenizer didn't split on `-`, so hyphens were swallowed into Hebrew word tokens

**Solutions Implemented**:
1. Added `\-` to `_split_into_grapheme_clusters` base character class (line 92) — hyphens now preserved as their own grapheme cluster during reversal.
2. Added `\-` to `_reverse_bare_hebrew_segments` separator pattern (line 194) — multi-word Hebrew with ASCII hyphens now fully detected and reversed as a single segment.
3. Added `\-` to `_reverse_primarily_hebrew_line` tokenizer split pattern (line 312) — hyphens treated as word separators alongside semicolons, commas, etc.

**Files Modified**:
- `src/utils/document_generator.py` — Three regex updates (lines 92, 194, 312).

**Verification**: Regenerated Psalm 47 DOCX — both verse header hyphens and inline Hebrew now render correctly. Regenerated Psalm 46 DOCX as regression test (uses U+05BE maqqaf) — no issues.

---

## Session 321 (2026-04-09): Ellipsis BiDi Fix in DOCX Hebrew Block Detection

**Objective**: Fix garbled Hebrew in Psalm 49 DOCX where a 10-word Hebrew quotation containing a Unicode ellipsis (`…`, U+2026) was not detected as a long block and rendered inline with BiDi corruption.

**Problem Identified**:
- Psalm 49 Selichot passage: `הַחוֹשְׁבִים לְהַשְׁכִּיחַ שֵׁם קֹדֶשׁ הַנִּכְבָּד… זֶה דַּרְכָּם טוּבֵי עָם אִבָּד` — 10 Hebrew words, well above the 6-word threshold for block extraction.
- The Unicode ellipsis `…` (U+2026) was not in the `separator` regex of `_split_long_hebrew_block`, splitting the sequence into two 5-word halves — neither reaching the 6-word threshold.
- Both halves were individually reversed by `_reverse_bare_hebrew_segments` and LRO-wrapped, but Word's BiDi algorithm garbled the visual ordering between the two reversed segments and the intervening ellipsis.

**Solution Implemented**:
1. Added `\u2026` (horizontal ellipsis) to the `separator` character class in `_split_long_hebrew_block` — the full 10-word sequence is now detected as one long block and rendered as a standalone RTL paragraph.
2. Added `\u2026` to the `separator` character class in `_reverse_bare_hebrew_segments` as a fallback — ensures ellipsis-separated Hebrew is treated as a single segment for inline reversal too.

**Files Modified**:
- `src/utils/document_generator.py` — Two separator regex updates (lines 632, 194).

**Verification**: Regenerated Psalm 49 DOCX. The Selichot Hebrew quotation now renders as a properly formatted RTL block quote.

---

## Session 320 (2026-03-29): DOCX Formatting Fixes for Psalms 44, 49, and 50

**Objective**: Resolve three specific formatting issues in the DOCX outputs: displaced liturgical headers in Psalm 44, incorrect inline styling for a full verse quotation in Psalm 49, and improperly split block formatting for a punctuated Hebrew quotation in Psalm 50.

**Problems Identified**:
- Psalm 44: The recovery script for displaced liturgical content was strictly looking for `#### Key Verses and Phrases`, but the LLM output `#### Key Verses`, causing the recovery to silently fail and leave liturgical headers inside the verse commentary.
- Psalm 49: The `_split_long_hebrew_block` regex did not recognize the `׀` (paseq) mark or `׃` (sof-pasuq) as valid separators, causing a full verse quotation to be incorrectly extracted as a block quote and split into three pieces.
- Psalm 50: The same regex did not recognize standard punctuation (`!`, `?`, `—`, etc.), causing a long Bialik Hebrew quotation to be chopped into pieces, with only the middle piece receiving block-quote formatting.

**Solutions Implemented**:
1. Updated the key verses header detection in `run_enhanced_pipeline.py` to use a flexible regex (`r'####\s*Key Verse'`).
2. Expanded the `separator` regex in `document_generator.py` to include basic punctuation (`!`, `?`, `.`, `-`, `–`, `—`, `(`, `)`, `[`, `]`, `'`, `"`) as well as `\u05C0` (paseq) and `\u05C3` (sof-pasuq).
3. Verified the fixes by regenerating the docx files for Psalms 44, 49, and 50 (created local testing script `test_fix_50.py`).

**Files Modified**:
- `scripts/run_enhanced_pipeline.py` - Loosened the displaced liturgical recovery heuristic.
- `src/utils/document_generator.py` - Expanded the `separator` character class in `_split_long_hebrew_block`.

---

## Session 319 (2026-03-27): Fix Split Block Quote Formatting in DOCX

**Objective**: Fix DOCX formatting issue where long Hebrew quotations containing markdown bold markers (`**`) or poetry line-break markers (`/`) were split between inline format (Aptos 12) and block quote format (Times New Roman 13).

**Problems Identified**:
- `_split_long_hebrew_block` regex required 6+ consecutive Hebrew words, but `**` bold markers around `עַל־כֵּן` interrupted the sequence, splitting one quotation into two segments — only the longer segment was extracted as a block quote
- Same issue with `/` poetry line-break separator in a Yiddish quotation (Kadya Molodowsky passage)
- Extracted Hebrew blocks lost bold formatting because `**` markers were stripped without being rendered

**Solutions Implemented**:
1. Updated separator regex in `_split_long_hebrew_block` to allow `**` bold markers and `/` as valid separators between Hebrew words: `r'(?:[\s:;,/\u05BE]|\*{1,2})+'`
2. Updated `_add_hebrew_block_paragraph` to parse `**...**` markers and create separate bold/non-bold runs instead of a single plain run

**Files Modified**:
- `src/utils/document_generator.py` — Updated separator regex in `_split_long_hebrew_block`; added bold-aware run creation in `_add_hebrew_block_paragraph`

**Verification**: Regenerated Psalm 45 DOCX. Both "The Logic of Therefore" quotations and the Molodowsky Yiddish quotation now render as unified block quotes with bold preserved.

---

## Session 318 (2026-03-26): BiDi Double-Reversal Fix

**Objective**: Fix garbled Hebrew text in parentheses in Psalm 43's DOCX output — `(תְּפִלָּה לִשְׁלוֹם הַמְּדִינָה)` displayed with scrambled word order.

**Problems Identified**:
- `_reverse_bare_hebrew_segments()` double-processed Hebrew text that was already reversed and wrapped with LRO/PDF by the parenthesized Hebrew handler. The bare segment regex matched reversed Hebrew characters inside the LRO wrapper as a new 3+ word segment, reversing them a second time and producing nested `LRO(LRO…PDF)PDF` — garbled display in Word.
- `_add_paragraph_with_soft_breaks()` was missing the `_reverse_bare_hebrew_segments()` call that all other 4 BiDi code paths included.

**Solutions Implemented**:
1. Added placeholder protection to `_reverse_bare_hebrew_segments()`: existing `LRO…PDF` blocks are replaced with null-byte placeholders before the bare Hebrew regex runs, then restored after — preventing double-processing.
2. Added the missing `_reverse_bare_hebrew_segments()` call to `_add_paragraph_with_soft_breaks()`, matching the other code paths.

**Files Modified**:
- `src/utils/document_generator.py` — Placeholder protection in `_reverse_bare_hebrew_segments()` (+11 lines); added bare-segment call to `_add_paragraph_with_soft_breaks()` (+2 lines)

**Verification**: Diagnostic script confirmed single LRO/PDF wrapper (no nesting). Psalm 43 and Psalm 40 DOCX files regenerated successfully.

---

## Session 317 (2026-03-18): SI Pipeline Parity Update

**Objective**: Bring `run_si_pipeline.py` fully up to date with all improvements that had accumulated in `run_enhanced_pipeline.py`.

**Problems Identified**:
- SI pipeline had drifted behind the enhanced pipeline in 12+ areas over many sessions
- Latent bug: `extract_insights()` call in SI pipeline passed only 4 args (missing `macro_analysis`) — would crash if insights were ever enabled via `--include-insights`
- Concordance counting used old method (counting query headers vs summing actual result counts)
- Missing `--exclude-insights` / `--exclude-questions` flags (added in enhanced pipeline)
- No file existence guards on print-ready and Word doc steps
- Doc gen error handling used `.warning()` instead of `.error()` with traceback
- `tracker.mark_pipeline_complete()` called too late (after print-ready instead of before)
- Deprecated `--use-o1` flag and `gpt-5` model choice still present
- Duplicate print statements in startup section
- `skip_college` still in `is_resuming` check
- Torah Temimah missing from commentary patterns
- Docstring/comments for `_extract_sections_from_copy_edited` less detailed than enhanced

**Solutions Implemented**:
1. Ported concordance counting fix (sum actual result numbers from `(N results` headers)
2. Added Torah Temimah to commentary pattern list
3. Added `exclude_insights` / `exclude_questions` flags to function signature, argparse, write_commentary call, reader questions save logic, and Word doc question logic
4. Ported rich insight extractor with phonetic text from micro_analysis + `macro_analysis` as 5th param
5. Added file existence guards on print-ready (`edited_intro_file.exists() and edited_verses_file.exists()`) and Word doc steps
6. Upgraded doc gen error handling to `logger.error()` with `exc_info=True` + stdout print
7. Moved `tracker.mark_pipeline_complete()` before print-ready step (matching enhanced)
8. Removed deprecated `--use-o1` flag and `gpt-5` from `--master-editor-model` choices
9. Updated help text for skip-insights/questions; added Session 280 comment
10. Cleaned up duplicate print statements in startup section
11. Removed `skip_college` from `is_resuming` check
12. Ported enhanced docstring and inline comments for `_extract_sections_from_copy_edited`

**Intentionally kept different** (by-design SI distinctions):
- `MasterEditorSI` class (vs `MasterEditor`)
- Special instruction loading + `--special-instruction` arg
- `_SI` filename suffixes
- `special_instruction=` param in `write_commentary` call

**Files Modified**:
- `scripts/run_si_pipeline.py` — All 12 improvements ported from enhanced pipeline

**Verification**: Smoke test passed (`--smoke-test --skip-copy-editor --skip-word-doc`), syntax check passed.

---

## Session 316 (2026-03-18): Session Management Overhaul

**Objective**: Review and restructure session management system to reduce startup token cost and improve cross-session knowledge carry-over for both Claude Code and Gemini.

**Problems Identified**:
- CLAUDE.md and PROJECT_STATUS.md had ~60% content overlap, wasting tokens every session
- PROJECT_STATUS.md was 15KB, bloated with frozen feature documentation from sessions 211-227
- IMPLEMENTATION_LOG.md was 153KB (sessions 241-315), never archived since session 200
- No Claude Code persistent memory existed — every session started cold
- Session number inconsistency (header said 315, body said 314)
- Stale `IMPLEMENTATION_LOG.md_content` fragment lying around

**Solutions Implemented**:
1. **Archived IMPLEMENTATION_LOG sessions 241-299** to `docs/archive/documentation_cleanup/IMPLEMENTATION_LOG_sessions_241-299_2026-03-18.md`. Active log now contains sessions 300+ only (153KB → 44KB).
2. **Created FEATURE_ARCHIVE.md** — moved detailed stable feature docs out of PROJECT_STATUS.md (4.5KB, read-on-demand).
3. **Slimmed PROJECT_STATUS.md** to stable reference (15KB → 3.5KB): pipeline phases, active features, databases, doc links. No longer read at startup.
4. **Rewrote CLAUDE.md as single startup doc** (5.5KB → 4KB): session number, last 5 sessions (3-line summaries), quick commands, key dirs, end-of-session checklist. Works for both Claude Code (auto-loaded) and Gemini (copy-paste via SESSION_PROMPTS.md).
5. **Updated SESSION_PROMPTS.md**: Gemini start prompt now says "read CLAUDE.md". End-of-session checklist references CLAUDE.md as primary update target.
6. **Created Claude Code persistent memory** (`MEMORY.md`): documents the new session management system and key project patterns.
7. **Deleted stale fragment** `IMPLEMENTATION_LOG.md_content`.

**Results**: Startup token cost reduced ~80% (20.5KB → 4KB). Single source of truth for session number. System works for both Claude Code and Gemini.

**Files Modified**:
- `CLAUDE.md` — Complete rewrite as compact single startup doc
- `docs/session_tracking/PROJECT_STATUS.md` — Slimmed to stable reference only
- `docs/session_tracking/SESSION_PROMPTS.md` — Updated for new system
- `docs/session_tracking/IMPLEMENTATION_LOG.md` — Archived 241-299, updated header
- `docs/session_tracking/FEATURE_ARCHIVE.md` — New file, extracted from PROJECT_STATUS
- `docs/archive/documentation_cleanup/IMPLEMENTATION_LOG_sessions_241-299_2026-03-18.md` — New archive
- `docs/session_tracking/IMPLEMENTATION_LOG.md_content` — Deleted (stale fragment)

---

## Session 315 (2026-03-18): Divine Name Normalization & Citation Difference Accuracy

**Objective**: Fix citation verifier to recognize programmatic divine name modifications (geniza-style) and improve the accuracy of "Likely issue" diagnostic messages.

**Problems Identified**:
- Psalm 22:2 `קֵלִי קֵלִי` was flagged as a misquote, but it's actually the divine name modifier's output for `אֵלִי אֵלִי` — the verifier lacked reverse mappings for El/Eli, Shaddai, and Eloah divine name patterns
- Existing `אלק` → `אלה` reverse mapping only worked on unvoweled Hebrew (consecutive consonants), failing on voweled forms like `אֱלֹקֵינוּ`
- Unicode diacritics ordering differences (dagesh+kamatz vs kamatz+dagesh) caused false substring mismatches even after correct normalization
- "Likely issue" message always said "Word(s) appear more times in quote than in actual verse" even when the real issue was word substitution, conjugation change, or word reordering
- GPT-5.1 judge annotations appended to `normalized_quoted` polluted the `_describe_difference()` analysis

**Solutions Implemented**:
1. Added reverse divine name mappings to `_DIVINE_NAME_PATTERNS`: `קֵלִי` → `אֵלִי`, `קֵל` → `אֵל`, `שקי` → `שדי`, `אלוק` → `אלוה`
2. Fixed `אלק` → `אלה` pattern to allow diacritics between consonants (voweled Hebrew support)
3. Added NFC Unicode normalization to `_normalize_hebrew()` — resolves diacritics ordering inconsistencies
4. Rewrote difference detection in `_describe_difference()`: distinguishes "word(s) not found in verse" from genuinely doubled words; strips `[GPT-5.1: ...]` annotations before analysis

**Results**:
- Psalm 42: 4 issues → 3 issues (Psalm 22:2 divine name false positive eliminated)
- Issue 3 (Ps 18:32): `אֱלֹקֵינוּ` now properly normalized, only `בִּלְעֲדֵי` flagged as unfound
- All "Likely issue" messages now accurately describe the problem
- Psalm 41 regression test passes (7 issues unchanged)

**Files Modified**:
- `src/utils/scripture_verifier.py` — Added divine name reverse mappings, NFC normalization, fixed voweled `אלק` pattern, improved `_describe_difference()` with annotation stripping and accurate word categorization

---

## Session 314 (2026-03-17): GPT Filter Default, End-to-End Citation Fix Verified

**Objective**: Make the GPT-5.1 false-positive filter the default for citation verification across all pipeline runners, and run a full end-to-end test confirming all 5 planted errors in Psalm 41 are detected and corrected.

**Changes Implemented**:
1. **GPT-5.1 filter now default**: Added `--gpt-filter` (default=True) and `--no-gpt-filter` flags to `run_enhanced_pipeline.py`, `run_si_pipeline.py`, and `run_scripture_verifier.py`. The GPT-5.1 judge runs automatically on citation mismatches; `--haiku-filter` remains as a cheaper alternative. `--no-gpt-filter` disables the default filter entirely.
2. **Fixed standalone verifier `--fix` bug**: The `fix_prompt` generated by `format_fix_prompt()` was never passed to `edit_commentary()`. Added `supplementary_prompt=fix_prompt` to the copy editor call.
3. **End-to-end verification**: Ran citation verifier + copy editor on Psalm 41 print-ready file. Results:
   - Regex verifier found 7 issues; GPT-5.1 filtered 2 false positives, keeping all 5 genuine errors ($0.039)
   - Copy editor (GPT-5.4) corrected all 5 citation errors, clearly tagged `[CITATION FIX]` in changes file ($0.49)
   - Total pipeline cost: $0.53
   - All corrections verified accurate: Gen 27:36 conjugation, Ex 20:7 missing word, 2 Chr 13:7 doubled word, Ps 55:13 truncated noun, 2 Sam 7:29 missing בֵּית

**Test Results — Psalm 41 End-to-End**:
| Stage | Issues | Cost |
|-------|--------|------|
| Regex verifier | 7 (5 genuine + 2 FP) | $0.000 |
| GPT-5.1 filter | 5 kept, 2 filtered | $0.039 |
| Copy editor fix | 5/5 corrected + 6 editorial changes | $0.490 |

4. **DOCX model attribution**: Added `citation_filter` to `track_model_for_step()` in both pipeline runners. Added "Citation Verifier Filter" line to Models Used section in both `document_generator.py` and `combined_document_generator.py`. Also added missing "Copy Editor" line to `combined_document_generator.py`.
5. **Documentation updates**: Updated `TECHNICAL_ARCHITECTURE_SUMMARY.md` (added Step 4½ to flow diagram, GPT-5.4 to model list, citation verifier to enhancements), `scriptReferences.md` (updated descriptions for all 3 scripts).

**Files Modified**:
- `scripts/run_enhanced_pipeline.py` — Added `--gpt-filter` (default), `--no-gpt-filter`; updated filter logic; added `citation_filter` model tracking
- `scripts/run_si_pipeline.py` — Same changes as above
- `scripts/run_scripture_verifier.py` — Added `--gpt-filter` (default), `--no-gpt-filter`; fixed `--fix` bug (supplementary_prompt not passed)
- `src/utils/document_generator.py` — Added "Citation Verifier Filter" to Models Used section
- `src/utils/combined_document_generator.py` — Added "Citation Verifier Filter" and "Copy Editor" to Models Used section
- `docs/architecture/TECHNICAL_ARCHITECTURE_SUMMARY.md` — Added Step 4½ citation verifier to flow, GPT-5.4 to model list, verifier to enhancements
- `docs/session_tracking/scriptReferences.md` — Updated descriptions for pipeline runners and verifier script
- `docs/session_tracking/IMPLEMENTATION_LOG.md` — This entry
- `docs/session_tracking/PROJECT_STATUS.md` — Session 314 entry

---

## Session 313 (2026-03-17): Citation Verifier — GPT-5.1 Judge, Precise Difference Hints

**Objective**: Test the citation verifier against Psalm 41's 5 known errors, fix the `_describe_difference` hint noise, and add GPT-5.1 as a smarter false-positive filter alternative to Haiku.

**Problems Identified**:
- `_describe_difference()` generated noisy hints — listed trailing verse words as "missing from middle" (e.g., Ex 20:7 hint included 5 unrelated words after `אֱלֹהֶיךָ`). This confused Haiku into filtering real errors.
- Doubled-word errors (e.g., `רֵקִים רֵקִים` in 2 Chr 13:7 when verse has one `רֵקִים`) were completely undetected.
- Haiku judge was too aggressive: even with improved prompt, it filtered Ex 20:7 (a genuine missing-word error) because the English translation nearby included the missing word.

**Solutions Implemented**:
1. **Fixed `_describe_difference()`**: Replaced buggy walk-through (which never turned off `in_quote` flag, causing all trailing words to be reported) with greedy left-to-right word alignment. Now reports only words between matched positions. Ex 20:7 hint: `Missing word(s) from middle of quote: אֱלֹהֶיךָ` (was: `אֱלֹהֶיךָ כִּי יְנַקֶּה אֵת אֲשֶׁר יִשָּׂא שְׁמוֹ`).
2. **Added doubled-word detection**: New check using `Counter` to detect words appearing more times in the quote than in the actual verse. Catches 2 Chr 13:7 (`רֵקִים` doubled).
3. **Strengthened Haiku judge prompt**: Replaced generic partial-quote guidance with numbered "AUTOMATED ANALYSIS HINTS" section — concrete examples for middle-word drops, doubled words, and conjugation differences with explicit DEFAULT verdicts.
4. **Added GPT-5.1 false-positive filter** (`--gpt-filter`): Uses GPT-5.1 with `reasoning.effort=medium` as an alternative to Haiku. Refactored `filter_false_positives()` into shared helpers (`_build_judge_pairs`, `_apply_judgments`) with separate `_filter_via_haiku` and `_filter_via_gpt` backends.

**Test Results — Psalm 41 (5 known errors)**:
| Filter | Real errors kept | False positives filtered | Cost |
|--------|:---:|:---:|---:|
| Regex only | 5/5 + 2 FP | — | $0.000 |
| Haiku (improved) | 4/5 (misses Ex 20:7) | 3 (1 wrong) | $0.007 |
| **GPT-5.1** | **5/5** | **2 (both correct)** | **$0.047** |

**Next Session Plan**: (1) Make `--gpt-filter` the default in pipeline runners, (2) full end-to-end test: run citation verifier + copy editor on Psalm 41 print-ready file to confirm all 5 errors get corrected and appear in the copy editor changes file.

**Files Modified**:
- `src/utils/scripture_verifier.py` — Fixed `_describe_difference()` (precise alignment, doubled-word detection), strengthened `_HAIKU_JUDGE_SYSTEM` prompt, refactored `filter_false_positives()` with `model` param, added `_filter_via_gpt()`, `_build_judge_pairs()`, `_apply_judgments()`
- `scripts/run_scripture_verifier.py` — Added `--gpt-filter` flag, unified filter invocation for both Haiku and GPT backends

---

## Session 312 (2026-03-17): Haiku Tool-Use Citation Verifier Architecture

**Objective**: Build a tool-use verification architecture where Haiku identifies all citations, calls a DB lookup tool to retrieve actual verse text, and the system compares them programmatically. Goal: eliminate regex pattern coverage gaps.

**Architecture Explored**:
Three approaches were tested and compared on Psalm 41 and Psalm 22:

1. **Pure Haiku comparison** (v1): Haiku extracts citations via tool-use, looks up verses, AND judges matches itself. Result: $0.21/psalm, found only 1/4 genuine errors. Haiku is unreliable at consonantal Hebrew comparison — too lenient.

2. **Hybrid approach** (v2, final): Haiku extracts citations via tool-use → Python does programmatic comparison (existing `_normalize_hebrew` + `_words_match`) → Haiku filters false positives. Result: $0.03-0.04/psalm, found 2-3 genuine errors.

3. **Regex + Haiku filter** (existing, Session 310): Regex patterns A/B/C/D extract citations → programmatic comparison → Haiku filters FPs. Result: $0.003/psalm, found 4 genuine errors.

**Key Findings**:
- Haiku's citation extraction is unreliable: it misses some citations (Ex 20:7, 2 Sam 7:29 in Psalm 41; 4 citations in Psalm 22) and occasionally fabricates Hebrew text that doesn't appear in the commentary (Ps 7:5 hallucination in Psalm 41).
- Haiku is great at judging mismatches (false positive filtering) but bad at extracting Hebrew exactly.
- Prompt caching (`cache_control: ephemeral`) reduced tool-use cost from $0.21 to $0.04 by avoiding re-sending the full commentary each turn.
- The regex approach remains the better primary verifier: it's free, faster (<1s vs 65-80s), and catches more genuine errors.

**Implementation**:
1. `verify_citations_tooluse()` in `scripture_verifier.py`: Full hybrid tool-use verifier with prompt caching, batched tool calls, programmatic comparison, and optional Haiku FP filter.
2. `--tooluse-verify` flag added to `run_enhanced_pipeline.py`, `run_si_pipeline.py`, and `run_scripture_verifier.py`. Runs alongside the regex verifier and merges results (deduplication by reference).
3. `test_haiku_tooluse_verifier.py` test script with comparison output.

**Test Results — Psalm 41**:
| Approach | Genuine Errors | False Positives | Cost | Time |
|----------|---------------|-----------------|------|------|
| Regex only | 4 genuine + 3 FP | 3 | Free | <1s |
| Regex + Haiku filter | 4 genuine | 0 | $0.003 | ~5s |
| Tool-use hybrid | 2 genuine + 1 fabricated | 1 | $0.038 | 65s |

**Test Results — Psalm 22**:
- Tool-use: 2 issues (both also found by regex), 0 novel finds
- Regex: 6 issues (4 additional not caught by tool-use)

**Conclusion**: The tool-use architecture is implemented and integrated as an optional supplementary mode. The regex+filter approach ($0.003/psalm) remains the recommended default. Tool-use adds coverage in theory but Haiku's extraction reliability needs to improve before it can be a primary verifier.

**Files Modified**:
- `src/utils/scripture_verifier.py` — Added `_TOOLUSE_EXTRACT_SYSTEM`, `_TOOLUSE_TOOLS` (lookup_verse, report_citations), `verify_citations_tooluse()` with prompt caching and hybrid comparison
- `scripts/test_haiku_tooluse_verifier.py` — **[NEW]** Tool-use verifier test script with regex comparison
- `scripts/run_enhanced_pipeline.py` — Added `--tooluse-verify` flag and tool-use integration in Step 5a½
- `scripts/run_si_pipeline.py` — Same `--tooluse-verify` integration
- `scripts/run_scripture_verifier.py` — Added `--tooluse-verify` flag with merge logic
- `docs/session_tracking/IMPLEMENTATION_LOG.md` — This entry
- `docs/session_tracking/PROJECT_STATUS.md` — Session 312 entry

---

## Session 311 (2026-03-17): Citation Verifier — Pattern D, Ellipsis Fragments, Normalization Fixes

**Objective**: Test the citation verifier against Psalm 41 with user-planted errors in verses 7, 10, and 13, then fix the gaps revealed by the test.

**Problems Identified**:
- The verifier only caught citations in parenthetical format `(Book Ch:V)`. Inline references like `2 Samuel 7:29 —` and `Psalm 55:13–14, ...` were invisible (no Pattern D).
- Ellipsis-separated Hebrew fragments (e.g., `כִּי לֹא אוֹיֵב... לֹא מְשַׂ עָלַי הִגְדִּיל...`) were treated as a single string and not verified per-fragment.
- The Haiku FP filter incorrectly filtered genuine errors (Ex 20:7, 2 Sam 7:29) because the `_describe_difference()` hint function failed: the Tetragrammaton `יְהֹוָה` (with vowels) didn't match the normalized `יהוה` (from `ה׳`), and meteg (U+05BD) caused word mismatches like `שֵׁם` ≠ `שֵֽׁם`.
- `Psalm` (singular) was missing from `_BOOK_ABBREVS`, so `Psalm 55:13` couldn't resolve to "Psalms" in the database.

**Solutions Implemented**:
1. **Pattern D: Forward inline citation extraction** (`scripture_verifier.py`): New `_CITATION_FORWARD_RE` regex and `_extract_hebrew_after_citation()` function. Matches non-parenthetical references like `2 Samuel 7:29 — Hebrew...` or `Psalm 55:13–14, ...Hebrew...`. Includes forward intervening-citation check, early-verify logic (short matching phrase near citation prevents false flagging of distant phrases), and parenthetical exclusion to avoid overlap with Patterns A/B/C.
2. **Ellipsis fragment splitting** (`scripture_verifier.py`): New `_split_ellipsis_fragments()` splits extracted Hebrew on `...`/`…` into independent fragments, each verified separately against the cited verse. Catches truncated words like `מְשַׂ` (should be `מְשַׂנְאִי`) within multi-fragment quotes.
3. **Divine name normalization fix** (`scripture_verifier.py`): Added Tetragrammaton pattern `יְהֹוָה` → `יהוה` with any diacritics between consonants, so the full voweled form normalizes to the same consonantal form as `ה׳`. This makes `_describe_difference()` correctly detect missing words in citations containing the divine name.
4. **Meteg stripping** (`scripture_verifier.py`): Added U+05BD (meteg/stress mark) to the stripped characters in `_normalize_hebrew()`, preventing false word mismatches like `שֵׁם` ≠ `שֵֽׁם`.
5. **Book name fix**: Added `"Psalm": "Psalms"` to `_BOOK_ABBREVS` for singular form resolution.
6. **Haiku prompt improvements** (`scripture_verifier.py`): Strengthened system prompt to flag "Missing word(s) from middle of verse" as typically GENUINE_ERROR. Added automated `_describe_difference()` output as a hint in each pair sent to Haiku.

**Test Results — Psalm 41 (regex-only, 6 issues)**:
- Gen 27:36 conjugation error: CAUGHT (existing)
- Ex 20:7 missing `אֱלֹהֶיךָ`: CAUGHT (existing)
- Ps 55:13 truncated `מְשַׂנְאִי` → `מְשַׂ`: CAUGHT (NEW, Pattern D + ellipsis fragments)
- 2 Sam 7:29 missing `בֵּית`: CAUGHT (NEW, Pattern D)
- Ps 72:18-19 piyyut: flagged (FP, Haiku filters correctly)
- Jer 20:10 plene/defective spelling: flagged (FP, Haiku filters correctly)

**Next Session**: Build Haiku tool-use verification architecture — Haiku identifies all citations, calls DB lookup tool, then judges matches. Eliminates regex pattern coverage gaps entirely (~$0.02/psalm).

**Files Modified**:
- `src/utils/scripture_verifier.py` — Added Pattern D (`_CITATION_FORWARD_RE`, `_extract_hebrew_after_citation`, forward-verify loop with intervening-citation check and early-verify), `_split_ellipsis_fragments()`, Tetragrammaton normalization, meteg stripping, `"Psalm"` book name, Haiku prompt improvements with difference hints
- `docs/session_tracking/IMPLEMENTATION_LOG.md` — This entry
- `docs/session_tracking/PROJECT_STATUS.md` — Session 311 entry
- `docs/session_tracking/scriptReferences.md` — Updated verifier description

---

## Session 310 (2026-03-17): Hybrid Haiku Citation Filter & Verifier Improvements

**Objective**: Explore using Claude Haiku 4.5 to improve citation verification accuracy by filtering false positives, and fix two underlying verifier issues (report contamination, loose consonantal matching).

**Problems Identified**:
- The regex verifier produced false positives when piyyut/liturgical Hebrew appeared near editorial citations in different clauses (e.g., Ps 72:18-19 in Psalm 41 — the regex associated piyyut text with a later editorial reference).
- Previously-appended verification reports were embedded in print-ready files. When the verifier re-read the file, it matched citations inside its own old report ("report contamination"), producing phantom errors like the Ex 20:7 issue.
- Pure consonantal substring matching was too loose: `עקבני` (from `עֲקָבַנִי`) passed as a substring of `ויעקבני` (from `וַיַּעְקְבֵנִי`), missing the Gen 27:36 conjugation error.

**Solutions Implemented**:
1. **Hybrid Haiku false-positive filter** (`scripture_verifier.py`): New `filter_false_positives()` function sends regex verifier mismatches to Claude Haiku 4.5 with surrounding context. Haiku classifies each as GENUINE_ERROR, FALSE_POSITIVE, or MINOR. Cost: ~$0.002/psalm. Activated via `--haiku-filter` flag on standalone runner and both pipeline runners.
2. **Report contamination fix** (`scripture_verifier.py`): New `_strip_appended_reports()` strips any "SCRIPTURE CITATION CHECK" block from the text before analysis, preventing the verifier from re-reading its own old output.
3. **Word-level consonantal matching** (`scripture_verifier.py`): New `_words_match()` replaces pure substring check — each quoted consonantal word must appear as a *complete* word in the actual verse, in sequence. Catches conjugation mismatches (e.g., `עקבני` vs `ויעקבני`) while still passing legitimate vowel-pointing differences.
4. **Pipeline integration**: Added `--haiku-filter` argument to `run_enhanced_pipeline.py`, `run_si_pipeline.py`, and `run_scripture_verifier.py`. Added Claude Haiku 4.5 pricing to `cost_tracker.py`.

**Prototype Exploration — Full Haiku Extraction (test_haiku_verifier.py)**:
- Also tested a two-step approach where Haiku extracts ALL citations (Step 1) and judges mismatches (Step 2). Cost: ~$0.023/psalm.
- Haiku extraction eliminated false positives perfectly but risked silently "correcting" quoted Hebrew during extraction (e.g., adding the missing `אֱלֹהֶיךָ` to Ex 20:7).
- The hybrid approach (regex extraction + Haiku judgment) was chosen as the better architecture: cheaper ($0.002 vs $0.023), no extraction risk, and the regex catches all citation patterns programmatically.

**Test Results — Psalm 41 (hybrid)**:
- Ps 72:18-19 false positive: FILTERED by Haiku (correctly identified piyyut/editorial mismatch)
- Gen 27:36 conjugation error: KEPT by Haiku (correctly identified verb form mismatch as genuine)
- Ex 20:7 report contamination: ELIMINATED by `_strip_appended_reports()` (was never a real error)
- Batch test (Ps 22, 34): Haiku correctly filtered 3 additional false positives ($0.0036 total)

**Files Modified**:
- `src/utils/scripture_verifier.py` — Added `_strip_appended_reports()`, `_words_match()`, `filter_false_positives()`; replaced consonantal substring with word-level match in both Pattern A/B and Pattern C paths
- `src/utils/cost_tracker.py` — Added `claude-haiku-4-5-20251001` pricing
- `scripts/run_scripture_verifier.py` — Added `--haiku-filter` flag and `filter_false_positives` integration
- `scripts/run_enhanced_pipeline.py` — Added `--haiku-filter` flag and Step 5a½ Haiku filter integration
- `scripts/run_si_pipeline.py` — Same `--haiku-filter` integration
- `scripts/test_haiku_verifier.py` — **[NEW]** Prototype exploration script (two-step Haiku extraction + judgment)
- `docs/session_tracking/IMPLEMENTATION_LOG.md` — This entry
- `docs/session_tracking/PROJECT_STATUS.md` — Session 310 entry
- `docs/session_tracking/scriptReferences.md` — Updated verifier descriptions

---

## Session 309 (2026-03-17): Citation Verifier Refinements & Copy Editor Integration Hardening

**Objective**: Make the citation verifier's output safe for copy editor consumption (avoiding false-positive overreaction), fix leaked instructions in DOCX, add Pattern C citation extraction, and test pipeline end-to-end on Psalm 41.

**Problems Identified**:
- The `format_fix_prompt()` used commanding language ("FIX THESE FIRST") that primed the copy editor into an overly aggressive correction posture, producing more changes than necessary.
- The copy editor echoed the supplementary citation-check instructions verbatim into its output, which then appeared in the generated DOCX as visible content.
- The verifier only detected Hebrew quotations that appear *before* a citation parenthetical (Patterns A/B). A common format — Hebrew text *inside* the parenthetical after a colon, e.g. `(Gen 27:36: עֲקָבַנִי זֶה פַעֲמַיִם, "...")` — was invisible (Pattern C, found in 18 psalms).
- The standalone `run_scripture_verifier.py` defaulted to `copy_edited.md` over `print_ready.md`, which masked errors already corrected by the copy editor.

**Solutions Implemented**:
1. **Softened citation fix prompt** (`scripture_verifier.py`): Replaced "SCRIPTURE CITATION ERRORS DETECTED — FIX THESE FIRST" with "SCRIPTURE CITATION CHECK (automated — apply with judgment)" plus methodology disclaimer explaining false-positive scenarios (liturgical adaptations, allusions, vowel differences). Added instruction to prefix citation-driven corrections with `[CITATION FIX]` in the Changes section.
2. **Strip echoed supplementary prompt** (`copy_editor.py`): Added `_strip_echoed_supplementary()` method that detects and removes any "SCRIPTURE CITATION CHECK" text the LLM echoes into its output, called between LLM response and `_split_changes()`.
3. **Pattern C citation extraction** (`scripture_verifier.py`): Added `_CITATION_INLINE_RE` regex and `_extract_hebrew_from_inline()` helper for citations with Hebrew inside parentheticals. Runs as a second pass in `verify_citations()` — existing Pattern A/B logic untouched. Includes same self-quote filter and MIN_HEBREW_WORDS threshold.
4. **Fixed standalone runner default** (`run_scripture_verifier.py`): Changed file priority from copy_edited → print_ready to print_ready → copy_edited, matching pipeline Step 5a½ behavior.

**Test Results — Psalm 41**:
- Copy editor correctly fixed Ex 20:7 misquote (tagged `[CITATION FIX]`), left false positive alone, and independently caught Gen 27:36 conjugation error.
- DOCX output clean — no leaked instructions.
- Pattern C tested across 15 psalms: zero regressions, new legitimate catches in Psalms 5, 7, 34 (paraphrases, spelling, word reordering).

**Files Modified**:
- `src/utils/scripture_verifier.py` — Softened `format_fix_prompt()` with methodology disclaimer and `[CITATION FIX]` tag instruction; added `_CITATION_INLINE_RE` regex, `_extract_hebrew_from_inline()`, and Pattern C pass in `verify_citations()`
- `src/agents/copy_editor.py` — Added `_strip_echoed_supplementary()` to remove echoed citation instructions from LLM output
- `scripts/run_scripture_verifier.py` — Changed default input file priority to print_ready over copy_edited
- `docs/session_tracking/IMPLEMENTATION_LOG.md` — This entry
- `docs/session_tracking/PROJECT_STATUS.md` — Session 309 entry

**Next Session Consideration**: Evaluate whether using Haiku to identify quotations, launch DB searches, and filter false positives would improve citation verification accuracy beyond the current regex approach.

---

## Session 308 (2026-03-17): Scripture Citation Verifier

**Objective**: Build a zero-LLM-cost scripture citation verifier to catch misquoted Hebrew passages, and integrate it into the pipeline to feed corrections to the copy editor.

**Problems Identified**:
- Psalm 41 commentary contained a misquote from Ex 20:7 — `לֹא תִשָּׂא אֶת שֵׁם ה׳ לַשָּׁוְא` is missing `אֱלֹהֶיךָ`. The writer LLM dropped the word and the copy editor didn't catch it.
- Initial verifier had high false-positive rate (19 issues) due to greedy regex, vowel pointing differences, self-quotes, and shared Hebrew phrases matching multiple citations.

**Solutions Implemented**:
1. **`src/utils/scripture_verifier.py`** (new, ~690 lines): Regex-based citation extraction, word-level Hebrew phrase detection, text normalization (cantillation stripping, divine name variants `ה׳`→`יהוה`, `אלק`→`אלה`), substring matching with consonantal-only fallback.
2. **False-positive mitigations** (7 techniques across 5 iterations): MIN_HEBREW_WORDS=3 threshold, psalm self-quote filter, intervening-citation check, expanded divine name normalization, punctuation stripping in consonantal comparison.
3. **`scripts/run_scripture_verifier.py`** (new): Standalone runner with `--fix` flag for copy-editor fix pass.
4. **Pipeline integration**: Added Step 5a½ to both `run_enhanced_pipeline.py` and `run_si_pipeline.py` — runs verifier on print-ready file BEFORE the copy editor, generates fix prompt via `format_fix_prompt()`, passes to copy editor via new `supplementary_prompt` parameter.
5. **`src/agents/copy_editor.py`**: Added `supplementary_prompt` parameter to `edit_commentary()` and `_call_editor()`, appended to user message to provide citation verification context.

**Test Results — Psalm 41**: Correctly detects Ex 20:7 misquote with only 1 false positive (piyyut text) out of ~30+ citations. False positives reduced from 19 → 1 across 5 iterations.

**Files Modified**:
- `src/utils/scripture_verifier.py` — **[NEW]** Core verifier module
- `scripts/run_scripture_verifier.py` — **[NEW]** Standalone runner
- `src/agents/copy_editor.py` — Added `supplementary_prompt` parameter
- `scripts/run_enhanced_pipeline.py` — Added Step 5a½ citation verification before copy editor
- `scripts/run_si_pipeline.py` — Same Step 5a½ integration
- `docs/session_tracking/PROJECT_STATUS.md` — Session 308 entry
- `docs/session_tracking/scriptReferences.md` — New verifier entries
- `docs/session_tracking/IMPLEMENTATION_LOG.md` — This entry

---

## Session 307 (2026-03-16): Fix Garbled Inline Hebrew in DOCX — Block Extraction for Long Segments

**Objective**: Fix garbled multi-word Hebrew text in Psalm 41's DOCX output, where Word's BiDi algorithm scrambled the visual order of a 15-word liturgical Hebrew quotation embedded inline in an English paragraph.

**Problems Identified**:
- Long inline Hebrew segments (6+ words) containing internal punctuation (colons, semicolons) are split by Word's BiDi algorithm into separate RTL runs, which Word then reorders independently — garbling the visual word order.
- The existing LRM fix (Session 303) correctly handled Hebrew+punctuation boundaries for short segments but was insufficient for long multi-word segments where the RTL run reordering was the core issue.
- Even after fixing word order with LRO reversal, long Hebrew segments wrapped awkwardly across lines: the LRO-forced LTR display caused the beginning of the quote to appear on the LOWER line (English-style wrapping instead of RTL wrapping).

**Solutions Implemented**:
1. **`_reverse_bare_hebrew_segments` method**: New centralized handler that detects 3+ consecutive Hebrew words in mixed English/Hebrew text and applies grapheme-cluster reversal + LRO/PDF wrapping. Integrated into all 5 DOCX BiDi code paths (`_process_text_rtl`, `_process_markdown_formatting`, `_add_formatted_content` x2, `_add_paragraph_with_soft_breaks`).
2. **Block extraction for long segments (6+ words)**: `_split_long_hebrew_block` detects inline Hebrew of 6+ words and `_add_hebrew_block_paragraph` renders them as standalone RTL paragraphs (w:bidi=1, right-aligned, 0.3" indent, 13pt TNR). Word handles Hebrew line-wrapping natively in RTL paragraphs, fixing the visual wrap direction.
3. **Comma stripping**: Orphaned leading commas/punctuation are stripped from continuation text after extracted Hebrew blocks.
4. **Verse quotation exclusion**: Hebrew segments containing sof-pasuq (׃) are excluded from block extraction so full verse quotations retain their original Aptos 12pt styling via the existing `_reverse_primarily_hebrew_line` path.
5. **Full coverage**: Block extraction integrated into both `_add_paragraph_with_markdown` (intro/liturgical) and `_add_paragraph_with_soft_breaks` (verse-by-verse commentary).

**Files Modified**:
- `src/utils/document_generator.py` — Added `_reverse_bare_hebrew_segments`, `_split_long_hebrew_block`, `_add_hebrew_block_paragraph`; integrated bare Hebrew reversal into 5 code paths; added block extraction to 2 paragraph-creating methods

---

## Session 306 (2026-03-15): Fix Displaced Liturgical Content Recovery in DOCX

**Objective**: Fix a bug where the liturgy section in the generated DOCX was interrupted by spurious "Verse-by-Verse Commentary" and "Verse 9" headers (Psalm 42).

**Problems Identified**:
- The copy editor LLM displaced per-verse liturgical key verse entries (`**Verse 9** is the most liturgically mobile...`, `**Verse 2's** imagery...`, etc.) from the introduction's "Key Verses and Phrases in Liturgy" section into the start of the "Verse-by-Verse Commentary" section.
- The existing recovery heuristic in `_extract_sections_from_copy_edited()` failed for two reasons:
  1. The intro's Key Verses section retained an introductory paragraph (~200 chars), so the `< 100` char threshold check passed incorrectly, concluding the section was fully populated.
  2. The regex `^\*\*Verse[s]?\s+\d+` matched the displaced `**Verse 9**` at position 0 of the verse text, so the `> 50` offset check also failed — the displaced content *started with* a bold verse reference.
- As a result, the DOCX generator treated `**Verse 9**` as the first verse commentary entry, producing a "Verse 9" heading containing liturgical content inside what should have been the liturgy section.

**Solutions Implemented**:
1. **Replaced detection logic with standalone verse header regex**: Instead of looking for any `**Verse N**` pattern (which matches inline liturgical references), the recovery now searches for the first **standalone** verse header — one where `**Verse N**` is the entire line content (`^\*\*Verses?\s+\d+(?:\s*[-–]\s*\d+)?\*\*\s*$`). This correctly distinguishes liturgical entries like `**Verse 9** is the most liturgically mobile verse...` (text continues on same line) from actual verse commentary headers like `**Verse 1**` (standalone line followed by Hebrew text).
2. **Removed the flawed `< 100` char threshold**: The old heuristic checked whether the intro's Key Verses section had < 100 chars of content after the header. This failed when the LLM kept the introductory paragraph but displaced the per-verse entries. The new logic does not depend on intro content length — it works entirely from the verses section side.
3. **Applied to both pipelines**: `run_enhanced_pipeline.py` and `run_si_pipeline.py`.
4. **Verified**: Re-ran Psalm 42 extraction + DOCX generation. Recovery triggered correctly (2,468 chars of displaced liturgical content moved back), producing a clean DOCX.

**Files Modified**:
- `scripts/run_enhanced_pipeline.py` — Replaced displaced liturgical content detection in `_extract_sections_from_copy_edited()` with standalone verse header regex
- `scripts/run_si_pipeline.py` — Same fix applied

---

## Session 305 (2026-03-15): Remove Auto-Skip-If-Exists Behavior

**Objective**: Eliminate implicit "skip if output exists" behavior so every pipeline step always runs and overwrites previous output unless explicitly skipped by the user.

**Problems Identified**:
- Steps 2b (Questions), 2c (Insights), and 5b (Copy Editor) silently skipped regeneration when their output files already existed, even without `--resume` or `--skip-*` flags.
- Step 5c (copy-edit extraction) was gated on `not skip_copy_editor`, so passing `--skip-copy-editor` also prevented extraction of existing copy-edited content into the intro/verses files needed for DOCX generation.
- This caused `--skip-macro --skip-micro --skip-writer --skip-copy-editor` (intending to regenerate DOCX only) to produce no DOCX, because the intro/verses files were missing and Step 5c refused to recreate them.

**Solutions Implemented**:
1. **Removed auto-skip in Step 2b (Questions)**: Removed `if reader_questions_file.exists(): skip` check. Now always regenerates when `--include-questions` is passed. Default behavior (skipped) unchanged.
2. **Removed auto-skip in Step 2c (Insights)**: Removed `if insights_file.exists(): load existing` check. Now always regenerates when `--include-insights` is passed. Default behavior (skipped) unchanged.
3. **Removed auto-skip in Step 5b (Copy Editor)**: Removed `if copy_edited_file.exists(): skip` check. Now always runs unless `--skip-copy-editor` is passed.
4. **Fixed Step 5c gating**: Changed condition from `copy_edited_file.exists() and not skip_copy_editor` to just `copy_edited_file.exists()`. Extraction of existing copy-edited content now works even when the copy editor step itself is skipped.
5. **Applied all changes to both pipelines**: `run_enhanced_pipeline.py` and `run_si_pipeline.py`.

**Preserved Behavior**:
- `--resume` flag still auto-detects completed steps (explicit user choice)
- `--skip-*` flags still prevent their respective steps from running
- Questions and insights still default to skipped (opt-in via `--include-questions`/`--include-insights`)

**Files Modified**:
- `scripts/run_enhanced_pipeline.py` — Removed auto-skip checks in Steps 2b, 2c, 5b; fixed Step 5c gating
- `scripts/run_si_pipeline.py` — Same changes as enhanced pipeline

---

## Session 304 (2026-03-15): Copy Editor Output Readability — Word-Level Diff & Rationale

**Objective**: Improve the copy editor's diff and changes output files so changes are easy to find and understand.

**Problems Identified**:
- The diff file used Python's `unified_diff` which showed entire paragraphs as +/- lines. Since each paragraph is one long line, a single word change made the whole paragraph appear as changed, burying the actual edit.
- The changes file listed *what* changed but not *why* — e.g., no explanation for why the Mesha Stele reference was removed.
- No cross-references between the changes and diff files.
- `_count_changes` had a bug: numbered list items like `1. [7]...` were counted as Category 1 instead of Category 7.

**Solutions Implemented**:
1. **System prompt update**: Changed the `## Changes` instructions to request numbered changes with verse/section location and a WHY rationale sentence explaining what was wrong with the original.
2. **Word-level diff generator**: Replaced `unified_diff` with a `SequenceMatcher`-based approach that finds word-level changes within each paragraph, shows only ~12 words of context on each side, and bolds the changed words. Added merge logic (MERGE_GAP=6) so nearby word changes within a paragraph produce a single diff entry.
3. **Section tracking**: New `_track_sections()` method labels each diff with its verse/section (e.g., "Verse 6", "The Intelligence of Compassion", "Liturgical — Full Psalm").
4. **Cross-reference links**: Changes file header links to the diff file; diff file header links to the changes file.
5. **Fixed `_count_changes`**: Now looks specifically for `[N]` bracket format instead of matching item numbers.

**Tested**: Ran against existing Psalm 41 original vs. copy-edited files — 37 raw word changes merged to 22 focused diff entries.

**Files Modified**:
- `src/agents/copy_editor.py` — System prompt changes section, replaced `_generate_diff()`, added `_track_sections()`, `_find_word_changes()`, `_truncate()`, fixed `_count_changes()`, added cross-reference in `edit_commentary()`

---

## Session 303 (2026-03-15): BiDi DOCX Fix — LRM Insertion

**Objective**: Implement the LRM-based BiDi fix planned in Session 302 to prevent Word from scrambling Hebrew+punctuation+Hebrew sequences.

**Problems Identified**:
- When a neutral character (colon, semicolon, comma) appears between two Hebrew segments in an LTR paragraph, Word's BiDi algorithm resolves the neutral to RTL, causing the entire Hebrew+neutral+Hebrew sequence to display as one RTL run — visually scrambling word order (e.g., `חפץ: חָפָצְתִּי` in Psalm 40 verses 9 and 15).
- Previous attempt (Session 301) used RLI/PDI (Unicode 6.3 isolates) which Word renders as visible dashed boxes.

**Solutions Implemented**:
1. **LRM insertion in all 5 DOCX code paths**: Added `re.sub(r'([\u05D0-\u05EA][\u0590-\u05FF]*)([:;,])', rf'\1\2{LRM}', text)` after verse-reference handling and before trailing-punctuation RLM anchoring. The LRM (U+200E) creates an explicit LTR boundary that prevents the neutral character from joining the RTL run.
   - `_process_text_rtl()` — centralized function
   - `_process_markdown_formatting()` plain text else branch
   - `_add_formatted_content()` nested formatting else branch
   - `_add_formatted_content()` no-nested else branch
   - `_add_paragraph_with_soft_breaks()` else branch
2. **Tested**: Regenerated Psalm 40 and Psalm 22 DOCX files successfully — no errors, no regressions.

**Files Modified**:
- `src/utils/document_generator.py` — LRM insertion in 5 code paths (15 lines added)

---

## Session 302 (2026-03-15): Copy Editor Critical Reading Stance & BiDi Plan

**Objective**: Address the 3 remaining content quality issues the copy editor missed in Session 301 (false contrast v.1, opaque logic v.6, weak parallel v.8), and document a ready-to-implement BiDi fix plan for next session.

**Problems Identified**:
- The copy editor's category-based scanning was pattern-matching rather than reasoning about arguments. 3/5 targeted issues were missed despite having correct categories (9d, 9f, 6).
- The BiDi DOCX fix from Session 301 used RLI/PDI (Unicode 6.3 isolates), which Word renders as visible dashed boxes — fundamentally wrong approach.

**Changes Implemented**:

1. **Copy Editor — Critical Reading Stance (meta-reasoning preamble)**:
   - Added "CRITICAL READING STANCE" section before the error categories, instructing the LLM to identify each paragraph's core claim and evidence, then ask: "Would a thoughtful first-time reader find this convincing?"
   - This shifts the cognitive approach from pattern-matching to argument evaluation.

2. **Category 6 — Strengthened with concrete test**:
   - Added: "Test: does the parallel illuminate something specific about the psalm that would be harder to see without it?"
   - Added: "Remove or replace parallels that share only a keyword."
   - Added warning about "but where X does Y, the psalmist does Z" pattern as a signal of forced comparison.

3. **Category 9d — Added concrete test for false contrasts**:
   - Added: "Test: cover the conjunction and read the two statements — are they complementary rather than opposed?"

4. **Category 9f — Added concrete test for opaque logic**:
   - Added: "Test: can you explain, from what is written in the text alone, each logical step from citation to conclusion?"

5. **Re-run Results — Psalm 40**: 17 changes (up from 14 in Session 301).
   - All 3 previously missed issues now caught: false contrast v.1 (9d), opaque logic v.6 (9f), weak parallel v.8 (6).
   - Category 6 now more aggressive — also removed Horace, Baudelaire, Euripides, Beckett parallels. Some may be overcorrections where the contrast itself is the insight.

6. **BiDi Fix Plan — Documented for Next Session**:
   - Approach: Use LRM (U+200E) instead of RLI/PDI. Insert after Hebrew+punctuation to create directional boundaries.
   - Detailed implementation plan with code, 5 code paths identified, safety analysis, and testing checklist.
   - Saved in `docs/session_tracking/BIDI_FIX_NOTES_SESSION_301.md` (appended Session 302 section).

**Files Modified**:
- `src/agents/copy_editor.py` — Critical reading stance, strengthened categories 6, 9d, 9f
- `output/psalm_40/psalm_040_copy_edited.md` — Re-run output (17 changes)
- `output/psalm_40/psalm_040_copy_edit_changes.md` — Change list
- `output/psalm_40/psalm_040_copy_edit_diff.md` — Diff
- `docs/session_tracking/BIDI_FIX_NOTES_SESSION_301.md` — Session 302 implementation plan appended
- `docs/session_tracking/PROJECT_STATUS.md` — Session 302 entry
- `docs/session_tracking/IMPLEMENTATION_LOG.md` — This entry
- `CLAUDE.md` — Updated recent changes

---

## Session 301 (2026-03-14): Copy Editor Prompt Hardening (9d–9g)

**Objective**: Address 7 issues found during Psalm 40 review — 5 content quality gaps the copy editor missed, and 2 bidirectional text rendering bugs (markdown and DOCX).

**Problems Identified**:
- 5 content quality issues the copy editor should have caught: false contrast (v. 1), overclaimed scope (v. 3), opaque scholarly logic (v. 6), weak literary parallel (v. 8), factually wrong analogy (v. 13)
- 2 BiDi rendering bugs: Hebrew word order scrambled in markdown (v. 15) and DOCX (v. 9) when neutral characters (colons) appear between Hebrew words

**Changes Implemented**:

1. **Copy Editor Prompt — 4 New Sub-categories (9d–9g)**:
   - **(d) FALSE CONTRASTS**: Flags adversative conjunctions ("yet," "but") where no actual tension exists.
   - **(e) OVERCLAIMED SCOPE**: Catches totalizing language ("spans the entire cosmos") unsupported by evidence.
   - **(f) OPAQUE SCHOLARLY LOGIC**: Requires citations to include the reasoning chain, not just a reference.
   - **(g) FACTUALLY WRONG ANALOGIES**: Catches incorrect physical-world comparisons (e.g., head-hairs as "most countable").
   - Also fixed 4 typos in the existing prompt ("grammatial," "first persion," "pleural," "specificausal").

2. **Copy Editor Re-run for Psalm 40**: Re-ran with new prompt; auto-caught 2 of 5 issues (overclaimed scope in v. 3, factually wrong head-hair analogy in v. 13) plus 12 other corrections.

3. **BiDi Fixes — Attempted and Reverted**:
   - Attempted MD fix (LRM insertion after Hebrew+punctuation) and DOCX fix (RLI/PDI wrapping for bare inline Hebrew) plus code deduplication in `document_generator.py`.
   - Both introduced serious regressions and were fully reverted.
   - Detailed notes saved in `docs/session_tracking/BIDI_FIX_NOTES_SESSION_301.md` for next session.

**Files Modified**:
- `src/agents/copy_editor.py` — New sub-categories 9d–9g, typo fixes
- `output/psalm_40/psalm_040_copy_edited.md` — Copy editor re-run output (14 auto-changes)
- `docs/session_tracking/BIDI_FIX_NOTES_SESSION_301.md` — BiDi fix notes for retry next session
- `docs/session_tracking/PROJECT_STATUS.md` — Session 301 entry
- `docs/session_tracking/IMPLEMENTATION_LOG.md` — This entry
- `CLAUDE.md` — Updated recent changes

---

