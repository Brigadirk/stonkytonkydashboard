// Shared page furniture: the card on top of every tab, folding sections, tables and chips.
import { $, el, app, lsGet, lsSet, fmt, pct } from "./core.js";
import { freshness, whenText } from "./data.js";

export const LEVEL_WORD = { good: "good", care: "care", bad: "caution", na: "neutral" };

/**
 * The card on top of every tab: a coloured state, what it means for you, the numbers behind it,
 * then the tab's detail lines (first two shown, the rest one click away), and how fresh the data is.
 * sig: { level: good|care|bad|na, state, means, reading, lines: [text | [text, cls] | Node] }
 */
export function topCard(sig, sources) {
  const card = el("section", { class: `verdict top lv-${sig.level ?? "na"}` });
  const head = el("div", { class: "top-head" });
  head.append(el("span", { class: `state lv-${sig.level ?? "na"}` }, sig.state ?? ""), freshLine(sources));
  card.append(head);
  const means = el("p", { class: "top-means" }, sig.means ?? "");
  if (sig.extra) means.append(" ", sig.extra);
  card.append(means);
  const lines = el("div", { class: "v-lines" });
  if (sig.reading) lines.append(el("p", { class: "top-reading" }, sig.reading));
  for (const l of sig.lines ?? []) {
    if (l instanceof Node) lines.append(l);
    else if (Array.isArray(l)) lines.append(el("p", { class: l[1] ?? "" }, l[0]));
    else lines.append(el("p", {}, l));
  }
  card.append(lines);
  return card;
}

/** "Updated Tue 3 Nov, 23:48" per source; red when a nightly run should have refreshed it and did not. */
export function freshLine(sources) {
  const box = el("span", { class: "fresh" });
  const fs = (sources ?? []).map(freshness);
  const stale = fs.filter((f) => f.stale);
  if (!fs.length) return box;
  if (!stale.length) {
    const newest = fs.map((f) => f.when).filter(Boolean).sort((a, b) => b - a)[0];
    box.textContent = `Updated ${whenText(newest)}`;
    box.title = fs.map((f) => `${f.label}: ${whenText(f.when)}`).join("\n");
  } else {
    box.classList.add("stale");
    box.textContent = `Not updated: ${stale.map((f) => `${f.label} (last ${whenText(f.when)})`).join(", ")}`;
    box.title = "The last nightly run did not refresh this. The numbers are from the date shown.";
  }
  return box;
}

export const staleAny = (sources) => (sources ?? []).some((s) => freshness(s).stale);

/** The first line of a section: a coloured state word and the reading, visible while the section is folded. */
export function nowLine(level, state, text) {
  const p = el("p", { class: "now" });
  if (state) p.append(el("span", { class: `state lv-${level ?? "na"}` }, state), " ");
  p.append(text);
  return p;
}

export function lines() {
  const box = el("div", { class: "v-lines" });
  const say = (text, cls = "") => { box.append(el("p", { class: cls }, text)); return box.lastChild; };
  return { box, say };
}

export function section(title, help, { id, cls = "hz-sec" } = {}) {
  const sec = el("section", { class: cls, ...(id ? { id } : {}) });
  sec.append(el("h3", {}, title));
  if (help) sec.append(el("p", { class: "help" }, help));
  return sec;
}

/** A table with a header row; columns from `numFrom` on are right-aligned. headers: [text | [text, tooltip]]. */
export function table(headers, { numFrom = 1, cls = "ps-table" } = {}) {
  const t = el("table", { class: cls });
  t.append(el("thead"), el("tbody"));
  const hr = el("tr");
  headers.forEach((h, i) => {
    const [text, tip] = Array.isArray(h) ? h : [h];
    hr.append(el("th", { class: i >= numFrom ? "num" : "", ...(tip ? { title: tip } : {}) }, text));
  });
  t.tHead.append(hr);
  return t;
}
export const scroll = (t) => { const s = el("div", { class: "ps-scroll" }); s.append(t); return s; };
/** A number cell, orange when stretched (at or above `hi`), blue when washed out (at or below `lo`). */
export function psCell(v, { digits = 1, pctFmt = false, hi = null, lo = null } = {}) {
  const td = el("td", { class: "num" }, v == null ? "n/a" : pctFmt ? pct(v, 0) : fmt(v, digits));
  if (v != null && hi != null && v >= hi) td.classList.add("ps-hot");
  if (v != null && lo != null && v <= lo) td.classList.add("ps-cold");
  return td;
}
export const numTd = (v, cls = "") => el("td", { class: `num ${cls}`.trim() }, v == null ? "n/a" : String(v));

/** A row of chips; `pick` runs with the chosen value. items: [[value, label]]. */
export function chips(items, current, pick) {
  const ctl = el("div", { class: "ranges" });
  for (const [v, label] of items) {
    const b = el("button", { class: "chip", "aria-pressed": String(current === v) }, label);
    b.addEventListener("click", () => pick(v));
    ctl.append(b);
  }
  return ctl;
}

// ---------- folding: the top card stays open, sections open on a click, method text on request ----------

// Each tab's main section starts open; everything else folds until clicked.
const FOLD_DEFAULT_OPEN = ["highlow:Brakes and tailwind", "markets:Rates as a source of volatility", "markets:Funding plumbing",
  "positioning:Index futures by trader type", "horizon:Dated events", "industry:Memory cycle: the makers' promises and the prices that test them",
  "industry:Korean discounts", "compute:Does it pay? Returns on the build-out", "compute:Who buys? Hyperscalers against everyone else",
  "compute:Who pays? Nvidia funding its own customers"];
const FOLD_KEY = "fold-open-v3";
const foldOpen = new Set((() => { try { return JSON.parse(lsGet(FOLD_KEY) ?? JSON.stringify(FOLD_DEFAULT_OPEN)); } catch { return FOLD_DEFAULT_OPEN; } })());

// Why each section is worth opening, in one line under its heading. Keyed by tab and heading start.
const WHY = {
  highlow: {
    "Brakes and tailwind": "Each condition that made past dips worse or better buys, and whether it is on now.",
    "Closest past dips": "The past dip days most like today, and what followed each.",
    "Nasdaq: fear with rising estimates": "When tech is scared but analysts keep raising numbers: what QQQ did next since 2006.",
    "S&P 500 washout score": "How washed out the index is, and what such readings returned afterwards.",
    "Sector washouts": "Which sectors are washed out, and which setups have had an edge.",
    "Breadth": "Whether most stocks join the move: turns from below zero have marked good entries.",
    "New highs and lows today": "Who is breaking out and who is breaking down, by name.",
    "Signal record since 1991": "The record of each highs-and-lows signal: how much it paid and how often.",
    "History": "The highs-and-lows signals over time against the S&P 500.",
  },
  positioning: {
    "Index futures by trader type": "Who is long or short S&P and Nasdaq futures: crowded sides unwind hardest.",
    "Volatility and hedging": "How much fear is priced in: spikes that fade on down days mark exhaustion.",
    "Margin debt": "Borrowed money in the market: high levels turn falls into forced selling.",
    "Korean retail margin": "Leverage behind the KOSPI and your Korean memory names.",
    "Stocks: long and short crowding": "Your names that are crowded long (fragile) or short (squeeze fuel).",
    "Rotation out of AI": "Pods de-grossing look like a rotation: whether it is on, and what chips did after past ones.",
    "Short-sale volume": "Daily short selling in one name: rising shorting into a fall is pressure, falling is relief.",
  },
  horizon: {
    "Dated events": "What is scheduled and how big a move the options market prices in.",
    "Could happen": "Prediction-market odds for the big unknowns, and how they moved.",
  },
  markets: {
    "Rates as a source of volatility": "Bond swings and bonds that stop hedging push every risk model to cut stocks.",
    "Funding plumbing": "Whether the overnight money behind all leverage is getting scarce.",
    "Rates and credit spreads": "Rising long rates hurt richly valued growth first; widening spreads mean lenders smell trouble.",
    "Oil shipping through the chokepoints": "The physical side of the oil price: tankers through Hormuz and the other straits.",
    "Price board": "Indexes, currencies, commodities and crypto: where each stands against its year.",
  },
  compute: {
    "Everything in one chart": "Every demand measure on one scale: are they still rising together?",
    "Does it pay?": "Whether the spending earns money: if it stops paying, the capex gets cut.",
    "Who pays?": "How much of the demand Nvidia pays for itself: the part that vanishes if its customers stumble.",
    "Who buys?": "Whether demand is broadening beyond the four big clouds: growth after 2027 needs it.",
    "What the companies themselves said": "Usage and revenue figures straight from the labs and clouds.",
    "Capex and backlog": "The spending that is your AI names' revenue, and the contracts behind it.",
    "Tokens on OpenRouter": "Developer usage by model maker: a fast but partial read on AI demand.",
  },
  industry: {
    "Memory cycle": "Whether the memory makers' promises hold, against the spot prices that turned first at earlier tops.",
    "Memory spot prices": "DRAM and NAND prices lead your memory names' earnings by a quarter or two.",
    "GPU rental prices": "What an hour of GPU costs: falling prices would mean compute is no longer scarce.",
    "Korean discounts": "Cheaper ways to own SK hynix and Samsung: worth it when the gap is wide.",
  },
};
const whyFor = (page, title) => Object.entries(WHY[page] ?? {}).find(([k]) => title.startsWith(k))?.[1];

function foldSections(root) {
  root.querySelectorAll("section").forEach((sec) => {
    if (sec.dataset.fold) return;
    sec.dataset.fold = "1";
    if (sec.classList.contains("verdict")) return clipVerdict(sec);
    const h = sec.querySelector(":scope > h3");
    if (!h) return;
    sec.classList.add("fold");
    const title = h.textContent.trim(), key = `${app.page}:${title}`;
    const why = whyFor(app.page, title);
    if (why) h.after(el("p", { class: "why" }, why));
    if (foldOpen.has(key)) sec.classList.add("open");
    h.tabIndex = 0;
    h.setAttribute("role", "button");
    const toggle = () => {
      const open = sec.classList.toggle("open");
      if (open) foldOpen.add(key); else foldOpen.delete(key);
      lsSet(FOLD_KEY, JSON.stringify([...foldOpen]));
    };
    h.addEventListener("click", toggle);
    h.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); }
    });
  });
}

// Cards show their first two lines; the rest one click away.
function clipVerdict(card) {
  const ls = [...card.querySelectorAll(":scope > .v-lines > p:not(.note-line)")];
  if (ls.length <= 2) return;
  card.classList.add("clip");
  const more = el("button", { class: "v-more" }, `${ls.length - 2} more`);
  more.addEventListener("click", () => {
    const shut = card.classList.toggle("clip");
    more.textContent = shut ? `${ls.length - 2} more` : "less";
  });
  card.append(more);
}

export function initUi() {
  new MutationObserver(() => foldSections($("#pagebody"))).observe($("#pagebody"), { childList: true, subtree: true });
  const btn = $("#explain");
  const setExplain = (on) => {
    document.body.classList.toggle("explain", on);
    btn.setAttribute("aria-pressed", String(on));
    lsSet("explain", on ? "1" : "0");
  };
  btn.addEventListener("click", () => setExplain(!document.body.classList.contains("explain")));
  setExplain(lsGet("explain") === "1");
}
