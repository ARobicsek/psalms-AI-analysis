# Psalm 76 — Micro Agent A/B: Sonnet 4.6 vs Sonnet 5 (`max` and `xhigh`)

**Session 382 (2026-09-17).** Status: **replicated the Session-362 verdict on a second psalm.
NOT adopted. `MicroAnalystV2.DEFAULT_MODEL` remains `claude-sonnet-4-6`.**

`output/` is gitignored, so this directory is the only surviving record of a **$1.5526** experiment.

## Why it was re-opened
Not because anyone doubted Session 362 — because its **pricing basis expired**. That A/B priced two
columns, Sonnet 5 intro ($2/$10 through 2026-08-31) and standard ($3/$15 from 2026-09-01), and
`SONNET5_MICRO_AB_FINDINGS.md` reasoned about both. On **2026-08-10 Anthropic made $2/$10 permanent
and cancelled the increase**, so the $3/$15 column is now dead and every figure computed from it is
unreachable. See Session 382's `cost_tracker.py` correction.

## Result

| | Sonnet 4.6 | S5 `max` | S5 `xhigh` |
|---|--:|--:|--:|
| **cost** (perm. $2/$10) | **$0.5298** | **$1.2079** `+128%` | **$0.3447** `-35%` |
| wall clock | not recorded | 26.6 min | 6.4 min |
| input tokens | 22,402 | 29,289 `+31%` | 24,331 `+9%` |
| output tokens | 30,841 | 114,932 `+273%` | 29,604 `-4%` |
| **JSON bytes** | **37,045** | **36,951** `-0%` | **27,523** `-26%` |
| lexical insights | 29 | 51 `+76%` | 43 `+48%` |
| lexical detail (chars) | 16,637 | 15,826 `-5%` | 11,277 `-32%` |
| figurative flags | 27 | 26 `-4%` | **11 `-59%`** |
| interesting questions | 10 | 16 `+60%` | 12 `+20%` |
| commentary prose (chars) | 4,733 | 3,945 `-17%` | 3,351 `-29%` |
| phrase targets 4.6 never touched | — | 14 (73% re-cut) | 8 (81% re-cut) |

## The three findings that are new

**1. `max` spends its money on thinking, not on content.** 114,932 output tokens produced a
*marginally smaller* JSON than 30,841 did (36,951 B vs 37,045 B). `budget_tokens` is removed on
Sonnet 5, so at `max` adaptive thinking is uncappable — this is the doc's warning, now measured as a
0% content return on a +273% token spend.

**2. The insight COUNT is inflated by re-cutting, not by new ground.** Classifying all 51 `max`
insights against 4.6's phrase coverage (consonantal normalisation): **73% re-cut ground 4.6 already
covered**, 81% at `xhigh`. Where 4.6 writes one dense entry on מְעוֹנָה carrying three proof texts
(Amos 3:4, Nah 2:13, Song 4:8), Sonnet 5 writes three thinner ones. Hence insights +76% while total
lexical detail is −5%. The Session-362 doc predicted the mechanism: *"Sonnet 5 follows length
instructions literally and defaults terse."*

**3. `xhigh` collapses the FIGURATIVE axis — 27 → 11 (−59%), and it is structural, not a parse
failure.** Per-verse counts are `[0,1,1,1,1,1,1,0,1,1,1,1,1]`: almost exactly **one flag per verse**,
floor-level compliance, against 4.6's 2–3. Session 362 never measured figurative at `xhigh` (its
table has `—` in that cell), so this fills a gap in the original data and is the clearest reason
`xhigh` is not a free win despite being 35% cheaper and 4× faster.

## Two checks that came back CLEAN — do not re-investigate
- **Cantillation is not a regression.** `max` emits te'amim in **84%** of `phrase` fields against
  4.6's **0%** (`xhigh` does not). Tested rather than assumed:
  `hebrew_text_processor.normalize_for_search` neutralises it at BOTH the `voweled` and
  `consonantal` levels, which are the levels the concordance searches. Cosmetic only.
- **Ps 65's headline did NOT replicate.** There, `max` doubled figurative flags (13 → 27). Here it is
  flat (27 → 26). Nothing about Ps 65's *quality* deltas should be assumed to transfer.

## What genuinely improved, so the cost is judged fairly
~8 of `max`'s 14 new phrase targets are real finds; 4 are LXX-grade, and `xhigh` keeps 6 of the 14:
- **πρός τὸν Ἀσσύριον** (v1) — LXX-only superscription plus; earliest datable link of Ps 76 to
  Sennacherib's 701 BCE campaign. 4.6 missed it entirely. *(kept at `xhigh`)*
- **ἑορτάσει** (v11) — LXX read תַּחְגֹּר as חגג (festival), not חגר (gird), defusing the paradox of
  "wrath that praises." *(LOST at `xhigh`)*
- **וּמִי־יַעֲמֹד לְפָנֶיךָ** (v8) — double-vocabulary overlap with Nah 1:6 (both מי יעמוד *and*
  חרון אף against this verse's אַפֶּךָ). *(kept)*
- **וַיְהִי** (v3) — wayyiqtol amid the hymn's timeless perfects. *(LOST at `xhigh`)*
- **כׇּל־סְבִיבָיו** (v12) — verbatim Ps 89:8, collocated with נורא exactly as here. *(kept)*

Filler in the remainder: `סֶלָה` twice as a structural marker, `{פ}` the petuchah.
**Caveat:** four of the eight real finds are LXX, and CLAUDE.md carries an open item that the LXX
budget is **not** biting (RULE 8b caps it at ≤2 verses in 5; Ps 27 measured 64%). More LXX raw
material may push that the wrong way.

## Verdict
**Keep Sonnet 4.6.** `max` costs 2.3× for a smaller artifact. `xhigh` is 35% cheaper and 4× faster
but gives up 59% of figurative flags and 32% of lexical detail. This is Session 362's conclusion —
"you cannot get cheaper AND richer at once" — now replicated on a second psalm under permanent
pricing.

**The one lever still untested** is Session 362's own "if revisited" item 1, which this run
strengthens: a **model-gated density nudge** to `DISCOVERY_PASS_PROMPT`'s WRITING-DENSITY block.
Every failure above is terseness, not incapacity — `xhigh` found 6 of the best new targets while
emitting one figurative flag per verse. If a density instruction buys 4.6-level depth at `xhigh`'s
−35%, that is the actual win. Must be model-gated so 4.6/production is byte-identical.

## Reproduction
`scripts/ab_micro_sonnet5.py <effort>` — Stages 1–2 only (Stage 3 is not a Sonnet call).
Baseline is the production run already on disk, so only the arms cost money.
`scripts/judge3.py` scores all three.

The runner does NOT modify production code. It shims `client.messages.stream` to apply the two
migration changes the Session-362 doc documents, and each arm's `shim_log.json` records that they
fired exactly once:
1. Stage 1 sends `thinking={"type":"enabled","budget_tokens":32768}` → **400 on Sonnet 5**.
   Rewritten to `{"type":"adaptive"}` with `max_tokens` raised to 128000 (thinking is uncappable and
   shares the budget with the JSON).
2. Stage 2 sends **no** `thinking`. On 4.6 that means OFF; on Sonnet 5 omitting it defaults to
   **adaptive ON**. Set to `{"type":"disabled"}` to match 4.6.
The `xhigh` log also shows `effort_was: max` → `effort_now: xhigh`, proving the arms differ only in
effort.

**Gotcha, already in the Session-362 doc and hit again anyway:** `MicroAnalystV2`'s default
`db_path` is `data/tanakh.db`; the populated 87 MB DB is at `database/tanakh.db`. Pass it explicitly
or you get "Psalm N not found" — it fails before any API call, so it costs $0.
