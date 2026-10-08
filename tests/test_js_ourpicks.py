"""Our pick, one per line (data/ourpicks.js, Node; Slips by kickoff window, David 2026-10-08, ledger #33).

"Our model is claude + model": where Claude and the model take the same side of a line the page shows that one
side as our pick; where they split it shows no side. A window leads with the games whose best pick is
Confident or Very confident, strongest first; the rest keep their kickoff order."""
import pytest

FILES = ("data/topcalls.js", "data/ourpicks.js")

VERY = {"side": "lower", "tier": "very", "q": 74.4}
CONF = {"side": "higher", "tier": "confident", "q": 63}
SLIGHT = {"side": "lower", "tier": "slight", "q": 56}


@pytest.fixture(scope="module")
def op(node_js):
    return node_js(*FILES)


def line(n, call, called=True, mkt="REC"):
    return {"i": 0, "slug": n.lower().replace(" ", "-"), "n": n, "pos": "WR", "team": "ATL", "mkt": mkt,
            "line": 40.5, "call": call, "called": called}


def ours(op, m):
    return op("opCall", m, {"side": m["side"]})


def test_same_side_is_our_pick_with_the_models_tier_and_chance(op):
    assert ours(op, VERY) == {"kind": "ours", "side": "lower", "tier": "very", "pct": 74}


def test_opposite_sides_are_a_split_with_no_side(op):
    assert op("opCall", CONF, {"side": "lower"}) == {"kind": "split"}


@pytest.mark.parametrize("m, c", [
    (VERY, None),                                              # Claude has not called the line yet
    (None, {"side": "lower"}),                                 # the model sent no tier for it
    ({"side": "lower", "tier": "none", "q": 51}, {"side": "lower"}),   # the model has no pick on it
    ({"td": True, "pct": 40}, {"side": "higher"}),             # a touchdown has no sides
])
def test_no_pick_without_both_sides(op, m, c):
    assert op("opCall", m, c) is None


def test_a_game_lists_its_picks_strongest_first_and_its_splits_apart(op):
    lines = [line("Slight Guy", {"kind": "ours", "side": "lower", "tier": "slight", "pct": 58}),
             line("Split Guy", {"kind": "split"}),
             line("Conf Guy", {"kind": "ours", "side": "higher", "tier": "confident", "pct": 61}),
             line("Very Guy", {"kind": "ours", "side": "lower", "tier": "very", "pct": 71}),
             line("Uncalled Guy", None, called=False)]
    g = op("opGame", lines)
    assert [x["n"] for x in g["picks"]] == ["Very Guy", "Conf Guy", "Slight Guy"]
    assert [x["n"] for x in g["split"]] == ["Split Guy"]
    assert g["called"] is True and g["lead"] is True


def test_a_game_claude_has_not_called_has_no_pick_and_says_so(op):
    g = op("opGame", [line("A", None, called=False), line("B", None, called=False)])
    assert g == {"picks": [], "split": [], "called": False, "lead": False}


def test_a_slight_best_pick_does_not_lead(op):
    g = op("opGame", [line("Slight Guy", {"kind": "ours", "side": "lower", "tier": "slight", "pct": 58})])
    assert g["lead"] is False


def game(name, best=None):
    picks = [{"n": name, "tier": best[0], "pct": best[1]}] if best else []
    lead = bool(best) and best[0] in ("confident", "very")
    return {"game": name, "op": {"picks": picks, "split": [], "called": True, "lead": lead}}


def test_a_window_leads_with_confident_games_strongest_first_then_kickoff_order(op):
    games = [game("Early Slight", ("slight", 59)), game("No Pick"), game("Conf 62", ("confident", 62)),
             game("Very 70", ("very", 70)), game("Conf 66", ("confident", 66)), game("Late Slight", ("slight", 57))]
    assert [g["game"] for g in op("opOrder", games)] == ["Very 70", "Conf 66", "Conf 62", "Early Slight", "No Pick", "Late Slight"]
