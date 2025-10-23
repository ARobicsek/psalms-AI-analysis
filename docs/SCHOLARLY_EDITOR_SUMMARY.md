Psalms Reader’s Guide: 
How it works
October 21, 2025
How the System Works
The aim of this process is to produce a ‘reader’s guide’ to each chapter of Psalms, informed by linguistic tools, contemporary scholarship, modern methods of poetic analysis of Biblical verse, traditional Jewish commentators and searchable collections of comparative language (concordance for words and phrases, and concordance for figurative language). This is accomplished using four Large Language Model (LLM) agents working in series, aided by digital ‘librarians’ with research tool access.
Stage 1: First Agent - Macro Analysis
A Large Language Model (Claude Sonnet 4.5) is provided with a chapter of Psalms including Masoretic Text in Hebrew; a Jewish Publication Society English (1985) translation; the Septuagint (LXX) Greek translation; Ugaritic poetry parallels (where available) and detailed instructions on frameworks for reading Biblical poetry. It is instructed to identify a thesis about the psalm’s central message/argument, structure, ritual usage and key poetic devices. It is also instructed to generate 5-10 questions that need to be answered to understand the psalm.
Stage 2: Second Agent - Micro Analysis
The same information, as well as the output of the First Agent is passed to the Second Agent (Claude Sonnet 4.5). It is instructed to do a close verse-by-verse reading of the psalm, generating 5-10 additional questions. Based on its questions and the work of the First Agent, it generates a set of requests for the ‘librarians’. 
It provides the librarians with four types of requests:
•	words to look up in the Klein/BDB biblical dictionaries
•	words and phrases to look up in a whole-Tanakh concordance (the librarians generate up to 66 variations on each word for their search)
•	commentaries of the traditional Jewish exegetes (Rashi, Ibn Ezra, Radak, Metzudat David, Malbim, Meiri) to a given verse
•	specific figurative vehicles to search for across Psalms and the Pentateuch (e.g. search for other examples of bird-of-prey metaphors). This search is done using a unique ‘figurative language concordance’ that was built separately.
The Second Agent also generates scholarly phonetic transcriptions of each verse using reconstructed Biblical pronunciations and syllabic breakdowns (following Gesenius’s Hebrew Grammar, Lambdin’s Introduction to Biblical Hebrew, Khan’s A Short Introduction to the Tiberian Masoretic Bible, etc.)
Stage 3: Research Assembly
Specialized librarian components retrieve dictionary definitions, concordance evidence, figurative language examples, and traditional commentaries. This stage operates automatically without using language models, ensuring consistent and comprehensive data collection.
Stage 4: Third Agent – Synthesis Writer
This agent (Claude Sonnet 4.5) receives the output of the prior three stages and is instructed to create a coherent commentary. It drafts an introductory essay (800–1200 words) and detailed verse-by-verse commentary (150–400 words per verse), integrating all the research materials into a unified scholarly narrative.
Stage 5: Fourth Agent - Editorial Review
This agent (GPT-5) receives the output of all the prior stages, typically amounting to 150,000 characters or more. It checks the work of the Synthesis writer for factual accuracy, verifies that all technical terms are defined, and ensures the writing is accessible to educated readers while maintaining scholarly rigor. It usually performs a thorough rewrite of both the introductory essay and the verse-by-verse commentaries, substantially sharpening them and adding insight.
Sources Available to the System
The system has access to a comprehensive collection of scholarly resources:
Textual Sources
•	Complete Hebrew text with all diacritical marks preserved
•	English translation for accessibility
•	Septuagint (LXX) Greek text for comparison
•	Phonetic transcriptions using reconstructed Biblical Hebrew pronunciation
Lexical Resources
•	Brown-Driver-Briggs Hebrew Dictionary (BDB)
•	Klein Hebrew Dictionary
•	Comprehensive Hebrew concordance with morphological variations
Figurative Language Database
•	Custom database covering all Psalms and the Pentateuch
•	5,000+ figurative language instances with target (who or what the figuration is about), vehicle (what the target is likened to) and ground (what characteristic of the target is illuminated by the vehicle), and hierarchical tags for each (e.g. vehicle = foxanimalnature).
Traditional Commentaries
•	Rashi (11th century)
•	Ibn Ezra (12th century)
•	Radak (13th century)
•	Metzudat David (17th century)
•	Malbim (19th century)
•	Meiri (13th century)
•	Torah Temimah (19th-20th century)
Comparative Materials
•	Ugaritic parallels from ancient Near Eastern literature
•	Analytical framework for psalm interpretation
•	Psalm function database with genre characteristics
Examples of Analysis

Psalms 1:1
אַ֥שְֽׁרֵי־הָאִ֗ישׁ אֲשֶׁ֤ר ׀ לֹ֥א הָלַךְ֮ בַּעֲצַ֢ת רְשָׁ֫עִ֥ים וּבְדֶ֣רֶךְ חַ֭טָּאִים לֹ֥א עָמָ֑ד וּבְמוֹשַׁ֥ב לֵ֝צִ֗ים לֹ֣א יָשָֽׁב׃
Happy is the man who has not followed the counsel of the wicked,
or taken the path of sinners,
or joined the company of the insolent;
Two sound-level cues deserve notice. First, the triple lo’ gives the line its spine and creates a cadence you can feel in the mouth. Second, the clustering of sibilants (š, s) in “ba‘atsat resha‘im... uvmoshav letsim” hisses with the air of whispered counsel—an instance of Hebrew poetry’s love of sound echoing sense.
Psalms 1: 2
כִּ֤י אִ֥ם־בְּתוֹרַ֥ת ה׳ חֶ֫פְצ֥וֹ וּֽבְתוֹרָת֥וֹ יֶהְגֶּ֗ה יוֹמָ֥ם וָלָֽיְלָה׃
rather, the teaching of the LORD is his delight,
and he studies that teaching day and night.
The verb “meditates,” yehgeh, is onomatopoetic: it can describe a lion’s low growl (Isaiah 31:4) or the murmuring of the heart (Proverbs 15:28). The psalmist imagines a person who mouths Scripture day and night—a merism, the pairing of opposites to suggest wholeness.
Psalms 1:3 
וְֽהָיָ֗ה כְּעֵץ֮ שָׁת֢וּל עַֽל־פַּלְגֵ֫י־מָ֥יִם אֲשֶׁ֤ר פִּרְי֨וֹ ׀ יִתֵּ֬ן בְּעִתּ֗וֹ וְעָלֵ֥הוּ לֹֽא־יִבּ֑וֹל וְכֹ֖ל אֲשֶׁר־יַעֲשֶׂ֣ה יַצְלִֽיחַ׃
He is like a tree planted beside streams of water,
which yields its fruit in season,
whose foliage never fades,
and whatever it produces thrives.
…the righteous “is like a tree transplanted (shatul) by channels of water (palgei mayim).” Two technicalities matter. First, the tree is not wild; it is set by intention. The passive participle shatul points to a careful gardener. Divine agency stands behind the flourishing that human choice makes possible. Second, palgei mayim are “divisions” of water—irrigation channels or runnels, not a lone river. This is cultivation as much as providence.
Psalms 1:4 
לֹא־כֵ֥ן הָרְשָׁעִ֑ים כִּ֥י אִם־כַּ֝מֹּ֗ץ אֲֽשֶׁר־תִּדְּפֶ֥נּוּ רֽוּחַ׃
Not so the wicked;
rather, they are like chaff that wind blows away.
The chaff comparison is a stock figure for worthless power. Psalm 35:5 prays, “Let them be like chaff before the wind,” and Hosea 13:3 piles up ephemera: “like morning fog... like chaff swirling from the threshing floor.” Isaiah 41:15–16 imagines Zion threshing mountains, reducing enemies to chaff driven by the wind. Psalm 1’s use is in line with this pattern, but its rhetoric is distinctive. It devotes its descriptive energy to the righteous. The dismissal of the wicked is brisk, almost offhand. The imbalance is the point: one life is heavy and rooted, the other light and scatterable.
Psalms 2: 1
לָ֭מָּה רָגְשׁ֣וּ גוֹיִ֑ם וּ֝לְאֻמִּ֗ים יֶהְגּוּ־רִֽיק׃
Why do nations assemble,
and peoples plot vain things;
The verb for “mutter/plot,” hāgāh, is a hinge between Psalm 1 and Psalm 2. The righteous person “mutters” Torah day and night (Psalm 1:2), while the nations “mutter” empty things (Psalm 2:1).
Psalms 2:9
תְּ֭רֹעֵם בְּשֵׁ֣בֶט בַּרְזֶ֑ל כִּכְלִ֖י יוֹצֵ֣ר תְּנַפְּצֵֽם׃
You can smash them with an iron mace,
shatter them like potter’s ware.
“You shall tĕrō‘ēm with an iron rod; like a potter’s vessel you shall shatter them.” Two interpretive tracks meet here. The MT (Masoretic Text) reads the verb from rā‘a‘ (“to break”), yielding a violent image, confirmed by the second colon’s tĕnappṣēm (“shatter”). The LXX reads “shepherd” (poimaineis)—hearing a different homograph (rā‘āh, “to shepherd”). Each has biblical credentials. The “potter’s vessel” simile (Jeremiah 19:1–11) underscores fragility; a clay jar’s ruin is quick and irreparable. Iron, by contrast, signals unbending strength (Deuteronomy 28:48’s “iron yoke”). If the MT is right, verse 9 is a stark judgment oracle. If the LXX, it is severe pastoral authority—still iron, but rule rather than ruin. The figurative database shows pottery imagery recurs to mark vulnerability; Psalm 2 applies it to nations who imagined themselves granite. The juxtaposition—iron against clay—smashes the rebellion’s self-estimate.
Psalms 2:11
עִבְד֣וּ אֶת־ה׳ בְּיִרְאָ֑ה וְ֝גִ֗ילוּ בִּרְעָדָֽה׃
Serve the LORD in awe;
tremble with fright,
“Serve the LORD with fear; rejoice with trembling.”…The paradox—joy with trembling—captures biblical piety’s double vision: God is the source of delight and the one before whom we tremble. Rashi resolves it temporally—when the trembling comes, you will rejoice if you have served. Meiri hears it devotionally: be glad precisely in what makes you tremble, because it is God’s will. The collocation is rare, which makes it memorable; it resists flattening piety into either sentimentality or terror.
Acknowledgments
•	Hebrew, JPS, BDB/Klein, traditional commentaries: Sefaria.org API
•	LXX: Bolls.life API
•	All other sources were developed in-house
•	With gratitude to my teachers…

© Ari Robicsek 2025
