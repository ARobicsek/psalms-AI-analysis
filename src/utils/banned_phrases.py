"""
BANNED PHRASES — house-style vocabulary the finished guide must not contain.

Session 374. The author's standing objection: "load-bearing" has become a verbal
tic of contemporary Claude models, and he does not want to see it in the psalms
final output.

This module is the SINGLE source of truth. Both readers derive from it:

  - `src/agents/copy_editor.py` renders `prompt_block()` into the copy-editor
    system prompt, so the model is told what to rewrite.
  - `scripts/check_banned_phrases.py` runs `find_banned()` over the finished
    text, so a phrase the model missed is reported rather than shipped silently.

Keeping the rule text and the detector on one list is deliberate. Session 373
lost an afternoon to `writer_prompt_variants.py` drifting out of lockstep with
the prompt it patched; a hand-maintained second copy of this list would fail the
same way, and the failure would be silent in exactly the direction that matters.

WHY THE FIX IS A REWRITE, NOT A SUBSTITUTION
--------------------------------------------
Do not implement this as find-and-replace. Measured over the 84 delivered guides
in `Documents/Psalm study guide/`, "load-bearing" appears 18 times in 10 guides,
and the right repair differs at every site. Two or three are live architectural
metaphors rather than tics — Psalm 8's "Cosmic strength here is structural,
load-bearing" sits inside an argument about the earth's foundations drawn from
Proverbs 8:29, and Psalm 66 has "the load-bearing wall of the whole edifice."
A swapped synonym leaves those sentences incoherent. The instruction is to
recast the sentence and keep the claim.

WHY IT IS NOT FIXED IN THE WRITER PROMPT
----------------------------------------
Two reasons. (1) The standing prior, now five instances (S368 copy editor,
S370 RULE 8b, S371 arms C/B2/B3): text added to `master_editor.py` intending to
produce restraint reliably produces its opposite, and any addition there is an
un-A/B'd delta on the arm-E prompt. (2) Naming a phrase in order to forbid it
puts the phrase in the model's context, which is the mechanism this session was
opened to remove. The upstream fix was subtractive instead: Session 374 deleted
three uses of "load-bearing" from `synthesis_discovery.py`'s own prompt, whose
observations the writer reads.

ADDING A PHRASE
---------------
Append an entry below. Keep `pattern` narrow — a false positive costs the copy
editor an edit on prose that was fine, which is the expensive direction. Prefer
matching the tic's actual surface form over matching a concept.
"""

import re
from typing import List, NamedTuple

__all__ = ["BANNED_PHRASES", "BannedHit", "find_banned", "prompt_block"]


class _Banned(NamedTuple):
    label: str      # human name, used in reports
    pattern: str    # regex, matched case-insensitively
    guidance: str   # what the copy editor should do instead


BANNED_PHRASES: List[_Banned] = [
    _Banned(
        label="load-bearing",
        pattern=r"\bload[-\s]bearing\b",
        guidance=(
            "Recast the sentence to say what the word or feature actually DOES in "
            "the poem — carries the argument, holds the structure together, is where "
            "the claim rests — or name the specific function directly. Where the "
            "surrounding sentence is genuinely about architecture (foundations, a "
            "wall, pillars), keep the architectural image and lose only this phrase. "
            "Do NOT delete the claim, and do NOT swap in a bare synonym that leaves "
            "the sentence limp."
        ),
    ),
]


class BannedHit(NamedTuple):
    """One occurrence of a banned phrase.

    Reporters must centre their excerpt on `col` rather than re-searching
    `context` for `matched`: a paragraph containing the phrase twice (Psalm 8's
    "structural, load-bearing. And its load-bearing element...") otherwise
    renders both hits with the identical excerpt and reads as a duplicate.
    """

    label: str
    matched: str
    line_no: int    # 1-indexed
    context: str    # the whole line the hit sits on, stripped
    col: int        # offset of the match within `context`


_COMPILED = [(b, re.compile(b.pattern, re.IGNORECASE)) for b in BANNED_PHRASES]


def find_banned(text: str) -> List[BannedHit]:
    """Every banned-phrase occurrence in `text`, in document order.

    Reports one hit per occurrence, not per line, so a line containing the phrase
    twice (Psalm 8 has exactly that) is counted twice.
    """
    hits: List[BannedHit] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        context = line.strip()
        lead = len(line) - len(line.lstrip())
        for banned, rx in _COMPILED:
            for m in rx.finditer(line):
                hits.append(BannedHit(
                    banned.label, m.group(0), line_no, context, m.start() - lead,
                ))
    hits.sort(key=lambda h: (h.line_no, h.col))
    return hits


def prompt_block() -> str:
    """The copy-editor rule text, generated from BANNED_PHRASES.

    Returns '' when the list is empty, so an emptied list removes the rule from
    the prompt rather than leaving a heading with nothing under it.
    """
    if not BANNED_PHRASES:
        return ""
    lines = [
        "11. BANNED HOUSE-STYLE PHRASES. The author has ruled the following out of "
        "the finished guide. Each is a verbal tic, not an error of fact, so the "
        "repair is always a REWRITE that preserves the claim — never a deletion, "
        "and never a bare synonym dropped into the same slot. Treat a sentence "
        "containing one as a sentence that has not yet found its own words.",
        "",
    ]
    for b in BANNED_PHRASES:
        lines.append(f'    - "{b.label}" — {b.guidance}')
    lines.append("")
    lines.append(
        "    This category applies to the guide's OWN prose only. If a banned "
        "phrase falls inside a direct quotation from a commentator, a translation, "
        "or any cited source, leave it exactly as it stands and change the "
        "surrounding sentence instead."
    )
    return "\n".join(lines)
