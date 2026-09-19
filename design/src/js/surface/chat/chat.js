/* ------------------------------------------------------------------
   CHAT — ask a fantasy football question about the data on this page.

   The only surface that talks to a server. POST /api/chat carries the question, a passphrase
   and the handful of player rows context.js picked; the key itself never leaves Vercel.

   Three questions a day, counted in this browser. That is a spending speed bump for one known
   user, not a lock -- clearing site data resets it. The passphrase is the thing that actually
   keeps this endpoint off a stranger's question. Both are deliberate: see api/chat.py.
------------------------------------------------------------------ */

const CHAT_DAILY = 3;
const CHAT_PASS_KEY = "tw-chat-pass";
let CHAT_LOG = [];          /* [{role:"user"|"assistant", content}] -- this session only */
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

function chatTurnHTML(turn){
  const who = turn.role === "user" ? t("chat.you") : t("chat.claude");
  /* Escaped, then newlines become breaks. The answer is model text rendered into our own page,
     so it is untrusted input like any other -- never innerHTML'd raw. */
  const body = esc(turn.content).replace(/\n/g, "<br>");
  return `<div class="chatturn ${turn.role === "user" ? "mine" : "theirs"}">
    <div class="chatwho">${who}</div><div class="chatbody">${body}</div></div>`;
}

function chatComposerHTML(){
  const left = chatLeft(), out = left === 0;
  return `<div class="chatbar">
    <textarea class="chatinput" data-chatinput rows="2" ${out || CHAT_BUSY ? "disabled" : ""}
      placeholder="${esc(out ? t("chat.limit.none") : t("chat.placeholder"))}"></textarea>
    <button class="chatsend" data-chatsend ${out || CHAT_BUSY ? "disabled" : ""}>${
      CHAT_BUSY ? t("chat.thinking") : t("chat.send")}</button>
  </div>`;
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

function chatHTML(){
  const log = CHAT_LOG.length
    ? CHAT_LOG.map(chatTurnHTML).join("")
    : `<p class="chatempty">${t("chat.empty")}</p>`;
  return `<div class="wrap">
    <section class="chatpanel">
      <h2 class="chattitle">${t("chat.title")}</h2>
      <p class="chatintro">${t("chat.intro")}</p>
      ${chatPass() ? "" : chatPassHTML()}
      <div class="chatlog" data-chatlog>${log}</div>
      ${CHAT_ERR ? `<p class="chaterr">${esc(CHAT_ERR)}</p>` : ""}
      ${chatComposerHTML()}
      <p class="chatfoot">${t("chat.limit.left", {n: chatLeft(), of: CHAT_DAILY})}${
        chatPass() ? ` · <button class="chatlink" data-chatforget>${t("chat.pass.forget")}</button>` : ""}</p>
    </section>
  </div>`;
}

/* ---------------------------------------------------------------- sending */

async function chatSend(question){
  const pass = chatPass();
  if (!pass){ CHAT_ERR = t("chat.error.nopass"); render(); return; }

  CHAT_LOG.push({role: "user", content: question});
  CHAT_BUSY = true; CHAT_ERR = ""; render();

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
  render();
}

/* ---------------------------------------------------------------- wiring */

function wireChat(v){
  const input = v.querySelector("[data-chatinput]");
  const send = () => {
    const q = (input.value || "").trim();
    if (q && !CHAT_BUSY && chatLeft() > 0) chatSend(q);
  };
  v.querySelector("[data-chatsend]")?.addEventListener("click", send);
  input?.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey){ e.preventDefault(); send(); }
  });
  v.querySelector("[data-chatsave]")?.addEventListener("click", () => {
    const el = v.querySelector("[data-chatpass]");
    chatSetPass((el.value || "").trim());
    CHAT_ERR = ""; render();
  });
  v.querySelector("[data-chatforget]")?.addEventListener("click", () => {
    chatSetPass(""); render();
  });
  const log = v.querySelector("[data-chatlog]");
  if (log) log.scrollTop = log.scrollHeight;
  if (!CHAT_BUSY && chatLeft() > 0) input?.focus();
}
