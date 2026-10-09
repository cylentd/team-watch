"""League > Trades, a player's trade page: ff-jarvis's pinned search files, written beside the page (ledger #65, 2026-10-08).

ff-jarvis (model.season.trade_pins, contract trade_pins_schema) writes into its jobs' data folder

    trade_pins/index.json            {"updated", "rules", "leagues": {league: {owner: "<league>/<name>.json"}}}
    trade_pins/<league>/<name>.json  one owner: {"updated", "league", "owner", "players": {key: player + holder},
                                     "offers": [offer, its players by key], "get": {key: [offer index] | {reason}},
                                     "send": {key: {partner: offer index} | {reason}}, "pairs": [{"send": [a, b], "offer": i}]}

36 files, ~4.5 MB, so none is injected: the build checks each where it enters and copies the folder, compact, to
`<repo>/trade_pins/`; the page fetches the index once, then the owner's file the index names (js/surface/finder/tpdata.js), so
our owner slug never has to match theirs. Like trade_offers.json the folder is generated and committed at land.

The shape check is the fields the page reads (js/data/tradepage.js), not ff-jarvis's whole contract: a file that fails it stops
the build before anything is written, the way the offers file does (contract.ContractError). With no index at all nothing is
written and what was there stays, and the page fills a trade page from trade_offers.json.
"""
import json
import pathlib
import re
import shutil

import contract
import leagues
import sources
import trade_offers as to

NAME = "trade_pins"
INDEX = "index.json"
NONE = "Trade pins: none from ff-jarvis, so a player's trade page fills from today's offers"
FILE = r"[A-Za-z0-9][A-Za-z0-9._-]*\.json"      # <name>.json in the league's folder; js/data/tradepage.js TP_PINS_FILE holds the same rule
SIDES = ("send", "get")                           # an offer's player lists, which must hold keys of `players` (and not be empty)
ROOMS = ("drop", "ir_moves")                      # and the lists that may be empty


def listed(x):
    return isinstance(x, list)


def keyed(key, players):
    return isinstance(key, str) and key in players


def reason_ok(entry):
    return isinstance(entry.get("reason"), str) and bool(entry["reason"])


def index_ok(i, n):
    """An offer index: a whole number inside the owner's offers."""
    return to.whole(i) and 0 <= i < n


def index_problems(doc, at="TRADE_PINS index"):
    """Missing or wrong fields of index.json as `TRADE_PINS index.leagues['espn']['Team']`."""
    if not isinstance(doc, dict):
        return [at]
    miss = [at + ".updated"] * (not (isinstance(doc.get("updated"), str) and doc["updated"]))
    lgs = doc.get("leagues")
    if not isinstance(lgs, dict) or not lgs:
        return miss + [at + ".leagues"]
    seen = set()
    for lg, owners in lgs.items():
        if lg not in leagues.KEYS or not isinstance(owners, dict) or not owners:
            miss.append(f"{at}.leagues[{lg!r}]")
            continue
        for owner, path in owners.items():
            ok = isinstance(path, str) and re.fullmatch(f"{re.escape(lg)}/{FILE}", path) and ".." not in path and path not in seen
            if not ok:
                miss.append(f"{at}.leagues[{lg!r}][{owner!r}]: {path!r} is not a file of its own, {lg}/<name>.json")
            seen.add(path if isinstance(path, str) else None)
    return miss


def player_problems(at, p):
    if not isinstance(p, dict):
        return [at]
    miss = [f"{at}.{k}" for k in (*to.PLAYER, "holder") if k not in p]
    if "holder" in p and not (isinstance(p["holder"], str) and p["holder"]):
        miss.append(at + ".holder")
    return miss + to.perceived_problems(at, p)


def offer_problems(at, o, players):
    """One offer: who it is with, its gain, and every list of player keys (each key a player of the file)."""
    if not isinstance(o, dict):
        return [at]
    miss = [at + ".partner"] * (not (isinstance(o.get("partner"), str) and o["partner"]))
    miss += [at + ".gain"] * (not to.number(o.get("gain")))
    their = o.get("their")
    lists = [(f"{at}.{k}", o.get(k), k in SIDES) for k in (*SIDES, *ROOMS)]
    if isinstance(their, dict):
        miss += [at + ".their.gain"] * (not to.number(their.get("gain")))
        lists += [(f"{at}.their.{k}", their.get(k), False) for k in to.THEIR]
    else:
        miss.append(at + ".their")
    for where, keys, needs_one in lists:
        if not listed(keys) or (needs_one and not keys):
            miss.append(where)
            continue
        miss += [f"{where}[{j}]" for j, k in enumerate(keys) if not keyed(k, players)]
    return miss + to.lens_problems(at, o)


def get_problems(at, get, players, n):
    """`get`: player key -> up to a few offer indexes, or {reason}."""
    if not isinstance(get, dict):
        return [at + ".get"]
    miss = []
    for key, entry in get.items():
        here = f"{at}.get[{key!r}]"
        if not keyed(key, players):
            miss.append(here)
        elif isinstance(entry, dict):
            miss += [here] * (not reason_ok(entry))
        elif not listed(entry) or not entry:
            miss.append(here)
        else:
            miss += [f"{here}[{j}]" for j, i in enumerate(entry) if not index_ok(i, n)]
    return miss


def send_problems(at, send, players, n):
    """`send`: player key -> {partner: offer index}, or {reason}."""
    if not isinstance(send, dict):
        return [at + ".send"]
    miss = []
    for key, entry in send.items():
        here = f"{at}.send[{key!r}]"
        if not keyed(key, players) or not isinstance(entry, dict) or not entry:
            miss.append(here)
        elif "reason" in entry:
            miss += [here] * (not reason_ok(entry))
        else:
            miss += [f"{here}[{partner!r}]" for partner, i in entry.items() if not index_ok(i, n)]
    return miss


def pairs_problems(at, pairs, players, n):
    if not listed(pairs):
        return [at + ".pairs"]
    miss = []
    for j, row in enumerate(pairs):
        here = f"{at}.pairs[{j}]"
        row = row if isinstance(row, dict) else {}
        two = listed(row.get("send")) and len(row["send"]) == 2 and all(keyed(k, players) for k in row["send"])
        miss += [here + ".send"] * (not two)
        miss += [here + ".offer"] * (not index_ok(row.get("offer"), n))
    return miss


def owner_problems(doc, at):
    """Missing or wrong fields of one owner's file, `at` the label before each (`TRADE_PINS espn/purdy.json`), at most to.LIMIT
    plus the last offer's."""
    if not isinstance(doc, dict):
        return [at]
    miss = [at + ".keys"] * (set(doc) != {"updated", "league", "owner", "players", "offers", "get", "send", "pairs"})
    miss += [at + ".updated"] * (not (isinstance(doc.get("updated"), str) and doc["updated"]))
    miss += [at + ".league"] * (doc.get("league") not in leagues.KEYS)
    miss += [at + ".owner"] * (not (isinstance(doc.get("owner"), str) and doc["owner"]))
    players, offers = doc.get("players"), doc.get("offers")
    if not isinstance(players, dict) or not players:
        return miss + [at + ".players"]
    for key, p in players.items():
        miss += player_problems(f"{at}.players[{key!r}]", p)
    if not listed(offers):
        return miss + [at + ".offers"]
    for i, o in enumerate(offers):
        miss += offer_problems(f"{at}.offers[{i}]", o, players)
        if len(miss) >= to.LIMIT:
            return miss
    n = len(offers)
    return miss + get_problems(at, doc.get("get"), players, n) + send_problems(at, doc.get("send"), players, n) \
        + pairs_problems(at, doc.get("pairs"), players, n)


def read(path, label):
    """The file's JSON, or a build stop naming it."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise contract.ContractError(f"contract: {label} is missing or is not JSON") from None


def stop(bad):
    if bad:
        raise contract.ContractError("contract: " + ", ".join(bad[:to.LIMIT]) + " missing or wrong")


def text_of(doc):
    return json.dumps(doc, ensure_ascii=False, separators=(",", ":"))


def build(repo, src=None):
    """build.py's one call: check the index and every file it names, then write the folder `<repo>/trade_pins/` whole (a file the
    index no longer lists goes), and return the summary line. `src` is ff-jarvis's trade_pins folder (default: its jobs' data).
    Nothing is written when anything fails the check, and with no index nothing is touched."""
    src = pathlib.Path(src) if src else sources.DWR / NAME
    if not (src / INDEX).is_file():
        return NONE
    index = read(src / INDEX, "TRADE_PINS index")
    stop(index_problems(index))
    docs = {}
    for lg, owners in index["leagues"].items():
        for owner, path in owners.items():
            label = f"TRADE_PINS {path}"
            doc = read(src / path, label)
            bad = owner_problems(doc, label)
            if not bad and (doc["league"], doc["owner"]) != (lg, owner):
                bad = [f"{label} is for {doc['league']}/{doc['owner']}, not {lg}/{owner}"]
            stop(bad)
            docs[path] = text_of(doc)
    out = pathlib.Path(repo) / NAME
    if out.exists():
        shutil.rmtree(out)
    for path, text in {INDEX: text_of(index), **docs}.items():
        (out / path).parent.mkdir(parents=True, exist_ok=True)
        (out / path).write_text(text, encoding="utf-8")
    kb = sum(len(t.encode("utf-8")) for t in docs.values()) / 1024
    owners = ", ".join(f"{lg} {len(o)} owner{'s' if len(o) != 1 else ''}" for lg, o in index["leagues"].items())
    return f"Trade pins: {owners}, updated {index['updated']}; {kb:.0f} KB to {NAME}/"
