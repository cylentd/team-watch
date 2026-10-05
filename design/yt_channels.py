"""Writes api/_yt_channels.json, the table api/clips.py reads (2026-10-05).

    python design/yt_channels.py

The channel ids and which channels refuse an embedded player live in ff-jarvis
(model/clients/youtube_channels.json, youtube_embed.json). The page's function needs each channel's
uploads playlist, which YouTube derives from the channel id: "UC..." becomes "UU...". This joins them
so nobody hand-writes a playlist id. The output is committed and tests/test_yt_channels.py holds it
equal to what this script would write now.

Format: {code: {"uploads": "UU...", "embed": bool}}, codes sorted, NFL included.
"""
import json
import pathlib

# Where design/sources.py looks for the ff-jarvis checkout.
FF_JARVIS = pathlib.Path("C:/Users/David/Github/ff-jarvis")
CLIENTS = FF_JARVIS / "model" / "clients"
OUT = pathlib.Path(__file__).resolve().parent.parent / "api" / "_yt_channels.json"


def table(channels, embed):
    """{code: channel id} and the embed file -> {code: {"uploads", "embed"}}."""
    blocked = set(embed.get("blocked") or [])
    out = {}
    for code in sorted(channels):
        cid = channels[code]
        if not cid.startswith("UC"):
            raise ValueError(f"{code}: {cid!r} is not a channel id (UC...)")
        out[code] = {"uploads": "UU" + cid[2:], "embed": code not in blocked}
    return out


def render(channels, embed):
    return json.dumps(table(channels, embed), indent=1) + "\n"


def from_ff_jarvis():
    """The table as ff-jarvis's two files give it now, as the text the script writes."""
    channels = json.loads((CLIENTS / "youtube_channels.json").read_text(encoding="utf-8"))
    embed = json.loads((CLIENTS / "youtube_embed.json").read_text(encoding="utf-8"))
    return render(channels, embed)


def main():
    OUT.write_text(from_ff_jarvis(), encoding="utf-8", newline="\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
