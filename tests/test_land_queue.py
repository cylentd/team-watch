"""scripts/land-queue.ps1 (2026-09-26): one writer to main at a time. Each case runs the real
PowerShell functions against a throwaway git repo, so the queue under test is never the real one."""
import shutil
import subprocess
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
QUEUE = REPO / "scripts" / "land-queue.ps1"
PS = shutil.which("powershell") or shutil.which("pwsh")
pytestmark = pytest.mark.skipif(not PS, reason="no PowerShell on this machine")


def ps(script, cwd):
    return subprocess.run([PS, "-NoProfile", "-NonInteractive", "-Command", f". '{QUEUE}'; {script}"],
                          cwd=cwd, capture_output=True, text=True, timeout=60)


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


def tickets(repo):
    return sorted(p.name for p in (repo / ".git" / "land-queue").glob("*.ticket"))


def test_an_empty_queue_is_ours_at_once_and_left_empty(repo):
    r = ps(f"$t = Enter-LandQueue -Repo '{repo}' -Label a; Exit-LandQueue $t", repo)
    assert r.returncode == 0, r.stderr
    assert "main is ours" in r.stdout
    assert tickets(repo) == []


def test_a_dead_sessions_ticket_is_cleared_not_waited_on(repo):
    q = repo / ".git" / "land-queue"
    q.mkdir()
    # PID 999999 is not running; its ticket is older than ours and would block us if it counted.
    (q / "00000000000000000001-999999.ticket").write_text('{"pid":999999,"label":"land gone","since":"2026-09-26T00:00:00Z"}')
    r = ps(f"$t = Enter-LandQueue -Repo '{repo}' -Label b; Exit-LandQueue $t", repo)
    assert r.returncode == 0, r.stderr
    assert "clearing a stale ticket" in r.stdout and "main is ours" in r.stdout
    assert tickets(repo) == []


def test_the_second_lander_waits_for_the_first(repo):
    """First holds main for 4s; the second, started 1s later, must get it only after the first
    lets go, and must say whose land it waited on."""
    first = subprocess.Popen([PS, "-NoProfile", "-NonInteractive", "-Command",
                              f". '{QUEUE}'; $t = Enter-LandQueue -Repo '{repo}' -Label first; "
                              f"Start-Sleep -Seconds 4; [datetime]::UtcNow.Ticks; Exit-LandQueue $t"],
                             cwd=repo, stdout=subprocess.PIPE, text=True)
    time.sleep(1.5)
    second = ps(f"$t = Enter-LandQueue -Repo '{repo}' -Label second; [datetime]::UtcNow.Ticks; Exit-LandQueue $t", repo)
    out_first, _ = first.communicate(timeout=60)
    assert second.returncode == 0, second.stderr
    assert "waiting on first" in second.stdout
    released = int(out_first.strip().splitlines()[-1])
    got = int(second.stdout.strip().splitlines()[-1])
    assert got >= released, "the second lander got main while the first still held it"
    assert tickets(repo) == []


def test_giving_up_leaves_the_queue(repo):
    q = repo / ".git" / "land-queue"
    q.mkdir()
    # A live holder: this test's own Python process, so the ticket is not stale.
    import os
    (q / "00000000000000000001-{}.ticket".format(os.getpid())).write_text(
        '{"pid":%d,"label":"land holder","since":"%s"}' % (os.getpid(), time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
    r = ps(f"Enter-LandQueue -Repo '{repo}' -Label late -TimeoutMinutes 0", repo)
    assert r.returncode != 0 and "gave up" in (r.stderr + r.stdout)
    assert tickets(repo) == ["00000000000000000001-{}.ticket".format(os.getpid())], "the one that gave up left no ticket"
