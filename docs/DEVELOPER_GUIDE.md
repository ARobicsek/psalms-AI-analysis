# Developer Guide: Psalms Commentary Pipeline

This guide helps developers navigate the codebase, understand the architecture, and contribute effectively to the Psalms commentary generation pipeline.

## Table of Contents

1. [Overview](#overview)
2. [Code Organization](#code-organization)
3. [Agent Architecture](#agent-architecture)
4. [Librarian vs AI Agents](#librarian-vs-ai-agents)
5. [Data Flow](#data-flow)
6. [Adding a New Agent](#adding-a-new-agent)
7. [Testing Procedures](#testing-procedures)
8. [Common Patterns](#common-patterns)

---

## Overview

This project generates scholarly biblical commentary on the Book of Psalms using a multi-agent AI pipeline. The pipeline combines:

- **AI Agents** (Claude Sonnet 4.5, GPT-5) for analysis and writing
- **Librarian Agents** (Python scripts) for data retrieval
- **Research Databases** (Sefaria API, local concordances, figurative language database)
- **RAG Documents** (genre analysis, Ugaritic parallels, analytical framework)

The result is National Book Award-level commentary suitable for sophisticated lay readers.

---

## Code Organization

### Directory Structure

```
src/
├── agents/              # All agent implementations (AI + Librarians)
├── concordance/         # Concordance search engine
├── data_sources/        # External data APIs (Sefaria, Tanakh DB)
├── schemas/             # Data structures and validation
├── utils/               # Helper functions and formatters
└── output/              # Generated files (not in repo)

docs/                    # RAG documents and documentation
├── rag/                 # Retrieval-augmented generation data
│   ├── psalm_function/  # Genre and structural analysis
│   └── ugaritic/        # Ancient Near Eastern parallels
└── analytical_framework.md  # Poetic analysis methodology

tests/                   # Unit and integration tests
database/                # SQLite database files
data/                    # Raw data files
```

### Key Source Files

#### Core Pipeline Agents
- `src/agents/macro_analyst.py` - Pass 1: Chapter-level thesis (Claude Sonnet 4.5)
- `src/agents/micro_analyst.py` - Pass 2: Verse-by-verse discovery (Claude Sonnet 4.5)
- `src/agents/synthesis_writer.py` - Pass 3: Commentary synthesis (Claude Sonnet 4.5)
- `src/agents/master_editor.py` - Pass 4: Editorial review (GPT-5)

#### Librarian Agents (Data Retrieval)
- `src/agents/bdb_librarian.py` - Hebrew lexicon entries (BDB, Klein)
- `src/agents/concordance_librarian.py` - Word/phrase concordance searches
- `src/agents/figurative_librarian.py` - Figurative language database queries
- `src/agents/commentary_librarian.py` - Traditional Jewish commentaries
- `src/agents/liturgical_librarian_sefaria.py` - Sefaria liturgical cross-references (Phase 0)
- `src/agents/liturgical_librarian.py` - Comprehensive liturgical usage (Phase 4/5)

#### Supporting Infrastructure
- `src/agents/research_assembler.py` - Coordinates all librarians
- `src/agents/rag_manager.py` - Manages RAG documents
- `src/agents/phonetic_analyst.py` - Phonetic transcription with stress marking
- `src/data_sources/tanakh_database.py` - Hebrew Bible text access
- `src/data_sources/sefaria_client.py` - Sefaria API wrapper
- `src/schemas/analysis_schemas.py` - Data structure definitions

---

## Agent Architecture

### The Five-Pass Pipeline

```
Pass 1: Macro Analyst (Claude Sonnet 4.5)
  Input:  Psalm text + RAG context
  Output: MacroAnalysis (thesis, structure, poetic devices)

Pass 2: Micro Analyst (Claude Sonnet 4.5)
  Input:  MacroAnalysis + Psalm text + Phonetic data
  Output: MicroAnalysis (verse discoveries) + ResearchRequest

Pass 2.5: Research Assembler (Python)
  Input:  ResearchRequest
  Output: ResearchBundle (lexicon, concordances, figurative, commentary)

Pass 3: Synthesis Writer (Claude Sonnet 4.5)
  Input:  MacroAnalysis + MicroAnalysis + ResearchBundle
  Output: Introduction essay + Verse commentary

Pass 4: Master Editor (GPT-5)
  Input:  All materials + drafts
  Output: Polished final commentary
```

### AI Agent Pattern

All AI agents follow a consistent pattern:

```python
class AgentName:
    def __init__(self, api_key=None, logger=None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        self.logger = logger or get_logger("agent_name")

    def analyze_psalm(self, psalm_number: int, **kwargs) -> AnalysisObject:
        # 1. Fetch inputs (psalm text, prior analyses)
        # 2. Build prompt from template
        # 3. Call LLM API
        # 4. Parse JSON/text response
        # 5. Return structured data object
        pass

    def analyze_and_save(self, psalm_number: int, output_dir: str):
        # Convenience method for CLI usage
        pass
```

**Example: MacroAnalyst**

```python
from src.agents.macro_analyst import MacroAnalyst

# Initialize
analyst = MacroAnalyst(api_key="your-key")

# Analyze
analysis = analyst.analyze_psalm(psalm_number=23)

# Access results
print(analysis.thesis_statement)
print(analysis.structural_outline)
print(analysis.poetic_devices)

# Save to files
analyst.analyze_and_save(23, output_dir="output", save_format="both")
```

### Librarian Agent Pattern

Librarians are pure Python - no LLM calls:

```python
class LibrarianName:
    def __init__(self):
        self.client = ExternalAPIClient()

    def fetch_entry(self, query: str) -> List[DataObject]:
        # Query external API or database
        # Return structured data objects
        pass

    def fetch_multiple(self, requests: List[Request]) -> Bundle:
        # Batch processing
        pass
```

**Example: BDBLibrarian**

```python
from src.agents.bdb_librarian import BDBLibrarian, LexiconRequest

# Initialize
librarian = BDBLibrarian()

# Single lookup
entries = librarian.fetch_entry("רעה")
for entry in entries:
    print(entry.entry_text)

# Multiple lookups
requests = [
    LexiconRequest("רעה", notes="shepherd verb"),
    LexiconRequest("צדק", notes="righteousness")
]
bundle = librarian.fetch_multiple(requests)
```

---

## Librarian vs AI Agents

### Librarian Agents (Python Data Retrievers)

**Purpose**: Fetch raw reference materials from databases and APIs

**Characteristics**:
- Pure Python code, no LLM calls
- Fast and deterministic
- Return structured data objects
- No analysis or interpretation

**Examples**:
- `BDBLibrarian` - Fetches Hebrew lexicon entries from Sefaria
- `ConcordanceLibrarian` - Searches local concordance database
- `FigurativeLibrarian` - Queries figurative language database
- `CommentaryLibrarian` - Retrieves traditional commentaries via Sefaria
- `SefariaLiturgicalLibrarian` (Phase 0) - Quick verse-level liturgical cross-references from Sefaria
- `LiturgicalLibrarian` (Phase 4/5) - Comprehensive phrase-level liturgical usage with optional LLM summaries

**Liturgical Librarian Details**:

**SefariaLiturgicalLibrarian** (Phase 0 Bootstrap):
- Purpose: Quick verse-level liturgical cross-references from Sefaria's curated data
- Coverage: ~74 Psalms with explicit liturgical connections
- No LLM required (pure data retrieval)
- Used for bootstrapping and quick reference

**LiturgicalLibrarian** (Phase 4/5 Comprehensive):
- Purpose: Phrase-level detection of Psalm passages in Jewish liturgy
- Database: `liturgy.db` with indexed prayers and phrase matches
- LLM Integration: Optional Claude Haiku 4.5 for intelligent summarization
- Aggregation: Groups matches by prayer name to prevent duplication
- Quality Assurance: Automatic validation and retry logic
- Output: Narrative summaries of liturgical contexts included in research bundle

**Think of them as**: Research assistants who fetch books from the library shelves

### AI Agents (Claude/GPT-5)

**Purpose**: Analyze, synthesize, and write commentary

**Characteristics**:
- Use large language models (Claude Sonnet 4.5, GPT-5)
- Perform deep analysis and synthesis
- Generate natural language output
- Make scholarly judgments

**Examples**:
- `MacroAnalyst` - Produces chapter-level thesis
- `MicroAnalyst` - Performs verse-by-verse discovery
- `SynthesisWriter` - Writes introduction and verse commentary
- `MasterEditor` - Provides final editorial polish

**Think of them as**: The scholars who read the books and write the commentary

### How They Work Together

```
MicroAnalyst (AI) discovers interesting words
    ↓
Generates ResearchRequest: ["רעה", "מִשְׁפָּט", "חֶסֶד"]
    ↓
ResearchAssembler coordinates librarians
    ↓
BDBLibrarian fetches lexicon entries
ConcordanceLibrarian finds usage patterns
FigurativeLibrarian identifies metaphors
CommentaryLibrarian retrieves Rashi, Ibn Ezra, etc.
LiturgicalLibrarian identifies prayer contexts
    ↓
ResearchBundle assembled
    ↓
SynthesisWriter (AI) analyzes bundle and writes commentary
```

---

## Data Flow

### Complete Pipeline Flow

```
1. INPUT
   └─ Psalm number (e.g., 23)

2. MACRO ANALYST
   ├─ Fetches: Psalm text (Hebrew/English) from TanakhDatabase
   ├─ Fetches: RAG context (genre, structure, Ugaritic parallels)
   └─ Produces: MacroAnalysis
      ├─ thesis_statement
      ├─ structural_outline
      ├─ poetic_devices
      └─ research_questions

3. MICRO ANALYST
   ├─ Receives: MacroAnalysis
   ├─ Fetches: Psalm text + LXX (Greek translation)
   ├─ Generates: Phonetic transcriptions with stress marking
   ├─ Stage 1: Discovery pass (identifies interesting features)
   ├─ Stage 2: Generates ResearchRequest
   └─ Produces: MicroAnalysis + ResearchRequest

4. RESEARCH ASSEMBLER
   ├─ Receives: ResearchRequest
   ├─ Dispatches to librarians:
   │  ├─ BDBLibrarian → lexicon entries
   │  ├─ ConcordanceLibrarian → usage patterns
   │  ├─ FigurativeLibrarian → metaphor/simile instances
   │  └─ CommentaryLibrarian → traditional interpretations
   └─ Produces: ResearchBundle

5. SYNTHESIS WRITER
   ├─ Receives: MacroAnalysis + MicroAnalysis + ResearchBundle
   ├─ Generates introduction essay (800-1600 words)
   ├─ Generates verse-by-verse commentary (300-500 words/verse)
   └─ Produces: Commentary draft

6. MASTER EDITOR
   ├─ Receives: All materials + commentary draft
   ├─ Performs: Critical review and revision
   ├─ Corrects: Factual errors, style issues, missed insights
   └─ Produces: Final polished commentary

7. OUTPUT
   ├─ psalm_NNN_edited.md (complete commentary)
   ├─ psalm_NNN_edited_intro.md (introduction only)
   ├─ psalm_NNN_edited_verses.md (verse commentary only)
   └─ psalm_NNN_edited_assessment.md (editorial notes)
```

### Data Structures

**MacroAnalysis** (Pass 1)
```python
MacroAnalysis(
    psalm_number: int,
    thesis_statement: str,
    genre: str,
    historical_context: str,
    structural_outline: List[StructuralDivision],
    poetic_devices: List[PoeticDevice],
    research_questions: List[str],
    working_notes: str
)
```

**MicroAnalysis** (Pass 2)
```python
MicroAnalysis(
    psalm_number: int,
    verse_commentaries: List[VerseCommentary],
    thematic_threads: List[str],
    interesting_questions: List[str],
    synthesis_notes: str
)

VerseCommentary(
    verse_number: int,
    commentary: str,
    lexical_insights: List[str],
    figurative_analysis: List[str],
    thesis_connection: str,
    phonetic_transcription: str  # NEW: with stress marking
)
```

**ResearchBundle** (Pass 2.5)
```python
ResearchBundle(
    psalm_chapter: int,
    lexicon_bundle: LexiconBundle,
    concordance_bundles: List[ConcordanceBundle],
    figurative_bundles: List[FigurativeBundle],
    commentary_bundles: List[CommentaryBundle],
    rag_context: RAGContext
)
```

---

## Adding a New Agent

### Step 1: Determine Agent Type

**Librarian Agent** (if you're fetching data from an external source):
- Pure Python, no LLM
- Extends librarian pattern
- Place in `src/agents/`

**AI Agent** (if you're analyzing or writing):
- Uses Claude or GPT
- Extends AI agent pattern
- Place in `src/agents/`

### Step 2: Create Agent File

**Template for Librarian Agent**:

```python
"""
New Librarian Agent
Fetches [DESCRIPTION] from [SOURCE].
"""

from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class DataEntry:
    """Single entry from the data source."""
    field1: str
    field2: str

    def to_dict(self) -> Dict:
        return {'field1': self.field1, 'field2': self.field2}

@dataclass
class DataBundle:
    """Collection of entries."""
    entries: List[DataEntry]

    def to_dict(self) -> Dict:
        return {'entries': [e.to_dict() for e in self.entries]}

class NewLibrarian:
    """Fetches data from [SOURCE]."""

    def __init__(self, api_key: Optional[str] = None):
        self.client = ExternalClient(api_key)

    def fetch_entry(self, query: str) -> List[DataEntry]:
        """Fetch single entry."""
        # Implementation
        pass

    def fetch_multiple(self, queries: List[str]) -> DataBundle:
        """Fetch multiple entries."""
        entries = []
        for query in queries:
            entries.extend(self.fetch_entry(query))
        return DataBundle(entries=entries)
```

**Template for AI Agent**:

```python
"""
New AI Agent (Pass N)
[DESCRIPTION OF PURPOSE]

Model: Claude Sonnet 4.5 / GPT-5
Input: [INPUTS]
Output: [OUTPUTS]
"""

import os
from pathlib import Path
from typing import Optional
import anthropic
from dotenv import load_dotenv

load_dotenv()

AGENT_PROMPT = """You are a [ROLE].

Your task: [DESCRIPTION]

## INPUT
{input_data}

## OUTPUT FORMAT
Return ONLY valid JSON:
{{
    "field1": "value",
    "field2": ["list", "of", "items"]
}}
"""

class NewAgent:
    """[BRIEF DESCRIPTION]"""

    def __init__(self, api_key: Optional[str] = None, logger=None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"
        self.logger = logger or get_logger("new_agent")

    def analyze(self, input_data: str) -> Dict:
        """Main analysis method."""
        # Build prompt
        prompt = AGENT_PROMPT.format(input_data=input_data)

        # Call API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        response_text = response.content[0].text
        data = json.loads(response_text)

        return data
```

### Step 3: Add to Pipeline

**If Librarian**: Register in `ResearchAssembler`:

```python
# In src/agents/research_assembler.py

class ResearchAssembler:
    def __init__(self):
        # ... existing librarians ...
        self.new_librarian = NewLibrarian()

    def assemble(self, request: ResearchRequest):
        # Add new data fetching
        new_data = self.new_librarian.fetch_multiple(request.new_requests)

        # Include in bundle
        return ResearchBundle(
            # ... existing fields ...
            new_data=new_data
        )
```

**If AI Agent**: Add to pipeline sequence:

```python
# In main pipeline script
from src.agents.new_agent import NewAgent

# Initialize
agent = NewAgent()

# Call in sequence
new_output = agent.analyze(previous_output)
```

### Step 4: Add Tests

Create `tests/test_new_agent.py`:

```python
"""Tests for NewAgent"""

import pytest
from src.agents.new_agent import NewAgent

def test_agent_initialization():
    """Test agent can be initialized."""
    agent = NewAgent()
    assert agent is not None

def test_agent_analysis():
    """Test agent produces expected output."""
    agent = NewAgent()
    result = agent.analyze("test input")
    assert result is not None
    assert 'expected_field' in result

@pytest.mark.integration
def test_agent_with_real_data():
    """Integration test with real psalm data."""
    agent = NewAgent()
    result = agent.analyze(psalm_number=23)
    assert result.field1 == "expected_value"
```

### Step 5: Document

Add to this guide:
- Update agent list in [Agent Architecture](#agent-architecture)
- Update data flow diagram in [Data Flow](#data-flow)
- Add example usage

---

## Testing Procedures

### Test Organization

```
tests/
├── test_macro_analyst.py       # Pass 1 tests
├── test_micro_analyst.py       # Pass 2 tests
├── test_synthesis_writer.py   # Pass 3 tests
├── test_phonetic_analyst.py   # Phonetic transcription tests
└── test_data/                  # Fixtures and sample data
```

### Running Tests

**Run all tests**:
```bash
pytest tests/
```

**Run specific test file**:
```bash
pytest tests/test_macro_analyst.py
```

**Run with verbose output**:
```bash
pytest tests/ -v
```

**Run integration tests only** (requires API keys):
```bash
pytest tests/ -m integration
```

**Skip integration tests** (for quick validation):
```bash
pytest tests/ -m "not integration"
```

### Test Categories

**Unit Tests**: Test individual functions and methods
- No API calls
- Use mock data
- Fast execution

**Integration Tests**: Test with real APIs
- Require API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY)
- Test actual pipeline flows
- Slower execution
- Mark with `@pytest.mark.integration`

### Example Test

```python
"""Test MacroAnalyst agent."""

import pytest
from src.agents.macro_analyst import MacroAnalyst
from src.schemas.analysis_schemas import MacroAnalysis

def test_macro_analyst_initialization():
    """Test MacroAnalyst can be initialized."""
    analyst = MacroAnalyst()
    assert analyst.model == "claude-sonnet-4-20250514"

@pytest.mark.integration
def test_macro_analyst_psalm_23():
    """Integration test: Analyze Psalm 23."""
    analyst = MacroAnalyst()

    # Analyze
    analysis = analyst.analyze_psalm(23)

    # Validate structure
    assert isinstance(analysis, MacroAnalysis)
    assert analysis.psalm_number == 23
    assert len(analysis.thesis_statement) > 50
    assert len(analysis.structural_outline) > 0
    assert analysis.genre in ["Hymn", "Lament", "Royal Psalm", "Wisdom"]

    # Validate content
    assert "shepherd" in analysis.thesis_statement.lower()
```

### Validation Checklist

Before committing:

- [ ] All unit tests pass
- [ ] Integration tests pass (if APIs available)
- [ ] Code follows existing patterns
- [ ] Docstrings added for new functions
- [ ] Type hints included
- [ ] No hardcoded paths or credentials
- [ ] Error handling implemented
- [ ] Logging added for debugging

---

## Common Patterns

### Environment Variables

All API keys use environment variables:

```python
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not set")
```

Create `.env` file:
```
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

### Error Handling

```python
def fetch_data(query: str):
    """Fetch data with proper error handling."""
    try:
        response = api_client.fetch(query)
        if not response:
            logger.warning(f"No results for query: {query}")
            return []
        return parse_response(response)
    except APIError as e:
        logger.error(f"API error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []  # Graceful degradation
```

### Logging

```python
from src.utils.logger import get_logger

logger = get_logger("agent_name")

# Log levels
logger.debug("Detailed info for debugging")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")

# Context logging
logger.info(f"Processing psalm {psalm_number}")
logger.info(f"  Input length: {len(input_data)} chars")
logger.info(f"  Output length: {len(output_data)} chars")
```

### File I/O

```python
from pathlib import Path

# Reading
input_path = Path("data/input.json")
with open(input_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Writing
output_path = Path("output/result.md")
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(content)

# Check existence
if not input_path.exists():
    raise FileNotFoundError(f"File not found: {input_path}")
```

### JSON Parsing

```python
import json

# Safe parsing with fallback
def parse_json_response(text: str) -> dict:
    """Parse JSON with error handling."""
    try:
        # Strip markdown code blocks if present
        if text.startswith("```"):
            lines = text.split('\n')
            text = '\n'.join(lines[1:-1])

        data = json.loads(text)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        logger.debug(f"Response text: {text[:500]}")
        raise ValueError(f"Invalid JSON: {e}")
```

### Context Managers

```python
# Database access
with TanakhDatabase() as db:
    psalm = db.get_psalm(23)
    # db.close() called automatically

# Agent initialization
with MacroAnalyst() as analyst:
    analysis = analyst.analyze_psalm(23)
    # cleanup called automatically
```

---

## Additional Resources

### Key Documentation

- `docs/TECHNICAL_ARCHITECTURE_SUMMARY.md` - System architecture overview
- `docs/rag/analytical_framework.md` - Poetic analysis methodology
- `docs/rag/psalm_function/` - Genre and structure analysis
- `docs/rag/ugaritic/` - Ancient Near Eastern parallels

### External APIs

- **Sefaria API**: https://www.sefaria.org/developers
  - Hebrew lexicons (BDB, Klein)
  - Traditional commentaries (Rashi, Ibn Ezra, Radak, Metzudat David, Malbim, Meiri, Torah Temimah)
  - Text retrieval (Tanakh, LXX)

- **Anthropic Claude**: https://www.anthropic.com/api
  - Model: `claude-sonnet-4-20250514`
  - Extended thinking mode available

- **OpenAI GPT-5**: https://platform.openai.com/docs
  - Model: `gpt-5`
  - Used for master editorial review

### Database Schema

The local SQLite database (`database/tanakh.db`) contains:

- **psalms** table: Hebrew and English text
- **concordance** table: Word usage indices
- **figurative_language** table: Metaphor/simile database with hierarchical tagging

### Project Philosophy

**Quality over Speed**: This pipeline prioritizes scholarly excellence. Each pass builds on the previous, with humans-in-the-loop review available at every stage.

**Transparency**: All prompts, intermediate outputs, and editorial decisions are logged and saved for review.

**Scholarly Rigor**: Commentary is grounded in:
- Hebrew lexical analysis (BDB, Klein)
- Concordance patterns across Scripture
- Figurative language comparative analysis
- Traditional Jewish interpretation
- Ancient Near Eastern context
- Modern critical scholarship

**Audience-Aware**: Writing targets sophisticated lay readers (New Yorker/Atlantic level) - scholarly but accessible.

---

## Getting Help

**Bugs or Issues**: Open an issue on GitHub with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Relevant log output

**Questions**: Check existing documentation first:
- This developer guide for code navigation
- Architecture docs for system design
- Agent docstrings for API usage

**Contributing**:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request with clear description

---

*Last updated: 2025-10-24*
*For questions or suggestions, contact the maintainers.*
