"""Start/Sit's three injected blocks, built together (leaf `matchups`), so build.py keeps one line for them.

LIVE_STARTSIT: each position's best spot (design/startsit.py), the board's lead.
LIVE_SSB: the picker and the matchup board, from blocks already built (ranks, schedule, preview).
LIVE_SS3: SMASH, the bold calls and the record (design/startsit_v3.py); no block yet reads as an empty week.
"""
from startsit import live_startsit, report as startsit_report
from startsit_board import live_ssb, report as ssb_report
from startsit_v3 import live_ss3, report as ss3_report
from sources import load_defense, load_expert_ranks, load_startsit, load_startsit_v3, load_status


def add_start_sit(blocks, report, slugify):
    """Adds the three blocks to `blocks` and their summary lines to `report`, both in place."""
    blocks["LIVE_STARTSIT"] = live_startsit(load_startsit(), slugify)
    blocks["LIVE_SSB"] = live_ssb(blocks["LIVE_RANKS"], blocks["LIVE_SCHEDULE"], blocks["LIVE_PREVIEW"],
                                  load_defense(), load_expert_ranks(), slugify, load_status())
    blocks["LIVE_SS3"] = live_ss3(load_startsit_v3(), slugify)
    report += [startsit_report(blocks["LIVE_STARTSIT"]), ssb_report(blocks["LIVE_SSB"]), ss3_report(blocks["LIVE_SS3"])]
