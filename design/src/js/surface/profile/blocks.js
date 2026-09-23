/* The three drawn blocks on the modal's right side, each a pure function of what it is handed:
   the matchup rank as a strip of every defence, the forecast as icons, and the red-zone split of
   the team's touches. sections.js composes them; nothing here reads a global except the copy. */

/* Every defence as a cell, easiest on the left, his opponent's lit. */
function rankStripHTML(n, of, cls){
  const cells = Array.from({length: of}, (_, i) => `<i${i + 1 === n ? ` class="me ${cls}"` : ""}></i>`).join("");
  return `<div class="pf-strip"><span class="pf-strip-cells">${cells}</span>
    <span class="pf-strip-ends"><em>${t("profile.matchup.easiest")}</em><em>${t("profile.matchup.toughest")}</em></span></div>`;
}

const WX_ICONS = {
  sun: `<circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1"/>`,
  cloud: `<path d="M7 18a4 4 0 0 1-.6-7.95A6 6 0 0 1 18 9.5 3.5 3.5 0 0 1 17.5 18Z"/>`,
  rain: `<path d="M7 15a4 4 0 0 1-.6-7.95A6 6 0 0 1 18 6.5 3.5 3.5 0 0 1 17.5 15Z"/><path d="M8 18l-1 3M12 18l-1 3M16 18l-1 3"/>`,
  snow: `<path d="M7 15a4 4 0 0 1-.6-7.95A6 6 0 0 1 18 6.5 3.5 3.5 0 0 1 17.5 15Z"/><path d="M8 18v3M12 18v3M16 18v3M6.5 19.5h3M10.5 19.5h3M14.5 19.5h3"/>`,
  wind: `<path d="M3 8h11a3 3 0 1 0-3-3M3 12h15a3 3 0 1 1-3 3M3 16h8a2 2 0 1 1-2 2"/>`,
  drop: `<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11Z"/>`,
  dome: `<path d="M3 20h18M4 20v-5a8 8 0 0 1 16 0v5M12 7V4"/>`,
};
function wxIcon(k){ return `<svg class="pf-wx-i" viewBox="0 0 24 24" aria-hidden="true">${WX_ICONS[k] || WX_ICONS.cloud}</svg>`; }
function wxKind(short){
  const s = (short || "").toLowerCase();
  return /snow|flurr|sleet|wintry|blizzard/.test(s) ? "snow" : /rain|shower|storm|drizzle/.test(s) ? "rain"
    : /cloud|overcast|fog|haze/.test(s) ? "cloud" : "sun";
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
  const seg = (n, cls, title, i) => n > 0 ? `<i${cls ? ` class="${cls}"` : ""} style="--w:${(100 * n / team).toFixed(1)}%;--i:${i}" title="${title}"></i>` : "";
  const bar = seg(mine, "me", `${esc(name)} ${mine}`, 0) + rest.map((o, i) => seg(o[field], "", `${esc(o.n)} ${o[field]}`, i + 1)).join("");
  const key = [`<b>${shortName(name)} ${mine}</b>`]
    .concat(rest.map(o => `<span>${shortName(o.n)} ${o[field]}</span>`), unnamed ? [`<span>${t("profile.rz.others", {n: unnamed})}</span>`] : []);
  return `<div class="pf-split"><span class="pf-split-bar">${bar}</span><div class="pf-split-key">${key.join("")}</div></div>`;
}
