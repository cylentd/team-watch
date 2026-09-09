# Team Watch

A roster console for two fantasy football teams — one on Yahoo, one on ESPN. It answers one
question per player: **what moved, and what do I do about it.**

Live: deployed on Vercel from `index.html`.

| Panel | What it shows |
|---|---|
| Roster board | six-week sparkline, delta %, position rank vs the league, unread news count |
| Player drawer | bigger trend chart, why it moved, news list, your player against all 12 rosters |
| The wire | waiver swap cards — drop → add, lineup delta, suggested FAAB bid |
| Combined view | the players who start for **both** teams, where one injury costs two lineups |

The page is a design mock. Rosters are real; trend, rank, news and waiver content are sample
data, replaced later by the `team-watch` skill. See [design/DESIGN.md](design/DESIGN.md) for the
data contract and the design system.

## Build

```
python design/build.py
```

Edit `design/template.html`, never the generated files. The build writes two copies of the same
page: `index.html` at the root (full HTML document, what Vercel serves) and `design/index.html`
(fragment, what the Artifact publisher takes). Player headshots are inlined as data URIs, so
both files work offline.

## Layout

```
design/template.html   source — all markup, CSS and sample data
design/build.py        inlines headshots, writes both outputs
design/DESIGN.md       design system + the field contract the skill must supply
index.html             generated — do not edit
```
