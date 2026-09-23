/* ---------------------------- helpers ---------------------------- */
const initials = n => n.split(/\s+/).slice(0,2).map(w=>w[0]).join("");
/* The app's one spelling of a name used inline, not as a title: "B. Allen". The full name is a
   heading's job. Everything after the first word stays, so a suffix rides with the surname
   ("H. Fannin Jr.") and so does a two-word surname ("A. St. Brown"). A first name that is already
   initials ("C.J. Stroud") stays as written, and a defence ("Seahawks D/ST") has no first name
   to shorten. Returns plain text; the caller escapes. */
function nameInitial(n){
  const s = String(n || "").trim(), parts = s.split(/\s+/);
  if (parts.length < 2 || /D\/ST$/.test(s) || /^([A-Z]\.){2,}$/.test(parts[0])) return s;
  return `${parts[0][0]}. ${parts.slice(1).join(" ")}`;
}
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
/* Copy is data: every user-facing string lives in design/src/content.json, injected above this
   file as `const COPY`. t() looks a key up and fills {name} placeholders. It deliberately does
   NOT escape -- copy may carry intentional markup (<b>, <ol>), and a call site still runs esc()
   over the data it interpolates, exactly as it did before. An unknown key throws rather than
   rendering "undefined": assemble --check catches it first, this catches the rest. */
const t = (k, v) => { const s = COPY[k]; if (s === undefined) throw new Error("copy: " + k); return v ? s.replace(/\{(\w+)\}/g, (_, n) => v[n]) : s; };

