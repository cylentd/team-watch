<#
.SYNOPSIS
  Rebuild the generated page, fold it into the branch's commit, and land -- from any worktree.

.DESCRIPTION
  index.html and design/index.html are build output. Committing them on every feature commit
  makes two parallel branches conflict on a 1.4 MB blob, so the convention is: feature branches
  never commit them, and the build runs once, here, at land time.

  Order matters. Rebase first, then test, then build, then commit -- building before the rebase
  produces a page from the wrong parent and guarantees the conflict this script exists to avoid,
  and the tests run on the rebased tree, which is the one that ships. The tests run before the
  queue and again inside it only if origin/<base> moved meanwhile (2026-10-05).

  `git land` never runs `git checkout <base>` -- it pushes HEAD onto origin/<base> and fast-forwards
  whichever checkout holds <base>, so this script lands straight from its own worktree with no
  contention over who gets to hold main. Two sessions landing at once queue (scripts/land-queue.ps1):
  the second waits, printing whose land it is behind, then rebases onto the first. If the push
  still loses a race (a push from outside the queue), git land reports that (exit 2 or 3); this
  script re-fetches, rebases, re-tests and retries once.

  A diff that only touches docs and tests (*.md, tests/**) lands on its own. Anything that touches
  the live page stops and asks -- pass -Yes once a human has said go.

  The testing skill's land gate (`land_gate.py`, $env:TESTING_SKILL else ~/.agents/skills/testing/
  scripts) runs once, after the first test run and its 10-run check: test-first (source with no test
  change stops, unless a commit says `Test-Exempt: <reason>`), the shrink-only backlog, test lint,
  frozen tests (`Test-Reapproved: <entry> <reason>`) and mutation. Every check is the skill's and
  every repo gets a new one without a change here. A dry run runs the gate without mutation.
  After it passes, `freeze.py --update` writes tests/.frozen.json and the fold below takes it with
  the build output: a feature branch never commits that file.

.EXAMPLE
  .\scripts\land.ps1 -DryRun          # say what would happen, change nothing
  .\scripts\land.ps1                  # docs/tests-only diff: lands unattended
  .\scripts\land.ps1 -Yes             # live-page diff, after asking the user
  .\scripts\land.ps1 -Yes -Full       # the same, testing everything rather than what the diff touches
#>
param(
    [switch]$DryRun,
    [string]$Base = "main",
    [switch]$Yes,
    [switch]$Full,    # every test, not only the ones this diff can break (scripts/impact.py)
    [switch]$AllowStaleData,  # build even when the ff-jarvis checkout is behind its origin/main
    [switch]$SkipMutate       # leave the mutation check out of the land gate (tests/README.md "Proving a test")
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot

# The testing skill's scripts: $env:TESTING_SKILL when set (a skill checkout agent-config has not landed
# yet), else the installed copy. scripts/run_tests.py and scripts/flake_run.py resolve it the same way.
$skill = if ($env:TESTING_SKILL) { $env:TESTING_SKILL } else { Join-Path $HOME ".agents/skills/testing/scripts" }

# Seconds per phase, appended to the test history when the land ends, landed or not
# (scripts/testlog.py land; `python scripts/testlog.py` reads them back). The pytest runs below are
# recorded there too, as kind "land".
$clock = [Diagnostics.Stopwatch]::StartNew()
# `mutate` is the land gate's phase (mutation is its slow check); testlog.py's table still names it so.
$phase = [ordered]@{ test = 0.0; repeat = 0.0; mutate = 0.0; queue = 0.0; retest = 0.0; build = 0.0; push = 0.0 }
$testRuns = 0
function Timed($name, [scriptblock]$block) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    try { & $block } finally { $phase[$name] += $sw.Elapsed.TotalSeconds }
}
# build.json belongs here for the same reason as the two pages: design/build.py writes it, so a
# branch that carried it would conflict with every other branch that had rebuilt. It is the hash
# of the injected data, which an open tab fetches to learn that main has moved.
# `games/` is the drive strips, one JSON per played game, also written by design/build.py. Unlike
# the three above these never conflict -- a finished game is never rewritten, so a build only ever
# adds files -- but they belong to the same build, so they are folded in at the same moment.
# `heads/` is the headshots, copied from ff-jarvis by the same build; the page names them by path.
# `avatars/` is each Yahoo team's avatar (design/avatars.py, 2026-10-06), copied the same way.
# `trade_offers.json` is the trade builder's offers (design/trade_offers.py), rewritten whole by every build
# like build.json, and fetched by the page on first open, so Vercel must serve it (.vercelignore).
# `preview_archive.json` is Preview's earlier weeks (design/preview_archive.py), the same kind of file.
# `tests/.frozen.json` is the frozen tests' hashes (the testing skill's freeze.py, 2026-10-06), written below once
# the gate has passed: a branch that carried it would conflict with every other branch, exactly like build.json.
$generated = @("index.html", "design/index.html", "build.json", "trade_offers.json", "preview_archive.json", "games", "heads", "avatars", "tests/.frozen.json")

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
# .testing-backlog.json counts as tests: the gate's backlog check fails any growth, so a change to it
# can only be a fixed test leaving the list.
$changedPaths = @(GitRead "diff --no-renames --name-only origin/$Base...HEAD" | Where-Object { $_ })
$notQuiet = @($changedPaths | Where-Object { -not ($_ -like "*.md" -or $_ -like "tests/*" -or $_ -eq ".testing-backlog.json") })
if ($notQuiet.Count -gt 0 -and -not $Yes) {
    Write-Host ($notQuiet -join "`n")
    throw "This changes the live page. Ask the user, then re-run with -Yes."
}

# --- the land gate ----------------------------------------------------------------------------------

# One call runs every check (CLAUDE.md "Testing"): test-first, backlog, lint, freeze, mutate. The script
# is the testing skill's, shared by every repo rather than copied into each. It runs after the first
# test run, below; a dry run runs it now, without mutation (mutation needs a green suite, the rest only
# reads git).
$gate = Join-Path $skill "land_gate.py"
if (-not (Test-Path $gate)) { throw "No $gate. Run agent-config's install.ps1, then land again." }
if ($DryRun) {
    & python $gate --repo $repo --base "origin/$Base" --skip mutate
    if ($LASTEXITCODE -ne 0) { throw "land gate failed ($LASTEXITCODE) -- add a test, a Test-Exempt: <reason> trailer, or fix what it names" }
}

# --- rebase and test --------------------------------------------------------------------------------

# A conflict in the two generated files is expected on any branch predating this convention.
# merge=ours settles it silently; anything else stops the rebase and is a real conflict.
function RebaseAndTest {
    $behind = [int](GitRead "rev-list --count HEAD..origin/$Base").Trim()
    if ($behind -gt 0) {
        Write-Host "$behind commit(s) behind origin/$Base -- rebasing" -ForegroundColor Cyan
        GitRun "rebase origin/$Base" | Out-Null
    }

    # scripts/run_tests.py picks and runs the tests, in parallel: only the ones this diff can break
    # (scripts/impact.py, tests/impact.json), so a change fenced to one view runs that view's tests
    # plus the core. Anything the map does not claim runs everything, and so does -Full. The
    # scheduled rebuild runs the whole suite twice a day either way.
    $testArgs = @("--base", "origin/$Base", "--committed")
    if ($Full) { $testArgs += "--full" }
    $runner = Join-Path $PSScriptRoot "run_tests.py"

    Write-Host "testing" -ForegroundColor Cyan
    if ($DryRun) {
        & python $runner @testArgs --dry-run
        if ($LASTEXITCODE -ne 0) { throw "scripts/run_tests.py failed ($LASTEXITCODE) -- fix it or re-run with -Full" }
        return
    }
    $env:TW_RUN_KIND = "land"
    $script:testRuns++
    try {
        Timed $(if ($script:testRuns -eq 1) { "test" } else { "retest" }) { & python $runner @testArgs }
        if ($LASTEXITCODE -ne 0) { throw "tests failed ($LASTEXITCODE) -- nothing landed" }
        # The branch's new and changed tests, 10 times in parallel: a flake is caught before it
        # lands, not by the weekly flake run after it. The land gate then runs every check the testing
        # skill has (test-first, backlog, lint, frozen tests, mutation), and any failure blocks. Both
        # run once: a retest after origin moved changes neither the branch's tests nor its code.
        if ($script:testRuns -eq 1) {
            Timed repeat { & python $runner --repeat-new 10 --base "origin/$Base" --committed }
            if ($LASTEXITCODE -ne 0) { throw "a new or changed test failed one of 10 runs -- nothing landed" }
            # Configured by .testing.json (mutate, limits, freeze); mutation's tests come from
            # scripts/mutate_tests.py. TW_RUN_KIND=mutate tags its pytest runs in the test history
            # (tests/runlog.py) apart from the land's own.
            $gateArgs = @("--repo", $repo, "--base", "origin/$Base")
            if ($SkipMutate) { $gateArgs += @("--skip", "mutate") }
            $env:TW_RUN_KIND = "mutate"
            Timed mutate { & python $gate @gateArgs }
            if ($LASTEXITCODE -ne 0) { throw "land gate failed ($LASTEXITCODE) -- nothing landed" }
            $env:TW_RUN_KIND = "land"
        }
    } finally { Remove-Item Env:TW_RUN_KIND -ErrorAction SilentlyContinue }
}

# The first test run happens before the queue (2026-10-05). Until then a land held main for its
# whole test run, so a second session's land waited out the first's tests and then ran its own.
# Now the queue holds only the check, the build and the push; tests run again inside it only when
# origin/$Base moved while they ran, because only then is the tree that ships a different one.
$outcome = "failed"
try {
RebaseAndTest

# --- the queue ------------------------------------------------------------------------------------

# One writer to main at a time (scripts/land-queue.ps1): from here to the push, this land holds
# main, so it rebases onto the last land that finished rather than racing it. The scheduled
# rebuild joins the same queue. A dry run changes nothing, so it does not queue.
$ticket = $null
if (-not $DryRun) {
    . (Join-Path $PSScriptRoot "land-queue.ps1")
    $ticket = Timed queue { Enter-LandQueue -Repo $repo -Label "land $branch" }
}
try {

# --- fetch again, build, fold, land ---------------------------------------------------------------

# `git land` can lose a fast-forward race to another session or a scheduled job (exit 2, push
# rejected) or find HEAD no longer contains origin/$Base (exit 3, needs a rebase). Either means
# origin/$Base moved since the fetch, so this retries the whole rebase-test-build-fold-land cycle
# once, on the theory that a second collision in a row means something needs a human.
$maxAttempts = 2
for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
    GitRun "fetch origin $Base" | Out-Null
    $moved = [int](GitRead "rev-list --count HEAD..origin/$Base").Trim()
    if ($moved -gt 0) {
        Write-Host "origin/$Base moved while testing ($moved commit(s)) -- rebasing and testing again" -ForegroundColor Yellow
        RebaseAndTest
    } else {
        Write-Host "origin/$Base unchanged since the tests -- no second run" -ForegroundColor DarkGray
    }

    # A docs/tests-only diff cannot change the page, so it lands without a rebuild: main already
    # carries a current build, and a fresh worktree has no data/feed.json to build a full one from.
    if ($notQuiet.Count -eq 0) {
        Write-Host "docs/tests only -- no rebuild" -ForegroundColor DarkGray
    } else {
        # The page is built from the ff-jarvis checkout's data/, which the jobs write into; after an
        # ff-jarvis land it can sit behind origin/main (2026-09-29: the 2018 Records lineups landed
        # and this built without them). Fetch it, and refuse a stale one unless told otherwise.
        if (-not $DryRun) {
            Push-Location $repo
            try { $ffjBehind, $ffj = (& python design/sources.py --fetch).Trim() -split ' ', 2 } finally { Pop-Location }
            if ($ffjBehind -match '^\d+$' -and [int]$ffjBehind -gt 0) {
                $msg = "ff-jarvis ($ffj) is $ffjBehind commit(s) behind origin/main, so this build would ship stale data. Run: python $ffj\scripts\sync-main.py"
                if ($AllowStaleData) { Write-Host "$msg (-AllowStaleData: building anyway)" -ForegroundColor Yellow }
                else { throw "$msg -- then re-run. -AllowStaleData builds anyway." }
            }
        }

        Write-Host "building" -ForegroundColor Cyan
        Write-Host "  python design/build.py" -ForegroundColor DarkGray
        if (-not $DryRun) {
            Push-Location $repo
            try {
                Timed build { & python design/build.py }
                if ($LASTEXITCODE -ne 0) { throw "build failed ($LASTEXITCODE)" }
            } finally { Pop-Location }
        }
    }

    # The frozen tests' hashes, from the tree that ships (the gate passed on it). Docs/tests-only diffs
    # need this too: they are where tests change. It joins the build output in the one fold below.
    Write-Host "freezing" -ForegroundColor Cyan
    Write-Host "  python $skill\freeze.py --repo $repo --update" -ForegroundColor DarkGray
    if (-not $DryRun) {
        Timed build { & python (Join-Path $skill "freeze.py") --repo $repo --update }
        if ($LASTEXITCODE -ne 0) { throw "freeze --update failed ($LASTEXITCODE) -- nothing landed" }
    }

    if (-not $DryRun) {
        $changed = @(GitRead "status --porcelain" | Where-Object { $_ })
        if ($changed.Count -gt 0) {
            Write-Host "folding the rebuild into the branch commit" -ForegroundColor Cyan
            # Only what exists: trade_offers.json is absent until ff-jarvis has written offers, and `git add` of a missing path fails.
            GitRun ("add " + (($generated | Where-Object { Test-Path (Join-Path $repo $_) }) -join " ")) | Out-Null
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
    $landOutput = Timed push { & git.exe -C $repo land $Base }
    $landCode = $LASTEXITCODE
    $landOutput | ForEach-Object { Write-Host $_ }

    if ($landCode -eq 0) {
        $outcome = "landed"
        break
    } elseif (($landCode -eq 2 -or $landCode -eq 3) -and $attempt -lt $maxAttempts) {
        Write-Host "origin/$Base moved -- rebasing and re-testing once" -ForegroundColor Yellow
        continue
    } else {
        throw "git land failed ($landCode) -- nothing landed"
    }
}

} finally { if ($ticket) { Exit-LandQueue $ticket } }

} finally {
    if (-not $DryRun) {
        $kv = @("branch=$branch", "outcome=$outcome", "full=$([bool]$Full)", "live=$($notQuiet.Count -gt 0)",
                "tests=$testRuns", "total=$($clock.Elapsed.TotalSeconds)") + @($phase.Keys | ForEach-Object { "$_=$($phase[$_])" })
        & python (Join-Path $PSScriptRoot "testlog.py") land @kv
        if ($LASTEXITCODE -ne 0) { Write-Host "  (land not recorded in the test history)" -ForegroundColor Yellow }
    }
}
