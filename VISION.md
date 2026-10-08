# Vision (team-watch)

Where this page is going. The conductor reads it before sizing work here and appends dated decisions; David edits it freely. Format: the `conductor` skill, section 4. Seeded 2026-10-07 from TODO.md, CLAUDE.md, design/DESIGN.md and design/STYLE.md.

## Direction

- Readers are David and friends in his Yahoo and ESPN leagues, mostly on a 360px phone.
- The page answers one question per player: what moved, and what do I do about it.
- Each weekday has one job: the Digest leads with that day's answer, and research is one tap away.
- It renders ff-jarvis data and never computes model numbers.
- Good looks like: nav that maps to Yahoo, ESPN and Sleeper habits (team, matchup, players, league), few tabs, chrome that stands apart from content, no endless scroll.

## Decisions

- 2026-09-29: chose a Preview slate plus a dossier per game, after David asked for "more research and evaluation of this matchup".
- 2026-10-05: chose yards and TDs over fantasy points in Digest headlines because "every league scores differently" (David).
- 2026-10-05: chose a bottom tab bar on a phone, for one-handed reach (David).
- 2026-10-05: chose centred modals over bottom sheets for reading, because a pull-down close fights the page scroll.
- 2026-10-06: chose award stamps in display type over grey chips because "grey chips read clinical" (David).
- 2026-10-06: chose a Digest with one job per Pacific weekday because it should hold "something that people actually care about" (David).
- 2026-10-07: chose five Digest cards a day over two because "a day of two cards was too thin" (David).
- 2026-10-07: chose trade offers judged on four lenses (Now, Push, Playoff run, ROS) over ROS alone: "ROS gain is one lens, not the gate" (David).
- 2026-10-07: chose a header and tab row that stay put on a phone scroll over ones that hide and return, because nothing should slide at the edge of the eye.
- 2026-10-07: chose a group tab that opens its first view on every click, Tuesday included (League opens Roster), over returning to the last view seen (David).
- 2026-10-08: chose our own rank and tiers, with Vegas as a supporting input, over the books' rank: "the rank was always supposed to be our own ranking system. if we use someone's else's, then what's the point?" Like borischen, keep only the sources that test accurate year to year and average them (ff-jarvis #40).
- 2026-10-08: chose Bold calls without a test-status label: "it's intentional murky and it's a take... a mini test every week" (David). Other model marks keep theirs.
- 2026-10-08: chose nav draft C (Team · Matchup · Players · League · Search, 28 tabs) as the target, reached through draft B's label-only regroup first (David).
- 2026-10-08: chose Slips grouped by kickoff window, each window showing the best call per game (David).
- 2026-10-08: chose the chrome its own darker surface, edge and shadow (David).

## Not doing

- No `max-age` cache header: Vercel already revalidates, and a max-age would only add staleness.
- No roster data on public views (Weather names no roster; the page is public).
- No automated scrape of the Yahoo DFS pool: the contest CSV is imported by hand.
- No fantasy points in Digest headlines.
