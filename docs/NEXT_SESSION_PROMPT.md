# Next Session Prompt - Phase 3: Scholar-Writer Agent (Pass 1)

## Current Status
✅ **Phase 2d COMPLETE** - RAG Integration Successfully Implemented
- All 4 librarians operational and integrated (BDB, Concordance, Figurative, Commentary)
- RAG Manager created and integrated with Research Assembler
- 3 RAG documents automatically available:
  1. **Analytical Framework** (~1,200 lines) - Poetic analysis methodology
  2. **Psalm Function Database** (150 entries) - Genre, structure, keywords per psalm
  3. **Ugaritic Comparisons** (27 parallels) - Ancient Near Eastern context
- Research infrastructure 100% complete - Ready for Scholar-Writer agents

### What RAG Provides (Automatically)
Example: Psalm 29 automatically receives:
- **Genre**: Hymn of Praise
- **Structure**: 3-part outline (vv. 1-2, 3-9, 10-11)
- **Keywords**: power, voice, worship, majesty, peace
- **Ugaritic Parallels**: 3 found (Divine Epithet, Divine Council, Poetic Word Pair)
- **Full Analytical Framework**: Complete methodology for poetic analysis

### Phase 2 Architecture Summary
```
Research Assembler
├── BDB Librarian (lexicon entries)
├── Concordance Librarian (word searches)
├── Figurative Librarian (metaphor/simile instances)
├── Commentary Librarian (6 traditional commentators)
└── RAG Manager (scholarly context)
    ├── Analytical Framework (always)
    ├── Psalm Function (psalm-specific)
    └── Ugaritic Parallels (verse-specific)
```

Total Phase 2 code: ~2,800 LOC across 6 modules

---

## Next Task: Phase 3 - Scholar-Writer Agent Architecture

### Objective
Implement a **three-pass writing system** where each pass builds on the previous:
1. **Pass 1** (Macro): Chapter-level thesis with analytical framework
2. **Pass 2** (Micro): Verse-by-verse analysis with full research
3. **Pass 3** (Synthesis): Coherent essay integrating all insights

### Phase 3 Overview: Three-Pass Architecture

#### Pass 1: Macro Analysis Agent
**Model**: Sonnet 4.5 (deep thinking)
**Input**:
- Psalm text (Hebrew + English)
- RAG context (genre, structure, keywords)
- Analytical framework (poetic methodology)

**Output**: High-level thesis document
- Overall theme and message
- Major structural divisions
- Key poetic devices and their function
- Theological/historical significance
- Research questions for Pass 2

**File**: `src/agents/macro_analyst.py` (~400 LOC)

#### Pass 2: Micro Analysis Agent
**Model**: Sonnet 4.5 (deep thinking)
**Input**:
- Pass 1 thesis
- Full research bundle (lexicon, concordance, figurative, commentary, RAG)
- Verse-by-verse breakdown

**Output**: Detailed analysis document
- Verse-by-verse commentary
- Lexical insights from BDB
- Figurative language analysis
- Traditional commentary integration
- Ugaritic parallels where relevant
- How each verse supports overall thesis

**File**: `src/agents/micro_analyst.py` (~500 LOC)

#### Pass 3: Synthesis Agent
**Model**: Sonnet 4.5 (essay writing)
**Input**:
- Pass 1 thesis
- Pass 2 detailed analysis
- Original research bundle

**Output**: Polished scholarly commentary
- Coherent essay format
- Smooth narrative flow
- Integration of all research sources
- Proper citations and references
- Academic yet accessible prose

**File**: `src/agents/synthesis_writer.py` (~400 LOC)

#### Critic/Revision Agent (Optional)
**Model**: Haiku 4.5 (fast, critical review)
**Purpose**: Review each pass for quality, coherence, accuracy
**File**: `src/agents/critic.py` (~200 LOC)

---

## Implementation Plan: Phase 3a - Pass 1 (Macro Analysis)

### Step 1: Design Macro Analysis Prompt
Create a prompt that leverages the analytical framework to produce a sophisticated thesis:
- Identify overall genre and function (from RAG)
- Analyze macro-structure (inclusio, chiasmus, refrain patterns)
- Identify dominant poetic techniques (parallelism types, imagery)
- Propose thematic thesis
- Generate research questions for Pass 2

### Step 2: Create MacroAnalyst Agent
```python
class MacroAnalyst:
    """
    Pass 1: Chapter-level analysis with analytical framework.
    Produces high-level thesis for micro analysis to build upon.
    """
    def __init__(self):
        self.rag_manager = RAGManager()
        self.anthropic_client = Anthropic()

    def analyze_psalm(self, psalm_num: int) -> MacroAnalysis:
        # Get RAG context (genre, structure, analytical framework)
        # Call Sonnet 4.5 with extended thinking time
        # Return thesis document with research questions
        pass
```

### Step 3: Define Output Schema
Create dataclass for MacroAnalysis output:
- `thesis_statement`: Overall argument
- `structural_outline`: Major divisions
- `poetic_devices`: Key techniques identified
- `research_questions`: List of questions for Pass 2
- `working_notes`: Raw analytical thinking

### Step 4: Test with Sample Psalm
Test with Psalm 29 (has rich Ugaritic context):
- Should identify: Hymn of Praise genre
- Should recognize: Divine Council opening, Storm Theophany, Royal conclusion
- Should detect: Anaphora ("The voice of the LORD" 7x)
- Should propose: Thesis about Yahweh's supremacy over Baal

---

## Files to Create in This Session

### 1. `src/agents/macro_analyst.py`
- MacroAnalyst class
- Integration with RAG Manager
- Anthropic API calls with extended thinking
- Output validation and parsing

### 2. `src/schemas/analysis_schemas.py`
- MacroAnalysis dataclass
- MicroAnalysis dataclass (for future)
- SynthesisOutput dataclass (for future)

### 3. `tests/test_macro_analyst.py`
- Test with Psalm 29
- Verify RAG integration
- Check output quality

---

## Success Criteria for Pass 1

✅ MacroAnalyst successfully loads RAG context (genre, structure, framework)
✅ Generates coherent thesis statement for test psalm
✅ Identifies key structural divisions accurately
✅ Recognizes dominant poetic techniques
✅ Produces meaningful research questions for Pass 2
✅ Output is well-formatted and parseable

---

## Next Session Start Commands

```bash
cd /c/Users/ariro/OneDrive/Documents/Psalms
source venv/Scripts/activate

# Read context files
cat docs/CONTEXT.md
cat docs/PROJECT_STATUS.md
tail -100 docs/IMPLEMENTATION_LOG.md

# Verify RAG Manager is working
python -c "from src.agents.rag_manager import RAGManager; mgr = RAGManager(); ctx = mgr.get_rag_context(29); print(f'Psalm 29: {ctx.psalm_function[\"genre\"]}, {len(ctx.ugaritic_parallels)} parallels')"
```

---

## Design Notes for Scholar-Writer Agents

### Key Principles
1. **Telescoping Analysis**: Start broad (macro), zoom in (micro), synthesize (essay)
2. **Iterative Refinement**: Each pass builds on and refines previous work
3. **Multi-Source Integration**: Seamlessly blend lexicon, concordance, figurative, commentary, RAG
4. **Scholarly Rigor**: Academic quality with proper methodology
5. **Accessible Prose**: Sophisticated but readable for educated lay audience

### Prompt Engineering Strategy
- Use extended thinking mode for Sonnet 4.5
- Provide analytical framework as methodological guide
- Use RAG context to ground analysis in scholarship
- Structure prompts with clear sections and expected outputs
- Include examples of high-quality commentary style

### Quality Control
- Critic agent reviews for:
  - Factual accuracy (cross-reference with sources)
  - Logical coherence (thesis → evidence → conclusion)
  - Writing quality (clear, engaging, properly cited)
  - Integration quality (smooth blending of sources)

---

## Priority
**HIGH** - Phase 3a (Pass 1: Macro Analysis) is the foundation for the entire writing system. Get this right, and the rest flows naturally.

## Estimated Scope
- **Phase 3a** (Pass 1): 1-2 sessions
- **Phase 3b** (Pass 2): 2-3 sessions
- **Phase 3c** (Pass 3): 1-2 sessions
- **Phase 3d** (Critic/Revision): 1 session

**Total Phase 3**: 5-8 sessions to complete full three-pass writing system
