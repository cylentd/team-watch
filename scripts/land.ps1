<#
.SYNOPSIS
  Rebuild the generated page, fold it into the branch's commit, and land -- from any worktree.

.DESCRIPTION
  index.html and design/index.html are build output. Committing them on every feature commit
  makes two parallel branches conflict on a 1.4 MB blob, so the convention is: feature branches
  never commit them, and the build runs once, here, at land time.

  Order matters. Rebase first, then test, then build, then commit -- building before the rebase
  produces a page from the wrong parent and guarantees the conflict this script exists to avoid,
  and the tests run on the rebased tree, which is the one that ships.

  `git land` never runs `git checkout <base>` -- it pushes HEAD onto origin/<base> and fast-forwards
  whichever checkout holds <base>, so this script lands straight from its own worktree with no
  contention over who gets to hold main. If the push loses a race to another session or a job, git
  land reports that (exit 2 or 3); this script re-fetches, rebases, re-tests and retries once.

  A diff that only touches docs and tests (*.md, tests/**) lands on its own. Anything that touches
  the live page stops and asks -- pass -Yes once a human has said go.

.EXAMPLE
  .\scripts\land.ps1 -DryRun          # say what would happen, change nothing
  .\scripts\land.ps1                  # docs/tests-only diff: lands unattended
  .\scripts\land.ps1 -Yes             # live-page diff, after asking the user
#>
param(
    [switch]$DryRun,
    [string]$Base = "main",
    [switch]$Yes
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
# build.json belongs here for the same reason as the two pages: design/build.py writes it, so a
# branch that carried it would conflict with every other branch that had rebuilt. It is the hash
# of the injected data, which an open tab fetches to learn that main has moved.
# `games/` is the drive strips, one JSON per played game, also written by design/build.py. Unlike
# the three above these never conflict -- a finished game is never rewritten, so a build only ever
# adds files -- but they belong to the same build, so they are folded in at the same moment.
# `heads/` is the headshots, copied from ff-jarvis by the same build; the page names them by path.
$generated = @("index.html", "design/index.html", "build.json", "games", "heads")

# Call git.exe explicitly, and never name a helper `Git`: PowerShell resolves a function name
# before an external command, case-insensitively, so `function Git { & git ... }` calls itself
# until the call depth blows.
function GitRun($argline) {
    Write-Host "  git $argline" -ForegroundColor DarkGray
    if ($DryRun) { return "" }
    $out = & git.exe -C $repo @($argline -split ' ')
    if ($LASTEXITCODE -ne 0) { throw "git $argline failed ($LASTEXITCODE)" }
    return $out
}

function GitRead($argline) { & git.exe -C $repo @($argline -split ' ') }

# --- guards -----------------------------------------------------------------------------------

# A detached HEAD has no branch to land and refuses the same way landing from $Base does --
# `rev-parse --abbrev-ref HEAD` prints the literal string "HEAD" when detached.
$branch = (GitRead "rev-parse --abbrev-ref HEAD").Trim()
if ($branch -eq $Base -or $branch -eq "HEAD") {
    throw "On '$branch'. Run this from the task branch -- landing is what it does."
}

# merge=ours in .gitattributes is silently ignored unless a driver is defined. A fresh clone has
# no local config, so set it here rather than trusting anyone to have read the README.
if (-not (GitRead "config --local --get merge.ours.driver")) {
    Write-Host "setting merge.ours.driver (was unset)" -ForegroundColor Yellow
    if (-not $DryRun) { GitRead "config --local merge.ours.driver true" | Out-Null }
}

# Uncommitted work that is not build output means this is not a finished branch. `games` is a
# directory, so a path counts as build output when it IS one of $generated or sits under one:
# comparing whole paths only let games/2026_02_LV_LAC.json through as unfinished work.
function IsGenerated($path) {
    foreach ($g in $generated) { if ($path -eq $g -or $path.StartsWith("$g/")) { return $true } }
    return $false
}
$dirty = @(GitRead "status --porcelain" | Where-Object { $_ -and -not (IsGenerated $_.Substring(3)) })
if ($dirty.Count -gt 0) {
    Write-Host ($dirty -join "`n")
    throw "Uncommitted changes that are not build output. Commit or stash them first."
}

# Every comparison from here on reads origin/$Base, never the local branch -- a session landing
# from its own worktree never touches the local $Base ref, so a stale local copy would lie.
Write-Host "fetching" -ForegroundColor Cyan
GitRun "fetch origin $Base" | Out-Null

$ahead = [int](GitRead "rev-list --count origin/$Base..HEAD").Trim()
if ($ahead -eq 0) { throw "Nothing to land: '$branch' has no commits origin/$Base does not." }
if ($ahead -gt 1) {
    throw "'$branch' has $ahead commits. Squash first: git reset --soft origin/$Base, then git commit."
}

# --- live-change gate ---------------------------------------------------------------------------

# Docs and tests land themselves; anything that touches the live page needs a human to have said
# go, because it ships to Vercel within a minute of hitting main.
# --no-renames: a rename lists only its new path, so moving code into docs/x.md would read as quiet.
$changedPaths = @(GitRead "diff --no-renames --name-only origin/$Base...HEAD" | Where-Object { $_ })
$notQuiet = @($changedPaths | Where-Object { -not ($_ -like "*.md" -or $_ -like "tests/*") })
if ($notQuiet.Count -gt 0 -and -not $Yes) {
    Write-Host ($notQuiet -join "`n")
    throw "This changes the live page. Ask the user, then re-run with -Yes."
}

# --- rebase, test, build, fold, land -------------------------------------------------------------

# A conflict in the two generated files is expected on any branch predating this convention.
# merge=ours settles it silently; anything else stops the rebase and is a real conflict.
#
# `git land` can lose a fast-forward race to another session or a scheduled job (exit 2, push
# rejected) or find HEAD no longer contains origin/$Base (exit 3, needs a rebase). Either means
# origin/$Base moved since the fetch above, so this retries the whole rebase-test-build-fold-land
# cycle once, on the theory that a second collision in a row means something needs a human.
$maxAttempts = 2
for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
    $behind = [int](GitRead "rev-list --count HEAD..origin/$Base").Trim()
    if ($behind -gt 0) {
        Write-Host "$behind commit(s) behind origin/$Base -- rebasing" -ForegroundColor Cyan
        GitRun "rebase origin/$Base" | Out-Null
    }

    Write-Host "testing" -ForegroundColor Cyan
    Write-Host "  python -m pytest" -ForegroundColor DarkGray
    if (-not $DryRun) {
        Push-Location $repo
        try {
            & python -m pytest
            if ($LASTEXITCODE -ne 0) { throw "tests failed ($LASTEXITCODE) -- nothing landed" }
        } finally { Pop-Location }
    }

    # A docs/tests-only diff cannot change the page, so it lands without a rebuild: main already
    # carries a current build, and a fresh worktree has no data/feed.json to build a full one from.
    if ($notQuiet.Count -eq 0) {
        Write-Host "docs/tests only -- no rebuild" -ForegroundColor DarkGray
    } else {
        Write-Host "building" -ForegroundColor Cyan
        Write-Host "  python design/build.py" -ForegroundColor DarkGray
        if (-not $DryRun) {
            Push-Location $repo
            try {
                & python design/build.py
                if ($LASTEXITCODE -ne 0) { throw "build failed ($LASTEXITCODE)" }
            } finally { Pop-Location }
        }

        $changed = @(GitRead "status --porcelain" | Where-Object { $_ })
        if ($changed.Count -gt 0) {
            Write-Host "folding the rebuild into the branch commit" -ForegroundColor Cyan
            GitRun ("add " + ($generated -join " ")) | Out-Null
            GitRun "commit --amend --no-edit" | Out-Null
        } else {
            Write-Host "build output unchanged -- nothing to fold" -ForegroundColor DarkGray
        }
    }

    Write-Host "landing" -ForegroundColor Cyan
    Write-Host "  git land $Base" -ForegroundColor DarkGray
    if ($DryRun) {
        Write-Host "(dry run -- nothing above actually ran)" -ForegroundColor Yellow
        break
    }

    # Called directly, not through GitRun, so $LASTEXITCODE survives to distinguish "moved, retry"
    # (2 or 3) from "landed" (0) from everything else (a real failure -- stop and say so).
    $landOutput = & git.exe -C $repo land $Base
    $landCode = $LASTEXITCODE
    $landOutput | ForEach-Object { Write-Host $_ }

    if ($landCode -eq 0) {
        break
    } elseif (($landCode -eq 2 -or $landCode -eq 3) -and $attempt -lt $maxAttempts) {
        Write-Host "origin/$Base moved -- rebasing and re-testing once" -ForegroundColor Yellow
        GitRun "fetch origin $Base" | Out-Null
        continue
    } else {
        throw "git land failed ($landCode) -- nothing landed"
    }
}
