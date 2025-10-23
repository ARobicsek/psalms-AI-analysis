# Prioritized Figuration Truncation - Implementation Summary

**Date**: 2025-10-23
**Phase**: Phase 4 - Commentary Enhancement
**Author**: Gemini

---

## 1. Goal

To improve the quality of the final commentary by making the research bundle truncation process "smarter." When the research bundle is too large for the model's context window, the system must shorten it. This enhancement ensures that when trimming the figurative language section, we preserve the most relevant examples—those from the Book of Psalms—at the expense of less relevant examples from other biblical books.

---

## 2. Problem

The existing truncation strategy for the figurative language research was purely proportional. If the section needed to be reduced by 20%, the script would discard 20% of the examples from *every* figurative language query, regardless of their source.

This led to a significant problem: valuable examples of metaphors and similes from within the Book of Psalms were being discarded with the same probability as less relevant examples from books like Leviticus or Chronicles. For a project focused on Psalms commentary, this was a suboptimal strategy that weakened the analytical material available to the Synthesis and Editor agents.

---

## 3. Solution: Prioritized Truncation

A new, priority-based truncation logic was implemented in the `SynthesisWriter` agent.

### How it Works

The core change is in the function responsible for trimming the figurative language section, which was renamed from `_trim_figurative_proportionally` to `_trim_figurative_with_priority` to reflect its new intelligence.

For each figurative language query that needs to be trimmed, the new logic executes a two-step process:

1.  **Categorize Instances**: The script first iterates through all retrieved examples and separates them into two distinct lists:
    *   `psalms_instances`: A list of all examples explicitly sourced from the Book of Psalms.
    *   `other_instances`: A list of all examples from any other biblical book.

2.  **Apply Prioritized Trimming**: When deciding which examples to keep, the function now follows a clear priority:
    *   It first fills its quota of examples to keep using the `psalms_instances`.
    *   Only if all available Psalms examples have been kept and the quota is still not met does the script begin to draw from the `other_instances` list.
    *   If the quota can be met with Psalms examples alone, all `other_instances` are discarded.

### Impact

This change ensures that the context provided to the LLM is of the highest possible relevance. The Synthesis and Editor agents will now receive a research bundle that preferentially includes figurative language as it is used *within the Psalter*, leading to more insightful, internally consistent, and contextually aware commentary.

---

## 4. Implementation Details

### File Modified: `src/agents/synthesis_writer.py`

1.  **Function Renamed and Rewritten**:
    *   `_trim_figurative_proportionally()` was replaced with `_trim_figurative_with_priority()`.
    *   The new function contains the logic to categorize instances by source (`if "Psalms" in instance`) and select which ones to keep based on the new priority system.

2.  **Call Site Updated**:
    *   The `_trim_research_bundle()` method was updated to call the new `_trim_figurative_with_priority()` function.
    *   The corresponding log message was also updated to accurately describe the new strategy.

### Code Snippet: The New Logic

```python
# --- New Prioritization Logic (inside _trim_figurative_with_priority) ---

# Categorize instances
psalms_instances = [inst for inst in instances if "Psalms" in inst]
other_instances = [inst for inst in instances if "Psalms" not in inst]

# Determine how many to keep
target_keep_count = max(1, int(len(instances) * keep_ratio))

kept_instances = []

# Prioritize keeping instances from Psalms
if len(psalms_instances) >= target_keep_count:
    # If we have enough Psalms instances, take from them
    kept_instances = psalms_instances[:target_keep_count]
else:
    # If not, take all Psalms instances and fill the rest from other books
    kept_instances.extend(psalms_instances)
    remaining_needed = target_keep_count - len(psalms_instances)
    if remaining_needed > 0:
        kept_instances.extend(other_instances[:remaining_needed])

omitted_count = len(instances) - len(kept_instances)

# Reassemble the query block...
```

---

## 5. Validation

The change is validated by its logical structure. To empirically test, one would need a research bundle large enough to trigger figurative language truncation. Running the pipeline on such a psalm and inspecting the `debug/verse_prompt_psalm_NNN.txt` file would show that the trimmed figurative language section contains primarily or exclusively examples from Psalms.
