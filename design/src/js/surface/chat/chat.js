/* ------------------------------------------------------------------
   CHAT — ask a fantasy football question about the data on this page.

   A floating panel, not a tab. It was a tab first, which meant leaving the roster to ask about
   the roster; the whole value of "start Achane or Pollard" is reading their rows while you ask.
   So the launcher and the panel live outside #view (see shell.html): render() rewrites #view on
   every surface change, and anything inside it loses its state.

   Deliberately NOT a modal. The drawer next door is one -- scrim, aria-modal, focus trap -- and
   that blocks the page behind it. This stays open while you navigate, so no scrim and no trap;
   Escape and the close button are the only ways out, and the conversation is still there when
   you come back.

   The only surface that talks to a server. POST /api/chat carries the question, a passphrase and
   the handful of player rows context.js picked; the key itself never leaves Vercel.
------------------------------------------------------------------ */

const CHAT_DAILY = 3;
const CHAT_PASS_KEY = "tw-chat-pass";
let CHAT_LOG = [];          /* [{role:"user"|"assistant", content}] -- this session only */
let CHAT_OPEN = false;
let CHAT_BUSY = false;
let CHAT_ERR = "";

/* Counted per calendar day, so the key is the date and yesterday's count simply stops being
   read. No cleanup, no expiry logic, and a day boundary needs no clock beyond toLocaleDateString. */
const chatDayKey = () => "tw-chat-" + new Date().toLocaleDateString("en-CA");

function chatUsed(){
  try { return parseInt(localStorage.getItem(chatDayKey()) || "0", 10) || 0; }
  catch (e) { return 0; }          /* private mode / blocked storage: never block the UI */
}
function chatBump(){
  try { localStorage.setItem(chatDayKey(), String(chatUsed() + 1)); } catch (e) {}
}
const chatLeft = () => Math.max(0, CHAT_DAILY - chatUsed());

function chatPass(){
  try { return localStorage.getItem(CHAT_PASS_KEY) || ""; } catch (e) { return ""; }
}
function chatSetPass(v){
  try { v ? localStorage.setItem(CHAT_PASS_KEY, v) : localStorage.removeItem(CHAT_PASS_KEY); }
  catch (e) {}
}

/* ---------------------------------------------------------------- markup */

const CHAT_GLYPH = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M20 4H4a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3v4l4-4h9a1 1 0 0 0 1-1V5a1 1 0 0 0-1-1z"/></svg>`;

function chatTurnHTML(turn){
  const who = turn.role === "user" ? t("chat.you") : t("chat.claude");
  /* Escaped, then newlines become breaks. The answer is model text rendered into our own page,
     so it is untrusted input like any other -- never innerHTML'd raw. */
  const body = esc(turn.content).replace(/\n/g, "<br>");
  return `<div class="chatturn ${turn.role === "user" ? "mine" : "theirs"}">
    <div class="chatwho">${who}</div><div class="chatbody">${body}</div></div>`;
}

function chatPassHTML(){
  return `<div class="chatpass">
    <label class="chatpasslab" for="chatpass">${t("chat.pass.label")}</label>
    <input class="chatpassin" id="chatpass" type="password" data-chatpass
      placeholder="${esc(t("chat.pass.placeholder"))}" value="${esc(chatPass())}">
    <button class="chatsend" data-chatsave>${t("chat.pass.save")}</button>
    <p class="chatpasshint">${t("chat.pass.hint")}</p>
  </div>`;
}

function chatDockHTML(){
  const left = chatLeft(), out = left === 0;
  const log = CHAT_LOG.length
    ? CHAT_LOG.map(chatTurnHTML).join("")
    : `<p class="chatempty">${t("chat.empty")}</p>`;
  return `<div class="chathead">
      <h2 class="chattitle" id="chattitle">${t("chat.title")}</h2>
      <button class="chatx" data-chatclose aria-label="${esc(t("chat.close"))}">✕</button>
    </div>
    <div class="chatscroll" data-chatlog>
      <p class="chatintro">${t("chat.intro")}</p>
      ${chatPass() ? "" : chatPassHTML()}
      ${log}
      ${CHAT_ERR ? `<p class="chaterr">${esc(CHAT_ERR)}</p>` : ""}
    </div>
    <div class="chatbar">
      <textarea class="chatinput" data-chatinput rows="1" ${out || CHAT_BUSY ? "disabled" : ""}
        placeholder="${esc(out ? t("chat.limit.none") : t("chat.placeholder"))}"></textarea>
      <button class="chatsend" data-chatsend ${out || CHAT_BUSY ? "disabled" : ""}>${
        CHAT_BUSY ? t("chat.thinking") : t("chat.send")}</button>
    </div>
    <p class="chatfoot">${t("chat.limit.left", {n: left, of: CHAT_DAILY})}${
      chatPass() ? ` · <button class="chatlink" data-chatforget>${t("chat.pass.forget")}</button>` : ""}</p>`;
}

/* ---------------------------------------------------------------- paint */

/* Repaints the panel only. Never call render() from here: that rebuilds #view, which would
   scroll the page and rebuild the surface underneath for no reason. */
function renderChat(){
  const fab = document.getElementById("chatfab"), dock = document.getElementById("chatdock");
  const left = chatLeft();
  fab.innerHTML = CHAT_GLYPH;
  fab.classList.toggle("out", !left);
  fab.setAttribute("aria-label", t("chat.open"));
  fab.title = t("chat.limit.left", {n: left, of: CHAT_DAILY});
  fab.setAttribute("aria-expanded", String(CHAT_OPEN));
  fab.classList.toggle("on", CHAT_OPEN);
  dock.classList.toggle("on", CHAT_OPEN);
  dock.setAttribute("aria-hidden", String(!CHAT_OPEN));
  if (!CHAT_OPEN){ dock.innerHTML = ""; return; }
  dock.innerHTML = chatDockHTML();
  dock.setAttribute("aria-labelledby", "chattitle");
  wireChat(dock);
}

function chatToggle(open){
  CHAT_OPEN = open === undefined ? !CHAT_OPEN : open;
  renderChat();
  if (CHAT_OPEN) document.querySelector("[data-chatinput]")?.focus({preventScroll: true});
}

/* ---------------------------------------------------------------- sending */

async function chatSend(question){
  const pass = chatPass();
  if (!pass){ CHAT_ERR = t("chat.error.nopass"); renderChat(); return; }

  CHAT_LOG.push({role: "user", content: question});
  CHAT_BUSY = true; CHAT_ERR = ""; renderChat();

  let payload = null, ok = false;
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        passphrase: pass,
        question,
        context: chatContext(question),
        /* The question just pushed is the live one; the server appends it itself. */
        history: CHAT_LOG.slice(0, -1),
      }),
    });
    payload = await res.json().catch(() => null);
    ok = res.ok;
  } catch (e) {
    CHAT_ERR = t("chat.error.network");
  }

  CHAT_BUSY = false;
  if (ok && payload && payload.answer){
    CHAT_LOG.push({role: "assistant", content: payload.answer});
    /* Counted only on an answer. A wrong passphrase or a dead server costs no question. */
    chatBump();
  } else if (!CHAT_ERR){
    CHAT_ERR = (payload && payload.error) || t("chat.error.network");
    CHAT_LOG.pop();                      /* unanswered question leaves no turn behind */
  }
  renderChat();
}

/* ---------------------------------------------------------------- wiring */

function wireChat(dock){
  const input = dock.querySelector("[data-chatinput]");
  const send = () => {
    const q = (input.value || "").trim();
    if (q && !CHAT_BUSY && chatLeft() > 0) chatSend(q);
  };
  dock.querySelector("[data-chatsend]")?.addEventListener("click", send);
  dock.querySelector("[data-chatclose]")?.addEventListener("click", () => chatToggle(false));
  input?.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey){ e.preventDefault(); send(); }
  });
  dock.querySelector("[data-chatsave]")?.addEventListener("click", () => {
    const el = dock.querySelector("[data-chatpass]");
    chatSetPass((el.value || "").trim());
    CHAT_ERR = ""; renderChat();
  });
  dock.querySelector("[data-chatforget]")?.addEventListener("click", () => {
    chatSetPass(""); renderChat();
  });
  const log = dock.querySelector("[data-chatlog]");
  if (log) log.scrollTop = log.scrollHeight;
}

/* Registered once, at load, because the launcher lives outside #view and render() never touches
   it -- wiring it per render would stack a listener on every surface change. */
function buildChat(){
  document.getElementById("chatfab").addEventListener("click", () => chatToggle());
  document.addEventListener("keydown", e => {
    /* The drawer owns Escape when it is open; closing both at once would be a surprise. */
    if (e.key === "Escape" && CHAT_OPEN && !document.getElementById("drawer").classList.contains("on"))
      chatToggle(false);
  });
  renderChat();
}
