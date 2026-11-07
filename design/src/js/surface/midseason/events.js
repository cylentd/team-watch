function msImages(root){
  root.querySelectorAll(".ms-avatar img").forEach(image => {
    image.addEventListener("error", () => image.remove(), {once: true});
    if (image.complete && !image.naturalWidth) image.remove();
  });
}

function msPaint(root, league, edition, id, direction, focus){
  MS_STATE.id = msCurrent(edition, id).id;
  root.querySelector("[data-msbody]").innerHTML = msControlsHTML(league, edition, MS_STATE.id)
    + msStageHTML(league, edition, MS_STATE.id);
  const stage = root.querySelector("[data-msstage]");
  stage.style.setProperty("--ms-direction", direction < 0 ? -1 : 1);
  stage.classList.add("ms-in");
  msImages(root);
  root.querySelector(".ms-status").textContent = msName(league, MS_STATE.id);
  const control = root.querySelector(focus);
  (control && !control.disabled ? control : root.querySelector("[data-msteam]")).focus({preventScroll: true});
}

async function msCopy(root, league, edition){
  const team = msCurrent(edition, MS_STATE.id), [headline, roast, hype] = msWords(team);
  const text = [league.league, t("midseason.through", {week: edition.through}), msName(league, team.id),
    msRecord(team), headline, roast, hype].join("\n\n");
  try {
    await navigator.clipboard.writeText(text);
    root.querySelector(".ms-status").textContent = t("midseason.copied");
  } catch {
    root.querySelector(".ms-status").textContent = t("midseason.copyFailed");
  }
}

function wireMidseason(view){
  const league = LG, edition = msData(league);
  if (!edition) return false;
  const entry = view.querySelector("[data-msopen]");
  if (entry) entry.addEventListener("click", () => {
    MS_STATE.open = true;
    msFilmDispose();
    MS_STATE.film.time = 0;
    MS_STATE.film.started = false;
    MS_STATE.id = lgMineId() || edition.teams[0].id;
    render();
    view.querySelector("[data-msclose]").focus({preventScroll: true});
  });
  const root = view.querySelector("[data-msshow]");
  if (!root) return false;
  msImages(root);
  wireMidseasonFilm(root, league, edition);
  root.addEventListener("change", event => {
    if (event.target.matches("[data-msteam]"))
      msPaint(root, league, edition, Number(event.target.value), 1, "[data-msteam]");
  });
  root.addEventListener("click", event => {
    if (msFilmAction(root, event)) return;
    if (event.target.closest("[data-msreport]")){
      if (MS_STATE.film.player) msFilmPause(MS_STATE.film.player);
      const heading = root.querySelector("#ms-report-title");
      heading.focus({preventScroll: true});
      heading.scrollIntoView({block: "start", behavior: "instant"});
      return;
    }
    const button = event.target.closest("[data-msclose],[data-msstep],[data-mscopy]");
    if (!button) return;
    if (button.hasAttribute("data-msclose")){
      msFilmDispose();
      MS_STATE.open = false;
      render();
      view.querySelector("[data-msopen]").focus({preventScroll: true});
    } else if (button.hasAttribute("data-mscopy")){
      msCopy(root, league, edition);
    } else {
      const direction = Number(button.dataset.msstep), next = msStep(edition, MS_STATE.id, direction);
      msPaint(root, league, edition, next, direction, `[data-msstep="${direction}"]`);
    }
  });
  return true;
}
