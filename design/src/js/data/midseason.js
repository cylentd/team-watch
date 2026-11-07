const MS_STATE = {open: false, id: null, film: {time: 0, playing: false, started: false, player: null}};
const msData = league => league && league.midseason || null;
const msCurrent = (edition, id) => edition.teams.find(team => team.id === id) || edition.teams[0];
const msName = (league, id) => (league.teams.find(team => team.id === id) || {}).name || "";
const msPoints = value => Number(value).toFixed(2);
const msRecord = team => [team.w, team.l, ...(team.t ? [team.t] : [])].join("–");

function msStep(edition, id, direction){
  const index = edition.teams.indexOf(msCurrent(edition, id));
  return edition.teams[Math.max(0, Math.min(edition.teams.length - 1, index + direction))].id;
}

const msAngle = angle => ({
  leader: t("midseason.angle.leader"), darkhorse: t("midseason.angle.darkhorse"),
  gauntlet: t("midseason.angle.gauntlet"), survivor: t("midseason.angle.survivor"),
  contender: t("midseason.angle.contender"), comeback: t("midseason.angle.comeback"),
})[angle];

function msWords(team){
  const words = {
    [MS_TEAM_IDS.romo]: [t("midseason.team.1.head"), t("midseason.team.1.roast"), t("midseason.team.1.hype")],
    [MS_TEAM_IDS.cooked]: [t("midseason.team.2.head"), t("midseason.team.2.roast"), t("midseason.team.2.hype")],
    [MS_TEAM_IDS.warrenty]: [t("midseason.team.3.head"), t("midseason.team.3.roast"), t("midseason.team.3.hype")],
    [MS_TEAM_IDS.bobo]: [t("midseason.team.4.head"), t("midseason.team.4.roast"), t("midseason.team.4.hype")],
    [MS_TEAM_IDS.gibbs]: [t("midseason.team.5.head"), t("midseason.team.5.roast"), t("midseason.team.5.hype")],
    [MS_TEAM_IDS.aura]: [t("midseason.team.6.head"), t("midseason.team.6.roast"), t("midseason.team.6.hype")],
    [MS_TEAM_IDS.honey]: [t("midseason.team.7.head"), t("midseason.team.7.roast"), t("midseason.team.7.hype")],
    [MS_TEAM_IDS.burrowed]: [t("midseason.team.8.head"), t("midseason.team.8.roast"), t("midseason.team.8.hype")],
    [MS_TEAM_IDS.chat]: [t("midseason.team.9.head"), t("midseason.team.9.roast"), t("midseason.team.9.hype")],
    [MS_TEAM_IDS.jaxon]: [t("midseason.team.10.head"), t("midseason.team.10.roast"), t("midseason.team.10.hype")],
    [MS_TEAM_IDS.lamarley]: [t("midseason.team.11.head"), t("midseason.team.11.roast"), t("midseason.team.11.hype")],
    [MS_TEAM_IDS.sausage]: [t("midseason.team.12.head"), t("midseason.team.12.roast"), t("midseason.team.12.hype")],
  };
  return (words[team.id] || [t("midseason.fallback.head"), t("midseason.fallback.roast"), t("midseason.fallback.hype")])
    .map(text => msFill(team, text));
}

function msFill(team, text){
  const values = {peak: msPoints(team.best.points), week: team.best.week, rank: team.scoring_rank,
    points: msPoints(team.pf), average: msPoints(team.average)};
  return text.replace(/{(\w+)}/g, (_, key) => values[key]);
}

function msReportWords(team){
  const reports = {
    [MS_TEAM_IDS.romo]: t("midseason.team.1.report"), [MS_TEAM_IDS.cooked]: t("midseason.team.2.report"),
    [MS_TEAM_IDS.warrenty]: t("midseason.team.3.report"), [MS_TEAM_IDS.bobo]: t("midseason.team.4.report"),
    [MS_TEAM_IDS.gibbs]: t("midseason.team.5.report"), [MS_TEAM_IDS.aura]: t("midseason.team.6.report"),
    [MS_TEAM_IDS.honey]: t("midseason.team.7.report"), [MS_TEAM_IDS.burrowed]: t("midseason.team.8.report"),
    [MS_TEAM_IDS.chat]: t("midseason.team.9.report"), [MS_TEAM_IDS.jaxon]: t("midseason.team.10.report"),
    [MS_TEAM_IDS.lamarley]: t("midseason.team.11.report"), [MS_TEAM_IDS.sausage]: t("midseason.team.12.report"),
  };
  return msFill(team, reports[team.id] || t("midseason.fallback.hype"));
}

function msReportHeadline(team){
  return ({
    [MS_TEAM_IDS.romo]: t("midseason.team.1.headline"), [MS_TEAM_IDS.cooked]: t("midseason.team.2.headline"),
    [MS_TEAM_IDS.warrenty]: t("midseason.team.3.headline"), [MS_TEAM_IDS.bobo]: t("midseason.team.4.headline"),
    [MS_TEAM_IDS.gibbs]: t("midseason.team.5.headline"), [MS_TEAM_IDS.aura]: t("midseason.team.6.headline"),
    [MS_TEAM_IDS.honey]: t("midseason.team.7.headline"), [MS_TEAM_IDS.burrowed]: t("midseason.team.8.headline"),
    [MS_TEAM_IDS.chat]: t("midseason.team.9.headline"), [MS_TEAM_IDS.jaxon]: t("midseason.team.10.headline"),
    [MS_TEAM_IDS.lamarley]: t("midseason.team.11.headline"), [MS_TEAM_IDS.sausage]: t("midseason.team.12.headline"),
  })[team.id];
}
