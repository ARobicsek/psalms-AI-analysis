# Next Session Prompt: Phase 3c - SynthesisWriter Agent

## Current Status: Phase 3b COMPLETE + Pipeline Refinements ✅

**Completed in Previous Sessions:**
- ✅ LXX (Greek Septuagint) integration into RAG Manager
- ✅ MicroAnalyst v2 agent built with curiosity-driven architecture
- ✅ Three-stage discovery process: Fresh Eyes → Research Requests → Assembly
- ✅ Comprehensive input logging for transparency
- ✅ Successfully tested on Psalm 29 with rich outputs
- ✅ **NEW**: Pipeline refinements for improved search recall (Oct 17)
  - Concordance searches now default to "consonantal" (not "exact")
  - Figurative searches no longer filter by type (metaphor, simile, etc.)
  - Expected 20-30% improvement in data retrieval

**Recent Improvements (Oct 17 Evening):**

Two critical pipeline refinements completed:

1. **Concordance Search Strategy**: Changed default from "exact" to "consonantal"
   - Exact searches were too restrictive (missed vocalization variants)
   - Consonantal matches all root forms regardless of Masoretic pointing
   - "Exact" now reserved for homograph disambiguation only
   - Files modified: `micro_analyst.py`, `scholar_researcher.py`, `ARCHITECTURE.md`

2. **Figurative Language Strategy**: Removed type filtering
   - Previously filtered by "metaphor" vs "simile" vs "personification"
   - This was too restrictive (figurative instances are multi-dimensional)
   - Now retrieves ALL figurative instances for a verse
   - Filters only by vehicle/target if specified
   - Files modified: `micro_analyst.py`, `scholar_researcher.py`

**Why This Matters for SynthesisWriter:**
- More comprehensive research data in research bundles
- Higher recall on concordance patterns across scripture
- Broader figurative language context
- SynthesisWriter will have richer data to work with

**Test Outputs Available:**
- `output/phase3_test/psalm_029_macro.json` - Pass 1 MacroAnalysis (thesis, structure, devices)
- `output/phase3_test/psalm_029_macro.md` - Human-readable macro analysis
- `output/phase3_test/psalm_029_micro.json` - Pass 2 discoveries and observations
- `output/phase3_test/psalm_029_micro.md` - Verse-by-verse discoveries
- `output/phase3_test/psalm_029_research.md` - Comprehensive research bundle (31 BDB entries, 7 concordances, 11 figurative checks, 4 commentaries)
- `output/phase3_test/psalm_029_research_requests.md` - All research requests with justifications

---

## Phase 3c Goal: Build SynthesisWriter Agent (Pass 3)

### What SynthesisWriter Does

The **SynthesisWriter** is the scholarly essayist who receives:
1. MacroAnalysis (thesis + structure from Pass 1)
2. MicroAnalysis (verse discoveries from Pass 2)
3. Research Bundle (all lexical/concordance/figurative/commentary data - NOW MORE COMPREHENSIVE!)

And produces:
1. **Introduction Essay (800-1200 words)**: Presents genre, context, thesis, structure, and key poetic devices
2. **Verse-by-Verse Commentary**: Detailed exegetical treatment integrating all research

### Critical Design Principles

**1. Authority to Revise/Reject Macro Thesis**
- SynthesisWriter has FULL authority to modify or reject the macro thesis
- If micro discoveries suggest a different interpretation, SynthesisWriter should follow the evidence
- The macro thesis is a hypothesis to be tested, not dogma to be confirmed

**2. Curiosity-Driven Integration**
- SynthesisWriter should prioritize what's ACTUALLY interesting in the text
- Don't force-fit discoveries to support the original thesis
- If a verse reveals something unexpected/surprising, feature that insight

**3. Telescopic Thinking**
- Connect micro details (word choices, poetic devices) to larger themes
- Show how individual verses build the psalm's argument
- Demonstrate coherence without ignoring complexity

**4. Scholarly but Accessible**
- Write for educated lay readers, not specialists
- Explain technical terms (e.g., "anaphora", "chiasmus")
- Cite sources properly (BDB, commentators)
- Avoid clichés and unsupported claims

**5. Research Integration**
- Smoothly weave lexical insights into commentary
- Reference concordance patterns where illuminating (NOW MORE COMPREHENSIVE!)
- Incorporate traditional commentary perspectives
- Use LXX to show ancient interpretive tradition
- Leverage figurative language analysis (NOW BROADER!)

### Implementation Task: Build `src/agents/synthesis_writer.py`

**Class Structure:**
```python
class SynthesisWriter:
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.model = model
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.logger = # setup logging to logs/synthesis_writer_YYYYMMDD_HHMMSS.log

    def synthesize_commentary(
        self,
        psalm_number: int,
        macro_analysis: MacroAnalysis,
        micro_analysis: MicroAnalysis,
        research_bundle: ResearchBundle
    ) -> SynthesisOutput:
        """
        Synthesize introduction essay + verse-by-verse commentary.

        Returns SynthesisOutput with:
        - title: str
        - essay: str (intro + verse commentary combined)
        - sources_cited: List[str]
        - word_count: int
        """
```

**Two-Stage Process:**

**Stage 1: Write Introduction Essay**
- Present genre and historical/theological context
- State the thesis (revised if needed based on micro discoveries)
- Outline structural divisions
- Discuss key poetic devices
- Set up expectations for verse commentary
- Target: 800-1200 words

**Stage 2: Write Verse-by-Verse Commentary**
- For each verse:
  - Integrate lexical insights from BDB
  - Reference concordance patterns if illuminating
  - Analyze figurative language (metaphor, simile, personification)
  - Incorporate traditional commentary perspectives
  - Show LXX interpretive tradition where relevant
  - Connect to larger themes/thesis
- Smooth, readable prose with inline citations
- Target: 150-300 words per verse (varies by complexity)

**Prompt Design Considerations:**

1. **Thesis Revision Authority**: Explicitly tell the model it can revise the thesis if micro discoveries warrant it
2. **Evidence-First Approach**: "What does the text actually say/do?" before "How does this fit the thesis?"
3. **Citation Format**: Establish clear format (e.g., "The Hebrew קוֹל (qôl, 'voice'; BDB) appears seven times...")
4. **Coherence Without Force-Fitting**: "Show how verses relate while honoring their individual complexity"
5. **Extended Thinking**: Use extended thinking for deeper synthesis (10K-15K token budget)

**Output Formats:**

Save three files:
1. `output/phase3_test/psalm_029_synthesis.json` - SynthesisOutput object
2. `output/phase3_test/psalm_029_synthesis.md` - Human-readable markdown
3. Auto-generated log: `logs/synthesis_writer_YYYYMMDD_HHMMSS.log`

### Test Plan: `tests/test_synthesis_writer.py`

**Test Script Should:**
1. Load MacroAnalysis from `output/phase3_test/psalm_029_macro.json`
2. Load MicroAnalysis from `output/phase3_test/psalm_029_micro.json`
3. Load ResearchBundle from saved JSON (need to add bundle saving to micro test)
4. Initialize SynthesisWriter
5. Generate commentary
6. Validate:
   - Introduction essay present (800-1200 words)
   - Verse commentary for all 11 verses
   - Sources cited (BDB entries, commentators)
   - Total word count reasonable (2000-4000 words)
   - Citations properly formatted
7. Save outputs (JSON + markdown)
8. Display summary to console

**Expected Runtime:** ~3-5 minutes (depends on extended thinking and output length)

### Validation Criteria

A successful SynthesisOutput should demonstrate:
- ✅ **Coherent thesis**: Clear, specific, textually grounded
- ✅ **Telescopic integration**: Connects micro details to macro themes
- ✅ **Research integration**: Smoothly incorporates lexical/figurative/traditional sources
- ✅ **Accessibility**: Scholarly but readable for educated lay readers
- ✅ **Proper citations**: Attributes BDB, commentators, concordances
- ✅ **Evidence-based claims**: Supports assertions with textual analysis
- ✅ **Poetic awareness**: Discusses parallelism, word choices, structure
- ✅ **Thesis flexibility**: Revises macro thesis if evidence warrants

### Files to Reference

**Schemas:**
- `src/schemas/analysis_schemas.py` - SynthesisOutput dataclass already defined (lines 211-260)

**Prior Passes:**
- `src/agents/macro_analyst.py` - Pass 1 implementation (for consistency)
- `src/agents/micro_analyst.py` - Pass 2 implementation (for consistency)

**Test Outputs:**
- `output/phase3_test/psalm_029_macro.md` - Review the macro thesis
- `output/phase3_test/psalm_029_micro.md` - See what discoveries were made
- `output/phase3_test/psalm_029_research.md` - Browse available research data

**Documentation:**
- `docs/PHASE3_ARCHITECTURE.md` - Full pipeline overview
- `docs/TESTING_AND_OUTPUT_CONVENTIONS.md` - Where to save files
- `docs/IMPLEMENTATION_LOG.md` - Historical context (includes Oct 17 refinements)
- `docs/ARCHITECTURE.md` - Updated with new search strategies

---

## Development Approach

**Suggested Steps:**

1. **Study Prior Outputs** (~10 min)
   - Read `psalm_029_macro.md` to understand the macro thesis
   - Read `psalm_029_micro.md` to see verse discoveries
   - Browse `psalm_029_research.md` to see available data

2. **Design Prompts** (~30 min)
   - Craft introduction essay prompt (with thesis revision authority)
   - Craft verse commentary prompt (with research integration guidelines)
   - Consider extended thinking budget allocation

3. **Implement SynthesisWriter** (~60 min)
   - Create `src/agents/synthesis_writer.py`
   - Implement two-stage process (intro + verse-by-verse)
   - Add comprehensive logging
   - Handle research bundle integration

4. **Build Test Script** (~30 min)
   - Create `tests/test_synthesis_writer.py`
   - Load all three prior outputs (macro + micro + research)
   - Run synthesis and validate outputs

5. **Run Test on Psalm 29** (~5 min runtime)
   - Execute: `python tests/test_synthesis_writer.py`
   - Review outputs in `output/phase3_test/`
   - Validate essay quality and research integration

6. **Review and Iterate** (~20 min)
   - Read generated commentary critically
   - Check for thesis coherence
   - Verify research citations
   - Ensure accessibility and scholarly rigor

---

## Success Criteria for Phase 3c

Phase 3c will be complete when:

1. ✅ `src/agents/synthesis_writer.py` implemented (~500 LOC)
2. ✅ `tests/test_synthesis_writer.py` passing
3. ✅ `output/phase3_test/psalm_029_synthesis.json` generated
4. ✅ `output/phase3_test/psalm_029_synthesis.md` is readable and scholarly
5. ✅ Introduction essay is 800-1200 words
6. ✅ All 11 verses have detailed commentary
7. ✅ Research is smoothly integrated with proper citations
8. ✅ Thesis is coherent (revised if needed)
9. ✅ Log file in `logs/synthesis_writer_*.log` shows process

**After Phase 3c:**
- Phase 3d: Build Critic agent (Pass 4) - test Haiku vs Sonnet
- Phase 3e: Build FinalPolisher agent (Pass 5)
- Phase 3f: End-to-end integration testing
- Phase 3g: Production deployment for all 150 psalms

---

## Recent Changes to Be Aware Of

**Pipeline Improvements (Oct 17):**

The research pipeline now provides MORE comprehensive data:

1. **Concordance Searches** - Higher Recall
   - Default level changed from "exact" to "consonantal"
   - Captures all root forms regardless of vowel pointing
   - "Exact" reserved only for homograph disambiguation
   - **Impact**: Expect 20-30% more concordance results

2. **Figurative Language** - Broader Coverage
   - No longer filters by specific type (metaphor vs. simile vs. personification)
   - Retrieves ALL figurative instances for a verse
   - Only filters by vehicle/target when specified
   - **Impact**: More comprehensive figurative context

**What This Means for SynthesisWriter:**
- Research bundles now contain richer data
- More concordance patterns to reference
- Broader figurative language context
- Better foundation for synthesis

**Code Changes:**
- `src/agents/micro_analyst.py` - Updated prompts and examples
- `src/agents/scholar_researcher.py` - Updated prompts and parsing logic
- `docs/ARCHITECTURE.md` - Enhanced search documentation

**Git Status:**
- Committed: `acdec5c` - "Pipeline Refinements: Improve Search Recall & Reduce Filtering"
- Clean working directory (ready for Phase 3c work)

---

## Quick Start Command

```bash
cd c:\Users\ariro\OneDrive\Documents\Psalms
source venv/Scripts/activate  # or: venv\Scripts\activate on Windows

# Review prior outputs first
cat output/phase3_test/psalm_029_macro.md
cat output/phase3_test/psalm_029_micro.md
head -100 output/phase3_test/psalm_029_research.md

# Review recent pipeline improvements
git log -1 --stat

# Then build and test SynthesisWriter
python tests/test_synthesis_writer.py
```

---

**Last Updated**: 2025-10-17 Evening (Pipeline refinements complete, Phase 3c ready to start)
**Next Agent**: SynthesisWriter (Pass 3)
**Test Psalm**: Psalm 29 (rich prior outputs available)
**Recent Changes**: Concordance/figurative search improvements for better data retrieval
