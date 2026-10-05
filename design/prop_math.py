"""Two small pieces of prop arithmetic, split out of build.py to keep it in budget (2026-10-05)."""

# Where the model's rate sits relative to the book's line across the whole slate (week 1 2026:
# medians 1.12 rush, 1.13 rec, 1.01 receptions, 0.94 pass), and how far from that a line can be
# before it is read as a role change rather than a disagreement.
STALE_CENTRE = {"RUSH": 1.12, "REC": 1.10, "RECS": 1.0, "PASS": 0.93}
STALE_BAND = 1.35


def is_stale(mkt, mu, line):
    r0 = STALE_CENTRE.get(mkt, 1.0)
    ratio = mu / line
    return ratio > r0 * STALE_BAND or ratio < r0 / STALE_BAND


def implied(american):
    """Break-even probability of an American price, vig included."""
    a = float(american)
    return 100.0 / (a + 100.0) if a > 0 else -a / (-a + 100.0)
