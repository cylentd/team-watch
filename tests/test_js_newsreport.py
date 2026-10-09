"""Players > News as an injury report (ledger #95, 2026-10-09), in Node: data/newsreport.js.

Who is on the report (the reader's players, their wire, the starters in their leagues), what each row says
(the Sunday word, Wednesday to Friday, the newest story, the next man up free in a league of theirs), the
order, and the Pacific week the practice cells belong to. Every word is the build's (design/news.py); the
page only picks and orders."""
import datetime

import pytest

pytestmark = pytest.mark.req("News", ac="the injury report")

THU = "2026-10-08T18:00:00Z"        # Thursday 11:00 AM Pacific
TUE = "2026-10-13T19:00:00Z"        # the next Tuesday, noon Pacific


def P(slug, slot="WR", start=True):
    return {"n": slug.replace("-", " ").title(), "slug": slug, "pos": "WR", "team": "CIN", "slot": slot, "start": start}


TEAMS = {
    "espn": {"key": "espn", "name": "Mine", "roster": [P("tee-higgins"), P("ladd-mcconkey", "BN", False)]},
    "espn-rival": {"key": "espn-rival", "league": "espn", "mate": True, "name": "Rival",
                   "roster": [P("saquon-barkley", "RB"), P("bench-guy", "BN", False)]},
    "yahoo": {"key": "yahoo", "name": "Other league", "roster": [P("will-shipley", "RB"), P("yahoo-star")]},
}


def item(slug, title, at, status=None, day=None, nxt=(), iid=None):
    return {"id": iid or title, "title": title, "at": at, "slug": slug, "slugs": [slug] if slug else [],
            "status": status, "day": day, "next": list(nxt), "link": "https://example.com/" + (slug or "x")}


PLAYERS = {s: {"n": s.replace("-", " ").title(), "pos": "WR", "team": "CIN", "injury": None}
           for s in ("tee-higgins", "ladd-mcconkey", "saquon-barkley", "bench-guy", "will-shipley", "yahoo-star",
                     "wire-man", "nobody-at-all")}
PLAYERS["ladd-mcconkey"]["injury"] = "questionable"


def news(*items):
    return {"items": list(items), "players": PLAYERS}


@pytest.fixture(scope="module")
def nr(node_js):
    return node_js("data/dayplan.js", "data/newsreport.js")


@pytest.mark.parametrize("now, start", [
    ("2026-10-08T18:00:00Z", "2026-10-06"),   # Thursday: the Tuesday two days before
    ("2026-10-13T19:00:00Z", "2026-10-13"),   # Tuesday: today
    ("2026-10-13T05:00:00Z", "2026-10-06"),   # Monday 10 PM Pacific, already Tuesday in UTC
    ("2026-10-11T20:00:00Z", "2026-10-06"),   # Sunday
])
def test_the_week_starts_on_the_tuesday_on_or_before_today_pacific(nr, now, start):
    assert nr(f"nrWeekStart(Date.parse('{now}'))") == start


@pytest.mark.parametrize("now, tue", [(TUE, True), (THU, False), ("2026-10-13T05:00:00Z", False)])
def test_tuesday_is_the_pacific_tuesday(nr, now, tue):
    assert nr(f"nrTuesday(Date.parse('{now}'))") is tue


def test_the_scope_is_the_followed_rosters_and_their_leagues_starters(nr):
    got = nr("nrScope", TEAMS, ["espn"])
    assert sorted(got["mine"]) == ["ladd-mcconkey", "tee-higgins"]
    assert got["leagues"] == ["espn"]
    assert sorted(got["starters"]) == ["saquon-barkley", "tee-higgins"]          # a bench is no starter
    assert sorted(got["rostered"]["espn"]) == ["bench-guy", "ladd-mcconkey", "saquon-barkley", "tee-higgins"]


def test_a_team_with_no_roster_yet_and_a_followed_key_gone_from_the_page_are_skipped(nr):
    teams = {**TEAMS, "conn-1": {"key": "conn-1", "connected": True}}     # a connected league still loading
    got = nr("nrScope", teams, ["espn", "conn-1", "gone"])
    assert (sorted(got["mine"]), got["leagues"]) == (["ladd-mcconkey", "tee-higgins"], ["espn"])


def test_the_report_opens_on_the_starters_first_page(node_js):
    assert node_js("data/news.js", globals={"LIVE_NEWS": None})("NEWS_AT") == 0


def test_with_no_team_followed_the_scope_is_every_leagues_starters(nr):
    got = nr("nrScope", TEAMS, [])
    assert got["mine"] == []
    assert sorted(got["leagues"]) == ["espn", "yahoo"]
    assert sorted(got["starters"]) == ["saquon-barkley", "tee-higgins", "will-shipley", "yahoo-star"]


def ms(iso):
    return int(datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)


def rows(nr, items, followed=("espn",), wire=(), now=THU):
    scope = nr("nrScope", TEAMS, list(followed))
    return nr("nrRows", news(*items), scope, list(wire), ms(now))


def test_only_the_readers_players_wire_and_starters_are_on_it(nr):
    got = rows(nr, [item("nobody-at-all", "Nobody (knee) limited Thursday", THU, "limited", "Thu"),
                    item(None, "Christian Darrisaw (concussion) ruled out Sunday", THU, "out"),
                    item("bench-guy", "Bench Guy (calf) limited Thursday", THU, "limited", "Thu"),
                    item("wire-man", "Wire Man (ankle) full Thursday", THU, "full", "Thu"),
                    item("saquon-barkley", "Saquon Barkley (hamstring) ruled out Sunday", THU, "out"),
                    item("ladd-mcconkey", "Ladd McConkey (foot) doesn't practice Thursday", THU, "dnp", "Thu")],
               wire=["wire-man"])
    assert [(r["slug"], r["group"]) for r in got] == [
        ("ladd-mcconkey", "mine"), ("wire-man", "wire"), ("saquon-barkley", "starter")]


def test_within_a_group_the_worst_sunday_word_leads(nr):
    got = rows(nr, [item("tee-higgins", "Tee Higgins (neck) will play Sunday", THU, "cleared"),
                    item("ladd-mcconkey", "Ladd McConkey (foot) ruled out Sunday", THU, "out")])
    assert [r["slug"] for r in got] == ["ladd-mcconkey", "tee-higgins"]


def test_with_no_sunday_word_the_worst_practice_line_leads_then_the_newest(nr):
    older, newer = "2026-10-08T15:00:00Z", "2026-10-08T17:00:00Z"
    got = rows(nr, [item("tee-higgins", "Tee Higgins (neck) full Thursday", newer, "full", "Thu"),
                    item("ladd-mcconkey", "Ladd McConkey (foot) doesn't practice Thursday", older, "dnp", "Thu")])
    assert [r["slug"] for r in got] == ["ladd-mcconkey", "tee-higgins"]          # dnp before full, newer or not
    block = news(item("ladd-mcconkey", "Ladd McConkey (foot) limited Thursday", older, "limited", "Thu"),
                 item("tee-higgins", "Tee Higgins (neck) limited Thursday", newer, "limited", "Thu"))
    block["players"] = {**PLAYERS, "ladd-mcconkey": {**PLAYERS["ladd-mcconkey"], "injury": None}}
    same = nr("nrRows", block, nr("nrScope", TEAMS, ["espn"]), [], ms(THU))
    assert [r["slug"] for r in same] == ["tee-higgins", "ladd-mcconkey"]          # one word: the newest first


def test_a_story_from_a_build_with_no_next_field_names_no_next_man(nr):
    it = item("tee-higgins", "Tee Higgins (neck) ruled out Sunday", THU, "out")
    del it["next"]
    assert rows(nr, [it])[0]["next"] == []


def test_a_row_is_one_player_with_his_newest_story_first(nr):
    got = rows(nr, [item("tee-higgins", "Tee Higgins (neck) listed questionable Sunday", "2026-10-09T18:00:00Z", "questionable", iid=3),
                    item("tee-higgins", "Tee Higgins (neck) limited Thursday", THU, "limited", "Thu", iid=2),
                    item("tee-higgins", "Tee Higgins (neck) doesn't practice Wednesday", "2026-10-07T20:00:00Z", "dnp", "Wed", iid=1)],
               now="2026-10-09T20:00:00Z")
    assert len(got) == 1
    r = got[0]
    assert (r["sunday"], r["newest"]["id"], [s["id"] for s in r["more"]]) == ("questionable", 3, [2, 1])
    assert r["days"] == {"Wed": "dnp", "Thu": "limited"}


def test_a_practice_line_from_last_week_fills_no_cell(nr):
    got = rows(nr, [item("tee-higgins", "Tee Higgins (neck) limited Friday", "2026-10-03T00:00:00Z", "limited", "Fri")])
    assert got[0]["days"] == {}


def test_the_newest_practice_line_for_a_day_wins(nr):
    got = rows(nr, [item("tee-higgins", "Tee Higgins (neck) upgraded to full Thursday", THU, "full", "Thu", iid=2),
                    item("tee-higgins", "Tee Higgins (neck) not seen practicing Thursday", "2026-10-08T17:00:00Z", "dnp", "Thu", iid=1)])
    assert got[0]["days"] == {"Thu": "full"}


def reported(slug, days, injury=None):
    """news() with ff-jarvis's practice report on `slug` (design/news.py's `players[slug].days`)."""
    block = news()
    block["players"] = {**PLAYERS, slug: {**PLAYERS[slug], "days": days, "injury": injury, "report": True}}
    return block


def test_the_practice_report_fills_the_cells_and_a_headline_fills_a_day_it_left_empty(nr):
    block = reported("tee-higgins", {"Wed": "dnp", "Thu": None, "Fri": None})
    block["items"] = [item("tee-higgins", "Tee Higgins (neck) limited Thursday", THU, "limited", "Thu")]
    got = nr("nrRows", block, nr("nrScope", TEAMS, ["espn"]), [], ms(THU))
    assert got[0]["days"] == {"Wed": "dnp", "Thu": "limited"}


def test_a_report_with_friday_only_fills_friday_and_leaves_wednesday_and_thursday_open(nr):
    # ff-jarvis #100 (00f0a88): NFL.com's report, week 5 had Friday only.
    block = reported("tee-higgins", {"Wed": None, "Thu": None, "Fri": "limited"}, "questionable")
    got = nr("nrRows", block, nr("nrScope", TEAMS, ["espn"]), [], ms("2026-10-09T23:00:00Z"))
    assert got[0]["days"] == {"Fri": "limited"}


def test_a_reported_player_with_no_story_still_has_a_row(nr):
    block = reported("tee-higgins", {"Wed": "limited", "Thu": None, "Fri": None}, "questionable")
    got = nr("nrRows", block, nr("nrScope", TEAMS, ["espn"]), [], ms(THU))
    assert [(r["slug"], r["sunday"], r["days"], r["newest"], r["more"]) for r in got] == [
        ("tee-higgins", "questionable", {"Wed": "limited"}, None, [])]


def test_a_reported_player_outside_the_readers_scope_has_no_row(nr):
    block = reported("nobody-at-all", {"Wed": "dnp", "Thu": None, "Fri": None}, "out")
    assert nr("nrRows", block, nr("nrScope", TEAMS, ["espn"]), [], ms(THU)) == []


def test_with_no_story_stating_one_the_sunday_word_is_sleepers(nr):
    got = rows(nr, [item("ladd-mcconkey", "Ladd McConkey (foot) doesn't practice Thursday", THU, "dnp", "Thu")])
    assert got[0]["sunday"] == "questionable"
    none = rows(nr, [item("tee-higgins", "Tee Higgins (neck) limited Thursday", THU, "limited", "Thu")])
    assert none[0]["sunday"] is None


def test_the_next_man_up_shows_only_where_he_is_free_in_the_readers_leagues(nr):
    out = item("saquon-barkley", "Saquon Barkley (hamstring) ruled out Sunday", THU, "out",
               nxt=["will-shipley", "bench-guy"])
    got = rows(nr, [out], followed=("espn", "yahoo"))
    # Shipley is on a Yahoo roster and free in ESPN; Bench Guy is rostered in ESPN and free in Yahoo.
    assert got[0]["next"] == [{"slug": "will-shipley", "n": "Will Shipley", "free": ["espn"]},
                              {"slug": "bench-guy", "n": "Bench Guy", "free": ["yahoo"]}]


def test_a_next_man_rostered_in_every_league_is_not_named(nr):
    out = item("saquon-barkley", "Saquon Barkley (hamstring) ruled out Sunday", THU, "out", nxt=["bench-guy"])
    assert rows(nr, [out])[0]["next"] == []


def test_a_story_the_build_could_not_name_is_matched_by_its_slug_candidates(nr):
    it = item(None, "Brock Purdy added to injury report as questionable", THU, "questionable")
    it["slugs"] = ["tee-higgins-extra", "tee-higgins"]
    assert [r["slug"] for r in rows(nr, [it])] == ["tee-higgins"]


def test_the_groups_keep_their_order_and_drop_an_empty_one(nr):
    got = rows(nr, [item("saquon-barkley", "Saquon Barkley (hamstring) ruled out Sunday", THU, "out"),
                    item("tee-higgins", "Tee Higgins (neck) limited Thursday", THU, "limited", "Thu")])
    assert [(g["key"], [r["slug"] for r in g["rows"]]) for g in nr("nrGroups", got)] == [
        ("mine", ["tee-higgins"]), ("starter", ["saquon-barkley"])]


@pytest.mark.parametrize("at, first_page", [(0, 0), (2, 2), (9, 2), (-1, 0)])
def test_a_page_of_rows_is_clamped_to_the_list(nr, at, first_page):
    size = nr("NR_PAGE")
    n = 2 * size + 3                                   # three pages, the last one short
    got = nr("nrPage", list(range(n)), at)
    assert got["at"] == first_page
    assert got["rows"] == list(range(first_page * size, min(n, (first_page + 1) * size)))
    assert got["pages"] == 3


@pytest.mark.parametrize("title, name, what", [
    ("Saquon Barkley (hamstring) officially ruled out Sunday ", "Saquon Barkley", "Officially ruled out Sunday"),
    ("Ja'Marr Chase remains in concussion protocol ", "Ja'Marr Chase", "Remains in concussion protocol"),
    ("Report: minor roster move for Detroit", "Jahmyr Gibbs", "Report: minor roster move for Detroit"),
    ("Tee Higgins (neck)", "Tee Higgins", "Tee Higgins (neck)"),          # nothing left but the name: keep it whole
    ("Tee Higgins ruled out", None, "Tee Higgins ruled out"),
])
def test_a_row_that_names_him_shows_only_what_happened(nr, title, name, what):
    assert nr("nrWhat", title, name) == what


def test_a_short_list_is_one_page(nr):
    assert nr("nrPage", [1, 2], 0) == {"rows": [1, 2], "at": 0, "pages": 1}
