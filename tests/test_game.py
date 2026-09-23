"""The /api/game endpoint's pure functions: how an ESPN game summary becomes a drive strip.

Nothing here touches the network. `fetch()` is the only function that would, and it is never
called: every test drives `shape()` and its helpers off tests/fixtures/data/espn_summary.json,
five real drives from Lions at Bills (event 401872932, 2026-09-22).

The facts worth pinning are the ones that were wrong first:
  * field position must come from `yardsToEndzone`. `start.yardLine` is the number painted on the
    field, so BUF 15 and DET 15 both arrive as 15 and a drive in the far half draws backwards;
  * an away possession runs the other way, so its coordinates flip and `dir` is -1. One fixed
    field, two directions -- not one direction and a field that flips;
  * a boxscore displayName carries a generational suffix the play text drops, so "James Cook III"
    has to reduce to "J. Cook" or a starting running back never gets a face;
  * kickoffs, punts, penalties and timeouts are drive bookkeeping and must not become plays --
    but an unrecognised type is reported rather than silently swallowed.
"""
import importlib.util
import json
import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = REPO / "tests" / "fixtures" / "data" / "espn_summary.json"


def _load():
    """api/game.py by path -- it is a Vercel file-based function, not an importable package."""
    spec = importlib.util.spec_from_file_location("game_fn", REPO / "api" / "game.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


game = _load()


@pytest.fixture(scope="module")
def summary():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def shaped(summary):
    return game.shape(summary)


def test_the_game_shapes_without_losing_its_drives(shaped):
    assert shaped["home"]["abbr"] == "BUF" and shaped["away"]["abbr"] == "DET"
    assert len(shaped["drives"]) == 5
    assert all(d["plays"] for d in shaped["drives"])
    assert shaped["current"] == len(shaped["drives"]) - 1


def test_every_play_type_in_a_real_game_is_either_drawn_or_named(shaped):
    """An unknown type is reported, never dropped in silence."""
    assert shaped["unknownPlayTypes"] is None


def test_position_comes_from_yards_to_endzone_not_the_painted_yard_line(summary):
    """The painted number cannot tell the halves apart; yardsToEndzone can."""
    far = {"yardLine": 15, "yardsToEndzone": 15}       # 15 yards out, deep in away territory
    own = {"yardLine": 15, "yardsToEndzone": 85}       # the home 15, 85 yards to go
    assert game.spot(far, home_ball=True) == 85
    assert game.spot(own, home_ball=True) == 15
    assert game.spot({"yardsToEndzone": None}, home_ball=True) is None


def test_an_away_drive_runs_the_other_way(shaped):
    """One fixed field: home drives 0 -> 100, away drives 100 -> 0."""
    home = next(d for d in shaped["drives"] if d["team"] == "BUF")
    away = next(d for d in shaped["drives"] if d["team"] == "DET")
    assert home["dir"] == 1 and away["dir"] == -1
    assert all(0 <= p["from"] <= 100 and 0 <= p["to"] <= 100
               for d in shaped["drives"] for p in d["plays"])


def test_the_distance_drawn_is_the_distance_the_play_text_states(shaped):
    """The strongest check on the coordinate mapping: what the field shows has to agree with the
    prose, in both directions. A sack is negative in the text and backwards on the field."""
    checked = 0
    for d in shaped["drives"]:
        for p in d["plays"]:
            if p["k"] == "fg":
                continue                          # a kick ends at the posts, not where it is spotted
            m = re.search(r"for (-?\d+) yards?\b", p["tx"])
            # A fumble moves the ball again after the stated yardage, so the end spot is the
            # recovery, not the run: "sacked ... for -4 yards. FUMBLES ..." ends 5 yards back.
            if not m or "penalty" in p["tx"].lower() or "FUMBLES" in p["tx"]:
                continue
            drawn = (p["to"] - p["from"]) * d["dir"]
            assert drawn == int(m.group(1)), f"drew {drawn} for {p['tx'][:70]!r}"
            checked += 1
    assert checked >= 15, f"only {checked} plays stated a distance"


def test_the_line_to_gain_is_ahead_of_the_ball_whichever_way_the_drive_runs(shaped):
    for d in shaped["drives"]:
        for p in d["plays"]:
            if "line" in p:
                assert (p["line"] - p["from"]) * d["dir"] >= 0


def test_a_generational_suffix_still_finds_a_face(summary):
    """ESPN writes 'James Cook III' in the boxscore and 'J.Cook' in the play text."""
    assert game.name_key("James Cook III") == "J.Cook"
    assert game.name_key("Josh Allen") == "J.Allen"
    assert game.name_key("Amon-Ra St. Brown") == "A.St.Brown"
    faces, names = game.athletes(summary)
    assert faces["J. Cook"].startswith("http")
    assert faces["J. Allen"].startswith("http")
    # and the table that saves the page from doing the same reduction in JavaScript: team-watch
    # knows him as "James Cook III" and every play in this payload calls him "J. Cook"
    assert names["James Cook III"] == "J. Cook"
    assert names["Josh Allen"] == "J. Allen"


def test_everyone_who_touches_the_ball_has_a_face(shaped):
    named = {p[k] for d in shaped["drives"] for p in d["plays"]
             for k in ("who", "qb") if p.get(k)}
    missing = sorted(n for n in named if n not in shaped["faces"])
    assert not missing, f"no headshot for {missing}"


def test_a_name_survives_a_formation_note_or_a_substitution():
    assert game.carrier("(Shotgun) J.Cook left tackle to BUF 41 for 4 yards") == "J. Cook"
    assert game.carrier("(No Huddle) J.Allen up the middle for 3 yards") == "J. Allen"
    assert game.passer("T.Grable reported in as eligible.  J.Allen pass short right") == "J. Allen"
    assert game.target("J.Allen pass short left to K.Shakir for 9 yards") == "K. Shakir"
    assert game.target("J.Allen pass deep middle intended for A.St. Brown") == "A. St. Brown"


def test_an_incompletion_that_names_nobody_is_not_a_crash():
    """Three of this game's incompletions name no target at all."""
    assert game.target("J.Allen pass incomplete short right.") is None
    row = game.play_row({"type": {"text": "Pass Incompletion"},
                         "text": "J.Allen pass incomplete short right.",
                         "start": {"yardsToEndzone": 70, "down": 3, "distance": 5},
                         "end": {"yardsToEndzone": 70}}, home_ball=True)
    assert row["k"] == "inc" and row["who"] is None and row["qb"] == "J. Allen"


def test_bookkeeping_records_never_become_plays(shaped):
    texts = " ".join(p["tx"] for d in shaped["drives"] for p in d["plays"])
    assert "kicks" not in texts and "punts" not in texts
    for label in ("Kickoff", "Punt", "Timeout", "Penalty", "Two-minute warning", "End of Game"):
        assert game.play_row({"type": {"text": label}, "text": "",
                              "start": {"yardsToEndzone": 50}, "end": {"yardsToEndzone": 50}},
                             home_ball=True) is None


def test_yards_after_the_catch_is_carried_when_the_feed_has_it(shaped):
    caught = [p for d in shaped["drives"] for p in d["plays"] if p["k"] == "pass"]
    assert caught, "the fixture should contain completions"
    assert sum("yac" in p for p in caught) >= len(caught) - 1      # 45 of 46 in the full game


def test_the_score_comes_from_the_play_records(shaped):
    """Every play carries homeScore/awayScore, so a drive's before and after are exact."""
    opener = shaped["drives"][0]
    assert opener["score"] == [0, 0]
    assert opener["end"]["score"][0] > 0                            # it ended in a touchdown
    for d in shaped["drives"]:
        assert d["end"]["score"][0] >= d["score"][0]
        assert d["end"]["score"][1] >= d["score"][1]


def test_a_field_goal_ends_at_the_posts(shaped):
    kicks = [(d, p) for d in shaped["drives"] for p in d["plays"] if p["k"] == "fg"]
    assert kicks, "the fixture should contain a field goal"
    for d, p in kicks:
        assert p["to"] == (100 if d["dir"] == 1 else 0)
        assert p["made"] is True


def test_a_game_that_has_not_kicked_off_says_so(summary):
    with pytest.raises(LookupError):
        game.shape({"header": summary["header"], "drives": {"previous": []}})


def test_the_payload_stays_small_enough_to_poll(shaped):
    """The page fetches this per drive view; it must not become another megabyte."""
    size = len(json.dumps(shaped))
    assert size < 120_000, f"{size} bytes for 5 drives"
