"""wording.words: the page's text for a key, read from content.json."""
import pytest

from wording import COPY, words


def test_a_key_gives_the_text_content_json_holds_for_it():
    key = next(iter(COPY))
    assert words(key) == COPY[key]


def test_a_missing_key_fails_naming_the_key():
    with pytest.raises(KeyError, match="no.such.key is not in design/src/content.json"):
        words("no.such.key")
