"""design/pbp.py: nflverse play-by-play becomes the same payload api/game.py builds from ESPN.

The shape is a contract with two producers, so the test that matters is agreement. Both describe
Lions at Bills (2026-09-17): ESPN's summary is pinned in tests/fixtures/data/espn_summary.json,
nflverse's rows in tests/fixtures/data/pbp_det_buf.json. Where they disagree about how many
drives a game had, or where a play started, one of them is wrong -- and that is worth failing
over, because the whole reason a second producer exists is that it can stand in for the first.

They do not agree about everything, and should not:
  * ESPN keeps one record per snap including the penalties that wiped a snap out; nflverse marks
    those `no_play`. So nflverse draws fewer plays, never more.
  * ESPN's prose names a tackler inside a sentence; nflverse names him in a column. Where the
    regex in api/game.py missed one, nflverse has it -- that is an improvement, not a mismatch.
"""
import importlib.util
import json
import pathlib

import pandas as pd
import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
DATA = REPO / "tests" / "fixtures" / "data"
GAME = "2026_02_DET_BUF"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


game = _load(REPO / "api" / "game.py", "game_fn")

import pbp                                     # design/ is on sys.path via conftest


@pytest.fixture(scope="module")
def rows():
    return json.loads((DATA / "pbp_det_buf.json").read_text(encoding="utf-8"))["plays"]


@pytest.fixture(scope="module")
def roster():
    raw = json.loads((DATA / "pbp_det_buf.json").read_text(encoding="utf-8"))["roster"]
    return pd.DataFrame(raw).set_index("gsis_id")


@pytest.fixture(scope="module")
def shaped(rows, roster):
    return pbp.shape(rows, roster, {"game_id": GAME, "home": "BUF", "away": "DET",
                                    "espn": "401872932"})


@pytest.fixture(scope="module")
def espn():
    return game.shape(json.loads((DATA / "espn_summary.json").read_text(encoding="utf-8")))


# --------------------------------------------------------------------------- the shape itself

def test_it_produces_the_payload_the_strip_takes(shaped):
    for key in ("event", "home", "away", "current", "drives", "faces", "names"):
        assert key in shaped, key
    assert shaped["home"]["abbr"] == "BUF" and shaped["away"]["abbr"] == "DET"
    assert shaped["current"] == len(shaped["drives"]) - 1
    assert shaped["source"] == "nflverse"


def test_every_play_type_is_drawn_or_named(shaped):
    assert shaped["unknownPlayTypes"] is None


def test_a_home_drive_and_an_away_drive_run_opposite_ways(shaped):
    home = next(d for d in shaped["drives"] if d["team"] == "BUF")
    away = next(d for d in shaped["drives"] if d["team"] == "DET")
    assert home["dir"] == 1 and away["dir"] == -1
    assert all(0 <= p["from"] <= 100 and 0 <= p["to"] <= 100
               for d in shaped["drives"] for p in d["plays"])


def test_the_distance_drawn_is_the_yardage_nflverse_states(shaped, rows):
    """nflverse states `yards_gained` as a column, so unlike the ESPN producer this needs no
    regex over prose -- which makes it a check on the direction, not on the parsing."""
    checked = 0
    for d in shaped["drives"]:
        for p in d["plays"]:
            if p["k"] in ("fg", "int") or "fum" in p:
                continue          # a kick ends at the posts; the others move the ball again after
            drawn = (p["to"] - p["from"]) * d["dir"]
            row = next(r for r in rows if pbp.text(r["desc"]) == p["tx"] and r.get("yards_gained") is not None)
            assert drawn == row["yards_gained"], f"drew {drawn} for {p['tx'][:70]!r}"
            checked += 1
    assert checked >= 100, f"only {checked} plays checked"


def test_a_sack_is_drawn_as_a_run_backwards(shaped):
    """Never forwards. Not always backwards either -- a sack at the line of scrimmage gains
    nothing and nflverse says so, which is a real play and not a shaping bug."""
    sacks = [(d, p) for d in shaped["drives"] for p in d["plays"] if "sacked" in p["tx"]]
    assert len(sacks) >= 4, f"the fixture should contain several sacks, found {len(sacks)}"
    assert all(p["k"] == "rush" for _, p in sacks)
    assert all((p["to"] - p["from"]) * d["dir"] <= 0 for d, p in sacks)
    assert any((p["to"] - p["from"]) * d["dir"] < 0 for d, p in sacks)


def test_an_assisted_tackle_names_both_men_once():
    """The pile the strip draws is the second name here. nflverse repeats a name across its
    solo/assist/with-assist columns; each man is named once, first-credited first."""
    r = {"solo_tackle_1_player_name": None, "assist_tackle_1_player_name": "A.Hutchinson",
         "assist_tackle_2_player_name": "J.Campbell", "tackle_with_assist_1_player_name": "A.Hutchinson"}
    assert pbp.tacklers(r) == ["A. Hutchinson", "J. Campbell"]
    assert pbp.tacklers({"solo_tackle_1_player_name": "F.Warner"}) == ["F. Warner"]


def test_a_sack_says_so(shaped):
    """Drawn as a run backwards, flagged so the strip can call it a sack."""
    sacks = [p for d in shaped["drives"] for p in d["plays"] if p.get("sack")]
    assert sacks and all(p["k"] == "rush" and (p["to"] - p["from"]) * d["dir"] <= 0
                         for d in shaped["drives"] for p in d["plays"] if p.get("sack"))


def test_kits_and_broken_tackles_ride_along(rows, roster):
    """Team colours come from design/kits.json; PFR's per-game broken tackles are keyed by the
    play text's spelling, and a player this game never names is dropped rather than guessed."""
    kits = {"BUF": {"jersey": "#00338d", "trim": "#c60c30", "dark": True}}
    out = pbp.shape(rows, roster, {"game_id": GAME, "home": "BUF", "away": "DET", "kits": kits,
                                   "brk": {"Josh Allen": 2, "Nobody Here": 4, "James Cook": 0}})
    assert out["home"]["kit"] == kits["BUF"] and "kit" not in out["away"]
    assert out["brk"] == {"J. Allen": 2}


def test_a_face_is_joined_by_id_not_by_spelling(shaped):
    """The failure this replaces: ESPN writes 'James Cook III' in a boxscore and 'J.Cook' in a
    play, so the ESPN producer has to strip suffixes and hope. nflverse gives an id per name."""
    assert shaped["faces"]["J. Allen"].startswith("http")
    assert shaped["names"]["Josh Allen"] == "J. Allen"
    named = {p[k] for d in shaped["drives"] for p in d["plays"] for k in ("who", "qb") if p.get(k)}
    missing = sorted(n for n in named if n not in shaped["faces"])
    assert len(missing) <= 2, f"no headshot for {missing}"


def test_bookkeeping_never_becomes_a_play(shaped):
    texts = " ".join(p["tx"] for d in shaped["drives"] for p in d["plays"])
    assert "kicks off" not in texts and " punts " not in texts
    for pt in ("kickoff", "punt", "extra_point", "no_play"):
        assert pbp.kind({"play_type": pt}) is None


# --------------------------------------------------------------------------- against ESPN

def pairs(shaped, espn):
    """The drives both fixtures describe, matched on the clock their first play ran at.

    The ESPN fixture is a deliberate trim -- five drives chosen to exercise the awkward paths --
    while nflverse's carries the whole game, so the comparison has to find its own overlap rather
    than zip two lists of different lengths. The game clock at the snap is the one thing neither
    producer computes: both read it off the record."""
    mine = {d["plays"][0]["clock"]: d for d in shaped["drives"]}
    out = [(mine[d["plays"][0]["clock"]], d) for d in espn["drives"] if d["plays"][0]["clock"] in mine]
    assert len(out) >= 4, f"only {len(out)} of ESPN's {len(espn['drives'])} drives matched by clock"
    return out


def test_both_producers_find_the_same_drives(shaped, espn):
    """The strongest check there is on a second producer: one game, described twice, by two
    organisations that never spoke to each other about it."""
    for mine, theirs in pairs(shaped, espn):
        assert mine["team"] == theirs["team"]
        assert mine["dir"] == theirs["dir"]


def test_both_producers_put_a_drive_in_the_same_place(shaped, espn):
    """Where each drive started, on the one absolute 0-100 scale both of them use. A yard of
    slack: ESPN spots a penalty enforcement where nflverse spots the snap."""
    for mine, theirs in pairs(shaped, espn):
        assert abs(mine["plays"][0]["from"] - theirs["plays"][0]["from"]) <= 1, \
            f"{mine['team']} drive starts at {mine['plays'][0]['from']} vs {theirs['plays'][0]['from']}"


def test_both_producers_agree_on_where_a_drive_ended_up(shaped, espn):
    """And on the score it left behind -- the number a reader actually looks at."""
    for mine, theirs in pairs(shaped, espn):
        assert mine["end"]["score"] == theirs["end"]["score"], \
            f"{mine['team']} drive ends {mine['end']['score']} vs {theirs['end']['score']}"


def test_neither_producer_invents_plays(shaped, espn):
    """nflverse marks a wiped-out snap `no_play`; ESPN keeps the record. So nflverse draws fewer,
    never more -- and not many fewer, or something else is being dropped silently."""
    for mine, theirs in pairs(shaped, espn):
        assert len(mine["plays"]) <= len(theirs["plays"]), \
            f"{mine['team']}: nflverse drew {len(mine['plays'])}, ESPN {len(theirs['plays'])}"
        assert len(theirs["plays"]) - len(mine["plays"]) <= 2
