"""
Pipeline Summary Tracker

Tracks detailed statistics throughout the enhanced pipeline run and generates
a comprehensive markdown summary report.

The tracker captures:
1. Token/character counts for each pipeline step
2. Research request details (lexicon, concordance, figurative, commentary)
3. Research bundle returns (counts per category)
4. Ugaritic parallel information
5. Question counts from analysis agents

Author: Claude (Anthropic)
Date: 2025-10-19
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class StepStats:
    """Statistics for a single pipeline step."""
    step_name: str
    input_char_count: int = 0
    input_token_estimate: int = 0
    output_char_count: int = 0
    output_token_estimate: int = 0
    duration_seconds: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token for English, 2-3 for Hebrew)."""
        # More conservative estimate for mixed Hebrew/English content
        return len(text) // 3


@dataclass
class ResearchStats:
    """Statistics for research requests and returns."""
    # Requests
    lexicon_requests: List[Dict[str, str]] = field(default_factory=list)
    concordance_requests: List[Dict[str, str]] = field(default_factory=list)
    figurative_requests: List[Dict[str, Any]] = field(default_factory=list)
    commentary_requests: List[Dict[str, str]] = field(default_factory=list)

    # Returns
    lexicon_entries_count: int = 0
    concordance_results: Dict[str, int] = field(default_factory=dict)  # query -> count
    figurative_results: Dict[str, int] = field(default_factory=dict)  # verse -> count
    commentary_counts: Dict[str, int] = field(default_factory=dict)  # commentator -> count
    sacks_references_count: int = 0  # Rabbi Jonathan Sacks references
    related_psalms_count: int = 0  # Related psalms from top connections analysis
    related_psalms_list: List[int] = field(default_factory=list)  # List of psalm numbers analyzed

    # Ugaritic parallels
    ugaritic_parallels: List[Dict[str, str]] = field(default_factory=list)

    # Research bundle size (total bundle generated in Step 2)
    research_bundle_chars: int = 0
    research_bundle_tokens: int = 0


@dataclass
class AnalysisStats:
    """Statistics for analysis outputs."""
    macro_questions: List[str] = field(default_factory=list)
    micro_questions: List[str] = field(default_factory=list)
    verse_count: int = 0


class PipelineSummaryTracker:
    """
    Tracks statistics throughout the enhanced pipeline run.

    Usage:
        tracker = PipelineSummaryTracker(psalm_number=23)

        # Track a step
        tracker.track_step_input("macro_analysis", macro_input_text)
        # ... run macro analysis ...
        tracker.track_step_output("macro_analysis", macro_output_text, duration=45.2)

        # Track research
        tracker.track_research_requests(research_request)
        tracker.track_research_bundle(research_bundle)

        # Track questions
        tracker.track_macro_questions(macro_analysis.research_questions)
        tracker.track_micro_questions(micro_analysis.interesting_questions)

        # Generate report
        report = tracker.generate_markdown_report()
        tracker.save_report(output_dir)
    """

    def __init__(self, psalm_number: int, initial_data: Optional[Dict[str, Any]] = None):
        """
        Initialize the tracker.

        Args:
            psalm_number: The psalm number being processed.
            initial_data: Optional dictionary to pre-populate the tracker, for resuming runs.
        """
        if initial_data:
            self.psalm_number = initial_data.get('psalm_number', psalm_number)
            
            # Reconstruct StepStats objects
            self.steps = {}
            for step_name, step_data in initial_data.get('steps', {}).items():
                self.steps[step_name] = StepStats(
                    step_name=step_name,
                    input_char_count=step_data.get('input_char_count', 0),
                    input_token_estimate=step_data.get('input_token_estimate', 0),
                    output_char_count=step_data.get('output_char_count', 0),
                    output_token_estimate=step_data.get('output_token_estimate', 0),
                    duration_seconds=step_data.get('duration_seconds'),
                    timestamp=step_data.get('timestamp')
                )

            # Reconstruct ResearchStats and AnalysisStats objects
            self.research = ResearchStats(**initial_data.get('research', {}))
            self.analysis = AnalysisStats(**initial_data.get('analysis', {}))

            # Load other top-level fields
            self.pipeline_start = datetime.fromisoformat(initial_data.get('pipeline_start')) if initial_data.get('pipeline_start') else datetime.now()
            self.pipeline_end = datetime.fromisoformat(initial_data.get('pipeline_end')) if initial_data.get('pipeline_end') else None
            self.model_usage = initial_data.get('model_usage', {})
            
        else:
            # Initialize fresh
            self.psalm_number = psalm_number
            self.steps: Dict[str, StepStats] = {}
            self.research: ResearchStats = ResearchStats()
            self.analysis: AnalysisStats = AnalysisStats()
            self.pipeline_start = datetime.now()
            self.pipeline_end: Optional[datetime] = None
            self.model_usage: Dict[str, Any] = {} # Can store simple key-value or complex dict

    def track_step_input(self, step_name: str, input_text: str):
        """Track input for a pipeline step."""
        if step_name not in self.steps:
            self.steps[step_name] = StepStats(step_name=step_name)

        step = self.steps[step_name]
        step.input_char_count = len(input_text)
        step.input_token_estimate = step.estimate_tokens(input_text)

    def track_step_output(self, step_name: str, output_text: str, duration: Optional[float] = None):
        """Track output for a pipeline step."""
        if step_name not in self.steps:
            self.steps[step_name] = StepStats(step_name=step_name)

        step = self.steps[step_name]
        step.output_char_count = len(output_text)
        step.output_token_estimate = step.estimate_tokens(output_text)
        step.duration_seconds = duration

    def track_research_requests(self, research_request):
        """Track research requests from MicroAnalyst."""
        # Lexicon requests
        for req in research_request.lexicon_requests:
            self.research.lexicon_requests.append({
                'word': req.word if hasattr(req, 'word') else str(req),
                'reason': getattr(req, 'notes', '') or getattr(req, 'reason', '')
            })

        # Concordance requests
        for req in research_request.concordance_requests:
            self.research.concordance_requests.append({
                'query': req.query,
                'scope': req.scope,
                'level': req.level,
                'purpose': getattr(req, 'notes', '') or getattr(req, 'purpose', '')
            })

        # Figurative language requests
        for req in research_request.figurative_requests:
            fig_dict = {
                'verse': getattr(req, 'verse', None),
                'reason': getattr(req, 'notes', ''),
            }

            # Extract search terms
            if hasattr(req, 'target_contains') and req.target_contains:
                fig_dict['target'] = req.target_contains
            if hasattr(req, 'vehicle_contains') and req.vehicle_contains:
                fig_dict['vehicle'] = req.vehicle_contains
            if hasattr(req, 'vehicle_search_terms') and req.vehicle_search_terms:
                fig_dict['vehicle_terms'] = req.vehicle_search_terms

            self.research.figurative_requests.append(fig_dict)

        # Commentary requests
        if research_request.commentary_requests:
            for req in research_request.commentary_requests:
                if isinstance(req, dict):
                    self.research.commentary_requests.append({
                        'verse': f"{req.get('psalm', '')}:{req.get('verse', '')}",
                        'reason': req.get('reason', '')
                    })

    def track_research_bundle(self, research_bundle):
        """Track research bundle returns."""
        # Lexicon entries
        if research_bundle.lexicon_bundle and research_bundle.lexicon_bundle.entries:
            self.research.lexicon_entries_count = len(research_bundle.lexicon_bundle.entries)

        # Concordance results
        for bundle in research_bundle.concordance_bundles:
            query = bundle.request.query
            count = len(bundle.results)
            self.research.concordance_results[query] = count

        # Figurative language results - Count all instances from all bundles
        # This ensures we count from the full, untrimmed bundle that the MasterEditor sees.
        total_figurative_instances = 0
        if research_bundle.figurative_bundles:
            for bundle in research_bundle.figurative_bundles:
                total_figurative_instances += len(bundle.instances)
        
        self.research.figurative_results['total_instances_used'] = total_figurative_instances

        # Commentary results
        if research_bundle.commentary_bundles:
            for bundle in research_bundle.commentary_bundles:
                for comm in bundle.commentaries:
                    commentator = comm.commentator
                    self.research.commentary_counts[commentator] = \
                        self.research.commentary_counts.get(commentator, 0) + 1

        # Rabbi Sacks references
        if research_bundle.sacks_references:
            self.research.sacks_references_count = len(research_bundle.sacks_references)

        # Related psalms (from top connections analysis)
        if research_bundle.related_psalms:
            self.research.related_psalms_count = len(research_bundle.related_psalms)
            self.research.related_psalms_list = [p.psalm_number for p in research_bundle.related_psalms]

        # Ugaritic parallels (from RAG context)
        if research_bundle.rag_context and research_bundle.rag_context.ugaritic_parallels:
            for parallel in research_bundle.rag_context.ugaritic_parallels:
                self.research.ugaritic_parallels.append({
                    'type': parallel.get('parallel_type', ''),
                    'reference': parallel.get('hebrew_psalter_source', {}).get('text_reference', ''),
                    'analysis': parallel.get('conceptual_analysis', '')[:100] + '...'
                })

    def track_macro_questions(self, questions: List[str]):
        """Track research questions from MacroAnalyst."""
        self.analysis.macro_questions = questions

    def track_micro_questions(self, questions: List[str]):
        """Track interesting questions from MicroAnalyst."""
        self.analysis.micro_questions = questions

    def track_verse_count(self, count: int):
        """Track number of verses in psalm."""
        self.analysis.verse_count = count

    def track_research_bundle_size(self, char_count: int, token_estimate: int):
        """
        Track the size of the research bundle generated in Step 2.

        Args:
            char_count: Total character count of the research bundle
            token_estimate: Estimated token count
        """
        self.research.research_bundle_chars = char_count
        self.research.research_bundle_tokens = token_estimate

    def mark_pipeline_complete(self):
        """Mark pipeline as complete."""
        self.pipeline_end = datetime.now()

        # Ensure the completion date is captured where formatters expect it
        # The print-ready and .docx generators read steps.master_editor.completion_date
        if "master_editor" not in self.steps:
            self.steps["master_editor"] = StepStats(step_name="master_editor")
        self.steps["master_editor"].completion_date = self.pipeline_end.isoformat()

    def track_model_usage(self, agent_name: str, model: str, input_tokens: int, output_tokens: int):
        """Track model usage for a specific agent."""
        if agent_name not in self.model_usage:
            self.model_usage[agent_name] = {'model': model, 'calls': 0, 'total_input_tokens': 0, 'total_output_tokens': 0}

        usage = self.model_usage[agent_name]
        usage['calls'] += 1
        usage['total_input_tokens'] += input_tokens
        usage['total_output_tokens'] += output_tokens
        
    def track_model_for_step(self, step_name: str, model_name: str):
        """
        Associates a model with a specific pipeline step, used when token counts are not available.
        This is simpler than track_model_usage and is intended for the skip-step logic.
        """
        # This will overwrite any existing complex data from track_model_usage,
        # but in a skip-step scenario, this is the desired behavior.
        self.model_usage[step_name] = model_name

    def track_completion_date(self, date_str: str):
        """
        Explicitly set the completion date for the master_editor step.
        Used when resuming a pipeline to preserve the original completion date.
        """
        if "master_editor" not in self.steps:
            self.steps["master_editor"] = StepStats(step_name="master_editor")
        
        # This is a bit of a hack, but it ensures the date is stored in the right place.
        self.steps["master_editor"].completion_date = date_str

    def generate_markdown_report(self) -> str:
        """Generate comprehensive markdown report."""
        lines = []

        # Header
        lines.append(f"# Pipeline Summary Report: Psalm {self.psalm_number}")
        lines.append(f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if self.pipeline_end:
            duration = (self.pipeline_end - self.pipeline_start).total_seconds()
            lines.append(f"**Total Pipeline Duration**: {duration:.1f} seconds ({duration/60:.1f} minutes)")

        lines.append(f"\n---\n")

        # Table of Contents
        lines.append("## Table of Contents")
        lines.append("1. [Pipeline Steps Overview](#pipeline-steps-overview)")
        lines.append("2. [Research Requests](#research-requests)")
        lines.append("3. [Research Bundle Returns](#research-bundle-returns)")
        lines.append("4. [Analysis Questions](#analysis-questions)")
        lines.append("5. [Token Usage Summary](#token-usage-summary)")
        lines.append("\n---\n")

        # Section 1: Pipeline Steps
        lines.append("## Pipeline Steps Overview\n")

        if self.steps:
            lines.append("| Step | Input Chars | Input Tokens (est) | Output Chars | Output Tokens (est) | Duration (s) |")
            lines.append("|------|-------------|-------------------|--------------|---------------------|--------------|")

            for step_name, step in self.steps.items():
                duration_str = f"{step.duration_seconds:.1f}" if step.duration_seconds else "N/A"
                lines.append(
                    f"| {step_name} | {step.input_char_count:,} | {step.input_token_estimate:,} | "
                    f"{step.output_char_count:,} | {step.output_token_estimate:,} | {duration_str} |"
                )

                # Add research bundle size row after micro_analysis
                if step_name == "micro_analysis" and self.research.research_bundle_chars > 0:
                    lines.append(
                        f"| → research_bundle | — | — | "
                        f"{self.research.research_bundle_chars:,} | {self.research.research_bundle_tokens:,} | — |"
                    )
        else:
            lines.append("*No step statistics tracked.*")

        lines.append("\n---\n")

        # Section 2: Research Requests
        lines.append("## Research Requests\n")

        # Lexicon requests
        lines.append(f"### Lexicon Requests ({len(self.research.lexicon_requests)})\n")
        if self.research.lexicon_requests:
            lines.append("| # | Hebrew Word | Reason |")
            lines.append("|---|-------------|--------|")
            for i, req in enumerate(self.research.lexicon_requests, 1):
                word = req['word']
                reason = req.get('reason', '')[:80] + ('...' if len(req.get('reason', '')) > 80 else '')
                lines.append(f"| {i} | {word} | {reason} |")
        else:
            lines.append("*No lexicon requests.*")

        lines.append("")

        # Concordance requests
        lines.append(f"### Concordance Searches ({len(self.research.concordance_requests)})\n")
        if self.research.concordance_requests:
            lines.append("| # | Query | Scope | Level | Purpose |")
            lines.append("|---|-------|-------|-------|---------|")
            for i, req in enumerate(self.research.concordance_requests, 1):
                query = req['query']
                scope = req['scope']
                level = req['level']
                purpose = req.get('purpose', '')[:60] + ('...' if len(req.get('purpose', '')) > 60 else '')
                lines.append(f"| {i} | {query} | {scope} | {level} | {purpose} |")
        else:
            lines.append("*No concordance requests.*")

        lines.append("")

        # Figurative language requests
        lines.append(f"### Figurative Language Searches ({len(self.research.figurative_requests)})\n")
        if self.research.figurative_requests:
            lines.append("| # | Verse | Vehicle Terms | Reason |")
            lines.append("|---|-------|---------------|--------|")
            for i, req in enumerate(self.research.figurative_requests, 1):
                verse = req.get('verse', 'N/A')

                # Gather vehicle terms
                vehicle_terms = []
                if 'vehicle' in req:
                    vehicle_terms.append(req['vehicle'])
                if 'vehicle_terms' in req:
                    vehicle_terms.extend(req['vehicle_terms'][:3])  # First 3 terms
                vehicle_str = ', '.join(vehicle_terms) if vehicle_terms else 'N/A'
                if len(vehicle_str) > 40:
                    vehicle_str = vehicle_str[:40] + '...'

                reason = req.get('reason', '')[:50] + ('...' if len(req.get('reason', '')) > 50 else '')
                lines.append(f"| {i} | {verse} | {vehicle_str} | {reason} |")
        else:
            lines.append("*No figurative language requests.*")

        lines.append("")

        # Commentary requests
        lines.append(f"### Commentary Requests ({len(self.research.commentary_requests)})\n")
        if self.research.commentary_requests:
            lines.append("| # | Verse | Reason |")
            lines.append("|---|-------|--------|")
            for i, req in enumerate(self.research.commentary_requests, 1):
                verse = req['verse']
                reason = req.get('reason', '')[:70] + ('...' if len(req.get('reason', '')) > 70 else '')
                lines.append(f"| {i} | {verse} | {reason} |")
        else:
            lines.append("*No commentary requests.*")

        lines.append("\n---\n")

        # Section 3: Research Bundle Returns
        lines.append("## Research Bundle Returns\n")

        # Lexicon entries
        lines.append(f"### Lexicon Entries\n")
        lines.append(f"**Total entries returned**: {self.research.lexicon_entries_count}\n")

        # Concordance results
        lines.append(f"### Concordance Results\n")
        if self.research.concordance_results:
            lines.append("| Query | Results Count |")
            lines.append("|-------|---------------|")
            for query, count in self.research.concordance_results.items():
                lines.append(f"| {query} | {count} |")
            total_conc = sum(self.research.concordance_results.values())
            lines.append(f"\n**Total concordance results**: {total_conc}\n")
        else:
            lines.append("*No concordance results.*\n")

        # Figurative language results
        lines.append(f"### Figurative Language Results\n")
        if self.research.figurative_results:
            lines.append("| Query/Verse | Instances Found |")
            lines.append("|-------------|-----------------|")
            for key, count in self.research.figurative_results.items():
                lines.append(f"| {key} | {count} |")
            total_fig = sum(self.research.figurative_results.values())
            lines.append(f"\n**Total figurative instances**: {total_fig}\n")
        else:
            lines.append("*No figurative language results.*\n")

        # Commentary results
        lines.append(f"### Commentary Results\n")
        if self.research.commentary_counts:
            lines.append("| Commentator | Entries |")
            lines.append("|-------------|---------|")
            for commentator, count in sorted(self.research.commentary_counts.items()):
                lines.append(f"| {commentator} | {count} |")
            total_comm = sum(self.research.commentary_counts.values())
            lines.append(f"\n**Total commentary entries**: {total_comm}\n")
        else:
            lines.append("*No commentary results.*\n")

        # Ugaritic parallels
        lines.append(f"### Ugaritic & Ancient Near Eastern Parallels\n")
        if self.research.ugaritic_parallels:
            lines.append(f"**Total parallels**: {len(self.research.ugaritic_parallels)}\n")
            lines.append("| Type | Reference | Analysis Preview |")
            lines.append("|------|-----------|------------------|")
            for parallel in self.research.ugaritic_parallels:
                ptype = parallel.get('type', 'N/A')
                ref = parallel.get('reference', 'N/A')
                analysis = parallel.get('analysis', '')
                lines.append(f"| {ptype} | {ref} | {analysis} |")
        else:
            lines.append("*No Ugaritic parallels found.*")

        lines.append("\n---\n")

        # Section 4: Analysis Questions
        lines.append("## Analysis Questions\n")

        # Macro questions
        lines.append(f"### MacroAnalyst Research Questions ({len(self.analysis.macro_questions)})\n")
        if self.analysis.macro_questions:
            for i, q in enumerate(self.analysis.macro_questions, 1):
                lines.append(f"{i}. {q}")
        else:
            lines.append("*No macro research questions.*")

        lines.append("")

        # Micro questions
        lines.append(f"### MicroAnalyst Interesting Questions ({len(self.analysis.micro_questions)})\n")
        if self.analysis.micro_questions:
            for i, q in enumerate(self.analysis.micro_questions, 1):
                lines.append(f"{i}. {q}")
        else:
            lines.append("*No micro research questions.*")

        lines.append("\n---\n")

        # Section 5: Token Usage Summary
        lines.append("## Token Usage Summary\n")

        total_input_tokens = sum(step.input_token_estimate for step in self.steps.values())
        total_output_tokens = sum(step.output_token_estimate for step in self.steps.values())
        total_tokens = total_input_tokens + total_output_tokens

        lines.append(f"**Total Input Tokens (estimated)**: {total_input_tokens:,}")
        lines.append(f"**Total Output Tokens (estimated)**: {total_output_tokens:,}")
        lines.append(f"**Total Tokens (estimated)**: {total_tokens:,}\n")

        lines.append("*Note: Token estimates are approximate (character count / 3). Actual API usage may vary.*")

        lines.append("\n---\n")

        # Footer
        lines.append(f"\n*Report generated by PipelineSummaryTracker*")
        lines.append(f"*Psalm {self.psalm_number} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(lines)

    def save_report(self, output_dir: str) -> Path:
        """
        Save markdown report to file.

        Args:
            output_dir: Output directory path

        Returns:
            Path to saved report file
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        report_file = output_path / f"psalm_{self.psalm_number:03d}_pipeline_summary.md"
        report_content = self.generate_markdown_report()

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return report_file

    def to_dict(self) -> Dict[str, Any]:
        """Export tracker data as dictionary for JSON serialization."""
        return {
            'psalm_number': self.psalm_number,
            'pipeline_start': self.pipeline_start.isoformat(),
            'pipeline_end': self.pipeline_end.isoformat() if self.pipeline_end else None,
            'steps': {
                name: {
                    'input_char_count': step.input_char_count,
                    'input_token_estimate': step.input_token_estimate,
                    'output_char_count': step.output_char_count,
                    'output_token_estimate': step.output_token_estimate,
                    'duration_seconds': step.duration_seconds, 
                    'completion_date': getattr(step, 'completion_date', None),
                    'timestamp': step.timestamp
                }
                for name, step in self.steps.items()
            },
            'research': {
                'lexicon_requests': self.research.lexicon_requests,
                'concordance_requests': self.research.concordance_requests,
                'figurative_requests': self.research.figurative_requests,
                'commentary_requests': self.research.commentary_requests,
                'lexicon_entries_count': self.research.lexicon_entries_count,
                'concordance_results': self.research.concordance_results,
                'figurative_results': self.research.figurative_results,
                'commentary_counts': self.research.commentary_counts,
                'sacks_references_count': self.research.sacks_references_count,
                'related_psalms_count': self.research.related_psalms_count,
                'ugaritic_parallels': self.research.ugaritic_parallels,
                'research_bundle_chars': self.research.research_bundle_chars,
                'research_bundle_tokens': self.research.research_bundle_tokens
            },
            'analysis': {
                'macro_questions': self.analysis.macro_questions,
                'micro_questions': self.analysis.micro_questions,
                'verse_count': self.analysis.verse_count,
            },
            'model_usage': self.model_usage
        }

    def save_json(self, output_dir: str) -> Path:
        """
        Save tracker data as JSON file.

        Args:
            output_dir: Output directory path

        Returns:
            Path to saved JSON file
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        json_file = output_path / f"psalm_{self.psalm_number:03d}_pipeline_stats.json"

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

        return json_file


def main():
    """Command-line interface for testing."""
    import argparse

    parser = argparse.ArgumentParser(description='Pipeline Summary Tracker Test')
    parser.add_argument('--psalm', type=int, default=23, help='Psalm number')
    parser.add_argument('--output-dir', type=str, default='output/test', help='Output directory')

    args = parser.parse_args()

    # Create sample tracker
    tracker = PipelineSummaryTracker(psalm_number=args.psalm)

    # Add sample data
    tracker.track_step_input("macro_analysis", "Sample input" * 1000)
    tracker.track_step_output("macro_analysis", "Sample output" * 500, duration=45.3)

    tracker.track_step_input("micro_analysis", "Sample input" * 1500)
    tracker.track_step_output("micro_analysis", "Sample output" * 800, duration=67.8)

    tracker.track_macro_questions([
        "What is the significance of the shepherd imagery?",
        "How does the psalm structure contribute to its meaning?"
    ])

    tracker.track_micro_questions([
        "Why does the poet use 'green pastures' specifically?",
        "What is the function of the 'valley of shadow' metaphor?"
    ])

    tracker.mark_pipeline_complete()

    # Generate and save report
    report_file = tracker.save_report(args.output_dir)
    json_file = tracker.save_json(args.output_dir)

    print(f"\nSample report saved to: {report_file}")
    print(f"Sample JSON saved to: {json_file}")
    print("\nPreview of report:\n")
    print(tracker.generate_markdown_report()[:1000] + "\n...\n")


if __name__ == '__main__':
    main()
