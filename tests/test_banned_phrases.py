"""Tests for the banned-phrase policy (Session 374).

One assertion per behaviour the reporting depends on. The `col` tests exist
because a paragraph containing the phrase twice — Psalm 8's "structural,
load-bearing. And its load-bearing element..." — printed the identical excerpt
for both hits until the column was carried on the hit.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.banned_phrases import (  # noqa: E402
    BANNED_PHRASES,
    find_banned,
    prompt_block,
)


@pytest.mark.parametrize("text", [
    "The grammatical shift from v. 14 is load-bearing.",
    "a load bearing claim",           # spaced variant
    "LOAD-BEARING points",            # upper case
    "Load-Bearing perfects",          # title case
])
def test_matches_surface_variants(text):
    assert len(find_banned(text)) == 1


@pytest.mark.parametrize("text", [
    "no tic in this sentence",
    "downloadbearing",                # no separator, must not match
    "download-bearing widgets",       # word boundary guards the prefix
    "a load  bearing gap",            # two spaces is not the phrase
    "the load was bearing down",      # intervening words
])
def test_ignores_near_misses(text):
    assert find_banned(text) == []


def test_reports_every_occurrence_not_every_line():
    hits = find_banned("structural, load-bearing. And its load-bearing element")
    assert len(hits) == 2
    assert [h.line_no for h in hits] == [1, 1]


def test_col_distinguishes_two_hits_on_one_line():
    """Both hits must point at their OWN offset, else excerpts read as duplicates."""
    line = "structural, load-bearing. And its load-bearing element"
    first, second = find_banned(line)
    assert first.col == line.index("load-bearing")
    assert second.col == line.index("load-bearing", first.col + 1)
    assert first.col != second.col


def test_col_is_relative_to_stripped_context():
    hit = find_banned("      load-bearing detail")[0]
    assert hit.context == "load-bearing detail"
    assert hit.context[hit.col:].startswith("load-bearing")


def test_line_numbers_are_one_indexed():
    hits = find_banned("clean line\nload-bearing line")
    assert len(hits) == 1
    assert hits[0].line_no == 2


def test_hits_are_in_document_order():
    text = "load-bearing a\nclean\nload-bearing b and load-bearing c"
    hits = find_banned(text)
    assert [(h.line_no, h.col) for h in hits] == sorted((h.line_no, h.col) for h in hits)


def test_prompt_block_names_every_banned_phrase():
    block = prompt_block()
    for banned in BANNED_PHRASES:
        assert banned.label in block
        assert banned.guidance in block


def test_prompt_block_is_empty_when_list_is_empty(monkeypatch):
    """An emptied list must remove the rule, not leave a bare heading."""
    monkeypatch.setattr("src.utils.banned_phrases.BANNED_PHRASES", [])
    assert prompt_block() == ""


def _copy_editor_prompt():
    pytest.importorskip("anthropic")
    from src.agents.copy_editor import COPY_EDITOR_SYSTEM_PROMPT

    return COPY_EDITOR_SYSTEM_PROMPT


def test_copy_editor_prompt_carries_the_generated_rule():
    """The rule must reach the model, and land inside the error taxonomy."""
    prompt = _copy_editor_prompt()
    assert prompt.count("11. BANNED HOUSE-STYLE PHRASES") == 1
    assert prompt.index("10. UNEXPLAINED") < prompt.index("11. BANNED")
    assert prompt.index("11. BANNED") < prompt.index("CRITICAL FORMATTING RULES")


def test_style_carve_out_follows_the_rule_it_overrides():
    """Category 11 is a style rule; "do not rewrite for style" would veto it."""
    prompt = _copy_editor_prompt()
    veto = prompt.index("Do not rewrite for\nstyle or voice")
    carve_out = prompt.index("One deliberate exception runs the other way")
    assert veto < carve_out
    # Must qualify the preamble, not sit orphaned down in the taxonomy.
    assert carve_out < prompt.index("Correct the follo")


def test_figures_carve_out_follows_the_rule_it_overrides():
    """FIGURES ARE NOT CLAIMS protects exactly the metaphors most needing recast."""
    prompt = _copy_editor_prompt()
    veto = prompt.index("FIGURES ARE NOT CLAIMS")
    carve_out = prompt.index("Nor does category 11 license flattening one")
    assert veto < carve_out


def test_carve_outs_do_not_name_individual_phrases():
    """They must reference the CATEGORY, so they cannot drift as the list changes."""
    prompt = _copy_editor_prompt()
    for marker in ("One deliberate exception runs the other way",
                   "Nor does category 11 license flattening one"):
        para = prompt[prompt.index(marker):]
        para = para[:para.index("\n\n")]
        for banned in BANNED_PHRASES:
            assert banned.label not in para
