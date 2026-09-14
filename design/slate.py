"""Kickoff times and the windows a slip is built from: which games share a slate, on whose clock.

BettingPros gives kickoff in UTC; everything here is on David's clock (Pacific). build.py calls
kickoff() per row, assign_windows() once over the rows, day_windows() over the windows.
"""
import datetime as dt
import zoneinfo

LOCAL_TZ = zoneinfo.ZoneInfo("America/Los_Angeles")
UTC = dt.timezone.utc


def kickoff(commence):
    """BettingPros gives kickoff in UTC. Bucket it on David's clock: the 1pm-ET wave is morning,
    the 4pm wave afternoon, everything from the night windows (Thu, Sun, Mon) evening. This is
    only the raw time-of-day bucket (`base`) -- it says nothing about which calendar date the
    game falls on, which is why `assign_windows` below exists as a second pass. `t` is the
    localized datetime, returned so that pass can group by `t.date()` (never the raw UTC
    string: a 5:20pm Pacific kickoff is after midnight UTC the next day, so slicing `commence`
    directly would put it on the wrong date)."""
    try:
        t = dt.datetime.strptime(commence, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC).astimezone(LOCAL_TZ)
    except (TypeError, ValueError):
        return None, None, None
    base = "morning" if t.hour < 12 else "afternoon" if t.hour < 16 else "evening"
    label = t.strftime("%a %I:%M%p").replace(" 0", " ").replace("AM", "a").replace("PM", "p")
    return base, label, t


def assign_windows(rows):
    """Split each time-of-day bucket (`base`) by calendar date, so a slip built from one window
    never mixes two different days -- the bug this exists to fix: "evening" alone can hold
    Thursday Night, Sunday Night and Monday Night, three different dates in the same week.

    A base with only one date that week keeps its plain label ("Evening"). A base with more
    than one date splits per date, labeled by weekday ("Thursday Night", "Monday Night") --
    applied to all three bases, not just evening, since a late-season Saturday slate can put
    real games in the morning/afternoon hour bands on two different dates too.

    Writes the resulting window key onto each row as `win` (kept separate from `slot`, the raw
    3-value time-of-day bucket -- `win` is the date-safe grouping key and its set of values is
    not stable week to week). Returns the ordered list of windows, chronological by kickoff.
    """
    by_base = {}
    for p in rows:
        t = p.pop("_t", None)
        if t is None:
            continue
        by_base.setdefault(p["slot"], {}).setdefault(t.date(), []).append((p, t))

    windows = []
    for base in ("morning", "afternoon", "evening"):
        dates = by_base.get(base)
        if not dates:
            continue
        multi = len(dates) > 1
        for d, entries in dates.items():
            if multi:
                key = f"{base}-{d:%a}".lower()
                label = f"{d:%A} Night" if base == "evening" else f"{d:%A} {base.capitalize()}"
            else:
                key = base
                label = base.capitalize()
            # Collision guard: two dates sharing a weekday name only happens if a pull ever
            # spans two weeks; disambiguate rather than silently merging them.
            if any(w["k"] == key for w in windows):
                key, label = f"{key}-{d.day}", f"{label} ({d.day})"
            for p, t in entries:
                p["win"] = key
            windows.append({
                "k": key, "label": label, "short": label.upper(), "date": d.isoformat(),
                "kick": min(entries, key=lambda e: e[1])[0]["kick"],
                "n": len(entries), "games": len({p["game"] for p, _ in entries}),
                "_when": min(t for _, t in entries),
            })
    windows.sort(key=lambda w: w["_when"])
    for w in windows:
        del w["_when"]
    return windows


def day_windows(windows):
    """One whole-day grouping per date that has more than one window (a Sunday: morning, afternoon,
    night). Safe where a whole-slate card was not: every window in it is the same calendar date.
    `wins` lists the window keys a leg may come from."""
    by_date = {}
    for w in windows:
        by_date.setdefault(w["date"], []).append(w)
    days = []
    for d, ws in by_date.items():
        if len(ws) < 2:
            continue
        name = dt.date.fromisoformat(d).strftime("%A")
        days.append({"k": f"day-{d}", "label": f"All {name}", "short": f"ALL {name.upper()}", "date": d,
                     "kick": ws[0]["kick"], "wins": [w["k"] for w in ws],
                     "n": sum(w["n"] for w in ws), "games": sum(w["games"] for w in ws)})
    return days
