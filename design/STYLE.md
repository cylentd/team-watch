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
| No sideways scroll inside a page that scrolls down. | Two axes to scroll is a maze on a phone. | Parlay's slip carousel |
| A row of up to ~6 siblings stays visible (tabs, chips). A dropdown is for many options or rare changes. | A dropdown hides the options and costs two taps. | Sub-tabs kept over dropdowns (2026-09-25) |
| What the reader builds (a slip, a lineup) lives on the bottom edge as a tray, not mid-page. | The thumb is already there, from any view. | Parlay slip, 875px down |
| The row holds the filter changed most; the rest goes behind a settings chip at its end that names what is set (`chrome/setchip.css`). | One row that fits beats a row that scrolls its last options off the edge. | Grid (12 controls) and DFS (3 rows), audit 2026-09-25 |
| A table too wide for a phone splits each row onto two lines; it never hides a column or scrolls. | Every number stays, with its label above it. | Grid and the DFS pool, audit 2026-09-25 |

Budget, at 360x800, measured in the browser: **the first data starts by ~200px**. A view over it
names the reason in its `DESIGN.md` section.

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

## Motion: feedback that shows the change

Every motion answers the reader's hand and ends where the thing now lives. The motion carries the
information; if it says nothing a still frame does not, cut it.

1. **Nothing moves on its own.** No idle loops, no timers. The one exception is data arriving.
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

1. Screenshot it at 360px, then desktop, including the next page and an empty state.
2. Measure where the first data starts; it is ~200px or less, or the reason is written down.
3. Page, filter and tap through it: nothing jumps, and every motion ends where its thing lives.
4. Every interaction has a render test (`tests/test_render.py`), and the golden diff shows only
   this view.
5. `tests/test_style_rules.py` passes: nothing scrolls sideways at 360px (Leaders' faded stat
   tabs are the one exception) and nothing loops while the page is idle.

The playable motion reference is the Bets storyboard, published 2026-09-25:
https://claude.ai/artifact/LQVFzVaNCNKhWWBHzHAL7L
