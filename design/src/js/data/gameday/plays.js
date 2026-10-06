/* ============================== GAMEDAY: NAMES IN A PLAY LINE ==============================
   Every player name in a play is bold (U9, 2026-10-05; David: "the game log should bold the players
   name"). ESPN's play text writes "J.Allen pass short left to K.Shakir pushed ob (D.White)".

   Two ways to find a name, both pure and both used, so a line never shows a name unbolded:
     1. ESPN's own participants on the play, when it sends them: each one's full name is turned into
        the forms the text uses ("Josh Allen" -> "Josh Allen", "J.Allen", "J. Allen").
     2. The initial-dot pattern ("J.Allen", "A.J.Brown", "A.St. Brown", "M.Harrison Jr."), for every
        name the participants leave out (a defender on a tackle, a long snapper).
   gsBoldNames returns escaped HTML; nothing here touches the page. */

/* The initial-dot pattern: one to three initials, the surname (apostrophes and hyphens inside it), an
   optional "St. " before it and a Jr./Sr./II-IV after. Not after a letter or a dot, so "DET-P.Sewell"
   and "Center-J.Cardona" match and "U.S.Open" would not start mid-word. */
const GS_NAME_RE = /(?<![A-Za-z.])(?:[A-Z]\.){1,3} ?(?:St\. )?[A-Z][A-Za-z'’-]*[A-Za-z](?: (?:Jr|Sr|II|III|IV)\b\.?)?/g;

/* The names ESPN lists on a play: athlete.displayName, else fullName, else the participant's own. */
function gsPlayNames(play){
  return ((play && play.participants) || []).map(x => {
    const a = (x && x.athlete) || x || {};
    return a.displayName || a.fullName || "";
  }).filter(Boolean);
}

/* The spellings of one full name a play line may use. */
function gsNameForms(full){
  const parts = String(full).trim().split(/\s+/), forms = new Set([parts.join(" ")]);
  if (parts.length > 1){
    const first = parts[0], rest = parts.slice(1).join(" ");
    const ini = /^([A-Z]\.){2,}$/.test(first) ? first : `${first[0]}.`;
    forms.add(`${ini}${rest}`); forms.add(`${ini} ${rest}`);
  }
  return [...forms];
}

const gsReEsc = s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/* The text with every name inside <b>…</b> and everything else escaped. `names` are the full names of the
   play's participants (gsPlayNames), or empty. */
function gsBoldNames(text, names){
  const s = String(text == null ? "" : text);
  if (!s) return "";
  const spans = [];
  for (const full of names || []) for (const f of gsNameForms(full)){
    const re = new RegExp(`(?<![A-Za-z])${gsReEsc(f)}(?![A-Za-z])`, "g");
    for (const m of s.matchAll(re)) spans.push([m.index, m.index + m[0].length]);
  }
  for (const m of s.matchAll(GS_NAME_RE)) spans.push([m.index, m.index + m[0].length]);
  spans.sort((a, b) => a[0] - b[0] || b[1] - a[1]);
  const merged = [];
  for (const sp of spans){
    const last = merged[merged.length - 1];
    if (last && sp[0] <= last[1]) last[1] = Math.max(last[1], sp[1]); else merged.push([...sp]);
  }
  let out = "", at = 0;
  for (const [a, b] of merged){ out += esc(s.slice(at, a)) + `<b>${esc(s.slice(a, b))}</b>`; at = b; }
  return out + esc(s.slice(at));
}
