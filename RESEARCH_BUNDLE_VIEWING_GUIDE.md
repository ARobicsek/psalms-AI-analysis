# Research Bundle Viewing Guide

This guide explains how to view the liturgical research bundles that are generated for commentary writing.

## Quick Start

View the research bundle for any psalm:

```bash
python view_research_bundle.py [psalm_number]
```

Examples:
```bash
# View Psalm 1 research bundle
python view_research_bundle.py 1

# View Psalm 23 research bundle
python view_research_bundle.py 23

# View Psalm 145 research bundle
python view_research_bundle.py 145
```

## Output Formats

### Text Format (Default)
Human-readable format showing the complete research bundle:

```bash
python view_research_bundle.py 1
```

Output file: `research_bundle_psalm1_YYYYMMDD_HHMMSS.txt`

### JSON Format
Machine-readable format (useful for programmatic access):

```bash
python view_research_bundle.py 1 --format json
```

Output file: `research_bundle_psalm1_YYYYMMDD_HHMMSS.json`

### Both Formats
Generate both text and JSON:

```bash
python view_research_bundle.py 1 --format both
```

## What You'll See

The research bundle contains two main sections:

### Section 1: Full Psalm Recitations

Shows where the entire psalm is recited in liturgy:
- Prayer name and metadata
- Canonical classification (L1-L4)
- Location description
- **LLM Summary**: Narrative summary of the full psalm's liturgical usage

### Section 2: Phrase-Level Usage

Shows where specific phrases from the psalm appear:
- Hebrew phrase text
- Verse range
- All liturgical contexts where this phrase appears
- **LLM Summary**: Scholarly commentary on this phrase's usage

## Console Output

While running, you'll see:
- `[FILTER]` messages showing what phrases were filtered out
- LLM validation steps
- Token usage and costs
- Generation progress

## Understanding the Output

### Full Psalm Recitations
These are the most significant - they show where worshippers recite the entire psalm.

**Example**:
```
Prayer: Aleinu
Nusach: Edot_HaMizrach
Service: Maariv
Occasion: Yom Kippur
```

### Phrase Groups
These show where specific phrases appear, even when the full psalm isn't recited.

**Key Fields**:
- `is_unique: 1` = Phrase unique to this psalm (included)
- `is_unique: 0` = Phrase appears in other psalms (filtered out)
- `match_type: phrase_match` = Partial phrase
- `match_type: exact_verse` = Complete verse

### LLM Summaries
The summaries are what get used for commentary generation. They provide:
- Historical/liturgical context
- Hebrew quotations from liturgy
- Theological significance
- Cross-tradition comparisons

## Tips for Reviewing

1. **Check filtering**: Console output shows `[FILTER]` messages for excluded phrases
2. **Verify is_unique**: All phrase_match items should have `is_unique: 1`
3. **Read summaries**: These are the scholarly narratives used in commentary
4. **Note validation**: Some phrase groups may have validation notes

## What Gets Passed to Commentary Agents

This exact research bundle structure is passed to:
1. **Master Editor**: Receives the bundle to create commentary structure
2. **Synthesis Writer**: Uses the summaries to write final commentary

## Files Generated

Each run creates timestamped files:
- `research_bundle_psalm{N}_YYYYMMDD_HHMMSS.txt` (text format)
- `research_bundle_psalm{N}_YYYYMMDD_HHMMSS.json` (JSON format)

You can keep multiple versions to compare changes over time.

## Common Issues

### No phrase groups found
This is normal for psalms that:
- Only appear as full recitations
- Have no unique phrases in liturgy
- Are rarely used in Jewish prayer

### Unicode errors in console
The script handles this - check the output files which have proper UTF-8 encoding.

### LLM costs
Each psalm generates:
- 1 LLM call for full psalm summary (if full recitations exist)
- 1 LLM call per phrase group
- Validation calls (with pre-filtering to minimize)

## Testing Different Psalms

Try these to see different patterns:

- **Psalm 1**: Full recitations + unique phrases
- **Psalm 23**: Very common, many phrase-level uses
- **Psalm 145**: Full recitation in daily prayers
- **Psalm 29**: Festival-specific usage
- **Psalm 92**: Shabbat-specific psalm

## Next Steps

Once you review the research bundle:
1. Verify it looks correct
2. Use it for commentary generation
3. Provide feedback on any issues

The research bundle is the foundation for all commentary work!
