/* Each club's two colours, for the defense support card (surface/teams/cards.js): the card is
   printed in the team's own kit. Data, not design tokens: a club's colours are a fact about the
   club, like its name. nflverse team codes (LA is the Rams); a club missing here gets the page's
   own panel colours. Order is [art and frame, card body]. */
const TEAM_COLOURS = {
  ARI: ["#97233f", "#101010"], ATL: ["#a71930", "#101010"], BAL: ["#241773", "#101010"],
  BUF: ["#00338d", "#c60c30"], CAR: ["#0085ca", "#101820"], CHI: ["#0b162a", "#c83803"],
  CIN: ["#fb4f14", "#101010"], CLE: ["#ff3c00", "#311d00"], DAL: ["#003594", "#869397"],
  DEN: ["#fb4f14", "#002244"], DET: ["#0076b6", "#b0b7bc"], GB:  ["#203731", "#ffb612"],
  HOU: ["#03202f", "#a71930"], IND: ["#002c5f", "#a2aaad"], JAX: ["#006778", "#101820"],
  KC:  ["#e31837", "#ffb81c"], LA:  ["#003594", "#ffa300"], LAC: ["#0080c6", "#ffc20e"],
  LV:  ["#101010", "#a5acaf"], MIA: ["#008e97", "#fc4c02"], MIN: ["#4f2683", "#ffc62f"],
  NE:  ["#002244", "#c60c30"], NO:  ["#d3bc8d", "#101820"], NYG: ["#0b2265", "#a71930"],
  NYJ: ["#125740", "#101010"], PHI: ["#004c54", "#a5acaf"], PIT: ["#ffb612", "#101820"],
  SF:  ["#aa0000", "#b3995d"], SEA: ["#002244", "#69be28"], TB:  ["#d50a0a", "#34302b"],
  TEN: ["#0c2340", "#4b92db"], WAS: ["#5a1414", "#ffb612"],
};

/* Relative luminance of a #rrggbb, 0 dark to 1 light: which ink reads on a team colour. */
function teamLuma(hex){
  const c = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map(v => v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}

/* The style attribute a defense card wears: its two colours and an ink for each that reads on it. */
function teamColourStyle(team){
  const c = TEAM_COLOURS[team];
  if (!c) return "";
  const ink = hex => teamLuma(hex) > 0.35 ? "var(--paper-ink)" : "var(--ink)";
  return `style="--team:${c[0]};--team-2:${c[1]};--on-team:${ink(c[0])};--on-team-2:${ink(c[1])}"`;
}
