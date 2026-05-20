"""
Synthesis Discovery Agent (Session 347)

Cross-verse synthesis DISCOVERY pass — a sidecar that produces calibrated
cross-verse observations the production one-call Master Writer can weave into
its commentary at its own discretion. NOT a structural spine: the writer keeps
full authorial control. See docs/session_tracking/NEXT_SESSION_BRIEF.md
(Session 347 brief) for the design rationale and what failed in earlier
attempts (`InsightExtractor` was too extractive; the two-call spine
architecture over-engineered the prose by forcing anchored arcs).

What this agent is FOR
----------------------
Generative discovery of patterns that become visible only when reading two or
more verses together — like a root that does double duty across the psalm, a
recurring formula that inverts a known biblical phrase, a tense/aspect arc
that is the plot in disguise. These are the things the one-call writer keeps
missing because the writing task crowds out the discovery task.

What this agent is NOT
----------------------
- Not an extractor of items already in the research bundle.
- Not a spine: it does not assign anchor verses or mandate where claims land.
- Not quota-driven: it outputs only what survives an adversarial novelty filter
  and a hardened evidence-honesty filter.

Output
------
A markdown block (one governing observation + tiered survivors, with per-verse
Hebrew evidence) saved to:
    output/psalm_NNN/psalm_NNN_synthesis_discovery.md

The Master Writer prompt assembly splices this in as a new INPUT block labelled
"CROSS-VERSE OBSERVATIONS (use where they fit; do NOT structure your commentary
around them)".
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


load_dotenv()


DEFAULT_MODEL = "claude-opus-4-7"


# =============================================================================
# Prompt — built to match the same INPUT BLOCKS the Master Writer sees, so the
# discovery pass reasons over identical evidence. Adapted from the Session-346
# experiment's SYNTHESIS_TASK with these deliberate changes per the brief:
#   - DROPPED: anchor-verse assignments and "how to signal at other verses"
#     fields. Those existed because the two-call architecture needed a spine;
#     here, the writer decides where things land.
#   - KEPT: tiered survivors, per-verse Hebrew evidence, novelty check.
#   - HARDENED: the evidence-honesty filter now names the exact failure modes
#     the Session-346 copy editor caught on the Ps 55 two-call run (counting
#     errors, strained etymology, non-sequitur synthesis, fabricated parallels,
#     non-uniqueness overclaims), and adds the meta-rule that calibration is
#     enumerable failure modes plus "if you can't think of two failure modes
#     you didn't already check, you haven't checked enough."
# =============================================================================

INPUTS_HEADER = """You are a CROSS-VERSE SYNTHESIS DISCOVERER for Psalm {psalm_number}.

Below is the full research dossier the Master Writer will see when it writes
the commentary. Your job is to read it ONCE WITH A SINGLE QUESTION in mind:

    "What patterns in this psalm become visible only when I hold two or more
    verses together — patterns the writer will miss if it composes verse by
    verse from the front?"

You will NOT write commentary. You will produce a calibrated list of
cross-verse OBSERVATIONS that the writer will read as additional input. The
writer is under no obligation to organize its commentary around your
observations — you are surfacing material, not dictating structure.

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

### ANALYTICAL FRAMEWORK (poetic conventions reference)
{analytical_framework}
"""


SYNTHESIS_TASK = """
═══════════════════════════════════════════════════════════════════════════
## YOUR TASK: CROSS-VERSE SYNTHESIS DISCOVERY (NO PROSE — DO NOT WRITE COMMENTARY)
═══════════════════════════════════════════════════════════════════════════

### WHAT A CROSS-VERSE OBSERVATION IS (AND IS NOT)

A cross-verse observation is a single claim that becomes true only when you
read TWO OR MORE verses — or a whole-psalm pattern — TOGETHER. It is
CONSTRUCTED by reading across the poem, not extracted from any one place.

- It is NOT a per-verse observation, however sharp.
- It is NOT a fact already sitting in the research bundle waiting to be quoted.
  You must BUILD it by reading across the psalm.
- It is NOT derivable from a good English translation.
- It is NOT something a learned reader of Psalms would already know.
- It is NOT the dictionary in disguise: a balanced restatement of what a word
  already means is not an insight (this is the "false profundity" failure the
  Master Writer's RULE 7b forbids).

Examples of the SHAPE (not content) we want:
  "Every finite verb whose subject is the enemy is in the perfect; God's verbs
   range the whole tense system; the speaker's own verbs migrate from
   imperative to cohortative to perfect — the conjugation is the plot."
  "Two consonantally identical roots do double duty: קֶרֶב 'interior' in v.5
   and קְרָב 'battle' in v.19, set against the speaker's plea for God to
   draw near (קָרוֹב) — the inner storm and the outer combat share the
   poem's signature consonants."
  "The poem twice reaches for a maximal image and twice retracts it; the gap
   between what it demands and what it shows is its moral signature."

That shape — multi-verse, constructed, transforms the reading — is the target.

### PROCEDURE (do all of this in your reasoning; output only the final block)

1. BRAINSTORM WIDELY — scale effort to the psalm. Generate a large candidate
   pool: at minimum ~10 candidates for a short psalm, more for a long one
   (a 20+ verse psalm has more cross-verse architecture — aim for 18-25
   candidates before filtering). Range across: verb system, divine-name
   distribution, sound architecture, structural hinges, juridical/forensic
   logic, the superscription-vs-body gap, restraint vs. excess, intertextual
   self-reading, the placement of selah, repeated roots and consonantal
   networks, spatial logic, address shifts, etc.

2. ADVERSARIAL NOVELTY FILTER. For EACH candidate, attack it:
   - "Would a scholar who knows Psalms already know this?" If yes, cut it.
   - "Is this actually just one verse dressed up as a pattern?" If yes, cut it.
   - "Strip the cadence — is there a claim left, or only a definition restated?"
     If only a definition, cut it (the false-profundity failure).
   - "Does this survive being said flatly?" If not, cut it.
   Keep ALL survivors. The filter is the only gate. Do NOT impose a number cap.

3. EVIDENCE-HONESTY FILTER (HARD — apply to EVERY survivor of step 2). An
   ambitious observation is worthless if its evidence is overstated. For each
   survivor, audit and DOWN-CALIBRATE its claim until it is exactly as strong
   as the text supports — or cut it if calibration leaves nothing. Check each
   of these failure modes EXPLICITLY:

   **(a) Homophony vs. consonantal overlap.** Two differently-vocalized lexemes
   sharing a root or consonants are NOT "the same word," "homophones," or
   "phonetically identical." Say "shares the consonants" / "consonantal play"
   / "the root does double duty." Never claim sound-identity for forms that
   are only consonantally related.

   **(b) Echo vs. verbatim.** Do not call a parallel "verbatim," "the exact
   formula," or "a quotation" unless it is a contiguous, word-for-word match.
   Default to "echoes," "clearly alludes to," "resonates with." When in
   doubt, weaker.

   **(c) Primary lexical meaning is what survives.** Do not stretch a verb's
   sense to land a thematic point. Example failure: claiming חלל means
   "stab through" when it means "profane / desecrate" (חָלָל "the slain"
   is a cognate field, not the verb's argument). The verb's primary sense
   is the verb's argument; cognate fields can RESONATE but cannot be smuggled
   in as the meaning.

   **(d) No invented or stretched prooftexts.** Every biblical/rabbinic
   citation in an observation must be one you can ground in the provided
   research bundle or state with very high confidence. Quoted Hebrew
   fragments must be CONTIGUOUS substrings of the source — never stitch
   non-adjacent words. If unsure of a chapter/verse or tractate number, omit
   the locator rather than guess. EVERY claimed parallel must be a phrase you
   can quote literally from the cited verse; if the phrase isn't there, the
   claim isn't there.

   **(e) Uniqueness claims require checking.** "The only place," "the sole
   parallel," "exactly one comparable formula elsewhere" — these are almost
   always wrong. A formula that feels unique usually has 3-5 cousins. Default
   to "most notably," "the closest parallel," "in one striking parallel."
   These carry the same rhetorical force without the false claim.

   **(f) Count before you cite a number.** "Eight movements," "ten
   occurrences," "five words in the clause," "the final two words" — if you
   cite a number, literally count first. The reader can count too.

   **(g) Non-sequitur synthesis.** If your observation requires the reader to
   accept an unstated leap to feel its force ("prayer begins where evil
   cannot follow"; "three-over-two outcovers evil"), it is overreach. State
   the more modest claim that survives strict reading, or cut it.

   **(h) No "signature root" / etymology claims unless certain.** Babel's
   signature verb is בלל, not פלג; a thematic evocation is fine, a root
   identification is not. Same for any other origin / etymology claim.

   **(i) Match assertion strength to evidence.** "the fit is exact,"
   "always," "the most consequential," "verbatim" — replace with calibrated
   wording unless literally true. An observation that needs an overstatement
   to land is a false-profundity failure; keep the calibrated version or cut.

   **(j) FINAL CHECK — META-RULE.** Re-read your survivors with this
   question: "Can I name two failure modes from (a)-(i) that I did NOT
   already check on this particular observation?" If yes, check them. If you
   can't generate two more failure modes you haven't already audited, you
   haven't checked enough. Repeat until the audit is exhausted.

   The point of all this: your observations will be read by the Master Writer
   as input it can use. Any overclaim you ship here propagates straight into
   the prose, where the copy editor will catch it — but the writer will have
   already wasted craft on a load-bearing claim that gets cut. A
   precisely-calibrated medium claim beats a thrilling false one every time.

4. SELECT AND TIER (quality-gated, NOT quota-gated — never discard an
   observation that survived steps 2 and 3 merely to hit a count):
   - ONE GOVERNING OBSERVATION: the single richest cross-verse pattern,
     strong enough to organize a reader's whole sense of the psalm.
   - CORE OBSERVATIONS: the strongest survivors, each independently
     transformative, each spanning >=2 verses or a whole-psalm pattern, each
     distinct from the governing one and from each other. Scale to the
     psalm's length: roughly one core observation per 3-4 verses, floor of 2,
     NO ceiling.
   - ADDITIONAL OBSERVATIONS: every other survivor that is real and
     cross-verse but a notch below the core ones. Long psalms in particular
     will have several — do not throw them away.
   Output every survivor. If the filter leaves only 3 total, output 3; if
   it leaves 11, output 11. Honesty about quantity is the point.

═══════════════════════════════════════════════════════════════════════════
## OUTPUT FORMAT (output ONLY this — no preamble, no brainstorm dump)
═══════════════════════════════════════════════════════════════════════════

---CROSS-VERSE-OBSERVATIONS-START---

## GOVERNING OBSERVATION

**Claim:** <2-3 sentences. The single richest cross-verse pattern in the psalm.>

**Verses it spans:** <list>

**Evidence (per verse, name the actual Hebrew):**
- v.<n>: <specific Hebrew + what it contributes to the pattern>
- v.<n>: <...>

**Novelty check (why a learned reader of Psalms would not already know this):** <1 sentence>

## CORE OBSERVATION 1

**Claim:** <2-3 sentences.>

**Verses it spans:** <list>

**Evidence (per verse, name the actual Hebrew):**
- v.<n>: <...>

**Novelty check:** <1 sentence>

## CORE OBSERVATION 2

<same fields>

(...continue CORE OBSERVATION 3, 4, ... — as many as survive the filter and
the ~1-per-3-4-verses scaling. Do NOT stop at an arbitrary number.)

## ADDITIONAL OBSERVATION 1

**Claim:** <1-2 sentences.>

**Verses it spans:** <list>

**Evidence (per verse, name the actual Hebrew):**
- v.<n>: <...>

**Novelty check:** <1 sentence>

(...continue ADDITIONAL OBSERVATION 2, 3, ... for every remaining survivor.
Omit this whole section only if there are genuinely no additional survivors.)

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
        debug_dir: Optional[Path] = None,
        retries: int = 4,
    ) -> Dict[str, Any]:
        """Run the synthesis-discovery pass and return the observations block.

        Returns a dict with keys:
          - observations_markdown: the contents between the START/END markers
            (or the full response if the markers were not emitted)
          - full_response: the raw Claude response text
          - input_tokens, output_tokens, thinking_chars
        """
        prompt = INPUTS_HEADER.format(
            psalm_number=psalm_number,
            psalm_text=psalm_text,
            macro_analysis=macro_analysis_text,
            micro_analysis=micro_analysis_text,
            research_bundle=research_bundle,
            phonetic_section=phonetic_section,
            analytical_framework=analytical_framework,
        ) + SYNTHESIS_TASK

        if debug_dir is not None:
            debug_dir = Path(debug_dir)
            debug_dir.mkdir(parents=True, exist_ok=True)
            (debug_dir / f"synthesis_discovery_prompt_psalm_{psalm_number}.txt").write_text(
                prompt, encoding="utf-8"
            )

        response_text, input_tokens, output_tokens, thinking_chars = self._stream_call(
            prompt, tag=f"SYNTHESIS-DISCOVERY psalm {psalm_number}", retries=retries
        )

        if debug_dir is not None:
            (debug_dir / f"synthesis_discovery_response_psalm_{psalm_number}.txt").write_text(
                response_text, encoding="utf-8"
            )

        self.cost_tracker.add_usage(
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thinking_tokens=0,
        )

        observations_markdown = self._extract_observations_block(response_text)

        return {
            "observations_markdown": observations_markdown,
            "full_response": response_text,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "thinking_chars": thinking_chars,
        }

    @staticmethod
    def _extract_observations_block(response_text: str) -> str:
        start_marker = "---CROSS-VERSE-OBSERVATIONS-START---"
        end_marker = "---CROSS-VERSE-OBSERVATIONS-END---"
        i = response_text.find(start_marker)
        j = response_text.find(end_marker, i + len(start_marker)) if i != -1 else -1
        if i == -1 or j == -1:
            return response_text.strip()
        return response_text[i + len(start_marker):j].strip()

    def _stream_call(self, prompt: str, tag: str, retries: int = 4):
        """One Opus 4.7 streaming call, mirroring the Master Writer config.

        Retries on transient stream drops (the 'incomplete chunked read'
        family) and on anthropic.* transient errors.
        """
        for attempt in range(1, retries + 1):
            self.logger.info(
                f"[{tag}] calling {self.model} (effort=max, adaptive thinking) "
                f"- attempt {attempt}/{retries}"
            )
            t0 = time.time()
            text, think_chars = "", 0
            input_tokens, output_tokens = 0, 0

            stream_kwargs = {
                "model": self.model,
                "max_tokens": 64000,
                "thinking": {"type": "adaptive"},
                "messages": [{"role": "user", "content": prompt}],
            }
            if "opus-4-7" in self.model:
                stream_kwargs["output_config"] = {"effort": "max"}

            try:
                with self.client.messages.stream(**stream_kwargs) as stream:
                    for event in stream:
                        if getattr(event, "type", None) == "content_block_delta":
                            if hasattr(event.delta, "text"):
                                text += event.delta.text
                            elif hasattr(event.delta, "thinking"):
                                think_chars += len(event.delta.thinking)
                    final = stream.get_final_message()
                    input_tokens = final.usage.input_tokens
                    output_tokens = final.usage.output_tokens

                dt = time.time() - t0
                self.logger.info(
                    f"[{tag}] done in {dt:.0f}s - in={input_tokens:,} out={output_tokens:,} "
                    f"(~{think_chars // 4:,} thinking) | response {len(text):,} chars"
                )
                return text, input_tokens, output_tokens, think_chars

            except TRANSIENT_ERRORS as e:
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
