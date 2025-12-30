# Figurative Curator Integration Guide

This guide explains how to continue iterating on the Figurative Curator and integrate it into the main pipeline.

## Overview

The **Figurative Curator** is an LLM-enhanced agent that transforms raw figurative concordance data into interpretive insights. It uses Gemini 3 Pro with high reasoning (`thinking_level="high"`) to:

1. Execute searches against the figurative language database
2. Iteratively refine searches based on results
3. Curate 5-15 examples per vehicle with Hebrew text
4. Synthesize 4-5 prose insights for commentary writers

## Current Location

- **Test script**: `scripts/test_figurative_curator.py`
- **Figurative DB**: `C:/Users/ariro/OneDrive/Documents/Bible/database/Biblical_fig_language.db`
- **Hebrew source**: `database/tanakh.db`
- **Output**: `output/psalm_NN/figurative_curator_output.md` (auto-saved)

## Running the Test Script

```bash
# Basic usage (Psalm 23) - outputs to output/psalm_23/figurative_curator_output.md
python scripts/test_figurative_curator.py --psalm 23

# Different psalm
python scripts/test_figurative_curator.py --psalm 22

# Dry run (no LLM calls, shows prompts)
python scripts/test_figurative_curator.py --psalm 23 --dry-run

# Verbose output
python scripts/test_figurative_curator.py --psalm 22 --verbose

# Save to specific file (overrides auto-save location)
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
   - Curate 5-15 examples per vehicle (for ALL vehicles with results)
   - Write 4-5 prose insights (100-150 words each)
   - Generate figurative structure summary with appropriate structure_type
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

Typical run: ~$0.30-0.50 per psalm (with comprehensive output).

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
| `curated_examples_by_vehicle` | Dict[str, List] | 5-15 examples per vehicle (ALL vehicles) |
| `figurative_insights` | List[Dict] | 4-5 prose insights (100-150 words each) |
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

The `vehicle_map` field adapts to psalm structure. Available structure types:

| Structure Type | When to Use |
|---------------|-------------|
| `journey` | Clear spatial/temporal progression (Ps 23: pasture → valley → table → house) |
| `descent` | Movement from suffering to deeper suffering |
| `descent_ascent` | From despair to hope, danger to deliverance (Ps 22) |
| `contrast` | Binary opposition (wicked vs. righteous, death vs. life) |
| `dominant_metaphor` | One vehicle controls entire psalm |
| `chiastic` | Vehicles mirror around a center point |
| `thematic_clusters` | Vehicles group by domain rather than sequence |
| `lament_structure` | Complaint → petition → confidence → praise |
| `other` | With explanation |

Example for Psalm 22 (descent_ascent):
```json
{
  "structure_type": "descent_ascent",
  "structure": "Abandonment (v2) → Bodily Dissolution (vv15-16) → Predator Attack (vv13-18) → Deliverance Hope (vv19-31)",
  "structure_meaning": "Figurative language tracks descent into animalistic noise and physical disintegration, followed by sudden restoration",
  "key_elements": [
    {
      "element": "Roaring (Human vs Beast)",
      "location": "vv2, 14",
      "significance": "Blurring of human/animal lines in suffering"
    }
  ]
}
```

## Integration into Main Pipeline

### CRITICAL Integration Reminders

Before integrating the Figurative Curator, address these three items:

#### 1. Remove Figurative Trimming Logic

The research bundle currently has trimming logic that reduces the size of figurative output when the bundle is too large. **This must be removed** for curator output since the data is now pre-curated by the LLM.

**Files to check:**
- `src/research/research_assembler.py` - Look for figurative trimming/truncation code
- Any bundle size limiting that affects figurative data

**Why:** The curator's output is already optimized (5-15 curated examples per vehicle, 4-5 prose insights). Trimming this would destroy the carefully selected examples.

#### 2. Incorporate Cost Tracking into Final Cost Tracker

The curator returns precise cost in `token_usage["cost"]`. This must be added to the pipeline's total cost tracking.

**Files to modify:**
- `scripts/run_enhanced_pipeline.py` - Add curator cost to total
- `scripts/cost_report.py` - Include "Figurative Curator" as a line item

**Example:**
```python
pipeline_costs["figurative_curator"] = curator_output.token_usage.get("cost", 0.0)
pipeline_costs["total"] += pipeline_costs["figurative_curator"]
```

#### 3. Update Methods Section in Word Documents

The three Word documents we produce have a "Methods" section that enumerates figurative parallels reviewed. **Update this to show ALL results the curator considered**, not just the curated examples.

**Current format (inadequate):**
> "We reviewed figurative parallels for shepherd, table, and cup imagery."

**New format (use `search_summary.results_by_vehicle`):**
> "Figurative Parallels Reviewed:
> - **hind**: 28 results
> - **roaring**: 42 results
> - **worm**: 22 results
> - **bulls**: 18 results
> - **lion**: 50 results
> - **water**: 50 results
> - *(etc.)*"

**Data source:** `curator_output.search_summary["results_by_vehicle"]` contains a dict like:
```python
{
  "hind": 28,
  "roaring": 42,
  "worm": 22,
  # ...
}
```

---

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

- [x] Test on Psalm 23 (journey structure) - should produce 4-5 insights, ~10 vehicle groups
- [x] Test on Psalm 22 (descent_ascent structure) - should produce 5 insights, 15 vehicle groups, ~75 curated examples
- [ ] Test on Psalm 1 (binary contrast) - should identify wicked/righteous opposition
- [x] Verify Hebrew text retrieval works for all book name formats (Roman numerals for tanakh.db)
- [x] Check cost tracking produces accurate totals (~$0.30-0.50 per psalm)
- [x] Confirm no boolean syntax in LLM search requests (e.g., "rod OR staff" should fail)
- [x] Verify title imagery is analyzed when present (e.g., "hind of the dawn" in Ps 22)
- [x] Confirm structure_type is appropriate (not defaulting to "journey")

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

## Next Steps (Integration Status)

1. ~~Run test script on several psalms to validate output quality~~ ✓ (Ps 22, 23 tested)
2. ~~Extract production class to `src/agents/figurative_curator.py`~~ ✓ (Session 226)
3. ~~Remove figurative trimming logic from synthesis writer~~ ✓ (Session 226 - skips trimming when curator output present)
4. ~~Integrate with research assembler~~ ✓ (Session 226)
5. ~~Add curator cost to pipeline cost tracking~~ ✓ (Session 227)
6. ~~Update Word doc Methods section to list all results reviewed~~ ✓ (Session 227)
7. Update synthesis prompts to use curator insights (In progress via standard bundle structure)

## Integration Complete (Session 227)

The Figurative Curator is now fully integrated into the production pipeline.

- **Enabled by default**: Controlled by `use_figurative_curator` in `ResearchAssembler`
- **Output**: Curated insights and examples appear in the research bundle
- **Trimming**: Synthesis Writer detects curator output and skips potentially destructive trimming
- **Reporting**:
  - Costs are tracked in the pipeline summary
  - Methods section in generated Word docs lists all figurative parallels reviewed
  - Research bundle markdown includes a "Curated" section with prose insights

To disable for a run (e.g. for testing old behavior), you would need to modify `ResearchAssembler` initialization or add a CLI flag (future work).

## Session Notes

**Session 225 (2025-12-29):** Improved Phase 2 prompt to produce more thorough output:
- Increased insight requirement from 3-5 to 4-5 (aim for 5)
- Added explicit requirement for curated examples from ALL vehicles with results
- Emphasized 5-15 examples is PER VEHICLE (not total)
- Added title imagery analysis requirement (e.g., "hind of the dawn")
- Expanded structure_type options (added descent, descent_ascent, lament_structure)
- Added final checklist for LLM to verify completeness
- Ps 22 now produces: 5 insights, 15 vehicle groups, 75 curated examples, correct "descent_ascent" structure
