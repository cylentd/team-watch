"""`design/sources.py`'s command line: how far the ff-jarvis checkout is behind origin/main.

scripts/land.ps1 runs `--fetch` and parses the printed line ("None": not a checkout); it owns -AllowStaleData.
`.testsched.json` adds `--refuse-stale`, because `ts.py land` stops only on a failed pre_build."""
import subprocess

import sources


def main(argv):
    """Exit code: 1 only with `--refuse-stale` on a checkout that is behind."""
    repo = sources.DWR.parent
    if "--fetch" in argv and (repo / ".git").exists():
        subprocess.run(["git", "-C", str(repo), "fetch", "--quiet", "origin", "main"])
    behind = sources.ff_jarvis_behind()
    print(behind, repo)
    if behind and "--refuse-stale" in argv:
        print(f"ff-jarvis is {behind} commit(s) behind origin/main, so this build would ship stale data. "
              f"Run: python {repo / 'scripts' / 'sync-main.py'}")
        return 1
    return 0
