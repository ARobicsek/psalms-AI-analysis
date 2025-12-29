# Figurative Curator Integration Guide

This guide explains how to continue iterating on the Figurative Curator and integrate it into the main pipeline.

## Overview

The **Figurative Curator** is an LLM-enhanced agent that transforms raw figurative concordance data into interpretive insights. It uses Gemini 3 Pro with high reasoning (`thinking_level="high"`) to:

1. Execute searches against the figurative language database
2. Iteratively refine searches based on results
3. Curate 5-15 examples per vehicle with Hebrew text
4. Synthesize prose insights for commentary writers

## Current Location

- **Test script**: `scripts/test_figurative_curator.py`
- **Figurative DB**: `C:/Users/ariro/OneDrive/Documents/Bible/database/Biblical_fig_language.db`
- **Hebrew source**: `database/tanakh.db`

## Running the Test Script

```bash
# Basic usage (Psalm 23)
python scripts/test_figurative_curator.py

# Different psalm
python scripts/test_figurative_curator.py --psalm 22

# Dry run (no LLM calls, shows prompts)
python scripts/test_figurative_curator.py --dry-run

# Verbose output
python scripts/test_figurative_curator.py --verbose

# Save to specific file
python scripts/test_figurative_curator.py --psalm 23 --output output/psalm_23/curator_output.md
```

## Architecture

### Key Classes

```
FigurativeSearchRequest    - Input from micro analyst (vehicle + search terms)
FigurativeCuratorOutput    - Output with curated examples, insights, token usage
FigurativeCurator          - Main agent class
```

### Processing Flow

```
1. INITIAL SEARCHES
   - Execute micro analyst's figurative requests
   - Cap: 50 results per search (INITIAL_SEARCH_CAP)

2. PHASE 1: LLM ANALYSIS
   - Analyze results, identify gaps
   - Recommend follow-up searches
   - Thinking budget: 8192 tokens

3. ITERATIVE SEARCH LOOP (up to 3 iterations)
   - Execute follow-up searches (cap: 30 per search)
   - Review results with LLM
   - If gaps remain, request more searches
   - Thinking budget: 4096 tokens per review

4. PHASE 2: SYNTHESIS
   - Curate 5-15 examples per vehicle
   - Write 3-5 prose insights
   - Generate figurative structure summary
   - Thinking budget: 12288 tokens
```

### Cost Tracking

The curator tracks precise costs using Gemini 3 Pro pricing:

| Token Type | Cost per Million |
|------------|------------------|
| Input      | $2.00           |
| Output     | $12.00          |
| Thinking   | $12.00          |

Cost is accumulated per LLM call and stored in `token_usage["cost"]`.

Typical run: ~$0.15-0.25 per psalm.

## Key Configuration Constants

```python
MAX_ITERATIONS = 3           # Max review → search → review cycles
MIN_RESULTS_FOR_USEFUL = 1   # Even 1 result is useful
INITIAL_SEARCH_CAP = 50      # Results per initial search
FOLLOWUP_SEARCH_CAP = 30     # Results per follow-up search
```

## Output Format

### FigurativeCuratorOutput Fields

| Field | Type | Description |
|-------|------|-------------|
| `psalm_number` | int | The psalm analyzed |
| `curated_examples_by_vehicle` | Dict[str, List] | 5-15 examples per vehicle |
| `figurative_insights` | List[Dict] | 3-5 prose insights |
| `search_summary` | Dict | Search stats + vehicle_map |
| `iteration_log` | List[Dict] | Debug log of each iteration |
| `token_usage` | Dict | input, output, thinking, cost |
| `raw_llm_response` | str | Raw Phase 2 response |

### Curated Example Structure

```json
{
  "reference": "Isaiah 40:11",
  "type": "metaphor",
  "figurative_text_english": "Like a shepherd he tends his flock...",
  "figurative_text_hebrew": "כְּרֹעֶה עֶדְרוֹ יִרְעֶה",
  "full_verse_hebrew": "כְּרֹעֶה עֶדְרוֹ יִרְעֶה בִּזְרֹעוֹ...",
  "reason_selected": "Shows shepherd imagery at national scale"
}
```

### Figurative Structure Summary

The `vehicle_map` field adapts to psalm structure:

```json
{
  "structure_type": "journey|contrast|dominant_metaphor|chiastic|thematic_clusters|other",
  "structure": "shepherd (vv1-4) → host (v5) → permanent dweller (v6)",
  "structure_meaning": "Movement from pastoral dependence to temple presence",
  "key_elements": [
    {
      "element": "shepherd/sheep → host/guest transition",
      "location": "v5",
      "significance": "Shift from animal to human status"
    }
  ]
}
```

## Integration into Main Pipeline

### Step 1: Create Production Module

Move the curator class to `src/agents/figurative_curator.py`:

```python
# src/agents/figurative_curator.py
from src.agents.figurative_librarian import FigurativeLibrarian, FigurativeRequest

class FigurativeCurator:
    # Copy the class from test_figurative_curator.py
    # Remove test-specific code (argparse, sample requests, etc.)
    pass
```

### Step 2: Add to Research Assembler

The Research Assembler (`src/research/research_assembler.py`) already collects figurative data. Integrate the curator:

```python
# In ResearchAssembler.assemble_research()

from src.agents.figurative_curator import FigurativeCurator

def assemble_research(self, psalm_number: int, ...):
    # ... existing code ...

    # After collecting micro analyst figurative requests
    if self.config.use_figurative_curator:
        curator = FigurativeCurator(verbose=self.verbose)
        curator_output = curator.curate(psalm_number, figurative_requests)

        # Add to research bundle
        bundle.figurative_curator_output = curator_output
        bundle.figurative_insights = curator_output.figurative_insights
        bundle.curated_examples = curator_output.curated_examples_by_vehicle
```

### Step 3: Update Pipeline Config

Add configuration option in `src/config.py`:

```python
@dataclass
class PipelineConfig:
    # ... existing fields ...
    use_figurative_curator: bool = True
    figurative_curator_max_iterations: int = 3
```

### Step 4: Integrate Cost Tracking

The curator returns cost in `token_usage["cost"]`. Add to pipeline totals:

```python
# In run_enhanced_pipeline.py or cost tracking module

# After curator runs
if curator_output:
    pipeline_costs["figurative_curator"] = curator_output.token_usage.get("cost", 0.0)
    pipeline_costs["total"] += curator_output.token_usage.get("cost", 0.0)
```

### Step 5: Update Synthesis Agent

Modify the synthesis agent to use curator insights instead of raw concordance data:

```python
# In src/agents/synthesis_agent.py

def build_prompt(self, bundle):
    # Use curator's prose insights directly
    if bundle.figurative_insights:
        figurative_section = "\n\n".join([
            f"### {insight['title']}\n{insight['insight']}"
            for insight in bundle.figurative_insights
        ])
    else:
        # Fallback to old method
        figurative_section = self._format_raw_figurative_data(bundle)
```

## Testing Checklist

Before integration, verify:

- [ ] Test on Psalm 23 (journey structure) - should produce ~5 insights
- [ ] Test on Psalm 22 (contrast structure) - should adapt vehicle_map
- [ ] Test on Psalm 1 (binary contrast) - should identify wicked/righteous opposition
- [ ] Verify Hebrew text retrieval works for all book name formats
- [ ] Check cost tracking produces accurate totals
- [ ] Confirm no boolean syntax in LLM search requests (e.g., "rod OR staff" should fail)

## Common Issues

### 1. Search Returns 0 Results

**Cause**: LLM used boolean syntax or multi-word phrases.

**Fix**: Instructions in prompts explicitly prohibit this. If it persists, add more examples to the prompt.

### 2. Hebrew Lookup Fails

**Cause**: Book name format mismatch between figurative DB and tanakh.db.

**Fix**: The `book_name_map` in `_get_verse_hebrew()` handles this. Add missing mappings if needed.

### 3. High Token Usage

**Cause**: Too many iterations or large result sets.

**Fix**: Reduce `MAX_ITERATIONS` or lower search caps. Typical run should be ~100-150K tokens.

## Files to Modify for Integration

1. `src/agents/figurative_curator.py` - New file (extract from test script)
2. `src/research/research_assembler.py` - Add curator call
3. `src/config.py` - Add curator config options
4. `src/agents/synthesis_agent.py` - Use curator insights
5. `scripts/run_enhanced_pipeline.py` - Add cost tracking
6. `scripts/cost_report.py` - Include curator costs in report

## Sample Integration Diff

```python
# research_assembler.py changes

+ from src.agents.figurative_curator import FigurativeCurator

class ResearchAssembler:
    def assemble_research(self, psalm_number, ...):
        # ... existing figurative search code ...

+       # Curate figurative insights with LLM
+       if self.config.use_figurative_curator and figurative_requests:
+           curator = FigurativeCurator(
+               verbose=self.verbose,
+               max_iterations=self.config.figurative_curator_max_iterations
+           )
+           curator_output = curator.curate(psalm_number, figurative_requests)
+
+           # Track costs
+           self.costs["figurative_curator"] = curator_output.token_usage.get("cost", 0.0)
+
+           # Add to bundle
+           bundle.figurative_curator_output = curator_output
```

## Next Steps

1. Run test script on several psalms to validate output quality
2. Extract production class to `src/agents/`
3. Add unit tests in `tests/test_figurative_curator.py`
4. Integrate with research assembler
5. Update synthesis prompts to use curator insights
6. Add to pipeline cost tracking
