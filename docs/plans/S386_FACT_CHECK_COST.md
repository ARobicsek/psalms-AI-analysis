# Session 386 — Cutting the fact checker from $4.87 to $1.83 without losing recall

**Status:** shipped in `src/agents/fact_checker.py` (defaults = the recommended **v5** configuration).
`run_enhanced_pipeline.py --fact-check` is still **default OFF**. The author accepted **~$1.80 per psalm** for the
fact check (2026-09-29). Every run below is on the same input, **Probe A**: the S383 all-Opus-5.5 Ps 76 guide
(`archive/psalm_76_S383_opus55_ab/B_opus55/psalm_076_copy_edited.md`), with the S384 inputs block as the bundle.
All records are in `archive/psalm_76_S386_fact_check_cost/`.

## The result

| Version | What changed | Cost | Contradicted | Real errors caught (my read) |
|---|---|---|---|---|
| S385 (Probe A) | gpt-6-sol, web search on every claim, 130K-token bundle in context on every round | $4.87 | 25 | ~11 |
| luna_baseline | the same pass on gpt-6-luna | $0.59 | 17 | ~5, plus 4 divine-name false alarms |
| staged_v1 | luna local → sol web → sol review | $1.39 | 8 | ~6 |
| sol_v2 | sol local, bundle via tools only, 70 claims to sol web | $5.11 | 25 | ~15 |
| sol_v3 | + shared evidence block (commentators + cited verses) up front | $5.86 | 20 | ~15 |
| v4 | + per-chunk evidence, triage, compact supported, **luna gathers / page check / sol judges** | $3.16 | 18 | ~16 |
| **v5 (shipped)** | + strict triage (1 claim in 10), ≤ 1 search per claim, smaller lookups | **$1.83** | 22 | **~17** |
| v6 | v5 at effort `medium` | $1.42 | 12 | ~8, plus one false alarm |

v5 split: **local (gpt-6-sol) $1.56; gather (gpt-6-luna) $0.15, 13 searches; judge (gpt-6-sol) $0.12.**

**Recall varies run to run.** v5 marked "King Hezekiah asks…" supported although three other Sol runs caught it (it is the
rabbinic Ḥizkiya, Shabbat 88a); v5 found three errors no other run did (Meiri's entry says nothing about Asaph's date;
Resh Lakish does not name the sixth of Sivan; the seventh day of creation also has the article). Judge one run, not the
best-of.

## Session 397: $2.76 → $1.22 on Ps 79, same model, same effort

By Ps 79 (13 verses, the first guide with the S395 liturgy section) the check had grown to **$2.76**, $2.60 of it stage 1.
Its anatomy: cache **writes** 511K tokens × $2.50 = $1.28, cached reads 3.2M × $0.20 = $0.64, output + reasoning $0.68.
The cache was working (writes ≈ the unique context; nothing missed); **79% of the written tokens were lookup results**,
and `search_liturgy` + `get_text` were 87% of those (liturgy searches up to 11K chars each, half of it `every_ref`).
Rounds were already batched (~8 lookups a round, ~10 rounds a chunk). Two changes, both shipped:

1. **OpenAI Flex** (`DEFAULT_SERVICE_TIER = "flex"`): the same model at Batch prices, **half** of standard on every token
   class (gpt-6-sol $1 / $0.10 / $1.25 write / $5), slower and occasionally `429 Resource Unavailable` (not billed;
   `_create` waits, and on the third try asks for the standard tier). Each response is billed by the tier the API
   REPORTS (`billing_model` → the `gpt-6-sol@flex` / `gpt-6-luna@flex` rows in `cost_tracker.PRICING`), so a fallback
   costs standard and the cost file shows which. `run_fact_checker.py --service-tier default` for the old tier.
2. **Compacted lookups, nothing a check needs removed**: liturgy passages and `get_text` Hebrew go out **unpointed**
   (cut first, so the same span; a verse's pointing stays in `get_verse` and the evidence block); `every_ref` grouped
   by book (`group_refs`; `get_text` takes the shortened 'book, place'); a passage reprinted word for word **between
   the same neighbouring prayers** is shown once with `also_in` (neighbours are in the key: order is what liturgical
   claims get wrong). Replayed at $0: Ps 79's lookups 406K → 225K tokens, Ps 78's 390K → 265K.

Validated on Ps 79's own pre-copy-edit guide (`archive/psalm_79_S397_fact_check_cost/README.md`): **$1.22**, 25
contradicted vs 29; every disagreement read: ~11 real catches each side the other missed, one false alarm each side —
the S386 run-to-run spread, not a loss. Flex did not slow it down (stage-1 chunks 79–168 s vs 95–156 s).

Not done: compacting the supported records (≈ $0.08 at flex prices, a schema change); the per-verse liturgy catalogue as
a lookup (would replace many `search_liturgy` calls, but changes what the checker sees — needs its own A/B). With the
check at half price, **two independent passes merged** (~$2.4) is now affordable if recall ever matters more than cost.

## The design (v5)

1. **Stage 1, local — gpt-6-sol, effort `high`, no web.** Each chunk (≈13K chars of the guide, section-aligned) starts with
   **its own evidence**: the commentators' full entries on the verses it covers (all entries for the introduction) and the
   Masoretic text + translation of every verse it cites (`shared_evidence`, `chunk_verses`, `cited_refs`). Tools:
   `get_verse`, `get_commentary`, `search_tanakh`, `get_text` (any Sefaria ref), `search_research` (keyword search of the
   bundle). The instructions:
   - skip the **wording of biblical quotations** — the $0 `verify_citations` does that, divine-name aware;
   - **divine names** (ה׳, אֱלֹקִים, קֵל, צְבָקוֹת, שַׁקַּי, אֱלוֹקַּ) are never an error (`DIVINE_NAMES_NOTE`);
   - the bundle's AI-written summaries of liturgy and literature are **not ground truth**;
   - **materiality**: contradicted = a reader would believe something false; a changed *shape* of a commentator's
     argument counts, a paraphrase does not (`MATERIALITY_NOTE`);
   - **triage**: `needs_web` only when exact wording/attribution/order/date/custom is the point AND there is a specific
     doubt (≈ 1 in 10); a standard fact → supported "known"; anything the Bible, a commentator or Sefaria can settle is
     never `needs_web`;
   - **supported records are short** (first six words of the sentence, claim ≤ 8 words, no evidence).
2. **Stage 2, web — gather, check, judge.**
   - **gpt-6-luna gathers** passages with OpenAI web search (`search_context_size: low`, ≤ 1 search per claim), no verdicts.
   - **Every passage is checked against its live page at $0** (`verify_sources` / `quote_on_page`: normalised substring or
     ≥ 60% of 5-word shingles; PDFs via `pypdf`).
   - **gpt-6-sol judges** from the checked passages, no web. A passage *found on its page* (or a Sefaria lookup) may
     support or contradict; an *unreadable page* may only support; a passage *not found* is not evidence.
3. **Stage 3, review — off by default.** It re-judges stage-1 contradictions and exists for a weaker stage-1 model
   (`--model gpt-6-luna --review-model gpt-6-sol`). With Sol in stage 1 it is redundant.

The copy editor's side is unchanged from S385: it gets the report through `supplementary_prompt`, corrects facts only where
the report says contradicted, and its system prompt is byte-identical.

## Where the money went, and what did not work

- **S385's $4.87**: 51% uncached input, 13% cached replay, 20% output, 16% search fees. The bundle (≈130K tokens) was
  re-sent on every tool round of every chunk.
- **Removing the bundle alone made it worse** (v2, $5.11): Sol made **560 lookups**, each output paid for once in full and
  then on every later round. Handing the evidence over up front (v3) cut uncached input 1.23M → 0.41M, but a 30K-token
  block replayed over ~100 rounds cost as much. Per-chunk evidence fixed that.
- **The web stage was the other half.** OpenAI bills the search results as input (~7.9K tokens per search, even at `low`
  context): Sol searching 71 claims cost **$3.79**. On Luna the same tokens are nearly free, leaving the **$0.01 fee per
  search** as the floor — hence triage (71 → 24 claims) and ≤ 1 search per claim.
- **gpt-6-luna as the main checker** ($0.59) catches counts and letter-level errors but misses the commentator- and
  rabbinic-shape errors the author cares about, trusts the research bundle's summaries, and waved "loose" paraphrases
  through.
- **Gemini is not usable here, for a reason worth remembering**: Google Search grounding does not bill retrieved content
  as input and gives 5,000 free searches a month, **but the models mostly did not search**. Gemini 3.1 Pro asked for
  verdicts ran 5 searches for 71 claims and answered the rest from memory (and reversed Sol's correct Kol Nidrei catch);
  Gemini 3.8 Flash, 3.5 Flash and 3.1 Pro at low thinking returned "verbatim" passages and URLs with **no grounding
  metadata at all** — from memory; only 33 of 71 claims got a passage that was really on its page; and its copyright
  filter (`RECITATION`) blocked whole batches. `gemini-3-flash-preview` did search but its pricing page entry is
  ambiguous. The Gemini path is still in the code (`web_model="gemini-…"`) behind the same page check.
- **Effort `medium`** (v6) saves $0.40 and loses about half the catches.

## Known limits

- ~~Web-search fees are outside CostTracker~~ — fixed in Session 387 (`CostTracker.add_charge`); they are in the run total.
- **GPT-6 Sol's price is settled (Session 388): $2 / $0.20 cached / $10, standard, no expiry.** The "promotional pricing
  through November 21, 2026" note on OpenAI's page belongs to GPT-5.6 Sol ($4/$20); S384 had pinned it on gpt-6-sol, so the
  "≈ $3.60 after that date" once written here was wrong. Also from S388: GPT-5.6+ models bill a **cache write at 1.25×
  input** (`input_tokens_details.cache_write_tokens`), which the tracker now prices; on Ps 77 that was ≈ $0.12 of the fact
  check the old accounting missed. Ps 77 anatomy (S388): of stage 1's $1.42, uncached input $0.49, visible output $0.40,
  cached replay $0.28, reasoning $0.25; cache hits were already ~85% of input and the $0 lookups returned only ~86K tokens.
- **Pages that block scripts or need JavaScript** come back unreadable (33 of 111 sources in v4), so they can support a
  claim but never contradict one. That is deliberate.
- Verse-number confusion: v6 flagged "v. 7" against the English numbering. Session 388: every chunk now opens with the
  psalm's own text under a heading that says the guide numbers verses as the Hebrew does.
- Session 388 added $0 lookups: `search_liturgy` (data/liturgy.db: siddurim, machzorim, selichot, the Haggadah, with each
  prayer's neighbours), `get_lxx` (Bolls.life: Brenton's English; the Greek there is LEMMAS only), helpful `get_text`
  failures (Sefaria's own title suggestions), and "no entry" for a commentator who skips a verse. On Ps 77, 29 of 315
  lookups had failed (13 guessed liturgy refs, 5 Septuagint, 8 works not on Sefaria, 3 absent commentary entries), and
  four liturgical claims passed as supported with no stated basis. Not yet measured in a paid run.
- **Not yet tested on essay F** (the Rashi 76:11 probe; Byron, Herodotus 2.141 and Sennacherib's prism must survive), and
  the copy edit with vs without the report has not been compared. `archive/psalm_76_S385_fact_check/run_s385_fact_check.py
  main --source F` does both; it now runs v5 by default.
