"""Preview's game page, ledger #82 (David, 2026-10-07: the players section "is the best part and is buried"; clean
up what is under it; the Moneyline / Spread / Total rows, Vegas beside Claude, "hard to read"). Storyboard draft A,
"Ledger", 2026-10-09: players first, each with the yards our model expects and his chance to score; each bet as
Vegas's number beside ours in the same unit, then the pick; the story's first paragraph, the rest one tap away;
the research under it. Component tests: Preview mounted at a phone's size, read through `PreviewDossier`."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.preview import PreviewPage
from pages.preview_dossier import PreviewDossier
from wording import words

PHONE = (360, 800)
# No endless scroll (VISION 2026-10-08): a game's page ends inside three phone screens with the story closed.
# Before ledger #82 the fixture's DET @ CAR ran past four, the live CHI @ GB to 4,700px.
DOSSIER_MAX_SCREENS = 3
DET_CAR, ATL_NO, SEA_SF = 2, 4, 3


@pytest.fixture
def dossier(mount):
    page, errors = mount("preview", size=PHONE, touch=True)
    return PreviewPage(page), PreviewDossier(page), errors


@pytest.mark.render
@pytest.mark.req("Preview", ac="players lead the game page")
def test_the_headline_leads_then_the_players_the_bets_and_the_research(dossier):
    """David, 2026-10-09: "i dont exactly love the players on top. The headline is gone! maybe swap?" """
    pv, dz, errors = dossier
    pv.tap_game(DET_CAR)
    assert dz.parts() == ["pvn-head", "pvn-pl", "pvn-ans", "pvn-call", "pvn-box"]
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Preview", ac="a player shows yards and touchdown chance")
def test_a_player_with_lines_leads_with_his_yards_and_chance_to_score_and_opens_his_lines(dossier):
    pv, dz, errors = dossier
    pv.handoff.plant_game_as_sea_sf()                                   # Kittle: the fixture's props slate has his lines
    lines = {r["mkt"]: r for r in dz.lines_of("george-kittle")}
    yds, td = f"{round(lines['REC']['mu'])} {words('preview.pl.rec')}", words("preview.pl.td").replace("{n}", str(lines["TD"]["model"]))
    assert dz.player_rows() == [["G. Kittle", yds, td]]
    assert dz.yards_is_button(0)
    dz.spy_on_lines_sheet()
    dz.tap_yards(0)
    assert dz.sheets_opened() == ["george-kittle"]
    assert dz.slips_button_count() == 1
    assert errors == []


@pytest.mark.render
def test_a_player_without_lines_shows_his_projected_points_and_no_way_to_lines(dossier):
    pv, dz, errors = dossier
    pv.tap_game(DET_CAR)
    players = dz.game(DET_CAR)["take"]["players"]
    bare = [j for j, p in enumerate(players) if not dz.lines_of(p["slug"])]
    assert bare, "the fixture's DET @ CAR names players with no lines"
    rows = dz.player_rows()
    assert [rows[j][1:] for j in bare] == [[words("preview.pl.pts").replace("{n}", f"{players[j]['proj']:.1f}"), None] for j in bare]
    assert [dz.yards_is_button(j) for j in bare] == [False] * len(bare)
    assert dz.slips_button_count() == 0                                 # no game of the props slate
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Preview", ac="each bet reads Vegas beside ours in one unit")
def test_each_bet_reads_vegas_beside_ours_in_the_same_unit_then_the_pick(dossier):
    pv, dz, errors = dossier
    pv.tap_game(DET_CAR)                                                # DET 30, CAR 19; Vegas DET by 3.5, 50.5
    assert dz.bet_heads() == ["", words("preview.ans.vegas"), words("preview.ans.ours"), words("preview.ans.pickcol")]
    assert dz.bet_rows() == [[words("preview.bet.ml"), "DET 64%", "DET 74%", "DET wins"],
                             [words("preview.bet.spread"), "DET by 3.5", "DET by 11", f"DET covers {words('preview.conf.solid')}"],
                             [words("preview.bet.total"), "50.5", "49", f"Under {words('preview.conf.lean')}"]]
    pv.step(1)
    pv.step(1)                                                          # ATL @ NO: no take, Vegas only
    assert [r[2:] for r in dz.bet_rows()] == [["–", "–"]] * 3
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Preview", ac="the story opens past its first paragraph")
def test_the_story_shows_its_first_paragraph_and_the_risk_and_the_rest_is_one_tap_away(dossier):
    pv, dz, errors = dossier
    pv.tap_game(DET_CAR)
    paras = dz.all_deks()
    assert len(paras) == 3
    assert dz.visible_deks() == paras[:1]
    assert dz.risk_visible()
    dz.open_rest_of_story()
    assert dz.visible_deks() == paras
    assert errors == []


@pytest.mark.render
def test_a_one_paragraph_story_has_nothing_to_open(dossier):
    pv, dz, errors = dossier
    pv.tap_game(0)                                                      # PIT @ CLE
    assert len(dz.all_deks()) == 1 and dz.more_count() == 0
    assert errors == []


@pytest.mark.render
def test_defense_rank_is_one_row_per_offense_with_the_wr_column_faded(dossier):
    pv, dz, errors = dossier
    pv.tap_game(DET_CAR)
    g = dz.game(DET_CAR)
    pos = ["QB", "RB", "WR", "TE"]
    want = [[""] + pos] + [[words("preview.mx.side").replace("{off}", t)] + [str(g["matchup"][t]["pos"][p]["rank"]) for p in pos]
                           for t in (g["away"], g["home"])]
    assert dz.matchup_grid() == want
    assert dz.dim_heads() == ["WR"]                                     # the backtest finds the WR matchup moves nothing
    assert errors == []


@pytest.mark.render
@pytest.mark.parametrize("i", range(5))
def test_a_game_page_ends_inside_three_screens(dossier, i):
    pv, dz, errors = dossier
    pv.show_game(i)
    assert dz.article_height() <= DOSSIER_MAX_SCREENS * PHONE[1]
    assert pv.scroll_width() <= PHONE[0]
    assert errors == []
