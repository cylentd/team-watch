"""The blocks the FourthDown Lab audit added (2026-10-05): LIVE_ACCURACY, LIVE_DST, LIVE_SOS, and (2026-10-06)
LIVE_D_STARTERS, defenses missing starters, and LIVE_ROS, the rest-of-season value.

Kept out of build.py, which is over its line budget (tests/test_budgets.py), the way design/startsit_blocks.py
holds Start/Sit's. Each is a cut of one ff-jarvis file; see the cut modules.
"""
from accuracy import live_accuracy, report as accuracy_report
from d_starters import live_d_starters, load_d_starters, report as d_starters_report
from dst import live_dst, report as dst_report
from kdst import live_kdst, load_kdst, report as kdst_report
from player_tags import live_player_tags, load_player_tags, report as player_tags_report
from ros import live_ros, load_ros_compare, load_ros_value, report as ros_report
from sos import live_sos, report as sos_report
from sources import load_accuracy, load_dst, load_sos
from td_research import load_live as load_td_research_block, report as td_research_report
from usage_movers import live_usage_movers, load_usage_movers, report as usage_movers_report


def add_audit_blocks(blocks, report):
    """Adds the blocks to `blocks` and their lines to the build `report`, in place. LIVE_USAGE_MOVERS (2026-10-06,
    the Digest's Usage movers) rides here too: build.py is over its line budget."""
    blocks["LIVE_USAGE_MOVERS"] = live_usage_movers(load_usage_movers())
    report.append(usage_movers_report(blocks["LIVE_USAGE_MOVERS"]))
    blocks["LIVE_ACCURACY"] = live_accuracy(load_accuracy())
    blocks["LIVE_DST"] = live_dst(load_dst())
    blocks["LIVE_KDST"] = live_kdst(load_kdst())
    report.append(kdst_report(blocks["LIVE_KDST"]))
    blocks["LIVE_SOS"] = live_sos(load_sos())
    blocks["LIVE_D_STARTERS"] = live_d_starters(load_d_starters())
    blocks["LIVE_ROS"] = live_ros(load_ros_value(), load_ros_compare())
    blocks["LIVE_PLAYER_TAGS"] = live_player_tags(load_player_tags())   # 2026-10-08, ledger #41
    report.append(player_tags_report(blocks["LIVE_PLAYER_TAGS"]))
    blocks["LIVE_TD_RESEARCH"] = load_td_research_block()   # 2026-10-09, Slips' Anytime TDs card
    report.append(td_research_report(blocks["LIVE_TD_RESEARCH"]))
    report += [accuracy_report(blocks["LIVE_ACCURACY"]), dst_report(blocks["LIVE_DST"]), sos_report(blocks["LIVE_SOS"]),
               d_starters_report(blocks["LIVE_D_STARTERS"]), ros_report(blocks["LIVE_ROS"])]
