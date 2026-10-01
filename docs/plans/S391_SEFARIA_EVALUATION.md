# Sefaria: what we use, what is there now, and what is worth adding (Session 391)

**The question** (the author): *"Sefaria has come a long way … it now contains a lot of new content (including R Jonathan Sacks content) … our R Sacks approach was also very clunky … evaluate how we use Sefaria, what if anything is now accessible that might substantially improve our insights or make our content legitimately more interesting/richer (so not just another medieval commentator similar to ones we have), and what we'd need to do to incorporate it."*

**Method**: everything below was measured against Sefaria's live public API on 2026-10-01, at $0: the full catalogue (`/api/index`), `/api/links/Psalms.N` for **all 150 psalms** (125,838 links), version and license lists for each candidate work, the text of every candidate on Psalm 77 (the current test psalm), a full download of Rabbi Sacks's liturgical commentary (1.38M characters) and a prototype alignment of it to the psalms. Scripts and reduced data: `archive/S391_sefaria_probe/`. No pipeline code was changed.

---

## 1. The short answer

Sefaria now holds three things that would make the guides **legitimately richer**, none of which is "another medieval commentator":

| # | What | Why it is different from what we have | Size per psalm | Effort |
|---|---|---|---|---|
| **1** | **The rabbinic and later reception of each verse**: Talmud, classical Midrash (incl. *Midrash Tehillim*), Philo; then, curated, Jewish thought, Hasidut, Kabbalah, Musar | Our eleven commentators are all exegetes reading the verse in order. This is the verse **in use**: quoted, argued over, built into law, theology, mysticism. Today the writer sees it only through Torah Temimah and its own memory, and the memory is wrong in exactly the ways a supplied text would prevent (§3.1) | median 70 midrash, 12 Talmud, 50 Hasidic, 26 Kabbalah, 20 thought links per psalm; Ps 77 = 162 passages | Medium (new harvester + cache, optional curator) |
| **2** | **The Aramaic Targum** of every verse | An ancient Jewish translation that interprets as it translates, the same class of witness as the LXX the writer got in S390. The guides already cite it, from memory or second hand (§3.2) | one line per verse | Small (same shape as S390's Brenton work) |
| **3** | **Rabbi Sacks, rebuilt**: his siddur and mahzor commentary (a genuine running commentary on the liturgical psalms) plus his books, harvested live | The current file is a 2025 snapshot of book excerpts only; the liturgical commentary (the closest thing to "Sacks on Psalms" that exists) is not in it at all (§3.3) | 0 to ~25K chars; 105 psalms have something vs 56 today | Small–medium |

Also worth doing, cheaply: **pin text versions** (Sefaria's default English for Psalms is now the 2023 JPS Gender-Sensitive Edition, and nothing in our code pins a version), and **fetch commentaries per chapter with retries** (today: one request per commentator per verse, a 10 s timeout and no retry, which is how Ibn Ezra on 77:9 silently vanished in S387). §4.

Looked at and **not** recommended: Steinsaltz on Psalms (a running paraphrase, the genre the corpus shows the writer ignores, and under copyright), Topics, source sheets, manuscripts, web pages, the midrash anthologies. §3.5.

---

## 2. How the pipeline uses Sefaria today

| Where | What it fetches | How | Notes |
|---|---|---|---|
| `data_sources/sefaria_client.py` → `tanakh.db` | Psalm (and all Tanakh) Hebrew + English | v1 `/api/texts`, **default versions** | Built once. A rebuild today would get the 2023 JPS GSE English, not whatever the db holds now |
| `sefaria_client.fetch_lexicon_entry` (BDB librarian, RAG manager) | BDB + Klein entries | `/api/words/{word}` | Fine |
| `agents/commentary_librarian.py` | 11 commentators on every verse | v1 `/api/texts/{Commentator}.{ch}.{v}`, **one request per commentator per verse** (Ps 77: 231), 0.5 s rate limit, 10 s timeout, **no retry** | A timeout returns `None` and the entry is silently missing |
| `liturgy/*` → `data/liturgy.db` | Psalms → liturgy links; prayer texts | `/api/related`, harvested once | Feeds the liturgical librarian and the fact checker's `search_liturgy` |
| `agents/sacks_librarian.py` | Rabbi Sacks | **No API call.** Reads `sacks_on_psalms.json` (7 MB, committed; built Session 68, Nov 2025) | 206 entries, 57 psalms (56 with a usable snippet); each = the raw Sefaria payload + a ~±1,000-char window. Every bundle that has one also carries a **2,243-char biography** of Sacks |
| `agents/fact_checker.py` | verse / commentary / any text lookups; Tanakh search; name resolution | v3 `/api/v3/texts`, `/api/search-wrapper`, `/api/name` | The only v3 user |
| Deep Web Research | reception history, generally | Manual Gemini Deep Research, not Sefaria | 9 files in the repo |

So for everything except the eleven commentators, the reception of a verse reaches the writer from Deep Research (when it exists), Torah Temimah (which indexes some of the Talmud), and the writer's own memory.

---

## 3. What is on Sefaria now, and what is worth having

Links to Psalms across all 150 psalms, by Sefaria's category (Commentary, Quoting Commentary and Reference are what we already use or do not need):

| Category | Links | Median / psalm | Range | With English | Main works |
|---|---|---|---|---|---|
| Midrash | 13,127 | 70.5 | 6–419 | 62% | *Midrash Tehillim* (1,932 links, 149 psalms), Tanchuma (×2), the Rabbot, Mekhilta, Pesikta (×2), PRE; plus anthologies (Yalkut, Ein Yaakov, Sekhel Tov, Lekach Tov) |
| Chasidut | 10,756 | 50.5 | 2–559 | 24% | Yismach Moshe, Likutei Moharan, Toldot Yaakov Yosef, Mei HaShiloach, Sefat Emet, Kedushat Levi, Tanya, the Ba'al Shem Tov |
| Kabbalah | 5,635 | 26 | 1–299 | 47% | Zohar (2,204, 142 psalms; Soncino English, public domain), Reshit Chokhmah, Tikkunei Zohar, Sha'arei Orah |
| Jewish Thought | 4,615 | 19.5 | 1–249 | 47% | Akeidat Yitzchak, Duties of the Heart, Saadia, the Guide, the Kuzari, Maharal, Rav Kook, Sacks |
| Musar | 4,025 | 19 | 0–217 | — | Shelah, Reshit Chokhmah, Pele Yoetz |
| Targum | 2,528 | 13 | 2–176 | see §3.2 | the Aramaic Targum to Psalms |
| Talmud | 2,174 | 11.5 | 0–65 | **97%** | Berakhot (192 links, 75 psalms), Yerushalmi Berakhot, Sanhedrin, Avot DeRabbi Natan, Pesachim, Rosh Hashanah |
| Halakhah | 1,765 | 10 | 0–87 | — | Mishneh Torah, Shulchan Arukh and commentaries |
| Second Temple | 48 | 0 | 0–5 (33 psalms) | 35% | **Philo** (33 links, 23 psalms), Josephus, Tobit, Maccabees |

### 3.1 The reception layer, which is the largest gap

**What it looks like on Psalm 77.** After dropping the anthologies (which repeat earlier midrash), Sefaria links Ps 77 to **162 passages**: 85 midrash, 22 Hasidic, 21 Targum, 12 Kabbalah, 10 Jewish thought, 6 Musar, 3 halakhah, 3 Talmud; 103 have English. A sample, read in full:

- **Sanhedrin 19b on 77:16** ("the children of Jacob and Joseph"): *"Did Joseph sire all of Israel? Jacob sired them and Joseph sustained them; therefore they were called by his name."* (Whoever raises a child is as if he bore him.) This is the source of the Targum's rendering (§3.2) and of Rashi's.
- **Berakhot 59a on 77:19** ("the voice of Your thunder was in the whirlwind [*galgal*]"): Shmuel's theory of thunder (clouds grinding against the curve of the firmament) is built on this verse, and the Rabbis answer him with others. A real "science of the ancients" moment.
- **The crux 77:11** (*ḥalloti hi shenot yemin elyon*) has a sustained afterlife as a theological text: the Rema's *Torat HaOlah*, the Shelah, the Toldot Yaakov Yosef and *Tzofnat Paneach* all read it as *"my sickness is that I think the right hand of the Most High has changed"*: God does not change; the change is in the receiver. That is a five-century reading of the psalm's hardest verse, and it touches the guide's central question.
- **Vayikra Rabbah 23:2 on 77:16**: the redemption from Egypt was as hard for God as picking a lily from among thorns.
- **Yerushalmi Berakhot 9:1 on 77:14** ("O God, Your way is in holiness"): God is "holy in every kind of holiness".
- **Midrash Tehillim 77**: the heading *al Yedutun* read as *al ha-datin*, "on the decrees"; Habakkuk draws a circle and will not leave it until God answers; *"I remember my song in the night"* = the Sanhedrin.
- **Yismach Moshe on 77:19**: why we see the lightning after the thunder that caused it.
- A **Selichot piyyut** for the Fast of Esther built on 77:15–16, and Rebbe Nachman's **Tikkun HaKlali** (Ps 77 is one of its ten psalms), which the source sheets surface.

**The guides need this, and their errors show it.** Two from finished guides in `archive/`:
1. **Ps 27** (`archive/psalm_27_PRE_S378/psalm_027_print_ready.md`, lines 98 and 203): *"Later pietistic works link אוֹרִי to Rosh Hashanah, וְיִשְׁעִי to Yom Kippur …"* It is **Vayikra Rabbah 21:4**, a classical midrash: *"The Rabbis interpreted the verse regarding Rosh Hashanah and Yom Kippur: 'my light' on Rosh Hashanah, 'my salvation' on Yom Kippur."* Sefaria links it to 27:1. The guide made a fifth-century rabbinic reading into a late pious custom.
2. **Ps 76** (§3.2 below): the Targum, known only through the Alshich, reported by half.

Across the Ps 76 two-call guides, the whole of rabbinic reception is 2–4 Talmud mentions, 2–3 "midrash", 2 Hasidic, 1 Kabbalah. The Ps 27 guide (7,844 words): Talmud 4, midrash 2, and no Midrash Tehillim, Targum, Zohar or Hasidic source at all.

**Size.** Prototype windows on Ps 77: **tier 1** (Talmud, classical midrash, Targum, Philo) = 109 passages, **~37K characters** at 400 characters each; **tier 2** (thought, Musar, Hasidut, Kabbalah, halakhah) = 53 passages, ~20K. Full segments would be ~320K English + ~370K Hebrew characters, so this must be cut, not dumped. Busy psalms are much bigger (Ps 145 has 1,759 links of all kinds, Ps 92 1,328), so a per-psalm cap matters.

**What it would take** (design follows the S389 echoes lesson: retrieve and cut in Python; a model may choose but never copies):
1. `src/data_sources/sefaria_reception.py`: one `/api/links/Psalms.N` call; keep the reception categories; drop the anthologies (Yalkut Shimoni, Ein Yaakov ×2, Sekhel Tov, Lekach Tov, Otzar Midrashim); fetch each segment through v3 (English preferred, Hebrew always); **locate the verse inside the segment by consonantal match** (Sefaria's English often paraphrases, so match the Hebrew) and cut a window (a sentence or two each side). Cache per psalm under `data/sefaria_cache/` (as `data/lxx/` is), so re-runs and the fact checker cost nothing.
2. **Choose, two options** (an A/B decides):
   - **(a) deterministic**: tier 1 in full (~35–60K chars), tier 2 as a one-line index (work, ref, verse, first words). $0, but adds ~10–17% to the 349K-char Ps 77 dossier.
   - **(b) curated**: a mid-tier model reads the whole harvest (~90K tokens on Ps 77) and returns ~20–30 picks with one sentence on the interpretive move each; Python cuts the passages. About $0.02 (luna) to ~$0.25 (Sonnet 5 / Gemini 3.1 Pro). Caution from S386: luna misses rabbinic shape errors, so the curator probably should not be luna.
3. Bundle section `## Rabbinic and Later Reception`, grouped by verse, each item labelled by work and date (`compDate` comes with every link). Give it a place in the trimmer's priority, a line on the methods page, and the fact checker's `get_text` can answer from the cache.
4. Writer: probably no instruction change at first (the S389 rule: the writer chooses). A/B on the guide.

**Cost per psalm**: harvest $0 (≈150–300 API requests, 1–2 minutes, cached); curation $0–0.25; writer + synthesis discovery read the extra ~10–20K tokens through the shared cache (Opus 5.5: $5/MTok write, $0.20/MTok read): **≈ $0.10–0.25**.


### 3.1a The author's decisions (same session) and the selection rules

**Decisions**: scope = Talmud, classical midrash, the Targum and Philo; Hasidut / Musar / halakhah possible; **no Kabbalah, no Jewish thought**. **No selection model**, because it would overdetermine what the writer writes: programmatic rules, or at most a very simple model. Licensing: **personal use only**, so CC-BY-NC is fine. Tests: **Ps 76 and 77**; re-running synthesis discovery and the writer on Ps 76 with and without the change is approved.

**Rules (prototype `archive/S391_sefaria_probe/rules2.py`, $0, no model).** They select on the KIND of source and its AGE, never on how interesting a passage looks:

1. **Locate or drop.** The verse must be found inside the passage: the longest run of consecutive verse words, matched on consonantal skeletons (matres lectionis removed, up to two prefix letters, common suffixes, the divine-name spellings ה׳ / יי / אלקים). This also removes Sefaria's mis-links (Ps 77 has links to "77:49" and "77:51", which belong to Ps 78).
2. **One passage, one item.** A passage linked to several verses is one item with a verse range (Eikhah Rabbah 1:23 covers 77:7–11).
3. **Parallels collapse to the earliest telling.** 4-gram shingle overlap ≥ 0.25 around the quotation; the later versions are named, not printed (Tanchuma / Tanchuma Buber; Shabbat 88a / Avodah Zarah 3a).
4. **Tier A, always kept:** Talmud, Mishnah and Tosefta with an early known date, plus *Midrash Tehillim* on its own psalm. (Ps 77: 4 items; Ps 76: 7.)
5. **Tier B, classical midrash and Philo:** per verse, earliest first; drop a bare proof-text (the verse after "שנאמר / דכתיב…", none of its words reused, in a passage of more than 600 characters); at most 2 per verse, filled round-robin so every verse gets its first before any gets its second.
6. **Tier C, later readers (Hasidut / Musar / halakhah):** a **convergence rule**. When three or more *different* later works return to the same verse, that verse has a reception tradition of its own: keep the earliest telling and name the others. Then a small allowance (one per four verses) for single passages that visibly work the verse.
7. **Budget**: about 1,100 characters per verse (Ps 77: 23K; Ps 76: 14K, about 6–7% of the dossier), with a Hebrew window of 30 words before and 60 after the quotation plus the English (whole if ≤ 900 characters, else a window). Fill order: A → first B per verse → C convergence leads → second B per verse → C singles.
8. **Presentation**: neutral, by verse, then date; work, date, ref, the cut text, "parallels:" and "also:" lines. **No summaries and no "why it matters"**, so nothing tells the writer what to make of it.

**What it keeps** (full lists in `selection_ps77.txt` / `selection_ps76.txt`):
- **Ps 77** (82 located → 77 after parallels → 24 kept): Midrash Tehillim 77, Sanhedrin 19b (v. 16), Berakhot 59a (v. 19), Yerushalmi Berakhot 9:1 (v. 14), the Mekhilta on the Sea (vv. 17–19), Pesikta DeRav Kahana and Eikhah Rabbah on vv. 7–11, and as convergence leads the Hasidic line on **v. 11** (Ben Porat Yosef; also Toldot Yaakov Yosef, Tzofnat Paneach), on v. 16 and on v. 20.
- **Ps 76** (70 → 66 → 13): Midrash Tehillim 76, Shabbat 88a on v. 9 (the earth "feared, then was still" until Israel accepted the Torah; parallel Avodah Zarah 3a), Bereshit Rabbah 56:10 on Salem = Jerusalem (v. 3), Tosefta Berakhot, Soferim, Yerushalmi Maasrot and Nedarim, and the Mekhilta. Its budget (14K) filled before the v. 9 Shavuot cluster (Sefat Emet ×6, Shem MiShmuel, Likutei Moharan…) was reached; **the per-verse budget is the knob.**

**What failed, and why the rules are structural.** v1 (`rules.py`) ranked by content: verse words reused outside the quotation, plus interpretive and proof-text cue words. It **dropped my three best Ps 77 finds**. Sanhedrin 19b lost to the per-verse cap. In Berakhot 59a the reused word was שבגלגל, two prefixes deep. And the Hasidim on 77:11 paraphrase rather than repeat the verse. Word overlap is good only for dropping obvious proof-texts.

**If a model is ever needed** (e.g. the proof-text filter proves too blunt): a **yes/no classifier** ("does this passage interpret this verse, or cite it as proof for something else?") on Haiku 4.5 or gpt-6-luna, about $0.01/psalm. It filters noise and never ranks or summarizes.

**Known rough edges**: Sefaria's `compDate` is noisy (Tanchuma Buber is dated 150), so "earliest" is sometimes wrong; undated works fall to tier C; the Hebrew window is cut by word count, not sentence.

### 3.2 The Targum

Sefaria has the Aramaic Targum to Psalms for **all 150 psalms** (Mikraot Gedolot, public domain). It has an English translation for only **35 psalms** (Edward M. Cook's, plus a community translation: Pss 1–18, 24, 68, 83, 90–92, 104, 113–118, 120–123). Opus 5.5 reads Aramaic; Cook's complete translation is published on targum.info if English for all 150 is wanted.

It is **interpretive**, and on Ps 77 the interpretations land on the cruxes:

| Verse | Hebrew | Targum (my gloss) |
|---|---|---|
| 77:3 | *yadi laylah niggerah* | "In the day of my distress I sought **instruction** from before the LORD; **prophecy rested on me** in the night; **my eye** shed tears without ceasing": the "hand" read twice, as the hand of prophecy and as the weeping eye |
| 77:7 | *va-yeḥappes ruḥi* | "and **trials** search out the knowledge of my spirit" |
| 77:9 | *gamar omer* | "has He completed **an evil decree** for every generation?" |
| 77:11 | *ḥalloti hi shenot yemin elyon* | **two readings**: "my sickness is this: the might of the right hand of the Most High has changed", **and** "my prayer is this: **the years of the End** from the right hand", an eschatological reading of the crux |
| 77:16 | *benei Yaakov ve-Yosef* | "the sons **whom Jacob begot and Joseph sustained**" (= Sanhedrin 19b) |
| 77:17 | *ra'ukha mayim* | "they saw **Your Shekhinah** in the midst of the sea … **the peoples** trembled" |
| 77:20 | *ba-yam darkekha* | "in **the Sea of Reeds** was Your way … the **traces of Your footsteps** were not known" |

And on **Ps 76:5** (*na'or attah*), where the S385 guide wrote *"The Alshich reports that the Targum renders the word דְּחִיל, 'fearsome'"*, the Targum actually reads **נְהִיר דְּחִיל אַתְּ**, "**luminous, fearsome** are You": both of the readings the commentators split over (Ibn Ezra's light, the root of awe) at once. The guide reported half, second hand, because the pipeline never gave it the Targum.

**What it would take**: the S390 Brenton work, again. `src/data_sources/targum.py` (fetch `Aramaic_Targum_to_Psalms.N` once, cache at `data/targum/`, Cook's or the community English where present); a `**Targum:**` line per verse in `MasterEditor._get_psalm_text` beside `**LXX:**` (synthesis discovery reads the same text, so the shared cache holds); `get_targum` for the fact checker. Numbering is the MT's (no LXX-style remapping). Consider a budget note like RULE 8b's for the LXX. **≈ 1–2K characters per psalm; cost ≈ $0.**

### 3.3 Rabbi Sacks, rebuilt

> **BUILT in Session 392** (`src/data_sources/sacks_index.py`, `src/agents/sacks_librarian.py`, `scripts/build_sacks_index.py`, `tests/test_sacks_index.py`). Differences from the plan below, all found while building: (1) the liturgical alignment does not need the comment's incipit at all: every comment is **linked** to its Koren paragraph (`/api/links/<work>`, one request per work), so a comment is aligned through the psalm verses found in that paragraph, and S391's false positive (76:8) is gone; (2) Sefaria holds most of his *Jewish Thought* books **only in Maggid's Hebrew translation** (*The Great Partnership*, *Future Tense*, *To Heal a Fractured World* …), so those passages are given in Hebrew, labelled as a translation; (3) a single-verse prayer-book comment (a mosaic paragraph) is kept only if it names the psalm or two words of its lemma are in the verse; book passages are capped at 4 per verse (Ps 23:4 alone had 10). Found on the way: `sefaria_reception.word_tokens` fused maqaf-joined words (the maqaf lies inside the niqqud range); fixed, and Ps 76's reception section is unchanged by it. **Coverage: 95 of 150 psalms (71 with prayer-book commentary), against 56; section median 4.6K chars, max 21.9K (Ps 115). Ps 76 and 77 still have nothing.** Ps 80's old "excerpt" was a footnote citing *Midrash Shoḥer Tov to 80:6*, correctly gone. `sacks_on_psalms.json` deleted. Not yet tested in a paid run.

**What we had**: `sacks_on_psalms.json`, built in Session 68: 206 entries over **57 psalms**, all from his books, each a ~±1,000-character window around a linked psalm reference (11 have no window at all), committed as 7 MB of raw API payloads, and introduced in the bundle by a 2,243-character biography.

**What is there now**:

1. **His liturgical commentary, which the file does not contain at all**: *Rabbi Sacks on Siddur* (the Koren Shalem Siddur), *Rabbi Sacks on Rosh HaShana Mahzor*, *… on Yom Kippur Mahzor*, *The Jonathan Sacks Haggadah* commentary. All English, CC-BY-NC, 240 sections, 1,305 comments, **1.38M characters**. It is a real running commentary on the psalms the liturgy uses: Kabbalat Shabbat (95–99, 29, 92–93), Pesukei DeZimra (19, 33, 34, 90, 91, 135, 136, 145–150 …), the daily psalms (24, 48, 82, 94, 81, 93, 92), Hallel (113–118), 27 for Elul, 130, 47, 23 at Seudah Shelishit, 104, 144, 121–134. Three examples:
   - Ps 92: *"the Midrash taking its opening phrase to mean not 'a song for the Sabbath day' but 'a song sung **by** the Sabbath day' … in the silence of Shabbat, we hear the song creation sings to its Creator."*
   - Ps 90: *"a succession of poetic images conveying the brevity of human life … The speed with which these metaphors succeed one another mirrors the rapidity with which the days and years"* pass.
   - Ps 23: *"a poetic masterpiece – a mere 57 words long – of trust in God's gentle care."*

   **These comments are not linked to Psalms on Sefaria.** They hang off the Koren siddur's paragraphs, and those paragraphs are not linked to Psalms either. They must be aligned by us. A prototype (the comment's Hebrew incipit matched against the psalm text, plus "Psalm N" in the English) reaches **92 psalms** (45 where he comments on the psalm's own words), but has false positives (it matched a Ne'ilah piyyut to Ps 76:8). The production version should align the **Koren siddur's Hebrew paragraph** to `tanakh.db` (≥ 3 consonantal words, as the liturgy indexer already does) and take the Sacks comment on that paragraph. $0.
2. **His books, harvested live**: `/api/links` now gives **286 passages over 67 psalms** (181 the same as the file's; 14 psalms new: 15, 41, 42, 61, 71, 81, 84, 88, 91, 102, 122, 127, 149, 150). New on Sefaria since the file: *The Great Partnership*, *Arguments for the Sake of Heaven*, *Will We Have Jewish Grandchildren?*, the Hebrew editions.
3. **Quotations Sefaria never linked**: a Hebrew phrase search (`/api/search-wrapper`, `naive_lemmatizer`) over his works finds more. For Ps 23 it adds 23:4 in *Future Tense* (×3), *The Great Partnership* (×2), *The Home We Build Together*, *Judaism's Life-Changing Ideas* and the C&C Hebrew edition.

**Coverage after a rebuild: 105 psalms with something, against 56 today. 45 still have nothing, including Ps 77.** Sacks will always be uneven, so the bundle section must stay optional.

**What it would take**: `scripts/build_sacks_index.py` (links + aligned liturgical commentary + Hebrew search, per psalm, to a gitignored cache); `SacksLibrarian` reads the cache and emits **whole paragraphs** (a segment and, when needed, its neighbors) rather than ±1,000-character windows, labelled by book and by which liturgical setting the comment belongs to; the biography cut to one sentence; `sacks_on_psalms.json` deleted. $0 to build; the bundle grows only on the psalms he wrote about.

### 3.4 Smaller things worth having

- **Translations for crux-spotting.** Sefaria's Psalms now has JPS 1917, JPS 1985, the **2023 JPS Gender-Sensitive Edition**, the **Koren Jerusalem Bible**, Silverstein's Rashi-based *Rashi Ketuvim*, Feuer's *Jerusalem Anthology*, Arnold **Ehrlich**'s German, Bernfeld's German, Cylkow's Polish, **Yehoash's Yiddish**, Chouraqui's French and Zamenhof's Esperanto. A per-verse note of where the Jewish translations **disagree** is a cheap, deterministic crux detector (e.g. 77:11 splits them). Low cost, modest value, and best as a micro-analyst input rather than writer prose.
- **Philo** (33 links on 23 psalms, e.g. *On Husbandry* on Ps 23's shepherd) comes free with §3.1's harvest.
- **The earliest Hebrew lexicography** (Menachem ibn Saruq's *Machberet*, Radak's *Sefer HaShorashim*) is linked word by word (Ps 77: 15 and 31 links). Niche; only for rare words.

### 3.5 Looked at and not recommended

- **Steinsaltz on Psalms** (Hebrew + English, 2015): a running paraphrase with interpolations, e.g. 77:20 *"Your way was through the Red Sea … Your footprints left no trace. When the splitting of the sea was over, the waters returned …"*. That is exactly the Metzudat David genre the S373 corpus measurement retired (cited at 10% of supply). The text is **"Copyright: Steinsaltz Center"**, and his per-psalm preface is one sentence (Ps 77: 176 characters). It is "another commentator similar to ones we have".
- **Topics**: 2–15 tags per psalm (Ps 77: *the Exodus*, *suffering*), mostly user- or Aspaklaria-generated. Nothing a writer can use.
- **Source sheets** (Ps 77: 53; Ps 23: 209): educators' collections, variable quality. Useful only as a reception signal (they are how Tikkun HaKlali showed up); not as dossier text.
- **Manuscripts**: Leningrad Codex page images (Ps 77 = folio 381r). A possible illustration for the DOCX, not an insight.
- **Web pages**: the site's "web pages" panel (TheTorah.com, etc.) is **not exposed** by the public API any more (`/api/webpages/…` 404s; `/api/related` returns no `webpages` key).
- **The midrash anthologies** (Yalkut Shimoni, Ein Yaakov, Sekhel Tov, Lekach Tov, Otzar Midrashim): they repeat the classical midrashim; drop them, or use them only when they are the sole witness.
- **Sefaria's MCP server as a live tool for the writer**: tool loops re-send context every round (S386 measured what that costs); pre-fetch and cache is this pipeline's pattern. It might suit an interactive `converse_with_editor` session.

---

## 4. Hygiene found along the way

1. **Unpinned versions.** The v1 default English for Psalms is now *THE JPS TANAKH: Gender-Sensitive Edition* (2023); Rashi's default is Judaica Press. `sefaria_client` and `commentary_librarian` never name a version, so a `tanakh.db` rebuild or a Sefaria default change alters our text silently. Fix: v3 `?version=english|<title>` with the titles held in one constant.
2. **The commentary librarian.** Today it makes 11 × verses requests (Ps 77: 231), with a 10 s timeout and no retry, and a failure returns `None`, so the entry silently disappears (S387: Ibn Ezra 77:9). Fix: fetch each commentator's whole chapter once (`/api/v3/texts/Rashi_on_Psalms.77`: 11 requests per psalm), retry with backoff, cache per psalm, and log a missing entry as a WARNING with the verse.
3. **`sacks_on_psalms.json`** is 7 MB of raw API payload in git; 11 entries have no snippet. It goes away with §3.3.
4. **The Sacks biography** (2,243 characters) rides every bundle that has a Sacks section; S265 already made the same cut for the commentators' biographies.
5. **FIXED THIS SESSION: the methods page's Sacks count.** The author noticed Ps 77's guide says *"Rabbi Jonathan Sacks References Reviewed: 4"*, but Ps 77 has no Sacks excerpt (the file has 0 entries, and Sefaria has 0 links and 0 liturgical comments). On a `--skip-micro` run the number comes from `_parse_research_stats_from_markdown`, and that function, copied into five runners, counted **every** "Rabbi Sacks" / "Jonathan Sacks" string anywhere in the bundle once "Rabbi Jonathan Sacks" appeared anywhere: the biography, the Research Summary's own "Rabbi Sacks references: 0" line, an echoes candidate. It was wrong in both directions: 4 for 0 on Ps 77, **9 for 10** on Ps 23. Now `sacks_librarian.count_references_in_bundle` counts the `#### Reference N:` entries inside the `## Rabbi Jonathan Sacks on Psalm N` section, and all five runners call it (3 tests in `tests/test_methods_page.py`). **Ps 77's existing guide is not re-rendered** (its files are on the author's machine): set `research.sacks_references_count` to 0 in `output/psalm_77/psalm_077_pipeline_stats.json`, then `python scripts/run_docx_only.py 77 --pdf`.

---

## 5a. A fair comparison (the author asked whether historical runs can serve as the baseline)

**No.** Neither psalm's existing guide is a fair baseline:

- **Ps 77**: the current guide (S389) was written from **S387's synthesis discovery, cut off at 14 observations** by the old 64K cap and never re-run (S388's complete 31-observation run was an experiment, not used). Its bundle has **uncurated figurative material** (S387's curator phase 2 timed out), is **missing Ibn Ezra 77:9**, and its micro research carries the **lemma-based false "LXX reading" of 77:2**. Its writer had **no LXX line** (added S390).
- **Ps 76**: its synthesis discovery (S383, Opus 5.5, 46K tokens) is **complete**, so this is the cleaner one. But its bundle **predates S384's concordance fixes and the shared-vocabulary radar**, its echoes are **legacy**, its writer had **no LXX line**, and its forest-writer guides were essay-prompt trials (K / new / F).
- Run to run, the writer varies (S372, S386), so any one historical guide is one draw.

**Design: paired fresh arms, everything identical except the new sections.**
1. Inputs fixed once per psalm: macro reused, echoes reused, research bundle as it stands. (Optionally refresh micro + bundle on today's code first, ≈ $1–2, so the test reflects the current pipeline; both arms share it either way.)
2. **Arm A**: synthesis discovery + forest writer on those inputs. **Arm B**: the same plus `## Rabbinic Reception` (the rules above) and the `**Targum:**` line per verse, then synthesis discovery + writer. SD runs in both arms because it reads the same dossier and it is where the original finds came from (S383).
3. Cost per arm ≈ $3.5–4 (Ps 76 measured: SD $1.64, writer $1.93 in S383; the two-call writer $2.25 in S386). **Ps 76 both arms ≈ $7–8**; Ps 77 ≈ $8–9 (21 verses). Copy edit + DOCX +$0.5 per arm if the author wants to read finished guides.
4. Read-outs: the author's reading; **$0 accuracy check** of every rabbinic / Targum / midrash claim in both arms against the cached Sefaria texts (the Ps 27 / Ps 76 error class); counts of reception material used; and whether SD's observations change.
5. Side benefit: arm A is also the overdue **SD → writer shared-cache check** (`NEXT_SESSION_PROMPT_session_391.md` §2).
6. Caveat: B changes two things (reception + Targum). Separating them would take a third arm; the Targum is small and low-risk, so it rides with B.

The runs must happen on the author's machine: `output/` (bundles, SD files) is not in the cloud container.

## 6. BUILT (same session): what exists now, and how to run the Ps 76 A/B

The author: *"yes, go ahead with 1,400"*; Ps 76 only, arm A = today's pipeline (fresh bundle, synthesis, echoes, writer), arm B = the same plus the new Sefaria material, echoes shared.

| What | Where | Default |
|---|---|---|
| **Commentary fetch, hardened**: one request per commentator per PSALM (was per verse: 231 on Ps 77), 4 attempts with backoff, 30 s timeout, versions PINNED (`PINNED_VERSIONS`, = Sefaria's defaults on 2026-10-01), disk cache `data/sefaria_cache/commentary/`, a lost commentator logged as a WARNING. Partial English (community / Feuer / a Radak translation) merged comment by comment, exactly as the old per-verse endpoint served it. **Verified identical to the old output on all 660 verse-commentator pairs of Pss 1, 23, 27, 76, 77.** | `src/agents/commentary_librarian.py`; `tests/test_commentary_librarian_fetch.py` (9) | ON (production) |
| **Reception section** (the §3.1a rules; 1,400 chars/verse, 40K cap) | `src/data_sources/sefaria_reception.py`; pipeline `--reception`; `tests/test_sefaria_reception.py` (14) | OFF |
| **Targum line** per verse (`**Targum:**`, `**Targum (English):**` where Sefaria has it): all 150 psalms align with the Hebrew verse numbering (0 mismatches) | `src/data_sources/targum.py`; `MasterEditor.include_targum`; pipeline `--targum`; `tests/test_targum.py` (4) | OFF |
| **`PSALMS_OUTPUT_ROOT`** relocates the writer's thinking, saved essay and telemetry (which `--output-dir` does not) | `src/utils/debug_paths.py` | unset = `output` |
| **The A/B driver** | `scripts/run_s391_reception_ab.py` | — |

Run it (on the author's machine; the bundles are there):
```bash
python scripts/run_s391_reception_ab.py 76 --dry-run     # $0: reception section (19 passages, 20.7K chars), Targum, plan, estimate
python scripts/run_s391_reception_ab.py 76               # both arms, ~$9-13; results in output/_s391_reception_ab/psalm_76/
```
The driver: copies the production macro into arm A; runs arm A as a plain pipeline subprocess (`--skip-macro`); copies A's macro, micro and research bundle (with A's fresh echoes) into arm B, **refuses to run B if its bundle would cross the 350K trim ceiling** (one-sided trimming would be a confound), then runs B with `--skip-macro --skip-micro --skip-lit-echoes --reception --targum`; backs up and restores the production echoes dossier and the `output/debug/*_psalm_76.txt` dumps; writes `README.md` (per-stage cost, both arms) and copies both DOCX/PDF to the folder's top.

### 6a. The 350K trim ceiling (the author asked whether to raise or remove it)

**Recommendation: keep it for now; revisit before Psalm 78.**
- **Its rationale is obsolete.** It was set for a 200K-token window ("~350K chars ≈ 200K tokens at 1.75:1"). Opus 5.5 has a **1M-token context, 128K output, and a flat $4/$20 with no long-context tier** (checked against the current API reference). Fit is no longer the constraint.
- **It almost never binds.** Bundles have run ~215–280K (S379, S380: none crossed it), and the S387 writer's whole inputs block for Ps 77 was 349K chars ≈ 231K tokens (≈ 1.5 chars/token, not 1.75). Raising or removing it changes nothing for the psalms done so far.
- **What it guards is cost and dilution, not fit.** Each extra 100K chars ≈ 66K tokens ≈ $0.33 per psalm in synthesis discovery's cache write plus reads, and S370–S372 measured more material producing *less* focused writing.
- **Where it will matter**: the long psalms (78 = 72 verses, 89, 104–107, 119 = 176). When it fires it drops Related Psalms first, then trims uncurated figurative material. Before Ps 78, measure those bundles (`$0`) and decide then; a ceiling that scales with verse count is the likely answer.
- **For this A/B** it must not fire on one arm only; the driver checks.

## 5. Suggested order and how to test it

| Step | What | Spend |
|---|---|---|
| 1 | **Targum** into the psalm text + fact checker (§3.2) | $0 build |
| 2 | **Hygiene**: pin versions; per-chapter commentary fetch with retry + cache (§4.1–2) | $0 |
| 3 | **Reception harvester** + cache, deterministic tier-1 section (§3.1 option a) | $0 build |
| 4 | **Sacks rebuild** (§3.3) | $0 build |
| 5 | **A/B on Ps 77** (or Ps 76, whose two-call guides are archived): reuse the bundle (`--skip-macro --skip-micro --reuse-synthesis-discovery`), swap in the new sections, run the writer with and without | ≈ $2.3 per writer arm (+ copy edit $0.5 if wanted) |
| 6 | If the writer drowns in tier 1 or ignores tier 2: build the curator (§3.1 option b) | +$0.02–0.25 per psalm |

**Things the author decides:**
1. **Scope of reception**: Talmud + classical midrash + Targum + Philo only, or also Hasidut / Kabbalah / thought (the 77:11 "the change is in the receiver" line lives there)?
2. **Deterministic or curated**: dossier size against a small curation cost.
3. **Licensing**: Talmud English is Koren/Steinsaltz (CC-BY-NC); the Sacks/Koren texts are CC-BY-NC; the community translations CC0; Feuer CC-BY; Steinsaltz Tanakh all rights reserved. NC is fine for non-commercial study guides with attribution; **if the guides are ever sold, the NC material can inform the writer but should not be quoted at length.** Worth a line on the methods page either way.
4. **Test psalm** for the A/B.
