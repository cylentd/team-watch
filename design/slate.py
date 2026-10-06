"""Kickoff times and the windows a slip is built from: which games share a slate, on whose clock.

BettingPros gives kickoff in UTC; everything here is on David's clock (Pacific). build.py calls
kickoff() per row, assign_windows() once over the rows, day_windows() over the windows.
"""
import datetime as dt
import zoneinfo
from collections import Counter

LOCAL_TZ = zoneinfo.ZoneInfo("America/Los_Angeles")
EASTERN = zoneinfo.ZoneInfo("America/New_York")
UTC = dt.timezone.utc


def et_slot(when):
    """(slot, the kickoff in Eastern time) for an aware datetime: the league's own window, by Eastern weekday
    and hour. The one definition: Preview's slate (design/preview.py `_slot`) and the Bets windows both read it,
    so a window has the same name in both (2026-10-05). thu / mon, sunam (before 1 PM ET: the London game),
    sun1 (the 1 PM wave), sunlate (4 PM), sunnight, else day."""
    t = when.astimezone(EASTERN)
    day, h = t.strftime("%a"), t.hour
    slot = {"Thu": "thu", "Mon": "mon"}.get(day) or (day == "Sun" and (
        "sunam" if h < 13 else "sun1" if h < 16 else "sunlate" if h < 19 else "sunnight")) or "day"
    return slot, t


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
    # The page's one kickoff format (js/lib/kick.js), on David's clock. Only the fallback: the page
    # rewrites every label from the row's own UTC time, in the reader's clock.
    label = f"{t:%a} {t.hour % 12 or 12}:{t.minute:02d} {'AM' if t.hour < 12 else 'PM'}"
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
            first = min(entries, key=lambda e: e[1])
            # Named by the league's Eastern slot (Preview's names, in the page), not by the Pacific bucket the
            # key still comes from: the slot most of its games fall in (the earlier on a tie), so the one London
            # game of a Sunday joins the 1 PM wave's window, as it did, and the tabs stay six. The page writes
            # the words (data/kickwin.js), because its times are in the reader's clock.
            slot = Counter(et_slot(t)[0] for _, t in sorted(entries, key=lambda e: e[1])).most_common(1)[0][0]
            windows.append({
                "k": key, "label": label, "short": label.upper(), "slot": slot, "date": d.isoformat(),
                "kick": first[0]["kick"], "at": first[1].astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
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
                     "kick": ws[0]["kick"], "at": ws[0]["at"], "wins": [w["k"] for w in ws],
                     "n": sum(w["n"] for w in ws), "games": sum(w["games"] for w in ws)})
    return days
