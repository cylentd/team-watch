"""design/news.py's report fields (ledger #95, 2026-10-09): Players > News as an injury report.

The build reads each headline once and hands the page what it states: the game-day word ("ruled out" is Out),
the practice day a practice line is about, the fantasy player the story is about, and the teammates the
scanner's read names as the next man up. The page only draws them. Every headline here is a real 2026-10-08/09
FantasyPros one."""
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "api"))
from _espn import slugify  # noqa: E402
from news import game_status, practice_day, news_report, news_people, check_practice_report  # noqa: E402

pytestmark = pytest.mark.req("News", ac="the injury report")


@pytest.mark.parametrize("title, word", [
    ("Saquon Barkley (hamstring) officially ruled out Sunday ", "out"),
    ("Jordan Mason (thumb) expected to return in Week 7", "out"),
    ("Justin Jefferson (ankle) listed questionable Sunday ", "questionable"),
    ("Terry McLaurin (hamstring) to be game-time decision Sunday ", "questionable"),
    ("Chris Olave (foot) off injury report Sunday ", "cleared"),
    ("Malik Nabers (knee) will play Sunday ", "cleared"),
    ("Tee Higgins (groin/neck) officially doesn't practice Thursday", "dnp"),
    ("Lamar Jackson (ankle) not seen practicing Thursday ", "dnp"),
    ("Alvin Kamara (back) officially limited Thursday", "limited"),
    ("Tony Pollard (foot) returns to practice in full Thursday", "full"),
    ("Tyler Shough (hand) upgraded to full participant Thursday", "full"),
])
def test_a_headline_states_one_game_day_word(title, word):
    assert game_status(title) == word


@pytest.mark.parametrize("title", [
    "Rhamondre Stevenson (knee) 'not ruled out yet' Sunday ",   # not ruled out is not Out
    "Ja'Marr Chase remains in concussion protocol ",
    "",
    None,
])
def test_a_headline_with_no_game_day_word_states_none(title):
    assert game_status(title) is None


@pytest.mark.parametrize("title, day", [
    ("Alvin Kamara (back) officially limited Thursday", "Thu"),
    ("Pat Bryant (ankle) misses practice Wednesday", "Wed"),
    ("Ashton Jeanty (ankle/foot) not practicing Friday ", "Fri"),
])
def test_a_practice_line_names_its_day(title, day):
    assert practice_day(title, game_status(title)) == day


def test_a_game_day_line_is_no_practice_day_even_when_it_names_one():
    title = "Justin Jefferson (ankle) listed questionable Sunday "
    assert practice_day(title, game_status(title)) is None
    assert practice_day("Kyle Monangai (toe) ruled out Friday", "out") is None


STATUS = {
    "saquon barkley": {"name": "Saquon Barkley", "pos": "RB", "team": "PHI", "injury": "Out"},
    "will shipley": {"name": "Will Shipley", "pos": "RB", "team": "PHI", "injury": None},
    "dameon pierce": {"name": "Dameon Pierce", "pos": "RB", "team": "PHI", "injury": None},
    "kenneth gainwell": {"name": "Kenneth Gainwell", "pos": "RB", "team": "PHI", "injury": None},
    "lamar jackson": {"name": "Lamar Jackson", "pos": "QB", "team": "BAL", "injury": "IR"},
    "tyler huntley": {"name": "Tyler Huntley", "pos": "QB", "team": "BAL", "injury": None},
    "michael penix": {"name": "Michael Penix Jr.", "pos": "QB", "team": "ATL", "injury": None},
    "tee higgins": {"name": "Tee Higgins", "pos": "WR", "team": "CIN", "injury": "Questionable"},
    "isaiah likely": {"name": "Isaiah Likely", "pos": "TE", "team": "BAL", "injury": "Doubtful"},
    "brandon aubrey": {"name": "Brandon Aubrey", "pos": "K", "team": "DAL", "injury": None},
}


def story(title, impact=None, slugs=None):
    return {"id": title, "title": title, "desc": None, "impact": impact, "slugs": slugs or []}


def report(*items):
    return news_report({"items": list(items)}, STATUS, slugify)


def test_a_story_is_about_the_fantasy_player_its_headline_leads_with():
    got = report(story("Saquon Barkley (hamstring) officially ruled out Sunday "),
                 story("Christian Darrisaw (concussion) ruled out Sunday "),     # a lineman: no fantasy player
                 story("Tee Higgins remains in protocol"))                        # no injury tag: matched by name
    assert [it["slug"] for it in got["items"]] == ["saquon-barkley", None, "tee-higgins"]


def test_the_next_man_up_is_a_teammate_the_read_names_in_its_order():
    got = report(story("Saquon Barkley (hamstring) officially ruled out Sunday ",
                       "Will Shipley becomes an RB2. The Eagles also elevated Dameon Pierce to the active roster."))
    assert got["items"][0]["next"] == ["will-shipley", "dameon-pierce"]


def test_the_next_man_up_is_never_the_opponent_the_read_names():
    got = report(story("Lamar Jackson (ankle) ruled out Sunday ",
                       "It will be Tyler Huntley getting the start Sunday night against Michael Penix Jr. and Atlanta."))
    assert got["items"][0]["next"] == ["tyler-huntley"]


def test_the_next_man_up_list_names_two_at_most():
    impact = "Will Shipley, Dameon Pierce and Kenneth Gainwell split the work."
    got = report(story("Saquon Barkley (hamstring) officially ruled out Sunday ", impact))
    assert got["items"][0]["next"] == ["will-shipley", "dameon-pierce"]


def test_a_story_whose_headline_hides_the_name_is_matched_by_its_slug_candidates():
    got = report(story("Report: Eagles back will miss Sunday", slugs=["nobody-here", "saquon-barkley"]))
    assert got["items"][0]["slug"] == "saquon-barkley"


def test_a_story_with_no_slug_candidates_is_matched_by_its_headline():
    item = {"id": 1, "title": "Tee Higgins (neck) limited Thursday", "desc": None, "impact": None}   # no `slugs`
    assert report(item)["items"][0]["slug"] == "tee-higgins"


def test_a_reported_player_sleeper_does_not_list_still_joins_the_players_block():
    rows = practice(report_row("Kyle Monangai", "kyle-monangai", {"wed": "DNP", "thu": None, "fri": None}, "Out", "CHI", "RB"))
    got = news_report({"items": []}, STATUS, slugify, rows)
    assert got["players"]["kyle-monangai"] == {"n": "Kyle Monangai", "pos": "RB", "team": "CHI", "injury": "out",
                                               "days": {"Wed": "dnp", "Thu": None, "Fri": None}, "report": True}


def test_only_an_out_story_names_a_next_man_up():
    got = report(story("Saquon Barkley (hamstring) limited Thursday", "Will Shipley would start if he sits."))
    assert got["items"][0]["next"] == []


def test_each_story_carries_its_word_and_day():
    got = report(story("Tee Higgins (groin/neck) officially doesn't practice Thursday"))["items"][0]
    assert (got["status"], got["day"]) == ("dnp", "Thu")


def test_the_players_block_holds_sleepers_designation_as_a_game_day_word():
    got = report(story("Tee Higgins (groin/neck) officially doesn't practice Thursday"),
                 story("Lamar Jackson (ankle) not seen practicing Thursday "),
                 story("Saquon Barkley (hamstring) officially ruled out Sunday ", "Will Shipley starts."))
    assert got["players"]["tee-higgins"] == {"n": "Tee Higgins", "pos": "WR", "team": "CIN", "injury": "questionable"}
    assert got["players"]["lamar-jackson"]["injury"] == "out"          # IR plays no Sunday either
    assert got["players"]["will-shipley"]["injury"] is None            # named as next up: in the block too
    assert set(got["players"]) == {"tee-higgins", "lamar-jackson", "saquon-barkley", "will-shipley"}


def test_a_kicker_is_not_a_player_the_report_follows():
    assert "brandon-aubrey" not in news_people(STATUS, slugify)


def test_without_sleeper_the_words_stay_and_no_player_is_named():
    got = news_report({"items": [story("Tee Higgins (groin/neck) officially doesn't practice Thursday")]}, {}, slugify)
    assert got["players"] == {}
    assert (got["items"][0]["slug"], got["items"][0]["status"], got["items"][0]["day"]) == (None, "dnp", "Thu")


def test_no_news_is_no_report():
    assert news_report(None, STATUS, slugify) is None


# ---- ff-jarvis's practice report (feed block `practice_report`, ff-jarvis #100, 2026-10-09) ------------------

def report_row(name, slug, days, status=None, team="CIN", pos="WR"):
    return {"name": name, "slug": slug, "team": team, "pos": pos, "days": days, "status": status,
            "status_set": None, "injury": None}


def practice(*rows, note=None):
    return {"generated": "2026-10-09T06:00", "season": 2026, "week": 5,
            "dates": {"wed": "2026-10-07", "thu": "2026-10-08", "fri": "2026-10-09"},
            "source": {"status_file": "sleeper_status.json", "marks": {"wed": 1, "thu": 1, "fri": 0}},
            "note": note, "players": list(rows)}


def test_the_report_gives_each_player_his_days_in_the_pages_words():
    rows = practice(report_row("Tee Higgins", "tee-higgins", {"wed": "DNP", "thu": "LP", "fri": None}, "Questionable"))
    got = news_report({"items": []}, STATUS, slugify, rows)
    assert got["players"]["tee-higgins"]["days"] == {"Wed": "dnp", "Thu": "limited", "Fri": None}
    assert got["players"]["tee-higgins"]["injury"] == "questionable"
    assert got["practice"] == {"note": None}


def test_a_player_on_the_report_with_no_story_is_in_the_players_block():
    rows = practice(report_row("Isaiah Likely", "isaiah-likely", {"wed": "FP", "thu": None, "fri": None}, "Doubtful", "BAL", "TE"))
    got = news_report({"items": []}, STATUS, slugify, rows)
    assert got["players"]["isaiah-likely"] == {"n": "Isaiah Likely", "pos": "TE", "team": "BAL", "injury": "doubtful",
                                               "days": {"Wed": "full", "Thu": None, "Fri": None}, "report": True}


def test_a_report_with_a_note_says_so_and_its_status_still_counts():
    rows = practice(report_row("Tee Higgins", "tee-higgins", {"wed": None, "thu": None, "fri": None}, "Out"),
                    note="Sleeper's feed holds no practice participation for any day of this week yet")
    got = news_report({"items": []}, STATUS, slugify, rows)
    assert got["practice"]["note"].startswith("Sleeper's feed holds no practice")
    assert got["players"]["tee-higgins"]["injury"] == "out"


def test_a_kicker_on_the_report_is_not_followed():
    rows = practice(report_row("Brandon Aubrey", "brandon-aubrey", {"wed": "DNP", "thu": None, "fri": None}, "Out", "DAL", "K"))
    assert "brandon-aubrey" not in news_report({"items": []}, STATUS, slugify, rows)["players"]


@pytest.mark.parametrize("bad, says", [
    ({k: v for k, v in practice().items() if k != "note"}, "note"),
    (practice(report_row("Tee Higgins", "tee-higgins", {"wed": "OUT", "thu": None, "fri": None})), "OUT"),
    (practice(report_row("Tee Higgins", "tee-higgins", {"wed": None, "thu": None})), "days"),
    (practice({"name": "Tee Higgins", "days": {"wed": None, "thu": None, "fri": None}}), "slug"),
])
def test_a_report_of_the_wrong_shape_fails_the_build(bad, says):
    with pytest.raises(ValueError, match=says):
        check_practice_report(bad)


def test_the_report_is_read_from_the_file_when_the_feed_has_no_block(tmp_path, monkeypatch):
    import json
    import sources
    monkeypatch.setattr(sources, "FEED", tmp_path / "no-feed.json")
    want = practice(note="from the file")
    (tmp_path / "practice_report.json").write_text(json.dumps(want), encoding="utf-8")
    assert sources.load_practice_report(tmp_path) == want


def test_no_report_anywhere_is_none(tmp_path, monkeypatch):
    import sources
    monkeypatch.setattr(sources, "FEED", tmp_path / "no-feed.json")
    assert sources.load_practice_report(tmp_path) is None


def test_no_report_keeps_the_news_without_practice():
    got = news_report({"items": []}, STATUS, slugify, None)
    assert "practice" not in got
