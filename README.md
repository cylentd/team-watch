# Team Watch

A console for two fantasy football teams — one on Yahoo, one on ESPN. It answers one question per
player: **what moved, and what do I do about it.**

Live: deployed on Vercel from `index.html`.

| # | Surface | What it shows |
|---|---|---|
| 01 | My teams | roster board with trend sparkline, position rank, news badge; player drawer; waiver swap cards; the players who start for **both** teams |
| 02 | The pool | every player who logged a snap, on a usage-against-luck scatter — role growing, points lagging, and the four quadrants that follow |
| 03 | Builder | parlay slip with model-vs-book edge and a correlated-legs warning, or a DFS lineup against a salary cap |

Rosters and team names are pulled live from the `draft-war-room` repo. Trend, rank, news, pool and
builder content are sample data, replaced later by the `team-watch` skill. See
[design/DESIGN.md](design/DESIGN.md) for the data contract and the design system.

## Build

```
python design/build.py
```

Edit `design/template.html`, never the generated files. The build writes two copies of the same
page: `index.html` at the root (full HTML document, what Vercel serves) and `design/index.html`
(fragment, what the Artifact publisher takes). Player headshots are inlined as data URIs, so
both files work offline.

The build also reads `draft-war-room/data/{espn_rosters,league_rosters}.json` and injects the live
rosters. If those files are missing it falls back to the copies inside the template, so the page
always renders.

## Layout

```
design/template.html   source — all markup, CSS and sample data
design/build.py        inlines headshots, writes both outputs
design/DESIGN.md       design system + the field contract the skill must supply
index.html             generated — do not edit
```
