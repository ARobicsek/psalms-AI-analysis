"""
EXPERIMENT (Session 367): does gpt-5.6-terra do Hebrew close reading as well as
claude-sonnet-4-6 on the Micro Analyst's Stage 1 discovery pass?

Why a probe and not a port: micro_analyst.py is Anthropic-only (two
`self.client.messages.stream()` call sites, no OpenAI branch). Building that
branch is real work — streaming, effort mapping, the 65K-with-retry-scaling
loop, JSON repair, across two stages. This script answers the only question
that justifies that work, for well under a dollar, touching no production code.

It rebuilds the EXACT Stage 1 prompt the production agent sends (same
DISCOVERY_PASS_PROMPT, same macro markdown, same LXX-formatted psalm text, same
RAG context) and sends it to Terra instead, then diffs the parsed result against
the Sonnet output already on disk.

Config note — the two providers cannot be made identical here:
  Sonnet 4.6 (production): thinking={"type":"enabled","budget_tokens":32768}
                           + output_config={"effort":"max"}
  Terra (this probe):      reasoning_effort="xhigh"   (Terra rejects "max")
There is no GPT equivalent of the hard 32K thinking cap that the Session-294 fix
introduced to stop thinking from eating the whole token budget. On GPT, reasoning
counts against max_completion_tokens with no separate knob — so budget exhaustion
is a live risk for a port, and this probe is also a test of that.

Usage:
    python scripts/EXPERIMENT_micro_terra_probe.py 69
    python scripts/EXPERIMENT_micro_terra_probe.py 69 --effort high

Archive after the session (see CLAUDE.md File Organization Rules).
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from src.agents.micro_analyst import MicroAnalystV2, DISCOVERY_PASS_PROMPT
from src.schemas.analysis_schemas import load_macro_analysis
from src.utils.cost_tracker import CostTracker
from src.utils.openai_usage import split_output_tokens

PROBE_MODEL = "gpt-5.6-terra"


def build_stage1_prompt(agent: MicroAnalystV2, psalm_number: int, macro_analysis) -> str:
    """Reproduce _stage1_discovery_pass's prompt assembly exactly."""
    psalm = agent.db.get_psalm(psalm_number)
    if not psalm:
        raise ValueError(f"Psalm {psalm_number} not found in database")
    rag_context = agent.rag_manager.get_rag_context(psalm_number)
    psalm_text_with_lxx = agent._format_psalm_with_lxx(psalm, rag_context)
    rag_formatted = agent.rag_manager.format_for_prompt(rag_context, include_framework=False)

    prompt = DISCOVERY_PASS_PROMPT
    prompt = prompt.replace('{psalm_number}', str(psalm_number))
    prompt = prompt.replace('{macro_analysis}', macro_analysis.to_markdown(include_working_notes=False))
    prompt = prompt.replace('{psalm_text_with_phonetics}', psalm_text_with_lxx)
    prompt = prompt.replace('{rag_context}', rag_formatted)
    prompt = prompt.replace('{verse_count}', str(len(psalm.verses)))
    return prompt


def extract_json(text: str) -> dict:
    """Same tolerance the production parser needs: fenced block, or first {...}."""
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            text = text[start:end + 1]
    return json.loads(text)


def summarize(payload: dict, label: str) -> dict:
    """Schema-agnostic so raw Stage 1 output and the saved baseline compare fairly.

    DISCOVERY_PASS_PROMPT asks the model for `verse_discoveries` with fields
    `observations` / `figurative_elements`. _create_micro_analysis() then RENAMES
    those into `verse_commentaries` / `commentary` / `figurative_analysis` before
    micro_v2.json is written. A probe that reads only the post-processed names
    scores raw model output as zero across the board — which says nothing about
    the model. Accept both vocabularies.
    """
    vc = payload.get("verse_commentaries") or payload.get("verse_discoveries") or []
    lex = sum(len(v.get("lexical_insights") or []) for v in vc)
    fig = sum(len(v.get("figurative_analysis") or v.get("figurative_elements") or [])
              for v in vc)
    commentary_chars = sum(len(v.get("commentary") or v.get("observations") or "")
                           for v in vc)
    thesis = sum(1 for v in vc if (v.get("thesis_connection") or "").strip())
    lex_chars = sum(len(json.dumps(v.get("lexical_insights") or [], ensure_ascii=False))
                    for v in vc)
    # NOTE: phonetic_transcription is deliberately NOT compared. It is injected by
    # the deterministic PhoneticAnalyst in _create_micro_analysis(), not produced
    # by the model, so the baseline has it on every verse and any raw model output
    # has it on none. Counting it would penalise the probe for something the model
    # was never asked to do.
    hebrew = sum(1 for v in vc
                 if re.search(r"[֐-׿]", json.dumps(v, ensure_ascii=False)))
    return {
        "label": label,
        "verses": len(vc),
        "lexical_insights": lex,
        "figurative_analyses": fig,
        "interesting_questions": len(payload.get("interesting_questions") or []),
        "thematic_threads": len(payload.get("thematic_threads") or []),
        "commentary_chars": commentary_chars,
        "chars_per_verse": round(commentary_chars / len(vc)) if vc else 0,
        "lexical_detail_chars": lex_chars,
        "chars_per_lex_insight": round(lex_chars / lex) if lex else 0,
        "verses_with_thesis_link": thesis,
        "verses_containing_hebrew": hebrew,
    }


def main() -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("psalm", type=int)
    ap.add_argument("--effort", default="xhigh",
                    choices=["low", "medium", "high", "xhigh"],
                    help="Terra reasoning_effort ('max' is rejected by the API)")
    ap.add_argument("--max-tokens", type=int, default=65536,
                    help="Mirrors the production Stage 1 budget")
    # MicroAnalystV2's own default is "data/tanakh.db", which is a 69KB STUB.
    # The pipeline always overrides it with database/tanakh.db (86MB, 312K rows);
    # using the class default silently yields "Psalm N not found in database".
    ap.add_argument("--db-path", default="database/tanakh.db",
                    help="Real Tanakh DB (default matches run_enhanced_pipeline.py)")
    args = ap.parse_args()
    pn = args.psalm

    out_dir = ROOT / "output" / f"psalm_{pn}"
    baseline_file = out_dir / f"psalm_{pn:03d}_micro_v2.json"
    macro_file = out_dir / f"psalm_{pn:03d}_macro.json"
    for f in (baseline_file, macro_file):
        if not f.exists():
            print(f"ERROR: missing {f.relative_to(ROOT)}", file=sys.stderr)
            return 1

    probe_dir = out_dir / "_micro_probe"
    probe_dir.mkdir(parents=True, exist_ok=True)

    agent = MicroAnalystV2(db_path=args.db_path)
    macro_analysis = load_macro_analysis(macro_file)
    prompt = build_stage1_prompt(agent, pn, macro_analysis)
    (probe_dir / "stage1_prompt.txt").write_text(prompt, encoding="utf-8")
    print(f"Stage 1 prompt rebuilt: {len(prompt):,} chars")

    from openai import OpenAI
    client = OpenAI()
    print(f"Calling {PROBE_MODEL} (reasoning_effort={args.effort}, "
          f"max_completion_tokens={args.max_tokens:,})...")
    t0 = time.time()
    resp = client.chat.completions.create(
        model=PROBE_MODEL,
        reasoning_effort=args.effort,
        max_completion_tokens=args.max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    elapsed = time.time() - t0

    text = resp.choices[0].message.content or ""
    (probe_dir / "terra_raw_response.txt").write_text(text, encoding="utf-8")

    visible_out, reasoning = split_output_tokens(resp.usage)
    tracker = CostTracker()
    tracker.add_usage(PROBE_MODEL, input_tokens=resp.usage.prompt_tokens,
                      output_tokens=visible_out, thinking_tokens=reasoning)
    cost = tracker.get_total_cost()
    finish = resp.choices[0].finish_reason

    print(f"  {elapsed:.0f}s | in={resp.usage.prompt_tokens:,} "
          f"out={resp.usage.completion_tokens:,} (reasoning={reasoning:,}) "
          f"| ${cost:.4f} | finish_reason={finish}")
    if finish == "length":
        print("  !! TRUNCATED — reasoning consumed the budget. This is exactly the "
              "failure the Session-294 budget_tokens cap prevents on Anthropic, and "
              "GPT has no equivalent knob. Strong signal against a port as-is.")

    try:
        probe = extract_json(text)
    except Exception as e:
        print(f"  !! JSON parse FAILED: {e}")
        print(f"  raw response saved to {(probe_dir / 'terra_raw_response.txt').relative_to(ROOT)}")
        print("  (production micro has repair/retry logic this probe deliberately omits,")
        print("   so a parse failure here is informative but not automatically fatal.)")
        return 1

    (probe_dir / f"psalm_{pn:03d}_micro_terra.json").write_text(
        json.dumps(probe, ensure_ascii=False, indent=2), encoding="utf-8")

    baseline = json.loads(baseline_file.read_text(encoding="utf-8"))
    a = summarize(baseline, f"sonnet-4-6 (production)")
    b = summarize(probe, f"{PROBE_MODEL} @ {args.effort}")

    keys = [k for k in a if k != "label"]
    w = max(len(k) for k in keys)
    print(f"\n{'metric'.ljust(w)} | {a['label']:>24} | {b['label']:>24} | delta")
    print("-" * (w + 60))
    for k in keys:
        av, bv = a[k], b[k]
        d = f"{bv - av:+d}" if isinstance(av, int) else ""
        print(f"{k.ljust(w)} | {av:>24,} | {bv:>24,} | {d}")

    print(f"\nCost: Terra Stage 1 ${cost:.4f}. Sonnet's FULL micro (both stages) on "
          f"Ps {pn} is in {baseline_file.name}'s run — compare stage-1-only figures "
          f"with care.")
    print(f"\nArtifacts -> {probe_dir.relative_to(ROOT)}")
    print("Numbers are a screen, not a verdict: read terra_raw_response.txt against "
          f"{baseline_file.name} for Hebrew accuracy, root analysis, and whether the "
          "insights are actually worth having.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
