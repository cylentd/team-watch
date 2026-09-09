# Team Watch — design mock

`design/index.html` is a self-contained mock. Open it directly, or rebuild after editing
`template.html`:

```
python design/build.py
```

`build.py` inlines headshots from `draft-war-room/app/public/heads` as data URIs, so the built
file works offline and as a published Artifact.

## Direction

Signal Desk — a dark trading-terminal console. The roster is a portfolio; the page answers
"what moved, and what do I do about it".

| Token | Meaning |
|---|---|
| lime `#c8ff2e` | active, starter, brand |
| green `#37e08b` | trending up |
| red `#ff5a52` | trending down |
| amber `#ffb020` | caution, stale data, questionable |
| violet / red marks | Yahoo / ESPN league identity only |

Positions are typographic, never coloured. Type: Bricolage Grotesque (display), Space Grotesk
(UI), JetBrains Mono (all numerals).

## What the skill has to supply

One object per player. Everything below is placeholder in the mock.

| Field | Type | Drives |
|---|---|---|
| `trend` | number[6] or `null` | row sparkline; `null` renders the dashed no-data baseline |
| `d` | number or `null` | delta chip (±%) |
| `rank` | `[posRank, poolSize, weekMove, percentile]` | rank cell + percentile bar |
| `news` | int | badge count; `hot: 1` turns it lime |
| `status` | `"Q"` / `"OUT"` / `null` | head badge + name pill + Out group |
| `note` | string | red callout at the top of the drawer |

Drawer sections (`why it moved`, news list, against-the-league bars) read the same object.
The wire panel takes `{out, in_, gain, faab, team}` swap objects.

## States already styled

Empty (no games played), loading skeletons, error (401 / token expired), stale (cached ranks).
They are rendered in a "Component states" strip at the bottom so nothing falls back to browser
defaults when the feed is missing.

## Verified 2026-09-08

Desktop 1400px and phone 390px, no horizontal overflow on either. Rosters are real: Yahoo from
`draft-war-room/data/league_rosters.json`, ESPN from `~/.claude/docs/projects/espn-league-2026.md`.
Trend, rank, news and wire content are sample data.
