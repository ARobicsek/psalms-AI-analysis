"""
Throwaway (Session 359): re-run ONLY the master-editor writer stage for a psalm
on its existing upstream inputs, using the CURRENT (edited) MASTER_WRITER_PROMPT_V4.

Usage: python scratch/compare_writer.py <psalm_number>

Writes new writer output to output/psalm_<N>/_writer_compare_new/ so production
files are never touched. Compare against the pristine old writer output:
    output/psalm_<N>/psalm_<NNN>_edited_intro_pre_copy_edit.md
    output/psalm_<N>/psalm_<NNN>_edited_verses_pre_copy_edit.md

Archive after the session.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from src.agents.master_editor import MasterEditor
from src.utils.cost_tracker import CostTracker

PN = int(sys.argv[1]) if len(sys.argv) > 1 else 62
out = ROOT / "output" / f"psalm_{PN}"
compare_dir = out / "_writer_compare_new"
compare_dir.mkdir(parents=True, exist_ok=True)

macro_file = out / f"psalm_{PN:03d}_macro.json"
micro_file = out / f"psalm_{PN:03d}_micro_v2.json"
research_file = out / f"psalm_{PN:03d}_research_v2.md"
synthesis_discovery_file = out / f"psalm_{PN:03d}_synthesis_discovery.md"

for f in (macro_file, micro_file, research_file, synthesis_discovery_file):
    assert f.exists(), f"missing input: {f}"

tracker = CostTracker()
editor = MasterEditor(main_model="claude-opus-4-8", cost_tracker=tracker)
print(f"[compare] psalm={PN} model={editor.model}")

result = editor.write_commentary(
    macro_file=macro_file,
    micro_file=micro_file,
    research_file=research_file,
    insights_file=None,                 # production run had no insights file
    psalm_number=PN,
    reader_questions_file=None,          # no reader-questions file present
    suppress_questions=False,
    synthesis_discovery_file=synthesis_discovery_file,
)

(compare_dir / f"psalm_{PN:03d}_edited_intro_NEW.md").write_text(result["introduction"], encoding="utf-8")
(compare_dir / f"psalm_{PN:03d}_edited_verses_NEW.md").write_text(result["verse_commentary"], encoding="utf-8")

print(f"[compare] intro words={len(result['introduction'].split())}  verses words={len(result['verse_commentary'].split())}")
try:
    print(f"[compare] total cost=${tracker.get_total_cost():.4f}")
except Exception as e:
    print(f"[compare] cost unavailable: {e}")
print(f"[compare] wrote -> {compare_dir}")
