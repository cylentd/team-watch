"""The fixture build carries News's injury report (ledger #95, #100, 2026-10-09): LIVE_NEWS's player fields from
design/news.py and the practice report from tests/fixtures/data/practice_report.json. Kept apart from
tests/test_news_report.py so that file stays a light one the mutation run picks for design/news.py."""
import json
import re

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.req("News", ac="the injury report")]


def live_news(built):
    m = re.search(r"^const LIVE_NEWS = (.*);$", built.fragment, re.M)
    return json.loads(m.group(1).replace("<\\/", "</"))


def test_the_fixture_build_carries_the_practice_report(built):
    news = live_news(built)
    assert news["practice"]["note"] is None
    # tests/fixtures/data/practice_report.json: Higgins DNP all week, Chase Brown LP, DNP, LP.
    assert news["players"]["tee-higgins"]["days"] == {"Wed": "dnp", "Thu": "dnp", "Fri": "dnp"}
    assert news["players"]["chase-brown"]["days"] == {"Wed": "limited", "Thu": "dnp", "Fri": "limited"}


def test_the_fixture_build_carries_the_report(built):
    news = live_news(built)
    first = next(it for it in news["items"] if it["title"].startswith("Chase Brown"))
    assert (first["slug"], first["status"]) == ("chase-brown", "questionable")
    assert news["players"]["chase-brown"]["n"] == "Chase Brown"
