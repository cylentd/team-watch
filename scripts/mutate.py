"""Mutation check on the code a branch changed (2026-10-05): does a test fail when the behaviour breaks?

    python scripts/mutate.py                          # design/src/js/data/*.js and design/*.py changed vs origin/main
    python scripts/mutate.py --files design/src/js/data/stock.js --max-mutants 10
    python scripts/mutate.py --threshold 60 --gate    # exit 1 below the threshold (default: warn, exit 0)
    python scripts/mutate.py --json                   # the report as JSON
    python scripts/mutate.py --budget 120             # start no new mutant after 120 s; partial score

One operator at a time, one mutant at a time: the mutated file is written in place, the tests that cover
it run, and the file is put back (a `finally`, SIGINT/SIGTERM and atexit all restore it, and the sha256
is checked). A mutant is killed when those tests exit nonzero or time out, and survives when they pass.
Score = killed / mutants. With --base, only lines the branch added or changed are mutated (the diff
against the fork point, uncommitted edits included); with --files, every line.

Operators (text level; comments, strings and JS regex literals are skipped):
    cmp     < <= > >=  === !==  == !=          arith   + -  * /
    bool    && ||  and or  true false          return  `return X` -> `return null` / `return None`
    const   integer n -> n+1

Tests per file: tests that name the file (data/<x>.js, or `import <x>` for design/<x>.py), plus the
tests impact.py picks for it, minus the shared checks (build, lint, budgets...) and test_render.py.
Node- and Python-layer files are preferred over browser ones, and `-m "not render"` is passed. The
unmutated file must pass them first, else the file is skipped as "baseline red". A file no test covers
counts every mutant as survived: untested changed code is what the score is for.

A mutant that does not parse (`node --check`, `compile`) is dropped, not counted. Mutants an equivalent
rewrite cannot be told from (x * 1 -> x / 1) survive; that is why the gate starts at 60%, not 100%.
"""
import argparse
import atexit
import contextlib
import hashlib
import json
import os
import pathlib
import random
import re
import shutil
import signal
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import impact  # noqa: E402

JS_DIR = "design/src/js/data/"
TIMEOUT = 120
# Shared checks that read every file or the assembled page: they never prove a function's behaviour.
META = {"test_assemble", "test_budgets", "test_build", "test_honest_tests", "test_impact", "test_js_harness",
        "test_js_syntax", "test_layer_ratchet", "test_lint", "test_mutate", "test_page_leak", "test_render",
        "test_scope", "test_style_rules", "test_sources_behind"}
HEAVY = re.compile(r"\b(browser|mount|page_file|built|open_view|sync_playwright)\b")
KEYWORDS = {"return", "typeof", "in", "of", "case", "yield", "function", "import", "print", "and", "or", "not",
            "if", "else", "elif", "lambda", "is", "await", "throw", "delete", "void", "new", "from", "while"}
OPS = re.compile(r"===|!==|==|!=|<=|>=|<<|>>|=>|->|&&|\|\||\+\+|--|\*\*|//|[+\-*/%]=|\*|/|\+|-|<|>")
SWAP = {"===": "!==", "!==": "===", "==": "!=", "!=": "==", "<": "<=", "<=": "<", ">": ">=", ">=": ">",
        "+": "-", "-": "+", "*": "/", "/": "*"}
JS_WORDS = {"true": "false", "false": "true"}
PY_WORDS = {"True": "False", "False": "True", "and": "or", "or": "and"}

_HELD = {}  # path -> original bytes of a file currently mutated


# ---------------------------------------------------------------- masking: what is code


def _skip_str(s, i, q):
    """Index after the string that opens at s[i] (quote q), a newline ending an unclosed one."""
    j = i + 1
    while j < len(s) and s[j] != q and s[j] != "\n":
        j += 2 if s[j] == "\\" else 1
    return min(j + 1, len(s))


def _skip_template(s, i):
    j = i + 1
    while j < len(s) and s[j] != "`":
        if s[j] == "\\":
            j += 2
        elif s.startswith("${", j):
            depth, j = 1, j + 2
            while j < len(s) and depth:
                if s[j] == "`":
                    j = _skip_template(s, j)
                    continue
                depth += {"{": 1, "}": -1}.get(s[j], 0)
                j += 1
        else:
            j += 1
    return min(j + 1, len(s))


def _skip_regex(s, i):
    j, cls = i + 1, False
    while j < len(s) and s[j] != "\n":
        if s[j] == "\\":
            j += 1
        elif s[j] == "[":
            cls = True
        elif s[j] == "]":
            cls = False
        elif s[j] == "/" and not cls:
            return j + 1
        j += 1
    return None


def _blank(out, a, b):
    for k in range(a, b):
        if out[k] != "\n":
            out[k] = " "


def mask_js(s):
    """s with comments, string and template bodies and regex literals blanked (same length, quotes kept)."""
    out, i, n, last = list(s), 0, len(s), ""
    while i < n:
        c = s[i]
        if s.startswith("//", i):
            j = s.find("\n", i)
            j = n if j < 0 else j
            _blank(out, i, j)
            i = j
        elif s.startswith("/*", i):
            j = s.find("*/", i + 2)
            j = n if j < 0 else j + 2
            _blank(out, i, j)
            i = j
        elif c in "'\"":
            j = _skip_str(s, i, c)
            _blank(out, i + 1, j - 1)
            i, last = j, "a"
        elif c == "`":
            j = _skip_template(s, i)
            _blank(out, i + 1, j - 1)
            i, last = j, "a"
        elif c == "/" and (last == "" or last in "(,=:[!&|?{};+-*%<>~^" or last in KEYWORDS):
            j = _skip_regex(s, i)
            if j is None:
                i += 1
            else:
                _blank(out, i + 1, j)
                i, last = j, "a"
        elif c.isspace():
            i += 1
        elif c.isalnum() or c in "_$":
            j = i
            while j < n and (s[j].isalnum() or s[j] in "_$"):
                j += 1
            last = s[i:j] if s[i:j] in KEYWORDS else "a"
            i = j
        else:
            last = c
            i += 1
    return "".join(out)


def mask_py(s):
    out, i, n = list(s), 0, len(s)
    while i < n:
        c = s[i]
        if c == "#":
            j = s.find("\n", i)
            j = n if j < 0 else j
            _blank(out, i, j)
            i = j
        elif c in "'\"":
            if s.startswith(c * 3, i):
                j = i + 3
                while j < n and not s.startswith(c * 3, j):
                    j += 2 if s[j] == "\\" else 1
                j = min(j + 3, n)
                _blank(out, i + 3, j - 3)
            else:
                j = _skip_str(s, i, c)
                _blank(out, i + 1, j - 1)
            i = j
        else:
            i += 1
    return "".join(out)


# ---------------------------------------------------------------- operators


def _prev_word(line, end):
    m = re.search(r"([A-Za-z_$][\w$]*)\s*$", line[:end])
    return m.group(1) if m else ""


def _binary(line, a, b):
    """Is the operator at line[a:b] binary: an operand before it, one after, and not a keyword."""
    before, after = line[:a].rstrip(), line[b:].lstrip()
    if not before or not after or before[-1] not in "\"'`)]}" + "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_$":
        return False
    return _prev_word(line, a) not in KEYWORDS and after[0] not in "=*+-" and after[:1] != ">"


def _return_end(line, start, py):
    """End of the expression `return` at `start` returns, or None when the line does not hold all of it."""
    depth, j = 0, start
    while j < len(line):
        ch = line[j]
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
            if depth < 0:
                return None if py else (j if line[start:j].strip() else None)
        elif ch == ";" and depth == 0:
            return j
        j += 1
    rest = line[start:].rstrip()
    if py and depth == 0 and rest and not rest.endswith(("\\", ":", ",")):
        return start + len(rest)
    return None


def line_mutants(line, py):
    """(col_start, col_end, op, old, new) for one masked line."""
    found = []
    for m in OPS.finditer(line):
        t = m.group()
        if t in ("===", "!==", "==", "!=", "<", "<=", ">", ">="):
            found.append((m.start(), m.end(), "cmp", t, SWAP[t]))
        elif t in ("+", "-", "*", "/") and _binary(line, m.start(), m.end()):
            found.append((m.start(), m.end(), "arith", t, SWAP[t]))
        elif t in ("&&", "||") and not py:
            found.append((m.start(), m.end(), "bool", t, "||" if t == "&&" else "&&"))
    words = PY_WORDS if py else JS_WORDS
    for m in re.finditer(r"(?<![\w$.])(" + "|".join(words) + r")(?![\w$])", line):
        found.append((m.start(), m.end(), "bool", m.group(), words[m.group()]))
    for m in re.finditer(r"(?<![\w$.])\d+(?![\w$]|\.\d)", line):
        t = m.group()
        if (len(t) == 1 or t[0] != "0") and not line[m.end():].startswith("."):
            found.append((m.start(), m.end(), "const", t, str(int(t) + 1)))
    r = re.search(r"(?<![\w$.])return[ \t]+", line)
    if r and (not py or not line[:r.start()].strip()):
        end = _return_end(line, r.end(), py)
        old = line[r.end():end].rstrip() if end else ""
        if old and old not in ("null", "None"):
            found.append((r.end(), r.end() + len(old), "return", old, "None" if py else "null"))
    return found


def mutants_of(text, py, lines=None):
    """Every mutant of text, as dicts with the offsets to splice; lines limits them to those (1-based)."""
    masked = (mask_py if py else mask_js)(text)
    out, offset = [], 0
    raw = text.split("\n")
    for no, line in enumerate(masked.split("\n"), 1):
        if lines is None or no in lines:
            for a, b, op, old, new in line_mutants(line, py):
                out.append({"line": no, "op": op, "old": text[offset + a:offset + b], "new": new,
                            "start": offset + a, "end": offset + b})
        offset += len(raw[no - 1]) + 1
    return out


def sample(muts, limit, seed):
    """At most limit mutants, the same ones every run for the same file."""
    if limit is None or len(muts) <= limit:
        return muts
    return [muts[i] for i in sorted(random.Random(seed).sample(range(len(muts)), limit))]


# ---------------------------------------------------------------- git: which files, which lines


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


def eligible(path):
    p = path.replace("\\", "/")
    return (p.startswith(JS_DIR) and p.endswith(".js")) or \
        (p.startswith("design/") and p.endswith(".py") and "/" not in p[len("design/"):])


def changed_files(base, root=ROOT):
    fork = git(root, "merge-base", base, "HEAD").strip()
    listed = git(root, "diff", "--no-renames", "--name-only", fork).splitlines() + \
        git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    return sorted({p for p in listed if eligible(p) and (pathlib.Path(root) / p).is_file()})


def changed_lines(base, path, root=ROOT):
    """1-based line numbers of path that differ from the fork point (committed, uncommitted, untracked)."""
    fork = git(root, "merge-base", base, "HEAD").strip()
    if git(root, "ls-files", "--others", "--exclude-standard", "--", path).strip():
        return None  # untracked: every line is new
    got = set()
    for m in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", git(root, "diff", "-U0", "--no-renames",
                                                                          fork, "--", path), re.M):
        start, count = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
        got.update(range(start, start + count))
    return got


# ---------------------------------------------------------------- which tests


def tests_for(path, root=ROOT):
    """Test files that cover path: the ones naming it, plus impact.py's pick, the light layers first."""
    root = pathlib.Path(root)
    stem = pathlib.PurePosixPath(path).stem
    if path.startswith(JS_DIR):
        named = re.compile(r"data/" + re.escape(path[len(JS_DIR):]) + r"\b|" + re.escape(path))
    else:
        named = re.compile(r"(?m)^\s*(?:from|import)\s+" + re.escape(stem) + r"\b|\b" + re.escape(stem) + r"\.py\b")
    core = set(impact.select([])["files"])
    picked = {f for f in impact.select([path])["files"] if f not in core and pathlib.PurePosixPath(f).stem not in META}
    texts = {}
    for f in sorted((root / "tests").glob("test_*.py")):
        if f.stem in META:
            continue
        rel = "tests/" + f.name
        texts[rel] = f.read_text(encoding="utf-8")
        if named.search(texts[rel]):
            picked.add(rel)
    picked = sorted(f for f in picked if (root / f).is_file())
    light = [f for f in picked if not HEAVY.search(texts.get(f) or (root / f).read_text(encoding="utf-8"))]
    return light or picked


def run_pytest(files, timeout=TIMEOUT, root=ROOT):
    """pytest exit code for these files; a hang counts as 124 (a killed mutant, usually a loop)."""
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "TW_RUN_KIND": "mutate"}
    try:
        return subprocess.run([sys.executable, "-m", "pytest", *files, "-x", "-q", "-p", "no:randomly",
                               "-m", "not render"], cwd=root, env=env, capture_output=True,
                              timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        return 124


def parses(path):
    p = pathlib.Path(path)
    if p.suffix == ".py":
        try:
            compile(p.read_text(encoding="utf-8"), str(p), "exec")
            return True
        except SyntaxError:
            return False
    node = shutil.which("node")
    return node is None or subprocess.run([node, "--check", str(p)], capture_output=True).returncode == 0


# ---------------------------------------------------------------- the file is always put back


def digest(b):
    return hashlib.sha256(b).hexdigest()


def put_back(path):
    original = _HELD.get(path)
    if original is None:
        return
    pathlib.Path(path).write_bytes(original)
    if digest(pathlib.Path(path).read_bytes()) != digest(original):
        raise RuntimeError(f"{path} was not restored: restore it with git checkout or from your editor")
    del _HELD[path]
    clear_pyc(path)


def clear_pyc(path):
    """A same-size mutant inside one second would load the last mutant's bytecode."""
    p = pathlib.Path(path)
    for pyc in (p.parent / "__pycache__").glob(p.stem + ".*.pyc"):
        with contextlib.suppress(OSError):
            pyc.unlink()


@contextlib.contextmanager
def in_place(path, text):
    """path holds text inside the block, and its original bytes after it, whatever happens."""
    p = pathlib.Path(path)
    _HELD.setdefault(path, p.read_bytes())
    try:
        p.write_bytes(text.encode("utf-8"))
        clear_pyc(path)
        yield
    finally:
        put_back(path)


def restore_all():
    for path in list(_HELD):
        with contextlib.suppress(Exception):
            put_back(path)


def _die(signum, frame):
    raise KeyboardInterrupt


# ---------------------------------------------------------------- the run


def mutate_file(rel, root, lines, limit, run=run_pytest, valid=parses, tests=None, deadline=None,
                clock=time.monotonic):
    """One file's report. run(files) -> exit code; valid(path) -> bool; tests overrides the selection.
    No mutant starts once clock() passes deadline (a `clock` value, None = no limit): budget_hit is set."""
    path = str(pathlib.Path(root) / rel)
    py = rel.endswith(".py")
    original = pathlib.Path(path).read_bytes()
    text = original.decode("utf-8")
    muts = sample(mutants_of(text, py, lines), limit, rel)
    report = {"path": rel, "status": "ok", "tests": [], "mutants": 0, "killed": 0, "survived": [], "invalid": 0,
              "planned": len(muts), "budget_hit": False}

    def late():
        return deadline is not None and clock() > deadline
    if not muts:
        return {**report, "status": "no mutants"}
    files = tests_for(rel, root) if tests is None else tests
    report["tests"] = files
    if not files:
        report["status"] = "untested"
        report["mutants"] = len(muts)
        report["survived"] = [_shown(m) for m in muts]
        return report
    if late():
        return {**report, "status": "budget", "budget_hit": True}
    if run(files) != 0:
        return {**report, "status": "baseline red"}
    for m in muts:
        if late():
            report["budget_hit"] = True
            break
        with in_place(path, text[:m["start"]] + m["new"] + text[m["end"]:]):
            if not valid(path):
                report["invalid"] += 1
                continue
            code = run(files)
        report["mutants"] += 1
        if code != 0:
            report["killed"] += 1
        else:
            report["survived"].append(_shown(m))
    if digest(pathlib.Path(path).read_bytes()) != digest(original):
        raise RuntimeError(f"{rel} differs from its original after the run")
    return report


def _shown(m):
    return {"line": m["line"], "op": m["op"], "old": m["old"], "new": m["new"]}


def score(killed, total):
    return None if not total else round(100.0 * killed / total, 1)


def summarize(reports, threshold):
    killed, total = sum(r["killed"] for r in reports), sum(r["mutants"] for r in reports)
    s = score(killed, total)
    run = sum(r["mutants"] + r.get("invalid", 0) for r in reports)
    planned = sum(r["planned"] if r.get("budget_hit") else r["mutants"] + r.get("invalid", 0) for r in reports)
    return {"threshold": threshold, "killed": killed, "mutants": total, "score": s,
            "pass": s is None or s >= threshold, "files": reports,
            "budget_hit": any(r.get("budget_hit") for r in reports), "run": run, "planned": planned}


def render(summary):
    lines = []
    for r in summary["files"]:
        head = f"{r['path']}  [{r['status']}]"
        if r["tests"]:
            head += "  tests: " + " ".join(r["tests"])
        lines.append(head)
        if r["mutants"]:
            lines.append(f"  mutants {r['mutants']}  killed {r['killed']}  survived {len(r['survived'])}"
                         f"  score {score(r['killed'], r['mutants'])}%")
        for s in r["survived"]:
            lines.append(f"  survived: line {s['line']} {s['op']} `{s['old']}` -> `{s['new']}`")
    if summary["score"] is None:
        lines.append("overall: no mutants")
    else:
        lines.append(f"overall: {summary['killed']}/{summary['mutants']} killed = {summary['score']}% "
                     f"(threshold {summary['threshold']}%)")
    if summary.get("budget_hit"):
        lines.append(f"(budget hit: {summary['run']} of {summary['planned']} mutants run)")
    return "\n".join(lines)


def main(argv=None, run=run_pytest, valid=parses, root=ROOT):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--files", nargs="+", help="mutate these (repo-relative) files, every line")
    ap.add_argument("--threshold", type=float, default=60.0)
    ap.add_argument("--gate", action="store_true", help="exit 1 below the threshold")
    ap.add_argument("--max-mutants", type=int, default=30, help="per file, sampled with a fixed seed")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--budget", type=float, metavar="SECONDS",
                    help="start no new mutant after this many seconds; the partial score is reported")
    a = ap.parse_args(argv)
    atexit.register(restore_all)
    old = {s: signal.signal(s, _die) for s in (signal.SIGINT, signal.SIGTERM)}
    try:
        return _run(a, run, valid, root)
    finally:
        for s, handler in old.items():
            signal.signal(s, handler)
        restore_all()


def _run(a, run, valid, root):
    try:
        if a.files:
            targets = [(f.replace("\\", "/"), None) for f in a.files]
        else:
            targets = [(f, changed_lines(a.base, f, root)) for f in changed_files(a.base, root)]
    except subprocess.CalledProcessError as e:
        print(f"mutate: git failed ({e.stderr.strip() or e}); is {a.base} fetched?", file=sys.stderr)
        return 2
    reports = []
    deadline = None if a.budget is None else time.monotonic() + a.budget
    for rel, lines in targets:
        if not eligible(rel):
            print(f"mutate: {rel} is not design/src/js/data/*.js or design/*.py", file=sys.stderr)
            return 2
        reports.append(mutate_file(rel, root, lines, a.max_mutants, run=run, valid=valid, deadline=deadline))
    summary = summarize(reports, a.threshold)
    print(json.dumps(summary, indent=1) if a.json else render(summary))
    if not summary["pass"]:
        print(f"WARNING: mutation score {summary['score']}% is below {a.threshold:g}%: a test the branch "
              "added or kept does not fail when the code it covers breaks", file=sys.stderr)
        return 1 if a.gate else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
