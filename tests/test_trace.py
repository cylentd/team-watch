"""The req and quarantine markers, their validation, and scripts/trace.py (tests/README.md "Markers").

The conftest hooks are tested through their helpers and, for the command-line option, through a
small pytester run that reuses this repo's conftest.
"""
import datetime as dt
import importlib.util
import pathlib
import types

import pytest

import conftest

REPO = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("tw_trace_test", REPO / "scripts" / "trace.py")
trace = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(trace)

DOC = """# Title
## Ranks (Stats, 2026-09-26; D/ST and K 2026-10-05)
text
## Start/Sit (This week)
```
## not a heading
```
### Third level
## Parlay and DFS
## Ranks (again)
"""


def test_sections_are_headings_cut_at_the_first_paren():
    assert trace.design_sections(DOC) == ["Ranks", "Start/Sit", "Parlay and DFS"]


def test_sections_skip_fenced_code_and_deeper_headings():
    assert "not a heading" not in trace.design_sections(DOC)
    assert "Third level" not in trace.design_sections(DOC)


def test_the_real_design_doc_has_sections_the_suite_can_name():
    names = trace.design_sections()
    assert {"Ranks", "Digest", "Start/Sit", "Parlay and DFS"} <= set(names)
    assert all(n == n.strip() and " (" not in n for n in names)


@pytest.mark.integration      # collects the whole suite in a pytest process
def test_every_req_in_the_suite_names_a_section_design_md_has():
    """A renamed DESIGN.md heading fails here, naming the tests to retarget (impact.json `designdoc`)."""
    tests, code, out = trace.collect()
    assert code == 0, out[-2000:]
    sections = set(trace.design_sections())
    bad = [(t["test"], r["section"]) for t in tests for r in t["req"] if r["section"] not in sections]
    assert bad == [], f"req names a section DESIGN.md lacks: {bad}"
    assert any(t["req"] for t in tests), "no req marker collected: the collection itself is broken"


def item(nodeid, *marks):
    """A stand-in for a collected test: only what bad_reqs reads."""
    markers = [types.SimpleNamespace(name=n, args=a, kwargs=k) for n, a, k in marks]
    return types.SimpleNamespace(
        nodeid=nodeid, iter_markers=lambda name=None: [m for m in markers if name in (None, m.name)])


def test_a_req_naming_a_missing_section_is_reported_with_its_test():
    good = item("t.py::a", ("req", ("Ranks",), {}))
    typo = item("t.py::b", ("req", ("Rankz",), {"ac": "x"}))
    none = item("t.py::c", ("req", (), {}))
    other = item("t.py::d", ("area", ("ranks",), {}))
    assert conftest.bad_reqs([good, typo, none, other], ["Ranks"]) == [("t.py::b", "Rankz"), ("t.py::c", None)]


def test_a_req_section_may_be_a_keyword():
    assert conftest.bad_reqs([item("t.py::a", ("req", (), {"section": "Ranks"}))], ["Ranks"]) == []


def fixtures(*names):
    return types.SimpleNamespace(fixturenames=names)


def test_a_mount_test_is_a_component_test_even_with_a_browser():
    assert conftest.layer_of(fixtures("mount")) == "component"
    assert conftest.layer_of(fixtures("browser", "mount")) == "component"
    assert conftest.layer_of(fixtures("mount", "built")) == "component"


def test_the_other_layers_keep_their_order():
    assert conftest.layer_of(fixtures("browser")) == "browser"
    assert conftest.layer_of(fixtures("browser", "built")) == "browser"
    assert conftest.layer_of(fixtures("built")) == "build"
    assert conftest.layer_of(fixtures("page_file")) == "build"
    assert conftest.layer_of(fixtures("node_js")) == "node"
    assert conftest.layer_of(fixtures()) == "python"


def marked(*names, marks=()):
    """A stand-in for a collected test with fixtures and marks: what layer_of reads."""
    return types.SimpleNamespace(fixturenames=names, get_closest_marker=lambda m: object() if m in marks else None)


def test_an_integration_marked_test_is_the_integration_layer():
    assert conftest.layer_of(marked(marks=("integration",))) == "integration"
    assert conftest.layer_of(marked("node_js", marks=("integration",))) == "integration"
    assert conftest.layer_of(marked(marks=("journey",))) == "python", "only the integration marker moves a layer"


def test_a_fixture_decides_the_layer_before_the_integration_marker_does():
    assert conftest.layer_of(marked("browser", marks=("integration",))) == "browser"
    assert conftest.layer_of(marked("mount", marks=("integration",))) == "component"
    assert conftest.layer_of(marked("built", marks=("integration",))) == "build"


def test_quarantine_age_is_counted_from_the_date_in_the_reason():
    today = dt.date(2026, 10, 10)
    assert trace.quarantine_days("2026-10-06 flaky: chat panel race", today) == 4
    assert trace.quarantine_days("flaky, no date", today) is None
    assert trace.quarantine_days("2026-13-45 not a date", today) is None


def test_report_groups_tests_by_section_and_lists_the_rest():
    tests = [
        {"test": "t.py::a", "req": [{"section": "Ranks", "ac": "tiers"}], "quarantine": []},
        {"test": "t.py::b", "req": [{"section": "Ranks", "ac": None}], "quarantine": ["2026-10-06 flaky"]},
        {"test": "t.py::c", "req": [], "quarantine": []},
    ]
    rep = trace.report(tests, ["Ranks", "Digest"], today=dt.date(2026, 10, 7))
    assert [r["test"] for r in rep["sections"]["Ranks"]] == ["t.py::a", "t.py::b"]
    assert rep["untested"] == ["Digest"]
    assert rep["quarantined"] == [{"test": "t.py::b", "reason": "2026-10-06 flaky", "days": 1}]
    text = trace.render(rep)
    assert "1 of 2 DESIGN.md sections have a test" in text and "No test (1): Digest" in text


# --- the hooks, end to end, in a throwaway pytest run that loads this repo's conftest -----------

pytest_plugins = ["pytester"]

SAMPLE = """
import pytest

def test_plain(): pass

@pytest.mark.quarantine("2026-10-06 flaky: race")
def test_flaky(): pass

@pytest.mark.req("Ranks", ac="tiers")
def test_traced(): pass
"""


PLUGINS = ("-p", "no:xdist", "-p", "conftest")   # this repo's conftest, loaded as a plugin of the throwaway run


@pytest.fixture
def sandbox(pytester, monkeypatch):
    """A throwaway test directory run with this repo's conftest; its runs stay out of the test history."""
    monkeypatch.setenv("TW_TEST_HISTORY", "off")
    pytester.makepyfile(test_sample=SAMPLE)
    return pytester


@pytest.mark.integration      # two pytest runs in this process
def test_no_quarantine_deselects_only_the_quarantined(sandbox):
    everything = sandbox.runpytest_inprocess(*PLUGINS)
    everything.assert_outcomes(passed=3)
    gated = sandbox.runpytest_inprocess(*PLUGINS, "--no-quarantine")
    gated.assert_outcomes(passed=2, deselected=1)


@pytest.mark.integration      # a pytest run in this process
def test_a_bad_req_stops_collection_and_names_the_test(sandbox):
    sandbox.makepyfile(test_bad='import pytest\n\n@pytest.mark.req("Nope")\ndef test_typo(): pass\n')
    res = sandbox.runpytest_inprocess(*PLUGINS)
    assert res.ret != 0
    res.stderr.fnmatch_lines(["*test_bad.py::test_typo*'Nope'*"])
    res.stderr.fnmatch_lines(["*valid sections*"])
