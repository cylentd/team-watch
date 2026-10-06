"""Start/Sit's shared pieces (data/startsit.js) in Node: the kickoff and matchup words a row prints,
and the record's own reading. The rows that print them are checked in the browser (test_startsit*)."""
import pytest


@pytest.fixture(scope="module")
def ss(node_js):
    # The kickoff is the page's one format (lib/kick.js) in the reader's clock; the test pins Pacific.
    return node_js("lib/kick.js", "data/startsit.js", globals={"KICK_TZ": "America/Los_Angeles"})


def test_kickoff_is_the_one_kickoff_format_without_a_comma(ss):
    assert ss("muKick", {"kick": "2026-10-04T17:00:00Z"}) == "Sun 10:00 AM"
    assert ss("muKick", {"kick": "2026-10-05T00:15:00Z"}) == "Sun 5:15 PM"     # still Sunday in Pacific
    assert ss("muKick", {"kick": None}) is None


def test_the_calls_own_club_comes_first(ss):
    assert ss("muVs", {"team": "DAL", "opp": "BAL", "home": True}) == "DAL vs BAL"
    assert ss("muVs", {"team": "LAC", "opp": "BUF", "home": False}) == "LAC @ BUF"
    assert ss("muVs", {"team": "LAC", "opp": None}) == "LAC"


def test_clubs_are_escaped(ss):
    assert ss("muVs", {"team": "<i>", "opp": "BUF", "home": True}) == "&lt;i&gt; vs BUF"


def test_the_game_line_adds_the_kickoff_only_when_there_is_one(ss):
    row = {"team": "CIN", "opp": "PIT", "home": False}
    assert ss("muGame", {**row, "kick": "2026-10-04T17:00:00Z"}) == "CIN @ PIT · Sun 10:00 AM"
    assert ss("muGame", row) == "CIN @ PIT"


def blank():
    return {k: {"hit": 0, "miss": 0, "void": 0} for k in ("smash", "start", "sit")} | {"weeks": []}


def test_a_record_counts_once_any_call_is_graded(ss):
    assert ss("ss3Graded", blank()) is False
    assert ss("ss3Graded", blank() | {"weeks": [4]}) is True
    voided = blank()
    voided["sit"]["void"] = 1                     # a voided call was graded all the same
    assert ss("ss3Graded", voided) is True
    assert ss("ss3Wl", {"hit": 5, "miss": 2}) == "5-2"


# ---- the picker's opening state and the FantasyPros row (plan U3, 2026-10-05) ----

def test_a_reader_with_no_team_opens_on_search_not_on_someone_elses_pair(ss):
    # The audit's first-time visitor landed on a preset pair he did not choose: 8 taps to his own.
    assert ss("ssOpening", {"team": False, "kept": None, "closest": ["a", "b"]}) == {"picks": [], "open": True}


def test_an_owner_opens_on_his_closest_call_with_the_list_shut(ss):
    assert ss("ssOpening", {"team": True, "kept": None, "closest": ["bench", "starter"]}) == {"picks": ["bench", "starter"], "open": False}


def test_an_owner_with_no_close_call_opens_on_search(ss):
    assert ss("ssOpening", {"team": True, "kept": None, "closest": []}) == {"picks": [], "open": True}


def test_picks_kept_this_week_win_over_everything(ss):
    assert ss("ssOpening", {"team": False, "kept": ["x", "y"], "closest": ["a", "b"]}) == {"picks": ["x", "y"], "open": False}
    # Kept as an empty list means he cleared the card on purpose: search again, never the closest call.
    assert ss("ssOpening", {"team": True, "kept": [], "closest": ["a", "b"]}) == {"picks": [], "open": True}


def col(slug, pos, pts):
    return {"p": {"slug": slug, "pos": pos, "n": slug.title()}, "pts": pts}


FP = {"harvey": {"pos": "RB", "ecr": 31}, "allen": {"pos": "RB", "ecr": 22}, "tate": {"pos": "WR", "ecr": 9}}


def test_fantasypros_contradicts_when_its_experts_rank_the_loser_ahead(ss):
    cols = [col("harvey", "RB", 12.1), col("allen", "RB", 9.4)]
    got = ss("ssFpCheck", cols, {"flip": False, "win": cols[0], "gap": 2.7}, FP)
    assert got == {"kind": "contradicts", "ours": "harvey", "theirs": "allen"}


def test_fantasypros_agrees_when_the_winner_is_ranked_ahead(ss):
    cols = [col("harvey", "RB", 12.1), col("allen", "RB", 9.4)]
    got = ss("ssFpCheck", cols, {"flip": False, "win": cols[0], "gap": 2.7}, {**FP, "harvey": {"pos": "RB", "ecr": 12}})
    assert got == {"kind": "agrees", "ours": "harvey", "theirs": None}


def test_no_comparison_for_a_coin_flip_two_positions_or_a_missing_rank(ss):
    rb = [col("harvey", "RB", 12.1), col("allen", "RB", 11.9)]
    assert ss("ssFpCheck", rb, {"flip": True, "gap": 0.2}, FP) is None
    mixed = [col("harvey", "RB", 12.1), col("tate", "WR", 9.4)]            # an RB rank and a WR rank are not one list
    assert ss("ssFpCheck", mixed, {"flip": False, "win": mixed[0], "gap": 2.7}, FP) is None
    gap = [col("harvey", "RB", 12.1), col("nobody", "RB", 9.4)]
    assert ss("ssFpCheck", gap, {"flip": False, "win": gap[0], "gap": 2.7}, FP) is None
    assert ss("ssFpCheck", rb, None, FP) is None


def test_the_contradiction_note_names_the_player_fantasypros_prefers(ss):
    note = ss("ssFpNote", {"kind": "contradicts", "ours": "harvey", "theirs": "allen"}, {"harvey": "R. Harvey", "allen": "B. Allen"})
    assert "B. Allen" in note and "R. Harvey" in note
    assert ss("ssFpNote", {"kind": "agrees", "ours": "harvey", "theirs": None}, {}) == ""
    assert ss("ssFpNote", None, {}) == ""
