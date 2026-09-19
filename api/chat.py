"""The ask-a-question endpoint behind the Chat surface. POST /api/chat.

This is the first server-side code this repo has ever had. Everything else is a static page
Vercel serves from the committed root index.html, and it stays that way: a Vercel Python
function is file-based only while NO Python web framework is detected, so requirements.txt
lists `anthropic` and nothing else. Adding fastapi/flask/django would make Vercel route every
request to that framework and stop serving the page.

Why a server at all: an API key cannot go in the page. The page is one public 1.4 MB blob of
HTML and JS with no secret-injection step, so anything it holds, everyone holds.

Two env vars, both set in the Vercel project, never in the repo:

    ANTHROPIC_API_KEY   the key. Absent -> 503 and the UI says "not configured".
    CHAT_PASSPHRASE     the shared secret. Absent -> 503, because an open endpoint on a public
                        URL spends real money for whoever finds it. There is deliberately no
                        "unset means open" path.

The page sends its own data with the question. It already holds every player row inlined at
build time, so it picks the handful a question is about and posts them; the server keeps no
copy. That is why there is no data file here to deploy, nothing to fall out of sync with the
page, and why a future public version can take a visitor's own roster without changing this
file -- the context is an argument, not a lookup.

The 3-a-day cap lives in the browser (see design/src/js/surface/chat/chat.js). It is a
spending speed bump for one known user, not a security control: clearing site data resets it.
The passphrase is what actually stands between this endpoint and someone else's bill. What IS
enforced here is per-call cost: question length, context size, history depth and max_tokens are
all capped below, so no single call can be expensive no matter what the client sends.
"""

import hmac
import json
import os

from http.server import BaseHTTPRequestHandler

MODEL = "claude-sonnet-5"
# Cost ceilings per call. A request over any of these is rejected before the model sees it,
# so a bad or hostile client cannot turn one call into a large bill.
MAX_QUESTION = 600         # characters
MAX_CONTEXT = 32_000       # characters of client-supplied JSON
MAX_HISTORY = 8            # turns kept, oldest dropped
MAX_TOKENS = 4000          # includes thinking tokens, which bill as output
MAX_BODY = 64_000          # bytes we will even read off the wire
EFFORT = "low"

# Half-PPR is the scoring both leagues' numbers are computed in; the ESPN league's real scoring
# is custom and its projections are known to be off, most of all for QBs. Saying so here keeps
# the answer honest rather than confidently wrong.
SYSTEM = """\
You answer fantasy football questions inside Team Watch, a personal console for two 12-team \
half-PPR leagues.

Answer fantasy football questions only. For anything else -- code, news, general knowledge, \
personal advice -- say in one line that you only cover fantasy football here, and stop.

A CONTEXT block may follow with rows from the user's own data: projections, usage shares, \
injury designations, market-implied points, roster membership. Those numbers come from the \
user's own model.

Rules about numbers:
- Use the numbers in CONTEXT. Never invent one, and never round a number into a different one.
- If CONTEXT does not contain what the question needs, say which number is missing rather than \
estimating it.
- CONTEXT is half-PPR. The ESPN league uses custom scoring and starts no kicker, so a \
projection there is approximate -- say so when it would change the answer.
- A projection is a price, not a fact. Usage carries to next week; a single week's points do not.

Shape of your answer:
- Lead with the recommendation or the direct answer, on its own line.
- Then at most three short supporting lines, each carrying a number from CONTEXT.
- No preamble, no recap, no "great question". Under 120 words unless asked to go deeper.\
"""


def clean_question(raw):
    """The user's question, or None when there isn't a usable one."""
    if not isinstance(raw, str):
        return None
    q = raw.strip()
    return q[:MAX_QUESTION] if q else None


def clean_history(raw):
    """Prior turns, trimmed to the last MAX_HISTORY and to the two roles the API accepts.

    A malformed entry is dropped rather than raising: a client bug should cost the user their
    conversation memory, not the answer they are waiting for.
    """
    if not isinstance(raw, list):
        return []
    out = []
    for turn in raw:
        if not isinstance(turn, dict):
            continue
        role, content = turn.get("role"), turn.get("content")
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            out.append({"role": role, "content": content.strip()[:MAX_QUESTION * 4]})
    # The API needs the turns to alternate and to end on the user message we append next, so a
    # trailing assistant turn is what we want and a trailing user turn is dropped.
    if out and out[-1]["role"] == "user":
        out.pop()
    return out[-MAX_HISTORY:]


def clean_context(raw):
    """The client-supplied data block, serialized, or "" when there is nothing usable.

    Serialized here rather than trusted as a string so a client cannot smuggle prompt text in
    through a field that is supposed to hold player rows.
    """
    if raw in (None, "", [], {}):
        return ""
    try:
        text = json.dumps(raw, separators=(",", ":"), sort_keys=True)
    except (TypeError, ValueError):
        return ""
    return "" if len(text) > MAX_CONTEXT else text


def build_messages(question, context, history):
    """The `messages` array for one turn: prior turns, then this question with its data.

    The data rides in the user turn, not the system prompt, because it changes with every
    question while the system prompt does not -- which is also what lets the cached prefix
    survive a follow-up.
    """
    if context:
        content = f"CONTEXT (the user's own data, half-PPR):\n{context}\n\nQUESTION: {question}"
    else:
        content = f"QUESTION: {question}"
    return list(history) + [{"role": "user", "content": content}]


def ask(question, context, history, api_key):
    """One call to Claude. Returns the answer text.

    Imported lazily so this module stays importable -- and testable -- without the SDK present.
    """
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        thinking={"type": "adaptive"},
        output_config={"effort": EFFORT},
        messages=build_messages(question, context, history),
    )
    if response.stop_reason == "refusal":
        return "I can't answer that one."
    return "\n".join(b.text for b in response.content if b.type == "text").strip()


class handler(BaseHTTPRequestHandler):

    def _send(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        # The answer is one user's league data; no cache, anywhere, ever.
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        """Whether the endpoint can work at all, so the UI can say "not configured" without
        spending a call. Says nothing about whether a given passphrase is right."""
        self._send(200, {"configured": bool(os.environ.get("ANTHROPIC_API_KEY"))
                         and bool(os.environ.get("CHAT_PASSPHRASE"))})

    def do_POST(self):
        key = os.environ.get("ANTHROPIC_API_KEY")
        secret = os.environ.get("CHAT_PASSPHRASE")
        if not key or not secret:
            return self._send(503, {"error": "Chat is not configured on the server yet."})

        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._send(400, {"error": "Bad request."})
        if length <= 0 or length > MAX_BODY:
            return self._send(413, {"error": "That question is too large."})

        try:
            body = json.loads(self.rfile.read(length))
        except (ValueError, OSError):
            return self._send(400, {"error": "Bad request."})
        if not isinstance(body, dict):
            return self._send(400, {"error": "Bad request."})

        # compare_digest on both sides so a wrong passphrase costs the same time as a right one.
        given = body.get("passphrase")
        if not isinstance(given, str) or not hmac.compare_digest(given, secret):
            return self._send(401, {"error": "Wrong passphrase."})

        question = clean_question(body.get("question"))
        if not question:
            return self._send(400, {"error": "Ask a question first."})

        try:
            answer = ask(question, clean_context(body.get("context")),
                         clean_history(body.get("history")), key)
        except Exception as exc:                                   # noqa: BLE001
            # The message can carry a key or a request id, so it goes to the function log and
            # never to the browser.
            print(f"chat: {type(exc).__name__}: {exc}")
            return self._send(502, {"error": "Claude could not answer that. Try again."})

        self._send(200, {"answer": answer or "No answer came back. Try rephrasing."})

    def log_message(self, fmt, *args):
        """Vercel already logs the request line; this would double every entry."""
