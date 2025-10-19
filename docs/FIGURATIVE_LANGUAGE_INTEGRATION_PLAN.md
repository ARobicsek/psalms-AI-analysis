# Figurative Language Database Integration Plan

**Date**: 2025-10-19
**Priority**: HIGHEST IMPACT
**Status**: Investigation Complete, Implementation Pending

---

## Executive Summary

Investigation of the figurative language database integration revealed **severe underutilization**: the pipeline uses only **1.2-1.8% of available database resources** (34-51 instances out of 2,863 total). This represents a major missed opportunity for enriching commentary with existing scholarly figurative language analysis.

**Expected Impact of Fixes**: Increase utilization from ~1.5% to 15-25%, dramatically improving commentary depth without additional research costs.

---

## Investigation Findings

### Current State (Problematic)

**Database Capacity:**
- 2,863 total figurative language instances in Psalms
- Rich coverage of major metaphors: "shield" (214), "light" (389), "rock" (97), "shepherd" (89), "hand" (600+), "eye" (400+)

**Actual Pipeline Usage (Psalm 145 example):**
- Only 34 instances returned from 11 searches
- Utilization rate: **1.2%** (34/2,863)

**Typical Pipeline Usage (across psalms):**
- Average: 34-51 instances per psalm
- Utilization rate: **1.2-1.8%**

### Root Causes

1. **Search Terms Too Specific**
   - Micro Analyst searches only very unusual vehicles (e.g., "womb," "nostril," "bubble")
   - Misses obvious major metaphors already in database (e.g., "hand," "eye," "rock," "light")

2. **No Baseline Metaphor Coverage**
   - Pipeline doesn't guarantee coverage of common biblical metaphors
   - Depends entirely on what Micro Analyst discovers in specific psalm

3. **Vehicle-Only Search Strategy**
   - Current system only searches for specific vehicle terms
   - Doesn't search by tenor (e.g., "God AS..." or "people AS...")

4. **No Database-Aware Prompting**
   - Micro Analyst doesn't know what's already in the database
   - Can't prioritize searches that will yield database hits

5. **Avoid List Too Broad**
   - Current avoid list excludes common imagery even when database has rich data
   - Example: "hand" avoided, but database has 600+ instances of figurative hand usage

6. **No Fallback to Common Metaphors**
   - If Micro Analyst finds few unusual metaphors, no fallback to major biblical themes
   - Results in very sparse figurative language coverage

---

## Proposed Fixes (6 Immediate Actions)

### Fix 1: Add Baseline Metaphor Coverage

**What**: Automatically include searches for major biblical metaphors in every psalm

**How**: Modify `src/agents/scholar_researcher.py` to always search these terms:
- God imagery: "king," "shepherd," "rock," "shield," "fortress," "light"
- Human condition: "sheep," "dust," "grass," "chaff," "tree"
- Emotional/moral: "darkness," "path," "way," "water," "fountain"

**Implementation**:
```python
# In ScholarResearcher.gather_research()
BASELINE_METAPHORS = [
    "king", "shepherd", "rock", "shield", "fortress", "light",
    "sheep", "dust", "grass", "chaff", "tree",
    "darkness", "path", "water", "fountain"
]

# Always search these in addition to Micro Analyst requests
for metaphor in BASELINE_METAPHORS:
    if metaphor not in requested_vehicles:
        search_baseline_metaphor(metaphor)
```

**Expected Impact**: +200-400 instances per psalm (utilization: 1.5% → 8-15%)

---

### Fix 2: Revise Avoid List to Database-Aware

**What**: Only avoid metaphors if they're NOT richly represented in database

**How**: Query database for instance counts, avoid only if <20 instances

**Implementation**:
```python
# New approach in micro_analyst.py
AVOID_IF_FEW_INSTANCES = 20  # threshold

def should_avoid_metaphor(vehicle: str) -> bool:
    """Only avoid if database has few instances."""
    count = query_figurative_db_count(vehicle)
    return count < AVOID_IF_FEW_INSTANCES

# Update prompt to be database-aware
AVOID_ONLY_IF_SPARSE = [
    "blessing", "praise", "fear" (if <20 instances),
    # but KEEP "hand", "eye", "mouth" (600+, 400+, 300+ instances)
]
```

**Expected Impact**: +100-200 instances per psalm (utilization: +3-7%)

---

### Fix 3: Database Statistics in Micro Analyst Prompt

**What**: Inform Micro Analyst which metaphors have rich database coverage

**How**: Add database statistics section to prompt

**Implementation**:
```markdown
## FIGURATIVE LANGUAGE DATABASE STATISTICS

The database contains rich coverage of these metaphors in Psalms:
- "hand" (600+ instances) - power, action, protection
- "eye" (400+ instances) - attention, favor, watchfulness
- "light" (389 instances) - guidance, revelation, life
- "shield" (214 instances) - protection, defense
- "rock" (97 instances) - stability, refuge, foundation
- "shepherd" (89 instances) - care, guidance, provision

**Prioritize searches that will leverage this existing research.**
If the psalm uses any of these major metaphors, request them explicitly.
```

**Expected Impact**: Better search prioritization, +50-100 instances (utilization: +2-3%)

---

### Fix 4: Tenor-Based Search Capability

**What**: Allow searching by what is being described, not just vehicle

**How**: Add tenor search parameters to figurative language queries

**Implementation**:
```python
# New search method in figurative_search.py
def search_by_tenor(tenor: str) -> List[FigurativeInstance]:
    """
    Search for instances describing a specific tenor.

    Example: tenor="God" returns all metaphors for God
             (shepherd, rock, shield, king, light, etc.)
    """
    query = """
    SELECT * FROM figurative_language
    WHERE tenor LIKE ?
    ORDER BY book_id, chapter, verse
    """
    return execute_query(query, f"%{tenor}%")

# Usage in Micro Analyst
# "This psalm describes God as protector"
# → search_by_tenor("God") + filter for protection semantics
```

**Expected Impact**: +100-150 instances per psalm (utilization: +3-5%)

---

### Fix 5: Hierarchical Metaphor Expansion

**What**: For any searched vehicle, automatically include related metaphors

**How**: Use metaphor families (already exists, enhance it)

**Implementation**:
```python
# Enhanced metaphor families in micro_analyst.py
METAPHOR_FAMILIES = {
    "protection": ["shield", "fortress", "rock", "refuge", "stronghold", "tower"],
    "guidance": ["light", "lamp", "path", "way", "shepherd", "staff"],
    "judgment": ["fire", "sword", "arrows", "whirlwind", "flood"],
    "praise": ["sing", "shout", "music", "trumpet", "lyre"],
    "life": ["water", "fountain", "tree", "vine", "bread"],
}

# When Micro Analyst requests "shield", auto-add family
if "shield" in requested_vehicles:
    add_related_from_family("protection")
```

**Expected Impact**: +50-100 instances per psalm (utilization: +2-3%)

---

### Fix 6: Figurative Language Summary in Pipeline Stats

**What**: Track database utilization in pipeline summary reports

**How**: Add metrics to `PipelineSummaryTracker`

**Implementation**:
```python
# In pipeline_summary.py
def track_figurative_utilization(self):
    """Calculate database utilization metrics."""
    total_db_instances = 2863  # Psalms total
    instances_returned = len(self.research_bundle.figurative_instances)

    self.metrics['figurative_db_utilization'] = {
        'total_available': total_db_instances,
        'instances_used': instances_returned,
        'utilization_rate': f"{(instances_returned/total_db_instances)*100:.1f}%",
        'searches_performed': len(self.research_requests['figurative']),
    }

# Output in summary report
## Figurative Language Database Utilization
- Total available: 2,863 instances
- Instances used: 412
- Utilization rate: 14.4%
- Searches performed: 23
```

**Expected Impact**: Visibility into improvement, enables ongoing optimization

---

## Implementation Checklist

### Phase 1: Quick Wins (1-2 hours)
- [ ] Implement Fix 1: Baseline metaphor coverage (highest impact)
- [ ] Implement Fix 2: Revise avoid list to database-aware
- [ ] Implement Fix 6: Add utilization tracking to pipeline stats
- [ ] Test on Psalm 145 to verify increased coverage

### Phase 2: Enhanced Search (2-3 hours)
- [ ] Implement Fix 3: Add database statistics to Micro Analyst prompt
- [ ] Implement Fix 5: Hierarchical metaphor expansion
- [ ] Test on Psalms 1, 23, 29 to verify diverse coverage

### Phase 3: Advanced Features (3-4 hours)
- [ ] Implement Fix 4: Tenor-based search capability
- [ ] Update documentation with new search strategies
- [ ] Generate comparative report: before/after utilization rates

### Phase 4: Validation (1 hour)
- [ ] Run full pipeline on 5 diverse psalms
- [ ] Verify 15-25% utilization rate achieved
- [ ] Document examples of enhanced commentary
- [ ] Update README and NEXT_SESSION_PROMPT

---

## Examples of Enhanced Commentary

### Before (1.2% utilization, 34 instances)

> Verse 16 speaks of God opening his hand. This imagery of divine generosity appears elsewhere in Scripture.

**Problem**: Generic observation, no specific parallel passages, no depth.

---

### After (15-25% utilization, 350-600 instances)

> Verse 16's imagery of God "opening his hand" (פּוֹתֵחַ אֶת־יָדֶךָ) participates in a rich biblical tradition of the divine hand as a source of provision and blessing. The phrase appears in nearly identical form in Psalm 104:28, also in a creation context, and echoes the hand imagery of Deuteronomy 15:8, where the opened hand represents covenant generosity. The database shows 600+ instances of figurative hand usage across Scripture, with the "opened hand" specifically signaling abundance (cf. Psalm 145:16; Job 12:9-10). This is distinct from the "strong hand" (יָד חֲזָקָה) of Exodus deliverance or the "right hand" (יָמִין) of power and favor. The poet's choice emphasizes not God's might but His generous disposition toward all creatures—appropriate for a wisdom psalm celebrating universal providence.

**Improvement**:
- Specific parallel passages cited
- Distinctions between hand metaphor types
- Database-supported usage patterns
- Theological precision
- Contextual appropriateness

---

## Success Metrics

### Quantitative Targets
- **Utilization Rate**: 1.5% → 15-25%
- **Instances per Psalm**: 34-51 → 350-600
- **Search Coverage**: 11 searches → 25-35 searches
- **Major Metaphors**: 0-2 per psalm → 8-12 per psalm

### Qualitative Improvements
- Commentary cites specific parallel passages from database
- Metaphor analysis includes usage pattern distinctions
- Theological insights grounded in scriptural cross-references
- Readers can trace figurative language themes across Psalms

---

## Files to Modify

### Core Pipeline
1. **`src/agents/micro_analyst.py`**
   - Update avoid list (Fix 2)
   - Add database statistics to prompt (Fix 3)
   - Enhance metaphor families (Fix 5)

2. **`src/agents/scholar_researcher.py`**
   - Add baseline metaphor coverage (Fix 1)
   - Implement tenor-based search (Fix 4)

3. **`src/utils/pipeline_summary.py`**
   - Add figurative utilization tracking (Fix 6)

### Database Layer
4. **`src/data_sources/figurative_search.py`**
   - Add `search_by_tenor()` method (Fix 4)
   - Add `get_instance_count()` helper (Fix 2)

---

## Related Documentation

- **Investigation Report**: See conversation history (2025-10-19 Session 2)
- **Database Schema**: `database/figurative_language.db` structure
- **Current Implementation**: `src/agents/micro_analyst.py` (lines 177-196)
- **Metaphor Families**: `src/agents/micro_analyst.py` (existing but can be enhanced)

---

## Cost/Benefit Analysis

**Implementation Time**: 6-10 hours total
**Token Cost Impact**: Minimal (~10-20k additional tokens per psalm)
**Quality Improvement**: MAJOR (10x more figurative language coverage)
**ROI**: Very High - leverages existing database without new research costs

**Why This Matters**:
- Database already paid for (2,863 instances pre-analyzed)
- Currently wasting 98.5% of available research
- Fixes require no new API calls, only smarter querying
- Immediate quality improvement without cost increase

---

## Next Steps (Immediate)

1. **Review this plan** with stakeholders
2. **Implement Phase 1** (quick wins, ~2 hours)
3. **Test on Psalm 145** to verify improvement
4. **Document results** in pipeline summary
5. **Proceed to Phase 2** if Phase 1 successful

---

## Contact for Questions

See: `docs/NEXT_SESSION_PROMPT.md` for current project status and priorities.

---

**Summary**: The figurative language database is a rich, underutilized resource. These 6 fixes will transform it from a 1.5% utilized curiosity into a 15-25% utilized foundation for deep metaphorical commentary—without increasing costs or API calls. This is the highest-impact improvement available to the pipeline today.
