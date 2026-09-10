/* The same slug rule build.py uses, for a player the headshot set does not know. */
const slugOf = n => n.toLowerCase().replace(/[^a-z0-9 ]/g, "").split(/\s+/).filter(w => !["jr","sr","ii","iii","iv","v"].includes(w)).join("-");
const lastName = n => n.replace(/\s+(Jr|Sr|II|III|IV|V)\.?$/i, "").trim().split(" ").slice(-1)[0];
let EXPANDED = new Set();

/* The last 12 games as bars, the line as a rule across them. A bar that clears the line is lime.
   For a touchdown line the bars are scores and the rule sits at one. */
function gameLogHTML(p, log){
  const vals = log.v[p.mkt] || [];
  const line = p.mkt === "TD" ? 1 : p.line;
  if (!vals.length) return "";
  const W = 600, H = 72, padT = 8, padB = 14, n = vals.length, gap = 4;
  const bw = (W - gap * (n - 1)) / n;
  const top = Math.max(...vals, line || 0, 1) * 1.08;
  const y = v => padT + (H - padT - padB) * (1 - v / top);
  const hit = vals.filter(v => line != null && (p.mkt === "TD" ? v >= 1 : v > line)).length;
  const bars = vals.map((v, k) => {
    const x = k * (bw + gap), h = Math.max(1.5, y(0) - y(v));
    const ok = line != null && (p.mkt === "TD" ? v >= 1 : v > line);
    const g = log.g[k];
    return `<rect x="${x.toFixed(1)}" y="${y(v).toFixed(1)}" width="${bw.toFixed(1)}" height="${h.toFixed(1)}" fill="${ok ? "var(--lime)" : "var(--line-2)"}"><title>${g[0]} wk${g[1]} ${g[2] ? "vs " + esc(g[2]) : ""}: ${v}</title></rect>
      <text x="${(x + bw/2).toFixed(1)}" y="${H - 3}" text-anchor="middle" font-size="8" fill="var(--ink-3)" font-family="var(--mono)">${g[1]}</text>`;
  }).join("");
  const rule = line != null ? `<line x1="0" x2="${W}" y1="${y(line).toFixed(1)}" y2="${y(line).toFixed(1)}" stroke="var(--amber)" stroke-dasharray="3 3" stroke-width="1"/>` : "";
  const avg = vals.reduce((a, b) => a + b, 0) / n;
  const first = log.g[0], last = log.g[n - 1];
  return `<div class="gl">
    <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-label="last ${n} games">${bars}${rule}</svg>
    <div class="glcap">
      <span>${p.mkt === "TD" ? `scored in <b>${hit} of ${n}</b>` : `cleared ${line} in <b>${hit} of ${n}</b>`} · avg <b>${p.mkt === "TD" || p.mkt === "RECS" ? avg.toFixed(1) : avg.toFixed(0)}</b>${typeof p.mu === "number" ? ` · rate <b>${p.mkt === "TD" ? (p.mu).toFixed(2) : p.mu.toFixed(p.mkt === "RECS" ? 1 : 0)}</b>` : ""}</span>
      <span>${first[0]} wk${first[1]} → ${last[0]} wk${last[1]} · week numbers under the bars</span>
    </div>
  </div>`;
}

const INJ = {Q:"Q", O:"O", OUT:"OUT", IR:"IR", SUSP:"SUSP", PUP:"PUP", D:"D"};
