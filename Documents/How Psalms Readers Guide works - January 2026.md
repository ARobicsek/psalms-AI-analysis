# How the Psalms Reader's Guide Works

**Updated: January 2026**

## Overview

The Psalms Reader's Guide is generated through an AI-powered pipeline that combines the reasoning capabilities of multiple advanced language models with ten specialized digital "librarians" that retrieve and curate source material. This system produces publication-quality biblical commentary that rivals traditional scholarly work.

The key innovation is a "telescopic analysis" approach—breaking complex tasks into specialized passes, each building on previous work while maintaining focus on specific aspects of analysis.

## The Six-Stage Pipeline

### Stage 1: Macro Analysis — Setting the Stage

The first AI agent (Claude Sonnet 4.5) examines the entire psalm with access to multiple source texts:
- **Hebrew (Masoretic Text)**: The authoritative Jewish text with vowels and cantillation
- **English translation**: Jewish Publication Society (1985) rendering
- **Septuagint (LXX)**: Ancient Greek translation for textual criticism and early interpretation insights

The agent establishes:
- **Genre identification**: Is this a lament, praise, thanksgiving, wisdom, or royal psalm?
- **Structural framework**: How is the psalm organized? Where are the turns and transitions?
- **Thematic thesis**: What is the psalm's central argument or spiritual insight?
- **Research questions**: What puzzles or patterns require deeper investigation?

This high-level view prevents the pipeline from getting lost in details before understanding the whole.

### Stage 2: Micro Analysis — Verse-by-Verse Discovery

A second AI agent (Claude Sonnet 4.5) performs discovery-driven analysis of each verse, looking for:
- **Hebrew wordplay**: Puns, alliteration, and sound patterns
- **Unusual vocabulary**: Rare words that may carry special significance
- **Intertextual echoes**: Connections to other biblical passages
- **Syntactic features**: Word order inversions, emphatic constructions
- **LXX variants**: Where the Greek translation differs, suggesting early textual traditions

The agent works with **phonetic transcriptions** of the Hebrew text, enabling accurate analysis of sound patterns, alliteration, and wordplay without requiring knowledge of Hebrew pronunciation.

Crucially, this agent generates specific **research requests** for the librarians—asking for lexicon entries, concordance searches, figurative language parallels, and traditional commentary on particular terms and phrases.

### Stage 3: Research Assembly — The Ten Librarians

Ten specialized Python-based "librarians" retrieve and curate source material:

1. **BDB Librarian**: Hebrew lexicon lookups from the Brown-Driver-Briggs and Klein dictionaries via Sefaria API

2. **Concordance Librarian**: Searches a Hebrew concordance database with morphological variations, finding where specific words and phrases appear elsewhere in the Hebrew Bible

3. **Figurative Language Librarian**: Queries a pre-analyzed database of metaphors, similes, and figurative expressions across Biblical Hebrew literature

4. **Figurative Curator** (NEW): An LLM-enhanced agent (Gemini 3 Pro) that transforms raw figurative concordance results into curated scholarly insights. Using a 3-iteration refinement process, it curates 5-15 examples per vehicle with full Hebrew text and synthesizes 4-5 prose insights (100-150 words each) connecting the examples to the psalm's themes.

5. **Commentary Librarian**: Fetches traditional Jewish commentaries—Rashi, Ibn Ezra, Radak, Metzudat David, Malbim, Meiri, and Torah Temimah

6. **Liturgical Librarian**: Identifies where psalm passages appear in Jewish liturgy across three traditions (Ashkenaz, Sefard, Edot HaMizrach), generating intelligent summaries using Gemini 2.5 Pro

7. **Related Psalms Librarian**: Uses statistical analysis (V6 scoring) to identify the five most related psalms, showing shared roots, contiguous phrases, and skipgram patterns

8. **Sacks Librarian**: Retrieves Rabbi Jonathan Sacks' references and insights on the psalm

9. **Deep Web Research Librarian**: Loads manually prepared research on cultural and artistic afterlife—how the psalm has been used in paintings, music, literature, and political discourse

10. **Research Bundle Assembler**: Coordinates all librarians and formats results into a comprehensive research bundle (up to 700,000 characters)

### Stage 3b: Figurative Language Curation

The Figurative Curator agent (Gemini 3 Pro with high reasoning) transforms raw figurative concordance results into scholarly interpretive insights:

- Analyzes figurative vehicle requests from the Micro Analyst
- Executes and refines searches against the figurative language database
- Curates 5-15 examples per vehicle with full Hebrew text
- Synthesizes 4-5 prose insights connecting examples to the psalm's themes
- Adapts analysis structure to the psalm's pattern (journey, descent_ascent, lament_structure, etc.)

### Stage 4: Synthesis Writing — Creating the Commentary

A third AI agent (Claude Sonnet 4.5, or Gemini 2.5 Pro for large psalms) integrates all analysis into coherent commentary:

- **Introduction essay**: 800-1200 words situating the psalm in its genre, historical context, and theological significance
- **Verse-by-verse commentary**: 150-400+ words per verse with generous quotation of sources in Hebrew and English
- **Enhanced quotation emphasis**: Biblical parallels are quoted, not just cited
- **Poetic punctuation**: LLM-generated verses include semicolons, periods, and commas showing structural divisions

For large psalms (51+ verses), the system automatically switches to Gemini 2.5 Pro, leveraging its 1 million token context window to prevent content loss from research bundle trimming.

### Stage 5: Editorial Review — The Master Editor

A fourth AI agent (GPT-5.1 with high reasoning effort) receives all prior outputs—typically 350,000 characters—for critical review using the restructured V2 prompt with explicit Deep Research guidance:

- **Factual accuracy**: Biblical, historical, and grammatical verification
- **Source verification**: Ensuring claims are supported by retrieved sources
- **Technical term definitions**: Making scholarly vocabulary accessible
- **Integration of cultural afterlife**: Weaving in reception history, art, music references
- **"Aha! moment" insights**: Highlights discoveries only possible through comprehensive LLM analysis
- **Style refinement**: Eliminating AI tendencies toward breathlessness or jargon

The Master Editor produces **two editions**:
1. **Main Edition**: For sophisticated lay readers (New Yorker/Atlantic audience)
2. **College Edition**: More accessible version for undergraduate students

### Stage 6: Document Generation

Python scripts format the commentary for publication:
- Divine name modifications for study texts (יהוה → ה׳)
- Professional Word document formatting with Hebrew fonts
- Phonetic transcription italicization
- Bidirectional text handling
- Three output files: Main commentary, College edition, Combined document

## Sources Consulted

### Traditional Commentaries
- **Rashi** (11th century France) — concise, focused on plain meaning
- **Ibn Ezra** (12th century Spain) — grammatical precision, philosophical depth
- **Radak** (13th century Provence) — expanded explanations, linguistic analysis
- **Metzudat David** (18th century) — accessible verse-by-verse commentary
- **Malbim** (19th century) — systematic analysis of synonyms and structure
- **Meiri** (13th century Provence) — philosophical and ethical interpretation
- **Torah Temimah** (19th century) — connects verses to rabbinic literature

### Modern Scholarship
- **Rabbi Jonathan Sacks** — contemporary British Orthodox philosopher
- **Deep Web Research** — cultural afterlife (art, music, literature, politics), scholarly debates, and reception history

### Linguistic Resources
- **BDB Dictionary** — Brown-Driver-Briggs Hebrew Lexicon
- **Klein Dictionary** — Comprehensive etymological dictionary
- **Hebrew Concordance** — 4-layer normalization (exact, voweled, consonantal, root)
- **Figurative Language Database** — Pre-analyzed metaphors and similes with curated insights
- **Phonetic Transcription System** — Reconstructed Biblical Hebrew phonology with dagesh distinction (b/v, k/kh, p/f)

### Ancient Translations
- **Septuagint (LXX)** — Ancient Greek translation, crucial for textual criticism and understanding early interpretive traditions

### Statistical Analysis
- **V6 Related Psalms Analysis** — 11,170 psalm pairs analyzed for shared roots, contiguous phrases, and skipgram patterns

## Key Technical Features

### Multi-Model Architecture
| Model | Purpose |
|-------|---------|
| Claude Sonnet 4.5 | Macro Analysis, Micro Analysis, Synthesis Writing |
| Gemini 2.5 Pro | Synthesis fallback for large psalms (1M token context) |
| Gemini 3 Pro | Figurative Curator (curated insights) |
| GPT-5.1 | Master Editorial Review (main and college editions) |

### Quality Assurance
- Multi-pass validation with cross-checking between agents
- Enhanced quotation verification (sources quoted, not just cited)
- Phonetic accuracy verification against authoritative transcriptions
- Poetic punctuation ensuring verses show structural divisions

### Advanced Features
- **Resume capability**: Pipeline can restart from any step
- **Special Instruction Pipeline**: Author-directed revisions without altering standard outputs
- **Strategic Verse Grouping**: Prevents truncation in long psalms
- **Priority-Based Figurative Trimming**: LLM-decided term priority with lowest-priority content trimmed first

## The Result

Each psalm commentary represents a synthesis of:
- Traditional Jewish interpretation spanning a millennium
- Modern scholarly analysis and linguistic precision
- Cultural reception and artistic legacy
- AI-enhanced pattern recognition and cross-referencing
- Careful editorial refinement for accessibility and accuracy

The goal: scholarly depth made accessible to thoughtful readers, preserving the richness of Hebrew while opening it to English-language audiences.
