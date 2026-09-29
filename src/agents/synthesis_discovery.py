"""
Synthesis Discovery Agent — "Synthesis Scholar" (Session 347; prompt v2 Session 357)

Synthesis DISCOVERY pass — a sidecar that produces calibrated observations the
production one-call Master Writer can weave into its commentary at its own
discretion. NOT a structural spine: the writer keeps full authorial control.
See docs/session_tracking/IMPLEMENTATION_LOG.md (Sessions 347, 357) and
docs/plans/SYNTHESIS_SCHOLAR_PROMPT_V2_DRAFT.md for design rationale; the v2
prompt was validated against v1 in a blind A/B on Psalms 67/60/49
(scripts/run_synthesis_ab.py).

What this agent is FOR
----------------------
Two species of "aha" observation:
- TYPE P (pattern): patterns visible only when reading two or more verses
  together — a root doing double duty across the psalm, a tense/aspect arc
  that is the plot in disguise.
- TYPE C (connection): abductive cross-source synthesis — facts the dossier
  (or standard scholarship) holds separately that explain EACH OTHER: an
  anomaly and its best explanation, an overdetermined liturgical custom, an
  idiom invoked/avoided, a lexical choice driven by sound. The novelty lives
  in the linkage, not the constituent facts.

What this agent is NOT
----------------------
- Not an extractor of items already in the research bundle.
- Not a spine: it does not assign anchor verses or mandate where claims land.
- Not quota-driven: it outputs only what survives a novelty-of-linkage filter,
  a hardened evidence-honesty audit, and an "aha" (boredom) audit. Interpretive
  conjecture is permitted but must be flagged CONJECTURE and pay explanatory
  rent.

Output
------
A markdown block (a flat, UNRANKED list of observations ordered by primary
verse — Session 358 v2.1 removed the governing/core/additional tiering so
the Master Writer selects and weights on its own judgment — each with
Type / Confidence / Anchors / Payoff fields) saved to:
    output/psalm_NNN/psalm_NNN_synthesis_discovery.md

The Master Writer prompt assembly splices this in as a new INPUT block labelled
"CROSS-VERSE OBSERVATIONS (use where they fit; do NOT structure your commentary
around them)". Items marked CONJECTURE must be rendered as conjecture in prose.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import anthropic
from dotenv import load_dotenv

from src.utils.cost_tracker import CostTracker
from src.utils.logger import get_logger
from src.utils.model_effort import apply_effort, effort_for


load_dotenv()


# Session 387: Opus 5.5 (effort high, set in model_effort.py). S383 traced the Ps 76
# originality lift to THIS stage on 5.5; the author adopted 5.5 for every Opus stage.
DEFAULT_MODEL = "claude-opus-5-5"


# =============================================================================
# Prompt v2 "Synthesis Scholar" (Session 357) — same INPUT BLOCKS the Master
# Writer sees, so the discovery pass reasons over identical evidence. Changes
# from v1 (Session 347), validated in a blind A/B on Pss 67/60/49:
#   - TWO SPECIES: TYPE P (cross-verse pattern, the v1 scope) + TYPE C
#     (cross-source abductive connection: anomaly→explanation, overdetermined
#     customs, idiom invoked/avoided, sound-as-motive for lexical choice).
#   - GENERATION: surprise inventory → per-source synthesis substrate →
#     deliberate collision pass (replaces the v1 pattern-type menu).
#   - NOVELTY tested on the LINKAGE, not the constituent facts (v1 cut any
#     candidate containing a famous fact, which suppressed exactly the
#     known-facts-newly-connected insights).
#   - CONJECTURE licensed if flagged and explanatory (filter (g)); the
#     Session-346-derived evidence-honesty failure modes (a)-(j) are kept.
#   - AHA AUDIT (boredom cut) + Type/Confidence/Anchors/Payoff output fields.
# The exact A/B-tested v2 text lives in scripts/synthesis_ab_prompts.py; the
# production copy below additionally instructs reconstruct-and-diff on
# reworked source formulas (so omissions, not just alterations, surface).
# =============================================================================

INPUTS_HEADER = """You are a SYNTHESIS SCHOLAR for Psalm {psalm_number}.

Below is the full research dossier the Master Writer will see when it writes
the commentary. The dossier was assembled by specialist agents that do not
talk to each other: a structural analyst, a verse-by-verse philologist,
lexicon and concordance librarians, a liturgical-reception librarian,
deep-research essays, and a cross-cultural literary-echoes researcher. Each
knows its own corner well. NO ONE has yet read the whole archive asking what
these facts mean when held together. That is your job.

Read the dossier holding TWO questions in mind at once:

  1. "What patterns become visible only when I hold two or more verses
     together — patterns a writer composing verse by verse from the front
     will miss?"

  2. "What do facts sitting in DIFFERENT parts of this archive — a
     grammatical oddity here, a liturgical custom eighty pages later, an
     idiom whose biblical usage I know from scholarship — explain about
     EACH OTHER that no single source knows it is saying?"

You will NOT write commentary. You will produce a calibrated list of
OBSERVATIONS that the writer will read as additional input. The writer is
under no obligation to organize its commentary around your observations —
you are surfacing material, not dictating structure.

═══════════════════════════════════════════════════════════════════════════
## INPUT DATA
═══════════════════════════════════════════════════════════════════════════

### PSALM TEXT (Hebrew + English, with phonetic transcriptions where present)
{psalm_text}

### STRUCTURAL OVERVIEW (Macro Analysis)
{macro_analysis}

### VERSE-LEVEL NOTES (Micro Analysis)
{micro_analysis}

### RESEARCH MATERIALS (Lexicons, Concordance, Commentaries, Deep Research, Cross-Cultural Literary Echoes)
{research_bundle}

### PHONETIC TRANSCRIPTIONS
{phonetic_section}

### COMPUTED DISTRIBUTIONAL FACTS (deterministic SQL counts over the full-Tanakh concordance)
{computed_facts}

### ANALYTICAL FRAMEWORK (poetic conventions reference)
{analytical_framework}
"""


# Session 388: the DOSSIER-FIRST layout, which lets the writer read this pass's prompt cache.
# The message opens with the writer's own INPUTS head (built by forest_writer.shared_dossier,
# byte-identical to what the writer sends) under a cache breakpoint; the role statement, the
# two inputs only this pass sees, and the task follow. The role statement is INPUTS_HEADER's
# own text with one word changed ("Below" -> "Above"), so the two layouts cannot drift apart.
_ROLE_END = "═══════════════════════════════════════════════════════════════════════════\n## INPUT DATA"
_BELOW = "Below is the full research dossier the Master Writer will see when it writes\nthe commentary."
_ABOVE = ("Above, under YOUR INPUTS, is the full research dossier the Master Writer will\n"
          "see when it writes the commentary.")
if _ROLE_END not in INPUTS_HEADER or _BELOW not in INPUTS_HEADER:
    raise RuntimeError("synthesis_discovery.INPUTS_HEADER changed; re-point the dossier-first layout")
ROLE_AFTER_DOSSIER = INPUTS_HEADER[:INPUTS_HEADER.index(_ROLE_END)].replace(_BELOW, _ABOVE)

EXTRA_INPUTS = """═══════════════════════════════════════════════════════════════════════════
## ADDITIONAL INPUT DATA (for this pass only; the writer does not see these)
═══════════════════════════════════════════════════════════════════════════

### COMPUTED DISTRIBUTIONAL FACTS (deterministic SQL counts over the full-Tanakh concordance)
{computed_facts}

### ANALYTICAL FRAMEWORK (poetic conventions reference)
{analytical_framework}
"""

# A 5-minute cache entry lives from the START of the request that wrote or last read it, and
# this pass runs ~10 minutes on Opus 5.5 (Ps 77: 637 s). Every this many seconds while it
# streams, a max_tokens=0 request re-reads the dossier head (0.05x input on Opus 5.5, ~$0.05);
# one more follows at the end if the last was long enough ago that the writer might miss it.
KEEPALIVE_EVERY_S = 200
FINAL_KEEPALIVE_IF_OLDER_THAN_S = 120


SYNTHESIS_TASK = """
═══════════════════════════════════════════════════════════════════════════
## YOUR TASK: SYNTHESIS DISCOVERY (NO PROSE — DO NOT WRITE COMMENTARY)
═══════════════════════════════════════════════════════════════════════════

### WHAT YOU ARE HUNTING

The unit of value is the "aha" observation: a reader who already knows the
Psalms well reads it, feels several things click into place at once, and
cannot afterwards un-see it. TWO SPECIES count. Hunt BOTH.

**TYPE P — PATTERN.** A claim that becomes true only when two or more
verses — or a whole-psalm pattern — are read together. It is CONSTRUCTED
by reading across the poem, not extracted from any one place.

Examples of the SHAPE (not content) we want for TYPE P:
  "Every finite verb whose subject is the enemy is in the perfect; God's
   verbs range the whole tense system; the speaker's own verbs migrate from
   imperative to cohortative to perfect — the conjugation is the plot."
  "Two consonantally identical roots do double duty: קֶרֶב 'interior' in v.5
   and קְרָב 'battle' in v.19, set against the speaker's plea for God to
   draw near (קָרוֹב) — the inner storm and the outer combat share the
   poem's signature consonants."
  "The poem twice reaches for a maximal image and twice retracts it; the
   gap between what it demands and what it shows is its moral signature."

**TYPE C — CONNECTION.** A claim that two or more facts which the dossier
(or standard scholarship) holds SEPARATELY in fact explain each other: an
anomaly and its best explanation, or known facts whose LINKAGE is new and
makes something click. The novelty of a TYPE C observation lives in the
connection, NOT in the constituent facts — the constituents may be
individually famous.

Examples of the SHAPE (not content) we want for TYPE C:
  "The superscription ties the psalm to a narrative the body never
   mentions; the one word the body shares with that narrative explains why
   the tradition forged the link — and what the link was for."
  "The micro analysis flags a rare grammatical form; eighty pages later the
   liturgical librarian reports the psalm's role in a rite; held together,
   the form explains why the rite chose THIS psalm. Neither source knows
   it is saying this."
  "An ordinary-looking word choice becomes pointed once you recall what the
   idiom it avoids (or invokes) means elsewhere in the Bible; the avoidance
   aligns exactly with the psalm's program, and is best read as deliberate."
  "A custom's standard explanation is real but half the story: the psalm
   supplies a second, independent support that no one cites — the custom is
   overdetermined, and the second support changes what the custom means."
  "The poet had ordinary synonyms available but chose this word; the
   phonetic transcription shows why — it rhymes (or near-rhymes) with the
   line it answers, alliterates across the colon, or its sound enacts its
   sense — so the lexical choice is driven by sound, not just meaning."

A TYPE C observation is NOT:
  - a fact restated from a single source, however striking (extraction);
  - a free association: both anchors must be real, and the linkage must
    EXPLAIN something — an anomaly resolved, a choice motivated, a custom
    grounded, an omission accounted for;
  - dependent on an invented fact: the CONNECTOR (an idiom's meaning, a
    historical practice, a comparative datum) may come from your scholarly
    general knowledge ONLY if you would stake it in print without hedging;
    the ANCHORS must be quotable from the dossier or from the psalm itself.

Universal exclusions (both types):
  - NOT derivable from a good English translation alone.
  - NOT the dictionary in disguise: a balanced restatement of what a word
    already means is not an insight (the "false profundity" failure).

### PROCEDURE (do ALL of this in your reasoning; output only the final block)

1. SURPRISE INVENTORY. Before anything else, list the 6-12 most genuinely
   UNEXPLAINED things about this psalm — the places a careful reader should
   stop and ask "why is that?" Draw from every altitude: a formula quoted
   with something missing or altered (when the psalm reworks a known source
   text, reconstruct the source IN FULL from your knowledge and diff it:
   list what is altered AND what is entirely ABSENT — an omission is often
   the loudest choice a poet makes); a superscription at odds with the
   body; a genre anomaly; a rare form or hapax in a structurally loaded
   position; a reception fact whose standard explanation feels thin ("why
   is THIS psalm used THERE?"); a translation crux; a structural
   irregularity in an otherwise regular design; a word chosen where an
   ordinary synonym would carry the same sense — ask whether SOUND (rhyme,
   near-rhyme, alliteration, assonance, sound enacting sense) is the hidden
   motive, reading the phonetic transcriptions as evidence. An observation
   that resolves a surprise is worth five that decorate a regularity.

2. SYNTHESIS SUBSTRATE. Distill from EACH section of the dossier (macro,
   micro, lexicon/concordance, commentaries, liturgical/reception, deep
   research, literary echoes, phonetic transcriptions) its 5-15 most
   consequential or pregnant facts — one line each, tagged with the section
   it came from. Mine the WHOLE archive: the strongest connections
   typically join facts that sit far apart, which is precisely why no one
   has made them.

3. COLLISION PASS. Now generate candidates by deliberate pairing, not by
   waiting for inspiration:
   - For each SURPRISE: "What — anywhere in the substrate, or in scholarly
     knowledge I would stake in print — would explain this?"
   - For promising substrate pairs from DIFFERENT sections: "Do these two
     facts explain each other? Does one motivate the other?"
   - SOUND-AS-MOTIVE sweep: for words/phrases in structurally or thematically
     loaded positions, ask whether the poet's lexical choice is driven by
     SOUND — rhyme or near-rhyme with the colon it answers, alliteration or
     assonance across a line, a sound pattern that enacts the sense, or a
     word preferred over an available synonym for euphony. Read the phonetic
     transcriptions as primary evidence and tie the sound to the choice.
   - DISTRIBUTIONAL sweep (one generative move among several — NOT a gate
     on TYPE P): pick a handful of distributional axes that THIS psalm's
     own surface suggests (which axes is your discovery), TABULATE them in
     your reasoning — actual occurrences mapped to actual verses — and
     inspect the tables for lopsidedness: clusters, migrations, and
     CONSPICUOUS ABSENCES (a feature withheld for a stretch of verses, a
     form that never lands on one actor, a name that never appears where
     it is most expected). Distributional patterns are discovered by
     counting, not recalled; a table you never build is a pattern you
     never see. Most tables will be boring — discard them without comment.
     When the COMPUTED DISTRIBUTIONAL FACTS block is present, start there:
     its counts are exact and already built — trust them over your own
     tabulation (and over your memory), and spend your reasoning on which
     rows actually carry weight, not on counting. Mind its stated limitation:
     it counts exact consonantal FORMS, not lemmas.
   - And the qualitative TYPE P sweep across the poem itself: verb system,
     sound architecture, structural hinges, juridical logic,
     superscription-vs-body gap, restraint vs. excess, intertextual
     self-reading, repeated roots and consonantal networks, spatial logic,
     address shifts, image-arcs raised and retracted, etc. These need NO
     tabulation — patterns of this kind are perceived by reading, and they
     are no less valuable; find them as you always have.
   Scale the pool to the psalm: at minimum ~15 candidates for a short
   psalm, 25+ for a 20+ verse psalm, spanning BOTH types. If your pool is
   all one type, you have under-generated the other — go back.

4. NOVELTY-OF-LINKAGE FILTER. For EACH candidate, attack it:
   - "Is the LINKAGE itself already standard fare — stated in the dossier,
     or a connection any learned reader of Psalms has already made?" If
     yes, cut it. (A famous constituent fact does NOT disqualify a novel
     linkage; test the connection, not the ingredients.)
   - "Is this one verse dressed up as a pattern?" If yes, cut it.
   - "Strip the cadence — is there a claim left, or only a definition
     restated?" If only a definition, cut it.
   - "Does this survive being said flatly?" If not, cut it.
   Keep ALL survivors. Do NOT impose a number cap.

5. EVIDENCE-HONESTY AUDIT (HARD — apply to EVERY survivor of step 4). An
   ambitious observation is worthless if its evidence is overstated. Audit
   and DOWN-CALIBRATE each claim until it is exactly as strong as the
   evidence supports — or cut it if calibration leaves nothing. Check each
   failure mode EXPLICITLY:

   **(a) Homophony vs. consonantal overlap.** Two differently-vocalized
   lexemes sharing a root or consonants are NOT "the same word,"
   "homophones," or "phonetically identical." Say "shares the consonants" /
   "consonantal play" / "the root does double duty." Never claim
   sound-identity for forms that are only consonantally related.

   **(b) Echo vs. verbatim.** Do not call a parallel "verbatim," "the exact
   formula," or "a quotation" unless it is a contiguous, word-for-word
   match. Default to "echoes," "clearly alludes to," "resonates with."
   When in doubt, weaker.

   **(c) Primary lexical meaning is what survives.** Do not stretch a
   verb's sense to land a thematic point. Example failure: claiming חלל
   means "stab through" when it means "profane / desecrate" (חָלָל "the
   slain" is a cognate field, not the verb's argument). The verb's primary
   sense is the verb's argument; cognate fields can RESONATE but cannot be
   smuggled in as the meaning.

   **(d) Anchors on the ground; no invented or stretched prooftexts.**
   Every biblical/rabbinic citation must be one you can ground in the
   provided research bundle or state with very high confidence. Quoted
   Hebrew fragments must be CONTIGUOUS substrings of the source — never
   stitch non-adjacent words. If unsure of a chapter/verse or tractate
   number, omit the locator rather than guess. EVERY claimed parallel must
   be a phrase you can quote literally from the cited verse. For TYPE C
   specifically: each ANCHOR must sit in the dossier or the psalm text;
   a CONNECTOR from general scholarship is admissible only at
   stake-it-in-print confidence — if the connector itself is uncertain,
   the observation is CONJECTURE at best, or cut.

   **(e) Uniqueness claims require checking.** "The only place," "the sole
   parallel," "exactly one comparable formula elsewhere" — these are almost
   always wrong. A formula that feels unique usually has 3-5 cousins.
   Default to "most notably," "the closest parallel," "in one striking
   parallel." These carry the same rhetorical force without the false
   claim.

   **(f) Count before you cite a number.** "Eight movements," "ten
   occurrences," "five words in the clause," "the final two words" — if
   you cite a number, literally count first. The reader can count too.

   **(g) Unmarked leap vs. flagged conjecture.** An interpretive leap —
   "perhaps the poet dropped X because of Y" — is PERMITTED, and is often
   where the deepest observations live. But it must (i) be explicitly
   flagged as conjecture, never worded as established fact, and (ii) pay
   rent: it must actually explain something concrete (an omission, an
   anomaly, a choice) better than the null hypothesis of coincidence. What
   remains FORBIDDEN is the unmarked non-sequitur — a leap the reader must
   swallow unannounced for the claim to feel forceful ("prayer begins
   where evil cannot follow"). Flag it honestly or cut it.

   **(h) No "signature root" / etymology claims unless certain.** Babel's
   signature verb is בלל, not פלג; a thematic evocation is fine, a root
   identification is not. Same for any other origin / etymology claim.

   **(i) Match assertion strength to evidence.** "the fit is exact,"
   "always," "the most consequential," "verbatim" — replace with calibrated
   wording unless literally true. An observation that needs an
   overstatement to land is a false-profundity failure; keep the calibrated
   version or cut.

   **(j) FINAL CHECK — META-RULE.** Re-read your survivors with this
   question: "Can I name two failure modes from (a)-(i) that I did NOT
   already check on this particular observation?" If yes, check them. If
   you can't generate two more failure modes you haven't already audited,
   you haven't checked enough. Repeat until the audit is exhausted.

   The point of all this: your observations will be read by the Master
   Writer as input it can use. Any overclaim you ship here propagates
   straight into the prose, where the copy editor will catch it — but the
   writer will have already wasted craft on a structurally central claim
   that gets cut. Honest calibration is what makes ambition affordable: a bold
   conjecture honestly flagged is welcome; a medium claim dressed as a
   certainty is not.

6. AHA AUDIT (the boredom cut — apply to every survivor of step 5). True,
   calibrated, novel — and dull — is still a failure. Test each survivor:
   - SURPRISE: did holding this observation change how you yourself read
     at least one verse, or the whole poem? If nothing shifted, demote.
   - ECONOMY: does ONE connection make SEVERAL facts click (the omission
     AND the theme AND the custom), or does it explain only itself?
     Explanatory economy is the signature of a real insight.
   - HINDSIGHT-INEVITABILITY: once seen, does it feel like it was always
     there? (The best observations feel found, not manufactured.)
   An observation can survive step 5 with perfect honesty and still fail
   here. Cut such items — or keep them only if they are real but minor
   texture, and say so plainly in the Payoff rather than dressing them up.

7. SELECT (quality-gated, NOT quota-gated — never discard a survivor
   merely to hit a count, and never pad to reach one):
   - Output EVERY survivor of steps 4-6 as a flat, UNRANKED list, ordered
     by the primary verse each observation is anchored to (whole-psalm
     observations first, in any order). Do NOT rank them, do NOT name a
     "governing" or "central" observation, and do NOT signal which one you
     consider strongest — selecting and weighting observations is the
     Master Writer's job, and any salience signal you attach distorts its
     judgment. Your job ends at: real, calibrated, novel, alive.
   - A healthy list usually mixes TYPE P and TYPE C; if yours is all one
     type, revisit step 3 once before finalizing.
   - If the filters leave only 3 total, output 3; if they leave 14, output
     14. Honesty about quantity is the point.

═══════════════════════════════════════════════════════════════════════════
## OUTPUT FORMAT (output ONLY this — no preamble, no brainstorm dump)
═══════════════════════════════════════════════════════════════════════════

---CROSS-VERSE-OBSERVATIONS-START---

## OBSERVATION 1

**Type:** <PATTERN | CONNECTION>

**Primary verse(s):** <e.g., "vv. 3-5" or "whole psalm">

**Claim:** <2-3 sentences.>

**Confidence:** <ESTABLISHED | PROBABLE | CONJECTURE> — <1 short clause of
justification. CONJECTURE items must be worded as conjecture in the Claim
itself ("perhaps," "is best explained as," "suggests").>

**Anchors (every fact this rests on, each with its footing):**
- <anchor: specific Hebrew / dossier fact + WHERE it sits (verse n / which
  dossier section / "general scholarship: ..." for a connector)>
- <anchor: ...>

**Payoff (what clicks):** <1-2 sentences: which facts or anomalies this
observation explains or newly illuminates.>

**Novelty of the linkage (why a learned reader of Psalms has not already
made this connection):** <1 sentence>

## OBSERVATION 2

<same fields>

(...continue OBSERVATION 3, 4, ... for EVERY survivor, ordered by primary
verse — whole-psalm observations first. Do NOT stop at an arbitrary number
and do NOT rank.)

---CROSS-VERSE-OBSERVATIONS-END---
"""


TRANSIENT_ERRORS = (
    anthropic.APIConnectionError,
    anthropic.InternalServerError,
    anthropic.RateLimitError,
)


class SynthesisDiscoveryAgent:
    """Cross-verse synthesis discovery — sidecar to the Master Writer."""

    def __init__(
        self,
        cost_tracker: Optional[CostTracker] = None,
        model: str = DEFAULT_MODEL,
        logger=None,
    ):
        self.model = model
        self.cost_tracker = cost_tracker or CostTracker()
        self.logger = logger or get_logger("synthesis_discovery")
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self.client = anthropic.Anthropic(api_key=api_key)

    def discover(
        self,
        psalm_number: int,
        psalm_text: str,
        macro_analysis_text: str,
        micro_analysis_text: str,
        research_bundle: str,
        phonetic_section: str,
        analytical_framework: str,
        computed_facts: str = "",
        debug_dir: Optional[Path] = None,
        retries: int = 4,
        shared_dossier: Optional[str] = None,
        cache_shared: bool = False,
        thinking: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run the synthesis-discovery pass and return the observations block.

        Session 388: with `shared_dossier` (forest_writer.shared_dossier -- the writer's own
        INPUTS head) the message opens with that text, and `cache_shared` puts a cache
        breakpoint on it and keeps the entry warm while this pass runs, so the writer reads
        it. `thinking` must be the dict the writer sends (model_effort.adaptive_thinking):
        thinking settings are part of the cache key. Without `shared_dossier`, the original
        single-block layout (INPUTS_HEADER + SYNTHESIS_TASK) is sent.

        Returns a dict with keys:
          - observations_markdown: the contents between the START/END markers
            (or the full response if the markers were not emitted)
          - full_response: the raw Claude response text
          - input_tokens, output_tokens, thinking_chars, usage (with cache fields)
        """
        facts = computed_facts or "[not available for this run]"
        if shared_dossier:
            # the head ends without whitespace (forest_writer.split_inputs); the break opens the tail
            tail = ("\n\n" + ROLE_AFTER_DOSSIER.format(psalm_number=psalm_number)
                    + EXTRA_INPUTS.format(computed_facts=facts, analytical_framework=analytical_framework)
                    + SYNTHESIS_TASK)
            head = {"type": "text", "text": shared_dossier}
            if cache_shared:
                head["cache_control"] = {"type": "ephemeral"}
            content = [head, {"type": "text", "text": tail}]
            prompt = shared_dossier + tail
        else:
            prompt = INPUTS_HEADER.format(
                psalm_number=psalm_number,
                psalm_text=psalm_text,
                macro_analysis=macro_analysis_text,
                micro_analysis=micro_analysis_text,
                research_bundle=research_bundle,
                phonetic_section=phonetic_section,
                computed_facts=facts,
                analytical_framework=analytical_framework,
            ) + SYNTHESIS_TASK
            content = prompt

        if debug_dir is not None:
            debug_dir = Path(debug_dir)
            debug_dir.mkdir(parents=True, exist_ok=True)
            (debug_dir / f"synthesis_discovery_prompt_psalm_{psalm_number}.txt").write_text(
                prompt, encoding="utf-8"
            )

        keepalive_head = content[0] if (shared_dossier and cache_shared) else None
        response_text, usage, thinking_chars = self._stream_call(
            content, tag=f"SYNTHESIS-DISCOVERY psalm {psalm_number}", retries=retries,
            thinking=thinking, keepalive_head=keepalive_head,
        )

        if debug_dir is not None:
            (debug_dir / f"synthesis_discovery_response_psalm_{psalm_number}.txt").write_text(
                response_text, encoding="utf-8"
            )

        observations_markdown = self._extract_observations_block(response_text)

        return {
            "observations_markdown": observations_markdown,
            "full_response": response_text,
            "input_tokens": usage["input"] + usage["cache_read"] + usage["cache_write"],
            "output_tokens": usage["output"],
            "thinking_chars": thinking_chars,
            "usage": usage,
        }

    def _bill(self, u) -> Dict[str, int]:
        """Bill one response's usage, cache fields included (they are disjoint from
        input_tokens on the Anthropic API). Before Session 388 only input and output were
        billed, which was right only while this pass never cached anything."""
        row = {"input": getattr(u, "input_tokens", 0) or 0,
               "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0,
               "cache_write": getattr(u, "cache_creation_input_tokens", 0) or 0,
               "output": getattr(u, "output_tokens", 0) or 0}
        self.cost_tracker.add_usage(model=self.model, input_tokens=row["input"],
                                    output_tokens=row["output"], thinking_tokens=0,
                                    cache_read_tokens=row["cache_read"],
                                    cache_write_tokens=row["cache_write"])
        return row

    def _keepalive(self, kwargs: Dict[str, Any], head: Dict[str, Any], tag: str) -> Optional[Dict[str, int]]:
        """Re-read the cached dossier head: max_tokens=0 (nothing generated), the same
        model, thinking and effort as the pass itself, which are part of the cache key."""
        try:
            kw = {k: v for k, v in kwargs.items() if k != "messages"}
            kw.update(max_tokens=0, messages=[{"role": "user", "content": [head]}])
            row = self._bill(self.client.messages.create(**kw).usage)
            self.logger.info(f"[{tag}] dossier cache keep-alive: read {row['cache_read']:,}, "
                             f"wrote {row['cache_write']:,}")
            return row
        except Exception as e:  # a failed keep-alive costs at most the writer's cache write
            self.logger.warning(f"[{tag}] dossier cache keep-alive failed: {str(e)[:160]}")
            return None

    @staticmethod
    def _extract_observations_block(response_text: str) -> str:
        start_marker = "---CROSS-VERSE-OBSERVATIONS-START---"
        end_marker = "---CROSS-VERSE-OBSERVATIONS-END---"
        i = response_text.find(start_marker)
        j = response_text.find(end_marker, i + len(start_marker)) if i != -1 else -1
        if i == -1 or j == -1:
            return response_text.strip()
        return response_text[i + len(start_marker):j].strip()

    def _stream_call(self, content, tag: str, retries: int = 4,
                     thinking: Optional[Dict[str, Any]] = None,
                     keepalive_head: Optional[Dict[str, Any]] = None):
        """One Opus streaming call, mirroring the Master Writer config.

        Retries on transient stream drops (the 'incomplete chunked read'
        family) and on anthropic.* transient errors. Session 388: with
        `keepalive_head`, a thread re-reads the cached dossier head every
        KEEPALIVE_EVERY_S seconds once the stream has begun (an entry is
        readable only then), and once more at the end if the last read is
        older than FINAL_KEEPALIVE_IF_OLDER_THAN_S. Returns (text, usage, thinking_chars).
        """
        import threading

        for attempt in range(1, retries + 1):
            self.logger.info(
                f"[{tag}] calling {self.model} (effort={effort_for(self.model) or 'API default'}, adaptive thinking) "
                f"- attempt {attempt}/{retries}"
            )
            t0 = time.time()
            text, think_chars = "", 0

            stream_kwargs = {
                "model": self.model,
                # Session 387: 64000 cut Ps 77 off mid-observation on Opus 5.5, which writes
                # ~75% more than Opus 4.8 did (S383). 128K is Opus 5.5's output ceiling.
                "max_tokens": 128000,
                "thinking": dict(thinking) if thinking else {"type": "adaptive"},
                "messages": [{"role": "user", "content": content}],
            }
            apply_effort(stream_kwargs, self.model, self.logger)

            stop = threading.Event()
            last_read = [t0]
            missed = [False]

            def keep_warm():
                while not stop.wait(KEEPALIVE_EVERY_S):
                    row = self._keepalive(stream_kwargs, keepalive_head, tag)
                    if row is None or row["cache_write"]:
                        # a WRITE means the prefix did not match: pinging again would pay again
                        missed[0] = True
                        self.logger.warning(f"[{tag}] keep-alive stopped (no cache hit)")
                        return
                    last_read[0] = time.time()

            warm = None
            try:
                with self.client.messages.stream(**stream_kwargs) as stream:
                    for event in stream:
                        if keepalive_head is not None and warm is None:
                            warm = threading.Thread(target=keep_warm, daemon=True)
                            warm.start()
                        if getattr(event, "type", None) == "content_block_delta":
                            if hasattr(event.delta, "text"):
                                text += event.delta.text
                            elif hasattr(event.delta, "thinking"):
                                think_chars += len(event.delta.thinking)
                    final = stream.get_final_message()
                stop.set()
                usage = self._bill(final.usage)
                if final.stop_reason == "max_tokens":
                    self.logger.error(
                        f"[{tag}] OUTPUT CUT OFF at max_tokens={stream_kwargs['max_tokens']:,}: "
                        "the last observation is incomplete and any after it are missing")
                if keepalive_head is not None:
                    if warm is not None:
                        warm.join(timeout=60)
                    if not missed[0] and time.time() - last_read[0] > FINAL_KEEPALIVE_IF_OLDER_THAN_S:
                        self._keepalive(stream_kwargs, keepalive_head, tag)

                dt = time.time() - t0
                self.logger.info(
                    f"[{tag}] done in {dt:.0f}s - in={usage['input']:,} cache read={usage['cache_read']:,} "
                    f"cache write={usage['cache_write']:,} out={usage['output']:,} "
                    f"(~{think_chars // 4:,} thinking) | response {len(text):,} chars"
                )
                return text, usage, think_chars

            except TRANSIENT_ERRORS as e:
                stop.set()
                wait = 10 * attempt
                self.logger.warning(
                    f"[{tag}] transient API error after {time.time()-t0:.0f}s: "
                    f"{type(e).__name__}: {e}"
                )
                if attempt == retries:
                    raise
                self.logger.info(f"[{tag}] retrying in {wait}s")
                time.sleep(wait)
            except Exception as e:
                stop.set()
                msg = str(e)
                if "incomplete chunked read" in msg or "peer closed connection" in msg:
                    wait = 10 * attempt
                    self.logger.warning(
                        f"[{tag}] transient stream drop after {time.time()-t0:.0f}s: {e}"
                    )
                    if attempt == retries:
                        raise
                    self.logger.info(f"[{tag}] retrying in {wait}s")
                    time.sleep(wait)
                    continue
                raise

        raise RuntimeError(f"[{tag}] exhausted {retries} attempts")
