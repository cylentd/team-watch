/* The Node side of tests/jsunit.py. One process per Python process, holding any number of sandboxes.
   Reads one JSON request per line on stdin, writes one JSON answer per line on stdout:
     {id, op: "load", ctx, files: [abs paths], globals: {name: value}}
                                              -> a fresh sandbox `ctx` holding those files
     {id, op: "eval", ctx, src: "expression", args: [...]}
                                              -> the expression's value, or, when it is a function,
                                                 its value called with args, in sandbox `ctx`
     {id, op: "drop", ctx}                    -> forget sandbox `ctx`
   Every answer repeats the request's id. Every value crosses as JSON, parsed inside the sandbox, so
   an array is the sandbox's own Array. A sandbox is a vm context of its own: nothing a call sets is
   visible in another sandbox. The files run as classic scripts in one sandbox, in the order given,
   the way the page runs its one <script>: a top-level const in one file is visible to the next. */
const fs = require("fs");
const readline = require("readline");
const vm = require("vm");

const boxes = new Map();
const scripts = new Map();      // path + mtime -> compiled vm.Script, shared by every sandbox that loads it

function script(f){
  const key = f + "@" + fs.statSync(f).mtimeMs;
  if (!scripts.has(key)) scripts.set(key, new vm.Script(fs.readFileSync(f, "utf8"), {filename: f}));
  return scripts.get(key);
}

function load(ctx, files, globals){
  /* stdout is the answer channel, so the code under test logs to stderr. */
  const log = (...a) => console.error(...a);
  const box = vm.createContext({console: {log, info: log, warn: log, error: log}});
  box.__json = JSON.stringify(globals || {});
  vm.runInContext("for (const [k, v] of Object.entries(JSON.parse(__json))) globalThis[k] = v;", box);
  boxes.set(ctx, box);
  for (const f of files) script(f).runInContext(box);
  return null;
}

function evaluate(ctx, src, args){
  const box = boxes.get(ctx);
  if (!box) throw new Error("jsunit: eval before load");
  box.__json = JSON.stringify(args || []);
  const out = vm.runInContext(`(() => { const v = (${src}); const a = JSON.parse(__json);
    const r = typeof v === "function" ? v(...a) : v;
    return r === undefined ? "null" : JSON.stringify(r); })()`, box, {filename: "jsunit-eval"});
  return JSON.parse(out);
}

const rl = readline.createInterface({input: process.stdin});
rl.on("line", line => {
  let id = null, answer;
  try {
    const q = JSON.parse(line);
    id = q.id;
    let value = null;
    if (q.op === "load") value = load(q.ctx, q.files, q.globals);
    else if (q.op === "drop") boxes.delete(q.ctx);
    else value = evaluate(q.ctx, q.src, q.args);
    answer = {id, ok: true, value};
  } catch (e) {
    answer = {id, ok: false, error: String(e && e.stack || e)};
  }
  process.stdout.write(JSON.stringify(answer) + "\n");
});
