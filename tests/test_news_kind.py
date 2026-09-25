"""design/news.py news_kind: what a story means for a lineup, from its own words.
Every case here is a real 2026-09-16 FantasyPros headline."""
import pytest

from news import news_kind, news_player


@pytest.mark.parametrize("title, kind", [
    ("Audric Estime (thigh) placed on injured reserve", "out"),
    ("De'Zhaun Stribling (ankle) set to miss around 10 weeks", "out"),
    ("Sam Darnold (glute) ruled out for Sunday", "out"),
    ("Malik Hooker (arm) suffers fractured forearm, out several weeks", "out"),
    ("Nico Collins (hamstring) limited at practice Wednesday", "injury"),   # a hamstring is caution
    ("Troy Fautanu (ankle) misses practice Wednesday", "injury"),
    ("Malik Nabers (knee) game-time decision for Week 1", "injury"),
    ("Aaron Banks (knee) officially limited Wednesday", "practice"),       # limited is routine
    ("Christian McCaffrey (rest) doesn't practice Wednesday", "practice"),  # a rest day is not an injury
    ("Keaton Mitchell (hamstring) without injury designation for Week 2", "practice"),
    ("Jalen Coker (ankle) in walking boot, not expected to miss time this week", "practice"),
    ("DeeJay Dallas signs with Vikings' active roster", "move"),
    ("Michael Penix Jr. (knee) could start in week or two for Falcons", "news"),
])
def test_real_headlines(title, kind):
    assert news_kind({"title": title}) == kind


def test_the_desc_decides_only_when_the_title_says_nothing():
    assert news_kind({"title": "Report: minor roster move for Detroit", "desc": "He was placed on IR."}) == "out"


@pytest.mark.parametrize("title, name, slug", [
    ("Cooper Kupp (back) practices fully Thursday ", "Cooper Kupp", "cooper-kupp"),
    ("Marvin Mims Jr. (foot) limited again Thursday", "Marvin Mims Jr.", "marvin-mims"),
    ("Amon-Ra St. Brown (ankle) limited Wednesday", "Amon-Ra St. Brown", "amonra-st-brown"),
    ("Brian O'Neill (knee) upgraded to full participant Thursday", "Brian O'Neill", "brian-oneill"),
])
def test_the_player_is_the_name_before_the_injury_tag(title, name, slug):
    got_name, slugs = news_player(title)
    assert got_name == name
    assert slugs[0] == slug   # the whole name, when it is all there is before the tag


def test_a_title_without_a_tag_names_no_player_but_still_offers_slugs():
    name, slugs = news_player("Ronnie Rivers placed on IR")
    assert name is None
    assert "ronnie-rivers" in slugs   # the page draws a head only if HEADS has one


def test_an_empty_title_offers_nothing():
    assert news_player(None) == (None, [])


def test_every_built_item_carries_a_kind(built):
    import re, json
    m = re.search(r"^const LIVE_NEWS = (.*);$", built.fragment, re.M)
    items = json.loads(m.group(1).replace("<\\/", "</"))["items"]
    assert {it["kind"] for it in items} >= {"out", "injury"}
