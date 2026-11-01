# Session 412: the writer stops reading the used-works register; rhyme clusters flagged

Two questions from the author after reading the Ps 84 guide. No psalm was run. Session spend: 0.7¢
(one live repeat check). Code, tests and docs: see `IMPLEMENTATION_LOG.md` Session 412.

## 1. Echoes the writer had to filter out

The author: the writer's reasoning "seemed … to apply a filter to remove echoes after it had already
started reasoning about them." It did: the Ps 84 verse-call thinking has a "Verifying Source Material …
confirm they are all acceptable" pass.

Measured on the Ps 84 bundle (`output/psalm_84/psalm_084_research_v2.md`):

| | chars |
|---|---|
| whole bundle | 362,830 |
| echoes section | 94,016 |
| of which the register (`### Already used in this collection`) | 57,213 (529 rows; 61% of the section) |

Every dossier entry had already been filtered against that register in code (`filter_used` by
work/passage before retrieval, `repeated_quotation` by cut text after). Its only remaining job was the
writer's additions from memory. Measured by comparing each guide's register entry with its own dossier
(`same_work`): Ps 81 added 4, Ps 82 3, Ps 83 4, Ps 84 6 (some are naming mismatches of dossier items;
real additions: Douglass, the Qur'an, NOAA tides, a Corpus Christi chant, Mencius, the Hayflick limit,
11QMelchizedek, Cao Zhi, Zemlinsky, the Chida, Ibn Ezra's *Tzamah Nafshi* ...). None repeated an earlier
guide; the one apparent hit was *Sefer Shimush Tehillim* (Ps 84 vs 79), which the register wrongly held
"used as a whole" (and which the Ps 83 writer had left out on the never-repeat rule).

The author asked whether a "link" to the list would do. Without a tool the model cannot open one, and a
lookup tool mid-call (streamed Argon, replayed thinking, the shared cache) was judged not worth the risk
for a ~0-a-guide event. Chosen: no register for the writer; a check of the finished draft instead.

Validation of the check (`guide_repeats`) over the 54 guides in `data/literary_echoes/used_works/`,
each against earlier guides only: first version 1 false alarm in Pss 79-84 (Ps 80's Shabbat HaGadol
piyyut vs Ps 49's bare mention of one), fixed by never counting a text another guide only mentioned.
After the fix: 9 flags, all genuine pre-register repeats (Celan's "Psalm" 44 vs 41; Gilgamesh XI 50 vs
30; Sappho 31 55 vs 39; Amichai 61 vs 49; Donne "Batter my heart" 62 vs 51; Shamlou 63 vs 54; Moshe ibn
Ezra 67 vs 65; Szymborska 68 vs 46; Schütz's Musikalische Exequien 73 vs 49); none in Pss 77-85. A live
run on Ps 84's print-ready guide: 16 works, 0 repeats, 0.7¢ (with one cache read of Ps 85's guide).

Duplicates: the Ps 84 dossier carried Bialik's "El ha-Tsippor" twice (Gemini "Stanza 1" / Opus "Opening
stanzas", two spellings) and Dickinson's "Some keep the Sabbath" twice. The Dickinson pair are different
stanzas (stanza 1; stanzas 2-3) and stay; Bialik is one passage and now merges (`merge_retrieved_twins`,
by the cut text): 31 -> 30 entries.

## 2. The rhymes of 84:12

The author: מָגֵן / חֵן / יִתֵּן (and לַהֹלְכִים / בְּתָמִים) — real, or accident?

- `rhyme_scan.py` (first pass, this folder): clusters of 3+ words with the same closed final syllable
  per verse, Psalter: 78 verses, most of them grammar (-im ×41, -ay ×11, -am ×8 ...).
- `rhyme_lex.py`: grammar endings removed: 9 verses vs a shuffle baseline of 5.0 (Psalter); whole Bible
  949 vs 703. Reported to the author as "about twice chance".
- The production module (`src/concordance/sound_patterns.py`) also drops function words (אֲשֶׁר, the
  preposition אֶל) and paragogic -un: the 9 included refrains repeated word for word (144:8 = 144:11,
  130:7 ~ 131:3), which inflate the count, and 104:29's -un. **4 verses (78:24, 84:12, 90:2, 147:16)
  against a shuffle mean of 3.9: chance level.** The author was told; the section's note says the sound is
  real to a reader but must not be claimed to have chosen the words.

What argues against "the rhyme chose the words" in 84:12: חֵן … יִתֵּן is a stock idiom (Prov 3:34
וְלַעֲנָוִים יִתֶּן־חֵן), and מָגֵן takes up מָגִנֵּנוּ of v. 10. The -im pair is grammar (and a stock phrase, Ps 15:2).
