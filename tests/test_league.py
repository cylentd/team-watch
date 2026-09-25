"""api/league.py: connected leagues. Nothing here touches the network; `fetch` is never called.

The payload below is hand-built in ESPN's shape (mTeam + mRoster + mSettings), trimmed to what
the functions read. Checked against David's live league on 2026-09-24: 12 teams, his roster's
slots, FLEX numbering, IR -> OUT and the Q badge all came out as asserted here.
"""

import base64
import importlib.util
import json
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "api"))


def _load():
    spec = importlib.util.spec_from_file_location("league_fn", REPO / "api" / "league.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lg = _load()


def entry(slot, name, pos=2, pro=15, injury=None):
    return {"lineupSlotId": slot, "playerPoolEntry": {"player": {
        "fullName": name, "defaultPositionId": pos, "proTeamId": pro, "injuryStatus": injury}}}


BODY = {
    "settings": {"name": "We're Big in Japan"},
    "teams": [
        {"id": 3, "name": "Someone Else", "primaryOwner": "{AAA}",
         "record": {"overall": {"wins": 1, "losses": 3}}, "roster": {"entries": []}},
        {"id": 12, "name": "Purdy Big in Japan", "primaryOwner": "{ABC-123}",
         "record": {"overall": {"wins": 2, "losses": 2}}, "roster": {"entries": [
             entry(0, "Brock Purdy", pos=1, pro=25),
             entry(2, "De'Von Achane"),
             entry(23, "Tee Higgins", pos=3, pro=4),
             entry(23, "Tony Pollard", pro=10, injury="QUESTIONABLE"),
             entry(20, "Amon-Ra St. Brown Jr.", pos=3, pro=8),
             entry(21, "Jordan Mason", pro=16, injury="INJURY_RESERVE"),
             entry(16, "Seahawks D/ST", pos=16, pro=26),
         ]}},
    ],
}


@pytest.mark.parametrize("text,want", [
    ("https://fantasy.espn.com/football/league?leagueId=1534545", 1534545),
    ("fantasy.espn.com/football/team?leagueId=1534545&teamId=12&seasonId=2026", 1534545),
    ("  1534545 ", 1534545),
])
def test_a_link_or_an_id_gives_the_league(text, want):
    assert lg.parse_league(text) == want


@pytest.mark.parametrize("text", ["", "https://football.fantasysports.yahoo.com/f1/75203", "12"])
def test_anything_else_is_refused(text):
    with pytest.raises(ValueError):
        lg.parse_league(text)


def test_the_swid_finds_the_visitors_team_braces_or_not():
    assert lg.owner_team(BODY, "{abc-123}") == 12
    assert lg.owner_team(BODY, "ABC-123") == 12
    assert lg.owner_team(BODY, "{nobody}") is None


def test_rows_carry_the_live_espn_shape():
    rows = lg.roster_rows(BODY, 12)
    assert all(set(r) == {"n", "pos", "team", "slot", "slug", "status"} for r in rows)
    by = {r["n"]: r for r in rows}
    assert [r["slot"] for r in rows if r["slot"].startswith("FLX")] == ["FLX1", "FLX2"]
    assert by["Tony Pollard"]["status"] == "Q"
    assert by["Amon-Ra St. Brown Jr."]["slot"] == "BN"
    assert by["Amon-Ra St. Brown Jr."]["slug"] == "amonra-st-brown"      # same slug as build.py
    assert by["Jordan Mason"]["slot"] == "OUT" and by["Jordan Mason"]["status"] == "OUT"
    assert by["Seahawks"]["pos"] == "DST" and by["Seahawks"]["team"] == "SEA"


def test_the_card_names_league_team_and_record():
    card = lg.league_card(BODY, {"lid": 1534545, "tid": 12})
    assert card["key"] == "espn-1534545"
    assert (card["league"], card["name"], card["record"]) == ("We're Big in Japan", "Purdy Big in Japan", "2-2")


def test_a_missing_team_is_a_lookup_error():
    with pytest.raises(LookupError):
        lg.roster_rows(BODY, 99)


def test_the_cookie_round_trips_and_is_locked_down():
    kept = [{"lid": 1, "tid": 2, "swid": "{X}", "s2": "abc%2Bdef"}]
    header = lg.write_cookie(kept)
    assert "HttpOnly" in header and "Secure" in header and "Path=/api/league" in header
    value = header.split(";")[0].split("=", 1)[1]
    assert lg.read_cookie(f"other=1; {lg.COOKIE}={value}") == kept


def test_a_damaged_cookie_reads_as_no_leagues():
    junk = base64.urlsafe_b64encode(b"not json").decode()
    assert lg.read_cookie(f"{lg.COOKIE}={junk}") == []
    assert lg.read_cookie("") == []


def test_forgetting_the_last_league_expires_the_cookie():
    assert "Max-Age=0" in lg.write_cookie([])


def test_the_cookie_stays_under_the_browser_limit_at_its_cap():
    s2 = "A" * 360          # espn_s2 runs a few hundred characters
    full = [{"lid": 10**9 + i, "tid": 12, "swid": "{" + "B" * 36 + "}", "s2": s2} for i in range(lg.MAX_LEAGUES)]
    assert len(lg.write_cookie(full)) < 4096
    assert json.loads(base64.urlsafe_b64decode(lg.write_cookie(full).split(";")[0].split("=", 1)[1] + "=="))
