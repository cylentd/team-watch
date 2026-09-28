"""Fences a view's CSS to the views that use it (2026-09-27).

Every view renders into one page, so a rule in css/surface/league/ could style Waivers, and a
change in one view could break another. assemble.py passes each file under css/surface/ through
fence() with the roots src/scope.json lists for it. Each selector's first element gains
`:where(R, R *)`: it must be the root or sit inside it, so everything after it does too. The
root itself may be the first element (`.modal .lbl` inside `#modal`). `:where()` adds no
specificity, so the cascade is unchanged; unlike @scope it works in every browser since 2021.

    fence(".a .b:hover{x}", ["#modal"]) -> ".a:where(#modal, #modal *) .b:hover{x}"

Rules inside @media, @container, @supports and @starting-style are fenced; @keyframes and
@property bodies are left alone. A leading `body.x ` is skipped and the next element fenced;
a selector that is only the page (`body.x`, `:root`) cannot be fenced, and fence() raises.
"""
import json
import re

DESCEND = ("@media", "@container", "@supports", "@starting-style")
PAGE_PREFIX = re.compile(r"^(?:html|body)[^\s>+~]*\s+")
GLOBAL = re.compile(r"^(html|body|:root)\b")


def roots(names):
    """scope.json's names as selectors: a view's leaf, or an overlay's own selector (`#modal`)."""
    return [n if n[0] in "#." else f'#view[data-view="{n}"]' for n in names]


def load(path):
    """{"fenced": {file: [root names]}, "shared": {file: why it is not fenced}}."""
    return json.loads(path.read_text(encoding="utf-8"))


def _skip(text, i):
    """Index past a comment or string starting at i, else i."""
    if text.startswith("/*", i):
        j = text.find("*/", i + 2)
        return len(text) if j < 0 else j + 2
    if text[i] in "\"'":
        q, j = text[i], i + 1
        while j < len(text) and text[j] != q:
            j += 2 if text[j] == "\\" else 1
        return j + 1
    return i


def _block_end(text, i):
    """Index of the `}` closing the block whose `{` is at i."""
    depth = 0
    while i < len(text):
        k = _skip(text, i)
        if k != i:
            i = k
            continue
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unclosed block")


def split_selectors(prelude):
    """Split a selector list on top-level commas (not inside :is(), :not(), [a=","])."""
    out, depth, cur, i = [], 0, "", 0
    while i < len(prelude):
        k = _skip(prelude, i)
        if k != i:
            cur += prelude[i:k]
            i = k
            continue
        c = prelude[i]
        if c in "([":
            depth += 1
        elif c in ")]":
            depth -= 1
        if c == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += c
        i += 1
    out.append(cur)
    return out


def rules(text):
    """Yield (start, end, prelude) for every style rule's prelude span, descending into
    DESCEND at-rules. `start:end` covers the prelude text only, comments included."""
    i, start = 0, 0
    while i < len(text):
        k = _skip(text, i)
        if k != i:
            if text.startswith("/*", i) and not text[start:i].strip():
                start = k          # a leading comment belongs to no prelude
            i = k
            continue
        c = text[i]
        if c == "{":
            prelude = text[start:i]
            end = _block_end(text, i)
            head = prelude.strip()
            if head.startswith("@"):
                if head.split()[0].split("(")[0] in DESCEND:
                    for s, e, p in rules(text[i + 1:end]):
                        yield s + i + 1, e + i + 1, p
            else:
                yield start, i, prelude
            i = start = end + 1
            continue
        if c == ";" or c == "}":
            start = i + 1
        i += 1


def first_compound(sel):
    """Where to attach a condition to the selector's first element: the end of its first
    compound, or before a pseudo-element there (`.a::before` -> before `::`)."""
    depth, i = 0, 0
    while i < len(sel):
        k = _skip(sel, i)
        if k != i:
            i = k
            continue
        c = sel[i]
        if c in "([":
            depth += 1
        elif c in ")]":
            depth -= 1
        elif depth == 0 and (c.isspace() or c in ">+~" or sel.startswith("::", i)):
            return i
        i += 1
    return i


def fence(text, roots):
    """Every style rule's selectors, their first element fenced to `roots`."""
    cond = ":where(" + ", ".join(roots + [r + " *" for r in roots]) + ")"
    out, last = [], 0
    for s, e, prelude in rules(text):
        sels = []
        for sel in split_selectors(prelude):
            lead = sel[:len(sel) - len(sel.lstrip())]
            body = sel.strip()
            m = PAGE_PREFIX.match(body)
            page, body = (m.group(0), body[m.end():]) if m else ("", body)
            if not body or GLOBAL.search(body):
                raise ValueError(f"selector names the page, not a view: {sel.strip()}")
            at = first_compound(body)
            sels.append(lead + page + body[:at] + cond + body[at:])
        out.append(text[last:s])
        out.append(",".join(sels))
        last = e
    out.append(text[last:])
    return "".join(out)
