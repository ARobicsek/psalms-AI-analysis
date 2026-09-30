"""
Session 388: the reading packet for the echoes v3 trial.

Part 1 (BLIND): for each psalm, the production literary-echoes dossier and the v3 dossier as
"Dossier X" and "Dossier Y" (order random per psalm). Literature only, and each entry shown the
same way -- verse, author, work, the quotation -- with no rationale, so the reader judges the
PAIRING of verse and passage. Part 2: v3's resonances beyond literature (not blind; the old
pipeline has none). Part 3: the key, v3's one-line moves, costs and checks.

    python scripts/s388_echoes_packet.py 76 77
"""

from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from docx.shared import Inches, Pt, RGBColor  # noqa: E402

from src.agents.echoes_v3 import usable  # noqa: E402
from src.agents.literary_echoes_parser import parse_document  # noqa: E402
from src.data_sources.tanakh_database import TanakhDatabase  # noqa: E402
from src.utils.document_generator import DocumentGenerator, add_page_number, export_pdf  # noqa: E402

DOCS = ROOT / "Documents" / "Psalm study guide"
BODY_PT = 10.5


class Packet(DocumentGenerator):
    def __init__(self, psalm: int, output_path: Path):
        super().__init__(psalm, output_path, output_path, output_path, output_path, None)

    def _set_default_styles(self):
        super()._set_default_styles()
        st = self.document.styles
        for name in ("Normal", "BodySans"):
            st[name].font.size = Pt(BODY_PT)
            st[name].paragraph_format.space_after = Pt(4)
        for name, size, before, after in (("Heading 1", 17, 0, 6), ("Heading 2", 14, 14, 4),
                                          ("Heading 3", 11, 8, 2), ("Heading 4", BODY_PT + 0.5, 7, 1)):
            h = st[name]
            h.font.size = Pt(size)
            h.paragraph_format.space_before = Pt(before)
            h.paragraph_format.space_after = Pt(after)
            h.paragraph_format.keep_with_next = True
        for s in self.document.sections:
            s.left_margin = s.right_margin = Inches(0.8)
            s.top_margin = Inches(0.75)
            s.bottom_margin = Inches(0.7)

    def note(self, text: str):
        p = self.document.add_paragraph(style="BodySans")
        self._process_markdown_formatting(p, text, set_font=True)
        for r in p.runs:
            r.italic = True
            r.font.color.rgb = RGBColor(0x59, 0x59, 0x59)

    def markdown(self, md: str):
        self._process_introduction_content(self.modifier.modify_text(md.strip()), style="BodySans")

    def finish(self):
        section = self.document.sections[0]
        p = section.footer.paragraphs[0] if section.footer.paragraphs else section.footer.add_paragraph()
        add_page_number(p)
        self._join_rtl_runs_across_whitespace()
        self._mirror_bold_to_complex_script()
        self._fix_complex_script_fonts()
        self.document.save(self.output_path)
        print(f"Saved {self.output_path}")


# -- the two dossiers in one neutral shape ---------------------------------------------

def _clean_quote(body: str) -> str:
    """The leading '>' block of an old entry, without the '— *Work*, locus' attribution line."""
    lines = []
    for ln in body.split("\n"):
        if not ln.lstrip().startswith(">"):
            if lines:
                break
            continue
        if re.match(r"^>\s*[—–-]\s", ln.strip()):
            continue
        lines.append(ln.rstrip())
    while lines and lines[-1].strip() == ">":
        lines.pop()
    return "\n".join(lines)


def old_entries(psalm: int):
    text = (ROOT / "data" / "literary_echoes" / f"psalm_{psalm:03d}_literary_echoes.txt").read_text(encoding="utf-8")
    out = []
    for e in parse_document(text, "old", "O").entries:
        verses = re.match(r"Psalm\s+([\d:,\s\-–]+)", e.cluster_heading)
        out.append({"verses": (verses.group(1).strip() if verses else e.cluster_key),
                    "sort": e.cluster_sort, "heading": e.heading.strip(), "quote": _clean_quote(e.body)})
    return sorted(out, key=lambda x: x["sort"])


def new_entries(psalm: int):
    d = ROOT / "output" / f"psalm_{psalm}" / "echoes_v3"
    entries = json.loads((d / "entries.json").read_text(encoding="utf-8"))
    out = []
    for e in entries:
        if e["lane"] != "literature" or not e.get("use"):
            continue
        c, r = e["candidate"], e.get("retrieved") or {}
        head = f"{c.get('creator') or ''}, *{c.get('work', '')}*" + (f" ({c['date']})" if c.get("date") else "")
        if usable(e):
            has_tr = r.get("check_translation") == "quote found on the page"
            src = r.get("original", "") if e.get("status") == "verified" else r.get("translation", "")
            q = "\n".join(f"> {ln}" if ln.strip() else ">" for ln in src.strip().split("\n"))
            if e.get("status") == "verified" and has_tr:
                q += "\n>\n" + "\n".join(f"> {ln}" if ln.strip() else ">" for ln in r["translation"].strip().split("\n"))
        else:
            q = f"*(text not retrieved — reference only: {c.get('locus', '')})*"
        m = re.search(r":(\d+)", e.get("verses", ""))
        out.append({"verses": e.get("verses", "").replace(f"{psalm}:", "") if e.get("verses") else "",
                    "sort": (int(m.group(1)) if m else 999, 0), "heading": head, "quote": q})
    return sorted(out, key=lambda x: x["sort"])


def dossier_md(entries, psalm: int) -> str:
    md = []
    for e in entries:
        v = e["verses"] if ":" in e["verses"] else f"{psalm}:{e['verses']}"
        md += [f"#### {v} — {e['heading'].replace('*', '')}", "", e["quote"], ""]
    return "\n".join(md)


def build(psalms):
    out = DOCS / f"Psalms {' and '.join(map(str, psalms))} - Echoes trial (S388).docx"
    g = Packet(psalms[0], out)
    d = g.document
    d.add_heading(f"Literary echoes: two dossiers for Psalms {' and '.join(map(str, psalms))}", level=1)
    g.note("Session 388. For each psalm there are two dossiers of literary echoes, 'X' and 'Y', in random "
           "order. One is the production dossier the guide was written from; the other comes from a new "
           "pipeline. Both are shown the same way (the verse, the author and work, and the passage) with no "
           "commentary, so you are judging how well each passage answers its verse. Part 2 shows the new "
           "pipeline's resonances beyond literature. The key and the costs are at the end.")
    key, db = {}, TanakhDatabase()
    rng = random.Random(388)
    for psalm in psalms:
        pair = [("production", old_entries(psalm)), ("v3", new_entries(psalm))]
        # counterbalanced: random for the first psalm, the opposite order for the next, so
        # recognising one pair gives nothing away about the other
        if not key:
            rng.shuffle(pair)
        elif key[psalms[psalms.index(psalm) - 1]]["X"] == "production":
            pair.reverse()
        key[psalm] = {"X": pair[0][0], "Y": pair[1][0]}
        d.add_page_break()
        d.add_heading(f"Psalm {psalm}", level=2)
        ps = db.get_psalm(psalm)
        g._format_psalm_text(psalm, {v.verse: {"hebrew": v.hebrew, "english": v.english} for v in ps.verses})
        for letter, (_, entries) in zip("XY", pair):
            d.add_page_break()
            d.add_heading(f"Psalm {psalm} — Dossier {letter} ({len(entries)} echoes)", level=2)
            g.markdown(dossier_md(entries, psalm))

    d.add_page_break()
    d.add_heading("Part 2 — Resonances beyond literature (new pipeline only)", level=2)
    for psalm in psalms:
        md = (ROOT / "output" / f"psalm_{psalm}" / "echoes_v3" / "final.md").read_text(encoding="utf-8")
        beyond = md.split("## Resonances beyond literature", 1)[-1]
        d.add_heading(f"Psalm {psalm}", level=3)
        beyond = "\n".join(l.replace("*", "") if l.startswith("### ") else l for l in beyond.split("\n"))
        g.markdown(beyond.replace("### ", "#### "))

    d.add_page_break()
    d.add_heading("Key", level=2)
    for psalm in psalms:
        g.note(f"Psalm {psalm}: Dossier X = {key[psalm]['X']}; Dossier Y = {key[psalm]['Y']}.")
    for psalm in psalms:
        d.add_heading(f"Psalm {psalm}: the new pipeline's one-line reasons", level=3)
        entries = json.loads((ROOT / "output" / f"psalm_{psalm}" / "echoes_v3" / "entries.json").read_text(encoding="utf-8"))
        g.markdown("\n".join(f"- **{e['verses']} — {e['candidate'].get('creator') or e['candidate'].get('work')}:** "
                             f"{e.get('move', '')}" for e in entries if e["lane"] == "literature" and e.get("use")))
        rep = json.loads((ROOT / "output" / f"psalm_{psalm}" / "echoes_v3" / "cost_report.json").read_text(encoding="utf-8"))
        old = json.loads((ROOT / "output" / f"psalm_{psalm}" / "literary_echoes" / "cost_report.json").read_text(encoding="utf-8"))
        g.note(f"Cost: new ${rep['total_usd']:.2f}, production ${old['total_cost_usd']:.2f}.")
    (ROOT / "output" / "s388_echoes_packet_key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
    g.finish()
    export_pdf(out)
    return out


if __name__ == "__main__":
    build([int(a) for a in sys.argv[1:]] or [76, 77])
