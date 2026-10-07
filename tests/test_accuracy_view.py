"""This week > Recap > Accuracy (2026-10-05): how far our projection missed each week, beside FantasyPros, from
ff-jarvis's accuracy.json (LIVE_ACCURACY, design/accuracy.py). The page computes nothing: every number it prints
is the file's own, so these tests read the fixture (tests/fixtures/data/accuracy.json, weeks 1-3 real, rank fields
and season_to_date null) and compare the page to it digit for digit.

Node: the cut (data/accuracy.js acView) and the card (surface/recap/accuracy.js acHTML). Browser: the tab and the
360px fit, which are layout and taps, on Recap mounted alone (tests/component.py; reads in tests/pages/accuracy.py);
the hash is a journey on the full page."""
import copy
import json
import pathlib
import re

import pytest

from component import Mounter, mount  # noqa: F401  (the fixture)
from pages.accuracy import AccuracyPage
from test_render import open_at

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "data" / "accuracy.json"
RAW = json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def ac(node_js):
    return node_js("data/accuracy.js", "surface/recap/accuracy.js")


def text(html):
    """What a reader sees: tags gone, entities left alone."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def with_season(raw=RAW, **over):
    out = copy.deepcopy(raw)
    row = lambda d, ci: {  # noqa: E731
        "all": {"n": 80, "mae": 4.5, "bias": 0.1, "bias_ci": [-0.4, 0.6]},
        "shared": {"n": 49, "mae_ours": 5.4, "mae_fp": 5.1, "bias_ours": 0.2, "bias_fp": -0.1,
                   "d": d, "d_ci": ci, "d_t": 1.1}}
    out["season_to_date"] = {"weeks": [1, 2, 3], "generated": "2026-10-05T06:00", "stale": False, "by_pos": {
        "QB": row(0.12, [-0.2, 0.44]), "RB": row(0.41, [0.12, 0.7]), "WR": row(-0.3, [-0.55, -0.05]),
        "TE": row(0.0, None), "ALL": row(0.05, [-0.1, 0.2])}}
    out["season_to_date"].update(over)
    return out


# ---- the cut: acView ----

def test_no_file_or_no_weeks_is_no_view(ac):
    assert ac("acView", None) is None
    assert ac("acView", {"weeks": []}) is None


def test_weeks_run_newest_first_and_carry_the_models_label(ac):
    v = ac("acView", RAW)
    assert [w["week"] for w in v["weeks"]] == [3, 2, 1]
    assert {w["model"] for w in v["weeks"]} == {"pre-blend"}
    assert v["ciLevel"] == 95


def test_every_number_in_the_view_is_the_files(ac):
    v = ac("acView", RAW)
    by_week = {w["week"]: w for w in v["weeks"]}
    positions = {}
    got = {}
    want = {}
    for raw_week in RAW["weeks"]:
        rows = {r["pos"]: r for r in by_week[raw_week["week"]]["rows"]}
        positions[raw_week["week"]] = list(rows)
        for pos, src in raw_week["by_pos"].items():
            r = rows[pos]
            got[(raw_week["week"], pos)] = (r["n"], r["ours"]["mae"], r["fp"]["mae"])
            want[(raw_week["week"], pos)] = (src["shared"]["n"], src["shared"]["ours"]["mae"], src["shared"]["fp"]["mae"])
    assert positions == {w["week"]: ["QB", "RB", "WR", "TE"] for w in RAW["weeks"]}
    assert want
    assert got == want


def test_week_3_rb_ours_5_38_against_5_11_and_fantasypros_was_closer(ac):
    row = next(r for r in ac("acView", RAW)["weeks"][0]["rows"] if r["pos"] == "RB")
    assert (row["ours"]["mae"], row["fp"]["mae"], row["closer"]) == (5.38, 5.11, "fp")


def test_closer_follows_the_smaller_miss_and_a_dead_heat_is_a_tie(ac):
    assert ac("acCloser", 4.2, 4.7) == "ours"
    assert ac("acCloser", 4.7, 4.2) == "fp"
    assert ac("acCloser", 4.2, 4.2) == "tie"
    assert ac("acCloser", None, 4.2) is None


def test_a_week_with_no_rank_fields_says_it_is_unranked(ac):
    assert all(not w["ranked"] for w in ac("acView", RAW)["weeks"])
    raw = copy.deepcopy(RAW)
    raw["weeks"][2]["by_pos"]["QB"]["shared"]["ours"].update(rho=0.61, hit=0.58)
    assert ac("acView", raw)["weeks"][0]["ranked"] is True


def test_missing_weeks_are_listed_not_graded(ac):
    raw = {**RAW, "missing_weeks": [4]}
    assert ac("acView", raw)["missing"] == [4]


def test_season_is_none_until_the_scorecard_exists(ac):
    assert ac("acView", RAW)["season"] is None


def test_season_rows_carry_the_files_d_and_range(ac):
    s = ac("acView", with_season())["season"]
    rows = {r["pos"]: r for r in s["rows"]}
    assert list(rows) == ["QB", "RB", "WR", "TE", "ALL"]
    assert (rows["RB"]["d"], rows["RB"]["ci"], rows["RB"]["closer"], rows["RB"]["clear"]) == (0.41, [0.12, 0.7], "fp", True)
    assert (rows["QB"]["closer"], rows["QB"]["clear"]) == ("fp", False)       # the range holds 0: noise
    assert (rows["WR"]["closer"], rows["WR"]["clear"]) == ("ours", True)
    assert rows["TE"]["closer"] == "tie" and rows["TE"]["ci"] is None
    assert (rows["RB"]["maeOurs"], rows["RB"]["maeFp"], rows["RB"]["n"]) == (5.4, 5.1, 49)
    assert s["range"] == "1–3" and s["stale"] is False


# ---- the card: acHTML ----

def test_week_3_rb_prints_both_numbers_and_names_fantasypros_closer(ac):
    html = ac("acHTML", ac("acView", RAW))
    week3 = html.split('data-acweek="3"')[1].split('data-acweek="2"')[0]
    rb = week3.split('data-acpos="RB"')[1].split('data-acpos="WR"')[0]
    assert "5.38" in rb and "5.11" in rb
    assert 'data-closer="fp"' in rb and "FantasyPros" in text(rb)


def test_every_week_and_position_prints_the_files_digits(ac):
    html = ac("acHTML", ac("acView", RAW))
    missing = []
    checked = 0
    for w in RAW["weeks"]:
        block = html.split(f'data-acweek="{w["week"]}"')[1]
        for pos, src in w["by_pos"].items():
            row = block.split(f'data-acpos="{pos}"')[1].split("data-acpos=")[0]
            t = text(row)
            checked += 1
            for key in ("ours", "fp"):
                digits = f'{src["shared"][key]["mae"]:.2f}'
                if digits not in t:
                    missing.append((w["week"], pos, key, digits))
    assert checked
    assert missing == []


def test_null_rank_fields_are_a_stated_empty_state_not_zeros(ac):
    t = text(ac("acHTML", ac("acView", RAW)))
    assert "not graded" in t.lower() and "rank" in t.lower()
    assert "NaN" not in t and "null" not in t and "undefined" not in t
    assert "0%" not in t and "ρ" not in t


def test_null_season_is_a_stated_empty_state_not_zeros(ac):
    html = ac("acHTML", ac("acView", RAW))
    season = html.split("data-acseason")[1].split("data-acweek=")[0]
    assert "Season to date" in text(season) and "yet" in text(season).lower()
    assert 'data-acpos' not in season                       # no row of zeros
    assert "0.00" not in text(season)


def test_season_card_prints_d_and_the_95_percent_range(ac):
    html = ac("acHTML", ac("acView", with_season()))
    season = html.split("data-acseason")[1].split("data-acweek=")[0]
    rb = season.split('data-acpos="RB"')[1].split('data-acpos="WR"')[0]
    t = text(rb)
    assert "0.41" in t and "0.12" in t and "0.70" in t and "95%" in t
    assert 'data-closer="fp"' in rb and 'data-clear="1"' in rb
    qb = season.split('data-acpos="QB"')[1].split('data-acpos="RB"')[0]
    assert 'data-clear="0"' in qb and "noise" in text(qb).lower()
    te = season.split('data-acpos="TE"')[1].split('data-acpos="ALL"')[0]
    assert "no range" in text(te).lower()


def test_ranks_print_when_the_file_has_them(ac):
    raw = copy.deepcopy(RAW)
    q = raw["weeks"][2]["by_pos"]["QB"]["shared"]
    q["ours"].update(rho=0.61, hit=0.58)
    q["fp"].update(rho=0.62, hit=0.5)
    q["hit_n"] = 12
    q["rank_n"] = 31
    qb = ac("acHTML", ac("acView", raw)).split('data-acweek="3"')[1].split('data-acpos="RB"')[0]
    t = text(qb)
    assert "0.61" in t and "0.62" in t and "58%" in t and "50%" in t and "12" in t


def test_the_model_line_names_what_was_live_and_a_stale_season_says_so(ac):
    t = text(ac("acHTML", ac("acView", RAW)))
    assert t.count("before the line blend") == 3
    stale = text(ac("acHTML", ac("acView", with_season(stale=True))))
    assert "ahead" in stale
    blend = copy.deepcopy(RAW)
    blend["weeks"][2]["model"] = "blend"
    assert "with the line blend" in text(ac("acHTML", ac("acView", blend)))


def test_a_week_not_graded_yet_is_named_and_a_model_label_is_escaped(ac):
    raw = {**copy.deepcopy(RAW), "missing_weeks": [4]}
    raw["weeks"][2]["model"] = "<b>x</b>"
    html = ac("acHTML", ac("acView", raw))
    assert "Week 4 is not graded yet" in text(html)
    assert "<b>x</b>" not in html and "&lt;b&gt;x" in html


# ---- the tab: browser ----

PHONE = (360, 800)


def planted(fragment, name, value):
    """The built page's data with `const NAME = ...;` replaced by `value`: a const, so the data is rewritten."""
    m = re.search(rf"const {name} = (.*?);\n", fragment)
    assert m, f"{name} is not in the built page"
    return fragment[:m.start()] + f"const {name} = {json.dumps(value)};\n" + fragment[m.end():]


@pytest.fixture(scope="module")
def without(mount, built, tmp_path_factory):
    """`without("LIVE_RECAP")` mounts Recap on a build whose block is null (a week with no recap file, or no
    accuracy file): (page, errors). It builds on `mount` (same browser), so a test that asks for it is a component test."""
    made = {}

    def mount_without(name):
        if name not in made:
            made[name] = Mounter(mount.browser, tmp_path_factory.getbasetemp() / f"component-accuracy-{name}",
                                 planted(built.fragment, name, None))
        return made[name]("weekrecap", size=PHONE)
    yield mount_without
    for m in made.values():
        m.pages.close()


@pytest.mark.render
def test_accuracy_is_the_fourth_tab_and_opens_the_card(mount):
    page, errors = mount("weekrecap", size=PHONE)
    acc = AccuracyPage(page)
    acc.open()
    assert acc.tab_names() == ["Players", "Scores", "Claude", "Accuracy"]
    assert acc.open_tab() == "accuracy"
    assert acc.week_cards() == 3
    assert acc.sideways() <= 0
    assert errors == []


@pytest.mark.render
@pytest.mark.journey
def test_the_accuracy_hash_opens_the_recap_on_that_tab(browser, page_file):
    ctx, page, errors = open_at(browser, page_file, PHONE, hash_="#accuracy")
    page.wait_for_selector(".wr-body")
    assert AccuracyPage(page).open_tab() == "accuracy"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_accuracy_is_reachable_with_no_recap_week(without):
    """LIVE_RECAP absent (a week with no recap file): Accuracy is still listed and opens, with no banner."""
    page, errors = without("LIVE_RECAP")
    acc = AccuracyPage(page)
    assert acc.open_tab() == "accuracy"
    assert acc.week_cards() == 3
    assert acc.empty_states() == 0
    assert errors == []


@pytest.mark.render
def test_no_accuracy_file_hides_the_tab(without):
    page, errors = without("LIVE_ACCURACY")
    assert AccuracyPage(page).tab_listed() == 0
    assert errors == []
