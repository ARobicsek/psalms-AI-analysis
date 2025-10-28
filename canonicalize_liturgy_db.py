"""
Liturgical Database Canonicalization Script
============================================

This script processes ALL prayers in liturgy.db and adds canonicalized
hierarchical metadata fields using the Gemini API.

The new fields are written directly back to the liturgy.db database.

Usage:
    python canonicalize_liturgy_db.py [--resume] [--start-id N]

Options:
    --resume     Resume from last processed prayer_id
    --start-id N Start from specific prayer_id
"""

import os
import sys
import json
import sqlite3
import time
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai

# Configuration
DB_PATH = "data/liturgy.db"
PROGRESS_FILE = "logs/canonicalization_db_progress.json"
ERROR_LOG_FILE = "logs/canonicalization_db_errors.jsonl"
GEMINI_MODEL = "gemini-2.5-pro"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
API_DELAY = 0.5  # delay between successful API calls

# Ensure logs directory exists
Path("logs").mkdir(exist_ok=True)

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

# Configure Gemini
genai.configure(api_key=api_key)

# L3 Signpost Categories
L3_SIGNPOST_CATEGORIES = """
- Preparatory Prayers (e.g., Birkhot HaShachar, Korbanot)
- Pesukei Dezimra (Verses of Praise)
- Birkhot K'riat Shema (Blessings of the Shema, e.g., Yotzer Or, Ahavah Rabbah)
- K'riat Shema (The Shema itself)
- Amidah (The "Standing Prayer")
- Post-Amidah (e.g., Tachanun, Vidui)
- Torah Service
- Concluding Prayers (e.g., Ashrei, Uva L'Tzion, Aleinu, Song of the Day, Psalm 27)
- Kabbalat Shabbat
- Mussaf
- Neilah
- Special - High Holiday (e.g., Malchuyot, Zichronot, Shofarot, Avodah)
- Special - Piyyutim (Liturgical poems inserted into the service)
- Home / Non-Synagogue Ritual (e.g., Kiddush, Havdalah, Bedtime Shema)
- Other / Supplemental (e.g., Annulment of Vows, Tikkun Chatzot)
""".strip()

SYSTEM_PROMPT = """You are a world-class expert in Jewish liturgy (Ashkenaz, Sefard, and Edot HaMizrach) and a master data analyst. Your task is to remap an entry from a messy liturgical text database (provided as 'Input Data') into a new, clean, and consistent hierarchical JSON format, as specified by the 'Required Output Format'.

**CRITICAL RULES:**

1. You *must* use one of the provided **Canonical `L3_Signpost` Categories** for the `L3_Signpost` field. Do not invent new ones.
2. The `L1_Occasion` and `L2_Service` fields must be standardized.
3. **HANDLING "CLUMPED" TEXT:** The `hebrew_text` field may contain multiple, distinct liturgical sections (e.g., Yishtabach, followed by Psalm 130, followed by Kaddish, followed by Yotzer Or). You must analyze the *entire* text.
    * The `L3_Signpost`, `L4_SubSection`, and `canonical_prayer_name` should reflect the **primary liturgical purpose** of the *entire* block (e.g., "Yotzer Or" in the example above, not "Yishtabach").
    * The `relative_location_description` *must* explicitly describe this composite structure (e.g., "This block begins with Yishtabach, includes Psalm 130, and then contains the full Yotzer Or blessing...").
4. The 'canonical_location_description' field should provide a clear, human-readable explanation of where this prayer fits within the overall liturgical service structure AND **it should identify any Psalms in the text if possible**.
5. Your output must be a single, valid JSON object and nothing else."""


def setup_database():
    """Add canonical fields to the prayers table if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(prayers)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    new_columns = {
        'canonical_L1_Occasion': 'TEXT',
        'canonical_L2_Service': 'TEXT',
        'canonical_L3_Signpost': 'TEXT',
        'canonical_L4_SubSection': 'TEXT',
        'canonical_prayer_name': 'TEXT',
        'canonical_usage_type': 'TEXT',
        'canonical_location_description': 'TEXT',
        'canonicalization_timestamp': 'TEXT',
        'canonicalization_status': 'TEXT'  # 'pending', 'completed', 'error'
    }

    columns_added = []
    for col_name, col_type in new_columns.items():
        if col_name not in existing_columns:
            cursor.execute(f"ALTER TABLE prayers ADD COLUMN {col_name} {col_type}")
            columns_added.append(col_name)

    conn.commit()
    conn.close()

    return columns_added


def create_user_prompt(prayer_data: Dict[str, Any]) -> str:
    """Construct the user prompt for a single prayer entry."""
    input_data = {
        "prayer_id": prayer_data["prayer_id"],
        "source_corpus": prayer_data.get("source_text", "Unknown"),
        "nusach": prayer_data.get("nusach", "Unknown"),
        "service": prayer_data.get("service", "Unknown"),
        "section": prayer_data.get("section", "Unknown"),
        "prayer_name": prayer_data.get("prayer_name", "Unknown"),
        "hebrew_text": prayer_data.get("hebrew_text", "")
    }

    prompt = f"""Please remap the following prayer entry into the new, standardized JSON schema.

---
### Canonical `L3_Signpost` Categories (Use one of these)
{L3_SIGNPOST_CATEGORIES}
---

### Input Data (from source file)
{json.dumps(input_data, ensure_ascii=False, indent=2)}
---

### Required Output Format (JSON only)
{{
  "original_prayer_id": null,
  "source_corpus": null,
  "nusach": null,
  "L1_Occasion": null,
  "L2_Service": null,
  "L3_Signpost": null,
  "L4_SubSection": null,
  "canonical_prayer_name": null,
  "usage_type": null,
  "relative_location_description": null,
  "hebrew_text": null
}}"""

    return prompt


def call_gemini_api(prayer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Call Gemini API to canonicalize a single prayer entry."""
    user_prompt = create_user_prompt(prayer_data)

    for attempt in range(MAX_RETRIES):
        try:
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                system_instruction=SYSTEM_PROMPT
            )

            generation_config = genai.types.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )

            response = model.generate_content(
                user_prompt,
                generation_config=generation_config
            )

            # Parse the JSON response
            result = json.loads(response.text)

            # Handle case where API returns an array instead of object
            if isinstance(result, list) and len(result) > 0:
                result = result[0]

            return result

        except json.JSONDecodeError as e:
            error_msg = f"JSON parsing error on attempt {attempt + 1}: {e}"
            print(f"  WARNING: {error_msg}")
            if attempt == MAX_RETRIES - 1:
                log_error(prayer_data["prayer_id"], error_msg, response.text if 'response' in locals() else None)
                return None
            time.sleep(RETRY_DELAY)

        except Exception as e:
            error_msg = f"API error on attempt {attempt + 1}: {type(e).__name__}: {e}"
            print(f"  WARNING: {error_msg}")
            if attempt == MAX_RETRIES - 1:
                log_error(prayer_data["prayer_id"], error_msg)
                return None
            time.sleep(RETRY_DELAY)

    return None


def update_prayer_in_db(prayer_id: int, canonical_data: Optional[Dict[str, Any]]):
    """Update a prayer with canonical data in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if canonical_data:
        # Success - update with canonical data
        cursor.execute("""
            UPDATE prayers
            SET canonical_L1_Occasion = ?,
                canonical_L2_Service = ?,
                canonical_L3_Signpost = ?,
                canonical_L4_SubSection = ?,
                canonical_prayer_name = ?,
                canonical_usage_type = ?,
                canonical_location_description = ?,
                canonicalization_timestamp = datetime('now'),
                canonicalization_status = 'completed'
            WHERE prayer_id = ?
        """, (
            canonical_data.get('L1_Occasion'),
            canonical_data.get('L2_Service'),
            canonical_data.get('L3_Signpost'),
            canonical_data.get('L4_SubSection'),
            canonical_data.get('canonical_prayer_name'),
            canonical_data.get('usage_type'),
            canonical_data.get('relative_location_description'),
            prayer_id
        ))
    else:
        # Error - mark as error
        cursor.execute("""
            UPDATE prayers
            SET canonicalization_status = 'error',
                canonicalization_timestamp = datetime('now')
            WHERE prayer_id = ?
        """, (prayer_id,))

    conn.commit()
    conn.close()


def log_error(prayer_id: int, error_msg: str, raw_response: Optional[str] = None):
    """Log errors to the error log file."""
    error_entry = {
        "prayer_id": prayer_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "error": error_msg,
        "raw_response": raw_response
    }

    with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(error_entry, ensure_ascii=False) + "\n")


def load_progress() -> Dict[str, Any]:
    """Load progress from the progress file."""
    if Path(PROGRESS_FILE).exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_processed_id": 0, "total_processed": 0, "total_errors": 0}


def save_progress(progress: Dict[str, Any]):
    """Save progress to the progress file."""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)


def get_prayers_to_process(start_id: int = 0):
    """Get prayers that need to be processed."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT prayer_id, source_text, sefaria_ref, nusach, prayer_type,
               occasion, service, section, prayer_name, hebrew_text
        FROM prayers
        WHERE prayer_id > ?
          AND (canonicalization_status IS NULL OR canonicalization_status = 'pending')
        ORDER BY prayer_id
    """, (start_id,))

    prayers = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return prayers


def main():
    """Main pipeline execution."""
    parser = argparse.ArgumentParser(description='Canonicalize liturgy.db prayers')
    parser.add_argument('--resume', action='store_true', help='Resume from last processed prayer')
    parser.add_argument('--start-id', type=int, default=0, help='Start from specific prayer_id')
    args = parser.parse_args()

    print("=" * 80)
    print("LITURGICAL DATABASE CANONICALIZATION")
    print("=" * 80)
    print(f"Model: {GEMINI_MODEL}")
    print(f"Database: {DB_PATH}")
    print(f"Error Log: {ERROR_LOG_FILE}")
    print("=" * 80)

    # Setup database schema
    print("\nChecking database schema...")
    columns_added = setup_database()
    if columns_added:
        print(f"Added {len(columns_added)} new columns to prayers table:")
        for col in columns_added:
            print(f"  - {col}")
    else:
        print("All canonical columns already exist in database.")

    # Determine starting point
    start_id = 0
    if args.resume:
        progress = load_progress()
        start_id = progress["last_processed_id"]
        print(f"\nResuming from prayer_id {start_id + 1}")
        print(f"Previously processed: {progress['total_processed']}")
        print(f"Previous errors: {progress['total_errors']}")
    elif args.start_id:
        start_id = args.start_id
        print(f"\nStarting from prayer_id {start_id}")

    # Get prayers to process
    prayers = get_prayers_to_process(start_id)
    total_to_process = len(prayers)

    print(f"\nPrayers to process: {total_to_process}")
    print(f"\nStarting canonicalization...\n")

    # Load or initialize progress
    progress = load_progress() if args.resume else {"last_processed_id": 0, "total_processed": 0, "total_errors": 0}

    # Process each prayer
    processed_count = 0
    error_count = 0

    for i, prayer in enumerate(prayers, 1):
        prayer_id = prayer["prayer_id"]
        prayer_name = prayer.get("prayer_name", "Unnamed")

        print(f"[{i}/{total_to_process}] Prayer ID {prayer_id}: {prayer_name}")

        # Call Gemini API
        canonical_data = call_gemini_api(prayer)

        if canonical_data:
            # Update database
            update_prayer_in_db(prayer_id, canonical_data)
            print(f"  SUCCESS: {canonical_data.get('canonical_prayer_name', 'N/A')}")
            print(f"    L3: {canonical_data.get('L3_Signpost', 'N/A')}")
        else:
            error_count += 1
            update_prayer_in_db(prayer_id, None)
            print(f"  ERROR: Failed after {MAX_RETRIES} attempts")

        # Update progress
        processed_count += 1
        progress["last_processed_id"] = prayer_id
        progress["total_processed"] = progress.get("total_processed", 0) + 1
        progress["total_errors"] = progress.get("total_errors", 0) + (1 if not canonical_data else 0)

        # Save progress every 10 prayers
        if processed_count % 10 == 0:
            save_progress(progress)
            print(f"\n  Progress saved: {processed_count}/{total_to_process} completed\n")

        # Delay between API calls
        if i < total_to_process:
            time.sleep(API_DELAY)

    # Final progress save
    save_progress(progress)

    print("\n" + "=" * 80)
    print("CANONICALIZATION COMPLETE")
    print("=" * 80)
    print(f"Successfully processed: {processed_count - error_count}/{total_to_process}")
    print(f"Errors: {error_count}/{total_to_process}")
    print(f"Database updated: {DB_PATH}")
    if error_count > 0:
        print(f"Error log: {ERROR_LOG_FILE}")
    print("=" * 80)


if __name__ == "__main__":
    main()
