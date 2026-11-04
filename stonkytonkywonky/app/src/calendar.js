// Calendar: dated events, how big a move options price in, and prediction-market odds for the rest.
import { el, svg, fmt, pct, dayNum, hzSigned, pageBox } from "./core.js";
import { topCard, nowLine, chips } from "./ui.js";

export const SOURCES = ["horizon"];
let D = null;

const HZ_RANGES = [[14, "2 weeks"], [31, "1 month"], [null, "All"]];
const HZ_THEMES = { rates: "Rates", oil: "Oil and the Gulf", geopolitics: "Geopolitics", growth: "Growth", politics: "Politics" };
const HZ_WEEKDAY = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const HZ_MONTH = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const hz = { range: 31, all: false };

export const hzDate = (iso) => {
  const d = new Date(`${iso}T12:00:00Z`);
  return `${HZ_WEEKDAY[d.getUTCDay()]} ${d.getUTCDate()} ${HZ_MONTH[d.getUTCMonth()]}`;
};
const hzIn = (iso, asOf) => {
  const n = dayNum(iso) - dayNum(asOf);
  return n === 0 ? "today" : n === 1 ? "tomorrow" : `in ${n} days`;
};
const hzPct = (p) => `${Math.round(p * 100)}%`;
const hzPts = (now, past) => (past == null ? null : Math.round((now - past) * 100));

function hzImpact(n) {
  return el("span", { class: "hz-impact", title: `Impact on an AI and memory book: ${n} of 3`, "aria-label": `impact ${n} of 3` }, "●".repeat(n) + "○".repeat(3 - n));
}

function hzExpect(x) {
  if (x.median != null) {
    const v = x.unit === "k" ? `${Math.round(x.median)}k`
      : x.unit === "%" ? `${x.signed === false ? x.median.toFixed(2) : hzSigned(x.median, 2)}%` : fmt(x.median, 2);
    return `${x.name}: market median ${v}`;
  }
  if (x.outcomes) return `${x.outcomes.map(([t, p]) => `${t} ${hzPct(p)}`).join(" · ")}`;
  if (x.text) return `${x.name} ${x.text}`;
  return null;
}

function hzTags(tags) {
  const box = el("div", { class: "hz-tags" });
  for (const t of tags || []) box.append(el("p", { class: `hz-tag tag-${t.key}` }, t.text));
  return box;
}

function hzEvent(ev, asOf) {
  const li = el("li", { class: "hz-ev" });
  const when = el("div", { class: "hz-when" });
  when.append(el("div", { class: "hz-day" }, hzDate(ev.date)), el("div", { class: "muted" }, hzIn(ev.date, asOf)));
  const body = el("div", { class: "hz-body" });
  const title = el("div", { class: "hz-title" });
  title.append(el("strong", {}, ev.name), hzImpact(ev.impact));
  const meta = [ev.time, ev.period, ev.company && ev.company !== ev.name ? ev.company : null].filter(Boolean).join(" · ");
  if (meta) title.append(el("span", { class: "muted" }, meta));
  body.append(title);
  for (const x of ev.expect || []) {
    const t = hzExpect(x);
    if (t) body.append(el("div", { class: "hz-expect" }, t));
  }
  if (ev.note) body.append(el("div", { class: "hz-note" }, ev.note));
  body.append(hzTags(ev.tags));
  const nums = el("div", { class: "hz-nums" });
  const via = ev.asset && ev.ticker !== ev.asset ? ` (${ev.asset})` : "";
  if (ev.implied) nums.append(el("div", {}, `Options: ±${(ev.implied.move * 100).toFixed(1)}%${via} by ${ev.implied.expiry.slice(5)}`));
  if (ev.runup) {
    const r = ev.runup;
    nums.append(el("div", { class: r.r20 >= 0 ? "ret pos" : "ret neg" }, `20d ${pct(r.r20, 0)}${r.z20 != null ? ` (${hzSigned(r.z20, 1)}σ)` : ""}${via && !ev.implied ? via : ""}`));
  }
  li.append(when, body, nums);
  return li;
}

// One probability as a 90-day line on a fixed 0–100% scale, so a move looks as big as it is.
function hzSpark(hist) {
  const w = 120, h = 30;
  const s = svg("svg", { viewBox: `0 0 ${w} ${h}`, class: "hz-spark", "aria-hidden": "true" });
  s.append(svg("line", { x1: 0, x2: w, y1: h / 2, y2: h / 2, class: "hz-mid" }));
  if (hist && hist.length > 1) {
    const d = hist.map(([, p], i) => `${i ? "L" : "M"}${((i / (hist.length - 1)) * w).toFixed(1)},${((1 - p) * (h - 2) + 1).toFixed(1)}`).join("");
    s.append(svg("path", { d, class: "hz-line" }));
  }
  return s;
}

function hzChange(o, past, label) {
  const v = hzPts(o.p, past);
  if (v == null) return el("span", { class: "hz-chg muted" }, `${label} n/a`);
  const helps = o.good_if === "yes" ? v > 0 : o.good_if === "no" ? v < 0 : null;
  const cls = v === 0 || helps == null ? "muted" : helps ? "ret pos" : "ret neg";
  return el("span", { class: `hz-chg ${cls}` }, `${label} ${hzSigned(v)}`);
}

function hzMarket(m) {
  const card = el("article", { class: "hz-mkt" });
  const head = el("div", { class: "hz-title" });
  head.append(el("strong", {}, m.title), hzImpact(m.impact));
  const link = el("a", { href: m.url, target: "_blank", rel: "noopener", class: "muted" }, "Polymarket ↗");
  head.append(link);
  card.append(head);
  if (m.note) card.append(el("div", { class: "hz-note" }, m.note));
  for (const o of m.outcomes) {
    const row = el("div", { class: "hz-out" });
    const lone = m.outcomes.length === 1;
    const name = el("div", { class: "hz-oname" }, lone ? "" : o.label);
    if (o.good_if === "yes" || o.good_if === "no") {
      name.append(el("span", { class: "muted" }, `${lone ? "" : " · "}good for the book if ${o.good_if}`));
    }
    const chg = el("div", { class: "hz-chgs" });
    chg.append(hzChange(o, o.p1, "1d"), hzChange(o, o.p7, "7d"), hzChange(o, o.p30, "30d"));
    row.append(name, el("div", { class: "hz-p" }, hzPct(o.p)), hzSpark(o.hist), chg);
    card.append(row);
    if (o.tags?.length) card.append(hzTags(o.tags));
  }
  return card;
}

// The detail lines of the top card.
function hzSummary(d, events) {
  const ls = [];
  const say = (text, cls = "") => ls.push([text, cls]);
  const soon = events.filter((e) => e.impact >= 3 && dayNum(e.date) - dayNum(d.as_of) <= 14);
  if (soon.length) say(`Next two weeks: ${soon.length} high-impact date${soon.length === 1 ? "" : "s"}: ${soon.map((e) => `${e.name.replace(" results", "")} (${hzDate(e.date)})`).join(", ")}.`);

  const moves = [];
  for (const m of d.markets) for (const o of m.outcomes) {
    const v = hzPts(o.p, o.p7);
    if (v != null && Math.abs(v) >= 5) moves.push({ m, o, v });
  }
  moves.sort((a, b) => Math.abs(b.v) - Math.abs(a.v));
  if (moves.length) {
    say(`Biggest shifts this week: ${moves.slice(0, 3).map(({ m, o, v }) => `${m.title}${m.outcomes.length > 1 ? ` (${o.label})` : ""} ${hzSigned(v)} points to ${hzPct(o.p)}`).join("; ")}.`);
  }
  const tails = [], upside = [];
  for (const m of d.markets) for (const o of m.outcomes) for (const t of o.tags || []) {
    const name = `${m.title}${m.outcomes.length > 1 ? ` (${o.label})` : ""} ${hzPct(o.p)}`;
    if (t.key === "tail-bad" && m.impact >= 2) tails.push(name);
    if (t.key === "tail-good" && m.impact >= 2) upside.push(name);
  }
  if (upside.length) say(`Cheap upside the market doubts: ${upside.slice(0, 4).join("; ")}.`);
  if (tails.length) say(`Tail risks it dismisses: ${tails.slice(0, 4).join("; ")}.`);
  const a = d.assets || {};
  const tone = ["SPY", "QQQ", "SMH"].filter((k) => a[k]).map((k) => `${k} ${pct(a[k].r20, 0)} in 20 days, ${pct(a[k].from_high, 0)} from its high`);
  if (tone.length) say(`So far: ${tone.join(" · ")}.`, "note-line");
  say("Read the tags as questions, not calls: a priced-in outcome moves prices most when it fails to happen, and a date the market has front-run often reverses on the day.", "note-line");
  return ls;
}

export function render(Dx) {
  D = Dx;
  const d = D.horizon;
  const box = pageBox();

  const shown = d.scheduled.filter((e) => (hz.all || e.impact >= 2) && (!hz.range || dayNum(e.date) - dayNum(d.as_of) <= hz.range));
  box.replaceChildren(topCard(signal(D), SOURCES));

  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "Dated events"));
  sec.append(el("p", { class: "help" }, "These will happen; the question is the outcome. Macro expectations come from Kalshi's traded ranges, the options figure is the at-the-money straddle to the first expiry after the date (the move the options market prices in), and 20d is how far the exposed asset has run into it, in its own volatility units."));
  const next = d.scheduled.filter((e) => e.impact >= 3 && dayNum(e.date) >= dayNum(d.as_of))[0];
  const dv = el("div", { class: "v-lines" });
  dv.append(nowLine(next && dayNum(next.date) - dayNum(d.as_of) <= 3 ? "care" : "na", next ? hzIn(next.date, d.as_of) : "",
    next ? `Next high-impact date: ${next.name} on ${hzDate(next.date)}${next.implied ? `, options price ±${(next.implied.move * 100).toFixed(1)}%` : ""}.` : "No high-impact date ahead."));
  sec.append(dv);
  const ctl = chips(HZ_RANGES, hz.range, (r) => { hz.range = r; render(D); });
  const allBtn = el("button", { class: "chip", "aria-pressed": String(hz.all) }, "Every stock I track");
  allBtn.addEventListener("click", () => { hz.all = !hz.all; render(D); });
  ctl.append(allBtn);
  sec.append(ctl);
  const list = el("ol", { class: "hz-list" });
  for (const ev of shown) list.append(hzEvent(ev, d.as_of));
  if (!shown.length) list.append(el("li", { class: "muted" }, "Nothing in this window."));
  sec.append(list);
  box.append(sec);

  const sec2 = el("section", { class: "hz-sec" });
  sec2.append(el("h3", {}, "Could happen"));
  sec2.append(el("p", { class: "help" }, "Prices on Polymarket read as probabilities. The changes are in percentage points; green means the move helps a long AI and memory book. The line is the last 90 days on a 0–100% scale, with 50% marked."));
  const moves = [];
  for (const m of d.markets) for (const o of m.outcomes) { const v = hzPts(o.p, o.p7); if (v != null) moves.push({ m, o, v }); }
  moves.sort((a, b) => Math.abs(b.v) - Math.abs(a.v));
  const cv = el("div", { class: "v-lines" });
  const mv = moves[0];
  cv.append(nowLine("na", "", mv && Math.abs(mv.v) >= 5 ? `Biggest shift this week: ${mv.m.title}${mv.m.outcomes.length > 1 ? ` (${mv.o.label})` : ""} ${hzSigned(mv.v)} points to ${hzPct(mv.o.p)}.` : "No market moved 5 points or more this week."));
  sec2.append(cv);
  const order = Object.keys(HZ_THEMES);
  const themes = [...new Set(d.markets.map((m) => m.theme))].sort((a, b) => (order.indexOf(a) + 99) % 99 - (order.indexOf(b) + 99) % 99);
  for (const th of themes) {
    sec2.append(el("h4", {}, HZ_THEMES[th] || th));
    const grid = el("div", { class: "hz-grid" });
    for (const m of d.markets.filter((x) => x.theme === th)) grid.append(hzMarket(m));
    sec2.append(grid);
  }
  box.append(sec2);
}

export function signal(Dx) {
  const d = Dx.horizon, asOf = dayNum(d.as_of);
  const soon = d.scheduled.filter((e) => e.impact >= 2 && dayNum(e.date) - asOf <= 14);
  const macro = soon.filter((e) => e.kind !== "earnings" && e.impact >= 3);
  const earn = soon.filter((e) => e.kind === "earnings").sort((a, b) => (b.implied?.move ?? 0) - (a.implied?.move ?? 0));
  const parts = [];
  if (macro.length) parts.push(macro.map((e) => `${e.name} ${hzDate(e.date)}`).join(", "));
  if (earn.length) parts.push(`earnings: ${earn.slice(0, 8).map((e) => `${e.ticker} ${hzDate(e.date)}${e.implied?.move ? ` ±${fmt(100 * e.implied.move, 0)}%` : ""}`).join(", ")}`);
  const close = soon.some((e) => e.impact >= 3 && dayNum(e.date) - asOf <= 3);
  const n = soon.filter((e) => e.impact >= 3).length;
  return { area: "Calendar", level: close ? "care" : "na", state: n ? `${n} big date${n === 1 ? "" : "s"} in 2 weeks` : "Quiet",
    short: parts.join(" · ") || "Nothing high-impact scheduled in the next two weeks.",
    means: earn.length ? "The ± is the move options price in: a stop closer than that can be taken out by the report alone. Size positions in these names for a gap." : "A quiet calendar: no scheduled date that usually moves markets.",
    reading: parts.length ? `Next two weeks: ${parts.join(" · ")}.` : "", lines: hzSummary(d, d.scheduled.filter((e) => e.impact >= 2)).filter(([t]) => !t.startsWith("Next two weeks")) };
}
