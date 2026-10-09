"""Home's hero headline as split-flap letters, in Node (David 2026-10-08, ledger #73: "on hover the headline doesnt
flip like a scoreboard like the previous animation"): data/hero.js dgFlapChars puts each letter of the already
word-split headline in a tile of its own, counted across the whole headline, as b0284898's ghost letters were. Where
the letters turn is tests/test_hero_desk.py."""
import re

import pytest


@pytest.fixture(scope="module")
def js(node_js):
    return node_js("data/hero.js")


def letters_of(html):
    return re.findall(r'<i class="dg-hc" style="--c:(\d+)">(.*?)</i>', html)


@pytest.mark.req("Home", ac="each letter of the hero's headline is one tile, counted left to right across its words")
def test_each_letter_is_one_tile_counting_across_words(js):
    got = letters_of(js("dgFlapChars", js("dgFlapWords", "Go up")))
    assert got == [("0", "G"), ("1", "o"), ("2", "u"), ("3", "p")]


def test_the_letters_sit_inside_their_word_and_emphasis(js):
    html = js("dgFlapChars", 'A <em class="dg-em go">2</em>')
    assert html == ('<i class="dg-hc" style="--c:0">A</i> <em class="dg-em go"><i class="dg-hc" style="--c:1">2</i></em>')


def test_an_entity_is_one_letter(js):
    assert letters_of(js("dgFlapChars", "A&amp;M")) == [("0", "A"), ("1", "&amp;"), ("2", "M")]


@pytest.mark.parametrize("head", ["Irving piles up", 'x <em class="dg-em">y z</em>.', "  ", ""])
def test_the_headline_reads_exactly_as_before(js, head):
    strip = lambda s: re.sub(r"<[^>]+>", "", s)
    assert strip(js("dgFlapChars", js("dgFlapWords", head))) == strip(head)
