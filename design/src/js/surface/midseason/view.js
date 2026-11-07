function msEntryHTML(league){
  if (!msData(league)) return "";
  return `<button type="button" class="ms-entry" data-msopen data-testid="midseason-entry">
    <span class="ms-entry-title">${t("midseason.title")}</span>
    <span class="ms-entry-sub">${t("midseason.entry")}</span>
    <span class="ms-entry-watch">${t("midseason.watch")} <span aria-hidden="true">↗</span></span></button>`;
}

function msAvatarHTML(league, id){
  const meta = league.teams.find(team => team.id === id) || {};
  const initials = String(meta.name || "").split(/\s+/).slice(0, 2).map(word => Array.from(word)[0]).join("");
  const image = /^avatars\/[\w./-]+$/.test(meta.avatar || "")
    ? `<img src="${esc(meta.avatar)}" alt="" loading="lazy">` : "";
  return `<div class="ms-avatar" aria-hidden="true"><span>${esc(initials)}</span>${image}</div>`;
}

function msChartHTML(edition, team){
  const max = Math.max(1, edition.max_score);
  const bar = (week, index) => `<div class="ms-week" style="--ms-beat:${index}" title="${esc(t("midseason.chartWeek", {
    week: week.week, points: msPoints(week.points), result: week.result}))}">
    <span class="ms-bar-value">${msPoints(week.points)}</span>
    <span class="ms-track"><span class="ms-bar" style="--ms-score:${week.points / max}"></span></span>
    <span>${t("midseason.week", {week: week.week})}</span><b>${esc(week.result)}</b></div>`;
  return `<section class="ms-chart"><div class="ms-chart-head"><h3>${t("midseason.chart")}</h3>
    <span>${t("midseason.average", {points: msPoints(team.average)})}</span></div>
    <div class="ms-bars" data-testid="midseason-chart" role="img" aria-label="${esc(t("midseason.chartAria", {max: msPoints(max)}) + " "
      + team.weeks.map(week => t("midseason.chartWeek", {week: week.week, points: msPoints(week.points), result: week.result})).join(" "))}">${
      team.weeks.map(bar).join("")}</div></section>`;
}

function msReceiptsHTML(league, edition, team){
  const best = team.best, close = team.closest_win;
  const bestLine = t("midseason.bestLine", {week: best.week, points: msPoints(best.points),
    opponent: esc(msName(league, best.opponent)), against: msPoints(best.against)});
  const closeLine = close ? t("midseason.closeLine", {week: close.week,
    margin: msPoints(close.points - close.against), opponent: esc(msName(league, close.opponent))}) : t("midseason.noWin");
  return `<details class="ms-receipts" data-msreceipts data-testid="midseason-receipts"><summary>${t("midseason.receipts")}</summary>
    <div class="ms-evidence"><div><h3>${t("midseason.best")}</h3><p>${bestLine}</p></div>
    <div><h3>${t("midseason.close")}</h3><p>${closeLine}</p></div>
    <dl class="ms-totals"><div><dt>${t("midseason.points")}</dt><dd>${msPoints(team.pf)}</dd></div>
    <div><dt>${t("midseason.against")}</dt><dd>${msPoints(team.pa)}</dd></div>
    <div><dt>${t("midseason.allplay")}</dt><dd>${team.allplay.join("–")}</dd></div></dl>
    <p class="ms-method">${t("midseason.allplayNote")}</p></div></details>`;
}

function msStageHTML(league, edition, id){
  const team = msCurrent(edition, id), [headline, roast, hype] = msWords(team);
  return `<article class="ms-stage ms-in" data-msstage="${team.id}" data-testid="midseason-stage" aria-labelledby="ms-team-name">
    <div class="ms-stage-head">${msAvatarHTML(league, team.id)}<div class="ms-team-id">
      <p class="ms-angle">${msAngle(team.angle)}</p><h2 id="ms-team-name">${esc(msName(league, team.id))}</h2>
      <dl class="ms-stats"><div><dt>${t("midseason.standing")}</dt><dd>${msRecord(team)}</dd></div>
      <div><dt>${t("midseason.scoring")}</dt><dd>${t("midseason.rank", {rank: team.scoring_rank, of: edition.teams.length})}</dd></div></dl></div></div>
    <div class="ms-story"><div class="ms-script"><h3 class="ms-headline">${esc(headline)}</h3>
      <section class="ms-roast" data-msroast><h4>${t("midseason.roast")}</h4><p>${esc(roast)}</p></section>
      <section class="ms-hype" data-mshype><h4>${t("midseason.hype")}</h4><p>${esc(hype)}</p></section></div>
      <div class="ms-proof">${msChartHTML(edition, team)}${msReceiptsHTML(league, edition, team)}</div></div>
    <div class="ms-lower"><span>${t("midseason.take")}</span><span>${esc(msName(league, team.id))}</span></div></article>`;
}

function msControlsHTML(league, edition, id){
  const current = msCurrent(edition, id), index = edition.teams.indexOf(current);
  const option = team => `<option value="${team.id}"${team.id === current.id ? " selected" : ""}>${esc(msName(league, team.id))}</option>`;
  return `<div class="ms-controls"><label class="ms-picker"><span>${t("midseason.choose")}</span>
    <select data-msteam aria-label="${t("midseason.choose")}">${edition.teams.map(option).join("")}</select></label>
    <div class="ms-step"><button type="button" data-msstep="-1" aria-label="${t("midseason.previous")}"${index === 0 ? " disabled" : ""}>‹</button>
      <span class="ms-counter">${t("midseason.counter", {n: index + 1, of: edition.teams.length})}</span>
      <button type="button" data-msstep="1" aria-label="${t("midseason.next")}"${index === edition.teams.length - 1 ? " disabled" : ""}>›</button></div></div>`;
}

function msPageHTML(league, edition, id){
  const team = msCurrent(edition, id);
  return `<section class="ms" data-msshow data-testid="midseason-show"><div class="ms-topline"><button type="button" class="ms-back" data-msclose>← ${t("midseason.back")}</button>
    <span class="ms-network">TW</span></div>
    <header class="ms-mast"><p>${t("midseason.desk")}</p><h1>${t("midseason.title")}</h1>
      <span class="ms-edition">${edition.season} / ${t("midseason.through", {week: edition.through})}${edition.final ? ` · ${t("midseason.final", {week: edition.target})}` : ""}</span></header>
    ${edition.final ? "" : `<p class="ms-preview">${t("midseason.preview", {week: edition.target})}</p>`}
    ${msNewsHTML(league, edition, MS_STATE.film)}${msReportHTML(league, edition)}
    <section class="ms-film"><h2>${t("midseason.film")}</h2>
    <div data-msbody>${msControlsHTML(league, edition, team.id)}${msStageHTML(league, edition, team.id)}</div></section>
    <footer class="ms-footer"><div><h2>${t("midseason.outro")}</h2><p>${t("midseason.outroSub")}</p></div>
      <button type="button" class="ms-copy" data-mscopy>${t("midseason.copy")}</button><span class="ms-status" role="status"></span>
      <p class="ms-source">${t("midseason.footer", {season: edition.season, week: edition.through})}</p></footer></section>`;
}
