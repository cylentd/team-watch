"""Assemble design/src/ into the page template string that build.py injects data into.

    python design/assemble.py --check            # manifests and files agree, placeholders present
    python design/assemble.py --map              # which part owns which line of the output
    python design/assemble.py --verify FILE      # sha256 of assemble() vs FILE (newline-normalised)
    python design/assemble.py --out FILE         # write the assembled template

The layout, and the rules the checks enforce:

    src/shell.html      the document: head, <style>/*{{css}}*/</style>, static body,
                        <script>/*__HEADS__*/ /*{{js}}*/</script>
    src/order.css.txt   every file under src/css/, one per line, in cascade order
    src/order.js.txt    every file under src/js/, one per line, in load order
    src/css/**          style only
    src/js/**           behaviour only

Concatenation is a byte cut: parts are joined with nothing between them and never re-indented.
The manifests are the single order authority; filenames carry no numbers. A file on disk that
no manifest lists, or a manifest line with no file, fails the build (`check()`), so a part can
neither silently drop out of the page nor silently join it.
"""
import argparse
import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
SHELL = SRC / "shell.html"
KINDS = {"css": SRC / "order.css.txt", "js": SRC / "order.js.txt"}
PLACEHOLDER = {"css": "/*{{css}}*/\n", "js": "/*{{js}}*/\n"}


def manifest(kind):
    """Relative part paths in order. Blank lines and `#` comments are ignored."""
    out = []
    for raw in KINDS[kind].read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            out.append(line)
    return out


def parts(kind):
    return [SRC / kind / rel for rel in manifest(kind)]


def banner(kind, rel):
    return f"/* ── {kind}/{rel} ── */\n"


def concat(kind, banners=False):
    chunks = []
    for rel in manifest(kind):
        if banners:
            chunks.append(banner(kind, rel))
        chunks.append((SRC / kind / rel).read_text(encoding="utf-8"))
    return "".join(chunks)


def check():
    """Every problem that would make the assembled page differ from what the tree says."""
    problems = []
    shell = SHELL.read_text(encoding="utf-8") if SHELL.exists() else ""
    if not SHELL.exists():
        problems.append(f"missing {SHELL.relative_to(ROOT)}")
    for kind, path in KINDS.items():
        if not path.exists():
            problems.append(f"missing {path.relative_to(ROOT)}")
            continue
        listed = manifest(kind)
        seen = set()
        for rel in listed:
            if rel in seen:
                problems.append(f"{kind}: {rel} listed twice")
            seen.add(rel)
            if not (SRC / kind / rel).is_file():
                problems.append(f"{kind}: {rel} listed but no such file")
        on_disk = {p.relative_to(SRC / kind).as_posix()
                   for p in (SRC / kind).rglob("*") if p.is_file()}
        for rel in sorted(on_disk - seen):
            problems.append(f"{kind}: {rel} exists but is not in order.{kind}.txt")
        n = shell.count(PLACEHOLDER[kind])
        if n != 1:
            problems.append(f"shell.html holds {PLACEHOLDER[kind].strip()} {n} times, want 1")
    if shell.count("/*__HEADS__*/") != 1:
        problems.append("shell.html must hold /*__HEADS__*/ exactly once")
    return problems


def assemble(banners=False):
    """The template as one string, LF newlines. Raises if check() finds anything."""
    problems = check()
    if problems:
        raise SystemExit("assemble: " + "; ".join(problems))
    text = SHELL.read_text(encoding="utf-8")
    for kind in KINDS:
        text = text.replace(PLACEHOLDER[kind], concat(kind, banners), 1)
    return text


def line_map(banners=False):
    """(kind/rel, first line, last line) of every part in the assembled output, 1-based."""
    text = SHELL.read_text(encoding="utf-8")
    rows = []
    for kind in KINDS:
        before = text.split(PLACEHOLDER[kind], 1)[0]
        line = before.count("\n") + 1
        for rel in manifest(kind):
            body = (SRC / kind / rel).read_text(encoding="utf-8")
            if banners:
                line += 1
            n = body.count("\n")
            rows.append((f"{kind}/{rel}", line, line + n - 1))
            line += n
        text = text.replace(PLACEHOLDER[kind], concat(kind, banners), 1)
    return rows


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--map", action="store_true")
    ap.add_argument("--verify", metavar="FILE")
    ap.add_argument("--out", metavar="FILE")
    ap.add_argument("--banners", action="store_true", help="prefix each part with an origin comment")
    a = ap.parse_args(argv)

    if a.check or not (a.map or a.verify or a.out):
        problems = check()
        for p in problems:
            print("  " + p)
        print("check: " + ("ok" if not problems else f"{len(problems)} problem(s)"))
        if problems:
            return 1
    if a.map:
        for name, s, e in line_map(a.banners):
            print(f"{s:5d}-{e:<5d} {e - s + 1:4d}  {name}")
    if a.verify:
        want = pathlib.Path(a.verify).read_text(encoding="utf-8")
        got = assemble(a.banners)
        ok = sha(want) == sha(got)
        print(f"assemble {sha(got)[:16]}  {a.verify} {sha(want)[:16]}  {'MATCH' if ok else 'DIFFER'}")
        if not ok:
            return 1
    if a.out:
        pathlib.Path(a.out).write_text(assemble(a.banners), encoding="utf-8")
        print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
