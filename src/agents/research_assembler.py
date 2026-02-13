"""
Research Bundle Assembler

Coordinates all librarian agents to assemble comprehensive research bundles.
Processes JSON requests from the Scholar-Researcher agent and returns
structured research data.

Librarian Agents Coordinated:
1. BDB Librarian - Hebrew lexicon entries
2. Concordance Librarian - Word/phrase searches with variations
3. Figurative Language Librarian - Figurative instances with hierarchical tags
4. Commentary Librarian - Traditional Jewish commentaries (Rashi, Ibn Ezra, Radak, Metzudat David, Malbim, Meiri)
5. Liturgical Librarian - Psalms→Liturgy cross-references from Sefaria (Phase 0 bootstrap)
6. Sacks Librarian - Rabbi Jonathan Sacks' references to Psalms from his collected works
7. Sacks Librarian - Rabbi Jonathan Sacks' references to Psalms from his collected works

Input: JSON research request from Scholar-Researcher
Output: Complete research bundle ready for Scholar-Writer agents
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import json
import random

# Handle imports for both module and script usage
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.agents.bdb_librarian import BDBLibrarian, LexiconRequest, LexiconBundle
    from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest, ConcordanceBundle
    from src.agents.figurative_librarian import FigurativeLibrarian, FigurativeRequest, FigurativeBundle
    from src.agents.commentary_librarian import CommentaryLibrarian, CommentaryBundle
    from src.agents.liturgical_librarian_sefaria import SefariaLiturgicalLibrarian, SefariaLiturgicalLink
    from src.agents.liturgical_librarian import LiturgicalLibrarian, PhraseUsageMatch
    from src.agents.sacks_librarian import SacksLibrarian, SacksReference
    from src.agents.sacks_librarian import SacksLibrarian, SacksReference
    from src.agents.rag_manager import RAGManager, RAGContext
    from src.agents.related_psalms_librarian import RelatedPsalmsLibrarian, RelatedPsalmMatch
    from src.agents.figurative_curator import FigurativeCurator, FigurativeCuratorOutput, FigurativeSearchRequest
else:
    from .bdb_librarian import BDBLibrarian, LexiconRequest, LexiconBundle
    from .concordance_librarian import ConcordanceLibrarian, ConcordanceRequest, ConcordanceBundle
    from .figurative_librarian import FigurativeLibrarian, FigurativeRequest, FigurativeBundle
    from .commentary_librarian import CommentaryLibrarian, CommentaryBundle
    from .liturgical_librarian_sefaria import SefariaLiturgicalLibrarian, SefariaLiturgicalLink
    from .liturgical_librarian import LiturgicalLibrarian, PhraseUsageMatch
    from .sacks_librarian import SacksLibrarian, SacksReference
    from .sacks_librarian import SacksLibrarian, SacksReference
    from .rag_manager import RAGManager, RAGContext
    from .related_psalms_librarian import RelatedPsalmsLibrarian, RelatedPsalmMatch
    from .figurative_curator import FigurativeCurator, FigurativeCuratorOutput, FigurativeSearchRequest


def _truncate_bdb_entry(text: str, max_chars: int = 500) -> str:
    """Truncate a BDB lexicon entry to max_chars, preserving complete lines."""
    if len(text) <= max_chars + 100:  # Small buffer to avoid cutting near end
        return text
    # Find last newline or period before max_chars
    truncated = text[:max_chars]
    last_newline = truncated.rfind('\n')
    last_period = truncated.rfind('. ')
    break_point = max(last_newline, last_period + 1)
    if break_point > max_chars * 0.5:  # Only use natural break if it's past halfway
        truncated = text[:break_point + 1]
    return truncated.rstrip() + "\n[...]"


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
    commentary_requests: Optional[List[Dict[str, Any]]] = None  # [{"psalm": 27, "verse": 1, "reason": "..."}]
    notes: Optional[str] = None  # Overall research notes from Scholar
    verse_count: Optional[int] = None  # Number of verses in the psalm (for result filtering)

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
            commentary_requests=data.get('commentary', []),
            notes=data.get('notes'),
            verse_count=data.get('verse_count')
        )


@dataclass
class ResearchBundle:
    """
    Complete research bundle assembled for a Psalm.

    Contains all lexicon entries, concordance searches, figurative
    language instances, traditional commentaries, liturgical usage, Rabbi Sacks references,
    and RAG documents requested by the Scholar-Researcher.
    """
    psalm_chapter: int
    lexicon_bundle: Optional[LexiconBundle]
    concordance_bundles: List[ConcordanceBundle]
    figurative_bundles: List[FigurativeBundle]
    commentary_bundles: Optional[List[CommentaryBundle]]
    liturgical_usage: Optional[List[SefariaLiturgicalLink]]  # Phase 0: Sefaria liturgical cross-references (deprecated)
    liturgical_usage_aggregated: Optional[List[PhraseUsageMatch]]  # Phase 4/5: Aggregated phrase-level liturgy
    liturgical_markdown: Optional[str]  # Phase 4/5: Pre-formatted markdown for LLM consumption
    sacks_references: Optional[List[SacksReference]]  # Rabbi Jonathan Sacks references to this psalm
    sacks_markdown: Optional[str]  # Pre-formatted Sacks markdown for LLM consumption
    sacks_references: Optional[List[SacksReference]]  # Rabbi Jonathan Sacks references to this psalm
    sacks_markdown: Optional[str]  # Pre-formatted Sacks markdown for LLM consumption
    rag_context: Optional[RAGContext]  # Phase 2d: RAG documents
    related_psalms: Optional[List[RelatedPsalmMatch]]  # Related psalms from top connections analysis
    related_psalms_markdown: Optional[str]  # Pre-formatted related psalms markdown for LLM consumption
    request: ResearchRequest
    # Deep Web Research (Gemini Deep Research output)
    deep_research_content: Optional[str] = None  # Raw content from deep research file
    deep_research_included: bool = False  # Whether deep research was included in final bundle
    deep_research_removed_for_space: bool = False  # Whether it was removed due to character limits
    # Figurative Curator (LLM-enhanced figurative insights)
    figurative_curator_output: Optional[FigurativeCuratorOutput] = None  # Curated figurative insights from Gemini 3 Pro
    
    # Track models used by sub-agents
    models_used: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'psalm_chapter': self.psalm_chapter,
            'lexicon': self.lexicon_bundle.to_dict() if self.lexicon_bundle else None,
            'concordance': [c.to_dict() for c in self.concordance_bundles],
            'figurative': [f.to_dict() for f in self.figurative_bundles],
            'commentary': [c.to_dict() for c in self.commentary_bundles] if self.commentary_bundles else [],
            'sacks_references': [s.to_dict() for s in self.sacks_references] if self.sacks_references else [],
            'sacks_references': [s.to_dict() for s in self.sacks_references] if self.sacks_references else [],
            'related_psalms': [r.to_dict() for r in self.related_psalms] if self.related_psalms else [],
            'summary': {
                'lexicon_entries': len(self.lexicon_bundle.entries) if self.lexicon_bundle else 0,
                'concordance_searches': len(self.concordance_bundles),
                'concordance_results': sum(len(c.results) for c in self.concordance_bundles),
                'figurative_searches': len(self.figurative_bundles),
                'figurative_instances': sum(len(f.instances) for f in self.figurative_bundles),
                'commentary_verses': len(self.commentary_bundles) if self.commentary_bundles else 0,
                'commentary_entries': sum(len(c.commentaries) for c in self.commentary_bundles) if self.commentary_bundles else 0,
                'liturgical_contexts_phase0': len(self.liturgical_usage) if self.liturgical_usage else 0,
                'liturgical_prayers_aggregated': len(self.liturgical_usage_aggregated) if self.liturgical_usage_aggregated else 0,
                'liturgical_total_occurrences': sum(p.occurrence_count for p in self.liturgical_usage_aggregated) if self.liturgical_usage_aggregated else 0,
                'sacks_references': len(self.sacks_references) if self.sacks_references else 0,
                'sacks_references': len(self.sacks_references) if self.sacks_references else 0,
                'related_psalms': len(self.related_psalms) if self.related_psalms else 0,
                'deep_research_included': self.deep_research_included,
                'deep_research_removed_for_space': self.deep_research_removed_for_space,
                'deep_research_chars': len(self.deep_research_content) if self.deep_research_content else 0
            },
            'models_used': self.models_used
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
                # Compact header: word [Lexicon Strong's] *transliteration*
                header_parts = [f"### {entry.word}"]
                meta = []
                if entry.lexicon_name:
                    meta.append(entry.lexicon_name)
                if entry.strong_number:
                    meta.append(entry.strong_number)
                if meta:
                    header_parts.append(f"[{' '.join(meta)}]")
                if entry.transliteration:
                    header_parts.append(f"*{entry.transliteration}*")
                md += " ".join(header_parts) + "\n"

                md += f"{_truncate_bdb_entry(entry.entry_text)}\n\n"

                # Compact Klein data on one line if present
                klein_parts = []
                if entry.etymology_notes:
                    klein_parts.append(f"Klein: {entry.etymology_notes}")
                if entry.derivatives:
                    klein_parts.append(f"Derivatives: {entry.derivatives}")
                if klein_parts:
                    md += ". ".join(klein_parts) + "\n\n"

                md += "---\n\n"

        # Concordance section
        if self.concordance_bundles:
            md += "## Concordance Searches\n\n"

            # Group bundles by lexical_insight_id (Phase 2 enhancement)
            grouped_bundles = {}
            ungrouped_bundles = []

            for bundle in self.concordance_bundles:
                if bundle.request.lexical_insight_id:
                    insight_id = bundle.request.lexical_insight_id
                    if insight_id not in grouped_bundles:
                        grouped_bundles[insight_id] = []
                    grouped_bundles[insight_id].append(bundle)
                else:
                    ungrouped_bundles.append(bundle)

            # Initialize search_num outside both blocks
            search_num = 1
            if grouped_bundles:
                for insight_id, bundles in grouped_bundles.items():
                    # Find primary search
                    primary_bundle = next((b for b in bundles if b.request.is_primary_search), bundles[0])
                    total_results = sum(len(b.results) for b in bundles)

                    md += f"### {primary_bundle.request.insight_notes or primary_bundle.request.query} ({total_results} results, {primary_bundle.request.scope}, {primary_bundle.request.level})\n"

                    # Collect all variants from alternate_queries
                    all_variants = set()
                    for bundle in bundles:
                        if bundle.request.alternate_queries:
                            all_variants.update(bundle.request.alternate_queries)

                    if all_variants:
                        md += f"Variants: {', '.join(sorted(all_variants))}\n"
                    md += "\n"

                    # Show results from all bundles in the group
                    all_results = []
                    for bundle in bundles:
                        for result in bundle.results:
                            result.query_found = bundle.request.query
                            all_results.append(result)

                    # Remove duplicates (same verse reference)
                    unique_results = []
                    seen_refs = set()
                    for result in all_results:
                        if result.reference not in seen_refs:
                            unique_results.append(result)
                            seen_refs.add(result.reference)

                    if unique_results:
                        for result in unique_results[:10]:
                            matched = result.matched_phrase if result.is_phrase_match else f"{result.matched_word} (pos {result.word_position})"
                            md += f"**{result.reference}** | {result.hebrew_text} | {result.english_text} | *{matched}*\n\n"

                        if len(unique_results) > 10:
                            md += f"*...and {len(unique_results) - 10} more results*\n\n"

                    md += "---\n\n"
                    search_num += 1

            # Display ungrouped searches (legacy format)
            if ungrouped_bundles:
                for i, bundle in enumerate(ungrouped_bundles, search_num):
                    md += f"### {bundle.request.query} ({len(bundle.results)} results, {bundle.request.scope}, {bundle.request.level})\n\n"

                    if bundle.results:
                        for result in bundle.results[:10]:
                            matched = result.matched_phrase if result.is_phrase_match else f"{result.matched_word} (pos {result.word_position})"
                            md += f"**{result.reference}** | {result.hebrew_text} | {result.english_text} | *{matched}*\n\n"

                        if len(bundle.results) > 10:
                            md += f"*...and {len(bundle.results) - 10} more results*\n\n"

                    md += "---\n\n"

        # Figurative language section
        # If curator output is available, use that instead of raw instances
        if self.figurative_curator_output:
            md += "## Figurative Language Insights (Curated)\n\n"
            curator = self.figurative_curator_output

            # Add search summary
            md += f"*Searches performed*: {curator.search_summary.get('initial_searches', 0)} initial, "
            md += f"{curator.search_summary.get('total_iterations', 1)} iterations  \n"
            md += f"*Total results reviewed*: {curator.search_summary.get('total_results', 0)}  \n"
            md += f"*Vehicles analyzed*: {', '.join(curator.search_summary.get('vehicles_searched', []))}  \n\n"

            # Results by vehicle (for Methods section tracking)
            if curator.search_summary.get('results_by_vehicle'):
                md += "**Figurative Parallels Reviewed**:\n"
                for vehicle, count in sorted(curator.search_summary['results_by_vehicle'].items()):
                    md += f"- **{vehicle}**: {count} results\n"
                md += "\n"

            # Add figurative insights
            if curator.figurative_insights:
                md += "### Prose Insights\n\n"
                for i, insight in enumerate(curator.figurative_insights, 1):
                    title = insight.get('title', f'Insight {i}')
                    text = insight.get('insight', '')
                    verses = insight.get('verses_addressed', [])

                    md += f"#### {i}. {title}\n"
                    if verses:
                        md += f"*Addresses verses*: {', '.join(verses)}  \n\n"
                    md += f"{text}\n\n"
                    md += "---\n\n"

            # Add curated examples by vehicle
            if curator.curated_examples_by_vehicle:
                md += "### Curated Examples by Vehicle\n\n"
                for vehicle, examples in curator.curated_examples_by_vehicle.items():
                    md += f"#### Vehicle: {vehicle.upper()} ({len(examples)} curated examples)\n\n"

                    for i, ex in enumerate(examples, 1):
                        ref = ex.get('reference', 'Unknown')
                        fig_type = ex.get('type', '?')
                        text_en = ex.get('figurative_text_english', ex.get('figurative_text', ''))
                        text_he = ex.get('figurative_text_hebrew', '')
                        full_verse_he = ex.get('full_verse_hebrew', '')
                        reason = ex.get('reason_selected', '')

                        md += f"**{i}. {ref}** ({fig_type})  \n"
                        if text_en:
                            md += f"*English*: {text_en}  \n"
                        if text_he:
                            md += f"*Hebrew phrase*: {text_he}  \n"
                        if full_verse_he and full_verse_he != text_he:
                            md += f"*Full verse*: {full_verse_he}  \n"
                        if reason:
                            md += f"*Why selected*: {reason}  \n"
                        md += "\n"

                    md += "---\n\n"

        elif self.figurative_bundles:
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
                    md += f"#### All Instances ({len(bundle.instances)} total):\n\n"
                    for inst in bundle.instances[:20]:
                        types = ', '.join([t for t in ['simile', 'metaphor', 'personification', 'idiom', 'hyperbole', 'metonymy']
                                          if getattr(inst, f'is_{t}')])
                        md += f"**{inst.reference}** ({types}) - confidence: {inst.confidence:.2f}  \n"
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




                    if len(bundle.instances) > 20:
                        md += f"*...and {len(bundle.instances) - 20} more instances*\n\n"

                    # Add vehicle frequency analysis if we have many instances
                    if len(bundle.instances) > 10:
                        vehicle_freq = bundle.get_vehicle_frequency()
                        if vehicle_freq and len(vehicle_freq) > 1:
                            top_3_vehicles = sorted(vehicle_freq.items(), key=lambda x: x[1], reverse=True)[:3]
                            md += f"**Usage breakdown**: "
                            md += ", ".join([f"{vehicle} ({count}x)" for vehicle, count in top_3_vehicles])
                            md += "\n\n"

                md += "---\n\n"

        # RAG Context section (Phase 2d)
        if self.rag_context:
            from .rag_manager import RAGManager
            rag_mgr = RAGManager()

            md += "## Scholarly Context (RAG Documents)\n\n"

            # Psalm Function/Genre
            if self.rag_context.psalm_function:
                pf = self.rag_context.psalm_function
                md += f"### Psalm {pf['psalm']} Function & Genre\n"
                md += f"**Genre**: {pf['genre']}  \n\n"
                md += f"**Structure**:  \n"
                for line in pf['structure']:
                    md += f"- {line}  \n"
                md += f"\n**Keywords**: {', '.join(pf['keywords'])}  \n\n"

            # Ugaritic Parallels
            if self.rag_context.ugaritic_parallels:
                md += f"### Ugaritic & Ancient Near Eastern Parallels ({len(self.rag_context.ugaritic_parallels)} found)\n\n"
                for parallel in self.rag_context.ugaritic_parallels:
                    heb = parallel.get('hebrew_psalter_source', {})
                    md += f"**{parallel.get('parallel_type')}** ({heb.get('text_reference')})  \n"
                    md += f"*Conceptual Analysis*: {parallel.get('conceptual_analysis', '')[:300]}...  \n\n"

            # Analytical framework is passed separately to consuming agents via their
            # prompt templates (e.g., {analytical_framework} in master_editor.py).
            # Not embedded in the research bundle to avoid duplication.
            md += "---\n\n"

        # Commentary section
        if self.commentary_bundles:
            md += "## Traditional Commentaries\n\n"
            md += "Rashi (1040–1105), Ibn Ezra (c.1092–1167), Radak (1160–1235), "
            md += "Meiri (1249–1316), Metzudat David (c.1687–1769), Malbim (1809–1879), "
            md += "Torah Temimah (1860–1941).\n\n"

            for bundle in self.commentary_bundles:
                if bundle.commentaries:
                    for comm in bundle.commentaries:
                        md += f"### {bundle.psalm}:{bundle.verse} — {comm.commentator}\n"
                        md += f"*{bundle.reason}*\n"

                        if comm.hebrew:
                            hebrew_text = comm.hebrew if len(comm.hebrew) <= 400 else f"{comm.hebrew[:400]}..."
                            md += f"{hebrew_text}\n"

                        if comm.english:
                            english_text = comm.english if len(comm.english) <= 400 else f"{comm.english[:400]}..."
                            md += f"{english_text}\n\n"
                else:
                    md += f"### {bundle.psalm}:{bundle.verse}\n"
                    md += "*No commentaries available.*\n\n"

        # Liturgical Usage section (Phase 4/5: Aggregated phrase-level data)
        if self.liturgical_markdown:
            md += self.liturgical_markdown
            md += "\n---\n\n"
        # Fallback to Phase 0 Sefaria data if Phase 4/5 not available
        elif self.liturgical_usage:
            md += "## Liturgical Usage (from Sefaria - Phase 0)\n\n"
            md += f"This Psalm appears in **{len(self.liturgical_usage)} liturgical context(s)** according to Sefaria's curated data:\n\n"

            for link in self.liturgical_usage:
                md += f"**{link.format_location()}**\n"
                md += f"- Reference: {link.liturgy_ref}\n"
                md += f"- Verses: {link.format_verse_range()}\n"

                if link.nusach:
                    md += f"- Tradition: {link.nusach}\n"

                md += "\n"

            md += "---\n\n"

        # Rabbi Sacks References section
        if self.sacks_markdown:
            md += self.sacks_markdown
            md += "\n---\n\n"



        # Related Psalms section
        if self.related_psalms_markdown:
            md += self.related_psalms_markdown
            md += "\n---\n\n"

        # Deep Web Research section (Gemini Deep Research output)
        if self.deep_research_included and self.deep_research_content:
            md += "## Deep Web Research\n\n"
            md += "*This section contains research assembled via Gemini Deep Research, including ancient, medieval, and modern scholarly commentary; ANE parallels; linguistic and philological analysis; reception history; liturgical usage; and literary/cultural influence.*\n\n"
            md += self.deep_research_content
            md += "\n\n---\n\n"

        # Summary
        summary = self.to_dict()['summary']
        md += "## Research Summary\n\n"
        md += f"- **Lexicon entries**: {summary['lexicon_entries']}\n"
        md += f"- **Concordance searches**: {summary['concordance_searches']}\n"
        md += f"- **Concordance results**: {summary['concordance_results']}\n"
        md += f"- **Figurative language searches**: {summary['figurative_searches']}\n"
        md += f"- **Figurative instances found**: {summary['figurative_instances']}\n"
        md += f"- **Commentary verses**: {summary['commentary_verses']}\n"
        md += f"- **Commentary entries**: {summary['commentary_entries']}\n"
        md += f"- **Liturgical prayers (aggregated)**: {summary['liturgical_prayers_aggregated']}\n"
        md += f"- **Rabbi Sacks references**: {summary['sacks_references']}\n"
        md += f"- **Liturgical total occurrences**: {summary['liturgical_total_occurrences']}\n"
        md += f"- **Related psalms analyzed**: {summary['related_psalms']}\n"
        md += f"- **Deep web research included**: {'Yes' if summary['deep_research_included'] else 'No'}\n"
        
        if self.models_used:
            md += "\n### Models Used in Research\n"
            for agent, model in self.models_used.items():
                md += f"- **{agent.replace('_', ' ').title()}**: {model}\n"

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

    @staticmethod
    def _filter_figurative_bundle(
        bundle: 'FigurativeBundle',
        max_results: int,
        search_terms: Optional[List[str]] = None
    ) -> 'FigurativeBundle':
        """
        Filter figurative bundle to limit results, prioritizing by priority ranking if available.

        Args:
            bundle: Original FigurativeBundle with all results
            max_results: Maximum number of instances to keep
            search_terms: Search terms used (for phrase match prioritization)

        Returns:
            New FigurativeBundle with filtered instances
        """
        if len(bundle.instances) <= max_results:
            return bundle

        instances = bundle.instances

        # NEW: If vehicle_contains was used and we have excess results, prioritize exact vehicle matches
        if hasattr(bundle, 'request') and hasattr(bundle.request, 'vehicle_contains') and bundle.request.vehicle_contains:
            search_term = bundle.request.vehicle_contains.lower()
            exact_matches = []
            other_matches = []

            for instance in instances:
                if not instance.vehicle:
                    other_matches.append(instance)
                    continue

                # Check if any vehicle element exactly matches the search term (case-insensitive)
                is_exact_match = any(
                    vehicle_element.lower() == search_term
                    for vehicle_element in instance.vehicle
                    if isinstance(vehicle_element, str)
                )

                if is_exact_match:
                    exact_matches.append(instance)
                else:
                    other_matches.append(instance)

            # Prioritize exact matches, then fill with others
            # This ensures "tent" exact matches appear before "tents" or compound matches
            instances = exact_matches + other_matches

        # If we have search terms, prioritize phrase matches over single-word matches
        if search_terms:
            # Classify each instance by match quality
            phrase_matches = []
            single_word_matches = []

            # Identify multi-word search terms (phrases)
            phrase_terms = [t.lower() for t in search_terms if ' ' in t]
            single_terms = [t.lower() for t in search_terms if ' ' not in t]

            for inst in instances:
                # Check if this instance matched a phrase term
                is_phrase_match = False
                if inst.vehicle:
                    vehicle_text = ' '.join(inst.vehicle).lower()
                    for phrase in phrase_terms:
                        if phrase in vehicle_text:
                            is_phrase_match = True
                            break

                if is_phrase_match:
                    phrase_matches.append(inst)
                else:
                    single_word_matches.append(inst)

            # Prioritize phrase matches, then fill with single-word matches
            filtered = phrase_matches[:max_results]
            remaining_slots = max_results - len(filtered)
            if remaining_slots > 0:
                filtered.extend(single_word_matches[:remaining_slots])

            instances = filtered

        # Sort by term_priority and randomize within each priority group
        if any(hasattr(inst, 'term_priority') and inst.term_priority is not None for inst in instances):
            # Group instances by term priority
            priority_groups = {}
            for inst in instances:
                priority = getattr(inst, 'term_priority', 999)  # Unknown = lowest priority
                if priority not in priority_groups:
                    priority_groups[priority] = []
                priority_groups[priority].append(inst)

            # Shuffle each group and reassemble in priority order
            instances = []
            for priority in sorted(priority_groups.keys()):
                group = priority_groups[priority]
                random.shuffle(group)  # Randomize within same priority
                instances.extend(group)

        # Limit to max_results
        instances = instances[:max_results]

        # Return new bundle with filtered instances
        return FigurativeBundle(
            instances=instances,
            request=bundle.request
        )

    def __init__(self, use_llm_summaries: bool = True, cost_tracker=None, use_figurative_curator: bool = True):
        """
        Initialize Research Assembler with all librarian agents.

        Args:
            use_llm_summaries: Enable LLM-powered liturgical summaries (Claude Haiku 4.5).
                             Requires ANTHROPIC_API_KEY environment variable.
            cost_tracker: CostTracker instance for tracking API costs
            use_figurative_curator: Enable Figurative Curator for LLM-enhanced insights (Gemini 3 Pro).
                                   Requires GEMINI_API_KEY environment variable. Default: True.
        """
        self.logger = logging.getLogger(__name__)
        self.bdb_librarian = BDBLibrarian()
        self.concordance_librarian = ConcordanceLibrarian(logger=self.logger)
        self.figurative_librarian = FigurativeLibrarian()
        self.commentary_librarian = CommentaryLibrarian()
        self.liturgical_librarian_sefaria = SefariaLiturgicalLibrarian()  # Phase 0: Sefaria bootstrap (fallback)
        self.liturgical_librarian = LiturgicalLibrarian(use_llm_summaries=use_llm_summaries, cost_tracker=cost_tracker)  # Phase 4/5: Aggregated phrase-level
        self.sacks_librarian = SacksLibrarian()  # Rabbi Jonathan Sacks references

        self.rag_manager = RAGManager()  # Phase 2d: RAG document manager
        self.related_psalms_librarian = RelatedPsalmsLibrarian(connections_file='data/analysis_results/top_550_connections_v6.json')  # Related psalms from top connections
        self.related_psalms_librarian.logger = self.logger  # Pass logger for debug output

        # Figurative Curator for LLM-enhanced figurative insights (Session 226)
        self.use_figurative_curator = use_figurative_curator
        self.figurative_curator = None
        if use_figurative_curator:
            try:
                self.figurative_curator = FigurativeCurator(verbose=False)
                if self.logger:
                    self.logger.info("Figurative Curator enabled (Gemini 3 Pro)")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Figurative Curator initialization failed: {e}. Falling back to standard figurative output.")
                self.use_figurative_curator = False

        # Deep research directory path (resolved relative to project root)
        self._deep_research_dir = Path(__file__).parent.parent.parent / 'data' / 'deep_research'

    def _load_deep_research(self, psalm_chapter: int) -> Optional[str]:
        """
        Load deep research content from file if it exists.

        Args:
            psalm_chapter: Psalm number to look up

        Returns:
            Deep research content as string, or None if not found
        """
        filename = f"psalm_{psalm_chapter:03d}_deep_research.txt"
        filepath = self._deep_research_dir / filename

        if filepath.exists():
            try:
                content = filepath.read_text(encoding='utf-8').strip()
                if content:
                    self.logger.info(f"Loaded deep research for Psalm {psalm_chapter}: {len(content)} chars")
                    return content
            except Exception as e:
                self.logger.warning(f"Failed to load deep research for Psalm {psalm_chapter}: {e}")

        return None
        
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
            # Inject source_psalm into each concordance request
            enhanced_requests = []
            for concordance_request in request.concordance_requests:
                # Create a new request with source_psalm and Phase 2 tracking fields added
                enhanced_request = ConcordanceRequest(
                    query=concordance_request.query,
                    scope='auto',  # Let librarian determine optimal scope
                    level=concordance_request.level,
                    include_variations=concordance_request.include_variations,
                    notes=concordance_request.notes,
                    max_results=concordance_request.max_results,
                    auto_scope_threshold=concordance_request.auto_scope_threshold,
                    alternate_queries=concordance_request.alternate_queries,
                    source_psalm=request.psalm_chapter,  # Inject current psalm
                    # Phase 2 tracking fields - pass through if present
                    lexical_insight_id=concordance_request.lexical_insight_id,
                    is_primary_search=concordance_request.is_primary_search,
                    insight_notes=concordance_request.insight_notes
                )
                enhanced_requests.append(enhanced_request)
            concordance_bundles = self.concordance_librarian.search_multiple(enhanced_requests)

        # Fetch figurative language instances
        figurative_bundles = []
        if request.figurative_requests:
            figurative_bundles = self.figurative_librarian.search_multiple(request.figurative_requests)

            # Apply verse-count-based filtering to limit results per query
            # <20 verses: 20 max per query; >=20 verses: 10 max per query
            if request.verse_count is not None:
                max_per_query = 20 if request.verse_count < 20 else 10

                filtered_bundles = []
                for bundle, fig_request in zip(figurative_bundles, request.figurative_requests):
                    # Get search terms for phrase prioritization
                    search_terms = fig_request.vehicle_search_terms
                    filtered_bundle = self._filter_figurative_bundle(
                        bundle,
                        max_results=max_per_query,
                        search_terms=search_terms
                    )
                    filtered_bundles.append(filtered_bundle)
                figurative_bundles = filtered_bundles

        # Curate figurative insights with Figurative Curator (if enabled)
        figurative_curator_output = None
        if self.use_figurative_curator and self.figurative_curator and request.figurative_requests:
            try:
                # Convert FigurativeRequest objects to FigurativeSearchRequest objects
                curator_requests = []
                for fig_req in request.figurative_requests:
                    curator_req = FigurativeSearchRequest(
                        vehicle_contains=fig_req.vehicle_contains or "",
                        vehicle_search_terms=fig_req.vehicle_search_terms or [],
                        notes=fig_req.notes or ""
                    )
                    curator_requests.append(curator_req)

                if self.logger:
                    self.logger.info(f"Curating figurative insights for Psalm {request.psalm_chapter} with {len(curator_requests)} search requests...")

                # Run the curator
                figurative_curator_output = self.figurative_curator.curate(
                    psalm_number=request.psalm_chapter,
                    micro_analyst_requests=curator_requests
                )

                if self.logger and figurative_curator_output:
                    total_examples = sum(len(exs) for exs in figurative_curator_output.curated_examples_by_vehicle.values())
                    cost = figurative_curator_output.token_usage.get("cost", 0.0)
                    self.logger.info(f"Curator produced {len(figurative_curator_output.figurative_insights)} insights, "
                                   f"{total_examples} curated examples across {len(figurative_curator_output.curated_examples_by_vehicle)} vehicles. "
                                   f"Cost: ${cost:.4f}")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Figurative Curator failed: {e}. Falling back to standard figurative output.")
                figurative_curator_output = None

        # Fetch traditional commentaries
        commentary_bundles = None
        if request.commentary_requests:
            commentary_bundles = self.commentary_librarian.process_requests(request.commentary_requests)

        # Fetch liturgical usage (Phase 4/5: Aggregated phrase-level with LLM summaries)
        liturgical_usage_aggregated = None
        liturgical_markdown = None
        try:
            # Try Phase 4/5 first (comprehensive, aggregated)
            liturgical_usage_aggregated = self.liturgical_librarian.find_liturgical_usage_aggregated(
                psalm_chapter=request.psalm_chapter,
                min_confidence=0.75
            )
            if liturgical_usage_aggregated:
                # Format as markdown for LLM consumption
                liturgical_markdown = self.liturgical_librarian.format_for_research_bundle(
                    liturgical_usage_aggregated,
                    psalm_chapter=request.psalm_chapter
                )
        except Exception as e:
            # If Phase 4/5 fails, will fall back to Phase 0 below
            print(f"Warning: Phase 4/5 liturgical lookup failed: {e}")
            liturgical_usage_aggregated = None

        # Fetch Phase 0 liturgical usage as fallback (Sefaria bootstrap)
        liturgical_usage = None
        if not liturgical_usage_aggregated:
            liturgical_usage = self.liturgical_librarian_sefaria.find_liturgical_usage(request.psalm_chapter)

        # Fetch Rabbi Sacks references (ALWAYS included, regardless of request)
        sacks_references = self.sacks_librarian.get_psalm_references(request.psalm_chapter)
        sacks_markdown = None
        if sacks_references:
            sacks_markdown = self.sacks_librarian.format_for_research_bundle(
                sacks_references,
                psalm_chapter=request.psalm_chapter
            )



        # Fetch RAG context (Phase 2d: Always included for psalm-level research)
        rag_context = self.rag_manager.get_rag_context(request.psalm_chapter)

        # Fetch related psalms from top connections analysis (ALWAYS included)
        related_psalms = self.related_psalms_librarian.get_related_psalms(request.psalm_chapter)
        related_psalms_markdown = None
        if related_psalms:
            related_psalms_markdown = self.related_psalms_librarian.format_for_research_bundle(
                request.psalm_chapter,
                related_psalms,
                max_size_chars=50000  # Reduced from default 100KB to prevent token limit overflow
            )
            if self.logger:
                self.logger.info(f"Related Psalms for Psalm {request.psalm_chapter}: "
                               f"{len(related_psalms)} matches, markdown size: {len(related_psalms_markdown)} chars")

        # Load deep research content (Gemini Deep Research output) if available
        deep_research_content = self._load_deep_research(request.psalm_chapter)

        # Collect models used
        models_used = {}
        if self.liturgical_librarian:
            models_used['liturgical_librarian'] = self.liturgical_librarian.active_model
        
        if self.use_figurative_curator and self.figurative_curator and figurative_curator_output:
            models_used['figurative_curator'] = self.figurative_curator.active_model

        return ResearchBundle(
            psalm_chapter=request.psalm_chapter,
            lexicon_bundle=lexicon_bundle,
            concordance_bundles=concordance_bundles,
            figurative_bundles=figurative_bundles,
            commentary_bundles=commentary_bundles,
            liturgical_usage=liturgical_usage if liturgical_usage else None,
            liturgical_usage_aggregated=liturgical_usage_aggregated if liturgical_usage_aggregated else None,
            liturgical_markdown=liturgical_markdown if liturgical_markdown else None,
            sacks_references=sacks_references if sacks_references else None,
            sacks_markdown=sacks_markdown if sacks_markdown else None,
            rag_context=rag_context,
            related_psalms=related_psalms if related_psalms else None,
            related_psalms_markdown=related_psalms_markdown if related_psalms_markdown else None,
            request=request,
            # Deep research - initially included if available, may be removed for space later
            deep_research_content=deep_research_content,
            deep_research_included=bool(deep_research_content),
            deep_research_removed_for_space=False,
            # Figurative curator - LLM-enhanced insights (Session 226)
            figurative_curator_output=figurative_curator_output,
            models_used=models_used
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
