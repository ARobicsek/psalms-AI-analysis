"""Session 388 experiment: synthesis discovery in the DOSSIER-FIRST layout with the dossier cache
shared with the writer, on a finished psalm, written to output/psalm_N/_s388_sd_shared/ so the
psalm's own observations file is untouched. Then a max_tokens=0 probe sends the writer's real
first turn (built as _call_forest_writer builds it, with the NEW observations) to show that the
writer would READ the dossier head instead of writing it. The writer itself is not run.

    python scripts/EXPERIMENT_s388_shared_cache.py 77
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from src.agents import forest_writer as fw  # noqa: E402
from src.agents.master_editor import MASTER_WRITER_PROMPT_V4, MasterEditor  # noqa: E402
from src.utils.cost_tracker import CostTracker  # noqa: E402
from src.utils.model_effort import adaptive_thinking, apply_effort  # noqa: E402


def main() -> int:
    ps = int(sys.argv[1]) if len(sys.argv) > 1 else 77
    model = "claude-opus-5-5"
    d = Path(f"output/psalm_{ps}")
    out = d / "_s388_sd_shared"
    out.mkdir(exist_ok=True)
    tracker = CostTracker()
    ed = MasterEditor(main_model=model, cost_tracker=tracker, writer_mode="forest")

    t0 = time.time()
    sd_file = ed.discover_cross_verse_observations(
        macro_file=d / f"psalm_{ps:03d}_macro.json", micro_file=d / f"psalm_{ps:03d}_micro_v2.json",
        research_file=d / f"psalm_{ps:03d}_research_v2.md", psalm_number=ps, output_path=out,
        skip_if_exists=False, model=model, share_cache_with_writer=True)
    sd_seconds = round(time.time() - t0)
    sd_cost = tracker.get_total_cost()
    sd_usage = tracker.to_dict().get(model)

    # The writer's first turn, as _perform_writer_synthesis + _call_forest_writer build it.
    macro = ed._load_json_file(d / f"psalm_{ps:03d}_macro.json")
    micro = ed._load_json_file(d / f"psalm_{ps:03d}_micro_v2.json")
    bundle, _, _ = ed.research_trimmer.trim_bundle(ed._load_text_file(d / f"psalm_{ps:03d}_research_v2.md"),
                                                  max_chars=350000)
    prompt = MASTER_WRITER_PROMPT_V4.format(
        psalm_number=ps, psalm_text=ed._get_psalm_text(ps, micro),
        macro_analysis=ed._format_analysis_for_prompt(macro, "macro"),
        micro_analysis=ed._format_analysis_for_prompt(micro, "micro"), research_bundle=bundle,
        phonetic_section=ed._format_phonetic_section(micro),
        curated_insights=ed._format_insights_for_prompt(None), reader_questions="[No reader questions provided]")
    ed._cross_verse_observations = Path(sd_file).read_text(encoding="utf-8")
    prompt = ed._splice_cross_verse_observations(prompt)
    prompt = prompt.replace("### READER QUESTIONS (initial questions)\n[No reader questions provided]\n", "")
    inputs = fw.extract_inputs_block(prompt)
    turn1 = fw.first_turn(inputs, fw.essay_instructions(ps, inputs))
    kw = {"model": model, "max_tokens": 0, "thinking": adaptive_thinking(model),
          "messages": [{"role": "user", "content": turn1}]}
    apply_effort(kw, model)
    probe_gap = round(time.time() - t0 - sd_seconds)
    u = ed.anthropic_client.messages.create(**kw).usage
    tracker.add_usage(model, input_tokens=u.input_tokens, output_tokens=u.output_tokens,
                      cache_read_tokens=u.cache_read_input_tokens or 0,
                      cache_write_tokens=u.cache_creation_input_tokens or 0)
    summary = {
        "psalm": ps, "sd_seconds": sd_seconds, "sd_cost_usd": round(sd_cost, 4), "sd_usage": sd_usage,
        "writer_probe": {"seconds_after_sd": probe_gap, "input": u.input_tokens,
                         "cache_read": u.cache_read_input_tokens, "cache_write": u.cache_creation_input_tokens},
        "total_cost_usd": round(tracker.get_total_cost(), 4),
        "observations_file": str(sd_file),
    }
    (out / "run_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
