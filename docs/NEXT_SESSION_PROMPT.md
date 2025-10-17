# Next Session Prompt - Phase 3b: LXX Integration + MicroAnalyst (Pass 2)

## Current Status: Phase 3a COMPLETE ✅

**What We Just Finished:**
- ✅ Created analysis schemas system (MacroAnalysis, MicroAnalysis, SynthesisOutput, CriticFeedback)
- ✅ Implemented MacroAnalyst agent (Pass 1) with Sonnet 4.5 + extended thinking
- ✅ Tested with Psalm 29 - excellent results!
- ✅ Refined architecture to 5-pass system
- ✅ Documented everything in PHASE3_ARCHITECTURE.md

**MacroAnalyst Works Beautifully:**
- Generates sophisticated thesis ("liturgical polemic that systematically transfers Baal's storm-god attributes to YHWH")
- Identifies 3 structural divisions
- Names 5 poetic devices (anaphora, inclusio, climactic parallelism, etc.)
- Produces 5 research questions for Pass 2
- Processing: ~45 seconds, ~$0.08 per psalm

---

## Next Task: Phase 3b - LXX Integration + MicroAnalyst

### Objective
1. **Add LXX (Greek Septuagint) to RAG Manager** so all agents can access ancient Greek translation
2. **Build MicroAnalyst agent** (Pass 2) that generates research requests and produces detailed verse-by-verse analysis

---

## Task 1: LXX Integration into RAG Manager

### Why LXX?
- Provides ancient interpretive tradition (3rd-2nd century BCE)
- Greek word choices reveal how early translators understood ambiguous Hebrew
- Illuminates textual variants and interpretive decisions
- Adds scholarly depth to all agents

### Implementation Steps

#### 1. Extend RAGContext Dataclass
**File**: `src/agents/rag_manager.py`

Add LXX field to RAGContext:
```python
@dataclass
class RAGContext:
    """Container for RAG documents relevant to a specific psalm/verse"""
    psalm_number: int
    verse_number: Optional[int] = None
    analytical_framework: str = ""
    psalm_function: Optional[Dict[str, Any]] = None
    ugaritic_parallels: List[Dict[str, Any]] = None
    lxx_text: Optional[str] = None  # ← ADD THIS
```

#### 2. Load LXX in get_rag_context()
Modify `get_rag_context()` to fetch LXX:
```python
def get_rag_context(self, psalm_number: int, verse_number: Optional[int] = None) -> RAGContext:
    # Fetch LXX text (already have fetch_lxx_psalm in sefaria_client)
    from ..data_sources.sefaria_client import SefariaClient
    sefaria = SefariaClient()

    # If verse_number specified, get that verse only
    # Otherwise get full psalm
    lxx_psalm = sefaria.fetch_lxx_psalm(psalm_number)
    if verse_number and lxx_psalm:
        lxx_text = next((v.lxx for v in lxx_psalm.verses if v.verse == verse_number), None)
    elif lxx_psalm:
        lxx_text = "\n".join([f"v{v.verse}: {v.lxx}" for v in lxx_psalm.verses if v.lxx])
    else:
        lxx_text = None

    context = RAGContext(
        psalm_number=psalm_number,
        verse_number=verse_number,
        analytical_framework=self.load_analytical_framework(),
        psalm_function=self.get_psalm_function(psalm_number),
        ugaritic_parallels=self.get_ugaritic_parallels(psalm_number, verse_number),
        lxx_text=lxx_text  # ← ADD THIS
    )
    return context
```

#### 3. Update format_for_prompt()
Add LXX section to formatted output:
```python
def format_for_prompt(self, context: RAGContext, include_framework: bool = True) -> str:
    sections = []

    # ... existing sections ...

    # Section: LXX Translation (if available)
    if context.lxx_text:
        sections.append("\n## LXX (SEPTUAGINT - GREEK TRANSLATION)")
        sections.append(context.lxx_text)

    # ... rest of sections ...
```

#### 4. Test LXX Integration
```bash
python -c "from src.agents.rag_manager import RAGManager; mgr = RAGManager(); ctx = mgr.get_rag_context(29); print('LXX length:', len(ctx.lxx_text) if ctx.lxx_text else 0)"
```

**Expected**: LXX text loaded for Psalm 29

---

## Task 2: MicroAnalyst Agent (Pass 2)

### Architecture Overview

The MicroAnalyst is the most complex agent:
- **Receives**: MacroAnalysis (thesis, structure, research questions) + RAG context + Psalm text
- **Generates**: Research requests (BDB, concordance, figurative, commentary)
- **Calls**: Research Assembler → Librarians fetch data
- **Produces**: Detailed verse-by-verse analysis integrating all research
- **Outputs**: MicroAnalysis object + Research Bundle

### Implementation Steps

#### 1. Design MicroAnalyst Prompt

The prompt must:
1. Receive macro thesis and research questions
2. Generate specific research requests (25-50 BDB words, concordance searches, figurative checks, commentary verses)
3. **Wait for research data** (two-stage process)
4. Analyze each verse with research integrated
5. Show how each verse supports macro thesis

**Two-Stage Approach:**

**Stage 1: Generate Research Requests**
```
INPUT: MacroAnalysis + Psalm text + RAG context
TASK: Generate research requests
OUTPUT: JSON with bdb_requests, concordance_requests, figurative_requests, commentary_requests
```

**Stage 2: Verse-by-Verse Analysis**
```
INPUT: MacroAnalysis + Research Bundle + Psalm text + RAG context
TASK: Analyze each verse with research
OUTPUT: MicroAnalysis object (verse commentaries)
```

#### 2. Create micro_analyst.py

**File Structure**:
```python
class MicroAnalyst:
    def __init__(self, api_key, db_path, docs_dir):
        self.client = anthropic.Anthropic(api_key)
        self.model = "claude-sonnet-4-20250514"
        self.rag_manager = RAGManager(docs_dir)
        self.db = TanakhDatabase(db_path)
        self.research_assembler = ResearchAssembler()

    def analyze_psalm(self, psalm_number: int, macro_analysis: MacroAnalysis) -> Tuple[MicroAnalysis, ResearchBundle]:
        """
        Two-stage analysis:
        1. Generate research requests
        2. Analyze verses with research data
        """
        # Stage 1: Generate research requests
        research_request = self._generate_research_requests(psalm_number, macro_analysis)

        # Stage 2: Fetch research data
        research_bundle = self.research_assembler.assemble(research_request)

        # Stage 3: Verse-by-verse analysis
        micro_analysis = self._analyze_verses(psalm_number, macro_analysis, research_bundle)

        return micro_analysis, research_bundle

    def _generate_research_requests(self, psalm_number, macro_analysis) -> ResearchRequest:
        # Call Sonnet 4.5 with RESEARCH_REQUEST_PROMPT
        # Parse JSON response
        # Return ResearchRequest object
        pass

    def _analyze_verses(self, psalm_number, macro_analysis, research_bundle) -> MicroAnalysis:
        # Call Sonnet 4.5 with VERSE_ANALYSIS_PROMPT
        # Parse JSON response
        # Return MicroAnalysis object
        pass
```

#### 3. Research Request Prompt

**Inspiration**: Use existing `scholar_researcher.py` prompt as template

**Key Requirements**:
- Comprehensive BDB requests (2-4 words per verse → 25-50 total for average psalm)
- Strategic concordance searches (thematic roots/phrases)
- Figurative language verse identification
- Commentary requests (2-5 key verses)

**Reuse Scholar-Researcher Logic:**
The existing Scholar-Researcher agent has excellent prompt. Copy and adapt it for MicroAnalyst's Stage 1.

#### 4. Verse Analysis Prompt

**Structure**:
```
You are analyzing Psalm {psalm_number} verse-by-verse.

MACRO THESIS (from Pass 1):
{macro_analysis.thesis_statement}

STRUCTURAL OUTLINE:
{macro_analysis.structural_outline}

RESEARCH QUESTIONS:
{macro_analysis.research_questions}

RESEARCH DATA:
{research_bundle.to_markdown()}

TASK:
For each verse, provide:
1. Verse text (Hebrew + English + LXX)
2. Lexical insights (from BDB data)
3. Figurative analysis (from figurative data)
4. Traditional commentary insights (from 6 commentators)
5. Thematic connections (from concordance)
6. How this verse supports the macro thesis

OUTPUT: JSON array of verse commentaries
```

#### 5. Test with Psalm 29

**Test Flow**:
1. Load Psalm 29 MacroAnalysis (from Phase 3a output)
2. Run MicroAnalyst Stage 1 → Get research requests
3. Verify requests look reasonable (25-50 BDB, concordance, etc.)
4. Run MicroAnalyst Stage 2 → Get verse-by-verse analysis
5. Validate: Each verse has commentary with research integrated

---

## File Structure After Phase 3b

```
src/agents/
├── macro_analyst.py         # Pass 1 ✅ COMPLETE
├── micro_analyst.py         # Pass 2 ← BUILD THIS
├── synthesis_writer.py      # Pass 3 (future)
├── critic.py                # Pass 4 (future)
├── final_polisher.py        # Pass 5 (future)
├── rag_manager.py           # ← UPDATE WITH LXX
├── research_assembler.py    # ✅ Already works
├── scholar_researcher.py    # ✅ Reuse prompt logic
└── [4 librarians]           # ✅ Already work

src/schemas/
└── analysis_schemas.py      # ✅ COMPLETE

tests/
├── test_macro_analyst.py    # ✅ COMPLETE
└── test_micro_analyst.py    # ← BUILD THIS
```

---

## Success Criteria for Phase 3b

✅ LXX text loads correctly in RAGContext for all psalms
✅ MicroAnalyst Stage 1 generates comprehensive research requests:
  - 25-50 BDB entries (2-4 words per verse)
  - 5-10 concordance searches (thematic roots)
  - 3-8 figurative language verse checks
  - 2-5 commentary verse requests
✅ Research Assembler successfully fetches all data
✅ MicroAnalyst Stage 2 produces verse-by-verse analysis:
  - Each verse has commentary
  - Lexical insights integrated
  - Figurative analysis integrated
  - Traditional commentary integrated
  - Shows connection to macro thesis
✅ MicroAnalysis object properly structured and serializable
✅ Test with Psalm 29 passes end-to-end

---

## Session Start Commands

```bash
cd /c/Users/ariro/OneDrive/Documents/Psalms
source venv/Scripts/activate

# Read context
cat docs/CONTEXT.md
cat docs/PROJECT_STATUS.md
tail -100 docs/IMPLEMENTATION_LOG.md

# Review Phase 3a work
cat docs/PHASE3_ARCHITECTURE.md
cat output/phase3_test/psalm_029_macro.md

# Verify RAG Manager current state
python -c "from src.agents.rag_manager import RAGManager; mgr = RAGManager(); ctx = mgr.get_rag_context(29); print(f'Psalm 29: {ctx.psalm_function[\"genre\"]}, {len(ctx.ugaritic_parallels)} parallels')"
```

---

## Estimated Scope

**Phase 3b Tasks**:
1. LXX integration: 0.5 hours
2. MicroAnalyst research request generation: 1.5 hours
3. MicroAnalyst verse analysis: 2 hours
4. Testing and refinement: 1 hour
5. Documentation: 0.5 hours

**Total**: ~5-6 hours (2 sessions)

---

## Key Design Principles

1. **Two-Stage Process**: Separate research request generation from analysis
2. **Deep Thinking**: Use extended thinking for both stages
3. **Thesis-Driven**: Every verse commentary must connect to macro thesis
4. **Research Integration**: Seamlessly blend BDB, concordance, figurative, commentary data
5. **Comprehensive Coverage**: 25-50 BDB requests per psalm (not just 5-8)

---

## Notes

- MicroAnalyst will reuse Scholar-Researcher prompt logic for Stage 1
- Research Assembler already works perfectly - just call it
- MicroAnalysis schema already defined - just populate it
- Psalm 29 is our test case throughout

---

## What to Tell the Next AI Assistant

```
I'm continuing work on the Psalms AI commentary pipeline.

Phase 3a is COMPLETE:
- ✅ MacroAnalyst agent built and tested (Pass 1)
- ✅ Excellent results with Psalm 29
- ✅ 5-pass architecture documented

Phase 3b is NEXT:
1. Add LXX (Greek Septuagint) to RAG Manager
2. Build MicroAnalyst agent (Pass 2) with:
   - Research request generation (Stage 1)
   - Verse-by-verse analysis (Stage 2)
   - Integration with Research Assembler

Please read:
1. docs/NEXT_SESSION_PROMPT.md (this file)
2. docs/PHASE3_ARCHITECTURE.md (5-pass system)
3. docs/IMPLEMENTATION_LOG.md (last entry - Phase 3a results)

Let's start with Task 1: Add LXX to RAG Manager.
```

---

**Priority**: HIGH - Phase 3b is critical foundation for remaining passes

**Status**: Ready to begin
