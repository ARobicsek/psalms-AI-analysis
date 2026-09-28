"""
Session 384: concordance retrieval fixes, measured on Psalm 76.

1. Lemmas resolve IN THE SOURCE PSALM first. The Bible-wide "most common lemma for
   this spelling" rule sent בצר to צר (foe / Tyre), רדם to רדה (rule), חמת to Hamath
   and ענו to ענה (answer) — about 4-6 of each run's ~25 searches were about a
   different word.
2. No alphabetical truncation. The SQL orders by book NAME, and a LIMIT 50 applied
   before sampling cut Psalms (and every book after "P") from any lemma with more than
   50 hits: מגן kept 4 of 19 Psalms verses; the רכב+סוס collocation lost Ps 20:8.
3. The display sample is stratified by section, so Psalms is always represented.
4. The shared-vocabulary radar finds the clusters the LLM-chosen searches hit only by
   luck (Hos 2:20, Isa 43:17, Isa 31 for Ps 76).
5. The methods section describes the concordance work honestly, from one helper.

DB-backed tests skip when database/tanakh.db is absent or a stub (the cloud clone).
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "database" / "tanakh.db"
needs_db = pytest.mark.skipif(
    not DB.exists() or DB.stat().st_size < 1_000_000,
    reason="populated database/tanakh.db not available",
)


@pytest.fixture(scope="module")
def librarian():
    from src.agents.concordance_librarian import ConcordanceLibrarian
    return ConcordanceLibrarian()


def _search(librarian, query, psalm=76):
    from src.agents.concordance_librarian import ConcordanceRequest
    return librarian.search_with_variations(
        ConcordanceRequest(query=query, level="consonantal", source_psalm=psalm,
                           include_variations=True))


# --- 1. in-context lemma resolution ------------------------------------------------

@needs_db
@pytest.mark.parametrize("query,global_lemma,psalm_lemma", [
    ("בצר", "צר", "בצר"),    # v.13 יִבְצֹר, not "foe"/Tyre
    ("רדם", "רדה", "רדם"),   # v.7 נִרְדָּם, not "rule"
    ("חמת", "חמת", "חמה"),   # v.11 חֲמַת אָדָם "human wrath", not Hamath
    ("ענו", "ענה", "ענו"),   # v.10 עַנְוֵי "the lowly", not "answer"
])
def test_psalm_context_picks_the_verse_word(librarian, query, global_lemma, psalm_lemma):
    s = librarian.search
    assert s._resolve_lemma(query) == global_lemma  # the old rule, still the fallback
    assert s._resolve_lemma(query, 76) == psalm_lemma


@needs_db
def test_context_resolves_prefixed_forms(librarian):
    # מעונתו is not a Bible-wide surface form on its own; in Ps 76 it is ומעונתו.
    assert librarian.search._resolve_lemma("מעונתו", 76) == "מענה"


@needs_db
def test_context_falls_back_when_word_is_not_in_the_psalm(librarian):
    s = librarian.search
    assert s._resolve_lemma("נדד", 76) == s._resolve_lemma("נדד")


@needs_db
def test_lemma_frequency_is_context_aware(librarian):
    # צר is far commoner than בצר; ranking by the wrong lemma misjudged distinctiveness
    assert librarian.lemma_frequency("בצר", 76) < librarian.lemma_frequency("בצר")


# --- 2. no alphabetical truncation ---------------------------------------------------

@needs_db
def test_common_lemma_keeps_its_psalms_hits(librarian):
    bundle = _search(librarian, "מגן")
    psalms = [r for r in bundle.results if r.book == "Psalms"]
    assert len(psalms) >= 15, "Psalms hits were being cut by the alphabetical LIMIT"
    assert len(bundle.results) > 50


@needs_db
def test_collocation_is_not_truncated(librarian):
    bundle = _search(librarian, "רכב סוס")
    refs = {(r.book, r.chapter, r.verse) for r in bundle.results}
    assert ("Psalms", 20, 8) in refs  # "some trust in chariots, some in horses..."


@needs_db
def test_results_are_in_canonical_order(librarian):
    from src.concordance.search import CANON_INDEX
    bundle = _search(librarian, "טרף")
    keys = [(CANON_INDEX[r.book], r.chapter, r.verse) for r in bundle.results]
    assert keys == sorted(keys)


# --- 3. stratified display ------------------------------------------------------------

def test_allocate_slots_gives_psalms_a_floor_and_every_section_a_slot():
    from src.agents.research_assembler import _allocate_slots, _PSALMS_DISPLAY_FLOOR
    q = _allocate_slots({"Torah": 40, "Prophets": 100, "Psalms": 5, "Writings": 30}, 10)
    assert sum(q.values()) == 10
    assert q["Psalms"] == _PSALMS_DISPLAY_FLOOR
    assert all(q[s] >= 1 for s in ("Torah", "Prophets", "Writings"))
    assert q["Prophets"] >= q["Torah"] >= 1


def test_allocate_slots_never_exceeds_what_a_section_holds():
    from src.agents.research_assembler import _allocate_slots
    q = _allocate_slots({"Torah": 1, "Prophets": 0, "Psalms": 1, "Writings": 2}, 10)
    assert q == {"Torah": 1, "Prophets": 0, "Psalms": 1, "Writings": 2}


def test_allocate_slots_with_fewer_slots_than_sections():
    from src.agents.research_assembler import _allocate_slots
    q = _allocate_slots({"Torah": 9, "Prophets": 9, "Psalms": 9, "Writings": 9}, 2)
    assert sum(q.values()) == 2


@needs_db
def test_display_sample_covers_sections_and_keeps_pins(librarian):
    from src.agents.research_assembler import _sample_for_display
    bundle = _search(librarian, "מגן")
    shown = _sample_for_display(bundle.results, 10, "מגן", "compare Isa 37:33")
    assert len(shown) == 10
    assert sum(r.book == "Psalms" for r in shown) >= 3
    assert any(r.book == "Isaiah" and (r.chapter, r.verse) == (37, 33) for r in shown)
    assert len({r.book for r in shown}) >= 4


# --- 4. shared-vocabulary radar -------------------------------------------------------

@needs_db
def test_radar_finds_the_known_ps76_parallels():
    from src.concordance.intertext_radar import compute_shared_vocabulary_parallels
    md, n = compute_shared_vocabulary_parallels(76)
    assert n == 20
    passages = set(re.findall(r"^\*\*(.+?)\*\* — shares", md, re.M))
    assert {"Hosea 2:20", "Isaiah 43:17", "Nahum 3:18"} <= passages
    chapters = set(re.findall(r"^- \*\*(.+?)\*\* —", md, re.M))
    assert "Isaiah 31" in chapters  # "Assyria shall fall by a sword not of man"


@needs_db
def test_radar_ignores_heading_formulas():
    # Every psalm heading with למנצח / מזמור used to top the list for Ps 76:1.
    from src.concordance.intertext_radar import score_parallels
    top = score_parallels(76)[:40]
    assert not any(k[0] == "Psalms" and k[2] == 1 for _, k, _ in top)


@needs_db
def test_radar_finds_classic_ps1_parallel():
    from src.concordance.intertext_radar import compute_shared_vocabulary_parallels
    md, _ = compute_shared_vocabulary_parallels(1)
    assert "**Joshua 1:8**" in md and "**Jeremiah 17:8**" in md


def test_radar_degrades_without_database(tmp_path):
    from src.concordance.intertext_radar import compute_shared_vocabulary_parallels
    assert compute_shared_vocabulary_parallels(76, tmp_path / "missing.db") == ("", 0)


# --- 5. methods section ---------------------------------------------------------------

def test_methods_summary_reports_searches_found_and_shown():
    from src.utils.pipeline_summary import concordance_methods_summary
    text = concordance_methods_summary(
        {"concordance_results": {"מגן": 62, "רשף": 6}, "shared_vocabulary_count": 20})
    assert text.startswith("2 word searches finding 68 matching verses, 16 of them quoted")
    assert "20 shared-vocabulary parallels" in text
    assert "מגן (62)" in text


def test_methods_summary_na_when_empty():
    from src.utils.pipeline_summary import concordance_methods_summary
    assert concordance_methods_summary({}) == "N/A"


def test_one_definition_of_the_display_count():
    """The per-search display count lives in concordance.search only. A duplicated
    constant has cost this project three sessions already (see Session 380)."""
    src = (ROOT / "src" / "agents" / "research_assembler.py").read_text(encoding="utf-8")
    assert not re.search(r"^MAX_DISPLAY_RESULTS\s*=\s*\d", src, re.M)
    for gen in ("document_generator.py", "combined_document_generator.py",
                "commentary_formatter.py"):
        text = (ROOT / "src" / "utils" / gen).read_text(encoding="utf-8")
        assert "Concordance Entries Reviewed" not in text
        assert "concordance_methods_summary" in text
