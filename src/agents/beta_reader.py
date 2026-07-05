"""
Beta Reader Agent — reader-experience measurement (NOT an editor)

Session 362: every quality agent in the pipeline polices accuracy and
convincingness (copy editor, scripture verifier); none reads the finished
guide the way a reader does. This agent simulates the commentary's target
audience — an intelligent, curious reader with Hebrew proficiency who is NOT
a biblical scholar — reading the final guide start to finish, and reports the
*experience*: where they leaned in, where they skimmed, what landed (aha /
wit / feeling), where the texture went template-ish, what confused them.

It is measurement-only BY DESIGN: it proposes no edits and its output feeds
no automatic revision pass (revision loops flatten voice). The report is for
the author — and for spotting systematic patterns across psalms (e.g. "the
back-half verses sag" showing up in every guide).

Cost: one Sonnet call over the finished guide (~45K chars in, ~3K tokens
out) ≈ $0.08/psalm.

Usage:
    from src.agents.beta_reader import BetaReader
    reader = BetaReader()
    result = reader.read_commentary(psalm_number=60)
    # -> output/psalm_60/psalm_060_beta_read.md
"""

import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, Optional

# Handle imports for both module and script usage
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.utils.logger import get_logger
    from src.utils.cost_tracker import CostTracker
else:
    from src.utils.logger import get_logger
    from src.utils.cost_tracker import CostTracker

import anthropic
from dotenv import load_dotenv

load_dotenv()


BETA_READER_PROMPT = """You are a BETA READER for a verse-by-verse readers' guide to a psalm. You are
the guide's exact target audience: intelligent, intellectually hungry, curious,
comfortable with Hebrew, NOT a biblical scholar. You read serious nonfiction
for pleasure. You are reading this guide the way a real reader does — once,
start to finish, for interest — not the way an editor combs a manuscript.

You are NOT an editor. Do not propose fixes, rewrites, cuts, or improvements.
Do not comment on factual accuracy — other agents do that. Your only job is to
report, honestly and specifically, what it was like to READ this.

Honesty calibration: a competent, accurate, but forgettable guide scores 5-6.
Reserve 8+ for sections you would read aloud to someone. Polite praise is
useless to the author; so is reflexive fault-finding. Report what actually
happened in your head as you read. When you quote, quote exactly.

Write your report in EXACTLY these sections:

## 1. Reading experience
A short paragraph: the honest story of your read. Where you sat up, where your
eyes started sliding, whether you finished eager or dutiful.

## 2. Engagement curve
One line per stretch of the guide (introduction essay; liturgical section;
then verse commentary in natural runs, e.g. "vv. 1-3"): LEANED IN / STEADY /
SKIMMED, plus one clause on why. This is the section future runs get compared
on, so be precise about WHERE attention changed.

## 3. Moments that landed
Up to 5 passages, quoted exactly (a phrase or sentence is enough), each tagged
AHA (an insight that clicked), WIT (made you smile), or FELT (moved you), with
one sentence on why it worked. If fewer than 5 landed, list fewer — an empty
category is data.

## 4. The affective landing
Did any single passage make you FEEL something — recognition, ache, awe —
rather than just interest? Quote it and say what it did. If nothing did, say
so plainly: "Nothing in this guide moved me." That sentence is one of the most
useful things you can tell the author.

## 5. Sag points and template feel
Where did attention flag? Where did consecutive sections feel like the same
move repeated (gloss a phrase → name a device → state the payoff)? Name the
specific verses/stretches. If a comparison, excursus, or device explanation
felt like it was there for completeness rather than for you, say which.

## 6. Confusion
Terms, threads, or transitions that lost you — quoted. (Not "could be
clearer" editorializing; only places you actually stumbled or re-read.)

## 7. Scores
Format each line exactly as `- <Dimension>: N/10 — <one-sentence justification>`:
- Engagement: how hard was it to stop reading?
- Clarity: did you ever feel talked past?
- Freshness: how much did you learn that a good translation + footnotes wouldn't give you?
- Wit: did it ever genuinely smile? (frequency AND quality)
- Emotional impact: did it ever move you?

## 8. Verdict
One or two sentences: would you hand this to the smartest friend you have who
isn't a scholar? Would they finish it?

THE GUIDE (Psalm {psalm_number}):

{guide_text}
"""


class BetaReader:
    """Simulated target-audience read of a finished guide. Measurement only."""

    DEFAULT_MODEL = "claude-sonnet-4-6"

    # Transient errors worth retrying (mirrors synthesis_discovery)
    TRANSIENT_ERRORS = (
        anthropic.APIConnectionError,
        anthropic.InternalServerError,
        anthropic.RateLimitError,
    )

    def __init__(self, model: str = None, logger=None, cost_tracker=None):
        self.model = model or self.DEFAULT_MODEL
        self.logger = logger or get_logger("beta_reader")
        self.cost_tracker = cost_tracker or CostTracker()
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self.client = anthropic.Anthropic(api_key=api_key)

    def read_commentary(
        self,
        psalm_number: int,
        input_file: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        retries: int = 3,
    ) -> Dict[str, str]:
        """Run the beta read on a finished guide.

        Input defaults to the copy-edited file when present (the closest text
        to what a reader sees), falling back to print_ready.

        Returns dict with keys: 'report_file', 'report', 'scores' (parsed
        {dimension: int} from section 7, empty if parsing fails).
        """
        psalm_dir = Path(f"output/psalm_{psalm_number}")
        if input_file is None:
            candidates = [
                psalm_dir / f"psalm_{psalm_number:03d}_copy_edited.md",
                psalm_dir / f"psalm_{psalm_number:03d}_print_ready.md",
            ]
            input_file = next((c for c in candidates if c.exists()), None)
            if input_file is None:
                raise FileNotFoundError(
                    f"No finished guide found for Psalm {psalm_number} "
                    f"(looked for copy_edited / print_ready in {psalm_dir})"
                )
        input_file = Path(input_file)
        if not input_file.exists():
            raise FileNotFoundError(f"Guide file not found: {input_file}")
        if output_dir is None:
            output_dir = psalm_dir
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        guide_text = input_file.read_text(encoding="utf-8")
        # The methodological/bibliographical tail is pipeline bookkeeping the
        # reader wouldn't read; don't bill for it or let it color the report.
        guide_text = re.split(
            r"## Methodological & Bibliographical Summary", guide_text
        )[0].rstrip()

        self.logger.info(f"═══ BETA READER — Psalm {psalm_number} ═══")
        self.logger.info(f"Input: {input_file} ({len(guide_text):,} chars)")

        prompt = BETA_READER_PROMPT.format(
            psalm_number=psalm_number, guide_text=guide_text
        )
        report, usage = self._call(prompt, psalm_number, retries=retries)

        self.cost_tracker.add_usage(
            model=self.model,
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            thinking_tokens=0,
        )

        report_path = output_dir / f"psalm_{psalm_number:03d}_beta_read.md"
        header = (
            f"# Beta Read — Psalm {psalm_number}\n\n"
            f"*Simulated target-audience read ({self.model}) of "
            f"`{input_file.name}`. Measurement only — feeds no revision "
            f"pass.*\n\n"
        )
        report_path.write_text(header + report.strip() + "\n", encoding="utf-8")
        self.logger.info(f"Saved: {report_path}")

        scores = self._parse_scores(report)
        if scores:
            self.logger.info(
                "Scores: " + ", ".join(f"{k} {v}/10" for k, v in scores.items())
            )

        return {
            "report_file": str(report_path),
            "report": report,
            "scores": scores,
        }

    # ------------------------------------------------------------------ utils

    @staticmethod
    def _parse_scores(report: str) -> Dict[str, int]:
        """Parse '- Dimension: N/10 — ...' lines from section 7."""
        scores: Dict[str, int] = {}
        for m in re.finditer(
            r"^\s*[-*]\s*([A-Za-z ]+?)\s*:\s*(\d{1,2})\s*/\s*10", report, re.M
        ):
            scores[m.group(1).strip()] = int(m.group(2))
        return scores

    def _call(self, prompt: str, psalm_number: int, retries: int = 3):
        for attempt in range(1, retries + 1):
            self.logger.info(
                f"[BETA READER psalm {psalm_number}] calling {self.model} "
                f"- attempt {attempt}/{retries}"
            )
            t0 = time.time()
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=8000,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = "".join(
                    block.text for block in response.content
                    if getattr(block, "type", None) == "text"
                )
                usage = {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                }
                self.logger.info(
                    f"[BETA READER psalm {psalm_number}] done in "
                    f"{time.time()-t0:.0f}s - in={usage['input_tokens']:,} "
                    f"out={usage['output_tokens']:,}"
                )
                return text, usage
            except self.TRANSIENT_ERRORS as e:
                wait = 10 * attempt
                self.logger.warning(
                    f"[BETA READER psalm {psalm_number}] transient error: "
                    f"{type(e).__name__}: {e}"
                )
                if attempt == retries:
                    raise
                self.logger.info(f"[BETA READER psalm {psalm_number}] retrying in {wait}s")
                time.sleep(wait)

        raise RuntimeError(f"[BETA READER psalm {psalm_number}] exhausted {retries} attempts")
