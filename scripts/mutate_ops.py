"""Mutation operators for scripts/mutate.py: which text is code, and every mutant of a line (2026-10-06 split)."""
import random
import re

KEYWORDS = {"return", "typeof", "in", "of", "case", "yield", "function", "import", "print", "and", "or", "not",
            "if", "else", "elif", "lambda", "is", "await", "throw", "delete", "void", "new", "from", "while"}
OPS = re.compile(r"===|!==|==|!=|<=|>=|<<|>>|=>|->|&&|\|\||\+\+|--|\*\*|//|[+\-*/%]=|\*|/|\+|-|<|>")
SWAP = {"===": "!==", "!==": "===", "==": "!=", "!=": "==", "<": "<=", "<=": "<", ">": ">=", ">=": ">",
        "+": "-", "-": "+", "*": "/", "/": "*"}
JS_WORDS = {"true": "false", "false": "true"}
PY_WORDS = {"True": "False", "False": "True", "and": "or", "or": "and"}


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
