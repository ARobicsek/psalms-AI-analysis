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
    psalm_function: Optional[Dict[str, Any]] = None
    ugaritic_parallels: List[Dict[str, Any]] = None
    lxx_text: Optional[str] = None  # Septuagint (Greek) translation

    def __post_init__(self):
        if self.ugaritic_parallels is None:
            self.ugaritic_parallels = []


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

        # File paths
        self.analytical_framework_path = self.docs_dir / "analytical_framework_for_RAG.md"
        self.psalm_function_path = self.docs_dir / "psalm_function_for_RAG.json"
        self.ugaritic_path = self.docs_dir / "ugaritic.json"

        # Cache for loaded documents
        self._analytical_framework: Optional[str] = None
        self._psalm_function_db: Optional[List[Dict]] = None
        self._ugaritic_db: Optional[List[Dict]] = None

        # Verify files exist
        self._verify_files()

    def _verify_files(self) -> None:
        """Verify that all required RAG files exist."""
        if not self.analytical_framework_path.exists():
            raise FileNotFoundError(
                f"Analytical Framework not found: {self.analytical_framework_path}"
            )
        if not self.psalm_function_path.exists():
            raise FileNotFoundError(
                f"Psalm Function database not found: {self.psalm_function_path}"
            )
        if not self.ugaritic_path.exists():
            raise FileNotFoundError(
                f"Ugaritic Comparisons database not found: {self.ugaritic_path}"
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

    def load_psalm_function_db(self) -> List[Dict]:
        """
        Load and parse the Psalm Function JSON database.

        Returns:
            List of psalm function entries (one per psalm)
        """
        if self._psalm_function_db is None:
            with open(self.psalm_function_path, 'r', encoding='utf-8') as f:
                self._psalm_function_db = json.load(f)

        return self._psalm_function_db

    def load_ugaritic_db(self) -> List[Dict]:
        """
        Load and parse the Ugaritic Comparisons JSON database.

        Returns:
            List of Ugaritic parallel entries
        """
        if self._ugaritic_db is None:
            with open(self.ugaritic_path, 'r', encoding='utf-8') as f:
                self._ugaritic_db = json.load(f)

        return self._ugaritic_db

    def get_psalm_function(self, psalm_number: int) -> Optional[Dict[str, Any]]:
        """
        Get function/genre information for a specific psalm.

        Args:
            psalm_number: Psalm number (1-150)

        Returns:
            Psalm function entry with genre, structure, keywords, or None if not found
        """
        db = self.load_psalm_function_db()

        for entry in db:
            if entry.get("psalm") == psalm_number:
                return entry

        return None

    def get_ugaritic_parallels(self, psalm_number: int, verse_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get Ugaritic parallels for a specific psalm or psalm:verse.

        Args:
            psalm_number: Psalm number
            verse_number: Optional verse number for more specific filtering

        Returns:
            List of relevant Ugaritic parallel entries
        """
        db = self.load_ugaritic_db()
        matches = []

        for entry in db:
            # Extract psalm reference from hebrew_psalter_source.text_reference
            text_ref = entry.get("hebrew_psalter_source", {}).get("text_reference", "")

            # Parse reference like "Psalm 29:1" or "Psalm 48:3 [Eng. 48:2]"
            psalm_match = re.search(r'Psalm\s+(\d+)(?::(\d+))?', text_ref)
            if not psalm_match:
                continue

            ref_psalm = int(psalm_match.group(1))
            ref_verse = int(psalm_match.group(2)) if psalm_match.group(2) else None

            # Filter by psalm number
            if ref_psalm != psalm_number:
                continue

            # If verse_number specified, filter by verse too
            if verse_number is not None and ref_verse is not None:
                if ref_verse == verse_number:
                    matches.append(entry)
            else:
                # No verse specified, include all matches for this psalm
                matches.append(entry)

        return matches

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
            psalm_function=self.get_psalm_function(psalm_number),
            ugaritic_parallels=self.get_ugaritic_parallels(psalm_number, verse_number),
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

        # Section 1: Psalm Function/Genre
        if context.psalm_function:
            pf = context.psalm_function
            sections.append("## PSALM FUNCTION & GENRE")
            sections.append(f"Psalm {pf['psalm']}: {pf['genre']}")
            sections.append(f"\nStructure:")
            for line in pf['structure']:
                sections.append(f"  - {line}")
            sections.append(f"\nKeywords: {', '.join(pf['keywords'])}")

        # Section 2: LXX Translation (Septuagint)
        if context.lxx_text:
            sections.append("\n## LXX (SEPTUAGINT - GREEK TRANSLATION)")
            sections.append("Ancient Greek translation (3rd-2nd century BCE) showing early interpretive tradition:")
            sections.append(context.lxx_text)

        # Section 3: Ugaritic Parallels (if any)
        if context.ugaritic_parallels:
            sections.append("\n## UGARITIC & ANCIENT NEAR EASTERN PARALLELS")
            for i, parallel in enumerate(context.ugaritic_parallels, 1):
                sections.append(f"\n### Parallel {i}: {parallel.get('parallel_type', 'Unknown')}")
                sections.append(f"Entry ID: {parallel.get('entry_id')}")

                # Hebrew source
                heb = parallel.get('hebrew_psalter_source', {})
                sections.append(f"\nHebrew Text: {heb.get('text_reference')}")
                sections.append(f"  Transliteration: {heb.get('transliteration')}")
                sections.append(f"  Translation: {heb.get('translation')}")

                # Ugaritic source
                ug = parallel.get('ugaritic_source', {})
                sections.append(f"\nUgaritic Text: {ug.get('text_reference')}")
                sections.append(f"  Transliteration: {ug.get('transliteration')}")
                sections.append(f"  Translation: {ug.get('translation')}")

                # Analysis
                sections.append(f"\nLinguistic Analysis:\n{parallel.get('linguistic_analysis')}")
                sections.append(f"\nConceptual Analysis:\n{parallel.get('conceptual_analysis')}")

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

    # Test 1: Load Psalm 29 (has Ugaritic parallels)
    print("\n[Test 1] Psalm 29 - Should have Ugaritic parallels")
    manager = RAGManager()
    context = manager.get_rag_context(29)

    print(f"Psalm: {context.psalm_number}")
    print(f"Genre: {context.psalm_function['genre'] if context.psalm_function else 'N/A'}")
    print(f"Ugaritic Parallels Found: {len(context.ugaritic_parallels)}")

    if context.ugaritic_parallels:
        for p in context.ugaritic_parallels:
            print(f"  - {p['entry_id']}: {p['parallel_type']}")

    # Test 2: Psalm 29:1 specifically
    print("\n[Test 2] Psalm 29:1 - Specific verse lookup")
    context_v1 = manager.get_rag_context(29, 1)
    print(f"Ugaritic Parallels for Psalm 29:1: {len(context_v1.ugaritic_parallels)}")

    # Test 3: Format for prompt
    print("\n[Test 3] Formatted prompt (without full framework)")
    formatted = manager.format_for_prompt(context_v1, include_framework=False)
    print(formatted[:500] + "..." if len(formatted) > 500 else formatted)

    print("\n" + "=" * 80)
    print("RAG Manager tests complete!")
