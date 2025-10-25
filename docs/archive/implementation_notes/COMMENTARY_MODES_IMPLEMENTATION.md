# Commentary Modes Implementation

## Overview

The pipeline now supports two modes for requesting traditional Jewish commentaries:

1. **Default Mode ("all")**: Requests ALL 7 commentaries for ALL verses in the psalm
2. **Selective Mode ("selective")**: Only requests commentaries for verses that the micro analyst specifically identifies as puzzling, complex, or meriting traditional interpretation

## Usage

### Default Mode (All Commentaries)

Run the pipeline normally without any special flags:

```bash
python scripts/run_enhanced_pipeline.py 1
```

This will:
- Request commentary from all 7 commentators (Rashi, Ibn Ezra, Radak, Metzudat David, Malbim, Meiri, Torah Temimah)
- Request commentary for EVERY verse in the psalm
- Provide comprehensive traditional grounding for the Synthesis Writer and Master Editor

### Selective Mode (Targeted Commentaries)

Use the `--skip-default-commentaries` flag:

```bash
python scripts/run_enhanced_pipeline.py 1 --skip-default-commentaries
```

This will:
- Request commentary from all 7 commentators
- ONLY request commentary for 3-8 verses that are genuinely puzzling, complex, or merit traditional interpretation
- Focus on interpretive puzzles, rare vocabulary, complex syntax, theologically loaded passages, and unusual imagery
- Be more judicious about which verses receive commentary attention

## Implementation Details

### Modified Files

1. **`src/agents/micro_analyst.py`**:
   - Added `commentary_mode` parameter to `__init__()` method
   - Created two commentary instruction templates:
     - `COMMENTARY_ALL_VERSES`: Instructions for requesting all verses
     - `COMMENTARY_SELECTIVE`: Instructions for selective requests
   - Updated `_generate_research_requests()` to inject the appropriate instructions based on mode
   - Added validation to ensure mode is either "all" or "selective"

2. **`scripts/run_enhanced_pipeline.py`**:
   - Added `skip_default_commentaries` parameter to `run_enhanced_pipeline()` function
   - Added `--skip-default-commentaries` command-line argument
   - Updated both MicroAnalystV2 instantiations to pass `commentary_mode` parameter
   - Added logging to indicate which commentary mode is being used

### Commentary Instructions

#### All Verses Mode
```
**REQUEST COMMENTARY FOR EVERY VERSE** in the psalm
- All 7 available commentators will be consulted
- Provide a brief reason explaining what aspect of each verse merits traditional commentary perspective
- This comprehensive approach ensures the Synthesis Writer has classical grounding for every verse
```

#### Selective Mode
```
**REQUEST COMMENTARY ONLY FOR VERSES** that are genuinely puzzling, complex, or merit traditional interpretation
- All 7 available commentators will be consulted
- Be selective and judicious: only request for 3-8 verses that would most benefit from classical commentary
- Focus on: interpretive puzzles, rare vocabulary, complex syntax, theologically loaded passages, unusual imagery
```

## Commentary Formatting

Commentaries are presented in a clean, organized format in the research bundle:

```markdown
### Psalms 1:1
**Reason for commentary request**: Opening beatitude - how do commentators interpret 'ashrei' and the threefold structure?

#### Rashi
**Hebrew**: [Hebrew text...]
**English**: [English translation...]

#### Ibn Ezra
**Hebrew**: [Hebrew text...]
**English**: [English translation...]

[... all 7 commentators ...]
```

## Rationale

### Default Mode (All Commentaries)
- **Pros**:
  - Comprehensive traditional perspective across all verses
  - Richer scholarly grounding for synthesis and editing
  - Better integration of classical sources throughout commentary
  - ~10-14% increase in research bundle size (manageable)
- **Use Case**: When you want maximum scholarly depth and traditional grounding

### Selective Mode
- **Pros**:
  - More focused use of commentaries where they add most value
  - Smaller research bundle (faster processing, lower token costs)
  - Commentary requests driven by actual discoveries and puzzles
- **Use Case**: When you want to be more targeted or when token costs are a concern

## Testing

To test both modes, you can run:

```bash
# Test default mode (all verses)
python scripts/run_enhanced_pipeline.py 1 --output-dir output/psalm_1_all_commentaries

# Test selective mode
python scripts/run_enhanced_pipeline.py 1 --output-dir output/psalm_1_selective_commentaries --skip-default-commentaries
```

Compare the resulting research bundles to see the difference:
- `output/psalm_1_all_commentaries/psalm_001_research_v2.md`
- `output/psalm_1_selective_commentaries/psalm_001_research_v2.md`

## Backward Compatibility

The default behavior is to use "all" mode, which matches the Session 12 implementation where all 7 commentaries were requested for all verses. Existing scripts and workflows will continue to work without modification.

## Future Enhancements

Potential future improvements:
1. Add commentary mode to pipeline statistics tracking
2. Add metrics comparing output quality between modes
3. Consider adding a "hybrid" mode that uses different criteria for selection
4. Add per-commentator selection (e.g., only request Rashi and Ibn Ezra)

## Session Context

This implementation was completed in response to the user's request to:
1. **ALWAYS provide ALL available commentaries** (7 commentators) in the research bundle (default behavior)
2. **ONLY provide selective commentaries** for verses where the micro analyst requests them (opt-in via `--skip-default-commentaries`)
3. Ensure clean and logically organized presentation of commentaries

The implementation preserves the Session 12 behavior as the default while adding flexibility for more selective commentary requests when desired.
