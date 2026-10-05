/* ============================== GAMEDAY: WHO A FRESH CLIP IS OF ==============================
   Live > TDs' reel (2026-10-05) names a fresh clip (tdclips.js holds what came back) for a scorer by its
   title alone, so the rule must not credit a clip for a word that merely is somebody's last name. Week 4
   showed how that goes wrong: "Chase Brown" credited Ja'Marr Chase, "let him cook" credited J. Cook,
   "Taylor Swift" D. Swift, "Hall of Fame" B. Hall.

   A clip is of a scorer when it was posted after his game's kickoff, on his club's channel or NFL's, and
   its title (case and accents gone, "Ja'Marr" read as one word) holds, once every OTHER player's full
   name is blanked out of it:
     his full name ("amon ra st brown" or first and last), or "J. Cook", or #FirstLast, or a nickname,
     his bare last name, only on his own club's channel (the NFL channel names whole players),
     his jersey number, only on his own club's channel, only as the title's first word followed by a word
       ("88 in the end zone") or as "No. 88": a number anywhere else is a score, a down or a count.
   LIVE_NAMES {slug: {n, t, k}} (design/player_names.py) supplies numbers and nicknames; the other
   players' names are its slugs and the day's scorers. A page built without it matches on the name alone. */

const TDC_SUFFIX = ["jr", "sr", "ii", "iii", "iv", "v"];
/* What a number opening a title may not be counting: "22 yards", "10 plays", "2 TDs in a quarter". */
const TDC_UNITS = "yards?|yds?|points?|pts?|plays?|tds?|touchdowns?|catches|receptions?|carries|seconds?|minutes?|games?|straight|years?|times?|weeks?";

const tdcFold = s => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const tdcRx = s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const tdcWord = (text, w) => !!w && new RegExp(`(?<![a-z0-9])${tdcRx(w)}(?![a-z0-9])`).test(text);
/* A title or a name as words: a possessive dropped ("Rusher's" is "rusher"), apostrophes, periods and hyphens
   joined, the way a slug is cut ("Ja'Marr" is "jamarr", "St. Brown" is "st brown"), anything else a space;
   # stays so a hashtag is one word. */
const tdcNorm = s => tdcFold(s).replace(/['’]s\b/g, "").replace(/[.'’-]/g, "").replace(/[^a-z0-9#]+/g, " ").trim();

/* The number as a jersey: "88 in the end zone" opening the title, or "No. 88". Never inside a time, a
   score, a down ("3rd and 10"), a count ("Top 10 plays") or a hashtag. `raw` is tdcFold's, punctuation kept. */
const tdcNumber = (raw, n) => Number.isFinite(n)
  && (new RegExp(`^\\s*${n}\\s+(?!(?:${TDC_UNITS})\\b)[a-z]`).test(raw)
    || new RegExp(`(?<![a-z0-9])no\\.?\\s*${n}(?![0-9:/%-])`).test(raw));

/* His words from "Amon-Ra St. Brown" (suffix dropped): the last name, the full names a title may use, the
   initial and last name, and #FirstLast. A one-word name has none of them. */
function tdcParts(name){
  const w = tdcNorm(name).split(" ").filter(x => x && !TDC_SUFFIX.includes(x));
  const first = w[0] || "", last = w.length > 1 ? w[w.length - 1] : "";
  if (!last) return {last: "", full: [], init: "", tags: []};
  return {last, full: [...new Set([w.join(" "), `${first} ${last}`])], init: `${first[0]} ${last}`,
          tags: [...new Set([`#${first}${last}`, `#${w.join("")}`])]};
}

/* Everybody the page knows by slug: LIVE_NAMES, and the day's scorers (a page built without it). */
function tdcSlugs(){
  const lead = Object.values((GD_STATS && GD_STATS.lead) || {}).map(v => slugOf(v.n || ""));
  return [...Object.keys((typeof LIVE_NAMES !== "undefined" && LIVE_NAMES) || {}), ...lead];
}
let TDC_KNOWN = {key: "", set: new Set()};
function tdcKnown(){
  const s = tdcSlugs(), key = `${s.length}:${s[0]}:${s[s.length - 1]}`;
  if (TDC_KNOWN.key !== key) TDC_KNOWN = {key, set: new Set(s.filter(Boolean).map(x => x.replace(/-/g, " ")))};
  return TDC_KNOWN.set;
}

/* The title with every player's full name but `own` (a normalised name) blanked to "_", longest first,
   so "chase brown" is nobody's "chase". */
function tdcBlank(title, own, known){
  const tok = title.split(" ");
  for (let i = 0; i < tok.length; i++) for (let n = 4; n >= 2; n--){
    if (i + n > tok.length) continue;
    const name = tok.slice(i, i + n).join(" ");
    if (name === own || !known.has(name)) continue;
    for (let j = i; j < i + n; j++) tok[j] = "_";
    i += n - 1;
    break;
  }
  return tok.join(" ");
}

/* w = {n, slug, team}; ch the channel the clip came from. */
function tdcMatches(w, c, ch, known = tdcKnown()){
  const kick = Date.parse((tdGameOf(w.team) || {}).kickoff);
  if (!(Date.parse(c.posted) > kick)) return false;
  const own = ch === tdcCode(w.team);
  if (!own && ch !== "NFL") return false;
  const nm = tdcParts(w.n), row = tdcNameRow(w.slug) || {}, raw = tdcFold(c.title);
  const title = tdcBlank(tdcNorm(c.title), nm.full[0] || tdcNorm(w.n), known);
  return (own && tdcWord(title, nm.last))
    || nm.full.some(f => tdcWord(title, f))
    || tdcWord(title, nm.init)
    || nm.tags.some(g => tdcWord(title, g))
    || (row.k || []).some(k => tdcWord(title, tdcNorm(k)))
    || (own && tdcNumber(raw, row.n));
}

/* One play, two uploads: the NFL's copy within TD_CLIPS_TWIN_MS of his own club's is the same play, and
   the club's plays here while the NFL's is blocked, so the NFL's goes. */
const TD_CLIPS_TWIN_MS = 900000;

/* The fresh clips that are of this scorer, one per id, newest not sorted here. */
function tdcFor(w){
  const known = tdcKnown(), seen = new Set(), hit = [];
  for (const [ch, clips] of Object.entries(TDC.by)) for (const c of clips){
    if (seen.has(c.id) || !tdcMatches(w, c, ch, known)) continue;
    seen.add(c.id); hit.push({c, ch});
  }
  const club = tdcCode(w.team), mine = hit.filter(x => x.ch === club).map(x => Date.parse(x.c.posted));
  return hit.filter(x => x.ch !== "NFL" || !mine.some(at => Math.abs(Date.parse(x.c.posted) - at) <= TD_CLIPS_TWIN_MS)).map(x => x.c);
}
