"""The blocks the FourthDown Lab audit added (2026-10-05): LIVE_ACCURACY, LIVE_DST, LIVE_SOS, and (2026-10-06)
LIVE_D_STARTERS, defenses missing starters.

Kept out of build.py, which is over its line budget (tests/test_budgets.py), the way design/startsit_blocks.py
holds Start/Sit's. Each is a cut of one ff-jarvis file; see the cut modules.
"""
from accuracy import live_accuracy, report as accuracy_report
from d_starters import live_d_starters, load_d_starters, report as d_starters_report
from dst import live_dst, report as dst_report
from sos import live_sos, report as sos_report
from sources import load_accuracy, load_dst, load_sos


def add_audit_blocks(blocks, report):
    """Adds the blocks to `blocks` and their lines to the build `report`, in place."""
    blocks["LIVE_ACCURACY"] = live_accuracy(load_accuracy())
    blocks["LIVE_DST"] = live_dst(load_dst())
    blocks["LIVE_SOS"] = live_sos(load_sos())
    blocks["LIVE_D_STARTERS"] = live_d_starters(load_d_starters())
    report += [accuracy_report(blocks["LIVE_ACCURACY"]), dst_report(blocks["LIVE_DST"]), sos_report(blocks["LIVE_SOS"]),
               d_starters_report(blocks["LIVE_D_STARTERS"])]
