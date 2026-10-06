"""Which files, which lines and which tests a mutation run covers, and how it runs them (2026-10-06 split)."""
import os
import pathlib
import re
import shutil
import subprocess
import sys

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
