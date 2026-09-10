"""Assemble design/src/ into the page template string that build.py injects data into.

    python design/assemble.py --check            # manifests and files agree, placeholders present
    python design/assemble.py --map              # which part owns which line of the output
    python design/assemble.py --verify FILE      # sha256 of assemble(banners=False) vs FILE
    python design/assemble.py --out FILE         # write the assembled template

The layout, and the rules the checks enforce:

    src/shell.html      the document: head, <style>/*{{css}}*/</style>, static body,
                        <script>/*__HEADS__*/ /*{{js}}*/</script>, {{copy:key}} in the markup
    src/content.json    every user-facing string, flat "area.component.slot" -> text
    src/order.css.txt   every file under src/css/, one per line, in cascade order
    src/order.js.txt    every file under src/js/, one per line, in load order
    src/css/**          style only
    src/js/**           behaviour only

Concatenation is a byte cut: parts are joined with nothing between them and never re-indented.
By default each part is preceded by a one-line origin banner (`/* ── css/chrome/nav.css ── */`)
so devtools says which file a rule or function came from; `strip_banners()` removes them again
for byte comparisons. The manifests are the single order authority; filenames carry no numbers.
A file on disk that no manifest lists, or a manifest line with no file, fails the build
(`check()`), so a part can neither silently drop out of the page nor silently join it.

Copy is data: content.json is injected as a one-line `const COPY = {...};` above the first JS
part (a `</` inside a value is escaped, so a `<b>` in copy cannot end the <script>), read by
`t("key")` in the JS and by `{{copy:key}}` in shell.html's static markup, which assemble
substitutes HTML-escaped. `check()` fails on a key referenced but missing, and on a key that
exists but nothing references: dead copy is a problem, not a leftover.
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
SHELL = SRC / "shell.html"
CONTENT = SRC / "content.json"
KINDS = {"css": SRC / "order.css.txt", "js": SRC / "order.js.txt"}
PLACEHOLDER = {"css": "/*{{css}}*/\n", "js": "/*{{js}}*/\n"}
COPY_CALL_RE = re.compile(r'\bt\(\s*"([^"\\]+)"')
COPY_SLOT_RE = re.compile(r"\{\{copy:([^{}]+)\}\}")


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


BANNER_RE = re.compile(r"^/\* ── (css|js)/\S+ ── \*/\n", re.M)


def banner(kind, rel):
    return f"/* ── {kind}/{rel} ── */\n"


def strip_banners(text):
    return BANNER_RE.sub("", text)


def content():
    """The copy map: one flat object of "area.component.slot" -> string."""
    return json.loads(CONTENT.read_text(encoding="utf-8"))


def copy_decl():
    """`const COPY = {...};`, one line. `</` is escaped so a `</b>` in copy cannot end <script>."""
    return "const COPY = " + json.dumps(content(), ensure_ascii=False).replace("</", "<\\/") + ";\n"


def html_escape(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def shell_html():
    """shell.html with its {{copy:key}} placeholders substituted, HTML-escaped."""
    copy = content()
    return COPY_SLOT_RE.sub(lambda m: html_escape(copy[m.group(1)]),
                            SHELL.read_text(encoding="utf-8"))


def concat(kind, banners=True):
    chunks = [copy_decl()] if kind == "js" else []
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
    problems += copy_problems(shell)
    return problems


def copy_problems(shell):
    """content.json is a flat str->str map, every t()/{{copy:}} resolves, every key is used."""
    if not CONTENT.exists():
        return [f"missing src/{CONTENT.name}"]
    try:
        copy = json.loads(CONTENT.read_text(encoding="utf-8"))
    except ValueError as e:
        return [f"content.json is not valid JSON: {e}"]
    if not isinstance(copy, dict):
        return ["content.json must be one flat object of key -> string"]
    problems = [f"content.json: {k} is {type(v).__name__}, want a string"
                for k, v in copy.items() if not isinstance(v, str)]
    used = set()
    for path in sorted((SRC / "js").rglob("*.js")):
        rel = path.relative_to(SRC).as_posix()
        for k in COPY_CALL_RE.findall(path.read_text(encoding="utf-8")):
            used.add(k)
            if k not in copy:
                problems.append(f'{rel}: t("{k}") is not a key in content.json')
    for k in COPY_SLOT_RE.findall(shell):
        used.add(k)
        if k not in copy:
            problems.append(f"shell.html: {{{{copy:{k}}}}} is not a key in content.json")
    problems += [f"content.json: {k} is never referenced" for k in sorted(set(copy) - used)]
    return problems


def assemble(banners=True):
    """The template as one string, LF newlines. Raises if check() finds anything."""
    problems = check()
    if problems:
        raise SystemExit("assemble: " + "; ".join(problems))
    text = shell_html()
    for kind in KINDS:
        text = text.replace(PLACEHOLDER[kind], concat(kind, banners), 1)
    return text


def line_map(banners=True):
    """(kind/rel, first line, last line) of every part in the assembled output, 1-based."""
    text = shell_html()
    rows = []
    for kind in KINDS:
        before = text.split(PLACEHOLDER[kind], 1)[0]
        line = before.count("\n") + 1
        if kind == "js":
            line += copy_decl().count("\n")   # the injected COPY shifts every JS part down
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
    ap.add_argument("--banners", action="store_true", help="keep the origin banners in --verify/--out")
    a = ap.parse_args(argv)

    if a.check or not (a.map or a.verify or a.out):
        problems = check()
        for p in problems:
            print("  " + p)
        print("check: " + ("ok" if not problems else f"{len(problems)} problem(s)"))
        if problems:
            return 1
    if a.map:
        for name, s, e in line_map(True):
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
