"""A league's scoring rules, from the words its own site uses, as terms over Sleeper's stat names.

The one table of its kind: the build (design/gameday.py) and, later, a connected league's read
(api/league.py) both call it, and the page scores every player with them (js/data/gameday/score.js).
Verified 2026-09-28 by scoring week 2 from Sleeper's stats: all 12 ESPN teams and all 108 started
Yahoo players matched the official numbers to the hundredth.

A term is {"s": [sleeper keys, summed], "p": points} plus at most one of
  "per": n   whole units of n, truncated toward zero (ESPN's "every 20 passing yards")
  "frac": n  the value over n, unrounded (Yahoo's "25 yards per point")
  "lo"/"hi"  1 when lo <= value <= hi (hi None: open) -- a bonus or a points-allowed tier
Rules are {"off": [term], "dst": [term], "unknown": [rules this table cannot read], "gaps": [rules it
reads but Sleeper keeps no stat for]}; a D/ST scores by "dst", everyone else, kickers included, by
"off". An unknown rule is reported, never guessed; a gap is a rare play (a 1-point safety).
"""
import re

T = lambda *s, **kw: {"s": list(s), **kw}

# ESPN statId -> (term for a player, term for a D/ST). The D/ST term uses the item's slot-16 override.
# Unverified keys (no week 2 instance) are marked "unseen"; the rest matched week 2 exactly.
ESPN = {
    1: (T("pass_cmp"), None), 2: (T("pass_inc"), None), 4: (T("pass_td"), None),
    7: (T("pass_yd", per=20), None), 15: (T("pass_td_40p"), None), 16: (T("pass_td_50p"), None),
    17: (T("pass_yd", lo=300, hi=399), None), 18: (T("pass_yd", lo=400, hi=None), None),      # 18 unseen
    19: (T("pass_2pt"), None), 20: (T("pass_int"), None),                                      # 19 unseen
    25: (T("rush_td"), None), 26: (T("rush_2pt"), None), 28: (T("rush_yd", per=10), None),
    35: (T("rush_td_40p"), None), 36: (T("rush_td_50p"), None),                                # unseen
    37: (T("rush_yd", lo=100, hi=199), None), 38: (T("rush_yd", lo=200, hi=None), None),       # 38 unseen
    43: (T("rec_td"), None), 44: (T("rec_2pt"), None), 45: (T("rec_td_40p"), None),            # 44 unseen
    46: (T("rec_td_50p"), None), 48: (T("rec_yd", per=10), None), 53: (T("rec"), None),
    56: (T("rec_yd", lo=100, hi=199), None), 57: (T("rec_yd", lo=200, hi=None), None),         # 57 unseen
    63: (T("fum_rec_td"), None), 72: (T("fum_lost"), None),                                    # 63 unseen
    # Kickers (no K slot in the league it was verified on: all unseen)
    77: (T("fgm_40_49"), None), 80: (T("fgm_0_19", "fgm_20_29", "fgm_30_39"), None),
    85: (T("fgmiss"), None), 86: (T("xpm"), None), 88: (T("xpmiss"), None),
    198: (T("fgm_50_59"), None), 201: (T("fgm_60p"), None),
    # Returns: a player's own, and a D/ST's
    101: (T("kr_td"), T("def_st_td")), 102: (T("pr_td"), None),          # Sleeper lumps KR+PR TDs for a D/ST
    103: (T("int_ret_td"), T("def_td")), 104: (T("fum_ret_td"), None),   # and INT+fumble return TDs
    117: (T("kr_yd", per=25), T("def_kr_yd", per=25)), 118: (T("pr_yd", per=10), T("def_pr_yd", per=10)),
    # D/ST
    89: (None, T("pts_allow", lo=0, hi=0)), 90: (None, T("pts_allow", lo=1, hi=6)),
    91: (None, T("pts_allow", lo=7, hi=13)), 92: (None, T("pts_allow", lo=14, hi=17)),
    123: (None, T("pts_allow", lo=28, hi=34)), 124: (None, T("pts_allow", lo=35, hi=45)),
    125: (None, T("pts_allow", lo=46, hi=None)),
    128: (None, T("yds_allow", lo=0, hi=99)), 129: (None, T("yds_allow", lo=100, hi=199)),
    130: (None, T("yds_allow", lo=200, hi=299)),
    132: (None, T("yds_allow", lo=350, hi=399)), 133: (None, T("yds_allow", lo=400, hi=449)),
    134: (None, T("yds_allow", lo=450, hi=499)), 135: (None, T("yds_allow", lo=500, hi=549)),
    136: (None, T("yds_allow", lo=550, hi=None)),
    95: (None, T("int")), 96: (None, T("fum_rec")), 97: (None, T("blk_kick")), 98: (None, T("safe")),
    99: (None, T("sack")), 106: (None, T("ff")), 206: (None, T("def_2pt")),                   # 206 unseen
    93: (None, None), 209: (None, None),     # blocked-kick return TD, 1-pt safety: Sleeper has neither
}
# Any other statId a league scores (another league's 18-27 points-allowed tiers, say) lands in
# `unknown` and the page says its score may differ, rather than this table guessing an id.


def espn_rules(items):
    """[[statId, points, D/ST points or None]] (ff-jarvis espn_league.json `scoring`) -> rules."""
    off, dst, unknown, gaps = [], [], [], []
    for stat, pts, dpts in items or []:
        if not (pts or dpts):
            continue
        if stat not in ESPN:
            unknown.append(str(stat))
            continue
        o, d = ESPN[stat]
        if not o and not d:
            gaps.append(str(stat))
        if o and pts:
            off.append({**o, "p": pts})
        dp = pts if dpts is None else dpts
        if d and dp:
            dst.append({**d, "p": dp})
    return {"off": off, "dst": dst, "unknown": unknown, "gaps": gaps}


# Yahoo's own label -> (term keys, D/ST or not). Ranges come from the label ("0-19 Yards", "35+ points").
YAHOO = {
    "Passing Yards": ("pass_yd",), "Passing Touchdowns": ("pass_td",), "Interceptions": ("pass_int",),
    "Rushing Yards": ("rush_yd",), "Rushing Touchdowns": ("rush_td",), "Receptions": ("rec",),
    "Receiving Yards": ("rec_yd",), "Receiving Touchdowns": ("rec_td",), "Return Touchdowns": ("kr_td", "pr_td"),
    "2-Point Conversions": ("pass_2pt", "rush_2pt", "rec_2pt"), "Fumbles Lost": ("fum_lost",),
    "Offensive Fumble Return TD": ("fum_rec_td",),
    "Field Goals 0-19 Yards": ("fgm_0_19",), "Field Goals 20-29 Yards": ("fgm_20_29",),
    "Field Goals 30-39 Yards": ("fgm_30_39",), "Field Goals 40-49 Yards": ("fgm_40_49",),
    "Field Goals 50+ Yards": ("fgm_50p",), "Field Goals Missed 0-19 Yards": ("fgmiss_0_19",),
    "Field Goals Missed 20-29 Yards": ("fgmiss_20_29",), "Field Goals Missed 30-39 Yards": ("fgmiss_30_39",),
    "Field Goals Missed 40-49 Yards": ("fgmiss_40_49",), "Field Goals Missed 50+ Yards": ("fgmiss_50p",),
    "Point After Attempt Made": ("xpm",), "Point After Attempt Missed": ("xpmiss",),
    "Field Goals Total Yards": ("fgm_yds",),
}
YAHOO_DST = {
    "Sack": ("sack",), "Interception": ("int",), "Fumble Recovery": ("fum_rec",), "Touchdown": ("def_td",),
    "Safety": ("safe",), "Block Kick": ("blk_kick",), "Kickoff and Punt Return Touchdowns": ("def_st_td",),
    "Extra Point Returned": ("def_2pt",),                                                     # unseen
}
PER = re.compile(r"^(\d+(?:\.\d+)?) yards per point$")
PTS_ALLOWED = re.compile(r"^Points Allowed (\d+)(?:-(\d+)|(\+))? points$")


def _value(v):
    """Yahoo's cell -> {"p": .., "frac": ..} or None: "25 yards per point", "0.5", "-1"."""
    m = PER.match(v)
    if m:
        return {"p": 1.0, "frac": float(m.group(1))}
    try:
        return {"p": float(v)}
    except ValueError:
        return None


def yahoo_rules(rows):
    """[[group, label, value]] (ff-jarvis yahoo_settings.json `scoring`) -> rules."""
    off, dst, unknown = [], [], []
    for _group, label, value in rows or []:
        v = _value(value)
        pa = PTS_ALLOWED.match(label)
        if v is None:
            unknown.append(label)
        elif pa:
            lo = int(pa.group(1))
            hi = None if pa.group(3) else int(pa.group(2) or lo)
            if v["p"]:
                dst.append({"s": ["pts_allow"], "lo": lo, "hi": hi, "p": v["p"]})
        elif label in YAHOO:
            if v["p"]:
                off.append({"s": list(YAHOO[label]), **v})
        elif label in YAHOO_DST:
            if v["p"]:
                dst.append({"s": list(YAHOO_DST[label]), **v})
        elif v["p"]:
            unknown.append(label)
    return {"off": off, "dst": dst, "unknown": unknown, "gaps": []}
