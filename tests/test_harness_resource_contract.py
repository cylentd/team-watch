import os
import subprocess

import psutil
import pytest
import xdist.plugin

import conftest


@pytest.mark.parametrize("cpu_count,requested,expected", [(1, "auto", 2), (64, "auto", 2),
                                                       (64, "logical", 2), (64, "5", 5), (64, "0", 0)])
def test_automatic_worker_budget_and_explicit_overrides(cpu_count, requested, expected, monkeypatch, tmp_path):
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.delenv("PYTEST_XDIST_AUTO_NUM_WORKERS", raising=False)
    monkeypatch.setattr(os, "cpu_count", lambda: cpu_count)
    monkeypatch.setattr(psutil, "cpu_count", lambda **kwargs: cpu_count)
    config = pytest.Config.fromdictargs({}, ["-p", "xdist.plugin", "--rootdir", str(tmp_path),
                                           "--confcutdir", str(tmp_path), str(tmp_path), "-n", requested])
    try:
        config.pluginmanager.register(conftest, "team_watch_harness")
        xdist.plugin.pytest_cmdline_main(config)
        assert config.option.numprocesses == expected
    finally:
        config._ensure_unconfigure()


@pytest.mark.integration
@pytest.mark.parametrize("path,expected", [("showcase/madden-curse/edition.json", "ours"),
                                         ("design/build.py", "unspecified"),
                                         ("design/src/shell.html", "unspecified")])
def test_only_generated_output_is_allowed_by_the_rebuild_attribute_contract(path, expected):
    result = subprocess.run(
        ["git", "check-attr", "merge", "--", path],
        cwd=conftest.REPO, capture_output=True, text=True, check=True, timeout=10,
    )
    assert result.stdout.strip() == f"{path}: merge: {expected}"
