# Psalms Project — Stable Reference

This file is a stable reference for the project's current architecture and capabilities. It is NOT read at startup — see `CLAUDE.md` for session context.

**Last Updated**: 2026-03-18

---

## Pipeline Phases

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1: Text Extraction | Complete | All Tanakh text extracted and stored in SQLite |
| Phase 2: Macro Analysis | Complete | All psalms analyzed for themes and structure |
| Phase 3: Micro Analysis | Complete | Verse-by-verse phrase extraction complete |
| Phase 3b: Question Curation | Complete | LLM-curated reader questions from analysis |
| Phase 3c: Insight Extraction | Complete | Curates high-value insights from research bundle (Step 2c) |
| Phase 4: Research Assembly | Complete | Optimizing figurative language search and trimming |
| Phase 5: Synthesis Generation | Complete | Commentary generation with Gemini fallback |
| Phase 6: Editing and Publication | Complete | Unified Writer V4, DOCX generation (RTL/Arabic supported) |

## Active Features

- **Unified Writer V4**: Single prompt merging Main + College editions; halves pipeline cost
- **Insight Extractor**: Dedicated agent (gpt-5.4) to curate "aha!" moments from research
- **Research Trimmer**: Intelligent context window management
- **Gemini 2.5 Pro Fallback**: Handles large psalms (51+ verses) without content loss
- **Deep Web Research Integration**: Supports Gemini Deep Research outputs
- **Strategic Verse Grouping**: Prevents truncation in long psalms
- **Pipeline Skip/Exclude Logic**: `--resume`, `--skip-*`, `--exclude-*`
- **Figurative Curator**: GPT-5.4 transforms raw figurative data into curated insights
- **Questions for the Reader**: LLM-curated questions appear before Introduction
- **Copy Editor**: 9-category error taxonomy with critical reading stance (gpt-5.4)
- **Scripture Citation Verifier**: Regex-based with GPT-5.1 false-positive filter (default)
- **Adaptive Thinking**: All Opus agents use adaptive thinking
- **Complex Script Font Support**: Arabic/CJK/Hebrew DOCX rendering with LRM BiDi fix

## Known Limitations

- Large psalms may require Gemini fallback (additional cost)
- Deep research must be manually prepared via Gemini browser interface
- Figurative Curator adds ~$0.30-0.50 per psalm
- Insight Extractor adds ~$0.50-1.00 per psalm

## Database Status

- **tanakh.db**: ~50MB, all 39 books of Tanakh, 23,145 verses, full-text indexed
- **psalm_relationships.db**: V6 skipgram patterns (130MB, 335,720 quality-filtered patterns)

## Key Documentation

- `CLAUDE.md` — Session startup context (auto-loaded by Claude Code)
- `docs/session_tracking/scriptReferences.md` — All scripts with descriptions
- `docs/session_tracking/IMPLEMENTATION_LOG.md` — Detailed session history (300+)
- `docs/session_tracking/FEATURE_ARCHIVE.md` — Detailed docs for completed features
- `docs/session_tracking/SESSION_PROMPTS.md` — Session start/end templates
- `docs/architecture/TECHNICAL_ARCHITECTURE_SUMMARY.md` — Full system architecture
- `docs/guides/DEVELOPER_GUIDE.md` — Coding standards, workflow

## Session History Archives

- Sessions 1-149: `docs/archive/documentation_cleanup/IMPLEMENTATION_LOG_sessions_1-149_2025-12-04.md`
- Sessions 150-199: `docs/archive/documentation_cleanup/IMPLEMENTATION_LOG_sessions_150-199_2026-01-12.md`
- Sessions 241-299: `docs/archive/documentation_cleanup/IMPLEMENTATION_LOG_sessions_241-299_2026-03-18.md`
- Sessions 300+: `docs/session_tracking/IMPLEMENTATION_LOG.md`
