"""
Test script for specific prayer IDs across the database.
Tests: 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100
"""

import os
import json
import sqlite3
import time
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Configuration
DB_PATH = "data/liturgy.db"
OUTPUT_FILE = "output/test_diverse_sample.jsonl"
GEMINI_MODEL = "gemini-2.5-pro"
PRAYER_IDS = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100]

# Ensure output directory exists
Path("output").mkdir(exist_ok=True)

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

print(f"API Key found: {api_key[:10]}...{api_key[-5:]}")
print(f"Model: {GEMINI_MODEL}\n")

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
4. Your output must be a single, valid JSON object and nothing else."""


def create_user_prompt(prayer_data):
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


def main():
    print("=" * 70)
    print("TESTING DIVERSE SAMPLE OF PRAYERS")
    print("=" * 70)

    # Get specific prayers
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Build query for specific IDs
    placeholders = ','.join('?' * len(PRAYER_IDS))
    cursor.execute(f"""
        SELECT prayer_id, source_text, nusach, service, section, prayer_name,
               hebrew_text, occasion, sefaria_ref
        FROM prayers
        WHERE prayer_id IN ({placeholders})
        ORDER BY prayer_id
    """, PRAYER_IDS)

    prayers = [dict(row) for row in cursor.fetchall()]
    conn.close()

    print(f"\nFound {len(prayers)} prayers to process")
    print(f"Prayer IDs: {[p['prayer_id'] for p in prayers]}\n")

    # Clear output file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        pass

    # Process each prayer
    success_count = 0
    error_count = 0

    for i, prayer in enumerate(prayers, 1):
        prayer_id = prayer["prayer_id"]
        prayer_name = prayer.get("prayer_name", "Unnamed")

        print(f"[{i}/{len(prayers)}] Prayer ID {prayer_id}: {prayer_name}")
        print(f"  Nusach: {prayer.get('nusach', 'N/A')}")
        print(f"  Service: {prayer.get('service', 'N/A')}")
        print(f"  Section: {prayer.get('section', 'N/A')}")
        print(f"  Occasion: {prayer.get('occasion', 'N/A')}")
        print(f"  Text length: {len(prayer.get('hebrew_text', ''))} chars")

        try:
            # Create the model and prompt
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                system_instruction=SYSTEM_PROMPT
            )

            user_prompt = create_user_prompt(prayer)

            generation_config = genai.types.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )

            print("  Calling Gemini API...")
            response = model.generate_content(
                user_prompt,
                generation_config=generation_config
            )

            # Parse and save result
            result = json.loads(response.text)

            # Handle case where API returns an array instead of object
            if isinstance(result, list) and len(result) > 0:
                result = result[0]

            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")

            print(f"  SUCCESS!")
            print(f"    Canonical Name: {result.get('canonical_prayer_name', 'N/A')}")
            print(f"    L3_Signpost: {result.get('L3_Signpost', 'N/A')}")
            print(f"    L1_Occasion: {result.get('L1_Occasion', 'N/A')}")
            success_count += 1

        except Exception as e:
            error_count += 1
            print(f"  ERROR: {type(e).__name__}: {e}")
            print(f"    Raw response: {response.text if 'response' in locals() else 'No response'}")

        print()

        # Small delay between API calls
        if i < len(prayers):
            time.sleep(1)

    print("=" * 70)
    print("TEST COMPLETE")
    print(f"Success: {success_count}/{len(prayers)}")
    print(f"Errors: {error_count}/{len(prayers)}")
    print(f"Results saved to: {OUTPUT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
