"""scripts/mutate.py: the operators, the changed-line restriction, restore on failure, the gate (2026-10-05).

No pytest subprocess per mutant: the runner is a function the tests pass in, and git work happens in a
throwaway repository.
"""
import hashlib
import json
import os
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import mutate  # noqa: E402

JS = "design/src/js/data/x.js"


def ops(src, py=False, lines=None):
    return [(m["op"], m["old"], m["new"]) for m in mutate.mutants_of(src, py, lines)]


# ---------------------------------------------------------------- operators


def test_comparison_operators_flip():
    assert ops("if (a < b) x();") == [("cmp", "<", "<=")]
    assert ops("if (a >= b) x();") == [("cmp", ">=", ">")]
    assert ops("if (a === b) x();") == [("cmp", "===", "!==")]
    assert ops("if (a != b) x();") == [("cmp", "!=", "==")]


def test_arithmetic_flips_only_a_binary_operator():
    assert ops("const c = a + b;") == [("arith", "+", "-")]
    assert ops("const c = a * (b / d);") == [("arith", "*", "/"), ("arith", "/", "*")]
    assert ops("const c = -a;") == []
    assert ops("const c = f(-a, +b, ...r);") == []
    assert ops("i++; j += 2; k **= 2;") == [("const", "2", "3"), ("const", "2", "3")]


def test_an_arrow_and_a_keyword_are_not_operators():
    assert ops("const f = (a) => a;") == []
    assert ops("return -x;", py=False) == [("return", "-x", "null")]
    assert ops("from m import *", py=True) == []


def test_boolean_operators_and_literals():
    assert ops("ok = a && b;") == [("bool", "&&", "||")]
    assert ops("ok = a || true;") == [("bool", "||", "&&"), ("bool", "true", "false")]
    assert ops("ok = a and b or False", py=True) == [("bool", "and", "or"), ("bool", "or", "and"),
                                                     ("bool", "False", "True")]
    assert ops("ok = a.true || b_true;") == [("bool", "||", "&&")]


def test_return_value_becomes_null_or_none():
    assert ops("function f(){ return a + 1; }") == [("arith", "+", "-"), ("const", "1", "2"),
                                                     ("return", "a + 1", "null")]
    assert ops("  return {a: [1, 2]};") == [("const", "1", "2"), ("const", "2", "3"),
                                            ("return", "{a: [1, 2]}", "null")]
    assert ops("def f():\n    return x, y\n", py=True) == [("return", "x, y", "None")]
    assert ops("return null;") == []
    assert ops("def f():\n    return None\n", py=True) == []
    assert ops("return;") == []


def test_a_return_that_continues_on_the_next_line_is_left_alone():
    assert ops("  return (\n    a\n  );") == []
    assert ops("def f():\n    return foo(\n        a)\n", py=True) == []


def test_integer_constants_nudge_by_one_but_floats_and_hex_do_not():
    assert ops("x = 5;") == [("const", "5", "6")]
    assert ops("x = 1.5 + 0x10 + 1e3 + a2;") == [("arith", "+", "-"), ("arith", "+", "-"), ("arith", "+", "-")]
    assert ops("x = obj.3;") == []


def test_comments_strings_and_regexes_are_skipped():
    src = 'const s = "a < b && 7"; // c > d, true\n/* 1 + 2 */ const t = `x ${a} < 3`;\nconst r = /a+b/g;'
    assert ops(src) == []
    assert ops("x = 'a == b'  # 3 < 4\n", py=True) == []
    assert ops('"""doc: 1 < 2\nmore"""\nx = 2', py=True) == [("const", "2", "3")]


def test_a_division_is_not_mistaken_for_a_regex():
    assert ops("const r = a / b / c;") == [("arith", "/", "*"), ("arith", "/", "*")]


def test_each_mutant_splices_into_valid_text():
    src = "function f(a, b){ return a < b ? 1 : 2; }\n"
    for m in mutate.mutants_of(src, False):
        out = src[:m["start"]] + m["new"] + src[m["end"]:]
        assert out != src and out.count("\n") == src.count("\n")


# ---------------------------------------------------------------- sampling and the changed-line restriction


def test_mutants_are_limited_to_the_given_lines():
    src = "a = b + 1;\nc = d - 2;\ne = f * 3;\n"
    assert {m["line"] for m in mutate.mutants_of(src, False)} == {1, 2, 3}
    assert {m["line"] for m in mutate.mutants_of(src, False, {2})} == {2}
    assert mutate.mutants_of(src, False, set()) == []


def test_sampling_is_deterministic_and_capped():
    muts = [{"start": i} for i in range(100)]
    a, b = mutate.sample(muts, 10, "f.js"), mutate.sample(muts, 10, "f.js")
    assert a == b and len(a) == 10
    assert [m["start"] for m in a] == sorted(m["start"] for m in a)
    assert mutate.sample(muts, 10, "g.js") != a
    assert mutate.sample(muts[:5], 10, "f.js") == muts[:5]


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A repository with `main` holding x.js and design/y.py, and one commit on a branch."""
    (tmp_path / "hooks").mkdir()

    def git(*args):
        subprocess.run(["git", "-C", str(tmp_path), "-c", f"core.hooksPath={tmp_path / 'hooks'}", *args],
                       check=True, capture_output=True, text=True,
                       env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})
    git("init", "-q", "-b", "main")
    (tmp_path / "design/src/js/data").mkdir(parents=True)
    (tmp_path / JS).write_text("a = 1;\nb = 2;\nc = 3;\nd = 4;\n", encoding="utf-8")
    (tmp_path / "design/y.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("hi\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-q", "-m", "base")
    git("checkout", "-q", "-b", "work")
    (tmp_path / JS).write_text("a = 1;\nb = 20;\nc = 3;\nd = 4;\n", encoding="utf-8")
    git("commit", "-qam", "edit line 2")
    return tmp_path


def test_changed_lines_are_the_committed_and_the_uncommitted_ones(repo):
    assert mutate.changed_lines("main", JS, repo) == {2}
    (repo / JS).write_text("a = 1;\nb = 20;\nc = 3;\nd = 40;\n", encoding="utf-8")
    assert mutate.changed_lines("main", JS, repo) == {2, 4}


def test_an_untracked_file_has_every_line_changed(repo):
    (repo / "design/new.py").write_text("x = 1\n", encoding="utf-8")
    assert mutate.changed_lines("main", "design/new.py", repo) is None


def test_changed_files_keep_only_data_js_and_design_py(repo):
    (repo / "design/y.py").write_text("x = 2\n", encoding="utf-8")
    (repo / "README.md").write_text("changed\n", encoding="utf-8")
    (repo / "design/src/js/data/new.js").write_text("z = 1;\n", encoding="utf-8")
    (repo / "design/src/js/ui").mkdir()
    (repo / "design/src/js/ui/u.js").write_text("z = 1;\n", encoding="utf-8")
    assert mutate.changed_files("main", repo) == ["design/src/js/data/new.js", JS, "design/y.py"]


def test_eligible_paths():
    assert mutate.eligible("design/src/js/data/gameday/hurt.js")
    assert mutate.eligible("design/build.py")
    assert not mutate.eligible("design/src/js/ui/player.js")
    assert not mutate.eligible("design/src/js/data/x.json")
    assert not mutate.eligible("tests/test_x.py")
    assert not mutate.eligible("design/tests/x.py")


# ---------------------------------------------------------------- which tests run


def _suite(root, files):
    (root / "tests").mkdir(exist_ok=True)
    for name, text in files.items():
        (root / "tests" / name).write_text(text, encoding="utf-8")


def test_tests_that_name_the_file_are_picked_and_the_light_ones_come_first(tmp_path):
    _suite(tmp_path, {
        "test_js_x.py": 'node_js("data/x.js")\n',
        "test_view_x.py": 'def test(browser):\n    page = "design/src/js/data/x.js"\n',
        "test_budgets.py": "design/src/js/data/x.js\n",
        "test_other.py": "nothing\n",
    })
    assert mutate.tests_for(JS, tmp_path) == ["tests/test_js_x.py"]


def test_a_python_file_is_found_by_its_import(tmp_path):
    _suite(tmp_path, {"test_y.py": "import y\n", "test_z.py": "import yy\nx = 'xy'\n"})
    assert mutate.tests_for("design/y.py", tmp_path) == ["tests/test_y.py"]


def test_heavy_files_are_used_when_no_light_one_covers_it(tmp_path):
    _suite(tmp_path, {"test_view_x.py": 'def test(browser):\n    "data/x.js"\n'})
    assert mutate.tests_for(JS, tmp_path) == ["tests/test_view_x.py"]


# ---------------------------------------------------------------- run, restore, score


SRC = "function f(a){\n  if (a < 5) return 1;\n  return 2;\n}\n"


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "design/src/js/data").mkdir(parents=True)
    path = tmp_path / JS
    path.write_bytes(SRC.replace("\n", "\r\n").encode("utf-8"))
    _suite(tmp_path, {"test_js_x.py": 'node_js("data/x.js")\n'})
    return tmp_path


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def killing(marker):
    """A runner that fails exactly when the file holds the marker text."""
    def run(files, **_):
        return 1 if marker in (pathlib.Path(run.root) / JS).read_text(encoding="utf-8") else 0
    return run


def valid(path):
    return True


def test_a_killed_and_a_surviving_mutant_are_counted_and_the_file_is_restored(tree):
    before = sha(tree / JS)
    run = killing("a <= 5")
    run.root = tree
    r = mutate.mutate_file(JS, tree, None, 30, run=run, valid=valid)
    assert (r["status"], r["killed"]) == ("ok", 1)
    assert r["mutants"] == len(r["survived"]) + 1
    assert {"line": 2, "op": "const", "old": "5", "new": "6"} in r["survived"]
    assert sha(tree / JS) == before


def test_only_the_changed_lines_are_mutated(tree):
    run = killing("never")
    run.root = tree
    r = mutate.mutate_file(JS, tree, {3}, 30, run=run, valid=valid)
    assert {s["line"] for s in r["survived"]} == {3}


def test_the_file_is_restored_when_the_runner_raises(tree):
    before, seen = sha(tree / JS), []

    def run(files, **_):
        seen.append((tree / JS).read_text(encoding="utf-8"))
        if len(seen) == 3:
            raise RuntimeError("boom")
        return 0
    with pytest.raises(RuntimeError):
        mutate.mutate_file(JS, tree, None, 30, run=run, valid=valid)
    assert len(seen) == 3 and seen[1].replace("\r\n", "\n") != SRC
    assert sha(tree / JS) == before and not mutate._HELD


def test_the_file_is_restored_on_an_interrupt(tree):
    before = sha(tree / JS)

    def run(files, **_):
        if sha(tree / JS) != before:  # a mutant is in place
            raise KeyboardInterrupt
        return 0
    with pytest.raises(KeyboardInterrupt):
        mutate.mutate_file(JS, tree, None, 30, run=run, valid=valid)
    assert sha(tree / JS) == before and not mutate._HELD


def test_restore_all_puts_back_a_file_a_dead_run_left(tree):
    before = sha(tree / JS)
    ctx = mutate.in_place(str(tree / JS), "garbage")
    ctx.__enter__()
    assert sha(tree / JS) != before
    mutate.restore_all()
    assert sha(tree / JS) == before and not mutate._HELD


def test_a_mutant_that_does_not_parse_is_dropped_not_counted(tree):
    run = killing("never")
    run.root = tree
    r = mutate.mutate_file(JS, tree, None, 30, run=run, valid=lambda p: "a <= 5" not in pathlib.Path(p).read_text())
    assert r["invalid"] == 1 and r["mutants"] == len(r["survived"])


def test_a_failing_baseline_skips_the_file(tree):
    r = mutate.mutate_file(JS, tree, None, 30, run=lambda files, **_: 1, valid=valid)
    assert r["status"] == "baseline red" and r["mutants"] == 0


def test_a_file_no_test_covers_counts_every_mutant_as_survived(tree):
    (tree / "tests" / "test_js_x.py").unlink()
    calls = []
    r = mutate.mutate_file(JS, tree, None, 30, run=lambda files, **_: calls.append(files) or 0, valid=valid)
    assert r["status"] == "untested" and r["killed"] == 0 and r["mutants"] == len(r["survived"]) > 0
    assert calls == []


def test_a_file_with_nothing_to_mutate_has_no_score(tree):
    (tree / JS).write_text("// nothing\n", encoding="utf-8")
    r = mutate.mutate_file(JS, tree, None, 30, run=lambda files, **_: 0, valid=valid)
    assert r["status"] == "no mutants"
    assert mutate.summarize([r], 60)["score"] is None and mutate.summarize([r], 60)["pass"]


def test_no_mutant_starts_after_the_budget_and_the_file_is_restored(tree):
    before, ticks = sha(tree / JS), iter(range(100))
    run = killing("never")
    run.root = tree
    r = mutate.mutate_file(JS, tree, None, 30, run=run, valid=valid, deadline=3, clock=lambda: next(ticks))
    # clock reads: baseline check 0, then one per mutant (1, 2, 3 run; 4 is past the deadline)
    assert r["budget_hit"] is True and r["mutants"] == 3 and r["planned"] > 3
    assert sha(tree / JS) == before and not mutate._HELD


def test_a_budget_already_spent_skips_the_file_but_counts_its_mutants(tree):
    r = mutate.mutate_file(JS, tree, None, 30, run=lambda f, **_: 0, valid=valid, deadline=0, clock=lambda: 1)
    assert (r["status"], r["mutants"], r["budget_hit"]) == ("budget", 0, True) and r["planned"] > 0


def test_the_summary_and_the_report_say_how_many_mutants_ran():
    partial = {"path": "a.js", "status": "ok", "tests": [], "mutants": 2, "killed": 1, "survived": [],
               "invalid": 0, "planned": 10, "budget_hit": True}
    whole = {"path": "b.js", "status": "ok", "tests": [], "mutants": 4, "killed": 4, "survived": [],
             "invalid": 0, "planned": 4, "budget_hit": False}
    s = mutate.summarize([partial, whole], 60)
    assert (s["run"], s["planned"], s["score"]) == (6, 14, 83.3)
    assert "(budget hit: 6 of 14 mutants run)" in mutate.render(s)
    assert "budget hit" not in mutate.render(mutate.summarize([whole], 60))


def test_the_budget_flag_stops_the_run_and_reports_the_partial_score(tree, capsys):
    code, out = cli(tree, capsys, "--budget", "-1")
    assert code == 0 and "(budget hit: 0 of " in out.out


def test_score_is_killed_over_mutants():
    assert mutate.score(3, 4) == 75.0
    assert mutate.score(0, 0) is None
    s = mutate.summarize([{"killed": 1, "mutants": 2}, {"killed": 2, "mutants": 2}], 60)
    assert (s["score"], s["pass"]) == (75.0, True)
    assert mutate.summarize([{"killed": 1, "mutants": 4}], 60)["pass"] is False
    assert mutate.summarize([{"killed": 3, "mutants": 5}], 60)["pass"] is True


# ---------------------------------------------------------------- the CLI and its exit codes


def cli(tree, capsys, *args, kill=False):
    def run(files, **_):
        text = (tree / JS).read_text(encoding="utf-8")
        return 1 if kill and text.replace("\r\n", "\n") != SRC else 0
    code = mutate.main(["--files", JS, *args], run=run, valid=valid, root=tree)
    return code, capsys.readouterr()


def test_below_the_threshold_warns_and_exits_zero_without_the_gate(tree, capsys):
    code, out = cli(tree, capsys)
    assert code == 0
    assert "WARNING: mutation score 0.0% is below 60%" in out.err
    assert "overall: 0/" in out.out and "survived: line 2" in out.out


def test_below_the_threshold_fails_with_the_gate(tree, capsys):
    code, out = cli(tree, capsys, "--gate")
    assert code == 1 and "WARNING" in out.err


def test_at_or_above_the_threshold_passes_the_gate(tree, capsys):
    code, out = cli(tree, capsys, "--gate", kill=True)
    assert code == 0 and "WARNING" not in out.err and "100.0%" in out.out


def test_the_threshold_is_configurable(tree, capsys):
    assert cli(tree, capsys, "--gate", "--threshold", "0")[0] == 0
    assert cli(tree, capsys, "--gate", "--threshold", "100")[0] == 1


def test_json_output_is_one_parsable_document_and_warnings_go_to_stderr(tree, capsys):
    code, out = cli(tree, capsys, "--json", "--max-mutants", "3")
    doc = json.loads(out.out)
    assert doc["mutants"] == 3 and doc["files"][0]["path"] == JS and doc["pass"] is False
    assert "WARNING" in out.err


def test_a_file_outside_the_scope_is_refused(tree, capsys):
    code = mutate.main(["--files", "design/src/js/ui/u.js"], run=lambda f, **_: 0, valid=valid, root=tree)
    assert code == 2


def test_base_mode_mutates_only_what_the_branch_changed(repo, capsys):
    _suite(repo, {"test_js_x.py": 'node_js("data/x.js")\n'})
    seen = []

    def run(files, **_):
        seen.append(1)
        return 0
    code = mutate.main(["--base", "main", "--json"], run=run, valid=valid, root=repo)
    doc = json.loads(capsys.readouterr().out)
    assert code == 0
    assert [f["path"] for f in doc["files"]] == [JS]
    assert {s["line"] for s in doc["files"][0]["survived"]} == {2}
