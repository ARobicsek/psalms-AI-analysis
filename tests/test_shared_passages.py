"""Session 409: the Shared Passages section (doublets and shared lines) that replaced the
Related Psalms Analysis. DB-backed tests skip when database/tanakh.db is absent or a stub."""

from pathlib import Path

import pytest

from src.concordance import shared_passages as sp
from src.utils.pipeline_summary import intertext_methods_line

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "database" / "tanakh.db"
needs_db = pytest.mark.skipif(
    not DB.exists() or DB.stat().st_size < 1_000_000,
    reason="populated database/tanakh.db not available",
)

# The calibration set: doublets and shared verses known from scholarship, all found.
FOUND = [
    (14, 'Psalms', 53), (40, 'Psalms', 70), (57, 'Psalms', 108), (60, 'Psalms', 108),
    (31, 'Psalms', 71), (115, 'Psalms', 135), (135, 'Psalms', 136), (79, 'Psalms', 115),
    (96, 'Psalms', 98), (6, 'Psalms', 38), (106, 'Psalms', 107), (107, 'Psalms', 118),
    (42, 'Psalms', 43), (35, 'Psalms', 40), (41, 'Psalms', 106), (93, 'Psalms', 96),
    (86, 'Psalms', 103), (103, 'Psalms', 145), (18, 'II Samuel', 22), (105, 'I Chronicles', 16),
    (96, 'I Chronicles', 16), (106, 'I Chronicles', 16), (132, 'II Chronicles', 6),
    (79, 'Jeremiah', 10), (135, 'Jeremiah', 10), (113, 'I Samuel', 2), (118, 'Exodus', 15),
    (77, 'Habakkuk', 3), (31, 'Jeremiah', 20), (1, 'Jeremiah', 17),
]
# Known and accepted misses: a loose echo (115:9-11 ~ 118:2-4) and a quotation split across
# distant verses (107:40 = Job 12:21a + 12:24b). The shared-vocabulary section covers leads.
NOT_FOUND = [(115, 'Psalms', 118), (107, 'Job', 12)]

DOUBLET_PSALMS = {14, 18, 31, 40, 53, 57, 60, 70, 71, 79, 96, 105, 106, 108, 115, 135, 136}


def test_tunables_are_pinned():
    assert (sp.MAX_GAP, sp.COMMON_TOP, sp.MIN_CONTENT, sp.TIGHT_GAP, sp.TIGHT_MIN) == (3, 100, 4, 1, 5)
    assert (sp.SEED_MAX_CHAPTERS, sp.DOUBLET_MIN, sp.MAX_VARIANTS, sp.MAX_SHARED_LINES) == (40, 12, 30, 6)


def _units(psalm):
    return {p.other for p in sp.find_shared_passages(psalm)}


@needs_db
@pytest.mark.parametrize("psalm,book,chapter", FOUND)
def test_known_doublets_and_shared_verses_are_found(psalm, book, chapter):
    assert (book, chapter) in _units(psalm)


@needs_db
@pytest.mark.parametrize("psalm,book,chapter", NOT_FOUND)
def test_known_misses_stay_documented(psalm, book, chapter):
    # If one of these starts being found, move it to FOUND (and check it is not noise).
    assert (book, chapter) not in _units(psalm)


@needs_db
def test_a_shared_heading_is_not_a_shared_passage():
    # למנצח לבני קרח מזמור: the old detector flagged 47~49, 47~85, 49~85, 42~44, 54~55.
    assert ('Psalms', 49) not in _units(47) and ('Psalms', 85) not in _units(47)
    assert ('Psalms', 44) not in _units(42) and ('Psalms', 55) not in _units(54)


@needs_db
@pytest.mark.parametrize("psalm", sorted(DOUBLET_PSALMS | {118, 42, 82, 29, 23}))
def test_doublet_label_only_where_one_passage_is_shared(psalm):
    md, refs = sp.compute_shared_passages(psalm)
    assert ("### DOUBLET" in md) == (psalm in DOUBLET_PSALMS)
    # The section is small by design; the Related Psalms section it replaced ran 5-47K.
    assert len(md) <= 2_500
    assert bool(md) == bool(refs)


@needs_db
def test_doublet_extent_crosses_differing_verse_divisions():
    md, _ = sp.compute_shared_passages(96)
    assert "≈ I Chronicles 16:23–30, 16:30–31, 16:32–33" in md   # all of 96:2-13, not 96:2-8


@needs_db
def test_a_refrain_is_one_line_and_each_text_is_listed_once():
    md, refs = sp.compute_shared_passages(136)
    assert md.count("~ Ps 118") == 0 or md.count("Ps 118:1–2") == 1
    assert len(refs) == len(set(refs))


@needs_db
def test_nothing_shared_means_no_section():
    assert sp.compute_shared_passages(82) == ("", [])


@needs_db
def test_parse_refs_round_trips():
    md, refs = sp.compute_shared_passages(79)
    bundle = "## Shared-Vocabulary Parallels (computed)\n\nx\n\n---\n\n" + md + "---\n\n## Research Summary\n"
    assert sp.parse_shared_passages_refs(bundle) == refs


@needs_db
def test_refresh_swaps_the_legacy_section():
    old = ("## Concordance Searches\n\nc\n\n---\n\n"
           "## Shared-Vocabulary Parallels (computed)\n\nradar\n\n---\n\n"
           "## Figurative Language Insights (Curated)\n\nf\n\n---\n\n"
           "## Related Psalms Analysis\n\nPsalm 79 shares...\n\n### Psalm 115 (Connection Score: 1)\n\n"
           "#### Shared Patterns\n\nlots\n\n---\n\n\n---\n\n"
           "## Deep Web Research\n\nd\n\n---\n\n"
           "## Research Summary\n\n- **Related psalms analyzed**: 5\n- **Deep web research included**: Yes\n")
    new, changed = sp.refresh_bundle_shared_passages(old, 79)
    assert changed
    assert "Related Psalms" not in new and "Related psalms analyzed" not in new
    assert new.index("## Shared-Vocabulary") < new.index(sp.SECTION_HEADER) < new.index("## Figurative")
    assert "## Deep Web Research" in new and "- **Deep web research included**: Yes" in new
    again, changed_again = sp.refresh_bundle_shared_passages(new, 79)
    assert again == new and not changed_again


def test_refresh_leaves_a_current_bundle_alone():
    bundle = "## Shared-Vocabulary Parallels (computed)\n\nx\n\n---\n\n## Research Summary\n"
    assert sp.refresh_bundle_shared_passages(bundle, 82) == (bundle, False)


def test_methods_line_new_runs_and_old_runs():
    label, value = intertext_methods_line({'shared_passages_refs': ['Jeremiah 10:25', 'Ps 115:2']})
    assert (label, value) == ("Shared Passages (Doublets, Shared Lines)", "2 (Jeremiah 10:25; Ps 115:2)")
    assert intertext_methods_line({'shared_passages_refs': []})[1] == "None found"
    many = intertext_methods_line({'shared_passages_refs': [f"Ps {i}:1" for i in range(15)]})[1]
    assert many.startswith("15 (") and many.endswith("; and 3 more)")
    # A guide rendered from a pre-S409 run keeps its old line.
    assert intertext_methods_line({'related_psalms_count': 2, 'related_psalms_list': [50, 39]}) == \
        ("Similar Psalms Analyzed", "2 (Psalms 50, 39)")
    assert intertext_methods_line({}) == ("Similar Psalms Analyzed", "N/A")
