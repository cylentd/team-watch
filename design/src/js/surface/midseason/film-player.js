function msFilmDispose(){
  const player = MS_STATE.film.player;
  MS_STATE.film.playing = false;
  MS_STATE.film.player = null;
  if (!player) return;
  player.frame?.contentWindow?.postMessage({type: "madden-pause"}, location.origin);
  if (player.timeline) player.timeline.cancel();
  player.observer.disconnect();
  player.abort.abort();
}

function msFilmPause(player){
  if (player.frame){
    player.frame.contentWindow?.postMessage({type: "madden-pause"}, location.origin);
    return;
  }
  if (player.timeline) player.timeline.pause();
  MS_STATE.film.playing = false;
  msFilmButtons(player);
}

function msFilmSeek(player, time, preview = false){
  msFilmPause(player);
  MS_STATE.film.started = !preview;
  if (player.timeline) player.timeline.seek(time);
  MS_STATE.film.time = time;
  msFilmDraw(player);
}

function msFilmAction(root, event){
  const button = event.target.closest("[data-msplay],[data-msrestart],[data-msstory]");
  const player = MS_STATE.film.player;
  if (!button || !player || player.root !== root) return false;
  const state = MS_STATE.film;
  if (button.hasAttribute("data-msstory")){
    const next = Math.max(0, Math.min(player.scenes.length - 1, player.scene + Number(button.dataset.msstory)));
    msFilmSeek(player, [0, MS_FILM.standingsEnd, MS_FILM.raceEnd][next], true);
    if (button.disabled) root.querySelector("[data-msreport]")?.focus({preventScroll: true});
  } else if (button.hasAttribute("data-msrestart")){
    msFilmSeek(player, 0, true);
  } else if (state.playing){
    msFilmPause(player);
  } else if (player.timeline && !player.media.matches){
    if (state.time >= MS_FILM.duration) msFilmSeek(player, 0);
    state.started = true;
    state.playing = true;
    player.timeline.play();
    root.querySelector("[data-msnews]").scrollIntoView({block: "start", behavior: "instant"});
    msFilmDraw(player);
  }
  return true;
}

function wireMidseasonFilm(root, league, edition){
  msFilmDispose();
  const frame = root.querySelector("[data-mscinema]");
  if (frame){
    const abort = new AbortController();
    const player = {root, frame, abort, observer: new MutationObserver(() => {
      if (!root.isConnected && MS_STATE.film.player === player) msFilmDispose();
    })};
    MS_STATE.film.player = player;
    player.observer.observe(document.body, {childList: true, subtree: true});
    window.addEventListener("message", event => {
      if (event.origin !== location.origin || event.source !== frame.contentWindow || event.data?.type !== "madden-report") return;
      const id = Number(event.data.team);
      const target = root.querySelector(Number.isInteger(id) && id > 0 && id <= MS_TEAM_COUNT ? `#ms-team-${id}` : "#ms-report-title");
      target?.setAttribute("tabindex", "-1"); target?.focus({preventScroll: true});
      target?.scrollIntoView({block: "start", behavior: "instant"});
    }, {signal: abort.signal});
    return;
  }
  if (!edition.film) return;
  const player = {root, league, edition, scenes: msNewsScenes(league, edition), scene: -1,
    media: matchMedia("(prefers-reduced-motion: reduce)"), abort: new AbortController(), racers: new Map(), timeline: null};
  root.querySelectorAll("[data-msracer]").forEach(row => player.racers.set(Number(row.dataset.msracer), {
    root: row, bar: row.querySelector("[data-msracebar]"), value: row.querySelector("[data-msracevalue]"),
  }));
  MS_STATE.film.player = player;
  const time = MS_STATE.film.time;
  if (typeof anime !== "undefined"){
    player.timeline = anime.createTimeline({autoplay: false, onUpdate: () => msFilmDraw(player),
      onComplete: () => {MS_STATE.film.playing = false; msFilmButtons(player);}})
      .add(MS_STATE.film, {time: [0, MS_FILM.duration], duration: MS_FILM.duration, ease: "linear"}, 0);
    player.timeline.seek(time);
  }
  root.addEventListener("input", event => {
    if (event.target.matches("[data-msseek]")) msFilmSeek(player, Number(event.target.value));
  }, {signal: player.abort.signal});
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) msFilmPause(player);
  }, {signal: player.abort.signal});
  player.media.addEventListener("change", () => {
    msFilmPause(player);
    MS_STATE.film.started = false;
    msFilmDraw(player);
  }, {signal: player.abort.signal});
  player.observer = new MutationObserver(() => {
    if (!root.isConnected && MS_STATE.film.player === player) msFilmDispose();
  });
  player.observer.observe(document.body, {childList: true, subtree: true});
  msFilmDraw(player);
}
