"""Which tests prove which design section (2026-10-05). Collection only: no browser, a few seconds.

    python scripts/trace.py          # sections with their tests, sections with none, quarantined tests
    python scripts/trace.py --json   # the same as JSON: {"sections": {name: [{"test", "ac"}]}, "untested": [...],
                                     #                    "quarantined": [{"test", "reason", "days"}]}

A test names its section with @pytest.mark.req("Ranks", ac="tiers break where points gap"); the name is a
`## ` heading of design/DESIGN.md up to its first ` (`. tests/conftest.py rejects a name DESIGN.md does not
have, so this report never lists a typo. @pytest.mark.quarantine("2026-10-06 flaky: why") marks a flaky test.
"""
import argparse
import contextlib
import datetime as dt
import io
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DESIGN_MD = ROOT / "design" / "DESIGN.md"


def design_sections(text=None):
    """The `## ` headings of DESIGN.md, in order, each cut at its first ` (`. Fenced code is skipped."""
    text = DESIGN_MD.read_text(encoding="utf-8") if text is None else text
    out, fenced = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced and line.startswith("## "):
            name = line[3:].split(" (")[0].strip()
            if name and name not in out:
                out.append(name)
    return out


def quarantine_days(reason, today=None):
    """Days since the date a quarantine reason starts with (YYYY-MM-DD), or None when it has none."""
    m = re.match(r"\s*(\d{4}-\d{2}-\d{2})", reason or "")
    if not m:
        return None
    try:
        return ((today or dt.date.today()) - dt.date.fromisoformat(m.group(1))).days
    except ValueError:
        return None


class Collector:
    """A pytest plugin that keeps what each collected test says about itself."""

    def __init__(self):
        self.tests = []

    def pytest_collection_finish(self, session):
        for item in session.items:
            reqs = [{"section": m.args[0] if m.args else m.kwargs.get("section"), "ac": m.kwargs.get("ac")}
                    for m in item.iter_markers("req")]
            quarantine = [m.args[0] if m.args else m.kwargs.get("reason", "") for m in item.iter_markers("quarantine")]
            self.tests.append({"test": item.nodeid, "req": reqs, "quarantine": quarantine})


def collect():
    """(tests, exit code, pytest's output): collect tests/ in this process, launching nothing."""
    import pytest
    plugin, out = Collector(), io.StringIO()
    with contextlib.redirect_stdout(out):
        code = pytest.main(["--collect-only", "-q", "-c", str(ROOT / "pytest.ini"), "--rootdir", str(ROOT),
                            str(ROOT / "tests")], plugins=[plugin])
    return plugin.tests, int(code), out.getvalue()


def report(tests, sections, today=None):
    """The three lists the command prints, from collected tests and DESIGN.md's section names."""
    by = {s: [] for s in sections}
    for t in tests:
        for r in t["req"]:
            by.setdefault(r["section"], []).append({"test": t["test"], "ac": r["ac"]})
    quarantined = [{"test": t["test"], "reason": q, "days": quarantine_days(q, today)}
                   for t in tests for q in t["quarantine"]]
    return {"sections": by, "untested": [s for s in sections if not by[s]], "quarantined": quarantined}


def render(rep):
    lines, by = [], rep["sections"]
    tested = [s for s in by if by[s]]
    lines.append(f"{len(tested)} of {len(by)} DESIGN.md sections have a test")
    lines.append("")
    for s in by:
        lines.append(f"{len(by[s]):>4}  {s}")
        for r in by[s]:
            lines.append(f"        {r['test']}" + (f"  [{r['ac']}]" if r["ac"] else ""))
    lines += ["", f"No test ({len(rep['untested'])}): " + (", ".join(rep["untested"]) or "none")]
    q = rep["quarantined"]
    lines += ["", f"Quarantined ({len(q)})"]
    for r in q:
        age = f", {r['days']} days" if r["days"] is not None else ""
        lines.append(f"  {r['test']}  {r['reason']}{age}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", action="store_true", help="machine output")
    args = ap.parse_args(argv)
    tests, code, out = collect()
    if code:    # a bad req, a syntax error in a test file: say so, trace nothing
        print(out[-3000:], file=sys.stderr)
        print(f"collection failed (pytest exit {code})", file=sys.stderr)
        return code
    rep = report(tests, design_sections())
    print(json.dumps(rep, indent=1) if args.json else render(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
