# Phase 3: Five-Pass Scholar-Writer Architecture

## Overview

The Phase 3 pipeline produces comprehensive psalm commentary through five sequential passes, each building on the previous work. All agents use **Claude Sonnet 4.5** with extended thinking (except Pass 4 Critic, which will test Haiku 4.5 vs Sonnet 4.5).

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│ AUTO-AVAILABLE TO ALL AGENTS                                │
│ • Psalm text (Hebrew + English)                             │
│ • LXX translation (Greek Septuagint)                        │
│ • RAG context (genre, structure, Ugaritic, framework)       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PASS 1: MacroAnalyst (Sonnet 4.5 + extended thinking) ✅    │
│ • Generates high-level thesis                               │
│ • Identifies structural divisions                           │
│ • Names key poetic devices                                  │
│ • Produces 5 research questions                             │
│                                                              │
│ OUTPUT: MacroAnalysis object                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PASS 2: MicroAnalyst v2 (Sonnet 4.5 + extended thinking) ✅ │
│                                                              │
│ INPUT: MacroAnalysis + RAG context + Psalm text + LXX       │
│                                                              │
│ PHILOSOPHY: CURIOSITY-DRIVEN (not thesis-confirming)        │
│                                                              │
│ STAGE 1: Quick Discovery Pass                               │
│   - Read each verse with fresh eyes                         │
│   - Notice patterns, surprises, puzzles, curious words      │
│   - Identify figurative language and poetic devices         │
│   - Keep macro thesis in peripheral vision only             │
│                                                              │
│ STAGE 2: Generate Research Requests                         │
│   - Based on discoveries (not thesis support)               │
│   - BDB lexicon (20-40 curious words)                       │
│   - Concordance searches (5-10 patterns)                    │
│   - Figurative language (all metaphorical verses)           │
│   - Traditional commentary (3-6 puzzling verses)            │
│                                                              │
│ STAGE 3: Call Research Assembler                            │
│   - Librarians fetch comprehensive research data            │
│                                                              │
│ OUTPUT: MicroAnalysis (discoveries) + Research Bundle       │
│                                                              │
│ NOTE: MicroAnalyst does NOT do heavy analysis - it          │
│ discovers and requests. SynthesisWriter analyzes.           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PASS 3: SynthesisWriter (Sonnet 4.5)                       │
│                                                              │
│ INPUT: MacroAnalysis + MicroAnalysis + Research Bundle      │
│                                                              │
│ PROCESS:                                                     │
│ 1. Write Introduction Essay (800-1200 words)                │
│    • Genre, historical context, themes                      │
│    • Present macro thesis                                   │
│    • Discuss structure and poetic devices                   │
│ 2. Write Verse-by-Verse Commentary (detailed)               │
│    • Each verse thoroughly treated                          │
│    • Integrate lexical/figurative/traditional research      │
│    • Show how verse supports thesis                         │
│    • Smooth, readable prose with citations                  │
│                                                              │
│ OUTPUT: SynthesisOutput object (intro + commentary)         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PASS 4: Critic (Haiku 4.5 OR Sonnet 4.5 - TO TEST)         │
│                                                              │
│ INPUT: All prior work + research bundle                     │
│                                                              │
│ CHECKS:                                                      │
│ • Factual accuracy (cross-ref sources)                      │
│ • Logical coherence (thesis → evidence → conclusion)        │
│ • Clichés or unsupported claims                             │
│ • Integration quality (smooth blending)                     │
│ • Telescopic integration (macro ↔ micro)                    │
│ • Prose quality (clear, engaging, accessible)               │
│                                                              │
│ OUTPUT: CriticFeedback object (score + suggestions)         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PASS 5: FinalPolisher (Sonnet 4.5)                         │
│                                                              │
│ INPUT: SynthesisOutput + CriticFeedback + full context      │
│                                                              │
│ PROCESS:                                                     │
│ • Address all critic feedback                               │
│ • Refine prose and flow                                     │
│ • Ensure proper citations                                   │
│ • Final quality check                                       │
│                                                              │
│ OUTPUT: Final polished commentary (ready for publication)   │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow: What Each Pass Receives

### Pass 1: MacroAnalyst
**Auto-Available:**
- Psalm text (Hebrew + English)
- LXX translation
- RAG context (genre, structure, Ugaritic parallels, analytical framework)

**Generates:**
- MacroAnalysis object

### Pass 2: MicroAnalyst
**Inherits:**
- Everything from Pass 1 (auto-available data)
- MacroAnalysis object from Pass 1

**Generates:**
- Research requests (JSON)
- MicroAnalysis object
- Research Bundle (assembled by librarians)

### Pass 3: SynthesisWriter
**Inherits:**
- Everything from Pass 1 (auto-available data)
- MacroAnalysis object from Pass 1
- MicroAnalysis object from Pass 2
- Research Bundle from Pass 2

**Generates:**
- SynthesisOutput object (intro essay + verse-by-verse commentary)

### Pass 4: Critic
**Inherits:**
- Everything from all prior passes

**Generates:**
- CriticFeedback object

### Pass 5: FinalPolisher
**Inherits:**
- Everything from all prior passes
- CriticFeedback from Pass 4

**Generates:**
- Final commentary (markdown + JSON)

## Key Design Decisions

### 1. LXX Integration
**Decision:** All agents receive LXX (Greek Septuagint) translation.

**Rationale:**
- LXX provides ancient interpretive tradition
- Greek word choices reveal how early translators understood Hebrew
- Can illuminate ambiguous passages
- Adds scholarly depth

**Implementation:** Add LXX to RAG Manager alongside Hebrew/English

### 2. MicroAnalyst Generates Research Requests
**Decision:** MicroAnalyst internally generates research requests and calls Research Assembler.

**Rationale:**
- Deep thinker (Sonnet 4.5) makes better, more sophisticated requests
- Has full context of macro thesis and research questions
- Eliminates separate Scholar-Researcher step
- More targeted and justified requests

**Implementation:** MicroAnalyst embeds Scholar-Researcher logic

### 3. Synthesis = Introduction + Commentary
**Decision:** Pass 3 produces BOTH an introductory essay AND verse-by-verse commentary.

**Rationale:**
- Reader needs orientation before diving into verses
- Introduction presents macro thesis and sets expectations
- Verse-by-verse provides detailed exegetical treatment
- This matches scholarly commentary format

**Implementation:** SynthesisOutput object has two sections

### 4. Critic is Separate Pass
**Decision:** Critic is Pass 4, not integrated into Synthesis.

**Rationale:**
- Fresh eyes review improves quality
- Can catch errors, clichés, unsupported claims
- Provides objective assessment
- Tests Haiku 4.5 vs Sonnet 4.5 cost/quality tradeoff

**Implementation:** Critic receives everything, produces structured feedback

### 5. All Sonnet 4.5 (with Haiku test)
**Decision:** Use Sonnet 4.5 for all passes except testing Haiku for Critic.

**Rationale:**
- Consistent quality across pipeline
- Extended thinking produces deeper insights
- Better research request generation
- More sophisticated synthesis
- Test Haiku for cost savings in review role

**Implementation:** Model parameter set to `claude-sonnet-4-20250514`

## Research Assembler Integration

The MicroAnalyst calls the **Research Assembler**, which coordinates:

1. **BDB Librarian** (Sefaria API)
   - Fetches Hebrew lexicon entries
   - Returns definitions, etymology, usage

2. **Concordance Librarian** (local 4-layer concordance)
   - Searches consonantal/voweled/exact/lemma
   - Returns verse references and contexts

3. **Figurative Librarian** (existing SQLite database)
   - Queries 2,863 figurative instances in Psalms
   - Returns metaphor/simile/personification data

4. **Commentary Librarian** (LXX + 6 traditional commentators)
   - Fetches relevant commentary excerpts
   - Returns traditional interpretations

**Output:** Research Bundle (JSON) with all assembled data

## File Structure

```
src/agents/
├── macro_analyst.py         # Pass 1 ✅ COMPLETE (430 LOC)
├── micro_analyst.py         # Pass 2 (600 LOC) - TO BUILD
├── synthesis_writer.py      # Pass 3 (500 LOC) - TO BUILD
├── critic.py                # Pass 4 (300 LOC) - TO BUILD
├── final_polisher.py        # Pass 5 (250 LOC) - TO BUILD
├── rag_manager.py           # RAG documents ✅ (needs LXX addition)
├── research_assembler.py    # Coordinates librarians ✅
├── scholar_researcher.py    # Logic reused in micro_analyst ✅
└── [4 librarians]           # Already built ✅

src/schemas/
└── analysis_schemas.py      # All dataclasses ✅ COMPLETE

tests/
├── test_macro_analyst.py    # Pass 1 tests ✅
├── test_micro_analyst.py    # Pass 2 tests - TO BUILD
├── test_synthesis_writer.py # Pass 3 tests - TO BUILD
├── test_critic.py           # Pass 4 tests - TO BUILD
└── test_final_polisher.py   # Pass 5 tests - TO BUILD
```

## Cost Estimates

### Per Psalm (average 16.8 verses)

**Pass 1: MacroAnalyst**
- Input: ~15K tokens (psalm + RAG + framework)
- Output: ~2K tokens
- Thinking: ~5K tokens
- Cost: ~$0.08

**Pass 2: MicroAnalyst**
- Input: ~30K tokens (psalm + macro + research bundle)
- Output: ~8K tokens (requests + analysis)
- Thinking: ~10K tokens
- Cost: ~$0.15

**Pass 3: SynthesisWriter**
- Input: ~50K tokens (all prior work + bundle)
- Output: ~5K tokens (intro + commentary)
- Cost: ~$0.15

**Pass 4: Critic**
- Haiku: ~$0.02
- Sonnet: ~$0.08
- **Will test both**

**Pass 5: FinalPolisher**
- Input: ~60K tokens
- Output: ~5K tokens
- Cost: ~$0.15

**Total per psalm: ~$0.60-0.65**
**150 psalms: ~$90-100**

With prompt caching: **~$60-70 total**

## Testing Strategy

### Haiku vs Sonnet for Critic (Pass 4)

**Test Plan:**
1. Run Psalm 29 with Haiku Critic
2. Run Psalm 29 with Sonnet Critic
3. Compare:
   - Quality of feedback
   - Specificity of suggestions
   - Accuracy of error detection
   - Cost differential
4. Make decision for production runs

**Decision Criteria:**
- If Haiku catches 80%+ of issues: use Haiku (saves ~$9 total)
- If Sonnet significantly better: use Sonnet (worth the cost)

## Next Implementation Steps

1. ✅ **Phase 3a Complete**: MacroAnalyst built and tested
2. **Phase 3b**: Add LXX to RAG Manager
3. **Phase 3c**: Build MicroAnalyst with research request generation
4. **Phase 3d**: Build SynthesisWriter (intro + commentary)
5. **Phase 3e**: Build Critic (test Haiku vs Sonnet)
6. **Phase 3f**: Build FinalPolisher
7. **Phase 3g**: Integration testing with full pipeline
8. **Phase 3h**: Run Psalm 29 end-to-end
9. **Phase 3i**: Production deployment for all 150 psalms

## Quality Metrics

Commentary must demonstrate:
- ✅ **Telescopic thinking**: Connects micro details to macro thesis
- ✅ **Specific thesis**: Not generic ("this psalm is about trust")
- ✅ **Textual support**: Claims backed by evidence
- ✅ **Poetic awareness**: Analyzes parallelism, word choice, structure
- ✅ **Novelty**: Goes beyond surface/cliché readings
- ✅ **Coherence**: Shows how verses build the argument
- ✅ **Accessibility**: Scholarly but readable for educated lay audience
- ✅ **Citations**: Properly attributes BDB, commentators, research

---

**Status**: Phase 3b (Pass 2) ✅ COMPLETE
**Completed**: MacroAnalyst ✅ | MicroAnalyst v2 ✅ | LXX Integration ✅
**Next**: Phase 3c (Build SynthesisWriter - Pass 3)
**Target Completion**: 4-6 more sessions for full Phase 3
