"""
Analysis Schemas for Scholar-Writer Agents
Phase 3: Three-Pass Telescopic Analysis System

This module defines the data structures for the three-pass writing system:
- Pass 1 (MacroAnalysis): Chapter-level thesis and structural analysis
- Pass 2 (MicroAnalysis): Verse-by-verse detailed commentary
- Pass 3 (SynthesisOutput): Polished scholarly essay

Author: Claude (Anthropic)
Date: 2025 (Phase 3)
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
import json


@dataclass
class StructuralDivision:
    """Represents a major structural division in the psalm."""
    section: str  # e.g., "vv. 1-2", "vv. 3-9", "vv. 10-11"
    theme: str  # Brief description of this section's theme
    notes: str = ""  # Additional observations


@dataclass
class PoeticDevice:
    """Represents a poetic technique identified in the psalm."""
    device: str  # e.g., "anaphora", "chiasmus", "inclusio"
    description: str  # How it's used in the psalm
    verses: str = ""  # Where it appears (e.g., "vv. 3-9")
    function: str = ""  # What purpose it serves


@dataclass
class MacroAnalysis:
    """
    Output from Pass 1: Macro Analysis Agent.

    Provides high-level thesis and structural framework that guides
    subsequent micro analysis and synthesis.
    """
    psalm_number: int
    thesis_statement: str  # Overall argument/interpretation (2-3 sentences)
    genre: str  # From RAG or analyst's determination
    historical_context: str  # Brief historical/theological setting
    structural_outline: List[StructuralDivision] = field(default_factory=list)
    poetic_devices: List[PoeticDevice] = field(default_factory=list)
    research_questions: List[str] = field(default_factory=list)  # Questions for Pass 2
    working_notes: str = ""  # Raw analytical thinking from extended mode

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MacroAnalysis':
        """Create from dictionary/JSON."""
        # Convert nested structures
        structural_outline = [
            StructuralDivision(**div) if isinstance(div, dict) else div
            for div in data.get('structural_outline', [])
        ]
        poetic_devices = [
            PoeticDevice(**dev) if isinstance(dev, dict) else dev
            for dev in data.get('poetic_devices', [])
        ]

        return cls(
            psalm_number=data['psalm_number'],
            thesis_statement=data.get('thesis_statement', ''),
            genre=data.get('genre', ''),
            historical_context=data.get('historical_context', ''),
            structural_outline=structural_outline,
            poetic_devices=poetic_devices,
            research_questions=data.get('research_questions', []),
            working_notes=data.get('working_notes', '')
        )

    def to_markdown(self) -> str:
        """Format as markdown for human reading and Pass 2 input."""
        lines = [
            f"# Macro Analysis: Psalm {self.psalm_number}",
            "",
            "## Thesis Statement",
            self.thesis_statement,
            "",
            f"## Genre",
            self.genre,
            "",
            "## Historical/Theological Context",
            self.historical_context,
            "",
            "## Structural Outline"
        ]

        for i, div in enumerate(self.structural_outline, 1):
            lines.append(f"\n### {i}. {div.section}: {div.theme}")
            if div.notes:
                lines.append(div.notes)

        if self.poetic_devices:
            lines.append("\n## Key Poetic Devices")
            for device in self.poetic_devices:
                lines.append(f"\n### {device.device.title()}")
                lines.append(f"**Description**: {device.description}")
                if device.verses:
                    lines.append(f"**Verses**: {device.verses}")
                if device.function:
                    lines.append(f"**Function**: {device.function}")

        if self.research_questions:
            lines.append("\n## Research Questions for Pass 2")
            for i, question in enumerate(self.research_questions, 1):
                lines.append(f"{i}. {question}")

        if self.working_notes:
            lines.append("\n## Working Notes")
            lines.append(self.working_notes)

        return "\n".join(lines)


@dataclass
class VerseCommentary:
    """Detailed commentary for a single verse from Pass 2."""
    verse_number: int
    commentary: str  # Full verse-by-verse analysis
    lexical_insights: List[str] = field(default_factory=list)  # Key words analyzed
    figurative_analysis: List[str] = field(default_factory=list)  # Metaphors, etc.
    thesis_connection: str = ""  # How this verse supports overall thesis


@dataclass
class MicroAnalysis:
    """
    Output from Pass 2: Micro Analysis Agent.

    Provides detailed verse-by-verse commentary building on macro thesis.
    """
    psalm_number: int
    verse_commentaries: List[VerseCommentary] = field(default_factory=list)
    thematic_threads: List[str] = field(default_factory=list)  # Themes across verses
    interesting_questions: List[str] = field(default_factory=list)  # Questions about words, phrases, devices
    synthesis_notes: str = ""  # Notes for Pass 3 synthesis

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MicroAnalysis':
        """Create from dictionary/JSON."""
        verse_commentaries = [
            VerseCommentary(**vc) if isinstance(vc, dict) else vc
            for vc in data.get('verse_commentaries', [])
        ]

        return cls(
            psalm_number=data['psalm_number'],
            verse_commentaries=verse_commentaries,
            thematic_threads=data.get('thematic_threads', []),
            interesting_questions=data.get('interesting_questions', []),
            synthesis_notes=data.get('synthesis_notes', '')
        )

    def to_markdown(self) -> str:
        """Format as markdown for human reading and Pass 3 input."""
        lines = [
            f"# Micro Analysis: Psalm {self.psalm_number}",
            "",
            "## Verse-by-Verse Commentary"
        ]

        for vc in self.verse_commentaries:
            lines.append(f"\n### Verse {vc.verse_number}")
            lines.append(vc.commentary)

            if vc.lexical_insights:
                lines.append("\n**Lexical Insights:**")
                for insight in vc.lexical_insights:
                    lines.append(f"- {insight}")

            if vc.figurative_analysis:
                lines.append("\n**Figurative Analysis:**")
                for analysis in vc.figurative_analysis:
                    lines.append(f"- {analysis}")

            if vc.thesis_connection:
                lines.append(f"\n**Connection to Thesis:** {vc.thesis_connection}")

        if self.thematic_threads:
            lines.append("\n## Thematic Threads")
            for i, thread in enumerate(self.thematic_threads, 1):
                lines.append(f"{i}. {thread}")

        if self.interesting_questions:
            lines.append("\n## Interesting Questions")
            for i, question in enumerate(self.interesting_questions, 1):
                lines.append(f"{i}. {question}")

        if self.synthesis_notes:
            lines.append("\n## Notes for Synthesis")
            lines.append(self.synthesis_notes)

        return "\n".join(lines)


@dataclass
class SynthesisOutput:
    """
    Output from Pass 3: Synthesis Agent.

    Provides polished scholarly essay integrating macro and micro analysis.
    """
    psalm_number: int
    title: str  # Essay title
    essay: str  # Complete polished essay
    sources_cited: List[str] = field(default_factory=list)  # BDB entries, commentaries used
    word_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SynthesisOutput':
        """Create from dictionary/JSON."""
        return cls(
            psalm_number=data['psalm_number'],
            title=data.get('title', ''),
            essay=data.get('essay', ''),
            sources_cited=data.get('sources_cited', []),
            word_count=data.get('word_count', 0)
        )

    def to_markdown(self) -> str:
        """Format as markdown for final output."""
        lines = [
            f"# {self.title}",
            "",
            self.essay,
            ""
        ]

        if self.sources_cited:
            lines.append("\n## Sources")
            for source in self.sources_cited:
                lines.append(f"- {source}")

        lines.append(f"\n---")
        lines.append(f"*Psalm {self.psalm_number} | {self.word_count} words*")

        return "\n".join(lines)


@dataclass
class CriticFeedback:
    """
    Output from Critic Agent.

    Provides structured feedback on synthesis quality.
    """
    psalm_number: int
    overall_assessment: str  # General evaluation
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    specific_suggestions: List[str] = field(default_factory=list)
    telescopic_integration_score: int = 0  # 1-10 scale

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CriticFeedback':
        """Create from dictionary/JSON."""
        return cls(
            psalm_number=data['psalm_number'],
            overall_assessment=data.get('overall_assessment', ''),
            strengths=data.get('strengths', []),
            weaknesses=data.get('weaknesses', []),
            specific_suggestions=data.get('specific_suggestions', []),
            telescopic_integration_score=data.get('telescopic_integration_score', 0)
        )

    def to_markdown(self) -> str:
        """Format as markdown for review."""
        lines = [
            f"# Critic Feedback: Psalm {self.psalm_number}",
            "",
            f"**Telescopic Integration Score**: {self.telescopic_integration_score}/10",
            "",
            "## Overall Assessment",
            self.overall_assessment,
            ""
        ]

        if self.strengths:
            lines.append("## Strengths")
            for strength in self.strengths:
                lines.append(f"- {strength}")
            lines.append("")

        if self.weaknesses:
            lines.append("## Weaknesses")
            for weakness in self.weaknesses:
                lines.append(f"- {weakness}")
            lines.append("")

        if self.specific_suggestions:
            lines.append("## Specific Suggestions")
            for i, suggestion in enumerate(self.specific_suggestions, 1):
                lines.append(f"{i}. {suggestion}")

        return "\n".join(lines)


# Convenience functions for loading/saving
def save_analysis(analysis: Any, filepath: str, format: str = "json") -> None:
    """
    Save any analysis object to file.

    Args:
        analysis: MacroAnalysis, MicroAnalysis, SynthesisOutput, or CriticFeedback
        filepath: Output file path
        format: "json" or "markdown"
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        if format == "json":
            f.write(analysis.to_json())
        elif format == "markdown":
            f.write(analysis.to_markdown())
        else:
            raise ValueError(f"Unknown format: {format}")


def load_macro_analysis(filepath: str) -> MacroAnalysis:
    """Load MacroAnalysis from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return MacroAnalysis.from_dict(data)


def load_micro_analysis(filepath: str) -> MicroAnalysis:
    """Load MicroAnalysis from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return MicroAnalysis.from_dict(data)


def load_synthesis_output(filepath: str) -> SynthesisOutput:
    """Load SynthesisOutput from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return SynthesisOutput.from_dict(data)


def load_critic_feedback(filepath: str) -> CriticFeedback:
    """Load CriticFeedback from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return CriticFeedback.from_dict(data)


if __name__ == "__main__":
    # Test the schemas
    print("Testing Analysis Schemas...")
    print("=" * 80)

    # Test MacroAnalysis
    print("\n[Test 1] MacroAnalysis Creation")
    macro = MacroAnalysis(
        psalm_number=29,
        thesis_statement="Psalm 29 presents Yahweh as supreme over the storm, deliberately echoing and subverting Baal mythology.",
        genre="Hymn of Praise",
        historical_context="Ancient Near Eastern context with Ugaritic parallels",
        structural_outline=[
            StructuralDivision(
                section="vv. 1-2",
                theme="Divine Council summons to worship",
                notes="Heavenly beings commanded to ascribe glory"
            ),
            StructuralDivision(
                section="vv. 3-9",
                theme="Theophany - Voice of the LORD over waters",
                notes="Seven-fold 'voice of the LORD' anaphora"
            ),
            StructuralDivision(
                section="vv. 10-11",
                theme="Yahweh enthroned, blessing his people",
                notes="Shifts from cosmic power to covenantal care"
            )
        ],
        poetic_devices=[
            PoeticDevice(
                device="anaphora",
                description="'The voice of the LORD' repeated 7x",
                verses="vv. 3-9",
                function="Emphasizes Yahweh's commanding power over creation"
            )
        ],
        research_questions=[
            "How does the seven-fold 'voice' relate to creation accounts?",
            "What Ugaritic parallels exist for divine council imagery?",
            "How does 'strength and peace' conclusion subvert storm god mythology?"
        ]
    )

    print(f"Created MacroAnalysis for Psalm {macro.psalm_number}")
    print(f"Thesis: {macro.thesis_statement[:60]}...")
    print(f"Structural divisions: {len(macro.structural_outline)}")
    print(f"Poetic devices: {len(macro.poetic_devices)}")

    # Test serialization
    print("\n[Test 2] JSON Serialization")
    macro_json = macro.to_json()
    macro_restored = MacroAnalysis.from_dict(json.loads(macro_json))
    print(f"Serialization successful: {macro_restored.psalm_number == 29}")

    # Test markdown export
    print("\n[Test 3] Markdown Export")
    macro_md = macro.to_markdown()
    print(f"Markdown length: {len(macro_md)} characters")
    print("\nFirst 200 chars of markdown:")
    print(macro_md[:200] + "...")

    print("\n" + "=" * 80)
    print("Schema tests complete!")
