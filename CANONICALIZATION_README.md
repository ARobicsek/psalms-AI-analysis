# Liturgical Database Canonicalization

This directory contains scripts to enrich the `liturgy.db` database with hierarchical, canonicalized metadata using the Gemini API.

## Overview

The canonicalization process adds 9 new fields to each prayer in `liturgy.db`:

| Field | Description |
|-------|-------------|
| `canonical_L1_Occasion` | Top-level occasion (e.g., "Weekday", "Shabbat", "Rosh Hashanah") |
| `canonical_L2_Service` | Service name (e.g., "Shacharit", "Mincha", "Arvit", "Mussaf") |
| `canonical_L3_Signpost` | Major liturgical milestone (from canonical list - REQUIRED) |
| `canonical_L4_SubSection` | Granular sub-section (e.g., "Birkhot HaShachar") |
| `canonical_prayer_name` | Standardized prayer name |
| `canonical_usage_type` | Nature of the text (e.g., "Full Psalm Recitation", "Tefillah") |
| `canonical_location_description` | Human-readable context (1-2 sentences) |
| `canonicalization_timestamp` | When the entry was processed |
| `canonicalization_status` | Status: `pending`, `completed`, or `error` |

## Scripts

### 1. `preview_db_changes.py`
Preview what changes will be made to the database **without modifying anything**.

```bash
python preview_db_changes.py
```

### 2. `canonicalize_liturgy_db.py`
**Main script** - Process all prayers and write canonicalized fields to `liturgy.db`.

```bash
# Process all prayers from the beginning
python canonicalize_liturgy_db.py

# Resume from last processed prayer (after interruption)
python canonicalize_liturgy_db.py --resume

# Start from a specific prayer_id
python canonicalize_liturgy_db.py --start-id 500
```

### 3. Test Scripts (for validation)
- `test_liturgical_canonicalizer.py` - Test first 3 prayers
- `test_specific_prayers.py` - Test specific prayer IDs (100, 200, 300, etc.)

## Process Details

### What Happens During Canonicalization

1. **Schema Update**: Adds 9 new columns to the `prayers` table (if not already present)
2. **API Processing**: For each prayer:
   - Sends prayer data to Gemini API (`gemini-2.5-pro`)
   - Receives canonicalized metadata
   - Updates the database with new fields
3. **Progress Tracking**: Saves progress every 10 prayers to `logs/canonicalization_db_progress.json`
4. **Error Handling**: Logs errors to `logs/canonicalization_db_errors.jsonl`

### Estimated Time

- **Total prayers**: 1,123
- **Average time per prayer**: ~2 seconds (including API delay)
- **Total estimated time**: ~37 minutes

### Resume Capability

The script is **fully resumable**. If interrupted:
```bash
python canonicalize_liturgy_db.py --resume
```

Progress is automatically saved every 10 prayers.

## Requirements

- Python 3.7+
- `google-generativeai` package
- `python-dotenv` package
- `.env` file with `GEMINI_API_KEY`

## Output

After completion, the `liturgy.db` database will have all 1,123 prayers enriched with hierarchical metadata. You can query them like:

```sql
-- Find all prayers in Pesukei Dezimra
SELECT prayer_id, canonical_prayer_name, canonical_L3_Signpost
FROM prayers
WHERE canonical_L3_Signpost LIKE '%Pesukei Dezimra%';

-- Get all Shabbat Shacharit prayers
SELECT prayer_id, canonical_prayer_name, canonical_location_description
FROM prayers
WHERE canonical_L1_Occasion = 'Shabbat'
  AND canonical_L2_Service = 'Shacharit';

-- View canonicalization status
SELECT
  canonicalization_status,
  COUNT(*) as count
FROM prayers
GROUP BY canonicalization_status;
```

## Error Recovery

If prayers fail during processing:
1. Check `logs/canonicalization_db_errors.jsonl` for details
2. Prayers with errors are marked with `canonicalization_status = 'error'`
3. To retry failed prayers:
   ```sql
   UPDATE prayers SET canonicalization_status = NULL WHERE canonicalization_status = 'error';
   ```
4. Then run: `python canonicalize_liturgy_db.py --resume`

## Files Generated

| File | Purpose |
|------|---------|
| `logs/canonicalization_db_progress.json` | Progress tracking (last prayer_id, counts) |
| `logs/canonicalization_db_errors.jsonl` | Error log (one error per line, JSON format) |

## Notes

- The script uses a 0.5 second delay between API calls to respect rate limits
- Each API call retries up to 3 times on failure
- Original prayer data is never modified - only new canonical fields are added
- The database is updated incrementally (transaction per prayer)
