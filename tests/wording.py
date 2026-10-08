"""The page's own words, for tests (2026-10-07): `words("ranks.head")` is content.json's text for that key.

A test that types a phrase the page shows breaks when the phrase is reworded, though nothing it checks
changed. Read the key instead, so a rewording is a content.json edit and nothing else. (testing skill,
references/design.md, "Coupling".) Named `wording`, not `copy`, so it never shadows the stdlib module.
"""
import json
import pathlib

CONTENT = pathlib.Path(__file__).resolve().parents[1] / "design" / "src" / "content.json"
COPY = json.loads(CONTENT.read_text(encoding="utf-8"))


def words(key):
    """content.json's text for `key`; a KeyError naming the key when it is gone."""
    try:
        return COPY[key]
    except KeyError:
        raise KeyError(f"{key} is not in design/src/content.json") from None
