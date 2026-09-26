<#
.SYNOPSIS
  One writer to main at a time: a first-come, first-served queue shared by every checkout.

.DESCRIPTION
  Dot-source it, then wrap the push:

      . "$repo\scripts\land-queue.ps1"
      $ticket = Enter-LandQueue -Repo $repo -Label "land worktree-x"
      try { ...fetch, rebase, test, build, push... } finally { Exit-LandQueue $ticket }

  Why (2026-09-26): several Claude sessions and the scheduled rebuild push to main. Each land
  takes ~2.5 min (fetch, rebase, the suite, the build) and only checks for a moved main at the
  push, so two lands in that window meant the loser re-ran everything, and a third meant a failed
  land and a hand rebase through a golden-file conflict. Holding the queue from fetch to push
  means every land rebases onto the last one that finished, and never races.

  The queue lives in the repo's common git dir (<repo>/.git/land-queue), which every worktree
  and the rebuild job's own checkout share. A ticket is a file named by its UTC ticks and PID;
  the oldest live ticket holds main. A ticket whose process is gone, or which is older than
  $StaleMinutes, is removed by whoever finds it, so a killed session never blocks the rest.
#>

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

<#
  Join the queue and return once this ticket is at the front. Throws after -TimeoutMinutes, having
  left the queue, so a caller that gives up never blocks the next one.
#>
function Enter-LandQueue {
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

function Exit-LandQueue([string]$Ticket) {
    if ($Ticket) { Remove-Item -Path $Ticket -Force -ErrorAction SilentlyContinue }
}
