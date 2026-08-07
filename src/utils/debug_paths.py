"""Where per-psalm debug artifacts live.

Session 377. The reasoning captures used to be written to a single flat
`output/debug/` directory shared by every psalm, so the artifacts belonging to one
psalm were scattered across two places: its own `output/psalm_NNN/` folder for
everything the pipeline produces, and `output/debug/` for the thinking. Reading
what the writer weighed on a psalm meant knowing that second convention existed.

Two naming facts this module exists to hide, because both call sites would
otherwise have to get them right independently:

  * The DIRECTORY is unpadded (`output/psalm_73`) but the FILES inside it are
    zero-padded to three digits (`psalm_073_macro.json`). That is the established
    convention, not a bug, and it is easy to get backwards.
  * Some older psalm directories are padded (`output/psalm_073`). Both forms exist
    on disk, which is why `check_lxx_density.py` and `converse_with_editor.py` each
    probe for both. An existing directory always wins; only when neither exists do
    we create the unpadded form, matching `copy_editor.py` and `beta_reader.py`.
"""

from pathlib import Path

OUTPUT_ROOT = Path("output")


def psalm_output_dir(psalm_number: int, create: bool = False) -> Path:
    """The psalm's output directory, preferring whichever form already exists.

    Never guesses when the answer is on disk: a psalm built before the unpadded
    convention keeps its padded directory instead of silently gaining a second one.
    """
    unpadded = OUTPUT_ROOT / f"psalm_{psalm_number}"
    padded = OUTPUT_ROOT / f"psalm_{psalm_number:03d}"

    if unpadded.is_dir():
        chosen = unpadded
    elif padded.is_dir():
        chosen = padded
    else:
        chosen = unpadded  # new psalm: the current convention

    if create:
        chosen.mkdir(parents=True, exist_ok=True)
    return chosen


def thinking_file(psalm_number: int, agent_prefix: str, create_dir: bool = True) -> Path:
    """Path for one agent's captured reasoning on one psalm.

    `agent_prefix` keeps the writer variants apart (`master_writer_v4`,
    `college_writer`, `copy_editor`), so an SI or college run cannot overwrite the
    production writer's capture.
    """
    directory = psalm_output_dir(psalm_number, create=create_dir)
    return directory / f"psalm_{psalm_number:03d}_{agent_prefix}_thinking.txt"


__all__ = ["OUTPUT_ROOT", "psalm_output_dir", "thinking_file"]
