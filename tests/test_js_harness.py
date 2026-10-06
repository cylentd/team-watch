"""The JS unit layer itself (tests/jsunit.py): files share one scope in order, as on the page;
COPY and esc() are there; a throw or a missing dependency fails loudly."""
import pytest

from jsunit import JSError


@pytest.fixture(scope="module")
def js(node_js):
    return node_js("data/startsit.js", globals={"PLANTED": {"a": [1, 2]}})


def test_a_files_top_level_const_is_visible_to_the_next(js):
    assert js("typeof ss3Wl") == "function"       # data/startsit.js
    assert js("typeof esc") == "function"         # lib/escape.js, always loaded


def test_t_reads_the_real_copy_and_esc_escapes(js):
    assert js("t", "matchups.vs.home", {"team": "DAL", "opp": "BAL"}) == "DAL vs BAL"
    assert js("esc", "<b>") == "&lt;b&gt;"


def test_globals_arrive_as_the_sandboxs_own_values(js):
    assert js("Array.isArray(PLANTED.a) && PLANTED.a instanceof Array") is True


def test_a_throw_fails_with_the_js_message(js):
    with pytest.raises(JSError, match="copy: no.such.key"):
        js("t", "no.such.key")


def test_a_dependency_the_list_lacks_is_a_reference_error(node_js):
    bare = node_js("surface/live/nflnow.js")      # GD_ALIAS lives in live.js, not listed
    with pytest.raises(JSError, match="GD_ALIAS is not defined"):
        bare("gdSameClub", "WSH", "WAS")


def test_undefined_comes_back_as_none(js):
    assert js("(() => {})") is None
