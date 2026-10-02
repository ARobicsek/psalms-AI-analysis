"""Session 394: the writer-side trim ceiling scales with the psalm's verse count, in ONE place.

Synthesis discovery and the writer share a prompt cache (S388), so they must trim the bundle to
the same ceiling; a hard-coded 350000 left at either site would split them on every long psalm.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.research_trimmer import (BASE_MAX_CHARS, max_chars_for_psalm,
                                        max_chars_for_verses)

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_TRIM_SITES = ("src/agents/master_editor.py", "src/agents/archive/master_editor_v2.py",
                         "src/agents/master_editor_si.py")


def test_short_psalms_keep_the_old_ceiling():
    assert BASE_MAX_CHARS == 350_000
    assert max_chars_for_verses(13) == 350_000
    assert max_chars_for_verses(30) == 350_000


def test_long_psalms_scale():
    assert max_chars_for_verses(72) == 560_000      # Ps 78
    assert max_chars_for_verses(176) == 1_080_000   # Ps 119


def test_unknown_psalm_falls_back_to_base():
    assert max_chars_for_psalm(999) == BASE_MAX_CHARS


def test_no_production_writer_site_hard_codes_the_ceiling():
    for rel in PRODUCTION_TRIM_SITES:
        src = (ROOT / rel).read_text(encoding="utf-8")
        calls = re.findall(r"research_trimmer\.trim_bundle\([^)]*\)", src, flags=re.S)
        writer_calls = [c for c in calls if "max_chars=" in c]
        assert writer_calls, rel
        for c in writer_calls:
            if rel.endswith("master_editor_v2.py") and "write_college_commentary" in src.split(c)[0][-4000:]:
                continue  # the dead college-commentary path; not production
            assert "max_chars_for_psalm(psalm_number)" in c, (rel, c)
