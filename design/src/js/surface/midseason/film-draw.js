function msFilmDrawRace(player, animated){
  const frames = player.edition.film.frames;
  const span = (MS_FILM.raceEnd - MS_FILM.standingsEnd) / frames.length;
  const elapsed = Math.max(0, MS_STATE.film.time - MS_FILM.standingsEnd);
  const index = animated ? Math.min(frames.length - 1, Math.floor(elapsed / span)) : frames.length - 1;
  const frame = frames[index], previous = frames[Math.max(0, index - 1)];
  const progress = animated ? Math.min(1, (elapsed % span) / Math.min(MS_FILM.raceTween, span)) : 1;
  frame.teams.forEach(team => {
    const before = previous.teams.find(other => other.id === team.id);
    const start = index === 0 ? {total: 0, share: 0, place: team.place} : before;
    const row = player.racers.get(team.id);
    row.root.style.setProperty("--ms-place", start.place + (team.place - start.place) * progress);
    row.bar.style.transform = `scaleX(${start.share + (team.share - start.share) * progress})`;
    row.value.textContent = msPoints(start.total + (team.total - start.total) * progress);
    row.root.classList.toggle("ms-leading", team.place === 0);
  });
  player.root.querySelector("[data-msraceweek]").textContent = t("midseason.week", {week: frame.week});
}

function msFilmButtons(player){
  const state = MS_STATE.film, root = player.root;
  const play = root.querySelector("[data-msplay]");
  const label = state.playing ? t("midseason.film.pause") : state.time >= MS_FILM.duration ? t("midseason.film.replay") : t("midseason.film.play");
  if (play.textContent !== label) play.textContent = label;
  play.setAttribute("aria-pressed", String(state.playing));
  play.disabled = !player.timeline || player.media.matches;
  const status = root.querySelector("[data-msfilmstatus]");
  const note = player.media.matches ? t("midseason.film.reduced") : !player.timeline ? t("midseason.film.unavailable") : state.time >= MS_FILM.duration ? t("midseason.film.finished") : "";
  if (status.textContent !== note) status.textContent = note;
}

function msFilmDraw(player){
  if (MS_STATE.film.player !== player) return;
  const state = MS_STATE.film, root = player.root, moment = msFilmMoment(state.time);
  const scene = player.scenes[moment.scene], theatre = root.querySelector(".ms-theatre");
  const animated = state.started && !player.media.matches;
  if (player.scene !== moment.scene){
    player.scene = moment.scene;
    root.querySelector("#ms-news-title").textContent = scene.title;
    root.querySelectorAll("[data-mscaption]").forEach(caption => {
      const active = Number(caption.dataset.mscaption) === moment.scene;
      caption.classList.toggle("ms-active", active);
      caption.setAttribute("aria-hidden", String(!active));
    });
    root.querySelector("[data-mschapter]").textContent = t("midseason.counter", {n: moment.scene + 1, of: player.scenes.length});
    root.querySelectorAll("[data-mspanel]").forEach(panel => {
      const active = Number(panel.dataset.mspanel) === moment.scene;
      panel.classList.toggle("ms-active", active);
      panel.setAttribute("aria-hidden", String(!active));
    });
    root.querySelector('[data-msstory="-1"]').disabled = moment.scene === 0;
    root.querySelector('[data-msstory="1"]').disabled = moment.scene === player.scenes.length - 1;
  }
  theatre.style.setProperty("--ms-reveal", animated ? state.time / MS_FILM.resultStep : player.edition.through + 1);
  theatre.style.setProperty("--ms-form-progress", animated ? Math.min(1, Math.max(0, state.time - MS_FILM.raceEnd) / MS_FILM.entrance) : 1);
  if (moment.scene === 1) msFilmDrawRace(player, animated);
  const stamp = msFilmTime(state.time) + " / " + msFilmTime(MS_FILM.duration);
  const time = root.querySelector("[data-mstime]");
  if (time.textContent !== stamp) time.textContent = stamp;
  root.querySelector("[data-msseek]").value = Math.round(state.time / MS_FILM.second) * MS_FILM.second;
  msFilmButtons(player);
}
