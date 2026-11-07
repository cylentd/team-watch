"""Stable data-format and scoring constants used by the Week 8 film contracts."""

SEASON_START_MONTH = 9  # September is the season anchor used by the draft-week calculation.
ISO_DATE_LENGTH = 10  # YYYY-MM-DD portion of archived transaction timestamps.
INJURY_RECEIPT_GAMES = 3  # The approved Week 8 draft receipt records three games.
RECEPTION_POINTS = 0.5  # The league's half-PPR scoring.
ALL_PLAY_TIE_CREDIT = 0.5  # An all-play tie earns half a win.
STANDIN_PLAYER_INDEX = 3  # Player field in the pickups (week, points, slot, player) tuple.
