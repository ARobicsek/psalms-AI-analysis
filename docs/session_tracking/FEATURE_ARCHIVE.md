# Feature Archive

Stable, completed features. Moved from PROJECT_STATUS.md on 2026-03-18 to reduce session startup token cost. These features are all active and working — this file is for reference only.

---

## Core Features

### Master Editor V2 (Session 215)
Completely restructured prompt that is now the default. Key improvements:
- Ground Rules section with unmissable Hebrew+English requirement
- Explicit Deep Research guidance for cultural afterlife and reception history
- "Aha! Moment" focus creating insights that couldn't exist before LLMs
- ~40% reduction in repeated instructions

Usage: `python scripts/run_enhanced_pipeline.py 126` (default)
Old prompt: `python scripts/run_enhanced_pipeline.py 126 --master-editor-old`

### Gemini 2.5 Pro Fallback (Session 211)
Automatic switching to Gemini for large psalms when research bundle exceeds limits:
- Trimming priority: Related Psalms > Figurative Language > switch to Gemini
- Gemini processes with 1M token context (vs Claude's 200K)
- GPT-5.1 Master Editor remains unchanged
- Cost tracking integrated

### Strategic Verse Grouping (Session 212)
Prevents truncation in long psalms through intelligent grouping:
- 2-4 thematically related verses can be grouped
- Pacing guidance ensures equal treatment
- No "remaining verses" truncation notes

### Figurative Curator (Sessions 224-227)
LLM-enhanced agent that transforms raw figurative concordance data into curated insights using GPT-5.4:
- Fully integrated into research assembler (Session 226)
- Executes searches against figurative language database (50 results/search initial, 30 follow-up)
- Iteratively refines searches (up to 3 iterations) based on gap analysis
- Curates 5-15 examples per vehicle with Hebrew text
- Synthesizes 4-5 prose insights (100-150 words each) for commentary writers
- Adapts structure_type to psalm pattern (journey, descent_ascent, contrast, etc.)
- Cost: ~$0.30-0.50 per psalm

Test script: `python scripts/test_figurative_curator.py --psalm 22`
Integration guide: `docs/guides/FIGURATIVE_CURATOR_INTEGRATION.md`

## Research Integration

### Deep Web Research (Session 209)
Support for manually prepared Gemini Deep Research outputs:
- Store in `data/deep_research/psalm_NNN_deep_research.txt`
- Auto-loads into research bundle
- Included after Concordance in priority

### Phrase Search Optimization (Sessions 180, 182)
- Fixed word order differences (Session 180)
- Fixed maqqef concatenation bug (Session 180)
- Fixed conceptual vs exact form extraction (Session 182)

## Interactive Tools

### Converse with Editor (Session 221)
Multi-turn conversation with the Master Editor (GPT-5.1) about a completed psalm commentary:
- Load commentary, research bundle sections, and analysis files
- Interactive context selection with character counts
- Streaming API responses for real-time feedback
- Cost tracking with $1 threshold warnings
- Transcript saving to markdown files

Usage:
```bash
python scripts/converse_with_editor.py 21
python scripts/converse_with_editor.py 21 --edition college
```

## Pipeline Features

### Special Instruction Pipeline (Session 220)
Author-directed commentary revisions without altering standard pipeline:
- Extends `MasterEditorV2` via inheritance (`MasterEditorSI` class)
- Special instruction prompts with "SPECIAL AUTHOR DIRECTIVE" section
- All outputs use `_SI` suffix (never overwrites originals)
- Generates three .docx documents: Main SI, College SI, Combined SI

Usage:
```bash
echo "Focus on theme of divine refuge..." > data/special_instructions/special_instructions_Psalm_019.txt
python scripts/run_si_pipeline.py 19
```

### Skip Logic & Resume (Session 219)
- `--resume` flag for automatic step detection
- `--skip-*` to skip regeneration but use existing file
- `--exclude-*` to skip regeneration AND omit existing file from writer/doc

### Research Bundle Trimming (Session 211)
Progressive trimming strategy:
1. Trim Related Psalms (remove full texts)
2. Remove Related Psalms entirely
3. Trim Figurative Language to 75%
4. Trim Figurative Language to 50%
5. Switch to Gemini 2.5 Pro

Never trimmed: Lexicon, Commentaries, Liturgical, Sacks, Scholarly Context, Concordance, Deep Web Research

## Document Generation

### Main DOCX Verse Commentary (Session 213)
- Updated regex to handle `**Verses X-Y**` format with en dashes
- Added support for verse ranges
- Both main and combined DOCX now complete

### Pipeline Stats Tracking (Session 214)
- Fixed lexicon count regex
- Added verse count tracking from database
- Stats JSON always complete
