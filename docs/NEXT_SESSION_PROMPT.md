# Next Session Prompt - Phase 2d: RAG Integration

## Current Status
✅ **Phase 2c COMPLETE** - Commentary Librarian fully integrated with Research Assembler
- All 4 librarians operational and integrated
- 6 commentators supported (Rashi, Ibn Ezra, Radak, Metzudat David, Malbim, Meiri)
- Research infrastructure complete and ready for Scholar-Writer agents

## Next Task: Phase 2d - RAG Document Integration

### Objective
Before implementing Scholar-Writer agents (Phase 3), integrate RAG documents to provide:
1. **Analytical framework** (always available to deep-thinking agents)
2. **Ugaritic comparisons** (verse-specific contextual knowledge)

### RAG Requirements

#### 1. Analytical Framework (`docs/analytical_framework_for_RAG.md`)
- **When**: ALWAYS included in Scholar-Writer agent prompts
- **How**: Load once as system context for all Psalms
- **Purpose**: Provides methodology for analyzing Hebrew poetry
  - Parallelism types (synonymous, antithetic, synthetic)
  - Poetic diction (terseness, concrete imagery)
  - Figurative language (metaphor, simile, merism, personification)
  - Macro-structures (chiasmus, inclusio, refrain)
  - Sound devices (paronomasia, alliteration, assonance)

#### 2. Ugaritic Comparisons (`docs/Ugaritic_comparisons_for_RAG.md`)
- **When**: ONLY when verse-specific data is available
- **How**: Parse JSON, filter by psalm:verse, inject relevant entries only
- **Purpose**: Provides ancient Near Eastern context
- **Structure**: JSON database with 25+ entries
  - Each entry has `hebrew_psalter_source.text_reference` (e.g., "Psalm 27:10")
  - Filter by psalm/verse to extract relevant parallels
  - Inject only matching entries into Scholar-Writer context

### Implementation Tasks

1. **Parse Ugaritic JSON**
   - Extract JSON array from markdown file
   - Create verse-lookup index: `{"psalm": 27, "verse": 10}` → relevant entries
   - Handle verse ranges (e.g., "Psalm 29:3-9" → verses 3,4,5,6,7,8,9)

2. **Create RAG Manager Module** (`src/agents/rag_manager.py`)
   ```python
   class RAGManager:
       def __init__(self):
           self.analytical_framework = self.load_analytical_framework()
           self.ugaritic_index = self.parse_ugaritic_json()

       def get_context_for_psalm(self, psalm_num: int, verses: List[int]) -> str:
           # Always include analytical framework
           # Add verse-specific Ugaritic parallels if available
           pass
   ```

3. **Design Injection Strategy**
   - Analytical framework: Include in system prompt (always)
   - Ugaritic data: Inject into research bundle markdown (verse-specific)
   - Create new section in ResearchBundle.to_markdown(): "## Ancient Near Eastern Context"

4. **Test with Sample Verses**
   - Psalm 27:10 (father/mother pair - PWP_14)
   - Psalm 68:5 (Rider on Clouds - DE_01)
   - Psalm 74:13 (Chaoskampf - CM_01)
   - Psalm 29:1 (Divine Council - DC_02)

### Success Criteria
✅ Analytical framework loads successfully (~50KB)
✅ Ugaritic JSON parses into verse-indexed dictionary
✅ RAG manager filters verse-specific entries correctly
✅ Research bundle includes relevant Ugaritic parallels when available
✅ Test output shows correct context for sample verses

### Files to Create/Modify
- **NEW**: `src/agents/rag_manager.py` (~300 LOC)
- **MODIFY**: `src/agents/research_assembler.py` (add Ugaritic section to markdown)
- **MODIFY**: `src/agents/scholar_researcher.py` (use RAG manager for context awareness)

### Next Session Start Commands
```bash
cd /c/Users/ariro/OneDrive/Documents/Psalms
source venv/Scripts/activate

# Read context files
cat docs/CONTEXT.md
cat docs/PROJECT_STATUS.md
tail -100 docs/IMPLEMENTATION_LOG.md
```

### Priority
**HIGH** - RAG integration must precede Phase 3 (Scholar-Writer) to ensure deep-thinking agents have proper analytical framework and cultural context.

## After RAG Integration: Phase 3
Once RAG is complete, proceed to Phase 3: Scholar-Writer Agents
- Pass 1: Macro Analysis (chapter-level thesis with analytical framework)
- Pass 2: Micro Analysis (verse-by-verse with full research bundle + RAG)
- Pass 3: Synthesis (coherent essay integrating all sources)
