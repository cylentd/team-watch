"""Who left the game hurt: the play-by-play scan (data/gameday/hurt.js gdHurtScan), in Node.

The scan is pure: a summary and the players to watch in, who is hurt out. It is pinned here against
nflverse's wording ("PHI-S.Barkley was injured during the play.", "** Injury Update: PHI-J.Hurts has
returned to the game."); what the page draws from it is test_left_hurt.py, in the browser. Moved out
of the browser 2026-10-05, where these ten tests shared a loaded page for no reason but the function."""
import pytest

# Two lines copied from games/2026_03_PHI_CHI.json and games/2026_02_PHI_TEN.json (nflverse wording).
REAL_INJURED = "S.Barkley left guard to PHI 28 for no gain (J.Simmons). PHI-S.Barkley was injured during the play."
REAL_RETURNED = "J.Hurts pass short right to D.Wicks pushed ob at PHI 46 for 13 yards (C.Lewis). ** Injury Update: PHI-J.Hurts has returned to the game."
# Real lines too: a defender hurt on a play my QB ran; and a trap, where the ball carrier's name sits just
# before the injured player's own ("M.Evans. SF-M.Evans").
REAL_DEFENDER = "J.Hurts scrambles left tackle to CHI 27 for 20 yards (X.Woods). CHI-C.Lewis was injured during the play."
REAL_TRAP = "B.Purdy pass incomplete short middle to M.Evans. SF-M.Evans was injured during the play."
REAL_STUKES = "O.Hampton up the middle to LV 26 for 7 yards (J.McCoy; T.Stukes). ** Injury Update: LV-T.Stukes has returned to the game."

HURTS_OUT = "J.Hurts pass incomplete short left to D.Smith. PHI-J.Hurts was injured during the play."


def me(slug, name, team):
    return {"slug": slug, "name": name, "team": team}


NAMES = {
    "s.barkley": [me("saquon-barkley", "Saquon Barkley", "PHI")],
    "j.hurts": [me("jalen-hurts", "Jalen Hurts", "PHI")],
    "t.stukes": [me("tre-stukes", "Tre Stukes", "LV")],
    "m.evans": [me("mike-evans", "Mike Evans", "SF")],
    "b.purdy": [me("brock-purdy", "Brock Purdy", "SF")],
    "j.williams": [me("jameson-williams", "Jameson Williams", "DET")],
}


def play(text, q=2, clock="9:41"):
    return {"text": text, "period": {"number": q}, "clock": {"displayValue": clock}}


def summary(clubs, plays):
    """ESPN's shape: drives.previous[] then drives.current, plays in order. The plays split across both."""
    k = max(len(plays) - 1, 0)
    return {"header": {"competitions": [{"competitors": [{"team": {"abbreviation": c}} for c in clubs]}]},
            "drives": {"previous": [{"plays": plays[:k]}], "current": {"plays": plays[k:]}}}


@pytest.fixture(scope="module")
def hurt(node_js):
    # gdSameClub is Live's (nflnow.js); GD_ALIAS, the schedule's code pairs, is live.js's, planted here.
    return node_js("surface/live/nflnow.js", "data/gameday/hurt.js", globals={"GD_ALIAS": {"WSH": "WAS"}})


def scan(hurt, clubs, plays, names=NAMES):
    return hurt("gdHurtScan", summary(clubs, plays), names)


def test_my_starter_is_flagged_and_a_defender_not_in_names_is_ignored(hurt):
    got = scan(hurt, ["PHI", "CHI"], [play(REAL_DEFENDER, 1, "3:02"), play(REAL_INJURED, 2, "9:41")])
    assert got == [{"slug": "saquon-barkley", "name": "Saquon Barkley", "team": "PHI", "q": 2, "clock": "9:41", "back": False}]
    # the QB named in the defender's line is not hurt: he only ran the ball
    assert scan(hurt, ["PHI", "CHI"], [play(REAL_DEFENDER)]) == []


def test_a_return_clears_him_and_a_second_injury_flags_him_again(hurt):
    got = scan(hurt, ["PHI", "CHI"], [play(HURTS_OUT, 3, "4:12"), play(REAL_RETURNED, 3, "2:30")])
    assert got == [{"slug": "jalen-hurts", "name": "Jalen Hurts", "team": "PHI", "q": 3, "clock": "4:12", "back": True}]
    again = scan(hurt, ["PHI", "CHI"], [play(HURTS_OUT), play(REAL_RETURNED), play(HURTS_OUT, 4, "1:00")])
    assert [(h["slug"], h["back"], h["q"]) for h in again] == [("jalen-hurts", False, 4)]
    # a return for someone never seen hurt in this summary is no news
    assert scan(hurt, ["PHI", "CHI"], [play(REAL_RETURNED)]) == []


@pytest.mark.parametrize("text", [
    "LV-T.Stukes was injured during the play.",
    "T.Stukes was injured during the play.",
    "T. Stukes was injured during the play.",
    "LV-T. Stukes was injured during the play.",
    "O.Hampton up the middle to LV 26 for 7 yards (J.McCoy; T.Stukes). LV-T.Stukes was injured during the play.",
])
def test_both_spellings_of_an_abbreviated_name_match(hurt, text):
    got = scan(hurt, ["LV", "LAC"], [play(text)])
    assert [h["slug"] for h in got] == ["tre-stukes"]


def test_the_real_return_line_for_stukes_clears_him_in_either_spelling(hurt):
    for spelled in (REAL_STUKES, REAL_STUKES.replace("LV-T.Stukes", "LV-T. Stukes")):
        got = scan(hurt, ["LV", "LAC"], [play("LV-T.Stukes was injured during the play."), play(spelled)])
        assert [(h["slug"], h["back"]) for h in got] == [("tre-stukes", True)]


def test_the_name_before_the_injured_players_is_not_taken_for_his(hurt):
    got = scan(hurt, ["SF", "ARI"], [play(REAL_TRAP)])
    assert [h["slug"] for h in got] == ["mike-evans"]


def test_a_club_in_the_text_must_be_his_and_two_in_one_play_are_both_read(hurt):
    # J.Williams on BUF is not my DET starter; with no club in the text he must play in this game
    assert scan(hurt, ["BUF", "HOU"], [play("BUF-J.Williams was injured during the play.")]) == []
    assert scan(hurt, ["DET", "BUF"], [play("DET-J.Williams was injured during the play.")])[0]["slug"] == "jameson-williams"
    assert scan(hurt, ["BUF", "HOU"], [play("J.Williams was injured during the play.")]) == []
    both = scan(hurt, ["PHI", "CHI"], [play("PHI-S.Barkley was injured during the play. PHI-J.Hurts was injured during the play.")])
    assert sorted(h["slug"] for h in both) == ["jalen-hurts", "saquon-barkley"]


def test_the_schedules_spelling_of_a_club_matches_sleepers(hurt):
    names = {"t.mclaurin": [me("terry-mclaurin", "Terry McLaurin", "WAS")]}
    got = scan(hurt, ["WSH", "DAL"], [play("T.McLaurin was injured during the play.")], names)
    assert [h["slug"] for h in got] == ["terry-mclaurin"]


def test_a_summary_without_plays_flags_nobody(hurt):
    for s in (None, {}, {"drives": {}}, {"drives": {"previous": [{}], "current": {}}}, summary(["PHI", "CHI"], [])):
        assert hurt("gdHurtScan", s, NAMES) == []
