# Pipeline Summary Integration Guide

## Overview

The `PipelineSummaryTracker` module provides comprehensive statistics tracking throughout the enhanced pipeline run. It captures detailed information about:

1. **Token/character counts** for each pipeline step
2. **Research requests** with full details (lexicon, concordance, figurative, commentary)
3. **Research bundle returns** with counts per category
4. **Ugaritic parallels** from RAG context
5. **Analysis questions** from Macro and Micro agents
6. **Execution timing** for each step

## Module Location

**File**: `c:\Users\ariro\OneDrive\Documents\Psalms\src\utils\pipeline_summary.py`

## Key Components

### 1. PipelineSummaryTracker Class

The main tracker class that accumulates statistics throughout the pipeline.

```python
from src.utils.pipeline_summary import PipelineSummaryTracker

# Initialize at start of pipeline
tracker = PipelineSummaryTracker(psalm_number=23)
```

### 2. Tracking Methods

#### Track Step Input/Output
```python
# Track input to a pipeline step
tracker.track_step_input("macro_analysis", input_text)

# Track output from a pipeline step (with optional duration)
tracker.track_step_output("macro_analysis", output_text, duration=45.3)
```

#### Track Research Requests
```python
# After generating research requests in MicroAnalyst
tracker.track_research_requests(research_request)
```

#### Track Research Bundle
```python
# After assembling research bundle
tracker.track_research_bundle(research_bundle)
```

#### Track Analysis Questions
```python
# Track questions from MacroAnalyst
tracker.track_macro_questions(macro_analysis.research_questions)

# Track questions from MicroAnalyst
tracker.track_micro_questions(micro_analysis.interesting_questions)
```

#### Track Verse Count
```python
# Track total verse count in psalm
tracker.track_verse_count(len(psalm.verses))
```

### 3. Report Generation

```python
# Mark pipeline complete
tracker.mark_pipeline_complete()

# Generate and save markdown report
summary_file = tracker.save_report(output_dir)

# Save JSON statistics
json_file = tracker.save_json(output_dir)
```

## Integration in run_enhanced_pipeline.py

The tracker has been integrated into `scripts/run_enhanced_pipeline.py` at the following points:

### Initialization (Line ~77)
```python
# Initialize pipeline summary tracker
tracker = PipelineSummaryTracker(psalm_number=psalm_number)
logger.info("Pipeline summary tracking enabled")
```

### Step 1: Macro Analysis (Lines ~104-130)
```python
step_start = time.time()

# Track input
psalm_text = "\n".join([f"{v.verse}: {v.hebrew} / {v.english}" for v in psalm.verses])
tracker.track_step_input("macro_analysis", psalm_text)
tracker.track_verse_count(len(psalm.verses))

# ... run macro analysis ...

# Track output
macro_output = macro_analysis.to_markdown()
step_duration = time.time() - step_start
tracker.track_step_output("macro_analysis", macro_output, duration=step_duration)

# Track macro questions
if macro_analysis.research_questions:
    tracker.track_macro_questions(macro_analysis.research_questions)
```

### Step 2: Micro Analysis (Lines ~153-183)
```python
step_start = time.time()

# Track input
tracker.track_step_input("micro_analysis", macro_analysis.to_markdown())

# ... run micro analysis ...

# Track output
micro_output = micro_analysis.to_markdown() + "\n\n" + research_bundle.to_markdown()
step_duration = time.time() - step_start
tracker.track_step_output("micro_analysis", micro_output, duration=step_duration)

# Track research requests and bundle
tracker.track_research_requests(research_bundle.request)
tracker.track_research_bundle(research_bundle)

# Track micro questions
if micro_analysis.interesting_questions:
    tracker.track_micro_questions(micro_analysis.interesting_questions)
```

### Step 3: Synthesis (Lines ~204-230)
```python
step_start = time.time()

# Track input
with open(research_file, 'r', encoding='utf-8') as f:
    research_content = f.read()
synthesis_input = macro_analysis.to_markdown() + "\n\n" + micro_output + "\n\n" + research_content
tracker.track_step_input("synthesis", synthesis_input)

# ... run synthesis ...

# Track output
synthesis_output = commentary['introduction'] + "\n\n" + commentary['verse_commentary']
step_duration = time.time() - step_start
tracker.track_step_output("synthesis", synthesis_output, duration=step_duration)
```

### Step 4: Master Editor (Lines ~254-288)
```python
step_start = time.time()

# Track input
with open(synthesis_intro_file, 'r', encoding='utf-8') as f:
    intro_content = f.read()
with open(synthesis_verses_file, 'r', encoding='utf-8') as f:
    verses_content = f.read()
editor_input = intro_content + "\n\n" + verses_content
tracker.track_step_input("master_editor", editor_input)

# ... run master editor ...

# Track output
editor_output = result['assessment'] + "\n\n" + result['revised_introduction'] + "\n\n" + result['revised_verses']
step_duration = time.time() - step_start
tracker.track_step_output("master_editor", editor_output, duration=step_duration)
```

### Pipeline Complete (Lines ~350-363)
```python
# Mark pipeline complete and generate summary
tracker.mark_pipeline_complete()

logger.info("\n[SUMMARY] Generating pipeline summary report...")
try:
    summary_file = tracker.save_report(str(output_path))
    summary_json = tracker.save_json(str(output_path))
    logger.info(f"✓ Pipeline summary saved to {summary_file}")
    logger.info(f"✓ Pipeline statistics saved to {summary_json}")
    print(f"\n✓ Pipeline summary: {summary_file}")
    print(f"✓ Pipeline statistics: {summary_json}")
except Exception as e:
    logger.error(f"Error generating pipeline summary: {e}")
    print(f"\n⚠ Warning: Could not generate pipeline summary: {e}")
```

## Output Files

The tracker generates two output files in the output directory:

### 1. Markdown Report
**Filename**: `psalm_XXX_pipeline_summary.md`

Contains:
- Pipeline steps overview table (with char/token counts and duration)
- Research requests detailed tables
  - Lexicon requests (word + reason)
  - Concordance searches (query, scope, level, purpose)
  - Figurative language searches (verse, vehicle terms, reason)
  - Commentary requests (verse + reason)
- Research bundle returns
  - Lexicon entries count
  - Concordance results per query
  - Figurative instances per search
  - Commentary counts per commentator
  - Ugaritic parallels table
- Analysis questions
  - MacroAnalyst research questions
  - MicroAnalyst interesting questions
- Token usage summary (estimated)

### 2. JSON Statistics
**Filename**: `psalm_XXX_pipeline_stats.json`

Machine-readable JSON containing all tracked statistics for further analysis or processing.

## Example Usage

### Running the Pipeline with Tracking
```bash
python scripts/run_enhanced_pipeline.py 23 --output-dir output/psalm_23
```

This will automatically:
1. Track all statistics throughout the pipeline
2. Generate `output/psalm_23/psalm_023_pipeline_summary.md`
3. Generate `output/psalm_23/psalm_023_pipeline_stats.json`

### Accessing Summary in Code
```python
from src.utils.pipeline_summary import PipelineSummaryTracker

# Load existing statistics
import json
with open('output/psalm_23/psalm_023_pipeline_stats.json', 'r') as f:
    stats = json.load(f)

print(f"Total tokens used: {stats['steps']['macro_analysis']['input_token_estimate']}")
print(f"Lexicon entries: {stats['research']['lexicon_entries_count']}")
```

## Report Format Example

```markdown
# Pipeline Summary Report: Psalm 23

**Generated**: 2025-10-19 14:30:00
**Total Pipeline Duration**: 458.3 seconds (7.6 minutes)

---

## Table of Contents
1. [Pipeline Steps Overview](#pipeline-steps-overview)
2. [Research Requests](#research-requests)
3. [Research Bundle Returns](#research-bundle-returns)
4. [Analysis Questions](#analysis-questions)
5. [Token Usage Summary](#token-usage-summary)

---

## Pipeline Steps Overview

| Step | Input Chars | Input Tokens (est) | Output Chars | Output Tokens (est) | Duration (s) |
|------|-------------|-------------------|--------------|---------------------|--------------|
| macro_analysis | 2,456 | 819 | 5,432 | 1,811 | 45.3 |
| micro_analysis | 5,432 | 1,811 | 45,678 | 15,226 | 67.8 |
| synthesis | 52,110 | 17,370 | 12,345 | 4,115 | 234.5 |
| master_editor | 12,345 | 4,115 | 13,567 | 4,522 | 110.7 |

---

## Research Requests

### Lexicon Requests (25)

| # | Hebrew Word | Reason |
|---|-------------|--------|
| 1 | רעה | Central to sevenfold anaphora - need semantic range and theological uses |
| 2 | מַבּוּל | Rare word (flood) - need etymology and comparative ANE usage |
...

### Concordance Searches (8)

| # | Query | Scope | Level | Purpose |
|---|-------|-------|-------|---------|
| 1 | קול יהוה | Psalms | consonantal | Track 'voice of LORD' formula usage patterns |
...

### Figurative Language Searches (12)

| # | Verse | Vehicle Terms | Reason |
|---|-------|---------------|--------|
| 1 | 3 | waters, water, sea, seas | Waters as primordial chaos imagery - vivid and theological... |
...

---

## Research Bundle Returns

### Lexicon Entries
**Total entries returned**: 23

### Concordance Results
| Query | Results Count |
|-------|---------------|
| קול יהוה | 42 |
...

**Total concordance results**: 156

### Figurative Language Results
| Query/Verse | Instances Found |
|-------------|-----------------|
| v29:3 | 15 |
...

**Total figurative instances**: 87

---

## Analysis Questions

### MacroAnalyst Research Questions (5)
1. What is the significance of the shepherd imagery?
2. How does the psalm structure contribute to its meaning?
...

### MicroAnalyst Interesting Questions (8)
1. Why does the poet use 'green pastures' specifically?
2. What is the function of the 'valley of shadow' metaphor?
...

---

## Token Usage Summary

**Total Input Tokens (estimated)**: 24,115
**Total Output Tokens (estimated)**: 25,674
**Total Tokens (estimated)**: 49,789

*Note: Token estimates are approximate (character count / 3). Actual API usage may vary.*
```

## Benefits

1. **Transparency**: Full visibility into what research was requested and returned
2. **Cost Tracking**: Token estimates help predict API costs
3. **Performance Monitoring**: Duration tracking identifies bottlenecks
4. **Reproducibility**: Complete record of pipeline execution for debugging
5. **Research Audit**: Detailed record of all research requests for scholarly review
6. **Quality Control**: Easy to verify that appropriate research was conducted

## Testing

You can test the tracker module standalone:

```bash
python src/utils/pipeline_summary.py --psalm 23 --output-dir output/test
```

This will create sample reports demonstrating the output format.

## Future Enhancements

Potential additions:
- API cost estimation (based on token counts and model pricing)
- Comparison between runs (track changes over pipeline iterations)
- Performance metrics (tokens per second, etc.)
- Warning system for unusually high token counts
- Automatic budget alerts

## Notes

- Token estimates use a conservative ratio (character count / 3) which works well for mixed Hebrew/English content
- Actual API token usage may vary from estimates
- The tracker is designed to be non-intrusive - errors in tracking won't stop the pipeline
- All tracking is synchronous and adds minimal overhead to pipeline execution
