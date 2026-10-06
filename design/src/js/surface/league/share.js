/* ============================== LEAGUE > RECAP: SHARE THE WEEK ==============================
   2026-10-06 (plan ~/.claude/plans/2026-10-06-recap-b.md, unit U3; storyboard section "share"): the League
   section's Share button turns the week into one 1080px PNG for the group chat. The same for every reader:
   the league, the week, the headline, every game with its tags and line; nothing about the picked team.
   lgShareData and lgShareText are pure (tests/test_js_league_share.py); the rest draws and sends. */

const LG_SHARE_TAGS = 2, LG_SHARE_W = 1080, LG_SHARE_PAD = 64;
const LG_SHARE_RESET_MS = 2000;
let LG_SHARE_TIMER = null;

/* A manager as plain text: the image and the text are not HTML, so lgMgr's escaping would show "&amp;". */
const lgShareName = id => { const x = LG && LG.teams.find(tm => tm.id === id); return x ? (x.mgr || x.name) : t("league.former"); };

function lgShareRow(w, g, headline){
  const aWon = g.win !== "away", [wi, wp, li, lp] = aWon ? [g.a, g.ap, g.b, g.bp] : [g.b, g.bp, g.a, g.ap];
  const tags = (lgGameTags(w, g) || []).slice(0, LG_SHARE_TAGS)
    .map(x => ({label: x.label, tone: x.tone, name: x.id != null ? lgShareName(x.id) : ""}));
  return {win: lgShareName(wi), winPts: lgPts(wp), lose: lgShareName(li), losePts: lgPts(lp), tie: g.win === "tie",
    tags, line: g.punch && g.punch !== headline ? g.punch : ""};
}

function lgShareData(w){
  const games = w.games.length ? lgGamesInOrder(w) : [], headline = w.head || (games[0] && games[0].punch) || "";
  return {kicker: t("league.share.kicker", {league: LG.league, n: w.week}), headline,
    rows: games.map(g => lgShareRow(w, g, headline)), url: t("league.share.url")};
}

function lgShareText(d){
  const out = [d.kicker.toUpperCase()];
  if (d.headline) out.push(d.headline);
  out.push("");
  d.rows.forEach(r => {
    const tags = r.tags.map(x => ` · ${x.label.toUpperCase()}${x.name ? " " + x.name : ""}`).join("");
    out.push(`${r.win} ${r.winPts} ${r.tie ? t("league.lead.tied") : t("league.lead.def")} ${r.lose} ${r.losePts}${tags}`);
    if (r.line) out.push(r.line);
    out.push("");
  });
  out.push(d.url);
  return out.join("\n");
}

function lgShareLabels(){
  return {btn: t("league.share.btn"), shared: t("league.share.shared"), copied: t("league.share.copied"),
    text: t("league.share.text"), saveTouch: t("league.share.saveTouch"), saveMouse: t("league.share.saveMouse"),
    close: t("league.share.close")};
}

/* ---------- the click ---------- */

/* The button's words: the label span if the markup has one, else its last text node. */
function lgShareSay(btn, state, label){
  const span = btn.querySelector(".lg-share-t"), node = span || [...btn.childNodes].reverse().find(n => n.nodeType === 3);
  if (node) node.textContent = label;
  btn.dataset.state = state;
}

function lgShareCanFiles(){
  try { return !!(navigator.canShare && navigator.canShare({files: [new File([""], "week.png", {type: "image/png"})]})); }
  catch (e) { return false; }
}

/* The share sheet is for a touch device that shares files; a desktop copies the image, even where it could
   share (Windows Chrome and Edge open the OS sheet, a detour on the way to a chat tab; review 2026-10-06). */
const lgShareRoute = (coarse, canFiles) => coarse && canFiles ? "sheet" : "clipboard";
const lgShareRouteHere = () => lgShareRoute(matchMedia("(pointer: coarse)").matches, lgShareCanFiles());

/* The week's PNG, drawn once per league and week. On a phone it is drawn when the League section is, so the
   tap can hand the share sheet a finished File without awaiting anything: iOS drops the tap's user
   activation across an await, and the share would fall through to the modal. */
const LG_SHARE_READY = new Map();
function lgSharePrep(w){
  const key = `${LG.league}|${w.week}`;
  let e = LG_SHARE_READY.get(key);
  if (!e){
    e = {png: lgSharePNG(lgShareData(w)), file: null};
    e.png.then(b => { e.file = new File([b], `week-${w.week}.png`, {type: "image/png"}); }, () => LG_SHARE_READY.delete(key));
    LG_SHARE_READY.set(key, e);
  }
  return e;
}
function lgShareWarm(w){ if (w && lgShareRouteHere() === "sheet") lgSharePrep(w); }

/* Last resort: the image in a centred modal (STYLE.md "Overlays"), saved by hand. Back closes it. */
function lgShareModal(png, d, L){
  const m = document.getElementById("modal"), hint = matchMedia("(pointer: coarse)").matches ? L.saveTouch : L.saveMouse;
  const url = URL.createObjectURL(png);
  m.innerHTML = `<div class="dr-head">
      <button type="button" class="dr-close" aria-label="${t("common.action.close")}">✕</button>
      <h3 id="lg-share-title" class="lg-share-hint">${esc(hint)}</h3>
    </div>
    <div class="dr-body lg-share-body"><img class="lg-share-img" src="${url}" alt="${esc(d.kicker)}"></div>
    <div class="lg-share-foot"><button type="button" class="lg-share-close">${esc(L.close)}</button></div>`;
  // A decoded image keeps showing, and saving reads the pixels, so the blob URL can go as soon as it loads.
  m.querySelector(".lg-share-img").addEventListener("load", () => URL.revokeObjectURL(url), {once: true});
  m.querySelector(".lg-share-close").addEventListener("click", () => closeModal(m));
  showModal(m, null, "lg-share-title");
}

/* Share the week: the share sheet on a phone that takes files, else the clipboard (image, then text), else
   the modal. The share sheet gets the File drawn ahead (lgSharePrep) when it is ready; the clipboard gets the
   image's promise unresolved, because Safari drops a clipboard write that begins after an await. Cancelling
   the share sheet is not an error. */
async function lgShare(w, btn){
  if (btn.dataset.state === "busy") return;
  const L = lgShareLabels(), d = lgShareData(w), ready = lgSharePrep(w), png = ready.png, sheet = lgShareRouteHere() === "sheet";
  png.catch(() => null);
  lgShareSay(btn, "busy", L.btn);
  const done = label => {
    lgShareSay(btn, "done", label);
    clearTimeout(LG_SHARE_TIMER);
    LG_SHARE_TIMER = setTimeout(() => lgShareSay(btn, "", L.btn), LG_SHARE_RESET_MS);
  };
  try {
    if (sheet){
      const file = ready.file || new File([await png], `week-${w.week}.png`, {type: "image/png"});
      await navigator.share({files: [file], text: d.url});
      return done(L.shared);
    }
    await navigator.clipboard.write([new ClipboardItem({"image/png": png})]);
    return done(L.copied);
  } catch (e) {
    if (e && e.name === "AbortError") return lgShareSay(btn, "", L.btn);
  }
  try {
    await navigator.clipboard.writeText(lgShareText(d));
    return done(L.text);
  } catch (e) {}
  lgShareSay(btn, "", L.btn);
  try { lgShareModal(await png, d, L); } catch (e) {}
}
