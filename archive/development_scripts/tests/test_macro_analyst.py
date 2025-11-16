"""
Tests for MacroAnalyst Agent (Pass 1)
Phase 3a: Macro-level analysis testing

Tests the MacroAnalyst agent with Psalm 29 to verify:
- RAG integration (genre, Ugaritic parallels)
- Thesis generation
- Structural analysis
- Poetic device identification
- Research question generation

Author: Claude (Anthropic)
Date: 2025 (Phase 3a)
"""

import sys
import os
from pathlib import Path
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.macro_analyst import MacroAnalyst
from src.schemas.analysis_schemas import MacroAnalysis
from src.agents.rag_manager import RAGManager
from src.data_sources.tanakh_database import TanakhDatabase


class TestMacroAnalyst:
    """Tests for MacroAnalyst agent."""

    @pytest.fixture
    def analyst(self):
        """Create MacroAnalyst instance for testing."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")
        return MacroAnalyst(api_key=api_key)

    @pytest.fixture
    def db(self):
        """Create TanakhDatabase instance."""
        return TanakhDatabase()

    @pytest.fixture
    def rag_manager(self):
        """Create RAGManager instance."""
        return RAGManager()

    def test_database_has_psalm_29(self, db):
        """Verify Psalm 29 is in database."""
        psalm = db.get_psalm(29)
        assert psalm is not None, "Psalm 29 not found in database"
        assert psalm.chapter == 29
        assert psalm.verse_count > 0
        print(f"\nPsalm 29 has {psalm.verse_count} verses")

    def test_rag_context_psalm_29(self, rag_manager):
        """Verify RAG context loads correctly for Psalm 29."""
        context = rag_manager.get_rag_context(29)

        # Check psalm function data
        assert context.psalm_function is not None
        assert context.psalm_function['psalm'] == 29
        assert 'genre' in context.psalm_function
        assert 'structure' in context.psalm_function

        print(f"\nPsalm 29 Genre: {context.psalm_function['genre']}")
        print(f"Structure divisions: {len(context.psalm_function['structure'])}")

        # Check Ugaritic parallels
        assert len(context.ugaritic_parallels) > 0, "Expected Ugaritic parallels for Psalm 29"
        print(f"Ugaritic parallels found: {len(context.ugaritic_parallels)}")

        for parallel in context.ugaritic_parallels:
            print(f"  - {parallel['entry_id']}: {parallel['parallel_type']}")

        # Check analytical framework
        assert len(context.analytical_framework) > 0
        print(f"Analytical framework length: {len(context.analytical_framework)} chars")

    def test_macro_analysis_psalm_29(self, analyst):
        """
        Full integration test: Run macro analysis on Psalm 29.

        This test will make an actual API call to Claude Sonnet 4.5.
        Expected cost: ~$0.05-0.10 per run.
        """
        print("\n" + "=" * 80)
        print("RUNNING MACRO ANALYSIS ON PSALM 29")
        print("This will make an API call to Claude Sonnet 4.5 (~30-60 seconds)")
        print("=" * 80)

        # Run analysis
        analysis = analyst.analyze_psalm(29)

        # Validate structure
        assert isinstance(analysis, MacroAnalysis)
        assert analysis.psalm_number == 29

        # Validate thesis
        assert len(analysis.thesis_statement) > 0
        assert len(analysis.thesis_statement.split()) >= 20, "Thesis should be 2-3 sentences minimum"
        print("\nTHESIS:")
        print(analysis.thesis_statement)

        # Validate genre
        assert len(analysis.genre) > 0
        print(f"\nGENRE: {analysis.genre}")

        # Validate historical context
        assert len(analysis.historical_context) > 0
        print(f"\nHISTORICAL CONTEXT:")
        print(analysis.historical_context[:200] + "...")

        # Validate structural outline
        assert len(analysis.structural_outline) >= 2, "Expected at least 2 structural divisions"
        print(f"\nSTRUCTURAL OUTLINE ({len(analysis.structural_outline)} divisions):")
        for i, div in enumerate(analysis.structural_outline, 1):
            print(f"  {i}. {div.section}: {div.theme}")
            assert len(div.section) > 0
            assert len(div.theme) > 0

        # Validate poetic devices
        assert len(analysis.poetic_devices) >= 1, "Expected at least 1 poetic device"
        print(f"\nPOETIC DEVICES ({len(analysis.poetic_devices)} identified):")
        for device in analysis.poetic_devices:
            print(f"  - {device.device}: {device.description}")
            print(f"    Verses: {device.verses}")
            print(f"    Function: {device.function}")
            assert len(device.device) > 0
            assert len(device.description) > 0

        # Validate research questions
        assert len(analysis.research_questions) >= 3, "Expected at least 3 research questions"
        print(f"\nRESEARCH QUESTIONS ({len(analysis.research_questions)}):")
        for i, q in enumerate(analysis.research_questions, 1):
            print(f"  {i}. {q}")
            assert len(q) > 0

        # Test serialization
        print("\nTESTING SERIALIZATION...")
        json_output = analysis.to_json()
        assert len(json_output) > 0
        print(f"JSON length: {len(json_output)} chars")

        markdown_output = analysis.to_markdown()
        assert len(markdown_output) > 0
        print(f"Markdown length: {len(markdown_output)} chars")

        # Validate specific expectations for Psalm 29
        print("\nVALIDATING PSALM 29 SPECIFIC FEATURES...")

        # Should identify hymn/praise genre
        assert any(word in analysis.genre.lower() for word in ['hymn', 'praise']), \
            f"Expected hymn/praise genre, got: {analysis.genre}"

        # Should mention "voice of the LORD" anaphora
        anaphora_found = any(
            'anaphora' in device.device.lower() and 'voice' in device.description.lower()
            for device in analysis.poetic_devices
        )
        assert anaphora_found, "Expected identification of 'voice of the LORD' anaphora"

        # Should mention Ugaritic/ANE context
        ane_context = any(
            word in analysis.historical_context.lower()
            for word in ['ugaritic', 'baal', 'ancient near east', 'ane', 'canaanite']
        )
        assert ane_context, "Expected mention of Ugaritic/ANE context"

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED FOR PSALM 29 MACRO ANALYSIS")
        print("=" * 80)

    def test_save_analysis(self, analyst, tmp_path):
        """Test saving analysis to files."""
        print("\nTesting file save functionality...")

        # Run analysis and save
        analysis = analyst.analyze_and_save(
            psalm_number=29,
            output_dir=str(tmp_path),
            save_format="both"
        )

        # Check JSON file
        json_file = tmp_path / "psalm_029_macro.json"
        assert json_file.exists(), "JSON file not created"
        json_content = json_file.read_text(encoding='utf-8')
        assert len(json_content) > 0
        print(f"JSON file: {json_file} ({len(json_content)} bytes)")

        # Check markdown file
        md_file = tmp_path / "psalm_029_macro.md"
        assert md_file.exists(), "Markdown file not created"
        md_content = md_file.read_text(encoding='utf-8')
        assert len(md_content) > 0
        print(f"Markdown file: {md_file} ({len(md_content)} bytes)")

        # Verify content
        assert "Psalm 29" in md_content
        assert analysis.thesis_statement in md_content


def test_schema_serialization():
    """Test MacroAnalysis schema serialization without API calls."""
    from src.schemas.analysis_schemas import MacroAnalysis, StructuralDivision, PoeticDevice

    # Create sample analysis
    analysis = MacroAnalysis(
        psalm_number=29,
        thesis_statement="Test thesis about Yahweh's power over storm.",
        genre="Hymn of Praise",
        historical_context="Ancient Near Eastern context",
        structural_outline=[
            StructuralDivision(
                section="vv. 1-2",
                theme="Divine Council worship",
                notes="Heavenly beings summoned"
            )
        ],
        poetic_devices=[
            PoeticDevice(
                device="anaphora",
                description="Seven-fold 'voice of the LORD'",
                verses="vv. 3-9",
                function="Emphasizes divine power"
            )
        ],
        research_questions=[
            "How does the seven-fold voice relate to creation?",
            "What Ugaritic parallels exist?"
        ]
    )

    # Test JSON serialization
    json_str = analysis.to_json()
    assert "psalm_number" in json_str
    assert "thesis_statement" in json_str

    # Test round-trip
    import json
    data = json.loads(json_str)
    restored = MacroAnalysis.from_dict(data)
    assert restored.psalm_number == 29
    assert restored.thesis_statement == analysis.thesis_statement
    assert len(restored.structural_outline) == 1
    assert len(restored.poetic_devices) == 1

    # Test markdown export
    md = analysis.to_markdown()
    assert "# Macro Analysis: Psalm 29" in md
    assert "Test thesis" in md
    assert "anaphora" in md.lower()

    print("✅ Schema serialization tests passed")


if __name__ == "__main__":
    """Run tests manually."""
    print("MacroAnalyst Tests")
    print("=" * 80)

    # Ensure UTF-8 for Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    # Test 1: Schema serialization (no API call)
    print("\n[Test 1] Schema Serialization")
    test_schema_serialization()

    # Test 2: Database check
    print("\n[Test 2] Database Check")
    test = TestMacroAnalyst()
    db = TanakhDatabase()
    test.test_database_has_psalm_29(db)
    db.close()

    # Test 3: RAG context
    print("\n[Test 3] RAG Context")
    rag_manager = RAGManager()
    test.test_rag_context_psalm_29(rag_manager)

    # Test 4: Full macro analysis (API call - costs money!)
    print("\n[Test 4] Full Macro Analysis")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        analyst = MacroAnalyst(api_key=api_key)
        try:
            test.test_macro_analysis_psalm_29(analyst)
        finally:
            analyst.close()
    else:
        print("⚠️  ANTHROPIC_API_KEY not set - skipping API test")

    print("\n" + "=" * 80)
    print("Test suite complete!")
