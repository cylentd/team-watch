# team-watch

A single self-contained HTML page, deployed on Vercel from the committed root `index.html`.
Vercel **is** git-connected: a push to `main` deploys within a minute, so `main` must always
carry a current build. Data comes from the sibling `ff-jarvis` repo; this repo renders it.

Global architecture rules apply here: `~/Github/agent-config/shared/architecture.md`.

## Source vs generated

| File | |
|---|---|
| `design/src/shell.html` | **source** — the document: head, static markup, the two slots, `{{copy:key}}` |
| `design/src/content.json` | **source** — every user-facing string, `area.component.slot` -> text; the JS says `t("key")` and `--check` fails on a missing or unreferenced one |
| `design/src/css/**`, `design/src/js/**` | **source** — one concern per file, none over ~200 lines |
| `design/src/order.css.txt`, `order.js.txt` | the only order authority; `# pin:` lines say why an order is load-bearing |
| `design/assemble.py` | joins the parts into the template string; `--check` fails on an unlisted or missing part |
| `design/build.py` | inlines headshots and live data into the assembled template, writes both outputs |
| `index.html` | **generated** — full document, what Vercel serves |
| `design/index.html` | **generated** — fragment, what the Artifact publisher takes |

Never hand-edit the generated files. They are ~1.4 MB each because headshots are inlined as
base64, and `build.py` rewrites both in full on every run.

## Build, test, land

```
python design/build.py      # rebuild both outputs
python -m pytest            # 7 s: assembler, build against fixtures, lint, budgets, rendered golden
python -m pytest -m "not render"   # under a second, no browser
.\scripts\land.ps1          # rebase, test, rebuild, fold into the commit, land
```

The build fails on a lint error (`design/lint_css.py`), a contract violation (`design/contract.py`:
an injected block missing a field the JS reads), or a part the manifests do not agree on. The
suite builds against `tests/fixtures/` (never ff-jarvis) and compares the rendered page, in
Chromium, to `tests/golden/render.json`. A refactor proves "no visual change" with an empty diff;
an intended change regenerates the golden with `pytest --update-golden` and the diff is the
review. `tests/test_budgets.py` holds the size ratchets: what is over budget today is listed
with its size and may only shrink.

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
