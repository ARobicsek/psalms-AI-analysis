"""
Echoes v3 — literary echoes and resonances beyond literature (Session 388, EXPERIMENTAL).

Replaces nothing yet: it writes to its own directory and never touches
data/literary_echoes/, so the production dossier and the author ledger are unchanged.

WHY (measured on the production pipeline, see docs/plans/S388_ECHOES_V3.md):
  * The Ps 77 writer's best echoes (Hopkins x2, Dickinson, on vv. 3-7) came from its OWN
    memory: both authors are banned from the dossier by the ledger, and Dickinson was the
    generator's "Default bypassed". The bans kept apt echoes out of the dossier, not out of
    the guides -- they arrived unchecked instead.
  * The generator reads the psalm blind (text only) and clusters it by topic; the writer then
    had to frame many entries as opposites ("the psalmist's memory is the opposite").
  * It quotes from memory: 8-13 of ~20 entries corrected per psalm, and verification of those
    quotations is 55-70% of a $1.2-1.4 bill.

THE SHAPE:
  1. propose  -- Opus 5.5, GPT-6 Sol and Gemini 3.1 Pro in parallel. Each reads the psalm AND
                 the macro reading, names the psalm's MOVES, then proposes candidates in two
                 lanes (literature; beyond literature: math, art, history, anthropology...).
                 NO QUOTATIONS: a work, a locus and a <=10-word anchor. Nothing to misremember,
                 and no verbatim-lyrics demand to trip Anthropic's output filter (S374).
  2. judge    -- Opus 5.5 ranks the anonymised pool, APTNESS FIRST. The author ledger is shown
                 as information and used only as a tie-break (the author's decision, S388).
  3. retrieve -- gpt-6-luna + web search copies the passage VERBATIM from a page (the S386
                 fact-checker gatherer), then every passage is checked against its live page
                 at $0 (fact_checker.verify_sources). A failed finalist is retried once; an
                 alternate is promoted if it still fails.
  4. assemble -- deterministic markdown; entries whose text could not be confirmed carry the
                 reference and the move only, never an unconfirmed quotation.
"""

from __future__ import annotations

import json
import os
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.agents.literary_echoes_parser import AuthorLedger, normalise_author
from src.utils.cost_tracker import price_tokens
from src.utils.model_effort import adaptive_thinking, apply_effort
from src.utils.openai_usage import split_input_tokens, split_output_tokens

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ECHOES_DATA_DIR = PROJECT_ROOT / "data" / "literary_echoes"

PROPOSER_MODELS = ("claude-opus-5-5", "gpt-6-sol", "gemini-3.1-pro-preview")
RETRIEVE_MODEL = "gpt-6-luna"
RETRIEVE_EFFORT = "medium"
RETRIEVE_BATCH = 5
WEB_SEARCH_USD_PER_CALL = 10.00 / 1000
OPUS_MAX_TOKENS = 128000   # S387: any Opus 5.5 call below 128K is a truncation candidate
JUDGE_MODELS = ("claude-opus-5-5", "gemini-3.1-pro-preview")   # S388 v3.1: the author asked for Gemini too
LANES = ("literature", "beyond", "far")
USED_WORKS_DIR = PROJECT_ROOT / "data" / "literary_echoes" / "used_works"   # the register: one file per guide


# ---------------------------------------------------------------------------
# Budgets (per psalm length)
# ---------------------------------------------------------------------------

def budgets(n_verses: int) -> Dict[str, int]:
    """How many candidates each proposer offers and how many each judge keeps.

    Literature finalists ~0.75 per verse (the author, S384); beyond literature and the far
    lane are 'plenty' (the author, S388)."""
    clamp = lambda x, lo, hi: max(lo, min(hi, x))
    return {
        "propose_lit": clamp(round(0.9 * n_verses), 12, 20),
        "propose_beyond": clamp(round(0.6 * n_verses), 8, 14),
        "propose_far": clamp(round(0.5 * n_verses), 6, 10),
        "final_literature": clamp(round(0.75 * n_verses), 8, 18),
        "alt_literature": 6,
        "final_beyond": clamp(round(0.6 * n_verses), 6, 14),
        "alt_beyond": 4,
        "final_far": clamp(round(0.4 * n_verses), 5, 8),
        "alt_far": 3,
    }


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

PROPOSE_PROMPT = """# Echoes and resonances for Psalm {psalm}

You are helping to build a study guide that reads Psalm {psalm} as a work of art. Its reader is literate and curious, reads Hebrew, and already owns the commentaries. What they want from you is what commentaries do not give: the places where another work -- a poem, a novel, a hymn, a painting, a proof, a historical event, a ritual, a field study, a machine -- makes the same MOVE the psalm makes, so that each lights up the other. They want to be delighted, haunted, amused and made to think, not only informed.

The guide's writer is a very widely read model and will think of the most famous comparisons by itself. Your list is most valuable where a candidate is BOTH apt AND something that writer would not reach for unaided. But if the famous comparison really is the best one for a verse, include it and mark it `"obvious": true`.

## The psalm (Hebrew verse numbering)

{psalm_text}

## A reading of the psalm (from an earlier analysis; use it, argue with it, go past it)

{reading}

## Already used in this series -- do not propose these works

These works are already quoted in the guides to other psalms, and the collection must not repeat itself. Do not propose them. Other works by the same authors are welcome.

{used_works}

## Step 1 -- the psalm's moves

Before you look for anything, name 8-14 MOVES the psalm makes. A move is concrete and specific: not a topic ("grief", "memory", "a storm") but something the poem DOES -- with an image, a verb, its syntax, its sound, its structure, its handling of time or voice or silence, or what it conspicuously leaves out. Anchor each to its verses.

## Step 2 -- echoes in literature ({n_lit} candidates)

Poetry, drama, fiction, hymns and liturgy, song, oratory, essays, the scriptures of other traditions; any language, any period. NOT the Hebrew Bible itself: its parallels (Exodus 15, Lamentations, Job...) are the commentary's job and are already covered. Each must make one of the psalm's moves (or one you add): the same image doing the same work, the same turn, the same structure -- or the same problem solved the opposite way, when the difference itself teaches something. Range widely across periods, languages and traditions. At most one candidate per author.

AT LEAST TWO of these must come from Jewish or Hebrew poetry of the last 2,000 years -- piyyut, Andalusian Hebrew verse, kinot, Hasidic song, Yiddish poetry, modern Hebrew poetry; secular or liturgical -- chosen for fit like the rest. Mark them `"jewish": true`.

## Step 3 -- resonances beyond literature ({n_beyond} candidates)

Anything that is not literature: mathematics, physics, biology, medicine, visual art, architecture, music as music, history, archaeology and ancient Near Eastern material, anthropology, sociology, psychology, economics, law, philosophy, film, technology, sport. A specific shared move, or a resonance that opens a new way into the poem. Material about the SAME event, place, object, institution or practice the psalm itself concerns is especially valuable: the other side's account, an artifact, the practice as it was actually performed. The right grain, from other psalms:
- Ps 90 ("a thousand years in Your sight are like yesterday"; "teach us to number our days"): the psychology of felt time -- why each year seems shorter than the last, and how counting changes it.
- Ps 19 ("there is no speech, there are no words... yet their line goes out through all the earth"): the Voyager Golden Record, a message built to be read by a listener who shares none of our words.
- Ps 8 ("what is man, that You are mindful of him?"): the 1990 "Pale Blue Dot" photograph and what it did to the viewer's sense of scale.
- Ps 126 ("those who sow in tears shall reap in joy"): the ethnographic record of ritual weeping at sowing.

## Step 4 -- far associations ({n_far} candidates)

Now range further. Take some of the psalm's moves and strip them of their content: state each as a bare pattern (examples from other psalms: "a vow sworn on one's own body" (Ps 137), "help found by looking past the thing you are looking at" (Ps 121), "a count that grows until counting fails" (Ps 139), "rootedness as the opposite of being blown away" (Ps 1)). Then look for that pattern somewhere far from religion and poetry. To push you past your habits, here are fields drawn at random for you: {domains}. Use them where a real bridge exists and ignore the rest; any other field is welcome too -- linguistics, shipbuilding, games, crafts, cooking, engineering, animal behaviour, anything at all.

Strange is welcome here: the association you would hesitate to say aloud, the one that makes a reader laugh or go quiet. It must still be TRUE as a fact, and once explained it must make the psalm stranger or clearer. Give the bare pattern in `pattern`.

## For every candidate

- `move`: ONE sentence naming what is shared and what differs. Never "both explore the theme of...".
- It must be REAL and LOCATABLE. Give the exact place: poem title and stanza or lines, chapter, act and scene, canto, plate, catalogue number, theorem, date, archive. DO NOT QUOTE THE PASSAGE: a later stage retrieves the exact text from a published source. Instead give `anchor`: at most 10 words from the start of the passage (or the object's title or caption) so it can be found. Describe facts accurately; if you are unsure of a detail, lower `confidence`; if you would be guessing, leave it out.
- No passage whose wording contains the most severe English profanity.

## Output

JSON only, in one ```json block, with exactly these keys:

{{"moves": [{{"id": "M1", "verses": "{psalm}:3-4", "move": "..."}}],
 "candidates": [{{"lane": "literature" | "beyond" | "far", "verses": "{psalm}:5", "move_id": "M2" (or ""),
   "domain": "poetry | piyyut | novel | hymn | song | drama | essay | scripture | visual art | music | mathematics | history | anthropology | shipbuilding | ...",
   "creator": "author, artist, composer, person or people ('' if none)", "work": "title, event, object or idea",
   "date": "...", "locus": "the exact place", "anchor": "<= 10 words", "language": "original language",
   "what": "one sentence: what the passage says, or what the object/fact is",
   "move": "one sentence: what is shared and the illuminating difference",
   "pattern": "far lane: the bare pattern; otherwise ''",
   "jewish": false, "obvious": false, "confidence": "high | medium | low"}}]}}
"""

# Step 4's random fields. Each proposer gets its own draw, so the three look in different places.
FAR_DOMAINS = (
    "shipbuilding", "sail-making", "navigation by stars", "tide tables", "knot theory", "topology", "graph theory",
    "probability", "game theory", "information theory", "cryptography", "error-correcting codes", "number theory",
    "fractals", "chaos theory", "thermodynamics", "acoustics", "optics", "crystallography", "metallurgy", "glassblowing",
    "bell-founding", "change-ringing", "organ building", "violin making", "typography", "bookbinding", "papermaking",
    "calligraphy", "cartography", "surveying", "architecture of bridges", "cathedral acoustics", "dam engineering",
    "clockmaking", "horology", "timekeeping at sea", "astronomy", "cosmology", "meteorology", "seismology",
    "volcanology", "glaciology", "oceanography", "hydrology", "geology of deserts", "soil science", "mycology",
    "botany", "tree rings", "pollination", "beekeeping", "ant colonies", "bird migration", "bird song", "whale song",
    "animal camouflage", "predator-prey behaviour", "sleep science", "dream research", "neuroscience of memory",
    "immunology", "epidemiology", "anatomy of the hand", "the physiology of fear", "anesthesia", "surgery", "genetics",
    "evolution", "palaeontology", "linguistics", "phonology", "historical linguistics", "sign languages",
    "whistled languages", "writing systems", "decipherment", "lexicography", "translation theory", "rhetoric",
    "law of evidence", "contract law", "maritime law", "courtroom procedure", "diplomacy", "treaty-making",
    "economics of debt", "insurance", "accounting", "auctions", "coinage", "cartels and trade routes",
    "military logistics", "siegecraft", "fortification", "camouflage in war", "radar", "sound-ranging", "codebreaking",
    "firefighting", "mountaineering", "polar exploration", "diving", "caving", "sailing races", "chess", "go",
    "card games", "puzzles and riddles", "magic tricks", "stage lighting", "puppetry", "dance notation", "choreography",
    "conducting", "counterpoint", "jazz improvisation", "tuning systems", "silence in music", "film editing",
    "photography", "cinema sound design", "animation", "comics", "architecture of prisons", "hospitals", "museums",
    "libraries", "archives", "urban planning", "roads and pilgrim routes", "railways", "aviation", "space flight",
    "robotics", "computer science", "algorithms", "machine learning", "debugging", "network routing", "databases",
    "search engines", "weaving", "dyeing", "embroidery", "pottery", "stone carving", "mosaic", "stained glass",
    "fresco technique", "perspective in painting", "colour theory", "cooking", "bread-making", "fermentation",
    "winemaking", "perfumery", "tea ceremony", "gardening", "irrigation", "herding and shepherding", "falconry",
    "horse-breaking", "farriery", "blacksmithing", "carpentry", "joinery", "masonry", "roof-building", "lighthouses",
    "fishing", "whaling", "salt-making", "mining", "oil lamps and lighting", "fireworks", "ballistics", "archery",
    "fencing", "wrestling", "marathon running", "team sports tactics", "gambling", "lotteries", "census-taking",
    "statistics", "demography", "migration studies", "folklore", "fairy tales", "children's games", "toys",
    "anthropology of gift exchange", "kinship systems", "funeral customs", "mourning dress", "names and naming",
    "heraldry", "flags", "maps of the underworld", "psychology of attention", "optical illusions", "perception of time",
)

JUDGE_PROMPT = """# Rate and choose the echoes and resonances for Psalm {psalm}

Several readers proposed the candidates below for a study guide that reads Psalm {psalm} as a work of art. Its reader is literate, reads Hebrew, owns the commentaries, and reads each guide for pleasure and education. They want comparisons that make the psalm read differently afterwards -- and they want to be delighted, haunted, amused and made to think. The guide's writer quotes what you choose; it can add famous comparisons of its own.

## The psalm

{psalm_text}

## A reading of the psalm

{reading}

## Rate EVERY candidate

For each candidate give integers 0-5:
- `ill` (illumination): after it, does the reader see something in the psalm they had not seen? A precise shared move scores high; so does a looser resonance that opens a new way into the poem. A shared theme with nothing more scores low.
- `tru` (truth): is it real and described accurately? 5 = sound. If the idea is good but a detail is wrong (a date, a mechanism, an attribution), score it 2-3 and write the correction in `fix` -- do NOT reject a strong idea for a fixable error. 0 = invented.
- `cra` (craft/beauty of the thing itself), `int` (interest), `fun` (humour, wit), `hau` (haunting), `mem` (memorable), `ori` (originality: would a well-read reader be surprised?), `tho` (thought-provoking).
- `note`: at most 15 words -- your honest reaction.

## Then choose

Two gates: the candidate must be true (or fixable), and it must illuminate. Past the gates, weigh illumination together with the qualities above: a candidate that is haunting, funny, beautiful or thought-provoking deserves a real boost even over one that is marginally more apt. An obvious echo that is the best one is welcome.
- Far associations are judged on their own terms: strangeness that pays off.
- In literature, include at least one Jewish or Hebrew poem of the last 2,000 years (`jewish`) when a good one exists.
- Two different passages of the same work are different candidates; keep both only if both earn it.
- Do not choose a passage from the Hebrew Bible.
- `prior_psalms` counts earlier dossiers in this series that used the creator: a tie-break only, between candidates of similar merit.
- Spread the choices across the psalm, but give a verse two when both earn it; no verse is owed one.

Choose: `literature` the best {final_lit} and `literature_alternates` the next {alt_lit}; `beyond` the best {final_beyond} and `beyond_alternates` the next {alt_beyond}; `far` the best {final_far} and `far_alternates` the next {alt_far}. Best first. Fewer is fine where fewer are good. For each choice give `id`, `verses`, `move` (ONE sharp sentence for the writer: what is shared and the illuminating difference; correct any error the candidate made), and `retrieve` (exactly what to fetch: for literature, which lines or passage, at most ~16 lines, and in which language(s); otherwise the specific fact, image or passage a reliable source should document).

## Candidates

{pool}

## Output

JSON only, in one ```json block:
{{"ratings": [{{"id": "C01", "ill": 4, "tru": 5, "cra": 3, "int": 4, "fun": 0, "hau": 2, "mem": 3, "ori": 4, "tho": 4, "note": "...", "fix": ""}}],
 "literature": [{{"id": "C07", "verses": "{psalm}:3", "move": "...", "retrieve": "..."}}],
 "literature_alternates": [...], "beyond": [...], "beyond_alternates": [...], "far": [...], "far_alternates": [...],
 "notes": "at most three sentences on the pool as a whole"}}
"""

RETRIEVE_LIT_PROMPT = """## YOUR TASK: FIND WHERE THESE PASSAGES ARE PRINTED

A study guide on Psalm {psalm} will quote the literary passages below. Your job is to FIND PAGES, not to copy the text: a program will fetch each page and cut the passage out of it.

For EACH passage give:
- `urls`: up to THREE pages that print the full text of the requested passage in plain HTML (best first). Prefer full-text sites -- Wikisource, Project Gutenberg, the Perseus Digital Library, ctext.org, Sefaria, Poetry Foundation, poets.org, a university or library edition, the author's estate -- and avoid pages that show only a snippet or render the text with JavaScript. Tag each `role` "original" (the original language) or "translation" (a published English translation; name the `translator`). For an English original, give original pages only; for a non-English original, give at least one of each when you can.
- `first_line` and `last_line`: the first and last line (or, for prose, the first and last few words) of the requested passage in the ORIGINAL language, exactly as the page prints them. `tr_first_line` and `tr_last_line`: the same for the translation (empty for an English original). These are search keys the program uses to find the passage on the page; keep them short.
- `n_lines`: how many lines (for prose, sentences) the requested passage has; at most 16.
- `locus`: the exact place as the page gives it. `public_domain`: "yes", "no" or "unknown" (for the original). `note`: one line, only if something differs from the request (a different title, stanza or attribution).

Use AT MOST TWO searches per passage (each search is paid for). `found` is false if you found no page printing the text.

Return JSON: one item per passage, with its `n`.

## PASSAGES
{items}
"""

RETRIEVE_BEYOND_PROMPT = """## YOUR TASK: FIND A RELIABLE SOURCE FOR EACH OF THESE

A study guide on Psalm {psalm} will draw on the non-literary material below (history, art, science, anthropology and so on). Your job is RETRIEVAL, not judgment and not memory.

For EACH item: search the web for a reliable page (a museum or collection page, an encyclopedia, a university or scholarly page, a primary source) that documents the specific fact, image or passage named in `retrieve`, and COPY one to four sentences VERBATIM from that page that establish it. Prefer pages anyone can open (Wikipedia, open-access journals, university pages, Smarthistory, the Met, the Louvre); AVOID the British Museum, ResearchGate, JSTOR and dokumen.pub, whose pages refuse the program that checks your quote. Never type from memory -- every passage you copy is checked against its page afterwards. Use AT MOST ONE search per item (each search is paid for). `found` is false if you found no page that documents it. `note`: one line, only if the source disagrees with the item or corrects a detail (a date, a name, a place).

Return JSON: one item per entry, with its `n`.

## ITEMS
{items}
"""

_STR = {"type": "string"}
RETRIEVE_LIT_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["claims"],
    "properties": {"claims": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["n", "found", "urls", "first_line", "last_line", "tr_first_line", "tr_last_line",
                     "n_lines", "locus", "public_domain", "note"],
        "properties": {"n": {"type": "integer"}, "found": {"type": "boolean"},
                       "urls": {"type": "array", "items": {
                           "type": "object", "additionalProperties": False,
                           "required": ["url", "role", "translator"],
                           "properties": {"url": _STR, "role": {"type": "string", "enum": ["original", "translation"]},
                                          "translator": _STR}}},
                       "first_line": _STR, "last_line": _STR, "tr_first_line": _STR, "tr_last_line": _STR,
                       "n_lines": {"type": "integer"}, "locus": _STR,
                       "public_domain": {"type": "string", "enum": ["yes", "no", "unknown"]},
                       "note": _STR}}}},
}
RETRIEVE_BEYOND_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["claims"],
    "properties": {"claims": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["n", "found", "source_title", "url", "quote", "note"],
        "properties": {"n": {"type": "integer"}, "found": {"type": "boolean"},
                       "source_title": _STR, "url": _STR, "quote": _STR, "note": _STR}}}},
}

_CANDIDATE_PROPS = {k: _STR for k in ("verses", "move_id", "domain", "creator", "work", "date", "locus",
                                      "anchor", "language", "what", "move", "pattern", "confidence")}
_CANDIDATE_PROPS["lane"] = {"type": "string", "enum": list(LANES)}
_CANDIDATE_PROPS["obvious"] = {"type": "boolean"}
_CANDIDATE_PROPS["jewish"] = {"type": "boolean"}
PROPOSE_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["moves", "candidates"],
    "properties": {
        "moves": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["id", "verses", "move"],
            "properties": {"id": _STR, "verses": _STR, "move": _STR}}},
        "candidates": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": sorted(_CANDIDATE_PROPS), "properties": _CANDIDATE_PROPS}}},
}

SCORE_KEYS = ("ill", "tru", "cra", "int", "fun", "hau", "mem", "ori", "tho")
SCORE_NAMES = {"ill": "illumination", "tru": "truth", "cra": "craft", "int": "interest", "fun": "humour",
               "hau": "haunting", "mem": "memorable", "ori": "originality", "tho": "thought-provoking"}
_INT = {"type": "integer"}
_CHOICE = {"type": "array", "items": {
    "type": "object", "additionalProperties": False, "required": ["id", "verses", "move", "retrieve"],
    "properties": {"id": _STR, "verses": _STR, "move": _STR, "retrieve": _STR}}}
JUDGE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["ratings", "notes"] + [k for lane in LANES for k in (lane, f"{lane}_alternates")],
    "properties": {
        "ratings": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["id", *SCORE_KEYS, "note", "fix"],
            "properties": {"id": _STR, **{k: _INT for k in SCORE_KEYS}, "note": _STR, "fix": _STR}}},
        "notes": _STR,
        **{k: _CHOICE for lane in LANES for k in (lane, f"{lane}_alternates")}},
}

# Bump when USED_WORKS_PROMPT changes: every cached guide is then read again (~$0.11 for 47 guides).
# v2 (S388): the psalm's own liturgical settings are not "used works" (they filled v1's register
# with "Yom Kippur Vidui", "Sefard Siddur" and the like, which the writer was told never to cite).
USED_WORKS_VERSION = 2

USED_WORKS_PROMPT = """Below is a study guide on Psalm {psalm}. List every work OUTSIDE the Hebrew Bible and the
rabbinic/medieval commentary tradition that it QUOTES or holds up as a comparison: poems, songs, hymns,
piyyutim and other liturgical poetry, novels, plays, essays, speeches, paintings and other artworks,
music, films, scientific papers, historical artifacts. Do NOT list Bible verses, the Talmud, Midrash,
Targum, the Septuagint, or commentators (Rashi, Ibn Ezra, Radak, Malbim, Meiri, and so on). Do NOT
list the prayers, services, prayer books, rites or customs in which this psalm or its verses are
recited (the guide's liturgy section reports those, and they are not echoes); DO list a piyyut or
prayer-poem that the guide quotes as a comparison.
For each give the creator ('' if none), the work's title as commonly known, and `quoted`: true if the
guide quotes words from it, false if it only refers to it.

## THE GUIDE
{guide}
"""
USED_WORKS_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["works"],
    "properties": {"works": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["creator", "work", "quoted"],
        "properties": {"creator": _STR, "work": _STR, "quoted": {"type": "boolean"}}}}},
}


def _loose(schema):
    """The same schema without additionalProperties, for Gemini's response_json_schema."""
    if isinstance(schema, dict):
        return {k: _loose(v) for k, v in schema.items() if k != "additionalProperties"}
    if isinstance(schema, list):
        return [_loose(v) for v in schema]
    return schema


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def reading_from_macro(macro: Dict) -> str:
    """The macro analysis as a compact reading: thesis, genre, structure, devices."""
    if not macro:
        return "(no earlier reading available)"
    out = []
    if macro.get("thesis_statement"):
        out.append(f"Thesis: {macro['thesis_statement']}")
    if macro.get("genre"):
        out.append(f"Genre: {macro['genre']}")
    struct = macro.get("structural_outline") or []
    if struct:
        out.append("Structure:")
        for s in struct:
            if isinstance(s, dict):
                out.append(f"- {s.get('section', '')}: {s.get('theme', '')}. {s.get('notes', '')}".strip())
    devices = macro.get("poetic_devices") or []
    if devices:
        out.append("Poetic devices:")
        for d in devices:
            if isinstance(d, dict):
                bits = [str(v) for v in d.values() if v]
                out.append("- " + " | ".join(bits))
            else:
                out.append(f"- {d}")
    return "\n".join(out)


def extract_json(text: str) -> Dict:
    """The JSON object in a model's answer: the last ```json block, else the outermost braces."""
    blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text or "", re.S)
    candidates = list(reversed(blocks))
    if text and "{" in text:
        candidates.append(text[text.index("{"): text.rindex("}") + 1])
    for c in candidates:
        try:
            return json.loads(c)
        except json.JSONDecodeError:
            continue
    raise ValueError(f"no JSON object in the answer ({len(text or '')} chars)")


def build_pool(proposals: Dict[str, Dict], seed: int = 0) -> List[Dict]:
    """Every proposer's candidates in one list, each with its move text resolved, a neutral
    id (C01...) and its source kept OUT of what the judge sees (shuffled, so order says
    nothing about the proposer either)."""
    pool = []
    for model, prop in proposals.items():
        moves = {m.get("id"): m.get("move", "") for m in prop.get("moves", []) if isinstance(m, dict)}
        for c in prop.get("candidates", []):
            if not isinstance(c, dict) or not (c.get("work") or c.get("creator")):
                continue
            c = dict(c)
            c["psalm_move"] = moves.get(c.get("move_id"), "")
            c["_source"] = model
            pool.append(c)
    random.Random(seed).shuffle(pool)
    for i, c in enumerate(pool, 1):
        c["id"] = f"C{i:02d}"
    return pool


def ledger_counts(pool: List[Dict], ledger: AuthorLedger, before_psalm: int) -> None:
    """Annotate each candidate in place with how many EARLIER psalms' dossiers used its creator."""
    for c in pool:
        rec = ledger.authors.get(normalise_author(c.get("creator", "") or ""))
        prior = sorted(p for p in (rec or {}).get("psalms", []) if p < before_psalm)
        c["prior_psalms"] = len(prior)


_JUDGE_FIELDS = ("id", "lane", "verses", "domain", "creator", "work", "date", "locus", "what",
                 "psalm_move", "move", "pattern", "jewish", "obvious", "confidence", "prior_psalms")


def pool_for_judge(pool: List[Dict]) -> str:
    rows = []
    for c in pool:
        rows.append(json.dumps({k: c.get(k) for k in _JUDGE_FIELDS if c.get(k) not in (None, "", False)},
                               ensure_ascii=False))
    return "\n".join(rows)


# -- matching works (one copy: the used-works filter, the judge merge and the S388 reports) --------

_TITLE_STOP = {"the", "and", "of", "a", "an", "in", "on", "to", "de", "la", "le", "les", "des", "der", "die",
               "das", "from", "with", "for", "book", "poem", "part", "no", "op", "song", "st", "saint"}


def _title_tokens(s: str) -> set:
    return {w for w in re.findall(r"[^\W\d_]{4,}", (s or "").lower()) if w not in _TITLE_STOP}


def same_author(a: Dict, b: Dict) -> bool:
    ka, kb = normalise_author(a.get("creator") or ""), normalise_author(b.get("creator") or "")
    return bool(ka) and ka == kb


def same_work(a: Dict, b: Dict) -> bool:
    """The same work (not necessarily the same passage). Numbered works must share a number, so
    Beethoven's Sixth and Ninth stay apart; two credits for one object ('Sennacherib's scribes' /
    'Sennacherib's royal scribes', Taylor Prism) match on two shared title words; a title too
    short to have distinctive words ('If') must match exactly."""
    wa, wb = a.get("work", ""), b.get("work", "")
    ta, tb = _title_tokens(wa), _title_tokens(wb)
    na, nb = set(re.findall(r"\d+", wa or "")), set(re.findall(r"\d+", wb or ""))
    if na and nb and not (na & nb):
        return False
    if len(ta & tb) >= 2:
        return True
    if not ta or not tb:
        return (same_author(a, b) or not (a.get("creator") and b.get("creator"))) and \
            _norm(wa) == _norm(wb) and bool(_norm(wa))
    if a.get("creator") and b.get("creator"):
        return same_author(a, b) and bool(ta & tb)
    return len(ta & tb) >= min(2, len(ta), len(tb))


def filter_used(pool: List[Dict], used: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Drop candidates whose WORK is already quoted in another psalm's guide (the author,
    S388: the collection must not repeat a poem -- Celan's 'Psalm' was quoted in the guides to
    Pss 41, 43 and 44 and chosen again for 77). Authors are not banned."""
    kept, removed = [], []
    for c in pool:
        hit = next((u for u in used if same_work(c, u)), None)
        if hit:
            removed.append(dict(c, used_in=hit.get("psalm")))
        else:
            kept.append(c)
    return kept, removed


def used_works_block(used: List[Dict]) -> str:
    rows = sorted({(u.get("creator") or "", u.get("work") or "") for u in used}, key=lambda t: (t[0].lower(), t[1]))
    return "\n".join(f"- {c + ', ' if c else ''}{w}" for c, w in rows) or "(none yet)"


UNION_FACTOR = 1.35   # two judges' union may run past one judge's budget; the author accepts longer guides


def merge_judges(judges: Dict[str, Dict], pool: List[Dict], b: Dict[str, int],
                 order: Tuple[str, ...] = ("claude-opus-5-5", "gemini-3.1-pro-preview")) -> List[Dict]:
    """Deterministic union of several judges' choices (no extra call).

    Per lane: candidates BOTH judges made finalists come first (by mean rank), then those only
    one chose, alternating by rank; the union is capped at UNION_FACTOR x the lane budget and the
    overflow joins the alternates. A candidate is placed in the lane most judges put it in. In
    literature, if no finalist is Jewish/Hebrew poetry, the best such alternate is promoted.
    The writer-facing text (move, retrieve) comes from the judge that ranked it higher."""
    by_id = {c["id"]: c for c in pool}
    models = [m for m in order if m in judges] + [m for m in judges if m not in order]
    votes: Dict[str, Dict] = {}
    for m in models:
        for lane in LANES:
            for role, key in (("final", lane), ("alternate", f"{lane}_alternates")):
                for r, sel in enumerate(judges[m].get(key) or [], 1):
                    cid = str(sel.get("id", "")).strip()
                    if cid not in by_id:
                        continue
                    v = votes.setdefault(cid, {"final": {}, "alternate": {}, "sel": {}, "lanes": []})
                    if m in v["final"] or m in v["alternate"]:
                        continue
                    v[role][m] = r
                    v["sel"][m] = sel
                    v["lanes"].append((0 if role == "final" else 1, lane))
    ratings = {m: {str(r.get("id")): r for r in judges[m].get("ratings") or []} for m in models}

    def lane_of(cid: str) -> str:
        v = votes[cid]
        best = min(role for role, _ in v["lanes"])
        lanes = [l for role, l in v["lanes"] if role == best]
        top = max(set(lanes), key=lambda l: (lanes.count(l), l == by_id[cid].get("lane")))
        return top

    def best_model(cid: str) -> str:
        v = votes[cid]
        keyed = [(0, r, models.index(m), m) for m, r in v["final"].items()] + \
                [(1, r, models.index(m), m) for m, r in v["alternate"].items()]
        return min(keyed)[3]

    def quality(cid: str) -> float:
        rs = [ratings[m][cid] for m in models if cid in ratings[m]]
        return sum(sum(int(r.get(k, 0) or 0) for k in SCORE_KEYS) for r in rs) / max(1, len(rs))

    out: List[Dict] = []
    for lane in LANES:
        ids = [cid for cid in votes if lane_of(cid) == lane]
        finals = [c for c in ids if votes[c]["final"]]
        finals.sort(key=lambda c: (-len(votes[c]["final"]),
                                   sorted(votes[c]["final"].values())[0] if len(votes[c]["final"]) == 1
                                   else sum(votes[c]["final"].values()) / len(votes[c]["final"]),
                                   models.index(next(iter(votes[c]["final"])))))
        cap = max(1, round(b[f"final_{lane}"] * UNION_FACTOR))
        keep, overflow = finals[:cap], finals[cap:]
        alts = [c for c in ids if not votes[c]["final"]]
        alts.sort(key=lambda c: (-len(votes[c]["alternate"]), min(votes[c]["alternate"].values())))
        alts = (overflow + alts)[: b[f"alt_{lane}"] + 2]
        if lane == "literature" and not any(by_id[c].get("jewish") for c in keep):
            pick = next((c for c in alts if by_id[c].get("jewish")), None)
            if pick is None:
                jew = [c["id"] for c in pool if c.get("jewish") and c.get("lane") == "literature"
                       and c["id"] not in votes and any(c["id"] in ratings[m] for m in models)]
                pick = max(jew, key=quality, default=None)
                if pick:
                    votes[pick] = {"final": {}, "alternate": {}, "sel": {}, "lanes": [(1, lane)]}
            if pick:
                alts = [c for c in alts if c != pick]
                keep.append(pick)
                votes[pick]["jewish_rule"] = True
        for role, group in (("final", keep), ("alternate", alts)):
            for rank, cid in enumerate(group, 1):
                v, c = votes[cid], by_id[cid]
                m = best_model(cid) if (v["final"] or v["alternate"]) else None
                sel = v["sel"].get(m, {}) if m else {}
                fixes = [ratings[x][cid].get("fix") for x in models if cid in ratings[x] and ratings[x][cid].get("fix")]
                chosen_by = {x: f"finalist #{r}" for x, r in v["final"].items()}
                chosen_by.update({x: f"alternate #{r}" for x, r in v["alternate"].items()})
                out.append({"id": cid, "lane": lane, "role": role, "rank": rank, "chosen_by": chosen_by,
                            "jewish_rule": bool(v.get("jewish_rule")),
                            "verses": sel.get("verses") or c.get("verses", ""),
                            "move": sel.get("move") or c.get("move", ""),
                            "retrieve": sel.get("retrieve", ""), "fix": " / ".join(dict.fromkeys(fixes))})
    return out


def _retrieve_item(c: Dict, sel: Dict, lane: str) -> Dict:
    """What the locator sees for ONE entry. The judge's `retrieve` is the authoritative locus; the
    proposer's own locus is sent only when the judge gave none (S388 Q1: two proposers can name
    different passages of one work, and the locator must not be handed both)."""
    item = {"creator": c.get("creator", ""), "work": c.get("work", ""), "date": c.get("date", ""),
            "retrieve": sel.get("retrieve") or c.get("locus", "")}
    if lane == "literature":
        item.update(anchor=c.get("anchor", "") if not sel.get("retrieve") else "", language=c.get("language", ""))
    else:
        item.update(what=c.get("what", ""), domain=c.get("domain", ""))
    if sel.get("fix"):
        item["correction"] = f"The proposer's description may be wrong: {sel['fix']} Document the correct fact."
    return item


def entry_status(e: Dict) -> str:
    """verified | page_unreadable | unconfirmed | not_found, from the $0 page checks.

    A literary entry needs its ORIGINAL on its page; a translation that fails is dropped
    but does not sink the entry. page_unreadable = the page could not be fetched (a
    JavaScript site, a 403), which is not evidence of a bad quotation."""
    r = e.get("retrieved") or {}
    if not r.get("found"):
        return "not_found"
    check = r.get("check_main", "")
    if check == "quote found on the page":
        return "verified"
    if check == "page could not be fetched or read":
        return "page_unreadable"
    if r.get("check_translation") == "quote found on the page":
        return "translation_only"
    return "unconfirmed"


# -- $0 extraction: cut the passage out of the page itself (Session 388) ------------------
#
# The first v3 run asked gpt-6-luna to COPY each passage. It returned one line of a
# public-domain Hopkins sonnet ("only a brief excerpt is provided here"), and the substring
# page check then failed correct texts on pages that print line numbers (Cowper on RPO) or
# render with JavaScript (Folger, Princeton Dante). Now the model only LOCATES the passage
# (urls + first/last line as search keys) and Python cuts it from the page, so a quotation
# is on its page by construction and its length is ours to set.

BROWSER_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/128.0 Safari/537.36",
              "Accept-Language": "en;q=0.9,*;q=0.5"}
MAX_PASSAGE_LINES = 16
MAX_PASSAGE_CHARS = 2200
_BLOCK_TAGS = r"p|div|li|h[1-6]|tr|td|blockquote|pre|section|article|dd|dt|table|ul|ol|center"


def html_to_lines(html: str) -> List[str]:
    """Visible text of a page, one printed line per list item (blank = stanza/paragraph break).
    Line numbers printed beside verse ("5", "10") are removed."""
    import html as _html
    h = re.sub(r"(?is)<(script|style|noscript|nav|footer|header)[^>]*>.*?</\1>", " ", html or "")
    h = re.sub(r"\s*\n\s*", " ", h)                      # source newlines are whitespace in HTML
    h = re.sub(r"(?i)<br\s*/?>", "\n", h)
    h = re.sub(rf"(?i)</?(?:{_BLOCK_TAGS})\b[^>]*>", "\n", h)
    h = _html.unescape(re.sub(r"(?s)<[^>]+>", " ", h)).replace("\xa0", " ").replace("\r", "")
    h = re.sub("[​‌‍﻿­]", "", h)        # zero-width marks, soft hyphens
    out: List[str] = []
    for ln in h.split("\n"):
        ln = re.sub(r"[ \t]+", " ", ln).strip()
        if re.fullmatch(r"\[?\d{1,4}\]?\.?", ln):
            continue                                        # a line number on its own line
        ln = re.sub(r"^\d{1,3}\s+(?=\D)", "", ln)          # leading line number
        ln = re.sub(r"(?<=\D)\s+\d{1,3}$", "", ln)          # trailing line number
        if ln or (out and out[-1]):
            out.append(ln)
    return out


def _norm(s: str) -> str:
    from src.agents.fact_checker import _norm_for_match
    return _norm_for_match(s)


def _line_score(key: str, line: str) -> float:
    """How well a printed line matches a search key (both normalised)."""
    if not key or not line:
        return 0.0
    if key == line:
        return 1.0
    if len(key) >= 12 and (key in line or line.startswith(key)):
        return 0.95
    if len(line) >= 12 and len(line) < len(key) and key.startswith(line):
        return 0.85                                         # the key ran past a wrapped line
    import difflib
    return difflib.SequenceMatcher(None, key, line[: len(key) + 20]).ratio()


def _cut(raw: str, key: str, at_end: bool) -> str:
    """Trim a long prose line so the passage starts at `key` (or ends after it)."""
    words = re.findall(r"\w+", key)
    words = words[-4:] if at_end else words[:4]
    if len(raw) < 1.5 * max(len(key), 40) or len(words) < 2:
        return raw
    m = None
    for m in re.finditer(r"\W+".join(map(re.escape, words)), raw, re.I):
        if not at_end:
            break
    if not m:
        return raw
    if at_end:
        end = m.end()
        tail = re.match(r"[^\w\s]*", raw[end:])            # keep the closing punctuation
        return raw[: end + (tail.end() if tail else 0)]
    return raw[m.start():]


def _non_latin(s: str) -> bool:
    return any(ch.isalpha() and ord(ch) > 0x2FF for ch in s)


def plausible_passage(text: str, first: str = "", anchored_end: bool = True) -> bool:
    """Reject what is not a passage. Measured on Ps 77's pages: a JavaScript page's interface
    text repeats itself and is one-word labels (Qur'an.com: 'Tafsirs / Leçons / Réflexions');
    a PDF whose spaces decode as a letter gives 'words' dozens of characters long (a Gita PDF:
    'Afterkseeingkthis...'); and a non-Latin original that runs into Latin page furniture."""
    lines = [l for l in text.split("\n") if l.strip()]
    if len(lines) >= 4 and len(set(lines)) / len(lines) < 0.75:
        return False
    words = text.split()
    if words and sum(len(w) for w in words) / len(words) > 14:
        return False
    if _non_latin(first) and lines and sum(map(_non_latin, lines)) / len(lines) < 0.7:
        return False
    if not anchored_end and len(first.split()) >= 3 and len(lines) >= 3:
        # no end anchor, so the cut is a line count: distrust a run of one-word lines
        if sum(len(l.split()) == 1 for l in lines) / len(lines) >= 0.4:
            return False
    return True


def extract_passage(lines: List[str], first: str, last: str = "", n_lines: int = 8,
                    max_lines: int = MAX_PASSAGE_LINES, max_chars: int = MAX_PASSAGE_CHARS,
                    threshold: float = 0.8) -> Optional[str]:
    """The passage from `first` to `last` as the page prints it, or None if `first` is not on it.
    Without a findable `last`, takes `n_lines` printed lines. Capped at `max_lines` / `max_chars`."""
    norm = [_norm(l) for l in lines]
    kf, kl = _norm(first), _norm(last)
    starts = [i for i, l in enumerate(norm) if _line_score(kf, l) >= threshold]
    if not starts:
        return None
    best = None
    if kl:
        for i in starts:
            window = range(i, min(len(norm), i + 3 * max_lines))
            ends = [j for j in window if _line_score(kl, norm[j]) >= threshold]
            if ends and (best is None or ends[0] - i < best[1] - best[0]):
                best = (i, ends[0])
    if best:
        i, j = best
        chunk = lines[i: j + 1]
    else:
        i = max(starts, key=lambda k: _line_score(kf, norm[k]))
        chunk, count = [], 0
        for ln in lines[i:]:
            chunk.append(ln)
            count += bool(ln)
            if count >= max(1, min(n_lines or 8, max_lines)):
                break
    chunk = list(chunk)
    chunk[0] = _cut(chunk[0], first, at_end=False)
    if best:
        chunk[-1] = _cut(chunk[-1], last, at_end=True)
    chunk = [ln for ln in chunk if not ln or re.search(r"\w", ln)]     # drop '##', '* * *' layout marks
    texts = [k for k, ln in enumerate(chunk) if ln]
    gaps = [any(not chunk[m] for m in range(a + 1, b)) for a, b in zip(texts, texts[1:])]
    if gaps and sum(gaps) / len(gaps) >= 0.6:
        chunk = [ln for ln in chunk if ln]        # one block element per line: the blanks are layout
    out, count = [], 0
    for ln in chunk:
        if not ln and (not out or not out[-1]):
            continue
        count += bool(ln)
        if count > max_lines:
            break
        out.append(ln)
    text = "\n".join(out).strip()
    if not plausible_passage(text, first, anchored_end=bool(best)):
        return None
    if len(text) > max_chars:
        cut = text[:max_chars]
        stop = max(cut.rfind(". "), cut.rfind("\n"))
        text = (cut[: stop + 1] if stop > max_chars // 2 else cut).rstrip() + " […]"
    return text or None


def fetch_lines(url: str, timeout: int = 20) -> Optional[List[str]]:
    """A page's printed lines ($0), or None when it cannot be fetched. PDFs come back as one
    block per page (no line structure), which still serves prose."""
    import requests
    try:
        r = requests.get(url, timeout=timeout, headers=BROWSER_UA, allow_redirects=True)
        if r.status_code >= 400:
            return None
        if "pdf" in r.headers.get("content-type", "") or url.lower().endswith(".pdf"):
            from src.agents.fact_checker import fetch_page_text
            t = fetch_page_text(url, timeout)
            return t.split("\n") if t else None
        if not r.encoding or r.encoding.lower() == "iso-8859-1":
            r.encoding = r.apparent_encoding
        return html_to_lines(r.text)
    except Exception:
        return None


def usable(e: Dict) -> bool:
    """Has text the dossier may quote. Literature: only text cut from its page (or a
    translation alone, flagged). Beyond: a quote found on its page, or one whose page could
    not be re-read (flagged as such)."""
    ok = ("verified", "translation_only") if e.get("lane") == "literature" else ("verified", "page_unreadable")
    return e.get("status") in ok


def _verse_key(v: str) -> Tuple[int, int]:
    m = re.search(r":(\d+)", v or "")
    return (int(m.group(1)) if m else 999, 0)


def _blockquote(text: str) -> List[str]:
    return [f"> {ln}" if ln.strip() else ">" for ln in (text or "").strip().split("\n")]


def assemble_markdown(psalm: int, entries: List[Dict]) -> str:
    """The dossier the writer reads. Literature, then resonances beyond literature, each in
    verse order; any entry whose text is not confirmed carries its reference and move only."""
    out = [f"# Psalm {psalm} — Echoes and Resonances (v3)", "",
           "Chosen for aptness to this psalm's moves. Quotations were copied from the page named "
           "under each and checked against it; entries marked *text not confirmed* give the "
           "reference only.", ""]
    for lane, title in (("literature", "Literary echoes"), ("beyond", "Resonances beyond literature"),
                        ("far", "Far associations")):
        chosen = [e for e in entries if e["lane"] == lane and e.get("use")]
        chosen.sort(key=lambda e: _verse_key(e.get("verses", "")))
        out += [f"## {title}", ""]
        for e in chosen:
            c, r, st = e["candidate"], e.get("retrieved") or {}, e.get("status")
            creator = c.get("creator") or ""
            head = f"### Psalm {e.get('verses', '')} — {creator + ', ' if creator else ''}*{c.get('work', '')}*"
            if c.get("date"):
                head += f" ({c['date']})"
            if lane != "literature" and c.get("domain"):
                head += f" — {c['domain']}"
            out += [head, "", f"**The move:** {e.get('move') or c.get('move', '')}", ""]
            if lane != "literature" and c.get("what"):
                out += [c["what"], ""]
            if e.get("fix"):
                out += [f"*Correction from the judge:* {e['fix']}", ""]
            if usable(e):
                if lane == "literature":
                    has_tr = r.get("check_translation") == "quote found on the page"
                    if st == "verified":
                        out += _blockquote(r.get("original", ""))
                        if has_tr:
                            out += [">"] + _blockquote(r["translation"])
                    else:
                        out += ["*(The original could not be retrieved; the translation only.)*", ""]
                        out += _blockquote(r["translation"])
                    tr = f" Translation: {r['translator']}." if r.get("translator") and has_tr else ""
                    pd = {"yes": "public domain", "no": "in copyright"}.get(r.get("public_domain", ""), "")
                    locus = (r.get("locus") or c.get("locus", "")).rstrip(". ")
                    out += ["", f"— {creator + ', ' if creator else ''}*{c.get('work', '')}*, {locus}.{tr}"
                                f"{' (' + pd + ')' if pd else ''}"]
                else:
                    out += _blockquote(r.get("quote", ""))
                    out += ["", f"— {r.get('source_title', '')}"]
                src = r.get("original_url") or r.get("url") or ""
                flag = "text checked on the page" if st in ("verified", "translation_only") else \
                    "the page could not be re-read to confirm this text"
                out += [f"Source: {src} ({flag})", ""]
                if r.get("note"):
                    out += [f"*Note:* {r['note']}", ""]
            else:
                out += [f"*Text not confirmed* — reference: {c.get('locus', '')}. Quote only if you know "
                        f"the passage exactly.", ""]
    return "\n".join(out).rstrip() + "\n"



# ---------------------------------------------------------------------------
# Writer mode (Session 388, v3.2 -- the production shape the author chose)
#
# v3.1's two judges scored every candidate and cost $0.80-1.10 a psalm; the author's call: no
# judge. Two proposers (Opus 5.5, Gemini 3.1 Pro) supply every lane at a count proportional to
# the psalm, every candidate is located and cut from its page, and the MASTER WRITER chooses,
# under targets set in forest_writer (>= 1 Jewish/Hebrew poem; >= 1 far association per 5
# verses; 0.5-1.5 literary-or-beyond items per verse). The used-works register still applies.
# ---------------------------------------------------------------------------

WRITER_PROPOSERS = ("claude-opus-5-5", "gemini-3.1-pro-preview")


def psalm_text_block(psalm: int, db_path: str = "database/tanakh.db") -> Tuple[str, int]:
    """The psalm as the proposers read it (Hebrew + English per verse), and its verse count."""
    from src.data_sources.tanakh_database import TanakhDatabase
    ps = TanakhDatabase(Path(db_path)).get_psalm(psalm)
    if not ps:
        raise RuntimeError(f"Psalm {psalm} not found in {db_path}")
    lines = []
    for v in ps.verses:
        lines += [f"**{psalm}:{v.verse}** {v.hebrew}", v.english, ""]
    return "\n".join(lines).strip(), len(ps.verses)


def budgets_writer(n_verses: int) -> Dict[str, int]:
    """Per proposer. For 21 verses: 13 literary, 8 beyond, 5 far each -- 52 candidates in all
    before duplicates, against the writer's target of 10-31 literary-or-beyond and >= 4 far."""
    clamp = lambda x, lo, hi: max(lo, min(hi, x))
    return {"propose_lit": clamp(round(0.6 * n_verses), 8, 16),
            "propose_beyond": clamp(round(0.4 * n_verses), 5, 10),
            "propose_far": clamp(round(0.25 * n_verses), 3, 6)}


def same_passage(a: Dict, b: Dict) -> bool:
    """Same work AND the same place in it. Different passages of one work stay separate
    entries (S388: Gemini's Iliad 24 and Opus's Iliad 18 are two different echoes)."""
    if not same_work(a, b):
        return False
    la, lb = a.get("locus", ""), b.get("locus", "")
    if re.search(r"\b(whole|entire|complete|full)\b", f"{la} {lb}", re.I):
        return True     # 'whole poem' contains 'stanzas 1-3'
    na, nb = set(re.findall(r"\d+", la)), set(re.findall(r"\d+", lb))
    if na and nb:
        return bool(na & nb)
    ta, tb = _title_tokens(la), _title_tokens(lb)
    return not ta or not tb or len(ta & tb) / min(len(ta), len(tb)) >= 0.5


def dedupe_passages(pool: List[Dict]) -> List[Dict]:
    """One entry per passage; a second proposer's reason is kept on the first entry."""
    kept: List[Dict] = []
    for c in pool:
        twin = next((k for k in kept if same_passage(k, c)), None)
        if twin is None:
            kept.append(dict(c, also=[]))
        else:
            twin["also"].append({"source": c["_source"], "move": c.get("move", ""), "locus": c.get("locus", "")})
    return kept


WRITER_LANES = (("literature", "Literary echoes"), ("beyond", "Resonances beyond literature"),
                ("far", "Far associations"))


def assemble_writer_dossier(psalm: int, entries: List[Dict], used: List[Dict]) -> str:
    """The unfiltered dossier the writer chooses from. No model names: the writer is told only
    that two readers proposed these independently."""
    # Headings start at ### : the dossier sits under the bundle's '## Cross-Cultural Literary
    # Echoes' section, and a '## ' inside it would end that section for every reader of the bundle.
    out = ["Two readers proposed these independently for this psalm, in three kinds: literary echoes, "
           "resonances beyond literature, and far associations (a pattern in the psalm found in a distant "
           "field). Nothing here has been ranked or filtered: there is more than you can use, and some "
           "entries miss. Where a passage or a source is quoted, it was cut from, or found on, the page "
           "named under it. *Text not confirmed* means the reference could not be checked: quote it only "
           "if you know the passage exactly.", ""]
    for lane, title in WRITER_LANES:
        chosen = sorted([e for e in entries if e["lane"] == lane], key=lambda e: _verse_key(e.get("verses", "")))
        out += [f"### {title} ({len(chosen)})", ""]
        for e in chosen:
            c, r, st = e["candidate"], e.get("retrieved") or {}, e.get("status")
            creator = c.get("creator") or ""
            head = f"#### {e.get('verses', '')} — {creator + ', ' if creator else ''}*{c.get('work', '')}*"
            head += f" ({c['date']})" if c.get("date") else ""
            if lane != "literature" and c.get("domain"):
                head += f" — {c['domain']}"
            if c.get("jewish"):
                head += " — Jewish/Hebrew poetry"
            out += [head, ""]
            if c.get("pattern"):
                out += [f"*The pattern:* {c['pattern']}", ""]
            if lane != "literature" and c.get("what"):
                out += [f"*What it is:* {c['what']}", ""]
            whys = [c.get("move", "")] + [a["move"] for a in c.get("also", []) if a.get("move")]
            out += [f"*Why it might belong:* {' / '.join(w for w in whys if w)}", ""]
            if usable(e):
                if lane == "literature":
                    has_tr = r.get("check_translation") == "quote found on the page"
                    if st == "verified":
                        out += _blockquote(r.get("original", ""))
                        if has_tr:
                            out += [">"] + _blockquote(r["translation"])
                    else:
                        out += ["*(The original could not be retrieved; the translation only.)*", ""]
                        out += _blockquote(r["translation"])
                    tr = f" Translation: {r['translator']}." if r.get("translator") and has_tr else ""
                    pd = {"yes": "public domain", "no": "in copyright"}.get(r.get("public_domain", ""), "")
                    locus = (r.get("locus") or c.get("locus", "")).rstrip(". ")
                    out += ["", f"— {creator + ', ' if creator else ''}*{c.get('work', '')}*, {locus}.{tr}"
                                f"{' (' + pd + ')' if pd else ''}"]
                else:
                    out += _blockquote(r.get("quote", ""))
                    out += ["", f"— {r.get('source_title', '')}"]
                src = r.get("original_url") or r.get("translation_url") or r.get("url") or ""
                flag = "text checked on the page" if st in ("verified", "translation_only") else \
                    "the page could not be re-read to confirm this text"
                out += [f"Source: {src} ({flag})", ""]
                if r.get("note"):
                    out += [f"*Note:* {r['note']}", ""]
            else:
                out += [f"*Text not confirmed* — reference: {c.get('locus', '')}.", ""]
    out += ["### Already used in this collection — never quote or cite these", "",
            "These works are already quoted or cited in the guides to other psalms, and the collection must "
            "never repeat one. Do not use them, even from your own knowledge. Other works by the same "
            "authors are fine.", "", used_works_block(used), ""]
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

@dataclass
class StageCost:
    stage: str
    model: str
    calls: int = 0
    input: int = 0
    cached: int = 0
    cache_write: int = 0
    output: int = 0
    reasoning: int = 0
    searches: int = 0
    usd: float = 0.0
    seconds: float = 0.0
    aborted: bool = False   # spent by a run that was stopped; kept in the total


@dataclass
class EchoesV3Result:
    psalm: int
    markdown: str
    entries: List[Dict]
    pool: List[Dict]
    proposals: Dict[str, Dict]
    judge: Dict
    costs: List[StageCost] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def total_usd(self) -> float:
        return sum(c.usd for c in self.costs)


class EchoesV3Agent:
    def __init__(self, proposers=PROPOSER_MODELS, judge_models=JUDGE_MODELS,
                 retrieve_model: str = RETRIEVE_MODEL, db_path: str = "database/tanakh.db", logger=None,
                 cost_tracker=None):
        self.proposers = tuple(proposers)
        self.cost_tracker = cost_tracker   # the pipeline's CostTracker: every call is recorded in it too
        self.judge_models = tuple(judge_models)
        self.retrieve_model = retrieve_model
        self.db_path = db_path
        self.logger = logger
        self._costs: List[StageCost] = []
        self._lock = threading.Lock()
        self._anthropic = self._openai = self._gemini = None

    # -- plumbing -------------------------------------------------------------
    def _log(self, msg: str) -> None:
        if self.logger:
            self.logger.info(msg)
        else:
            print(msg, flush=True)

    def _bill(self, stage: str, model: str, t0: float, input=0, cached=0, cache_write=0, output=0,
              reasoning=0, searches=0) -> StageCost:
        """One call's cost. Anthropic folds thinking into output (pass reasoning=0); OpenAI
        and Gemini report it separately (see price_tokens' token contract)."""
        usd = price_tokens(model, input_tokens=input, output_tokens=output, thinking_tokens=reasoning,
                           cached_input_tokens=cached, cache_write_tokens=cache_write)
        usd += searches * (0.0 if model.startswith("gemini-") else WEB_SEARCH_USD_PER_CALL)
        sc = StageCost(stage, model, 1, input, cached, cache_write, output, reasoning, searches, usd,
                       time.time() - t0)
        with self._lock:
            self._costs.append(sc)
            if self.cost_tracker is not None:
                self.cost_tracker.add_usage(model, input_tokens=input, output_tokens=output,
                                            thinking_tokens=reasoning, cache_read_tokens=cached,
                                            cache_write_tokens=cache_write)
                if searches and not model.startswith("gemini-"):
                    self.cost_tracker.add_charge(f"echoes {stage}: web search", searches * WEB_SEARCH_USD_PER_CALL,
                                                 model=model, detail=f"{searches} searches")
        return sc

    def _client_anthropic(self):
        if self._anthropic is None:
            import anthropic
            key = os.environ.get("PSALMS_ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
            if not key:
                raise RuntimeError("no Anthropic API key (PSALMS_ANTHROPIC_API_KEY / ANTHROPIC_API_KEY)")
            self._anthropic = anthropic.Anthropic(api_key=key)
        return self._anthropic

    def _client_openai(self):
        if self._openai is None:
            from openai import OpenAI
            self._openai = OpenAI(timeout=1800, max_retries=2)   # S387: long non-streamed calls
        return self._openai

    def _client_gemini(self):
        if self._gemini is None:
            from google import genai
            self._gemini = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        return self._gemini

    # -- model calls ------------------------------------------------------------
    def _call(self, stage: str, model: str, prompt: str, schema: Dict, effort: str = "high") -> Tuple[Dict, str]:
        """One JSON-returning call on any of the three vendors. Returns (json, thinking)."""
        last = None
        for attempt in range(3):
            t0 = time.time()
            try:
                if model.startswith("claude-"):
                    return self._call_claude(stage, model, prompt, t0)
                if model.startswith("gpt-"):
                    return self._call_openai(stage, model, prompt, schema, effort, t0)
                if model.startswith("gemini-"):
                    return self._call_gemini(stage, model, prompt, schema, effort, t0)
                raise ValueError(f"unknown vendor for {model}")
            except Exception as e:   # transient API errors, a truncated or non-JSON answer
                last = e
                self._log(f"  {stage} [{model}] attempt {attempt + 1} failed: {str(e)[:240]}")
                time.sleep(10 * (attempt + 1))
        raise RuntimeError(f"{stage} [{model}] failed: {last}")

    def _call_claude(self, stage, model, prompt, t0):
        kw = {"model": model, "max_tokens": OPUS_MAX_TOKENS,
              "thinking": adaptive_thinking(model),
              "messages": [{"role": "user", "content": prompt}]}
        apply_effort(kw, model, self.logger)
        text, thinking = "", []
        with self._client_anthropic().messages.stream(**kw) as stream:
            for ev in stream:
                if getattr(ev, "type", None) == "content_block_delta":
                    if hasattr(ev.delta, "text"):
                        text += ev.delta.text
                    elif hasattr(ev.delta, "thinking"):
                        thinking.append(ev.delta.thinking)
            final = stream.get_final_message()
        u = final.usage
        sc = self._bill(stage, model, t0, input=u.input_tokens or 0,
                        cached=getattr(u, "cache_read_input_tokens", 0) or 0,
                        cache_write=getattr(u, "cache_creation_input_tokens", 0) or 0,
                        output=u.output_tokens or 0)
        self._log(f"  {stage} [{model}] {sc.seconds:.0f}s ${sc.usd:.3f} out={sc.output:,} stop={final.stop_reason}")
        if final.stop_reason == "max_tokens":
            raise RuntimeError("output cut off at max_tokens")
        return extract_json(text), "".join(thinking)

    def _call_openai(self, stage, model, prompt, schema, effort, t0):
        r = self._client_openai().responses.create(
            model=model, input=[{"role": "user", "content": prompt}],
            reasoning={"effort": effort, "summary": "auto"}, max_output_tokens=64000,
            text={"format": {"type": "json_schema", "name": "echoes", "schema": schema, "strict": True}})
        fresh, cached, write = split_input_tokens(r.usage)
        out, rsn = split_output_tokens(r.usage)
        sc = self._bill(stage, model, t0, input=fresh, cached=cached, cache_write=write, output=out, reasoning=rsn)
        self._log(f"  {stage} [{model}] {sc.seconds:.0f}s ${sc.usd:.3f} out={out:,} reasoning={rsn:,} status={r.status}")
        summary = "\n\n".join(s.text for it in r.output if it.type == "reasoning" for s in (it.summary or []))
        return json.loads(r.output_text), summary

    def _call_gemini(self, stage, model, prompt, schema, effort, t0):
        from google.genai import types
        r = self._client_gemini().models.generate_content(
            model=model, contents=prompt, config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level=effort, include_thoughts=True),
                response_mime_type="application/json", response_json_schema=_loose(schema)))
        um = r.usage_metadata
        cached = getattr(um, "cached_content_token_count", 0) or 0
        sc = self._bill(stage, model, t0, input=(um.prompt_token_count or 0) - cached, cached=cached,
                        output=um.candidates_token_count or 0, reasoning=um.thoughts_token_count or 0)
        self._log(f"  {stage} [{model}] {sc.seconds:.0f}s ${sc.usd:.3f} out={sc.output:,} thinking={sc.reasoning:,}")
        thoughts = [p.text for p in r.candidates[0].content.parts if getattr(p, "thought", False) and p.text]
        return extract_json(r.text or ""), "\n\n".join(thoughts)

    # -- retrieval ----------------------------------------------------------------
    def _retrieve(self, psalm: int, lane: str, items: List[Dict]) -> List[Dict]:
        """gpt-6-luna + web search, in batches; returns one dict per item (same order)."""
        from src.agents.fact_checker import FactChecker
        fc = FactChecker(model="gpt-6-sol", web_model=self.retrieve_model, logger=self.logger,
                         client=self._client_openai())
        prompt_t = RETRIEVE_LIT_PROMPT if lane == "literature" else RETRIEVE_BEYOND_PROMPT
        schema = RETRIEVE_LIT_SCHEMA if lane == "literature" else RETRIEVE_BEYOND_SCHEMA
        batches = [items[i:i + RETRIEVE_BATCH] for i in range(0, len(items), RETRIEVE_BATCH)]

        def run(bi: int) -> List[Dict]:
            block = json.dumps([dict(it, n=k) for k, it in enumerate(batches[bi], 1)], ensure_ascii=False, indent=1)
            t0 = time.time()
            res = fc._loop(f"retrieve {lane} {bi + 1}/{len(batches)}", self.retrieve_model, RETRIEVE_EFFORT,
                           [{"type": "input_text", "text": prompt_t.format(psalm=psalm, items=block)}],
                           [{"type": "web_search", "search_context_size": "low"}], schema, "",
                           f"echoes-v3-retrieve-ps{psalm}")
            u = res["usage"]
            self._bill(f"retrieve_{lane}", self.retrieve_model, t0, input=u["input"], cached=u["cached"],
                       cache_write=u.get("cache_write", 0), output=u["output"], reasoning=u["reasoning"],
                       searches=res["searches"])
            by_n = {r.get("n"): r for r in res["records"] if isinstance(r, dict)}
            return [by_n.get(k, {"found": False, "note": "no answer returned"}) for k in range(1, len(batches[bi]) + 1)]

        with ThreadPoolExecutor(max_workers=4) as ex:
            out = list(ex.map(run, range(len(batches))))
        return [r for batch in out for r in batch]

    @staticmethod
    def _page_check(lane: str, retrieved: List[Dict]) -> Dict[str, int]:
        """$0. Literature: fetch each located page and CUT the passage out of it
        (`extract_passage`), trying the urls in order; the text is then on its page by
        construction. Beyond literature: look for the gathered quote on its page
        (fact_checker.verify_sources)."""
        if lane != "literature":
            # fact_checker.verify_sources announces itself as a fact-checker in its User-Agent,
            # and museum sites refuse it (Ps 76: 4 of 6 pages unreadable). Same test, browser fetch.
            from src.agents.fact_checker import quote_on_page
            found = [r for r in retrieved if r.get("found") and r.get("url")]
            urls = sorted({r["url"] for r in found})
            with ThreadPoolExecutor(max_workers=8) as ex:
                pages = dict(zip(urls, ex.map(fetch_lines, urls)))
            counts = {"sources": len(found), "verified": 0, "page_unreadable": 0}
            for r in found:
                lines = pages.get(r["url"])
                if lines is None:
                    r["check_main"] = "page could not be fetched or read"
                    counts["page_unreadable"] += 1
                elif quote_on_page(r.get("quote", ""), " ".join(lines)):
                    r["check_main"] = "quote found on the page"
                    counts["verified"] += 1
                else:
                    r["check_main"] = "quote NOT found on the page"
            return counts

        urls = sorted({u.get("url", "") for r in retrieved if r.get("found") for u in r.get("urls", []) if u.get("url")})
        with ThreadPoolExecutor(max_workers=8) as ex:
            pages = dict(zip(urls, ex.map(fetch_lines, urls)))
        counts = {"original": 0, "translation": 0, "unreadable_pages": sum(v is None for v in pages.values())}
        for r in retrieved:
            if not r.get("found"):
                continue
            for role, first, last, text_key, url_key, check_key in (
                    ("original", r.get("first_line", ""), r.get("last_line", ""), "original", "original_url", "check_main"),
                    ("translation", r.get("tr_first_line", ""), r.get("tr_last_line", ""), "translation",
                     "translation_url", "check_translation")):
                cands = [u for u in r.get("urls", []) if u.get("role") == role and u.get("url")]
                if not cands or not first:
                    continue
                readable = False
                for u in cands:
                    lines = pages.get(u["url"])
                    if lines is None:
                        continue
                    readable = True
                    text = extract_passage(lines, first, last, r.get("n_lines") or 8)
                    if text:
                        r[text_key], r[url_key], r[check_key] = text, u["url"], "quote found on the page"
                        if role == "translation":
                            r["translator"] = u.get("translator", "")
                        counts[role] += 1
                        break
                else:
                    r[check_key] = ("quote NOT found on the page" if readable
                                    else "page could not be fetched or read")
        return counts

    def _retrieve_and_check(self, psalm: int, lane: str, entries: List[Dict]) -> None:
        if not entries:
            return
        items = [_retrieve_item(e["candidate"], e, lane) for e in entries]
        got = self._retrieve(psalm, lane, items)
        counts = self._page_check(lane, got)
        self._log(f"  page check [{lane}]: {counts}")
        for e, r in zip(entries, got):
            e["retrieved"] = r
            e["status"] = entry_status(e)

    # -- the run ----------------------------------------------------------------
    def run(self, psalm: int, psalm_text: str, n_verses: int, macro: Optional[Dict] = None,
            out_dir: Optional[Path] = None, resume: bool = False) -> EchoesV3Result:
        """`resume`: reuse the saved proposals and judge choices in `out_dir` (and their costs,
        from stage_costs.json) and redo only retrieval and assembly."""
        self._costs = []
        b = budgets(n_verses)
        reading = reading_from_macro(macro or {})
        notes: List[str] = []
        out_dir = Path(out_dir) if out_dir else None
        if out_dir:
            (out_dir / "thinking").mkdir(parents=True, exist_ok=True)

        saved = out_dir and resume and (out_dir / "judge.json").exists() and (out_dir / "pool.json").exists()
        if saved:
            pool = json.loads((out_dir / "pool.json").read_text(encoding="utf-8"))
            judge = json.loads((out_dir / "judge.json").read_text(encoding="utf-8"))
            proposals = {f.stem[len("proposal_"):]: json.loads(f.read_text(encoding="utf-8"))
                         for f in sorted(out_dir.glob("proposal_*.json"))}
            cf = out_dir / "stage_costs.json"
            prior = json.loads(cf.read_text(encoding="utf-8")) if cf.exists() else []
            self._costs = [StageCost(**c) for c in prior if not c["stage"].startswith(("retrieve", "assemble"))
                           or c.get("aborted")]
            notes.append(f"resumed: reused {len(proposals)} proposals and the judge's choices")
            self._log(f"[echoes v3] Ps {psalm}: resuming from {out_dir} ({len(pool)} candidates, "
                      f"${sum(c.usd for c in self._costs):.2f} already spent)")
        else:
            pool, judge, proposals = self._propose_and_judge(psalm, psalm_text, b, reading, notes, out_dir)
        return self._finish(psalm, pool, judge, proposals, notes, out_dir)

    def _save_costs(self, out_dir: Optional[Path]) -> None:
        if out_dir:
            from dataclasses import asdict
            (out_dir / "stage_costs.json").write_text(
                json.dumps([asdict(c) for c in self._costs], indent=1), encoding="utf-8")

    def used_works(self, exclude_psalm: int, parallel: int = 8) -> List[Dict]:
        """Every work QUOTED in the finished guides to other psalms (S388, the author's point 7:
        no poem twice in the collection). gpt-6-luna reads each copy-edited guide once (~$0.002);
        the answer is cached beside the guide's mtime in output/_echoes_used_works/."""
        USED_WORKS_DIR.mkdir(parents=True, exist_ok=True)
        guides = []
        for g in sorted(PROJECT_ROOT.glob("output/psalm_*/psalm_*_copy_edited.md")):
            n = int(re.search(r"psalm_(\d+)_copy_edited", g.name).group(1))
            if n != exclude_psalm:
                guides.append((n, g))

        def read(item):
            n, g = item
            cache = USED_WORKS_DIR / f"psalm_{n:03d}.json"
            mtime = g.stat().st_mtime
            if cache.exists():
                c = json.loads(cache.read_text(encoding="utf-8"))
                if c.get("mtime") == mtime and c.get("version") == USED_WORKS_VERSION:
                    return n, c["works"]
            try:
                got, _ = self._call("used_works", RETRIEVE_MODEL,
                                    USED_WORKS_PROMPT.format(psalm=n, guide=g.read_text(encoding="utf-8")),
                                    USED_WORKS_SCHEMA, effort="low")
            except Exception as e:
                self._log(f"  used works: Ps {n} failed ({str(e)[:120]}); skipped")
                return n, []
            works = got.get("works", [])
            cache.write_text(json.dumps({"mtime": mtime, "version": USED_WORKS_VERSION, "works": works}, ensure_ascii=False, indent=1), encoding="utf-8")
            return n, works

        with ThreadPoolExecutor(max_workers=parallel) as ex:
            found = list(ex.map(read, guides))
        # The author (S388): "keep a register of used works and never reuse them" -- a work the
        # guide only CITES as a comparison is used too. The register is the latest guide per
        # psalm: a regenerated guide replaces its psalm's entry.
        return [dict(w, psalm=n) for n, works in found for w in works]

    def run_for_writer(self, psalm: int, psalm_text: str, n_verses: int, macro: Optional[Dict] = None,
                       out_dir: Optional[Path] = None) -> EchoesV3Result:
        """v3.2, the production shape: two proposers, no judge, every candidate located and cut
        from its page; the writer chooses. Returns the dossier the research bundle carries."""
        self._costs = []
        notes: List[str] = []
        out_dir = Path(out_dir) if out_dir else None
        if out_dir:
            (out_dir / "thinking").mkdir(parents=True, exist_ok=True)
        b = budgets_writer(n_verses)
        reading = reading_from_macro(macro or {})
        used = self.used_works(psalm)
        self._log(f"[echoes] Ps {psalm}: {len(used)} works in the used-works register (other psalms); "
                  f"proposing on {', '.join(self.proposers)}, {b} each")

        def prompt_for(model):
            rng = random.Random(f"{psalm}-{model}")
            return PROPOSE_PROMPT.format(psalm=psalm, psalm_text=psalm_text, reading=reading,
                                         used_works=used_works_block(used), n_lit=b["propose_lit"],
                                         n_beyond=b["propose_beyond"], n_far=b["propose_far"],
                                         domains=", ".join(rng.sample(FAR_DOMAINS, 15)))

        def propose(model):
            try:
                return model, *self._call("propose", model, prompt_for(model), PROPOSE_SCHEMA)
            except Exception as e:
                notes.append(f"proposer {model} failed: {e}")
                self._log(f"  proposer {model} FAILED: {e}")
                return model, None, ""

        with ThreadPoolExecutor(max_workers=len(self.proposers)) as ex:
            results = list(ex.map(propose, self.proposers))
        proposals = {m: p for m, p, _ in results if p}
        if not proposals:
            raise RuntimeError("every proposer failed")
        pool, removed = filter_used(build_pool(proposals, seed=psalm), used)
        pool = [c for c in pool if c.get("lane") in LANES]
        pool = dedupe_passages(pool)
        if removed:
            notes.append(f"{len(removed)} candidate(s) dropped as already used in another guide: " +
                         "; ".join(f"{c.get('creator') or ''} {c.get('work', '')} (Ps {c['used_in']})".strip()
                                   for c in removed))
        entries = [{"id": c["id"], "lane": c["lane"], "role": "final", "rank": 0, "candidate": c,
                    "verses": c.get("verses", ""), "move": c.get("move", ""), "retrieve": "", "use": True}
                   for c in pool]
        self._log(f"[echoes] {len(entries)} candidates after the register ({len(removed)} dropped) and "
                  f"duplicates; locating and cutting their texts")
        for lane in LANES:
            self._retrieve_and_check(psalm, lane, [e for e in entries if e["lane"] == lane])
        failed = [e for e in entries if not usable(e)]
        if failed:
            for e in failed:
                prev = e.get("retrieved") or {}
                e["retrieve"] = (f"{e['candidate'].get('locus', '')} [An earlier attempt failed: "
                                 f"{prev.get('check_main') or prev.get('note') or 'not found'}. "
                                 f"Find a different page that prints the text.]")
            self._log(f"[echoes] retrying {len(failed)} entries once")
            for lane in LANES:
                self._retrieve_and_check(psalm, lane, [e for e in failed if e["lane"] == lane])
        for e in entries:
            e.setdefault("status", "not_retrieved")
        md = assemble_writer_dossier(psalm, entries, used)
        record = {"mode": "writer", "used_works": len(used), "dropped_as_used": removed}
        res = EchoesV3Result(psalm, md, entries, pool, proposals, record, list(self._costs), notes)
        if out_dir:
            for m, p, th in results:
                (out_dir / f"prompt_propose_{m}.txt").write_text(prompt_for(m), encoding="utf-8")
                if p:
                    (out_dir / f"proposal_{m}.json").write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
                    (out_dir / "thinking" / f"propose_{m}.txt").write_text(th or "", encoding="utf-8")
            (out_dir / "pool.json").write_text(json.dumps(pool, ensure_ascii=False, indent=1), encoding="utf-8")
            (out_dir / "judge.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
            (out_dir / "final.md").write_text(md, encoding="utf-8")
            (out_dir / "entries.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
            (out_dir / "cost_report.json").write_text(json.dumps(cost_report(res), indent=1), encoding="utf-8")
            self._save_costs(out_dir)
        return res

    def _propose_and_judge(self, psalm, psalm_text, b, reading, notes, out_dir):
        # 0. the works the collection has already quoted
        used = self.used_works(psalm)
        self._log(f"[echoes v3.1] {len(used)} works already quoted in other guides")

        # 1. propose (parallel, three families; each gets its own random draw of far fields)
        def prompt_for(model):
            rng = random.Random(f"{psalm}-{model}")
            return PROPOSE_PROMPT.format(psalm=psalm, psalm_text=psalm_text, reading=reading,
                                         used_works=used_works_block(used), n_lit=b["propose_lit"],
                                         n_beyond=b["propose_beyond"], n_far=b["propose_far"],
                                         domains=", ".join(rng.sample(FAR_DOMAINS, 15)))
        self._log(f"[echoes v3.1] Ps {psalm}: proposing ({', '.join(self.proposers)}), budgets {b}")

        def propose(model):
            try:
                return model, *self._call("propose", model, prompt_for(model), PROPOSE_SCHEMA)
            except Exception as e:
                notes.append(f"proposer {model} failed: {e}")
                self._log(f"  proposer {model} FAILED: {e}")
                return model, None, ""

        with ThreadPoolExecutor(max_workers=len(self.proposers)) as ex:
            results = list(ex.map(propose, self.proposers))
        proposals = {m: p for m, p, _ in results if p}
        if not proposals:
            raise RuntimeError("every proposer failed")
        if out_dir:
            (out_dir / "used_works.json").write_text(json.dumps(used, ensure_ascii=False, indent=1), encoding="utf-8")
            for m, p, th in results:
                (out_dir / f"prompt_propose_{m}.txt").write_text(prompt_for(m), encoding="utf-8")
                if p:
                    (out_dir / f"proposal_{m}.json").write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
                    (out_dir / "thinking" / f"propose_{m}.txt").write_text(th or "", encoding="utf-8")
        self._save_costs(out_dir)

        # 2. drop works already used elsewhere, then two judges in parallel
        pool, removed = filter_used(build_pool(proposals, seed=psalm), used)
        if removed:
            notes.append(f"{len(removed)} candidate(s) dropped as already quoted in another guide: " +
                         "; ".join(f"{c.get('creator') or ''} {c.get('work', '')} (Ps {c['used_in']})".strip()
                                   for c in removed))
        ledger_counts(pool, AuthorLedger.build(ECHOES_DATA_DIR, exclude_psalm=psalm), psalm)
        jprompt = JUDGE_PROMPT.format(
            psalm=psalm, psalm_text=psalm_text, reading=reading, pool=pool_for_judge(pool),
            final_lit=b["final_literature"], alt_lit=b["alt_literature"], final_beyond=b["final_beyond"],
            alt_beyond=b["alt_beyond"], final_far=b["final_far"], alt_far=b["alt_far"])
        self._log(f"[echoes v3.1] judging a pool of {len(pool)} candidates ({len(removed)} dropped as used) "
                  f"on {', '.join(self.judge_models)}")

        def judge(model):
            try:
                return model, *self._call("judge", model, jprompt, JUDGE_SCHEMA)
            except Exception as e:
                notes.append(f"judge {model} failed: {e}")
                self._log(f"  judge {model} FAILED: {e}")
                return model, None, ""

        with ThreadPoolExecutor(max_workers=len(self.judge_models)) as ex:
            jres = list(ex.map(judge, self.judge_models))
        judges = {m: j for m, j, _ in jres if j}
        if not judges:
            raise RuntimeError("every judge failed")
        selections = merge_judges(judges, pool, b, order=self.judge_models)
        record = {"judges": judges, "selections": selections, "dropped_as_used": removed}
        if out_dir:
            (out_dir / "prompt_judge.txt").write_text(jprompt, encoding="utf-8")
            (out_dir / "pool.json").write_text(json.dumps(pool, ensure_ascii=False, indent=1), encoding="utf-8")
            (out_dir / "judge.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
            for m, _, th in jres:
                (out_dir / "thinking" / f"judge_{m}.txt").write_text(th or "", encoding="utf-8")
        self._save_costs(out_dir)
        return pool, record, proposals

    def _finish(self, psalm, pool, judge, proposals, notes, out_dir) -> EchoesV3Result:
        by_id = {c["id"]: c for c in pool}
        entries: List[Dict] = []
        for sel in judge["selections"]:
            c = by_id[sel["id"]]
            entries.append({**sel, "candidate": c, "use": sel["role"] == "final"})

        # 3. retrieve + $0 page check: finalists, then one retry of failures, then alternates
        self._log(f"[echoes v3.1] retrieving {sum(e['role'] == 'final' for e in entries)} finalists")
        for lane in LANES:
            self._retrieve_and_check(psalm, lane, [e for e in entries if e["lane"] == lane and e["role"] == "final"])
        for lane in LANES:
            failed = [e for e in entries if e["lane"] == lane and e["role"] == "final" and not usable(e)]
            if not failed:
                continue
            self._log(f"[echoes v3] {len(failed)} {lane} finalist(s) failed; retrying once and fetching alternates")
            for e in failed:
                prev = e["retrieved"]
                e["retrieve"] = (e["retrieve"] + f" [An earlier attempt failed: "
                                 f"{prev.get('check_main') or prev.get('note') or 'not found'}. "
                                 f"Find a different page that prints the text.]")
            alts = [e for e in entries if e["lane"] == lane and e["role"] == "alternate"][:len(failed)]
            self._retrieve_and_check(psalm, lane, failed + alts)
            still = [e for e in failed if not usable(e)]
            for alt in [a for a in alts if usable(a)][:len(still)]:
                alt["use"] = True
                alt["promoted"] = True
        for e in entries:
            e.setdefault("status", "not_retrieved")

        md = assemble_markdown(psalm, entries)
        res = EchoesV3Result(psalm, md, entries, pool, proposals, judge, list(self._costs), notes)
        if out_dir:
            (out_dir / "final.md").write_text(md, encoding="utf-8")
            (out_dir / "entries.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
            (out_dir / "cost_report.json").write_text(json.dumps(cost_report(res), indent=1), encoding="utf-8")
            self._save_costs(out_dir)
        return res

    def reextract(self, psalm: int, out_dir: Path) -> EchoesV3Result:
        """$0: cut the literary passages again from the pages a finished run located (after a
        change to the extractor), re-read the non-literary pages, and rebuild the dossier.
        Nothing is sent to a model; the saved costs carry over unchanged."""
        out_dir = Path(out_dir)
        entries = json.loads((out_dir / "entries.json").read_text(encoding="utf-8"))
        pool = json.loads((out_dir / "pool.json").read_text(encoding="utf-8"))
        judge = json.loads((out_dir / "judge.json").read_text(encoding="utf-8"))
        proposals = {f.stem[len("proposal_"):]: json.loads(f.read_text(encoding="utf-8"))
                     for f in sorted(out_dir.glob("proposal_*.json"))}
        self._costs = [StageCost(**c) for c in json.loads((out_dir / "stage_costs.json").read_text(encoding="utf-8"))]
        for lane in LANES:
            got = [e for e in entries if e["lane"] == lane and e.get("retrieved")]
            for e in got:
                if lane == "literature":
                    for k in ("original", "original_url", "translation", "translation_url", "check_main",
                              "check_translation"):
                        e["retrieved"].pop(k, None)
                else:
                    e["retrieved"].pop("check_main", None)
            self._log(f"  re-extract [{lane}]: {self._page_check(lane, [e['retrieved'] for e in got])}")
            for e in got:
                e["status"] = entry_status(e)
        md = assemble_markdown(psalm, entries)
        res = EchoesV3Result(psalm, md, entries, pool, proposals, judge, list(self._costs),
                             ["re-extracted at $0 from the saved page locations"])
        (out_dir / "final.md").write_text(md, encoding="utf-8")
        (out_dir / "entries.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
        (out_dir / "cost_report.json").write_text(json.dumps(cost_report(res), indent=1), encoding="utf-8")
        return res


def cost_report(res: EchoesV3Result) -> Dict:
    stages: Dict[str, Dict] = {}
    for c in res.costs:
        key = f"{c.stage} [{c.model}]"
        s = stages.setdefault(key, {"calls": 0, "usd": 0.0, "input": 0, "cached": 0, "output": 0,
                                    "reasoning": 0, "searches": 0, "seconds": 0.0})
        for k in ("input", "cached", "output", "reasoning", "searches"):
            s[k] += getattr(c, k)
        s["calls"] += 1
        s["usd"] = round(s["usd"] + c.usd, 4)
        s["seconds"] = round(s["seconds"] + c.seconds, 1)
    st = {}
    for e in res.entries:
        key = f"{e['lane']}/{e['role']}/{e.get('status')}"
        st[key] = st.get(key, 0) + 1
    return {"psalm": res.psalm, "total_usd": round(res.total_usd, 4), "stages": stages,
            "pool": {m: len(p.get("candidates", [])) for m, p in res.proposals.items()},
            "entry_status": st,
            "used": {lane: sum(1 for e in res.entries if e["lane"] == lane and e.get("use")) for lane in LANES},
            "notes": res.notes}
