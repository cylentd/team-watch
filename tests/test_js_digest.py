"""The Digest's pure functions, in Node (data/digest.js, data/navmap.js; 2026-10-06).

Moved out of tests/test_digest.py, where each one cost a browser and a page load to call a function
that reads no DOM: the short name two players on a team share, where the Recap row ends, and which
tab opens Stats. What the Digest draws from them is tests/test_digest*.py, in the component layer.
"""
import pytest

KICK_MON = "2026-10-06T00:15:00Z"      # Monday 5:15 PM Pacific; Mon or Tue in every zone from UTC-12 to UTC+11


@pytest.fixture
def digest(node_js):
    return node_js("data/digest.js", globals={"LIVE_SCHEDULE": {"games": []}})


@pytest.mark.req("Digest", ac="two players on one team with one short name keep their first names")
def test_two_players_one_team_one_short_name_keep_their_first_names(digest):
    """ATL has Bijan and Brian Robinson (2026-09-29, David: "two B. Robinson on ATL ... confusing"):
    a short form two players on one team share keeps the first name; one on two teams stays short."""
    digest("globalThis.searchIndex = () => [{n: 'Bijan Robinson', slug: 'bijan-robinson', team: 'ATL'},"
           " {n: 'Brian Robinson Jr.', slug: 'brian-robinson', team: 'ATL'},"
           " {n: 'Zed Quill', slug: 'zed-quill', team: 'SF'}, {n: 'Zack Quill', slug: 'zack-quill', team: 'NYJ'}]")
    assert [digest("dgShort", n) for n in ("Bijan Robinson", "Brian Robinson Jr.", "Zed Quill")] == [
        "Bijan Robinson", "Brian Robinson", "Z. Quill"]


@pytest.mark.req("Digest", ac="a short name drops a suffix and keeps a single word whole")
def test_a_short_name_drops_a_suffix_and_a_single_word_stays_whole(digest):
    digest("globalThis.searchIndex = () => []")
    assert [digest("dgShort", n) for n in ("Travis Etienne Jr.", "Michael Pittman Jr", "Jaxon Smith-Njigba", "Kyren Williams", "Ceedee")] == [
        "T. Etienne", "M. Pittman", "J. Smith-Njigba", "K. Williams", "Ceedee"]


@pytest.mark.req("Digest", ac="the Recap row ends at the reader's midnight after the first Wednesday")
def test_the_recap_end_is_thursday_midnight_after_the_weeks_last_kickoff(digest):
    """The end is the reader's own midnight: Thursday 00:00 local, to the minute, after the last kickoff
    and less than four days after it."""
    recap = {"week": 4, "games": [{"kickoff": "2026-10-04T17:00:00Z"}, {"kickoff": KICK_MON}]}
    end = digest("""r => { const e = dgRecapEnd(r), d = new Date(e);
      return [e, d.getDay(), d.getHours(), d.getMinutes(), Math.max(...r.games.map(g => Date.parse(g.kickoff)))]; }""", recap)
    assert end[1:4] == [4, 0, 0]
    assert end[0] > end[4] and end[0] - end[4] < 4 * 86400e3


@pytest.mark.req("Digest", ac="a recap with no kickoff to count from has no end")
def test_a_recap_with_no_kickoff_has_no_end(digest):
    assert digest("dgRecapEnd", {"week": 4, "games": [{"kickoff": None}, {}]}) is None


@pytest.mark.req("Digest", ac="the schedule's kickoffs of the recap's week count too")
def test_the_schedule_counts_when_the_recap_has_no_kickoff(node_js):
    js = node_js("data/digest.js", globals={"LIVE_SCHEDULE": {"games": [{"week": 4, "kickoff": KICK_MON}, {"week": 5, "kickoff": "2026-10-12T17:00:00Z"}]}})
    end = js("r => { const d = new Date(dgRecapEnd(r)); return [d.getDay(), d.getHours(), d.getMinutes()]; }", {"week": 4, "games": [{"kickoff": None}]})
    assert end == [4, 0, 0]


@pytest.mark.req("Navigation: one League group, Stats", ac="Highlights sits in Matchup beside Today")
def test_highlights_sits_in_matchup_beside_today(node_js):
    """David, 2026-10-04: the Digest lost its Highlights section and Stats kept them, first. Since the nav regroup
    (2026-10-08, storyboard draft B) Highlights waits in Matchup, beside Today, until step 2 folds it in as a card."""
    nav = node_js("data/navmap.js")
    assert nav("navGroupOf", "highlights") == nav("navGroupOf", "digest") == "week"


# ------------------------------------------------------------------ the day plan (2026-10-06, Digest by day)
#
# Each Pacific weekday is one job: the banner's kind, its cards in order, the strip's views. Noon Pacific
# (19:00Z) of week 5's days, Sunday 2026-10-04 to Saturday 2026-10-10.

NOON = {"sun": "2026-10-04T19:00:00Z", "mon": "2026-10-05T19:00:00Z", "tue": "2026-10-06T19:00:00Z",
        "wed": "2026-10-07T19:00:00Z", "thu": "2026-10-08T19:00:00Z", "fri": "2026-10-09T19:00:00Z",
        "sat": "2026-10-10T19:00:00Z"}
# David, 2026-10-07: a day of two cards was too thin ("the digest should have more relevant stuff"). Each day
# keeps its job first, then the cards that have data that day, five at most.
PLAN = {"tue": ("adds", ["adds", "gains", "usage"]), "wed": ("usage", ["usage", "gains", "defenses", "adds", "calls"]),
        "thu": ("tnf", ["vegas", "game", "status", "calls"]), "fri": ("status", ["status", "gains", "smash", "weather"]),
        "sat": ("smash", ["smash", "bold", "calls", "weather"]), "sun": ("kickoff", ["need", "now", "weather", "calls"]),
        "mon": ("tonight", ["game", "gains", "calls"])}


@pytest.fixture
def plan(node_js):
    return node_js("data/schedule.js", "data/navmap.js", "data/dayplan.js", "data/digest.js", globals={"LIVE_SCHEDULE": {"games": [], "alias": {"LA": "LAR"}}})


def ms(iso):
    from datetime import datetime
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)


@pytest.mark.req("Digest", ac="each Pacific weekday picks its banner and its cards")
@pytest.mark.parametrize("day", list(NOON))
def test_each_pacific_weekday_picks_its_banner_and_cards(plan, day):
    got = plan("ms => { const p = dgDayPlan(ms); return [p.key, p.banner, p.cards]; }", ms(NOON[day]))
    assert got == [day, *PLAN[day]]


@pytest.mark.req("Digest", ac="the day is Pacific, not the reader's or UTC's")
@pytest.mark.parametrize("iso,day", [("2026-10-07T06:30:00Z", "tue"), ("2026-10-07T07:30:00Z", "wed"),
                                     ("2026-10-09T00:15:00Z", "thu")])
def test_late_evening_pacific_is_still_that_days_plan(plan, iso, day):
    """11:30 PM Tuesday in Los Angeles is already Wednesday in UTC: the Digest still does Tuesday's job."""
    assert plan("ms => dgDayPlan(ms).key", ms(iso)) == day


@pytest.mark.req("Digest", ac="a card with nothing to show is skipped")
def test_a_card_with_nothing_to_show_is_skipped(plan):
    got = plan("""() => { const p = dgDayPlan(Date.parse('2026-10-10T19:00:00Z'));
      return dgDayCards(p, {smash: '', bold: '<b>', calls: '<c>', weather: ''}); }""")
    assert got == ["bold", "calls"]


@pytest.mark.req("Digest", ac="a day whose cards are all empty shows Need to know")
@pytest.mark.parametrize("day", list(NOON))
def test_a_day_whose_cards_are_all_empty_shows_need_to_know(plan, day):
    assert plan("ms => dgDayCards(dgDayPlan(ms), {})", ms(NOON[day])) == ["need"]


@pytest.mark.req("Digest", ac="the strip links the views that are not today's job")
@pytest.mark.parametrize("day", list(NOON))
def test_the_strip_holds_views_and_none_of_todays_cards(plan, day):
    """Every chip is a view the nav can open, at most four, and Recap only while its week is fresh (dgRecap)."""
    fresh, stale = plan("ms => { const p = dgDayPlan(ms); return [dgStripLeaves(p, {recap: true}), dgStripLeaves(p, {recap: false})]; }", ms(NOON[day]))
    assert fresh and len(fresh) <= 4
    assert all(plan("navLeafOf", leaf) == leaf for leaf in fresh), fresh
    assert "digest" not in fresh
    assert "weekrecap" not in stale and [x for x in fresh if x != "weekrecap"] == stale


@pytest.mark.req("Digest", ac="News and Recap became strip links")
def test_news_and_recap_are_strip_links_somewhere_in_the_week(plan):
    leaves = {leaf for d in NOON for leaf in plan("ms => dgStripLeaves(dgDayPlan(ms), {recap: true})", ms(NOON[d]))}
    assert {"news", "weekrecap", "waivers", "matchups", "usage", "schedule"} <= leaves


REC = {"since_week": 5, "weeks": [5], "smash": {"hit": 7, "miss": 3, "void": 0}, "start": {"hit": 2, "miss": 2, "void": 0},
       "sit": {"hit": 4, "miss": 1, "void": 0}}


@pytest.mark.req("Digest", ac="a card of Start/Sit's calls ends in its record and what each call has been through")
def test_a_card_of_start_sit_calls_ends_in_its_record_and_marks(node_js):
    """The foot SMASH, Bold calls and Start in this game share (card.js dgCardRecord): Start/Sit's own numbers,
    then the marks (12.61, 12.73, 12.75; tests/test_flag_marks.py F16). Nothing graded yet says when it starts."""
    card = node_js("data/startsit.js", "surface/digest/card.js")
    foot = card("dgCardRecord", {"record": REC})
    assert foot.startswith("Record since week 5: SMASH 7-3, START 2-2, SIT 4-1.")
    assert "Failed test (12.61, 12.73)" in foot and "Failed test (12.75)" in foot and "Untested" in foot
    empty = {**REC, "weeks": [], **{k: {"hit": 0, "miss": 0, "void": 0} for k in ("smash", "start", "sit")}}
    assert card("dgCardRecord", {"record": empty}).startswith("Record starts with week 5.")
    assert card("dgCardRecord", None) == ""


@pytest.mark.req("Digest", ac="the Start/Sit record foot shows once a day, on the first card of calls that draws")
def test_the_record_foot_is_drawn_once_on_the_first_card_that_asks(node_js):
    card = node_js("data/startsit.js", "surface/digest/card.js")
    ask = "([ctx, id]) => dgRecordFoot(ctx, id)"
    ctx = {"ss3": {"record": REC}, "recordBy": None}
    assert card(ask, [ctx, "smash"]).startswith("Record since week 5")
    assert card("([ctx]) => [dgRecordFoot(ctx, 'smash') === dgRecordFoot(ctx, 'smash'), dgRecordFoot(ctx, 'bold')]", [ctx]) == [True, ""], \
        "the same card draws it again on a repaint; the next card does not"
    assert card(ask, [{"ss3": {"record": None}, "recordBy": None}, "bold"]) == "", "no record, no foot"
    assert card("([ctx]) => { dgRecordFoot(ctx, 'bold'); return ctx.recordBy; }", [{"ss3": {"record": REC}, "recordBy": None}]) == "bold", \
        "a card that does not draw never asks, so the first one that does gets it"


CARD_FILES = ("data/schedule.js", "data/navmap.js", "data/dayplan.js", "data/digest.js", "surface/digest/cards/usage.js",
              "surface/digest/cards/status.js", "surface/digest/cards/adds.js", "surface/digest/cards/defenses.js")


@pytest.fixture
def cards(node_js):
    js = node_js(*CARD_FILES, globals={"LIVE_SCHEDULE": {"games": [], "alias": {"LA": "LAR"}}})
    js("globalThis.searchIndex = () => []")
    return js


@pytest.mark.req("Digest", ac="a share's change is in points of share, with the metric word on the share")
def test_a_usage_change_is_points_of_share_and_the_metric_word_belongs_to_the_share(cards):
    assert cards("dgUsageAnswer", {"now": 78.2, "change": 23, "metric": "snap"}) == {
        "num": "78%", "unit": "snaps", "change": "+23 pts", "dir": "up"}
    assert cards("dgUsageAnswer", {"now": 28, "change": 17, "metric": "tgt_pct"}) == {
        "num": "28%", "unit": "targets", "change": "+17 pts", "dir": "up"}
    assert cards("dgUsageAnswer", {"now": 41, "change": -12, "metric": "snap"})["change"] == "−12 pts"
    mover = {"now": 28, "change": 17, "metric": "tgt_pct"}
    assert cards("([m]) => dgAddsAnswer({}, {}, m)", [mover]) == cards("dgUsageAnswer", mover), "Top adds says it the same way"


@pytest.mark.req("Digest", ac="an injury is shown as the source wrote it")
@pytest.mark.parametrize("text", ["Hip", "Coach's Decision", "ACL", "Undisclosed", "Left hamstring"])
def test_an_injury_keeps_the_sources_capitals(cards, text):
    assert cards("dgInjury", text) == text


@pytest.mark.req("Digest", ac="the Defenses card words its rank through the one allowed-rank function")
def test_the_defense_card_ranks_through_dgallowed(cards):
    rank = "([d, team, pos]) => dgDefRank(d, team, pos)"
    assert cards(rank, [DEF, "DET", "TE"]) == "most", "rank 32 of 32 allows the most"
    assert cards(rank, [DEF, "BUF", "WR"]) == "#2 most", "31 of 32"
    assert cards(rank, [DEF, "LAR", "QB"]) == "#3 most", "30 of 32, the club the page spells LA"


GAINS = [
    {"out": {"slug": "o-wr", "name": "Olu Wide", "team": "CLE", "pos": "WR", "status": "Out"}, "next": {"slug": "the-add", "name": "The Add", "team": "CLE", "pos": "WR"}},
    {"out": {"slug": "o-rb", "name": "Ray Back", "team": "CLE", "pos": "RB", "status": "Doubtful"}, "next": {"slug": "n-rb", "name": "Nick Back", "team": "CLE", "pos": "RB"}},
]


@pytest.mark.req("Digest", ac="an add's reason is his own path: the starter he replaces, never any out player on the team")
def test_an_adds_reason_is_his_own_path(cards):
    reason = "([gains, add]) => dgAddsReason({d: {gains}}, add, null)"
    cle_wr = {"slug": "the-add", "team": "CLE", "pos": "WR"}
    assert cards(reason, [GAINS, cle_wr]) == "O. Wide out", "he is the man next in the gains row"
    other_wr = {"slug": "x-wr", "team": "CLE", "pos": "WR"}
    assert cards(reason, [GAINS, other_wr]) == "O. Wide out", "a gains row at his position on his team"
    cle_te = {"slug": "x-te", "team": "CLE", "pos": "TE"}
    assert cards(reason, [GAINS, cle_te]) == "", "a starter out at another position is not his reason"
    assert cards(reason, [GAINS[1:], cle_wr]) == "", "nor is a back's injury a receiver's"
    assert cards(reason, [GAINS, {"slug": "z", "team": "DEN", "pos": "WR"}]) == "", "another team's"
    assert cards(reason, [GAINS, {"slug": "n", "team": "CLE"}]) == "", "an add with no position matches no one by position"


# ------------------------------------------------------------------ the banner's pick, per day


@pytest.mark.req("Digest", ac="Tuesday's banner is the top add")
def test_tuesdays_banner_is_the_top_add(plan):
    assert plan("dgPickAdd", {"adds": [{"n": "Keon Coleman"}, {"n": "B"}]}) == {"n": "Keon Coleman"}
    assert plan("dgPickAdd", {"adds": []}) is None
    assert plan("dgPickAdd", None) is None


@pytest.mark.req("Digest", ac="Wednesday's banner is the top usage mover, built from his numbers, when the block exists")
def test_wednesdays_banner_is_the_top_usage_mover(plan):
    row = {"slug": "t-mcmillan", "name": "Tetairoa McMillan", "now": 41, "line": "Claude's long line"}
    assert plan("dgPickUsage", {"rows": [row, {"slug": "x", "now": 20}]}) == row
    assert plan("dgPickUsage", None) is None
    assert plan("dgPickUsage", {"rows": []}) is None
    assert plan("dgPickUsage", {"rows": [{"slug": "a", "line": "y"}]}) is None, "a row with no share has no headline"
    bare = {"slug": "b", "now": 30}
    assert plan("dgPickUsage", {"rows": [bare]}) == bare, "the head is the numbers, so a row needs no line"


@pytest.mark.req("Digest", ac="with no usage mover Wednesday's banner is the top row of the Defenses card")
def test_wednesdays_fallback_is_the_defense_card_top_row(plan):
    got = plan("d => { const p = dgPickDefense(d); return p && [p.team, p.pos, p.pts]; }", DEF)
    assert got == ["NYJ", "QB", 25.0], "the first position the card draws, the club allowing it the most"
    assert plan("dgPickDefense", None) is None
    assert plan("dgPickDefense", {"form": {}}) is None
    qb_less = {"form": {"DET": {"current": {"TE": {"pts_pg": 23.8, "rank": 32}}}}}
    assert plan("d => { const p = dgPickDefense(d); return p && [p.team, p.pos]; }", qb_less) == ["DET", "TE"]


PREVIEW = {"games": [
    {"key": "sun", "away": "BUF", "home": "LA", "kickoff": "2026-10-11T17:00:00Z", "take": {"head": "Sunday's", "pick": {"winner": "LA"}}},
    {"key": "tnf", "away": "TB", "home": "DAL", "kickoff": "2026-10-09T00:15:00Z",
     "take": {"head": "Dallas wins, but Tampa's rookie keeps it close", "pick": {"winner": "DAL", "score": {"DAL": 28, "TB": 21}}}}]}


@pytest.mark.req("Digest", ac="Thursday's banner is the Thursday game's preview take")
def test_thursdays_banner_is_the_thursday_games_take(plan):
    """TNF kicks off at 00:15 UTC Friday, 5:15 PM Thursday in Los Angeles: it is Thursday's game."""
    got = plan("([p, ms]) => dgPickTnf(p, ms)", [PREVIEW, ms(NOON["thu"])])
    assert got["key"] == "tnf"
    assert plan("([p, ms]) => dgPickTnf(p, ms)", [PREVIEW, ms(NOON["wed"])]) is None, "no game today"
    no_take = {"games": [{**PREVIEW["games"][1], "take": None}]}
    assert plan("([p, ms]) => dgPickTnf(p, ms)", [no_take, ms(NOON["thu"])]) is None
    assert plan("([p, ms]) => dgPickTnf(p, ms)", [None, ms(NOON["thu"])]) is None
    assert plan("dgTakePick", PREVIEW["games"][1]["take"]) == "DAL 28–21"
    assert plan("dgTakePick", {"pick": {"winner": "DAL"}}) == "DAL"


HURT = [{"slug": "a-qb", "pos": "QB", "rank": 9}, {"slug": "b-wr", "pos": "WR", "rank": 2}, {"slug": "c-rb", "pos": "RB", "rank": 1}]
RANKS = {"rows": [{"slug": "p", "pos": "QB", "rank": 9, "pts": 15.0}, {"slug": "q", "pos": "WR", "rank": 2, "pts": 17.5},
                  {"slug": "r", "pos": "RB", "rank": 1, "pts": 19.0}]}


@pytest.mark.req("Digest", ac="Friday's banner is the hurt player with the highest healthy projection")
def test_fridays_banner_is_the_hurt_row_with_the_highest_projection(plan):
    pick = "([d, r]) => { const x = dgPickStatus(d, r); return x && x.slug; }"
    # no row of his own: the points the list puts at his position and rank
    assert plan(pick, [{"hurt": HURT}, RANKS]) == "c-rb"
    # his own row wins over the one at his rank
    own = {"rows": [*RANKS["rows"], {"slug": "b-wr", "pos": "WR", "rank": 7, "pts": 25.0}]}
    assert plan(pick, [{"hurt": HURT}, own]) == "b-wr"
    assert plan(pick, [{"hurt": []}, RANKS]) is None


@pytest.mark.req("Digest", ac="with no projection Friday's banner is the best-ranked hurt row across positions")
def test_fridays_banner_without_projections_is_the_lowest_rank_number(plan):
    pick = "([d, r]) => { const x = dgPickStatus(d, r); return x && x.slug; }"
    assert plan(pick, [{"hurt": HURT}, None]) == "c-rb", "rank 1 beats rank 2 and 9, whatever the position"
    assert plan(pick, [{"hurt": [{"slug": "x"}, {"slug": "y"}]}, None]) == "x", "no ranks at all: the packet's own first"


SS3 = {"smash": [
    {"slug": "josh-allen", "name": "Josh Allen", "pos": "QB", "opp": "LA", "rank": 1},
    {"slug": "trey-mcbride", "name": "Trey McBride", "pos": "TE", "opp": "DET", "rank": 1},
    {"slug": "puka-nacua", "name": "Puka Nacua", "pos": "WR", "opp": "BUF", "rank": 1}]}
DEF = {"form": {
    "DET": {"current": {"QB": {"pts_pg": 20.1, "rank": 20}, "TE": {"pts_pg": 23.8, "rank": 32}, "WR": {"pts_pg": 30.0, "rank": 25}}},
    "LAR": {"current": {"QB": {"pts_pg": 24.0, "rank": 30}, "TE": {"pts_pg": 5.0, "rank": 1}, "WR": {"pts_pg": 20.0, "rank": 5}}},
    "BUF": {"current": {"QB": {"pts_pg": 12.0, "rank": 1}, "TE": {"pts_pg": 9.0, "rank": 10}, "WR": {"pts_pg": 35.0, "rank": 31}}},
    "NYJ": {"current": {"QB": {"pts_pg": 25.0, "rank": 32}, "TE": {"pts_pg": 8.0, "rank": 9}, "WR": {"pts_pg": 36.0, "rank": 32}}}}}


@pytest.mark.req("Digest", ac="Saturday's banner is the SMASH whose opponent allows the most at his position")
def test_saturdays_banner_is_the_smash_against_the_softest_defense(plan):
    """McBride's DET allows TEs the most of 32 (rank 32 of 32: #1); Nacua's BUF is #2 against WRs; Allen's LA
    (spelled LAR in the defense block) is #3 against QBs."""
    got = plan("([s, d]) => { const p = dgPickSmash(s, d); return [p.row.slug, p.most, p.of, p.allow.pts_pg]; }", [SS3, DEF])
    assert got == ["trey-mcbride", 1, 32, 23.8]
    alone = {"smash": [SS3["smash"][0]]}
    assert plan("([s, d]) => { const p = dgPickSmash(s, d); return [p.row.slug, p.most]; }", [alone, DEF]) == ["josh-allen", 3]


@pytest.mark.req("Digest", ac="Saturday's banner is the SMASH whose opponent allows the most at his position")
def test_saturdays_banner_without_defense_data_is_the_first_smash(plan):
    got = plan("([s, d]) => { const p = dgPickSmash(s, d); return [p.row.slug, p.allow, p.most]; }", [SS3, None])
    assert got == ["josh-allen", None, None]
    assert plan("([s, d]) => dgPickSmash(s, d)", [{"smash": []}, DEF]) is None
    assert plan("([s, d]) => dgPickSmash(s, d)", [None, DEF]) is None


@pytest.mark.req("Digest", ac="one rank for the banner and the SMASH card: the opponent's nth most allowed to a position")
def test_the_allowed_rank_is_the_nth_most_of_the_clubs_ranked_at_the_position(plan):
    """The banner picks by it and the SMASH card words it (cards/smash.js), so both read dgAllowed."""
    got = plan("([d, o, p]) => { const a = dgAllowed(d, o, p); return a && [a.cur.pts_pg, a.most, a.of]; }", [DEF, "DET", "TE"])
    assert got == [23.8, 1, 32]
    assert plan("([d, o, p]) => dgAllowed(d, o, p).most", [DEF, "LA", "QB"]) == 3, "LA is LAR in the defense block"


@pytest.mark.req("Digest", ac="one rank for the banner and the SMASH card: the opponent's nth most allowed to a position")
@pytest.mark.parametrize("args", [[None, "DET", "TE"], [DEF, "XXX", "TE"], [DEF, "", "TE"], [DEF, "DET", "K"]])
def test_the_allowed_rank_is_none_without_a_ranked_club_at_the_position(plan, args):
    """No defense block, an unknown or empty opponent, or a position the block does not rank (K): no rank."""
    assert plan("([d, o, p]) => dgAllowed(d, o, p)", args) is None, args


GAMES = [{"home": "JAX", "away": "PHI", "kickoff": "2026-10-04T13:30:00Z", "final": False},
         {"home": "DAL", "away": "NYJ", "kickoff": "2026-10-04T17:00:00Z", "final": False},
         {"home": "KC", "away": "SF", "kickoff": "2026-10-05T00:20:00Z", "final": False},
         {"home": "LA", "away": "BUF", "kickoff": "2026-10-06T00:15:00Z", "final": False}]


@pytest.mark.req("Digest", ac="Sunday's banner is the first kickoff still to come today")
def test_sundays_banner_is_the_first_kickoff_to_come(plan):
    pick = "([g, ms]) => { const x = dgPickKickoff(g, ms); return x && x.home; }"
    assert plan(pick, [GAMES, ms("2026-10-04T12:00:00Z")]) == "JAX"          # 5 AM Pacific: London first
    assert plan(pick, [GAMES, ms("2026-10-04T14:00:00Z")]) == "DAL"
    assert plan(pick, [GAMES, ms("2026-10-05T01:00:00Z")]) is None             # Sunday night: none left today


@pytest.mark.req("Digest", ac="Monday's banner is tonight's game")
def test_mondays_banner_is_tonights_game(plan):
    pick = "([g, ms]) => { const x = dgPickTonight(g, ms); return x && x.home; }"
    assert plan(pick, [GAMES, ms(NOON["mon"])]) == "LA"                         # 5:15 PM Pacific Monday
    done = [{**g, "final": True} for g in GAMES]
    assert plan(pick, [done, ms(NOON["mon"])]) is None
    assert plan(pick, [GAMES, ms(NOON["tue"])]) is None
