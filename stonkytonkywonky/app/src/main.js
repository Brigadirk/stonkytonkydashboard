// StonkyTonkyWonky: the tabs and the router. Each tab lives in its own module.
import { $, el, app } from "./core.js";
import { allData } from "./data.js";
import { initUi, freshLine, staleAny } from "./ui.js";
import * as signals from "./signals.js";
import * as valuation from "./valuation.js";
import * as dips from "./dips.js";
import * as macro from "./macro.js";
import * as positioning from "./positioning.js";
import * as calendar from "./calendar.js";
import * as ai from "./ai.js";
import * as memory from "./memory.js";

// The menu label is the page title; `sub` is the question the tab answers.
const TABS = [
  { key: "signals", label: "Signals", sub: "What each area says now, and what it means for you", mod: signals, sources: [] },
  { key: "valuation", label: "Valuation", sub: "Each stock's forward P/E against its own history", mod: null, sources: ["ranking"] },
  { key: "highlow", label: "Dips", sub: "Is this dip buyable? The verdict, and everything behind it", mod: dips, sources: dips.SOURCES },
  { key: "markets", label: "Macro", sub: "Bond volatility, funding, rates, credit and oil: the brakes on buying a dip", mod: macro, sources: macro.SOURCES },
  { key: "positioning", label: "Positioning", sub: "Who has already sold and who could still sell", mod: positioning, sources: positioning.SOURCES },
  { key: "horizon", label: "Calendar", sub: "Which dates can move your stocks, and how much the options market expects", mod: calendar, sources: calendar.SOURCES },
  { key: "compute", label: "AI build-out", sub: "Is the AI build-out still growing, who is paying, and does it earn money?", mod: ai, sources: ai.SOURCES },
  { key: "industry", label: "Memory & GPUs", sub: "Memory and GPU prices, and the cheaper ways to own the Korean memory names", mod: memory, sources: memory.SOURCES },
];
const TAB = Object.fromEntries(TABS.map((t) => [t.key, t]));
// Links from tabs that were merged into others.
const MOVED = { market: "highlow", ai: "compute", breadth: "highlow", discounts: "industry" };

function buildNav() {
  const nav = $("nav.tabs");
  const explain = $("#explain");
  for (const t of TABS) {
    const b = el("button", { class: "tab", "data-page": t.key, title: t.sub }, t.label);
    b.addEventListener("click", () => showPage(t.key));
    nav.insertBefore(b, explain);
  }
}

async function showPage(name) {
  name = MOVED[name] ?? name;
  if (!(name in TAB)) name = "valuation";
  app.page = name;
  const tab = TAB[name], onValuation = name === "valuation";
  document.querySelectorAll(".tab").forEach((t) => {
    if (t.dataset.page === name) t.setAttribute("aria-current", "page");
    else t.removeAttribute("aria-current");
  });
  $("main.layout").hidden = !onValuation;
  $("#valuation-controls").hidden = !onValuation;
  $("#foot").hidden = !onValuation;
  $("#page").hidden = onValuation;
  const sub = $("#asof");
  sub.replaceChildren(onValuation ? valuation.state.asof ?? tab.sub : tab.sub);
  if (onValuation) sub.append(" · ", freshLine(["ranking"]));
  const url = new URL(location.href);
  if (onValuation) url.searchParams.delete("page");
  else {
    url.searchParams.set("page", name);
    url.searchParams.delete("t");
  }
  history.replaceState(null, "", url);
  if (onValuation) return;
  $("#pagebody").replaceChildren(el("p", { class: "empty" }, "Loading…"));
  const D = await allData();
  if (app.page !== name) return;
  try {
    tab.mod.render(D);
  } catch (e) {
    console.error(e);
    $("#pagebody").replaceChildren(el("p", { class: "empty" }, `This tab could not be drawn from tonight's data (${e.message}). The nightly log for its script says why.`));
  }
}
app.go = showPage;

async function boot() {
  buildNav();
  initUi();
  const D = await allData();
  for (const t of TABS) if (staleAny(t.sources)) document.querySelector(`.tab[data-page="${t.key}"]`)?.classList.add("stale");
  const params = new URLSearchParams(location.search);
  const wanted = params.get("t");
  const asked = wanted === "$NYSI" ? "breadth" : params.get("page"); // old links used t=$NYSI
  // No page and no ticker in the link: open on Signals; a ticker link opens its valuation.
  const page = asked in TAB || asked in MOVED ? asked : wanted ? "valuation" : "signals";
  if (D.ranking) {
    await valuation.loadRanking(D.ranking);
    const first = valuation.state.rows.find((r) => r.ticker === wanted) || valuation.visibleRows()[0];
    if (first) await valuation.select(first.ticker, { keepPage: page !== "valuation" });
    if (params.get("view") === "list") valuation.setExpanded(true);
  }
  await showPage(page);
}
boot();
