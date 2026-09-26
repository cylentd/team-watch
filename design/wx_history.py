"""LIVE_WX_HISTORY: ff-jarvis's weather backtest (model/season/weather_backtest.py, METHODOLOGY
12.53), summarised per condition into the two questions This week > Weather asks a casual reader.

1. Does it matter? Arm "a": points a game against the player's normal (his recent games and the
   opponent). A position whose arm-a cell passes is listed with its mean; the rest have "no clear
   effect". When none passes, the position that came closest (most of the four checks, then the
   biggest number) is named with why it fell short: "rolling" (it does not hold up season to
   season) or "noisy" (the range, the t or the sample size).
2. Already in our projections? From the projections' own `weather_adjust` block (ff-jarvis adds
   the proven cells to its projections from `since` on). For the positions that matter: those in
   the block's cells are in, kickers are not projected at all, the rest are not in yet. Without
   the block the question is not asked.

The page prints these summaries and computes nothing. The thresholds ship too, because they define
the conditions. The backtest file is optional: without it the block is None and no lines draw.
"""

POS = ["QB", "RB", "WR", "TE", "K"]
CHECKS = ["n", "ci", "t", "rolling"]
UNPROJECTED = {"K"}


def _cell(c):
    return {"pos": c["position"], "mean": c["mean"], "n": c["n"], "lo": c["lo"], "hi": c["hi"]}


def _reason(c):
    checks = c.get("checks") or {}
    only_rolling = not checks.get("rolling") and all(checks.get(k) for k in ("n", "ci", "t"))
    return "rolling" if only_rolling else "noisy"


def _inproj(passing, adjusted):
    """{yes, no, kickers} over the positions that matter, or None without an adjust block."""
    if adjusted is None or not passing:
        return None
    pos = [c["position"] for c in passing]
    return {"yes": [p for p in pos if p in adjusted and p not in UNPROJECTED],
            "no": [p for p in pos if p not in adjusted and p not in UNPROJECTED],
            "kickers": any(p in UNPROJECTED for p in pos)}


def _condition(cells, adjusted):
    arm_a = {c["position"]: c for c in cells if c.get("arm") == "a"}
    order = [arm_a[p] for p in POS if p in arm_a]
    passing = sorted((c for c in order if c["passes"]), key=lambda c: -abs(c["mean"]))
    top = None
    if not passing and order:
        best = max(order, key=lambda c: (sum(bool((c.get("checks") or {}).get(k)) for k in CHECKS), abs(c["mean"])))
        top = {"pos": best["position"], "mean": best["mean"], "reason": _reason(best)}
    return {"matters": [_cell(c) for c in passing],
            "unproven": [c["position"] for c in order if not c["passes"]],
            "top": top,
            "inproj": _inproj(passing, adjusted),
            "why": [_cell(c) for c in order]}


def live_wx_history(raw, proj=None):
    """-> {"seasons", "thresholds", "since", "conditions": {name: summary}} or None. `proj` is the
    projections block; its `weather_adjust` (when present) answers the second question."""
    if not raw or not isinstance(raw.get("cells"), list):
        return None
    names = sorted({c.get("condition") for c in raw["cells"] if c.get("arm") == "a" and c.get("condition")})
    if not names:
        return None
    adjust = (proj or {}).get("weather_adjust") if isinstance(proj, dict) else None
    cells = (adjust or {}).get("cells") or {}
    th = raw.get("thresholds") or {}
    return {"seasons": raw.get("seasons"),
            "thresholds": {"wind_mph": th.get("wind_mph"), "cold_f": th.get("cold_f")},
            "since": (adjust or {}).get("since"),
            "conditions": {n: _condition([c for c in raw["cells"] if c.get("condition") == n],
                                         set(cells.get(n) or {}) if adjust else None) for n in names}}


def report(block):
    if not block:
        return "Weather history: no backtest file, so no history lines"
    shown = ", ".join(f"{n} {len(s['matters'])}/5" for n, s in block["conditions"].items())
    adj = f"in projections since {block['since']}" if block["since"] else "no projections adjust block"
    return f"Weather history: positions where it matters: {shown}; {adj}"
