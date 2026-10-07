"""sources.ff_jarvis_behind: the guard scripts/land.ps1 uses to refuse a build from an ff-jarvis checkout
behind its origin/main (2026-09-29, the 2018 Records lineups). Throwaway repos with the commit hook
switched off (the global one refuses a commit on main and costs a shell start per commit): a seed repo
the checkout clones, so its origin/main is the seed's main. Six git calls, down from fifteen."""
import os
import pathlib
import subprocess
import sys

import pytest

from conftest import REPO

sys.path.insert(0, str(REPO / "design"))
import sources  # noqa: E402

pytestmark = pytest.mark.integration      # real git repos

ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
       "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.hooksPath", "GIT_CONFIG_VALUE_0": "no-hooks-here"}


def run(cwd, *a):
    subprocess.run(["git", *a], cwd=cwd, env=ENV, capture_output=True, text=True, check=True)


def commit(repo, name):
    run(repo, "commit", "--allow-empty", "-m", name)


def test_it_counts_the_commits_the_checkout_lacks(tmp_path, monkeypatch):
    seed, ffj = tmp_path / "seed", tmp_path / "ff-jarvis"
    run(tmp_path, "init", "-b", "main", str(seed))
    commit(seed, "a")
    run(tmp_path, "clone", str(seed), str(ffj))
    (ffj / "data").mkdir()
    monkeypatch.setattr(sources, "DWR", ffj / "data")
    assert sources.ff_jarvis_behind() == 0
    commit(seed, "b")
    commit(seed, "c")
    assert sources.ff_jarvis_behind() == 0          # nothing fetched yet: it reads the last fetch
    run(ffj, "fetch", "origin")
    assert sources.ff_jarvis_behind() == 2


def test_the_jobs_data_path_is_ff_jarvis_own():
    """One path in two repos: ff-jarvis's model.JOBS_DATA is the source, this test holds the copy to it."""
    import importlib.util
    import pytest
    # ff-jarvis sits beside team-watch's main checkout, which is an ancestor of a .claude/worktrees one.
    init = next((p / "ff-jarvis" / "model" / "__init__.py" for p in REPO.parents
                 if (p / "ff-jarvis" / "model" / "__init__.py").exists()), None)
    if init is None:
        pytest.skip("ff-jarvis is not checked out beside team-watch")
    spec = importlib.util.spec_from_file_location("ffj_model", init)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "JOBS_DATA"):
        pytest.skip("this ff-jarvis checkout predates fix 3")
    assert sources.JOBS_DATA == pathlib.Path(mod.JOBS_DATA)


def test_data_outside_a_checkout_is_none(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, "DWR", tmp_path / "data")
    assert sources.ff_jarvis_behind() is None
