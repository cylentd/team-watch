"""Team avatars (2026-10-06): each Yahoo team's own image, which ff-jarvis's refresh step `team_avatars` keeps in
its data dir as avatars/<league>/<team id>.webp (128px). The build copies the folder beside the page and names a
team's file on the league block (`avatar`); the Recap draws the winner's on the lead and each game card and in
the shared image. Read from sources.DWR, so the test suite's fixture data dir carries its own."""
import pathlib
import shutil

import sources

AVATARS_DIR = "avatars"   # served next to the page, and the prefix of every `avatar` path


def _src():
    return pathlib.Path(sources.DWR) / AVATARS_DIR


def avatar_ids(key):
    """The team ids of one league that have an avatar file."""
    return {int(p.stem) for p in (_src() / key).glob("*.webp") if p.stem.isdigit()}


def avatar_path(key, tid):
    return f"{AVATARS_DIR}/{key}/{tid}.webp"


def write_avatars(dest_root):
    """Make <dest_root>/avatars/ hold exactly ff-jarvis's league folders and their .webp files: copy what changed,
    drop a file or a league that is gone. Returns how many files are there."""
    out, src = pathlib.Path(dest_root) / AVATARS_DIR, _src()
    out.mkdir(parents=True, exist_ok=True)
    leagues = {p.name for p in src.iterdir() if p.is_dir()} if src.exists() else set()
    for gone in (p for p in out.iterdir() if p.is_dir() and p.name not in leagues):
        shutil.rmtree(gone)
    n = 0
    for key in sorted(leagues):
        dst, files = out / key, {p.name: p for p in (src / key).glob("*.webp")}
        dst.mkdir(exist_ok=True)
        for stale in dst.glob("*.webp"):
            if stale.name not in files:
                stale.unlink()
        for name, p in files.items():
            data = p.read_bytes()
            if not (dst / name).exists() or (dst / name).read_bytes() != data:
                (dst / name).write_bytes(data)
        n += len(files)
    return n
