# Session 384 — Findings and Plan: Concordance, Literary Echoes, and an Overnight Writer Test

**Date**: 2026-09-28. **Trigger**: the author's review of Psalm 76 arm B (Opus 5.5). Four requests: (1) review the concordance, including why the counts differ between A and B; (2) propose a better literary-echoes pipeline using current models; (3) the writer used too few echoes, and about 0.75 per verse is fine if they are good; (4) review the writer prompt and plan an autonomous overnight test of prompt changes and models, especially Opus 5.5 and GPT-6 Sol. The author's central complaint is that the writer loses the forest for the trees.

**Nothing in `src/` changed this session.** Every figure below was measured at $0 against the saved Ps 76 A/B artifacts and `database/tanakh.db`. The one exception is the free model-listing calls used to confirm which models the keys can reach.

Evidence kept: `archive/psalm_76_S384_planning/` (intertext-radar prototype + its Ps 76 output).

---

## 0. Summary

1. **The concordance has two retrieval bugs, and it is also where B's originality came from.** S383 traced B's best finds to synthesis discovery. One step further upstream, synthesis discovery found them in **B's concordance results**. Hosea 2:20 came from B's `שבר קשת` search, Exod 15 from `רכב סוס`, Josh 14:15 from `שקטה`, and Isa 37:33 from `מגן`. A never ran any of those searches. The bugs:
   - **Wrong-lemma resolution.** The resolver picks the most common lemma for a surface form anywhere in the Bible, not the one in the verse. In Ps 76 that gave בצר→צר ("foe/distress"), רדם→רדה ("to rule"), חמת→חמת (Hamath, or a wineskin, instead of חֵמָה "wrath"), and ענו→ענה ("to answer" instead of עָנָו "lowly"). About 4–6 of each run's ~25 searches pulled verses about the wrong word.
   - **Alphabetical truncation.** The SQL sorts by book *name* and then applies `LIMIT 50`, so for any word with more than 50 hits, Psalms and every book after "P" is cut before the random sampler ever sees it. מגן has 19 Psalms verses and kept 4; נצח kept 12 of 73; ענה and ירא kept 0 of 53 and 0 of 73. The `רכב+סוס` search lost both Psalms hits, including Ps 20:8, "some trust in chariots, some in horses, but **we**…", which is the one parallel that speaks directly to B's own "no one says *we*" thesis.
   - **The methods-section count means little.** It is a sum of capped hits over whatever queries the micro analyst happened to choose. It is not the total number of occurrences, and it is not what the writer saw, which is 10 per search.
   - **A $0 fix goes beyond repair.** An IDF-weighted shared-vocabulary "intertext radar" (a prototype, ~60 lines) finds, in its top 45 for Ps 76: Hosea 2:20, Ps 46:10, Exod 15:1, Nahum 3:18, **Isa 43:17** (horse and chariot that "lie down and shall not rise"; no arm, no synthesis-discovery file and no bundle ever found it), Jer 30:10/46:27, Isa 7:4, Hab 3:8, Ezek 38:15 (Gog, Radak's reading) and 2 Kgs 6–7.
2. **The echoes pipeline is built for novelty across the series, not for aptness to this psalm.** Its "Second Echo Principle" makes Gemini skip the obvious match and record it in a "Default bypassed" line, which is then thrown away. For Ps 76 the discarded defaults were **Byron's *Destruction of Sennacherib*** (a poem about the very event the LXX heading assigns to this psalm), **the Iliad's "sleep of bronze"** (Homer is banned outright), **Revelation 8:1's silence in heaven**, Ozymandias, and the Magnificat. Several are better than the kept entries. Also, **12 of 18 quotations needed correction** at verification, because the generator quotes from memory.
3. **The writer rationed echoes because the prompt told it to.** "Sparingly… at most 1–2 in the essay" and "at least 2–3" in the commentary became a target: B's thinking caps echoes at "two or three in the commentary plus one in the essay". It used 4 of 18, which is 0.3 per verse. The thinking also says outright: *"quoting the entire thing raises copyright concerns… trim quotes to a couple lines."*
4. **The forest-for-the-trees problem is built into the prompt, and it is measurable.**
   - About 26% of the 76K-character prompt is about handling commentators. RULE 8b alone runs 15.4K characters, the largest section. The part asking *what the poem is doing* is about 1.5K (2%).
   - **55–60% of the writer's thinking summary, in both A and B, is spent on commentators.** Your "it planned twice" observation is literally right, and the prompt causes it: RULE 8b says *"Rank before you cut. Across the whole psalm, sort every candidate gloss,"* then *"COUNT THEM BEFORE YOU FINISH."* B ranked every gloss in paragraphs 7–30 of its thinking and re-ranked them verse by verse in 78–125. The governing argument got about 5 paragraphs out of 126.
   - The writer meets the poem through 205K characters of apparatus, and **no input anywhere is a reading of the poem as an experience**. The macro analysis is a telegraphic structural thesis.
   - The wit was planned as a quota ("I want to weave in a few sharp moments of wit"), because RULE 13 says "don't be miserly."
5. **Model access is confirmed.** The keys reach `gpt-6-sol`, `gpt-6-astra` and `gpt-6-luna` (launched 2026-09-22; Sol is $2/$10 on a promo guaranteed through 2026-11-21), `claude-fable-5-1`, `claude-opus-5-5`, `gemini-3.1-pro-preview` and `deep-research-pro-preview`. **Two silent traps must be fixed before any GPT-6 run**:
   - The writer's GPT path would send `gpt-6-sol` with `max_tokens=16000` and **no reasoning effort**. Its guard checks `"gpt-5" in model`.
   - There is no pricing row, so the cost tracker would report $0 (the S377 failure).

---

## 1. Concordance (item 1)

### 1.1 Why A and B report different counts
The number printed as "Concordance Entries Reviewed" (A: 529, B: 828) is `sum(len(bundle.results))` over the searches the micro analyst requested. Three things move it, and none of them measures anything about the psalm:
- **Different queries.** B's macro was different, so its micro chose different searches. Only 7 of ~25 queries are string-identical across the arms. About 8 more are the same idea in a different inflection (אבירי/אביר, שקט/שקטה, מורא/מוֹרָא, …), and the rest are different searches.
- **Different alternates.** The same query `בצר` returned 48 in A and 74 in B.
- **Caps.** Most counts in the 39–50 range are artifacts of `max_results=50` after dropping self-matches.

The writer sees **10 sampled lines per search**, whatever the header count says.

### 1.2 Defects (all measured on Ps 76)
| # | Defect | Where | Effect on Ps 76 |
|---|---|---|---|
| D1 | `_resolve_lemma` takes the Bible-wide most frequent lemma for a surface form | `concordance/search.py` ~962 | בצר→צר, רדם→רדה, חמת→Hamath, ענו→ענה, תודה for תּוֹדֶךָּ (from ידה). Roughly **4–6 of ~25 searches per run are about a different word.** The psalm's own tokens already carry the correct BHSA lemma (נִרְדָּם→רדם, חֲמַת→חמה, עַנְוֵי→ענו). |
| D2 | `ORDER BY c.book_name` (alphabetical) + `LIMIT max_results` before any sampling | `search_lemma`, `search_lemmas_in_verse`, `search_word` | For lemmas with more than 50 hits, the pool is Amos, Chronicles, Daniel, Deuteronomy… Psalms is dropped. מגן: 4 of 19 Psalms verses kept. נצח: 12 of 73. ענה: 0 of 53. ירא: 0 of 73. `רכב+סוס`: 0 of 2 (Ps 20:8 lost). The S350 "random spread" sampler was built to fight exactly this bias, but it samples from the already-truncated pool. |
| D3 | The header count is not the true frequency, and there is no distribution | `research_assembler` | The writer cannot tell "rare, and concentrated in the Prophets" from "everywhere." |
| D4 | Wasted queries | micro prompt/selection | נצח and מזמור come from the **superscription** (all 57 מזמור hits are psalm headings); `ידוע` is not the verse's form (נוֹדָע); `חמה תודה` returned 0. |
| D5 | Lemma coverage gaps | DB | 3.0% of tokens have no lemma (1.9% in Psalms), including סוּכּוֹ in 76:3. Minor. |

### 1.3 Are we using the concordance's affordances well? Mostly not.
We have a lemma-indexed table of all 312K tokens. We use it as 25 independent "look up word X" calls chosen by an LLM. The finds that made B original are **clusters of shared vocabulary** (bow + sword + war + break → Hosea 2:20; horse + chariot + majestic + awesome + name → Exod 15). A database finds those exhaustively; an LLM finds them only when it happens to guess the right pair of words.

**Prototype:** `archive/psalm_76_S384_planning/intertext_radar_prototype.py`. For every verse and every 2-verse window of the psalm, it scores every Bible verse by summed IDF of shared content lemmas (stop list plus a frequency ceiling). Output: `radar_ps76_top45.txt`. Its hits: Hos 2:20, Ps 46:10, Exod 15:1, Nah 3:18, Isa 43:17, Jer 30:10/46:27, Isa 7:4, Ps 132:5, Ps 22:26, Hab 3:8, Ezek 38:15, 2 Kgs 6–7, Deut 20:1. Its noise is superscription matches (Ps 67:1 and the like), which are trivially filtered.

### 1.4 Renovation plan (≈1 session, $0 at runtime)
- **R1 In-context lemma resolution.** Resolve each query against the source psalm's own tokens first, then fall back to the global most-frequent lemma. Collocations get the same treatment per word. Unit tests: the 5 Ps 76 mis-resolutions above.
- **R2 Remove pre-sample truncation.** Fetch all hits (the lemma index makes even ידע at ~900 verses cheap), order them canonically, then do a **stratified** display sample: Psalms first, then Torah, Prophets and other Writings, with pinned targets kept. Print a distribution line under each header: `143 verses · Torah 12 · Prophets 61 · Psalms 38 · Writings 32`.
- **R3 Intertext radar as a new bundle section**, "SHARED-VOCABULARY PARALLELS", ~5–8K chars. Top 20–30 passages, Hebrew with the shared lemmas **bolded**; superscription excluded; a chapter-level aggregate ("Exodus 15 shares vocabulary with vv. 5, 7, 8") to catch **sustained dialogues**, which is how "the Song at the Sea run backwards" would be found by computation. Feed it to both synthesis discovery and the writer. Deterministic, $0.
- **R4 An honest methods line.** "N lemma searches · X distinct passages retrieved (true totals) · Y shown; radar: Z passages."
- **R5 Micro query schema.** Let the analyst name a *word in a verse* ("v.10 word 5") instead of retyping a surface string, so the lemma is exact by construction. Drop superscription words from root traces.
- **R6 (optional) Semantic-field searches.** A lemma set such as sleep = {נום, ישן, רדם, תרדמה}, which the lemma column makes trivial.

**Validation:** re-run only the concordance stage on the saved A and B request sets and diff the bundles. Then check the radar on 3 more finished psalms against their guides, to confirm it surfaces parallels the writer liked and not just noise.

---

## 2. Literary echoes (item 2)

### 2.1 How it works now
Gemini 3.1 Pro generates (12 entries), then Gemini gap-fills (6), then gpt-5.6-terra verifies each entry with web search (18 calls), then the document is assembled deterministically. On Ps 76: **$1.18, of which verification was $0.81 (69%)**. 12 of 18 entries were "corrected," 0 rejected. An author ledger banned 81 authors for this run; Homer, Dante, Virgil and Ovid are banned outright.

### 2.2 What is wrong with it
- **It optimizes the wrong objective.** Novelty across the series (the Second Echo Principle, the author bans) beats aptness to *this* verse, and the best candidates get thrown away (see §0.2).
- **It quotes from memory.** Two-thirds of the quotations were wrong and repaired afterwards, and verification is where most of the money goes.
- **It has one generator family.** Anthropic models were blocked as generators (S374: an output content filter, very likely the lyric-reproduction classifier, since the prompt demands verbatim song lyrics).
- **Its interpretive prose is generic** ("perfectly illuminates", "In both texts…"). The writer rewrites it anyway, so it is dead weight at ~19K chars of bundle.
- **It covers only literature.** Your ask is cross-*domain*.

### 2.3 Ideas, ranked by expected value per dollar
1. **Aptness first, novelty as a tie-break.** Keep the "Default bypassed" candidates in the pool instead of discarding them. Replace the second-echo *rule* with a judged choice between tiers. Lift the whole-author bans (Homer's "sleep of bronze" is the textbook echo for נָמוּ שְׁנָתָם) and keep only work-level bans on truly worn items. Turn the ledger into information the judge sees, not a prohibition. **$0.**
2. **Propose, then retrieve.** Generators name *author + work + locus + why*, with **no quotation**. A retrieval call (GPT-6 Sol + `web_search`) fetches the exact text and a standard translation, with source URL and public-domain/in-copyright status. This removes misquotation at the source and absorbs most of today's verification cost.
3. **Several generators from different model families.** GPT-6 Sol (high) + Gemini 3.1 Pro, each proposing independently, because each family has different reflexes. S374 saw 11 of 13 new authors when a second family ran. About +$0.3.
4. **A judge stage.** Opus 5.5 or GPT-6 Sol (xhigh) ranks the pool per verse cluster on a rubric: the *specific* shared move (image, syntax or structure, not theme); whether the psalm reads differently afterwards; force; surprise; quotability. Pick ~0.75 × verses finalists plus alternates.
5. **Resonances beyond literature**, a new section with the same propose → retrieve → judge flow. It would cover:
   - music (Handel's *Israel in Egypt* on "the horse and his rider");
   - artifacts and iconography (**Sennacherib's own prism**, "Hezekiah… like a bird in a cage", the enemy's account of the same siege; **Assyrian tribute-procession reliefs**, which v. 12 inverts by having the nations bring tribute to God rather than to the Assyrian king);
   - history (Drumclog, 1679);
   - psychology (the literature on awe and freeze states, for the "stunned into stillness" of v. 9);
   - film and visual art.
6. **Copyright status on every entry.** Public-domain works carry longer passages. In-copyright works carry the 3–8 lines that hold the echo. That spares the writer the deliberation seen in its thinking (see §3).
7. **Move verification to GPT-6 Sol**, or fold it into (2). Sol is priced at or below terra.
8. **Optional: automate Deep Research.** `deep-research-pro-preview` is reachable on our Gemini key. Today's `data/deep_research/` files appear to be produced by hand. This needs a cost probe first.

**Expected cost:** about the same as today, $1.0–1.5 per psalm. Verification spend shifts into retrieval.
**Test:** old vs new dossiers on Ps 76 + two more psalms, blind, judged by you (a 10-minute read each) and by the §5 panel. Build this **after** the overnight writer test, which needs a fixed dossier.

---

## 3. The writer's use of echoes (item 3)
Three prompt changes, tested inside §5's arms:
- **A budget of about 0.75 per verse** across essay + commentary (≈10 for Ps 76), stated as "the best ones, given room" and not as a minimum to fill. Delete "sparingly / at most 1–2 in the essay"; allow 1–3 in the essay where they serve the argument.
- **A quotation norm**: "the lines that carry the echo, typically 3–8; for public-domain works, quote generously; set lineated."
- **A context statement**: the quotations come from published sources gathered for a private study guide, and quoting in service of commentary is the purpose.

**Candidly:** this removes the over-caution we saw (trimming *public-domain* Trakl and Darío to a couple of lines, and swapping works by copyright status rather than fit). I will not write prompt text aimed at getting a model to reproduce long in-copyright works verbatim. That is the model provider's line to draw, and for a whole modern poem (the 5-line 1945 Jarrell) Opus may still quote only part. Item §2.3(6) makes this mostly moot, because the dossier will lead with public-domain material and flag the rest.

---

## 4. Writer prompt review (item 4): findings

### 4.1 Where the prompt spends its words (76,052 chars)
| Topic | Chars | Share |
|---|---|---|
| Handling commentators (RULE 8b 15.4K, RULE 5 3.1K, item 4 ~1K) | ~19.5K | 26% |
| Hebrew/English formatting and grammar presentation (RULES 1–3c) | ~14K | 18% |
| Prose anti-patterns (RULES 4, 7, 7b, 8, 13) | ~11K | 15% |
| Verse-commentary "items of interest" (12 research categories) | ~13.8K | 18% |
| Essay task (of which "what is the psalm doing") | 5.5K (~1.5K) | 7% (2%) |
| Cross-domain insight | 0 | 0% |

The prompt is 40 sessions of fixes, each a prohibition with a worked failure. It is good at preventing specific bad sentences. **Nothing in it rewards what you are asking for**: a macro, artistic, cross-domain reading of what the poem does and evokes. S371 already found that positive exemplars beat negative ones, and that deleting scaffolding cost no capability.

### 4.2 Where the writer spends its thinking
| | Paragraphs | Share of text in commentator paragraphs | "Tier" mentions |
|---|---|---|---|
| A (Opus 5) | 49 | 55% | 17 |
| B (Opus 5.5) | 126 | 60% | 32 |

B's sequence:
- governing argument (paragraphs 0–6);
- **a psalm-wide commentator ranking** (7–30, "13 verses matched to 13 Tier-1 commentator quotes");
- gathering parallels (34–43);
- translation (44–46);
- **wit planned as a quota** (47);
- drafting the essay (49–77);
- **a second verse-by-verse commentator pass** (78–125).

### 4.3 What the writer reads
The B bundle is 205K chars: commentaries 26.5%, figurative 22%, concordance 19%, echoes 9%, Deep Research 7%, BDB 7%. The poem is under 1%. **Nothing supplied is an experiential reading of the poem.** The macro prompt asks for thesis, genre, structure and devices in telegraphic fragments, and the micro and synthesis-discovery passes work at word or pattern level. So the essay argues from inventories ("Who Holds the Verbs") and not from what hearing the poem does. The Selahs as silences, the turn to direct address at v. 5 (נָאוֹר אַתָּה), and the earth "feared and fell still" are there in B only as data points.

### 4.4 Other findings
- **Wit.** RULE 13's "don't be miserly: aim for a few genuine moments" turns wit into a deliverable. Remove the quota.
- **The model is not the main lever.** B's gain came from its dossier. The writer model matters less than what it is given and what it is asked to do, which is why the overnight test varies both.

---

## 5. Overnight test plan (item 4)

**Principles:**
- The dossier is fixed (B's bundle + B's synthesis discovery + the existing echoes), so the writer is the only variable, except where an arm deliberately adds an input.
- Essays are screened first, because they are cheap and are where the forest lives. Only finalists get full guides.
- Judges come from three model families, with positions swapped.
- **Your A and B essays are included as calibration anchors.** You preferred A overall, so if the judges prefer B, their taste has diverged from yours (the S372 lesson), and I will say so.
- **Your own reading (roar → stunned silence → a vista → call to worship) is never shown to any model.** It is a held-out check: which arms find something like it independently.

### Phase 0: prep and safety (~$3, ~45 min)
1. **Harness.** `scripts/overnight_writer_ab.py`, archived after the session. It will be:
   - resumable, skipping finished arms;
   - protected by a **hard spend cap** (abort on overrun);
   - fitted with per-call timeouts and retries;
   - supplied with an `essay-only` mode and a `full` mode;
   - written only to `output/psalm_76/_S384_ab/…`;
   - protected by a thinking-capture isolation patch (S383's `debug_paths` patch);
   - checked by a **hash manifest of the repo before and after**, as in S383.
2. **Model adapters.**
   - GPT-6 via the **Responses API** with explicit `reasoning.effort` and `reasoning.summary="auto"` (captured as the thinking appendix), `max_output_tokens` ≥ 64K, and a preflight token count to stay under the **272K long-context surcharge**.
   - Opus 5.5 and Fable 5.1 with **explicit effort**.
   - Fixes for the two traps in §0.5.
3. **Pricing rows** for `gpt-6-sol`, `gpt-6-astra` and `gpt-6-luna`. Sol's $2/$10 goes in `INTRO_PRICING` expiring 2026-11-21, with the durable row marked *unverified, re-check at expiry* (the S382 lesson).
4. **Prompt caching.** Arms put the fixed inputs first and the instructions last. Anthropic's long-context guidance also recommends that order, so it is a candidate change in its own right, and one control arm isolates it. The ~200K-token dossier is then a cached prefix shared across all arms of a model (Opus 5.5 cache read = 0.05×). This cuts input cost per arm from ~$0.84 to ~$0.04 after the first write.
5. **New inputs, generated once:**
   - **(a) "First reading."** Each of Opus 5.5 (high), GPT-6 Sol (xhigh) and Fable 5.1 reads *only* the psalm (Hebrew, a literal gloss, LXX, phonetics) and writes 600–1,000 words on what the poem does and evokes as a work of art: its dramatic arc and camera, who speaks to whom and when that changes, its silences and pauses, its repetitions, the grammar that "shouldn't" be there (stray vavs, a singular verb with two subjects), and what it resonates with outside the Bible. ~$0.3–1 each.
   - **(b) The radar section** (§1.4 R3). $0.
   - **(c) Retrieved texts for the 7 bypassed defaults** (§2.2), via GPT-6 Sol + web search. ~$0.5.

### Phase 1: essay screen (~$25)
Output is the introduction essay only (~1,000–1,500 words).

| Arm | Prompt delta (from production) |
|---|---|
| **P0-prod** | Production prompt, production order. Baseline. |
| **P0** | Production prompt, inputs-first order. Isolates the order effect. |
| **P1 Poem-first** | A new mission paragraph; the essay task rewritten around *what the poem does and is meant to evoke*, with research as evidence; the first-reading doc as input; RULE 8b compressed to ~1.5K (commentators are one voice among many, no psalm-wide ranking, no count, a ceiling not a target); wit quota removed; echo budget (§3). |
| **P2 Poem-first + cross-domain** | P1 + the persona widened (history, ANE iconography, classics, world literature, music, art, psychology, philosophy) + "at least two insights a reader could not get from any Bible commentary" + radar and retrieved-defaults inputs + an explicit "linger on repetitions and poetic anomalies" instruction. |
| **P3 Lean** | A positive-only prompt of ~15–20K chars: the Hebrew/English formatting rules, audience, grounding and accuracy rules, output format, 2–3 positive exemplars, and the P2 mission. Tests whether 76K of prohibitions suppresses ambition. |

| Model × setting | Prompts |
|---|---|
| Opus 5.5, high | P0-prod, P0, P1, P2, P3 |
| GPT-6 Sol, high | P0, P1, P2, P3 |
| Opus 5 (current production writer), high | P0 (true baseline on this dossier) |
| Opus 5.5 **max** · GPT-6 Sol **xhigh** | P2 (effort sweep on the best-guess prompt) |
| Fable 5.1, high · GPT-6 Astra, high | P2 (ceiling checks: is the 5× price tier worth it?) |
| Gemini 3.1 Pro, high | P2 (a third family) |

That is **16 essays**, plus A and B as anchors. P1–P3 bundle several changes on purpose: this is a screen for large effects, and ablations come only for whatever wins.

### Phase 2: judging (~$12)
- **Mechanical metrics per essay:**
  - words;
  - distinct biblical references;
  - cross-domain references (non-biblical works, events, disciplines);
  - commentator mentions;
  - echoes used and lines quoted;
  - headings and bullet lists;
  - the scripture verifier on quoted Hebrew;
  - whether the psalm's experiential arc is named (held-out check).
- **Blind absolute scoring.** Opus 5.5, GPT-6 Sol and Gemini 3.1 Pro score every essay twice on a rubric built from your words:
  - what the poem *does* and evokes, as art;
  - fresh cross-text and cross-domain insight;
  - compelling writing ("would I keep reading");
  - grounding and accuracy;
  - wit, with failed wit penalized;
  - commentators serving the argument rather than driving it;
  - attention to repetitions and anomalies.

  Each judge must quote the best and the worst sentence, which forces grounding.
- **Pairwise tournament among the top 6.** Both position orders, all three judges, Bradley–Terry scores. Report inter-judge agreement.

### Phase 3: full guides for the finalists (~$18)
- The top 3 (prompt, model) combinations get full runs (essay + liturgy + verse commentary). The verse-commentary deltas are: the echo budget and quotation norm; commentators compressed; "linger on repetitions and anomalies"; the S382 deferral rule kept.
- **The architecture test on the winner.** S1 is one call, as today. S2 is **two calls**: the essay first, then the verse commentary with the finished essay as input. The cached dossier makes the second call cheap. S2 removes the double planning pass and gives the verse commentary a concrete essay to defer to.
- Copy editor (gpt-5.4) + DOCX in the compact print layout → `Documents/Psalm study guide/Psalm 76 (S384 – <arm>).docx`. **Nothing is overwritten.**
- Full-guide panel judging; copy-edit change counts (a proxy for error rate); echo counts per verse.

### Phase 4: replication on a second psalm (~$10)
The winner vs production on a psalm of a different genre with a finished production run (my suggestion is **Ps 73**, wisdom; Ps 75 also qualifies). Essay screen of 3 arms, then one full guide. This checks whether the win is specific to Ps 76.

### What you'll have in the morning
1. A **reading packet**: 3–4 finalist Ps 76 DOCXs + 1 for the second psalm, each with its thinking summary appended.
2. An **essay comparison page** (an artifact): all 16 essays side by side with their scores and metrics, so you can read the top ones yourself.
3. A **findings report**: what won and why, how far the judges agree with each other and with your A-over-B preference, cost per psalm for each option, and a recommended production change. Nothing in production changes until you have read it.

### Budget and time
Expected **~$70**; hard cap **$100** (the script aborts, and I stop it, above that). The runs take about 4–6 hours of wall-clock time at 3–4 concurrent calls. The machine needs to stay awake overnight; I can turn on the app's keep-awake setting if you want.

---

## 6. Decisions for you
1. **Go / no-go on the overnight run and the cap** ($100 suggested; ~$70 expected).
2. **Ceiling arms**: keep Fable 5.1 and GPT-6 Astra (+~$10), or drop them?
3. **The second psalm**: 73, 75, or another with a finished production run?
4. **Order of work**: my recommendation is the writer test tonight on the current dossier, with the radar added as an input in P2 only. The concordance renovation (§1.4) and echoes v3 (§2.3) follow in the next sessions, each with its own before/after.
