const SVG = "http://www.w3.org/2000/svg";
const DAY = 864e5;

// Time windows whose forward P/E range each stock is compared against.
const WINDOWS = [
  { key: "90d", days: 90, label: "Last 90 days" },
  { key: "180d", days: 180, label: "Last 6 months" },
  { key: "1Y", days: 365, label: "Last year" },
  { key: "2Y", days: 730, label: "Last 2 years" },
  { key: "3Y", days: 1095, label: "Last 3 years" },
  { key: "4Y", days: 1461, label: "Last 4 years" },
  { key: "5Y", days: 1826, label: "Last 5 years" },
];
const MAIN_WINDOW = "3Y"; // the window the list and the verdict use
// Recent listings and newly profitable companies lack 3 years; judge them on the longest window they have.
const FALLBACK = ["3Y", "2Y", "1Y", "180d", "90d"];
// The cheap/expensive flag leans on the recent past: a weighted blend of three windows.
const FLAG_BLEND = [["90d", 0.6], ["180d", 0.2], ["1Y", 0.2]];
const FLAG_SPAN = "a blend of the last 90 days (60%), 180 days (20%) and year (20%)";

/** σ and percentile of today's P/E, blended over FLAG_BLEND; weights rescale when a window is missing. */
function flagBlend(r) {
  const have = FLAG_BLEND.filter(([k]) => r.corridors?.[k]?.sigma != null);
  if (!have.length) return { sigma: null, pct: null };
  const w = have.reduce((a, [, x]) => a + x, 0);
  const avg = (f) => have.reduce((a, [k, x]) => a + r.corridors[k][f] * x, 0) / w;
  return { sigma: avg("sigma"), pct: avg("pct") };
}

// Seven valuation zones on the σ-equivalent scale (levels are read off percentiles).
const ZONES = [
  { key: "c3", upTo: -2, label: "Extremely cheap", side: "cheap" },
  { key: "c2", upTo: -1.5, label: "Very cheap", side: "cheap" },
  { key: "c1", upTo: -1, label: "Cheap", side: "cheap" },
  { key: "n", upTo: 1, label: "Normal", side: "normal" },
  { key: "e1", upTo: 1.5, label: "Expensive", side: "rich" },
  { key: "e2", upTo: 2, label: "Very expensive", side: "rich" },
  { key: "e3", upTo: Infinity, label: "Extremely expensive", side: "rich" },
];
const LEVELS = ["2", "1.5", "1", "0", "-1", "-1.5", "-2"];
const LEVEL_NAME = {
  "2": "Extremely expensive above",
  "1.5": "Very expensive above",
  "1": "Expensive above",
  "0": "Typical",
  "-1": "Cheap below",
  "-1.5": "Very cheap below",
  "-2": "Extremely cheap below",
};

// Direction of analysts' forecast for next financial year over the last 90 days.
const REVS = {
  up2: { icon: "↑↑", label: "Rising steadily", short: "Keeps rising", tone: "up" },
  up1: { icon: "↑", label: "Rising", short: "Rising", tone: "up" },
  flat: { icon: "→", label: "Flat", short: "Flat", tone: "flat" },
  down1: { icon: "↓", label: "Falling", short: "Falling", tone: "down" },
  down2: { icon: "↓↓", label: "Falling steadily", short: "Keeps falling", tone: "down" },
};

// Combined ranking: each criterion is the stock's position among all stocks (100 = best),
// so outliers like +400% growth can't dominate; the score is the plain average.
const CRITERIA = [
  { key: "rel", better: "high", label: "Cheap compared with other stocks", explain: (r) => `${r.rel.toFixed(0)}/100 on the "vs others" score` },
  { key: "growth", better: "high", label: "Expected profit growth", explain: (r) => `${pct(r.growth, 0)} next 12 months vs last 12` },
  { key: "rev90", better: "high", label: "Forecasts being raised", explain: (r) => `next-year forecast ${pct(r.rev90)} in 90 days` },
  { key: "r_mid", better: "high", label: "Upside if valued at its typical level", explain: (r) => `${pct(r.r_mid, 0)} in a year` },
];

const RANGES = [
  { label: "1Y", days: 365 },
  { label: "3Y", days: 1095 },
  { label: "5Y", days: 1826 },
  { label: "All", days: null },
];

const state = {
  rows: [],
  query: "",
  sort: { key: "score", dir: -1 },
  selected: null,
  window: MAIN_WINDOW,
  range: 1095,
  expanded: false,
};
const $ = (sel) => document.querySelector(sel);

function el(tag, attrs = {}, text) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (text !== undefined) node.textContent = text;
  return node;
}
function svg(tag, attrs = {}) {
  const node = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
}
const fmt = (v, d = 1) => (v == null || !Number.isFinite(v) ? "n/a" : v.toFixed(d));
const pct = (v, d = 1) => (v == null ? "n/a" : `${v >= 0 ? "+" : ""}${(v * 100).toFixed(d)}%`);
const money = (v, ccy) => (v == null || !Number.isFinite(v) ? "n/a" : `${v >= 1000 ? v.toFixed(0) : v.toFixed(2)} ${ccy || ""}`.trim());
const dayNum = (iso) => Math.round(Date.parse(iso) / DAY);
const isoOf = (n) => new Date(n * DAY).toISOString().slice(0, 10);
const zoneOf = (sigma) => (sigma == null ? null : ZONES.find((z) => sigma <= z.upTo));
const windowOf = (key) => WINDOWS.find((w) => w.key === key);
const spanOf = (key) => windowOf(key).label.replace(/^Last /, "the last ").replace("the last year", "the last year");

function ordinal(n) {
  const tail = n % 100 >= 11 && n % 100 <= 13 ? "th" : ["th", "st", "nd", "rd"][n % 10] || "th";
  return `${n}${tail}`;
}

function revBadge(rv, short = false) {
  const info = rv ? REVS[rv.category] : null;
  const span = el("span", { class: `rev rev-${info ? info.tone : "na"}` });
  if (!info) {
    span.textContent = "n/a";
    return span;
  }
  span.append(el("span", { class: "rev-icon", "aria-hidden": "true" }, info.icon), document.createTextNode(short ? info.short : info.label));
  return span;
}

function zoneBadge(zone, big = false) {
  const span = el("span", { class: `zone zone-${zone ? zone.key : "na"}${big ? " big" : ""}` });
  span.append(el("span", { class: "dot", "aria-hidden": "true" }), document.createTextNode(zone ? zone.label : "No history yet"));
  return span;
}

async function load() {
  const res = await fetch("data/ranking.json", { cache: "no-store" });
  const data = await res.json();
  const rows = data.rows
    .filter((r) => !r.missing)
    .map((r) => ({
      ...r,
      mainKey: FALLBACK.find((k) => r.corridors?.[k]) ?? null,
    }))
    .map((r) => ({
      ...r,
      sig3: flagBlend(r).sigma,
      pctMain: flagBlend(r).pct,
      ...targets(r),
      rev90: r.revisions?.change_90d ?? null,
      fy27: r.fy_eps?.FY2027?.eps ?? null,
      fy28: r.fy_eps?.FY2028?.eps ?? null,
    }));
  state.rows = scoreRows(rows);
  state.asof = `Each stock's price-to-earnings compared with its own past · data as of ${data.as_of} · ${state.rows.length} stocks`;
  $("#asof").textContent = state.asof;
  renderTable();
  const params = new URLSearchParams(location.search);
  const wanted = params.get("t");
  const first = state.rows.find((r) => r.ticker === wanted) || visibleRows()[0];
  const page = wanted === BREADTH ? "breadth" : params.get("page"); // old links used t=$NYSI
  if (first) await select(first.ticker, { keepPage: PAGES[page] });
  if (params.get("view") === "list") setExpanded(true);
  if (PAGES[page]) await showPage(page);
}

// ---------- sections: valuation is the list and detail; the others get the full width ----------

const PAGES = {
  valuation: null,
  breadth: () => showBreadth(),
  highlow: () => showHighLow(),
  positioning: () => showPositioning(),
  horizon: () => showHorizon(),
  markets: () => showMarkets(),
  industry: () => showIndustry(),
  compute: () => showCompute(),
  discounts: () => showDiscounts(),
};

async function showPage(name) {
  if (!(name in PAGES)) name = "valuation";
  const onValuation = name === "valuation";
  document.querySelectorAll(".tab").forEach((t) => {
    if (t.dataset.page === name) t.setAttribute("aria-current", "page");
    else t.removeAttribute("aria-current");
  });
  $("main.layout").hidden = !onValuation;
  $("#valuation-controls").hidden = !onValuation;
  $("#foot").hidden = !onValuation;
  $("#page").hidden = onValuation;
  $("#asof").textContent = PAGE_SUBS[name] ?? state.asof ?? "";
  const url = new URL(location.href);
  if (onValuation) url.searchParams.delete("page");
  else {
    url.searchParams.set("page", name);
    url.searchParams.delete("t");
  }
  history.replaceState(null, "", url);
  if (!onValuation) await PAGES[name]();
}
const pageBox = () => $("#pagebody");
const PAGE_SUBS = {
  breadth: "How many NYSE stocks take part in the move",
  highlow: "How washed out the market and each sector are, and when that was a time to buy",
  positioning: "Who is already leaning which way",
  horizon: "What the market is waiting for, and how far it has run ahead",
  markets: "The reference frame: indexes, rates, credit, currencies, commodities",
  industry: "Oil shipping, memory spot prices and GPU rental prices",
  compute: "How much AI compute the world uses and pays for, and who uses it",
  discounts: "Holding companies against their stakes, preferred against common shares",
};

// ---------- list ----------

// ---------- cheap compared with other stocks ----------

const PEG_GROWTH_CAP = 0.5; // one-year rebounds from near-zero profit would otherwise look endlessly cheap
const PEG_GROWTH_MIN = 0.03;
const MIN_PEERS = 5;

/** Percentile position (0–100) of each row's value among `pool`; `low` means lower is better. */
function positions(pool, key, low) {
  const sorted = [...pool].sort((a, b) => a[key] - b[key]);
  const out = new Map();
  sorted.forEach((r, i) => {
    const up = sorted.length > 1 ? (i / (sorted.length - 1)) * 100 : 50;
    out.set(r.ticker, low ? 100 - up : up);
  });
  return out;
}

/**
 * "Cheap vs others", 0–100 (100 = cheapest): the average of forward P/E against all stocks,
 * forward P/E against industry peers (sector when the industry is too small), and
 * P/E relative to growth (PEG). Share classes after the first don't count as extra peers.
 */
function addRelative(rows) {
  // Sales-valued loss-makers carry P/S in `pe`; comparing that with other stocks' P/E would be nonsense.
  const priced = rows.filter((r) => r.pe > 0 && r.metric !== "ps");
  const firstOfCompany = new Map();
  for (const r of priced) if (!firstOfCompany.has(r.company || r.ticker)) firstOfCompany.set(r.company || r.ticker, r);
  const pool = [...firstOfCompany.values()];
  const vsAll = positions(priced, "pe", true);

  for (const r of priced) {
    const g = r.growth;
    r.peg = g != null && g >= PEG_GROWTH_MIN ? r.pe / (Math.min(g, PEG_GROWTH_CAP) * 100) : null;
    // The usual PEG, shown in the list; only the ranking uses the capped version above.
    r.pegRaw = g != null && g > 0 ? r.pe / (g * 100) : null;
  }
  const vsPeg = positions(priced.filter((r) => r.peg != null), "peg", true);

  const groups = new Map();
  for (const r of pool) {
    for (const [level, name] of [["industry", r.industry], ["sector", r.sector]]) {
      if (!name) continue;
      const k = `${level}:${name}`;
      if (!groups.has(k)) groups.set(k, []);
      groups.get(k).push(r);
    }
  }
  for (const r of priced) {
    const ind = groups.get(`industry:${r.industry}`) || [];
    const sec = groups.get(`sector:${r.sector}`) || [];
    const [level, peers] = ind.length >= MIN_PEERS ? ["industry", ind] : sec.length >= MIN_PEERS ? ["sector", sec] : [null, []];
    let vsPeers = null;
    if (level) {
      const withSelf = peers.some((p) => p.ticker === r.ticker) ? peers : [...peers, r];
      vsPeers = positions(withSelf, "pe", true).get(r.ticker);
      r.peerGroup = { level, name: level === "industry" ? r.industry : r.sector, size: peers.length,
        cheaper: withSelf.filter((p) => p.pe > r.pe).length, median: median(peers.map((p) => p.pe)) };
    }
    r.relParts = { all: vsAll.get(r.ticker), peers: vsPeers, peg: vsPeg.get(r.ticker) ?? null };
    const have = Object.values(r.relParts).filter((v) => v != null);
    r.rel = have.reduce((a, b) => a + b, 0) / have.length;
  }
}

function median(xs) {
  const s = [...xs].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

function scoreRows(rows) {
  addRelative(rows);
  const valid = {
    rel: (r) => r.rel != null,
    growth: (r) => r.growth != null,
    rev90: (r) => r.rev90 != null,
    r_mid: (r) => r.r_mid != null,
  };
  const ranks = {};
  for (const c of CRITERIA) {
    const pool = rows.filter(valid[c.key]).sort((a, b) => a[c.key] - b[c.key]);
    ranks[c.key] = new Map(pool.map((r, i) => {
      const up = pool.length > 1 ? (i / (pool.length - 1)) * 100 : 50;
      return [r.ticker, c.better === "low" ? 100 - up : up];
    }));
  }
  // One company, one ranking slot: of several share classes, only the cheapest (lowest P/E) is ranked.
  const cheapest = new Map();
  for (const r of rows) {
    const k = r.company || r.ticker;
    const best = cheapest.get(k);
    if (r.pe > 0 && (!best || r.pe < best.pe)) cheapest.set(k, r);
  }
  const scored = rows.map((r) => {
    const parts = Object.fromEntries(CRITERIA.map((c) => [c.key, ranks[c.key].get(r.ticker) ?? null]));
    const have = Object.values(parts).filter((v) => v != null);
    const best = cheapest.get(r.company || r.ticker);
    const rankedVia = best && best.ticker !== r.ticker ? best.ticker : null;
    const score = !rankedVia && have.length >= 3 ? have.reduce((a, b) => a + b, 0) / have.length : null;
    return { ...r, parts, score, rankedVia };
  });
  const ordered = scored.filter((r) => r.score != null).sort((a, b) => b.score - a.score);
  ordered.forEach((r, i) => (r.rank = i + 1));
  return Object.assign(scored, { rankedOf: ordered.length });
}

/** Price in a year at the −1σ, median and +1σ P/E of the stock's main window, and the return from today. */
function targets(r) {
  const c = r.corridors?.[r.mainKey];
  if (!c || !(r.eps > 0) || !r.price) return {};
  const eps1 = epsAhead(r, 365);
  const at = (k) => c.levels[k] * eps1;
  const t_lo = at("-1"), t_mid = at("0"), t_hi = at("1");
  return {
    t_lo, t_mid, t_hi,
    r_lo: t_lo / r.price - 1,
    r_mid: t_mid / r.price - 1,
    r_hi: t_hi / r.price - 1,
  };
}

function retCell(v) {
  return el("td", { class: `num xcol ret ${v == null ? "" : v >= 0 ? "pos" : "neg"}` }, v == null ? "n/a" : pct(v, 0));
}

function visibleRows() {
  const q = state.query.trim().toLowerCase();
  const { key, dir } = state.sort;
  return state.rows
    .filter((r) => !q || r.ticker.toLowerCase().includes(q) || (r.name || "").toLowerCase().includes(q))
    .sort((a, b) => {
      const av = a[key], bv = b[key];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      return (typeof av === "string" ? av.localeCompare(bv) : av - bv) * dir;
    });
}

/** Profit growth vs the last 12 months; a loss there has no percentage, so say which way it goes. */
function growthText(r, g, ahead, twoYears) {
  const gaap = r.ttm_basis && r.ttm_basis !== "adjusted" ? " Last 12 months from Yahoo's GAAP figure, which can include one-offs." : "";
  const yearly = twoYears && g != null ? ` (${pct(Math.sqrt(1 + g) - 1, 0)} a year)` : "";
  const guess = twoYears && r.extrapolated_24m ? " Includes an extrapolated year (no forecast found): growth assumed to halve." : "";
  if (g != null) return { text: `${twoYears && r.extrapolated_24m ? "≈" : ""}${pct(g, 0)}`, title: `${pct(g, 0)}${yearly}.${gaap}${guess}`, muted: !!guess };
  if (r.ttm_loss) return ahead != null && ahead > 0
    ? { text: "from loss", title: `Loss over the last 12 months, profit expected${twoYears ? " in months 13–24" : ""}.${guess}`, muted: false }
    : { text: "loss", title: "Loss over the last 12 months and still expected.", muted: false };
  if (ahead != null && ahead <= 0) return { text: "to loss", title: "A loss is expected.", muted: false };
  return { text: "n/a", title: r.ttm_basis == null ? "No profit figure for the last 12 months" : "No forecast that far out", muted: false };
}

function growthCell(r, g, ahead, twoYears) {
  const t = growthText(r, g, ahead, twoYears);
  return el("td", { class: `num${t.muted ? " chained" : ""}`, title: t.title }, t.text);
}

/** Consensus EPS for one fiscal year; chained years (from another source's growth rate) are marked ~. */
function fyCell(r, fy) {
  const f = r.fy_eps?.[fy];
  if (!f) return el("td", { class: "num", title: "No forecast for this fiscal year" }, "n/a");
  const chained = !f.source.startsWith("Yahoo consensus");
  const v = Math.abs(f.eps) >= 1000 ? f.eps.toFixed(0) : f.eps.toFixed(2);
  return el("td", { class: `num${chained ? " chained" : ""}`, title: `${fy}: ${f.source}` }, `${f.extrapolated ? "≈" : chained ? "~" : ""}${v}`);
}

function renderTable() {
  const tbody = $("#table tbody");
  tbody.replaceChildren();
  for (const r of visibleRows()) {
    const tr = el("tr", { "aria-selected": String(r.ticker === state.selected), tabindex: "0" });
    const tick = el("td");
    tick.append(el("strong", {}, r.ticker), el("span", { class: "name" }, r.name || ""));
    const scoreTd = el("td", { class: "num score", title: r.rankedVia ? `Ranked via ${r.rankedVia}` : "" },
      r.rankedVia ? `→ ${r.rankedVia}` : r.score == null ? "n/a" : r.score.toFixed(0));
    const relTd = el("td", { class: "num", title: "Cheap compared with other stocks, 0–100 (100 = cheapest)" },
      r.rel == null ? "n/a" : r.rel.toFixed(0));
    const val = el("td", { class: "val" });
    val.append(zoneBadge(zoneOf(r.sig3)));
    if (r.mainKey && r.mainKey !== MAIN_WINDOW) {
      val.append(el("span", { class: "short-hist", title: `Only ${spanOf(r.mainKey)} of usable history` }, ` (${r.mainKey})`));
    }
    tr.append(
      tick,
      scoreTd,
      relTd,
      val,
      r.metric === "ps"
        ? el("td", { class: "num ps", title: "Loss-making: valued on sales. Trailing price ÷ sales; forward P/S in the panel" }, `P/S ${fmt(r.pe, 2)}`)
        : el("td", { class: "num" }, r.pe == null || r.pe <= 0 ? "n/m" : fmt(r.pe)),
      el("td", { class: "num" }, r.trailing_pe == null ? "n/m" : fmt(r.trailing_pe)),
      el("td", { class: "num" }, r.pb == null ? "n/m" : fmt(r.pb, 1)),
      el("td", { class: "num", title: r.fcf_negative ? "Free cash flow is negative" : r.fcf_basis ? `Free cash flow over the ${r.fcf_basis} to ${r.fcf_end}` : "" },
        r.ev_fcf == null ? (r.fcf_negative ? "neg" : "n/a") : fmt(r.ev_fcf)),
      growthCell(r, r.growth, r.metric === "ps" ? r.fy1_eps : r.eps, false),
      growthCell(r, r.growth_24m, r.eps_24m, true),
      el("td", { class: "num", title: r.pegRaw == null ? "Growth is zero or negative, so PEG has no meaning" : "" },
        r.pegRaw == null ? "n/m" : fmt(r.pegRaw, 2)),
      fyCell(r, "FY2027"),
      fyCell(r, "FY2028"),
      (() => { const td = el("td"); td.append(revBadge(r.revisions, true)); return td; })(),
      el("td", { class: "num xcol" }, r.pctMain == null ? "n/a" : ordinal(Math.round(r.pctMain))),
      el("td", { class: "num xcol" }, money(r.price, r.currency)),
      el("td", { class: "num xcol group-start" }, money(r.t_lo, "")),
      retCell(r.r_lo),
      el("td", { class: "num xcol group-start" }, money(r.t_mid, "")),
      retCell(r.r_mid),
      el("td", { class: "num xcol group-start" }, money(r.t_hi, "")),
      retCell(r.r_hi),
    );
    tr.onclick = () => {
      if (state.expanded) setExpanded(false);
      select(r.ticker);
    };
    tr.onkeydown = (e) => e.key === "Enter" && select(r.ticker);
    tbody.append(tr);
  }
  document.querySelectorAll("#table th[data-sort]").forEach((th) => {
    const key = th.dataset.sort;
    th.setAttribute("aria-sort", key === state.sort.key ? (state.sort.dir > 0 ? "ascending" : "descending") : "none");
    th.onclick = () => {
      state.sort = { key, dir: state.sort.key === key ? -state.sort.dir : 1 };
      renderTable();
    };
  });
}

async function select(ticker, { keepPage = false } = {}) {
  state.selected = ticker;
  if (!keepPage) {
    const url = new URL(location.href);
    url.searchParams.set("t", ticker);
    history.replaceState(null, "", url);
  }
  renderTable();
  const row = state.rows.find((r) => r.ticker === ticker);
  let series = null;
  try {
    const res = await fetch(`data/series/${encodeURIComponent(ticker)}.json`, { cache: "no-store" });
    if (res.ok) series = await res.json();
  } catch {
    series = null;
  }
  renderDetail(row, series);
}

// ---------- detail ----------

function renderDetail(row, series) {
  const box = $("#detail");
  box.replaceChildren();
  const head = el("div", { class: "d-head" });
  head.append(el("h2", {}, `${row.name || row.ticker}`), el("div", { class: "d-sub" }, `${row.ticker} · ${money(row.price, row.currency)} · data as of ${row.as_of}`));
  box.append(head, verdictCard(row), scoreCard(row), relativeCard(row));
  if (DC_TICKERS[row.ticker]) {
    const link = el("a", { href: "?page=discounts" }, "Discounts tab");
    link.addEventListener("click", (e) => { e.preventDefault(); showPage("discounts"); });
    const p = el("p", { class: "help" }, `${DC_TICKERS[row.ticker]} See its discount over time in the `);
    p.append(link, document.createTextNode("."));
    box.append(p);
  }

  if (row.pe == null || row.pe <= 0) {
    box.append(el("p", { class: "plain" }, "This company is expected to lose money over the next 12 months, so its price can't be compared with its earnings. There is nothing to rank."));
    box.append(detailsSection(row, series));
    return;
  }
  if (!row.corridors?.[state.window] && row.mainKey) state.window = row.mainKey;
  box.append(gaugeSection(row));
  if (row.notes) box.append(notesSection(row));
  if (row.revisions) box.append(revisionSection(row));
  if (row.analysts) box.append(analystSection(row));
  if (row.targets) box.append(targetsSection(row));
  if (series && series.dates.length > 1 && row.corridors?.[state.window]) {
    box.append(priceSection(row, series));
  }
  box.append(detailsSection(row, series));
}

function verdictCard(row) {
  const main = row.sig3 == null ? null : { sigma: row.sig3, pct: row.pctMain };
  const span = FLAG_SPAN;
  const zone = zoneOf(main?.sigma);
  const card = el("section", { class: `verdict side-${zone ? zone.side : "na"}` });
  card.append(zoneBadge(zone, true));

  const lines = el("div", { class: "v-lines" });
  const say = (text, cls = "") => lines.append(el("p", { class: cls }, text));
  const name = row.name || row.ticker;

  if (row.pe == null || row.pe <= 0) {
    say(`${name} is expected to make a loss, so this screen has no view on it.`);
  } else if (!main) {
    say(`${name} doesn't have enough history yet to say whether it's cheap or expensive. The app records new data every weekday, so this fills in over time.`);
  } else {
    const p = Math.round(main.pct);
    const vs = p < 1
      ? `That's the cheapest it has been in ${span}.`
      : p > 99
        ? `That's the most expensive it has been in ${span}.`
        : p <= 50
          ? `That's cheaper than on ${100 - p}% of trading days in ${span}.`
          : `That's more expensive than on ${p}% of trading days in ${span}.`;
    if (row.metric === "ps") {
      say(`${name} is loss-making, so it's valued on sales instead of profit. You pay ${fmt(row.pe, 2)}× its sales over the last 12 months` +
        `${row.ps_forward ? ` (${fmt(row.ps_forward, 2)}× the sales ${row.rev_analysts || "the"} analysts expect over the next 12)` : ""}. ${vs}`);
      say("Sales multiples fall naturally as a young company grows, so a low reading against its own past is weaker evidence than a low P/E would be.", "note-line");
    } else {
      say(`You pay ${fmt(row.pe)}× the profit analysts expect over the next 12 months. ${vs}`);
    }
    if (row.mainKey !== MAIN_WINDOW) {
      say(`Note: there's only ${spanOf(row.mainKey)} of usable history (recent listing, or profits only recently turned positive), so its typical level and the price targets in a year compare with a shorter past than usual.`, "note-line");
    }
  }

  const rv = row.revisions;
  const cat = rv?.category;
  const moved = rv ? `${pct(rv.change_90d)} in 90 days` : "";
  if (cat === "up2") {
    say(`Analysts keep raising their profit forecast for next year: ${moved}, up at every check along the way.`);
  } else if (cat === "up1") {
    say(`Analysts have raised their profit forecast for next year (${moved}).`);
  } else if (cat === "flat") {
    say(`Analysts' profit forecast for next year has held steady (${moved}).`);
  } else if (cat === "down1" || cat === "down2") {
    say(`⚠ Analysts ${cat === "down2" ? "keep cutting" : "have cut"} their profit forecast for next year (${moved}). A stock that looks cheap while forecasts fall is often a trap.`, "warn-line");
  }

  const trust = {
    good: ["Reliable history.", "The past valuations used here were checked against real data and match closely."],
    caution: ["Roughly reliable history.", "The past valuations used here are reconstructed and can be 15–35% off. Treat the verdict as approximate."],
    biased: ["Unreliable history for this stock.", "Profit forecasts jumped after the fact, so the past looks cheaper than it really was and today looks more expensive than it is."],
  }[row.b_grade] || (row.metric === "ps"
    ? ["History from reported sales.", "Past multiples use revenue as actually reported at the time, so there is no look-ahead."]
    : ["Recorded history only.", "Real data has been recorded since 2026-09-24; the picture sharpens as it builds up."]);
  const t = el("p", { class: "trust" });
  t.append(el("strong", {}, trust[0] + " "), document.createTextNode(trust[1]));
  lines.append(t);

  if (zone && zone.side === "cheap") {
    const text = cat === "up2"
      ? ["yes", "✓✓ Strongest pattern: cheap against its own past, and analysts keep raising forecasts."]
      : cat === "down1" || cat === "down2"
        ? ["no", "✗ Cheap, but forecasts are falling: doesn't match the strategy's pattern."]
        : ["yes", "✓ Matches the strategy's pattern: cheap against its own past, and forecasts holding up."];
    lines.append(el("p", { class: `pattern ${text[0]}` }, text[1]));
  } else if (zone && zone.side === "rich") {
    lines.append(el("p", { class: "pattern no" }, "Expensive against its own past: the strategy would take profits here, not buy."));
  }
  card.append(lines);
  return card;
}

function scoreCard(row) {
  const sec = el("section", { class: "scorecard" });
  if (row.rankedVia) {
    sec.append(el("h3", {}, "Combined ranking"));
    sec.append(el("p", { class: "help" }, `Not ranked separately: this is another share class of the same company, with the same profit forecasts. The cheaper class, ${row.rankedVia}, carries the company's ranking.`));
    return sec;
  }
  if (row.score == null) {
    sec.append(el("h3", {}, "Combined ranking"));
    sec.append(el("p", { class: "help" }, "Not ranked: needs at least three of the four measures (usually because the company is loss-making or too new)."));
    return sec;
  }
  const top = el("div", { class: "sc-top" });
  top.append(
    el("span", { class: "sc-rank" }, `#${row.rank}`),
    el("span", { class: "sc-of" }, ` of ${state.rows.rankedOf} ranked stocks`),
    el("span", { class: "sc-score" }, `score ${row.score.toFixed(0)}/100`),
  );
  sec.append(el("h3", {}, "Combined ranking"), top);
  sec.append(el("p", { class: "help" }, "Four measures, each scored by where this stock stands among all the others (100 = best in the list, 50 = middle). The score is their average."));
  for (const c of CRITERIA) {
    const v = row.parts[c.key];
    const line = el("div", { class: "sc-row" });
    line.append(el("span", { class: "sc-label" }, c.label));
    const bar = el("span", { class: "sc-bar" });
    if (v != null) bar.append(el("span", { class: "sc-fill", style: `width:${Math.max(v, 2)}%` }));
    line.append(bar);
    line.append(el("span", { class: "sc-val" }, v == null ? "no data" : `${v.toFixed(0)} · ${c.explain(row)}`));
    sec.append(line);
  }
  if (row.b_grade === "biased") {
    sec.append(el("p", { class: "help" }, "⚠ This stock's history is unreliable, so its 'typical level' (and the upside measure) is distorted."));
  }
  return sec;
}

function relativeCard(row) {
  const sec = el("section", { class: "scorecard" });
  sec.append(el("h3", {}, "Cheap compared with other stocks"));
  if (row.rel == null) {
    sec.append(el("p", { class: "help" }, "No comparison: the company is expected to make a loss, so it has no P/E."));
    return sec;
  }
  const top = el("div", { class: "sc-top" });
  top.append(el("span", { class: "sc-rank" }, `${row.rel.toFixed(0)}`), el("span", { class: "sc-of" }, "/100 (100 = cheapest in the list)"));
  sec.append(top);
  sec.append(el("p", { class: "help" }, "The section above compares the stock with its own past. This one compares it with other companies today."));
  const pg = row.peerGroup;
  const lines = [
    ["Against all stocks", row.relParts.all, `forward P/E ${fmt(row.pe)}× vs a list median of ${fmt(median(state.rows.filter((r) => r.pe > 0).map((r) => r.pe)))}×`],
    ["Against its peers", row.relParts.peers, pg
      ? `cheaper than ${pg.cheaper} of ${pg.size} ${pg.name} ${pg.level === "sector" ? "sector " : ""}stocks (their median ${fmt(pg.median)}×)`
      : "too few similar companies in the list to compare"],
    ["For its growth (PEG)", row.relParts.peg, row.peg != null
      ? `PEG ${fmt(row.pegRaw, 2)}${row.growth > PEG_GROWTH_CAP ? `; ranked on ${fmt(row.peg, 2)}, with growth counted up to +50%` : ""}`
      : "expected growth below +3%, so growth doesn't justify the price"],
  ];
  for (const [label, v, why] of lines) {
    const line = el("div", { class: "sc-row" });
    line.append(el("span", { class: "sc-label" }, label));
    const bar = el("span", { class: "sc-bar" });
    if (v != null) bar.append(el("span", { class: "sc-fill", style: `width:${Math.max(v, 2)}%` }));
    line.append(bar, el("span", { class: "sc-val" }, v == null ? why : `${v.toFixed(0)} · ${why}`));
    sec.append(line);
  }
  return sec;
}

function gaugeSection(row) {
  const sec = el("section", { class: "gauges" });
  sec.append(el("h3", {}, "How cheap or expensive, by time window"));
  sec.append(el("p", { class: "help" }, "Each bar is the range of prices-to-earnings this stock traded at over that period. The dot is today. Click a row to see it on the price chart."));

  const scale = el("div", { class: "g-scale", "aria-hidden": "true" });
  scale.append(el("span", {}, "cheaper"), el("span", {}, "normal"), el("span", {}, "more expensive"));
  sec.append(scale);

  const lo = -2.5, hi = 2.5;
  const at = (s) => ((Math.max(lo, Math.min(hi, s)) - lo) / (hi - lo)) * 100;
  for (const w of WINDOWS) {
    const c = row.corridors?.[w.key];
    const btn = el("button", { class: `g-row${state.window === w.key ? " on" : ""}`, "aria-pressed": String(state.window === w.key) });
    btn.append(el("span", { class: "g-label" }, w.label));
    const bar = el("span", { class: "g-bar" });
    let edge = lo;
    for (const z of ZONES) {
      const end = Math.min(z.upTo, hi);
      bar.append(el("span", { class: `g-seg zone-${z.key}`, style: `left:${at(edge)}%;width:${at(end) - at(edge)}%` }));
      edge = end;
    }
    if (c) bar.append(el("span", { class: "g-dot", style: `left:${at(c.sigma)}%`, title: `Today: ${zoneOf(c.sigma).label}` }));
    btn.append(bar);
    const zone = c ? zoneOf(c.sigma) : null;
    const txt = el("span", { class: "g-text" });
    if (c) {
      const p = Math.round(c.pct);
      const where = p < 1 ? "cheapest in this period" : p > 99 ? "priciest in this period"
        : p <= 50 ? `cheaper than ${100 - p}% of days` : `pricier than ${p}% of days`;
      txt.append(el("strong", {}, zone.label), el("span", { class: "g-pct" }, ` · ${where}`));
    } else {
      txt.append(el("span", { class: "muted" }, "not enough history"));
    }
    btn.append(txt);
    if (c) btn.onclick = () => {
      state.window = w.key;
      rerender();
    };
    else btn.disabled = true;
    sec.append(btn);
  }
  return sec;
}

function revisionSection(row) {
  const rv = row.revisions;
  const info = REVS[rv.category];
  const sec = el("section", { class: "revs" });
  sec.append(el("h3", {}, "Are analysts raising or cutting their forecasts?"));
  sec.append(el("p", { class: "help" }, "Analysts' average forecast of profit per share for the company's next financial year, as it stood at each point over the last 90 days. Forecasts that keep rising often keep pushing the price up."));

  const top = el("div", { class: "rev-top" });
  const badge = revBadge(rv);
  badge.classList.add("big");
  top.append(badge, el("span", { class: "muted" }, `${pct(rv.change_90d)} over 90 days`));
  sec.append(top);

  // Five points: 90, 60, 30, 7 days ago and today.
  const W = 800, H = 120, L = 58, R = 16, T = 14, B = 24;
  const root = svg("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "Next-year profit forecast over the last 90 days" });
  const vals = rv.points.map((p) => p.eps);
  let lo = Math.min(...vals), hi = Math.max(...vals);
  const pad = (hi - lo) * 0.25 || Math.abs(hi) * 0.02 || 1;
  lo -= pad; hi += pad;
  const xOf = (daysAgo) => L + ((90 - daysAgo) / 90) * (W - L - R);
  const yOf = (v) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);
  const grid = svg("g", { class: "grid" });
  for (const v of [lo + pad, hi - pad]) {
    grid.append(svg("line", { x1: L, x2: W - R, y1: yOf(v), y2: yOf(v) }));
    const lab = svg("text", { x: L - 6, y: yOf(v) + 4, "text-anchor": "end", class: "tick" });
    lab.textContent = v.toFixed(2);
    grid.append(lab);
  }
  for (const p of rv.points.filter((q) => q.days_ago !== 7)) {
    const lab = svg("text", { x: xOf(p.days_ago), y: H - 6, "text-anchor": p.days_ago === 90 ? "start" : p.days_ago === 0 ? "end" : "middle", class: "tick" });
    lab.textContent = p.days_ago === 0 ? "today" : `${p.days_ago}d ago`;
    grid.append(lab);
  }
  root.append(grid);
  root.append(svg("path", { class: `rev-line rev-${info.tone}`, d: rv.points.map((p, i) => `${i ? "L" : "M"}${xOf(p.days_ago).toFixed(1)},${yOf(p.eps).toFixed(1)}`).join("") }));
  for (const p of rv.points) {
    const c = svg("circle", { class: `rev-pt rev-${info.tone}`, cx: xOf(p.days_ago), cy: yOf(p.eps), r: 5 });
    const t = svg("title");
    t.textContent = `${p.days_ago === 0 ? "Today" : `${p.days_ago} days ago`}: ${p.eps.toFixed(2)}`;
    c.append(t);
    root.append(c);
  }
  const holder = el("div", { class: "chart" });
  holder.append(root);
  sec.append(holder);

  if (rv.up_30d != null && rv.down_30d != null) {
    sec.append(el("p", { class: "help" }, `Last 30 days, roughly: ${rv.up_30d} analyst revisions up, ${rv.down_30d} down (Yahoo's counts are approximate).`));
  }
  return sec;
}

// The earlier project stored some firms by short lowercase keys.
const FIRM_NAMES = { mirae: "Mirae Asset", hana: "Hana Securities", meritz: "Meritz Securities", kb: "KB Securities",
  nh: "NH Investment", hyundai: "Hyundai Motor Securities", samsung: "Samsung Securities", kiwoom: "Kiwoom", daishin: "Daishin" };
const firmName = (f) => FIRM_NAMES[(f || "").toLowerCase()] || f || "?";

function analystSection(row) {
  const a = row.analysts;
  const [y0, y1] = a.years;
  const sec = el("section", { class: "analysts" });
  sec.append(el("h3", {}, "What individual analysts forecast"));
  const named = a.reports.filter((r) => r.kind === "analyst" && r.eps[y1] != null);
  const c1 = a.consensus[y1];
  if (named.length && c1) {
    const vals = named.map((r) => r.eps[y1]);
    const avg = vals.reduce((x, y) => x + y, 0) / vals.length;
    sec.append(el("p", { class: "help" },
      `${named.length} analyst report${named.length > 1 ? "s" : ""} from the last two years. For ${y1}, they average ` +
      `${money(avg, "")} per share (${pct(avg / c1 - 1)} vs the consensus of ${money(c1, "")}` +
      `${a.consensus_analysts ? `, ${a.consensus_analysts} analysts` : ""}), ranging from ${money(Math.min(...vals), "")} to ${money(Math.max(...vals), "")}.`));
  }
  const wrap = el("div", { class: "ladder" });
  const t = el("table");
  const head = el("tr");
  ["Analyst", "Report", `${y1} EPS`, "vs consensus"].forEach((h, i) => head.append(el("th", i >= 2 ? { class: "num" } : {}, h)));
  t.append(head);
  const cons = el("tr", { class: "lvl-mid" });
  cons.append(el("td", {}, `Consensus${a.consensus_analysts ? ` · ${a.consensus_analysts} analysts` : ""}`), el("td", {}, "today"),
    el("td", { class: "num" }, money(c1, "")), el("td", { class: "num" }, "—"));
  t.append(cons);
  for (const r of a.reports) {
    const tr = el("tr");
    const who = el("td");
    const firm = /^https?:/.test(r.source_url)
      ? el("a", { href: r.source_url, target: "_blank", rel: "noopener", title: "Open the report (PDF)" }, firmName(r.firm))
      : el("strong", {}, firmName(r.firm));
    who.append(firm, el("span", { class: "name" }, r.kind === "consensus" ? "published consensus" : r.analyst));
    if (r.status === "needs_review") who.append(el("span", { class: "review", title: "A figure could not be matched in the report text" }, " ⚠"));
    const age = r.age_days < 60 ? `${r.age_days}d ago` : `${Math.round(r.age_days / 30)}mo ago`;
    const when = el("td", {}, r.date);
    when.append(el("span", { class: `name${r.age_days > 180 ? " stale" : ""}` }, age));
    const vs = r.vs_consensus;
    tr.append(who, when,
      (() => {
        const td = el("td", { class: "num" }, money(r.eps[y1], ""));
        if (r.gaap) td.append(el("span", { class: "gaap", title: "GAAP/reported EPS; the consensus is adjusted, so the gap is not like for like" }, " GAAP"));
        return td;
      })(),
      el("td", { class: `num ret ${vs == null ? "" : vs >= 0 ? "pos" : "neg"}` }, vs == null ? "" : pct(vs)));
    t.append(tr);
  }
  wrap.append(t);
  sec.append(wrap);
  sec.append(el("p", { class: "help" }, "From broker reports: imported from the earlier dashboard project, collected nightly (Morningstar via Firstrade, Korean brokers via Telegram) or dropped into the inbox. Per share on today's share count, in the price currency."));
  return sec;
}

function notesSection(row) {
  const sec = el("section", { class: "notes" });
  sec.append(el("h3", {}, "What changed recently"));
  for (const n of row.notes) {
    const card = el("div", { class: "note-card" });
    const title = n.source_url ? el("a", { href: n.source_url, target: "_blank", rel: "noopener" }, n.title) : el("strong", {}, n.title);
    const head = el("div", { class: "note-head" });
    head.append(title, el("span", { class: "name" }, n.date));
    card.append(head);
    for (const p of [].concat(n.text)) card.append(el("p", {}, p));
    sec.append(card);
  }
  return sec;
}

function targetsSection(row) {
  const tg = row.targets;
  const sec = el("section", { class: "analysts" });
  sec.append(el("h3", {}, "Analysts' price targets"));
  sec.append(el("p", { class: "help" },
    `${tg.items.length} firm${tg.items.length > 1 ? "s" : ""} in the last year. Median target ${money(tg.median, row.currency)}` +
    `${tg.upside != null ? ` (${pct(tg.upside)} from today's price)` : ""}, ranging from ${money(tg.low, row.currency)} to ${money(tg.high, row.currency)}.`));
  const wrap = el("div", { class: "ladder" });
  const t = el("table");
  const head = el("tr");
  ["Analyst", "Date", "Rating", "Target", "vs price"].forEach((h, i) => head.append(el("th", i >= 3 ? { class: "num" } : {}, h)));
  t.append(head);
  for (const r of tg.items) {
    const tr = el("tr");
    const who = el("td");
    who.append(r.source_url ? el("a", { href: r.source_url, target: "_blank", rel: "noopener", title: "Where this was reported" }, r.firm) : el("strong", {}, r.firm),
      el("span", { class: "name" }, r.analyst || ""));
    const when = el("td", {}, r.date);
    when.append(el("span", { class: `name${r.age_days > 180 ? " stale" : ""}` }, r.age_days < 60 ? `${r.age_days}d ago` : `${Math.round(r.age_days / 30)}mo ago`));
    const move = r.prev_target && r.prev_target !== r.target ? ` (was ${money(r.prev_target, "")})` : "";
    const up = row.price ? r.target / row.price - 1 : null;
    tr.append(who, when, el("td", {}, [r.rating, r.action].filter(Boolean).join(" · ") || "—"),
      el("td", { class: "num" }, `${money(r.target, "")}${move}`),
      el("td", { class: `num ret ${up == null ? "" : up >= 0 ? "pos" : "neg"}` }, up == null ? "" : pct(up)));
    t.append(tr);
  }
  wrap.append(t);
  sec.append(wrap);
  sec.append(el("p", { class: "help" }, "Entered by hand from press reports of the notes (linked). Each firm's latest target is shown."));
  return sec;
}

function rerender() {
  const row = state.rows.find((r) => r.ticker === state.selected);
  fetch(`data/series/${encodeURIComponent(row.ticker)}.json`, { cache: "force-cache" })
    .then((r) => (r.ok ? r.json() : null))
    .then((series) => renderDetail(row, series))
    .catch(() => renderDetail(row, null));
}

/** EPS from today's NTM, moving linearly to next fiscal year's consensus over 365 days. */
function epsAhead(row, k) {
  const target = row.fy1_eps != null && row.fy1_eps > 0 ? row.fy1_eps : row.eps;
  return row.eps + (target - row.eps) * (k / 365);
}

function priceSection(row, series) {
  const w = windowOf(state.window);
  const c = row.corridors[state.window];
  const sec = el("section", { class: "price-sec" });
  sec.append(el("h3", {}, `Price against its usual valuation, ${w.label.toLowerCase()} and one year ahead`));

  const chips = el("div", { class: "ranges", role: "group", "aria-label": "Time window" });
  for (const x of WINDOWS) {
    const b = el("button", { class: "chip", "aria-pressed": String(state.window === x.key) }, x.key);
    if (!row.corridors?.[x.key]) b.disabled = true;
    b.onclick = () => {
      state.window = x.key;
      rerender();
    };
    chips.append(b);
  }
  sec.append(chips);
  sec.append(el("p", { class: "help" },
    "The coloured bands show where the price would be if the stock were valued the way it usually was in this window. " +
    "Grey is its normal range, blue is cheap, red is expensive. The shaded area on the right projects this a year ahead, using analysts' forecasts for next year."));

  priceChart(sec, row, series, c, w.days);
  sec.append(ladder(row, c));
  return sec;
}

function priceChart(sec, row, series, c, days) {
  const W = 800, H = 280, L = 58, R = 12, T = 10, B = 24;
  const holder = el("div", { class: "chart" });
  const root = svg("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "Price with valuation bands" });
  holder.append(root);
  sec.append(holder);

  const today = dayNum(series.dates[series.dates.length - 1]);
  const startDay = today - Math.max(days, 180);
  const endDay = today + 365;
  const hist = series.dates.map((d, i) => ({ day: dayNum(d), price: series.price[i], eps: series.eps[i] }))
    .filter((p) => p.day >= startDay);
  const ahead = [];
  for (let k = 7; k <= 365; k += 7) ahead.push({ day: today + k, eps: epsAhead(row, k) });
  const pts = [...hist.filter((h) => h.eps > 0), ...ahead].map((h) => ({
    day: h.day,
    lv: Object.fromEntries(LEVELS.map((k) => [k, c.levels[k] * h.eps])),
  }));

  const ys = [...hist.map((h) => h.price), ...pts.flatMap((q) => [q.lv["-2"], q.lv["2"]])].filter((v) => v != null && Number.isFinite(v));
  let lo = Math.min(...ys), hi = Math.max(...ys);
  const pad = (hi - lo) * 0.06 || 1;
  lo = Math.max(0, lo - pad);
  hi += pad;
  const xOf = (day) => L + ((day - startDay) / (endDay - startDay)) * (W - L - R);
  const yOf = (v) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);

  const grid = svg("g", { class: "grid" });
  for (let k = 0; k <= 4; k++) {
    const v = lo + ((hi - lo) * k) / 4;
    grid.append(svg("line", { x1: L, x2: W - R, y1: yOf(v), y2: yOf(v) }));
    const lab = svg("text", { x: L - 6, y: yOf(v) + 4, "text-anchor": "end", class: "tick" });
    lab.textContent = v >= 100 ? v.toFixed(0) : v.toFixed(2);
    grid.append(lab);
  }
  for (const [day, anchor, text] of [[startDay, "start", isoOf(startDay)], [today, "middle", "today"], [endDay, "end", isoOf(endDay)]]) {
    const lab = svg("text", { x: xOf(day), y: H - 6, "text-anchor": anchor, class: "tick" });
    lab.textContent = text;
    grid.append(lab);
  }
  root.append(grid);

  const clipId = `clip-${Math.random().toString(36).slice(2)}`;
  const defs = svg("defs");
  const clip = svg("clipPath", { id: clipId });
  clip.append(svg("rect", { x: L, y: T, width: W - L - R, height: H - T - B }));
  defs.append(clip);
  root.append(defs);
  root.append(svg("rect", { class: "future", x: xOf(today), y: T, width: xOf(endDay) - xOf(today), height: H - T - B }));
  const plot = svg("g", { "clip-path": `url(#${clipId})` });

  const areaBetween = (a, b, cls) => {
    const top = pts.map((q, i) => `${i ? "L" : "M"}${xOf(q.day).toFixed(1)},${yOf(q.lv[b]).toFixed(1)}`).join("");
    const bottom = [...pts].reverse().map((q) => `L${xOf(q.day).toFixed(1)},${yOf(q.lv[a]).toFixed(1)}`).join("");
    plot.append(svg("path", { class: `zband ${cls}`, d: `${top}${bottom}Z` }));
  };
  areaBetween("-2", "-1.5", "zone-c2");
  areaBetween("-1.5", "-1", "zone-c1");
  areaBetween("-1", "1", "zone-n");
  areaBetween("1", "1.5", "zone-e1");
  areaBetween("1.5", "2", "zone-e2");
  plot.append(svg("path", { class: "zmid", d: pts.map((q, i) => `${i ? "L" : "M"}${xOf(q.day).toFixed(1)},${yOf(q.lv["0"]).toFixed(1)}`).join("") }));

  let d = "", pen = false;
  for (const h of hist) {
    if (h.price == null) { pen = false; continue; }
    d += `${pen ? "L" : "M"}${xOf(h.day).toFixed(1)},${yOf(h.price).toFixed(1)}`;
    pen = true;
  }
  plot.append(svg("path", { class: "price", d }));
  root.append(plot);
  root.append(svg("line", { class: "todayline", x1: xOf(today), x2: xOf(today), y1: T, y2: H - B }));
  if (row.price) root.append(svg("circle", { class: "today-dot", cx: xOf(today), cy: yOf(row.price), r: 4 }));

  const legend = el("div", { class: "legend" });
  const key = (cls, text) => {
    const k = el("span", { class: "key" });
    k.append(el("span", { class: `sw ${cls}`, "aria-hidden": "true" }), document.createTextNode(text));
    legend.append(k);
  };
  key("sw-price", "Price");
  key("zone-n", "Normal");
  key("zone-c1", "Cheap");
  key("zone-c2", "Very cheap");
  key("zone-e1", "Expensive");
  key("zone-e2", "Very expensive");
  key("sw-mid", "Typical");
  holder.prepend(legend);

  const tip = el("div", { class: "tip", hidden: "" });
  holder.append(tip);
  const cross = svg("line", { class: "cross", y1: T, y2: H - B, visibility: "hidden" });
  root.append(cross);
  const hit = svg("rect", { class: "hit", x: L, y: T, width: W - L - R, height: H - T - B });
  root.append(hit);
  const nearest = (arr, day) => arr.reduce((best, q) => (Math.abs(q.day - day) < Math.abs(best.day - day) ? q : best), arr[0]);
  hit.addEventListener("pointermove", (e) => {
    const r = root.getBoundingClientRect();
    const day = Math.round(startDay + ((((e.clientX - r.left) / r.width) * W - L) / (W - L - R)) * (endDay - startDay));
    cross.setAttribute("x1", xOf(day));
    cross.setAttribute("x2", xOf(day));
    cross.setAttribute("visibility", "visible");
    const lines = [el("div", { class: "tip-date" }, isoOf(day) + (day > today ? " (projected)" : ""))];
    if (day <= today && hist.length) lines.push(el("div", {}, `Price ${money(nearest(hist, day).price, row.currency)}`));
    const q = pts.length ? nearest(pts, day) : null;
    if (q && Math.abs(q.day - day) <= 10) {
      lines.push(el("div", {}, `Normal ${money(q.lv["-1"], "")}–${money(q.lv["1"], "")}`));
      lines.push(el("div", {}, `Typical ${money(q.lv["0"], "")}`));
      lines.push(el("div", {}, `Very cheap below ${money(q.lv["-1.5"], "")}`));
    }
    tip.replaceChildren(...lines);
    tip.hidden = false;
    const x = xOf(day) * (holder.clientWidth / W);
    tip.style.left = `${Math.min(Math.max(x + 12, 0), holder.clientWidth - 190)}px`;
    tip.style.top = "40px";
  });
  hit.addEventListener("pointerleave", () => {
    cross.setAttribute("visibility", "hidden");
    tip.hidden = true;
  });
}

function ladder(row, c) {
  const wrap = el("div", { class: "ladder" });
  wrap.append(el("h4", {}, "What price would each level mean?"));
  const t = el("table");
  const head = el("tr");
  ["Level", row.metric === "ps" ? "× sales" : "× profit", "Price now", "In a year"].forEach((h, i) => head.append(el("th", i ? { class: "num" } : {}, h)));
  t.append(head);
  const eps1 = epsAhead(row, 365);
  let placed = false;
  const youAreHere = () => {
    const tr = el("tr", { class: "here" });
    tr.append(
      el("td", {}, "▶ Today"),
      el("td", { class: "num" }, `${fmt(row.pe)}×`),
      el("td", { class: "num" }, money(row.price, row.currency)),
      el("td", { class: "num" }, ""),
    );
    t.append(tr);
    placed = true;
  };
  for (const k of LEVELS) {
    const pe = c.levels[k];
    if (!placed && row.pe >= pe) youAreHere();
    const tr = el("tr", { class: `lvl-${k === "0" ? "mid" : Number(k) > 0 ? "rich" : "cheap"}` });
    tr.append(
      el("td", {}, LEVEL_NAME[k]),
      el("td", { class: "num" }, `${fmt(pe)}×`),
      el("td", { class: "num" }, money(pe * row.eps, "")),
      el("td", { class: "num" }, money(pe * eps1, "")),
    );
    t.append(tr);
  }
  if (!placed) youAreHere();
  wrap.append(t);
  wrap.append(el("p", { class: "help" },
    row.metric === "ps"
      ? `"In a year" assumes sales per share grow from the last 12 months (${fmt(row.eps, 2)}) to what analysts expect over the next 12 (${fmt(row.fy1_eps ?? row.eps, 2)}) and the stock is valued at the same multiple of sales.`
      : `"In a year" assumes profit per share grows from today's forecast (${fmt(row.eps, 2)}) to analysts' forecast for next financial year (${fmt(row.fy1_eps ?? row.eps, 2)}) and the stock is valued the same way.`));
  return wrap;
}

function detailsSection(row, series) {
  const d = el("details", { class: "more" });
  d.append(el("summary", {}, "More detail: the numbers, charts and the historical test"));

  const stats = el("div", { class: "stats" });
  const stat = (k, v, help) => {
    const s = el("div", { class: "stat", title: help });
    s.append(el("div", { class: "k" }, k), el("div", { class: "v" }, v));
    stats.append(s);
  };
  if (row.metric === "ps") {
    stat("Sales per share, last 12 months", fmt(row.eps, 2), "Reported revenue per share, in the price currency");
    stat("Price ÷ sales, last 12 months", `${fmt(row.pe, 2)}×`, "Trailing P/S");
    stat("Price ÷ expected sales, next 12 months", row.ps_forward ? `${fmt(row.ps_forward, 2)}×` : "n/a",
      `Forward P/S on ${row.rev_analysts || "?"} analysts' revenue consensus`);
    if (row.shares_source && !row.shares_source.startsWith("yahoo")) stat("Share count", "override", row.shares_source);
  } else {
    stat("Expected profit per share, next 12 months", fmt(row.eps, 2), "Analysts' average forecast (consensus NTM EPS)");
    stat("Price ÷ expected profit", row.pe == null || row.pe <= 0 ? "n/m" : `${fmt(row.pe)}×`, "Forward P/E");
  }
  stat("Price ÷ last 12 months' profit", row.trailing_pe == null ? "n/m" : `${fmt(row.trailing_pe)}×`, "Trailing P/E on the same (adjusted) basis as the forecasts");
  stat("Price ÷ book value", row.pb == null ? "n/m" : `${fmt(row.pb, 1)}×`, "Market value over shareholders' equity on the last balance sheet");
  stat("Enterprise value ÷ free cash flow", row.ev_fcf == null ? (row.fcf_negative ? "negative FCF" : "n/a") : `${fmt(row.ev_fcf)}×`,
    row.fcf_basis ? `Market value + debt − cash, over operating cash flow − capex for the ${row.fcf_basis} to ${row.fcf_end}; free cash flow yield ${pct(row.fcf_yield, 1)}` : "No cash flow statement found");
  const g12 = growthText(row, row.growth, row.metric === "ps" ? row.fy1_eps : row.eps, false), g24 = growthText(row, row.growth_24m, row.eps_24m, true);
  stat("Expected profit growth", g12.text, `Next 12 months' forecast against the last 12 months' reported profit. ${g12.title}`);
  stat("Expected profit growth, 24 months", g24.text, `Forecast profit in months 13–24 from now against the last 12 months' reported profit. ${g24.title}`);
  for (const fy of ["FY2027", "FY2028"]) {
    const f = row.fy_eps?.[fy];
    stat(`Expected profit per share, ${fy}`, f ? fmt(f.eps, 2) : "n/a", f ? f.source : "No forecast for this fiscal year");
  }
  stat("Forecast change, next year, 90 days", pct(row.fy1_revision_90d), "How analysts' forecast for next financial year moved in 90 days");
  d.append(stats);

  if (series && series.dates.length > 1) {
    const ranges = el("div", { class: "ranges", role: "group", "aria-label": "Time range" });
    for (const r of RANGES) {
      const b = el("button", { class: "chip", "aria-pressed": String(state.range === r.days) }, r.label);
      b.onclick = () => {
        state.range = r.days;
        renderDetail(row, series);
        $("#detail details.more").open = true;
      };
      ranges.append(b);
    }
    d.append(ranges);
    smallCharts(d, row, series);
  }

  const past = row.past;
  if (past && past.scored_days) {
    const wrap = el("div", { class: "past" });
    wrap.append(el("h4", {}, "Historical test: what happened after the stock looked cheap or expensive"));
    wrap.append(el("p", { class: "help" }, "Average price change after each day the stock was cheap (bottom sixth of its 3-year range) or expensive (top sixth), next to the average after any day. Reconstructed history flatters these numbers."));
    const t = el("table");
    const head = el("tr");
    ["After", "Any day", "After cheap", "After expensive"].forEach((h, i) => head.append(el("th", i ? { class: "num" } : {}, h)));
    t.append(head);
    for (const [h, s] of Object.entries(past.horizons)) {
      const tr = el("tr");
      tr.append(el("td", {}, `${Math.round(Number(h) / 21)} months`));
      tr.append(el("td", { class: "num" }, pct(s.all_avg)));
      const cheap = el("td", { class: "num" }, `${pct(s.cheap_avg)} (${s.cheap_n} days)`);
      if (s.cheap_avg != null && s.all_avg != null && s.cheap_avg > s.all_avg) cheap.classList.add("better");
      tr.append(cheap, el("td", { class: "num" }, `${pct(s.expensive_avg)} (${s.expensive_n} days)`));
      t.append(tr);
    }
    wrap.append(t);
    d.append(wrap);
  }
  if (row.warnings?.length) {
    const ul = el("ul", { class: "warn" });
    row.warnings.forEach((w) => ul.append(el("li", {}, w)));
    d.append(ul);
  }
  return d;
}

function sliceRange(series) {
  if (!state.range) return series;
  const last = dayNum(series.dates[series.dates.length - 1]);
  const i = series.dates.findIndex((d) => dayNum(d) >= last - state.range);
  const from = i < 0 ? 0 : i;
  return Object.fromEntries(Object.entries(series).map(([k, v]) => [k, v.slice(from)]));
}

function smallCharts(box, row, full) {
  const s = sliceRange(full);
  const c = row.corridors?.[row.mainKey];
  const charts = [
    row.metric === "ps"
      ? { title: "Sales per share, last 12 months (as reported at the time)", values: s.eps, digits: 2 }
      : { title: "Expected profit per share, next 12 months (analyst consensus)", values: s.eps, digits: 2 },
    { title: `Price ÷ ${row.metric === "ps" ? "sales" : "expected profit"}, with its normal range over ${row.mainKey ? spanOf(row.mainKey) : "the last 3 years"}`,
      values: s.pe, digits: row.metric === "ps" ? 2 : 1, band: c ? [c.levels["-1"], c.levels["0"], c.levels["1"]] : null },
  ].map((spec) => lineChart(box, s, spec));
  const holder = charts[1].wrap;
  const tip = el("div", { class: "tip", hidden: "" });
  holder.append(tip);
  const move = (idx) => {
    for (const ch of charts) ch.cross(idx);
    if (idx == null) {
      tip.hidden = true;
      return;
    }
    tip.hidden = false;
    tip.replaceChildren(
      el("div", { class: "tip-date" }, s.dates[idx]),
      el("div", {}, `Price ${money(s.price[idx], row.currency)}`),
      el("div", {}, `Expected profit ${fmt(s.eps[idx], 2)}`),
      el("div", {}, `Price ÷ profit ${s.pe[idx] == null ? "n/m" : fmt(s.pe[idx])}×`),
    );
    const x = charts[1].xOf(idx) * (holder.clientWidth / 800);
    tip.style.left = `${Math.min(Math.max(x + 12, 0), holder.clientWidth - 150)}px`;
    tip.style.top = "28px";
  };
  charts.forEach((ch) => ch.onMove(move));
}

function lineChart(box, s, { title, values, digits, band, extra }) {
  const W = 800, H = 180, L = 52, R = 12, T = 8, B = 24;
  const wrap = el("div", { class: "chart" });
  wrap.append(el("h4", {}, title));
  const root = svg("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": title });
  wrap.append(root);
  box.append(wrap);

  const t0 = dayNum(s.dates[0]), t1 = dayNum(s.dates[s.dates.length - 1]) || t0 + 1;
  const nums = values.concat(extra || []).filter((v) => v != null && Number.isFinite(v));
  if (band) nums.push(band[0], band[2]);
  let lo = nums.length ? Math.min(...nums) : 0, hi = nums.length ? Math.max(...nums) : 1;
  if (lo === hi) { lo -= 1; hi += 1; }
  const pad = (hi - lo) * 0.08;
  lo -= pad; hi += pad;
  const xOf = (i) => L + ((dayNum(s.dates[i]) - t0) / (t1 - t0 || 1)) * (W - L - R);
  const yOf = (v) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);

  const grid = svg("g", { class: "grid" });
  for (let k = 0; k <= 4; k++) {
    const v = lo + ((hi - lo) * k) / 4;
    grid.append(svg("line", { x1: L, x2: W - R, y1: yOf(v), y2: yOf(v) }));
    const lab = svg("text", { x: L - 6, y: yOf(v) + 4, "text-anchor": "end", class: "tick" });
    lab.textContent = v.toFixed(digits);
    grid.append(lab);
  }
  for (const f of [0, 0.5, 1]) {
    const i = Math.round(f * (s.dates.length - 1));
    const lab = svg("text", { x: xOf(i), y: H - 6, "text-anchor": f === 0 ? "start" : f === 1 ? "end" : "middle", class: "tick" });
    lab.textContent = s.dates[i];
    grid.append(lab);
  }
  root.append(grid);
  if (band && band[0] != null && band[2] != null) {
    root.append(svg("rect", { class: "band", x: L, width: W - L - R, y: yOf(band[2]), height: yOf(band[0]) - yOf(band[2]) }));
    root.append(svg("line", { class: "mean", x1: L, x2: W - R, y1: yOf(band[1]), y2: yOf(band[1]) }));
  }
  const path = (vals) => {
    let d = "", pen = false;
    vals.forEach((v, i) => {
      if (v == null || !Number.isFinite(v)) { pen = false; return; }
      d += `${pen ? "L" : "M"}${xOf(i).toFixed(1)},${yOf(v).toFixed(1)}`;
      pen = true;
    });
    return d;
  };
  if (extra) root.append(svg("path", { class: "series extra", d: path(extra) }));
  root.append(svg("path", { class: "series", d: path(values) }));
  const cross = svg("line", { class: "cross", y1: T, y2: H - B, visibility: "hidden" });
  root.append(cross);
  const hit = svg("rect", { class: "hit", x: L, y: T, width: W - L - R, height: H - T - B });
  root.append(hit);

  let handler = () => {};
  const idxAt = (evt) => {
    const r = root.getBoundingClientRect();
    const x = ((evt.clientX - r.left) / r.width) * W;
    const t = t0 + ((x - L) / (W - L - R)) * (t1 - t0);
    let a = 0, b = s.dates.length - 1;
    while (b - a > 1) {
      const m = (a + b) >> 1;
      if (dayNum(s.dates[m]) < t) a = m; else b = m;
    }
    return Math.abs(dayNum(s.dates[a]) - t) < Math.abs(dayNum(s.dates[b]) - t) ? a : b;
  };
  hit.addEventListener("pointermove", (e) => handler(idxAt(e)));
  hit.addEventListener("pointerleave", () => handler(null));
  return {
    wrap,
    xOf,
    onMove: (fn) => (handler = fn),
    cross: (idx) => {
      if (idx == null) return cross.setAttribute("visibility", "hidden");
      cross.setAttribute("x1", xOf(idx));
      cross.setAttribute("x2", xOf(idx));
      cross.setAttribute("visibility", "visible");
    },
  };
}

// ---------- market breadth (NYSE McClellan Summation Index) ----------

const BREADTH = "$NYSI";
const BREADTH_RANGES = [
  { label: "6M", days: 183 },
  { label: "1Y", days: 365 },
  { label: "All", days: null },
];
let breadthRange = 365;

async function showBreadth() {
  const box = pageBox();
  try {
    const res = await fetch("data/breadth.json", { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    renderBreadth(await res.json());
  } catch {
    box.replaceChildren(el("p", { class: "empty" }, "No breadth data yet. It is computed each weekday night after the US close."));
  }
}

// Consecutive sessions the last value kept moving the same way.
function streak(xs) {
  const n = xs.length;
  if (n < 2) return { dir: 0, days: 0 };
  const dir = Math.sign(xs[n - 1] - xs[n - 2]);
  let days = 0;
  for (let i = n - 1; i > 0 && Math.sign(xs[i] - xs[i - 1]) === dir && dir !== 0; i--) days++;
  return { dir, days };
}

function breadthCard(b) {
  const n = b.dates.length - 1;
  const v = b.nysi[n], rsi = b.rsi[n], rsiPrev = b.rsi[n - 1];
  const bull = b.macd[n] > b.signal[n];
  const rising = b.osc[n] > 0;
  const run = streak(b.nysi);
  const side = rising && bull ? "cheap" : !rising && !bull ? "rich" : "na";
  const card = el("section", { class: `verdict side-${side}` });
  const head = rising && bull
    ? v < 0 ? "Breadth turning up from a washout" : "Breadth broad and improving"
    : !rising && !bull
      ? v > 0 ? "Breadth rolling over from strength" : "Breadth weak and still falling"
      : "Breadth turning, not confirmed";
  card.append(el("h3", {}, head));
  const lines = el("div", { class: "v-lines" });
  const say = (text, cls = "") => lines.append(el("p", { class: cls }, text));

  say(`The summation index is at ${fmt(v, 0)} and has ${run.dir > 0 ? "risen" : "fallen"} ${run.days} session${run.days === 1 ? "" : "s"} in a row. ` +
    (rising ? "More NYSE stocks are rising than its recent average, so breadth is improving." : "Fewer NYSE stocks are rising than its recent average, so breadth is weakening.") +
    ` ${v < 0 ? "Below zero: over the last couple of months most stocks have lagged." : "Above zero: most stocks have been taking part."}`);
  if (rsi != null) {
    const zone = rsi < 30 ? "oversold" : rsi > 70 ? "overbought" : "neutral";
    say(`RSI of the index ${fmt(rsi, 0)} (${zone}), ${rsi > rsiPrev ? "turning higher" : "still falling"}.`);
  }
  const lc = b.last_cross;
  say(`MACD is ${bull ? "above" : "below"} its signal line` +
    (lc ? `; the last cross was ${lc.dir === "bull" ? "bullish" : "bearish"} on ${lc.date}.` : ".") +
    (Math.abs(b.macd[n] - b.signal[n]) < 2 ? " The two lines are nearly touching, so a cross is close." : ""));
  if (rising && bull && v < 0) {
    say("This is the classic early buy signal for the broad market. It fails often on the first hook; trust it after a few weeks of follow-through.", "note-line");
  }
  if (b.official) {
    say(`StockCharts' official $NYSI: ${fmt(b.official.nysi, 1)} on ${b.official.date}` +
      `${b.official.rsi != null ? `, RSI ${fmt(b.official.rsi, 1)}` : ""}. Our line is counted from ${b.advances[n] + b.declines[n] + (b.unchanged?.[n] ?? 0)} NYSE issues and set to the official level, so day-to-day moves can differ slightly.`, "note-line");
  }
  card.append(lines);
  return card;
}

function renderBreadth(b) {
  const box = pageBox();
  box.replaceChildren();
  const head = el("div", { class: "d-head" });
  head.append(el("h2", {}, "Market breadth"), el("div", { class: "d-sub" }, `NYSE McClellan Summation Index (ratio-adjusted) · data as of ${b.as_of}`));
  box.append(head, breadthCard(b));

  const sec = el("section");
  sec.append(el("h3", {}, "History"));
  sec.append(el("p", { class: "help" }, "Advances minus declines per 1000 NYSE issues, smoothed (19- and 39-day) and summed. Rising: breadth improving. The RSI and MACD below are taken of the index itself."));
  const ranges = el("div", { class: "ranges" });
  for (const r of BREADTH_RANGES) {
    const b2 = el("button", { class: "chip", "aria-pressed": String(breadthRange === r.days) }, r.label);
    b2.addEventListener("click", () => { breadthRange = r.days; renderBreadth(b); });
    ranges.append(b2);
  }
  sec.append(ranges);
  box.append(sec);

  let from = 0;
  if (breadthRange) {
    const last = dayNum(b.dates[b.dates.length - 1]);
    from = Math.max(0, b.dates.findIndex((d) => dayNum(d) >= last - breadthRange));
  }
  const s = Object.fromEntries(Object.entries(b).map(([k, v]) => [k, Array.isArray(v) ? v.slice(from) : v]));
  const charts = [
    lineChart(sec, s, { title: "Summation index (zero line dashed)", values: s.nysi, digits: 0, band: [0, 0, 0] }),
    lineChart(sec, s, { title: "MACD of the index (solid) and its signal line (dashed)", values: s.macd, extra: s.signal, digits: 0, band: [0, 0, 0] }),
    lineChart(sec, s, { title: "RSI of the index, 14 days (shaded 30–70)", values: s.rsi, digits: 0, band: [30, 50, 70] }),
  ];
  const holder = charts[0].wrap;
  const tip = el("div", { class: "tip", hidden: "" });
  holder.append(tip);
  const move = (idx) => {
    for (const ch of charts) ch.cross(idx);
    if (idx == null) { tip.hidden = true; return; }
    tip.hidden = false;
    tip.replaceChildren(
      el("div", { class: "tip-date" }, s.dates[idx]),
      el("div", {}, `NYSI ${fmt(s.nysi[idx], 0)}`),
      el("div", {}, `RSI ${fmt(s.rsi[idx], 0)} · MACD ${fmt(s.macd[idx] - s.signal[idx], 1)} vs signal`),
      el("div", {}, `${s.advances[idx]} up · ${s.declines[idx]} down`),
    );
    const x = charts[0].xOf(idx) * (holder.clientWidth / 800);
    tip.style.left = `${Math.min(Math.max(x + 12, 0), holder.clientWidth - 170)}px`;
    tip.style.top = "28px";
  };
  charts.forEach((ch) => ch.onMove(move));
}

// ---------- horizon: what the market is waiting for ----------

const HZ_RANGES = [
  { label: "2 weeks", days: 14 },
  { label: "1 month", days: 31 },
  { label: "All", days: null },
];
const HZ_THEMES = { rates: "Rates", oil: "Oil and the Gulf", geopolitics: "Geopolitics", growth: "Growth", politics: "Politics" };
const HZ_WEEKDAY = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const HZ_MONTH = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const hz = { range: 31, all: false };

async function showHorizon() {
  const box = pageBox();
  try {
    const res = await fetch("data/horizon.json", { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    renderHorizon(await res.json());
  } catch {
    box.replaceChildren(el("p", { class: "empty" }, "No horizon data yet. It is collected each weekday night after the US close."));
  }
}

const hzDate = (iso) => {
  const d = new Date(`${iso}T12:00:00Z`);
  return `${HZ_WEEKDAY[d.getUTCDay()]} ${d.getUTCDate()} ${HZ_MONTH[d.getUTCMonth()]}`;
};
const hzIn = (iso, asOf) => {
  const n = dayNum(iso) - dayNum(asOf);
  return n === 0 ? "today" : n === 1 ? "tomorrow" : `in ${n} days`;
};
const hzPct = (p) => `${Math.round(p * 100)}%`;
const hzPts = (now, past) => (past == null ? null : Math.round((now - past) * 100));
const hzSigned = (v, d = 0) => `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(d)}`;

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

function hzSummary(d, events) {
  const card = el("section", { class: "verdict" });
  card.append(el("h3", {}, "What the market is waiting for"));
  const lines = el("div", { class: "v-lines" });
  const say = (text, cls = "") => lines.append(el("p", { class: cls }, text));
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
  card.append(lines);
  return card;
}

function renderHorizon(d) {
  const box = pageBox();
  box.replaceChildren();
  const head = el("div", { class: "d-head" });
  head.append(el("h2", {}, "Horizon"), el("div", { class: "d-sub" }, `What the market is waiting for, how likely it is, and how far it has run ahead · data as of ${d.as_of}`));

  const shown = d.scheduled.filter((e) => (hz.all || e.impact >= 2) && (!hz.range || dayNum(e.date) - dayNum(d.as_of) <= hz.range));
  box.append(head, hzSummary(d, d.scheduled.filter((e) => e.impact >= 2)));

  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "Dated events"));
  sec.append(el("p", { class: "help" }, "These will happen; the question is the outcome. Macro expectations come from Kalshi's traded ranges, the options figure is the at-the-money straddle to the first expiry after the date (the move the options market prices in), and 20d is how far the exposed asset has run into it, in its own volatility units."));
  const ctl = el("div", { class: "ranges" });
  for (const r of HZ_RANGES) {
    const b = el("button", { class: "chip", "aria-pressed": String(hz.range === r.days) }, r.label);
    b.addEventListener("click", () => { hz.range = r.days; renderHorizon(d); });
    ctl.append(b);
  }
  const allBtn = el("button", { class: "chip", "aria-pressed": String(hz.all) }, "Every stock I track");
  allBtn.addEventListener("click", () => { hz.all = !hz.all; renderHorizon(d); });
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
  const order = Object.keys(HZ_THEMES);
  const themes = [...new Set(d.markets.map((m) => m.theme))].sort((a, b) => (order.indexOf(a) + 99) % 99 - (order.indexOf(b) + 99) % 99);
  for (const th of themes) {
    sec2.append(el("h4", {}, HZ_THEMES[th] || th));
    const grid = el("div", { class: "hz-grid" });
    for (const m of d.markets.filter((x) => x.theme === th)) grid.append(hzMarket(m));
    sec2.append(grid);
  }
  box.append(sec2);
  box.append(el("p", { class: "help" }, "Coming: positioning (who is already leaning which way) and sentiment, so each catalyst shows how crowded the bet on it is."));
}

// ---------- positioning: who is already leaning which way ----------

const PS_GROUPS = { memory: "Memory", "ai-infra": "AI infrastructure", neocloud: "Neoclouds", megacap: "Megacaps", crowding: "Old crowding watchlist", market: "Index and macro ETFs" };
const PS_SIDES = { leveraged: "Hedge funds (leveraged funds)", asset_managers: "Asset managers", dealers: "Dealers" };
const ps = { contract: "20974+", group: "all", sv: "QQQ" };

async function showPositioning() {
  const box = pageBox();
  try {
    const res = await fetch("data/positioning.json", { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    const d = await res.json();
    // Korean retail margin is a separate collector; the tab works without it.
    d.korea = await fetch("data/korea_margin.json", { cache: "no-store" }).then((r) => (r.ok ? r.json() : null)).catch(() => null);
    renderPositioning(d);
  } catch {
    box.replaceChildren(el("p", { class: "empty" }, "No positioning data yet. It is collected each weekday night after the US close."));
  }
}

const psOrd = (p) => (p == null ? "n/a" : ordinal(Math.round(p)));

// A chart with a one-line readout under its title that follows the pointer.
function psChart(box, s, opts, readout) {
  const ch = lineChart(box, s, opts);
  const line = el("div", { class: "help ps-readout" }, readout(s.dates.length - 1));
  ch.wrap.querySelector("h4").after(line);
  ch.onMove((i) => {
    ch.cross(i);
    line.textContent = readout(i ?? s.dates.length - 1);
  });
  return ch;
}

function psSummary(d) {
  const card = el("section", { class: "verdict" });
  card.append(el("h3", {}, "How the market is positioned"));
  const lines = el("div", { class: "v-lines" });
  const say = (text, cls = "") => lines.append(el("p", { class: cls }, text));
  const md = d.margin_debt;
  if (md) say(`Leverage: margin debt ${fmt(md.debit_billions / 1000, 2)} trillion dollars in ${md.month}, ${pct(md.yoy, 0)} on a year earlier, at the ${psOrd(md.pct_all)} percentile of its history${md.pct_all >= 99 ? " (a record or close to it)" : ""}.`);
  const sp = d.cftc["13874+"], nq = d.cftc["20974+"];
  if (sp && nq) {
    say(`Futures (${sp.report_date}): hedge funds are net ${sp.latest.leveraged < 0 ? "short" : "long"} S&P futures, ${psOrd(sp.pct_2y.leveraged)} percentile of two years, while asset managers sit at the ${psOrd(sp.pct_2y.asset_managers)}. ` +
      `In Nasdaq futures hedge funds are at the ${psOrd(nq.pct_2y.leveraged)} and asset managers at the ${psOrd(nq.pct_2y.asset_managers)}.` +
      (sp.pct_2y.asset_managers > 50 && sp.pct_2y.leveraged < 30 ? " Fast money is already light; real money still has length it could sell." : ""));
  }
  const v = d.volatility;
  const vix = v.indices.VIX, vxn = v.indices.VXN, skew = v.indices.SKEW;
  if (vix && vxn) say(`Fear: VIX ${fmt(vix.value, 1)} (${hzSigned(vix.change_5d, 1)} in 5 days, ${psOrd(vix.pct_1y)} percentile of the year), Nasdaq volatility ${fmt(vxn.value, 1)} (${hzSigned(vxn.change_5d, 1)}).`);
  const vn = v.vxn_vs_nasdaq;
  if (vn) {
    const fading = vn.qqq_down_days >= 3 && vn.qqq_down_vxn_down / vn.qqq_down_days >= 0.5;
    say(`Panic check: the Nasdaq fell on ${vn.qqq_down_days} of the last ${vn.sessions} sessions and its volatility fell on ${vn.qqq_down_vxn_down} of those days. ` +
      (fading ? "Volatility falling with prices: the selling is getting orderly, a classic sign a selloff is tiring."
        : vn.qqq_down_days >= 3 ? "Volatility still rises on down days: fear is building, no sign of exhaustion yet." : "Too few down days to read."),
      fading ? "pattern yes" : "");
  }
  if (skew && skew.pct_1y >= 90) say(`Tail hedging: SKEW at ${fmt(skew.value, 0)}, ${psOrd(skew.pct_1y)} percentile of the year. Investors are paying up for crash protection.`);
  if (v.term_ratio) say(`Short-term against 3-month VIX: ${fmt(v.term_ratio.value, 2)}${v.term_ratio.value >= 1 ? ", inverted: near-term stress is priced above later stress." : v.term_ratio.value >= 0.95 ? ", close to inverting." : ", normal upward slope."}`);
  const m = d.market?.scores;
  if (m) say(`Model scores (0–100): leverage ${fmt(m.gross_leverage, 0)}, systematic selling pressure ${fmt(m.systematic_selling, 0)}, liquidity fragility ${fmt(m.liquidity_fragility, 0)}, direction ${hzSigned(m.directional_exposure, 0)} (−100 short to +100 long).`, "note-line");
  const k = d.korea?.latest;
  if (k) say(`Korean retail leverage: ${fmt(k.kospi_margin_tn, 1)} trillion won of margin loans in Kospi stocks, ${pct(k.margin_chg_1w, 1)} in a week and ${pct(k.from_peak, 0)} from the ${k.peak_date} record, while the Kospi is ${pct(k.kospi_from_peak_date, 0)} since then. ` +
    (k.margin_chg_1w <= -0.04 ? "Loans are being cut fast: margin calls are forcing sales." : k.margin_chg_1w >= 0.02 ? "Loans are growing again: retail is buying with borrowed money." : "Loans are roughly steady."));
  say("Light positioning is fuel, not a trigger: it says how hard prices can move once selling stops, not when.", "note-line");
  card.append(lines);
  return card;
}

function psCell(v, { digits = 1, pctFmt = false, hi = null, lo = null } = {}) {
  const td = el("td", { class: "num" }, v == null ? "n/a" : pctFmt ? pct(v, 0) : fmt(v, digits));
  if (v != null && hi != null && v >= hi) td.classList.add("ps-hot");
  if (v != null && lo != null && v <= lo) td.classList.add("ps-cold");
  return td;
}

function renderPositioning(d) {
  const box = pageBox();
  box.replaceChildren();
  const head = el("div", { class: "d-head" });
  head.append(el("h2", {}, "Positioning"), el("div", { class: "d-sub" }, `Who is already leaning which way · prices as of ${d.as_of}`));
  box.append(head, psSummary(d));

  // Futures by trader type
  const fut = el("section", { class: "hz-sec" });
  fut.append(el("h3", {}, "Index futures by trader type"));
  fut.append(el("p", { class: "help" }, "CFTC Traders in Financial Futures, weekly (Tuesday positions, published Friday). Net long minus short as a share of open interest; the percentile compares it with the last two years."));
  const t = el("table", { class: "ps-table" });
  const hr = el("tr");
  ["Index", ...Object.values(PS_SIDES)].forEach((h, i) => hr.append(el("th", { class: i ? "num" : "" }, h)));
  t.append(el("thead"), el("tbody"));
  t.tHead.append(hr);
  for (const [code, c] of Object.entries(d.cftc)) {
    const tr = el("tr", { class: code === ps.contract ? "ps-sel" : "" });
    tr.append(el("td", {}, c.name));
    for (const k of Object.keys(PS_SIDES)) {
      tr.append(el("td", { class: "num" }, `${hzSigned(c.latest[k], 1)}% · ${psOrd(c.pct_2y[k])}`));
    }
    tr.addEventListener("click", () => { ps.contract = code; renderPositioning(d); });
    t.tBodies[0].append(tr);
  }
  const fs = el("div", { class: "ps-scroll" });
  fs.append(t);
  fut.append(fs);
  const c = d.cftc[ps.contract];
  if (c) {
    const s = { dates: c.history.dates };
    psChart(fut, s, { title: `${c.name}: hedge funds (solid) and asset managers (dashed), % of open interest`, values: c.history.leveraged, extra: c.history.asset_managers, digits: 0, band: [0, 0, 0] },
      (i) => `${s.dates[i]}: hedge funds ${hzSigned(c.history.leveraged[i], 1)}%, asset managers ${hzSigned(c.history.asset_managers[i], 1)}%, dealers ${hzSigned(c.history.dealers[i], 1)}%`);
  }
  box.append(fut);

  // Volatility complex
  const vol = el("section", { class: "hz-sec" });
  vol.append(el("h3", {}, "Volatility and hedging"));
  vol.append(el("p", { class: "help" }, "Cboe indices. The percentile compares today with the last year; high means more fear or more hedging than usual."));
  const vt = el("table", { class: "ps-table" });
  vt.append(el("thead"), el("tbody"));
  const vh = el("tr");
  ["Index", "Level", "1 day", "5 days", "Year pct"].forEach((h, i) => vh.append(el("th", { class: i ? "num" : "" }, h)));
  vt.tHead.append(vh);
  for (const k of ["VIX", "VXN", "VIX9D", "VIX3M", "VVIX", "SKEW", "OVX"]) {
    const x = d.volatility.indices[k];
    if (!x) continue;
    const tr = el("tr");
    tr.append(el("td", {}, x.name), psCell(x.value), psCell(x.change_1d, { hi: 2, lo: -2 }), psCell(x.change_5d, { hi: 3, lo: -3 }), psCell(x.pct_1y, { digits: 0, hi: 80, lo: 20 }));
    vt.tBodies[0].append(tr);
  }
  const vs = el("div", { class: "ps-scroll" });
  vs.append(vt);
  vol.append(vs);
  const vxn = d.volatility.indices.VXN;
  if (vxn) {
    const s = { dates: vxn.history.dates };
    psChart(vol, s, { title: "Nasdaq-100 volatility (VXN), last two years", values: vxn.history.values, digits: 0 }, (i) => `${s.dates[i]}: VXN ${fmt(vxn.history.values[i], 1)}`);
  }
  box.append(vol);

  // Margin debt
  const md = d.margin_debt;
  if (md) {
    const sec = el("section", { class: "hz-sec" });
    sec.append(el("h3", {}, "Margin debt"));
    sec.append(el("p", { class: "help" }, "FINRA customer debit balances, monthly, in billions of dollars. Borrowed money in the market; it turns into forced selling when prices fall far enough."));
    const s = { dates: md.history.months.map((m) => `${m}-01`) };
    psChart(sec, s, { title: "Margin debt, last five years (billions of dollars)", values: md.history.values, digits: 0 }, (i) => `${md.history.months[i]}: ${fmt(md.history.values[i], 0)} billion`);
    box.append(sec);
  }

  if (d.korea) box.append(psKorea(d.korea));

  // Stocks
  const st = el("section", { class: "hz-sec" });
  st.append(el("h3", {}, "Stocks: long and short crowding"));
  st.append(el("p", { class: "help" }, "Long side: the model's long-crowding score leans on momentum ranks, so read it next to the moves measured in each stock's own volatility (σ), its distance above the 200-day average in σ, and how closely it trades with GVIP, Goldman's basket of hedge funds' favourite longs. Short side: days to cover, borrow fee and the change in short interest. Orange marks a stretched reading, blue a washed-out one."));
  const chips = el("div", { class: "ranges" });
  for (const [k, label] of [["all", "All"], ...Object.entries(PS_GROUPS)]) {
    const b = el("button", { class: "chip", "aria-pressed": String(ps.group === k) }, label);
    b.addEventListener("click", () => { ps.group = k; renderPositioning(d); });
    chips.append(b);
  }
  st.append(chips);
  const tbl = el("table", { class: "ps-table ps-stocks" });
  tbl.append(el("thead"), el("tbody"));
  const sh = el("tr");
  [["Stock", ""], ["Long crowd", "Model long-crowding score, 0–100"], ["20d σ", "Last 20 sessions in units of the stock's own volatility"], ["6m σ", "Last 120 sessions in volatility units"],
    ["Above 200d", "Distance above the 200-day average, in volatility units"], ["From high", "Below the 1-year high"], ["Trades with crowd", "Correlation with GVIP over 60 sessions"],
    ["Short crowd", "Model short-crowding score, 0–100"], ["Days to cover", "Short interest ÷ average daily volume"], ["Borrow fee", "Annual % to borrow the shares (IBKR)"], ["SI change", "Change in short interest since the last report"]]
    .forEach(([h, tip], i) => sh.append(el("th", { class: i ? "num" : "", title: tip }, h)));
  tbl.tHead.append(sh);
  const order = Object.keys(PS_GROUPS);
  const rank = (g) => (order.includes(g) ? order.indexOf(g) : order.length);
  const rows = d.stocks.filter((r) => ps.group === "all" || r.group === ps.group)
    .sort((a, b) => rank(a.group) - rank(b.group) || a.symbol.localeCompare(b.symbol));
  let lastGroup = null;
  for (const r of rows) {
    if (ps.group === "all" && r.group !== lastGroup) {
      lastGroup = r.group;
      const gh = el("tr", { class: "ps-group" });
      gh.append(el("td", { colspan: "11" }, PS_GROUPS[r.group] || r.group || "Other"));
      tbl.tBodies[0].append(gh);
    }
    const p = r.price || {}, s = r.short_side || {};
    const tr = el("tr", { class: r.symbol === ps.sv ? "ps-sel" : "" });
    if (d.short_volume?.[r.symbol]) tr.addEventListener("click", () => { ps.sv = r.symbol; renderPositioning(d); document.getElementById("ps-sv")?.scrollIntoView({ block: "start" }); });
    const name = el("td");
    name.append(el("strong", {}, r.symbol), el("span", { class: "name" }, r.name || ""));
    tr.append(name,
      psCell(r.scores.long_crowding, { digits: 0, hi: 75, lo: 25 }),
      psCell(p.z_20d, { digits: 1, hi: 1.5, lo: -1.5 }),
      psCell(p.z_120d, { digits: 1, hi: 1.5, lo: -1.5 }),
      psCell(p.above_200d_sigma, { digits: 1, hi: 1.5, lo: -1.5 }),
      psCell(p.from_high, { pctFmt: true, lo: -0.3 }),
      psCell(p.corr_crowd_60d, { digits: 2, hi: 0.8 }),
      psCell(r.scores.short_crowding, { digits: 0, hi: 50 }),
      psCell(s.days_to_cover, { digits: 1, hi: 5 }),
      psCell(s.borrow_fee, { digits: 2, hi: 3 }),
      el("td", { class: "num" }, s.short_interest_change == null ? "n/a" : `${hzSigned(s.short_interest_change, 0)}%`));
    tbl.tBodies[0].append(tr);
  }
  st.append(el("div", { class: "ps-scroll" }, ""));
  st.lastChild.append(tbl);
  box.append(st);
  const sv = d.short_volume?.[ps.sv];
  if (sv) box.append(psShortVolume(ps.sv, sv));
  box.append(el("p", { class: "help" }, "Sources: CFTC, Cboe, FINRA (short interest twice a month, margin debt monthly), OCC stock loans, IBKR borrow file, Yahoo prices. Every figure is a proxy for positioning; nobody publishes the real books."));
}

// Korean retail margin loans: the leverage behind Samsung and Hynix, and how fast it is being cut.
function psKorea(k) {
  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "Korean retail margin"));
  sec.append(el("p", { class: "help" }, "KOFIA, daily, one business day behind, by settlement date. Margin loans are money Korean investors borrowed from brokers to buy stocks; deposits are the cash they hold at brokers. Margin per Kospi point divides Kospi margin loans (billions of won) by the index: it rises when prices fall faster than loans, meaning the holders left are more leveraged. Forced selling ends when loans stop falling."));
  const L = k.latest, h = k.history, n = h.dates.length - 1;
  sec.append(el("p", {}, `${k.as_of}: Kospi margin loans ${fmt(L.kospi_margin_tn, 1)} trillion won (${pct(L.margin_chg_1w, 1)} in a week, ${pct(L.margin_chg_1m, 1)} in a month, ${pct(L.from_peak, 0)} from the ${fmt(L.peak_tn, 1)} trillion record on ${L.peak_date}); Kosdaq ${fmt(L.kosdaq_margin_tn, 1)} trillion; deposits ${fmt(L.deposits_tn, 0)} trillion (${pct(L.deposits_chg_1m, 0)} in a month). Margin per Kospi point ${fmt(L.ratio, 2)}, ${psOrd(L.ratio_pct)} percentile since 2023.`));
  const s = { dates: h.dates };
  const readout = (i) => `${s.dates[i]}: Kospi margin ${fmt(h.kospi_margin_tn[i], 1)}tn, Kosdaq ${fmt(h.kosdaq_margin_tn[i], 1)}tn · deposits ${fmt(h.deposits_tn[i], 0)}tn · Kospi ${h.kospi[i] == null ? "n/a" : fmt(h.kospi[i], 0)} · per point ${h.ratio[i] == null ? "n/a" : fmt(h.ratio[i], 2)}`;
  const charts = [
    psChart(sec, s, { title: "Margin loans, trillions of won: Kospi stocks (solid), Kosdaq (dashed)", values: h.kospi_margin_tn, extra: h.kosdaq_margin_tn, digits: 0 }, readout),
    psChart(sec, s, { title: "Kospi", values: h.kospi, digits: 0 }, readout),
    psChart(sec, s, { title: "Margin per Kospi point, 5-day average (leverage against the market's size)", values: h.ratio, digits: 1 }, readout),
    psChart(sec, s, { title: "Investor cash at brokers, trillions of won", values: h.deposits_tn, digits: 0 }, readout),
  ];
  for (const ch of charts) ch.onMove((i) => charts.forEach((c) => {
    c.cross(i);
    c.wrap.querySelector(".ps-readout").textContent = readout(i ?? n);
  }));
  return sec;
}

// Daily short-sale volume: the raw count people chart, next to the share of volume it is.
function psShortVolume(symbol, sv) {
  const sec = el("section", { class: "hz-sec", id: "ps-sv" });
  sec.append(el("h3", {}, `Short-sale volume: ${symbol}`));
  sec.append(el("p", { class: "help" }, "FINRA's daily count of shares sold short on its reporting venues. Most of it is market makers and ETF dealers selling short to fill buy orders and covering within hours, so the raw count rises and falls with total volume. A spike in the count is mostly a high-volume day; the share of volume sold short shows whether shorts were unusually heavy. Real short positions are in short interest and stock loans above. Click a stock in the table to switch."));
  const n = sv.dates.length - 1;
  const share = (v) => (v == null ? "n/a" : `${Math.round(v * 100)}%`);
  const lo = sv.share_mean - sv.share_sd, hi = sv.share_mean + sv.share_sd;
  const x = (i) => (sv.ema_m[i] ? sv.short_m[i] / sv.ema_m[i] : null);
  const where = (v) => (v > hi ? "above its usual range" : v < lo ? "below its usual range" : "inside its usual range");
  sec.append(el("p", {}, `Last session (${sv.dates[n]}): ${fmt(sv.short_m[n], 1)} million shares sold short, ${fmt(x(n), 1)}× its 20-day average; ${share(sv.share[n])} of volume, ${where(sv.share[n])} (${share(lo)}–${share(hi)} over two years).`));
  const s = { dates: sv.dates };
  const readout = (i) => `${s.dates[i]}: ${fmt(sv.short_m[i], 1)}M short (${fmt(x(i), 1)}× average) · ${share(sv.share[i])} of volume · close ${sv.close[i] == null ? "n/a" : fmt(sv.close[i], 2)}`;
  const charts = [
    psChart(sec, s, { title: "Shares sold short a day, millions (solid), and its 20-day average (dashed)", values: sv.short_m, extra: sv.ema_m, digits: 0 }, readout),
    psChart(sec, s, { title: "Share of volume sold short, % (band: two-year average ± 1 sd)", values: sv.share.map((v) => v * 100), digits: 0, band: [lo * 100, sv.share_mean * 100, hi * 100] }, readout),
    psChart(sec, s, { title: `${symbol} price`, values: sv.close, digits: 0 }, readout),
  ];
  // Move one crosshair, move all three.
  for (const ch of charts) ch.onMove((i) => charts.forEach((c) => {
    c.cross(i);
    c.wrap.querySelector(".ps-readout").textContent = readout(i ?? n);
  }));
  return sec;
}

// ---------- highs and lows: S&P 1500 stocks at new 52-week highs and lows, and what followed ----------

const HL_RANGES = [
  { label: "1 year", days: 365 },
  { label: "5 years", days: 1826 },
  { label: "Since 1991", days: null },
];
const hl = { range: 1826, open: null, sector: null, data: null };

async function showHighLow() {
  const box = pageBox();
  try {
    const res = await fetch("data/highlow.json", { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    renderHighLow(await res.json());
  } catch {
    box.replaceChildren(el("p", { class: "empty" }, "No highs and lows data yet. It is computed each weekday night after the US close."));
  }
}

const hlPct = (v) => (v == null ? "n/a" : `${Math.round(v * 100)}%`);

function hlSummary(d) {
  const L = d.latest, now = d.study.filter((r) => r.now);
  const total = L.nh + L.nl;
  const narrow = L.dd > -0.03 && (L.above200 < 0.5 || L.hp10 < 0.5);
  const washout = now.some((r) => ["washout30", "washout15", "hp10_10", "above200_20", "vix35", "vix_fading"].includes(r.key));
  const card = el("section", { class: `verdict side-${washout ? "cheap" : narrow ? "rich" : "na"}` });
  card.append(el("h3", {}, washout ? "Washout: historically a time to buy" : narrow ? "Index near its high, most stocks not" : "No extreme either way"));
  const lines = el("div", { class: "v-lines" });
  const say = (text, cls = "") => lines.append(el("p", { class: cls }, text));
  say(`${d.as_of}: ${L.nh} of ${L.n} stocks made a new 52-week high and ${L.nl} a new low (${total ? hlPct(L.nh / total) : "n/a"} highs). Over the last 10 sessions highs were ${hlPct(L.hp10)} of the total, lower than on ${100 - Math.round(L.hp10_pct)}% of days since 1991.`);
  say(`${hlPct(L.above200)} of stocks are above their 200-day average (${psOrd(L.above200_pct)} percentile). The S&P 500 is ${L.dd > -0.005 ? "at its high" : `${pct(-L.dd, 1).replace("+", "")} below its high`}, VIX ${fmt(L.vix, 1)}.`);
  if (now.length) say(`Active now: ${now.map((r) => r.label.split(":")[0].toLowerCase()).join("; ")}.`);
  if (narrow) say("A narrow market: the index is carried by a few large stocks while the typical stock lags. Afterwards the S&P 500 did worse than usual on average (12 months: about +6% against +12% on all days), but the spread was wide: 1999, 2007 and 2021 went badly, 1996, 2017 and 2024 well. It is a caution, not a sell signal.", "note-line");
  if (washout) say("Capitulation readings have been the best times to buy in this record. Returns were strongest a year out; the first month is often still rough.", "note-line");
  card.append(lines);
  return card;
}

// The tweet-style board: a bar of highs against lows, then chips grouped by sector.
function hlBoard(d) {
  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "New highs and lows today"));
  sec.append(el("p", { class: "help" }, "S&P 500, 400 and 600 stocks whose high (low) today beat every high (low) of the past year. The small number counts how many of the last 21 sessions made a new high (low): a high count is a stock trending steadily, 1 is a fresh breakout. Hover a ticker for its name, industry and today's move."));
  const { highs, lows } = d.today;
  const total = highs.length + lows.length;
  const bar = el("div", { class: "hl-bar" });
  bar.append(
    el("div", { class: "hl-bar-labels" }, ""),
  );
  const labels = bar.firstChild;
  labels.append(el("span", { class: "hl-hi-text" }, `New highs ${total ? hlPct(highs.length / total) : "n/a"} (${highs.length})`),
    el("span", { class: "hl-lo-text" }, `New lows ${total ? hlPct(lows.length / total) : "n/a"} (${lows.length})`));
  const track = el("div", { class: "hl-track" });
  const g = el("div", { class: "hl-g" });
  g.style.width = `${total ? (100 * highs.length) / total : 50}%`;
  track.append(g);
  bar.append(track);
  sec.append(bar);

  const cols = el("div", { class: "hl-cols" });
  for (const [side, list] of [["hi", highs], ["lo", lows]]) {
    const col = el("div", { class: "hl-col" });
    const groups = new Map();
    for (const x of list) {
      if (!groups.has(x.sector)) groups.set(x.sector, []);
      groups.get(x.sector).push(x);
    }
    const ordered = [...groups.entries()].sort((a, b) => b[1].length - a[1].length);
    if (!ordered.length) col.append(el("p", { class: "help" }, side === "hi" ? "No new highs." : "No new lows."));
    for (const [sector, xs] of ordered) {
      xs.sort((a, b) => b.hits - a.hits);
      const box = el("div", { class: "hl-group" });
      const h = el("div", { class: "hl-group-head" });
      h.append(el("span", {}, sector), el("span", { class: `hl-n hl-${side}-text` }, `${xs.length}`));
      box.append(h);
      const chips = el("div", { class: "hl-chips" });
      for (const x of xs) {
        const c = el("span", { class: `hl-chip hl-${side}`, title: `${x.name} · ${x.industry} · ${pct(x.chg, 1)} today · ${x.hits} new ${side === "hi" ? "highs" : "lows"} in 21 sessions` });
        c.append(document.createTextNode(x.s), el("small", {}, String(x.hits)));
        chips.append(c);
      }
      box.append(chips);
      col.append(box);
    }
    cols.append(col);
  }
  sec.append(cols);
  return sec;
}

// What the S&P 500 did after each signal: one event per signal at most every 60 sessions.
function hlStudy(d) {
  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "When was it a good time to buy?"));
  sec.append(el("p", { class: "help" }, "S&P 500 return after each signal since 1991, median over the events (share of events that ended higher in brackets). A signal counts again only after 60 quiet sessions, so one sell-off is one event. \"Worst in 3 months\" is the median lowest close within three months, the pain before the payoff. Sorted by the 12-month return. Click a row for its dates. Today's members only: delisted losers are missing from the past, so the breadth levels run high; the index returns are real."));
  const H = ["1m", "3m", "6m", "12m"];
  const t = el("table", { class: "ps-table hl-study" });
  t.append(el("thead"), el("tbody"));
  const hr = el("tr");
  ["Signal", "Events", "1 month", "3 months", "6 months", "12 months", "Worst in 3 months", "Last seen"].forEach((h, i) => hr.append(el("th", { class: i ? "num" : "" }, h)));
  t.tHead.append(hr);
  const cell = (m, up) => (m == null ? "n/a" : `${pct(m, 1)} (${Math.round(up * 100)})`);
  const base = d.baseline;
  const better = (r, k) => (r["med_" + k] == null ? "" : r["med_" + k] > base["med_" + k] * 1.25 ? "ps-cold" : r["med_" + k] < base["med_" + k] * 0.75 ? "ps-hot" : "");
  const rows = [...d.study].sort((a, b) => (b.med_12m ?? -1) - (a.med_12m ?? -1));
  for (const r of rows) {
    const tr = el("tr", { class: `${r.now ? "ps-sel" : ""} hl-row` });
    const name = el("td", {}, r.label);
    if (r.now) name.append(el("span", { class: "hl-now" }, "now"));
    tr.append(name, el("td", { class: "num" }, String(r.events)));
    for (const k of H) tr.append(el("td", { class: `num ${better(r, k)}` }, cell(r["med_" + k], r["up_" + k])));
    tr.append(el("td", { class: "num" }, pct(r.pain3m, 1)), el("td", { class: "num" }, r.last ?? "never"));
    tr.addEventListener("click", () => { hl.open = hl.open === r.key ? null : r.key; renderHighLow(d); });
    t.tBodies[0].append(tr);
    if (hl.open === r.key) {
      const dr = el("tr", { class: "hl-dates" });
      dr.append(el("td", { colspan: "8" }, `Events: ${r.dates.join(", ")}`));
      t.tBodies[0].append(dr);
    }
  }
  const btr = el("tr", { class: "hl-base" });
  btr.append(el("td", {}, "Any day (baseline)"), el("td", { class: "num" }, ""));
  for (const k of H) btr.append(el("td", { class: "num" }, cell(base["med_" + k], base["up_" + k])));
  btr.append(el("td", { class: "num" }, pct(base.pain3m, 1)), el("td", { class: "num" }, ""));
  t.tBodies[0].append(btr);
  const sc = el("div", { class: "ps-scroll" });
  sc.append(t);
  sec.append(sc);
  sec.append(el("p", { class: "help" }, "Blue: at least a quarter better than the baseline; amber: at least a quarter worse. The washout signals rest on 5 to 22 events each, so one or two years (2008, 2020) can swing a median."));
  return sec;
}

const DIP_LEVEL = { washout: "Washout (90+)", deep: "Deep (80–90)", dip: "Pullback (60–80)", none: "Normal (under 60)" };
const DIP_REGIME = {
  up: "S&P above its 200-day",
  down: "Below its 200-day, credit calm",
  knife: "Below its 200-day, credit widening (falling knife)",
};
const DIP_VERDICT = {
  beaten: ["Washed out after a bad year", "Score 85+ and down 20% or more over 12 months. Historically beat the S&P 500 over the next year, in both halves of the record: the one sector setup with an edge."],
  with_market: ["Selling with the whole market", "Score 85+ while the market score is 80+. Buy the market rather than the sector: it did about the same as the S&P 500."],
  alone: ["Sold off on its own", "Score 85+ while the market is calm. Sectors trend, so a sell-off of its own has tended to keep lagging the S&P 500."],
  dip: ["Pullback", "Score 60–85. No edge over the S&P 500 on its own."],
  none: ["No dip", "Score under 60."],
};
const dipClass = (lv) => (lv === "washout" ? "ps-cold" : lv === "deep" ? "dip-deep" : "");

function dipMarket(dip) {
  const m = dip.market, all = m.all;
  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "Dip-buying score: S&P 500"));
  sec.append(el("p", { class: "help" }, "How washed out the market is, 0–100: the average percentile of five oversold measures, each ranked only against its own past (no hindsight). Share of stocks above their 50-day and 200-day average, most new 52-week lows on one day in 10 sessions, VIX against its one-year median, the S&P 500 below its 20-day average. The table shows what the S&P 500 (SPY, with dividends) did afterwards, by score and by trend and credit: a falling knife is the S&P under its 200-day while the Baa corporate spread widened more than 0.25 points in three months."));
  const cell = m.cells.find((c) => c.regime === m.regime && c.level === m.level);
  const card = el("div", { class: "dip-gauge" });
  const big = el("div", { class: `dip-score ${dipClass(m.level)}` }, fmt(m.score, 0));
  const txt = el("div");
  txt.append(
    el("div", { class: "dip-level" }, `${DIP_LEVEL[m.level]} · ${DIP_REGIME[m.regime]}`),
    el("div", { class: "help" }, `S&P ${pct(m.spx_vs_200, 1)} against its 200-day; Baa spread ${fmt(m.baa, 2)} (${m.baa_chg_3m >= 0 ? "+" : ""}${fmt(m.baa_chg_3m, 2)} in 3 months).` +
      (cell ? ` In this state before, the S&P 500 did ${pct(cell.med_3m, 1)} over 3 months and ${pct(cell.med_12m, 1)} over 12 (up ${Math.round(cell.up_12m * 100)}% of the time; ${cell.days} days), against ${pct(all.med_12m, 1)} on any day.` : "")),
  );
  card.append(big, txt);
  sec.append(card);
  const comps = { above50: "Stocks above 50-day", above200: "Stocks above 200-day", lows10: "Most new lows in a day, 10 sessions", fear: "VIX vs its 1-year median", stretch: "S&P vs its 20-day average" };
  const show = { above50: (v) => hlPct(-v), above200: (v) => hlPct(-v), lows10: (v) => `${fmt(v * 100, 1)}%`, fear: (v) => `${fmt(v, 2)}×`, stretch: (v) => pct(-v, 1) };
  const cl = el("div", { class: "dip-comps" });
  for (const [k, label] of Object.entries(comps)) {
    const c = m.components[k];
    const row = el("div", { class: "dip-comp" });
    const barBox = el("div", { class: "dip-cbar" });
    const fill = el("div");
    fill.style.width = `${c.pct ?? 0}%`;
    barBox.append(fill);
    row.append(el("span", {}, label), el("span", { class: "num" }, show[k](c.value)), barBox, el("span", { class: "num" }, psOrd(c.pct)));
    cl.append(row);
  }
  sec.append(cl);

  const t = el("table", { class: "ps-table" });
  t.append(el("thead"), el("tbody"));
  const hr = el("tr");
  ["Trend and credit", "Score", "Days", "1 month", "3 months", "12 months", "12m, 1993–2008", "12m, 2009–", "Worst in 3 months"].forEach((h, i) => hr.append(el("th", { class: i > 1 ? "num" : "" }, h)));
  t.tHead.append(hr);
  const c2 = (v, up) => (v == null ? "n/a" : up == null ? pct(v, 1) : `${pct(v, 1)} (${Math.round(up * 100)})`);
  const better = (v) => (v == null ? "" : v > all.med_12m * 1.25 ? "ps-cold" : v < all.med_12m * 0.75 ? "ps-hot" : "");
  for (const c of m.cells) {
    const tr = el("tr", { class: c.regime === m.regime && c.level === m.level ? "ps-sel" : "" });
    tr.append(el("td", {}, DIP_REGIME[c.regime]), el("td", {}, DIP_LEVEL[c.level]), el("td", { class: "num" }, String(c.days)),
      el("td", { class: "num" }, c2(c.med_1m, c.up_1m)), el("td", { class: "num" }, c2(c.med_3m, c.up_3m)),
      el("td", { class: `num ${better(c.med_12m)}` }, c2(c.med_12m, c.up_12m)),
      el("td", { class: `num ${better(c.early_12m)}` }, c2(c.early_12m)), el("td", { class: `num ${better(c.late_12m)}` }, c2(c.late_12m)),
      el("td", { class: "num" }, pct(c.pain3m, 1)));
    t.tBodies[0].append(tr);
  }
  const btr = el("tr", { class: "hl-base" });
  btr.append(el("td", {}, "Any day (baseline)"), el("td"), el("td", { class: "num" }, String(all.days)), el("td", { class: "num" }, c2(all.med_1m, all.up_1m)),
    el("td", { class: "num" }, c2(all.med_3m, all.up_3m)), el("td", { class: "num" }, c2(all.med_12m, all.up_12m)),
    el("td", { class: "num" }, c2(all.early_12m)), el("td", { class: "num" }, c2(all.late_12m)), el("td", { class: "num" }, pct(all.pain3m, 1)));
  t.tBodies[0].append(btr);
  const sc = el("div", { class: "ps-scroll" });
  sc.append(t);
  sec.append(sc);
  sec.append(el("p", { class: "help" }, "Days, not events: neighbouring days overlap, so a row of 300 days may be a handful of sell-offs. Read across both halves of the record; a row that only worked after 2009 leans on the Fed rescuing every dip."));
  const s = m.history;
  const hs = { dates: s.dates.slice(-2520) };
  const sh = s.score.slice(-2520), px = s.spx.slice(-2520);
  const readout = (i) => `${hs.dates[i]}: score ${fmt(sh[i], 0)} · S&P 500 ${fmt(px[i], 0)}`;
  const charts = [
    psChart(sec, hs, { title: "Dip-buying score, last 10 years (shaded 80–90; above 90 is a washout)", values: sh, digits: 0, band: [80, 90, 90] }, readout),
    psChart(sec, hs, { title: "S&P 500", values: px, digits: 0 }, readout),
  ];
  for (const ch of charts) ch.onMove((i) => charts.forEach((c) => {
    c.cross(i);
    c.wrap.querySelector(".ps-readout").textContent = readout(i ?? hs.dates.length - 1);
  }));
  return sec;
}

function dipSectors(dip) {
  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "Dip-buying score: sectors"));
  sec.append(el("p", { class: "help" }, "The same idea within each sector: share of its S&P 1500 members above their 50-day and 200-day average, most new lows in a day over 10 sessions, its equal-weighted index below its 20-day average. Returns are the SPDR sector ETFs (SMH for semiconductors) with dividends, against SPY. A washed-out sector is not on its own a buy: what matters is why it is washed out. Click a sector for its history."));
  const t = el("table", { class: "ps-table" });
  t.append(el("thead"), el("tbody"));
  const hr = el("tr");
  ["Sector", "Score", "Above 50-day", "Above 200-day", "1 month", "12 months", "Setup"].forEach((h, i) => hr.append(el("th", { class: i && i < 6 ? "num" : "" }, h)));
  t.tHead.append(hr);
  const rows = [...dip.sectors].sort((a, b) => b.score - a.score);
  for (const x of rows) {
    const tr = el("tr", { class: `hl-row ${hl.sector === x.sector ? "ps-sel" : ""}` });
    const name = el("td", {}, x.sector);
    name.append(el("span", { class: "name" }, `${x.etf} · ${x.members} stocks`));
    tr.append(name, el("td", { class: `num ${dipClass(level(x.score))}` }, fmt(x.score, 0)),
      el("td", { class: "num" }, hlPct(x.above50)), el("td", { class: "num" }, hlPct(x.above200)),
      el("td", { class: "num" }, pct(x.chg_1m, 1)), el("td", { class: "num" }, pct(x.mom12, 0)),
      el("td", { title: DIP_VERDICT[x.verdict][1] }, DIP_VERDICT[x.verdict][0]));
    tr.addEventListener("click", () => { hl.sector = hl.sector === x.sector ? null : x.sector; renderHighLow(hl.data); });
    t.tBodies[0].append(tr);
  }
  const sc = el("div", { class: "ps-scroll" });
  sc.append(t);
  sec.append(sc);

  sec.append(el("h4", {}, "What each setup did afterwards (all sectors pooled, 1999–)"));
  const vt = el("table", { class: "ps-table" });
  vt.append(el("thead"), el("tbody"));
  const vh = el("tr");
  ["Setup", "Days", "ETF, 12 months", "vs S&P, 3 months", "vs S&P, 12 months", "vs S&P 12m, 1999–2008", "vs S&P 12m, 2009–"].forEach((h, i) => vh.append(el("th", { class: i ? "num" : "" }, h)));
  vt.tHead.append(vh);
  const sign = (v) => (v == null ? "" : v > 0.02 ? "ps-cold" : v < -0.01 ? "ps-hot" : "");
  for (const v of dip.sector_verdicts) {
    const tr = el("tr");
    const name = el("td", {}, DIP_VERDICT[v.verdict][0]);
    name.append(el("span", { class: "name dip-why" }, DIP_VERDICT[v.verdict][1]));
    tr.append(name, el("td", { class: "num" }, String(v.days)), el("td", { class: "num" }, pct(v.med_12m, 1)),
      el("td", { class: `num ${sign(v.rel_3m)}` }, pct(v.rel_3m, 1)),
      el("td", { class: `num ${sign(v.rel_12m)}` }, `${pct(v.rel_12m, 1)} (${Math.round(v.beat_12m * 100)})`),
      el("td", { class: `num ${sign(v.early_12m)}` }, pct(v.early_12m, 1)), el("td", { class: `num ${sign(v.late_12m)}` }, pct(v.late_12m, 1)));
    vt.tBodies[0].append(tr);
  }
  const vs = el("div", { class: "ps-scroll" });
  vs.append(vt);
  sec.append(vs);
  sec.append(el("p", { class: "help" }, "Median return over the S&P 500 (share of days the sector beat it in brackets). Sector ETFs start in December 1998; XLRE in 2015, XLC in 2018."));

  const x = dip.sectors.find((s) => s.sector === hl.sector);
  if (x) {
    const h = x.history, s = { dates: h.dates };
    const readout = (i) => `${s.dates[i]}: score ${fmt(h.score[i], 0)} · ${x.etf} ${fmt(h.price[i], 2)}`;
    const charts = [
      psChart(sec, s, { title: `${x.sector}: dip-buying score, last 5 years (shaded 85–100)`, values: h.score, digits: 0, band: [85, 85, 100] }, readout),
      psChart(sec, s, { title: `${x.etf}, with dividends`, values: h.price, digits: 0 }, readout),
    ];
    for (const ch of charts) ch.onMove((i) => charts.forEach((c) => {
      c.cross(i);
      c.wrap.querySelector(".ps-readout").textContent = readout(i ?? s.dates.length - 1);
    }));
  }
  return sec;
}

const level = (v) => (v == null ? null : v >= 90 ? "washout" : v >= 80 ? "deep" : v >= 60 ? "dip" : "none");

function renderHighLow(d) {
  hl.data = d;
  const box = pageBox();
  box.replaceChildren();
  const head = el("div", { class: "d-head" });
  head.append(el("h2", {}, "Highs & lows"), el("div", { class: "d-sub" }, `S&P 1500 stocks at new 52-week highs and lows · data as of ${d.as_of}`));
  box.append(head, hlSummary(d));
  if (d.dip) box.append(dipMarket(d.dip), dipSectors(d.dip));
  box.append(hlBoard(d), hlStudy(d));

  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "History"));
  const ranges = el("div", { class: "ranges" });
  for (const r of HL_RANGES) {
    const b = el("button", { class: "chip", "aria-pressed": String(hl.range === r.days) }, r.label);
    b.addEventListener("click", () => { hl.range = r.days; renderHighLow(d); });
    ranges.append(b);
  }
  sec.append(ranges);
  box.append(sec);
  const h = d.history;
  let from = 0;
  if (hl.range) {
    const last = dayNum(h.dates[h.dates.length - 1]);
    from = Math.max(0, h.dates.findIndex((x) => dayNum(x) >= last - hl.range));
  }
  const s = Object.fromEntries(Object.entries(h).map(([k, v]) => [k, v.slice(from)]));
  const n = s.dates.length - 1;
  const readout = (i) => `${s.dates[i]}: S&P 500 ${fmt(s.spx[i], 0)} (${pct(s.dd[i], 1)} from high) · ${s.nh[i]} highs, ${s.nl[i]} lows · 10-day share of highs ${hlPct(s.hp10[i])} · ${hlPct(s.above200[i])} above 200-day · VIX ${fmt(s.vix[i], 1)}`;
  const charts = [
    psChart(sec, s, { title: "S&P 500", values: s.spx, digits: 0 }, readout),
    psChart(sec, s, { title: "Share of highs over 10 sessions, % (shaded 10–50; under 10 is a washout)", values: s.hp10.map((v) => (v == null ? null : v * 100)), digits: 0, band: [10, 50, 50] }, readout),
    psChart(sec, s, { title: "Stocks above their 200-day average, % (shaded 20–50)", values: s.above200.map((v) => (v == null ? null : v * 100)), digits: 0, band: [20, 50, 50] }, readout),
    psChart(sec, s, { title: "New highs (solid) and new lows (dashed), number of stocks", values: s.nh, extra: s.nl, digits: 0 }, readout),
  ];
  for (const ch of charts) ch.onMove((i) => charts.forEach((c) => {
    c.cross(i);
    c.wrap.querySelector(".ps-readout").textContent = readout(i ?? n);
  }));
}

// ---------- AI demand: tokens, lab revenue, hyperscaler capex and contracted backlog ----------

const CP_MAKERS = { anthropic: "Anthropic", openai: "OpenAI", google: "Google", deepseek: "DeepSeek", "x-ai": "xAI", qwen: "Qwen (Alibaba)", "z-ai": "Z.ai", minimax: "MiniMax", xiaomi: "Xiaomi", tencent: "Tencent", stealth: "Stealth (unnamed)", "meta-llama": "Meta", mistralai: "Mistral", Others: "Others" };
const CP_CO = { MSFT: "Microsoft", GOOGL: "Alphabet", AMZN: "Amazon", META: "Meta", ORCL: "Oracle", CRWV: "CoreWeave" };
const cp = { range: null };

async function showCompute() {
  const box = pageBox();
  try {
    const res = await fetch("data/compute.json", { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    renderCompute(await res.json());
  } catch {
    box.replaceChildren(el("p", { class: "empty" }, "No AI demand data yet. It is collected each weekday night."));
  }
}

const tn = (v, d = 1) => (v == null ? "n/a" : `${fmt(v / 1e12, d)}T`);
const bn = (v, d = 0) => (v == null ? "n/a" : `$${fmt(v, d)}bn`);
const growth = (a, b) => (a == null || b == null || !b ? null : a / b - 1);

function cpSummary(d) {
  const o = d.openrouter, s = d.sec;
  const n = o.weeks.length - (o.last_week_partial ? 2 : 1);
  const at = (k) => (n - k >= 0 ? o.total[n - k] : null);
  const share = (m, i) => (o.by_maker[m] ? o.by_maker[m][i] / o.total[i] : null);
  const qi = s.capex_total_bn.findLastIndex((v) => v != null);
  const card = el("section", { class: "verdict" });
  card.append(el("h3", {}, "How much AI compute is being used and paid for"));
  const lines = el("div", { class: "v-lines" });
  const say = (t, c = "") => lines.append(el("p", { class: c }, t));
  say(`Tokens on OpenRouter, week of ${o.weeks[n]}: ${tn(o.total[n])}, ${pct(growth(at(0), at(4)), 0)} in 4 weeks, ${pct(growth(at(0), at(13)), 0)} in 13 weeks, ${n >= 52 ? `${pct(growth(at(0), at(52)), 0)} in a year` : `${pct(growth(at(0), o.total[0]), 0)} since ${o.weeks[0]}`}. Anthropic models ${hlPct(share("anthropic", n))} of them (${hlPct(share("anthropic", Math.max(0, n - 13)))} 13 weeks earlier).`);
  if (qi >= 0) say(`Capex of Microsoft, Alphabet, Amazon, Meta and Oracle: ${bn(s.capex_total_bn[qi])} in ${s.quarters[qi]}, ${pct(growth(s.capex_total_bn[qi], s.capex_total_bn[qi - 4]), 0)} on a year earlier: about ${bn(s.capex_total_bn[qi] * 4)} a year.`);
  const rpo = Object.entries(s.rpo).map(([t, r]) => [t, r.bn[r.bn.length - 1], r.dates[r.dates.length - 1]]);
  if (rpo.length) say(`Contracted, not yet billed revenue (remaining performance obligations): ${rpo.map(([t, v, dt]) => `${CP_CO[t]} ${bn(v)} (${dt})`).join(", ")}. Total ${bn(rpo.reduce((a, r) => a + r[1], 0))}.`);
  const latest = (series) => (d.disclosed.points ?? []).filter((p) => p.series === series).sort((a, b) => a.date.localeCompare(b.date)).pop();
  const ar = latest("anthropic_revenue_runrate"), or = latest("openai_revenue_runrate");
  if (ar && or) say(`Paid demand at the two biggest labs: Anthropic's revenue run-rate ${bn(ar.value)} (${ar.date}), OpenAI's ${bn(or.value)} (${or.date}). Anthropic's share of the two: ${hlPct(ar.value / (ar.value + or.value))}. Run-rates are the latest month × 12.`);
  const com = (d.disclosed.commitments ?? []).filter((c) => !/negotiation/i.test(c.counterparty));
  if (com.length && rpo.length) say(`Anthropic alone has committed ${d.disclosed.commitments_total_bn ? `more than ${bn(d.disclosed.commitments_total_bn)}` : `about ${bn(com.reduce((a, c) => a + c.amount_bn, 0))}`} to compute over the next decade, against ${bn(rpo.reduce((a, r) => a + r[1], 0))} of contracted backlog at the clouds above: a large slice of the industry's committed demand rests on a few labs.`);
  say("OpenRouter is a router for developers. It leans to cheap open models and misses most direct use of Claude, ChatGPT and Gemini, so read it for growth and for the price-sensitive end, not for market share.", "note-line");
  card.append(lines);
  return card;
}

function cpTokens(d) {
  const o = d.openrouter;
  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "Tokens on OpenRouter, by model maker"));
  sec.append(el("p", { class: "help" }, "Weekly tokens processed through OpenRouter's API, from its public rankings. The latest week is still running and is left out."));
  const n = o.weeks.length - (o.last_week_partial ? 1 : 0);
  const s = { dates: o.weeks.slice(0, n) };
  const tot = o.total.slice(0, n);
  const sh = (m) => o.by_maker[m].slice(0, n).map((v, i) => (tot[i] ? (100 * v) / tot[i] : null));
  const readout = (i) => `${s.dates[i]}: ${tn(tot[i])} · Anthropic ${fmt(sh("anthropic")[i], 1)}% · OpenAI ${fmt(sh("openai")[i], 1)}% · Google ${fmt(sh("google")[i], 1)}%`;
  const charts = [
    psChart(sec, s, { title: "Tokens a week, trillions", values: tot.map((v) => v / 1e12), digits: 0 }, readout),
    psChart(sec, s, { title: "Share of tokens, %: Anthropic (solid), OpenAI (dashed)", values: sh("anthropic"), extra: sh("openai"), digits: 0 }, readout),
  ];
  for (const ch of charts) ch.onMove((i) => charts.forEach((c) => {
    c.cross(i);
    c.wrap.querySelector(".ps-readout").textContent = readout(i ?? s.dates.length - 1);
  }));
  const last = n - 1, then = Math.max(0, n - 14);
  const t = el("table", { class: "ps-table" });
  t.append(el("thead"), el("tbody"));
  const hr = el("tr");
  ["Model maker", `Week of ${o.weeks[last]}`, "Share", "Share 13 weeks earlier", "Tokens vs 13 weeks earlier"].forEach((h, i) => hr.append(el("th", { class: i ? "num" : "" }, h)));
  t.tHead.append(hr);
  const makers = Object.keys(o.by_maker).sort((a, b) => o.by_maker[b][last] - o.by_maker[a][last]);
  for (const m of makers) {
    const v = o.by_maker[m];
    if (!v[last] && !v[then]) continue;
    const tr = el("tr", { class: m === "anthropic" ? "ps-sel" : "" });
    tr.append(el("td", {}, CP_MAKERS[m] ?? m), el("td", { class: "num" }, tn(v[last])), el("td", { class: "num" }, hlPct(v[last] / o.total[last])),
      el("td", { class: "num" }, hlPct(v[then] / o.total[then])), el("td", { class: "num" }, v[then] ? pct(v[last] / v[then] - 1, 0) : "new"));
    t.tBodies[0].append(tr);
  }
  const sc = el("div", { class: "ps-scroll" });
  sc.append(t);
  sec.append(sc);
  return sec;
}

function cpCapex(d) {
  const s = d.sec;
  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "Hyperscaler capex and contracted backlog"));
  sec.append(el("p", { class: "help" }, "From the companies' SEC filings (XBRL), each quarter. Capex is cash spent on property and equipment; Microsoft's and Oracle's headline figures also count finance leases, so theirs here run lower. Quarters are calendar quarters (Microsoft's fiscal year ends in June, Oracle's in May). Remaining performance obligations are signed contracts not yet billed: for these companies mostly multi-year cloud and AI compute deals, so they show demand already committed for the next years. Amazon no longer reports its backlog in tagged form; Meta sells no cloud."));
  const k = s.quarters.length;
  const from = Math.max(0, k - 9);
  const t = el("table", { class: "ps-table" });
  t.append(el("thead"), el("tbody"));
  const hr = el("tr");
  ["Capex, $bn", ...s.quarters.slice(from), "vs year before"].forEach((h, i) => hr.append(el("th", { class: i ? "num" : "" }, h)));
  t.tHead.append(hr);
  const addRow = (label, vals, cls = "") => {
    const tr = el("tr", { class: cls });
    tr.append(el("td", {}, label));
    for (let i = from; i < k; i++) tr.append(el("td", { class: "num" }, vals[i] == null ? "" : fmt(vals[i], 1)));
    const li = vals.findLastIndex((v) => v != null);
    tr.append(el("td", { class: "num" }, li >= 4 ? pct(growth(vals[li], vals[li - 4]), 0) : ""));
    t.tBodies[0].append(tr);
  };
  for (const [tk, vals] of Object.entries(s.capex_bn)) addRow(CP_CO[tk] ?? tk, vals);
  addRow("Big five (without CoreWeave)", s.capex_total_bn, "hl-base");
  const sc = el("div", { class: "ps-scroll" });
  sc.append(t);
  sec.append(sc);
  const qn = s.capex_total_bn.findLastIndex((v) => v != null) + 1;
  const qs = { dates: s.quarters.slice(0, qn).map((q) => `${q.slice(0, 4)}-${String(Number(q.slice(5)) * 3).padStart(2, "0")}-28`) };
  psChart(sec, qs, { title: "Big-five capex a quarter, $bn", values: s.capex_total_bn.slice(0, qn), digits: 0 }, (i) => `${s.quarters[i]}: ${bn(s.capex_total_bn[i])}${i >= 4 ? ` (${pct(growth(s.capex_total_bn[i], s.capex_total_bn[i - 4]), 0)} on a year earlier)` : ""}`);
  for (const [tk, r] of Object.entries(s.rpo)) {
    const rs = { dates: r.dates };
    psChart(sec, rs, { title: `${CP_CO[tk]}: remaining performance obligations, $bn`, values: r.bn, digits: 0 }, (i) => `${r.dates[i]}: ${bn(r.bn[i])}${i >= 4 ? ` (${pct(growth(r.bn[i], r.bn[i - 4]), 0)} on a year earlier)` : ""}`);
  }
  return sec;
}

function cpDisclosed(d) {
  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "What the companies themselves said"));
  sec.append(el("p", { class: "help" }, "Figures stated by the companies (earnings calls, events, filings) or reported from their documents, collected with sources; added to as new ones appear. Hover a value for the quote. Italic rows rest on a secondary source or an approximate date. Run-rates are the latest month times twelve, so they run ahead of booked revenue."));
  const D = d.disclosed;
  if (D.commitments?.length) {
    sec.append(el("h4", {}, D.commitments_title ?? "Anthropic's compute commitments"));
    const t = el("table", { class: "ps-table" });
    t.append(el("thead"), el("tbody"));
    const hr = el("tr");
    ["With", "Amount", "What", "Source"].forEach((h, i) => hr.append(el("th", { class: i === 1 ? "num" : "" }, h)));
    t.tHead.append(hr);
    for (const c of D.commitments) {
      const tr = el("tr");
      const src = el("td");
      src.append(el("a", { href: c.url, target: "_blank", rel: "noopener" }, c.source));
      tr.append(el("td", {}, c.counterparty), el("td", { class: "num" }, bn(c.amount_bn)), el("td", {}, c.what), src);
      t.tBodies[0].append(tr);
    }
    const sc = el("div", { class: "ps-scroll" });
    sc.append(t);
    sec.append(sc);
  }
  const groups = new Map();
  for (const p of D.points ?? []) {
    if (!groups.has(p.series)) groups.set(p.series, []);
    groups.get(p.series).push(p);
  }
  for (const [series, pts] of groups) {
    pts.sort((a, b) => a.date.localeCompare(b.date));
    sec.append(el("h4", {}, D.series_names?.[series] ?? series));
    const units = new Set(pts.map((p) => p.unit));
    if (pts.length >= 3 && units.size === 1) {
      const s = { dates: pts.map((p) => p.date) };
      psChart(sec, s, { title: pts[0].unit, values: pts.map((p) => p.value), digits: 0 }, (i) => `${pts[i].date}: ${fmt(pts[i].value, pts[i].value < 10 ? 1 : 0)} ${pts[i].unit} (${pts[i].who})`);
    }
    const t = el("table", { class: "ps-table" });
    t.append(el("thead"), el("tbody"));
    const hr = el("tr");
    ["Date", "Figure", "Said by", "Source"].forEach((h, i) => hr.append(el("th", { class: i === 1 ? "num" : "" }, h)));
    t.tHead.append(hr);
    for (const p of pts) {
      const tr = el("tr");
      const src = el("td");
      src.append(el("a", { href: p.url, target: "_blank", rel: "noopener" }, p.where || "link"));
      tr.append(el("td", {}, p.date), el("td", { class: "num", title: [p.quote, p.note].filter(Boolean).join(" · ") }, `${fmt(p.value, p.value < 10 ? 2 : p.value < 100 ? 1 : 0)} ${p.unit}`), el("td", {}, p.who ?? ""), src);
      if (p.note) tr.classList.add("cp-uncertain");
      t.tBodies[0].append(tr);
    }
    const sc = el("div", { class: "ps-scroll" });
    sc.append(t);
    sec.append(sc);
  }
  return sec;
}

// One chart for everything: each line divided by its own latest value, on a log scale, so the
// slope is the growth rate whatever the unit (tokens, dollars, users, an index).
const CP_LINE_COLOR = {
  openrouter: "--cp-c1", google_tokens: "--cp-c2", google_api: "--cp-c3", bytedance: "--cp-c4",
  anthropic_rr: "--cp-c5", openai_rr: "--cp-c6", gemini_users: "--cp-c7", chatgpt_users: "--cp-c7",
  capex: "--cp-c8", backlog: "--cp-c9", dram: "--cp-c10",
};
const CP_ALL_RANGES = [
  { label: "1 year", days: 365 },
  { label: "2 years", days: 730 },
  { label: "Since 2019", days: null },
];
const cpAll = { range: 730, off: new Set() };

// Value at a day by log-linear interpolation between the points around it; null outside the series.
function cpAt(line, t) {
  const ts = line.ts;
  if (t < ts[0] || t > ts[ts.length - 1]) return null;
  let i = ts.findIndex((x) => x >= t);
  if (ts[i] === t) return line.values[i];
  const a = i - 1, f = (t - ts[a]) / (ts[i] - ts[a]);
  return Math.exp(Math.log(line.values[a]) * (1 - f) + Math.log(line.values[i]) * f);
}

function cpYearGrowth(line) {
  const last = line.ts[line.ts.length - 1];
  const then = cpAt(line, last - 365);
  if (then) return { x: line.values[line.values.length - 1] / then, approx: false };
  const span = last - line.ts[0];
  if (span < 90) return null;
  return { x: (line.values[line.values.length - 1] / line.values[0]) ** (365 / span), approx: true };
}

function cpCombined(d) {
  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "Everything in one chart"));
  sec.append(el("p", { class: "help" }, "Each line is divided by its own latest value and drawn on a log scale, so every line ends at 1 and a steeper line is faster growth, whatever its unit. A line that rose 10× ends one gridline above where it started. Dots are the dates a company stated a figure; between them the line is drawn straight. Click a name to hide or show it. The number after each name is its growth over the last year (~ where the series is younger than a year, scaled to a year)."));
  const ranges = el("div", { class: "ranges" });
  for (const r of CP_ALL_RANGES) {
    const b = el("button", { class: "chip", "aria-pressed": String(cpAll.range === r.days) }, r.label);
    b.addEventListener("click", () => { cpAll.range = r.days; renderCompute(d); });
    ranges.append(b);
  }
  sec.append(ranges);

  const lines = d.combined.map((l) => ({ ...l, ts: l.dates.map(dayNum) }));
  const end = Math.max(...lines.map((l) => l.ts[l.ts.length - 1]));
  const start = cpAll.range ? end - cpAll.range : Math.min(...lines.map((l) => l.ts[0]));
  const shown = lines.filter((l) => !cpAll.off.has(l.key));
  // Log of value ÷ latest, over the visible window.
  let lo = 0;
  for (const l of shown) {
    const last = l.values[l.values.length - 1];
    l.ys = l.values.map((v) => Math.log10(v / last));
    l.ts.forEach((t, i) => { if (t >= start) lo = Math.min(lo, l.ys[i]); });
    const edge = cpAt(l, start);
    if (edge) lo = Math.min(lo, Math.log10(edge / last));
  }
  lo = Math.floor(lo) === lo ? lo - 0.25 : Math.floor(lo * 2) / 2;
  const hi = 0.15;
  const W = 900, H = 420, L = 64, R = 14, T = 12, B = 28;
  const xOf = (t) => L + ((t - start) / (end - start)) * (W - L - R);
  const yOf = (v) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);
  const wrap = el("div", { class: "chart cp-big" });
  const readout = el("div", { class: "help ps-readout" });
  wrap.append(readout);
  const root = svg("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "AI demand measures, each relative to its latest value, log scale" });
  wrap.append(root);
  const grid = svg("g", { class: "grid" });
  for (let k = Math.ceil(lo); k <= 0; k++) {
    grid.append(svg("line", { x1: L, x2: W - R, y1: yOf(k), y2: yOf(k) }));
    const lab = svg("text", { x: L - 6, y: yOf(k) + 4, "text-anchor": "end", class: "tick" });
    lab.textContent = k === 0 ? "today" : `÷${10 ** -k >= 1000 ? `${10 ** -k / 1000}k` : 10 ** -k}`;
    grid.append(lab);
  }
  for (const f of [0, 0.25, 0.5, 0.75, 1]) {
    const t = start + f * (end - start);
    const lab = svg("text", { x: xOf(t), y: H - 8, "text-anchor": f === 0 ? "start" : f === 1 ? "end" : "middle", class: "tick" });
    lab.textContent = new Date(t * DAY).toISOString().slice(0, 7);
    grid.append(lab);
  }
  root.append(grid);
  const clip = svg("clipPath", { id: "cp-clip" });
  clip.append(svg("rect", { x: L, y: T, width: W - L - R, height: H - T - B }));
  root.append(clip);
  const plot = svg("g", { "clip-path": "url(#cp-clip)" });
  root.append(plot);
  for (const l of shown) {
    const color = `var(${CP_LINE_COLOR[l.key] ?? "--line"})`;
    let path = "";
    l.ts.forEach((t, i) => { path += `${i ? "L" : "M"}${xOf(t).toFixed(1)},${yOf(l.ys[i]).toFixed(1)}`; });
    plot.append(svg("path", { d: path, fill: "none", stroke: color, "stroke-width": l.values.length > 40 ? 1.6 : 2, "stroke-linejoin": "round" }));
    if (l.values.length <= 40) l.ts.forEach((t, i) => plot.append(svg("circle", { cx: xOf(t), cy: yOf(l.ys[i]), r: 3.2, fill: color })));
  }
  const cross = svg("line", { class: "cross", y1: T, y2: H - B, visibility: "hidden" });
  root.append(cross);
  const hit = svg("rect", { class: "hit", x: L, y: T, width: W - L - R, height: H - T - B });
  root.append(hit);
  const say = (t) => {
    if (t == null) {
      readout.textContent = "Hover the chart to read every line on one date.";
      return;
    }
    const parts = shown.map((l) => [l, cpAt(l, t)]).filter(([, v]) => v != null)
      .map(([l, v]) => `${l.label} ${fmt((100 * v) / l.values[l.values.length - 1], v / l.values[l.values.length - 1] < 0.1 ? 1 : 0)}%`);
    readout.textContent = `${new Date(t * DAY).toISOString().slice(0, 10)}, as % of today: ${parts.join(" · ") || "no data"}`;
  };
  say(null);
  hit.addEventListener("pointermove", (e) => {
    const r = root.getBoundingClientRect();
    const x = ((e.clientX - r.left) / r.width) * W;
    const t = Math.round(start + ((x - L) / (W - L - R)) * (end - start));
    cross.setAttribute("x1", xOf(t));
    cross.setAttribute("x2", xOf(t));
    cross.setAttribute("visibility", "visible");
    say(t);
  });
  hit.addEventListener("pointerleave", () => { cross.setAttribute("visibility", "hidden"); say(null); });
  sec.append(wrap);

  const legend = el("div", { class: "cp-legend" });
  const groups = { tokens: "Tokens", revenue: "Lab revenue", users: "Users", spend: "Capex and backlog", memory: "Memory prices" };
  for (const [g, name] of Object.entries(groups)) {
    const ls = lines.filter((l) => l.group === g);
    if (!ls.length) continue;
    const col = el("div", { class: "cp-lgroup" });
    col.append(el("div", { class: "cp-lhead" }, name));
    for (const l of ls) {
      const gr = cpYearGrowth(l);
      const item = el("button", { class: "cp-litem", "aria-pressed": String(!cpAll.off.has(l.key)) });
      const sw = el("span", { class: "cp-swatch" });
      sw.style.background = `var(${CP_LINE_COLOR[l.key] ?? "--line"})`;
      item.append(sw, el("span", {}, l.label), el("span", { class: "cp-growth" }, gr ? `${gr.approx ? "~" : ""}${fmt(gr.x, gr.x < 10 ? 1 : 0)}×` : ""));
      item.title = `Latest ${l.dates[l.dates.length - 1]}: ${fmt(l.values[l.values.length - 1], 1)} ${l.unit}`;
      item.addEventListener("click", () => {
        if (cpAll.off.has(l.key)) cpAll.off.delete(l.key); else cpAll.off.add(l.key);
        renderCompute(d);
      });
      col.append(item);
    }
    legend.append(col);
  }
  sec.append(legend);
  return sec;
}

function renderCompute(d) {
  const box = pageBox();
  box.replaceChildren();
  const head = el("div", { class: "d-head" });
  head.append(el("h2", {}, "AI demand"), el("div", { class: "d-sub" }, `Tokens, lab revenue, hyperscaler capex and backlog · updated ${d.generated.slice(0, 10)}`));
  box.append(head, cpSummary(d));
  if (d.combined) box.append(cpCombined(d));
  box.append(cpDisclosed(d), cpCapex(d), cpTokens(d));
}

// ---------- markets: indexes, rates, credit, FX, commodities, crypto as the reference frame ----------

const MK_RANGES = [
  { label: "1 year", days: 365 },
  { label: "2 years", days: 730 },
  { label: "5 years", days: null },
];
const mk = { sel: "^GSPC", range: 365 };

async function showMarkets() {
  const box = pageBox();
  try {
    const res = await fetch("data/markets.json", { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    renderMarkets(await res.json());
  } catch {
    box.replaceChildren(el("p", { class: "empty" }, "No market data yet. It is collected each weekday night."));
  }
}

const mkYield = (s) => s.unit === "%";
function mkLevel(s, v) {
  if (v == null) return "n/a";
  if (mkYield(s)) return `${v.toFixed(2)}%`;
  const a = Math.abs(v);
  return a >= 1000 ? Math.round(v).toLocaleString("en-US") : a >= 10 ? v.toFixed(2) : v.toFixed(4);
}
// Prices move in percent, yields and spreads in basis points. Up isn't good or bad for a
// yield or a spread, so those stay uncoloured.
function mkChange(s, v) {
  if (v == null) return el("td", { class: "num muted" }, "n/a");
  if (mkYield(s)) return el("td", { class: "num" }, `${hzSigned(v * 100, 0)} bp`);
  return el("td", { class: `num ret ${v >= 0 ? "pos" : "neg"}` }, pct(v, 1));
}

function mkSummary(d) {
  const card = el("div", { class: "card hz-summary" });
  const highs = d.series.filter((s) => s.pct_1y >= 97).map((s) => s.name);
  const lows = d.series.filter((s) => s.pct_1y != null && s.pct_1y <= 3).map((s) => s.name);
  const lines = [];
  if (highs.length) lines.push(`At or near a 1-year high: ${highs.join(", ")}.`);
  if (lows.length) lines.push(`At or near a 1-year low: ${lows.join(", ")}.`);
  const big = d.series
    .filter((s) => s.chg["1w"] != null && !mkYield(s))
    .sort((a, b) => Math.abs(b.chg["1w"]) - Math.abs(a.chg["1w"]))
    .slice(0, 4)
    .map((s) => `${s.name} ${pct(s.chg["1w"], 1)}`);
  if (big.length) lines.push(`Biggest moves this week: ${big.join(", ")}.`);
  const byId = Object.fromEntries(d.series.map((s) => [s.id, s]));
  const hy = byId.BAMLH0A0HYM2, real = byId.DFII10;
  if (hy) lines.push(`High-yield spread ${hy.last.toFixed(2)}%, ${hzSigned(hy.chg["1m"] * 100, 0)} bp in a month, at the ${psOrd(hy.pct_5y)} percentile of 5 years.`);
  if (real) lines.push(`10-year real yield ${real.last.toFixed(2)}%, at the ${psOrd(real.pct_5y)} percentile of 5 years.`);
  for (const l of lines) card.append(el("p", {}, l));
  return card;
}

function renderMarkets(d) {
  const box = pageBox();
  box.replaceChildren();
  const head = el("div", { class: "d-head" });
  head.append(el("h2", {}, "Markets"), el("div", { class: "d-sub" }, `Indexes, rates, credit, currencies, commodities and crypto · as of ${d.as_of}`));
  box.append(head, mkSummary(d));

  const byId = Object.fromEntries(d.series.map((s) => [s.id, s]));
  const cur = byId[mk.sel] || d.series[0];
  const chartSec = el("section", { class: "hz-sec", id: "mk-chart" });
  const ctl = el("div", { class: "ranges" });
  for (const r of MK_RANGES) {
    const b = el("button", { class: "chip", "aria-pressed": String(mk.range === r.days) }, r.label);
    b.addEventListener("click", () => { mk.range = r.days; renderMarkets(d); });
    ctl.append(b);
  }
  chartSec.append(ctl);
  if (cur) {
    const h = cur.history;
    const from = mk.range ? isoOf(dayNum(h.dates[h.dates.length - 1]) - mk.range) : "";
    const i0 = Math.max(0, h.dates.findIndex((x) => x >= from));
    const s = { dates: h.dates.slice(i0) };
    const vals = h.values.slice(i0);
    psChart(chartSec, s, { title: `${cur.name}${cur.note ? ` (${cur.note})` : ""}`, values: vals, digits: mkYield(cur) ? 2 : Math.abs(cur.last) >= 100 ? 0 : 2 },
      (i) => `${s.dates[i]}: ${mkLevel(cur, vals[i])}`);
  }
  box.append(chartSec);

  const cols = [["Market", ""], ["Last", "Latest close"], ["1d", ""], ["1w", ""], ["1m", ""], ["3m", ""], ["YTD", "Since the last close of last year"], ["1y", ""],
    ["From high", "Below the 1-year high"], ["1y pct", "Where today sits in the last year's range of closes, 0–100"], ["5y pct", "The same over 5 years"]];
  for (const [g, title] of Object.entries(d.groups)) {
    const rows = d.series.filter((s) => s.group === g);
    if (!rows.length) continue;
    const sec = el("section", { class: "hz-sec" });
    sec.append(el("h3", {}, title));
    const t = el("table", { class: "ps-table mk-table" });
    t.append(el("thead"), el("tbody"));
    const hr = el("tr");
    cols.forEach(([c, tip], i) => hr.append(el("th", { class: i ? "num" : "", title: tip }, c)));
    t.tHead.append(hr);
    for (const s of rows) {
      const tr = el("tr", { class: s.id === cur?.id ? "ps-sel" : "" });
      const name = el("td");
      name.append(el("strong", {}, s.name), el("span", { class: "name" }, s.note || s.id));
      tr.append(name, el("td", { class: "num" }, mkLevel(s, s.last)));
      for (const k of ["1d", "1w", "1m", "3m", "ytd", "1y"]) tr.append(mkChange(s, s.chg[k]));
      tr.append(
        psCell(s.from_high, { pctFmt: true, lo: -0.2 }),
        psCell(s.pct_1y, { digits: 0, hi: 95, lo: 5 }),
        psCell(s.pct_5y, { digits: 0, hi: 95, lo: 5 }));
      tr.addEventListener("click", () => {
        mk.sel = s.id;
        renderMarkets(d);
        $("#mk-chart").scrollIntoView({ behavior: "smooth", block: "start" });
      });
      t.tBodies[0].append(tr);
    }
    const sc = el("div", { class: "ps-scroll" });
    sc.append(t);
    sec.append(sc);
    box.append(sec);
  }
  const failed = d.failed?.length ? ` Not updated this time: ${d.failed.join(", ")}.` : "";
  box.append(el("p", { class: "help" }, `Click a row for its chart. Sources: Yahoo (indexes, currencies, futures, crypto), FRED (Treasury yields, Fed funds, ICE BofA credit spreads; German and Japanese 10-year are monthly).${failed}`));
}

// ---------- industry: memory spot prices, GPU rental, oil shipping ----------

const ind = { port: "Strait of Hormuz", mem: "DRAM chips|DDR5 16Gb (2Gx8) 4800/5600", gpu: "H100 SXM", range: 730 };
const IND_RANGES = [
  { label: "1 year", days: 365 },
  { label: "2 years", days: 730 },
  { label: "All", days: null },
];
const IND_MEM_ORDER = ["DRAM chips", "DRAM modules", "GDDR", "NAND wafers", "NAND chips", "Memory cards"];

async function showIndustry() {
  const box = pageBox();
  try {
    const res = await fetch("data/industry.json", { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    renderIndustry(await res.json());
  } catch {
    box.replaceChildren(el("p", { class: "empty" }, "No industry data yet. It is collected each night."));
  }
}

function indSlice(dates, ...cols) {
  const from = ind.range ? isoOf(dayNum(dates[dates.length - 1]) - ind.range) : "";
  const i0 = Math.max(0, dates.findIndex((x) => x >= from));
  return [{ dates: dates.slice(i0) }, ...cols.map((c) => c && c.slice(i0))];
}

function indRanges(d) {
  const ctl = el("div", { class: "ranges" });
  for (const r of IND_RANGES) {
    const b = el("button", { class: "chip", "aria-pressed": String(ind.range === r.days) }, r.label);
    b.addEventListener("click", () => { ind.range = r.days; renderIndustry(d); });
    ctl.append(b);
  }
  return ctl;
}

function indTable(cols) {
  const t = el("table", { class: "ps-table" });
  t.append(el("thead"), el("tbody"));
  const hr = el("tr");
  cols.forEach(([c, tip], i) => hr.append(el("th", { class: i ? "num" : "", title: tip || "" }, c)));
  t.tHead.append(hr);
  return t;
}
const indScroll = (t) => { const s = el("div", { class: "ps-scroll" }); s.append(t); return s; };
const indChg = (v) => (v == null ? el("td", { class: "num muted" }, "n/a") : el("td", { class: `num ret ${v >= 0 ? "pos" : "neg"}` }, pct(v, 1)));

function indSummary(d) {
  const card = el("div", { class: "card hz-summary" });
  const h = (d.shipping || []).find((x) => x.name === "Strait of Hormuz");
  if (h) card.append(el("p", {}, `Strait of Hormuz: ${h.now.n_tanker.toFixed(1)} tankers a day with their transponder on in the week to ${h.date}, against ${h.before.n_tanker.toFixed(1)} in the year before ${d.war_start}. Dark tankers aren't in this count; satellite trackers see several times more.`));
  const ddr5 = (d.memory?.items || []).find((x) => x.item.startsWith("DDR5 16Gb") && x.item.includes("4800"));
  if (ddr5) card.append(el("p", {}, `DDR5 16Gb spot $${ddr5.last.toFixed(2)} on ${ddr5.date}${ddr5.chg["1m"] != null ? `, ${pct(ddr5.chg["1m"], 1)} in a month` : ""}${ddr5.chg["1y"] != null ? `, ${pct(ddr5.chg["1y"], 0)} in a year` : ""}.`));
  const h100 = (d.gpu || []).find((x) => x.gpu === "H100 SXM");
  if (h100) card.append(el("p", {}, `H100 SXM rental on vast.ai: median $${h100.median.toFixed(2)} per GPU-hour, ${h100.offers} offers free right now.`));
  return card;
}

function renderIndustry(d) {
  const box = pageBox();
  box.replaceChildren();
  const head = el("div", { class: "d-head" });
  head.append(el("h2", {}, "Industry"), el("div", { class: "d-sub" }, "Oil shipping, memory spot prices and GPU rental prices"));
  box.append(head, indSummary(d), indRanges(d));

  // Oil shipping through the chokepoints
  const sh = el("section", { class: "hz-sec" });
  sh.append(el("h3", {}, "Oil shipping through the chokepoints"));
  sh.append(el("p", { class: "help" }, `Ships counted from their AIS positions by IMF PortWatch, 7-day averages; about a week behind. "Before" is the year up to ${d.war_start}, when Hormuz traffic collapsed. Tanker capacity is deadweight tonnage, closer to barrels than a ship count.`));
  sh.append(el("p", { class: "help ind-warn" }, "Read the level with care: ships that switch their transponder off are not counted, and in a war zone many tankers do. For Hormuz, satellite-based trackers (Windward, Kpler) counted roughly 15–40 transits a day in late September 2026, about a third of them dark, against ~2 here. The timing and direction of changes are reliable; the size of the drop is overstated."));
  const st = indTable([["Chokepoint"], ["Tankers a day", "Last 7 days"], ["Before", "Year before the war"], ["Change"], ["All ships a day"], ["Before"], ["Tanker capacity, kt a day"], ["Before"]]);
  for (const c of d.shipping || []) {
    const tr = el("tr", { class: c.name === ind.port ? "ps-sel" : "" });
    tr.append(el("td", {}, c.name), el("td", { class: "num" }, c.now.n_tanker.toFixed(1)), el("td", { class: "num" }, c.before.n_tanker.toFixed(1)),
      indChg(c.before.n_tanker ? c.now.n_tanker / c.before.n_tanker - 1 : null),
      el("td", { class: "num" }, c.now.n_total.toFixed(1)), el("td", { class: "num" }, c.before.n_total.toFixed(1)),
      el("td", { class: "num" }, (c.now.capacity_tanker / 1000).toFixed(0)), el("td", { class: "num" }, (c.before.capacity_tanker / 1000).toFixed(0)));
    tr.addEventListener("click", () => { ind.port = c.name; renderIndustry(d); });
    st.tBodies[0].append(tr);
  }
  sh.append(indScroll(st));
  const port = (d.shipping || []).find((x) => x.name === ind.port);
  if (port) {
    const [s, tankers, ships] = indSlice(port.history.dates, port.history.tankers, port.history.ships);
    psChart(sh, s, { title: `${port.name}: tankers a day (solid) and all ships (dashed), 7-day average`, values: tankers, extra: ships, digits: 0 },
      (i) => `${s.dates[i]}: ${tankers[i]} tankers, ${ships[i]} ships`);
  }
  box.append(sh);

  // Memory spot prices
  const ms = el("section", { class: "hz-sec" });
  ms.append(el("h3", {}, "Memory spot prices"));
  ms.append(el("p", { class: "help" }, "DRAMeXchange spot prices in US dollars, session average. Spot is the small, fast market that turns before contract prices do; DRAM chips update daily, the others weekly. History before October 2026 is rebuilt from archived copies of the page, so it has gaps."));
  const mt = indTable([["Item"], ["Price", "Session average, US$"], ["1w"], ["1m"], ["3m"], ["1y"], ["Date", "Last update"]]);
  const items = (d.memory?.items || []).slice().sort((a, b) => IND_MEM_ORDER.indexOf(a.section) - IND_MEM_ORDER.indexOf(b.section) || a.item.localeCompare(b.item));
  let lastSec = null;
  for (const m of items) {
    if (m.section !== lastSec) {
      lastSec = m.section;
      const gh = el("tr", { class: "ps-group" });
      gh.append(el("td", { colspan: "7" }, m.section));
      mt.tBodies[0].append(gh);
    }
    const key = `${m.section}|${m.item}`;
    const tr = el("tr", { class: key === ind.mem ? "ps-sel" : "" });
    tr.append(el("td", {}, m.item), el("td", { class: "num" }, m.last.toFixed(2)));
    for (const k of ["1w", "1m", "3m", "1y"]) tr.append(indChg(m.chg[k]));
    tr.append(el("td", { class: "num" }, m.date));
    tr.addEventListener("click", () => { ind.mem = key; renderIndustry(d); });
    mt.tBodies[0].append(tr);
  }
  ms.append(indScroll(mt));
  const mem = items.find((m) => `${m.section}|${m.item}` === ind.mem) || items[0];
  if (mem && mem.history.dates.length > 1) {
    const [s, v] = indSlice(mem.history.dates, mem.history.values);
    psChart(ms, s, { title: `${mem.item} (${mem.section}), US$`, values: v, digits: 2 }, (i) => `${s.dates[i]}: $${v[i].toFixed(2)}`);
  }
  box.append(ms);

  // GPU rental
  const gs = el("section", { class: "hz-sec" });
  gs.append(el("h3", {}, "GPU rental prices"));
  gs.append(el("p", { class: "help" }, "vast.ai marketplace, on-demand offers that are free right now, per GPU-hour. A spot market of mostly smaller hosts, cheaper than the big clouds; the trend matters more than the level. Fewer free offers means tighter supply. Recorded nightly from 19 October 2026."));
  const gt = indTable([["GPU"], ["Median $/h"], ["Cheapest quarter", "25th percentile"], ["Cheapest"], ["Free offers"], ["Free GPUs"], ["1w"], ["1m"]]);
  for (const g of d.gpu || []) {
    const tr = el("tr", { class: g.gpu === ind.gpu ? "ps-sel" : "" });
    tr.append(el("td", {}, g.gpu), el("td", { class: "num" }, g.median.toFixed(2)), el("td", { class: "num" }, g.p25.toFixed(2)), el("td", { class: "num" }, g.min.toFixed(2)),
      el("td", { class: "num" }, String(g.offers)), el("td", { class: "num" }, String(g.gpus)), indChg(g.chg["1w"]), indChg(g.chg["1m"]));
    tr.addEventListener("click", () => { ind.gpu = g.gpu; renderIndustry(d); });
    gt.tBodies[0].append(tr);
  }
  gs.append(indScroll(gt));
  const gpu = (d.gpu || []).find((g) => g.gpu === ind.gpu);
  if (gpu && gpu.history.dates.length > 1) {
    const [s, v] = indSlice(gpu.history.dates, gpu.history.values);
    psChart(gs, s, { title: `${gpu.gpu}: median $ per GPU-hour`, values: v, digits: 2 }, (i) => `${s.dates[i]}: $${v[i].toFixed(2)}`);
  }
  box.append(gs);
  const failed = d.failed?.length ? ` Not updated this time: ${d.failed.join(", ")}.` : "";
  box.append(el("p", { class: "help" }, `Click a row for its chart. Sources: IMF PortWatch, DRAMeXchange (TrendForce), vast.ai.${failed}`));
}

document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => showPage(t.dataset.page)));

// The grouped header row wraps, so pin the sub-header just below its real height.
function pinSubHeader() {
  const h = $("#table thead tr").getBoundingClientRect().height;
  document.querySelectorAll("#table thead tr.sub th").forEach((th) => (th.style.top = `${h}px`));
}
window.addEventListener("resize", pinSubHeader);

function setExpanded(on) {
  state.expanded = on;
  $("main.layout").classList.toggle("expanded", on);
  pinSubHeader();
  const b = $("#expand");
  b.setAttribute("aria-pressed", String(on));
  b.textContent = on ? "⤡ Back to stock view" : "⤢ Expand list: 1-year price targets";
  const url = new URL(location.href);
  if (on) url.searchParams.set("view", "list");
  else url.searchParams.delete("view");
  history.replaceState(null, "", url);
}
$("#expand").addEventListener("click", () => setExpanded(!state.expanded));

$("#search").addEventListener("input", (e) => {
  state.query = e.target.value;
  renderTable();
});
load();

// ---------- discounts: holding companies and preferred shares against what they track ----------

const dc = { range: 1095 };
const DC_TICKERS = {
  "402340.KS": "SK Square is mostly a holding of 20% of SK hynix.",
  "005935.KS": "Samsung's preferred shares track the common shares at a discount.",
};
const DC_RANGES = [{ label: "1Y", days: 365 }, { label: "3Y", days: 1095 }, { label: "5Y", days: 1826 }, { label: "All", days: 0 }];

async function showDiscounts() {
  const box = pageBox();
  try {
    const res = await fetch("data/discounts.json", { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    renderDiscounts(await res.json());
  } catch {
    box.replaceChildren(el("p", { class: "empty" }, "No discount data yet. It is collected each night."));
  }
}

const dcPts = (v) => (v == null ? "n/a" : `${v >= 0 ? "+" : "−"}${Math.abs(v * 100).toFixed(1)} pts`);

/** Where today's discount sits: wide against its own past means the derivative is cheap. */
function dcVerdict(s) {
  const p = s.pct_3y;
  if (p >= 80) return ["cheap", "Wide against its last 3 years: the cheap end of its range."];
  if (p <= 20) return ["rich", "Narrow against its last 3 years: little left of the usual discount."];
  return ["normal", "Inside its usual range of the last 3 years."];
}

function renderDiscounts(d) {
  const box = pageBox();
  box.replaceChildren();
  const head = el("div", { class: "d-head" });
  head.append(el("h2", {}, "Discounts"), el("div", { class: "d-sub" }, "Stocks that are mostly a claim on another stock, and how far below that stock they trade"));
  box.append(head);
  const card = el("div", { class: "card hz-summary" });
  for (const it of d.items) {
    const s = it.stats;
    card.append(el("p", {}, `${it.name}: ${(s.last * 100).toFixed(1)}% discount on ${s.date}, against a median of ${(s.median_3y * 100).toFixed(1)}% over 3 years ` +
      `(wider than on ${Math.round(s.pct_3y)}% of days). ${dcVerdict(s)[1]}`));
  }
  card.append(el("p", { class: "help" }, "Discount = 1 − (what the market pays for the derivative ÷ what the underlying stock is worth). A wider discount than usual makes the derivative the cheaper way to own the same thing; it can stay wide for years, so read it against its own history."));
  box.append(card);

  const ctl = el("div", { class: "ranges" });
  for (const r of DC_RANGES) {
    const b = el("button", { class: "chip", "aria-pressed": String(dc.range === r.days) }, r.label);
    b.addEventListener("click", () => { dc.range = r.days; renderDiscounts(d); });
    ctl.append(b);
  }
  box.append(ctl);

  for (const it of d.items) {
    const s = it.stats;
    const sec = el("section", { class: "hz-sec" });
    sec.append(el("h3", {}, it.name));
    const lt = it.latest;
    const what = it.kind === "holding"
      ? `${it.holdco_name} is worth ${krw(lt.holdco_cap)} (${lt.holdco_shares.toLocaleString("en")} shares at ${krw(lt.holdco_price)}); its ${it.stakes.map((x) => `${(x.shares / 1e6).toFixed(1)}m ${x.name} shares`).join(" and ")} are worth ${krw(lt.stake_value)}.`
      : `Preferred ${krw(lt.pref_price)} against common ${krw(lt.common_price)}.`;
    sec.append(el("p", { class: "help" }, `${what} ${it.note}`));
    const t = indTable([["Discount now"], ["1m", "Change in discount points; negative = narrowing"], ["3m"], ["1y"], ["Median 1y"], ["Median 3y"], ["Median, all", "Since the first date in the chart"], ["Range", "Narrowest to widest"], ["Percentile 3y", "Share of days in 3 years with a narrower discount"]]);
    const tr = el("tr");
    const chg = (v) => el("td", { class: `num ret ${v == null ? "" : v <= 0 ? "neg" : "pos"}` }, dcPts(v));
    tr.append(el("td", {}, `${(s.last * 100).toFixed(1)}%`), chg(s.chg_1m), chg(s.chg_3m), chg(s.chg_1y),
      el("td", { class: "num" }, `${(s.median_1y * 100).toFixed(1)}%`), el("td", { class: "num" }, `${(s.median_3y * 100).toFixed(1)}%`),
      el("td", { class: "num" }, `${(s.median_all * 100).toFixed(1)}%`),
      el("td", { class: "num" }, `${(s.min * 100).toFixed(0)}–${(s.max * 100).toFixed(0)}%`),
      el("td", { class: "num" }, `${Math.round(s.pct_3y)}th`));
    t.tBodies[0].append(tr);
    sec.append(indScroll(t));
    const h = it.history;
    const from = dc.range ? isoOf(dayNum(h.dates[h.dates.length - 1]) - dc.range) : "";
    const i0 = Math.max(0, h.dates.findIndex((x) => x >= from));
    const sl = { dates: h.dates.slice(i0) };
    const v = h.values.slice(i0).map((x) => x * 100);
    const m3 = s.median_3y * 100;
    psChart(sec, sl, { title: `Discount, % (dashed: 3-year median ${m3.toFixed(1)}%)`, values: v, extra: v.map(() => m3), digits: 0 },
      (i) => `${sl.dates[i]}: ${v[i].toFixed(1)}% discount`);
    box.append(sec);
  }
}

const krw = (v) => (v >= 1e12 ? `₩${(v / 1e12).toFixed(1)}trn` : `₩${Math.round(v).toLocaleString("en")}`);
