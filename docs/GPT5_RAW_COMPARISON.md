# GPT-5 Raw Comparison Script

## Overview

This script generates psalm commentary using **ONLY GPT-5 (o1)** with the raw psalm text and high-quality writing instructions. It provides a baseline for comparison with the full research-enhanced pipeline.

**What it does:**
- Generates introduction essay (800-1200 words)
- Generates verse-by-verse commentary (150-400 words per verse)
- Uses only the Hebrew and English text of the psalm
- No research bundle, no macro/micro analysis, no other agents

**What it doesn't have access to:**
- BDB lexicon entries
- Concordance data showing usage patterns
- Figurative language database with 40K+ instances
- Traditional commentary (Rashi, Ibn Ezra, Radak)
- Ugaritic parallels from RAG
- Macro structural thesis
- Micro verse discoveries
- Research questions from analysts

## Purpose

This allows you to compare:
1. **GPT-5 Raw Output** (this script) - What GPT-5 can produce with only instructions and psalm text
2. **Full Pipeline Output** - What the research-enhanced pipeline produces with macro/micro analysis + research bundle + synthesis + master editing

The comparison helps assess:
- How much value the research bundle adds
- Whether the macro/micro analysis provides useful guidance
- What GPT-5 can infer vs. what requires research
- The quality difference between raw generation and research-enhanced generation

## Usage

### Interactive Mode (Prompts for Psalm Number)

```bash
python scripts/gpt5_raw_comparison.py
```

You'll be prompted to enter a psalm number (1-150).

### Command-Line Mode (Specify Psalm Number)

```bash
# Generate commentary for Psalm 23
python scripts/gpt5_raw_comparison.py 23

# Generate for Psalm 1
python scripts/gpt5_raw_comparison.py 1

# Generate for Psalm 145
python scripts/gpt5_raw_comparison.py 145
```

### Custom Output Directory

```bash
python scripts/gpt5_raw_comparison.py 23 --output-dir output/comparisons/psalm_23
```

## Output Files

The script generates three files in `output/gpt5_raw/` (or your specified directory):

1. **`psalm_XXX_gpt5_raw.md`** - Complete commentary (introduction + verses)
2. **`psalm_XXX_gpt5_raw_intro.md`** - Introduction essay only
3. **`psalm_XXX_gpt5_raw_verses.md`** - Verse-by-verse commentary only

## Example Workflow

### 1. Generate GPT-5 Raw Commentary

```bash
python scripts/gpt5_raw_comparison.py 23
```

### 2. Generate Research-Enhanced Pipeline Commentary

```bash
python scripts/run_enhanced_pipeline.py 23 --output-dir output/test_psalm_23
```

### 3. Compare the Two Outputs

Compare these files:
- **GPT-5 Raw**: `output/gpt5_raw/psalm_023_gpt5_raw.md`
- **Pipeline**: `output/test_psalm_23/psalm_023_print_ready.md`

### What to Look For in Comparison:

**Introduction Essay:**
- Does the pipeline version cite specific lexical insights the raw version couldn't know?
- Does the pipeline version reference concordance patterns or figurative language data?
- Does the pipeline version engage with traditional commentary?
- Is the structural analysis more detailed with macro thesis?

**Verse Commentary:**
- Does the pipeline version cite specific Hebrew lexical insights from BDB?
- Does the pipeline version reference how figurative language is used elsewhere in Scripture?
- Does the pipeline version cite Rashi, Ibn Ezra, or other traditional commentators?
- Does the pipeline version reference Ugaritic or ANE parallels?
- Is the poetic analysis more detailed?

## Performance

- **Generation time**: 2-5 minutes (depending on psalm length)
- **Cost**: ~$0.50-0.75 per psalm (GPT-5 pricing)
- **Quality**: High-quality scholarly prose, but limited to what GPT-5 knows/can infer

## Technical Details

**Model**: GPT-5 (o1)

**Input to GPT-5**:
- Psalm text (Hebrew + English)
- High-quality writing instructions adapted from the full pipeline prompts
- Style guidelines (Robert Alter level, no LLM-ish breathlessness)

**No Access To**:
- Research bundle (lexicon, concordance, figurative, commentary)
- Macro structural thesis
- Micro verse discoveries
- Research questions from analysts

**Writing Instructions Include**:
- Scholarly style guidelines (Alter, Kugel, Davis level)
- Avoid LLM-ish superlatives ("masterpiece," "tour de force," etc.)
- Focus on analysis over praise
- Vary sentence structure
- Define technical terms
- Ground in textual evidence
- 800-1200 word introduction
- 150-400 word verse commentaries (longer when warranted)

## Recommended Comparison Psalms

Good psalms to compare:

1. **Psalm 1** (6 verses, wisdom) - Short, allows close comparison
2. **Psalm 23** (6 verses, trust/pastoral) - Famous, well-known
3. **Psalm 29** (11 verses, theophany) - Ugaritic parallels important
4. **Psalm 145** (21 verses, praise acrostic) - Long, complex structure

## Notes

- The script uses the same database as the full pipeline (`database/tanakh.db`)
- Output is formatted in markdown with proper Hebrew/English text
- GPT-5 will rely on its training knowledge for scholarly insights
- The full pipeline has access to ~130k tokens of research materials per psalm
- This raw version has access to only the psalm text (~2-10k tokens)

## See Also

- [docs/NEXT_SESSION_PROMPT.md](NEXT_SESSION_PROMPT.md) - Full pipeline documentation
- [docs/PIPELINE_SUMMARY_INTEGRATION.md](PIPELINE_SUMMARY_INTEGRATION.md) - Pipeline statistics tracking
- [scripts/run_enhanced_pipeline.py](../scripts/run_enhanced_pipeline.py) - Full research-enhanced pipeline
