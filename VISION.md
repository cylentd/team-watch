# Vision (team-watch)

Where this page is going. The conductor reads it before sizing work here and appends dated decisions; David edits it freely. Format: the `conductor` skill, section 4. Seeded 2026-10-07 from TODO.md, CLAUDE.md, design/DESIGN.md and design/STYLE.md.

## Direction

- Readers are David and friends in his Yahoo and ESPN leagues, mostly on a 360px phone.
- The page answers one question per player: what moved, and what do I do about it.
- Each weekday has one job: the Digest leads with that day's answer, and research is one tap away.
- It renders ff-jarvis data and never computes model numbers.
- Focus, in David's order (2026-10-08); work outside these five is nice to have:
  1. An amazing home landing page for users.
  2. Accurate rankings and matchup analysis.
  3. Simpler parlay research, and getting better at picking hits.
  4. A better journey for viewing a roster and researching its players and potential trades.
  5. Previewing games and following them live.
  All five are on the site already; the work is improving, redesigning and polishing them, not building them anew (David).
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
- 2026-10-08: chose one pick per Slips line, model and Claude as one "our pick": "users dont need to understand if claude or model is better" (David).
- 2026-10-08: chose Home as the fantasy week for everyone, nothing personal, over a personal Home: "how is home different from roster view then?" (David). The reader's own team lives in Team. Home is its own tab: Home · Team · Matchup · Players · League, Search in the header, Bets under Matchup; each weekday's job leads; draft B adds a week tier sheet.
- 2026-10-08: chose a page per player for trades (Get every package for him, Send each team's best return) over a filter on the finder or a locked Edit page (David, trade draft B).
- 2026-10-08: chose show over tell: no legends or explainer blocks; the content must explain itself ("show not tell is our design principles", David).
- 2026-10-08: dropped ff-jarvis's SLEEPER tag ("a starter on the waiver almost never happens") and show POTENTIAL under the name SLEEPER (David).
- 2026-10-08: chose four focus areas over the Later list (Yahoo sign-in, chain trades, Follow a game): "they're nice to have. I rather focus on the vision" (David).
- 2026-10-08: chose the Home hero's face in a slanted pane at the band's right edge, club code on its edge (draft C), over a trading card or a medallion: the sign behind the face "looks ok mobile but awkward on wider screens" and the face rising from the bottom "looks like a whack a mole" (David).
- 2026-10-09: chose the headline leading Preview's game page, players right after it, over players on top: "i dont exactly love the players on top. The headline is gone!" (David).
- 2026-10-09: chose Back leaving the view over Back stepping through a view's own tabs (Live, Recap, Ranks' Rest of season) (David).
- 2026-10-09: chose Ranks printing our own projection, with order and tiers from it, everywhere the page shows a player's week (David, reapproving the tests that pinned the books' order).
- 2026-10-09: chose a default, consistent landing view for every group over returning to the last view seen: the last view "is confusing as we want to reduce mental load on the user" (David).
- 2026-10-09: chose Start/Sit leading with the reader's own lineup and our one swap (draft A) over a compare-first or a by-position page; every call, running backs too, decided by our points, never the books (David).
- 2026-10-09: chose News as an injury report (each player's Sunday word and Wed-Fri practice), blended with player rows on Tuesday, over a filtered feed; facts only, no lineup instructions: "I dont like the Bench him because we are not linked to their fantasy app" (David).
- 2026-10-09: chose Ranks drawing ff-jarvis's week_ranks rank and tier as shipped, now that ff-jarvis orders them on our own points, over re-sorting here; the "No line" tag and the books' RB note are gone (David).
- 2026-10-09: chose a tier ladder with the rank on each name for week ranks on Home, and fantasy team avatars as a Teams list plus a picker grid, over a dot chart, packs or avatars on today's cards (David, storyboards a + d).

## Not doing

- No `max-age` cache header: Vercel already revalidates, and a max-age would only add staleness.
- No roster data on public views (Weather names no roster; the page is public).
- No automated scrape of the Yahoo DFS pool: the contest CSV is imported by hand.
- No fantasy points in Digest headlines.
- No private leagues: public leagues only, "too hard to support private ones" (David, 2026-10-08). The ESPN QR fallback is dropped with it.
- 2026-10-08: dropped the Highlights view: "the information is not useful" (David); each line repeated a number its own view already shows.
