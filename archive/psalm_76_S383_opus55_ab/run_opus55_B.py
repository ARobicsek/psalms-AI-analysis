"""Session 383: Ps 76 arm B -- every Opus stage on claude-opus-5-5 (effort=high).

Arm A is the production run of 2026-09-17 in output/psalm_76/:
    macro              claude-opus-4-8   (effort high)
    synthesis disc.    claude-opus-4-8   (effort high)
    master writer      claude-opus-5     (effort high)

Arm B swaps all three to claude-opus-5-5 and re-runs ONLY what depends on them:
    macro -> micro + research bundle (micro consumes the macro) -> synthesis
    discovery -> writer -> print-ready / citation filter -> copy editor -> DOCX.
Literary echoes is SKIPPED: it depends on nothing upstream, and its step overwrites
the canonical data/literary_echoes/psalm_076_literary_echoes.txt, so B reads A's.

Isolation: --output-dir alone is not enough. debug_paths.thinking_file() always
resolves to output/psalm_76/, so the writer and copy-editor thinking captures would
overwrite arm A's. We patch debug_paths.psalm_output_dir (looked up at call time by
thinking_file) to point at B. The output/debug/*_psalm_76.txt single slots are
backed up before and restored after by the caller.
"""
import os
import sys
from pathlib import Path

REPO = Path(r"C:\dev\personal\psalms")
os.chdir(REPO)
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

B_DIR = REPO / "output" / "psalm_76" / "_opus55_B"
B_DIR.mkdir(parents=True, exist_ok=True)

from src.utils import debug_paths  # noqa: E402


def _b_dir(psalm_number, create=False):
    B_DIR.mkdir(parents=True, exist_ok=True)
    return B_DIR


debug_paths.psalm_output_dir = _b_dir
assert debug_paths.thinking_file(76, "master_writer_v4").parent == B_DIR

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from run_enhanced_pipeline import run_enhanced_pipeline  # noqa: E402
from src.agents.copy_editor import CopyEditor  # noqa: E402

MODEL = "claude-opus-5-5"

run_enhanced_pipeline(
    psalm_number=76,
    output_dir=str(B_DIR),
    db_path="database/tanakh.db",
    delay_between_steps=30,
    skip_lit_echoes=True,
    macro_model=MODEL,
    synthesis_discovery=True,
    synthesis_discovery_model=MODEL,
    master_editor_model=MODEL,
    # everything else exactly as main() resolves it for a plain run
    skip_questions=True,
    exclude_questions=False,
    question_model="gpt-5.6-terra",
    copy_model=CopyEditor.DEFAULT_MODEL,
    skip_beta_reader=True,
)
