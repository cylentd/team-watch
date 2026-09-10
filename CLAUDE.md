# team-watch

A single self-contained HTML page, deployed on Vercel from the committed root `index.html`.
Vercel **is** git-connected: a push to `main` deploys within a minute, so `main` must always
carry a current build. Data comes from the sibling `ff-jarvis` repo; this repo renders it.

Global architecture rules apply here: `~/Github/agent-config/shared/architecture.md`.

## Source vs generated

| File | |
|---|---|
| `design/src/shell.html` | **source** — the document: head, static markup, the two slots |
| `design/src/css/**`, `design/src/js/**` | **source** — one concern per file, none over ~200 lines |
| `design/src/order.css.txt`, `order.js.txt` | the only order authority; `# pin:` lines say why an order is load-bearing |
| `design/assemble.py` | joins the parts into the template string; `--check` fails on an unlisted or missing part |
| `design/build.py` | inlines headshots and live data into the assembled template, writes both outputs |
| `index.html` | **generated** — full document, what Vercel serves |
| `design/index.html` | **generated** — fragment, what the Artifact publisher takes |

Never hand-edit the generated files. They are ~1.4 MB each because headshots are inlined as
base64, and `build.py` rewrites both in full on every run.

## Build and land

```
python design/build.py      # rebuild both outputs
.\scripts\land.ps1          # rebase, rebuild, fold into the commit, land
```

**Feature branches do not commit `index.html` or `design/index.html`.** The build runs once, at
land time, via `scripts/land.ps1`. This is not tidiness: both files are single blobs that change
completely on every build, so two branches that each carry one conflict on a million lines that
cannot be merged, only chosen. `.gitattributes` marks them `-diff merge=ours` (the `merge=ours`
attribute needs `git config --local merge.ours.driver true`, which `land.ps1` sets if missing).

**If they ever do conflict, never merge them.** Take either side and rebuild:

```
git checkout --ours index.html design/index.html
git rebase --continue
python design/build.py
```

## Two sessions at once

More than one Claude session works this repo. Two sessions in one checkout interleave edits in
the same source file and overwrite each other's `index.html` — it has already happened. The
second session takes a worktree: say "use a worktree", which branches from `origin/main` under
`.claude/worktrees/`. Notes that cost time to learn:

- `git land` runs `git checkout main`, and git refuses a branch checked out in another worktree.
  Land from a checkout where `main` is free, or remove the worktree first.
- A fresh worktree has no `data/feed.json` (untracked). The build falls back to reading
  `ff-jarvis` directly, so it still works; copy the file in if you want the freshness badges.
- Before touching a file the other session may hold, ask it. `git stash show --name-only` is the
  cheap way to prove a file really is dirty before claiming it is.

## Data

`design/build.py` reads `ff-jarvis`'s `data/*.json` (rosters, props, prop model, player
projections, Sleeper status, DFS pool) through `data/feed.json` first and the files directly as
a fallback. DFS projections come from ff-jarvis's `model.market.projections`; the page never
computes model numbers itself. See `README.md` for the DFS CSV import and `design/DESIGN.md` for
the design system and the field contract.
