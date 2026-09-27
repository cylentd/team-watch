"""LIVE_WX_HISTORY: ff-jarvis's weather backtest (model/season/weather_backtest.py, METHODOLOGY
12.53), cut to what This week > Weather prints (reworked 2026-09-26: only what moves scoring).

Per condition:
- `matters`: the positions whose arm-a cell passes (points a game against the player's own recent
  games and the opponent), each with its mean, in the page's position order. The page sums these
  across the conditions a game meets, the way the projection adds its cells (12.54).
- `tested`: every position the backtest has an arm-a cell for, so the page can name what was
  tested and showed nothing (domes, running backs).
- `inproj`: {yes, no, kickers} over `matters`, from the projections' own `weather_adjust` cells;
  None without that block.

`thresholds` define the conditions: wind and cold from the backtest, the rain chance and the roof
the projections adjust for from `weather_adjust` (None without it, and then rain never applies).
The page computes no threshold of its own. The backtest file is optional: without it the block
is None and the view draws only the forecast.
"""

POS = ["QB", "WR", "TE", "K", "RB"]
UNPROJECTED = {"K"}


def _inproj(passing, adjusted):
    """{yes, no, kickers} over the positions that matter, or None without an adjust block."""
    if adjusted is None or not passing:
        return None
    return {"yes": [p for p in passing if p in adjusted and p not in UNPROJECTED],
            "no": [p for p in passing if p not in adjusted and p not in UNPROJECTED],
            "kickers": any(p in UNPROJECTED for p in passing)}


def _condition(cells, adjusted):
    arm_a = {c["position"]: c for c in cells if c.get("arm") == "a"}
    order = [arm_a[p] for p in POS if p in arm_a]
    passing = [c for c in order if c["passes"]]
    return {"matters": [{"pos": c["position"], "mean": c["mean"]} for c in passing],
            "tested": [c["position"] for c in order],
            "inproj": _inproj([c["position"] for c in passing], adjusted)}


def live_wx_history(raw, proj=None):
    """-> {"seasons", "thresholds", "since", "conditions": {name: summary}} or None. `proj` is the
    projections block; its `weather_adjust` (when present) answers "already in our projections"."""
    if not raw or not isinstance(raw.get("cells"), list):
        return None
    names = sorted({c.get("condition") for c in raw["cells"] if c.get("arm") == "a" and c.get("condition")})
    if not names:
        return None
    adjust = (proj or {}).get("weather_adjust") if isinstance(proj, dict) else None
    cells = (adjust or {}).get("cells") or {}
    th, ath = raw.get("thresholds") or {}, (adjust or {}).get("thresholds") or {}
    return {"seasons": raw.get("seasons"),
            "thresholds": {"wind_mph": th.get("wind_mph"), "cold_f": th.get("cold_f"),
                           "precip_pct": ath.get("precip_pct"), "roof": ath.get("roof")},
            "since": (adjust or {}).get("since"),
            "conditions": {n: _condition([c for c in raw["cells"] if c.get("condition") == n],
                                         set(cells.get(n) or {}) if adjust else None) for n in names}}


def report(block):
    if not block:
        return "Weather history: no backtest file, so no history lines"
    shown = ", ".join(f"{n} {len(s['matters'])}/{len(s['tested'])}" for n, s in block["conditions"].items())
    adj = f"in projections since {block['since']}" if block["since"] else "no projections adjust block"
    return f"Weather history: positions where it matters: {shown}; {adj}"
