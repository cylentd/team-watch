# Team Watch style guide

The rules every view follows. `DESIGN.md` records what each view decided; this file is the test a
new or changed view must pass before it lands. Colour, type and lint rules stay in `DESIGN.md`
("Direction", "Theme rules") and are not repeated here.

## Controls: one job per view, one row above the data

A reader on a phone scrolls to reach data, never to get past controls.

| Rule | Why | Where it was learned |
|---|---|---|
| One job per view. Two questions are two views in the sub-row, not a mode switch inside one. | A switch is a row of controls; a view tab costs nothing new. | Leaders and Movers (2026-09-25): data moved from 251px to 197px |
| At most one row of controls between the sub-row and the data. | Every row pushes the answer down. | Board, 5 rows to 4; Movers 3 |
| A filter is chosen once per surface. Two views that share a filter share one setting. | The same choice twice reads as two different things. | Parlay's two kickoff selects |
| No sideways scroll inside a page that scrolls down. Exception: a row of video thumbnails may scroll sideways when it is one row, the next card shows past the edge, and nothing else in the view scrolls sideways. | Two axes to scroll is a maze on a phone. A thumbnail rail is the one shape where a cut-off card says "more" better than buttons do. | Parlay's slip carousel; the exception: Roster clips, 2026-10-05; a second dated exception, 2026-10-05: Live's scoreboard strip, one row of matchup chips above the score head, the next chip showing past the edge, nothing else on My league scrolling sideways (the TDs chip row and the phone's tab row scroll the same way, as one row of controls) |
| A sideways swipe only turns to the next thing in a set the reader can already page with buttons; a pull down from the top only closes a sheet or modal (see Overlays). One meaning per surface, both from `lib/swipe.js`, never a swipe between views. | The same finger meaning two things on one screen is a guess. | Leaders stat, Preview game, profile tab, game sheet game; profile, search, game sheet close (2026-09-29). Live's league on Matchup and League (superseded 2026-10-05: the strip replaced it); the game sheet walks the Games tab's order and names the game on each side (2026-10-04) |
| A row of up to ~6 siblings stays visible (tabs, chips). A dropdown is for many options or rare changes. | A dropdown hides the options and costs two taps. | Sub-tabs kept over dropdowns (2026-09-25) |
| What the reader builds (a slip, a lineup) lives on the bottom edge as a tray, not mid-page. | The thumb is already there, from any view. | Parlay slip, 875px down |
| The row holds the filter changed most; the rest goes behind a settings chip at its end that names what is set (`chrome/setchip.css`). | One row that fits beats a row that scrolls its last options off the edge. | Grid (12 controls) and DFS (3 rows), audit 2026-09-25 |
| A table too wide for a phone splits each row onto two lines; it never hides a column or scrolls. | Every number stays, with its label above it. | Grid and the DFS pool, audit 2026-09-25 |

Budget, at 360x800, measured in the browser: **the first data starts by ~200px**. A view over it
names the reason in its `DESIGN.md` section.

## Phone chrome: header bar, one tab row, bottom bar

Decided 2026-10-05 (David: groups to a bottom tab bar, a header bar "like Yahoo and Sleeper", "Tab opens in
place"; storyboard https://claude.ai/artifact/ArF53Lvh12QV8fbL3mr9KP). Detail in `DESIGN.md` "The phone's chrome".

| Rule | Why | Where it was learned |
|---|---|---|
| On a phone the chrome is three layers: a header bar (the reader's team, Ask), one tab row, a bottom bar (Week, League, Stats, Bets, Search). | One thumb reaches the groups and search at the bottom edge; the team and Ask are the two things a reader changes rarely. The Yahoo and Sleeper pattern. | The groups sat at the top from 2026-09-24; back to the bottom 2026-10-05 |
| A view's own tabs open in place inside the tab row, in the open view's pill. A view draws no second tab bar of its own on a phone. | Two rows of tabs are two rows of controls before the data (Controls, above); one row that opens in place costs none. | Live, Recap and Slips (`data/tabrow.js`, 2026-10-05) |
| A new view with tabs declares them with `navModes`, never draws its own bar above the data on a phone. | The row is the one place a reader looks for a view's tabs. | `tests/test_js_tabrow.py` |

## Overlays: a bottom sheet is for doing, a centred modal for reading

David, 2026-10-05: "I don't like modals popping up from the bottom … I think we are using it wrong."

| Rule | Why | Where it was learned |
|---|---|---|
| A bottom sheet holds only a short action on what was just tapped: pick a line, add a leg, choose an option. It fits on the screen with no scroll of its own (David, 2026-10-05; "about half the screen" until the leg sheet measured 61% and was kept). | The thumb is already at the bottom edge, and nothing scrolls inside the scrolling page. | The Slips line sheet; the leg sheet (2026-10-05) |
| Something to read (a game, a player, a team) opens as a centred modal: a margin on all four sides on a phone, a max-width on a desktop, closed by ✕, a tap on the scrim or Back. Too long for one modal: a full page with Back. Never a bottom sheet, and never one that slides up full screen. | A reading sheet is a scroll inside a scrolling page, and its pull-down close fights that scroll. | League > Teams, sheets to full pages (2026-10-05); the Live game sheet (2026-10-05) |
| On a phone a reading modal also closes from a footer at its bottom edge: a Close button within the thumb's reach (a game's Prev · Close · Next, 48px), besides the ✕, the scrim and Back, which stay. | The ✕ sits at the top, the farthest point from a one-handed thumb. | The Live game sheet (2026-10-05) |
| On a desktop nothing docks to the bottom edge but the tray. | A phone-shaped panel stretched along a wide screen reads as a mistake. | The game sheet from 960px |

Bottom sheets on 2026-10-05, and what each holds: the slip sheet the tray grows into
(`builder/bets.css`, an action: keep), the leg sheet (`builder/legsheet.css`, an action: keep; 475 of
780px, no scroll of its own), the Slips player sheet
(`builder/playersheet.css`, reading: a centred modal since 2026-10-05), the Live game sheet
(`live/gamesheet.css`, reading: a centred modal since 2026-10-05), and chat on a phone
(`chat/chat.css`, a conversation: its own call). The player profile is already a centred modal
(`#modal`), and so are its orb and compare layers.

## Layout: nothing reflows under the reader

- **Mobile first.** Build and check at 360px, then desktop. About 90% of readers are on a phone.
- **Fixed-size siblings.** Cards in a grid are one size: a fixed row count with empty slots, not a
  height that follows the content. A page turn then swaps cards without moving the grid.
  (Movers cards, 2026-09-25.)
- **Measure, never guess.** A size that depends on the screen is read in the reader's browser at
  render (`board/fit.js`): a page of rows is one screen, whatever the screen is.
- **Share edges.** Two blocks side by side share a top and a bottom edge; a block that floats
  centred inside a taller one reads as a mistake. (Leaders card, 2026-09-25.)
- **Desktop fills the width it has.** A 3x3 grid, a hero beside its list; never one stretched
  column with bars a thousand pixels long.
- **A label stays within 560px of its value.** A row that pins its name to one edge and its number
  to the other (`space-between`, a `flex:1` label, a `1fr` track) reads as two facts on a desktop.
  A wide pane gets columns, or the row a max-width. (Profile, 2026-09-29, flagged twice in one day:
  usage bars 988px wide, then Bio draft picks 1,100px from their league;
  `test_desktop_panes_sit_side_by_side_and_a_phone_stacks_them`.)
- **Rows, not columns.** A desktop page of sections pairs them in rows of like height (ranking
  beside heists) and gives a long section the full width with its cards two across. Never split the
  sections into a left and a right column by kind: the columns end ~1000px apart and the short one
  leaves a hole. Check: sections side by side end within 150px of each other. (Trades, 2026-09-28:
  1730px beside 705px; `test_trades_desktop_rows_end_level`.)

## Alignment: by what the reader does with it

Alignment follows the reading direction, not habit. Decided 2026-09-30, after the Compare cards
(a round photo over a left-aligned name and number) read as off-centre.

| Content | Align | Why |
|---|---|---|
| Lists, rows, tables, paragraphs, labels down a column | Left | The eye returns to one left edge each line; centred lines are ragged on both sides |
| A column of like numbers read downward (a stat column in a list) | One edge, the same every row | Digits line up so the column compares at a glance |
| A small card that stacks items: a face or icon over a name over a number | Centre | The round face is symmetric; left-aligned, the card leaves a lopsided gap on its right |
| A lane per subject in a side-by-side compare, one short value per row, read across | Centre in its lane | The value sits on the lane's middle line, under its subject's header and card |

A row of centred lanes takes its label on its own line above it, left-aligned, so the lanes keep
the full width and line up with whatever sits above them (Compare's strips under its cards; a
label column beside the lanes pushed them off the cards' and the graph's centre, 2026-09-30).

## Motion: feedback that shows the change

Every motion answers the reader's hand and ends where the thing now lives. The motion carries the
information; if it says nothing a still frame does not, cut it.

1. **Nothing moves on its own, except data arriving and a tap cue.** No idle loops, no timers.
   Rewritten 2026-09-28 (David found "nothing moves on its own" too restrictive): a thing the reader
   can tap may move slowly to say so. It runs only while it is on screen and the tab is visible,
   rests regularly where its data reads, never moves text, and is still under reduced motion. The
   first is the profile's sphere (`surface/profile/orb.js`): one turn in 14 s, then 2 s at rest.
   The Trades loops below predate this rule and stay as dated exceptions.
   Exception (David, 2026-09-28): League > Trades shuffles its decided-a-season cards every 10 s,
   only on screen, paused under a pointer or after a touch, off under reduced motion, after Show all
   and on a phone (which swipes instead) (`surface/trades/alive.js`). Rule 4 still holds: the swap
   never happens under a hand. The filling bar that announced it is gone (David: "too distracting"),
   superseded 2026-09-28; the new cards drop in one after another instead.
   Exception (David, 2026-09-28: "I was imagining mist around the card"): the purple mist around
   each Trades curse card drifts on an 11 s loop. It sits behind the card's panel, so it moves no
   text; off under reduced motion.
2. **A motion ends at the thing's new home.** A pick flies to the tray; a loaded slip's legs drop
   in one by one; a page's cards slide in from the side the page turned.
3. **The motion is the data change.** A bar grows from the old value to the new one; a percentage
   rolls to its new number; the "all legs hit" bar draws after the legs, shorter.
4. **Never move what is being read.** A kept card slides to its new place (FLIP); only cards that
   leave fade. Enter animations fire when the view's content changed, not on every tap
   (`markEnter`, `js/chrome/motion.js`).
5. **Reduced motion gets every end state, instantly.** `responsive/motion.css` does it globally;
   JS motion checks `prefers-reduced-motion` and jumps to the end.

| Beat | Token | Use |
|---|---|---|
| Press | `--press` scale, `--spring` | every control under a finger |
| Move | `--spring` over `--dur-spring` (460ms, 5.7% overshoot) | anything that answers a hand: slides, sheets, lifts |
| Pop | `--spring-pop` over `--dur-pop` (690ms, 16%) | one small thing landing: a count, a check |
| Draw | `--ease` | bars and meters filling to a value |
| Stagger | `--enter-step` (28ms) per item | a set arriving; legs landing use ~70ms so each is counted |
| Lift | `--lift` (-3px) | a card under a pointer, hover devices only |

The springs are `linear()` curves sampled from a damped spring (`tokens.css`); no motion library
loads. A new curve or duration is a new token, never a literal in a component.

## Before a view lands

1. Screenshot it at 360px, then desktop, including the next page and an empty state. On the
   desktop shot, check every row whose label and value sit at opposite edges (Layout, above),
   and every block against the Alignment table.
2. Measure where the first data starts; it is ~200px or less, or the reason is written down.
3. Page, filter and tap through it: nothing jumps, and every motion ends where its thing lives.
4. Every interaction has a render test (`tests/test_render.py`), and the golden diff shows only
   this view.
5. Its cards pass Material Design's rule (`DESIGN.md`, "Cards"): one card per subject, rows
   inside it, never a card in a card. Its states and reasons pass "Say it in a shape" (the same
   file): tags, meters and pills, every code named on screen, no prose where a pill fits.
6. `tests/test_style_rules.py` passes: nothing scrolls sideways at 360px (Leaders' faded stat
   tabs are the one exception) and nothing loops while the page is idle.

The playable motion reference is the Bets storyboard, published 2026-09-25:
https://claude.ai/artifact/LQVFzVaNCNKhWWBHzHAL7L
