"""
Check Canonicalization Status
==============================

Quick script to check the status of the canonicalization process.
"""

import sqlite3

DB_PATH = "data/liturgy.db"

def check_status():
    """Display canonicalization statistics."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if canonical columns exist
    cursor.execute("PRAGMA table_info(prayers)")
    columns = {row[1] for row in cursor.fetchall()}

    canonical_columns = [
        'canonical_L1_Occasion',
        'canonical_L2_Service',
        'canonical_L3_Signpost',
        'canonical_L4_SubSection',
        'canonical_prayer_name',
        'canonical_usage_type',
        'canonical_location_description',
        'canonicalization_timestamp',
        'canonicalization_status'
    ]

    missing_columns = [col for col in canonical_columns if col not in columns]

    print("=" * 80)
    print("CANONICALIZATION STATUS CHECK")
    print("=" * 80)

    if missing_columns:
        print("\nWARNING: Canonical columns not yet added to database!")
        print(f"Missing columns: {', '.join(missing_columns)}")
        print("\nRun 'python canonicalize_liturgy_db.py' to begin canonicalization.")
        conn.close()
        return

    # Get total prayers
    cursor.execute("SELECT COUNT(*) FROM prayers")
    total = cursor.fetchone()[0]

    # Get status breakdown
    cursor.execute("""
        SELECT
            COALESCE(canonicalization_status, 'not_started') as status,
            COUNT(*) as count
        FROM prayers
        GROUP BY canonicalization_status
    """)
    status_breakdown = cursor.fetchall()

    # Get completed count
    cursor.execute("""
        SELECT COUNT(*) FROM prayers
        WHERE canonicalization_status = 'completed'
    """)
    completed = cursor.fetchone()[0]

    # Get error count
    cursor.execute("""
        SELECT COUNT(*) FROM prayers
        WHERE canonicalization_status = 'error'
    """)
    errors = cursor.fetchone()[0]

    # Sample of completed prayers
    cursor.execute("""
        SELECT prayer_id, prayer_name, canonical_prayer_name,
               canonical_L3_Signpost, canonical_L1_Occasion
        FROM prayers
        WHERE canonicalization_status = 'completed'
        ORDER BY prayer_id
        LIMIT 5
    """)
    samples = cursor.fetchall()

    conn.close()

    # Display results
    print(f"\nTotal prayers: {total}")
    print(f"Completed: {completed} ({100*completed/total:.1f}%)")
    print(f"Errors: {errors} ({100*errors/total:.1f}%)" if errors > 0 else "Errors: 0")
    print(f"Not started: {total - completed - errors}")

    print("\n\nSTATUS BREAKDOWN:")
    print("-" * 80)
    for status, count in status_breakdown:
        status_name = status if status else "not_started"
        percentage = 100 * count / total
        bar_length = int(percentage / 2)
        bar = "█" * bar_length
        print(f"  {status_name:15s} {count:4d} ({percentage:5.1f}%) {bar}")

    if samples:
        print("\n\nSAMPLE CANONICALIZED PRAYERS:")
        print("-" * 80)
        for sample in samples:
            print(f"\nID {sample[0]}: {sample[1]}")
            print(f"  Canonical Name: {sample[2]}")
            print(f"  L3 Signpost: {sample[3]}")
            print(f"  L1 Occasion: {sample[4]}")

    print("\n" + "=" * 80)

    if completed == total:
        print("CANONICALIZATION COMPLETE!")
    elif completed > 0:
        print(f"IN PROGRESS: {total - completed - errors} prayers remaining")
        print("\nTo continue: python canonicalize_liturgy_db.py --resume")
    else:
        print("NOT STARTED")
        print("\nTo begin: python canonicalize_liturgy_db.py")

    if errors > 0:
        print(f"\nWARNING: {errors} prayers failed. Check logs/canonicalization_db_errors.jsonl")

    print("=" * 80)


if __name__ == "__main__":
    check_status()
