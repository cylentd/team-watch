"""The headshot files: where ff-jarvis keeps them and how they are copied beside the built page.

build.py names the page's HEADS maps from HEADS_SRC and calls `write_heads` once per build.
"""
import os
import pathlib

# Pointed elsewhere by env var so a build can run against a pinned snapshot (the regression
# suite) instead of whatever ff-jarvis holds right now. The other input roots (DWR, FEED) live
# in sources.py, which owns every ff-jarvis read; this one only ever feeds write_heads().
HEADS_SRC = pathlib.Path(os.environ.get("TEAM_WATCH_HEADS", "C:/Users/David/Github/ff-jarvis/app/public/heads"))
# Served next to the page, and the prefix of every HEADS url, so the two cannot disagree.
HEADS_DIR = "heads"
# The 256px heads (2026-09-25), which ff-jarvis cuts for its draft board's players only. The
# 96px ones are sharp in a 40px row but blur when a trading card stretches them 2-3x, so the
# cards (HEADS_LG) take the large file where there is one. About 230 players, 1.9 MB.
HEADS_LG = "lg"
HEADS_XL = "xl"   # 512px (2026-09-25); the page's srcset loads it only where 256px blurs (player.js)


def _mirror(src_dir, out):
    """Make <out> hold exactly src_dir's .webp files: copy what changed, drop what is gone."""
    out.mkdir(parents=True, exist_ok=True)
    src = {p.name: p for p in src_dir.glob("*.webp")}
    for stale in out.glob("*.webp"):
        if stale.name not in src:
            stale.unlink()
    for name, p in src.items():
        target = out / name
        data = p.read_bytes()
        if not target.exists() or target.read_bytes() != data:
            target.write_bytes(data)
    return len(src)


def write_heads(dest_root):
    """Mirror HEADS_SRC into <dest_root>/heads/ (and its lg/ and xl/ into heads/lg/, heads/xl/),
    dropping a head ff-jarvis no longer has, so each folder is exactly the set HEADS / HEADS_LG /
    HEADS_XL names. Returns how many 96px heads were written."""
    out = pathlib.Path(dest_root) / HEADS_DIR
    n = _mirror(HEADS_SRC, out)
    for sub in (HEADS_LG, HEADS_XL):
        _mirror(HEADS_SRC / sub, out / sub)
    return n
