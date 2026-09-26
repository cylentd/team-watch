/* Weather drawing shared by every surface that shows a forecast: the profile's matchup block, the
   roster cards, and This week > Weather. Pure functions of what they are handed; nothing here reads
   a global. Moved here from profile/blocks.js and teams/cardweather.js on 2026-09-26, when the
   Weather view became the third reader. The icon's size and stroke are `.pf-wx-i` in
   surface/profile/sheet.css, one rule for every reader. */
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
/* Which sky icon a forecast phrase ("Chance Rain Showers") draws. */
function wxKind(short){
  const s = (short || "").toLowerCase();
  return /snow|flurr|sleet|wintry|blizzard/.test(s) ? "snow" : /rain|shower|storm|drizzle/.test(s) ? "rain"
    : /cloud|overcast|fog|haze/.test(s) ? "cloud" : "sun";
}
/* The top of a forecast's wind range: "5 to 10 mph" is 10. */
const wxWindMph = w => w && w.wind ? Math.max(...(w.wind.match(/\d+/g) || ["0"]).map(Number)) : 0;
