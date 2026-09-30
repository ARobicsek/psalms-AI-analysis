"""Session 390: the pipeline's Septuagint is Brenton's INFLECTED Greek, not Bolls.life's lemmas."""
from types import SimpleNamespace

VPL = """PSA 76:1 Εἰς τὸ τέλος, ὑπὲρ Ἰδιθοὺν ψαλμὸς τῷ Ἀσάφ.
PSA 76:2 Φωνῇ μου πρὸς Κύριον ἐκέκραξα, καὶ ἡ φωνή μου πρὸς τὸν Θεὸν, καὶ προσέσχε μοι.
PSA 76:3 Ἐν ἡμέρᾳ θλίψεώς μου τὸν Θεὸν ἐξεζήτησα
GEN 1:1 ἘΝ ἀρχῇ ἐποίησεν ὁ Θεὸς τὸν οὐρανὸν καὶ τὴν γῆν.
not a verse line
"""


def test_parse_vpl_and_psalm_verses_keep_the_heading_as_verse_one(monkeypatch):
    from src.data_sources import lxx_brenton as lb
    data = lb.parse_vpl(VPL)
    assert sorted(data) == ["GEN", "PSA"] and data["PSA"]["76"]["2"].endswith("προσέσχε μοι.")
    monkeypatch.setattr(lb, "_data", data)
    assert lb.chapter("PSA", 76)[2].startswith("Φωνῇ μου")
    assert lb.psalm_verses(76)[0].startswith("Εἰς τὸ τέλος")          # heading = verse 1, as Bolls
    assert lb.chapter("PSA", 999) == {} and lb.chapter("XXX", 1) == {}


def test_fetch_lxx_psalm_prefers_brenton_and_falls_back_to_bolls(monkeypatch):
    from src.data_sources import lxx_brenton as lb
    from src.data_sources.sefaria_client import SefariaClient
    monkeypatch.setattr(lb, "_data", lb.parse_vpl(VPL))
    client = SefariaClient.__new__(SefariaClient)
    client.session = SimpleNamespace(get=lambda *a, **k: (_ for _ in ()).throw(AssertionError("no web")))
    assert client.fetch_lxx_psalm(77)[1].startswith("Φωνῇ μου")      # MT 77 = LXX 76, no web call

    def unavailable():
        raise RuntimeError("offline")
    monkeypatch.setattr(lb, "load", unavailable)
    lemmas = [{"verse": 1, "text": "φωνή ἐγώ"}]
    client.session = SimpleNamespace(get=lambda *a, **k: SimpleNamespace(
        raise_for_status=lambda: None, json=lambda: lemmas))
    client._wait_for_rate_limit = lambda: None
    assert client.fetch_lxx_psalm(77) == ["φωνή ἐγώ"]
