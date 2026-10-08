"""Player tags on the page (2026-10-08, ledger #41), in Node: which tags a player has, in what order, and the one plain
line each says. data/tags.js decides; ui/tags.js only draws (tests/test_tags_view.py proves the screen).

The block is LIVE_PLAYER_TAGS as design/player_tags.py cuts it (tests/test_player_tags.py): Rising, Sleeper (ff-jarvis's
POTENTIAL) and Trending; LUCKY and SLEEPER never reach it. Words come from content.json through `words`, never typed here.
"""
import pytest

from wording import words


def say(key, **kw):
    """The page's text for `key` with its {name} slots filled, as t() fills them."""
    text = words(key)
    for k, v in kw.items():
        text = text.replace("{" + k + "}", str(v))
    return text


BLOCK = {
    "season": 2026, "week": 3, "through": 2, "last_n": 3, "hours": 24, "effect": 1.17,
    "effect_signals": ["ROOKIE_RAMP", "ROUTES_FIRST", "EFFICIENT_PARTTIMER"], "alias": {"LA": "LAR"},
    "players": {
        "breece-hall": [{"tag": "TRENDING", "kind": "fact", "nums": {"rank": 9, "adds": 236169}},
                        {"tag": "RISING", "kind": "fact", "nums": {"last": 16.6, "earlier": 10.0, "delta": 6.6}},
                        {"tag": "POTENTIAL", "kind": "fact", "nums": {"signal": "VACATED", "games_out": 2}}],
        "chase-brown": [{"tag": "POTENTIAL", "kind": "fact", "nums": {"signal": "VACATED", "tgt_share": 0.231}},
                        {"tag": "POTENTIAL", "kind": "fact", "nums": {"signal": "ROUTES_FIRST", "route_pct": 0.71}}],
        "rookie-guy": [{"tag": "POTENTIAL", "kind": "fact", "nums": {"signal": "ROOKIE_RAMP", "delta": 0.38}}],
        "vac-only": [{"tag": "POTENTIAL", "kind": "fact", "nums": {"signal": "VACATED", "games_out": 2}}],
        "part-timer": [{"tag": "POTENTIAL", "kind": "fact", "nums": {"signal": "EFFICIENT_PARTTIMER", "yprr": 2.4}}],
        "george-kittle-sf": [{"tag": "RISING", "kind": "tested", "nums": {"last": 12.3, "earlier": 8.7, "delta": 3.6}}],
        "george-kittle-buf": [{"tag": "TRENDING", "kind": "fact", "nums": {"rank": 2, "adds": 602775}}],
        "puka-nacua-la": [{"tag": "RISING", "kind": "fact", "nums": {"last": 20.0, "earlier": 15.0, "delta": 5.0}}],
        "odd-kind": [{"tag": "TRENDING", "kind": "tested", "nums": {"rank": 3, "adds": 1000}}],
    },
}


@pytest.fixture(scope="module")
def tg(node_js):
    return node_js("data/tags.js")


def tags(tg, slug, team="NYJ", block=BLOCK):
    return [x["tag"] for x in tg("tagsFor", block, {"slug": slug, "team": team})]


def test_a_players_tags_come_rising_then_sleeper_then_trending_whatever_the_files_order(tg):
    assert tags(tg, "breece-hall") == ["RISING", "POTENTIAL", "TRENDING"]


def test_potentials_signals_merge_into_one_tag_in_the_files_order(tg):
    got = tg("tagsFor", BLOCK, {"slug": "chase-brown", "team": "CIN"})
    assert got == [{"tag": "POTENTIAL", "kind": "fact", "signals": ["VACATED", "ROUTES_FIRST"]}]


@pytest.mark.parametrize("team,want", [("SF", ["RISING"]), ("BUF", ["TRENDING"]), ("KC", [])])
def test_two_players_who_share_a_name_are_found_by_team_and_never_merged(tg, team, want):
    assert tags(tg, "george-kittle", team) == want


def test_a_shared_name_is_found_in_the_files_team_spelling_too(tg):
    """ff-jarvis keys with nflverse's code (LA); the page spells it LAR."""
    assert tags(tg, "puka-nacua", "LAR") == ["RISING"]


@pytest.mark.parametrize("block,slug", [(None, "breece-hall"), (BLOCK, "nobody"), (BLOCK, None)])
def test_no_block_no_entry_or_no_slug_means_no_tags(tg, block, slug):
    assert tg("tagsFor", block, {"slug": slug, "team": "NYJ"}) == []
    assert tg("tagRowView", block, {"slug": slug, "team": "NYJ"}) is None


def view(tg, slug, team="NYJ"):
    return tg("tagRowView", BLOCK, {"slug": slug, "team": team})


def test_the_row_shows_the_first_tag_with_its_label_and_class(tg):
    v = view(tg, "breece-hall")
    assert (v["tag"], v["label"], v["cls"]) == ("RISING", words("tags.label.rising"), "rising")


def test_rising_as_a_fact_says_the_games_counted_and_both_numbers(tg):
    assert view(tg, "breece-hall")["lines"] == [say("tags.rising.fact", n=3, last="16.6", earlier="10.0")]


def test_rising_tested_adds_what_the_test_found_to_its_line(tg):
    assert view(tg, "george-kittle", "SF")["lines"] == [say("tags.rising.tested", n=3, last="12.3", earlier="8.7")]


def test_trending_names_its_place_hours_and_adds_with_separators(tg):
    v = view(tg, "george-kittle", "BUF")
    assert v["label"] == words("tags.label.trending") and v["cls"] == "trending"
    assert v["lines"] == [say("tags.trending.fact", rank=2, hours=24, adds="602,775")]


def test_a_tested_kind_with_no_tested_words_reads_as_a_fact(tg):
    assert view(tg, "odd-kind")["lines"] == [say("tags.trending.fact", rank=3, hours=24, adds="1,000")]


def test_no_view_carries_a_kind_word(tg):
    """David, 2026-10-08 ("show not tell"): no Fact or Tested word; the line says it."""
    assert set(view(tg, "george-kittle", "SF")) == {"tag", "cls", "label", "lines", "tip"}


def test_potential_is_named_sleeper_and_says_one_line_per_signal(tg):
    v = view(tg, "vac-only")
    assert (v["tag"], v["label"], v["cls"]) == ("POTENTIAL", words("tags.label.sleeper"), "sleeper")
    assert v["lines"] == [words("tags.sleeper.vacated")]


@pytest.mark.parametrize("slug,key", [("rookie-guy", "tags.sleeper.rookieRamp"), ("part-timer", "tags.sleeper.partTimer")])
def test_an_effect_signal_carries_the_effect_line(tg, slug, key):
    assert view(tg, slug)["lines"] == [words(key), say("tags.sleeper.effect", pts="1.17")]


def test_vacated_never_carries_the_effect_and_the_effect_follows_its_own_signal(tg):
    """VACATED was dropped from 12.118 before the score: the effect line sits after the routes signal and before VACATED."""
    assert view(tg, "chase-brown", "CIN")["lines"] == [
        words("tags.sleeper.routesFirst"), say("tags.sleeper.effect", pts="1.17"), words("tags.sleeper.vacated")]


def test_no_effect_in_the_file_means_no_effect_line(tg):
    bare = {**BLOCK, "effect": None, "effect_signals": []}
    assert tg("tagRowView", bare, {"slug": "rookie-guy", "team": "NYJ"})["lines"] == [words("tags.sleeper.rookieRamp")]


def test_the_tip_is_every_line_in_one_string(tg):
    v = view(tg, "chase-brown", "CIN")
    assert v["tip"] == " ".join(v["lines"])


def test_watchs_verdict_gives_way_only_when_the_same_tag_fires(tg):
    assert tg("tagCovers", BLOCK, {"slug": "breece-hall", "team": "NYJ"}, "RISING") is True
    assert tg("tagCovers", BLOCK, {"slug": "breece-hall", "team": "NYJ"}, "SELL HIGH") is False
    assert tg("tagCovers", BLOCK, {"slug": "chase-brown", "team": "CIN"}, "RISING") is False
    assert tg("tagCovers", None, {"slug": "breece-hall", "team": "NYJ"}, "RISING") is False
