"""
Question Curator - Generates "Questions for the Reader" from macro/micro analysis

This module extracts research questions from MacroAnalysis and "interesting questions"
from MicroAnalysis, then uses an LLM to curate 4-6 engaging, scholarly questions
designed to prime readers before they read the commentary.

The questions should be:
- Grounded in specific textual observations
- Thought-provoking but accessible
- Diverse (covering structure, language, theology, reception)
- Addressed somewhere in the introduction or verse commentary

Author: Claude (Anthropic)
Date: 2026-01-05
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Handle imports for both module and script usage
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.utils.logger import get_logger
    from src.utils.cost_tracker import CostTracker
else:
    from ..utils.logger import get_logger
    from ..utils.cost_tracker import CostTracker


# Prompt for LLM-assisted curation
CURATION_PROMPT = """You are curating "Questions for the Reader" to appear before a scholarly commentary on Psalm {psalm_number}.

These questions prime readers to engage deeply with the psalm BEFORE reading the commentary.
The commentary will address these questions, so readers can appreciate the insights more fully.

## Source Questions from Analysis

### From Macro-Level Analysis (structural/thematic questions):
{macro_questions}

### From Micro-Level Analysis (verse-level discoveries):
{micro_questions}

## Your Task

Select and adapt 4-6 questions that will:
1. **Prime curiosity** - Make readers want to look carefully at the psalm
2. **Span different aspects** - Structure, language, theological puzzles, reception
3. **Be specific to THIS psalm** - Not generic "what is the main theme?" questions
4. **Use engaging scholarly style** - Accessible but intellectually serious

## Transformation Guidelines

- Convert scholarly phrasing to inviting phrasing where helpful
- Keep Hebrew terms (with English) when they add specificity
- Add verse references when questions focus on specific passages
- Ensure questions can be answered by careful reading + the commentary

## Output Format

Return ONLY a JSON array of 4-6 question strings. Example:
[
    "The psalm opens with 'El' but switches to 'YHWH' in verse 8. Why might the poet change divine names?",
    "Verse 4 says the heavens 'speak' but have 'no words.' Is this a contradiction or something deeper?",
    "The sun is compared to both a 'bridegroom' and a 'warrior' (v. 6). What do these images together suggest?",
    "After celebrating Torah's perfection (vv. 8-10), why does the psalmist confess to 'hidden faults' (v. 13)?",
    "The final verse offers 'words of my mouth' as a kind of sacrifice (v. 15). What does it mean to offer speech to God?"
]

Return ONLY the JSON array, no additional text.
"""


class QuestionCurator:
    """
    Curates "Questions for the Reader" from macro/micro analysis outputs.
    
    Uses Gemini Flash for cost-effective LLM-assisted curation.
    """
    
    def __init__(
        self,
        logger=None,
        cost_tracker: Optional[CostTracker] = None
    ):
        """
        Initialize QuestionCurator.
        
        Args:
            logger: Logger instance
            cost_tracker: CostTracker instance for tracking API costs
        """
        self.logger = logger or get_logger("question_curator")
        self.cost_tracker = cost_tracker or CostTracker()
        
        # Initialize Gemini client
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.gemini_api_key:
            self.logger.warning("No Gemini API key found. Question curation will use fallback extraction.")
            self.client = None
        else:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                self.client = genai.GenerativeModel("gemini-2.0-flash")
                self.logger.info("QuestionCurator initialized with Gemini Flash")
            except ImportError:
                self.logger.warning("google-generativeai not installed. Using fallback extraction.")
                self.client = None
    
    def curate_questions(
        self,
        psalm_number: int,
        macro_file: Path,
        micro_file: Path,
        num_questions: int = 5
    ) -> Tuple[List[str], Dict[str, List[str]]]:
        """
        Curate reader questions from macro/micro analysis files.
        
        Args:
            psalm_number: Psalm number
            macro_file: Path to macro analysis JSON
            micro_file: Path to micro analysis JSON
            num_questions: Target number of questions (4-6)
            
        Returns:
            Tuple of:
            - List of curated question strings
            - Dict with 'macro_source' and 'micro_source' lists (original questions)
        """
        self.logger.info(f"Curating questions for Psalm {psalm_number}")
        
        # Extract source questions
        macro_questions = self._extract_macro_questions(macro_file)
        micro_questions = self._extract_micro_questions(micro_file)
        
        source_questions = {
            'macro_source': macro_questions,
            'micro_source': micro_questions
        }
        
        self.logger.info(f"  Found {len(macro_questions)} macro questions, {len(micro_questions)} micro questions")
        
        # If no LLM available, use simple extraction
        if not self.client:
            curated = self._fallback_extraction(macro_questions, micro_questions, num_questions)
            return curated, source_questions
        
        # Use LLM to curate
        try:
            curated = self._llm_curate(psalm_number, macro_questions, micro_questions, num_questions)
            return curated, source_questions
        except Exception as e:
            self.logger.warning(f"LLM curation failed, using fallback: {e}")
            curated = self._fallback_extraction(macro_questions, micro_questions, num_questions)
            return curated, source_questions
    
    def _extract_macro_questions(self, macro_file: Path) -> List[str]:
        """Extract research_questions from macro analysis JSON."""
        if not macro_file.exists():
            self.logger.warning(f"Macro file not found: {macro_file}")
            return []
        
        try:
            with open(macro_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('research_questions', [])
        except Exception as e:
            self.logger.error(f"Error reading macro file: {e}")
            return []
    
    def _extract_micro_questions(self, micro_file: Path) -> List[str]:
        """Extract interesting_questions from micro analysis JSON."""
        if not micro_file.exists():
            self.logger.warning(f"Micro file not found: {micro_file}")
            return []
        
        try:
            with open(micro_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('interesting_questions', [])
        except Exception as e:
            self.logger.error(f"Error reading micro file: {e}")
            return []
    
    def _llm_curate(
        self,
        psalm_number: int,
        macro_questions: List[str],
        micro_questions: List[str],
        num_questions: int
    ) -> List[str]:
        """Use Gemini Flash to curate questions."""
        self.logger.info("  Using Gemini Flash for question curation")
        
        # Format questions for prompt
        macro_formatted = "\n".join(f"- {q}" for q in macro_questions) if macro_questions else "(none available)"
        micro_formatted = "\n".join(f"- {q}" for q in micro_questions) if micro_questions else "(none available)"
        
        prompt = CURATION_PROMPT.format(
            psalm_number=psalm_number,
            macro_questions=macro_formatted,
            micro_questions=micro_formatted
        )
        
        # Call Gemini Flash
        response = self.client.generate_content(prompt)
        
        # Track usage
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            self.cost_tracker.add_usage(
                model="gemini-2.0-flash",
                input_tokens=getattr(usage, 'prompt_token_count', 0),
                output_tokens=getattr(usage, 'candidates_token_count', 0)
            )
        
        # Parse response
        response_text = response.text.strip()
        
        # Clean up response if wrapped in markdown
        if response_text.startswith("```"):
            lines = response_text.split('\n')
            json_lines = []
            in_json = False
            for line in lines:
                if line.startswith("```"):
                    if in_json:
                        break
                    in_json = True
                    continue
                if in_json:
                    json_lines.append(line)
            response_text = '\n'.join(json_lines)
        
        questions = json.loads(response_text)
        
        if not isinstance(questions, list):
            raise ValueError("Expected list of questions from LLM")
        
        self.logger.info(f"  ✓ LLM curated {len(questions)} questions")
        return questions[:num_questions + 1]  # Allow up to 6
    
    def _fallback_extraction(
        self,
        macro_questions: List[str],
        micro_questions: List[str],
        num_questions: int
    ) -> List[str]:
        """Simple extraction without LLM - take first N questions alternating sources."""
        self.logger.info("  Using fallback extraction (no LLM)")
        
        result = []
        macro_idx = 0
        micro_idx = 0
        
        while len(result) < num_questions:
            # Alternate between macro and micro
            if macro_idx < len(macro_questions) and (len(result) % 2 == 0 or micro_idx >= len(micro_questions)):
                result.append(macro_questions[macro_idx])
                macro_idx += 1
            elif micro_idx < len(micro_questions):
                result.append(micro_questions[micro_idx])
                micro_idx += 1
            else:
                break
        
        return result
    
    def format_for_markdown(self, questions: List[str]) -> str:
        """Format curated questions as markdown for output."""
        if not questions:
            return ""
        
        lines = ["## Questions for the Reader\n"]
        lines.append("*Before reading this commentary, consider the following questions:*\n")
        
        for i, q in enumerate(questions, 1):
            lines.append(f"{i}. {q}\n")
        
        lines.append("\n---\n")
        return "\n".join(lines)
    
    def save_questions(
        self,
        questions: List[str],
        source_questions: Dict[str, List[str]],
        output_path: Path,
        psalm_number: int
    ) -> Path:
        """
        Save curated questions to JSON file.
        
        Args:
            questions: Curated question list
            source_questions: Dict with macro_source and micro_source lists
            output_path: Output directory
            psalm_number: Psalm number
            
        Returns:
            Path to saved JSON file
        """
        output_file = output_path / f"psalm_{psalm_number:03d}_reader_questions.json"
        
        data = {
            'psalm_number': psalm_number,
            'curated_questions': questions,
            'source_questions': source_questions
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"  ✓ Saved questions to {output_file}")
        return output_file


# CLI for testing
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Curate reader questions for a psalm')
    parser.add_argument('psalm_number', type=int, help='Psalm number')
    parser.add_argument('--output-dir', type=str, default='output', help='Output directory')
    
    args = parser.parse_args()
    
    output_path = Path(args.output_dir) / f"psalm_{args.psalm_number}"
    macro_file = output_path / f"psalm_{args.psalm_number:03d}_macro.json"
    micro_file = output_path / f"psalm_{args.psalm_number:03d}_micro_v2.json"
    
    curator = QuestionCurator()
    questions, sources = curator.curate_questions(args.psalm_number, macro_file, micro_file)
    
    print("\n=== Curated Questions ===\n")
    for i, q in enumerate(questions, 1):
        print(f"{i}. {q}\n")
    
    # Save
    curator.save_questions(questions, sources, output_path, args.psalm_number)
