# Next session (394) — start here

Session 393 worked on deep research instead of the 393 handoff: audited the Gemini files for Pss 75–77, rewrote the
Gemini prompt, settled on a research chat + a fresh checker chat, and built `deep_research_cleaner` (Sonnet 5.5,
≤ $0.10/psalm) so the writer gets the report with the check applied. Details: `IMPLEMENTATION_LOG.md`, Session 393;
the record: `docs/plans/S393_DEEP_RESEARCH.md`; the prompts: `docs/prompts_reference/deep_research_prompt.md`.

## 1. Ps 78 is ready for its first full run

`data/deep_research/` holds the Ps 78 report, check (with the Tur OC 237 addendum) and the Sonnet-cleaned file
(current, so the run uses it without a new call). `python scripts/run_enhanced_pipeline.py 78` (full run; NOT
`--skip-micro`, which reuses an old bundle). Watch:
- the log line `Loaded deep research for Psalm 78: … chars (checked)`;
- the bundle's `## Deep Web Research` opens with the "corrected against an independent check" label and runs to
  `## Cross-Cultural Literary Echoes` (headings demoted);
- the methods page: "Deep Web Research: Yes (corrected against an independent check)";
- whether the guide uses `[unconfirmed]` items as fact, and whether the `[corrected by check]` tags leak into prose;
- Ps 78 is 72 verses: watch the 350K trim ceiling (S391 §6a) and the writer's length.

For the next psalms: two Gemini chats per psalm (research, then checker in a fresh chat), saved as
`psalm_NNN_deep_research.txt` and `psalm_NNN_deep_research_check.txt`; the pipeline cleans by itself.
`python scripts/clean_deep_research.py N` runs it ahead and writes a log to read.

## 2. Deep research, not done

- The $0 liturgy-and-practice table for all 150 psalms (`S393_DEEP_RESEARCH.md` §5): three of the seven Ps 78
  errors were liturgy.
- Two unsourced sentences already printed: Ps 77 guide line 41 ("some manuscripts add…" for Shimush), Ps 76 guide
  line 25 (the seventh day of Pesach).

## 3. Carried from the 393 handoff (untouched in 393)

`NEXT_SESSION_PROMPT_session_393.md`, all sections: the author's read of the Ps 76 reception A/B and the
`--reception` / `--targum` default decision; the first paid writer run of the rebuilt Sacks section (Ps 92 or 27);
the Ps 77 methods-page Sacks count; the older 391 items.
