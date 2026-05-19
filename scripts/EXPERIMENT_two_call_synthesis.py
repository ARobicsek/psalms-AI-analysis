"""
EXPERIMENT — Two-Call Synthesis Split  (DISCARDABLE)
====================================================

Purpose
-------
Test whether splitting the Master Writer into two sequential calls —
(1) cross-verse SYNTHESIS DISCOVERY with an adversarial novelty filter, then
(2) WRITE using the approved synthesis as a structural spine — produces the
kind of whole-psalm syntheses a one-call writer keeps missing.

Design (clean A/B: only the call structure varies)
--------------------------------------------------
* Context is the EXACT prompt the production pipeline already built and sent
  to the Master Writer for this psalm:
      output/debug/master_writer_v4_prompt_psalm_<N>.txt
  We reuse it verbatim so inputs (psalm text, macro, micro, research bundle,
  phonetics, framework) are byte-identical to the shipped run.
* Call 1: the context's INPUT DATA + ground rules, with the WRITING task
  replaced by a synthesis-discovery task (no prose).
* Call 2: the full original writer prompt, PLUS (a) the new RULE 7b /
  phrase-coverage rule updates pulled live from src/agents/master_editor.py
  so the write call benefits from our recent fixes, and (b) the approved
  synthesis spine from Call 1, with anchor-verse instructions + veto license.
* Same model as production (claude-opus-4-7, effort=max, adaptive thinking).

Discard instructions
--------------------
Delete this file and output/psalm_<N>/EXPERIMENT_two_call/ .
Touches NO production code path. Nothing imports this.

Usage
-----
    python scripts/EXPERIMENT_two_call_synthesis.py 54
"""

import os
import re
import sys
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

MODEL = "claude-opus-4-7"
TASK_MARKER = "## YOUR TASK: WRITE THE COMMENTARY"


# ---------------------------------------------------------------------------
# Pull our newest rule text live from the production prompt so the WRITE call
# benefits from RULE 7b + the phrase-coverage proportionality fix even though
# the saved prompt predates them.
# ---------------------------------------------------------------------------
def extract_rule_updates() -> str:
    from src.agents.master_editor import MASTER_WRITER_PROMPT_V4 as P

    def between(start: str, end: str) -> str:
        i = P.index(start)
        j = P.index(end, i)
        return P[i:j].strip()

    rule_7b = between("### RULE 7b: NO FALSE PROFUNDITY", "### RULE 8: NO ORPHANED FACTS")
    rule_8 = between("### RULE 8: NO ORPHANED FACTS", "### RULE 9: COMMIT TO AMBIGUITY")
    phrase_cov = between(
        "**Phrase coverage (CRITICAL — read this twice):**",
        "**ITEMS OF INTEREST TO ILLUMINATE**",
    )
    return (
        "## ═══════════════════════════════════════════════════════════════════════════\n"
        "## PROMPT RULE UPDATES — THESE SUPERSEDE ANYTHING EARLIER THAT CONFLICTS\n"
        "## ═══════════════════════════════════════════════════════════════════════════\n\n"
        "The following rules were added after the body of this prompt was written. "
        "They take precedence over any earlier instruction they conflict with.\n\n"
        f"{rule_7b}\n\n{rule_8}\n\n"
        "### STAGE 3 — PHRASE COVERAGE (REPLACES the older phrase-coverage bullet):\n\n"
        f"{phrase_cov}\n"
    )


# ---------------------------------------------------------------------------
# Call 1 — SYNTHESIS DISCOVERY
# ---------------------------------------------------------------------------
SYNTHESIS_TASK = """
## ═══════════════════════════════════════════════════════════════════════════
## YOUR TASK: SYNTHESIS DISCOVERY (NO PROSE — DO NOT WRITE COMMENTARY)
## ═══════════════════════════════════════════════════════════════════════════

You have just been given the full research dossier for Psalm {psalm_number}
(text, structure, verse notes, lexicon, concordance, commentaries, literary
echoes). Your ONLY job right now is to DISCOVER the psalm's strongest
cross-verse syntheses. You will NOT write any commentary or essay in this
step. Another pass will do the writing, using what you produce here as its
skeleton.

### WHAT A SYNTHESIS IS (AND IS NOT)

A synthesis is a single claim that becomes true only when you read TWO OR MORE
verses — or a whole-psalm pattern — TOGETHER. It is constructed, not extracted.

- It is NOT a per-verse observation, however sharp.
- It is NOT a fact already sitting in the research bundle waiting to be quoted.
  You must BUILD it by reading across the psalm.
- It is NOT derivable from a good English translation.
- It is NOT something a learned reader of Psalms would already know.
- It is NOT the dictionary in disguise: a balanced restatement of what a word
  already means is not an insight (see RULE 7b in the rules above).

A real synthesis names a pattern the poet built across the poem and says what
that pattern DOES. Examples of the SHAPE (not content) we want:
  "Every finite verb whose subject is the enemy is in the perfect; God's verbs
   range the whole tense system; the speaker's own verbs migrate from
   imperative to cohortative to perfect — the conjugation is the plot."
  "The poem twice reaches for a maximal image and twice retracts it; the gap
   between what it demands and what it shows is its moral signature."
That shape — multi-verse, constructed, transforms the reading — is the target.

### PROCEDURE (do all of this in your reasoning; output only the final block)

1. BRAINSTORM WIDELY — scale effort to the psalm. Generate a large candidate
   pool: at minimum ~10 for a short psalm, and MORE for a long one (a 20+
   verse psalm has more cross-verse architecture — aim for 18–25 candidates
   before filtering). Range across: verb system, divine-name distribution,
   sound architecture, structural hinges, juridical/forensic logic, the
   superscription-vs-body gap, restraint vs. excess, intertextual self-reading,
   the placement of selah, repeated roots, spatial logic, address shifts, etc.

2. ADVERSARIAL NOVELTY FILTER. For EACH candidate, attack it:
   - "Would a scholar who knows Psalms already know this?" If yes, cut it.
   - "Is this actually just one verse dressed up as a pattern?" If yes, cut it.
   - "Strip the cadence — is there a claim left, or only a definition restated?"
     If only a definition, cut it (RULE 7b).
   - "Does this survive being said flatly?" If not, cut it.
   Keep ALL survivors. The filter is the only gate. Do NOT impose a number cap.

2b. EVIDENCE-HONESTY FILTER (HARD — apply to EVERY survivor of step 2). An
   ambitious synthesis is worthless if its evidence is overstated. For each
   survivor, audit and DOWN-CALIBRATE its claim until it is exactly as strong
   as the text supports — or cut it if calibration leaves nothing:
   - **Homophony vs. consonantal overlap.** Two differently-vocalized lexemes
     sharing a root are NOT "the same word," "homophones," or "phonetically
     identical." Say "shares the consonants" / "consonantal play." Never claim
     sound-identity for forms that are only consonantally related.
   - **Echo vs. verbatim.** Do not call a parallel "verbatim," "the exact
     formula," or "a quotation" unless it is a contiguous, word-for-word
     match. Default to "echoes" / "clearly alludes to." When in doubt, weaker.
   - **No invented or stretched prooftexts.** Every biblical/rabbinic citation
     in the spine must be one you can ground in the provided research bundle or
     state with high confidence. Quoted Hebrew fragments must be CONTIGUOUS
     substrings of the source — never stitch non-adjacent words. If unsure of
     a chapter/verse or tractate number, omit the locator rather than guess.
   - **No "signature root" / etymology claims** unless certain (e.g. Babel's
     signature verb is בלל, not פלג — a thematic evocation is fine; a root
     identification is not).
   - **Match assertion strength to evidence.** "the fit is exact," "always,"
     "the most consequential," "verbatim" — replace with calibrated wording
     unless literally true. A synthesis that needs an overstatement to land is
     a RULE 7b failure; keep the calibrated version or cut it.
   The point: the spine must not seed overclaims that propagate into the prose.
   A precisely-calibrated medium claim beats a thrilling false one every time.

3. SELECT AND TIER (quality-gated, NOT quota-gated — never discard a synthesis
   that survived step 2 merely to hit a count):
   - ONE GOVERNING THESIS: the single richest synthesis, strong enough to be
     the spine of the whole essay.
   - CORE SYNTHESES: the strongest survivors, each independently
     transformative, each spanning ≥2 verses or a whole-psalm pattern, each
     distinct. Scale the number to the psalm's length: roughly one core
     synthesis per 3–4 verses, floor of 3, NO ceiling. A 9-verse psalm yields
     ~3; a 22-verse psalm should yield ~6–8 if that many genuinely survive.
   - ADDITIONAL SYNTHESES: every OTHER survivor that is real and cross-verse
     but a notch below the core ones. Do not throw these away — a long psalm
     in particular will have several. They will be woven more lightly into the
     prose rather than each given a full anchored development.
   Output every survivor. If the filter only leaves 3, output 3; if it leaves
   11, output 11. Honesty about quantity is the point.

### OUTPUT FORMAT (output ONLY this — no preamble, no brainstorm dump)

---SYNTHESIS-SPINE-START---

## GOVERNING THESIS
**Claim:** <2–3 sentences. The single idea the essay is built to deliver.>
**Verses it spans:** <list>
**Evidence (per verse, name the actual Hebrew):**
- v.<n>: <specific Hebrew + what it contributes>
- v.<n>: <...>
**Why a learned reader would not already know this:** <1 sentence>

## CORE SYNTHESIS 1
**Claim:** <2–3 sentences.>
**Verses it spans:** <list>
**Anchor verse:** <the ONE verse in whose commentary this must be developed in full>
**How to signal it at the other verses it touches:** <1 sentence>
**Evidence (per verse, name the actual Hebrew):**
- v.<n>: <...>
**Novelty check (why this is not obvious / not the dictionary):** <1 sentence>

## CORE SYNTHESIS 2
<same fields>

## CORE SYNTHESIS 3
<same fields>

(...continue CORE SYNTHESIS 4, 5, 6, ... — as many as survive the filter and
the ~1-per-3-4-verses scaling. Do NOT stop at an arbitrary number.)

## ADDITIONAL SYNTHESIS 1
**Claim:** <2–3 sentences.>
**Verses it spans:** <list>
**Anchor verse:** <best single verse to touch it>
**Evidence (per verse, name the actual Hebrew):**
- v.<n>: <...>
**Novelty check:** <1 sentence>

(...continue ADDITIONAL SYNTHESIS 2, 3, ... for every remaining survivor.
Omit this whole section only if there are genuinely no additional survivors.)

---SYNTHESIS-SPINE-END---
"""


# ---------------------------------------------------------------------------
# Call 2 — WRITE, using the approved spine
# ---------------------------------------------------------------------------
SPINE_ADDENDUM = """

## ═══════════════════════════════════════════════════════════════════════════
## APPROVED SYNTHESIS SPINE — BUILD THE COMMENTARY AROUND THIS
## ═══════════════════════════════════════════════════════════════════════════

Before this writing step, you performed a dedicated synthesis-discovery pass
on this same dossier and produced the spine below. Treat it as YOUR OWN prior
analysis (it is), now pre-approved as the skeleton for the piece.

{spine}

### HOW TO USE THE SPINE (non-negotiable)

1. The GOVERNING THESIS is the essay's spine. The introduction essay must
   build cumulatively toward it, exactly as STAGE 1 already requires.

2. Each CORE SYNTHESIS must be DEVELOPED IN FULL in the verse commentary at
   its named ANCHOR VERSE — not scattered as asides. At the anchor verse,
   explicitly trace the cross-verse arc (name the other verses and their
   Hebrew). At the other verses it touches, add the brief signal the spine
   specifies, so the reader feels the thread without redundancy. This is how a
   whole-psalm pattern earns a home in a verse-by-verse format.

3. Each ADDITIONAL SYNTHESIS must also reach the reader, but woven MORE
   LIGHTLY — a sentence or two at its anchor verse is enough. Do not inflate
   it into a full arc, and do not drop it. On a long psalm these are where
   much of the richness lives; the goal is that none of the survivors the
   discovery pass found simply vanishes in the writing.

4. The finished piece MUST carry the governing thesis PLUS every CORE synthesis
   visibly developed at its anchor verse, PLUS every ADDITIONAL synthesis at
   least touched. More syntheses is better here, not worse — a long psalm
   should feel dense with cross-verse architecture, never padded to a quota.

5. VETO LICENSE (RULE 12 still governs — you are the author, not a transcriber):
   if while writing you find a synthesis weak, or discover a stronger one, you
   MAY demote, reshape, promote an ADDITIONAL to CORE, or replace it. What you
   may NOT do is fall back to verse-isolated cataloguing, or quietly drop
   survivors to lighten your load. The constraint is on FORM (all core
   syntheses developed and anchored, all additional ones at least touched),
   not on which specific claims survive.

6. All other rules — especially RULE 7b (no false profundity), RULE 8 (cut or
   state plainly; never manufacture a payoff), phrase coverage's proportionate
   option (b), RULE 3c (no jargon) — apply with full force to the prose.

7. EVIDENCE HONESTY (hard): the spine's claims have already been calibrated for
   evidentiary strength. Do NOT re-inflate them when writing — keep "echoes"
   from becoming "verbatim," "consonantal play" from becoming "the same word /
   homophone," "close fit" from becoming "exact." Introduce NO biblical or
   rabbinic citation you cannot ground; every quoted Hebrew fragment must be a
   contiguous substring of its source. A calibrated claim that survives the
   citation verifier beats a thrilling one that gets deleted in copy-edit.

Now write the full commentary (essay + liturgical section + verse-by-verse +
refined reader questions) per the OUTPUT FORMAT above, built on this spine.
"""


TRANSIENT = (
    anthropic.APIConnectionError,
    anthropic.InternalServerError,
    anthropic.RateLimitError,
)


def stream_call(client: anthropic.Anthropic, prompt: str, tag: str, retries: int = 4) -> str:
    """One streaming Opus 4.7 call, mirroring the production writer config.

    Retries on transient stream drops (the RemoteProtocolError 'incomplete
    chunked read' that killed the first run is a mid-stream disconnect, not a
    logic error). Each attempt restarts the call from scratch.
    """
    for attempt in range(1, retries + 1):
        print(f"\n[{tag}] calling {MODEL} (effort=max, adaptive thinking) — attempt {attempt}/{retries}…")
        t0 = time.time()
        text, think_chars = "", 0
        try:
            with client.messages.stream(
                model=MODEL,
                max_tokens=128000,
                thinking={"type": "adaptive"},
                output_config={"effort": "max"},
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                for event in stream:
                    if getattr(event, "type", None) == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            text += event.delta.text
                        elif hasattr(event.delta, "thinking"):
                            think_chars += len(event.delta.thinking)
                final = stream.get_final_message()
            dt = time.time() - t0
            u = final.usage
            print(
                f"[{tag}] done in {dt:.0f}s — in={u.input_tokens:,} out={u.output_tokens:,} "
                f"(~{think_chars // 4:,} thinking) | response {len(text):,} chars"
            )
            return text
        except TRANSIENT as e:
            wait = 10 * attempt
            print(f"[{tag}] transient API error after {time.time()-t0:.0f}s: {type(e).__name__}: {e}")
            if attempt == retries:
                raise
            print(f"[{tag}] retrying in {wait}s (fresh call)…")
            time.sleep(wait)
        except Exception as e:
            # httpx.RemoteProtocolError (incomplete chunked read) is not an
            # anthropic.* type but is the exact transient we must survive.
            if "incomplete chunked read" in str(e) or "peer closed connection" in str(e):
                wait = 10 * attempt
                print(f"[{tag}] transient stream drop after {time.time()-t0:.0f}s: {e}")
                if attempt == retries:
                    raise
                print(f"[{tag}] retrying in {wait}s (fresh call)…")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError(f"[{tag}] exhausted {retries} attempts")


def main() -> None:
    psalm = int(sys.argv[1]) if len(sys.argv) > 1 else 54
    saved_prompt_path = ROOT / f"output/debug/master_writer_v4_prompt_psalm_{psalm}.txt"
    if not saved_prompt_path.exists():
        sys.exit(f"Missing saved writer prompt: {saved_prompt_path}")

    saved_prompt = saved_prompt_path.read_text(encoding="utf-8")
    if TASK_MARKER not in saved_prompt:
        sys.exit(f"Split marker not found in {saved_prompt_path}")

    # Context = persona + ground rules + ALL input data, minus the writing task.
    context_block = saved_prompt.split(TASK_MARKER)[0].rstrip()

    out_dir = ROOT / f"output/psalm_{psalm}/EXPERIMENT_two_call"
    out_dir.mkdir(parents=True, exist_ok=True)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # ---- Call 1: synthesis discovery (resume: skip if already done) ------
    call1_out_path = out_dir / "call1_synthesis_output.md"
    if call1_out_path.exists() and call1_out_path.stat().st_size > 500:
        print(f"[CALL 1 · SYNTHESIS] reusing existing output ({call1_out_path.name}) — skipping.")
        synthesis_out = call1_out_path.read_text(encoding="utf-8")
    else:
        call1_prompt = context_block + "\n\n" + SYNTHESIS_TASK.format(psalm_number=psalm)
        (out_dir / "call1_synthesis_prompt.txt").write_text(call1_prompt, encoding="utf-8")
        synthesis_out = stream_call(client, call1_prompt, "CALL 1 · SYNTHESIS")
        call1_out_path.write_text(synthesis_out, encoding="utf-8")

    m = re.search(
        r"---SYNTHESIS-SPINE-START---(.*?)---SYNTHESIS-SPINE-END---",
        synthesis_out,
        re.DOTALL,
    )
    spine = (m.group(1).strip() if m else synthesis_out.strip())
    if not m:
        print("[CALL 1] WARNING: spine markers not found — using full output as spine.")

    # ---- Call 2: write, built on the approved spine ----------------------
    call2_prompt = (
        saved_prompt
        + "\n\n"
        + extract_rule_updates()
        + SPINE_ADDENDUM.format(spine=spine)
    )
    (out_dir / "call2_write_prompt.txt").write_text(call2_prompt, encoding="utf-8")
    written = stream_call(client, call2_prompt, "CALL 2 · WRITE")
    (out_dir / "call2_full_response.md").write_text(written, encoding="utf-8")

    # Split intro vs verse commentary for easy side-by-side reading.
    vm = re.search(r"###?\s*VERSE COMMENTARY\s*\n", written, re.IGNORECASE)
    if vm:
        (out_dir / "TWO_CALL_intro.md").write_text(written[: vm.start()].strip(), encoding="utf-8")
        (out_dir / "TWO_CALL_verses.md").write_text(written[vm.end():].strip(), encoding="utf-8")

    print(f"\n[DONE] Experiment complete. Outputs in: {out_dir}")
    print("  - call1_synthesis_output.md  (the discovered spine)")
    print("  - TWO_CALL_intro.md / TWO_CALL_verses.md  (the written commentary)")
    print(f"\nCompare against shipped baseline:")
    print(f"  output/psalm_{psalm}/psalm_0{psalm}_edited_verses_pre_copy_edit.md")


if __name__ == "__main__":
    main()
