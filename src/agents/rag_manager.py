"""
RAG Manager: Retrieval-Augmented Generation Document Manager
Phase 2d: Provides contextual scholarly documents to Scholar-Researcher and Scholar-Writer agents

This module manages three types of RAG documents:
1. Analytical Framework (always included) - Poetic analysis methodology
2. Psalm Function Database (psalm-specific) - Genre and structure info
3. Ugaritic Comparisons (verse-specific) - Ancient Near Eastern parallels

Author: Claude (Anthropic)
Date: 2025 (Phase 2d)
"""

import json
import re
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass


@dataclass
class RAGContext:
    """Container for RAG documents relevant to a specific psalm/verse"""
    psalm_number: int
    verse_number: Optional[int] = None
    analytical_framework: str = ""
    lxx_text: Optional[str] = None  # Septuagint (Greek) translation


class RAGManager:
    """
    Manages loading and filtering of RAG documents for psalm commentary generation.

    The RAG Manager provides three types of contextual documents:
    - Analytical Framework: Always included, provides poetic analysis methodology
    - Psalm Function: Psalm-specific genre, structure, and keywords
    - Ugaritic Comparisons: Verse-specific ancient Near Eastern parallels
    """

    def __init__(self, docs_dir: str = "docs"):
        """
        Initialize RAG Manager with paths to RAG documents.

        Args:
            docs_dir: Path to directory containing RAG documents
        """
        self.docs_dir = Path(docs_dir)

        # File paths (updated for new docs organization - Session 181)
        self.analytical_framework_path = self.docs_dir / "architecture" / "analytical_framework_for_RAG.md"

        # Cache for loaded documents
        self._analytical_framework: Optional[str] = None

        # Verify files exist
        self._verify_files()

    def _verify_files(self) -> None:
        """Verify that all required RAG files exist."""
        if not self.analytical_framework_path.exists():
            raise FileNotFoundError(
                f"Analytical Framework not found: {self.analytical_framework_path}"
            )

    def load_analytical_framework(self) -> str:
        """
        Load the Analytical Framework document.
        This is always included for Scholar-Writer agents.

        Returns:
            Full text of analytical framework document
        """
        if self._analytical_framework is None:
            with open(self.analytical_framework_path, 'r', encoding='utf-8') as f:
                self._analytical_framework = f.read()

        return self._analytical_framework

    # (Psalm function and Ugaritic DBs removed)

    def get_rag_context(self, psalm_number: int, verse_number: Optional[int] = None) -> RAGContext:
        """
        Get complete RAG context for a psalm or specific verse.
        This is the main method used by other agents.

        Args:
            psalm_number: Psalm number (1-150)
            verse_number: Optional verse number for verse-specific context

        Returns:
            RAGContext object with all relevant documents
        """
        # Fetch LXX text (Septuagint Greek translation)
        from ..data_sources.sefaria_client import SefariaClient
        sefaria = SefariaClient()

        lxx_verses = sefaria.fetch_lxx_psalm(psalm_number)

        # If verse_number specified, get that verse only
        if verse_number and lxx_verses and verse_number <= len(lxx_verses):
            lxx_text = f"v{verse_number}: {lxx_verses[verse_number - 1]}"
        elif lxx_verses:
            # Full psalm - format as multi-line with verse numbers
            lxx_text = "\n".join([f"v{i}: {v}" for i, v in enumerate(lxx_verses, 1) if v])
        else:
            lxx_text = None

        context = RAGContext(
            psalm_number=psalm_number,
            verse_number=verse_number,
            analytical_framework=self.load_analytical_framework(),
            lxx_text=lxx_text
        )

        return context

    def format_for_prompt(self, context: RAGContext, include_framework: bool = True) -> str:
        """
        Format RAG context into a text prompt suitable for LLM agents.

        Args:
            context: RAGContext object
            include_framework: Whether to include full analytical framework (can be large)

        Returns:
            Formatted text ready to inject into agent prompts
        """
        sections = []

        # Section 2: LXX Translation (Septuagint)
        if context.lxx_text:
            sections.append("\n## LXX (SEPTUAGINT - GREEK TRANSLATION)")
            sections.append("Ancient Greek translation (3rd-2nd century BCE) showing early interpretive tradition:")
            sections.append(context.lxx_text)

        # Section 4: Analytical Framework (optional, can be large)
        if include_framework:
            sections.append("\n## ANALYTICAL FRAMEWORK FOR BIBLICAL POETRY")
            sections.append(context.analytical_framework)

        return "\n".join(sections)


# Convenience function for quick access
def get_rag_context(psalm_number: int, verse_number: Optional[int] = None, docs_dir: str = "docs") -> RAGContext:
    """
    Convenience function to quickly get RAG context without creating a manager instance.

    Args:
        psalm_number: Psalm number (1-150)
        verse_number: Optional verse number
        docs_dir: Path to docs directory

    Returns:
        RAGContext object
    """
    manager = RAGManager(docs_dir)
    return manager.get_rag_context(psalm_number, verse_number)


if __name__ == "__main__":
    # Test the RAG Manager
    print("Testing RAG Manager...")
    print("=" * 80)

    manager = RAGManager()
    context = manager.get_rag_context(29)

    print(f"Psalm: {context.psalm_number}")

    # Test Format for prompt
    print("\n[Test] Formatted prompt (without full framework)")
    formatted = manager.format_for_prompt(context, include_framework=False)
    print(formatted[:500] + "..." if len(formatted) > 500 else formatted)

    print("\n" + "=" * 80)
    print("RAG Manager tests complete!")
