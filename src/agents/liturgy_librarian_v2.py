"""
Liturgical librarian, Session 395: one grounded account per psalm from a COMPLETE catalogue.

What it replaces (`liturgical_librarian.LiturgicalLibrarian`, kept for `--liturgy legacy`)
summarised each matched PHRASE separately (Ps 78:38 got five GPT calls and five
contradictory paragraphs) and showed its model the first five matching prayers of each,
chosen by prayer name: 47% of all matches never reached a model, and in 118 summaries a
whole rite was missing. The model, seeing the Edot HaMizrach copies of a passage, wrote
that it was said "in the Nusach Sefard and Edot HaMizrach forms of Uva le-Tziyon"; the
Ashkenaz copies were in the database, unseen. Nothing told it which books had been searched,
so "the selichot we happen to have" became "certain selichot".

Here the code does the finding and the counting, and the model does the reading:

1. `verse_matcher.find_hits` — every place the psalm's words occur (word boundaries,
   spelling-tolerant), each tested against the rest of the Bible.
2. `liturgy_catalogue.build_units` — per verse (or the whole psalm), the PLACES it is said,
   each with every rite and book it was found in, and one excerpt.
3. One model call reads the whole catalogue and writes the section: where each verse is
   said (generalised only as far as the catalogue shows), the prayer's words around it,
   quotation vs. allusion vs. coincidence (coincidences go to a SET ASIDE list, logged, not
   printed). The scope of the search is stated in the section by code, not by the model.

Interface kept from the old class (the research assembler calls these two):
`find_liturgical_usage_aggregated(psalm_chapter, ...)` and `format_for_research_bundle(...)`.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from src.liturgy import liturgy_catalogue as lc
from src.liturgy import verse_matcher as vm
from src.utils.debug_paths import psalm_output_dir

DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_EFFORT = "medium"   # S395, Ps 78: high thought through 32K tokens and was cut off ($0.88); medium $0.72, complete
MAX_TOKENS = 64000
CHUNK_CHARS = 80000      # a catalogue longer than this is written in parts (Ps 119: 180K chars, 85 units)
SECTION_TITLE = "## Modern Jewish Liturgical Use (Psalm {n})"

# The texts searched. Written by code into every section, so the writer reads the scope of
# the search beside the findings and nobody has to infer it.
CORPUS_NOTE = (
    "*Texts searched (Sefaria): the Ashkenaz, Sefard (Hasidic) and Edot HaMizrach siddurim; the Chabad "
    "weekday siddur; the Rosh Hashanah and Yom Kippur machzorim of all three rites; the full selichot "
    "(Ashkenaz, Lithuanian and Polish; Edot HaMizrach); the Ashkenaz kinnot and the Edot HaMizrach "
    "Tisha B'Av order; two Haggadot; Ma'avar Yabbok, Seder Ma'amadot, Tikkun HaKlali, Perek Shirah, "
    "Yizkor, Akdamut, Keter Malkhut and the Azharot. Not searched: festival machzorim for Pesach, "
    "Shavuot and Sukkot beyond what the siddurim carry, and the Yemenite, Italian, Romaniote and "
    "other rites. A place missing below may still exist: nothing here shows that a verse is said "
    "ONLY somewhere, or in 'certain' services.*"
)

SYSTEM = """You are an expert in Jewish liturgy (Ashkenaz, Sefard/Hasidic, Chabad, Edot HaMizrach) preparing the liturgy section of a research file for a scholar writing a commentary on Psalm {n}. A program has searched a fixed set of digitized prayer books and found EVERY place where words of the psalm occur. You receive its complete catalogue. Turn it into an account the scholar can rely on without checking it.

{corpus_note}

HOW TO READ THE CATALOGUE
- A unit is a verse, a run of verses, or the whole psalm. Within a unit, a PLACE is one passage of the liturgy; under it, every text in which that passage was found: rite, book, Sefaria's section path, position in the section, and what was matched ("whole v. N", or "words: …" for part of a verse).
- Sefaria's section titles are containers, not prayer names: a section titled "Ashrei" may continue into Uva LeTzion; a section titled "Amidah" may run on past the Amidah. The place label is the program's best guess from the nearest known prayer opening; the EXCERPT (the psalm's words marked ⟦…⟧) is the evidence. Name the prayer from the excerpt and your knowledge of the liturgy.
- One passage is often reprinted in many books: the weekday siddur, the Shabbat siddur, and both machzorim carry the same Pesukei Dezimra. A machzor's copy of a daily prayer does not make it a High Holiday prayer.

RULES
1. Generalise from the whole place, never from one row. If a passage appears in the siddurim of every rite, say it is said in every rite; if in the weekday and Shabbat services, say so. Name the occasions the paths and excerpts show.
2. Never infer a restriction from absence. Do not write "only", "exclusively", "in certain/some selichot", "in some communities", "in the X rite" (as if others lacked it), unless the catalogue POSITIVELY shows the restriction: a rubric in the excerpt ("on Monday and Thursday say…"), or a place whose every copy belongs to one occasion. When a rite does not appear for a passage, say nothing about that rite.
3. Distinguish the kinds of use: recited in the service; part of a piyyut or selicha (a poet's quotation or allusion); a prooftext in a text that is read or studied (the Haggadah's midrash, a mishnah of Pirkei Avot, Seder Ma'amadot); a citation inside an instruction or a kabbalistic discourse (much of Ma'avar Yabbok). Say which it is.
4. Quotation, allusion or coincidence. For "words: …" rows, decide whether the prayer is using THIS psalm (it carries the psalm's sense or setting, or a poet is weaving the phrase) or merely shares an idiom. Coincidences are dropped from the account and listed under SET ASIDE. A row noting that "the wording follows" another verse means the prayer quotes that verse (Hodu is 1 Chronicles 16, the Chronicler's version of Psalms 105 and 96): say so.
5. Quote the liturgy. For each main placement, quote the prayer's Hebrew around the psalm's words, 10–35 words taken from the excerpt, with an English translation. Never quote Hebrew that is not in an excerpt or in the psalm text given, and leave out the program's ⟦ ⟧ marks.
6. Use your knowledge to NAME and EXPLAIN what the catalogue shows (which prayer this is, where it falls in the service, what it does there). Do not add places that are not in the catalogue.
7. Where a placement is not self-explanatory (the plain sense does not obviously fit the setting), add one sentence saying so, with the traditional reason only if you know it to be documented. Do not invent reasons.
8. Rites: "Sefard" is the Hasidic rite of Ashkenazi Hasidim, never "Sephardic"; "Edot HaMizrach" is the rite of Sephardic and Middle Eastern communities.

OUTPUT (markdown; nothing before the first heading)
### The whole psalm
(only if the catalogue has a whole-psalm unit: where and when the psalm is recited in full)

### v. N (or vv. N–M): <the first words of the verse in Hebrew>
**Where:** where and when it is said, generalised as far as the catalogue shows and no further.
**The text:** the prayer's words around the verse, Hebrew, then English.
**Note:** (optional, one or two sentences: what the placement does, or why it is not self-explanatory)

Give each verse with a place in the regular services its own heading, in verse order. Gather the minor uses (a single piyyut, a selicha, a kinah, a passage of Ma'avar Yabbok or Seder Ma'amadot, an allusion) under one heading at the end:

### Echoes in piyyut, selichot and other works
- v. N, <work and place>: one or two sentences, with the words quoted.

End with exactly this block, one line per row you dropped (or "- none"):

SET ASIDE
- v. N, <place>: <why: idiom, not this psalm>

Be complete and compact: every place in the catalogue is either described, gathered under the echoes, or set aside. No preamble, no summary paragraph."""


@dataclass
class LiturgyUnitSummary:
    """What the research assembler reads for its statistics (len() and occurrence_count)."""
    label: str
    occurrence_count: int
    places: int


def split_set_aside(text: str):
    """(section without the SET ASIDE block, the block's lines)."""
    m = re.search(r"^\s*\**SET ASIDE\**:?\s*$", text, flags=re.M)
    if not m:
        return text.strip(), []
    body, tail = text[:m.start()], text[m.end():]
    rows = [ln.strip("- ").strip() for ln in tail.splitlines() if ln.strip().startswith("-")]
    return body.strip(), [r for r in rows if r and r.lower() != "none"]


def demote_headings(text: str) -> str:
    """The section sits under a `##` heading in the bundle: anything at `#`/`##` becomes `###`."""
    return re.sub(r"^#{1,2}(?=\s)", "###", text, flags=re.M)


ECHOES_HEADING = "### Echoes in piyyut, selichot and other works"

# ---------------------------------------------------------------------------
# A reused bundle (--resume, --skip-micro) keeps whatever liturgy section it was built with.
# The pipelines call `refresh_bundle_liturgy` on it, so a re-run of an old psalm always carries
# the Session-395 section (the author: re-running a psalm must overwrite the old section).
# ---------------------------------------------------------------------------

V2_MARKER = CORPUS_NOTE[:40]          # the code-written note opens every S395 section
_OLD_HEADERS = ("## Modern Jewish Liturgical Use", "## Liturgical Usage (from Sefaria")
_NEXT_H2 = re.compile(r"^## ", re.M)


def liturgy_section_is_current(bundle: str) -> bool:
    return V2_MARKER in bundle


def replace_liturgy_section(bundle: str, section: str) -> str:
    """The bundle with its liturgy section (old or new) replaced by `section`, which runs to the
    next level-2 heading; inserted before the reception or summary section when there was none."""
    section = section.rstrip() + "\n\n"
    for head in _OLD_HEADERS:
        start = bundle.find(head)
        if start >= 0:
            nxt = _NEXT_H2.search(bundle, start + len(head))
            return bundle[:start] + section + (bundle[nxt.start():] if nxt else "")
    for anchor in ("## Rabbinic and Later Reception", "## Research Summary"):
        at = bundle.find(anchor)
        if at >= 0:
            return bundle[:at] + section + bundle[at:]
    return bundle.rstrip() + "\n\n" + section


def _update_summary_lines(bundle: str, model: str, units: List["LiturgyUnitSummary"]) -> str:
    """The bundle's closing summary names the liturgy model and counts; the methods page reads them."""
    bundle = re.sub(r"(\*\*Liturgical Librarian\*\*: ).*", lambda m: m.group(1) + model, bundle)
    bundle = re.sub(r"(\*\*Liturgical prayers \(aggregated\)\*\*: ).*", lambda m: m.group(1) + str(len(units)), bundle)
    return re.sub(r"(\*\*Liturgical total occurrences\*\*: ).*",
                  lambda m: m.group(1) + str(sum(u.occurrence_count for u in units)), bundle)


def refresh_bundle_liturgy(bundle: str, psalm: int, cost_tracker=None, logger=None):
    """(bundle, refreshed?) — a bundle whose liturgy section predates Session 395 gets a new one.
    A current section is left alone ($0); `PSALMS_LITURGY=legacy` leaves every bundle alone."""
    import os
    log = logger or logging.getLogger(__name__)
    if os.environ.get("PSALMS_LITURGY", "v2") == "legacy" or liturgy_section_is_current(bundle):
        return bundle, False
    lib = LiturgicalLibrarianV2(cost_tracker=cost_tracker, logger=log)
    units = lib.find_liturgical_usage_aggregated(psalm)
    section = lib.format_for_research_bundle(units, psalm)
    if not section:
        return bundle, False
    bundle = _update_summary_lines(replace_liturgy_section(bundle, section), lib.active_model, units)
    log.info(f"[liturgy] Ps {psalm}: the reused bundle's old liturgy section was replaced "
             f"({len(units)} units, {len(section):,} chars)")
    return bundle, True


def chunk_units(n: int, units: List[lc.Unit], limit: int = CHUNK_CHARS) -> List[List[lc.Unit]]:
    """Consecutive runs of units whose rendered catalogue stays under `limit` characters."""
    parts: List[List[lc.Unit]] = [[]]
    size = 0
    for u in units:
        k = len(lc.render_for_model(n, [u]))
        if parts[-1] and size + k > limit:
            parts.append([])
            size = 0
        parts[-1].append(u)
        size += k
    return parts


def part_note(k: int, total: int, n: int, part: List[lc.Unit]) -> str:
    if total == 1:
        return ""
    return (f" This is part {k + 1} of {total} of the catalogue ({part[0].label(n)} to {part[-1].label(n)}); "
            "the other parts are written separately and joined after yours. Cover exactly the units in "
            "this part, in the same format, with its own echoes list and SET ASIDE block.")


def merge_parts(bodies: List[str]) -> str:
    """Join the parts' verse sections in order, and their echoes under one heading."""
    if len(bodies) == 1:
        return bodies[0]
    mains, echoes = [], []
    for b in bodies:
        m = re.search(r"^###\s+Echoes[ ,].*$", b, flags=re.M)
        if m:
            mains.append(b[:m.start()].strip())
            echoes.extend(ln for ln in b[m.end():].strip().splitlines() if ln.strip())
        else:
            mains.append(b.strip())
    out = "\n\n".join(x for x in mains if x)
    if echoes:
        out += f"\n\n{ECHOES_HEADING}\n" + "\n".join(echoes)
    return out


class LiturgicalLibrarianV2:
    def __init__(self, cost_tracker=None, model: str = DEFAULT_MODEL, effort: str = DEFAULT_EFFORT,
                 use_llm: bool = True, client=None, logger=None):
        self.model = model
        self.effort = effort
        self.use_llm = use_llm
        self.client = client
        self.logger = logger or logging.getLogger(__name__)
        if cost_tracker is None:
            from src.utils.cost_tracker import CostTracker
            cost_tracker = CostTracker()
        self.cost_tracker = cost_tracker
        self._markdown: Dict[int, str] = {}
        self.last_set_aside: List[str] = []

    @property
    def active_model(self) -> str:
        return self.model if self.use_llm else "none (catalogue only)"

    # -- the research assembler's interface ---------------------------------------------
    def find_liturgical_usage_aggregated(self, psalm_chapter: int, min_confidence: float = 0.75
                                         ) -> List[LiturgyUnitSummary]:
        units = lc.build_units(psalm_chapter)
        if not units:
            self._markdown[psalm_chapter] = ""
            return []
        self.last_set_aside = []
        catalogue = lc.render_for_model(psalm_chapter, units)
        if self.use_llm:
            parts = chunk_units(psalm_chapter, units)
            bodies = [self._write(psalm_chapter, lc.render_for_model(psalm_chapter, part),
                                  part_note(k, len(parts), psalm_chapter, part))
                      for k, part in enumerate(parts)]
            body = merge_parts(bodies)
        else:
            body = catalogue
        self._markdown[psalm_chapter] = self._section(psalm_chapter, body)
        self._save(psalm_chapter, catalogue)
        return [LiturgyUnitSummary(u.label(psalm_chapter), u.n_texts, len(u.places)) for u in units]

    def format_for_research_bundle(self, usage, psalm_chapter: int) -> str:
        if psalm_chapter not in self._markdown:
            self.find_liturgical_usage_aggregated(psalm_chapter)
        return self._markdown[psalm_chapter]

    # -- internals -------------------------------------------------------------------------
    def _section(self, n: int, body: str) -> str:
        if not body.strip():
            return ""
        return f"{SECTION_TITLE.format(n=n)}\n\n{CORPUS_NOTE}\n\n{demote_headings(body).strip()}\n\n"

    def _client(self):
        if self.client is None:
            import anthropic
            from dotenv import load_dotenv
            load_dotenv()
            self.client = anthropic.Anthropic(timeout=1800)
        return self.client

    def _write(self, n: int, catalogue: str, note: str = "") -> str:
        system = SYSTEM.format(n=n, corpus_note=CORPUS_NOTE)
        user = (f"Psalm {n}: the complete catalogue of where its words occur in the texts searched.{note}\n\n"
                f"{catalogue}\n\nWrite the liturgy section as instructed.")
        last_err = None
        for attempt in range(3):
            try:
                text, thinking, usage, stop = self._stream(system, user)
                self.cost_tracker.add_usage(model=self.model, input_tokens=usage.input_tokens,
                                            output_tokens=usage.output_tokens)
                self._thinking = thinking
                if stop == "refusal":
                    raise RuntimeError(f"{self.model} declined the liturgy section")
                if stop == "max_tokens":
                    self.logger.warning(f"[liturgy] Ps {n}: output cut off at {MAX_TOKENS} tokens")
                body, set_aside = split_set_aside(text)
                if not body:
                    raise RuntimeError("empty liturgy section")
                self.last_set_aside.extend(set_aside)
                self.logger.info(f"[liturgy] Ps {n}: {len(body):,} chars, {len(set_aside)} set aside "
                                 f"({usage.input_tokens:,} in / {usage.output_tokens:,} out)")
                return body
            except Exception as e:      # retried: a transient API error must not lose the section
                last_err = e
                self.logger.warning(f"[liturgy] Ps {n} attempt {attempt + 1} failed: {e}")
                time.sleep(5 * (attempt + 1))
        self.logger.error(f"[liturgy] Ps {n}: the model failed ({last_err}); the bundle gets the raw catalogue")
        return catalogue

    def _stream(self, system: str, user: str):
        kw = dict(model=self.model, max_tokens=MAX_TOKENS, system=system,
                  messages=[{"role": "user", "content": user}],
                  thinking={"type": "adaptive"}, output_config={"effort": self.effort})
        text, thinking = [], []
        with self._client().messages.stream(**kw) as s:
            for ev in s:
                if getattr(ev, "type", "") == "content_block_delta":
                    d = ev.delta
                    if getattr(d, "type", "") == "text_delta":
                        text.append(d.text)
                    elif getattr(d, "type", "") == "thinking_delta":
                        thinking.append(d.thinking)
            final = s.get_final_message()
        return "".join(text), "".join(thinking), final.usage, final.stop_reason

    def _save(self, n: int, catalogue: str) -> None:
        """The catalogue the model read, and what it set aside, beside the psalm's other files ($0 audit)."""
        try:
            d = psalm_output_dir(n, create=True)
            (d / f"psalm_{n:03d}_liturgy_catalogue.md").write_text(catalogue, encoding="utf-8")
            (d / f"psalm_{n:03d}_liturgy_set_aside.json").write_text(
                json.dumps({"model": self.active_model, "set_aside": self.last_set_aside},
                           ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as e:
            self.logger.warning(f"[liturgy] could not save the catalogue: {e}")
