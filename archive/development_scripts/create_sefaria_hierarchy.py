#!/usr/bin/env python3
"""Create a CSV of Sefaria's thematic hierarchy."""

import csv

# Sefaria-inspired thematic hierarchy
HIERARCHY = [
    # MAJOR THEMES
    {
        "major_theme": "Creation & Cosmology",
        "mid_level_themes": [
            {
                "theme": "Six Days of Creation",
                "connections": [
                    "Genesis 1:1-2:3", "John 1:1-3", "Psalm 33:6-9", "Proverbs 8:22-31",
                    "2 Corinthians 4:6", "Colossians 1:16-17", "Hebrews 11:3"
                ]
            },
            {
                "theme": "Garden of Eden",
                "connections": [
                    "Genesis 2-3", "Ezekiel 28:11-19", "Revelation 2:7", "Revelation 22:1-5",
                    "1 Corinthians 15:45-49", "2 Esdras 8:52-54", "4 Ezra 7:123"
                ]
            },
            {
                "theme": "Primeval History",
                "connections": [
                    "Genesis 4-11", "1 Chronicles 1:1-4", "Luke 3:36-38", "Jubilees 4-5",
                    "1 Enoch 6-11", "Sirach 44-50", "Wisdom 10-19"
                ]
            },
            {
                "theme": "Divine Order",
                "connections": [
                    "Psalm 104", "Job 38-41", "Isaiah 45:18-19", "Jeremiah 10:12-13",
                    "Amos 4:13", "Acts 17:24-28", "Wisdom 7:15-21"
                ]
            }
        ]
    },
    {
        "major_theme": "Covenant & Promise",
        "mid_level_themes": [
            {
                "theme": "Noahic Covenant",
                "connections": [
                    "Genesis 6:5-9:17", "Isaiah 54:9-10", "Jeremiah 33:20-26", "1 Peter 3:20-22",
                    "2 Peter 2:5", "Sirach 44:17-18", "Wisdom 10:4", "Jubilees 6:1-24"
                ]
            },
            {
                "theme": "Abrahamic Covenant",
                "connections": [
                    "Genesis 12-25", "Romans 4", "Galatians 3:6-29", "Hebrews 11:8-19",
                    "Sirach 44:19-23", "Jubilees 12-22", "1 Maccabees 2:52-60", "Acts 7:2-8"
                ]
            },
            {
                "theme": "Sinai Covenant",
                "connections": [
                    "Exodus 19-24", "Deuteronomy 5", "Jeremiah 31:31-34", "Hebrews 8-10",
                    "2 Corinthians 3:4-18", "Sirach 24:23-29", "Jubilees 30-31"
                ]
            },
            {
                "theme": "Davidic Covenant",
                "connections": [
                    "2 Samuel 7", "Psalm 89", "Psalm 132", "Isaiah 11:1-10",
                    "Jeremiah 23:5-6", "Ezekiel 34:23-24", "Amos 9:11-15", "Acts 2:25-36"
                ]
            }
        ]
    },
    {
        "major_theme": "Exodus & Redemption",
        "mid_level_themes": [
            {
                "theme": "Slavery in Egypt",
                "connections": [
                    "Exodus 1-2", "Leviticus 26:13", "Deuteronomy 28:68", "Acts 7:6-19",
                    "Sirach 45:1-6", "Wisdom 18-19", "Jubilees 34-46"
                ]
            },
            {
                "theme": "The Plagues",
                "connections": [
                    "Exodus 7-12", "Psalm 78:42-51", "Psalm 105:26-36", "Wisdom 16-18",
                    "Revelation 8-16", "Jubilees 48-49", "1 Maccabees 2:64-68"
                ]
            },
            {
                "theme": "Passover",
                "connections": [
                    "Exodus 12-13", "Leviticus 23:5-8", "Numbers 9:1-14", "Deuteronomy 16:1-8",
                    "Joshua 5:10-12", "2 Kings 23:21-23", "2 Chronicles 30", "Ezra 6:19-22"
                ]
            },
            {
                "theme": "Redemption from Egypt",
                "connections": [
                    "Exodus 14-15", "Judges 11:26", "1 Samuel 12:8", "2 Samuel 7:6",
                    "Nehemiah 9:9-15", "Psalm 78", "Psalm 105-106", "Isaiah 11:15-16"
                ]
            }
        ]
    },
    {
        "major_theme": "Wilderness & Revelation",
        "mid_level_themes": [
            {
                "theme": "Wilderness Journey",
                "connections": [
                    "Numbers 10-21", "Deuteronomy 1-3", "Psalm 78:12-16", "Psalm 107:4-9",
                    "Hebrews 3-4", "1 Corinthians 10:1-13", "Jubilees 47-50"
                ]
            },
            {
                "theme": "Divine Provision",
                "connections": [
                    "Exodus 16", "Numbers 11", "Deuteronomy 8", "Nehemiah 9:15-21",
                    "Psalm 78:23-31", "John 6:31-35", "1 Corinthians 10:3-4"
                ]
            },
            {
                "theme": "Tabernacle & Worship",
                "connections": [
                    "Exodus 25-40", "Leviticus 1-7", "Numbers 1-10", "Hebrews 8-9",
                    "2 Chronicles 5-7", "Ezekiel 40-48", "Revelation 21-22"
                ]
            },
            {
                "theme": "Rebellion & Consequence",
                "connections": [
                    "Numbers 13-14", "Numbers 20", "Numbers 21:4-9", "Deuteronomy 1:19-46",
                    "Psalm 95:7-11", "Hebrews 3:7-19", "1 Corinthians 10:6-11"
                ]
            }
        ]
    },
    {
        "major_theme": "Prophecy & Revelation",
        "mid_level_themes": [
            {
                "theme": "Prophetic Calling",
                "connections": [
                    "Isaiah 6", "Jeremiah 1", "Ezekiel 1-3", "Amos 7:14-15",
                    "Jonah 1-3", "Hosea 1-2", "Micah 3:8", "1 Kings 19:19-21"
                ]
            },
            {
                "theme": "Prophetic Visions",
                "connections": [
                    "Isaiah 6", "Ezekiel 1-3", "Daniel 7-12", "Zechariah 1-8",
                    "Amos 7-9", "Revelation 1-22", "1 Enoch 72-82"
                ]
            },
            {
                "theme": "Prophetic Oracles",
                "connections": [
                    "Isaiah 13-23", "Jeremiah 46-51", "Ezekiel 25-32", "Amos 1-2",
                    "Obadiah", "Nahum", "Zephaniah 2", "Revelation 17-18"
                ]
            },
            {
                "theme": "Day of the Lord",
                "connections": [
                    "Joel 2", "Zephaniah 1", "Obadiah 15-21", "Malachi 4",
                    "Isaiah 24-27", "Ezekiel 7", "1 Thessalonians 5", "2 Peter 3"
                ]
            }
        ]
    },
    {
        "major_theme": "Wisdom & Understanding",
        "mid_level_themes": [
            {
                "theme": "Nature of Wisdom",
                "connections": [
                    "Proverbs 1-9", "Job 28", "Sirach 1-24", "Wisdom 6-10",
                    "Daniel 2:20-23", "James 1:5", "Colossians 2:3"
                ]
            },
            {
                "theme": "Fear of the Lord",
                "connections": [
                    "Proverbs 1:7", "Proverbs 9:10", "Job 28:28", "Psalm 111:10",
                    "Ecclesiastes 12:13", "Sirach 1:12-20", "Acts 9:31"
                ]
            },
            {
                "theme": "Parables & Riddles",
                "connections": [
                    "Judges 14", "2 Samuel 12", "1 Kings 20", "Ezekiel 17",
                    "Hosea 12:10", "Psalm 49", "Psalm 78", "Mark 4"
                ]
            },
            {
                "theme": "Two Ways",
                "connections": [
                    "Deuteronomy 30", "Psalm 1", "Jeremiah 21:8", "Proverbs 4",
                    "Sirach 15:14-17", "Matthew 7:13-14", "2 Peter 2:20-22"
                ]
            }
        ]
    },
    {
        "major_theme": "Kingship & Messiah",
        "mid_level_themes": [
            {
                "theme": "Divine Kingship",
                "connections": [
                    "Psalm 47", "Psalm 93", "Psalm 97", "Psalm 99",
                    "Isaiah 6:5", "Jeremiah 10:7", "Daniel 4:34-35", "1 Timothy 6:15-16"
                ]
            },
            {
                "theme": "Davidic King",
                "connections": [
                    "2 Samuel 7", "Psalm 2", "Psalm 72", "Psalm 89",
                    "Psalm 110", "Isaiah 11", "Jeremiah 23", "Ezekiel 34"
                ]
            },
            {
                "theme": "Messianic Prophecies",
                "connections": [
                    "Isaiah 7:14", "Isaiah 9:6-7", "Isaiah 53", "Jeremiah 23:5-6",
                    "Ezekiel 37:24-28", "Daniel 7:13-14", "Micah 5:2-5", "Zechariah 9:9"
                ]
            },
            {
                "theme": "Royal Psalms",
                "connections": [
                    "Psalm 2", "Psalm 18", "Psalm 20", "Psalm 21",
                    "Psalm 45", "Psalm 72", "Psalm 89", "Psalm 110", "Psalm 144"
                ]
            }
        ]
    },
    {
        "major_theme": "Temple & Worship",
        "mid_level_themes": [
            {
                "theme": "Tabernacle",
                "connections": [
                    "Exodus 25-40", "Numbers 1-10", "Hebrews 8-9", "Revelation 21",
                    "2 Chronicles 5-7", "Acts 7:44-50", "Sirach 24:23-29"
                ]
            },
            {
                "theme": "Solomon's Temple",
                "connections": [
                    "1 Kings 5-8", "2 Chronicles 2-7", "Psalm 132", "Ezekiel 40-48",
                    "Haggai 2", "Zechariah 6:12-13", "John 2:19-21"
                ]
            },
            {
                "theme": "Priesthood",
                "connections": [
                    "Exodus 28-29", "Leviticus 8-10", "Numbers 18", "Deuteronomy 18",
                    "Psalm 110", "Hebrews 5-7", "1 Peter 2:5-9", "Revelation 1:6"
                ]
            },
            {
                "theme": "Sacrifices & Offerings",
                "connections": [
                    "Leviticus 1-7", "Numbers 28-29", "Deuteronomy 12", "Psalm 40:6",
                    "Psalm 50", "Psalm 51", "Hebrews 9-10", "1 Corinthians 5:7"
                ]
            }
        ]
    },
    {
        "major_theme": "Exile & Diaspora",
        "mid_level_themes": [
            {
                "theme": "Assyrian Exile",
                "connections": [
                    "2 Kings 15-17", "2 Chronicles 30", "Isaiah 36-37", "Hosea",
                    "Amos", "Micah", "Judith", "Tobit 1-2"
                ]
            },
            {
                "theme": "Babylonian Exile",
                "connections": [
                    "2 Kings 24-25", "2 Chronicles 36", "Jeremiah 24-29", "Jeremiah 52",
                    "Ezekiel 1-24", "Lamentations", "Daniel 1-6", "Baruch"
                ]
            },
            {
                "theme": "Restoration",
                "connections": [
                    "Ezra 1-6", "Nehemiah 1-13", "Haggai", "Zechariah", "Malachi",
                    "Isaiah 40-55", "Jeremiah 30-33", "Ezekiel 33-48"
                ]
            },
            {
                "theme": "Diaspora Life",
                "connections": [
                    "Esther", "Daniel", "Tobit", "Judith", "1-2 Maccabees",
                    "Psalm 137", "Psalm 44", "Jeremiah 29", "Letter of Aristeas"
                ]
            }
        ]
    },
    {
        "major_theme": "Ethics & Justice",
        "mid_level_themes": [
            {
                "theme": "Social Justice",
                "connections": [
                    "Deuteronomy 15", "Deuteronomy 24", "Isaiah 1:17", "Isaiah 58",
                    "Jeremiah 22:3", "Amos 5:24", "Micah 6:8", "Zechariah 7:9-10"
                ]
            },
            {
                "theme": "Righteousness",
                "connections": [
                    "Genesis 15:6", "Psalm 1", "Psalm 15", "Psalm 24",
                    "Isaiah 33:15-16", "Habakkuk 2:4", "Matthew 5-7", "Romans 4"
                ]
            },
            {
                "theme": "Poverty & Wealth",
                "connections": [
                    "Deuteronomy 15", "Deuteronomy 24", "Proverbs 13-15", "Proverbs 22-23",
                    "Amos 2-6", "Micah 2-3", "Jeremiah 22", "James 5"
                ]
            },
            {
                "theme": "Truth & Falsehood",
                "connections": [
                    "Exodus 20:16", "Proverbs 12-13", "Proverbs 6:16-19", "Jeremiah 9:5-6",
                    "Zechariah 8:16-17", "Ephesians 4:25", "Colossians 3:9"
                ]
            }
        ]
    },
    {
        "major_theme": "Human Nature & Destiny",
        "mid_level_themes": [
            {
                "theme": "Creation of Humanity",
                "connections": [
                    "Genesis 1-2", "Psalm 8", "Psalm 139", "Sirach 17",
                    "Wisdom 2:23", "1 Corinthians 15:45-49", "James 3:7-10"
                ]
            },
            {
                "theme": "Sin & Fall",
                "connections": [
                    "Genesis 3", "Romans 5", "1 Corinthians 15", "Wisdom 2-4",
                    "Sirach 25", "Psalm 51", "Ezekiel 18", "Jeremiah 17"
                ]
            },
            {
                "theme": "Life After Death",
                "connections": [
                    "Psalm 16:10", "Psalm 49", "Psalm 73", "Isaiah 26:19",
                    "Daniel 12:2-3", "2 Maccabees 7", "1 Corinthians 15", "John 5:28-29"
                ]
            },
            {
                "theme": "Eschatology",
                "connections": [
                    "Daniel 7-12", "Isaiah 24-27", "Ezekiel 38-39", "Zechariah 12-14",
                    "Joel 2-3", "Matthew 24-25", "Revelation 20-22", "1 Enoch 91-105"
                ]
            }
        ]
    }
]

def create_csv():
    """Create the hierarchy CSV."""
    output_path = Path(__file__).parent.parent / "data" / "sefaria_topic_hierarchy.csv"

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['major_theme', 'mid_level_theme', 'level', 'connection_type', 'reference', 'notes']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for major in HIERARCHY:
            for mid in major["mid_level_themes"]:
                # Add header row for mid-level theme
                writer.writerow({
                    'major_theme': major["major_theme"],
                    'mid_level_theme': mid["theme"],
                    'level': 'MID_LEVEL',
                    'connection_type': '',
                    'reference': '',
                    'notes': f'{mid["theme"]} - {len(mid["connections"])} connections'
                })

                # Add all connections
                for conn in mid["connections"]:
                    writer.writerow({
                        'major_theme': major["major_theme"],
                        'mid_level_theme': mid["theme"],
                        'level': 'FINE_GRAINED',
                        'connection_type': 'Direct Reference',
                        'reference': conn,
                        'notes': ''
                    })

    print(f"Created Sefaria topic hierarchy at: {output_path}")

    # Print summary
    total_connections = sum(len(mid["connections"]) for major in HIERARCHY for mid in major["mid_level_themes"])
    print(f"\nSummary:")
    print(f"  Major themes: {len(HIERARCHY)}")
    print(f"  Mid-level themes: {sum(len(major['mid_level_themes']) for major in HIERARCHY)}")
    print(f"  Total connections: {total_connections}")

if __name__ == "__main__":
    from pathlib import Path
    create_csv()