"""Inline the ff-jarvis headshots into a self-contained index.html.

template.html holds the design; this replaces the /*__HEADS__*/ token with a
slug -> data-URI map so the page works offline and as a published Artifact.
Run: python design/build.py
"""
import base64
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
HEADS_SRC = pathlib.Path("C:/Users/David/Github/ff-jarvis/app/public/heads")

DWR = pathlib.Path("C:/Users/David/Github/ff-jarvis/data")
ESPN_ROSTERS = DWR / "espn_rosters.json"
YAHOO_ROSTERS = DWR / "league_rosters.json"

SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}

SLUGS = [
    # league-wide pool + builder samples
    "chase-brown", "isaiah-likely", "jalen-coker", "bhayshul-tuten", "blake-corum",
    "braelon-allen", "dylan-sampson", "chig-okonkwo", "brenton-strange",
    "dontayvion-wicks", "jalen-nailor", "adonai-mitchell", "alec-pierce",
    "carnell-tate", "denzel-boston", "devaughn-vele",
    # Yahoo - Chat Take the Wheel
    "derrick-henry", "devon-achane", "rashee-rice", "tetairoa-mcmillan",
    "davante-adams", "jameson-williams", "josh-jacobs", "tony-pollard",
    "courtland-sutton", "matthew-stafford", "xavier-worthy", "deebo-samuel",
    "dallas-goedert",
    # ESPN - Saquon Deez Nuts
    "amonra-st-brown", "cam-skattebo", "tee-higgins", "george-kittle",
    "dk-metcalf", "brock-purdy", "jordan-mason", "jared-goff", "jerry-jeudy",
    "hunter-henry", "najee-harris", "tyrone-tracy",
]


def slugify(name):
    """ESPN display name -> headshot slug, matching ff-jarvis's file naming."""
    cleaned = "".join(c if (c.isalnum() or c == " ") else "" for c in name.lower())
    parts = [p for p in cleaned.split() if p not in SUFFIXES]
    return "-".join(parts)


def live_espn(available):
    """The real ESPN roster, so the mock's structure is never invented."""
    if not ESPN_ROSTERS.exists():
        return None
    d = json.loads(ESPN_ROSTERS.read_text(encoding="utf-8"))
    me = d["me"]
    out = []
    flex = 0
    for p in d["detail"][me]:
        slot = p["slot"]
        if slot == "FLEX":
            flex += 1
            slot = f"FLX{flex}"
        elif slot == "BE":
            slot = "BN"
        slug = slugify(p["name"].replace(" D/ST", ""))
        out.append({
            "n": p["name"].replace(" D/ST", ""),
            "pos": "DST" if p["pos"] == "DEF" else p["pos"],
            "team": p["team"],
            "slot": slot,
            "slug": slug if slug in available else None,
            "status": {"QUESTIONABLE": "Q", "OUT": "OUT"}.get(p.get("status") or "", None),
        })
    return {"name": me, "league": d["league"], "league_id": d["league_id"],
            "updated": d["updated"], "roster": out}


def live_feed():
    """What `python -m model.refresh` last wrote. Drives the status strip, so the page reports
    the real state of each source instead of a hardcoded banner. Only the provenance is taken —
    the payloads stay out of the page until there is something in them."""
    path = REPO / "data" / "feed.json"
    if not path.exists():
        return None
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    usage = (d.get("usage") or {}).get("data") or {}
    market = d.get("market") or {}
    return {
        "generated": d.get("generated"),
        "steps": d.get("steps", []),
        "usage_ready": bool(usage.get("ready")),
        "usage_note": usage.get("note"),
        "pool_size": len(usage.get("pool") or []),
        "fetched": {
            "espn": ((d.get("rosters") or {}).get("espn") or {}).get("fetched"),
            "yahoo": ((d.get("rosters") or {}).get("yahoo") or {}).get("fetched"),
            "props": ((market.get("props") or {}).get("fetched")),
            "dfs": ((market.get("dfs") or {}).get("fetched")),
        },
    }


def live_yahoo(available):
    """Yahoo comes from a website scrape, so it carries no lineup slot or injury status.
    The template infers slots and says so on the page."""
    if not YAHOO_ROSTERS.exists():
        return None
    d = json.loads(YAHOO_ROSTERS.read_text(encoding="utf-8"))
    me = d["me"]
    out = []
    for p in d["detail"][me]:
        slug = slugify(p["name"])
        out.append({
            "n": p["name"],
            "pos": "DST" if p["pos"] in ("DEF", "D/ST") else p["pos"],
            "team": p["team"],
            "slug": slug if slug in available else None,
        })
    return {"name": me, "league": d["league"], "league_id": d["league_id"],
            "updated": d["updated"], "roster": out}


def main():
    available = {p.stem for p in HEADS_SRC.glob("*.webp")}
    live = live_espn(available)
    liveY = live_yahoo(available)

    wanted = list(SLUGS)
    for src in (live, liveY):
        if src:
            wanted += [p["slug"] for p in src["roster"] if p["slug"]]

    heads = {}
    missing = []
    for slug in dict.fromkeys(wanted):
        path = HEADS_SRC / f"{slug}.webp"
        if not path.exists():
            missing.append(slug)
            continue
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        heads[slug] = f"data:image/webp;base64,{b64}"

    injected = (
        "const HEADS = " + json.dumps(heads) + ";\n"
        "const LIVE_ESPN = " + json.dumps(live) + ";\n"
        "const LIVE_YAHOO = " + json.dumps(liveY) + ";\n"
        "const LIVE_FEED = " + json.dumps(live_feed()) + ";"
    )
    tpl = (ROOT / "template.html").read_text(encoding="utf-8")
    body = tpl.replace("/*__HEADS__*/", injected)

    # design/index.html is the fragment the Artifact publisher wants (no doctype/head).
    (ROOT / "index.html").write_text(body, encoding="utf-8")

    # The repo root is what Vercel serves, so that copy is a full HTML document.
    favicon = (
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
        "%3Crect width='32' height='32' fill='%2308080a'/%3E"
        "%3Crect x='11' y='6' width='10' height='20' fill='%23c8ff2e'/%3E%3C/svg%3E"
    )
    head = "\n".join([
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="description" content="Team Watch - roster console for two fantasy football teams.">',
        f'<link rel="icon" href="{favicon}">',
        "<style>html{background:#08080a;color-scheme:dark}body{margin:0}"
        "img{max-width:100%}[hidden]{display:none!important}</style>",
        "</head>",
        "<body>",
    ])
    page = f"{head}\n{body}\n</body>\n</html>\n"
    (REPO / "index.html").write_text(page, encoding="utf-8")

    kb = len(page.encode("utf-8")) / 1024
    print(f"wrote {REPO/'index.html'} and {ROOT/'index.html'} ({kb:.0f} KB), {len(heads)} heads inlined")
    for label, src in (("ESPN", live), ("Yahoo", liveY)):
        if src:
            print(f"{label}: {len(src['roster'])} players, {src['league']}, pulled {src['updated']}")
        else:
            print(f"{label}: no live file, template falls back to its own copy")
    if missing:
        print("no headshot (initials fallback renders):", ", ".join(missing))


if __name__ == "__main__":
    main()
