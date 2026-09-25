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
| `design/build.py` | inlines live data into the assembled template, writes both outputs, copies headshots to `heads/` |
| `heads/` | **generated** — every ff-jarvis headshot, `<slug>.webp` (96px); the page names them by path (since 2026-09-24). `heads/lg/` holds the 256px ones ff-jarvis cuts for its board players (~230); the trading cards use those (since 2026-09-25) |
| `index.html` | **generated** — full document, what Vercel serves |
| `design/index.html` | **generated** — fragment, what the Artifact publisher takes |

Never hand-edit the generated files. The pages are ~2.6 MB each (all live data inlined), and
`build.py` rewrites both in full on every run.

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
the same source file and overwrite each other's `index.html` — it has already happened. So every
feature, not only the second, starts in its own worktree (`EnterWorktree` before the first edit),
and the main checkout stays on `main`, unedited. Notes that cost time to learn:

- `.\scripts\land.ps1` lands from the worktree itself (since 2026-09-24 `git land` pushes
  `HEAD:main` and never checks `main` out). A diff outside `tests/` and `*.md` changes the live
  page, so it needs `-Yes`, passed only after the user says yes. Landing ends the feature:
  `ExitWorktree` with `remove` puts the session back in the main checkout, and the session goes on.
- The page-rebuild job pushes to `main` at 6:30 and 15:00. A land that races it gets exit 2 from
  `git land`; `land.ps1` rebases, rebuilds and retries once.
- A fresh worktree has no `data/feed.json` (untracked). The build falls back to reading
  `ff-jarvis` directly, so it still works; copy the file in if you want the freshness badges.
- Before touching a file the other session may hold, ask it. `git stash show --name-only` is the
  cheap way to prove a file really is dirty before claiming it is.

## Navigation

Two levels since 2026-09-21. Four groups in the nav bar, each holding the views that answer one
question; `SURFACE` is always the **leaf**, never the group, and the group is derived from it.

| group | views |
|---|---|
| My teams | Roster, Waivers |
| Players (id `scouting`, was "Scouting" until 2026-09-25) | Board (Leaders: who leads each stat; Movers: whose role is growing, the old Pool, a mode since 2026-09-25), Grid (weekly usage), News |
| Bets | Parlay, DFS |
| Gameday | Live |

The view is in the hash (`#usage`, `#roster`), so a reload, a bookmark and Back all land where they
point; the group is derived from the leaf, and only the view is in the URL (the grid's position and
week reset on purpose). `tests/test_render.py::test_a_hash_opens_its_view` pins it. One exception:
the Board's Movers mode is `#movers`, and the old `#pool` opens it, because Movers was a view and
bookmarks point at it (`test_movers_hash_opens_the_board_in_movers`).

With no hash, `navDefaultLeaf` in `js/chrome/nav.js` opens Board (rosters barely move; stats and
news move daily) except on a Tuesday, when Waivers still leads.

`NAV` in `js/chrome/nav.js` is the whole table; a group of one draws no sub-row. Every copy key is
spelled out literally, because `assemble.py --check` finds orphaned keys by scanning for literal
lookups and cannot see one built from a template. The sub-row lives **outside** `.navbar`: on a
phone the navbar is fixed to the bottom edge, and a `.modes-sub.dock` inside it lands in the slot
Parlay's and DFS's own switchers already occupy. Adding a view = one entry in `NAV`, one copy key,
one branch in `render()`.

Player search (2026-09-22) is not a view: no `NAV` entry, no hash. It is the bar's fifth slot on a
phone and `/` on a desktop; `js/data/search.js` joins every live player row by slug and ranks,
`js/chrome/search.js` is the sheet. Overlays push a URL-less history entry (`js/chrome/layers.js`),
so Back closes the profile, then search, before it ever changes the view.

## Staying current in an open tab

The page carries its data inside itself, so a tab left open holds the build it loaded with, however
long it sits there. No cache header helps — the tab never asks again, and Vercel already serves the
page `max-age=0, must-revalidate`, so a reload is always fresh. **Do not add a `max-age`**: it would
only introduce staleness that does not exist today.

`build.json` (written by `design/build.py`, folded in by `land.ps1` like the two pages) holds a hash
of the injected data — never a clock, or every rebuild would claim new data. `js/chrome/fresh.js`
fetches it on a tab click and on the window regaining focus, never on a timer: the refresh runs once
a day and the week turns on a Tuesday. A different hash turns the DATA pill into a reload control,
naming the new week when there is one. Only over http(s); from `file://` there is nothing to ask.

## Data

`design/sources.py` owns every read of an ff-jarvis file or feed block (feed first, file as
fallback); `design/build.py` orchestrates and no longer loads. It reads rosters, props, prop model,
player projections, Sleeper status, the DFS pool, and `usage_weekly.json` (the Grid, via
`design/usage.py`, whose feed key is `usage_grid` — plain `usage` is already watch.json), and
A visitor's own ESPN league is read at runtime by `api/league.py`, never baked in (DESIGN.md,
"Connected leagues"). `wire_watch` (the Waivers Breaking rail, via `design/wire_watch.py`; its field lists live in `contract.py`). DFS projections come from ff-jarvis's `model.market.projections`; the page never
computes model numbers itself. See `README.md` for the DFS CSV import and `design/DESIGN.md` for
the design system and the field contract.
