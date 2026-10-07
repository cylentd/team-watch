<#
.SYNOPSIS
  One writer to main at a time: the land queue, testsched's (agent-config/testsched, SPEC 14), or the
  old git-dir queue when loadgate is off or not installed (SPEC invariant 6).

.DESCRIPTION
  Dot-source it, then wrap the push (the scheduled rebuild job in agent-config does exactly this):

      . "$repo\scripts\land-queue.ps1"
      $ticket = Enter-LandQueue -Repo $repo -Label "land worktree-x"
      try { ...fetch, rebase, test, build, push... } finally { Exit-LandQueue $ticket }

  The queue is `ts.py queue enter|exit` (testsched/queue.py): tickets in <git common dir>/land-queue,
  `<ticks:D20>-<pid>.ticket`, the oldest live one holds main, a dead or 30-minute-old ticket is cleared by
  whoever finds it, a wait over -TimeoutMinutes gives up with nothing landed. Why it exists: 2026-09-26.

  With LOADGATE=off (TESTSCHED=off, TW_SLOTS=off) or no ts.py ($env:LOADGATE_CODE, ~/.agents/testsched),
  the same two functions run the queue this file held before testsched (same folder, same ticket names,
  same messages), so a machine without the library still lands and rebuilds.
#>

# The folder holding ts.py: $env:LOADGATE_CODE, else the install junction ~/.agents/testsched. $null when neither.
function Find-TestschedDir {
    $candidates = @($env:LOADGATE_CODE, (Join-Path $HOME ".agents/testsched"))
    foreach ($c in $candidates) { if ($c -and (Test-Path (Join-Path $c "ts.py"))) { return $c } }
    return $null
}

function Get-TestschedDir {
    $dir = Find-TestschedDir
    if (-not $dir) { throw "testsched not found (`$env:LOADGATE_CODE, ~/.agents/testsched): run agent-config's install.ps1" }
    return $dir
}

# loadgate's off switch, as loadgate/state.py reads it (OFF_NAMES, OFF_VALUES; PowerShell cannot import it).
function Test-LoadgateOff {
    foreach ($name in "LOADGATE", "TESTSCHED", "TW_SLOTS") {
        $v = [Environment]::GetEnvironmentVariable($name)
        if ($v -and @("off", "0", "false", "no") -contains $v.Trim().ToLower()) { return $true }
    }
    return $false
}

# True when the queue is testsched's: loadgate is on and ts.py is installed.
function Use-Testsched { return (-not (Test-LoadgateOff)) -and [bool](Find-TestschedDir) }

# --- the old queue: a ticket file per land in <git common dir>/land-queue, no testsched ---------------

$script:LandQueueStaleMinutes = 30

function Get-LandQueueDir([string]$Repo) {
    $common = (& git.exe -C $Repo rev-parse --path-format=absolute --git-common-dir).Trim()
    $dir = Join-Path $common "land-queue"
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    return $dir
}

# Live tickets, oldest first, after removing the dead ones.
function Get-LandQueue([string]$Dir) {
    $now = (Get-Date).ToUniversalTime()
    $live = @()
    foreach ($f in Get-ChildItem -Path $Dir -Filter "*.ticket" -File | Sort-Object Name) {
        $t = $null
        try { $t = Get-Content -Raw -Path $f.FullName | ConvertFrom-Json } catch { }
        $age = if ($t) { ($now - [datetime]::Parse($t.since).ToUniversalTime()).TotalMinutes } else { 999 }
        $alive = $t -and (Get-Process -Id ([int]$t.pid) -ErrorAction SilentlyContinue)
        if (-not $alive -or $age -gt $script:LandQueueStaleMinutes) {
            Write-Host "land queue: clearing a stale ticket ($($f.Name))" -ForegroundColor Yellow
            Remove-Item -Path $f.FullName -Force -ErrorAction SilentlyContinue
            continue
        }
        $live += [pscustomobject]@{Path = $f.FullName; Name = $f.Name; Label = $t.label; Pid = [int]$t.pid}
    }
    return ,$live
}

# Join the queue and return once this ticket is at the front. Throws after -TimeoutMinutes, having
# left the queue, so a caller that gives up never blocks the next one.
function Enter-GitDirQueue {
    param([Parameter(Mandatory)][string]$Repo, [string]$Label = "land", [int]$TimeoutMinutes = 20)
    $dir = Get-LandQueueDir $Repo
    $now = (Get-Date).ToUniversalTime()
    $name = "{0:D20}-{1}.ticket" -f $now.Ticks, $PID
    $path = Join-Path $dir $name
    @{pid = $PID; label = $Label; since = $now.ToString("o")} | ConvertTo-Json -Compress |
        Set-Content -Path $path -Encoding utf8
    $deadline = $now.AddMinutes($TimeoutMinutes)
    $said = ""
    while ($true) {
        $queue = Get-LandQueue $dir
        $at = [array]::IndexOf(@($queue | ForEach-Object Name), $name)
        if ($at -eq 0) { Write-Host "land queue: main is ours" -ForegroundColor Cyan; return $path }
        if ($at -lt 0) {
            # Our own ticket was cleared (a clock jump past the stale limit): rejoin at the back.
            @{pid = $PID; label = $Label; since = (Get-Date).ToUniversalTime().ToString("o")} | ConvertTo-Json -Compress |
                Set-Content -Path $path -Encoding utf8
            continue
        }
        $msg = "land queue: #$($at + 1), waiting on $($queue[0].Label) (pid $($queue[0].Pid))"
        if ($msg -ne $said) { Write-Host $msg -ForegroundColor Yellow; $said = $msg }
        if ((Get-Date).ToUniversalTime() -gt $deadline) {
            Remove-Item -Path $path -Force -ErrorAction SilentlyContinue
            throw "land queue: waited $TimeoutMinutes min behind $($queue[0].Label) -- gave up, nothing landed"
        }
        Start-Sleep -Seconds 3
    }
}

# --- the two entry points land.ps1 and the rebuild job call --------------------------------------------

# Join the queue; returns the ticket once it is at the front. Throws after -TimeoutMinutes, having left the queue.
function Enter-LandQueue {
    param([Parameter(Mandatory)][string]$Repo, [string]$Label = "land", [int]$TimeoutMinutes = 20)
    if (-not (Use-Testsched)) { return Enter-GitDirQueue -Repo $Repo -Label $Label -TimeoutMinutes $TimeoutMinutes }
    $ts = Join-Path (Get-TestschedDir) "ts.py"
    $ticket = $null
    # -u: each "waiting on" line must reach the console as it is printed. The last line is the ticket.
    & python -u $ts queue enter --repo $Repo --label $Label --pid $PID --timeout $TimeoutMinutes |
        ForEach-Object { Write-Host $_; $ticket = "$_" }
    if ($LASTEXITCODE -ne 0) { throw "land queue: gave up (ts.py exit $LASTEXITCODE) -- nothing landed" }
    return $ticket
}

function Exit-LandQueue([string]$Ticket) {
    if (-not $Ticket) { return }
    if (-not (Use-Testsched)) { Remove-Item -Path $Ticket -Force -ErrorAction SilentlyContinue; return }
    & python (Join-Path (Get-TestschedDir) "ts.py") queue exit $Ticket | Out-Null
}
