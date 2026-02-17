"""
Insight Extractor Agent
Phase 2b: Intermediate filtering step between Analysis and Synthesis

This agent acts as a CURATOR, filtering the massive volume of research data
to identify only the "transformative" insights—the ones that change how
a reader understands the text.

It prevents the Synthesis Writer from getting overwhelmed and defaulting to summary.

Model: Claude Opus 4.6 (high reasoning)
Input: MicroAnalysis + ResearchBundle + Psalm Text
Output: JSON with prioritized psalm-level and verse-level insights

Author: Claude (Anthropic)
Date: 2026-01-26
"""

import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Handle imports for both module and script usage
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.schemas.analysis_schemas import MicroAnalysis
    from src.utils.logger import get_logger
    from src.utils.cost_tracker import CostTracker
else:
    from ..schemas.analysis_schemas import MicroAnalysis
    from ..utils.logger import get_logger
    from ..utils.cost_tracker import CostTracker


# =============================================================================
# INSIGHT EXTRACTOR PROMPT
# =============================================================================

INSIGHT_EXTRACTOR_PROMPT = """You are an Insight Curator for biblical commentary on Psalm {psalm_number}.

Your job is to FILTER, not to write. You will receive extensive research materials. Most of this material is useful background but not transformative. 

**Your task:** Identify ONLY the insights that would make a thoughtful reader say "I never saw it that way."

## WHAT COUNTS AS A HIGH-VALUE INSIGHT

1. **Reading-changers:** A Hebrew nuance that fundamentally alters meaning (not just adds color)
2. **Puzzle-solvers:** Something that explains why the text says X instead of the expected Y
3. **Productive ambiguities:** Cases where the text deliberately sustains multiple readings
4. **Surprising parallels:** Connections to other texts that create unexpected meaning
5. **Commentator gems:** Traditional interpretations that are genuinely illuminating (not just pious)
6. **Liturgical insights:** Insights that reveal why the psalm or its elements are used in the way they are liturgically
7. **Historical insights:** Insights about sitz-im-leben or polemical use of the psalm, or interesting facts about the afterlife or reception history of the psalm or its elements
8. **Poetic insights:** Illuminating insights about poetic devices and figurative language that will enhance the reader's appreciation of the psalm as a literary work
9. **Historical & Cultural points of interest**: Insights gained by examining the adoption of the psalm or elements of its content in later historical cotexts (e.g. Continental congress, American natives, German leider, R&B music, etc.)
10. **Cross-cultural literary echoes**: Connections between this psalm's imagery, structure, or emotional logic and works from world literature — Shakespeare, Homer, Rumi, Li Bai, Dickinson, Neruda, political speeches, folk traditions. Focus on cases where the comparison illuminates the psalm: a shared metaphor used differently, a parallel emotional arc, a contrasting approach to the same human experience. Do NOT force connections — only flag comparisons where the juxtaposition genuinely deepens understanding of the psalm's craft or meaning.

## WHAT DOES NOT COUNT

- Etymology that doesn't change interpretation
- Parallels that merely confirm what we already see
- "Interesting" facts that don't alter reading
- Standard grammatical observations
- Consensus scholarly views that are already obvious

## YOUR INPUTS

### PSALM TEXT
{psalm_text}

### MACRO ANALYSIS (structural analysis)
{macro_analysis}

### MICRO ANALYSIS (verse discoveries)
{micro_analysis}

### RESEARCH BUNDLE (lexicon, concordance, commentaries, etc.)
{research_bundle}

## YOUR OUTPUT

Return a JSON object with this structure:

```json
{{
  "psalm_level_insights": [
    {{
      "insight": "[One sentence describing the transformative observation]",
      "evidence": "[Source: BDB, Rashi, concordance pattern, etc.]",
      "affects_verses": [list of verse numbers this insight illuminates],
      "why_it_matters": "[One sentence on interpretive payoff]"
    }}
  ],
  "verse_insights": {{
    "1": "[Single most important crux for this verse, or 'STANDARD' if nothing remarkable]",
    "2": "[...]",
    ...
  }}
}}
```

## CRITICAL INSTRUCTIONS

1. **Be ruthless.** If an observation is merely "interesting" but doesn't change how the verse reads, DO NOT include it.
2. **Quality over quantity.** 3 transformative insights beat 10 mild ones.
3. **Psalm-level insights:** Maximum 5. These are the "big ideas" that organize the whole psalm.
4. **Verse insights:** Maximum 1 per verse. If a verse has only standard content, mark it "STANDARD" — this is useful information (tells the writer not to pad that verse).
5. **Be specific.** "The water-drawing verb changes the rescue metaphor" is good. "Interesting vocabulary" is useless.

Return ONLY the JSON object. No preamble or explanation.
"""


class InsightExtractor:
    """
    Phase 2b: Insight Extractor Agent.
    
    Filters research materials to identifying transformative insights.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        logger=None,
        cost_tracker: Optional[CostTracker] = None
    ):
        """
        Initialize InsightExtractor agent.

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            logger: Logger instance (or will create default)
            cost_tracker: CostTracker instance
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required (pass api_key or set ANTHROPIC_API_KEY)")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-opus-4-6"  # High reasoning model
        self.logger = logger or get_logger("insight_extractor")
        self.cost_tracker = cost_tracker or CostTracker()
        
        self.logger.info(f"InsightExtractor initialized with model {self.model}")

    def extract_insights(
        self,
        psalm_number: int,
        psalm_text: str,
        micro_analysis: MicroAnalysis,
        macro_analysis: Dict,
        research_bundle: str,
        max_tokens: int = 4000
    ) -> Dict[str, Any]:
        """
        Extract high-value insights from research materials.

        Args:
            psalm_number: Psalm number
            psalm_text: Full text of the psalm
            micro_analysis: MicroAnalysis object
            macro_analysis: Macro analysis dictionary
            research_bundle: Full research bundle text
            max_tokens: Max output tokens

        Returns:
            JSON dictionary with prioritized insights
        """
        self.logger.info(f"Extracting insights for Psalm {psalm_number}")
        
        # Prepare inputs
        micro_markdown = micro_analysis.to_markdown() if hasattr(micro_analysis, 'to_markdown') else str(micro_analysis)
        
        # Helper to safely get values from macro_analysis (which might be dict or object)
        def get_macro_val(key, default='N/A'):
            if isinstance(macro_analysis, dict):
                return macro_analysis.get(key, default)
            return getattr(macro_analysis, key, default)

        # Format macro analysis
        macro_lines = []
        macro_lines.append(f"**Thesis:** {get_macro_val('thesis_statement')}")
        macro_lines.append(f"**Genre:** {get_macro_val('genre')}")
        
        # Handle structural outline which might be nested list of objects or dicts
        structure = get_macro_val('structural_outline', [])
        if structure:
            macro_lines.append("\n**Structure:**")
            for div in structure:
                # Handle division item which might be dict or object
                if isinstance(div, dict):
                    sec = div.get('section', '')
                    theme = div.get('theme', '')
                else:
                    sec = getattr(div, 'section', '')
                    theme = getattr(div, 'theme', '')
                macro_lines.append(f"  - {sec}: {theme}")
        
        macro_markdown = "\n".join(macro_lines)
        
        # Construct prompt
        prompt = INSIGHT_EXTRACTOR_PROMPT.format(
            psalm_number=psalm_number,
            psalm_text=psalm_text,
            micro_analysis=micro_markdown,
            macro_analysis=macro_markdown,
            research_bundle=research_bundle
        )
        
        self.logger.info(f"  Input size: {len(prompt)} chars")
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.0,  # Strict adherence to instructions
                system="You are a rigorous scholarly editor who hates fluff. Your goal is to identify only the observations that genuinely transform understanding.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Track cost
            if hasattr(response, 'usage'):
                self.cost_tracker.add_usage(
                    model=self.model,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens
                )
            
            # Extract content
            content = response.content[0].text
            
            # Parse JSON
            try:
                # Find JSON block if wrapped in markdown
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                insights = json.loads(content)
                
                num_psalm_insights = len(insights.get('psalm_level_insights', []))
                num_verse_insights = len([v for k, v in insights.get('verse_insights', {}).items() if v != 'STANDARD'])
                
                self.logger.info(f"  ✓ Extraction complete: {num_psalm_insights} psalm insights, {num_verse_insights} verse insights found")
                
                return insights
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {e}")
                self.logger.debug(f"Raw response: {content[:500]}...")
                # Return empty structure on failure
                return {
                    "psalm_level_insights": [],
                    "verse_insights": {},
                    "error": "JSON parse failed"
                }
                
        except Exception as e:
            self.logger.error(f"LLM extraction failed: {e}")
            raise

    def save_insights(self, insights: Dict[str, Any], output_path: Path):
        """Save extracted insights to JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(insights, f, ensure_ascii=False, indent=2)
        self.logger.info(f"Saved insights to {output_path}")
