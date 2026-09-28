# Next session (386): run the two-call forest writer, then decide on fact-checking

## Where Session 385 left things
- **The author's blind reading of the S384 essay trials is recorded** in
  `archive/psalm_76_S384_essay_trials/AUTHOR_READING_S385.md`: F and C best (both forest essays by Opus 5.5), D top of
  the middle group; all Sol essays in the middle or below; both production essays in the middle (K) or weakest (B).
  F mis-explains Rashi on 76:11.
- **The author chose two calls** (essay, then everything else) and asked for the verse instructions to be drafted and
  run. They are drafted and the runner is built and tested at $0, but **nothing ran: this container had no
  `ANTHROPIC_API_KEY`**. Read `docs/plans/S385_two_call_writer_and_fact_check.md` first.

## Do this first
1. Confirm `ANTHROPIC_API_KEY` is set (`python -c "import os; print(bool(os.environ.get('ANTHROPIC_API_KEY')))"`).
   If not, ask the author to add it in the environment settings. Never ask for the key in chat.
2. `pip install anthropic python-docx python-dotenv` if missing.
3. `python scripts/s385_two_call_writer.py --dry-run`, then `python scripts/s385_two_call_writer.py`
   (≈ $3.1; cap $8).
4. Confirm call 2 read the cache: `cache_read` ≈ 185K in `archive/psalm_76_S385_two_call/ledger.json`.
5. Send the author both DOCXs (`archive/psalm_76_S385_two_call/{new,F}/*.docx`). Neither is copy edited. Report the
   metrics against K descriptively. Commit the outputs.

## Then, the author chooses
- **Fact-check pass** (proposed in the S385 plan doc §"The copy editor…", not built). It verifies claims against the
  bundle, our own lookups and web search, and returns verdicts with evidence. The copy editor then corrects facts only
  from that evidence. Probe cases are listed there, F's Rashi first.
- **Copy editor on GPT-6 Sol**: roughly cost-neutral (±$0.2/psalm), but do not switch without the Terra probe cases
  (`COPY_EDITOR_TERRA_FINDINGS.md`). Their saved Ps 70 input is on the author's machine.
- Take the two-call writer into `MasterEditor` for a fresh psalm, if the Ps 76 read is good.
- The S384 queue still stands: regenerate the Ps 76 bundle on the fixed concordance and radar (~$2–3), and literary
  echoes v3 (now with evidence: no top-three essay used a dossier echo).

## Gotchas
- **Effort must be identical in both calls** (it is part of the cached prefix), and so must the first user turn,
  byte for byte, `cache_control` included.
- Opus 5.5 thinking blocks are replayed unchanged. Never edit or strip earlier turns, or the preserved-thinking check
  400s on new accounts.
- The DOCX builder stubs `TanakhDatabase` with the psalm text from the inputs block. `tanakh.db` is not in the repo.
- LibreOffice in the cloud container would not load the DOCX ("source file could not be loaded"), so render-check on
  the author's machine or in Word.
