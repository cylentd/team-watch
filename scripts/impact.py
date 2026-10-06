"""Which tests a branch's diff can break (2026-09-27). land.ps1 runs these instead of everything.

    python scripts/impact.py                   # the diff against origin/main
    python scripts/impact.py --worktree        # the same, uncommitted edits included
    python scripts/impact.py --paths a.js b.py # any list of paths

Prints JSON: {"all": bool, "why": [...], "files": [test files], "areas": [golden areas]}. The
run is `pytest <files> --areas <areas>`; `--areas` narrows tests/test_render.py to those areas
(tests/conftest.py).

tests/impact.json owns the map. A path no area claims runs everything, so a missing entry costs
time, never coverage. A view's CSS counts as its area's only when design/src/scope.json fences
it; a shared file can style any view. The scheduled rebuild runs the whole suite twice a day,
which is the net for anything the map gets wrong.

Five files every view shares are read by what changed inside them (2026-10-05), because nearly
every feature touches one, and until then 23 of the last 24 feature lands ran everything:

    design/src/content.json     a changed key counts as the files that say t("key") / {{copy:key}}
    design/src/order.*.txt      an added or removed line counts as the part it names; a moved
                                JS part runs everything (load order), a moved CSS part counts as itself
    design/src/scope.json       a changed entry counts as the css file it names, plus the golden
                                slice of any view its fence dropped; a file leaving `shared` runs everything
    tests/golden/render.json    a changed state counts as its golden area (area_of)

A key, part or entry whose file no area owns still runs everything, as before.

Markdown is ignored (docs change no behaviour) except design/DESIGN.md: a renamed section breaks
the collection of every test whose `req` marker names it, so the `designdoc` area runs test_trace.py.
"""
import argparse
import difflib
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MAP = ROOT / "tests" / "impact.json"
SCOPE = ROOT / "design" / "src" / "scope.json"
CSS_SURFACE = "design/src/css/surface/"
SRC = "design/src/"
CONTENT = SRC + "content.json"
GOLDEN = "tests/golden/render.json"
DESIGN_DOC = "design/DESIGN.md"
ORDERS = {SRC + "order.js.txt": SRC + "js/", SRC + "order.css.txt": SRC + "css/"}


def load():
    return json.loads(MAP.read_text(encoding="utf-8")), json.loads(SCOPE.read_text(encoding="utf-8"))


def area_of(state):
    """The impact area a golden state belongs to (tests/impact.json): its name's first word.
    tests/test_render.py marks its states with this, so the two cannot disagree."""
    first = state.split("-")[0]
    return {"teams": "roster", "profile": "profile"}.get(first, first)


def owner(path, areas):
    """The area whose paths claim this one: a trailing `/` is a directory, anything else a file."""
    for name, area in areas.items():
        if any(path.startswith(p) if p.endswith("/") else path == p for p in area["paths"]):
            return name
    return None


def _json(text):
    return json.loads(text) if text else {}


def changed_entries(old, new):
    """Keys of a flat JSON object whose value was added or changed. A removed key is left out: the
    file that stopped using it is in the same diff, and assemble --check fails on a dangling one."""
    o, n = _json(old), _json(new)
    return sorted(k for k in n if o.get(k) != n[k])


def changed_states(old, new):
    """Golden states added, changed or removed, in either viewport."""
    o, n = _json(old), _json(new)
    out = set()
    for vp in set(o) | set(n):
        a, b = o.get(vp, {}), n.get(vp, {})
        out |= {s for s in set(a) | set(b) if a.get(s) != b.get(s)}
    return sorted(out)


def manifest_lines(text):
    """A manifest's part paths, comments and blanks dropped (assemble.manifest's reading)."""
    return [ln.split("#", 1)[0].strip() for ln in (text or "").splitlines() if ln.split("#", 1)[0].strip()]


def changed_lines(old, new):
    """Manifest lines added, removed or moved. A move reads as a removal and an insertion, so the
    moved part counts; the parts it passed over do not."""
    a, b = manifest_lines(old), manifest_lines(new)
    out = set()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag != "equal":
            out.update(a[i1:i2] + b[j1:j2])
    return sorted(out)


def users_of(keys, read):
    """The design/src files that reference any of these copy keys, by their literal call."""
    if not keys:
        return []
    pats = [re.compile(r'\bt\(\s*"' + re.escape(k) + '"') for k in keys]
    pats += [re.compile(r"\{\{copy:" + re.escape(k) + r"\}\}") for k in keys]
    return sorted(p for p, text in read() if any(r.search(text) for r in pats))


def expand(path, old, new, read):
    """What a shared file's change stands for: (paths, golden areas), or None to run everything."""
    if path == CONTENT:
        return users_of(changed_entries(old, new), read), []
    if path in ORDERS:
        parts = changed_lines(old, new)
        # A JS part that moved changes load order for every part it passed, and any of those can
        # break on a name it now reads before it is declared. A CSS part's order matters only in
        # the views its fence names, so a moved CSS part counts as itself.
        moved = set(parts) & set(manifest_lines(old)) & set(manifest_lines(new))
        if path.endswith("js.txt") and moved:
            return None
        return [ORDERS[path] + rel for rel in parts], []
    if path == SRC + "scope.json":
        o, n = _json(old), _json(new)
        of, nf = o.get("fenced", {}), n.get("fenced", {})
        # A file that leaves `shared` styled every view until now, so every view can change.
        if set(o.get("shared", {})) - set(n.get("shared", {})):
            return None
        rels = set(changed_entries(json.dumps(of), json.dumps(nf))) | (set(of) - set(nf))
        rels |= set(changed_entries(json.dumps(o.get("shared", {})), json.dumps(n.get("shared", {}))))
        # A view a fence no longer names loses that file's styling: its slice has to run too. A
        # fence root that is no golden area (#modal, .navbar) could be anywhere.
        dropped = {v for rel in rels for v in set(of.get(rel, [])) - set(nf.get(rel, []))}
        if any(v[:1] in "#." for v in dropped):
            return None
        return [SRC + "css/" + rel for rel in sorted(rels)], sorted(dropped)
    if path == GOLDEN:
        return [], sorted({area_of(s) for s in changed_states(old, new)})
    return None


def select(paths, cfg=None, scope=None, golden=()):
    if cfg is None:
        cfg, scope = load()
    fenced = {CSS_SURFACE + rel[len("surface/"):]: views for rel, views in scope["fenced"].items()}
    renders = {r for a in cfg["areas"].values() for r in a["render"]}
    files, areas, why = list(cfg["core"]), set(golden), []
    for g in golden:
        if g not in renders:
            why.append(f"golden state area {g} is no impact area's")
    for path in paths:
        if path.endswith(".md") and path != DESIGN_DOC:    # DESIGN.md names the sections `req` cites
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
        # A fence can name views beyond its owner's (the bet slip's CSS also styles Preview).
        areas.update(v for v in fenced.get(path, ()) if v in renders)
    if areas:
        files.append("tests/test_render.py")
    return {"all": bool(why), "why": why, "files": sorted(set(files)), "areas": sorted(areas)}


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


def at(rev, path):
    """A file's text at a revision, or None where it does not exist."""
    out = subprocess.run(["git", "-C", str(ROOT), "show", f"{rev}:{path}"], capture_output=True,
                         text=True, encoding="utf-8", errors="replace")
    return out.stdout if out.returncode == 0 else None


def src_texts():
    for p in sorted((ROOT / SRC).rglob("*")):
        if p.is_file() and p.suffix in (".js", ".html"):
            yield p.relative_to(ROOT).as_posix(), p.read_text(encoding="utf-8")


def on_disk(path):
    p = ROOT / path
    return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else None


def changed(base, worktree=False):
    """The diff's paths and the golden areas it changes, shared files read by what changed in them.

    worktree: the files on disk, uncommitted and untracked ones included, against the fork point
    (scripts/run_tests.py, while working); otherwise HEAD against it (land.ps1, a finished branch)."""
    fork = git("merge-base", base, "HEAD").strip()
    if worktree:
        listed = git("diff", "--no-renames", "--name-only", fork) + \
            git("ls-files", "--others", "--exclude-standard")
        now = on_disk
    else:
        listed = git("diff", "--no-renames", "--name-only", f"{base}...HEAD")
        now = lambda path: at("HEAD", path)
    paths = sorted({p for p in listed.splitlines() if p})
    out, golden = [], set()
    for path in paths:
        got = expand(path, at(fork, path), now(path), src_texts)
        if got is None:
            out.append(path)
        else:
            out += got[0]
            golden.update(got[1])
    return sorted(set(out)), sorted(golden)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--paths", nargs="*")
    ap.add_argument("--worktree", action="store_true", help="the files on disk, not HEAD")
    a = ap.parse_args(argv)
    if a.paths is not None:
        print(json.dumps(select(a.paths)))
    else:
        paths, golden = changed(a.base, a.worktree)
        print(json.dumps(select(paths, golden=golden)))


if __name__ == "__main__":
    sys.exit(main())
