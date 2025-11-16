"""
Preview Database Schema Changes
================================

This script shows what changes will be made to liturgy.db
without actually making any changes.
"""

import sqlite3

DB_PATH = "data/liturgy.db"

def preview_schema():
    """Show current schema and proposed changes."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get current schema
    cursor.execute("PRAGMA table_info(prayers)")
    existing_columns = cursor.fetchall()

    # Get total prayers
    cursor.execute("SELECT COUNT(*) FROM prayers")
    total_prayers = cursor.fetchone()[0]

    # Get sample prayer
    cursor.execute("""
        SELECT prayer_id, prayer_name, nusach, service, section,
               LENGTH(hebrew_text) as text_len
        FROM prayers
        LIMIT 1
    """)
    sample = cursor.fetchone()

    conn.close()

    print("=" * 80)
    print("DATABASE SCHEMA PREVIEW")
    print("=" * 80)
    print(f"\nDatabase: {DB_PATH}")
    print(f"Total prayers to process: {total_prayers}")
    print(f"\nSample prayer:")
    print(f"  ID: {sample[0]}, Name: {sample[1]}, Nusach: {sample[2]}")
    print(f"  Service: {sample[3]}, Section: {sample[4]}, Text length: {sample[5]} chars")

    print(f"\n\nCURRENT COLUMNS ({len(existing_columns)}):")
    print("-" * 80)
    for col in existing_columns:
        print(f"  {col[1]:35s} {col[2]:15s}")

    new_columns = [
        ('canonical_L1_Occasion', 'TEXT', 'Top-level occasion (e.g., Weekday, Shabbat)'),
        ('canonical_L2_Service', 'TEXT', 'Service (e.g., Shacharit, Mincha, Arvit)'),
        ('canonical_L3_Signpost', 'TEXT', 'Major section milestone (REQUIRED)'),
        ('canonical_L4_SubSection', 'TEXT', 'Granular sub-section (optional)'),
        ('canonical_prayer_name', 'TEXT', 'Standardized prayer name'),
        ('canonical_usage_type', 'TEXT', 'Nature of text (e.g., Full Psalm, Tefillah)'),
        ('canonical_location_description', 'TEXT', 'Human-readable location context'),
        ('canonicalization_timestamp', 'TEXT', 'When this entry was processed'),
        ('canonicalization_status', 'TEXT', 'Status: pending/completed/error')
    ]

    existing_names = {col[1] for col in existing_columns}
    columns_to_add = [col for col in new_columns if col[0] not in existing_names]

    print(f"\n\nNEW COLUMNS TO BE ADDED ({len(columns_to_add)}):")
    print("-" * 80)
    for col_name, col_type, description in columns_to_add:
        print(f"  {col_name:35s} {col_type:15s} - {description}")

    print("\n" + "=" * 80)
    print("WHAT WILL HAPPEN:")
    print("=" * 80)
    print(f"1. Add {len(columns_to_add)} new columns to the 'prayers' table")
    print(f"2. Process all {total_prayers} prayers through Gemini API")
    print(f"3. Update each prayer with canonicalized metadata")
    print(f"4. Track progress in logs/canonicalization_db_progress.json")
    print(f"5. Log errors to logs/canonicalization_db_errors.jsonl")
    print("\nEstimated time: ~{:.0f} minutes (at 2 seconds per prayer)".format(total_prayers * 2 / 60))
    print("\nThe script is RESUMABLE - if interrupted, run with --resume flag")
    print("=" * 80)


if __name__ == "__main__":
    preview_schema()
