"""
Scholar-Researcher Agent

Coordinates research requests for biblical commentary generation.
This agent receives a macro overview of a Psalm and generates specific,
justified research requests for the librarian agents.

Model: Claude Haiku 4.5 (cost-effective for pattern recognition)
Input: Macro overview from Pass 1 (chapter-level thesis + structure)
Output: JSON research request with three categories:
  - BDB lexicon requests (5-8 significant Hebrew words)
  - Concordance searches (roots/phrases to track)
  - Figurative language checks (verses with likely metaphors)

The Scholar-Researcher is a coordination agent:
- It doesn't do research itself
- It identifies WHAT needs researching and WHY
- Librarians do the actual data retrieval
- Research Assembler formats the results
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Handle imports for both module and script usage
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.agents.research_assembler import ResearchAssembler, ResearchRequest
    from src.utils.logger import get_logger
else:
    from .research_assembler import ResearchAssembler, ResearchRequest
    from ..utils.logger import get_logger


# System prompt for Scholar-Researcher agent
SCHOLAR_RESEARCHER_PROMPT = """You are a research coordinator for biblical scholarship.

You have read the macro overview of Psalm {psalm_number}:

{macro_overview}

---

Now the chapter will undergo detailed verse-by-verse analysis. Your job is to identify what research data is needed.

Generate specific research requests in the following categories:

1. **BDB LEXICON REQUESTS**
   - Identify ALL significant Hebrew words that deserve lexical investigation across the entire psalm
   - BE COMPREHENSIVE. Request lexicon entries for EVERY theologically, poetically, or semantically significant word
   - For each word, explain WHY it's significant (not just "it appears")
   - Expected volume: Typically 2-4 words per verse, so a 14-verse psalm should have 25-50 requests
   - Include:
     * Theological terms (salvation, trust, fear, waiting, etc.)
     * Action verbs with theological implications (gaze, hide, lift up, stumble, etc.)
     * Metaphorical language (light, rock, fortress, face, etc.)
     * Rare or unusual vocabulary
     * Terms with rich semantic ranges or ambiguous meanings
     * Words where etymology would illuminate theological meaning
   - Examples of GOOD requests:
     * "אֶבְיוֹן" - Central poverty term, appears 3x, key to social justice theme
     * "מָעוֹז" - Military metaphor for divine protection, worth exploring etymology and usage patterns
     * "לַחֲזוֹת" - Mystical seeing/gazing verb, contemplative theology implications
     * "יַסְתִּרֵנִי" - Divine hiding/concealment, theodicy and protection language
     * "יְרוֹמְמֵנִי" - Elevation/exaltation verb, vertical spatial metaphor for divine action
   - Examples of BAD requests (skip these):
     * "אֱלֹהִים" - Generic divine name (unless used in unusual way)
     * "אֶת" - Object marker, grammatical function only
     * "וְ" - Conjunction, no semantic content
     * "בְּ" - Preposition (unless part of significant phrase)

2. **CONCORDANCE SEARCHES**
   - Identify Hebrew roots or phrases (e.g. מָעוֹז־חַ֝יַּ֗י) to trace across biblical corpus
   - What themes or motifs need tracking?
   - Specify search level for each:
     * "consonantal": Find all forms of root (רעה → רֹעִי, רֹעֶה, רָעָה, etc.)
     * "voweled": Distinguish homographs by meaning (אֵל ≠ אֶל)
     * "exact": Find specific form with exact vocalization
   - Specify scope for each:
     * "auto": Let system auto-detect common vs. rare words (RECOMMENDED)
     * "Psalms": Search within Psalms only
     * "Torah": Pentateuch only
     * "Prophets": Nevi'im
     * "Writings": Ketuvim
     * "Tanakh": Entire Hebrew Bible
   - Example: {{"query": "רעה", "level": "consonantal", "scope": "auto", "purpose": "Track shepherd imagery across Psalms to identify thematic connections"}}
   - Be strategic: Don't request concordance searches for every BDB word. Focus on thematic patterns.

3. **FIGURATIVE LANGUAGE CHECKS**
   - Which specific verses likely contain metaphor, simile, personification, metonymy or other figurative language?
   - Understanding how this figuration is used across the biblical corpus can illuminate the psalm's meaning.
   - For each verse, specify:
     * Verse number (integer)
     * Reason for checking this verse
     * **VEHICLE**: What is the comparison/image used? (e.g., "shepherd", "light", "fortress", "rock")
     * **VEHICLE_SYNONYMS**: List 2-4 related terms/synonyms that might appear in the figurative database
       - This helps the Figurative Librarian search effectively
       - Example: If vehicle is "shepherd", synonyms might be ["pastor", "herdsman", "keeper", "guide"]
   - IMPORTANT: DO NOT filter by specific type (metaphor, simile, etc.) - searches are broad and find all figurative instances
   - REMINDER: Figurative language structure:
     * TARGET: What/who the figure is about (e.g., "God's care")
     * VEHICLE: What it's compared to (e.g., "shepherd")
     * GROUND: What quality is described (e.g., "protective guidance")
   - Example: {{"verse": 1, "reason": "Shepherd imagery for divine care", "vehicle": "shepherd", "vehicle_synonyms": ["pastor", "herdsman", "protector"]}}

4. **COMMENTARY REQUESTS (OPTIONAL)**
   - Identify verses that would benefit from classical Jewish commentary (Rashi, Ibn Ezra, Radak)
   - Request commentaries for verses that are:
     * Theologically complex or perplexing
     * Using rare or unusual vocabulary
     * Presenting interpretive challenges
     * Central to the psalm's thesis
   - Be selective: Request commentaries for 2-5 key verses per psalm (not every verse)
   - For each verse, specify:
     * Verse number (integer)
     * Reason for requesting commentary (why this verse is significant/challenging)
   - Example: {{"verse": 4, "reason": "Rare term 'beauty of the LORD' - classical interpretation would illuminate meaning"}}
   - NOTE: Commentaries add significant length to research bundles, so request only for truly significant verses

CRITICAL REQUIREMENTS:
- Be SPECIFIC. Vague requests waste resources and produce generic results.
- Justify EVERY request. "It appears" is not a justification.
- Align requests with macro thesis. Don't request tangential research.
- Be MAXIMALLY COMPREHENSIVE. Request lexicon entries for ALL significant words across the entire psalm.
  * For a 6-verse psalm (like Psalm 23): expect 15-25 BDB requests (2-4 words per verse)
  * For a 14-verse psalm (like Psalm 27): expect 30-50 BDB requests (2-4 words per verse)
  * For a 22-verse psalm: expect 50-80 BDB requests (2-4 words per verse)
  * For a 176-verse psalm (like Psalm 119): expect 350-700 BDB requests (2-4 words per verse)
  * Include ALL: theological terms, action verbs, metaphorical language, rare vocabulary
  * DO NOT be conservative - the Scholar-Writer needs comprehensive data
- Don't over-request concordance searches - be selective, focus on thematic patterns (5-10 searches typical)
- Request figurative checks for ALL verses with likely figurative language
- Use "scope: auto" for smart frequency detection (system will restrict to Psalms for common words, expand to Tanakh for rare words)

IMPORTANT: The Scholar-Writer will analyze EVERY verse in detail. They need lexicon data for ALL significant words, not just a few highlights. When in doubt, include the word.

OUTPUT FORMAT: Return ONLY a valid JSON object with this exact structure:

{{
  "bdb_requests": [
    {{"word": "אוֹר", "reason": "Light as theological salvation metaphor v.1"}},
    {{"word": "יְשָׁעִי", "reason": "Salvation term with military deliverance connotations v.1"}},
    {{"word": "מָעוֹז", "reason": "Stronghold metaphor for divine protection v.1"}},
    {{"word": "חַיַּי", "reason": "Life - relationship to salvation and stronghold v.1"}},
    {{"word": "אִירָא", "reason": "Fear verb - exploring relationship between trust and fear v.1"}},
    {{"word": "אֶפְחָד", "reason": "Dread/anxiety term distinct from אִירָא, semantic nuance v.1"}},
    {{"word": "בִּקְרֹב", "reason": "Drawing near - spatial metaphor for threat approach v.2"}},
    {{"word": "מְרֵעִים", "reason": "Evil-doers specific term beyond generic רַע v.2"}},
    {{"word": "לֶאֱכֹל", "reason": "To eat/devour - predatory violence metaphor v.2"}},
    {{"word": "בָּשָׂר", "reason": "Flesh - literal violence or metaphorical destruction? v.2"}},
    {{"word": "צָרַי", "reason": "Adversaries term with possible legal connotations v.2"}},
    {{"word": "אֹיְבַי", "reason": "Enemies - parallel to צָרַי, semantic overlap/distinction v.2"}},
    {{"word": "כָשְׁלוּ", "reason": "Stumble verb - defeat metaphor v.2"}},
    {{"word": "נָפָלוּ", "reason": "Fall verb - complete defeat imagery v.2"}},
    {{"word": "מַחֲנֶה", "reason": "Military camp imagery escalating threat language v.3"}},
    {{"word": "מִלְחָמָה", "reason": "War terminology showing existential threat v.3"}},
    {{"word": "בוֹטֵחַ", "reason": "Trust/confidence term central to psalm's theology v.3"}},
    {{"word": "אַחַת", "reason": "One thing - theological singularity concept v.4"}},
    {{"word": "שָׁאַלְתִּי", "reason": "Ask/request verb - prayer language v.4"}},
    {{"word": "אֲבַקֵּשׁ", "reason": "Seek verb - intensified seeking parallel to שָׁאַלְתִּי v.4"}},
    {{"word": "שִׁבְתִּי", "reason": "Dwelling verb - permanent residence theology v.4"}},
    {{"word": "לַחֲזוֹת", "reason": "To gaze/behold - mystical contemplative vision of God v.4"}},
    {{"word": "נֹעַם", "reason": "Beauty/pleasantness rare divine attribute term v.4"}},
    {{"word": "בַּקֵּר", "reason": "Inquire/visit temple vocabulary with seeking connotations v.4"}},
    {{"word": "הֵיכָל", "reason": "Temple/palace term architectural-theological implications v.4"}},
    {{"word": "יִצְפְּנֵנִי", "reason": "Hide me verb - divine concealment protection v.5"}},
    {{"word": "סֻכָּה", "reason": "Booth/pavilion temporary shelter with ritual overtones v.5"}},
    {{"word": "יוֹם רָעָה", "reason": "Day of evil - eschatological/crisis terminology v.5"}},
    {{"word": "יַסְתִּרֵנִי", "reason": "Conceal me - double protection verb with יִצְפְּנֵנִי v.5"}},
    {{"word": "אֹהֶל", "reason": "Tent - nomadic dwelling imagery for divine presence v.5"}},
    {{"word": "צוּר", "reason": "Rock divine epithet with geological metaphor v.5"}},
    {{"word": "יְרוֹמְמֵנִי", "reason": "Lift me up - elevation/exaltation spatial metaphor v.5"}},
    ... (continue through v.6-14: רֹאשִׁי, תְרוּעָה, זֶבַח, שְׁמַע, חָנֵּנִי, פָּנֶיךָ, etc.)
  ],
  "concordance_searches": [
    {{"query": "מָעוֹז", "level": "consonantal", "scope": "auto", "purpose": "Track divine protection fortress metaphor"}},
    {{"query": "נֹעַם יְהוָה", "level": "exact", "scope": "Tanakh", "purpose": "Rare beauty of LORD phrase"}},
    {{"query": "אַל־תַּסְתֵּר פָּנֶיךָ", "level": "exact", "scope": "Psalms", "purpose": "Hiding face lament formula"}}
  ],
  "figurative_checks": [
    {{"verse": 1, "reason": "Light as salvation, stronghold as protection", "vehicle": "light", "vehicle_synonyms": ["lamp", "sun", "illumination", "brightness"]}},
    {{"verse": 1, "reason": "Fortress/stronghold as divine protection", "vehicle": "fortress", "vehicle_synonyms": ["stronghold", "citadel", "refuge", "fortification"]}},
    {{"verse": 2, "reason": "Flesh-devouring as destruction imagery", "vehicle": "predator", "vehicle_synonyms": ["beast", "devourer", "consumer", "enemy"]}},
    {{"verse": 5, "reason": "Pavilion/booth as divine shelter", "vehicle": "pavilion", "vehicle_synonyms": ["tent", "booth", "tabernacle", "shelter"]}},
    {{"verse": 5, "reason": "Rock as divine stability", "vehicle": "rock", "vehicle_synonyms": ["stone", "cliff", "mountain", "foundation"]}},
    ... (check ALL verses with figurative language)
  ],
  "commentary_requests": [
    {{"verse": 4, "reason": "Rare term 'beauty of the LORD' - need classical interpretation"}},
    {{"verse": 7, "reason": "Complex request 'hear my voice' with theological implications"}},
    ... (2-5 key verses maximum)
  ]
}}

IMPORTANT: The example above shows the DENSITY of requests expected. For a 14-verse psalm, expect 30-50 BDB requests covering most significant theological, poetic, and thematic terms. Do not be conservative - request research for ALL words that could illuminate the psalm's meaning.

REMINDER: Your job is to request research for the Scholar-Writer who will write verse-by-verse commentary. They need lexicon data for EVERY significant word to write thorough analysis. If you request too few words, the Scholar-Writer will lack the data needed for deep commentary. Always err on the side of MORE requests rather than fewer.

Do not include any text before or after the JSON object. Return ONLY the JSON."""


@dataclass
class ScholarResearchRequest:
    """
    Complete research request generated by Scholar-Researcher agent.

    This is the raw output from the LLM before being converted to
    ResearchRequest format for the Research Assembler.
    """
    bdb_requests: List[Dict[str, str]]  # [{"word": "...", "reason": "..."}]
    concordance_searches: List[Dict[str, str]]  # [{"query": "...", "level": "...", "scope": "...", "purpose": "..."}]
    figurative_checks: List[Dict[str, Any]]  # [{"verse": 1, "reason": "...", "vehicle": "...", "vehicle_synonyms": [...]}]
    commentary_requests: List[Dict[str, Any]] = None  # [{"verse": 1, "reason": "..."}] - Optional

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScholarResearchRequest':
        """Create from dictionary/JSON."""
        # Post-processing: ensure alternates field is always present
        concordance_searches = data.get('concordance_searches', [])
        for req in concordance_searches:
            if 'alternates' not in req and 'alternate_queries' not in req:
                req['alternates'] = []  # Guarantee field presence even if LLM didn't provide it

        return cls(
            bdb_requests=data.get('bdb_requests', []),
            concordance_searches=concordance_searches,
            figurative_checks=data.get('figurative_checks', []),
            commentary_requests=data.get('commentary_requests', [])
        )

    def to_research_request(self, psalm_chapter: int, logger=None) -> Dict[str, Any]:
        """
        Convert to ResearchRequest format for Research Assembler.

        Args:
            psalm_chapter: Psalm chapter number
            logger: Optional logger for debug output

        Returns:
            Dictionary in ResearchRequest.from_dict() format
        """
        # Convert BDB requests
        lexicon_requests = [
            {"word": req["word"], "notes": req.get("reason", "")}
            for req in self.bdb_requests
        ]

        # Convert concordance searches
        concordance_requests = []
        for idx, req in enumerate(self.concordance_searches):
            conc_req = {
                "query": req["query"],
                "scope": req.get("scope", "auto"),
                "level": req.get("level", "consonantal"),
                "notes": req.get("purpose", "")
            }
            # Add alternates if present (support both field names)
            alternates = req.get("alternates") or req.get("alternate_queries")

            # DEBUG: Log what we're seeing
            if logger:
                logger.debug(f"Concordance request {idx+1}: query='{req['query']}'")
                logger.debug(f"  Has 'alternates' key: {'alternates' in req}")
                logger.debug(f"  Has 'alternate_queries' key: {'alternate_queries' in req}")
                if alternates:
                    logger.info(f"  ✓ Alternates found for '{req['query']}': {alternates}")
                    conc_req["alternates"] = alternates
                else:
                    logger.warning(f"  ✗ NO ALTERNATES PROVIDED BY LLM for '{req['query']}'")

            concordance_requests.append(conc_req)

        # Convert figurative checks
        figurative_requests = []
        for check in self.figurative_checks:
            verse = check.get("verse")
            vehicle = check.get("vehicle", "")
            vehicle_synonyms = check.get("vehicle_synonyms", [])
            scope = check.get("scope", "Psalms")  # Default to Psalms only if not specified

            # Build request dict based on scope
            req = {}

            # Parse scope to determine which books to search
            # NOTE: Our database only contains Psalms + Pentateuch + Proverbs, so we don't support
            # searching the entire Tanakh even if requested
            if scope == "Psalms+Pentateuch" or scope == "Pentateuch+Psalms" or scope == "Tanakh":
                # Search across Psalms, Pentateuch books, and Proverbs (our entire database)
                req["books"] = ["Psalms", "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Proverbs"]
            elif scope == "Psalms":
                # Search only Psalms
                req["book"] = "Psalms"
            else:
                # Unknown scope - default to searching entire database
                req["books"] = ["Psalms", "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]

            # NOTE: We do NOT filter by figurative type (metaphor, simile, etc.)
            # This was too restrictive. We let the search be broad and find all
            # figurative instances, then filter by vehicle if specified.

            # Add vehicle search if specified
            if vehicle:
                req["vehicle_contains"] = vehicle

            # Add vehicle synonyms for broader searching
            if vehicle_synonyms:
                # Combine vehicle + synonyms for comprehensive search
                all_vehicles = [vehicle] + vehicle_synonyms if vehicle else vehicle_synonyms
                # Store as LIST (not string) for FigurativeRequest
                req["vehicle_search_terms"] = all_vehicles

            # Add notes
            notes_parts = []
            if "reason" in check:
                notes_parts.append(check["reason"])
            if vehicle:
                notes_parts.append(f"Vehicle: {vehicle}")
            if vehicle_synonyms:
                notes_parts.append(f"Related terms: {', '.join(vehicle_synonyms)}")

            if notes_parts:
                req["notes"] = " | ".join(notes_parts)

            figurative_requests.append(req)

        # Convert commentary requests
        commentary_reqs = []
        if self.commentary_requests:
            for req in self.commentary_requests:
                psalm = req.get("psalm", psalm_chapter)  # Default to current psalm
                verse = req.get("verse")
                reason = req.get("reason", "Requested by Scholar-Researcher")

                if verse:
                    commentary_reqs.append({
                        "psalm": psalm,
                        "verse": verse,
                        "reason": reason
                    })

        return {
            "psalm_chapter": psalm_chapter,
            "lexicon": lexicon_requests,
            "concordance": concordance_requests,
            "figurative": figurative_requests,
            "commentary": commentary_reqs
        }


class ScholarResearcher:
    """
    Scholar-Researcher Agent using Claude Haiku 4.5.

    This agent analyzes a macro overview of a Psalm and generates
    specific, justified research requests for the librarian agents.

    Example:
        >>> researcher = ScholarResearcher(api_key="your-key")
        >>> macro_overview = '''
        ... Psalm 23 is a trust psalm that depicts God's care through
        ... shepherd imagery. The psalmist moves from trust (vv.1-4)
        ... to celebration (vv.5-6), using pastoral and banquet metaphors.
        ... '''
        >>> request = researcher.generate_research_request(
        ...     psalm_number=23,
        ...     macro_overview=macro_overview
        ... )
        >>> print(request.to_json())
    """

    def __init__(self, api_key: Optional[str] = None, logger=None):
        """
        Initialize Scholar-Researcher agent.

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            logger: Logger instance (or will create default)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required (pass api_key or set ANTHROPIC_API_KEY)")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-haiku-20241022"  # Haiku 3.5 (latest available)
        self.logger = logger or get_logger("scholar_researcher")

    def generate_research_request(
        self,
        psalm_number: int,
        macro_overview: str,
        max_tokens: int = 8192
    ) -> ScholarResearchRequest:
        """
        Generate research request from macro overview.

        Args:
            psalm_number: Psalm chapter number
            macro_overview: Macro analysis from Pass 1
            max_tokens: Maximum tokens for response (default 8192, the max for Haiku 3.5)

        Returns:
            ScholarResearchRequest with BDB, concordance, and figurative checks

        Raises:
            ValueError: If JSON parsing fails or response invalid
        """
        # Format prompt
        prompt = SCHOLAR_RESEARCHER_PROMPT.format(
            psalm_number=psalm_number,
            macro_overview=macro_overview
        )

        self.logger.log_research_request(
            psalm_chapter=psalm_number,
            request={"macro_overview_length": len(macro_overview)}
        )

        # Call Claude Haiku 4.5
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract JSON from response
            response_text = response.content[0].text.strip()

            # Log API call
            self.logger.log_api_call(
                api_name="Anthropic Claude",
                endpoint=self.model,
                status_code=200,
                response_time_ms=0  # Not available in SDK
            )

            # Parse JSON
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
                raise ValueError(f"Invalid JSON from Scholar-Researcher: {e}")

            # Create request object
            request = ScholarResearchRequest.from_dict(data)

            # Log results
            self.logger.info(f"Generated research request for Psalm {psalm_number}")
            self.logger.info(f"  BDB requests: {len(request.bdb_requests)}")
            self.logger.info(f"  Concordance searches: {len(request.concordance_searches)}")
            self.logger.info(f"  Figurative checks: {len(request.figurative_checks)}")

            return request

        except Exception as e:
            self.logger.error(f"Error calling Claude API: {e}")
            raise

    def generate_and_assemble(
        self,
        psalm_number: int,
        macro_overview: str
    ) -> tuple[ScholarResearchRequest, Any]:
        """
        Generate research request AND assemble research bundle.

        This is the full pipeline: macro overview → research request → research bundle.

        Args:
            psalm_number: Psalm chapter number
            macro_overview: Macro analysis from Pass 1

        Returns:
            Tuple of (ScholarResearchRequest, ResearchBundle)
        """
        # Generate research request
        scholar_request = self.generate_research_request(psalm_number, macro_overview)

        # Convert to ResearchRequest format
        request_dict = scholar_request.to_research_request(psalm_number, logger=self.logger)

        # Assemble research bundle
        assembler = ResearchAssembler()
        research_request = ResearchRequest.from_dict(request_dict)
        bundle = assembler.assemble(research_request)

        self.logger.info(f"Assembled research bundle for Psalm {psalm_number}")
        summary = bundle.to_dict()['summary']
        self.logger.info(f"  Lexicon entries: {summary['lexicon_entries']}")
        self.logger.info(f"  Concordance results: {summary['concordance_results']}")
        self.logger.info(f"  Figurative instances: {summary['figurative_instances']}")

        return scholar_request, bundle


def main():
    """Command-line interface for Scholar-Researcher agent."""
    import argparse

    # Ensure UTF-8 for Hebrew output on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Generate research requests from macro overview (Claude Haiku 4.5)'
    )
    parser.add_argument('psalm_number', type=int,
                       help='Psalm chapter number')
    parser.add_argument('macro_overview', type=str,
                       help='Path to macro overview text file OR macro overview text')
    parser.add_argument('--output', type=str,
                       help='Output file for research request JSON (default: stdout)')
    parser.add_argument('--assemble', action='store_true',
                       help='Also assemble research bundle using librarians')
    parser.add_argument('--bundle-output', type=str,
                       help='Output file for research bundle (markdown format)')

    args = parser.parse_args()

    # Read macro overview
    if Path(args.macro_overview).exists():
        with open(args.macro_overview, 'r', encoding='utf-8') as f:
            macro_overview = f.read()
    else:
        macro_overview = args.macro_overview

    try:
        # Initialize agent
        researcher = ScholarResearcher()

        if args.assemble:
            # Full pipeline
            scholar_request, bundle = researcher.generate_and_assemble(
                psalm_number=args.psalm_number,
                macro_overview=macro_overview
            )

            # Output research request
            request_json = scholar_request.to_json()
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(request_json)
                print(f"Research request written to {args.output}")
            else:
                print("=== RESEARCH REQUEST ===")
                print(request_json)

            # Output research bundle
            bundle_md = bundle.to_markdown()
            if args.bundle_output:
                with open(args.bundle_output, 'w', encoding='utf-8') as f:
                    f.write(bundle_md)
                print(f"Research bundle written to {args.bundle_output}")
            else:
                print("\n=== RESEARCH BUNDLE ===")
                print(bundle_md)

        else:
            # Just generate research request
            request = researcher.generate_research_request(
                psalm_number=args.psalm_number,
                macro_overview=macro_overview
            )

            output_json = request.to_json()

            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output_json)
                print(f"Research request written to {args.output}")
            else:
                print(output_json)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
