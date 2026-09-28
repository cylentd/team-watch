"""design/wx_kicked.py: the last forecast before each kickoff, in LIVE_WEATHER's own row shape."""
import sys

from conftest import REPO

sys.path.insert(0, str(REPO / "design"))
from wx_kicked import kicked   # noqa: E402

row = lambda team, ko, at, wind=10, roof="outdoor": {"team": team, "kickoff": ko, "as_of": at, "roof": roof,
                                                      "temp_f": 60, "wind_mph": wind, "precip_pct": 5, "short": "Sunny"}


def test_the_last_forecast_before_kickoff_wins_and_a_later_fetch_is_not_a_forecast():
    out = kicked([row("BUF", "2026-09-27T17:00:00Z", "2026-09-26T12:00:00+00:00", 8),
                  row("BUF", "2026-09-27T17:00:00Z", "2026-09-27T07:57:43+00:00", 13),
                  row("BUF", "2026-09-27T17:00:00Z", "2026-09-27T18:00:00+00:00", 30)])     # after kickoff
    assert out["BUF"] == [{"roof": "outdoor", "kickoff": "2026-09-27T17:00:00Z", "as_of": "2026-09-27T07:57:43+00:00",
                           "temp_f": 60, "wind": "13 mph", "short": "Sunny", "precip_pct": 5}]


def test_each_kickoff_keeps_its_own_forecast_and_domes_are_skipped():
    out = kicked([row("CHI", "2026-09-20T17:00:00Z", "2026-09-20T08:00:00+00:00"),
                  row("CHI", "2026-09-27T17:00:00Z", "2026-09-27T08:00:00+00:00"),
                  row("DET", "2026-09-27T17:00:00Z", "2026-09-27T08:00:00+00:00", roof="dome")])
    assert [r["kickoff"] for r in out["CHI"]] == ["2026-09-20T17:00:00Z", "2026-09-27T17:00:00Z"]
    assert "DET" not in out
