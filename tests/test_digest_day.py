"""This week > Digest by day (2026-10-06, storyboard "Digest by Day", option B; STYLE.md "Answer first").

Component tests on `mount("digest")` (`DigestDayPage`): the 128px banner each weekday and its subject, a
card's rows and their research one tap away, the fallback to Need to know, and "Rest of the week". Which
day picks which plan, and each banner's pick, are Node tests in tests/test_js_digest.py. The card bodies
are stubs until they are built, so the row component is proven on a planted card.
"""
import json
import pathlib

import pytest

from component import mount  # noqa: E402,F401  (the fixture)
from pages.digest_day import DigestDayPage
from test_render import open_at

pytestmark = pytest.mark.render

PHONE = (360, 800)
COPY = json.loads((pathlib.Path(__file__).resolve().parent.parent / "design" / "src" / "content.json").read_text(encoding="utf-8"))

# Noon Pacific of week 5's days; the fixture packet's own clock does not matter to the banner's frame.
NOON = {"tue": "2026-10-06T19:00:00Z", "wed": "2026-10-07T19:00:00Z", "thu": "2026-10-08T19:00:00Z",
        "fri": "2026-10-09T19:00:00Z", "sat": "2026-10-10T19:00:00Z", "sun": "2026-10-04T19:00:00Z",
        "mon": "2026-10-05T19:00:00Z"}
LABEL = {"tue": "TUE · WAIVER DAY", "wed": "WED · USAGE DAY", "thu": "THU · GAME NIGHT", "fri": "FRI · PRACTICE REPORT",
         "sat": "SAT · LINEUP DAY", "sun": "SUN · GAME DAY", "mon": "MON · GAME NIGHT"}
# The recap fixture is week 4, 8 of 16 games final, its last kickoff Monday 2026-10-05 5:15 PM Pacific.
RECAP_ON, RECAP_LAST_DAY = "2026-10-05T15:00:00Z", "2026-10-07T12:00:00Z"


def day(mount, size=PHONE):
    page, errors = mount("digest", size=size)
    return DigestDayPage(page), errors


@pytest.mark.req("Digest", ac="the banner is 128px at 360px every day, under the day's label")
def test_the_banner_is_128px_at_360_every_day(mount):
    dg, errors = day(mount)
    for key, at in NOON.items():
        dg.at(at)
        got = dg.banner()
        assert (got["day"], got["h"], got["day_attr"]) == (LABEL[key], 128, key), (key, got)
        assert dg.fits(), key
    assert dg.retired_rows() == 0
    assert errors == []


@pytest.mark.req("Digest", ac="Tuesday's banner is the top add and its number")
def test_tuesdays_banner_is_the_top_add(mount):
    dg, errors = day(mount)
    dg.plant_sleeper_adds(NOON["tue"])
    assert dg.headline() == "O. Gordon is the top waiver add"
    assert dg.lead_fact() == "4.0M Sleeper adds in 24 hours."
    assert dg.lead_buttons()["slug"] == 1          # the band opens his profile
    assert errors == []


def mover(**over):
    """A LIVE_USAGE_MOVERS row as ff-jarvis writes it, with Claude's whole line."""
    return {"slug": "tetairoa-mcmillan", "name": "Tetairoa McMillan", "pos": "WR", "team": "CAR", "metric": "tgt_pct", "was": 24,
            "now": 41, "change": 17, "spark": [24, 30, 41], "targets": 9, "carries": None, "teammate": None,
            "line": "Tetairoa McMillan got 41% of Carolina's targets in week 4, up from 24% in week 3.", **over}


@pytest.mark.req("Digest", ac="Wednesday's banner is the top usage mover in a short head built from his numbers")
def test_wednesdays_banner_is_the_top_usage_mover_in_a_short_head(mount):
    dg, errors = day(mount)
    dg.plant_usage_movers(NOON["wed"], [mover()])
    assert dg.headline() == "T. McMillan got 41% of his team's targets"
    assert dg.lead_fact() == "The week's biggest role change."
    assert dg.banner_marks()["head"] == COPY["digest.card.usage.mark"], "a change in usage is untested, and the banner says so"
    assert dg.lead_label() == "Open Tetairoa McMillan’s profile", "the profile button names him"
    dg.plant_usage_movers(NOON["wed"], [mover(slug="bijan-robinson", name="Bijan Robinson", metric="snap", now=78)])
    assert dg.headline() == "B. Robinson's snap share hit 78%"
    assert errors == []


@pytest.mark.req("Digest", ac="with no usage mover Wednesday's banner is the Defenses card's top row, never a news line")
def test_wednesdays_banner_without_usage_movers_is_the_softest_defense(mount):
    dg, errors = day(mount)
    dg.plant_usage_movers(NOON["wed"], [])
    assert dg.headline() == "The NY Jets defense gives up the most points to QBs"
    assert dg.lead_fact() == "21.4 a game, the most of 28 teams."
    assert dg.banner_marks()["head"] == COPY["digest.card.defenses.foot"]
    assert dg.banner()["h"] == 128 and dg.fits()
    assert errors == []


@pytest.mark.req("Digest", ac="Thursday's banner is the game's take with the two codes and Claude's untested pick")
def test_thursdays_banner_is_the_games_take(mount):
    dg, errors = day(mount)
    dg.plant_tnf(NOON["thu"])
    assert dg.headline() == "Dallas wins, but Tampa's rookie keeps it close"
    assert dg.lead_fact().endswith("Claude: DAL 28–21")
    assert dg.banner()["side"] == "vs" and dg.banner_vs() == ["TB", "at", "DAL"]
    assert dg.banner_marks()["fact"] == "Untested: Claude's call, not backtested."
    assert dg.banner()["h"] == 128
    assert errors == []


@pytest.mark.req("Digest", ac="Friday's banner is the hurt player with the highest healthy projection, named by initials")
def test_fridays_banner_is_the_hurt_player_with_the_highest_projection(mount):
    dg, errors = day(mount)
    dg.at("2026-09-18T19:00:00Z")                      # a Friday inside the fixture packet's week
    dg.plant_hurt_across_positions()
    assert dg.headline() == "W. Wr is doubtful", "the WR2 outprojects the QB the packet lists first, and the head is initials"
    assert dg.lead_label() == "Open Walt Wr’s profile"
    assert errors == []


@pytest.mark.req("Digest", ac="Saturday's banner is a SMASH and says it is untested")
def test_saturdays_banner_is_a_smash_with_its_mark(mount):
    dg, errors = day(mount)
    dg.at(NOON["sat"])
    assert dg.banner_marks()["head"].startswith("Untested (12.75)")
    assert dg.lead_buttons()["slug"] == 1
    assert errors == []


@pytest.mark.req("Digest", ac="Sunday's banner is the first kickoff, Monday's tonight's game, each with its two codes")
def test_sunday_is_the_first_kickoff_and_monday_tonights_game(mount):
    dg, errors = day(mount)
    dg.plant_schedule("2026-10-04T12:00:00Z", [{"away": "PHI", "home": "JAX", "kickoff": "2026-10-04T13:30:00Z"},
                                               {"away": "NYJ", "home": "DAL", "kickoff": "2026-10-04T17:00:00Z"}])
    assert dg.headline().startswith("First kickoff ") and dg.lead_fact() == "PHI @ JAX."
    assert dg.banner_vs() == ["PHI", "at", "JAX"]
    dg.plant_schedule(NOON["mon"], [{"away": "BUF", "home": "LA", "kickoff": "2026-10-06T00:15:00Z"}])
    assert dg.headline() == "BUF @ LA tonight" and dg.lead_fact().startswith("Kickoff ")
    assert dg.banner_vs() == ["BUF", "at", "LA"]
    assert errors == []


@pytest.mark.req("Digest", ac="a day whose cards are all empty still shows the banner and Need to know")
def test_a_day_whose_cards_are_empty_shows_need_to_know(mount):
    dg, errors = day(mount)
    dg.at("2026-09-15T19:00:00Z")                      # a Tuesday: Top adds and Out, who gains
    assert dg.card_ids() == ["adds", "gains"] and dg.need_count() == 0, "the fixtures feed both cards"
    dg.plant_empty("adds", "gains")
    assert dg.card_ids() == [] and dg.need_count() == 1
    assert dg.banner()["h"] == 128
    assert errors == []


@pytest.mark.req("Digest", ac="a row shows its answer and opens its research in place, one at a time, by tap or key")
def test_a_rows_research_opens_in_place_one_at_a_time(mount):
    dg, errors = day(mount)
    dg.at("2026-09-15T19:00:00Z")
    dg.plant_empty("gains")                            # Tuesday's other card: the rows below are the planted card's alone
    dg.plant_card()
    assert dg.card_ids() == ["adds"] and dg.need_count() == 0, "a card that drew takes Need to know's place"
    assert dg.card_title() == "Top adds" and dg.card_more() == {"leaf": "waivers", "text": "Waivers"}
    rows = dg.rows()
    assert [(r["name"], r["answer"]) for r in rows] == [(dg.first_hurt_name(), "23% +16 targets"), ("Trey McBride", "SMASH TE1"),
                                                        ("Detroit", "OUT")]
    assert rows[1]["mark"].startswith("Untested (12.75)") and rows[2]["mark"] is None
    assert [r["expanded"] for r in rows] == ["false", "false", None] and rows[2]["tag"] == "DIV"
    assert dg.research_open() == [False, False]
    dg.tap_row(0)
    assert dg.research_open() == [True, False]
    assert "48% → 78%" in dg.research_text(0) and "Untested" in dg.research_text(0)
    dg.tap_row(1)
    assert dg.research_open() == [False, True], "one open at a time"
    dg.tap_row(1)
    assert dg.research_open() == [False, False], "a second tap closes it"
    dg.key_row(0, "Enter")
    assert dg.research_open() == [True, False]
    assert dg.fits()
    dg.tap_research_profile(0)
    assert dg.profile_open()
    dg.close_profile()
    assert errors == []


@pytest.mark.req("Digest", ac="Rest of the week links the views that are not today's job, Recap while its week is fresh")
def test_rest_of_the_week_links_the_other_views(mount):
    dg, errors = day(mount)
    dg.plant_recap(RECAP_ON)                          # Monday, the recap half final
    assert dg.strip() == [["weekrecap", "Recap"], ["waivers", "Waivers"]]
    dg.plant_recap(RECAP_LAST_DAY)                    # Wednesday, its last day
    assert [leaf for leaf, _ in dg.strip()] == ["waivers", "preview", "matchups", "weekrecap"]
    dg.plant_recap(RECAP_ON, "LIVE_RECAP.n_final = 7")        # under half final: no Recap chip
    assert [leaf for leaf, _ in dg.strip()] == ["waivers"]
    dg.plant_recap(RECAP_ON, "LIVE_RECAP.n_final = 8")        # exactly half
    assert [leaf for leaf, _ in dg.strip()] == ["weekrecap", "waivers"]
    dg.plant_recap(RECAP_ON, "LIVE_RECAP.n_games = 0")
    assert [leaf for leaf, _ in dg.strip()] == ["waivers"]
    assert errors == []


@pytest.mark.journey
@pytest.mark.req("Digest", ac="a strip chip opens its view")
def test_the_recap_chip_opens_the_recap_view(browser, page_file):
    ctx, page, errors = open_at(browser, page_file, PHONE, "#digest")
    try:
        dg = DigestDayPage(page)
        dg.plant_recap(RECAP_ON)
        dg.tap_chip("weekrecap")
        assert dg.hash() == "#weekrecap"
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.req("Digest", ac="a wide screen lays the cards side by side under a full-width banner")
def test_a_wide_screen_fits(mount):
    dg, errors = day(mount, size=(1400, 900))
    dg.at("2026-09-15T19:00:00Z")
    dg.plant_card()
    assert dg.fits() and dg.banner()["h"] == 128
    assert errors == []
