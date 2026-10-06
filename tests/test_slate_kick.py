"""design/slate.py hands the page an ISO time beside every kickoff label (2026-10-05).

The page writes kickoffs in the reader's clock from that time (js/lib/kick.js); the Pacific label is the
fallback, in the page's one format ("Sun 5:15 PM", not "Sun 5:15p")."""
import slate


def rows():
    out = []
    for commence in ("2026-10-02 00:15:00", "2026-10-04 17:00:00", "2026-10-04 20:25:00", "2026-10-06 00:15:00"):
        base, label, t = slate.kickoff(commence)
        out.append({"slot": base, "kick": label, "commence": commence, "_t": t, "game": commence})
    return out


def test_the_fallback_label_is_the_pages_one_format():
    assert [r["kick"] for r in rows()] == ["Thu 5:15 PM", "Sun 10:00 AM", "Sun 1:25 PM", "Mon 5:15 PM"]


def test_a_window_is_named_by_its_eastern_slot_whatever_the_build_clock():
    """The window's `slot` is Preview's (design/preview.py): the league's Eastern clock, not the Pacific bucket
    the key still comes from. The 1 PM ET wave is "Sunday early" in a New York reader's clock and a Los Angeles
    one's alike; before 2026-10-05 it was "Sunday Morning"."""
    rows_ = rows() + [dict(zip(("slot", "kick", "commence", "_t", "game"), (*slate.kickoff(c)[:2], c, slate.kickoff(c)[2], c)))
                      for c in ("2026-10-04 13:30:00", "2026-10-04 23:20:00", "2026-10-04 17:00:00")]
    by_key = {w["k"]: w["slot"] for w in slate.assign_windows(rows_)}
    assert by_key == {"evening-thu": "thu", "morning": "sun1", "afternoon": "sunlate", "evening-sun": "sunnight",
                      "evening-mon": "mon"}


def test_preview_and_bets_share_one_slot_function():
    import preview
    assert preview._slot("2026-10-04T17:00:00Z")[0] == "sun1" == slate.et_slot(slate.dt.datetime(2026, 10, 4, 17, tzinfo=slate.UTC))[0]
    assert slate.et_slot(slate.dt.datetime(2026, 10, 4, 13, 30, tzinfo=slate.UTC))[0] == "sunam", "9:30 AM ET, London"
    assert slate.et_slot(slate.dt.datetime(2026, 10, 5, 0, 15, tzinfo=slate.UTC))[0] == "sunnight", "8:15 PM ET Sunday"
    assert slate.et_slot(slate.dt.datetime(2026, 10, 6, 0, 15, tzinfo=slate.UTC))[0] == "mon"


def test_a_window_and_a_day_carry_their_first_kickoff_as_utc():
    ws = slate.assign_windows(rows())
    assert {w["k"]: w["at"] for w in ws} == {"evening-thu": "2026-10-02T00:15:00Z", "morning": "2026-10-04T17:00:00Z",
                                             "afternoon": "2026-10-04T20:25:00Z", "evening-mon": "2026-10-06T00:15:00Z"}
    days = slate.day_windows(ws)
    assert [(d["k"], d["at"]) for d in days] == [("day-2026-10-04", "2026-10-04T17:00:00Z")]
