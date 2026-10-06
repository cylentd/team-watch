"""Top calls: the model's strongest lines in games still to play, and the same-game slip note (data/topcalls.js, Node).

Slips leads with these (2026-10-05, plan "Bets UX" change 1): strongest tier first, then the model's chance of
its side, one line per player, only games that have not kicked off, each with the book's break-even so the edge
is two numbers a reader can subtract. A slip holding two legs of one game says so and shows no combined chance."""
import pytest

# 2026-10-05 13:00 UTC, Monday: Sunday has kicked off, Monday night (00:15 UTC Tuesday) has not.
NOW = 1791205200000
SUN, MON = "2026-10-04 17:00:00", "2026-10-06 00:15:00"
FILES = ("lib/kick.js", "lib/odds.js", "data/topcalls.js")


def book(model, over=-110, under=-110, line=40.5, **more):
    return {"line": line, "over": over, "under": under, "model": model, **more}


def prop(n, model, tier, side, mkt="REC", commence=MON, game="ATL @ NO", ud=None, **more):
    """A row at DraftKings' line; `ud` is Underdog's own entry when it has one."""
    dk = book(model, over=-115, under=-105)
    books = {"DraftKings": dk, **({"Underdog": ud} if ud else {})}
    return {"n": n, "slug": n.lower().replace(" ", "-"), "pos": "WR", "team": "ATL", "mkt": mkt, "line": 40.5,
            "game": game, "commence": commence, "kick": "Mon 5:15p", "book": "DraftKings", "books": books,
            "model": model, "tier": tier, "side": side, **more}


@pytest.fixture(scope="module")
def tc(node_js):
    return node_js(*FILES)


def calls(tc, props, **opts):
    return tc("topCalls", props, {"now": NOW, "book": "underdog", **opts})


def test_the_strongest_tier_leads_then_the_chance_of_the_side(tc):
    props = [prop("Slight Guy", 45, "slight", "lower"),
             prop("Very Guy", 12, "very", "lower"),
             prop("Confident Guy", 36, "confident", "lower"),
             prop("Confident Higher", 66, "confident", "higher")]
    got = [c["n"] for c in calls(tc, props)]
    assert got == ["Very Guy", "Confident Higher", "Confident Guy", "Slight Guy"]


def test_the_chance_is_that_of_the_models_side_not_the_over(tc):
    got = calls(tc, [prop("Lower Guy", 26, "confident", "lower")])[0]
    assert (got["side"], got["pct"], got["tier"]) == ("lower", 74, "confident")


def test_only_games_that_have_not_kicked_off(tc):
    props = [prop("Played Guy", 10, "very", "lower", commence=SUN, game="DET @ CAR"),
             prop("Open Guy", 40, "slight", "lower"),
             prop("Undated Guy", 38, "slight", "lower", commence=None, game="SF @ NYJ")]
    assert sorted(c["n"] for c in calls(tc, props)) == ["Open Guy", "Undated Guy"]


def test_no_pick_a_touchdown_an_out_player_or_a_moved_line_is_a_call(tc):
    props = [prop("None Guy", 52, "none", "higher"), prop("No Tier Guy", 20, None, None),
             prop("TD Guy", 70, "very", "higher", mkt="TD"), prop("Long Guy", 70, "very", "higher", mkt="LONG"),
             prop("Out Guy", 10, "very", "lower", flag="out"),
             prop("Moved Guy", 10, "very", "lower", books={"DraftKings": book(10, over=-115, under=-105)}, stale=1),
             prop("Fine Guy", 40, "slight", "lower")]
    assert [c["n"] for c in calls(tc, props, book="dk")] == ["Fine Guy"]


def test_the_edge_is_the_chance_less_the_break_even_of_the_sides_own_price(tc):
    """Lower at Underdog's -110: break-even 52%, so 74% is +22. DraftKings' own Under was -105 (51%)."""
    ud = book(26, line=41.5, side="lower", tier="confident")
    row = prop("Edge Guy", 30, "slight", "lower", ud=ud)
    got = calls(tc, [row])[0]
    assert (got["pct"], got["be"], got["edge"], got["line"]) == (74, 52, 22, 41.5)
    dk = calls(tc, [row], book="dk")[0]
    assert (dk["pct"], dk["be"], dk["edge"], dk["tier"]) == (70, 51, 19, "slight")


def test_a_call_priced_worse_than_its_break_even_is_not_a_top_call(tc):
    """Lower at -250 breaks even at 71%: a 70% chance is -1, so the row would print "+-1" and is no edge. A call
    at exactly break-even stays, and so does one whose price the book never sent."""
    steep = book(30, over=200, under=-250)
    even = book(29, over=200, under=-250)
    props = [prop("Steep Guy", 30, "very", "lower", ud={**steep, "side": "lower", "tier": "very"}),
             prop("Even Guy", 29, "very", "lower", ud={**even, "side": "lower", "tier": "very"}),
             prop("Bare Guy", 30, "confident", "lower", books={"DraftKings": {"line": 40.5, "model": 30}})]
    got = {c["n"]: c["edge"] for c in calls(tc, props)}
    assert "Steep Guy" not in got and all(e is None or e >= 0 for e in got.values())
    assert got["Bare Guy"] is None


def test_a_players_negative_line_does_not_hide_his_other_one(tc):
    steep = book(30, over=200, under=-250)
    props = [prop("Two Lines", 30, "very", "lower", ud={**steep, "side": "lower", "tier": "very"}),
             prop("Two Lines", 40, "slight", "lower", mkt="RUSH")]
    assert [(c["mkt"], c["tier"]) for c in calls(tc, props)] == [("RUSH", "slight")]


def test_a_higher_call_is_priced_at_the_over(tc):
    ud = book(66, over=-125, under=105, side="higher", tier="confident")
    got = calls(tc, [prop("Higher Guy", 60, "slight", "higher", ud=ud)])[0]
    assert (got["side"], got["pct"], got["be"], got["edge"]) == ("higher", 66, 56, 10)


def test_a_price_the_book_did_not_send_leaves_the_edge_empty_but_keeps_the_call(tc):
    got = calls(tc, [prop("Bare Guy", 30, "confident", "lower", books={"DraftKings": {"line": 40.5, "model": 30}})], book="dk")[0]
    assert (got["pct"], got["be"], got["edge"]) == (70, None, None)


def test_underdog_uses_its_own_tier_and_not_the_other_books(tc):
    """Underdog's number has no tier of its own: the row's tier belongs to DraftKings' line, so no call."""
    ud = book(26, line=41.5)
    assert calls(tc, [prop("Quiet Guy", 30, "confident", "lower", ud=ud)]) == []


def test_one_call_per_player_his_strongest(tc):
    props = [prop("Two Lines", 40, "slight", "lower"), prop("Two Lines", 10, "very", "lower", mkt="RUSH")]
    got = calls(tc, props)
    assert [(c["n"], c["mkt"], c["tier"]) for c in got] == [("Two Lines", "RUSH", "very")]


def test_the_list_is_cut_to_the_limit_and_names_its_row(tc):
    props = [prop(f"Guy {k}", 30 + k, "slight", "lower") for k in range(8)]
    got = calls(tc, props, limit=5)
    assert len(got) == 5 and [c["i"] for c in got] == [0, 1, 2, 3, 4]


def test_the_tier_words_keep_one_order(tc):
    assert tc("PT_TIERS") == ["none", "slight", "confident", "very"]
    assert tc("PT_RANK") == {"slight": 1, "confident": 2, "very": 3}


# ---- the slip: same-game legs move together ----

def test_two_legs_of_one_game_are_flagged_with_the_game(tc):
    assert tc("slipSameGame", ["ATL @ NO", "SEA @ SF", "ATL @ NO"], None) == "ATL @ NO"


def test_legs_of_different_games_are_not(tc):
    assert tc("slipSameGame", ["ATL @ NO", "SEA @ SF"], None) is None
    assert tc("slipSameGame", ["ATL @ NO"], None) is None
    assert tc("slipSameGame", [], None) is None


def test_a_whole_stack_counts_once_its_joint_chance_is_measured(tc):
    """The stack's three legs are one unit (ff-jarvis 12.32 measured them together); a fourth leg of that game is not."""
    assert tc("slipSameGame", ["ATL @ NO"], "SEA @ SF") is None
    assert tc("slipSameGame", ["ATL @ NO", "SEA @ SF"], "SEA @ SF") == "SEA @ SF"


def test_the_note_says_they_move_together_and_no_combined_chance_is_shown(tc):
    note = tc("t('slips.joint.note')")
    assert "move together" in note and "combined chance isn't shown" in note
