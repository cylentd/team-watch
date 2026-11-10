import json
import os
import subprocess

import pytest

from conftest import REPO


pytestmark = pytest.mark.integration
HARNESS = r'''
$ErrorActionPreference = "Stop"
. $env:LAND_QUEUE_SCRIPT
$owner = if ($env:TEST_OWNER -eq "dead") { [int]::MaxValue } else { $PID }
$since = if ($env:TEST_OWNER -eq "malformed") { "not a timestamp" } else { "2000-01-01T00:00:00Z" }
$ticket = Join-Path $env:TEST_QUEUE "00000000000000000001-$owner.ticket"
@{pid = $owner; label = "old owner"; since = $since} | ConvertTo-Json -Compress |
    Set-Content -LiteralPath $ticket -Encoding utf8
$live = Get-LandQueue $env:TEST_QUEUE
[ordered]@{count = $live.Count; exists = (Test-Path -LiteralPath $ticket)} | ConvertTo-Json -Compress
'''


@pytest.mark.parametrize("owner,expected", [("live", {"count": 1, "exists": True}),
                                          ("dead", {"count": 0, "exists": False}),
                                          ("malformed", {"count": 0, "exists": False})])
def test_fallback_queue_preserves_live_owners_and_reclaims_invalid_tickets(tmp_path, owner, expected):
    environment = dict(os.environ, LAND_QUEUE_SCRIPT=str(REPO / "scripts/land-queue.ps1"),
                       TEST_QUEUE=str(tmp_path), TEST_OWNER=owner)
    done = subprocess.run(["powershell", "-NoProfile", "-Command", HARNESS], env=environment,
                          capture_output=True, text=True, timeout=15)
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout.splitlines()[-1]) == expected
