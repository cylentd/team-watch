# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

David, who manages two 12-team half-PPR leagues (Yahoo "The Madden Curse" and ESPN "We're Big in Japan"),
and his leaguemates, who open the same page and can connect their own ESPN league. A leaguemate does not
know how the ff-jarvis model works, so no page may assume it. A wider audience is expected later and is
undecided (2026-09-25).

## Product Purpose

Team Watch turns the ff-jarvis model's daily data into the few decisions a fantasy manager actually makes:
who to start, who to add, who to drop, what to bet. Success is a manager who opens it, reads for under a
minute, and knows what to do this week.

## Positioning

Every number traces to a named source, and the model's calls carry a public record: ours is graded weekly
against Pitcher List's, on the same rule, and shown even while it trails. Numbers that have not been
backtested say so. Neighbouring apps publish rankings and opinion with no record attached.

## Operating Context

- **Phone, morning:** a quick scan of what changed overnight.
- **Phone, game day:** Sunday before the 10am Pacific lock, setting lineups.
- **Desktop, planning:** Tuesday and Wednesday, waivers, trades, a deeper look.
- **From Discord:** a tap through from the morning `ff-digest` post, which leads with the top news and
  links to the page.

The data refreshes once a day (the morning job) plus the 6:30 and 15:00 page rebuilds; weeks turn on
Tuesday. Waivers clear Wednesday 12am in both leagues.

## Capabilities and Constraints

- One self-contained HTML page on Vercel, built from `design/src` by `design/build.py`; all data inlined.
- Data comes only from the sibling `ff-jarvis` repo; the page computes no model numbers itself.
- Views are grouped: My teams, Players, Bets, Gameday. A "This week" group (the Digest) is decided as
  the new front page, first in the nav, 2026-09-25.
- ESPN scoring is custom (not plain half-PPR); a call for one league never carries to the other.
- Terminology: a **call** is a start or sit; the **record** is the graded season score of calls; a
  number is **not backtested** when ff-jarvis's METHODOLOGY has no passing test for it.

## Evidence on Hand

- The start/sit record since week 1 of 2026 (`ff-jarvis` `data/grades/`), ours vs Pitcher List's.
- Backtest ledger: `ff-jarvis/docs/METHODOLOGY.md`; current truths: `ff-jarvis/docs/FINDINGS.md`.
- No testimonials, users counts, or accuracy claims exist; none may be invented.

## Product Principles

1. **True first, then exciting.** Pages may be bold and lead with what matters, but never oversell. The
   caveat (sample size, "not backtested") lives one tap deeper, never removed.
2. **Usage over points.** Role and volume carry to next week; points alone do not.
3. **Say the decision.** Each view leads with what to do, then the evidence behind it.
4. **Narrative is noise.** A story with no number behind it is labelled as such or left out.
5. **Show the record, including when it loses.**
