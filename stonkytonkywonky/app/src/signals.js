// Signals: one line per area (state, what it means, link), and what flipped since the last data day.
import { el, app, pageBox } from "./core.js";
import { freshLine, staleAny } from "./ui.js";
import { diff } from "./state.js";
import * as valuation from "./valuation.js";
import * as dips from "./dips.js";
import * as macro from "./macro.js";
import * as positioning from "./positioning.js";
import * as calendar from "./calendar.js";
import * as ai from "./ai.js";
import * as memory from "./memory.js";

// Dashboard order: the tab key each line opens, how to read it, and the files behind it.
const ROWS = [
  ["valuation", valuation.signal, ["ranking"]],
  ["highlow", dips.signal, dips.SOURCES],
  ["markets", macro.signal, macro.SOURCES],
  ["positioning", positioning.signal, positioning.SOURCES],
  ["horizon", calendar.signal, calendar.SOURCES],
  ["compute", ai.signal, ai.SOURCES],
  ["industry", memory.signal, ["industry"]],
  ["industry", memory.discountSignal, ["discounts"]],
];

function row(key, build, sources, D) {
  let s;
  try { s = build(D); } catch { return null; }
  const r = el("button", { class: `sig-row lv-${s.level ?? "na"}` });
  const body = el("div", { class: "sig-body" });
  const top = el("p", { class: "sig-means" });
  top.append(el("span", { class: `state lv-${s.level ?? "na"}` }, s.state), " ", s.short ?? s.means);
  body.append(top);
  if (s.extra) body.append(s.extra);
  if (staleAny(sources)) body.append(freshLine(sources));
  r.append(el("span", { class: "sig-dot", "aria-hidden": "true" }), el("span", { class: "sig-area" }, s.area), body);
  r.addEventListener("click", (e) => {
    if (e.target.closest(".sig-tk")) return;
    app.go(key).then(() => s.anchor && document.getElementById(s.anchor)?.scrollIntoView({ block: "start" }));
  });
  return r;
}

// What flipped between the two latest nightly snapshots (scripts/snapshot.mjs).
function changes(C) {
  const snaps = C?.snapshots ?? [];
  const box = el("div", { class: "changes" });
  if (snaps.length < 2) {
    box.append(el("h3", {}, "What changed"), el("p", { class: "muted" }, snaps.length ? `The first snapshot was taken for ${snaps[0].date}; changes show from the next nightly run.` : "No snapshots yet."));
    return box;
  }
  const prev = snaps[snaps.length - 2], now = snaps[snaps.length - 1];
  const d = diff(prev, now);
  box.append(el("h3", {}, `What changed since ${prev.date}`));
  const ul = el("ul");
  for (const f of d.flips) {
    const li = el("li");
    li.append(el("strong", {}, f.label), `: ${f.from} → ${f.to}`);
    ul.append(li);
  }
  if (d.added.length) ul.append(el("li", {}, `New on the cheap list (estimates holding): ${d.added.join(", ")}`));
  if (d.dropped.length) ul.append(el("li", {}, `Off the cheap list: ${d.dropped.join(", ")}`));
  if (!ul.children.length) box.append(el("p", { class: "muted" }, "Nothing flipped: every reading is where it was."));
  else box.append(ul);
  return box;
}

export function render(D) {
  const head = el("div", { class: "d-head" });
  head.append(el("div", { class: "d-sub" }, `Data as of ${D.ranking?.as_of ?? "n/a"} · click a line to open its tab`));
  const list = el("div", { class: "sig-list" });
  for (const [key, build, sources] of ROWS) {
    const r = row(key, build, sources, D);
    if (r) list.append(r);
  }
  pageBox().replaceChildren(head, changes(D.changes), list);
}
