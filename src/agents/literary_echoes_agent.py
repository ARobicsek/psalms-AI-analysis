"""
Literary Echoes Agent — automated literary-echoes generation.

Pass 1a (generation)   — Gemini 3.1 Pro, high thinking
Pass 1b (generation)   — OPTIONAL second generator, OFF by default (see below)
         merge         — deterministic, alternating by cluster
Pass 2  (gap-fill)     — Gemini 3.1 Pro, high thinking, 5-10 new comparisons
Pass 3  (verification) — gpt-5.6-terra + web search, ONE CALL PER ENTRY, JSON verdicts
         reconstruct   — deterministic, in Python (see literary_echoes_parser)

SESSION 374 REWRITE. Four things were wrong with the previous shape:

1. PASS 4 WAS SILENTLY EATING FINISHED WORK. The LLM "reconstruction" pass
   truncated mid-quotation on psalms 69/70/71/72, which kept 16%/37%/47%/61% of
   their verified echoes. None hit `max_completion_tokens` (Ps 71 emitted 2,784
   of a 32,000 budget) — the model just stopped, and `finish_reason` was never
   checked. Psalm 71 is the psalm every writer-prompt A/B since Session 370 ran
   on, and its dossier was missing half its echoes the whole time. Pass 4 is now
   gone: Pass 3 returns structured per-entry verdicts and `literary_echoes_parser`
   rebuilds the document by string manipulation, which cannot stop early.

2. EMPTY GENERATIONS WERE SWALLOWED. `response.text or ""` turned a failed Gemini
   call into an empty string and the pipeline carried on. 3 of 26 runs lost a
   whole pass this way (Ps 1 and 68 lost Pass 1, Ps 55 lost Pass 2). Every call
   now validates its own output and retries, then raises.

3. THE PRICING TABLE WAS A STALE DUPLICATE. This module carried its own copy of
   the rates with terra at $2.50/$15.00, six weeks after Session 373 corrected
   `cost_tracker.PRICING` to $2.00/$12.00 — the docstring said "keep in sync" and
   it was not. Costs now come from `cost_tracker.PRICING`, the one table, and
   OpenAI cached-input tokens are credited at the cache_read rate instead of
   being billed as fresh input.

4. THE EXCLUSION LIST COULD ONLY SEE 4 FILES. Author diversity is a claim about
   the whole series, but the scan looked at the 4 most recently written files.
   Replaced by a corpus-wide `AuthorLedger`. Measured over the 24 psalms this
   pipeline has built: 12 authors were already at 4 appearances, 22 more at 3.

Per-psalm output layout:
    output/psalm_NNN/literary_echoes/
        pass_1a_gemini.txt
        pass_1b_opus.txt          (only when --second-generator is used)
        pass_1_merged.md          (deterministic merge, for inspection)
        pass_2_raw.txt
        pass_3_verdicts.json      (one record per entry: verdict + reason)
        final.md
        exclusion_list.txt
        author_ledger.json
        cost_report.json
        prompts/
            pass_1a_full.txt, pass_1b_full.txt, pass_2_full.txt, pass_3_sample.txt

The final document is also copied to
    data/literary_echoes/psalm_NNN_literary_echoes.txt
so downstream `research_assembler` and the next psalm's ledger can pick it up.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from dotenv import load_dotenv

from src.agents.literary_echoes_parser import (
    AuthorLedger,
    EchoEntry,
    Verdict,
    apply_replacements,
    apply_verdict,
    dedupe_authors,
    drop_malformed,
    merge_pass1_variants,
    parse_document,
    parse_verdict,
    reconstruct,
)
from src.data_sources.tanakh_database import TanakhDatabase
from src.utils.cost_tracker import PRICING, CostTracker
from src.utils.logger import get_logger
from src.utils.openai_usage import split_output_tokens

load_dotenv()


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROMPTS_DIR = PROJECT_ROOT / "docs" / "prompts_reference"
ECHOES_DATA_DIR = PROJECT_ROOT / "data" / "literary_echoes"
LEDGER_PATH = ECHOES_DATA_DIR / "_author_ledger.json"

PASS_1_PROMPT_FILE = PROMPTS_DIR / "literary echoes pass 1 - tier override.txt"
PASS_2_PROMPT_FILE = PROMPTS_DIR / "literary echoes pass 2 - tier override.txt"
PASS_3_PROMPT_FILE = PROMPTS_DIR / "literary echoes pass 3 - per entry.txt"

GEMINI_MODEL = "gemini-3.1-pro-preview"

# Second Pass-1 generator — BUILT, MEASURED, AND OFF BY DEFAULT (Session 374).
#
# The idea is sound: the Second Echo Principle asks the model to push past the
# first names that surface, but a model can only push past its OWN reflexes, so a
# second model from a different family attacks the problem at its root. When it
# did run, the merge was exactly what was wanted — on Psalm 1, Sonnet 5 supplied
# 11 authors Gemini never reached, with only 2 overlaps out of 13.
#
# It does not work on any Anthropic model with the current Pass-1 prompt. Measured:
#
#   claude-opus-4-8   effort=high,   32k  -> content-filter block  (x3, live run)
#   claude-opus-4-8   effort=high,   32k  -> block (softened profanity section)
#   claude-opus-4-8   effort=high,   32k  -> block (no-modern-lyrics restriction)
#   claude-opus-4-8   effort=medium, 32k  -> block
#   claude-opus-4-8   effort=medium, 64k  -> block
#   claude-opus-4-8   effort=high,   64k  -> block
#   claude-sonnet-5   effort=high,   32k  -> no block, but 0 visible chars
#                                            (all 32k spent thinking)
#   claude-sonnet-5   effort=medium, 64k  -> block
#   claude-sonnet-5   effort=low,    64k  -> RUNS, but the model does its
#                                            deliberation in the DOCUMENT:
#                                            "#### Gwendolyn Brooks - not eligible
#                                            (American, but let me choose properly)"
#
# So high/medium effort trips an output content filter, and the only setting that
# clears it produces format-non-compliant output. `drop_malformed` in the parser
# now catches that class of damage whatever model emits it, but a generator whose
# usable configuration is "none" should not run by default and silently burn a
# blocked call on every psalm.
#
# NEXT THING TO TRY (not attempted, to stop spending on trial and error): a
# non-Anthropic second generator. gpt-5.6-terra is already wired for Pass 3, so
# the key and cost model exist, and it is as different from Gemini as Claude is.
SECOND_GEN_MODEL = "claude-sonnet-5"
SECOND_GEN_MAX_TOKENS = 64000
# Explicitly NOT via `model_effort.apply_effort`: that helper is the single source
# of truth for the three deep-reasoning agents (macro analyst, synthesis discovery,
# master writer). Pass 1b is recall-and-recite, and inheriting their `high` is what
# starved Sonnet 5 of output room in the measurement above.
SECOND_GEN_EFFORT = "low"

# Pass 3 verification. Kept on terra: Session 367 moved it here and the measured
# rejection rate (~1.7 fabrications per psalm out of ~19 quotations) says the
# model is doing the job. If verification quality ever regresses, "gpt-5.4" is
# the known-good predecessor and cost_tracker prices it.
GPT_VERIFY_MODEL = "gpt-5.6-terra"

# Gemini accepts budgets up to 32768. 24000 gives ample room for the "silently
# list first echoes, push past them" reasoning without blowing up latency.
GEMINI_THINKING_BUDGET = 24000

# Ledger policy.
#   EXCLUSION_WINDOW  hard ban on anyone used in the last N psalms (adjacency)
#   LIFETIME_BAN_AT   hard ban on anyone already used in >= N psalms (series)
# LIFETIME_BAN_AT=3 means an author may appear in at most two psalms ever. On the
# corpus as it stands that bans 34 names — a real constraint that still leaves
# the field wide open. Raise it if the generators start struggling to fill quotas.
EXCLUSION_WINDOW = 4
LIFETIME_BAN_AT = 3
LEDGER_PROMPT_LIMIT = 120

# Pass 3 fans out one call per entry. Concurrency is bounded to stay well inside
# OpenAI rate limits while still collapsing what was a 200-580s serial pass.
VERIFY_WORKERS = 6
VERIFY_RETRIES = 3
VERIFY_MAX_OUTPUT_TOKENS = 8000


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class PassResult:
    pass_name: str
    model: str
    output_text: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    cached_input_tokens: int = 0
    cost: float = 0.0
    elapsed_s: float = 0.0
    call_count: int = 1


@dataclass
class LiteraryEchoesResult:
    psalm_number: int
    final_text: str
    final_path: Path
    exclusion_authors: List[str]
    overused_authors: List[str]
    passes: List[PassResult] = field(default_factory=list)
    entry_stats: Dict[str, int] = field(default_factory=dict)
    provenance: Dict[str, int] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    @property
    def total_cost(self) -> float:
        return sum(p.cost for p in self.passes)

    def to_cost_report(self) -> dict:
        return {
            "psalm_number": self.psalm_number,
            "total_cost_usd": round(self.total_cost, 4),
            "exclusion_author_count": len(self.exclusion_authors),
            "overused_author_count": len(self.overused_authors),
            "entry_stats": self.entry_stats,
            "surviving_entries_by_source": self.provenance,
            "notes": self.notes,
            "passes": [
                {
                    "pass": p.pass_name,
                    "model": p.model,
                    "calls": p.call_count,
                    "input_tokens": p.input_tokens,
                    "cached_input_tokens": p.cached_input_tokens,
                    "output_tokens": p.output_tokens,
                    "thinking_tokens": p.thinking_tokens,
                    "cost_usd": round(p.cost, 4),
                    "elapsed_s": round(p.elapsed_s, 1),
                }
                for p in self.passes
            ],
        }


class LiteraryEchoesGenerationError(RuntimeError):
    """A pass produced no usable output after all retries."""


# Substrings that mark a failure worth retrying. Everything else is treated as
# deterministic: a content-filter refusal, a malformed request, or a bad API key
# will reproduce identically on every attempt, so retrying only spends wall clock
# and — for a stream that was already partly generated — real output tokens.
_TRANSIENT_MARKERS = (
    "429",
    "500",
    "502",
    "503",
    "504",
    "overloaded",
    "rate limit",
    "rate_limit",
    "too many",
    "timeout",
    "timed out",
    "try again",
    "connection",
    "incomplete chunked read",
    "peer closed connection",
    "temporarily unavailable",
)


def _is_transient(exc: Exception) -> bool:
    """Is this error worth a retry?

    Deliberately conservative in the retry direction: an unrecognised error is
    treated as transient, because a spurious retry costs one extra call whereas
    wrongly giving up loses the pass.
    """
    text = f"{type(exc).__name__}: {exc}".lower()
    deterministic = (
        "content filtering",
        "content_filter",
        "invalid_request_error",
        "authentication",
        "permission",
        "not_found_error",
    )
    if any(marker in text for marker in deterministic):
        # An overloaded/rate-limited signal still wins if both are present.
        return any(marker in text for marker in _TRANSIENT_MARKERS)
    return True


# ---------------------------------------------------------------------------
# Pricing — one table, the shared one
# ---------------------------------------------------------------------------


def price_call(
    model: str,
    input_tokens: int,
    output_tokens: int,
    thinking_tokens: int = 0,
    cached_input_tokens: int = 0,
) -> float:
    """Cost of a single call, priced from `cost_tracker.PRICING`.

    TOKEN CONTRACT — every argument is DISJOINT, matching what `CostTracker`
    expects, because `calculate_cost` ADDS output and thinking together:

        input_tokens         fresh (uncached) input only
        cached_input_tokens  input served from cache, priced at cache_read
        output_tokens        visible output, EXCLUDING reasoning
        thinking_tokens      reasoning only

    Callers are responsible for the split, because the three vendors disagree:
      * Gemini reports them separately already (`candidates` vs `thoughts`).
      * Anthropic folds thinking INTO `output_tokens`, so pass `thinking=0`.
      * OpenAI also folds reasoning into `output_tokens` AND folds cached tokens
        into `input_tokens` — use `openai_usage.split_output_tokens` and subtract
        `input_tokens_details.cached_tokens`. Passing OpenAI's raw totals for both
        would bill reasoning twice, which is the exact trap `src/utils/openai_usage.py`
        was written to document.

    Crediting cached input matters here: Pass 3's prompt is ~11k tokens but the
    old single-call design billed ~125k input, because the web-search loop resends
    context every round and nearly all of those repeats are cache hits.
    """
    rates = PRICING.get(model)
    if rates is None:
        # Report 0 rather than guessing. A pass suddenly costing $0.00 means a
        # model constant changed without a matching row in cost_tracker.PRICING.
        return 0.0
    return (
        (max(0, input_tokens) / 1_000_000) * rates.get("input", 0.0)
        + (max(0, cached_input_tokens) / 1_000_000) * rates.get("cache_read", 0.0)
        + (max(0, output_tokens) / 1_000_000) * rates.get("output", 0.0)
        + (max(0, thinking_tokens) / 1_000_000)
        * rates.get("thinking", rates.get("output", 0.0))
    )


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class LiteraryEchoesAgent:
    """Run the literary-echoes workflow for one psalm."""

    def __init__(
        self,
        cost_tracker: Optional[CostTracker] = None,
        db_path: str = "database/tanakh.db",
        logger=None,
        second_generator: bool = False,
        second_gen_model: str = SECOND_GEN_MODEL,
        verify_workers: int = VERIFY_WORKERS,
    ):
        self.cost_tracker = cost_tracker or CostTracker()
        self.db_path = db_path
        self.logger = logger or get_logger("literary_echoes_agent")
        self.second_generator = second_generator
        self.second_gen_model = second_gen_model
        self.verify_workers = max(1, verify_workers)
        self._gemini_client = None
        self._openai_client = None
        self._anthropic_client = None
        # Per-pass spend, including retried and failed calls. See `_record`.
        # Pass 3 mutates this from worker threads; += on a float under the GIL
        # is not atomic, so it is guarded.
        self._spend: Dict[str, float] = {}
        self._spend_lock = threading.Lock()
        self._templates: Dict[Path, str] = {}

    # ------------------------------------------------------------------ API

    def generate(
        self,
        psalm_number: int,
        psalm_output_dir: Path,
        skip_if_exists: bool = False,
    ) -> LiteraryEchoesResult:
        """Run the full workflow for one psalm.

        Default behaviour is regenerate-and-overwrite. Pass `skip_if_exists=True`
        to short-circuit when the canonical output already exists.
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
                overused_authors=[],
            )

        work_dir = Path(psalm_output_dir) / "literary_echoes"
        prompts_dir = work_dir / "prompts"
        work_dir.mkdir(parents=True, exist_ok=True)
        prompts_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"[lit_echoes] Starting workflow for Psalm {psalm_number}")
        notes: List[str] = []
        # Reset the per-pass ledger: one agent instance may generate several
        # psalms in a batch, and carrying spend forward would bill psalm N's
        # passes with psalm N-1's cost. (The shared CostTracker is cumulative on
        # purpose — that one is the run total.)
        with self._spend_lock:
            self._spend.clear()
        self._clear_legacy_artifacts(work_dir)

        # 1. Inputs + corpus-wide author ledger
        psalm_text = self._load_psalm_text(psalm_number)
        ledger = AuthorLedger.build(ECHOES_DATA_DIR, exclude_psalm=psalm_number)
        recent = ledger.recent(EXCLUSION_WINDOW)
        overused = ledger.overused(LIFETIME_BAN_AT, limit=LEDGER_PROMPT_LIMIT)
        ledger.save(LEDGER_PATH)
        (work_dir / "author_ledger.json").write_text(
            json.dumps(ledger.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        self._save_exclusion_list(work_dir, recent, overused, ledger)
        self.logger.info(
            f"[lit_echoes] Ledger: {len(ledger.authors)} authors across the corpus; "
            f"banning {len(recent)} recent + {len(overused)} overused (>= {LIFETIME_BAN_AT} psalms)"
        )

        # 2. Pass 1 — two independent generators, in parallel
        p1_prompt = self._build_pass_1_prompt(psalm_number, psalm_text, recent, overused)
        (prompts_dir / "pass_1a_full.txt").write_text(p1_prompt, encoding="utf-8")

        pass_results: List[PassResult] = []
        if self.second_generator:
            (prompts_dir / "pass_1b_full.txt").write_text(p1_prompt, encoding="utf-8")
            with ThreadPoolExecutor(max_workers=2) as pool:
                fut_gemini = pool.submit(self._call_gemini, p1_prompt, "pass_1a")
                fut_opus = pool.submit(self._call_opus, p1_prompt, "pass_1b")
                p1a = fut_gemini.result()
                try:
                    p1b = fut_opus.result()
                except Exception as exc:
                    # The second generator is an enhancement, not a dependency.
                    # Losing it degrades diversity; it must not fail the psalm.
                    self.logger.warning(f"[lit_echoes] pass_1b failed, continuing with Gemini only: {exc}")
                    notes.append(f"pass_1b ({self.second_gen_model}) failed: {exc}")
                    p1b = None
        else:
            p1a = self._call_gemini(p1_prompt, "pass_1a")
            p1b = None

        pass_results.append(p1a)
        (work_dir / "pass_1a_gemini.txt").write_text(p1a.output_text, encoding="utf-8")
        entries_a = parse_document(p1a.output_text, "pass_1_gemini", "A").entries

        entries_b: List[EchoEntry] = []
        if p1b is not None:
            pass_results.append(p1b)
            (work_dir / "pass_1b_opus.txt").write_text(p1b.output_text, encoding="utf-8")
            entries_b = parse_document(p1b.output_text, "pass_1_opus", "O").entries

        merged = merge_pass1_variants(entries_a, entries_b)
        merged_doc = reconstruct(merged)
        (work_dir / "pass_1_merged.md").write_text(merged_doc, encoding="utf-8")
        self.logger.info(
            f"[lit_echoes] Pass 1 merge: gemini={len(entries_a)} opus={len(entries_b)} "
            f"-> {len(merged)} entries "
            f"({sum(1 for e in merged if e.source == 'pass_1_gemini')} gemini / "
            f"{sum(1 for e in merged if e.source == 'pass_1_opus')} opus)"
        )
        if not merged:
            raise LiteraryEchoesGenerationError(
                f"Psalm {psalm_number}: Pass 1 produced no parseable entries"
            )

        # 3. Pass 2 — gap-fill against the merged document
        p2_prompt = self._build_pass_2_prompt(
            psalm_number, psalm_text, merged_doc, recent, overused
        )
        (prompts_dir / "pass_2_full.txt").write_text(p2_prompt, encoding="utf-8")
        p2 = self._call_gemini(p2_prompt, "pass_2")
        pass_results.append(p2)
        (work_dir / "pass_2_raw.txt").write_text(p2.output_text, encoding="utf-8")
        entries_2 = parse_document(p2.output_text, "pass_2", "B").entries

        # 4. Deterministic merge, replacement, de-duplication
        entries = list(merged) + list(entries_2)
        entries, malformed_notes = drop_malformed(entries)
        entries, replace_notes = apply_replacements(entries)
        entries, dupe_notes = dedupe_authors(entries)
        notes.extend(malformed_notes)
        notes.extend(replace_notes)
        notes.extend(dupe_notes)
        pre_verify = len(entries)
        self.logger.info(
            f"[lit_echoes] {pre_verify} entries to verify "
            f"(pass 2 added {len(entries_2)}; {len(replace_notes)} replaced, {len(dupe_notes)} de-duped)"
        )

        # 5. Pass 3 — one verification call per entry, fanned out
        (prompts_dir / "pass_3_sample.txt").write_text(
            self._build_pass_3_prompt(psalm_number, entries[0]) if entries else "",
            encoding="utf-8",
        )
        p3, verdicts = self._verify_entries(psalm_number, entries)
        pass_results.append(p3)
        (work_dir / "pass_3_verdicts.json").write_text(
            json.dumps(
                [
                    {
                        "entry_id": e.entry_id,
                        "author": e.author,
                        "source": e.source,
                        "verdict": verdicts[e.entry_id].verdict,
                        "reason": verdicts[e.entry_id].reason,
                    }
                    for e in entries
                ],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        # 6. Apply verdicts and rebuild — in Python, so it cannot stop early
        survivors: List[EchoEntry] = []
        rejected = corrected = 0
        for entry in entries:
            verdict = verdicts[entry.entry_id]
            if verdict.is_rejection:
                rejected += 1
                notes.append(f"{entry.entry_id} ({entry.author}) rejected: {verdict.reason}")
                continue
            if verdict.verdict == "corrected":
                corrected += 1
            survivors.append(apply_verdict(entry, verdict))

        final_text = reconstruct(survivors)
        if not final_text.strip():
            raise LiteraryEchoesGenerationError(
                f"Psalm {psalm_number}: every entry was rejected; refusing to write an empty file"
            )
        (work_dir / "final.md").write_text(final_text, encoding="utf-8")

        ECHOES_DATA_DIR.mkdir(parents=True, exist_ok=True)
        final_canonical.write_text(final_text, encoding="utf-8")
        self.logger.info(f"[lit_echoes] Canonical file written -> {final_canonical}")

        provenance: Dict[str, int] = {}
        for entry in survivors:
            provenance[entry.source] = provenance.get(entry.source, 0) + 1

        result = LiteraryEchoesResult(
            psalm_number=psalm_number,
            final_text=final_text,
            final_path=final_canonical,
            exclusion_authors=recent,
            overused_authors=overused,
            passes=pass_results,
            entry_stats={
                "pass_1_gemini": len(entries_a),
                "pass_1_opus": len(entries_b),
                "pass_1_merged": len(merged),
                "pass_2": len(entries_2),
                "verified_input": pre_verify,
                "rejected": rejected,
                "corrected": corrected,
                "final": len(survivors),
            },
            provenance=provenance,
            notes=notes,
        )
        (work_dir / "cost_report.json").write_text(
            json.dumps(result.to_cost_report(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        self.logger.info(
            f"[lit_echoes] Psalm {psalm_number} complete — {len(survivors)}/{pre_verify} entries kept "
            f"({rejected} rejected, {corrected} corrected), ${result.total_cost:.4f}"
        )
        return result

    # --------------------------------------------------------- Input loaders

    # Artifacts written by the pre-Session-374 pipeline. Re-running a psalm that
    # was built by the old code leaves these behind next to the new ones, and
    # `pass_4_final.txt` is the dangerous one: on Psalms 69-72 it holds a document
    # truncated mid-quotation, which reads exactly like a finished file. They are
    # regenerable pipeline output, not source data, so a re-run clears them.
    # `pass_2_raw.txt` is deliberately NOT here: the new pipeline writes that same
    # filename, so it is overwritten in the normal course of a run. Clearing it up
    # front would destroy the previous copy if a later pass then failed.
    _LEGACY_ARTIFACTS = (
        "pass_1_raw.txt",
        "pass_3_verification.txt",
        "pass_4_final.txt",
    )
    _LEGACY_DIRS = ("gemini_prompts",)

    def _clear_legacy_artifacts(self, work_dir: Path) -> None:
        removed = []
        for name in self._LEGACY_ARTIFACTS:
            path = work_dir / name
            if path.is_file():
                path.unlink()
                removed.append(name)
        for name in self._LEGACY_DIRS:
            path = work_dir / name
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
                removed.append(name + "/")
        if removed:
            self.logger.info(
                f"[lit_echoes] Cleared {len(removed)} stale pre-Session-374 artifact(s): "
                f"{', '.join(removed)}"
            )

    def _load_psalm_text(self, psalm_number: int) -> str:
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

    def _save_exclusion_list(
        self,
        work_dir: Path,
        recent: Sequence[str],
        overused: Sequence[str],
        ledger: AuthorLedger,
    ) -> None:
        lines = [
            "# Author exclusions for this literary echoes run",
            f"# Corpus ledger: {len(ledger.authors)} distinct authors across all rendered psalms",
            f"# Recent window: {EXCLUSION_WINDOW} most recently written files",
            f"# Lifetime ban threshold: used in >= {LIFETIME_BAN_AT} psalms",
            "",
            "## Banned — recently used",
            "",
        ]
        lines.extend(f"- {a}" for a in recent) if recent else lines.append("(none)")
        lines.extend(["", "## Banned — overused across the series", ""])
        if overused:
            lines.extend(f"- {a} ({ledger.count_for(a)} psalms)" for a in overused)
        else:
            lines.append("(none)")
        (work_dir / "exclusion_list.txt").write_text("\n".join(lines), encoding="utf-8")

    # --------------------------------------------------- Prompt construction

    def _load_template(self, path: Path) -> str:
        """Read a prompt template, cached for the life of the agent.

        Caching is not just about I/O: Pass 3 builds one prompt per entry from
        several threads, and re-reading the file each time would let an edit
        mid-run split a psalm across two prompt versions.
        """
        cached = self._templates.get(path)
        if cached is not None:
            return cached
        if not path.exists():
            raise FileNotFoundError(f"Prompt template missing: {path}")
        text = path.read_text(encoding="utf-8")
        self._templates[path] = text
        return text

    @staticmethod
    def _exclusion_block(recent: Sequence[str], overused: Sequence[str]) -> str:
        parts = []
        if recent:
            parts.append(
                "=== AUTHORS USED IN THE LAST FEW PSALMS (DO NOT REUSE) ===\n\n"
                "These authors appeared in the most recent psalms in this series. None of "
                "them may appear in this document — find fresher second-tier sources.\n\n"
                + ", ".join(recent)
                + "\n\n"
            )
        if overused:
            parts.append(
                "=== AUTHORS ALREADY OVERUSED ACROSS THIS SERIES (DO NOT REUSE) ===\n\n"
                "This guide covers all 150 psalms and the same major names keep resurfacing. "
                "Each author below has already been used in this series and is now closed. "
                "This applies even to Earned Canonical Slot authors: if one appears below, "
                "skip them and pick a different voice.\n\n"
                + ", ".join(overused)
                + "\n\n"
            )
        return "".join(parts)

    def _build_pass_1_prompt(
        self,
        psalm_number: int,
        psalm_text: str,
        recent: Sequence[str],
        overused: Sequence[str],
    ) -> str:
        template = self._load_template(PASS_1_PROMPT_FILE)
        template = template.replace("{NUMBER}", str(psalm_number))
        template = template.replace("[PSALM FULL TEXT]", psalm_text)
        block = self._exclusion_block(recent, overused)
        if block:
            anchor = "=== THE SECOND ECHO PRINCIPLE ==="
            if anchor not in template:
                # Fail loudly rather than silently dropping the ban list, which
                # would look like a diversity regression with no visible cause.
                raise ValueError(
                    f"Pass 1 template no longer contains the anchor {anchor!r}; "
                    "the exclusion block has nowhere to go."
                )
            template = template.replace(anchor, block + anchor, 1)
        return template

    def _build_pass_2_prompt(
        self,
        psalm_number: int,
        psalm_text: str,
        pass_1_document: str,
        recent: Sequence[str],
        overused: Sequence[str],
    ) -> str:
        template = self._load_template(PASS_2_PROMPT_FILE)
        template = template.replace("{NUMBER}", str(psalm_number))
        header = [
            f"PSALM {psalm_number} — LITERARY ECHOES (Pass 2 input)\n\n",
            f"[PSALM FULL TEXT]\n\n{psalm_text}\n\n",
            "[EXISTING LITERARY ECHOES DOCUMENT]\n\n",
            f"{pass_1_document}\n\n",
        ]
        block = self._exclusion_block(recent, overused)
        if block:
            header.append(block)
        header.extend(["---\n\n", "[PASS 2 INSTRUCTIONS]\n\n"])
        return "".join(header) + template

    def _build_pass_3_prompt(self, psalm_number: int, entry: EchoEntry) -> str:
        template = self._load_template(PASS_3_PROMPT_FILE)
        return (
            f"{template}\n\n"
            f"Psalm reference: {entry.cluster_heading}\n\n"
            f"#### {entry.heading}\n"
            f"{entry.quotation_block}\n\n"
            "Return the JSON object now."
        )

    # ----------------------------------------------------- Model invocations

    def _get_gemini_client(self):
        if self._gemini_client is None:
            try:
                from google import genai
            except ImportError:
                raise ImportError(
                    "google-genai required for literary echoes. pip install google-genai"
                )
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

    def _get_anthropic_client(self):
        if self._anthropic_client is None:
            import anthropic

            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set in environment")
            self._anthropic_client = anthropic.Anthropic(api_key=api_key)
        return self._anthropic_client

    @staticmethod
    def _looks_like_echoes(text: str) -> bool:
        """A generation pass must have produced at least one author block.

        This is the check whose absence let 3 of 26 runs ship a psalm with a whole
        pass missing. `response.text or ""` is not a validation.
        """
        return bool(text and re.search(r"^####[ \t]+\S", text, re.MULTILINE))

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
            if attempt > 0:
                wait = 2 * (2 ** (attempt - 1))
                self.logger.info(
                    f"[lit_echoes] {pass_name}: retry {attempt + 1}/{max_retries} after {wait}s"
                )
                time.sleep(wait)
            try:
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
            except Exception as e:
                last_err = e
                msg = str(e).lower()
                transient = any(
                    ind in msg
                    for ind in ["429", "rate limit", "too many", "try again", "503", "504"]
                )
                if transient and attempt < max_retries - 1:
                    continue
                raise

            output_text = response.text or ""
            usage = getattr(response, "usage_metadata", None)
            input_tokens = getattr(usage, "prompt_token_count", 0) or 0
            output_tokens = getattr(usage, "candidates_token_count", 0) or 0
            thinking_tokens = getattr(usage, "thoughts_token_count", 0) or 0

            # An empty or unparseable response still consumed tokens; bill it,
            # log why it was rejected, and try again rather than sailing on.
            self._record(pass_name, GEMINI_MODEL, input_tokens, output_tokens, thinking_tokens)
            if not self._looks_like_echoes(output_text):
                reason = self._finish_reason_gemini(response)
                last_err = LiteraryEchoesGenerationError(
                    f"{pass_name}: Gemini returned no author blocks "
                    f"({len(output_text)} chars, finish_reason={reason})"
                )
                self.logger.warning(f"[lit_echoes] {last_err}")
                continue

            elapsed = time.time() - start
            cost = self._spend.get(pass_name, 0.0)
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

        raise LiteraryEchoesGenerationError(
            f"{pass_name}: Gemini produced no usable output after {max_retries} attempts"
        ) from last_err

    @staticmethod
    def _finish_reason_gemini(response) -> str:
        try:
            return str(response.candidates[0].finish_reason)
        except Exception:
            return "unknown"

    def _call_opus(self, prompt: str, pass_name: str) -> PassResult:
        """Second Pass-1 generator on Claude, streamed.

        Streaming is not optional at this output size — a non-streaming request
        with a large `max_tokens` risks an HTTP timeout, and the SDK guards
        against it.
        """
        client = self._get_anthropic_client()
        self.logger.info(
            f"[lit_echoes] {pass_name}: {self.second_gen_model} "
            f"(adaptive thinking, prompt {len(prompt):,} chars)"
        )
        max_retries = 3
        start = time.time()
        last_err: Optional[Exception] = None

        for attempt in range(max_retries):
            if attempt > 0:
                wait = 5 * attempt
                self.logger.info(
                    f"[lit_echoes] {pass_name}: retry {attempt + 1}/{max_retries} after {wait}s"
                )
                time.sleep(wait)
            try:
                kwargs = {
                    "model": self.second_gen_model,
                    "max_tokens": SECOND_GEN_MAX_TOKENS,
                    "thinking": {"type": "adaptive"},
                    "output_config": {"effort": SECOND_GEN_EFFORT},
                    "messages": [{"role": "user", "content": prompt}],
                }
                text = ""
                with client.messages.stream(**kwargs) as stream:
                    for event in stream:
                        if getattr(event, "type", None) == "content_block_delta":
                            if hasattr(event.delta, "text"):
                                text += event.delta.text
                    final = stream.get_final_message()
                input_tokens = final.usage.input_tokens
                output_tokens = final.usage.output_tokens
                stop_reason = getattr(final, "stop_reason", None)
            except Exception as e:
                last_err = e
                self.logger.warning(f"[lit_echoes] {pass_name}: {type(e).__name__}: {e}")
                if not _is_transient(e):
                    # A deterministic rejection reproduces on every attempt. The
                    # first live run of this pass burned three attempts and ~5
                    # minutes on the same content-filter refusal before falling
                    # back — retrying bought nothing and billed the output twice.
                    self.logger.warning(
                        f"[lit_echoes] {pass_name}: error is not transient, not retrying"
                    )
                    raise
                if attempt < max_retries - 1:
                    continue
                raise

            # Anthropic bills thinking inside output_tokens, so it is not split out.
            self._record(pass_name, self.second_gen_model, input_tokens, output_tokens, 0)
            if not self._looks_like_echoes(text):
                last_err = LiteraryEchoesGenerationError(
                    f"{pass_name}: {self.second_gen_model} returned no author blocks "
                    f"({len(text)} chars, stop_reason={stop_reason})"
                )
                self.logger.warning(f"[lit_echoes] {last_err}")
                continue

            elapsed = time.time() - start
            cost = self._spend.get(pass_name, 0.0)
            self.logger.info(
                f"[lit_echoes] {pass_name}: done in {elapsed:.1f}s — "
                f"in={input_tokens:,} out={output_tokens:,} ${cost:.4f} (stop={stop_reason})"
            )
            return PassResult(
                pass_name=pass_name,
                model=self.second_gen_model,
                output_text=text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                elapsed_s=elapsed,
            )

        raise LiteraryEchoesGenerationError(
            f"{pass_name}: {self.second_gen_model} produced no usable output after {max_retries} attempts"
        ) from last_err

    # --------------------------------------------------- Pass 3: verification

    def _verify_entries(
        self, psalm_number: int, entries: Sequence[EchoEntry]
    ) -> Tuple[PassResult, Dict[str, Verdict]]:
        """Verify every entry independently, in parallel.

        The old single-call design sent the whole ~39k-char document and let the
        model budget its search effort across 18 quotations at once; it billed
        ~125k input tokens because each web-search round resends the accumulated
        context. Per entry, each call carries only its own quotation, the search
        loop is scoped to one source, and the pass parallelises.
        """
        start = time.time()
        verdicts: Dict[str, Verdict] = {}
        totals = {"input": 0, "output": 0, "thinking": 0, "cached": 0}
        self.logger.info(
            f"[lit_echoes] pass_3: verifying {len(entries)} entries with {GPT_VERIFY_MODEL} "
            f"({self.verify_workers} workers, web search on)"
        )

        def verify(entry: EchoEntry):
            prompt = self._build_pass_3_prompt(psalm_number, entry)
            return entry, self._call_openai_verify(prompt, entry.entry_id)

        with ThreadPoolExecutor(max_workers=self.verify_workers) as pool:
            futures = {pool.submit(verify, e): e for e in entries}
            for future in as_completed(futures):
                entry = futures[future]
                try:
                    _entry, (raw, usage) = future.result()
                except Exception as exc:
                    # Fail safe toward KEEPING the entry. This whole rewrite
                    # exists because content was being lost silently; a verifier
                    # outage must never delete a real echo.
                    self.logger.warning(
                        f"[lit_echoes] pass_3: {entry.entry_id} ({entry.author}) "
                        f"verification failed, keeping unverified: {exc}"
                    )
                    verdicts[entry.entry_id] = Verdict(
                        entry_id=entry.entry_id,
                        verdict="verified",
                        reason=f"verification call failed: {exc}",
                    )
                    continue
                for key in totals:
                    totals[key] += usage[key]
                verdicts[entry.entry_id] = parse_verdict(raw, entry.entry_id)

        for entry in entries:
            verdicts.setdefault(
                entry.entry_id,
                Verdict(entry_id=entry.entry_id, verdict="verified", reason="no verdict returned"),
            )

        elapsed = time.time() - start
        # From the ledger, not from `totals`: `totals` only accumulates calls that
        # returned, so a retried or failed verification would otherwise be billed
        # to the run but missing from this pass's line in the report.
        cost = self._spend.get("pass_3", 0.0)
        counts = {"verified": 0, "corrected": 0, "rejected": 0}
        for v in verdicts.values():
            counts[v.verdict] = counts.get(v.verdict, 0) + 1
        self.logger.info(
            f"[lit_echoes] pass_3: done in {elapsed:.1f}s — {counts['verified']} verified, "
            f"{counts['corrected']} corrected, {counts['rejected']} rejected; "
            f"in={totals['input']:,} (cached {totals['cached']:,}) out={totals['output']:,} ${cost:.4f}"
        )
        return (
            PassResult(
                pass_name="pass_3",
                model=GPT_VERIFY_MODEL,
                input_tokens=totals["input"],
                output_tokens=totals["output"],
                thinking_tokens=totals["thinking"],
                cached_input_tokens=totals["cached"],
                cost=cost,
                elapsed_s=elapsed,
                call_count=len(entries),
            ),
            verdicts,
        )

    def _call_openai_verify(self, prompt: str, tag: str) -> Tuple[str, Dict[str, int]]:
        client = self._get_openai_client()
        last_err: Optional[Exception] = None
        for attempt in range(VERIFY_RETRIES):
            if attempt > 0:
                time.sleep(2 * (2 ** (attempt - 1)))
            try:
                # `max_output_tokens` bounds reasoning AND the visible answer
                # together on the Responses API. The JSON verdict is ~200 tokens;
                # the rest is headroom for a multi-round web-search deliberation,
                # and unused headroom is free. Each retry doubles it, because the
                # commonest way this call fails is an `incomplete` status from a
                # search loop that ran longer than the budget allowed — retrying
                # at the same ceiling would just reproduce it.
                response = client.responses.create(
                    model=GPT_VERIFY_MODEL,
                    input=prompt,
                    reasoning={"effort": "medium"},
                    tools=[{"type": "web_search_preview"}],
                    max_output_tokens=VERIFY_MAX_OUTPUT_TOKENS * (2 ** attempt),
                )
            except Exception as e:
                last_err = e
                if attempt < VERIFY_RETRIES - 1:
                    continue
                raise

            # OpenAI folds reasoning into output_tokens and cached into
            # input_tokens; both are split out here so nothing is billed twice.
            usage = response.usage
            visible_output, reasoning = split_output_tokens(usage)
            in_details = getattr(usage, "input_tokens_details", None)
            cached = (getattr(in_details, "cached_tokens", 0) or 0) if in_details else 0
            raw_input = getattr(usage, "input_tokens", 0) or 0
            stats = {
                "input": max(0, raw_input - cached),
                "output": visible_output,
                "thinking": reasoning,
                "cached": cached,
            }
            self._record(
                "pass_3",
                GPT_VERIFY_MODEL,
                stats["input"],
                stats["output"],
                stats["thinking"],
                stats["cached"],
            )

            text = response.output_text or ""
            status = getattr(response, "status", None)
            if not text.strip() or status == "incomplete":
                last_err = LiteraryEchoesGenerationError(
                    f"{tag}: empty or incomplete verifier response (status={status})"
                )
                if attempt < VERIFY_RETRIES - 1:
                    continue
                raise last_err
            return text, stats

        raise last_err or LiteraryEchoesGenerationError(f"{tag}: verification exhausted retries")

    # ------------------------------------------------------------- Bookkeeping

    def _record(
        self,
        pass_name: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        thinking_tokens: int,
        cached_tokens: int = 0,
    ) -> None:
        """Bill one API call to both the shared tracker and this pass's ledger.

        Arguments follow `price_call`'s disjoint contract, so the run total and
        this module's per-pass report agree.

        The ledger is why every billable call routes through here: a pass that
        retried twice before succeeding, or one whose verification call failed
        outright, still consumed tokens. Computing `PassResult.cost` from the
        successful response alone would under-report exactly the runs that went
        wrong — the ones worth noticing.
        """
        cost = price_call(model, input_tokens, output_tokens, thinking_tokens, cached_tokens)
        with self._spend_lock:
            # CostTracker is not thread-safe either — its read-modify-write of
            # usage_by_model runs under this same lock so Pass 3's workers cannot
            # lose an update.
            self.cost_tracker.add_usage(
                model=model,
                input_tokens=max(0, input_tokens),
                output_tokens=max(0, output_tokens),
                thinking_tokens=max(0, thinking_tokens),
                cache_read_tokens=max(0, cached_tokens),
            )
            self._spend[pass_name] = self._spend.get(pass_name, 0.0) + cost


__all__ = [
    "LiteraryEchoesAgent",
    "LiteraryEchoesGenerationError",
    "LiteraryEchoesResult",
    "PassResult",
    "price_call",
]
