# Psalms Commentary Project - Status

**Last Updated**: 2025-10-27 (Session 35 Complete)
**Current Phase**: Liturgical Librarian Redesign - Phrase-First Grouping

---

## Quick Status

### Completed ✅
- **Core Pipeline**: 4-pass commentary generation (Macro → Micro → Synthesis → Editor)
- **Hebrew Processing**: Phonetic transcription, concordance, morphology
- **Figurative Language**: 2,863 analyzed instances indexed
- **Liturgical Context Phase 0**: Sefaria curated links operational
- **Liturgical Context Phase 4**: Phrase-level indexing complete (some Psalms)
- **Liturgical Context Phase 5**: Intelligent aggregation with LLM summaries ✅
- **Liturgical Context Phase 6**: Pipeline integration ✅
- **NEW (Session 35)**: Phrase-first grouping with intelligent deduplication! ✅

### In Progress 🔄
- **Bug Fixes**: Full psalm detection too aggressive (filters ALL matches)
- **Enhancement**: Need to add LLM analysis of hebrew_text field

### Next Up 📋
- **PRIORITY**: Fix `_verify_full_psalm_matches()` (currently too strict)
- **PRIORITY**: Add hebrew_text analysis to LLM prompts for context verification
- Test fixes with Psalm 23 full chapter
- Full pipeline testing after fixes complete

---

## Phase Completion Status

| Phase | Status | Notes |
|-------|--------|-------|
| **Phase 1**: Foundation | ✅ Complete | Hebrew processing, phonetic transcription |
| **Phase 2**: Concordance | ✅ Complete | 4-layer search system operational |
| **Phase 3**: Figurative Language | ✅ Complete | 2,863 instances indexed |
| **Phase 4A**: Liturgy Harvesting | ✅ Complete | ~1,113 prayers from Sefaria |
| **Phase 4B**: Phrase Extraction | ✅ Complete | ~12,253 phrases cached |
| **Phase 4C**: Phrase Indexing | 🔄 Partial | Psalm 23 indexed, not all 150 |
| **Phase 4D**: Bug Fixes | ✅ Complete | Phrase extraction corrected (Session 32) |
| **Phase 5**: Intelligent Aggregation | ✅ Complete | 730-line module with LLM (Session 33) |
| **Phase 6**: Pipeline Integration | ✅ Complete | Integrated into ResearchAssembler (Session 34) |
| **Phase 6.5**: Phrase-First Redesign | ✅ Complete | Groups by phrase not prayer (Session 35) |
| **Phase 6.6**: Bug Fixes | 🔧 Needed | Full psalm detection, hebrew_text analysis |
| **Phase 7**: Optimization | 📋 After fixes | LLM summary caching, verse-level queries |

---

## Current Architecture

### Liturgical Librarian (Two Implementations)

#### Phase 0 (Sefaria Bootstrap)
- **File**: `src/agents/liturgical_librarian_sefaria.py`
- **Data**: Curated Psalms→Liturgy links from Sefaria
- **Coverage**: 67 Psalms with curated links
- **Use case**: Fallback when Phase 4/5 unavailable

#### Phase 4/5/6.5 (Phrase-First + Intelligent Deduplication) ⭐ CURRENT
- **File**: `src/agents/liturgical_librarian.py`
- **Data**: Phrase-level index (`psalms_liturgy_index` table)
- **Architecture**: **Phrase-first grouping** (redesigned in Session 35)
  - Groups by PSALM PHRASE, not prayer name
  - Answers: "Where does THIS SPECIFIC PHRASE appear?"
  - Separates full psalm recitations from excerpts
- **Features**:
  - Intelligent deduplication (merges overlapping phrases)
  - False positive filtering (metadata error detection)
  - LLM summaries describe specific phrases (Claude Haiku 4.5)
  - Verbose mode for debugging (`--verbose`)
- **Example**:
  - OLD (Session 34): 56 distinct prayers (unclear which phrases)
  - NEW (Session 35): 3 distinct phrases with clear descriptions
  - "The phrase 'למען שמו' from Psalm 23:3 appears in the Amidah..."

### Data Flow (Current)
```
1. Psalm Text (database/tanakh.db)
   ↓
2. Phrase Extraction (src/liturgy/phrase_extractor.py)
   ↓
3. Phrase Indexing (src/liturgy/liturgy_indexer.py)
   ↓
4. Raw Index (data/liturgy.db::psalms_liturgy_index)
   ↓
5. Phrase-First Aggregation (src/agents/liturgical_librarian.py)
   │  ├─ Group by psalm phrase
   │  ├─ Verify full psalm matches
   │  ├─ Deduplicate overlapping phrases
   │  └─ Generate LLM summaries (Claude Haiku 4.5)
   ↓
6. PhraseUsageMatch objects (phrase-first results)
   ↓
7. Research Bundle (markdown for AI agents)
```

### Integration Points (Active)
```
ResearchAssembler:
├─ Concordance lookup
├─ Figurative language search
└─ Liturgical usage (phrase-first) ← ACTIVE (Session 34-35)
   └─ find_liturgical_usage_by_phrase() ← NEW (Session 35)

MicroAnalyst:
└─ Calls ResearchAssembler per verse

SynthesisWriter:
├─ Receives ResearchBundle with liturgical_markdown
└─ Generates verse-by-verse commentary
```

---

## Recent Achievements (Sessions 32-35)

### Session 32: Bug Fix
- **Problem**: Liturgy phrase extraction returning wrong phrases from same context
- **Solution**: Replaced character-position indexing with sliding window approach
- **Impact**: All liturgy_phrase_hebrew fields now accurate
- **Code**: `src/liturgy/liturgy_indexer.py::_extract_exact_match()`

### Session 33: Intelligent Aggregation
- **Problem**: Prayer duplication (e.g., 79 Amidah entries for one phrase)
- **Solution**: Smart grouping + optional LLM summaries
- **Impact**: Clean, concise liturgical context for agents
- **Code**: `src/agents/liturgical_librarian.py` (730 lines)
- **Features**:
  - Prayer name normalization (Avot/Patriarchs, Amida/Amidah)
  - Claude Haiku 4.5 for natural language summaries
  - Graceful fallback to code-only
  - CLI with `--skip-liturgy-llm` flag

### Session 34: Pipeline Integration
- **Goal**: Integrate Phase 4/5 Liturgical Librarian into commentary pipeline
- **Solution**: Enhanced ResearchAssembler with dual-path liturgical support
- **Impact**: Research bundles now include aggregated liturgical data with LLM summaries
- **Code**: `src/agents/research_assembler.py` (~100 lines modified)
- **Test Results**:
  - Psalm 23: 56 distinct prayers, 282 total occurrences
  - ~78% token reduction vs raw index
  - LLM summaries verified working
  - All integration tests passing
- **Features**:
  - Primary: Phase 4/5 aggregated with LLM
  - Fallback: Phase 0 Sefaria curated links
  - Backward compatible
  - Pre-formatted markdown for agents

### Session 35: Phrase-First Redesign ⭐ NEW
- **Problem**: Output grouped by prayer name without identifying which specific phrase
- **Solution**: Complete redesign to phrase-first grouping with intelligent deduplication
- **Impact**: Clear descriptions of WHERE SPECIFIC PHRASES appear in liturgy
- **Code**: `src/agents/liturgical_librarian.py` (~400 lines added)
- **New Features**:
  - **PhraseUsageMatch** dataclass (phrase-first)
  - **find_liturgical_usage_by_phrase()** method (replaces old aggregation)
  - **Intelligent deduplication**:
    - Filters false "full psalm" matches (metadata errors)
    - Removes redundant phrases from full psalm contexts
    - Merges overlapping phrases from identical contexts
  - **Enhanced LLM prompts**: Describe specific phrases, not prayers
- **Test Results** (Psalm 23:3):
  - Before: 5 redundant entries
  - After: 3 distinct phrases with clear descriptions
  - Example: "The phrase 'למען שמו' (l'ma'an shemo, 'for His name's sake') from Psalm 23:3 appears in the Amidah across all traditions..."
- **Known Issues**:
  - Full psalm detection too aggressive (filters ALL matches)
  - Need to add hebrew_text analysis to LLM
  - **Session 36 priority**: Fix these bugs

---

## Test Results (Psalm 23)

### Verse 3 (Phrase-First Results - Session 35)
- **Raw matches**: 106
- **Phrase-first aggregation**: 3 distinct phrases
- **Top phrases**:
  1. "למען שמו" - 82 occurrences across 34 prayer contexts
  2. Merged Sefard phrases - 10 occurrences across 5 contexts
  3. Additional Ashkenaz phrase - 6 occurrences across 6 contexts
- **Deduplication**: 5 initial phrases → 3 final (after merging)
- **Output**: `logs/psalm23_verse3_deduplicated.txt`

### Full Chapter (Prayer-First Results - Session 34)
- **Raw matches**: 282
- **Aggregated**: 56 distinct prayers
- **Top prayers**:
  - Amidah: 54 occurrences
  - Vayechulu: 20 occurrences
  - Kiddush: 18 occurrences
  - Multiple Zemirot variations: 12+ occurrences each
- **Note**: Session 35 makes prayer-first aggregation obsolete

---

## API & Cost Information

### Claude API Usage

#### Sonnet 4.5 (Main Commentary)
- **MacroAnalyst**: ~10K tokens per Psalm ($0.030)
- **MicroAnalyst**: ~50K tokens per Psalm ($0.150)
- **SynthesisWriter**: ~80K tokens per Psalm ($0.240)
- **Subtotal**: ~$0.42 per Psalm (Sonnet only)

#### Haiku 4.5 (Liturgy Summaries) ⭐ NEW
- **Per phrase query**: ~$0.0005 (half a cent)
- **Per Psalm** (~50 phrases): ~$0.025
- **All 150 Psalms**: ~$3.75 total
- **Impact**: Negligible addition to budget

#### GPT-5 (Final Editing)
- **MasterEditor**: ~$0.18 per Psalm
- **Total with GPT-5**: ~$0.60-0.65 per Psalm

**Total Project Cost** (all 150 Psalms):
- **With LLM liturgy summaries**: ~$95
- **Without LLM**: ~$92
- **Difference**: $3 (recommend enabling LLM)

---

## Command Reference

### Liturgical Librarian CLI
```bash
# Test with LLM summaries (default, requires ANTHROPIC_API_KEY)
python src/agents/liturgical_librarian.py 23

# Test without LLM (code-only)
python src/agents/liturgical_librarian.py 23 --skip-liturgy-llm

# Test specific verses
python src/agents/liturgical_librarian.py 23 --verses 1 2 3

# Show statistics
python src/agents/liturgical_librarian.py --stats

# Set confidence threshold
python src/agents/liturgical_librarian.py 23 --min-confidence 0.85

# Include detailed raw matches
python src/agents/liturgical_librarian.py 23 --detailed
```

### Programmatic Usage
```python
from src.agents.liturgical_librarian import LiturgicalLibrarian

# Initialize
librarian = LiturgicalLibrarian(use_llm_summaries=True)

# Query
results = librarian.find_liturgical_usage_aggregated(
    psalm_chapter=23,
    psalm_verses=[3],
    min_confidence=0.75
)

# Format for agents
markdown = librarian.format_for_research_bundle(
    results,
    psalm_chapter=23,
    psalm_verses=[3]
)
```

---

## Database Status

### liturgy.db (Main Liturgy Database)
```
prayers table:           1,113 prayers
phrase_cache:            12,253 phrases (Psalm 23 + others)
psalms_liturgy_index:    Varies by Psalm (Psalm 23 fully indexed)
sefaria_liturgy_links:   212 curated links (Phase 0)
```

### tanakh.db (Canonical Hebrew Text)
```
verses table:            Complete Tanakh
All 150 Psalms available for processing
```

---

## Known Issues & Limitations

### Current
1. **Phase 4 Indexing Incomplete**: Only some Psalms indexed (e.g., Psalm 23)
   - **Impact**: Need to run indexer for remaining Psalms
   - **Solution**: Run `python src/liturgy/liturgy_indexer.py --all` (long-running)

2. **LLM Testing Pending**: Haiku 4.5 not yet tested with API key
   - **Impact**: Code-only summaries used in tests
   - **Solution**: Set `ANTHROPIC_API_KEY` and verify

3. **Caching Not Implemented**: LLM summaries regenerated each query
   - **Impact**: Minor cost/latency overhead
   - **Solution**: Phase 2 optimization (cache summaries in DB)

### Design Decisions
- **Aggregation ON by default**: Always groups prayers
- **Confidence threshold**: 0.75 (configurable)
- **LLM opt-in**: Use `--skip-liturgy-llm` to disable
- **Backward compatible**: Phase 0 librarian still available

---

## Next Session Priorities

### High Priority
1. ✅ Set `ANTHROPIC_API_KEY` and test LLM summaries
2. ✅ Verify aggregation handles pattern from `logs/another_example.txt`
3. ✅ Integrate librarian into MicroAnalyst research bundle generation
4. ✅ Test end-to-end pipeline with Psalm 23

### Medium Priority
5. ⚪ Add cost tracking for Haiku 4.5 API calls
6. ⚪ Index remaining Psalms (or decide on Phase 0 fallback strategy)
7. ⚪ Update TECHNICAL_ARCHITECTURE_SUMMARY.md

### Low Priority / Future
8. ⚪ Implement LLM summary caching (optimization)
9. ⚪ Add drill-down capability (expand aggregated entries)
10. ⚪ Export aggregated liturgy data to CSV/JSON

---

## Files Modified (Session 33)

### New Files
- `src/agents/liturgical_librarian.py` - Comprehensive librarian with aggregation

### Updated Files
- `docs/IMPLEMENTATION_LOG.md` - Session 33 entry
- `NEXT_SESSION_PROMPT.md` - Session 34 handoff
- `PROJECT_STATUS.md` - This file

### Test Files
- `logs/one_phrase_example.txt` - Example of duplication problem
- `logs/another_example.txt` - Pattern to assess

---

## Success Metrics

### Phase 5 Completion Criteria ✅
- [x] Prayer aggregation working (31 from 106 for Psalm 23:3)
- [x] LLM integration with graceful fallback
- [x] CLI with `--skip-liturgy-llm` flag
- [x] Research bundle formatter
- [x] Documentation complete

### Phase 6 Goals (Next)
- [ ] Integrated into pipeline
- [ ] LLM summaries tested and verified
- [ ] Full Psalm 23 end-to-end test passes
- [ ] Cost tracking implemented
- [ ] No regression in commentary quality

---

## Contact & Resources

- **GitHub**: (add repository URL)
- **Documentation**: See `docs/` directory
- **Cost Reports**: Run `python scripts/cost_report.py`
- **Session Logs**: See `docs/IMPLEMENTATION_LOG.md`

---

**Status**: Ready for Phase 6 integration testing! 🚀
