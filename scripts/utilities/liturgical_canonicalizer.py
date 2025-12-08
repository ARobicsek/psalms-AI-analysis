"""
Liturgical Canonicalization Pipeline
=====================================

This script processes raw liturgical texts from liturgy.db and transforms them
into a canonicalized format with hierarchical metadata using the Gemini API.

The output is a JSONL file where each line contains a single canonicalized prayer entry.
"""

import os
import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai

# Configuration
OUTPUT_FILE = "data/canonical_liturgy.jsonl"
ERROR_LOG_FILE = "logs/canonicalization_errors.jsonl"
PROGRESS_FILE = "logs/canonicalization_progress.json"
DB_PATH = "data/liturgy.db"
GEMINI_MODEL = "gemini-2.5-pro"  # Using Gemini 2.5 Pro
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Ensure logs directory exists
Path("logs").mkdir(exist_ok=True)

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

# Configure Gemini
genai.configure(api_key=api_key)

# L3 Signpost Categories (from the plan document)
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

# System prompt (the "brain" of the operation)
SYSTEM_PROMPT = """You are a world-class expert in Jewish liturgy (Ashkenaz, Sefard, and Edot HaMizrach) and a master data analyst. Your task is to remap an entry from a messy liturgical text database (provided as 'Input Data') into a new, clean, and consistent hierarchical JSON format, as specified by the 'Required Output Format'.

**CRITICAL RULES:**

1. You *must* use one of the provided **Canonical `L3_Signpost` Categories** for the `L3_Signpost` field. Do not invent new ones.
2. The `L1_Occasion` and `L2_Service` fields must be standardized.
3. **HANDLING "CLUMPED" TEXT:** The `hebrew_text` field may contain multiple, distinct liturgical sections (e.g., Yishtabach, followed by Psalm 130, followed by Kaddish, followed by Yotzer Or). You must analyze the *entire* text.
    * The `L3_Signpost`, `L4_SubSection`, and `canonical_prayer_name` should reflect the **primary liturgical purpose** of the *entire* block (e.g., "Yotzer Or" in the example above, not "Yishtabach").
    * The `relative_location_description` *must* explicitly describe this composite structure (e.g., "This block begins with Yishtabach, includes Psalm 130, and then contains the full Yotzer Or blessing...").
4. Your output must be a single, valid JSON object and nothing else."""


def create_user_prompt(prayer_data: Dict[str, Any]) -> str:
    """Construct the user prompt for a single prayer entry."""

    # Prepare input data JSON
    input_data = {
        "prayer_id": prayer_data["prayer_id"],
        "source_corpus": prayer_data.get("source_text", "Unknown"),
        "nusach": prayer_data.get("nusach", "Unknown"),
        "service": prayer_data.get("service", "Unknown"),
        "section": prayer_data.get("section", "Unknown"),
        "prayer_name": prayer_data.get("prayer_name", "Unknown"),
        "hebrew_text": prayer_data.get("hebrew_text", "")
    }

    # Construct the prompt exactly as specified in the plan
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
    """
    Call Gemini API to canonicalize a single prayer entry.
    Returns the canonicalized JSON or None on failure.
    """
    user_prompt = create_user_prompt(prayer_data)

    for attempt in range(MAX_RETRIES):
        try:
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                system_instruction=SYSTEM_PROMPT
            )

            # Configure to request JSON output
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,  # Low temperature for consistency
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
            print(f"  ⚠️  {error_msg}")
            if attempt == MAX_RETRIES - 1:
                log_error(prayer_data["prayer_id"], error_msg, response.text if 'response' in locals() else None)
                return None
            time.sleep(RETRY_DELAY)

        except Exception as e:
            error_msg = f"API error on attempt {attempt + 1}: {type(e).__name__}: {e}"
            print(f"  ⚠️  {error_msg}")
            if attempt == MAX_RETRIES - 1:
                log_error(prayer_data["prayer_id"], error_msg)
                return None
            time.sleep(RETRY_DELAY)

    return None


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


def save_canonical_entry(canonical_data: Dict[str, Any]):
    """Append a canonicalized entry to the output file."""
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(canonical_data, ensure_ascii=False) + "\n")


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


def get_prayers_from_db(start_id: int = 0):
    """Generator that yields prayers from the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    cursor = conn.cursor()

    cursor.execute("""
        SELECT prayer_id, source_text, sefaria_ref, nusach, prayer_type,
               occasion, service, section, prayer_name, hebrew_text
        FROM prayers
        WHERE prayer_id > ?
        ORDER BY prayer_id
    """, (start_id,))

    for row in cursor:
        yield dict(row)

    conn.close()


def main():
    """Main pipeline execution."""
    print("=" * 70)
    print("LITURGICAL CANONICALIZATION PIPELINE")
    print("=" * 70)
    print(f"Model: {GEMINI_MODEL}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Error Log: {ERROR_LOG_FILE}")
    print("=" * 70)

    # Load progress
    progress = load_progress()
    start_id = progress["last_processed_id"]

    if start_id > 0:
        print(f"\n🔄 Resuming from prayer_id {start_id + 1}")
        print(f"   Previously processed: {progress['total_processed']}")
        print(f"   Previous errors: {progress['total_errors']}\n")

    # Get total count for progress tracking
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM prayers WHERE prayer_id > ?", (start_id,))
    total_remaining = cursor.fetchone()[0]
    conn.close()

    print(f"📊 Total prayers to process: {total_remaining}\n")

    # Process each prayer
    processed_count = 0
    error_count = 0

    for prayer in get_prayers_from_db(start_id):
        prayer_id = prayer["prayer_id"]
        prayer_name = prayer.get("prayer_name", "Unnamed")

        print(f"[{processed_count + 1}/{total_remaining}] Processing prayer_id {prayer_id}: {prayer_name}...")

        # Call Gemini API
        canonical_data = call_gemini_api(prayer)

        if canonical_data:
            # Save the result
            save_canonical_entry(canonical_data)
            print(f"  ✅ Canonicalized as: {canonical_data.get('canonical_prayer_name', 'N/A')}")
        else:
            error_count += 1
            print(f"  ❌ Failed after {MAX_RETRIES} attempts (logged to error file)")

        # Update progress
        processed_count += 1
        progress["last_processed_id"] = prayer_id
        progress["total_processed"] = progress.get("total_processed", 0) + 1
        progress["total_errors"] = progress.get("total_errors", 0) + (1 if not canonical_data else 0)

        # Save progress every 10 prayers
        if processed_count % 10 == 0:
            save_progress(progress)
            print(f"\n💾 Progress saved (processed: {processed_count}, errors: {error_count})\n")

        # Small delay to respect API rate limits
        time.sleep(0.5)

    # Final progress save
    save_progress(progress)

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"✅ Successfully processed: {processed_count - error_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📁 Output file: {OUTPUT_FILE}")
    print(f"📁 Error log: {ERROR_LOG_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
