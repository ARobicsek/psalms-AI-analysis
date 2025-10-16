# Next Session Prompt - Phase 2: Scholar-Researcher Agent

## Session Start Instructions

I'm continuing work on the Psalms AI commentary pipeline - Phase 2: Scholar Agents.

**Phase 1 (Foundation) is 100% complete** with all final refinements implemented, including today's BDB Librarian scholarly enhancement.

Please read these files in order:
1. `docs/CONTEXT.md` (project overview)
2. `docs/PROJECT_STATUS.md` (Phase 1 complete, starting Phase 2)
3. `docs/IMPLEMENTATION_LOG.md` (scroll to **2025-10-16 - Day 5 Final Session**)
4. `docs/ARCHITECTURE.md` (complete system architecture with updated BDB Librarian section)

## Phase 1 Delivered (100% Complete ✅)

### Foundation Components
- ✅ **Sefaria API Client**: Full Tanakh download, lexicon integration
- ✅ **Hebrew Concordance**: 269,844 words indexed, 4-layer search, phrase support
- ✅ **BDB Librarian**: Scholarly lexicons (BDB Dictionary + Klein) with etymology
- ✅ **Concordance Librarian**: 66 morphological variations, smart scoping
- ✅ **Figurative Language Librarian**: 2,863 instances, hierarchical tag queries
- ✅ **Research Bundle Assembler**: JSON + Markdown outputs

### Key Enhancements (Day 5 Final Session)
- ✅ **BDB Scholarly Upgrade**: 8.3x more data per word
  - Switched: "BDB Augmented Strong" (150 chars) → "BDB Dictionary" (1,247 chars)
  - Added Klein Dictionary with Ugaritic cognates, Egyptian borrowings
  - HTML stripping for clean definitions
  - Fields: morphology, etymology_notes, derivatives
- ✅ **Division of Labor**: Clean separation between librarians
  - BDB: Semantic ranges, etymology, morphology, parallel words
  - Concordance: Biblical citations, usage patterns, frequency
  - Figurative: Metaphor analysis, target/vehicle/ground

### Test Results
- Psalm 27:1 demo: 29 figurative instances, 14 concordance matches
- BDB test (אֶבְיוֹן): 3 scholarly entries with full depth
- All librarians operational, no hardcoded restrictions

## Phase 2: Scholar-Researcher Agent (Week 2)

### Primary Objective
Design and implement the **Scholar-Researcher Agent** that:
1. Receives a macro overview of a Psalm
2. Generates specific, targeted research requests
3. Coordinates with all three librarian agents
4. Returns a comprehensive research bundle

### Agent Specifications

**Model**: Claude Haiku 4.5 (cost-effective for pattern recognition)

**Input**: Macro overview from Pass 1 (chapter-level thesis + structure)

**Output**: JSON research request with three categories:
```json
{
  "bdb_requests": [
    {"word": "אֶבְיוֹן", "reason": "Key poverty term, appears 3x, central to social justice theme"}
  ],
  "concordance_searches": [
    {"query": "רעה", "level": "consonantal", "scope": "auto", "purpose": "Track shepherd imagery"}
  ],
  "figurative_checks": [
    {"verse": 1, "likely_type": "metaphor", "reason": "Divine protection as fortress/stronghold"}
  ]
}
```

### Implementation Tasks

1. **Prompt Design** (Critical!)
   - Guide Scholar to identify 5-8 significant Hebrew words
   - Explain WHY each word matters (not just "it appears")
   - Focus: unusual choices, loaded terms, ambiguous meanings, thematic keywords
   - Encourage smart scoping (auto-detect common vs. rare)

2. **Integration with Research Bundle Assembler**
   - Parse Scholar's JSON output
   - Route requests to appropriate librarians
   - Assemble comprehensive bundle (JSON + Markdown)

3. **Quality Validation**
   - Are requests specific and justified?
   - Does Scholar avoid vague/generic requests?
   - Do requests align with macro overview thesis?

4. **Testing Strategy**
   - Test with diverse Psalm types:
     - Lament (Psalm 13, 22)
     - Praise (Psalm 100, 150)
     - Wisdom (Psalm 1, 37)
     - Royal (Psalm 2, 72)
     - Trust (Psalm 23, 27)
   - Verify appropriate research depth for each genre

### Success Criteria

✅ Scholar generates 5-8 targeted BDB requests with clear justifications
✅ Concordance requests use smart scoping appropriately
✅ Figurative checks align with verse content
✅ Research bundle contains rich, relevant data
✅ No generic/vague requests (e.g., "research אל because it's God")
✅ End-to-end flow: Macro Overview → Research Request → Research Bundle

### Available Resources

**All librarians are operational and tested:**
- `python src/agents/bdb_librarian.py <word>` - Test BDB lookups
- `python src/agents/concordance_librarian.py <query> --scope <scope>` - Test searches
- `python src/agents/figurative_librarian.py --chapter <num>` - Test figurative queries
- `python src/agents/research_assembler.py <json_file>` - Test full assembly

**Example research requests** in `docs/LIBRARIAN_USAGE_EXAMPLES.md`

### Key Considerations

1. **Cost Optimization**: Haiku 4.5 is 5x cheaper than Sonnet for this task
2. **Specificity**: Scholar must justify WHY each word is significant
3. **Scope Intelligence**: Use `scope: "auto"` for smart frequency detection
4. **No Redundancy**: Don't request both BDB AND concordance for same word's usage

### Development Approach

**Suggested workflow:**
1. Design Scholar-Researcher prompt (see `docs/ARCHITECTURE.md` for template)
2. Create agent module: `src/agents/scholar_researcher.py`
3. Test with simple macro overview (Psalm 23)
4. Refine prompt based on output quality
5. Test with diverse Psalm types
6. Integrate with Research Bundle Assembler
7. Full pipeline test: Macro → Research → Bundle

### Architecture Notes

The Scholar-Researcher is a **coordination agent**:
- It doesn't do research itself
- It identifies WHAT needs researching and WHY
- Librarians do the actual data retrieval
- Research Assembler formats the results

This separation keeps costs low and responsibilities clear.

## Questions to Consider

Before coding:
1. How do we ensure Scholar requests are **specific** (not generic)?
2. What makes a "good" BDB request vs. a "bad" one?
3. How many words is "too many" vs. "too few"?
4. Should Scholar request phrases or individual words?
5. When should figurative checks be requested?

## Ready to Begin

When you're ready, let me know and we'll start designing the Scholar-Researcher agent!

Focus areas:
1. Prompt engineering (this is 80% of the work)
2. JSON schema design
3. Integration testing
4. Quality metrics

**Phase 1 Status**: 100% Complete ✅
**Phase 2 Goal**: Scholar-Researcher operational by end of Week 2
**Total Project Cost So Far**: $0.00 (all infrastructure, no LLM calls yet)

Let's build the Scholar! 🚀
