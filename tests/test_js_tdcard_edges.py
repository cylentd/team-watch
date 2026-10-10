"""Anytime TDs edges (data/tdwhy.js, data/tdcard.js, 2026-10-09), in Node: teen ordinals, every group's rule line
when a value is missing, a tier record of zero wins, the countdown at a minute's boundary, and a game at the exact
kickoff instant. The happy path is test_js_tdcard.py."""
import pytest

pytestmark = pytest.mark.req("Parlay and DFS", ac="Anytime TDs card")

RULES = {"lock_min_p": 0.55, "value_min_p": 0.3, "value_min_checks": 3, "list_min_p": 0.2}
KICK = "2026-09-13T17:00:00Z"
PROPS = [{"commence": "2026-09-13 17:00:00", "win": "morning", "slug": "a", "mkt": "TD"}]


@pytest.fixture(scope="module")
def td(node_js):
    return node_js("data/tdwhy.js", "data/tdcard.js")


def test_the_sheets_role_check_names_the_chips(td):
    row = {"pos": "WR", "checks": [{"key": "role_up", "passed": True, "value": ["RISING", "ROUTES_FIRST"]}]}
    assert td("tdSheetChecks", row)["rows"][0]["num"] == "Rising, New role"
    assert td("tdSheetChecks", {"checks": [{"key": "role_up", "passed": False, "value": []}]})["rows"][0]["num"] == ""


def test_teens_end_in_th(td):
    assert [td("tdOrd", n) for n in (10, 11, 12, 13, 14, 19, 20, 111, 113, 121)] == [
        "10th", "11th", "12th", "13th", "14th", "19th", "20th", "111th", "113th", "121st"]


def test_each_rule_line_needs_its_values(td):
    assert td("tdRuleLine", "MORE", RULES) == "Book 30%+, under 3 checks"
    assert td("tdRuleLine", "MORE", {**RULES, "value_min_checks": None}) == ""
    assert td("tdRuleLine", "MORE", {**RULES, "value_min_p": None}) == ""
    assert td("tdRuleLine", "VALUE", {**RULES, "value_min_checks": 0}) == "Book 30%+ and 0 of 6 checks"
    assert td("tdRuleLine", "VALUE", {**RULES, "value_min_checks": None}) == ""
    assert td("tdRuleLine", "LONG", {**RULES, "value_min_p": None}) == ""
    assert td("tdRuleLine", "LOCK", {**RULES, "lock_min_p": None}) == ""
    assert td("tdRuleLine", "SMASH", RULES) == ""
    assert td("tdRuleLine", "LOCK", None) == ""


def test_a_tier_record_prints_even_with_no_wins(td):
    assert td("tdTierRecord", "VALUE", {"VALUE": {"w": 0, "l": 3, "weeks": "5"}}) == "0-3 in weeks 5"
    assert td("tdTierRecord", "LOCK", {"LOCK": {"w": 38, "l": 18, "weeks": "1-4"}}) == "38-18 in weeks 1-4"
    assert td("tdTierRecord", "VALUE", {"VALUE": {"w": None, "l": 0}}) == ""
    assert td("tdTierRecord", "VALUE", None) == ""
    assert td("tdTierRecord", "VALUE", {"LOCK": {"w": 1, "l": 0, "weeks": "1"}}) == ""


def test_the_countdown_rounds_up_to_the_minute(td):
    assert td("tdLeft", 60000, 0) == "in 1m"
    assert td("tdLeft", 60001, 0) == "in 2m"
    assert td("tdLeft", 59999, 0) == "in 1m"
    assert td("tdLeft", 3600000, 0) == "in 1h 0m"
    assert td("tdLeft", 3540001, 0) == "in 1h 0m"
    assert td("tdLeft", 3540000, 0) == "in 59m"


def test_a_game_at_its_kickoff_instant_is_gone(td):
    block = {"players": [{"name": "A", "kickoff": KICK, "tier": "LOCK", "book": {"p": 0.6}}]}
    pending = [{"kickoff": KICK, "expected_at": "2026-09-13T13:00:00Z"}]
    at = td(f"Date.parse('{KICK}')")
    assert [r["name"] for r in td("tdRows", block, ["morning"], PROPS, at - 1)] == ["A"]
    assert td("tdRows", block, ["morning"], PROPS, at) == []
    assert td("tdPendingAt", pending, ["morning"], PROPS, at - 1) == td("Date.parse('2026-09-13T13:00:00Z')")
    assert td("tdPendingAt", pending, ["morning"], PROPS, at) is None
