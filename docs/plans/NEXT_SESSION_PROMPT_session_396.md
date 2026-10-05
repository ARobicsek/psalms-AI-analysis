# Next session (396) — start here

Session 395 rebuilt the liturgy section (`docs/plans/S395_LITURGY.md`): 19 more Sefaria books in `liturgy.db`
(full selichot, Sefard machzorim, kinnot, the Chabad siddur, Ma'avar Yabbok …), a word-level matcher tested
against the whole Tanakh, a per-verse catalogue that groups reprints of one passage, and one Opus 5.5 call that
reads the WHOLE catalogue (the old librarian showed GPT-5.1 five rows per phrase). The writer and the fact
checker were told never to restrict a use from absence. Any re-run of a psalm (even `--resume` / `--skip-micro`)
replaces an old liturgy section with the new one. Committed and pushed.

## 1. A new machine needs the books

`data/liturgy.db` is gitignored: its 285 new rows are rebuilt with `python -m src.liturgy.sefaria_book_harvester`
(several minutes, $0). Without them the matcher still runs, on the old 1,123 texts.

## 2. The first full run on the new section

Next production psalm (79?) runs it by default. Watch: the section's length in the bundle (Ps 78: 17K chars),
the writer's liturgy section (does it keep the breadth — "every rite, weekday and Shabbat" — and not reintroduce
"only"/"certain"?), and the fact checker's liturgy verdicts (`every_ref` in use?). The liturgy call bills inside
the micro + bundle stage (~$0.55–1.0).

## 3. Optional

- **Ps 78's guide** still has the five old liturgy errors (S395 doc §3). Any full re-run now fixes them (a
  `--skip-micro` run reuses the bundle and swaps only the liturgy section, ~$0.6, then SD, writer, fact check,
  copy edit). Pss 1–77 likewise get the new section whenever they are re-run.
- **Ps 119** is the one psalm whose catalogue needs three parts; the merge was tested on Ps 103 (two).
- Sefaria's **Yom Ha'atzmaut & Yom Yerushalayim machzor** returned "no book" from the index API on 2026-10-04;
  retry with the harvester (it is in `BOOKS`).
- The old phrase index (`psalms_liturgy_index`) is now used only by `--liturgy legacy`.

## 4. Carried from the 395 handoff (untouched this session)

`NEXT_SESSION_PROMPT_session_395.md` §1–6: the author's read of the Ps 78 guide (the thread between notes,
grouping, the Sonnet 5.5 micro); chunking the micro discovery pass for long psalms; the fact-check budget on
long psalms; the synthesis-discovery empty-answer watch; the small items; the carried 393/394 items.
