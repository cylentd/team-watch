from test_draft_receipts import run


def test_romo_five_positive_returns_and_full_class_are_separate():
    result = run("data.draftDetails(draft).finale")["ok"]
    assert [row["name"] for row in result["rows"]] == [
        "M. Wilson", "J. Coker", "K. Monangai", "J. Coleman", "B. Irving"]
    assert [row["gain"] for row in result["rows"]] == ["+23", "+23", "+12", "+10", "+7"]
    assert [row["round"] for row in result["rows"]] == [9, 11, 10, 14, 4]
    assert result["total"] == "+41"
    assert result["rows"][0]["comparison"] == "WR41 → WR18"


def test_each_finale_row_carries_the_players_headshot():
    rows = run("data.draftDetails(draft).finale")["ok"]["rows"]
    assert all(row["slug"] for row in rows)
    assert rows[0]["slug"] == run("draft.picks.find(pick => pick.name.endsWith('Wilson') && pick.team === draft.beats.finale.team).slug")["ok"]


def test_the_film_prints_no_small_print():
    # docs/madden-film-rules.md rules 19 and 20: captions, legends and method lines are cut, not shrunk.
    detail = run("Object.keys((await import('./film-copy.mjs')).FILM_COPY.detail)".replace(
        "./film-copy.mjs", (__import__('test_draft_receipts').ROOT / 'film-copy.mjs').as_uri()))
    assert detail.get("ok") is not None, detail
    assert all((key not in detail['ok']) for key in ['weeklyKey', 'foot', 'returns', 'pick', 'gain', 'now', 'drafted', 'starts', 'points', 'weeks', 'injury']), [key for key in ['weeklyKey', 'foot', 'returns', 'pick', 'gain', 'now', 'drafted', 'starts', 'points', 'weeks', 'injury']]


def test_golden_comparison_includes_draft_price_and_current_rank():
    result = run("data.draftDetails(draft).steal")["ok"]
    assert result["price"] == "WR40"
    assert result["finish"] == "WR7"
    assert result["pick"] == 96
    assert result["gain"] == "+33"


def test_brown_receipt_counts_only_new_owner_starts():
    result = run("data.receiptValues(draft).traded")["ok"]
    assert result["starts"] == 2
    assert result["startPoints"] == "4.2 / 6.3"


def test_nonpositive_unranked_and_other_teams_do_not_enter_the_returns():
    picks = [
        {'team': 1, 'name': 'A Positive', 'pos': 'RB', 'price': 10, 'finish': 8, 'value': 2, 'round': 3},
        {'team': 1, 'name': 'B Negative', 'pos': 'WR', 'price': 10, 'finish': 20, 'value': -10, 'round': 2},
        {'team': 1, 'name': 'C Kicker', 'pos': 'K', 'price': 10, 'finish': 1, 'value': 9, 'round': 12},
        {'team': 2, 'name': 'D Other', 'pos': 'RB', 'price': 10, 'finish': 1, 'value': 9, 'round': 1},
        {'team': 1, 'name': 'E Level', 'pos': 'WR', 'price': 10, 'finish': 10, 'value': 0, 'round': 4},
        {'team': 1, 'name': 'F Unknown', 'pos': 'WR', 'price': 10, 'finish': None, 'value': 5, 'round': 5}]
    rows = run('data.positiveDraftReturns(draft, 1)', {'picks': picks})['ok']
    assert [row['name'] for row in rows] == ['A. Positive']


def test_the_headline_is_a_lower_third_across_the_frame_not_a_side_column():
    # docs/madden-film-rules.md rule 21: the scene takes the full width; the headline sits in a bar at the foot.
    import re
    from test_draft_receipts import ROOT
    css = (ROOT / "film.css").read_text()
    bar = re.search(r"^\.receipt\{([^}]*)\}", css, re.M).group(1)
    sides = set(re.findall(r"(?:^|[;{\s])(top|bottom|left|right):", bar))
    assert sides == {"top", "left", "right"}, bar
    assert "broadcast-column" not in bar
