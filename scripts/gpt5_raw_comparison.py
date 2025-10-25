"""
GPT-5 Raw Comparison Script

This script generates commentary using ONLY GPT-5 with raw psalm text and instructions.
No research bundle, no other agents - just the psalm text and quality writing instructions.

This allows comparison with the full research-enhanced pipeline to see the value
added by macro/micro analysis and the research bundle.

Usage:
    python scripts/gpt5_raw_comparison.py [PSALM_NUMBER]

    If no psalm number is provided, you'll be prompted to enter one.

Example:
    python scripts/gpt5_raw_comparison.py 23
    python scripts/gpt5_raw_comparison.py  # Will prompt for psalm number

Author: Claude (Anthropic)
Date: 2025-10-19
"""

import sys
import os
import time
import argparse
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI
from dotenv import load_dotenv
from src.data_sources.tanakh_database import TanakhDatabase
from src.utils.logger import get_logger

# Load environment variables
load_dotenv()


# GPT-5 Introduction Prompt (raw, no research)
GPT5_RAW_INTRO_PROMPT = """You are a distinguished biblical scholar writing an introduction essay for Psalm {psalm_number}.

You are akin to figures like Robert Alter, Ellen F. Davis, or James Kugel. Your task is to write a scholarly introduction essay for a sophisticated lay audience, such as the readers of The New Yorker or The Atlantic.

## THE PSALM TEXT

{psalm_text}

---

## YOUR TASK: WRITE INTRODUCTION ESSAY (800-1200 words)

Write a scholarly introduction essay that:

1. **Analyzes the psalm's structure and genre**
   - What is the psalm's literary form? (lament, praise, wisdom, royal, etc.)
   - How is it structured? What are the major divisions or movements?
   - What poetic devices are employed? (parallelism, chiasm, inclusio, etc.)

2. **Explores the central message and theology**
   - What is the psalm's core message or purpose?
   - What theological claims does it make?
   - How does it portray God, humanity, or the divine-human relationship?

3. **Examines poetic and rhetorical strategies**
   - What are the key poetic techniques and why do they matter?
   - What makes this psalm distinctive or memorable?
   - How do literary features serve theological or emotional aims?

4. **Considers historical and cultural context** (to the extent discernible from the text)
   - Are there clues about the psalm's setting or period?
   - What liturgical or worship contexts might it have served?
   - How does it relate to Ancient Near Eastern literary traditions?

5. **Addresses interpretive questions**
   - What are the most significant interpretive puzzles or debates?
   - What earned this psalm its place in the biblical canon?
   - What is fascinating about it from literary, theological, and historical perspectives?

6. **Engages prior scholarship** (based on your expertise)
   - Reference relevant traditional interpretations where appropriate
   - Acknowledge known interpretive debates
   - Draw on your knowledge of biblical scholarship

7. **Makes intertextual connections**
   - Cite parallel biblical texts where similar language/imagery appears (from your knowledge)
   - Reference Ancient Near Eastern parallels where relevant
   - Show how this psalm's language relates to other biblical literature

## WRITING STYLE GUIDELINES

You are a distinguished professor of biblical literature. Your prose should be scholarly, lucid, and engaging. Your tone is one of measured confidence, not breathless praise.

**Key Stylistic Directives:**

- **Tone & Persona**: Authoritative yet accessible. You are a trusted guide leading the reader through the literary and theological landscape of the psalm.

- **From Praise to Analysis**: Do not use effusive language. Avoid words like "masterpiece," "tour de force," "breathtaking," "audacious," or "remarkable." Show sophistication through analysis, not labels.

- **Instead of**: "The psalm's central innovation lies in its theological revolution..."
- **Try**: "The psalm's engine is the sevenfold repetition of imagery X. By taking the familiar motif and transforming it, the poet re-maps the relationship between God and creation."

- **Use Jargon Sparingly**: Technical terms should bring clarity, not signal academic status. When used, integrate them naturally and explain if necessary.

- **Emphasize Action and Imagery**: Use strong verbs and concrete imagery. Describe what the poet does. How do they construct the poem? What world do they build?

- **Vary Sentence Structure**: Mix shorter, punchier sentences with longer, complex ones. Use rhetorical questions to engage the reader.

## CRITICAL REQUIREMENTS

- **Length**: 800-1200 words (aim for the middle of this range)
- **Tone**: Scholarly but engaging, confident but nuanced
- **Structure**: Clear paragraphs with logical flow
- **Evidence**: Ground observations in the psalm text itself
- **Hebrew**: When referring to Hebrew terms, transliterate them (e.g., qôl YHWH)
- **Divine Name**: Replace the tetragrammaton with "the LORD" or "YHWH" as appropriate

---

Write the introduction essay below in plain text. Use markdown formatting for emphasis (*italics*) and Hebrew transliterations.
"""


# GPT-5 Verse Commentary Prompt (raw, no research)
GPT5_RAW_VERSE_PROMPT = """You are a biblical scholar writing verse-by-verse commentary for Psalm {psalm_number}.

You have already written an introduction essay (provided below). Now write detailed verse-by-verse annotations that complement (not repeat) the introduction.

## THE PSALM TEXT

{psalm_text}

## YOUR INTRODUCTION ESSAY (for context)

{introduction_essay}

---

## YOUR TASK: WRITE VERSE-BY-VERSE COMMENTARY

For EACH verse in the psalm, write commentary that explores diverse scholarly angles:

**LENGTH GUIDELINES:**
- Target length: 150-400 words per verse
- Can be longer (400+ words) if there's genuinely interesting material
- Let the content determine the length

### AREAS TO ILLUMINATE (when relevant):

1. **Poetics**
   - Parallelism types (synonymous, antithetical, synthetic, climactic)
   - Wordplay, alliteration, assonance
   - Sound patterns and phonetic effects
   - Meter and rhythm
   - Structural devices (chiasm, inclusio, envelope structure)
   - Unusual turns of phrase or distinctive Hebrew idioms

2. **Literary Insights**
   - Narrative techniques and rhetorical strategies
   - Genre conventions and innovations
   - Dramatic progression and turning points
   - Imagery and its function
   - Irony, hyperbole, understatement

3. **Historical and Cultic Context** (based on textual clues and your expertise)
   - Liturgical setting and worship context
   - Historical period indicators
   - Temple/sanctuary practices
   - Royal psalms and kingship theology
   - Festival associations

4. **Comparative Religion** (from your knowledge)
   - Ancient Near Eastern parallels (Ugaritic, Akkadian, Egyptian)
   - Polemic against or appropriation of ANE motifs
   - Cite specific texts where you know them

5. **Grammar and Syntax** (when illuminating)
   - Rare or ambiguous grammatical forms
   - Verb tenses and aspect (jussive, cohortative, imperative)
   - Word order significance
   - Difficult constructions that affect meaning

6. **Textual Insights** (from your expertise)
   - Known textual variants and their implications
   - Translation challenges
   - Scholarly debates about readings

7. **Lexical Analysis**
   - Etymology when theologically illuminating
   - Semantic range of key terms
   - Rare vocabulary
   - Technical terminology (legal, cultic, military, agricultural)

8. **Comparative Biblical Usage** (from your knowledge)
   - How this word/phrase appears elsewhere in Scripture
   - Development of theological concepts
   - Formulaic language and its variations
   - Quotations and allusions to other biblical texts

9. **Figurative Language**
   - How metaphors and similes function
   - What makes imagery effective or distinctive
   - Conventional vs. innovative uses of figures

10. **Traditional Interpretation** (from your knowledge)
    - Classical Jewish commentary when known
    - Patristic readings
    - Modern critical scholarship debates

### IMPORTANT NOTES:

- **Relationship to Introduction**: Your verse commentary should COMPLEMENT (not repeat) the introduction
- **Independence**: Don't force thematic connections if they're not natural - follow what's interesting in each verse
- **Reader Interest**: Focus on what would genuinely interest intelligent, well-read lay readers
- **Flexibility**: Some verses may focus on poetics, others on context, others on imagery - vary your approach
- **Depth over Breadth**: Better to explore 2-3 angles deeply than mention everything superficially
- **Evidence-Based**: Ground observations in the psalm text itself
- **Define Terms**: Explain technical terminology when used
- **Vary Approach**: Don't use the same scholarly angles for every verse

### FORMAT FOR EACH VERSE:

**Verse [N]**
[150-400 words of commentary]

---

## CRITICAL REQUIREMENTS

- **Cover ALL verses** in the psalm
- **Length**: 150-400 words per verse (longer when warranted)
- **Variety**: Vary your approach across different scholarly angles
- **Evidence**: Cite Hebrew terms (transliterated), textual details, observable features
- **Readability**: Scholarly but accessible (New Yorker/Atlantic level)
- **Define terms**: Explain technical terminology
- **Independence**: Follow what's interesting in each verse, not a forced template
- **Complementary**: Don't repeat what was said in the introduction

---

Write the verse-by-verse commentary below in plain text. Use markdown formatting.
"""


class GPT5RawComparison:
    """
    Generates psalm commentary using only GPT-5 with raw psalm text.

    No research bundle, no macro/micro analysis - just high-quality instructions
    and the psalm text itself.
    """

    def __init__(self, api_key: Optional[str] = None, logger=None):
        """Initialize GPT-5 raw comparison generator."""
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required (set OPENAI_API_KEY env var)")

        self.client = OpenAI(api_key=self.api_key)
        self.model = "o1"  # GPT-5
        self.logger = logger or get_logger("gpt5_raw_comparison")

        self.logger.info(f"GPT5RawComparison initialized with model {self.model}")

    def generate_commentary(
        self,
        psalm_number: int,
        db_path: Path = Path("database/tanakh.db")
    ) -> dict:
        """
        Generate complete commentary for a psalm using only GPT-5 and raw text.

        Args:
            psalm_number: Psalm number (1-150)
            db_path: Path to Tanakh database

        Returns:
            Dictionary with 'introduction' and 'verse_commentary' keys
        """
        self.logger.info(f"Generating GPT-5 raw commentary for Psalm {psalm_number}")

        # Load psalm text from database
        db = TanakhDatabase(db_path)
        psalm = db.get_psalm(psalm_number)

        if not psalm:
            raise ValueError(f"Psalm {psalm_number} not found in database")

        # Format psalm text (Hebrew + English)
        psalm_text_lines = []
        for verse in psalm.verses:
            psalm_text_lines.append(f"**Verse {verse.verse}**")
            psalm_text_lines.append(f"Hebrew: {verse.hebrew}")
            psalm_text_lines.append(f"English: {verse.english}")
            psalm_text_lines.append("")

        psalm_text = "\n".join(psalm_text_lines)

        self.logger.info(f"Psalm {psalm_number} has {len(psalm.verses)} verses")

        # Step 1: Generate introduction essay
        self.logger.info("Generating introduction essay with GPT-5...")
        introduction = self._generate_introduction(psalm_number, psalm_text)

        # Step 2: Generate verse commentary
        self.logger.info("Generating verse commentary with GPT-5...")
        verse_commentary = self._generate_verse_commentary(
            psalm_number,
            psalm_text,
            introduction
        )

        self.logger.info("GPT-5 raw commentary generation complete")

        return {
            'introduction': introduction,
            'verse_commentary': verse_commentary,
            'psalm_number': psalm_number,
            'verse_count': len(psalm.verses)
        }

    def _generate_introduction(self, psalm_number: int, psalm_text: str) -> str:
        """Generate introduction essay using GPT-5 with raw psalm text."""
        prompt = GPT5_RAW_INTRO_PROMPT.format(
            psalm_number=psalm_number,
            psalm_text=psalm_text
        )

        self.logger.info(f"Calling GPT-5 for introduction (prompt: {len(prompt)} chars)")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            introduction = response.choices[0].message.content.strip()
            self.logger.info(f"Introduction generated: {len(introduction)} chars")

            return introduction

        except Exception as e:
            self.logger.error(f"Error generating introduction: {e}")
            raise

    def _generate_verse_commentary(
        self,
        psalm_number: int,
        psalm_text: str,
        introduction: str
    ) -> str:
        """Generate verse commentary using GPT-5 with raw psalm text."""
        prompt = GPT5_RAW_VERSE_PROMPT.format(
            psalm_number=psalm_number,
            psalm_text=psalm_text,
            introduction_essay=introduction
        )

        self.logger.info(f"Calling GPT-5 for verse commentary (prompt: {len(prompt)} chars)")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            commentary = response.choices[0].message.content.strip()
            self.logger.info(f"Verse commentary generated: {len(commentary)} chars")

            return commentary

        except Exception as e:
            self.logger.error(f"Error generating verse commentary: {e}")
            raise

    def generate_and_save(
        self,
        psalm_number: int,
        output_dir: str = "output/gpt5_raw",
        db_path: Path = Path("database/tanakh.db")
    ) -> dict:
        """
        Generate commentary and save to files.

        Args:
            psalm_number: Psalm number (1-150)
            output_dir: Directory to save output files
            db_path: Path to Tanakh database

        Returns:
            Commentary dictionary
        """
        # Generate commentary
        commentary = self.generate_commentary(psalm_number, db_path)

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save complete commentary
        full_file = output_path / f"psalm_{psalm_number:03d}_gpt5_raw.md"
        with open(full_file, 'w', encoding='utf-8') as f:
            f.write(f"# Psalm {psalm_number} Commentary (GPT-5 Raw)\n\n")
            f.write("*Generated using only GPT-5 with raw psalm text - no research bundle*\n\n")
            f.write("---\n\n")
            f.write("## Introduction\n\n")
            f.write(commentary['introduction'])
            f.write("\n\n---\n\n")
            f.write("## Verse-by-Verse Commentary\n\n")
            f.write(commentary['verse_commentary'])

        self.logger.info(f"Saved complete commentary to {full_file}")

        # Save separate files
        intro_file = output_path / f"psalm_{psalm_number:03d}_gpt5_raw_intro.md"
        with open(intro_file, 'w', encoding='utf-8') as f:
            f.write(commentary['introduction'])

        verse_file = output_path / f"psalm_{psalm_number:03d}_gpt5_raw_verses.md"
        with open(verse_file, 'w', encoding='utf-8') as f:
            f.write(commentary['verse_commentary'])

        self.logger.info(f"Saved introduction to {intro_file}")
        self.logger.info(f"Saved verse commentary to {verse_file}")

        print(f"\n{'='*80}")
        print(f"GPT-5 RAW COMMENTARY COMPLETE: PSALM {psalm_number}")
        print(f"{'='*80}")
        print(f"\nFiles saved:")
        print(f"  • Complete: {full_file}")
        print(f"  • Introduction: {intro_file}")
        print(f"  • Verses: {verse_file}")
        print(f"\nVerse count: {commentary['verse_count']}")
        print(f"Introduction length: {len(commentary['introduction'])} chars")
        print(f"Verse commentary length: {len(commentary['verse_commentary'])} chars")
        print(f"{'='*80}\n")

        return commentary


def main():
    """Command-line interface for GPT-5 raw comparison."""
    # Ensure UTF-8 for Hebrew output on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Generate psalm commentary using only GPT-5 with raw psalm text (no research bundle)',
        epilog='Example: python scripts/gpt5_raw_comparison.py 23'
    )
    parser.add_argument(
        'psalm_number',
        type=int,
        nargs='?',  # Makes it optional
        help='Psalm number (1-150). If not provided, you will be prompted.'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output/gpt5_raw',
        help='Output directory (default: output/gpt5_raw)'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        default='database/tanakh.db',
        help='Path to Tanakh database (default: database/tanakh.db)'
    )

    args = parser.parse_args()

    # If psalm number not provided via argument, prompt for it
    if args.psalm_number is None:
        print("\n" + "="*80)
        print("GPT-5 RAW COMPARISON - Psalm Commentary Generator")
        print("="*80)
        print("\nThis script generates commentary using ONLY GPT-5 with raw psalm text.")
        print("No research bundle, no other agents - just high-quality instructions.\n")

        while True:
            try:
                psalm_input = input("Enter psalm number (1-150): ").strip()
                psalm_number = int(psalm_input)
                if 1 <= psalm_number <= 150:
                    break
                else:
                    print("Please enter a number between 1 and 150.")
            except ValueError:
                print("Please enter a valid number.")
            except KeyboardInterrupt:
                print("\n\nCancelled by user.")
                return 1

        args.psalm_number = psalm_number

    try:
        print(f"\n{'='*80}")
        print(f"GPT-5 RAW COMPARISON - PSALM {args.psalm_number}")
        print(f"{'='*80}\n")
        print(f"Database: {args.db_path}")
        print(f"Output directory: {args.output_dir}")
        print(f"\nThis will generate:")
        print(f"  1. Introduction essay (800-1200 words)")
        print(f"  2. Verse-by-verse commentary (150-400 words per verse)")
        print(f"\nUsing: GPT-5 with ONLY the raw psalm text\n")

        # Initialize generator
        generator = GPT5RawComparison()

        print("Starting generation...")
        print("This may take 2-5 minutes depending on psalm length.\n")

        start_time = time.time()

        # Generate and save
        commentary = generator.generate_and_save(
            psalm_number=args.psalm_number,
            output_dir=args.output_dir,
            db_path=Path(args.db_path)
        )

        duration = time.time() - start_time

        print(f"\nTotal generation time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print(f"\nYou can now compare this with the research-enhanced pipeline output!")

        return 0

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
