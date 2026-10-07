"""The roster's Cards view (2026-09-25): the tier is this week's rank at the position, K and DST are
support cards with no tier, the Sheet / Cards choice survives a reload, and the week's pack opens
once. The ranks and the implied points are computed at build time; the rest renders.

Python for the build side, Node for the pure card functions (the tier, the weather words), component
(`mount`, `RosterPage`, tests/pages/roster.py) for what a card and the pack draw. The one test that
needs the headshot files mounts with `heads=True`. `on_cards` below mounts the roster; the page's
clock and its mount (`pages.roster_motion.on_motion`, `rip`, `vc_*`, `VCLOCK`) live in
tests/pages/roster_motion.py and roster_pack.py, for test_pack_stage.py and test_clip_sheet.py.
"""
import re

import pytest

from component import Mounter, mount as base_mount
from lines import live_lines
from pages.roster import RosterPage
from pages.roster_motion import show_cards
from pages.warm import warm
from projections import position_ranks

REQ = "Phone layout"       # the Roster cards and Week's pack rows
PHONE = (360, 660)


@pytest.fixture(scope="module")
def mount(base_mount):
    """`mount`, with the phone's context opened once for the module (pages/warm.py)."""
    return warm(base_mount, ("roster", PHONE))


def slug(n):
    return n.lower().replace(" ", "-")


def wr(name, slug_):
    """A starting receiver of JAX, as a roster row."""
    return {"n": name, "pos": "WR", "team": "JAX", "slot": "WR", "start": True, "slug": slug_}


def on_cards(mount, size=PHONE, pack="skipped", heads=False, tap_chip=False):
    """The ESPN roster in Cards view, reduced motion. ESPN is a followed team, so this week's pack waits
    in the starters' place (2026-10-05). `pack` "gate" leaves it there, "stage" opens it onto its stage
    with Rip, "skipped" puts the starters face up, so a test reads the cards themselves. `heads` loads
    the headshot files beside the page. The setup presses the Cards chip and Skip or Rip in the page, in
    one round trip (pages/roster_motion.py); `tap_chip` taps all of them for real instead."""
    page, errors = mount("roster", size=size, heads=heads)
    roster = RosterPage(page)
    if tap_chip:
        roster.show_cards("espn")
        assert roster.gates() == 1, "the fixture's schedule has a week ahead, so a pack waits"
        if pack == "stage":
            roster.open_stage()
        elif pack == "skipped":
            roster.skip_pack()
        return roster, errors
    waiting = show_cards(roster, "espn", {"stage": "rip", "skipped": "skip"}.get(pack))
    assert waiting == 1, "the fixture's schedule has a week ahead, so a pack waits"
    if pack == "stage":
        roster.wait_for_stage()
    return roster, errors


@pytest.fixture(scope="module")
def signed_mount(mount, built):
    """`mount` over the same build with an empty LIVE_SIGNED for week 3 (the fixtures log too few teams for
    any week to be complete, so the build writes null): the build writes it as one `const LIVE_SIGNED = ...;`
    line. Its own folder, so its page is its own file."""
    text, n = re.subn(r"^const LIVE_SIGNED = .*;$", 'const LIVE_SIGNED = {"wk": 3, "players": {}};', built.fragment, count=1, flags=re.M)
    assert n == 1
    m = Mounter(mount.browser, mount.folder / "signed", text)
    yield m
    m.pages.close()


@pytest.fixture(scope="module")
def card_js(node_js):
    return node_js("ui/weather.js", "surface/teams/cardweather.js", "surface/teams/cards.js")


# ---- what the build computes ----

@pytest.mark.req(REQ, ac="a rank is within the position over everyone projected; a duplicate keeps his best number")
def test_rank_is_within_the_position_over_everyone_projected():
    players = [{"name": "A One", "pos": "RB", "pts": 20}, {"name": "B Two", "pos": "RB", "pts": 12},
               {"name": "C Three", "pos": "WR", "pts": 15}, {"name": "D Four", "pos": "RB", "pts": None},
               {"name": "B Two", "pos": "RB", "pts": 9}]          # a duplicate keeps his best number
    r = position_ranks(players, slug)
    assert r["a-one"] == (1, 2) and r["b-two"] == (2, 2) and r["c-three"] == (1, 1)
    assert "d-four" not in r


@pytest.mark.req(REQ, ac="a player not playing has no points and no rank, and the rest move up")
def test_a_player_not_playing_has_no_points_no_rank_and_the_rest_move_up():
    from projections import live_projections
    raw = {"players": [{"name": "A One", "pos": "RB", "pts": 20, "src": "model"},
                       {"name": "B Two", "pos": "RB", "pts": 12, "src": "model"},
                       {"name": "C Three", "pos": "RB", "pts": 9, "src": "model"}]}
    status = {"a one": {"name": "A One", "injury": "NA"}, "b two": {"name": "B Two", "injury": "Questionable"}}
    got = live_projections(raw, slug, {"a-one", "b-two", "c-three"}, status)["players"]
    assert got["a-one"]["pts"] is None and got["a-one"]["rank"] is None and got["a-one"]["out"] == "NA"
    assert got["b-two"]["rank"] == 1 and got["b-two"]["pts"] == 12 and got["b-two"]["out"] is None
    assert got["c-three"]["rank"] == 2 and got["c-three"]["of"] == 2


@pytest.mark.req(REQ, ac="the defense's implied points split the game's total by its spread")
def test_implied_points_split_the_total_by_the_spread():
    pool = {"games": {"BAL@DAL": {"odds": {"overUnder": 52.5, "homeSpread": 3.5, "awaySpread": -3.5}},
                      "LA@SF": {"odds": {"overUnder": 44.0, "homeSpread": -2.0, "awaySpread": 2.0}},
                      "X@Y": {"odds": {"overUnder": None}}}}
    t = live_lines(pool, {"LA": "LAR"})["teams"]
    assert t["BAL"] == {"implied": 28.0, "opp": "DAL", "spread": -3.5, "total": 52.5}
    assert t["DAL"]["implied"] == 24.5
    assert t["LAR"]["opp"] == "SF" and t["SF"]["implied"] == 23.0
    assert "X" not in t
    assert live_lines({"games": {}}, {}) is None


@pytest.mark.req(REQ, ac="an autograph is a top-three finish in the last completed week")
def test_an_autograph_is_a_top_three_finish_in_the_last_completed_week():
    from signed import completed_week, live_signed
    games = [{"week": 2, "home": "A", "away": "B"}, {"week": 2, "home": "C", "away": "D"},
             {"week": 3, "home": "A", "away": "C"}, {"week": 3, "home": "B", "away": "D"}]
    rows = [{"name": f"R{i}", "pos": "RB", "week": 2, "team": "ABCD"[i % 4], "pts": 30 - i} for i in range(5)]
    rows += [{"name": "Q1", "pos": "QB", "week": 2, "team": "A", "pts": 25},
             {"name": "R9", "pos": "RB", "week": 3, "team": "A", "pts": 50}]      # Thursday's game alone
    assert completed_week(rows, games) == 2
    got = live_signed({"rows": rows}, {"games": games}, slug, {"r0", "r2", "r3", "q1", "r9"})
    assert got == {"wk": 2, "players": {"r0": {"rank": 1, "pts": 30}, "r2": {"rank": 3, "pts": 28},
                                        "q1": {"rank": 1, "pts": 25}}}
    assert live_signed({"rows": rows}, {"games": []}, slug, {"r0"}) is None


# ---- the card's pure functions, in Node ----

@pytest.mark.req(REQ, ac="#1 is holo, #2-3 gold, #4-6 silver, the rest and the unranked plain stock")
def test_a_tier_is_the_rank_and_the_unranked_have_none(card_js):
    tiers = [card_js("cardTier", rank) for rank in (1, 2, 3, 4, 6, 7, 12, None, 0)]
    assert tiers == ["holo", "gold", "gold", "silver", "silver", "base", "base", "base", "base"]


@pytest.mark.req(REQ, ac="weather shows where it touches a player and nowhere covered; wind skips a runner")
def test_weather_shows_where_it_touches_a_player_and_nowhere_covered(card_js):
    storm = {"roof": "outdoor", "wind": "15 to 20 mph", "precip_pct": 60, "short": "Rain"}
    gust = {"roof": "outdoor", "wind": "22 mph", "precip_pct": 0, "short": "Sunny"}
    snow = {"roof": "outdoor", "wind": "5 mph", "precip_pct": 0, "short": "Light Snow"}
    fair = {"roof": "outdoor", "wind": "3 to 8 mph", "precip_pct": 5, "short": "Sunny"}
    fx = lambda w, pos: card_js("cardWeatherFx", w, pos)
    note = lambda w, pos: card_js("cardWeatherNote", w, pos)
    assert "wind" in fx(storm, "K") and "rain" in fx(storm, "K")
    assert "snow" in fx(snow, "QB") and "wind" not in fx(snow, "QB")
    assert fx(fair, "WR") == "" and fx({**storm, "roof": "dome", "wind": "30 mph", "precip_pct": 90, "short": "Snow"}, "WR") == ""
    assert fx(storm, "TE") != "" and fx({**storm, "roof": "retractable"}, "TE") == ""
    # Wind does not hurt a runner, and rain gives him no "run ↑": 12.53 measured every RB weather cell at about
    # zero or below (rain -0.09, wind -0.21), so a runner's card says nothing about weather (2026-10-06).
    assert fx(gust, "RB") == "" and note(gust, "RB") is None
    assert note(gust, "WR") == {"what": "WIND 22", "kind": "WIND", "effect": "pass ↓"}
    assert note(storm, "RB") is None and note(snow, "RB") is None


# ---- the Sheet / Cards choice ----

@pytest.mark.render
@pytest.mark.req(REQ, ac="every player is a card, K and DST support cards, and the choice survives a reload")
def test_cards_draw_every_player_and_the_choice_survives_a_reload(mount):
    roster, errors = on_cards(mount, tap_chip=True)       # the one setup that taps the chip and Skip, for real
    assert roster.card_count() == roster.roster_size()
    assert roster.support_card_count() == roster.support_size()
    roster.reload()
    assert roster.roster_mode() == "cards"
    assert errors == []


# ---- the card's face ----

@pytest.mark.render
@pytest.mark.req(REQ, ac="a support card has no rank, no holo tint, the same banner and a badge of just K or DST")
def test_a_support_card_has_no_holo_and_a_badge_of_just_k_or_dst(mount):
    roster, errors = on_cards(mount)
    roster.add_support_cards()
    faces = roster.support_faces()
    assert faces["dst"]["holo"] == 0 and faces["dst"]["banner"] == "Bengals"
    assert faces["dst"]["badge"] == "DST" and faces["k"]["badge"] == "K"
    assert faces["k"]["banner"] == "Little"
    assert roster.stages() == 0 and errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="the border is the metal and the badge ring follows; only the #1 tints the photo")
def test_the_border_is_the_metal_and_the_badge_ring_follows(mount):
    roster, errors = on_cards(mount)
    looks = [roster.metal_look(roster.add_card(wr(f"T Metal{i}", f"test-metal-{i}"), rank)) for i, rank in enumerate((1, 2, 5, 9))]
    assert [g["tier"] for g in looks] == ["tier-holo", "tier-gold", "tier-silver", "tier-base"]
    assert [g["background"] for g in looks] == ["conic-gradient", "linear-gradient", "linear-gradient", "none"]   # base is the plain stock colour
    assert [g["holo"] for g in looks] == [True, False, False, False]                                            # only #1 tints the photo
    assert [g["badge"] for g in looks] == ["WR1", "WR2", "WR5", "WR9"]
    assert len({g["ring"] for g in looks}) == 4, "each tier has its own ring"
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a long last name ends before the badge, a Jr. dropped, never under 10px")
def test_a_long_last_name_ends_before_the_badge(mount):
    roster, errors = on_cards(mount)
    names = ("Dalton Montgomery", "Amon-Ra St. Brown", "Michael Pittman Jr.", "Jaxon Smith-Njigba")
    fits = [roster.name_fit(roster.add_card(wr(name, f"test-long-{n}"), 20 + n)) for n, name in enumerate(names)]
    assert [g["name"] for g in fits] == ["Montgomery", "St. Brown", "Pittman", "Smith-Njigba"]      # a last name, a Jr. dropped
    assert all(g["clear_of_badge"] and g["font"] >= 10 for g in fits), fits
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="every card back fits its card on a 360px phone, the signed row and the matchup line included")
def test_every_card_back_fits_its_card_on_a_small_phone(signed_mount):
    # A 360px screen: the support backs lost their values to a squeezed row, then overflowed; the
    # matchup line and a signed card's row (2026-10-05) must not do it again.
    roster, errors = on_cards(signed_mount)
    roster.add_support_and_signed_cards()
    assert roster.backs_overflowing() == []
    assert roster.signed_backs() >= 1, "a signed back was measured"
    assert roster.defense_abbr() == "CIN", "the defense's face is its club code"
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="the back leads with rank and game, a signed card says why, and the front no longer names the game")
def test_the_back_leads_with_the_game_and_a_signed_card_says_why(signed_mount):
    roster, errors = on_cards(signed_mount)
    got = roster.back_facts({"n": "Test Back", "pos": "TE", "team": "JAX", "slot": "TE", "start": True, "slug": "test-back-te"},
                            2, {"rank": 2, "pts": 22.6})
    assert got["first"].startswith("#2 TE") and got["matchup"] in got["first"], "rank, then the game, on the first line"
    assert got["signed"] == f"Signed for week {roster.signed_week()}: #2 TE, 22.6 pts"
    assert got["matchup"] not in got["front"], "the front no longer says the game"
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="with no week complete nobody is signed, not even the #1 (it was every #1-5 until 2026-09-25)")
def test_nobody_is_signed_when_no_week_is_complete(mount):
    # The fixtures log too few teams for any week to be complete, so the build writes no signed block.
    roster, errors = on_cards(mount)
    assert roster.signed_block_is_null()
    assert roster.autograph_count() == 0
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="only a signed player has the autograph, whatever his tier")
def test_only_a_signed_player_has_the_autograph_whatever_his_tier(signed_mount):
    roster, errors = on_cards(signed_mount)
    assert roster.autograph_count() == 0, "a signed week nobody earned draws none"
    got = roster.autographs_of_two_skill_players()
    assert got is not None, "the fixture's ESPN roster has two skill players"
    assert got == [1, 0]
    assert errors == []


SIGNED = wr("Christian Kirk-Johnson Jr.", "test-signed-long")


@pytest.mark.render
@pytest.mark.req(REQ, ac="a signed card keeps only the golden name and it fits a 360 card; its words are on the back once")
def test_a_signed_card_keeps_only_the_golden_name_and_it_fits_a_360_card(signed_mount):
    """2026-10-05: the face keeps the signature alone, in a structure the pack's motion relies on, and a
    long name shrinks (fitSig, never under 12px) until it is inside the card."""
    roster, errors = on_cards(signed_mount)
    roster.sign("test-signed-long", 2, 22.6)
    a = roster.autograph(roster.add_card(SIGNED, 3))
    assert a["count"] == 1 and a["shaped"], "the pen's ink and nib sit beside the finished gold"
    # The name is the full one, or the last name alone when the full one cannot fit even at 12px.
    assert a["cool"] == a["hot"] and a["hot"] in ("Christian Kirk-Johnson Jr.", "Kirk-Johnson")
    # Static: the finished gold shows, the pen's hot ink and nib are hidden.
    assert a["opacity"] == ("1", "0", "0")
    # It fits: inside the card whole, its font stepped down from the 24px start, never under 12px.
    assert a["inside"] and a["fits"], a
    assert 12 <= a["font"] <= 24, a
    # Its words are on the back, once, and in the tooltip.
    assert a["back"] == "Signed for week 3: #2 WR, 22.6 pts"
    assert "week 3" in a["title"]
    assert roster.fronts_with_at_most_one_autograph()
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="an OUT card greys the photo and reddens the number, with no red bar across the foot")
def test_an_out_card_greys_the_photo_and_reddens_the_number_with_no_red_bar(mount):
    roster, errors = on_cards(mount)
    roster.plant_out_player("test-out-rb")
    out = roster.out_card(roster.add_card({"n": "Out Player", "pos": "RB", "team": "JAX", "slot": "RB", "start": True, "slug": "test-out-rb"}))
    assert out["bar"] == 0, "no red bar across the foot"
    assert out["num"] == "OUT"
    assert out["num_color"] == out["down"]
    assert out["photo_filter"].startswith("grayscale")
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="no chip covers the projection, the badge or the banner at 360px")
def test_no_chip_ever_covers_the_projection_the_badge_or_the_banner(mount):
    """The weather chip and the Q and D chips sit on their own row under the projection chip (360px)."""
    roster, errors = on_cards(mount)
    roster.plant_chip_scene()
    added = [roster.add_card(wr(name, slug_), 4) for slug_, name in (("test-q-wr", "Q Player"), ("test-d-wr", "D Player"))]
    rows = roster.chip_layout(added)
    assert [r["n"] for r in rows] == [2, 2], "each shows its weather and its Q or D"
    assert not any(r["clash"] for r in rows) and all(r["inside"] for r in rows), rows
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="the border shines once when asked and never on its own; none under reduced motion")
def test_the_border_shines_once_when_asked_and_never_on_its_own(mount):
    roster, errors = on_cards(mount)
    with roster.motion_allowed():
        assert roster.border_animation()[0] == "none", "no idle loop"
        roster.shine_first_card(True)
        assert roster.border_animation() == ["tc-sweep", "1"]
        # The shine is the border's: the layer is cut out of the face.
        mask = roster.border_mask()
        assert "exclude" in mask or "xor" in mask, mask
        roster.reduced_motion()
        assert roster.border_animation()[0] == "none", "reduced motion: none"
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="an IR spot is a bench spot, never a starter")
def test_an_ir_spot_is_not_in_the_starting_lineup(mount):
    roster, errors = on_cards(mount)
    rows = [{"n": "A", "pos": "RB", "team": "X", "slug": "a", "slot": "IR"}, {"n": "B", "pos": "RB", "team": "X", "slug": "b", "slot": "RB"}]
    assert roster.espn_row_starts(rows) == [False, True]
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a starter who will sit is named in a red pill in the week row and marked in the roster; Q is only a chip")
def test_a_starter_who_will_sit_is_named_in_the_week_row_and_marked_in_the_roster(mount):
    roster, errors = on_cards(mount)
    roster.plant_one_out_one_questionable()
    roster.press_escape()
    # 2026-10-05: a red pill in the "This week" row, not a strip above the roster; the reason is its tooltip.
    pill = roster.sit_pill()
    assert pill["count"] == 1 and pill["text"].endswith(" out") and "Knee" in pill["title"]
    assert roster.sit_strips() == 0
    alert = roster.alert_cards()
    assert alert["count"] == 1 and alert["bars"] == 0, "OUT is a grey photo and a red number, never a bar across the foot"
    # Questionable is only a chip, never the warning.
    q = roster.questionable_cards()
    assert q["chips"] <= 1 and q["alerts"] == 0
    roster.mode("sheet")
    assert roster.sit_pill()["count"] == 1 and roster.alert_rows() == 1
    assert errors == []


# ---- the back ----

@pytest.mark.render
@pytest.mark.req(REQ, ac="a tap flips the card and its back opens the profile")
def test_a_tap_flips_the_card_and_its_back_opens_the_profile(mount):
    roster, errors = on_cards(mount)
    roster.flip()
    assert roster.flipped()
    roster.open_profile_from_back()
    assert roster.profile_open()
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a card back is three usage stats with percentile bars, from his latest game")
def test_a_card_back_is_a_role_sheet_from_his_latest_game(mount):
    roster, errors = on_cards(mount)
    got = roster.role_sheet_back()
    assert got is not None, "the fixture's usage grid has a rostered skill player"
    assert got["stats"] == 3 and all(b != "" for b in got["bars"])
    assert got["week"] and got["spark"] == 0
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a card takes the 256px head where there is one, else the 96px")
def test_a_card_takes_the_256px_head_where_there_is_one(mount):
    roster, errors = on_cards(mount)
    assert roster.head_sources() == ["heads/lg/a-sharp-one.webp", "heads/a-soft-one.webp"]
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="the photo is full bleed and its foot is under the banner")
def test_the_photo_is_full_bleed_and_stands_on_the_banner(mount):
    """2026-10-05: the art is the whole face; the head fills its height above the banner and stands
    on the banner's edge (its foot is under the banner, never in the gap above it). It needs the headshot
    files beside the page, so it mounts with `heads=True`."""
    roster, errors = on_cards(mount, heads=True)
    g = roster.photo_geometry()
    assert g["has_photo"], "the fixture build has a headshot file"
    face, art, ban, box = g["face"], g["art"], g["banner"], g["photo"]
    assert art["width"] == face["width"] and art["height"] == face["height"], "the art fills the face"
    assert box["height"] > face["height"] * 0.6
    foot = box["y"] + box["height"]
    assert ban["y"] < foot <= face["y"] + face["height"] + 1, "the head's foot is under the banner"
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="on a desktop the starters are three by three with the bench beside them")
def test_on_a_desktop_the_starters_are_three_by_three_with_the_bench_beside(mount):
    roster, errors = on_cards(mount, size=(1400, 900))
    assert roster.grid_columns()[0] == 3
    starters, bench = roster.starters_box(), roster.bench_box()
    assert bench["x"] > starters["x"] + starters["width"] - 1 and abs(bench["y"] - starters["y"]) < 2
    assert errors == []


