"""The Digest's pure functions, in Node (data/digest.js, data/navmap.js; 2026-10-06).

Moved out of tests/test_digest.py, where each one cost a browser and a page load to call a function
that reads no DOM: the short name two players on a team share, where the Recap row ends, and which
tab opens Stats. What the Digest draws from them is tests/test_digest*.py, in the component layer.
"""
import pytest

KICK_MON = "2026-10-06T00:15:00Z"      # Monday 5:15 PM Pacific; Mon or Tue in every zone from UTC-12 to UTC+11


@pytest.fixture
def digest(node_js):
    return node_js("data/digest.js", globals={"LIVE_SCHEDULE": {"games": []}})


@pytest.mark.req("Digest", ac="two players on one team with one short name keep their first names")
def test_two_players_one_team_one_short_name_keep_their_first_names(digest):
    """ATL has Bijan and Brian Robinson (2026-09-29, David: "two B. Robinson on ATL ... confusing"):
    a short form two players on one team share keeps the first name; one on two teams stays short."""
    digest("globalThis.searchIndex = () => [{n: 'Bijan Robinson', slug: 'bijan-robinson', team: 'ATL'},"
           " {n: 'Brian Robinson Jr.', slug: 'brian-robinson', team: 'ATL'},"
           " {n: 'Zed Quill', slug: 'zed-quill', team: 'SF'}, {n: 'Zack Quill', slug: 'zack-quill', team: 'NYJ'}]")
    assert [digest("dgShort", n) for n in ("Bijan Robinson", "Brian Robinson Jr.", "Zed Quill")] == [
        "Bijan Robinson", "Brian Robinson", "Z. Quill"]


@pytest.mark.req("Digest", ac="a short name drops a suffix and keeps a single word whole")
def test_a_short_name_drops_a_suffix_and_a_single_word_stays_whole(digest):
    digest("globalThis.searchIndex = () => []")
    assert [digest("dgShort", n) for n in ("Travis Etienne Jr.", "Michael Pittman Jr", "Jaxon Smith-Njigba", "Kyren Williams", "Ceedee")] == [
        "T. Etienne", "M. Pittman", "J. Smith-Njigba", "K. Williams", "Ceedee"]


@pytest.mark.req("Digest", ac="the Recap row ends at the reader's midnight after the first Wednesday")
def test_the_recap_end_is_thursday_midnight_after_the_weeks_last_kickoff(digest):
    """The end is the reader's own midnight: Thursday 00:00 local, to the minute, after the last kickoff
    and less than four days after it."""
    recap = {"week": 4, "games": [{"kickoff": "2026-10-04T17:00:00Z"}, {"kickoff": KICK_MON}]}
    end = digest("""r => { const e = dgRecapEnd(r), d = new Date(e);
      return [e, d.getDay(), d.getHours(), d.getMinutes(), Math.max(...r.games.map(g => Date.parse(g.kickoff)))]; }""", recap)
    assert end[1:4] == [4, 0, 0]
    assert end[0] > end[4] and end[0] - end[4] < 4 * 86400e3


@pytest.mark.req("Digest", ac="a recap with no kickoff to count from has no end")
def test_a_recap_with_no_kickoff_has_no_end(digest):
    assert digest("dgRecapEnd", {"week": 4, "games": [{"kickoff": None}, {}]}) is None


@pytest.mark.req("Digest", ac="the schedule's kickoffs of the recap's week count too")
def test_the_schedule_counts_when_the_recap_has_no_kickoff(node_js):
    js = node_js("data/digest.js", globals={"LIVE_SCHEDULE": {"games": [{"week": 4, "kickoff": KICK_MON}, {"week": 5, "kickoff": "2026-10-12T17:00:00Z"}]}})
    end = js("r => { const d = new Date(dgRecapEnd(r)); return [d.getDay(), d.getHours(), d.getMinutes()]; }", {"week": 4, "games": [{"kickoff": None}]})
    assert end == [4, 0, 0]


@pytest.mark.req("Navigation: one League group, Stats", ac="Stats opens on Highlights")
def test_the_stats_tab_opens_on_highlights(node_js):
    """David, 2026-10-04: the Digest lost its Highlights section; the Players tab keeps them, first."""
    nav = node_js("data/navmap.js")
    assert nav("NAV.find(([g]) => g === 'scouting')[1][0]") == "highlights"
