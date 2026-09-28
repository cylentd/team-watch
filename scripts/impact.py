"""Which tests a branch's diff can break (2026-09-27). land.ps1 runs these instead of everything.

    python scripts/impact.py                   # the diff against origin/main
    python scripts/impact.py --paths a.js b.py # any list of paths

Prints JSON: {"all": bool, "why": [...], "files": [test files], "areas": [golden areas]}. The
run is `pytest <files> --areas <areas>`; `--areas` narrows tests/test_render.py to those areas
(tests/conftest.py).

tests/impact.json owns the map. A path no area claims runs everything, so a missing entry costs
time, never coverage. A view's CSS counts as its area's only when design/src/scope.json fences
it; a shared file can style any view. The scheduled rebuild runs the whole suite twice a day,
which is the net for anything the map gets wrong.
"""
import argparse
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MAP = ROOT / "tests" / "impact.json"
SCOPE = ROOT / "design" / "src" / "scope.json"
CSS_SURFACE = "design/src/css/surface/"


def load():
    return json.loads(MAP.read_text(encoding="utf-8")), json.loads(SCOPE.read_text(encoding="utf-8"))


def owner(path, areas):
    """The area whose paths claim this one: a trailing `/` is a directory, anything else a file."""
    for name, area in areas.items():
        if any(path.startswith(p) if p.endswith("/") else path == p for p in area["paths"]):
            return name
    return None


def select(paths, cfg=None, scope=None):
    if cfg is None:
        cfg, scope = load()
    fenced = {CSS_SURFACE + rel[len("surface/"):] for rel in scope["fenced"]}
    files, areas, why = list(cfg["core"]), set(), []
    for path in paths:
        if path.endswith(".md"):
            continue
        if path.startswith("tests/"):
            if path.startswith("tests/test_") and path.endswith(".py") and path != "tests/test_render.py":
                files.append(path)
            elif path != "tests/impact.json":
                why.append(f"{path} is shared test setup")
            continue
        if path.startswith(CSS_SURFACE) and path not in fenced:
            why.append(f"{path} is shared CSS (design/src/scope.json)")
            continue
        name = owner(path, cfg["areas"])
        if name is None:
            why.append(f"no area owns {path}")
            continue
        files += cfg["areas"][name]["tests"]
        areas.update(cfg["areas"][name]["render"])
    if areas:
        files.append("tests/test_render.py")
    return {"all": bool(why), "why": why, "files": sorted(set(files)), "areas": sorted(areas)}


def changed(base):
    out = subprocess.run(["git", "-C", str(ROOT), "diff", "--no-renames", "--name-only", f"{base}...HEAD"],
                         capture_output=True, text=True, check=True).stdout
    return [p for p in out.splitlines() if p]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--paths", nargs="*")
    a = ap.parse_args(argv)
    print(json.dumps(select(a.paths if a.paths is not None else changed(a.base))))


if __name__ == "__main__":
    sys.exit(main())
