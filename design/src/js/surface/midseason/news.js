function msNewsScenes(league, edition){
  const film = edition.film;
  if (!film) return [];
  const lead = msCurrent(edition, film.leaders[0]), surge = film.surge;
  return [
    {title: t("midseason.film.raceTitle"), caption: t("midseason.film.raceCaption", {
      count: film.crowd, leaders: film.leaders.map(id => msName(league, id)).join(t("midseason.film.join")),
      record: msRecord(lead), chase: film.chase.length})},
    {title: t("midseason.film.pointsTitle"), caption: t("midseason.film.pointsCaption", {
      week: edition.through, count: film.top_count, gap: msPoints(film.top_gap)})},
    {title: surge.change > 0 ? t("midseason.film.formTitle") : t("midseason.film.formNeutral"), caption: t("midseason.film.formCaption", {
      team: msName(league, surge.id), change: msPoints(Math.abs(surge.change)), recent: surge.recent_weeks,
      direction: surge.change >= 0 ? t("midseason.film.more") : t("midseason.film.fewer"),
      baseline: surge.baseline_weeks, wins: surge.wins, losses: surge.losses})},
  ];
}

function msFormHTML(league, edition){
  const head = edition.teams[0].weeks.map(week => `<span>${week.week}</span>`).join("");
  const rows = edition.teams.map(team => `<div class="ms-form-row${edition.film.leaders.includes(team.id) ? " ms-front" : ""}">
    <span class="ms-form-name" title="${esc(msName(league, team.id))}">${msAvatarHTML(league, team.id)}<span>${esc(msName(league, team.id))}</span></span>
    <span class="ms-form-weeks">${team.weeks.map(week => `<span class="ms-result ms-result-${week.result}" data-msresult="${week.week}" style="--ms-week:${week.week}"
      title="${esc(t("midseason.chartWeek", {week: week.week, points: msPoints(week.points), result: week.result}))}">${week.result}</span>`).join("")}</span>
    <b>${msRecord(team)}</b></div>`).join("");
  return `<div class="ms-form" style="--ms-weeks:${edition.through}">
    <div class="ms-form-head"><span>${t("midseason.film.team")}</span><span class="ms-form-weeks">${head}</span><span>${t("midseason.film.record")}</span></div>${rows}</div>`;
}

function msRaceHTML(league, edition){
  const last = edition.film.frames.at(-1);
  return `<div class="ms-race"><div class="ms-race-meta"><span>${t("midseason.film.cumulative")}</span>
    <b data-msraceweek>${t("midseason.week", {week: edition.through})}</b></div>
    <div class="ms-racers" style="--ms-count:${edition.teams.length}">${last.teams.map(team => `<div class="ms-racer" data-msracer="${team.id}" style="--ms-place:${team.place}">
      <div class="ms-racer-name">${msAvatarHTML(league, team.id)}<span title="${esc(msName(league, team.id))}">${esc(msName(league, team.id))}</span><b data-msracevalue>${msPoints(team.total)}</b></div>
      <span class="ms-racer-track"><span data-msracebar style="transform:scaleX(${team.share})"></span></span></div>`).join("")}</div>
    <div class="ms-race-axis"><span>0</span><span>${msPoints(edition.film.max_total)}</span></div></div>`;
}

function msSurgeHTML(league, edition){
  const surge = edition.film.surge, maximum = Math.max(1, surge.baseline, surge.recent);
  return `<div class="ms-surge"><div class="ms-surge-team">${msAvatarHTML(league, surge.id)}<h3>${esc(msName(league, surge.id))}</h3></div>
    <div class="ms-surge-number"><strong>${surge.change > 0 ? "+" : ""}${msPoints(surge.change)}</strong><span>${t("midseason.film.formUnit")}</span></div>
    <div class="ms-surge-row"><span>${t("midseason.film.baseline", {weeks: surge.baseline_weeks})}</span><b>${msPoints(surge.baseline)}</b>
      <span class="ms-surge-track"><span style="--ms-share:${surge.baseline / maximum}"></span></span></div>
    <div class="ms-surge-row ms-recent"><span>${t("midseason.film.recent", {weeks: surge.recent_weeks})}</span><b>${msPoints(surge.recent)}</b>
      <span class="ms-surge-track"><span style="--ms-share:${surge.recent / maximum}"></span></span></div></div>`;
}

function msNewsHTML(league, edition, filmState){
  if (edition.final) return `<section class="ms-news ms-show" data-msnews data-testid="midseason-news">
    <iframe data-mscinema src="showcase/madden-curse/?embed&film" title="${esc(t("midseason.show.title"))}" allow="autoplay" loading="lazy"></iframe>
    <button type="button" data-msreport>${t("midseason.report.read")}</button>
    </section>`;
  const scenes = msNewsScenes(league, edition);
  if (!scenes.length) return "";
  const moment = msFilmMoment(filmState.time), scene = scenes[moment.scene];
  const panels = [msFormHTML(league, edition), msRaceHTML(league, edition), msSurgeHTML(league, edition)];
  return `<section class="ms-news" data-msnews data-testid="midseason-news" aria-labelledby="ms-news-title">
    <div class="ms-news-heading"><span>${t("midseason.film.label", {week: edition.through})}</span><span data-mschapter>${t("midseason.counter", {n: moment.scene + 1, of: scenes.length})}</span></div>
    <div class="ms-play-row"><button type="button" data-msplay>${t("midseason.film.play")}</button>
      <span class="ms-time" data-mstime>${msFilmTime(filmState.time)} / ${msFilmTime(MS_FILM.duration)}</span>
      <button type="button" data-msrestart>${t("midseason.film.restart")}</button></div>
    <div class="ms-theatre"><h2 id="ms-news-title">${esc(scene.title)}</h2>
      <div class="ms-panels">${panels.map((html, index) => `<div class="ms-film-panel${index === moment.scene ? " ms-active" : ""}" data-mspanel="${index}" aria-hidden="${index !== moment.scene}">${html}</div>`).join("")}</div>
      <div class="ms-captions" aria-live="polite">${scenes.map((item, index) => `<p class="ms-news-script${index === moment.scene ? " ms-active" : ""}" data-mscaption="${index}" aria-hidden="${index !== moment.scene}">${esc(item.caption)}</p>`).join("")}</div></div>
    <div class="ms-player">
      <input type="range" data-msseek min="0" max="${MS_FILM.duration}" step="${MS_FILM.second}" value="${filmState.time}" aria-label="${t("midseason.film.seek")}">
      <div class="ms-news-controls"><button type="button" data-msstory="-1"${moment.scene === 0 ? " disabled" : ""}>${t("midseason.film.previous")}</button>
      <button type="button" data-msstory="1"${moment.scene === scenes.length - 1 ? " disabled" : ""}>${t("midseason.film.next")}</button>
      </div>
      <span class="ms-film-status" role="status" data-msfilmstatus></span></div></section>`;
}

function msReportHTML(league, edition){
  if (!edition.final) return "";
  const film = edition.film;
  const intro = film ? t("midseason.report.intro", {
    leaders: film.leaders.map(id => msName(league, id)).join(t("midseason.film.join")),
    chase: film.chase.length, gap: msPoints(film.top_gap), count: film.top_count}) : "";
  return `<section class="ms-report" data-testid="midseason-report" aria-labelledby="ms-report-title">
    <header><h2 id="ms-report-title" tabindex="-1">${t("midseason.report.title")}</h2><p class="ms-report-lede">${esc(intro)}</p></header>
    <div class="ms-report-teams">${edition.teams.map(team => `<article id="ms-team-${team.id}">
      <div class="ms-report-name">${msAvatarHTML(league, team.id)}<h3>${esc(msName(league, team.id))}</h3></div>
      <h4>${esc(msReportHeadline(team))}</h4>
      <p>${esc(msReportWords(team))}</p></article>`).join("")}</div>
      <p class="ms-report-source">${t("midseason.report.source")}</p></section>`;
}
