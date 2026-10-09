"""Stats > Ranks reads ff-jarvis's week_ranks (ledger #23, 2026-10-08, METHODOLOGY 12.116/12.117): our rank and
tiers per position and FLEX, `val` the order key (never shown), `src` whose number it is (never shown). The
roster cards' rank reads the same lists, so the two never disagree. A build without the file keeps the old
cut (natural breaks of our projections, ledger #96), and says so in its report line. No browser here: the view's own
test is test_ranks.py."""
import copy
import json
import pathlib

import pytest

import build
import contract
import sources
import week_ranks
from projections import live_projections
from ranks import live_ranks, ranks_places, report as ranks_report
from test_build import injected

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "data" / "week_ranks.json"
DOC = json.loads(FIXTURE.read_text(encoding="utf-8"))
PROJ = json.loads((FIXTURE.parent / "player_projections.json").read_text(encoding="utf-8"))
SLUGS = {p["name"]: p["name"].lower().replace(".", "").replace(" ", "-") for p in PROJ["players"]}


def slug(name):
    return SLUGS.get(name) or name.lower().replace(".", "").replace(" ", "-")


def edited(path, value):
    """A copy of the fixture with one field changed: path is a tuple of keys and list indexes."""
    doc = copy.deepcopy(DOC)
    node = doc
    for step in path[:-1]:
        node = node[step]
    node[path[-1]] = value
    return doc


def rows(block, pos):
    return [r for r in block["rows"] if r["pos"] == pos]


def test_the_fixture_file_meets_its_own_contract():
    assert week_ranks.problems(DOC) == []


@pytest.mark.parametrize("doc, where", [
    (edited(("v",), 3), "v"),
    (edited(("weekly", "scoring"), "ppr"), "weekly.scoring"),
    (edited(("weekly", "lists", "RB", 1, "rank"), 5), "weekly.lists.RB[1].rank"),
    (edited(("weekly", "lists", "RB", 1, "tier"), 3), "weekly.lists.RB[1].tier"),
    (edited(("weekly", "lists", "RB", 1, "val"), 20.0), "weekly.lists.RB[1].val"),
    (edited(("weekly", "lists", "RB", 1, "key"), "chase brown"), "weekly.lists.RB[1].key"),
    (edited(("weekly", "lists", "RB", 0, "pts"), None), "weekly.lists.RB[0].pts"),
])
def test_a_malformed_file_is_named_where_it_is_wrong(doc, where):
    bad = week_ranks.problems(doc)
    assert [b.split(":")[0] for b in bad][:1] == [where], bad


def test_a_missing_list_or_row_field_is_named():
    no_flex = copy.deepcopy(DOC)
    del no_flex["weekly"]["lists"]["FLEX"]
    assert week_ranks.problems(no_flex)[0].startswith("weekly.lists.FLEX")
    no_opp = copy.deepcopy(DOC)
    del no_opp["weekly"]["lists"]["QB"][0]["opp"]
    assert week_ranks.problems(no_opp)[0].startswith("weekly.lists.QB[0]")
    assert week_ranks.problems({})[0].startswith("week_ranks")


def test_the_lists_set_each_positions_order_rank_and_tier():
    """(ledger #98, 2026-10-09; was #81's re-sort) ff-jarvis #88 orders and tiers on our own points, so the page draws
    each list's order, rank and tier as shipped."""
    block = live_ranks(PROJ, slug, None, None, DOC)
    rbs = rows(block, "RB")
    shipped = [(slug(r["name"]), r["rank"], r["tier"]) for r in DOC["weekly"]["lists"]["RB"]]
    assert [(r["slug"], r["rank"], r["tier"]) for r in rbs] == shipped
    assert [r["pts"] for r in rbs] == [16.2, 15.0, 3.1], "the number shown is his projection"
    assert [(r["slug"], r["tier"]) for r in rows(block, "QB")] == [("joe-burrow", 1), ("brock-purdy", 2)]
    assert (block["week"], block["off"], block["scoring"]) == (2, [], "half-PPR")


def test_flex_rows_keep_the_shipped_order_and_tier_with_their_position_rank():
    flex = live_ranks(PROJ, slug, None, None, DOC)["flex"]
    pos_rank = {slug(r["name"]): r["rank"] for p in ("QB", "RB", "WR", "TE") for r in DOC["weekly"]["lists"][p]}
    shipped = [(slug(r["name"]), pos_rank[slug(r["name"])], r["tier"]) for r in DOC["weekly"]["lists"]["FLEX"]]
    assert [(r["slug"], r["rank"], r["tier"]) for r in flex] == shipped, "rank is the place at his position, tier the FLEX list's own"


@pytest.mark.parametrize("field", ["src", "val", "key", "rank_pts", "unlined_backup", "pts_before_unlined"])
def test_a_row_shows_one_rank_whoever_made_it(field):
    block = live_ranks(PROJ, slug, None, None, DOC)
    assert [r["slug"] for r in block["rows"] + block["flex"] if field in r] == [], "the producer's bookkeeping and the books stay out"


def test_a_row_keeps_what_only_the_projections_know():
    """Home, injury, what the points are made of, the matchup and the band come from the projections row, by slug."""
    by = {r["slug"]: r for r in rows(live_ranks(PROJ, slug, None, None, DOC), "RB")}
    brown = by["chase-brown"]
    assert (brown["home"], brown["inj"], brown["mx"], brown["mxp"]) == (False, "Q", 1.4, 0.6)
    assert (by["breece-hall"]["floor"], by["breece-hall"]["ceil"]) == (6.4, 26.0), "the number shown is ours (15.0), so his band stays"
    assert brown["mu"] == {"RUSH": 75, "REC": 20, "TD": 0.4}
    assert (brown["team"], brown["opp"], brown["kick"]) == ("CIN", "NYJ", "2026-09-13T17:00:00Z"), "the game is the list's own"


def test_a_player_in_the_list_but_not_the_projections_is_still_a_row():
    doc = copy.deepcopy(DOC)
    doc["weekly"]["lists"]["QB"][1]["name"] = "Unknown Passer"
    purdy = rows(live_ranks(PROJ, slug, None, None, doc), "QB")[1]
    assert (purdy["slug"], purdy["rank"], purdy["pts"], purdy["mu"], purdy["inj"]) == ("unknown-passer", 2, 18.1, None, None)


def test_a_list_cut_by_the_producer_is_not_cut_again():
    """Out players are dropped upstream: whatever the list holds is drawn, with no status lookup here."""
    out = {"x": {"name": "Chase Brown", "injury": "Out"}}
    assert [r["slug"] for r in rows(live_ranks(PROJ, slug, out, None, DOC), "RB")] == ["chase-brown", "breece-hall", "kendre-miller"]


def test_the_cards_read_the_same_rank():
    wanted = {"breece-hall", "chase-brown", "kendre-miller", "joe-burrow", "george-kittle"}
    block = live_ranks(PROJ, slug, None, None, DOC)
    cards = live_projections(PROJ, slug, wanted, None, None, DOC, ranks=ranks_places(block))["players"]
    on_page = {r["slug"]: r["rank"] for r in block["rows"]}
    assert {s: cards[s]["rank"] for s in wanted} == {s: on_page[s] for s in wanted}
    assert cards["chase-brown"]["rank"] == 1 and cards["breece-hall"]["rank"] == 2
    assert cards["breece-hall"]["of"] == 3, "of: the length of his position's list"


def test_a_player_the_lists_do_not_hold_has_no_card_rank():
    raw = copy.deepcopy(PROJ)
    raw["players"].append({"key": "deep back", "name": "Deep Back", "pos": "RB", "team": "GB", "opp": "TB", "game": "GB @ TB", "pts": 2.0, "src": "model"})
    card = live_projections(raw, slug, {"deep-back"}, None, None, DOC)["players"]["deep-back"]
    assert (card["rank"], card["of"]) == (None, None), "ranked beyond the list's depth: no number rather than one the page disagrees with"


def test_without_the_file_the_old_cut_stands():
    old = live_ranks(PROJ, slug, None, None, None)
    assert [r["slug"] for r in rows(old, "RB")] == ["chase-brown", "breece-hall", "kendre-miller"], "our points, as on every view (ledger #96)"
    assert old["from"] == "projections"
    assert live_ranks(PROJ, slug, None, None, DOC)["from"] == "week_ranks"


def test_the_report_line_names_the_source():
    assert ranks_report(live_ranks(PROJ, slug, None, None, DOC)) == "Ranks: week_ranks · QB 2 in 2 tiers · RB 3 in 2 tiers · WR 1 in 1 tiers · TE 1 in 1 tiers · FLEX 5 in 3 tiers"
    old = ranks_report(live_ranks(PROJ, slug, None, None, None))
    assert old.startswith("Ranks: week_ranks missing, so the old cut (natural breaks of our projections) · QB 2 in")
    assert ranks_report(None) == "Ranks: none, so no Ranks view"


def test_the_block_meets_the_contract():
    assert contract.problems("LIVE_RANKS", live_ranks(PROJ, slug, None, None, DOC)) == []
    assert contract.problems("LIVE_RANKS", live_ranks(PROJ, slug, None, None, None)) == []


def test_the_feed_block_wins_over_the_file(tmp_path, monkeypatch):
    feed = tmp_path / "feed.json"
    feed.write_text(json.dumps({"week_ranks": {"data": {**DOC, "weekly": {**DOC["weekly"], "week": 9}}}}), encoding="utf-8")
    monkeypatch.setattr(sources, "FEED", feed)
    assert week_ranks.load_week_ranks()["weekly"]["week"] == 9
    feed.write_text("{}", encoding="utf-8")
    assert week_ranks.load_week_ranks()["weekly"]["week"] == 2, "no feed block: the file is read"


def test_a_malformed_feed_block_fails_the_build_not_the_page(tmp_path, monkeypatch):
    feed = tmp_path / "feed.json"
    bad = edited(("weekly", "lists", "RB", 1, "rank"), 7)
    feed.write_text(json.dumps({"week_ranks": {"data": bad}}), encoding="utf-8")
    monkeypatch.setattr(sources, "FEED", feed)
    with pytest.raises(SystemExit, match=r"weekly\.lists\.RB\[1\]\.rank"):
        week_ranks.load_week_ranks()


def test_the_fixture_build_reads_the_lists(built):
    block = injected(built.fragment)["LIVE_RANKS"]
    assert block["from"] == "week_ranks"
    assert [r["slug"] for r in block["rows"] if r["pos"] == "RB"][0] == "chase-brown", "most points leads, not the producer's first"
    assert any(line.startswith("Ranks: week_ranks ·") for line in built.report), built.report


@pytest.mark.integration      # a real build of the page
def test_no_file_builds_the_old_ranks_and_says_so(monkeypatch):
    real = sources.read_first
    monkeypatch.setattr(sources, "read_first", lambda *paths: None if any(p.name == "week_ranks.json" for p in paths) else real(*paths))
    made = build.render()
    assert injected(made.fragment)["LIVE_RANKS"]["from"] == "projections"
    assert any("week_ranks missing" in line for line in made.report), made.report
