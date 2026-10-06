"""design/league_back.py through live_league_yahoo against the 4-team fixture plus a week 2 box score
and roast: each game's records, punchline, facts, stamp and box; the bench award; the tape; the record book."""
import json
import sys

import pytest

from conftest import REPO

sys.path.insert(0, str(REPO / "design"))
sys.path.insert(0, str(REPO / "api"))
import contract                              # noqa: E402
from league_recap import live_league_yahoo   # noqa: E402
from _espn import slugify                    # noqa: E402

FIX = REPO / "tests" / "fixtures" / "data"
read = lambda n: json.loads((FIX / n).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def back():
    b = live_league_yahoo(read("yahoo_league.json"), read("yahoo_league_history.json"), read("yahoo_league_owners.json"),
                          read("league_rosters.json"), slugify, read("yahoo_league_box.json"), read("yahoo_league_recap.json"),
                          read("yahoo_league_managers.json"))
    contract.validate("LIVE_LEAGUE_YAHOO", b)
    return b


def test_managers_name_teams_champions_and_records(back):
    assert {t["id"]: t["mgr"] for t in back["teams"]} == {3: "Kearny", 7: "Crystal W.", 9: "David", 10: "Jon"}
    assert all(c["mgr"] for c in back["champs"] if c["id"] is not None)
    every = back["book"]["fame"] + back["book"]["shame"]
    # A former manager's record keeps its manager's name after its id is dropped.
    assert any(f.get("id") is None and f.get("mgr") == "Justin" for f in every) or not any(
        f.get("id") is None and "y" in f for f in every)
    assert all(f.get("mgr") for f in every if f.get("id") is not None)


def test_a_roasted_week_carries_its_words(back):
    w2 = back["weeks"][1]
    assert w2["head"] == "CHAT SURVIVES BY 0.44" and w2["dek"].startswith("Jaxon The Box")
    g = {f"{x['a']}-{x['b']}": x for x in w2["games"]}
    assert g["7-3"]["stamp"] == "BURIED" and g["10-9"]["stamp"] is None
    assert g["10-9"]["punch"] == "Jaxon The Box benched the win."
    assert g["10-9"]["beats"] == ["Rico Dowdle on the bench: 15.5", "Jaylen Warren started: 6.5", "Lost by 0.44"]


def test_a_skipped_week_draws_scores_without_words(back):
    w1 = back["weeks"][0]
    assert w1["head"] is None and w1["dek"] is None
    assert all(g["punch"] is None and g["beats"] == [] and g["box"] is None for g in w1["games"])


def test_records_are_after_that_week(back):
    w1, w2 = ({f"{x['a']}-{x['b']}": x for x in w["games"]} for w in back["weeks"])
    assert (w1["9-10"]["ar"], w1["9-10"]["br"]) == ("0–1", "1–0")
    assert (w2["10-9"]["ar"], w2["10-9"]["br"]) == ("1–1", "1–1")


def test_box_is_slim_and_keeps_empty_slots_and_the_mistake(back):
    box = {f"{x['a']}-{x['b']}": x for x in back["weeks"][1]["games"]}["10-9"]["box"]
    assert box["slots"] == [["QB", "Justin Herbert", 20.24, "Josh Allen", 40.82], ["RB", "Jaylen Warren", 6.5, None, None]]
    assert box["proj"] == [104.5, 110.2]
    assert box["left"] == [{"benched": "Rico Dowdle", "bp": 15.5, "started": "Jaylen Warren", "sp": 6.5, "lost": 9.0}, None]


def test_bench_award_is_the_weeks_biggest_mistake(back):
    assert back["weeks"][1]["awards"]["bench"] == {"id": 10, "v": 9.0, "name": "Rico Dowdle", "bp": 15.5, "started": "Jaylen Warren", "sp": 6.5}
    assert "bench" not in back["weeks"][0]["awards"]


def test_tape_fields_on_every_team(back):
    for tm in back["teams"]:
        assert len(tm["all"]) == 3 and isinstance(tm["titles"], list) and isinstance(tm["lasts"], list)


def test_book_splits_fame_and_shame(back):
    fame = [f["k"] for f in back["book"]["fame"]]
    shame = [f["k"] for f in back["book"]["shame"]]
    assert fame[:2] == ["high", "blow"] and shame[0] == "low"
    assert "robbed" in shame and "stole" in shame
    assert not set(fame) & set(shame)


def test_luck_is_wins_minus_the_wins_a_teams_points_earned_against_everyone():
    # David, 2026-10-06: Luck so far. Each week a score "earns" the share of the other teams it beat; luck is
    # real wins minus those earned wins, in wins, one decimal. Tags by luck_tags (the test below).
    from league_back import add_standings
    g = lambda a, b, ap, bp: {"a": a, "b": b, "ap": ap, "bp": bp, "win": "home" if ap > bp else "away"}
    weeks = [{"games": [g(1, 2, 100, 90), g(3, 4, 80, 70)]},      # earned 1, 2/3, 1/3, 0
             {"games": [g(1, 3, 60, 110), g(2, 4, 120, 50)]}]     # earned 1/3, 1, 2/3, 0
    add_standings(weeks, [1, 2, 3, 4])
    luck = {r["id"]: (r["luck"], r["tag"]) for r in weeks[1]["table"]}
    assert luck == {1: (-0.3, None), 2: (-0.7, "robbed"), 3: (1.0, "lucky"), 4: (0.0, None)}
    assert {r["id"]: r["luck"] for r in weeks[0]["table"]} == {1: 0.0, 2: -0.7, 3: 0.7, 4: 0.0}


def test_luck_tags_the_two_luckiest_and_the_two_unluckiest_half_a_win_or_more_off():
    # David, 2026-10-06, "we should have unlucky as well?": a week tagged only at a whole win showed Lucky and no
    # Snakebit (the worst were -0.9). So each side tags its two most extreme teams, if half a win or more off.
    from league_back import luck_tags
    lucks = {1: 1.1, 2: 1.1, 3: 0.8, 4: 0.2, 5: -0.4, 6: -0.9, 7: -0.9, 8: -1.3}
    assert luck_tags(lucks) == {1: "lucky", 2: "lucky", 8: "robbed", 6: "robbed"}, "two a side, ties by id"
    assert luck_tags({1: 0.4, 2: -0.4, 3: 0.0}) == {}, "nobody half a win off, nobody tagged"


def test_standings_after_each_week(back):
    t1, t2 = (w["table"] for w in back["weeks"])
    assert [r["id"] for r in t1][:2] == [10, 3]                     # both 1-0, Jaxon The Box on points
    top = t2[0]
    assert (top["id"], top["w"], top["l"], top["pf"], top["pfr"]) == (3, 2, 0, 292.08, 1)
    assert all(r["move"] == 0 for r in t1)                           # week 1 has no week before it
    assert sum(r["move"] for r in t2) == 0                           # every place gained is one lost


def test_next_grudge_is_the_most_lopsided_pairing(back):
    from league_back import next_grudge
    rec = lambda w, l: {"w": w, "l": l, "t": 0}
    h2h = {"1": {"2": rec(5, 6)}, "2": {"1": rec(6, 5)}, "3": {"4": rec(0, 10)}, "4": {"3": rec(10, 0)},
           "5": {"6": rec(2, 0)}, "6": {"5": rec(0, 2)}}
    now = [{"a": 1, "b": 2}, {"a": 3, "b": 4}, {"a": 5, "b": 6}]
    assert next_grudge(now, h2h) == {"a": 4, "b": 3}          # 10-0, told from the side that leads it
    assert next_grudge([{"a": 5, "b": 6}], h2h) is None        # 2 meetings is not a grudge yet
    assert back["grudge"] is None                              # the fixture's pairings met at most twice


def test_blip_reacts_to_the_lead_games_place_in_the_week():
    """2026's real weeks 1 and 3 (a, b, a's points, b's points)."""
    from league_back import blip_of
    wk = lambda lead, games: {"lead": lead, "games": [{"a": a, "b": b, "ap": ap, "bp": bp} for a, b, ap, bp in games]}
    w1 = [(1, 6, 117.66, 76.42), (2, 4, 123.96, 76.84), (3, 11, 145.46, 104.76),
          (5, 8, 128.12, 70.66), (7, 12, 99.2, 144.2), (9, 10, 113.9, 163.56)]
    w3 = [(1, 7, 91.44, 118.64), (2, 12, 73.74, 126.28), (3, 8, 120.56, 103.58),
          (4, 10, 85.08, 108.38), (5, 9, 141.28, 86.6), (6, 11, 78.62, 138.84)]
    assert blip_of(wk("5-8", w1)) == "ko"          # won by 57.46, Michelle's 70.66 the week's worst
    assert blip_of(wk("6-11", w3)) == "wince"      # won by 60.22
    assert blip_of(wk("2-12", w3)) == "flatline"   # Victoria's 73.74
    assert blip_of(wk("3-8", w3)) == "sweat"       # 16.98, the week's closest
    assert blip_of(wk("1-7", w3)) == "laugh"


def test_blip_reacts_on_every_lead_even_one_whose_line_is_about_a_player(back):
    # David, 2026-10-06: Blip on every lead, because the recap is the whole league's board, not one roster's;
    # a player's headshot took Blip's place until then.
    assert all(w["blip"] in ("ko", "wince", "flatline", "sweat", "laugh") for w in back["weeks"])
    recap = read("yahoo_league_recap.json")
    recap["weeks"]["2"] = {**recap["weeks"]["2"], "lead": "10-9", "photo": "Justin Herbert"}
    b = live_league_yahoo(read("yahoo_league.json"), read("yahoo_league_history.json"), read("yahoo_league_owners.json"),
                          read("league_rosters.json"), slugify, read("yahoo_league_box.json"), recap,
                          read("yahoo_league_managers.json"))
    wk = next(w for w in b["weeks"] if w["week"] == 2)
    assert wk["blip"] in ("ko", "wince", "flatline", "sweat", "laugh")
    assert "photo" not in wk, "the board never pictures one roster's player"


def test_every_week_names_its_lead_game(back):
    for w in back["weeks"]:
        assert w["lead"] in {f"{g['a']}-{g['b']}" for g in w["games"]}


def test_a_private_pairs_record_never_ships():
    from league_back import withhold, next_grudge
    rec = lambda w, l, m: {"w": w, "l": l, "t": 0, "m": m}
    h2h = {"3": {"4": rec(0, 3, [[2024, 1, -5.0, 0]] * 3), "5": rec(1, 0, [])}, "4": {"3": rec(3, 0, [[2024, 1, 5.0, 0]] * 3)}}
    assert withhold(h2h, [(3, 4)]) == [[3, 4]]                                 # the pair, never its record
    assert "4" not in h2h["3"] and "3" not in h2h["4"] and "5" in h2h["3"]     # gone both ways, the rest kept
    assert next_grudge([{"a": 3, "b": 4}], h2h) is None                        # nor can it be next week's grudge


def test_streaks_run_across_seasons_and_a_tie_ends_one():
    from league_back import add_streaks
    g = lambda y, wk, h, a, win: {"y": y, "week": wk, "home": h, "away": a, "winner": win}
    games = [g(2025, 16, 1, 2, "home"), g(2025, 17, 1, 3, "home"), g(2026, 1, 1, 2, "home"), g(2026, 1, 3, 4, "tie"),
             g(2026, 2, 1, 3, "away")]
    weeks = add_streaks([{"week": 1}, {"week": 2}], games, {1, 2, 3, 4})
    w1 = {r["id"]: r for r in weeks[0]["streaks"]}
    assert w1[1] == {"id": 1, "n": 3, "w": 1, "y": 2025, "wk": 16}             # three straight, begun last season
    assert w1[2]["n"] == 2 and w1[2]["w"] == 0 and 3 not in w1 and 4 not in w1  # the tie left 3 and 4 with no run
    w2 = {r["id"]: r for r in weeks[1]["streaks"]}
    assert w2[1] == {"id": 1, "n": 1, "w": 0, "y": 2026, "wk": 2} and weeks[1]["streaks"][0]["id"] == 2


def test_last_place_is_yahoos_final_place_where_read():
    from league_back import last_places
    g = lambda y, h, a, win: {"y": y, "week": 1, "home": h, "away": a, "hp": 90.0, "ap": 80.0, "winner": win, "tier": None}
    games = [g(2019, 1, 2, "home"), g(2020, 1, 2, "home")]
    assert last_places(games, 2026) == {2019: 2, 2020: 2}                      # the worst record, as a fallback
    assert last_places(games, 2026, {2019: 1}) == {2019: 1, 2020: 2}           # the consolation bracket counts


def test_the_spoon_case_names_each_last_place(back):
    assert all({"y", "id", "name", "mgr", "final"} <= set(s) for s in back["spoons"])
    # 2025's final places are Yahoo's: 4th of the fixture's four was team 2 then, Crystal W. (7) today.
    assert back["spoons"][0] == {"y": 2025, "id": 7, "name": "Bower", "mgr": "Crystal W.", "final": True}
    assert [s["y"] for s in back["spoons"]] == sorted((s["y"] for s in back["spoons"]), reverse=True)


def test_a_skipped_manager_holds_no_record_and_the_next_one_down_does():
    from league_back import book
    from league_recap import facts
    g = lambda y, wk, h, a, hp, ap, tier=None: {"y": y, "week": wk, "home": h, "away": a, "hp": hp, "ap": ap,
                                                  "winner": "home" if hp > ap else "away", "tier": tier}
    games = [g(2018, 1, 1002, 1, 30.0, 90.0), g(2018, 2, 1002, 2, 40.0, 95.0), g(2018, 3, 1, 2, 60.0, 80.0)]
    low = lambda fx: next(f for f in fx if f["k"] == "low")
    assert low(facts(games, [], {}))["id"] == 1002
    assert low(facts(games, [], {}, frozenset({1002})))["id"] == 1 and low(facts(games, [], {}, frozenset({1002})))["v"] == 60.0
    teams = [{"id": 1, "all": [1, 1, 0]}, {"id": 2, "all": [2, 0, 0]}]
    shame = book([], games, teams, {}, frozenset({1002}))["shame"]
    assert all(f.get("id") != 1002 for f in shame)


def test_the_record_skip_file_names_no_one():
    """design/league_record_skip.json holds manager keys and dates, never a name."""
    import json, pathlib
    raw = json.loads((pathlib.Path(__file__).parents[1] / "design" / "league_record_skip.json").read_text(encoding="utf-8"))
    assert all(set(m) <= {"key", "asked", "keeps"} and m["key"].startswith("former-") for m in raw["managers"])


def test_meetings_say_their_kind():
    from league_back import add_meets
    h2h = {"1": {"2": {"w": 0, "l": 0, "t": 0}}, "2": {"1": {"w": 0, "l": 0, "t": 0}}}
    g = lambda wk, tier: {"y": 2024, "week": wk, "home": 1, "away": 2, "hp": 90.0, "ap": 80.0, "tier": tier}
    add_meets(h2h, [g(1, None), g(15, "playoff"), g(16, "consolation")])
    assert [x[3] for x in h2h["1"]["2"]["m"]] == [0, 1, 2]


def test_the_private_file_names_no_one():
    """design/league_private.json holds ids and dates only: the repo is not the place for the story."""
    import json, pathlib
    raw = json.loads((pathlib.Path(__file__).parents[1] / "design" / "league_private.json").read_text(encoding="utf-8"))
    assert all(set(p) <= {"a", "b", "asked"} for p in raw["pairs"])


def test_without_box_or_roast_the_block_still_draws():
    b = live_league_yahoo(read("yahoo_league.json"), read("yahoo_league_history.json"), read("yahoo_league_owners.json"),
                          read("league_rosters.json"), slugify)
    contract.validate("LIVE_LEAGUE_YAHOO", b)
    assert all(w["head"] is None for w in b["weeks"])


# ---- Recap direction B (2026-10-06, plan 2026-10-06-recap-b U2): the page's own markup, in Node ----

@pytest.fixture(scope="module")
def recap_js(node_js, back):
    """The Recap's draw functions with the fixture league on screen (LG), week 2 showing."""
    js = node_js("data/league.js", "surface/league/slate.js", "surface/league/back.js", "surface/league/share.js",
                 "surface/league/tape.js", "surface/league/lead.js", "surface/league/records.js",
                 "surface/league/myrecap.js")
    js("(b) => { globalThis.ordinal = n => `${n}th`; globalThis.headImgHTML = () => '<img>';"
       " globalThis.blipReactSVG = (l, p) => `<svg class=\"br br-${p}\"></svg>`; LG = b; LG_WEEK = null; return 1; }", back)
    return js


def game(a, b, ap, bp):
    return {"a": a, "b": b, "ap": ap, "bp": bp, "win": "home" if ap > bp else "away"}


AW = lambda id, **k: {"id": id, "v": 100.0, "opp": 0, "m": 5.0, "rank": 1, "of": 8, **k}
BUSY = {"games": [game(1, 2, 120.0, 118.0), game(3, 4, 99.0, 80.0)],
        "awards": {"top": AW(1), "low": AW(2), "unluck": AW(2), "luck": AW(1), "bench": AW(1, v=9.0, name="A", bp=1, started="B", sp=0),
                   "close": {"id": 1, "opp": 2, "v": 2.0, "p": 120.0, "op": 118.0}}}


def kinds(js, w, g):
    return [t["k"] for t in js("lgGameTags", w, g)]


def test_a_game_wears_at_most_two_award_tags_in_priority_order(recap_js):
    w = {"games": [game(1, 2, 120.0, 90.0)], "awards": {"top": AW(1), "low": AW(2), "unluck": AW(2), "luck": AW(1)}}
    assert kinds(recap_js, w, w["games"][0]) == ["top", "low"]
    only = {"games": w["games"], "awards": {"luck": AW(1), "bench": AW(2, v=9.0, name="A", bp=1, started="B", sp=0)}}
    assert kinds(recap_js, only, only["games"][0]) == ["luck", "bench"]
    assert kinds(recap_js, w, game(5, 6, 100.0, 90.0)) == [], "a game no award names has no tags"


def test_the_nail_biter_is_always_on_the_weeks_closest_game_even_in_a_busy_one(recap_js):
    assert kinds(recap_js, BUSY, BUSY["games"][0]) == ["top", "close"], "close keeps a slot; the other is the top priority"
    assert kinds(recap_js, BUSY, BUSY["games"][1]) == []
    assert sum("close" in kinds(recap_js, BUSY, g) for g in BUSY["games"]) == 1


def test_a_tag_carries_its_label_tone_and_team(recap_js):
    tags = {t["k"]: t for t in recap_js("lgGameTags", BUSY, BUSY["games"][0])}
    assert tags["top"] == {"k": "top", "label": "Top dog", "tone": "g", "id": 1}
    assert tags["close"]["label"] == "Nail-biter" and tags["close"]["tone"] == "x"
    far = {**BUSY, "awards": {"close": {"id": 1, "opp": 2, "v": 14.0, "p": 120.0, "op": 106.0}}}
    assert recap_js("lgGameTags", far, BUSY["games"][0])[0]["label"] == "Closest game", "10 points or more is not a nail-biter"
    rest = {**BUSY, "awards": {k: v for k, v in BUSY["awards"].items() if k not in ("top", "close")}}
    assert [(t["k"], t["tone"]) for t in recap_js("lgGameTags", rest, BUSY["games"][0])] == [("low", "r"), ("unluck", "r")]
    amber = {**BUSY, "awards": {"bench": BUSY["awards"]["bench"]}}
    assert recap_js("lgGameTags", amber, BUSY["games"][0])[0]["tone"] == "a"


def test_the_week_stepper_disables_each_end_and_walks_by_week(recap_js, back):
    nums = [w["week"] for w in back["weeks"]]
    html = lambda wk: recap_js("(n) => { LG_WEEK = n; return lgStepHTML(lgWeek()); }", wk)
    first, last = html(nums[0]), html(nums[-1])
    assert 'data-lgweek="' + str(nums[0] - 1) not in first and "disabled" in first.split("lg-step-next")[0], "no week before the first"
    assert "disabled" not in last.split("lg-step-next")[0] and f'data-lgweek="{nums[-1] - 1}"' in last
    assert last.count("disabled") == 1 and first.count("disabled") == 1
    assert "Week 2" in last and "Final" in last


def test_the_league_section_is_the_same_for_every_reader(recap_js):
    page = lambda id: recap_js("(id) => { LG_WEEK = null; return lgBackWeekHTML(id); }", id)
    league = lambda html: html[html.index('<section class="lg-league'):]
    me, other, nobody = page(9), page(3), page(None)
    assert league(me) == league(other) == league(nobody)
    assert "lg-you" in me and "lg-you" in other and "lg-you" not in nobody
    assert "lg-you" not in league(me), "the reader's own game is an ordinary row in League"
    assert "lime" not in league(me) and 'class="me' not in league(me)


ROW = lambda id, luck, tag=None: {"id": id, "w": 2, "l": 2, "t": 0, "pf": 400.0, "pfr": 1, "move": 0, "luck": luck, "tag": tag}


def test_the_luck_ladder_ranks_every_team_luckiest_first_and_never_says_robbed(recap_js):
    # David, 2026-10-06: the bottom row's gap holds "Luck so far", every team by its luck in wins
    # (league_back.add_standings), the tag only at a whole win either way; "Robbed" is the week's award, so the
    # unlucky side is "Snakebit". Kept simple: record, the signed number, the tag, one caption; no jargon.
    table = [ROW(1, 0.0), ROW(2, 1.2, "lucky"), ROW(3, 0.4), ROW(4, -1.1, "robbed"), ROW(5, -0.3)]
    html = recap_js("(table) => lgLuckHTML({table})", table)
    assert recap_js("(table) => lgLuckRows({table}).map(r => r.id)", table) == [2, 3, 1, 5, 4]
    assert html.count("<li") == 5, "every team has a rung"
    assert html.count("Lucky") == 1 and html.count("Snakebit") == 1 and "Robbed" not in html
    assert "+1.2" in html and "−1.1" in html and ">0.0<" in html, "the luck as a signed number, one decimal"
    assert "vs. what their points earned" in html and "all-play" not in html.lower()
    # A chart, not a second table (David, 2026-10-06, "looks the same" as the standings): a bar per team from
    # a zero line, its length against the week's biggest luck, its side by sign; no record column.
    bars = recap_js("(table) => [...lgLuckHTML({table}).matchAll(/lg-luckbar (up|dn|zero)\" style=\"--w:([\\d.]+)%/g)].map(m => [m[1], +m[2]])", table)
    assert bars == [["up", 100], ["up", 33.3], ["zero", 0], ["dn", 25], ["dn", 91.7]]
    assert "2–2" not in html, "the standings carry the records"


def test_the_league_section_has_one_headline_and_it_tops_the_lead(recap_js):
    # David, 2026-10-06, "it looks like two headlines": Claude's headline is the lead card's title; the game's
    # line runs under the score as text; the dek opens the other games.
    html = recap_js("() => { LG_WEEK = null; const w = lgWeek(); w.head = 'Chanel hangs 146.98 on Crystal W.'; w.dek = 'And the rest.';"
                    " return lgLeagueHTML(w); }")
    lead = html[html.index('<article class="bp2-lead'):html.index("</article>")]
    assert html.count('class="lg-hl') == 1 and 'class="lg-hl' in lead, "one headline, inside the lead card"
    assert html.index("lg-dek") > html.index("</article>"), "the dek follows the lead, opening the other games"
    assert recap_js("(table) => lgLuckHTML({table})", []) == "", "no table, no section"


def test_the_lead_draws_blip_even_when_the_week_names_a_photo(recap_js):
    # HEADS holds the player's cut, so the headshot could draw: the lead must still pick Blip.
    html = recap_js("() => { globalThis.HEADS = {'josh-allen': 'heads/josh-allen.webp'}; LG_WEEK = null; const w = lgWeek();"
                    " return lgLeadHTML({...w, photo: {name: 'Josh Allen', slug: 'josh-allen', pts: 40.82, flop: false}, blip: 'laugh'},"
                    " w.games[0]); }")
    assert "br-laugh" in html and "<img" not in html


def test_the_page_has_no_superlative_cards_streaks_block_week_chips_or_extra_stamps(recap_js):
    html = recap_js("() => { LG_WEEK = null; return lgBackWeekHTML(9); }")
    for gone in ("bp-su", "bp-sups", "lg-weeks", "bp2-streaks", "bp2-you", "bp2-brief", "bp2-tag", "bp-game"):
        assert gone not in html, gone
    assert html.count("bp-stamp") <= 1, "only the lead card keeps its stamp"
    assert 'data-lgweek="1"' in html, "the stepper's back button asks for week 1"


def test_your_game_box_opens_nothing_by_default_and_names_three_disclosures(recap_js):
    html = recap_js("() => { LG_WEEK = null; return lgBackWeekHTML(9); }")
    box = html[html.index('<div class="lg-you'):html.index('<section class="lg-league')]
    assert box.count("<details") == 3 and " open" not in box
    assert "Box score" in box and "You in the record book" in box and "Next week vs" in box
    assert "Your game" in box


def test_standings_end_each_row_with_a_streak_tinted_by_its_run(recap_js, back):
    html = recap_js("() => { LG_WEEK = null; return lgAgateHTML(lgWeek()); }")
    run = {s["id"]: s for s in back["weeks"][-1]["streaks"]}
    long = [s for s in run.values() if s["n"] >= 2]
    assert ("lg-sk hot" in html) == any(s["w"] for s in long) and ("lg-sk cold" in html) == any(not s["w"] for s in long)
    assert html.count("<i>") == 4, "one rank cell per team"
