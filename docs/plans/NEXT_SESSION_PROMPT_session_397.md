# Next session (397) — start here

Session 396 ran **Ps 79** in full ($10.02, no errors): the first production run on the S395 liturgy section.
Guide: `output/psalm_79/` (PDF also in the author's Google Drive as `Psalm 79.pdf`; NOT yet copied to
`Documents/Psalm study guide/`). Record: `IMPLEMENTATION_LOG.md`, Session 396.

## 1. The author's read of the Ps 79 guide

Open questions for the author once it is read: the liturgy section's breadth (the S395 rebuild's first guide),
the far echoes, and the one hand edit (the *Shimush Tehillim* sentence, softened after the run because its
wording came only from Gemini's checker).

## 2. Watch items from the Ps 79 run

- **Fact-check cost**: $2.76 on a 13-verse psalm (335 claims), against the ~$1.80 accepted budget. One data
  point; compare on the next psalm before acting.
- **Liturgy precision**: 12 of 78 liturgical claims contradicted, mostly sequence/adjacency slips ("immediately
  follows", "ends the selichot") and quotation details; the copy editor fixed them. If the pattern repeats, the
  liturgy section may need to state order only where the catalogue shows it.
- **`every_ref`** does not appear in `psalm_079_fact_check_telemetry.json`: confirm whether the fact checker
  actually uses it on liturgy claims (S395 wiring).
- **Editors' report false alarm**: a contradicted claim whose fix landed in the NEIGHBOURING sentence is reported
  "NOT changed … word for word" (Ps 79 C243, Alshich). Cosmetic, but it reads as a miss.

## 3. Known, left alone by the author's decision (do not re-propose unprompted)

- The echoes **used-works register** reads only `output/psalm_N/psalm_NNN_copy_edited.md`: blind to ~35 older
  printed guides and to A/B-arm guides copied to `Documents` (how Ps 78 repeated Bialik's *Metei Midbar* from the
  printed Ps 76). Details in the S396 log entry.

## 3b. New this session: the deep-research cleaner's guards

`deep_research_cleaner.guard_edit_list` (S396) turns placeholder replacements into deletions and withholds any
correction that quotes the CHECK (the original is marked `[unconfirmed]`). On the next psalm, read
`psalm_NNN_deep_research_clean_log.md`: the stats line counts both guards, and each withheld edit says which
quotation it refused. Known cost: a correction quoting the psalm in the checker's words is withheld too (Ps 79's
1 Maccabees item). If that recurs, consider exempting quoted spans found in the psalm's own text.

## 4. Remote sessions: getting the Gemini output in

Long pastes through the remote client arrive scrambled. Have the author share the research chat and the checker
chat as **Google Docs**; read them with the Drive connector and write the research file FIRST, the check second
(the cleaner runs only when the check is newer). Watch for the author's pre-made "empty" files: in S396 they were
byte-copies of the previous psalm's.

## 5. Carried

The whole 396 handoff (`NEXT_SESSION_PROMPT_session_396.md` §1, §3, §4): rebuilding `liturgy.db` on a new
machine; the optional Ps 78 re-run for its five old liturgy errors; Ps 119's three-part catalogue; the Yom
Ha'atzmaut machzor retry; and the 395 handoff carried inside it (the author's read of Ps 78, chunking the micro
pass for long psalms, the fact-check budget on long psalms, the SD empty-answer watch).
