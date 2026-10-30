"""design/yt_channels.py finds ff-jarvis beside any checkout, so a Linux runner compares the table too (2026-10-30).

Before this the path was the PC's own, and tests/test_yt_channels.py skipped on every clone elsewhere.
"""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("yt_channels_path", ROOT / "design" / "yt_channels.py")
yt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(yt)


def checkout(parent):
    (parent / "ff-jarvis" / "model" / "clients").mkdir(parents=True)
    return parent / "ff-jarvis"


def test_a_clone_finds_ff_jarvis_beside_it(tmp_path):
    ffj = checkout(tmp_path)
    assert yt.find_ff_jarvis(tmp_path / "team-watch") == ffj


def test_a_worktree_finds_ff_jarvis_beside_its_main_checkout(tmp_path):
    ffj = checkout(tmp_path)
    assert yt.find_ff_jarvis(tmp_path / "team-watch" / ".claude" / "worktrees" / "x") == ffj


def test_a_checkout_with_no_sibling_keeps_the_pc_path(tmp_path):
    assert yt.find_ff_jarvis(tmp_path / "team-watch") == yt.PC_FF_JARVIS
