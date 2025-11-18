"""
Macro Analyst Agent (Pass 1)
Phase 3a: Chapter-level analysis with analytical framework

This agent produces the initial high-level thesis for a psalm, leveraging:
- RAG context (genre, structure, Ugaritic parallels)
- Analytical framework (poetic methodology)
- Extended thinking mode for deep analysis

Model: Claude Sonnet 4.5 with extended thinking
Input: Psalm text (Hebrew + English) + RAG context
Output: MacroAnalysis with thesis, structure, poetic devices, research questions

Author: Claude (Anthropic)
Date: 2025 (Phase 3a)
"""

import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, List, Any
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Handle imports for both module and script usage
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.agents.rag_manager import RAGManager, RAGContext
    from src.schemas.analysis_schemas import MacroAnalysis, StructuralDivision, PoeticDevice
    from src.data_sources.tanakh_database import TanakhDatabase
    from src.utils.logger import get_logger
else:
    from .rag_manager import RAGManager, RAGContext
    from ..schemas.analysis_schemas import MacroAnalysis, StructuralDivision, PoeticDevice
    from ..data_sources.tanakh_database import TanakhDatabase
    from ..utils.logger import get_logger


# System prompt for MacroAnalyst agent
MACRO_ANALYST_PROMPT = """You are a biblical scholar specializing in Hebrew poetry analysis.

You have been provided with Psalm {psalm_number} in both Hebrew and English, along with scholarly context (genre, structure, Ugaritic parallels, and an analytical framework for biblical poetry).

Your task is to produce a **macro-level analysis** - a chapter-level thesis that identifies the psalm's overall message, structure, and key poetic techniques. This analysis will guide subsequent detailed verse-by-verse commentary.

## PSALM TEXT

{psalm_text}

## SCHOLARLY CONTEXT

{rag_context}

---

## YOUR TASK: MACRO ANALYSIS

Produce a comprehensive chapter-level analysis addressing the following:

### 1. THESIS STATEMENT (2-3 sentences)
- What is the psalm's central message or argument?
- Go beyond surface-level readings - what deeper theological, poetic, or rhetorical insight does this psalm offer?
- How does this psalm function within ancient Israelite worship/theology?

### 2. GENRE IDENTIFICATION
- Confirm or refine the genre identified in the scholarly context
- If the genre is ambiguous, explain why and propose alternatives
- How does genre shape the psalm's rhetoric and theology?

### 3. HISTORICAL/THEOLOGICAL CONTEXT
- What is the likely setting or occasion for this psalm?
- What theological themes or concerns does it address?
- How does it relate to broader biblical themes or Ancient Near Eastern context?

### 4. STRUCTURAL OUTLINE
- Identify major structural divisions (e.g., vv. 1-3, vv. 4-6, etc.)
- For each division, provide:
  * **section**: The verse range (e.g., "vv. 1-2")
  * **theme**: Brief description of this section's theme
  * **notes**: Additional observations about structure, tone shifts, or key features
  * **are there unexpected moments? What is this poem really ABOUT?**

### 5. KEY POETIC DEVICES
- Identify the dominant poetic techniques used across the psalm
- For each device, provide:
  * **device**: Name of the technique (e.g., "anaphora", "chiasmus", "inclusio", "parallelism")
  * **description**: How it's employed in this psalm
  * **verses**: Where it appears
  * **function**: What rhetorical or theological purpose it serves

Consider:
- **Parallelism types**: Synonymous, antithetic, synthetic, emblematic
- **Sound patterns**: Alliteration, assonance, wordplay
- **Structural patterns**: Inclusio (bookending), chiasmus (AB|BA), refrain, staircase parallelism
- **Rhetorical devices**: Anaphora (repetition at start), epiphora (at end), anadiplosis (end-to-start)
- **Imagery**: Dominant metaphors, similes, personification
- **Verbal features**: Imperative mood, perfect/imperfect tenses, divine epithets

### 6. RESEARCH QUESTIONS FOR PASS 2
- Generate 5-10 specific questions (more for long psalms) that detailed verse-by-verse analysis should address
- Focus on areas that need lexical, concordance, or figurative language research
- Examples:
  * "How does the seven-fold 'voice of the LORD' relate to creation theology?"
  * "What is the significance of the shift from military to pastoral imagery?"
  * "How do the Ugaritic parallels illuminate the divine council scene?"

### 7. WORKING NOTES (OPTIONAL)
- Any additional analytical observations
- Ambiguities or interpretive challenges
- Connections to other psalms or biblical texts
- Raw thinking that might inform Pass 2 analysis

---

## OUTPUT FORMAT

Return ONLY a valid JSON object with this exact structure:

{{
  "psalm_number": {psalm_number},
  "thesis_statement": "Your 2-3 sentence thesis here...",
  "genre": "Genre name (e.g., Hymn of Praise, Lament, Royal Psalm)",
  "historical_context": "Brief historical/theological context...",
  "structural_outline": [
    {{
      "section": "vv. 1-2",
      "theme": "Brief theme description",
      "notes": "Additional structural observations"
    }},
    {{
      "section": "vv. 3-5",
      "theme": "Brief theme description",
      "notes": "Additional observations"
    }}
  ],
  "poetic_devices": [
    {{
      "device": "anaphora",
      "description": "How it's used in this psalm",
      "verses": "vv. 3-9",
      "function": "Rhetorical/theological purpose"
    }},
    {{
      "device": "inclusio",
      "description": "Opening and closing bookends",
      "verses": "v.1, v.11",
      "function": "Creates thematic unity"
    }}
  ],
  "research_questions": [
    "Specific question 1?",
    "Specific question 2?",
    "Specific question 3?"
  ],
  "working_notes": "Optional additional observations..."
}}

## CRITICAL REQUIREMENTS

1. **Be SPECIFIC**: Avoid vague generalities like "this psalm is about trust"
2. **Use the ANALYTICAL FRAMEWORK**: Apply the poetic methodology provided
3. **Leverage RAG CONTEXT**: Integrate genre info, structural notes, and Ugaritic parallels
4. **Think DEEPLY**: Use extended thinking to find non-obvious insights
5. **Be THOROUGH**: Identify ALL major structural divisions and poetic devices
6. **Return ONLY JSON**: No text before or after the JSON object

Take your time. Think deeply. Produce a thesis that will guide meaningful verse-by-verse analysis."""


class MacroAnalyst:
    """
    Pass 1: Macro Analysis Agent using Claude Sonnet 4.5.

    Produces chapter-level thesis and structural framework for a psalm,
    leveraging RAG context and analytical framework.

    Example:
        >>> analyst = MacroAnalyst(api_key="your-key")
        >>> analysis = analyst.analyze_psalm(29)
        >>> print(analysis.thesis_statement)
        >>> print(analysis.to_markdown())
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        db_path: Optional[Path] = None,
        docs_dir: str = "docs",
        logger=None
    ):
        """
        Initialize MacroAnalyst agent.

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            db_path: Path to Tanakh database (for fetching psalm text)
            docs_dir: Path to docs directory (for RAG documents)
            logger: Logger instance (or will create default)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required (pass api_key or set ANTHROPIC_API_KEY)")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-5"  # Sonnet 4.5 with extended thinking
        self.logger = logger or get_logger("macro_analyst")

        # Initialize RAG Manager
        self.rag_manager = RAGManager(docs_dir=docs_dir)

        # Initialize Tanakh Database
        self.db = TanakhDatabase(db_path=db_path)

        self.logger.info(f"MacroAnalyst initialized with model {self.model}")

    def analyze_psalm(
        self,
        psalm_number: int,
        max_tokens: int = 32000,  # Doubled from 16K to ensure no output constraint
        include_full_framework: bool = False
    ) -> MacroAnalysis:
        """
        Analyze a psalm at the macro level.

        Args:
            psalm_number: Psalm number (1-150)
            max_tokens: Maximum tokens for response (default: 32K)
            include_full_framework: Whether to include full analytical framework
                                   (can be very large, ~1200 lines)

        Returns:
            MacroAnalysis object with thesis, structure, and poetic devices

        Raises:
            ValueError: If psalm not found or JSON parsing fails
        """
        self.logger.info(f"Starting macro analysis for Psalm {psalm_number}")

        # Step 1: Get psalm text from database
        psalm_text = self.db.get_psalm(psalm_number)
        if not psalm_text:
            raise ValueError(f"Psalm {psalm_number} not found in database. Run database download first.")

        # Step 2: Get RAG context
        rag_context = self.rag_manager.get_rag_context(psalm_number)

        # Step 3: Format inputs for prompt
        psalm_text_formatted = self._format_psalm_text(psalm_text)
        rag_context_formatted = self.rag_manager.format_for_prompt(
            rag_context,
            include_framework=include_full_framework
        )

        # Step 4: Build prompt
        prompt = MACRO_ANALYST_PROMPT.format(
            psalm_number=psalm_number,
            psalm_text=psalm_text_formatted,
            rag_context=rag_context_formatted
        )

        # Log prompt stats
        self.logger.info(f"Prompt length: {len(prompt)} characters")
        self.logger.info(f"Psalm verses: {psalm_text.verse_count}")
        self.logger.info(f"RAG: Genre={rag_context.psalm_function['genre'] if rag_context.psalm_function else 'N/A'}, "
                        f"Ugaritic={len(rag_context.ugaritic_parallels)} parallels")

        # Step 5: Call Claude Sonnet 4.5 with extended thinking
        try:
            self.logger.info(f"Calling Claude API with model: {self.model}")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                thinking={
                    "type": "enabled",
                    "budget_tokens": 10000  # Allow extended thinking
                },
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            self.logger.info("API call successful")

            # Extract thinking and response
            thinking_text = ""
            response_text = ""

            # Debug: Log response structure
            self.logger.info(f"Response has {len(response.content)} content blocks")
            for i, block in enumerate(response.content):
                self.logger.info(f"  Block {i}: type={block.type}")
                if block.type == "thinking":
                    thinking_text = block.thinking
                    self.logger.info(f"    Thinking block: {len(thinking_text)} chars")
                elif block.type == "text":
                    response_text = block.text
                    self.logger.info(f"    Text block: {len(response_text)} chars")

            self.logger.info(f"Response received. Thinking tokens: {len(thinking_text.split()) if thinking_text else 0}")

            # Check if we got a text response
            if not response_text or not response_text.strip():
                self.logger.error("ERROR: Empty text block received from API!")
                self.logger.error(f"Model: {self.model}")
                self.logger.error(f"Response structure: {len(response.content)} blocks")
                for i, block in enumerate(response.content):
                    self.logger.error(f"  Block {i}: type={block.type}")
                self.logger.error(f"Thinking text length: {len(thinking_text)} chars")
                raise ValueError("MacroAnalyst returned empty text block. This may be due to extended thinking mode allocating all tokens to thinking.")

            # Log API call
            self.logger.log_api_call(
                api_name="Anthropic Claude",
                endpoint=self.model,
                status_code=200,
                response_time_ms=0
            )

            # Step 6: Parse JSON response
            response_text = response_text.strip()

            # Strip markdown code fences if present
            if response_text.startswith("```json"):
                self.logger.info("Removing markdown json code fence from response")
                response_text = response_text[7:]  # Remove ```json
            elif response_text.startswith("```"):
                self.logger.info("Removing markdown code fence from response")
                response_text = response_text[3:]  # Remove ```

            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove trailing ```

            response_text = response_text.strip()

            try:
                data = json.loads(response_text)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {e}")
                self.logger.error(f"Response text (first 1000 chars): {response_text[:1000]}...")
                raise ValueError(f"Invalid JSON from MacroAnalyst: {e}")

            # Step 7: Create MacroAnalysis object
            analysis = MacroAnalysis.from_dict(data)

            # Add thinking to working notes if available
            if thinking_text:
                analysis.working_notes = (
                    "=== EXTENDED THINKING ===\n\n" +
                    thinking_text +
                    "\n\n=== END THINKING ===\n\n" +
                    analysis.working_notes
                )

            # Log results
            self.logger.info(f"Macro analysis complete for Psalm {psalm_number}")
            self.logger.info(f"  Thesis length: {len(analysis.thesis_statement)} chars")
            self.logger.info(f"  Structural divisions: {len(analysis.structural_outline)}")
            self.logger.info(f"  Poetic devices: {len(analysis.poetic_devices)}")
            self.logger.info(f"  Research questions: {len(analysis.research_questions)}")

            return analysis

        except Exception as e:
            self.logger.error(f"Error calling Claude API: {e}")
            self.logger.error(f"Exception type: {type(e).__name__}")
            self.logger.error(f"Model used: {self.model}")
            # If it's an API error, log more details
            if hasattr(e, 'response'):
                self.logger.error(f"API Response: {e.response}")
            if hasattr(e, 'status_code'):
                self.logger.error(f"Status code: {e.status_code}")
            raise

    def _format_psalm_text(self, psalm_text) -> str:
        """
        Format psalm text for prompt.

        Args:
            psalm_text: PsalmText object

        Returns:
            Formatted text with Hebrew and English
        """
        lines = [
            f"### {psalm_text.title_english}",
            f"### {psalm_text.title_hebrew}",
            f"",
            f"**Verse Count**: {psalm_text.verse_count}",
            ""
        ]

        for verse in psalm_text.verses:
            lines.append(f"**Verse {verse.verse}**")
            lines.append(f"Hebrew: {verse.hebrew}")
            lines.append(f"English: {verse.english}")
            lines.append("")

        return "\n".join(lines)

    def analyze_and_save(
        self,
        psalm_number: int,
        output_dir: str = "output",
        save_format: str = "both"
    ) -> MacroAnalysis:
        """
        Analyze psalm and save results to file.

        Args:
            psalm_number: Psalm number (1-150)
            output_dir: Directory to save output files
            save_format: "json", "markdown", or "both"

        Returns:
            MacroAnalysis object
        """
        analysis = self.analyze_psalm(psalm_number)

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save files
        base_name = f"psalm_{psalm_number:03d}_macro"

        if save_format in ["json", "both"]:
            json_path = output_path / f"{base_name}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write(analysis.to_json())
            self.logger.info(f"Saved JSON to {json_path}")

        if save_format in ["markdown", "both"]:
            md_path = output_path / f"{base_name}.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(analysis.to_markdown())
            self.logger.info(f"Saved markdown to {md_path}")

        return analysis

    def close(self):
        """Close database connection."""
        self.db.close()

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close()


def main():
    """Command-line interface for MacroAnalyst agent."""
    import argparse

    # Ensure UTF-8 for Hebrew output on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Generate macro-level analysis for a Psalm (Claude Sonnet 4.5)'
    )
    parser.add_argument('psalm_number', type=int,
                       help='Psalm number (1-150)')
    parser.add_argument('--output-dir', type=str, default='output',
                       help='Output directory for analysis files (default: output)')
    parser.add_argument('--format', type=str, default='both',
                       choices=['json', 'markdown', 'both'],
                       help='Output format (default: both)')
    parser.add_argument('--include-framework', action='store_true',
                       help='Include full analytical framework in prompt (increases token usage)')
    parser.add_argument('--max-tokens', type=int, default=16000,
                       help='Maximum tokens for response (default: 16000)')

    args = parser.parse_args()

    try:
        # Initialize analyst
        with MacroAnalyst() as analyst:
            print(f"Analyzing Psalm {args.psalm_number}...")
            print("This may take 30-60 seconds due to extended thinking mode.\n")

            # Run analysis
            analysis = analyst.analyze_and_save(
                psalm_number=args.psalm_number,
                output_dir=args.output_dir,
                save_format=args.format
            )

            # Display results
            print("=" * 80)
            print(f"MACRO ANALYSIS: PSALM {args.psalm_number}")
            print("=" * 80)
            print()
            print("THESIS:")
            print(analysis.thesis_statement)
            print()
            print(f"GENRE: {analysis.genre}")
            print()
            print(f"STRUCTURAL DIVISIONS: {len(analysis.structural_outline)}")
            for i, div in enumerate(analysis.structural_outline, 1):
                print(f"  {i}. {div.section}: {div.theme}")
            print()
            print(f"POETIC DEVICES: {len(analysis.poetic_devices)}")
            for device in analysis.poetic_devices:
                print(f"  - {device.device}: {device.description[:60]}...")
            print()
            print(f"RESEARCH QUESTIONS: {len(analysis.research_questions)}")
            for i, q in enumerate(analysis.research_questions, 1):
                print(f"  {i}. {q}")
            print()
            print("=" * 80)
            print(f"Analysis saved to {args.output_dir}/")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
