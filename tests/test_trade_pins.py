"""League > Trades, the pinned files (ledger #65, 2026-10-08): ff-jarvis's trade_pins/ (index.json and one file per owner) is
checked where it enters and copied beside the page by design/trade_pins.py, and the page fetches the owner's file the index
names (tests/test_js_trade_pins.py). Built here from a hand-made owner file in the producer's shape (model.season.
trade_pins_schema): players by key, offers that name those keys, get / send / pairs that name offers by index."""
import copy
import json
import pathlib
import re
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "design"))
import contract  # noqa: E402
import sources  # noqa: E402
import trade_offers  # noqa: E402
import trade_pins  # noqa: E402
from conftest import REPO  # noqa: E402

OWNER, PARTNER = "Purdy Big in Japan", "Run It Back"


def player(name, holder, **kw):
    slug = name.lower().replace(" ", "-")
    return {"name": name, "pos": "WR", "team": "SEA", "slug": slug, "seen": 12.5, "injury": None, "last2": None,
            "chips": [], "holder": holder, **kw}


def owner_doc(league="espn", owner=OWNER):
    """One owner's file: his Brock Purdy for their Puka Nacua, and a second player nobody has an offer for."""
    return {
        "updated": "2026-10-08T05:00", "league": league, "owner": owner,
        "players": {"brock purdy": player("Brock Purdy", owner, pos="QB"), "puka nacua": player("Puka Nacua", PARTNER),
                    "tee higgins": player("Tee Higgins", owner), "nobody": player("Nobody Here", PARTNER)},
        "offers": [{"partner": PARTNER, "send": ["brock purdy"], "get": ["puka nacua"], "gain": 4.5, "drop": [], "ir_moves": [],
                    "their": {"ir_moves": [], "drop": [], "gain": 1.5}}],
        "get": {"puka nacua": [0], "nobody": {"reason": "lens_gate"}},
        "send": {"brock purdy": {PARTNER: 0}, "tee higgins": {"reason": "no_gain_for_him"}},
        "pairs": []}


def index_doc(*files):
    """An index naming each (league, owner, path)."""
    leagues = {}
    for league, owner, path in files:
        leagues.setdefault(league, {})[owner] = path
    return {"updated": "2026-10-08T05:00", "rules": {"get_n": 5}, "leagues": leagues}


class Source:
    """A pins folder as ff-jarvis writes it, in a temp dir."""

    def __init__(self, tmp_path, docs=None, index=None):
        self.dir = tmp_path / "src" / "trade_pins"
        docs = docs if docs is not None else {"espn/purdy.json": owner_doc()}
        for path, doc in docs.items():
            (self.dir / path).parent.mkdir(parents=True, exist_ok=True)
            (self.dir / path).write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        listed = [(d["league"], d["owner"], p) for p, d in docs.items()]
        self.index = index if index is not None else index_doc(*listed)
        (self.dir / "index.json").parent.mkdir(parents=True, exist_ok=True)
        (self.dir / "index.json").write_text(json.dumps(self.index), encoding="utf-8")


def tree(folder):
    return {p.relative_to(folder).as_posix(): p.read_text(encoding="utf-8") for p in sorted(folder.rglob("*")) if p.is_file()}


# ---- the folder is copied beside the page ---------------------------------------------------------------------------

def test_the_index_and_every_owner_file_are_written_beside_the_page(tmp_path):
    src = Source(tmp_path, {"espn/purdy.json": owner_doc(), "yahoo/chat.json": owner_doc("yahoo", "Chat Take the Wheel")})
    repo = tmp_path / "repo"
    repo.mkdir()
    trade_pins.build(repo, src.dir)
    got = tree(repo / "trade_pins")
    assert sorted(got) == ["espn/purdy.json", "index.json", "yahoo/chat.json"]
    assert json.loads(got["index.json"]) == src.index
    assert json.loads(got["espn/purdy.json"]) == owner_doc()
    assert json.loads(got["yahoo/chat.json"]) == owner_doc("yahoo", "Chat Take the Wheel")


def test_the_files_are_written_compact_with_a_team_name_as_written(tmp_path):
    name = "Chat Take the Wheel \U0001F47E"
    src = Source(tmp_path, {"yahoo/chat.json": owner_doc("yahoo", name)})
    repo = tmp_path / "repo"
    repo.mkdir()
    trade_pins.build(repo, src.dir)
    text = (repo / "trade_pins" / "yahoo" / "chat.json").read_text(encoding="utf-8")
    assert text == json.dumps(owner_doc("yahoo", name), ensure_ascii=False, separators=(",", ":"))


def test_the_summary_line_counts_the_owners_and_says_where_it_wrote(tmp_path):
    src = Source(tmp_path, {"espn/purdy.json": owner_doc(), "yahoo/chat.json": owner_doc("yahoo", "Chat Take the Wheel")})
    repo = tmp_path / "repo"
    repo.mkdir()
    line = trade_pins.build(repo, src.dir)
    assert line.startswith("Trade pins: espn 1 owner, yahoo 1 owner, updated 2026-10-08T05:00; "), line
    assert line.endswith(" KB to trade_pins/"), line


def test_a_file_the_index_no_longer_lists_is_removed(tmp_path):
    src = Source(tmp_path)
    repo = tmp_path / "repo"
    (repo / "trade_pins" / "espn").mkdir(parents=True)
    (repo / "trade_pins" / "espn" / "gone.json").write_text("{}", encoding="utf-8")
    trade_pins.build(repo, src.dir)
    assert sorted(tree(repo / "trade_pins")) == ["espn/purdy.json", "index.json"]


def test_with_no_source_nothing_is_written_and_what_was_there_stays(tmp_path):
    repo = tmp_path / "repo"
    (repo / "trade_pins").mkdir(parents=True)
    (repo / "trade_pins" / "index.json").write_text("{}", encoding="utf-8")
    line = trade_pins.build(repo, tmp_path / "nowhere")
    assert line == "Trade pins: none from ff-jarvis, so a player's trade page fills from today's offers"
    assert tree(repo / "trade_pins") == {"index.json": "{}"}


def test_with_no_source_and_nothing_written_before_the_folder_is_not_created(tmp_path):
    trade_pins.build(tmp_path, tmp_path / "nowhere")
    assert not (tmp_path / "trade_pins").exists()


def test_the_default_source_is_the_folder_in_ff_jarvis_data(tmp_path, monkeypatch):
    src = Source(tmp_path)
    monkeypatch.setattr(sources, "DWR", src.dir.parent)
    repo = tmp_path / "repo"
    repo.mkdir()
    trade_pins.build(repo)
    assert sorted(tree(repo / "trade_pins")) == ["espn/purdy.json", "index.json"]


def test_the_build_calls_it_beside_the_other_files_the_page_fetches():
    text = (REPO / "design" / "build.py").read_text(encoding="utf-8")
    assert "trade_pins.build(REPO)" in text, "build.py must write the pinned files each run"


def test_vercel_serves_the_folder_git_marks_it_generated_and_land_folds_it_in():
    assert f"!{trade_pins.NAME}" in (REPO / ".vercelignore").read_text(encoding="utf-8").split(), ".vercelignore is an allowlist"
    attrs = (REPO / ".gitattributes").read_text(encoding="utf-8")
    assert re.search(rf"^{trade_pins.NAME}/\*\*\s+-diff merge=ours", attrs, re.M)
    assert f'"{trade_pins.NAME}"' in (REPO / "scripts" / "land.ps1").read_text(encoding="utf-8")
    assert f'"{trade_pins.NAME}"' in (REPO / ".testsched.json").read_text(encoding="utf-8"), "a rebuilt folder is not a dirty tree"


# ---- a file the page cannot read stops the build, before anything is written -----------------------------------------

def fails(tmp_path, **kw):
    src = Source(tmp_path, **kw)
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(contract.ContractError) as e:
        trade_pins.build(repo, src.dir)
    assert not (repo / "trade_pins").exists(), "a bad file must not leave a half-written folder"
    return str(e.value)


@pytest.mark.parametrize("bad,missing", [
    ({"rules": {}, "leagues": {"espn": {OWNER: "espn/purdy.json"}}}, "TRADE_PINS index.updated"),
    ({"updated": "t", "rules": {}}, "TRADE_PINS index.leagues"),
    ({"updated": "t", "rules": {}, "leagues": {}}, "TRADE_PINS index.leagues"),
    ({"updated": "t", "rules": {}, "leagues": {"espn": {}}}, "TRADE_PINS index.leagues['espn']"),
    ({"updated": "t", "rules": {}, "leagues": {"espn": {OWNER: "../purdy.json"}}}, f"TRADE_PINS index.leagues['espn'][{OWNER!r}]"),
    ({"updated": "t", "rules": {}, "leagues": {"espn": {OWNER: "yahoo/purdy.json"}}}, f"TRADE_PINS index.leagues['espn'][{OWNER!r}]"),
    ({"updated": "t", "rules": {}, "leagues": {"espn": {OWNER: "espn/purdy.txt"}}}, f"TRADE_PINS index.leagues['espn'][{OWNER!r}]"),
    ({"updated": "t", "rules": {}, "leagues": {"espn": {OWNER: "espn/a/b.json"}}}, f"TRADE_PINS index.leagues['espn'][{OWNER!r}]"),
    ({"updated": "t", "rules": {}, "leagues": {"espn": {OWNER: 7}}}, f"TRADE_PINS index.leagues['espn'][{OWNER!r}]"),
])
def test_an_index_that_does_not_name_each_owners_file_fails_the_build(tmp_path, bad, missing):
    assert missing in fails(tmp_path, index=bad)


def test_an_index_that_is_not_an_object_fails_the_build(tmp_path):
    assert "TRADE_PINS index" in fails(tmp_path, index=["espn/purdy.json"])


def test_two_owners_sharing_one_file_fail_the_build(tmp_path):
    index = index_doc(("espn", OWNER, "espn/purdy.json"), ("espn", PARTNER, "espn/purdy.json"))
    assert "espn/purdy.json" in fails(tmp_path, docs={"espn/purdy.json": owner_doc()}, index=index)


def test_a_listed_file_that_is_missing_fails_the_build_naming_it(tmp_path):
    index = index_doc(("espn", OWNER, "espn/purdy.json"), ("espn", PARTNER, "espn/run.json"))
    assert "espn/run.json" in fails(tmp_path, docs={"espn/purdy.json": owner_doc()}, index=index)


def test_a_file_that_is_not_json_fails_the_build_naming_it(tmp_path):
    src = Source(tmp_path)
    (src.dir / "espn" / "purdy.json").write_text("{not json", encoding="utf-8")
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(contract.ContractError, match="espn/purdy.json"):
        trade_pins.build(repo, src.dir)


@pytest.mark.parametrize("league,owner", [("yahoo", OWNER), ("espn", PARTNER)])
def test_a_file_for_another_league_or_owner_than_the_index_says_fails_the_build(tmp_path, league, owner):
    wrong = owner_doc()
    wrong["league"], wrong["owner"] = league, owner
    assert "espn/purdy.json" in fails(tmp_path, docs={"espn/purdy.json": wrong}, index=index_doc(("espn", OWNER, "espn/purdy.json")))


# ---- the owner file's shape: every field the page reads --------------------------------------------------------------

def edited(change):
    doc = owner_doc()
    change(doc)
    return doc


def drop_key(path):
    def change(doc):
        *parents, last = path
        target = doc
        for k in parents:
            target = target[k]
        del target[last]
    return change


def put(path, value):
    def change(doc):
        *parents, last = path
        target = doc
        for k in parents:
            target = target[k]
        target[last] = value
    return change


BAD = [
    ("no updated", drop_key(["updated"]), ".keys"),
    ("an extra key", put(["surprise"], 1), ".keys"),
    ("no pairs", drop_key(["pairs"]), ".keys"),
    ("an empty updated", put(["updated"], ""), ".updated"),
    ("an unknown league", put(["league"], "nfl"), ".league"),
    ("no owner", put(["owner"], ""), ".owner"),
    ("no players", put(["players"], {}), ".players"),
    ("a player with no slug", drop_key(["players", "brock purdy", "slug"]), ".players['brock purdy'].slug"),
    ("a player with no holder", drop_key(["players", "puka nacua", "holder"]), ".players['puka nacua'].holder"),
    ("a player with no injury key", drop_key(["players", "tee higgins", "injury"]), ".players['tee higgins'].injury"),
    ("a player with no chips", drop_key(["players", "tee higgins", "chips"]), ".players['tee higgins'].chips"),
    ("chips that are not a list", put(["players", "tee higgins", "chips"], "Hot"), ".players['tee higgins'].chips"),
    ("offers that are not a list", put(["offers"], {}), ".offers"),
    ("an offer with no partner", drop_key(["offers", 0, "partner"]), ".offers[0].partner"),
    ("an offer with no gain", drop_key(["offers", 0, "gain"]), ".offers[0].gain"),
    ("a gain that is a string", put(["offers", 0, "gain"], "4.5"), ".offers[0].gain"),
    ("an offer sending nobody", put(["offers", 0, "send"], []), ".offers[0].send"),
    ("an offer getting nobody", put(["offers", 0, "get"], []), ".offers[0].get"),
    ("a send key with no player", put(["offers", 0, "send"], ["ghost"]), ".offers[0].send[0]"),
    ("a get key with no player", put(["offers", 0, "get"], ["ghost"]), ".offers[0].get[0]"),
    ("a drop key with no player", put(["offers", 0, "drop"], ["ghost"]), ".offers[0].drop[0]"),
    ("an ir move with no player", put(["offers", 0, "ir_moves"], ["ghost"]), ".offers[0].ir_moves[0]"),
    ("no drop list", drop_key(["offers", 0, "drop"]), ".offers[0].drop"),
    ("no their", drop_key(["offers", 0, "their"]), ".offers[0].their"),
    ("their with no gain", drop_key(["offers", 0, "their", "gain"]), ".offers[0].their.gain"),
    ("their drop with no player", put(["offers", 0, "their", "drop"], ["ghost"]), ".offers[0].their.drop[0]"),
    ("their ir move with no player", put(["offers", 0, "their", "ir_moves"], ["ghost"]), ".offers[0].their.ir_moves[0]"),
    ("a bad lens field", put(["offers", 0, "score"], "x"), ".offers[0].score"),
    ("get that is not an object", put(["get"], []), ".get"),
    ("a get index past the offers", put(["get", "puka nacua"], [1]), ".get['puka nacua'][0]"),
    ("a get index that is a string", put(["get", "puka nacua"], ["0"]), ".get['puka nacua'][0]"),
    ("a get entry that is empty", put(["get", "puka nacua"], []), ".get['puka nacua']"),
    ("a get entry that is a number", put(["get", "puka nacua"], 0), ".get['puka nacua']"),
    ("a get reason that is not a string", put(["get", "nobody"], {"reason": 3}), ".get['nobody']"),
    ("get naming a player with no entry in players", put(["get", "ghost"], [0]), ".get['ghost']"),
    ("send that is not an object", put(["send"], None), ".send"),
    ("a send index past the offers", put(["send", "brock purdy", PARTNER], 5), f".send['brock purdy'][{PARTNER!r}]"),
    ("a send index that is a bool", put(["send", "brock purdy", PARTNER], True), f".send['brock purdy'][{PARTNER!r}]"),
    ("a send entry that is empty", put(["send", "brock purdy"], {}), ".send['brock purdy']"),
    ("a send reason that is not a string", put(["send", "tee higgins"], {"reason": None}), ".send['tee higgins']"),
    ("pairs that are not a list", put(["pairs"], {}), ".pairs"),
    ("a pair of one", put(["pairs"], [{"send": ["brock purdy"], "offer": 0}]), ".pairs[0].send"),
    ("a pair with an offer past the list", put(["pairs"], [{"send": ["a", "b"], "offer": 3}]), ".pairs[0].offer"),
]


@pytest.mark.parametrize("what,change,where", BAD, ids=[b[0] for b in BAD])
def test_an_owner_file_the_page_cannot_read_names_the_field(what, change, where):
    got = trade_pins.owner_problems(edited(change), "TRADE_PINS espn/purdy.json")
    assert any(where in p for p in got), (what, got)


def test_the_hand_made_owner_file_has_no_problem():
    assert trade_pins.owner_problems(owner_doc(), "T") == []


def test_a_pair_the_file_lists_is_two_of_the_players_and_an_offer():
    doc = owner_doc()
    doc["pairs"] = [{"send": ["brock purdy", "tee higgins"], "offer": 0}]
    assert trade_pins.owner_problems(doc, "T") == []


def test_a_file_that_is_not_an_object_is_one_problem():
    assert trade_pins.owner_problems([], "T") == ["T"]


def test_the_problems_stop_at_the_limit_so_a_bad_file_does_not_print_a_page():
    doc = owner_doc()
    doc["offers"] = [{"partner": "", "send": [], "get": [], "gain": None} for _ in range(40)]
    got = trade_pins.owner_problems(doc, "T")
    assert trade_offers.LIMIT <= len(got) < 2 * trade_offers.LIMIT, "stops early, not after all 40 offers"


def test_the_error_names_the_file_and_the_field(tmp_path):
    bad = owner_doc()
    del bad["offers"][0]["gain"]
    msg = fails(tmp_path, docs={"espn/purdy.json": bad}, index=index_doc(("espn", OWNER, "espn/purdy.json")))
    assert msg.startswith("contract: TRADE_PINS espn/purdy.json") and ".offers[0].gain" in msg, msg
