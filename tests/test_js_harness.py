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


# One node process serves every sandbox of a Python process (a spawn is 0.4 s, a sandbox is 5 ms),
# so the sandboxes must stay as apart as two processes were.
def test_a_global_set_in_one_sandbox_is_not_visible_in_another(node_js):
    first = node_js("data/startsit.js")
    second = node_js("data/startsit.js")
    first("(globalThis.leaked = 7)")
    assert first("typeof leaked") == "number"       # a sandbox keeps its own state between calls
    assert second("typeof leaked") == "undefined"
    first("(Array.prototype.leakedToo = 1)")        # nor does an edited built-in
    assert second("typeof [].leakedToo") == "undefined"


def test_a_planted_global_is_not_shared_between_sandboxes(node_js):
    first = node_js("data/startsit.js", globals={"PLANTED": {"n": 1}})
    second = node_js("data/startsit.js", globals={"PLANTED": {"n": 2}})
    first("(PLANTED.n = 99)")
    assert second("PLANTED.n") == 2


def test_sandboxes_share_one_node_process(node_js):
    assert node_js("data/startsit.js").pid == node_js("data/schedule.js").pid


def test_a_crashed_node_restarts_on_the_next_call(node_js):
    import jsunit
    js = node_js("data/startsit.js")
    js("(globalThis.leaked = 7)")
    old = js.pid
    jsunit.kill_host()
    assert js("typeof ss3Wl") == "function"         # a fresh sandbox of the same files
    assert js("typeof leaked") == "undefined"
    assert js.pid != old


def test_a_throw_leaves_the_sandbox_and_the_process_usable(js):
    with pytest.raises(JSError):
        js("t", "no.such.key")
    assert js("t", "matchups.vs.home", {"team": "DAL", "opp": "BAL"}) == "DAL vs BAL"
