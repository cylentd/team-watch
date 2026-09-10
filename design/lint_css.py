"""Theme rules, checked in the build rather than in review.

    python design/lint_css.py            # print every finding; exit 1 if any is an error

Each rule is a check, not a preference. A rule with a known backlog runs at `warn` until the
commit that clears the backlog flips it to `error`; a rule at `error` fails `build.py`. The
token triples the rgba rule looks for are read from base/tokens.css, so adding a token there
is enough to have its literal form flagged everywhere else.

Rules:
    hex-outside-tokens     a colour literal anywhere but base/tokens.css
    rgba-token-triple      rgba(r,g,b,...) spelling out a token's own channels
    font-family-literal    font-family not a var() (fonts are tokens too)
    breakpoint             a @media width that is not one of the three the page uses
    inline-colour-in-js    a colour literal inside a style="" attribute in the JS or shell
    duplicate-selector     the same selector defined in two non-responsive parts, unless
                           src/css/_overrides.txt lists it (the cascade is then deliberate)
    token-triple-agrees    every --x-rgb in tokens.css must equal the channels of --x, and
                           every colour token with a hex must have a triple -- catches a token
                           edited in one spot (the hex) and not the other (the triple)
"""
import pathlib
import re
import sys
from collections import namedtuple

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
TOKENS = "base/tokens.css"
BREAKPOINTS = {960, 760, 430}

Finding = namedtuple("Finding", "rule level file line text")

LEVEL = {
    "hex-outside-tokens": "error",     # backlog cleared: every hex literal now has a role token
    "rgba-token-triple": "error",      # backlog cleared: every rgba() spelling a token is now rgb(var(--x-rgb) / a)
    "font-family-literal": "error",    # backlog cleared: surface/pool/pool.css literals are now var(--mono/--ui/--disp)
    "breakpoint": "error",
    "inline-colour-in-js": "error",
    "duplicate-selector": "error",     # zero today; a new one names itself in src/css/_overrides.txt or splits
    "token-triple-agrees": "error",    # a drifted or missing triple is a build-breaking typo, not a style choice
}

HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RGBA = re.compile(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)")
FONT = re.compile(r"font-family\s*:\s*([^;}]+)")
MEDIA = re.compile(r"@media[^{]*\((?:max|min)-width\s*:\s*(\d+)px")
STYLE_ATTR = re.compile(r'style="[^"]*"')
SELECTOR = re.compile(r"^([.#][^{@/]+?)\s*\{", re.M)


def _files(kind):
    return sorted(p for p in (SRC / kind).rglob("*") if p.is_file())


def _rel(path):
    return path.relative_to(SRC).as_posix()


def token_triples(tokens_css):
    """{(r,g,b): '--name'} for every 6-digit hex token."""
    out = {}
    for m in re.finditer(r"(--[\w-]+)\s*:\s*#([0-9a-fA-F]{6})\b", tokens_css):
        h = m.group(2)
        out[(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))] = m.group(1)
    return out


def token_triple_agreement(tokens_css):
    """Findings for a --x-rgb triple that disagrees with --x's own hex, or either half missing.
    Keeps the two spellings of a colour from drifting apart -- edit the hex, forget the triple
    (or the reverse), and the rgb(var(--x-rgb) / a) sites go stale silently otherwise."""
    found = []
    hex_by_name = {}
    for m in re.finditer(r"(--[\w-]+)\s*:\s*#([0-9a-fA-F]{6})\b", tokens_css):
        name, h = m.group(1), m.group(2)
        hex_by_name[name] = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    rgb_by_name = {}
    for m in re.finditer(r"(--[\w-]+)-rgb\s*:\s*([^;}]+)[;}]", tokens_css):
        name = m.group(1)
        parts = m.group(2).split()
        try:
            rgb_by_name[name] = tuple(int(p) for p in parts)
        except ValueError:
            continue
    for name, hexval in hex_by_name.items():
        if name not in rgb_by_name:
            found.append(Finding("token-triple-agrees", LEVEL["token-triple-agrees"], TOKENS, 0,
                                 f"{name} has a hex but no {name}-rgb triple"))
        elif rgb_by_name[name] != hexval:
            found.append(Finding("token-triple-agrees", LEVEL["token-triple-agrees"], TOKENS, 0,
                                 f"{name}-rgb {rgb_by_name[name]} disagrees with {name} #{'%02x%02x%02x' % hexval}"))
    for name in rgb_by_name:
        if name not in hex_by_name:
            found.append(Finding("token-triple-agrees", LEVEL["token-triple-agrees"], TOKENS, 0,
                                 f"{name}-rgb has no matching {name} hex token"))
    return found


def lint_css_text(rel, text, triples):
    """Findings for one CSS part. Pure, so the tests can feed it snippets."""
    found = []
    is_tokens = rel == TOKENS
    for n, line in enumerate(text.split("\n"), 1):
        code = re.sub(r"/\*.*?\*/", "", line)          # a hex in a comment is prose
        code = re.sub(r"url\([^)]*\)", "url()", code)  # a data: URI is not a colour
        if not is_tokens:
            for m in HEX.finditer(code):
                found.append(Finding("hex-outside-tokens", LEVEL["hex-outside-tokens"], rel, n, m.group(0)))
            for m in RGBA.finditer(code):
                trip = tuple(int(x) for x in m.groups())
                if trip in triples:
                    found.append(Finding("rgba-token-triple", LEVEL["rgba-token-triple"], rel, n,
                                         f"{m.group(0)}...) is {triples[trip]}"))
            for m in FONT.finditer(code):
                if not m.group(1).strip().startswith("var("):
                    found.append(Finding("font-family-literal", LEVEL["font-family-literal"], rel, n, m.group(1).strip()))
        for m in MEDIA.finditer(code):
            if int(m.group(1)) not in BREAKPOINTS:
                found.append(Finding("breakpoint", LEVEL["breakpoint"], rel, n, f"{m.group(1)}px"))
    return found


def lint_inline(rel, text):
    """A colour literal inside style="" in JS template literals or the shell."""
    found = []
    for n, line in enumerate(text.split("\n"), 1):
        for m in STYLE_ATTR.finditer(line):
            if HEX.search(m.group(0)) or RGBA.search(m.group(0)):
                found.append(Finding("inline-colour-in-js", LEVEL["inline-colour-in-js"], rel, n, m.group(0)[:60]))
    return found


def duplicate_selectors(parts, acknowledged):
    """(selector, [parts]) for selectors defined in more than one non-responsive part."""
    where = {}
    for rel, text in parts:
        if rel.startswith("responsive/"):
            continue
        for m in SELECTOR.finditer(text):
            sel = re.sub(r"\s+", " ", m.group(1).strip())
            where.setdefault(sel, [])
            if rel not in where[sel]:
                where[sel].append(rel)
    return [(sel, files) for sel, files in sorted(where.items())
            if len(files) > 1 and sel not in acknowledged]


def lint(src=SRC):
    tokens_path = src / "css" / TOKENS
    tokens_text = tokens_path.read_text(encoding="utf-8") if tokens_path.exists() else ""
    triples = token_triples(tokens_text)
    css = [(p.relative_to(src).as_posix().split("/", 1)[1], p.read_text(encoding="utf-8"))
           for p in sorted(q for q in (src / "css").rglob("*.css"))]
    found = token_triple_agreement(tokens_text)
    for rel, text in css:
        found += lint_css_text(rel, text, triples)
    for p in sorted(q for q in (src / "js").rglob("*.js")) + [src / "shell.html"]:
        found += lint_inline(p.relative_to(src).as_posix(), p.read_text(encoding="utf-8"))
    ack_path = src / "css" / "_overrides.txt"
    acknowledged = set()
    if ack_path.exists():
        acknowledged = {l.split("#", 1)[0].strip() for l in ack_path.read_text(encoding="utf-8").splitlines()}
        acknowledged.discard("")
    for sel, files in duplicate_selectors(css, acknowledged):
        found.append(Finding("duplicate-selector", LEVEL["duplicate-selector"], files[-1], 0,
                             f"{sel}  also in {', '.join(files[:-1])}"))
    return found


def errors(findings):
    return [f for f in findings if f.level == "error"]


def main():
    found = lint()
    for f in found:
        print(f"{f.level:5s} {f.rule:22s} {f.file}:{f.line}  {f.text}")
    n_err, n_warn = len(errors(found)), len(found) - len(errors(found))
    print(f"lint: {n_err} error(s), {n_warn} warning(s)")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
