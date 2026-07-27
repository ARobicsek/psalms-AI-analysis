# Copy Editor — Terra overreach findings (Session 368)

**Status: SETTLED. Do not re-run this A/B.** The copy editor is pinned to
`gpt-5.4`; the writer-A/B harness takes `--copy-editor-model`. Read this before
touching `COPY_EDITOR_SYSTEM_PROMPT` or moving the copy editor back to
`gpt-5.6-terra`.

## The question

Session 367 swapped the GPT default `gpt-5.4` → `gpt-5.6-terra` (cost-neutral,
one generation newer). Finishing the Ps 70 writer A/B, the Terra copy editor
overwrote a **correct** statement about George Herbert's *Denial* with a false
one and deleted an Akhmatova echo. Was Terra overstepping, or was this a
long-standing prompt problem the swap merely exposed?

## Method

Four copy-editor runs over **one identical input** —
`output/psalm_70/_writer_ab/claude-opus-5/psalm_070_print_ready.md` (6,875
words). Same prompt except where noted. Total spend $1.23.

## Results

| Run | changes | cat-7 | Herbert | fortress figure | closing figure | Ps 40:17 waw |
|---|---|---|---|---|---|---|
| `gpt-5.4` | 16 | 6 | untouched | kept | kept | kept |
| `gpt-5.6-terra` (production) | 25 | — | false rewrite | flattened | flattened | kept |
| `gpt-5.6-terra` (re-run) | 28 | 8 | minor edit | **deleted** | flattened | kept |
| `gpt-5.6-terra` + burden-of-proof rules | 28 | **11** | false rewrite | kept | flattened | **falsely deleted** |

**Terra makes ~1.7× the edits of gpt-5.4 on identical input**, and the extra
volume lands disproportionately on two classes:

1. **Literalizing figurative prose.** The re-run replaced *"a man who needs a
   fortress can wait inside it; a man who needs extraction cannot wait at all"*
   — one of the two first-rate arguments that justified recommending Opus 5 —
   with *"suits a psalm whose repeated request is haste."* Every Terra run
   flattened *"stop asking mid-sentence"* → *"leave the request unresolved,"*
   reasoning that the psalm "ends with a syntactically complete prohibition."
   That is reading a rhetorical figure as a factual claim and correcting it.
   **gpt-5.4 left both intact.**
2. **Asserting about outside works with no source in hand.** Terra touched the
   Herbert paragraph in **3 of 3** runs; gpt-5.4 in 0 of 1. It also re-dated
   Cassian and recast the Monteverdi/Britten comparison.

## Two things that are NOT Terra's fault

- **Echo deletion is pre-existing.** Under `gpt-5.4`, the copy editor removed
  the Lauryn Hill comparison and reframed Vallejo (Ps 62), and removed both
  Lorca and Walcott (Ps 67). The Ps 70 Akhmatova deletion is the same
  long-standing behaviour, sanctioned by category 6.
- **The prompt has no scope rule.** Category 7 is scoped to *biblical* texts,
  but nothing forbids correcting claims about Herbert or Cassian, while the
  CRITICAL READING STANCE and the hedge-hardening pass actively invite it.
  Terra is simply better at accepting an invitation gpt-5.4 declined.

## The fix that FAILED — do not retry it

A three-rule "BURDEN OF PROOF ON THE EDITOR" block was added and tested:
(a) an outside-world **specificity test** — correct a claim only if you can
state the right fact as specifically as the guide states the wrong one;
(b) **never substitute a vaguer contrary claim**; (c) **figures are not claims**.

Rule (c) worked (the fortress line survived). **Rules (a) and (b) backfired:**

- **The specificity test is gameable by confabulation.** Terra satisfied it by
  inventing *more* specific detail — replacing *chime* answering *rhyme* with
  "piles up *-ing* rhymes before ending on *chime*." There are no *-ing* rhymes
  in that stanza and it ends on *ryme*.
- **The framing raised category-7 aggression** (6 → 8 → 11 across runs).
  *"If you are sure enough to overwrite, you are sure enough to be specific"*
  reads as a licence to assert confidently.
- **It caused the worst error observed.** That run deleted Opus 5's correct
  claim that Ps 40:17 lacks the connecting waw, asserting "it has וְיֹאמְרוּ."
  Per `database/tanakh.db`: Ps 40:17 = `...כׇּֽל־מְבַ֫קְשֶׁ֥יךָ יֹאמְר֣וּ תָ֭מִיד` (no waw);
  Ps 70:5 = `...כׇּֽל־מְבַ֫קְשֶׁ֥יךָ וְיֹאמְר֣וּ תָ֭מִיד`. Opus 5 was right. That was one of
  the four doublet variants justifying its adoption, destroyed by a fabricated
  Hebrew reading — inside category 7's real scope, where ground truth is one
  SQL query away. **All three other runs left it alone.**

Rules (a) and (b) were reverted. Rule (c) was kept as the standalone
`FIGURES ARE NOT CLAIMS` block.

## What shipped

1. **`FIGURES ARE NOT CLAIMS`** block in `COPY_EDITOR_SYSTEM_PROMPT`
   (`src/agents/copy_editor.py`), placed after the hedge-hardening check.
2. **Copy editor pinned to `gpt-5.4`** — `CopyEditor.DEFAULT_MODEL`. It was the
   only run that damaged none of the four probe cases while still catching real
   errors gpt-5.4-only found (Cranmer's BCP versicle is plural *"make speed to
   save us,"* not *"save me"*). Costs ~$0.4 more per psalm than Terra
   ($0.52 vs $0.35 on Ps 70) — negligible against a ~$15 run.
3. **`scripts/ab_finish_arms.py --copy-editor-model`** so A/B arms are not
   silently pinned to `DEFAULT_MODEL`.

Note this pin is **copy-editor-only**. Terra remains correct and in production
for insight extraction, question curation, figurative curation and literary
echoes passes 3–4, where Session 367 measured it clean.

## Known-good probe cases

Any future change to this agent should be checked against the saved Ps 70
Opus-5 input on these four, all of which the SHIPPED text has right:

1. Herbert's *Denial* — the final stanza **does** restore the rhyme
   (*chime* / *ryme*); five stanzas leave the fifth line unpaired.
2. `a man who needs a fortress can wait inside it; a man who needs extraction
   cannot wait at all` — a figure; must survive verbatim.
3. `hold the form and stop asking mid-sentence` — a figure; must survive.
4. Ps 40:17 lacks the waw before יֹאמְרוּ; Ps 70:5 has it.

```bash
python scripts/run_copy_editor.py 70 \
  --input-file output/psalm_70/_writer_ab/claude-opus-5/psalm_070_print_ready.md \
  --output-dir <scratch>
```

## Open — the real structural fix

The copy editor's own factual assertions are checked by nothing. The scripture
citation verifier runs **before** it (STEP 5a½) and feeds it as
`supplementary_prompt`; it does not run after. A post-copy-edit verification
pass (~$0.15/run) would have caught the fabricated Ps 40:17 waw deterministically,
and is the durable answer for the biblical class. Deferred pending Ps 71
evidence on how often the class actually occurs at full psalm length.

For non-biblical claims (Herbert, Cassian, Monteverdi) the pipeline has **no**
ground truth, while the writer works from a 4-pass web-verified literary-echoes
dossier. There the writer is the better-informed party — an argument for
narrowing the editor's licence on grounds of authority, not timidity. Note that
a materials-only rule would have been **actively harmful** on Herbert:
`literary_echoes/pass_4_final.txt` supplies only stanzas 1–2 and says Herbert
"lets perceived delay shatter meter and rhyme," which would have *licensed*
Terra's false correction. The *chime*/*ryme* observation was Opus 5's own
knowledge, and correct.
