"""Session 377: per-psalm location for captured model reasoning.

The two things worth pinning down are the ones a call site would otherwise have to
remember on its own: the directory is unpadded while the files inside it are
zero-padded, and an already-existing padded directory must win over the current
convention rather than gaining a silent duplicate.
"""

import pytest

import src.utils.debug_paths as dp


@pytest.fixture
def fake_output_root(tmp_path, monkeypatch):
    monkeypatch.setattr(dp, "OUTPUT_ROOT", tmp_path)
    return tmp_path


def test_new_psalm_uses_the_unpadded_directory(fake_output_root):
    assert dp.psalm_output_dir(73) == fake_output_root / "psalm_73"


def test_existing_padded_directory_wins(fake_output_root):
    """A psalm built under the older convention keeps its directory instead of
    growing a second one next to it."""
    (fake_output_root / "psalm_073").mkdir()
    assert dp.psalm_output_dir(73) == fake_output_root / "psalm_073"


def test_existing_unpadded_directory_wins_over_padded(fake_output_root):
    (fake_output_root / "psalm_73").mkdir()
    (fake_output_root / "psalm_073").mkdir()
    assert dp.psalm_output_dir(73) == fake_output_root / "psalm_73"


def test_filename_is_padded_even_though_the_directory_is_not(fake_output_root):
    path = dp.thinking_file(9, "master_writer_v4")
    assert path.parent.name == "psalm_9"
    assert path.name == "psalm_009_master_writer_v4_thinking.txt"


def test_agents_do_not_collide(fake_output_root):
    """Every writer variant and the copy editor get distinct files, so an SI or
    college run cannot overwrite the production writer's capture."""
    names = {
        dp.thinking_file(73, prefix).name
        for prefix in ("master_writer_v4", "college_writer", "copy_editor")
    }
    assert len(names) == 3


def test_directory_is_created_on_demand(fake_output_root):
    assert not (fake_output_root / "psalm_150").exists()
    dp.thinking_file(150, "master_writer_v4")
    assert (fake_output_root / "psalm_150").is_dir()


def test_lookup_can_be_side_effect_free(fake_output_root):
    dp.thinking_file(150, "master_writer_v4", create_dir=False)
    assert not (fake_output_root / "psalm_150").exists()
