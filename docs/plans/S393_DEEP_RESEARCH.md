# Session 393: deep research (Gemini) audited, re-prompted, checked and cleaned

**Read before changing the deep-research prompts, `src/agents/deep_research_cleaner.py`, or the
"Deep Web Research" section of the bundle.**

## 1. Why (the audit of Pss 75–77)

The writer took almost nothing from the deep-research files' paraphrases of Rashi/Radak/Ibn Ezra, Gunkel/Mowinckel
or the ANE tables; it took **liturgy, Shimush Tehillim and reception history** (Ps 76: Sukkot day 1, the seventh day
of Pesach, Shimush, the Armada, Drumclog, Resheph; Ps 77: Tikkun HaKlali, Shimush, Cowper) — the part no other
pipeline source checks. Spot checks (Wikisource, Sefaria, Wikipedia):

| Claim | Result |
|---|---|
| Shimush Tehillim, Ps 76 and Ps 77 entries | right (verbatim on Wikisource) |
| BCP: Ps 76 and Ps 77 at Evening Prayer, day 15 | wrong (Morning) |
| Charpentier *Notus in Judaea* "H.206" | wrong (H.179, H.219) |
| Ps 77 "secondary manuscript variants" (sea, night) | no source; printed in the Ps 77 guide (line 41) |
| Ps 76 on the seventh day of Pesach "in some Ashkenazi and Hasidic communities" | no source found; printed in the Ps 76 guide (line 25) |
| Ps 77 on Sukkot days 3–6 "Vilna Gaon", water-libation rationale | embellished: Wikipedia (citing the ArtScroll Tehillim p. 329) says days 3–6; Gemini added the Gra and the reason. Sukkah 55a's list for those days is 29, 50, 94, 94, 81, 82 |

Pattern: the liturgy/reception sections were Wikipedia's "Judaism / BCP / Music" sections plus confident additions,
and the telegraphic style stripped the "according to X". The bundle introduced the section as scholarly commentary.
About half of each file repeated what the pipeline now has from primary texts (commentaries in full, the Sefaria
reception section, Brenton's LXX, the Targum, the shared-vocabulary radar).

## 2. Four Ps 78 rounds (Gemini, free, the author's Spark skill)

1. **Old prompt, Deep Research mode (Flash):** ignored the format; a 30K-character essay, no sources, nothing on
   practice. Good: Sinaiticus/Jerome/Porphyry on Matt 13:35, Campbell, Weber, "Moses is never named". Half right:
   the middle verse (Masorah at 78:36; the Talmud, Kiddushin 30a, says 78:38).
2. **New prompt (below), plain Spark:** followed the format, covered far more — but the errors moved into the
   citations: the **Old Deluder Satan Act** (1647) "rests on Ps 78" (the Act cites no psalm); the **Mishnah**'s
   "13 × 3 = 39" (not in the Mishnah); Clifford's article title and journal invented; a "verbatim" Shimush entry
   (Wikisource has none for 78).
3. **Research + audit in one prompt:** the self-audit "confirmed" its own errors (the Ma'ariv reason "confirmed"
   with a Makkot link), skipped the Old Deluder claim, and refuted a claim the report never made. Do not do this.
4. **Research chat, then a fresh "checker" chat told the report contains errors:** the checker caught every error
   found by hand plus four more (Ma'aseh Rav §194 day 2; Liturgy of the Hours Week IV; Lasso LV 705 is the
   *Improperia*; Jerome's Matthew commentary does not name Porphyry). Its own faults: "the Shulchan Arukh has no
   chapter 237" (it does), and CONFIRMED verdicts that quote text it cannot have seen (a Selig page, a Schütz
   catalogue entry, Greek with a Hebrew letter in it). **Trust its WRONG / NOT CONFIRMED; read its CONFIRMED as
   "not caught".**

Found by hand and added to the Ps 78 check as an ADDENDUM: **Tur, Orach Chayim 237** gives both reasons Ma'ariv
opens with Ps 78:38 (no evening offering to atone; people were flogged in the evening and the verse, 13 words × 3,
was said during the 39 lashes). The Rema (OC 607:6) applies the count to the erev–Yom Kippur lashes.

## 3. The workflow now

1. Gemini chat 1 (research prompt, below) → `data/deep_research/psalm_NNN_deep_research.txt`.
2. Gemini chat 2, fresh (checker prompt, below) → `psalm_NNN_deep_research_check.txt`. Add an `## ADDENDUM`
   to correct the check itself if needed; the cleaner lets it win.
3. The pipeline (or `python scripts/clean_deep_research.py N`) writes `psalm_NNN_deep_research_clean.txt` +
   `_clean_log.md` when the check is newer than the clean file, and the bundle uses the clean file, labelled
   (`DEEP_RESEARCH_CHECKED_NOTE`). A hand-edited clean file is never overwritten. Without a check file the raw
   report goes in with the old label (unchanged behaviour for the 66 older files).

**The cleaner** (`src/agents/deep_research_cleaner.py`): the model returns FIND/REPLACE edits on the report
(`copy_editor.apply_edit_list`), so nothing the check does not address can change. WRONG → corrected fact +
`[corrected by check]` (or deleted); NOT CONFIRMED → `[unconfirmed]`; CONFIRMED untouched; the checker's quotations
are never copied in. Cap $0.10 per psalm, enforced before each call (input counted, `max_tokens` cut).

Model comparison on the same Ps 78 report and check:

| Model | Cost | Result |
|---|---|---|
| **Sonnet 5.5, one pass, effort low (default)** | 7.0¢ | every WRONG item fixed in every place; nothing invented; tags only where the check put them |
| Haiku 4.5, two passes (pass 1 + "sweep") | 5.1¢ | kept a softened Puritan claim as [unconfirmed]; over-tagged two bullets; invented "an Ashkenazic custom" |
| Haiku 4.5, one pass (first version) | 2.4¢ | fixed each claim once, leaving its TOP FINDINGS / body twin wrong; softened the Old Deluder claim |
| gpt-6-luna, one pass | 0.3¢ | left TOP FINDING #11 (Cotton Mather) untouched |

If a long report leaves Sonnet < 4,000 output tokens under the cap, the run falls back to Haiku with the sweep.

**Also fixed:** the loader demotes the file's `#`/`##` headings under `## Deep Web Research`; before, a `##` inside
the file (Pss 27, 72, 74, 77, 78) ended the section for every reader that splits on `## ` (the runners' stats regex,
the trimmer). The methods page now says "Yes (corrected against an independent check)" for a cleaned file
(`pipeline_summary.deep_research_methods_value`, shared by the three renderers).

## 4. The prompts (the author's Spark skills are the live copies)

### Research (chat 1)

```
The user gives a psalm number {N} (Masoretic numbering). Use your strongest research model and search thoroughly.

ROLE. You research for an AI writer producing a reader's guide to each psalm. The writer quotes and builds on what you report and cannot check it: a wrong fact you report will be printed. Accuracy and sources first, coverage second.

THE WRITER ALREADY HAS (do not research or summarise these; they come from primary texts):
- Hebrew text, JPS translation, Brenton's Septuagint (Greek + English), the Targum.
- Full Sefaria commentaries: Rashi, Ibn Ezra, Radak, Meiri, Malbim, Metzudot, Sforno, Alshich, others.
- Talmud, Midrash Tehillim and classical midrash passages that quote the psalm; Rabbi Sacks.
- Concordance, BDB lexicon, verbal parallels elsewhere in the Bible.
- Literary echoes (poems, novels, art); a separate process finds these.
Mention these only where a modern scholar argues about them, or where you found something not in the text itself (a manuscript variant, a Qumran reading).

FIND (the gaps):
1. Modern scholarship: positions of the major critical commentaries (e.g. Hossfeld–Zenger, Goldingay, Tate, Kraus, Alter, Amos Hakham/Da'at Mikra, Dahood) and journal articles of the last ~40 years on this psalm. Who argues what, especially disagreements. TheTorah.com articles.
2. Text criticism: Dead Sea Scrolls (siglum), Peshitta, Aquila/Symmachus where they differ from MT; emendations, with who proposed them.
3. Ancient Near Eastern parallels: specific texts only, cited by edition (COS, ANET, KTU no.) with a short quote. No generic "ANE kings did X".
4. Jewish practice: where/when the psalm or a verse is recited (rite, occasion) and the SOURCE recording the custom (Mishnah/Talmud, Soferim, Ma'aseh Rav for the Gra, a named siddur or minhag book). Shimush Tehillim: quote the entry verbatim, name the edition. Other folk, amuletic or Hasidic uses, with source. Give a reason a custom chose this psalm only if a source gives one; your own reason may follow, labelled INFERENCE.
5. Christian use: liturgy (BCP day and office, Roman office) and notable patristic/medieval/Reformation readings with the work cited.
6. Afterlife: political, military, legal, musical (composer, work, catalogue no., year), artistic. A dated event needs a documentary or scholarly source, not a devotional site.
7. Anything genuinely surprising: an unexpected use, a famous misreading, a live scholarly controversy.

RULES:
- Every item has a source: author/title + page or section, or a DIRECT URL (never a google.com/search link). Tag it [primary] / [scholarly] / [reference] (encyclopedia, Wikipedia) / [popular].
- Tag every source [seen] (you opened it in this session; give the URL) or [memory]. Never invent a page number: if you did not see the page, give the chapter or nothing.
- When you say a source says something, it must say that itself. If the detail comes from a later source or custom, name that one instead.
- If an item came from Wikipedia or a popular site, say so, and give the source it cites.
- Quote verbatim (≤ 50 words) wherever the source has a quotable sentence; the writer quotes.
- Never fill a gap with a plausible guess. Searched and found nothing → write NOT FOUND. An empty heading is useful information.
- Mark your own inferences INFERENCE.
- Masoretic verse numbers throughout (superscription = v. 1).

FORMAT (for an AI reader: dense, but never at the cost of the source):
- Open with ## TOP FINDINGS: the 8–12 items most likely to surprise a well-read reader or change how the psalm is read, one line each, with source.
- Then one ## section per area above, in bullets. Fragments fine, no filler; "according to X" is not filler.
- Close with ## UNCERTAIN: items found but not confirmed, and why.
```

### Checker (chat 2, a FRESH chat — never the research chat)

```
This report on Psalm {N} was written by another model and contains errors. Find them. For each item about practice, liturgy, law, reception, dates, editions or catalogue numbers: open the source and quote the sentence that supports the claim. If you can't produce that quote, the item is NOT CONFIRMED. Output WRONG / NOT CONFIRMED / CONFIRMED (with the quote), with the correction for every WRONG item.
```

## 5. Not done (ideas, ranked in the session)

- **A $0 liturgy-and-practice table for all 150 psalms** (BCP day/office computed; Shimush Tehillim verbatim from
  Wikisource; Tikkun HaKlali; Tamid 7:4 and Sukkah 55a; Ma'aseh Rav §194-type festival lists; Wikipedia's usage
  sections with their footnotes). Three of the seven Ps 78 errors were liturgy.
- The two unsourced sentences already printed: Ps 77 guide line 41 ("some manuscripts add…"), Ps 76 guide line 25
  (seventh day of Pesach).
- Merge two research runs for coverage; where two runs disagree, at least one is wrong.
