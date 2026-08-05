"""
Tests for the literary-echoes parser, merger, and deterministic reconstruction.

Each test names the failure it guards. The two that matter most are
`test_reconstruct_is_lossless` and the fail-safe verdict tests: Session 374 found
that the old LLM reconstruction pass silently dropped 40-84% of verified echoes on
psalms 69-72, so the invariants here are "nothing is lost" and "ambiguity keeps
content rather than deleting it".

Run: python -m pytest tests/test_literary_echoes_parser.py -q
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.literary_echoes_parser import (  # noqa: E402
    AuthorLedger,
    apply_replacements,
    apply_verdict,
    dedupe_authors,
    drop_malformed,
    extract_authors,
    merge_pass1_variants,
    normalise_author,
    parse_document,
    parse_verdict,
    reconstruct,
)

PASS_1 = """### Psalm 72:1-2 — The King as Judge

**72:1 אֱלֹהִים מִשְׁפָּטֶיךָ לְמֶלֶךְ תֵּן**
O God, endow the king with Your judgments.

*Default bypassed: Shakespeare, Measure for Measure*

#### Saadi Shirazi, *Bustan*, Chapter 1 (13th c.)
> شنیدم که در وقت نزع روان
> "I heard that at the moment the soul departs"
> — *Bustan*, Chapter 1

Saadi turns the psalm's petition into a deathbed instruction, which relocates the
question of just rule from divine endowment to inherited obligation.

#### Bertolt Brecht, *Die Dreigroschenoper* (1928)
> Denn die einen sind im Dunkeln
> "For some are in the darkness"
> — *Die Dreigroschenoper*, finale

Brecht inverts the psalm's confidence in the sheltering king.

---

### Psalm 72:6 — Rain on Mown Grass

**72:6 יֵרֵד כְּמָטָר עַל־גֵּז**
May he be like rain that falls on mown grass.

#### Du Fu, "Spring Night, Delighting in Rain" (8th c.)
> 好雨知時節
> "The good rain knows its season"
> — line 1

Du Fu shares the psalm's image of rain as a moral agent that knows when to arrive.
"""

PASS_2 = """This document under-met the medieval Hebrew quota and the song/libretto quota.
I am filling both, plus one uncovered verse.

### Psalm 72:6 — Rain on Mown Grass

#### Anna Margolin, *Mary Wants to Be a Beggar Woman* (1929)
> איך װיל זײַן אַ בעטלערין
> "I want to be a beggar woman"
> — stanza 2

Margolin's descent answers the psalm's descent of rain with a descent of status.

---

### Psalm 72:12 — He Delivers the Needy

**72:12 כִּי־יַצִּיל אֶבְיוֹן מְשַׁוֵּעַ**
For he saves the needy who cry out.

*Default bypassed: Victor Hugo, Les Misérables*

#### Blind Willie Johnson, "Nobody's Fault But Mine" (1927)
> "Nobody's fault but mine"
> — refrain

The blues turns the psalm's third-person rescue into first-person accusation.
"""


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------


def test_parses_clusters_and_entries():
    doc = parse_document(PASS_1, "pass_1_gemini", "A")
    assert [e.entry_id for e in doc.entries] == ["A01", "A02", "A03"]
    assert [e.author for e in doc.entries] == ["Saadi Shirazi", "Bertolt Brecht", "Du Fu"]
    assert [e.cluster_key for e in doc.entries] == ["72:1", "72:1", "72:6"]
    assert doc.entries[0].cluster_sort == (72, 1)


def test_generator_scaffolding_is_stripped():
    """'Default bypassed' is a cognitive-forcing device, never reader-facing."""
    doc = parse_document(PASS_1, "pass_1_gemini", "A")
    for entry in doc.entries:
        assert "Default bypassed" not in entry.body
        assert "Default bypassed" not in entry.cluster_preamble
    assert "Default bypassed" not in reconstruct(doc.entries)


def test_pass_2_audit_paragraph_is_dropped():
    """Pass 2 opens with an internal quota audit that must not reach the reader."""
    doc = parse_document(PASS_2, "pass_2", "B")
    assert "under-met" in doc.preamble
    assert "under-met" not in reconstruct(doc.entries)


def test_analysis_prose_is_preserved_verbatim():
    doc = parse_document(PASS_1, "pass_1_gemini", "A")
    assert "relocates the\nquestion of just rule" in doc.entries[0].body


def test_quotation_block_isolates_the_quote():
    doc = parse_document(PASS_1, "pass_1_gemini", "A")
    block = doc.entries[2].quotation_block
    assert block.startswith("> 好雨知時節")
    assert block.endswith("— line 1")
    assert "Du Fu shares" not in block


def test_empty_and_garbage_input_yield_no_entries():
    """The empty-Gemini-response case that shipped 3 broken psalms."""
    for text in ("", "   \n\n", "I could not complete this request."):
        assert parse_document(text, "pass_1_gemini", "A").entries == []


def test_horizontal_rules_do_not_leak_into_bodies():
    doc = parse_document(PASS_1, "pass_1_gemini", "A")
    assert not any(line.strip() == "---" for e in doc.entries for line in e.body.split("\n"))


# --------------------------------------------------------------------------
# Reconstruction
# --------------------------------------------------------------------------


def test_reconstruct_is_lossless():
    """THE core invariant. Every parsed entry appears in the output."""
    entries = (
        parse_document(PASS_1, "pass_1_gemini", "A").entries
        + parse_document(PASS_2, "pass_2", "B").entries
    )
    out = reconstruct(entries)
    assert out.count("#### ") == len(entries) == 5
    for entry in entries:
        assert entry.author in out
        assert entry.body.strip().split("\n")[-1] in out


def test_reconstruct_groups_clusters_and_orders_by_verse():
    entries = (
        parse_document(PASS_1, "pass_1_gemini", "A").entries
        + parse_document(PASS_2, "pass_2", "B").entries
    )
    out = reconstruct(entries)
    headings = [ln for ln in out.split("\n") if ln.startswith("### ")]
    assert len(headings) == 3  # 72:1, 72:6, 72:12 — 72:6 merged across passes
    assert out.index("72:1") < out.index("Rain on Mown Grass") < out.index("He Delivers the Needy")
    # Pass 2's addition to an existing cluster sits inside it, not in a new one.
    assert out.index("Du Fu") < out.index("Anna Margolin") < out.index("72:12")


def test_reconstruct_emits_psalm_quote_once_per_cluster():
    entries = (
        parse_document(PASS_1, "pass_1_gemini", "A").entries
        + parse_document(PASS_2, "pass_2", "B").entries
    )
    assert reconstruct(entries).count("May he be like rain") == 1


def test_reconstruct_of_nothing_is_empty():
    assert reconstruct([]) == ""


# --------------------------------------------------------------------------
# Replacement / de-duplication
# --------------------------------------------------------------------------


def test_replaces_marker_drops_the_superseded_entry():
    """Never exercised by real Pass 2 output, so only a test covers it."""
    replacement = """### Psalm 72:6 — Rain on Mown Grass

**REPLACES: Du Fu, *Spring Night* for Psalm 72:6**

#### Bei Dao, "The Answer" (1976)
> 卑鄙是卑鄙者的通行证
> "Baseness is the passport of the base"
> — line 1

Bei Dao refuses the psalm's confidence entirely.
"""
    entries = (
        parse_document(PASS_1, "pass_1_gemini", "A").entries
        + parse_document(replacement, "pass_2", "B").entries
    )
    assert any(e.replaces for e in entries)
    kept, notes = apply_replacements(entries)
    authors = [e.author for e in kept]
    assert "Du Fu" not in authors
    assert "Bei Dao" in authors
    assert len(notes) == 1


def test_drop_malformed_catches_deliberation_written_into_the_document():
    """Verbatim from Claude Sonnet 5 at effort=low on the real Pass-1 prompt.

    Session 374 measured this: the only Anthropic configuration that completes the
    prompt without tripping an output content filter is the one where the model
    stops deliberating internally and does it in the visible document instead.
    Parsed naively, "Gwendolyn Brooks" becomes a cited author.
    """
    observed = """### Psalm 1:1 — The Threefold Refusal

**1:1 text**
English.

#### Gwendolyn Brooks — not eligible (American, but let me choose properly)

I'll replace with a verified fit:

#### Tom Waits, *"Get Behind the Mule"* (1999)
> "You can drive your buick / Down to the ocean's edge"
> — Actually let me choose a securely recalled Waits passage instead.

Waits turns the psalm's refusal into a work song, where the refusal to sit with
scorners becomes an injunction to keep one's hands on the plough regardless.
"""
    entries = parse_document(observed, "pass_1_sonnet", "S").entries
    assert [e.author for e in entries][0].startswith("Gwendolyn Brooks")  # parsed as an entry

    kept, notes = drop_malformed(entries)
    authors = [e.author for e in kept]
    assert not any(a.startswith("Gwendolyn Brooks") for a in authors)
    assert "Tom Waits" in authors  # the real entry survives
    assert len(notes) == 1 and "no quotation block" in notes[0]


def test_drop_malformed_keeps_well_formed_entries():
    entries = parse_document(PASS_1, "pass_1_gemini", "A").entries
    kept, notes = drop_malformed(entries)
    assert len(kept) == len(entries) and notes == []


def test_drop_malformed_rejects_a_quotation_with_no_analysis():
    stub = """### Psalm 1:1 — X

**1:1 text**
English.

#### Real Poet, *Work* (1900)
> "a line"
> — *Work*, 1
"""
    entries = parse_document(stub, "pass_1_gemini", "A").entries
    kept, notes = drop_malformed(entries)
    assert kept == [] and "no analysis" in notes[0]


def test_dedupe_keeps_first_occurrence():
    entries = parse_document(PASS_1, "pass_1_gemini", "A").entries
    dupe = parse_document(PASS_1, "pass_2", "B").entries
    kept, notes = dedupe_authors(entries + dupe)
    assert len(kept) == 3
    assert len(notes) == 3
    assert all(e.source == "pass_1_gemini" for e in kept)


def test_author_normalisation_folds_accents_and_case():
    assert normalise_author("César Vallejo") == normalise_author("Cesar  vallejo")
    assert normalise_author("Ödön von Horváth") == normalise_author("Odon von Horvath")
    assert normalise_author("") == ""


def test_extract_authors_ignores_deeper_headings():
    assert extract_authors("##### Not an entry\n#### Real Author, *Work*\n") == ["Real Author"]


# --------------------------------------------------------------------------
# Merging two Pass-1 generators
# --------------------------------------------------------------------------


OPUS_PASS_1 = """### Psalm 72:1-2 — The King as Judge

**72:1 אֱלֹהִים מִשְׁפָּטֶיךָ לְמֶלֶךְ תֵּן**
O God, endow the king with Your judgments.

#### Aimé Césaire, *Cahier d'un retour au pays natal* (1939)
> et surtout mon corps aussi bien que mon âme
> "and above all my body as well as my soul"
> — section 4

Cesaire refuses the psalm's delegation of justice upward.

#### Saadi Shirazi, *Gulistan*, Chapter 1 (13th c.)
> بنی آدم اعضای یک پیکرند
> "The children of Adam are limbs of one body"
> — Chapter 1

A duplicate author, to prove global de-duplication works.

---

### Psalm 72:20 — The Prayers Are Ended

**72:20 כָּלּוּ תְפִלּוֹת דָּוִד**
The prayers of David are ended.

#### Zbigniew Herbert, "Report from the Besieged City" (1983)
> zbyt stary aby nosić broń
> "too old to carry weapons"
> — line 1

Herbert's colophon-as-poem answers the psalm's editorial colophon.
"""


def test_merge_alternates_between_generators():
    a = parse_document(PASS_1, "pass_1_gemini", "A").entries
    o = parse_document(OPUS_PASS_1, "pass_1_opus", "O").entries
    merged = merge_pass1_variants(a, o, per_cluster_cap=2)
    cluster_72_1 = [e for e in merged if e.cluster_key == "72:1"]
    assert [e.source for e in cluster_72_1] == ["pass_1_gemini", "pass_1_opus"]


def test_merge_caps_volume_so_verification_cost_does_not_double():
    a = parse_document(PASS_1, "pass_1_gemini", "A").entries
    o = parse_document(OPUS_PASS_1, "pass_1_opus", "O").entries
    merged = merge_pass1_variants(a, o, per_cluster_cap=2)
    # 72:1 is covered by both models and fills its cap of 2 (one entry each, so
    # Gemini's second entry is dropped); 72:6 is Gemini-only and 72:20 is
    # Opus-only, and each contributes its single entry. 2 + 1 + 1 = 4.
    assert len(merged) == 4
    assert len(merged) < len(a) + len(o)
    assert sum(1 for e in merged if e.cluster_key == "72:1") == 2


def test_merge_dedupes_authors_globally():
    a = parse_document(PASS_1, "pass_1_gemini", "A").entries
    o = parse_document(OPUS_PASS_1, "pass_1_opus", "O").entries
    merged = merge_pass1_variants(a, o, per_cluster_cap=3)
    authors = [e.author for e in merged]
    assert len(authors) == len(set(authors))
    assert authors.count("Saadi Shirazi") == 1


def test_merge_keeps_clusters_only_one_model_found():
    a = parse_document(PASS_1, "pass_1_gemini", "A").entries
    o = parse_document(OPUS_PASS_1, "pass_1_opus", "O").entries
    merged = merge_pass1_variants(a, o, per_cluster_cap=2)
    assert any(e.cluster_key == "72:20" for e in merged)  # opus only
    assert any(e.cluster_key == "72:6" for e in merged)   # gemini only


def test_merge_with_no_second_generator_is_a_passthrough():
    a = parse_document(PASS_1, "pass_1_gemini", "A").entries
    merged = merge_pass1_variants(a, [], per_cluster_cap=2)
    assert len(merged) == len(a)


def test_cap_never_shrinks_a_cluster_below_the_primary_generator():
    """A flat cap would have deleted 23 real echoes across the 26 built psalms.

    21 Pass-1 clusters in production carry 3+ entries, so the per-cluster ceiling
    has to floor at the primary generator's own count or the merge reintroduces
    silent content loss.
    """
    fat = """### Psalm 72:6 — Rain

**72:6 text**
English.

#### Poet One, *A* (1900)
> line
> "line"
> — A

Analysis one.

#### Poet Two, *B* (1901)
> line
> "line"
> — B

Analysis two.

#### Poet Three, *C* (1902)
> line
> "line"
> — C

Analysis three.
"""
    a = parse_document(fat, "pass_1_gemini", "A").entries
    assert len(a) == 3
    assert len(merge_pass1_variants(a, [], per_cluster_cap=2)) == 3

    o = parse_document(
        fat.replace("Poet One", "Poet Four").replace("Poet Two", "Poet Five")
           .replace("Poet Three", "Poet Six"),
        "pass_1_opus",
        "O",
    ).entries
    merged = merge_pass1_variants(a, o, per_cluster_cap=2)
    # Volume matches the primary generator alone; provenance is now mixed.
    assert len(merged) == 3
    assert {e.source for e in merged} == {"pass_1_gemini", "pass_1_opus"}


# --------------------------------------------------------------------------
# Verdicts — every ambiguous case must FAIL SAFE toward keeping content
# --------------------------------------------------------------------------


def test_verdict_parses_plain_json():
    v = parse_verdict('{"verdict": "rejected", "reason": "fabricated"}', "A01")
    assert v.is_rejection and v.reason == "fabricated"


def test_verdict_parses_fenced_json_with_preamble():
    raw = 'Here is my finding:\n```json\n{"verdict": "verified", "reason": "checks out"}\n```'
    assert parse_verdict(raw, "A01").verdict == "verified"


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "I was unable to complete this verification.",
        "{not json at all",
        '{"verdict": "rejected"',  # truncated mid-object
        '["rejected"]',
        '{"verdict": "banana"}',
    ],
)
def test_malformed_verdicts_never_delete_an_entry(raw):
    """A verifier failure must not be able to silently drop a real echo."""
    assert parse_verdict(raw, "A01").verdict == "verified"


def test_corrected_with_nothing_to_substitute_degrades_to_verified():
    v = parse_verdict('{"verdict": "corrected", "reason": "close enough"}', "A01")
    assert v.verdict == "verified"


def test_verification_markers_are_stripped_from_corrections():
    raw = (
        '{"verdict": "corrected", "corrected_heading": "\\u2705 Du Fu, *Spring Night* (8th c.)",'
        ' "corrected_quotation_block": "> 好雨知時節\\n> \\"The good rain\\"\\n> — line 2"}'
    )
    v = parse_verdict(raw, "A01")
    assert v.corrected_heading == "Du Fu, *Spring Night* (8th c.)"
    assert "✅" not in (v.corrected_quotation_block or "")


def test_apply_verdict_swaps_the_quotation_but_not_the_analysis():
    entry = parse_document(PASS_1, "pass_1_gemini", "A").entries[2]
    original_analysis = "Du Fu shares the psalm's image of rain as a moral agent"
    v = parse_verdict(
        '{"verdict": "corrected", "corrected_quotation_block":'
        ' "> 好雨知時節\\n> \\"The good rain knows its season\\"\\n> — line 2"}',
        entry.entry_id,
    )
    updated = apply_verdict(entry, v)
    assert "line 2" in updated.body
    assert "line 1" not in updated.body
    assert original_analysis in updated.body


def test_apply_verdict_with_no_corrections_is_a_no_op():
    entry = parse_document(PASS_1, "pass_1_gemini", "A").entries[0]
    before = entry.body
    apply_verdict(entry, parse_verdict('{"verdict": "verified"}', entry.entry_id))
    assert entry.body == before


# --------------------------------------------------------------------------
# Author ledger
# --------------------------------------------------------------------------


def _write_corpus(tmp_path, mapping):
    import os
    import time

    for i, (number, text) in enumerate(mapping):
        path = tmp_path / f"psalm_{number:03d}_literary_echoes.txt"
        path.write_text(text, encoding="utf-8")
        # Deterministic mtime ordering: later entries in `mapping` are newer.
        os.utime(path, (time.time() + i, time.time() + i))
    return tmp_path


def test_ledger_counts_authors_across_the_corpus(tmp_path):
    _write_corpus(
        tmp_path,
        [
            (10, "#### Du Fu, *A* (8th c.)\ntext\n"),
            (11, "#### Du Fu, *B* (8th c.)\ntext\n#### Bei Dao, *C* (1976)\ntext\n"),
            (12, "#### Du Fu, *D* (8th c.)\ntext\n"),
        ],
    )
    ledger = AuthorLedger.build(tmp_path)
    assert ledger.count_for("Du Fu") == 3
    assert ledger.count_for("Bei Dao") == 1
    assert ledger.count_for("Nobody At All") == 0


def test_ledger_lifetime_ban_catches_what_the_4_file_window_misses(tmp_path):
    """The bug the ledger exists to fix: reuse outside the recency window."""
    corpus = [(10, "#### Du Fu, *A* (8th c.)\ntext\n")]
    corpus += [(20 + i, f"#### Poet {i}, *W* (1900)\ntext\n") for i in range(5)]
    corpus.append((30, "#### Du Fu, *B* (8th c.)\ntext\n"))
    corpus += [(40 + i, f"#### Other {i}, *W* (1900)\ntext\n") for i in range(5)]
    _write_corpus(tmp_path, corpus)

    ledger = AuthorLedger.build(tmp_path)
    assert "Du Fu" not in ledger.recent(4)  # invisible to the old scan
    assert "Du Fu" in ledger.overused(2)    # caught by the ledger


def test_ledger_excludes_the_psalm_being_regenerated(tmp_path):
    _write_corpus(tmp_path, [(10, "#### Du Fu, *A* (8th c.)\ntext\n")])
    assert AuthorLedger.build(tmp_path, exclude_psalm=10).count_for("Du Fu") == 0


def test_ledger_overused_is_ordered_worst_first_and_capped(tmp_path):
    corpus = []
    for n in range(6):
        corpus.append((10 + n, "#### Du Fu, *A* (8th c.)\ntext\n"))
    for n in range(3):
        corpus.append((30 + n, "#### Bei Dao, *C* (1976)\ntext\n"))
    _write_corpus(tmp_path, corpus)
    ledger = AuthorLedger.build(tmp_path)
    assert ledger.overused(2) == ["Du Fu", "Bei Dao"]
    assert ledger.overused(2, limit=1) == ["Du Fu"]


def test_ledger_on_missing_directory_is_empty(tmp_path):
    assert AuthorLedger.build(tmp_path / "nope").authors == {}
