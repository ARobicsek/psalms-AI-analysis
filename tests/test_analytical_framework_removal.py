"""Session 379: the analytical framework is gone from the writer prompt.

Two things are pinned here, because both failed silently in Session 378 and neither
would raise on its own:

1. The framework block is out of BOTH writer templates, and the SI template is still
   just the V4 template plus its directive section. `str.format()` ignores extra
   kwargs, so a half-finished removal is invisible at runtime.

2. The Session-347 cross-verse observations block still splices. Its anchor used to be
   the framework heading, and a missing anchor only logs a warning — so removing the
   heading could drop ~$1.50/psalm of synthesis discovery without anything failing.
   The SI pipeline had its own hand-copied duplicate of the splice, which is exactly
   how it came to drift; the splice is now inherited, and that is asserted below.
"""

import re

from src.agents.master_editor import MasterEditor, MASTER_WRITER_PROMPT_V4
from src.agents.master_editor_si import MasterEditorSI, MASTER_WRITER_PROMPT_SI, SI_SECTION
from src.utils.research_trimmer import ResearchTrimmer

FRAMEWORK_HEADING = "### ANALYTICAL FRAMEWORK (poetic conventions reference)"
OBSERVATIONS_HEADING = "### CROSS-VERSE OBSERVATIONS"
READER_QUESTIONS_ANCHOR = "### READER QUESTIONS (initial questions)"


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


def test_reader_questions_anchor_survives_as_the_splice_target():
    """The fallback anchor must exist in both templates — it is now the live one."""
    for template in (MASTER_WRITER_PROMPT_V4, MASTER_WRITER_PROMPT_SI):
        assert template.count(READER_QUESTIONS_ANCHOR) == 1


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


def test_splice_is_shared_not_duplicated():
    """MasterEditorSI must INHERIT the splice. A second copy is what let the SI
    pipeline keep the old anchor and the pre-Session-371 guidance."""
    assert "_splice_cross_verse_observations" not in vars(MasterEditorSI)
    assert (
        MasterEditorSI._splice_cross_verse_observations
        is MasterEditor._splice_cross_verse_observations
    )


def test_observations_splice_into_a_prompt_with_no_framework_heading():
    for editor in (_Editor(), _EditorSI()):
        editor._cross_verse_observations = "OBSERVATION ONE\nOBSERVATION TWO"
        prompt = f"### KEY INSIGHTS\nstuff\n\n{READER_QUESTIONS_ANCHOR}\n1. a question\n"
        out = editor._splice_cross_verse_observations(prompt)
        assert OBSERVATIONS_HEADING in out
        assert "OBSERVATION ONE" in out
        assert out.index(OBSERVATIONS_HEADING) < out.index(READER_QUESTIONS_ANCHOR)


def test_splice_carries_the_session_371_guidance():
    """The SI copy still said "do NOT structure your commentary around them", the
    wording that suppressed the best idea in the Ps 71 dossier under Opus 5."""
    editor = _EditorSI()
    editor._cross_verse_observations = "OBS"
    out = editor._splice_cross_verse_observations(f"{READER_QUESTIONS_ANCHOR}\n")
    assert "do NOT structure your commentary around them" not in out
    assert "SHOULD carry your essay" in out


def test_no_observations_leaves_the_prompt_byte_identical():
    editor = _Editor()
    prompt = f"### KEY INSIGHTS\nstuff\n\n{READER_QUESTIONS_ANCHOR}\n"
    assert editor._splice_cross_verse_observations(prompt) == prompt


def test_missing_anchor_warns_and_returns_the_prompt_unchanged():
    editor = _Editor()
    editor._cross_verse_observations = "OBS"
    prompt = "a prompt with no anchor at all"
    assert editor._splice_cross_verse_observations(prompt) == prompt


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
