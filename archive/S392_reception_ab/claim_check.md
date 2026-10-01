# Psalm 76 A/B: rabbinic-citation check ($0)

Scope: every citation in either guide (`*/psalm_76/psalm_076_print_ready.md`, after the copy editor) of the Talmud, Mishnah,
Tosefta, minor tractates, midrash, Targum, Hasidic or practical-kabbalah works, including those reported through a
commentator ("the Alshich, citing a midrash"). Out of scope: the medieval commentators' own readings, piyyut and prayer-book
claims, literary echoes. Checked against `data/sefaria_cache/reception/psalm_076.json`, `…/targum/psalm_076.json`,
the commentary entries in the research bundle, Sefaria (Onkelos Deut 32:24) and Hebrew Wikisource (שמוש תהלים/עו).

| | Arm A (current pipeline) | Arm B (+ reception + Targum) |
|---|---|---|
| Citations checked | 14 | 21 |
| Right | 11 | 20 |
| Wrong | **2** | 1 (minor) |
| Unverifiable | 1 | 0 |

## Arm A: the two errors

1. **The Targum on v. 5 (introduction).** *"The Aramaic Targum, as the Alshich reports, had already heard the second word
   inside the first and translated 'You are fearsome.'"* The Targum reads **נְהִיר דְחִיל אַתְּ**, "shining, fearsome are
   You": it keeps the light AND adds the fear. The guide repeats the Alshich faithfully (Romemot El 76:5: *"כדעת המתרגם
   שתרגם דחיל את"*), but the Alshich quotes only half the Targum. This is the error the S385 guide made.
2. **The Talmud on v. 9 (introduction).** *"The Talmud records that Hezekiah, the king of the Assyrian siege, found the pair
   puzzling."* The speaker is the amora **Ḥizkiyya** (Avodah Zarah 3a, Shabbat 88a), not King Hezekiah. The writer's only
   source was the Chida's *"אמר חזקיה"*, and the psalm's Sennacherib setting suggested the king. Session 386 found the same
   error. It survived the copy editor (no fact check ran).

Unverifiable: *"Later manuals extend the psalm's use to travelers facing attackers"* (the bundle's deep research mentions
Selig's "violent mobs"; not checked against a source).

Right (11): the Talmud's answer and the Sinai setting; Rashi's Mishnaic term for a knife-nick; the Alshich's midrash on
v. 2 (Midrash Tehillim 76:1 + Eikhah Rabbah, as he gives them); the Chida's *"I kindled a fire in Zion"* (Bava Kamma,
ch. HaKoness); Radak's Shem/Abraham midrash (= Bereshit Rabbah 56:10); the Chida citing *Migdal David* on יראה + שלם;
the Alshich's wrath-on-wood-and-stones saying; the Alshich's בַּעַל חֵמָה midrash; the Chida citing Mahari HaKohen;
Rashi via Onkelos on רֶשֶׁף (Onkelos: וַאֲכוּלֵי עוּף); Shimush Tehillim, "to be saved from fire and water".

## Arm B: the one error

1. **The Jerusalem Talmud on v. 11 (introduction).** *"Two rabbis argue over which half of verse 11 belongs to this world
   and which to the world to come, and a third remarks that the halves could just as well be swapped."* In Maasrot 3:4
   R. Abba bar Kahana assigns the halves, and **R. Zeira, one of the two**, proposes the swap; the third, R. Levi, gives
   another reading. The verse-11 note tells the same exchange correctly, line by line.

Right (20): the Yerushalmi exchange in the v. 11 note (R. Zeira's סִיפְרֵי קִיסְמֵי, the challenge, the swap, R. Levi, the
verdict הִיא הָפְכָה וְהִיא מְהַפְּכָה); **the Targum on v. 5 as נְהִיר דְחִיל, "shining, fearsome"** (the error arm A made);
**Ḥizkiyya named correctly** (the other error arm A made), his answer, and the creation-conditional-on-Torah story (AZ 3a,
Shabbat 88a); Soferim 19:2 (Sukkot, quoted exactly); Midrash Tehillim on v. 2; Abraham/Shem and Yerushalayim (Shem =
Melchizedek, as Midrash Tehillim 76:2 says); Tosefta Berakhot 1:16 (simplified: the Tosefta draws the forgiveness from
Ps 68:17); Bereshit Rabbah 56:10, God's booth and prayer; Rashi via Onkelos; Tanchuma Shelach (Moses and Aaron slack,
Caleb on the bench); Midrash Aggadah on Baal-Peor (Moses' hands slackened, the holy spirit cries out, Pinchas rises);
Shemot Rabbah 18:9; Pesikta de-Rav Kahana 12:6; Likkutei HaPardes on the Kaddish; Rashi and R. Eleazar the Gaon;
the Alshich's בַּעַל חֵמָה midrash; Vayikra Rabbah 37:1 / Y. Nedarim 1:1 on vowing (R. Meir *for* vow-and-pay, R. Judah
against; the Bavli swaps the two, so the citation matters); the Alshich's wood-and-stones reading; Shimush Tehillim.

## What arm B used

- **Reception section: 13 of the 19 passages** reached the guide (Tosefta Berakhot, Y. Maasrot, Y. Nedarim, Avodah Zarah
  3a, Soferim, Midrash Tehillim 76:1, Bereshit Rabbah 56:10, Tanchuma Shelach, Shemot Rabbah, Pesikta de-Rav Kahana,
  Vayikra Rabbah, Likkutei HaPardes, Midrash Aggadah on Numbers); Midrash Tehillim 76:2 possibly (its content overlaps
  Bereshit Rabbah). **Not used**: the Mekhilta, the Shelah, Tanchuma Beshalach, Midrash Aggadah on Genesis, Yismach Moshe.
- **Targum: used once**, at v. 5, and that is where it corrected arm A's error.
- **Synthesis discovery: 22 observations vs 15** (B's mention Pesikta, Soferim, Midrash Aggadah; A's only the Talmud and
  Targum). N = 1 per arm.
- The rabbinic material went in without lengthening the guide (B 8,845 words, A 9,094).

## Caveat

N = 1 per arm. Arm A's two errors are of a kind that recurs (S385, S386), but a second arm-A run might not repeat them.
The handoff's next step is the author's own reading of both guides.
