"""Session 391: the Targum line in the writer's psalm text (behind `include_targum`, the pipeline's
--targum) and the Targum source module. Offline."""
import json
import logging
from types import SimpleNamespace

from src.data_sources import targum as T


def _editor(monkeypatch, targum=None):
    from src.agents import master_editor as me
    import src.data_sources.tanakh_database as tdb
    import src.data_sources.lxx_brenton as lxx
    verses = [SimpleNamespace(verse=1, hebrew="קוֹלִי", english="My voice"),
              SimpleNamespace(verse=2, hebrew="בְּיוֹם", english="On the day")]
    monkeypatch.setattr(tdb, "TanakhDatabase", lambda *a, **k: SimpleNamespace(
        get_psalm=lambda n: SimpleNamespace(verses=verses)))
    monkeypatch.setattr(lxx, "greek_by_mt_verse", lambda n: {1: "Φωνῇ μου", 2: "ἐν ἡμέρᾳ"})
    monkeypatch.setattr(lxx, "lxx_chapters_for_mt", lambda n: [76])
    monkeypatch.setattr(T, "targum_by_verse", lambda n, **k: targum or {})
    ed = me.MasterEditor.__new__(me.MasterEditor)
    ed.logger = logging.getLogger("test")
    return ed


def test_off_by_default_the_psalm_text_is_unchanged(monkeypatch):
    ed = _editor(monkeypatch, targum={1: ("קָלִי קֳדָם יְיָ", "My voice before the LORD")})
    text = ed._get_psalm_text(77, {})
    assert "Targum" not in text
    assert "**LXX:** Φωνῇ μου" in text


def test_on_adds_aramaic_and_english_per_verse(monkeypatch):
    ed = _editor(monkeypatch, targum={1: ("קָלִי קֳדָם יְיָ", "My voice before the LORD"), 2: ("בְּיוֹם עָקְתִי", "")})
    ed.include_targum = True
    text = ed._get_psalm_text(77, {})
    assert T.SOURCE_NOTE in text
    v1 = text.split("### Verse 1")[1].split("### Verse 2")[0]
    assert "**Targum:** קָלִי קֳדָם יְיָ" in v1 and "**Targum (English):** My voice before the LORD" in v1
    v2 = text.split("### Verse 2")[1]
    assert "**Targum:** בְּיוֹם עָקְתִי" in v2 and "Targum (English)" not in v2
    assert v1.index("**LXX:**") < v1.index("**Targum:**")


def test_targum_by_verse_prefers_cook_and_caches(tmp_path, monkeypatch):
    payload = {"versions": [
        {"language": "he", "versionTitle": "Mikraot Gedolot", "text": ["<b>א</b>", "ב", ""]},
        {"language": "en", "versionTitle": "Sefaria Community Translation", "text": ["community 1", "community 2"]},
        {"language": "en", "versionTitle": T.COOK, "text": ["Cook 1", ""]}]}
    calls = []
    monkeypatch.setattr(T, "_fetch", lambda p: calls.append(p) or payload)
    got = T.targum_by_verse(1, cache_dir=tmp_path)
    assert got == {1: ("א", "Cook 1"), 2: ("ב", "community 2")}
    assert T.targum_by_verse(1, cache_dir=tmp_path) == got and calls == [1]       # second call: cache
    assert json.loads((tmp_path / "psalm_001.json").read_text(encoding="utf-8"))["1"] == ["א", "Cook 1"]


def test_an_unavailable_targum_is_empty_not_an_error(tmp_path, monkeypatch):
    def boom(p):
        raise RuntimeError("504")
    monkeypatch.setattr(T, "_fetch", boom)
    assert T.targum_by_verse(5, cache_dir=tmp_path) == {}
