"""Size budgets, as ratchets: what is over today is listed with its size and may only shrink;
anything new must fit. Numbers, not opinions -- see shared/architecture.md, "Budgets, not vibes"."""
import ast
import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
SRC = REPO / "design" / "src"

PART_LINES = 250          # a src part; the rule's 500 halved because these are single-concern by construction
FUNCTION_LINES = 60

# JS functions over budget when the ratchet was set (2026-09-10). Shrink one, lower its number.
JS_BACKLOG = {
    "wireBuilder": 140,
    "parlayHTML": 93,
    "scatterHTML": 74,
    "openPoolDrawer": 64,
    "dfsSurfaceHTML": 64,
    "openDrawer": 63,
}
# Same for design/*.py. build.py itself is over the 500-line file budget; the split that fixes
# that is a model-vs-view change, not a refactor, so it is a ratchet here rather than a fail.
PY_FILE_BACKLOG = {"build.py": 900}
PY_BACKLOG = {"live_props": 200, "render": 110, "live_dfs_yahoo": 70}


def parts():
    return sorted(p for p in SRC.rglob("*") if p.is_file() and p.suffix in (".css", ".js", ".html"))


@pytest.mark.parametrize("path", parts(), ids=lambda p: p.relative_to(SRC).as_posix())
def test_part_within_budget(path):
    n = path.read_text(encoding="utf-8").count("\n")
    assert n <= PART_LINES, f"{n} lines; split it"


def js_functions():
    """(name, lines) for every top-level `function name(` whose body closes with a `}` at col 0."""
    out = []
    for p in sorted(SRC.rglob("*.js")):
        lines = p.read_text(encoding="utf-8").split("\n")
        i = 0
        while i < len(lines):
            m = re.match(r"^(?:async )?function (\w+)\(", lines[i])
            if m:
                j = i + 1
                while j < len(lines) and lines[j] != "}":
                    j += 1
                out.append((m.group(1), j - i + 1))
                i = j
            i += 1
    return out


@pytest.mark.parametrize("name,n", js_functions(), ids=lambda x: x if isinstance(x, str) else "")
def test_js_function_within_budget(name, n):
    cap = max(FUNCTION_LINES, JS_BACKLOG.get(name, 0))
    assert n <= cap, f"{name} is {n} lines (budget {cap})"


def test_js_backlog_is_still_needed():
    """A function that shrank under budget leaves the list, so the list cannot rot."""
    sizes = dict(js_functions())
    stale = [k for k, v in JS_BACKLOG.items() if sizes.get(k, 0) <= FUNCTION_LINES]
    assert stale == [], f"remove from JS_BACKLOG, now within budget: {stale}"


def py_functions(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [(n.name, n.end_lineno - n.lineno + 1) for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


@pytest.mark.parametrize("path", sorted((REPO / "design").glob("*.py")), ids=lambda p: p.name)
def test_py_file_within_budget(path):
    n = path.read_text(encoding="utf-8").count("\n")
    assert n <= PY_FILE_BACKLOG.get(path.name, 500), f"{n} lines"


@pytest.mark.parametrize("path", sorted((REPO / "design").glob("*.py")), ids=lambda p: p.name)
def test_py_functions_within_budget(path):
    over = [(name, n) for name, n in py_functions(path)
            if n > max(FUNCTION_LINES, PY_BACKLOG.get(name, 0))]
    assert over == []


def test_no_hand_mirrored_logic_grows():
    """`mirrors ff-jarvis` comments mark logic copied across repos (architecture rule: never).
    The four that exist are known; a fifth is a new scheduled bug."""
    text = (REPO / "design" / "build.py").read_text(encoding="utf-8")
    assert len(re.findall(r"[Mm]irrors ff-jarvis", text)) <= 4
