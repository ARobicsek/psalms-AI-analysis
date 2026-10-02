"""Session 379: the analytical framework is gone from the writer prompt.

Two things are pinned here, because both failed silently in Session 378 and neither
would raise on its own:

1. The framework block is out of BOTH writer templates, and the SI template is still
   just the V4 template plus its directive section. `str.format()` ignores extra
   kwargs, so a half-finished removal is invisible at runtime.

2. The Session-347 cross-verse observations still reach the writer. Their anchor used to
   be the framework heading (then, from S379, the reader-questions heading), and a missing
   anchor only logged a warning, so removing a heading could drop ~$1.50/psalm of synthesis
   discovery without anything failing. Session 394 replaced the anchor with a template SLOT,
   {cross_verse_observations}, which .format() cannot skip. The SI pipeline once had its own
   hand-copied duplicate of the splice; the block is inherited, and that is asserted below.
"""

import re

from src.agents.master_editor import MasterEditor, MASTER_WRITER_PROMPT_V4
from src.agents.master_editor_si import MasterEditorSI, MASTER_WRITER_PROMPT_SI, SI_SECTION
from src.utils.research_trimmer import ResearchTrimmer

FRAMEWORK_HEADING = "### ANALYTICAL FRAMEWORK (poetic conventions reference)"
OBSERVATIONS_HEADING = "### CROSS-VERSE OBSERVATIONS"
SLOT = "{cross_verse_observations}"


# ---------------------------------------------------------------------------
# 1. the prompt templates
# ---------------------------------------------------------------------------

def test_framework_block_is_gone_from_both_templates():
    for name, template in (("V4", MASTER_WRITER_PROMPT_V4), ("SI", MASTER_WRITER_PROMPT_SI)):
        assert FRAMEWORK_HEADING not in template, f"{name} still has the framework heading"
        assert "{analytical_framework}" not in template, f"{name} still has the placeholder"


def test_si_template_is_v4_plus_the_directive_only():
    """The SI prompt is derived from V4 by a .replace(). If that ever stops being true,
    one template edit no longer covers both pipelines."""
    assert len(MASTER_WRITER_PROMPT_SI) == len(MASTER_WRITER_PROMPT_V4) + len(SI_SECTION)


def test_both_templates_have_the_observations_slot_and_no_reader_questions():
    """Session 394: one slot in each template; reader questions are gone from both."""
    for template in (MASTER_WRITER_PROMPT_V4, MASTER_WRITER_PROMPT_SI):
        assert template.count(SLOT) == 1
        assert "READER QUESTIONS" not in template.upper()
        assert "{reader_questions}" not in template
        assert "Questions for the Reader" not in template


def test_a_template_formatted_without_the_slot_fails_loudly():
    """The point of a slot over an anchor: it cannot go missing in silence."""
    import pytest
    with pytest.raises(KeyError):
        MASTER_WRITER_PROMPT_V4.format(psalm_number=1, psalm_text="", macro_analysis="",
                                       micro_analysis="", research_bundle="",
                                       phonetic_section="", curated_insights="")


# ---------------------------------------------------------------------------
# 2. the cross-verse splice
# ---------------------------------------------------------------------------

class _Editor(MasterEditor):
    """MasterEditor with the constructor's API clients stubbed out."""

    def __init__(self):  # noqa: D107 - test double
        import logging
        self.logger = logging.getLogger("test")
        self._cross_verse_observations = None


class _EditorSI(MasterEditorSI):
    def __init__(self):  # noqa: D107 - test double
        import logging
        self.logger = logging.getLogger("test")
        self._cross_verse_observations = None


def test_observations_block_is_shared_not_duplicated():
    """MasterEditorSI must INHERIT the block. A second copy is what let the SI
    pipeline keep the old anchor and the pre-Session-371 guidance."""
    assert "_cross_verse_observations_block" not in vars(MasterEditorSI)
    assert (
        MasterEditorSI._cross_verse_observations_block
        is MasterEditor._cross_verse_observations_block
    )


def _fill(template, block):
    return template.format(psalm_number=1, psalm_text="TEXT", macro_analysis="MACRO",
                           micro_analysis="MICRO", research_bundle="BUNDLE", phonetic_section="PHON",
                           curated_insights="INSIGHTS", cross_verse_observations=block,
                           special_instruction="SI")


def test_observations_fill_the_slot_after_key_insights():
    for editor, template in ((_Editor(), MASTER_WRITER_PROMPT_V4), (_EditorSI(), MASTER_WRITER_PROMPT_SI)):
        editor._cross_verse_observations = "OBSERVATION ONE\nOBSERVATION TWO"
        block = editor._cross_verse_observations_block()
        assert block.startswith(OBSERVATIONS_HEADING) and "OBSERVATION ONE" in block
        out = _fill(template, block)
        # The layout the old anchor-and-strip produced, byte for byte (verified on the full
        # Ps 77 / Ps 78 prompts in Session 394): insights, blank line, block, then the rule.
        assert "### KEY INSIGHTS TO INCORPORATE\nINSIGHTS\n\n" + block + "\n---\n" in out


def test_block_carries_the_session_371_guidance():
    """The SI copy once said "do NOT structure your commentary around them", the
    wording that suppressed the best idea in the Ps 71 dossier under Opus 5."""
    editor = _EditorSI()
    editor._cross_verse_observations = "OBS"
    out = editor._cross_verse_observations_block()
    assert "do NOT structure your commentary around them" not in out
    assert "SHOULD carry your essay" in out


def test_no_observations_leaves_an_empty_slot():
    editor = _Editor()
    assert editor._cross_verse_observations_block() == ""
    assert "### KEY INSIGHTS TO INCORPORATE\nINSIGHTS\n\n\n---\n" in _fill(MASTER_WRITER_PROMPT_V4, "")


# ---------------------------------------------------------------------------
# 3. the legacy bundles
# ---------------------------------------------------------------------------

LEGACY_BUNDLE = """# Research Bundle for Psalm 10

## Hebrew Lexicon Entries (BDB)
lexicon body

## Analytical Framework for Biblical Poetry

Preamble: Purpose and Methodological Stance...

### III.1 Paronomasia
sub-heading inside the framework must NOT end the section

more framework prose

---

## Traditional Commentaries
commentary body
"""


def test_legacy_framework_section_is_stripped_whole():
    out = ResearchTrimmer().strip_analytical_framework(LEGACY_BUNDLE)
    assert "Analytical Framework for Biblical Poetry" not in out
    assert "Paronomasia" not in out, "a ### sub-heading must not terminate the section"
    assert "framework prose" not in out
    # everything else survives, in order
    assert re.findall(r"^#{1,2} .*", out, re.M) == [
        "# Research Bundle for Psalm 10",
        "## Hebrew Lexicon Entries (BDB)",
        "## Traditional Commentaries",
    ]
    assert "lexicon body" in out and "commentary body" in out


def test_modern_bundle_is_untouched():
    modern = "# Research Bundle\n\n## Hebrew Lexicon Entries (BDB)\nbody\n"
    assert ResearchTrimmer().strip_analytical_framework(modern) == modern


def test_framework_as_final_section_strips_to_end_of_bundle():
    bundle = "# Research Bundle\n\n## Analytical Framework for Biblical Poetry\nprose\n"
    out = ResearchTrimmer().strip_analytical_framework(bundle)
    assert out == "# Research Bundle\n\n"


def test_strip_runs_before_the_early_size_return():
    """trim_bundle returns early on any bundle under the limit — which is every real
    bundle. The strip has to happen before that or it never runs at all."""
    trimmed, _, _ = ResearchTrimmer().trim_bundle(LEGACY_BUNDLE, max_chars=10_000_000)
    assert "Analytical Framework for Biblical Poetry" not in trimmed
