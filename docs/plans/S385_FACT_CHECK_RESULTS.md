# Session 385 — Evidence-based fact check before the copy editor: BUILT, NOT YET RUN

**Status:** the code is complete, tested at $0 (`python -m pytest -q`: 199 passed, 14 skipped) and pushed.
**No test run has been completed.** The parent session stopped all paid runs in the cloud at the author's
request; the author runs them locally, where `.env` holds the keys and `database/tanakh.db` exists. Nothing in
production changes until `--fact-check` is passed: the flag defaults to OFF.

## Why

The forest writer prompt asks Opus 5.5 to use its own knowledge (Herodotus, Byron, Sennacherib's prism), so the
guide now carries more claims that no pipeline source vouches for. The copy editor (gpt-5.4) corrects facts
from memory, and that is where the pipeline's worst copy-edit errors came from:

- Session 368 (`COPY_EDITOR_TERRA_FINDINGS.md`): Terra invented a Hebrew reading (Ps 40:17's waw) and
  "corrected" a true claim about Herbert. A stricter rule ("burden of proof") made it worse. That doc's
  verdict: ground truth, not a sterner rule.
- Session 383: gpt-5.4 turned the writer's correct *"the only other occurrence of the form רִשְׁפֵי is Song
  8:6"* into a false *"the only other plural use of the noun is Song 8:6"* (Ps 78:48 has לָרְשָׁפִים).

The design splits the two jobs. A fact-check pass verifies claims against evidence. The copy editor then
corrects facts ONLY where that report says `contradicted`, and it gets this licence as supplementary
context, never as a new rule in its system prompt.

## What was built, file by file

| File | What |
|---|---|
| `src/agents/fact_checker.py` | `FactChecker`: **gpt-6-sol** on the OpenAI Responses API, effort `high`, a different model family from the writer. Tools: OpenAI's built-in **web search**, plus three function tools: `get_verse(ref)`, `get_commentary(commentator, ref)` and `search_tanakh(hebrew)`. The verse and search tools read `tanakh.db` read-only when it holds verses, else Sefaria. `get_commentary` reads the research bundle's `### 76:11 — Rashi` entry first, else Sefaria. The guide is split into section-aligned chunks (`split_guide_for_checking`, ~13K chars, never mid-section). Each chunk call carries the whole bundle first, then the instructions, then the excerpt, so every call after the first reads the ~130K-token bundle at the cache rate. The first chunk runs alone to write the cache; the rest run 3 at a time. Output is strict JSON, one record per claim: location, the exact sentence, claim, claim type, verdict (`supported` / `contradicted` / `unverifiable`), evidence (quoted source text + ref/URL), explanation, and `suggested_fix` for a contradiction. **A `contradicted` verdict with no quoted evidence is downgraded to `unverifiable`** in `validate_records`, so it can never license an edit. Also: `format_report_markdown`, `format_copy_editor_prompt` (the copy editor's block), `load_copy_editor_prompt` (re-validates a saved report), `combine_supplementary`, `usable_db`. The module loads the project's `.env`. |
| `scripts/run_fact_checker.py` | Standalone CLI. Default input: the psalm's `print_ready.md` and `research_trimmed.md`/`research_v2.md`. Writes `psalm_NNN_fact_check.json`, `.md`, `_copy_editor_prompt.txt` and `_thinking.txt`. `--dry-run` shows the chunks at $0. |
| `src/agents/copy_editor.py` | (1) **`COPY_EDITOR_SYSTEM_PROMPT` is byte-identical** to before, and a test pins its sha256. (2) `build_user_message()` is the old user turn factored out, and returns exactly the pre-S385 message when no report is given (tested). (3) **`_reassemble` split fix**: the intro/verses split now anchors on a verse header alone on its line (`STANDALONE_VERSE_HEADER`, the same regex as the pipeline's recovery path). A liturgical `**Verse 2.** In Nusach Sefard…` line no longer moves the key-verses block into the verses (the S383 defect). The loose pattern is kept only as a fallback. (4) A Responses-API path for `gpt-6-*`, used only when that model is requested: on chat.completions it would have run with `max_tokens=16000` and no reasoning. `DEFAULT_MODEL` is still `gpt-5.4`. (5) `_strip_echoed_supplementary` also strips an echoed fact-check block. |
| `scripts/run_copy_editor.py` | `--fact-check-report <psalm_NNN_fact_check.json>` sends the report as supplementary context. |
| `scripts/run_enhanced_pipeline.py` | `--fact-check` (default OFF). **STEP 5a¾** runs the fact check on `print_ready.md` just before the copy editor, and its block goes in with the citation report. **STEP 5b½**, with the flag, where `tanakh.db` holds verses: re-runs the $0 `verify_citations` on the copy-edited text and writes `psalm_NNN_post_copy_edit_citations.md`, listing only mismatches the copy editor introduced (`new_citation_issues`). This is the "Open" item in the Terra doc. Without the flag the copy editor receives exactly the citation report, as before (tested). |
| `src/utils/scripture_verifier.py` | `new_citation_issues(before, after)`. |
| `pytest.ini` | `testpaths = tests`. A bare `python -m pytest -q` used to collect `archive/` (32 collection errors here). It also imported the root-level `test_api.py`, which makes a **live** gpt-5.5-pro call and rewrites `test_api_out.txt`, and archive scripts left an **empty `database/tanakh.db`** behind. |
| `tests/test_fact_checker.py` | 24 tests: the prompt hash, the unchanged user message, the identical system message with and without a report (captured from a fake client), the echo strip, the split fix (three cases), evidence-free `contradicted` → `unverifiable`, JSON parsing, prompt and report formatting, chunking, ref parsing, bundle lookup, the empty-db guard, the citation diff and the pipeline default. |
| `archive/psalm_76_S385_fact_check/run_s385_fact_check.py` | The Ps 76 test driver (below). Every paid step is appended to `ledger.json` and refused once the ledger would pass **$12**. |

### How the copy editor is told to use the report

The block (`format_copy_editor_prompt`) is appended to the user turn after the citation report. Its three rules:

1. Correct a factual claim ONLY where an item is marked CONTRADICTED, only as far as its quoted evidence
   supports, with the smallest change that makes the sentence true, keeping the author's wording, figures and
   argument. Tag the change-log entry `[FACT-CHECK]`.
2. Do NOT correct any other factual claim from memory. List doubts under `### UNVERIFIED` at the end of
   `## Changes`; these are notes for the author, not edits.
3. Leave SUPPORTED and UNVERIFIABLE claims alone as matters of fact.

After the rules comes each contradicted item with its sentence, finding, quoted evidence and suggested fix,
then one-line lists of the supported and unverifiable claims.

## What happened in the cloud (spend $1.18, all logged in `ledger.json`)

- **Smoke test, $0.2282**, on a two-sentence excerpt with no bundle: 8 web searches, 10 lookups, 64 s.
  - It marked *"The only other plural use of the noun רֶשֶׁף is Song 8:6"* **contradicted**, quoting Ps 78:48
    `וּמִקְנֵיהֶם לָרְשָׁפִים` and Song 8:6 `רְשָׁפֶיהָ רִשְׁפֵּי אֵשׁ` with Sefaria URLs. Its suggested fix
    names both verses.
  - It marked Herodotus 2.141's mice and bowstrings **supported**, quoting Rawlinson's translation with a URL
    and noting "gnawed" as a fair paraphrase of "devoured".
  - This shows the whole mechanism works end to end: web search, function tools, strict JSON, evidence and fix.
- **Probe A, attempt 1 (~$0.45, estimated)**, stopped after 2 rounds. An empty `database/tanakh.db`, left by my
  bare `pytest` run, would have answered every count with zero. Fixed: `usable_db` opens the db read-only and
  requires rows (tested). Also fixed by `pytest.ini`.
- **Probe A, attempt 2 (~$0.50, estimated)**, stopped during chunk 1 on the parent session's instruction.
- The two aborted runs returned no usage, so their costs are estimates from the token volumes, rounded up.

**Nothing below has been run.** It is the local procedure.

## Local procedure (VS Code, repo root)

Keys come from `.env`; every script loads it. `database/tanakh.db` is used automatically when present.

| # | Command | What it does | Expected cost |
|---|---|---|---|
| 0 | `python -m pytest -q` | the suite | $0 |
| 1 | `python scripts/s385_two_call_writer.py` | the parent's two-call writer; produces `archive/psalm_76_S385_two_call/F/` (`full_writer_response.md`, `psalm_076_edited_intro.md`, `psalm_076_edited_verses.md`) | ≈ $3.1 (its own ledger, cap $8) |
| 2 | `python archive/psalm_76_S385_fact_check/run_s385_fact_check.py probe-a` | Probe A: fact check of `archive/psalm_76_S383_opus55_ab/B_opus55/psalm_076_copy_edited.md` against the S384 inputs block (5 chunks) | ≈ $2–3.5 |
| 3 | `… run_s385_fact_check.py main --source F` | builds `main_F/psalm_076_print_ready.md` like STEP 5 (CommentaryFormatter; psalm text from the inputs block), fact-checks it, then two gpt-5.4 copy edits: **with the report** and **without it (control)** | fact check ≈ $2–3.5; each copy edit ≈ $0.65–0.8 |
| 4 | `… run_s385_fact_check.py sol --source F` | optional: gpt-6-sol copy edit with the report | ≈ $0.3–0.5 (promo $2/$10 through 2026-11-21) |
| 5 | `… run_s385_fact_check.py compare --source F` | $0: edit counts and probe survival per arm → `main_F/comparison.json` | $0 |
| 6 | `… run_s385_fact_check.py docx --source F` | $0: the compact reading DOCX of the fact-checked, copy-edited F guide, with the fact-check report and the change log as an appendix | $0 |
| — | `… run_s385_fact_check.py spent` | ledger total | $0 |

**Expected total for steps 2–4 ≈ $6–8.** Together with the $1.18 already in the ledger, that fits the $12 cap.
The writer's $3.1 is on its own ledger. If F never materializes, `main --source B383` runs the same test on the
S383 all-Opus-5.5 guide (`master_writer_v4_response_psalm_76.txt`).

**Web-search pricing** (OpenAI pricing page, read 2026-09-29): *"Web search (all models) | $10.00 / 1k calls +
Search content tokens billed at model rates."* The content tokens arrive inside `input_tokens` and are priced by
`price_tokens`. The $0.01-per-call fee is added separately (`WEB_SEARCH_USD_PER_CALL`) and reported as
`search_cost_usd`. **In the pipeline, CostTracker does not include the per-call fee**: it tracks tokens only,
and STEP 5a¾ logs the fee beside it. In the smoke test, search content was most of the input: 60K input tokens
for 8 searches.

## What counts as PASS

**Probe A** (`probe_A/psalm_076_fact_check.json`):
- PASS: a record whose sentence is *"The only other plural use of the noun is Song 8:6, and the very next verse
  says …"* (line 95 of the S383 copy-edited guide) has verdict **`contradicted`**, and its evidence quotes Ps
  78:48 with `לָרְשָׁפִים`.
- Also check the neighbours stay clean. Line 135's *"in רִשְׁפֵּי אֵשׁ… (Song 8:6) it has one [a dagesh]"* and
  its *Minchat Shai* point are true and must NOT be `contradicted`.
- FAIL: the line is supported or unverifiable, or it is contradicted with evidence that does not name Ps 78:48.

**Rashi on 76:11** (main F):
- Essay F says *"Rashi offers two readings. In one, the tyrant's rage… turns into an admission of God's
  power… In the other, drawing on a Mishnaic sense of the root, תַּחְגֹּר means 'You restrain'…"*.
- Rashi actually gives ONE reading in two steps. Human fury ends in praise (Nebuchadnezzar, Dan 3:28), *and
  thereby* (וְעַל יְדֵי כֵן) the remaining fury is restrained: תחגר in the Mishnah's sense of a nick that
  "catches" the nail. He then offers an alternative: literal girding (*"It is also possible to interpret this
  according to its usual meaning of… girding… It is fitting for You to gird Yourself with wrath"*). The
  bundle's `### 76:11 — Rashi` entry has both texts.
- PASS, checker: a record for that sentence is **`contradicted`**, quoting the "And thereby" link and the
  girding alternative.
- PASS, copy edit with the report: `Rashi offers two readings` is gone, the passage presents one reading
  (praise, and thereby restraint) with girding as Rashi's alternative, and the change is tagged
  `[FACT-CHECK]`. `compare` reports `rashi_two_readings_still_there: false`.
- Check the control too. If it also fixes Rashi unaided, the report is not what made the difference.

**Claims from memory that must survive** (`compare` → `survivors`, all `true` in every arm):
- Byron, *The Destruction of Sennacherib*: the four quoted lines and *"the breath of his pride."*
- Herodotus 2.141: the mice, and the statue's inscription `ἐς ἐμέ τις ὁρέων εὐσεβὴς ἔστω`.
- Sennacherib's prism: *"like a bird in a cage"*, *"thirty talents of gold, eight hundred of silver"*, *"his own
  daughters"*.
- The checker should mark each **`supported`** with a source URL (`compare` → `probe_records`).
- A `contradicted` verdict on any of them is a checker failure. Read its evidence before trusting it. Two real
  wrinkles to allow for: the prism figure is 800 talents of silver in the Chicago/Taylor prism text, while
  2 Kgs 18:14 has 300; and Herodotus calls him "king of the Arabians and Assyrians".

## How to compare factual edits with and without the report

`compare` prints and saves, per arm:
- total changes, category-7 changes, and a count for every category;
- the number of `[FACT-CHECK]`-tagged entries and `### UNVERIFIED` notes;
- probe survival, and whether the Rashi error is still there;
- the full text of every category-7 entry (`category_7_entries`).

The question is **whether the report made the editor more or less aggressive**:
- Fewer category-7 entries WITHOUT a `[FACT-CHECK]` tag in the with-report arm than in the control = more
  restraint.
- Doubts moved to UNVERIFIED instead of edited = the rule working.
- More untagged category-7 edits = the report acting as a licence (the Terra failure shape). If so, drop it and
  keep the post-copy-edit check.

Then read `psalm_076_copy_edit_diff.md` in both arms for **every figure of speech an edit touched**
(`FIGURES ARE NOT CLAIMS`): list each one and say whether it was flattened. Include the **gpt-6-sol arm** for
the author's model question (edit counts and notable differences). This does not change the default model.

## Where things land

```
archive/psalm_76_S385_fact_check/
  ledger.json                                  every paid step (cap $12)
  probe_A/psalm_076_fact_check.{json,md}       + _copy_editor_prompt.txt, _thinking.txt
  main_F/psalm_076_print_ready.md              the copy editor's input
  main_F/psalm_076_fact_check.{json,md}        + _copy_editor_prompt.txt, _thinking.txt
  main_F/copy_edit_with_report/                psalm_076_copy_edited.md, _copy_edit_changes.md, _copy_edit_diff.md, supplementary_prompt.txt
  main_F/copy_edit_control/                    the same, without the report
  main_F/copy_edit_sol_with_report/            optional gpt-6-sol arm
  main_F/comparison.json                       from `compare`
  Psalm 76 - F fact-checked and copy-edited (S385).docx
```

The copy editor also writes its usual side files, `output/psalm_76/psalm_076_copy_editor_thinking.txt` and
`output/debug/copy_editor_response_psalm_76.txt`. Each arm overwrites them. They are not the record; the arm
folders are.

## Known limits and open questions

- **Recommendation, pending the local run:** adopt `--fact-check` if Probe A and Rashi pass, the three
  memory claims survive, and the with-report arm has no more untagged category-7 edits than the control.
  Run it on one more psalm before making it the default.
- `search_tanakh` falls back to Sefaria's search, which is prefix/suffix-tolerant (naive lemmatizer): רשף
  returns Deut 32:24, Hab 3:5, Ps 78:48, Job 5:7 and 1 Chr 7:25 (the personal name), but misses Ps 76:4 and
  Song 8:6 (surface רשפי finds those two). The tool's own output tells the model to confirm forms with
  `get_verse`. Locally, `tanakh.db` answers with an exact consonantal substring instead.
- `get_commentary` resolves common commentators by name. Rarer ones fall to Sefaria's `"<Name> on Psalms N:V"`
  spelling and may miss.
- The checker's own false `contradicted` verdicts are the main risk; the evidence requirement is the guard. When
  reading results, count false contradictions separately. The Terra doc says a wrong "correction" from a
  confident source is worse than a missed error.
- The per-search fee is outside CostTracker (see above).
- Cost on a full guide is not yet measured. The $2–3.5 estimate is extrapolated from the smoke test and the
  aborted chunk.
