# Next Session Prompt - Psalms Commentary Project

**Date**: 2025-10-26
**Phase**: Phase 4 - Commentary Enhancement & Experimentation
**Progress**: 91% (25 sessions complete, production-ready pipeline + clean documentation + liturgical librarian planned)

---

## Current Status

The pipeline is **production-ready** with all core features implemented:
- ✅ 4-pass commentary generation (Macro → Micro → Synthesis → MasterEditor)
- ✅ Stress-aware phonetic transcription system
- ✅ Hierarchical figurative language search
- ✅ Hebrew concordance (4-layer system)
- ✅ Print-ready output (.md and .docx)
- ✅ Comprehensive documentation suite (DEVELOPER_GUIDE, GLOSSARY, OPERATIONAL_GUIDE, DOCUMENTATION_INDEX)
- ✅ **NEW**: Liturgical Librarian implementation plan complete

---

## Next Steps

### Immediate Priority: Liturgical Librarian Implementation

**RECOMMENDED START**: Phase 0 - Bootstrap from Sefaria (4-6 hours)

**What to build next session**:
1. **Create Sefaria links harvester** (~2 hours)
   - File: `src/liturgy/sefaria_links_harvester.py`
   - Harvest existing Psalms→Liturgy cross-references from Sefaria API
   - Store in `liturgy.db` table: `sefaria_liturgy_links`

2. **Run harvest for all 150 Psalms** (~10 minutes)
   - Automated API calls with rate limiting
   - Expected ~200-300 liturgical cross-references

3. **Build quick librarian** (~1.5 hours)
   - File: `src/agents/liturgical_librarian_sefaria.py`
   - Query interface for Sefaria's curated links
   - Research bundle formatting

4. **Test and integrate** (~30 minutes)
   - Validate with known Psalms (23, 145, etc.)
   - Add to existing research bundle in `scholar_researcher.py`

**Result**: Liturgical data working in commentary generation TODAY!

**Full Implementation Plan**: [LITURGICAL_LIBRARIAN_IMPLEMENTATION_PLAN.md](LITURGICAL_LIBRARIAN_IMPLEMENTATION_PLAN.md)

---

### Alternative Priorities

1. **Production Testing**
   - Run pipeline on Psalm 23 (benchmark test)
   - Verify stress marking in Word output
   - Validate cost estimates

2. **Phase 4 Refinements** (Optional)
   - Consider Master Editor length improvement strategies (Session 21 findings)
   - Explore commentary mode variations (scholarly, devotional, study Bible)

---

## Long-Term Goals

- **Liturgical Librarian**: Full phrase-level detection system (Phases 1-6 from implementation plan)
- Complete remaining 140+ psalms
- Generate consolidated PDF/print edition
- Refine figurative language integration (currently 1.2-1.8% utilization)

---

## Recent Sessions Summary

### Session 25 (2025-10-26): Liturgical Librarian Research & Planning

**Goal**: Research and plan a liturgical cross-reference system to identify where Psalms passages appear in Jewish prayer and ritual

**User Requirements**:
- Detect exact verse quotations, sub-verse phrases, and likely influences
- Determine WHERE in Jewish prayer/ritual (e.g., Shacharit, Tashlich, Selichot)
- Cover multiple traditions (Ashkenazi, Sephardic, Edot HaMizrach)
- Prefer comprehensive solution with sub-verse phrase detection

**Research Conducted**:
1. ✅ Analyzed existing pipeline architecture
2. ✅ Researched available corpora (Sefaria API, Open Siddur Project)
3. ✅ Evaluated Sefaria's `/api/related/` endpoint for Psalms→Liturgy cross-references
4. ✅ Analyzed phrase matching requirements (distinctiveness scoring, n-gram extraction)

**Implementation Options Designed**:
- **Option 1**: Lightweight Sefaria Cross-Reference Librarian (1-2 days, verse-level only)
- **Option 2**: Enhanced with Phrase Detection (1-2 weeks, sub-verse capability)
- **Option 3**: Comprehensive Annotated Liturgical Corpus (3-4 weeks, full system) ← **CHOSEN**
- **Option 4**: Hybrid with ML Enhancement (4-6 weeks, semantic similarity)

**Decision**: Option 3 (Comprehensive) with **Phase 0 bootstrap** for immediate value

**Deliverable Created**:
- **LITURGICAL_LIBRARIAN_IMPLEMENTATION_PLAN.md** (2,490+ lines)
  - Complete technical architecture
  - Database schemas (prayers, psalms_liturgy_index, liturgical_metadata, harvest_log)
  - Phase 0: Bootstrap from Sefaria (4-6 hours) ⚡ QUICK WIN
  - Phase 1: Database design
  - Phase 2: Corpus harvesting from Sefaria
  - Phase 3: Phrase extraction with TF-IDF distinctiveness scoring
  - Phase 4: Indexing algorithm with 4-layer normalization
  - Phase 5: Librarian implementation & integration
  - Phase 6: Testing & refinement
  - Complete code examples for all phases
  - Incremental build strategy (can process Psalms one at a time)

**Key Innovation - Phase 0**:
- Harvest Sefaria's existing curated cross-references FIRST
- Get 70-80% of value in 4-6 hours
- Use as validation dataset for custom phrase-level index
- No wasted work - feeds into comprehensive system

**Technical Highlights**:
- Leverages existing 4-layer Hebrew normalization system
- TF-IDF-based phrase distinctiveness scoring
- Smart n-gram filtering (2-word: score > 0.75, 3-word: > 0.5, 4+: > 0.3)
- Confidence scoring based on match type and normalization level
- Multiple nusachim support (Ashkenaz, Sefard, Edot HaMizrach)

**Integration Point**:
- New `LiturgicalLibrarian` agent (similar to existing librarians)
- Adds "Liturgical Usage" section to research bundles
- Minimal changes to `scholar_researcher.py`

**Files Modified**:
- docs/LITURGICAL_LIBRARIAN_IMPLEMENTATION_PLAN.md (new, 2,490+ lines)
- docs/NEXT_SESSION_PROMPT.md (this file)
- docs/PROJECT_STATUS.md (progress update)
- docs/IMPLEMENTATION_LOG.md (session history)

**Time**: ~2 hours (research, analysis, planning, documentation)

**Next Session**: Implement Phase 0 (Sefaria bootstrap) - get immediate value!

---

### Session 24 (2025-10-25): Documentation Cleanup Phase 2

**Goal**: Consolidate operational guides (BATCH_API, RATE_LIMITING, TESTING)

**Approach**: Direct consolidation - merge all three guides into single comprehensive document

**Tasks Completed**:
1. ✅ **Created OPERATIONAL_GUIDE.md** (742 lines)
   - Section 1: Testing & Output Conventions (~166 lines)
   - Section 2: Rate Limiting & API Usage (~311 lines)
   - Section 3: Batch API for Production (~352 lines)

2. ✅ **Archived Original Files** (3 files to docs/archive/deprecated/)

3. ✅ **Updated DOCUMENTATION_INDEX.md**
   - Operational Guides section: 3 separate files → 1 consolidated file
   - Statistics updated (docs: 17→15 core files, archived: 20+→23+)

**Impact**: Single entry point for all operational concerns, easier maintenance

**Time**: ~30 minutes

---

### Session 23 (2025-10-24): Documentation Cleanup Phase 1

**Goal**: Aggressively clean up and archive session-specific and completed documentation files

**Tasks Completed**:
1. ✅ **Root Directory Audit** (67% reduction: 6→2 files)
2. ✅ **Docs Directory Audit** (37% reduction: 27→17 files)
3. ✅ **Cross-Reference Analysis** (fixed 2 broken references)
4. ✅ **Executed File Moves** (15 files archived to organized categories)
5. ✅ **Created DOCUMENTATION_INDEX.md** (comprehensive navigation)

**Impact**: Cleaner navigation, better onboarding, zero information loss

**Time**: ~45 minutes

---

## Key Implementation Notes

### Liturgical Librarian Architecture (Session 25)
- **Phase 0**: Bootstrap from Sefaria's existing cross-references (immediate value)
- **Database**: `liturgy.db` with 4 tables (prayers, index, metadata, harvest_log)
- **Search Strategy**: 4-layer normalization + phrase distinctiveness scoring
- **Coverage**: Multiple nusachim (Ashkenaz, Sefard, Edot HaMizrach)
- **Integration**: New librarian agent → research bundle → AI agents

### Phonetic Transcription System (Sessions 18-19)
- **Session 18**: Implemented stress-aware transcription based on cantillation marks
- **Session 19**: Fixed maqqef stress domain handling
- **Current**: Fully integrated with **BOLD CAPS** notation throughout pipeline

### Data Flow Architecture
```
PhoneticAnalyst → stressed transcription
  ↓
MicroAnalystV2 → extracts and stores
  ↓
SynthesisWriter / MasterEditor → receives in prompt
  ↓
DocumentGenerator → renders as bold italic
  ↓
Final Word Document → ***bold italic*** for stressed syllables
```

---

## Key Documentation

**Getting Started**:
- [QUICK_START.md](../QUICK_START.md) - 2-minute setup guide
- [CONTEXT.md](CONTEXT.md) - Project overview
- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) - Complete navigation

**Technical Reference**:
- [TECHNICAL_ARCHITECTURE_SUMMARY.md](TECHNICAL_ARCHITECTURE_SUMMARY.md) - System architecture
- [PHONETIC_SYSTEM.md](PHONETIC_SYSTEM.md) - Phonetic transcription reference
- [LITURGICAL_LIBRARIAN_IMPLEMENTATION_PLAN.md](LITURGICAL_LIBRARIAN_IMPLEMENTATION_PLAN.md) - Liturgical system design ✨ NEW

**Development**:
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Code navigation and agent development
- [GLOSSARY.md](GLOSSARY.md) - Project terminology reference
- [OPERATIONAL_GUIDE.md](OPERATIONAL_GUIDE.md) - Testing, rate limiting, batch API
- [SESSION_MANAGEMENT.md](SESSION_MANAGEMENT.md) - Workflow protocols
- [IMPLEMENTATION_LOG.md](IMPLEMENTATION_LOG.md) - Complete development history (Sessions 1-25)
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Current progress tracking

---

## Historical Context

For complete development history, see:
- **[IMPLEMENTATION_LOG.md](IMPLEMENTATION_LOG.md)** - All 25 sessions documented
- **[docs/archive/sessions/](archive/sessions/)** - Individual session summaries archived

**Key Milestones**:
- **Phase 1** (Sessions 1-6): Core pipeline development
- **Phase 2** (Sessions 7-12): Hebrew concordance and research bundle
- **Phase 3** (Sessions 13-17): Figurative language integration
- **Phase 4** (Sessions 18-25): Phonetic transcription, stress marking, documentation consolidation, liturgical planning

---

*This document is intentionally brief. See IMPLEMENTATION_LOG.md for comprehensive session details.*
