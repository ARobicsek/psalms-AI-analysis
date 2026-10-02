# Deep research prompts (Session 393)

Two Gemini chats per psalm (Gemini Spark, free with the author's Pro account; the author's Spark skills are the live
copies of these texts):

1. **Research** → save as `data/deep_research/psalm_NNN_deep_research.txt`
2. **Checker, in a FRESH chat** (never the research chat: a model auditing its own report in the same chat
   "confirms" its own errors) → save as `data/deep_research/psalm_NNN_deep_research_check.txt`

The pipeline then cleans the report against the check (`src/agents/deep_research_cleaner.py`, Sonnet 5.5,
≤ $0.10) and the writer gets the corrected text. Why, and what each version of the prompt produced on Ps 78:
`docs/plans/S393_DEEP_RESEARCH.md`. The pre-S393 prompt: `archive/deep_research_prompt_pre_S393.md`.

## 1. Research

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

## 2. Checker (fresh chat)

```
This report on Psalm {N} was written by another model and contains errors. Find them. For each item about practice, liturgy, law, reception, dates, editions or catalogue numbers: open the source and quote the sentence that supports the claim. If you can't produce that quote, the item is NOT CONFIRMED. Output WRONG / NOT CONFIRMED / CONFIRMED (with the quote), with the correction for every WRONG item.
```

Read the check's **WRONG / NOT CONFIRMED** verdicts as strong and its **CONFIRMED** as "not caught": on Ps 78 the
checker quoted text it could not have seen and made one error of its own. To correct the check, append a section
headed `## ADDENDUM` to the check file; the cleaner lets the addendum win.
