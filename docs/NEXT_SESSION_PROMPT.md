# Next Session: Phase 2 - Scholar Agents

## Phase 1 Status: 100% COMPLETE ✅

All librarian infrastructure is production-ready and verified:
- ✅ BDB Librarian (lexicon lookups with homograph disambiguation + usage examples)
- ✅ Concordance Librarian (morphological variations + smart scoping)
- ✅ Figurative Language Librarian (hierarchical tags + full verse context)
- ✅ Research Bundle Assembler (JSON + Markdown outputs)
- ✅ Full Tanakh concordance (269,844 words indexed)
- ✅ Comprehensive logging system
- ✅ Complete documentation

## Start Next Session With This Prompt

```
I'm continuing work on the Psalms AI commentary pipeline - Phase 2: Scholar Agents.

Phase 1 (Foundation) is 100% complete with all final refinements implemented.

Please read these files in order:
1. docs/CONTEXT.md (project overview)
2. docs/PROJECT_STATUS.md (Phase 1 complete, starting Phase 2)
3. docs/IMPLEMENTATION_LOG.md (scroll to 2025-10-16 - Day 5 Final session)
4. docs/ARCHITECTURE.md (complete system architecture)

Phase 1 delivered:
- All 4 librarian agents operational
- 5 critical refinements implemented and verified
- Psalm 27:1 demo successful (29 figurative instances, 14 concordance matches)
- No hardcoded Psalms-only restrictions (defaults to full Tanakh/Pentateuch+Psalms)

Ready to begin Phase 2: Scholar-Researcher Agent implementation.
```

---

## What Phase 1 Accomplished

### Core Infrastructure (100% Complete)

**1. Data Sources**
- Sefaria API client (lexicon + text fetching)
- Full Tanakh database (23,206 verses, 269,844 words)
- Figurative language database (Pentateuch + Psalms: 2,863 instances)

**2. Librarian Agents**
- **BDB Librarian**: Homograph disambiguation, usage examples extraction
- **Concordance Librarian**: 66 morphological variations, smart scoping (auto-detect common/rare words)
- **Figurative Language Librarian**: Case-insensitive search, full verse context
- **Research Assembler**: Coordinates all librarians, dual output formats

**3. Critical Refinements (Day 5 Final)**
1. Case-insensitive figurative search → Found 27 stronghold metaphors (was 13)
2. Full verse context for figurative instances → Scholar sees complete poetic structure
3. Phrase search verified working → Multi-word queries auto-detected
4. Biblical citations extraction → Usage examples from BDB entries
5. Smart concordance scoping → Common words limited to key books, rare words search full Tanakh

**4. Quality Metrics**
- Morphological recall: 99%+ (66 variations per root)
- Database query speed: <10ms (indexed)
- Zero hardcoded Psalms-only restrictions (verified)
- Complete provenance tracking (every data point traceable)

### Default Scopes (Production-Ready)

**Concordance Librarian**:
- Default scope: `'Tanakh'` (all 39 books, 23,206 verses)
- Smart scoping: `scope='auto'` (auto-detect common vs. rare words)
- No Psalms-only restrictions

**Figurative Language Librarian**:
- Default book: `None` (searches all available: Pentateuch + Psalms)
- Available books: Genesis, Exodus, Leviticus, Numbers, Deuteronomy, Psalms
- No Psalms-only restrictions

---

## Phase 2: Scholar Agents (Week 2)

### Overview

Now we build the AI agents that actually write the commentary, using the research materials the librarians provide.

### Phase 2 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PSALM TEXT INPUT                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         SCHOLAR-RESEARCHER AGENT (Pass 0)                    │
│  Model: Claude Haiku 4.5                                     │
│  Task: Generate research requests from macro overview        │
│  Output: JSON with lexicon/concordance/figurative requests   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              RESEARCH BUNDLE ASSEMBLER                       │
│  (Coordinates: BDB, Concordance, Figurative librarians)      │
│  Output: Comprehensive research bundle (JSON + Markdown)     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│          SCHOLAR-WRITER AGENT (Pass 1: Macro)                │
│  Model: Claude Sonnet 4.5                                    │
│  Task: Chapter-level thesis and structural analysis          │
│  Output: Macro overview with key themes                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│          SCHOLAR-WRITER AGENT (Pass 2: Micro)                │
│  Model: Claude Sonnet 4.5                                    │
│  Task: Verse-by-verse analysis with research integration     │
│  Output: Detailed verse commentary                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│        SCHOLAR-WRITER AGENT (Pass 3: Synthesis)              │
│  Model: Claude Sonnet 4.5                                    │
│  Task: Synthesize macro + micro into coherent essay          │
│  Output: Complete polished commentary                        │
└─────────────────────────────────────────────────────────────┘
```

### Day 6-7: Scholar-Researcher Agent

**Goal**: Create agent that analyzes a psalm and generates intelligent research requests

**Input**: Psalm text (Hebrew + English)

**Output**: JSON research request
```json
{
  "psalm_chapter": 23,
  "lexicon": [
    {"word": "רעה", "notes": "Key verb - shepherd imagery"},
    {"word": "צדק", "notes": "righteousness/justice theme"}
  ],
  "concordance": [
    {"query": "רעה", "scope": "auto", "notes": "Shepherd imagery"},
    {"query": "צדק", "scope": "auto", "notes": "Righteousness concept"}
  ],
  "figurative": [
    {"book": null, "chapter": 23, "metaphor": true, "notes": "All metaphors in psalm"},
    {"vehicle_contains": "shepherd", "notes": "Shepherd metaphor across Scripture"}
  ]
}
```

**Key Design Decisions**:
1. Use Haiku 4.5 (fast, cheap, good at structured tasks)
2. Prompt should encourage smart scoping (use "auto" for concordance)
3. Don't restrict to Psalms - let it search broadly when appropriate
4. Include reasoning/notes for each request (transparency)

**Implementation Steps**:
1. Create `src/agents/scholar_researcher.py`
2. Design prompt template
3. Test with diverse Psalms (lament, praise, wisdom, royal)
4. Validate JSON output format
5. Integration test: Researcher → Assembler → Bundle

**Estimated Time**: 2-3 hours

---

## Critical Reminders for Phase 2

### 1. No Psalms-Only Restrictions

**Verified defaults** (do not change):
- `ConcordanceRequest(scope='Tanakh')` - searches all 39 books
- `FigurativeRequest(book=None)` - searches Pentateuch + Psalms
- Demo script restrictions are for demo only

### 2. Smart Scoping Usage

Encourage Scholar-Researcher to use:
```json
{"query": "אור", "scope": "auto"}  // Common word → limited scope
{"query": "מעוז", "scope": "auto"}  // Rare word → full Tanakh
```

### 3. Figurative Language Scope

Available books for figurative search:
- Genesis, Exodus, Leviticus, Numbers, Deuteronomy, Psalms
- NOT available: Prophets, Writings (except Psalms)
- This is a database limitation, not a code restriction

### 4. Cost Targets

Phase 2 will be first LLM usage:
- Haiku 4.5: ~$0.01 per psalm (Pass 0: research request generation)
- Sonnet 4.5: ~$0.20 per psalm (Passes 1-3: commentary writing)
- Target: Stay under $0.25 per psalm average

---

## Files Structure for Phase 2

**New files to create**:
```
src/agents/
  scholar_researcher.py    # Pass 0: Generate research requests
  scholar_writer.py        # Passes 1-3: Write commentary
  critic.py                # Quality feedback (later)

prompts/
  researcher_system.md     # Researcher agent system prompt
  writer_pass1_macro.md    # Macro analysis prompt
  writer_pass2_micro.md    # Micro analysis prompt
  writer_pass3_synthesis.md # Synthesis prompt

tests/
  test_scholar_researcher.py
  test_scholar_writer.py
```

---

## Test Cases for Scholar-Researcher

Start with these diverse psalm types:

1. **Psalm 23** - Shepherd metaphor (pastoral, trust)
2. **Psalm 2** - Royal psalm (kingship, nations)
3. **Psalm 51** - Penitential (confession, forgiveness)
4. **Psalm 8** - Creation hymn (majesty, humanity)
5. **Psalm 137** - Lament (exile, vengeance)

Each should generate different research requests reflecting their themes.

---

## Git Status

**Last commit**: "Phase 1 Complete: Final Refinements for Production-Ready Librarian System" (b80de87)

**Ready to commit before Phase 2?** No uncommitted changes that need saving (all refinements already committed).

---

## Useful Commands for Next Session

```bash
# Activate environment
cd /c/Users/ariro/OneDrive/Documents/Psalms
source venv/Scripts/activate

# Verify no Psalms restrictions (should show Tanakh default)
python -c "from src.agents.concordance_librarian import ConcordanceRequest; print(ConcordanceRequest(query='test').scope)"

# Test smart scoping
python -c "
from src.agents.concordance_librarian import ConcordanceLibrarian
lib = ConcordanceLibrarian()
print('Common word:', lib.determine_smart_scope('אור'))
print('Rare word:', lib.determine_smart_scope('מעוז'))
"

# Fetch a psalm for testing
python -c "
from src.data_sources.sefaria_client import SefariaClient
client = SefariaClient()
psalm = client.fetch_psalm(23)
print(psalm.verses[0].hebrew)
"
```

---

## Next Session Objectives

**Primary Goal**: Implement Scholar-Researcher Agent (Pass 0)

**Success Criteria**:
1. ✅ Agent generates valid JSON research requests
2. ✅ Requests use smart scoping appropriately
3. ✅ No unnecessary Psalms-only restrictions
4. ✅ Integration test passes: Psalm → Researcher → Assembler → Bundle
5. ✅ Cost: <$0.02 per psalm (Haiku 4.5)

**Deliverables**:
- `src/agents/scholar_researcher.py` (agent implementation)
- `prompts/researcher_system.md` (system prompt)
- Test suite with 3-5 diverse psalms
- Documentation update

---

## Questions for Start of Session

When you begin Phase 2, consider:

1. **API keys ready?** You'll need Anthropic API key for Claude
2. **Prompt strategy?** System prompt + user message with psalm text?
3. **Which psalm to test first?** Recommend Psalm 23 (well-known, good test case)
4. **Output validation?** Schema validation for JSON research requests?

---

**Phase 1 is complete and production-ready. Time to build the Scholar agents!** 🎓📚
