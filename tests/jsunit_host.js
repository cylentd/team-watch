/* The Node side of tests/jsunit.py. One process per loaded set of files, kept open for a test module.
   Reads one JSON request per line on stdin, writes one JSON answer per line on stdout:
     {op: "load", files: [abs paths], globals: {name: value}}  -> a fresh sandbox holding those files
     {op: "eval", src: "expression", args: [...]}             -> the expression's value, or, when it is a
                                                                 function, its value called with args
   Every value crosses as JSON, parsed inside the sandbox, so an array is the sandbox's own Array.
   The files run as classic scripts in one sandbox, in the order given, the way the page runs its one
   <script>: a top-level const in one file is visible to the next. */
const fs = require("fs");
const readline = require("readline");
const vm = require("vm");

let box = null;

function load(files, globals){
  /* stdout is the answer channel, so the code under test logs to stderr. */
  const log = (...a) => console.error(...a);
  box = vm.createContext({console: {log, info: log, warn: log, error: log}});
  box.__json = JSON.stringify(globals || {});
  vm.runInContext("for (const [k, v] of Object.entries(JSON.parse(__json))) globalThis[k] = v;", box);
  for (const f of files) vm.runInContext(fs.readFileSync(f, "utf8"), box, {filename: f});
  return null;
}

function evaluate(src, args){
  if (!box) throw new Error("jsunit: eval before load");
  box.__json = JSON.stringify(args || []);
  const out = vm.runInContext(`(() => { const v = (${src}); const a = JSON.parse(__json);
    const r = typeof v === "function" ? v(...a) : v;
    return r === undefined ? "null" : JSON.stringify(r); })()`, box, {filename: "jsunit-eval"});
  return JSON.parse(out);
}

const rl = readline.createInterface({input: process.stdin});
rl.on("line", line => {
  let answer;
  try {
    const q = JSON.parse(line);
    const value = q.op === "load" ? load(q.files, q.globals) : evaluate(q.src, q.args);
    answer = {ok: true, value};
  } catch (e) {
    answer = {ok: false, error: String(e && e.stack || e)};
  }
  process.stdout.write(JSON.stringify(answer) + "\n");
});
