#!/usr/bin/env python3
"""Create a comprehensive CSV of biblical themes for thematic parallel search."""

import csv
from pathlib import Path

# Comprehensive biblical theme hierarchy
COMPREHENSIVE_THEMES = {
    # CREATION & PRIMEVAL HISTORY
    "Creation & Primeval History": {
        "Cosmic Creation": [
            ("Genesis 1:1-2:3", "Six days of creation"),
            ("Genesis 2:4-25", "Adam and Eve narrative"),
            ("John 1:1-3", "Logos as creator"),
            ("Psalm 33:6-9", "Word creates"),
            ("Psalm 104", "Creation psalm"),
            ("Proverbs 8:22-31", "Wisdom in creation"),
            ("Job 38-41", "God speeches on creation"),
            ("Isaiah 45:18", "Creator's purpose"),
            ("Colossians 1:16-17", "All things through Him"),
            ("Hebrews 11:3", "Faith understands creation")
        ],
        "Human Creation": [
            ("Genesis 1:26-27", "Image of God"),
            ("Genesis 2:7", "Breath of life"),
            ("Genesis 2:18-25", "Woman created"),
            ("Psalm 8", "Human dignity"),
            ("Psalm 139:13-16", "Knit in womb"),
            ("Sirach 17", "Human nature"),
            ("Wisdom 2:23", "Created for immortality"),
            ("1 Corinthians 15:45", "Adam as living soul")
        ],
        "The Garden": [
            ("Genesis 2:8-17", "Eden geography"),
            ("Genesis 2:16-17", "Tree command"),
            ("Genesis 3", "The Fall"),
            ("Genesis 3:15", "Protoevangelium"),
            ("Ezekiel 28:11-19", "Eden imagery"),
            ("Revelation 22:1-5", "New Eden")
        ],
        "The Fall": [
            ("Genesis 3", "First sin"),
            ("Genesis 3:1-6", "Temptation narrative"),
            ("Genesis 3:7-13", "Consequences"),
            ("Genesis 3:14-19", "Curses"),
            ("Genesis 3:22-24", "Exile from Eden"),
            ("Romans 5:12-21", "Sin through Adam"),
            ("1 Corinthians 15:21-22", "Adam/Christ contrast")
        ],
        "Cain & Abel": [
            ("Genesis 4:1-8", "First murder"),
            ("Genesis 4:9-16", "Curse of Cain"),
            ("Genesis 4:17-26", "Cain's descendants"),
            ("Hebrews 11:4", "Abel's faith"),
            ("1 John 3:12", "Cain's evil"),
            ("Jude 1:11", "Way of Cain")
        ],
        "Patriarchs Before Flood": [
            ("Genesis 5", "Genealogies"),
            ("Genesis 5:21-24", "Enoch translation"),
            ("Genesis 5:24", "Enoch walked with God"),
            ("Genesis 6:1-4", "Sons of God"),
            ("Hebrews 11:5", "Enoch's faith"),
            ("Jude 1:14-15", "Enoch's prophecy")
        ],
        "The Flood": [
            ("Genesis 6:5-22", "Decision to flood"),
            ("Genesis 7", "Flood narrative"),
            ("Genesis 8", "Waters recede"),
            ("Genesis 9:1-7", "Noahic covenant"),
            ("Genesis 9:8-17", "Rainbow covenant"),
            ("1 Peter 3:18-22", "Noah as salvation type"),
            ("2 Peter 2:5", "Noah preserved"),
            ("Matthew 24:37-39", "Days of Noah")
        ],
        "Post-Flood History": [
            ("Genesis 9:18-29", "Noah's vineyard"),
            ("Genesis 10", "Table of nations"),
            ("Genesis 11:1-9", "Tower of Babel"),
            ("Genesis 11:10-32", "Shem to Terah")
        ]
    },

    # PATRIARCHS & MATRIARCHS
    "Patriarchs & Matriarchs": {
        "Abraham's Call": [
            ("Genesis 12:1-3", "Call and promises"),
            ("Genesis 12:4-9", "Journey to Canaan"),
            ("Genesis 12:10-20", "Egypt sojourn"),
            ("Acts 7:2-5", "Stephen on Abraham"),
            ("Romans 4", "Abraham's faith"),
            ("Galatians 3:6-9", "Blessing of Abraham"),
            ("Hebrews 11:8-10", "Faith journey")
        ],
        "Abraham & Lot": [
            ("Genesis 13", "Separation"),
            ("Genesis 14", "Rescue of Lot"),
            ("Genesis 18-19", "Sodom intercession"),
            ("Genesis 19", "Lot's escape"),
            ("Luke 17:28-32", "Days of Lot"),
            ("2 Peter 2:7-8", "Righteous Lot")
        ],
        "Abrahamic Covenant": [
            ("Genesis 15", "Covenant ceremony"),
            ("Genesis 17", "Name change & circumcision"),
            ("Genesis 22", "Binding of Isaac"),
            ("Romans 4", "Covenant faith"),
            ("Galatians 3-4", "Covenant fulfillment"),
            ("Hebrews 6:13-20", "Covenant oath")
        ],
        "Sarah & Hagar": [
            ("Genesis 16", "Hagar and Ishmael"),
            ("Genesis 18", "Sarah's laughter"),
            ("Genesis 20", "Sarah as sister"),
            ("Genesis 21", "Ishmael's birth"),
            ("Galatians 4:21-31", "Hagar/Sarah allegory"),
            ("1 Peter 3:6", "Sarah's obedience")
        ],
        "Isaac": [
            ("Genesis 21:1-7", "Isaac's birth"),
            ("Genesis 22", "Binding"),
            ("Genesis 24", "Marriage to Rebekah"),
            ("Genesis 25:21-28", "Jacob/Esau birth"),
            ("Genesis 26", "Isaac's narrative"),
            ("Romans 9:7-9", "Isaac as promised child"),
            ("Hebrews 11:17-19", "Isaac's near-sacrifice")
        ],
        "Jacob": [
            ("Genesis 25:29-34", "Birthright sold"),
            ("Genesis 27", "Blessing deception"),
            ("Genesis 28", "Jacob's ladder"),
            ("Genesis 29-30", "Marriages and children"),
            ("Genesis 32", "Wrestles with God"),
            ("Genesis 33", "Reconciliation with Esau"),
            ("Genesis 35", "Return to Bethel"),
            ("Genesis 37-50", "Joseph connection"),
            ("Romans 9:10-13", "Jacob's election"),
            ("Hebrews 11:20-21", "Jacob's blessings")
        ],
        "Joseph": [
            ("Genesis 37", "Dreams and betrayal"),
            ("Genesis 39", "Potiphar's house"),
            ("Genesis 40", "Prison interpretations"),
            ("Genesis 41", "Rise to power"),
            ("Genesis 42-45", "Brothers' reconciliation"),
            ("Genesis 46-47", "Family to Egypt"),
            ("Genesis 50", "Death and legacy"),
            ("Acts 7:9-16", "Joseph in Stephen's speech"),
            ("Hebrews 11:22", "Joseph's faith")
        ]
    },

    # EXODUS & WILDERNESS
    "Exodus & Wilderness": {
        "Israel in Egypt": [
            ("Exodus 1", "Oppression begins"),
            ("Exodus 2", "Moses' birth"),
            ("Exodus 2:11-25", "Moses flees"),
            ("Exodus 3-4", "Burning bush"),
            ("Acts 7:17-36", "Stephen on Moses"),
            ("Hebrews 11:23-29", "Parents' and Moses' faith")
        ],
        "The Plagues": [
            ("Exodus 7:14-12:36", "Ten plagues"),
            ("Psalm 78:42-51", "Plagues in Psalm"),
            ("Psalm 105:26-36", "Plagues in Psalm"),
            ("Psalm 135:8-9", "Plagues in Psalm"),
            ("Wisdom 16-19", "Philosophy of plagues"),
            ("Revelation 8-16", "Plague imagery")
        ],
        "Passover": [
            ("Exodus 12", "Passover institution"),
            ("Exodus 13", "Unleavened bread"),
            ("Numbers 9", "Second Passover"),
            ("Deuteronomy 16", "Passover law"),
            ("Joshua 5", "Canaan Passover"),
            ("2 Kings 23", "Josiah's Passover"),
            ("2 Chronicles 30", "Hezekiah's Passover"),
            ("Ezra 6", "Return Passover"),
            ("Matthew 26", "Last Supper"),
            ("1 Corinthians 5:7", "Christ our Passover"),
            ("Hebrews 11:28", "Faith kept Passover")
        ],
        "Crossing the Sea": [
            ("Exodus 14", "Red Sea crossing"),
            ("Exodus 15", "Song of the sea"),
            ("Numbers 33:8", "Wilderness route"),
            ("Psalm 106:7-12", "Sea crossing"),
            ("Psalm 136:13-16", "Sea crossing"),
            ("Nehemiah 9:9-11", "Sea crossing"),
            ("Acts 7:36", "Stephen on Red Sea"),
            ("1 Corinthians 10:1-2", "Baptized into Moses"),
            ("Hebrews 11:29", "Faith crossed sea")
        ],
        "Wilderness Journey": [
            ("Numbers 10-21", "Wilderness wanderings"),
            ("Deuteronomy 1-3", "Wilderness review"),
            ("Psalm 78:12-16", "Wilderness provision"),
            ("Psalm 95:7-11", "Wilderness testing"),
            ("Psalm 107:4-9", "Wilderness wandering"),
            ("Hebrews 3-4", "Rest and wilderness"),
            ("1 Corinthians 10:1-13", "Wilderness examples")
        ],
        "Manna & Water": [
            ("Exodus 16", "Manna from heaven"),
            ("Exodus 17", "Water from rock"),
            ("Numbers 20", "Second water"),
            ("Deuteronomy 8", "Wilderness provision"),
            ("Nehemiah 9:15-21", "God's provision"),
            ("Psalm 78:23-31", "Manna in Psalm"),
            ("John 6:31-35", "Manna symbolism"),
            ("1 Corinthians 10:3-4", "Spiritual food/drink")
        ],
        "Sinai Covenant": [
            ("Exodus 19-24", "Covenant establishment"),
            ("Deuteronomy 5", "Ten Commandments"),
            ("Deuteronomy 28", "Blessings/curses"),
            ("Jeremiah 31:31-34", "New covenant"),
            ("Hebrews 8-10", "Better covenant"),
            ("2 Corinthians 3", "Glorious ministry"),
            ("Galatians 3-4", "Covenant purpose")
        ],
        "The Tabernacle": [
            ("Exodus 25-31", "Instructions"),
            ("Exodus 35-40", "Construction"),
            ("Leviticus 1-7", "Sacrifices"),
            ("Leviticus 16", "Day of Atonement"),
            ("Numbers 1-10", "Organization"),
            ("Hebrews 8-9", "Heavenly tabernacle"),
            ("Hebrews 10", "Better sacrifice"),
            ("Revelation 21-22", "New Jerusalem")
        ],
        "Wilderness Rebellion": [
            ("Numbers 13-14", "Spies and rebellion"),
            ("Numbers 16", "Korah's rebellion"),
            ("Numbers 20", "Moses strikes rock"),
            ("Numbers 21", "Bronze serpent"),
            ("Deuteronomy 1:19-46", "Rebellion review"),
            ("Psalm 78:32-41", "Wilderness testing"),
            ("Psalm 95:7-11", "Wilderness testing"),
            ("1 Corinthians 10:6-11", "Warnings"),
            ("Hebrews 3:7-19", "Wilderness rest"),
            ("Jude 1:5", "Unfaithfulness")
        ]
    },

    # CONQUEST & JUDGES
    "Conquest & Judges": {
        "Entering Canaan": [
            ("Deuteronomy 31-34", "Moses' death"),
            ("Joshua 1-5", "Jordan crossing"),
            ("Joshua 6", "Jericho falls"),
            ("Joshua 7", "Achan's sin"),
            ("Joshua 8-12", "Conquest narrative"),
            ("Hebrews 4:8", "Joshua's rest"),
            ("Acts 7:45", "Stephen on Joshua")
        ],
        "Land Distribution": [
            ("Joshua 13-22", "Tribal allotments"),
            ("Joshua 23-24", "Joshua's farewell"),
            ("Judges 1", "Incomplete conquest"),
            ("Judges 2", "Israel's failure")
        ],
        "The Judges Cycle": [
            ("Judges 2:6-23", "Judge cycle pattern"),
            ("Judges 3", "Othniel & Ehud"),
            ("Judges 4-5", "Deborah & Barak"),
            ("Judges 6-8", "Gideon"),
            ("Judges 9", "Abimelech"),
            ("Judges 10-12", "Tola, Jair, Jephthah"),
            ("Judges 13-16", "Samson"),
            ("Judges 17-21", "Epilogue"),
            ("Hebrews 11:32", "Judges in faith hall")
        ],
        "Ruth": [
            ("Ruth 1", "Naomi's return"),
            ("Ruth 2", "Gleaning with Boaz"),
            ("Ruth 3", "Midnight encounter"),
            ("Ruth 4", "Redemption & marriage"),
            ("Matthew 1:5", "Ruth in genealogy")
        ],
        "Samuel": [
            ("1 Samuel 1-3", "Hannah & Samuel"),
            ("1 Samuel 4-7", "Ark narratives"),
            ("1 Samuel 8", "Request for king"),
            ("1 Samuel 9-15", "Saul's reign"),
            ("1 Samuel 16-31", "David & Saul"),
            ("2 Samuel 1-24", "David's reign"),
            ("1 Chronicles 10-29", "Chronicler's version"),
            ("Acts 13:16-23", "Paul on Samuel")
        ]
    },

    # WISDOM LITERATURE
    "Wisdom Literature": {
        "Nature of Wisdom": [
            ("Job 28", "Where is wisdom?"),
            ("Proverbs 1:7", "Fear of Lord"),
            ("Proverbs 2", "Wisdom's value"),
            ("Proverbs 3:13-18", "Blessing of wisdom"),
            ("Proverbs 4", "Get wisdom"),
            ("Proverbs 8", "Wisdom personified"),
            ("Proverbs 9", "Wisdom's feast"),
            ("Sirach 1", "Wisdom's praise"),
            ("Sirach 24", "Wisdom's origin"),
            ("Wisdom 7-9", "Nature of wisdom"),
            ("James 1:5", "Ask for wisdom"),
            ("James 3:13-18", "Two wisdoms")
        ],
        "Suffering of Righteous": [
            ("Job 1-2", "Job's trials"),
            ("Job 3", "Lament"),
            ("Job 4-27", "Friends' dialogues"),
            ("Job 28", "Wisdom chapter"),
            ("Job 29-31", "Job's defense"),
            ("Job 32-37", "Elihu"),
            ("Job 38-41", "God speaks"),
            ("Job 42", "Restoration"),
            ("Psalm 22", "Suffering psalm"),
            ("Psalm 44", "National suffering"),
            ("Lamentations", "Jerusalem's suffering"),
            ("Isaiah 53", "Suffering servant"),
            ("1 Peter 4:12-19", "Suffering as Christian")
        ],
        "Meaning of Life": [
            ("Ecclesiastes 1", "Vanity of life"),
            ("Ecclesiastes 2", "Pleasures futile"),
            ("Ecclesiastes 3", "Seasons of life"),
            ("Ecclesiastes 4", "Life's hardships"),
            ("Ecclesiastes 5", "Approach God"),
            ("Ecclesiastes 6", "Evils under sun"),
            ("Ecclesiastes 7", "Wisdom and folly"),
            ("Ecclesiastes 8", "Divine sovereignty"),
            ("Ecclesiastes 9", "Death and life"),
            ("Ecclesiastes 10", "Wisdom and folly"),
            ("Ecclesiastes 11", "Youth and old age"),
            ("Ecclesiastes 12", "Remember creator"),
            ("Matthew 6:19-34", "True treasures"),
            ("Philippians 4:11-13", "Contentment")
        ],
        "Marriage & Family": [
            ("Proverbs 5", "Avoid adultery"),
            ("Proverbs 6:20-35", "Adultery's cost"),
            ("Proverbs 7", "Strange woman"),
            ("Proverbs 12:4", "Virtuous wife"),
            ("Proverbs 14:1", "Wise woman"),
            ("Proverbs 18:22", "Find good wife"),
            ("Proverbs 19:13-14", "Family strife"),
            ("Proverbs 20:20", "Honor parents"),
            ("Proverbs 22:6", "Train up child"),
            ("Proverbs 31", "Virtuous woman"),
            ("Song of Songs", "Marital love"),
            ("Malachi 2:14-16", "Marriage covenant"),
            ("Ephesians 5:21-33", "Marriage mystery")
        ],
        "Speech & Tongue": [
            ("Proverbs 10:19", "Few words"),
            ("Proverbs 12:18", "Healing speech"),
            ("Proverbs 13:3", "Guard mouth"),
            ("Proverbs 15:1", "Soft answer"),
            ("Proverbs 15:23", "Timely word"),
            ("Proverbs 16:24", "Pleasant words"),
            ("Proverbs 17:27-28", "Silence is wise"),
            ("Proverbs 18:13", "Listen first"),
            ("Proverbs 18:21", "Death and life"),
            ("Proverbs 20:15", "Knowledge in lips"),
            ("Proverbs 21:23", "Guard mouth and soul"),
            ("Proverbs 25:11", "Word fitly spoken"),
            ("Proverbs 26:4-5", "Fool's debate"),
            ("Proverbs 26:18-19", "Madness"),
            ("Proverbs 27:2", "Praise not self"),
            ("James 1:19", "Slow to speak"),
            ("James 3", "Taming tongue"),
            ("1 Peter 3:10", "Control tongue")
        ],
        "Wealth & Poverty": [
            ("Proverbs 10:2-4", "Wealth/poverty"),
            ("Proverbs 10:22", "Lord's blessing"),
            ("Proverbs 11:4", "Riches not profit"),
            ("Proverbs 11:24-28", "Generosity"),
            ("Proverbs 13:7-8", "Rich/poor illusions"),
            ("Proverbs 13:11", "Wealth from diligence"),
            ("Proverbs 13:22", "Inheritance to children"),
            ("Proverbs 14:20-24", "Poor"),
            ("Proverbs 15:16-17", "Better poverty"),
            ("Proverbs 16:8", "Better justice"),
            ("Proverbs 17:5", "Mocking poor"),
            ("Proverbs 18:23", "Poor petitions"),
            ("Proverbs 19:4", "Wealth's friends"),
            ("Proverbs 19:7", "Poor's family"),
            ("Proverbs 19:17", "Lend to Lord"),
            ("Proverbs 20:13", "Don't love sleep"),
            ("Proverbs 21:13", "Poor's cry"),
            ("Proverbs 21:17", "Pleasures vain"),
            ("Proverbs 22:2", "Rich/poor made"),
            ("Proverbs 22:7", "Borrower servant"),
            ("Proverbs 22:9", "Generous blessed"),
            ("Proverbs 22:16", "Oppressing poor"),
            ("Proverbs 22:22-23", "Don't exploit poor"),
            ("Proverbs 23:4-5", "Don't weary for rich"),
            ("Proverbs 24:30-34", "Lazy field"),
            ("Proverbs 28:3", "Poor oppressing"),
            ("Proverbs 28:6", "Poor integrity"),
            ("Proverbs 28:8", "Usury"),
            ("Proverbs 28:11", "Rich appears wise"),
            ("Proverbs 28:20", "Faithful blessed"),
            ("Proverbs 28:22", "Hasty rich"),
            ("Proverbs 28:27", "Giving to poor"),
            ("Proverbs 29:7", "Poor's justice"),
            ("Proverbs 29:13", "Poor/poorer"),
            ("Proverbs 30:7-9", "Contentment"),
            ("Ecclesiastes 5:10-20", "Wealth vanity"),
            ("Matthew 6:19-21", "Treasures"),
            ("Luke 12:15-21", "Rich fool"),
            ("1 Timothy 6:6-10", "Contentment"),
            ("James 1:9-11", "Boasting"),
            ("James 2:1-9", "Partiality"),
            ("James 5:1-6", "Rich condemnation")
        ]
    },

    # PSALMS & POETRY
    "Psalms & Poetry": {
        "Royal Psalms": [
            ("Psalm 2", "Coronation psalm"),
            ("Psalm 18", "David's victory"),
            ("Psalm 20", "Prayer for king"),
            ("Psalm 21", "King's triumph"),
            ("Psalm 45", "Royal wedding"),
            ("Psalm 72", "Ideal king"),
            ("Psalm 89", "Davidic covenant"),
            ("Psalm 110", "Priest-king"),
            ("Psalm 144", "King's victory")
        ],
        "Wisdom Psalms": [
            ("Psalm 1", "Two ways"),
            ("Psalm 19", "Creation and law"),
            ("Psalm 32", "Confession blessed"),
            ("Psalm 34", "Fear the Lord"),
            ("Psalm 37", "Wait for Lord"),
            ("Psalm 49", "Wealth's folly"),
            ("Psalm 73", "Problem of evil"),
            ("Psalm 78", "History lesson"),
            ("Psalm 90", "Human mortality"),
            ("Psalm 92", "Wisdom of aging"),
            ("Psalm 94", "God's wisdom"),
            ("Psalm 103", "God's mercy"),
            ("Psalm 107", "Four redemptions"),
            ("Psalm 112", "Righteous blessed"),
            ("Psalm 119", "Law's value"),
            ("Psalm 127", "Human effort vain"),
            ("Psalm 128", "Blessed home"),
            ("Psalm 133", "Brotherly love"),
            ("Psalm 139", "God's knowledge"),
            ("Psalm 145", "God's praise")
        ],
        "Lament Psalms": [
            ("Psalm 6", "Sickness lament"),
            ("Psalm 13", "How long?"),
            ("Psalm 22", "Forsaken psalm"),
            ("Psalm 30", "Past deliverance"),
            ("Psalm 31", "Persecuted"),
            ("Psalm 35", "False accusation"),
            ("Psalm 38", "Sickness"),
            ("Psalm 39", "Life's brevity"),
            ("Psalm 42-43", "Thirst for God"),
            ("Psalm 44", "National lament"),
            ("Psalm 51", "Penitential"),
            ("Psalm 55", "Betrayal"),
            ("Psalm 57", "Refuge"),
            ("Psalm 60", "Defeat"),
            ("Psalm 61", "Refuge"),
            ("Psalm 63", "Spiritual thirst"),
            ("Psalm 64", "Enemy plots"),
            ("Psalm 69", "Righteous suffering"),
            ("Psalm 70", "Urgent help"),
            ("Psalm 71", "Aged lament"),
            ("Psalm 74", "Temple destroyed"),
            ("Psalm 77", "God's silence"),
            ("Psalm 79", "Jerusalem"),
            ("Psalm 80", "Shepherd plea"),
            ("Psalm 83", "Enemies"),
            ("Psalm 85", "Restoration plea"),
            ("Psalm 86", "Needy prayer"),
            ("Psalm 88", "Dark despair"),
            ("Psalm 90", "Human frailty"),
            ("Psalm 94", "Vengeance plea"),
            ("Psalm 102", "Afflicted soul"),
            ("Psalm 109", "Imprecatory"),
            ("Psalm 120", "Distress"),
            ("Psalm 123", "Mercy plea"),
            ("Psalm 130", "Depths"),
            ("Psalm 140", "Violent men"),
            ("Psalm 141", "Protection"),
            ("Psalm 142", "Refuge"),
            ("Psalm 143", "Revival"),
            ("Psalm 144", "Struggle")
        ],
        "Thanksgiving Psalms": [
            ("Psalm 30", "Deliverance"),
            ("Psalm 40", "Answered prayer"),
            ("Psalm 66", "Praise for deliverance"),
            ("Psalm 68", "Triumph"),
            ("Psalm 75", "Thanksgiving"),
            ("Psalm 92", "Sabbath thanksgiving"),
            ("Psalm 96", "Thankful worship"),
            ("Psalm 97", "Lord reigns"),
            ("Psalm 98", "New song"),
            ("Psalm 100", "Enter gates"),
            ("Psalm 103", "Bless the Lord"),
            ("Psalm 106", "Thanksgiving with history"),
            ("Psalm 107", "Thankful redemption"),
            ("Psalm 116", "Thankful love"),
            ("Psalm 118", "Thanksgiving"),
            ("Psalm 119:1-8", "Blessing for obedience"),
            ("Psalm 124", "Deliverance thanks"),
            ("Psalm 129", "Persecution overcome"),
            ("Psalm 130", "Forgiveness thanks"),
            ("Psalm 132", "David's throne"),
            ("Psalm 136", "His love endures"),
            ("Psalm 138", "Thankful promise"),
            ("Psalm 144", "Deliverance"),
            ("Psalm 146", "Thankful praise"),
            ("Psalm 147", "Thankful rebuilding"),
            ("Psalm 149", "Victory praise")
        ],
        "Creation Psalms": [
            ("Psalm 8", "Man's place"),
            ("Psalm 19", "Creation sings"),
            ("Psalm 24", "Creation's King"),
            ("Psalm 29", "Voice in storm"),
            ("Psalm 33", "Creation by word"),
            ("Psalm 65", "Creation's bounty"),
            ("Psalm 74", "Creation power"),
            ("Psalm 89", "Creation order"),
            ("Psalm 90", "Creation limits"),
            ("Psalm 93", "Creation's majesty"),
            ("Psalm 95", "Creation's worship"),
            ("Psalm 96", "Creation rejoices"),
            ("Psalm 97", "Creation trembles"),
            ("Psalm 98", "Creation sings"),
            ("Psalm 99", "Creation's king"),
            ("Psalm 104", "Creation details"),
            ("Psalm 107", "Creation cares"),
            ("Psalm 113", "Creation's high"),
            ("Psalm 114", "Creation's power"),
            ("Psalm 136", "Creation's love"),
            ("Psalm 138", "Creation's king"),
            ("Psalm 146", "Creation's creator"),
            ("Psalm 147", "Creation's provision"),
            ("Psalm 148", "All creation praise")
        ],
        "Messianic Psalms": [
            ("Psalm 2", "Son reigns"),
            ("Psalm 8", "Son of man"),
            ("Psalm 16", "Resurrection"),
            ("Psalm 22", "Suffering"),
            ("Psalm 40", "Willings"),
            ("Psalm 41", "Betrayed"),
            ("Psalm 45", "Messiah's marriage"),
            ("Psalm 68", "Ascension"),
            ("Psalm 69", "Zeal"),
            ("Psalm 72", "Reign"),
            ("Psalm 78", "Shepherd"),
            ("Psalm 89", "Davidic throne"),
            ("Psalm 94", "Vengeance"),
            ("Psalm 95", "Rest"),
            ("Psalm 96", "Reign"),
            ("Psalm 102", "Preexistence"),
            ("Psalm 106", "Intercession"),
            ("Psalm 109", "Betrayal"),
            ("Psalm 110", "Priest-king"),
            ("Psalm 118", "Cornerstone"),
            ("Psalm 132", "Throne"),
            ("Psalm 138", "Promise"),
            ("Psalm 140", "Violent men"),
            ("Psalm 142", "Spirit")
        ]
    },

    # PROPHETS - ISAIAH
    "Prophets - Isaiah": {
        "Isaiah's Call": [
            ("Isaiah 6", "Vision and call"),
            ("Isaiah 1:1", "Historical setting"),
            ("John 12:37-41", "Isaiah's blindness"),
            ("Acts 8:26-40", "Ethiopian on Isaiah 53")
        ],
        "Judgment on Israel": [
            ("Isaiah 1", "Rebels nation"),
            ("Isaiah 2-4", "Day of Lord"),
            ("Isaiah 5", "Vineyard song"),
            ("Isaiah 7", "Immanuel sign"),
            ("Isaiah 8-9", "Assyrian threat"),
            ("Isaiah 10", "Woe to Assyria"),
            ("Isaiah 11", "Branch from Jesse"),
            ("Isaiah 12", "Thanksgiving"),
            ("Isaiah 13-23", "Oracles against nations"),
            ("Isaiah 24-27", "Apocalypse"),
            ("Isaiah 28-33", "Woes to Judah"),
            ("Isaiah 34-35", "Edom/judgment salvation"),
            ("Isaiah 36-39", "Hezekiah's reign")
        ],
        "Suffering Servant": [
            ("Isaiah 42:1-4", "First servant song"),
            ("Isaiah 49:1-6", "Second servant song"),
            ("Isaiah 50:4-9", "Third servant song"),
            ("Isaiah 52:13-53:12", "Fourth servant song"),
            ("Matthew 8:17", "Took our infirmities"),
            ("Luke 22:37", "Numbered with transgressors"),
            ("John 12:38", "Not believed"),
            ("Acts 8:32-35", "Interpretation"),
            ("Romans 10:16", "Not obeyed"),
            ("Romans 15:21", "Gentiles will hear"),
            ("1 Peter 2:21-25", "Suffering example")
        ],
        "Redemption Promise": [
            ("Isaiah 40-55", "Deutero-Isaiah"),
            ("Isaiah 40:1-11", "Comfort my people"),
            ("Isaiah 40:12-31", "Creator's majesty"),
            ("Isaiah 41", "God's servants"),
            ("Isaiah 42", "Servant and light"),
            ("Isaiah 43", "Redeemed people"),
            ("Isaiah 44", "Only God"),
            ("Isaiah 45", "Cyrus as instrument"),
            ("Isaiah 46", "Babylon's gods"),
            ("Isaiah 47", "Babylon's fall"),
            ("Isaiah 48", "Stubborn Israel"),
            ("Isaiah 49", "Servant mission"),
            ("Isaiah 50", "Servant's faith"),
            ("Isaiah 51", "Listen to me"),
            ("Isaiah 52", "Awake awake"),
            ("Isaiah 53", "Suffering servant"),
            ("Isaiah 54", "Barren woman"),
            ("Isaiah 55", "Seek the Lord")
        ],
        "Restoration Hope": [
            ("Isaiah 56-66", "Trito-Isaiah"),
            ("Isaiah 56", "All peoples welcome"),
            ("Isaiah 57", "False gods"),
            ("Isaiah 58", "True fasting"),
            ("Isaiah 59", "Sin separates"),
            ("Isaiah 60", "Glory of Zion"),
            ("Isaiah 61", "Year of Jubilee"),
            ("Isaiah 62", "Watchmen on walls"),
            ("Isaiah 63", "Divine warrior"),
            ("Isaiah 64", "Form us"),
            ("Isaiah 65-66", "New heavens")
        ]
    },

    # PROPHETS - JEREMIAH & LAMENTATIONS
    "Prophets - Jeremiah & Lamentations": {
        "Jeremiah's Call": [
            ("Jeremiah 1", "Call and commission"),
            ("Jeremiah 1:5", "Before formed"),
            ("Jeremiah 1:7-8", "Don't fear"),
            ("Jeremiah 1:10", "Overthrow nations"),
            ("Jeremiah 1:17-19", "Jerusalem's sin"),
            ("Jeremiah 20:7-9", "Decieved by Lord"),
            ("Acts 7:51-53", "Stephen on prophets")
        ],
        "Temple Sermon": [
            ("Jeremiah 7", "Temple sermon"),
            ("Jeremiah 7:1-15", "Trust in temple"),
            ("Jeremiah 7:16-20", "Don't pray"),
            ("Jeremiah 7:21-26", "Obey voice"),
            ("Jeremiah 7:30-34", "High places"),
            ("Jeremiah 26", "Temple sermon threatened")
        ],
        "Covenant & Law": [
            ("Jeremiah 11", "Broken covenant"),
            ("Jeremiah 31:31-34", "New covenant"),
            ("Jeremiah 33:20-26", "Covenant sure"),
            ("Hebrews 8-10", "Better covenant"),
            ("Luke 22:20", "New covenant")
        ],
        "False Prophets": [
            ("Jeremiah 2:8", "False prophets"),
            ("Jeremiah 5:30-31", "Terrible things"),
            ("Jeremiah 6:14", "Peace peace"),
            ("Jeremiah 14:14-16", "Lying prophets"),
            ("Jeremiah 23", "False shepherds"),
            ("Jeremiah 27-28", "Hananiah"),
            ("Jeremiah 28", "Yoke broken"),
            ("Jeremiah 29", "False dreams"),
            ("Matthew 7:15", "False prophets"),
            ("2 Peter 2", "False teachers")
        ],
        "Jerusalem's Fall": [
            ("Jeremiah 4", "Disaster from north"),
            ("Jeremiah 6", "Enemy from north"),
            ("Jeremiah 8-9", "Mourning"),
            ("Jeremiah 10", "Idols folly"),
            ("Jeremiah 12", "Why wicked prosper"),
            ("Jeremiah 13", "Linen sash"),
            ("Jeremiah 15-17", "Intercession"),
            ("Jeremiah 18", "Potter's house"),
            ("Jeremiah 19", "Broken flask"),
            ("Jeremiah 20", "Persecution"),
            ("Jeremiah 22", "Kings judged"),
            ("Jeremiah 24", "Two baskets"),
            ("Jeremiah 25", "Seventy years"),
            ("Jeremiah 34", "Covenant broken"),
            ("Jeremiah 36", "Scroll burned"),
            ("Jeremiah 37-39", "Fall and exile"),
            ("Jeremiah 52", "Jerusalem falls")
        ],
        "Lamentations": [
            ("Lamentations 1", "Jerusalem sits"),
            ("Lamentations 2", "Lord's anger"),
            ("Lamentations 3", "Hope in suffering"),
            ("Lamentations 4", "Children suffer"),
            ("Lamentations 5", "Prayer for restoration")
        ]
    },

    # PROPHETS - EZEKIEL
    "Prophets - Ezekiel": {
        "Ezekiel's Call": [
            ("Ezekiel 1", "Vision of God"),
            ("Ezekiel 2-3", "Commission"),
            ("Ezekiel 3:16-21", "Watchman"),
            ("Daniel 10:5-9", "Similar vision"),
            ("Revelation 1:12-16", "Similar vision"),
            ("Revelation 4", "Similar vision")
        ],
        "Signs & Symbols": [
            ("Ezekiel 4", "Siege sign"),
            ("Ezekiel 5", "Shaved hair"),
            ("Ezekiel 12", "Exile sign"),
            ("Ezekiel 24", "No mourning"),
            ("Hosea 12:10", "Spoke in visions"),
            ("Jeremiah 28:9", "Prophet's signs")
        ],
        "Temple Vision": [
            ("Ezekiel 8-11", "Temple abominations"),
            ("Ezekiel 8:3", "Image of jealousy"),
            ("Ezekiel 8:5", "Image at gate"),
            ("Ezekiel 8:10", "Carved images"),
            ("Ezekiel 8:14", "Tammuz"),
            ("Ezekiel 8:16", "Sun worship"),
            ("Ezekiel 9", "Mark with tau"),
            ("Ezekiel 10", "Glory departs"),
            ("Ezekiel 11", "Jerusalem's judgment")
        ],
        "Responsibility": [
            ("Ezekiel 18", "Individual responsibility"),
            ("Ezekiel 18:4", "Soul that sins"),
            ("Ezekiel 18:20", "Father/son"),
            ("Ezekiel 18:30-32", "Repentance"),
            ("Deuteronomy 24:16", "Children not die"),
            ("Jeremiah 31:29-30", "Individual sin"),
            ("Daniel 9:4-19", "Corporate confession")
        ],
        "Shepherd Kings": [
            ("Ezekiel 34", "False shepherds"),
            ("Ezekiel 34:2-4", "Self-serving"),
            ("Ezekiel 34:5-6", "Sheep scattered"),
            ("Ezekiel 34:11-16", "Lord as shepherd"),
            ("Ezekiel 34:23-24", "David as prince"),
            ("Jeremiah 23:1-8", "Righteous shepherds"),
            ("John 10", "Good shepherd"),
            ("1 Peter 2:25", "Shepherd bishop")
        ],
        "Dry Bones": [
            ("Ezekiel 37", "Valley of dry bones"),
            ("Ezekiel 37:1-14", "Life to bones"),
            ("Ezekiel 37:15-28", "Two sticks"),
            ("Romans 11:11-24", "Olive tree"),
            ("Ephesians 2:11-22", "One new man"),
            ("Revelation 11:11", "Two witnesses")
        ],
        "Gog and Magog": [
            ("Ezekiel 38-39", "Gog invasion"),
            ("Ezekiel 38:2", "Prince of Rosh"),
            ("Ezekiel 38:8-12", "End times"),
            ("Ezekiel 38:22", "God's judgment"),
            ("Ezekiel 39", "God's glory"),
            ("Revelation 20:8", "Final battle"),
            ("Revelation 20:9", "Satan's deception")
        ],
        "Temple Blueprint": [
            ("Ezekiel 40-48", "New temple"),
            ("Ezekiel 40", "Gate measurements"),
            ("Ezekiel 41", "Temple interior"),
            ("Ezekiel 42", "Priestly chambers"),
            ("Ezekiel 43", "Glory returns"),
            ("Ezekiel 44", "Priestly duties"),
            ("Ezekiel 45", "Land division"),
            ("Ezekiel 46", "Prince provisions"),
            ("Ezekiel 47", "River flows"),
            ("Ezekiel 48", "Tribal portions"),
            ("Revelation 21-22", "New Jerusalem"),
            ("Hebrews 8-9", "Heavenly sanctuary")
        ]
    },

    # PROPHETS - MINOR PROPHETS
    "Prophets - Minor Prophets": {
        "Hosea": [
            ("Hosea 1-3", "Unfaithful wife"),
            ("Hosea 1:2", "Harlot wife"),
            ("Hosea 2", "Israel unfaithful"),
            ("Hosea 3", "Restoration"),
            ("Hosea 4", "No knowledge"),
            ("Hosea 5", "Priest/king judged"),
            ("Hosea 6", "Return to Lord"),
            ("Hosea 7", "Deceitful"),
            ("Hosea 8", "Sown wind"),
            ("Hosea 9", "Exile"),
            ("Hosea 10", "False worship"),
            ("Hosea 11", "Father's love"),
            ("Hosea 12", "Jacob's struggles"),
            ("Hosea 13", "Samaria's fall"),
            ("Hosea 14", "Return"),
            ("Romans 9:25-26", "Not my people"),
            ("Romans 11:26", "Deliverer from Zion")
        ],
        "Joel": [
            ("Joel 1", "Locust plague"),
            ("Joel 2", "Day of Lord"),
            ("Joel 2:28-32", "Spirit poured"),
            ("Joel 3", "Nations judged"),
            ("Acts 2:16-21", "Pentecost fulfillment"),
            ("Romans 10:13", "Call on name")
        ],
        "Amos": [
            ("Amos 1-2", "Nations condemned"),
            ("Amos 1:3", "Syria"),
            ("Amos 1:6", "Philistia"),
            ("Amos 1:9", "Tyre"),
            ("Amos 1:11", "Edom"),
            ("Amos 1:13", "Ammon"),
            ("Amos 2:1", "Moab"),
            ("Amos 2:4", "Judah"),
            ("Amos 2:6", "Israel"),
            ("Amos 3", "Privilege brings responsibility"),
            ("Amos 4", "Yet not returned"),
            ("Amos 5", "Seek the Lord"),
            ("Amos 5:24", "Let justice roll"),
            ("Amos 6", "Complacent"),
            ("Amos 7", "Prophetic visions"),
            ("Amos 8", "Famine"),
            ("Amos 9", "Restoration"),
            ("Acts 7:42-43", "Stephen on Amos"),
            ("Acts 15:16-17", "David's tent")
        ],
        "Obadiah": [
            ("Obadiah", "Edom's judgment"),
            ("Obadiah 1-4", "Edom's pride"),
            ("Obadiah 5-9", "Edom's betrayal"),
            ("Obadiah 10-14", "Edom's destruction"),
            ("Obadiah 15-21", "Kingdom the Lord's"),
            ("Jeremiah 49:7-22", "Edom"),
            ("Psalm 137:7-9", "Edom")
        ],
        "Jonah": [
            ("Jonah 1", "Running away"),
            ("Jonah 2", "Prayer from deep"),
            ("Jonah 3", "Nineveh repents"),
            ("Jonah 4", "God's compassion"),
            ("Matthew 12:38-41", "Sign of Jonah"),
            ("Matthew 16:4", "Sign of Jonah"),
            ("Luke 11:29-32", "Sign of Jonah")
        ],
        "Micah": [
            ("Micah 1", "Samaria/Judah"),
            ("Micah 2", "Injustice"),
            ("Micah 3", "Corrupt leaders"),
            ("Micah 4", "Peaceful kingdom"),
            ("Micah 5", "Bethlehem ruler"),
            ("Micah 6", "Lord's case"),
            ("Micah 7", "God's compassion"),
            ("Matthew 2:6", "Bethlehem"),
            ("Jeremiah 26:18", "Micah's prophecy")
        ],
        "Nahum": [
            ("Nahum 1", "God's character"),
            ("Nahum 2", "Nineveh's fall"),
            ("Nahum 3", "Nineveh's sins"),
            ("Jonah 3-4", "Contrast")
        ],
        "Habakkuk": [
            ("Habakkuk 1", "Why evil prosper"),
            ("Habakkuk 2", "Just shall live"),
            ("Habakkuk 3", "God's power"),
            ("Romans 1:17", "Just shall live"),
            ("Galatians 3:11", "Just shall live"),
            ("Hebrews 10:38", "Just shall live")
        ],
        "Zephaniah": [
            ("Zephaniah 1", "Day of Lord"),
            ("Zephaniah 2", "Call to seek"),
            ("Zephaniah 3", "Restoration"),
            ("Zephaniah 3:17", "Rejoice greatly")
        ],
        "Haggai": [
            ("Haggai 1", "Consider your ways"),
            ("Haggai 2", "Future glory"),
            ("Haggai 2:9", "Glory later"),
            ("Haggai 2:23", "Zerubbabel as signet"),
            ("Ezra 5-6", "Temple rebuilt"),
            ("Zechariah 4", "Zerubbabel"),
            ("Hebrews 12:26-29", "Earthquake")
        ],
        "Zechariah": [
            ("Zechariah 1-6", "Night visions"),
            ("Zechariah 7-8", "Historical"),
            ("Zechariah 9-11", "Messianic"),
            ("Zechariah 12-14", "End times"),
            ("Zechariah 3", "Joshua as symbol"),
            ("Zechariah 4", "Menorah"),
            ("Zechariah 6:12", "Branch"),
            ("Zechariah 9:9", "King on donkey"),
            ("Zechariah 11:12-13", "Thirty pieces"),
            ("Zechariah 12:10", "Pierced"),
            ("Zechariah 13:7", "Strike shepherd"),
            ("Matthew 21:5", "Donkey"),
            ("Matthew 26:31", "Shepherd struck"),
            ("Matthew 27:9-10", "Thirty pieces"),
            ("John 12:15", "Donkey"),
            ("John 19:37", "Pierced"),
            ("Revelation 1:7", "Coming with clouds")
        ],
        "Malachi": [
            ("Malachi 1", "Priest dishonor"),
            ("Malachi 2", "Covenant broken"),
            ("Malachi 3", "Messiah's coming"),
            ("Malachi 3:1", "My messenger"),
            ("Malachi 3:10", "Tithes"),
            ("Malachi 4", "Elijah return"),
            ("Matthew 11:10", "Malachi 3:1"),
            ("Luke 1:17", "Elijah spirit"),
            ("Mark 9:11-13", "Elijah"),
            ("Romans 9:13", "Jacob loved")
        ]
    },

    # GOSPELS & NEW TESTAMENT THEMES
    "Gospels & NT Themes": {
        "Kingdom of God": [
            ("Matthew 3:2", "Repent for kingdom"),
            ("Matthew 5-7", "Sermon on mount"),
            ("Matthew 13", "Kingdom parables"),
            ("Mark 1:15", "Time fulfilled"),
            ("Luke 4:43", "Kingdom preaching"),
            ("Luke 10:9", "Kingdom near"),
            ("Luke 17:20-21", "Within you"),
            ("John 3:3-5", "Born again"),
            ("John 18:36", "Not of this world"),
            ("Acts 1:3", "Kingdom preaching"),
            ("Acts 8:12", "Kingdom name"),
            ("Romans 14:17", "Righteousness peace joy"),
            ("1 Corinthians 4:20", "Power not word"),
            ("Colossians 1:13", "Delivered into kingdom"),
            ("Revelation 11:15", "Kingdom become")
        ],
        "Sermon on the Mount": [
            ("Matthew 5:1-12", "Beatitudes"),
            ("Matthew 5:13-16", "Salt/light"),
            ("Matthew 5:17-48", "Law fulfilled"),
            ("Matthew 6:1-18", "Piety"),
            ("Matthew 6:19-34", "Anxiety"),
            ("Matthew 7:1-12", "Judgment/golden rule"),
            ("Matthew 7:13-27", "Narrow way/house built"),
            ("Luke 6:17-49", "Plain sermon"),
            ("Luke 11:9-13", "Ask seek knock"),
            ("Luke 12:22-31", "Don't worry"),
            ("Romans 12", "Practical application")
        ],
        "Parables of Jesus": [
            ("Matthew 13:1-52", "Kingdom parables"),
            ("Mark 4:1-34", "Sower soils"),
            ("Luke 8:4-18", "Sower soils"),
            ("Luke 10:25-37", "Good Samaritan"),
            ("Luke 10:38-42", "Mary/Martha"),
            ("Luke 11:5-13", "Friend at midnight"),
            ("Luke 12:16-21", "Rich fool"),
            ("Luke 13:6-9", "Barren fig"),
            ("Luke 14:7-14", "Great banquet"),
            ("Luke 14:15-24", "Feast invitations"),
            ("Luke 15", "Lost sheep/coin/son"),
            ("Luke 16:1-13", "Shrewd manager"),
            ("Luke 16:19-31", "Rich man/Lazarus"),
            ("Luke 17:7-10", "Unworthy servants"),
            ("Luke 18:1-8", "Unjust judge"),
            ("Luke 18:9-14", "Pharisee/tax collector"),
            ("Luke 19:11-27", "Ten minas"),
            ("Luke 20:9-19", "Wicked tenants"),
            ("Matthew 18:21-35", "Unforgiving servant"),
            ("Matthew 20:1-16", "Vineyard workers"),
            ("Matthew 21:28-32", "Two sons"),
            ("Matthew 22:1-14", "Wedding feast"),
            ("Matthew 25:1-13", "Ten virgins"),
            ("Matthew 25:14-30", "Talents"),
            ("Matthew 25:31-46", "Sheep/goats"),
            ("John 10", "Good shepherd"),
            ("John 12:24", "Grain of wheat"),
            ("John 15", "Vine and branches"),
            ("Acts 10:9-16", "Peter's vision")
        ],
        "Miracles": [
            ("Matthew 8:1-17", "Leper/centurion"),
            ("Matthew 8:23-27", "Sea calmed"),
            ("Matthew 8:28-34", "Gadarenes demons"),
            ("Matthew 9:1-8", "Paralytic"),
            ("Matthew 9:18-26", "Ruler's daughter/woman"),
            ("Matthew 9:27-31", "Two blind men"),
            ("Matthew 9:32-34", "Demon mute"),
            ("Matthew 12:9-14", "Withered hand"),
            ("Matthew 14:13-21", "Five thousand fed"),
            ("Matthew 14:22-33", "Jesus walks water"),
            ("Matthew 15:21-28", "Canaanite woman"),
            ("Matthew 15:29-39", "Four thousand fed"),
            ("Matthew 17:14-21", "Demon-possessed boy"),
            ("Matthew 20:29-34", "Two blind men"),
            ("Mark 5:21-43", "Jairus's daughter"),
            ("Mark 5:25-34", "Woman with issue"),
            ("Mark 7:31-37", "Deaf mute"),
            ("Mark 8:22-26", "Blind man"),
            ("Mark 9:14-29", "Epileptic boy"),
            ("Mark 10:46-52", "Blind Bartimaeus"),
            ("Luke 5:17-26", "Paralytic lowered"),
            ("Luke 7:11-17", "Widow's son"),
            ("Luke 7:36-50", "Sinful woman"),
            ("Luke 8:40-56", "Jairus's daughter"),
            ("Luke 9:37-43", "Demon-possessed boy"),
            ("Luke 13:10-17", "Crippled woman"),
            ("Luke 14:1-6", "Dropsy man"),
            ("Luke 17:11-19", "Ten lepers"),
            ("Luke 18:35-43", "Blind beggar"),
            ("Luke 22:50-51", "Peter's ear"),
            ("John 2:1-11", "Water to wine"),
            ("John 4:46-54", "Royal official's son"),
            ("John 5:1-15", "Pool of Bethesda"),
            ("John 6:1-14", "Five thousand fed"),
            ("John 6:16-21", "Walking water"),
            ("John 9", "Man born blind"),
            ("John 11", "Lazarus raised"),
            ("Acts 3", "Lame man healed"),
            ("Acts 5:12-16", "Healing ministry"),
            ("Acts 9:32-35", "Aeneas healed"),
            ("Acts 10:38", "Healing ministry"),
            ("Acts 14:8-10", "Lystra cripple"),
            ("Acts 20:9-12", "Eutychus raised"),
            ("Acts 28:8-9", "Publius' father")
        ],
        "Last Supper": [
            ("Matthew 26:17-30", "Institution"),
            ("Mark 14:12-26", "Institution"),
            ("Luke 22:7-23", "Institution"),
            ("John 13-17", "Farewell discourse"),
            ("1 Corinthians 11:23-26", "Institution"),
            ("1 Corinthians 10:16-17", "Communion")
        ],
        "Crucifixion": [
            ("Matthew 27", "Crucifixion"),
            ("Mark 15", "Crucifixion"),
            ("Luke 23", "Crucifixion"),
            ("John 19", "Crucifixion"),
            ("Psalm 22", "Fulfilled"),
            ("Isaiah 53", "Fulfilled"),
            ("Acts 8:32-35", "Interpretation"),
            ("Romans 5", "Justified by death"),
            ("1 Corinthians 15", "Resurrection center"),
            ("Galatians 3:13", "Cursed"),
            ("Philippians 2:5-11", "Humiliation"),
            ("Hebrews 9-10", "Perfect sacrifice"),
            ("1 Peter 2:24", "Wounds heal"),
            ("Revelation 5", "Lamb slain")
        ],
        "Resurrection": [
            ("Matthew 28", "Resurrection"),
            ("Mark 16", "Resurrection"),
            ("Luke 24", "Resurrection"),
            ("John 20-21", "Resurrection"),
            ("Acts 1", "Ascension"),
            ("1 Corinthians 15", "Resurrection chapter"),
            ("Romans 1:4", "Declared Son"),
            ("Romans 6:4", "Walk newness"),
            ("Romans 8:11", "Spirit who raised"),
            ("1 Peter 1:3", "Living hope"),
            ("Ephesians 1:20", "Resurrection power"),
            ("Philippians 3:10", "Power resurrection"),
            ("Colossians 2:12", "Raised with"),
            ("1 Thessalonians 4:14", "Jesus risen")
        ],
        "Great Commission": [
            ("Matthew 28:18-20", "Go make disciples"),
            ("Mark 16:15-18", "Preach gospel"),
            ("Luke 24:47-49", "Repentance preached"),
            ("John 20:21-23", "As Father sent"),
            ("Acts 1:8", "Witness Jerusalem"),
            ("Acts 2", "Pentecost"),
            ("Romans 10:14-17", "Preaching necessary"),
            ("Romans 16:25-27", "Mystery revealed"),
            ("2 Corinthians 5:18-20", "Ministry of reconciliation"),
            ("Ephesians 3", "Mystery revealed")
        ]
    }
}

def create_comprehensive_csv():
    """Create the comprehensive themes CSV."""
    output_path = Path(__file__).parent.parent / "data" / "comprehensive_biblical_themes.csv"

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'major_theme',
            'mid_level_theme',
            'level',
            'connection_type',
            'reference',
            'description',
            'testament',
            'genre'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for major_theme, mid_themes in COMPREHENSIVE_THEMES.items():
            for mid_theme, connections in mid_themes.items():
                # Add header row for mid-level theme
                writer.writerow({
                    'major_theme': major_theme,
                    'mid_level_theme': mid_theme,
                    'level': 'MID_LEVEL',
                    'connection_type': '',
                    'reference': '',
                    'description': f'{mid_theme} - {len(connections)} passages',
                    'testament': determine_testament(major_theme),
                    'genre': determine_genre(major_theme)
                })

                # Add all connections
                for ref_desc in connections:
                    if isinstance(ref_desc, tuple):
                        ref = ref_desc[0]
                        desc = ref_desc[1] if len(ref_desc) > 1 else ""
                    else:
                        ref = ref_desc
                        desc = ""

                    writer.writerow({
                        'major_theme': major_theme,
                        'mid_level_theme': mid_theme,
                        'level': 'FINE_GRAINED',
                        'connection_type': 'Direct Reference',
                        'reference': ref,
                        'description': desc,
                        'testament': determine_testament(ref),
                        'genre': determine_genre(ref)
                    })

    print(f"Created comprehensive biblical themes at: {output_path}")

    # Print summary
    total_majors = len(COMPREHENSIVE_THEMES)
    total_mids = sum(len(mids) for mids in COMPREHENSIVE_THEMES.values())
    total_connections = sum(len(conns) for mids in COMPREHENSIVE_THEMES.values() for conns in mids.values())

    print(f"\nSummary:")
    print(f"  Major themes: {total_majors}")
    print(f"  Mid-level themes: {total_mids}")
    print(f"  Total connections: {total_connections}")

def determine_testament(text):
    """Determine if reference is Old/New Testament."""
    if any(book in text.lower() for book in [
        'matthew', 'mark', 'luke', 'john', 'acts', 'romans', 'corinthians',
        'galatians', 'ephesians', 'philippians', 'colossians', 'thessalonians',
        'timothy', 'titus', 'philemon', 'hebrews', 'james', 'peter', 'john',
        'jude', 'revelation'
    ]):
        return 'New Testament'
    elif any(book in text.lower() for book in [
        'sirach', 'wisdom', 'baruch', 'tobit', 'judith', 'maccabees', '1 esdras',
        '2 esdras', '1 enoch', 'jubilees', 'letter of aristeas'
    ]):
        return 'Apocrypha'
    else:
        return 'Old Testament'

def determine_genre(text):
    """Determine genre of text."""
    if any(word in text.lower() for word in ['psalm', 'song', 'lamentation']):
        return 'Poetry'
    elif any(word in text.lower() for word in ['proverb', 'ecclesiastes']):
        return 'Wisdom'
    elif any(word in text.lower() for word in ['prophet', 'isaiah', 'jeremiah', 'ezekiel', 'hosea', 'joel', 'amos', 'obadiah', 'jonah', 'micah', 'nahum', 'habakkuk', 'zephaniah', 'haggai', 'zechariah', 'malachi']):
        return 'Prophecy'
    elif any(word in text.lower() for word in ['genesis', 'exodus', 'leviticus', 'numbers', 'deuteronomy', 'joshua', 'judges', 'ruth', 'samuel', 'kings', 'chronicles', 'ezra', 'nehemiah', 'esther']):
        return 'Narrative'
    elif any(word in text.lower() for word in ['law', 'covenant', 'command', 'statute']):
        return 'Law'
    elif 'revelation' in text.lower():
        return 'Apocalypse'
    elif any(word in text.lower() for word in ['gospel', 'matthew', 'mark', 'luke', 'john']):
        return 'Gospel'
    elif any(word in text.lower() for word in ['epistle', 'romans', 'corinthians', 'galatians']):
        return 'Epistle'
    else:
        return 'General'

if __name__ == "__main__":
    create_comprehensive_csv()