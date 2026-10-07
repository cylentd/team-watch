"""Team avatars (design/avatars.py, 2026-10-06, David: "it would make it look A LOT better"): each Yahoo team's own
avatar, downloaded by ff-jarvis (model.season.team_avatars) into its data dir as avatars/<league>/<id>.webp, copied
beside the page by the build, named on each team of the league block (`avatar`, "" with no file), and drawn on the
Recap's lead and game cards and in the shared image. The fixture data holds avatars for Yahoo teams 3 and 9 only."""
import json

from avatars import AVATARS_DIR, avatar_ids, write_avatars
import contract
from league_recap import live_league_yahoo
from conftest import FIXTURES, REPO

read = lambda n: json.loads((FIXTURES / "data" / n).read_text(encoding="utf-8"))
slugify = lambda s: s.lower().replace(" ", "-")


def test_the_ids_with_an_avatar_file_are_the_files_present():
    assert avatar_ids("yahoo") == {3, 9}
    assert avatar_ids("ayo") == set(), "a league with no folder has none"


def test_each_yahoo_team_names_its_avatar_file_or_nothing():
    b = live_league_yahoo(read("yahoo_league.json"), None, None, read("league_rosters.json"), slugify, avatars={3, 9})
    contract.validate("LIVE_LEAGUE_YAHOO", b)
    got = {t["id"]: t["avatar"] for t in b["teams"]}
    assert got == {3: "avatars/yahoo/3.webp", 7: "", 9: "avatars/yahoo/9.webp", 10: ""}
    plain = live_league_yahoo(read("yahoo_league.json"), None, None, read("league_rosters.json"), slugify)
    assert all(t["avatar"] == "" for t in plain["teams"]), "no avatars given, none named"


def test_write_avatars_mirrors_each_leagues_folder_and_drops_what_is_gone(tmp_path):
    stale = tmp_path / AVATARS_DIR / "yahoo"
    stale.mkdir(parents=True)
    (stale / "12.webp").write_bytes(b"old")
    (tmp_path / AVATARS_DIR / "gone").mkdir()
    (tmp_path / AVATARS_DIR / "gone" / "1.webp").write_bytes(b"old")
    n = write_avatars(tmp_path)
    assert n == 2 and sorted(p.name for p in stale.glob("*.webp")) == ["3.webp", "9.webp"]
    assert not (tmp_path / AVATARS_DIR / "gone").exists(), "a league ff-jarvis no longer has leaves the site"


def test_a_team_that_changed_its_avatar_gets_the_new_one(tmp_path):
    # a manager uploads a new picture on Yahoo: ff-jarvis fetches it under the same <id>.webp, and the site's copy follows
    old = tmp_path / AVATARS_DIR / "yahoo" / "3.webp"
    old.parent.mkdir(parents=True)
    old.write_bytes(b"last week's picture")
    write_avatars(tmp_path)
    assert old.read_bytes() == (FIXTURES / "data" / "avatars" / "yahoo" / "3.webp").read_bytes()


def test_the_site_serves_the_avatars_folder():
    # .vercelignore is an allowlist: a folder not named is never uploaded (memory: Bot Protection, 2026-09-30).
    assert f"!{AVATARS_DIR}" in (REPO / ".vercelignore").read_text(encoding="utf-8").split()
# The build's own check that the avatars reach the page lives in test_build.py, with the other injected blocks:
# a file holding a `built` test is passed over by the mutator for a light one (scripts/mutate_tests.py).
