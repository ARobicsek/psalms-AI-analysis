"""
Literary Echoes Agent — Automated 4-pass literary-echoes generation.

Replaces the manual Gemini-web workflow with an API-driven pipeline:
  Pass 1  (generation)     — Gemini 3.1 Pro, high thinking
  Pass 2  (gap-fill)       — Gemini 3.1 Pro, high thinking, 5-10 new comparisons
  Pass 3  (verification)   — GPT-5.4 reasoning=high, with web_search_preview tool
  Pass 4  (reconstruction) — GPT-5.1 reasoning=minimal

Author-exclusion list: scans the 4 most-recently-rendered literary_echoes files
in data/literary_echoes/ and injects their authors into Pass 1 as a hard ban.

Per-psalm output layout:
    output/psalm_NNN/literary_echoes/
        pass_1_raw.txt
        pass_2_raw.txt
        pass_3_verification.txt
        pass_4_final.txt
        exclusion_list.txt
        cost_report.json
        gemini_prompts/
            pass_1_full.txt
            pass_2_full.txt
            pass_3_full.txt
            pass_4_full.txt

The final `pass_4_final.txt` is also copied to
    data/literary_echoes/psalm_NNN_literary_echoes.txt
so downstream `research_assembler` and the next psalm's exclusion-scan can pick
it up.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

from src.data_sources.tanakh_database import TanakhDatabase
from src.utils.cost_tracker import CostTracker
from src.utils.logger import get_logger

load_dotenv()


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROMPTS_DIR = PROJECT_ROOT / "docs" / "prompts_reference"
ECHOES_DATA_DIR = PROJECT_ROOT / "data" / "literary_echoes"

PASS_1_PROMPT_FILE = PROMPTS_DIR / "literary echoes pass 1 - tier override.txt"
PASS_2_PROMPT_FILE = PROMPTS_DIR / "literary echoes pass 2 - tier override.txt"
PASS_3_PROMPT_FILE = PROMPTS_DIR / "literary echoes pass 3.txt"
PASS_4_PROMPT_FILE = PROMPTS_DIR / "literary echoes pass 4 - tier override.txt"

GEMINI_MODEL = "gemini-3.1-pro-preview"
GPT_VERIFY_MODEL = "gpt-5.4"
# Note: We tried gpt-5.1 first per the original plan (cheaper "inexpensive GPT")
# but it self-terminated early at all reasoning levels on the ~30K char Pass-4
# prompt, emitting only the first cluster. gpt-5.4 produces the full
# reconstruction reliably. Cost differential is ~$0.04/psalm — acceptable.
GPT_RECONSTRUCT_MODEL = "gpt-5.4"

# High thinking for creative passes; Gemini accepts budgets up to 32768.
# 24000 gives the model ample budget for "silently list first echoes, push past"
# reasoning without blowing up latency/cost.
GEMINI_THINKING_BUDGET = 24000

# Scan the N most-recently-rendered files for exclusions.
EXCLUSION_WINDOW = 4


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class PassResult:
    pass_name: str
    model: str
    output_text: str
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    cost: float = 0.0
    elapsed_s: float = 0.0


@dataclass
class LiteraryEchoesResult:
    psalm_number: int
    final_text: str
    final_path: Path
    exclusion_authors: List[str]
    exclusion_source_files: List[str]
    passes: List[PassResult] = field(default_factory=list)

    @property
    def total_cost(self) -> float:
        return sum(p.cost for p in self.passes)

    def to_cost_report(self) -> dict:
        return {
            "psalm_number": self.psalm_number,
            "total_cost_usd": round(self.total_cost, 4),
            "exclusion_source_files": self.exclusion_source_files,
            "exclusion_author_count": len(self.exclusion_authors),
            "passes": [
                {
                    "pass": p.pass_name,
                    "model": p.model,
                    "input_tokens": p.input_tokens,
                    "output_tokens": p.output_tokens,
                    "thinking_tokens": p.thinking_tokens,
                    "cost_usd": round(p.cost, 4),
                    "elapsed_s": round(p.elapsed_s, 1),
                }
                for p in self.passes
            ],
        }


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class LiteraryEchoesAgent:
    """Run the 4-pass literary-echoes workflow for one psalm."""

    def __init__(
        self,
        cost_tracker: Optional[CostTracker] = None,
        db_path: str = "database/tanakh.db",
        logger=None,
    ):
        self.cost_tracker = cost_tracker or CostTracker()
        self.db_path = db_path
        self.logger = logger or get_logger("literary_echoes_agent")
        self._gemini_client = None
        self._openai_client = None

    # ------------------------------------------------------------------ API

    def generate(
        self,
        psalm_number: int,
        psalm_output_dir: Path,
        skip_if_exists: bool = False,
    ) -> LiteraryEchoesResult:
        """Run the full 4-pass workflow for one psalm.

        Default behavior is to regenerate and overwrite. Pass
        `skip_if_exists=True` to short-circuit when the canonical output
        already exists in data/literary_echoes/.
        """
        final_canonical = ECHOES_DATA_DIR / f"psalm_{psalm_number:03d}_literary_echoes.txt"
        if skip_if_exists and final_canonical.exists():
            self.logger.info(
                f"[lit_echoes] Canonical file exists and skip_if_exists=True — skipping Psalm {psalm_number}"
            )
            return LiteraryEchoesResult(
                psalm_number=psalm_number,
                final_text=final_canonical.read_text(encoding="utf-8"),
                final_path=final_canonical,
                exclusion_authors=[],
                exclusion_source_files=[],
                passes=[],
            )

        work_dir = Path(psalm_output_dir) / "literary_echoes"
        prompts_dir = work_dir / "gemini_prompts"
        work_dir.mkdir(parents=True, exist_ok=True)
        prompts_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"[lit_echoes] Starting 4-pass workflow for Psalm {psalm_number}")

        # 1. Gather inputs
        psalm_text = self._load_psalm_text(psalm_number)
        exclusion_authors, exclusion_sources = self._build_exclusion_list(psalm_number)
        self._save_exclusion_list(work_dir, exclusion_authors, exclusion_sources)

        # 2. Pass 1 — Gemini generation
        p1_prompt = self._build_pass_1_prompt(psalm_number, psalm_text, exclusion_authors)
        (prompts_dir / "pass_1_full.txt").write_text(p1_prompt, encoding="utf-8")
        p1 = self._call_gemini(p1_prompt, pass_name="pass_1")
        (work_dir / "pass_1_raw.txt").write_text(p1.output_text, encoding="utf-8")

        # 3. Pass 2 — Gemini gap-fill (also inject exclusion list: session-338 test
        # on Psalm 53 showed Pass 2 used canonical-slot authors already banned by
        # the cross-psalm exclusion — Pass 2 must see the same ban list as Pass 1)
        p2_prompt = self._build_pass_2_prompt(
            psalm_number, psalm_text, p1.output_text, exclusion_authors
        )
        (prompts_dir / "pass_2_full.txt").write_text(p2_prompt, encoding="utf-8")
        p2 = self._call_gemini(p2_prompt, pass_name="pass_2")
        (work_dir / "pass_2_raw.txt").write_text(p2.output_text, encoding="utf-8")

        # 4. Pass 3 — GPT-5.4 verification with web search
        p3_prompt = self._build_pass_3_prompt(psalm_number, psalm_text, p1.output_text, p2.output_text)
        (prompts_dir / "pass_3_full.txt").write_text(p3_prompt, encoding="utf-8")
        p3 = self._call_openai_verify(p3_prompt, pass_name="pass_3")
        (work_dir / "pass_3_verification.txt").write_text(p3.output_text, encoding="utf-8")

        # 5. Pass 4 — GPT-5.1 reconstruction
        p4_prompt = self._build_pass_4_prompt(
            psalm_number, psalm_text, p1.output_text, p2.output_text, p3.output_text
        )
        (prompts_dir / "pass_4_full.txt").write_text(p4_prompt, encoding="utf-8")
        p4 = self._call_openai_reconstruct(p4_prompt, pass_name="pass_4")
        (work_dir / "pass_4_final.txt").write_text(p4.output_text, encoding="utf-8")

        # 6. Copy final to canonical location
        ECHOES_DATA_DIR.mkdir(parents=True, exist_ok=True)
        final_canonical.write_text(p4.output_text, encoding="utf-8")
        self.logger.info(f"[lit_echoes] Canonical file written → {final_canonical}")

        # 7. Assemble result + cost report
        result = LiteraryEchoesResult(
            psalm_number=psalm_number,
            final_text=p4.output_text,
            final_path=final_canonical,
            exclusion_authors=exclusion_authors,
            exclusion_source_files=exclusion_sources,
            passes=[p1, p2, p3, p4],
        )
        (work_dir / "cost_report.json").write_text(
            json.dumps(result.to_cost_report(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        self.logger.info(
            f"[lit_echoes] Psalm {psalm_number} complete — total ${result.total_cost:.4f} "
            f"across {len(result.passes)} passes"
        )
        return result

    # --------------------------------------------------------- Input loaders

    def _load_psalm_text(self, psalm_number: int) -> str:
        """Build the Hebrew+English psalm text block for prompt substitution."""
        db = TanakhDatabase(Path(self.db_path))
        psalm = db.get_psalm(psalm_number)
        if not psalm:
            raise RuntimeError(f"Psalm {psalm_number} not found in database {self.db_path}")
        lines = []
        for v in psalm.verses:
            lines.append(f"**{psalm_number}:{v.verse}** {v.hebrew}")
            lines.append(f"{v.english}")
            lines.append("")
        return "\n".join(lines).strip()

    def _build_exclusion_list(self, psalm_number: int) -> Tuple[List[str], List[str]]:
        """Scan the N most-recently-rendered echoes files (by mtime) and
        extract authors.

        Excludes the current psalm's file if it exists (we are regenerating it).
        """
        if not ECHOES_DATA_DIR.exists():
            return [], []

        current_name = f"psalm_{psalm_number:03d}_literary_echoes.txt"
        candidates = []
        for f in ECHOES_DATA_DIR.glob("psalm_*_literary_echoes.txt"):
            if f.name == current_name:
                continue
            try:
                candidates.append((f.stat().st_mtime, f))
            except OSError:
                continue
        candidates.sort(key=lambda t: t[0], reverse=True)
        recent = [f for _, f in candidates[:EXCLUSION_WINDOW]]

        author_pattern = re.compile(r"^####\s+([^,\n*]+?)\s*,", re.MULTILINE)
        seen: Dict[str, str] = {}  # lowercase -> original
        for path in recent:
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for m in author_pattern.finditer(text):
                name = m.group(1).strip()
                # Strip any leading asterisks/whitespace artifacts from markdown
                name = name.strip(" *")
                if not name:
                    continue
                key = name.lower()
                if key not in seen:
                    seen[key] = name
        authors = sorted(seen.values(), key=str.casefold)
        source_files = [p.name for p in recent]
        self.logger.info(
            f"[lit_echoes] Exclusion scan: {len(authors)} unique authors from {len(recent)} recent files"
        )
        return authors, source_files

    def _save_exclusion_list(
        self, work_dir: Path, authors: List[str], sources: List[str]
    ) -> None:
        lines = [
            "# Exclusion list for this literary echoes run",
            f"# Window: last {EXCLUSION_WINDOW} rendered files (by mtime)",
            "",
            "## Source files",
        ]
        lines.extend(f"- {s}" for s in sources) if sources else lines.append("- (none)")
        lines.extend(["", "## Authors banned from this run", ""])
        if authors:
            lines.extend(f"- {a}" for a in authors)
        else:
            lines.append("(none — no prior rendered files found)")
        (work_dir / "exclusion_list.txt").write_text("\n".join(lines), encoding="utf-8")

    # --------------------------------------------------- Prompt construction

    def _load_template(self, path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(f"Prompt template missing: {path}")
        return path.read_text(encoding="utf-8")

    def _build_pass_1_prompt(
        self, psalm_number: int, psalm_text: str, exclusion_authors: List[str]
    ) -> str:
        template = self._load_template(PASS_1_PROMPT_FILE)
        # Replace psalm-number tokens + psalm-text placeholder
        template = template.replace("{NUMBER}", str(psalm_number))
        template = template.replace("[PSALM FULL TEXT]", psalm_text)

        # Inject exclusion block immediately above SECOND ECHO PRINCIPLE
        if exclusion_authors:
            exclusion_block = (
                "=== AUTHORS USED IN LAST 4 PSALMS (DO NOT REUSE) ===\n\n"
                "The following authors appeared in the most recent psalms in this "
                "series. None of them may appear in this document — find fresher "
                "second-tier sources.\n\n"
                + ", ".join(exclusion_authors)
                + "\n\n"
            )
            template = template.replace(
                "=== THE SECOND ECHO PRINCIPLE ===",
                exclusion_block + "=== THE SECOND ECHO PRINCIPLE ===",
                1,
            )
        return template

    def _build_pass_2_prompt(
        self,
        psalm_number: int,
        psalm_text: str,
        pass_1_output: str,
        exclusion_authors: Optional[List[str]] = None,
    ) -> str:
        template = self._load_template(PASS_2_PROMPT_FILE)
        template = template.replace("{NUMBER}", str(psalm_number))

        # Pass 2 prompt starts with "You are enriching the literary echoes document
        # above". We need to actually provide that document. Prepend psalm + pass 1.
        header_parts = [
            f"PSALM {psalm_number} — LITERARY ECHOES (Pass 2 input)\n\n",
            f"[PSALM FULL TEXT]\n\n{psalm_text}\n\n",
            f"[PASS 1 OUTPUT — the existing literary echoes document]\n\n",
            f"{pass_1_output}\n\n",
        ]
        if exclusion_authors:
            header_parts.append(
                "[AUTHORS USED IN LAST 4 PSALMS — DO NOT REUSE, even in Earned Canonical Slots]\n\n"
                "The following authors appeared in the most recent psalms. They are "
                "banned from THIS psalm as well, in addition to the ones already used "
                "in Pass 1. This applies even to Earned Canonical Slot authors — if a "
                "canonical-slot author appears below, skip them and pick a different "
                "second-tier voice:\n\n"
                + ", ".join(exclusion_authors)
                + "\n\n"
            )
        header_parts.extend([
            "---\n\n",
            "[PASS 2 INSTRUCTIONS]\n\n",
        ])
        return "".join(header_parts) + template

    def _build_pass_3_prompt(
        self,
        psalm_number: int,
        psalm_text: str,
        pass_1_output: str,
        pass_2_output: str,
    ) -> str:
        template = self._load_template(PASS_3_PROMPT_FILE)
        template = template.replace("{NUMBER}", str(psalm_number))
        # Pass 3 template says "Attached is a literary echoes document" — attach it.
        header = (
            f"PSALM {psalm_number} — LITERARY ECHOES (Pass 3 input)\n\n"
            f"[PSALM FULL TEXT]\n\n{psalm_text}\n\n"
            f"[PASS 1 + PASS 2 COMBINED DOCUMENT TO AUDIT]\n\n"
            f"{pass_1_output}\n\n{pass_2_output}\n\n"
            f"---\n\n"
            f"[PASS 3 INSTRUCTIONS]\n\n"
        )
        return header + template

    def _build_pass_4_prompt(
        self,
        psalm_number: int,
        psalm_text: str,
        pass_1_output: str,
        pass_2_output: str,
        pass_3_output: str,
    ) -> str:
        template = self._load_template(PASS_4_PROMPT_FILE)
        template = template.replace("{NUMBER}", str(psalm_number))
        header = (
            f"PSALM {psalm_number} — LITERARY ECHOES (Pass 4 input)\n\n"
            f"[PSALM FULL TEXT]\n\n{psalm_text}\n\n"
            f"[PASS 1 OUTPUT]\n\n{pass_1_output}\n\n"
            f"[PASS 2 OUTPUT]\n\n{pass_2_output}\n\n"
            f"[PASS 3 VERIFICATION NOTES]\n\n{pass_3_output}\n\n"
            f"---\n\n"
            f"[PASS 4 INSTRUCTIONS]\n\n"
        )
        return header + template

    # ----------------------------------------------------- Model invocations

    def _get_gemini_client(self):
        if self._gemini_client is None:
            try:
                from google import genai  # noqa: F401
            except ImportError:
                raise ImportError(
                    "google-genai required for literary echoes. "
                    "pip install google-genai"
                )
            from google import genai
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not set in environment")
            self._gemini_client = genai.Client(api_key=api_key)
        return self._gemini_client

    def _get_openai_client(self):
        if self._openai_client is None:
            from openai import OpenAI
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set in environment")
            self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client

    def _call_gemini(self, prompt: str, pass_name: str) -> PassResult:
        from google.genai import types

        client = self._get_gemini_client()
        self.logger.info(
            f"[lit_echoes] {pass_name}: Gemini {GEMINI_MODEL} "
            f"(thinking_budget={GEMINI_THINKING_BUDGET}, prompt {len(prompt):,} chars)"
        )
        max_retries = 3
        start = time.time()
        last_err: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait = 2 * (2 ** (attempt - 1))
                    self.logger.info(f"[lit_echoes] {pass_name}: retry {attempt+1}/{max_retries} after {wait}s")
                    time.sleep(wait)
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.8,
                        thinking_config=types.ThinkingConfig(
                            thinking_budget=GEMINI_THINKING_BUDGET
                        ),
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(
                            disable=True
                        ),
                    ),
                )
                break
            except Exception as e:
                last_err = e
                msg = str(e).lower()
                if any(ind in msg for ind in ["429", "rate limit", "too many", "try again", "503", "504"]):
                    if attempt < max_retries - 1:
                        continue
                raise
        else:
            raise last_err  # pragma: no cover — loop exits via break or raise

        output_text = response.text or ""
        elapsed = time.time() - start

        input_tokens = output_tokens = thinking_tokens = 0
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = response.usage_metadata
            input_tokens = getattr(usage, "prompt_token_count", 0) or 0
            output_tokens = getattr(usage, "candidates_token_count", 0) or 0
            thinking_tokens = getattr(usage, "thoughts_token_count", 0) or 0

        self.cost_tracker.add_usage(
            model=GEMINI_MODEL,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thinking_tokens=thinking_tokens,
        )
        cost = self._compute_cost_gemini(input_tokens, output_tokens, thinking_tokens)
        self.logger.info(
            f"[lit_echoes] {pass_name}: done in {elapsed:.1f}s — "
            f"in={input_tokens:,} out={output_tokens:,} think={thinking_tokens:,} ${cost:.4f}"
        )
        return PassResult(
            pass_name=pass_name,
            model=GEMINI_MODEL,
            output_text=output_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thinking_tokens=thinking_tokens,
            cost=cost,
            elapsed_s=elapsed,
        )

    def _call_openai_verify(self, prompt: str, pass_name: str) -> PassResult:
        """Pass 3 — GPT-5.4 with web_search_preview tool enabled."""
        client = self._get_openai_client()
        self.logger.info(
            f"[lit_echoes] {pass_name}: {GPT_VERIFY_MODEL} "
            f"(reasoning=high, web_search ON, prompt {len(prompt):,} chars)"
        )
        start = time.time()
        # Responses API supports `tools=[{"type": "web_search_preview"}]`
        response = client.responses.create(
            model=GPT_VERIFY_MODEL,
            input=prompt,
            reasoning={"effort": "high"},
            tools=[{"type": "web_search_preview"}],
            max_output_tokens=32000,
        )
        output_text = response.output_text or ""
        elapsed = time.time() - start

        usage = response.usage
        input_tokens = getattr(usage, "input_tokens", 0) or 0
        output_tokens = getattr(usage, "output_tokens", 0) or 0
        thinking_tokens = 0
        details = getattr(usage, "output_tokens_details", None)
        if details is not None:
            thinking_tokens = getattr(details, "reasoning_tokens", 0) or 0

        self.cost_tracker.add_usage(
            model=GPT_VERIFY_MODEL,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thinking_tokens=thinking_tokens,
        )
        cost = self._compute_cost_gpt(GPT_VERIFY_MODEL, input_tokens, output_tokens, thinking_tokens)
        self.logger.info(
            f"[lit_echoes] {pass_name}: done in {elapsed:.1f}s — "
            f"in={input_tokens:,} out={output_tokens:,} think={thinking_tokens:,} ${cost:.4f}"
        )
        return PassResult(
            pass_name=pass_name,
            model=GPT_VERIFY_MODEL,
            output_text=output_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thinking_tokens=thinking_tokens,
            cost=cost,
            elapsed_s=elapsed,
        )

    def _call_openai_reconstruct(self, prompt: str, pass_name: str) -> PassResult:
        """Pass 4 — GPT-5.1 via Chat Completions API (mechanical reconstruction).

        Uses Chat Completions rather than the Responses API because the
        Responses-API content filter is more aggressive on long multi-language
        religious/literary prompts and was rejecting the assembled Pass-4
        input (reason='content_filter', all usage fields zero). Chat
        Completions handles the same content fine. `reasoning_effort="low"`
        keeps cost minimal for what is essentially string-manipulation.
        """
        client = self._get_openai_client()
        self.logger.info(
            f"[lit_echoes] {pass_name}: {GPT_RECONSTRUCT_MODEL} "
            f"(chat.completions, reasoning_effort=medium, prompt {len(prompt):,} chars)"
        )
        start = time.time()
        response = client.chat.completions.create(
            model=GPT_RECONSTRUCT_MODEL,
            reasoning_effort="medium",
            max_completion_tokens=32000,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
        output_text = response.choices[0].message.content or ""
        elapsed = time.time() - start

        usage = response.usage
        input_tokens = getattr(usage, "prompt_tokens", 0) or 0
        output_tokens = getattr(usage, "completion_tokens", 0) or 0
        thinking_tokens = 0
        details = getattr(usage, "completion_tokens_details", None)
        if details is not None:
            thinking_tokens = getattr(details, "reasoning_tokens", 0) or 0

        self.cost_tracker.add_usage(
            model=GPT_RECONSTRUCT_MODEL,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thinking_tokens=thinking_tokens,
        )
        cost = self._compute_cost_gpt(GPT_RECONSTRUCT_MODEL, input_tokens, output_tokens, thinking_tokens)
        self.logger.info(
            f"[lit_echoes] {pass_name}: done in {elapsed:.1f}s — "
            f"in={input_tokens:,} out={output_tokens:,} think={thinking_tokens:,} ${cost:.4f}"
        )
        return PassResult(
            pass_name=pass_name,
            model=GPT_RECONSTRUCT_MODEL,
            output_text=output_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thinking_tokens=thinking_tokens,
            cost=cost,
            elapsed_s=elapsed,
        )

    # ---------------------------------------------------- Cost calculations
    # (Rates are duplicated from src/utils/cost_tracker.py PRICING table so the
    # per-pass report is self-contained. Keep in sync.)

    @staticmethod
    def _compute_cost_gemini(in_tok: int, out_tok: int, think_tok: int) -> float:
        # gemini-3.1-pro-preview: $2 / $12 / $12 per M
        return (in_tok / 1_000_000) * 2.00 + (out_tok / 1_000_000) * 12.00 + (think_tok / 1_000_000) * 12.00

    @staticmethod
    def _compute_cost_gpt(model: str, in_tok: int, out_tok: int, think_tok: int) -> float:
        if model == "gpt-5.4":
            i, o, t = 2.50, 15.00, 15.00
        elif model == "gpt-5.1" or model == "gpt-5":
            i, o, t = 1.25, 10.00, 10.00
        else:
            return 0.0
        # GPT output_tokens already *includes* reasoning/thinking tokens, so
        # attribute the reasoning fraction at thinking-rate and the rest at
        # output-rate.
        non_think = max(0, out_tok - think_tok)
        return (in_tok / 1_000_000) * i + (non_think / 1_000_000) * o + (think_tok / 1_000_000) * t


__all__ = ["LiteraryEchoesAgent", "LiteraryEchoesResult", "PassResult"]
