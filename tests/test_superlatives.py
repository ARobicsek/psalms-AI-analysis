"""Session 380: ungrounded ranking and uniqueness claims.

The author, on the Psalm 73 guide: "I'm seeing multiple examples of an 'LLM
verbal tic' — describing something as 'the most' something."

The hard part of this rule is NOT catching superlatives; it is not catching the
wrong ones. Measured over the 44 finished guides there are 529 raw superlative
constructions, and hand-classifying all 20 in Psalm 73 put only ~30% in the tic
bucket. Eight were verifiable concordance findings that are among the best lines
in the guide, and six were not superlatives at all. So the tests below spend most
of their weight on what must NOT fire.

The dangerous false positive has its own test: an earlier draft matched "read",
which caught "it is better read as" — a construction COPY_EDITOR_SYSTEM_PROMPT
explicitly sanctions, twice, as a legitimate flagged conjecture the editor is
told not to delete or weaken.
"""

import re

from src.utils.superlatives import (
    CANDIDATE_PATTERNS,
    RECEPTION_PATTERNS,
    find_candidates,
    find_reception_claims,
    prompt_block,
)


# ---------------------------------------------------------------------------
# 1. the reception tier catches the author's actual complaints
# ---------------------------------------------------------------------------

AUTHOR_EXAMPLES = [
    "arrives at the same ontology in the most famous soliloquy in Spanish:",
    "The second half is the most argued clause in the psalm, and the Masoretic",
    "Lamentations, in the middle of its most famous consolation, says of God's",
]


def test_catches_every_reception_claim_the_author_flagged():
    for line in AUTHOR_EXAMPLES:
        assert find_reception_claims(line), f"missed: {line!r}"


def test_reports_one_hit_per_site_not_one_per_pattern():
    """'the most famous soliloquy' matches two patterns by design. The author
    should see one problem, not the same problem twice."""
    hits = find_reception_claims(
        "arrives at the same ontology in the most famous soliloquy in Spanish:"
    )
    assert len(hits) == 1, [h.matched for h in hits]


def test_two_distinct_sites_on_one_line_are_both_reported():
    hits = find_reception_claims(
        "His most famous lyric, and separately the most debated crux, both appear."
    )
    assert len(hits) == 2, [h.matched for h in hits]


# ---------------------------------------------------------------------------
# 2. what must NOT fire — the expensive direction
# ---------------------------------------------------------------------------

SANCTIONED_HEDGES = [
    "The unmarked entry of divine speech is better read as the requested answer.",
    "Its arrival has struck readers as an intrusion. It is best read as a capstone.",
    "Whichever direction of dependence is correct (most read Job as parodying Ps 8).",
]


def test_does_not_fire_on_the_sanctioned_best_read_as_hedge():
    """Regression guard. COPY_EDITOR_SYSTEM_PROMPT lists 'is best read as' as a
    legitimate flagged conjecture and forbids weakening it. An audit that flagged
    it would set the copy editor against its own rule."""
    for line in SANCTIONED_HEDGES:
        assert not find_reception_claims(line), f"false positive: {line!r}"


PROTECTED_CONCORDANCE_CLAIMS = [
    "And דּוֹר בָּנֶיךָ occurs nowhere else in the Bible; the poet has coined a phrase.",
    "this is the poem's single Tetragrammaton (the four-letter divine name).",
    "אֵיכָה is a heavy word — the first word of Lamentations.",
    "The construct phrase is unique in the Bible; the nearest thing is Isaiah's.",
    "the only imperative in the psalm",
]


def test_does_not_fire_on_verifiable_textual_distribution_claims():
    """These are established by the research bundle and are the entire payoff of
    the concordance work. The reception tier must leave them alone."""
    for line in PROTECTED_CONCORDANCE_CLAIMS:
        assert not find_reception_claims(line), f"false positive: {line!r}"


def test_does_not_fire_on_divine_titles_or_quoted_translations():
    for line in [
        'Is there knowledge in the Most High?" (v. 11).',
        "and the greatest good is small; for all of life is a dream",
        "His awe in the highest heavens, His bow in the heavens",
        "the nearest antecedent is the wicked",
    ]:
        assert not find_reception_claims(line), f"false positive: {line!r}"


def test_does_not_fire_on_the_authors_own_aesthetic_judgment():
    """'the most honest line in the psalm' is the author judging the text in front
    of him, not making a claim about the outside world. An earlier canonicity
    pattern caught it; that pattern was narrowed."""
    assert not find_reception_claims("“Not forever”—the most honest line in the psalm")
    assert not find_reception_claims("The sharpest of these reassignments is epistemological")


def test_no_reception_pattern_matches_a_verb_of_interpretation():
    """Structural guard, so a future edit cannot quietly re-add 'read'."""
    for pat in RECEPTION_PATTERNS:
        for verb in ("read", "understood", "taken", "construed"):
            assert not re.search(rf"\b{verb}\b", pat.pattern), (
                f"pattern {pat.label!r} matches the interpretive verb {verb!r}"
            )


# ---------------------------------------------------------------------------
# 3. the candidate tier is broad ON PURPOSE and is never a gate
# ---------------------------------------------------------------------------

def test_candidate_tier_is_broader_than_the_reception_tier():
    text = (
        "the most famous soliloquy in Spanish, and דּוֹר בָּנֶיךָ occurs nowhere "
        "else in the Bible, and leaven is the one thing barred from the altar."
    )
    assert len(find_candidates(text)) > len(find_reception_claims(text))


def test_candidate_tier_surfaces_the_leaven_case():
    """The uniqueness-contradicted-by-evidence shape needs semantic judgment, so
    it is deliberately NOT in the gating tier — but it must be reviewable."""
    hits = find_candidates("Leaven is the one thing barred from the altar.")
    assert any(h.label == "the-one" for h in hits)


def test_candidate_patterns_do_not_leak_into_the_gate():
    reception_labels = {p.label for p in RECEPTION_PATTERNS}
    candidate_labels = {p.label for p in CANDIDATE_PATTERNS}
    assert not (reception_labels & candidate_labels)


# ---------------------------------------------------------------------------
# 4. the rule text, and that it actually reaches the copy editor
# ---------------------------------------------------------------------------

def test_prompt_block_protects_the_verifiable_claims():
    block = prompt_block()
    assert "LEAVE ALONE" in block
    assert "nowhere else in" in block


def test_prompt_block_forbids_hedging_as_a_repair():
    """RULE 9 of the writer prompt says 'Do not hedge'. The repair here is cut or
    ground; 'perhaps the most famous' keeps the unsupported ranking and adds
    evasion on top."""
    block = prompt_block()
    assert "Never repair one of these by hedging" in block
    assert "Cut it or ground it" in block


def test_rule_is_spliced_into_the_live_copy_editor_prompt():
    from src.agents.copy_editor import COPY_EDITOR_SYSTEM_PROMPT

    assert "(h) UNGROUNDED RANKING OR UNIQUENESS CLAIMS" in COPY_EDITOR_SYSTEM_PROMPT
    # It must sit inside category 9, so it inherits "fix them, do not delete".
    h_at = COPY_EDITOR_SYSTEM_PROMPT.index("(h) UNGROUNDED RANKING")
    g_at = COPY_EDITOR_SYSTEM_PROMPT.index("(g) FACTUALLY WRONG ANALOGIES")
    salvage_at = COPY_EDITOR_SYSTEM_PROMPT.index("Do not remove arguments that can be salvaged")
    assert g_at < h_at < salvage_at


def test_splice_is_idempotent_on_reimport():
    """The prompt is mutated at import time. A module reload must not stack a
    second copy of the rule into it."""
    import importlib

    from src.agents import copy_editor

    importlib.reload(copy_editor)
    assert copy_editor.COPY_EDITOR_SYSTEM_PROMPT.count("(h) UNGROUNDED RANKING") == 1
