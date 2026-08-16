"""
UNGROUNDED SUPERLATIVES — ranking and uniqueness claims the guide cannot support.

Session 380. The author, reading the Psalm 73 guide: "I'm seeing multiple
examples of an 'LLM verbal tic' — describing something as 'the most' something."
His three instances, and what each one actually is:

  1. "the most famous soliloquy in Spanish"        — appeal to external reputation
  2. "Leaven is the one thing barred from the altar" — FALSE, and refuted by the
     verse quoted in the same sentence
  3. "The second half is the most argued clause in the psalm" — a claim about
     scholarly consensus, unknowable in principle

Three different failures wearing one surface form. The shared mechanism is that
a superlative is a FREE INTENSIFIER: it costs no evidence and adds rhetorical
torque, so it gets reached for exactly where an argument needs force it has not
earned. Case 2 is the tell — "the one thing barred" is doing load-bearing work
(it pivots to "a leavened heart may not come near"), and the writer had Lev 2:11
on screen saying "no leaven AND NO HONEY" while writing it.

WHY THIS IS NOT A BANNED-PHRASE LIST
------------------------------------
`banned_phrases.py` works because "load-bearing" is always a tic. Superlatives
are not. Measured over the 44 finished guides: 529 raw hits, 1.62 per 1,000
words. But classifying all 20 hits in Psalm 73 by hand gives:

    6  false positives   — "the Most High" (translating עֶלְיוֹן), "the greatest
                           good" (inside the Calderón translation), "the nearest
                           antecedent" (a grammatical term)
    8  VERIFIABLE, and among the best lines in the guide — "דּוֹר בָּנֶיךָ occurs
       nowhere else in the Bible", "the poem's single Tetragrammaton"
    6  the actual tic

So a blanket ban would destroy the concordance payoff, which is the whole point
of the research pipeline. The discriminator is semantic, not lexical, and only
the copy editor can apply it. This module therefore ships TWO tiers:

  RECEPTION  — high precision. Claims about fame, canonicity or scholarly
               consensus. A guide that cites its sources cannot source these,
               so they are wrong essentially every time. Reported loudly, same
               as a banned phrase.
  CANDIDATE  — low precision, review only. The broader ranking/uniqueness
               family. NEVER reported as an error; surfaced by
               `scripts/check_superlatives.py --all` so a human can skim. Wiring
               these into the copy editor's warning channel would cry wolf at a
               ~70% false-positive rate and train the author to ignore it.

WHY THE FIX IS THE COPY EDITOR AND NOT THE WRITER
-------------------------------------------------
(1) All four Psalm 73 instances passed the copy editor untouched, so this is a
    gap in its ruleset, not a rule firing weakly.
(2) It is a local, sentence-level failure — the copy editor's job description —
    not a compositional one that needs the writer to plan differently.
(3) The standing prior, now five instances: text added to `master_editor.py`
    intending to produce restraint reliably produces its opposite.
(4) RULE 9 of the writer prompt says "Do not hedge". Any "soften your
    superlatives" instruction there collides with it head-on. The repair must
    be CUT OR GROUND, never HEDGE — which is also why the copy-editor rule text
    below never offers "perhaps" as an option.

ADDING A PATTERN
----------------
Put it in RECEPTION only if a false positive would be rare AND cheap. Everything
else goes in CANDIDATE, where a false positive costs a human two seconds of
skimming instead of an unwanted edit to prose that was fine.
"""

import re
from typing import List, NamedTuple

__all__ = [
    "RECEPTION_PATTERNS",
    "CANDIDATE_PATTERNS",
    "SuperlativeHit",
    "find_reception_claims",
    "find_candidates",
    "prompt_block",
]


class _Pattern(NamedTuple):
    label: str
    pattern: str


# ---------------------------------------------------------------------------
# TIER 1 — reception claims. Unsourceable by construction; ~always wrong.
# Deliberately narrow: each requires a reputation word, not a bare superlative.
# ---------------------------------------------------------------------------
#
# CAUTION, measured on the 89 delivered guides: an earlier draft of `fame`
# included "read" and the bare prefix "better", which matched "it is better read
# as" and "most read Job as parodying Ps 8". "is best read as" is an EXPLICITLY
# SANCTIONED hedge in COPY_EDITOR_SYSTEM_PROMPT — listed twice, as a legitimate
# flagged conjecture the editor is told NOT to delete or weaken. Pointing this
# audit at it would have set the copy editor against its own rule. The
# alternation below is therefore a fixed list of reputation words with no verbs
# of interpretation in it. Do not re-add "read".
#
# An earlier `canonicity` pattern (`the most <any adjective> <text-noun>`) was
# likewise cut: it caught "the most honest line in the psalm", which is the
# author's aesthetic judgment about the text in front of him, not a claim about
# the outside world. It now requires an explicit word of circulation.
RECEPTION_PATTERNS: List[_Pattern] = [
    _Pattern("fame", r"\b(?:most|best|better|widely)[-\s](?:famous|famed|celebrated|beloved|renowned|quoted|cited|known|loved|popular|recognizable|recognisable)\b"),
    _Pattern("consensus", r"\bmost[-\s](?:argued|debated|disputed|contested|discussed|studied|analyzed|analysed|commented)\b"),
    _Pattern("canonicity", r"\bmost[-\s](?:travelled|traveled|anthologized|anthologised|reprinted|recited|translated|sung|performed)\b"),
]

# ---------------------------------------------------------------------------
# TIER 2 — review candidates. ~30% true-positive rate; NOT errors on their own.
# ---------------------------------------------------------------------------
CANDIDATE_PATTERNS: List[_Pattern] = [
    _Pattern("the-most", r"\bthe\s+(?:single\s+)?most\s+\w+"),
    _Pattern("the-only", r"\bthe\s+only\s+\w+"),
    _Pattern("the-one", r"\bthe\s+one\s+(?:thing|word|verb|noun|place|psalm|verse|time|text|case|instance|book)\b"),
    _Pattern("est", r"\bthe\s+\w{3,}est\s+\w+"),
    _Pattern("no-other", r"\bno\s+other\s+\w+"),
    _Pattern("nowhere-else", r"\bnowhere\s+else\b"),
    _Pattern("unparalleled", r"\b(?:unparalleled|unprecedented|without\s+parallel)\b"),
]


class SuperlativeHit(NamedTuple):
    """One occurrence. `col` is the offset within `context`, so a line carrying
    two hits renders two distinct excerpts rather than one duplicated twice —
    the same trap `banned_phrases.BannedHit` documents."""

    label: str
    matched: str
    line_no: int
    context: str
    col: int


_RECEPTION = [(p, re.compile(p.pattern, re.IGNORECASE)) for p in RECEPTION_PATTERNS]
_CANDIDATE = [(p, re.compile(p.pattern, re.IGNORECASE)) for p in CANDIDATE_PATTERNS]


def _scan(text: str, compiled) -> List[SuperlativeHit]:
    """Every match, in document order, with overlapping matches collapsed.

    Several patterns are designed to catch the same site from different angles
    ("the most famous" as `fame`, "the most famous soliloquy" as `canonicity`).
    Reporting both would show the author one problem twice, so a hit whose span
    is contained in another hit's span on the same line is dropped and the
    longest match wins. Distinct sites on one line are kept — a paragraph can
    carry two.
    """
    raw = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        context = line.strip()
        lead = len(line) - len(line.lstrip())
        for pat, rx in compiled:
            for m in rx.finditer(line):
                raw.append((line_no, m.start(), m.end(), pat.label, m.group(0), context, lead))

    # Longest first at each site, so the containment test keeps the fuller match.
    raw.sort(key=lambda r: (r[0], r[1], -(r[2] - r[1])))
    kept = []
    for r in raw:
        if any(k[0] == r[0] and k[1] <= r[1] and r[2] <= k[2] for k in kept):
            continue
        kept.append(r)

    hits = [
        SuperlativeHit(label, matched, line_no, context, start - lead)
        for line_no, start, _end, label, matched, context, lead in kept
    ]
    hits.sort(key=lambda h: (h.line_no, h.col))
    return hits


def find_reception_claims(text: str) -> List[SuperlativeHit]:
    """High-precision hits only. Safe to report as probable errors."""
    return _scan(text, _RECEPTION)


def find_candidates(text: str) -> List[SuperlativeHit]:
    """The broad family. For HUMAN REVIEW — most of these are legitimate."""
    return _scan(text, _CANDIDATE)


def prompt_block() -> str:
    """The copy-editor rule text for ungrounded ranking and uniqueness claims.

    Rendered into COPY_EDITOR_SYSTEM_PROMPT as sub-item (h) of the
    argument-failure category, so it inherits that category's standing
    instruction: fix the argument, do not delete the insight.
    """
    return (
        "   (h) UNGROUNDED RANKING OR UNIQUENESS CLAIMS. A sentence asserts that\n"
        "       something is the most/least/only/first/single X, or that it is\n"
        "       unique, unparalleled or occurs nowhere else — where the guide has\n"
        "       not shown this and could not. There are three shapes, and only\n"
        "       the first two are errors:\n"
        "\n"
        "       RECEPTION CLAIMS — an appeal to fame, canonicity or scholarly\n"
        "       consensus: \"the most famous soliloquy in Spanish,\" \"its most\n"
        "       famous consolation,\" \"the most argued clause in the psalm,\"\n"
        "       \"the best-known midrash.\" These are unknowable to this guide and\n"
        "       it cites its sources for everything else. Two repairs, in order\n"
        "       of preference: (1) delete the ranking and keep the substance —\n"
        "       \"the most famous soliloquy in Spanish\" becomes \"a soliloquy in\n"
        "       Spanish\" or simply names the play; (2) where the claim is\n"
        "       actually about disagreement the guide DOES display, replace the\n"
        "       ranking with the evidence — \"the most argued clause in the psalm\"\n"
        "       becomes \"commentators divide here,\" which the surrounding\n"
        "       paragraph then demonstrates.\n"
        "\n"
        "       UNIQUENESS THE EVIDENCE CONTRADICTS, or that is clearly\n"
        "       unknowable. Test the claim against the research bundle, against\n"
        "       any text quoted nearby, and against what you know. The published\n"
        "       instance: the guide quotes Lev 2:11 as \"no leaven AND NO HONEY\n"
        "       shall you burn as an offering\" and then writes \"Leaven is the one\n"
        "       thing barred from the altar\" — refuted by the words in its own\n"
        "       sentence. Repair by scaling the claim to the evidence (\"leaven is\n"
        "       barred from the altar\"); the surrounding argument almost always\n"
        "       survives intact, because the superlative was decoration on a\n"
        "       point that stood without it.\n"
        "\n"
        "       LEAVE ALONE — claims about the biblical text's own distribution,\n"
        "       which the research bundle establishes and which are the whole\n"
        "       point of the concordance work: \"דּוֹר בָּנֶיךָ occurs nowhere else in\n"
        "       the Bible,\" \"the only imperative in the psalm,\" \"this is the\n"
        "       poem's single Tetragrammaton,\" \"the first word of Lamentations.\"\n"
        "       These are verifiable and they are among the best observations in\n"
        "       the guide. Do NOT soften, hedge or qualify them. Likewise leave\n"
        "       superlatives inside a direct quotation, a translation, or a\n"
        "       divine title (\"the Most High\" renders עֶלְיוֹן).\n"
        "\n"
        "       Never repair one of these by hedging. \"Perhaps the most famous\"\n"
        "       and \"arguably the most argued\" are worse than the original: they\n"
        "       keep the unsupported ranking and add evasion. Cut it or ground it."
    )
