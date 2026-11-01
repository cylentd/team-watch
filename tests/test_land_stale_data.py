"""S3: scripts/land.ps1 refuses a build from an ff-jarvis checkout behind origin unless -AllowStaleData.
The real land.ps1 runs in a throwaway repo (its own copy beside its own origin), with a fake `python` first
on PATH that answers `design/sources.py --fetch` with a chosen count and fails at `design/build.py`. So the
run stops right after the guard: nothing is rebased, folded, landed or pushed, and the real checkout is never
read. `Write-Host` is replaced so each message arrives with its colour. land.ps1 is a Windows script, so a
machine without PowerShell fails `land` loudly (CI is windows-latest) instead of skipping."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
PS = shutil.which("powershell") or shutil.which("pwsh")
pytestmark = pytest.mark.integration      # PowerShell processes and git

FAKE_FFJ = "C:/fake/ff-jarvis"
BUILD_REACHED = "FAKE-BUILD-REACHED"
STUB = f'''import os, sys
a = sys.argv[1:]
if any(x.endswith("sources.py") for x in a):
    print(os.environ["FAKE_BEHIND"] + " {FAKE_FFJ}")
elif any(x.endswith("build.py") for x in a):
    print("{BUILD_REACHED}")
    sys.exit(1)
'''
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
           "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.hooksPath", "GIT_CONFIG_VALUE_0": "no-hooks-here"}
# Colour and text of every Write-Host, and the message of the throw that ends the run.
WRAP = ("function Write-Host { param($Object, $ForegroundColor) Write-Output \"$ForegroundColor|$Object\" }; "
        "try { & '%s' -Yes -NoPostland %s } catch { Write-Output \"THROWN|$($_.Exception.Message)\" }")


def git(cwd, *a):
    subprocess.run(["git", *a], cwd=cwd, env={**os.environ, **GIT_ENV}, capture_output=True, text=True, check=True)


@pytest.fixture(scope="module")
def origin(tmp_path_factory):
    """A bare origin and a clone of it holding copies of land.ps1 and its queue script on main."""
    root = tmp_path_factory.mktemp("land")
    git(root, "init", "-q", "--bare", "-b", "main", "origin.git")
    git(root, "clone", "-q", "origin.git", "work")
    (root / "work" / "scripts").mkdir()
    for name in ("land.ps1", "land-queue.ps1"):
        shutil.copy(REPO / "scripts" / name, root / "work" / "scripts" / name)
    git(root / "work", "add", ".")
    git(root / "work", "commit", "-q", "-m", "base")
    git(root / "work", "push", "-q", "origin", "HEAD:main")
    return root / "work"


@pytest.fixture(scope="module")
def work(origin):
    """The clone on a branch whose one commit changes a live file, so land.ps1 reaches the build."""
    git(origin, "checkout", "-q", "-b", "feat")
    (origin / "app.js").write_text("live change\n")
    git(origin, "add", ".")
    git(origin, "commit", "-q", "-m", "feat")
    return origin


@pytest.fixture(scope="module")
def stubs(tmp_path_factory):
    """A folder with the fake `python` and an empty land_gate.py (land.ps1 only checks that it exists)."""
    root = tmp_path_factory.mktemp("stubs")
    (root / "land_gate.py").write_text("")
    (root / "stub.py").write_text(STUB)
    (root / "python.cmd").write_text(f'@"{sys.executable}" "{root / "stub.py"}" %*\r\n')
    return root


def land(work, stubs, behind, switch=""):
    assert PS, "land.ps1 is a PowerShell script: this test needs PowerShell (Windows)"
    env = {**os.environ, "PATH": f"{stubs}{os.pathsep}{os.environ['PATH']}", "FAKE_BEHIND": str(behind),
           "TESTING_SKILL": str(stubs), "LOADGATE": "off", **GIT_ENV}
    cmd = WRAP % (work / "scripts" / "land.ps1", switch)
    done = subprocess.run([PS, "-NoProfile", "-NonInteractive", "-Command", cmd], cwd=work, env=env,
                          capture_output=True, text=True, timeout=120)
    return done.stdout.splitlines()


@pytest.fixture(scope="module")
def behind_no_switch(work, stubs):
    return land(work, stubs, 2)


@pytest.fixture(scope="module")
def behind_with_switch(work, stubs):
    return land(work, stubs, 2, "-AllowStaleData")


@pytest.fixture(scope="module")
def not_behind(work, stubs):
    return land(work, stubs, 0)


def test_s3_a_land_behind_origin_throws_before_the_build_and_names_the_fix(behind_no_switch):
    thrown = [x for x in behind_no_switch if x.startswith("THROWN|")]

    assert len(thrown) == 1
    assert "ff-jarvis (C:/fake/ff-jarvis) is 2 commit(s) behind origin/main" in thrown[0]
    assert "sync-main.py" in thrown[0] and "-AllowStaleData builds anyway" in thrown[0]
    assert BUILD_REACHED not in behind_no_switch


def test_s3_allow_stale_data_warns_in_yellow_and_goes_on_to_the_build(behind_with_switch):
    warned = [x for x in behind_with_switch if "behind origin/main" in x]

    assert len(warned) == 1
    assert warned[0].startswith("Yellow|ff-jarvis (C:/fake/ff-jarvis) is 2 commit(s) behind")
    assert warned[0].endswith("(-AllowStaleData: building anyway)")
    assert BUILD_REACHED in behind_with_switch
    assert "THROWN|build failed (1)" in behind_with_switch


def test_s3_a_current_checkout_says_nothing_and_goes_on_to_the_build(not_behind):
    assert BUILD_REACHED in not_behind
    assert "THROWN|build failed (1)" in not_behind
    assert [x for x in not_behind if "behind" in x] == []
