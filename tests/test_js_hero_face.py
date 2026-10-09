"""Home's hero gets a face (ledger #63, David 2026-10-08 "face a"), in Node: data/hero.js dgHeroFace picks the
player a headline is about when the page has his head, else Blip's reaction to the day's job and Claude's call.
What the band draws is tests/test_digest_day.py."""
import pytest

LG = {"ceedee-lamb": "heads/lg/ceedee-lamb.webp"}
SM = {"ceedee-lamb": "heads/ceedee-lamb.webp", "bucky-irving": "heads/bucky-irving.webp"}
TB_DAL = [{"slug": "ceedee-lamb", "n": "CeeDee Lamb", "pos": "WR", "team": "DAL"},
          {"slug": "bucky-irving", "n": "Bucky Irving", "pos": "RB", "team": "TB"},
          {"slug": "marvin-harrison-jr", "n": "Marvin Harrison Jr.", "pos": "WR", "team": "ARI"}]
POSES = ("wince", "flatline", "ko", "sweat", "laugh")


@pytest.fixture(scope="module")
def face(node_js):
    js = node_js("data/hero.js")
    return lambda lead, job="tnf", lg=LG, sm=SM: js("dgHeroFace", lead, job, lg, sm)


def take(head, score=None, winner="DAL"):
    pick = {"winner": winner, **({"score": score} if score else {})}
    return {"head": head, "players": TB_DAL, "pick": pick}


# ---------------------------------------------------------------- a player's face

@pytest.mark.req("Home", ac="a headline about one player shows his face, the 256px head first")
def test_a_lead_about_one_player_shows_his_big_head(face):
    assert face({"slug": "ceedee-lamb", "tone": "go"}) == {"slug": "ceedee-lamb", "src": LG["ceedee-lamb"]}


def test_without_a_big_head_the_small_one_stands_in(face):
    assert face({"slug": "bucky-irving"}) == {"slug": "bucky-irving", "src": SM["bucky-irving"]}


@pytest.mark.req("Home", ac="a take that names one player shows his face")
@pytest.mark.parametrize("head, slug", [
    ("Lamb feasts as Dallas pulls away", "ceedee-lamb"),               # his surname
    ("Bucky Irving keeps Tampa close", "bucky-irving"),                # his full name
])
def test_a_take_naming_one_player_shows_him(face, head, slug):
    assert face({"take": take(head)})["slug"] == slug


def test_a_name_inside_another_word_is_not_a_mention(face):
    assert face({"take": take("Lambeau weather slows both offenses", {"DAL": 24, "TB": 23})}) == {"pose": "sweat"}


def test_a_suffix_does_not_hide_a_surname(face):
    got = face({"take": take("Harrison runs free", {"DAL": 24, "TB": 23})}, sm={"marvin-harrison-jr": "h.webp"})
    assert got == {"slug": "marvin-harrison-jr", "src": "h.webp"}


@pytest.mark.req("Home", ac="two players named, or a player with no head file, is Blip")
@pytest.mark.parametrize("lead", [
    {"take": take("Lamb and Irving trade blows all night", {"DAL": 27, "TB": 24})},  # two players: not one
    {"slug": "nobody-with-a-head", "tone": "", "take": take("x", {"DAL": 27, "TB": 24})},
    {"slug": "ceedee-lamb", "slugs": ["ceedee-lamb", "bucky-irving"], "take": take("x", {"DAL": 27, "TB": 24})},
])
def test_no_single_player_with_a_head_is_blip(face, lead):
    assert face(lead) == {"pose": "sweat"}


# ---------------------------------------------------------------- Blip's pose

@pytest.mark.req("Home", ac="Blip reacts to Claude's call: a close game sweats, a rout laughs")
@pytest.mark.parametrize("score, pose", [
    ({"DAL": 24, "TB": 21}, "sweat"),        # a field goal: as close as a call gets
    ({"DAL": 31, "TB": 17}, "laugh"),        # two scores
    ({"DAL": 27, "TB": 20}, "sweat"),        # between the two: the job's own pose (a game night sweats)
])
def test_claudes_margin_picks_the_pose(face, score, pose):
    assert face({"take": take("Dallas wins", score)}) == {"pose": pose}


def test_a_rout_on_the_job_default_is_still_a_laugh(face):
    assert face({"take": take("Dallas rolls", {"TB": 10, "DAL": 38})}, job="kickoff") == {"pose": "laugh"}


@pytest.mark.req("Home", ac="the lead's tone outranks the call: out is KO, questionable or weather a wince, nothing a flatline")
@pytest.mark.parametrize("tone, pose", [("out", "ko"), ("q", "wince"), ("sky", "wince"), ("quiet", "flatline"),
                                        ("out team", "ko")])
def test_the_leads_tone_picks_the_pose(face, tone, pose):
    assert face({"tone": tone, "take": take("x", {"DAL": 40, "TB": 3})}) == {"pose": pose}


@pytest.mark.req("Home", ac="with no call, the day's job picks the pose")
@pytest.mark.parametrize("job, pose", [("adds", "laugh"), ("usage", "laugh"), ("smash", "laugh"), ("status", "wince"),
                                       ("tnf", "sweat"), ("tonight", "sweat"), ("kickoff", "sweat"), ("", "flatline")])
def test_the_days_job_picks_the_pose_without_a_call(face, job, pose):
    assert face({"tone": "go"}, job=job) == {"pose": pose}


def test_a_winner_with_no_score_is_no_margin(face):
    assert face({"take": take("Dallas wins")}, job="adds") == {"pose": "laugh"}


@pytest.mark.parametrize("job", ["adds", "status", "tnf", "", "nonsense"])
def test_every_pose_is_one_blip_can_draw(face, job):
    assert face({}, job=job)["pose"] in POSES


def test_no_lead_at_all_is_blip(face):
    assert face(None, job="") == {"pose": "flatline"}


# ---------------------------------------------------------------- his club, for the glow behind him

@pytest.fixture(scope="module")
def club(node_js):
    js = node_js("data/hero.js")
    return lambda lead, slug="ceedee-lamb": js("dgHeroTeam", lead, slug)


@pytest.mark.req("Home", ac="the glow behind the face is his club's colour: the lead's club, a live scorer's, else the take's row")
@pytest.mark.parametrize("lead, team", [
    ({"team": "DAL", "live": {"team": "TB"}, "take": take("x")}, "DAL"),      # the lead's own club first
    ({"live": {"n": "CeeDee Lamb", "team": "DAL"}}, "DAL"),                      # a live scorer's
    ({"take": take("Lamb feasts")}, "DAL"),                                      # the take's row for him
    ({"take": {"head": "x", "players": [], "pick": {}}}, ""),                   # no row for him: no club
    ({}, ""),
    (None, ""),
])
def test_the_faces_club_comes_from_the_lead_then_the_take(club, lead, team):
    assert club(lead) == team


def test_the_takes_row_is_his_own_not_the_first(club):
    assert club({"take": take("Irving")}, slug="bucky-irving") == "TB"
