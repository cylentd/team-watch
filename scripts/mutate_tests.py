"""Which tests the mutator runs against one source file (2026-10-06): prints them, one per line.

    python scripts/mutate_tests.py design/src/js/data/stock.js

The testing skill's mutate.py calls this through `.testing.json` `mutate.select_command`, so the pick follows
impact.json instead of a hand-kept map. Tests per file: the ones naming it (data/<x>.js, or `import <x>` for
design/<x>.py), plus impact.py's pick for it minus the always-run core, minus the whole-repo checks (META).
Node- and Python-layer files are preferred over browser ones (HEAVY).
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import impact  # noqa: E402

JS_DIR = "design/src/js/data/"
# Shared checks that read every file or the assembled page: they never prove a function's behaviour.
META = {"test_assemble", "test_budgets", "test_build", "test_honest_tests", "test_impact", "test_js_harness",
        "test_js_syntax", "test_layer_ratchet", "test_lint", "test_mutate_tests", "test_page_leak", "test_render",
        "test_scope", "test_style_rules", "test_sources_behind"}
HEAVY = re.compile(r"\b(browser|mount|page_file|built|open_view|sync_playwright)\b")


def tests_for(path, root=ROOT):
    """Test files that cover path: the ones naming it, plus impact.py's pick, the light layers first."""
    root = pathlib.Path(root)
    path = path.replace("\\", "/")
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


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: python scripts/mutate_tests.py <repo-relative source path>", file=sys.stderr)
        return 2
    for f in tests_for(args[0]):
        print(f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
