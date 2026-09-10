<#
.SYNOPSIS
  Rebuild the generated page, fold it into the branch's commit, and land.

.DESCRIPTION
  index.html and design/index.html are build output. Committing them on every feature commit
  makes two parallel branches conflict on a 1.4 MB blob, so the convention is: feature branches
  never commit them, and the build runs once, here, at land time.

  Order matters. Rebase first, then build, then commit -- building before the rebase produces a
  page from the wrong parent and guarantees the conflict this script exists to avoid.

.EXAMPLE
  .\scripts\land.ps1 -DryRun     # say what would happen, change nothing
  .\scripts\land.ps1
#>
param(
    [switch]$DryRun,
    [string]$Base = "main"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$generated = @("index.html", "design/index.html")

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

$branch = (GitRead "rev-parse --abbrev-ref HEAD").Trim()
if ($branch -eq $Base) {
    throw "On '$Base'. Run this from the task branch -- landing is what it does."
}

# merge=ours in .gitattributes is silently ignored unless a driver is defined. A fresh clone has
# no local config, so set it here rather than trusting anyone to have read the README.
if (-not (GitRead "config --local --get merge.ours.driver")) {
    Write-Host "setting merge.ours.driver (was unset)" -ForegroundColor Yellow
    if (-not $DryRun) { GitRead "config --local merge.ours.driver true" | Out-Null }
}

# Uncommitted work that is not build output means this is not a finished branch.
$dirty = @(GitRead "status --porcelain" | Where-Object { $_ -and ($_.Substring(3) -notin $generated) })
if ($dirty.Count -gt 0) {
    Write-Host ($dirty -join "`n")
    throw "Uncommitted changes that are not build output. Commit or stash them first."
}

$ahead = [int](GitRead "rev-list --count $Base..HEAD").Trim()
if ($ahead -eq 0) { throw "Nothing to land: '$branch' has no commits $Base does not." }
if ($ahead -gt 1) {
    throw "'$branch' has $ahead commits. Squash first: git reset --soft $Base, then git commit."
}

# --- rebase, build, fold ----------------------------------------------------------------------

$behind = [int](GitRead "rev-list --count HEAD..$Base").Trim()
if ($behind -gt 0) {
    Write-Host "$behind commit(s) behind $Base -- rebasing" -ForegroundColor Cyan
    GitRun "rebase $Base" | Out-Null
    # A conflict in the two generated files is expected on any branch predating this convention.
    # merge=ours settles it silently; anything else stops the rebase and is a real conflict.
}

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

# --- land -------------------------------------------------------------------------------------

Write-Host "landing" -ForegroundColor Cyan
GitRun "land $Base" | Out-Null
if ($DryRun) { Write-Host "(dry run -- nothing above actually ran)" -ForegroundColor Yellow }
