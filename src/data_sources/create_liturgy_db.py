"""
Create and initialize the comprehensive liturgical database.

This script:
1. Executes the liturgy_db_schema.sql to create tables
2. Populates liturgical_metadata with standard values
3. Preserves existing Phase 0 data (sefaria_liturgy_links table)

Usage:
    python src/data_sources/create_liturgy_db.py
"""

import sqlite3
from pathlib import Path


def create_liturgy_database(db_path: str = "data/liturgy.db"):
    """
    Create the comprehensive liturgical database with all tables and indexes.

    Args:
        db_path: Path to SQLite database file
    """

    print(f"Creating comprehensive liturgical database: {db_path}")
    print("=" * 60)

    # Read schema SQL
    schema_path = Path(__file__).parent / "liturgy_db_schema.sql"

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # Connect and execute schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n1. Creating tables and indexes...")
    cursor.executescript(schema_sql)
    print("   [OK] Tables created:")
    print("     - prayers")
    print("     - psalms_liturgy_index")
    print("     - liturgical_metadata")
    print("     - harvest_log")
    print("     - phrase_cache")

    # Populate metadata
    print("\n2. Populating liturgical_metadata...")
    rows_inserted = _insert_metadata(cursor)
    print(f"   [OK] Inserted {rows_inserted} metadata entries")

    conn.commit()

    # Display summary
    print("\n3. Database summary:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   - {table}: {count} rows")

    conn.close()

    print("\n" + "=" * 60)
    print(f"[OK] Liturgical database ready: {db_path}")
    print("\nNext steps:")
    print("  1. Run Phase 2: Harvest liturgical corpus from Sefaria")
    print("  2. Run Phase 3: Extract and score phrases from Psalms")
    print("  3. Run Phase 4: Index phrases against liturgy")


def _insert_metadata(cursor):
    """
    Populate liturgical_metadata table with standard values.

    Returns:
        Number of rows inserted
    """

    metadata = [
        # Nusachim (Liturgical Traditions)
        ('nusach', 'Ashkenaz', 'Ashkenazi', 'אשכנז',
         'Central and Eastern European Jewish tradition', 'Widespread'),
        ('nusach', 'Sefard', 'Sephardic/Hasidic', 'ספרד',
         'Hasidic version based on Lurianic kabbalah', 'Common in Hasidic communities'),
        ('nusach', 'Edot_HaMizrach', 'Edot HaMizrach', 'עדות המזרח',
         'Middle Eastern and North African Jewish tradition', 'Common in Israel'),

        # Services (Daily prayer times)
        ('service', 'Shacharit', 'Morning Service', 'שחרית',
         'Daily morning prayer service', 'Daily, typically sunrise'),
        ('service', 'Mincha', 'Afternoon Service', 'מנחה',
         'Daily afternoon prayer service', 'Daily, typically mid-afternoon'),
        ('service', 'Maariv', 'Evening Service', 'מעריב',
         'Daily evening prayer service', 'Daily, after nightfall'),
        ('service', 'Musaf', 'Additional Service', 'מוסף',
         'Additional service on Sabbath and holidays', 'Sabbath and festivals only'),
        ('service', 'Neilah', 'Closing Service', 'נעילה',
         'Final service on Yom Kippur', 'Yom Kippur only'),

        # Major sections within services
        ('section', 'Pesukei_DZimrah', 'Verses of Praise', 'פסוקי דזמרה',
         'Preparatory psalms and biblical verses before Shacharit', 'Daily morning'),
        ('section', 'Shema', 'Shema and Blessings', 'שמע',
         'Declaration of faith with surrounding blessings', 'Twice daily'),
        ('section', 'Amidah', 'Standing Prayer', 'עמידה',
         'Central prayer recited while standing (also called Shemoneh Esrei)', 'All services'),
        ('section', 'Tachanun', 'Supplication', 'תחנון',
         'Penitential prayers on weekdays', 'Weekday mornings/afternoons'),
        ('section', 'Hallel', 'Praise', 'הלל',
         'Psalms 113-118 recited on festivals', 'Festivals and Rosh Chodesh'),
        ('section', 'Kabbalat_Shabbat', 'Welcoming Sabbath', 'קבלת שבת',
         'Friday evening prayers to welcome Sabbath', 'Friday evening only'),
        ('section', 'Selichot', 'Penitential Prayers', 'סליחות',
         'Special prayers for forgiveness during High Holiday season', 'Pre-Rosh Hashanah, fast days'),
        ('section', 'Torah_Reading', 'Torah Reading', 'קריאת התורה',
         'Public reading from the Torah scroll', 'Sabbath, festivals, Mondays, Thursdays'),

        # Occasions (When prayers are recited)
        ('occasion', 'Weekday', 'Weekday', 'יום חול',
         'Monday-Friday services (regular liturgy)', 'Daily'),
        ('occasion', 'Shabbat', 'Sabbath', 'שבת',
         'Saturday services with special prayers', 'Weekly'),
        ('occasion', 'Rosh_Hashanah', 'Rosh Hashanah', 'ראש השנה',
         'Jewish New Year (Tishrei 1-2)', 'Annually, fall'),
        ('occasion', 'Yom_Kippur', 'Yom Kippur', 'יום כיפור',
         'Day of Atonement (Tishrei 10)', 'Annually, fall'),
        ('occasion', 'Sukkot', 'Sukkot', 'סוכות',
         'Feast of Tabernacles (Tishrei 15-21)', 'Annually, fall'),
        ('occasion', 'Shemini_Atzeret', 'Shemini Atzeret', 'שמיני עצרת',
         'Eighth Day of Assembly (Tishrei 22)', 'Annually, fall'),
        ('occasion', 'Simchat_Torah', 'Simchat Torah', 'שמחת תורה',
         'Rejoicing of the Torah (Tishrei 23 in Diaspora)', 'Annually, fall'),
        ('occasion', 'Chanukah', 'Chanukah', 'חנוכה',
         'Festival of Lights (Kislev 25 - Tevet 2/3)', 'Annually, winter'),
        ('occasion', 'Purim', 'Purim', 'פורים',
         'Festival commemorating the Esther story (Adar 14)', 'Annually, spring'),
        ('occasion', 'Pesach', 'Passover', 'פסח',
         'Festival of Unleavened Bread (Nisan 15-22)', 'Annually, spring'),
        ('occasion', 'Shavuot', 'Shavuot', 'שבועות',
         'Feast of Weeks (Sivan 6-7)', 'Annually, late spring'),
        ('occasion', 'Rosh_Chodesh', 'New Moon', 'ראש חודש',
         'Beginning of Hebrew month', 'Monthly'),
        ('occasion', 'Fast_Days', 'Fast Days', 'תעניות',
         'Public fast days (various dates)', 'Several times yearly'),

        # Prayer types (Categories of liturgical texts)
        ('prayer_type', 'Siddur', 'Prayer Book', 'סידור',
         'Standard prayer book for daily and Sabbath prayers', 'Daily/Sabbath use'),
        ('prayer_type', 'Machzor', 'Festival Prayer Book', 'מחזור',
         'Special prayer book for High Holidays', 'Rosh Hashanah and Yom Kippur'),
        ('prayer_type', 'Haggadah', 'Passover Haggadah', 'הגדה',
         'Text for Passover Seder', 'Passover night'),
        ('prayer_type', 'Kinot', 'Lamentations', 'קינות',
         'Elegies for Tisha B\'Av', 'Tisha B\'Av'),
        ('prayer_type', 'Selichot_Book', 'Penitential Prayers', 'ספר סליחות',
         'Collection of penitential prayers', 'Pre-Rosh Hashanah, fast days'),
    ]

    cursor.executemany(
        """INSERT INTO liturgical_metadata
           (category, key, display_name_english, display_name_hebrew, description, typical_timing)
           VALUES (?, ?, ?, ?, ?, ?)""",
        metadata
    )

    return len(metadata)


if __name__ == "__main__":
    create_liturgy_database()
