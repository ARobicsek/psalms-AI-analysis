

# Developer Guide: Liturgical Text Canonicalization Pipeline

## 1\. Project Overview & "The Why"

### 1.1. Project Goal

The goal of this project is to pre-process our entire corpus of raw liturgical texts (from Sefaria and other sources) and transform them into a new, clean, and **hierarchically-aware** dataset. This new "canonical corpus" will serve as the ground truth for our main Psalms phrase-matching algorithm.

### 1.2. The Problem We Are Solving

Our current data, while textually complete, has "flat" and inconsistent metadata. This causes several major problems for our analysis:

  * **Inconsistent Naming:** The same prayer is often named differently across various texts (e.g., "LeDavid", "L'David Hashem", "Psalm 27").
  * **Lack of Context:** A prayer's name (e.g., "Mizmor LeDavid") provides no information about *where* it is recited. Our current metadata (e.g., `section: Aleinu`) is often inaccurate, grouping unrelated prayers together.
  * **False Groupings:** Our phrase-matcher incorrectly groups textually identical phrases that are used in different liturgical contexts (e.g., the phrase `יְהֹוָ֥ה הוֹשִׁ֑יעָה...` is used in both "Vehu Rachum" at the start of Arvit and in "Motzei Yom Kippur", but our current output clumps them together confusingly).
  * **"Clumped" Data:** Some source entries (like `prayer_id: 989` from the Yom Kippur Machzor) incorrectly bundle multiple, distinct liturgical sections (Yishtabach, Psalm 130, Kaddish, and Yotzer Or) into a single row with a misleading name.

### 1.3. The Solution

We will create a new pipeline that **runs before the phrase-matcher**. This pipeline will:

1.  Iterate through every prayer/row in our existing source files.
2.  For each row, make a call to the Gemini API.
3.  The API will analyze the prayer's text and its (messy) metadata.
4.  The API will return a **single, clean, and standardized JSON object** for that prayer, formatted according to our new **Canonical Schema**.
5.  This new JSON data will be saved, forming our new canonical corpus.

The phrase-matching algorithm will then be run against this new, clean dataset, which will have all the necessary context built-in.

-----

## 2\. The Canonical Data Schema

The output of the Gemini API *must* conform to the following JSON structure. This is the schema for our new, clean database.

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `original_prayer_id` | string/int | The `prayer_id` from the source file, for traceability. |
| `source_corpus` | string | The name of the source text (e.g., "siddur\_ashkenaz", "machzor\_yom\_kippur"). |
| `nusach` | string | Standardized nusach (e.g., "Ashkenaz", "Edot HaMizrach", "Sefard"). |
| `L1_Occasion` | string | The top-level calendar event (e.g., "Weekday", "Shabbat", "High Holy Day"). |
| `L2_Service` | string | The specific service (e.g., "Shacharit", "Mincha", "Arvit", "Mussaf"). |
| **`L3_Signpost`** | string | **CRITICAL:** The "major milestone" section of the service. *Must* be one of the provided canonical categories. |
| `L4_SubSection` | string | (Optional) A granular sub-section (e.g., "Birkhot HaShachar", "Halleluyah Psalms"). |
| `canonical_prayer_name` | string | The standardized, common name for this prayer (e.g., "Psalm 27", "Aleinu"). |
| `usage_type` | string | The nature of the text (e.g., "Full Psalm Recitation", "Piyyut", "Tefillah", "Instruction", "Liturgical Sequence"). |
| **`relative_location_description`** | string | **CRITICAL:** A 1-2 sentence human-readable description of *exactly* where this prayer is and, if it's a "clumped" block, what it contains. |
| `hebrew_text` | string | The full, original Hebrew text from the source file. |

-----

## 3\. Implementation: The Annotation Pipeline

Your script should perform the following steps:

1.  **Load Source Data:** Read a source file (e.g., `siddur_ashkenaz.txt`) line by line or as a list of objects.
2.  **Iterate:** Loop through each prayer entry in the source file.
3.  **Construct Prompt:** For each entry, create the detailed API prompt (see Section 4) by injecting the prayer's `prayer_id`, `nusach`, `prayer_name`, `hebrew_text`, etc., into the "Input Data" section of the prompt.
4.  **Call Gemini API:** Send the complete prompt to the Gemini API. Ensure you are requesting JSON output.
5.  **Process Response:**
      * **On Success:** Parse the JSON response from the API.
      * **On Failure/Error:** Implement robust error handling. Log the `original_prayer_id` and the error (e.g., API timeout, non-JSON response, malformed JSON). We may need to re-run these.
6.  **Save Clean Data:** Append the new, clean JSON object to our output file (e.g., `canonical_corpus.jsonl`). Using the JSON Lines format (`.jsonl`) is recommended, as it allows us to append one valid JSON object per line, which is resilient to interruption.

-----

## 4\. The Gemini API Prompt (The "Brain")

This is the core of the pipeline. The prompt must be structured as follows to ensure consistent, accurate, and parsable JSON output.

### 4.1. System Prompt (Role)

This preamble sets the context and rules for the AI.

> You are a world-class expert in Jewish liturgy (Ashkenaz, Sefard, and Edot HaMizrach) and a master data analyst. Your task is to remap an entry from a messy liturgical text database (provided as 'Input Data') into a new, clean, and consistent hierarchical JSON format, as specified by the 'Required Output Format'.
>
> **CRITICAL RULES:**
>
> 1.  You *must* use one of the provided **Canonical `L3_Signpost` Categories** for the `L3_Signpost` field. Do not invent new ones.
> 2.  The `L1_Occasion` and `L2_Service` fields must be standardized.
> 3.  **HANDLING "CLUMPED" TEXT:** The `hebrew_text` field may contain multiple, distinct liturgical sections (e.g., Yishtabach, followed by Psalm 130, followed by Kaddish, followed by Yotzer Or). You must analyze the *entire* text.
>       * The `L3_Signpost`, `L4_SubSection`, and `canonical_prayer_name` should reflect the **primary liturgical purpose** of the *entire* block (e.g., "Yotzer Or" in the example above, not "Yishtabach").
>       * The `relative_location_description` *must* explicitly describe this composite structure (e.g., "This block begins with Yishtabach, includes Psalm 130, and then contains the full Yotzer Or blessing...").
> 4.  Your output must be a single, valid JSON object and nothing else.

### 4.2. User Prompt (The Task)

```yaml
Please remap the following prayer entry into the new, standardized JSON schema.

---
### Canonical `L3_Signpost` Categories (Use one of these)
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
---

### Input Data (from source file)
{
  "prayer_id": [INJECT_PRAYER_ID_HERE],
  "source_corpus": [INJECT_SOURCE_CORPUS_NAME_HERE],
  "nusach": [INJECT_NUSACH_HERE],
  "service": [INJECT_SERVICE_HERE],
  "section": [INJECT_SECTION_HERE],
  "prayer_name": [INJECT_PRAYER_NAME_HERE],
  "hebrew_text": "[INJECT_FULL_HEBREW_TEXT_HERE]"
}
---

### Required Output Format (JSON only)
{
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
  "hebrew_text": "[INJECT_THE_SAME_FULL_HEBREW_TEXT_HERE]"
}
```

-----

## 5\. Example of "Clumped" Text Handling

This example demonstrates how the pipeline should handle the `prayer_id: 989` case, per the `CRITICAL RULES` in the prompt.

### 5.1. Messy Input

```json
{
  "prayer_id": 989,
  "source_corpus": "Machzor Yom Kippur Ashkenaz",
  "nusach": "Ashkenaz",
  "service": "Shacharit",
  "prayer_name": "Yishtabach",
  "hebrew_text": "יִשְׁתַּבַּח שִׁמְךָ לָעַד... (text of Yishtabach)... וְהוּא יִפְדֶּה אֶת־יִשְׂרָאֵל... (full text of Psalm 130)... יִתְגַּדַּל וְיִתְקַדַּשׁ... (full text of Kaddish)... בָּרְכוּ אֶת יְהֹוָה... (Barechu)... יוֹצֵר אוֹר וּבוֹרֵא חֽשֶׁךְ... (full text of Yotzer Or and all its Piyyutim)... וְאֵין דוֹמֶה לְךָ מוֹשִׁיעֵֽנוּ לִתְחִיַּת הַמֵּתִים:"
}
```

### 5.2. Correct Canonical Output (from API)

The API will correctly identify the *primary purpose* of this block (Yotzer Or) and use the `relative_location_description` to explain the "clump."

```json
{
  "original_prayer_id": 989,
  "source_corpus": "Machzor Yom Kippur Ashkenaz",
  "nusach": "Ashkenaz",
  "L1_Occasion": "High Holy Day",
  "L2_Service": "Shacharit",
  "L3_Signpost": "Birkhot K'riat Shema",
  "L4_SubSection": "Yotzer Or (with Piyyutim)",
  "canonical_prayer_name": "Yotzer Or (Yom Kippur)",
  "usage_type": "Liturgical Sequence",
  "relative_location_description": "This is a large, composite text block. It begins with Yishtabach (concluding Pesukei Dezimra), includes Psalm 130 and Chatzi Kaddish, and then contains the full Yotzer Or blessing (the first blessing of the Shema) along with all its associated Piyyutim for Yom Kippur.",
  "hebrew_text": "יִשְׁתַּבַּח שִׁמְךָ לָעַd... (full text)... וְאֵין דוֹמֶה לְךָ מוֹשִׁיעֵֽנוּ לִתְחִיַּת הַמֵּתִים:"
}
```