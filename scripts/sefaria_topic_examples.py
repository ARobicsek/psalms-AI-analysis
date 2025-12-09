#!/usr/bin/env python3
"""Show real examples of how Sefaria organizes content by topics."""

print("SEFARIA TOPIC-BASED CHUNKING EXAMPLES")
print("=" * 60)

print("""
Based on Sefaria's actual organization, here are concrete examples
of how topics would group biblical passages:

1. TOPIC: "Creation" (Bereshit)
   Primary Texts:
   - Genesis 1:1-31 (Six days of creation)
   - Genesis 2:1-3 (Shabbat completion)
   - Genesis 2:4-25 (Adam and Eve in Garden)

   Thematic Connections:
   - Psalm 104 (God as Creator)
   - Isaiah 40:12-26 (Creation's scope)
   - Job 38-41 (God's creative power)
   - Proverbs 8:22-31 (Wisdom in creation)

2. TOPIC: "Covenant" (Brit)
   Primary Texts:
   - Genesis 9:8-17 (Noahic covenant - rainbow)
   - Genesis 15 (Abrahamic covenant - stars)
   - Genesis 17 (Covenant of circumcision)

   Thematic Connections:
   - Exodus 19-24 (Sinai covenant)
   - Jeremiah 31:31-34 (New covenant)
   - Psalm 89 (Davidic covenant)
   - Ezekiel 16 (Covenant as marriage)

3. TOPIC: "Exodus and Redemption" (Yetziat Mitzrayim)
   Primary Texts:
   - Exodus 1-15 (Slavery to redemption)
   - Exodus 12 (Passover narrative)
   - Exodus 14 (Crossing the Red Sea)

   Thematic Connections:
   - Psalm 78, 105, 106 (Historical psalms)
   - Isaiah 11:15-16 (Redemption prophecy)
   - Micah 7:15 (Like exodus from Egypt)
   - Jeremiah 16:14-15 (New exodus)

4. TOPIC: "Divine Providence" (Hashgacha)
   Primary Texts:
   - Genesis 45:5-8 (Joseph's providence)
   - Esther (Hidden providence)
   - Daniel 3 (Fiery furnace deliverance)

   Thematic Connections:
   - Psalm 91 (Divine protection)
   - Proverbs 16:9 (Man plans, God directs)
   - Lamentations 3:22-23 (New mercies)
   - Romans 8:28 (All works for good)

5. TOPIC: "Wisdom and Folly" (Chochma v'Sevora)
   Primary Texts:
   - 1 Kings 3 (Solomon chooses wisdom)
   - Proverbs 1-9 (Wisdom personified)
   - Ecclesiastes (Wisdom's limits)

   Thematic Connections:
   - Job 28 (Where is wisdom found?)
   - Daniel (Wisdom in exile)
   - James 1:5 (Ask for wisdom)

6. TOPIC: "Shepherd Motif" (Ro'eh)
   Primary Texts:
   - Genesis 49:24 (Joseph as shepherd)
   - Psalm 23 (Lord as shepherd)
   - Ezekiel 34 (False shepherds vs true)

   Thematic Connections:
   - Isaiah 40:11 (Gentle shepherd)
   - Micah 7:14 (Shepherd Israel)
   - John 10 (Good Shepherd)
   - 1 Peter 2:25 (Shepherd and bishop)

7. TOPIC: "Messianic Prophecies" (Mashiach)
   Primary Texts:
   - Isaiah 7:14 (Immanuel)
   - Isaiah 9:6-7 (Wonderful counselor)
   - Isaiah 53 (Suffering servant)
   - Jeremiah 23:5-6 (Righteous branch)

   Thematic Connections:
   - Psalm 2, 110 (Royal psalms)
   - Daniel 7:13-14 (Son of man)
   - Micah 5:2 (Bethlehem birth)

HOW SEFARIA MAKES THESE CONNECTIONS:
-----------------------------------
1. Traditional Links (Mesorah)
   - Cross-references in printed editions
   - Rabbinic commentaries
   - Ge'onic and medieval supercommentaries

2. Linguistic Connections
   - Shared keywords and phrases
   - Allusions and quotations
   - Thematic vocabulary

3. Conceptual Networks
   - AI-powered similarity detection
   - Topic modeling
   - User-generated connections

IMPLEMENTATION STRATEGY:
-----------------------
1. Start with ~50 core topics
2. Use Sefaria's API to fetch connections
3. Add topics gradually based on needs
4. Maintain manual curation for quality

Example topic size distribution:
- Large topics (30+ texts): Creation, Covenant, Temple
- Medium topics (10-30 texts): Prophecy, Kingship, Wisdom
- Small topics (5-10 texts): Specific motifs, minor themes

This approach ensures:
✓ Thematic coherence
✓ Scholarly validation
✓ Scalable system
✓ Quality control
""")

print("\nExample of a Single Topic Chunk:")
print("-" * 40)
print("""
Topic: "Divine Shepherd"
Chunks created:
1. Genesis 49:24 - "From there is the Shepherd, the Stone of Israel"
2. Psalm 23:1-6 - Complete psalm (6 verses)
3. Psalm 80:1-3 - "Shepherd of Israel, you who lead Joseph"
4. Isaiah 40:11 - "He tends his flock like a shepherd"
5. Ezekiel 34:11-16 - "I myself will search for my sheep"
6. Ezekiel 34:23-24 - "I will place one shepherd over them"
7. Micah 7:14 - "Shepherd your people with your staff"
8. Zechariah 13:7 - "Strike the shepherd, scatter the sheep"

Total: 8 chunks spanning Torah, Prophets, and Writings
Each chunk is thematically unified around the shepherd metaphor
Size varies (1-6 verses) based on natural passage boundaries
""")