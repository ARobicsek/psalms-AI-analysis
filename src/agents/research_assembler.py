"""
Research Bundle Assembler

Coordinates all librarian agents to assemble comprehensive research bundles.
Processes JSON requests from the Scholar-Researcher agent and returns
structured research data.

Librarian Agents Coordinated:
1. BDB Librarian - Hebrew lexicon entries
2. Concordance Librarian - Word/phrase searches with variations
3. Figurative Language Librarian - Figurative instances with hierarchical tags

Input: JSON research request from Scholar-Researcher
Output: Complete research bundle ready for Scholar-Writer agents
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import json

# Handle imports for both module and script usage
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.agents.bdb_librarian import BDBLibrarian, LexiconRequest, LexiconBundle
    from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest, ConcordanceBundle
    from src.agents.figurative_librarian import FigurativeLibrarian, FigurativeRequest, FigurativeBundle
else:
    from .bdb_librarian import BDBLibrarian, LexiconRequest, LexiconBundle
    from .concordance_librarian import ConcordanceLibrarian, ConcordanceRequest, ConcordanceBundle
    from .figurative_librarian import FigurativeLibrarian, FigurativeRequest, FigurativeBundle


@dataclass
class ResearchRequest:
    """
    A complete research request from the Scholar-Researcher agent.

    This represents all the research materials requested for analyzing
    a particular Psalm or passage.
    """
    psalm_chapter: int
    lexicon_requests: List[LexiconRequest]
    concordance_requests: List[ConcordanceRequest]
    figurative_requests: List[FigurativeRequest]
    notes: Optional[str] = None  # Overall research notes from Scholar

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResearchRequest':
        """Create from dictionary/JSON."""
        return cls(
            psalm_chapter=data['psalm_chapter'],
            lexicon_requests=[
                LexiconRequest.from_dict(r) if isinstance(r, dict) else LexiconRequest(word=r)
                for r in data.get('lexicon', [])
            ],
            concordance_requests=[
                ConcordanceRequest.from_dict(r)
                for r in data.get('concordance', [])
            ],
            figurative_requests=[
                FigurativeRequest.from_dict(r)
                for r in data.get('figurative', [])
            ],
            notes=data.get('notes')
        )


@dataclass
class ResearchBundle:
    """
    Complete research bundle assembled for a Psalm.

    Contains all lexicon entries, concordance searches, and figurative
    language instances requested by the Scholar-Researcher.
    """
    psalm_chapter: int
    lexicon_bundle: Optional[LexiconBundle]
    concordance_bundles: List[ConcordanceBundle]
    figurative_bundles: List[FigurativeBundle]
    request: ResearchRequest

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'psalm_chapter': self.psalm_chapter,
            'lexicon': self.lexicon_bundle.to_dict() if self.lexicon_bundle else None,
            'concordance': [c.to_dict() for c in self.concordance_bundles],
            'figurative': [f.to_dict() for f in self.figurative_bundles],
            'summary': {
                'lexicon_entries': len(self.lexicon_bundle.entries) if self.lexicon_bundle else 0,
                'concordance_searches': len(self.concordance_bundles),
                'concordance_results': sum(len(c.results) for c in self.concordance_bundles),
                'figurative_searches': len(self.figurative_bundles),
                'figurative_instances': sum(len(f.instances) for f in self.figurative_bundles)
            }
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        """
        Convert to Markdown format for LLM consumption.

        This format is optimized for Claude to read and analyze.
        """
        md = f"# Research Bundle for Psalm {self.psalm_chapter}\n\n"

        # Lexicon section
        if self.lexicon_bundle and self.lexicon_bundle.entries:
            md += "## Hebrew Lexicon Entries (BDB)\n\n"
            for entry in self.lexicon_bundle.entries:
                md += f"### {entry.word}\n"
                md += f"**Lexicon**: {entry.lexicon_name}\n"

                # Show disambiguation metadata
                if entry.headword:
                    md += f"**Vocalized**: {entry.headword}  \n"
                if entry.strong_number:
                    md += f"**Strong's**: {entry.strong_number}  \n"
                if entry.transliteration:
                    md += f"**Pronunciation**: {entry.transliteration}  \n"

                md += f"\n{entry.entry_text}\n\n"

                # Show usage examples if found
                if entry.usage_examples:
                    md += f"**Usage examples**: {', '.join(entry.usage_examples[:10])}  \n"
                    if len(entry.usage_examples) > 10:
                        md += f"*...and {len(entry.usage_examples) - 10} more*  \n"
                    md += "\n"

                if entry.url:
                    md += f"[View on Sefaria]({entry.url})\n\n"
                md += "---\n\n"

        # Concordance section
        if self.concordance_bundles:
            md += "## Concordance Searches\n\n"
            for i, bundle in enumerate(self.concordance_bundles, 1):
                md += f"### Search {i}: {bundle.request.query}\n"
                md += f"**Scope**: {bundle.request.scope}  \n"
                md += f"**Level**: {bundle.request.level}  \n"
                md += f"**Variations searched**: {len(bundle.variations_searched)}  \n"
                md += f"**Results**: {len(bundle.results)}  \n\n"

                if bundle.results:
                    md += "#### Top Results:\n\n"
                    for result in bundle.results[:10]:
                        md += f"**{result.reference}**  \n"
                        md += f"Hebrew: {result.hebrew_text}  \n"
                        md += f"English: {result.english_text}  \n"
                        md += f"Matched: *{result.matched_word}* (position {result.word_position})  \n\n"

                    if len(bundle.results) > 10:
                        md += f"*...and {len(bundle.results) - 10} more results*\n\n"

                md += "---\n\n"

        # Figurative language section
        if self.figurative_bundles:
            md += "## Figurative Language Instances\n\n"
            for i, bundle in enumerate(self.figurative_bundles, 1):
                md += f"### Query {i}\n"
                req = bundle.request
                filters = []
                if req.book:
                    filters.append(f"Book: {req.book}")
                if req.chapter:
                    filters.append(f"Chapter: {req.chapter}")
                type_filters = [t for t in ['simile', 'metaphor', 'personification', 'idiom', 'hyperbole', 'metonymy']
                               if getattr(req, t)]
                if type_filters:
                    filters.append(f"Types: {', '.join(type_filters)}")
                if req.target_contains:
                    filters.append(f"Target contains: {req.target_contains}")
                if req.vehicle_contains:
                    filters.append(f"Vehicle contains: {req.vehicle_contains}")

                md += f"**Filters**: {' | '.join(filters)}  \n"
                md += f"**Results**: {len(bundle.instances)}  \n\n"

                if bundle.instances:
                    md += "#### Instances:\n\n"
                    for inst in bundle.instances[:10]:
                        types = ', '.join([t for t in ['simile', 'metaphor', 'personification', 'idiom', 'hyperbole', 'metonymy']
                                          if getattr(inst, f'is_{t}')])
                        md += f"**{inst.reference}** ({types})  \n"
                        md += f"*Figurative phrase*: {inst.figurative_text}  \n\n"

                        # Include full verse context
                        if inst.hebrew_text:
                            md += f"**Full verse (Hebrew)**: {inst.hebrew_text}  \n"
                        if inst.english_text:
                            md += f"**Full verse (English)**: {inst.english_text}  \n\n"

                        if inst.figurative_text_hebrew:
                            md += f"*Hebrew phrase*: {inst.figurative_text_hebrew}  \n"
                        md += f"*Explanation*: {inst.explanation[:200]}...  \n"

                        if inst.target:
                            md += f"*Target*: {' → '.join(inst.target[:3])}  \n"
                        if inst.vehicle:
                            md += f"*Vehicle*: {' → '.join(inst.vehicle[:3])}  \n"
                        if inst.ground:
                            md += f"*Ground*: {' → '.join(inst.ground[:3])}  \n"

                        md += f"*Confidence*: {inst.confidence:.2f}  \n\n"

                    if len(bundle.instances) > 10:
                        md += f"*...and {len(bundle.instances) - 10} more instances*\n\n"

                md += "---\n\n"

        # Summary
        summary = self.to_dict()['summary']
        md += "## Research Summary\n\n"
        md += f"- **Lexicon entries**: {summary['lexicon_entries']}\n"
        md += f"- **Concordance searches**: {summary['concordance_searches']}\n"
        md += f"- **Concordance results**: {summary['concordance_results']}\n"
        md += f"- **Figurative language searches**: {summary['figurative_searches']}\n"
        md += f"- **Figurative instances found**: {summary['figurative_instances']}\n"

        return md


class ResearchAssembler:
    """
    Assembles complete research bundles by coordinating all librarian agents.

    This class serves as the central coordinator that:
    1. Receives JSON research requests from Scholar-Researcher
    2. Dispatches requests to appropriate librarians
    3. Assembles results into structured bundles
    4. Returns formatted research data for Scholar-Writer

    Example:
        >>> assembler = ResearchAssembler()
        >>> request_json = '''
        ... {
        ...   "psalm_chapter": 23,
        ...   "lexicon": [
        ...     {"word": "רעה", "notes": "shepherd verb"},
        ...     {"word": "צדק", "notes": "righteousness"}
        ...   ],
        ...   "concordance": [
        ...     {"query": "רעה", "scope": "Psalms", "level": "consonantal"}
        ...   ],
        ...   "figurative": [
        ...     {"book": "Psalms", "chapter": 23, "metaphor": true}
        ...   ]
        ... }
        ... '''
        >>> bundle = assembler.assemble_from_json(request_json)
        >>> print(bundle.to_markdown())
    """

    def __init__(self):
        """Initialize Research Assembler with all librarian agents."""
        self.bdb_librarian = BDBLibrarian()
        self.concordance_librarian = ConcordanceLibrarian()
        self.figurative_librarian = FigurativeLibrarian()

    def assemble(self, request: ResearchRequest) -> ResearchBundle:
        """
        Assemble research bundle from request.

        Args:
            request: ResearchRequest specifying all research needs

        Returns:
            ResearchBundle with all assembled research data

        Example:
            >>> request = ResearchRequest(
            ...     psalm_chapter=23,
            ...     lexicon_requests=[LexiconRequest("רעה")],
            ...     concordance_requests=[ConcordanceRequest(query="רעה", scope="Psalms")],
            ...     figurative_requests=[FigurativeRequest(book="Psalms", chapter=23, metaphor=True)]
            ... )
            >>> bundle = assembler.assemble(request)
        """
        # Fetch lexicon entries
        lexicon_bundle = None
        if request.lexicon_requests:
            lexicon_bundle = self.bdb_librarian.fetch_multiple(request.lexicon_requests)

        # Fetch concordance results
        concordance_bundles = []
        if request.concordance_requests:
            concordance_bundles = self.concordance_librarian.search_multiple(request.concordance_requests)

        # Fetch figurative language instances
        figurative_bundles = []
        if request.figurative_requests:
            figurative_bundles = self.figurative_librarian.search_multiple(request.figurative_requests)

        return ResearchBundle(
            psalm_chapter=request.psalm_chapter,
            lexicon_bundle=lexicon_bundle,
            concordance_bundles=concordance_bundles,
            figurative_bundles=figurative_bundles,
            request=request
        )

    def assemble_from_json(self, json_str: str) -> ResearchBundle:
        """
        Assemble research bundle from JSON request.

        Args:
            json_str: JSON string with research request

        Returns:
            ResearchBundle with all assembled research data

        Example:
            >>> json_request = '''
            ... {
            ...   "psalm_chapter": 23,
            ...   "lexicon": ["רעה", "צדק"],
            ...   "concordance": [
            ...     {"query": "רעה", "scope": "Psalms"}
            ...   ],
            ...   "figurative": [
            ...     {"book": "Psalms", "chapter": 23, "metaphor": true}
            ...   ]
            ... }
            ... '''
            >>> bundle = assembler.assemble_from_json(json_request)
        """
        data = json.loads(json_str)
        request = ResearchRequest.from_dict(data)
        return self.assemble(request)

    def assemble_from_file(self, filepath: str) -> ResearchBundle:
        """
        Assemble research bundle from JSON file.

        Args:
            filepath: Path to JSON file with research request

        Returns:
            ResearchBundle with all assembled research data
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            json_str = f.read()
        return self.assemble_from_json(json_str)


def main():
    """Command-line interface for Research Assembler."""
    import argparse

    # Ensure UTF-8 for Hebrew output on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Assemble complete research bundles from all librarian agents'
    )
    parser.add_argument('request_file', type=str,
                       help='JSON file with research request')
    parser.add_argument('--output', type=str,
                       help='Output file for results (default: stdout)')
    parser.add_argument('--format', type=str, default='markdown',
                       choices=['json', 'markdown'],
                       help='Output format (default: markdown)')

    args = parser.parse_args()

    try:
        assembler = ResearchAssembler()
        bundle = assembler.assemble_from_file(args.request_file)

        # Generate output
        if args.format == 'json':
            output = bundle.to_json()
        else:  # markdown
            output = bundle.to_markdown()

        # Write or print output
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Research bundle written to {args.output}")
            print(f"\nSummary:")
            summary = bundle.to_dict()['summary']
            print(f"  Lexicon entries: {summary['lexicon_entries']}")
            print(f"  Concordance searches: {summary['concordance_searches']}")
            print(f"  Concordance results: {summary['concordance_results']}")
            print(f"  Figurative instances: {summary['figurative_instances']}")
        else:
            print(output)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
