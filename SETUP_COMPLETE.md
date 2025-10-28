# Liturgical Canonicalization Pipeline - Ready to Run

## Summary

I've created a complete pipeline to enrich your `liturgy.db` database with hierarchical, canonicalized metadata using Gemini 2.5 Pro. The test results look excellent!

## Test Results

Tested on 8 diverse prayers (IDs: 100, 200, 300, 400, 500, 600, 700, 800):
- ✅ All successfully canonicalized
- ✅ Rich contextual descriptions
- ✅ Proper handling of composite text blocks
- ✅ Accurate liturgical categorization

**Example output from Prayer ID 700 (Birkhot K'riat Shema - Maariv):**
- **L3_Signpost**: "Birkhot K'riat Shema"
- **Location**: "This is a complete, composite block for the Shema and its blessings for the Maariv service. It begins with the two blessings preceding the Shema..."
- **Usage Type**: "Congregational"

## Scripts Created

| Script | Purpose |
|--------|---------|
| `preview_db_changes.py` | Preview schema changes (no modifications) |
| `canonicalize_liturgy_db.py` | **Main script** - Process all prayers |
| `check_canonicalization_status.py` | Check progress and status |
| `CANONICALIZATION_README.md` | Full documentation |

## How to Run

### Step 1: Preview Changes (Optional but Recommended)
```bash
python preview_db_changes.py
```

### Step 2: Start Canonicalization
```bash
python canonicalize_liturgy_db.py
```

### Step 3: Monitor Progress
Open another terminal and run:
```bash
python check_canonicalization_status.py
```

### Step 4: Resume if Interrupted
```bash
python canonicalize_liturgy_db.py --resume
```

## What Gets Added to Database

9 new columns will be added to the `prayers` table:

```
canonical_L1_Occasion              (e.g., "Weekday", "Shabbat", "Rosh Hashanah")
canonical_L2_Service               (e.g., "Shacharit", "Mincha", "Arvit")
canonical_L3_Signpost              (e.g., "Pesukei Dezimra", "Birkhot K'riat Shema")
canonical_L4_SubSection            (e.g., "Birkhot HaShachar", "Halleluyah Psalms")
canonical_prayer_name              (e.g., "Modeh Ani", "Ashrei")
canonical_usage_type               (e.g., "Standard", "Core Liturgy", "Congregational")
canonical_location_description     (e.g., "Recited immediately upon waking...")
canonicalization_timestamp         (e.g., "2025-10-28 17:30:45")
canonicalization_status            ("completed", "error", or NULL)
```

## Key Features

✅ **Resumable** - Progress saved every 10 prayers
✅ **Error Handling** - Failed prayers logged, can be retried
✅ **Non-Destructive** - Original data never modified
✅ **Progress Tracking** - Real-time status updates
✅ **Incremental Updates** - Database updated prayer-by-prayer

## Estimated Runtime

- **Total prayers**: 1,123
- **Estimated time**: ~37 minutes
- **Model**: gemini-2.5-pro
- **Rate**: ~2 seconds per prayer (including API delay)

## After Completion

You can query the enriched data like:

```sql
-- All Pesukei Dezimra prayers
SELECT prayer_id, canonical_prayer_name
FROM prayers
WHERE canonical_L3_Signpost LIKE '%Pesukei Dezimra%';

-- View canonicalization summary
SELECT canonical_L3_Signpost, COUNT(*) as count
FROM prayers
WHERE canonicalization_status = 'completed'
GROUP BY canonical_L3_Signpost
ORDER BY count DESC;
```

## Files & Logs

| File | Location |
|------|----------|
| Progress tracking | `logs/canonicalization_db_progress.json` |
| Error log | `logs/canonicalization_db_errors.jsonl` |
| Test results | `output/test_diverse_sample.jsonl` |

## Ready to Go!

The database is untouched and ready. When you're ready to begin:

```bash
python canonicalize_liturgy_db.py
```

---

**Note**: You can stop the process at any time (Ctrl+C) and resume later with `--resume` flag.
