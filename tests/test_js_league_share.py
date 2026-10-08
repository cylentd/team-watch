"""League > Recap, Share: what goes into the shared image and its text version (surface/league/share.js).

lgShareData and lgShareText are pure: the week in, plain data out, the same for every reader. The picture
(Canvas) and the click (share sheet, clipboard, modal) need a browser and are checked there by hand.
lgGameTags is back.js's (unit U2, 2026-10-06); it is planted here as a stub so these tests pin share.js's
side of the contract: at most two tags a game, whatever the tagger returns.
"""
import json

import pytest

from wording import words

# Names with an "&" and an apostrophe: the image and the text are not HTML, so they must stay as written.
TEAMS = [{"id": 1, "mgr": "Chanel", "name": "Lamarley & Me", "avatar": "avatars/yahoo/1.webp"}, {"id": 2, "mgr": "Crystal W.", "name": "Two"},
         {"id": 3, "mgr": "Phillip", "name": "Three"}, {"id": 4, "mgr": "Jon & Kay", "name": "Four"},
         {"id": 5, "mgr": "", "name": "Five's Team"}, {"id": 6, "mgr": "Victoria", "name": "Six"},
         {"id": 7, "mgr": "Kearny", "name": "Seven"}, {"id": 8, "mgr": "Theo", "name": "Eight"}]

HEAD = "Chanel hangs 146.98 on Crystal W. for a third straight W"
# w.games is not in page order: the lead sits in the middle, and 3-4 carries a stamp.
GAMES = [
    {"a": 7, "b": 8, "ap": 100.5, "bp": 99.0, "win": "home", "punch": "Kearny by a hair."},
    {"a": 1, "b": 2, "ap": 146.98, "bp": 93.04, "win": "home", "punch": "Lamarley & Me, and Me is Kyren Williams."},
    {"a": 3, "b": 4, "ap": 82.78, "bp": 80.28, "win": "home", "punch": "Jon lost to a -3.0 defense.", "stamp": "Sleepwalked"},
    {"a": 5, "b": 6, "ap": 90, "bp": 140.4, "win": "away", "punch": HEAD},
    {"a": 2, "b": 5, "ap": 77.7, "bp": 77.7, "win": "tie", "punch": ""},
]
WEEK = {"week": 4, "head": HEAD, "lead": "1-2", "games": GAMES}
TAGS = {
    "1-2": [{"k": "top", "label": "Top dog", "tone": "g", "id": 1}],
    "3-4": [{"k": "luck", "label": "Stole one", "tone": "g", "id": 3}, {"k": "low", "label": "Dumpster fire", "tone": "r", "id": 4},
            {"k": "close", "label": "Nail-biter", "tone": "x", "id": 3}],
}
# The stub: whatever TAGS holds for the game's key, however many.
STUB = f"(globalThis.lgGameTags = (w, g) => ({json.dumps(TAGS)})[lgKey(g)] || [], true)"


@pytest.fixture(scope="module")
def share(node_js):
    # data/league.js is lgPts (and the LG holder); slate.js is lgKey. Neither has top-level side effects Node cannot run.
    # back.js is lgGamesInOrder, the page's own order, which the image follows (review 2026-10-06).
    js = node_js("data/league.js", "surface/league/slate.js", "surface/league/back.js", "surface/league/share.js")
    js(f"(LG = {json.dumps({'league': 'Madden Curse', 'teams': TEAMS, 'weeks': [WEEK]})}, true)")
    js(STUB)
    return js


def data(share, week=WEEK):
    return share("lgShareData", week)


@pytest.mark.parametrize("coarse, can_files, route", [
    (True, True, "sheet"),        # a phone that shares files: the share sheet
    (False, True, "clipboard"),   # Windows Chrome shares files too, but a desktop copies the image (review 2026-10-06)
    (True, False, "clipboard"),   # a phone that cannot share files
    (False, False, "clipboard"),
])
def test_only_a_touch_device_that_shares_files_gets_the_share_sheet(share, coarse, can_files, route):
    assert share("lgShareRoute", coarse, can_files) == route


def test_every_game_is_in_the_image_in_the_pages_order_the_lead_then_the_widest_margin(share):
    rows = data(share)["rows"]
    assert [(r["win"], r["lose"]) for r in rows] == [
        ("Chanel", "Crystal W."),       # the lead, though it is second in w.games
        ("Victoria", "Five's Team"),    # margin 50.4
        ("Phillip", "Jon & Kay"),       # margin 2.5; its stamp no longer moves it (rows carry no stamps)
        ("Kearny", "Theo"),             # margin 1.5
        ("Crystal W.", "Five's Team"),  # a tie, margin 0
    ]


def test_a_score_line_names_the_winner_first_with_two_decimals_and_plain_text_names(share):
    rows = {r["win"]: r for r in data(share)["rows"]}
    assert (rows["Chanel"]["winPts"], rows["Chanel"]["losePts"]) == ("146.98", "93.04")
    # an away win swaps the sides; a manager with no first name falls back to the team's name, unescaped
    assert (rows["Victoria"]["lose"], rows["Victoria"]["winPts"], rows["Victoria"]["losePts"]) == ("Five's Team", "140.40", "90.00")
    assert rows["Phillip"]["lose"] == "Jon & Kay"
    assert [r["tie"] for r in data(share)["rows"]].count(True) == 1


def test_a_game_carries_at_most_two_tags_with_the_team_and_side_each_belongs_to(share):
    # side: which half of the score line the stamp sits beside (David, 2026-10-06: Dumpster fire, Jon's, sat
    # under Phillip); a Nail-biter is the game's, so it closes the line.
    rows = {r["win"]: r for r in data(share)["rows"]}
    assert rows["Phillip"]["tags"] == [{"label": "Stole one", "tone": "g", "name": "Phillip", "side": "win"},
                                       {"label": "Dumpster fire", "tone": "r", "name": "Jon & Kay", "side": "lose"}]
    assert rows["Chanel"]["tags"] == [{"label": "Top dog", "tone": "g", "name": "Chanel", "side": "win"}]
    nail = share("(g) => { const keep = globalThis.lgGameTags; globalThis.lgGameTags = () => [{k: 'close', label: 'Nail-biter', tone: 'x', id: 3}];"
                 " const t = lgShareRow({}, g, '').tags; globalThis.lgGameTags = keep; return t; }", GAMES[2])
    assert nail == [{"label": "Nail-biter", "tone": "x", "name": "Phillip", "side": "game"}]
    assert rows["Kearny"]["tags"] == []
    assert max(len(r["tags"]) for r in data(share)["rows"]) == 2


def test_each_game_carries_its_winners_avatar_or_none(share):
    # David, 2026-10-06: "we need team avatars for the shared image version"; the winner's only, as on the page,
    # and a team with none gets "" (the picture draws the manager's initial in its place).
    rows = {r["win"]: r["winAv"] for r in data(share)["rows"]}
    assert rows == {"Chanel": "avatars/yahoo/1.webp", "Victoria": "", "Phillip": "", "Kearny": "", "Crystal W.": ""}


def test_the_headline_is_claudes_and_a_line_that_repeats_it_is_left_out(share):
    d = data(share)
    assert d["headline"] == HEAD
    lines = {r["win"]: r["line"] for r in d["rows"]}
    assert lines["Victoria"] == "", "the game whose joke is the headline would say it twice"
    assert lines["Chanel"] == "Lamarley & Me, and Me is Kyren Williams."
    assert lines["Crystal W."] == ""
    # with no headline of its own the lead's line leads, and is not repeated under its score
    d = data(share, {**WEEK, "head": ""})
    assert d["headline"] == "Lamarley & Me, and Me is Kyren Williams."
    assert d["rows"][0]["line"] == ""


def test_the_image_holds_the_league_and_nothing_about_the_reader(share):
    d = data(share)
    assert d["kicker"] == "Madden Curse · Week 4 · Final"
    assert d["url"] == words("league.share.url")
    assert set(d) == {"kicker", "headline", "rows", "url"}, "no dek, team, standings or your-game box"
    assert all(set(r) == {"win", "winPts", "lose", "losePts", "tie", "tags", "line", "winAv"} for r in d["rows"])
    assert all(set(tg) == {"label", "tone", "name", "side"} for r in d["rows"] for tg in r["tags"])


def test_the_text_version_is_kicker_headline_each_game_with_its_line_then_the_link(share):
    d = {"kicker": "Madden Curse · Week 4 · Final", "headline": "A beats B", "url": "u.example/#recap", "rows": [
        {"win": "Chanel", "winPts": "146.98", "lose": "Crystal W.", "losePts": "93.04", "tie": False,
         "tags": [{"label": "Top dog", "tone": "g", "name": "Chanel"}], "line": "Me is Kyren."},
        {"win": "Kearny", "winPts": "77.70", "lose": "Theo", "losePts": "77.70", "tie": True, "tags": [], "line": ""}]}
    assert share("lgShareText", d) == "\n".join([
        "MADDEN CURSE · WEEK 4 · FINAL", "A beats B", "",
        "Chanel 146.98 beat Crystal W. 93.04 · TOP DOG Chanel", "Me is Kyren.", "",
        "Kearny 77.70 tied Theo 77.70", "",
        "u.example/#recap"])


def test_the_real_text_has_every_game_the_link_last_and_no_tone_word(share):
    text = share("lgShareText", data(share))
    lines = text.split("\n")
    assert lines[-1] == words("league.share.url")
    assert lines[0] == "MADDEN CURSE · WEEK 4 · FINAL"
    assert sum(" beat " in ln or " tied " in ln for ln in lines) == len(GAMES)
    assert not any(w in text.lower() for w in ("roast", "props", "your game", "cheer"))
    assert lines[3] == "Chanel 146.98 beat Crystal W. 93.04 · TOP DOG Chanel", "lead first, below the headline and a blank line"


def test_a_week_with_no_games_is_a_headline_and_a_link_not_an_error(share):
    d = data(share, {"week": 4, "head": "", "lead": "", "games": []})
    assert d["rows"] == [] and d["headline"] == ""
    assert share("lgShareText", d) == "MADDEN CURSE · WEEK 4 · FINAL\n\n" + words("league.share.url")
