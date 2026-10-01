"""Session 391: the commentary librarian fetches each commentator's whole psalm once, with retries,
pinned versions and a disk cache. Before, it made one request per commentator per VERSE (231 on
Ps 77) with a 10 s timeout and no retry, and a timeout silently dropped the entry (Ibn Ezra on
77:9 in Session 387). Verified live, before shipping, to give output identical to the old code on
all 660 verse-commentator pairs of Pss 1, 23, 27, 76 and 77. These tests are offline."""
import json
import logging

import pytest
import requests

from src.agents import commentary_librarian as cl


class Resp:
    def __init__(self, status=200, payload=None):
        self.status_code, self._payload = status, payload

    def raise_for_status(self):
        if self.status_code >= 400:
            err = requests.HTTPError(f"{self.status_code}")
            err.response = self
            raise err

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, script):
        self.script, self.calls = list(script), []
        self.headers = {}

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def chapter(he, en=None, he_title="Ibn Ezra on Psalms -- Daat", en_versions=()):
    versions = [{"language": "he", "versionTitle": he_title, "text": he}]
    if en is not None:
        versions.append({"language": "en", "versionTitle": "Pinned EN", "text": en})
    versions += [{"language": "en", "versionTitle": t, "text": txt} for t, txt in en_versions]
    return Resp(200, {"versions": versions, "warnings": []})


@pytest.fixture
def lib(tmp_path, monkeypatch):
    monkeypatch.setattr(cl.time, "sleep", lambda s: None)
    lib = cl.CommentaryLibrarian(rate_limit_delay=0, cache_dir=tmp_path)
    return lib


def test_one_request_per_psalm_and_the_old_join(lib):
    lib.session = FakeSession([chapter([["<b>a</b>", "b"], [], ["c"]])])
    got = [lib.fetch_commentary(5, v, "Ibn Ezra") for v in (1, 2, 3, 4)]
    assert [g.hebrew if g else None for g in got] == ["a | b", None, "c", None]
    assert got[0].reference == "Ibn Ezra on Psalms 5:1"
    assert len(lib.session.calls) == 1
    params = lib.session.calls[0][1]
    assert ("version", "hebrew|Ibn Ezra on Psalms -- Daat") in params
    assert ("version", "english|all") in params      # partial English, merged (see below)


def test_a_timeout_is_retried_not_dropped(lib):
    lib.session = FakeSession([requests.Timeout("slow"), requests.ConnectionError("reset"),
                               chapter([["x"]])])
    assert lib.fetch_commentary(77, 1, "Ibn Ezra").hebrew == "x"
    assert len(lib.session.calls) == 3


def test_a_404_is_an_empty_chapter_without_retries(lib):
    lib.session = FakeSession([Resp(404)])
    assert lib.fetch_chapter(150, "Chomat Anakh") == {}
    assert len(lib.session.calls) == 1


def test_exhausted_retries_warn_that_the_commentator_is_missing(lib, caplog):
    lib.session = FakeSession([requests.Timeout("t")] * cl.MAX_ATTEMPTS)
    with caplog.at_level(logging.WARNING, logger=cl.logger.name):
        assert lib.fetch_chapter(77, "Radak") == {}
    assert any("Radak is MISSING from this bundle" in r.getMessage() for r in caplog.records)


def test_a_vanished_pinned_version_falls_back_loudly(lib, caplog):
    no_he = Resp(200, {"versions": [], "warnings": [{"hebrew": "no such version"}]})
    default = chapter([["fallback text"]], he_title="Some Newer Edition")
    lib.session = FakeSession([no_he, default])
    with caplog.at_level(logging.WARNING, logger=cl.logger.name):
        assert lib.fetch_commentary(1, 1, "Ibn Ezra").hebrew == "fallback text"
    msgs = " ".join(r.getMessage() for r in caplog.records)
    assert "pinned he version" in msgs and "Some Newer Edition" in msgs


def test_the_disk_cache_spares_sefaria_and_a_new_pin_invalidates_it(tmp_path, monkeypatch):
    monkeypatch.setattr(cl.time, "sleep", lambda s: None)
    first = cl.CommentaryLibrarian(rate_limit_delay=0, cache_dir=tmp_path)
    first.session = FakeSession([chapter([["cached"]])])
    first.fetch_chapter(3, "Ibn Ezra")
    second = cl.CommentaryLibrarian(rate_limit_delay=0, cache_dir=tmp_path)
    second.session = FakeSession([])                       # any request would fail the test
    assert second.fetch_commentary(3, 1, "Ibn Ezra").hebrew == "cached"
    monkeypatch.setitem(cl.PINNED_VERSIONS, "Ibn Ezra", ("A Different Edition", None))
    third = cl.CommentaryLibrarian(rate_limit_delay=0, cache_dir=tmp_path)
    third.session = FakeSession([chapter([["refetched"]], he_title="A Different Edition")])
    assert third.fetch_commentary(3, 1, "Ibn Ezra").hebrew == "refetched"


def test_partial_english_is_merged_comment_by_comment(lib):
    # Ibn Ezra on 1:1 (live, S391): Wikisource has comment 1 only, the community translation all
    # six; the old per-verse endpoint served comment 1 from the first and 2-6 from the second.
    lib.session = FakeSession([chapter(
        [["h1", "h2", "h3"], ["k1"]],
        en_versions=[("Wikisource", [["w1"], []]),
                     ("Community", [["c1", "c2", "c3"], ["d1"]])])])
    e1, e2 = lib.fetch_commentary(1, 1, "Ibn Ezra"), lib.fetch_commentary(1, 2, "Ibn Ezra")
    assert e1.english == "w1 | c2 | c3"
    assert e2.english == "d1"
    cached = json.loads(next(lib.cache_dir.rglob("*.json")).read_text(encoding="utf-8"))
    assert cached["partial_english_by_verse"] == {"1": ["Wikisource", "Community"], "2": ["Community"]}


def test_rashi_english_is_pinned_not_merged(lib):
    lib.session = FakeSession([chapter([["r"]], en=[["Rosenberg"]], he_title="Sefaria vocalized edition")])
    e = lib.fetch_commentary(1, 1, "Rashi")
    assert e.english == "Rosenberg"
    params = lib.session.calls[0][1]
    assert ("version", "english|all") not in params
    assert any(v.startswith("english|The Judaica Press") for k, v in params)


def test_every_commentator_has_a_pinned_version():
    assert set(cl.PINNED_VERSIONS) == set(cl.COMMENTATORS)
