/* The three drawn blocks on the modal's right side, each a pure function of what it is handed:
   the matchup rank as a strip of every defence, the forecast as icons, and the red-zone split of
   the team's touches. sections.js composes them; nothing here reads a global except the copy.
   The weather icons (wxIcon, wxKind) live in ui/weather.js, shared with the cards and Weather. */

/* Every defence as a cell, easiest on the left, his opponent's lit. */
function rankStripHTML(n, of, cls){
  const cells = Array.from({length: of}, (_, i) => `<i${i + 1 === n ? ` class="me ${cls}"` : ""}></i>`).join("");
  return `<div class="pf-strip"><span class="pf-strip-cells">${cells}</span>
    <span class="pf-strip-ends"><em>${t("profile.matchup.easiest")}</em><em>${t("profile.matchup.toughest")}</em></span></div>`;
}

/* The next game's forecast at whichever stadium it's actually played at -- his own team's when
   he's home, the opponent's when he's away -- as one short line: sky and temperature, wind.
   The sky phrase already carries the rain chance, so no separate percentage. Domes render a
   roof and the word instead; a retractable roof still gets a forecast, with the caveat, since
   whether it's closed is a game-time call this API has no way to know. */
function weatherHTML(prof){
  const nx = prof.next;
  if (typeof LIVE_WEATHER === "undefined" || !LIVE_WEATHER || !nx) return "";
  const w = LIVE_WEATHER.teams[nx.home ? prof.team : nx.opp];
  if (!w) return "";
  if (w.roof === "dome") return `<div class="pf-wx pf-weather"><span class="pf-wx-c">${wxIcon("dome")}<em>${t("profile.weather.dome")}</em></span></div>`;
  if (w.temp_f === null || w.temp_f === undefined) return "";
  const cells = [
    [wxIcon(wxKind(w.short)), t("profile.weather.temp", {n: w.temp_f}), esc(w.short || "")],
    [wxIcon("wind"), esc(w.wind || "—"), w.wind_dir ? t("profile.weather.windFrom", {dir: esc(w.wind_dir)}) : t("profile.weather.wind")],
  ];
  const roof = w.roof === "retractable" ? `<span class="pf-wx-c pf-wx-note">${wxIcon("dome")}<em>${t("profile.weather.retractable")}</em></span>` : "";
  return `<div class="pf-wx pf-weather">${cells.map(([i, v, l]) => `<span class="pf-wx-c">${i}<b>${v}</b><em>${l}</em></span>`).join("")}${roof}</div>`;
}

/* The team's red-zone touches of one kind as a bar: his first, then each named teammate, the
   unnamed rest as bare track. `others` is the profile's red_zone.others; an older profile
   without it still draws his share against the rest. */
function rzSplitHTML(mine, team, others, field, name){
  if (!team) return "";
  const rest = others.filter(o => (o[field] || 0) > 0).sort((a, b) => b[field] - a[field]);
  const named = rest.reduce((s, o) => s + o[field], 0);
  const unnamed = Math.max(0, team - mine - named);
  const seg = (n, cls, title) => n > 0 ? `<i${cls ? ` class="${cls}"` : ""} style="--w:${(100 * n / team).toFixed(1)}%" title="${title}"></i>` : "";
  const bar = seg(mine, "me", `${esc(name)} ${mine}`) + rest.map(o => seg(o[field], "", `${esc(o.n)} ${o[field]}`)).join("");
  const key = [`<b>${shortName(name)} ${mine}</b>`]
    .concat(rest.map(o => `<span>${shortName(o.n)} ${o[field]}</span>`), unnamed ? [`<span>${t("profile.rz.others", {n: unnamed})}</span>`] : []);
  return `<div class="pf-split"><span class="pf-split-bar">${bar}</span><div class="pf-split-key">${key.join("")}</div></div>`;
}
