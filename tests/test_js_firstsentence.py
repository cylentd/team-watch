"""The waiver card's lede is the summary's first sentence, and the back shows the rest (2026-10-07: the back
repeated the lede, which made it taller than the front and left a hole there). `wvFirstSentence`
(data/firstsentence.js) cuts at the first sentence end followed by a capital. A period after a short word
("vs.", "St.") or inside a number ("2.6") is not an end; one after a unit ("pts/wk.") is."""
import pytest


@pytest.fixture(scope="module")
def fs(node_js):
    return node_js("data/firstsentence.js")


def test_a_period_after_a_unit_ends_the_sentence(fs):
    text = "Mayer upgrades your bench over D. Schultz by 2.6 pts/wk. He also fills a TE need in Yahoo."
    assert fs("wvFirstSentence", text) == "Mayer upgrades your bench over D. Schultz by 2.6 pts/wk."


def test_a_two_sentence_summary_keeps_the_first(fs):
    text = "Wilson took 21 carries in week 2. He starts over Chase Brown in both leagues."
    assert fs("wvFirstSentence", text) == "Wilson took 21 carries in week 2."


def test_one_sentence_is_the_whole_text(fs):
    text = "Ford projects 11.9 against Chase Brown's 9.7 at FLEX."
    assert fs("wvFirstSentence", text) == text


def test_vs_is_not_a_sentence_end(fs):
    text = "He sees the Bengals vs. Cleveland on Sunday. The line moved."
    assert fs("wvFirstSentence", text) == "He sees the Bengals vs. Cleveland on Sunday."


def test_a_decimal_is_not_a_sentence_end(fs):
    text = "He gains 2.6 points a week. Claim him."
    assert fs("wvFirstSentence", text) == "He gains 2.6 points a week."


def test_no_text_is_empty(fs):
    assert fs("wvFirstSentence", None) == ""
