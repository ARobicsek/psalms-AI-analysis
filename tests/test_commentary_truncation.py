"""Session 380: traditional-commentary entries are no longer cut at 400 chars.

The bug was one expression repeated twice in `research_assembler._generate_markdown`
(`comm.hebrew[:400] + "..."`). It silently discarded 23% of every commentary entry
in the corpus — 1,119 of 4,907 — and nothing ever raised, because a truncated
quotation is still a valid quotation. It surfaced only because the Psalm 73 writer
thinking capture recorded the writer rating Malbim on v.15 and Torah Temimah on
v.17 as Tier 1 and then discarding both as "cut off mid-thought".

What is pinned here:

1. The cap and the marker have exactly ONE definition, in `commentary_librarian`.
   `research_assembler` imports it. Three sessions in this project have now lost
   time to a duplicated constant (S377's third pricing table, S379's hand-copied
   splice that had drifted for eight sessions), so the absence of a second copy is
   asserted by reading the module source, not assumed.

2. Truncation, when it does happen, is VISIBLE. The old marker was a bare "...",
   indistinguishable from an ellipsis the commentator wrote, which is why the
   writer had to infer the damage instead of being told.
"""

import inspect
import re

from src.agents import research_assembler
from src.agents.commentary_librarian import (
    COMMENTARY_ENTRY_MAX_CHARS,
    COMMENTARY_TRUNCATION_MARKER,
    truncate_commentary,
)


# ---------------------------------------------------------------------------
# 1. the helper itself
# ---------------------------------------------------------------------------

def test_text_within_the_cap_is_returned_byte_identical():
    text = "א" * (COMMENTARY_ENTRY_MAX_CHARS - 1)
    assert truncate_commentary(text) is text


def test_text_exactly_at_the_cap_is_not_truncated():
    """Off-by-one guard: the cap is inclusive."""
    text = "א" * COMMENTARY_ENTRY_MAX_CHARS
    assert truncate_commentary(text) == text
    assert COMMENTARY_TRUNCATION_MARKER not in truncate_commentary(text)


def test_text_over_the_cap_is_cut_and_marked():
    text = "א" * (COMMENTARY_ENTRY_MAX_CHARS + 500)
    out = truncate_commentary(text)
    assert out.endswith(COMMENTARY_TRUNCATION_MARKER)
    assert len(out) == COMMENTARY_ENTRY_MAX_CHARS + len(COMMENTARY_TRUNCATION_MARKER)


def test_empty_and_missing_text_do_not_raise():
    """`comm.english` is routinely empty — most Hebrew commentators have no
    translation on Sefaria — and the old call sites indexed it unconditionally."""
    assert truncate_commentary("") == ""
    assert truncate_commentary(None) is None


def test_the_marker_is_not_a_bare_ellipsis():
    """The whole point. A bare '...' reads as the commentator's own ellipsis."""
    assert COMMENTARY_TRUNCATION_MARKER.strip() not in {"...", "…"}
    assert "truncat" in COMMENTARY_TRUNCATION_MARKER.lower()


# ---------------------------------------------------------------------------
# 2. the cap is meaningfully larger than the one that caused the bug
# ---------------------------------------------------------------------------

def test_cap_recovers_the_psalm_73_entries_that_were_cut():
    """Measured against Sefaria: of Psalm 73's 67 truncated entries the largest
    was Malbim on 73:17 at 2,795 chars and the next at 1,771. A cap of 2,000
    recovers 66 of 67 whole. Anything at or below the old 400 is a regression."""
    assert COMMENTARY_ENTRY_MAX_CHARS >= 1771, (
        "cap no longer recovers the Psalm 73 entries this fix was written for"
    )
    assert COMMENTARY_ENTRY_MAX_CHARS > 400


# ---------------------------------------------------------------------------
# 3. exactly one definition, and the old expression is gone
# ---------------------------------------------------------------------------

def test_research_assembler_uses_the_shared_helper_and_defines_no_copy():
    src = inspect.getsource(research_assembler)
    assert "truncate_commentary(comm.hebrew)" in src
    assert "truncate_commentary(comm.english)" in src
    assert "COMMENTARY_ENTRY_MAX_CHARS =" not in src, (
        "research_assembler has grown its own copy of the cap — there must be "
        "exactly one, in commentary_librarian"
    )
    assert "def truncate_commentary" not in src, (
        "research_assembler has redefined the helper instead of importing it"
    )


def test_the_old_400_char_slice_is_gone_from_every_render_path():
    """Both render paths, including the librarian's debug dump, which had its own
    300-char variant of the same bug."""
    from src.agents import commentary_librarian

    for module in (research_assembler, commentary_librarian):
        src = inspect.getsource(module)
        offenders = re.findall(r"comm\.(?:hebrew|english)\[:\d+\]", src)
        assert not offenders, f"{module.__name__} still hard-slices: {offenders}"
