# Next Session Prompt - Phase 2b: Expanding Scholarly Resources

## Session Start Instructions

I'm continuing work on the Psalms AI commentary pipeline - Phase 2b: Expanding Scholarly Resources.

**Phase 2 Day 6 (Scholar-Researcher Agent) is 100% complete** ✅

Please read these files in order:
1. `docs/CONTEXT.md` (project overview)
2. `docs/PROJECT_STATUS.md` (Phase 2 Day 6 complete, starting Phase 2b)
3. `docs/IMPLEMENTATION_LOG.md` (scroll to **2025-10-16 - Day 6: Phase 2 - Scholar-Researcher Agent**)

## Phase 2 Day 6 Delivered (100% Complete ✅)

### Scholar-Researcher Agent
- ✅ **Module**: `src/agents/scholar_researcher.py` (~550 LOC)
- ✅ **Model**: Claude 3.5 Haiku (`claude-3-5-haiku-20241022`)
- ✅ **Functionality**: Analyzes macro overview, generates comprehensive research requests
- ✅ **Output**: JSON with BDB requests, concordance searches, figurative checks
- ✅ **Key Feature**: Vehicle identification for figurative language (vehicle + synonyms)
- ✅ **Comprehensiveness**: 2-4 words per verse (Psalm 23: 17 requests, Psalm 27: 32 requests)
- ✅ **Cost**: ~$0.0003 per psalm request

### Test Results
- Psalm 23 (6 verses): 17 BDB, 3 concordance, 4 figurative ✅
- Psalm 27 (14 verses): 32 BDB, 3 concordance, 5 figurative ✅
- Full pipeline working: Macro Overview → Research Request → Research Bundle

## Phase 2b: Expanding Scholarly Resources (THIS SESSION)

**Objective**: Before implementing Scholar-Writer agents, expand the resources available to our scholars for richer analysis.

### Task 1: Septuagint (LXX) Integration ⏳

**Goal**: Auto-provide LXX text for all verses (no Scholar-Researcher request needed)

**Why**: Enables Vorlage analysis - understanding textual variants
- Example: Psalm 22:17
  - MT: "like a lion, my hands and feet" (כָּאֲרִי יָדַי וְרַגְלָי)
  - LXX: "they have pierced my hands and feet"
  - Suggests different Hebrew Vorlage (כָּרוּ)

**Implementation**:
1. Extend Sefaria API client to fetch LXX text
2. Add LXX field to verse data structure
3. Include LXX in research bundles automatically (no request needed)
4. Format for Scholar-Writer consumption

**Sefaria API Endpoint**: `/api/texts/Psalms.{chapter}:{verse}?context=0&lang=en`
- Returns both Hebrew and LXX (if available)

### Task 2: Commentary Librarian Agent ⏳

**Goal**: Fetch traditional Jewish commentaries on verses of interest

**Why**:
- Puts AI analysis in conversation with established interpretations
- Helps Critic agent identify if insights are novel or echo classical readings
- Provides scholarly context for unusual interpretations

**Commentaries to fetch** (via Sefaria):
- Rashi (11th century, France)
- Ibn Ezra (12th century, Spain)
- David Kimchi / Radak (12th-13th century, Provence)
- Metzudat David (18th century, Italy)

**Implementation**:
1. Create `src/agents/commentary_librarian.py`
2. Extend Scholar-Researcher to identify "perplexing" verses needing commentary
3. Fetch commentaries from Sefaria for those verses
4. Include in research bundle with attribution

**Sefaria API**:
- `/api/related/{ref}` returns commentary links
- `/api/texts/{commentary_ref}` returns commentary text

**Request Format** (from Scholar-Researcher):
```json
{
  "commentary_requests": [
    {"verse": 4, "reason": "Rare term 'beauty of the LORD' - check classical interpretations"}
  ]
}
```

### Task 3: RAG Documents for Scholar-Writer ⏳

**Goal**: Provide contextual knowledge to "heavy thinking" agents (Scholar-Writer, Critic)

**Documents** (already created in `/docs`):
1. **Analytical Framework** (`analytical_framework_for_RAG.md`)
   - Always provided to Scholar-Writer agents
   - Guides poetic analysis methodology

2. **Psalm Function/Type** (`psalm_function_for_RAG.md`)
   - Provided when available for the specific psalm
   - Example: "Psalm 23 = Trust Psalm (Vertrauenspsalm)"

3. **Ugaritic Comparisons** (`Ugaritic_comparisons_for_RAG.md`)
   - Provided when relevant comparisons exist
   - Example: Ugaritic "El" epithets parallel to Hebrew divine names

**Implementation Questions** (HELP NEEDED!):
1. **How to format these for RAG?**
   - Current: Markdown files
   - Need: Optimal structure for Claude prompt injection?
   - Options: Keep as markdown? Convert to JSON? Structured prompts?

2. **When to include each document?**
   - Analytical Framework: Always (system prompt?)
   - Psalm Function: When available in database
   - Ugaritic Comparisons: When relevant keywords detected (how to detect?)

3. **How to inject into Scholar-Writer prompts?**
   - Prepend to macro overview?
   - Separate context section?
   - Use Claude's extended thinking feature?

**Expected Workflow**:
```
Macro Overview
  +
Analytical Framework (always)
  +
Psalm Function (if available)
  +
Ugaritic Comparisons (if relevant)
  ↓
Scholar-Writer Agent (Sonnet 4)
```

## Model Name Correction ⚠️

**IMPORTANT**: Verify correct Claude Sonnet 4 model name for Scholar-Writer agents:
- Current assumption: `claude-sonnet-4-20250514`
- Need to confirm actual model ID with Anthropic API

Scholar-Writer will use Sonnet 4 for:
- Pass 1: Macro Analysis (chapter-level thesis)
- Pass 2: Micro Analysis (verse-by-verse commentary)
- Pass 3: Synthesis (final essay)

## File Locations

**RAG Documents** (need formatting help):
- `C:\Users\ariro\OneDrive\Documents\Psalms\docs\analytical_framework_for_RAG.md`
- `C:\Users\ariro\OneDrive\Documents\Psalms\docs\psalm_function_for_RAG.md`
- `C:\Users\ariro\OneDrive\Documents\Psalms\docs\Ugaritic_comparisons_for_RAG.md`

**Existing Code to Extend**:
- `src/data_sources/sefaria_client.py` - Add LXX fetch method
- `src/agents/` - Create commentary_librarian.py
- `src/agents/scholar_researcher.py` - Add commentary_requests field

## Success Criteria

By end of this session:
1. ✅ LXX text auto-provided for all verses
2. ✅ Commentary Librarian fetches Rashi, Ibn Ezra, Radak for requested verses
3. ✅ RAG documents properly formatted and injection strategy determined
4. ✅ Integration tested with Psalm 23 or 27
5. ✅ Documentation updated

## Questions for Discussion

1. **RAG Format**: How should we structure the RAG documents for optimal Claude prompt injection?
2. **Relevance Detection**: How to automatically detect when Ugaritic comparisons are relevant?
3. **Commentary Selection**: Should Scholar-Researcher request specific commentators, or always fetch all available?
4. **Token Budget**: With LXX + commentaries + RAG docs, are we within token limits?

## Ready to Begin

When ready, let's start with:
1. **Task 1** (LXX integration) - straightforward API extension
2. **Task 2** (Commentary Librarian) - new agent module
3. **Task 3** (RAG documents) - formatting and injection strategy

**Current Status**: Phase 2b ready to begin! 🚀

**Cost So Far**: ~$0.05 (Haiku requests for testing)
**Next Phase**: Scholar-Writer agents (Sonnet 4)
