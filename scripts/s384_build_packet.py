"""
Session 384 — build the Psalm 76 essay-trials reading packet (DOCX, $0).

Reads output/psalm_76/_S384_essays/ (written by s384_essay_trials.py) and renders,
through the production DocumentGenerator so Hebrew/RTL and quoted poems render
correctly, in a compact print layout:

  1. How to read this packet + the psalm
  2. Every essay under a blind letter (A, B, ...), each followed by two reader's notes
  3. The ideas map (which idea appears in which essay)
  4. Simple counts per essay
  5. Appendix: the two research-free "first readings"
  6. The key (letter -> prompt arm / model / effort / cost)

A second DOCX carries the writers' reasoning summaries.

    python scripts/s384_build_packet.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Inches, Pt, RGBColor  # noqa: E402

from src.data_sources.tanakh_database import TanakhDatabase  # noqa: E402
from src.utils.document_generator import DocumentGenerator, add_page_number  # noqa: E402

TRIALS = ROOT / "output" / "psalm_76" / "_S384_essays"
DOCS = ROOT / "Documents" / "Psalm study guide"
OUT_MAIN = DOCS / "Psalm 76 - Essay trials (S384).docx"
OUT_THINK = DOCS / "Psalm 76 - Essay trials (S384) - writers' reasoning.docx"
BODY_PT = 10.5

ARM_DESCRIPTIONS = {
    "P0": "P0 — current production prompt (with the new echo budget), essay only",
    "P1": "P1 — the 'forest' rewrite",
    "P2": "P2 — the 'forest' rewrite + two research-free first readings + shared-vocabulary parallels",
}
MODEL_NAMES = {"claude-opus-5-5": "Claude Opus 5.5", "gpt-6-sol": "GPT-6 Sol"}


def _set_cs_size(style, pt):
    rpr = style.element.get_or_add_rPr()
    el = rpr.find(qn("w:szCs"))
    if el is None:
        el = OxmlElement("w:szCs")
        rpr.append(el)
    el.set(qn("w:val"), str(int(round(pt * 2))))


def _demote_headings(md: str) -> str:
    """Essay headings sit under 'Essay X' (a level-2 heading): push them down a level."""
    out = []
    for line in md.splitlines():
        m = re.match(r"^(#{1,3})\s+(.*)$", line)
        out.append(("#### " + m.group(2)) if m else line)
    return "\n".join(out)


class PacketGenerator(DocumentGenerator):
    def __init__(self, output_path: Path):
        super().__init__(76, output_path, output_path, output_path, output_path, None)

    def _set_default_styles(self):
        super()._set_default_styles()
        st = self.document.styles
        for name in ("Normal", "BodySans"):
            st[name].font.size = Pt(BODY_PT)
            _set_cs_size(st[name], BODY_PT + 1)
            st[name].paragraph_format.space_after = Pt(5)
        for name, size, before, after in (("Heading 1", 17, 0, 6), ("Heading 2", 14, 14, 4),
                                          ("Heading 3", 11.5, 9, 2), ("Heading 4", BODY_PT + 0.5, 7, 1)):
            h = st[name]
            h.font.size = Pt(size)
            h.paragraph_format.space_before = Pt(before)
            h.paragraph_format.space_after = Pt(after)
            h.paragraph_format.keep_with_next = True
        for s in self.document.sections:
            s.left_margin = s.right_margin = Inches(0.8)
            s.top_margin = Inches(0.75)
            s.bottom_margin = Inches(0.7)

    # -- small helpers -------------------------------------------------------------
    def note(self, text: str, italic=True, grey=True):
        p = self.document.add_paragraph(style="BodySans")
        self._process_markdown_formatting(p, text, set_font=True)
        for r in p.runs:
            r.italic = italic
            if grey:
                r.font.color.rgb = RGBColor(0x59, 0x59, 0x59)
        return p

    def markdown(self, md: str):
        self._process_introduction_content(self.modifier.modify_text(md.strip()), style="BodySans")

    def md_table(self, lines):
        rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines
                if l.strip().startswith("|") and not re.match(r"^\|\s*:?-{2,}", l.strip())]
        if not rows:
            return
        ncol = max(len(r) for r in rows)
        t = self.document.add_table(rows=0, cols=ncol)
        t.style = "Table Grid"
        t.autofit = False
        # Column widths in proportion to content (capped), across the 6.9" text block.
        weight = [max(10, min(60, max(len(r[c]) if c < len(r) else 0 for r in rows))) for c in range(ncol)]
        widths = [Inches(6.9 * w / sum(weight)) for w in weight]
        for ri, r in enumerate(rows):
            cells = t.add_row().cells
            for ci in range(ncol):
                cells[ci].width = widths[ci]
                p = cells[ci].paragraphs[0]
                self._process_markdown_formatting(p, r[ci] if ci < len(r) else "", set_font=True)
                for run in p.runs:
                    run.font.size = Pt(8.5)
                    if ri == 0:
                        run.bold = True
        self.document.add_paragraph()

    def markdown_with_tables(self, md: str):
        buf, table = [], []
        for line in md.splitlines():
            if line.strip().startswith("|"):
                if buf:
                    self.markdown("\n".join(buf))
                    buf = []
                table.append(line)
            else:
                if table:
                    self.md_table(table)
                    table = []
                buf.append(line)
        if table:
            self.md_table(table)
        if buf:
            self.markdown("\n".join(buf))

    def finish(self):
        section = self.document.sections[0]
        p = section.footer.paragraphs[0] if section.footer.paragraphs else section.footer.add_paragraph()
        add_page_number(p)
        self._join_rtl_runs_across_whitespace()
        self._mirror_bold_to_complex_script()
        self._fix_complex_script_fonts()
        self.document.save(self.output_path)
        print(f"Saved {self.output_path}")


def load():
    key = json.loads((TRIALS / "blind_key.json").read_text(encoding="utf-8"))
    metrics = json.loads((TRIALS / "metrics.json").read_text(encoding="utf-8"))
    essays = {}
    for letter, name in key.items():
        if name.startswith("REF-"):
            src = {"REF-A": ROOT / "output/psalm_76/psalm_076_edited_intro_pre_copy_edit.md",
                   "REF-B": ROOT / "output/psalm_76/_opus55_B/psalm_076_edited_intro_pre_copy_edit.md"}
            text = src[name[:5]].read_text(encoding="utf-8").split("---LITURGICAL-SECTION-START---")[0]
            meta = {"arm": name}
        else:
            d = TRIALS / "essays" / name
            text = (d / "essay.md").read_text(encoding="utf-8")
            meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        essays[letter] = (name, text, meta)
    return key, metrics, essays


def describe(name: str, meta: dict) -> str:
    if name.startswith("REF-A"):
        return "Reference: the essay in the production guide (Opus 5, A's dossier), before copy editing"
    if name.startswith("REF-B"):
        return "Reference: the essay in the all-Opus-5.5 'B' guide (same dossier as the trials), before copy editing"
    arm = name.split("_")[0]
    rep = " (second run)" if name.endswith("_r2") else ""
    return (f"{ARM_DESCRIPTIONS[arm]} — {MODEL_NAMES[meta['model']]}, effort {meta['effort']}{rep}; "
            f"{meta['words']:,} words; ${meta['cost_usd']:.2f}")


def build_main(key, metrics, essays):
    g = PacketGenerator(OUT_MAIN)
    d = g.document
    d.add_heading("Psalm 76 — Essay Trials", level=1)
    n_ref = sum(1 for n, _, _ in essays.values() if n.startswith("REF-"))
    g.note(f"Session 384. {len(essays)} introduction essays on Psalm 76, in random order under blind "
           f"letters. {len(essays) - n_ref} were written overnight from the same research dossier as "
           f"the 'B' guide, under three prompts and two models; {n_ref} are the essays from the "
           "existing A and B guides, included for reference. The key is on the last page.")
    g.note("After each essay come two reader's notes, one by Claude Opus 5.5 and one by GPT-6 Sol. "
           "They were asked to DESCRIBE — governing idea, insights, best writing, weak spots, claims "
           "worth checking — and not to score or rank. Neither knew which model or prompt wrote the "
           "essay. The ideas map after the essays shows which idea turns up in which essay.")

    db = TanakhDatabase()
    ps = db.get_psalm(76)
    d.add_heading("The psalm", level=2)
    g._format_psalm_text(76, {v.verse: {"hebrew": v.hebrew, "english": v.english} for v in ps.verses})

    for letter in sorted(essays):
        name, text, meta = essays[letter]
        d.add_page_break()
        d.add_heading(f"Essay {letter}", level=2)
        g.markdown(_demote_headings(text))
        for tag, who in (("opus", "Claude Opus 5.5"), ("sol", "GPT-6 Sol")):
            f = TRIALS / "notes" / f"{letter}_{tag}.md"
            if f.exists():
                d.add_heading(f"Reader's notes on Essay {letter} — {who}", level=3)
                g.markdown(f.read_text(encoding="utf-8"))

    d.add_page_break()
    d.add_heading("Ideas map", level=2)
    g.note("Built by GPT-6 Sol from all essays at once; descriptive only. Letters as above.")
    im = TRIALS / "ideas_map.md"
    if im.exists():
        g.markdown_with_tables(im.read_text(encoding="utf-8").replace("## ", "### "))

    d.add_heading("Counts per essay", level=2)
    g.note("Mechanical counts, for orientation only. 'Book ch:v citations' counts only references "
           "written in that form (a passage named as 'Hosea promised…' or 'Herodotus 2.141' is not "
           "counted). 'Echoes used' = authors from the literary-echoes dossier named in the essay.")
    rows = ["| Essay | Words | Headings | Bullet lines | 'Book ch:v' citations | Commentator mentions | "
            "Echoes used (from dossier) | Block-quote lines | Selah mentions |", "|---|---|---|---|---|---|---|---|---|"]
    for letter in sorted(essays):
        m = metrics[essays[letter][0]]
        rows.append(f"| {letter} | {m['words']} | {m['headings']} | {m['bullet_lines']} | "
                    f"{m['bible_refs_distinct']} | {m['commentator_mentions']} | "
                    f"{', '.join(m['dossier_echoes_used']) or '—'} | {m['block_quote_lines']} | "
                    f"{m['selah_mentions']} |")
    g.md_table(rows)

    d.add_page_break()
    d.add_heading("Appendix: the two first readings", level=2)
    g.note("Written from the psalm alone (Hebrew, English, Greek, transcription) with no research, "
           "and given as extra input to the two P2 essays.")
    for tag, who in (("opus", "Claude Opus 5.5 (effort high)"), ("sol", "GPT-6 Sol (effort xhigh)")):
        f = TRIALS / "first_readings" / f"first_reading_{tag}.md"
        if f.exists():
            d.add_heading(f"First reading — {who}", level=3)
            g.markdown(_demote_headings(f.read_text(encoding="utf-8")))

    d.add_page_break()
    d.add_heading("Key", level=2)
    rows = ["| Essay | What produced it |", "|---|---|"]
    for letter in sorted(essays):
        name, _, meta = essays[letter]
        rows.append(f"| {letter} | {describe(name, meta)} |")
    g.md_table(rows)
    ledger = json.loads((TRIALS / "ledger.json").read_text(encoding="utf-8"))
    total = sum(c["cost_usd"] for c in ledger["calls"])
    g.note(f"Total spend for the trials (essays, first readings, notes, ideas map): ${total:.2f} "
           f"across {len(ledger['calls'])} API calls.")
    failed = [c for c in ledger["calls"] if c["label"] == "P1_opus_max"]
    if failed and not (TRIALS / "essays" / "P1_opus_max" / "essay.md").exists():
        g.note(f"One planned arm is missing: P1 on Claude Opus 5.5 at effort MAX produced no essay. "
               f"Both attempts spent the whole 128,000-token output budget reasoning (~19 minutes "
               f"each) and never began writing; that cost ${sum(c['cost_usd'] for c in failed):.2f} "
               f"of the total. Effort 'high' is the usable Opus setting for this task.")
    g.note("Per-essay costs: the first Opus P1 essay (and the first GPT-6 one) carries the one-time "
           "cost of caching the ~180K-token dossier; later essays on the same model reuse it. The "
           "P0 essays use the production prompt order, which cannot share that cache.")
    g.finish()


def build_thinking(key, essays):
    g = PacketGenerator(OUT_THINK)
    d = g.document
    d.add_heading("Psalm 76 — Essay Trials: the writers' reasoning", level=1)
    g.note("The reasoning summaries each model returned while writing (Claude's summarized thinking; "
           "GPT-6's reasoning summary) — summaries, not verbatim traces. Letters match the main packet.")
    for letter in sorted(essays):
        name, _, meta = essays[letter]
        if name.startswith("REF-"):
            continue
        f = TRIALS / "essays" / name / "thinking_summary.txt"
        if not f.exists() or not f.read_text(encoding="utf-8").strip():
            continue
        d.add_heading(f"Essay {letter} — {describe(name, meta)}", level=2)
        for para in re.split(r"\n\s*\n", f.read_text(encoding="utf-8")):
            if para.strip():
                g._add_paragraph_with_markdown(" ".join(para.split("\n")), style="BodySans")
    g.finish()


if __name__ == "__main__":
    key, metrics, essays = load()
    build_main(key, metrics, essays)
    build_thinking(key, essays)
