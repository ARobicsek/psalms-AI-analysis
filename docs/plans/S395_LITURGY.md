# Session 395 — the liturgy section rebuilt

**The ask (the author, after reading Ps 78's guide and thinking):** "we haven't looked at our liturgy curation
pipeline in a while. it definitely gets things subtly wrong. e.g. 'vehu rachum' as being present in only certain
liturgical variants on monday and thursday, or an element being in CERTAIN selichot when it's in more than those
specific ones … it will find a passage in place A and not intelligently realize its also in similar place A' or
A'' etc. Can we investigate?"; then "yes. Use this session to maximally optimize our liturgical output".

## 1. What was wrong (measured, $0)

The data was mostly there; the librarian hid it.

1. **The model saw five rows.** `LiturgicalLibrarian._generate_phrase_llm_summary` sent GPT-5.1
   `prioritized_matches[:5]` per phrase, ties broken alphabetically by prayer name, plus a COUNT of contexts
   (the list itself was never sent). Over all 150 psalms: **3,779 of 8,024 matches (47%) never reached a
   model; in 118 summaries a whole rite was hidden, in 264 an occasion.** Ps 78:38 had 39 whole-verse rows
   (every rite: Hodu, Yehi Chevod, Uva LeTzion, weekday Ma'ariv, Monday/Thursday); the five shown were
   Edot HaMizrach and Sefard, so the guide printed "in the Nusach Sefard and Edot HaMizrach forms of Uva
   le-Tziyon" (line 44) and "the Shabbat and festival Pesukei Dezimra" (line 45). The "…and N more" line
   subtracted 15 when 5 were shown.
2. **One verse, many summaries.** Groups were keyed by (exact phrase, match type, verse), so 78:38 got five
   independent GPT calls and five contradicting paragraphs; the "Monday and Thursday" one saw only the Avinu
   Malkeinu rubric and three Sefard selichot. Corpus: 407 verses split this way, 1,112 calls.
3. **No corpus statement.** The model did not know which books had been searched (no daily selichot, no
   festival machzorim), so "the selichot we have" became "certain selichot".
4. **Matching faults.** Consonant SUBSTRINGS with no word boundary ("ציון אשר" found in the header "ובא
   לציון אשרי"; "אל וקדוש" in "אל וקדושתו"); the zero-width joiner of עָו‍ֹן survived normalisation (111 of
   1,123 texts), demoting the Ashkenaz machzorim's 78:38 to fragments; `is_unique` meant unique among
   PSALMS, not the Bible.
5. **Section titles are containers.** Ashkenaz Uva LeTzion at Ne'ilah is filed under "Ashrei".
6. **The fact checker checks presence, not scope**: "Sefard and EH forms of Uva le-Tziyon" → *supported*.

## 2. What was built

| Piece | File | Notes |
|---|---|---|
| More books | `src/liturgy/sefaria_book_harvester.py` | 19 Sefaria books into `prayers` (rows tagged `S395 book harvest`): full selichot (Ashkenaz Lita + Polin, EH), RH/YK machzorim in Nusach Sefard, Kinnot (Ashkenaz), Seder Tisha B'Av (EH), the EH Haggadah, the Chabad weekday siddur, Ma'avar Yabbok, Seder Ma'amadot, Tikkun HaKlali, Perek Shirah, Yizkor, Akdamut, Keter Malkhut, the Azharot, Ma'aneh Lashon. 1,123 → 1,408 texts, 5.4M → 10.2M chars. The Yom Ha'atzmaut machzor's index 404s. Backup: `data/liturgy.pre_S395.db` |
| Matcher | `src/liturgy/verse_matcher.py` | Word tokens on a spelling-tolerant key (`skeleton`); maximal runs; runs split by ≤ 2 variant words merged; refrains kept under both verses; every run tested against the whole Tanakh (`attribute`): a fragment the prayer quotes from another verse, or ≤ 3 words another verse shares, is dropped; a whole verse is kept with the parallel named (Hodu = 1 Chr 16) |
| Catalogue | `src/liturgy/liturgy_catalogue.py` | Units (whole psalm / verse span) → PLACES. A place is named by the nearest prayer opening (`LANDMARKS`, each with a reach; "just before Barchu"), else the section title. Hits are one place if the words on BOTH sides match (a day's selichot, a machzor's copy of the daily Hodu), or the same landmark with ≥ 3 of 6 words agreeing on both sides (another rite's copy). One line per rite × book, one excerpt per place |
| Librarian | `src/agents/liturgy_librarian_v2.py` | One Opus 5.5 call (effort `medium`, 64K) reads the whole catalogue; a catalogue over 80K chars is written in parts and merged (Ps 119: 3). Rules: generalise from the whole place; never restrict from absence; say what kind of use (recited / piyyut / prooftext / discourse); quote only from excerpts; coincidences → SET ASIDE (saved, not printed). The section opens with a code-written statement of the texts searched |
| Wiring | `research_assembler.py`, both pipelines | V2 by default; `--liturgy legacy` (env `PSALMS_LITURGY`) restores the old librarian |
| Writer | `forest_writer.S395_LITURGY_EDITS`, V4 RULE 5 | Every placement under a verse heading must appear; the echoes are optional; never "only"/"certain" without a quoted rubric |
| Fact checker | `fact_checker.py` | `search_liturgy` returns `every_ref` when hits exceed the six shown; a restricting claim is a claim about where the words are NOT |
| Runner | `scripts/run_liturgy_librarian.py N [--no-llm]` | one psalm's section on its own |
| Re-runs | `liturgy_librarian_v2.refresh_bundle_liturgy`, both pipelines' reused-bundle branch | a reused bundle with a pre-S395 section gets the new one in place (the author: re-running a psalm must overwrite the old section) |

## 3. Measured

- **Recall vs the old index:** 2,883 of its 2,886 verse-level (verse, prayer) pairs (the 3: Ps 126:5–6 in one
  Haggadah's Birkat HaMazon, Ps 118:29 in one Sefard Mincha). The first version lost 118, nearly all refrains
  (46:8 = 46:12; 118:1 = 118:29), now kept.
- **All 150 psalms** have catalogue entries; median 41K chars, largest Ps 119 (184K, 85 units).
- **Model choice (Ps 78):** Opus 5.5 `high`: thought through 32K tokens and was cut off ($0.88); Sonnet 5.5 `high`:
  cut off ($0.44), copied the ⟦ ⟧ marks and put Ne'ilah in the RH machzor; **Opus 5.5 `medium`, 64K: complete,
  $0.72** (then $0.55 after the catalogue was compacted).
- **Cost:** Ps 78 $0.55, Ps 27 $0.63, Ps 130 $0.60, Ps 103 $0.99 (2 parts). The old librarian: $0.17–0.52
  (Pss 74–77). About +$0.4 per psalm.
- **Ps 78 against its guide's five liturgy errors:** Uva LeTzion in all four rites; Pesukei Dezimra weekday and
  Shabbat in every rite; "אשר צוה את אבותינו" attributed to 1 Kgs 8:57; the annulment-of-vows and "ציון אשר"
  matches gone. New: the malkot on Yom Kippur eve (the Sefard rubric: 13 words × 3 = 39 lashes), the Edot
  HaMizrach house of mourning, Shir HaYichud (v. 8), kinnot (vv. 16, 54, 63), the selichot (vv. 5, 39, 60).
- **Ps 27:** the Elul rubrics quoted from each book (Ashkenaz to Shemini Atzeret; Sefard and Chabad to Hoshana
  Rabbah), and "the excerpt carries no seasonal rubric" for the Edot HaMizrach copy rather than a guess.
- Session spend ≈ $4.82 (all liturgy test calls).

## 4. Traps

1. **Never send the model a sample of the rows.** The whole failure was a `[:5]`. A place's rows are compacted
   per book, not cut; a catalogue too long for one call is split by units, never truncated.
2. **One side of shared context is not the same place.** The liturgy reuses verse chains: 78:38 + Ps 20:10 is
   both the end of Yehi Chevod and the verses before Barchu. Merge on BOTH sides (exact), or a landmark plus
   both sides nearly equal. A landmark label alone merged Ma'ariv into Yehi Chevod.
3. **Landmarks that are biblical verses get quoted in anthologies** (Viyehi Noam, Vayehi Binsoa, Mi El Kamokha
   were dropped): landmarks apply only in siddur / machzor / Haggadah texts, each with a reach, and "just before"
   only for the service openings in `JUST_BEFORE_LABELS`.
4. **A two-word fragment shared with another verse cannot be attributed** ("ביד צר" is Lam 1:7). `attribute`
   runs on every hit; keep it.
5. **The section's opening note is code, not model**: if the corpus changes, change `CORPUS_NOTE`.
6. **A re-run always carries the new section.** A plain run rebuilds the bundle; a run that REUSES one
   (`--resume`, `--skip-micro`, both pipelines) calls `refresh_bundle_liturgy`, which replaces a pre-S395
   section in place (one Opus call, ~$0.6, recorded as its own cost stage) and fixes the bundle summary's
   'Liturgical Librarian' line the methods page reads; a current section is left alone ($0). The test is
   `V2_MARKER` (the opening of `CORPUS_NOTE`): if `CORPUS_NOTE`'s first words change, old S395 sections will
   be re-written once.
7. Heredoc edits of Python with `\b` / `\n` in this shell corrupted twice (a literal backspace in a regex):
   edit regex lines with the Edit tool.
